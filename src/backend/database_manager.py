import os
from sqlalchemy import (
    create_engine, Column, Integer, String,
    Boolean, ForeignKey, DateTime, JSON, Text
)
from sqlalchemy.orm import Session,sessionmaker, relationship, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# ======================================================
# ✅ CONFIG TOÀN CỤC
# ======================================================
Base = declarative_base()
_engine = None
_Session = None
_engine_url = "mysql+pymysql://root:qteovas2235@localhost/ref_app"  # ⚙️ Cập nhật thông tin kết nối MySQL


def get_engine_url():
    """Trả về connection string MySQL hiện tại."""
    global _engine_url
    return _engine_url


def init_db(db_url=None):
    """Khởi tạo engine + session factory cho MySQL"""
    global _engine, _Session

    if db_url is None:
        db_url = _engine_url

    try:
        print(f"🔗 Connecting to MySQL database at {db_url}")
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        Base.metadata.create_all(_engine)
        _Session = sessionmaker(bind=_engine)
        print("✅ MySQL schema initialized")
    except SQLAlchemyError as e:
        print(f"❌ Database initialization failed: {e}")
        raise


def get_session():
    """Trả về một SQLAlchemy session."""
    global _Session
    if _Session is None:
        raise RuntimeError("⚠️ Database engine chưa được init. Gọi init_db() trước khi dùng.")
    return _Session()

# ======================================================
# ✅ MODEL KHAI BÁO ORM
# ======================================================
class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    photos = relationship("Photo", back_populates="folder", cascade="all, delete")

    def __repr__(self):
        return f"<Folder(name={self.name})>"


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True)
    file_path = Column(String(500), nullable=False)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"))

    # EXIF + Metadata
    exif_iso = Column(Integer, nullable=True)
    exif_focal_length = Column(String(50), nullable=True)
    exif_aperture = Column(String(50), nullable=True)
    exif_shutter_speed = Column(String(50), nullable=True)

    rating = Column(Integer, default=0)
    note = Column(Text, nullable=True)
    tags = Column(JSON, default=[])
    color_palette = Column(JSON, default=[])

    is_deleted = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)

    date_created = Column(DateTime, default=datetime.now)
    date_imported = Column(DateTime, default=datetime.now)
    date_modified = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    folder = relationship("Folder", back_populates="photos")

    def __repr__(self):
        return f"<Photo(id={self.id}, file={os.path.basename(self.file_path)})>"

# ======================================================
# ✅ TIỆN ÍCH ORM
# ======================================================
def add_photo(session, folder_id, file_path, metadata=None):
    """Thêm ảnh mới vào thư mục."""
    photo = Photo(folder_id=folder_id, file_path=file_path, **(metadata or {}))
    session.add(photo)
    session.commit()
    return photo


def get_all_photos(session):
    """Lấy toàn bộ ảnh chưa xóa."""
    return session.query(Photo).filter(Photo.is_deleted == False).all()


def get_trash_photos(session):
    """Lấy ảnh trong thùng rác."""
    return session.query(Photo).filter(Photo.is_deleted == True).all()


def move_to_trash(session, photo_id):
    """Đưa ảnh vào thùng rác (soft delete)."""
    photo = session.query(Photo).get(photo_id)
    if photo:
        photo.is_deleted = True
        session.commit()
        return True
    return False


def restore_from_trash(session, photo_id):
    """Khôi phục ảnh từ thùng rác."""
    photo = session.query(Photo).get(photo_id)
    if photo:
        photo.is_deleted = False
        session.commit()
        return True
    return False

def delete_folder_permanently(folder_id: int):
    """
    🧹 Xóa hoàn toàn folder và ảnh liên quan khỏi database (KHÔNG xóa file gốc).
    - Chỉ xóa dữ liệu trong DB
    - Không xóa thư mục hay file ảnh vật lý
    - An toàn cho dữ liệu gốc trên ổ đĩa
    """
    session = get_session()
    try:
        folder = session.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            print(f"[WARN] Folder ID={folder_id} not found in DB.")
            return

        # 🧹 Xóa toàn bộ ảnh trong DB (chỉ database)
        photos = session.query(Photo).filter(Photo.folder_id == folder.id).all()
        for photo in photos:
            session.delete(photo)

        # 🧾 Commit sau khi xóa ảnh
        session.commit()

        # 🗑️ Cuối cùng xóa folder khỏi DB
        session.delete(folder)
        session.commit()

        print(f"🗑️ Deleted folder '{folder.name}' (ID={folder.id}) from database.")

    except SQLAlchemyError as e:
        session.rollback()
        print(f"[DB ERROR] Failed to delete folder {folder_id}: {e}")
    finally:
        session.close()