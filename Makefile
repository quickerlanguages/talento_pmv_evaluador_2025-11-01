# Talento PMV Evaluador — M9 (Flask)
SHELL := /bin/bash
ROOT_DIR := $(shell pwd)

# --- Configuración base ---
PY := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYBIN := $(VENV)/bin/python

BACKEND_DIR ?= $(ROOT_DIR)/backend
BACKEND_DB  ?= $(BACKEND_DIR)/talento_READY_2025-09-14.db

PLAY_HOST ?= 127.0.0.1
PLAY_PORT ?= 5001
PANEL_HOST ?= 127.0.0.1
PANEL_PORT ?= 5002

# --- Ayuda general ---
.PHONY: help init run-evaluator run-panel export-session pmv-package clean print-vars

help:
	@echo "Targets:"
	@echo "  init            → Crea venv e instala dependencias"
	@echo "  run-evaluator   → Lanza play-ui (Flask) en $(PLAY_HOST):$(PLAY_PORT)"
	@echo "  run-panel       → Lanza panel-ui (Flask) en $(PANEL_HOST):$(PANEL_PORT)"
	@echo "  export-session  → Comprime data/sessions a data/exports/<ts>.zip"
	@echo "  pmv-package     → Genera ZIP distribuible del PMV"
	@echo "  print-vars      → Muestra rutas/puertos activos"
	@echo "  clean           → Limpia artefactos temporales"

init:
	python3 -m venv $(VENV)
	$(PIP) install -U pip wheel
	$(PIP) install -r requirements.txt

run-evaluator: .venv
	BACKEND_DB="$(BACKEND_DB)" $(PYBIN) play-ui/app_play.py --host $(PLAY_HOST) --port $(PLAY_PORT)

run-panel: .venv
	BACKEND_DB="$(BACKEND_DB)" $(PYBIN) panel-ui/app_panel.py --host $(PANEL_HOST) --port $(PANEL_PORT)

export-session:
	@mkdir -p data/exports
	@ts=$$(date +%Y%m%d_%H%M%S); out="data/exports/sessions_$$ts.zip"; \
	zip -r "$$out" data/sessions >/dev/null; echo "→ $$out"

print-vars:
	@echo "ROOT_DIR   = $(ROOT_DIR)"
	@echo "BACKEND_DIR= $(BACKEND_DIR)"
	@echo "BACKEND_DB = $(BACKEND_DB)"
	@echo "PLAY       = $(PLAY_HOST):$(PLAY_PORT)"
	@echo "PANEL      = $(PANEL_HOST):$(PANEL_PORT)"

clean:
	rm -rf __pycache__ */__pycache__ .pytest_cache .venv

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

# --- Empaquetado PMV ---
pmv-package:
	@TS="$$(date +%Y-%m-%d_%H%M%S)"; OUT="talento_pmv_evaluador_$$TS.zip"; \
	echo "→ Empaquetando $$OUT"; \
	zip -r "$$OUT" \
	  backend panel-ui play-ui scripts data docs Makefile VERSION \
	  -x "*/.venv/*" "*/__pycache__/*" "*.pyc" "*.pyo" "data/exports/*" >/dev/null; \
	echo "  OK: $$OUT"; shasum -a 256 "$$OUT"

# --- Dev supervisor (una sola terminal) ----------------
.PHONY: dev-up dev-down dev-status dev-logs

LOG_DIR ?= logs
PLAY_HOST ?= 127.0.0.1
PLAY_PORT ?= 5001
PANEL_HOST ?= 127.0.0.1
PANEL_PORT ?= 5002
PANEL_ADMIN_TOKEN ?= pmv-local

# Comprueba que un puerto está libre; si no, sale con error
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