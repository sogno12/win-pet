import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt
from core.config_manager import ConfigManager

class DialogApiKey(QDialog):
    """🔑 비개발자 친구용 Gemini API 키 입력 팝업 UI (보안 마스킹 및 안정 복호화 적용)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Gemini API 키 설정")
        self.setFixedSize(420, 200)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        info_label = QLabel("🐱 win_pet 대화를 시작하려면 Gemini API 키가 필요합니다!\n입력하신 키는 PC 고유 암호화로 .env 파일에 안전하게 보관됩니다.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 13px; color: #333; line-height: 1.4;")
        layout.addWidget(info_label)

        # 입력 필드 및 보기/숨기기 토글 버튼 레이아웃
        input_container = QHBoxLayout()
        input_container.setSpacing(6)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("AIzaSy...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setStyleSheet("""
            QLineEdit {
                padding: 8px; 
                border: 1px solid #ccc; 
                border-radius: 5px; 
                font-size: 13px;
                background-color: #fff;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """)
        
        # 기존 저장된 정상 키가 있으면 표시
        saved_key = ConfigManager.get_api_key()
        if saved_key:
            self.key_input.setText(saved_key)

        self.toggle_btn = QPushButton("👁️")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setFixedSize(38, 36)
        self.toggle_btn.setToolTip("API 키 보기 / 숨기기")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0; 
                border: 1px solid #ccc; 
                border-radius: 5px; 
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #e4e4e4;
            }
            QPushButton:checked {
                background-color: #dcdcdc;
            }
        """)
        self.toggle_btn.toggled.connect(self.on_toggle_visibility)

        input_container.addWidget(self.key_input)
        input_container.addWidget(self.toggle_btn)
        layout.addLayout(input_container)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        save_btn = QPushButton("💾 저장하고 시작하기")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; border: none; 
                padding: 8px 16px; border-radius: 5px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        save_btn.clicked.connect(self.save_key)

        cancel_btn = QPushButton("취소")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575; color: white; border: none; 
                padding: 8px 16px; border-radius: 5px; font-size: 13px;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def on_toggle_visibility(self, checked):
        if checked:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def save_key(self):
        api_key = self.key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "경고", "API 키를 입력해 주세요!")
            return

        if not api_key.startswith("AIzaSy"):
            reply = QMessageBox.question(
                self,
                "API 키 형식 확인",
                "입력하신 키가 일반적인 Gemini API 키 형식('AIzaSy...')과 다릅니다.\n이대로 저장하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        ConfigManager.save_api_key(api_key)

        QMessageBox.information(self, "완료", "✨ API 키가 PC 고유 암호화로 .env 보안 파일에 성공적으로 저장되었습니다!")
        self.accept()
