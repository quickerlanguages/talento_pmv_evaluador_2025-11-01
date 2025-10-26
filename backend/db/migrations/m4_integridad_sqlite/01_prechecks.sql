PRAGMA foreign_keys=ON;
BEGIN;
.print 'ORPHANS (previos)'
SELECT COUNT(*) AS orphan_respuesta_sesion FROM tlt_respuesta r LEFT JOIN tlt_sesion s ON s.id=r.sesion_id WHERE s.id IS NULL;
SELECT COUNT(*) AS orphan_respuesta_item   FROM tlt_respuesta r LEFT JOIN tlt_item   i ON i.id=r.item_id   WHERE i.id IS NULL;
SELECT COUNT(*) AS orphan_sesion_item_sesion FROM tlt_sesion_item si LEFT JOIN tlt_sesion s ON s.id=si.sesion_id WHERE s.id IS NULL;
SELECT COUNT(*) AS orphan_sesion_item_item   FROM tlt_sesion_item si LEFT JOIN tlt_item   it ON it.id=si.item_id WHERE it.id IS NULL;
SELECT COUNT(*) AS orphan_item_ccp FROM tlt_item i LEFT JOIN tlt_ccp c ON c.code=i.ccp_code WHERE c.code IS NULL;
SELECT COUNT(*) AS orphan_item_element_item FROM tlt_item_element ie LEFT JOIN tlt_item it ON it.id=ie.item_id WHERE it.id IS NULL;
SELECT COUNT(*) AS orphan_item_element_elemento FROM tlt_item_element ie LEFT JOIN tlt_elemento el ON el.id=ie.elemento_id WHERE el.id IS NULL;
COMMIT;
