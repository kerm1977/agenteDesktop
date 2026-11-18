"""Analizador de modelos: mide la latencia real de cada modelo instalado."""
import time

from core import backends

_PING = [{"role": "user", "content": "responde solo: ok"}]


def ping_model(backend, model, timeout=30):
    """Devuelve (ok, ms, detalle_error)."""
    cfg = backends.BACKENDS.get(backend, backends.BACKENDS["ollama"])
    t0 = time.monotonic()
    try:
        if cfg["tipo"] == "ollama":
            data = backends._http_json(
                cfg["url"] + "/api/chat", timeout=timeout,
                payload={"model": model, "messages": _PING,
                         "stream": False, "options": {"num_predict": 8}})
            ok = bool(data.get("message") or data.get("done"))
        else:
            data = backends._http_json(
                cfg["url"].rstrip("/") + "/chat/completions",
                timeout=timeout,
                payload={"model": model, "messages": _PING,
                         "max_tokens": 8, "stream": False})
            ok = bool(data.get("choices"))
        return ok, int((time.monotonic() - t0) * 1000), ""
    except Exception as e:
        return False, int((time.monotonic() - t0) * 1000), str(e)[:80]
