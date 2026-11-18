"""Ventana principal: barra de herramientas, splitter y docks."""
import os
import subprocess
import sys

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QComboBox, QDockWidget, QFileDialog, QLabel,
                               QMainWindow, QMessageBox, QProgressDialog,
                               QSplitter)

from core import backends, consola, memoria, ollama, ota, tools
from ui.chat_panel import ChatPanel
from ui.console_panel import ConsolePanel
from ui.editor_panel import EditorPanel
from ui.tree_panel import TreePanel
from ui.worker import ChatWorker

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SYSTEM_BASE = ("Eres un agente de código local. Respondes en español, breve y "
               "preciso. " + tools.TOOLS_DOC)

SYSTEM_SELF = ("\n\nMODO MEJORAR AGENTE: trabajas ÚNICAMENTE sobre el código de "
               "la propia aplicación en " + APP_DIR + ". Respeta REGLAS.md "
               "(archivos <250 líneas, sin CDNs). No toques proyectos del "
               "usuario.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Agente Desktop")
        self.resize(1280, 800)
        self.setStyleSheet("QMainWindow{background:#1b1b1c;}"
                           "QToolBar{background:#2d2d30;border:none;spacing:6px;"
                           "padding:4px;}")
        self._worker = None
        self._messages = []
        self._self_mode = False

        self.tree = TreePanel()
        self.editor = EditorPanel()
        self.chat = ChatPanel()
        split = QSplitter(Qt.Horizontal)
        split.addWidget(self.tree)
        split.addWidget(self.editor)
        split.addWidget(self.chat)
        split.setSizes([240, 560, 480])
        self.setCentralWidget(split)

        self._dock = QDockWidget("Consola", self)
        self.console = ConsolePanel()
        self._dock.setWidget(self.console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._dock)
        self._dock.hide()

        self._build_toolbar()
        self._wire()
        self.set_root(os.getcwd())
        QTimer.singleShot(1500, self._ota_check)
        QTimer.singleShot(500, self._check_ollama)

    # ---------- barra de herramientas ----------
    def _build_toolbar(self):
        tb = self.addToolBar("Principal")
        tb.setMovable(False)

        act_dir = QAction("📂 Abrir carpeta", self)
        act_dir.triggered.connect(self._pick_dir)
        tb.addAction(act_dir)

        act_save = QAction("💾 Guardar", self)
        act_save.setShortcut(QKeySequence.Save)
        act_save.triggered.connect(self.editor.editor.save)
        tb.addAction(act_save)
        tb.addSeparator()

        tb.addWidget(QLabel(" Motor: "))
        self.cmb_backend = QComboBox()
        for key, cfg in backends.BACKENDS.items():
            self.cmb_backend.addItem(cfg["nombre"], key)
        self.cmb_backend.currentIndexChanged.connect(self._load_models)
        tb.addWidget(self.cmb_backend)

        tb.addWidget(QLabel(" Modelo: "))
        self.cmb_model = QComboBox()
        self.cmb_model.setMinimumWidth(200)
        self.cmb_model.setEditable(True)
        tb.addWidget(self.cmb_model)
        self._load_models()
        tb.addSeparator()

        act_console = QAction("🖥 Consola", self)
        act_console.triggered.connect(
            lambda: self._dock.setVisible(not self._dock.isVisible()))
        tb.addAction(act_console)

        act_self = QAction("🛠 Mejorar agente", self)
        act_self.setCheckable(True)
        act_self.toggled.connect(self._toggle_self_mode)
        tb.addAction(act_self)

        act_ota = QAction("⬆ Actualizar", self)
        act_ota.triggered.connect(lambda: self._ota_check(manual=True))
        tb.addAction(act_ota)
        tb.addSeparator()

        self.lbl_status = QLabel("…")
        tb.addWidget(self.lbl_status)

    # ---------- wiring ----------
    def _wire(self):
        self.tree.file_opened.connect(self.editor.open_file)
        self.editor.file_saved.connect(
            lambda p: consola.log_info("editor", "guardado " + p))
        self.chat.send_requested.connect(self._send)
        self.chat.stop_requested.connect(self._stop)

    def set_root(self, root):
        self.tree.set_root(root)
        self.editor.set_root(root)
        self._root = root
        memoria.load(root)

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Carpeta del proyecto",
                                             self._root)
        if d:
            self.set_root(d)

    def _toggle_self_mode(self, on):
        self._self_mode = on
        if on:
            self.set_root(APP_DIR)
            self.chat.add_system("MODO MEJORAR AGENTE activo: trabajaré solo "
                                 "sobre el código de esta aplicación.")
        else:
            self.chat.add_system("Modo agente desactivado.")

    def _check_ollama(self):
        ok = backends.backend_status("ollama")
        if not ok:
            ok = ollama.ensure_running()
        v = ollama.version() or "desconectado"
        self.lbl_status.setText(f"Ollama {v}")
        self._load_models()

    def _load_models(self):
        backend = self.cmb_backend.currentData()
        models = backends.list_models(backend)
        self.cmb_model.clear()
        self.cmb_model.addItems(models or ["(sin modelos)"])

    # ---------- chat ----------
    def _send(self, text):
        backend = self.cmb_backend.currentData()
        model = self.cmb_model.currentText()
        if not model or model.startswith("("):
            self.chat.add_system("No hay modelo disponible en ese motor.")
            return
        self.chat.add_user(text)
        system = self._build_system()
        self._messages = ([{"role": "system", "content": system}]
                          + [m for m in self._messages
                             if m["role"] != "system"])
        self._messages.append({"role": "user", "content": text})
        self.chat.start_stream()
        self.chat.set_busy(True)
        self._worker = ChatWorker(backend, model, self._messages, self._root)
        self._worker.token.connect(self.chat.append_token)
        self._worker.card.connect(self.chat.add_card)
        self._worker.finished_text.connect(self._chat_done)
        self._worker.failed.connect(self._chat_failed)
        self._worker.start()

    def _build_system(self):
        system = SYSTEM_BASE
        if self._self_mode:
            system += SYSTEM_SELF
        ed = self.editor.context()
        if ed and not self._self_mode:
            content = ed["content"]
            cap = 6000
            system += (f"\n\nEl usuario tiene abierto '{ed['path']}' en el "
                       f"editor. Contenido actual (puede estar sin guardar):\n"
                       f"```\n{content[:cap]}\n```")
            if len(content) > cap:
                system += "\n(Contenido truncado: usa read_file para ver más.)"
        if self._root:
            try:
                system += ("\n\nMemoria del proyecto (estructura y firmas):\n"
                           + memoria.digest(self._root, cap=4000))
            except Exception as e:
                consola.log_error("memoria", repr(e))
        return system

    def _stop(self):
        if self._worker:
            self._worker.request_stop()

    def _chat_done(self, text):
        self.chat.end_stream()
        self.chat.set_busy(False)
        if text:
            self._messages.append({"role": "assistant", "content": text})
        self._worker = None

    def _chat_failed(self, err):
        self.chat.end_stream()
        self.chat.set_busy(False)
        self.chat.add_system("Error: " + err)
        self._worker = None

    # ---------- OTA ----------
    def _ota_check(self, manual=False):
        res = ota.check_update()
        if not res["ok"]:
            consola.log_error("ota", res["error"])
            if manual:
                self.chat.add_system("Sin conexión al repositorio de "
                                     "actualizaciones.")
            return
        if not res["archivos"]:
            if manual:
                self.chat.add_system(
                    f"Ya estás en la última versión ({res['actual']}).")
            return
        msg = (f"Hay actualización {res['actual']} → {res['remota']} "
               f"({len(res['archivos'])} archivos). ¿Descargar y aplicar?")
        if QMessageBox.question(self, "Actualización", msg) != QMessageBox.Yes:
            return
        prog = QProgressDialog("Descargando actualización…", "Cancelar", 0,
                               len(res["archivos"]), self)
        prog.setWindowModality(Qt.WindowModal)

        def tick(i, total, rel):
            prog.setValue(i)
            if prog.wasCanceled():
                raise InterruptedError()

        out = ota.download_update(res["manifest"], progress=tick)
        prog.close()
        if out["errores"]:
            consola.log_error("ota", "; ".join(out["errores"]))
        ans = QMessageBox.question(
            self, "Actualización lista",
            "Descargada. ¿Reiniciar ahora para aplicarla?")
        if ans == QMessageBox.Yes:
            updater = os.path.join(APP_DIR, "core", "updater.py")
            subprocess.Popen(
                [sys.executable, updater, os.path.join(APP_DIR, "app.py")],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            from PySide6.QtWidgets import QApplication
            QApplication.quit()
