# Talento — PMV Evaluador (M9)

Este paquete proporciona una versión mínima ejecutable local para:
- **Evaluación** (play-ui): ejecución de pruebas y registro de resultados.
- **Panel** (panel-ui): visualización de métricas locales y exportación.

## Requisitos
- Python 3.9+
- macOS/Windows/Linux
- SQLite (incluido en Python standard library)

## Instalación rápida
```bash
make init
# Copia el backend validado (M8) a ./backend/
# Ej.: cp -R /ruta/a/m7_lts_extract ./backend
make print-vars
```

## Ejecución
En terminales separadas:
```bash
make run-evaluator   # http://127.0.0.1:5001
make run-panel       # http://127.0.0.1:5002
```

## Exportación de sesiones
```bash
make export-session
```

## Empaquetado PMV
```bash
make pmv-package
```

## Variables útiles
- `BACKEND_DB` (por defecto `./backend/talento_READY_2025-09-14.db`)
- `PLAY_HOST`, `PLAY_PORT`
- `PANEL_HOST`, `PANEL_PORT`
