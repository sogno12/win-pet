import sys
import os
import json
import random
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPixmap, QAction, QActionGroup, QIcon, QTransform, QCursor
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QMenu, QSystemTrayIcon

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
PETS_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "pets.json")

DEFAULT_CONFIG = {
    "current_pet": "cat_cheese",
    "pet_width": 48,
    "pet_height": 48,
    "is_always_on_top": True,
    "move_speed": 1,
    "anim_interval_ms": 140
}

DEFAULT_PETS = {
    "cat_cheese": {"name": "🧀 치즈태비 고양이", "enabled": True},
    "owl_white": {"name": "🦉 헤드위그 하얀 부엉이", "enabled": True}
}

def load_pets_registry():
    pets_data = DEFAULT_PETS.copy()
    if os.path.exists(PETS_REGISTRY_PATH):
        try:
            with open(PETS_REGISTRY_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                pets_data.update(loaded)
        except Exception as e:
            print(f"⚠️ pets.json 로드 실패: {e}")

    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    if os.path.exists(assets_dir):
        for item in os.listdir(assets_dir):
            item_path = os.path.join(assets_dir, item)
            if os.path.isdir(item_path) and item not in pets_data:
                pets_data[item] = {
                    "name": f"🐾 {item}",
                    "enabled": True
                }
                
    save_pets_registry(pets_data)
    return pets_data

def save_pets_registry(pets_data):
    try:
        with open(PETS_REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(pets_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ pets.json 저장 실패: {e}")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception as e:
            print(f"⚠️ 설정 로드 실패, 기본값 사용: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("💾 설정이 config.json에 저장되었습니다.")
    except Exception as e:
        print(f"❌ 설정 저장 실패: {e}")

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        
        self.config = load_config()
        self.pets_registry = load_pets_registry()
        
        self.current_pet = self.config.get("current_pet", "cat_cheese")
        if self.current_pet not in self.pets_registry:
            self.current_pet = "cat_cheese"
            
        self.pet_width = self.config.get("pet_width", 48)
        self.pet_height = self.config.get("pet_height", 48)
        self.is_always_on_top = self.config.get("is_always_on_top", True)
        self.move_speed = self.config.get("move_speed", 1)
        self.anim_interval = self.config.get("anim_interval_ms", 140)
        
        self.is_dragging = False
        self.drag_position = QPoint()
        self.direction = 1  # 1: 오른쪽, -1: 왼쪽
        self.state = "WALK" # "WALK", "IDLE", "DRAG", "HAPPY", "SPECIAL"
        
        self.init_window_flags()
        
        self.anim_frames = {
            "walk_r": [], "walk_l": [],
            "idle_r": [], "idle_l": [],
            "drag_r": None, "drag_l": None,
            "happy_r": [], "happy_l": [],
            "special_r": [], "special_l": []
        }
        self.current_frame_idx = 0
        self.load_and_cache_standard_assets()
        
        self.label = QLabel(self)
        self.label.resize(self.pet_width, self.pet_height)
        self.update_pet_image()
        
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.update_tooltip()
        
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.update_movement)
        self.move_timer.start(30)
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(self.anim_interval)
        
        self.state_timer = QTimer(self)
        self.state_timer.timeout.connect(self.update_behavior_state)
        self.state_timer.start(8000)
        
        self.init_tray_icon()
        
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 250, screen.height() - 150)
        self.show()

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

    def _load_folder_frames(self, folder_path):
        right_list, left_list = [], []
        if os.path.exists(folder_path):
            files = sorted([f for f in os.listdir(folder_path) if f.endswith((".png", ".jpg"))])
            for f in files:
                pix = QPixmap(os.path.join(folder_path, f))
                if not pix.isNull():
                    scaled_r = pix.scaled(
                        self.pet_width, self.pet_height, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.FastTransformation
                    )
                    flipped = pix.transformed(QTransform().scale(-1, 1))
                    scaled_l = flipped.scaled(
                        self.pet_width, self.pet_height, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.FastTransformation
                    )
                    right_list.append(scaled_r)
                    left_list.append(scaled_l)
        return right_list, left_list

    def load_and_cache_standard_assets(self):
        pet_dir = os.path.join(os.path.dirname(__file__), "assets", self.current_pet)
        if not os.path.exists(pet_dir):
            pet_dir = os.path.join(os.path.dirname(__file__), "assets", "cat_cheese")
            
        # (1) walk
        walk_dir = os.path.join(pet_dir, "walk")
        w_r, w_l = self._load_folder_frames(walk_dir)
        if not w_r:
            w_r, w_l = self._load_folder_frames(pet_dir)
            
        if not w_r:
            fallback = QPixmap(64, 64)
            fallback.fill(Qt.GlobalColor.transparent)
            w_r, w_l = [fallback], [fallback]
            
        self.anim_frames["walk_r"], self.anim_frames["walk_l"] = w_r, w_l
        
        # (2) idle
        idle_dir = os.path.join(pet_dir, "idle")
        i_r, i_l = self._load_folder_frames(idle_dir)
        self.anim_frames["idle_r"] = i_r if i_r else w_r
        self.anim_frames["idle_l"] = i_l if i_l else w_l
        
        # (3) drag
        drag_dir = os.path.join(pet_dir, "drag")
        d_r, d_l = self._load_folder_frames(drag_dir)
        if d_r:
            self.anim_frames["drag_r"], self.anim_frames["drag_l"] = d_r[0], d_l[0]
        else:
            drag_file = os.path.join(pet_dir, "drag.png")
            if os.path.exists(drag_file):
                pix = QPixmap(drag_file)
                if not pix.isNull():
                    scaled_r = pix.scaled(self.pet_width, self.pet_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
                    scaled_l = pix.transformed(QTransform().scale(-1, 1)).scaled(self.pet_width, self.pet_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
                    self.anim_frames["drag_r"], self.anim_frames["drag_l"] = scaled_r, scaled_l
            if not self.anim_frames["drag_r"]:
                self.anim_frames["drag_r"], self.anim_frames["drag_l"] = w_r[0], w_l[0]

        # (4) happy
        happy_dir = os.path.join(pet_dir, "happy")
        h_r, h_l = self._load_folder_frames(happy_dir)
        self.anim_frames["happy_r"] = h_r if h_r else w_r
        self.anim_frames["happy_l"] = h_l if h_l else w_l

        # (5) special
        special_dir = os.path.join(pet_dir, "special")
        s_r, s_l = self._load_folder_frames(special_dir)
        self.anim_frames["special_r"] = s_r if s_r else w_r
        self.anim_frames["special_l"] = s_l if s_l else w_l

    def update_pet_image(self):
        if self.is_dragging:
            pix = self.anim_frames["drag_r"] if self.direction == 1 else self.anim_frames["drag_l"]
            self.label.setPixmap(pix)
            return
            
        current_list = self.anim_frames["walk_r"] if self.direction == 1 else self.anim_frames["walk_l"]
        if self.state == "IDLE":
            current_list = self.anim_frames["idle_r"] if self.direction == 1 else self.anim_frames["idle_l"]
        elif self.state == "HAPPY":
            current_list = self.anim_frames["happy_r"] if self.direction == 1 else self.anim_frames["happy_l"]
        elif self.state == "SPECIAL":
            current_list = self.anim_frames["special_r"] if self.direction == 1 else self.anim_frames["special_l"]

        if current_list:
            idx = self.current_frame_idx % len(current_list)
            self.label.setPixmap(current_list[idx])

    def update_movement(self):
        if self.is_dragging or self.state in ["IDLE", "DRAG", "SPECIAL"]:
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
        if self.state == "IDLE":
            current_list = self.anim_frames["idle_r"]
        elif self.state == "HAPPY":
            current_list = self.anim_frames["happy_r"]
        elif self.state == "SPECIAL":
            current_list = self.anim_frames["special_r"]

        if current_list:
            self.current_frame_idx = (self.current_frame_idx + 1) % len(current_list)
            
        self.update_pet_image()

    def update_behavior_state(self):
        if self.is_dragging:
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
        if not self.is_dragging:
            self.state = "WALK"

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
            self.state = "WALK"
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.update_pet_image()
            event.accept()

    def _build_size_menu(self, parent_menu):
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

    # --- 우클릭 메뉴 ---
    def show_context_menu(self, global_pos):
        menu = QMenu(self)
        self.pets_registry = load_pets_registry()
        
        top_text = "📌 맨 위 고정 해제" if self.is_always_on_top else "📌 항상 위에 표시"
        toggle_top_action = QAction(top_text, self)
        toggle_top_action.triggered.connect(self.toggle_always_on_top)
        menu.addAction(toggle_top_action)
        
        self._build_pet_skin_menu(menu)
        self._build_size_menu(menu)
        
        menu.addSeparator()
        hide_action = QAction("🙈 숨기기 (트레이로)", self)
        hide_action.triggered.connect(self.hide)
        menu.addAction(hide_action)
        
        exit_action = QAction("❌ 종료", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_action)
        
        menu.exec(global_pos)

    def change_pet(self, pet_key):
        self.current_pet = pet_key
        self.config["current_pet"] = pet_key
        save_config(self.config)
        self.load_and_cache_standard_assets()
        self.update_pet_image()
        self.update_tooltip()
        if hasattr(self, 'tray_icon'):
            self.update_tray_menu()

    def toggle_always_on_top(self):
        self.is_always_on_top = not self.is_always_on_top
        self.config["is_always_on_top"] = self.is_always_on_top
        save_config(self.config)
        self.init_window_flags()
        self.show()
        self.summon_to_mouse()

    def summon_to_mouse(self):
        """✨ 딜레이(50ms) 후 마우스 커서 위치로 펫을 100% 강제 소환"""
        QTimer.singleShot(50, self._do_summon)

    def _do_summon(self):
        # 1. 창을 숨김 해제하고 무조건 보이기
        self.show()
        self.setHidden(False)
        
        # 2. 마우스 커서 위치 탐색
        mouse_pos = QCursor.pos()
        target_x = max(0, mouse_pos.x() - (self.pet_width // 2))
        target_y = max(0, mouse_pos.y() - (self.pet_height // 2))
        self.move(target_x, target_y)
        
        # 3. Windows OS Z-Order 강제 재설정하여 최상단으로 복구
        self.init_window_flags()
        self.show()
        self.raise_()
        self.activateWindow()

    def change_size(self, size):
        self.pet_width = size
        self.pet_height = size
        self.config["pet_width"] = size
        self.config["pet_height"] = size
        save_config(self.config)
        
        self.resize(size, size)
        self.label.resize(size, size)
        self.load_and_cache_standard_assets()
        self.update_pet_image()
        if hasattr(self, 'tray_icon'):
            self.update_tray_menu()

    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        if self.anim_frames["walk_r"]:
            self.tray_icon.setIcon(QIcon(self.anim_frames["walk_r"][0]))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
            
        self.update_tray_menu()
        self.tray_icon.show()

    def update_tray_menu(self):
        tray_menu = QMenu()
        self.pets_registry = load_pets_registry()
        
        summon_action = QAction("✨ 내 앞으로 불러오기 (마우스 위치로)", self)
        summon_action.triggered.connect(self.summon_to_mouse)
        tray_menu.addAction(summon_action)
        
        top_text = "📌 맨 위 고정 해제" if self.is_always_on_top else "📌 항상 위에 표시"
        toggle_top_action = QAction(top_text, self)
        toggle_top_action.triggered.connect(self.toggle_always_on_top_from_tray)
        tray_menu.addAction(toggle_top_action)
        
        self._build_pet_skin_menu(tray_menu)
        self._build_size_menu(tray_menu)
            
        tray_menu.addSeparator()
        
        show_action = QAction("🐾 펫 소환하기", self)
        show_action.triggered.connect(self.summon_to_mouse)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("🙈 트레이로 숨기기", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("❌ 종료", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)

    def toggle_always_on_top_from_tray(self):
        self.toggle_always_on_top()
        self.update_tray_menu()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = DesktopPet()
    sys.exit(app.exec())
