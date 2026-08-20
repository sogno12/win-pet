import os
import json
from datetime import datetime
from core.config_manager import ConfigManager
from core.logger import PetLogger

class MemoryAgent:
    """단기 세션 대화 및 독립된 5개 태그/중요도 기반 장기기억(long_term_memory.json) 관리 모듈"""

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SHORT_MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")
    LONG_MEMORY_PATH = os.path.join(BASE_DIR, "long_term_memory.json")
    DATETIME_FORMAT = "%Y/%m/%d %H:%M:%S"

    # 표준 5개 카테고리 태그
    TAGS = ["profile", "preference", "schedule", "habit", "relation"]

    # --- 단기 메모리 (memory.json) 제어 ---

    @classmethod
    def load_short_memory(cls) -> dict:
        if os.path.exists(cls.SHORT_MEMORY_PATH):
            try:
                with open(cls.SHORT_MEMORY_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                PetLogger.log_error(f"memory.json 로드 오류: {e}")
        return {
            "last_active_time": None,
            "short_term_session": []
        }

    @classmethod
    def save_short_memory(cls, memory_data: dict):
        try:
            with open(cls.SHORT_MEMORY_PATH, "w", encoding="utf-8") as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            PetLogger.log_error(f"memory.json 저장 오류: {e}")

    # --- 장기 메모리 (long_term_memory.json) 제어 ---

    @classmethod
    def load_long_memory(cls) -> dict:
        if os.path.exists(cls.LONG_MEMORY_PATH):
            try:
                with open(cls.LONG_MEMORY_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                PetLogger.log_error(f"long_term_memory.json 로드 오류: {e}")
        return {"user_facts": []}

    @classmethod
    def save_long_memory(cls, long_data: dict):
        try:
            with open(cls.LONG_MEMORY_PATH, "w", encoding="utf-8") as f:
                json.dump(long_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            PetLogger.log_error(f"long_term_memory.json 저장 오류: {e}")

    # --- 유틸리티 및 시간 판별 ---

    @classmethod
    def format_relative_time(cls, past_time_str: str, now: datetime) -> str:
        """past_time_str을 읽어 상대적 시간 표기 변환"""
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
        """설정된 session_timeout_minutes 초과 시 단기 세션 리셋"""
        config = ConfigManager.load_config()
        timeout_mins = config.get("session_timeout_minutes", 30)

        last_active_str = memory.get("last_active_time")
        if last_active_str:
            try:
                last_dt = datetime.strptime(last_active_str, cls.DATETIME_FORMAT)
                diff_mins = (now - last_dt).total_seconds() / 60.0

                if diff_mins >= timeout_mins:
                    session = memory.get("short_term_session", [])
                    if session:
                        # 이전 세션 중 중요 팩트 추출하여 장기기억 보관
                        for turn in session:
                            if turn.get("role") == "user":
                                cls.analyze_and_store_fact(turn.get("text"), turn.get("time"))
                    memory["short_term_session"] = []
                    PetLogger.log_tool("MemoryAgent", {"timeout_mins": timeout_mins}, f"세션 만료({diff_mins:.1f}분 경과)로 단기 대화 리셋 완료.")
            except Exception as e:
                PetLogger.log_error(f"세션 타임아웃 계산 오류: {e}")

    # --- 장기기억 추출 & 저장 논리 (중요도 3점 이상만 저장) ---

    @classmethod
    def analyze_and_store_fact(cls, user_text: str, time_str: str = None):
        """사용자 입력 텍스트에서 5개 태그 및 중요도(1~5점)를 판단하여 장기기억에 채택 저장"""
        if not user_text or len(user_text.strip()) < 4:
            return

        text = user_text.strip()
        now_str = time_str or datetime.now().strftime(cls.DATETIME_FORMAT)

        tag = None
        importance = 1
        fact_content = text

        # 1. schedule (일정/약속/이벤트 - 중요도 5점)
        schedule_kw = ["전시회", "고야전", "여행", "약속", "예정", "갈 예정", "보러 갈", "방문", "일정", "콘서트", "영화 보러"]
        if any(kw in text for kw in schedule_kw):
            tag = "schedule"
            importance = 5
            fact_content = f"일정/이벤트: {text}"

        # 2. profile (인적사항/호칭 - 중요도 5점)
        elif any(kw in text for kw in ["내 이름은", "나를 ~라", "직업은", "개발자", "사는 곳", "사는 지역"]):
            tag = "profile"
            importance = 5
            fact_content = f"프로필: {text}"

        # 3. preference (취향/호불호 - 중요도 4점)
        elif any(kw in text for kw in ["좋아해", "좋아함", "최애", "싫어해", "즐겨 듣", "즐겨 보", "즐겨 먹"]):
            tag = "preference"
            importance = 4
            fact_content = f"취향/선호: {text}"

        # 4. relation (관계/인맥 - 중요도 4점)
        elif any(kw in text for kw in ["친구 이름", "가족", "반려동물", "고양이 이름", "강아지 이름"]):
            tag = "relation"
            importance = 4
            fact_content = f"인맥/관계: {text}"

        # 5. habit (습관/일상 - 중요도 3점)
        elif any(kw in text for kw in ["주말마다", "매일", "항상", "퇴근하면"]):
            tag = "habit"
            importance = 3
            fact_content = f"습관/일상: {text}"

        # 중요도 3점 이상인 가치 있는 기억만 long_term_memory.json에 저장
        if tag and importance >= 3:
            long_data = cls.load_long_memory()
            facts = long_data.get("user_facts", [])

            # 중복 체크
            already_exists = any(f.get("content") == fact_content for f in facts)
            if not already_exists:
                new_fact = {
                    "id": len(facts) + 1,
                    "tag": tag,
                    "importance": importance,
                    "content": fact_content,
                    "created_at": now_str
                }
                facts.append(new_fact)
                long_data["user_facts"] = facts
                cls.save_long_memory(long_data)
                PetLogger.log_tool("MemoryAgent", {"tag": tag, "importance": importance}, f"장기기억 채택 저장 완료: '{fact_content}'")

    # --- 선택적 장기기억 회상 (Selective Retrieval) ---

    @classmethod
    def get_memory_context(cls, user_query: str = "") -> str:
        """현재 user_query의 키워드와 연관된 장기기억만 선택적(Selective)으로 추출 주입"""
        short_mem = cls.load_short_memory()
        now = datetime.now()
        now_str = now.strftime(cls.DATETIME_FORMAT)

        cls.check_and_update_session(short_mem, now)

        long_data = cls.load_long_memory()
        all_facts = long_data.get("user_facts", [])

        # user_query 키워드 기반 태그 선택
        matched_facts = []
        query_text = user_query.strip().lower()

        # 태그 매칭 규칙
        relevant_tags = set()
        if any(kw in query_text for kw in ["어디", "장소", "전시회", "고야전", "주말", "일정", "약속", "갈"]):
            relevant_tags.add("schedule")
        if any(kw in query_text for kw in ["좋아", "음악", "음식", "노래", "취향", "추천"]):
            relevant_tags.add("preference")
        if any(kw in query_text for kw in ["이름", "누구", "나", "직업", "프로필"]):
            relevant_tags.add("profile")
        if any(kw in query_text for kw in ["친구", "가족", "반려"]):
            relevant_tags.add("relation")

        # 연관 태그가 있거나, 매칭되는 팩트 추출
        for item in all_facts:
            item_tag = item.get("tag")
            if item_tag in relevant_tags or item.get("importance", 0) >= 5:
                matched_facts.append(item)

        # 아무 매칭이 없는 일상 대화라면 최근 중요 장기기억 2개만 선별
        if not matched_facts and all_facts:
            matched_facts = sorted(all_facts, key=lambda x: x.get("importance", 0), reverse=True)[:2]

        lines = [f"[현재 시각: {now_str}]"]

        if matched_facts:
            lines.append("\n[선택적 회상된 펫의 장기 기억 팩트 (long_term_memory.json)]")
            for item in matched_facts[-5:]: # 최대 5개
                rel_time = cls.format_relative_time(item.get("created_at", ""), now)
                lines.append(f"- {rel_time} (태그: {item.get('tag')}, 중요도: {item.get('importance')}점) {item.get('content')}")

        short_session = short_mem.get("short_term_session", [])
        if short_session:
            lines.append("\n[최근 진행 중인 단기 대화 히스토리]")
            for turn in short_session[-6:]:
                rel_time = cls.format_relative_time(turn.get("time", ""), now)
                role = "User" if turn.get("role") == "user" else "Pet"
                lines.append(f"- {rel_time} {role}: {turn.get('text')}")

        return "\n".join(lines)

    @classmethod
    def save_interaction(cls, user_query: str, pet_response: str):
        """대화 수행 후 단기 세션 업데이트 및 장기기억 분석 저장"""
        short_mem = cls.load_short_memory()
        now = datetime.now()
        now_str = now.strftime(cls.DATETIME_FORMAT)

        session = short_mem.get("short_term_session", [])
        session.append({"time": now_str, "role": "user", "text": user_query})
        session.append({"time": now_str, "role": "pet", "text": pet_response})

        short_mem["short_term_session"] = session[-20:]
        short_mem["last_active_time"] = now_str
        cls.save_short_memory(short_mem)

        # 사용자 입력에 장기기억 팩트가 포함되어 있는지 즉시 분석 채택
        cls.analyze_and_store_fact(user_query, now_str)
