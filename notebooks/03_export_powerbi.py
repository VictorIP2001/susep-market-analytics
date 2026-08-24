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

# 3. Dimensão Ramos com a ordem de precedência corrigida
ramos_unicos = df_fato[['coramo']].drop_duplicates().copy()

def classificar_linha(cod):
    c = str(cod).strip()
    
    # 1. Prefixos específicos de 2 dígitos PRIMEIRO
    if c.startswith(('10', '62', '65', '71')):
        return '04. Rural / Agronegócio'
    if c.startswith(('13', '12', '19', '97', '98', '99', '09', '9')):
        return '02. Vida, Prestamista & Pessoas'
    if c.startswith(('53', '55', '54', '58', '52', '05', '5')):
        return '01. Automóveis & Frotas'
    if c.startswith(('74', '77', '35', '04', '4')):
        return '05. Transportes & Cargas'
    if c.startswith(('31', '37', '23', '02', '2')):
        return '06. Resp. Civil & Linhas Financeiras'
    if c.startswith(('08', '8')):
        return '07. Habitacional'
    if c.startswith(('07', '7')):
        return '08. Garantia & Fiança'
        
    # 2. Prefixos genéricos de Patrimonial por ÚLTIMO (para não engolir o 10, 12, 13)
    if c.startswith(('01', '11', '14', '15', '16', '17', '18', '1')):
        return '03. Patrimonial & Residencial'
        
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

print("✅ Arquivos atualizados com todas as colunas mantidas e precedência de ramos corrigida!")