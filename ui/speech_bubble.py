from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication

class SpeechBubble(QWidget):
    """텍스트 길이에 따라 동적으로 크기가 늘어나는 듀얼 모니터 완벽 지원 말풍선 UI"""
    
    def __init__(self, target_widget):
        super().__init__()
        self.target_widget = target_widget
        
        # 윈도우 프레임리스 설정
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 텍스트 라벨 (멀티라인 짤림 방지 높이 자동 확장)
        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Malgun Gothic", 9, QFont.Weight.Bold))
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 245);
                color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 12px;
                padding: 10px 14px;
            }
        """)
        
        # 너비 범위 제약 (최소 200px ~ 최대 340px)
        self.label.setMinimumWidth(200)
        self.label.setMaximumWidth(340)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.label)
        
        self.typing_timer = QTimer(self)
        self.typing_timer.timeout.connect(self._update_typing)
        
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_bubble)
        
        self.full_text = ""
        self.current_idx = 0
        self.duration_ms = 6000
        
    def show_message(self, text, duration_ms=6000):
        self.hide_timer.stop()
        self.full_text = text
        self.current_idx = 0
        self.duration_ms = duration_ms
        self.label.setText("")
        
        self.show()
        self._update_size_and_position()
        
        self.typing_timer.start(25)  # 25ms 타이핑 속도

    def _update_typing(self):
        if self.current_idx < len(self.full_text):
            self.current_idx += 1
            self.label.setText(self.full_text[:self.current_idx])
            self._update_size_and_position()
        else:
            # 💡 타이핑이 완전히 완료된 직후부터 hide_timer 카운트다운 시작 (duration_ms <= 0 일 경우 클릭 시까지 영구 유지)
            self.typing_timer.stop()
            if self.duration_ms > 0:
                self.hide_timer.start(self.duration_ms)

    def _update_size_and_position(self):
        self.label.adjustSize()
        self.adjustSize()
        self.update_position()

    def update_position(self):
        if not self.target_widget or not self.target_widget.isVisible():
            self.hide()
            return
            
        pet_geo = self.target_widget.geometry()
        
        # 넉넉한 렌더링 높이 확보
        bubble_size = self.sizeHint()
        bubble_w = max(self.width(), bubble_size.width(), 200)
        bubble_h = max(self.height(), bubble_size.height(), 40)
        
        screen = QApplication.screenAt(pet_geo.center()) or QApplication.primaryScreen()
        screen_geo = screen.geometry()
        
        pos_x = pet_geo.x() + (pet_geo.width() // 2) - (bubble_w // 2)
        pos_y = pet_geo.y() - bubble_h - 8
        
        pos_x = max(screen_geo.left() + 5, min(pos_x, screen_geo.right() - bubble_w - 5))
        pos_y = max(screen_geo.top() + 5, min(pos_y, screen_geo.bottom() - bubble_h - 5))
        
        self.setGeometry(pos_x, pos_y, bubble_w, bubble_h)

    def hide_bubble(self):
        self.typing_timer.stop()
        self.hide()
