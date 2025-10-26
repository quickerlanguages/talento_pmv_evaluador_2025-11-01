# progress/views.py
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse, Http404
from django.views.decorators.http import require_GET
from django.db import connection
from django.utils.encoding import smart_str

# ------------- helpers -------------
def dictfetchall(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def _table_exists(name: str) -> bool:
    # funciona en SQLite y Postgres
    with connection.cursor() as c:
        try:
            c.execute("""
                SELECT 1 FROM (
                    SELECT table_name AS name FROM information_schema.tables
                    UNION ALL
                    SELECT name FROM sqlite_master WHERE type IN ('table','view')
                ) t WHERE lower(t.name)=lower(%s) LIMIT 1
            """, [name])
            return c.fetchone() is not None
        except Exception:
            return False

def _pick_source():
    # si hay vista v_respuesta_basic la usamos; si no, tabla respuesta
    if _table_exists("v_respuesta_basic"):
        return "v_respuesta_basic"
    elif _table_exists("respuesta"):
        return "respuesta"
    else:
        raise Http404("No hay tabla/vista de respuestas disponible")

# ------------- /api/progress -------------
@require_GET
def api_progress(request):
    sesion_id = request.GET.get("sesion_id")
    if not sesion_id:
        return JsonResponse({"error": "Falta sesion_id"}, status=400)

    src = _pick_source()

    # KPI global
    sql_kpi = f"""
        SELECT
            COALESCE(AVG(CASE WHEN correcta IN (1, '1', 't', 'true') THEN 100.0 ELSE 0.0 END), 0.0) AS acierto_pct,
            COALESCE(AVG(NULLIF(tr_ms,0)), NULLIF(AVG(tr_ms),0)) AS tr_ms_mean,
            COUNT(*) AS n_total
        FROM {src}
        WHERE sesion_id = %s
    """

    # Por CCP
    sql_by_ccp = f"""
        SELECT
            ccp_code,
            COUNT(*) AS n,
            COALESCE(AVG(CASE WHEN correcta IN (1, '1', 't', 'true') THEN 100.0 ELSE 0.0 END), 0.0) AS acierto_pct,
            COALESCE(AVG(NULLIF(tr_ms,0)), NULLIF(AVG(tr_ms),0)) AS tr_ms_mean
        FROM {src}
        WHERE sesion_id = %s
        GROUP BY ccp_code
        ORDER BY n DESC, ccp_code
    """

    # Últimos ítems (top 200)
    # Compatibles con SQLite/Postgres para ordenar por timestamp si existe
    order_ts = "ts" if _table_exists(src) else "rowid"
    sql_recent = f"""
        SELECT item_id, ccp_code,
               CASE WHEN correcta IN (1, '1', 't', 'true') THEN 1 ELSE 0 END AS correcta,
               tr_ms,
               COALESCE(ts, NULL) AS ts
        FROM {src}
        WHERE sesion_id = %s
        ORDER BY COALESCE(ts, '1970-01-01'::timestamp) DESC NULLS LAST, item_id DESC
        LIMIT 200
    """ if connection.vendor != "sqlite" else f"""
        SELECT item_id, ccp_code,
               CASE WHEN correcta IN (1, '1') THEN 1 ELSE 0 END AS correcta,
               tr_ms,
               ts
        FROM {src}
        WHERE sesion_id = ?
        ORDER BY COALESCE(ts, '1970-01-01') DESC, item_id DESC
        LIMIT 200
    """

    params = [sesion_id]
    with connection.cursor() as c:
        c.execute(sql_kpi, params)
        kpi = dictfetchall(c)[0]

        c.execute(sql_by_ccp, params)
        by_ccp = dictfetchall(c)

        c.execute(sql_recent, params)
        recent = dictfetchall(c)

    # Normaliza numéricos (por si vienen como Decimal)
    def fnum(x):
        try:
            return float(x) if x is not None else None
        except Exception:
            return None

    kpis = {
        "acierto_pct": fnum(kpi.get("acierto_pct")),
        "tr_ms_mean": fnum(kpi.get("tr_ms_mean")),
        "n_total": int(kpi.get("n_total") or 0),
    }
    for row in by_ccp:
        row["acierto_pct"] = fnum(row.get("acierto_pct"))
        row["tr_ms_mean"]  = fnum(row.get("tr_ms_mean"))
        row["n"] = int(row.get("n") or 0)

    return JsonResponse({
        "sesion_id": int(sesion_id),
        "kpis": kpis,
        "by_ccp": by_ccp,
        "recent_items": recent,
    }, json_dumps_params={"ensure_ascii": False})

# ------------- /api/export/session/:id -------------
@require_GET
def api_export_session(request, sesion_id: str):
    fmt = request.GET.get("format", "json").lower()
    src = _pick_source()

    # Cargamos todo lo de la sesión
    sql = f"""
        SELECT sesion_id, item_id, ccp_code,
               CASE WHEN correcta IN (1, '1', 't', 'true') THEN 1 ELSE 0 END AS correcta,
               tr_ms, ts
        FROM {src}
        WHERE sesion_id = %s
        ORDER BY COALESCE(ts, '1970-01-01'::timestamp) ASC, item_id ASC
    """ if connection.vendor != "sqlite" else f"""
        SELECT sesion_id, item_id, ccp_code,
               CASE WHEN correcta IN (1, '1') THEN 1 ELSE 0 END AS correcta,
               tr_ms, ts
        FROM {src}
        WHERE sesion_id = ?
        ORDER BY COALESCE(ts, '1970-01-01') ASC, item_id ASC
    """

    with connection.cursor() as c:
        c.execute(sql, [sesion_id])
        rows = dictfetchall(c)

    if fmt == "json":
        return JsonResponse({"sesion_id": int(sesion_id), "rows": rows},
                            json_dumps_params={"ensure_ascii": False})

    # CSV streaming
    def row_iter():
        header = ["sesion_id", "item_id", "ccp_code", "correcta", "tr_ms", "ts"]
        yield ",".join(header) + "\n"
        for r in rows:
            vals = [
                str(r.get("sesion_id") or ""),
                smart_str(r.get("item_id") or ""),
                smart_str(r.get("ccp_code") or ""),
                str(1 if (r.get("correcta") in (1, "1", True)) else 0),
                str(r.get("tr_ms") or ""),
                smart_str(r.get("ts") or ""),
            ]
            yield ",".join(v.replace(",", "␟") for v in vals) + "\n"

    resp = StreamingHttpResponse(row_iter(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="talento_session_{sesion_id}.csv"'
    return resp
