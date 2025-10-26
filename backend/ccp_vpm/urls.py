from django.urls import path
from . import views

urlpatterns = [
    path("api/v1/sessions", views.create_session),
    path("api/v1/trials", views.post_trial),
    path("api/v1/score/session/<int:session_id>", views.session_score),
    path("vpm/code-ghost/<int:session_id>", views.ui_code_ghost),
    path("vpm/scene-ghost/<int:session_id>", views.ui_scene_ghost),
]
