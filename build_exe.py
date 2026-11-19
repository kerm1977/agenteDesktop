"""Instalador: empaqueta Mini Agente en un .exe portable (PyInstaller).

Uso:  .venv\\Scripts\\python.exe build_exe.py
Resultado: dist\\MiniAgente\\MiniAgente.exe (carpeta completa portable).
Ollama y los modelos se instalan aparte en cada equipo.
"""
import os
import subprocess
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    py = os.path.join(APP_DIR, ".venv", "Scripts", "python.exe")
    if not os.path.exists(py):
        py = sys.executable
    subprocess.check_call([py, "-m", "pip", "install", "-q", "pyinstaller"],
                          cwd=APP_DIR)
    subprocess.check_call([
        py, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--windowed", "--name", "MiniAgente",
        "--icon", "NONE",
        "--add-data", "perfil_modelos.json;.",
        "--add-data", "ORDENES.md;.",
        "--hidden-import", "PySide6.QtSvg",
        "app.py"], cwd=APP_DIR)
    print("Listo: dist\\MiniAgente\\MiniAgente.exe")


if __name__ == "__main__":
    main()
