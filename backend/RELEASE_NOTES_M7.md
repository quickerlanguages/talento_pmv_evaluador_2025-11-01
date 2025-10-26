# Talento — Backend LTS / PMV (M7)

**Fecha:** 2025-10-21  
**Ámbito:** Entrega reproducible en local (SQLite) con Panel del Orientador operativo y datasets de prueba.

## Novedades clave
- Panel del Orientador `/panel/` estable (M5 cerrado).
- API `/panel/metrics` en JSON y CSV (export desde Makefile).
- Fixtures: `EXTENDED`, `HUGE` (~1k), `HUGE_x10` (~10k).
## QA y rendimiento (host local)

**Puerto 8001 (build PMV / SQLite LTS)**  
- JSON avg: **0.181 ms** · p95: **0.216 ms** (5 runs)  
- CSV avg: **0.148 ms** · p95: **0.148 ms** (5 runs)  
- Bench concurrente (40 req, P = 8): **avg 0.17 ms · p95 0.27 ms · p99 0.28 ms**

**Puerto 8000 (qa-full)**  
- JSON avg: **6.526 ms** · p95: **6.618 ms** (5 runs)  
- CSV avg: **6.680 ms** · p95: **6.680 ms** (5 runs) 
- Bench concurrente (40 req, P = 8): **avg 218.5 ms · p95 246.5 ms · p99 255.7 ms**

## Umbrales referencia (local, ~1 k filas)
- **PMV (8001)** → JSON avg ≤ 1 ms · CSV avg ≤ 1 ms · p95 ≤ 2 ms  
- **Ref (8000)** → JSON avg ≤ 10 ms · CSV avg ≤ 10 ms · p95 ≤ 15 ms  
- **Concurrente (40/8)** → avg ≤ 30 ms · p95 ≤ 50 ms

---

- Makefile con:
  - `qa-full`, `qa-report`, `bench-panel`, `bench-concurrent`
  - `fixtures-*`, `tune-panel`, `release`

---

## Requisitos
- macOS / Linux, Python 3.10+
- `sqlite3`, `curl`, `jq` (opcional para inspección)

## Instalación rápida
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
./run.sh  # o: make run

---

## Verificación LTS / PMV reproducible

**Hash DB base:**  
```bash
shasum -a 256 talento_READY_2025-09-14.db