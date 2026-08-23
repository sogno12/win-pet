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
        
        dist_dir = os.path.join(BASE_DIR, "dist", "win_pet")
        if os.path.exists(dist_dir):
            import shutil
            import json

            # 1. 필수 리소스 및 설정 파일을 dist/win_pet 루트로 복사
            # (포터블 실행 시 사용자가 assets를 추가하거나 pets.json을 수정할 수 있도록 루트에 배치)
            sync_files = ["pets.json", "config.json", "pc_targets.json", ".env.example"]
            for f in sync_files:
                src_f = os.path.join(BASE_DIR, f)
                dst_f = os.path.join(dist_dir, f)
                if os.path.exists(src_f):
                    shutil.copy2(src_f, dst_f)

            sync_dirs = ["assets", "prompts"]
            for d in sync_dirs:
                src_d = os.path.join(BASE_DIR, d)
                dst_d = os.path.join(dist_dir, d)
                if os.path.exists(src_d):
                    if os.path.exists(dst_d):
                        shutil.rmtree(dst_d, ignore_errors=True)
                    shutil.copytree(src_d, dst_d)

            # 사용법 안내 텍스트 생성
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

            # 보안 조치: config.json 내 API 키 소거
            dist_config_path = os.path.join(dist_dir, "config.json")
            if os.path.exists(dist_config_path):
                try:
                    with open(dist_config_path, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                    for k in ["llm_api_key", "gemini_api_key"]:
                        if k in cfg_data:
                            del cfg_data[k]
                    with open(dist_config_path, "w", encoding="utf-8") as f:
                        json.dump(cfg_data, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass

            # 2. 사용자 혼란 방지를 위해 build/ 임시 폴더 및 .spec 파일 정리
            build_dir = os.path.join(BASE_DIR, "build")
            if os.path.exists(build_dir):
                shutil.rmtree(build_dir, ignore_errors=True)
            spec_file = os.path.join(BASE_DIR, "win_pet.spec")
            if os.path.exists(spec_file):
                try:
                    os.remove(spec_file)
                except Exception:
                    pass

            print("\n[SUCCESS] 무설치 포터블 패키지 빌드가 완벽하게 완료되었습니다!")
            print(f"[DIST] 배포용 폴더 위치: {dist_dir}")
            print(f"[EXE] 실행 파일 위치: {os.path.join(dist_dir, 'win_pet.exe')}")
    except Exception as e:
        print(f"\n[ERROR] 빌드 중 오류 발생: {e}")

if __name__ == "__main__":
    build_portable_package()
