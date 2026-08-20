import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def check_and_install_pyinstaller():
    """pyinstaller 패키지 설치 유무 확인 및 자동 설치"""
    try:
        import PyInstaller
        print("[OK] PyInstaller 패키지가 준비되어 있습니다.")
    except ImportError:
        print("[INFO] PyInstaller 패키지가 필요합니다. 자동 설치를 시작합니다...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_portable_package():
    """win_pet 무설치 포터블 실행 패키지 빌드"""
    print("\n[BUILD] win_pet 무설치 포터블 실행 패키지 빌드를 시작합니다...")
    
    check_and_install_pyinstaller()

    # 빌드 전 실행 중인 win_pet.exe 프로세스 안전 종료 (파일 락 해제)
    try:
        subprocess.call(["taskkill", "/F", "/IM", "win_pet.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 동봉할 리소스 데이터 경로 설정 (Windows 릴리스)
    sep = os.pathsep
    add_data_args = [
        f"--add-data=assets{os.path.pathsep}assets",
        f"--add-data=pets.json{os.path.pathsep}.",
        f"--add-data=config.json{os.path.pathsep}.",
        f"--add-data=.env.example{os.path.pathsep}.",
    ]

    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onedir",
        "--name=win_pet",
        "--clean",
        "-y",
    ] + add_data_args + [os.path.join(BASE_DIR, "main.py")]

    print(f"[CMD] PyInstaller 명령어 실행중: {' '.join(pyinstaller_cmd)}\n")
    
    try:
        subprocess.check_call(pyinstaller_cmd, cwd=BASE_DIR)
        
        # 포터블 배포 폴더에 사용법 안내 txt 자동 생성
        dist_dir = os.path.join(BASE_DIR, "dist", "win_pet")
        if os.path.exists(dist_dir):
            readme_path = os.path.join(dist_dir, "비개발자_사용법_안내.txt")
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(
"""==================================================
  win-pet 무설치 포터블 데스크톱 펫 실행 방법 안내
==================================================

1. [win_pet.exe] 더블 클릭:
   - 본 폴더 안의 win_pet.exe 파일만 더블 클릭하시면 바탕화면에 귀여운 투명 픽셀 펫이 소환됩니다!

2. API 키 입력 방법:
   - 펫을 오른쪽 마우스 클릭하여 [API 키 설정...] 메뉴를 누르신 후,
     Google Gemini API 키를 넣으시면 바로 AI 대화가 시작됩니다.

3. 신규 펫 추가 방법:
   - assets/ 폴더 안에 새 펫 폴더(예: assets/my_cat)를 만들고 이미지를 넣으신 후,
     우클릭 메뉴 [펫 스킨 변경] -> [신규 펫 자동 정돈/추가...]를 누르시면 1초 만에 등록됩니다!

즐거운 시간 되세요!
"""
                )
            # 🔒 보안 조치: 배포본 config.json 내 개발자 API 키 자동 소거(Sanitize)
            dist_config_path = os.path.join(dist_dir, "config.json")
            if os.path.exists(dist_config_path):
                try:
                    with open(dist_config_path, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                    if "llm_api_key" in cfg_data:
                        cfg_data["llm_api_key"] = ""
                    with open(dist_config_path, "w", encoding="utf-8") as f:
                        json.dump(cfg_data, f, indent=2, ensure_ascii=False)
                    print("[SECURITY] 배포용 config.json 내 개발자 API 키 자동 소거 완료!")
                except Exception as e:
                    print(f"[WARN] config.json 소거 처리 중 알림: {e}")

            print("\n[SUCCESS] 무설치 포터블 패키지 빌드가 완료되었습니다!")
            print(f"[DIST] 배포용 폴더 위치: {dist_dir}")
            print(f"[EXE] 실행 파일 위치: {os.path.join(dist_dir, 'win_pet.exe')}")
    except Exception as e:
        print(f"\n[ERROR] 빌드 중 오류 발생: {e}")

if __name__ == "__main__":
    build_portable_package()
