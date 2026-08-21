import os
import sys
import argparse
from PIL import Image

def is_magenta_background(r, g, b):
    """배경 마젠타 색상인지 판별 (#FF00FF 부근)"""
    return r > 180 and g < 130 and b > 160

def is_skin_pixel(r, g, b):
    """캐릭터 피부(얼굴, 손 등) 영역 픽셀인지 판별"""
    if is_magenta_background(r, g, b):
        return False
    # 검은 머리카락/옷/음영 제외
    if r < 140 or g < 90 or b < 80:
        return False
    # 피부색 특성: 밝고 R이 가장 높음
    if r >= g and g >= b * 0.5 and (r - b) >= 5:
        return True
    return False

def get_mean_skin_color(img: Image.Image):
    """이미지에서 피부 영역의 평균 RGB 색상 추출"""
    pixels = list(img.convert("RGBA").getdata())
    skin_r, skin_g, skin_b = [], [], []
    for r, g, b, a in pixels:
        if a > 50 and is_skin_pixel(r, g, b):
            skin_r.append(r)
            skin_g.append(g)
            skin_b.append(b)

    if not skin_r:
        return None

    return (
        sum(skin_r) / len(skin_r),
        sum(skin_g) / len(skin_g),
        sum(skin_b) / len(skin_b)
    )

def calibrate_single_image(ref_mean_rgb: tuple, target_img_path: str, output_path: str, factor: float = 1.0) -> bool:
    """기준 피부색 평균을 바탕으로 대상 이미지의 피부 붉은기/자줏빛을 역보정"""
    if not os.path.exists(target_img_path):
        return False

    tgt_img = Image.open(target_img_path).convert("RGBA")
    tgt_mean = get_mean_skin_color(tgt_img)

    if not tgt_mean:
        tgt_img.save(output_path)
        return True

    # 델타 오차 계산 (타겟 - 기준)
    diff_r = int((tgt_mean[0] - ref_mean_rgb[0]) * factor)
    diff_g = int((tgt_mean[1] - ref_mean_rgb[1]) * factor)
    diff_b = int((tgt_mean[2] - ref_mean_rgb[2]) * factor)

    tgt_pixels = list(tgt_img.getdata())
    new_pixels = []
    for r, g, b, a in tgt_pixels:
        if a > 50 and is_skin_pixel(r, g, b):
            nr = max(0, min(255, r - diff_r))
            ng = max(0, min(255, g - diff_g))
            nb = max(0, min(255, b - diff_b))
            new_pixels.append((nr, ng, nb, a))
        else:
            new_pixels.append((r, g, b, a))

    res_img = Image.new("RGBA", tgt_img.size)
    res_img.putdata(new_pixels)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    res_img.save(output_path)
    return True

def calibrate_folder(ref_img_path: str, input_folder: str, output_folder: str = None, factor: float = 1.0):
    """기준 이미지 1장으로 특정 폴더 안의 모든 프레임 이미지를 일괄 피부색 캘리브레이션"""
    ref_img = Image.open(ref_img_path).convert("RGBA")
    ref_mean = get_mean_skin_color(ref_img)

    if not ref_mean:
        print("[Error] 기준 이미지에서 피부색을 감지하지 못했습니다.")
        return

    print(f"[*] 기준 이미지 피부 평균 RGB: R={ref_mean[0]:.1f}, G={ref_mean[1]:.1f}, B={ref_mean[2]:.1f}")

    if output_folder is None:
        output_folder = input_folder

    valid_exts = (".png", ".jpg", ".jpeg", ".bmp")
    files = [f for f in os.listdir(input_folder) if f.lower().endswith(valid_exts)]
    
    success_count = 0
    for fname in files:
        in_path = os.path.join(input_folder, fname)
        out_path = os.path.join(output_folder, fname)
        if calibrate_single_image(ref_mean, in_path, out_path, factor):
            print(f"  -> 보정 완료: {fname}")
            success_count += 1

    print(f"[*] 총 {success_count}개 이미지 피부색 보정 완료! ({output_folder})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 생성 픽셀 캐릭터 피부색 붉은기/자줏빛 일괄 보정 도구")
    parser.add_argument("--ref", required=True, help="기준이 되는 1번 원본 이미지 경로 (깨끗한 피부색)")
    parser.add_argument("--target", help="보정할 단일 대상 이미지 경로")
    parser.add_argument("--folder", help="일괄 보정할 이미지 폴더 경로")
    parser.add_argument("--out", help="출력 파일 또는 폴더 경로 (생략 시 덮어쓰기 또는 기본 경로)")
    parser.add_argument("--factor", type=float, default=1.0, help="보정 강도 (기본 1.0)")

    args = parser.parse_args()

    if args.target:
        ref_img = Image.open(args.ref).convert("RGBA")
        ref_mean = get_mean_skin_color(ref_img)
        out_file = args.out or args.target
        calibrate_single_image(ref_mean, args.target, out_file, args.factor)
        print(f"[Done] {out_file} 보정 완료!")
    elif args.folder:
        calibrate_folder(args.ref, args.folder, args.out, args.factor)
    else:
        print("사용법: python tools/skin_calibrator.py --ref 기준이미지.png --target 대상이미지.png --out 결과.png")
        print("또는: python tools/skin_calibrator.py --ref 기준이미지.png --folder assets/my_char/walk/ --out assets/my_char/walk/")
