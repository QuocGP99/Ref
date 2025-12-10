from pathlib import Path
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGraphicsView,
    QGraphicsScene,
)
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt, QRectF
from ..backend.db import get_conn
from .inspector_panel import InspectorPanel

class ZoomGraphicsView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            angle = event.angleDelta().y()
            factor = 1.25 if angle > 0 else 0.8
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)


class ImageViewer(QDialog):
    """
    Viewer + Inspector panel
    """

    def __init__(self, photos, start_index=0, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.photos = photos
        self.index = start_index
        self.setWindowTitle("Ref Viewer")

        # ⚡ MUST CREATE BEFORE BUILD UI
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

        # LEFT: image + navigation
        view_layout = QVBoxLayout()
        view_layout.addWidget(self.view)

        nav_layout = QHBoxLayout()
        btn_prev = QPushButton("◀ Prev")
        btn_next = QPushButton("Next ▶")

        btn_prev.clicked.connect(self.show_prev)
        btn_next.clicked.connect(self.show_next)

        nav_layout.addWidget(btn_prev)
        nav_layout.addWidget(btn_next)

        view_layout.addLayout(nav_layout)

        # RIGHT: inspector
        photo_id, _ = self.photos[self.index]
        self.meta = self.load_photo_meta(photo_id)

        self.inspector = InspectorPanel(self.meta)
        self.inspector.btn_save.clicked.connect(self.save_note)

        layout.addLayout(view_layout, 4)
        layout.addWidget(self.inspector, 2)

        self.resize(1200, 800)

        self.setFocus()


    # --------------------------------------------------------
    # LOAD AND DISPLAY IMAGE
    # --------------------------------------------------------
    def load_current(self):
        photo_id, path = self.photos[self.index]
        self.scene.clear()

        pix = QPixmap(path)
        if pix.isNull():
            return

        item = self.scene.addPixmap(pix)
        self.scene.setSceneRect(QRectF(pix.rect()))
        self.view.fitInView(item, Qt.KeepAspectRatio)

        self.setWindowTitle(f"Ref Viewer ({self.index + 1}/{len(self.photos)})")

        # --- reload metadata cho Inspector mỗi lần đổi ảnh ---
        meta = self.load_photo_meta(photo_id)
        self.inspector.meta = meta
        self.inspector.load_data()

    # --------------------------------------------------------
    # DB METADATA
    # --------------------------------------------------------
    def load_photo_meta(self, photo_id):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                category,
                lens,
                style,
                lighting,
                tags,
                exif_iso,
                exif_focal_length,
                exif_aperture,
                exif_shutter_speed,
                notes
            FROM photo_metadata
            WHERE photo_id=?
            """,
            (photo_id,),
        )
        row = cur.fetchone()

        if not row:
            return {}

        (
            category,
            lens,
            style,
            lighting,
            tags,
            iso,
            focal,
            aperture,
            shutter,
            note,
        ) = row

        return {
            "category": category,
            "lens": lens,
            "style": style,
            "lighting": lighting,
            "tags": tags,
            "iso": iso,
            "focal": focal,
            "aperture": aperture,
            "shutter": shutter,
            "note": note,
        }

    # --------------------------------------------------------
    # SAVENOTE
    # --------------------------------------------------------
    def save_note(self):
        data = self.inspector.get_metadata()
        photo_id, _ = self.photos[self.index]

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE photo_metadata SET
                category=?, lens=?, style=?, lighting=?, tags=?, notes=?
            WHERE photo_id=?
        """, (
            data["category"],
            data["lens"],
            data["style"],
            data["lighting"],
            data["tags"],
            data["note"],
            photo_id
        ))
        conn.commit()

    # --------------------------------------------------------
    # KEYBOARD
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
