#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica o layout da sidebar ao PBIP: move a navegação e os visuais.

Uso:
    python figma/_aplicar_layout.py
"""
from __future__ import annotations

import json
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
REPORT = PROJ / "powerbi" / "pib_brasileiro" / "pib_brasileiro.Report" / "definition"
PAGES = REPORT / "pages"

ITEM_Y = {"capa": 196, "visao_geral": 248, "temporal": 300, "setores": 352, "sintese": 404}
ITEM_X, ITEM_W, ITEM_H = 28, 188, 44

# posições novas dos visuais de conteúdo
LAYOUT = {
    "capa": {
        "capa_titulo": (296, 130, 800, 80),
        "capa_sub": (296, 220, 560, 60),
        "capa_pergunta": (296, 300, 560, 54),
        "capa_kpi": (296, 380, 300, 120),
        "capa_nota": (296, 510, 520, 40),
        "rodape_capa": (296, 670, 900, 18),
    },
    "visao_geral": {
        "titulo_visao_geral": (272, 24, 620, 38),
        "sub_visao_geral": (272, 64, 680, 18),
        "rodape_visao_geral": (272, 688, 976, 18),
        "vg_card_0": (272, 112, 232, 90),
        "vg_card_1": (520, 112, 232, 90),
        "vg_card_2": (768, 112, 232, 90),
        "vg_card_3": (1016, 112, 232, 90),
        "vg_participacao": (272, 220, 478, 220),
        "vg_contribuicao": (770, 220, 478, 220),
        "vg_tabela": (272, 456, 976, 200),
    },
    "temporal": {
        "titulo_temporal": (272, 24, 620, 38),
        "sub_temporal": (272, 64, 680, 18),
        "rodape_temporal": (272, 688, 976, 18),
        "tmp_pib": (272, 112, 478, 250),
        "tmp_yoy": (770, 112, 478, 250),
        "tmp_setores": (272, 382, 478, 250),
        "tmp_qoq": (770, 382, 478, 250),
    },
    "setores": {
        "titulo_setores": (272, 24, 620, 38),
        "sub_setores": (272, 64, 680, 18),
        "rodape_setores": (272, 688, 976, 18),
        "st_ano": (272, 112, 180, 80),
        "st_grupo": (464, 112, 180, 80),
        "st_matriz": (272, 212, 600, 420),
        "st_ranking": (892, 112, 356, 300),
        "st_participacao": (892, 428, 356, 204),
    },
    "sintese": {
        "titulo_sintese": (272, 24, 620, 38),
        "sub_sintese": (272, 64, 680, 18),
        "rodape_sintese": (272, 688, 976, 18),
        "sintese_achado_0": (272, 112, 314, 240),
        "sintese_achado_1": (602, 112, 314, 240),
        "sintese_achado_2": (932, 112, 314, 240),
        "sintese_recomendacao": (272, 368, 640, 264),
        "sintese_numeros": (928, 368, 320, 264),
    },
}

LABELS = {
    "vg_card_0": "PIB nominal 2025",
    "vg_card_1": "PIB real 2025",
    "vg_card_2": "CAGR 2000–2025",
    "vg_card_3": "Serviços no VA 2025",
    "capa_kpi": "PIB nominal 2025 · R$ tri",
}


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def set_bool(props: dict, key: str, value: bool):
    props[key] = lit("true" if value else "false")


def button_target(name: str) -> str | None:
    for key in ("visao_geral", "temporal", "setores", "sintese", "capa"):
        if name.endswith("_" + key):
            return key
    return None


def make_button_invisible(v: dict):
    v["objects"] = {
        "text": [{"properties": {"show": lit("false")}}],
        "icon": [{"properties": {"show": lit("false")}}],
        "fill": [{"properties": {"show": lit("false")}}],
        "outline": [{"properties": {"show": lit("false")}}],
    }
    vco = v.setdefault("visualContainerObjects", {})
    for key in ("background", "border", "visualHeader"):
        vco[key] = [{"properties": {"show": lit("false")}}]


def set_font_color(section, color: str):
    for item in section or []:
        props = item.get("properties", {})
        fc = props.get("fontColor")
        if fc and "solid" in fc:
            fc["solid"]["color"]["expr"]["Literal"]["Value"] = f"'{color}'"


def set_font_size(section, size: str):
    for item in section or []:
        props = item.get("properties", {})
        if "fontSize" in props:
            props["fontSize"] = lit(size)


def set_label_text(section, text: str):
    for item in section or []:
        props = item.get("properties", {})
        if "text" in props:
            props["text"] = lit(f"'{text}'")


def update_card(visual: dict, name: str):
    obj = visual.get("objects", {})
    if name in LABELS:
        label = obj.get("label", [])
        set_font_size(label, "9D")
        set_label_text(label, LABELS[name])
    if name == "capa_kpi":
        set_font_color(obj.get("label", []), "#A9AEC6")
        set_font_color(obj.get("value", []), "#FFFFFF")
        vco = visual.setdefault("visualContainerObjects", {})
        vco["background"] = [{"properties": {"show": lit("false")}}]
        vco["border"] = [{"properties": {"show": lit("false")}}]


def update_textbox_colors(visual: dict, name: str):
    colors = {
        "capa_titulo": "#FFFFFF",
        "capa_sub": "#A9AEC6",
        "capa_pergunta": "#D6DAE8",
        "capa_nota": "#8E94AC",
        "rodape_capa": "#6C728E",
    }
    if name not in colors:
        return
    color = colors[name]
    for section in visual.get("objects", {}).get("general", []):
        props = section.get("properties", {})
        for para in props.get("paragraphs", []):
            for run in para.get("textRuns", []):
                style = run.get("textStyle")
                if style:
                    style["color"] = color


def update_sintese_fonts(visual: dict, name: str):
    if name.startswith("sintese_achado_"):
        sizes = ["12pt", "10pt"]
    elif name == "sintese_recomendacao":
        sizes = ["13pt", "11pt", "10pt"]
    elif name == "sintese_numeros":
        sizes = ["12pt", "10pt", "10pt", "10pt", "10pt", "10pt", "9pt"]
    else:
        return
    for section in visual.get("objects", {}).get("general", []):
        for pi, para in enumerate(section.get("properties", {}).get("paragraphs", [])):
            size = sizes[pi] if pi < len(sizes) else sizes[-1]
            for run in para.get("textRuns", []):
                style = run.get("textStyle")
                if style:
                    style["fontSize"] = size


def update_card_chrome(visual: dict, name: str):
    vco = visual.get("visualContainerObjects", {})
    # raio 12 nos cartões/gráficos
    border = vco.get("border")
    if border:
        for item in border:
            props = item.get("properties", {})
            if "radius" in props:
                props["radius"] = lit("12L")
    # fundo branco nos visuais de conteúdo (menos a capa)
    bg = vco.get("background")
    if bg and name not in ("capa_kpi",):
        for item in bg:
            props = item.get("properties", {})
            color = props.get("color")
            if color and "solid" in color:
                color["solid"]["color"]["expr"]["Literal"]["Value"] = "'#FFFFFF'"


def main():
    changed = 0
    for page_dir in sorted(PAGES.iterdir()):
        if not page_dir.is_dir() or page_dir.name == "pages.json":
            continue
        page = page_dir.name
        # cor de fundo da página
        page_json = page_dir / "page.json"
        if page_json.exists():
            d = json.load(open(page_json, encoding="utf-8"))
            try:
                bg = d["objects"]["background"][0]["properties"]["color"]["solid"]["color"]["expr"]["Literal"]
                bg["Value"] = "'#171B2C'" if page == "capa" else "'#F4F5F7'"
            except (KeyError, IndexError):
                pass
            page_json.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        visuals_dir = page_dir / "visuals"
        if not visuals_dir.exists():
            continue
        for vdir in sorted(visuals_dir.iterdir()):
            vjson = vdir / "visual.json"
            if not vjson.exists():
                continue
            d = json.load(open(vjson, encoding="utf-8"))
            name = d.get("name", vdir.name)
            v = d.get("visual", {})
            vtype = v.get("visualType", "")
            if vtype == "actionButton":
                target = button_target(name)
                if target:
                    d["position"].update({"x": ITEM_X, "y": ITEM_Y[target],
                                          "width": ITEM_W, "height": ITEM_H})
                    make_button_invisible(v)
            elif name in LAYOUT.get(page, {}):
                x, y, w, h = LAYOUT[page][name]
                d["position"].update({"x": x, "y": y, "width": w, "height": h})
                if vtype == "cardVisual":
                    update_card(v, name)
                if vtype == "textbox":
                    update_textbox_colors(v, name)
                    update_sintese_fonts(v, name)
                update_card_chrome(v, name)
            else:
                print("[AVISO] sem posição:", page, name)
            vjson.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            changed += 1
    # página ativa
    pages_json = PAGES / "pages.json"
    d = json.load(open(pages_json, encoding="utf-8"))
    d["activePageName"] = "capa"
    pages_json.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[OK] {changed} visuais atualizados")


if __name__ == "__main__":
    main()
