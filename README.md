# Talento — PMV Evaluador (M9)

Demo local con dos apps Flask:
- `play-ui` → evaluador (envía respuestas simuladas a `data/sessions/*.jsonl`)
- `panel-ui` → panel orientador (lee KPIs desde SQLite)

## Requisitos
- Python 3.14 (o 3.11+ probado)  
- macOS/Linux con `make`, `sqlite3`, `curl`, `jq` (opcional para pretty JSON)

## Arranque rápido
```bash
make init
BACKEND_DB="$PWD/backend/talento_READY_2025-09-14.db" make dev-up
# Evaluador: http://127.0.0.1:5001  (o 5101 si cambias el puerto)
# Panel:     http://127.0.0.1:5002  (o 5102)
