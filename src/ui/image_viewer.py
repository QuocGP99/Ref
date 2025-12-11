import os
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QGraphicsView, QGraphicsScene, QMessageBox
)
from PySide6.QtGui import QPixmap, QPainter, QTransform
from PySide6.QtCore import Qt, QRectF
from ..backend.database_manager import get_session, Photo
from .inspector_panel import InspectorPanel


class ZoomGraphicsView(QGraphicsView):
    """View hỗ trợ zoom bằng chuột"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        factor = 1.1 if angle > 0 else 0.9
        self.scale(factor, factor)


class ImageViewer(QDialog):
    """Viewer + Inspector Panel (ORM MySQL version)"""

    def __init__(self, photos, start_index=0, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.photos = photos
        self.index = start_index
        self.setWindowTitle("Ref Viewer")

        self.session = get_session()
        self.view = ZoomGraphicsView()
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)

        self._build_ui()
        self.load_current()

    # --------------------------------------------------------
    # BUILD UI
    # --------------------------------------------------------
    def _build_ui(self):
        layout = QHBoxLayout(self)

        # LEFT: Image View + Toolbar + Nav
        view_layout = QVBoxLayout()
        view_layout.addWidget(self.view)

        # --- Toolbar ---
        tool_layout = QHBoxLayout()
        btn_rotate = QPushButton("⟳ Rotate")
        btn_rotate.clicked.connect(self.rotate_image)
        tool_layout.addWidget(btn_rotate)

        btn_flip = QPushButton("⇋ Flip")
        btn_flip.clicked.connect(self.flip_image)
        tool_layout.addWidget(btn_flip)

        btn_crop = QPushButton("✂ Crop")
        btn_crop.clicked.connect(self.crop_image)
        tool_layout.addWidget(btn_crop)

        self.btn_fit = QPushButton("Fit to Window")
        self.btn_fit.setCheckable(True)
        self.btn_fit.setChecked(True)
        self.btn_fit.toggled.connect(self.toggle_fit_to_window)
        tool_layout.addWidget(self.btn_fit)
        tool_layout.addStretch()
        view_layout.addLayout(tool_layout)

        # --- Navigation ---
        nav_layout = QHBoxLayout()
        btn_prev = QPushButton("◀ Prev")
        btn_next = QPushButton("Next ▶")
        btn_prev.clicked.connect(self.show_prev)
        btn_next.clicked.connect(self.show_next)
        nav_layout.addWidget(btn_prev)
        nav_layout.addWidget(btn_next)
        view_layout.addLayout(nav_layout)

        # RIGHT: Inspector
        photo_id, _ = self.photos[self.index]
        self.meta = self.load_photo_meta(photo_id)
        self.inspector = InspectorPanel(self.meta)
        self.inspector.btn_save.clicked.connect(self.save_note)

        layout.addLayout(view_layout, 4)
        layout.addWidget(self.inspector, 2)
        self.resize(1200, 800)
        self.setFocus()

    # --------------------------------------------------------
    # LOAD & DISPLAY IMAGE
    # --------------------------------------------------------
    def load_current(self):
        photo_id, path = self.photos[self.index]
        self.scene.clear()

        # ✅ Kiểm tra file tồn tại trước khi mở
        if not os.path.exists(path):
            QMessageBox.warning(self, "Missing File", f"File not found:\n{path}")
            return

        pix = QPixmap(path)
        if pix.isNull():
            QMessageBox.warning(self, "Invalid Image", f"Cannot open image:\n{path}")
            return

        item = self.scene.addPixmap(pix)
        self.scene.setSceneRect(QRectF(pix.rect()))
        self.view.fitInView(item, Qt.KeepAspectRatio)
        self.setWindowTitle(f"Ref Viewer ({self.index + 1}/{len(self.photos)})")

        # Reload metadata
        self.meta = self.load_photo_meta(photo_id)
        self.inspector.meta = self.meta
        self.inspector.load_data()


    # --------------------------------------------------------
    # ORM METADATA HANDLING
    # --------------------------------------------------------
    def load_photo_meta(self, photo_id):
        """Lấy metadata từ ORM"""
        return self.session.query(Photo).get(photo_id)

    def save_note(self):
        """Lưu metadata từ Inspector panel"""
        data = self.inspector.get_metadata()
        photo_id, _ = self.photos[self.index]
        photo = self.session.query(Photo).get(photo_id)
        if not photo:
            return

        # Gán lại giá trị từ form
        for key, value in data.items():
            if hasattr(photo, key):
                setattr(photo, key, value)

        self.session.commit()
        QMessageBox.information(self, "Saved", "Metadata updated successfully!")

    # --------------------------------------------------------
    # KEYBOARD NAVIGATION
    # --------------------------------------------------------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.show_prev()
        elif event.key() == Qt.Key_Right:
            self.show_next()
        elif event.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.close()

    # --------------------------------------------------------
    # NEXT / PREV
    # --------------------------------------------------------
    def show_prev(self):
        self.index = (self.index - 1) % len(self.photos)
        self.load_current()

    def show_next(self):
        self.index = (self.index + 1) % len(self.photos)
        self.load_current()

    # --------------------------------------------------------
    # IMAGE TOOLS
    # --------------------------------------------------------
    def rotate_image(self):
        """Rotate image 90 degrees clockwise."""
        items = self.scene.items()
        if not items:
            return
        item = items[0]
        transform = item.transform()
        transform.rotate(90)
        item.setTransform(transform)
        self.view.fitInView(item, Qt.KeepAspectRatio)

    def flip_image(self):
        """Flip image horizontally."""
        items = self.scene.items()
        if not items:
            return
        item = items[0]
        transform = item.transform()
        transform.scale(-1, 1)
        item.setTransform(transform)
        self.view.fitInView(item, Qt.KeepAspectRatio)

    def crop_image(self):
        """Placeholder crop tool."""
        QMessageBox.information(self, "Crop Tool", "Crop tool will be implemented in Phase 3.")

    def toggle_fit_to_window(self, checked):
        items = self.scene.items()
        if not items:
            return
        item = items[0]
        if checked:
            self.view.fitInView(item, Qt.KeepAspectRatio)
        else:
            self.view.resetTransform()
