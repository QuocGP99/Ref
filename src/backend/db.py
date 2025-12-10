import sqlite3
from pathlib import Path

DB_PATH = Path("data/ref.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_favorite TEXT DEFAULT 0,
                is_trashed TEXT DEFAULT 0
                )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS photo_metadata (
               photo_id INTEGER,
               category TEXT,
               lens TEXT,
               style TEXT,
               lighting TEXT,
               tags TEXT,
               notes TEXT,
               exif_iso INTEGER,
               exif_focal_length INTEGER,
               exif_aperture REAL,
               exif_shutter_speed REAL,
               FOREIGN KEY(photo_id) REFERENCES photos(id)
            )
    """)

def search_photos(keyword=None, lens=None, style=None, lighting=None, tags=None, focal=None):

    conn = get_conn()
    cur = conn.cursor()

    sql = """
    SELECT photos.id, photos.file_path
    FROM photos
    JOIN photo_metadata ON photos.id = photo_metadata.photo_id
    WHERE 1=1
    """

    params = []

    if keyword:
        sql += " AND photos.file_path LIKE ?"
        params.append(f"%{keyword}%")

    if lens:
        sql += " AND photo_metadata.lens=?"
        params.append(lens)

    if focal:
        sql += " AND photo_metadata.exif_focal_length=?"
        params.append(focal)

    if style:
        sql += " AND photo_metadata.style=?"
        params.append(style)

    if lighting:
        sql += " AND photo_metadata.lighting=?"
        params.append(lighting)

    if tags:
        sql += " AND photo_metadata.tags LIKE ?"
        params.append(f"%{tags}%")

    cur.execute(sql, params)
    return cur.fetchall()

def migrate():
    conn = get_conn()
    cur = conn.cursor()

    with open("src/backend/migrations/01_create_folders.sql", "r", encoding="utf-8") as f:
        sql = f.read()
        cur.executescript(sql)


def get_photos_by_folder(folder_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.file_path
        FROM photos p
        JOIN photo_folder pf ON pf.photo_id = p.id
        WHERE pf.folder_id = ?
        ORDER BY p.created_at DESC
    """, (folder_id,))
    return cur.fetchall()
    

def assign_photo_folder(photo_id, folder_id):
    conn = get_conn()
    cur = conn.cursor()
    # nếu đã có thì replace
    cur.execute("""
        INSERT OR REPLACE INTO photo_folder(photo_id, folder_id)
        VALUES (?,?)
    """, (photo_id, folder_id))

def toogle_favorite(photo_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE photo_metadata
        SET favorite = CASE favorite WHEN 1 THEN 0 ELSE 1 END
        WHERE id = ?
    """, (photo_id,))
    conn.commit()

