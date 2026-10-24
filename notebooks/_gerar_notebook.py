# -*- coding: utf-8 -*-
"""Gera notebooks/etapa02_etl.ipynb."""
from pathlib import Path
import nbformat as nbf

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "notebooks" / "etapa02_etl.ipynb"
DESTINO.parent.mkdir(parents=True, exist_ok=True)

nb = nbf.v4.new_notebook()
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata["language_info"] = {"name": "python", "version": "3.12"}

C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip("\n")))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip("\n")))

# ---------------------------------------------------------------- capa
md(r"""
# Etapa 02 — ETL dos dados do PIB brasileiro

**Projeto de Business Intelligence · Tema 12 — PIB Brasileiro**
**Aluno:** Evandro Miguel · **Turma 1** · **Apresentação:** 17/11/2026

**Pergunta norteadora:** como o PIB brasileiro evoluiu e como os principais setores
participaram desse desempenho?

---

Este notebook documenta, de forma executável, todo o processo de ETL da Etapa 02:
inspeção das bases originais, decisões de tratamento, execução, validações e o log de
decisões. Ele chama **as mesmas funções** de `scripts/transformar_sidra.py`, de modo que
notebook e script produzem exatamente o mesmo resultado.

**Fontes:** IBGE — SIDRA, tabelas 1620, 1621, 1846 e 5932 (Contas Nacionais Trimestrais).
Acesso em 20/10/2026.
""")

# ---------------------------------------------------------------- setup
code(r"""
from pathlib import Path
import contextlib
import csv
import io
import sys

import pandas as pd
from IPython.display import HTML, display

# Localiza a raiz do projeto (a pasta que contém dados_originais/), funcione o
# notebook a partir de notebooks/ ou da raiz.
RAIZ = Path.cwd()
while not (RAIZ / "dados_originais").exists() and RAIZ != RAIZ.parent:
    RAIZ = RAIZ.parent
assert (RAIZ / "dados_originais").exists(), "Abra o notebook dentro da pasta do projeto."

sys.path.insert(0, str(RAIZ / "scripts"))
import transformar_sidra as etl

pd.set_option("display.max_columns", 40)
print("Raiz do projeto:", RAIZ)
print("Python:", sys.version.split()[0], "| pandas:", pd.__version__)
print("Originais encontrados:", sorted(p.name for p in (RAIZ / "dados_originais").glob("*.csv")))
""")

# ---------------------------------------------------------------- helpers
code(r"""
# ---------------------------------------------------------------------------
# Formatação no padrão brasileiro — é isto que deixa os valores "bonitos".
# ---------------------------------------------------------------------------
def n_br(valor, casas=2):
    '''1234.5 vira 1.234,50'''
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")

def sinal(valor, casas=2):
    texto = n_br(valor, casas)
    return texto if texto.startswith("-") else "+" + texto

def pct(valor, casas=1, com_sinal=False):
    base = sinal(valor, casas) if com_sinal else n_br(valor, casas)
    return f"{base}%"

def ppp(valor, casas=2):
    return f"{sinal(valor, casas)} p.p."

def brl_milhoes(valor_mi):
    '''Recebe R$ milhões e devolve texto legível: R$ 12,74 trilhões.'''
    reais = valor_mi * 1_000_000
    for escala, singular, plural in (
        (1e12, "trilhão", "trilhões"),
        (1e9, "bilhão", "bilhões"),
        (1e6, "milhão", "milhões"),
    ):
        if abs(reais) >= escala:
            valor = reais / escala
            nome = singular if abs(valor) < 2 else plural
            return f"R$ {n_br(valor, 2)} {nome}"
    return f"R$ {n_br(reais, 0)}"

def indice(valor, casas=2):
    return n_br(valor, casas)

# ---------------------------------------------------------------------------
# Tabelas e cartões em HTML, para a leitura ficar limpa.
# ---------------------------------------------------------------------------
CSS = '''
<style>
.tbl {border-collapse: collapse; font-family: 'Segoe UI', Arial, sans-serif;
      font-size: 13px; margin: 6px 0 16px 0; background: #fff;}
.tbl th {background: #0f4c5c; color: #fff; text-align: left; padding: 7px 12px;
         font-weight: 600; white-space: nowrap;}
.tbl td {padding: 6px 12px; border-bottom: 1px solid #e3e8ec;}
.tbl tr:nth-child(even) td {background: #f6f9fa;}
.num {text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap;}
.ok  {color: #1b7f5a; font-weight: 700;}
.err {color: #b23b3b; font-weight: 700;}
</style>
'''

def tabela_html(linhas, colunas, alinhamento=None):
    alinhamento = alinhamento or {}
    cabecalho = "".join(f"<th>{c}</th>" for c in colunas)
    corpo = []
    for linha in linhas:
        celulas = "".join(
            f'<td class="{alinhamento.get(c, "")}">{linha[c]}</td>' for c in colunas
        )
        corpo.append(f"<tr>{celulas}</tr>")
    html = (
        CSS
        + f'<table class="tbl"><thead><tr>{cabecalho}</tr></thead>'
        + f'<tbody>{"".join(corpo)}</tbody></table>'
    )
    return HTML(html)

def cartoes(itens):
    html = "<div style='display:flex;gap:12px;flex-wrap:wrap;margin:10px 0 18px'>"
    for titulo, valor, detalhe, cor in itens:
        html += (
            f"<div style='flex:1 1 170px;border:1px solid #dfe6ea;border-left:5px solid {cor};"
            f"border-radius:8px;padding:12px 14px;background:#fff'>"
            f"<div style='font-size:11px;color:#5b6b75;text-transform:uppercase;"
            f"letter-spacing:.05em'>{titulo}</div>"
            f"<div style='font-size:21px;font-weight:700;color:#12232e;margin:4px 0'>{valor}</div>"
            f"<div style='font-size:12px;color:#6b7c86'>{detalhe}</div></div>"
        )
    return HTML(html + "</div>")

ARQUIVOS = {
    "1620": "tabela1620.csv",
    "1621": "tabela1621.csv",
    "1846": "tabela1846.csv",
    "5932": "tabela5932.csv",
}
print("Funções de formatação carregadas.")
""")

# ---------------------------------------------------------------- 1. originais
md(r"""
## 1. As bases originais

Os quatro arquivos foram baixados do SIDRA no formato **largo**: cada trimestre ocupa um
bloco de colunas, e dentro do bloco cada série ocupa **duas** colunas — o valor e a
unidade. O rótulo do trimestre aparece apenas na primeira coluna do bloco.
""")

code(r"""
estrutura = []
for codigo, nome in ARQUIVOS.items():
    with open(RAIZ / "dados_originais" / nome, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.reader(fh, delimiter=";"))
    estrutura.append({
        "Tabela": codigo,
        "Linhas no arquivo": len(linhas),
        "Colunas de dados": len(linhas[5]) - 1,
        "Variável": linhas[1][0].replace("Variável - ", "")[:64],
    })

display(tabela_html(
    estrutura,
    ["Tabela", "Linhas no arquivo", "Colunas de dados", "Variável"],
    {"Linhas no arquivo": "num", "Colunas de dados": "num"},
))
""")

code(r"""
with open(RAIZ / "dados_originais" / "tabela1620.csv", encoding="utf-8-sig", newline="") as fh:
    exemplo = list(csv.reader(fh, delimiter=";"))

recorte = []
for i, rotulo in ((3, "Linha 4 — trimestres"), (4, "Linha 5 — séries"), (5, "Linha 6 — valores")):
    recorte.append({
        "Elemento": rotulo,
        "col 1": exemplo[i][1][:36],
        "col 2": exemplo[i][2][:36],
        "col 3": exemplo[i][3][:36],
        "col 4": exemplo[i][4][:36],
    })

print("Primeiras colunas de tabela1620.csv (delimitador ';'):")
display(tabela_html(recorte, ["Elemento", "col 1", "col 2", "col 3", "col 4"]))
""")

md(r"""
A leitura é: em `col 1` está o **valor** de 2000-T1 para a agropecuária (`132,75`), em
`col 2` a **unidade** (`Número-índice`), em `col 3` o valor da indústria e assim por diante.
O rótulo `1º trimestre 2000` vale para todo o bloco até o próximo rótulo.
""")

# ---------------------------------------------------------------- 2. diagnóstico
md(r"""
## 2. Inspeção: o que há de sujo na base

Antes de transformar, varri **todos** os valores das quatro tabelas em busca dos problemas
que costumam aparecer em CSV: separador decimal, símbolos do SIDRA (`-`, `..`, `X`, `...`),
campos vazios, unidades misturadas e chaves duplicadas.
""")

code(r"""
diagnostico = []
for codigo, nome in ARQUIVOS.items():
    with open(RAIZ / "dados_originais" / nome, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.reader(fh, delimiter=";"))
    lt, ls, lv = linhas[3], linhas[4], linhas[5]
    inicios = [i for i, v in enumerate(lt) if v.strip()]

    total = virgula = especiais = vazios = 0
    unidades = set()
    chaves = []
    for k, ini in enumerate(inicios):
        fim = inicios[k + 1] if k + 1 < len(inicios) else len(lv)
        for col in range(ini, fim, 2):
            if col >= len(lv):
                continue
            total += 1
            bruto = lv[col].replace("\xa0", " ").strip()
            unidade = lv[col + 1].strip() if col + 1 < len(lv) else ""
            unidades.add(unidade)
            chaves.append((ls[col].strip(), lt[ini].strip()))
            if bruto == "":
                vazios += 1
            elif bruto in etl.VALORES_ESPECIAIS:
                especiais += 1
            elif "," in bruto:
                virgula += 1

    diagnostico.append({
        "Tabela": codigo,
        "Registros": total,
        "Decimal com vírgula": virgula,
        "Símbolos especiais": especiais,
        "Campos vazios": vazios,
        "Unidades": ", ".join(sorted(u for u in unidades if u)) or "-",
        "Duplicadas": len(chaves) - len(set(chaves)),
    })

display(tabela_html(
    diagnostico,
    ["Tabela", "Registros", "Decimal com vírgula", "Símbolos especiais",
     "Campos vazios", "Unidades", "Duplicadas"],
    {"Registros": "num", "Decimal com vírgula": "num", "Símbolos especiais": "num",
     "Campos vazios": "num", "Duplicadas": "num"},
))
""")

md(r"""
**Conclusão da inspeção:** não há sujeira de *conteúdo* — nenhum símbolo especial, nenhum
campo vazio, nenhuma unidade misturada e nenhuma chave duplicada. O que exige tratamento é
o **formato**:

| Problema de formato | Onde aparece |
|---|---|
| Layout largo, uma linha com 4.000+ colunas | nos quatro arquivos |
| Decimal com vírgula (`132,75`) e inteiros (`16347`) | 1620, 1621, 5932 e 1846 |
| Rótulo do trimestre só na primeira coluna do bloco | nos quatro arquivos |
| Sem colunas de tempo separadas (ano, trimestre, data) | nos quatro arquivos |
| Valores em R$ milhões sem separador de milhar | 1846 |

É esse formato que faz o número parecer "sujo" quando o CSV é aberto no Excel. O tratamento
resolve isso sem alterar nenhum valor.
""")

# ---------------------------------------------------------------- 3. decisões
md(r"""
## 3. Decisões de tratamento

Cada decisão abaixo tem uma justificativa e o número de registros que ela afeta. Nenhum
registro foi descartado.

| # | Situação | Decisão | Justificativa | Registros afetados |
|---|---|---|---|---:|
| D1 | Layout largo, blocos de 2 colunas por trimestre | Converter para formato longo | Uma linha por série × trimestre: formato que o Power BI consome sem ajuste | 9.328 |
| D2 | Números com vírgula decimal (`132,75`) | Converter para decimal com ponto, mantendo o texto original | Permite cálculo numérico; o texto serve de auditoria | 6.890 |
| D3 | Valor original só existia como texto | Manter a coluna `valor_txt` | Rastreabilidade: cada número pode ser conferido contra o SIDRA | 9.328 |
| D4 | Sem colunas de tempo utilizáveis | Derivar `trimestre`, `ano` e `data` (1º dia do trimestre) | Necessário para o modelo em estrela e para inteligência de tempo no DAX | 9.328 |
| D5 | Rótulo do trimestre só na 1ª coluna do bloco | Propagar o rótulo para todas as séries do bloco | Sem isso, os registros não podem ser identificados | 9.328 |
| D6 | Tabela 5932 traz três variáveis de taxa | Usar apenas "taxa trimestral vs. mesmo trimestre do ano anterior" | Evita métricas duplicadas e é a base do indicador YoY | 2.332 |
| D7 | Séries vêm agregadas e desagregadas juntas | Não agregar nem filtrar nada | Preserva o dado original; o modelo separa por `nivel` na `dim_serie` | 0 |
| D8 | Nenhum valor ausente, especial ou duplicado | Nenhum descarte | Não havia o que tratar | 0 |

**Princípio adotado:** tratar apenas o necessário. Não preencher, não interpolar, não
arredondar e não agregar — o dado bruto do IBGE é a fonte da verdade.
""")

# ---------------------------------------------------------------- 4. execução
md(r"""
## 4. Execução do ETL

A célula abaixo chama `etl.executar()`, a mesma função usada pela linha de comando. Ela lê
os originais, grava os quatro fatos, as duas dimensões e o log.
""")

code(r"""
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    resumos = etl.executar(RAIZ / "dados_originais", RAIZ / "dados")
print(buffer.getvalue())
""")

code(r"""
resumo = []
for codigo, cfg, info in resumos:
    resumo.append({
        "Tabela": codigo,
        "Arquivo gerado": info["arquivo_saida"],
        "Registros": info["n_registros"],
        "Séries": info["n_series"],
        "Trimestres": info["n_periodos"],
        "Período": f"{info['periodo_min']} a {info['periodo_max']}",
        "Unidade": info["unidades"][0],
    })

display(tabela_html(
    resumo,
    ["Tabela", "Arquivo gerado", "Registros", "Séries", "Trimestres", "Período", "Unidade"],
    {"Registros": "num", "Séries": "num", "Trimestres": "num"},
))
""")

md(r"""
### Antes e depois

O mesmo número, antes e depois da transformação:
""")

code(r"""
with open(RAIZ / "dados_originais" / "tabela1620.csv", encoding="utf-8-sig", newline="") as fh:
    bruto = list(csv.reader(fh, delimiter=";"))
lt, ls, lv = bruto[3], bruto[4], bruto[5]

antes = []
for col in range(1, 9, 2):
    antes.append({
        "Trimestre": lt[1],
        "Série": ls[col].strip(),
        "Valor (texto)": lv[col],
        "Unidade": lv[col + 1],
    })

print("ANTES — formato largo do SIDRA")
display(tabela_html(
    antes, ["Trimestre", "Série", "Valor (texto)", "Unidade"], {"Valor (texto)": "num"}
))

volume = pd.read_csv(RAIZ / "dados" / "fato_pib_volume.csv")
depois = []
for _, r in volume.head(4).iterrows():
    depois.append({
        "trimestre_txt": r.trimestre_txt,
        "serie": r.serie,
        "valor_txt": r.valor_txt,
        "valor (no CSV)": r.valor,
        "valor (formatado)": indice(r.valor),
        "ano": int(r.ano),
        "data": r.data,
    })

print("DEPOIS — formato longo, com o valor já numérico")
display(tabela_html(
    depois,
    ["trimestre_txt", "serie", "valor_txt", "valor (no CSV)", "valor (formatado)", "ano", "data"],
    {"valor_txt": "num", "valor (no CSV)": "num", "valor (formatado)": "num", "ano": "num"},
))
print("O CSV guarda o valor no formato neutro (132.75); a exibição usa a vírgula (132,75).")
""")

# ---------------------------------------------------------------- 5. validações
md(r"""
## 5. Validações

As validações não são só "o script rodou": elas conferem a **coerência interna** dos dados
e o **cruzamento entre tabelas** do IBGE. Todas precisam passar.
""")

code(r"""
v = pd.read_csv(RAIZ / "dados" / "fato_pib_volume.csv")
s = pd.read_csv(RAIZ / "dados" / "fato_pib_volume_sazonal.csv")
c = pd.read_csv(RAIZ / "dados" / "fato_pib_corrente.csv")
t = pd.read_csv(RAIZ / "dados" / "fato_pib_taxa.csv")
dt = pd.read_csv(RAIZ / "dados" / "dim_tempo.csv")
ds = pd.read_csv(RAIZ / "dados" / "dim_serie.csv")

verificacoes = []
def checar(nome, condicao, resultado):
    verificacoes.append({
        "Status": "OK" if condicao else "FALHA",
        "Verificação": nome,
        "Resultado": resultado,
    })

# 1-4: estrutura dos fatos
for codigo, cfg, info in resumos:
    checar(
        f"Tabela {codigo}: registros = séries × trimestres",
        info["n_registros"] == info["n_series"] * info["n_periodos"],
        f"{info['n_registros']} = {info['n_series']} × {info['n_periodos']}",
    )

# 5-8: ausências, duplicadas e unidades
for nome, df in (("volume", v), ("sazonal", s), ("corrente", c), ("taxa", t)):
    checar(
        f"{nome}: sem nulos, sem duplicadas, uma unidade",
        df.valor.notna().all()
        and not df.duplicated(["serie", "data"]).any()
        and df.unidade.nunique() == 1,
        f"nulos {int(df.valor.isna().sum())} · duplicadas "
        f"{int(df.duplicated(['serie', 'data']).sum())} · unidades {df.unidade.nunique()}",
    )

# 9: dimensão de tempo contígua
tempos = sorted(zip(dt.ano, dt.trimestre))
contiguo = all(
    (a[1] == 4 and b == (a[0] + 1, 1)) or (a[1] < 4 and b == (a[0], a[1] + 1))
    for a, b in zip(tempos, tempos[1:])
)
checar("dim_tempo contígua e sem buracos", len(dt) == 106 and contiguo,
       f"{len(dt)} trimestres de {dt.ano_trimestre.iloc[0]} a {dt.ano_trimestre.iloc[-1]}")

# 10: dim_serie cobre todas as séries
todas = set(v.serie) | set(s.serie) | set(c.serie) | set(t.serie)
checar("dim_serie cobre todas as séries dos fatos", todas == set(ds.serie),
       f"{len(todas)} séries, {len(set(ds.serie))} na dimensão")

# 11: YoY calculado x taxa publicada
pib = v[v.serie == "PIB a preços de mercado"].set_index("data").valor.sort_index()
yoy_calc = (pib / pib.shift(4) - 1) * 100
taxa_pub = t[t.serie == "PIB a preços de mercado"].set_index("data").valor.sort_index()
dif_yoy = (yoy_calc - taxa_pub).abs().max()
checar("YoY calculado (1620) confere com a taxa publicada (5932)", dif_yoy < 0.1,
       f"diferença máxima de {n_br(dif_yoy, 3)} p.p.")

# 12: VA + impostos = PIB
va = c[(c.ano == 2025) & (c.serie == "Valor adicionado a preços básicos")].valor.sum()
imp = c[(c.ano == 2025) & (c.serie == "Impostos líquidos sobre produtos")].valor.sum()
pib_nom = c[(c.ano == 2025) & (c.serie == "PIB a preços de mercado")].valor.sum()
checar("1846: valor adicionado + impostos = PIB (2025)",
       abs(va + imp - pib_nom) / pib_nom < 1e-6,
       f"{brl_milhoes(va)} + {brl_milhoes(imp)} = {brl_milhoes(pib_nom)}")

# 13: soma dos setores = valor adicionado
setores = ["Agropecuária - total", "Indústria - total", "Serviços - total"]
soma_setores = c[(c.ano == 2025) & (c.serie.isin(setores))].valor.sum()
checar("1846: soma dos três setores = valor adicionado (2025)",
       abs(soma_setores - va) / va < 1e-6,
       f"{brl_milhoes(soma_setores)} = {brl_milhoes(va)}")

# 14: demanda - importação = PIB
demanda = ["Despesa de consumo das famílias",
           "Despesa de consumo da administração pública",
           "Formação bruta de capital fixo",
           "Variação de estoque",
           "Exportação de bens e serviços"]
soma_demanda = c[(c.ano == 2025) & (c.serie.isin(demanda))].valor.sum()
importacao = c[(c.ano == 2025) & (c.serie == "Importação de bens e serviços (-)")].valor.sum()
checar("1846: demanda - importações = PIB (2025)",
       abs(soma_demanda - importacao - pib_nom) / pib_nom < 1e-6,
       f"{brl_milhoes(soma_demanda)} - {brl_milhoes(importacao)} = {brl_milhoes(pib_nom)}")

# 15: 2026 parcial
checar("2026 tem apenas T1 e T2 (período parcial)",
       sorted(v[v.ano == 2026].trimestre.unique().tolist()) == [1, 2],
       "T1 e T2 de 2026")

for linha in verificacoes:
    linha["Status"] = f'<span class="{"ok" if linha["Status"] == "OK" else "err"}">{linha["Status"]}</span>'

display(tabela_html(
    verificacoes, ["Status", "Verificação", "Resultado"], {"Status": "num"}
))

falhas = sum(1 for x in verificacoes if "FALHA" in x["Status"])
print(("Todas as %d verificações passaram." % len(verificacoes)) if falhas == 0
      else ("ATENÇÃO: %d verificação(ões) falharam." % falhas))
""")

# ---------------------------------------------------------------- 6. resultados
md(r"""
## 6. O que a base entrega

Números já formatados no padrão brasileiro, calculados a partir dos arquivos tratados.
""")

code(r"""
pib_ano = v[v.serie == "PIB a preços de mercado"].groupby("ano").valor.mean()
nominal = c[c.serie == "PIB a preços de mercado"].groupby("ano").valor.sum()
va_2025 = c[(c.ano == 2025) & (c.serie == "Valor adicionado a preços básicos")].valor.sum()

cagr = (pib_ano[2025] / pib_ano[2000]) ** (1 / 25) - 1
real_2025 = pib_ano[2025] / pib_ano[2024] - 1
servicos_2025 = c[(c.ano == 2025) & (c.serie == "Serviços - total")].valor.sum() / va_2025

sazonal_pib = s[s.serie == "PIB a preços de mercado"].set_index("data").valor.sort_index()
qoq_2026t2 = sazonal_pib.loc["2026-04-01"] / sazonal_pib.loc["2026-01-01"] - 1
yoy_2026t2 = taxa_pub.loc["2026-04-01"] / 100

display(cartoes([
    ("PIB nominal 2025", brl_milhoes(nominal[2025]), "preços correntes", "#0f4c5c"),
    ("PIB real 2025", pct(real_2025 * 100, 2, com_sinal=True), "vs. 2024", "#1b7f5a"),
    ("Crescimento médio", pct(cagr * 100, 2) + " a.a.", "2000 a 2025", "#2a6f97"),
    ("Serviços no valor adicionado", pct(servicos_2025 * 100, 1), "2025", "#c47f17"),
    ("PIB 2026-T2", pct(yoy_2026t2 * 100, 1, com_sinal=True), "YoY · " + pct(qoq_2026t2 * 100, 2, com_sinal=True) + " QoQ", "#8d5a97"),
]))
""")

code(r"""
linhas_destaque = []
for setor in setores:
    valor_2025 = c[(c.ano == 2025) & (c.serie == setor)].valor.sum()
    valor_2000 = c[(c.ano == 2000) & (c.serie == setor)].valor.sum()
    va_2000 = c[(c.ano == 2000) & (c.serie == "Valor adicionado a preços básicos")].valor.sum()
    serie_indice = v[v.serie == setor].groupby("ano").valor.mean()
    linhas_destaque.append({
        "Setor": setor.replace(" - total", ""),
        "Participação 2000": pct(valor_2000 / va_2000 * 100, 1),
        "Participação 2025": pct(valor_2025 / va_2025 * 100, 1),
        "Variação (p.p.)": ppp(valor_2025 / va_2025 * 100 - valor_2000 / va_2000 * 100, 1),
        "Crescimento real 2000–2025": pct((serie_indice[2025] / serie_indice[2000] - 1) * 100, 1, com_sinal=True),
    })

display(tabela_html(
    linhas_destaque,
    ["Setor", "Participação 2000", "Participação 2025", "Variação (p.p.)", "Crescimento real 2000–2025"],
    {"Participação 2000": "num", "Participação 2025": "num",
     "Variação (p.p.)": "num", "Crescimento real 2000–2025": "num"},
))
""")

# ---------------------------------------------------------------- 7. achados
md(r"""
## 7. Três achados que a base sustenta

1. **Serviços sustentam o crescimento e concentram quase 70% do valor adicionado.**
   É o setor decisivo para o nível de atividade, mas cresce a taxas moderadas no longo prazo.

2. **A agropecuária é pequena em participação, porém a mais dinâmica.**
   Cresce bem acima da média e ganha peso na explicação do crescimento recente.

3. **A indústria perde participação, e a transformação está estagnada.**
   O crescimento de 2026 está concentrado em poucos setores — extrativa, agropecuária e
   informação/comunicação — enquanto a indústria de transformação recua.

Os números exatos de cada achado estão na seção 6 e em `docs/analise_e_plano.md`.
""")

# ---------------------------------------------------------------- 8. log
md(r"""
## 8. Log de decisões gerado

O ETL grava `dados/log_etl.txt` com fontes, transformações, validações, limitações e a
lista de arquivos gerados. É a evidência documental da Etapa 02.
""")

code(r"""
caminho_log = RAIZ / "dados" / "log_etl.txt"
conteudo = caminho_log.read_text(encoding="utf-8")
print(conteudo)
print("-" * 70)
print(f"Log gravado em: {caminho_log}")
print(f"Linhas: {len(conteudo.splitlines())} | Tamanho: {caminho_log.stat().st_size} bytes")
""")

# ---------------------------------------------------------------- 9. limitações
md(r"""
## 9. Limitações e cuidados que seguem para o Power BI

- **2026 é parcial:** existem apenas o 1º e o 2º trimestres; não calcular "ano fechado".
- **Nominal × real:** a tabela 1846 é a preços correntes e não é comparável em nível entre
  anos. Para evolução real, usar 1620/1621.
- **1621 é ajustada sazonalmente:** serve para comparação trimestre contra trimestre
  (QoQ), não para somas anuais.
- **Importação:** vem com sinal positivo e precisa ser **subtraída** ao compor a demanda.
  A validação 14 confirma a identidade.
- **Séries diferentes entre tabelas:** 1620/5932 têm 22 séries, 1621 tem 21 e 1846 tem 23.
  Ao cruzar, usar `dim_serie` e tratar as ausências.
- **Revisões do IBGE:** as Contas Nacionais são revisadas; registrar a data de acesso e
  reexecutar o ETL quando necessário.
- **Formato do CSV:** UTF-8, delimitador vírgula e ponto decimal. No Power BI, importar com
  `Culture = en-US`. No Excel, abrir por *Dados → De Texto/CSV* (ou usar a planilha
  formatada gerada por `scripts/gerar_planilha.py`).
""")

code(r"""
gerados = ["fato_pib_volume.csv", "fato_pib_volume_sazonal.csv", "fato_pib_corrente.csv",
           "fato_pib_taxa.csv", "dim_tempo.csv", "dim_serie.csv", "log_etl.txt"]
for nome in gerados:
    caminho = RAIZ / "dados" / nome
    print(("[OK] " if caminho.exists() else "[FALTA] ") + nome)
""")

nb.cells = C
nbf.write(nb, DESTINO)
print("Notebook gravado em:", DESTINO, "| células:", len(C))
