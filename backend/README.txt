
Talento Backend Step 10 v2 (Django + SQLite)

Pasos:
1) Copia tu BD SQLite a esta carpeta con nombre: talento_READY_2025-09-14.db
   (o export TALENTO_DB_PATH=/ruta/a/tu.db)
2) python3 -m venv .venv && source .venv/bin/activate
3) python3 -m pip install -r requirements.txt
4) python3 manage.py runserver 127.0.0.1:8000

Endpoints:
- GET /api/health
- GET /api/ccp/<ccp>/items
- GET /api/select/vpm?submod=&max_ms=
- GET /api/select/mcp?submod=&target_len=
- GET /api/select/mdt?submod=&n_back=&carga=&dificultad=
- GET /api/select/inh/gonogo?submod=&min_prop=&max_prop=&dificultad=
- GET /api/select/inh/stopsignal?submod=&max_stop_ms=&dificultad=
- POST /api/sesion
- POST /api/respuesta

Datos demo opcionales:
  python3 manage.py load_demo_data
