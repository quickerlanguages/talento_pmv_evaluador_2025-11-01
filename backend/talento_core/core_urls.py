# backend/talento_core/core_urls.py
from django.urls import path
from . import views           # vistas “normales” (UI + APIs actuales)
from . import core_views      # utilidades/legacy (solo lo que necesites)

urlpatterns = [
    # UI
    path("progress", views.ui_progress, name="ui_progress"),
    path("play", views.play_ui, name="play_ui"),

    # APIs actuales
    path("api/progress", views.api_progress, name="api_progress"),
    path("api/export/session/<int:sesion_id>", views.api_export_session, name="api_export_session"),
    path("api/respuesta", views.create_respuesta, name="create_respuesta"),
    path("api/next-vpm-item", views.api_next_vpm_item, name="api_next_vpm_item"),
    path("api/answer", views.api_answer, name="api_answer"),

    # Debug (vive en core_views)
    path("api/debug-db", core_views.api_debug_db, name="api_debug_db"),

    path("api/csrf", core_views.api_csrf, name="api_csrf"),
]
