from PySide6.QtWidgets import QApplication
from src.ui.welcome_window import WelcomeWindow
from src.ui.main_window import MainWindow

def run():
    app = QApplication([])

    def open_project(folder):
        app.win = MainWindow(folder)  
        app.win.show()

    welcome = WelcomeWindow(on_project_selected=open_project)
    welcome.show()

    app.exec()


if __name__ == "__main__":
    run()
