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

def hex_to_rgb(hex_str):
    """Hex 색상 코드를 (R, G, B) 튜플로 변환"""
    hex_str = hex_str.lstrip("#").strip()
    if len(hex_str) == 6:
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return None

def smart_auto_center_square_remover(pil_img, target_colors=None, tolerance=65):
    """
    🎯 [3단계 완전 자동화 파이프라인]
    (1) 스마트 배경색 + 바깥쪽 연결된 지정 타겟 색상(마젠타/보라 그림자 등) 투명 제거
        - BFS Flood-Fill로 바깥쪽(배경)에서 이어져 있는 영역만 지워 캐릭터 내부 구멍 뚫림 방지!
    (2) 외곽 경계 잔여 자줏빛/마젠타 테두리 픽셀 타이트 정돈 (De-fringing)
    (3) 캐릭터 픽셀 바운딩 박스 타이트 크롭 (Tight-Crop)
    (4) 정사각형 1:1 캔버스 자동 생성 후 캐릭터 100% 정중앙(Center) 완벽 정렬!
    """
    img = pil_img.convert("RGBA")
    w, h = img.size

    # 기본 크로마키/그림자 지정 색상 (마젠타, 보라, 핫핑크 계열)
    default_target_hexs = ["#FF00FF", "#800080", "#AA00AA", "#FF00AA", "#7A007A", "#8B008B", "#990099"]
    if target_colors is None:
        target_colors = default_target_hexs
    elif isinstance(target_colors, list):
        target_colors = target_colors + [c for c in default_target_hexs if c not in target_colors]

    target_rgbs = []
    for c in target_colors:
        if isinstance(c, str):
            rgb = hex_to_rgb(c)
            if rgb:
                target_rgbs.append(rgb)
        elif isinstance(c, (tuple, list)) and len(c) >= 3:
            target_rgbs.append((c[0], c[1], c[2]))

    # 1. 배경색 및 최외곽 테두리 픽셀 수집
    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    bg_colors = [img.getpixel(c)[:3] for c in corners]

    mask = Image.new("L", (w, h), 255)
    pixels = img.load()
    mask_pixels = mask.load()

    def is_color_similar(p_rgb, bg_rgb, tol):
        return (abs(p_rgb[0] - bg_rgb[0]) + abs(p_rgb[1] - bg_rgb[1]) + abs(p_rgb[2] - bg_rgb[2])) <= tol

    def is_target_bg(p_rgb):
        # 모서리 배경색과 유사하거나 지정한 마젠타/보라 크로마키 색상과 유사한지 확인
        if any(is_color_similar(p_rgb, bg_c, tolerance) for bg_c in bg_colors):
            return True
        if any(is_color_similar(p_rgb, t_c, tolerance + 20) for t_c in target_rgbs):
            return True
        return False

    # 2. 바깥쪽(최외곽 경계)에서부터 출발하는 BFS Flood-Fill
    visited = set()
    queue = []

    # 최외곽 4개 테두리의 모든 픽셀을 탐색 시작점으로 등록
    for x in range(w):
        for y in [0, h - 1]:
            if (x, y) not in visited:
                visited.add((x, y))
                p = pixels[x, y]
                if p[3] < 50 or is_target_bg(p[:3]):
                    mask_pixels[x, y] = 0
                    queue.append((x, y))

    for y in range(h):
        for x in [0, w - 1]:
            if (x, y) not in visited:
                visited.add((x, y))
                p = pixels[x, y]
                if p[3] < 50 or is_target_bg(p[:3]):
                    mask_pixels[x, y] = 0
                    queue.append((x, y))

    # BFS 수행
    while queue:
        cx, cy = queue.pop(0)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                visited.add((nx, ny))
                np = pixels[nx, ny]
                if np[3] < 50 or is_target_bg(np[:3]):
                    mask_pixels[nx, ny] = 0
                    queue.append((nx, ny))

    img.putalpha(mask)

    # 3. 외곽 잔여 픽셀 정돈 (Border De-fringing)
    # 배경 제거 후 투명 영역과 맞닿아 있는 외곽 경계선 중 마젠타/보라 색조 픽셀 정리
    pixels = img.load()
    clean_mask = mask.copy()
    clean_pixels = clean_mask.load()

    for x in range(1, w - 1):
        for y in range(1, h - 1):
            if clean_pixels[x, y] > 0:
                p = pixels[x, y]
                p_rgb = p[:3]
                # 주변 8방향 중 하나라도 투명 픽셀이면 경계선 픽셀
                has_transparent_neighbor = any(
                    clean_pixels[x + dx, y + dy] == 0 
                    for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx != 0 or dy != 0)
                )
                if has_transparent_neighbor:
                    # 경계선 픽셀이 마젠타/보라 타겟 색상과 가깝다면 투명화
                    if any(is_color_similar(p_rgb, t_c, tolerance + 30) for t_c in target_rgbs):
                        clean_pixels[x, y] = 0

    img.putalpha(clean_mask)

    # 4. 투명 배경 크롭 (Tight-Crop)으로 캐릭터 픽셀만 타이트하게 추출
    bbox = img.getbbox()
    if bbox:
        cropped_char = img.crop(bbox)
    else:
        cropped_char = img

    # 5. 정사각형 1:1 캔버스 자동 생성 및 100% 꽉 차게 정중앙 배치 (여백 제거)
    cw, ch = cropped_char.size
    max_dim = max(cw, ch)
    square_size = max_dim

    square_canvas = Image.new("RGBA", (square_size, square_size), (0, 0, 0, 0))
    offset_x = (square_size - cw) // 2
    offset_y = (square_size - ch) // 2
    square_canvas.paste(cropped_char, (offset_x, offset_y), cropped_char)

    return square_canvas

def organize_and_convert_pet_pack(pet_id, pet_name=None, target_colors=None, tolerance=65):
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

    pet_name = pet_name or f"{pet_id.replace('_', ' ').title()}"
    try:
        print(f"[{pet_name}] 3단계 오토 파이프라인 (스마트 크로마키 투명화 ➔ 크롭 ➔ 1:1 정중앙 배치) 진행 중...")
    except Exception:
        print(f"[{pet_id}] 3단계 오토 파이프라인 진행 중...")

    categories = ["walk", "idle", "drag", "happy", "special"]
    for cat in categories:
        os.makedirs(os.path.join(pet_dir, cat), exist_ok=True)

    # 카테고리 내부 이미지도 항상 재투명화/정돈 수행
    for cat in categories:
        cat_dir = os.path.join(pet_dir, cat)
        if os.path.exists(cat_dir):
            for f in os.listdir(cat_dir):
                if f.endswith((".png", ".jpg", ".jpeg")):
                    f_path = os.path.join(cat_dir, f)
                    try:
                        raw = Image.open(f_path)
                        clean = smart_auto_center_square_remover(raw, target_colors=target_colors, tolerance=tolerance)
                        clean.save(f_path, "PNG")
                    except Exception as e:
                        print(f"[{f}] 정돈 실패: {e}")

    root_files = [f for f in os.listdir(pet_dir) if f.endswith((".png", ".jpg", ".jpeg")) and os.path.isfile(os.path.join(pet_dir, f))]
    for fname in root_files:
        fpath = os.path.join(pet_dir, fname)
        fname_lower = fname.lower()
        
        target_cat = None
        for cat in categories:
            if fname_lower.startswith(cat):
                target_cat = cat
                break

        if not target_cat:
            continue

        dest_dir = os.path.join(pet_dir, target_cat)
        dest_path = os.path.join(dest_dir, fname if fname.endswith(".png") else f"{os.path.splitext(fname)[0]}.png")

        try:
            raw_img = Image.open(fpath)
            clean_img = smart_auto_center_square_remover(raw_img, target_colors=target_colors, tolerance=tolerance)
            clean_img.save(dest_path, "PNG")
            
            if os.path.exists(fpath) and fpath != dest_path:
                os.remove(fpath)
            print(f"  ✓ [{fname}] ➔ [스마트 배경 투명 ➔ 1:1 정중앙 자동 배치] 완료 후 [{target_cat}/] 이동")
        except Exception as e:
            print(f"[{fname}] 변환 실패: {e}")

    pets_data = load_pets_json()
    pets_data[pet_id] = {
        "name": pet_name,
        "enabled": True
    }
    save_pets_json(pets_data)

    print(f"[성공] [{pet_name}] ({pet_id}) 3단계 오토 파이프라인 정돈이 완벽하게 완료되었습니다!")
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
    import argparse
    parser = argparse.ArgumentParser(description="🐾 범용 펫 오토 정돈 도구 (pet_generator.py)")
    parser.add_argument("pet_id", type=str, help="펫 폴더 ID (예: fox_orange)")
    parser.add_argument("pet_name", nargs="?", type=str, default=None, help="펫 표시 이름")
    parser.add_argument("--remove-colors", type=str, default=None, help="지울 색상 콤마 구분 Hex 목록 (예: '#FF00FF,#800080')")
    parser.add_argument("--tolerance", type=int, default=65, help="색상 탐지 허용 오차 (기본값: 65)")

    args = parser.parse_args()

    if args.pet_id.lower() == "delete":
        if args.pet_name:
            delete_pet(args.pet_name)
    elif args.pet_id.lower() == "list":
        list_pets()
    else:
        colors = [c.strip() for c in args.remove_colors.split(",")] if args.remove_colors else None
        organize_and_convert_pet_pack(args.pet_id, args.pet_name, target_colors=colors, tolerance=args.tolerance)

