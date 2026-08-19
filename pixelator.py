"""
pixelator.py - 일반 이미지/사진을 픽셀 아트 PNG로 변환해주는 유틸리티

사용법:
    python pixelator.py --input my_cat.jpg --output assets/custom_cat.png --size 64
"""

import argparse
from PIL import Image

def pixelate_image(input_path: str, output_path: str, pixel_size: int = 64, remove_bg_white: bool = True):
    """
    일반 이미지를 지정된 pixel_size(예: 64x64) 픽셀 아트로 변환합니다.
    """
    img = Image.open(input_path).convert("RGBA")
    
    # 1. 배경이 흰색에 가까우면 투명화 처리 (선택)
    if remove_bg_white:
        datas = img.getdata()
        new_data = []
        for item in datas:
            # R, G, B가 모두 240 이상이면 투명 처리
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        img.putdata(new_data)
        
    # 2. 이미지의 원본 비율 유지하면서 지정 크기 이하로 감축 (Nearest-Neighbor / Box)
    w, h = img.size
    max_dim = max(w, h)
    scale = pixel_size / max_dim
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    
    # 작은 크기로 줄이기 (픽셀화)
    img_small = img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    
    # 도트 느낌을 강조하기 위해 Nearest Neighbor로 다시 키워서 보관할 수 있음
    # 여기서는 원본 픽셀 데이터(new_w, new_h) 자체를 저장합니다.
    img_small.save(output_path, "PNG")
    print(f"✅ 픽셀 변환 완료! 저장된 위치: {output_path} ({new_w}x{new_h} 픽셀)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="일반 이미지를 픽셀 아트로 변환합니다.")
    parser.add_argument("--input", "-i", required=True, help="입력 이미지 경로 (jpg, png 등)")
    parser.add_argument("--output", "-o", default="assets/custom_cat.png", help="출력 PNG 경로")
    parser.add_argument("--size", "-s", type=int, default=64, help="목표 픽셀 크기 (기본값: 64)")
    
    args = parser.parse_args()
    pixelate_image(args.input, args.output, args.size)
