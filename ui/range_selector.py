import sys
import os
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QCursor, QScreen, QGuiApplication
from PyQt6.QtWidgets import QWidget, QApplication, QPushButton, QHBoxLayout

class MonitorRangeOverlay(QWidget):
    """단일 모니터에 1:1로 밀착되는 커스텀 범위 드래그 선택 오버레이 윈도우 (듀얼/멀티모니터 무결점 지원)"""

    def __init__(self, screen: QScreen, manager: 'RangeSelector'):
        super().__init__()
        self.screen = screen
        self.manager = manager
        self.geo = screen.geometry()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setGeometry(self.geo)

        self._start_pos = None
        self._current_pos = None
        self._is_selecting = False
        self._selected_rect = QRect()
        self._is_completed = False

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
        self.btn_cancel.clicked.connect(self.manager.cancel_selection)

        layout.addWidget(self.btn_apply)
        layout.addWidget(self.btn_cancel)

        self.btn_container.adjustSize()
        self.btn_container.hide()

    def clear_selection(self):
        self._start_pos = None
        self._current_pos = None
        self._is_selecting = False
        self._selected_rect = QRect()
        self._is_completed = False
        if hasattr(self, 'btn_container'):
            self.btn_container.hide()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.btn_container.isVisible() and self.btn_container.geometry().contains(event.pos()):
                super().mousePressEvent(event)
                return

            self.manager.on_overlay_start_selecting(self)
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

        bx = self._selected_rect.center().x() - (btn_w // 2)
        by = self._selected_rect.bottom() + 12

        # 모니터 화면 경계 벗어나지 않게 안전 조정
        if by + btn_h > self.height() - 10:
            by = self._selected_rect.top() - btn_h - 12
        if bx < 10:
            bx = 10
        if bx + btn_w > self.width() - 10:
            bx = self.width() - btn_w - 10

        self.btn_container.move(bx, by)
        self.btn_container.show()
        self.btn_container.raise_()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._is_completed and not self._selected_rect.isEmpty():
                self._accept_selection()
        elif event.key() == Qt.Key.Key_Escape:
            self.manager.cancel_selection()

    def _accept_selection(self):
        if not self._selected_rect.isEmpty():
            # 모니터 로컬 좌표 -> 글로벌 화면 절대 좌표로 변환
            global_top_left = self.mapToGlobal(self._selected_rect.topLeft())
            global_rect = QRect(global_top_left, self._selected_rect.size())
            self.manager.complete_selection(global_rect)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. 전체 모니터 반투명 어두운 오버레이
        painter.fillRect(self.rect(), QColor(15, 20, 30, 140))

        # 2. 각 모니터 상단 중앙 가이드 바
        header_w = min(580, self.width() - 40)
        header_rect = QRect((self.width() - header_w) // 2, 30, header_w, 42)
        painter.setBrush(QBrush(QColor(25, 30, 42, 220)))
        painter.setPen(QPen(QColor(80, 160, 255, 200), 1.5))
        painter.drawRoundedRect(header_rect, 10, 10)

        painter.setPen(QColor(240, 245, 255))
        font = QFont("Malgun Gothic", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignCenter, "🖱️ 펫이 거닐 직사각형 안개 영역을 마우스로 드래그하세요! (Esc: 취소)")

        # 3. 드래그 중이거나 선택된 영역 렌더링
        curr_rect = QRect()
        if self._is_selecting and self._start_pos and self._current_pos:
            curr_rect = QRect(self._start_pos, self._current_pos).normalized()
        elif self._is_completed:
            curr_rect = self._selected_rect

        if not curr_rect.isEmpty():
            cloud_bg = QColor(220, 235, 255, 90)
            painter.setBrush(QBrush(cloud_bg))

            border_color = QColor(70, 150, 255)
            painter.setPen(QPen(border_color, 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(curr_rect, 16, 16)

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


class RangeSelector(QObject):
    """모든 연결된 모니터에 독립 오버레이를 띄워 듀얼/멀티 모니터에서도 완벽하게 범위를 지정하는 관리자"""

    range_selected = pyqtSignal(QRect)
    cancelled = pyqtSignal()

    _instance = None

    def __init__(self):
        super().__init__()
        self._overlays: list[MonitorRangeOverlay] = []

    def _open_overlays(self):
        self._close_all()
        screens = QGuiApplication.screens()
        if not screens:
            screens = [QApplication.primaryScreen()]

        for screen in screens:
            ov = MonitorRangeOverlay(screen, self)
            self._overlays.append(ov)
            ov.show()
            ov.raise_()

        if self._overlays:
            self._overlays[0].activateWindow()

    def on_overlay_start_selecting(self, active_overlay: MonitorRangeOverlay):
        for ov in self._overlays:
            if ov is not active_overlay:
                ov.clear_selection()

    def complete_selection(self, global_rect: QRect):
        self._close_all()
        self.range_selected.emit(global_rect)

    def cancel_selection(self):
        self._close_all()
        self.cancelled.emit()

    def _close_all(self):
        for ov in self._overlays:
            ov.hide()
            ov.close()
        self._overlays.clear()

    @classmethod
    def start_selection(cls, callback_on_selected=None, callback_on_cancelled=None):
        inst = RangeSelector()
        cls._instance = inst

        if callback_on_selected:
            inst.range_selected.connect(callback_on_selected)
        if callback_on_cancelled:
            inst.cancelled.connect(callback_on_cancelled)

        inst._open_overlays()
        return inst
