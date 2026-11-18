"""Flujo de actualización OTA con diálogos."""
import os
import subprocess
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QMessageBox, QProgressDialog)

from core import consola, ota

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_and_prompt(parent, chat, manual=False):
    """Revisa actualizaciones; descarga y ofrece reiniciar si las hay."""
    res = ota.check_update()
    if not res["ok"]:
        consola.log_error("ota", res["error"])
        if manual:
            if res.get("sin_repo"):
                chat.add_system(
                    "El repo 'agente-desktop' aún no existe en GitHub: créalo "
                    "desde la tarjeta de Devin y el auto-updater quedará listo.")
            else:
                chat.add_system("Sin conexión al repositorio de "
                                "actualizaciones.")
        return
    if not res["archivos"]:
        if manual:
            chat.add_system(f"Ya estás en la última versión ({res['actual']}).")
        return
    msg = (f"Hay actualización {res['actual']} → {res['remota']} "
           f"({len(res['archivos'])} archivos). ¿Descargar y aplicar?")
    if QMessageBox.question(parent, "Actualización",
                            msg) != QMessageBox.Yes:
        return
    prog = QProgressDialog("Descargando actualización…", "Cancelar", 0,
                           len(res["archivos"]), parent)
    prog.setWindowModality(Qt.WindowModal)

    def tick(i, total, rel):
        prog.setValue(i)
        if prog.wasCanceled():
            raise InterruptedError()

    out = ota.download_update(res["manifest"], progress=tick)
    prog.close()
    if out["errores"]:
        consola.log_error("ota", "; ".join(out["errores"]))
    ans = QMessageBox.question(parent, "Actualización lista",
                               "Descargada. ¿Reiniciar ahora para aplicarla?")
    if ans == QMessageBox.Yes:
        updater = os.path.join(APP_DIR, "core", "updater.py")
        subprocess.Popen(
            [sys.executable, updater, os.path.join(APP_DIR, "app.py")],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        QApplication.quit()
