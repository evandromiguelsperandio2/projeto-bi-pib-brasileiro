# Projeto BI — Tema 12: PIB Brasileiro

**Aluno:** Evandro Miguel · **Turma:** 1 · **Apresentação:** 17/11/2026
**Pergunta norteadora:** Como o PIB brasileiro evoluiu e como os principais setores participaram desse desempenho?

## Estrutura

```
projeto_pib/
├── dados_originais/                 # CSV brutos exportados do SIDRA (intocáveis)
│   ├── tabela1620.csv
│   ├── tabela1621.csv
│   ├── tabela1846.csv
│   └── tabela5932.csv
├── dados/
│   ├── fato_pib_volume.csv          # 1620 — índice de volume (sem ajuste sazonal)
│   ├── fato_pib_volume_sazonal.csv  # 1621 — índice de volume com ajuste sazonal
│   ├── fato_pib_corrente.csv        # 1846 — valores a preços correntes (R$ milhões)
│   ├── fato_pib_taxa.csv            # 5932 — taxa trimestral vs. mesmo trimestre do ano anterior
│   ├── dim_tempo.csv                # dimensão calendário trimestral
│   ├── dim_serie.csv                # dimensão das séries (grupo, subgrupo, nível)
│   ├── planilha_pib.xlsx            # a mesma base em Excel, já formatada
│   └── log_etl.txt                  # log de decisões e validações (Etapa 02)
├── notebooks/
│   └── etapa02_etl.ipynb            # Etapa 02 executável: inspeção, decisões, validação
├── scripts/
│   ├── transformar_sidra.py         # ETL reproduzível dos CSV do SIDRA
│   └── gerar_planilha.py            # gera a planilha .xlsx a partir dos CSV tratados
├── powerbi/
│   └── tema_pib.json                # tema de cores validado (daltonismo e contraste)
└── docs/
    ├── ficha_fontes.md              # ficha de fontes (Etapa 01)
    ├── analise_e_plano.md           # achados, modelo, DAX e páginas do dashboard
    ├── medidas_dax.md               # medidas DAX corrigidas e validadas
    └── modelo_powerbi.md            # importação, relacionamentos e identidade visual
```

## Como reproduzir o ETL

A partir da raiz do projeto:

```bash
python scripts/transformar_sidra.py
```

Os caminhos padrão já apontam para `dados_originais/` e `dados/`, resolvidos a partir
da pasta do próprio script (funciona de qualquer diretório). Para usar outras pastas:

```bash
python scripts/transformar_sidra.py --indir outra/pasta --outdir saida
```

O script lê os quatro CSV originais do SIDRA (`tabela1620.csv`, `tabela1621.csv`,
`tabela1846.csv`, `tabela5932.csv`), valida a estrutura, converte para formato longo e
grava os fatos, as dimensões e o log. Ele interrompe a execução se encontrar duplicidade,
período incompleto, valor não numérico ou mais de uma unidade na mesma tabela.

## Notebook da Etapa 02

`notebooks/etapa02_etl.ipynb` documenta o ETL de ponta a ponta — inspeção dos originais,
decisões de tratamento, execução, validações e log — com os valores formatados no padrão
brasileiro. Ele chama `transformar_sidra.executar()`, a mesma função da linha de comando,
então notebook e script produzem exatamente o mesmo resultado.

```bash
python -m jupyter notebook notebooks/etapa02_etl.ipynb
```

O notebook já está salvo com as saídas executadas. Para reexecutar tudo do zero:

```bash
python -m nbconvert --to notebook --execute --inplace notebooks/etapa02_etl.ipynb
```

## Planilha para Excel

Os CSV usam ponto decimal (formato neutro, ideal para o Power BI). Para abrir a base no
Excel já formatada — com R$, percentuais e índices no padrão brasileiro — gere a planilha:

```bash
python scripts/gerar_planilha.py
```

O resultado é `dados/planilha_pib.xlsx`, com as abas Leia-me, Fatos, dim_tempo, dim_serie
e Destaques.

## Versões

O projeto é versionado em Git. `dados_originais/` é imutável: qualquer mudança de fonte
deve gerar um novo commit com a data de acesso registrada na ficha de fontes.

## Fontes

| Tabela SIDRA | Variável | Unidade | Período |
|---|---|---|---|
| 1620 | Índice de volume trimestral, série encadeada (1995 = 100) | Número-índice | 2000-T1 a 2026-T2 |
| 1621 | Índice de volume trimestral com ajuste sazonal (1995 = 100) | Número-índice | 2000-T1 a 2026-T2 |
| 1846 | Valores a preços correntes | R$ milhões | 2000-T1 a 2026-T2 |
| 5932 | Taxa trimestral vs. mesmo trimestre do ano anterior | % | 2000-T1 a 2026-T2 |

Acesso: 20/10/2026. Fonte: IBGE — SIDRA. Dados públicos; citar a fonte.

## Cuidados

- 2026 tem apenas 1º e 2º trimestres; não calcular “ano fechado” para 2026.
- Valores correntes (1846) não são comparáveis em nível entre anos; para evolução real, usar 1620/1621.
- 1621 é ajustada sazonalmente: serve para comparação trimestre contra trimestre, não para somas anuais.
- 1620 e 5932 têm 22 séries; 1621 tem 21; 1846 tem 23 (inclui “Variação de estoque”).
- Índices e percentuais não devem ser somados; somas só fazem sentido em R$ correntes.
