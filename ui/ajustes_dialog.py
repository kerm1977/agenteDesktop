"""Diálogo de Rendimiento: velocidad, contexto, tokens e hilos del modelo."""
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox,
                               QFormLayout, QLabel, QSpinBox,
                               QVBoxLayout)

from core import db

PRESETS = {
    "Rápida":      {"num_ctx": 2048, "num_predict": 512,  "temperature": 0.4},
    "Equilibrada": {"num_ctx": 4096, "num_predict": 1024, "temperature": 0.7},
    "Avanzada":    {"num_ctx": 8192, "num_predict": 2048, "temperature": 0.8},
}


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
            int(db.get_cfg("num_thread", cpu)))
        self._threads.setToolTip(f"Tu CPU tiene {cpu} hilos disponibles")
        form.addRow(f"Hilos de CPU (1–{cpu}):", self._threads)

        lay.addLayout(form)
        lay.addWidget(QLabel(
            "Más contexto/tokens = respuestas más largas pero más lentas.\n"
            "Los hilos se aplican a todos los modelos (Ollama)."))
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

    def _save(self):
        p = PRESETS.get(self._preset.currentText(),
                        {"temperature": 0.7})
        db.set_model_prefs(self._model, "custom",
                           self._ctx.value(), self._pred.value(),
                           p.get("temperature", 0.7))
        db.set_cfg("num_thread", self._threads.value())
        self.accept()
