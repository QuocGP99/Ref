# src/services/save_to_db.py
from ..backend.db import get_conn

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
    conn = get_conn()
    cur = conn.cursor()

    # photos
    cur.execute(
        """
        INSERT INTO photos (file_path, source, created_at, folder_id)
        VALUES (?, ?, ?, ?)
        """,
        (file_path, source, created_at, folder_id),
    )
    photo_id = cur.lastrowid

    # metadata
    cur.execute(
        """
        INSERT INTO photo_metadata
            (photo_id, exif_iso, exif_focal_length, exif_aperture, exif_shutter_speed)
        VALUES (?, ?, ?, ?, ?)
        """,
        (photo_id, exif_iso, exif_focal_length, exif_aperture, exif_shutter_speed),
    )

    conn.commit()
    conn.close()
