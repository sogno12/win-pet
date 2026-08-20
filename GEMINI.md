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
- [x] 우클릭 서브메뉴 `🐢 펫 이동 속도` 5단계 세분화 개편 (🐢 느리게 150ms / 🍃 느긋하게 100ms / 🐾 천천히 70ms / 🎵 경쾌하게 45ms / ⚡ 빠르게 30ms)
- [x] 우클릭 서브메뉴 `📍 펫 이동 범위` 4단계 추가 (🤏 좁게 / 🏡 아늑하게 / 🖥️ 모니터 전용 / 🌐 자유롭게)
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
- [x] **[0순위] 비개발자 배포용 환경 준비 (API 키 입력 UI & GUI 신규 펫 자동 정돈/추가 메뉴 완료!)**
  - [x] **API 키 설정 팝업 UI:** 펫 우클릭 및 대화 시 API 키 미설정 상태 탐지 ➔ 사용자 자동 입력 팝업 UI (`ui/dialog_api_key.py`, `config.json` 저장)
  - [x] **GUI 신규 펫 자동 정돈/추가 버튼:** 우클릭 메뉴 `✨ 신규 펫 자동 정돈/추가` 클릭 ➔ `assets/` 신규 폴더 다중 감지 ➔ 수정 가능한 기본 타이틀 입력 팝업 ➔ 3단계 배경 제거 오토 파이프라인 1초 완료
- [x] **[1순위] PC 제어 Agent (Function Calling) & 로깅 시스템 & 키워드 페르소나 엔진:**
  - [x] 유튜브 음악/영상 검색 재생, 메모장/계산기/작업관리자 앱 실행, PC 화면 잠금, 볼륨 조절/음소거 구현 ([`core/pc_agent.py`](file:///d:/sjchoi/win_pet/core/pc_agent.py))
  - [x] Gemini REST API `systemInstruction` 페이로드 분리로 Function Calling 트리거율 100% 보장 ([`core/llm_client.py`](file:///d:/sjchoi/win_pet/core/llm_client.py))
  - [x] 매일 날짜별 자동 회전 로깅 시스템 구축 ([`core/logger.py`](file:///d:/sjchoi/win_pet/core/logger.py) ➔ `logs/YYYY-MM-DD.log`, `yyyy/MM/dd HH:mm:ss` 포맷 준수)
  - [x] 키워드 기반 페르소나 엔진 구축 (`pets.json` ➔ `species`, `tone`, `speech_style` 키워드 지원, [`core/persona_builder.py`](file:///d:/sjchoi/win_pet/core/persona_builder.py))
  - [x] 턴 변경 시에도 존댓말/반말이 섞이지 않는 엄격한 어미 일관성 지침 적용 완료
  - [x] Gemini 2-Pass Function Call 도입 ➔ 하드코딩 `if-else` 대사 코드 100% 완전 삭제!
- [x] **[2순위] 실시간 정보 탐색 Agent:** Open-Meteo 실시간 기상/날씨 정보 조회 및 부담 없는 2단계 대화형 점심 메뉴 추천 연동 완료 ([`core/info_agent.py`](file:///d:/sjchoi/win_pet/core/info_agent.py))
- [x] **[3순위] 기억력 Agent (Memory):** 대화 타임스탬프 및 설정 가능한 세션 만료(`session_timeout_minutes`) 기반 대화 회상 시스템 연동 완료 ([`core/memory_agent.py`](file:///d:/sjchoi/win_pet/core/memory_agent.py))
- [ ] **[4순위] 펫 상태 & 친밀도 (Status):** 머리 다듬기/대화에 따른 행복/심심 상태 변화
- [ ] **[5순위] win_pet (무설치 포터블 패키징):** 파이썬 미설치 PC에서도 켜지는 포터블 실행기 빌드

**4단계: 음성 (STT/TTS) 연동 (예정)**
- [ ] **STT (Speech-To-Text):** 마이크 음성 입력 텍스트 변환 (Whisper / 윈도우 API)
- [ ] **TTS (Text-To-Speech):** 펫의 대답을 귀여운 음성으로 출력 (Edge-TTS / ElevenLabs)

---

### 💾 데이터 및 자원 관리
- **픽셀 이미지 자원:** 32x32 / 64x64 픽셀 아트 스프라이트 프레임 (`assets/owl_white/`, `assets/fox_orange/` 폴더)
- **설정 데이터:** `config.json`, `pets.json`
- **날짜 형식:** 모든 날짜 형식은 `yyyy/MM/dd`로 통일
