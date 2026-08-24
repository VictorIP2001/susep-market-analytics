import os
import pandas as pd
from sqlalchemy import create_engine

print("🚀 Iniciando pipeline de ETL dos dados da SUSEP...")

# Caminho base dos arquivos
BASE_PATH = os.path.join("data", "BaseCompleta")

# 1. Conexão com o banco SQLite local
engine = create_engine("sqlite:///susep_analytics.db")

def limpar_monetario(serie):
    """Converte números formatados no padrão BR (ex: 1.234,56) para float."""
    return (
        serie.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0.0)
    )

# ----------------------------------------------------
# 1. Processar Dimensão Seguradoras (Ses_cias.csv)
# ----------------------------------------------------
print("📥 Processando Seguradoras (Ses_cias.csv)...")
df_cias = pd.read_csv(os.path.join(BASE_PATH, "Ses_cias.csv"), sep=";", encoding="latin1", low_memory=False)
# Padronizar nomes das colunas em minúsculo
df_cias.columns = [c.strip().lower() for c in df_cias.columns]
df_cias.to_sql("dim_seguradoras", engine, if_exists="replace", index=False)
print(f"✅ Dimensão Seguradoras salva ({len(df_cias)} registros).")

# ----------------------------------------------------
# 2. Processar Dimensão Ramos (Ses_ramos.csv)
# ----------------------------------------------------
print("📥 Processando Ramos de Seguros (Ses_ramos.csv)...")
df_ramos = pd.read_csv(os.path.join(BASE_PATH, "Ses_ramos.csv"), sep=";", encoding="latin1", low_memory=False)
df_ramos.columns = [c.strip().lower() for c in df_ramos.columns]
df_ramos.to_sql("dim_ramos", engine, if_exists="replace", index=False)
print(f"✅ Dimensão Ramos salva ({len(df_ramos)} registros).")

# ----------------------------------------------------
# 3. Processar Grupos de Ramos (ses_gruposramos.csv)
# ----------------------------------------------------
if os.path.exists(os.path.join(BASE_PATH, "ses_gruposramos.csv")):
    print("📥 Processando Grupos de Ramos (ses_gruposramos.csv)...")
    df_grupos = pd.read_csv(os.path.join(BASE_PATH, "ses_gruposramos.csv"), sep=";", encoding="latin1", low_memory=False)
    df_grupos.columns = [c.strip().lower() for c in df_grupos.columns]
    df_grupos.to_sql("dim_grupos_ramos", engine, if_exists="replace", index=False)
    print(f"✅ Dimensão Grupos de Ramos salva ({len(df_grupos)} registros).")

# ----------------------------------------------------
# 4. Processar Fato Movimento Seguros (Ses_seguros.csv)
# ----------------------------------------------------
print("📥 Processando Fato Seguros (Ses_seguros.csv)... Isso pode levar alguns segundos.")
df_seguros = pd.read_csv(os.path.join(BASE_PATH, "Ses_seguros.csv"), sep=";", encoding="latin1", low_memory=False)
df_seguros.columns = [c.strip().lower() for c in df_seguros.columns]

# Limpar valores numéricos de todas as colunas que não são IDs/Datas
cols_ignorar = ['co_cia', 'co_ramo', 'dt_competencia', 'co_grupo_ramo', 'co_uf']
cols_numericas = [c for c in df_seguros.columns if c not in cols_ignorar]

for col in cols_numericas:
    df_seguros[col] = limpar_monetario(df_seguros[col])

# Tratar data de competência (AAAAMM -> AAAA-MM-01)
if 'dt_competencia' in df_seguros.columns:
    df_seguros['dt_competencia_str'] = df_seguros['dt_competencia'].astype(str)
    df_seguros['ano'] = df_seguros['dt_competencia_str'].str[:4].astype(int)
    df_seguros['mes'] = df_seguros['dt_competencia_str'].str[4:6].astype(int)

df_seguros.to_sql("fato_seguros", engine, if_exists="replace", index=False, chunksize=10000)
print(f"✅ Fato Seguros salva com sucesso ({len(df_seguros):,} linhas) no banco SQLite!")

print("\n🎉 ETL CONCLUÍDO COM SUCESSO! O arquivo 'susep_analytics.db' foi gerado.")