import os
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///susep_analytics.db")
os.makedirs("data_bi", exist_ok=True)

print("🚀 Exportando dados dimensionais consolidados para o Power BI...")

# 1. Fato Seguros (Competência >= 2020)
query_fato = """
SELECT 
    damesano,
    coenti,
    coramo,
    premio_ganho,
    sinistro_ocorrido,
    desp_com
FROM fato_seguros
WHERE damesano >= 202001
  AND (premio_ganho > 0 OR sinistro_ocorrido > 0)
"""
df_fato = pd.read_sql(query_fato, engine)
df_fato['damesano_str'] = df_fato['damesano'].astype(str)
df_fato['data_competencia'] = pd.to_datetime(df_fato['damesano_str'] + '01', format='%Y%m%d', errors='coerce')
df_fato = df_fato.drop(columns=['damesano_str'])

# 2. Dimensão Seguradoras
df_cias = pd.read_sql("""
SELECT 
    coenti, 
    noenti AS nome_seguradora, 
    grupo_economico 
FROM dim_seguradoras
""", engine)

# 3. Dimensão Ramos (Tratamento dinâmico do nome do ramo)
df_ramos_raw = pd.read_sql("SELECT * FROM dim_ramos", engine)

col_nome = [c for c in df_ramos_raw.columns if 'ram' in c and c != 'coramo']
if col_nome:
    df_ramos_raw['nome_ramo'] = df_ramos_raw[col_nome[0]].fillna('Ramo ' + df_ramos_raw['coramo'].astype(str))
else:
    df_ramos_raw['nome_ramo'] = 'Ramo ' + df_ramos_raw['coramo'].astype(str)

df_ramos = df_ramos_raw[['coramo', 'nome_ramo', 'linha_negocio']].drop_duplicates().copy()
df_ramos['status_carteira'] = 'Mercado Ativo'
df_ramos['is_run_off'] = 0

# 4. Salvar arquivos CSV
df_fato.to_csv("data_bi/fato_seguros.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
df_cias.to_csv("data_bi/dim_seguradoras.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
df_ramos.to_csv("data_bi/dim_ramos.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")

print("✅ CSVs exportados com sucesso com base na fonte única de verdade (SSOT)!")