#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Projeto BI - Tema 12 (PIB brasileiro)
ETL das tabelas do SIDRA/IBGE para formato longo (tidy), pronto para Power BI.

Entrada : CSV exportados do SIDRA no formato largo (uma linha de dados, colunas
          agrupadas por trimestre e, dentro de cada trimestre, por série).
Saída   : um CSV longo por tabela + dimensões de tempo e de série + log de ETL.

Uso (a partir da raiz do projeto):
    python scripts/transformar_sidra.py

Por padrão lê de dados_originais/ e grava em dados/, resolvidos a partir da pasta
do próprio script. Para apontar outras pastas:
    python scripts/transformar_sidra.py --indir outra/pasta --outdir saida

Tabelas:
    1620 - índice de volume trimestral, série encadeada (base 1995 = 100)
    1621 - mesmo índice, com ajuste sazonal
    1846 - valores a preços correntes (R$ milhões)
    5932 - taxas de variação do volume (taxa trimestral vs. mesmo trimestre
           do ano anterior)
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração das tabelas
# ---------------------------------------------------------------------------
TABELAS = {
    "1620": {
        "arquivo": "tabela1620.csv",
        "saida": "fato_pib_volume.csv",
        "descricao": "Série encadeada do índice de volume trimestral (Base: média 1995 = 100)",
        "unidade": "Número-índice",
        "url": "https://sidra.ibge.gov.br/tabela/1620",
    },
    "1621": {
        "arquivo": "tabela1621.csv",
        "saida": "fato_pib_volume_sazonal.csv",
        "descricao": "Série encadeada do índice de volume trimestral com ajuste sazonal (Base: média 1995 = 100)",
        "unidade": "Número-índice",
        "url": "https://sidra.ibge.gov.br/tabela/1621",
    },
    "1846": {
        "arquivo": "tabela1846.csv",
        "saida": "fato_pib_corrente.csv",
        "descricao": "Valores a preços correntes (R$ milhões)",
        "unidade": "Milhões de Reais",
        "url": "https://sidra.ibge.gov.br/tabela/1846",
    },
    "5932": {
        "arquivo": "tabela5932.csv",
        "saida": "fato_pib_taxa.csv",
        "descricao": "Taxa trimestral de variação do volume (em relação ao mesmo período do ano anterior)",
        "unidade": "%",
        "url": "https://sidra.ibge.gov.br/tabela/5932",
    },
}

COLUNAS = [
    "trimestre_txt",
    "serie",
    "valor_txt",
    "unidade",
    "valor",
    "trimestre",
    "ano",
    "data",
]

RE_TRIMESTRE = re.compile(r"^\s*(\d)º\s+trimestre\s+(\d{4})\s*$")
VALORES_ESPECIAIS = {"", "...", "..", "X", "-", "–", "—"}

# Raiz do projeto (a pasta que contém scripts/ e dados_originais/)
RAIZ = Path(__file__).resolve().parent.parent

# Data em que os CSV foram baixados do SIDRA (registrada na ficha de fontes).
# Mantida fixa para que o log não mude a cada reexecução.
DATA_ACESSO = "2026-10-20"

# Classificação das séries para a dimensão (modelo em estrela)
CLASSIFICACAO = {
    "Agropecuária - total": ("Agropecuária", "Agropecuária", "Setor", 1),
    "Indústria - total": ("Indústria", "Indústria", "Setor", 2),
    "Indústrias extrativas": ("Indústria", "Extrativa", "Subsetor", 21),
    "Indústrias de transformação": ("Indústria", "Transformação", "Subsetor", 22),
    "Eletricidade e gás, água, esgoto, atividades de gestão de resíduos": (
        "Indústria",
        "Eletricidade, gás e saneamento",
        "Subsetor",
        23,
    ),
    "Construção": ("Indústria", "Construção", "Subsetor", 24),
    "Serviços - total": ("Serviços", "Serviços", "Setor", 3),
    "Comércio": ("Serviços", "Comércio", "Subsetor", 31),
    "Transporte, armazenagem e correio": ("Serviços", "Transporte e correio", "Subsetor", 32),
    "Informação e comunicação": ("Serviços", "Informação e comunicação", "Subsetor", 33),
    "Atividades financeiras, de seguros e serviços relacionados": (
        "Serviços",
        "Financeiras e seguros",
        "Subsetor",
        34,
    ),
    "Atividades imobiliárias": ("Serviços", "Imobiliárias", "Subsetor", 35),
    "Outras atividades de serviços": ("Serviços", "Outros serviços", "Subsetor", 36),
    "Administração, saúde e educação públicas e seguridade social": (
        "Serviços",
        "Administração pública, saúde e educação",
        "Subsetor",
        37,
    ),
    "Valor adicionado a preços básicos": ("Agregados", "Valor adicionado", "Agregado", 4),
    "Impostos líquidos sobre produtos": ("Agregados", "Impostos líquidos", "Agregado", 5),
    "PIB a preços de mercado": ("Agregados", "PIB", "Agregado", 6),
    "Despesa de consumo das famílias": ("Demanda", "Consumo das famílias", "Componente", 7),
    "Despesa de consumo da administração pública": (
        "Demanda",
        "Consumo da administração pública",
        "Componente",
        8,
    ),
    "Formação bruta de capital fixo": ("Demanda", "Investimento (FBCF)", "Componente", 9),
    "Variação de estoque": ("Demanda", "Variação de estoque", "Componente", 10),
    "Exportação de bens e serviços": ("Setor externo", "Exportação", "Componente", 11),
    "Importação de bens e serviços (-)": ("Setor externo", "Importação", "Componente", 12),
}


def numero(texto: str) -> float | None:
    """Converte número no padrão brasileiro (1.234,56) ou inteiro (123456)."""
    t = texto.replace("\xa0", " ").strip()
    if t in VALORES_ESPECIAIS:
        return None
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    try:
        return float(t)
    except ValueError:
        return None


def formatar_valor(v: float | None) -> str:
    if v is None:
        return ""
    if v == int(v):
        return str(int(v))
    return repr(round(v, 10))


def ler_largo(caminho: Path) -> dict:
    """Lê um CSV largo do SIDRA e devolve metadados + matriz de blocos."""
    with caminho.open(encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.reader(fh, delimiter=";"))

    if len(linhas) < 6:
        raise ValueError(f"{caminho.name}: estrutura inesperada ({len(linhas)} linhas)")

    titulo = linhas[0][0].strip()
    variavel = linhas[1][0].strip()
    linha_trimestre = linhas[3]
    linha_serie = linhas[4]
    linha_valor = linhas[5]

    inicios = [i for i, v in enumerate(linha_trimestre) if v.strip()]
    if not inicios:
        raise ValueError(f"{caminho.name}: nenhum trimestre encontrado na linha 4")

    return {
        "titulo": titulo,
        "variavel": variavel,
        "linha_trimestre": linha_trimestre,
        "linha_serie": linha_serie,
        "linha_valor": linha_valor,
        "inicios": inicios,
    }


def transformar(caminho: Path, meta_tabela: dict) -> tuple[list[dict], dict]:
    largo = ler_largo(caminho)
    inicios = largo["inicios"]
    lt, ls, lv = largo["linha_trimestre"], largo["linha_serie"], largo["linha_valor"]

    registros: list[dict] = []
    series_vistas: list[str] = []
    unidades_vistas: set[str] = set()
    periodos_vistos: set[str] = set()
    descartados_especiais = 0
    erros_conversao = 0

    for k, inicio in enumerate(inicios):
        fim = inicios[k + 1] if k + 1 < len(inicios) else len(lv)
        m = RE_TRIMESTRE.match(lt[inicio])
        if not m:
            raise ValueError(f"{caminho.name}: trimestre inválido em {inicio}: {lt[inicio]!r}")
        trimestre, ano = int(m.group(1)), int(m.group(2))
        if not 1 <= trimestre <= 4:
            raise ValueError(f"{caminho.name}: trimestre fora de 1..4: {trimestre}")
        if (fim - inicio) % 2 != 0:
            raise ValueError(
                f"{caminho.name}: bloco do trimestre {trimestre}/{ano} com "
                f"{(fim - inicio)} colunas (esperado par)"
            )

        data_iso = date(ano, 3 * (trimestre - 1) + 1, 1).isoformat()
        trimestre_txt = f"{trimestre}º trimestre {ano}"
        periodos_vistos.add(trimestre_txt)

        for col in range(inicio, fim, 2):
            serie = ls[col].strip()
            unidade = lv[col + 1].strip() if col + 1 < len(lv) else ""
            if not serie:
                raise ValueError(f"{caminho.name}: série vazia na coluna {col}")
            valor_txt = lv[col].strip()
            valor = numero(valor_txt)
            if valor_txt in VALORES_ESPECIAIS:
                descartados_especiais += 1
            elif valor is None:
                erros_conversao += 1

            series_vistas.append(serie)
            unidades_vistas.add(unidade)
            registros.append(
                {
                    "trimestre_txt": trimestre_txt,
                    "serie": serie,
                    "valor_txt": valor_txt,
                    "unidade": unidade,
                    "valor": formatar_valor(valor),
                    "trimestre": trimestre,
                    "ano": ano,
                    "data": data_iso,
                }
            )

    # ---------------- validações ----------------
    series_unicas = list(dict.fromkeys(series_vistas))
    chaves = [(r["serie"], r["data"]) for r in registros]
    duplicadas = len(chaves) - len(set(chaves))
    n_por_periodo = {p: 0 for p in periodos_vistos}
    for r in registros:
        n_por_periodo[r["trimestre_txt"]] += 1
    periodos_irregulares = {p: n for p, n in n_por_periodo.items() if n != len(series_unicas)}
    faltantes = sum(1 for r in registros if r["valor"] == "")

    resumo = {
        "titulo": largo["titulo"],
        "variavel": largo["variavel"],
        "arquivo_origem": caminho.name,
        "arquivo_saida": meta_tabela["saida"],
        "n_registros": len(registros),
        "n_series": len(series_unicas),
        "n_periodos": len(periodos_vistos),
        "periodo_min": min(periodos_vistos, key=lambda p: (int(p[-4:]), int(p[0]))),
        "periodo_max": max(periodos_vistos, key=lambda p: (int(p[-4:]), int(p[0]))),
        "unidades": sorted(unidades_vistas),
        "duplicadas": duplicadas,
        "periodos_irregulares": periodos_irregulares,
        "valores_ausentes": faltantes,
        "descartados_especiais": descartados_especiais,
        "erros_conversao": erros_conversao,
        "series": series_unicas,
    }
    if not registros:
        raise ValueError(f"{caminho.name}: nenhum registro gerado")
    if duplicadas:
        raise ValueError(f"{caminho.name}: {duplicadas} chaves duplicadas (serie, data)")
    if periodos_irregulares:
        raise ValueError(f"{caminho.name}: períodos com contagem irregular: {periodos_irregulares}")
    if erros_conversao:
        raise ValueError(f"{caminho.name}: {erros_conversao} valores não numéricos")
    if len(unidades_vistas) > 1:
        raise ValueError(f"{caminho.name}: mais de uma unidade: {unidades_vistas}")

    return registros, resumo


def escrever_csv(caminho: Path, colunas: list[str], registros: list[dict]) -> None:
    with caminho.open("w", encoding="utf-8", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=colunas, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(registros)


def dimensao_tempo(registros: list[dict]) -> list[dict]:
    vistos: dict[str, dict] = {}
    for r in registros:
        if r["data"] not in vistos:
            vistos[r["data"]] = {
                "data": r["data"],
                "ano": r["ano"],
                "trimestre": r["trimestre"],
                "trimestre_txt": r["trimestre_txt"],
                "ano_trimestre": f"{r['ano']}-T{r['trimestre']}",
            }
    return sorted(vistos.values(), key=lambda x: x["data"])


def dimensao_serie(todas_as_series: list[str]) -> list[dict]:
    ordem = {s: i for i, s in enumerate(todas_as_series)}
    registros = []
    for serie in todas_as_series:
        grupo, subgrupo, nivel, ordem_negocio = CLASSIFICACAO.get(
            serie, ("Não classificado", serie, "Outro", 99)
        )
        registros.append(
            {
                "serie": serie,
                "grupo": grupo,
                "subgrupo": subgrupo,
                "nivel": nivel,
                "ordem": ordem_negocio,
                "ordem_origem": ordem[serie] + 1,
            }
        )
    return sorted(registros, key=lambda x: x["ordem"])


def executar(indir: Path, outdir: Path) -> list[tuple[str, dict, dict]]:
    """Executa o ETL completo e devolve o resumo de cada tabela.

    Usado pela linha de comando (main) e pelo notebook da Etapa 02, para que os
    dois caminhos produzam exatamente o mesmo resultado.
    """
    indir = Path(indir).resolve()
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    resumos = []
    todas_as_series: list[str] = []
    registros_por_tabela: dict[str, list[dict]] = {}

    for codigo, cfg in TABELAS.items():
        origem = indir / cfg["arquivo"]
        if not origem.exists():
            raise FileNotFoundError(f"não encontrado: {origem}")
        registros, resumo = transformar(origem, cfg)
        registros_por_tabela[codigo] = registros
        escrever_csv(outdir / cfg["saida"], COLUNAS, registros)
        resumos.append((codigo, cfg, resumo))
        for serie in resumo["series"]:
            if serie not in todas_as_series:
                todas_as_series.append(serie)
        print(
            f"[OK] {cfg['arquivo']}: {resumo['n_registros']} registros, "
            f"{resumo['n_series']} séries, {resumo['n_periodos']} trimestres "
            f"({resumo['periodo_min']} a {resumo['periodo_max']}) -> {cfg['saida']}"
        )

    # Dimensões compartilhadas (modelo em estrela)
    tempo = dimensao_tempo(registros_por_tabela["1620"])
    escrever_csv(
        outdir / "dim_tempo.csv",
        ["data", "ano", "trimestre", "trimestre_txt", "ano_trimestre"],
        tempo,
    )
    serie = dimensao_serie(todas_as_series)
    escrever_csv(
        outdir / "dim_serie.csv",
        ["serie", "grupo", "subgrupo", "nivel", "ordem", "ordem_origem"],
        serie,
    )

    # Log de decisões (Etapa 02)
    execucao = date.today().isoformat()
    linhas = [
        "LOG DE ETL - PROJETO BI / TEMA 12 - PIB BRASILEIRO",
        f"Data de execução: {execucao}",
        f"Data de acesso às fontes: {DATA_ACESSO}",
        "",
        "1. FONTES (SIDRA/IBGE)",
    ]
    for codigo, cfg, resumo in resumos:
        linhas += [
            f"   - Tabela {codigo}: {resumo['variavel']}",
            f"     URL: {cfg['url']}",
            f"     Arquivo original: {resumo['arquivo_origem']} | acesso: {DATA_ACESSO}",
            f"     Arquivo tratado: {cfg['saida']}",
        ]
    linhas += [
        "",
        "2. LEITURA E ESTRUTURA",
        "   - CSV do SIDRA lido com delimitador ';' e codificação UTF-8 com BOM.",
        "   - Layout largo: linha 4 = trimestres, linha 5 = séries, linha 6 = valores.",
        "   - Cada série ocupa 2 colunas (valor + unidade); o rótulo do trimestre",
        "     aparece só na primeira coluna do bloco e foi propagado.",
        "   - Saída em UTF-8, delimitador ',' e decimal '.', formato neutro: no Power BI",
        "     importar com Culture en-US; no Excel usar Dados > De Texto/CSV.",
        "",
        "3. TRANSFORMAÇÕES",
        "   - Layout largo convertido para longo (uma linha por série x trimestre).",
        "   - Números no padrão brasileiro convertidos para decimal (vírgula -> ponto).",
        "   - valor_txt preservado para auditoria; valor convertido para numérico.",
        "   - Derivados: trimestre (1-4), ano, data (1º dia do trimestre).",
        "   - Séries mantidas exatamente como no SIDRA (sem agregações).",
        "   - Tabela 5932: usada a variável 'Taxa trimestral (em relação ao mesmo",
        "     período do ano anterior)', conforme recorte definido.",
        "",
        "4. VALIDAÇÕES EXECUTADAS",
    ]
    for codigo, cfg, resumo in resumos:
        linhas += [
            f"   - {codigo}: {resumo['n_registros']} registros = "
            f"{resumo['n_series']} séries x {resumo['n_periodos']} trimestres;",
            f"     duplicadas: {resumo['duplicadas']}; períodos irregulares: "
            f"{len(resumo['periodos_irregulares'])}; ausentes: {resumo['valores_ausentes']}; "
            f"símbolos especiais descartados: {resumo['descartados_especiais']}; "
            f"não numéricos: {resumo['erros_conversao']}; unidades: {resumo['unidades']}.",
        ]
    linhas += [
        "",
        "5. LIMITAÇÕES E OBSERVAÇÕES",
        "   - 2026 tem apenas 1º e 2º trimestres: comparações anuais de 2026 são parciais.",
        "   - Importação (1846) é armazenada com sinal positivo; ao compor a demanda",
        "     (consumo + governo + FBCF + estoque + exportações - importações), subtrair.",
        "   - 1846 é expressa em R$ milhões inteiros (sem centavos); as demais séries",
        "     têm duas casas decimais. São tipos numéricos, sem perda de informação.",
        "   - Tabela 1846 inclui 'Variação de estoque' (23 séries); 1620/5932 têm 22 e",
        "     1621 tem 21 (não há impostos líquidos nem variação de estoque na 1621).",
        "   - A série 1621 é ajustada sazonalmente; não deve ser somada com a 1620.",
        "   - Valores correntes (1846) não são comparáveis em nível entre anos;",
        "     para evolução real usar 1620/1621.",
        "",
        "6. ARQUIVOS GERADOS",
        "   - fato_pib_volume.csv (1620)",
        "   - fato_pib_volume_sazonal.csv (1621)",
        "   - fato_pib_corrente.csv (1846)",
        "   - fato_pib_taxa.csv (5932)",
        "   - dim_tempo.csv / dim_serie.csv",
        "   - log_etl.txt",
    ]
    (outdir / "log_etl.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    print(f"[OK] dimensões e log gravados em {outdir}")
    return resumos


def main() -> int:
    parser = argparse.ArgumentParser(description="ETL das tabelas SIDRA do projeto PIB.")
    parser.add_argument(
        "--indir",
        default=str(RAIZ / "dados_originais"),
        help="Pasta com os CSV originais do SIDRA (padrão: dados_originais/)",
    )
    parser.add_argument(
        "--outdir",
        default=str(RAIZ / "dados"),
        help="Pasta de saída dos arquivos tratados (padrão: dados/)",
    )
    args = parser.parse_args()

    try:
        executar(Path(args.indir), Path(args.outdir))
    except FileNotFoundError as erro:
        print(f"[ERRO] {erro}", file=sys.stderr)
        return 2
    except ValueError as erro:
        print(f"[ERRO] {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
