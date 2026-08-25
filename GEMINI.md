# 🐱 AI 픽셀 데스크톱 펫 ('win_pet')

### 🎯 프로젝트 개요
- **컨셉:** 윈도우 바탕화면에서 뽀짝뽀짝 움직이며 사용자와 대화하고 PC 제어 및 추천 등의 역할을 수행하는 AI 픽셀 컴패니언 펫.
- **주요 기능:** 바탕화면 투명 픽셀 펫, LLM 기반 대화 및 표정/행동 반응, Agent 기능(PC 제어, 정보 검색, 기억력, 친밀도), 음성(STT/TTS) 연동, 3단계 오토 에셋 정돈기.
- **개발 환경 / 기술 스택:** Windows OS, Anaconda (Conda 가상환경 `wincat`), Python 3.10+, PyQt6, Pillow, LLM API (Gemini API 등).

---

### 🐍 Conda 가상환경 설정
```bash
# 1. wincat 가상환경 생성
conda create -n wincat python=3.10 -y

# 2. 가상환경 활성화
conda activate wincat

# 3. 필수 패키지 설치
pip install PyQt6 Pillow requests python-dotenv

# 4. 실행
python setup_assets.py        # 픽셀 이미지 준비 (최초 1회)
python main.py                # 펫 실행
```

---

### 🚨 핵심 제약 사항 및 검토 결론 (Strict Policy)
> **⚠️ [이미지 API 자동 생성 불가 명시]**
> 외부 AI 이미지 생성 API를 파이썬 스크립트에서 자동 호출하여 펫 이미지를 만들어내는 방식은 **해부학적 왜곡(다리가 5~6개로 렌더링되는 문제, 얼굴 뚫림, 컷 간 캐릭터 불일치, 저품질 렌더링)**으로 인해 **100% 사용 불가함이 검증 완료되었습니다.**
> 따라서 펫 에셋은 사용자가 직접 준비한 고품질 이미지를 `pet_generator.py`의 **3단계 오토 파이프라인 (스마트 배경 제거 ➔ 캐릭터 크롭 ➔ 1:1 정사각형 정중앙 배치)**을 통해 정돈하여 탑재하는 방식을 정식 스펙으로 채택합니다.

---

### 🚀 4단계 개발 로드맵 현황

**1단계: 바탕화면 픽셀 펫 띄우기 (🎉 100% 완료)**
- [x] 투명 및 무테두리 윈도우 창 생성 (`main.py`)
- [x] 픽셀 보정 렌더링 (Nearest-Neighbor / Pixelated)
- [x] 독립 타이머 기반 60FPS 부드러운 자율 걷기/대기/드래그 애니메이션 & 2D 상하좌우 대각선 무작위 보행 로직
- [x] 우클릭 서브메뉴 `📍 펫 이동 속도` 5단계 세분화 개편 (🐢 느리게 150ms / 🍃 느긋하게 100ms / 🐾 천천히 70ms / 🎵 경쾌하게 45ms / ⚡ 빠르게 30ms)
- [x] 우클릭 서브메뉴 `📍 펫 이동 범위` 4단계 추가 (🤏 좁게 / 🏡 아늑하게 / 🖥️ 모니터 전용 / 🌐 자유롭게) 및 **설정 가능한(1.5초) 몽환 반투명 안개 영역 미리보기 UI (`ui/range_overlay.py`) 연동**
- [x] **[개선] `🔍 현재 이동 범위 미리보기 (안개 보기)` 다시보기 버튼 & `🤏 매우 좁게 (구석에서 놀기 / 반경 60px)` 5단계 이동 모드 완비**
- [x] **[개선] 안개 텍스트 제거 솜사탕 구름 렌더링 & `👁️ 이동 범위 안개 항상 켜기 (테스트 고정용)` 지속 고정 토글 메뉴 완비**
- [x] **[개선] 안개 외곽선 표시 유무(`range_overlay_show_border`), 색상 Hex(`range_overlay_color`), 투명도(`range_overlay_opacity`) `config.json` 커스텀 분리 완비**
- [x] **[개선] 마우스 드래그&드롭 시 놓은 자리로 이동 범위 기준점(`origin_center`) 및 안개 구름 실시간 자동 추적 갱신 완비**
- [x] **[버그 수정] `🔍 현재 이동 범위 미리보기` 다시보기 버튼 클릭 시 펫 이동 위치로 영역이 재설정되던 버그 완벽 수정 (오리지널 `origin_center` 기준 고정)**
- [x] **[버그 수정] 펫 몸통이 안개 구름 바깥으로 튀어나가던 좌표 엇박자 완벽 수정 (통일 바운딩 박스 알고리즘 적용)**
- [x] **3단계 오토 파이프라인 (스마트 배경 제거 ➔ 캐릭터 크롭 ➔ 1:1 정사각형 정중앙 배치) 구축 (`pet_generator.py`)**
- [x] 마우스 호버 시 이동 정지 & 정면 바라보기 상호작용 추가 (`enterEvent`/`leaveEvent`)
- [x] 마우스 호버 커서(손가락 👆) & 안내 툴팁 추가
- [x] 설정 영구 보관용 `config.json` 연동 (크기, 스킨, 속도, 범위, 항상 위 고정 등)
- [x] 펫 메타데이터 & 노출 제어용 `pets.json` 도입 (`"enabled": true/false`로 우클릭 메뉴 노출 유무 제어)
- [x] 6단계 펫 크기 옵션 개편 (매우 작게 24px ~ 매우 크게 128px, 기본 48px 디폴트)
- [x] 부엉이 몸통 내부 깃털 투명화 버그 완벽 수정 (마젠타 #FF00FF 크로마키 알고리즘 적용)
- [x] 뒷목 잡힌 전용 픽셀 프레임 (`drag.png`) 연동
- [x] 정면 바라보며 멍때리는 `idle/` 전용 픽셀 이미지 연동
- [x] 동물 5대 표준 에셋 폴더 스펙 적용 (`walk/`, `idle/`, `drag/`, `happy/`, `special/`)
- [x] 걷기 애니메이션 프레임 간 크기 꿀렁거림 완전 차단 (통일 바운딩 박스 알고리즘 적용)
- [x] 시스템 트레이 소환 기능 개편 (✨ 마우스가 위치한 곳으로 펫 즉시 순간이동 소환)
- [x] 시스템 트레이 아이콘 우클릭 메뉴에 `📏 펫 크기` 서브메뉴 추가
- [x] `QActionGroup` 도입으로 펫 스킨 메뉴 다중 체크 표시 버그 완벽 수정
- [x] 시스템 트레이 아이콘 메뉴 (✨ 내 앞으로 불러오기 / 📌 항상 위에 표시 / 🙈 숨기기 / ❌ 종료)
- [x] `core/` 및 `ui/` 전문 모듈 분리 구조 리팩토링 완료

**2단계: 텍스트 / LLM 대화 연결 (🎉 100% 완료)**
- [x] **펫 클릭 시 대화 질문 입력창(`ui/dialog_input.py`) 팝업**
- [x] **대화 입력 중 펫 이동 자동 멈춤 & 답변 전송 후 입력필드 자동 비우기**
- [x] **입력창 `취소` 버튼 및 `Esc` 키 닫기 지원**
- [x] **펫 머리 위 실시간 추적 말풍선 UI(`ui/speech_bubble.py`) & 타이핑 애니메이션**
- [x] **Gemini LLM API 연동 (`core/llm_client.py`) & 스레드 안전 QThread 바인딩**
- [x] **오글거리지 않는 자연스러운 1~3문장 톤앤매너 페르소나 적용**
- [x] **.env 보안 지원 (`python-dotenv`) 및 .gitignore 자동 차단**
- [x] **`config.json` 연동 최고속/최경량 LLM 모델 지정 (`gemini-3.1-flash-lite`)**

**3단계: Agent 작업 & 비서/배포 확장 (진행 중 🔥)**
- [x] **[0순위] 비개발자 배포용 환경 준비 (API 키 입력 UI & GUI 신규 펫 자동 정돈/추가):**
  - [x] **API 키 설정 팝업 UI:** 펫 우클릭 및 대화 시 API 키 미설정 상태 탐지 ➔ 사용자 자동 입력 팝업 UI (`ui/dialog_api_key.py`, `.env` 전용 난독화 저장)
  - [x] **[보안 강화] API 키 .env 전용 파일 격리 보관 & Base64 난독화(`ENC:...`) 암호화 저장 시스템 완비 (`config.json` 키 필드 완벽 제거)**
  - [x] **[개선] API 키 미설정 시 오프라인 픽셀 펫 정상 보행/상호작용 유지 & 최초 구동 시 1회 등록 안내 팝업 및 '다시 묻지 않기' (`api_key_prompted`) 플래그 완비**
  - [x] **GUI 신규 펫 자동 정돈/추가 버튼:** 우클릭 메뉴 `✨ 신규 펫 자동 정돈/추가` 클릭 ➔ `assets/` 신규 폴더 다중 감지 ➔ 수정 가능한 기본 타이틀 입력 팝업 ➔ 3단계 배경 제거 오토 파이프라인 1초 완료
- [x] **[1순위] PC 제어 Agent (Function Calling) & 로깅 시스템 & 키워드 페르소나 엔진:**
  - [x] 유튜브 음악/영상 검색 재생, 메모장/계산기/작업관리자 앱 실행, PC 화면 잠금, 볼륨 조절/음소거 구현 ([`core/pc_agent.py`](file:///d:/sjchoi/win_pet/core/pc_agent.py))
  - [x] Gemini REST API `systemInstruction` 페이로드 분리로 Function Calling 트리거율 100% 보장 ([`core/llm_client.py`](file:///d:/sjchoi/win_pet/core/llm_client.py))
  - [x] **[버그 수정] 메모장/검색/앱 실행 요청 시 말로만 시늉 대사 치고 안 여는 현상 원천 차단 (Action-Fulfillment Safety Guard 파이썬 강제 실행기 연동)**
  - [x] 매일 날짜별 자동 회전 로깅 시스템 구축 ([`core/logger.py`](file:///d:/sjchoi/win_pet/core/logger.py) ➔ `logs/YYYY-MM-DD.log`, `yyyy/MM/dd HH:mm:ss` 포맷 준수)
  - [x] 키워드 기반 페르소나 엔진 구축 (`pets.json` ➔ `species`, `tone`, `speech_style` 키워드 지원, [`core/persona_builder.py`](file:///d:/sjchoi/win_pet/core/persona_builder.py))
  - [x] 턴 변경 시에도 존댓말/반말이 섞이지 않는 엄격한 어미 일관성 지침 적용 완료
  - [x] Gemini 2-Pass Function Call 도입 ➔ 하드코딩 `if-else` 대사 코드 100% 완전 삭제!
- [x] **[2순위] 실시간 정보 탐색 Agent:** Open-Meteo 실시간 기상/오늘·내일·주간 날씨 & 강수 예보 조회 및 부담 없는 2단계 대화형 점심 메뉴 추천 연동 완료 ([`core/info_agent.py`](file:///d:/sjchoi/win_pet/core/info_agent.py))
- [x] **[3순위] 기억력 Agent (Memory):** 대화 타임스탬프 및 설정 가능한 세션 만료(`session_timeout_minutes`) 기반 대화 회상 시스템 연동 완료 ([`core/memory_agent.py`](file:///d:/sjchoi/win_pet/core/memory_agent.py))
  - [x] 독립된 장기기억 보관소(`long_term_memory.json`) 및 5개 표준 태그(`profile`, `preference`, `schedule`, `habit`, `relation`) 구축
  - [x] 중요도 3~5점 이상 팩트 선별 저장 및 키워드 매칭 선택적 추출(`Selective Retrieval`) 연동 완료
- [x] **[4순위] 🚀 윈도우 시작 시 자동 실행 (Start with Windows):** 레지스트리(`HKCU\...\Run`) 자동 등록 및 우클릭 토글 메뉴 연동 완료 ([`core/config_manager.py`](file:///d:/sjchoi/win_pet/core/config_manager.py))
- [x] **[5순위] ⏰ 1회성 타이머 & 반복 포모도로(Pomodoro) 스케줄러:** 
  - [x] 대화 연동 (`set_timer`, `start_pomodoro`, `stop_pomodoro`) 및 백그라운드 1초 카운트다운 ([`core/schedule_agent.py`](file:///d:/sjchoi/win_pet/core/schedule_agent.py))
  - [x] 특정 시각("5시 5분") 00초 정각 맞춤 알람 (`17:05:00`) 및 유저 클릭 확인 시까지 알림 영구 유지 (`duration_ms=0`) 적용
  - [x] 집중(25분) ➔ 휴식(5분) ➔ 집중 반복 사이클 및 펫 말풍선/행복 포즈(`happy/`) 시각 알림
  - [x] 우클릭 `⏰ 펫 타이머 / 포모도로...` GUI 팝업 UI 완비 ([`ui/dialog_timer.py`](file:///d:/sjchoi/win_pet/ui/dialog_timer.py))
- [x] **[4순위] 펫 상태 & 친밀도 (Status):** 3대 상태 지수(친밀도, 행복도, 심심함) 및 독립 보관소(`status.json`), 쓰다듬기/대화 보상 & 방치 감지, `📊 펫 상태창...` GUI 팝업 연동 완료 ([`core/status_agent.py`](file:///d:/sjchoi/win_pet/core/status_agent.py), [`ui/dialog_status.py`](file:///d:/sjchoi/win_pet/ui/dialog_status.py))
  - [x] 이미지가 없는 펫 이미지 미존재 시 `idle/` 프레임 100% 안전 폴백(Fallback) 방어 모듈 연동 완료
- [x] **[5순위] win_pet (무설치 포터블 패키징):** `build_portable.py` 구축 완료 ➔ `dist/win_pet/win_pet.exe` 원클릭 실행 파일 및 리소스/안내문 동봉 완비

**4단계: 음성 (STT/TTS) 연동 및 신규 TODO 기능 목록**

- [x] **[TODO-1] 🛑 PC 프로그램 안전 제어 및 종료 Agent (`close_app` 도구 & `pc_targets.json`):**
  - [x] 외부 JSON (`pc_targets.json`) 파일 분리로 제어 가능 프로그램(메모장, 계산기, 크롬, 엣지, 카카오톡, 디스코드 등) 안전 화이트리스트 관리
  - [x] 강제 킬 방지 및 Graceful Close 우선 종료 처리로 데이터 유실 방어 완비 ([`core/pc_agent.py`](file:///c:/Users/nivis/Desktop/sogno-skill-up/win-pet/core/pc_agent.py))
- [x] **[TODO-2] 📅 오늘의 일정 & 할 일(TODO) 통합 관리 및 아침 1회 브리핑 Agent:**
  - [x] 단일 `schedules.json` 파일에서 일정(시작일시)과 할 일(마감일시 TODO/체크박스) 통합 CRUD 관리 ([`core/calendar_agent.py`](file:///c:/Users/nivis/Desktop/sogno-skill-up/win-pet/core/calendar_agent.py))
  - [x] 아침 06~12시 최초 1회 실시간 날씨 + 오늘 일정 요약 굿모닝 브리핑 및 `status.json` 중복 방지 플래그 연동
  - [x] 시작 10분 전 사전 알림 백그라운드 체커 및 펫 말풍선/행복 표정 연동
  - [x] 우클릭 `📅 일정 / 할 일(TODO) 관리...` 다크 테마 GUI 팝업 UI 완비 ([`ui/dialog_calendar.py`](file:///c:/Users/nivis/Desktop/sogno-skill-up/win-pet/ui/dialog_calendar.py))
- [x] **[개선] 시스템 프롬프트 외부 텍스트 분리:**
  - [x] 파이썬 코드 수정 없이 누구나 메모장으로 공통 행동 지침을 수정할 수 있도록 `prompts/system_base.txt` 분리 및 실시간 동적 로드 완비 ([`core/persona_builder.py`](file:///c:/Users/nivis/Desktop/sogno-skill-up/win-pet/core/persona_builder.py))
- [x] **[개선] AI 생성 이미지 피부색 붉은기 일괄 캘리브레이터 (`tools/skin_calibrator.py`):**
  - [x] 마젠타/보라 배경으로 인한 피부색 번짐(Color Bleed) 감지 ➔ 1번 기준 이미지와의 RGB 오차(델타) 정밀 계산 ➔ 피부 영역만 1:1 역보정 복원 완비
  - [x] 단일 파일 및 폴더 전체 일괄(Batch) 캘리브레이션 지원
- [x] **[개선] 신규 펫 자동 정돈 비동기 QThread 전환 (`PetGeneratorWorker`):**
  - [x] 대용량 이미지 배경 제거/크롭 중 펫이 멈추던 UI 프리징(Freeze) 완벽 해결 ➔ 작업 중 자율 보행 유지 + 말풍선 실시간 안내 팝업
- [x] **[개선] `pets.json` 단일 기준(Single Source of Truth) 일원화 & 페르소나 자동 완성:**
  - [x] 임의의 `assets/` 스캔 주입 로직 제거 ➔ `pets.json` 삭제/비활성화 시 100% 즉시 반영
  - [x] 신규 펫 등록 시 `species`, `tone`, `speech_style` 기본 템플릿 필드 오프라인 자동 완성 완비
  - [x] Windows CP949 콘솔 인코딩 예외 크래시 방어 완비
- [x] **[개선] 무설치 포터블 패키징 (`build_portable.py`) 리소스 완벽 동기화:**
  - [x] `dist/win_pet/` 루트에 `assets/`, `prompts/`, `pets.json`, `config.json`, `pc_targets.json` 자동 동기화 배치
  - [x] 포터블 실행 시 `BASE_DIR` 경로 일치 보장 및 빌드 임시 폴더(`build/`) 자동 정리
- [x] **[개선] API 사용량(Token Usage) / Tool 호출 / 에러 실시간 로깅 & 이력 확인 메뉴 완비:**
  - [x] 매 대화별 Gemini API 토큰 수(`Prompt`, `Candidate`, `Total`) 파싱 및 `logs/YYYY-MM-DD.log` 실시간 기록 ([`core/llm_client.py`](file:///d:/sjchoi/win_pet/core/llm_client.py))
  - [x] 우클릭 / 트레이 메뉴에 `📋 실행 및 API 이력 로그 보기...` 및 `🚀 윈도우 시작 시 자동 실행` 연동 완비 ([`ui/pet_widget.py`](file:///d:/sjchoi/win_pet/ui/pet_widget.py), [`ui/tray_manager.py`](file:///d:/sjchoi/win_pet/ui/tray_manager.py))
  - [x] 윈도우 시작 프로그램 자동 실행 시 CWD(`System32` 등) 경로 이탈 방어 로직 연동 (`main.py` ➔ `os.chdir(BASE_DIR)`)
- [ ] **[TODO-3] 🎮 펫 퀴즈/미션 & 🎵 백그라운드 Lo-Fi BGM 플레이어**:
  - 심심함 해소 상식 퀴즈/습관 미션 및 집중용 백그라운드 음악 재생 연동.

**기타 확장 계획:**
- [ ] **STT (Speech-To-Text):** 마이크 음성 입력 텍스트 변환 (Whisper / 윈도우 API)
- [ ] **TTS (Text-To-Speech):** 펫의 대답을 귀여운 음성으로 출력 (Edge-TTS / ElevenLabs)

---

### 💾 데이터 및 자원 관리
- **픽셀 이미지 자원:** 32x32 / 64x64 픽셀 아트 스프라이트 프레임 (`assets/owl_white/`, `assets/fox_orange/` 폴더)
- **설정 데이터:** `config.json`, `pets.json`
- **날짜 형식:** 모든 날짜 형식은 `yyyy/MM/dd`로 통일
