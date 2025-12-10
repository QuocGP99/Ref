# src/backend/db.py
import sqlite3

DB_PATH = None   # GLOBAL DB path


# ---------------------------------------------------------
# DB PATH
# ---------------------------------------------------------
def set_db_path(path: str):
    global DB_PATH
    DB_PATH = path
    print("DB PATH SET TO:", DB_PATH)


def get_conn():
    if DB_PATH is None:
        raise Exception("DB_PATH chưa được set từ project_manager!")
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------
# LOAD PHOTOS
# ---------------------------------------------------------
def get_photos_by_folder(folder_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, file_path
        FROM photos
        WHERE folder_id=? AND deleted=0
        ORDER BY id DESC
    """, (folder_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_photos():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, file_path
        FROM photos
        WHERE deleted=0
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------
# FAVORITE
# ---------------------------------------------------------
def toggle_favorite(photo_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE photos
        SET favorite = CASE favorite WHEN 1 THEN 0 ELSE 1 END
        WHERE id = ?
    """, (photo_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# DELETE (SOFT)
# ---------------------------------------------------------
def soft_delete(photo_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE photos SET deleted=1 WHERE id=?", (photo_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# RESTORE
# ---------------------------------------------------------
def restore_photo(photo_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE photos SET deleted=0 WHERE id=?", (photo_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# DELETE PERMANENT
# ---------------------------------------------------------
def delete_permanently(photo_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM photos WHERE id=?", (photo_id,))
    cur.execute("DELETE FROM photo_metadata WHERE photo_id=?", (photo_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# MOVE PHOTO TO ANOTHER FOLDER
# ---------------------------------------------------------
def assign_photo_folder(photo_id, folder_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE photos SET folder_id=? WHERE id=?
    """, (folder_id, photo_id))
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# GET META FOR VIEWER
# ---------------------------------------------------------
def get_photo_meta(photo_id: int):
    """
    Trả về dict EXIF đơn giản cho viewer:
    {iso, focal, aperture, shutter}
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT exif_iso, exif_focal_length, exif_aperture, exif_shutter_speed
        FROM photo_metadata
        WHERE photo_id=?
    """, (photo_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return {}

    iso, focal, aperture, shutter = row
    return {
        "iso": iso,
        "focal": focal,
        "aperture": aperture,
        "shutter": shutter,
    }


# ---------------------------------------------------------
# SEARCH (EXIF ONLY — FILTER CƠ BẢN)
# ---------------------------------------------------------
def search_photos(keyword="", lens="", focal="", style="", lighting="", tags=""):
    """
    Tạm thời chỉ filter:
    - keyword trong file_path
    - focal_length (EXIF)
    Các field khác chưa có trong DB → bỏ qua.
    """
    conn = get_conn()
    cur = conn.cursor()

    query = """
        SELECT p.id, p.file_path
        FROM photos p
        LEFT JOIN photo_metadata m ON p.id = m.photo_id
        WHERE p.deleted = 0
    """

    params = []

    # Search theo tên file
    if keyword:
        query += " AND p.file_path LIKE ?"
        params.append(f"%{keyword}%")

    # Filter focal_length
    if focal:
        query += " AND m.exif_focal_length = ?"
        params.append(float(focal))

    query += " ORDER BY p.created_at DESC"

    cur.execute(query, params)
    rows = cur.fetchall()

    conn.close()
    return rows


# ---------------------------------------------------------
# INIT DB
# ---------------------------------------------------------
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # folders table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS folders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            path TEXT
        )
    """)

    # photos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS photos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            source TEXT,
            created_at TEXT,
            folder_id INTEGER,
            favorite INTEGER DEFAULT 0,
            deleted INTEGER DEFAULT 0
        )
    """)

    # photo metadata
    cur.execute("""
        CREATE TABLE IF NOT EXISTS photo_metadata(
            photo_id INTEGER UNIQUE,
            exif_iso INTEGER,
            exif_focal_length REAL,
            exif_aperture REAL,
            exif_shutter_speed REAL
        )
    """)

    conn.commit()
    conn.close()
