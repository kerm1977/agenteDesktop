"""Diálogo 'Nuevo proyecto': crea una carpeta (vacía o plantilla Flask)."""
import os

from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox,
                               QFileDialog, QFormLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QVBoxLayout)

FLASK_APP = '''"""Sitio Flask generado por Mini Agente Desktop."""
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=7862)
'''

FLASK_HTML = """<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><title>Mi sitio</title>
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body><h1>Hola, mundo</h1></body>
</html>
"""

FLASK_CSS = "body { font-family: sans-serif; margin: 2rem; }\n"


class NuevoProyectoDialog(QDialog):
    def __init__(self, base_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo proyecto")
        self.setMinimumWidth(380)
        self.setStyleSheet(
            "QDialog{background:#202024;color:#e2e2e6;}"
            "QLineEdit,QComboBox{background:#2a2a30;color:#e2e2e6;"
            "border:1px solid #3a3a42;border-radius:5px;padding:5px;}"
            "QPushButton{background:#2e7fb8;color:#fff;border:none;"
            "border-radius:5px;padding:6px 14px;}")
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self._nombre = QLineEdit()
        self._nombre.setPlaceholderText("mi-proyecto")
        form.addRow("Nombre:", self._nombre)

        row = QHBoxLayout()
        self._dir = QLineEdit(base_dir)
        btn_dir = QPushButton("…")
        btn_dir.setFixedWidth(36)
        btn_dir.clicked.connect(self._pick_dir)
        row.addWidget(self._dir, 1)
        row.addWidget(btn_dir)
        form.addRow("Carpeta base:", row)

        self._plantilla = QComboBox()
        self._plantilla.addItems(["Vacío", "Sitio web Flask"])
        form.addRow("Plantilla:", self._plantilla)
        lay.addLayout(form)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self.ruta = None

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Carpeta base",
                                             self._dir.text())
        if d:
            self._dir.setText(d)

    def accept(self):
        nombre = self._nombre.text().strip()
        if not nombre:
            return
        self.ruta = os.path.join(self._dir.text().strip(), nombre)
        super().accept()


def crear_proyecto(ruta, plantilla):
    """Crea la carpeta y la estructura inicial. Devuelve la ruta."""
    os.makedirs(ruta, exist_ok=True)
    if plantilla == "Sitio web Flask":
        _w(os.path.join(ruta, "app.py"), FLASK_APP)
        _w(os.path.join(ruta, "templates", "index.html"), FLASK_HTML)
        _w(os.path.join(ruta, "static", "style.css"), FLASK_CSS)
        _w(os.path.join(ruta, "requirements.txt"), "flask>=3.0\n")
    _w(os.path.join(ruta, "README.md"), "# " + os.path.basename(ruta) + "\n")
    return ruta


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
