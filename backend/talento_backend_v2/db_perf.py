# backend/talento_backend_v2/db_perf.py  (o donde ya tengas _ensure_perf_indexes)
from django.db import connection

def ensure_perf_indexes():
    stmts = [
        "CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_sesion ON tlt_respuesta(sesion_id)",
        "CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_ccp ON tlt_respuesta(ccp_code)",
        "CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_ejer ON tlt_respuesta(ejer_code)",
        "CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_created ON tlt_respuesta(created_at)",
        # Muy útiles para /api/progress:
        "CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_sesion_ccp ON tlt_respuesta(sesion_id, ccp_code)",
        "CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_sesion_ejer ON tlt_respuesta(sesion_id, ejer_code)",
    ]
    with connection.cursor() as cur:
        for s in stmts:
            cur.execute(s)
