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
