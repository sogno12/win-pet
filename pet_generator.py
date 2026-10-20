import os
import sys
import json
import shutil
from PIL import Image

from core.config_manager import ConfigManager, BASE_DIR, ASSETS_DIR, PETS_REGISTRY_PATH
from core.sprite_normalizer import normalize_pet_dir, ALIGNED_MARKER
from core.sheet_splitter import split_sheet

# 정렬 전 프레임 보관 위치 (assets/ 밖이라 펫 폴더로 오인되지 않음)
RAW_BACKUP_DIR = os.path.join(BASE_DIR, "assets_raw")

def load_pets_json():
    return ConfigManager.load_pets_registry()

def save_pets_json(data):
    ConfigManager.save_pets_registry(data)

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

    # 이미 배경이 투명한 이미지는 다시 크로마키 처리하지 않음
    # (투명 모서리의 RGB(0,0,0)를 배경색으로 오인해 검은 머리카락/옷 테두리를 지워버리는 문제 방지)
    if img.getextrema()[3][0] == 0:
        return img

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

    categories = ["walk", "idle", "drag", "happy", "special", "think"]
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

        # 접두사가 없는 파일명(예: 1.png, image.png)은 기본적으로 walk 카테고리로 자동 할당
        if not target_cat:
            target_cat = "walk"

        dest_dir = os.path.join(pet_dir, target_cat)
        dest_path = os.path.join(dest_dir, fname if fname.endswith(".png") else f"{os.path.splitext(fname)[0]}.png")

        try:
            raw_img = Image.open(fpath)
            clean_img = smart_auto_center_square_remover(raw_img, target_colors=target_colors, tolerance=tolerance)
            clean_img.save(dest_path, "PNG")
            
            if os.path.exists(fpath) and fpath != dest_path:
                os.remove(fpath)
            print(f"  [OK] [{fname}] -> [{target_cat}/] 이동")
        except Exception as e:
            print(f"[{fname}] 변환 실패: {e}")

    # 모든 프레임을 같은 캔버스/같은 크기/발바닥 기준으로 정렬 (프레임 간 출렁임 제거)
    # 배경 제거까지 끝난 정렬 전 프레임은 assets_raw/에 보관되고, 이후 재정렬은 항상 그 보관본에서 시작
    sprite_scale = load_pets_json().get(pet_id, {}).get("sprite_scale", "height")
    normalize_pet_dir(pet_dir, mode=sprite_scale, backup_root=RAW_BACKUP_DIR)

    # 변환 결과 검증: walk 또는 idle에 유효한 프레임이 존재하는지 확인
    walk_dir = os.path.join(pet_dir, "walk")
    idle_dir = os.path.join(pet_dir, "idle")
    walk_frames = [f for f in os.listdir(walk_dir) if f.endswith((".png", ".jpg", ".jpeg"))] if os.path.exists(walk_dir) else []
    idle_frames = [f for f in os.listdir(idle_dir) if f.endswith((".png", ".jpg", ".jpeg"))] if os.path.exists(idle_dir) else []
    
    if not walk_frames and not idle_frames:
        print(f"[FAIL] [{pet_name}] ({pet_id}) 유효한 이미지 프레임이 생성되지 않아 등록이 취소되었습니다.")
        return False

    # walk 프레임이 비어있고 idle만 있다면 안전하게 idle 프레임을 복사
    if not walk_frames and idle_frames:
        shutil.copy2(os.path.join(idle_dir, idle_frames[0]), os.path.join(walk_dir, idle_frames[0]))

    # 모든 변환 및 검증이 완벽히 끝난 최종 단계에서 pets.json에 즉시 디스크 영구 저장!
    pets_data = load_pets_json()
    existing_pet = pets_data.get(pet_id, {})
    
    # 💡 species, tone, speech_style 기본 템플릿 자동 지정
    clean_species = pet_name.replace("🐾", "").replace("🦉", "").replace("🦊", "").strip() or pet_id.replace("_", " ").title()
    
    pets_data[pet_id] = {
        "name": pet_name,
        "species": existing_pet.get("species", clean_species),
        "tone": existing_pet.get("tone", "다정하고 애교 있으며 호기심 많음"),
        "speech_style": existing_pet.get("speech_style", "다정하고 친근한 존댓말체 (~해요, ~합니다, ~해드릴게요)"),
        "enabled": True
    }
    save_pets_json(pets_data)

    print(f"[SUCCESS] [{pet_id}] 3단계 오토 파이프라인 정돈 완료 및 페르소나 포함 pets.json 최종 등록 성공!")
    return True

# 시트 칸 순서(왼→오, 위→아래)별 카테고리. 이미지 생성 프롬프트의 4x3 배치와 동일
DEFAULT_SHEET_LAYOUT = ["walk"] * 4 + ["idle"] * 2 + ["happy"] * 2 + ["drag"] + ["special"] * 3


def _move_files(src_dir, dst_dir):
    """src_dir 아래 파일을 dst_dir로 하위 구조 그대로 이동 (폴더 자체는 남김)"""
    if not os.path.isdir(src_dir):
        return
    for root, _, files in os.walk(src_dir):
        for f in files:
            dst = os.path.join(dst_dir, os.path.relpath(os.path.join(root, f), src_dir))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.replace(os.path.join(root, f), dst)


def replace_frames_from_sheet(pet_id, sheet_path, cols=4, rows=3, layout=None):
    """스프라이트 시트에서 펫 프레임을 교체

    layout: 칸 순서(왼→오, 위→아래)별 대상. 예) "walk", "_"(사용 안 함),
            "walk@1"(파일 번호 지정), "walk@1|walk@3"(한 칸을 여러 프레임에 재사용)
    layout에 등장하는 카테고리만 교체하고 나머지(idle 등)는 그대로 둔다.
    교체되는 카테고리의 기존 파일과 assets_raw/<펫ID>/ 보관본은 assets_raw/_archive/ 로 옮긴다.
    """
    layout = layout or DEFAULT_SHEET_LAYOUT
    if len(layout) != cols * rows:
        raise ValueError(f"layout 칸 수({len(layout)})가 {cols}x{rows}와 다릅니다.")

    frames = split_sheet(Image.open(sheet_path), cols, rows)  # 실패 시 기존 파일은 그대로

    # (프레임, 카테고리, 파일번호) 목록으로 펼치기
    targets, counters = [], {}
    for img, cell in zip(frames, layout):
        for t in cell.split("|"):
            t = t.strip()
            if not t or t in ("-", "_"):
                continue
            cat, _, num = t.partition("@")
            idx = int(num) if num else counters.get(cat, 0)
            counters[cat] = max(counters.get(cat, 0), idx + 1)
            targets.append((img, cat, idx))
    return _install_frames(pet_id, targets, source=sheet_path)


def replace_frames_from_video(pet_id, video_path, category="walk", count=8, start_sec=None, end_sec=None, loop=True,
                              trim_effects=False, pad=8):
    """그린스크린 동영상에서 프레임을 뽑아 한 카테고리(walk/special 등)를 교체"""
    from core.video_extractor import extract_frames
    frames, info = extract_frames(video_path, count=count, start_sec=start_sec, end_sec=end_sec, loop=loop,
                                  trim_effects=trim_effects, pad=pad)
    print(f"[VIDEO] {info}")
    return _install_frames(pet_id, [(img, category, i) for i, img in enumerate(frames)], source=video_path,
                           aligned=True)


def _install_frames(pet_id, targets, source="", aligned=False):
    """(이미지, 카테고리, 번호) 목록으로 해당 카테고리 프레임을 교체하고 정규화

    교체되는 카테고리의 기존 파일과 assets_raw/<펫ID>/ 보관본은 assets_raw/_archive/ 로 옮긴다.
    """
    from datetime import datetime
    pet_dir = os.path.join(ASSETS_DIR, pet_id)
    cats = sorted({cat for _, cat, _ in targets})
    archive = os.path.join(RAW_BACKUP_DIR, "_archive", f"{pet_id}_{datetime.now():%Y%m%d_%H%M%S}")
    for cat in cats:
        _move_files(os.path.join(pet_dir, cat), os.path.join(archive, "assets", cat))
        _move_files(os.path.join(RAW_BACKUP_DIR, pet_id, cat), os.path.join(archive, "raw", cat))

    for cat in cats:
        os.makedirs(os.path.join(pet_dir, cat), exist_ok=True)
        if aligned:  # 동영상 추출본: 정규화 때 프레임 간 위치 관계(점프 높이 등)를 유지
            with open(os.path.join(pet_dir, cat, ALIGNED_MARKER), "w", encoding="utf-8") as f:
                f.write(os.path.basename(source))

    counts = {}
    for img, cat, idx in targets:
        os.makedirs(os.path.join(pet_dir, cat), exist_ok=True)
        prefix = cat.split("/")[0]  # special/dog → special_0.png
        img.save(os.path.join(pet_dir, cat, f"{prefix}_{idx}.png"), "PNG")
        counts[cat] = counts.get(cat, 0) + 1

    mode = load_pets_json().get(pet_id, {}).get("sprite_scale", "height")
    n = normalize_pet_dir(pet_dir, mode=mode, backup_root=RAW_BACKUP_DIR)
    print(f"[OK] {pet_id}: {os.path.basename(source)} → {counts} 교체, 전체 {n}개 프레임 정규화 (이전 파일: {os.path.relpath(archive, BASE_DIR)})")
    return n


def delete_pet(pet_id):
    pet_dir = os.path.join(ASSETS_DIR, pet_id)
    if os.path.exists(pet_dir):
        shutil.rmtree(pet_dir, ignore_errors=True)
        print(f"[DELETE] [{pet_id}] 에셋 폴더가 삭제되었습니다.")

    pets_data = load_pets_json()
    if pet_id in pets_data:
        del pets_data[pet_id]
        save_pets_json(pets_data)
        print(f"[DELETE] pets.json에서 [{pet_id}]가 삭제되었습니다.")

def list_pets():
    pets_data = load_pets_json()
    print("\n[PET LIST] 현재 등록된 펫 목록:")
    for k, v in pets_data.items():
        status = "활성화" if v.get("enabled", True) else "비활성화"
        print(f"  * ID: {k:15s} | 이름: {v.get('name', k):25s} | 상태: {status}")
    print()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="🐾 범용 펫 오토 정돈 도구 (pet_generator.py)")
    parser.add_argument("pet_id", type=str, help="펫 폴더 ID (예: fox_orange)")
    parser.add_argument("pet_name", nargs="?", type=str, default=None, help="펫 표시 이름")
    parser.add_argument("--remove-colors", type=str, default=None, help="지울 색상 콤마 구분 Hex 목록 (예: '#FF00FF,#800080')")
    parser.add_argument("--tolerance", type=int, default=65, help="색상 탐지 허용 오차 (기본값: 65)")
    parser.add_argument("--sheet", type=str, default=None, help="split: 스프라이트 시트 이미지 경로")
    parser.add_argument("--cols", type=int, default=4, help="split: 시트 열 수 (기본 4)")
    parser.add_argument("--rows", type=int, default=3, help="split: 시트 행 수 (기본 3)")
    parser.add_argument("--video", type=str, default=None, help="video: 그린스크린 동영상 경로")
    parser.add_argument("--category", type=str, default="walk", help="video: 교체할 카테고리 (기본 walk). 특수 동작은 special/이름 (예: special/dog)")
    parser.add_argument("--frames", type=int, default=8, help="video: 추출할 프레임 수 (기본 8)")
    parser.add_argument("--start", type=float, default=None, help="video: 시작 초")
    parser.add_argument("--end", type=float, default=None, help="video: 끝 초 (--once 일 때)")
    parser.add_argument("--once", action="store_true", help="video: 반복 동작이 아닌 1회성 동작(지팡이 휘두르기 등)으로 구간 균등 추출")
    parser.add_argument("--pad", type=int, default=8, help="video: 몸 주변 몇 px까지 이펙트(하트 등)를 살릴지 (기본 8)")
    parser.add_argument("--trim-effects", action="store_true", help="video: 일부 프레임에만 크게 퍼지는 연기·이펙트는 잘라냄")
    parser.add_argument("--layout", type=str, default=None, help="split: 칸별 대상 콤마 목록. '_'=건너뜀, 'walk@1'=번호 지정, 'a|b'=한 칸 재사용 (기본 walk x4,idle x2,happy x2,drag,special x3)")

    args = parser.parse_args()

    if args.pet_id.lower() == "video":
        # 예: python pet_generator.py video sirius_black --video assets_raw/sheets/sirius_walk.mp4
        #     python pet_generator.py video sirius_black --video wand.mp4 --category special --once --start 1 --end 4 --frames 6
        replace_frames_from_video(args.pet_name, args.video, args.category, args.frames,
                                  args.start, args.end, loop=not args.once, trim_effects=args.trim_effects, pad=args.pad)
    elif args.pet_id.lower() == "split":
        # 예: python pet_generator.py split sirius_black --sheet assets_raw/sheets/sirius_black_sheet.png
        layout = [c.strip() for c in args.layout.split(",")] if args.layout else None
        replace_frames_from_sheet(args.pet_name, args.sheet, args.cols, args.rows, layout)
    elif args.pet_id.lower() == "normalize":
        # 예: python pet_generator.py normalize all   /   python pet_generator.py normalize fox_orange
        pets = load_pets_json()
        targets = list(pets.keys()) if args.pet_name in (None, "all") else [args.pet_name]
        for pid in targets:
            pdir = os.path.join(ASSETS_DIR, pid)
            if not os.path.isdir(pdir):
                print(f"[SKIP] {pid}: 폴더 없음")
                continue
            mode = pets.get(pid, {}).get("sprite_scale", "height")
            n = normalize_pet_dir(pdir, mode=mode, backup_root=RAW_BACKUP_DIR)
            print(f"[OK] {pid}: {n}개 프레임 정규화 (mode={mode}, 원본 보관: assets_raw/{pid}/)")
    elif args.pet_id.lower() == "delete":
        if args.pet_name:
            delete_pet(args.pet_name)
    elif args.pet_id.lower() == "list":
        list_pets()
    else:
        colors = [c.strip() for c in args.remove_colors.split(",")] if args.remove_colors else None
        organize_and_convert_pet_pack(args.pet_id, args.pet_name, target_colors=colors, tolerance=args.tolerance)

