from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QLineEdit, QPushButton, QHBoxLayout, QApplication

class DialogInput(QDialog):
    """사용자가 펫에게 질문을 입력하는 팝업 대화창 (멀티 모니터 & 음수 좌표계 안전)"""
    
    def __init__(self, parent_widget, on_send_callback):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.on_send_callback = on_send_callback
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 1. 입력 필드
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("펫에게 질문 입력... (Esc: 취소)")
        self.input_field.setFont(QFont("Malgun Gothic", 9))
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 14px;
                padding: 6px 12px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        
        # 2. 전송 버튼
        send_btn = QPushButton("전송", self)
        send_btn.setFont(QFont("Malgun Gothic", 9, QFont.Weight.Bold))
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 14px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        send_btn.clicked.connect(self.send_message)

        # 3. 취소 버튼
        cancel_btn = QPushButton("취소", self)
        cancel_btn.setFont(QFont("Malgun Gothic", 9))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border-radius: 14px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self.cancel_dialog)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)
        layout.addWidget(self.input_field)
        layout.addWidget(send_btn)
        layout.addWidget(cancel_btn)
        
        self.resize(320, 42)

    def popup_near_pet(self):
        """멀티 모니터 음수 좌표계에서도 OS 레벨 경고 없이 안전하게 대화창 팝업"""
        pet_geo = self.parent_widget.geometry()
        
        screen = QApplication.screenAt(pet_geo.center()) or QApplication.primaryScreen()
        screen_geo = screen.geometry()
        
        dialog_w = self.width()
        dialog_h = self.height()
        
        pos_x = pet_geo.x() + (pet_geo.width() // 2) - (dialog_w // 2)
        pos_y = pet_geo.y() + pet_geo.height() + 8
        
        pos_x = max(screen_geo.left() + 5, min(pos_x, screen_geo.right() - dialog_w - 5))
        pos_y = max(screen_geo.top() + 5, min(pos_y, screen_geo.bottom() - dialog_h - 5))
        
        self.move(pos_x, pos_y)
        
        self.input_field.setText("")
        self.input_field.clear()
        
        self.show()
        self.activateWindow()
        self.input_field.setFocus()

    def send_message(self):
        query = self.input_field.text().strip()
        self.input_field.setText("")
        self.input_field.clear()
        
        if query:
            self.hide()
            self.on_send_callback(query)

    def cancel_dialog(self):
        self.input_field.setText("")
        self.input_field.clear()
        self.hide()
        if hasattr(self.parent_widget, 'resume_walking'):
            self.parent_widget.resume_walking()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_dialog()
            event.accept()
        else:
            super().keyPressEvent(event)
