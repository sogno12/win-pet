import os
import json
from core.config_manager import ConfigManager

class PersonaBuilder:
    """펫의 키워드(종류, 성격/말투)와 중앙 프롬프트 지침을 결합하여 systemInstruction을 만드는 모듈"""

    BASE_INSTRUCTION = (
        "너는 사용자의 바탕화면에 살고 있는 픽셀 데스크톱 컴패니언 펫이다.\n"
        "- 너무 짧고 딱딱하게 답하지 말고, 2~3문장 이내로 친절하고 풍부하게 대화를 나누어라.\n"
        "- 사용자가 PC 제어(화면 잠금, 앱 실행, 볼륨 조절, 구글/유튜브 검색 등)나 실시간 정보 조회(날씨, 점심 메뉴 추천 등)를 원하면 "
        "말로만 대답하지 말고 반드시 제공된 도구(Tools)를 즉시 호출해라.\n"
        "- 점심 메뉴나 날씨를 물어보면 툴 결과를 바탕으로 다정하게 메뉴/날씨를 대화로 제안하고, 맛집 검색이 필요하면 말해달라고 유도해라.\n"
        "- 사용자가 할 수 있는 기능이나 역할을 물어보면 화면 잠금(🔒), 앱 실행(🚀), 유튜브 검색(🎵), 구글 검색(🌐), 날씨 정보(🌤️), 점심 추천(🍱), 볼륨 조절(🔊)이 가능하다고 안내해라."
    )

    PETS_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pets.json")

    @classmethod
    def load_pets_info(cls):
        if os.path.exists(cls.PETS_JSON_PATH):
            try:
                with open(cls.PETS_JSON_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    @classmethod
    def get_system_instruction(cls, pet_key: str) -> str:
        pets_data = cls.load_pets_info()
        pet_info = pets_data.get(pet_key, {})

        species = pet_info.get("species", f"{pet_key.replace('_', ' ').title()} 펫")
        tone = pet_info.get("tone", "다정하고 친절한 성격")
        speech_style = pet_info.get("speech_style", "다정한 한국어 어투")

        persona_note = (
            f"[캐릭터 정체성 및 말투 규격]\n"
            f"- 캐릭터 종류: {species}\n"
            f"- 성격 특징: {tone}\n"
            f"- 지정 어미 스타일: {speech_style}\n\n"
            f"⚠️ [어미 일관성 엄격 규칙]\n"
            f"- 답변 시 반드시 지정된 어미 스타일({speech_style})만을 100% 처음부터 끝까지 일관되게 유지하십시오.\n"
            f"- 대화 턴이 바뀌거나 기능 툴을 실행하더라도 존댓말과 반말을 절대 섞거나 말투 연령대를 바꾸지 마십시오."
        )

        return f"{cls.BASE_INSTRUCTION}\n\n{persona_note}"
