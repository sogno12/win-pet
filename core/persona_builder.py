import os
import json
from core.config_manager import ConfigManager

class PersonaBuilder:
    """펫의 키워드(종류, 성격/말투)와 중앙 프롬프트 지침을 결합하여 systemInstruction을 만드는 모듈"""

    BASE_INSTRUCTION = (
        "너는 사용자의 바탕화면에 살고 있는 픽셀 데스크톱 컴패니언 펫이다.\n"
        "- 과한 어미 남발을 하지 않고, 1~2문장 이내의 완결된 한국어로 자연스럽게 대화해라.\n"
        "- 사용자가 PC 제어(화면 잠금, 앱 실행, 볼륨 조절, 구글/유튜브 검색 등)나 정보 조회를 원하면 "
        "말로만 대답하지 말고 반드시 제공된 도구(Tools)를 즉시 호출해라.\n"
        "- 사용자가 할 수 있는 기능이나 역할을 물어보면 화면 잠금(🔒), 앱 실행(🚀), 유튜브 검색(🎵), 구글 검색(🌐), 볼륨 조절(🔊)이 가능하다고 안내해라."
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

        persona_note = (
            f"[캐릭터 정체성 설정]\n"
            f"- 캐릭터 종류: {species}\n"
            f"- 성격 및 말투 스타일: {tone}\n"
            f"위 정체성 성격에 맞게 답변해라."
        )

        return f"{cls.BASE_INSTRUCTION}\n\n{persona_note}"
