# === Talento • M4 • Integridad referencial ===
# Variables esperadas:
# DB ?= ./talento_READY_2025-09-14.db
# PGURL ?= postgres://user:pass@localhost:5432/talento

.PHONY: m4-integridad-sqlite m4-integridad-pg m4-integridad-qa

m4-integridad-sqlite: ## Aplica integridad en SQLite
	@echo "[M4] SQLite integridad referencial"
	sqlite3 "$(DB)" "PRAGMA foreign_keys=ON;"
	sqlite3 "$(DB)" ".read sqlite_integridad_m4.sql"
	@$(MAKE) m4-integridad-qa

m4-integridad-pg: ## Aplica integridad en PostgreSQL
	@echo "[M4] PostgreSQL integridad referencial"
	psql "$(PGURL)" -v ON_ERROR_STOP=1 -f postgres_integridad_m4.sql
	@$(MAKE) m4-integridad-qa

m4-integridad-qa: ## QA: huérfanos y consistencia
	@echo "[M4][QA] SQLite (si DB definido)"
	-@[ -f "$(DB)" ] && sqlite3 "$(DB)" "PRAGMA foreign_keys=ON; PRAGMA foreign_key_check; PRAGMA integrity_check;" || echo "Saltando SQLite QA (DB no definido)"
	@echo "[M4][QA] PostgreSQL (si PGURL definido)"
	-@[ -n "$(PGURL)" ] && psql "$(PGURL)" -v ON_ERROR_STOP=1 -c "\
WITH checks AS (\
  SELECT 'tlt_respuesta->tlt_sesion' rel, COUNT(*) n FROM tlt_respuesta r LEFT JOIN tlt_sesion s ON s.id=r.sesion_id WHERE s.id IS NULL \
  UNION ALL SELECT 'tlt_respuesta->tlt_item', COUNT(*) FROM tlt_respuesta r LEFT JOIN tlt_item i ON i.id=r.item_id WHERE i.id IS NULL \
  UNION ALL SELECT 'tlt_item->tlt_ccp', COUNT(*) FROM tlt_item i LEFT JOIN tlt_ccp c ON c.code=i.ccp_code WHERE c.code IS NULL \
  UNION ALL SELECT 'tlt_item_element->tlt_item', COUNT(*) FROM tlt_item_element ie LEFT JOIN tlt_item it ON it.id=ie.item_id WHERE it.id IS NULL \
  UNION ALL SELECT 'tlt_item_element->tlt_elemento', COUNT(*) FROM tlt_item_element ie LEFT JOIN tlt_elemento el ON el.id=ie.elemento_id WHERE el.id IS NULL \
  UNION ALL SELECT 'tlt_sesion_item->tlt_sesion', COUNT(*) FROM tlt_sesion_item si LEFT JOIN tlt_sesion s ON s.id=si.sesion_id WHERE s.id IS NULL \
  UNION ALL SELECT 'tlt_sesion_item->tlt_item', COUNT(*) FROM tlt_sesion_item si LEFT JOIN tlt_item it ON it.id=si.item_id WHERE it.id IS NULL ) SELECT * FROM checks;" \
	|| echo "Saltando PostgreSQL QA (PGURL no definido)"
