import os
from PySide6.QtWidgets import (
    QWidget, QLabel, QGridLayout, QScrollArea, QVBoxLayout,
    QFormLayout, QLineEdit, QComboBox, QPushButton, QMenu
)
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtCore import Signal, Qt

from ..backend.db import get_conn, get_photos_by_folder, search_photos
from ..utils.thumbnail import get_thumbnail

class PhotoCard(QWidget):
    clicked = Signal(int)

    def __init__(self, photo_id, thumb_path, parent=None):
        super().__init__(parent)
        self.photo_id = photo_id
        self.thumb_path = thumb_path
        self.setFixedSize(220, 180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        # Thumbnail
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(200, 150)

        pix = QPixmap(self.thumb_path)
        if not pix.isNull():
            self.label.setPixmap(
                pix.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        layout.addWidget(self.label)

        # Lấy tên file + kích thước
        filename = os.path.basename(self.thumb_path)
        size_text = f"{pix.width()}×{pix.height()} px"
        self.info = QLabel(f"{filename}\n{size_text}")
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setStyleSheet("font-size: 11px; color: #444;")
        layout.addWidget(self.info)

        # Click
        self.label.mousePressEvent = self.mousePressEvent

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.photo_id)
        return super().mousePressEvent(event)

class ClickableLabel(QLabel):
    clicked = Signal(int)

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)
        super().mouseDoubleClickEvent(event)


class GalleryView(QWidget):
    """
    Hiển thị thumbnail dạng grid – tương thích DB schema mới.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.photos = []      # list[(id, file_path)]
        self.thumbnails = []
        self.current_folder_id = None

        self._build_ui()
        self.load_photos()

    # ----------------------------------------------------------
    # UI
    # ----------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- Tiêu đề trang ---
        self.title_label = QLabel("All Photos")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
            padding: 8px 0;
        """)
        layout.addWidget(self.title_label)

        # --- Bộ lọc ---
        self.filter = FilterPanel()
        self.filter.btn_apply.clicked.connect(self.apply_filter)
        layout.addWidget(self.filter, 1)

        # --- Khu vực ảnh ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll, 10)

        self.inner = QWidget()
        self.grid = QGridLayout(self.inner)
        self.grid.setContentsMargins(10, 10, 10, 10)
        self.grid.setSpacing(10)
        self.scroll.setWidget(self.inner)

    #thêm tiêu đề
    def update_title(self, title: str):
        self.title_label.setText(title)
    # ----------------------------------------------------------
    # LOAD PHOTOS
    # ----------------------------------------------------------
    def load_for_folder(self, folder_id):
        """Load ảnh theo folder."""
        self.current_folder_id = folder_id
        self.photos = get_photos_by_folder(folder_id)   # [(id, file_path)]
        self._render_photos()

    def load_photos(self, rows=None):
        """Load tất cả ảnh (trừ deleted)."""
        if rows is None:
            rows = search_photos(keyword="", lens="", focal="", style="", lighting="", tags="")

        self.photos = [(r[0], r[1]) for r in rows]  # sanitize result
        self._render_photos()

    # ----------------------------------------------------------
    # RENDER GRID
    # ----------------------------------------------------------
    def _render_photos(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        self.thumbnails = []   # reset

        widgets = []
        for idx, (photo_id, file_path) in enumerate(self.photos):
            thumb = get_thumbnail(photo_id, file_path)

            card = PhotoCard(photo_id, thumb)
            card.index = idx     # <-- NEW: đánh số thứ tự đúng
            card.clicked.connect(self._open_viewer_by_id)

            self.thumbnails.append(card)  
            widgets.append(card)

        row, col = 0, 0
        for w in widgets:
            self.grid.addWidget(w, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1

    # ----------------------------------------------------------
    # VIEWER
    # ----------------------------------------------------------
    def open_viewer(self, index: int):
        from .image_viewer import ImageViewer
        viewer = ImageViewer(self.photos, start_index=index, parent=self)
        viewer.exec()

    # ----------------------------------------------------------
    # FILTER
    # ----------------------------------------------------------
    def apply_filter(self):
        keyword = self.filter.txt_keyword.text()
        rows = search_photos(keyword=keyword)
        self.load_photos(rows)

    # ----------------------------------------------------------
    # CONTEXT MENU
    # ----------------------------------------------------------
    def contextMenuEvent(self, event):
        photo_id = self._hit_test(event.pos())
        if photo_id is None:
            return

        menu = QMenu(self)
        mw = self.parent().parent()

        if mw.current_view == "trash":
            act_restore = QAction("Restore Photo", self)
            act_restore.triggered.connect(lambda _, pid=photo_id: self._restore_photo(pid))
            menu.addAction(act_restore)

            act_delete = QAction("Delete Permanently", self)
            act_delete.triggered.connect(lambda _, pid=photo_id: self._delete_photo(pid))
            menu.addAction(act_delete)
        else:
            act_add = QAction("Add Photo to this Folder…", self)
            act_add.triggered.connect(lambda: mw.add_photo_to_folder())
            menu.addAction(act_add)

            act_mv = QAction("Move to Folder…", self)
            act_mv.triggered.connect(lambda _, pid=photo_id: self._move_photo(pid))
            menu.addAction(act_mv)

            act_fav = QAction("Toggle Favorite", self)
            act_fav.triggered.connect(lambda _, pid=photo_id: self._toggle_favorite(pid))
            menu.addAction(act_fav)

            act_del = QAction("Move to Trash", self)
            act_del.triggered.connect(lambda _, pid=photo_id: self._move_to_trash(pid))
            menu.addAction(act_del)

        menu.exec(event.globalPos())

    def _hit_test(self, pos):
        # Chuyển đổi tọa độ click chính xác sang inner widget
        inner_pos = self.inner.mapFrom(self, pos)
        widget = self.inner.childAt(inner_pos)

        if not widget:
            return None

        # Lấy PhotoCard thực tế (nếu click vào QLabel thì lấy parent)
        if isinstance(widget, QLabel) and hasattr(widget.parent(), "photo_id"):
            widget = widget.parent()

        if isinstance(widget, PhotoCard):
            return widget.photo_id

        return None

    # ----------------------------------------------------------
    # DB OPS
    # ----------------------------------------------------------
    def _toggle_favorite(self, photo_id):
        from ..backend.db import toggle_favorite
        toggle_favorite(photo_id)
        self.reload_current_view()

    def _move_to_trash(self, photo_id):
        from ..backend.db import move_to_trash
        move_to_trash(photo_id)
        self.reload_current_view()

    def _move_photo(self, photo_id):
        from ..backend.db import assign_photo_folder, get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM folders ORDER BY name ASC")
        folders = cur.fetchall()
        if not folders:
            return

        menu = QMenu(self)
        for fid, name in folders:
            act = QAction(name, self)
            act.triggered.connect(lambda _, f=fid: assign_photo_folder(photo_id, f))
            menu.addAction(act)

        menu.exec(self.mapToGlobal(self.cursor().pos()))
        self.reload_current_view()

    def _restore_photo(self, photo_id):
        from ..backend.db import restore_photo
        restore_photo(photo_id)
        self.reload_current_view()

    def _delete_photo(self, photo_id):
        from ..backend.db import delete_permanently
        delete_permanently(photo_id)
        self.reload_current_view()


    # ----------------------------------------------------------
    def reload_current_view(self):
        """Reload UI đúng view hiện tại."""
        mw = self.parent().parent()

        if mw.current_view == "folder":
            mw.show_folder(mw.show_folder_id)
        elif mw.current_view == "trash":
            mw.show_trash()
        elif mw.current_view == "favorites":
            mw.show_favorites()
        else:
            mw.show_all()

    #xem ảnh theo id
    def _open_viewer_by_id(self, photo_id):
        # tìm index trong self.photos
        for idx, (pid, path) in enumerate(self.photos):
            if pid == photo_id:
                self.open_viewer(idx)
                return

# --------------------------------------------------------------
# FILTER PANEL
# --------------------------------------------------------------
class FilterPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)

        self.txt_keyword = QLineEdit()
        self.btn_apply = QPushButton("Search")

        layout.addRow("Search:", self.txt_keyword)
        layout.addWidget(self.btn_apply)
