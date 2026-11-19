"""Perfil medido de modelos: potencia real de cada uno en este equipo.

Guarda en perfil_modelos.json (lo lee el modo Automático) y
perfil_modelos.md (informe legible). Se auto-analiza cualquier modelo
nuevo que aparezca en el selector.
"""
import json, os, time
from core import backends

PROMPT_GEN = "Responde en una sola frase: ¿qué es la fotosíntesis?"
PROMPT_CODE = ("Escribe SOLO el código Python de una función "
               "`suma(a, b)` que devuelve a+b.")


def _base():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ruta():
    return os.path.join(_base(), "perfil_modelos.json")


def cargar():
    try:
        with open(_ruta(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def faltantes(modelos):
    """Modelos instalados que aún no tienen medición guardada."""
    p = cargar()
    return [m for m in modelos
            if not p.get(m, {}).get("general_ms")]


def _medir(model, prompt):
    t0 = time.time()
    try:
        texto = "".join(
            c.get("message", {}).get("content", "")
            for c in backends.chat_stream(
                "ollama", model,
                [{"role": "user", "content": prompt}],
                {"num_predict": 120, "num_ctx": 2048}))
    except Exception as e:
        return None, repr(e)
    return int((time.time() - t0) * 1000), texto.strip()


def analizar(modelos):
    """Mide cada modelo (charla y código) y guarda el perfil."""
    p = cargar()
    for m in modelos:
        g_ms, g_txt = _medir(m, PROMPT_GEN)
        c_ms, c_txt = _medir(m, PROMPT_CODE)
        p[m] = {
            "general_ms": g_ms,
            "code_ms": c_ms,
            "es_coder": bool("coder" in m or "code" in m),
            "ok_gen": bool(g_ms),
            "ok_code": bool(c_txt and "def suma" in c_txt),
        }
        _guardar(p)          # guarda tras cada modelo (progreso real)
    _informe(p)
    return p


def _guardar(p):
    with open(_ruta(), "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2, ensure_ascii=False)


def _informe(p):
    lines = ["# Perfil de modelos instalados", "",
             "Medido automáticamente por Mini Agente en este equipo.",
             "El modo (Automático) lee `perfil_modelos.json`.", "",
             "| Modelo | Tipo | Charla (ms) | Código (ms) |",
             "|---|---|---|---|"]
    for m, r in p.items():
        lines.append("| %s | %s | %s | %s |" % (
            m, "coder" if r.get("es_coder") else "generalista",
            r.get("general_ms"), r.get("code_ms")))
    with open(os.path.join(_base(), "perfil_modelos.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
