# Talento PMV Evaluador — M9 (Flask)  ·  Makefile “premium”
SHELL := /bin/bash
.ONESHELL:

ROOT_DIR := $(shell pwd)

# --- Configuración base ---
PY ?= /opt/homebrew/bin/python3.14
VENV    := .venv
PIP     := $(VENV)/bin/pip
PYBIN   := $(VENV)/bin/python

BACKEND_DIR ?= $(ROOT_DIR)/backend
BACKEND_DB  ?= $(BACKEND_DIR)/talento_READY_2025-09-14.db

PLAY_HOST ?= 127.0.0.1
PLAY_PORT ?= 5001
PANEL_HOST ?= 127.0.0.1
PANEL_PORT ?= 5002

# --- Artefactos de distribución ---
DIST_NAME ?= talento_pmv_evaluador_2025-11-01
ZIP       ?= $(DIST_NAME).clean.zip
EXCLUDE   ?= exclude.lst

# ZIP reproducible (mismo hash si no cambian contenidos)
ZIPFLAGS ?= -X -D
export SOURCE_DATE_EPOCH ?= 1700000000

# Carpetas de salida de “release”
RELEASE_DIR ?= $(HOME)/Releases/Talento
RELEASE_NOTES_PREFIX ?= RELEASE_NOTES
PROMOTE_DIR ?= $(HOME)/Releases/Talento/Final

# --- Herramientas necesarias (se validan en check-tools) ---
REQUIRED_TOOLS := zip zipinfo shasum sqlite3 curl jq lsof git

# --- Ayuda general ---
.PHONY: help
help:
	@echo "Targets:"
	@echo "  init                  → Crear venv e instalar dependencias"
	@echo "  run-evaluator         → Lanza play-ui (Flask) en $(PLAY_HOST):$(PLAY_PORT)"
	@echo "  run-panel             → Lanza panel-ui (Flask) en $(PANEL_HOST):$(PANEL_PORT)"
	@echo "  export-session        → Comprime data/sessions a data/exports/<ts>.zip"
	@echo "  ingest-sessions       → Ingesta JSONL → SQLite (usa BACKEND_DB)"
	@echo "  panel-refresh         → ANALYZE/PRAGMA optimize en BACKEND_DB"
	@echo "  purge-session SESION= → Borra respuestas de una sesión"
	@echo "  migrate-pmv-index     → Crea índice único en tlt_respuesta"
	@echo "  panel-admin-*         → Acciones remotas (ingest/purge/reindex)"
	@echo "  dev-up|dev-status|dev-logs|dev-down → Supervisor simple"
	@echo "  verify-exclude        → Comprueba patrones mínimos en exclude.lst"
	@echo "  pmv-package           → ZIP rápido del PMV (no reproducible, legacy)"
	@echo "  dist                  → Genera ZIP limpio reproducible + SHA256SUMS.txt"
	@echo "  dist-check            → Escaneo de archivos prohibidos dentro del ZIP"
	@echo "  dist-list             → Lista el contenido del ZIP"
	@echo "  dist-show-hash        → Muestra el hash actual del ZIP"
	@echo "  dist-verify           → Verifica SHA256SUMS.txt"
	@echo "  dist-clean            → Elimina ZIP y SHA"
	@echo "  release               → Copia ZIP+SHA a $(RELEASE_DIR) y crea notas"
	@echo "  release-promote       → Copia artefactos a $(PROMOTE_DIR)"
	@echo "  bump-version          → Actualiza VERSION con DIST_NAME y commitea"
	@echo "  tag-release           → Crea tag git anotado con SHA del ZIP"
	@echo "  smoke                 → Arranca → healthcheck → para (endpoints /health)"
	@echo "  qa-dryrun / qa-all    → Pipeline QA (verificaciones + release)"

# --- Utilidades ---
.PHONY: check-tools print-vars clean
check-tools:
	@missing=0; \
	for t in $(REQUIRED_TOOLS); do \
	  command -v $$t >/dev/null 2>&1 || { echo "✖ Falta herramienta: $$t"; missing=1; }; \
	done; \
	[ $$missing -eq 0 ] || { echo "Aborta: instala las herramientas anteriores."; exit 1; }

print-vars:
	@echo "ROOT_DIR    = $(ROOT_DIR)"
	@echo "BACKEND_DIR = $(BACKEND_DIR)"
	@echo "BACKEND_DB  = $(BACKEND_DB)"
	@echo "PLAY        = $(PLAY_HOST):$(PLAY_PORT)"
	@echo "PANEL       = $(PANEL_HOST):$(PANEL_PORT)"
	@echo "DIST_NAME   = $(DIST_NAME)"
	@echo "ZIP         = $(ZIP)"
	@echo "EXCLUDE     = $(EXCLUDE)"
	@echo "RELEASE_DIR = $(RELEASE_DIR)"
	@echo "PROMOTE_DIR = $(PROMOTE_DIR)"

clean:
	rm -rf __pycache__ */__pycache__ .pytest_cache .venv

# --- Setup entorno ---
.PHONY: init
init:
	$(PY) -m venv $(VENV)
	$(PIP) install -U pip wheel
	$(PIP) install -r requirements.txt

# --- Run locales ---
.PHONY: run-evaluator run-panel export-session
run-evaluator: .venv
	BACKEND_DB="$(BACKEND_DB)" $(PYBIN) play-ui/app_play.py --host $(PLAY_HOST) --port $(PLAY_PORT)

run-panel: .venv
	BACKEND_DB="$(BACKEND_DB)" $(PYBIN) panel-ui/app_panel.py --host $(PANEL_HOST) --port $(PANEL_PORT)

export-session:
	@mkdir -p data/exports
	@ts=$$(date +%Y%m%d_%H%M%S); out="data/exports/sessions_$$ts.zip"; \
	zip -r "$$out" data/sessions >/dev/null; echo "→ $$out"

# --- Mantenimiento de datos ---
.PHONY: ingest-sessions panel-refresh purge-session migrate-pmv-index
ingest-sessions: .venv
	@BACKEND_DB="$(BACKEND_DB)" $(PYBIN) scripts/ingest_jsonl_to_sqlite.py

panel-refresh:
	@sqlite3 "$(BACKEND_DB)" "ANALYZE; PRAGMA optimize;" >/dev/null || true
	@echo "→ panel views refrescadas"

purge-session:
	@[ -n "$(SESION)" ] || (echo "Uso: make purge-session SESION=<id>"; exit 1)
	@sqlite3 "$(BACKEND_DB)" "DELETE FROM tlt_respuesta WHERE sesion_id=$(SESION);" && echo "→ purged $(SESION)"

migrate-pmv-index:
	@sqlite3 "$(BACKEND_DB)" "CREATE UNIQUE INDEX IF NOT EXISTS idx_tlt_resp_unique ON tlt_respuesta (sesion_id, ejer_code, item_id);"
	@echo "→ Índice único creado/ya existente"

# --- Panel admin remoto ---
.PHONY: panel-admin-ingest panel-admin-purge panel-admin-reindex
PANEL_URL ?= http://127.0.0.1:5002
PANEL_ADMIN_TOKEN ?= pmv-local

panel-admin-ingest:
	@curl -s -X POST "$(PANEL_URL)/admin/ingest?token=$(PANEL_ADMIN_TOKEN)" | jq .

panel-admin-purge:
	@[ -n "$(SESION)" ] || (echo "Uso: make panel-admin-purge SESION=<id>"; exit 1)
	@curl -s -X POST "$(PANEL_URL)/admin/purge?token=$(PANEL_ADMIN_TOKEN)&sesion=$(SESION)" | jq .

panel-admin-reindex:
	@curl -s -X POST "$(PANEL_URL)/admin/reindex?token=$(PANEL_ADMIN_TOKEN)" | jq .

# --- Verificación de exclude.lst ------------------------
.PHONY: verify-exclude
verify-exclude:
	@need="\\.env \\.db \\*.sqlite backend/staticfiles backend/runtime/sql data/sessions logs"; \
	miss=0; \
	for p in $$need; do \
	  grep -Eq "$$p" "$(EXCLUDE)" || { echo "✖ Falta patrón en $(EXCLUDE): $$p"; miss=1; }; \
	done; \
	[ $$miss -eq 0 ] && echo "✔ exclude.lst cubre patrones mínimos"

# --- Empaquetado legacy (opcional) ---
.PHONY: pmv-package
pmv-package:
	@TS="$$(date +%Y-%m-%d_%H%M%S)"; OUT="talento_pmv_evaluador_$$TS.zip"; \
	echo "→ Empaquetando $$OUT"; \
	zip -r "$$OUT" \
	  backend panel-ui play-ui scripts data docs Makefile VERSION \
	  -x "*/.venv/*" "*/__pycache__/*" "*.pyc" "*.pyo" "data/exports/*" >/dev/null; \
	echo "  OK: $$OUT"; shasum -a 256 "$$OUT"

# --- Dev supervisor (una sola terminal) ---
.PHONY: dev-up dev-down dev-status dev-logs
LOG_DIR ?= logs

define check_port
	@! lsof -iTCP:$(1) -sTCP:LISTEN -n -P >/dev/null 2>&1 || \
	 (echo "✖ Puerto $(1) en uso. Para el proceso o cambia el puerto (PLAY_PORT/PANEL_PORT)." && exit 1)
endef

dev-up:
	@mkdir -p $(LOG_DIR)
	$(call check_port,$(PLAY_PORT))
	$(call check_port,$(PANEL_PORT))
	@echo "→ arrancando play-ui en background..."
	@BACKEND_DB="$(BACKEND_DB)" nohup .venv/bin/python play-ui/app_play.py \
	  --host $(PLAY_HOST) --port $(PLAY_PORT) > $(LOG_DIR)/play-ui.log 2>&1 & echo $$! > .play.pid
	@echo "→ arrancando panel-ui en background..."
	@PANEL_ADMIN_TOKEN="$(PANEL_ADMIN_TOKEN)" BACKEND_DB="$(BACKEND_DB)" \
	  nohup .venv/bin/python panel-ui/app_panel.py \
	  --host $(PANEL_HOST) --port $(PANEL_PORT) > $(LOG_DIR)/panel-ui.log 2>&1 & echo $$! > .panel.pid
	@echo "OK: play-ui http://$(PLAY_HOST):$(PLAY_PORT) · panel http://$(PANEL_HOST):$(PANEL_PORT)"
	@$(MAKE) dev-status

dev-status:
	@echo "— STATUS —"
	@if [ -f .play.pid ] && ps -p $$(cat .play.pid) > /dev/null 2>&1; then \
	  ps -p $$(cat .play.pid) -o pid,comm,args | awk '{print "play: " $$0}'; \
	else \
	  if lsof -nP -iTCP:$(PLAY_PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
	    echo "play: running (no pidfile)"; \
	    lsof -nP -iTCP:$(PLAY_PORT) -sTCP:LISTEN | awk 'NR==1{print "    "$$0} NR>1{print "    "$$0}'; \
	  else echo "play: stopped"; fi; \
	fi
	@if [ -f .panel.pid ] && ps -p $$(cat .panel.pid) > /dev/null 2>&1; then \
	  ps -p $$(cat .panel.pid) -o pid,comm,args | awk '{print "panel: " $$0}'; \
	else \
	  if lsof -nP -iTCP:$(PANEL_PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
	    echo "panel: running (no pidfile)"; \
	    lsof -nP -iTCP:$(PANEL_PORT) -sTCP:LISTEN | awk 'NR==1{print "    "$$0} NR>1{print "    "$$0}'; \
	  else echo "panel: stopped"; fi; \
	fi
	@echo "Logs: tail -f $(LOG_DIR)/play-ui.log $(LOG_DIR)/panel-ui.log"

dev-logs:
	@tail -f $(LOG_DIR)/play-ui.log $(LOG_DIR)/panel-ui.log

dev-down:
	@echo "→ parando servicios..."
	@[ -f .play.pid ]  && kill $$(cat .play.pid)  2>/dev/null || true
	@[ -f .panel.pid ] && kill $$(cat .panel.pid) 2>/dev/null || true
	@rm -f .play.pid .panel.pid
	@echo "OK: servicios detenidos"

# --- Smoke tests / Healthchecks -------------------------
.PHONY: smoke-up smoke-health smoke-down smoke
HEALTH_RETRIES ?= 30
HEALTH_SLEEP   ?= 0.5

smoke-up: dev-up

smoke-health:
	@echo "→ comprobando salud play-ui y panel-ui"
	@ok=0; \
	for i in $$(seq 1 $(HEALTH_RETRIES)); do \
	  c1=$$(curl -s -o /dev/null -w "%{http_code}" "http://$(PLAY_HOST):$(PLAY_PORT)/health" || true); \
	  c2=$$(curl -s -o /dev/null -w "%{http_code}" "http://$(PANEL_HOST):$(PANEL_PORT)/health" || true); \
	  if [ "$$c1" = "200" ] && [ "$$c2" = "200" ]; then ok=1; break; fi; \
	  sleep $(HEALTH_SLEEP); \
	done; \
	[ $$ok -eq 1 ] || (echo "✖ healthcheck falló (play=$$c1, panel=$$c2)"; exit 1); \
	echo "✔ health OK (play=$(PLAY_HOST):$(PLAY_PORT), panel=$(PANEL_HOST):$(PANEL_PORT))"

smoke-down: dev-down

smoke: smoke-up smoke-health smoke-down
	@echo "✔ smoke test OK"

# --- Dist: ZIP limpio reproducible + SHA ---
.PHONY: dist dist-check dist-list dist-show-hash dist-verify dist-clean
dist: check-tools $(EXCLUDE)
	@test -f $(EXCLUDE) || (echo "✖ Falta $(EXCLUDE)"; exit 1)
	@rm -f ../$(ZIP) ../SHA256SUMS.txt
	@zip -r $(ZIPFLAGS) ../$(ZIP) . -x@$(EXCLUDE)
	@( cd .. && shasum -a 256 $(ZIP) > SHA256SUMS.txt )
	@echo "Hecho: ../$(ZIP) y ../SHA256SUMS.txt"

dist-check:
	@test -f ../$(ZIP) || (echo "✖ No existe ../$(ZIP). Ejecuta: make dist"; exit 1)
	@zipinfo -1 ../$(ZIP) | egrep '\.pid$$|(^|/)\.coverage$$|\.db|\.sqlite|(^|/)\.env($$|\.local$$)' && \
	  (echo "✖ Encontrado algo prohibido"; exit 1) || echo "✔ ZIP limpio"

dist-list:
	@test -f ../$(ZIP) || (echo "✖ No existe ../$(ZIP). Ejecuta: make dist"; exit 1)
	@zipinfo -1 ../$(ZIP) | sed -n '1,200p'

dist-show-hash:
	@test -f ../$(ZIP) || (echo "✖ No existe ../$(ZIP). Ejecuta: make dist"; exit 1)
	@( cd .. && shasum -a 256 $(ZIP) )

dist-verify:
	@test -f ../SHA256SUMS.txt || (echo "✖ No existe ../SHA256SUMS.txt"; exit 1)
	@( cd .. && shasum -a 256 -c SHA256SUMS.txt )

dist-clean:
	@rm -f ../$(ZIP) ../SHA256SUMS.txt

# --- Release: copiar artefactos y generar notas ---
.PHONY: release release-promote
release: dist dist-check
	@mkdir -p "$(RELEASE_DIR)"
	@cp -f ../$(ZIP) ../SHA256SUMS.txt "$(RELEASE_DIR)/"
	@ts=$$(date +%Y-%m-%d_%H%M%S); \
	hash=$$(cd .. && shasum -a 256 $(ZIP) | awk '{print $$1}'); \
	notes="$(RELEASE_DIR)/$(RELEASE_NOTES_PREFIX)_$${ts}.md"; \
	{ \
	  echo "# Talento PMV Evaluador — Release $${ts}"; \
	  echo ""; \
	  echo "- Artefacto: $(ZIP)"; \
	  echo "- SHA256: $${hash}"; \
	  echo "- Origen: $(ROOT_DIR)"; \
	  echo ""; \
	  echo "## Verificación"; \
	  echo "\`shasum -a 256 -c SHA256SUMS.txt\` → OK"; \
	} > "$${notes}"; \
	echo "Release generado en $(RELEASE_DIR) (notas: $${notes})"

release-promote: release
	@mkdir -p "$(PROMOTE_DIR)"
	@cp -f ../$(ZIP) ../SHA256SUMS.txt "$(PROMOTE_DIR)/"
	@echo "✔ promovido a $(PROMOTE_DIR)"

# --- Version bump & tagging -----------------------------
.PHONY: bump-version tag-release
bump-version:
	@echo "$(DIST_NAME)" > VERSION
	@git add VERSION
	@git commit -m "chore: bump VERSION -> $(DIST_NAME)" || true
	@echo "✔ VERSION actualizado a $(DIST_NAME)"

# --- Tag idempotente ---------------------------------------------
.PHONY: tag-release
tag-release: dist-verify
	@TAG="rel/$(DIST_NAME)"; \
	if git rev-parse "$$TAG" >/dev/null 2>&1; then \
	  echo "✔ tag $$TAG ya existe (ok)"; \
	else \
	  ZIP_SHA=$$(awk '{print $$1}' ../SHA256SUMS.txt); \
	  git tag -a "$$TAG" -m "Release $(DIST_NAME) (zip SHA256=$$ZIP_SHA)"; \
	  echo "✔ tag $$TAG creado"; \
	fi

# --- QA pipeline (one-shot) ---
.PHONY: qa-all qa-dryrun
qa-all: check-tools dist verify-exclude dist-check dist-verify release
	@echo ""
	@echo "———————————————— QA DONE ————————————————"
	@echo "ZIP          : ../$(ZIP)"
	@echo "SHA256SUMS   : ../SHA256SUMS.txt"
	@echo "Release dir  : $(RELEASE_DIR)"
	@echo "Verificación : (cd .. && shasum -a 256 -c SHA256SUMS.txt) → OK"
	@echo "—————————————————————————————————————————"

qa-dryrun: check-tools
	@test -f $(EXCLUDE) || (echo "✖ Falta $(EXCLUDE)"; exit 1)
	@echo "✔ Entorno OK. Listo para 'make qa-all'"

# --- Quality of life targets -----------------------------------------------
.PHONY: doctor dist-size clean-logs git-push-tags dist-open

doctor: check-tools print-vars
	@echo "✔ Entorno OK"

dist-size:
	@test -f ../$(ZIP) || (echo "✖ No existe ../$(ZIP). Ejecuta: make dist"; exit 1)
	@du -h ../$(ZIP)

clean-logs:
	@rm -f logs/*.log .play.pid .panel.pid 2>/dev/null || true
	@echo "✔ logs y pidfiles limpiados"

git-push-tags:
	@git push || true
	@git push --tags || true
	@echo "✔ commits y tags enviados"

dist-open:
	@open .. || true

.PHONY: release-gh
release-gh: check-tools dist-check dist-verify
	@scripts/release_gh.sh
	
.PHONY: doctor-make
doctor-make:
	@echo "make path: $$(command -v make)"
	@make --version || true