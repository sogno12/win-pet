import os
import shutil

base_dir = os.path.dirname(__file__)
old_cat_dir = os.path.join(base_dir, "assets", "cat")
new_cat_dir = os.path.join(base_dir, "assets", "cat_cheese")
owl_dir = os.path.join(base_dir, "assets", "owl_white")

os.makedirs(new_cat_dir, exist_ok=True)
os.makedirs(owl_dir, exist_ok=True)

if os.path.exists(old_cat_dir):
    for f in os.listdir(old_cat_dir):
        shutil.copy(os.path.join(old_cat_dir, f), os.path.join(new_cat_dir, f))
    print("[OK] assets/cat -> assets/cat_cheese migrated successfully.")
