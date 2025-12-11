from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QFormLayout, QPushButton, QComboBox, QLineEdit
)


class InspectorPanel(QWidget):
    """
    Panel metadata + note + EXIF
    Tự động nhận Photo ORM hoặc dict
    """

    def __init__(self, meta=None, parent=None):
        super().__init__(parent)
        self.meta = meta
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # --- EXIF ---
        self.lbl_iso = QLabel()
        self.lbl_focal = QLabel()
        self.lbl_aperture = QLabel()
        self.lbl_shutter = QLabel()

        form.addRow("ISO:", self.lbl_iso)
        form.addRow("Focal:", self.lbl_focal)
        form.addRow("Aperture:", self.lbl_aperture)
        form.addRow("Shutter:", self.lbl_shutter)

        layout.addLayout(form)

        # --- Metadata ---
        self.cmb_category = QComboBox()
        self.cmb_category.addItems(["", "Kỷ yếu", "Cưới", "Portrait", "Concept"])

        self.cmb_lens = QComboBox()
        self.cmb_lens.addItems([
            "", "RF 35mm f1.8", "RF 16-35mm f2.8",
            "RF 85mm f1.8", "EF 50mm f1.8", "EF 24-70mm f2.8",
        ])

        self.cmb_style = QComboBox()
        self.cmb_style.addItems(["", "Outdoor", "Indoor", "Backlight", "Portrait"])

        self.cmb_lighting = QComboBox()
        self.cmb_lighting.addItems(["", "Side Light", "Back Light", "Front Fill", "Rembrandt"])

        self.txt_tags = QLineEdit()

        form.addRow("Category:", self.cmb_category)
        form.addRow("Lens:", self.cmb_lens)
        form.addRow("Style:", self.cmb_style)
        form.addRow("Lighting:", self.cmb_lighting)
        form.addRow("Tags:", self.txt_tags)

        layout.addWidget(QLabel("Notes:"))
        self.txt_note = QTextEdit()
        layout.addWidget(self.txt_note)

        self.btn_save = QPushButton("Save Note")
        layout.addWidget(self.btn_save)
        layout.addStretch()

    def _get_value(self, attr_name, default=None):
        """Hàm hỗ trợ ORM hoặc dict"""
        if self.meta is None:
            return default
        if hasattr(self.meta, attr_name):
            return getattr(self.meta, attr_name, default)
        if isinstance(self.meta, dict):
            return self.meta.get(attr_name, default)
        return default

    def load_data(self):
        """Load dữ liệu EXIF + note từ meta"""
        iso = self._get_value("exif_iso")
        focal = self._get_value("exif_focal_length")
        aperture = self._get_value("exif_aperture")
        shutter = self._get_value("exif_shutter_speed")
        note = self._get_value("note")
        tags = self._get_value("tags")

        focal_txt = f"{focal}mm" if focal else ""
        aperture_txt = f"f/{aperture}" if aperture else ""
        shutter_txt = ""
        if shutter:
            try:
                inv = 1 / float(shutter)
                shutter_txt = f"1/{int(inv)}"
            except Exception:
                shutter_txt = str(shutter)

        self.lbl_iso.setText(str(iso or ""))
        self.lbl_focal.setText(focal_txt)
        self.lbl_aperture.setText(aperture_txt)
        self.lbl_shutter.setText(shutter_txt)
        self.txt_note.setText(str(note or ""))
        self.txt_tags.setText(str(tags or ""))

    def get_metadata(self):
        return {
            "category": self.cmb_category.currentText(),
            "lens": self.cmb_lens.currentText(),
            "style": self.cmb_style.currentText(),
            "lighting": self.cmb_lighting.currentText(),
            "tags": self.txt_tags.text(),
            "note": self.txt_note.toPlainText(),
        }
