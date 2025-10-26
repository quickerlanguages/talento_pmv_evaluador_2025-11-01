from django.conf import settings
from django.http import JsonResponse

def panel_token_required(view):
    from functools import wraps
    @wraps(view)
    def _w(request, *a, **kw):
        if getattr(request, "user", None) and request.user.is_authenticated:
            return view(request, *a, **kw)
        token_cfg = getattr(settings, "PANEL_ORIENTADOR_TOKEN", None)
        token = request.headers.get("X-Panel-Token") or (
            request.GET.get("token") if getattr(settings, "PANEL_ALLOW_QUERYTOKEN", True) else None
        )
        if (token_cfg and token == token_cfg) or (not token_cfg and settings.DEBUG):
            return view(request, *a, **kw)
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    return _w
