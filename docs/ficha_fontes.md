# Ficha de fontes — Etapa 01

## Identificação

- **Tema:** 12 — PIB Brasileiro
- **Aluno:** Evandro Miguel
- **Turma:** 1
- **Apresentação:** 17/11/2026
- **Pergunta norteadora:** Como o PIB brasileiro evoluiu e como os principais setores participaram desse desempenho?

## Público-alvo e decisão apoiada

**Público:** analista de conjuntura econômica ou gestor público responsável por acompanhar
crescimento e prioridades setoriais.

**Decisão apoiada:** identificar quais setores sustentam o crescimento do PIB e onde há
perda de dinamismo, para orientar a priorização de políticas públicas e a alocação de
investimentos. O dashboard deve permitir responder, em poucos segundos, “o PIB está
crescendo?”, “quem está puxando o crescimento?” e “isso mudou nos últimos anos?”.

## Recorte

- **País:** Brasil
- **Período:** 1º trimestre de 2000 a 2º trimestre de 2026
- **Frequência:** trimestral
- **Unidade de análise:** série econômica × trimestre
- **Abrangência:** Contas Nacionais Trimestrais (IBGE)
- **Variáveis:** PIB, valor adicionado, setores (agropecuária, indústria, serviços e
  subsetores) e componentes da demanda.

## Fontes

| # | Origem | Link | Variável usada | Unidade | Período | Acesso |
|---|---|---|---|---|---|---|
| 1 | IBGE — SIDRA, tabela 1620 | https://sidra.ibge.gov.br/tabela/1620 | Índice de volume trimestral, série encadeada (1995 = 100) | Número-índice | 2000-T1 a 2026-T2 | 20/10/2026 |
| 2 | IBGE — SIDRA, tabela 1621 | https://sidra.ibge.gov.br/tabela/1621 | Índice de volume trimestral com ajuste sazonal (1995 = 100) | Número-índice | 2000-T1 a 2026-T2 | 20/10/2026 |
| 3 | IBGE — SIDRA, tabela 1846 | https://sidra.ibge.gov.br/tabela/1846 | Valores a preços correntes | R$ milhões | 2000-T1 a 2026-T2 | 20/10/2026 |
| 4 | IBGE — SIDRA, tabela 5932 | https://sidra.ibge.gov.br/tabela/5932 | Taxa trimestral vs. mesmo trimestre do ano anterior | % | 2000-T1 a 2026-T2 | 20/10/2026 |

**Fonte complementar do tema:** IPEADATA (séries econômicas). Não foi necessária para o
recorte atual; pode ser usada para contextualizar salário mínimo ou atividade econômica.

**Licença/uso:** dados públicos do IBGE. Citar “Fonte: IBGE — SIDRA, tabela XXXX,
acesso em 20/10/2026” em todos os visuais e documentos.

## Indicadores pretendidos

1. PIB real (índice) e variação % contra o mesmo trimestre do ano anterior.
2. Variação % trimestre contra trimestre imediatamente anterior (série com ajuste sazonal).
3. PIB nominal em R$ e crescimento nominal.
4. Participação de cada setor no valor adicionado.
5. Contribuição setorial ao crescimento (pontos percentuais).
6. PIB acumulado em 4 trimestres e média móvel de 4 trimestres.
7. Deflator implícito do PIB (nominal / volume), como apoio à distinção real × nominal.
8. Componentes da demanda: consumo das famílias, consumo do governo, FBCF, exportações e importações.

## Viabilidade e limitações

- **Volume:** 4 tabelas, 106 trimestres, 21 a 23 séries cada; base pequena e adequada ao Power BI.
- **Formato:** CSV largo exportado do SIDRA; o ETL converte para formato longo.
- **Atualização:** trimestral; a base vai até 2026-T2.
- **Lacunas:** 2026 incompleto (somente 1º e 2º trimestres); 1621 não traz impostos líquidos nem variação de estoque.
- **Comparabilidade:** valores correntes não devem ser comparados em nível entre anos; usar a série de volume para evolução real.
- **Revisões:** o IBGE revisa as Contas Nacionais; registrar a data de acesso e reexecutar o ETL quando necessário.
