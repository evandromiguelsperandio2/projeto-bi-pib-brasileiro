# Power BI — importação, modelo e identidade visual

**Projeto BI · Tema 12 — PIB Brasileiro · Evandro Miguel**

Guia da Etapa 03 (consolidação e início do Power BI) e base para as Etapas 04 e 05.
Siga na ordem.

---

## 1. Importação dos arquivos

No Power BI Desktop: **Página Inicial → Obter dados → Texto/CSV**.

Para cada um dos seis arquivos de `dados/`:

| Arquivo | Papel |
|---|---|
| `fato_pib_volume.csv` | fato — índice de volume (1620) |
| `fato_pib_volume_sazonal.csv` | fato — índice com ajuste sazonal (1621) |
| `fato_pib_corrente.csv` | fato — valores correntes em R$ milhões (1846) |
| `fato_pib_taxa.csv` | fato — taxa YoY (5932) |
| `dim_tempo.csv` | dimensão de tempo |
| `dim_serie.csv` | dimensão de séries |

Na janela de pré-visualização:

- **Delimitador:** vírgula
- **Codificação do arquivo:** 65001: Unicode (UTF-8)
- Clique em **Transformar Dados** (não em Carregar) na primeira importação.

### O ponto que quebra tudo se passar batido

Os CSVs usam **ponto decimal** (`132.75`). Se o Power Query interpretar com a
configuração regional brasileira, pode ler `132.75` como `13275`.

Na coluna `valor`: **Tipo de Dados → Número Decimal → Usando Configurações Regionais →
Inglês (EUA)**.

**Teste de aceitação:** o índice do PIB em 2025 deve ser **194,45**. Se aparecer
**19445**, o locale está errado — refaça o tipo da coluna.

Depois de importar, confira os tipos:

| Tabela | Coluna | Tipo |
|---|---|---|
| fatos | `valor` | Número decimal |
| fatos | `ano`, `trimestre` | Número inteiro |
| fatos, `dim_tempo` | `data` | Data |
| `dim_serie` | `ordem`, `ordem_origem` | Número inteiro |

---

## 2. Modelo em estrela

Oito relacionamentos, todos **1 para muitos**, direção **única**, filtro simples:

| De (lado 1) | Para (lado muitos) |
|---|---|
| `dim_tempo[data]` | `fato_pib_volume[data]` |
| `dim_tempo[data]` | `fato_pib_volume_sazonal[data]` |
| `dim_tempo[data]` | `fato_pib_corrente[data]` |
| `dim_tempo[data]` | `fato_pib_taxa[data]` |
| `dim_serie[serie]` | `fato_pib_volume[serie]` |
| `dim_serie[serie]` | `fato_pib_volume_sazonal[serie]` |
| `dim_serie[serie]` | `fato_pib_corrente[serie]` |
| `dim_serie[serie]` | `fato_pib_taxa[serie]` |

**Por que quatro fatos e não um:** as unidades são diferentes (índice, %, R$ milhões).
Empilhar tudo em uma coluna `valor` mistura grandezas e permite somas sem sentido.

Configurações adicionais:

- **Marcar `dim_tempo` como tabela de datas:** Exibição de Tabela → `dim_tempo` →
  Marcar como tabela de data → coluna `data`.
- **Classificar por coluna:**
  - `dim_tempo[trimestre_txt]` por `dim_tempo[data]`
  - `dim_tempo[ano_trimestre]` por `dim_tempo[data]`
  - `dim_serie[nivel]` por `dim_serie[ordem]`
  - `dim_serie[subgrupo]` por `dim_serie[ordem]`
- Não criar relacionamento entre fatos.

---

## 3. Colunas de apoio na `dim_serie` (Power Query)

Estas colunas resolvem três problemas de uma vez: medidas que não ignoram o
segmentador, contribuição correta e importação com sinal negativo. No Power Query,
com `dim_serie` selecionada, adicione as colunas abaixo em sequência — ou cole o bloco
final no **Editor Avançado**, substituindo o `in`.

```m
#"eh_pib" = Table.AddColumn(#"Tipo alterado", "eh_pib",
    each [serie] = "PIB a preços de mercado", type logical),
#"eh_va" = Table.AddColumn(#"eh_pib", "eh_valor_adicionado",
    each [serie] = "Valor adicionado a preços básicos", type logical),
#"eh_setor" = Table.AddColumn(#"eh_va", "eh_setor",
    each [nivel] = "Setor", type logical),
#"sinal" = Table.AddColumn(#"eh_setor", "sinal",
    each if Text.StartsWith([serie], "Importação") then -1 else 1, Int64.Type),
#"em_1620" = Table.AddColumn(#"sinal", "em_1620",
    each [serie] <> "Variação de estoque", type logical),
#"em_1621" = Table.AddColumn(#"em_1620", "em_1621",
    each [serie] <> "Variação de estoque"
         and [serie] <> "Impostos líquidos sobre produtos", type logical),
#"em_1846" = Table.AddColumn(#"em_1621", "em_1846", each true, type logical),
#"em_5932" = Table.AddColumn(#"em_1846", "em_5932",
    each [serie] <> "Variação de estoque", type logical)
in
    #"em_5932"
```

As colunas `em_*` refletem o recorte atual (1620/5932 têm 22 séries, 1621 tem 21 e
1846 tem 23). Se o recorte mudar, atualize essas listas.

Crie também, na `dim_tempo`, uma coluna de ano parcial:

```m
#"ano_parcial" = Table.AddColumn(#"Tipo alterado", "ano_parcial",
    each [ano] = 2026, type logical)
```

---

## 4. Medidas

Crie as medidas de `docs/medidas_dax.md`. Elas substituem a seção 4 de
`analise_e_plano.md` e já vêm com valores de conferência.

Organize em pastas de exibição:

- **01 PIB** — PIB real, YoY, QoQ, nominal
- **02 Setores** — participação, contribuição
- **03 Tendência** — média móvel, CAGR, inflação implícita
- **04 Apoio** — ano parcial, demanda agregada

---

## 5. Identidade visual

A paleta foi validada para daltonismo e contraste (protanopia, deuteranopia, tritanopia
e contraste contra o fundo claro). Use sempre **uma cor por setor, em todas as páginas**.

### Cores dos setores

| Setor | Hex | Observação |
|---|---|---|
| Serviços | `#2A78D6` | azul — maior setor, cor de destaque |
| Indústria | `#EB6834` | laranja |
| Agropecuária | `#1BAF7A` | verde-água — **exige rótulo direto** (contraste 2,82:1) |

O verde puro (`#008300`) foi testado e **reprovou** na separação para daltonismo contra
o laranja (ΔE 3,2 em protanopia). Não use verde puro ao lado do laranja.

Regra de alívio: como o verde-água fica abaixo de 3:1 contra o branco, todo gráfico que
usar essa cor deve ter **rótulo direto visível** ou uma tabela de apoio.

### Cores de estado (nunca use como série)

| Papel | Hex | Uso |
|---|---|---|
| Positivo | `#006300` | texto de variação positiva |
| Negativo | `#D03B3B` | texto de variação negativa |
| Neutro | `#898781` | eixos, rótulos discretos |

Estado nunca é comunicado só por cor: acompanhe com sinal (`+`/`−`) ou ícone.

### Tinta e superfícies

| Papel | Hex |
|---|---|
| Fundo da página | `#F9F9F7` |
| Fundo do cartão | `#FCFCFB` |
| Texto primário | `#0B0B0B` |
| Texto secundário | `#52514E` |
| Rótulos e eixos | `#898781` |
| Linha de grade | `#E1E0D9` |
| Linha de base | `#C3C2B7` |

**Tipografia:** Segoe UI. Títulos em 14–16 px, textos em 10–11 px. Números de cartão em
24–28 px, com figuras proporcionais; `tabular-nums` apenas em colunas de tabela.

### Tema pronto

Importe `powerbi/tema_pib.json` (Exibição → Temas → Procurar temas). Ele já traz as cores
na ordem correta — **não reordene** as cores da série: a ordem é o mecanismo de segurança
para daltonismo.

---

## 6. Páginas

| # | Página | Conteúdo |
|---|---|---|
| 1 | Capa | título, pergunta, período, fonte, autoria, data de acesso |
| 2 | Visão geral | cartões de KPI + participação setorial + cascata de contribuição do último ano |
| 3 | Análise temporal | linha do índice 2000–2026 com faixas de recessão; colunas de YoY; linha de QoQ sazonal |
| 4 | Setores | matriz de contribuição setor × ano; ranking do último trimestre; área empilhada da participação |
| 5 | Demanda (opcional) | consumo, governo, FBCF, exportações e importações (com sinal) |
| 6 | Síntese | 3 achados + 1 recomendação, com títulos informativos |

Regras de visualização:

- Um eixo só. **Nunca dois eixos Y** no mesmo gráfico.
- Sem pizza com muitas categorias; para participação, use barra empilhada 100% ou área.
- Cascata para contribuições; linha para séries temporais.
- Rodapé com unidade e fonte: "Fonte: IBGE — SIDRA, tabelas 1620/1621/1846/5932,
  acesso em 20/10/2026".
- Destaque visual para 2026 como período parcial.
- Tooltip com o valor exato e a unidade.

---

## 7. Checklist da Etapa 03

- [ ] Seis arquivos importados com locale en-US
- [ ] Índice do PIB 2025 = 194,45 (teste de aceitação)
- [ ] Oito relacionamentos 1:* criados
- [ ] `dim_tempo` marcada como tabela de datas
- [ ] Colunas-flag criadas na `dim_serie`
- [ ] Medidas de `medidas_dax.md` criadas e conferidas
- [ ] Tema `tema_pib.json` importado
- [ ] Colunas técnicas ocultas
- [ ] `.pbix` salvo em `powerbi/pib_brasileiro.pbix`
- [ ] Commit no Git com a mensagem "Etapa 03 — modelo inicial"

## 8. Conferência rápida (antes de fechar a etapa)

| Medida | Valor esperado |
|---|---:|
| PIB nominal 2025 | R$ 12,74 trilhões |
| PIB real 2025 | +2,29% |
| PIB real 2026-T2 (YoY) | +2,0% |
| PIB real 2026-T2 (QoQ) | +0,48% |
| CAGR 2000–2025 | 2,26% a.a. |
| Serviços no VA (2025) | 69,5% |
| Contribuição serviços (2025) | +1,25 p.p. |

Se algum número divergir, o problema costuma ser locale na importação ou filtro de
série faltando na medida.
