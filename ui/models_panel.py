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

from core import backends, catalogo, consola, db, hwinfo, ollama

CSS = ("QWidget{background:#18181a;color:#ddd;}"
       "QListWidget,QScrollArea{background:#131314;border:1px solid #2c2c30;}"
       "QLineEdit,QComboBox,QSpinBox{background:#131314;border:1px solid #2c2c30;"
       "border-radius:4px;padding:3px 6px;color:#ddd;}"
       "QPushButton{background:#0e639c;color:#fff;border:none;"
       "border-radius:4px;padding:4px 10px;}"
       "QPushButton:disabled{background:#2a2a2e;color:#666;}"
       "QProgressBar{background:#131314;border:1px solid #2c2c30;"
       "border-radius:4px;height:10px;text-align:center;font-size:9px;}"
       "QProgressBar::chunk{background:#0e639c;}")

PCT_RX = re.compile(r"(\d{1,3})\s*%")


class PullWorker(QThread):
    pct = Signal(int)
    done = Signal(int)

    def __init__(self, tag):
        super().__init__()
        self._tag = tag

    def run(self):
        env = dict(os.environ)
        env["OLLAMA_MODELS"] = ollama.MODELS_DIR
        try:
            proc = subprocess.Popen(
                [ollama._ollama_exe(), "pull", self._tag],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, env=env, errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            for ln in proc.stdout:
                ln = ln.strip()
                m = PCT_RX.search(ln)
                if m:
                    self.pct.emit(min(100, int(m.group(1))))
                if ln:
                    consola.log_info("pull " + self._tag, ln)
            self.done.emit(proc.wait())
        except Exception as e:
            consola.log_error("pull", repr(e))
            self.done.emit(1)


class HwWorker(QThread):
    done = Signal(dict)

    def run(self):
        self.done.emit(hwinfo.scan())


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
        self.btn = QPushButton("⬇ Descargar")
        self.btn.setStyleSheet("font-size:12px;padding:5px 12px;"
                               "background:#0e639c;")
        self.btn.clicked.connect(
            lambda: self.pull_requested.emit(info["tag"], self))
        top.addWidget(self.btn)
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
            "QFrame{border-bottom:1px solid #26262a;}"
            "QFrame:hover{background:#1e1e22;}")

    def mousePressEvent(self, event):
        if self.btn.isEnabled():
            self.pull_requested.emit(self.info["tag"], self)
        self.selected.emit(self.info["tag"])
        super().mousePressEvent(event)

    def set_installed(self):
        self.btn.setText("✔ Instalado")
        self.btn.setStyleSheet("font-size:12px;padding:5px 12px;"
                               "background:#234d35;color:#7fdca8;")
        self.btn.setEnabled(False)
        self.bar.setVisible(False)


class ModelsPanel(QWidget):
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

        cfg = QFrame()
        cfg.setStyleSheet("QFrame{border-top:1px solid #2c2c30;}")
        cl = QHBoxLayout(cfg)
        cl.addWidget(QLabel("Peso:"))
        self._peso = QComboBox()
        self._peso.addItems(["ligero", "medio", "fuerte"])
        self._peso.currentTextChanged.connect(self._peso_changed)
        cl.addWidget(self._peso)
        cl.addWidget(QLabel("Ctx:"))
        self._ctx = QSpinBox()
        self._ctx.setRange(512, 131072)
        self._ctx.setSingleStep(1024)
        cl.addWidget(self._ctx)
        cl.addWidget(QLabel("Max:"))
        self._pred = QSpinBox()
        self._pred.setRange(-1, 32768)
        self._pred.setSingleStep(512)
        cl.addWidget(self._pred)
        lay.addWidget(cfg)

        row2 = QHBoxLayout()
        btn_dir = QPushButton("📁 Carpeta")
        btn_dir.setStyleSheet("background:#2a2a2e;")
        btn_dir.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(ollama.MODELS_DIR)))
        btn_ref = QPushButton("↻")
        btn_ref.setStyleSheet("background:#2a2a2e;")
        btn_ref.clicked.connect(self.refresh)
        row2.addWidget(btn_dir, 1)
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
        for info in catalogo.CATALOGO:
            if filtro != "todos" and info["peso"] != filtro:
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
        row.bar.setVisible(True)
        w = PullWorker(tag)
        w.pct.connect(row.bar.setValue)
        w.done.connect(lambda c, t=tag, r=row: self._pull_done(t, r, c))
        self._pulls[tag] = w
        self._status.setText("Descargando " + tag + "…")
        w.start()

    def _pull_done(self, tag, row, code):
        self._pulls.pop(tag, None)
        if code == 0:
            row.set_installed()
            self.refresh()
        else:
            row.bar.setVisible(False)
            row.btn.setVisible(True)
            self._status.setText(f"Falló {tag} (exit {code}) — ver consola")

    # ---------- prefs por modelo ----------
    def _select_model(self, model):
        p = db.get_model_prefs(model)
        self._peso.setCurrentText(p["peso"])
        self._ctx.setValue(p["num_ctx"])
        self._pred.setValue(p["num_predict"])

    def _peso_changed(self, peso):
        pr = catalogo.PESOS[peso]
        self._ctx.setValue(pr["num_ctx"])
        self._pred.setValue(pr["num_predict"])

    def save_prefs(self, model):
        db.set_model_prefs(model, self._peso.currentText(),
                           self._ctx.value(), self._pred.value())

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
        self._list.addItems(backends.list_models("ollama")
                            or ["(Ollama desconectado o sin modelos)"])
