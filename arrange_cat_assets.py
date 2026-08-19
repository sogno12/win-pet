import os
import shutil

base_dir = os.path.dirname(__file__)
cat_base = os.path.join(base_dir, "assets", "cat_cheese")

walk_dir = os.path.join(cat_base, "walk")
drag_dir = os.path.join(cat_base, "drag")
idle_dir = os.path.join(cat_base, "idle")

os.makedirs(walk_dir, exist_ok=True)
os.makedirs(drag_dir, exist_ok=True)
os.makedirs(idle_dir, exist_ok=True)

# 루트에 있던 이미지 이동
for f in os.listdir(cat_base):
    src = os.path.join(cat_base, f)
    if os.path.isfile(src):
        if f.startswith("frame_") or f.startswith("walk_"):
            shutil.move(src, os.path.join(walk_dir, f))
        elif f == "drag.png":
            shutil.move(src, os.path.join(drag_dir, "drag_0.png"))

print("[OK] All cat_cheese assets arranged into standard folders!")
