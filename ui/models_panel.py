"""Panel de modelos: instalados, catálogo con descarga y compatibilidad."""
import os
import re
import subprocess

from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QMessageBox,
                               QProgressBar, QPushButton, QScrollArea,
                               QSpinBox, QVBoxLayout, QWidget)

from core import backends, bench, catalogo, consola, db, hwinfo, ollama

CSS = ("QWidget{background:#212126;color:#e2e2e6;}"
       "QListWidget,QScrollArea{background:#232329;border:1px solid #3a3a42;}"
       "QLineEdit,QComboBox,QSpinBox{background:#232329;border:1px solid #3a3a42;"
       "border-radius:4px;padding:3px 6px;color:#e2e2e6;}"
       "QPushButton{background:#2e7fb8;color:#fff;border:none;"
       "border-radius:4px;padding:4px 10px;}"
       "QPushButton:disabled{background:#303038;color:#777;}"
       "QProgressBar{background:#232329;border:1px solid #3a3a42;"
       "border-radius:4px;height:12px;text-align:center;font-size:10px;}"
       "QProgressBar::chunk{background:#2e7fb8;}")

PCT_RX = re.compile(r"(\d{1,3})\s*%")


class PullWorker(QThread):
    pct = Signal(int)
    done = Signal(int)

    def __init__(self, tag):
        super().__init__()
        self._tag = tag
        self._proc = None
        self._cancelled = False

    def stop(self):
        self._cancelled = True
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    def run(self):
        env = dict(os.environ)
        env["OLLAMA_MODELS"] = ollama.MODELS_DIR
        try:
            self._proc = subprocess.Popen(
                [ollama._ollama_exe(), "pull", self._tag],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, env=env, errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            for ln in self._proc.stdout:
                ln = ln.strip()
                m = PCT_RX.search(ln)
                if m:
                    self.pct.emit(min(100, int(m.group(1))))
                if ln:
                    consola.log_info("pull " + self._tag, ln)
            code = self._proc.wait()
            self.done.emit(-1 if self._cancelled else code)
        except Exception as e:
            consola.log_error("pull", repr(e))
            self.done.emit(1)


class HwWorker(QThread):
    done = Signal(dict)

    def run(self):
        self.done.emit(hwinfo.scan())


class BenchWorker(QThread):
    """Prueba cada modelo instalado midiendo su latencia real."""
    step = Signal(str, int, object)   # modelo, ms, ok | error
    done = Signal(list)

    def __init__(self, models):
        super().__init__()
        self._models = models

    def run(self):
        res = []
        for m in self._models:
            ok, ms, err = bench.ping_model("ollama", m)
            db.save_bench(m, ok, ms)
            self.step.emit(m, ms, ok if ok else err)
            res.append((m, ok, ms))
        self.done.emit(res)


class ModelRow(QFrame):
    pull_requested = Signal(str, object)  # tag, row
    selected = Signal(str)

    def __init__(self, info, hw):
        super().__init__()
        self.info = info
        self.setCursor(Qt.PointingHandCursor)
        compat = hwinfo.compatible(info, hw)
        mark = "✓" if compat else ("✗" if compat is False else "·")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 7, 10, 7)
        lay.setSpacing(3)

        top = QHBoxLayout()
        lbl = QLabel(f"<b>{info['nombre']}</b>")
        lbl.setStyleSheet("font-size:13px;color:#e8e8e8;")
        top.addWidget(lbl, 1)
        self._badge = QLabel(mark)
        self._badge.setStyleSheet(
            "font-size:14px;color:"
            + ("#4ec9b0" if compat else "#e06c60") + ";")
        top.addWidget(self._badge)
        self.btn = QPushButton("Descargar")
        self.btn.setStyleSheet("font-size:12px;padding:5px 12px;"
                               "background:#2e7fb8;")
        self.btn.clicked.connect(
            lambda: self.pull_requested.emit(info["tag"], self))
        top.addWidget(self.btn)
        self.btn_stop = QPushButton("✕")
        self.btn_stop.setFixedWidth(34)
        self.btn_stop.setStyleSheet("font-size:13px;padding:5px 8px;"
                                    "background:#6e2f2f;")
        self.btn_stop.setVisible(False)
        top.addWidget(self.btn_stop)
        lay.addLayout(top)

        specs = (f"{info['peso']} · {info['gb']} GB · "
                 f"RAM ≥ {info['ram_gb']} GB · contexto {info['ctx']//1024}k")
        sl = QLabel(specs)
        sl.setStyleSheet("font-size:12px;color:#8a8a8a;")
        lay.addWidget(sl)

        self.bar = QProgressBar()
        self.bar.setMinimumHeight(14)
        self.bar.setVisible(False)
        lay.addWidget(self.bar)
        self.setStyleSheet(
            "QFrame{border-bottom:1px solid #32323a;}"
            "QFrame:hover{background:#2a2a30;}")

    def mousePressEvent(self, event):
        if self.btn.isEnabled() and self.btn.isVisible():
            self.pull_requested.emit(self.info["tag"], self)
        self.selected.emit(self.info["tag"])
        super().mousePressEvent(event)

    def set_installed(self):
        self.btn.setText("Instalado")
        self.btn.setStyleSheet("font-size:12px;padding:5px 12px;"
                               "background:#234d35;color:#7fdca8;")
        self.btn.setEnabled(False)
        self.bar.setVisible(False)


class ModelsPanel(QWidget):
    installed = Signal(str)   # tag instalado con éxito

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(CSS)
        self._pulls = {}
        self._hw = db.last_hw_scan()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)

        lay.addWidget(QLabel("Instalados"))
        self._list = QListWidget()
        self._list.setMaximumHeight(90)
        lay.addWidget(self._list)

        row = QHBoxLayout()
        row.addWidget(QLabel("Catálogo"))
        self._filtro = QComboBox()
        self._filtro.addItems(["todos", "ligero", "medio", "fuerte"])
        self._filtro.currentTextChanged.connect(self._render_catalogo)
        row.addWidget(self._filtro)
        lay.addLayout(row)

        self._buscar = QLineEdit()
        self._buscar.setPlaceholderText("Buscar modelos gratuitos…")
        self._buscar.textChanged.connect(self._render_catalogo)
        lay.addWidget(self._buscar)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._cat = QWidget()
        self._cat_lay = QVBoxLayout(self._cat)
        self._cat_lay.setAlignment(Qt.AlignTop)
        self._cat_lay.setSpacing(0)
        self._cat_lay.setContentsMargins(0, 0, 0, 0)
        self._scroll.setWidget(self._cat)
        lay.addWidget(self._scroll, 1)

        self._render_catalogo()
        self._sel = None

        row2 = QHBoxLayout()
        btn_dir = QPushButton("Carpeta")
        btn_dir.setStyleSheet("background:#303038;")
        btn_dir.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(ollama.MODELS_DIR)))
        btn_ref = QPushButton("↻")
        btn_ref.setStyleSheet("background:#303038;")
        btn_ref.clicked.connect(self.refresh)
        btn_bench = QPushButton("Analizar")
        btn_bench.setStyleSheet("background:#303038;")
        btn_bench.setToolTip("Mide qué tan rápido responde cada modelo")
        btn_bench.clicked.connect(self.analyze)
        btn_aj = QPushButton("Rendimiento")
        btn_aj.setStyleSheet("background:#303038;")
        btn_aj.setToolTip("Velocidad, contexto, tokens e hilos del modelo")
        btn_aj.clicked.connect(self._ajustes)
        row2.addWidget(btn_dir, 1)
        row2.addWidget(btn_aj)
        row2.addWidget(btn_bench)
        row2.addWidget(btn_ref)
        lay.addLayout(row2)

        self._status = QLabel("Modelos en: " + ollama.MODELS_DIR)
        self._status.setWordWrap(True)
        self._status.setStyleSheet("color:#888;font-size:10px;")
        lay.addWidget(self._status)
        self.refresh()

    # ---------- catálogo ----------
    def _render_catalogo(self):
        while self._cat_lay.count():
            it = self._cat_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        installed = set(backends.list_models("ollama"))
        filtro = self._filtro.currentText()
        texto = self._buscar.text().strip().lower()
        for info in catalogo.CATALOGO:
            if filtro != "todos" and info["peso"] != filtro:
                continue
            if texto and texto not in info["nombre"].lower() \
                    and texto not in info["tag"].lower():
                continue
            row = ModelRow(info, self._hw)
            if info["tag"] in installed:
                row.set_installed()
            row.pull_requested.connect(self._pull)
            row.selected.connect(self._select_model)
            self._cat_lay.addWidget(row)

    def _pull(self, tag, row):
        if tag in self._pulls:
            return
        row.btn.setVisible(False)
        row.btn_stop.setVisible(True)
        row.bar.setVisible(True)
        row.btn_stop.clicked.connect(
            lambda _c, t=tag, r=row: self._confirm_cancel(t, r))
        w = PullWorker(tag)
        w.pct.connect(row.bar.setValue)
        w.done.connect(lambda c, t=tag, r=row: self._pull_done(t, r, c))
        self._pulls[tag] = w
        self._status.setText("Descargando " + tag + "…")
        w.start()

    def _confirm_cancel(self, tag, row):
        w = self._pulls.get(tag)
        if not w:
            return
        ans = QMessageBox.question(
            self, "Cancelar descarga",
            f"¿Seguro que quieres cancelar la descarga de {tag}?")
        if ans == QMessageBox.Yes:
            w.stop()

    def _pull_done(self, tag, row, code):
        self._pulls.pop(tag, None)
        row.btn_stop.setVisible(False)
        if code == 0:
            row.set_installed()
            self.refresh()
            self.installed.emit(tag)
        elif code == -1:
            row.bar.setVisible(False)
            row.bar.setValue(0)
            row.btn.setVisible(True)
            self._status.setText("Descarga de " + tag + " cancelada.")
        else:
            row.bar.setVisible(False)
            row.btn.setVisible(True)
            self._status.setText(f"Falló {tag} (exit {code}) — ver consola")

    # ---------- prefs por modelo ----------
    def _select_model(self, model):
        self._sel = model

    def _ajustes(self):
        model = self._sel or (backends.list_models("ollama") or [None])[0]
        if not model:
            self._status.setText("Sin modelo para ajustar.")
            return
        from ui.ajustes_dialog import AjustesDialog
        AjustesDialog(model, self).exec()

    def save_prefs(self, model):
        self._sel = model

    # ---------- hardware ----------
    def scan_hardware(self):
        self._status.setText("Analizando el equipo…")
        self._hw_worker = HwWorker()
        self._hw_worker.done.connect(self._hw_done)
        self._hw_worker.start()

    def _hw_done(self, datos):
        self._hw = datos
        db.save_hw_scan(datos)
        gpus = ", ".join(g["nombre"] for g in datos["gpu"]) or "sin GPU"
        resumen = (f"RAM {datos['ram_gb']} GB · CPU {datos['cpu'][:40]} · "
                   f"GPU {gpus} · Disco libre {datos['disco_libre_gb']} GB")
        self._status.setText(resumen)
        consola.log_info("hw", resumen)
        self._render_catalogo()
        QMessageBox.information(self, "Requerimientos del equipo", resumen)

    def refresh(self):
        self._list.clear()
        for m in backends.list_models("ollama") \
                or ["(Ollama desconectado o sin modelos)"]:
            b = db.get_bench(m)
            suf = f"   ✓ {b[1] / 1000:.1f} s" if b and b[0] else \
                  ("   ✗ sin respuesta" if b else "")
            self._list.addItem(m + suf)

    # ---------- analizador ----------
    def analyze(self):
        models = backends.list_models("ollama")
        if not models:
            self._status.setText("Sin modelos instalados para analizar.")
            return
        self._status.setText(f"Analizando {len(models)} modelos…")
        self._bench = BenchWorker(models)
        self._bench.step.connect(
            lambda m, ms, r: self._status.setText(
                f"{m}: " + (f"✓ {ms / 1000:.1f} s"
                           if r is True else f"✗ {r}")))
        self._bench.done.connect(self._bench_done)
        self._bench.start()

    def _bench_done(self, res):
        ok = [x for x in res if x[1]]
        mal = [x[0] for x in res if not x[1]]
        for m, okk, ms in res:
            consola.log_info("bench", f"{m}: "
                             + (f"✓ {ms / 1000:.1f} s" if okk else "✗"))
        rapido = min(ok, key=lambda x: x[2])[0] if ok else "—"
        self._status.setText(
            f"Funcionan: {len(ok)}/{len(res)} · más rápido: {rapido}"
            + (f" · fallan: {', '.join(mal)}" if mal else ""))
        self.refresh()
