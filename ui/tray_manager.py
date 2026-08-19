from PyQt6.QtGui import QAction, QActionGroup, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon
from core.config_manager import ConfigManager

class TrayManager:
    """시스템 트레이 아이콘 및 우클릭 트레이 메뉴 전담 관리 클래스"""
    
    def __init__(self, pet_widget):
        self.pet_widget = pet_widget
        self.tray_icon = QSystemTrayIcon(self.pet_widget)
        self.init_tray_icon()

    def init_tray_icon(self):
        self.update_icon()
        self.update_tray_menu()
        self.tray_icon.show()

    def update_icon(self):
        if self.pet_widget.anim_frames["walk_r"]:
            self.tray_icon.setIcon(QIcon(self.pet_widget.anim_frames["walk_r"][0]))
        else:
            self.tray_icon.setIcon(self.pet_widget.style().standardIcon(self.pet_widget.style().StandardPixmap.SP_ComputerIcon))

    def update_tray_menu(self):
        tray_menu = QMenu()
        pets_registry = ConfigManager.load_pets_registry()
        
        # 1. 순간이동 소환 버튼
        summon_action = QAction("✨ 내 앞으로 불러오기 (마우스 위치로)", self.pet_widget)
        summon_action.triggered.connect(self.pet_widget.summon_to_mouse)
        tray_menu.addAction(summon_action)
        
        # 2. 맨 위 고정 토글
        top_text = "📌 맨 위 고정 해제" if self.pet_widget.is_always_on_top else "📌 항상 위에 표시"
        toggle_top_action = QAction(top_text, self.pet_widget)
        toggle_top_action.triggered.connect(self.pet_widget.toggle_always_on_top)
        tray_menu.addAction(toggle_top_action)
        
        # 3. 🐾 펫 스킨 변경 (QActionGroup 단일 체크)
        pet_menu = tray_menu.addMenu("🐾 펫 스킨 변경")
        pet_group = QActionGroup(self.pet_widget)
        pet_group.setExclusive(True)
        
        for pet_key, pet_info in pets_registry.items():
            if not pet_info.get("enabled", True):
                continue
                
            pet_name = pet_info.get("name", pet_key)
            pet_action = QAction(pet_name, self.pet_widget)
            pet_action.setCheckable(True)
            if self.pet_widget.current_pet == pet_key:
                pet_action.setChecked(True)
            pet_action.triggered.connect(lambda checked, k=pet_key: self.pet_widget.change_pet(k))
            pet_group.addAction(pet_action)
            pet_menu.addAction(pet_action)
            
        # 4. 📏 펫 크기 서브메뉴
        self.pet_widget.build_size_menu(tray_menu)
            
        tray_menu.addSeparator()
        
        show_action = QAction("🐾 펫 소환하기", self.pet_widget)
        show_action.triggered.connect(self.pet_widget.summon_to_mouse)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("🙈 트레이로 숨기기", self.pet_widget)
        hide_action.triggered.connect(self.pet_widget.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("❌ 종료", self.pet_widget)
        exit_action.triggered.connect(self.pet_widget.quit_app)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
