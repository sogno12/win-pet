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
        self.is_range_overlay_always_on = False

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

        # 💡 최초 1회 API 키 등록 안내 팝업 점검 (800ms 후)
        QTimer.singleShot(800, self.check_first_run_api_key_prompt)

        # 💡 ScheduleAgent 시그널 바인딩 (타이머 알림 & 포모도로 전환)
        from core.schedule_agent import ScheduleAgent
        sched = ScheduleAgent.get_instance()
        sched.timer_triggered.connect(self._on_schedule_timer_triggered)
        sched.pomodoro_phase_changed.connect(self._on_pomodoro_phase_changed)

        # 💡 CalendarAgent 시그널 바인딩 (사전 알림 & 아침 브리핑)
        from core.calendar_agent import CalendarAgent
        cal = CalendarAgent.get_instance()
        cal.schedule_reminded.connect(self._on_schedule_reminded)
        cal.briefing_ready.connect(self._on_briefing_ready)

        # ☀️ 아침 첫 실행 시 1회 브리핑 점검 (1500ms 후)
        QTimer.singleShot(1500, self.check_morning_briefing)

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

        # 안개 구름 중심 좌표 (cx, cy)
        cx = self.origin_center.x() + self.pet_width // 2
        cy = self.origin_center.y() + self.pet_height // 2

        if self.boundary_mode in ["VERY_NARROW", "NARROW", "MEDIUM"]:
            radius = 60 if self.boundary_mode == "VERY_NARROW" else (120 if self.boundary_mode == "NARROW" else 280)
            
            # 💡 펫의 몸통 전체가 안개 구름 [cx - radius ~ cx + radius] 내에 100% 갇히도록 한계 정합!
            cloud_left = cx - radius
            cloud_right = cx + radius - self.pet_width
            cloud_top = cy - radius
            cloud_bottom = cy + radius - self.pet_height

            limit_left = max(limit_left, cloud_left)
            limit_right = min(limit_right, cloud_right)
            limit_top = max(limit_top, cloud_top)
            limit_bottom = min(limit_bottom, cloud_bottom)
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
            current_list = self.anim_frames.get("happy_r") or self.anim_frames.get("idle_r")
        elif self.state == "SPECIAL":
            current_list = self.anim_frames.get("special_r") or self.anim_frames.get("idle_r")

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
                if self.is_range_overlay_always_on:
                    self.show_boundary_overlay(self.boundary_mode)
                event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.speech_bubble.isVisible():
                self.speech_bubble.hide_bubble()
                self.state = "IDLE"
                self.update_pet_image()
            if not self.is_dragging:
                from core.status_agent import StatusAgent
                StatusAgent.interact("pat")
                self.open_dialog_input()
            else:
                self.is_dragging = False
                self.state = "IDLE" if self.is_hovered else "WALK"
                self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                self.origin_center = self.pos()
                self.update_pet_image()

                # 💡 마우스로 끌어다 놓아 이동 범위가 재설정된 순간 안개 구름 미리보기 무조건 팝업!
                self.show_boundary_overlay(self.boundary_mode)
            event.accept()

    def check_first_run_api_key_prompt(self):
        """최초 구동 시 API 키 미설정 상태라면 1회 등록 안내 팝업 표시"""
        api_key = ConfigManager.get_api_key()
        prompted = self.config.get("api_key_prompted", False)

        if not api_key and not prompted:
            from PyQt6.QtWidgets import QMessageBox
            ans = QMessageBox.question(
                self,
                "✨ win_pet AI 서비스 안내",
                "반가워요! 펫과 대화를 나누고 PC 제어/날씨/검색 기능을 이용하시려면 무료 Gemini API 키가 필요합니다.\n\n"
                "지금 API 키를 등록하시겠어요?\n\n"
                "('아니오'를 누르시면 대화 없이 픽셀 펫 모드로 얌전하게 거닐며, 나중에 우클릭 메뉴에서 언제든 등록하실 수 있습니다.)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            self.config["api_key_prompted"] = True
            ConfigManager.save_config(self.config)

            if ans == QMessageBox.StandardButton.Yes:
                self.open_api_key_dialog()

    def open_dialog_input(self):
        """펫 클릭 시 대화 입력창을 엽니다 (API 키 미설정 시 부담 없이 무반응)"""
        api_key = ConfigManager.get_api_key()
        if not api_key:
            return

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

        # 1. 언제든 다시 안개 영역을 확인하는 버튼
        preview_act = QAction("🔍 현재 이동 범위 미리보기 (안개 보기)", self)
        preview_act.triggered.connect(lambda: self.show_boundary_overlay(self.boundary_mode))
        boundary_menu.addAction(preview_act)

        # 2. 이동 범위 안개 지속 고정 토글 액션 (테스트용)
        toggle_always_act = QAction("👁️ 이동 범위 안개 항상 켜기 (테스트 고정용)", self)
        toggle_always_act.setCheckable(True)
        toggle_always_act.setChecked(self.is_range_overlay_always_on)
        toggle_always_act.triggered.connect(self.toggle_always_on_boundary_overlay)
        boundary_menu.addAction(toggle_always_act)

        boundary_menu.addSeparator()

        boundary_group = QActionGroup(self)
        boundary_group.setExclusive(True)

        boundary_options = [
            ("🤏 구석에서 놀기 (반경 60px)", "VERY_NARROW"),
            ("🐾 좁게 (반경 120px)", "NARROW"),
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

        pet_menu.addSeparator()
        add_new_act = QAction("✨ 신규 펫 자동 정돈/추가...", self)
        add_new_act.triggered.connect(self.scan_and_add_new_pets_gui)
        pet_menu.addAction(add_new_act)

    def open_api_key_dialog(self):
        from ui.dialog_api_key import DialogApiKey
        dlg = DialogApiKey(self)
        if dlg.exec() == DialogApiKey.DialogCode.Accepted:
            self.config = ConfigManager.load_config()

    def scan_and_add_new_pets_gui(self):
        """✨ [GUI 0순위] assets/ 신규 폴더 탐지 ➔ 수정가능한 기본 이름 팝업 ➔ 3단계 배경 제거 오토 파이프라인"""
        import os
        from PyQt6.QtWidgets import QInputDialog, QMessageBox
        from pet_generator import organize_and_convert_pet_pack

        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
        if not os.path.exists(assets_dir):
            QMessageBox.warning(self, "경고", "assets/ 폴더를 찾을 수 없습니다.")
            return

        unregistered = []
        for item in os.listdir(assets_dir):
            item_path = os.path.join(assets_dir, item)
            if os.path.isdir(item_path) and item not in self.pets_registry:
                unregistered.append(item)

        if not unregistered:
            QMessageBox.information(
                self, "안내",
                "ℹ️ 새로 추가할 미등록 펫 폴더가 없습니다.\n\n"
                "새 펫을 추가하시려면 assets/ 폴더 안에 새 폴더(예: assets/my_rabbit)를 만들어 이미지를 넣은 후 이 버튼을 눌러주세요!"
            )
            return

        added_count = 0
        for folder_id in unregistered:
            # 기본 디폴트 이름 생성 (수정 가능!)
            default_display_name = f"🐾 {folder_id.replace('_', ' ').title()}"

            pet_name, ok = QInputDialog.getText(
                self,
                f"✨ 신규 펫 [{folder_id}] 등록",
                f"[{folder_id}] 펫이 탐지되었습니다!\n메뉴에 표시할 예쁜 이름을 입력해 주세요 (수정 가능):",
                text=default_display_name
            )

            if not ok or not pet_name.strip():
                pet_name = default_display_name

            # 3단계 오토 파이프라인 구동
            if organize_and_convert_pet_pack(folder_id, pet_name.strip()):
                added_count += 1

        if added_count > 0:
            self.pets_registry = ConfigManager.load_pets_registry()
            QMessageBox.information(self, "성공", f"🎉 {added_count}개의 신규 펫이 스마트 배경 제거 후 메뉴에 추가 등록되었습니다!")
            if self.tray_manager:
                self.tray_manager.update_tray_menu()

    def _on_schedule_timer_triggered(self, timer_id, memo):
        self.state = "HAPPY" if "HAPPY" in self.anim_frames and self.anim_frames["HAPPY"] else "IDLE"
        self.update_pet_image()
        # duration_ms=0: 유저가 클릭으로 확인할 때까지 영구 표시
        self.speech_bubble.show_message(f"⏰ [알림] '{memo}' 시간이 다 되었어요! (클릭하여 확인)", duration_ms=0)

    def _on_pomodoro_phase_changed(self, phase, msg, cycle_count, remaining_secs):
        if phase == "REST_START":
            self.state = "HAPPY" if "HAPPY" in self.anim_frames and self.anim_frames["HAPPY"] else "IDLE"
        elif phase == "WORK_START":
            self.state = "IDLE"
        elif phase == "STOPPED":
            self.state = "IDLE"
        self.update_pet_image()
        # duration_ms=0: 유저가 클릭으로 확인할 때까지 영구 표시
        self.speech_bubble.show_message(f"{msg} (클릭하여 확인)", duration_ms=0)

    def _on_schedule_reminded(self, sched_id, title, remind_type):
        """10분 전 사전 일정/TODO 알림 발생 시 펫 반응"""
        self.state = "HAPPY" if "HAPPY" in self.anim_frames and self.anim_frames["HAPPY"] else "IDLE"
        self.update_pet_image()
        self.speech_bubble.show_message(f"⏰ [알림] '{title}' ({remind_type}) (클릭하여 확인)", duration_ms=0)

    def _on_briefing_ready(self, briefing_text):
        """아침 브리핑 출력"""
        if briefing_text:
            self.state = "HAPPY" if "HAPPY" in self.anim_frames and self.anim_frames["HAPPY"] else "IDLE"
            self.update_pet_image()
            self.speech_bubble.show_message(briefing_text, duration_ms=12000)

    def check_morning_briefing(self):
        """아침 06~12시 최초 1회 브리핑 시도"""
        from core.calendar_agent import CalendarAgent
        briefing = CalendarAgent.get_instance().get_morning_briefing(force=False)
        if briefing:
            self._on_briefing_ready(briefing)

    def open_calendar_dialog(self):
        """일정 / 할 일 관리 팝업 열기"""
        from ui.dialog_calendar import CalendarDialog
        dlg = CalendarDialog(self)
        dlg.exec()

    def open_timer_dialog(self):
        from ui.dialog_timer import DialogTimer
        dlg = DialogTimer(self)
        dlg.exec()

    def toggle_autostart(self):
        from PyQt6.QtWidgets import QMessageBox
        enabled = not ConfigManager.is_autostart_enabled()
        if ConfigManager.set_autostart(enabled):
            status_str = "등록" if enabled else "해제"
            QMessageBox.information(self, "성공", f"🚀 윈도우 시작 시 자동 실행이 {status_str}되었습니다.")

    def open_status_dialog(self):
        from ui.dialog_status import DialogStatus
        dlg = DialogStatus(self)
        dlg.exec()

    def show_context_menu(self, global_pos):
        menu = QMenu(self)
        self.pets_registry = ConfigManager.load_pets_registry()

        status_action = QAction("📊 펫 상태창...", self)
        status_action.triggered.connect(self.open_status_dialog)
        menu.addAction(status_action)

        calendar_action = QAction("📅 일정 / 할 일(TODO) 관리...", self)
        calendar_action.triggered.connect(self.open_calendar_dialog)
        menu.addAction(calendar_action)

        timer_action = QAction("⏰ 펫 타이머 / 포모도로...", self)
        timer_action.triggered.connect(self.open_timer_dialog)
        menu.addAction(timer_action)

        menu.addSeparator()

        top_text = "📌 맨 위 고정 해제" if self.is_always_on_top else "📌 항상 위에 표시"
        toggle_top_action = QAction(top_text, self)
        toggle_top_action.triggered.connect(self.toggle_always_on_top)
        menu.addAction(toggle_top_action)

        autostart_action = QAction("🚀 윈도우 시작 시 자동 실행", self)
        autostart_action.setCheckable(True)
        autostart_action.setChecked(ConfigManager.is_autostart_enabled())
        autostart_action.triggered.connect(self.toggle_autostart)
        menu.addAction(autostart_action)

        self._build_pet_skin_menu(menu)
        self.build_size_menu(menu)
        self.build_speed_menu(menu)
        self.build_boundary_menu(menu)

        menu.addSeparator()
        api_key_action = QAction("🔑 API 키 설정...", self)
        api_key_action.triggered.connect(self.open_api_key_dialog)
        menu.addAction(api_key_action)

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

        self.show_boundary_overlay(mode)

    def toggle_always_on_boundary_overlay(self):
        """테스트/확인용 이동 범위 안개 지속 고정 토글"""
        from ui.range_overlay import RangeOverlay
        self.is_range_overlay_always_on = not self.is_range_overlay_always_on
        if self.is_range_overlay_always_on:
            self.show_boundary_overlay(self.boundary_mode)
        else:
            RangeOverlay.hide_overlay()
        if self.tray_manager:
            self.tray_manager.update_tray_menu()

    def show_boundary_overlay(self, mode):
        """이동 범위 변경 시 은은한 솜사탕 구름 반투명 안개 영역 표시 (지정된 origin_center 기준 고정)"""
        from PyQt6.QtCore import QRect
        from PyQt6.QtWidgets import QApplication
        from ui.range_overlay import RangeOverlay

        screen = QApplication.screenAt(self.origin_center) or QApplication.primaryScreen()
        screen_geo = screen.geometry()

        preview_rect = QRect()

        # 💡 현재 펫의 실시간 이동 위치가 아니라, 이미 지정된 origin_center 기준으로 안개 표시!
        cx = self.origin_center.x() + self.pet_width // 2
        cy = self.origin_center.y() + self.pet_height // 2

        if mode == "VERY_NARROW":
            radius = 60
            preview_rect = QRect(cx - radius, cy - radius, radius * 2, radius * 2)
        elif mode == "NARROW":
            radius = 120
            preview_rect = QRect(cx - radius, cy - radius, radius * 2, radius * 2)
        elif mode == "MEDIUM":
            radius = 280
            preview_rect = QRect(cx - radius, cy - radius, radius * 2, radius * 2)
        elif mode == "MONITOR":
            preview_rect = screen_geo
        elif mode == "FREE":
            v_geo = QApplication.primaryScreen().virtualGeometry()
            preview_rect = v_geo

        if not preview_rect.isEmpty():
            RangeOverlay.show_preview(preview_rect, always_on=self.is_range_overlay_always_on)

    def quit_app(self):
        if hasattr(self, 'speech_bubble'):
            self.speech_bubble.close()
        if hasattr(self, 'dialog_input'):
            self.dialog_input.close()
        QApplication.instance().quit()
