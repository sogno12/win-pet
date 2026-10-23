"""LLM 도구(Function Calling) 선언과 실행을 한곳에서 관리하는 레지스트리.

도구를 추가하려면
1. 담당 에이전트의 execute_tool()에 분기를 추가하고
2. 아래 TOOLS에 (에이전트 키, 선언) 항목을 하나 추가하세요.

llm_client(대화)와 schedule_agent(타이머 예약 액션)는 모두 이 파일만 봅니다.
"""
import importlib
from core.logger import PetLogger

# 에이전트 키 -> (모듈, 클래스)
# 실행할 때 import 해서 Qt 객체 생성 시점을 늦추고 순환 import를 피함
#
# ⚠️ 주의: 문자열로 동적 import 하므로 PyInstaller가 이 모듈들을 자동으로 찾지 못함.
#   - 에이전트 모듈은 반드시 core 패키지 안에 둘 것 (build_portable.py의 --collect-submodules=core 로 포함됨)
#   - core 밖 모듈을 추가해야 하면 build_portable.py에 --hidden-import 를 함께 추가할 것
#   - build_portable.py의 verify_bundled_modules()가 빌드 후 누락 여부를 검사함
_AGENTS = {
    "info": ("core.info_agent", "InfoAgent"),
    "pc": ("core.pc_agent", "PCAgent"),
    "schedule": ("core.schedule_agent", "ScheduleAgent"),
    "calendar": ("core.calendar_agent", "CalendarAgent"),
    "asset": ("core.asset_agent", "AssetAgent"),
}

# 타이머 만료 시 자동 실행을 허용하는 에이전트 (조회와 PC 제어만)
TIMER_ACTION_AGENTS = {"info", "pc"}

TOOLS = [
    # --- 정보 조회 (InfoAgent)
    ("info", {
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
    }),
    ("info", {
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
    }),
    # --- PC 제어 (PCAgent)
    ("pc", {
        "name": "lock_pc",
        "description": "Windows PC 화면을 잠금 상태로 전환합니다.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    }),
    ("pc", {
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
    }),
    ("pc", {
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
    }),
    ("pc", {
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
    }),
    ("pc", {
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
    }),
    ("pc", {
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
    }),
    ("pc", {
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
    }),
    # --- 타이머 / 포모도로 (ScheduleAgent)
    ("schedule", {
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
    }),
    ("schedule", {
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
    }),
    ("schedule", {
        "name": "stop_pomodoro",
        "description": "현재 진행 중인 포모도로 타이머 사이클을 중단하거나 끕니다.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    }),
    # --- 일정 / 할 일 (CalendarAgent)
    ("calendar", {
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
    }),
    ("calendar", {
        "name": "get_today_schedule",
        "description": "오늘 등록된 일정 및 할 일(TODO) 목록을 조회합니다. 사용자가 '오늘 뭐 해야 돼?', '오늘 일정 알려줘', '할 일 목록' 등을 물어볼 때 호출하세요.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    }),
    ("calendar", {
        "name": "get_morning_briefing",
        "description": "오늘 날씨와 오늘의 일정/할 일을 종합한 아침 굿모닝 브리핑을 요청합니다.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    }),
    # --- 올인윈 자산관리 (AssetAgent)
    ("asset", {
        "name": "get_asset_summary",
        "description": "사용자의 All-in-Win 자산관리 포트폴리오 현황(총 평가자산, 총 투자원금, 누적 손익, 수익률, 비중 상위 자산, 자산군별 비중)을 조회합니다. 사용자가 '내 자산 얼마야?', '자산 현황 알려줘', '수익률 어때?', '포트폴리오 비중' 등을 물어볼 때 호출하세요.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    }),
    ("asset", {
        "name": "open_asset_dashboard",
        "description": "All-in-Win 자산관리 웹 대시보드(http://127.0.0.1:8000)를 웹 브라우저로 엽니다. 사용자가 '올인윈 켜줘', '자산관리 대시보드 열어줘', '포트폴리오 화면 띄워줘' 등을 요청할 때 호출하세요.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    }),
]

_AGENT_OF = {decl["name"]: agent for agent, decl in TOOLS}
assert len(_AGENT_OF) == len(TOOLS), "도구 이름이 중복됐습니다"
assert set(_AGENT_OF.values()) <= set(_AGENTS), "등록되지 않은 에이전트 키가 있습니다"

# Gemini API payload의 "tools" 값
GEMINI_TOOLS = [{"functionDeclarations": [decl for _, decl in TOOLS]}]


def execute(name: str, args: dict, allowed_agents=None) -> str:
    """도구 이름에 맞는 에이전트의 execute_tool()을 호출합니다.

    allowed_agents를 주면 그 에이전트의 도구만 실행합니다 (타이머 예약 액션용).
    """
    agent = _AGENT_OF.get(name)
    if agent is None or (allowed_agents is not None and agent not in allowed_agents):
        msg = f"지원하지 않는 도구입니다: {name}"
        PetLogger.log_error(msg)
        return msg
    module_name, class_name = _AGENTS[agent]
    agent_cls = getattr(importlib.import_module(module_name), class_name)
    return agent_cls.execute_tool(name, args or {})
