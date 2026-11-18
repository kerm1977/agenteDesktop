"""Mini Agente Desktop - entrada principal."""
import faulthandler
import os
import sys
import traceback

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

# Anti-crash: vuelca errores nativos y excepciones a crash.log
_crash_log = open(os.path.join(APP_DIR, "crash.log"), "a",
                  encoding="utf-8")
faulthandler.enable(_crash_log)


def _excepthook(t, v, tb):
    txt = "".join(traceback.format_exception(t, v, tb))
    try:
        _crash_log.write("\n=== EXCEPCION ===\n" + txt)
        _crash_log.flush()
        from core import consola
        consola.log_error("crash", txt)
    except Exception:
        pass
    sys.__excepthook__(t, v, tb)


sys.excepthook = _excepthook

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
