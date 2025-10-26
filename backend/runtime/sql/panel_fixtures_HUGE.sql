-- runtime/sql/panel_fixtures_HUGE.sql
-- ===================================
-- 🔥 Dataset sintético ~1000 filas para estrés de /panel/metrics
--   - Sesiones: 100..119 (20 sesiones)
--   - 50 items por sesión → 1000 items
--   - CCP: VPM / MCP / MDT / INH / FM (reparto cíclico)
--   - correcta: ~66% (determinista por patrón), + pequeñas variaciones
--   - tr_ms: base por CCP + jitter
--   - created_at: incrementos de minutos desde 2025-10-01 09:00

PRAGMA foreign_keys = OFF;

DELETE FROM tlt_respuesta WHERE sesion_id BETWEEN 100 AND 119;

WITH RECURSIVE seq(n) AS (
  SELECT 0
  UNION ALL
  SELECT n+1 FROM seq WHERE n < 999
),
base AS (
  SELECT
    n,
    (100 + (n / 50))                    AS sesion_id,          -- 50 items por sesión
    CASE (n % 5)
      WHEN 0 THEN 'VPM'
      WHEN 1 THEN 'MCP'
      WHEN 2 THEN 'MDT'
      WHEN 3 THEN 'INH'
      ELSE        'FM'
    END                                 AS ccp_code,
    CASE (n % 5)
      WHEN 0 THEN 'VPM_CFANT_S'
      WHEN 1 THEN 'MCP_SPAN_B'
      WHEN 2 THEN 'MDT_WM_S'
      WHEN 3 THEN 'INH_GO_NOGO'
      ELSE        'FM_RULE_SHIFT'
    END                                 AS ejer_code,
    -- ~66% acierto: todo menos múltiplos de 3. Metemos ligera variación con random()
    CASE WHEN (n % 3) != 0 OR (abs(random()) % 7) IN (1,2) THEN 1 ELSE 0 END AS correcta,
    -- tr_ms por CCP con jitter (200–1900ms según modalidad)
    CASE (n % 5)
      WHEN 0 THEN 350 + (abs(random()) % 300)      -- VPM: 350–649
      WHEN 1 THEN 800 + (abs(random()) % 400)      -- MCP: 800–1199
      WHEN 2 THEN 850 + (abs(random()) % 450)      -- MDT: 850–1299
      WHEN 3 THEN 450 + (abs(random()) % 250)      -- INH: 450–699
      ELSE        1200 + (abs(random()) % 700)     -- FM: 1200–1899
    END                                 AS tr_ms,
    -- Timestamps espaciados por minuto
    datetime('2025-10-01 09:00:00', printf('+%d minutes', n)) AS created_at,
    -- item_id único reproducible
    printf('huge_%04d', n)              AS item_id
  FROM seq
)
INSERT INTO tlt_respuesta (sesion_id, ccp_code, ejer_code, item_id, correcta, tr_ms, created_at)
SELECT sesion_id, ccp_code, ejer_code, item_id, correcta, tr_ms, created_at
FROM base;

-- Sugerencia tras carga (lo hará el Make): ANALYZE/optimize
