# talento_core/core_views.py

from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.db import connection
from django.views.decorators.http import require_http_methods, require_GET
from django.middleware.csrf import get_token

import json
import time
import random

from typing import Optional


# ----------------------------
# Helpers SQLite sencillos
# ----------------------------

def _table_exists(name: str) -> bool:
    """True si existe una tabla o vista con ese nombre."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM sqlite_master WHERE (type='table' OR type='view') AND name=%s",
            [name],
        )
        return cur.fetchone() is not None


def _table_columns(name: str):
    """Devuelve lista de nombres de columna de una tabla/vista sqlite."""
    try:
        with connection.cursor() as cur:
            # Nota: aquí no usamos %s por ser PRAGMA con identificador
            cur.execute(f"PRAGMA table_info({name});")
            return [row[1] for row in cur.fetchall()]
    except Exception:
        return []


def _q(sql: str, params=None):
    """
    Ejecuta SQL y devuelve lista de dicts (si hay columnas), o lista vacía.
    IMPORTANTE: Usa SIEMPRE %s como placeholder en 'sql'.
    """
    params = params or []
    with connection.cursor() as cur:
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = cur.fetchall() if cur.description else []
    return [dict(zip(cols, r)) for r in rows]

def _ensure_tlt_respuesta_table():
    with connection.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tlt_respuesta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sesion_id INTEGER NOT NULL,
                ccp_code TEXT,
                ejer_code TEXT,
                item_id TEXT,
                respuesta TEXT,
                correcta INTEGER,
                tr_ms INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

def _ensure_perf_indexes():
    with connection.cursor() as cur:
        # tlt_respuesta siempre intentamos indexarla (la creamos antes)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tlt_resp_sesion ON tlt_respuesta(sesion_id)")

        # Estos solo si existen las tablas legacy/catálogos
        if _table_exists("respuesta"):
            # Evita fallo si la tabla aún no existe
            cur.execute("CREATE INDEX IF NOT EXISTS idx_resp_sesion ON respuesta(id_sesion)")
        if _table_exists("item"):
            cur.execute("CREATE INDEX IF NOT EXISTS idx_item_id     ON item(id_item)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_item_ccp    ON item(id_ccp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_item_submod ON item(id_submod)")
# ----------------------------
# UI mínimo
# ----------------------------

def ui_progress(request):
    sesion_id = request.GET.get("sesion_id", "1")
    html = f"""
    <html><body>
    <h1>Progreso (demo)</h1>
    <p>Prueba la API agregada: <code>/api/progress?sesion_id={sesion_id}</code></p>
    <p>Export JSON: <code>/api/export/session/{sesion_id}?format=json</code></p>
    <p>Export CSV: <code>/api/export/session/{sesion_id}?format=csv</code></p>
    </body></html>
    """
    return HttpResponse(html)


def play_ui(request):
    try:
        return render(request, "play.html", {})
    except Exception:
        return HttpResponse("<h1>Play UI</h1><p>Template 'play.html' no encontrado (demo).</p>")


# ----------------------------
# Agregado de progreso
# ----------------------------

def _rows_union_for_session(sesion_id: int):
    """
    Devuelve filas normalizadas:
      ccp_code, ejer_code, correcta (0/1), tr_ms
    Une tlt_respuesta (nuevo) + respuesta join item/ref_ccp (legado).
    """
    parts = []
    params = []

    # Fuente nueva
    if _table_exists("tlt_respuesta"):
        parts.append("""
            SELECT
              COALESCE(ccp_code, 'UNK')  AS ccp_code,
              COALESCE(ejer_code,'UNK')  AS ejer_code,
              COALESCE(correcta,0)       AS correcta,
              COALESCE(tr_ms,0)          AS tr_ms
            FROM tlt_respuesta
            WHERE sesion_id = %s
        """)
        params.append(sesion_id)

    # Legado: respuesta -> item -> ref_ccp (para obtener ccp_code). ejer_code no está en el legado, lo marcamos UNK.
    if _table_exists("respuesta") and _table_exists("item") and _table_exists("ref_ccp"):
        parts.append("""
            SELECT
              COALESCE(c.codigo,'UNK')     AS ccp_code,
              'UNK'                      AS ejer_code,
              COALESCE(r.correcta,0)     AS correcta,
              COALESCE(r.rt_ms,0)        AS tr_ms
            FROM respuesta r
            JOIN item    i ON i.id_item = r.id_item
            JOIN ref_ccp c ON c.id_ccp  = i.id_ccp
            WHERE r.id_sesion = %s
        """)
        params.append(sesion_id)

    if parts:
        sql = "\nUNION ALL\n".join(parts)
        return _q(sql, params)

    # Último fallback si solo existiera 'respuesta' sin catálogos
    if _table_exists("respuesta"):
        return _q("""
            SELECT 'UNK' as ccp_code, 'UNK' as ejer_code,
                   COALESCE(correcta,0) as correcta,
                   COALESCE(rt_ms,0)    as tr_ms
            FROM respuesta
            WHERE id_sesion = %s
        """, [sesion_id])

    return []

def _aggregate(rows):
    if not rows:
        return {"kpis": [], "by_ccp": [], "by_ejer": []}

    from collections import defaultdict
    by_ccp = defaultdict(lambda: {"n": 0, "ok": 0, "tr_sum": 0})
    by_ejer = defaultdict(lambda: {"n": 0, "ok": 0, "tr_sum": 0})

    for r in rows:
        ccp = r.get("ccp_code") or "UNK"
        ejer = r.get("ejer_code") or "UNK"
        ok = 1 if (r.get("correcta") in (1, True, "1")) else 0
        tr = int(r.get("tr_ms") or 0)

        by_ccp[ccp]["n"] += 1
        by_ccp[ccp]["ok"] += ok
        by_ccp[ccp]["tr_sum"] += tr

        key_ejer = (ccp, ejer)
        by_ejer[key_ejer]["n"] += 1
        by_ejer[key_ejer]["ok"] += ok
        by_ejer[key_ejer]["tr_sum"] += tr

    def pack(n, ok, tr_sum, ccp=None, ejer=None):
        acierto_pct = round((ok * 100.0 / n), 1) if n else 0.0
        tr_ms_avg = round(tr_sum / float(n), 1) if n else 0.0
        d = {"n": n, "acierto_pct": acierto_pct, "tr_ms_avg": tr_ms_avg}
        if ccp is not None:
            d["ccp_code"] = ccp
        if ejer is not None:
            d["ejer_code"] = ejer
        return d

    by_ccp_list = [pack(v["n"], v["ok"], v["tr_sum"], ccp=k) for k, v in by_ccp.items()]
    by_ejer_list = [
        pack(v["n"], v["ok"], v["tr_sum"], ccp=k[0], ejer=k[1]) for k, v in by_ejer.items()
    ]

    return {
        "kpis": sorted(by_ccp_list, key=lambda x: x["ccp_code"]),
        "by_ccp": sorted(by_ccp_list, key=lambda x: x["ccp_code"]),
        "by_ejer": sorted(by_ejer_list, key=lambda x: (x["ccp_code"], x["ejer_code"])),
    }


@require_GET
def api_progress(request):
    try:
        sesion_id = int(str(request.GET.get("sesion_id", "1")).strip().split()[0].strip().strip("."))
    except Exception:
        return HttpResponseBadRequest("sesion_id inválido")

    rows = _rows_union_for_session(sesion_id)
    aggr = _aggregate(rows)
    payload = {"sesion_id": sesion_id, **aggr}
    if not rows:
        payload["note"] = "Sin datos. ¿Existen tlt_respuesta/v_respuesta_basic/respuesta?"
    return JsonResponse(payload, status=200)


def api_export_session(request, sesion_id: int):
    try:
        sesion_id = int(sesion_id)
    except Exception:
        return HttpResponseBadRequest("sesion_id inválido")

    fmt = (request.GET.get("format") or "json").lower().strip()

    rows = _rows_union_for_session(sesion_id)
    aggr = _aggregate(rows)
    payload = {"sesion_id": sesion_id, **aggr}
    if not rows:
        payload["note"] = "Export agregado (fallback): no hay tabla per-ítem disponible."

    if fmt == "json":
        return JsonResponse(payload, status=200)

    if fmt == "csv":
        import csv, io
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["sesion_id", "ccp_code", "ejer_code", "n", "acierto_pct", "tr_ms_avg"])
        for r in payload.get("by_ejer", []):
            w.writerow([
                sesion_id,
                r.get("ccp_code"),
                r.get("ejer_code"),
                r.get("n"),
                r.get("acierto_pct"),
                r.get("tr_ms_avg"),
            ])
        data = buf.getvalue()
        return HttpResponse(data, content_type="text/csv")

    return HttpResponseBadRequest("format debe ser json|csv")


# ----------------------------
# NEXT ITEM (demo VPM)
# ----------------------------

@csrf_exempt
def api_next_vpm_item(_request):
    item = random.choice([
        {
            "ejer_code": "VPM_TR_CIRCLE",
            "ccp_code": "VPM",
            "stim": {"type": "circle", "color": "#e33", "radius": 32},
            "kind": "reaction",
            "timeout_ms": 2000,
            "correcta": None,
        },
        (lambda:
            (lambda A, B: {
                "ejer_code": "VPM_DEC_MAYOR",
                "ccp_code": "VPM",
                "stim": {"type": "compare", "A": A, "B": B, "prompt": "¿Cuál es mayor?"},
                "kind": "decideAB",
                "timeout_ms": 2500,
                "correcta": "A" if A >= B else "B",
            })(random.randint(2, 99), random.randint(2, 99))
        )()
    ])
    payload = {
        "sesion_id": 1,
        "ejer_code": item["ejer_code"],
        "ccp_code": item["ccp_code"],
        "item_id": f"demo_{int(time.time()*1000)}",
        "stimulus": item["stim"],
        "response_schema": {"type": "boolean"},
        "timeout_ms": item["timeout_ms"],
    }
    return JsonResponse(payload)


# ----------------------------
# Ingesta de respuestas mínimas (tabla nueva)
# ----------------------------

@csrf_exempt
def api_submit_answer(request):
    """
    Registra una respuesta mínima en tlt_respuesta.
    Espera JSON: {sesion_id, ccp_code, ejer_code, item_id, respuesta, correcta, tr_ms}
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")

    # 1) Parseo del JSON
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        return HttpResponseBadRequest(f"JSON inválido: {e}")

    # 2) Extracción y defaults
    try:
        sesion_id = int(data.get("sesion_id", 1))
        ccp_code  = str(data.get("ccp_code", "VPM"))
        ejer_code = str(data["ejer_code"])
        item_id   = str(data["item_id"])
        respuesta = str(data.get("respuesta", "CLICK"))
        correcta  = int(bool(data.get("correcta", 0)))
        tr_ms     = int(data.get("tr_ms", 0))
    except KeyError as e:
        return HttpResponseBadRequest(f"Falta campo obligatorio: {e}")

    # 3) Validación de sesión si existe tlt_sesion
    if _table_exists("tlt_sesion"):
        if not _q("SELECT 1 FROM tlt_sesion WHERE id = %s", [sesion_id]):
            return JsonResponse({"ok": False, "error": f"sesion_id {sesion_id} no existe"}, status=400)

    # 4) Garantiza que exista tlt_respuesta
    with connection.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tlt_respuesta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sesion_id INTEGER NOT NULL,
                ccp_code TEXT,
                ejer_code TEXT,
                item_id TEXT,
                respuesta TEXT,
                correcta INTEGER,
                tr_ms INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 5) INSERT simple (usa lo que vino en el JSON)
        cur.execute("""
            INSERT INTO tlt_respuesta
                (sesion_id, ccp_code, ejer_code, item_id, respuesta, correcta, tr_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, [sesion_id, ccp_code, ejer_code, item_id, respuesta, correcta, tr_ms])

    return JsonResponse({"ok": True})



# Alias para compatibilidad con core_urls.py
@csrf_exempt
def api_answer(request, *args, **kwargs):
    return api_submit_answer(request, *args, **kwargs)


# ----------------------------
# Ingesta legacy (tabla 'respuesta')
# ----------------------------

@csrf_exempt
def create_respuesta(request):
    """
    Inserta en la tabla 'respuesta' (modelo viejo).
    Acepta claves flexibles: id_sesion/sesion_id, id_item/item_id, rt_ms/tr_ms.
    Duplica (best-effort) en tlt_respuesta si existe/puede crearse.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")
    try:
        p = json.loads(request.body.decode("utf-8"))
        id_sesion = int(p.get("id_sesion", p.get("sesion_id", 1)))
        id_item   = int(p.get("id_item",   p.get("item_id", 0)))
        correcta  = 1 if int(p.get("correcta", 0)) else 0
        rt_ms     = int(p.get("rt_ms", p.get("tr_ms", 0)))
    except Exception as e:
        return HttpResponseBadRequest(f"JSON inválido: {e}")

    if not _table_exists("respuesta"):
        _q(
            """
            CREATE TABLE IF NOT EXISTS respuesta (
                id_respuesta INTEGER PRIMARY KEY AUTOINCREMENT,
                id_sesion INTEGER NOT NULL,
                id_item   INTEGER NOT NULL,
                correcta  INTEGER NOT NULL,
                rt_ms     INTEGER NOT NULL
            )
            """
        )

    _q(
        """
        INSERT INTO respuesta (id_sesion, id_item, correcta, rt_ms)
        VALUES (%s, %s, %s, %s)
        """,
        [id_sesion, id_item, correcta, rt_ms],
    )

    # --- duplicar automáticamente en tlt_respuesta (siempre creando tabla si no existe) ---
    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tlt_respuesta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sesion_id INTEGER NOT NULL,
                    ccp_code TEXT,
                    ejer_code TEXT,
                    item_id TEXT,
                    respuesta TEXT,
                    correcta INTEGER,
                    tr_ms INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                """
                INSERT INTO tlt_respuesta (
        sesion_id, ccp_code, ejer_code, item_id, respuesta, correcta, tr_ms, created_at
    )
    -- caso ideal: mapeamos por catálogos
    SELECT
        %s,
        COALESCE(c.codigo,'UNK'),
        COALESCE(s.codigo,'UNK'),
        CAST(i.id_item AS TEXT),
        'LEGACY',
        %s,
        %s,
        CURRENT_TIMESTAMP
    FROM item i
    LEFT JOIN ref_ccp          c ON c.id_ccp  = i.id_ccp
    LEFT JOIN ref_submodalidad s ON s.id_submod = i.id_submod
    WHERE i.id_item = %s

    UNION ALL

    -- fallback: si no existe el item, insertamos igualmente con UNK
    SELECT
        %s, 'UNK','UNK', CAST(%s AS TEXT), 'LEGACY', %s, %s, CURRENT_TIMESTAMP
    WHERE NOT EXISTS (SELECT 1 FROM item WHERE id_item = %s)
    """,
    [id_sesion, correcta, rt_ms, id_item,
     id_sesion, id_item,  correcta, rt_ms, id_item],
            )
    except Exception:
        # tolerante a fallos de duplicación
        pass

    return JsonResponse({"ok": True, "persisted": True})


# ----------------------------
# Diagnóstico DB y CSRF
# ----------------------------

def api_debug_db(request):
    out = {}
    with connection.cursor() as cur:
        # ruta del fichero sqlite (si aplica)
        try:
            cur.execute("PRAGMA database_list;")
            out["database_list"] = cur.fetchall()
        except Exception as e:
            out["database_list_error"] = str(e)

        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            out["tables"] = [r[0] for r in cur.fetchall()]
        except Exception as e:
            out["tables_error"] = str(e)

        try:
            cur.execute("PRAGMA foreign_keys;")
            out["sqlite_foreign_keys"] = cur.fetchone()[0]
        except Exception as e:
            out["foreign_keys_error"] = str(e)

    return JsonResponse(out)


@ensure_csrf_cookie
def api_csrf(request):
    token = get_token(request)
    return JsonResponse({"csrftoken": token})


# ----------------------------
# QA Final (agregado por CCP, robusto a esquema)
# ----------------------------

@csrf_exempt
def qa_final(request):
    try:
        # 1) Elegimos la columna de etiqueta disponible en ref_ccp
        cols = set(_table_columns("ref_ccp"))
        label_candidates = [
            "code", "ccp_code", "codigo", "sigla", "abrev",
            "abreviatura", "short", "name", "nombre"
        ]
        label_col = next((c for c in label_candidates if c in cols), None)

        # 2) Armamos la SELECT con esa columna (o con id_ccp si no hay etiqueta)
        if label_col:
            select_ccp = f"c.{label_col} AS ccp_code"
            group_ccp  = f"c.{label_col}"
            order_ccp  = f"c.{label_col}"
        else:
            select_ccp = "CAST(i.id_ccp AS TEXT) AS ccp_code"
            group_ccp  = "i.id_ccp"
            order_ccp  = "i.id_ccp"

        sql = f"""
            SELECT
                {select_ccp},
                COUNT(*) AS n_items,
                SUM(CASE WHEN r.correcta=1 THEN 1 ELSE 0 END) AS aciertos,
                ROUND(AVG(r.rt_ms), 1) AS rt_avg,
                MAX(r.id_respuesta) AS ultima_respuesta
            FROM respuesta r
            JOIN item    i ON i.id_item = r.id_item
            JOIN ref_ccp c ON c.id_ccp  = i.id_ccp
            GROUP BY {group_ccp}
            ORDER BY {order_ccp}
        """
        rows = _q(sql)
        return JsonResponse({"ok": True, "qa_final": rows})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

def _backfill_legacy_to_tlt(sesion_id: int | None = None) -> dict:
    """
    Copia filas desde 'respuesta' (legacy) hacia 'tlt_respuesta',
    mapeando ccp/ejer por catálogos. Evita duplicados y respeta FK a tlt_sesion.
    Si sesion_id es None, procesa todas las sesiones existentes en tlt_sesion (si aplica).
    """
    if not _table_exists("respuesta"):
        return {"inserted": 0, "before": 0, "after": 0, "note": "No existe 'respuesta'."}

    _ensure_tlt_respuesta_table()
    _ensure_perf_indexes()

    # Contador previo para estimar insertados
    before = _q(
        f"SELECT COUNT(*) AS n FROM tlt_respuesta {'WHERE sesion_id=%s' if sesion_id is not None else ''}",
        [sesion_id] if sesion_id is not None else []
    )
    before_n = before[0]["n"] if before else 0

    # Armamos filtros dinámicos para el WHERE
    filters = []
    params = []

    if sesion_id is not None:
        filters.append("r.id_sesion = %s")
        params.append(sesion_id)

    # Si existe tlt_sesion, respetamos el FK: solo insertar sesiones válidas
    if _table_exists("tlt_sesion"):
        filters.append("EXISTS (SELECT 1 FROM tlt_sesion s WHERE s.id = r.id_sesion)")

    # Filtro anti-duplicados (mismo criterio que antes)
    nx = """
        NOT EXISTS (
          SELECT 1 FROM tlt_respuesta t
          WHERE t.sesion_id = r.id_sesion
            AND t.item_id   = CAST(r.id_item AS TEXT)
            AND t.tr_ms     = COALESCE(r.rt_ms,0)
            AND t.correcta  = COALESCE(r.correcta,0)
            AND t.respuesta = 'LEGACY'
        )
    """
    filters.append(nx)

    where_clause = ("WHERE " + " AND ".join(filters)) if filters else ""

    sql = f"""
        INSERT INTO tlt_respuesta (
          sesion_id, ccp_code, ejer_code, item_id, respuesta, correcta, tr_ms, created_at
        )
        SELECT
          r.id_sesion,
          COALESCE(c.codigo, 'UNK')        AS ccp_code,
          COALESCE(s.codigo, 'UNK')        AS ejer_code,
          CAST(r.id_item AS TEXT)          AS item_id,
          'LEGACY'                         AS respuesta,
          COALESCE(r.correcta, 0)          AS correcta,
          COALESCE(r.rt_ms, 0)             AS tr_ms,
          CURRENT_TIMESTAMP
        FROM respuesta r
        LEFT JOIN item i              ON i.id_item   = r.id_item
        LEFT JOIN ref_ccp c           ON c.id_ccp    = i.id_ccp
        LEFT JOIN ref_submodalidad s  ON s.id_submod = i.id_submod
        {where_clause}
    """

    with connection.cursor() as cur:
        cur.execute(sql, params)

    after = _q(
        f"SELECT COUNT(*) AS n FROM tlt_respuesta {'WHERE sesion_id=%s' if sesion_id is not None else ''}",
        [sesion_id] if sesion_id is not None else []
    )
    after_n = after[0]["n"] if after else 0

    # Métrica opcional: cuántas sesiones legacy no existen en tlt_sesion (si aplica)
    missing = []
    if _table_exists("tlt_sesion"):
        q_missing = """
            SELECT DISTINCT r.id_sesion AS sesion_id
            FROM respuesta r
            LEFT JOIN tlt_sesion s ON s.id = r.id_sesion
            WHERE s.id IS NULL
        """
        mp = []
        if sesion_id is not None:
            q_missing += " AND r.id_sesion = %s"
            mp.append(sesion_id)
        missing = [row["sesion_id"] for row in _q(q_missing, mp)]

    out = {"inserted": max(0, after_n - before_n), "before": before_n, "after": after_n}
    if missing:
        out["skipped_sessions_missing_in_tlt_sesion"] = missing
    return out

@csrf_exempt
@require_http_methods(["POST"])
def api_backfill_legacy_to_tlt(request):
    """
    POST /api/backfill
    Body JSON opcional: {"sesion_id": 1} -> limita a esa sesión
    Sin body o sin sesion_id -> procesa todas.
    """
    # 1) Parseo del body (tolerante a vacío / inválido)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        payload = {}

    # 2) sesion_id opcional
    sesion_id = payload.get("sesion_id", None)
    if sesion_id is not None:
        try:
            sesion_id = int(sesion_id)
        except Exception:
            return HttpResponseBadRequest("sesion_id inválido")

    # 3) Ejecuta backfill
    stats = _backfill_legacy_to_tlt(sesion_id)

    # 4) Hook de vista previa: si viene sesion_id, devolvemos agregado
    preview = None
    if sesion_id is not None:
        rows = _rows_union_for_session(sesion_id)
        aggr = _aggregate(rows)
        preview = {"sesion_id": sesion_id, **aggr}

    # 5) Respuesta
    resp = {"ok": True, "stats": stats}
    if preview is not None:
        resp["preview"] = preview
    return JsonResponse(resp, status=200)

