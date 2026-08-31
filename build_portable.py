import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def find_wincat_python():
    """PC 내 wincat 가상환경의 python.exe 위치 탐색"""
    possible_paths = [
        os.path.expanduser(r"~\miniconda3\envs\wincat\python.exe"),
        os.path.expanduser(r"~\anaconda3\envs\wincat\python.exe"),
        r"C:\miniconda3\envs\wincat\python.exe",
        r"C:\anaconda3\envs\wincat\python.exe",
        os.path.abspath(os.path.join(sys.executable, "..", "..", "envs", "wincat", "python.exe")),
        os.path.abspath(os.path.join(sys.executable, "..", "envs", "wincat", "python.exe")),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def verify_environment():
    """환경 오염 없는 안전한 PyQt6 / PyInstaller 구동 환경 검증"""
    try:
        import PyQt6
        import PyInstaller
        return sys.executable
    except ImportError:
        pass

    # 현재 환경에 PyQt6 또는 PyInstaller가 없는 경우 wincat 가상환경 자동 탐색
    wincat_py = find_wincat_python()
    if wincat_py and wincat_py != sys.executable:
        try:
            check_cmd = [wincat_py, "-c", "import PyQt6, PyInstaller"]
            res = subprocess.run(check_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                print(f"[INFO] 현재 환경에 PyQt6가 없어 wincat 가상환경({wincat_py})으로 빌드를 전달합니다.")
                return wincat_py
        except Exception:
            pass

    print("\n❌ [ERROR] 필수 라이브러리(PyQt6)가 설치된 파이썬 환경을 찾을 수 없습니다.")
    print("👉 현재 파이썬 환경을 더럽히지 않도록 자동 설치하지 않았습니다.")
    print("👉 터미널에서 [ conda activate wincat ] 을 실행하신 후 [ python build_portable.py ]를 다시 실행해 주세요!\n")
    sys.exit(1)

def build_portable_package():
    """win_pet 무설치 포터블 실행 패키지 빌드"""
    print("\n[BUILD] win_pet 무설치 포터블 실행 패키지 빌드를 시작합니다...")
    
    python_exe = verify_environment()

    # 빌드 전 실행 중인 win_pet.exe 프로세스 안전 종료 (파일 락 해제)
    try:
        subprocess.call(["taskkill", "/F", "/IM", "win_pet.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 동봉할 리소스 데이터 경로 설정 (Windows 릴리스)
    sep = os.pathsep
    add_data_args = [
        f"--add-data=assets{os.path.pathsep}assets",
        f"--add-data=pets.json.template{os.path.pathsep}.",
        f"--add-data=config.json.template{os.path.pathsep}.",
        f"--add-data=.env.example{os.path.pathsep}.",
    ]

    pyinstaller_cmd = [
        python_exe, "-m", "PyInstaller",
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

            # 1. 필수 리소스 및 설정 템플릿 파일을 dist/win_pet 루트로 복사
            # (유저 가변 데이터인 config.json/pets.json 대신 .template을 배포하여 복붙 덮어쓰기 시 기존 유저 설정 보존)
            sync_files = ["pets.json.template", "config.json.template", "pc_targets.json", ".env.example"]
            for f in sync_files:
                src_f = os.path.join(BASE_DIR, f)
                dst_f = os.path.join(dist_dir, f)
                if os.path.exists(src_f):
                    shutil.copy2(src_f, dst_f)

            # dist/win_pet 루트에 유저 설정 원본 파일이 존재한다면 삭제 (덮어쓰기 보호)
            for user_file in ["config.json", "pets.json"]:
                f_path = os.path.join(dist_dir, user_file)
                if os.path.exists(f_path):
                    try:
                        os.remove(f_path)
                    except Exception:
                        pass

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

4. 버전 업데이트 (덮어쓰기 안내):
   - 새 버전 빌드 후 파일들을 기존 사용 폴더에 그대로 덮어씌우셔도(Copy & Overwrite)
     기존 사용자의 설정, API 키, 일정, 펫 상태, 대화 기억이 100% 안전하게 유지됩니다!

즐거운 시간 되세요!
"""
                )

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
