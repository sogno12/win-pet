import os
import json
import socket
import subprocess
import webbrowser
import time
from core.config_manager import BASE_DIR
from core.logger import PetLogger

class AssetAgent:
    """All-in-Win 자산관리 대시보드 및 포트폴리오 데이터 연동 에이전트"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def get_allinwin_dir():
        """all-in-win 프로젝트 디렉토리 경로 탐색"""
        # 1. 상위 폴더 기준 상대 경로
        candidate1 = os.path.abspath(os.path.join(BASE_DIR, "..", "all-in-win"))
        if os.path.exists(candidate1):
            return candidate1
        
        # 2. 동일 작업영역 절대 경로
        candidate2 = r"C:\Users\nivis\Desktop\sogno-skill-up\all-in-win"
        if os.path.exists(candidate2):
            return candidate2
            
        return candidate1

    @staticmethod
    def get_python_exe():
        """allinwin 전용 Conda 환경 또는 시스템 python 실행 경로 탐색"""
        candidates = [
            r"C:\Users\nivis\miniconda3\envs\allinwin\python.exe",
            r"C:\Users\nivis\anaconda3\envs\allinwin\python.exe",
            r"C:\ProgramData\miniconda3\envs\allinwin\python.exe"
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        import sys
        return sys.executable

    @staticmethod
    def get_summary_file_path():
        """summary.json 파일 경로"""
        allinwin_dir = AssetAgent.get_allinwin_dir()
        return os.path.join(allinwin_dir, "data", "summary.json")

    @classmethod
    def get_asset_summary(cls):
        """all-in-win 요약 데이터(summary.json)를 읽어 정돈된 문자열 반환"""
        path = cls.get_summary_file_path()
        if not os.path.exists(path):
            return "아직 All-in-Win 자산관리 데이터가 기록되지 않았거나 summary.json 파일을 찾을 수 없어요. 대시보드에서 스냅샷을 먼저 저장해 주세요!"
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            last_updated = data.get("last_updated", "날짜 미상")
            total_invested = data.get("total_invested", 0)
            total_evaluated = data.get("total_evaluated", 0)
            total_profit = data.get("total_profit", 0)
            return_rate = data.get("return_rate", 0.0)
            
            sign = "+" if total_profit > 0 else ("-" if total_profit < 0 else "")
            profit_str = f"{sign}{abs(total_profit):,}원"
            
            top_assets = data.get("top_assets", [])
            top_str_list = []
            for item in top_assets[:3]:
                name = item.get("name", "")
                ratio = item.get("ratio", 0.0)
                top_str_list.append(f"{name}({ratio}%)")
            top_desc = ", ".join(top_str_list) if top_str_list else "내역 없음"
            
            alloc = data.get("asset_allocation", {})
            alloc_list = [f"{k} {v}%" for k, v in alloc.items() if v > 0]
            alloc_desc = ", ".join(alloc_list) if alloc_list else "내역 없음"
            
            summary_msg = (
                f"[All-in-Win 자산 현황 요약]\n"
                f"- 기준일자: {last_updated}\n"
                f"- 총 평가자산: {total_evaluated:,}원\n"
                f"- 총 투자원금: {total_invested:,}원\n"
                f"- 누적 손익: {profit_str} (수익률 {return_rate:+.2f}%)\n"
                f"- 주요 보유자산: {top_desc}\n"
                f"- 자산군 비중: {alloc_desc}"
            )
            return summary_msg
        except Exception as e:
            PetLogger.log_error(f"AssetAgent.get_asset_summary error: {e}")
            return f"자산 요약 데이터를 읽는 중 오류가 발생했어요: {str(e)}"

    @classmethod
    def is_server_running(cls, host="127.0.0.1", port=8000):
        """포트 8000이 열려있는지(FastAPI 서버 가동 중인지) 확인"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0

    @classmethod
    def open_dashboard(cls):
        """All-in-Win 웹 대시보드 서버 확인 및 브라우저 오픈"""
        url = "http://127.0.0.1:8000"
        allinwin_dir = cls.get_allinwin_dir()
        
        if not os.path.exists(allinwin_dir):
            return f"All-in-Win 프로젝트 폴더를 찾을 수 없어요: {allinwin_dir}"

        # 1. 서버가 아직 안 켜져 있다면 백그라운드로 실행
        if not cls.is_server_running():
            py_exe = cls.get_python_exe()
            app_script = os.path.join(allinwin_dir, "app.py")
            
            try:
                # Windows 백그라운드 프로세스 (창 숨김)
                creation_flags = 0
                if os.name == "nt":
                    creation_flags = subprocess.CREATE_NO_WINDOW
                
                subprocess.Popen(
                    [py_exe, app_script],
                    cwd=allinwin_dir,
                    creationflags=creation_flags
                )
                time.sleep(1.2)  # 서버 구동 대기
            except Exception as e:
                PetLogger.log_error(f"Failed to launch All-in-Win server: {e}")
                return f"All-in-Win 서버 실행 중 오류가 발생했습니다: {str(e)}"
        
        # 2. 웹 브라우저 열기
        try:
            webbrowser.open(url)
            return "All-in-Win 자산관리 대시보드(http://127.0.0.1:8000)를 브라우저로 열었어요!"
        except Exception as e:
            PetLogger.log_error(f"Failed to open browser: {e}")
            return f"대시보드 브라우저를 여는 중 오류가 발생했습니다: {str(e)}"

    @classmethod
    def execute_tool(cls, fn_name, fn_args):
        """LLM Function Calling 라우터"""
        if fn_name == "get_asset_summary":
            return cls.get_asset_summary()
        elif fn_name == "open_asset_dashboard":
            return cls.open_dashboard()
        return f"알 수 없는 자산관리 도구 호출: {fn_name}"
