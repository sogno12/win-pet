"""펫 스프라이트 프레임 정규화

프레임마다 원본 크기/여백이 달라서 48px로 줄였을 때 캐릭터가 출렁이던 문제를 해결한다.
펫 한 마리의 모든 프레임(walk/idle/drag/happy/special)을 한 그룹으로 보고
  1) 크로마키(마젠타) 잔여 픽셀 제거
  2) 캐릭터 영역만 타이트 크롭
  3) 공통 기준으로 크기 통일
  4) 같은 크기 정사각 캔버스에 발바닥(아래쪽) 기준 정렬
     가로는 머리 위치 기준 정렬 (팔·다리·망토가 흔들려도 몸이 좌우로 미끄러지지 않게)
해서 저장한다.

크기 통일 방식 (pets.json 의 "sprite_scale")
  - "height" (기본): 모든 프레임의 캐릭터 키를 같게 맞춤. 프레임마다 따로 생성/확대된 그림(AI 생성)에 적합
  - "keep": 같은 카테고리(walk 등) 안에서는 원본 상대 크기 유지 (날개를 펴는 프레임 등).
            카테고리끼리는 대표 키(중앙값)를 맞춤 (idle/walk 원본 해상도가 서로 달라도 OK)

재실행 시 항상 assets_raw/ 의 원본에서 다시 만든다 (정돈본을 재가공하며 화질이 깎이는 것 방지).
"""
import os
import re
import shutil
from PIL import Image

CATEGORIES = ["walk", "idle", "drag", "happy", "special", "think"]
IMAGE_EXTS = (".png", ".jpg", ".jpeg")
CANVAS_SIZE = 256      # 저장 캔버스 (화면 표시는 AssetLoader가 24~128px로 축소)
FILL_RATIO = 0.94      # 캔버스 대비 캐릭터 최대 크기
BOTTOM_MARGIN = 4      # 발바닥 아래 여백(px)
BASE_GROUPS = ("walk", "idle")  # 펫 크기의 기준이 되는 동작
CLIP_MARKER = "_allow_clip"  # 이 파일이 있는 폴더는 크기를 줄이지 않고 넘치는 가장자리를 자름
ALIGNED_MARKER = "_from_video"  # 이 파일이 있는 폴더는 프레임 위치가 맞춰진 동영상 추출본


def remove_chroma_residue(img: Image.Image) -> Image.Image:
    """배경 제거 후 남은 마젠타 계열 픽셀(테두리 잔여물, 팔-몸 사이 구멍 등)을 투명화

    녹색 성분이 거의 없고 R≈B 인 순수 마젠타/보라만 대상 (분홍 눈동자, 빨간 망토 안감은 해당 없음)
    """
    img = img.convert("RGBA")
    try:
        import numpy as np
    except ImportError:
        np = None

    if np is not None:
        arr = np.array(img)
        r, g, b = (arr[..., i].astype(int) for i in range(3))
        mask = (g < 60) & (r > 50) & (b > 50) & (abs(r - b) < 60) & (r - g > 50)
        arr[..., 3][mask] = 0
        return Image.fromarray(arr, "RGBA")

    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            rv, gv, bv, av = px[x, y]
            if av and gv < 60 and rv > 50 and bv > 50 and abs(rv - bv) < 60 and rv - gv > 50:
                px[x, y] = (rv, gv, bv, 0)
    return img


def _tight_crop(img: Image.Image) -> Image.Image:
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def _head_center_x(img, top_ratio=0.3):
    """캐릭터 윗부분(머리)의 가로 중심 x"""
    a = img.getchannel("A")
    head = a.crop((0, 0, img.width, max(1, int(img.height * top_ratio))))
    try:
        import numpy as np
        cols = np.asarray(head).astype(float).sum(axis=0)
        return float((cols * np.arange(len(cols))).sum() / cols.sum()) if cols.sum() else img.width / 2
    except ImportError:
        bbox = head.getbbox()
        return (bbox[0] + bbox[2]) / 2 if bbox else img.width / 2


def normalize_frames(frames, mode="height", groups=None, aligned=(), allow_clip=(), canvas=CANVAS_SIZE):
    """RGBA 프레임 리스트를 같은 캔버스/같은 기준으로 정렬해 반환

    groups : 프레임별 그룹 이름(카테고리). mode="keep"일 때 그룹 안에서만 상대 크기를 유지한다.
    allow_clip: 줄이지 않고 평소 크기로 그리는 그룹 (칸 밖으로 나가는 이펙트 가장자리는 잘림)
    aligned: 프레임끼리 위치가 이미 맞춰진 그룹(동영상에서 뽑은 프레임). 그룹 전체를 한 영역으로 잘라
             점프 높이·몸의 흔들림 같은 원본 움직임을 그대로 살린다.
    """
    cleaned = [remove_chroma_residue(f) for f in frames]
    crops = [_tight_crop(c) for c in cleaned]
    groups = groups or ["all"] * len(crops)

    # 그룹별 대표 키: 보통은 중앙값, 동영상(aligned)은 첫 프레임
    # (변신처럼 중간에 모습이 바뀌어도 시작 모습이 다른 동작과 같은 크기가 되도록)
    med = {}
    for g in set(groups):
        hs = [c.height for c, gg in zip(crops, groups) if gg == g]
        med[g] = hs[0] if g in aligned else sorted(hs)[len(hs) // 2]

    # aligned 그룹: 그룹 합집합 영역으로 자른 이미지를 사용 (프레임 크기·위치 관계 동일)
    union = {}
    for g in set(groups) & set(aligned):
        boxes = [c.getbbox() for c, gg in zip(cleaned, groups) if gg == g and c.getbbox()]
        union[g] = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    sources = [cl.crop(union[g]) if g in union else cr for cl, cr, g in zip(cleaned, crops, groups)]

    # 프레임별 '상대 키': height 모드는 전부 1(키 통일), keep/aligned 는 그룹 중앙값 대비 비율
    units = [c.height / med[g] if (mode == "keep" or g in union) else 1.0 for c, g in zip(crops, groups)]

    # 캔버스를 넘지 않도록 기준 키 결정.
    # 가장 자주 보이는 walk/idle 기준으로 정하고, 다른 동작(날개 펴기·변신·이펙트)이 넘치면 그 동작만 따로 줄인다
    max_char = canvas * FILL_RATIO
    need = {}
    for src, c, u, g in zip(sources, crops, units, groups):
        need[g] = max(need.get(g, 0), u * max(src.width, src.height) / c.height)
    normal = ([v for g, v in need.items() if g in BASE_GROUPS]
              or [v for g, v in need.items() if not g.startswith("special")] or list(need.values()))
    base_h = max_char / max(normal)
    group_h = {g: base_h if g in allow_clip else min(base_h, max_char / v) for g, v in need.items()}

    scales = [group_h[g] * u / c.height for c, u, g in zip(crops, units, groups)]

    # 변신처럼 일부 프레임(개·연기) 때문에 크게 줄어든 동영상 특수 동작:
    # 첫 프레임과 모양이 비슷한 '원래 모습' 프레임은 평소 크기로, 발을 바닥에 붙여 그린다
    # (모습이 바뀌는 순간은 연기가 가려서 크기 변화가 드러나지 않음)
    first = {}
    for i, g in enumerate(groups):
        first.setdefault(g, i)
    pose, grounded = set(), set()
    for i, (c, g) in enumerate(zip(crops, groups)):
        if g in union and g.startswith("special") and group_h[g] < base_h * 0.9:
            grounded.add(i)  # 모습이 바뀌는 동작은 프레임마다 자기 발 위치를 바닥에 붙임 (떠 보이지 않게)
            ref = crops[first[g]]
            # 키가 원래 모습과 비슷하고(연기가 막 덮기 시작한 장면 포함), 평소 크기로 키워도 칸에 들어가면
            fits = c.width * base_h / med[g] <= canvas
            if abs(c.height / ref.height - 1) < 0.1 and fits:
                pose.add(i)
    for i in pose:
        sources[i] = crops[i]
        scales[i] = base_h / med[groups[i]]
    heads = [_head_center_x(src) * sc for src, sc in zip(sources, scales)]
    widths = [src.width * sc for src, sc in zip(sources, scales)]
    # 그룹별 '머리가 몸 중심에서 벗어난 평균 거리' → 그룹 안에서는 머리 x를 고정, 몸 전체는 대략 가운데
    offs = {}
    for g, hx, w in zip(groups, heads, widths):
        offs.setdefault(g, []).append(hx - w / 2)
    mean_off = {g: sum(v) / len(v) for g, v in offs.items()}

    out = []
    for i, (src, sc, hx, g) in enumerate(zip(sources, scales, heads, groups)):
        nw, nh = max(1, round(src.width * sc)), max(1, round(src.height * sc))
        # 투명 테두리 번짐 방지를 위해 premultiplied alpha(RGBa)로 리샘플
        resized = src.convert("RGBa").resize((nw, nh), Image.LANCZOS).convert("RGBA")
        sheet = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
        if g in union or i in pose:
            x = (canvas - nw) // 2  # 영상 속 위치 그대로 (원래 모습 프레임은 가운데)
        else:
            x = max(0, min(canvas - nw, round(canvas / 2 + mean_off[g] - hx)))
        y = canvas - BOTTOM_MARGIN - nh
        if i in grounded and i not in pose:
            bottom = cleaned[i].getbbox()[3] - union[g][1]  # 이 프레임의 실제 발끝 (영역 위쪽 기준)
            y = canvas - BOTTOM_MARGIN - round(bottom * sc)
        sheet.paste(resized, (x, y), resized)
        out.append(sheet)
    return out


def _natural_key(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def collect_frame_paths(pet_dir):
    paths = []
    for cat in CATEGORIES:
        cat_dir = os.path.join(pet_dir, cat)
        # 하위 폴더(special/wand, special/dog 등)까지 포함
        for root, dirs, files in os.walk(cat_dir):
            dirs.sort()
            for f in sorted(files, key=_natural_key):
                if f.lower().endswith(IMAGE_EXTS):
                    paths.append(os.path.join(root, f))
    return paths


def backup_originals(pet_dir, paths, backup_root):
    """덮어쓰기 전 원본을 backup_root/<펫ID>/<카테고리>/ 에 보관 (이미 있으면 최초 원본 유지)"""
    pet_id = os.path.basename(os.path.normpath(pet_dir))
    for p in paths:
        rel = os.path.relpath(p, pet_dir)
        dest = os.path.join(backup_root, pet_id, rel)
        if not os.path.exists(dest):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(p, dest)


def normalize_pet_dir(pet_dir, mode="height", backup_root=None):
    """펫 폴더의 카테고리 프레임 전체를 정규화해 PNG로 덮어쓴다. 처리한 프레임 수 반환

    backup_root가 주어지면 원본을 보관하고, 보관된 원본이 있으면 그것을 입력으로 쓴다.
    """
    paths = collect_frame_paths(pet_dir)
    if not paths:
        return 0

    sources = paths
    if backup_root:
        backup_originals(pet_dir, paths, backup_root)
        pet_id = os.path.basename(os.path.normpath(pet_dir))
        sources = [os.path.join(backup_root, pet_id, os.path.relpath(p, pet_dir)) for p in paths]

    frames = [Image.open(p).convert("RGBA") for p in sources]
    groups = [os.path.relpath(os.path.dirname(p), pet_dir) for p in paths]  # 예: walk, special/wand
    aligned = {g for g in set(groups) if os.path.exists(os.path.join(pet_dir, g, ALIGNED_MARKER))}
    allow_clip = {g for g in set(groups) if os.path.exists(os.path.join(pet_dir, g, CLIP_MARKER))}
    for p, img in zip(paths, normalize_frames(frames, mode=mode, groups=groups, aligned=aligned, allow_clip=allow_clip)):
        out_path = os.path.splitext(p)[0] + ".png"
        img.save(out_path, "PNG", optimize=True)
    return len(paths)
