"""Panel de chat: mensajes, tarjetas contraíbles y composer estilo Devin."""
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QComboBox, QFrame, QGroupBox, QHBoxLayout,
                               QLabel, QMenu, QPlainTextEdit, QPushButton,
                               QScrollArea, QToolButton, QVBoxLayout, QWidget)

from core import consola


class Bubble(QLabel):
    def __init__(self, text, kind="assistant"):
        super().__init__(text)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        color = {"user": "#2d629b", "assistant": "#2b2b31",
                 "system": "#4a4020"}.get(kind, "#2b2b31")
        self.setStyleSheet(f"QLabel{{background:{color};color:#e8e8e8;"
                           "border-radius:10px;padding:10px 12px;}}")


class TaskCard(QGroupBox):
    """Tarjeta contraíble para cada acción del agente."""

    def __init__(self, title, detail=""):
        super().__init__("▸ " + title)
        self.setCheckable(True)
        self.setChecked(False)
        lay = QVBoxLayout(self)
        self._lbl = QLabel(detail or "(sin detalle)")
        self._lbl.setWordWrap(True)
        self._lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        f = QFont("Consolas", 9)
        f.setStyleHint(QFont.Monospace)
        self._lbl.setFont(f)
        self._lbl.setStyleSheet("color:#b5b5b5;")
        self._lbl.setVisible(False)
        lay.addWidget(self._lbl)
        self.setStyleSheet(
            "QGroupBox{background:#28282e;color:#9cdcfe;"
            "border:1px solid #3a3a44;border-radius:8px;"
            "margin-top:12px;padding-top:16px;}"
            "QGroupBox::title{subcontrol-origin:margin;left:10px;}")
        self._title = title
        self.toggled.connect(self._toggle)

    def _toggle(self, on):
        self.setTitle(("▾ " if on else "▸ ") + self._title)
        self._lbl.setVisible(on)


class ChatPanel(QWidget):
    send_requested = Signal(str, list)
    stop_requested = Signal()
    attach_requested = Signal(str)  # "files" | "folder"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._attachments = []
        self._stream_lbl = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea{border:none;background:#1b1b1f;}")
        self._box = QWidget()
        self._vbox = QVBoxLayout(self._box)
        self._vbox.setAlignment(Qt.AlignTop)
        self._vbox.setSpacing(8)
        self._vbox.setContentsMargins(10, 10, 10, 10)
        self._scroll.setWidget(self._box)
        lay.addWidget(self._scroll, 1)
        lay.addWidget(self._build_composer())

        self.btn_send.clicked.connect(self._emit_send)
        self.btn_stop.clicked.connect(self.stop_requested)
        self.input.installEventFilter(self)

    # ---------- composer ----------
    def _build_composer(self):
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame{background:#26262b;border:1px solid #3a3a44;"
            "border-radius:12px;margin:8px;}")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)

        self._chips = QLabel("")
        self._chips.setStyleSheet("color:#7ab3e0;font-size:11px;")
        self._chips.setVisible(False)
        lay.addWidget(self._chips)

        self.input = QPlainTextEdit()
        self.input.setPlaceholderText(
            "Ordena algo al agente… (Ctrl+Enter envía)")
        self.input.setMaximumHeight(90)
        self.input.setStyleSheet(
            "QPlainTextEdit{background:transparent;color:#e8e8e8;"
            "border:none;font-size:13px;}")
        lay.addWidget(self.input)

        row = QHBoxLayout()
        self.btn_attach = QToolButton()
        self.btn_attach.setText("＋")
        self.btn_attach.setPopupMode(QToolButton.InstantPopup)
        self.btn_attach.setStyleSheet(
            "QToolButton{background:#303038;color:#ddd;border:1px solid #42424c;"
            "border-radius:12px;padding:4px 10px;font-size:14px;}")
        menu = QMenu(self.btn_attach)
        menu.setStyleSheet("QMenu{background:#2a2a30;color:#ddd;"
                           "border:1px solid #42424c;}")
        menu.addAction("📄 Adjuntar archivos",
                       lambda: self.attach_requested.emit("files"))
        menu.addAction("📁 Adjuntar carpeta",
                       lambda: self.attach_requested.emit("folder"))
        self.btn_attach.setMenu(menu)
        row.addWidget(self.btn_attach)

        self.cmb_backend = QComboBox()
        self.cmb_model = QComboBox()
        self.cmb_model.setMinimumWidth(160)
        for c in (self.cmb_backend, self.cmb_model):
            c.setStyleSheet("QComboBox{background:#303038;color:#ddd;"
                            "border:1px solid #42424c;border-radius:6px;"
                            "padding:3px 8px;}")
        row.addWidget(self.cmb_backend)
        row.addWidget(self.cmb_model)
        row.addStretch(1)

        self.cmb_voz = QComboBox()
        self.cmb_voz.addItems(["Vosk", "Google"])
        self.cmb_voz.setToolTip("Motor de voz: Vosk = offline, "
                              "Google = online")
        self.cmb_voz.setStyleSheet(
            "QComboBox{background:#303038;color:#ddd;"
            "border:1px solid #42424c;border-radius:6px;"
            "padding:3px 8px;}")
        row.addWidget(self.cmb_voz)
        self.btn_mic = QPushButton("🎤")
        self.btn_mic.setToolTip("Dictar por voz (es-ES)")
        self.btn_mic.setCheckable(True)
        self.btn_mic.setStyleSheet(
            "QPushButton{background:#303038;color:#ddd;border:1px solid #42424c;"
            "border-radius:12px;padding:5px 12px;}"
            "QPushButton:checked{background:#a33d3d;color:#fff;}")
        self.btn_mic.clicked.connect(self._toggle_mic)
        row.addWidget(self.btn_mic)
        self._voz = None

        self.btn_stop = QPushButton("■")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet(
            "QPushButton{background:#6e3636;color:#eee;border:none;"
            "border-radius:12px;padding:5px 12px;}"
            "QPushButton:disabled{background:#303038;color:#777;}")
        self.btn_send = QPushButton("➤")
        self.btn_send.setStyleSheet(
            "QPushButton{background:#2e7fb8;color:white;border:none;"
            "border-radius:12px;padding:5px 14px;font-size:14px;}"
            "QPushButton:disabled{background:#303038;color:#777;}")
        row.addWidget(self.btn_stop)
        row.addWidget(self.btn_send)
        lay.addLayout(row)
        return frame

    # ---------- adjuntos ----------
    def add_attachment(self, path):
        self._attachments.append(path)
        names = [os.path.basename(p) for p in self._attachments]
        self._chips.setText("📎 " + "  ·  ".join(names))
        self._chips.setVisible(True)

    # ---------- mensajes ----------
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
        if text or self._attachments:
            self.input.clear()
            atts, self._attachments = self._attachments, []
            self._chips.setVisible(False)
            self.send_requested.emit(text, atts)

    # ---------- dictado por voz ----------
    def _toggle_mic(self, on):
        try:
            if on:
                from core.voz import VoiceWorker
                engine = self.cmb_voz.currentText().lower()
                self._voz = VoiceWorker(engine)
                self._voz.text.connect(self._dictar)
                self._voz.error.connect(self._voz_error)
                self._voz.finished.connect(self._voz.deleteLater)
                self._voz.start()
                self.add_system("🎤 Escuchando… habla y se dicta aquí. "
                                "Toca 🎤 otra vez para parar.")
            elif self._voz:
                voz, self._voz = self._voz, None
                voz.stop()
                voz.wait(3000)  # evita destruir el hilo en marcha
        except Exception as e:
            consola.log_error("voz", repr(e))
            self.add_system("🎤 Error: " + str(e))

    def _dictar(self, texto):
        self.input.insertPlainText(texto + " ")

    def _voz_error(self, err):
        self.add_system("🎤 " + err)
        consola.log_error("voz", err)
        self.btn_mic.setChecked(False)
        if self._voz:
            voz, self._voz = self._voz, None
            voz.stop()
            voz.wait(3000)

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
