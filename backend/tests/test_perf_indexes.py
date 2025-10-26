import time
import pytest
from django.db import connection

pytestmark = pytest.mark.django_db(transaction=True)

def _q(sql, params=()):
    with connection.cursor() as cur:
        t0 = time.perf_counter()
        cur.execute(sql, params)
        rows = cur.fetchall()
        dt = (time.perf_counter() - t0) * 1000  # ms
    return rows, dt

def test_count_and_last10_timed(capsys):
    sql1 = """
    SELECT COUNT(*) FROM tlt_respuesta
    WHERE sesion_id=? AND ccp_code=?
      AND created_at BETWEEN ? AND ?;
    """
    sql2 = """
    SELECT created_at FROM tlt_respuesta
    WHERE sesion_id=? AND ccp_code=?
      AND created_at BETWEEN ? AND ?
    ORDER BY created_at DESC
    LIMIT 10;
    """
    params = (2, "MDT", "2025-10-01", "2025-10-31 23:59:59")

    _, t1 = _q(sql1, params)
    _, t2 = _q(sql2, params)

    print(f"[perf] COUNT(*) ms={t1:.3f}")
    print(f"[perf] LAST10 ms={t2:.3f}")

    # No aseveramos tiempos: solo registro. (Podrías poner umbrales suaves si quieres.)
    captured = capsys.readouterr()
    assert "[perf]" in captured.out
