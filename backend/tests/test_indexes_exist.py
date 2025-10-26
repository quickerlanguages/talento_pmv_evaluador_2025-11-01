import pytest
from django.db import connection

pytestmark = pytest.mark.django_db(transaction=True)

def _index_names(table):
    with connection.cursor() as cur:
        cur.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name=?
            ORDER BY name
        """, [table])
        return [r[0] for r in cur.fetchall()]

def test_required_indexes_present():
    names = _index_names("tlt_respuesta")
    # Índices “canónicos”
    assert "idx_tlt_respuesta_sesion_fecha" in names
    assert "idx_tlt_respuesta_sesion_ccp_fecha" in names
