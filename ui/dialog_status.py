from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QFrame
)
from PyQt6.QtGui import QFont, QColor
from core.status_agent import StatusAgent
from core.config_manager import ConfigManager

class DialogStatus(QDialog):
    """우클릭 메뉴에서 펫의 3대 상태지수 및 친밀도를 시각적으로 확인하는 상태창 GUI 팝업"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 펫 상태 및 친밀도")
        self.setFixedSize(340, 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. 펫 타이틀 & 친밀도 레벨 뱃지
        status = StatusAgent.load_status()
        level, title = StatusAgent.get_affection_level(status.get("affection", 30))

        title_label = QLabel(f"📊 {title}")
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # 2. 친밀도 (Affection)
        aff_val = status.get("affection", 30)
        layout.addLayout(self._create_bar_row("💖 친밀도", aff_val, "#FF6B81"))

        # 3. 행복도 (Happiness)
        hap_val = status.get("happiness", 50)
        layout.addLayout(self._create_bar_row("✨ 행복도", hap_val, "#FF9FF3"))

        # 4. 심심함 (Boredom)
        bor_val = status.get("boredom", 20)
        layout.addLayout(self._create_bar_row("💤 심심함", bor_val, "#FECA57"))

        # 구분선
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line2)

        # 마지막 상호작용 시간
        last_time = status.get("last_interaction_time") or "기록 없음"
        time_label = QLabel(f"🕒 최근 놀아준 시각: {last_time}")
        time_label.setStyleSheet("color: #78909C; font-size: 11px;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(time_label)

        # 5. 닫기 버튼
        close_btn = QPushButton("확인")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #546E7A;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def _create_bar_row(self, label_text: str, val: int, color_hex: str) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        hdr_layout = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-weight: bold; font-size: 12px;")
        val_lbl = QLabel(f"{val} / 100")
        val_lbl.setStyleSheet("color: #555555; font-size: 11px;")
        hdr_layout.addWidget(lbl)
        hdr_layout.addStretch()
        hdr_layout.addWidget(val_lbl)

        pbar = QProgressBar()
        pbar.setRange(0, 100)
        pbar.setValue(val)
        pbar.setTextVisible(False)
        pbar.setFixedHeight(12)
        pbar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #CFD8DC;
                border-radius: 6px;
                background-color: #ECEFF1;
            }}
            QProgressBar::chunk {{
                background-color: {color_hex};
                border-radius: 5px;
            }}
        """)

        vbox.addLayout(hdr_layout)
        vbox.addWidget(pbar)
        return vbox
