import os
import shutil
from PIL import Image

def is_magenta_bg(r, g, b):
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

def make_uniform_square_frames(frames_list, padding=4):
    min_x, min_y, max_x, max_y = 9999, 9999, 0, 0
    for f in frames_list:
        bbox = f.getbbox()
        if bbox:
            min_x = min(min_x, bbox[0])
            min_y = min(min_y, bbox[1])
            max_x = max(max_x, bbox[2])
            max_y = max(max_y, bbox[3])
            
    if min_x >= max_x or min_y >= max_y:
        return frames_list
        
    cw = max_x - min_x
    ch = max_y - min_y
    max_dim = max(cw, ch) + (padding * 2)
    
    square_frames = []
    for f in frames_list:
        cropped = f.crop((min_x, min_y, max_x, max_y))
        sq = Image.new("RGBA", (max_dim, max_dim), (255, 255, 255, 0))
        offset_x = (max_dim - cw) // 2
        offset_y = (max_dim - ch) // 2
        sq.paste(cropped, (offset_x, offset_y))
        square_frames.append(sq)
        
    return square_frames

def setup_sleek_cat_assets():
    base_dir = os.path.dirname(__file__)
    cat_base = os.path.join(base_dir, "assets", "cat_cheese")
    
    cat_walk = os.path.join(cat_base, "walk")
    cat_drag = os.path.join(cat_base, "drag")
    cat_idle = os.path.join(cat_base, "idle")
    
    if os.path.exists(cat_base):
        shutil.rmtree(cat_base)
        
    os.makedirs(cat_walk, exist_ok=True)
    os.makedirs(cat_drag, exist_ok=True)
    os.makedirs(cat_idle, exist_ok=True)
    
    sheet_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\sleek_cheese_cat_full_1787127979144.jpg"
    drag_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\sleek_cheese_cat_drag_1787127993100.jpg"
    
    if os.path.exists(sheet_path):
        full_img = remove_magenta_bg(Image.open(sheet_path))
        w, h = full_img.size
        
        # 상단 2x2 영역: walk 4프레임
        # 하단 1개 영역: idle 정면 1프레임
        hw, hh = w // 2, h // 3
        
        raw_walk = [
            full_img.crop((0, 0, hw, hh)),
            full_img.crop((hw, 0, w, hh)),
            full_img.crop((0, hh, hw, 2 * hh)),
            full_img.crop((hw, hh, w, 2 * hh))
        ]
        
        raw_idle = [full_img.crop((0, 2 * hh, w, h))]
        
        # 걷기 프레임 통일 캔버스 세팅
        processed_walk = make_uniform_square_frames(raw_walk)
        for idx, frame in enumerate(processed_walk):
            frame.save(os.path.join(cat_walk, f"frame_{idx}.png"), "PNG")
            
        processed_idle = make_uniform_square_frames(raw_idle)[0]
        processed_idle.save(os.path.join(cat_idle, "idle_0.png"), "PNG")
        
    if os.path.exists(drag_path):
        drag_img = remove_magenta_bg(Image.open(drag_path))
        processed_drag = make_uniform_square_frames([drag_img])[0]
        processed_drag.save(os.path.join(cat_drag, "drag_0.png"), "PNG")
        
    print("[SLEEK CAT COMPLETE] Sleek matching cheese cat assets generated and updated!")

if __name__ == "__main__":
    setup_sleek_cat_assets()
