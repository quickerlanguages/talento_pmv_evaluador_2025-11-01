from flask import Flask, render_template, request, jsonify
import os, sqlite3, argparse, subprocess, sys

app = Flask(__name__, template_folder="templates")

# DB del backend (validada en M8)
BACKEND_DB = os.environ.get("BACKEND_DB", "./backend/talento_READY_2025-09-14.db")

# Token admin simple para acciones locales (por defecto: pmv-local)
PANEL_ADMIN_TOKEN = os.environ.get("PANEL_ADMIN_TOKEN", "pmv-local")


def db_connect():
    return sqlite3.connect(BACKEND_DB)


@app.get("/")
def panel():
    kpis = {"rows": [], "error": None}
    try:
        with db_connect() as con:
            cur = con.cursor()
            cur.execute("""
                SELECT ccp_code,
                       COUNT(*)                         AS n,
                       ROUND(AVG(correcta)*100, 1)      AS acierto_pct,
                       ROUND(AVG(tr_ms), 1)             AS tr
                  FROM tlt_respuesta
              GROUP BY ccp_code
              ORDER BY ccp_code
            """)
            rows = cur.fetchall()
            kpis["rows"] = [{"ccp": r[0], "n": r[1], "acierto_pct": r[2], "tr_ms": r[3]} for r in rows]
    except Exception as e:
        kpis["error"] = str(e)
    return render_template("panel.html", kpis=kpis)


@app.get("/health")
def health():
    ok = os.path.exists(BACKEND_DB)
    return {"status": "ok" if ok else "no-db", "db": BACKEND_DB}, (200 if ok else 503)


@app.post("/admin/ingest")
def admin_ingest():
    """
    Importa sesiones JSONL -> SQLite llamando al script del PMV.
    Protección básica con token (query ?token=... o header X-Panel-Token).
    """
    token = request.args.get("token") or request.headers.get("X-Panel-Token", "")
    if token != PANEL_ADMIN_TOKEN:
        return {"ok": False, "error": "unauthorized"}, 401

    # Ejecuta el ingestor del PMV con BACKEND_DB heredado / forzado
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = os.environ.copy()
    env["BACKEND_DB"] = os.environ.get("BACKEND_DB", os.path.join(root, "backend", "talento_READY_2025-09-14.db"))

    cmd = [sys.executable, os.path.join(root, "scripts", "ingest_jsonl_to_sqlite.py")]
    run = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True)

    # (Opcional) Afinar la DB tras ingesta
    try:
        with sqlite3.connect(env["BACKEND_DB"]) as con:
            con.execute("ANALYZE;")
            con.execute("PRAGMA optimize;")
    except Exception:
        pass  # no crítico

    return {
        "ok": (run.returncode == 0),
        "stdout": run.stdout,
        "stderr": run.stderr
    }, (200 if run.returncode == 0 else 500)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5002)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()

@app.post("/admin/purge")
def admin_purge():
    """Elimina respuestas de una sesión concreta. Uso: POST /admin/purge?token=...&sesion=101"""
    token = request.args.get("token") or request.headers.get("X-Panel-Token","")
    if token != PANEL_ADMIN_TOKEN:
        return {"ok": False, "error": "unauthorized"}, 401
    sesion = request.args.get("sesion", "").strip()
    if not sesion.isdigit():
        return {"ok": False, "error": "sesion inválida"}, 400
    with sqlite3.connect(BACKEND_DB) as con:
        cur = con.cursor()
        cur.execute("DELETE FROM tlt_respuesta WHERE sesion_id=?;", (int(sesion),))
        con.commit()
        deleted = cur.rowcount if cur.rowcount is not None else 0
    return {"ok": True, "deleted": deleted}

@app.post("/admin/reindex")
def admin_reindex():
    """Recrea índice único y optimiza DB (por si llegan datasets externos)."""
    token = request.args.get("token") or request.headers.get("X-Panel-Token","")
    if token != PANEL_ADMIN_TOKEN:
        return {"ok": False, "error": "unauthorized"}, 401
    with sqlite3.connect(BACKEND_DB) as con:
        cur = con.cursor()
        # Limpieza duplicados + índice único (igual que el ingestor)
        cur.execute("""
            DELETE FROM tlt_respuesta
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM tlt_respuesta
                GROUP BY sesion_id, ejer_code, item_id
            );
        """)
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_tlt_resp_unique
              ON tlt_respuesta (sesion_id, ejer_code, item_id);
        """)
        con.execute("ANALYZE;")
        con.execute("PRAGMA optimize;")
    return {"ok": True}