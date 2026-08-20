import os
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from core.config_manager import ConfigManager

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class LLMWorkerThread(QThread):
    """Qt 시그널을 이용하여 메인 GUI 스레드로 안전하게 결과를 전달하는 LLM 백그라운드 스레드"""
    response_received = pyqtSignal(str)
    
    def __init__(self, pet_key, user_query):
        super().__init__()
        self.pet_key = pet_key
        self.user_query = user_query
        
    def run(self):
        response_text = LLMClient.ask_pet(self.pet_key, self.user_query)
        self.response_received.emit(response_text)

class LLMClient:
    """Gemini LLM API 통신 및 자연스러운 펫 페르소나 응답 생성 모듈"""
    
    PET_PERSONAS = {
        "fox_orange": (
            "너는 사용자의 바탕화면에 살고 있는 앙증맞고 귀여운 아기 여우 펫이다. "
            "과한 어미 남발을 하지 않고, 발랄하면서도 다정하게 1~2문장 이내의 완결된 문장으로 한국어로 답변해라."
        ),
        "owl_white": (
            "너는 사용자의 바탕화면에 살고 있는 조용하고 지혜롭고 듬직한 복슬복슬 하얀 부엉이 펫이다. "
            "과한 어미 남발을 하지 않고, 차분하고 위트 있게 1~2문장 이내의 완결된 문장으로 한국어로 답변해라."
        )
    }

    @classmethod
    def get_api_key(cls):
        config = ConfigManager.load_config()
        saved_key = config.get("gemini_api_key", "").strip()
        if saved_key:
            return saved_key
        return os.environ.get("GEMINI_API_KEY", "").strip()

    @classmethod
    def ask_pet(cls, pet_key, user_query):
        api_key = cls.get_api_key()
        system_instruction = cls.PET_PERSONAS.get(pet_key, cls.PET_PERSONAS["owl_white"])
        
        if not api_key:
            return "🔑 Gemini API 키가 입력되지 않았어! 펫 우클릭 ➔ [🔑 API 키 설정]에서 키를 넣어줘!"

        config = ConfigManager.load_config()
        model_name = config.get("llm_model", "gemini-3.1-flash-lite").strip()
        
        deprecated_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash"]
        if model_name in deprecated_models:
            model_name = "gemini-3.1-flash-lite"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System Note: {system_instruction}\n\nUser Question: {user_query}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 400
            }
        }
        
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return text
            else:
                try:
                    err_json = res.json()
                    err_msg = err_json.get("error", {}).get("message", f"HTTP {res.status_code}")
                    return f"오류 ({res.status_code}): {err_msg}"
                except Exception:
                    return f"음... 생각 중에 오류가 났어. (코드: {res.status_code})"
        except Exception as e:
            return f"통신에 약간 차질이 생겼어. ({str(e)})"
