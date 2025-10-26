from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ("runtime", "0002_add_tlt_respuesta_indexes"),  # ajusta si tu número cambia
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DROP INDEX IF EXISTS idx_tlt_resp_sesion;
            DROP INDEX IF EXISTS idx_tlt_respuesta_sesion;
            DROP INDEX IF EXISTS idx_tlt_respuesta_created;
            DROP INDEX IF EXISTS idx_tlt_respuesta_ccp;
            DROP INDEX IF EXISTS idx_tlt_respuesta_ejer;
            """,
            reverse_sql="""
            CREATE INDEX IF NOT EXISTS idx_tlt_resp_sesion
                ON tlt_respuesta(sesion_id);
            CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_sesion
                ON tlt_respuesta(sesion_id);
            CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_created
                ON tlt_respuesta(created_at);
            CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_ccp
                ON tlt_respuesta(ccp_code);
            CREATE INDEX IF NOT EXISTS idx_tlt_respuesta_ejer
                ON tlt_respuesta(ejer_code);
            """,
        ),
    ]
