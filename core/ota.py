"""Actualizador OTA: compara manifest remoto y descarga archivos nuevos."""
import hashlib
import json
import os
import urllib.request

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGING = os.path.join(APP_DIR, ".update")
VERSION_FILE = os.path.join(APP_DIR, "version.json")
MANIFEST_URL = ("https://raw.githubusercontent.com/kerm1977/agenteDesktop/"
                "main/manifest.json")
RAW_BASE = MANIFEST_URL.rsplit("/", 1)[0] + "/"

SKIP_PREFIXES = (".update/", ".git/", ".venv/", "modelos/", "__pycache__/",
                 "adjuntos/", ".agente/", "voz/")
SKIP_SUFFIXES = (".db", ".log", ".pyc")


def local_version():
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("version", "0.0.0")
    except (OSError, json.JSONDecodeError):
        return "0.0.0"


def _skipped(rel):
    return (any(rel.startswith(p) for p in SKIP_PREFIXES)
            or rel.endswith(SKIP_SUFFIXES))


def version_tuple(v):
    try:
        return tuple(int(p) for p in str(v).split("."))
    except ValueError:
        return (0,)


def hay_version_nueva(local, remota):
    return version_tuple(remota) > version_tuple(local)


def _sha(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def check_update(timeout=10):
    """Devuelve {ok, actual, remota, archivos:[paths a descargar], error}."""
    try:
        with urllib.request.urlopen(MANIFEST_URL, timeout=timeout) as r:
            manifest = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"ok": False, "sin_repo": True,
                    "error": "repositorio aún no publicado en GitHub"}
        return {"ok": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    remote_v = manifest.get("version", "?")
    pendientes = []
    for rel, sha in manifest.get("files", {}).items():
        if _skipped(rel):
            continue
        local = os.path.join(APP_DIR, rel.replace("/", os.sep))
        if not os.path.exists(local) or _sha(local) != sha:
            pendientes.append(rel)
    return {"ok": True, "actual": local_version(), "remota": remote_v,
            "archivos": pendientes, "manifest": manifest}


def download_update(manifest, progress=None):
    """Descarga los archivos del manifest a .update/. progress(i,total,rel)."""
    files = manifest.get("files", {})
    os.makedirs(STAGING, exist_ok=True)
    done, errores = 0, []
    items = [r for r in files if not _skipped(r)]
    for i, rel in enumerate(items):
        dest = os.path.join(STAGING, rel.replace("/", os.sep))
        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            urllib.request.urlretrieve(RAW_BASE + rel, dest)
            done += 1
        except Exception as e:
            errores.append(f"{rel}: {e}")
        if progress:
            progress(i + 1, len(items), rel)
    meta = {"version": manifest.get("version"), "files": manifest.get("files", {})}
    with open(os.path.join(STAGING, "_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(meta, f)
    return {"descargados": done, "errores": errores, "staging": STAGING}
