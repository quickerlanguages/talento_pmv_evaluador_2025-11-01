import csv
import io
import pytest
from django.db import connection
from django.conf import settings

pytestmark = pytest.mark.django_db(transaction=True)
def _parse_csv(content: bytes):
    text = content.decode()
    reader = csv.DictReader(io.StringIO(text))
    return [{k: v for k, v in row.items()} for row in reader]

def test_export_by_ccp_matches_sql(client):
    url = "/api/export/session/2/by_ccp?date_from=2025-10-01&date_to=2025-10-31"
    r = client.get(url, HTTP_X_PANEL_TOKEN=settings.PANEL_ORIENTADOR_TOKEN)
    assert r.status_code == 200
    csv_rows = _parse_csv(r.content)
    with connection.cursor() as cur:
        cur.execute("""
        SELECT v.ccp_code,
               COUNT(*) AS n,
               ROUND(AVG(v.correcta)*100,1) AS acierto_pct,
               CAST(ROUND(AVG(v.tr_ms),0) AS INTEGER) AS tr_ms_avg
        FROM v_respuesta_basic v
        JOIN respuesta r USING(id_respuesta)
        WHERE v.sesion_id=2
          AND date(r.created_at) BETWEEN '2025-10-01' AND '2025-10-31'
        GROUP BY v.ccp_code
        ORDER BY v.ccp_code;
        """)
        sql_rows = [
            {"ccp_code": code, "n": str(n), "acierto_pct": str(pct), "tr_ms_avg": str(tr)}
            for code, n, pct, tr in cur.fetchall()
        ]
    assert csv_rows == sql_rows
