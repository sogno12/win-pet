import os
import sys
import logging
from datetime import datetime

if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class PetLogger:
    """일별 로그 파일 생성 및 펫 대화/툴콜/에러 로깅 모듈"""
    
    _logger = None

    @classmethod
    def get_logger(cls):
        if cls._logger is not None:
            return cls._logger

        log_dir = os.path.join(_BASE_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)

        today_str = datetime.now().strftime("%Y-%m-%d")
        log_file_path = os.path.join(log_dir, f"{today_str}.log")

        logger = logging.getLogger("WinPetLogger")
        logger.setLevel(logging.INFO)

        # 기존 핸들러 제거
        if logger.hasHandlers():
            logger.handlers.clear()

        # 파일 핸들러 (utf-8 인코딩)
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 날짜 형식 yyyy/MM/dd HH:mm:ss 통일 (유저 규격)
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", datefmt="%Y/%m/%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        cls._logger = logger
        return cls._logger

    @classmethod
    def log_user(cls, user_query: str):
        logger = cls.get_logger()
        logger.info(f"[USER_QUERY] {user_query}")

    @classmethod
    def log_tool(cls, tool_name: str, args: dict, result: str):
        logger = cls.get_logger()
        logger.info(f"[TOOL_CALL] Executed '{tool_name}' with args={args} -> Result: {result}")

    @classmethod
    def log_pet(cls, pet_key: str, response: str):
        logger = cls.get_logger()
        logger.info(f"[PET_RESPONSE] ({pet_key}): {response}")

    @classmethod
    def log_api_usage(cls, prompt_tokens: int, candidate_tokens: int, total_tokens: int, model_name: str = ""):
        logger = cls.get_logger()
        logger.info(f"[API_USAGE] Model={model_name} | Prompt={prompt_tokens}, Candidate={candidate_tokens}, Total={total_tokens} tokens")

    @classmethod
    def log_error(cls, error_msg: str):
        logger = cls.get_logger()
        logger.error(f"[ERROR] {error_msg}")

    @classmethod
    def get_today_log_path(cls) -> str:
        log_dir = os.path.join(_BASE_DIR, "logs")
        today_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(log_dir, f"{today_str}.log")

    @classmethod
    def open_today_log(cls):
        """오늘자 로그 파일을 메모장(Notepad)이나 기본 연결 프로그램으로 즉시 엽니다."""
        log_path = cls.get_today_log_path()
        if not os.path.exists(log_path):
            cls.get_logger() # 생성
        try:
            os.startfile(log_path)
        except Exception as e:
            cls.log_error(f"로그 파일 열기 실패: {e}")

