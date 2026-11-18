"""Dock de consola: registra errores/eventos con copiar y limpiar."""
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QPlainTextEdit,
                               QPushButton, QVBoxLayout, QWidget)

from core import consola


class _Bridge(QObject):
    entry = Signal(dict)


class ConsolePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        self._view = QPlainTextEdit()
        self._view.setReadOnly(True)
        f = QFont("Consolas", 9)
        f.setStyleHint(QFont.Monospace)
        self._view.setFont(f)
        self._view.setStyleSheet(
            "QPlainTextEdit{background:#1d1d21;color:#dcdce2;border:none;}")
        lay.addWidget(self._view, 1)

        row = QHBoxLayout()
        self.btn_copy = QPushButton("Copiar")
        self.btn_clear = QPushButton("Limpiar")
        for b in (self.btn_copy, self.btn_clear):
            b.setStyleSheet("QPushButton{background:#34343c;color:#ddd;"
                            "border:none;border-radius:4px;padding:4px 12px;}")
        row.addStretch(1)
        row.addWidget(self.btn_copy)
        row.addWidget(self.btn_clear)
        lay.addLayout(row)
        self.btn_copy.clicked.connect(self._copy)
        self.btn_clear.clicked.connect(self._clear)

        self._bridge = _Bridge()
        self._bridge.entry.connect(self._render)
        consola.subscribe(self._bridge.entry.emit)
        for e in consola.entries():
            self._render(e)

    def _render(self, e):
        mark = "❌" if e["nivel"] == "error" else "ℹ"
        self._view.appendPlainText(
            f"{e['ts']} {mark} [{e['origen']}] {e['detalle']}")

    def _copy(self):
        text = self._view.toPlainText()
        QApplication.clipboard().setText(text)

    def _clear(self):
        consola.clear()
        self._view.clear()
