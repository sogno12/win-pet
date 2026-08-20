from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from core.asset_loader import AssetLoader
from core.config_manager import ConfigManager

class TrayManager:
    """시스템 트레이 아이콘 및 컨텍스트 메뉴 관리 클래스"""
    
    def __init__(self, pet_widget):
        self.pet_widget = pet_widget
        self.tray_icon = QSystemTrayIcon(self.pet_widget)
        
        self.update_icon()
        self.build_tray_menu()
        self.tray_icon.show()
        
    def update_icon(self):
        pix = AssetLoader.get_icon_pixmap(self.pet_widget.current_pet)
        icon = QIcon(pix)
        self.tray_icon.setIcon(icon)
        
        pet_info = self.pet_widget.pets_registry.get(self.pet_widget.current_pet, {})
        pet_name = pet_info.get("name", self.pet_widget.current_pet)
        self.tray_icon.setToolTip(f"🐾 win_pet ({pet_name})")

    def build_tray_menu(self):
        menu = QMenu()
        
        # 1. 내 앞으로 불러오기
        summon_action = QAction("✨ 내 앞으로 불러오기", self.pet_widget)
        summon_action.triggered.connect(self.pet_widget.summon_to_mouse)
        menu.addAction(summon_action)

        # 펫 상태창
        status_action = QAction("📊 펫 상태창...", self.pet_widget)
        status_action.triggered.connect(self.pet_widget.open_status_dialog)
        menu.addAction(status_action)
        
        menu.addSeparator()
        
        # 2. 펫 스킨 변경 서브메뉴
        self.pet_widget._build_pet_skin_menu(menu)
        
        # 3. 펫 크기 서브메뉴
        self.pet_widget.build_size_menu(menu)
        
        # 4. 🐢 펫 이동 속도 서브메뉴
        self.pet_widget.build_speed_menu(menu)
        
        # 5. 📍 펫 이동 범위 서브메뉴 (새로 추가!)
        self.pet_widget.build_boundary_menu(menu)
        
        menu.addSeparator()
        
        # 6. 항상 위에 표시 토글
        top_text = "📌 맨 위 고정 해제" if self.pet_widget.is_always_on_top else "📌 항상 위에 표시"
        top_action = QAction(top_text, self.pet_widget)
        top_action.triggered.connect(self.pet_widget.toggle_always_on_top)
        menu.addAction(top_action)
        
        # API 키 설정
        api_key_action = QAction("🔑 API 키 설정...", self.pet_widget)
        api_key_action.triggered.connect(self.pet_widget.open_api_key_dialog)
        menu.addAction(api_key_action)

        # 7. 숨기기 / 보이기 토글
        if self.pet_widget.isVisible():
            toggle_action = QAction("🙈 숨기기", self.pet_widget)
            toggle_action.triggered.connect(self.pet_widget.hide)
        else:
            toggle_action = QAction("👀 보이기", self.pet_widget)
            toggle_action.triggered.connect(self.pet_widget.show)
        menu.addAction(toggle_action)
        
        menu.addSeparator()
        
        # 8. 종료
        exit_action = QAction("❌ 종료", self.pet_widget)
        exit_action.triggered.connect(self.pet_widget.quit_app)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)

    def update_tray_menu(self):
        self.build_tray_menu()
