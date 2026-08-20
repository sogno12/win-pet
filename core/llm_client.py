import os
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from core.config_manager import ConfigManager
from core.pc_agent import PCAgent
from core.logger import PetLogger
from core.persona_builder import PersonaBuilder

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
    """Gemini LLM API 통신 및 동적 펫 키워드 페르소나 (2-Pass Function Call) 응답 생성 모듈"""
    
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
                    "name": "search_google",
                    "description": "구글(Google)에서 검색어로 정보(전시회, 뉴스, 맛집, 키워드 등)를 검색하여 웹 브라우저로 검색 결과 페이지를 엽니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "query": {
                                "type": "STRING",
                                "description": "구글에서 검색할 검색 키워드 (예: 고야전, 오늘 날씨 등)"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "open_website",
                    "description": "지정한 웹사이트 URL 주소(예: naver.com, google.com 등)를 웹 브라우저로 엽니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "url_or_query": {
                                "type": "STRING",
                                "description": "방문할 웹사이트 URL 주소"
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
    def ask_pet(cls, pet_key, user_query):
        PetLogger.log_user(user_query)
        api_key = cls.get_api_key()
        
        if not api_key:
            errMsg = "🔑 Gemini API 키가 입력되지 않았어! 펫 우클릭 ➔ [🔑 API 키 설정]에서 키를 넣어줘!"
            PetLogger.log_error(errMsg)
            return errMsg

        system_instruction = PersonaBuilder.get_system_instruction(pet_key)

        config = ConfigManager.load_config()
        model_name = config.get("llm_model", "gemini-3.1-flash-lite").strip()
        
        deprecated_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash"]
        if model_name in deprecated_models:
            model_name = "gemini-3.1-flash-lite"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        contents = [
            {
                "role": "user",
                "parts": [{"text": user_query}]
            }
        ]

        payload = {
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": contents,
            "tools": cls.TOOLS_DECLARATION,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 400
            }
        }
        
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                data = res.json()
                candidate = data.get("candidates", [{}])[0]
                parts = candidate.get("content", {}).get("parts", [])
                
                if not parts:
                    resp = "음... 어떤 말씀을 하셔야 할지 잠시 생각을 잊었나 봐요."
                    PetLogger.log_pet(pet_key, resp)
                    return resp
                
                first_part = parts[0]
                
                # Function Call 발생 시 2-Pass 아키텍처 수행 (Gemini 표준)
                if "functionCall" in first_part:
                    fn_call = first_part["functionCall"]
                    fn_name = fn_call.get("name", "")
                    fn_args = fn_call.get("args", {})
                    
                    # 1. 툴 로직 실제 실행
                    exec_result = PCAgent.execute_tool(fn_name, fn_args)
                    
                    # 2. 2-Pass Gemini API 호출 (Function Response 전달하여 펫 성격별 피드백 대사 자동 수신)
                    contents.append({
                        "role": "model",
                        "parts": [first_part]
                    })
                    contents.append({
                        "role": "user",
                        "parts": [
                            {
                                "functionResponse": {
                                    "name": fn_name,
                                    "response": {
                                        "name": fn_name,
                                        "output": {"result": exec_result}
                                    }
                                }
                            }
                        ]
                    })

                    pass2_payload = {
                        "systemInstruction": {
                            "parts": [{"text": system_instruction}]
                        },
                        "contents": contents,
                        "tools": cls.TOOLS_DECLARATION,
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 300
                        }
                    }

                    res2 = requests.post(url, headers=headers, json=pass2_payload, timeout=15)
                    if res2.status_code == 200:
                        data2 = res2.json()
                        parts2 = data2.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        if parts2 and "text" in parts2[0]:
                            resp2 = parts2[0]["text"].strip()
                            PetLogger.log_pet(pet_key, resp2)
                            return resp2

                    # 2-Pass 응답 실패 시 폴백
                    PetLogger.log_pet(pet_key, exec_result)
                    return exec_result
                
                # 일반 텍스트 응답 시
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
