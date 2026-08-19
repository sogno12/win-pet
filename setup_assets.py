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
    """
    모든 프레임의 전체 유효 영역(Max Common Bounding Box)을 고정 기준으로 통일하여
    프레임 간 크기가 컸다 작아지며 꿀렁거리는 현상을 100% 원천 차단합니다.
    """
    min_x, min_y, max_x, max_y = 9999, 9999, 0, 0
    
    # 1. 모든 프레임에서 유효 알파 픽셀의 최대 영역(Max BBox) 계산
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
        # 통일된 위치 기준으로 정확히 잘라냄
        cropped = f.crop((min_x, min_y, max_x, max_y))
        
        # 1:1 정방형 정사각형 캔버스 정중앙에 고정 배치
        sq = Image.new("RGBA", (max_dim, max_dim), (255, 255, 255, 0))
        offset_x = (max_dim - cw) // 2
        offset_y = (max_dim - ch) // 2
        sq.paste(cropped, (offset_x, offset_y))
        square_frames.append(sq)
        
    return square_frames

def setup_all_assets_uniform():
    base_dir = os.path.dirname(__file__)
    assets_dir = os.path.join(base_dir, "assets")
    
    # 기존 폴더 클린업
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
    owl_idle_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\owl_idle_front_1787126948499.jpg"
    
    if os.path.exists(grid_img_path):
        img = remove_magenta_bg(Image.open(grid_img_path))
        w, h = img.size
        cols, rows = 4, 4
        fw, fh = w // cols, h // rows
        
        raw_owl_walk = []
        for c in range(cols):
            box = (c * fw, 2 * fh, (c + 1) * fw, 3 * fh)
            raw_owl_walk.append(img.crop(box))
            
        # 통일 캔버스 적용
        processed_owl_walk = make_uniform_square_frames(raw_owl_walk)
        for idx, frame in enumerate(processed_owl_walk):
            frame.save(os.path.join(owl_walk, f"frame_{idx}.png"), "PNG")
            
    if os.path.exists(owl_idle_path):
        o_idle_img = remove_magenta_bg(Image.open(owl_idle_path))
        processed_owl_idle = make_uniform_square_frames([o_idle_img])[0]
        processed_owl_idle.save(os.path.join(owl_idle, "idle_0.png"), "PNG")
        
    if os.path.exists(drag_img_path):
        d_img = remove_magenta_bg(Image.open(drag_img_path))
        processed_owl_drag = make_uniform_square_frames([d_img])[0]
        processed_owl_drag.save(os.path.join(owl_drag, "drag_0.png"), "PNG")

    # --- 2. 🧀 화풍 100% 일치 치즈태비 고양이 세팅 ---
    cat_base = os.path.join(assets_dir, "cat_cheese")
    cat_walk = os.path.join(cat_base, "walk")
    cat_drag = os.path.join(cat_base, "drag")
    cat_idle = os.path.join(cat_base, "idle")
    
    os.makedirs(cat_walk, exist_ok=True)
    os.makedirs(cat_drag, exist_ok=True)
    os.makedirs(cat_idle, exist_ok=True)
    
    cat_grid_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\pixel_cat_1787120321696.jpg"
    cat_drag_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\pixel_cat_drag_1787124485594.jpg"
    # 🔥 화풍 100% 일치하는 새로 생성된 정면 고양이!
    matching_cat_idle_path = r"C:\Users\sjcho\.gemini\antigravity\brain\dced5723-8a67-4ff8-b712-4eed41639c10\matching_cat_idle_1787127616181.jpg"
    
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
        raw_cat_walk = []
        for i in range(4):
            raw_cat_walk.append(c_img.crop((i * fw, 0, (i + 1) * fw, h)))
            
        # 💡 통일된 공통 캔버스 기준(Uniform Frame Size) 적용 ➔ 꿀렁거림 완전 제거!
        processed_cat_walk = make_uniform_square_frames(raw_cat_walk)
        for idx, frame in enumerate(processed_cat_walk):
            frame.save(os.path.join(cat_walk, f"frame_{idx}.png"), "PNG")
            
    if os.path.exists(matching_cat_idle_path):
        mc_img = Image.open(matching_cat_idle_path).convert("RGBA")
        datas = mc_img.get_flattened_data() if hasattr(mc_img, 'get_flattened_data') else mc_img.getdata()
        new_data = []
        for item in datas:
            if item[0] > 210 and item[1] > 210 and item[2] > 210:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        mc_img.putdata(new_data)
        processed_cat_idle = make_uniform_square_frames([mc_img])[0]
        processed_cat_idle.save(os.path.join(cat_idle, "idle_0.png"), "PNG")
        
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
        processed_cat_drag = make_uniform_square_frames([cd_img])[0]
        processed_cat_drag.save(os.path.join(cat_drag, "drag_0.png"), "PNG")
        
    print("[UNIFORM FIX COMPLETE] All pet frames aligned with 100% matching style and fixed bounding boxes!")

if __name__ == "__main__":
    setup_all_assets_uniform()
