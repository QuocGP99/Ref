from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog


class WelcomeWindow(QWidget):
    def __init__(self, on_project_selected=None, parent=None):
        super().__init__(parent)
        self.on_project_selected = on_project_selected
        self.setWindowTitle("Welcome to Ref")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        lbl = QLabel("Ref – Photo Reference Library\n\nCreate or open a project folder")
        layout.addWidget(lbl)

        btn_new = QPushButton("Create / Select Project Folder")
        btn_new.clicked.connect(self.open_folder_dialog)
        layout.addWidget(btn_new)

        layout.addStretch()

    def open_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Root")
        if folder and self.on_project_selected:
            self.on_project_selected(folder)
            self.close()
