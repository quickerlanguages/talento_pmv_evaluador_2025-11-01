-- runtime/sql/panel_fixtures_EXTENDED.sql
-- =========================================
-- 🔹 Datos de prueba para M6 – QA y rendimiento del Panel Orientador
--    Crea 5 sesiones completas (~40 registros)

DELETE FROM tlt_respuesta WHERE sesion_id BETWEEN 10 AND 14;

INSERT INTO tlt_respuesta (sesion_id, ccp_code, ejer_code, item_id, correcta, tr_ms, created_at)
VALUES
-- Sesión 10: velocidad de procesamiento (VPM)
(10,'VPM','VPM_CFANT_S','demo_vpm_001',1,480,'2025-10-16 09:00:00'),
(10,'VPM','VPM_CFANT_S','demo_vpm_002',0,620,'2025-10-16 09:00:30'),
(10,'VPM','VPM_CFANT_S','demo_vpm_003',1,510,'2025-10-16 09:01:00'),
(10,'VPM','VPM_CFANT_S','demo_vpm_004',1,440,'2025-10-16 09:01:30'),
(10,'VPM','VPM_CFANT_S','demo_vpm_005',0,750,'2025-10-16 09:02:00'),

-- Sesión 11: MCP y MDT combinadas
(11,'MCP','MCP_SPAN_B','demo_mcp_001',1,850,'2025-10-17 10:00:00'),
(11,'MCP','MCP_SPAN_B','demo_mcp_002',1,920,'2025-10-17 10:00:40'),
(11,'MDT','MDT_WM_S','demo_mdt_001',0,1150,'2025-10-17 10:01:00'),
(11,'MDT','MDT_WM_S','demo_mdt_002',1,970,'2025-10-17 10:01:40'),
(11,'INH','INH_GO_NOGO','demo_inh_001',1,530,'2025-10-17 10:02:00'),

-- Sesión 12: INH + FM (flexibilidad mental)
(12,'INH','INH_GO_NOGO','inh_demo_001',1,560,'2025-10-18 09:00:00'),
(12,'INH','INH_GO_NOGO','inh_demo_002',0,690,'2025-10-18 09:00:30'),
(12,'INH','INH_GO_NOGO','inh_demo_003',1,520,'2025-10-18 09:01:00'),
(12,'FM','FM_RULE_SHIFT','fm_demo_001',1,1300,'2025-10-18 09:02:00'),
(12,'FM','FM_RULE_SHIFT','fm_demo_002',0,1700,'2025-10-18 09:02:40'),

-- Sesión 13: mezcla completa (simula sesión real)
(13,'VPM','VPM_CFANT_S','vpm_013_001',1,400,'2025-10-19 11:00:00'),
(13,'VPM','VPM_CFANT_S','vpm_013_002',1,390,'2025-10-19 11:00:30'),
(13,'MCP','MCP_SPAN_B','mcp_013_001',1,910,'2025-10-19 11:01:00'),
(13,'MCP','MCP_SPAN_B','mcp_013_002',0,1050,'2025-10-19 11:01:30'),
(13,'MDT','MDT_WM_S','mdt_013_001',1,980,'2025-10-19 11:02:00'),
(13,'MDT','MDT_WM_S','mdt_013_002',1,940,'2025-10-19 11:02:30'),
(13,'INH','INH_GO_NOGO','inh_013_001',1,530,'2025-10-19 11:03:00'),
(13,'FM','FM_RULE_SHIFT','fm_013_001',1,1450,'2025-10-19 11:04:00'),

-- Sesión 14: rendimiento prolongado
(14,'VPM','VPM_CFANT_S','vpm_014_001',1,470,'2025-10-20 09:00:00'),
(14,'VPM','VPM_CFANT_S','vpm_014_002',1,490,'2025-10-20 09:00:30'),
(14,'MCP','MCP_SPAN_B','mcp_014_001',1,870,'2025-10-20 09:01:00'),
(14,'MCP','MCP_SPAN_B','mcp_014_002',0,1010,'2025-10-20 09:01:30'),
(14,'MDT','MDT_WM_S','mdt_014_001',1,960,'2025-10-20 09:02:00'),
(14,'MDT','MDT_WM_S','mdt_014_002',1,910,'2025-10-20 09:02:30'),
(14,'INH','INH_GO_NOGO','inh_014_001',1,550,'2025-10-20 09:03:00'),
(14,'FM','FM_RULE_SHIFT','fm_014_001',0,1780,'2025-10-20 09:04:00');
