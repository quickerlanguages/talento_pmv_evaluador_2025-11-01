# ============================
#  Makefile - Backend Talento (M7 LTS/PMV)
# ============================

SHELL := /bin/bash
.ONESHELL:

# --- Runtime config (override por CLI o .env exportado en tu shell) ---
HOST ?= 127.0.0.1
PORT ?= 8000
BASE_URL ?= http://$(HOST):$(PORT)

export DJANGO_DEBUG ?= 1
export PANEL_ORIENTADOR_TOKEN ?= mi-token-local

# --- Paths & tools ---
BACKEND_DIR := .
VENV := $(BACKEND_DIR)/.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(PYTHON) -m pytest
MANAGE := $(PYTHON) $(BACKEND_DIR)/manage.py

# DBs
DB_SRC  ?= $(BACKEND_DIR)/talento_READY_2025-09-14.db
DB_TEST ?= $(BACKEND_DIR)/test.sqlite3
DB      ?= $(DB_SRC)

# Herramientas externas
CURL := curl -s
JQ   := jq -r
SQL  ?= $(shell command -v sqlite3 || echo /usr/bin/sqlite3)

# --- Excludes para el ZIP de release ---
EXCLUDES := \
  ".venv/*" "*/.venv/*" \
  "__pycache__/*" "*/__pycache__/*" "*.pyc" "*.pyo" \
  ".pytest_cache/*" "*/.pytest_cache/*" \
  ".DS_Store" "*/.DS_Store" \
  "_release_artifacts/*" "*/_release_artifacts/*" \
  "htmlcov/*" "*/htmlcov/*" \
  "_reports/*" "*/_reports/*" \
  "panel_metrics.json" "*/panel_metrics.json" \
  "panel_metrics.csv" "*/panel_metrics.csv" \
  "cookies.txt" "*/cookies.txt" \
  ".env" "*/.env" \
  "*.db-shm" "*.db-wal" \
  "*.db.BAK*" "*.BAK*" "*.bak" "*.bak_*" \
  "talento_READY_*RESPALDO*.db" \
  "test.sqlite3" "db.sqlite3" \
  ".zip"

# --- Phony ---
.PHONY: help init run run-8001 smoke answer freeze clean \
        db-path db-check db-tail restore-demo-db \
        qa test cov cov-html analyze explain-ccp release qa-fast \
        sql-views-check sql-views-sample \
        curl-metrics curl-metrics-sesion export-metrics-json export-metrics-csv open-panel \
        fixtures-load fixtures-clear \
        fixtures-extended-api fixtures-huge-api fixtures-huge-x10-api \
        fixtures-extended-sql fixtures-huge-sql fixtures-huge-x10-sql \
        fixtures-huge-clear fixtures-huge-x10-clear qa-reset \
        bench-panel bench-panel-filters explain-panel tune-panel \
        qa-full qa-report db-health db-vacuum panel-contract panel-security csv-validate \
        bench-concurrent clean-bak preflight-clean release-check sanitize

# ---------------- Help ----------------
help:
	@echo "Targets más usados:"
	@echo "  make init / run / run-8001 / smoke"
	@echo "  make qa-full / qa-report / bench-panel / bench-concurrent"
	@echo "  make fixtures-extended-api | -sql"
	@echo "  make fixtures-huge-api | -sql"
	@echo "  make fixtures-huge-x10-api | -sql"
	@echo "  make qa-reset (limpia sesiones >=100)"
	@echo "  make release (ZIP M7 LTS)"
	@echo "Variables: HOST, PORT, BASE_URL, PANEL_ORIENTADOR_TOKEN, DB_SRC"

# --------------- Bootstrap ---------------
init:
	python3 -m venv $(VENV)
	$(PIP) install -r $(BACKEND_DIR)/requirements.txt

run:
	DJANGO_DEBUG=$(DJANGO_DEBUG) $(BACKEND_DIR)/run.sh

run-8001:
	$(MANAGE) runserver 127.0.0.1:8001

smoke:
	@$(CURL) "$(BASE_URL)/smoke/" | jq
	@$(CURL) "$(BASE_URL)/smoke-ui/" | head -n 20

answer:
	@$(CURL) -X POST "$(BASE_URL)/api/answer/" \
	  -H "Content-Type: application/json" \
	  -d '{"sesion_id":1,"ejer_code":"VPM_CFANT_S","item_id":"demo_item_001","correcta":1,"tr_ms":999}' | jq

freeze:
	@$(PIP) freeze > $(BACKEND_DIR)/requirements.txt
	@echo "requirements.txt updated."

clean:
	@rm -rf __pycache__ */__pycache__ $(BACKEND_DIR)/**/__pycache__ *.pyc *.pyo
	@rm -rf $(BACKEND_DIR)/.pytest_cache htmlcov .coverage .coverage.*

# --------------- DB utils ---------------
db-path:
	@$(MANAGE) shell -c "from django.conf import settings; print(settings.DATABASES['default']['NAME'])"

db-check:
	@DB="$$(make -s db-path)"; echo "$$DB"; \
	$(SQL) "$$DB" "SELECT sesion_id,ejer_code,item_id,correcta,tr_ms FROM tlt_respuesta WHERE sesion_id=1 AND ejer_code='VPM_CFANT_S' AND item_id='demo_item_001';"

db-tail:
	@DB="$$(make -s db-path)"; \
	$(SQL) "$$DB" "SELECT rowid,sesion_id,ejer_code,item_id,correcta,tr_ms,created_at FROM tlt_respuesta ORDER BY rowid DESC LIMIT 10;"

restore-demo-db:
	@cd $(BACKEND_DIR) && cp -v talento_READY_2025-09-14_RESPALDO.db talento_READY_2025-09-14.db

# --------------- QA / Tests ---------------
qa:
	@echo "==> Preparing test DB and running tests"
	@DB_SRC_SH="$(DB_SRC)"; DB_TEST_SH="$(DB_TEST)"; \
	echo "DB_SRC = $$DB_SRC_SH"; echo "DB_TEST = $$DB_TEST_SH"; \
	rm -f "$$DB_TEST_SH"; \
	if [ ! -f "$$DB_SRC_SH" ]; then echo "ERROR: No existe $$DB_SRC_SH"; exit 1; fi; \
	cp "$$DB_SRC_SH" "$$DB_TEST_SH"; \
	$(MANAGE) migrate; \
	printf '%s\n' "ANALYZE;" "PRAGMA optimize;" | $(MANAGE) dbshell >/dev/null; \
	$(PYTEST) --reuse-db

test:
	$(PYTEST) --reuse-db

cov:
	$(PYTEST) --reuse-db --cov=. --cov-config=.coveragerc --cov-report=term-missing

cov-html:
	$(PYTEST) --reuse-db --cov=. --cov-config=.coveragerc --cov-report=html
	@echo "→ open htmlcov/index.html"

# --------------- Diagnostics ---------------
analyze:
	@printf '%s\n' "ANALYZE;" "PRAGMA optimize;" | $(MANAGE) dbshell >/dev/null

explain-ccp:
	@printf '%s\n' \
	"EXPLAIN QUERY PLAN" \
	"SELECT COUNT(*) FROM tlt_respuesta" \
	"WHERE sesion_id=2 AND ccp_code='MDT'" \
	"  AND created_at BETWEEN '2025-10-01' AND '2025-10-31 23:59:59';" \
	"" \
	"EXPLAIN QUERY PLAN" \
	"SELECT created_at" \
	"FROM tlt_respuesta" \
	"WHERE sesion_id=2 AND ccp_code='MDT'" \
	"  AND created_at BETWEEN '2025-10-01' AND '2025-10-31 23:59:59'" \
	"ORDER BY created_at DESC" \
	"LIMIT 10;" | $(MANAGE) dbshell

# --------------- Release (M7 LTS) ---------------
release: preflight-clean clean-bak
	@set -e
	@pkill -f "manage.py runserver" 2>/dev/null || true; sleep 1
	@mkdir -p _release_artifacts
	@ART="_release_artifacts/talento_backend_M7_LTS_$$(date +%Y-%m-%d).zip"; \
	echo "→ Construyendo $$ART"; \
	zip -r "$$ART" \
	  README.md RELEASE_NOTES_M7.md env.example Makefile . \
	  $(EXCLUDES:%=-x %) >/dev/null; \
	echo "ZIP: $$ART"; \
	unzip -t "$$ART"; \
	shasum -a 256 "$$ART"

# (Opcional) Comprobación rápida de que no se han colado cosas indeseadas
release-check:
	@ART="$$(ls -1t _release_artifacts/*.zip | head -n1)"; \
	echo "→ Verificando $$ART"; \
	if unzip -l "$$ART" | egrep '\.venv/|(^|/)_(reports|pytest_cache|htmlcov)/|(^|/)panel_metrics\.(json|csv)$$|(^|/)\.env$$|(^|/)test\.sqlite3$$|(^|/)db\.sqlite3$$|\.BAK(\.|_|/|$$)|\.bak(_|\.|/|$$)|(^|/)\.zip$$' > /tmp/release_check_hits.txt; then \
	  echo "❌ Se colaron ficheros prohibidos"; \
	  sed 's/^/   ⚠ /' /tmp/release_check_hits.txt; \
	  exit 1; \
	else \
	  echo "✅ OK: exclusiones aplicadas"; \
	fi

# Pre-chequeo de backups residuales antes de empaquetar
preflight-clean:
	@echo "→ Buscando backups residuales (*.bak, *.bak_*, *.BAK*, *.db.BAK.*)..."
	@found=$$(find . -type f \( -name '*.bak' -o -name '*.bak_*' -o -name '*.BAK*' -o -name '*.db.BAK.*' \)); \
	if [ -n "$$found" ]; then echo "$$found"; exit 1; else echo "✅ limpio"; fi

# Elimina backups y derivados que no deben empaquetarse
clean-bak:
	@find . -type f \( -name '*.bak' -o -name '*.bak_*' -o -name '*.BAK*' -o -name '*.db.BAK.*' \) -print -delete

qa-fast:
	$(PYTEST) --reuse-db

# --------------- Panel: vistas SQL ---------------
sql-views-check:
	@$(SQL) "$(DB_SRC)" "SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'v_panel_metrics%';"

sql-views-sample:
	@$(SQL) "$(DB_SRC)" "SELECT sesion_id, ccp_code, n, ROUND(acierto_pct,1) pct, ROUND(tr_ms_avg,1) tr FROM v_panel_metrics ORDER BY sesion_id, ccp_code LIMIT 20;"

# --------------- Panel: API helpers ---------------
curl-metrics:
	@$(CURL) -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" "$(BASE_URL)/panel/metrics" | jq

curl-metrics-sesion:
	@$(CURL) -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" "$(BASE_URL)/panel/metrics?sesion_id=$(SESION)" | jq

export-metrics-json:
	@$(CURL) -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" -H "Accept: application/json" \
	"$(BASE_URL)/panel/metrics?since=$(SINCE)&until=$(UNTIL)" > panel_metrics.json && echo "→ panel_metrics.json"

export-metrics-csv:
	@$(CURL) -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" -H "Accept: text/csv" \
	"$(BASE_URL)/panel/metrics?since=$(SINCE)&until=$(UNTIL)&format=csv" > panel_metrics.csv && echo "→ panel_metrics.csv"

open-panel:
	@open "$(BASE_URL)/panel/"

# --------------- Fixtures DEMO (ORM) ---------------
fixtures-load:
	@echo "→ Cargando fixtures demo (ORM)..."
	@$(MANAGE) loaddata runtime/fixtures/panel_demo_2025.json || echo "⚠️  Usa fixtures SQL o API si el modelo no existe en ORM."

fixtures-clear:
	@echo "→ Borrando sesiones demo (10,11)..."
	@printf "%s\n" "DELETE FROM tlt_respuesta WHERE sesion_id IN (10,11);" | $(MANAGE) dbshell >/dev/null

# --------------- Fixtures via SQL (repro rápido, sin servidor) ---------------
fixtures-extended-sql:
	@echo "==> Cargando EXTENDED vía SQL (~40 filas)"
	@$(SQL) "$(DB_SRC)" < runtime/sql/panel_fixtures_EXTENDED.sql
	@echo "OK: EXTENDED (SQL)"

fixtures-huge-sql:
	@echo "==> Cargando HUGE vía SQL (~1k filas, 100..119)"
	@$(SQL) "$(DB_SRC)" < runtime/sql/panel_fixtures_HUGE.sql
	@$(MAKE) tune-panel
	@$(SQL) "$(DB_SRC)" "SELECT sesion_id, COUNT(*) n, ROUND(AVG(tr_ms),1) tr FROM tlt_respuesta WHERE sesion_id BETWEEN 100 AND 119 GROUP BY sesion_id ORDER BY sesion_id LIMIT 5;"
	@$(SQL) "$(DB_SRC)" "SELECT ccp_code, COUNT(*) n, ROUND(AVG(correcta)*100,1) acierto_pct, ROUND(AVG(tr_ms),1) tr FROM tlt_respuesta WHERE sesion_id BETWEEN 100 Y 119 GROUP BY ccp_code ORDER BY ccp_code;"

fixtures-huge-x10-sql:
	@echo "==> Cargando HUGE x10 vía SQL (~10k filas, 200..399)"
	@$(SQL) "$(DB_SRC)" < runtime/sql/panel_fixtures_HUGE_x10.sql
	@$(MAKE) tune-panel
	@$(SQL) "$(DB_SRC)" "SELECT COUNT(*) FROM tlt_respuesta WHERE sesion_id BETWEEN 200 AND 399;"

# Limpieza datasets SQL de estrés
fixtures-huge-clear:
	@echo "==> Borrando sesiones HUGE (100..119)"
	@$(SQL) "$(DB_SRC)" "DELETE FROM tlt_respuesta WHERE sesion_id BETWEEN 100 AND 119;"
	@$(MAKE) tune-panel

fixtures-huge-x10-clear:
	@echo "==> Borrando sesiones HUGE x10 (200..399)"
	@$(SQL) "$(DB_SRC)" "DELETE FROM tlt_respuesta WHERE sesion_id BETWEEN 200 AND 399;"
	@$(MAKE) tune-panel

# --------------- Fixtures via API (requiere servidor en marcha) ---------------
define _BACKFILL_SESSION
CSRF=$$($(CURL) "$(BASE_URL)/api/csrf" -c cookies.txt | $(JQ) '.csrftoken'); \
$(CURL) -X POST \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $$CSRF" \
  -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" \
  -b cookies.txt \
  "$(BASE_URL)/api/backfill" \
  --data "{\"sesion_id\": $(1)}" | jq .
endef

define _ENSURE_SESSION
$(SQL) "$(DB_SRC)" "INSERT OR IGNORE INTO tlt_sesion(id) VALUES ($(1));"
endef

fixtures-extended-api:
	@set -e; \
	for sid in 11 12 13 14; do \
		echo "→ preparando sesion_id=$$sid"; \
		$(call _ENSURE_SESSION,$$sid); \
		$(call _BACKFILL_SESSION,$$sid); \
	done; \
	echo "OK: fixtures-extended (API)"

fixtures-huge-api:
	@set -e; \
	for sid in $$(seq 100 119); do \
		echo "→ preparando sesion_id=$$sid"; \
		$(call _ENSURE_SESSION,$$sid); \
		$(call _BACKFILL_SESSION,$$sid); \
	done; \
	echo "OK: fixtures-huge (API)"

fixtures-huge-x10-api:
	@set -e; \
	for sid in $$(seq 200 399); do \
		echo "→ preparando sesion_id=$$sid"; \
		$(call _ENSURE_SESSION,$$sid); \
		$(call _BACKFILL_SESSION,$$sid); \
	done; \
	echo "OK: fixtures-huge-x10 (API)"

# Limpieza unificada (para datasets de estrés)
qa-reset: fixtures-huge-clear fixtures-huge-x10-clear
	@echo "→ QA datasets limpiados."

# --------------- Bench & Tuning ---------------
bench-panel:
	@echo "==> Benchmark /panel/metrics (JSON y CSV)"
	@runs=5; \
	json_times=$$( for i in $$(seq 1 $$runs); do \
	    curl -s -o /dev/null -w '%{time_total}\n' -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" "$(BASE_URL)/panel/metrics"; \
	  done ); \
	printf "%s\n" "$$json_times" | nl -ba -w1 -s'. Run ' | sed 's/$$/s/'; \
	printf "%s\n" "$$json_times" | python3 -c 'import sys; v=[float(x) for x in sys.stdin.read().split()]; v.sort(); p=lambda q:int((len(v)-1)*q); print(f"→ JSON avg: {sum(v)/len(v)*1000:.3f} ms · p95: {v[p(0.95)]*1000:.3f} · p99: {v[p(0.99)]*1000:.3f}")'
	@echo ""
	@csv_times=$$( for i in $$(seq 1 $$runs); do \
	    curl -s -o /dev/null -w '%{time_total}\n' -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" "$(BASE_URL)/panel/metrics?format=csv"; \
	  done ); \
	printf "%s\n" "$$csv_times" | nl -ba -w1 -s'. Run ' | sed 's/$$/s/'; \
	printf "%s\n" "$$csv_times" | python3 -c 'import sys; v=[float(x) for x in sys.stdin.read().split()]; v.sort(); p=lambda q:int((len(v)-1)*q); print(f"→  CSV avg: {sum(v)/len(v)*1000:.3f} ms · p95: {v[p(0.95)]*1000:.3f} · p99: {v[p(0.99)]*1000:.3f}")'

bench-panel-filters:
	@echo "==> Bench con filtros (sesion_id=14)"
	@curl -s -o /dev/null -w '  JSON: %{time_total}s\n' -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" \
	  "$(BASE_URL)/panel/metrics?sesion_id=14"
	@curl -s -s -o /dev/null -w '  CSV:  %{time_total}s\n' -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" \
	  "$(BASE_URL)/panel/metrics?sesion_id=14&format=csv"
	@echo "==> Bench con rango de fechas (2025-10-16..21)"
	@curl -s -o /dev/null -w '  JSON: %{time_total}s\n' -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" \
	  "$(BASE_URL)/panel/metrics?since=2025-10-16&until=2025-10-21"

explain-panel:
	@echo "==> EXPLAIN QUERY PLAN v_panel_metrics"
	@$(SQL) "$(DB_SRC)" "EXPLAIN QUERY PLAN SELECT * FROM v_panel_metrics LIMIT 5;"
	@echo ""
	@echo "==> EXPLAIN QUERY PLAN v_panel_metrics_session"
	@$(SQL) "$(DB_SRC)" "EXPLAIN QUERY PLAN SELECT * FROM v_panel_metrics_session LIMIT 5;"

tune-panel:
	@echo "==> ANALYZE + PRAGMA optimize"
	@$(SQL) "$(DB_SRC)" "ANALYZE;"
	@$(SQL) "$(DB_SRC)" "PRAGMA optimize;"
	@echo "→ Optimización completada."

qa-full:
	@$(MAKE) tune-panel
	@$(MAKE) explain-panel
	@PANEL_ORIENTADOR_TOKEN="$(PANEL_ORIENTADOR_TOKEN)" $(MAKE) bench-panel

qa-report:
	@mkdir -p _reports
	@TS="$$(date +%Y%m%d_%H%M%S)"; OUT="_reports/qa_panel_$$TS.txt"; \
	echo "== QA Panel $(BASE_URL) — $$(date)"            > "$$OUT"; \
	echo ""                                             >> "$$OUT"; \
	echo "[DB] Tamaño por sesión (100..119, top 5)"     >> "$$OUT"; \
	$(SQL) "$(DB_SRC)" "SELECT sesion_id, COUNT(*) n, ROUND(AVG(tr_ms),1) tr FROM tlt_respuesta WHERE sesion_id BETWEEN 100 AND 119 GROUP BY sesion_id ORDER BY sesion_id LIMIT 5;" >> "$$OUT"; \
	echo ""                                             >> "$$OUT"; \
	echo "[DB] Resumen por CCP (100..119)"             >> "$$OUT"; \
	$(SQL) "$(DB_SRC)" "SELECT ccp_code, COUNT(*) n, ROUND(AVG(correcta)*100,1) acierto_pct, ROUND(AVG(tr_ms),1) tr FROM tlt_respuesta WHERE sesion_id BETWEEN 100 AND 119 GROUP BY ccp_code ORDER BY ccp_code;" >> "$$OUT"; \
	echo "" >> "$$OUT"; \
	echo "[BENCH] /panel/metrics (JSON,5)" >> "$$OUT"; \
	for i in 1 2 3 4 5; do curl -s -o /dev/null -w '%{time_total}\n' -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" "$(BASE_URL)/panel/metrics"; done | tee -a "$$OUT" | python3 -c 'import sys;v=[float(x) for x in sys.stdin];print(f"AVG: {sum(v)/len(v)*1000:.3f} ms")' >> "$$OUT"; \
	echo "" >> "$$OUT"; \
	echo "[BENCH] /panel/metrics?format=csv (5)" >> "$$OUT"; \
	for i in 1 2 3 4 5; do curl -s -o /dev/null -w '%{time_total}\n' -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" "$(BASE_URL)/panel/metrics?format=csv"; done | tee -a "$$OUT" | python3 -c 'import sys;v=[float(x) for x in sys.stdin];print(f"AVG: {sum(v)/len(v)*1000:.3f} ms")' >> "$$OUT"; \
	echo "→ Reporte: $$OUT"

# --------------- Health & Seguridad ---------------
db-health:
	@echo "==> PRAGMA integrity_check"
	@$(SQL) "$(DB_SRC)" "PRAGMA integrity_check;"
	@echo "==> PRAGMA foreign_keys"
	@$(SQL) "$(DB_SRC)" "PRAGMA foreign_keys;"
	@echo "==> Vistas del panel"
	@$(SQL) "$(DB_SRC)" "SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'v_panel_metrics%';"
	@echo "==> Tamaño tlt_respuesta"
	@$(SQL) "$(DB_SRC)" "SELECT COUNT(*) AS n FROM tlt_respuesta;"

db-vacuum:
	@echo "==> VACUUM + ANALYZE + PRAGMA optimize"
	@$(SQL) "$(DB_SRC)" "VACUUM;"
	@$(SQL) "$(DB_SRC)" "ANALYZE;"
	@$(SQL) "$(DB_SRC)" "PRAGMA optimize;"
	@echo "→ Compactación y estadísticas actualizadas."

panel-contract:
	@echo "==> Validación shape JSON de /panel/metrics"
	@curl -s -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" "$(BASE_URL)/panel/metrics" \
	| jq -e '. | has("sessions") and (.sessions|type=="array")' >/dev/null \
	&& echo "OK: top-level.sessions[]" || (echo "FAIL: shape inesperado"; exit 1)
	@echo "==> Comprobación de campos esperados en una sesión"
	@curl -s -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" "$(BASE_URL)/panel/metrics" \
	| jq -e '.sessions[0] | has("sesion_id") and has("ccp") and has("totals")' >/dev/null \
	&& echo "OK: sesion_id/ccp/totals presentes" || (echo "FAIL: faltan claves"; exit 1)

panel-security:
	@echo "==> Sin token"
	@code=$$(curl -s -o /dev/null -w '%{http_code}' "$(BASE_URL)/panel/metrics"); \
	test "$$code" = "401" -o "$$code" = "403" && echo "OK: $$code sin token" || (echo "FAIL: esperado 401/403, got $$code"; exit 1)
	@echo "==> Token incorrecto"
	@code=$$(curl -s -H "X-Panel-Token: WRONG" -o /dev/null -w '%{http_code}' "$(BASE_URL)/panel/metrics"); \
	test "$$code" = "401" -o "$$code" = "403" && echo "OK: $$code con token inválido" || (echo "FAIL: esperado 401/403, got $$code"; exit 1)
	@echo "==> Token correcto"
	@code=$$(curl -s -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" -o /dev/null -w '%{http_code}' "$(BASE_URL)/panel/metrics"); \
	test "$$code" = "200" && echo "OK: 200 con token válido" || (echo "FAIL: esperado 200, got $$code"; exit 1)

csv-validate:
	@echo "==> Validación CSV"
	@h=$$(curl -s -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" "$(BASE_URL)/panel/metrics?format=csv" | head -n1 | tr -d '\r'); \
	echo "Header: $$h"; \
	exp='sesion_id,ccp_code,n,aciertos,acierto_pct,tr_ms_avg,first_ts,last_ts'; \
	[ "$$h" = "$$exp" ] && echo "OK: cabecera esperada" || (echo "FAIL: cabecera inesperada"; exit 1)
	@rows=$$(curl -s -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" "$(BASE_URL)/panel/metrics?format=csv" | tr -d '\r' | wc -l | tr -d ' '); \
	test "$$rows" -ge 2 && echo "OK: $$rows líneas (>=2)" || (echo "FAIL: CSV vacío"; exit 1)

# --------------- Benchmark concurrente ---------------
bench-concurrent:
	@N=$${N:-40}; P=$${P:-8}; echo "==> Benchmark concurrente: N=$$N, P=$$P"; \
	seq 1 $$N | xargs -P $$P -I{} \
	curl -s -o /dev/null -w '%{time_total}\n' -H "X-Panel-Token: $(PANEL_ORIENTADOR_TOKEN)" "$(BASE_URL)/panel/metrics" \
	| python3 -c 'import sys; v=[float(x) for x in sys.stdin.read().split()]; v.sort(); p=lambda q:int((len(v)-1)*q); print(f"avg: {sum(v)/len(v)*1000:.2f} ms · p95: {v[p(0.95)]*1000:.2f} · p99: {v[p(0.99)]*1000:.2f} · n={len(v)}")'

# --------------- Pipeline de saneo rápido ---------------
sanitize: preflight-clean clean-bak release release-check
