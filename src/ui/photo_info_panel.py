from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QFormLayout,
    QPushButton, QLineEdit, QComboBox, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap, QPainter
from ..backend.database_manager import get_session, Photo
from colorthief import ColorThief
from PIL import Image
import os


class PhotoInfoPanel(QWidget):
    """
    Panel hiển thị thông tin chi tiết ảnh:
    - Click 1 lần trong gallery: hiển thị info panel này
    - Gồm: 5 màu chính, notes, tags, folder, exif, rating, dates
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = get_session()
        self.photo = None
        self._build_ui()
        self.hide()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.title = QLabel("Photo Info")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(self.title)

        # 🎨 Màu sắc chính trong ảnh
        self.color_layout = QHBoxLayout()
        layout.addLayout(self.color_layout)

        # Thông tin cơ bản
        self.form = QFormLayout()
        self.lbl_folder = QLabel()
        self.lbl_size = QLabel()
        self.lbl_dimensions = QLabel()
        self.lbl_type = QLabel()
        self.lbl_iso = QLabel()
        self.lbl_focal = QLabel()
        self.lbl_shutter = QLabel()
        self.lbl_created = QLabel()
        self.lbl_imported = QLabel()
        self.lbl_modified = QLabel()

        # ⭐ Rating
        self.cmb_rating = QComboBox()
        self.cmb_rating.addItems(["", "1", "2", "3", "4", "5"])

        # 🏷️ Tags và Note
        self.txt_tags = QLineEdit()
        self.txt_note = QTextEdit()

        # 🧩 Form layout
        self.form.addRow("Folder:", self.lbl_folder)
        self.form.addRow("Rating:", self.cmb_rating)
        self.form.addRow("Tags:", self.txt_tags)
        self.form.addRow("Notes:", self.txt_note)
        self.form.addRow("Dimensions:", self.lbl_dimensions)
        self.form.addRow("Size:", self.lbl_size)
        self.form.addRow("Type:", self.lbl_type)
        self.form.addRow("ISO:", self.lbl_iso)
        self.form.addRow("Shutter:", self.lbl_shutter)
        self.form.addRow("Focal:", self.lbl_focal)
        self.form.addRow("Date Imported:", self.lbl_imported)
        self.form.addRow("Date Created:", self.lbl_created)
        self.form.addRow("Date Modified:", self.lbl_modified)

        layout.addLayout(self.form)

        # 💾 Nút lưu
        self.btn_save = QPushButton("💾 Save Info")
        self.btn_save.clicked.connect(self._save_metadata)
        layout.addWidget(self.btn_save)
        layout.addStretch()

        # 💠 Style
        self.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #333;
            }
            QLineEdit, QTextEdit, QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 3px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #2d89ef;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e5fb4;
            }
        """)

    # ------------------------------------------------------------------
    # LOAD THÔNG TIN ẢNH
    # ------------------------------------------------------------------
    def load_photo_info(self, photo_id: int):
        self.photo = self.session.get(Photo, photo_id)
        if not self.photo:
            self.title.setText("Photo not found")
            return

        path = self.photo.file_path
        self.title.setText(os.path.basename(path))

        # Folder
        self.lbl_folder.setText(
            str(self.photo.folder.name if getattr(self.photo, "folder", None) else "Add Category")
        )

        # Thông tin file
        self.lbl_size.setText(self._get_file_size(path))
        self.lbl_dimensions.setText(self._get_dimensions(path))
        self.lbl_type.setText(os.path.splitext(path)[-1].upper())

        # EXIF
        self.lbl_iso.setText(str(getattr(self.photo, "exif_iso", "")))
        self.lbl_focal.setText(str(getattr(self.photo, "exif_focal_length", "")))
        self.lbl_shutter.setText(str(getattr(self.photo, "exif_shutter_speed", "")))

        # Date
        self.lbl_created.setText(str(getattr(self.photo, "date_created", "")))
        self.lbl_imported.setText(str(getattr(self.photo, "date_imported", "")))
        self.lbl_modified.setText(str(getattr(self.photo, "date_modified", "")))

        # Rating, tags, note
        self.cmb_rating.setCurrentText(str(self.photo.rating or ""))
        self.txt_tags.setText(self.photo.tags or "")
        self.txt_note.setText(self.photo.note or "")

        # 🎨 Palette màu
        self._load_color_palette(path)

        self.show()

    def _load_color_palette(self, path):
        """Tạo 5 chấm màu đại diện cho ảnh."""
        for i in reversed(range(self.color_layout.count())):
            w = self.color_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not os.path.exists(path):
            return
        try:
            color_thief = ColorThief(path)
            palette = color_thief.get_palette(color_count=5)
            for rgb in palette:
                dot = QLabel()
                dot.setFixedSize(24, 24)
                dot.setStyleSheet(
                    f"background-color: rgb{rgb}; border-radius: 12px; border: 1px solid #999;"
                )
                self.color_layout.addWidget(dot)
        except Exception as e:
            print(f"[WARN] Color extract failed: {e}")

    # ------------------------------------------------------------------
    # SAVE DỮ LIỆU
    # ------------------------------------------------------------------
    def _save_metadata(self):
        if not self.photo:
            return
        try:
            self.photo.rating = int(self.cmb_rating.currentText() or 0)
            self.photo.tags = self.txt_tags.text()
            self.photo.note = self.txt_note.toPlainText()
            self.session.commit()
            print(f"[INFO] Saved photo {self.photo.id} metadata.")
        except Exception as e:
            print(f"[ERROR] Save metadata failed: {e}")
            self.session.rollback()

    # ------------------------------------------------------------------
    # HELPER
    # ------------------------------------------------------------------
    def _get_file_size(self, path):
        try:
            size = os.path.getsize(path)
            return f"{size / (1024*1024):.2f} MB"
        except Exception:
            return "N/A"

    def _get_dimensions(self, path):
        try:
            with Image.open(path) as img:
                return f"{img.width}×{img.height}"
        except Exception:
            return "N/A"
