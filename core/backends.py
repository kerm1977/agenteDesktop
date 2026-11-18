"""Motores de modelos: Ollama, LM Studio, llama.cpp y API compatible OpenAI."""
import http.client
import json
import os
import socket
import urllib.parse
import urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

BACKENDS = {
    "ollama": {"nombre": "Ollama", "url": OLLAMA_URL, "tipo": "ollama"},
    "lmstudio": {"nombre": "LM Studio", "url": os.environ.get("LMSTUDIO_URL", "http://127.0.0.1:1234"), "tipo": "openai"},
    "llamacpp": {"nombre": "llama.cpp", "url": os.environ.get("LLAMACPP_URL", "http://127.0.0.1:8080"), "tipo": "openai"},
    "openai": {"nombre": "API OpenAI", "url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"), "tipo": "openai"},
}


def _http_json(url, payload=None, timeout=8):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    key = os.environ.get("OPENAI_API_KEY")
    if key and "/v1" in url:
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


_active_conn = None
_active_resp = None


def abort_stream():
    """Cierra conexión/respuesta activa para desbloquear chat_stream."""
    global _active_conn, _active_resp
    resp = _active_resp
    conn = _active_conn
    _active_resp = _active_conn = None
    if resp is not None:
        try:
            resp.close()
        except Exception:
            pass
    if conn is not None:
        try:
            if conn.sock is not None:
                conn.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


def _open_stream(cfg, path, payload):
    """Abre POST streaming y registra la conexión para abort_stream()."""
    global _active_conn, _active_resp
    u = urllib.parse.urlparse(cfg["url"])
    https = u.scheme == "https"
    cls = http.client.HTTPSConnection if https else http.client.HTTPConnection
    conn = cls(u.hostname, u.port or (443 if https else 80), timeout=600)
    _active_conn = conn
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("OPENAI_API_KEY")
    if key and cfg["tipo"] != "ollama":
        headers["Authorization"] = f"Bearer {key}"
    conn.request("POST", path, body=json.dumps(payload).encode(),
                 headers=headers)
    resp = conn.getresponse()
    _active_resp = resp
    return conn, resp


def _end_stream():
    global _active_conn, _active_resp
    _active_resp = _active_conn = None


def backend_status(backend="ollama"):
    cfg = BACKENDS.get(backend, BACKENDS["ollama"])
    try:
        if cfg["tipo"] == "ollama":
            _http_json(cfg["url"] + "/api/version", timeout=4)
        else:
            _http_json(cfg["url"].rstrip("/") + "/models", timeout=4)
        return True
    except Exception:
        return False


def list_models(backend="ollama"):
    cfg = BACKENDS.get(backend, BACKENDS["ollama"])
    try:
        if cfg["tipo"] == "ollama":
            data = _http_json(cfg["url"] + "/api/tags", timeout=10)
            return [m.get("name") for m in data.get("models", []) if m.get("name")]
        data = _http_json(cfg["url"].rstrip("/") + "/models", timeout=10)
        return [m.get("id") for m in data.get("data", []) if m.get("id")]
    except Exception:
        return []


def chat_stream(backend, model, messages, options=None):
    """Generador que rinde fragmentos NDJSON al estilo Ollama.

    Produce dicts {"message": {"role": "assistant", "content": ...}, "done": bool}.
    """
    cfg = BACKENDS.get(backend, BACKENDS["ollama"])
    options = options or {}
    if cfg["tipo"] == "ollama":
        payload = {"model": model, "messages": messages,
                   "stream": True, "options": options,
                   "keep_alive": "30m"}
        conn = None
        try:
            conn, resp = _open_stream(cfg, "/api/chat", payload)
            for raw in resp:
                raw = raw.strip()
                if raw:
                    yield json.loads(raw.decode())
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
            _end_stream()
        return

    opts = dict(options)
    if "num_predict" in opts:
        v = opts.pop("num_predict")
        if v is not None and int(v) >= 0:
            opts["max_tokens"] = v
    opts.pop("num_ctx", None)
    payload = {"model": model, "messages": messages, "stream": True}
    payload.update(opts)
    conn = None
    try:
        conn, resp = _open_stream(cfg, "/chat/completions", payload)
        for raw in resp:
            raw = raw.strip()
            if not raw or raw == b"data: [DONE]":
                continue
            if raw.startswith(b"data:"):
                raw = raw[5:].strip()
            try:
                obj = json.loads(raw.decode())
            except Exception:
                continue
            for ch in obj.get("choices", []):
                delta = ch.get("delta", {})
                content = delta.get("content")
                if content:
                    yield {"model": model, "created_at": "",
                           "message": {"role": "assistant",
                                       "content": content},
                           "done": ch.get("finish_reason") is not None}
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        _end_stream()
