# 🐱 AI 픽셀 데스크톱 펫 ('win_cat') 펫 관리 및 신규 제작 가이드

본 프로젝트에서는 AI 도움 없이 **사용자가 직접 터미널 명령어 한 줄로 펫을 새로 만들거나, 삭제하거나, 이미지를 픽셀 펫으로 자동 변환**할 수 있습니다.

---

## 🛠️ 1. 터미널 명령어로 펫 관리하기 (`pet_generator.py`)

Conda 가상환경(`wincat`)에서 `pet_generator.py` 스크립트를 사용하여 간편하게 제어합니다.

### ➕ (1) 신규 펫 생성하기
새로운 동물 펫의 폴더 구조와 템플릿 이미지를 자동으로 뚝딱 생성합니다.
```bash
python pet_generator.py create <pet_id> "<펫_이름>"
```
- **사용 예시:**
  ```bash
  python pet_generator.py create tiger_cute "🐯 귀여운 호랑이"
  ```
- **결과:** `assets/tiger_cute/` 폴더가 생성되고 `walk/`, `idle/`, `drag/` 에셋 구조와 `pets.json` 등록이 자동으로 작성됩니다!

---

### 🗑️ (2) 맘에 안 드는 펫 삭제 및 재창작하기
원하지 않는 펫의 이미지 폴더와 `pets.json` 등록 정보를 깨끗이 삭제합니다.
```bash
python pet_generator.py delete <pet_id>
```
- **사용 예시:**
  ```bash
  python pet_generator.py delete turtle_green
  ```
- **결과:** `assets/turtle_green/` 폴더와 `pets.json` 등록 정보가 깨끗하게 지워집니다. 이후 다시 (1)번 명령어로 깔끔하게 재창작할 수 있습니다!

---

### 🖼️ (3) 가지고 있는 일반 이미지를 픽셀 펫으로 변환하기
내 스마트폰 사진이나 인터넷 이미지를 32x32 픽셀 펫으로 자동 변환하여 등록합니다.
```bash
python pet_generator.py convert <이미지파일_경로> <pet_id> "<펫_이름>"
```
- **사용 예시:**
  ```bash
  python pet_generator.py convert C:/Users/name/Desktop/my_dog.png dog_coco "🐶 우리집 코코"
  ```

---

## 📁 2. 폴더에서 수동으로 이미지만 넣어서 만들기 (가장 직관적!)

코드가 익숙지 않다면 **윈도우 탐색기 폴더**에서 이미지만 넣으셔도 100% 자동 인식됩니다!

1. `win_cat/assets/` 폴더 안에 원하는 새 동물 폴더(예: `assets/my_puppy/`)를 만듭니다.
2. 아래 3개 하위 폴더를 만들고 32x32 픽셀 PNG 이미지를 넣습니다:
   - `assets/my_puppy/walk/` : 걷기 이미지 (`walk_0.png`, `walk_1.png`)
   - `assets/my_puppy/idle/` : 멍때리는 정면 이미지 (`idle_0.png`)
   - `assets/my_puppy/drag/` : 마우스로 덜미 잡힌 이미지 (`drag_0.png`)
3. `python main.py`를 실행하면 **자동으로 우클릭 펫 스킨 메뉴에 추가**됩니다!
