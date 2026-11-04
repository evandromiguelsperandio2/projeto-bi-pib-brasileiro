#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Troca a matriz de Setores por colunas empilhadas e melhora a tabela da Visão geral.

Uso:
    python figma/_ajustar_tabelas.py
"""
from __future__ import annotations

import json
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
REPORT = PROJ / "powerbi" / "pib_brasileiro" / "pib_brasileiro.Report" / "definition" / "pages"


def lit(v: str):
    return {"expr": {"Literal": {"Value": v}}}


def color(v: str):
    return {"solid": {"color": {"expr": {"Literal": {"Value": f"'{v}'"}}}}}


def load(name: str) -> dict:
    return json.load(open(REPORT / name / "visual.json", encoding="utf-8"))


def save(name: str, d: dict):
    (REPORT / name / "visual.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def matriz_para_colunas():
    name = "setores/visuals/st_matriz"
    d = load(name)
    v = d["visual"]
    q = v["query"]["queryState"]
    if v.get("visualType") == "columnChart" and "Category" in q:
        print("[SKIP] st_matriz já convertida")
        return
    ano = q["Rows"]["projections"][0]
    serie = q["Columns"]["projections"][0]
    valor = q["Values"]["projections"][0]
    v["visualType"] = "columnChart"
    v["query"] = {
        "queryState": {
            "Category": {"projections": [ano]},
            "Series": {"projections": [serie]},
            "Y": {"projections": [valor]},
        }
    }
    v["objects"] = {
        "labels": [{"properties": {"show": lit("false")}}],
        "valueAxis": [{"properties": {
            "show": lit("true"),
            "fontSize": lit("9D"),
            "labelColor": color("#52514E"),
        }}],
        "categoryAxis": [{"properties": {
            "show": lit("true"),
            "fontSize": lit("9D"),
            "labelColor": color("#52514E"),
        }}],
        "legend": [{"properties": {
            "show": lit("true"),
            "position": lit("'Bottom'"),
            "fontSize": lit("9D"),
        }}],
    }
    try:
        v["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"] = \
            "'Contribuição ao crescimento por setor e ano (p.p.)'"
    except (KeyError, IndexError):
        pass
    save(name, d)
    print("[OK] st_matriz -> columnChart")


def tabela_visao():
    name = "visao_geral/visuals/vg_tabela"
    d = load(name)
    v = d["visual"]
    v["objects"] = {
        "rowHeaders": [{"properties": {
            "bold": lit("false"),
            "fontSize": lit("10D"),
            "fontColor": color("#111827"),
            "backColor": color("#FFFFFF"),
        }}],
        "columnHeaders": [{"properties": {
            "bold": lit("true"),
            "fontSize": lit("9D"),
            "fontColor": color("#4B5563"),
            "backColor": color("#F3F2EE"),
        }}],
        "values": [{"properties": {
            "fontSize": lit("10D"),
            "backColorPrimary": color("#FFFFFF"),
            "backColorSecondary": color("#FAFAFA"),
            "fontColorPrimary": color("#111827"),
            "fontColorSecondary": color("#111827"),
        }}],
        "subTotals": [{"properties": {
            "rowSubtotals": lit("false"),
            "columnSubtotals": lit("false"),
        }}],
        "grid": [{"properties": {
            "gridHorizontal": lit("true"),
            "gridVertical": lit("false"),
            "rowPadding": lit("8D"),
            "outlineColor": color("#E6E8EE"),
            "outlineWeight": lit("1D"),
        }}],
    }
    save(name, d)
    print("[OK] vg_tabela estilizada")


if __name__ == "__main__":
    matriz_para_colunas()
    tabela_visao()
