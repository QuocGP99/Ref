from datetime import datetime
from ..backend.database_manager import get_session, Photo


def save_photo(
    file_path,
    source,
    created_at,
    exif_iso,
    exif_focal_length,
    exif_aperture,
    exif_shutter_speed,
    folder_id=None,
):
    """
    Lưu thông tin ảnh + EXIF vào MySQL ORM
    """
    session = get_session()

    photo = Photo(
        file_path=file_path,
        source=source,
        folder_id=folder_id,
        date_imported=datetime.now(),
        date_created=datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S"),
        exif_iso=exif_iso,
        exif_focal_length=exif_focal_length,
        exif_aperture=exif_aperture,
        exif_shutter_speed=exif_shutter_speed,
    )

    session.add(photo)
    session.commit()
    print(f"✅ Imported photo: {file_path}")
