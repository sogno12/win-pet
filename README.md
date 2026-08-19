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

가상환경 활성화 상태에서 순서대로 실행합니다:

```bash
# 1. AI 픽셀 이미지 프레임 준비 (최초 1회 실행)
python setup_assets.py        # 기본 프레임
python process_drag_assets.py # 뒷목 잡힌 전용 프레임

# 2. 바탕화면 픽셀 펫 실행
python main.py
```

## 🎨 펫 에셋 표준 규격 (Standard Asset Spec)

새로운 펫(동물) 스킨을 추가할 때는 `assets/<pet_id>/` 하위에 아래 5가지 폴더에 PNG 이미지를 배치하면 코드가 자동 인식합니다:

- `walk/`: 걷기 / 날기 연속 이미지 (`walk_0.png`, `walk_1.png`...)
- `idle/`: 멈췄을 때 정면 보기 & 눈 깜빡이기 (`idle_0.png`...)
- `drag/`: 뒷목/몸통이 잡혀 둥둥 들린 포즈 (`drag.png`)
- `happy/`: 펄쩍 뛰기 / 애교 / 하트 발사 (`happy_0.png`...)
- `special/`: 펫 특화 행동 (식빵 굽기 / 부엉이 머리 갸웃 등)

## 📁 프로젝트 구조
- `main.py`: 바탕화면 픽셀 펫 실행 메인 스크립트 (PyQt6 다중 스킨/FSM 구동)
- `setup_assets.py` / `process_cute_owl.py`: AI 스프라이트 시트 분할 유틸리티
- `pixelator.py`: 일반 이미지를 픽셀 아트로 픽셀화 변환해주는 유틸리티
- `config.json`: 펫 스킨, 크기, 항상 위 옵션 영구 보관용 설정 파일
- `assets/`: 펫 픽셀 아트 애니메이션 저장소 (`cat_cheese/`, `owl_white/`)
- `GEMINI.md`: 프로젝트 개발 로드맵 및 메모
