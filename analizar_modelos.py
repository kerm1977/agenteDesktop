"""Análisis único de modelos instalados.

Mide velocidad de charla general y de código de cada modelo y guarda:
- perfil_modelos.json → lo lee el modo Automático para elegir modelo.
- perfil_modelos.md   → informe legible para el usuario.

Ejecutar una sola vez (o al instalar modelos nuevos):
    .venv\\Scripts\\python.exe analizar_modelos.py
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import backends

PROMPT_GEN = "Responde en una sola frase: ¿qué es la fotosíntesis?"
PROMPT_CODE = ("Escribe SOLO el código Python de una función "
               "`suma(a, b)` que devuelve a+b.")


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


def main():
    modelos = backends.list_models("ollama")
    print("modelos instalados:", modelos)
    res = {}
    for m in modelos:
        g_ms, g_txt = _medir(m, PROMPT_GEN)
        c_ms, c_txt = _medir(m, PROMPT_CODE)
        res[m] = {
            "general_ms": g_ms,
            "code_ms": c_ms,
            "es_coder": bool("coder" in m or "code" in m),
            "ok_gen": bool(g_ms),
            "ok_code": bool(c_txt and "def suma" in c_txt),
        }
        print(m, res[m], flush=True)
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "perfil_modelos.json"), "w",
              encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    lines = ["# Perfil de modelos instalados", "",
             "El modo (Automático) lee `perfil_modelos.json`.",
             "Regenerar: `.venv\\Scripts\\python.exe analizar_modelos.py`",
             "", "| Modelo | Tipo | Charla (ms) | Código (ms) |",
             "|---|---|---|---|"]
    for m, r in res.items():
        lines.append("| %s | %s | %s | %s |" % (
            m, "coder" if r["es_coder"] else "generalista",
            r["general_ms"], r["code_ms"]))
    with open(os.path.join(base, "perfil_modelos.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("perfil_modelos.json y perfil_modelos.md generados")


main()
