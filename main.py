import sys
import os
import json
import random
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPixmap, QAction, QIcon, QTransform, QCursor
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QMenu, QSystemTrayIcon

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "pet_width": 80,
    "pet_height": 80,
    "is_always_on_top": True,
    "move_speed": 1,
    "anim_interval_ms": 140
}

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
        self.pet_width = self.config.get("pet_width", 80)
        self.pet_height = self.config.get("pet_height", 80)
        self.is_always_on_top = self.config.get("is_always_on_top", True)
        self.move_speed = self.config.get("move_speed", 1)
        self.anim_interval = self.config.get("anim_interval_ms", 140)
        
        self.is_dragging = False
        self.drag_position = QPoint()
        self.direction = 1  # 1: 오른쪽, -1: 왼쪽
        self.state = "WALK" # "WALK", "IDLE"
        
        # 2. 창 투명화 및 무테두리 설정
        self.init_window_flags()
        
        # 3. 프레임 이미지 캐싱
        self.raw_frames = []
        self.cached_right = []
        self.cached_left = []
        self.current_frame_idx = 0
        self.load_and_cache_frames()
        
        # 4. UI 구성 (픽셀 라벨 및 호버 커서/툴팁)
        self.label = QLabel(self)
        self.label.resize(self.pet_width, self.pet_height)
        self.update_pet_image()
        
        # 호버 커서 & 툴팁
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("🐾 우클릭: 설정 메뉴 | 좌클릭: 드래그 이동")
        
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
        
        # 초기 위치 설정 (화면 우하단)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 250, screen.height() - 150)
        self.show()

    def init_window_flags(self):
        """윈도우 투명화, 무테두리, 항상 위 설정"""
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow
        if self.is_always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
            
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.resize(self.pet_width, self.pet_height)

    def load_and_cache_frames(self):
        """assets/cat/ 프레임을 정방향(우) 및 역방향(좌)으로 사전 캐싱"""
        assets_dir = os.path.join(os.path.dirname(__file__), "assets", "cat")
        self.raw_frames = []
        self.cached_right = []
        self.cached_left = []
        
        if os.path.exists(assets_dir):
            files = sorted([f for f in os.listdir(assets_dir) if f.endswith((".png", ".jpg"))])
            for file in files:
                pix = QPixmap(os.path.join(assets_dir, file))
                if not pix.isNull():
                    self.raw_frames.append(pix)
                    
        if not self.raw_frames:
            fallback = QPixmap(64, 64)
            fallback.fill(Qt.GlobalColor.transparent)
            self.raw_frames = [fallback]
            
        for pix in self.raw_frames:
            scaled_r = pix.scaled(
                self.pet_width, 
                self.pet_height, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.FastTransformation
            )
            self.cached_right.append(scaled_r)
            
            flipped = pix.transformed(QTransform().scale(-1, 1))
            scaled_l = flipped.scaled(
                self.pet_width, 
                self.pet_height, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.FastTransformation
            )
            self.cached_left.append(scaled_l)

    def update_pet_image(self):
        if not self.cached_right:
            return
            
        idx = self.current_frame_idx % len(self.cached_right)
        if self.direction == 1:
            self.label.setPixmap(self.cached_right[idx])
        else:
            self.label.setPixmap(self.cached_left[idx])

    def update_movement(self):
        if self.is_dragging or self.state == "IDLE":
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
        if self.state == "IDLE":
            self.current_frame_idx = 0
        else:
            if self.cached_right:
                self.current_frame_idx = (self.current_frame_idx + 1) % len(self.cached_right)
                
        self.update_pet_image()

    def update_behavior_state(self):
        if self.is_dragging:
            return
            
        if random.random() < 0.3:
            self.state = "IDLE"
            QTimer.singleShot(random.randint(3000, 5000), self.resume_walking)
        else:
            self.state = "WALK"
            if random.random() < 0.4:
                self.direction *= -1

    def resume_walking(self):
        if not self.is_dragging:
            self.state = "WALK"

    # --- 마우스 이벤트 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
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
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            event.accept()

    # --- 펫 자체 우클릭 컨텍스트 메뉴 ---
    def show_context_menu(self, global_pos):
        menu = QMenu(self)
        
        top_text = "📌 맨 위 고정 해제" if self.is_always_on_top else "📌 항상 위에 표시"
        toggle_top_action = QAction(top_text, self)
        toggle_top_action.triggered.connect(self.toggle_always_on_top)
        menu.addAction(toggle_top_action)
        
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

    def toggle_always_on_top(self):
        self.is_always_on_top = not self.is_always_on_top
        self.config["is_always_on_top"] = self.is_always_on_top
        save_config(self.config)
        self.init_window_flags()
        self.show()
        self.bring_to_front()

    def bring_to_front(self):
        """펫을 현재 모든 화면의 맨 앞으로 즉시 끌어올려 노출"""
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
        self.load_and_cache_frames()
        self.update_pet_image()

    # --- 트레이 아이콘 & 우클릭 메뉴 ---
    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        if self.raw_frames:
            self.tray_icon.setIcon(QIcon(self.raw_frames[0]))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
            
        self.update_tray_menu()
        self.tray_icon.show()

    def update_tray_menu(self):
        """트레이 우클릭 메뉴 동적 생성"""
        tray_menu = QMenu()
        
        # 1. 펫을 내 앞으로 가져오기 (Bring to Front)
        bring_front_action = QAction("✨ 내 앞으로 불러오기", self)
        bring_front_action.triggered.connect(self.bring_to_front)
        tray_menu.addAction(bring_front_action)
        
        # 2. 항상 위에 표시 토글
        top_text = "📌 맨 위 고정 해제" if self.is_always_on_top else "📌 항상 위에 표시 (Always on Top)"
        toggle_top_action = QAction(top_text, self)
        toggle_top_action.triggered.connect(self.toggle_always_on_top_from_tray)
        tray_menu.addAction(toggle_top_action)
        
        tray_menu.addSeparator()
        
        # 3. 소환하기 / 숨기기
        show_action = QAction("🐾 펫 소환하기 / 보이기", self)
        show_action.triggered.connect(self.bring_to_front)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("🙈 트레이로 숨기기", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        # 4. 종료
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
