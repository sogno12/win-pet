import random
import requests
from urllib.parse import quote
from core.logger import PetLogger

class InfoAgent:
    """실시간 날씨 정보 및 점심 메뉴 추천을 담당하는 정보 탐색 모듈"""

    # 도시별 위도/경도 프리셋 (Open-Meteo API용)
    CITY_COORDS = {
        "서울": (37.5665, 126.9780),
        "부산": (35.1796, 129.0756),
        "인천": (37.4563, 126.7052),
        "대구": (35.8714, 128.6014),
        "광주": (35.1595, 126.8526),
        "대전": (36.3504, 127.3845),
        "울산": (35.5384, 129.3114),
        "수원": (37.2636, 127.0286),
        "제주": (33.4996, 126.5312),
        "성남": (37.4200, 127.1265),
        "고양": (37.6584, 126.8320),
        "용인": (37.2410, 127.1779),
        "창원": (35.2280, 128.6811)
    }

    # WMO 날씨 코드 변환 표
    WMO_WEATHER_CODES = {
        0: "☀️ 맑음",
        1: "🌤️ 대개 맑음",
        2: "⛅ 구름 조금",
        3: "☁️ 흐림",
        45: "🌫️ 안개",
        48: "🌫️ 서리 안개",
        51: "🌦️ 가벼운 이슬비",
        53: "🌦️ 이슬비",
        55: "🌧️ 강한 이슬비",
        61: "🌧️ 약한 비",
        63: "🌧️ 비",
        65: "🌧️ 폭우",
        71: "🌨️ 약한 눈",
        73: "🌨️ 눈",
        75: "❄️ 대설",
        80: "🌦️ 소나기",
        81: "🌧️ 강한 소나기",
        82: "⛈️ 격렬한 소나기",
        95: "🌩️ 뇌우"
    }

    # 카테고리별 점심 메뉴 데이터베이스
    LUNCH_MENU_DB = {
        "한식": ["김치찌개 🍲", "된장찌개 🥘", "제육볶음 🥩", "비빔밥 🥗", "순두부찌개 🍲", "불고기 덮밥 🍚", "갈비탕 🥣", "부대찌개 🥘", "칼국수 🍜", "수제비 🥣"],
        "중식": ["짜장면 🍜", "짬뽕 🌶️", "볶음밥 🍛", "탕수육 🥩", "마파두부 덮밥 🍛", "간짜장 🍜", "울면 🥣"],
        "일식": ["돈카츠 🥩", "라멘 🍜", "연어 덮밥(사케동) 🐟", "초밥 🍣", "가츠동 🍚", "우동 🍜", "소바 🍝"],
        "양식": ["파스타 🍝", "수제 버거 🍔", "돈까스 🥩", "리조또 🧀", "피자 🍕", "스테이크 🥩"],
        "분식": ["떡볶이 🌶️", "김밥 🍙", "라면 🍜", "순대 🍢", "튀김 🍤", "쫄면 🍝"],
        "간편/기타": ["샌드위치 🥪", "샐러드 🥗", "포케 🥗", "쌀국수 🍜", "카레 🍛", "타코 🌮"]
    }

    @classmethod
    def get_weather(cls, location: str = "서울", date_target: str = "today") -> str:
        """Open-Meteo 무료 API를 연동하여 오늘/내일/주간 날씨 및 강수 예보 조회"""
        clean_loc = location.strip()
        coords = cls.CITY_COORDS.get(clean_loc)
        
        if not coords:
            # 기본 서울 좌표 사용
            lat, lon = cls.CITY_COORDS["서울"]
            loc_name = f"{clean_loc}(서울 기준)"
        else:
            lat, lon = coords
            loc_name = clean_loc

        # 7일간의 일간 및 시간별 기상 데이터 동시 수집
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current_weather=true&hourly=precipitation_probability,rain"
            f"&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            f"&forecast_days=7&timezone=Asia%2FTokyo"
        )
        
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                
                # 1. 내일 날씨 요구 시 (tomorrow)
                if date_target == "tomorrow":
                    daily = data.get("daily", {})
                    d_times = daily.get("time", [])
                    if len(d_times) >= 2:
                        tm_max = daily.get("temperature_2m_max", [])[1]
                        tm_min = daily.get("temperature_2m_min", [])[1]
                        tm_wcode = daily.get("weathercode", [])[1]
                        tm_prob = daily.get("precipitation_probability_max", [])[1]
                        tm_desc = cls.WMO_WEATHER_CODES.get(tm_wcode, "🌤️ 맑음")
                        
                        msg = (
                            f"{loc_name} 내일({d_times[1]}) 날씨 정보: "
                            f"상태는 [{tm_desc}], 최고 기온 {tm_max}°C / 최저 기온 {tm_min}°C, "
                            f"최대 강수 확률은 {tm_prob}%입니다."
                        )
                        PetLogger.log_tool("get_weather", {"location": location, "date_target": date_target}, msg)
                        return msg

                # 2. 주간/주말 날씨 요구 시 (weekly)
                elif date_target == "weekly":
                    daily = data.get("daily", {})
                    d_times = daily.get("time", [])
                    d_maxs = daily.get("temperature_2m_max", [])
                    d_mins = daily.get("temperature_2m_min", [])
                    d_wcodes = daily.get("weathercode", [])
                    
                    summaries = []
                    for i in range(min(5, len(d_times))):
                        wdesc = cls.WMO_WEATHER_CODES.get(d_wcodes[i], "맑음")
                        summaries.append(f"{d_times[i]}: {wdesc}({d_mins[i]}~{d_maxs[i]}°C)")
                    
                    msg = f"{loc_name} 향후 5일간 날씨 추이: " + " / ".join(summaries)
                    PetLogger.log_tool("get_weather", {"location": location, "date_target": date_target}, msg)
                    return msg

                # 3. 오늘/현재 날씨 요구 시 (today - 기본값)
                current = data.get("current_weather", {})
                temp = current.get("temperature", "N/A")
                wind = current.get("windspeed", "N/A")
                wcode = current.get("weathercode", 0)
                
                weather_desc = cls.WMO_WEATHER_CODES.get(wcode, "🌤️ 맑음")
                
                hourly = data.get("hourly", {})
                times = hourly.get("time", [])
                precip_prob = hourly.get("precipitation_probability", [])
                
                rain_summary = ""
                if times and precip_prob:
                    rain_times = []
                    # 오늘 24시간 범위 내 비 예보 체크
                    for t, prob in zip(times[:24], precip_prob[:24]):
                        if prob >= 40:
                            hour_str = t.split("T")[-1] if "T" in t else t
                            rain_times.append(f"{hour_str}(확률 {prob}%)")
                    if rain_times:
                        rain_summary = f" [오늘 예상 비 시간대: {', '.join(rain_times[:4])}]"
                    else:
                        rain_summary = " [오늘 당분간 비 예보는 없습니다]"

                msg = f"{loc_name} 오늘 실시간 날씨: 현재 기온 {temp}°C, 상태 [{weather_desc}], 풍속 {wind}km/h.{rain_summary}"
                PetLogger.log_tool("get_weather", {"location": location, "date_target": date_target}, msg)
                return msg
            else:
                msg = f"{loc_name} 날씨 정보를 가져오는 데 실패했습니다 (HTTP {res.status_code})."
                PetLogger.log_error(msg)
                return msg
        except Exception as e:
            msg = f"날씨 정보 조회 중 오류가 발생했습니다: {str(e)}"
            PetLogger.log_error(msg)
            return msg

    @classmethod
    def recommend_lunch(cls, category: str = None) -> str:
        """한식/중식/일식/양식/분식 중 메뉴 추천"""
        if category and category.strip() in cls.LUNCH_MENU_DB:
            cat_name = category.strip()
            menus = cls.LUNCH_MENU_DB[cat_name]
        else:
            all_cats = list(cls.LUNCH_MENU_DB.keys())
            cat_name = random.choice(all_cats)
            menus = cls.LUNCH_MENU_DB[cat_name]

        picked_menu = random.choice(menus)
        msg = f"오늘 추천 점심 메뉴는 [{cat_name}] 카테고리의 '{picked_menu}'입니다! 맛집 찾기가 필요하시면 '맛집 검색해줘'라고 말씀해 주세요."
        PetLogger.log_tool("recommend_lunch", {"category": category}, msg)
        return msg

    @classmethod
    def execute_tool(cls, tool_name: str, args: dict) -> str:
        """도구 이름과 인자를 받아 정보 탐색 기능을 실행합니다."""
        if tool_name == "get_weather":
            return cls.get_weather(
                location=args.get("location", "서울"),
                date_target=args.get("date_target", "today")
            )
        elif tool_name == "recommend_lunch":
            return cls.recommend_lunch(args.get("category", None))
        else:
            msg = f"지원하지 않는 정보 탐색 명령입니다: {tool_name}"
            PetLogger.log_error(msg)
            return msg
