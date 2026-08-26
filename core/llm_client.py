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
                    "description": "Windows 응용 프로그램(메모장/notepad, 계산기/calc, 크롬/chrome, 엣지/edge, 그림판/mspaint, 카카오톡/kakaotalk, 디스코드/discord, 스포티파이/spotify, 작업관리자/taskmgr 등)을 실제 실행합니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "app_name": {
                                "type": "STRING",
                                "description": "실행할 프로그램 이름 (예: 메모장, 계산기, 크롬, 카카오톡, 디스코드 등)"
                            }
                        },
                        "required": ["app_name"]
                    }
                },
                {
                    "name": "close_app",
                    "description": "실행 중인 응용 프로그램(메모장, 계산기, 크롬, 엣지, 카카오톡, 디스코드, 그림판 등)을 안전하게 종료(끄기/닫기)합니다. 사용자가 특정 프로그램을 꺼달라거나 닫아달라고 할 때 호출하세요.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "app_name": {
                                "type": "STRING",
                                "description": "종료할 프로그램 이름 (예: 메모장, 계산기, 크롬, 카카오톡, 디스코드 등)"
                            }
                        },
                        "required": ["app_name"]
                    }
                },
                {
                    "name": "add_schedule",
                    "description": "일정(약속/시작일시) 또는 할 일(TODO/마감일시)을 캘린더에 등록합니다. 사용자가 '내일 3시 미팅', '오늘 6시까지 코딩하기' 등을 말할 때 호출하세요.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "title": {
                                "type": "STRING",
                                "description": "일정 또는 할 일 내용 (예: 팀 미팅, 치과 방문, 장보기 등)"
                            },
                            "date_str": {
                                "type": "STRING",
                                "description": "날짜 (오늘, 내일, 모레, 또는 yyyy/MM/dd)"
                            },
                            "time_str": {
                                "type": "STRING",
                                "description": "시간 (예: 15:00, 오후 3시, ALL_DAY 등)"
                            },
                            "item_type": {
                                "type": "STRING",
                                "enum": ["event", "todo"],
                                "description": "항목 구분 (event: 일정/약속, todo: 할 일/체크리스트)"
                            },
                            "remind_before": {
                                "type": "INTEGER",
                                "description": "사전 알림 시간(분 단위, 기본 10분)"
                            }
                        },
                        "required": ["title"]
                    }
                },
                {
                    "name": "get_today_schedule",
                    "description": "오늘 등록된 일정 및 할 일(TODO) 목록을 조회합니다. 사용자가 '오늘 뭐 해야 돼?', '오늘 일정 알려줘', '할 일 목록' 등을 물어볼 때 호출하세요.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {}
                    }
                },
                {
                    "name": "get_morning_briefing",
                    "description": "오늘 날씨와 오늘의 일정/할 일을 종합한 아침 굿모닝 브리핑을 요청합니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {}
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
                    "description": "일회성 타이머 또는 특정 시각 알람(예: 5분 뒤 화면 잠금, 10분 뒤 메모장 열기, 17:05 알람 등)을 설정합니다. 사용자가 특정 시간 후 PC 제어 동작(화면 잠금, 앱 실행/종료, 볼륨 조절 등) 자동 실행을 요청할 때 action_name과 action_args를 함께 지정할 수 있습니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "minutes": {
                                "type": "NUMBER",
                                "description": "상대적 타이머 분 시간 (예: 5, 10, 30, 60). 특정 시각 알람일 경우 0 설정 가능"
                            },
                            "target_time_str": {
                                "type": "STRING",
                                "description": "특정 알람 시각 (예: '17:05', '05:05', '07:30'). 특정 시각 언급 시 반드시 입력!"
                            },
                            "memo": {
                                "type": "STRING",
                                "description": "타이머 내용 또는 메모 (예: 화면 잠금, 메모장 열기, 알림 등)"
                            },
                            "action_name": {
                                "type": "STRING",
                                "description": "타이머 만료 시 자동으로 실행할 PC 제어 또는 조회 도구 이름 (예: lock_pc, launch_app, close_app, adjust_volume, search_youtube 등). 필요 없으면 생략"
                            },
                            "action_args": {
                                "type": "OBJECT",
                                "description": "action_name 도구 실행 시 전달할 인자 객체 (예: launch_app인 경우 {'app_name': '메모장'}, close_app인 경우 {'app_name': '크롬'})"
                            }
                        }
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
                    
                    # 1. 툴 로직 실제 실행 (InfoAgent / ScheduleAgent / CalendarAgent / PCAgent)
                    if fn_name in ["get_weather", "recommend_lunch"]:
                        exec_result = InfoAgent.execute_tool(fn_name, fn_args)
                    elif fn_name in ["set_timer", "start_pomodoro", "stop_pomodoro"]:
                        from core.schedule_agent import ScheduleAgent
                        exec_result = ScheduleAgent.execute_tool(fn_name, fn_args)
                    elif fn_name in ["add_schedule", "get_today_schedule", "get_morning_briefing"]:
                        from core.calendar_agent import CalendarAgent
                        exec_result = CalendarAgent.execute_tool(fn_name, fn_args)
                    else:
                        exec_result = PCAgent.execute_tool(fn_name, fn_args)
                    
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
                    
                    # 🚨 [행동 세이프티 가드] LLM이 말로만 "검색창을 띄워드릴게요", "메모장을 엽니다" 대사를 치고
                    # 툴을 안 부른 경우, 시스템이 키워드를 자동 감지하여 100% 실시간 강제 브라우저/앱 실행!
                    if any(kw in resp for kw in ["검색창을 띄워", "검색창을 열어", "구글 검색", "검색 결과를 띄워"]):
                        PetLogger.log_tool("SafetyGuard:search_google", {"query": user_query}, "Triggered by keyword fallback")
                        PCAgent.search_google(user_query)
                    elif any(kw in resp for kw in ["유튜브 검색", "유튜브를 띄워", "유튜브를 열어"]):
                        PetLogger.log_tool("SafetyGuard:search_youtube", {"query": user_query}, "Triggered by keyword fallback")
                        PCAgent.search_youtube(user_query)
                    elif any(kw in resp for kw in ["메모장을 띄워", "메모장을 열어", "메모장을 실행"]):
                        PetLogger.log_tool("SafetyGuard:launch_app", {"app_name": "메모장"}, "Triggered by keyword fallback")
                        PCAgent.launch_app("메모장")
                    elif any(kw in resp for kw in ["계산기를 띄워", "계산기를 열어", "계산기를 실행"]):
                        PetLogger.log_tool("SafetyGuard:launch_app", {"app_name": "계산기"}, "Triggered by keyword fallback")
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

