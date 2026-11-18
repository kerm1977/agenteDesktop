"""Dictado por micrófono: multimotor Vosk (offline) + Google (online).

Emite `level` (amplitud 0..1) para la barra de onda, `text` (frases en
vivo, solo Vosk) y `final` (transcripción completa al detener).
"""
import json
import os

from PySide6.QtCore import QThread, Signal

from core import consola

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOSK_DIR = os.path.join(APP_DIR, "voz")
_RATE = 16000
_CHUNK = 2000


def modelos_vosk():
    """Modelos Vosk instalados en <app>/voz/vosk-model-*."""
    try:
        return [os.path.join(VOSK_DIR, d) for d in os.listdir(VOSK_DIR)
                if d.startswith("vosk-model")
                and os.path.isdir(os.path.join(VOSK_DIR, d))]
    except OSError:
        return []


def _rms(data):
    """Amplitud RMS 0..1 de un chunk PCM int16 (sin audioop)."""
    import array
    s = array.array("h", data)
    if not s:
        return 0.0
    return min(1.0, (sum(x * x for x in s) / len(s)) ** 0.5 / 8192)


class VoiceWorker(QThread):
    text = Signal(str)    # dictado en vivo (vosk)
    final = Signal(str)   # texto completo al detener
    level = Signal(float)
    error = Signal(str)

    def __init__(self, engine="vosk"):
        super().__init__()
        self._stop = False
        self.engine = engine

    def stop(self):
        self._stop = True

    def run(self):
        try:
            import pyaudio
        except ImportError:
            self.error.emit("Falta pyaudio (pip install pyaudio)")
            return
        pa = pyaudio.PyAudio()
        stream = None
        try:
            stream = pa.open(format=pyaudio.paInt16, channels=1,
                             rate=_RATE, input=True,
                             frames_per_buffer=_CHUNK)
            stream.start_stream()
            if self.engine == "vosk":
                self._run_vosk(stream)
            else:
                self._run_google(stream)
        except Exception as e:
            consola.log_error("voz", repr(e))
            self.error.emit("Voz: " + str(e))
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            pa.terminate()

    def _leer(self, stream):
        try:
            data = stream.read(_CHUNK, exception_on_overflow=False)
        except OSError:
            return b""
        self.level.emit(_rms(data))
        return data

    def _run_vosk(self, stream):
        try:
            from vosk import KaldiRecognizer, Model
        except ImportError as e:
            self.error.emit("Falta " + e.name +
                            " (pip install vosk pyaudio)")
            return
        modelos = modelos_vosk()
        if not modelos:
            self.error.emit("Sin modelo Vosk en voz/ — cambia a Google")
            return
        rec = KaldiRecognizer(Model(modelos[0]), _RATE)
        while not self._stop:
            data = self._leer(stream)
            if data and rec.AcceptWaveform(data):
                t = json.loads(rec.Result()).get("text", "").strip()
                if t:
                    self.text.emit(t)
        t = json.loads(rec.FinalResult()).get("text", "").strip()
        if t:
            self.final.emit(t)

    def _run_google(self, stream):
        try:
            import speech_recognition as sr
        except ImportError:
            self.error.emit("Falta SpeechRecognition")
            return
        partes = []
        while not self._stop:
            data = self._leer(stream)
            if data:
                partes.append(data)
        if not partes:
            return
        try:
            audio = sr.AudioData(b"".join(partes), _RATE, 2)
            texto = sr.Recognizer().recognize_google(audio,
                                                     language="es-ES")
            if texto:
                self.final.emit(texto)
        except sr.UnknownValueError:
            pass
        except Exception as e:
            consola.log_error("voz", repr(e))
            self.error.emit("Reconocimiento: " + str(e))
