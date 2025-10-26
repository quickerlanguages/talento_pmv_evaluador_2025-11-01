PRAGMA foreign_keys=ON;
BEGIN;
CREATE TABLE IF NOT EXISTS item_parametro_especifico_new(
  id_item      INTEGER NOT NULL,
  id_param_esp INTEGER NOT NULL,
  valor_num    REAL,
  valor_text   TEXT,
  FOREIGN KEY (id_item) REFERENCES item(id_item) ON DELETE CASCADE
);
INSERT INTO item_parametro_especifico_new (id_item,id_param_esp,valor_num,valor_text)
SELECT id_item,id_param_esp,valor_num,valor_text
FROM item_parametro_especifico
WHERE id_item IN (SELECT id_item FROM item);
COMMIT;
