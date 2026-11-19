"""Diálogo de Rendimiento: velocidad, contexto, tokens e hilos del modelo."""
import os

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog,
                               QDialogButtonBox, QFormLayout, QLabel,
                               QLineEdit, QPushButton, QSpinBox,
                               QVBoxLayout)

from core import backends, bench, db

PRESETS = {
    "Rápida":      {"num_ctx": 2048, "num_predict": 512,  "temperature": 0.4},
    "Equilibrada": {"num_ctx": 4096, "num_predict": 1024, "temperature": 0.7},
    "Avanzada":    {"num_ctx": 8192, "num_predict": 2048, "temperature": 0.8},
}


class _TestWorker(QThread):
    """Prueba de latencia: un modelo o todos los instalados."""
    step = Signal(str)
    done = Signal(list)   # [(model, ok, ms)]

    def __init__(self, models):
        super().__init__()
        self._models = models

    def run(self):
        res = []
        for m in self._models:
            self.step.emit("Midiendo " + m + "…")
            ok, ms, err = bench.ping_model("ollama", m)
            db.save_bench(m, ok, ms)
            res.append((m, ok, ms))
            self.step.emit(
                m + ": " + (f"{ms / 1000:.1f} s" if ok else f"falla: {err}"))
        self.done.emit(res)


class AjustesDialog(QDialog):
    """Ajustes de rendimiento para un modelo concreto (+ hilos globales)."""

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self._model = model
        self.setWindowTitle("Rendimiento — " + model)
        self.setMinimumWidth(360)
        prefs = db.get_model_prefs(model)

        lay = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self._preset = QComboBox()
        self._preset.addItems(list(PRESETS) + ["Personalizado"])
        self._preset.currentTextChanged.connect(self._apply_preset)
        form.addRow("Velocidad:", self._preset)

        self._ctx = QSpinBox()
        self._ctx.setRange(512, 131072)
        self._ctx.setSingleStep(1024)
        self._ctx.setValue(int(prefs["num_ctx"]))
        self._ctx.valueChanged.connect(
            lambda _v: self._preset.setCurrentText("Personalizado"))
        form.addRow("Contexto (tokens):", self._ctx)

        self._pred = QSpinBox()
        self._pred.setRange(-1, 32768)
        self._pred.setSingleStep(256)
        self._pred.setValue(int(prefs["num_predict"]))
        self._pred.setToolTip("-1 = sin límite")
        self._pred.valueChanged.connect(
            lambda _v: self._preset.setCurrentText("Personalizado"))
        form.addRow("Respuesta máx (tokens):", self._pred)

        cpu = os.cpu_count() or 4
        self._threads = QSpinBox()
        self._threads.setRange(1, cpu)
        self._threads.setValue(
            int(db.get_cfg("num_thread", max(1, cpu // 2))))
        self._threads.setToolTip(f"Tu CPU tiene {cpu} hilos disponibles")
        form.addRow(f"Hilos de CPU (1–{cpu}):", self._threads)

        self._gpu = QSpinBox()
        self._gpu.setRange(0, 200)
        self._gpu.setValue(int(db.get_cfg("num_gpu", 0)))
        self._gpu.setToolTip("Capas del modelo en VRAM (0 = solo CPU/RAM; "
                             "Ollama reparte el resto en RAM)")
        form.addRow("Capas en GPU:", self._gpu)

        self._detalle = QComboBox()
        self._detalle.addItems(["Resumida (corta)", "Media (normal)",
                                "Explicativa (con detalle)"])
        self._detalle.setToolTip(
            "Qué tan desarrolladas serán las respuestas del modelo")
        nivel = db.get_cfg("detalle:" + model, "media")
        self._detalle.setCurrentIndex(
            {"resumida": 0, "media": 1, "explicativa": 2}.get(nivel, 1))
        form.addRow("Detalle de respuesta:", self._detalle)

        form.addRow(QLabel("API keys de motores gratuitos:"))
        self._api_keys = {}
        for b, hint in (("groq", "gsk_..."), ("gemini", "AIza..."),
                        ("openrouter", "sk-or-..."),
                        ("github", "github_pat_..."),
                        ("together", "..."), ("cerebras", "csk-...")):
            w = QLineEdit(db.get_cfg("apikey:" + b) or "")
            w.setEchoMode(QLineEdit.Password)
            w.setPlaceholderText(hint)
            form.addRow(f"API key {b}:", w)
            self._api_keys[b] = w

        lay.addLayout(form)
        self._auto = QCheckBox("Auto-ajustar velocidad (reduce contexto "
                               "y respuesta si el modelo va lento)")
        self._auto.setChecked(db.get_cfg("auto_tune", "1") == "1")
        lay.addWidget(self._auto)
        self._dinamico = QCheckBox(
            "Inteligencia dinámica: elegir el mejor modelo instalado "
            "según cada pregunta (rápido para simple, coder para código)")
        self._dinamico.setChecked(db.get_cfg("dinamico", "1") == "1")
        lay.addWidget(self._dinamico)

        lay.addWidget(QLabel(
            "Más contexto/tokens = respuestas más largas pero más lentas.\n"
            "Los hilos se aplican a todos los modelos (Ollama)."))

        row = QVBoxLayout()
        self._lbl_test = QLabel("Prueba de rendimiento: sin ejecutar")
        self._lbl_test.setWordWrap(True)
        row.addWidget(self._lbl_test)
        self.btn_test = QPushButton("Probar este modelo")
        self.btn_test.clicked.connect(self._test_one)
        row.addWidget(self.btn_test)
        self.btn_all = QPushButton("Probar todos los instalados")
        self.btn_all.clicked.connect(self._test_all)
        row.addWidget(self.btn_all)
        lay.addLayout(row)

        btns = QDialogButtonBox(QDialogButtonBox.Save
                                | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)
        self._detect_preset()

    def _detect_preset(self):
        for name, p in PRESETS.items():
            if p["num_ctx"] == self._ctx.value() \
                    and p["num_predict"] == self._pred.value():
                self._preset.blockSignals(True)
                self._preset.setCurrentText(name)
                self._preset.blockSignals(False)
                return
        self._preset.blockSignals(True)
        self._preset.setCurrentText("Personalizado")
        self._preset.blockSignals(False)

    def _apply_preset(self, name):
        p = PRESETS.get(name)
        if not p:
            return
        self._ctx.blockSignals(True)
        self._pred.blockSignals(True)
        self._ctx.setValue(p["num_ctx"])
        self._pred.setValue(p["num_predict"])
        self._ctx.blockSignals(False)
        self._pred.blockSignals(False)

    # ---------- prueba de rendimiento ----------
    def _test_one(self):
        self._start_test([self._model])

    def _test_all(self):
        models = backends.list_models("ollama")
        if not models:
            self._lbl_test.setText("Sin modelos instalados.")
            return
        self._start_test(models)

    def _start_test(self, models):
        self.btn_test.setEnabled(False)
        self.btn_all.setEnabled(False)
        self._t = _TestWorker(models)
        self._t.step.connect(self._lbl_test.setText)
        self._t.done.connect(self._test_done)
        self._t.start()

    def _test_done(self, res):
        self.btn_test.setEnabled(True)
        self.btn_all.setEnabled(True)
        ok = sorted([x for x in res if x[1]], key=lambda x: x[2])
        mal = [x[0] for x in res if not x[1]]
        if len(res) == 1:
            m, okk, ms = res[0]
            self._lbl_test.setText(
                m + ": " + (f"{ms / 1000:.1f} s por respuesta"
                            if okk else f"falla: {ms}"))
            return
        lento = ok[-1] if ok else None
        texto = " · ".join(f"{m} {ms / 1000:.0f}s" for m, _, ms in ok)
        if lento:
            texto += (f"\nMás lento: {lento[0]} ({lento[2] / 1000:.1f} s) "
                      "— candidato a eliminar en equipos lentos")
        if mal:
            texto += "\nSin respuesta: " + ", ".join(mal)
        self._lbl_test.setText(texto)

    def _save(self):
        p = PRESETS.get(self._preset.currentText(),
                        {"temperature": 0.7})
        db.set_model_prefs(self._model, "custom",
                           self._ctx.value(), self._pred.value(),
                           p.get("temperature", 0.7))
        db.set_cfg("num_thread", self._threads.value())
        db.set_cfg("num_gpu", self._gpu.value())
        db.set_cfg("auto_tune", "1" if self._auto.isChecked() else "0")
        db.set_cfg("dinamico", "1" if self._dinamico.isChecked() else "0")
        db.set_cfg("detalle:" + self._model,
                   ("resumida", "media", "explicativa")[
                       self._detalle.currentIndex()])
        for b, w in self._api_keys.items():
            k = w.text().strip()
            db.set_cfg("apikey:" + b, k)
            backends.configure_backend(b, k)
        self.accept()
