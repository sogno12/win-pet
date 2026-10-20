"""스프라이트 시트(크로마키 배경 위에 캐릭터 N x M 배치)를 프레임별 이미지로 분리

고정 격자로 자르면 행 간격이 좁을 때 머리카락/발이 잘리므로,
배경색만 있는 '빈 띠'를 찾아 그 사이로 자른다.
  1) 시트 전체에서 세로 빈 띠 → 열(column) 범위
  2) 각 열 안에서 가로 빈 띠 → 행(row) 범위 (펫마다 위아래 위치가 달라도 OK)
  3) 기대 개수보다 많이 쪼개지면(떨어진 반짝이 등) 가장 작은 조각을 이웃에 병합
"""
from PIL import Image

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None


def _bg_mask(arr, tol=90):
    """배경(마젠타 계열 + 이미 투명)이면 True"""
    r, g, b, a = (arr[..., i].astype(int) for i in range(4))
    magenta = (r - g > tol) & (b - g > tol) & (abs(r - b) < 80)
    return magenta | (a == 0)


def _segments(occupied_1d, min_gap):
    """True(내용 있음) 구간들을 [start, end) 리스트로. min_gap 미만의 빈틈은 이어붙임"""
    segs, start, gap = [], None, 0
    for i, v in enumerate(occupied_1d):
        if v:
            if start is None:
                start = i
            gap = 0
            end = i + 1
        elif start is not None:
            gap += 1
            if gap >= min_gap:
                segs.append([start, end])
                start = None
    if start is not None:
        segs.append([start, end])
    return segs


def _merge_to(segs, want):
    """조각이 want개보다 많으면 가장 작은 조각을 가까운 이웃과 합침"""
    segs = [list(s) for s in segs]
    while len(segs) > want:
        i = min(range(len(segs)), key=lambda k: segs[k][1] - segs[k][0])
        if i == 0:
            j = 1
        elif i == len(segs) - 1:
            j = i - 1
        else:
            j = i - 1 if segs[i][0] - segs[i - 1][1] <= segs[i + 1][0] - segs[i][1] else i + 1
        a, b = sorted((i, j))
        segs[a] = [segs[a][0], segs[b][1]]
        del segs[b]
    return segs


def _clear_watermark(arr, bg):
    """Gemini 워터마크(오른쪽 아래 밝은 별)를 배경 처리: 코너 영역의 밝고 채도 낮은 픽셀만"""
    h, w = bg.shape
    y0, x0 = int(h * 0.90), int(w * 0.93)
    rgb = arr[y0:, x0:, :3].astype(int)
    bright = (rgb.min(axis=-1) > 150)
    bg[y0:, x0:] |= bright


def split_sheet(img, cols, rows, min_gap=6, min_pixels=50):
    """시트를 행 우선 순서(왼→오, 위→아래)의 프레임 리스트로 반환 (배경은 투명 처리됨)"""
    if np is None:
        raise RuntimeError("numpy가 필요합니다: pip install numpy")
    arr = np.array(img.convert("RGBA"))
    bg = _bg_mask(arr)
    _clear_watermark(arr, bg)
    arr[..., 3][bg] = 0
    occ = ~bg

    col_occ = occ.sum(axis=0) >= 1
    col_segs = _segments(col_occ, min_gap)
    col_segs = [s for s in col_segs if occ[:, s[0]:s[1]].sum() >= min_pixels]
    if len(col_segs) < cols:
        raise ValueError(f"열을 {cols}개로 나누지 못했습니다 (찾은 열: {len(col_segs)})")
    col_segs = _merge_to(col_segs, cols)

    grid = [[None] * cols for _ in range(rows)]
    for c, (x0, x1) in enumerate(col_segs):
        strip = occ[:, x0:x1]
        row_occ = strip.sum(axis=1) >= 1
        row_segs = [s for s in _segments(row_occ, min_gap) if strip[s[0]:s[1]].sum() >= min_pixels]
        if len(row_segs) < rows:
            raise ValueError(f"{c + 1}번째 열을 {rows}행으로 나누지 못했습니다 (찾은 행: {len(row_segs)})")
        row_segs = _merge_to(row_segs, rows)
        for r, (y0, y1) in enumerate(row_segs):
            grid[r][c] = Image.fromarray(arr[y0:y1, x0:x1].copy(), "RGBA")
    return [grid[r][c] for r in range(rows) for c in range(cols)]
