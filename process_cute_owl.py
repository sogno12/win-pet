import os
import shutil
from PIL import Image

def is_magenta_bg(r, g, b):
    # 마젠타 핑크 (#FF00FF) 배경 판별
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

def arrange_cute_owl_assets():
    base_dir = os.path.dirname(__file__)
    owl_base = os.path.join(base_dir, "assets", "owl_white")
    
    walk_dir = os.path.join(owl_base, "walk")
    drag_dir = os.path.join(owl_base, "drag")
    idle_dir = os.path.join(owl_base, "idle")
    
    os.makedirs(walk_dir, exist_ok=True)
    os.makedirs(drag_dir, exist_ok=True)
    os.makedirs(idle_dir, exist_ok=True)
    
    grid_img_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\cute_hedwig_owl_1787124649534.jpg"
    drag_img_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\cute_hedwig_owl_drag_1787124666832.jpg"
    
    # 1. 걷기/날기 (walk_0.png ~ walk_3.png)
    if os.path.exists(grid_img_path):
        img = remove_magenta_bg(Image.open(grid_img_path))
        w, h = img.size
        cols, rows = 4, 4
        fw, fh = w // cols, h // rows
        
        # 3번째 줄 4개 파닥이는 귀여운 프레임
        for c in range(cols):
            box = (c * fw, 2 * fh, (c + 1) * fw, 3 * fh)
            frame = img.crop(box)
            frame.save(os.path.join(walk_dir, f"walk_{c}.png"), "PNG")
            
        # 1번째 줄 1번 프레임 -> idle (정면 멍때리기)
        idle_frame = img.crop((0, 0, fw, fh))
        idle_frame.save(os.path.join(idle_dir, "idle_0.png"), "PNG")
        
    # 2. 잡힘 (drag_0.png)
    if os.path.exists(drag_img_path):
        d_img = remove_magenta_bg(Image.open(drag_img_path))
        d_img.save(os.path.join(drag_dir, "drag_0.png"), "PNG")
        
    print("[OK] All cute Hedwig owl assets arranged into standard folders!")

if __name__ == "__main__":
    arrange_cute_owl_assets()
