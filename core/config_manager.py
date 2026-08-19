import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
PETS_REGISTRY_PATH = os.path.join(BASE_DIR, "pets.json")

DEFAULT_CONFIG = {
    "current_pet": "cat_cheese",
    "pet_width": 48,
    "pet_height": 48,
    "is_always_on_top": True,
    "move_speed": 1,
    "anim_interval_ms": 140
}

DEFAULT_PETS = {
    "cat_cheese": {"name": "🧀 치즈태비 고양이", "enabled": True},
    "owl_white": {"name": "🦉 헤드위그 하얀 부엉이", "enabled": True}
}

class ConfigManager:
    """설정 데이터 및 펫 메타데이터 레지스트리 총괄 클래스"""
    
    @staticmethod
    def load_config():
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except Exception as e:
                print(f"⚠️ 설정 로드 실패, 기본값 사용: {e}")
        return DEFAULT_CONFIG.copy()

    @staticmethod
    def save_config(config):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print("💾 설정이 config.json에 저장되었습니다.")
        except Exception as e:
            print(f"❌ 설정 저장 실패: {e}")

    @staticmethod
    def load_pets_registry():
        """pets.json을 읽고, assets/ 폴더의 신규 펫을 동적 스캔하여 자동 등록"""
        pets_data = DEFAULT_PETS.copy()
        if os.path.exists(PETS_REGISTRY_PATH):
            try:
                with open(PETS_REGISTRY_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    pets_data.update(loaded)
            except Exception as e:
                print(f"⚠️ pets.json 로드 실패: {e}")

        assets_dir = os.path.join(BASE_DIR, "assets")
        if os.path.exists(assets_dir):
            for item in os.listdir(assets_dir):
                item_path = os.path.join(assets_dir, item)
                if os.path.isdir(item_path) and item not in pets_data:
                    pets_data[item] = {
                        "name": f"🐾 {item}",
                        "enabled": True
                    }
                    
        ConfigManager.save_pets_registry(pets_data)
        return pets_data

    @staticmethod
    def save_pets_registry(pets_data):
        try:
            with open(PETS_REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump(pets_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ pets.json 저장 실패: {e}")
