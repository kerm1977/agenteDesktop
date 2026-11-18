"""Editor de código nativo con números de línea y resaltado básico."""
import os
import re

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import (QColor, QFont, QPainter, QSyntaxHighlighter,
                           QTextCharFormat, QTextCursor)
from PySide6.QtWidgets import QPlainTextEdit, QWidget


class Highlighter(QSyntaxHighlighter):
    """Resaltado mínimo para Python/JS/TS: comentarios, strings, keywords."""

    KW = {
        "py": ("def class import from as return if elif else for while try "
               "except finally with lambda pass break continue raise yield "
               "global nonlocal assert del in is not and or True False None "
               "async await print self").split(),
        "js": ("function class const let var return if else for while do "
               "switch case default try catch finally throw new delete "
               "typeof instanceof in of async await export import from "
               "extends super this true false null undefined").split(),
    }

    def __init__(self, doc, lang="py"):
        super().__init__(doc)
        self.rules = []
        fmt_kw = QTextCharFormat(); fmt_kw.setForeground(QColor("#569CD6"))
        fmt_str = QTextCharFormat(); fmt_str.setForeground(QColor("#CE9178"))
        fmt_com = QTextCharFormat(); fmt_com.setForeground(QColor("#6A9955"))
        fmt_num = QTextCharFormat(); fmt_num.setForeground(QColor("#B5CEA8"))
        for kw in self.KW.get(lang, []):
            self.rules.append((re.compile(r"\b" + kw + r"\b"), fmt_kw))
        self.rules.append((re.compile(r"\b\d+(\.\d+)?\b"), fmt_num))
        self.rules.append((re.compile(r'"[^"\n]*"|\'[^\'\n]*\''), fmt_str))
        self.rules.append((re.compile(r"#[^\n]*" if lang == "py" else r"//[^\n]*"),
                           fmt_com))

    def highlightBlock(self, text):
        for rx, fmt in self.rules:
            for m in rx.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._ed = editor

    def sizeHint(self):
        return QSize(self._ed.line_number_width(), 0)

    def paintEvent(self, event):
        self._ed.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    file_saved = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_area = LineNumberArea(self)
        self.path = None
        self._hl = None
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.setStyleSheet("QPlainTextEdit{background:#242429;color:#dcdce2;"
                           "border:none;}")
        self.blockCountChanged.connect(self._update_line_area_width)
        self.updateRequest.connect(self._update_line_area)
        self._update_line_area_width(0)

    def line_number_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 8 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_area_width(self, _):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def _update_line_area(self, rect, dy):
        if dy:
            self._line_area.scroll(0, dy)
        else:
            self._line_area.update(0, rect.y(),
                                   self._line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_width(), cr.height()))

    def paint_line_numbers(self, event):
        painter = QPainter(self._line_area)
        painter.fillRect(event.rect(), QColor("#2a2a30"))
        block = self.firstVisibleBlock()
        num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block)
                  .translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        painter.setPen(QColor("#858585"))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(0, top, self._line_area.width() - 4,
                                 self.fontMetrics().height(),
                                 Qt.AlignRight, str(num + 1))
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            num += 1
        painter.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_S and event.modifiers() & Qt.ControlModifier:
            self.save()
            return
        if event.key() == Qt.Key_Tab:
            self.textCursor().insertText("    ")
            return
        super().keyPressEvent(event)

    def load_file(self, path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        self.path = path
        self.setPlainText(text)
        self.document().setModified(False)
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        lang = "py" if ext in ("py", "pyw") else "js"
        self._hl = Highlighter(self.document(), lang)
        self.setPlaceholderText("")

    def save(self):
        if not self.path:
            return
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(self.toPlainText())
        self.document().setModified(False)
        self.file_saved.emit(self.path)


class EditorPanel(QWidget):
    """Editor + etiqueta del archivo abierto."""
    file_saved = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QVBoxLayout, QLabel
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._label = QLabel("  Sin archivo — abre uno en el árbol")
        self._label.setStyleSheet("background:#2c2c32;color:#d4d4da;"
                                  "padding:4px;font-size:11px;")
        self.editor = CodeEditor()
        lay.addWidget(self._label)
        lay.addWidget(self.editor, 1)
        self.editor.file_saved.connect(self.file_saved)

    def open_file(self, path):
        try:
            self.editor.load_file(path)
            self._label.setText("  " + self._crumb(path))
        except OSError as e:
            self._label.setText("  Error: " + str(e))

    def _crumb(self, path):
        root = self._project_root
        if root and os.path.normcase(path).startswith(
                os.path.normcase(root + os.sep)):
            rel = os.path.relpath(path, root)
            return f"📁 {os.path.basename(root)}  ›  {rel.replace(os.sep, ' › ')}"
        return "  " + path

    def context(self):
        """Contexto del editor para el chat."""
        if not self.editor.path:
            return None
        return {"path": self.editor.path,
                "dir": self._project_root,
                "content": self.editor.toPlainText()}

    _project_root = None

    def set_root(self, root):
        self._project_root = root
