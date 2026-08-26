import os
import sys
import ctypes
import subprocess
import webbrowser
from urllib.parse import quote
from core.logger import PetLogger

import json

if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class PCAgent:
    """Windows PC 제어 및 자동화를 수행하는 클래스"""

    PC_TARGETS_PATH = os.path.join(_BASE_DIR, "pc_targets.json")

    # 기본 폴백 앱 매핑
    FALLBACK_APPS = {
        "notepad": {"name": "메모장", "exe": "notepad.exe", "aliases": ["메모장", "notepad"]},
        "calc": {"name": "계산기", "exe": "calc.exe", "aliases": ["계산기", "calc"]},
        "chrome": {"name": "크롬", "exe": "chrome.exe", "aliases": ["크롬", "chrome"]},
        "edge": {"name": "엣지", "exe": "msedge.exe", "aliases": ["엣지", "edge"]},
        "mspaint": {"name": "그림판", "exe": "mspaint.exe", "aliases": ["그림판", "paint"]},
        "kakaotalk": {"name": "카카오톡", "exe": "KakaoTalk.exe", "aliases": ["카카오톡", "카톡"]},
        "discord": {"name": "디스코드", "exe": "Discord.exe", "aliases": ["디스코드", "디코"]},
        "spotify": {"name": "스포티파이", "exe": "Spotify.exe", "aliases": ["스포티파이", "스포티"]},
        "explorer": {"name": "파일 탐색기", "exe": "explorer.exe", "aliases": ["탐색기", "파일탐색기"], "allow_close": False},
        "taskmgr": {"name": "작업 관리자", "exe": "taskmgr.exe", "aliases": ["작업관리자", "taskmgr"], "allow_close": True}
    }

    # VK 키 코드
    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF

    @classmethod
    def load_targets(cls) -> dict:
        """pc_targets.json 파일에서 프로그램 목록을 로드"""
        if os.path.exists(cls.PC_TARGETS_PATH):
            try:
                with open(cls.PC_TARGETS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("programs", cls.FALLBACK_APPS)
            except Exception as e:
                PetLogger.log_error(f"pc_targets.json 로드 실패: {e}")
        return cls.FALLBACK_APPS

    @classmethod
    def _find_target(cls, app_name: str):
        """앱 이름이나 별칭으로 설정 정보 검색"""
        clean_name = app_name.lower().strip().replace(" ", "").replace(".exe", "")
        programs = cls.load_targets()
        
        for key, info in programs.items():
            if clean_name == key.lower():
                return info
            if clean_name == info.get("name", "").lower().replace(" ", ""):
                return info
            for alias in info.get("aliases", []):
                if clean_name == alias.lower().replace(" ", "").replace(".exe", ""):
                    return info
        return None

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
        """지정한 애플리케이션을 안전하게 실행합니다."""
        info = cls._find_target(app_name)
        
        if not info:
            # 화이트리스트 외 임의 실행 차단 또는 윈도우 기본 런처 전달
            try:
                clean_name = app_name.strip()
                subprocess.Popen(clean_name, shell=True)
                msg = f"'{app_name}' 실행 명령을 전달했습니다."
                PetLogger.log_tool("launch_app", {"app_name": app_name}, msg)
                return msg
            except Exception as e:
                err_msg = f"'{app_name}' 실행 실패: {str(e)}"
                PetLogger.log_error(err_msg)
                return err_msg
        
        exe = info.get("exe")
        display_name = info.get("name", app_name)
        try:
            if hasattr(os, "startfile"):
                os.startfile(exe)
            else:
                subprocess.Popen(exe, shell=True)
            msg = f"'{display_name}' 프로그램을 실행했습니다."
            PetLogger.log_tool("launch_app", {"app_name": app_name, "exe": exe}, msg)
            return msg
        except Exception as e:
            # os.startfile 실패 시 subprocess.Popen(exe, shell=True)로 2차 시도
            try:
                subprocess.Popen(exe, shell=True)
                msg = f"'{display_name}' 프로그램을 실행했습니다."
                PetLogger.log_tool("launch_app", {"app_name": app_name, "exe": exe}, msg)
                return msg
            except Exception as e2:
                err_msg = f"'{display_name}' 실행 실패: {str(e2)}"
                PetLogger.log_error(err_msg)
                return err_msg

    @classmethod
    def close_app(cls, app_name: str) -> str:
        """화이트리스트에 등록된 애플리케이션을 안전하게(Graceful close) 종료합니다."""
        info = cls._find_target(app_name)
        
        if not info:
            msg = f"안전을 위해 pc_targets.json에 등록된 프로그램만 종료할 수 있어요. ('{app_name}'은(는) 목록에 없습니다.)"
            PetLogger.log_tool("close_app", {"app_name": app_name}, msg)
            return msg
        
        if info.get("allow_close") is False:
            msg = f"'{info.get('name', app_name)}'은(는) 시스템 안정성을 위해 종료가 제한된 프로그램이에요."
            PetLogger.log_tool("close_app", {"app_name": app_name}, msg)
            return msg

        exe = info.get("exe")
        display_name = info.get("name", app_name)

        try:
            # 1. Graceful 종료 시도 (강제 /F 없이 창 닫기 신호 전송)
            cmd = f'taskkill /IM "{exe}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                msg = f"'{display_name}' 프로그램을 안전하게 종료했습니다."
            elif "찾을 수 없습니다" in result.stderr or "not found" in result.stderr.lower() or "128" in str(result.returncode):
                msg = f"'{display_name}' 프로그램이 현재 실행 중이지 않아요."
            else:
                msg = f"'{display_name}' 종료 신호를 보냈습니다."
            
            PetLogger.log_tool("close_app", {"app_name": app_name, "exe": exe}, msg)
            return msg
        except Exception as e:
            err_msg = f"'{display_name}' 종료 처리 중 오류 발생: {str(e)}"
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
        elif tool_name == "close_app":
            return cls.close_app(args.get("app_name", ""))
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

