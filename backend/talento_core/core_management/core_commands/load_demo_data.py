
from django.core.management.base import BaseCommand
from django.db import connection

SQL = r"""
PRAGMA foreign_keys=ON;
BEGIN;
INSERT OR IGNORE INTO ref_parametro_especifico(id_ccp, codigo, nombre, tipo)
SELECT c.id_ccp, 'ventana_presentacion_ms', 'Ventana de presentación (ms)', 'num' FROM ref_ccp c WHERE c.codigo='VPM';
INSERT OR IGNORE INTO ref_parametro_especifico(id_ccp, codigo, nombre, tipo)
SELECT c.id_ccp, 'longitud_lista', 'Longitud de lista', 'num' FROM ref_ccp c WHERE c.codigo='MCP';
INSERT OR IGNORE INTO ref_parametro_especifico(id_ccp, codigo, nombre, tipo)
SELECT c.id_ccp, 'n_back', 'n-back', 'num' FROM ref_ccp c WHERE c.codigo='MDT';
INSERT OR IGNORE INTO ref_parametro_especifico(id_ccp, codigo, nombre, tipo)
SELECT c.id_ccp, 'carga_operaciones', 'Carga de operaciones', 'num' FROM ref_ccp c WHERE c.codigo='MDT';
INSERT OR IGNORE INTO ref_parametro_especifico(id_ccp, codigo, nombre, tipo)
SELECT c.id_ccp, 'proporcion_no_go', 'Proporción No-Go', 'num' FROM ref_ccp c WHERE c.codigo='INH';
INSERT OR IGNORE INTO ref_parametro_especifico(id_ccp, codigo, nombre, tipo)
SELECT c.id_ccp, 'ventana_stop_ms', 'Ventana Stop-Signal (ms)', 'num' FROM ref_ccp c WHERE c.codigo='INH';

-- MDT demo
INSERT INTO item (id_ccp, id_submod, dificultad_ref, n_elementos, tiempo_total_ms, intervalo_ms, layout, payload_json, activo)
SELECT c.id_ccp, NULL, NULL, 20, 60000, 0, 'nback', '{"type":"letters"}', 1
FROM ref_ccp c WHERE c.codigo='MDT';
INSERT INTO item_parametro_especifico (id_item, id_param_esp, valor_num, valor_text)
SELECT (SELECT MAX(id_item) FROM item), p.id_param_esp, 2, NULL
FROM ref_parametro_especifico p JOIN ref_ccp c ON c.id_ccp=p.id_ccp WHERE c.codigo='MDT' AND p.codigo='n_back';
INSERT INTO item_parametro_especifico (id_item, id_param_esp, valor_num, valor_text)
SELECT (SELECT MAX(id_item) FROM item), p.id_param_esp, 1, NULL
FROM ref_parametro_especifico p JOIN ref_ccp c ON c.id_ccp=p.id_ccp WHERE c.codigo='MDT' AND p.codigo='carga_operaciones';

INSERT INTO item (id_ccp, id_submod, dificultad_ref, n_elementos, tiempo_total_ms, intervalo_ms, layout, payload_json, activo)
SELECT c.id_ccp, NULL, NULL, 25, 60000, 0, 'nback', '{"type":"digits"}', 1
FROM ref_ccp c WHERE c.codigo='MDT';
INSERT INTO item_parametro_especifico (id_item, id_param_esp, valor_num, valor_text)
SELECT (SELECT MAX(id_item) FROM item), p.id_param_esp, 3, NULL
FROM ref_parametro_especifico p JOIN ref_ccp c ON c.id_ccp=p.id_ccp WHERE c.codigo='MDT' AND p.codigo='n_back';
INSERT INTO item_parametro_especifico (id_item, id_param_esp, valor_num, valor_text)
SELECT (SELECT MAX(id_item) FROM item), p.id_param_esp, 2, NULL
FROM ref_parametro_especifico p JOIN ref_ccp c ON c.id_ccp=p.id_ccp WHERE c.codigo='MDT' AND p.codigo='carga_operaciones';

-- INH demo
INSERT INTO item (id_ccp, id_submod, dificultad_ref, n_elementos, tiempo_total_ms, intervalo_ms, layout, payload_json, activo)
SELECT c.id_ccp, NULL, NULL, 60, 60000, 0, 'gonogo', '{"type":"shapes"}', 1
FROM ref_ccp c WHERE c.codigo='INH';
INSERT INTO item_parametro_especifico (id_item, id_param_esp, valor_num, valor_text)
SELECT (SELECT MAX(id_item) FROM item), p.id_param_esp, 0.4, NULL
FROM ref_parametro_especifico p JOIN ref_ccp c ON c.id_ccp=p.id_ccp WHERE c.codigo='INH' AND p.codigo='proporcion_no_go';

INSERT INTO item (id_ccp, id_submod, dificultad_ref, n_elementos, tiempo_total_ms, intervalo_ms, layout, payload_json, activo)
SELECT c.id_ccp, NULL, NULL, 60, 60000, 0, 'stopsignal', '{"type":"letters"}', 1
FROM ref_ccp c WHERE c.codigo='INH';
INSERT INTO item_parametro_especifico (id_item, id_param_esp, valor_num, valor_text)
SELECT (SELECT MAX(id_item) FROM item), p.id_param_esp, 250, NULL
FROM ref_parametro_especifico p JOIN ref_ccp c ON c.id_ccp=p.id_ccp WHERE c.codigo='INH' AND p.codigo='ventana_stop_ms';

COMMIT;
"""

class Command(BaseCommand):
    help = "Carga datos demo para MDT/INH y garantiza parámetros específicos mínimos."
    def handle(self, *args, **kwargs):
        with connection.cursor() as cur:
            for statement in SQL.split(';'):
                st = statement.strip()
                if not st:
                    continue
                cur.execute(st + ';')
        self.stdout.write(self.style.SUCCESS("Demo MDT/INH cargado."))
