from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QInputDialog, QMessageBox, QMenu
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt

from src.backend.database_manager import get_session, Folder, delete_folder_permanently
from src.backend.project_manager import get_current_project_path


# ========== NAV BUTTON ==========
class NavButton(QPushButton):
    def __init__(self, text, icon=None, parent=None):
        super().__init__(text, parent)
        if icon:
            self.setIcon(QIcon(icon))
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 14px;
                border-radius: 6px;
                border: none;
                background: transparent;
                color: #333;
                font-size: 14px;
                transition: all 0.2s ease-in-out;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:checked {
                background-color: #d0e2ff;
                color: #0055ff;
                font-weight: 600;
            }
        """)


# ========== FOLDER BUTTON ==========
class FolderButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 14px;
                border-radius: 6px;
                border: none;
                background: transparent;
                color: #333;
                font-size: 14px;
                transition: all 0.2s ease-in-out;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:checked {
                background-color: #d0e2ff;
                color: #0055ff;
                font-weight: 600;
            }
        """)


# ========== SIDEBAR ==========
class Sidebar(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.session = get_session()
        self.setFixedWidth(220)
        self.setStyleSheet("background: #f6f6f6; border-right: 1px solid #ddd;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Title
        title = QLabel("Ref Library")
        title.setStyleSheet("font-size:18px; font-weight:bold; color:#222;")
        layout.addWidget(title)
        layout.addSpacing(8)

        # Navigation buttons
        self.btn_all = NavButton("All Photos", "assets/icons/all.svg")
        self.btn_all.clicked.connect(lambda: self._set_active_button(self.btn_all, "all"))
        layout.addWidget(self.btn_all)

        self.btn_fav = NavButton("Favorites", "assets/icons/favorite.svg")
        self.btn_fav.clicked.connect(lambda: self._set_active_button(self.btn_fav, "favorites"))
        layout.addWidget(self.btn_fav)

        self.btn_trash = NavButton("Trash", "assets/icons/trash.svg")
        self.btn_trash.clicked.connect(lambda: self._set_active_button(self.btn_trash, "trash"))
        layout.addWidget(self.btn_trash)

        layout.addSpacing(16)
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #ddd;")
        layout.addWidget(divider)

        # Folders Section
        lbl = QLabel("Folders")
        lbl.setStyleSheet("font-size:13px; color:#555; font-weight:600;")
        layout.addWidget(lbl)

        from PySide6.QtWidgets import QWidget as _W, QVBoxLayout as _V
        container = _W()
        self.folder_container = _V(container)
        self.folder_container.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        btn_add = QPushButton("+ Add Folder")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                text-align:left;
                border:none;
                color:#0055ff;
                font-weight:600;
                background: transparent;
            }
            QPushButton:hover {
                text-decoration: underline;
                background-color: #e8f0ff;
            }
        """)
        btn_add.clicked.connect(self.add_folder)
        layout.addWidget(btn_add)
        layout.addStretch()

        self.nav_buttons = [self.btn_all, self.btn_fav, self.btn_trash]
        self.refresh_folders()

    # -------------------------------------------------------
    def _set_active_button(self, active_btn, target_view):
        """Kích hoạt nav button và thay đổi nội dung chính."""
        for btn in self.nav_buttons:
            btn.setChecked(False)
        for fbtn in getattr(self, "folder_buttons", []):
            fbtn.setChecked(False)

        active_btn.setChecked(True)

        if target_view == "all":
            self.main_window.current_view = "all"
            self.main_window.show_all()
        elif target_view == "favorites":
            self.main_window.current_view = "favorites"
            self.main_window.show_favorites()
        elif target_view == "trash":
            self.main_window.current_view = "trash"
            self.main_window.show_trash()

    # -------------------------------------------------------
    def refresh_folders(self):
        """Reload danh sách thư mục từ DB."""
        self.session.expire_all()

        while self.folder_container.count():
            item = self.folder_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        folders = self.session.query(Folder).order_by(Folder.name.asc()).all()
        self.folder_buttons = []

        for f in folders:
            btn = FolderButton(f.name)
            btn.setIcon(QIcon("assets/icons/folder.png"))
            btn.original_text = f.name
            btn.clicked.connect(lambda checked=False, fid=f.id, b=btn: self.on_folder_clicked(fid, b))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, fid=f.id: self.show_folder_context_menu(fid))
            self.folder_buttons.append(btn)
            self.folder_container.addWidget(btn)

    # -------------------------------------------------------
    def on_folder_clicked(self, folder_id, button):
        """Click chọn folder để hiển thị ảnh tương ứng."""
        for nav in self.nav_buttons:
            nav.setChecked(False)
        for fbtn in getattr(self, "folder_buttons", []):
            fbtn.setChecked(False)

        button.setChecked(True)
        self.main_window.current_view = f"folder_{folder_id}"
        self.main_window.show_folder(folder_id)

    # -------------------------------------------------------
    def show_folder_context_menu(self, folder_id):
        """Hiển thị menu chuột phải."""
        menu = QMenu()
        act_rename = QAction("Rename")
        act_delete = QAction("Delete")

        act_rename.triggered.connect(lambda: self.rename_folder(folder_id))
        act_delete.triggered.connect(lambda: self.delete_folder(folder_id))

        menu.addAction(act_rename)
        menu.addAction(act_delete)
        menu.exec_(QtGui.QCursor.pos())

    # -------------------------------------------------------
    def rename_folder(self, folder_id):
        """Đổi tên thư mục."""
        folder = self.session.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            return

        new_name, ok = QInputDialog.getText(self, "Rename Folder", "New name:", text=folder.name)
        if ok and new_name.strip():
            folder.name = new_name.strip()
            self.session.commit()
            self.refresh_folders()

    # -------------------------------------------------------
    def delete_folder(self, folder_id):
        """Xóa thư mục."""
        reply = QMessageBox.question(self, "Confirm Delete", "Delete this folder?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            delete_folder_permanently(folder_id)
            self.refresh_folders()

    # -------------------------------------------------------
    def add_folder(self):
        """Thêm thư mục mới."""
        name, ok = QInputDialog.getText(self, "Add Folder", "Folder name:")
        if ok and name.strip():
            folder = Folder(name=name.strip(), path=get_current_project_path())
            self.session.add(folder)
            self.session.commit()
            self.refresh_folders()
