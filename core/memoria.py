"""Memoria del proyecto: escaneo de estructura y firmas para el agente."""
import json
import os
import re
import time

SKIP = {".git", ".agente", ".update", "node_modules", ".venv", ".venv312",
        "modelos", "vendor", "exports", "dist", "build", "__pycache__"}
MAX_DEPTH = 6

_SIG_PY = re.compile(r"^\s*(def|class)\s+\w+")
_SIG_JS = re.compile(r"^\s*(function|class|const|let|var|export)\s+\w*")
_EXT_SIG = {".py": _SIG_PY, ".js": _SIG_JS, ".ts": _SIG_JS,
            ".jsx": _SIG_JS, ".tsx": _SIG_JS}

# Extensiones cuyo contenido inicial se memoriza (archivos de texto)
HEAD_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css",
             ".json", ".md", ".txt", ".yml", ".yaml", ".toml", ".ini",
             ".cfg", ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rs",
             ".php", ".rb", ".sh", ".bat", ".sql", ".vue", ".xml"}


def _head(path, cap=1200):
    """Primeras ~1200 letras del archivo si es texto y pesa <200 KB."""
    if os.path.splitext(path)[1].lower() not in HEAD_EXTS:
        return ""
    try:
        if os.path.getsize(path) > 200000:
            return ""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(cap)
    except OSError:
        return ""


def scan_project(root, max_files=400):
    """Devuelve {dirs, files:[{path,size,sig[]}], scanned_at}."""
    root = os.path.abspath(root)
    out = {"root": root, "dirs": [], "files": [], "scanned_at": time.time()}
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP and not d.startswith(".") and depth < MAX_DEPTH]
        if rel_dir != ".":
            out["dirs"].append(rel_dir.replace(os.sep, "/"))
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            rel = os.path.join(rel_dir, name) if rel_dir != "." else name
            rel = rel.replace(os.sep, "/")
            full = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(full)
            except OSError:
                size = 0
            entry = {"path": rel, "size": size, "sig": _signatures(full),
                     "head": _head(full)}
            out["files"].append(entry)
            if len(out["files"]) >= max_files:
                return out
    return out


def _signatures(path, max_sig=12):
    ext = os.path.splitext(path)[1].lower()
    rx = _EXT_SIG.get(ext)
    if not rx:
        return []
    sigs = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if rx.search(line):
                    sigs.append(line.strip()[:100])
                    if len(sigs) >= max_sig:
                        break
    except OSError:
        pass
    return sigs


def load(root, max_age=300):
    """Carga memoria cacheada en <root>/.agente/memoria.json o la regenera."""
    cache = os.path.join(root, ".agente", "memoria.json")
    try:
        if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < max_age:
            with open(cache, "r", encoding="utf-8") as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError):
        pass
    data = scan_project(root)
    try:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except OSError:
        pass
    return data


def digest(root, cap=6000):
    """Estructura + inicio de cada archivo para inyectar al prompt."""
    data = load(root)
    lines = [f"Directorios ({len(data['dirs'])}): "
             + ", ".join(data["dirs"][:60])]
    total = len(lines[0])
    n_head = 0
    for f in data["files"]:
        line = f["path"] + f" ({f['size']}B)"
        if f["sig"]:
            line += " :: " + " | ".join(f["sig"][:4])
        lines.append(line)
        total += len(line)
        head = (f.get("head") or "")[:350]
        if head and n_head < 40:
            block = "    | " + head.replace("\n", "\n    | ")
            lines.append(block)
            total += len(block)
            n_head += 1
        if total > cap:
            lines.append("... (memoria truncada: usa read_file para el resto)")
            break
    return "\n".join(lines)


def invalidate(root):
    cache = os.path.join(root, ".agente", "memoria.json")
    try:
        os.remove(cache)
    except OSError:
        pass
