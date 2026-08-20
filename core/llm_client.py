import os
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from core.config_manager import ConfigManager
from core.pc_agent import PCAgent
from core.info_agent import InfoAgent
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
    
    TOOLS_DECLARATION = [
        {
            "functionDeclarations": [
                {
                    "name": "get_weather",
                    "description": "지정한 도시(서울, 부산, 인천, 대구, 광주, 대전, 울산, 수원, 제주 등)의 오늘/내일/주간 날씨, 기온, 강수 확률 및 상태 정보를 조회합니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "location": {
                                "type": "STRING",
                                "description": "조회할 도시 이름 (예: 서울, 부산, 제주, 대전 등)"
                            },
                            "date_target": {
                                "type": "STRING",
                                "enum": ["today", "tomorrow", "weekly"],
                                "description": "날씨 조회 대상 날짜 (today: 오늘/현재, tomorrow: 내일, weekly: 이번주/주말/주간)"
                            }
                        }
                    }
                },
                {
                    "name": "recommend_lunch",
                    "description": "점심 또는 저녁 식사 메뉴(한식, 중식, 일식, 양식, 분식 등)를 다양하게 추천합니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "category": {
                                "type": "STRING",
                                "description": "원하는 음식 카테고리 (한식, 중식, 일식, 양식, 분식 중 선택, 또는 생략)"
                            }
                        }
                    }
                },
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
                    "description": "Windows 응용 프로그램(메모장/notepad, 계산기/calc, 그림판/mspaint, 파일탐색기/explorer, 작업관리자/taskmgr, 크롬/chrome 등)을 실제 실행합니다. 사용자가 메모장을 켜달라거나 메모/기록/저장을 위해 메모장 실행을 요청할 때 무조건 이 함수를 호출하세요.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "app_name": {
                                "type": "STRING",
                                "description": "실행할 앱 이름 (예: 메모장, notepad, 계산기, calc, taskmgr 등)"
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
                },
                {
                    "name": "set_timer",
                    "description": "일회성 타이머/알람을 설정합니다. (예: 10분 뒤 알림, 30분 타이머 설정)",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "minutes": {
                                "type": "NUMBER",
                                "description": "타이머 분 시간 (예: 5, 10, 30, 60)"
                            },
                            "memo": {
                                "type": "STRING",
                                "description": "타이머 내용 또는 메모 (예: 약 먹기, 찌개 끄기, 알림 등)"
                            }
                        },
                        "required": ["minutes"]
                    }
                },
                {
                    "name": "start_pomodoro",
                    "description": "집중 시간과 휴식 시간이 자동 반복되는 포모도로(Pomodoro) 세션을 시작합니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "work_minutes": {
                                "type": "INTEGER",
                                "description": "집중 시간(분) (기본값 25)"
                            },
                            "rest_minutes": {
                                "type": "INTEGER",
                                "description": "휴식 시간(분) (기본값 5)"
                            }
                        }
                    }
                },
                {
                    "name": "stop_pomodoro",
                    "description": "현재 진행 중인 포모도로 타이머 사이클을 중단하거나 끕니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {}
                    }
                }
            ]
        }
    ]

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
                    
                    # 1. 툴 로직 실제 실행 (InfoAgent / ScheduleAgent / PCAgent)
                    if fn_name in ["get_weather", "recommend_lunch"]:
                        exec_result = InfoAgent.execute_tool(fn_name, fn_args)
                    elif fn_name in ["set_timer", "start_pomodoro", "stop_pomodoro"]:
                        from core.schedule_agent import ScheduleAgent
                        exec_result = ScheduleAgent.execute_tool(fn_name, fn_args)
                    else:
                        exec_result = PCAgent.execute_tool(fn_name, fn_args)
                    
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
                        "tools": cls.TOOLS_DECLARATION,
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 300
                        }
                    }

                    try:
                        res2 = requests.post(url, headers=headers, json=pass2_payload, timeout=15)
                        if res2.status_code == 200:
                            data2 = res2.json()
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
                    
                    # 🚨 [행동 세이프티 가드] LLM이 말로만 "검색창을 띄워드릴게요", "메모장을 엽니다" 대사를 치고
                    # 툴을 안 부른 경우, 시스템이 키워드를 자동 감지하여 100% 실시간 강제 브라우저/앱 실행!
                    if any(kw in resp for kw in ["검색창을 띄워", "검색창을 열어", "구글 검색", "검색 결과를 띄워"]):
                        PCAgent.search_google(user_query)
                    elif any(kw in resp for kw in ["유튜브 검색", "유튜브를 띄워", "유튜브를 열어"]):
                        PCAgent.search_youtube(user_query)
                    elif any(kw in resp for kw in ["메모장을 띄워", "메모장을 열어", "메모장을 실행"]):
                        PCAgent.launch_app("메모장")
                    elif any(kw in resp for kw in ["계산기를 띄워", "계산기를 열어", "계산기를 실행"]):
                        PCAgent.launch_app("계산기")

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

