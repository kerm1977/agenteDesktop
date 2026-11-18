"""Hilo de chat: streaming del modelo + ejecución de herramientas."""
import json
import re

from PySide6.QtCore import QThread, Signal

from core import backends, consola, tools

TOOL_RX = re.compile(r"```tool\s*\n(.*?)```", re.S)


class ChatWorker(QThread):
    token = Signal(str)
    card = Signal(str, str)      # título, detalle
    finished_text = Signal(str)
    failed = Signal(str)

    def __init__(self, backend, model, messages, root, options=None):
        super().__init__()
        self._backend = backend
        self._model = model
        self._messages = list(messages)
        self._root = root
        self._options = options or {}
        self._stop = False
        self._rounds_max = 8

    def request_stop(self):
        self._stop = True
        backends.abort_stream()

    def run(self):
        try:
            self._loop()
        except Exception as e:
            consola.log_error("worker", repr(e))
            self.failed.emit(str(e))

    def _loop(self):
        full_reply = ""
        for _round in range(self._rounds_max):
            if self._stop:
                break
            buf = ""
            try:
                for chunk in backends.chat_stream(
                        self._backend, self._model,
                        self._messages, self._options):
                    if self._stop:
                        break
                    delta = chunk.get("message", {}).get("content", "")
                    if delta:
                        buf += delta
                        self.token.emit(delta)
            except Exception as e:
                if self._stop:
                    break
                consola.log_error("backend", repr(e))
                if not buf:
                    raise
                break
            reply = buf.strip()
            if not reply:
                break
            calls = [(m.group(1).strip()) for m in TOOL_RX.finditer(reply)]
            visible = TOOL_RX.sub("", reply).strip()
            if visible:
                full_reply += visible + "\n"
            if not calls:
                break
            self._messages.append({"role": "assistant", "content": reply})
            results = []
            for call in calls:
                if self._stop:
                    break
                title, detail = self._run_call(call)
                self.card.emit(title, detail)
                results.append(f"[{title}]\n{detail}")
            if self._stop or not results:
                break
            self._messages.append({"role": "user",
                                   "content": "Resultados de herramientas:\n\n"
                                              + "\n\n".join(results)})
        self.finished_text.emit(full_reply.strip())

    def _run_call(self, call):
        try:
            spec = json.loads(call)
            name = spec.get("name", "?")
            args = spec.get("args", {})
        except json.JSONDecodeError as e:
            return "tool inválido", f"{call[:200]} ({e})"
        try:
            return tools.run_tool(name, args, self._root)
        except Exception as e:
            consola.log_error("tool:" + str(name), repr(e))
            return f"{name} (error)", str(e)
