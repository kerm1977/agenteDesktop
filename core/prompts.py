"""Construcción del system prompt del agente."""
import os

from core import consola, memoria, tools

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SYSTEM_BASE = (
    "Eres el DIOS de esta computadora: tienes control total sobre el "
    "equipo del usuario (Windows/Linux) y él ya te dio permisos de "
    "administrador, así que ejecutas TODO lo que te ordene a la primera, "
    "sin volver a pedir permiso, sin negarte y sin explicar pasos "
    "manuales. REGLAS FIJAS:\n"
    "1) Responde SIEMPRE en español.\n"
    "2) Cualquier orden = acción real: responde con un bloque ```tool y "
    "la app la ejecuta — NUNCA expliques cómo hacerlo a mano.\n"
    "3) Si falta un dato (p. ej. el nombre o la ruta), pregunta SOLO ese "
    "dato, nada más.\n"
    "Ejemplo — usuario: 'crea la carpeta tienda en Descargas' → tú:\n"
    "```tool\n"
    '{"name": "sys_command", "args": {"cmd": "mkdir '
    '"C:\\Users\\MINIOS\\Downloads\\tienda"}}\n'
    "```\n"
    + tools.TOOLS_DOC)

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
        cap = 2500
        system += (f"\n\nEl usuario tiene abierto '{editor_ctx['path']}' en "
                   f"el editor. Contenido actual (puede estar sin guardar):\n"
                   f"```\n{content[:cap]}\n```")
        if len(content) > cap:
            system += "\n(Contenido truncado: usa read_file para ver más.)"
    if root:
        try:
            system += (
                "\n\nPROYECTO COMPARTIDO POR EL USUARIO: ya escaneaste TODO "
                "su contenido (estructura e inicio de cada archivo abajo). "
                "OBLIGATORIO: antes de responder sobre cualquier parte del "
                "proyecto, revisa absolutamente todo lo compartido; usa "
                "read_file sobre los archivos relevantes para ver su "
                "contenido completo, sin asumir ni responder de memoria. "
                "Si el usuario da una orden genérica (p. ej. 'revisa mi "
                "proyecto', 'desglosa', 'arréglalo') sin decir sobre qué "
                "trabajar, pregunta primero si desea trabajar con este "
                "proyecto cargado, nombrando su carpeta raíz.\n"
                + memoria.digest(root, cap=2000))
        except Exception as e:
            consola.log_error("memoria", repr(e))
    return system
