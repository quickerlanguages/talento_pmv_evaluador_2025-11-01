PRAGMA foreign_keys=ON;
BEGIN;
DROP TABLE IF EXISTS tlt_respuesta;
ALTER TABLE tlt_respuesta_new RENAME TO tlt_respuesta;
COMMIT;
