import os
import subprocess
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QApplication, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from core.vision_agent import VisionAgent
from core.logger import PetLogger


# ─── 공통 버튼 스타일 헬퍼 ───────────────────────────────────────────────────
def _btn_style(bg: str, hover: str, pressed: str, text_color: str = "white",
               border: str = "none") -> str:
    return f"""
        QPushButton {{
            padding: 8px 12px;
            background-color: {bg};
            color: {text_color};
            font-weight: bold;
            border-radius: 6px;
            border: {border};
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {pressed}; padding-top: 10px; }}
        QPushButton:disabled {{ background-color: #BDC3C7; }}
    """


# ─── 백그라운드 Vision 워커 ──────────────────────────────────────────────────
class VisionWorkerThread(QThread):
    """비동기 Vision AI / OCR 처리 스레드 (UI 프리징 방지)"""
    finished_signal = pyqtSignal(str)

    def __init__(self, mode: str, image_path: str, prompt: str = ""):
        super().__init__()
        self.mode = mode          # "ANALYZE" | "OCR"
        self.image_path = image_path
        self.prompt = prompt

    def run(self):
        if self.mode == "ANALYZE":
            res = VisionAgent.analyze_image(self.image_path, self.prompt)
        else:
            res = VisionAgent.extract_text_ocr(self.image_path)
        self.finished_signal.emit(res)


# ─── AI 분석 결과 전용 팝업 ─────────────────────────────────────────────────
class DialogAnalysisResult(QDialog):
    """🔍 AI 분석 결과 전용 팝업: 스크롤 텍스트 + 전체 복사 버튼"""

    def __init__(self, result_text: str, parent_pet=None):
        super().__init__(parent_pet)
        self.result_text = result_text
        self.parent_pet = parent_pet

        self.setWindowTitle("🔍 AI 이미지 분석 결과")
        self.setMinimumSize(500, 420)
        self.resize(560, 500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 헤더
        header = QLabel("🔍 AI 이미지 분석 결과")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # 결과 텍스트 영역 (스크롤 가능, 제한 없음)
        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)
        self.result_view.setPlainText(self.result_text)
        self.result_view.setFont(QFont("맑은 고딕", 10))
        self.result_view.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                padding: 10px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.result_view, stretch=1)

        # 버튼 행
        btn_layout = QHBoxLayout()

        copy_btn = QPushButton("📋 전체 복사")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet(_btn_style("#27AE60", "#2ECC71", "#1E8449"))
        copy_btn.clicked.connect(self._copy_all)

        close_btn = QPushButton("닫기")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(_btn_style("#ECF0F1", "#BDC3C7", "#95A5A6",
                                           text_color="#2C3E50",
                                           border="1px solid #BDC3C7"))
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(copy_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _copy_all(self):
        QApplication.clipboard().setText(self.result_text)
        # 버튼 텍스트를 일시적으로 바꿔 복사 완료 피드백
        btn = self.sender()
        if btn:
            btn.setText("✅ 복사 완료!")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: btn.setText("📋 전체 복사"))


# ─── 캡처 초기 팝업 (미리보기 + 분석/OCR 선택) ──────────────────────────────
class DialogCaptureResult(QDialog):
    """📸 캡처된 이미지 미리보기 & Vision AI 분석 / OCR 전용 팝업 GUI"""

    def __init__(self, image_path: str, parent_pet=None):
        super().__init__(parent_pet)
        self.image_path = image_path
        self.parent_pet = parent_pet
        self.worker = None

        self.setWindowTitle("📸 캡처 스마트 분석 & OCR")
        self.setFixedSize(480, 500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 1. 상단 안내
        info_label = QLabel("📸 이미지 저장 및 클립보드 복사 완료! (Ctrl+V 사용 가능)")
        info_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #2ECC71;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # 2. 이미지 썸네일 미리보기
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(450, 240)
        self.preview_label.setStyleSheet(
            "border: 1px solid #ddd; background-color: #222; border-radius: 6px;"
        )
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(self.image_path)
        if not pix.isNull():
            scaled = pix.scaled(440, 230,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(scaled)
        layout.addWidget(self.preview_label)

        # 3. 질문 입력창
        layout.addWidget(QLabel("💬 AI 질문 / 분석 요청:"))
        self.prompt_edit = QLineEdit()
        self.prompt_edit.setPlaceholderText("예: 이 에러 원인이 뭐야? / 이 그래프 요약해줘 (생략 가능)")
        self.prompt_edit.setClearButtonEnabled(True)
        self.prompt_edit.returnPressed.connect(self.run_analysis)
        layout.addWidget(self.prompt_edit)

        # 상태 라벨
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 12px; color: #E67E22; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # 4. 버튼
        btn_layout = QHBoxLayout()

        analyze_btn = QPushButton("🔍 AI 분석/질문")
        analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        analyze_btn.setStyleSheet(_btn_style("#3498DB", "#5DADE2", "#2874A6"))
        analyze_btn.clicked.connect(self.run_analysis)
        self._analyze_btn = analyze_btn

        ocr_btn = QPushButton("📝 텍스트 추출 (OCR)")
        ocr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ocr_btn.setStyleSheet(_btn_style("#9B59B6", "#AF7AC5", "#76448A"))
        ocr_btn.clicked.connect(self.run_ocr)
        self._ocr_btn = ocr_btn

        folder_btn = QPushButton("📂 폴더 열기")
        folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        folder_btn.setStyleSheet(_btn_style("#7F8C8D", "#95A5A6", "#616A6B"))
        folder_btn.clicked.connect(self.open_screenshot_folder)

        cancel_btn = QPushButton("닫기")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(_btn_style("#ECF0F1", "#BDC3C7", "#95A5A6",
                                            text_color="#2C3E50",
                                            border="1px solid #BDC3C7"))
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(analyze_btn)
        btn_layout.addWidget(ocr_btn)
        btn_layout.addWidget(folder_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # API 키 미설정 시 AI 기능 버튼 비활성화 + 안내
        from core.config_manager import ConfigManager
        if not ConfigManager.get_api_key():
            self._analyze_btn.setEnabled(False)
            self._ocr_btn.setEnabled(False)
            no_key_label = QLabel("⚠️ Gemini API 키 미설정 — AI 분석/OCR 기능을 사용하려면 [🔑 API 키 설정]에서 키를 등록하세요.")
            no_key_label.setStyleSheet("font-size: 11px; color: #E74C3C; font-weight: bold;")
            no_key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_key_label.setWordWrap(True)
            layout.addWidget(no_key_label)

    # ── 분석 ────────────────────────────────────────────────────────────────
    def run_analysis(self):
        prompt = self.prompt_edit.text().strip()
        self.status_label.setText("⏳ Gemini Vision AI가 이미지를 분석 중입니다...")
        self.setEnabled(False)

        self.worker = VisionWorkerThread("ANALYZE", self.image_path, prompt)
        self.worker.finished_signal.connect(self.on_analysis_finished)
        self.worker.start()

    def on_analysis_finished(self, result_text: str):
        self.setEnabled(True)
        self.status_label.setText("")

        # 기존 말풍선 대신 → 전용 결과 팝업 창으로 표시
        self.accept()   # 캡처 팝업 먼저 닫기
        result_dlg = DialogAnalysisResult(result_text, self.parent_pet)
        result_dlg.exec()

    # ── OCR ─────────────────────────────────────────────────────────────────
    def run_ocr(self):
        self.status_label.setText("⏳ 이미지 내부 텍스트(OCR)를 추출하는 중입니다...")
        self.setEnabled(False)

        self.worker = VisionWorkerThread("OCR", self.image_path)
        self.worker.finished_signal.connect(self.on_ocr_finished)
        self.worker.start()

    def on_ocr_finished(self, result_text: str):
        self.setEnabled(True)
        self.status_label.setText("")

        # OCR 결과 클립보드 자동 복사 + 결과 팝업 표시
        QApplication.clipboard().setText(result_text)
        self.accept()
        result_dlg = DialogAnalysisResult(
            f"[OCR 추출 텍스트 — 클립보드에 자동 복사됨]\n\n{result_text}",
            self.parent_pet
        )
        result_dlg.exec()

    # ── 폴더 열기 ────────────────────────────────────────────────────────────
    def open_screenshot_folder(self):
        folder = os.path.dirname(self.image_path)
        if os.path.exists(folder):
            subprocess.Popen(f'explorer "{folder}"')
