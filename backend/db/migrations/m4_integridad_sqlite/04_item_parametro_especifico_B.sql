PRAGMA foreign_keys=ON;
BEGIN;
DROP TABLE IF EXISTS item_parametro_especifico;
ALTER TABLE item_parametro_especifico_new RENAME TO item_parametro_especifico;
COMMIT;
CREATE UNIQUE INDEX IF NOT EXISTS ux_item_param_esp
ON item_parametro_especifico(id_item, id_param_esp);
