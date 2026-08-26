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
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        """트레이 아이콘 클릭/더블클릭 시 숨겨진 펫을 보이기/소환"""
        if reason in [QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick]:
            if not self.pet_widget.isVisible():
                self.pet_widget.show_pet()
            else:
                self.pet_widget.summon_to_mouse()
        
    def update_icon(self):
        pix = AssetLoader.get_icon_pixmap(self.pet_widget.current_pet)
        icon = QIcon(pix)
        self.tray_icon.setIcon(icon)
        
        pet_info = self.pet_widget.pets_registry.get(self.pet_widget.current_pet, {})
        pet_name = pet_info.get("name", self.pet_widget.current_pet)
        self.tray_icon.setToolTip(f"🐾 win_pet ({pet_name})")

    def build_tray_menu(self):
        menu = QMenu()
        
        # 1. 트레이 아이콘 1순위: 내 앞으로 불러오기
        summon_action = QAction("✨ 내 앞으로 불러오기", self.pet_widget)
        summon_action.triggered.connect(self.pet_widget.summon_to_mouse)
        menu.addAction(summon_action)

        # 2. 동적 menu_layout 커스텀 메뉴 구성 반영
        self.pet_widget.build_dynamic_menu(menu)
        self.tray_icon.setContextMenu(menu)

    def update_tray_menu(self):
        self.build_tray_menu()
