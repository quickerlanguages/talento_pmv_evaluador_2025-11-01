# backend/talento_backend_v2/urls.py
from django.contrib import admin
from django.urls import path, include
from . import views
from talento_core.core_views import (
    ui_progress, play_ui, api_export_session,
    create_respuesta, api_next_vpm_item, api_answer,
    api_debug_db, api_csrf, qa_final, api_backfill_legacy_to_tlt
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # UI/legacy del core (si los usas aún)
    path("progress", ui_progress, name="ui_progress"),
    path("play", play_ui, name="play_ui"),

    # API del core (existente)
    path("api/export/session/<int:sesion_id>", api_export_session, name="api_export_session"),
    path("api/respuesta", create_respuesta, name="create_respuesta"),
    path("api/next-vpm-item", api_next_vpm_item, name="api_next_vpm_item"),
    path("api/answer", api_answer, name="api_answer"),
    path("api/debug-db", api_debug_db, name="api_debug_db"),
    path("api/csrf", api_csrf, name="api_csrf"),
    path("api/qa/final/", qa_final, name="qa_final"),
    path("api/backfill", views.api_backfill, name="api_backfill"),


    # Nuevo Panel Orientador (M4/M5)
    path("orientador/", views.orientador_panel, name="orientador"),
    path("accounts/", include("django.contrib.auth.urls")),  # login/logout

    # APIs del Panel (protegidas por token/login)
    path("api/sessions", views.api_sessions, name="api_sessions"),
    path("api/progress", views.api_progress, name="api_progress"),
    path("api/export/session/<int:sesion_id>/by_ccp", views.api_export_by_ccp, name="api_export_by_ccp"),
    path("api/export/session/<int:sesion_id>/by_ejer", views.api_export_by_ejer, name="api_export_by_ejer"),

    # (Opcional) otras rutas del core
    path("", include("talento_core.core_urls")),

    path("api/health", views.health),

    path("", include("runtime.urls"))
]
