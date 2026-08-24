import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///susep_analytics.db")

# CTE reutilizável para padronizar os grupos econômicos
CASE_GRUPOS = """
    CASE 
        WHEN c.noenti LIKE '%BRADESCO%' THEN 'GRUPO BRADESCO SEGUROS'
        WHEN c.noenti LIKE '%PORTO SEGURO%' OR c.noenti LIKE '%AZUL COMPANHIA%' OR c.noenti LIKE '%ITAÚ SEGUROS%' OR c.noenti LIKE '%ITAU SEGUROS%' THEN 'GRUPO PORTO / ITAÚ'
        WHEN c.noenti LIKE '%BRASILSEG%' OR c.noenti LIKE '%BB SEGUR%' OR c.noenti LIKE '%BRASILVEÍCULOS%' THEN 'GRUPO BB SEGUROS (BRASILSEG)'
        WHEN c.noenti LIKE '%MAPFRE%' THEN 'GRUPO MAPFRE'
        WHEN c.noenti LIKE '%TOKIO MARINE%' THEN 'GRUPO TOKIO MARINE'
        WHEN c.noenti LIKE '%ZURICH%' THEN 'GRUPO ZURICH'
        WHEN c.noenti LIKE '%ALLIANZ%' THEN 'GRUPO ALLIANZ'
        WHEN c.noenti LIKE '%SUL AMÉRICA%' OR c.noenti LIKE '%SULAMERICA%' THEN 'GRUPO SULAMÉRICA'
        WHEN c.noenti LIKE '%CAIXA%' THEN 'GRUPO CAIXA SEGURIDADE'
        ELSE c.noenti
    END
"""

print("="*90)
print("🏆 QUERY 1: RANKING POR CONGLOMERADO / GRUPO ECONÔMICO REAL")
print("="*90)
q1 = f"""
WITH base_agrupada AS (
    SELECT 
        {CASE_GRUPOS} AS grupo_economico,
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
print("🛡️ QUERY 2: CONSOLIDAÇÃO POR LINHA DE NEGÓCIO (SUSEP)")
print("\n" + "="*90)
print("🛡️ QUERY 2: CONSOLIDAÇÃO POR LINHA DE NEGÓCIO (SUSEP) - FONTE ÚNICA")
print("="*90)
q2 = """
SELECT 
    r.linha_negocio,
    ROUND(SUM(f.premio_ganho) / 1e9, 2) AS premio_bi,
    ROUND(SUM(f.sinistro_ocorrido) / 1e9, 2) AS sinistro_bi,
    ROUND((SUM(f.sinistro_ocorrido) * 1.0 / NULLIF(SUM(f.premio_ganho), 0)) * 100, 1) AS loss_ratio_pct,
    CASE 
        WHEN (SUM(f.sinistro_ocorrido) * 1.0 / NULLIF(SUM(f.premio_ganho), 0)) > 0.50 THEN 'Alerta (Sinistralidade Elevada)'
        WHEN (SUM(f.sinistro_ocorrido) * 1.0 / NULLIF(SUM(f.premio_ganho), 0)) BETWEEN 0.30 AND 0.50 THEN 'Equilibrado'
        ELSE 'Alta Rentabilidade'
    END AS status_operacional
FROM fato_seguros f
JOIN dim_ramos r ON f.coramo = r.coramo
WHERE f.premio_ganho > 0
GROUP BY r.linha_negocio
ORDER BY premio_bi DESC;
"""
print(pd.read_sql(q2, engine).to_string(index=False))
print("📈 QUERY 3: EVOLUÇÃO MENSAL E CRESCIMENTO MoM (Recente)")
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
q4 = f"""
SELECT 
    {CASE_GRUPOS} AS grupo_economico,
    ROUND(SUM(f.premio_ganho) / 1e9, 2) AS premio_bi,
    ROUND(SUM(f.sinistro_ocorrido) / 1e9, 2) AS sinistro_bi,
    ROUND((SUM(f.sinistro_ocorrido) * 1.0 / NULLIF(SUM(f.premio_ganho), 0)) * 100, 1) AS loss_ratio_pct,
    ROUND(SUM(f.desp_com) / 1e9, 2) AS despesas_comerciais_bi
FROM fato_seguros f
JOIN dim_seguradoras c ON f.coenti = c.coenti
WHERE f.damesano >= 202201
GROUP BY 1
HAVING SUM(f.premio_ganho) > 1000000000
ORDER BY premio_bi DESC
LIMIT 6;
"""
print(pd.read_sql(q4, engine).to_string(index=False))