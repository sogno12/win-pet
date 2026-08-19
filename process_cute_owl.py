import os
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

def process_cute_owl_frames():
    base_dir = os.path.dirname(__file__)
    owl_out_dir = os.path.join(os.path.dirname(__file__), "assets", "owl_white")
    os.makedirs(owl_out_dir, exist_ok=True)
    
    # 1. 걷기/날개 파닥이는 4개 프레임 분할
    grid_img_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\cute_hedwig_owl_1787124649534.jpg"
    if os.path.exists(grid_img_path):
        img = Image.open(grid_img_path)
        img_no_bg = remove_magenta_bg(img)
        
        w, h = img_no_bg.size
        cols, rows = 4, 4
        fw, fh = w // cols, h // rows
        
        for c in range(cols):
            box = (c * fw, 2 * fh, (c + 1) * fw, 3 * fh)
            frame = img_no_bg.crop(box)
            out_path = os.path.join(owl_out_dir, f"frame_{c}.png")
            frame.save(out_path, "PNG")
            print(f"[OK] Cute Owl walk frame saved: {out_path}")
            
    # 2. 잡힌 드래그 프레임 (drag.png)
    drag_img_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\cute_hedwig_owl_drag_1787124666832.jpg"
    if os.path.exists(drag_img_path):
        d_img = Image.open(drag_img_path)
        d_no_bg = remove_magenta_bg(d_img)
        out_drag_path = os.path.join(owl_out_dir, "drag.png")
        d_no_bg.save(out_drag_path, "PNG")
        print(f"[OK] Cute Owl drag frame saved: {out_drag_path}")

if __name__ == "__main__":
    process_cute_owl_frames()
