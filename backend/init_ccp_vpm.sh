#!/usr/bin/env bash
set -euo pipefail

APP=ccp_vpm
ROOT="$(pwd)"

echo "→ Creando app (si no existe)…"
if [ ! -d "$APP" ]; then
  python3 manage.py startapp $APP || python manage.py startapp $APP
fi

echo "→ Estructura de carpetas"
mkdir -p $APP/templates/$APP
mkdir -p $APP/static/$APP/js
mkdir -p $APP/management/commands

# apps.py
cat > $APP/apps.py <<'PY'
from django.apps import AppConfig
class CcpVpmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ccp_vpm"
PY

# models.py
cat > $APP/models.py <<'PY'
from django.db import models

class VpmSubmodality(models.TextChoices):
    VIS_S = "VIS_S", "Visual Simbólica"
    VIS_I = "VIS_I", "Visual Icónica"

class Session(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)
    user_id = models.CharField(max_length=64, blank=True, null=True)
    vpm_mode = models.CharField(max_length=16, choices=VpmSubmodality.choices)
    meta = models.JSONField(default=dict, blank=True)

class Item(models.Model):
    submodality = models.CharField(max_length=16, choices=VpmSubmodality.choices)
    difficulty_level = models.PositiveSmallIntegerField(default=1)
    stimulus = models.JSONField()
    options = models.JSONField()
    correct_index = models.PositiveSmallIntegerField()
    params = models.JSONField(default=dict, blank=True)

class Trial(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="trials")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    started_ms = models.IntegerField()
    responded_ms = models.IntegerField()
    response_time_ms = models.IntegerField()
    chosen_index = models.IntegerField()
    is_correct = models.BooleanField()
    client_meta = models.JSONField(default=dict, blank=True)
PY

# urls.py
cat > $APP/urls.py <<'PY'
from django.urls import path
from . import views

urlpatterns = [
    path("api/v1/sessions", views.create_session),
    path("api/v1/trials", views.post_trial),
    path("api/v1/score/session/<int:session_id>", views.session_score),
    path("vpm/code-ghost/<int:session_id>", views.ui_code_ghost),
    path("vpm/scene-ghost/<int:session_id>", views.ui_scene_ghost),
]
PY

# views.py
cat > $APP/views.py <<'PY'
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
    _ = get_object_or_404(Session, id=session_id, vpm_mode=VpmSubmodality.VIS_S)
    items = Item.objects.filter(submodality=VpmSubmodality.VIS_S).order_by("difficulty_level")[:12]
    return render(request, "ccp_vpm/code_ghost.html", {"session_id": session_id, "items": items})

def ui_scene_ghost(request, session_id:int):
    _ = get_object_or_404(Session, id=session_id, vpm_mode=VpmSubmodality.VIS_I)
    items = Item.objects.filter(submodality=VpmSubmodality.VIS_I).order_by("difficulty_level")[:12]
    return render(request, "ccp_vpm/scene_ghost.html", {"session_id": session_id, "items": items})
PY

# templates
cat > $APP/templates/$APP/code_ghost.html <<'HTML'
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Código Fantasma — VPM</title>
  <script src="/static/ccp_vpm/js/code_ghost.js" defer></script>
  <style>
    body { font-family: system-ui, sans-serif; padding: 24px; }
    .panel { border: 1px solid #444; padding: 16px; border-radius: 12px; margin-bottom: 16px;}
    .symbols { font-size: 40px; letter-spacing: 10px; text-align:center; }
    .options { display:flex; gap:12px; }
    .opt { flex:1; border:1px solid #888; padding:12px; border-radius: 10px; cursor:pointer; text-align:center;}
    .hidden { visibility: hidden; }
  </style>
</head>
<body>
  <h1>Código Fantasma (VIS-S)</h1>
  <div class="panel">
    <div id="flash" class="symbols"></div>
    <div id="mask" class="symbols hidden">•••</div>
  </div>
  <div class="panel">
    <div class="options" id="options"></div>
  </div>
  <div id="status"></div>

  <script>
    window.VPM_SESSION_ID = {{ session_id }};
    window.VPM_ITEMS = {{ items|safe }};
  </script>
</body>
</html>
HTML

cat > $APP/templates/$APP/scene_ghost.html <<'HTML'
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Escena Fantasma — VPM</title>
  <script src="/static/ccp_vpm/js/scene_ghost.js" defer></script>
  <style>
    body { font-family: system-ui, sans-serif; padding: 24px; }
    .stage { display:flex; justify-content:center; align-items:center; height:180px; border:1px solid #444; border-radius:12px; margin-bottom:16px;}
    .options { display:flex; gap:12px; }
    .opt { flex:1; border:1px solid #888; padding:12px; border-radius: 10px; cursor:pointer; text-align:center;}
    .hidden { visibility:hidden; }
  </style>
</head>
<body>
  <h1>Escena Fantasma (VIS-I)</h1>
  <div class="stage">
    <canvas id="sceneCanvas" width="420" height="140"></canvas>
  </div>
  <div class="options" id="options"></div>
  <div id="status"></div>

  <script>
    window.VPM_SESSION_ID = {{ session_id }};
    window.VPM_ITEMS = {{ items|safe }};
  </script>
</body>
</html>
HTML

# JS
cat > $APP/static/$APP/js/code_ghost.js <<'JS'
(function(){
  const flashEl = document.getElementById("flash");
  const maskEl = document.getElementById("mask");
  const optsEl = document.getElementById("options");
  const statusEl = document.getElementById("status");

  let idx = 0;
  let startedMs = 0;

  function renderSymbols(arr){ flashEl.textContent = arr.join(" "); }

  function nextItem(){
    if (idx >= VPM_ITEMS.length){ statusEl.textContent = "Fin de la serie."; return; }
    const it = VPM_ITEMS[idx];
    renderSymbols(it.stimulus.symbols);
    maskEl.classList.add("hidden");
    optsEl.innerHTML = "";
    setTimeout(()=>{
      maskEl.classList.remove("hidden");
      flashEl.textContent = "";
      it.options.forEach((opt, i)=>{
        const d = document.createElement("div");
        d.className = "opt";
        d.textContent = (opt.symbols||[]).join(" ");
        d.onclick = ()=> choose(i);
        optsEl.appendChild(d);
      });
      startedMs = Date.now();
    }, it.params.flash_ms || 1500);
  }

  async function choose(chosenIndex){
    const it = VPM_ITEMS[idx];
    const respondedMs = Date.now();
    const payload = {
      session_id: VPM_SESSION_ID,
      item_id: it.id,
      started_ms: startedMs,
      responded_ms: respondedMs,
      chosen_index: chosenIndex,
      client_meta: { ua: navigator.userAgent }
    };
    const res = await fetch("/api/v1/trials", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });
    const j = await res.json();
    statusEl.textContent = j.is_correct ? "✔️ Correcto ("+j.response_time_ms+" ms)" : "✖️ Incorrecto ("+j.response_time_ms+" ms)";
    idx += 1;
    setTimeout(()=>{ statusEl.textContent=""; nextItem(); }, 600);
  }

  nextItem();
})();
JS

cat > $APP/static/$APP/js/scene_ghost.js <<'JS'
(function(){
  const canvas = document.getElementById("sceneCanvas");
  const ctx = canvas.getContext("2d");
  const optsEl = document.getElementById("options");
  const statusEl = document.getElementById("status");

  let idx = 0, startedMs = 0;

  function drawBase(){
    ctx.clearRect(0,0,canvas.width, canvas.height);
    ctx.fillRect(40, 50, 40, 40);
    ctx.beginPath(); ctx.arc(180, 70, 20, 0, Math.PI*2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(280, 90); ctx.lineTo(320, 30); ctx.lineTo(360, 90); ctx.closePath(); ctx.fill();
  }

  function nextItem(){
    if (idx >= VPM_ITEMS.length){ statusEl.textContent = "Fin de la serie."; return; }
    const it = VPM_ITEMS[idx];
    drawBase();
    setTimeout(()=>{
      ctx.clearRect(0,0,canvas.width,canvas.height);
      optsEl.innerHTML = "";
      it.options.forEach((opt,i)=>{
        const d = document.createElement("div");
        d.className = "opt";
        d.textContent = `Opción ${i+1} (${opt.change||"none"})`;
        d.onclick = ()=> choose(i);
        optsEl.appendChild(d);
      });
      startedMs = Date.now();
    }, it.params.flash_ms || 1500);
  }

  async function choose(chosenIndex){
    const it = VPM_ITEMS[idx];
    const respondedMs = Date.now();
    const payload = {
      session_id: VPM_SESSION_ID,
      item_id: it.id,
      started_ms: startedMs,
      responded_ms: respondedMs,
      chosen_index: chosenIndex,
      client_meta: { ua: navigator.userAgent }
    };
    const res = await fetch("/api/v1/trials", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });
    const j = await res.json();
    statusEl.textContent = j.is_correct ? `✔️ Correcto (${j.response_time_ms} ms)` : `✖️ Incorrecto (${j.response_time_ms} ms)`;
    idx += 1;
    setTimeout(()=>{ statusEl.textContent=""; nextItem(); }, 600);
  }

  nextItem();
})();
JS

# seed command
cat > $APP/management/commands/seed_vpm_demo.py <<'PY'
from django.core.management.base import BaseCommand
from ccp_vpm.models import Item, VpmSubmodality

class Command(BaseCommand):
    help = "Carga items demo para VPM (Visual Simbólica e Icónica)"

    def handle(self, *args, **opts):
        Item.objects.all().delete()

        demo_sym = [
            (1, ["A","∆","7"], [["A","7","∆"],["A","∆","7"],["7","A","∆"]], 1, {"flash_ms":1800}),
            (2, ["B","Φ","3","∆"], [["B","3","∆","Φ"],["B","Φ","3","∆"],["Φ","B","3","∆"]], 1, {"flash_ms":1600}),
            (3, ["Q","∑","9","∂","Z"], [["Q","∑","9","∂","Z"],["Q","9","∑","∂","Z"],["Z","∑","9","∂","Q"]], 0, {"flash_ms":1500}),
        ]
        for lvl, seq, opts, correct, params in demo_sym:
            Item.objects.create(
                submodality=VpmSubmodality.VIS_S,
                difficulty_level=lvl,
                stimulus={"symbols": seq},
                options=[{"symbols": o} for o in opts],
                correct_index=correct,
                params=params
            )

        demo_img = [
            (1, {"base":"scene_1"}, [{"change":"none"},{"change":"remove-dot"},{"change":"swap-colors"}], 0, {"flash_ms":1800}),
            (2, {"base":"scene_2"}, [{"change":"none"},{"change":"mirror-left"},{"change":"remove-segment"}], 1, {"flash_ms":1600}),
            (3, {"base":"scene_3"}, [{"change":"remove-small-shape"},{"change":"none"},{"change":"rotate-15"}], 1, {"flash_ms":1500}),
        ]
        for lvl, stim, opts, correct, params in demo_img:
            Item.objects.create(
                submodality=VpmSubmodality.VIS_I,
                difficulty_level=lvl,
                stimulus=stim,
                options=opts,
                correct_index=correct,
                params=params
            )

        self.stdout.write(self.style.SUCCESS("Items demo cargados"))
PY

echo
echo "→ Añade 'ccp_vpm' a INSTALLED_APPS y monta rutas en urls.py principal:"
echo "   INSTALLED_APPS += ['ccp_vpm']"
echo "   urlpatterns += [ path('', include('ccp_vpm.urls')), ]"
echo "Listo."
