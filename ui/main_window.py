"""Ventana principal: riel de iconos, stack lateral, chat central, editor."""
import os
import shutil

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QDockWidget, QFileDialog, QMainWindow,
                               QMessageBox, QSplitter, QStackedWidget)

from core import backends, consola, db, memoria, ollama, prompts
from ui import barras, ota_ui
from ui.chat_panel import ChatPanel
from ui.console_panel import ConsolePanel
from ui.editor_panel import EditorPanel
from ui.ajustes_dialog import AjustesDialog
from ui.equipo_dialog import EquipoDialog
from ui.models_panel import ModelsPanel
from ui.nuevo_proyecto import NuevoProyectoDialog, crear_proyecto
from ui.tree_panel import TreePanel
from ui.worker import ChatWorker, ScanWorker

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
        self._queue = []          # mensajes en espera, en orden
        self._messages = []
        self._self_mode = False
        self._root = os.getcwd()
        self._data_dir = os.path.join(os.path.expanduser("~"),
                                      "Downloads", "agente-desktop")

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
        QTimer.singleShot(900, self._ask_perm_descargas)
        QTimer.singleShot(2500, lambda: ota_ui.check_and_prompt(
            self, self.chat))

    def _ask_perm_descargas(self):
        """Pide UNA vez: guardar en Descargas + permisos de administrador."""
        if db.get_cfg("perm_descargas") is not None \
                and db.get_cfg("perm_admin") is not None:
            return
        ans = QMessageBox.question(
            self, "Permisos del agente (una sola vez)",
            "¿Otorgar al agente permisos de administrador para actuar "
            "en todo tu equipo (crear carpetas, ejecutar comandos, "
            "abrir programas) y guardar sus archivos en:\n\n"
            + self._data_dir
            + "\n\nSolo se pregunta una vez; se guarda tu respuesta.")
        ok = "1" if ans == QMessageBox.Yes else "0"
        db.set_cfg("perm_admin", ok)
        db.set_cfg("perm_descargas", ok)
        os.makedirs(self._data_dir, exist_ok=True)

    def _equipo_info(self):
        EquipoDialog(self).exec()
        self.models.scan_hardware()  # refresca compatibilidad del catálogo

    def _scan_hw(self):
        self._equipo_info()

    def _ajustes(self):
        model = self.chat.cmb_model.currentText()
        if model and not model.startswith("("):
            AjustesDialog(model, self).exec()
            consola.log_info("ui", "rendimiento ajustado para " + model)

    def _fill_backends(self):
        for key, cfg in backends.BACKENDS.items():
            self.chat.cmb_backend.addItem(cfg["nombre"], key)
        prev = db.get_cfg("ultimo_backend")
        if prev is not None:
            i = self.chat.cmb_backend.findData(prev)
            if i >= 0:
                self.chat.cmb_backend.setCurrentIndex(i)
        self.chat.cmb_backend.currentIndexChanged.connect(self._load_models)
        self._load_models()

    def _wire(self):
        self.tree.file_opened.connect(self.editor.open_file)
        self.proyecto_tree.file_opened.connect(self.editor.open_file)
        self.editor.file_saved.connect(
            lambda p: (consola.log_info("editor", "guardado " + p),
                       memoria.invalidate(self._root)))
        self.chat.send_requested.connect(self._send)
        self.chat.stop_requested.connect(self._stop)
        self.chat.attach_requested.connect(self._attach)
        self.chat.cmb_model.currentTextChanged.connect(
            self.models._select_model)
        self.chat.cmb_model.currentTextChanged.connect(self._model_rule)
        self.chat.cmb_model.currentTextChanged.connect(self._save_model_sel)
        prev_voz = db.get_cfg("ultima_voz")
        if prev_voz:
            i = self.chat.cmb_voz.findText(prev_voz)
            if i >= 0:
                self.chat.cmb_voz.setCurrentIndex(i)
        self.chat.cmb_voz.currentTextChanged.connect(
            lambda t: db.set_cfg("ultima_voz", t))
        self._last_text = ""

    def _save_model_sel(self, text):
        if text and not text.startswith("("):
            db.set_cfg("ultimo_modelo", text)

    def _model_rule(self, text):
        if text and not text.startswith("("):
            self.chat.add_rule("Pensando con " + text)

    # ---------- proyecto ----------
    def set_root(self, root):
        self._root = root
        self.tree.set_root(root)
        self.proyecto_tree.set_root(root)
        self.editor.set_root(root)
        memoria.invalidate(root)
        self.chat.add_system("Analizando todo el proyecto…")
        self._scan = ScanWorker(root)
        self._scan.done.connect(self._scan_done)
        self._scan.start()

    def _scan_done(self, data, root):
        if root != self._root:
            return
        n, m = len(data["files"]), len(data["dirs"])
        self.chat.add_system(
            f"Proyecto analizado: {n} archivos en {m} carpetas — "
            "tengo todo su contenido en memoria.")
        consola.log_info("memoria", f"{n} archivos indexados en {root}")

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Abrir proyecto (carpeta)",
                                             self._root)
        if d:
            self.set_root(d)
            self._stack.setCurrentIndex(0)
            self.editor._label.setText(
                f"  ▸ {os.path.basename(d)}  ›  (elige un archivo del árbol)")
            self.chat.add_system("Proyecto abierto: " + d)

    def _nuevo_proyecto(self):
        base = os.path.join(self._data_dir, "proyectos")
        os.makedirs(base, exist_ok=True)
        dlg = NuevoProyectoDialog(base, self)
        if dlg.exec() and dlg.ruta:
            ruta = crear_proyecto(dlg.ruta, dlg._plantilla.currentText())
            self.set_root(ruta)
            self._stack.setCurrentIndex(0)
            self.chat.add_system("Proyecto creado en " + ruta)
            consola.log_info("proyecto", "creado " + ruta)

    def _attach(self, kind):
        dest = os.path.join(self._data_dir, "adjuntos")
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
        memoria.invalidate(self._root)
        if ultimo:
            self._stack.setCurrentIndex(0)
            self.tree.reveal(ultimo)
            if os.path.isdir(ultimo):
                self.proyecto_tree.set_root(ultimo)
                self.editor.set_root(ultimo)
                self.editor._label.setText(
                    f"  ▸ {os.path.basename(ultimo)}  ›  "
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
        if backend:
            db.set_cfg("ultimo_backend", backend)
        prev = db.get_cfg("ultimo_modelo")
        models = backends.list_models(backend)
        self.chat.cmb_model.blockSignals(True)
        self.chat.cmb_model.clear()
        self.chat.cmb_model.addItems(models or ["(sin modelos)"])
        self.chat.cmb_model.blockSignals(False)
        if prev and prev in (models or []):
            self.chat.cmb_model.setCurrentText(prev)
        elif models:
            db.set_cfg("ultimo_modelo", models[0])
            self.chat.cmb_model.setCurrentText(models[0])

    # ---------- chat ----------
    def _send(self, text, attachments):
        backend = self.chat.cmb_backend.currentData()
        model = self.chat.cmb_model.currentText()
        if not model or model.startswith("("):
            self.chat.add_system("No hay modelo disponible en ese motor.")
            return
        if self._worker is not None:
            self._queue.append((text, attachments))
            self.chat.add_user(text or "(adjuntos)")
            self.chat.add_system(
                f"En cola ({len(self._queue)}): se procesará en orden "
                "al terminar la respuesta actual.")
            return
        msg = text
        if attachments:
            msg += "\n\nAdjuntos (copiados en adjuntos/):\n" + "\n".join(
                "- " + os.path.relpath(p, self._root) for p in attachments)
        self._last_text = text
        self.chat.add_user(text or "(adjuntos)")
        self.models.save_prefs(model)
        system = prompts.build_system(
            self.editor.context(), self._root, self._self_mode,
            detalle=db.get_cfg("detalle:" + model, "media"))
        historial = [m for m in self._messages
                     if m["role"] != "system"][-8:]
        self._messages = ([{"role": "system", "content": system}]
                          + historial)
        msg += ("\n\n(Instrucción interna: responde SIEMPRE en español. "
                "Nunca respondas en inglés ni otro idioma.)")
        self._messages.append({"role": "user", "content": msg})
        db.log_chat("user", msg)
        options = {k: v for k, v in db.get_model_prefs(model).items()
                   if k in ("num_ctx", "num_predict", "temperature")}
        options["num_thread"] = int(db.get_cfg(
            "num_thread", os.cpu_count() or 4))
        self.chat.start_stream()
        self.chat.set_busy(True)
        self._worker = ChatWorker(backend, model, self._messages, self._root,
                                  options=options)
        self._worker.token.connect(self.chat.append_token)
        self._worker.card.connect(self.chat.add_card)
        self._worker.finished_text.connect(self._chat_done)
        self._worker.failed.connect(self._chat_failed)
        self._worker.stat.connect(self.chat.add_rule)
        self._worker.perf.connect(lambda dt, ntok, m=model:
                                  self._auto_tune(m, dt, ntok))
        self._worker.open_dir.connect(self.set_root)
        self._worker.start()

    def _stop(self):
        if self._worker:
            self._worker.request_stop()
        self._queue.clear()          # stop también limpia la cola
        self.chat.add_system("El usuario detuvo la respuesta.")
        if self._last_text and not self.chat.input.toPlainText().strip():
            self.chat.input.setPlainText(self._last_text)

    def _auto_tune(self, model, dt, ntok):
        """Si el modelo va lento (<4 tok/s), reduce contexto/respuesta."""
        if dt <= 0 or db.get_cfg("auto_tune", "1") != "1":
            return
        vel = ntok / dt
        if vel >= 4 or ntok < 20:
            return
        p = db.get_model_prefs(model)
        npred = p["num_predict"]
        npred = max(256, npred // 2) if npred > 0 else 512
        nctx = max(1024, min(int(p["num_ctx"]) // 2, 2048))
        db.set_model_prefs(model, "custom", nctx, npred,
                           p["temperature"])
        consola.log_info(
            "auto-ajuste",
            f"{model} lento ({vel:.1f} tok/s) → ctx {nctx}, "
            f"max {npred}")
        self.chat.add_rule(
            f"auto-ajuste: {model} iba a {vel:.1f} tok/s — reduje "
            f"contexto y respuesta para ir más rápido")

    def _chat_done(self, text):
        self.chat.end_stream()
        self.chat.set_busy(False)
        if text:
            self._messages.append({"role": "assistant", "content": text})
            db.log_chat("assistant", text)
        self._worker = None
        self._desencolar()

    def _chat_failed(self, err):
        self.chat.end_stream()
        self.chat.set_busy(False)
        self.chat.add_system("Error: " + err)
        self._worker = None
        self._desencolar()

    def _desencolar(self):
        """Procesa el siguiente mensaje de la cola, en orden."""
        if self._queue:
            text, attachments = self._queue.pop(0)
            self.chat.add_system("Procesando mensaje en cola…")
            self._send(text, attachments)
