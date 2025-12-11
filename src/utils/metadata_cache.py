import os
import json
from PIL import Image

CACHE_DIR = os.path.join(os.getcwd(), ".cache")
CACHE_FILE = os.path.join(CACHE_DIR, "photo_meta.json")

def load_cache():
    """Đọc cache JSON nếu có."""
    if not os.path.exists(CACHE_FILE):
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_cache(data: dict):
    """Lưu lại cache JSON."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_metadata(file_path: str) -> dict:
    cache = load_cache()
    modified_time = os.path.getmtime(file_path) if os.path.exists(file_path) else 0

    if file_path in cache:
        cached = cache[file_path]
        if abs(cached.get("modified", 0) - modified_time) < 0.01:
            return cached  # Cache còn hợp lệ

    meta = {}
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        img = Image.open(file_path)
        w, h = img.size
        img.close()
        size_kb = os.path.getsize(file_path) / 1024
        created = os.path.getctime(file_path)

        meta = {
            "filename": os.path.basename(file_path),
            "width": w,
            "height": h,
            "size_mb": round(size_kb / 1024, 2),
            "created": created,
            "modified": modified_time,
        }

        cache[file_path] = meta
        save_cache(cache)
    except Exception as e:
        print(f"[META ERROR] {e}")
        meta = {"filename": os.path.basename(file_path), "width": 0, "height": 0, "size_mb": 0}

    return meta
