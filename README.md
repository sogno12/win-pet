# 🐱 win_cat: AI 픽셀 데스크톱 펫

윈도우 바탕화면을 뽀짝뽀짝 움직이는 AI 픽셀 펫 프로그램입니다.

## 🛠️ Conda 가상환경 세팅 및 설치

터미널(Prompt)에서 아래 명령어를 실행하여 전용 가상환경을 구성하세요.

```bash
# 1. 가상환경 생성 (Python 3.10)
conda create -n wincat python=3.10 -y

# 2. 가상환경 활성화
conda activate wincat

# 3. 필요한 패키지 설치
pip install PyQt6 Pillow requests
```

## 🚀 실행 방법

가상환경 활성화 상태에서 실행합니다:

```bash
# 바탕화면 픽셀 펫 실행
python main.py
```

---

## 🐯 새로운 펫 (예: 호랑이, 펭귄) 직접 추가하는 방법

원하는 새로운 동물을 앱에 추가하고 싶을 때는 아래 **3단계 과정**으로 아주 쉽게 추가할 수 있습니다:

### Step 1. 펫 폴더 생성하기
```bash
python pet_generator.py --id tiger --name "🐯 아기 호랑이"
```
* 위 명령어를 치면 `assets/tiger/` 하위에 5대 표준 폴더가 자동으로 만들어집니다.

### Step 2. 5대 표준 폴더에 PNG 이미지 넣기
`assets/tiger/` 폴더 안의 각 역할별 폴더에 준비하신 픽셀 PNG 이미지를 넣으세요:

* `assets/tiger/walk/` ➔ 걸어가는 픽셀 이미지 (`walk_0.png`, `walk_1.png`...)
* `assets/tiger/idle/` ➔ 정면 보고 멍때리는 픽셀 이미지 (`idle_0.png`)
* `assets/tiger/drag/` ➔ 마우스로 들려 잡힌 픽셀 이미지 (`drag_0.png`)
* `assets/tiger/happy/` ➔ 기뻐서 펄쩍 뛰는 픽셀 이미지 (`happy_0.png`)
* `assets/tiger/special/` ➔ 호랑이 특이 행동 이미지

*(※ 이미지가 없는 폴더는 걷기 이미지가 자동으로 대신 사용됩니다.)*

### Step 3. 펫 앱 재실행 및 스킨 선택
```bash
python main.py
```
* `main.py`가 새 폴더를 자동 탐색하여, 우클릭 **`🐾 펫 스킨 변경`** 메뉴에 **`🐯 아기 호랑이`**가 짜잔! 하고 자동으로 나타납니다.

---

## 🎨 펫 에셋 표준 규격 (Standard Asset Spec)
- `walk/`: 걷기 / 날기 연속 이미지
- `idle/`: 멈췄을 때 정면 보기 & 눈 깜빡이기
- `drag/`: 뒷목/몸통이 잡혀 둥둥 들린 포즈
- `happy/`: 펄쩍 뛰기 / 애교 / 하트 발사
- `special/`: 펫 특화 행동 (식빵 굽기 / 부엉이 머리 갸웃 등)

## 📁 프로젝트 구조
- `main.py`: 바탕화면 픽셀 펫 실행 메인 스크립트 (PyQt6 다중 스킨/FSM 구동)
- `pet_generator.py`: 범용 펫 스킨 자동 폴더 생성 유틸리티
- `pixelator.py`: 일반 이미지를 픽셀 아트로 픽셀화 변환해주는 유틸리티
- `config.json`: 펫 스킨, 크기, 항상 위 옵션 영구 보관용 설정 파일
- `assets/`: 펫 픽셀 아트 애니메이션 저장소 (`cat_cheese/`, `owl_white/`, `tiger/` 등)
- `GEMINI.md`: 프로젝트 개발 로드맵 및 메모
