from django.conf import settings
from django.db import connection
from django.http import JsonResponse, HttpResponse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET
from django.shortcuts import render


def smoke(request):
    return JsonResponse({"ok": True, "app": "runtime", "status": "alive"})

def smoke_ui(request):
    return HttpResponse("<h1>Smoke UI OK</h1>", content_type="text/html")

def _auth_ok(request):
    expected = getattr(settings, "PANEL_ORIENTADOR_TOKEN", "mi-token-local")
    got = request.headers.get("X-Panel-Token")
    return bool(expected) and (got == expected)

def _fetch_metrics(sesion_id=None, ccp=None, since=None, until=None):
    # Agregación directa (SQLite/PG portable)
    sql = [
        "SELECT",
        "  sesion_id,",
        "  ccp_code,",
        "  COUNT(*) AS n,",
        "  SUM(CASE WHEN correcta IN (1, TRUE) THEN 1 ELSE 0 END) AS aciertos,",
        "  100.0 * SUM(CASE WHEN correcta IN (1, TRUE) THEN 1 ELSE 0 END) / COUNT(*) AS acierto_pct,",
        "  AVG(tr_ms) AS tr_ms_avg,",
        "  MIN(created_at) AS first_ts,",
        "  MAX(created_at) AS last_ts",
        "FROM tlt_respuesta",
        "WHERE 1=1",
    ]
    params = []
    if sesion_id:
        sql.append("AND sesion_id = %s")
        params.append(sesion_id)
    if ccp:
        sql.append("AND ccp_code = %s")
        params.append(ccp)
    if since:
        sql.append("AND date(created_at) >= %s")
        params.append(str(since))
    if until:
        sql.append("AND date(created_at) < %s")
        params.append(str(until))
    sql.append("GROUP BY sesion_id, ccp_code")
    sql.append("ORDER BY sesion_id, ccp_code")
    sql_str = " ".join(sql)

    with connection.cursor() as cur:
        cur.execute(sql_str, params)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    # Normaliza tipos/decimales
    for r in rows:
        r["n"] = int(r["n"] or 0)
        r["aciertos"] = int(r["aciertos"] or 0)
        r["acierto_pct"] = float(r["acierto_pct"] or 0.0)
        r["tr_ms_avg"] = float(r["tr_ms_avg"]) if r["tr_ms_avg"] is not None else None
    return rows

def _group_by_session(rows):
    by_session = {}
    for r in rows:
        sid = r["sesion_id"]
        by_session.setdefault(sid, {"sesion_id": sid, "ccp": []})
        by_session[sid]["ccp"].append({
            "ccp_code": r["ccp_code"],
            "n": r["n"],
            "aciertos": r["aciertos"],
            "acierto_pct": round(r["acierto_pct"], 1),
            "tr_ms_avg": round(r["tr_ms_avg"], 1) if r["tr_ms_avg"] is not None else None,
            "first_ts": r["first_ts"],
            "last_ts": r["last_ts"],
        })
    for s in by_session.values():
        n = sum(x["n"] for x in s["ccp"])
        ac = sum(x["aciertos"] for x in s["ccp"])
        s["totals"] = {
            "n": n,
            "aciertos": ac,
            "acierto_pct": round(100.0 * ac / n, 1) if n else 0.0,
            "tr_ms_avg": round(sum((x["tr_ms_avg"] or 0.0) * x["n"] for x in s["ccp"]) / n, 1) if n else 0.0,
        }
    return sorted(by_session.values(), key=lambda x: x["sesion_id"])

@require_GET
def panel_metrics(request):
    if not _auth_ok(request):
        return JsonResponse({"error": "unauthorized"}, status=401)

    sesion_id = request.GET.get("sesion_id") or None
    ccp = request.GET.get("ccp") or None
    since = parse_date(request.GET.get("since") or "")  # YYYY-MM-DD
    until = parse_date(request.GET.get("until") or "")
    fmt = (request.GET.get("format") or "json").lower()

    rows = _fetch_metrics(sesion_id, ccp, since, until)
    grouped = _group_by_session(rows)

    if fmt == "csv":
        import io, csv
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["sesion_id","ccp_code","n","aciertos","acierto_pct","tr_ms_avg","first_ts","last_ts"])
        for g in grouped:
            for x in g["ccp"]:
                w.writerow([g["sesion_id"], x["ccp_code"], x["n"], x["aciertos"],
                            x["acierto_pct"], x["tr_ms_avg"], x["first_ts"], x["last_ts"]])
        resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="panel_metrics.csv"'
        return resp

    return JsonResponse({"sessions": grouped}, json_dumps_params={"ensure_ascii": False})

def panel_page(request):
    # Solo renderiza el HTML. Los datos se cargan vía fetch() desde /panel/metrics.
    return render(request, "panel.html", {})