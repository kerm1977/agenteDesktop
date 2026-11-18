"""Dictado por micrófono: multimotor Vosk (offline) + Google (online)."""
import json
import os

from PySide6.QtCore import QThread, Signal

from core import consola

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOSK_DIR = os.path.join(APP_DIR, "voz")


def modelos_vosk():
    """Modelos Vosk instalados en <app>/voz/vosk-model-*."""
    try:
        return [os.path.join(VOSK_DIR, d) for d in os.listdir(VOSK_DIR)
                if d.startswith("vosk-model")
                and os.path.isdir(os.path.join(VOSK_DIR, d))]
    except OSError:
        return []


class VoiceWorker(QThread):
    """Escucha el micrófono y emite cada frase reconocida."""
    text = Signal(str)
    error = Signal(str)

    def __init__(self, engine="vosk"):
        super().__init__()
        self._stop = False
        self.engine = engine

    def stop(self):
        self._stop = True

    def run(self):
        try:
            if self.engine == "vosk":
                self._run_vosk()
            else:
                self._run_google()
        except Exception as e:
            consola.log_error("voz", repr(e))
            self.error.emit("Voz: " + str(e))

    # ---------- Vosk (offline) ----------
    def _run_vosk(self):
        try:
            import pyaudio
            from vosk import KaldiRecognizer, Model
        except ImportError as e:
            self.error.emit("Falta " + e.name +
                            " (pip install vosk pyaudio)")
            return
        modelos = modelos_vosk()
        if not modelos:
            self.error.emit("Sin modelo Vosk en voz/ — cambia a Google "
                            "o instala uno en la carpeta voz/")
            return
        rec = KaldiRecognizer(Model(modelos[0]), 16000)
        pa = pyaudio.PyAudio()
        try:
            stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000,
                             input=True, frames_per_buffer=8000)
            stream.start_stream()
            while not self._stop:
                try:
                    data = stream.read(4000, exception_on_overflow=False)
                except OSError:
                    continue
                if rec.AcceptWaveform(data):
                    texto = json.loads(rec.Result()).get("text", "").strip()
                    if texto:
                        self.text.emit(texto)
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
            pa.terminate()

    # ---------- Google (online) ----------
    def _run_google(self):
        try:
            import speech_recognition as sr
        except ImportError:
            self.error.emit("Falta SpeechRecognition "
                            "(pip install SpeechRecognition pyaudio)")
            return
        r = sr.Recognizer()
        r.energy_threshold = 300
        try:
            mic = sr.Microphone()
        except Exception as e:
            self.error.emit("Sin micrófono: " + str(e))
            return
        with mic as src:
            try:
                r.adjust_for_ambient_noise(src, duration=0.6)
            except Exception as e:
                self.error.emit("No pude abrir el micrófono: " + str(e))
                return
            while not self._stop:
                try:
                    audio = r.listen(src, timeout=1,
                                     phrase_time_limit=10)
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    self.error.emit("Micrófono: " + str(e))
                    return
                if self._stop:
                    return
                try:
                    texto = r.recognize_google(audio, language="es-ES")
                    if texto:
                        self.text.emit(texto)
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    consola.log_error("voz", repr(e))
                    self.error.emit("Reconocimiento: " + str(e))
                    return
