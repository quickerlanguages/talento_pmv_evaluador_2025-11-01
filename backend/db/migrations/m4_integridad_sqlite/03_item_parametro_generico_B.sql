PRAGMA foreign_keys=ON;
BEGIN;
DROP TABLE IF EXISTS item_parametro_generico;
ALTER TABLE item_parametro_generico_new RENAME TO item_parametro_generico;
COMMIT;
