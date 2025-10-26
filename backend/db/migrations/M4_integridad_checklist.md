# Talento • M4 • Integridad referencial – Checklist de ejecución

**Antes de empezar**
- [ ] Backup de la base de datos (SQLite/PG).
- [ ] Ventana de mantenimiento (si aplica).

## SQLite
1. [ ] `PRAGMA foreign_keys=ON;`
2. [ ] `sqlite3 "$DB" ".read sqlite_integridad_m4.sql"`
3. [ ] Ver resultados de `PRAGMA foreign_key_check;` y `PRAGMA integrity_check;` (ambos deben salir `ok`).
4. [ ] Smoke `/api/answer` con un POST de ejemplo (correcta=1, tr_ms=999).
5. [ ] Revisar `v_score_ccp_session` y endpoints `/smoke/`, `/smoke-ui/`.

## PostgreSQL
1. [ ] `psql "$PGURL" -v ON_ERROR_STOP=1 -f postgres_integridad_m4.sql`
2. [ ] Confirmar 0 filas en el bloque QA (relaciones con `COUNT(*)`).
3. [ ] `VACUUM ANALYZE` (si procede) y `REINDEX` opcional en tablas afectadas.
4. [ ] Smoke `/api/answer` y vistas de agregación.

## Datos problemáticos (si los hubiera)
- [ ] Si hay huérfanos listados por las consultas previas:
  - [ ] Decidir si **eliminar** huérfanos o **insertar** padres faltantes.
  - [ ] Re-ejecutar script hasta 0 incidencias.

## Post
- [ ] subir cambios al repo: `postgres_integridad_m4.sql`, `sqlite_integridad_m4.sql`, y snippet de `Makefile`.
- [ ] Registrar en `README_MILESTONES.md` que la integridad M4 está “ON”.

## Notas
- Este paquete asume tablas: `tlt_usuario`, `tlt_sesion`, `tlt_ccp`, `tlt_item`, `tlt_item_param`, `tlt_elemento`, `tlt_item_element`, `tlt_sesion_item`, `tlt_respuesta`, `tlt_metrica`, `tlt_score`.
- Si tus nombres difieren, **buscar y reemplazar** en ambos SQL antes de aplicar.
