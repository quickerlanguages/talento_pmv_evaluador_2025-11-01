from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("runtime", "0001_add_created_at_to_respuesta"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_sesion_fecha ON tlt_respuesta(sesion_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_sesion_ccp   ON tlt_respuesta(sesion_id, ccp_code);
                CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_sesion_ejer  ON tlt_respuesta(sesion_id, ejer_code);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_tlt_respuesta_sesion_fecha;
                DROP INDEX IF EXISTS idx_tlt_respuesta_sesion_ccp;
                DROP INDEX IF EXISTS idx_tlt_respuesta_sesion_ejer;
            """,
        ),
    ]

