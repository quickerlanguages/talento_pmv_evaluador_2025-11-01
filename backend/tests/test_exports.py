import re
import pytest
from django.conf import settings

pytestmark = pytest.mark.django_db(transaction=True)

def _token_headers():
    return {"HTTP_X_PANEL_TOKEN": settings.PANEL_ORIENTADOR_TOKEN}

def test_sessions_smoke(client, settings):
    r = client.get("/api/sessions", HTTP_X_PANEL_TOKEN=settings.PANEL_ORIENTADOR_TOKEN)
    assert r.status_code == 200
    js = r.json()
    assert js.get("ok") is True
    assert isinstance(js.get("sessions"), list)

def test_export_by_ccp_ok(client):
    r = client.get("/api/export/session/2/by_ccp", **_token_headers())
    assert r.status_code == 200
    disp = r.headers.get("Content-Disposition", "")
    assert re.search(r'sesion_2_by_ccp', disp)
    head = r.content.splitlines()[0].decode()
    assert head == "ccp_code,n,acierto_pct,tr_ms_avg"

def test_export_by_ccp_with_filters(client):
    url = "/api/export/session/2/by_ccp?ccp=MDT&date_from=2025-10-01&date_to=2025-10-31"
    r = client.get(url, **_token_headers())
    assert r.status_code == 200
    disp = r.headers.get("Content-Disposition", "")
    assert "ccp-MDT" in disp and "2025-10-01" in disp and "2025-10-31" in disp
    lines = r.content.decode().strip().splitlines()
    assert len(lines) >= 1  # al menos la cabecera
def test_export_by_ejer_with_filters(client):
    url = "/api/export/session/2/by_ejer?ccp=MDT&ejer=visual&date_from=2025-10-01&date_to=2025-10-31"
    r = client.get(url, **_token_headers())
    assert r.status_code == 200
    disp = r.headers.get("Content-Disposition", "")
    assert all(s in disp for s in ("ccp-MDT", "ejer-visual", "2025-10-01", "2025-10-31"))
    head = r.content.splitlines()[0].decode()
    assert head == "ccp_code,ejer_code,n,acierto_pct,tr_ms_avg"

def test_export_forbidden_without_token(client):
    r = client.get("/api/export/session/2/by_ccp")
    assert r.status_code in (401, 403)
def test_export_empty_filters(client):
    url = "/api/export/session/2/by_ejer?ccp=ZZZ&ejer=falso&date_from=2025-10-01&date_to=2025-10-31"
    r = client.get(url, HTTP_X_PANEL_TOKEN=settings.PANEL_ORIENTADOR_TOKEN)
    assert r.status_code == 200
    lines = r.content.decode().strip().splitlines()
    # Sólo cabecera (sin datos)
    assert len(lines) == 1

def test_export_invalid_dates(client):
    url = "/api/export/session/2/by_ccp?date_from=2025-11-01&date_to=2025-10-01"
    r = client.get(url, HTTP_X_PANEL_TOKEN=settings.PANEL_ORIENTADOR_TOKEN)
    # Esperado: 400 si implementas validación, o 200 con CSV vacío
    assert r.status_code in (200, 400)

def test_invalid_date_from_returns_400(client, settings):
    r = client.get("/api/export/session/2/by_ccp?date_from=2025-13-40",
                   HTTP_X_PANEL_TOKEN=settings.PANEL_ORIENTADOR_TOKEN)
    assert r.status_code == 400

def test_inverted_range_returns_400(client, settings):
    r = client.get("/api/progress?sesion_id=2&date_from=2025-10-31&date_to=2025-10-01",
                   HTTP_X_PANEL_TOKEN=settings.PANEL_ORIENTADOR_TOKEN)
    assert r.status_code == 400

def test_head_sets_filename(client, settings):
    r = client.head("/api/export/session/2/by_ejer?ccp=MDT&ejer=visual&date_from=2025-10-01&date_to=2025-10-31",
                    HTTP_X_PANEL_TOKEN=settings.PANEL_ORIENTADOR_TOKEN)
    assert r.status_code == 200
    assert "filename=" in r.headers.get("Content-Disposition","")
