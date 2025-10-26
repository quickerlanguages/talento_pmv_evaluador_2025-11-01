import json, statistics
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Session, Item, Trial, VpmSubmodality

def _require_fields(data, fields):
    missing = [f for f in fields if f not in data]
    if missing:
        return f"Missing fields: {', '.join(missing)}"
    return None

@csrf_exempt
def create_session(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")
    err = _require_fields(data, ["vpm_mode"])
    if err: return HttpResponseBadRequest(err)

    sess = Session.objects.create(
        vpm_mode=data["vpm_mode"],
        user_id=data.get("user_id"),
        meta=data.get("meta", {})
    )
    items = list(Item.objects.filter(submodality=data["vpm_mode"]).order_by("difficulty_level")[:12]
                 .values("id","difficulty_level","stimulus","options","params"))
    return JsonResponse({"session_id": sess.id, "items": items})

@csrf_exempt
def post_trial(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")
    err = _require_fields(data, ["session_id","item_id","started_ms","responded_ms","chosen_index"])
    if err: return HttpResponseBadRequest(err)

    session = get_object_or_404(Session, id=data["session_id"])
    item = get_object_or_404(Item, id=data["item_id"])
    rt = int(data["responded_ms"]) - int(data["started_ms"])
    is_correct = int(data["chosen_index"]) == item.correct_index

    Trial.objects.create(
        session=session, item=item,
        started_ms=data["started_ms"], responded_ms=data["responded_ms"],
        response_time_ms=rt, chosen_index=data["chosen_index"],
        is_correct=is_correct, client_meta=data.get("client_meta", {})
    )
    return JsonResponse({"ok": True, "is_correct": is_correct, "response_time_ms": rt})

def session_score(request, session_id: int):
    sess = get_object_or_404(Session, id=session_id)
    trials = list(Trial.objects.filter(session=sess).values("is_correct","response_time_ms","item__difficulty_level"))
    if not trials:
        return JsonResponse({"session_id": sess.id, "n": 0, "message":"No trials yet"})

    acc = sum(1 for t in trials if t["is_correct"]) / len(trials)
    rt_list = [t["response_time_ms"] for t in trials]
    rt_avg = sum(rt_list)/len(rt_list)
    from collections import defaultdict
    by_lvl = defaultdict(lambda: {"n":0,"ok":0})
    for t in trials:
        lvl = t["item__difficulty_level"]
        by_lvl[lvl]["n"] += 1
        by_lvl[lvl]["ok"] += 1 if t["is_correct"] else 0
    reached = max([lvl for lvl,agg in by_lvl.items() if agg["n"]>0 and agg["ok"]/agg["n"]>=0.6], default=1)

    return JsonResponse({
        "session_id": sess.id,
        "mode": sess.vpm_mode,
        "n": len(trials),
        "accuracy": round(acc,3),
        "rt_avg_ms": int(rt_avg),
        "rt_median_ms": int(sorted(rt_list)[len(rt_list)//2]),
        "level_reached": reached,
    })

def ui_code_ghost(request, session_id:int):
    sess = get_object_or_404(Session, id=session_id, vpm_mode=VpmSubmodality.VIS_S)
    items = Item.objects.filter(submodality=VpmSubmodality.VIS_S).order_by("difficulty_level")[:12]
    items = list(items.values("id","difficulty_level","stimulus","options","params"))
    return render(request, "ccp_vpm/code_ghost.html", {"session_id": session_id, "items": items})

def ui_scene_ghost(request, session_id:int):
    sess = get_object_or_404(Session, id=session_id, vpm_mode=VpmSubmodality.VIS_I)
    items = Item.objects.filter(submodality=VpmSubmodality.VIS_I).order_by("difficulty_level")[:12]
    items = list(items.values("id","difficulty_level","stimulus","options","params"))
    return render(request, "ccp_vpm/scene_ghost.html", {"session_id": session_id, "items": items})
