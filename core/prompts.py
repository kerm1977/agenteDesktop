"""Construcción del system prompt del agente."""
import os

from core import consola, memoria, tools

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SYSTEM_BASE = ("Eres un agente de código local. Respondes en español, breve y "
               "preciso. " + tools.TOOLS_DOC)

SYSTEM_SELF = ("\n\nMODO MEJORAR AGENTE: trabajas ÚNICAMENTE sobre el código "
               "de la propia aplicación en " + APP_DIR + ". Respeta REGLAS.md "
               "(archivos <250 líneas, sin CDNs). No toques proyectos del "
               "usuario.")


def build_system(editor_ctx, root, self_mode=False):
    system = SYSTEM_BASE
    if self_mode:
        system += SYSTEM_SELF
    if editor_ctx and not self_mode:
        content = editor_ctx["content"]
        cap = 6000
        system += (f"\n\nEl usuario tiene abierto '{editor_ctx['path']}' en "
                   f"el editor. Contenido actual (puede estar sin guardar):\n"
                   f"```\n{content[:cap]}\n```")
        if len(content) > cap:
            system += "\n(Contenido truncado: usa read_file para ver más.)"
    if root:
        try:
            system += ("\n\nMemoria del proyecto (estructura y firmas):\n"
                       + memoria.digest(root, cap=4000))
        except Exception as e:
            consola.log_error("memoria", repr(e))
    return system
