from datetime import datetime
from pathlib import Path
import shutil
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
from ..backend.database_manager import get_session, Folder, Photo
from .sidebar import Sidebar
from .gallery_view import GalleryView
from .photo_info_panel import PhotoInfoPanel
from ..backend.project_manager import get_current_project_path


class MainWindow(QMainWindow):
    """
    Main UI window – chứa Sidebar, Gallery, và các hành động chính.
    """

    def __init__(self, project_path: str):
        super().__init__()
        self.setWindowTitle("Ref App")
        self.project_path = project_path
        self.session = get_session()
        self.current_folder_id = None
        self.current_view = "all"  # 🟢 Trạng thái mặc định

        # Build layout
        self._build_gallery_ui()

    # ------------------------------------------------------------
    # BUILD UI
    # ------------------------------------------------------------
    def _build_gallery_ui(self):
        root_widget = QWidget()
        root_layout = QHBoxLayout(root_widget)
        self.setCentralWidget(root_widget)

        # Sidebar bên trái
        self.sidebar = Sidebar(self)
        root_layout.addWidget(self.sidebar, 1)

        # Gallery ở giữa
        self.gallery = GalleryView(self, session=self.session)

        # --- Toolbar + Title ---
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 8, 8, 8)

        # Tiêu đề hiển thị tên section
        self.title_label = QLabel("📸 All Photos")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        toolbar_layout.addWidget(self.title_label, alignment=Qt.AlignLeft)

        toolbar_layout.addStretch()

        # Nút thêm ảnh
        btn_add_photo = QPushButton("+ Add Photo")
        btn_add_photo.setFixedHeight(32)
        btn_add_photo.setStyleSheet("""
            QPushButton {
                background-color: #0055ff;
                color: white;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0041cc;
            }
        """)
        btn_add_photo.clicked.connect(self.add_photo_to_folder)
        toolbar_layout.addWidget(btn_add_photo, alignment=Qt.AlignRight)

        # Container chứa toolbar + gallery
        gallery_container = QWidget()
        gallery_layout = QVBoxLayout(gallery_container)
        gallery_layout.setContentsMargins(0, 0, 0, 0)
        gallery_layout.setSpacing(0)
        gallery_layout.addWidget(toolbar)
        gallery_layout.addWidget(self.gallery)

        root_layout.addWidget(gallery_container, 5)
        # Thêm panel thông tin ảnh bên phải
        self.info_panel = PhotoInfoPanel(self)
        self.info_panel.setFixedWidth(320)
        root_layout.addWidget(self.info_panel, 2)

        # 🟢 Load mặc định All Photos
        self.show_all()

    # ------------------------------------------------------------
    # FOLDER & PHOTO HANDLING
    # ------------------------------------------------------------
    def add_photo_to_folder(self):
        """Chọn ảnh từ file dialog và thêm vào thư mục hiện tại hoặc All."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select photos to import", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not files:
            return

        project_dir = Path(get_current_project_path())
        import_count = 0

        for file_path in files:
            dest_folder = project_dir / "photos"
            dest_folder.mkdir(parents=True, exist_ok=True)
            dest_path = dest_folder / Path(file_path).name

            # Sao chép ảnh nếu chưa tồn tại
            if not dest_path.exists():
                shutil.copy(file_path, dest_path)

            photo = Photo(file_path=str(dest_path))
            if self.current_folder_id:
                photo.folder_id = self.current_folder_id
            self.session.add(photo)
            import_count += 1

        self.session.commit()
        QMessageBox.information(self, "Import completed", f"✅ Imported {import_count} photos successfully.")
        self.refresh_gallery()

    def import_photos(self, folder_id: int):
        """Import ảnh vào folder được chọn."""
        session = get_session()
        folder = session.query(Folder).filter_by(id=folder_id).first()
        if not folder:
            QMessageBox.warning(self, "Error", "Folder not found.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select photos to import",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not files:
            return

        imported = 0
        for f in files:
            if not session.query(Photo).filter_by(file_path=f).first():
                photo = Photo(file_path=f, folder_id=folder_id)
                session.add(photo)
                imported += 1

        session.commit()
        QMessageBox.information(self, "Import Completed", f"✅ Imported {imported} photo(s).")

        # Sau khi import, load lại gallery
        self.show_folder(folder_id)

    # ------------------------------------------------------------
    # GALLERY VIEW
    # ------------------------------------------------------------
    def refresh_gallery(self):
        """Reload lại gallery theo trạng thái hiện tại."""
        self.session.expire_all()
        if self.current_view == "trash":
            self.show_trash()
        elif self.current_view == "favorites":
            self.show_favorites()
        elif self.current_folder_id:
            self.show_folder(self.current_folder_id)
        else:
            self.show_all()

    def show_folder(self, folder_id: int):
        """Hiển thị ảnh trong folder được chọn."""
        self.current_folder_id = folder_id
        self.current_view = "folder"
        folder = self.session.query(Folder).filter_by(id=folder_id).first()
        photos = (
            self.session.query(Photo)
            .filter(Photo.folder_id == folder_id, Photo.is_deleted == False)
            .all()
        )
        self.gallery.load_photos(photos)
        self.gallery.update_title(f"📁 {folder.name if folder else 'Folder'}")

    def show_all(self):
        """Hiển thị tất cả ảnh (trừ đã xóa)."""
        self.current_folder_id = None
        self.current_view = "all"
        self.session.expire_all()
        photos = (
            self.session.query(Photo)
            .filter(Photo.is_deleted == False)
            .all()
        )
        self.gallery.load_photos(photos)
        self.gallery.update_title("📸 All Photos")

    def show_favorites(self):
        """Hiển thị ảnh yêu thích."""
        self.current_folder_id = None
        self.current_view = "favorites"
        photos = (
            self.session.query(Photo)
            .filter(Photo.rating >= 4, Photo.is_deleted == False)
            .all()
        )
        self.gallery.load_photos(photos)
        self.gallery.update_title("⭐ Favorites")

    def show_trash(self):
        """Hiển thị ảnh trong thùng rác."""
        self.current_folder_id = None
        self.current_view = "trash"
        self.session.rollback()
        photos = (
            self.session.query(Photo)
            .filter(Photo.is_deleted == True)
            .all()
        )
        self.gallery.load_photos(photos)
        self.gallery.update_title("🗑 Trash")

    # ------------------------------------------------------------
    # FOLDER MANAGEMENT
    # ------------------------------------------------------------
    def add_folder(self, folder_name: str):
        if not folder_name.strip():
            return

        project_root = get_current_project_path()
        if not project_root:
            QMessageBox.warning(self, "Warning", "Please select or open a project first.")
            return

        folder_path = Path(project_root) / folder_name.strip()
        folder_path.mkdir(parents=True, exist_ok=True)

        folder = Folder(name=folder_name.strip(), path=str(folder_path), created_at=datetime.now())
        self.session.add(folder)
        self.session.commit()
        self.sidebar.refresh_folders()

    # ------------------------------------------------------------
    # UTILS
    # ------------------------------------------------------------
    def confirm_action(self, message: str):
        """Hiển thị confirm box."""
        reply = QMessageBox.question(
            self, "Confirm", message,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        return reply == QMessageBox.Yes
    
    # ------------------------------------------------------------
    # PHOTO INFO DISPLAY
    # ------------------------------------------------------------
    def show_photo_info(self, photo_id: int):
        """Hiển thị thông tin chi tiết của ảnh khi click 1 lần."""
        if hasattr(self, "info_panel") and self.info_panel:
            self.info_panel.load_photo_info(photo_id)
