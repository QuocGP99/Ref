from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QInputDialog,
    QFileDialog,
)
from PySide6.QtCore import Qt
from .sidebar import Sidebar
from .gallery_view import GalleryView
from ..backend.project_manager import init_project_folder

class MainWindow(QMainWindow):
    def __init__(self, project_folder):
        super().__init__()
        self.project_folder = project_folder
        self.setWindowTitle(f"Ref – {project_folder}")

        # state cho view
        self.current_view = "all"
        self.show_folder_id = None
        self.ui_enabled = False

        # init project structure + db
        self.ref_folder, self.db_path = init_project_folder(project_folder)
        self._build_ui()
    
    def _build_ui(self):
        container = QWidget()
        root_layout = QHBoxLayout(container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Placeholder khi chưa có thư mục / chưa bật gallery
        self.empty_box = QWidget()
        v = QVBoxLayout(self.empty_box)
        v.setAlignment(Qt.AlignCenter)

        self.msg = QLabel(
            "Project created.\n\nNo photos yet.\n\nPlease Add Folder to start.",
        )
        self.msg.setAlignment(Qt.AlignCenter)
        v.addWidget(self.msg)

        self.btn_add_folder = QPushButton("Add Folder")
        self.btn_add_folder.clicked.connect(self.create_folder)
        v.addWidget(self.btn_add_folder, alignment=Qt.AlignCenter)

        root_layout.addWidget(self.empty_box, alignment=Qt.AlignCenter)

        self.setCentralWidget(container)
        self.resize(1400, 800)

    def enable_gallery_ui(self):
        """Bật Sidebar + Gallery một lần duy nhất sau khi đã có dữ liệu."""
        if self.ui_enabled:
            return

        self.ui_enabled = True

        container = self.centralWidget()
        layout = container.layout()

        # bỏ placeholder empty
        if hasattr(self, "empty_box"):
            layout.removeWidget(self.empty_box)
            self.empty_box.hide()

        # Tạo Sidebar + Gallery
        self.sidebar = Sidebar(self)
        self.gallery = GalleryView()

        layout.addWidget(self.sidebar)
        layout.addWidget(self.gallery, 1)

        # Lần đầu tiên: hiển thị All Photos (có thể đang trống)
        self.show_all()

    def create_folder(self):
        # Chọn thư mục ảnh thật
        folder_path = QFileDialog.getExistingDirectory(self, "Select photo folder")
        if not folder_path:
            return

        folder_name = folder_path.split("/")[-1]

        from ..backend.db import get_conn
        conn = get_conn()
        cur = conn.cursor()

        # Lưu folder_name + folder_path vào DB
        cur.execute(
            "INSERT INTO folders(name, path) VALUES(?, ?)",
            (folder_name, folder_path)
        )
        conn.commit()
        folder_id = cur.lastrowid

        # Import ảnh từ folder này
        from src.services.import_service import import_folder
        import_folder(folder_path, folder_id=folder_id)

        # Bật giao diện sidebar + gallery nếu chưa bật
        self.enable_gallery_ui()
        self.sidebar.refresh_folders()
        self.show_folder(folder_id)


    def show_folder(self, folder_id):
        from ..backend.db import get_photos_by_folder
        self.current_view = "folder"
        self.show_folder_id = folder_id
        photos = get_photos_by_folder(folder_id)
        self.gallery.load_photos(photos)

    def show_all(self):
        self.current_view = "all"
        self.show_folder_id = None
        self.gallery.load_photos()

    def show_favorites(self):
        from ..backend.db import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.file_path
            FROM photos p
            JOIN photo_metadata m ON p.id = m.photo_id
            WHERE m.favorite = 1 AND m.is_deleted = 0
            ORDER BY p.created_at DESC
        """)
        photos = cur.fetchall()
        self.current_view = "favorites"
        self.show_folder_id = None
        self.gallery.load_photos(photos)

    def show_trash(self):
        from ..backend.db import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.file_path
            FROM photos p
            JOIN photo_metadata m ON p.id = m.photo_id
            WHERE m.is_deleted = 1
            ORDER BY p.created_at DESC
        """)
        photos = cur.fetchall()
        self.current_view = "trash"
        self.show_folder_id = None
        self.gallery.load_photos(photos)

    def add_photo_to_folder(self):
        # folder hiện tại?
        if not hasattr(self, "show_folder_id") or not self.show_folder_id:
            print("Chưa chọn folder")
            return

        from PySide6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn ảnh", "", "Images (*.png *.jpg *.jpeg)")
        if not files:
            return

        import os
        folder_id = self.show_folder_id

        from ..backend.db import add_photo_with_folder

        for file_path in files:
            add_photo_with_folder(file_path, folder_id)

        # reload gallery
        self.show_folder(folder_id)



