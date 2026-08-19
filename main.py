import sys
from PyQt6.QtWidgets import QApplication
from ui.pet_widget import PetWidget
from ui.tray_manager import TrayManager

def main():
    """win_cat 데스크톱 펫 애플리케이션 진입점"""
    app = QApplication(sys.argv)
    
    # 메인 펫 윈도우 생성
    pet = PetWidget()
    
    # 시스템 트레이 매니저 연결
    tray = TrayManager(pet)
    pet.set_tray_manager(tray)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
