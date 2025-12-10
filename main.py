from PySide6.QtWidgets import QApplication
from src.backend.db import init_db
from src.ui.main_window import MainWindow
from src.services.import_service import import_folder
from src.backend.db import migrate
import sys




def run():
    init_db()
    migrate()

    # import_folder("data/images")

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
