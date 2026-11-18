"""Genera manifest.json para el sistema OTA. Uso: gen_manifest.py [version]."""
import hashlib
import json
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {".git", ".venv", "modelos", ".update", ".agente",
             "__pycache__", "dist", "build", "adjuntos"}
SKIP_FILES = {"manifest.json", "gen_manifest.py", "_smoke.py"}
SKIP_EXT = (".pyc", ".log", ".db")


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else None
    files = {}
    for dirpath, dirnames, filenames in os.walk(APP_DIR):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name in SKIP_FILES or name.endswith(SKIP_EXT):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, APP_DIR).replace(os.sep, "/")
            h = hashlib.sha256()
            with open(full, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            files[rel] = h.hexdigest()
    if version:
        with open(os.path.join(APP_DIR, "version.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"version": version}, f)
    else:
        try:
            with open(os.path.join(APP_DIR, "version.json"),
                      encoding="utf-8") as f:
                version = json.load(f).get("version", "0.0.0")
        except (OSError, json.JSONDecodeError):
            version = "0.0.0"
    manifest = {"version": version, "files": files}
    with open(os.path.join(APP_DIR, "manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    print(f"manifest.json generado: version {version}, {len(files)} archivos")


if __name__ == "__main__":
    main()
