from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from core.config_manager import ConfigManager
from core.logger import PetLogger

class RangeOverlay(QWidget):
    """이동 범위 표시용 커스텀 안개/구름 반투명 오버레이 위젯 (외곽선 유무, 색상, 투명도 config 지원)"""

    _instance = None

    def __init__(self):
        super().__init__()
        # 클릭을 통과시키며 최상단에 표시되는 무테두리 도구 창
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        self.opacity = 1.0
        self.is_always_on = False
        
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self._fade_out_step)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # config.json에서 외곽선 유무, 안개 색상, 투명도 설정 로드
        config = ConfigManager.load_config()
        show_border = config.get("range_overlay_show_border", True)
        color_hex = config.get("range_overlay_color", "#E6F0FF")
        base_opacity = config.get("range_overlay_opacity", 0.25)

        # 페이드아웃 상태와 연동된 최종 알파/투명도 계산
        final_alpha_f = min(1.0, max(0.0, base_opacity * self.opacity))

        # 안개 배경색
        bg_color = QColor(color_hex)
        bg_color.setAlphaF(final_alpha_f)
        painter.setBrush(QBrush(bg_color))

        # 외곽선 설정 여부에 따른 렌더링
        if show_border:
            border_color = QColor(color_hex).darker(140)
            border_color.setAlphaF(min(1.0, max(0.0, (base_opacity * 2.2) * self.opacity)))
            painter.setPen(QPen(border_color, 2, Qt.PenStyle.DashLine))
        else:
            painter.setPen(Qt.PenStyle.NoPen)

        # 둥근 솜사탕 구름 느낌의 렌더링
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 20, 20)

    def _fade_out_step(self):
        if self.is_always_on:
            self.fade_timer.stop()
            return

        self.opacity -= 0.05
        if self.opacity <= 0:
            self.opacity = 0
            self.fade_timer.stop()
            self.hide()
        else:
            self.update()

    @classmethod
    def show_preview(cls, rect: QRect, always_on: bool = False):
        """지정된 QRect 영역에 커스텀 안개 오버레이 표시"""
        if cls._instance is None:
            cls._instance = RangeOverlay()

        inst = cls._instance
        inst.fade_timer.stop()
        inst.is_always_on = always_on
        
        config = ConfigManager.load_config()
        duration_ms = config.get("range_preview_duration_ms", 1500)

        inst.setGeometry(rect)
        inst.opacity = 1.0
        inst.show()
        inst.update()

        # 항상 켜기 모드가 아닐 때만 1.5초 후 스르륵 페이드아웃
        if not always_on:
            start_fade_delay = max(200, duration_ms - 500)
            QTimer.singleShot(start_fade_delay, lambda: inst.fade_timer.start(35))
        
        PetLogger.log_tool("RangeOverlay", {"always_on": always_on, "rect": f"{rect.width()}x{rect.height()}"}, f"커스텀 안개 오버레이 표시 (항상켜기={always_on})")

    @classmethod
    def hide_overlay(cls):
        if cls._instance:
            cls._instance.is_always_on = False
            cls._instance.fade_timer.stop()
            cls._instance.hide()
