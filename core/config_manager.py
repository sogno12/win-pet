import sys
import os
import json
import base64

if getattr(sys, 'frozen', False):
    # PyInstaller 포터블 바이너리로 실행 중일 때 (.exe 위치)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 파이썬 소스 스크립트로 실행 중일 때
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
PETS_REGISTRY_PATH = os.path.join(BASE_DIR, "pets.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

DEFAULT_MENU_LAYOUT = [
    {"id": "hide_pet", "enabled": True, "title": "🙈 펫 잠시 숨기기 (트레이 보관)"},
    {"type": "separator"},
    {"id": "screen_capture", "enabled": True, "title": "📸 스마트 화면 캡처 (AI 분석 / OCR)"},
    {"id": "calendar", "enabled": True, "title": "📅 일정 / 할 일(TODO) 관리..."},
    {"id": "timer", "enabled": True, "title": "⏰ 펫 타이머 / 포모도로..."},
    {"id": "asset_management", "enabled": True, "title": "💼 올인윈(All-in-Win) 자산관리"},
    {"type": "separator"},
    {"id": "always_on_top", "enabled": True, "title": "📌 항상 위에 표시"},
    {"id": "autostart", "enabled": True, "title": "🚀 윈도우 시작 시 자동 실행"},
    {"id": "skin_change", "enabled": True, "title": "🐾 펫 스킨 변경"},
    {"id": "pet_size", "enabled": True, "title": "📏 펫 크기"},
    {"id": "move_speed", "enabled": True, "title": "🐢 펫 이동 속도"},
    {"id": "move_range", "enabled": True, "title": "📍 펫 이동 범위"},
    {"type": "separator"},
    {"id": "status_window", "enabled": True, "title": "📊 펫 상태창..."},
    {"id": "api_key", "enabled": True, "title": "🔑 API 키 설정..."},
    {"id": "log_view", "enabled": True, "title": "📋 실행 및 API 이력 로그 보기..."},
    {"type": "separator"},
    {"id": "quit", "enabled": True, "title": "❌ 종료"}
]

DEFAULT_CONFIG = {
    "current_pet": "owl_white",
    "llm_model": "gemini-3.1-flash-lite",
    "pet_width": 48,
    "pet_height": 48,
    "is_always_on_top": True,
    "move_speed": 1,
    "move_timer_ms": 70,
    "move_boundary_mode": "MEDIUM",
    "anim_interval_ms": 140,
    "menu_layout": DEFAULT_MENU_LAYOUT
}

DEFAULT_PETS = {
    "owl_white": {"name": "🦉 하얀 부엉이", "enabled": True}
}

class ConfigManager:
    """설정 데이터 및 펫 레지스트리 관리 클래스 (임시 분할 코드 전면 제거 완료)"""
    
    @staticmethod
    def load_config():
        config = DEFAULT_CONFIG.copy()
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    config.update(loaded)
            except Exception as e:
                print(f"⚠️ 설정 로드 실패, 기본값 사용: {e}")

        if "menu_layout" not in config or not config["menu_layout"]:
            config["menu_layout"] = DEFAULT_MENU_LAYOUT
            ConfigManager.save_config(config)

        deprecated_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash"]
        if config.get("llm_model") in deprecated_models:
            config["llm_model"] = "gemini-3.1-flash-lite"
            ConfigManager.save_config(config)
            
        return config

    @staticmethod
    def save_config(config):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass

    @classmethod
    def load_pets_registry(cls):
        """pets.json 레지스트리를 단일 기준으로 읽어오며, 파일에서 삭제하거나 비활성화한 설정을 100% 존중합니다."""
        if os.path.exists(PETS_REGISTRY_PATH):
            try:
                with open(PETS_REGISTRY_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                pass
        return DEFAULT_PETS.copy()

    @classmethod
    def get_dynamic_salt(cls) -> bytes:
        """하드코딩 키 없이, 사용자의 머신 식별자(UUID/System Host)를 동적 결합한 무결점 솔트 생성"""
        import uuid
        import platform
        node_id = str(uuid.getnode())
        system_id = platform.node() + platform.processor()
        salt_str = f"win_pet_dynamic_salt_{node_id}_{system_id}"
        return salt_str.encode("utf-8")

    @classmethod
    def _xor_cipher(cls, data: bytes) -> bytes:
        """동적 머신 고유 솔트를 이용한 XOR 비트 대칭 암호화/복호화"""
        salt_bytes = cls.get_dynamic_salt()
        return bytes([b ^ salt_bytes[i % len(salt_bytes)] for i, b in enumerate(data)])

    @classmethod
    def encode_key(cls, raw_key: str) -> str:
        """Secret Salt XOR 암호화 후 Base64 인코딩"""
        if not raw_key:
            return ""
        if raw_key.startswith("ENC_XOR:"):
            return raw_key
        raw_bytes = raw_key.strip().encode("utf-8")
        cipher_bytes = cls._xor_cipher(raw_bytes)
        encoded = base64.b64encode(cipher_bytes).decode("utf-8")
        return f"ENC_XOR:{encoded}"

    @classmethod
    def decode_key(cls, enc_key: str) -> str:
        """Secret Salt XOR 복호화"""
        if not enc_key:
            return ""
        if enc_key.startswith("ENC_XOR:"):
            try:
                cipher_b64 = enc_key[8:]
                cipher_bytes = base64.b64decode(cipher_b64.encode("utf-8"))
                raw_bytes = cls._xor_cipher(cipher_bytes)
                return raw_bytes.decode("utf-8")
            except Exception:
                return ""
        elif enc_key.startswith("ENC:"):
            # 이전 하위 호환
            try:
                raw_b64 = enc_key[4:]
                return base64.b64decode(raw_b64.encode("utf-8")).decode("utf-8")
            except Exception:
                return ""
        return enc_key

    @classmethod
    def get_api_key(cls) -> str:
        """.env 파일 전용으로 난독화된 GEMINI_API_KEY를 읽어 복호화 반환합니다."""
        env_file = os.path.join(BASE_DIR, ".env")
        if os.path.exists(env_file):
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for line in lines:
                    line_str = line.strip()
                    if line_str.startswith("GEMINI_API_KEY="):
                        val = line_str.split("=", 1)[1].strip()
                        if val and val != "your_gemini_api_key_here":
                            dec_key = cls.decode_key(val)
                            if dec_key:
                                return dec_key
            except Exception:
                pass
        elif not getattr(sys, 'frozen', False):
            # 개발 환경에서 파이썬 직접 실행 시만 호환
            env_key = os.getenv("GEMINI_API_KEY", "").strip()
            if env_key and env_key != "your_gemini_api_key_here":
                return cls.decode_key(env_key)

        return ""

    @classmethod
    def save_api_key(cls, raw_key: str):
        """API 키를 난독화하여 .env 파일 전용으로 보관하고 config.json에서는 완벽 제거합니다."""
        clean_key = raw_key.strip()
        enc_key = cls.encode_key(clean_key)
        env_file = os.path.join(BASE_DIR, ".env")

        # 1. .env 파일에 난독화 API 키 작성
        try:
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(f"GEMINI_API_KEY={enc_key}\n")
        except Exception as e:
            print(f"⚠️ .env API 키 저장 실패: {e}")

        # 2. config.json에서 API 키 필드 완벽 제거 (보안 격리)
        config = cls.load_config()
        modified = False
        for k in ["llm_api_key", "gemini_api_key"]:
            if k in config:
                del config[k]
                modified = True
        if modified:
            cls.save_config(config)

        # 3. 현재 런타임 메모리 적용
        os.environ["GEMINI_API_KEY"] = clean_key

    REG_APP_NAME = "win_pet_companion"

    @classmethod
    def is_autostart_enabled(cls) -> bool:
        """윈도우 레지스트리에 자동 실행이 등록되어 있는지 확인"""
        if os.name != 'nt':
            return False
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            try:
                val, _ = winreg.QueryValueEx(key, cls.REG_APP_NAME)
                winreg.CloseKey(key)
                return bool(val)
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False

    @classmethod
    def set_autostart(cls, enable: bool) -> bool:
        """윈도우 자동 실행 레지스트리 등록 및 해제"""
        if os.name != 'nt':
            return False
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_ALL_ACCESS
            )
            if enable:
                if getattr(sys, 'frozen', False):
                    exe_path = f'"{sys.executable}"'
                else:
                    main_py = os.path.join(BASE_DIR, "main.py")
                    python_exe = sys.executable
                    exe_path = f'"{python_exe}" "{main_py}"'
                winreg.SetValueEx(key, cls.REG_APP_NAME, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, cls.REG_APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)

            cfg = cls.load_config()
            cfg["start_with_windows"] = enable
            cls.save_config(cfg)
            return True
        except Exception as e:
            print(f"⚠️ 레지스트리 설정 오류: {e}")
            return False

    @staticmethod
    def save_pets_registry(pets_data):
        try:
            with open(PETS_REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump(pets_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass
