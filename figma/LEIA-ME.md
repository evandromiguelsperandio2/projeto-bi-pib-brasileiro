# Figma + Power BI — layout com sidebar

Versão 2 do visual: **sidebar escura à esquerda** em todas as páginas, capa escura
com o motivo do PIB e conteúdo em cartões claros. O layout do PBIP já foi atualizado
para essa estrutura.

## O que mudou

- A navegação saiu de cima e virou uma **sidebar de 212 px** com logo, perfil e cinco
  itens: Capa, Visão geral, Temporal, Setores e Síntese.
- A **capa** agora é um hero escuro com título grande, pergunta, KPI do PIB nominal e
  um gráfico decorativo do índice do PIB.
- O conteúdo ocupa a área à direita da sidebar, com cartões de raio 12 px, cabeçalho de
  página e chip “2026-T2”.
- As posições dos visuais, a página ativa e as cores da capa já foram aplicadas no
  PBIP desta cópia.
- A matriz “Contribuição ao crescimento por setor e ano” virou **colunas empilhadas**
  (uma coluna por ano, três setores), com eixo, legenda e cores do tema.
- A tabela “Setores em números” recebeu cabeçalho, bandas, grade e tipografia maiores.

## Arquivos

```
figma/
├── frames/                  # frames completos 1280×720 (mock, para o Figma)
│   ├── 00_design_system.svg/.png
│   ├── 01_capa.svg/.png
│   ├── 02_visao_geral.svg/.png
│   ├── 03_temporal.svg/.png
│   ├── 04_setores.svg/.png
│   └── 05_sintese.svg/.png
├── fundos/                  # fundos prontos para o Power BI (sidebar + cartões)
│   ├── 01_capa.png ...
│   └── 05_sintese.png
├── preview.html             # abra no navegador para ver tudo
├── posicoes.csv             # posições novas de cada visual no PBIP
├── _gerar_frames.py         # regera SVGs, PNGs, CSV e preview
├── _aplicar_layout.py       # reaplica o layout no PBIP
├── _ajustar_tabelas.py      # colunas empilhadas + estilo da tabela
├── _gerar_frames_topnav.py  # gerador antigo (backup)
└── _old_topnav/             # frames/fundos antigos (backup)
```

## Como funciona a sidebar no Power BI

A sidebar é **estática na imagem de fundo**: logo, perfil, ícones, textos e o item
ativo de cada página estão no PNG. Os botões do Power BI foram movidos para cima dela
e ficaram **invisíveis** — continuam clicando e navegando, mas quem aparece é o desenho
do fundo.

Consequências práticas:

- **Não apague** os botões `nav_*` / `capa_botao_*`; eles são a área clicável.
- Cada página tem um fundo com o item correspondente ativo (azul).
- Se você mudar a posição dos itens no Figma, ajuste `ITEM_Y` em
  `_aplicar_layout.py` e rode o script de novo.
- O item **Capa** não tem botão na própria capa (ele é o ativo); nas outras páginas
  ele tem botão e volta para a capa.

## Como aplicar no Power BI

1. Abra `powerbi/pib_brasileiro/pib_brasileiro.pbip` e clique em **Atualizar**.
2. Para cada página, use **Formatar página → Plano de fundo da tela → Adicionar
   imagem** e escolha o PNG correspondente de `figma/fundos/`.
3. Ajuste a imagem para **Preencher** (Fit) e transparência **0%**.
4. Bloqueie a imagem no painel **Seleção**.
5. Deixe os visuais (gráficos, cartões, tabela, botões invisíveis) por cima.
6. Confira os números: **12,74 · +2,29% · 2,26% · 69,5% · +2,0% / +0,48%**.

O PBIP já está com:

- sidebar de botões invisíveis nas posições `x=28`, `y=196/248/300/352/404`;
- conteúdo reposicionado para `x=272..1248`;
- capa com textos claros e cartão transparente sobre o fundo escuro;
- página ativa = **Capa**;
- cartões com raio 12 e fundo branco;
- tabela `vg_tabela` agora em **976×200**, sem precisar redimensionar.

## Como importar no Figma

O **plano gratuito (Starter)** basta: importar SVG/PNG não é recurso pago. Os limites
práticos são **3 arquivos de Design no espaço da equipe** e **3 páginas por arquivo**;
este pacote usa **um arquivo com três páginas**.

1. Crie um arquivo novo.
2. Crie as páginas **Design system**, **Frames** e **Fundos**.
3. Arraste `frames/00_design_system.svg` e os cinco `frames/0X_*.svg` para o canvas
   (ou **File → Place image**, Shift+Ctrl+K).
4. Em **Fundos**, arraste os `fundos/0X_*.svg` se quiser editar; ou use os PNGs.
5. Os SVGs vêm com as camadas `fundo`, `titulos`, `interativos` e `conteudo`.

### Fonte e tamanho

A fonte é **Segoe UI**. No app desktop do Figma (gratuito), ele usa as fontes do
Windows; no navegador pode substituir. Se preferir, troque para **Inter** mantendo os
tamanhos. O Power BI usa pontos; o Figma usa pixels. Os SVGs já convertem `pt × 4/3`:

| Papel | Power BI | Figma |
|---|---:|---:|
| Título da capa | 44 pt | 58,7 px |
| Título de página | 22 pt | 29,3 px |
| Subtítulo da capa | 20 pt | 26,7 px |
| Pergunta | 14 pt | 18,7 px |
| Corpo | 12 pt | 16,0 px |
| Título de visual | 11 pt | 14,7 px |
| Rótulo | 9 pt | 12,0 px |
| Rodapé | 8 pt | 10,7 px |

## Para exportar o fundo do Figma

Use os PNGs de `fundos/` (já prontos) ou, no frame:

- mantenha `fundo` visível;
- oculte `titulos`, `interativos` e `conteudo`;
- exporte em PNG 1× (1280×720) ou 2×.

A camada `fundo` inclui a sidebar, os cartões, a linha do cabeçalho, o chip, a capa
escura e o motivo do PIB. Ela **não** inclui títulos, valores, gráficos, textos da
Síntese, botões de conteúdo nem segmentadores.

## Cores

| Papel | Hex |
|---|---|
| Sidebar | `#1D2134` |
| Item da sidebar | `#272C46` |
| Hero da capa | `#171B2C` |
| Cartão do hero | `#222741` |
| Fundo da página | `#F4F5F7` |
| Cartão | `#FFFFFF` |
| Borda | `#E6E8EE` |
| Texto primário | `#111827` |
| Texto secundário | `#4B5563` |
| Serviços | `#2A78D6` |
| Indústria | `#EB6834` |
| Agropecuária | `#1BAF7A` |
| Positivo / negativo | `#006300` / `#D03B3B` |

Raio dos cartões: **12 px**. Sidebar: **24 px**. Botões da sidebar: **12 px**.
Margem lateral do conteúdo: **24 px** a partir de `x=248`.

## Se precisar mexer no layout

1. Edite `figma/_gerar_frames.py` (posições e conteúdo dos frames).
2. Rode `python figma/_gerar_frames.py` para regerar SVGs, PNGs, CSV e preview.
3. Ajuste `LAYOUT` em `figma/_aplicar_layout.py` com as mesmas coordenadas.
4. Rode `python figma/_aplicar_layout.py` para aplicar no PBIP.
5. Rode `python figma/_ajustar_tabelas.py` para manter o gráfico de contribuição e o
   estilo da tabela.
6. Reabra o PBIP e reaplique os PNGs de `figma/fundos/`.

Os scripts usam a pasta pai de `figma/` como raiz do projeto. Se você copiar a pasta
`figma/` para `C:\Users\Aluno\pib_analise\repo`, rode os dois scripts lá para atualizar
a cópia canônica.

## Checklist

- [ ] PBIP aberto e atualizado
- [ ] Fundos aplicados nas 5 páginas
- [ ] Imagens bloqueadas no painel Seleção
- [ ] Sidebar clicando em todas as páginas
- [ ] Capa como página ativa
- [ ] Números conferidos (12,74 · +2,29% · 2,26% · 69,5% · +2,0% / +0,48%)
- [ ] Frames importados no Figma (3 páginas)
- [ ] Fundos exportados/usados em 1280×720

## Observações

- A entrega é o **`.pbip`**; o `.pbix` é opcional.
- Se você abrir a cópia em `Downloads`, o parâmetro `PastaDados` ainda aponta para
  `C:/Users/Aluno/pib_analise/repo/dados`. Funciona enquanto essa pasta existir. Para
  deixar a cópia independente, ajuste o parâmetro para a pasta `dados/` dela.
- O backup do layout anterior está em `figma/_old_topnav/` e
  `figma/_gerar_frames_topnav.py`.
