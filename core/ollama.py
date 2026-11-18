"""Gestión local de Ollama: auto-arranque, estado y modelos."""
import os
import subprocess
import time
import urllib.request
import json

from core.backends import OLLAMA_URL, backend_status

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(APP_DIR, "modelos")
os.makedirs(MODELS_DIR, exist_ok=True)

_autostart_ts = 0.0


def _ollama_exe():
    exe = os.environ.get("OLLAMA_EXE")
    if exe and os.path.exists(exe):
        return exe
    local = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                         "Programs", "Ollama", "ollama.exe")
    if os.path.exists(local):
        return local
    return "ollama"


def ensure_running(timeout=15):
    """Levanta `ollama serve` si no responde; throttle de 30s."""
    global _autostart_ts
    if backend_status("ollama"):
        return True
    if time.time() - _autostart_ts < 30:
        return False
    _autostart_ts = time.time()
    try:
        env = dict(os.environ)
        env["OLLAMA_MODELS"] = env.get("OLLAMA_MODELS", MODELS_DIR)
        subprocess.Popen([_ollama_exe(), "serve"], env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:
        return False
    deadline = time.time() + timeout
    while time.time() < deadline:
        if backend_status("ollama"):
            return True
        time.sleep(0.8)
    return backend_status("ollama")


def version():
    try:
        with urllib.request.urlopen(OLLAMA_URL + "/api/version", timeout=4) as r:
            return json.loads(r.read().decode()).get("version", "?")
    except Exception:
        return None
