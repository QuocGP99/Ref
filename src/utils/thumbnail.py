import os
import hashlib
from PIL import Image, ImageOps
from ..backend.project_manager import get_current_project_path  # ✅ cần hàm này

def get_thumbnail(photo_id: int, file_path: str) -> str:
    """
    Tạo thumbnail từ ảnh gốc, lưu trong thư mục metadata của project.
    """
    # ✅ Lấy đường dẫn thư mục project hiện tại
    project_root = get_current_project_path()
    meta_dir = os.path.join(project_root, ".metadata", "thumbnails")
    os.makedirs(meta_dir, exist_ok=True)

    # ✅ Hash theo file_path để tránh trùng
    hash_name = hashlib.md5(file_path.encode("utf-8")).hexdigest()
    thumb_path = os.path.join(meta_dir, f"{photo_id}_{hash_name}.jpg")

    # Nếu đã có thumbnail thì trả về luôn
    if os.path.exists(thumb_path):
        return thumb_path

    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        img = Image.open(file_path)
        img = ImageOps.exif_transpose(img)  # Giữ đúng orientation
        img = img.convert("RGB")
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        img.save(thumb_path, "JPEG", quality=85)
        print(f"[THUMB] Created: {thumb_path}")
    except Exception as e:
        print(f"[THUMB ERROR] {file_path}: {e}")
        return file_path

    return thumb_path
