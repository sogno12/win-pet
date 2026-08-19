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

def make_square_tight_crop(img, padding=4):
    bbox = img.getbbox()
    if not bbox:
        return img
    cropped = img.crop(bbox)
    cw, ch = cropped.size
    max_dim = max(cw, ch) + (padding * 2)
    square_img = Image.new("RGBA", (max_dim, max_dim), (255, 255, 255, 0))
    offset_x = (max_dim - cw) // 2
    offset_y = (max_dim - ch) // 2
    square_img.paste(cropped, (offset_x, offset_y))
    return square_img

def update_idle_front_assets():
    base_dir = os.path.dirname(__file__)
    assets_dir = os.path.join(base_dir, "assets")
    
    # 1. 🐱 치즈고양이 정면 멍때리기 (idle/idle_0.png)
    cat_idle_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\cat_idle_front_1787126931936.jpg"
    cat_idle_dir = os.path.join(assets_dir, "cat_cheese", "idle")
    os.makedirs(cat_idle_dir, exist_ok=True)
    if os.path.exists(cat_idle_path):
        c_img = Image.open(cat_idle_path).convert("RGBA")
        datas = c_img.get_flattened_data() if hasattr(c_img, 'get_flattened_data') else c_img.getdata()
        new_data = []
        for item in datas:
            if item[0] > 210 and item[1] > 210 and item[2] > 210:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        c_img.putdata(new_data)
        idle_frame = make_square_tight_crop(c_img)
        idle_frame.save(os.path.join(cat_idle_dir, "idle_0.png"), "PNG")
        print("[OK] Front-facing cat idle image updated!")

    # 2. 🦉 헤드위그 부엉이 정면 멍때리기 (idle/idle_0.png)
    owl_idle_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\owl_idle_front_1787126948499.jpg"
    owl_idle_dir = os.path.join(assets_dir, "owl_white", "idle")
    os.makedirs(owl_idle_dir, exist_ok=True)
    if os.path.exists(owl_idle_path):
        o_img = remove_magenta_bg(Image.open(owl_idle_path))
        owl_idle_frame = make_square_tight_crop(o_img)
        owl_idle_frame.save(os.path.join(owl_idle_dir, "idle_0.png"), "PNG")
        print("[OK] Front-facing owl idle image updated!")

if __name__ == "__main__":
    update_idle_front_assets()
