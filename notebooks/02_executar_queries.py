import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///susep_analytics.db")

print("="*90)
print("🏆 QUERY 1: RANKING POR CONGLOMERADO / GRUPO ECONÔMICO REAL")
print("="*90)
q1 = """
WITH base_agrupada AS (
    SELECT 
        c.grupo_economico,
        f.premio_ganho,
        f.sinistro_ocorrido
    FROM fato_seguros f
    JOIN dim_seguradoras c ON f.coenti = c.coenti
    WHERE f.premio_ganho > 0
),
total_geral AS (
    SELECT SUM(premio_ganho) AS total_mercado FROM base_agrupada
),
consolidador AS (
    SELECT 
        grupo_economico,
        SUM(premio_ganho) AS total_premio,
        SUM(sinistro_ocorrido) AS total_sinistro,
        ROUND((SUM(sinistro_ocorrido) * 1.0 / NULLIF(SUM(premio_ganho), 0)) * 100, 1) AS loss_ratio_pct
    FROM base_agrupada
    GROUP BY grupo_economico
)
SELECT 
    c.grupo_economico,
    ROUND(c.total_premio / 1e9, 2) AS premio_bi,
    ROUND(c.total_sinistro / 1e9, 2) AS sinistro_bi,
    c.loss_ratio_pct,
    ROUND((c.total_premio * 100.0 / t.total_mercado), 2) AS market_share_pct
FROM consolidador c
CROSS JOIN total_geral t
ORDER BY c.total_premio DESC
LIMIT 8;
"""
print(pd.read_sql(q1, engine).to_string(index=False))

print("\n" + "="*90)
print("🛡️ QUERY 2: CONSOLIDAÇÃO POR LINHA DE NEGÓCIO (SUSEP) - FONTE ÚNICA")
print("="*90)
q2 = """
WITH fato_categorizada AS (
    SELECT 
        premio_ganho,
        sinistro_ocorrido,
        CASE 
            WHEN PRINTF('%04d', coramo) LIKE '10%' OR PRINTF('%04d', coramo) LIKE '62%' OR PRINTF('%04d', coramo) LIKE '65%' OR PRINTF('%04d', coramo) LIKE '71%' THEN '04. Rural / Agronegócio'
            WHEN PRINTF('%04d', coramo) LIKE '02%' OR PRINTF('%04d', coramo) LIKE '09%' OR PRINTF('%04d', coramo) LIKE '12%' OR PRINTF('%04d', coramo) LIKE '13%' OR PRINTF('%04d', coramo) LIKE '19%' OR PRINTF('%04d', coramo) LIKE '97%' OR PRINTF('%04d', coramo) LIKE '98%' OR PRINTF('%04d', coramo) LIKE '99%' THEN '02. Vida, Prestamista & Pessoas'
            WHEN PRINTF('%04d', coramo) LIKE '03%' OR PRINTF('%04d', coramo) LIKE '05%' OR PRINTF('%04d', coramo) LIKE '52%' OR PRINTF('%04d', coramo) LIKE '53%' OR PRINTF('%04d', coramo) LIKE '54%' OR PRINTF('%04d', coramo) LIKE '55%' OR PRINTF('%04d', coramo) LIKE '58%' THEN '01. Automóveis & Frotas'
            WHEN PRINTF('%04d', coramo) LIKE '04%' OR PRINTF('%04d', coramo) LIKE '06%' OR PRINTF('%04d', coramo) LIKE '35%' OR PRINTF('%04d', coramo) LIKE '74%' OR PRINTF('%04d', coramo) LIKE '77%' THEN '05. Transportes & Cargas'
            WHEN PRINTF('%04d', coramo) LIKE '07%' THEN '08. Garantia & Fiança'
            WHEN PRINTF('%04d', coramo) LIKE '08%' THEN '07. Habitacional'
            WHEN PRINTF('%04d', coramo) LIKE '23%' OR PRINTF('%04d', coramo) LIKE '31%' OR PRINTF('%04d', coramo) LIKE '37%' THEN '06. Resp. Civil & Linhas Financeiras'
            WHEN PRINTF('%04d', coramo) LIKE '01%' OR PRINTF('%04d', coramo) LIKE '11%' OR PRINTF('%04d', coramo) LIKE '14%' OR PRINTF('%04d', coramo) LIKE '15%' OR PRINTF('%04d', coramo) LIKE '16%' OR PRINTF('%04d', coramo) LIKE '17%' OR PRINTF('%04d', coramo) LIKE '18%' THEN '03. Patrimonial & Residencial'
            ELSE '09. Outros Ramos'
        END AS linha_negocio
    FROM fato_seguros
    WHERE premio_ganho > 0
)
SELECT 
    linha_negocio,
    ROUND(SUM(premio_ganho) / 1e9, 2) AS premio_bi,
    ROUND(SUM(sinistro_ocorrido) / 1e9, 2) AS sinistro_bi,
    ROUND((SUM(sinistro_ocorrido) * 1.0 / NULLIF(SUM(premio_ganho), 0)) * 100, 1) AS loss_ratio_pct,
    CASE 
        WHEN (SUM(sinistro_ocorrido) * 1.0 / NULLIF(SUM(premio_ganho), 0)) > 0.50 THEN 'Alerta (Sinistralidade Elevada)'
        WHEN (SUM(sinistro_ocorrido) * 1.0 / NULLIF(SUM(premio_ganho), 0)) BETWEEN 0.30 AND 0.50 THEN 'Equilibrado'
        ELSE 'Alta Rentabilidade'
    END AS status_operacional
FROM fato_categorizada
GROUP BY linha_negocio
ORDER BY premio_bi DESC;
"""
print(pd.read_sql(q2, engine).to_string(index=False))

print("\n" + "="*90)
print("📈 QUERY 3: EVOLUÇÃO MENSAL E CRESCIMENTO MoM")
print("="*90)
q3 = """
WITH mensal AS (
    SELECT 
        damesano,
        SUM(premio_ganho) AS premio_mes,
        SUM(sinistro_ocorrido) AS sinistro_mes
    FROM fato_seguros
    WHERE damesano >= 202301
    GROUP BY damesano
)
SELECT 
    damesano AS ano_mes,
    ROUND(premio_mes / 1e9, 2) AS premio_bi,
    ROUND((sinistro_mes * 1.0 / NULLIF(premio_mes, 0)) * 100, 1) AS loss_ratio_pct,
    ROUND(((premio_mes - LAG(premio_mes) OVER (ORDER BY damesano)) * 100.0) / NULLIF(LAG(premio_mes) OVER (ORDER BY damesano), 0), 2) AS crescimento_mom_pct
FROM mensal
ORDER BY damesano DESC
LIMIT 6;
"""
print(pd.read_sql(q3, engine).to_string(index=False))

print("\n" + "="*90)
print("🎯 QUERY 4: MATRIZ DE EFICIÊNCIA POR GRUPO ECONÔMICO")
print("="*90)
q4 = """
SELECT 
    c.grupo_economico,
    ROUND(SUM(f.premio_ganho) / 1e9, 2) AS premio_bi,
    ROUND(SUM(f.sinistro_ocorrido) / 1e9, 2) AS sinistro_bi,
    ROUND((SUM(f.sinistro_ocorrido) * 1.0 / NULLIF(SUM(f.premio_ganho), 0)) * 100, 1) AS loss_ratio_pct,
    ROUND(SUM(f.desp_com) / 1e9, 2) AS despesas_comerciais_bi
FROM fato_seguros f
JOIN dim_seguradoras c ON f.coenti = c.coenti
WHERE f.damesano >= 202201
GROUP BY c.grupo_economico
HAVING SUM(f.premio_ganho) > 1000000000
ORDER BY premio_bi DESC
LIMIT 6;
"""
print(pd.read_sql(q4, engine).to_string(index=False))