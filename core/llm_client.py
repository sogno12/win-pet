import os
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from core.config_manager import ConfigManager
from core.pc_agent import PCAgent
from core.logger import PetLogger

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
            "과한 어미 남발을 하지 않고, 발랄하면서도 다정하게 1~2문장 이내의 완결된 문장으로 한국어로 답변해라. "
            "사용자가 PC 제어(화면 잠금, 프로그램 실행, 볼륨 조절, 유튜브/웹 검색 등)를 원하면 텍스트로만 흉내 내지 말고 반드시 제공된 도구(Tools)를 호출해라. "
            "만약 사용자가 할 수 있는 기능이나 역할을 물어보면 화면 잠금(🔒), 메모장/계산기/그림판/탐색기/작업관리자 실행(🚀), 유튜브 검색/재생(🎵), 구글/웹 검색(🌐), 볼륨/음소거 조절(🔊)이 가능하다고 앙증맞게 안내해라."
        ),
        "owl_white": (
            "너는 사용자의 바탕화면에 살고 있는 조용하고 지혜롭고 듬직한 복슬복슬 하얀 부엉이 펫이다. "
            "과한 어미 남발을 하지 않고, 차분하고 위트 있게 1~2문장 이내의 완결된 문장으로 한국어로 답변해라. "
            "사용자가 PC 제어(화면 잠금, 프로그램 실행, 볼륨 조절, 유튜브/웹 검색 등)를 원하면 텍스트로만 흉내 내지 말고 반드시 제공된 도구(Tools)를 호출해라. "
            "만약 사용자가 할 수 있는 기능이나 역할을 물어보면 화면 잠금(🔒), 메모장/계산기/그림판/탐색기/작업관리자 실행(🚀), 유튜브 검색/재생(🎵), 구글/웹 검색(🌐), 볼륨/음소거 조절(🔊)을 도울 수 있다고 차분하고 듬직하게 안내해라."
        )
    }

    TOOLS_DECLARATION = [
        {
            "functionDeclarations": [
                {
                    "name": "lock_pc",
                    "description": "Windows PC 화면을 잠금 상태로 전환합니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {}
                    }
                },
                {
                    "name": "launch_app",
                    "description": "응용 프로그램(메모장, 계산기, 그림판, 파일 탐색기, 작업관리자 등)을 실행합니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "app_name": {
                                "type": "STRING",
                                "description": "실행할 앱 이름 (예: notepad, calc, mspaint, explorer, taskmgr 등)"
                            }
                        },
                        "required": ["app_name"]
                    }
                },
                {
                    "name": "search_youtube",
                    "description": "유튜브에서 지정된 검색어로 동영상이나 음악을 검색하여 브라우저에서 재생합니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "query": {
                                "type": "STRING",
                                "description": "유튜브에서 검색할 키워드 또는 노래 제목"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "open_website",
                    "description": "웹사이트 주소를 열거나 지정한 검색어로 구글 검색을 수행합니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "url_or_query": {
                                "type": "STRING",
                                "description": "방문할 웹사이트 URL 또는 검색어"
                            }
                        },
                        "required": ["url_or_query"]
                    }
                },
                {
                    "name": "adjust_volume",
                    "description": "시스템 볼륨을 조절하거나 음소거합니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "action": {
                                "type": "STRING",
                                "enum": ["mute", "unmute", "up", "down"],
                                "description": "볼륨 동작 (mute: 음소거, up: 볼륨 올림, down: 볼륨 줄임)"
                            }
                        },
                        "required": ["action"]
                    }
                }
            ]
        }
    ]

    @classmethod
    def get_api_key(cls):
        config = ConfigManager.load_config()
        saved_key = config.get("gemini_api_key", "").strip()
        if saved_key:
            return saved_key
        return os.environ.get("GEMINI_API_KEY", "").strip()

    @classmethod
    def format_action_response(cls, pet_key, tool_name, args, result_msg):
        """도구 실행 후 펫 페르소나에 부합하는 피드백 멘트 반환"""
        if pet_key == "fox_orange":
            prefix = "🦊 "
            if tool_name == "lock_pc":
                return f"{prefix}주인님! PC 화면을 즉시 잠갔어요. 자물쇠를 꼭 채웠답니다! 🔒"
            elif tool_name == "launch_app":
                app = args.get("app_name", "프로그램")
                return f"{prefix}요청하신 '{app}'(을)를 빠르게 켜드렸어요! 🚀"
            elif tool_name == "search_youtube":
                query = args.get("query", "")
                return f"{prefix}유튜브에서 '{query}'(을)를 찾아 웹 브라우저로 띄워드렸어요! 🎵"
            elif tool_name == "open_website":
                target = args.get("url_or_query", "")
                return f"{prefix}'{target}' 페이지를 신나게 열었어요! 🌐"
            elif tool_name == "adjust_volume":
                return f"{prefix}요청하신 대로 소리/볼륨 조절을 완료했어요! 🔊"
        else:
            prefix = "🦉 "
            if tool_name == "lock_pc":
                return f"{prefix}주인님, 요청하신 대로 안전하게 PC 화면을 잠갔습니다. 🔒"
            elif tool_name == "launch_app":
                app = args.get("app_name", "프로그램")
                return f"{prefix}'{app}' 응용 프로그램을 성공적으로 실행했습니다. 🚀"
            elif tool_name == "search_youtube":
                query = args.get("query", "")
                return f"{prefix}유튜브에서 '{query}' 검색 결과를 띄워드렸습니다. 🎵"
            elif tool_name == "open_website":
                target = args.get("url_or_query", "")
                return f"{prefix}'{target}' 검색 및 브라우저 열기를 완료했습니다. 🌐"
            elif tool_name == "adjust_volume":
                return f"{prefix}시스템 볼륨 설정을 성공적으로 변경했습니다. 🔊"
        return f"{prefix}{result_msg}"

    @classmethod
    def ask_pet(cls, pet_key, user_query):
        PetLogger.log_user(user_query)
        api_key = cls.get_api_key()
        system_instruction = cls.PET_PERSONAS.get(pet_key, cls.PET_PERSONAS["owl_white"])
        
        if not api_key:
            errMsg = "🔑 Gemini API 키가 입력되지 않았어! 펫 우클릭 ➔ [🔑 API 키 설정]에서 키를 넣어줘!"
            PetLogger.log_error(errMsg)
            return errMsg

        config = ConfigManager.load_config()
        model_name = config.get("llm_model", "gemini-3.1-flash-lite").strip()
        
        deprecated_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash"]
        if model_name in deprecated_models:
            model_name = "gemini-3.1-flash-lite"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        # systemInstruction을 루트 파라미터로 올바르게 선언하여 Function Calling 인식률 최적화
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_query}]
                }
            ],
            "tools": cls.TOOLS_DECLARATION,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 400
            }
        }
        
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                candidate = data.get("candidates", [{}])[0]
                parts = candidate.get("content", {}).get("parts", [])
                
                if not parts:
                    resp = "음... 어떤 말씀을 하셔야 할지 잠시 생각을 잊었나 봐요."
                    PetLogger.log_pet(pet_key, resp)
                    return resp
                
                first_part = parts[0]
                # Function Call 발생 시
                if "functionCall" in first_part:
                    fn_call = first_part["functionCall"]
                    fn_name = fn_call.get("name", "")
                    fn_args = fn_call.get("args", {})
                    
                    exec_result = PCAgent.execute_tool(fn_name, fn_args)
                    resp = cls.format_action_response(pet_key, fn_name, fn_args, exec_result)
                    PetLogger.log_pet(pet_key, resp)
                    return resp
                
                # 텍스트 응답 시
                elif "text" in first_part:
                    resp = first_part["text"].strip()
                    PetLogger.log_pet(pet_key, resp)
                    return resp
                
                resp = "답변을 정확히 이해하지 못했어요."
                PetLogger.log_pet(pet_key, resp)
                return resp
            else:
                try:
                    err_json = res.json()
                    err_msg = err_json.get("error", {}).get("message", f"HTTP {res.status_code}")
                    errMsg = f"오류 ({res.status_code}): {err_msg}"
                except Exception:
                    errMsg = f"음... 생각 중에 오류가 났어. (코드: {res.status_code})"
                PetLogger.log_error(errMsg)
                return errMsg
        except Exception as e:
            errMsg = f"통신에 약간 차질이 생겼어. ({str(e)})"
            PetLogger.log_error(errMsg)
            return errMsg


