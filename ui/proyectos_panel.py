"""Registro de proyectos: lista con buscador + abrir/renombrar/eliminar."""
import json
import os
import shutil
import subprocess

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMessageBox,
                               QPushButton, QVBoxLayout, QWidget)

from core import consola, db


class ProyectosPanel(QWidget):
    """Barra izquierda: proyectos creados con su ruta real."""

    abrir = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 6)
        lay.setSpacing(4)

        cab = QHBoxLayout()
        cab.addWidget(QLabel("Proyectos"))
        cab.addStretch(1)
        self._buscar = QLineEdit()
        self._buscar.setPlaceholderText("Buscar proyecto…")
        self._buscar.setClearButtonEnabled(True)
        self._buscar.setMaximumWidth(140)
        self._buscar.textChanged.connect(self.refresh)
        cab.addWidget(self._buscar)
        lay.addLayout(cab)

        self._lista = QListWidget()
        self._lista.setStyleSheet(
            "QListWidget{background:#222227;border:1px solid #33333b;"
            "border-radius:6px;}"
            "QListWidget::item{padding:4px 6px;}"
            "QListWidget::item:selected{background:#2e5f8a;}")
        self._lista.itemDoubleClicked.connect(
            lambda it: self.abrir.emit(it.data(Qt.UserRole)))
        lay.addWidget(self._lista, 1)

        for texto, fn in (("Abrir", self._abrir),
                          ("Renombrar", self._renombrar),
                          ("Eliminar", self._eliminar),
                          ("Ubicar", self._ubicar)):
            b = QPushButton(texto)
            b.setStyleSheet(
                "QPushButton{background:#303038;color:#ddd;"
                "border:1px solid #42424c;border-radius:6px;"
                "padding:3px 8px;}")
            b.clicked.connect(fn)
            lay.addWidget(b)
        self.refresh()

    # ---------- datos ----------
    @staticmethod
    def _hist():
        try:
            return json.loads(db.get_cfg("historial_roots", "[]"))
        except Exception:
            return []

    @staticmethod
    def _save_hist(hist):
        db.set_cfg("historial_roots", json.dumps(hist, ensure_ascii=False))

    def refresh(self):
        q = self._buscar.text().strip().lower()
        self._lista.clear()
        for h in self._hist():
            path, nombre = h.get("path", ""), h.get("nombre", "")
            if q and q not in nombre.lower() and q not in path.lower():
                continue
            it = QListWidgetItem(f"{nombre}\n{path}")
            it.setData(Qt.UserRole, path)
            it.setToolTip(path)
            self._lista.addItem(it)

    def _sel(self):
        it = self._lista.currentItem()
        return it.data(Qt.UserRole) if it else None

    # ---------- acciones ----------
    def _abrir(self):
        p = self._sel()
        if p:
            self.abrir.emit(p)

    def _renombrar(self):
        p = self._sel()
        if not p:
            return
        nuevo, ok = QInputDialog.getText(
            self, "Renombrar proyecto", "Nuevo nombre:",
            text=os.path.basename(p))
        nuevo = nuevo.strip()
        if not ok or not nuevo or nuevo == os.path.basename(p):
            return
        dest = os.path.join(os.path.dirname(p), nuevo)
        try:
            os.rename(p, dest)
        except OSError as e:
            QMessageBox.warning(self, "Renombrar", "No se pudo: " + str(e))
            return
        hist = self._hist()
        for h in hist:
            if h.get("path") == p:
                h["path"], h["nombre"] = dest, nuevo
        self._save_hist(hist)
        if db.get_cfg("ultimo_root") == p:
            db.set_cfg("ultimo_root", dest)
        consola.log_info("proyectos", f"renombrado {p} -> {dest}")
        self.refresh()
        self.abrir.emit(dest)

    def _eliminar(self):
        p = self._sel()
        if not p:
            return
        ans = QMessageBox.question(
            self, "Eliminar proyecto",
            f"¿Eliminar '{os.path.basename(p)}' y TODO su contenido "
            f"de la computadora?\n\n{p}\n\nNo se puede deshacer.")
        if ans != QMessageBox.Yes:
            return
        try:
            shutil.rmtree(p, ignore_errors=True)
        except OSError as e:
            consola.log_error("proyectos", f"eliminar {p}: {e}")
        self._save_hist([h for h in self._hist() if h.get("path") != p])
        consola.log_info("proyectos", "eliminado " + p)
        self.refresh()

    def _ubicar(self):
        p = self._sel()
        if not p:
            return
        try:
            if os.path.isdir(p):
                subprocess.Popen(["explorer", "/select,", p])
            else:
                subprocess.Popen(["explorer", os.path.dirname(p)])
        except OSError:
            os.startfile(p)
