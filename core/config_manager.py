import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
PETS_REGISTRY_PATH = os.path.join(BASE_DIR, "pets.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

DEFAULT_CONFIG = {
    "current_pet": "owl_white",
    "llm_model": "gemini-3.1-flash-lite",
    "pet_width": 48,
    "pet_height": 48,
    "is_always_on_top": True,
    "move_speed": 1,
    "move_timer_ms": 70,
    "move_boundary_mode": "MEDIUM",
    "anim_interval_ms": 140
}

DEFAULT_PETS = {
    "owl_white": {"name": "🦉 복슬복슬 하얀 부엉이 (HD)", "enabled": True}
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
            print("💾 설정이 config.json에 저장되었습니다.")
        except Exception as e:
            print(f"❌ 설정 저장 실패: {e}")

    @classmethod
    def load_pets_registry(cls):
        """pets.json 레지스트리 데이터를 깔끔하고 빠르게 읽어오는 정갈한 로더"""
        pets_data = DEFAULT_PETS.copy()
        if os.path.exists(PETS_REGISTRY_PATH):
            try:
                with open(PETS_REGISTRY_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    pets_data.update(loaded)
            except Exception as e:
                print(f"⚠️ pets.json 로드 실패: {e}")

        # assets/ 폴더 내에 실재하는 펫만 동적 검증
        if os.path.exists(ASSETS_DIR):
            for item in os.listdir(ASSETS_DIR):
                item_path = os.path.join(ASSETS_DIR, item)
                if os.path.isdir(item_path):
                    walk_dir = os.path.join(item_path, "walk")
                    if os.path.exists(walk_dir) and item not in pets_data:
                        pets_data[item] = {
                            "name": f"🐾 {item.replace('_', ' ').title()}",
                            "enabled": True
                        }
                    
        return pets_data

    @staticmethod
    def save_pets_registry(pets_data):
        try:
            with open(PETS_REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump(pets_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ pets.json 저장 실패: {e}")
