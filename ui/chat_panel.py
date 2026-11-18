"""Panel de chat: mensajes, tarjetas de tarea contraíbles, entrada."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QGroupBox, QHBoxLayout, QLabel, QPlainTextEdit,
                               QPushButton, QScrollArea, QVBoxLayout, QWidget)


class Bubble(QLabel):
    def __init__(self, text, kind="assistant"):
        super().__init__(text)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setTextFormat(Qt.PlainText)
        color = {"user": "#0b5cad", "assistant": "#2d2d30",
                 "system": "#5a3a00"}.get(kind, "#2d2d30")
        self.setStyleSheet(f"QLabel{{background:{color};color:#e8e8e8;"
                           "border-radius:8px;padding:8px;}}")


class TaskCard(QGroupBox):
    """Tarjeta contraíble para cada acción del agente."""

    def __init__(self, title, detail=""):
        super().__init__(title)
        self.setCheckable(True)
        self.setChecked(False)
        lay = QVBoxLayout(self)
        self._lbl = QLabel(detail or "(sin detalle)")
        self._lbl.setWordWrap(True)
        self._lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        f = QFont("Consolas", 9)
        f.setStyleHint(QFont.Monospace)
        self._lbl.setFont(f)
        self._lbl.setVisible(False)
        lay.addWidget(self._lbl)
        self.setStyleSheet(
            "QGroupBox{background:#252526;color:#9cdcfe;border:1px solid #3e3e42;"
            "border-radius:6px;margin-top:10px;padding-top:14px;}"
            "QGroupBox::title{subcontrol-origin:margin;left:8px;}"
            "QGroupBox::indicator{right:6px;}")
        self.toggled.connect(self._lbl.setVisible)

    def append(self, text):
        self._lbl.setText(self._lbl.text() + "\n" + text)


class ChatPanel(QWidget):
    send_requested = Signal(str)
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea{border:none;background:#1b1b1c;}")
        self._box = QWidget()
        self._vbox = QVBoxLayout(self._box)
        self._vbox.setAlignment(Qt.AlignTop)
        self._vbox.setSpacing(6)
        self._scroll.setWidget(self._box)
        lay.addWidget(self._scroll, 1)

        self.input = QPlainTextEdit()
        self.input.setPlaceholderText(
            "Escribe tu orden… (Ctrl+Enter para enviar)")
        self.input.setMaximumHeight(80)
        self.input.setStyleSheet(
            "QPlainTextEdit{background:#252526;color:#e8e8e8;"
            "border:1px solid #3e3e42;border-radius:6px;padding:6px;}")
        self.input.installEventFilter(self)
        lay.addWidget(self.input)

        row = QHBoxLayout()
        self.btn_send = QPushButton("Enviar")
        self.btn_stop = QPushButton("Detener")
        self.btn_stop.setEnabled(False)
        for b in (self.btn_send, self.btn_stop):
            b.setStyleSheet("QPushButton{background:#0e639c;color:white;"
                            "border:none;border-radius:4px;padding:6px 14px;}"
                            "QPushButton:disabled{background:#3e3e42;}")
        row.addStretch(1)
        row.addWidget(self.btn_stop)
        row.addWidget(self.btn_send)
        lay.addLayout(row)

        self.btn_send.clicked.connect(self._emit_send)
        self.btn_stop.clicked.connect(self.stop_requested)
        self._stream_lbl = None

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj is self.input and event.type() == QEvent.KeyPress:
            if (event.key() in (Qt.Key_Return, Qt.Key_Enter)
                    and event.modifiers() & Qt.ControlModifier):
                self._emit_send()
                return True
        return super().eventFilter(obj, event)

    def _emit_send(self):
        text = self.input.toPlainText().strip()
        if text:
            self.input.clear()
            self.send_requested.emit(text)

    def add_user(self, text):
        self._vbox.addWidget(Bubble("Tú: " + text, "user"))
        self._scroll_down()

    def add_system(self, text):
        self._vbox.addWidget(Bubble(text, "system"))
        self._scroll_down()

    def add_card(self, title, detail=""):
        card = TaskCard(title, detail)
        self._vbox.addWidget(card)
        self._scroll_down()
        return card

    def start_stream(self):
        self._stream_lbl = Bubble("", "assistant")
        self._vbox.addWidget(self._stream_lbl)
        self._scroll_down()

    def append_token(self, text):
        if self._stream_lbl is not None:
            self._stream_lbl.setText(self._stream_lbl.text() + text)
            self._scroll_down()

    def end_stream(self):
        self._stream_lbl = None
        self._scroll_down()

    def set_busy(self, busy):
        self.btn_send.setEnabled(not busy)
        self.btn_stop.setEnabled(busy)

    def _scroll_down(self):
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())
