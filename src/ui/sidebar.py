from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QLineEdit, QInputDialog, QMenu, QMessageBox
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from ..backend.db import get_conn

class NavButton(QPushButton):
    def __init__(self, text, icon=None, parent=None):
        super().__init__(text, parent)

        if icon:
            self.setIcon(QIcon(icon))

        self.setCheckable(True)

        self.setStyleSheet("""
            NavButton {
                text-align: left;
                padding: 8px 14px;
                border-radius: 6px;
                border: none;
                background: transparent;
                color: #333;
                font-size: 14px;
            }
            NavButton:hover {
                background: #eaeaea;
            }
            NavButton:checked {
                background: #d0e2ff;
                color: #0055ff;
            }
        """)


class Sidebar(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setFixedWidth(220)
        self.setStyleSheet("""
            background: #f6f6f6;
            border-right: 1px solid #ddd;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header title
        title = QLabel("Ref Library")
        title.setStyleSheet("""
            font-size: 18px;
            color: #222;
            font-weight: bold;
            margin-bottom: 6px;
        """)
        layout.addWidget(title)

        layout.addSpacing(6)

        # Navigation items (system)
        self.btn_all = NavButton("All Photos")
        self.btn_all.setIcon(QIcon("assets/icons/all.svg"))
        self.btn_all.clicked.connect(lambda: self.main_window.show_all())

        self.btn_fav = NavButton("Favorites")
        self.btn_fav.setIcon(QIcon("assets/icons/favorite.svg"))
        self.btn_fav.clicked.connect(lambda: self.main_window.show_favorites())
        
        self.btn_trash = NavButton("Trash")
        self.btn_trash.setIcon(QIcon("assets/icons/trash.svg"))
        self.btn_trash.clicked.connect(self.main_window.show_trash)


        layout.addWidget(self.btn_all)
        layout.addWidget(self.btn_fav)
        layout.addWidget(self.btn_trash)

        layout.addSpacing(20)

        #Collapse
        self.btn_toogle = QPushButton("<-")
        self.btn_toogle.setFixedSize(30,30)
        self.btn_toogle.clicked.connect(self.toggle_sidebar)
        layout.addWidget(self.btn_toogle, alignment=Qt.AlignRight)

        # Section divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #ddd;")
        layout.addWidget(divider)

        # Folder Title
        lbl_folders = QLabel("Folders")
        lbl_folders.setStyleSheet("font-size: 13px;color:#555;font-weight:600;")
        layout.addWidget(lbl_folders)

        # Folder list container
        folder_widget = QWidget()
        self.folder_container = QVBoxLayout(folder_widget)
        self.folder_container.setContentsMargins(0, 0, 0, 0)
        self.folder_container.setSpacing(2)

        layout.addWidget(folder_widget)
        
        btn_add = QPushButton("+ Add Folder")
        btn_add.setStyleSheet("text-align:left;border:none;color:#0055ff;")
        btn_add.clicked.connect(self.add_folder)
        layout.addWidget(btn_add)

        btn_add_photo = QPushButton("+ Add Photo")
        btn_add_photo.clicked.connect(lambda: self.main_window.add_photo_to_folder())
        layout.addWidget(btn_add_photo)


        layout.addStretch()

        # Load folder từ DB
        self.refresh_folders()


    def load_folders(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM folders ORDER BY name ASC")
        return cur.fetchall()

    def refresh_folders(self):
        while self.folder_container.count():
            item = self.folder_container.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        folders = self.load_folders()
        print("DEBUG FOLDERS:", folders)

        # Reset danh sách button (để hỗ trợ collapse)
        self.folder_buttons = []

        # Add từng button
        for folder_id, folder_name in folders:
            btn = NavButton(folder_name)
            btn.original_text = folder_name

            # add icon folder
            btn.setIcon(QIcon("assets/icons/folder.png"))

            btn.clicked.connect(lambda checked, fid=folder_id: self.on_folder_clicked(fid))

            self.folder_buttons.append(btn)
            self.folder_container.addWidget(btn)


    def on_folder_clicked(self, folder_id):
        self.main_window.show_folder(folder_id)

    def add_folder(self):
        name, ok = QInputDialog.getText(self, "New folder", "Folder name:")
        if not ok or not name:
            return

        from ..backend.db import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO folders(name) VALUES(?)", (name,))
        conn.commit()

        self.refresh_folders()

    def toggle_sidebar(self):
        if self.width() > 60:
            self.setFixedWidth(60)
            self.set_icon_only(True)
        else:
            self.setFixedWidth(250)
            self.set_icon_only(False)

    def set_icon_only(self, flag):
        for btn in self.folder_buttons:
            if flag:
                btn.setText("")
            else:
                btn.setText(btn.original_text)

    def contextMenuEvent(self, event):
        item = self.childAt(event.pos())
        if not item:
            return

        # Tìm button folder được click
        for btn in self.folder_buttons:
            if btn.underMouse():
                folder_name = btn.original_text
                folder_id = self._get_folder_id_by_name(folder_name)
                self._show_folder_context_menu(folder_id, event.globalPos())
                return


    def _get_folder_id_by_name(self, name):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM folders WHERE name=?", (name,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None


    def _show_folder_context_menu(self, folder_id, pos):
        menu = QMenu(self)

        act_rename = QAction("Rename Folder", self)
        act_rename.triggered.connect(lambda: self._rename_folder(folder_id))
        menu.addAction(act_rename)

        act_delete = QAction("Delete Folder", self)
        act_delete.triggered.connect(lambda: self._delete_folder(folder_id))
        menu.addAction(act_delete)

        menu.exec(pos)


    def _rename_folder(self, folder_id):
        from PySide6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, "Rename Folder", "New name:")
        if not ok or not new_name.strip():
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE folders SET name=? WHERE id=?", (new_name, folder_id))
        conn.commit()
        conn.close()
        self.refresh_folders()


    def _delete_folder(self, folder_id):
        from PySide6.QtWidgets import QMessageBox
        from ..backend.db import delete_folder

        reply = QMessageBox.question(
            self,
            "Delete Folder",
            "Do you really want to delete this folder and all its photos?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_folder(folder_id)
            self.refresh_folders()

