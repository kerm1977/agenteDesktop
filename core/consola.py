"""Bus central de errores y eventos para la consola de la app."""
import time

MAX_ENTRIES = 300
_entries = []
_listeners = []


def _emit(entry):
    for fn in list(_listeners):
        try:
            fn(entry)
        except Exception:
            pass


def log_error(origen, detalle):
    entry = {"ts": time.strftime("%H:%M:%S"), "nivel": "error",
             "origen": str(origen), "detalle": str(detalle)[:2000]}
    _entries.append(entry)
    del _entries[:-MAX_ENTRIES]
    _emit(entry)


def log_info(origen, detalle):
    entry = {"ts": time.strftime("%H:%M:%S"), "nivel": "info",
             "origen": str(origen), "detalle": str(detalle)[:2000]}
    _entries.append(entry)
    del _entries[:-MAX_ENTRIES]
    _emit(entry)


def entries():
    return list(_entries)


def clear():
    _entries.clear()


def subscribe(fn):
    """fn(entry) — se llama en el hilo que emite; la UI debe usar signals."""
    _listeners.append(fn)


def unsubscribe(fn):
    if fn in _listeners:
        _listeners.remove(fn)
