-- ====================================================================
-- PROJETO SUSEP: 4 QUERIES ANALÍTICAS DE MERCADO E SINISTRALIDADE
-- ====================================================================

-- --------------------------------------------------------------------
-- QUERY 1: Ranking Nacional das Top 10 Seguradoras & Market Share
-- Técnicas: Window Functions (DENSE_RANK), CTEs, Subquery de Total
-- --------------------------------------------------------------------
WITH total_geral AS (
    SELECT SUM(premio_ganho) AS total_premio_mercado 
    FROM fato_seguros 
    WHERE premio_ganho > 0
),
metricas_por_grupo AS (
    SELECT 
        COALESCE(c.nogrupo, c.noenti) AS grupo_ou_seguradora,
        SUM(f.premio_ganho) AS total_premio_ganho,
        SUM(f.sinistro_ocorrido) AS total_sinistros,
        ROUND((SUM(f.sinistro_ocorrido) * 1.0 / NULLIF(SUM(f.premio_ganho), 0)) * 100, 2) AS loss_ratio_pct
    FROM fato_seguros f
    JOIN dim_seguradoras c ON f.coenti = c.coenti
    WHERE f.premio_ganho > 0
    GROUP BY COALESCE(c.nogrupo, c.noenti)
)
SELECT 
    m.grupo_ou_seguradora,
    ROUND(m.total_premio_ganho / 1e9, 2) AS premio_ganho_bi,
    ROUND(m.total_sinistros / 1e9, 2) AS sinistros_bi,
    m.loss_ratio_pct,
    ROUND((m.total_premio_ganho * 100.0 / t.total_premio_mercado), 2) AS market_share_pct,
    DENSE_RANK() OVER (ORDER BY m.total_premio_ganho DESC) AS ranking_mercado
FROM metricas_por_grupo m
CROSS JOIN total_geral t
ORDER BY m.total_premio_ganho DESC
LIMIT 10;


-- --------------------------------------------------------------------
-- QUERY 2: Diagnóstico de Rentabilidade e Risco por Ramo de Seguro
-- Técnicas: Classificação condicional (CASE WHEN), Agrupamento Categórico
-- --------------------------------------------------------------------
SELECT 
    r.noramo AS nome_ramo,
    ROUND(SUM(f.premio_ganho) / 1e9, 2) AS premio_ganho_bi,
    ROUND(SUM(f.sinistro_ocorrido) / 1e9, 2) AS sinistros_bi,
    ROUND((SUM(f.premio_ganho) - SUM(f.sinistro_ocorrido)) / 1e9, 2) AS margem_tecnica_bi,
    ROUND((SUM(f.sinistro_ocorrido) * 1.0 / NULLIF(SUM(f.premio_ganho), 0)) * 100, 2) AS loss_ratio_pct,
    CASE 
        WHEN (SUM(f.sinistro_ocorrido) * 1.0 / NULLIF(SUM(f.premio_ganho), 0)) > 0.75 THEN 'Alto Risco (Crítico)'
        WHEN (SUM(f.sinistro_ocorrido) * 1.0 / NULLIF(SUM(f.premio_ganho), 0)) BETWEEN 0.50 AND 0.75 THEN 'Moderado (Saudável)'
        ELSE 'Alta Rentabilidade'
    END AS status_operacional
FROM fato_seguros f
JOIN dim_ramos r ON f.coramo = r.coramo
GROUP BY r.noramo
HAVING SUM(f.premio_ganho) > 100000000 -- Filtra ramos com mais de R$ 100M arrecadados
ORDER BY premio_ganho_bi DESC
LIMIT 15;


-- --------------------------------------------------------------------
-- QUERY 3: Evolução Mensal & Crescimento MoM (Month-over-Month)
-- Técnicas: Window Function LAG() para comparar mês atual vs. anterior
-- --------------------------------------------------------------------
WITH consolidado_mensal AS (
    SELECT 
        damesano,
        SUM(premio_ganho) AS premio_mes,
        SUM(sinistro_ocorrido) AS sinistro_mes
    FROM fato_seguros
    WHERE damesano >= 202201
    GROUP BY damesano
)
SELECT 
    damesano AS ano_mes,
    ROUND(premio_mes / 1e9, 2) AS premio_ganho_bi,
    ROUND(sinistro_mes / 1e9, 2) AS sinistro_bi,
    ROUND((sinistro_mes * 1.0 / NULLIF(premio_mes, 0)) * 100, 2) AS loss_ratio_pct,
    -- Cálculo de crescimento em relação ao mês anterior
    ROUND(
        ((premio_mes - LAG(premio_mes) OVER (ORDER BY damesano)) * 100.0) 
        / NULLIF(LAG(premio_mes) OVER (ORDER BY damesano), 0), 
        2
    ) AS crescimento_premio_mom_pct
FROM consolidado_mensal
ORDER BY damesano;


-- --------------------------------------------------------------------
-- QUERY 4: Matriz de Eficiência das Companhias (Base do Gráfico de Dispersão)
-- Técnicas: Filtros de corte temporal e cálculo de rentabilidade agregada
-- --------------------------------------------------------------------
SELECT 
    c.noenti AS seguradora,
    ROUND(SUM(f.premio_ganho) / 1e9, 2) AS total_premio_bi,
    ROUND(SUM(f.sinistro_ocorrido) / 1e9, 2) AS total_sinistro_bi,
    ROUND((SUM(f.sinistro_ocorrido) * 1.0 / NULLIF(SUM(f.premio_ganho), 0)) * 100, 2) AS loss_ratio_pct,
    ROUND(SUM(f.desp_com) / 1e9, 2) AS despesas_comerciais_bi
FROM fato_seguros f
JOIN dim_seguradoras c ON f.coenti = c.coenti
WHERE f.damesano >= 202201
GROUP BY c.noenti
HAVING SUM(f.premio_ganho) > 1000000000 -- Companhias com mais de R$ 1 Bi arrecadado
ORDER BY total_premio_bi DESC;

-- 1. Adiciona a coluna nova na tabela dim_ramos
ALTER TABLE dim_ramos ADD COLUMN is_run_off INTEGER DEFAULT 0;

-- 2. Atualiza os registros que contêm 'RUN OFF'
UPDATE dim_ramos
SET is_run_off = 1
WHERE noramo LIKE '%RUN OFF%' OR noramo LIKE '%RUN-OFF%';