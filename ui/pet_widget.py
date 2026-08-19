import random
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QAction, QActionGroup, QCursor
from PyQt6.QtWidgets import QWidget, QLabel, QMenu, QApplication

from core.config_manager import ConfigManager
from core.asset_loader import AssetLoader

class PetWidget(QWidget):
    """바탕화면 픽셀 펫 투명 윈도우 GUI 클래스"""
    
    def __init__(self, current_pet=None):
        super().__init__()
        
        # 1. 설정 및 레지스트리 로드
        self.config = ConfigManager.load_config()
        self.pets_registry = ConfigManager.load_pets_registry()
        
        self.current_pet = current_pet or self.config.get("current_pet", "cat_cheese")
        if self.current_pet not in self.pets_registry:
            self.current_pet = "cat_cheese"
            
        self.pet_width = self.config.get("pet_width", 48)
        self.pet_height = self.config.get("pet_height", 48)
        self.is_always_on_top = self.config.get("is_always_on_top", True)
        self.move_speed = self.config.get("move_speed", 1)
        self.anim_interval = self.config.get("anim_interval_ms", 140)
        
        self.is_dragging = False
        self.is_hovered = False  # 🔥 마우스 호버 감지 플래그
        self.drag_position = QPoint()
        self.direction = 1  # 1: 오른쪽, -1: 왼쪽
        self.state = "WALK" # "WALK", "IDLE", "DRAG", "HAPPY", "SPECIAL"
        self.tray_manager = None
        
        # 2. 창 투명화 및 무테두리 설정
        self.init_window_flags()
        
        # 3. 에셋 로딩
        self.anim_frames = {}
        self.current_frame_idx = 0
        self.reload_assets()
        
        # 4. UI 렌더링 라벨
        self.label = QLabel(self)
        self.label.resize(self.pet_width, self.pet_height)
        self.update_pet_image()
        
        # 호버 커서 & 툴팁
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.update_tooltip()
        
        # 마우스 추적 활성화
        self.setMouseTracking(True)
        
        # 5. 독립된 타이머 세팅
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.update_movement)
        self.move_timer.start(30)
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(self.anim_interval)
        
        self.state_timer = QTimer(self)
        self.state_timer.timeout.connect(self.update_behavior_state)
        self.state_timer.start(8000)
        
        # 초기 위치 배치
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 250, screen.height() - 150)
        self.show()

    def set_tray_manager(self, tray_manager):
        self.tray_manager = tray_manager

    def update_tooltip(self):
        pet_info = self.pets_registry.get(self.current_pet, {})
        pet_name = pet_info.get("name", self.current_pet)
        self.setToolTip(f"[{pet_name}] 🐾 우클릭: 메뉴 | 좌클릭: 잡아서 이동")

    def init_window_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow
        if self.is_always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
            
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.resize(self.pet_width, self.pet_height)

    def reload_assets(self):
        self.anim_frames = AssetLoader.load_pet_assets(
            self.current_pet, self.pet_width, self.pet_height
        )

    def update_pet_image(self):
        if self.is_dragging:
            pix = self.anim_frames["drag_r"] if self.direction == 1 else self.anim_frames["drag_l"]
            self.label.setPixmap(pix)
            return
            
        current_list = self.anim_frames["walk_r"] if self.direction == 1 else self.anim_frames["walk_l"]
        if self.state == "IDLE" or self.is_hovered:
            current_list = self.anim_frames["idle_r"] if self.direction == 1 else self.anim_frames["idle_l"]
        elif self.state == "HAPPY":
            current_list = self.anim_frames["happy_r"] if self.direction == 1 else self.anim_frames["happy_l"]
        elif self.state == "SPECIAL":
            current_list = self.anim_frames["special_r"] if self.direction == 1 else self.anim_frames["special_l"]

        if current_list:
            idx = self.current_frame_idx % len(current_list)
            self.label.setPixmap(current_list[idx])

    def update_movement(self):
        # 🔥 마우스 호버 중이거나, 드래그 중이거나, IDLE/SPECIAL 상태면 이동 일시정지!
        if self.is_dragging or self.is_hovered or self.state in ["IDLE", "DRAG", "SPECIAL"]:
            return
            
        current_pos = self.pos()
        new_x = current_pos.x() + (self.move_speed * self.direction)
        
        screen_geo = QApplication.primaryScreen().geometry()
        if new_x <= 0:
            self.direction = 1
            new_x = 0
            self.update_pet_image()
        elif new_x >= screen_geo.width() - self.pet_width:
            self.direction = -1
            new_x = screen_geo.width() - self.pet_width
            self.update_pet_image()
            
        self.move(new_x, current_pos.y())

    def update_animation(self):
        if self.is_dragging or self.state == "DRAG":
            self.update_pet_image()
            return

        current_list = self.anim_frames["walk_r"]
        if self.state == "IDLE" or self.is_hovered:
            current_list = self.anim_frames["idle_r"]
        elif self.state == "HAPPY":
            current_list = self.anim_frames["happy_r"]
        elif self.state == "SPECIAL":
            current_list = self.anim_frames["special_r"]

        if current_list:
            self.current_frame_idx = (self.current_frame_idx + 1) % len(current_list)
            
        self.update_pet_image()

    def update_behavior_state(self):
        if self.is_dragging or self.is_hovered:
            return
            
        rand = random.random()
        if rand < 0.25:
            self.state = "IDLE"
            QTimer.singleShot(random.randint(3000, 5000), self.resume_walking)
        elif rand < 0.35 and self.anim_frames["special_r"]:
            self.state = "SPECIAL"
            QTimer.singleShot(random.randint(4000, 6000), self.resume_walking)
        else:
            self.state = "WALK"
            if random.random() < 0.4:
                self.direction *= -1

    def resume_walking(self):
        if not self.is_dragging and not self.is_hovered:
            self.state = "WALK"

    # 🔥 마우스 커서 진입 (호버 시작)
    def enterEvent(self, event):
        self.is_hovered = True
        self.state = "IDLE"
        self.update_pet_image()
        super().enterEvent(event)

    # 🔥 마우스 커서 이탈 (호버 해제)
    def leaveEvent(self, event):
        self.is_hovered = False
        if not self.is_dragging:
            self.state = "WALK"
        self.update_pet_image()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.state = "DRAG"
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            self.update_pet_image()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.state = "IDLE" if self.is_hovered else "WALK"
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.update_pet_image()
            event.accept()

    def build_size_menu(self, parent_menu):
        size_menu = parent_menu.addMenu("📏 펫 크기")
        size_group = QActionGroup(self)
        size_group.setExclusive(True)
        
        size_options = [
            ("🔹 매우 작게 (24px)", 24),
            ("🔸 작게 (32px)", 32),
            ("⭐️ 기본 (48px)", 48),
            ("🔹 보통 (64px)", 64),
            ("🔸 크게 (96px)", 96),
            ("🌟 매우 크게 (128px)", 128)
        ]
        for label, sz in size_options:
            act = QAction(label, self)
            act.setCheckable(True)
            if self.pet_width == sz:
                act.setChecked(True)
            act.triggered.connect(lambda checked, s=sz: self.change_size(s))
            size_group.addAction(act)
            size_menu.addAction(act)

    def _build_pet_skin_menu(self, parent_menu):
        pet_menu = parent_menu.addMenu("🐾 펫 스킨 변경")
        pet_group = QActionGroup(self)
        pet_group.setExclusive(True)
        
        for pet_key, pet_info in self.pets_registry.items():
            if not pet_info.get("enabled", True):
                continue
                
            pet_name = pet_info.get("name", pet_key)
            pet_action = QAction(pet_name, self)
            pet_action.setCheckable(True)
            if self.current_pet == pet_key:
                pet_action.setChecked(True)
            pet_action.triggered.connect(lambda checked, k=pet_key: self.change_pet(k))
            pet_group.addAction(pet_action)
            pet_menu.addAction(pet_action)

    def show_context_menu(self, global_pos):
        menu = QMenu(self)
        self.pets_registry = ConfigManager.load_pets_registry()
        
        top_text = "📌 맨 위 고정 해제" if self.is_always_on_top else "📌 항상 위에 표시"
        toggle_top_action = QAction(top_text, self)
        toggle_top_action.triggered.connect(self.toggle_always_on_top)
        menu.addAction(toggle_top_action)
        
        self._build_pet_skin_menu(menu)
        self.build_size_menu(menu)
        
        menu.addSeparator()
        hide_action = QAction("🙈 숨기기 (트레이로)", self)
        hide_action.triggered.connect(self.hide)
        menu.addAction(hide_action)
        
        exit_action = QAction("❌ 종료", self)
        exit_action.triggered.connect(self.quit_app)
        menu.addAction(exit_action)
        
        menu.exec(global_pos)

    def change_pet(self, pet_key):
        self.current_pet = pet_key
        self.config["current_pet"] = pet_key
        ConfigManager.save_config(self.config)
        self.reload_assets()
        self.update_pet_image()
        self.update_tooltip()
        if self.tray_manager:
            self.tray_manager.update_icon()
            self.tray_manager.update_tray_menu()

    def toggle_always_on_top(self):
        self.is_always_on_top = not self.is_always_on_top
        self.config["is_always_on_top"] = self.is_always_on_top
        ConfigManager.save_config(self.config)
        self.init_window_flags()
        self.show()
        self.summon_to_mouse()
        if self.tray_manager:
            self.tray_manager.update_tray_menu()

    def summon_to_mouse(self):
        QTimer.singleShot(50, self._do_summon)

    def _do_summon(self):
        self.show()
        self.setHidden(False)
        mouse_pos = QCursor.pos()
        target_x = max(0, mouse_pos.x() - (self.pet_width // 2))
        target_y = max(0, mouse_pos.y() - (self.pet_height // 2))
        self.move(target_x, target_y)
        
        self.init_window_flags()
        self.show()
        self.raise_()
        self.activateWindow()

    def change_size(self, size):
        self.pet_width = size
        self.pet_height = size
        self.config["pet_width"] = size
        self.config["pet_height"] = size
        ConfigManager.save_config(self.config)
        
        self.resize(size, size)
        self.label.resize(size, size)
        self.reload_assets()
        self.update_pet_image()
        if self.tray_manager:
            self.tray_manager.update_tray_menu()

    def quit_app(self):
        QApplication.instance().quit()
