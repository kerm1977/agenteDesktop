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


init()
