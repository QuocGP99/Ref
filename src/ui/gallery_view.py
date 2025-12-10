from PySide6.QtWidgets import (
    QWidget, QLabel, QGridLayout, QScrollArea, QVBoxLayout,
    QFormLayout, QLineEdit, QComboBox, QPushButton, QMenu
)
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtCore import Signal, Qt

from ..backend.db import get_conn, get_photos_by_folder, search_photos
from ..utils.thumbnail import get_thumbnail


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

        self.filter = FilterPanel()
        self.filter.btn_apply.clicked.connect(self.apply_filter)
        layout.addWidget(self.filter, 1)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll, 10)

        self.inner = QWidget()
        self.grid = QGridLayout(self.inner)
        self.grid.setContentsMargins(10, 10, 10, 10)
        self.grid.setSpacing(10)

        self.scroll.setWidget(self.inner)

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
        # clear grid
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.thumbnails = []

        col_max = 6
        r, c = 0, 0

        for idx, (photo_id, file_path) in enumerate(self.photos):
            thumb_path = get_thumbnail(photo_id, file_path, size=260)

            lbl = ClickableLabel(idx)
            pix = QPixmap(thumb_path)
            lbl.setPixmap(pix)
            lbl.setScaledContents(True)
            lbl.setFixedSize(260, 260)

            lbl.clicked.connect(self.open_viewer)

            self.thumbnails.append(lbl)
            self.grid.addWidget(lbl, r, c)

            c += 1
            if c >= col_max:
                c = 0
                r += 1

        self.inner.adjustSize()

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
        lens = self.filter.cmb_lens.currentText()
        focal = self.filter.cmb_focal.currentText()
        style = self.filter.cmb_style.currentText()
        light = self.filter.cmb_lighting.currentText()
        tags = self.filter.txt_tags.text()

        rows = search_photos(keyword, lens, focal, style, light, tags)
        self.load_photos(rows)

    # ----------------------------------------------------------
    # CONTEXT MENU
    # ----------------------------------------------------------
    def contextMenuEvent(self, event):
        idx = self._hit_test(event.pos())
        if idx is None:
            return

        menu = QMenu(self)

        # Add photo
        act_add = QAction("Add Photo to this Folder…", self)
        act_add.triggered.connect(lambda: self.parent().parent().add_photo_to_folder())
        menu.addAction(act_add)

        # Move to folder
        act_mv = QAction("Move to Folder…", self)
        act_mv.triggered.connect(lambda: self._move_photo(idx))
        menu.addAction(act_mv)

        # Favorite
        act_fav = QAction("Toggle Favorite", self)
        act_fav.triggered.connect(lambda: self._toggle_favorite(idx))
        menu.addAction(act_fav)

        # Trash
        act_del = QAction("Move to Trash", self)
        act_del.triggered.connect(lambda: self._move_to_trash(idx))
        menu.addAction(act_del)

        menu.exec(event.globalPos())

    def _hit_test(self, pos):
        """Tìm index ảnh user right-click."""
        for i, lbl in enumerate(self.thumbnails):
            if lbl.geometry().contains(pos):
                return i
        return None

    # ----------------------------------------------------------
    # DB OPS
    # ----------------------------------------------------------
    def _toggle_favorite(self, index):
        from ..backend.db import toggle_favorite
        pid, _ = self.photos[index]
        toggle_favorite(pid)
        self.reload_current_view()

    def _move_to_trash(self, index):
        from ..backend.db import move_to_trash
        pid, _ = self.photos[index]
        move_to_trash(pid)
        self.reload_current_view()

    def _move_photo(self, index):
        from ..backend.db import assign_photo_folder, get_conn

        pid, _ = self.photos[index]
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM folders ORDER BY name ASC")
        folders = cur.fetchall()

        if not folders:
            return

        menu = QMenu(self)
        for fid, name in folders:
            act = QAction(name, self)
            act.triggered.connect(lambda _, f=fid: assign_photo_folder(pid, f))
            menu.addAction(act)

        menu.exec(self.mapToGlobal(self.cursor().pos()))
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


# --------------------------------------------------------------
# FILTER PANEL
# --------------------------------------------------------------
class FilterPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QFormLayout(self)

        self.txt_keyword = QLineEdit()
        self.cmb_lens = QComboBox()
        self.cmb_focal = QComboBox()
        self.cmb_style = QComboBox()
        self.cmb_lighting = QComboBox()
        self.txt_tags = QLineEdit()

        self.cmb_lens.addItems(["", "RF 35mm", "RF 50mm", "RF 85mm", "RF 70-200mm"])
        self.cmb_focal.addItems(["", "24", "35", "50", "85", "105"])
        self.cmb_style.addItems(["", "Outdoor", "Indoor", "Studio"])
        self.cmb_lighting.addItems(["", "Side Light", "Back Light", "Front Light"])

        layout.addRow("Search:", self.txt_keyword)
        layout.addRow("Lens:", self.cmb_lens)
        layout.addRow("Focal:", self.cmb_focal)
        layout.addRow("Style:", self.cmb_style)
        layout.addRow("Lighting:", self.cmb_lighting)
        layout.addRow("Tags:", self.txt_tags)

        self.btn_apply = QPushButton("Filter")
        layout.addWidget(self.btn_apply)
