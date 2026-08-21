import os
import json
from core.config_manager import ConfigManager

class PersonaBuilder:
    """펫의 키워드(종류, 성격/말투)와 중앙 프롬프트 지침을 결합하여 systemInstruction을 만드는 모듈"""

    BASE_INSTRUCTION = (
        "너는 사용자의 바탕화면에 살고 있는 픽셀 데스크톱 컴패니언 펫이다.\n"
        "🚨 [행동 및 도구 호출 절대 수칙 - 말과 행동 일치 규칙]\n"
        "1. 사용자가 구글/유튜브 검색, 날씨 조회, 타이머 설정, 응용 프로그램(메모장, 계산기 등) 실행, PC 잠금/볼륨 조절을 요청하거나 언급할 때는 "
        "절대로 말로만 '구글 검색창을 띄워드릴게요', '메모장을 엽니다', '잠시만 기다려주세요' 같은 시늉/거짓말 대사를 1글자도 출력하지 마십시오!\n"
        "2. 반드시 해당하는 도구(search_google, search_youtube, launch_app, get_weather, set_timer 등)를 직접 호출하여 행동(Function Call)으로 실천해야 합니다.\n"
        "3. 만약 툴 도구를 호출하지 않고 말로만 '검색창을 띄워드릴게요' 등의 대사를 하면 치명적인 오류입니다. 구글/유튜브 검색이나 정보 조회를 말할 때는 100% search_google 또는 search_youtube 도구만을 즉시 호출하십시오!\n"
        "4. 대답은 2~3문장 이내로 친절하고 다정하게 대화를 나누어라."
    )

    PROMPT_BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "system_base.txt")
    PETS_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pets.json")

    @classmethod
    def get_base_instruction(cls) -> str:
        """외부 prompts/system_base.txt 파일이 있으면 읽고, 없으면 기본 지침 리턴"""
        if os.path.exists(cls.PROMPT_BASE_PATH):
            try:
                with open(cls.PROMPT_BASE_PATH, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return content
            except Exception:
                pass
        return cls.BASE_INSTRUCTION

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

        return f"{cls.get_base_instruction()}\n\n{persona_note}"
