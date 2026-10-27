#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o Power BI Project (.pbip) do projeto PIB Brasileiro.

Saída: powerbi/pib_brasileiro/
  pib_brasileiro.pbip
  pib_brasileiro.SemanticModel/   (TMDL: tabelas, relacionamentos, medidas)
  pib_brasileiro.Report/          (PBIR: páginas e visuais)

O modelo importa os CSV de dados/ via o parâmetro PastaDados. Se o projeto for
movido, altere o parâmetro em Transformar dados > Gerenciar parâmetros.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if not (RAIZ / "dados").exists():          # script fora do repositório do projeto
    RAIZ = RAIZ / "repo"
SAIDA = RAIZ / "powerbi" / "pib_brasileiro"
PASTA_DADOS = str(RAIZ / "dados").replace("\\", "/")

NOME = "pib_brasileiro"
TITULO = "PIB Brasileiro"

VIS_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json"
REPORT_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json"
PBIR_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json"
PBISM_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json"
PLATFORM_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json"
VERSION_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json"
PAGES_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json"

COR = {
    "azul": "#2A78D6",
    "laranja": "#EB6834",
    "agua": "#1BAF7A",
    "amarelo": "#EDA100",
    "rosa": "#E87BA4",
    "verde": "#008300",
    "roxo": "#6250D6",
    "vermelho": "#E34948",
    "tinta": "#0B0B0B",
    "tinta2": "#52514E",
    "mudo": "#898781",
    "fundo": "#F9F9F7",
    "cartao": "#FCFCFB",
    "borda": "#E1E0D9",
    "grade": "#E1E0D9",
}

FATOS = {
    "fato_pib_volume": "fato_pib_volume.csv",
    "fato_pib_volume_sazonal": "fato_pib_volume_sazonal.csv",
    "fato_pib_corrente": "fato_pib_corrente.csv",
    "fato_pib_taxa": "fato_pib_taxa.csv",
}

COLUNAS_FATO = [
    ("trimestre_txt", "string", True),
    ("serie", "string", True),
    ("valor_txt", "string", True),
    ("unidade", "string", True),
    ("valor", "double", False),
    ("trimestre", "int64", True),
    ("ano", "int64", True),
    ("data", "dateTime", True),
]


def uid(texto: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "pib-brasileiro:" + texto))


def escrever(caminho: Path, conteudo: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8")


def escrever_json(caminho: Path, obj) -> None:
    escrever(caminho, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Modelo semântico (TMDL)
# ---------------------------------------------------------------------------

def coluna(nome, tipo, oculta=False, formato=None, summarize="none", sort=None,
           chave=False) -> str:
    linhas = [f"\tcolumn {nome}"]
    if chave:
        linhas.append("\t\tisKey")
    linhas.append(f"\t\tdataType: {tipo}")
    if oculta:
        linhas.append("\t\tisHidden")
    if formato:
        linhas.append(f"\t\tformatString: {formato}")
    linhas.append(f"\t\tlineageTag: {uid('col:' + nome)}")
    linhas.append(f"\t\tsummarizeBy: {summarize}")
    linhas.append(f"\t\tsourceColumn: {nome}")
    if sort:
        linhas.append(f"\t\tsortByColumn: {sort}")
    linhas.append("")
    linhas.append("\t\tannotation SummarizationSetBy = Automatic")
    return "\n".join(linhas)


def particao(tabela: str, arquivo: str, tipos: list[tuple[str, str]]) -> str:
    """Partição M que lê um CSV com cultura en-US (ponto decimal)."""
    transformacoes = ", ".join(
        '{{ "{0}", {1} }}'.format(nome, tipo) for nome, tipo in tipos
    )
    return (
        f"\tpartition {tabela} = m\n"
        f"\t\tmode: import\n"
        f"\t\tsource = ```\n"
        f"\t\t\t\tlet\n"
        f'\t\t\t\t    Fonte = Csv.Document ( File.Contents ( PastaDados & "/{arquivo}" ), [ Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv ] ),\n'
        f"\t\t\t\t    Cabecalho = Table.PromoteHeaders ( Fonte, [ PromoteAllScalars = true ] ),\n"
        f"\t\t\t\t    Tipos = Table.TransformColumnTypes ( Cabecalho, {{ {transformacoes} }}, \"en-US\" )\n"
        f"\t\t\t\tin\n"
        f"\t\t\t\t    Tipos\n"
        f"\t\t```"
    )


def tabela_fato(nome: str, arquivo: str) -> str:
    partes = [f"table {nome}", f"\tlineageTag: {uid('tabela:' + nome)}", ""]
    for col, tipo, oculta in COLUNAS_FATO:
        formato = "yyyy-mm-dd" if tipo == "dateTime" else None
        partes.append(coluna(col, tipo, oculta, formato))
        partes.append("")
    partes.append(particao(nome, arquivo, [
        ("valor", "type number"),
        ("trimestre", "Int64.Type"),
        ("ano", "Int64.Type"),
        ("data", "type date"),
    ]))
    return "\n".join(partes) + "\n"


def tabela_calendario() -> str:
    partes = [
        "table dim_calendario",
        f"\tlineageTag: {uid('tabela:dim_calendario')}",
        "\tdataCategory: Time",
        "",
        coluna("data", "dateTime", formato="yyyy-mm-dd", chave=True),
        "",
        coluna("ano", "int64", formato="0"),
        "",
        coluna("trimestre", "int64", formato="0"),
        "",
        coluna("trimestre_txt", "string", sort="data"),
        "",
        coluna("ano_trimestre", "string", sort="data"),
        "",
        coluna("mes", "int64", formato="0"),
        "",
        coluna("nome_mes", "string"),
        "",
        coluna("ano_mes", "string"),
        "",
        coluna("dia", "int64", formato="0"),
        "",
        coluna("nome_dia_semana", "string"),
        "",
        coluna("eh_fim_trimestre", "boolean", oculta=True),
        "",
        coluna("ano_parcial", "boolean", oculta=True),
        "",
        particao("dim_calendario", "dim_calendario.csv", [
            ("ano", "Int64.Type"),
            ("trimestre", "Int64.Type"),
            ("mes", "Int64.Type"),
            ("dia", "Int64.Type"),
            ("data", "type date"),
            ("eh_fim_trimestre", "type logical"),
            ("ano_parcial", "type logical"),
        ]),
    ]
    return "\n".join(partes) + "\n"


def tabela_serie() -> str:
    partes = [
        "table dim_serie",
        f"\tlineageTag: {uid('tabela:dim_serie')}",
        "",
        coluna("serie", "string", sort="ordem_cor"),
        "",
        coluna("grupo", "string"),
        "",
        coluna("subgrupo", "string"),
        "",
        coluna("nivel", "string"),
        "",
        coluna("ordem", "int64", oculta=True, formato="0"),
        "",
        coluna("ordem_cor", "int64", oculta=True, formato="0"),
        "",
        coluna("ordem_origem", "int64", oculta=True, formato="0"),
        "",
        coluna("eh_pib", "boolean", oculta=True),
        "",
        coluna("eh_valor_adicionado", "boolean", oculta=True),
        "",
        coluna("eh_setor", "boolean", oculta=True),
        "",
        coluna("sinal", "int64", oculta=True, formato="0"),
        "",
        coluna("em_1620", "boolean", oculta=True),
        "",
        coluna("em_1621", "boolean", oculta=True),
        "",
        coluna("em_1846", "boolean", oculta=True),
        "",
        coluna("em_5932", "boolean", oculta=True),
        "",
        particao("dim_serie", "dim_serie.csv", [
            ("ordem", "Int64.Type"),
            ("ordem_cor", "Int64.Type"),
            ("ordem_origem", "Int64.Type"),
            ("sinal", "Int64.Type"),
            ("eh_pib", "type logical"),
            ("eh_valor_adicionado", "type logical"),
            ("eh_setor", "type logical"),
            ("em_1620", "type logical"),
            ("em_1621", "type logical"),
            ("em_1846", "type logical"),
            ("em_5932", "type logical"),
        ]),
    ]
    return "\n".join(partes) + "\n"


def medida(nome: str, dax: str, formato: str | None = None, pasta: str = "Medidas",
           descricao: str | None = None) -> str:
    linhas = []
    if descricao:
        linhas.append(f"\t/// {descricao}")
    linhas.append(f"\tmeasure '{nome}' = ```")
    for linha in dax.strip("\n").split("\n"):
        linhas.append("\t\t\t" + linha if linha.strip() else "")
    linhas.append("\t\t```")
    if formato:
        linhas.append(f"\t\tformatString: {formato}")
    linhas.append(f"\t\tdisplayFolder: {pasta}")
    linhas.append(f"\t\tlineageTag: {uid('medida:' + nome)}")
    return "\n".join(linhas)


MEDIDAS = {
    "01 PIB": [
        ("PIB real (índice)", """
CALCULATE (
    AVERAGE ( fato_pib_volume[valor] ),
    REMOVEFILTERS ( dim_serie ),
    dim_serie[eh_pib] = TRUE ()
)""", "0.00", "Índice médio de volume do PIB no contexto selecionado."),
        ("PIB real YoY %", """
VAR atual = [PIB real (índice)]
VAR anterior = CALCULATE ( [PIB real (índice)], SAMEPERIODLASTYEAR ( dim_calendario[data] ) )
RETURN DIVIDE ( atual - anterior, anterior )""", "0.0%", "Variação real contra o mesmo período do ano anterior."),
        ("PIB real QoQ % (sazonal)", """
VAR atual = CALCULATE (
    AVERAGE ( fato_pib_volume_sazonal[valor] ),
    REMOVEFILTERS ( dim_serie ),
    dim_serie[eh_pib] = TRUE ()
)
VAR anterior = CALCULATE (
    AVERAGE ( fato_pib_volume_sazonal[valor] ),
    REMOVEFILTERS ( dim_serie ),
    dim_serie[eh_pib] = TRUE (),
    DATEADD ( dim_calendario[data], -1, QUARTER )
)
RETURN DIVIDE ( atual - anterior, anterior )""", "0.0%", "Variação contra o trimestre anterior, com ajuste sazonal."),
        ("PIB nominal (R$)", """
CALCULATE (
    SUM ( fato_pib_corrente[valor] ),
    REMOVEFILTERS ( dim_serie ),
    dim_serie[eh_pib] = TRUE ()
) * 1000000""", "#,##0", "PIB a preços correntes, em reais."),
        ("PIB nominal (R$ trilhões)", """
DIVIDE ( [PIB nominal (R$)], 1E12 )""", "0.00", "PIB a preços correntes, em trilhões de reais."),
        ("Média móvel 4T", """
CALCULATE (
    AVERAGE ( fato_pib_volume[valor] ),
    REMOVEFILTERS ( dim_serie ),
    dim_serie[eh_pib] = TRUE (),
    DATESINPERIOD ( dim_calendario[data], MAX ( dim_calendario[data] ), -4, QUARTER )
)""", "0.00", "Média móvel de quatro trimestres do índice do PIB."),
        ("CAGR do período", """
VAR ano_ini = MIN ( dim_calendario[ano] )
VAR ano_fim = MAX ( dim_calendario[ano] )
VAR n = ano_fim - ano_ini
VAR valor_ini = CALCULATE ( [PIB real (índice)], dim_calendario[ano] = ano_ini )
VAR valor_fim = CALCULATE ( [PIB real (índice)], dim_calendario[ano] = ano_fim )
RETURN IF ( n > 0, ( valor_fim / valor_ini ) ^ ( 1 / n ) - 1 )""", "0.00%", "Crescimento composto anual do PIB real no período selecionado."),
        ("Inflação implícita (YoY)", """
VAR g_nominal = DIVIDE (
    CALCULATE ( [PIB nominal (R$)], dim_calendario[ano] = MAX ( dim_calendario[ano] ) ),
    CALCULATE ( [PIB nominal (R$)], dim_calendario[ano] = MAX ( dim_calendario[ano] ) - 1 )
) - 1
VAR g_real = [PIB real YoY %]
RETURN DIVIDE ( 1 + g_nominal, 1 + g_real ) - 1""", "0.00%", "Deflator implícito: crescimento nominal menos o real."),
    ],
    "02 Setores": [
        ("Índice de volume (série selecionada)", """
AVERAGE ( fato_pib_volume[valor] )""", "0.00", "Índice de volume da série em contexto (respeita o segmentador)."),
        ("Participação no VA %", """
VAR numerador = SUM ( fato_pib_corrente[valor] )
VAR denominador = CALCULATE (
    SUM ( fato_pib_corrente[valor] ),
    REMOVEFILTERS ( dim_serie ),
    dim_serie[eh_valor_adicionado] = TRUE ()
)
RETURN DIVIDE ( numerador, denominador )""", "0.0%", "Peso da série no valor adicionado a preços correntes."),
        ("Contribuição ao crescimento (p.p.)", """
VAR ano_atual = MAX ( dim_calendario[ano] )
VAR indice_atual = CALCULATE ( AVERAGE ( fato_pib_volume[valor] ), dim_calendario[ano] = ano_atual )
VAR indice_anterior = CALCULATE ( AVERAGE ( fato_pib_volume[valor] ), dim_calendario[ano] = ano_atual - 1 )
VAR crescimento = DIVIDE ( indice_atual, indice_anterior ) - 1
VAR peso_anterior = DIVIDE (
    CALCULATE ( SUM ( fato_pib_corrente[valor] ), dim_calendario[ano] = ano_atual - 1 ),
    CALCULATE (
        SUM ( fato_pib_corrente[valor] ),
        dim_calendario[ano] = ano_atual - 1,
        REMOVEFILTERS ( dim_serie ),
        dim_serie[eh_valor_adicionado] = TRUE ()
    )
)
RETURN crescimento * peso_anterior * 100""", "0.00", "Contribuição da série ao crescimento do valor adicionado, em pontos percentuais."),
        ("Crescimento 2026-T2 % (série)", """
VAR atual = CALCULATE (
    AVERAGE ( fato_pib_volume[valor] ),
    REMOVEFILTERS ( dim_calendario ),
    dim_calendario[ano] = 2026,
    dim_calendario[trimestre] = 2
)
VAR anterior = CALCULATE (
    AVERAGE ( fato_pib_volume[valor] ),
    REMOVEFILTERS ( dim_calendario ),
    dim_calendario[ano] = 2025,
    dim_calendario[trimestre] = 2
)
RETURN DIVIDE ( atual - anterior, anterior )""", "0.0%", "Variação real de cada série em 2026-T2, independente do filtro de ano."),
    ],
    "03 Demanda": [
        ("Demanda agregada (R$)", """
CALCULATE (
    SUMX (
        fato_pib_corrente,
        fato_pib_corrente[valor] * RELATED ( dim_serie[sinal] )
    ),
    REMOVEFILTERS ( dim_serie ),
    dim_serie[nivel] = "Componente"
) * 1000000""", "#,##0", "Consumo + governo + FBCF + estoque + exportações - importações."),
        ("Demanda agregada (R$ trilhões)", """
DIVIDE ( [Demanda agregada (R$)], 1E12 )""", "0.00", "Demanda agregada em trilhões de reais."),
    ],
    "04 Apoio": [
        ("PIB nominal 2025 (R$ trilhões)", """
CALCULATE (
    [PIB nominal (R$ trilhões)],
    REMOVEFILTERS ( dim_calendario ),
    dim_calendario[ano] = 2025
)""", "0.00", "Cartão do PIB nominal de 2025, independente de filtros."),
        ("PIB real 2025", """
CALCULATE (
    [PIB real YoY %],
    REMOVEFILTERS ( dim_calendario ),
    dim_calendario[ano] = 2025
)""", "0.0%", "Crescimento real de 2025, independente de filtros."),
        ("CAGR 2000–2025", """
CALCULATE (
    [CAGR do período],
    REMOVEFILTERS ( dim_calendario ),
    dim_calendario[ano] >= 2000,
    dim_calendario[ano] <= 2025
)""", "0.00%", "Crescimento composto de 2000 a 2025."),
        ("Serviços no VA 2025", """
CALCULATE (
    [Participação no VA %],
    REMOVEFILTERS ( dim_calendario ),
    REMOVEFILTERS ( dim_serie ),
    dim_calendario[ano] = 2025,
    dim_serie[serie] = "Serviços - total"
)""", "0.0%", "Peso dos serviços no valor adicionado de 2025."),
        ("PIB 2026-T2 YoY", """
CALCULATE (
    [PIB real YoY %],
    REMOVEFILTERS ( dim_calendario ),
    dim_calendario[ano] = 2026,
    dim_calendario[trimestre] = 2
)""", "0.0%", "Crescimento real do PIB em 2026-T2 contra 2025-T2."),
        ("PIB 2026-T2 QoQ", """
CALCULATE (
    [PIB real QoQ % (sazonal)],
    REMOVEFILTERS ( dim_calendario ),
    dim_calendario[ano] = 2026,
    dim_calendario[trimestre] = 2
)""", "0.0%", "Crescimento real do PIB em 2026-T2 contra 2026-T1."),
        ("Participação 2025 %", """
CALCULATE (
    [Participação no VA %],
    REMOVEFILTERS ( dim_calendario ),
    dim_calendario[ano] = 2025
)""", "0.0%", "Participação de cada setor no VA de 2025."),
        ("Contribuição 2025 (p.p.)", """
CALCULATE (
    [Contribuição ao crescimento (p.p.)],
    REMOVEFILTERS ( dim_calendario ),
    dim_calendario[ano] = 2025
)""", "0.00", "Contribuição de cada setor ao crescimento de 2025."),
        ("É ano parcial", """
VAR _ano = MAX ( dim_calendario[ano] )
VAR _trimestres = CALCULATE (
    DISTINCTCOUNT ( dim_calendario[trimestre] ),
    dim_calendario[ano] = _ano,
    REMOVEFILTERS ( dim_calendario )
)
RETURN IF ( _trimestres < 4, "Período parcial", BLANK () )""", None, "Aviso para não tratar 2026 como ano fechado."),
    ],
}


def tabela_medidas() -> str:
    partes = [
        "table _Medidas",
        f"\tlineageTag: {uid('tabela:_Medidas')}",
        "",
    ]
    for pasta, items in MEDIDAS.items():
        for nome, dax, formato, descricao in items:
            partes.append(medida(nome, dax, formato, pasta, descricao))
            partes.append("")
    partes.append(
        "\tpartition _Medidas = calculated\n"
        "\t\tmode: import\n"
        "\t\tsource = SELECTCOLUMNS ( { 1 }, \"_Medidas\", ''[Value] )"
    )
    return "\n".join(partes) + "\n"


def relacionamentos() -> str:
    linhas = []
    for fato in FATOS:
        for dim, chave in (("dim_calendario", "data"), ("dim_serie", "serie")):
            linhas.append(f"relationship {uid('rel:' + dim + ':' + fato)}")
            linhas.append(f"\tfromColumn: {fato}.{chave}")
            linhas.append(f"\ttoColumn: {dim}.{chave}")
            linhas.append("")
    return "\n".join(linhas).rstrip() + "\n"


def gerar_modelo() -> None:
    pasta = SAIDA / f"{NOME}.SemanticModel"
    escrever_json(pasta / ".platform", {
        "$schema": PLATFORM_SCHEMA,
        "metadata": {"type": "SemanticModel", "displayName": TITULO},
        "config": {"version": "2.0", "logicalId": uid("platform:model")},
    })
    escrever_json(pasta / "definition.pbism", {
        "$schema": PBISM_SCHEMA,
        "version": "4.2",
        "settings": {"qnaEnabled": False},
    })
    defs = pasta / "definition"
    escrever(defs / "database.tmdl",
            f"database {NOME}\n"
            f"\tid: {uid('database')}\n"
            "\tcompatibilityLevel: 1702\n"
            "\tcompatibilityMode: powerBI\n"
            "\tlanguage: 1033\n")
    escrever(defs / "expressions.tmdl",
            f'expression PastaDados = "{PASTA_DADOS}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
            f"\tlineageTag: {uid('param:PastaDados')}\n"
            "\tqueryGroup: Parameters\n\n"
            "\tannotation PBI_ResultType = Text\n")
    tabelas = ["dim_calendario", "dim_serie"] + list(FATOS) + ["_Medidas"]
    model = [
        f"model {NOME}",
        "\tculture: pt-BR",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tdiscourageImplicitMeasures",
        "\tsourceQueryCulture: en-US",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        "queryGroup Parameters",
        "",
        "\tannotation PBI_QueryGroupOrder = 0",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        'annotation PBI_QueryOrder = ["PastaDados","dim_calendario","dim_serie","fato_pib_volume","fato_pib_volume_sazonal","fato_pib_corrente","fato_pib_taxa","_Medidas"]',
        "",
    ]
    for t in tabelas:
        model.append(f"ref table {t}")
    escrever(defs / "model.tmdl", "\n".join(model) + "\n")
    escrever(defs / "relationships.tmdl", relacionamentos())
    (defs / "tables").mkdir(parents=True, exist_ok=True)
    escrever(defs / "tables" / "dim_calendario.tmdl", tabela_calendario())
    escrever(defs / "tables" / "dim_serie.tmdl", tabela_serie())
    for nome, arquivo in FATOS.items():
        escrever(defs / "tables" / f"{nome}.tmdl", tabela_fato(nome, arquivo))
    escrever(defs / "tables" / "_Medidas.tmdl", tabela_medidas())


# ---------------------------------------------------------------------------
# Relatório (PBIR)
# ---------------------------------------------------------------------------

def lit(valor: str) -> dict:
    return {"expr": {"Literal": {"Value": valor}}}


def cor_solida(hexcor: str) -> dict:
    return {"solid": {"color": lit("'" + hexcor + "'")}}


def booleano(valor: bool) -> dict:
    return lit("true" if valor else "false")


def numero(valor) -> dict:
    return lit(f"{valor}D")


def inteiro(valor) -> dict:
    return lit(f"{valor}L")


def texto(valor: str) -> dict:
    return lit("'" + valor.replace("'", "''") + "'")


def coluna_ref(tabela: str, coluna: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": coluna}}


def medida_ref(tabela: str, nome: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": nome}}


def proj_coluna(tabela: str, coluna: str) -> dict:
    return {
        "field": coluna_ref(tabela, coluna),
        "queryRef": f"{tabela}.{coluna}",
        "nativeQueryRef": coluna,
        "active": True,
    }


def proj_medida(nome: str, rotulo: str | None = None) -> dict:
    p = {
        "field": medida_ref("_Medidas", nome),
        "queryRef": f"_Medidas.{nome}",
        "nativeQueryRef": rotulo or nome,
    }
    if rotulo:
        p["displayName"] = rotulo
    return p


def titulo_visual(titulo: str, tamanho=11) -> dict:
    return {
        "title": [{
            "properties": {
                "show": booleano(True),
                "text": texto(titulo),
                "fontSize": numero(tamanho),
                "fontColor": cor_solida(COR["tinta2"]),
                "bold": booleano(True),
                "alignment": texto("left"),
            }
        }]
    }


def container(cor_fundo: str = COR["cartao"]) -> dict:
    return {
        "background": [{"properties": {
            "show": booleano(True),
            "color": cor_solida(cor_fundo),
            "transparency": numero(0),
        }}],
        "border": [{"properties": {
            "show": booleano(True),
            "color": cor_solida(COR["borda"]),
            "radius": inteiro(8),
        }}],
        "visualHeader": [{"properties": {"show": booleano(False)}}],
        "padding": [{"properties": {
            "top": numero(8), "bottom": numero(8),
            "left": numero(8), "right": numero(8),
        }}],
    }


def junta(*partes: dict) -> dict:
    out = {}
    for p in partes:
        out.update(p)
    return out


def visual(nome: str, tipo: str, x, y, w, h, query=None, objects=None,
           vco=None, z=0, tab=0) -> dict:
    v = {"visualType": tipo}
    if query is not None:
        v["query"] = query
    if objects is not None:
        v["objects"] = objects
    if vco is not None:
        v["visualContainerObjects"] = vco
    v["drillFilterOtherVisuals"] = True
    return {
        "$schema": VIS_SCHEMA,
        "name": nome,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": tab},
        "visual": v,
    }


def textbox(nome, x, y, w, h, paragrafos, alinhamento="left", z=1000) -> dict:
    """paragrafos: lista de listas de (texto, estilo)."""
    paras = []
    for runs in paragrafos:
        textruns = []
        for conteudo, estilo in runs:
            ts = {
                "fontFamily": estilo.get("familia", "Segoe UI"),
                "fontSize": f"{estilo.get('tamanho', 11)}pt",
                "color": estilo.get("cor", COR["tinta"]),
            }
            if estilo.get("negrito"):
                ts["fontWeight"] = "bold"
            if estilo.get("italico"):
                ts["fontStyle"] = "italic"
            textruns.append({"value": conteudo, "textStyle": ts})
        paras.append({"textRuns": textruns, "horizontalTextAlignment": alinhamento})
    objects = {"general": [{"properties": {"paragraphs": paras}}]}
    vco = {
        "title": [{"properties": {"show": booleano(False)}}],
        "background": [{"properties": {"show": booleano(False)}}],
        "border": [{"properties": {"show": booleano(False)}}],
        "visualHeader": [{"properties": {"show": booleano(False)}}],
        "padding": [{"properties": {
            "top": numero(0), "bottom": numero(0),
            "left": numero(0), "right": numero(0),
        }}],
    }
    return visual(nome, "textbox", x, y, w, h, objects=objects, vco=vco, z=z)


def cartao(nome, x, y, w, h, medida, rotulo, accent, tamanho_valor=28) -> dict:
    query = {"queryState": {"Data": {"projections": [proj_medida(medida)]}}}
    objects = {
        "value": [{"properties": {
            "fontSize": numero(tamanho_valor),
            "fontColor": cor_solida(accent),
            "bold": booleano(True),
        }, "selector": {"id": "default"}}],
        "label": [{"properties": {
            "text": texto(rotulo),
            "fontSize": numero(10),
            "fontColor": cor_solida(COR["tinta2"]),
        }, "selector": {"id": "default"}}],
        "accentBar": [{"properties": {
            "show": booleano(True),
            "position": texto("Left"),
            "width": numero(4),
            "color": cor_solida(accent),
        }, "selector": {"id": "default"}}],
        "outline": [{"properties": {"show": booleano(False)}, "selector": {"id": "default"}}],
        "layout": [{"properties": {
            "topOuterMargin": numero(0), "bottomOuterMargin": numero(0),
            "leftOuterMargin": numero(0), "rightOuterMargin": numero(0),
            "paddingUniform": numero(0),
        }, "selector": {"id": "default"}}],
        "padding": [{"properties": {
            "leftMargin": numero(12), "rightMargin": numero(8),
            "topMargin": numero(0), "bottomMargin": numero(0),
        }, "selector": {"id": "default"}}],
    }
    vco = {
        "background": [{"properties": {
            "show": booleano(True), "color": cor_solida("#FFFFFF"), "transparency": numero(0),
        }}],
        "border": [{"properties": {
            "show": booleano(True), "color": cor_solida(COR["borda"]), "radius": inteiro(8),
        }}],
        "visualHeader": [{"properties": {"show": booleano(False)}}],
        "title": [{"properties": {"show": booleano(False)}}],
        "padding": [{"properties": {
            "top": numero(0), "bottom": numero(0), "left": numero(0), "right": numero(0),
        }, "selector": {"id": "default"}}],
        "spacing": [{"properties": {
            "customizeSpacing": booleano(True), "verticalSpacing": numero(2),
        }, "selector": {"id": "default"}}],
    }
    return visual(nome, "cardVisual", x, y, w, h, query=query, objects=objects, vco=vco)


def query_barras(categoria, medidas, legenda=None) -> dict:
    qs = {}
    if categoria:
        qs["Category"] = {"projections": [proj_coluna(*categoria)]}
    qs["Y"] = {"projections": [proj_medida(m, r) for m, r in medidas]}
    if legenda:
        qs["Series"] = {"projections": [proj_coluna(*legenda)]}
    return {"queryState": qs}


def barras(nome, x, y, w, h, categoria, medidas, cor, titulo, horizontal=True,
           legenda=None, ordenar_desc=True, filtro_nivel=None, rotulos=True,
           tipo=None) -> dict:
    tipo = tipo or ("barChart" if horizontal else "columnChart")
    query = query_barras(categoria, medidas, legenda)
    if ordenar_desc:
        campo = medida_ref("_Medidas", medidas[0][0])
        query["sortDefinition"] = {"sort": [{"field": campo, "direction": "Descending"}]}
    objects = {
        "labels": [{"properties": {
            "show": booleano(rotulos),
            "labelPosition": texto("OutsideEnd"),
            "fontSize": numero(10),
            "color": cor_solida(COR["tinta"]),
        }}],
        "valueAxis": [{"properties": {"show": booleano(False)}}],
        "categoryAxis": [{"properties": {
            "show": booleano(True), "fontSize": numero(9), "labelColor": cor_solida(COR["tinta2"]),
        }}],
        "legend": [{"properties": {"show": booleano(bool(legenda)), "position": texto("Bottom"), "fontSize": numero(9)}}],
    }
    if not legenda:
        objects["dataPoint"] = [{"properties": {"fill": cor_solida(cor), "borderShow": booleano(False)}}]
    vco = junta(container(), titulo_visual(titulo))
    vis = visual(nome, tipo, x, y, w, h, query=query, objects=objects, vco=vco)
    if filtro_nivel:
        vis["filterConfig"] = filtro_coluna("dim_serie", "nivel", filtro_nivel)
    return vis


def linha(nome, x, y, w, h, categoria, medidas, titulo, legenda=None,
          cor=None, area=False, filtro_nivel=None, rotulos=False) -> dict:
    query = query_barras(categoria, medidas, legenda)
    objects = {
        "lineStyles": [{"properties": {
            "strokeWidth": numero(2),
            "lineChartType": texto("smooth"),
            "interpolationSmooth": texto("monotoneX"),
            "areaShow": booleano(area),
            "showMarker": booleano(False),
        }}],
        "labels": [{"properties": {"show": booleano(rotulos)}}],
        "legend": [{"properties": {
            "show": booleano(bool(legenda)), "position": texto("Top"),
            "fontSize": numero(9), "labelColor": cor_solida(COR["tinta2"]),
        }}],
        "categoryAxis": [{"properties": {
            "show": booleano(True), "fontSize": numero(8), "labelColor": cor_solida(COR["tinta2"]),
        }}],
        "valueAxis": [{"properties": {
            "show": booleano(True), "fontSize": numero(8), "labelColor": cor_solida(COR["mudo"]),
            "gridlineShow": booleano(True), "gridlineColor": cor_solida(COR["grade"]),
        }}],
    }
    if cor and not legenda:
        objects["dataPoint"] = [{"properties": {"defaultColor": cor_solida(cor)}}]
    vco = junta(container(), titulo_visual(titulo))
    vis = visual(nome, "lineChart", x, y, w, h, query=query, objects=objects, vco=vco)
    if filtro_nivel:
        vis["filterConfig"] = filtro_coluna("dim_serie", "nivel", filtro_nivel)
    return vis


def filtro_coluna(tabela: str, coluna: str, valor: str) -> dict:
    return {"filters": [{
        "name": uid(f"filtro:{tabela}:{coluna}:{valor}")[:20],
        "field": coluna_ref(tabela, coluna),
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "t", "Entity": tabela, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {
                    "Expression": {"SourceRef": {"Source": "t"}},
                    "Property": coluna,
                }}],
                "Values": [[{"Literal": {"Value": "'" + valor + "'"}}]],
            }}}],
        },
        "howCreated": "User",
    }]}


def tabela(nome, x, y, w, h, colunas, medidas, titulo) -> dict:
    projs = [proj_coluna(*c) for c in colunas] + [proj_medida(m, r) for m, r in medidas]
    query = {"queryState": {"Values": {"projections": projs}}}
    objects = {
        "columnHeaders": [{"properties": {
            "autoSizeColumnWidth": booleano(True),
            "columnAdjustment": texto("growToFit"),
            "bold": booleano(True),
            "fontSize": numero(10),
            "backColor": cor_solida("#F3F2F1"),
            "fontColor": cor_solida(COR["tinta2"]),
        }}],
        "values": [{"properties": {
            "fontSize": numero(10),
            "backColorPrimary": cor_solida("#FFFFFF"),
            "backColorSecondary": cor_solida("#FAFAFA"),
            "fontColorPrimary": cor_solida(COR["tinta"]),
            "fontColorSecondary": cor_solida(COR["tinta"]),
        }}],
        "grid": [{"properties": {"gridHorizontal": booleano(True), "gridlineColor": cor_solida(COR["grade"]), "rowPadding": numero(6)}}],
        "total": [{"properties": {"show": booleano(False)}}],
    }
    vco = junta(container(), titulo_visual(titulo))
    return visual(nome, "tableEx", x, y, w, h, query=query, objects=objects, vco=vco)


def matriz(nome, x, y, w, h, linhas, colunas, medidas, titulo, filtro_nivel=None) -> dict:
    qs = {"Rows": {"projections": [proj_coluna(*c) for c in linhas]}}
    if colunas:
        qs["Columns"] = {"projections": [proj_coluna(*c) for c in colunas]}
    qs["Values"] = {"projections": [proj_medida(m, r) for m, r in medidas]}
    objects = {
        "rowHeaders": [{"properties": {"bold": booleano(True), "fontSize": numero(10), "fontColor": cor_solida(COR["tinta2"])}}],
        "columnHeaders": [{"properties": {"fontSize": numero(8), "fontColor": cor_solida(COR["tinta2"])}}],
        "values": [{"properties": {
            "fontSize": numero(9),
            "backColorPrimary": cor_solida("#FFFFFF"),
            "backColorSecondary": cor_solida("#FAFAFA"),
            "fontColorPrimary": cor_solida(COR["tinta"]),
            "fontColorSecondary": cor_solida(COR["tinta"]),
        }}],
        "subTotals": [{"properties": {
            "rowSubtotals": booleano(False),
            "columnSubtotals": booleano(False),
        }}],
    }
    vco = junta(container(), titulo_visual(titulo))
    vis = visual(nome, "pivotTable", x, y, w, h, query={"queryState": qs}, objects=objects, vco=vco)
    if filtro_nivel:
        vis["filterConfig"] = filtro_coluna("dim_serie", "nivel", filtro_nivel)
    return vis


def segmentador(nome, x, y, w, h, tabela_nome, coluna, titulo) -> dict:
    query = {"queryState": {"Values": {"projections": [proj_coluna(tabela_nome, coluna)]}}}
    objects = {
        "data": [{"properties": {"mode": texto("Dropdown")}}],
        "header": [{"properties": {"show": booleano(True), "text": texto(titulo)}}],
    }
    vco = {
        "padding": [{"properties": {
            "top": numero(8), "bottom": numero(8), "left": numero(8), "right": numero(8),
        }}],
        "background": [{"properties": {"show": booleano(True), "color": cor_solida("#FFFFFF")}}],
        "border": [{"properties": {"show": booleano(True), "color": cor_solida(COR["borda"]), "radius": inteiro(8)}}],
        "visualHeader": [{"properties": {"show": booleano(False)}}],
        "title": [{"properties": {"show": booleano(False)}}],
    }
    return visual(nome, "slicer", x, y, w, h, query=query, objects=objects, vco=vco)


def botao(nome, x, y, w, h, rotulo, destino, ativo=False) -> dict:
    preenchimento = COR["azul"] if ativo else "#FFFFFF"
    cor_texto = "#FFFFFF" if ativo else COR["tinta2"]
    objects = {
        "text": [
            {"properties": {"show": booleano(True)}},
            {"properties": {
                "text": texto(rotulo),
                "fontSize": numero(9),
                "fontColor": cor_solida(cor_texto),
                "horizontalAlignment": texto("center"),
            }, "selector": {"id": "default"}},
        ],
        "icon": [{"properties": {"show": booleano(False)}}],
        "fill": [
            {"properties": {"show": booleano(True)}},
            {"properties": {"fillColor": cor_solida(preenchimento)}, "selector": {"id": "default"}},
        ],
        "outline": [
            {"properties": {"show": booleano(True)}},
            {"properties": {"lineColor": cor_solida(COR["borda"]), "weight": numero(1)}, "selector": {"id": "default"}},
        ],
        "shape": [
            {"properties": {"tileShape": texto("rectangleRounded"), "roundEdge": inteiro(6)}},
            {"properties": {"tileShape": texto("rectangleRounded")}, "selector": {"id": "default"}},
        ],
    }
    vco = {
        "background": [{"properties": {"show": booleano(False)}}],
        "border": [{"properties": {"show": booleano(False)}}],
        "visualLink": [{"properties": {
            "show": booleano(True),
            "type": texto("PageNavigation"),
            "navigationSection": texto(destino),
            "tooltip": texto(rotulo),
        }}],
    }
    return visual(nome, "actionButton", x, y, w, h, objects=objects, vco=vco)


PAGINAS = [
    ("capa", "Capa"),
    ("visao_geral", "Visão geral"),
    ("temporal", "Temporal"),
    ("setores", "Setores"),
    ("sintese", "Síntese"),
]


def cabecalho(pagina: str, titulo: str, subtitulo: str) -> list[dict]:
    vis = [
        textbox(f"titulo_{pagina}", 32, 10, 620, 38,
                [[(titulo, {"tamanho": 22, "negrito": True, "familia": "Segoe UI Semibold"})]]),
        textbox(f"sub_{pagina}", 32, 50, 680, 18,
                [[(subtitulo, {"tamanho": 10, "cor": COR["tinta2"]})]]),
    ]
    largura = 96
    gap = 8
    x0 = 1280 - 32 - (len(PAGINAS) * largura + (len(PAGINAS) - 1) * gap)
    for i, (alvo, rotulo) in enumerate(PAGINAS):
        vis.append(botao(f"nav_{pagina}_{alvo}", x0 + i * (largura + gap), 18,
                         largura, 28, rotulo, alvo, ativo=(alvo == pagina)))
    return vis


def rodape(pagina: str) -> dict:
    return textbox(
        f"rodape_{pagina}", 32, 688, 1216, 18,
        [[("Fonte: IBGE — SIDRA, tabelas 1620, 1621, 1846 e 5932 (Contas Nacionais Trimestrais). "
           "Acesso em 20/10/2026. Projeto BI · Tema 12 · Evandro Miguel.", {"tamanho": 8, "cor": COR["mudo"]})]],
    )


def pagina_capa() -> list[dict]:
    vis = [
        textbox("capa_titulo", 80, 150, 900, 72,
                [[("PIB Brasileiro", {"tamanho": 44, "negrito": True, "familia": "Segoe UI Semibold"})]]),
        textbox("capa_sub", 80, 226, 900, 30,
                [[("Evolução e participação setorial · 2000-T1 a 2026-T2",
                   {"tamanho": 20, "cor": COR["tinta2"]})]]),
        textbox("capa_pergunta", 80, 296, 780, 54,
                [[("Como o PIB brasileiro evoluiu e como os principais setores participaram desse desempenho?",
                   {"tamanho": 14})]]),
        cartao("capa_kpi", 80, 380, 320, 112, "PIB nominal 2025 (R$ trilhões)",
               "PIB nominal 2025 · R$ trilhões", COR["azul"], 32),
        textbox("capa_nota", 80, 506, 520, 40,
                [[("Dados públicos. O relatório usa índices de volume para o crescimento real e valores "
                   "correntes apenas para participação e nível.", {"tamanho": 9, "cor": COR["tinta2"]})]]),
    ]
    destinos = [("visao_geral", "Visão geral"), ("temporal", "Temporal"),
                ("setores", "Setores"), ("sintese", "Síntese")]
    for i, (alvo, rotulo) in enumerate(destinos):
        vis.append(botao(f"capa_botao_{alvo}", 80 + i * 196, 566, 180, 40, rotulo, alvo, ativo=(i == 0)))
    vis.append(rodape("capa"))
    return vis


def pagina_visao_geral() -> list[dict]:
    vis = cabecalho("visao_geral", "Visão geral",
                    "O nível de atividade, o crescimento e o peso de cada setor")
    cards = [
        ("PIB nominal 2025 (R$ trilhões)", "PIB nominal 2025 · R$ trilhões", COR["azul"]),
        ("PIB real 2025", "PIB real 2025 · variação anual", COR["agua"]),
        ("CAGR 2000–2025", "Crescimento real médio · % a.a.", COR["laranja"]),
        ("Serviços no VA 2025", "Serviços no valor adicionado · 2025", COR["roxo"]),
    ]
    for i, (medida_nome, rotulo, accent) in enumerate(cards):
        vis.append(cartao(f"vg_card_{i}", 32 + i * 308, 80, 292, 96, medida_nome, rotulo, accent))
    vis.append(barras(
        "vg_participacao", 32, 196, 592, 220,
        ("dim_calendario", "ano"),
        [("Participação no VA %", "Participação no VA")],
        COR["azul"], "Composição do valor adicionado por ano",
        horizontal=False, legenda=("dim_serie", "serie"), ordenar_desc=False,
        tipo="hundredPercentStackedColumnChart", filtro_nivel="Setor", rotulos=False,
    ))
    vis.append(barras(
        "vg_contribuicao", 656, 196, 592, 220,
        ("dim_serie", "serie"),
        [("Contribuição 2025 (p.p.)", "Contribuição 2025")],
        COR["azul"], "Contribuição ao crescimento de 2025 (p.p.)",
        horizontal=True, filtro_nivel="Setor",
    ))
    vis.append(matriz(
        "vg_tabela", 32, 432, 1216, 236,
        [("dim_serie", "serie")], [],
        [("Participação 2025 %", "Participação 2025"),
         ("Contribuição 2025 (p.p.)", "Contribuição 2025 (p.p.)"),
         ("Crescimento 2026-T2 % (série)", "Crescimento 2026-T2")],
        "Setores em números",
        filtro_nivel="Setor",
    ))
    vis.append(rodape("visao_geral"))
    return vis


def pagina_temporal() -> list[dict]:
    vis = cabecalho("temporal", "Análise temporal",
                    "2000-T1 a 2026-T2 · 2026 tem apenas dois trimestres")
    vis.append(linha(
        "tmp_pib", 32, 80, 700, 270,
        ("dim_calendario", "data"),
        [("PIB real (índice)", "PIB real (índice)")],
        "PIB real — índice de volume (1995 = 100)",
        cor=COR["azul"], area=True,
    ))
    vis.append(barras(
        "tmp_yoy", 748, 80, 500, 270,
        ("dim_calendario", "ano"),
        [("PIB real YoY %", "PIB real YoY")],
        COR["azul"], "Crescimento real por ano (%)",
        horizontal=False, rotulos=False, ordenar_desc=False,
    ))
    vis.append(linha(
        "tmp_setores", 32, 366, 700, 276,
        ("dim_calendario", "ano"),
        [("Índice de volume (série selecionada)", "Índice de volume")],
        "Índice de volume por setor",
        legenda=("dim_serie", "serie"), filtro_nivel="Setor",
    ))
    vis.append(linha(
        "tmp_qoq", 748, 366, 500, 276,
        ("dim_calendario", "data"),
        [("PIB real QoQ % (sazonal)", "PIB real QoQ")],
        "Variação contra o trimestre anterior (%)",
        cor=COR["laranja"],
    ))
    vis.append(rodape("temporal"))
    return vis


def pagina_setores() -> list[dict]:
    vis = cabecalho("setores", "Setores",
                    "Quem puxa o crescimento e como o peso muda ao longo do tempo")
    vis.append(segmentador("st_ano", 32, 80, 180, 80, "dim_calendario", "ano", "Ano"))
    vis.append(segmentador("st_grupo", 228, 80, 180, 80, "dim_serie", "grupo", "Grupo"))
    vis.append(matriz(
        "st_matriz", 32, 176, 760, 464,
        [("dim_calendario", "ano")], [("dim_serie", "serie")],
        [("Contribuição ao crescimento (p.p.)", "Contribuição (p.p.)")],
        "Contribuição ao crescimento por setor e ano",
        filtro_nivel="Setor",
    ))
    vis.append(barras(
        "st_ranking", 808, 80, 440, 300,
        ("dim_serie", "subgrupo"),
        [("Crescimento 2026-T2 % (série)", "Crescimento 2026-T2")],
        COR["azul"], "Crescimento em 2026-T2 por subsetor",
        horizontal=True, filtro_nivel="Subsetor",
    ))
    vis.append(linha(
        "st_participacao", 808, 396, 440, 244,
        ("dim_calendario", "ano"),
        [("Participação no VA %", "Participação no VA")],
        "Participação no valor adicionado por ano",
        legenda=("dim_serie", "serie"), filtro_nivel="Setor",
    ))
    vis.append(rodape("setores"))
    return vis


def pagina_sintese() -> list[dict]:
    vis = cabecalho("sintese", "Síntese",
                    "Três achados e uma recomendação para o público do relatório")
    achar = [
        ("1 · Serviços sustentam o crescimento",
         "O setor responde por 69,5% do valor adicionado e contribuiu com +1,25 p.p. "
         "do crescimento de 2025. É o setor decisivo para o nível de atividade, mas cresce "
         "a taxas moderadas: 2,41% a.a. entre 2000 e 2025.", COR["azul"]),
        ("2 · Agropecuária é pequena, mas a mais dinâmica",
         "São 7,1% do valor adicionado e +0,78 p.p. em 2025. No longo prazo cresce 3,71% a.a., "
         "o maior ritmo entre os três setores; em 2026-T2 avança 6,8%.", COR["agua"]),
        ("3 · Indústria perde peso e a transformação estagna",
         "A indústria caiu de 26,7% para 23,4% do valor adicionado em 25 anos e contribuiu com "
         "apenas +0,35 p.p. em 2025. Em 2026-T2, a transformação recua 0,9% enquanto a extrativa "
         "cresce 12,0%.", COR["laranja"]),
    ]
    for i, (titulo, corpo, accent) in enumerate(achar):
        vis.append(textbox(
            f"sintese_achado_{i}", 32 + i * 400, 96, 384, 250,
            [
                [(titulo, {"tamanho": 16, "negrito": True, "cor": accent})],
                [(corpo, {"tamanho": 12, "cor": COR["tinta"]})],
            ],
        ))
    vis.append(textbox(
        "sintese_recomendacao", 32, 372, 760, 290,
        [
            [("Recomendação", {"tamanho": 16, "negrito": True, "cor": COR["roxo"]})],
            [("Priorizar a leitura do crescimento por setor, e não apenas o número do PIB. "
              "O PIB de 2025 cresceu 2,29%, mas a composição mostra serviços sustentando o nível "
              "e agropecuária puxando a margem. Para 2026, o avanço é positivo, porém concentrado "
              "em agropecuária, extrativa e informação/comunicação — a transformação industrial "
              "segue em queda.", {"tamanho": 12, "cor": COR["tinta"]})],
            [("Como usar: comece pela visão geral para o nível, passe pela análise temporal para "
              "o ciclo e pela página de setores para identificar os motores. O ano de 2026 é "
              "parcial (apenas T1 e T2) e não deve ser lido como ano fechado.",
              {"tamanho": 10, "cor": COR["tinta2"]})],
        ],
    ))
    vis.append(textbox(
        "sintese_numeros", 808, 372, 440, 290,
        [
            [("Números para lembrar", {"tamanho": 16, "negrito": True, "cor": COR["tinta"]})],
            [("PIB nominal 2025: R$ 12,74 trilhões", {"tamanho": 12})],
            [("PIB real 2025: +2,29%", {"tamanho": 12})],
            [("CAGR 2000–2025: 2,26% a.a.", {"tamanho": 12})],
            [("PIB 2026-T2: +2,0% YoY · +0,48% QoQ", {"tamanho": 12})],
            [("Serviços no VA: 69,5%", {"tamanho": 12})],
            [("Fonte: IBGE — SIDRA. Acesso em 20/10/2026.", {"tamanho": 9, "cor": COR["mudo"]})],
        ],
    ))
    vis.append(rodape("sintese"))
    return vis


CONSTRUTORES = {
    "capa": pagina_capa,
    "visao_geral": pagina_visao_geral,
    "temporal": pagina_temporal,
    "setores": pagina_setores,
    "sintese": pagina_sintese,
}


def gerar_relatorio() -> None:
    pasta = SAIDA / f"{NOME}.Report"
    escrever_json(pasta / ".platform", {
        "$schema": PLATFORM_SCHEMA,
        "metadata": {"type": "Report", "displayName": TITULO},
        "config": {"version": "2.0", "logicalId": uid("platform:report")},
    })
    escrever_json(pasta / "definition.pbir", {
        "$schema": PBIR_SCHEMA,
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NOME}.SemanticModel"}},
    })
    defs = pasta / "definition"
    escrever_json(defs / "version.json", {"$schema": VERSION_SCHEMA, "version": "2.0.0"})
    escrever_json(defs / "pages" / "pages.json", {
        "$schema": PAGES_SCHEMA,
        "pageOrder": [p for p, _ in PAGINAS],
        "activePageName": PAGINAS[0][0],
    })
    escrever_json(defs / "report.json", {
        "$schema": REPORT_SCHEMA,
        "themeCollection": {
            "customTheme": {
                "name": "tema_pib.json",
                "reportVersionAtImport": {"visual": "2.1.0", "report": "2.1.0", "page": "2.0.0"},
                "type": "RegisteredResources",
            }
        },
        "resourcePackages": [{
            "name": "RegisteredResources",
            "type": "RegisteredResources",
            "items": [{"name": "tema_pib.json", "path": "tema_pib.json", "type": "CustomTheme"}],
        }],
        "settings": {"useStylableVisualContainerHeader": True},
    })
    for nome, titulo in PAGINAS:
        pagina = {
            "$schema": PAGE_SCHEMA,
            "name": nome,
            "displayName": titulo,
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
            "objects": {"background": [{"properties": {
                "color": cor_solida(COR["fundo"]),
                "transparency": numero(0),
            }}]},
        }
        escrever_json(defs / "pages" / nome / "page.json", pagina)
        for i, vis in enumerate(CONSTRUTORES[nome]()):
            vis["position"]["z"] = i
            vis["position"]["tabOrder"] = i
            escrever_json(defs / "pages" / nome / "visuals" / vis["name"] / "visual.json", vis)
    # Tema registrado
    tema = json.loads((RAIZ / "powerbi" / "tema_pib.json").read_text(encoding="utf-8"))
    escrever_json(pasta / "StaticResources" / "RegisteredResources" / "tema_pib.json", tema)


def gerar_pbip() -> None:
    escrever_json(SAIDA / f"{NOME}.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NOME}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    })


def main() -> int:
    gerar_modelo()
    gerar_relatorio()
    gerar_pbip()
    paginas = len(PAGINAS)
    visuais = sum(len(CONSTRUTORES[p]()) for p, _ in PAGINAS)
    print(f"[OK] projeto gerado em {SAIDA}")
    print(f"[OK] {paginas} páginas, {visuais} visuais, 8 relacionamentos")
    print(f"[OK] parâmetro PastaDados = {PASTA_DADOS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
