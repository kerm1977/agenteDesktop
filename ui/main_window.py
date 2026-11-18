"""Ventana principal: riel de iconos, stack lateral, chat central, editor."""
import os
import shutil

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QDockWidget, QFileDialog, QMainWindow,
                               QSplitter, QStackedWidget)

from core import backends, consola, db, memoria, ollama, prompts
from ui import barras, ota_ui
from ui.chat_panel import ChatPanel
from ui.console_panel import ConsolePanel
from ui.editor_panel import EditorPanel
from ui.models_panel import ModelsPanel
from ui.nuevo_proyecto import NuevoProyectoDialog, crear_proyecto
from ui.tree_panel import TreePanel
from ui.worker import ChatWorker

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DARK = ("QMainWindow,QWidget{background:#202024;color:#e2e2e6;}"
        "QToolBar{background:#26262b;border:none;spacing:4px;padding:4px;}"
        "QToolBar QToolButton{background:transparent;color:#d0d0d6;"
        "border-radius:6px;padding:5px 8px;}"
        "QToolBar QToolButton:hover{background:#34343c;}"
        "QToolBar QToolButton:checked{background:#2e7fb8;color:#fff;}"
        "QLabel{color:#d4d4da;}"
        "QSplitter::handle{background:#303038;}"
        "QScrollBar:vertical{background:transparent;width:10px;margin:2px;}"
        "QScrollBar::handle:vertical{background:#45454d;border-radius:5px;"
        "min-height:30px;}"
        "QScrollBar::handle:vertical:hover{background:#5a5a66;}"
        "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
        "QScrollBar:horizontal{background:transparent;height:10px;margin:2px;}"
        "QScrollBar::handle:horizontal{background:#45454d;border-radius:5px;"
        "min-width:30px;}"
        "QScrollBar::handle:horizontal:hover{background:#5a5a66;}"
        "QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal"
        "{width:0;}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Agente Desktop")
        self.resize(1340, 840)
        self.setStyleSheet(DARK)
        self._worker = None
        self._messages = []
        self._self_mode = False
        self._root = os.getcwd()

        self.tree = TreePanel()
        self.models = ModelsPanel()
        self.editor = EditorPanel()
        self.chat = ChatPanel()
        self.proyecto_tree = TreePanel()  # árbol del proyecto, junto al IDE

        self._stack = QStackedWidget()
        self._stack.addWidget(self.tree)
        self._stack.addWidget(self.models)
        self._stack.setMinimumWidth(220)
        self._stack.setMaximumWidth(360)

        split = QSplitter(Qt.Horizontal)
        split.addWidget(self._stack)
        split.addWidget(self.chat)
        split.addWidget(self.proyecto_tree)
        split.addWidget(self.editor)
        split.setSizes([230, 540, 240, 430])
        self._split = split
        split.setCollapsible(0, False)
        self.setCentralWidget(split)

        self._dock = QDockWidget("Consola", self)
        self.console = ConsolePanel()
        self._dock.setWidget(self.console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._dock)
        self._dock.hide()

        barras.build_rail(self)
        barras.build_toolbar(self)
        self._fill_backends()
        self._wire()

        QTimer.singleShot(600, self._check_ollama)
        QTimer.singleShot(2500, lambda: ota_ui.check_and_prompt(
            self, self.chat))

    def _scan_hw(self):
        self._stack.setCurrentIndex(1)
        self.models.scan_hardware()

    def _fill_backends(self):
        for key, cfg in backends.BACKENDS.items():
            self.chat.cmb_backend.addItem(cfg["nombre"], key)
        self.chat.cmb_backend.currentIndexChanged.connect(self._load_models)
        self._load_models()

    def _wire(self):
        self.tree.file_opened.connect(self.editor.open_file)
        self.proyecto_tree.file_opened.connect(self.editor.open_file)
        self.editor.file_saved.connect(
            lambda p: consola.log_info("editor", "guardado " + p))
        self.chat.send_requested.connect(self._send)
        self.chat.stop_requested.connect(self._stop)
        self.chat.attach_requested.connect(self._attach)
        self.chat.cmb_model.currentTextChanged.connect(
            self.models._select_model)

    # ---------- proyecto ----------
    def set_root(self, root):
        self._root = root
        self.tree.set_root(root)
        self.proyecto_tree.set_root(root)
        self.editor.set_root(root)
        memoria.load(root)

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Abrir proyecto (carpeta)",
                                             self._root)
        if d:
            self.set_root(d)
            self._stack.setCurrentIndex(0)
            self.editor._label.setText(
                f"  📁 {os.path.basename(d)}  ›  (elige un archivo del árbol)")
            self.chat.add_system("Proyecto abierto: " + d)

    def _nuevo_proyecto(self):
        base = os.path.join(os.path.expanduser("~"), "proyectos")
        os.makedirs(base, exist_ok=True)
        dlg = NuevoProyectoDialog(base, self)
        if dlg.exec() and dlg.ruta:
            ruta = crear_proyecto(dlg.ruta, dlg._plantilla.currentText())
            self.set_root(ruta)
            self._stack.setCurrentIndex(0)
            self.chat.add_system("Proyecto creado en " + ruta)
            consola.log_info("proyecto", "creado " + ruta)

    def _attach(self, kind):
        dest = os.path.join(self._root, "adjuntos")
        os.makedirs(dest, exist_ok=True)
        if kind == "files":
            paths, _ = QFileDialog.getOpenFileNames(self, "Adjuntar archivos")
        else:
            d = QFileDialog.getExistingDirectory(self, "Adjuntar carpeta")
            paths = [d] if d else []
        ultimo = None
        for p in paths:
            target = os.path.join(dest, os.path.basename(p))
            try:
                if os.path.isdir(p):
                    shutil.copytree(p, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(p, target)
                self.chat.add_attachment(target)
                consola.log_info("adjuntos", "copiado " + target)
                ultimo = target
            except OSError as e:
                consola.log_error("adjuntos", repr(e))
        if ultimo:
            self._stack.setCurrentIndex(0)
            self.tree.reveal(ultimo)
            if os.path.isdir(ultimo):
                self.proyecto_tree.set_root(ultimo)
                self.editor.set_root(ultimo)
                self.editor._label.setText(
                    f"  📁 {os.path.basename(ultimo)}  ›  "
                    "(elige un archivo del árbol)")

    def _toggle_self_mode(self, on):
        self._self_mode = on
        if on:
            self.set_root(APP_DIR)
            self.chat.add_system("MODO MEJORAR AGENTE: trabajaré solo sobre "
                                 "el código de esta aplicación.")
        else:
            self.chat.add_system("Modo agente desactivado.")

    # ---------- modelos ----------
    def _check_ollama(self):
        if not backends.backend_status("ollama"):
            ollama.ensure_running()
        v = ollama.version() or "desconectado"
        self.lbl_status.setText("Ollama " + v)
        self._load_models()
        self.models.refresh()

    def _load_models(self):
        backend = self.chat.cmb_backend.currentData()
        models = backends.list_models(backend)
        self.chat.cmb_model.clear()
        self.chat.cmb_model.addItems(models or ["(sin modelos)"])

    # ---------- chat ----------
    def _send(self, text, attachments):
        backend = self.chat.cmb_backend.currentData()
        model = self.chat.cmb_model.currentText()
        if not model or model.startswith("("):
            self.chat.add_system("No hay modelo disponible en ese motor.")
            return
        msg = text
        if attachments:
            msg += "\n\nAdjuntos (copiados en adjuntos/):\n" + "\n".join(
                "- " + os.path.relpath(p, self._root) for p in attachments)
        self.chat.add_user(text or "(adjuntos)")
        self.models.save_prefs(model)
        system = prompts.build_system(self.editor.context(), self._root,
                                      self._self_mode)
        self._messages = ([{"role": "system", "content": system}]
                          + [m for m in self._messages
                             if m["role"] != "system"])
        self._messages.append({"role": "user", "content": msg})
        db.log_chat("user", msg)
        options = {k: v for k, v in db.get_model_prefs(model).items()
                   if k in ("num_ctx", "num_predict", "temperature")}
        self.chat.start_stream()
        self.chat.set_busy(True)
        self._worker = ChatWorker(backend, model, self._messages, self._root,
                                  options=options)
        self._worker.token.connect(self.chat.append_token)
        self._worker.card.connect(self.chat.add_card)
        self._worker.finished_text.connect(self._chat_done)
        self._worker.failed.connect(self._chat_failed)
        self._worker.start()

    def _stop(self):
        if self._worker:
            self._worker.request_stop()

    def _chat_done(self, text):
        self.chat.end_stream()
        self.chat.set_busy(False)
        if text:
            self._messages.append({"role": "assistant", "content": text})
            db.log_chat("assistant", text)
        self._worker = None

    def _chat_failed(self, err):
        self.chat.end_stream()
        self.chat.set_busy(False)
        self.chat.add_system("Error: " + err)
        self._worker = None
