import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from core.logger import PetLogger

class ScheduleAgent(QObject):
    """1회성 타이머 및 집중/휴식 반복 포모도로 사이클을 백그라운드 관리하는 스케줄러"""
    
    # 시그널 정의
    timer_triggered = pyqtSignal(str, str)  # (timer_id, memo) -> 1회성 타이머 알림
    pomodoro_phase_changed = pyqtSignal(str, str, int, int)  # (phase, msg, cycle_count, remaining_seconds)
    
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ScheduleAgent()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.timers = []  # [{id, memo, end_time, initial_seconds}]
        
        # 포모도로 세션 상태
        self.pomodoro = {
            "is_active": False,
            "work_minutes": 25,
            "rest_minutes": 5,
            "phase": "WORK",  # WORK(집중) 또는 REST(휴식)
            "cycle_count": 0,
            "end_time": 0
        }
        
        # 1초 주기의 백그라운드 타이머
        self.clock = QTimer(self)
        self.clock.setInterval(1000)
        self.clock.timeout.connect(self._on_tick)
        self.clock.start()

    def add_timer(self, minutes: float = 0, memo: str = "타이머", target_time_str: str = "", action_name: str = "", action_args: dict = None) -> str:
        """1회성 타이머 또는 00초 정각 시각 알람 추가 (자동 액션 연동 지원)"""
        import datetime
        now_dt = datetime.datetime.now()
        target_dt = None
        
        # 1. target_time_str (예: "17:05", "5:05", "05:05:00") 파싱
        if target_time_str and target_time_str.strip():
            clean_str = target_time_str.strip().replace("시", ":").replace("분", "").replace(" ", "")
            parts = clean_str.split(":")
            if len(parts) >= 2:
                try:
                    hr = int(parts[0])
                    mn = int(parts[1])
                    sc = int(parts[2]) if len(parts) >= 3 else 0
                    
                    target_dt = now_dt.replace(hour=hr, minute=mn, second=sc, microsecond=0)
                    if target_dt <= now_dt:
                        # 이미 지난 시각인 경우 내일 해당 시각으로 설정
                        target_dt += datetime.timedelta(days=1)
                except Exception:
                    target_dt = None

        action_desc = f" ({action_name})" if action_name else ""
        if target_dt:
            end_time = target_dt.timestamp()
            time_display = target_dt.strftime("%H:%M:%S")
            msg = f"⏰ [{memo}] {time_display} 정각 알람{action_desc}이 설정되었어요!"
        else:
            secs = int(minutes * 60)
            if secs <= 0:
                secs = 10
            end_time = time.time() + secs
            m, s = divmod(secs, 60)
            if m > 0:
                msg = f"⏰ [{memo}] {m}분 {s}초 후 타이머{action_desc}가 설정되었어요!"
            else:
                msg = f"⏰ [{memo}] {s}초 후 타이머{action_desc}가 설정되었어요!"

        timer_id = f"timer_{int(time.time()*1000)}"
        self.timers.append({
            "id": timer_id,
            "memo": memo,
            "end_time": end_time,
            "initial_seconds": int(end_time - time.time()),
            "action_name": action_name,
            "action_args": action_args or {}
        })
        
        PetLogger.log_tool("add_timer", {"minutes": minutes, "target_time": target_time_str, "memo": memo, "action_name": action_name, "action_args": action_args}, msg)
        return msg

    def cancel_timer(self, timer_id: str) -> str:
        """1회성 타이머 취소"""
        self.timers = [t for t in self.timers if t["id"] != timer_id]
        msg = "⏰ 타이머가 취소되었습니다."
        PetLogger.log_tool("cancel_timer", {"timer_id": timer_id}, msg)
        return msg

    def start_pomodoro(self, work_minutes: int = 25, rest_minutes: int = 5) -> str:
        """반복 포모도로 사이클 시작 (집중 -> 휴식 -> 집중...)"""
        if work_minutes <= 0:
            work_minutes = 25
        if rest_minutes <= 0:
            rest_minutes = 5
            
        self.pomodoro["is_active"] = True
        self.pomodoro["work_minutes"] = work_minutes
        self.pomodoro["rest_minutes"] = rest_minutes
        self.pomodoro["phase"] = "WORK"
        self.pomodoro["cycle_count"] = 1
        self.pomodoro["end_time"] = time.time() + (work_minutes * 60)
        
        msg = f"🍅 [포모도로 제 1세션] {work_minutes}분 집중 시간을 시작합니다! 파이팅이에요! 🔥 (휴식 {rest_minutes}분 지정)"
        PetLogger.log_tool("start_pomodoro", {"work": work_minutes, "rest": rest_minutes}, msg)
        
        # 팝업 알림 시그널
        self.pomodoro_phase_changed.emit(
            "WORK_START",
            msg,
            1,
            work_minutes * 60
        )
        return msg

    def stop_pomodoro(self) -> str:
        """포모도로 사이클 중단"""
        if not self.pomodoro["is_active"]:
            return "현재 진행 중인 포모도로 사이클이 없어요."
            
        self.pomodoro["is_active"] = False
        msg = "🛑 포모도로 사이클이 중단되었어요."
        PetLogger.log_tool("stop_pomodoro", {}, msg)
        self.pomodoro_phase_changed.emit("STOPPED", msg, 0, 0)
        return msg

    def get_status_summary(self) -> dict:
        """현재 진행 중인 타이머 및 포모도로 현황 요약 리턴"""
        now = time.time()
        
        # 1. 일반 타이머 현황
        active_timers = []
        for t in self.timers:
            rem = max(0, int(t["end_time"] - now))
            active_timers.append({
                "id": t["id"],
                "memo": t["memo"],
                "remaining_seconds": rem
            })
            
        # 2. 포모도로 현황
        pomo_info = {
            "is_active": self.pomodoro["is_active"],
            "work_minutes": self.pomodoro["work_minutes"],
            "rest_minutes": self.pomodoro["rest_minutes"],
            "phase": self.pomodoro["phase"],
            "cycle_count": self.pomodoro["cycle_count"],
            "remaining_seconds": max(0, int(self.pomodoro["end_time"] - now)) if self.pomodoro["is_active"] else 0
        }
        
        return {
            "timers": active_timers,
            "pomodoro": pomo_info
        }

    def _on_tick(self):
        """1초 마다 백그라운드 카운트다운 체크"""
        now = time.time()
        
        # 1. 일반 타이머 체크
        triggered = []
        remaining_timers = []
        for t in self.timers:
            if now >= t["end_time"]:
                triggered.append(t)
            else:
                remaining_timers.append(t)
                
        self.timers = remaining_timers
        
        for t in triggered:
            action_name = t.get("action_name", "")
            action_args = t.get("action_args", {})
            action_result_msg = ""
            
            if action_name:
                try:
                    from core.pc_agent import PCAgent
                    from core.info_agent import InfoAgent
                    if action_name in ["get_weather", "recommend_lunch"]:
                        action_result_msg = InfoAgent.execute_tool(action_name, action_args)
                    else:
                        action_result_msg = PCAgent.execute_tool(action_name, action_args)
                except Exception as e:
                    action_result_msg = f"액션 '{action_name}' 실행 중 오류: {e}"
            
            if action_result_msg:
                msg = f"⏰ [{t['memo']}] 시간이 다 되었어요! ({action_result_msg})"
            else:
                msg = f"⏰ [알림] '{t['memo']}' 시간이 다 되었어요!"
                
            PetLogger.log_tool("timer_triggered", {"id": t["id"], "action": action_name, "action_args": action_args}, msg)
            self.timer_triggered.emit(t["id"], msg)

        # 2. 포모도로 체크
        if self.pomodoro["is_active"]:
            if now >= self.pomodoro["end_time"]:
                current_phase = self.pomodoro["phase"]
                cycle = self.pomodoro["cycle_count"]
                
                if current_phase == "WORK":
                    # 집중 종료 -> 휴식 전환
                    self.pomodoro["phase"] = "REST"
                    rest_secs = self.pomodoro["rest_minutes"] * 60
                    self.pomodoro["end_time"] = now + rest_secs
                    
                    msg = (
                        f"⏰ [포모도로 알림] 제 {cycle}세션 {self.pomodoro['work_minutes']}분 집중 완료! "
                        f"이제 {self.pomodoro['rest_minutes']}분간 기지개를 켜고 휴식하세요! ☕"
                    )
                    PetLogger.log_tool("pomodoro_rest_start", {"cycle": cycle}, msg)
                    self.pomodoro_phase_changed.emit("REST_START", msg, cycle, rest_secs)
                    
                else:
                    # 휴식 종료 -> 다음 세션 집중 전환
                    self.pomodoro["phase"] = "WORK"
                    self.pomodoro["cycle_count"] += 1
                    next_cycle = self.pomodoro["cycle_count"]
                    work_secs = self.pomodoro["work_minutes"] * 60
                    self.pomodoro["end_time"] = now + work_secs
                    
                    msg = (
                        f"⏰ [포모도로 알림] 휴식 끝! "
                        f"제 {next_cycle}세션 {self.pomodoro['work_minutes']}분 집중을 시작합니다! 🔥"
                    )
                    PetLogger.log_tool("pomodoro_work_start", {"cycle": next_cycle}, msg)
                    self.pomodoro_phase_changed.emit("WORK_START", msg, next_cycle, work_secs)

    @classmethod
    def execute_tool(cls, tool_name: str, args: dict) -> str:
        inst = cls.get_instance()
        if tool_name == "set_timer":
            minutes = args.get("minutes", 0)
            memo = args.get("memo", "알림")
            target_time_str = args.get("target_time_str", "")
            action_name = args.get("action_name", "")
            action_args = args.get("action_args", {})
            return inst.add_timer(
                minutes=minutes, 
                memo=memo, 
                target_time_str=target_time_str, 
                action_name=action_name, 
                action_args=action_args
            )
        elif tool_name == "start_pomodoro":
            work_m = args.get("work_minutes", 25)
            rest_m = args.get("rest_minutes", 5)
            return inst.start_pomodoro(work_m, rest_m)
        elif tool_name == "stop_pomodoro":
            return inst.stop_pomodoro()
        else:
            return f"알 수 없는 스케줄러 도구: {tool_name}"
