# 📊 Panorama do Mercado Segurador Brasileiro | SUSEP Analytics

[![Power BI](https://img.shields.io/badge/PowerBI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![DAX](https://img.shields.io/badge/DAX-Analysis-blue?style=for-the-badge)](https://learn.microsoft.com/pt-br/dax/)

Pipeline de dados end-to-end e dashboard executivo de Business Intelligence desenvolvido para analisar a dinâmica contábil, sinistralidade (*Loss Ratio*) e posicionamento de mercado das seguradoras no Brasil reguladas pela **SUSEP (Superintendência de Seguros Privados)**.

---

## 🖼️ Visão do Dashboard

| Visão Executiva Macro | Raio-X da Seguradora (Drill-Through) |
| :---: | :---: |
| ![Dashboard Overview](dashboard_overview.png) | ![Raio-X Overview](dashboard_raiox.png) |

---

## 🎯 Contexto de Negócio & Objetivos

O projeto consolida dados contábeis oficiais para responder a perguntas estratégicas de diretoria e inteligência de mercado:

1. **Market Share & Concentração:** Identificar quais grupos econômicos dominam a captação de prêmios no país.
2. **Mix de Carteira:** Mapear a representatividade de cada linha de negócio (Vida, Auto, Patrimonial, Rural, Cargas).
3. **Eficiência Técnica (Loss Ratio):** Acompanhar a margem técnica operacional e a sinistralidade por conglomerado.
4. **Auditoria Individual (Drill-Through):** Permitir um diagnóstico sob demanda por player com detalhamento de ramos e sinistros.

> *Nota Técnica: Dados contábeis oficiais regulados pela SUSEP. Não inclui operações de Saúde Suplementar (reguladas pela ANS).*

---

## 🧠 Indicadores & Modelagem DAX

* **Prêmio Ganho:** Volume contábil de prêmio reconhecido após diferimento do prêmio não ganho.
* **Sinistros Ocorridos:** Custo total de indenizações avisadas e liquidadas no período.
* **Loss Ratio (% Sinistralidade):**
  $$\text{Loss Ratio} = \frac{\text{Sinistros Ocorridos}}{\text{Prêmio Ganho}} \times 100$$
  *Resultado consolidado de **44,3%**, indicando rentabilidade técnica saudável.*
* **Market Share % (Dinâmico):**
  $$\text{Market Share} = \frac{\text{Prêmio Ganho (Seguradora)}}{\text{Prêmio Ganho (Total Mercado)}}$$
* **Despesas Comerciais:** Custos de intermediação, agenciamento e comissões de corretagem.

---

## 📊 Principais Insights de Negócio & Mercado Segurador

Com base na consolidação de mais de **1,8 milhão de registros históricos da SUSEP** e no volume de **R$ 1,01 Tri em prêmios ganhos**, destacam-se os seguintes achados:

* **Alta Concentração de Mercado no Top 3:** O *Grupo Porto / Itaú* lidera o market share nacional com ~16,2% de participação, seguido por *Grupo Bradesco Seguros* (~9,6%) e *BB Seguros / Brasilseg* (~9,5%). Juntos, os três maiores grupos concentram mais de um terço de todo o prêmio emitido no país.
* **Dominância de Linhas Pessoais e Patrimoniais:** As carteiras de *Vida, Prestamista & Pessoas* (~R$ 351 Bi) e *Automóveis & Frotas* (~R$ 320 Bi) representam mais de 65% da receita operacional total do mercado.
* **Eficiência e Rentabilidade Operacional:** O mercado consolidado opera com um *Loss Ratio* (Sinistralidade) médio de **44,3%**, considerado um patamar saudável e controlado dentro dos padrões atuariais regulatórios.
* **Resiliência do Ramo Rural / Agronegócio:** Com a modelagem estrita e correção na precedência de ramos, a carteira de *Rural / Agro* revelou um volume acumulado expressivo de **R$ 76 Bi**, com índice de sinistralidade equilibrado (~30,2%), reforçando a força do agronegócio na demanda de proteção securitária.
* **Crescimento Consistente e Sazonalidade:** A série temporal histórica (2020–2026) demonstra estabilidade nos prêmios emitidos mês a mês (~R$ 16–17 Bi/mês em 2026), com picos controlados de sinistralidade ao longo do ciclo econômico.