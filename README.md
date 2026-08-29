# 🐱 win-pet: AI 픽셀 데스크톱 컴패니언 펫 (WinPet)

> 윈도우 바탕화면에서 투명하게 뽀짝뽀짝 움직이며 사용자와 대화하고 PC 제어, 정보 탐색, 기억력 및 친밀도를 나눌 수 있는 **모바일/바탕화면 우선 AI 픽셀 펫 컴패니언**입니다.

---

## ✨ 핵심 주요 기능

- 🐾 **투명 픽셀 보행 & 몽환 안개 오버레이 UI (`ui/range_overlay.py`)**:
  - 60FPS의 부드러운 자율 보행/대기 애니메이션 (상하좌우/대각선 2D 이동)
  - `🔍 현재 이동 범위 미리보기 (안개 보기)` 및 `👁️ 이동 범위 안개 항상 켜기 (테스트 고정용)` 지원
  - 5단계 세분화 이동 범위 (`🤏 매우 좁게` ~ `🌐 자유롭게`) 및 `config.json` 커스텀 안개 외곽선/색상/투명도 지원
- 💬 **Gemini LLM 대화 & 프롬프트 외부 분리 (`prompts/system_base.txt`, `core/persona_builder.py`)**:
  - `prompts/system_base.txt`로 공통 행동 수칙 분리 (메모장으로 누구나 손쉽게 수정 가능)
  - `pets.json` 동적 펫 레지스트리 기반 어미 일관성 규칙 (`speech_style`) 및 2-Pass 대사 생성
- 🛑 **PC 프로그램 안전 제어 & 종료 Agent (`pc_targets.json`, `core/pc_agent.py`)**:
  - 외부 JSON (`pc_targets.json`) 기반으로 제어 가능 프로그램(메모장, 계산기, 크롬, 엣지, 카톡, 디스코드 등) 안전 화이트리스트 관리
  - 윈도우 창 닫기 신호(`taskkill /IM`) 우선 전송으로 저장되지 않은 작업 데이터 유실 원천 방어
  - 유튜브/구글 음악/영상 검색 재생, PC 화면 잠금, 시스템 볼륨 조절/음소거 지원
- 📅 **통합 일정 & 할 일(TODO) 관리 / 아침 1회 굿모닝 브리핑 (`core/calendar_agent.py`, `ui/dialog_calendar.py`)**:
  - 단일 `schedules.json` 파일에서 일정(시작일시 약속)과 할 일(마감일시 TODO/체크박스) 통합 CRUD 관리
  - 아침(06~12시) 최초 1회 실시간 날씨 + 오늘 일정 요약 굿모닝 브리핑 (중복 방지 플래그 지원)
  - 일정 시작 10분 전 사전 알림 펫 말풍선 팝업
  - 펫 우클릭 메뉴 `📅 일정 / 할 일(TODO) 관리...` 다크 테마 GUI 팝업 완비
- ⏰ **1회성 타이머 & 반복 포모도로 스케줄러 (`core/schedule_agent.py`, `ui/dialog_timer.py`)**:
  - 대화 및 GUI로 타이머/정각 알람 설정 및 집중(25분)-휴식(5분) 자동 반복 포모도로 사이클
  - 우클릭 `⏰ 펫 타이머 / 포모도로...` GUI 팝업 완비
- 🌤️ **실시간 정보 탐색 Agent (`core/info_agent.py`)**:
  - Open-Meteo REST API 실시간 기상/날씨 파싱 및 부담 없는 2단계 대화형 점심 메뉴 추천
- 🧠 **독립 장기기억 시스템 (`long_term_memory.json`)** (`core/memory_agent.py`):
  - 5가지 표준 카테고리 태그 (`profile`, `preference`, `schedule`, `habit`, `relation`)
  - 중요도 (3~5점) 선별 영구 저장 및 키워드 연관 매칭 선택적 회상 (`Selective Retrieval`)
- 📊 **펫 3대 상태 및 친밀도 시스템 (`status.json`)** (`core/status_agent.py`, `ui/dialog_status.py`):
  - 머리 쓰다듬기/대화 보상, 30분 방치 감지, 5단계 친밀도 뱃지 및 `📊 펫 상태창...` GUI 팝업
  - `happy/` 또는 `special/` 에셋 이미지가 없는 펫이라도 에러 없이 `idle/`로 100% 안전 폴백(Fallback)
- 📋 **실시간 API 토큰 사용량 & 실행 이력 로그 보기 (`core/logger.py`, `core/llm_client.py`)**:
  - 매 대화별 Gemini API 토큰 수 (`Prompt`, `Candidate`, `Total` tokens) 자동 파싱 및 `logs/YYYY-MM-DD.log` 실시간 기록
  - 펫 우클릭 및 트레이 메뉴 `📋 실행 및 API 이력 로그 보기...` 지원 (메모장으로 즉시 로그 확인)
  - 펫의 대화, 툴 수행 인자/결과, Action-Fulfillment Safety Guard 강제 실행 이력 및 API 오류 종합 추적
- 🚀 **윈도우 시작 시 자동 실행 & CWD 경로 방어 (`main.py`, `core/config_manager.py`)**:
  - 우클릭 및 트레이 메뉴 `🚀 윈도우 시작 시 자동 실행` 토글 지원 (Windows 시작 프로그램 레지스트리 자동 등록)
  - 부팅 시 작업 디렉터리(`CWD`)가 `System32` 등으로 이탈되어 발생할 수 있는 상대 경로 예외 방어 (`os.chdir(BASE_DIR)` 강제 고정)
- 💼 **All-in-Win 자산관리 포트폴리오 연동 Agent (`core/asset_agent.py`)**:
  - `all-in-win/data/summary.json` 경량 요약 데이터(총자산, 원금, 손익, 수익률, TOP 3 자산, 비중) 0.001초 파싱
  - Gemini 대화 연동 (`get_asset_summary`, `open_asset_dashboard` 2-Pass Function Calling)
  - FastAPI 대시보드 미실행 시 백그라운드 프로세스 자동 구동 및 웹 브라우저(`http://127.0.0.1:8000`) 즉시 호출
  - 펫 우클릭 및 트레이 메뉴에 `💼 올인윈(All-in-Win) 자산관리` 서브메뉴 완비
- 🎨 **3단계 오토 파이프라인 정돈기 (`pet_generator.py`)**:
  - `assets/` 신규 펫 폴더 탐지 ➔ 1초 배경 제거(마젠타 #FF00FF 크로마키 포함) ➔ 캐릭터 크롭 ➔ 1:1 정사각형 정중앙 배치 ➔ 자동 메뉴 추가
- 📸 **스마트 화면 캡처 & Vision AI / OCR 분석 (`ui/screen_capturer.py`, `ui/dialog_capture_result.py`, `core/vision_agent.py`)**:
  - **모니터별 독립 오버레이 (Windows 캡처 도구 방식)**: 연결된 모든 모니터에 각각 독립 오버레이를 띄워 경계 없이 깔끔하게 드래그 캡처
  - **High DPI / 멀티 모니터 무결점 지원**: `PIL.ImageGrab` 물리 픽셀 좌표 변환으로 DPI 배율 왜곡·검은 공간 완전 제거
  - `screenshots/` 자동 저장 + Windows 클립보드 즉시 복사(`Ctrl+V`)
  - **AI 분석**: Gemini Vision 모델로 캡처 화면을 상세 분석 (에러 원인, UI 설명, 데이터 해석 등)
  - **OCR**: 이미지 내 텍스트 추출 후 클립보드 자동 복사
  - API 키 미설정 시 버튼 자동 비활성화 + Vision 미지원 모델 에러 친절 안내
  - 분석 결과는 텍스트 길이 제한 없는 **스크롤 팝업 창 + 📋 전체 복사 버튼** 제공
- 🙈 **펫 일괄 숨기기 / 다시 보이기 (`ui/pet_widget.py`, `ui/tray_manager.py`)**:
  - 우클릭 `🙈 펫 잠시 숨기기 (트레이 보관)` → 펫 본체 + 말풍선 + 입력창 + 안개 일괄 숨김
  - 트레이 아이콘 클릭 또는 `👀 펫 다시 보이기` 메뉴로 즉시 복원

---

## 🐍 Conda 가상환경 및 설치 가이드

### 1. 가상환경 생성 및 패키지 설치
```bash
# 1. wincat 가상환경 생성 (Python 3.10+)
conda create -n wincat python=3.10 -y

# 2. 가상환경 활성화
conda activate wincat

# 3. 필수 패키지 설치
pip install PyQt6 Pillow requests python-dotenv
```

### 2. 🔑 API 키 및 보안 설정 (.env)

본 앱은 **Google Gemini API Key**가 필요합니다. 두 가지 방법 중 편하신 방법으로 등록할 수 있습니다:

#### 방법 A: 프로그램 실행 후 GUI 팝업으로 입력 (추천)
앱 실행 후 우클릭 메뉴의 **`🔑 API 키 설정...`**을 눌러 발급받은 키를 등록하면 자동으로 `config.json`에 저장되어 바로 작동합니다.

#### 방법 B: `.env` 환경 변수 파일 생성
루트 디렉토리에 `.env` 파일 (샘플: `.env.example` 참고)을 생성하고 아래와 같이 입력합니다:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

> [!IMPORTANT]
> **보안 주의사항 (`.gitignore`)**:
> - `.env` 파일 및 발급받은 API 키는 **Git 추적에서 완전히 차단(`.gitignore`)**되어 있으므로 GitHub public 저장소에 올리더라도 안심하셔도 됩니다.
> - 개인 대화 로그(`logs/`), 단기/장기기억(`memory.json`, `long_term_memory.json`), 상태 수치(`status.json`)도 개인정보 보호를 위해 `.gitignore`에 등록되어 있습니다.

---

## 🚀 실행 방법

### 개발 환경 실행 (Python)
```bash
# 1. 픽셀 에셋 준비 (최초 1회 실행)
python setup_assets.py

# 2. win_pet 데스크톱 펫 실행
python main.py
```

### 📦 무설치 포터블 패키지 빌드 (비개발자 배포용)
파이썬이 설치되지 않은 일반 PC에 배포할 수 있는 **원클릭 무설치 실행 파일(`win_pet.exe`)**을 직접 빌드할 수 있습니다:

```bash
# 포터블 빌드 자동화 스크립트 구동 (PyInstaller 자동 연동)
python build_portable.py
```

- **빌드 결과물 위치**: `dist/win_pet/`
- **배포 안내**: 생성된 `dist/win_pet/` 폴더 전체를 압축하여 비개발자분께 전달하시면, 사용자는 파이썬 설치 없이 `win_pet.exe` 파일만 더블 클릭해서 바로 펫을 소환할 수 있습니다. (폴더 내 `비개발자_사용법_안내.txt` 동봉)

---

## 🎨 신규 펫 자동 정돈 및 추가 가이드 (`pet_generator.py`)

사용자가 직접 준비한 고품질 이미지를 **3단계 오토 파이프라인 (스마트 배경 제거 ➔ 캐릭터 크롭 ➔ 1:1 정사각형 정중앙 배치)**을 거쳐 1초 만에 새로운 펫 스킨으로 정돈하고 추가할 수 있습니다:

### 방법 A: GUI 우클릭 메뉴 사용 (가장 편리)
1. `assets/` 폴더 내에 원하는 이름의 새 폴더(예: `assets/my_rabbit`)를 생성하고 캐릭터 이미지를 넣습니다.
2. 실행 중인 펫을 오른쪽 마우스 클릭 ➔ **`🐾 펫 스킨 변경`** ➔ **`✨ 신규 펫 자동 정돈/추가...`**를 클릭합니다.
3. 1초 만에 스마트 배경 제거(마젠타 크로마키 포함) 및 크롭이 수행되어 메뉴에 동적 등록되며 바로 펫 스킨을 바꿀 수 있습니다.

### 방법 B: CLI 파이썬 오토 파이프라인 직접 구동
```bash
python pet_generator.py
```

---

## 🎨 AI 생성 이미지 피부색 붉은기 일괄 캘리브레이터 (`tools/skin_calibrator.py`)

AI 이미지 생성 시 마젠타/보라 배경색이 캐릭터의 얼굴/피부에 스며들어(Color Bleed) 다음 프레임으로 갈수록 피부가 붉거나 자줏빛으로 변색되는 현상을 **1번 기준 이미지와의 RGB 오차 역보정**을 통해 원본 피부색으로 일괄 복원합니다:

```bash
# 1. 단일 이미지 피부색 보정
python tools/skin_calibrator.py --ref 1번기준이미지.png --target 보정할이미지.png --out 결과.png

# 2. 폴더 내 모든 프레임(walk, idle, happy 등) 일괄 캘리브레이션
python tools/skin_calibrator.py --ref assets/my_pet/walk_0.png --folder assets/my_pet/
```

---

## 📂 프로젝트 폴더 구조

```text
win_pet/
├── assets/                  # 픽셀 아트 프레임 이미지 (owl_white, fox_orange 등)
├── core/                    # 전문 비즈니스 모듈
│   ├── asset_agent.py       # All-in-Win 자산관리 대시보드 & 요약 데이터 연동
│   ├── pc_agent.py          # PC 제어 및 안전 종료 (pc_targets.json 연동)
│   ├── calendar_agent.py    # 통합 일정/TODO 관리 & 아침 1회 브리핑
│   ├── schedule_agent.py    # 1회성 타이머 & 포모도로 스케줄러
│   ├── info_agent.py        # 실시간 날씨 & 점심 추천
│   ├── memory_agent.py      # 스마트 회상 & long_term_memory.json
│   ├── status_agent.py      # 3대 상태지수 & status.json
│   ├── vision_agent.py      # Gemini Vision 이미지 분석 & OCR
│   ├── llm_client.py        # Gemini REST API 연동
│   ├── persona_builder.py   # 어미 일관성 페르소나 (prompts/system_base.txt 연동)
│   └── logger.py            # 날짜별 회전 로거
├── prompts/                 # 시스템 프롬프트 외부 보관소
│   └── system_base.txt      # 공통 행동 수칙 텍스트
├── tools/                   # 에셋 제작 보조 유틸리티
│   └── skin_calibrator.py   # AI 생성 피부색 붉은기 일괄 캘리브레이터
├── ui/                      # PyQt6 GUI 오버레이 & 팝업
│   ├── pet_widget.py        # 메인 투명 펫 위젯 (비동기 QThread 에셋 정돈 연동)
│   ├── range_overlay.py     # 몽환 반투명 안개 미리보기 UI
│   ├── screen_capturer.py   # 📸 모니터별 드래그 캡처 오버레이 (멀티모니터 지원)
│   ├── dialog_capture_result.py  # 📸 캡처 결과 팝업 & AI 분석/OCR UI
│   ├── dialog_calendar.py   # 📅 일정 / 할 일(TODO) 관리창
│   ├── dialog_timer.py      # ⏰ 펫 타이머 / 포모도로 관리창
│   ├── dialog_status.py     # 📊 펫 상태창 팝업
│   ├── dialog_api_key.py    # 🔑 API 키 설정 팝업
│   ├── dialog_input.py      # 대화 질의 입력창
│   ├── speech_bubble.py     # 머리 위 실시간 말풍선
│   └── tray_manager.py      # 시스템 트레이 아이콘 관리
├── screenshots/             # 📸 캡처된 스크린샷 자동 저장 폴더
├── pc_targets.json          # PC 제어/종료 허용 프로그램 화이트리스트
├── schedules.json           # 통합 일정 및 할 일(TODO) 로컬 데이터
├── config.json              # 펫 크기, 속도, 안개 옵션 설정
├── pets.json                # 펫 레지스트리 및 어미 페르소나
├── pet_generator.py         # 3단계 스마트 에셋 정돈 오토 파이프라인
├── build_portable.py        # 무설치 포터블 패키지 자동 빌더
├── setup_assets.py          # 기본 에셋 자동 준비 스크립트
├── .env.example             # 환경 변수 샘플 파일
├── .gitignore               # 개인 키 & 대화 데이터 차단 설정
├── main.py                  # 프로그램 실행 진입점
└── GEMINI.md                # 개발 로드맵 및 스펙 관리 문서
```
