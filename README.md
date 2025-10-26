# Talento — PMV Evaluador (M9)
Demo local con dos apps Flask: `play-ui` (evaluador) y `panel-ui` (panel).

## Arranque rápido
make init
BACKEND_DB="$PWD/backend/talento_READY_2025-09-14.db" \
  make dev-up
# Evaluador: http://127.0.0.1:5101  (o 5001)
# Panel:     http://127.0.0.1:5102  (o 5002)

## Ingesta desde el panel
curl -s -X POST "http://127.0.0.1:<panel_port>/admin/ingest?token=pmv-local" | jq .
