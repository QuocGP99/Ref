from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout
from .sidebar import Sidebar
from .gallery_view import GalleryView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ref")

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar(self)
        self.sidebar.setFixedWidth(220)

        self.gallery = GalleryView()

        layout.addWidget(self.sidebar)
        layout.addWidget(self.gallery, 1)

        self.setCentralWidget(container)
        self.resize(1400, 800)

    def show_folder(self, folder_id):
        from ..backend.db import get_photos_by_folder
        photos = get_photos_by_folder(folder_id)
        self.gallery.load_photos(photos)

    def show_all(self):
        from ..backend.db import search_photos
        photos = search_photos()
        self.gallery.load_photos(photos)
    
    def show_favorites(self):
        from ..backend.db import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.file_path
            FROM photos p
            JOIN photo_metadata m ON p.id = m.photo_id
            WHERE m.favorite = 1
            ORDER BY p.created_at DESC
        """)
        rows = cur.fetchall()

        self.gallery.current_filter = "favorites"
        self.gallery.load_photos(rows)