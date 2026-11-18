"""Herramientas del agente sobre el proyecto abierto."""
import os
import subprocess

from core import db, memoria

MAX_READ = 20000
_DENY = ("format ", "del /s", "rd /s", "rmdir /s", "shutdown", "reg ",
         "mkfs", "dd if", "> /dev/", "rm -rf /", "rm -fr /")
_SYS_DENY = _DENY + ("bcdedit", "diskpart", "fdisk", "net user",
                     "del c:\\", "rd c:\\", "takeown", "cipher /w")


def _safe(root, path):
    full = os.path.abspath(os.path.join(root, path))
    if not full.startswith(os.path.abspath(root)):
        raise ValueError(f"ruta fuera del proyecto: {path}")
    return full


def run_tool(name, args, root):
    """Ejecuta una herramienta y devuelve (titulo, detalle) para la tarjeta."""
    args = args or {}
    if name == "list_dir":
        path = _safe(root, args.get("path", "."))
        items = sorted(os.listdir(path))
        return "list_dir " + args.get("path", "."), "\n".join(items) or "(vacío)"
    if name == "read_file":
        path = _safe(root, args["path"])
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read(MAX_READ)
        note = "\n...[truncado]" if os.path.getsize(path) > MAX_READ else ""
        return "read_file " + args["path"], text + note
    if name == "write_file":
        path = _safe(root, args["path"])
        os.makedirs(os.path.dirname(path) or root, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(args.get("content", ""))
        memoria.invalidate(root)
        return "write_file " + args["path"], f"escritos {len(args.get('content', ''))} caracteres"
    if name == "edit_file":
        path = _safe(root, args["path"])
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        old, new = args["old"], args["new"]
        if old not in text:
            raise ValueError("texto 'old' no encontrado en " + args["path"])
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace(old, new, 1))
        memoria.invalidate(root)
        return "edit_file " + args["path"], f"{len(old)} -> {len(new)} caracteres"
    if name == "append_file":
        path = _safe(root, args["path"])
        with open(path, "a", encoding="utf-8") as f:
            f.write(args.get("content", ""))
        memoria.invalidate(root)
        return "append_file " + args["path"], f"+{len(args.get('content', ''))} caracteres"
    if name == "create_dir":
        p = args["path"]
        if os.path.isabs(p):
            if db.get_cfg("perm_admin") != "1":
                raise ValueError(
                    "ruta absoluta sin permiso de administrador "
                    "(actívalo una vez en la app)")
            path = p
        else:
            path = _safe(root, p)
        os.makedirs(path, exist_ok=True)
        memoria.invalidate(root)
        return "create_dir " + p, "creada: " + path
    if name == "open_dir":
        p = args["path"]
        full = p if os.path.isabs(p) else _safe(root, p)
        if not os.path.isdir(full):
            raise ValueError("no existe la carpeta: " + p)
        return "open_dir " + p, "@OPEN:" + full
    if name == "search_files":
        needle = args.get("text", "")
        hits = []
        data = memoria.load(root)
        for f in data["files"]:
            full = _safe(root, f["path"])
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as fh:
                    for i, line in enumerate(fh, 1):
                        if needle in line:
                            hits.append(f"{f['path']}:{i}: {line.strip()[:120]}")
                            if len(hits) >= 50:
                                break
            except OSError:
                continue
            if len(hits) >= 50:
                break
        return "search_files " + needle, "\n".join(hits) or "sin coincidencias"
    if name == "project_map":
        return "project_map", memoria.digest(root, cap=6000)
    if name == "sys_command":
        cmd = args.get("cmd", "")
        low = cmd.lower()
        if any(b in low for b in _SYS_DENY):
            raise ValueError("comando de sistema bloqueado por seguridad")
        cwd = args.get("cwd") or os.path.expanduser("~")
        out = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True,
                             text=True, timeout=120, errors="replace")
        text = (out.stdout + out.stderr).strip()[:4000]
        return "sys_command " + cmd, f"exit {out.returncode}\n{text}"
    if name == "run_command":
        cmd = args.get("cmd", "")
        low = cmd.lower()
        if any(b in low for b in _DENY):
            raise ValueError("comando bloqueado por seguridad")
        out = subprocess.run(cmd, shell=True, cwd=root, capture_output=True,
                             text=True, timeout=60, errors="replace")
        text = (out.stdout + out.stderr).strip()[:4000]
        return "run_command " + cmd, f"exit {out.returncode}\n{text}"
    raise ValueError(f"herramienta desconocida: {name}")


TOOLS_DOC = """Tienes herramientas para actuar sobre el proyecto. Úsalas en bloques:

```tool
{"name": "NOMBRE", "args": {"...": "..."}}
```

Herramientas: list_dir{path}, read_file{path}, write_file{path,content},
edit_file{path,old,new}, append_file{path,content}, create_dir{path},
search_files{text}, project_map{}, open_dir{path} (abre una carpeta como
raíz del editor/árbol), run_command{cmd} (dentro del proyecto),
sys_command{cmd,cwd} (cualquier comando del sistema operativo: crear
carpetas fuera del proyecto, abrir programas, instalar/desinstalar,
gestionar archivos del equipo; funciona en Windows y Linux).
OJO: el contenido del bloque tool debe ser JSON válido:
{"name": "sys_command", "args": {"cmd": "mkdir ruta"}} — nunca
`sys_command{cmd=...}`.

ERES UN AGENTE REAL del sistema operativo: si el usuario pide crear una
carpeta, abrir algo, instalar/desinstalar un programa o cualquier acción
en su equipo, usa sys_command — nunca respondas que no puedes hacerlo.
Al crear/abrir un directorio de trabajo nuevo, usa open_dir para que la
app lo muestre como raíz en el árbol y el editor.

Modo de trabajo inteligente:
- Si no conoces la estructura, PRIMERO usa project_map; no leas todo el proyecto.
- Lee solo los archivos relevantes, puedes emitir varias herramientas en un bloque.
- Si una petición es ambigua (varios archivos o componentes posibles), PREGUNTA antes de tocar nada.
- Puedes editar varios archivos en la misma respuesta.
- Después de ejecutar herramientas recibirás los resultados y continúas la tarea.
"""
