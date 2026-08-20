import random
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QAction, QActionGroup, QCursor
from PyQt6.QtWidgets import QWidget, QLabel, QMenu, QApplication

from core.config_manager import ConfigManager
from core.asset_loader import AssetLoader
from core.llm_client import LLMWorkerThread
from ui.speech_bubble import SpeechBubble
from ui.dialog_input import DialogInput

class PetWidget(QWidget):
    """바탕화면 픽셀 펫 투명 윈도우 GUI 클래스 (5단계 세분화 이동 속도 지원)"""
    
    def __init__(self, current_pet=None):
        super().__init__()
        
        # 1. 설정 및 레지스트리 로드
        self.config = ConfigManager.load_config()
        self.pets_registry = ConfigManager.load_pets_registry()
        
        self.current_pet = current_pet or self.config.get("current_pet", "turtle_green")
        if self.current_pet not in self.pets_registry:
            self.current_pet = "turtle_green"
            
        self.pet_width = self.config.get("pet_width", 48)
        self.pet_height = self.config.get("pet_height", 48)
        self.is_always_on_top = self.config.get("is_always_on_top", True)
        self.move_speed = self.config.get("move_speed", 1)
        self.move_timer_ms = self.config.get("move_timer_ms", 70)  # 기본값 70ms (천천히)
        self.boundary_mode = self.config.get("move_boundary_mode", "MEDIUM")
        
        # 💡 발걸음 프레임 속도 자동 싱크
        self.anim_interval = int(self.move_timer_ms * 2.8)
        
        self.is_dragging = False
        self.is_hovered = False
        self.mouse_press_pos = None
        self.drag_position = QPoint()
        
        # 2D 이동 방향 벡터
        self.direction_x = 1
        self.direction_y = 0
        self.facing_direction = 1
        
        self.state = "WALK" # "WALK", "IDLE", "DRAG", "HAPPY", "SPECIAL"
        self.tray_manager = None
        self.llm_worker = None
        
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
        
        # 5. 말풍선 및 입력창 UI 연동
        self.speech_bubble = SpeechBubble(self)
        self.dialog_input = DialogInput(self, self.on_user_question)
        
        # 호버 커서 & 툴팁
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.update_tooltip()
        
        # 마우스 추적 활성화
        self.setMouseTracking(True)
        
        # 6. 이동 타이머 세팅
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.update_movement)
        self.move_timer.start(self.move_timer_ms)
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(self.anim_interval)
        
        self.state_timer = QTimer(self)
        self.state_timer.timeout.connect(self.update_behavior_state)
        self.state_timer.start(6000)
        
        # 📍 홈 중심 좌표
        screen = QApplication.primaryScreen().geometry()
        init_x = screen.width() - 250
        init_y = screen.height() - 150
        self.move(init_x, init_y)
        self.origin_center = QPoint(init_x, init_y)
        self.show()

    def set_tray_manager(self, tray_manager):
        self.tray_manager = tray_manager

    def update_tooltip(self):
        pet_info = self.pets_registry.get(self.current_pet, {})
        pet_name = pet_info.get("name", self.current_pet)
        self.setToolTip(f"[{pet_name}] 🐾 좌클릭: 대화하기 | 우클릭: 메뉴 | 드래그: 이동")

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
            pix = self.anim_frames["drag_r"] if self.facing_direction == 1 else self.anim_frames["drag_l"]
            self.label.setPixmap(pix)
            return
            
        current_list = self.anim_frames["walk_r"] if self.facing_direction == 1 else self.anim_frames["walk_l"]
        is_dialog_open = hasattr(self, 'dialog_input') and self.dialog_input.isVisible()
        if self.state == "IDLE" or self.is_hovered or is_dialog_open:
            current_list = self.anim_frames["idle_r"] if self.facing_direction == 1 else self.anim_frames["idle_l"]
        elif self.state == "HAPPY":
            current_list = self.anim_frames["happy_r"] if self.facing_direction == 1 else self.anim_frames["happy_l"]
        elif self.state == "SPECIAL":
            current_list = self.anim_frames["special_r"] if self.facing_direction == 1 else self.anim_frames["special_l"]

        if current_list:
            idx = self.current_frame_idx % len(current_list)
            self.label.setPixmap(current_list[idx])

    def update_movement(self):
        is_dialog_open = hasattr(self, 'dialog_input') and self.dialog_input.isVisible()
        if self.is_dragging or self.is_hovered or is_dialog_open or self.state in ["IDLE", "DRAG", "SPECIAL"]:
            if self.speech_bubble.isVisible():
                self.speech_bubble.update_position()
            return
            
        current_pos = self.pos()
        screen = QApplication.screenAt(current_pos) or QApplication.primaryScreen()
        screen_geo = screen.geometry()
        
        limit_left = screen_geo.left()
        limit_right = screen_geo.right() - self.pet_width
        limit_top = screen_geo.top() + 10
        limit_bottom = screen_geo.bottom() - self.pet_height - 30
        
        if self.boundary_mode == "NARROW":
            radius = 120
            limit_left = max(limit_left, self.origin_center.x() - radius)
            limit_right = min(limit_right, self.origin_center.x() + radius)
            limit_top = max(limit_top, self.origin_center.y() - radius)
            limit_bottom = min(limit_bottom, self.origin_center.y() + radius)
        elif self.boundary_mode == "MEDIUM":
            radius = 280
            limit_left = max(limit_left, self.origin_center.x() - radius)
            limit_right = min(limit_right, self.origin_center.x() + radius)
            limit_top = max(limit_top, self.origin_center.y() - radius)
            limit_bottom = min(limit_bottom, self.origin_center.y() + radius)
        elif self.boundary_mode == "MONITOR":
            pass
        elif self.boundary_mode == "FREE":
            v_geo = QApplication.primaryScreen().virtualGeometry()
            limit_left = v_geo.left()
            limit_right = v_geo.right() - self.pet_width
            limit_top = v_geo.top() + 10
            limit_bottom = v_geo.bottom() - self.pet_height - 30

        new_x = current_pos.x() + (self.move_speed * self.direction_x)
        new_y = current_pos.y() + (self.move_speed * self.direction_y)
        
        if new_x <= limit_left:
            self.direction_x = 1
            self.facing_direction = 1
            new_x = limit_left
            self.update_pet_image()
        elif new_x >= limit_right:
            self.direction_x = -1
            self.facing_direction = -1
            new_x = limit_right
            self.update_pet_image()
            
        if new_y <= limit_top:
            self.direction_y = 1
            new_y = limit_top
        elif new_y >= limit_bottom:
            self.direction_y = -1
            new_y = limit_bottom
            
        self.move(new_x, new_y)
        
        if self.speech_bubble.isVisible():
            self.speech_bubble.update_position()

    def update_animation(self):
        if self.is_dragging or self.state == "DRAG":
            self.update_pet_image()
            return

        current_list = self.anim_frames["walk_r"]
        is_dialog_open = hasattr(self, 'dialog_input') and self.dialog_input.isVisible()
        if self.state == "IDLE" or self.is_hovered or is_dialog_open:
            current_list = self.anim_frames["idle_r"]
        elif self.state == "HAPPY":
            current_list = self.anim_frames["happy_r"]
        elif self.state == "SPECIAL":
            current_list = self.anim_frames["special_r"]

        if current_list:
            self.current_frame_idx = (self.current_frame_idx + 1) % len(current_list)
            
        self.update_pet_image()

    def update_behavior_state(self):
        is_dialog_open = hasattr(self, 'dialog_input') and self.dialog_input.isVisible()
        if self.is_dragging or self.is_hovered or is_dialog_open or self.speech_bubble.isVisible():
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
            self.direction_x = random.choice([-1, 1])
            self.direction_y = random.choice([-1, 0, 1])
            self.facing_direction = self.direction_x

    def resume_walking(self):
        is_dialog_open = hasattr(self, 'dialog_input') and self.dialog_input.isVisible()
        if not self.is_dragging and not self.is_hovered and not is_dialog_open and not self.speech_bubble.isVisible():
            self.state = "WALK"

    def enterEvent(self, event):
        self.is_hovered = True
        self.state = "IDLE"
        self.update_pet_image()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        is_dialog_open = hasattr(self, 'dialog_input') and self.dialog_input.isVisible()
        if not self.is_dragging and not is_dialog_open and not self.speech_bubble.isVisible():
            self.state = "WALK"
        self.update_pet_image()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_press_pos = event.globalPosition().toPoint()
            self.is_dragging = False
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            curr_pos = event.globalPosition().toPoint()
            if self.mouse_press_pos and (curr_pos - self.mouse_press_pos).manhattanLength() > 5:
                if not self.is_dragging:
                    self.is_dragging = True
                    self.state = "DRAG"
                    self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
                    self.update_pet_image()
                self.move(curr_pos - self.drag_position)
                if self.speech_bubble.isVisible():
                    self.speech_bubble.update_position()
                event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_dragging:
                self.open_dialog_input()
            else:
                self.is_dragging = False
                self.state = "IDLE" if self.is_hovered else "WALK"
                self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                self.origin_center = self.pos()
                self.update_pet_image()
            event.accept()

    def open_dialog_input(self):
        self.state = "IDLE"
        self.update_pet_image()
        self.dialog_input.popup_near_pet()

    def on_user_question(self, user_query):
        self.state = "IDLE"
        self.update_pet_image()
        self.speech_bubble.show_message("생각 중...", duration_ms=10000)
        
        self.llm_worker = LLMWorkerThread(self.current_pet, user_query)
        self.llm_worker.response_received.connect(self._handle_llm_response)
        self.llm_worker.start()

    def _handle_llm_response(self, response_text):
        self.speech_bubble.show_message(response_text, duration_ms=7000)

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

    def build_speed_menu(self, parent_menu):
        """🐢 5단계 이동 속도 선택 서브메뉴 빌더"""
        speed_menu = parent_menu.addMenu("🐢 펫 이동 속도")
        speed_group = QActionGroup(self)
        speed_group.setExclusive(True)
        
        speed_options = [
            ("🐢 느리게 (150ms - 엉금엉금)", 150),
            ("🍃 느긋하게 (100ms)", 100),
            ("🐾 천천히 (70ms)", 70),
            ("🎵 경쾌하게 (45ms)", 45),
            ("⚡ 빠르게 (30ms)", 30)
        ]
        for label, interval_ms in speed_options:
            act = QAction(label, self)
            act.setCheckable(True)
            if self.move_timer_ms == interval_ms:
                act.setChecked(True)
            act.triggered.connect(lambda checked, ms=interval_ms: self.change_speed(ms))
            speed_group.addAction(act)
            speed_menu.addAction(act)

    def build_boundary_menu(self, parent_menu):
        boundary_menu = parent_menu.addMenu("📍 펫 이동 범위")
        boundary_group = QActionGroup(self)
        boundary_group.setExclusive(True)
        
        boundary_options = [
            ("🤏 여기서만 좁게 (반경 120px)", "NARROW"),
            ("🏡 아늑하게 (반경 280px)", "MEDIUM"),
            ("🖥️ 현재 모니터 안에서만", "MONITOR"),
            ("🌐 자유롭게 (전체 바탕화면)", "FREE")
        ]
        for label, mode in boundary_options:
            act = QAction(label, self)
            act.setCheckable(True)
            if self.boundary_mode == mode:
                act.setChecked(True)
            act.triggered.connect(lambda checked, m=mode: self.change_boundary_mode(m))
            boundary_group.addAction(act)
            boundary_menu.addAction(act)

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
        self.build_speed_menu(menu)
        self.build_boundary_menu(menu)
        
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
        self.origin_center = self.pos()
        
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

    def change_speed(self, interval_ms):
        """🐢 5단계 이동 속도 변경 및 발걸음 프레임 완벽 동기화"""
        self.move_timer_ms = interval_ms
        self.config["move_timer_ms"] = interval_ms
        ConfigManager.save_config(self.config)
        
        self.move_timer.setInterval(interval_ms)
        self.anim_interval = int(interval_ms * 2.8)
        self.anim_timer.setInterval(self.anim_interval)
        
        if self.tray_manager:
            self.tray_manager.update_tray_menu()

    def change_boundary_mode(self, mode):
        self.boundary_mode = mode
        self.config["move_boundary_mode"] = mode
        ConfigManager.save_config(self.config)
        
        self.origin_center = self.pos()
        if self.tray_manager:
            self.tray_manager.update_tray_menu()

    def quit_app(self):
        if hasattr(self, 'speech_bubble'):
            self.speech_bubble.close()
        if hasattr(self, 'dialog_input'):
            self.dialog_input.close()
        QApplication.instance().quit()
