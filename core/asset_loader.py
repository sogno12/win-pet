import os
import re
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QTransform
from core.config_manager import BASE_DIR

def natural_key(name):
    """frame_2.png 가 frame_10.png 보다 앞에 오도록 숫자를 숫자로 비교"""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


class AssetLoader:
    """펫 에셋(walk, idle, drag, happy, special) 전용 로딩 및 캐싱 클래스"""
    
    @staticmethod
    def _load_folder_frames(folder_path, width, height):
        right_list, left_list = [], []
        if os.path.exists(folder_path):
            files = sorted([f for f in os.listdir(folder_path) if f.endswith((".png", ".jpg"))], key=natural_key)
            for f in files:
                pix = QPixmap(os.path.join(folder_path, f))
                if not pix.isNull():
                    scaled_r = pix.scaled(
                        width, height, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    flipped = pix.transformed(QTransform().scale(-1, 1))
                    scaled_l = flipped.scaled(
                        width, height, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    right_list.append(scaled_r)
                    left_list.append(scaled_l)
        return right_list, left_list

    @classmethod
    def load_pet_assets(cls, pet_key, width, height):
        anim_frames = {
            "walk_r": [], "walk_l": [],
            "idle_r": [], "idle_l": [],
            "drag_r": None, "drag_l": None,
            "happy_r": [], "happy_l": [],
            "special_r": [], "special_l": [],
            # 실제 전용 프레임 존재 여부 (없으면 위 리스트는 walk 프레임으로 대체됨)
            "has_happy": False, "has_special": False
        }
        
        pet_dir = os.path.join(BASE_DIR, "assets", pet_key)
        if not os.path.exists(pet_dir):
            pet_dir = os.path.join(BASE_DIR, "assets", "owl_white")

        # (1) walk
        walk_dir = os.path.join(pet_dir, "walk")
        w_r, w_l = cls._load_folder_frames(walk_dir, width, height)
        if not w_r:
            w_r, w_l = cls._load_folder_frames(pet_dir, width, height)
            
        if not w_r:
            fallback = QPixmap(64, 64)
            fallback.fill(Qt.GlobalColor.transparent)
            w_r, w_l = [fallback], [fallback]
            
        anim_frames["walk_r"], anim_frames["walk_l"] = w_r, w_l
        
        # (2) idle
        idle_dir = os.path.join(pet_dir, "idle")
        i_r, i_l = cls._load_folder_frames(idle_dir, width, height)
        anim_frames["idle_r"] = i_r if i_r else w_r
        anim_frames["idle_l"] = i_l if i_l else w_l
        
        # (3) drag
        drag_dir = os.path.join(pet_dir, "drag")
        d_r, d_l = cls._load_folder_frames(drag_dir, width, height)
        if d_r:
            anim_frames["drag_r"], anim_frames["drag_l"] = d_r[0], d_l[0]
        else:
            drag_file = os.path.join(pet_dir, "drag.png")
            if os.path.exists(drag_file):
                pix = QPixmap(drag_file)
                if not pix.isNull():
                    scaled_r = pix.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    scaled_l = pix.transformed(QTransform().scale(-1, 1)).scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    anim_frames["drag_r"], anim_frames["drag_l"] = scaled_r, scaled_l
            if not anim_frames["drag_r"]:
                anim_frames["drag_r"], anim_frames["drag_l"] = w_r[0], w_l[0]
        # 드래그 중 반복 재생용 전체 프레임 (1장뿐이면 그 1장)
        anim_frames["drag_rs"] = d_r or [anim_frames["drag_r"]]
        anim_frames["drag_ls"] = d_l or [anim_frames["drag_l"]]

        # (4) happy
        happy_dir = os.path.join(pet_dir, "happy")
        h_r, h_l = cls._load_folder_frames(happy_dir, width, height)
        anim_frames["happy_r"] = h_r if h_r else w_r
        anim_frames["happy_l"] = h_l if h_l else w_l

        # (5) special: special/ 바로 아래 파일 = 동작 1개, special/<이름>/ 하위 폴더마다 동작 1개씩
        special_dir = os.path.join(pet_dir, "special")
        special_sets = []
        s_r, s_l = cls._load_folder_frames(special_dir, width, height)
        if s_r:
            special_sets.append((s_r, s_l))
        if os.path.isdir(special_dir):
            for sub in sorted(os.listdir(special_dir), key=natural_key):
                sub_r, sub_l = cls._load_folder_frames(os.path.join(special_dir, sub), width, height)
                if sub_r:
                    special_sets.append((sub_r, sub_l))
        anim_frames["special_sets"] = special_sets
        anim_frames["special_r"], anim_frames["special_l"] = special_sets[0] if special_sets else (w_r, w_l)

        # (6) think: 질문 답변을 기다리는 동안
        t_r, t_l = cls._load_folder_frames(os.path.join(pet_dir, "think"), width, height)
        anim_frames["think_r"] = t_r if t_r else anim_frames["idle_r"]
        anim_frames["think_l"] = t_l if t_l else anim_frames["idle_l"]

        anim_frames["has_happy"] = bool(h_r)
        anim_frames["has_special"] = bool(special_sets)
        anim_frames["has_think"] = bool(t_r)

        return anim_frames

    @classmethod
    def get_icon_pixmap(cls, pet_key):
        pet_dir = os.path.join(BASE_DIR, "assets", pet_key)
        idle_dir = os.path.join(pet_dir, "idle")
        if os.path.exists(idle_dir):
            files = sorted([f for f in os.listdir(idle_dir) if f.endswith((".png", ".jpg"))], key=natural_key)
            if files:
                return QPixmap(os.path.join(idle_dir, files[0]))
        walk_dir = os.path.join(pet_dir, "walk")
        if os.path.exists(walk_dir):
            files = sorted([f for f in os.listdir(walk_dir) if f.endswith((".png", ".jpg"))], key=natural_key)
            if files:
                return QPixmap(os.path.join(walk_dir, files[0]))
        fallback = QPixmap(32, 32)
        fallback.fill(Qt.GlobalColor.transparent)
        return fallback
