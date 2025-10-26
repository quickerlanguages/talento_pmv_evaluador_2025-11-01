#!/usr/bin/env python3
# Talento · PMV Evaluador — JSONL → SQLite
# v1.1-idempotent (UPSERT + dedupe + índice único)
import os, sys, json, glob, sqlite3, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESS_DIR = os.path.join(ROOT, "data", "sessions")
DB_PATH  = os.environ.get("BACKEND_DB", os.path.join(ROOT, "backend", "talento_READY_2025-09-14.db"))

# Defaults por si el JSON no trae ccp/ejer
DEF_CCP  = "VPM"
DEF_EJER = "VPM_CFANT_S"

def iter_records():
    for path in sorted(glob.glob(os.path.join(SESS_DIR, "session_*.jsonl"))):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)

def ensure_unique_index(cur):
    # Limpia duplicados antiguos y crea índice único (sesion_id, ejer_code, item_id)
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

def upsert_answer(cur, sesion_id, ccp, ejer, item, correcta, tr_ms, created_at):
    # Idempotente: inserta o actualiza el trío único (sesion_id, ejer_code, item_id)
    cur.execute("""
        INSERT OR REPLACE INTO tlt_respuesta
            (sesion_id, ccp_code, ejer_code, item_id, correcta, tr_ms, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (sesion_id, ccp, ejer, item, correcta, tr_ms, created_at))

def main():
    if not os.path.exists(DB_PATH):
        sys.exit(f"ERROR: no se encuentra DB: {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    ensure_unique_index(cur)

    processed = 0
    before = con.total_changes

    for rec in iter_records():
        sesion_id = int(rec.get("sesion_id") or 0)
        ts = float(rec.get("ts") or time.time())
        created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        for a in rec.get("answers", []):
            ccp  = a.get("ccp_code", DEF_CCP)
            ejer = a.get("ejer_code", DEF_EJER)
            item = a.get("item_id", "demo_item_001")
            correcta = int(a.get("correcta", 0))
            tr_ms = int(a.get("tr_ms", 0))
            upsert_answer(cur, sesion_id, ccp, ejer, item, correcta, tr_ms, created_at)
            processed += 1

    con.commit()
    after = con.total_changes
    delta = after - before  # inserciones + reemplazos aplicados
    con.close()

    print(f"→ Procesadas {processed} respuestas; cambios aplicados: {delta}; DB: {DB_PATH}")

if __name__ == "__main__":
    main()