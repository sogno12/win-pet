"""win-pet에서 쓰는 모든 파일/폴더 경로를 한곳에서 관리합니다.

- 소스 실행: 프로젝트 루트 (main.py가 있는 폴더)
- PyInstaller 빌드: exe가 있는 폴더 (dist/win_pet/)

새 데이터 파일이 생기면 여기에 상수를 추가하고 가져다 쓰세요.
"""
import os
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 설정
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
CONFIG_TEMPLATE_PATH = os.path.join(BASE_DIR, "config.json.template")
ENV_PATH = os.path.join(BASE_DIR, ".env")
PC_TARGETS_PATH = os.path.join(BASE_DIR, "pc_targets.json")
PROMPT_BASE_PATH = os.path.join(BASE_DIR, "prompts", "system_base.txt")

# 펫
PETS_REGISTRY_PATH = os.path.join(BASE_DIR, "pets.json")
PETS_TEMPLATE_PATH = os.path.join(BASE_DIR, "pets.json.template")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# 사용자 데이터
SHORT_MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")
LONG_MEMORY_PATH = os.path.join(BASE_DIR, "long_term_memory.json")
STATUS_PATH = os.path.join(BASE_DIR, "status.json")
SCHEDULES_PATH = os.path.join(BASE_DIR, "schedules.json")

# 출력
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
