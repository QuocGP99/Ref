from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QGridLayout,
    QScrollArea,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QMenu,
)
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtCore import Signal, Qt

from ..backend.db import get_conn
from ..utils.thumbnail import get_thumbnail


class ClickableLabel(QLabel):
    clicked = Signal(int)  # emit index trong list photos

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)
        super().mouseDoubleClickEvent(event)


class GalleryView(QWidget):
    """
    Hiển thị danh sách ảnh dạng grid trong QScrollArea.
    Double-click thumbnail để mở ImageViewer.
    """
    

    def __init__(self, parent=None):
        super().__init__(parent)

        self.photos = []  # list[(photo_id, file_path)]
        self.thumbnails = []

        self._build_ui()
        self.load_photos()

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
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(10)

        self.scroll.setWidget(self.inner)

    def load_photos(self, rows = None):
        self.thumbnails = []
        if rows is None:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, file_path FROM photos ORDER BY created_at DESC")
            rows = cur.fetchall()

        self.photos = rows

        # clear grid cũ
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        col_count = 6  # số cột cố định, sau nâng cấp responsive sau
        row = 0
        col = 0

        for idx, (photo_id, path) in enumerate(rows):
            thumb_path = get_thumbnail(photo_id, path, size=260)
            label = ClickableLabel(idx)
            label.setScaledContents(True)
            pix = QPixmap(thumb_path)
            self.thumbnails.append(label)

            if not pix.isNull():
                label.setPixmap(pix)
            label.setFixedSize(260, 260)
            label.setStyleSheet("background-color: #111;")

            label.clicked.connect(self.open_viewer)

            self.grid.addWidget(label, row, col)

            col += 1
            if col >= col_count:
                col = 0
                row += 1

        self.inner.adjustSize()

    def open_viewer(self, index: int):
        """
        Mở ImageViewer cho ảnh tại index.
        """
        from .image_viewer import ImageViewer

        if not self.photos:
            return

        viewer = ImageViewer(self.photos, start_index=index, parent=self)
        viewer.exec()

    def apply_filter(self):
        from ..backend.db import search_photos

        photos = search_photos(
            keyword=self.filter.txt_keyword.text(),
            lens=self.filter.cmb_lens.currentText(),
            style=self.filter.cmb_style.currentText(),
            lighting=self.filter.cmb_lighting.currentText(),
            tags=self.filter.txt_tags.text(),
            focal=self.filter.cmb_focal.currentText()
        )


        self.load_photos(photos)

    def contextMenuEvent(self, event):
        index = self.get_clicked_photo_index(event.pos())  # ta sẽ viết hàm này
        if index is None:
            return

        menu = QMenu(self)

        action_move = QAction("Move to Folder...", self)
        action_move.triggered.connect(lambda: self.move_photo_to_folder(index))
        menu.addAction(action_move)

        action_fav = QAction("Add to Favorites", self)
        action_fav.triggered.connect(lambda: self.toggle_favorite(index))
        menu.addAction(action_fav)

        menu.exec(event.globalPos())

    def toggle_favorite(self, index):
        from ..backend.db import toggle_favorite
        photo_id, _ = self.photos[index]
        toggle_favorite(photo_id)
        
        if getattr(self, "current_filter", None) == "favorites":
            self.show_favorites()

    def get_clicked_photo_index(self, pos):
        for i, (_, path) in enumerate(self.photos):
            label = self.thumbnails[i]   # nếu bạn dùng QLabel list
            if label.geometry().contains(pos):
                return i
        return None
    
    def move_photo_to_folder(self, index):
        from ..backend.db import get_conn, assign_photo_folder

        photo_id, _ = self.photos[index]

        # lấy danh sách folder
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id,name FROM folders ORDER BY name ASC")
        folders = cur.fetchall()

        if not folders:
            print("No folders")
            return

        # Hiển thị QMenu chọn folder
        menu = QMenu(self)
        for fid, fname in folders:
            act = QAction(fname, self)
            act.triggered.connect(lambda _, f=fid: assign_photo_folder(photo_id, f))
            menu.addAction(act)

        menu.exec(self.mapToGlobal(self.cursor().pos()))
        # sau khi gán xong thì reload view hiện tại
        self.reload_current_view()

    def reload_current_view(self):
        from ..backend.db import search_photos
        self.load_photos(search_photos())


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

        self.cmb_lens.addItems(["", "35mm", "50mm", "85mm", "135mm"])
        self.cmb_focal.addItems(["", "35", "50", "85", "135"])
        self.cmb_style.addItems(["", "Outdoor", "Indoor", "Backlight"])
        self.cmb_lighting.addItems(["", "Side Light", "Back Light", "Front"])

        layout.addRow("Search:", self.txt_keyword)
        layout.addRow("Lens:", self.cmb_lens)
        layout.addRow("Focal:", self.cmb_focal)
        layout.addRow("Style:", self.cmb_style)
        layout.addRow("Lighting:", self.cmb_lighting)
        layout.addRow("Tags:", self.txt_tags)

        self.btn_apply = QPushButton("Filter")
        layout.addWidget(self.btn_apply)


    
