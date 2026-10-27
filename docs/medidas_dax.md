> **Atualização de 26/10/2026.** As medidas já estão implementadas em
> `powerbi/pib_brasileiro/.../tables/_Medidas.tmdl`, usando `dim_calendario`. Onde este
> documento citar `dim_tempo`, leia `dim_calendario`. `REMOVEFILTERS` aceita **uma tabela
> por argumento**: `REMOVEFILTERS(dim_calendario, dim_serie)` gera erro; use dois
> argumentos separados.

# Medidas DAX — versão corrigida

**Projeto BI · Tema 12 — PIB Brasileiro · Evandro Miguel**

Este documento substitui a seção 4 de `analise_e_plano.md`. As medidas abaixo corrigem
quatro problemas da versão inicial e foram conferidas contra os dados tratados.

## O que mudou e por quê

| Problema na versão inicial | Consequência | Correção |
|---|---|---|
| `CALCULATE(..., dim_serie[serie] = "PIB")` | O filtro do `CALCULATE` **substitui** o segmentador de série: a medida mostra o PIB mesmo com outro setor selecionado | `REMOVEFILTERS(dim_serie)` + coluna-flag `eh_pib` |
| `Contribuição` usava `AVERAGE(fato_pib_taxa[valor])` | Com um ano no contexto, tira a média de 4 taxas trimestrais, que não é o crescimento anual | Crescimento calculado pelo **índice de volume** e peso do ano anterior |
| `CAGR` com 2000, 2025 e 25 fixos | Ao filtrar outro período, mostra um número errado com aparência de certo | `MIN`/`MAX` de `dim_tempo[ano]` |
| Medidas sem distinção entre "PIB fixo" e "série selecionada" | Gráficos por setor e cartões de PIB competiam pelo mesmo filtro | Duas medidas com intenção explícita |

## Pré-requisitos no modelo

1. `dim_tempo` marcada como **tabela de datas** (coluna `data`).
2. `dim_tempo[data]` com tipo Data; `ano` e `trimestre` como número inteiro.
3. Colunas de apoio na `dim_serie` (código M em `modelo_powerbi.md`):
   `eh_pib`, `eh_valor_adicionado`, `eh_setor`, `sinal`, `em_1620`, `em_1621`,
   `em_1846`, `em_5932`.
4. Relacionamentos 1:* com direção única, de `dim_tempo[data]` e `dim_serie[serie]`
   para os quatro fatos.

---

## 1. PIB real (índice)

```dax
PIB real (índice) =
CALCULATE(
    AVERAGE(fato_pib_volume[valor]),
    REMOVEFILTERS(dim_serie),
    dim_serie[eh_pib] = TRUE()
)
```

Sempre devolve o PIB, ignorando o segmentador de série. É a medida dos cartões de KPI.
Para gráficos por setor, use a medida 2.

## 2. Índice de volume da série selecionada

```dax
Índice de volume (série selecionada) =
AVERAGE(fato_pib_volume[valor])
```

Respeita o segmentador e a linha do visual. É a medida das linhas por setor.

## 3. PIB real — variação contra o mesmo trimestre do ano anterior

```dax
PIB real YoY % =
VAR atual = [PIB real (índice)]
VAR anterior =
    CALCULATE([PIB real (índice)], SAMEPERIODLASTYEAR(dim_tempo[data]))
RETURN DIVIDE(atual - anterior, anterior)
```

- Em nível **trimestral**, é exatamente o YoY do trimestre.
- Em nível **anual**, compara a média dos 4 trimestres com a do ano anterior. É uma
  aproximação do crescimento anual (o IBGE calcula por volume total); a diferença é
  de centésimos e está documentada.

**Conferência:** em 2025 deve dar **+2,29%**; em 2026-T2, **+2,0%**.

## 4. PIB real — variação contra o trimestre anterior (com ajuste sazonal)

```dax
PIB real QoQ % (sazonal) =
VAR atual =
    CALCULATE(
        AVERAGE(fato_pib_volume_sazonal[valor]),
        REMOVEFILTERS(dim_serie),
        dim_serie[eh_pib] = TRUE()
    )
VAR anterior =
    CALCULATE(
        AVERAGE(fato_pib_volume_sazonal[valor]),
        REMOVEFILTERS(dim_serie),
        dim_serie[eh_pib] = TRUE(),
        DATEADD(dim_tempo[data], -1, QUARTER)
    )
RETURN DIVIDE(atual - anterior, anterior)
```

Use **apenas em visuais de nível trimestral** (linha do tempo). Não faz sentido somar
esta medida em um ano.

**Conferência:** 2026-T2 deve dar **+0,48%**.

## 5. PIB nominal

```dax
PIB nominal (R$) =
CALCULATE(
    SUM(fato_pib_corrente[valor]),
    REMOVEFILTERS(dim_serie),
    dim_serie[eh_pib] = TRUE()
) * 1000000
```

```dax
PIB nominal (R$ trilhões) = DIVIDE([PIB nominal (R$)], 1E12)
```

A tabela 1846 está em R$ milhões; a multiplicação converte para reais. Formate a segunda
medida com duas casas e sufixo "tri".

**Conferência:** 2025 deve dar **R$ 12,74 trilhões**.

## 6. Participação no valor adicionado

```dax
Participação no VA % =
VAR numerador = SUM(fato_pib_corrente[valor])
VAR denominador =
    CALCULATE(
        SUM(fato_pib_corrente[valor]),
        REMOVEFILTERS(dim_serie),
        dim_serie[eh_valor_adicionado] = TRUE()
    )
RETURN DIVIDE(numerador, denominador)
```

Use **somente** com `dim_serie[serie]` ou `dim_serie[nivel]` no visual. Sem filtro de
série, o numerador soma setores + subsetores + agregados e duplica valores.

**Conferência (2025):** agropecuária **7,1%**, indústria **23,4%**, serviços **69,5%**.

## 7. Contribuição ao crescimento (pontos percentuais)

```dax
Contribuição ao crescimento (p.p.) =
VAR ano_atual = MAX(dim_tempo[ano])
VAR indice_atual =
    CALCULATE(AVERAGE(fato_pib_volume[valor]), dim_tempo[ano] = ano_atual)
VAR indice_anterior =
    CALCULATE(AVERAGE(fato_pib_volume[valor]), dim_tempo[ano] = ano_atual - 1)
VAR crescimento = DIVIDE(indice_atual, indice_anterior) - 1
VAR peso_anterior =
    DIVIDE(
        CALCULATE(SUM(fato_pib_corrente[valor]), dim_tempo[ano] = ano_atual - 1),
        CALCULATE(
            SUM(fato_pib_corrente[valor]),
            dim_tempo[ano] = ano_atual - 1,
            REMOVEFILTERS(dim_serie),
            dim_serie[eh_valor_adicionado] = TRUE()
        )
    )
RETURN crescimento * peso_anterior * 100
```

Desenhada para **visuais anuais** (matriz setor × ano, cascata). O crescimento vem do
índice de volume; o peso, do valor adicionado do ano anterior.

**Conferência (2025):** agropecuária **+0,78 p.p.**, indústria **+0,35 p.p.**,
serviços **+1,25 p.p.** Em 2015: **+0,17 / −1,37 / −1,95**.

## 8. CAGR do período selecionado

```dax
CAGR do período =
VAR ano_ini = MIN(dim_tempo[ano])
VAR ano_fim = MAX(dim_tempo[ano])
VAR n = ano_fim - ano_ini
VAR valor_ini = CALCULATE([PIB real (índice)], dim_tempo[ano] = ano_ini)
VAR valor_fim = CALCULATE([PIB real (índice)], dim_tempo[ano] = ano_fim)
RETURN IF(n > 0, (valor_fim / valor_ini) ^ (1 / n) - 1)
```

Funciona com qualquer recorte de anos. Com um único ano selecionado, retorna vazio
(não há crescimento composto a calcular).

**Conferência (2000–2025):** **2,26% a.a.**

## 9. Média móvel de 4 trimestres

```dax
Média móvel 4T =
CALCULATE(
    AVERAGE(fato_pib_volume[valor]),
    REMOVEFILTERS(dim_serie),
    dim_serie[eh_pib] = TRUE(),
    DATESINPERIOD(dim_tempo[data], MAX(dim_tempo[data]), -4, QUARTER)
)
```

Suaviza a série trimestral para leitura de tendência.

## 10. Inflação implícita (variação anual dos preços)

```dax
Inflação implícita (YoY) =
VAR g_nominal =
    DIVIDE(
        CALCULATE([PIB nominal (R$)], dim_tempo[ano] = MAX(dim_tempo[ano])),
        CALCULATE([PIB nominal (R$)], dim_tempo[ano] = MAX(dim_tempo[ano]) - 1)
    ) - 1
VAR g_real = [PIB real YoY %]
RETURN DIVIDE(1 + g_nominal, 1 + g_real) - 1
```

**Conferência (2025):** aproximadamente **5,7%**.

## 11. Aviso de período parcial

```dax
É ano parcial =
VAR ano = MAX(dim_tempo[ano])
VAR trimestres =
    CALCULATE(COUNTROWS(dim_tempo), dim_tempo[ano] = ano, REMOVEFILTERS(dim_tempo))
RETURN IF(trimestres < 4, "Período parcial", BLANK())
```

Use como rótulo/condicional nas páginas para não sugerir "ano fechado" em 2026.

## 12. Demanda — importação com sinal correto

```dax
Demanda agregada (R$) =
CALCULATE(
    SUMX(
        fato_pib_corrente,
        fato_pib_corrente[valor] * RELATED(dim_serie[sinal])
    ),
    REMOVEFILTERS(dim_serie),
    dim_serie[nivel] = "Componente"
) * 1000000
```

`dim_serie[sinal]` vale −1 apenas para "Importação de bens e serviços (-)". Sem isso, a
demanda fica superestimada em cerca de 35%.

**Conferência (2025):** deve fechar em **R$ 12,74 trilhões**, igual ao PIB nominal.

---

## Formatação no Power BI

| Medida | Formato |
|---|---|
| `PIB real (índice)` | Número decimal, 2 casas |
| `PIB real YoY %`, `QoQ %` | Percentual, 2 casas |
| `PIB nominal (R$ trilhões)` | Número decimal, 2 casas, sufixo " tri" |
| `Participação no VA %` | Percentual, 1 casa |
| `Contribuição ao crescimento (p.p.)` | Número decimal, 2 casas, sufixo " p.p." |
| `CAGR do período`, `Inflação implícita` | Percentual, 2 casas |

## Ocultar do usuário

Colunas técnicas que não devem aparecer em visuais:

- `fato_*[valor]`, `fato_*[valor_txt]`, `fato_*[unidade]`, `fato_*[data]`,
  `fato_*[ano]`, `fato_*[trimestre]` — o usuário navega pelas dimensões.
- `dim_serie[ordem_origem]`, colunas-flag `eh_*`, `sinal`, `em_*`.

Deixe visíveis apenas `serie`, `grupo`, `subgrupo`, `nivel` e as colunas de `dim_tempo`.
