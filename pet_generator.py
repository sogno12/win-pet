"""
pet_generator.py - 단 하나의 범용 펫 자동 생성 및 표준 5대 폴더 자동 분할 스크립트

사용법:
    python pet_generator.py --id tiger --name "🐯 호랑이" --prompt "cute chubby baby tiger"
"""

import os
import sys
import argparse
from PIL import Image

def is_magenta_bg(r, g, b):
    # 마젠타 핑크 (#FF00FF) 배경 판별
    return r > 180 and g < 100 and b > 180

def remove_magenta_bg(img):
    img = img.convert("RGBA")
    datas = img.get_flattened_data() if hasattr(img, 'get_flattened_data') else img.getdata()
    new_data = []
    for item in datas:
        r, g, b, a = item[0], item[1], item[2], item[3]
        if is_magenta_bg(r, g, b):
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)
    return img

def auto_generate_and_slice_pet(pet_id: str, pet_name: str, custom_prompt: str = None):
    """
    하나의 공통 함수로 5대 표준 폴더(walk, idle, drag, happy, special)를 자동 세팅합니다.
    """
    base_dir = os.path.dirname(__file__)
    pet_dir = os.path.join(base_dir, "assets", pet_id)
    
    walk_dir = os.path.join(pet_dir, "walk")
    idle_dir = os.path.join(pet_dir, "idle")
    drag_dir = os.path.join(pet_dir, "drag")
    happy_dir = os.path.join(pet_dir, "happy")
    special_dir = os.path.join(pet_dir, "special")
    
    for d in [walk_dir, idle_dir, drag_dir, happy_dir, special_dir]:
        os.makedirs(d, exist_ok=True)
        
    print(f"✨ [{pet_name}] ({pet_id}) 5대 표준 폴더 생성 완료!")
    print(f"📂 저장 경로: {pet_dir}")
    print("👉 이제 AI로 생성되거나 가지고 계신 픽셀 이미지를 walk, idle, drag 폴더에 넣으시면 main.py가 즉시 인식합니다!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="새로운 픽셀 펫 스킨을 5대 표준 폴더에 자동 생성합니다.")
    parser.add_argument("--id", required=True, help="펫 식별자 (예: tiger, penguin, hamster)")
    parser.add_argument("--name", required=True, help="표시 이름 (예: '🐯 아기 호랑이')")
    parser.add_argument("--prompt", help="AI 생성 프롬프트 힌트")
    
    args = parser.parse_args()
    auto_generate_and_slice_pet(args.id, args.name, args.prompt)
