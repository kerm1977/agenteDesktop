"""Flujo de actualización OTA: diálogo con barra + mini consola."""
import os
import subprocess
import sys

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
                               QMessageBox, QPlainTextEdit, QProgressBar,
                               QPushButton, QVBoxLayout)

from core import consola, ota

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DownloadWorker(QThread):
    line = Signal(str, bool)   # texto, es_error
    pct = Signal(int, int)
    done = Signal(dict)

    def __init__(self, manifest):
        super().__init__()
        self._manifest = manifest

    def run(self):
        def tick(i, total, rel):
            self.pct.emit(i, total)
            self.line.emit(rel, False)
        out = ota.download_update(self._manifest, progress=tick)
        self.done.emit(out)


class UpdateDialog(QDialog):
    """Modal de descarga: barra de progreso + mini consola + copiar."""

    def __init__(self, manifest, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Descargando actualización")
        self.setMinimumWidth(430)
        self.setStyleSheet(
            "QDialog{background:#202024;color:#e2e2e6;}"
            "QProgressBar{background:#232329;border:1px solid #3a3a42;"
            "border-radius:5px;height:14px;text-align:center;font-size:10px;}"
            "QProgressBar::chunk{background:#2e7fb8;}"
            "QPlainTextEdit{background:#1b1b1f;color:#c8c8ce;border:1px solid "
            "#3a3a42;font-family:Consolas;font-size:11px;}"
            "QPushButton{background:#34343c;color:#ddd;border:none;"
            "border-radius:5px;padding:5px 12px;}")
        lay = QVBoxLayout(self)
        self._manifest = manifest
        self._result = None

        self._lbl = QLabel("Preparando descarga…")
        lay.addWidget(self._lbl)
        self.bar = QProgressBar()
        lay.addWidget(self.bar)

        self.mini = QPlainTextEdit()
        self.mini.setReadOnly(True)
        self.mini.setMaximumBlockCount(200)
        self.mini.setFixedHeight(64)  # ~3-4 líneas visibles
        lay.addWidget(self.mini)

        row = QHBoxLayout()
        row.addStretch(1)
        self._btn_copy = QPushButton("Copiar")
        self._btn_copy.clicked.connect(
            lambda: QApplication.clipboard().setText(self.mini.toPlainText()))
        row.addWidget(self._btn_copy)
        self._btn_close = QPushButton("Cerrar")
        self._btn_close.clicked.connect(self.accept)
        self._btn_close.setEnabled(False)
        row.addWidget(self._btn_close)
        lay.addLayout(row)

        self._w = DownloadWorker(manifest)
        self._w.line.connect(self._log)
        self._w.pct.connect(self._tick)
        self._w.done.connect(self._fin)
        self._w.start()

    def _log(self, text, error=False):
        self.mini.appendHtml(
            ("<span style='color:#e06c60'>" if error
             else "<span style='color:#8a8a94'>") + text + "</span>")

    def _tick(self, i, total):
        self.bar.setMaximum(total)
        self.bar.setValue(i)
        self._lbl.setText(f"Descargando… {i}/{total}")

    def _fin(self, out):
        self._result = out
        for e in out["errores"]:
            self._log(e, error=True)
        ok = not out["errores"]
        self._lbl.setText(
            f"Descargados {out['descargados']} archivos." if ok
            else f"Completó con {len(out['errores'])} errores.")
        self._log("Descarga finalizada.", not ok)
        self._btn_close.setEnabled(True)


def check_and_prompt(parent, chat, manual=False):
    """Revisa actualizaciones; descarga y ofrece reiniciar si las hay."""
    res = ota.check_update()
    if not res["ok"]:
        consola.log_error("ota", res["error"])
        if manual:
            if res.get("sin_repo"):
                chat.add_system(
                    "El repo de la app aún no existe o es privado en GitHub; "
                    "publícalo para activar el auto-updater.")
            else:
                chat.add_system("Sin conexión al repositorio de "
                                "actualizaciones.")
        return
    if not ota.hay_version_nueva(res["actual"], res["remota"]):
        if manual:
            chat.add_system(
                f"Ya estás en la última versión ({res['actual']}).")
        return
    msg = (f"Actualización {res['actual']} → {res['remota']} "
           f"({len(res['archivos'])} archivos). ¿Descargar y aplicar?")
    if QMessageBox.question(parent, "Actualización",
                            msg) != QMessageBox.Yes:
        return
    dlg = UpdateDialog(res["manifest"], parent)
    dlg.exec()
    out = dlg._result or {"descargados": 0, "errores": ["interrumpido"]}
    if out["errores"]:
        for e in out["errores"]:
            consola.log_error("ota", e)
        return
    ans = QMessageBox.question(parent, "Actualización lista",
                               "Descargada. ¿Reiniciar ahora para aplicarla?")
    if ans == QMessageBox.Yes:
        updater = os.path.join(APP_DIR, "core", "updater.py")
        subprocess.Popen(
            [sys.executable, updater, os.path.join(APP_DIR, "app.py")],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        QApplication.quit()
