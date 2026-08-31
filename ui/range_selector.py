import sys
import os
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QCursor
from PyQt6.QtWidgets import QWidget, QApplication, QPushButton, QHBoxLayout

class RangeSelector(QWidget):
    """마우스 드래그로 펫의 커스텀 직사각형 이동 범위를 지정하는 몽환 안개 셀렉터 윈도우"""

    range_selected = pyqtSignal(QRect)  # 선택된 직사각형 영역 (가상 스크린 global 좌표계)
    cancelled = pyqtSignal()

    _instance = None

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        v_geo = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(v_geo)

        self._start_pos = None
        self._current_pos = None
        self._is_selecting = False
        self._selected_rect = QRect()
        self._is_completed = False

        # 적용 / 취소용 버튼 컨테이너 생성
        self._init_buttons()

    def _init_buttons(self):
        self.btn_container = QWidget(self)
        self.btn_container.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 35, 45, 230);
                border: 1px solid rgba(100, 180, 255, 180);
                border-radius: 12px;
            }
            QPushButton {
                background-color: rgba(60, 130, 240, 200);
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 6px 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(80, 160, 255, 255);
            }
            QPushButton#btn_cancel {
                background-color: rgba(100, 100, 110, 180);
            }
            QPushButton#btn_cancel:hover {
                background-color: rgba(130, 130, 140, 220);
            }
        """)

        layout = QHBoxLayout(self.btn_container)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        self.btn_apply = QPushButton("✅ 이 영역으로 범위 설정 (Enter)", self.btn_container)
        self.btn_cancel = QPushButton("❌ 취소 (Esc)", self.btn_container)
        self.btn_cancel.setObjectName("btn_cancel")

        self.btn_apply.clicked.connect(self._accept_selection)
        self.btn_cancel.clicked.connect(self._cancel_selection)

        layout.addWidget(self.btn_apply)
        layout.addWidget(self.btn_cancel)

        self.btn_container.adjustSize()
        self.btn_container.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 버튼 컨테이너 내부 클릭 통과 보장
            if self.btn_container.isVisible() and self.btn_container.geometry().contains(event.pos()):
                super().mousePressEvent(event)
                return

            self._start_pos = event.pos()
            self._current_pos = event.pos()
            self._is_selecting = True
            self._is_completed = False
            self._selected_rect = QRect()
            self.btn_container.hide()
            self.update()

    def mouseMoveEvent(self, event):
        if self._is_selecting:
            self._current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._is_selecting = False
            self._current_pos = event.pos()

            rect = QRect(self._start_pos, self._current_pos).normalized()
            # 최소 유효 크기 확인 (30x30 이상)
            if rect.width() >= 30 and rect.height() >= 30:
                self._selected_rect = rect
                self._is_completed = True
                self._position_button_container()
            else:
                self._selected_rect = QRect()
                self._is_completed = False
                self.btn_container.hide()
            self.update()

    def _position_button_container(self):
        if self._selected_rect.isEmpty():
            return

        self.btn_container.adjustSize()
        btn_w = self.btn_container.width()
        btn_h = self.btn_container.height()

        # 선택 직사각형의 하단 중앙 위치 (화면 이탈 방지)
        bx = self._selected_rect.center().x() - (btn_w // 2)
        by = self._selected_rect.bottom() + 12

        v_geo = self.rect()
        if by + btn_h > v_geo.bottom() - 10:
            by = self._selected_rect.top() - btn_h - 12
        if bx < 10:
            bx = 10
        if bx + btn_w > v_geo.right() - 10:
            bx = v_geo.right() - btn_w - 10

        self.btn_container.move(bx, by)
        self.btn_container.show()
        self.btn_container.raise_()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._is_completed and not self._selected_rect.isEmpty():
                self._accept_selection()
        elif event.key() == Qt.Key.Key_Escape:
            self._cancel_selection()

    def _accept_selection(self):
        if not self._selected_rect.isEmpty():
            # global 좌표 변환
            global_rect = QRect(
                self.mapToGlobal(self._selected_rect.topLeft()),
                self._selected_rect.size()
            )
            self.range_selected.emit(global_rect)
        self.close()

    def _cancel_selection(self):
        self.cancelled.emit()
        self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. 전체 화면 어두운 안개 배경 (반투명 오버레이)
        painter.fillRect(self.rect(), QColor(15, 20, 30, 140))

        # 2. 상단 중앙 안내 바
        header_rect = QRect((self.width() - 580) // 2, 30, 580, 42)
        painter.setBrush(QBrush(QColor(25, 30, 42, 220)))
        painter.setPen(QPen(QColor(80, 160, 255, 200), 1.5))
        painter.drawRoundedRect(header_rect, 10, 10)

        painter.setPen(QColor(240, 245, 255))
        font = QFont("Malgun Gothic", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignCenter, "🖱️ 펫이 거닐 직사각형 안개 영역을 마우스로 드래그하세요!")

        # 3. 현재 드래그 중이거나 선택 완료된 영역 렌더링
        curr_rect = QRect()
        if self._is_selecting and self._start_pos and self._current_pos:
            curr_rect = QRect(self._start_pos, self._current_pos).normalized()
        elif self._is_completed:
            curr_rect = self._selected_rect

        if not curr_rect.isEmpty():
            # (1) 안개 솜사탕 강조 영역 구름 채우기 & 테두리
            cloud_bg = QColor(220, 235, 255, 90)
            painter.setBrush(QBrush(cloud_bg))

            border_color = QColor(70, 150, 255)
            painter.setPen(QPen(border_color, 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(curr_rect, 16, 16)

            # (2) 크기 안내 텍스트 (W x H)
            txt = f"{curr_rect.width()} px  ×  {curr_rect.height()} px"
            txt_w = 150
            txt_h = 26
            txt_bg = QRect(curr_rect.x() + 8, curr_rect.y() + 8, txt_w, txt_h)
            if txt_bg.right() > curr_rect.right():
                txt_bg.setLeft(curr_rect.right() - txt_w - 8)
                txt_bg.setRight(curr_rect.right() - 8)
            if txt_bg.bottom() > curr_rect.bottom():
                txt_bg.setTop(curr_rect.bottom() - txt_h - 8)
                txt_bg.setBottom(curr_rect.bottom() - 8)

            painter.setBrush(QBrush(QColor(20, 25, 35, 190)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(txt_bg, 6, 6)

            painter.setPen(QColor(255, 255, 255))
            font_sm = QFont("Malgun Gothic", 9, QFont.Weight.Bold)
            painter.setFont(font_sm)
            painter.drawText(txt_bg, Qt.AlignmentFlag.AlignCenter, txt)

    @classmethod
    def start_selection(cls, callback_on_selected=None, callback_on_cancelled=None):
        """드래그 선택창을 띄우고 결과를 콜백으로 전달"""
        inst = RangeSelector()
        cls._instance = inst

        if callback_on_selected:
            inst.range_selected.connect(callback_on_selected)
        if callback_on_cancelled:
            inst.cancelled.connect(callback_on_cancelled)

        inst.show()
        inst.raise_()
        inst.activateWindow()
        return inst
