import os
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///susep_analytics.db")
os.makedirs("data_bi", exist_ok=True)

print("🚀 Exportando dados consolidados para o Power BI...")

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

# 3. Dimensão Ramos (Garante que TODOS os ramos da FATO existam na DIMENSÃO)
ramos_unicos = df_fato[['coramo']].drop_duplicates().copy()

def classificar_linha_oficial(cod):
    c = str(cod).strip().zfill(4)
    if c.startswith(('10', '62', '65', '71')):
        return '04. Rural / Agronegócio'
    if c.startswith(('02', '09', '12', '13', '19', '97', '98', '99')):
        return '02. Vida, Prestamista & Pessoas'
    if c.startswith(('03', '05', '52', '53', '54', '55', '58')):
        return '01. Automóveis & Frotas'
    if c.startswith(('04', '06', '35', '74', '77')):
        return '05. Transportes & Cargas'
    if c.startswith('07'):
        return '08. Garantia & Fiança'
    if c.startswith('08'):
        return '07. Habitacional'
    if c.startswith(('23', '31', '37')):
        return '06. Resp. Civil & Linhas Financeiras'
    if c.startswith(('01', '11', '14', '15', '16', '17', '18')):
        return '03. Patrimonial & Residencial'
    return '09. Outros Ramos'

ramos_unicos['linha_negocio'] = ramos_unicos['coramo'].apply(classificar_linha_oficial)
ramos_unicos['nome_ramo'] = 'Ramo ' + ramos_unicos['coramo'].astype(str)
ramos_unicos['status_carteira'] = 'Mercado Ativo'
ramos_unicos['is_run_off'] = 0

# 4. Salvar arquivos CSV
df_fato.to_csv("data_bi/fato_seguros.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
df_cias.to_csv("data_bi/dim_seguradoras.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
ramos_unicos.to_csv("data_bi/dim_ramos.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")

print("✅ CSVs exportados com sucesso sem ramos nulos/em branco!")