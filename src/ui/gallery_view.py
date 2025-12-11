import os
from PySide6.QtWidgets import (
    QWidget, QLabel, QGridLayout, QScrollArea, QVBoxLayout,
    QFormLayout, QLineEdit, QPushButton, QMenu, QMessageBox, QHBoxLayout, QGraphicsView, QGraphicsScene, QPushButton, QFrame
)
from PySide6.QtGui import QPixmap, QAction, QPainter, QTransform
from PySide6.QtCore import Signal, Qt
from ..backend.database_manager import get_session, Photo, Folder
from ..utils.thumbnail import get_thumbnail

class PhotoCard(QWidget):
    """Thẻ ảnh hiển thị thumbnail + tên file + click sự kiện."""
    clicked = Signal(int)
    double_clicked = Signal(int)

    def __init__(self, photo_id, file_path, thumb_path, parent=None):
        super().__init__(parent)
        self.photo_id = photo_id
        self.file_path = file_path
        self.thumb_path = thumb_path
        self.setFixedSize(220, 190)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        # Thumbnail
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(200, 150)

        pix = QPixmap(self.thumb_path)
        if not pix.isNull():
            self.label.setPixmap(pix.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self.label)

        # File name
        filename = os.path.basename(self.file_path)
        self.info = QLabel(filename)
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setStyleSheet("font-size: 11px; color: #555;")
        layout.addWidget(self.info)

        # Sự kiện click
        self.label.mousePressEvent = self.mousePressEvent
        self.label.mouseDoubleClickEvent = self.mouseDoubleClickEvent

    def mousePressEvent(self, event):
        """Click 1 lần: hiển thị thông tin ảnh."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.photo_id)

    def mouseDoubleClickEvent(self, event):
        """Click 2 lần: phóng to ảnh ngay trong gallery."""
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.photo_id)

class ZoomGraphicsView(QGraphicsView):
    """GraphicsView hỗ trợ zoom và kéo ảnh."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        self.scale(factor, factor)


class GalleryView(QWidget):
    def __init__(self, main_window, session=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.session = session if session is not None else get_session()

        self.photos = []
        self.current_folder_id = None
        self.full_image_label = None  # dùng để hiển thị ảnh full

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("All Photos")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 600; padding: 8px 0;")
        layout.addWidget(self.title_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll, 1)

        self.inner = QWidget()
        self.grid = QGridLayout(self.inner)
        self.grid.setContentsMargins(10, 10, 10, 10)
        self.grid.setSpacing(10)
        self.scroll.setWidget(self.inner)

    def update_title(self, text: str):
        if hasattr(self, "title_label"):
            self.title_label.setText(text)

    # ============================================================
    # LOAD / DISPLAY
    # ============================================================
    def load_photos(self, photos):
        """Load và hiển thị danh sách ảnh."""
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.photos = [(p.id, p.file_path) for p in photos]

        for idx, (photo_id, file_path) in enumerate(self.photos):
            thumb_path = get_thumbnail(photo_id, file_path)
            card = PhotoCard(photo_id, file_path, thumb_path, parent=self.inner)
            card.clicked.connect(self._on_photo_clicked)
            card.double_clicked.connect(self._on_photo_double_clicked)
            row, col = divmod(idx, 4)
            self.grid.addWidget(card, row, col)

    def _on_photo_clicked(self, photo_id):
        """Click 1 lần hiển thị info panel."""
        mw = self.window()
        if hasattr(mw, "show_photo_info"):
            mw.show_photo_info(photo_id)

    def _on_photo_double_clicked(self, photo_id):
        """Phóng to ảnh trực tiếp trong gallery với toolbar điều khiển."""
        photo = self.session.get(Photo, photo_id)
        if not photo or not os.path.exists(photo.file_path):
            QMessageBox.warning(self, "Error", "Photo file not found.")
            return

        # Ẩn lưới ảnh hiện tại
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            if item and item.widget():
                item.widget().hide()

        # Tạo frame để hiển thị full ảnh + toolbar
        self.full_frame = QFrame()
        vbox = QVBoxLayout(self.full_frame)
        vbox.setContentsMargins(0, 0, 0, 0)

        # GraphicsView hiển thị ảnh
        self.scene = QGraphicsScene(self)
        self.view = ZoomGraphicsView()
        self.view.setScene(self.scene)
        pix = QPixmap(photo.file_path)
        self.image_item = self.scene.addPixmap(pix)
        self.scene.setSceneRect(pix.rect())
        self.view.fitInView(self.image_item, Qt.KeepAspectRatio)
        vbox.addWidget(self.view, 1)

        # Toolbar điều khiển
        toolbar = QHBoxLayout()
        btn_prev = QPushButton("◀ Prev")
        btn_next = QPushButton("Next ▶")
        btn_rotate = QPushButton("⟳ Rotate")
        btn_flip = QPushButton("⇋ Flip")
        btn_crop = QPushButton("✂ Crop")
        btn_fit = QPushButton("Fit to Window")
        btn_back = QPushButton("↩ Back")

        for b in [btn_prev, btn_next, btn_rotate, btn_flip, btn_crop, btn_fit, btn_back]:
            toolbar.addWidget(b)

        vbox.addLayout(toolbar)

        # Sự kiện
        btn_prev.clicked.connect(lambda: self._navigate_photo(photo_id, -1))
        btn_next.clicked.connect(lambda: self._navigate_photo(photo_id, 1))
        btn_rotate.clicked.connect(self._rotate_image)
        btn_flip.clicked.connect(self._flip_image)
        btn_crop.clicked.connect(self._crop_image)
        btn_fit.clicked.connect(self._fit_image)
        btn_back.clicked.connect(self._restore_grid_view)

        # Gắn vào layout
        self.grid.addWidget(self.full_frame, 0, 0)


    def _restore_grid_view(self):
        """Quay lại chế độ hiển thị lưới."""
        if self.full_image_label:
            self.full_image_label.deleteLater()
            self.full_image_label = None
        self.load_photos([self.session.get(Photo, pid) for pid, _ in self.photos if self.session.get(Photo, pid)])

    # ============================================================
    # CONTEXT MENU / DATABASE
    # ============================================================
    def contextMenuEvent(self, event):
        photo_id = self._hit_test(event.pos())
        if photo_id is None:
            return

        menu = QMenu(self)
        mw = self.window()

        if mw.current_view == "trash":
            act_restore = QAction("Restore Photo", self)
            act_restore.triggered.connect(lambda _, pid=photo_id: self._restore_photo(pid))
            menu.addAction(act_restore)

            act_delete = QAction("Delete Permanently", self)
            act_delete.triggered.connect(lambda _, pid=photo_id: self._delete_photo(pid))
            menu.addAction(act_delete)
        else:
            act_mv_trash = QAction("Move to Trash", self)
            act_mv_trash.triggered.connect(lambda _, pid=photo_id: self._move_to_trash(pid))
            menu.addAction(act_mv_trash)

        menu.exec(event.globalPos())

    def _hit_test(self, pos):
        inner_pos = self.inner.mapFrom(self, pos)
        widget = self.inner.childAt(inner_pos)
        if not widget:
            return None
        if isinstance(widget, QLabel) and hasattr(widget.parent(), "photo_id"):
            widget = widget.parent()
        if isinstance(widget, PhotoCard):
            return widget.photo_id
        return None

    # ============================================================
    # DB ACTIONS (giữ nguyên từ bạn)
    # ============================================================
    def _move_to_trash(self, photo_id):
        mw = self.window()
        session = mw.session
        try:
            photo = session.get(Photo, photo_id)
            if not photo:
                QMessageBox.warning(self, "Error", "Photo not found.")
                return

            reply = QMessageBox.question(
                self,
                "Confirm Move to Trash",
                f"Move '{os.path.basename(photo.file_path)}' to Trash?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

            photo.is_deleted = True
            session.commit()
            mw.refresh_gallery()
            mw.show_trash()
            QMessageBox.information(self, "Moved to Trash", "Photo moved successfully.")
        except Exception as e:
            print(f"[ERROR] Move to Trash: {e}")
            session.rollback()

    def _restore_photo(self, photo_id):
        try:
            photo = self.session.get(Photo, photo_id)
            if not photo:
                return
            photo.is_deleted = False
            self.session.commit()
            QMessageBox.information(self, "Restored", "Photo restored successfully.")
            self.reload_current_view()
        except Exception as e:
            print(f"[ERROR] Restore photo: {e}")
            self.session.rollback()

    def _delete_photo(self, photo_id):
        try:
            photo = self.session.get(Photo, photo_id)
            if not photo:
                return
            self.session.delete(photo)
            self.session.commit()
            QMessageBox.information(self, "Deleted", "Photo deleted permanently.")
            self.reload_current_view()
        except Exception as e:
            print(f"[ERROR] Delete photo: {e}")
            self.session.rollback()

    def reload_current_view(self):
        mw = self.window()
        if mw.current_view == "trash":
            mw.show_trash()
        elif mw.current_view == "favorites":
            mw.show_favorites()
        elif mw.current_view == "folder" and hasattr(mw, "show_folder_id"):
            mw.show_folder(mw.show_folder_id)
        else:
            mw.show_all()

    def _navigate_photo(self, current_id, step):
        """Chuyển ảnh kế tiếp hoặc trước đó."""
        ids = [pid for pid, _ in self.photos]
        if current_id not in ids:
            return
        idx = ids.index(current_id)
        new_idx = (idx + step) % len(ids)
        new_id = ids[new_idx]
        self._on_photo_double_clicked(new_id)

    def _rotate_image(self):
        if hasattr(self, "image_item"):
            t = self.image_item.transform()
            t.rotate(90)
            self.image_item.setTransform(t)
            self.view.fitInView(self.image_item, Qt.KeepAspectRatio)

    def _flip_image(self):
        if hasattr(self, "image_item"):
            t = self.image_item.transform()
            t.scale(-1, 1)
            self.image_item.setTransform(t)
            self.view.fitInView(self.image_item, Qt.KeepAspectRatio)

    def _crop_image(self):
        QMessageBox.information(self, "Crop Tool", "Crop feature coming soon!")

    def _fit_image(self):
        if hasattr(self, "image_item"):
            self.view.fitInView(self.image_item, Qt.KeepAspectRatio)
