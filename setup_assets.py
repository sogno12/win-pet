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

def clean_and_setup_all_assets():
    base_dir = os.path.dirname(__file__)
    assets_dir = os.path.join(base_dir, "assets")
    
    # 🧹 구버전 1:4 길쭉한 파일 싹 청소!
    for pet in ["cat_cheese", "owl_white"]:
        p_dir = os.path.join(assets_dir, pet)
        if os.path.exists(p_dir):
            shutil.rmtree(p_dir)
            
    # --- 1. 🦉 복슬복슬 헤드위그 하얀 부엉이 세팅 ---
    owl_base = os.path.join(assets_dir, "owl_white")
    owl_walk = os.path.join(owl_base, "walk")
    owl_drag = os.path.join(owl_base, "drag")
    owl_idle = os.path.join(owl_base, "idle")
    
    os.makedirs(owl_walk, exist_ok=True)
    os.makedirs(owl_drag, exist_ok=True)
    os.makedirs(owl_idle, exist_ok=True)
    
    grid_img_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\cute_hedwig_owl_1787124649534.jpg"
    drag_img_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\cute_hedwig_owl_drag_1787124666832.jpg"
    
    if os.path.exists(grid_img_path):
        img = remove_magenta_bg(Image.open(grid_img_path))
        w, h = img.size
        cols, rows = 4, 4
        fw, fh = w // cols, h // rows
        
        for c in range(cols):
            box = (c * fw, 2 * fh, (c + 1) * fw, 3 * fh)
            frame = make_square_tight_crop(img.crop(box))
            frame.save(os.path.join(owl_walk, f"frame_{c}.png"), "PNG")
            
        idle_frame = make_square_tight_crop(img.crop((0, 0, fw, fh)))
        idle_frame.save(os.path.join(owl_idle, "idle_0.png"), "PNG")
        
    if os.path.exists(drag_img_path):
        d_img = make_square_tight_crop(remove_magenta_bg(Image.open(drag_img_path)))
        d_img.save(os.path.join(owl_drag, "drag_0.png"), "PNG")

    # --- 2. 🧀 치즈태비 고양이 세팅 ---
    cat_base = os.path.join(assets_dir, "cat_cheese")
    cat_walk = os.path.join(cat_base, "walk")
    cat_drag = os.path.join(cat_base, "drag")
    cat_idle = os.path.join(cat_base, "idle")
    
    os.makedirs(cat_walk, exist_ok=True)
    os.makedirs(cat_drag, exist_ok=True)
    os.makedirs(cat_idle, exist_ok=True)
    
    cat_grid_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\pixel_cat_1787120321696.jpg"
    cat_drag_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\pixel_cat_drag_1787124485594.jpg"
    
    if os.path.exists(cat_grid_path):
        c_img = Image.open(cat_grid_path).convert("RGBA")
        datas = c_img.get_flattened_data() if hasattr(c_img, 'get_flattened_data') else c_img.getdata()
        new_data = []
        for item in datas:
            if item[0] > 210 and item[1] > 210 and item[2] > 210:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        c_img.putdata(new_data)
        
        w, h = c_img.size
        fw = w // 4
        for i in range(4):
            raw_frame = c_img.crop((i * fw, 0, (i + 1) * fw, h))
            frame = make_square_tight_crop(raw_frame)
            frame.save(os.path.join(cat_walk, f"frame_{i}.png"), "PNG")
            
        idle_frame = make_square_tight_crop(c_img.crop((0, 0, fw, h)))
        idle_frame.save(os.path.join(cat_idle, "idle_0.png"), "PNG")
        
    if os.path.exists(cat_drag_path):
        cd_img = Image.open(cat_drag_path).convert("RGBA")
        datas = cd_img.get_flattened_data() if hasattr(cd_img, 'get_flattened_data') else cd_img.getdata()
        new_data = []
        for item in datas:
            if item[0] > 210 and item[1] > 210 and item[2] > 210:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        cd_img.putdata(new_data)
        cd_frame = make_square_tight_crop(cd_img)
        cd_frame.save(os.path.join(cat_drag, "drag_0.png"), "PNG")
        
    print("[CLEAN COMPLETE] Regenerated all pet assets into perfect 1:1 square canvas!")

if __name__ == "__main__":
    clean_and_setup_all_assets()
