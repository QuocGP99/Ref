from pathlib import Path
from PIL import Image

THUMB_DIR = Path("data/thumbnails")
THUMB_DIR.mkdir(parents=True, exist_ok=True)


def get_thumbnail(photo_id: int, file_path: str, size: int = 256) -> str:
    """
    Tạo (nếu chưa có) và trả về đường dẫn thumbnail cho ảnh.
    Thumbnail đặt tên theo photo_id để tránh trùng.
    """
    thumb_path = THUMB_DIR / f"{photo_id}_{size}.jpg"

    if not thumb_path.exists():
        try:
            img = Image.open(file_path)
            img = img.convert("RGB")
            img.thumbnail((size, size))
            img.save(thumb_path, "JPEG", quality=85)
        except Exception as e:
            print(f"[thumbnail] Lỗi tạo thumbnail cho {file_path}: {e}")
            # fallback: nếu lỗi, trả về file gốc (Qt sẽ tự scale)
            return file_path

    return str(thumb_path)
