import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt
from core.config_manager import ConfigManager

class DialogApiKey(QDialog):
    """🔑 비개발자 친구용 Gemini API 키 입력 팝업 UI"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Gemini API 키 설정")
        self.setFixedSize(400, 180)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        info_label = QLabel("🐱 win_cat 대화를 시작하려면 Gemini API 키가 필요합니다!\nAPI 키를 입력하시면 config.json에 영구 저장됩니다.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 13px; color: #333; line-height: 1.4;")
        layout.addWidget(info_label)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("AIzaSy...")
        
        # 기존 저장된 키가 있으면 표시
        config = ConfigManager.load_config()
        saved_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
        if saved_key:
            self.key_input.setText(saved_key)
            
        self.key_input.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 5px; font-size: 13px;")
        layout.addWidget(self.key_input)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 저장하고 시작하기")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; border: none; 
                padding: 8px 16px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        save_btn.clicked.connect(self.save_key)

        cancel_btn = QPushButton("취소")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; color: white; border: none; 
                padding: 8px 16px; border-radius: 5px;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def save_key(self):
        api_key = self.key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "경고", "API 키를 입력해 주세요!")
            return

        config = ConfigManager.load_config()
        config["gemini_api_key"] = api_key
        ConfigManager.save_config(config)
        os.environ["GEMINI_API_KEY"] = api_key

        QMessageBox.information(self, "완료", "✨ API 키가 성공적으로 저장되었습니다!")
        self.accept()
