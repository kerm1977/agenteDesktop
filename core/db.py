"""SQLite incorporado: preferencias de modelos, escaneo de hardware, historial."""
import json
import os
import sqlite3
import time

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(APP_DIR, "agente.db")


def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init():
    with _conn() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS hw_scan(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL, datos TEXT)""")
        con.execute("""CREATE TABLE IF NOT EXISTS model_prefs(
            model TEXT PRIMARY KEY,
            peso TEXT, num_ctx INTEGER, num_predict INTEGER,
            temperature REAL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS chat_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL, role TEXT, content TEXT)""")
        con.execute("""CREATE TABLE IF NOT EXISTS model_bench(
            model TEXT PRIMARY KEY, ok INTEGER, ms INTEGER, ts REAL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS config(
            k TEXT PRIMARY KEY, v TEXT)""")
        con.execute("""CREATE TABLE IF NOT EXISTS cache_resp(
            k TEXT PRIMARY KEY, respuesta TEXT, ts REAL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS conversacion(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT, ts REAL, mensajes TEXT)""")


# ---------- configuración persistente ----------
def get_cfg(k, default=None):
    with _conn() as con:
        row = con.execute("SELECT v FROM config WHERE k=?", (k,)
                          ).fetchone()
    return row["v"] if row else default


def set_cfg(k, v):
    with _conn() as con:
        con.execute("INSERT OR REPLACE INTO config VALUES(?,?)", (k, str(v)))


# ---------- preferencias por modelo ----------
def set_model_prefs(model, peso, num_ctx, num_predict, temperature=0.7):
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO model_prefs VALUES(?,?,?,?,?)",
            (model, peso, num_ctx, num_predict, temperature))


def get_model_prefs(model):
    with _conn() as con:
        row = con.execute("SELECT * FROM model_prefs WHERE model=?",
                          (model,)).fetchone()
    if row:
        return dict(row)
    return {"peso": "medio", "num_ctx": 4096, "num_predict": -1,
            "temperature": 0.7}


# ---------- escaneo de hardware ----------
def save_hw_scan(datos):
    with _conn() as con:
        con.execute("INSERT INTO hw_scan(ts,datos) VALUES(?,?)",
                    (time.time(), json.dumps(datos, ensure_ascii=False)))


def last_hw_scan():
    with _conn() as con:
        row = con.execute("SELECT * FROM hw_scan ORDER BY id DESC LIMIT 1"
                          ).fetchone()
    return json.loads(row["datos"]) if row else None


# ---------- analizador de modelos ----------
def save_bench(model, ok, ms):
    with _conn() as con:
        con.execute("INSERT OR REPLACE INTO model_bench VALUES(?,?,?,?)",
                    (model, int(ok), ms, time.time()))


def get_bench(model):
    with _conn() as con:
        row = con.execute("SELECT ok, ms FROM model_bench WHERE model=?",
                          (model,)).fetchone()
    return (row["ok"], row["ms"]) if row else None


# ---------- historial ----------
def log_chat(role, content):
    with _conn() as con:
        con.execute("INSERT INTO chat_log(ts,role,content) VALUES(?,?,?)",
                    (time.time(), role, content[:8000]))


def chat_history():
    """Todo el historial [(role, content)] en orden."""
    with _conn() as con:
        rows = con.execute(
            "SELECT role, content FROM chat_log ORDER BY id").fetchall()
    return [(r["role"], r["content"]) for r in rows]


# ---------- registro de puertos OTA de proyectos ----------
def next_puerto(base=8700):
    """Puerto libre para el OTA local de un proyecto nuevo; lo registra."""
    try:
        usados = json.loads(get_cfg("puertos_ota", "[]"))
    except Exception:
        usados = []
    p = base
    while p in usados:
        p += 1
    usados.append(p)
    set_cfg("puertos_ota", json.dumps(usados))
    return p


def puertos_usados():
    try:
        return json.loads(get_cfg("puertos_ota", "[]"))
    except Exception:
        return []


# ---------- registro de conversaciones ----------
def save_conversacion(titulo, mensajes, cid=None):
    """Guarda o actualiza una conversación; mantiene el tope definido."""
    data = json.dumps(mensajes, ensure_ascii=False)
    with _conn() as con:
        if cid:
            con.execute(
                "UPDATE conversacion SET titulo=?,ts=?,mensajes=? "
                "WHERE id=?", (titulo, time.time(), data, cid))
        else:
            cur = con.execute(
                "INSERT INTO conversacion(titulo,ts,mensajes) "
                "VALUES(?,?,?)", (titulo, time.time(), data))
            cid = cur.lastrowid
        tope = int(get_cfg("max_conversaciones", 50))
        con.execute("DELETE FROM conversacion WHERE id NOT IN "
                    "(SELECT id FROM conversacion ORDER BY ts DESC "
                    "LIMIT ?)", (tope,))
    return cid


def list_conversaciones(query=""):
    """[(id, titulo, ts)] más recientes primero; filtra por texto."""
    with _conn() as con:
        if query:
            rows = con.execute(
                "SELECT id,titulo,ts FROM conversacion "
                "WHERE titulo LIKE ? ORDER BY ts DESC",
                ("%" + query + "%",)).fetchall()
        else:
            rows = con.execute(
                "SELECT id,titulo,ts FROM conversacion "
                "ORDER BY ts DESC").fetchall()
    return [(r["id"], r["titulo"], r["ts"]) for r in rows]


def get_conversacion(cid):
    with _conn() as con:
        row = con.execute("SELECT * FROM conversacion WHERE id=?",
                          (cid,)).fetchone()
    return (json.loads(row["mensajes"]), row["titulo"], row["ts"]) \
        if row else (None, None, None)


def del_conversacion(cid):
    with _conn() as con:
        con.execute("DELETE FROM conversacion WHERE id=?", (cid,))


# ---------- caché de respuestas frecuentes ----------
def get_cached(k):
    with _conn() as con:
        row = con.execute(
            "SELECT respuesta FROM cache_resp WHERE k=?", (k,)
            ).fetchone()
    return row["respuesta"] if row else None


def set_cached(k, respuesta, max_items=200):
    with _conn() as con:
        con.execute("INSERT OR REPLACE INTO cache_resp(k,respuesta,ts) "
                    "VALUES(?,?,?)", (k, respuesta, time.time()))
        con.execute("DELETE FROM cache_resp WHERE k NOT IN "
                    "(SELECT k FROM cache_resp ORDER BY ts DESC LIMIT ?)",
                    (max_items,))


init()
