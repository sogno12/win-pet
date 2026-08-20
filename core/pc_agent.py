import os
import ctypes
import subprocess
import webbrowser
from urllib.parse import quote
from core.logger import PetLogger

class PCAgent:
    """Windows PC 제어 및 자동화를 수행하는 클래스"""

    ALLOWED_APPS = {
        "notepad": "notepad.exe",
        "메모장": "notepad.exe",
        "calc": "calc.exe",
        "계산기": "calc.exe",
        "mspaint": "mspaint.exe",
        "그림판": "mspaint.exe",
        "explorer": "explorer.exe",
        "탐색기": "explorer.exe",
        "파일탐색기": "explorer.exe",
        "taskmgr": "taskmgr.exe",
        "작업관리자": "taskmgr.exe",
        "chrome": "chrome.exe",
        "크롬": "chrome.exe",
        "edge": "msedge.exe",
        "엣지": "msedge.exe"
    }

    # VK 키 코드
    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF

    @classmethod
    def lock_pc(cls) -> str:
        """Windows PC를 잠금 상태로 전환합니다."""
        try:
            res = ctypes.windll.user32.LockWorkStation()
            msg = "PC 화면을 성공적으로 잠갔습니다."
            PetLogger.log_tool("lock_pc", {}, msg)
            return msg
        except Exception as e:
            err_msg = f"PC 화면 잠금 중 오류 발생: {str(e)}"
            PetLogger.log_error(err_msg)
            return err_msg

    @classmethod
    def launch_app(cls, app_name: str) -> str:
        """지정한 애플리케이션을 실행합니다."""
        clean_name = app_name.lower().strip()
        exe = cls.ALLOWED_APPS.get(clean_name)
        
        if not exe:
            try:
                subprocess.Popen(clean_name, shell=True)
                msg = f"'{app_name}' 앱 실행 명령을 전달했습니다."
                PetLogger.log_tool("launch_app", {"app_name": app_name}, msg)
                return msg
            except Exception as e:
                err_msg = f"'{app_name}' 실행 실패: {str(e)}"
                PetLogger.log_error(err_msg)
                return err_msg
        
        try:
            subprocess.Popen(exe)
            msg = f"'{app_name}' 프로그램이 실행되었습니다."
            PetLogger.log_tool("launch_app", {"app_name": app_name}, msg)
            return msg
        except Exception as e:
            err_msg = f"'{app_name}' 실행 실패: {str(e)}"
            PetLogger.log_error(err_msg)
            return err_msg

    @classmethod
    def search_youtube(cls, query: str) -> str:
        """유튜브에서 키워드로 검색하여 웹 브라우저로 엽니다."""
        encoded = quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        webbrowser.open(url)
        msg = f"유튜브에서 '{query}' 검색 결과를 웹 브라우저로 열었습니다."
        PetLogger.log_tool("search_youtube", {"query": query}, msg)
        return msg

    @classmethod
    def search_google(cls, query: str) -> str:
        """구글에서 키워드로 검색하여 웹 브라우저로 엽니다."""
        encoded = quote(query.strip())
        url = f"https://www.google.com/search?q={encoded}"
        webbrowser.open(url)
        msg = f"구글에서 '{query}' 검색 결과를 웹 브라우저로 열었습니다."
        PetLogger.log_tool("search_google", {"query": query}, msg)
        return msg

    @classmethod
    def open_website(cls, url_or_query: str) -> str:
        """웹사이트 URL을 열거나 구글 검색을 수행합니다."""
        target = url_or_query.strip()
        if target.startswith("http://") or target.startswith("https://"):
            webbrowser.open(target)
            msg = f"웹사이트 '{target}'(으)로 이동했습니다."
        elif "." in target and " " not in target:
            webbrowser.open(f"https://{target}")
            msg = f"웹사이트 'https://{target}'(으)로 이동했습니다."
        else:
            return cls.search_google(target)
        PetLogger.log_tool("open_website", {"url_or_query": url_or_query}, msg)
        return msg

    @classmethod
    def adjust_volume(cls, action: str) -> str:
        """시스템 볼륨을 조절합니다 (mute, unmute, up, down)."""
        action = action.lower().strip()
        try:
            if action in ["mute", "unmute", "toggle_mute", "음소거"]:
                ctypes.windll.user32.keybd_event(cls.VK_VOLUME_MUTE, 0, 0, 0)
                ctypes.windll.user32.keybd_event(cls.VK_VOLUME_MUTE, 0, 2, 0)
                msg = "볼륨 음소거 상태를 전환했습니다."
            elif action in ["up", "키워", "올려"]:
                for _ in range(5):
                    ctypes.windll.user32.keybd_event(cls.VK_VOLUME_UP, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(cls.VK_VOLUME_UP, 0, 2, 0)
                msg = "볼륨을 올렸습니다."
            elif action in ["down", "줄여", "내려"]:
                for _ in range(5):
                    ctypes.windll.user32.keybd_event(cls.VK_VOLUME_DOWN, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(cls.VK_VOLUME_DOWN, 0, 2, 0)
                msg = "볼륨을 줄였습니다."
            else:
                msg = f"알 수 없는 볼륨 동작입니다: {action}"
            PetLogger.log_tool("adjust_volume", {"action": action}, msg)
            return msg
        except Exception as e:
            err_msg = f"볼륨 조절 오류: {str(e)}"
            PetLogger.log_error(err_msg)
            return err_msg

    @classmethod
    def execute_tool(cls, tool_name: str, args: dict) -> str:
        """도구 이름과 인자를 받아 적절한 제어 기능을 실행합니다."""
        if tool_name == "lock_pc":
            return cls.lock_pc()
        elif tool_name == "launch_app":
            return cls.launch_app(args.get("app_name", ""))
        elif tool_name == "search_youtube":
            return cls.search_youtube(args.get("query", ""))
        elif tool_name == "search_google":
            return cls.search_google(args.get("query", args.get("url_or_query", "")))
        elif tool_name == "open_website":
            return cls.open_website(args.get("url_or_query", ""))
        elif tool_name == "adjust_volume":
            return cls.adjust_volume(args.get("action", ""))
        else:
            msg = f"지원하지 않는 제어 명령입니다: {tool_name}"
            PetLogger.log_error(msg)
            return msg

