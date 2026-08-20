import os
import sys
import json
import shutil
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PETS_JSON_PATH = os.path.join(BASE_DIR, "pets.json")

def load_pets_json():
    if os.path.exists(PETS_JSON_PATH):
        try:
            with open(PETS_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_pets_json(data):
    try:
        with open(PETS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ pets.json 저장 실패: {e}")

def smart_auto_center_square_remover(pil_img, tolerance=55):
    """
    🎯 [3단계 완전 자동화 파이프라인]
    (1) 스마트 배경색 탐지 및 100% 투명 제거 (Color Bleeding 대응)
    (2) 캐릭터 픽셀 바운딩 박스 타이트 크롭 (Tight-Crop)
    (3) 정사각형 1:1 캔버스 자동 생성 후 캐릭터 100% 정중앙(Center) 완벽 정렬!
    """
    img = pil_img.convert("RGBA")
    w, h = img.size
    
    # 1. 모서리 기반 배경색 수집 및 스마트 투명화 (BFS Flood-Fill)
    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    bg_colors = [img.getpixel(c) for c in corners]

    mask = Image.new("L", (w, h), 255)
    pixels = img.load()
    mask_pixels = mask.load()

    def is_bg_similar(p, bg_c):
        return (abs(p[0] - bg_c[0]) + abs(p[1] - bg_c[1]) + abs(p[2] - bg_c[2])) <= tolerance

    visited = set()
    queue = corners.copy()
    
    for c in corners:
        visited.add(c)
        mask_pixels[c[0], c[1]] = 0

    while queue:
        cx, cy = queue.pop(0)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                np = pixels[nx, ny]
                if any(is_bg_similar(np, bg_c) for bg_c in bg_colors):
                    visited.add((nx, ny))
                    mask_pixels[nx, ny] = 0
                    queue.append((nx, ny))

    img.putalpha(mask)

    # 2. 투명 배경 크롭 (Tight-Crop)으로 캐릭터 픽셀만 타이트하게 추출
    bbox = img.getbbox()
    if bbox:
        cropped_char = img.crop(bbox)
    else:
        cropped_char = img

    # 3. 정사각형 1:1 캔버스 자동 생성 및 정중앙(Center Alignment) 자동 배치
    cw, ch = cropped_char.size
    max_dim = max(cw, ch)
    # 여유 픽셀 패딩 (+10% 여백) 추가하여 꽉 차지 않게 예쁘게 정돈
    padding = int(max_dim * 0.1)
    square_size = max_dim + (padding * 2)

    square_canvas = Image.new("RGBA", (square_size, square_size), (0, 0, 0, 0))
    offset_x = (square_size - cw) // 2
    offset_y = (square_size - ch) // 2
    square_canvas.paste(cropped_char, (offset_x, offset_y), cropped_char)

    return square_canvas

def organize_and_convert_pet_pack(pet_id, pet_name=None):
    """
    🎯 [3단계 오토 파이프라인 통합 에셋 정돈기]
    사용자가 직접 정사각형으로 자르는 수고 0%!
    어떤 비율/여백의 이미지를 넣어놔도 알아서 
    [배경 투명화 -> 캐릭터 크롭 -> 정사각형 1:1 정중앙 배치] 100% 자동 완성!
    """
    pet_dir = os.path.join(ASSETS_DIR, pet_id)
    if not os.path.exists(pet_dir):
        print(f"❌ [{pet_dir}] 폴더를 찾을 수 없습니다.")
        return False

    pet_name = pet_name or f"🐾 {pet_id.replace('_', ' ').title()}"
    print(f"🧹 [{pet_name}] 3단계 오토 파이프라인 (투명화 ➔ 크롭 ➔ 1:1 정중앙 배치) 진행 중...")

    categories = ["walk", "idle", "drag", "happy", "special"]
    for cat in categories:
        os.makedirs(os.path.join(pet_dir, cat), exist_ok=True)

    root_files = [f for f in os.listdir(pet_dir) if f.endswith((".png", ".jpg", ".jpeg")) and os.path.isfile(os.path.join(pet_dir, f))]

    if not root_files:
        print(f"ℹ️ [{pet_id}] 루트 폴더에 이동할 이미지 파일이 없거나 이미 정돈이 완료되었습니다.")
        for cat in categories:
            cat_dir = os.path.join(pet_dir, cat)
            if os.path.exists(cat_dir):
                for f in os.listdir(cat_dir):
                    if f.endswith((".png", ".jpg", ".jpeg")):
                        f_path = os.path.join(cat_dir, f)
                        try:
                            raw = Image.open(f_path)
                            clean = smart_auto_center_square_remover(raw)
                            clean.save(f_path, "PNG")
                        except Exception:
                            pass
    else:
        for fname in root_files:
            fpath = os.path.join(pet_dir, fname)
            fname_lower = fname.lower()
            
            target_cat = None
            for cat in categories:
                if fname_lower.startswith(cat):
                    target_cat = cat
                    break

            if not target_cat:
                print(f"  ⏭️ [{fname}] 규칙 미지정 무작위 파일 ➔ 원본 유지 (건너뜀)")
                continue

            dest_dir = os.path.join(pet_dir, target_cat)
            dest_path = os.path.join(dest_dir, fname if fname.endswith(".png") else f"{os.path.splitext(fname)[0]}.png")

            try:
                raw_img = Image.open(fpath)
                # 💡 3단계 자동화 (배경투명 -> 크롭 -> 1:1 정중앙 배치)
                clean_img = smart_auto_center_square_remover(raw_img)
                clean_img.save(dest_path, "PNG")
                
                # 사본 저장 후 원래 루트 파일 안전 제거
                if os.path.exists(fpath) and fpath != dest_path:
                    os.remove(fpath)
                print(f"  ✓ [{fname}] ➔ [배경 투명 ➔ 1:1 정중앙 자동 배치] 완료 후 [{target_cat}/] 이동")
            except Exception as e:
                print(f"⚠️ [{fname}] 변환 실패: {e}")

    pets_data = load_pets_json()
    pets_data[pet_id] = {
        "name": pet_name,
        "enabled": True
    }
    save_pets_json(pets_data)

    print(f"🎉 [성공] [{pet_name}] ({pet_id}) 3단계 오토 파이프라인 정돈이 완벽하게 완료되었습니다!")
    return True

def delete_pet(pet_id):
    pet_dir = os.path.join(ASSETS_DIR, pet_id)
    if os.path.exists(pet_dir):
        shutil.rmtree(pet_dir, ignore_errors=True)
        print(f"🗑️ [{pet_id}] 에셋 폴더가 삭제되었습니다.")

    pets_data = load_pets_json()
    if pet_id in pets_data:
        del pets_data[pet_id]
        save_pets_json(pets_data)
        print(f"🗑️ pets.json에서 [{pet_id}]가 삭제되었습니다.")

def list_pets():
    pets_data = load_pets_json()
    print("\n📋 현재 등록된 펫 목록:")
    for k, v in pets_data.items():
        status = "✅ 활성화" if v.get("enabled", True) else "❌ 비활성화"
        print(f"  • ID: {k:15s} | 이름: {v.get('name', k):25s} | 상태: {status}")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("🐾 범용 펫 오토 정돈 도구 (pet_generator.py) 🐾")
        print("💡 사용법: python pet_generator.py <pet_id> [펫이름]")
        print("   예시: python pet_generator.py fox_orange \"🦊 주황 아기 여우\"")
    else:
        cmd = sys.argv[1].lower()
        if cmd == "delete" and len(sys.argv) >= 3:
            delete_pet(sys.argv[2])
        elif cmd == "list":
            list_pets()
        else:
            pid = sys.argv[1]
            pname = sys.argv[2] if len(sys.argv) >= 3 else None
            organize_and_convert_pet_pack(pid, pname)
