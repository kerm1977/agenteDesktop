"""Motores de modelos: Ollama, LM Studio, llama.cpp y API compatible OpenAI."""
import json
import os
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
        payload = {"model": model, "messages": messages, "stream": True, "options": options}
        req = urllib.request.Request(cfg["url"] + "/api/chat",
                                     data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            for raw in r:
                raw = raw.strip()
                if raw:
                    yield json.loads(raw.decode())
        return

    opts = dict(options)
    if "num_predict" in opts:
        v = opts.pop("num_predict")
        if v is not None and int(v) >= 0:
            opts["max_tokens"] = v
    opts.pop("num_ctx", None)
    payload = {"model": model, "messages": messages, "stream": True}
    payload.update(opts)
    url = cfg["url"].rstrip("/") + "/chat/completions"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req, timeout=600) as r:
        for raw in r:
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
                           "message": {"role": "assistant", "content": content},
                           "done": ch.get("finish_reason") is not None}
