import os
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///susep_analytics.db")
os.makedirs("data_bi", exist_ok=True)

print("🚀 Exportando dados otimizados para o Power BI...")

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
df_cias = pd.read_sql("SELECT coenti, noenti AS nome_seguradora FROM dim_seguradoras", engine)

def mapear_grupo(nome):
    n = str(nome).upper()
    if 'BRADESCO' in n: return 'GRUPO BRADESCO SEGUROS'
    if any(k in n for k in ['PORTO SEGURO', 'AZUL COMPANHIA', 'ITAÚ SEGUROS', 'ITAU SEGUROS']): return 'GRUPO PORTO / ITAÚ'
    if any(k in n for k in ['BRASILSEG', 'BB SEGUR', 'BRASILVEÍCULOS']): return 'GRUPO BB SEGUROS (BRASILSEG)'
    if 'MAPFRE' in n: return 'GRUPO MAPFRE'
    if 'TOKIO MARINE' in n: return 'GRUPO TOKIO MARINE'
    if 'ZURICH' in n: return 'GRUPO ZURICH'
    if 'ALLIANZ' in n: return 'GRUPO ALLIANZ'
    if any(k in n for k in ['SUL AMÉRICA', 'SULAMERICA']): return 'GRUPO SULAMÉRICA'
    if 'CAIXA' in n: return 'GRUPO CAIXA SEGURIDADE'
    return nome

df_cias['grupo_economico'] = df_cias['nome_seguradora'].apply(mapear_grupo)

# 3. Dimensão Ramos com todas as colunas esperadas pelo Power Query
ramos_unicos = df_fato[['coramo']].drop_duplicates().copy()

def classificar_linha(cod):
    c = str(cod).strip()
    if c.startswith('5') or c.startswith('05') or c.startswith('53') or c.startswith('55') or c.startswith('54') or c.startswith('58') or c.startswith('52'):
        return '01. Automóveis & Frotas'
    if c.startswith('9') or c.startswith('09') or c.startswith('19') or c.startswith('97') or c.startswith('98') or c.startswith('13') or c.startswith('99') or c.startswith('12'):
        return '02. Vida, Prestamista & Pessoas'
    if c.startswith('1') or c.startswith('01') or c.startswith('11') or c.startswith('14') or c.startswith('15') or c.startswith('16') or c.startswith('17') or c.startswith('18'):
        return '03. Patrimonial & Residencial'
    if c.startswith('10') or c.startswith('62') or c.startswith('65') or c.startswith('71'):
        return '04. Rural / Agronegócio'
    if c.startswith('4') or c.startswith('04') or c.startswith('74') or c.startswith('77') or c.startswith('35'):
        return '05. Transportes & Cargas'
    if c.startswith('2') or c.startswith('02') or c.startswith('31') or c.startswith('37') or c.startswith('23'):
        return '06. Resp. Civil & Linhas Financeiras'
    if c.startswith('8') or c.startswith('08'):
        return '07. Habitacional'
    if c.startswith('7') or c.startswith('07'):
        return '08. Garantia & Fiança'
    return '09. Outros Ramos'

ramos_unicos['linha_negocio'] = ramos_unicos['coramo'].apply(classificar_linha)
ramos_unicos['nome_ramo'] = 'Ramo ' + ramos_unicos['coramo'].astype(str)
ramos_unicos['status_carteira'] = 'Mercado Ativo'
ramos_unicos['is_run_off'] = 0
df_ramos = ramos_unicos

# 4. Salvar arquivos
df_fato.to_csv("data_bi/fato_seguros.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
df_cias.to_csv("data_bi/dim_seguradoras.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
df_ramos.to_csv("data_bi/dim_ramos.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")

print("✅ Arquivos atualizados com todas as colunas mantidas!")