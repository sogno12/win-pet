import os
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from core.config_manager import ConfigManager
from core import tool_registry
from core.logger import PetLogger
from core.persona_builder import PersonaBuilder
from core.memory_agent import MemoryAgent

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
    """Gemini LLM API 통신 및 동적 펫 키워드 페르소나 (2-Pass Function Call + Memory) 응답 생성 모듈"""
    
    @classmethod
    def get_api_key(cls):
        return ConfigManager.get_api_key()

    @classmethod
    def ask_pet(cls, pet_key, user_query):
        PetLogger.log_user(user_query)
        api_key = cls.get_api_key()
        
        if not api_key:
            errMsg = "🔑 Gemini API 키가 입력되지 않았어! 펫 우클릭 ➔ [🔑 API 키 설정]에서 키를 넣어줘!"
            PetLogger.log_error(errMsg)
            return errMsg

        # 메모리 컨텍스트 (시간 힌트 + 선택적 장기기억 + 단기 히스토리) 조립
        from core.status_agent import StatusAgent
        memory_context = MemoryAgent.get_memory_context(user_query)
        status_hint = StatusAgent.get_prompt_hint()
        base_system_instruction = PersonaBuilder.get_system_instruction(pet_key)
        
        system_instruction = f"{base_system_instruction}\n\n[펫의 시공간 대화 기억 컨텍스트]\n{memory_context}\n\n{status_hint}"

        config = ConfigManager.load_config()
        model_name = config.get("llm_model", "gemini-3.1-flash-lite").strip()
        
        deprecated_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash"]
        if model_name in deprecated_models:
            model_name = "gemini-3.1-flash-lite"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}  # 키는 URL이 아닌 헤더로 (예외 메시지/로그 노출 방지)
        
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
            "tools": tool_registry.GEMINI_TOOLS,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 400
            }
        }
        
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                data = res.json()
                usage = data.get("usageMetadata", {})
                if usage:
                    PetLogger.log_api_usage(
                        usage.get("promptTokenCount", 0),
                        usage.get("candidatesTokenCount", 0),
                        usage.get("totalTokenCount", 0),
                        model_name
                    )

                candidate = data.get("candidates", [{}])[0]
                parts = candidate.get("content", {}).get("parts", [])
                
                if not parts:
                    resp = "음... 어떤 말씀을 하셔야 할지 잠시 생각을 잊었나 봐요."
                    PetLogger.log_pet(pet_key, resp)
                    return resp
                
                fn_part = None
                text_part = None
                for pt in parts:
                    if "functionCall" in pt:
                        fn_part = pt
                        break
                    elif "text" in pt and not text_part:
                        text_part = pt
                
                # Function Call 발생 시 2-Pass 아키텍처 수행 (Gemini 표준)
                if fn_part:
                    fn_call = fn_part["functionCall"]
                    fn_name = fn_call.get("name", "")
                    fn_args = fn_call.get("args", {})
                    
                    # 1. 툴 로직 실제 실행 (core/tool_registry.py가 담당 에이전트로 연결)
                    exec_result = tool_registry.execute(fn_name, fn_args)
                    
                    PetLogger.log_tool(fn_name, fn_args, str(exec_result))

                    # 2. 2-Pass Gemini API 호출 (Function Response 전달하여 펫 성격별 피드백 대사 자동 수신)
                    contents.append({
                        "role": "model",
                        "parts": [fn_part]
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
                        "tools": tool_registry.GEMINI_TOOLS,
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 300
                        }
                    }

                    try:
                        res2 = requests.post(url, headers=headers, json=pass2_payload, timeout=15)
                        if res2.status_code == 200:
                            data2 = res2.json()
                            usage2 = data2.get("usageMetadata", {})
                            if usage2:
                                PetLogger.log_api_usage(
                                    usage2.get("promptTokenCount", 0),
                                    usage2.get("candidatesTokenCount", 0),
                                    usage2.get("totalTokenCount", 0),
                                    f"{model_name}-pass2"
                                )
                            parts2 = data2.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                            if parts2:
                                for pt2 in parts2:
                                    if "text" in pt2:
                                        resp2 = pt2["text"].strip()
                                        PetLogger.log_pet(pet_key, resp2)
                                        MemoryAgent.save_interaction(user_query, resp2)
                                        StatusAgent.interact("chat")
                                        return resp2
                    except Exception as e2:
                        PetLogger.log_error(f"2-Pass Exception: {e2}")

                    # 2-Pass 응답 실패 시 툴 실행 결과 직관적 폴백 리턴 (예: 날씨 정보 텍스트 반환)
                    PetLogger.log_pet(pet_key, exec_result)
                    MemoryAgent.save_interaction(user_query, exec_result)
                    StatusAgent.interact("chat")
                    return exec_result
                
                # 일반 텍스트 응답 시
                elif text_part:
                    resp = text_part["text"].strip()
                    
                    PetLogger.log_pet(pet_key, resp)
                    MemoryAgent.save_interaction(user_query, resp)
                    StatusAgent.interact("chat")
                    return resp
                
                resp = "답변을 정확히 이해하지 못했어요."
                PetLogger.log_pet(pet_key, resp)
                MemoryAgent.save_interaction(user_query, resp)
                StatusAgent.interact("chat")
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

