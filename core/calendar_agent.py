import os
import json
import time
import datetime
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from core.logger import PetLogger
from core.info_agent import InfoAgent
from core.status_agent import StatusAgent

class CalendarAgent(QObject):
    """통합 일정(시작일시) 및 할일(마감일시 TODO)과 아침 브리핑/사전 알림을 관리하는 에이전트"""

    schedule_reminded = pyqtSignal(str, str, str)  # (id, title, remind_type) -> 사전 알림
    briefing_ready = pyqtSignal(str)              # (briefing_text) -> 아침 브리핑

    SCHEDULES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schedules.json")
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = CalendarAgent()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.schedules = self.load_schedules()

        # 30초 주기의 백그라운드 알림 및 브리핑 체커
        self.clock = QTimer(self)
        self.clock.setInterval(30000)
        self.clock.timeout.connect(self._on_tick)
        self.clock.start()

    def load_schedules(self) -> list:
        if os.path.exists(self.SCHEDULES_PATH):
            try:
                with open(self.SCHEDULES_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                PetLogger.log_error(f"schedules.json 로드 실패: {e}")
        return []

    def save_schedules(self):
        try:
            with open(self.SCHEDULES_PATH, "w", encoding="utf-8") as f:
                json.dump(self.schedules, f, ensure_ascii=False, indent=2)
        except Exception as e:
            PetLogger.log_error(f"schedules.json 저장 실패: {e}")

    @staticmethod
    def normalize_date_str(date_str: str) -> str:
        """오늘, 내일, 모레 또는 yyyy/MM/dd 포맷으로 통일"""
        now = datetime.datetime.now()
        clean = (date_str or "").strip().lower()
        if not clean or clean in ["오늘", "today"]:
            return now.strftime("%Y/%m/%d")
        elif clean in ["내일", "tomorrow"]:
            return (now + datetime.timedelta(days=1)).strftime("%Y/%m/%d")
        elif clean in ["모레", "글피"]:
            return (now + datetime.timedelta(days=2)).strftime("%Y/%m/%d")

        clean = clean.replace("-", "/").replace(".", "/")
        parts = clean.split("/")
        if len(parts) == 3:
            try:
                y = int(parts[0])
                m = int(parts[1])
                d = int(parts[2])
                return f"{y:04d}/{m:02d}/{d:02d}"
            except Exception:
                pass
        elif len(parts) == 2:
            try:
                m = int(parts[0])
                d = int(parts[1])
                return f"{now.year:04d}/{m:02d}/{d:02d}"
            except Exception:
                pass
        return now.strftime("%Y/%m/%d")

    @staticmethod
    def normalize_time_str(time_str: str) -> str:
        """오후 3시, 15:00 등을 HH:mm 또는 ALL_DAY로 통일"""
        clean = (time_str or "").strip()
        if not clean or clean in ["종일", "하루종일", "all_day", "allday"]:
            return "ALL_DAY"

        is_pm = "오후" in clean or "pm" in clean.lower() or "저녁" in clean or "밤" in clean
        is_am = "오전" in clean or "am" in clean.lower() or "아침" in clean or "새벽" in clean

        digits = "".join(c for c in clean if c.isdigit() or c == ":")
        if ":" in digits:
            parts = digits.split(":")
            try:
                h = int(parts[0])
                m = int(parts[1])
                if is_pm and h < 12:
                    h += 12
                elif is_am and h == 12:
                    h = 0
                return f"{h:02d}:{m:02d}"
            except Exception:
                return "ALL_DAY"
        elif digits.isdigit():
            try:
                h = int(digits)
                if is_pm and h < 12:
                    h += 12
                elif is_am and h == 12:
                    h = 0
                return f"{h:02d}:00"
            except Exception:
                return "ALL_DAY"
        return "ALL_DAY"

    def add_schedule(self, title: str, date_str: str = "오늘", time_str: str = "ALL_DAY", item_type: str = "event", remind_before: int = 10) -> str:
        """일정(event) 또는 할일(todo)을 등록"""
        target_date = self.normalize_date_str(date_str)
        target_time = self.normalize_time_str(time_str)
        item_type = "todo" if "todo" in item_type.lower() or "할일" in item_type else "event"

        sched_id = f"sched_{int(time.time() * 1000)}"
        new_item = {
            "id": sched_id,
            "type": item_type,
            "date": target_date,
            "time": target_time,
            "title": title.strip(),
            "done": False,
            "remind_before": remind_before,
            "is_notified": False,
            "created_at": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        }

        self.schedules.append(new_item)
        self.save_schedules()

        type_label = "할 일(TODO)" if item_type == "todo" else "일정"
        time_display = "종일" if target_time == "ALL_DAY" else target_time
        msg = f"📅 [{type_label}] {target_date} {time_display} '{title}' 등록 완료!"
        PetLogger.log_tool("add_schedule", new_item, msg)
        return msg

    def get_today_schedules(self) -> list:
        """오늘 날짜의 일정 및 할일 목록 조회"""
        today_str = datetime.datetime.now().strftime("%Y/%m/%d")
        return [s for s in self.schedules if s.get("date") == today_str]

    def get_today_summary_text(self) -> str:
        """오늘의 일정 및 할일 텍스트 요약"""
        items = self.get_today_schedules()
        if not items:
            return "오늘 등록된 일정이나 할 일이 없어요! 여유로운 하루 보내세요~"

        events = [s for s in items if s.get("type") == "event"]
        todos = [s for s in items if s.get("type") == "todo"]

        lines = []
        if events:
            lines.append("📌 [오늘의 일정]")
            for e in events:
                t = e.get("time", "종일")
                lines.append(f"- {t}: {e.get('title')}")

        if todos:
            if lines:
                lines.append("")
            lines.append("✅ [오늘의 할 일(TODO)]")
            for td in todos:
                status = "(완료)" if td.get("done") else "(진행중)"
                t = f" (~{td.get('time')})" if td.get("time") != "ALL_DAY" else ""
                lines.append(f"- {td.get('title')}{t} {status}")

        return "\n".join(lines)

    def toggle_done(self, sched_id: str) -> bool:
        """할 일 완료 여부 토글"""
        for s in self.schedules:
            if s.get("id") == sched_id:
                s["done"] = not s.get("done", False)
                self.save_schedules()
                return s["done"]
        return False

    def delete_schedule(self, sched_id: str) -> bool:
        """일정/할일 삭제"""
        orig_len = len(self.schedules)
        self.schedules = [s for s in self.schedules if s.get("id") != sched_id]
        if len(self.schedules) < orig_len:
            self.save_schedules()
            return True
        return False

    def get_morning_briefing(self, force: bool = False) -> str:
        """오늘 날씨와 오늘 일정을 결합한 아침 굿모닝 브리핑 생성"""
        now = datetime.datetime.now()
        today_str = now.strftime("%Y/%m/%d")

        # 중복 체크
        status_data = StatusAgent.load_status()
        last_briefing = status_data.get("last_briefing_date", "")
        if not force and last_briefing == today_str:
            return ""

        # 아침 시간대(06시 ~ 11시 59분) 체크 (강제 실행 아닐 때)
        if not force and not (6 <= now.hour < 12):
            return ""

        # 날씨 조회
        try:
            weather_text = InfoAgent.get_weather("서울", "today")
        except Exception:
            weather_text = "오늘 하루도 맑고 상쾌한 기운이 가득하길 바라요!"

        # 스케줄 요약
        today_items = self.get_today_schedules()
        if today_items:
            events_count = len([s for s in today_items if s.get("type") == "event"])
            todos_count = len([s for s in today_items if s.get("type") == "todo" and not s.get("done")])
            sched_brief = f"오늘 일정 {events_count}개와 해야 할 일 {todos_count}개가 있어요."
        else:
            sched_brief = "오늘은 등록된 일정이 없어서 여유롭게 집중할 수 있는 날이에요."

        briefing = f"☀️ 좋은 아침이에요!\n{weather_text}\n{sched_brief}"

        # 브리핑 완료 날짜 저장
        status_data["last_briefing_date"] = today_str
        StatusAgent.save_status(status_data)

        PetLogger.log_tool("morning_briefing", {"date": today_str}, briefing)
        return briefing

    def _on_tick(self):
        """30초마다 사전 알림 체크"""
        now = datetime.datetime.now()
        today_str = now.strftime("%Y/%m/%d")
        current_minute = now.hour * 60 + now.minute

        for s in self.schedules:
            if s.get("date") != today_str or s.get("is_notified") or s.get("done"):
                continue

            time_str = s.get("time", "ALL_DAY")
            if time_str == "ALL_DAY":
                continue

            try:
                parts = time_str.split(":")
                target_minute = int(parts[0]) * 60 + int(parts[1])
                remind_before = s.get("remind_before", 10)
                diff = target_minute - current_minute

                if 0 <= diff <= remind_before:
                    s["is_notified"] = True
                    self.save_schedules()

                    item_type_label = "할 일" if s.get("type") == "todo" else "일정"
                    remind_msg = f"⏰ [{item_type_label} 알림] {diff}분 뒤에 '{s.get('title')}' 시간이 다가와요!"
                    PetLogger.log_tool("schedule_remind", {"id": s["id"]}, remind_msg)
                    self.schedule_reminded.emit(s["id"], s.get("title", ""), f"{diff}분 전 알림")
            except Exception:
                pass

    @classmethod
    def execute_tool(cls, tool_name: str, args: dict) -> str:
        inst = cls.get_instance()
        if tool_name == "add_schedule":
            title = args.get("title", "")
            date_str = args.get("date_str", "오늘")
            time_str = args.get("time_str", "ALL_DAY")
            item_type = args.get("item_type", "event")
            remind_before = args.get("remind_before", 10)
            return inst.add_schedule(title, date_str, time_str, item_type, remind_before)
        elif tool_name in ["get_today_schedule", "get_schedules"]:
            return inst.get_today_summary_text()
        elif tool_name == "get_morning_briefing":
            res = inst.get_morning_briefing(force=True)
            return res if res else inst.get_today_summary_text()
        return f"알 수 없는 일정 도구: {tool_name}"
