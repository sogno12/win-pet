from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QSpinBox, QLineEdit, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from core.schedule_agent import ScheduleAgent

class DialogTimer(QDialog):
    """⏰ 펫 타이머 및 포모도로 반복 스케줄러 관리 UI"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏰ 펫 타이머 & 포모도로 스케줄러")
        self.setFixedSize(480, 520)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        self.agent = ScheduleAgent.get_instance()
        self.init_ui()
        
        # 1초마다 잔여 시간 실시간 UI 갱신
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(1000)
        self.refresh_timer.timeout.connect(self.update_status)
        self.refresh_timer.start()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 1. 🍅 포모도로(Pomodoro) 세션 컨트롤 그룹
        pomo_box = QGroupBox("🍅 포모도로(Pomodoro) 집중/휴식 사이클")
        pomo_layout = QVBoxLayout()
        
        self.pomo_status_label = QLabel("현재 진행 중인 포모도로가 없습니다.")
        self.pomo_status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        self.pomo_status_label.setWordWrap(True)
        pomo_layout.addWidget(self.pomo_status_label)
        
        pomo_btn_layout = QHBoxLayout()
        start_25_btn = QPushButton("🍅 25분 집중 / 5분 휴식")
        start_25_btn.setStyleSheet("padding: 6px; background-color: #FF6B6B; color: white; font-weight: bold; border-radius: 4px;")
        start_25_btn.clicked.connect(lambda: self.start_pomo(25, 5))
        
        start_50_btn = QPushButton("⚡ 50분 집중 / 10분 휴식")
        start_50_btn.setStyleSheet("padding: 6px; background-color: #4D96FF; color: white; font-weight: bold; border-radius: 4px;")
        start_50_btn.clicked.connect(lambda: self.start_pomo(50, 10))
        
        stop_pomo_btn = QPushButton("🛑 포모도로 중단")
        stop_pomo_btn.setStyleSheet("padding: 6px; background-color: #6c757d; color: white; border-radius: 4px;")
        stop_pomo_btn.clicked.connect(self.stop_pomo)
        
        pomo_btn_layout.addWidget(start_25_btn)
        pomo_btn_layout.addWidget(start_50_btn)
        pomo_btn_layout.addWidget(stop_pomo_btn)
        pomo_layout.addLayout(pomo_btn_layout)
        pomo_box.setLayout(pomo_layout)
        layout.addWidget(pomo_box)

        # 2. ⏰ 일반 1회성 타이머 목록 그룹
        timer_box = QGroupBox("⏰ 일반 1회성 타이머 / 알람 목록")
        timer_layout = QVBoxLayout()
        
        self.timer_list_widget = QListWidget()
        self.timer_list_widget.setStyleSheet("font-size: 13px; border: 1px solid #ddd; border-radius: 4px;")
        timer_layout.addWidget(self.timer_list_widget)
        
        # 타이머 수동 추가 라인
        add_layout = QHBoxLayout()
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(1, 300)
        self.minutes_spin.setValue(10)
        self.minutes_spin.setSuffix(" 분")
        
        self.memo_edit = QLineEdit()
        self.memo_edit.setPlaceholderText("메모 (예: 약 먹기, 찌개 끄기)")
        
        add_btn = QPushButton("➕ 타이머 추가")
        add_btn.setStyleSheet("padding: 6px; background-color: #2ECC71; color: white; font-weight: bold; border-radius: 4px;")
        add_btn.clicked.connect(self.add_custom_timer)
        
        cancel_btn = QPushButton("🗑️ 선택 타이머 취소")
        cancel_btn.setStyleSheet("padding: 6px; background-color: #E74C3C; color: white; border-radius: 4px;")
        cancel_btn.clicked.connect(self.cancel_selected_timer)

        add_layout.addWidget(QLabel("시간:"))
        add_layout.addWidget(self.minutes_spin)
        add_layout.addWidget(self.memo_edit)
        add_layout.addWidget(add_btn)
        timer_layout.addLayout(add_layout)
        timer_layout.addWidget(cancel_btn)
        
        timer_box.setLayout(timer_layout)
        layout.addWidget(timer_box)

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)
        self.update_status()

    def update_status(self):
        """1초마다 UI 카운트다운 갱신"""
        summary = self.agent.get_status_summary()
        pomo = summary["pomodoro"]
        
        # 1. 포모도로 갱신
        if pomo["is_active"]:
            phase_name = "🔥 [집중 시간]" if pomo["phase"] == "WORK" else "☕ [휴식 시간]"
            rem = pomo["remaining_seconds"]
            m, s = divmod(rem, 60)
            self.pomo_status_label.setText(
                f"🍅 제 {pomo['cycle_count']}세션 진행 중 - {phase_name}\n"
                f"⏱️ 남은 시간: {m:02d}분 {s:02d}초 (설정: 집중 {pomo['work_minutes']}분 / 휴식 {pomo['rest_minutes']}분)"
            )
        else:
            self.pomo_status_label.setText("현재 진행 중인 포모도로 사이클이 없습니다.")

        # 2. 1회성 타이머 목록 갱신
        self.timer_list_widget.clear()
        for t in summary["timers"]:
            rem = t["remaining_seconds"]
            m, s = divmod(rem, 60)
            item_text = f"⏰ [{t['memo']}] - 남은 시간: {m:02d}분 {s:02d}초"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, t["id"])
            self.timer_list_widget.addItem(item)

    def start_pomo(self, work_m, rest_m):
        msg = self.agent.start_pomodoro(work_m, rest_m)
        QMessageBox.information(self, "포모도로 시작", msg)
        self.update_status()

    def stop_pomo(self):
        msg = self.agent.stop_pomodoro()
        QMessageBox.information(self, "포모도로 중단", msg)
        self.update_status()

    def add_custom_timer(self):
        mins = self.minutes_spin.value()
        memo = self.memo_edit.text().strip() or "알림"
        msg = self.agent.add_timer(mins, memo)
        self.memo_edit.clear()
        self.update_status()

    def cancel_selected_timer(self):
        item = self.timer_list_widget.currentItem()
        if not item:
            return
        t_id = item.data(Qt.ItemDataRole.UserRole)
        if t_id:
            self.agent.cancel_timer(t_id)
            self.update_status()
