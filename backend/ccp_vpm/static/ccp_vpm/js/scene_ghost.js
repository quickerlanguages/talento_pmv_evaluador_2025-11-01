(function(){
  'use strict';
  const canvas = document.getElementById("sceneCanvas");
  if(!canvas){ console.error("VIS-I: no canvas"); return; }
  const ctx = canvas.getContext("2d");
  const optsEl = document.getElementById("options");
  if(!optsEl){ console.error("VIS-I: no options container"); return; }
  const statusEl = document.getElementById("status");
  const now = () => Date.now();
  const setStatus = (msg) => { if(statusEl) statusEl.textContent = msg || ""; console.log("[VIS-I]", msg||""); };
  const clamp = (n,min,max)=>Math.max(min,Math.min(max,n));
  let clickLock = false;
  const lock = (ms=400)=>{ clickLock = true; setTimeout(()=>clickLock=false, ms); };

  function clear(){ ctx.clearRect(0,0,canvas.width,canvas.height); }
  function fill(color){ ctx.fillStyle = color; ctx.fillRect(0,0,canvas.width,canvas.height); }
  function square(color){ ctx.fillStyle = color; ctx.fillRect(40, 50, 40, 40); }
  function circle(color){ ctx.fillStyle = color; ctx.beginPath(); ctx.arc(180,70,20,0,Math.PI*2); ctx.fill(); }
  function triangle(color){ ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(280,90); ctx.lineTo(320,30); ctx.lineTo(360,90); ctx.closePath(); ctx.fill(); }
  const PALETTE = { fg: "#eaeaea", bg: "#222222" };
  function drawBaseScene(pal=PALETTE){ clear(); fill(pal.bg); square(pal.fg); circle(pal.fg); triangle(pal.fg); }
  function drawChangedScene(change){
    let fg = PALETTE.fg, bg = PALETTE.bg;
    if(change === "swap-colors"){ const t = fg; fg = bg; bg = t; }
    clear(); fill(bg);
    const showTri = !(change === "remove-segment");
    const showSq  = !(change === "remove-small-shape");
    const showCir = !(change === "remove-dot");
    if(showSq) square(fg);
    if(showCir) circle(fg);
    if(showTri){
      ctx.save();
      if(change === "mirror-left"){ ctx.translate(320,0); ctx.scale(-1,1); ctx.translate(-320,0); }
      if(change === "rotate-15"){ ctx.translate(320,70); ctx.rotate(15*Math.PI/180); ctx.translate(-320,-70); }
      triangle(fg);
      ctx.restore();
    }
  }
  let idx = 0;
  let startedMs = 0;
  const ITEMS = Array.isArray(window.VPM_ITEMS) ? window.VPM_ITEMS : [];
  if(ITEMS.length === 0){ setStatus("Sin ítems para mostrar"); return; }
  document.addEventListener("keydown", (e)=>{ if(e.key==="1") choose(0); if(e.key==="2") choose(1); if(e.key==="3") choose(2); });
  function label(change){
    const map = {"none":"Sin cambios","remove-dot":"Quitar círculo","swap-colors":"Intercambiar colores","mirror-left":"Espejo horizontal","remove-segment":"Quitar triángulo","remove-small-shape":"Quitar cuadrado","rotate-15":"Rotar 15°"};
    return map[change] || change;
  }
  function renderOptions(it){
    optsEl.innerHTML = "";
    (it.options || []).forEach((opt,i)=>{
      const d = document.createElement("div");
      d.className = "opt";
      d.textContent = label((opt && opt.change) || "none");
      d.tabIndex = 0;
      d.onclick = ()=> choose(i);
      d.onkeydown = (ev)=>{ if(ev.key==="Enter"||ev.key===" "){ choose(i); } };
      optsEl.appendChild(d);
    });
  }
  function nextItem(){
    if(idx >= ITEMS.length){ setStatus("Fin de la serie."); renderOptions({options:[]}); return; }
    const it = ITEMS[idx];
    const flashMs = clamp((it.params && it.params.flash_ms) ? it.params.flash_ms : 1500, 300, 4000);
    setStatus("Mostrando escena base…");
    drawBaseScene();
    setTimeout(()=>{
      const ci = (typeof it.correct_index==="number" && it.correct_index>=0) ? it.correct_index : 0;
      const correct = (Array.isArray(it.options) && it.options[ci]) ? (it.options[ci].change || "none") : "none";
      drawChangedScene(correct);
      renderOptions(it);
      setStatus("Elige el cambio realizado");
      startedMs = now();
    }, flashMs);
  }
  async function choose(chosenIndex){
    if(clickLock) return; lock();
    const it = ITEMS[idx];
    if(!it){ setStatus("Ítem inválido"); return; }
    const respondedMs = now();
    try{
      const res = await fetch("/api/v1/trials", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ session_id: window.VPM_SESSION_ID, item_id: it.id, started_ms: startedMs, responded_ms: respondedMs, chosen_index: chosenIndex, client_meta:{ua:navigator.userAgent} })
      });
      const j = await res.json();
      setStatus(j.is_correct ? `✔️ Correcto (${j.response_time_ms} ms)` : `✖️ Incorrecto (${j.response_time_ms} ms)`);
    }catch(err){ console.error(err); setStatus("Error enviando respuesta"); }
    idx += 1;
    setTimeout(()=>{ setStatus(""); nextItem(); }, 700);
  }
  nextItem();
})();