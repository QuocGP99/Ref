# src/services/import_service.py
from datetime import datetime
from pathlib import Path
import exifread

from .save_to_db import save_photo

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}


def import_folder(folder_path, folder_id=None):
    folder = Path(folder_path)
    if not folder.exists():
        return

    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            process_photo(file, folder_id)


def process_photo(image_path: Path, folder_id=None):
    iso, focal_length, aperture, shutter_speed = read_exif(image_path)

    save_photo(
        file_path=str(image_path),
        source="local",
        created_at=datetime.now().isoformat(timespec="seconds"),
        exif_iso=iso,
        exif_focal_length=focal_length,
        exif_aperture=aperture,
        exif_shutter_speed=shutter_speed,
        folder_id=folder_id,
    )


def read_exif(image_path: Path):
    """
    Đọc EXIF cơ bản, return (iso, focal, aperture, shutter)
    Nếu thiếu EXIF → trả về None tương ứng.
    """
    try:
        with open(image_path, "rb") as f:
            tags = exifread.process_file(f, details=False)
    except Exception:
        return (None, None, None, None)

    iso = tags.get("EXIF ISOSpeedRatings")
    focal = tags.get("EXIF FocalLength")
    aperture = tags.get("EXIF FNumber")
    shutter = tags.get("EXIF ExposureTime")

    # ---- safe conversion wrappers ----
    def to_int(value):
        try:
            return int(str(value).split()[0])
        except Exception:
            return None

    def to_float(value):
        try:
            s = str(value)

            # dạng rational "18/10"
            if "/" in s:
                num, den = s.split("/")
                return float(num) / float(den)

            # dạng "F/2.8"
            if "F/" in s:
                return float(s.replace("F/", ""))

            return float(s)
        except Exception:
            return None

    return (
        to_int(iso),
        to_int(focal),
        to_float(aperture),
        to_float(shutter),
    )
