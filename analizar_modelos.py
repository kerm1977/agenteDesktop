"""Analiza a mano los modelos instalados (igual que el auto-análisis).

    .venv\\Scripts\\python.exe analizar_modelos.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import backends, perfil


modelos = backends.list_models("ollama")
print("modelos instalados:", modelos)
res = perfil.analizar(modelos)
for m, r in res.items():
    print(m, r)
print("perfil_modelos.json y perfil_modelos.md actualizados")
