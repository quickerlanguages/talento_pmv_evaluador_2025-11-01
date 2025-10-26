from django.db import migrations, connection

SQL_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS trg_respuesta_set_created_at
AFTER INSERT ON respuesta
FOR EACH ROW
WHEN NEW.created_at IS NULL
BEGIN
  UPDATE respuesta
  SET created_at = datetime('now')
  WHERE id_respuesta = NEW.id_respuesta;
END;
"""

SQL_INDEX = """
CREATE INDEX IF NOT EXISTS idx_respuesta_sesion_fecha
ON respuesta(id_sesion, created_at);
"""

def forwards(apps, schema_editor):
    with connection.cursor() as cur:
        # 1) ¿Existe la columna created_at?
        cur.execute("PRAGMA table_info('respuesta');")
        cols = [row[1] for row in cur.fetchall()]  # row[1] = name
        if "created_at" not in cols:
            cur.execute("ALTER TABLE respuesta ADD COLUMN created_at TEXT;")
            # Backfill inicial
            cur.execute("UPDATE respuesta SET created_at = datetime('now') WHERE created_at IS NULL;")
        else:
            # Por si viniera nula en alguna fila antigua
            cur.execute("UPDATE respuesta SET created_at = datetime('now') WHERE created_at IS NULL;")

        # 2) Trigger (idempotente)
        cur.execute(SQL_TRIGGER)

        # 3) Índice (idempotente)
        cur.execute(SQL_INDEX)

def backwards(apps, schema_editor):
    # No eliminamos columna (riesgo de pérdida de datos).
    with connection.cursor() as cur:
        cur.execute("DROP TRIGGER IF EXISTS trg_respuesta_set_created_at;")
        cur.execute("DROP INDEX IF EXISTS idx_respuesta_sesion_fecha;")

class Migration(migrations.Migration):
    # Si es tu primera migración de 'runtime', puedes dejar dependencias vacías
    dependencies = []

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
