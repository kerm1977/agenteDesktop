"""Panel de modelos: instalados, descarga (pull) y carpeta de modelos."""
import os
import subprocess

from PySide6.QtCore import QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QPushButton, QVBoxLayout, QWidget)

from core import backends, consola, ollama


class PullWorker(QThread):
    line = Signal(str)
    done = Signal(int)

    def __init__(self, name):
        super().__init__()
        self._name = name

    def run(self):
        env = dict(os.environ)
        env["OLLAMA_MODELS"] = ollama.MODELS_DIR
        try:
            proc = subprocess.Popen(
                [ollama._ollama_exe(), "pull", self._name],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, env=env, errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            for ln in proc.stdout:
                self.line.emit(ln.strip())
            self.done.emit(proc.wait())
        except Exception as e:
            self.line.emit("error: " + repr(e))
            self.done.emit(1)


class ModelsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        self.setStyleSheet(
            "QWidget{background:#18181a;color:#ddd;}"
            "QListWidget{background:#131314;border:1px solid #2c2c30;}"
            "QLineEdit{background:#131314;border:1px solid #2c2c30;"
            "border-radius:4px;padding:4px;color:#ddd;}"
            "QPushButton{background:#0e639c;color:#fff;border:none;"
            "border-radius:4px;padding:5px 10px;}"
            "QPushButton:disabled{background:#2a2a2e;color:#666;}")

        lay.addWidget(QLabel("Modelos instalados"))
        self._list = QListWidget()
        lay.addWidget(self._list, 1)

        row = QHBoxLayout()
        self._inp = QLineEdit()
        self._inp.setPlaceholderText("ej. qwen2.5-coder:3b")
        self._btn = QPushButton("Descargar")
        row.addWidget(self._inp, 1)
        row.addWidget(self._btn)
        lay.addLayout(row)

        row2 = QHBoxLayout()
        btn_dir = QPushButton("📁 Carpeta de modelos")
        btn_dir.setStyleSheet("background:#2a2a2e;")
        btn_dir.clicked.connect(self._open_dir)
        btn_ref = QPushButton("↻")
        btn_ref.setStyleSheet("background:#2a2a2e;")
        btn_ref.clicked.connect(self.refresh)
        row2.addWidget(btn_dir, 1)
        row2.addWidget(btn_ref)
        lay.addLayout(row2)

        self._status = QLabel("Carpeta: " + ollama.MODELS_DIR)
        self._status.setWordWrap(True)
        self._status.setStyleSheet("color:#888;font-size:10px;")
        lay.addWidget(self._status)

        self._worker = None
        self._btn.clicked.connect(self._pull)
        self.refresh()

    def refresh(self):
        self._list.clear()
        models = backends.list_models("ollama")
        self._list.addItems(models or ["(Ollama desconectado o sin modelos)"])

    def _pull(self):
        name = self._inp.text().strip()
        if not name or self._worker:
            return
        self._btn.setEnabled(False)
        self._status.setText("Descargando " + name + "…")
        self._worker = PullWorker(name)
        self._worker.line.connect(
            lambda ln: consola.log_info("pull", ln))
        self._worker.done.connect(self._pull_done)
        self._worker.start()

    def _pull_done(self, code):
        self._btn.setEnabled(True)
        self._status.setText(
            "Descarga completa." if code == 0 else f"Falló (exit {code}) — ver consola")
        self._worker = None
        self.refresh()

    def _open_dir(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(ollama.MODELS_DIR))
