import os
import sys
import datetime
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor, QPen, QGuiApplication, QPixmap, QImage, QScreen
from PyQt6.QtWidgets import QWidget, QApplication
from core.logger import PetLogger

try:
    from PIL import ImageGrab
    HAS_PIL_GRAB = True
except ImportError:
    HAS_PIL_GRAB = False


def _get_base_dir() -> str:
    """PyInstaller 빌드/개발 환경 모두에서 프로젝트 루트(exe 또는 main.py 위치)를 반환"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)   # dist/win_pet/
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 개발: 프로젝트 루트


class MonitorOverlay(QWidget):
    """단일 모니터에 1:1로 붙는 캡처 오버레이 윈도우"""
    region_selected = pyqtSignal(QPixmap, str)  # (크롭된 픽스맵, 모니터 이름)
    cancelled = pyqtSignal()

    def __init__(self, screen: QScreen, full_pixmap: QPixmap):
        super().__init__()
        self._screen = screen
        self._full_pixmap = full_pixmap  # 이 모니터의 1:1 스냅샷 (DPR=1.0)
        self._geo = screen.geometry()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setGeometry(self._geo)

        self._start = QPoint()
        self._end = QPoint()
        self._selecting = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.pos()
            self._end = event.pos()
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._selecting = False
            self._end = event.pos()
            self._do_crop()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()

    def paintEvent(self, event):
        painter = QPainter(self)

        # 1. 이 모니터 스냅샷을 오버레이 창에 1:1 채워 그리기
        painter.drawPixmap(self.rect(), self._full_pixmap)

        # 2. 반투명 어두운 마스크
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        # 3. 드래그 선택 영역 원본 복원 + 가이드선
        if self._selecting:
            rect = QRect(self._start, self._end).normalized()
            if rect.width() > 0 and rect.height() > 0:
                sx = self._full_pixmap.width() / self.width() if self.width() > 0 else 1.0
                sy = self._full_pixmap.height() / self.height() if self.height() > 0 else 1.0
                src = QRect(
                    int(rect.x() * sx), int(rect.y() * sy),
                    int(rect.width() * sx), int(rect.height() * sy)
                )
                painter.drawPixmap(rect, self._full_pixmap, src)

                pen = QPen(QColor(255, 80, 80), 2, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawRect(rect)

                txt = f"{rect.width()} x {rect.height()}"
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(
                    rect.x() + 5,
                    rect.y() - 5 if rect.y() > 20 else rect.y() + 15,
                    txt
                )

    def _do_crop(self):
        rect = QRect(self._start, self._end).normalized()
        if rect.width() < 5 or rect.height() < 5:
            self.cancelled.emit()
            return

        sx = self._full_pixmap.width() / self.width() if self.width() > 0 else 1.0
        sy = self._full_pixmap.height() / self.height() if self.height() > 0 else 1.0

        cx = max(0, int(rect.x() * sx))
        cy = max(0, int(rect.y() * sy))
        cw = min(int(rect.width() * sx), self._full_pixmap.width() - cx)
        ch = min(int(rect.height() * sy), self._full_pixmap.height() - cy)

        cropped = self._full_pixmap.copy(cx, cy, cw, ch)
        self.region_selected.emit(cropped, self._screen.name())


class ScreenCapturer(QObject):
    """
    Windows 캡처 도구 방식: 모니터마다 독립 오버레이를 띄우고
    드래그한 모니터 영역만 캡처 (모니터 경계 넘기 불가).
    """
    captured_signal = pyqtSignal(str)  # (저장된 파일 경로)

    _instance = None

    @classmethod
    def start_capture(cls, parent=None):
        if cls._instance is None:
            cls._instance = ScreenCapturer()
        cls._instance._open_overlays()

    def __init__(self):
        super().__init__()
        self._overlays: list[MonitorOverlay] = []

    def _grab_screen(self, screen: QScreen) -> QPixmap:
        """단일 모니터의 스냅샷을 논리 크기와 1:1 맞는 픽스맵으로 반환"""
        pix = None
        geo = screen.geometry()
        dpr = screen.devicePixelRatio()

        if HAS_PIL_GRAB:
            try:
                # ImageGrab은 물리 픽셀 좌표 기준 → 논리좌표 × DPR 변환 필수
                phys_x = int(geo.x() * dpr)
                phys_y = int(geo.y() * dpr)
                phys_w = int(geo.width() * dpr)
                phys_h = int(geo.height() * dpr)
                bbox = (phys_x, phys_y, phys_x + phys_w, phys_y + phys_h)

                pil_img = ImageGrab.grab(bbox=bbox, all_screens=True)
                pil_img = pil_img.convert("RGBA")
                data = pil_img.tobytes("raw", "RGBA")
                qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
                pix = QPixmap.fromImage(qimg)
                PetLogger.log_tool("screen_capture", {"screen": screen.name(), "dpr": dpr, "bbox": str(bbox)}, "모니터 캡처 성공")
            except Exception as e:
                PetLogger.log_error(f"ImageGrab 실패 ({screen.name()}): {e}")
                pix = None

        if pix is None or pix.isNull():
            pix = screen.grabWindow(0)

        # DPR 이중 스케일링 방지: 1.0으로 고정
        pix.setDevicePixelRatio(1.0)
        return pix

    def _open_overlays(self):
        """모든 모니터에 각각 독립 오버레이 창 생성"""
        self._close_all()
        QApplication.processEvents()

        screens = QGuiApplication.screens()
        if not screens:
            return

        for screen in screens:
            pixmap = self._grab_screen(screen)
            overlay = MonitorOverlay(screen, pixmap)
            overlay.region_selected.connect(self._on_region_selected)
            overlay.cancelled.connect(self._close_all)
            self._overlays.append(overlay)

        for ov in self._overlays:
            ov.show()
            ov.raise_()

        if self._overlays:
            self._overlays[0].activateWindow()

    def _close_all(self):
        for ov in self._overlays:
            ov.hide()
            ov.close()
        self._overlays.clear()

    def _on_region_selected(self, cropped: QPixmap, screen_name: str):
        """한 모니터에서 캡처 완료 → 나머지 오버레이 즉시 닫기 & 저장"""
        self._close_all()

        # 1. screenshots/ 폴더에 저장 (빌드/개발 환경 모두 exe/main.py 옆에 생성)
        save_dir = os.path.join(_get_base_dir(), "screenshots")
        os.makedirs(save_dir, exist_ok=True)

        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(save_dir, f"screenshot_{now_str}.png")
        cropped.save(file_path, "PNG")

        # 클립보드 복사
        QApplication.clipboard().setPixmap(cropped)

        PetLogger.log_tool(
            "screen_capture",
            {"screen": screen_name, "file": file_path},
            f"캡처 완료 [{screen_name}]: {file_path}"
        )

        self.captured_signal.emit(file_path)
