<div align="center">
  <h1>🏟️ Público e Renda - Futebol Cearense</h1>
  <p>Dashboard analítico e interativo dos boletins financeiros oficiais de Fortaleza EC e Ceará SC.</p>

  <!-- Badges -->
  <a href="https://streamlit.community.cloud/"><img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white" alt="Streamlit"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://plotly.com/"><img src="https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly"></a>
  <a href="#"><img src="https://img.shields.io/badge/Fortaleza_EC-C41E3A?style=for-the-badge&logo=data:image/svg+xml;base64,&logoColor=white" alt="Fortaleza EC"></a>
  <a href="#"><img src="https://img.shields.io/badge/Status-Online-success?style=for-the-badge" alt="Status"></a>
</div>

<br>

Este projeto é uma ferramenta de **Data Visualization** e análise de dados focada na bilheteria e finanças do futebol cearense. O objetivo central é fornecer transparência e *insights* numéricos sobre a arrecadação, composição de público (sócios, pagantes, gratuidades) e lucratividade dos maiores clubes do estado.

---

## 🎯 O que você encontra aqui

A aplicação conta com quatro páginas principais e seis painéis analíticos:

### 🏠 Início

Página de visão geral com os indicadores consolidados: público total, renda bruta, total de sócios e média de ingressos — filtráveis por ano. Exibe também um *feed* com as últimas partidas adicionadas à base, incluindo data, competição, público e renda de cada uma.

### ⚽ Jogos

Listagem completa de todas as partidas registradas, com filtros por clube, adversário, competição, estádio, período, mando de campo e clássicos. Ao selecionar uma partida, é exibida uma ficha detalhada com público segmentado (sócios, pagantes, cortesias, gratuidades), receita bruta e líquida, preço médio do ingresso e, quando disponível, a quebra entre público mandante e visitante. Inclui links para os documentos originais (Borderô e Súmula em PDF).

### 📊 Relatórios

Seis painéis analíticos independentes, todos com os mesmos filtros compartilhados (clube, adversário, competição, estádio, período, mando e clássico):

*   **Painel Geral** — KPIs de público e renda, composição do público com barras de proporção, recordes históricos (maior público, maior renda, maior % de sócios), evolução anual, rankings por estádio, competição e adversário, e as 10 maiores bilheterias.
*   **FOR vs CEA** — Comparativo lado a lado entre Fortaleza e Ceará: número de jogos, médias de público e renda, preço médio, percentual de sócios, ranking ano a ano com indicação de vencedor, e top 10 clássicos por público.
*   **Composição** — Análise de sócios-torcedores: totais, médias, recordes, evolução anual, penetração percentual ao longo do tempo, correlação entre sócios e público total, e quebra completa por tipo (sócios, ingressos, cortesias, gratuidades) em gráficos de rosca e barras empilhadas.
*   **Financeiro** — Renda bruta vs. líquida, preço médio do ingresso, custo por espectador, evolução anual, correlação público × receita, e rankings por competição.
*   **Sazonalidade** — Distribuição mensal de público e renda, heatmap de média de público por mês e ano, e tabela consolidada ano a ano com jogos, público, receita e preço médio.
*   **Por Competição** — Ranking de competições por média de público e receita, com tabela agregada e gráfico de barras.

### 🧾 Borderô

Recriação digital da ficha de prestação financeira de cada partida. Permite buscar jogos por texto livre e exibe o detalhamento completo: receita de ingressos por setor, despesas por rubrica (aluguéis, impostos, operacional, eventuais, descontos), e o resultado líquido final. Também oferece uma aba de análise cruzada por rubrica entre múltiplos jogos.

## 💼 Sobre o Projeto

Informações financeiras de clubes de futebol no Brasil geralmente ficam presas em PDFs mal escaneados publicados pelas federações. Este projeto transforma esses dados em algo acessível: um painel interativo onde qualquer pessoa pode consultar, filtrar e comparar os números reais de público e renda do futebol cearense.

<div align="center">
  <br>
  <b>[r.lab]</b> • fabio farias
</div>
