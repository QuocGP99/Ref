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
from ..backend.project_manager import init_or_load_project


class MainWindow(QMainWindow):
    def __init__(self, project_folder):
        super().__init__()
        self.project_folder = project_folder
        self.setWindowTitle(f"Ref – {project_folder}")

        # state cho view
        self.current_view = "all"
        self.show_folder_id = None
        self.ui_enabled = False

        # init hoặc load project
        self.ref_folder, self.db_path = init_or_load_project(project_folder)

        # kiểm tra DB có folder sẵn → bật UI hoặc hiển thị trống
        from ..backend.db import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM folders")
        has_folder = cur.fetchone()[0] > 0
        conn.close()

        if has_folder:
            # Nếu project đã có folder → bật luôn UI gallery
            self._build_gallery_ui()
        else:
            # Nếu chưa có folder → hiển thị khung trống như cũ
            self._build_empty_ui()

    def _build_empty_ui(self):
        """Hiển thị giao diện trống khi project chưa có folder."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.empty_box = QWidget()
        v = QVBoxLayout(self.empty_box)
        v.setAlignment(Qt.AlignCenter)

        msg = QLabel("Project created.\n\nNo photos yet.\n\nPlease Add Folder to start.")
        msg.setAlignment(Qt.AlignCenter)
        v.addWidget(msg)

        btn_add_folder = QPushButton("Add Folder")
        btn_add_folder.clicked.connect(self.create_folder)
        v.addWidget(btn_add_folder, alignment=Qt.AlignCenter)

        layout.addWidget(self.empty_box, alignment=Qt.AlignCenter)

        self.setCentralWidget(container)
        self.resize(1400, 800)

    def _build_gallery_ui(self):
        """Bật Sidebar + Gallery (khi DB đã có folder hoặc ảnh)."""
        container = QWidget()
        root_layout = QHBoxLayout(container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar(self)
        self.gallery = GalleryView()

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.gallery, 1)

        self.setCentralWidget(container)
        self.resize(1400, 800)

        # Hiển thị ảnh mặc định
        self.show_all()

        self.ui_enabled = True

    def enable_gallery_ui(self):
        """Bật Sidebar + Gallery sau khi thêm folder đầu tiên."""
        if self.ui_enabled:
            return
        self._build_gallery_ui()

    def create_folder(self):
        from PySide6.QtWidgets import QMessageBox
        from ..backend.db import get_conn, folder_exists

        folder_path = QFileDialog.getExistingDirectory(self, "Select photo folder")
        if not folder_path:
            return

        # Kiểm tra trùng
        if folder_exists(folder_path):
            QMessageBox.warning(self, "Duplicate Folder", "This folder has already been added to the project.")
            return

        folder_name = folder_path.split("/")[-1]
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO folders(name, path) VALUES(?, ?)", (folder_name, folder_path))
        conn.commit()
        folder_id = cur.lastrowid

        from ..services.import_service import import_folder
        import_folder(folder_path, folder_id=folder_id)

        self.enable_gallery_ui()
        self.sidebar.refresh_folders()
        self.show_folder(folder_id)

    def show_folder(self, folder_id):
        from ..backend.db import get_photos_by_folder
        self.current_view = "folder"
        self.show_folder_id = folder_id
        photos = get_photos_by_folder(folder_id)
        self.gallery.load_photos(photos)
        self.gallery.update_title(f"Folder: {folder_id}")


    def show_all(self):
        self.current_view = "all"
        self.show_folder_id = None
        self.gallery.load_photos()
        self.gallery.update_title("All Photos")

    def show_favorites(self):
        from ..backend.db import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, file_path
            FROM photos
            WHERE favorite = 1 AND deleted = 0
            ORDER BY created_at DESC
        """)
        photos = cur.fetchall()
        conn.close()

        self.current_view = "favorites"
        self.show_folder_id = None
        self.gallery.load_photos(photos)
        self.gallery.update_title("Favorites")

    def show_trash(self):
        from ..backend.db import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, file_path
            FROM photos
            WHERE deleted = 1
            ORDER BY created_at DESC
        """)
        photos = cur.fetchall()
        conn.close()

        self.current_view = "trash"
        self.show_folder_id = None
        self.gallery.load_photos(photos)
        self.gallery.update_title("Trash")

    def add_photo_to_folder(self):
        if not self.show_folder_id:
            print("Chưa chọn folder")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn ảnh", "", "Images (*.png *.jpg *.jpeg)"
        )
        if not files:
            return

        from src.services.import_service import process_photo

        for file_path in files:
            process_photo(file_path, self.show_folder_id)

        self.show_folder(self.show_folder_id)



