import os
import json
from datetime import datetime, timedelta
from core.config_manager import ConfigManager
from core.logger import PetLogger

class MemoryAgent:
    """시간 감각(타임스탬프)과 세션 관리 기능을 갖춘 대화 기억력 모듈"""

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MEMORY_FILE_PATH = os.path.join(BASE_DIR, "memory.json")
    DATETIME_FORMAT = "%Y/%m/%d %H:%M:%S"

    @classmethod
    def load_memory(cls) -> dict:
        if os.path.exists(cls.MEMORY_FILE_PATH):
            try:
                with open(cls.MEMORY_FILE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                PetLogger.log_error(f"memory.json 로드 오류: {e}")
        return {
            "last_active_time": None,
            "short_term_session": [],
            "long_term_facts": []
        }

    @classmethod
    def save_memory(cls, memory_data: dict):
        try:
            with open(cls.MEMORY_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            PetLogger.log_error(f"memory.json 저장 오류: {e}")

    @classmethod
    def format_relative_time(cls, past_time_str: str, now: datetime) -> str:
        """past_time_str을 읽어 '방금 전', '5분 전', '2시간 전', '어제', '3일 전' 등의 상대 시간 텍스트로 변환"""
        try:
            past_dt = datetime.strptime(past_time_str, cls.DATETIME_FORMAT)
            diff = now - past_dt
            seconds = int(diff.total_seconds())

            if seconds < 60:
                return "[방금 전]"
            elif seconds < 3600:
                mins = seconds // 60
                return f"[{mins}분 전]"
            elif seconds < 86400:
                hours = seconds // 3600
                return f"[{hours}시간 전]"
            elif seconds < 172800:
                return f"[어제 {past_dt.strftime('%H:%M')}]"
            else:
                days = seconds // 86400
                return f"[{days}일 전 ({past_dt.strftime('%Y/%m/%d')})]"
        except Exception:
            return f"[{past_time_str}]"

    @classmethod
    def check_and_update_session(cls, memory: dict, now: datetime):
        """설정된 session_timeout_minutes 초과 시 단기 세션 리셋 및 장기 팩트 이관"""
        config = ConfigManager.load_config()
        timeout_mins = config.get("session_timeout_minutes", 30)

        last_active_str = memory.get("last_active_time")
        if last_active_str:
            try:
                last_dt = datetime.strptime(last_active_str, cls.DATETIME_FORMAT)
                diff_mins = (now - last_dt).total_seconds() / 60.0

                # 설정된 분 수 초과 시 단기 세션 종결 및 팩트 추출 저장
                if diff_mins >= timeout_mins:
                    session = memory.get("short_term_session", [])
                    if session:
                        # 이전 세션 중 의미있는 사용자 대화를 장기 기억 팩트로 이관
                        for turn in session:
                            if turn.get("role") == "user" and len(turn.get("text", "")) >= 4:
                                memory["long_term_facts"].append({
                                    "time": turn.get("time"),
                                    "fact": f"이전 대화 요약: 사용자가 '{turn.get('text')}' 언급함"
                                })
                    # 최근 10개 팩트만 남김
                    memory["long_term_facts"] = memory["long_term_facts"][-10:]
                    # 단기 세션 초기화
                    memory["short_term_session"] = []
                    PetLogger.log_tool("MemoryAgent", {"timeout_mins": timeout_mins}, f"세션 만료({diff_mins:.1f}분 경과)로 단기 대화 리셋 및 팩트 보관 완료.")
            except Exception as e:
                PetLogger.log_error(f"세션 타임아웃 계산 오류: {e}")

    @classmethod
    def get_memory_context(cls) -> str:
        """LLM 프롬프트에 주입할 시간 힌트 포함 메모리 컨텍스트 생성"""
        memory = cls.load_memory()
        now = datetime.now()
        now_str = now.strftime(cls.DATETIME_FORMAT)

        cls.check_and_update_session(memory, now)

        short_session = memory.get("short_term_session", [])
        long_facts = memory.get("long_term_facts", [])

        lines = [f"[현재 시각: {now_str}]"]

        if long_facts:
            lines.append("\n[펫이 기억하고 있는 장기 기억 팩트 및 과거 활동 레코드]")
            for item in long_facts[-5:]: # 최근 5개 팩트
                rel_time = cls.format_relative_time(item.get("time", ""), now)
                lines.append(f"- {rel_time} {item.get('fact')}")

        if short_session:
            lines.append("\n[최근 진행 중인 단기 대화 히스토리]")
            # 최근 6개 대화 턴만 표시 (속도 최적화)
            for turn in short_session[-6:]:
                rel_time = cls.format_relative_time(turn.get("time", ""), now)
                role = "User" if turn.get("role") == "user" else "Pet"
                lines.append(f"- {rel_time} {role}: {turn.get('text')}")

        return "\n".join(lines)

    @classmethod
    def save_interaction(cls, user_query: str, pet_response: str):
        """대화 수행 후 memory.json 실시간 업데이트"""
        memory = cls.load_memory()
        now = datetime.now()
        now_str = now.strftime(cls.DATETIME_FORMAT)

        session = memory.get("short_term_session", [])
        session.append({"time": now_str, "role": "user", "text": user_query})
        session.append({"time": now_str, "role": "pet", "text": pet_response})

        # 단기 세션은 최대 10턴(20개 메시지)까지만 보관
        memory["short_term_session"] = session[-20:]
        memory["last_active_time"] = now_str

        cls.save_memory(memory)
