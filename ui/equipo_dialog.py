"""Diálogo 'Analizar equipo': reporte completo de hardware, copiable."""
from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPlainTextEdit,
                               QPushButton, QVBoxLayout)

from core import db, hwinfo


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
        self.lbl_perf = QLabel(
            "Velocidad de pensamiento: sin respuestas aún")
        self.lbl_perf.setStyleSheet(
            "color:#7ab3e0;padding:3px;border:1px solid #42424c;"
            "border-radius:5px;")
        lay.addWidget(self.lbl_perf)
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
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_perf)
        self._timer.start(1000)

    def _tick_perf(self):
        p = db.get_cfg("ultimo_perf")
        if p:
            self.lbl_perf.setText("Velocidad de pensamiento: " + p)

    def _mostrar(self, datos):
        self._datos = datos
        self.txt.setPlainText(hwinfo.reporte(datos))

    def _copiar(self):
        self.txt.selectAll()
        self.txt.copy()
        sel = self.txt.textCursor()
        sel.clearSelection()
        self.txt.setTextCursor(sel)
