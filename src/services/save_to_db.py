from ..backend.db import get_conn

def save_photo(file_path, source, created_at, exif_iso, exif_focal_length, exif_aperture, exif_shutter_speed):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO photos (file_path, source, created_at)
    VALUES (?, ?, ?)
    """, (file_path, source, created_at))
    photo_id = cur.lastrowid

    cur.execute("""
    INSERT INTO photo_metadata (photo_id, exif_iso, exif_focal_length, exif_aperture, exif_shutter_speed)
    VALUES (?, ?, ?, ?, ?)
    """, (photo_id, exif_iso, exif_focal_length, exif_aperture, exif_shutter_speed))

    conn.commit()