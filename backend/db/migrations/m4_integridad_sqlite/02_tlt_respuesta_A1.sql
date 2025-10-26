PRAGMA foreign_keys=ON;
BEGIN;
CREATE TABLE IF NOT EXISTS tlt_respuesta_new(
  id INTEGER PRIMARY KEY,
  sesion_id INTEGER NOT NULL,
  ccp_code TEXT,
  ejer_code TEXT,
  item_id TEXT,
  respuesta TEXT,
  correcta INTEGER,
  tr_ms INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (sesion_id) REFERENCES tlt_sesion(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CHECK (correcta IS NULL OR correcta IN (0,1)),
  CHECK (tr_ms IS NULL OR tr_ms >= 0)
);
COMMIT;
