# src/utils/thumbnail.py
import os
from PIL import Image
from ..backend.db import DB_PATH

def get_thumbnail(photo_id: int, file_path: str) -> str:
    """
    Tạo thumbnail dựa trên project_root/.ref/thumbnails/
    Thumbnail = {photo_id}.jpg
    """

    if DB_PATH is None:
        return file_path  # fallback, DB chưa init

    project_root = os.path.dirname(DB_PATH)
    thumb_dir = os.path.join(project_root, "thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)

    thumb_path = os.path.join(thumb_dir, f"{photo_id}.jpg")

    # nếu đã có thumbnail → dùng ngay
    if os.path.exists(thumb_path):
        return thumb_path

    # tạo thumbnail mới
    try:
        img = Image.open(file_path)
        img.thumbnail((400, 400))
        img.save(thumb_path, "JPEG", quality=85)
    except Exception as e:
        print("THUMB ERROR:", e)
        return file_path

    return thumb_path
