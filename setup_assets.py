import os
from PIL import Image, ImageChops

def slice_sprite_sheet(image_path, output_dir, num_frames=4):
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일 없음: {image_path}")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    img = Image.open(image_path).convert("RGBA")
    
    # 1. 흰색/연회색 배경을 투명하게 처리 (Threshold 210)
    datas = img.getdata()
    new_data = []
    for item in datas:
        if item[0] > 210 and item[1] > 210 and item[2] > 210:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    
    w, h = img.size
    frame_w = w // num_frames
    
    # 각 프레임 자르기
    for i in range(num_frames):
        box = (i * frame_w, 0, (i + 1) * frame_w, h)
        frame = img.crop(box)
        
        # 바닥 기준 및 알파 채널 여백 정리
        frame_path = os.path.join(output_dir, f"walk_{i}.png")
        frame.save(frame_path, "PNG")
        print(f"✅ 프레임 저장 완료: {frame_path}")

if __name__ == "__main__":
    generated_img_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\pixel_cat_1787120321696.jpg"
    out_dir = os.path.join(os.path.dirname(__file__), "assets", "cat")
    slice_sprite_sheet(generated_img_path, out_dir, 4)
