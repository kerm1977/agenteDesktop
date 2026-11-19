"""Panel de historial de conversaciones: lista con buscador y borrado."""
import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QPushButton, QVBoxLayout,
                               QWidget)

from core import db


class ConversacionesPanel(QWidget):
    """Registro de conversaciones recientes, con fecha/hora y buscador."""

    abrir = Signal(int)
    borrar = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 6)
        lay.setSpacing(4)

        cab = QHBoxLayout()
        cab.addWidget(QLabel("Conversaciones recientes"))
        cab.addStretch(1)
        self._buscar = QLineEdit()
        self._buscar.setPlaceholderText("Buscar conversación…")
        self._buscar.setClearButtonEnabled(True)
        self._buscar.setMaximumWidth(240)
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

        pie = QHBoxLayout()
        self._btn_abrir = QPushButton("Continuar")
        self._btn_abrir.clicked.connect(self._abrir_sel)
        self._btn_borrar = QPushButton("Eliminar")
        self._btn_borrar.clicked.connect(self._borrar_sel)
        for b in (self._btn_abrir, self._btn_borrar):
            b.setStyleSheet(
                "QPushButton{background:#303038;color:#ddd;"
                "border:1px solid #42424c;border-radius:6px;"
                "padding:3px 10px;}")
        pie.addStretch(1)
        pie.addWidget(self._btn_abrir)
        pie.addWidget(self._btn_borrar)
        lay.addLayout(pie)
        self.refresh()

    def refresh(self):
        query = self._buscar.text().strip()
        self._lista.clear()
        for cid, titulo, ts in db.list_conversaciones(query):
            fecha = time.strftime("%d/%m/%Y %H:%M", time.localtime(ts))
            it = QListWidgetItem(f"{titulo}\n{fecha}")
            it.setData(Qt.UserRole, cid)
            it.setToolTip(fecha)
            self._lista.addItem(it)

    def _sel_id(self):
        it = self._lista.currentItem()
        return it.data(Qt.UserRole) if it else None

    def _abrir_sel(self):
        cid = self._sel_id()
        if cid:
            self.abrir.emit(cid)

    def _borrar_sel(self):
        cid = self._sel_id()
        if cid:
            self.borrar.emit(cid)
