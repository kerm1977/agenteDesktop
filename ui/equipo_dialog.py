"""Diálogo 'Analizar equipo': reporte completo de hardware, copiable."""
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPlainTextEdit,
                               QPushButton, QVBoxLayout)

from core import hwinfo


class _ScanThread(QThread):
    done = Signal(dict)

    def run(self):
        self.done.emit(hwinfo.scan())


class EquipoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analizador del equipo")
        self.resize(560, 420)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Especificaciones del equipo:"))
        self.txt = QPlainTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setPlainText("Analizando el equipo…")
        lay.addWidget(self.txt, 1)
        row = QHBoxLayout()
        btn_copiar = QPushButton("Copiar")
        btn_cerrar = QPushButton("Cerrar")
        btn_copiar.clicked.connect(self._copiar)
        btn_cerrar.clicked.connect(self.accept)
        row.addStretch(1)
        row.addWidget(btn_copiar)
        row.addWidget(btn_cerrar)
        lay.addLayout(row)
        self._t = _ScanThread(self)
        self._t.done.connect(self._mostrar)
        self._t.start()

    def _mostrar(self, datos):
        self._datos = datos
        self.txt.setPlainText(hwinfo.reporte(datos))

    def _copiar(self):
        self.txt.selectAll()
        self.txt.copy()
        sel = self.txt.textCursor()
        sel.clearSelection()
        self.txt.setTextCursor(sel)
