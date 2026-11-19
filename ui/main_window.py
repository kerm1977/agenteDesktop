"""Ventana principal: riel de iconos, stack lateral, chat central, editor."""
import os
import re
import shutil

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QDockWidget, QFileDialog, QInputDialog,
                               QLineEdit, QMainWindow, QMessageBox,
                               QSplitter, QStackedWidget)

from core import backends, consola, db, memoria, ollama, prompts, tools
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
        if model.startswith("("):   # (Automático): ajusta el 1.º real
            model = next((self.chat.cmb_model.itemText(i)
                          for i in range(self.chat.cmb_model.count())
                          if not self.chat.cmb_model.itemText(i)
                          .startswith("(")), "")
        if model:
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
        self.models.installed.connect(
            lambda _tag: (self._load_models(),
                          self.chat.add_system(
                              "Modelo instalado — ya está en el selector.")))
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
        if text and (text == "(Automático)"
                     or not text.startswith("(")):
            db.set_cfg("ultimo_modelo", text)
            self._precargar()   # el nuevo modelo entra en RAM de una vez

    def _model_rule(self, text):
        if text and not text.startswith("("):
            self.chat.add_rule("Pensando con " + text)

    # ---------- proyecto ----------
    def set_root(self, root):
        self._root = root
        # historial persistente de proyectos (último siempre en [0])
        try:
            import json as _j
            hist = _j.loads(db.get_cfg("historial_roots", "[]"))
        except Exception:
            hist = []
        hist = [h for h in hist if h.get("path") != root]
        hist.insert(0, {"id": (hist[0]["id"] + 1) if hist else 1,
                        "path": root,
                        "nombre": os.path.basename(
                            root.rstrip("\\/")) or root})
        db.set_cfg("historial_roots", _j.dumps(hist[:12],
                                               ensure_ascii=False))
        db.set_cfg("ultimo_root", root)
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
        if backend == "openai":
            self._config_openai()
        prev = db.get_cfg("ultimo_modelo")
        models = backends.list_models(backend)
        self.chat.cmb_model.blockSignals(True)
        self.chat.cmb_model.clear()
        self.chat.cmb_model.addItems(["(Automático)"]
                                     + (models or ["(sin modelos)"]))
        self.chat.cmb_model.blockSignals(False)
        # auto-análisis: cualquier modelo nuevo se mide en 2.º plano
        try:
            from core import perfil
            falta = perfil.faltantes(models or [])
            if falta:
                consola.log_info("perfil", "midiendo: " + ", ".join(falta))
                threading.Thread(
                    target=perfil.analizar, args=(falta,),
                    daemon=True).start()
        except Exception as e:
            consola.log_error("perfil", repr(e))
        if prev and prev in (["(Automático)"] + (models or [])):
            self.chat.cmb_model.setCurrentText(prev)
        elif models:
            db.set_cfg("ultimo_modelo", models[0])
            self.chat.cmb_model.setCurrentText(models[0])
        self._restaurar_root()

    def _config_openai(self):
        """Carga la clave OpenAI guardada en Ajustes (sin preguntar)."""
        if os.environ.get("OPENAI_API_KEY"):
            return
        key = db.get_cfg("openai_key")
        if key:
            backends.configure_openai(key, db.get_cfg("openai_base"))

    def _restaurar_root(self):
        """Al arrancar vuelve al último proyecto trabajado."""
        if getattr(self, "_root_restaurado", False):
            return
        self._root_restaurado = True
        ult = db.get_cfg("ultimo_root")
        if ult and os.path.isdir(ult) and ult != self._root:
            self.set_root(ult)
            self.chat.add_system(
                "Proyecto restaurado: " + ult)
        self._precargar()

    def _precargar(self):
        """Carga el modelo activo en RAM: primera respuesta al instante."""
        backend = self.chat.cmb_backend.currentData()
        model = self.chat.cmb_model.currentText()
        if not model or model.startswith("("):
            return
        import threading
        def go():
            if backends.preload(backend, model):
                consola.log_info("ram", f"{model} precargado en RAM")
        threading.Thread(target=go, daemon=True).start()

    def _elegir_modelo(self, text):
        """Inteligencia dinámica: el mejor modelo instalado por pregunta."""
        actual = self.chat.cmb_model.currentText()
        instalados = [self.chat.cmb_model.itemText(i)
                      for i in range(self.chat.cmb_model.count())
                      if not self.chat.cmb_model.itemText(i).startswith("(")]
        auto = (actual.startswith("(")
                or db.get_cfg("dinamico", "1") == "1")
        if not auto or not instalados:
            return actual, None
        if actual.startswith("(") and len(instalados) == 1:
            return instalados[0], True
        t = text.lower()
        perfil = {}
        try:   # perfil medido por analizar_modelos.py (persistente)
            import json
            ruta = os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "perfil_modelos.json")
            with open(ruta, encoding="utf-8") as f:
                perfil = json.load(f)
        except Exception:
            pass
        codigo = re.search(
            r"c[oó]digo|program|funci[oó]n|clase|bug|error|depura|html|css|"
            r"python|javascript|sql|flask|django|script|archivo|proyecto",
            t)
        if codigo:
            pref = [m for m in instalados
                    if re.search(r"coder|code|deepseek|starcoder", m)]
            if pref:
                pick = min(
                    pref,
                    key=lambda m: perfil.get(m, {}).get("code_ms")
                    or 99999)
                return pick, pick != actual
        # charla general -> generalista más capaz instalado
        gens = [m for m in instalados if re.search(
            r"^(?!.*coder|.*code)(llama|qwen|mistral|gemma|phi|yi|deepseek-?llm)",
            m)]
        if gens:
            ok = [m for m in gens
                  if perfil.get(m, {}).get("ok_gen", True)]
            if ok and perfil:
                pick = min(ok, key=lambda m: perfil.get(
                    m, {}).get("general_ms") or 99999)
                return pick, pick != actual
            def _bigs(m):   # tamaño aproximado: 7b>3b>1.5b>0.5b
                mm = re.search(r"(\d+(?:\.\d+)?)\s*b", m)
                return float(mm.group(1)) if mm else 0
            mejor = max(gens, key=_bigs)
            return mejor, mejor != actual
        def _vel(m):
            b = db.get_bench(m)
            return b[1] if b and b[1] else 99999
        rapido = min(instalados, key=_vel)
        return rapido, rapido != actual

    # ---------- chat ----------
    # ---------- acciones directas (sin modelo) ----------
    def _donde(self, t):
        """Carpeta destino según palabras del usuario."""
        home = os.path.expanduser("~")
        if re.search(r"escritorio|desktop", t):
            for d in ("Desktop", "Escritorio"):
                p = os.path.join(home, d)
                if os.path.isdir(p):
                    return p
            return os.path.join(home, "Desktop")
        if "descarga" in t:
            return os.path.join(home, "Downloads")
        if "documento" in t:
            return os.path.join(home, "Documents")
        m = re.search(r"[a-z]:[\\/][\w\-.\\/ ]+", t)
        if m:
            return m.group(0).strip()
        return self._data_dir

    def _nombre(self, text):
        m = re.search(
            r"(?:llamad[ao]s?|llame|nombre)\s+([\w\-. ]+?)(?:\s+en\s|\s*$|[.,])",
            text, re.I)
        if m:
            return m.group(1).strip().strip('"\'')
        m = re.search(r"(?:llamad[ao]s?|se llame|nombre)\s+"
                      r"([\w\-. ]+?)(?:\s+(?:en|y|con|que|para)\s|[.,]|$)",
                      text, re.I)
        if not m:
            m = re.search(r"(?:carpeta|directorio|archivo)\s+([\w\-. ]+?)"
                          r"(?:\s+en\s|[.,]|$)", text, re.I)
        if not m:
            return None
        nom = m.group(1).strip().strip('"\'')
        # corta el nombre en el primer verbo/palabra de acción incrustada
        nom = re.split(
            r"\b(?:tienes|tiene|puedes|puedo|quiero|necesito|queremos|"
            r"utilizando|usando|mediante|capacidad|debes|debe)\b",
            nom)[0].strip()
        return nom or None

    def _crear_web(self, text):
        """Genera una página web de verdad: carpeta + index.html con CDN."""
        nombre = (self._nombre(text) or "mi-web").replace(" ", "-")
        base = os.path.join(self._donde(text.lower()), nombre)
        os.makedirs(base, exist_ok=True)
        m = re.search(r"que diga (.*?)(?:\.|$)|diga (.*?)(?:\.|$)", text, re.I)
        saludo = (m.group(1) or m.group(2)).strip() if m else (
            "Hola mundo — primera página creada con Mini Agente")
        html = ("<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n"
                "<meta charset=\"UTF-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, "
                "initial-scale=1\">\n"
                "<title>" + nombre + "</title>\n"
                "<link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/"
                "dist/css/bootstrap.min.css\" rel=\"stylesheet\">\n"
                "</head>\n"
                "<body class=\"d-flex align-items-center justify-content-"
                "center vh-100 bg-dark text-light\">\n"
                "<h1 class=\"display-4\">" + saludo + "</h1>\n"
                "<script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/"
                "dist/js/bootstrap.bundle.min.js\"></script>\n"
                "</body>\n</html>\n")
        index = os.path.join(base, "index.html")
        with open(index, "w", encoding="utf-8") as f:
            f.write(html)
        return self._ejecutar(
            text, "crear página web", "@OPEN:" + base,
            "Página creada en: " + index
            + "\n(ábrela doble-clic o en el editor)")

    def _ejecutar(self, text, titulo, detalle, ok_msg):
        """Muestra la acción como tarjeta + respuesta, y abre raíz si aplica."""
        self.chat.add_user(text)
        if detalle.startswith("@OPEN:"):
            dest = detalle[6:]
            self.set_root(dest)
            self._stack.setCurrentIndex(0)
            detalle = dest
        self.chat.add_card(titulo, detalle)
        self.chat.add_system(ok_msg)
        db.log_chat("user", text)
        db.log_chat("assistant", ok_msg + "\n" + detalle)
        consola.log_info("tool", titulo)
        return True

    def _accion_directa(self, text):
        """Ordenes comunes del equipo ejecutadas al instante."""
        if not text.strip():
            return False
        t = " " + text.lower().strip() + " "
        if "sabes" in t or "puedes " in t and "crea" not in t:
            return False
        from core import ordenes
        ints = ordenes.intenciones(t)
        crear = "crear" in ints
        borrar = "borrar" in ints
        renom = "renombrar" in ints
        abrir = "abrir" in ints
        leer = "analizar" in ints or "verificar" in ints
        mover = "mover" in ints
        cosa = re.search(r"carpeta|directorio|archivo|documento|fichero|"
                         r"aplicaci[oó]n|proyecto", t)

        # preguntas (dónde, cuál, qué es…) nunca son órdenes de acción
        if re.search(r"d[oó]nde|cu[aá]l|qu[eé] es|c[oó]mo se llama|"
                     r"por ?qu[eé]|cu[aá]ndo", t):
            return False
        # "elimina/borra X" tiene prioridad sobre cualquier "crear"
        # mencionado en la frase ("lo que acabas de crear…")
        if borrar:
            # "elimina el último proyecto" -> resuelto por el historial
            if re.search(r"[úu]ltim[ao]\w*\s+(proyecto|carpeta|p[aá]gina|"
                         r"web|trabajo|directorio)", t):
                try:
                    import json as _j
                    hist = _j.loads(db.get_cfg("historial_roots", "[]"))
                except Exception:
                    hist = []
                dest = (hist[0]["path"] if hist
                        else db.get_cfg("ultimo_root", ""))
                if dest:
                    return self._run(text, "delete_path", {"path": dest},
                                     "Eliminado último proyecto: " + dest)
                return False
            t2 = re.sub(r"gui[oó]n( medio)?", "-", t)
            m = re.search(
                r"([a-z]:\\[^\s\"*]+|"           # ruta absoluta
                r"\"([^\"]+)\"|'([^']+)'|"      # entre comillas
                r"([\w\-]+\.[a-z]{2,5})|"       # archivo.ext
                r"([\w]+\-[\w\-]+)|"            # nombre-con-guion
                r"(?:carpeta|p[aá]gina|web|sitio|directorio|proyecto)\s+"
                r"(?:llamad[ao]|nombrad[ao])?\s*([\w\-]+))",
                t2, re.I)
            nom = next((g for g in m.groups() if g), "").strip() if m else ""
            if nom:
                dest = nom if os.path.isabs(nom) else os.path.join(
                    self._donde(t2), nom)
                return self._run(text, "delete_path", {"path": dest},
                                 "Eliminado: " + dest)
            return False   # borrar sin nombre claro -> que pregunte el modelo
        # "crea una página/sitio/index.html" -> plantilla real al instante
        if crear and re.search(
                r"single.?page|simple.?page|p[aá]gina|index|sitio|"
                r"web ?app|web|html", t):
            return self._crear_web(text)
        # "crea una app/juego/programa" genérico -> lo intenta el modelo
        if re.search(r"app|aplicaci|juego|programa|script|c[oó]digo|"
                     r"calculadora|hola mundo", t):
            return False
        m = re.search(r"https?://\S*github\S*", text, re.I)
        if m and re.search(r"clon|repo|github|agrega", t):
            return self._run(text, "clone_repo", {"url": m.group(0).rstrip('.,)')},
                             "Repositorio clonado y abierto en el editor.")
        if crear and cosa:
            nombre = self._nombre(text) or "nueva-carpeta"
            if re.search(r"archivo|documento|fichero", t):
                return self._run(text, "write_file",
                                 {"path": os.path.join(self._donde(t), nombre),
                                  "content": ""},
                                 f"Archivo creado: {nombre}")
            dest = os.path.join(self._donde(t), nombre)
            tools.run_tool("create_dir", {"path": dest}, self._root)
            return self._ejecutar(
                text, "create_dir", "@OPEN:" + dest,
                f"Carpeta creada: {dest} (abierta en el editor)")
        if borrar and cosa:
            nombre = self._nombre(text)
            if nombre:
                dest = nombre if os.path.isabs(nombre) else os.path.join(
                    self._donde(t), nombre)
                return self._run(text, "delete_path", {"path": dest},
                                 f"Eliminado: {dest}")
        if renom and cosa:
            m = re.search(r"(?:renombra\w*|cambia el nombre\w*)\s+"
                          r"([\w\-. ]+?)\s+(?:a|por|como)\s+([\w\-. ]+?)"
                          r"(?:\s+en\s|\s*$|[.,])", text, re.I)
            if m:
                viejo = os.path.join(self._donde(t), m.group(1).strip())
                nuevo = os.path.join(os.path.dirname(viejo),
                                     m.group(2).strip())
                try:
                    os.rename(viejo, nuevo)
                    return self._ejecutar(text, "rename " + viejo,
                                          "-> " + nuevo,
                                          f"Renombrado a: {nuevo}")
                except OSError as e:
                    return self._ejecutar(text, "rename " + viejo, str(e),
                                          "No se pudo renombrar: " + viejo)
        if mover and cosa:
            m = re.search(r"([\w\-. ]+?)\s+(?:a|hacia)\s+([\w\-.\\/: ]+?)"
                          r"\s*$", text, re.I)
            if m:
                src = os.path.join(self._donde(t), m.group(1).strip())
                dst_dir = self._donde(" " + m.group(2).lower() + " ")
                try:
                    shutil.move(src, dst_dir)
                    return self._ejecutar(text, "move " + src, "-> " + dst_dir,
                                          f"Movido a: {dst_dir}")
                except OSError as e:
                    return self._ejecutar(text, "move " + src, str(e),
                                          "No se pudo mover: " + src)
        if leer and re.search(r"\.(pdf|docx|xlsx|pptx|txt|md|csv|json|py|js|"
                              r"html|xml)\b", t):
            m = re.search(r"([\w\-. ]+\.(?:pdf|docx|xlsx|pptx|txt|md|csv|"
                          r"json|py|js|html|xml))", text, re.I)
            ruta = m.group(1).strip()
            if not os.path.isabs(ruta):
                ruta = os.path.join(self._donde(t), ruta)
            return self._run(text, "read_doc", {"path": ruta},
                             "Documento leído.")
        if abrir and cosa:
            nombre = self._nombre(text)
            if nombre:
                dest = nombre if os.path.isabs(nombre) else os.path.join(
                    self._donde(t), nombre)
                return self._run(text, "open_dir", {"path": dest},
                                 f"Abierto en el editor: {dest}")
        if re.search(r"lista|escanea|explora|qué hay|que hay", t) and cosa:
            dest = self._donde(t)
            return self._run(text, "list_dir", {"path": dest},
                             f"Contenido de: {dest}")
        return False

    def _run(self, text, name, args, ok_msg):
        """Corre una herramienta al instante y la muestra."""
        try:
            titulo, detalle = tools.run_tool(name, args, self._root)
        except Exception as e:  # noqa: BLE001
            self.chat.add_user(text)
            self.chat.add_system(f"Error en {name}: {e}")
            consola.log_error("tool", f"{name}: {e}")
            db.log_chat("user", text)
            db.log_chat("assistant", f"Error en {name}: {e}")
            return True
        return self._ejecutar(text, titulo, detalle, ok_msg)

    def _send(self, text, attachments):
        if self._accion_directa(text):
            return
        backend = self.chat.cmb_backend.currentData()
        model, _avisa = self._elegir_modelo(text)
        if _avisa:
            self.chat.add_system(f"Inteligencia dinámica → {model}")
        if not model or model.startswith("("):
            self.chat.add_system("No hay modelo disponible en ese motor.")
            return
        self._precargar()
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
        nivel = db.get_cfg("detalle:" + model, "media")
        es_tecnico = re.search(
            r"c[oó]digo|program|funci[oó]n|clase|bug|error|depura|html|css|"
            r"python|javascript|sql|flask|django|script|archivo|proyecto|"
            r"carpeta|lee |analiza|resume|traduc|clona|github|herramienta",
            text.lower())
        system = prompts.build_system(
            self.editor.context(), self._root, self._self_mode,
            detalle=nivel, chat=not es_tecnico)
        historial = [m for m in self._messages
                     if m["role"] != "system"][-8:]
        self._messages = ([{"role": "system", "content": system}]
                          + historial)
        db.log_chat("user", msg)   # el log guarda solo lo que escribiste
        msg += ("\n\n(Instrucción interna: responde SIEMPRE en español. "
                "Nunca respondas en inglés ni otro idioma.)")
        self._messages.append({"role": "user", "content": msg})
        options = {k: v for k, v in db.get_model_prefs(model).items()
                   if k in ("num_ctx", "num_predict", "temperature")}
        caps = {"resumida": 160, "media": 700}   # el modelo no se pasa
        if nivel in caps:
            cur = options.get("num_predict")
            if cur is None or int(cur) <= 0 or int(cur) > caps[nivel]:
                options["num_predict"] = caps[nivel]
        options["num_thread"] = int(db.get_cfg(
            "num_thread", os.cpu_count() or 4))
        self.chat.start_stream()
        self.chat.set_busy(True)
        # el intérprete (modelo más rápido MEDIDO) traduce la intención
        interprete = None
        # mensajes cortos y claros no necesitan traducción: se ahorra tiempo
        if (db.get_cfg("interprete", "1") == "1"
                and len(text.strip()) >= 40):
            candidatos = [self.chat.cmb_model.itemText(i)
                          for i in range(self.chat.cmb_model.count())
                          if not self.chat.cmb_model.itemText(i)
                          .startswith("(") and
                          self.chat.cmb_model.itemText(i) != model]
            if candidatos:
                from core import perfil as _perfil
                p = _perfil.cargar()
                def _vel(m):
                    g = p.get(m, {}).get("general_ms")
                    if g:
                        return g
                    b = db.get_bench(m)
                    return b[1] if b and b[1] else 99999
                interprete = min(candidatos, key=_vel)
        self._worker = ChatWorker(backend, model, self._messages, self._root,
                                  options=options, interpreter=interprete,
                                  corte=(nivel == "resumida"))
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

    def _copy_chat(self):
        """Copia toda la conversación (Tú / Agente) al portapapeles."""
        from PySide6.QtWidgets import QApplication
        partes = []
        for role, content in db.chat_history():
            quién = "Tú" if role == "user" else "Agente"
            partes.append(f"{quién}:\n{content}")
        if self._messages:  # incluye lo aún no persistido
            pass
        texto = "\n\n---\n\n".join(partes) or "(conversación vacía)"
        QApplication.clipboard().setText(texto)
        self.chat.add_system(
            f"Conversación copiada ({len(partes)} mensajes) — "
            "pégala con Ctrl+V donde quieras.")
        consola.log_info("ui", f"chat copiado: {len(partes)} mensajes")

    def _desencolar(self):
        """Procesa el siguiente mensaje de la cola, en orden."""
        if self._queue:
            text, attachments = self._queue.pop(0)
            self.chat.add_system("Procesando mensaje en cola…")
            self._send(text, attachments)
