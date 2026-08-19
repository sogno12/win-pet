import os
from PIL import Image

def process_single_drag_image(image_path, output_path):
    if not os.path.exists(image_path):
        print(f"[ERR] File missing: {image_path}")
        return
        
    img = Image.open(image_path).convert("RGBA")
    datas = img.getdata()
    new_data = []
    for item in datas:
        if item[0] > 220 and item[1] > 220 and item[2] > 220:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"[OK] Saved drag image: {output_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    
    # 1. 고양이 잡힌 이미지
    cat_drag_img = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\pixel_cat_drag_1787124485594.jpg"
    cat_drag_out = os.path.join(base_dir, "assets", "cat_cheese", "drag.png")
    process_single_drag_image(cat_drag_img, cat_drag_out)
    
    # 2. 부엉이 잡힌 이미지
    owl_drag_img = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\pixel_owl_drag_1787124592985.jpg"
    owl_drag_out = os.path.join(base_dir, "assets", "owl_white", "drag.png")
    process_single_drag_image(owl_drag_img, owl_drag_out)
