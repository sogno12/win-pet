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
        
        # 1. 최우선: 내 앞으로 불러오기 & 숨기기/보이기 토글
        summon_action = QAction("✨ 내 앞으로 불러오기", self.pet_widget)
        summon_action.triggered.connect(self.pet_widget.summon_to_mouse)
        menu.addAction(summon_action)

        if self.pet_widget.isVisible():
            toggle_action = QAction("🙈 펫 잠시 숨기기 (트레이 보관)", self.pet_widget)
            toggle_action.triggered.connect(self.pet_widget.hide_pet)
        else:
            toggle_action = QAction("👀 펫 다시 보이기", self.pet_widget)
            toggle_action.triggered.connect(self.pet_widget.show_pet)
        menu.addAction(toggle_action)
        
        menu.addSeparator()

        # 2. 주요 기능 그룹: 캡처 -> 일정 -> 타이머/포모도로
        capture_action = QAction("📸 스마트 화면 캡처 (AI 분석 / OCR)", self.pet_widget)
        capture_action.triggered.connect(self.pet_widget.trigger_screen_capture)
        menu.addAction(capture_action)

        calendar_action = QAction("📅 일정 / 할 일(TODO) 관리...", self.pet_widget)
        calendar_action.triggered.connect(self.pet_widget.open_calendar_dialog)
        menu.addAction(calendar_action)

        timer_action = QAction("⏰ 펫 타이머 / 포모도로...", self.pet_widget)
        timer_action.triggered.connect(self.pet_widget.open_timer_dialog)
        menu.addAction(timer_action)

        menu.addSeparator()
        
        # 3. 펫 설정 및 화면 고정 그룹
        top_text = "📌 맨 위 고정 해제" if self.pet_widget.is_always_on_top else "📌 항상 위에 표시"
        top_action = QAction(top_text, self.pet_widget)
        top_action.triggered.connect(self.pet_widget.toggle_always_on_top)
        menu.addAction(top_action)

        autostart_action = QAction("🚀 윈도우 시작 시 자동 실행", self.pet_widget)
        autostart_action.setCheckable(True)
        autostart_action.setChecked(ConfigManager.is_autostart_enabled())
        autostart_action.triggered.connect(self.pet_widget.toggle_autostart)
        menu.addAction(autostart_action)

        self.pet_widget._build_pet_skin_menu(menu)
        self.pet_widget.build_size_menu(menu)
        self.pet_widget.build_speed_menu(menu)
        self.pet_widget.build_boundary_menu(menu)

        menu.addSeparator()
        
        # 4. 펫 상태창 및 시스템 정보 그룹 (API 키 설정 위에 펫 상태창 배치)
        status_action = QAction("📊 펫 상태창...", self.pet_widget)
        status_action.triggered.connect(self.pet_widget.open_status_dialog)
        menu.addAction(status_action)

        api_key_action = QAction("🔑 API 키 설정...", self.pet_widget)
        api_key_action.triggered.connect(self.pet_widget.open_api_key_dialog)
        menu.addAction(api_key_action)

        from core.logger import PetLogger
        log_action = QAction("📋 실행 및 API 이력 로그 보기...", self.pet_widget)
        log_action.triggered.connect(PetLogger.open_today_log)
        menu.addAction(log_action)

        menu.addSeparator()
        
        # 5. 맨 아래: 종료
        exit_action = QAction("❌ 종료", self.pet_widget)
        exit_action.triggered.connect(self.pet_widget.quit_app)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)

    def update_tray_menu(self):
        self.build_tray_menu()
