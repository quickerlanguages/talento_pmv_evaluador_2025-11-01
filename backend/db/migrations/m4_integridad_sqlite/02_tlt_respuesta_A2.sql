PRAGMA foreign_keys=ON;
BEGIN;
INSERT INTO tlt_respuesta_new (id,sesion_id,ccp_code,ejer_code,item_id,respuesta,correcta,tr_ms,created_at)
SELECT id,sesion_id,ccp_code,ejer_code,item_id,respuesta,correcta,tr_ms,created_at
FROM tlt_respuesta
WHERE sesion_id IN (SELECT id FROM tlt_sesion)
  AND (correcta IS NULL OR correcta IN (0,1))
  AND (tr_ms IS NULL OR tr_ms >= 0);
COMMIT;
