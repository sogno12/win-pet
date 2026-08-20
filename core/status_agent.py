import os
import json
from datetime import datetime
from core.logger import PetLogger

class StatusAgent:
    """펫의 3대 상태지수 (친밀도, 행복도, 심심함) 관리 및 방치 감지 모듈"""

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STATUS_PATH = os.path.join(BASE_DIR, "status.json")
    DATETIME_FORMAT = "%Y/%m/%d %H:%M:%S"

    DEFAULT_STATUS = {
        "affection": 30,
        "happiness": 50,
        "boredom": 20,
        "last_interaction_time": None
    }

    @classmethod
    def load_status(cls) -> dict:
        status = cls.DEFAULT_STATUS.copy()
        if os.path.exists(cls.STATUS_PATH):
            try:
                with open(cls.STATUS_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    status.update(loaded)
            except Exception as e:
                PetLogger.log_error(f"status.json 로드 오류: {e}")
        return status

    @classmethod
    def save_status(cls, status_data: dict):
        try:
            with open(cls.STATUS_PATH, "w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            PetLogger.log_error(f"status.json 저장 오류: {e}")

    @classmethod
    def _clamp(cls, val: int, min_val: int = 0, max_val: int = 100) -> int:
        return max(min_val, min(max_val, val))

    @classmethod
    def update_time_decay(cls):
        """방치 시간에 따른 수치 자연 변화 (30분마다 행복도 -5, 심심함 +10)"""
        status = cls.load_status()
        now = datetime.now()
        now_str = now.strftime(cls.DATETIME_FORMAT)

        last_str = status.get("last_interaction_time")
        if last_str:
            try:
                last_dt = datetime.strptime(last_str, cls.DATETIME_FORMAT)
                diff_minutes = (now - last_dt).total_seconds() / 60.0

                if diff_minutes >= 30:
                    cycles = int(diff_minutes // 30)
                    status["happiness"] = cls._clamp(status["happiness"] - (5 * cycles))
                    status["boredom"] = cls._clamp(status["boredom"] + (10 * cycles))
                    status["last_interaction_time"] = now_str
                    cls.save_status(status)
                    PetLogger.log_tool("StatusAgent", {"diff_minutes": diff_minutes}, f"방치 시간({diff_minutes:.1f}분) 감지: 행복도 {status['happiness']}, 심심함 {status['boredom']}")
            except Exception as e:
                PetLogger.log_error(f"상태 decay 로직 오류: {e}")
        else:
            status["last_interaction_time"] = now_str
            cls.save_status(status)

    @classmethod
    def interact(cls, action_type: str = "chat") -> dict:
        """상호작용 발생 시 수치 상승 및 보상"""
        status = cls.load_status()
        now_str = datetime.now().strftime(cls.DATETIME_FORMAT)

        if action_type == "pat": # 쓰다듬기
            status["happiness"] = cls._clamp(status["happiness"] + 8)
            status["affection"] = cls._clamp(status["affection"] + 2)
            status["boredom"] = cls._clamp(status["boredom"] - 15)
            msg = "펫 쓰다듬기 상호작용! ✨"
        elif action_type == "chat": # 대화하기
            status["happiness"] = cls._clamp(status["happiness"] + 5)
            status["affection"] = cls._clamp(status["affection"] + 1)
            status["boredom"] = cls._clamp(status["boredom"] - 10)
            msg = "펫 대화 상호작용! 💬"
        else:
            msg = "일반 상호작용"

        status["last_interaction_time"] = now_str
        cls.save_status(status)
        PetLogger.log_tool("StatusAgent", {"action": action_type}, f"{msg} (친밀도={status['affection']}, 행복도={status['happiness']}, 심심함={status['boredom']})")
        return status

    @classmethod
    def get_affection_level(cls, affection_score: int) -> tuple[int, str]:
        """친밀도 점수에 따른 5단계 호칭 레벨"""
        if affection_score < 20:
            return 1, "🌱 낯선 이웃"
        elif affection_score < 40:
            return 2, "🐾 서먹한 친구"
        elif affection_score < 65:
            return 3, "💖 다정한 친한 친구"
        elif affection_score < 85:
            return 4, "✨ 단짝 컴패니언"
        else:
            return 5, "👑 평생 베스트 프렌드"

    @classmethod
    def get_prompt_hint(cls) -> str:
        """LLM 대화 주입용 기분 및 친밀도 힌트"""
        cls.update_time_decay()
        status = cls.load_status()
        level, title = cls.get_affection_level(status["affection"])

        hints = [f"[펫의 상태 & 친밀도 정보: {title} (친밀도 {status['affection']}점)]"]
        
        if status["boredom"] >= 75:
            hints.append("- 현재 펫이 꽤 심심해하고 있습니다. 은근히 주인님과 노는 것을 원합니다.")
        elif status["happiness"] >= 80:
            hints.append("- 현재 펫이 대단히 기분이 좋고 신나 있습니다! 발랄한 태도를 유지하세요.")
        elif status["happiness"] <= 30:
            hints.append("- 현재 펫이 약간 기운이 없거나 조용합니다.")

        return "\n".join(hints)
