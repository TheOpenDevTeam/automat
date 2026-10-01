import sys
from pathlib import Path

if __package__ in (None, ""):
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from automat.config import APP_NAME


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    from automat.app import AutomatApp
    window = AutomatApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
