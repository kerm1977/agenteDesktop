"""Mini Agente Desktop - entrada principal."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from core import ollama


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Mini Agente Desktop")
    app.setOrganizationName("kerm1977")
    ollama.ensure_running()
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
