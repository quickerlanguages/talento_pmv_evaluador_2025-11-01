# progress/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("api/progress", views.api_progress, name="api_progress"),
    path("api/export/session/<int:sesion_id>", views.api_export_session, name="api_export_session"),
]
