# Etapa 04 — roteiro do `.pbix` e spec do Figma

**Projeto BI · Tema 12 — PIB Brasileiro · Evandro Miguel**

Este documento fecha a Etapa 03/04: o que já está pronto no projeto Power BI,
como abrir, como salvar o `.pbix` e como reproduzir o layout no Figma.

---

## 1. O que está pronto

`powerbi/pib_brasileiro/` é um **Power BI Project (PBIP)** com:

- **Modelo em estrela**: 2 dimensões (`dim_calendario`, `dim_serie`) e 4 fatos
  (`fato_pib_volume`, `fato_pib_volume_sazonal`, `fato_pib_corrente`, `fato_pib_taxa`).
- **8 relacionamentos** 1:* com direção única.
- **23 medidas DAX** na tabela `_Medidas`, organizadas em 4 pastas de exibição.
- **5 páginas**: Capa, Visão geral, Análise temporal, Setores e Síntese.
- Navegação por botões, segmentadores de Ano e Grupo, títulos informativos e rodapé de fonte.
- Tema `tema_pib.json` aplicado (paleta validada, uma cor por setor).

### Por que `dim_calendario.csv` e não `dim_tempo.csv`

O Power BI só permite **marcar como tabela de datas** uma coluna com **todos os dias,
sem buracos**. A `dim_tempo.csv` tem 106 datas (início de trimestre) e por isso não pode
ser marcada. O ETL passou a gerar `dim_calendario.csv` (9.678 dias, 2000-01-01 a
2026-06-30), que é a tabela de datas do modelo. A `dim_tempo.csv` continua no projeto
como referência do grão trimestral.

### Colunas-flag já vêm no CSV

`dim_serie.csv` agora traz `eh_pib`, `eh_valor_adicionado`, `eh_setor`, `sinal`,
`em_1620`, `em_1621`, `em_1846`, `em_5932` e `ordem_cor`. Não é preciso criá-las no
Power Query: o modelo apenas as importa. A `ordem_cor` garante que Serviços receba a
primeira cor (azul), Indústria a segunda (laranja) e Agropecuária a terceira (verde-água).

---

## 2. Como abrir e salvar o `.pbix`

1. Abra `powerbi/pib_brasileiro/pib_brasileiro.pbip` no Power BI Desktop.
2. Clique em **Atualizar agora** (o modelo abre sem dados até o primeiro refresh).
3. Confira o cartão da capa: **12,74** (PIB nominal 2025 em R$ trilhões).
4. **Arquivo → Salvar como → `powerbi/pib_brasileiro.pbix`**. Esse é o arquivo da Etapa 04.

> Se o projeto for movido de pasta, ajuste o parâmetro **PastaDados** em
> *Transformar dados → Gerenciar parâmetros*. Ele aponta para a pasta `dados/` do projeto.

### Números de conferência (já validados no motor DAX)

| Medida | Valor |
|---|---:|
| PIB nominal 2025 | R$ 12,7386 tri |
| PIB real 2025 | +2,29% |
| CAGR 2000–2025 | 2,26% a.a. |
| PIB 2026-T2 YoY | +1,98% |
| PIB 2026-T2 QoQ | +0,48% |
| Serviços no VA 2025 | 69,48% |
| Contribuição 2025 — serviços / agro / indústria | +1,25 / +0,78 / +0,35 p.p. |
| Crescimento 2026-T2 — serviços / agro / indústria | +1,52% / +6,76% / +1,50% |

> O teste de aceitação do índice em 2025 é **194,45 na média dos quatro trimestres**;
> o 4º trimestre isolado é **192,94**. Os dois estão certos.

---

## 3. Mapa das páginas

| Página | Conteúdo | Interação |
|---|---|---|
| **Capa** | título, pergunta, período, cartão do PIB nominal, fonte e autoria | 4 botões para as demais páginas |
| **Visão geral** | 4 cartões de KPI; composição do VA por ano (100% empilhada); contribuição de 2025; matriz “Setores em números” | — |
| **Análise temporal** | índice do PIB (área); crescimento anual; índice por setor (média anual); QoQ sazonal | — |
| **Setores** | matriz contribuição ano × setor; ranking 2026-T2 por subsetor; participação no VA | segmentadores **Ano** e **Grupo** |
| **Síntese** | 3 achados, recomendação e números para lembrar | — |

Todos os visuais têm título próprio, unidade no eixo e fonte no rodapé. 2026 é
tratado como período parcial (apenas T1 e T2).

---

## 4. Spec do Figma

O objetivo é reproduzir o layout do `.pbix` no Figma para a Etapa 05. Use **um frame
1280 × 720 por página**, com o mesmo grid do relatório.

### 4.1 Grid e espaçamento

- Margem lateral: **32 px**; margem superior: **16 px**; rodapé a **688 px**.
- Grid de 12 colunas, gutter de **16 px**.
- Espaçamento vertical entre blocos: **20 px**.
- Cantos: cartões e gráficos com raio **8 px**; botões com raio **6 px**.

### 4.2 Tipografia (Segoe UI)

| Papel | Tamanho | Peso | Cor |
|---|---:|---|---|
| Título da capa | 44 pt | Semibold | `#0B0B0B` |
| Título de página | 22 pt | Semibold | `#0B0B0B` |
| Subtítulo de página | 10 pt | Regular | `#52514E` |
| Título de visual | 11 pt | Semibold | `#52514E` |
| Corpo / achados | 12 pt | Regular | `#0B0B0B` |
| Rótulo de cartão | 10 pt | Regular | `#52514E` |
| Valor de cartão | 28–32 pt | Bold | cor de destaque |
| Rodapé / fonte | 8 pt | Regular | `#898781` |

### 4.3 Cores

| Papel | Hex |
|---|---|
| Serviços | `#2A78D6` |
| Indústria | `#EB6834` |
| Agropecuária | `#1BAF7A` |
| Apoio (4ª série) | `#EDA100` |
| Positivo / negativo | `#006300` / `#D03B3B` |
| Fundo da página | `#F9F9F7` |
| Cartão | `#FCFCFB` / `#FFFFFF` |
| Texto primário / secundário | `#0B0B0B` / `#52514E` |
| Rótulos e eixos | `#898781` |
| Borda / grade | `#E1E0D9` |

### 4.4 Componentes (crie como componentes no Figma)

| Componente | Dimensões | Regras |
|---|---|---|
| `KPI card` | 292 × 96 | barra de destaque de 4 px à esquerda; rótulo 10 pt; valor 28 pt; borda `#E1E0D9`; raio 8 |
| `Nav button` | 96 × 28 | raio 6; ativo: fundo `#2A78D6` e texto branco; inativo: fundo branco, texto `#52514E`, borda `#E1E0D9` |
| `Chart card` | 592 × 220 (ou 700 × 270) | fundo branco; borda `#E1E0D9`; raio 8; título 11 pt no topo; respiro interno 8 px |
| `Slicer` | 180 × 80 | rótulo 10 pt; campo com borda `#E1E0D9`; raio 8 |
| `Footer` | 1216 × 18 | 8 pt `#898781` |

### 4.5 Coordenadas por página

**Capa**: título em (80, 150) 900×72; subtítulo (80, 226); pergunta (80, 296) 780×54;
cartão em (80, 380) 320×112; botões em y=566, x=80 + 196·i, 180×40; rodapé (80, 660).

**Visão geral**: cartões em y=80, x=32 + 308·i, 292×96; composição (32, 196) 592×220;
contribuição (656, 196) 592×220; matriz (32, 432) 1216×236.

**Análise temporal**: índice (32, 80) 700×270; crescimento anual (748, 80) 500×270;
setores (32, 366) 700×276; QoQ (748, 366) 500×276.

**Setores**: segmentadores (32, 80) e (228, 80), 180×80; matriz (32, 176) 760×464;
ranking (808, 80) 440×300; participação (808, 396) 440×244.

**Síntese**: três achados em (32 + 400·i, 96) 384×250; recomendação (32, 372) 760×290;
números (808, 372) 440×290.

### 4.6 Ordem de trabalho no Figma

1. Crie uma página **Design system** com os estilos de cor e texto da tabela 4.2/4.3.
2. Monte os 5 componentes da tabela 4.4, com variantes `Ativo`/`Inativo` para o botão.
3. Crie 5 frames 1280×720 com Auto Layout e replique as coordenadas de 4.5.
4. Importe o tema do Power BI como referência: `powerbi/tema_pib.json` tem os mesmos hex.
5. Exporte a capa em PNG para o slide de abertura e o frame completo em PDF para o anexo.

---

## 5. Checklist da Etapa 04

- [ ] `.pbip` aberto e atualizado (cartão 12,74)
- [ ] 8 relacionamentos visíveis no modo Modelo
- [ ] `dim_calendario` marcada como tabela de datas
- [ ] 23 medidas conferidas contra os números da seção 2
- [ ] 5 páginas navegando pelos botões
- [ ] segmentadores de Ano e Grupo filtrando a página Setores
- [ ] tema `tema_pib.json` aplicado
- [ ] `.pbix` salvo em `powerbi/pib_brasileiro.pbix`
- [ ] frames do Figma com o mesmo grid, cores e tipografia
- [ ] commit “Etapa 04 — .pbix funcional e layout no Figma”
