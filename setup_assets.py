import os
from PIL import Image

def slice_grid_sprite_sheet(image_path, output_dir, rows=2, cols=2):
    if not os.path.exists(image_path):
        print(f"[ERR] Image file missing: {image_path}")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    img = Image.open(image_path).convert("RGBA")
    
    datas = img.getdata()
    new_data = []
    for item in datas:
        if item[0] > 220 and item[1] > 220 and item[2] > 220:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    
    w, h = img.size
    frame_w = w // cols
    frame_h = h // rows
    
    idx = 0
    for r in range(rows):
        for c in range(cols):
            box = (c * frame_w, r * frame_h, (c + 1) * frame_w, (r + 1) * frame_h)
            frame = img.crop(box)
            frame_path = os.path.join(output_dir, f"frame_{idx}.png")
            frame.save(frame_path, "PNG")
            print(f"[OK] Owl frame saved: {frame_path}")
            idx += 1

def slice_linear_sprite_sheet(image_path, output_dir, num_frames=4):
    if not os.path.exists(image_path):
        return
    os.makedirs(output_dir, exist_ok=True)
    img = Image.open(image_path).convert("RGBA")
    
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
    
    for i in range(num_frames):
        box = (i * frame_w, 0, (i + 1) * frame_w, h)
        frame = img.crop(box)
        frame_path = os.path.join(output_dir, f"frame_{i}.png")
        frame.save(frame_path, "PNG")
        print(f"[OK] Cat frame saved: {frame_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    
    generated_cat = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\pixel_cat_1787120321696.jpg"
    cat_dir = os.path.join(base_dir, "assets", "cat_cheese")
    slice_linear_sprite_sheet(generated_cat, cat_dir, 4)
    
    generated_owl = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\pixel_owl_1787124091067.jpg"
    owl_dir = os.path.join(base_dir, "assets", "owl_white")
    slice_grid_sprite_sheet(generated_owl, owl_dir, 2, 2)
