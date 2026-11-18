"""Ventana principal: riel de iconos, stack lateral, chat central, editor."""
import os
import shutil
import subprocess
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (QDockWidget, QFileDialog, QLabel, QMainWindow,
                               QMessageBox, QProgressDialog, QSplitter,
                               QStackedWidget, QToolBar)

from core import backends, consola, memoria, ollama, ota, tools
from ui.chat_panel import ChatPanel
from ui.console_panel import ConsolePanel
from ui.editor_panel import EditorPanel
from ui.models_panel import ModelsPanel
from ui.tree_panel import TreePanel
from ui.worker import ChatWorker

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SYSTEM_BASE = ("Eres un agente de código local. Respondes en español, breve y "
               "preciso. " + tools.TOOLS_DOC)

SYSTEM_SELF = ("\n\nMODO MEJORAR AGENTE: trabajas ÚNICAMENTE sobre el código de "
               "la propia aplicación en " + APP_DIR + ". Respeta REGLAS.md "
               "(archivos <250 líneas, sin CDNs). No toques proyectos del "
               "usuario.")

DARK = ("QMainWindow,QWidget{background:#131314;color:#d4d4d4;}"
        "QToolBar{background:#1b1b1d;border:none;spacing:4px;padding:4px;}"
        "QToolBar QToolButton{background:transparent;color:#ccc;"
        "border-radius:6px;padding:5px 8px;}"
        "QToolBar QToolButton:hover{background:#2a2a2e;}"
        "QToolBar QToolButton:checked{background:#0e639c;color:#fff;}"
        "QLabel{color:#ccc;}"
        "QSplitter::handle{background:#232326;}")


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

        # --- paneles ---
        self.tree = TreePanel()
        self.models = ModelsPanel()
        self.editor = EditorPanel()
        self.chat = ChatPanel()

        self._stack = QStackedWidget()
        self._stack.addWidget(self.tree)
        self._stack.addWidget(self.models)
        self._stack.setMinimumWidth(220)
        self._stack.setMaximumWidth(360)

        split = QSplitter(Qt.Horizontal)
        split.addWidget(self._stack)
        split.addWidget(self.chat)
        split.addWidget(self.editor)
        split.setSizes([260, 620, 460])
        split.setCollapsible(0, False)
        self.setCentralWidget(split)

        self._dock = QDockWidget("Consola", self)
        self.console = ConsolePanel()
        self._dock.setWidget(self.console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._dock)
        self._dock.hide()

        self._build_rail()
        self._build_toolbar()
        self._fill_backends()
        self._wire()

        QTimer.singleShot(600, self._check_ollama)
        QTimer.singleShot(2500, self._ota_check)

    # ---------- riel lateral ----------
    def _build_rail(self):
        rail = QToolBar("Secciones")
        rail.setMovable(False)
        rail.setOrientation(Qt.Vertical)
        rail.setFixedWidth(52)
        self.addToolBar(Qt.LeftToolBarArea, rail)
        grp = QActionGroup(self)
        grp.setExclusive(True)
        for icon, name, idx in (("📁", "Archivos", 0), ("🧠", "Modelos", 1)):
            act = QAction(icon, self)
            act.setToolTip(name)
            act.setCheckable(True)
            act.setData(idx)
            act.triggered.connect(
                lambda _c, i=idx: self._stack.setCurrentIndex(i))
            grp.addAction(act)
            rail.addAction(act)
            if idx == 0:
                act.setChecked(True)
        rail.addSeparator()
        act_editor = QAction("📝", self)
        act_editor.setToolTip("Editor")
        act_editor.setCheckable(True)
        act_editor.setChecked(True)
        act_editor.toggled.connect(self.editor.setVisible)
        rail.addAction(act_editor)

    # ---------- toolbar superior ----------
    def _build_toolbar(self):
        tb = QToolBar("Principal")
        tb.setMovable(False)
        self.addToolBar(tb)

        act_dir = QAction("📂 Abrir proyecto", self)
        act_dir.triggered.connect(self._pick_dir)
        tb.addAction(act_dir)

        act_save = QAction("💾", self)
        act_save.setToolTip("Guardar (Ctrl+S)")
        act_save.setShortcut(QKeySequence.Save)
        act_save.triggered.connect(self.editor.editor.save)
        tb.addAction(act_save)
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

        spacer = QLabel("   ")
        tb.addWidget(spacer)
        self.lbl_status = QLabel("Ollama …")
        self.lbl_status.setStyleSheet("color:#7ab3e0;")
        tb.addWidget(self.lbl_status)

    def _fill_backends(self):
        for key, cfg in backends.BACKENDS.items():
            self.chat.cmb_backend.addItem(cfg["nombre"], key)
        self.chat.cmb_backend.currentIndexChanged.connect(self._load_models)
        self._load_models()

    def _wire(self):
        self.tree.file_opened.connect(self.editor.open_file)
        self.editor.file_saved.connect(
            lambda p: consola.log_info("editor", "guardado " + p))
        self.chat.send_requested.connect(self._send)
        self.chat.stop_requested.connect(self._stop)
        self.chat.attach_requested.connect(self._attach)

    # ---------- proyecto ----------
    def set_root(self, root):
        self._root = root
        self.tree.set_root(root)
        self.editor.set_root(root)
        memoria.load(root)

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Carpeta del proyecto",
                                             self._root)
        if d:
            self.set_root(d)

    def _attach(self, kind):
        dest = os.path.join(self._root, "adjuntos")
        os.makedirs(dest, exist_ok=True)
        if kind == "files":
            paths, _ = QFileDialog.getOpenFileNames(self, "Adjuntar archivos")
        else:
            d = QFileDialog.getExistingDirectory(self, "Adjuntar carpeta")
            paths = [d] if d else []
        for p in paths:
            target = os.path.join(dest, os.path.basename(p))
            try:
                if os.path.isdir(p):
                    shutil.copytree(p, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(p, target)
                self.chat.add_attachment(target)
                consola.log_info("adjuntos", "copiado " + target)
            except OSError as e:
                consola.log_error("adjuntos", repr(e))

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
        self._messages = ([{"role": "system",
                            "content": self._build_system()}]
                          + [m for m in self._messages
                             if m["role"] != "system"])
        self._messages.append({"role": "user", "content": msg})
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
