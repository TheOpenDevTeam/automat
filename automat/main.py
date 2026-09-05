import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from config import APP_NAME


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    from app import AutomatApp
    window = AutomatApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
