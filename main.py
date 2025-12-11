from PySide6.QtWidgets import QApplication, QMessageBox
from src.ui.welcome_window import WelcomeWindow
from src.ui.main_window import MainWindow
from src.backend.database_manager import init_db, get_session


def run():
    app = QApplication([])

    # ✅ 1. Khởi tạo MySQL engine chỉ 1 lần
    db_url = "mysql+pymysql://root:qteovas2235@localhost/ref_app"  # ⚙️ Cập nhật user/pass thật
    try:
        init_db(db_url)
        print(f"[DB] ✅ Connected to MySQL database: {db_url}")
    except Exception as e:
        QMessageBox.critical(None, "Database Error", f"❌ Cannot connect to database.\n\n{str(e)}")
        return

    # ✅ 2. Tạo ORM session toàn cục
    session = get_session()

    # 📁 3. Khi chọn project, truyền session vào MainWindow
    def open_project(folder):
        try:
            app.win = MainWindow(folder)
            app.win.session = session  # ✅ Gán session dùng chung
            app.win.show()
        except Exception as e:
            QMessageBox.critical(None, "Project Error", f"❌ Cannot open project.\n\n{str(e)}")

    # 🏠 4. Mở cửa sổ Welcome
    welcome = WelcomeWindow(on_project_selected=open_project)
    welcome.show()

    app.exec()


if __name__ == "__main__":
    run()
