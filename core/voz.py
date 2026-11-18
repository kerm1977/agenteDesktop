"""Dictado por micrófono: escucha continua en español (SpeechRecognition)."""
from PySide6.QtCore import QThread, Signal

from core import consola


class VoiceWorker(QThread):
    """Escucha el micrófono y emite cada frase reconocida."""
    text = Signal(str)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
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
