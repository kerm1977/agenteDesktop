"""Árbol de archivos del proyecto abierto."""
import os

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QFileSystemModel, QTreeView, QVBoxLayout,
                               QWidget)

SKIP = {".git", ".agente", ".update", "node_modules", ".venv", ".venv312",
        "modelos", "vendor", "exports", "dist", "build", "__pycache__"}


class TreePanel(QWidget):
    file_opened = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self._model = QFileSystemModel(self)
        self._view = QTreeView(self)
        self._view.setModel(self._model)
        self._view.setHeaderHidden(True)
        for col in (1, 2, 3):
            self._view.hideColumn(col)
        self._view.setAnimated(False)
        self._view.setStyleSheet(
            "QTreeView{background:#232329;color:#dcdce2;border:none;}"
            "QTreeView::item:selected{background:#2f6ea3;}")
        self._view.doubleClicked.connect(self._open)
        lay.addWidget(self._view)
        self.root = None

    def set_root(self, path):
        self.root = path
        idx = self._model.setRootPath(path)
        self._view.setRootIndex(idx)
        self._model.setNameFilters(["*"])
        self._view.expand(idx)

    def _open(self, index):
        path = self._model.filePath(index)
        if os.path.isfile(path):
            self.file_opened.emit(path)
