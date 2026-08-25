import sys
import os

# 윈도우 시작 프로그램 자동 실행 시 작업 디렉터리(CWD)가 System32 등으로 변경되어 발생하는 경로 예외 완벽 방어
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

from PyQt6.QtWidgets import QApplication
from ui.pet_widget import PetWidget
from ui.tray_manager import TrayManager

def main():
    """win_pet 데스크톱 펫 애플리케이션 진입점"""
    app = QApplication(sys.argv)
    
    # 메인 펫 윈도우 생성
    pet = PetWidget()
    
    # 시스템 트레이 매니저 연결
    tray = TrayManager(pet)
    pet.set_tray_manager(tray)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
