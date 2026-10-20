"""그린스크린 동영상에서 애니메이션 프레임 추출

AI 동영상(제자리 걷기 등)에서
  1) 초록 배경 투명화 + 테두리 초록 번짐(spill) 제거
  2) 전체 프레임 공통 영역으로 크롭 (프레임 간 위치 관계 유지)
  3) 반복 동작이면 한 주기를 자동 탐지해 N장 균등 추출, 아니면 구간에서 N장 균등 추출
한다. 결과는 normalize_pet_dir 로 크기 맞춤까지 하면 된다.

필요: opencv-python (pip install opencv-python) 또는 PATH 상의 ffmpeg
"""
import os
import glob
import shutil
import subprocess
import tempfile

import numpy as np
from PIL import Image

WATERMARK_CORNER = 0.85  # 오른쪽 아래 15% 영역의 워터마크(별)는 무시


def read_video_frames(path):
    """동영상을 RGB numpy 프레임 리스트와 fps로 반환"""
    try:
        import cv2
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 24
        frames = []
        while True:
            ok, bgr = cap.read()
            if not ok:
                break
            frames.append(bgr[..., ::-1].copy())
        cap.release()
        if frames:
            return frames, fps
    except ImportError:
        pass

    if not shutil.which("ffmpeg"):
        raise RuntimeError("동영상을 읽으려면 'pip install opencv-python' 또는 ffmpeg 설치가 필요합니다.")
    tmp = tempfile.mkdtemp(prefix="winpet_vid_")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-i", path, os.path.join(tmp, "f_%04d.png")], check=True)
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=r_frame_rate", "-of", "csv=p=0", path], capture_output=True, text=True)
        num, _, den = out.stdout.strip().partition("/")
        fps = float(num) / float(den or 1) if num else 24
        frames = [np.asarray(Image.open(f).convert("RGB")) for f in sorted(glob.glob(os.path.join(tmp, "f_*.png")))]
        return frames, fps
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def green_mask(rgb):
    """초록 배경이면 True"""
    r, g, b = (rgb[..., i].astype(np.int16) for i in range(3))
    return (g > 120) & (g - np.maximum(r, b) > 50)


def key_frame(rgb, box):
    """box 영역을 잘라 초록 배경 투명화 + spill 제거한 RGBA 이미지"""
    x0, y0, x1, y1 = box
    a = rgb[y0:y1, x0:x1].astype(np.int16)
    bg = green_mask(a)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    g = np.minimum(g, np.maximum(r, b) + 10)  # 경계의 초록빛 제거
    alpha = np.where(bg, 0, 255)
    out = np.stack([r, g, b, alpha], axis=-1).clip(0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def _fg_masks(frames):
    masks = []
    for f in frames:
        m = ~green_mask(f)
        h, w = m.shape
        m[int(h * WATERMARK_CORNER):, int(w * WATERMARK_CORNER):] = False
        masks.append(m)
    return masks


def _main_body_bbox(mask):
    """가장 큰 덩어리(캐릭터+손에 든 물건)의 bbox. 떨어진 반짝이/먼지는 제외"""
    try:
        import cv2
        n, _, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
        if n <= 1:
            return None
        i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        x, y, w, h = stats[i, :4]
        return x, y, x + w, y + h
    except ImportError:
        ys, xs = np.nonzero(mask)
        return (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1) if len(xs) else None


def find_cycle(masks, fps, start, min_sec=0.4, max_sec=2.0):
    """start 프레임과 가장 비슷하게 돌아오는 간격(=한 주기 길이)과 유사도"""
    ys, xs = np.nonzero(np.logical_or.reduce(masks))
    y_leg = ys.min() + int((ys.max() - ys.min()) * 0.5)  # 하반신(다리/망토)으로 비교
    crop = lambda m: m[y_leg:ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32)
    ref = crop(masks[start])
    best = (None, -1.0)
    for lag in range(max(2, int(fps * min_sec)), int(fps * max_sec) + 1):
        if start + lag >= len(masks):
            break
        sim = 1 - np.abs(ref - crop(masks[start + lag])).sum() / max(ref.sum(), 1)
        if sim > best[1]:
            best = (lag, sim)
    return best


def extract_frames(video_path, count=8, start_sec=None, end_sec=None, loop=True, pad=8, trim_effects=False):
    """동영상에서 RGBA 프레임 count장을 추출

    loop=True: start_sec 부근에서 반복 주기를 찾아 한 주기를 균등 분할 (걷기 등)
    loop=False: start_sec~end_sec 구간을 균등 분할 (지팡이 휘두르기 등 1회성 동작)
    trim_effects=True: 몇 프레임에만 크게 퍼지는 연기·이펙트는 잘라내고 대부분 프레임 기준으로 영역을 잡음
    """
    frames, fps = read_video_frames(video_path)
    if not frames:
        raise ValueError("동영상에서 프레임을 읽지 못했습니다.")
    masks = _fg_masks(frames)

    # 자를 영역: 프레임별 '몸통 덩어리' bbox의 합집합 (멀리 퍼진 반짝이 때문에 캐릭터가 작아지지 않게)
    boxes = [b for b in (_main_body_bbox(m) for m in masks) if b]
    h, w = masks[0].shape
    if trim_effects:
        lo, hi = (lambda v: float(np.percentile(v, 10))), (lambda v: float(np.percentile(v, 90)))
    else:
        lo, hi = min, max
    box = (max(0, int(lo([b[0] for b in boxes])) - pad), max(0, int(lo([b[1] for b in boxes])) - pad),
           min(w, int(hi([b[2] for b in boxes])) + pad), min(h, int(hi([b[3] for b in boxes])) + pad))

    if loop:
        best_start, best = None, (None, -1.0)
        # 시작 직후는 동작이 덜 붙은 경우가 많아 1초 뒤부터, 여러 시작점 중 가장 깔끔하게 반복되는 주기 선택
        first = int(fps * (start_sec if start_sec is not None else 1.0))
        for s in range(first, min(len(frames) - int(fps * 2), first + int(fps * 4)), max(1, int(fps / 4))):
            lag, sim = find_cycle(masks, fps, s)
            if lag and sim > best[1]:
                best_start, best = s, (lag, sim)
        if best_start is None:
            raise ValueError("반복 주기를 찾지 못했습니다. loop=False로 구간을 지정해 보세요.")
        lag, sim = best
        idx = [best_start + round(k * lag / count) for k in range(count)]
        info = f"주기 {lag}프레임({lag / fps:.2f}초), 시작 {best_start / fps:.2f}초, 반복 일치도 {sim:.2f}"
    else:
        s = int(fps * (start_sec or 0))
        e = min(len(frames) - 1, int(fps * end_sec) if end_sec else len(frames) - 1)
        idx = [round(s + k * (e - s) / max(1, count - 1)) for k in range(count)]
        info = f"{s / fps:.2f}~{e / fps:.2f}초 구간"

    return [key_frame(frames[i], box) for i in idx], info
