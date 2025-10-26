import json
import datetime as dt
from django.urls import reverse
from django.test import override_settings
from runtime.models import TltRespuesta

@override_settings(PANEL_ORIENTADOR_TOKEN="mi-token-local")
def test_panel_metrics_json(client, db):
    t0 = dt.datetime(2025, 10, 15, 18, 0, 0)
    rows = [
        TltRespuesta(sesion_id=1, ccp_code="MCP", correcta=1, tr_ms=500, created_at=t0),
        TltRespuesta(sesion_id=1, ccp_code="MCP", correcta=0, tr_ms=700, created_at=t0),
        TltRespuesta(sesion_id=1, ccp_code="VPM", correcta=1, tr_ms=400, created_at=t0),
    ]
    TltRespuesta.objects.bulk_create(rows)
    url = reverse("panel-metrics")
    r = client.get(url, HTTP_X_PANEL_TOKEN="mi-token-local")
    assert r.status_code == 200
    data = json.loads(r.content)
    ses1 = next(s for s in data["sessions"] if s["sesion_id"] == 1)
    mcp = next(c for c in ses1["ccp"] if c["ccp_code"] == "MCP")
    assert mcp["n"] == 2 and mcp["aciertos"] == 1 and mcp["acierto_pct"] == 50.0
    assert round(ses1["totals"]["acierto_pct"], 1) == 66.7

@override_settings(PANEL_ORIENTADOR_TOKEN="mi-token-local")
def test_panel_metrics_csv(client, db):
    TltRespuesta.objects.create(sesion_id=3, ccp_code="INH", correcta=True, tr_ms=350)
    url = reverse("panel-metrics") + "?format=csv"
    r = client.get(url, HTTP_X_PANEL_TOKEN="mi-token-local")
    assert r.status_code == 200
    assert r["Content-Type"].startswith("text/csv")
    body = r.content.decode("utf-8")
    assert "sesion_id,ccp_code,n,aciertos,acierto_pct,tr_ms_avg,first_ts,last_ts" in body
