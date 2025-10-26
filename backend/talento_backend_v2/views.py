# backend/talento_backend_v2/views.py
from django.conf import settings
from django.db import connection
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils.encoding import smart_str
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

import io
import csv
import re
from datetime import datetime
from typing import Optional, Tuple

# Parser de datetimes (si viene hora en date_to, no añadimos 23:59:59)
from django.utils.dateparse import parse_datetime as dt_parse


# -----------------------------
# Utilidades de fechas y validación
# -----------------------------
DATE_FMT = "%Y-%m-%d"


def _parse_date(s: str) -> Optional[datetime]:
    try:
        return datetime.strptime(s, DATE_FMT)
    except Exception:
        return None


def parse_date_range(request) -> Tuple[Optional[str], Optional[str], Optional[JsonResponse]]:
    """
    Lee date_from/date_to del querystring.
    Devuelve (date_from_str, date_to_str, error_response).
    - Si vienen con formato inválido → 400
    - Si ambos vienen y date_from > date_to → 400
    """
    df_raw = request.GET.get("date_from")
    dt_raw = request.GET.get("date_to")

    if df_raw and not _parse_date(df_raw):
        return None, None, JsonResponse(
            {"ok": False, "error": "invalid date_from", "hint": "YYYY-MM-DD"}, status=400
        )
    if dt_raw and not _parse_date(dt_raw):
        return None, None, JsonResponse(
            {"ok": False, "error": "invalid date_to", "hint": "YYYY-MM-DD"}, status=400
        )

    if df_raw and dt_raw:
        if _parse_date(df_raw) > _parse_date(dt_raw):
            return None, None, JsonResponse(
                {"ok": False, "error": "invalid date range", "hint": "date_from <= date_to"},
                status=400,
            )

    return df_raw, dt_raw, None


def _normalize_date_to_end_of_day(val: str | None) -> str | None:
    """
    Si val viene sin hora (YYYY-MM-DD) la extiende a 'YYYY-MM-DD 23:59:59'.
    Si ya trae hora válida o es None, la devuelve tal cual.
    """
    if not val:
        return val
    try:
        # Si parsea con hora -> ya incluye hora; no tocamos
        if dt_parse(val):
            return val
    except Exception:
        pass
    return val.strip() + " 23:59:59"


def clamp_last_n(request, default: int = 10, max_n: int = 100) -> int:
    try:
        n = int(request.GET.get("last_n", default))
    except Exception:
        return default
    return max(0, min(n, max_n))


# -----------------------------
# Helpers comunes
# -----------------------------
def _slug(s: str) -> str:
    """Convierte a un fragmento seguro para filename: letras/números/._-"""
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", s or "")


def _json_bad_request(msg: str):
    return JsonResponse({"ok": False, "error": msg}, status=400)


def _json_forbidden(msg: str = "Forbidden (login or valid token required)"):
    return JsonResponse({"ok": False, "error": msg}, status=403)


def _has_panel_access(request):
    # Si hay login activo y autenticado, OK
    if getattr(request, "user", None) and request.user.is_authenticated:
        return True

    # Si hay token en settings y coincide con el header/query, OK
    token_cfg = getattr(settings, "PANEL_ORIENTADOR_TOKEN", None)
    token = request.headers.get("X-Panel-Token") or (
        request.GET.get("token") if getattr(settings, "PANEL_ALLOW_QUERYTOKEN", True) else None
    )
    if token_cfg and token == token_cfg:
        return True

    # Si no hay token configurado y está en DEBUG, dejamos abierto (entorno local)
    if not token_cfg and settings.DEBUG:
        return True

    return False


# -----------------------------
# Vistas
# -----------------------------
@require_GET
@ensure_csrf_cookie
def orientador_panel(request):
    if not _has_panel_access(request):
        return _json_forbidden()
    return render(request, "orientador.html", {})


@require_GET
def api_sessions(request):
    if not _has_panel_access(request):
        return _json_forbidden()

    # Validación y normalización de fechas
    df_raw, dt_raw, err = parse_date_range(request)
    if err:
        return err
    date_from = df_raw
    date_to = _normalize_date_to_end_of_day(dt_raw)

    where = []
    params = []
    if date_from:
        where.append("r.created_at >= %s")
        params.append(date_from)
    if date_to:
        where.append("r.created_at <= %s")
        params.append(date_to)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
        SELECT
          r.sesion_id       AS sesion_id,
          COUNT(*)          AS n_respuestas,
          MAX(r.created_at) AS fecha_ultima
        FROM tlt_respuesta r
        {where_sql}
        GROUP BY r.sesion_id
        ORDER BY MAX(r.created_at) DESC
    """
    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    sessions = [
        {"sesion_id": row[0], "n_respuestas": row[1], "fecha_ultima": row[2]}
        for row in rows
    ]
    return JsonResponse({"ok": True, "sessions": sessions})


@require_GET
def api_progress(request):
    # Seguridad: login O token
    if not _has_panel_access(request):
        return _json_forbidden()

    # sesion_id requerido
    try:
        sesion_id = int(request.GET.get("sesion_id") or request.GET.get("session_id"))
    except Exception:
        return _json_bad_request("sesion_id requerido")

    # Validación y normalización de fechas
    df_raw, dt_raw, err = parse_date_range(request)
    if err:
        return err
    date_from = df_raw
    date_to = _normalize_date_to_end_of_day(dt_raw)

    # Filtros opcionales
    ccp = request.GET.get("ccp")
    ejer = request.GET.get("ejer")

    where = ["sesion_id = %s"]
    params = [sesion_id]

    if date_from:
        where.append("created_at >= %s")
        params.append(date_from)
    if date_to:
        where.append("created_at <= %s")
        params.append(date_to)
    if ccp:
        where.append("ccp_code = %s")
        params.append(ccp)
    if ejer:
        where.append("ejer_code = %s")
        params.append(ejer)

    where_sql = "WHERE " + " AND ".join(where)

    # Aggregates by_ccp / by_ejer con los mismos filtros
    sql_by_ccp = f"""
        SELECT
          COALESCE(ccp_code, 'UNK') AS ccp_code,
          COUNT(*)                  AS n,
          AVG(CASE WHEN correcta IN (1,'1','t','true','TRUE') THEN 1.0 ELSE 0.0 END)*100.0 AS acierto_pct,
          AVG(tr_ms)                AS tr_ms_avg
        FROM tlt_respuesta
        {where_sql}
        GROUP BY COALESCE(ccp_code, 'UNK')
        ORDER BY ccp_code
    """

    sql_by_ejer = f"""
        SELECT
          COALESCE(ccp_code, 'UNK')  AS ccp_code,
          COALESCE(ejer_code, 'UNK') AS ejer_code,
          COUNT(*)                   AS n,
          AVG(CASE WHEN correcta IN (1,'1','t','true','TRUE') THEN 1.0 ELSE 0.0 END)*100.0 AS acierto_pct,
          AVG(tr_ms)                 AS tr_ms_avg
        FROM tlt_respuesta
        {where_sql}
        GROUP BY COALESCE(ccp_code, 'UNK'), COALESCE(ejer_code, 'UNK')
        ORDER BY ccp_code, ejer_code
    """

    with connection.cursor() as cur:
        cur.execute(sql_by_ccp, params)
        rows_ccp = cur.fetchall()
        cur.execute(sql_by_ejer, params)
        rows_ejer = cur.fetchall()

    by_ccp = [
        {
            "ccp_code": r[0],
            "n": r[1],
            "acierto_pct": float(r[2]) if r[2] is not None else None,
            "tr_ms_avg": float(r[3]) if r[3] is not None else None,
        }
        for r in rows_ccp
    ]
    by_ejer = [
        {
            "ccp_code": r[0],
            "ejer_code": r[1],
            "n": r[2],
            "acierto_pct": float(r[3]) if r[3] is not None else None,
            "tr_ms_avg": float(r[4]) if r[4] is not None else None,
        }
        for r in rows_ejer
    ]

    payload = {
        "sesion_id": sesion_id,
        "filters_applied": {
            "ccp": ccp,
            "ejer": ejer,
            # devolvemos lo CRUDO que envió el cliente
            "date_from": df_raw or None,
            "date_to": dt_raw or None,
        },
        "kpis": by_ccp,  # alias compat
        "by_ccp": by_ccp,
        "by_ejer": by_ejer,
    }

    # last_n opcional, respetando los filtros anteriores
    last_n = request.GET.get("last_n")
    if last_n:
        try:
            last_n_int = max(1, min(int(last_n), 500))
            sql_last = f"""
                SELECT created_at, ccp_code, ejer_code,
                       CASE WHEN correcta IN (1,'1','t','true','TRUE') THEN 1 ELSE 0 END AS correcta,
                       tr_ms
                FROM tlt_respuesta
                {where_sql}
                ORDER BY created_at DESC
                LIMIT %s
            """
            with connection.cursor() as cur:
                cur.execute(sql_last, params + [last_n_int])
                rows = cur.fetchall()
            payload["last_items"] = [
                {
                    "created_at": r[0],
                    "ccp_code": r[1],
                    "ejer_code": r[2],
                    "correcta": bool(r[3]),
                    "tr_ms": r[4],
                }
                for r in rows
            ]
        except Exception:
            payload["last_items"] = []

    return JsonResponse(payload)


@require_http_methods(["GET", "HEAD"])
def api_export_by_ccp(request, sesion_id: int):
    if not _has_panel_access(request):
        return _json_forbidden()

    # Validación y normalización de fechas
    df_raw, dt_raw, err = parse_date_range(request)
    if err:
        return err
    date_from = df_raw
    date_to = _normalize_date_to_end_of_day(dt_raw)
    ccp = request.GET.get("ccp")

    # WHERE + params
    where = ["sesion_id = %s"]
    params = [sesion_id]
    if date_from:
        where.append("created_at >= %s")
        params.append(date_from)
    if date_to:
        where.append("created_at <= %s")
        params.append(date_to)
    if ccp:
        where.append("(ccp_code = %s)")
        params.append(ccp)
    where_sql = "WHERE " + " AND ".join(where)

    # Construye filename con los valores crudos del querystring
    suffix = []
    if ccp:
        suffix.append(f"ccp-{_slug(ccp)}")
    if df_raw or dt_raw:
        df = _slug(df_raw or "")
        dt = _slug(dt_raw or "")
        suffix.append(f"{df or '…'}_{dt or '…'}")
    suffix_txt = ("_" + "_".join(suffix)) if suffix else ""
    filename = f"sesion_{smart_str(sesion_id)}_by_ccp{suffix_txt}.csv"

    # HEAD: solo cabeceras
    if request.method == "HEAD":
        resp = HttpResponse("", content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

    # GET: query + CSV
    sql = f"""
        SELECT
          COALESCE(ccp_code, 'UNK') AS ccp_code,
          COUNT(*)                  AS n,
          AVG(CASE WHEN correcta IN (1,'1','t','true','TRUE') THEN 1.0 ELSE 0.0 END)*100.0 AS acierto_pct,
          AVG(tr_ms)                AS tr_ms_avg
        FROM tlt_respuesta
        {where_sql}
        GROUP BY COALESCE(ccp_code, 'UNK')
        ORDER BY ccp_code
    """
    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["ccp_code", "n", "acierto_pct", "tr_ms_avg"])
    for ccp_code, n, acc, tr in rows:
        writer.writerow([
            "" if ccp_code is None else str(ccp_code),
            int(n) if n is not None else "",
            "" if acc is None else f"{float(acc):.1f}",
            "" if tr is None else f"{float(tr):.0f}",
        ])

    resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@require_http_methods(["GET", "HEAD"])
def api_export_by_ejer(request, sesion_id: int):
    if not _has_panel_access(request):
        return _json_forbidden()

    # Validación y normalización de fechas
    df_raw, dt_raw, err = parse_date_range(request)
    if err:
        return err
    date_from = df_raw
    date_to = _normalize_date_to_end_of_day(dt_raw)
    ccp = request.GET.get("ccp")
    ejer = request.GET.get("ejer")

    # WHERE y parámetros
    where = ["sesion_id = %s"]
    params = [sesion_id]
    if date_from:
        where.append("created_at >= %s")
        params.append(date_from)
    if date_to:
        where.append("created_at <= %s")
        params.append(date_to)
    if ccp:
        where.append("(ccp_code = %s)")
        params.append(ccp)
    if ejer:
        where.append("(ejer_code = %s)")
        params.append(ejer)

    where_sql = "WHERE " + " AND ".join(where)

    # Nombre de fichero con valores crudos
    suffix = []
    if ccp:
        suffix.append(f"ccp-{_slug(ccp)}")
    if ejer:
        suffix.append(f"ejer-{_slug(ejer)}")
    if df_raw or dt_raw:
        df = _slug(df_raw or "")
        dt = _slug(dt_raw or "")
        suffix.append(f"{df or '…'}_{dt or '…'}")
    suffix_txt = ("_" + "_".join(suffix)) if suffix else ""
    filename = f"sesion_{smart_str(sesion_id)}_by_ejer{suffix_txt}.csv"

    # HEAD: solo cabeceras
    if request.method == "HEAD":
        resp = HttpResponse("", content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

    # SQL agregado por ejercicio
    sql = f"""
        SELECT
          COALESCE(ccp_code, 'UNK')  AS ccp_code,
          COALESCE(ejer_code, 'UNK') AS ejer_code,
          COUNT(*)                   AS n,
          AVG(CASE WHEN correcta IN (1,'1','t','true','TRUE') THEN 1.0 ELSE 0.0 END)*100.0 AS acierto_pct,
          AVG(tr_ms)                 AS tr_ms_avg
        FROM tlt_respuesta
        {where_sql}
        GROUP BY COALESCE(ccp_code, 'UNK'), COALESCE(ejer_code, 'UNK')
        ORDER BY ccp_code, ejer_code
    """

    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    # Construcción CSV
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["ccp_code", "ejer_code", "n", "acierto_pct", "tr_ms_avg"])
    for ccp_code, ejer_code, n, acc, tr in rows:
        writer.writerow([
            "" if ccp_code is None else str(ccp_code),
            "" if ejer_code is None else str(ejer_code),
            int(n) if n is not None else "",
            "" if acc is None else f"{float(acc):.1f}",
            "" if tr is None else f"{float(tr):.0f}",
        ])

    resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@require_POST
def api_backfill(request):
    if not _has_panel_access(request):
        return _json_forbidden()
    # Placeholder de backfill
    return JsonResponse({"ok": True, "stats": {"inserted": 0, "before": 33, "after": 33}})


@require_GET
def health(request):
    return JsonResponse({"ok": True, "status": "healthy"})