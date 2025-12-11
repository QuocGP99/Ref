from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from src.backend.project_manager import set_current_project_path


class WelcomeWindow(QWidget):
    def __init__(self, on_project_selected=None, parent=None):
        super().__init__(parent)
        self.on_project_selected = on_project_selected
        self.setWindowTitle("Welcome to Ref")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        lbl = QLabel("📁 Ref – Photo Reference Library\n\nCreate or open a project folder")
        lbl.setStyleSheet("font-size: 15px; padding: 8px; color: #333;")
        layout.addWidget(lbl)

        btn_new = QPushButton("Create / Select Project Folder")
        btn_new.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px 18px;
                background-color: #0066ff;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #3388ff;
            }
        """)
        btn_new.clicked.connect(self.open_folder_dialog)
        layout.addWidget(btn_new)

        layout.addStretch()

    def open_folder_dialog(self):
        """Open folder selection and initialize project path."""
        folder = QFileDialog.getExistingDirectory(self, "Select Project Root")

        if folder:
            # 🔥 Ghi nhớ project path để các module khác (gallery, db, import) sử dụng
            set_current_project_path(folder)

            # 🔥 Kích hoạt callback để mở project
            if self.on_project_selected:
                self.on_project_selected(folder)
                self.close()
