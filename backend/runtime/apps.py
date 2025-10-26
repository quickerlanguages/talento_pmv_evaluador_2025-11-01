from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.dispatch import receiver

class RuntimeConfig(AppConfig):
    name = "runtime"
    verbose_name = "Runtime hooks"

    def ready(self):
        @receiver(connection_created)
        def activate_sqlite_fk(sender, connection, **kwargs):
            if connection.vendor == "sqlite":
                with connection.cursor() as cur:
                    cur.execute("PRAGMA foreign_keys = ON;")
