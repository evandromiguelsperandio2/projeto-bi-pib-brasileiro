# Figma — PIB Brasileiro

Pacote para montar o Figma e usar o resultado como **imagem de fundo** do relatório
Power BI. Tudo parte do layout real do projeto em `powerbi/pib_brasileiro/`, então as
posições dos visuais batem com o PBIP.

## O que tem aqui

```
figma/
├── frames/                  # frames completos 1280×720, com títulos e gráficos de referência
│   ├── 00_design_system.svg
│   ├── 01_capa.svg
│   ├── 02_visao_geral.svg
│   ├── 03_temporal.svg
│   ├── 04_setores.svg
│   └── 05_sintese.svg
├── fundos/                  # versão só com a estrutura, pronta para o Power BI
│   ├── 01_capa.svg / .png
│   ├── 02_visao_geral.svg / .png
│   ├── 03_temporal.svg / .png
│   ├── 04_setores.svg / .png
│   └── 05_sintese.svg / .png
├── preview.html             # abra no navegador para ver tudo
├── posicoes.csv             # x, y, largura e altura reais de cada visual no PBIP
└── _gerar_frames.py         # regera os SVGs se o layout mudar
```

Os SVGs têm **quatro camadas** (grupos), importadas como grupos no Figma:

| Camada | O que contém | Usar no fundo? |
|---|---|---|
| `fundo` | fundo da página, linha superior, réguas, cartões, moldura do KPI, motivo da capa | **Sim** |
| `titulos` | títulos de página, subtítulos, títulos dos visuais, rótulos dos KPIs, rodapé | Depende do modo |
| `interativos` | botões de navegação e segmentadores desenhados | **Não** — o Power BI tem os de verdade |
| `conteudo` | gráficos de referência, valores dos KPIs, tabela e textos da Síntese | **Não** |

Os arquivos de `fundos/` já vêm somente com a camada `fundo`. Se preferir, use os PNGs
diretamente no Power BI — eles estão em 1280×720.

## Como importar no Figma

O **plano gratuito (Starter)** é suficiente: importar SVG/PNG não é recurso pago. Os
limites que importam aqui são **3 arquivos de Design no espaço da equipe** e
**3 páginas por arquivo**; os Drafts são ilimitados. Este pacote já foi pensado para
caber em **um arquivo com três páginas**.

1. Crie um arquivo novo no Figma.
2. Crie três páginas: **Design system**, **Frames** e **Fundos**.
3. Em **Design system**, arraste `frames/00_design_system.svg` para o canvas (ou use
   **File → Place image**, Shift+Ctrl+K).
4. Em **Frames**, arraste os cinco `frames/0X_*.svg`. Cada um vira um frame de
   1280×720; posicione em (0, 0).
5. Em **Fundos**, arraste os `fundos/0X_*.svg` se quiser editar o fundo; ou use os PNGs
   prontos.
6. Confira se o texto veio como texto editável. A fonte é **Segoe UI**. No app desktop
   do Figma (gratuito) ela usa as fontes do Windows; no navegador pode haver
   substituição. Se preferir, troque para **Inter** mantendo os tamanhos.

> **Atenção ao tamanho da fonte:** o Power BI usa **pontos**; o Figma usa **pixels**.
> Os SVGs já convertem `pt × 4/3`. Então 22 pt do Power BI = **29,3 px** no Figma.
> Não use 22 px achando que é 22 pt.

| Papel | Power BI | Figma |
|---|---:|---:|
| Título da capa | 44 pt | 58,7 px |
| Título de página | 22 pt | 29,3 px |
| Subtítulo da capa | 20 pt | 26,7 px |
| Pergunta da capa | 14 pt | 18,7 px |
| Corpo | 12 pt | 16,0 px |
| Título de visual | 11 pt | 14,7 px |
| Rótulo / eixo | 9 pt | 12,0 px |
| Rodapé | 8 pt | 10,7 px |

## Como exportar o fundo

### Opção A — mais rápida (recomendada)

Use os PNGs de `fundos/` diretamente no Power BI. Eles têm só a estrutura: fundo,
cartões, linha superior, réguas e o motivo da capa. Os textos, títulos e gráficos
continuam vindo do Power BI. **Você não precisa mexer em nada no relatório além de
encaixar os visuais.**

### Opção B — visual do Figma

Se quiser que o fundo traga também os títulos e rótulos do Figma:

1. No frame do Figma, mantenha `fundo` e `titulos` visíveis; oculte `interativos` e
   `conteudo`.
2. Exporte o frame em PNG 1× (1280×720) ou 2× (2560×1440).
3. No Power BI, oculte ou apague os textboxes equivalentes (títulos de página, rodapé,
   textos da Síntese) e desligue o título/rótulo dos visuais para não duplicar.
4. Como os botões e segmentadores são interativos, eles **não** entram no fundo: mantenha
   os visuais do Power BI por cima.

## Como aplicar no Power BI

1. Abra `powerbi/pib_brasileiro/pib_brasileiro.pbip`.
2. Confirme que a página está em **1280 × 720** (já está).
3. **Formatar página → Plano de fundo da tela → Adicionar imagem** e escolha
   `figma/fundos/0X_*.png`.
4. Ajuste a imagem para **Preencher** (Fit) e transparência **0%**. Desligue
   “Corresponder plano de fundo” se aparecer.
5. No painel **Seleção**, bloqueie a imagem de fundo para não mover sem querer.
6. Se quiser que as molduras dos cartões do Figma apareçam, selecione cada visual e
   deixe **Plano de fundo = Transparente** e **Borda = Desligada**. Se preferir o visual
   como está, o cartão do Power BI cobre a moldura e o resultado continua correto.
7. Posicione os visuais com `posicoes.csv`. Os valores são os do PBIP atual.
8. Deixe os **botões de navegação** e os **segmentadores** por cima do fundo — eles são
   os elementos interativos.
9. Antes de apresentar, coloque a **Capa** como página ativa.

### Ajuste necessário na Visão geral

O visual `vg_tabela` está em **592×232** no PBIP, mas o desenho do Figma usa a matriz
**1216×232** (largura total), como manda o roteiro. No Power BI, redimensione o visual
para `x=32, y=432, largura=1216, altura=232`. Se preferir mantê-lo em 592, ajuste o
fundo para deixar a moldura só na metade esquerda.

## Estrutura do fundo por página

| Página | Molduras no fundo |
|---|---|
| Capa | KPI 320×112, barra de destaque do título e motivo do PIB à direita |
| Visão geral | 4 KPIs 292×96, 2 gráficos 592×220 e tabela 1216×232 |
| Análise temporal | 4 gráficos: 700×270, 500×270, 700×276 e 500×276 |
| Setores | matriz 760×464, ranking 440×300 e participação 440×244 |
| Síntese | 3 achados 384×250, recomendação 760×290 e números 440×290 |

As posições exatas de cada visual estão em `posicoes.csv`.

## Cores e componentes

| Papel | Hex |
|---|---|
| Serviços | `#2A78D6` |
| Indústria | `#EB6834` |
| Agropecuária | `#1BAF7A` |
| Apoio | `#EDA100` |
| Positivo / negativo | `#006300` / `#D03B3B` |
| Fundo | `#F9F9F7` |
| Cartão | `#FFFFFF` |
| Borda | `#E1E0D9` |
| Texto primário / secundário | `#0B0B0B` / `#52514E` |
| Rótulos | `#898781` |

Raio dos cartões: **8 px**. Botões: **6 px**. Margem lateral: **32 px**. Rodapé em
**y=688**. A linha superior azul tem **4 px**.

## Checklist

- [ ] Frames importados e conferidos em 1280×720
- [ ] Texto em Segoe UI e tamanhos da tabela acima
- [ ] Fundo exportado (ou PNG de `fundos/` usado)
- [ ] Imagem aplicada como plano de fundo no Power BI
- [ ] Imagem bloqueada no painel Seleção
- [ ] Botões e segmentadores por cima do fundo
- [ ] `vg_tabela` redimensionada para 1216×232
- [ ] Capa definida como página ativa
- [ ] Números conferidos: 12,74 · +2,29% · 2,26% · 69,5% · +2,0% / +0,48%

## Observações do projeto

- A entrega é o **`.pbip`** (projeto Power BI). O `.pbix` é opcional; se o professor pedir,
  use Arquivo → Salvar como.
- Se você abrir a cópia em `Downloads`, o parâmetro `PastaDados` ainda aponta para
  `C:/Users/Aluno/pib_analise/repo/dados`. Funciona enquanto essa pasta existir. Para
  deixar a cópia independente, ajuste o parâmetro para a pasta `dados/` dela.
- O `README`/`CHANGELOG` ainda falam em `.pbix`; o roteiro da Etapa 05 fala em Figma.
  Alinhe a documentação com a entrega que o professor pediu.
