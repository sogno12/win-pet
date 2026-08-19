import sys
import os
import json
import random
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPixmap, QAction, QIcon, QTransform, QCursor
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QMenu, QSystemTrayIcon

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "current_pet": "cat_cheese",
    "pet_width": 80,
    "pet_height": 80,
    "is_always_on_top": True,
    "move_speed": 1,
    "anim_interval_ms": 140
}

# 기본 펫 이름 맵핑
PET_NAME_MAP = {
    "cat_cheese": "🧀 치즈태비 고양이",
    "owl_white": "🦉 헤드위그 하얀 부엉이",
    "tiger": "🐯 아기 호랑이",
    "penguin": "🐧 핑구 펭귄"
}

def scan_available_pets():
    """assets/ 폴더를 스캔하여 존재하는 모든 펫 스킨 리스트 자동 반환"""
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    available = {}
    if os.path.exists(assets_dir):
        for item in os.listdir(assets_dir):
            item_path = os.path.join(assets_dir, item)
            if os.path.isdir(item_path):
                display_name = PET_NAME_MAP.get(item, f"🐾 {item}")
                available[item] = display_name
    if not available:
        available["cat_cheese"] = "🧀 치즈태비 고양이"
    return available

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
        
        # 1. config.json 로드
        self.config = load_config()
        self.available_pets = scan_available_pets()
        
        self.current_pet = self.config.get("current_pet", "cat_cheese")
        if self.current_pet not in self.available_pets:
            self.current_pet = list(self.available_pets.keys())[0]
            
        self.pet_width = self.config.get("pet_width", 80)
        self.pet_height = self.config.get("pet_height", 80)
        self.is_always_on_top = self.config.get("is_always_on_top", True)
        self.move_speed = self.config.get("move_speed", 1)
        self.anim_interval = self.config.get("anim_interval_ms", 140)
        
        self.is_dragging = False
        self.drag_position = QPoint()
        self.direction = 1  # 1: 오른쪽, -1: 왼쪽
        self.state = "WALK" # "WALK", "IDLE", "DRAG", "HAPPY", "SPECIAL"
        
        # 2. 창 투명화 및 무테두리 설정
        self.init_window_flags()
        
        # 3. 표준 에셋 캐싱
        self.anim_frames = {
            "walk_r": [], "walk_l": [],
            "idle_r": [], "idle_l": [],
            "drag_r": None, "drag_l": None,
            "happy_r": [], "happy_l": [],
            "special_r": [], "special_l": []
        }
        self.current_frame_idx = 0
        self.load_and_cache_standard_assets()
        
        # 4. UI 구성
        self.label = QLabel(self)
        self.label.resize(self.pet_width, self.pet_height)
        self.update_pet_image()
        
        # 호버 커서 & 툴팁
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.update_tooltip()
        
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
        
        # 6. 시스템 트레이 아이콘
        self.init_tray_icon()
        
        # 초기 위치 설정
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 250, screen.height() - 150)
        self.show()

    def update_tooltip(self):
        pet_name = self.available_pets.get(self.current_pet, self.current_pet)
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

    # --- 우클릭 메뉴 ---
    def show_context_menu(self, global_pos):
        menu = QMenu(self)
        self.available_pets = scan_available_pets()
        
        top_text = "📌 맨 위 고정 해제" if self.is_always_on_top else "📌 항상 위에 표시"
        toggle_top_action = QAction(top_text, self)
        toggle_top_action.triggered.connect(self.toggle_always_on_top)
        menu.addAction(toggle_top_action)
        
        # 동적 펫 스킨 목록
        pet_menu = menu.addMenu("🐾 펫 스킨 변경")
        for pet_key, pet_name in self.available_pets.items():
            pet_action = QAction(pet_name, self)
            pet_action.setCheckable(True)
            if self.current_pet == pet_key:
                pet_action.setChecked(True)
            pet_action.triggered.connect(lambda checked, k=pet_key: self.change_pet(k))
            pet_menu.addAction(pet_action)
            
        size_menu = menu.addMenu("📏 펫 크기")
        small_action = QAction("작게 (48px)", self)
        medium_action = QAction("보통 (80px)", self)
        large_action = QAction("크게 (120px)", self)
        
        small_action.triggered.connect(lambda: self.change_size(48))
        medium_action.triggered.connect(lambda: self.change_size(80))
        large_action.triggered.connect(lambda: self.change_size(120))
        
        size_menu.addAction(small_action)
        size_menu.addAction(medium_action)
        size_menu.addAction(large_action)
        
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
        if hasattr(self, 'tray_icon') and self.anim_frames["walk_r"]:
            self.tray_icon.setIcon(QIcon(self.anim_frames["walk_r"][0]))

    def toggle_always_on_top(self):
        self.is_always_on_top = not self.is_always_on_top
        self.config["is_always_on_top"] = self.is_always_on_top
        save_config(self.config)
        self.init_window_flags()
        self.show()
        self.bring_to_front()

    def bring_to_front(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
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
        self.available_pets = scan_available_pets()
        
        bring_front_action = QAction("✨ 내 앞으로 불러오기", self)
        bring_front_action.triggered.connect(self.bring_to_front)
        tray_menu.addAction(bring_front_action)
        
        top_text = "📌 맨 위 고정 해제" if self.is_always_on_top else "📌 항상 위에 표시"
        toggle_top_action = QAction(top_text, self)
        toggle_top_action.triggered.connect(self.toggle_always_on_top_from_tray)
        tray_menu.addAction(toggle_top_action)
        
        pet_menu = tray_menu.addMenu("🐾 펫 스킨 변경")
        for pet_key, pet_name in self.available_pets.items():
            pet_action = QAction(pet_name, self)
            pet_action.setCheckable(True)
            if self.current_pet == pet_key:
                pet_action.setChecked(True)
            pet_action.triggered.connect(lambda checked, k=pet_key: self.change_pet(k))
            pet_menu.addAction(pet_action)
            
        tray_menu.addSeparator()
        
        show_action = QAction("🐾 펫 소환하기", self)
        show_action.triggered.connect(self.bring_to_front)
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
