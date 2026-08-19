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

## 🚀 1단계 실행 방법

가상환경 활성화 상태에서 순서대로 실행합니다:

```bash
# 1. AI 생성 고양이 이미지 프레임 분할 (최초 1회 실행)
python setup_assets.py

# 2. 바탕화면 픽셀 펫 실행
python main.py
```

## 🖼️ 일반 이미지를 픽셀 아트로 변환하기 (Pixelator)

원하는 일반 이미지(JPG/PNG)를 픽셀 펫용 픽셀 아트로 자동 변환할 수 있습니다:

```bash
python pixelator.py --input my_photo.png --output assets/cat/walk_custom.png --size 64
```

## 📁 프로젝트 구조
- `main.py`: 바탕화면 픽셀 펫 실행 메인 스크립트 (PyQt6)
- `setup_assets.py`: AI 스프라이트 시트 이미지를 개별 프레임으로 분할해주는 준비 스크립트
- `pixelator.py`: 일반 이미지를 픽셀 아트로 픽셀화 변환해주는 유틸리티
- `assets/cat/`: 펫 픽셀 아트 애니메이션 프레임 저장소
- `GEMINI.md`: 프로젝트 개발 로드맵 및 메모
