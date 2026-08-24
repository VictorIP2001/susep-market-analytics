import os
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///susep_analytics.db")
os.makedirs("data_bi", exist_ok=True)

# 1. Fato Seguros
df_fato = pd.read_sql("""
SELECT damesano, coenti, coramo, premio_ganho, sinistro_ocorrido, desp_com
FROM fato_seguros
WHERE damesano >= 202001 AND (premio_ganho > 0 OR sinistro_ocorrido > 0)
""", engine)

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

# 3. Dimensão Ramos - MAPEAMENTO OFICIAL UNIFICADO
ramos_unicos = df_fato[['coramo']].drop_duplicates().copy()

def classificar_linha_oficial(cod):
    c = str(cod).strip()
    if c.startswith(('10', '62', '65', '71')):
        return '04. Rural / Agronegócio'
    if c.startswith(('02', '09', '12', '13', '19', '97', '98', '99', '9')):
        return '02. Vida, Prestamista & Pessoas'
    if c.startswith(('03', '05', '52', '53', '54', '55', '58', '5')):
        return '01. Automóveis & Frotas'
    if c.startswith(('04', '06', '35', '74', '77', '4')):
        return '05. Transportes & Cargas'
    if c.startswith(('07', '7')):
        return '08. Garantia & Fiança'
    if c.startswith(('08', '8')):
        return '07. Habitacional'
    if c.startswith(('23', '31', '37', '2')):
        return '06. Resp. Civil & Linhas Financeiras'
    if c.startswith(('01', '11', '14', '15', '16', '17', '18', '1')):
        return '03. Patrimonial & Residencial'
    return '09. Outros Ramos'

ramos_unicos['linha_negocio'] = ramos_unicos['coramo'].apply(classificar_linha_oficial)
ramos_unicos['nome_ramo'] = 'Ramo ' + ramos_unicos['coramo'].astype(str)
ramos_unicos['status_carteira'] = 'Mercado Ativo'
ramos_unicos['is_run_off'] = 0

# 4. Salvar CSVs
df_fato.to_csv("data_bi/fato_seguros.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
df_cias.to_csv("data_bi/dim_seguradoras.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
ramos_unicos.to_csv("data_bi/dim_ramos.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")

print("✅ Sincronização completa de ramos!")