from django.urls import path
from . import views

urlpatterns = [
    path("smoke/", views.smoke, name="smoke"),
    path("smoke-ui/", views.smoke_ui, name="smoke-ui"),
    path("panel/metrics", views.panel_metrics, name="panel-metrics"),
    path("panel/", views.panel_page, name="panel-page"),  # <— NUEVO
]
