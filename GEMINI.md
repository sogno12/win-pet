# 🐱 AI 픽셀 데스크톱 펫 ('win_cat')

### 🎯 프로젝트 개요
- **컨셉:** 윈도우 바탕화면에서 뽀짝뽀짝 움직이며 사용자와 대화하고 PC 제어 및 추천 등의 역할을 수행하는 AI 픽셀 컴패니언 펫.
- **주요 기능:** 바탕화면 투명 픽셀 펫, LLM 기반 대화 및 표정/행동 반응, Agent 기능(PC 제어, 정보 검색, 기억력, 친밀도), 음성(STT/TTS) 연동, 이미지 픽셀화 변환기.
- **개발 환경 / 기술 스택:** Windows OS, Anaconda (Conda 가상환경 `wincat`), Python 3.10+, PyQt6, Pillow, LLM API (Gemini API 등).

---

### 🐍 Conda 가상환경 설정
```bash
# 1. wincat 가상환경 생성
conda create -n wincat python=3.10 -y

# 2. 가상환경 활성화
conda activate wincat

# 3. 필수 패키지 설치
pip install PyQt6 Pillow requests

# 4. 실행
python setup_assets.py        # 픽셀 이미지 준비 (최초 1회)
python process_drag_assets.py # 뒷목 잡힌 전용 프레임 준비 (최초 1회)
python main.py                # 펫 실행
```

---

### 🚀 4단계 개발 로드맵 현황

**1단계: 바탕화면 픽셀 펫 띄우기 (완료 및 개선 중)**
- [x] 투명 및 무테두리 윈도우 창 생성 (`main.py`)
- [x] 픽셀 보정 렌더링 (Nearest-Neighbor / Pixelated)
- [x] 독립 타이머 기반 60FPS 부드러운 자율 걷기/대기/드래그 애니메이션 & 이동 로직
- [x] 마우스 호버 커서(손가락 👆) & 안내 툴팁 추가
- [x] 설정 영구 보관용 `config.json` 연동 (크기, 스킨, 항상 위 고정 등)
- [x] 다중 펫 스킨 연동 (🧀 치즈태비 고양이 / 🦉 복슬복슬 해리포터 솜뭉치 하얀 부엉이)
- [x] **부엉이 몸통 내부 깃털 투명화 버그 완벽 수정** (마젠타 #FF00FF 크로마키 알고리즘 적용)
- [x] **뒷목 잡힌 전용 픽셀 프레임 (`drag.png`) 연동** (고양이 & 부엉이 전용 포즈)
- [x] **동물 5대 표준 에셋 폴더 스펙 적용** (`walk/`, `idle/`, `drag/`, `happy/`, `special/`)
- [x] **범용 펫 생성기 (`pet_generator.py`) 구축 및 동적 펫 스킨 스캐너 연동**
- [x] 시스템 트레이 아이콘 메뉴 (✨ 내 앞으로 불러오기 / 📌 항상 위에 표시 / 🙈 숨기기 / ❌ 종료)
- [x] 이미지 픽셀화 변환 모듈 (`pixelator.py`) 작성 (일반 이미지 ➡️ 픽셀 펫 변환)

**2단계: 텍스트 / LLM 대화 연결 (예정)**
- [ ] 펫 클릭/핫키 입력 시 텍스트 입력창 및 말풍선 UI
- [ ] LLM (Gemini API) 연동 및 JSON Structured Output 구조 설계
- [ ] 대화 결과에 따른 펫 표정 및 행동 애니메이션 전환

**3단계: Agent 작업 & 기능 확장 (예정)**
- [ ] **PC 제어 (Function Calling):** 유튜브/메모장 등 앱 실행 및 PC 제어
- [ ] **정보 탐색:** 날씨, 점심 메뉴 추천 등 웹 검색 기능
- [ ] **기억력 (Memory):** Supabase 또는 로컬 DB에 대화 내용 기록 및 회상
- [ ] **상태 및 친밀도 (Status):** 대화 빈도에 따른 기분(행복/심심/피곤) 및 상태 변화

**4단계: 음성 (STT/TTS) 연동 (예정)**
- [ ] **STT (Speech-To-Text):** 마이크 음성 입력 텍스트 변환 (Whisper / 윈도우 API)
- [ ] **TTS (Text-To-Speech):** 펫의 대답을 귀여운 음성으로 출력 (Edge-TTS / ElevenLabs)

---

### 💾 데이터 및 자원 관리
- **픽셀 이미지 자원:** 32x32 / 64x64 픽셀 아트 스프라이트 프레임 (`assets/cat_cheese/`, `assets/owl_white/` 폴더)
- **설정 데이터:** `config.json`
- **날짜 형식:** 모든 날짜 형식은 `yyyy/MM/dd`로 통일
