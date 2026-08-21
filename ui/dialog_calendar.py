import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem, QCheckBox,
    QWidget, QMessageBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from core.calendar_agent import CalendarAgent
import datetime

class CalendarDialog(QDialog):
    """일정(Event) 및 할 일(TODO)을 시각적으로 확인하고 추가/삭제/체크하는 아기자기한 다크 테마 GUI 팝업"""

    schedule_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent = CalendarAgent.get_instance()
        self.setWindowTitle("📅 펫의 일정 & 할 일(TODO) 노트")
        self.setFixedSize(480, 560)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #202225;
                color: #FFFFFF;
                border-radius: 12px;
            }
            QLabel {
                color: #ECEFF4;
                font-family: 'Segoe UI', '맑은 고딕';
            }
            QLineEdit, QComboBox {
                background-color: #2F3136;
                color: #FFFFFF;
                border: 1px solid #40444B;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #7289DA;
            }
            QPushButton {
                background-color: #5865F2;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
            QPushButton#btn_delete {
                background-color: #ED4245;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton#btn_delete:hover {
                background-color: #C03537;
            }
            QListWidget {
                background-color: #2F3136;
                border: 1px solid #40444B;
                border-radius: 8px;
                padding: 6px;
            }
            QListWidget::item {
                background-color: #36393F;
                border-radius: 6px;
                margin-bottom: 5px;
                padding: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # 1. 헤더 (오늘 날짜 및 타이틀)
        header_layout = QHBoxLayout()
        today_str = datetime.datetime.now().strftime("%Y/%m/%d (%a)")
        title_label = QLabel(f"🐾 오늘의 스케줄 노트")
        title_label.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        
        date_label = QLabel(today_str)
        date_label.setStyleSheet("color: #99AAB5; font-size: 13px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(date_label)
        layout.addLayout(header_layout)

        # 2. 일정 / TODO 리스트 위젯
        self.list_widget = QListWidget()
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        layout.addWidget(self.list_widget)

        # 3. 신규 항목 추가 패널
        add_frame = QFrame()
        add_frame.setStyleSheet("background-color: #2A2C30; border-radius: 8px; padding: 6px;")
        add_layout = QVBoxLayout(add_frame)
        add_layout.setSpacing(8)

        add_title = QLabel("➕ 새 일정 / 할 일 추가")
        add_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        add_title.setStyleSheet("color: #7289DA;")
        add_layout.addWidget(add_title)

        # 첫 번째 줄: 제목 입력
        self.input_title = QLineEdit()
        self.input_title.setPlaceholderText("내용을 입력하세요 (예: 치과 진료, 파이썬 코딩)")
        add_layout.addWidget(self.input_title)

        # 두 번째 줄: 날짜, 시간, 유형 선택
        row2 = QHBoxLayout()
        self.input_date = QLineEdit()
        self.input_date.setText("오늘")
        self.input_date.setPlaceholderText("오늘 / 내일 / YYYY/MM/DD")
        self.input_date.setFixedWidth(110)

        self.input_time = QLineEdit()
        self.input_time.setText("15:00")
        self.input_time.setPlaceholderText("시간 (예: 15:00 / 종일)")
        self.input_time.setFixedWidth(100)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["일정 (📌 Event)", "할 일 (✅ TODO)"])
        self.combo_type.setFixedWidth(130)

        btn_add = QPushButton("추가")
        btn_add.clicked.connect(self._add_item)

        row2.addWidget(self.input_date)
        row2.addWidget(self.input_time)
        row2.addWidget(self.combo_type)
        row2.addWidget(btn_add)
        add_layout.addLayout(row2)

        layout.addWidget(add_frame)

    def _load_data(self):
        """저장된 일정/TODO 불러와서 리스트 렌더링"""
        self.list_widget.clear()
        schedules = self.agent.schedules

        if not schedules:
            empty_item = QListWidgetItem("등록된 일정이나 할 일이 없어요. 아래에서 새로 추가해 보세요!")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            empty_item.setForeground(Qt.GlobalColor.gray)
            self.list_widget.addItem(empty_item)
            return

        # 날짜순 정렬
        sorted_schedules = sorted(schedules, key=lambda x: (x.get("date", ""), x.get("time", "")))

        for s in sorted_schedules:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(6, 4, 6, 4)

            # 유형 뱃지
            is_todo = s.get("type") == "todo"
            badge_text = "✅" if is_todo else "📌"
            badge_label = QLabel(badge_text)
            item_layout.addWidget(badge_label)

            # TODO인 경우 체크박스
            if is_todo:
                chk = QCheckBox()
                chk.setChecked(s.get("done", False))
                chk.stateChanged.connect(lambda state, sid=s["id"]: self._toggle_done(sid))
                item_layout.addWidget(chk)

            # 텍스트 내용
            time_str = s.get("time", "ALL_DAY")
            time_display = "종일" if time_str == "ALL_DAY" else time_str
            date_str = s.get("date", "")
            title_str = s.get("title", "")

            info_text = f"[{date_str} {time_display}] {title_str}"
            text_label = QLabel(info_text)
            if is_todo and s.get("done", False):
                text_label.setStyleSheet("color: #72767D; text-decoration: line-through;")
            else:
                text_label.setStyleSheet("color: #FFFFFF; font-weight: 500;")

            item_layout.addWidget(text_label, 1)

            # 삭제 버튼
            btn_del = QPushButton("🗑️")
            btn_del.setObjectName("btn_delete")
            btn_del.setToolTip("삭제")
            btn_del.clicked.connect(lambda _, sid=s["id"]: self._delete_item(sid))
            item_layout.addWidget(btn_del)

            # QListWidgetItem 생성 및 바인딩
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, item_widget)

    def _add_item(self):
        title = self.input_title.text().strip()
        if not title:
            QMessageBox.warning(self, "입력 오류", "일정 또는 할 일 내용을 입력해 주세요.")
            return

        date_str = self.input_date.text().strip()
        time_str = self.input_time.text().strip()
        item_type = "event" if self.combo_type.currentIndex() == 0 else "todo"

        self.agent.add_schedule(title, date_str, time_str, item_type)
        self.input_title.clear()
        self._load_data()
        self.schedule_updated.emit()

    def _toggle_done(self, sched_id: str):
        self.agent.toggle_done(sched_id)
        self._load_data()
        self.schedule_updated.emit()

    def _delete_item(self, sched_id: str):
        self.agent.delete_schedule(sched_id)
        self._load_data()
        self.schedule_updated.emit()
