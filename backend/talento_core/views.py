
# talento_core/views.py — SHIM ROBUSTO (v2)

from importlib import import_module
from django.http import JsonResponse

from django.views.decorators.csrf import ensure_csrf_cookie


# Cargamos el módulo real con las vistas
_core = import_module(".core_views", __package__)

def _export(name):
    if hasattr(_core, name):
        globals()[name] = getattr(_core, name)
    if hasattr(_core, "play_ui"):
        play_ui = ensure_csrf_cookie(getattr(_core, "play_ui"))

# Reexportamos nombres habituales
for _name in [
    "ui_progress",
    "api_progress",
    "api_export_session",
    "api_next_vpm_item",
    "api_submit_answer",
    "create_respuesta",
    "play_ui",
    "api_debug_db",
    "api_answer",  # por si existe nativo
]:
    _export(_name)

# Alias de compatibilidad: api_answer -> api_submit_answer
if "api_answer" not in globals():
    if hasattr(_core, "api_submit_answer"):
        def api_answer(request, *args, **kwargs):
            return _core.api_submit_answer(request, *args, **kwargs)
    else:
        def api_answer(request, *args, **kwargs):
            return JsonResponse({"error": "api_answer no implementado"}, status=501)

# Fallbacks suaves para levantar el server aunque falte alguna vista
if "api_debug_db" not in globals():
    from django.db import connection
    def api_debug_db(request, *args, **kwargs):
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
                one = cur.fetchone()[0]
            return JsonResponse({
                "ok": True,
                "ping": one,
                "vendor": connection.vendor,
                "alias": getattr(connection, "alias", "default")
            })
        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=500)

__all__ = [
    "ui_progress",
    "api_progress",
    "api_export_session",
    "api_next_vpm_item",
    "api_submit_answer",
    "create_respuesta",
    "play_ui",
    "api_debug_db",
    "api_answer",
]

