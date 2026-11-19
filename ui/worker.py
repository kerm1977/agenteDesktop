"""Hilo de chat: streaming del modelo + ejecución de herramientas."""
import json
import re
import time

from PySide6.QtCore import QThread, Signal

from core import backends, consola, memoria, tools

TOOL_RX = re.compile(r"```tool\s*\n(.*?)```", re.S)


class ScanWorker(QThread):
    """Escaneo completo del proyecto en segundo plano (memoria)."""
    done = Signal(dict, str)

    def __init__(self, root):
        super().__init__()
        self._root = root

    def run(self):
        self.done.emit(memoria.load(self._root), self._root)


class ChatWorker(QThread):
    token = Signal(str)
    card = Signal(str, str)      # título, detalle
    finished_text = Signal(str)
    failed = Signal(str)
    stat = Signal(str)
    perf = Signal(float, int)   # segundos, tokens
    open_dir = Signal(str)      # carpeta a abrir como raíz

    def __init__(self, backend, model, messages, root, options=None,
                 interpreter=None, corte=False):
        super().__init__()
        self._backend = backend
        self._model = model
        self._messages = [dict(m) for m in messages]
        self._root = root
        self._options = options or {}
        self._interpreter = interpreter
        self._corte = corte
        self._stop = False
        self._rounds_max = 8

    def request_stop(self):
        self._stop = True
        backends.abort_stream()

    def run(self):
        try:
            self._interpretar()
            self._loop()
        except Exception as e:
            consola.log_error("worker", repr(e))
            self.failed.emit(str(e))

    def _interpretar(self):
        """El modelo intérprete traduce la petición a una orden clara."""
        if not self._interpreter or self._interpreter == self._model:
            return
        ultimo = next((m for m in reversed(self._messages)
                       if m["role"] == "user"), None)
        if not ultimo or not ultimo["content"].strip():
            return
        prompt = [{"role": "system", "content":
                   "Reescribe la petición del usuario como una orden clara "
                   "y técnica en español, máximo 2 líneas. Si ya es clara, "
                   "repítela igual. NO la respondas."},
                  {"role": "user", "content": ultimo["content"]}]
        try:
            texto = "".join(
                c.get("message", {}).get("content", "")
                for c in backends.chat_stream(
                    self._backend, self._interpreter, prompt,
                    {"num_predict": 90, "num_ctx": 2048}))
            texto = texto.strip()
        except Exception as e:
            consola.log_error("interprete", repr(e))
            return
        if texto:
            # deduplica líneas repetidas y limita a 2 (evita bucles)
            lins = [l.strip() for l in texto.splitlines() if l.strip()]
            lins = list(dict.fromkeys(lins))[:2]
            texto = " ".join(lins)[:300]
        if texto:
            consola.log_info("interprete", texto[:120])
            self.card.emit("Intérprete → " + self._interpreter, texto)
            ultimo["content"] += "\n\n(Intención interpretada: " + texto + ")"

    def _loop(self):
        full_reply = ""
        ntok = 0
        t0 = time.monotonic()
        first = None
        consola.log_info("chat", f"enviando a {self._model}…")
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
                        if first is None:
                            first = time.monotonic()
                            consola.log_info(
                                "chat", f"primer token en "
                                        f"{first - t0:.1f} s")
                        buf += delta
                        ntok += 1
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
                consola.log_info("chat", "herramienta: " + call[:60])
                title, detail = self._run_call(call)
                self.card.emit(title, detail)
                results.append(f"[{title}]\n{detail}")
            if self._stop or not results:
                break
            self._messages.append({"role": "user",
                                   "content": "Resultados de herramientas:\n\n"
                                              + "\n\n".join(results)})
        dt = time.monotonic() - t0
        vel = ntok / dt if dt > 0 else 0
        self.stat.emit(
            f"⏱ {self._model} — {ntok} tokens · {dt:.1f} s"
            f" · {vel:.1f} tok/s"
            + (f" · 1.er token {first - t0:.1f} s" if first else "")
            + (" · detenida" if self._stop else ""))
        self.perf.emit(dt, ntok)
        self.finished_text.emit(self._recortar(full_reply.strip()))

    def _recortar(self, texto):
        """Si el nivel es resumida, cierra en fin de frase, no a mitad."""
        if not self._corte or "```" in texto:
            return texto
        fin = max(texto.rfind(". "), texto.rfind(".\n"),
                  texto.rfind("!"), texto.rfind("?"))
        return texto[:fin + 1] if fin > 0 else texto

    def _run_call(self, call):
        try:
            spec = json.loads(call)
            name = spec.get("name", "?")
            args = spec.get("args", {})
        except json.JSONDecodeError as e:
            return "tool inválido", f"{call[:200]} ({e})"
        try:
            title, detail = tools.run_tool(name, args, self._root)
            if detail.startswith("@OPEN:"):
                self.open_dir.emit(detail[6:])
            return title, detail
        except Exception as e:
            consola.log_error("tool:" + str(name), repr(e))
            return f"{name} (error)", str(e)
