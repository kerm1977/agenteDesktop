"""Aplica una actualización descargada en .update/ y relanza la app.

Se ejecuta como proceso independiente: `python -m core.updater <app.py>`.
"""
import json
import os
import shutil
import subprocess
import sys
import time

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGING = os.path.join(APP_DIR, ".update")


def apply():
    meta_file = os.path.join(STAGING, "_manifest.json")
    if not os.path.exists(meta_file):
        return False
    time.sleep(0.6)  # deja que la app salga
    for dirpath, _dirs, files in os.walk(STAGING):
        for name in files:
            src = os.path.join(dirpath, name)
            rel = os.path.relpath(src, STAGING)
            dest = os.path.join(APP_DIR, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            version = json.load(f).get("version", "0.0.0")
        with open(os.path.join(APP_DIR, "version.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"version": version}, f)
    except (OSError, json.JSONDecodeError):
        pass
    shutil.rmtree(STAGING, ignore_errors=True)
    return True


def main():
    app_py = sys.argv[1] if len(sys.argv) > 1 else os.path.join(APP_DIR, "app.py")
    apply()
    subprocess.Popen([sys.executable, app_py],
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


if __name__ == "__main__":
    main()
