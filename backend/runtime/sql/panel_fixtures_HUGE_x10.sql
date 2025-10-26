PRAGMA foreign_keys = OFF;
DELETE FROM tlt_respuesta WHERE sesion_id BETWEEN 200 AND 399;

WITH RECURSIVE seq(n) AS (
  SELECT 0 UNION ALL SELECT n+1 FROM seq WHERE n < 9999  -- 10k
),
base AS (
  SELECT
    n,
    (200 + (n / 50)) AS sesion_id,
    CASE (n % 5)
      WHEN 0 THEN 'VPM' WHEN 1 THEN 'MCP' WHEN 2 THEN 'MDT' WHEN 3 THEN 'INH' ELSE 'FM' END AS ccp_code,
    CASE (n % 5)
      WHEN 0 THEN 'VPM_CFANT_S' WHEN 1 THEN 'MCP_SPAN_B' WHEN 2 THEN 'MDT_WM_S' WHEN 3 THEN 'INH_GO_NOGO' ELSE 'FM_RULE_SHIFT' END AS ejer_code,
    CASE WHEN (n % 3) != 0 OR (abs(random()) % 7) IN (1,2) THEN 1 ELSE 0 END AS correcta,
    CASE (n % 5)
      WHEN 0 THEN 350 + (abs(random()) % 300)
      WHEN 1 THEN 800 + (abs(random()) % 400)
      WHEN 2 THEN 850 + (abs(random()) % 450)
      WHEN 3 THEN 450 + (abs(random()) % 250)
      ELSE        1200 + (abs(random()) % 700)
    END AS tr_ms,
    datetime('2025-10-01 09:00:00', printf('+%d seconds', n)) AS created_at,
    printf('hugex10_%05d', n) AS item_id
  FROM seq
)
INSERT INTO tlt_respuesta (sesion_id, ccp_code, ejer_code, item_id, correcta, tr_ms, created_at)
SELECT sesion_id, ccp_code, ejer_code, item_id, correcta, tr_ms, created_at FROM base;
