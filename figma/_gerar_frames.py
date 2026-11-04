#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Frames 1280x720 com sidebar lateral — PIB Brasileiro.

Reutiliza os helpers e os dados de _gerar_frames_topnav.py (backup da versão
anterior) e troca o layout por uma sidebar escura à esquerda.

Uso:
    python figma/_gerar_frames.py
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _gerar_frames_topnav as b  # noqa: E402

# ---------------- tema ----------------
MAIN_BG = "#F4F5F7"
CARD = "#FFFFFF"
BORDER = "#E6E8EE"
INK = "#111827"
INK2 = "#4B5563"
MUTED = "#8A90A2"
SIDEBAR = "#1D2134"
SIDEBAR_2 = "#272C46"
SIDEBAR_TXT = "#A9AEC6"
SIDEBAR_MUTED = "#6C728E"
HERO = "#171B2C"
HERO_CARD = "#222741"
HERO_BORDER = "#343A58"
SERV, IND, AGRO = b.SERV, b.IND, b.AGRO

OUT = b.OUT
FRAMES = b.FRAMES
FUNDOS = OUT / "fundos"
FRAMES.mkdir(parents=True, exist_ok=True)
FUNDOS.mkdir(parents=True, exist_ok=True)

# ---------------- sidebar ----------------
NAV = [
    ("Capa", "capa", "home"),
    ("Visão geral", "visao_geral", "grid"),
    ("Temporal", "temporal", "line"),
    ("Setores", "setores", "bars"),
    ("Síntese", "sintese", "doc"),
]
ITEM_Y = {key: 196 + i * 52 for i, (_, key, _) in enumerate(NAV)}
ITEM_X, ITEM_W, ITEM_H = 28, 188, 44


def icon(gf, x, y, kind, color):
    if kind == "home":
        gf.append(b.path(f"M{x+2},{y+9} L{x+9},{y+2} L{x+16},{y+9} M{x+4},{y+8} L{x+4},{y+16} L{x+14},{y+16} L{x+14},{y+8}",
                         stroke=color, sw=1.6))
    elif kind == "grid":
        for dx, dy in ((1, 1), (9, 1), (1, 9), (9, 9)):
            gf.append(b.rect(x + dx, y + dy, 6, 6, rx=1.5, fill="none", stroke=color, sw=1.4))
    elif kind == "line":
        gf.append(b.path(f"M{x+1},{y+16} L{x+1},{y+2} M{x+3},{y+12} L{x+7},{y+8} L{x+10},{y+11} L{x+16},{y+4}",
                         stroke=color, sw=1.6))
    elif kind == "bars":
        gf.append(b.rect(x + 2, y + 9, 3, 7, rx=1, fill=color))
        gf.append(b.rect(x + 7, y + 5, 3, 11, rx=1, fill=color))
        gf.append(b.rect(x + 12, y + 2, 3, 14, rx=1, fill=color))
    elif kind == "doc":
        gf.append(b.rect(x + 3, y + 2, 12, 15, rx=2, fill="none", stroke=color, sw=1.4))
        for yy in (y + 7, y + 10, y + 13):
            gf.append(b.line(x + 6, yy, x + 12, yy, stroke=color, sw=1.2))


def sidebar(gf, gt, active):
    gf.append(b.rect(0, 0, 1280, 720, fill=MAIN_BG))
    gf.append(b.rect(16, 16, 212, 688, rx=24, fill=SIDEBAR))
    # marca
    gf.append(b.rect(40, 44, 24, 24, rx=8, fill=SERV))
    gf.append(b.rect(45, 56, 3, 6, rx=1, fill="#FFFFFF"))
    gf.append(b.rect(50, 52, 3, 10, rx=1, fill="#FFFFFF"))
    gf.append(b.rect(55, 48, 3, 14, rx=1, fill="#FFFFFF"))
    gf.append(b.rect(60, 60, 4, 4, rx=2, fill=AGRO))
    gf.append(b.text(74, 60, "PIB Brasil", size=16, weight=600, fill="#FFFFFF"))
    gf.append(b.text(74, 76, "Tema 12 · BI", size=8, fill=SIDEBAR_MUTED))
    gf.append(b.line(32, 96, 212, 96, stroke="#2A2F47"))
    # perfil
    gf.append(b.rect(40, 112, 44, 44, rx=22, fill=SIDEBAR_2, stroke="#343A58"))
    gf.append(b.text(62, 139, "EM", size=13, weight=600, fill="#FFFFFF", anchor="middle"))
    gf.append(b.text(96, 127, "Evandro Miguel", size=11, weight=600, fill="#FFFFFF"))
    gf.append(b.text(96, 143, "Turma 1", size=8, fill=SIDEBAR_MUTED))
    # navegação
    for i, (lab, key, kind) in enumerate(NAV):
        y = ITEM_Y[key]
        on = key == active
        if on:
            gf.append(b.rect(ITEM_X, y, ITEM_W, ITEM_H, rx=12, fill=SERV))
        color = "#FFFFFF" if on else SIDEBAR_TXT
        icon(gf, ITEM_X + 16, y + 13, kind, color)
        gf.append(b.text(ITEM_X + 44, y + 27, lab, size=11,
                         weight=600 if on else 400, fill=color))
    # rodapé da sidebar
    gf.append(b.line(32, 596, 212, 596, stroke="#2A2F47"))
    gf.append(b.text(40, 620, "Dados até 2026-T2", size=8, fill=SIDEBAR_MUTED))
    gf.append(b.text(40, 634, "Atualizado 20/10/2026", size=8, fill=SIDEBAR_MUTED))
    gf.append(b.rect(40, 650, 6, 6, rx=3, fill=AGRO))
    gf.append(b.text(52, 656, "Base validada", size=8, fill=SIDEBAR_MUTED))
    gf.append(b.text(40, 676, "v1.0 · Tema 12", size=8, fill="#4E5470"))


def page_head(gf, gt, title, subtitle):
    gt.append(b.text(272, 56, title, size=b.pt(22), weight=600, fill=INK))
    gt.append(b.text(272, 80, subtitle, size=b.pt(10), fill=INK2))
    gf.append(b.rect(1108, 32, 140, 28, rx=14, fill="#FFFFFF", stroke="#E4E6EB"))
    gf.append(b.rect(1122, 43, 6, 6, rx=3, fill=AGRO))
    gf.append(b.text(1134, 51, "2026-T2", size=b.pt(9), fill="#4B5563"))
    gf.append(b.line(272, 96, 1248, 96, stroke="#E4E6EB"))


def card(gf, x, y, w, h, accent=None):
    gf.append(b.rect(x, y, w, h, rx=12, fill=CARD, stroke=BORDER))
    if accent:
        gf.append(b.rect(x + 1, y + 12, 4, h - 24, rx=2, fill=accent))


def vtitle(gt, x, y, s):
    gt.append(b.text(x + 14, y + 24, s, size=b.pt(11), weight=600, fill=INK2))


def kpi(gf, gt, gc, x, y, w, h, label, value, color, accent):
    card(gf, x, y, w, h, accent)
    for i, ln in enumerate(b.wrap(label, w - 32, b.pt(9))[:2]):
        gt.append(b.text(x + 16, y + 26 + i * 14, ln, size=b.pt(9), fill=INK2))
    gc.append(b.text(x + 16, y + 74, value, size=b.pt(28), weight=700, fill=color))


def footer(gt, x=272, y=688, w=976):
    gt.append(b.text(x, y, "Fonte: IBGE — SIDRA, tabelas 1620, 1621, 1846 e 5932 (Contas Nacionais Trimestrais). Acesso em 20/10/2026. Projeto BI · Tema 12 · Evandro Miguel.",
                     size=b.pt(8), fill=MUTED))


# ---------------- páginas ----------------
def page_capa():
    gf, gt, gi, gc = [], [], [], []
    sidebar(gf, gt, "capa")
    gf.append(b.rect(248, 16, 1016, 688, rx=24, fill=HERO))
    # círculos decorativos
    gf.append(b.rect(1010, 62, 250, 250, rx=125, fill="none", stroke=SERV, sw=1, opacity=0.10))
    gf.append(b.rect(1130, 540, 160, 160, rx=80, fill="none", stroke=SERV, sw=1, opacity=0.07))
    # motivo do PIB
    pts = b.pib_q
    x0, y0, x1, y1 = 900, 150, 1200, 520
    lo, hi = min(v for _, v in pts), max(v for _, v in pts)
    d = " ".join(
        f"{'M' if i == 0 else 'L'}{b.xscale(t, pts[0][0], pts[-1][0], x0, x1):.1f},"
        f"{b.yscale(v, lo, hi, y0, y1):.1f}" for i, (t, v) in enumerate(pts))
    gf.append(b.path(d + f" L{x1:.1f},{y1:.1f} L{x0:.1f},{y1:.1f} Z", fill=SERV, opacity=0.12))
    gf.append(b.path(d, stroke=SERV, sw=2.6, opacity=0.85))
    for yy in (250, 350, 450):
        gf.append(b.line(x0, yy, x1, yy, stroke=SERV, sw=1, opacity=0.06))
    # badge tema
    gf.append(b.rect(1120, 40, 96, 28, rx=14, fill=HERO_CARD, stroke=HERO_BORDER))
    gf.append(b.text(1168, 58, "Tema 12", size=b.pt(9), fill=SIDEBAR_TXT, anchor="middle"))
    # barra e título
    gf.append(b.rect(284, 136, 4, 64, rx=2, fill=SERV))
    gt.append(b.text(296, 190, "PIB Brasileiro", size=b.pt(44), weight=700, fill="#FFFFFF"))
    sub = b.wrap("Evolução e participação setorial · 2000-T1 a 2026-T2", 560, b.pt(20))
    gt.append(b.multiline(296, 232, sub, size=b.pt(20), fill=SIDEBAR_TXT, lh=30))
    q = b.wrap("Como o PIB brasileiro evoluiu e como os principais setores participaram desse desempenho?",
               560, b.pt(14))
    gt.append(b.multiline(296, 310, q, size=b.pt(14), fill="#D6DAE8"))
    # KPI
    gf.append(b.rect(296, 380, 300, 120, rx=16, fill=HERO_CARD, stroke=HERO_BORDER))
    gf.append(b.rect(297, 392, 4, 96, rx=2, fill=SERV))
    gt.append(b.text(316, 400, "PIB nominal 2025 · R$ trilhões", size=b.pt(9), fill=SIDEBAR_TXT))
    gc.append(b.text(316, 456, "12,74", size=b.pt(32), weight=700, fill="#FFFFFF"))
    note = b.wrap("Dados públicos. O relatório usa índices de volume para o crescimento real e valores correntes apenas para participação e nível.",
                  520, b.pt(9))
    gt.append(b.multiline(296, 510, note, size=b.pt(9), fill="#8E94AC"))
    gf.append(b.text(296, 560, "Navegue pelo menu à esquerda.", size=b.pt(9), fill="#6C728E"))
    gt.append(b.text(296, 670, "Fonte: IBGE — SIDRA, tabelas 1620, 1621, 1846 e 5932. Acesso em 20/10/2026.",
                     size=b.pt(8), fill="#6C728E"))
    return gf, gt, gi, gc


def page_visao():
    gf, gt, gi, gc = [], [], [], []
    sidebar(gf, gt, "visao_geral")
    page_head(gf, gt, "Visão geral", "O nível de atividade, o crescimento e o peso de cada setor")
    cards = [
        ("PIB nominal 2025", "12,74", SERV, SERV),
        ("PIB real 2025", "+2,29%", b.POS, AGRO),
        ("CAGR 2000–2025", "2,26%", IND, IND),
        ("Serviços no VA 2025", "69,5%", b.PURPLE, b.PURPLE),
    ]
    for i, (lab, val, col, acc) in enumerate(cards):
        kpi(gf, gt, gc, 272 + i * 248, 112, 232, 90, lab, val, col, acc)

    card(gf, 272, 220, 478, 220); vtitle(gt, 272, 220, "Composição do valor adicionado por ano")
    b.stacked_columns(gc, 272, 220, 478, 220, b.YEARS, b.shares)

    card(gf, 770, 220, 478, 220); vtitle(gt, 770, 220, "Contribuição ao crescimento de 2025 (p.p.)")
    items = [(lab, b.contrib[2025][s], col) for lab, s, col in b.SECTORS]
    b.bar_chart(gc, 770, 220, 478, 220, items, 0, 1.4, [0, 0.5, 1.0], lambda v: f"{v:.1f}", [],
                horizontal=True, value_fmt=lambda v: f"{v:+.2f}")

    card(gf, 272, 456, 976, 200)
    rows = []
    for lab, s, _ in b.SECTORS:
        p = b.annual(b.cur, s)[2025] / b.annual(b.cur, b.VA)[2025] * 100
        g = b.series_growth(s, 2026, 2, 2025, 2)
        rows.append([lab, f"{p:.1f}%", f"{b.contrib[2025][s]:+.2f} p.p.", f"{g:+.1f}%"])
    b.table(gc, gt, 272, 456, 976, 200,
            ["Setor", "Participação 2025", "Contribuição 2025", "Crescimento 2026-T2"],
            rows, [224, 240, 240, 240], font=12, row_h=34, title="Setores em números")
    gc.append(b.text(304, 642,
                     "2026-T2 = variação contra 2025-T2. Participação e contribuição usam valores correntes; crescimento usa índice de volume.",
                     size=b.pt(8), fill=MUTED))
    footer(gt)
    return gf, gt, gi, gc


def page_temporal():
    gf, gt, gi, gc = [], [], [], []
    sidebar(gf, gt, "temporal")
    page_head(gf, gt, "Análise temporal", "2000-T1 a 2026-T2 · 2026 tem apenas dois trimestres")
    card(gf, 272, 112, 478, 250); vtitle(gt, 272, 112, "PIB real — índice de volume (1995 = 100)")
    b.line_chart(gc, 272, 112, 478, 250, b.pib_q, SERV, 90, 210, [90, 120, 150, 180, 210],
                 lambda v: f"{v:.0f}",
                 [(2000, "2000"), (2005, "2005"), (2010, "2010"), (2015, "2015"), (2020, "2020"), (2025, "2025")],
                 bands=[(2015, 2016.99, "2015–16"), (2020, 2020.99, "2020")])

    card(gf, 770, 112, 478, 250); vtitle(gt, 770, 112, "Crescimento real por ano (%)")
    items = [(str(y), b.yoy[y] * 100, b.POS if b.yoy[y] >= 0 else b.NEG) for y in b.YEARS[1:]]
    b.bar_chart(gc, 770, 112, 478, 250, items, -5, 8, [-5, 0, 5], lambda v: f"{v:.0f}",
                [(2001, "2001"), (2005, "2005"), (2010, "2010"), (2015, "2015"), (2020, "2020"), (2025, "2025")])

    card(gf, 272, 382, 478, 250); vtitle(gt, 272, 382, "Índice de volume por setor")
    x0, y0, x1, y1 = b.plot(272, 382, 478, 250)
    for v in (90, 130, 170, 210, 250):
        yy = b.yscale(v, 90, 260, y0, y1)
        gc.append(b.line(x0, yy, x1, yy, stroke=b.GRID))
        gc.append(b.text(x0 - 6, yy + 4, f"{v}", size=10, fill=b.MUTED, anchor="end"))
    for yr in (2000, 2005, 2010, 2015, 2020, 2025):
        xx = b.xscale(yr, 2000, 2025, x0, x1)
        gc.append(b.text(xx, y1 + 16, str(yr), size=10, fill=b.MUTED, anchor="middle"))
    for _, s, col in b.SECTORS:
        pts = [(y, b.sector_ann[s][y]) for y in b.YEARS]
        d = " ".join(
            f"{'M' if i == 0 else 'L'}{b.xscale(y, 2000, 2025, x0, x1):.1f},"
            f"{b.yscale(v, 90, 260, y0, y1):.1f}" for i, (y, v) in enumerate(pts))
        gc.append(b.path(d, stroke=col, sw=2))
    lx = x0
    for lab, _, col in b.SECTORS:
        gc.append(b.rect(lx, y1 + 28, 10, 10, rx=2, fill=col))
        gc.append(b.text(lx + 14, y1 + 37, lab, size=10, fill=b.INK2))
        lx += 14 + len(lab) * 5.6 + 18

    card(gf, 770, 382, 478, 250); vtitle(gt, 770, 382, "Variação contra o trimestre anterior (%)")
    b.line_chart(gc, 770, 382, 478, 250, b.qoq, SERV, -12, 6, [-12, -9, -6, -3, 0, 3, 6],
                 lambda v: f"{v:.0f}",
                 [(2000, "2000"), (2005, "2005"), (2010, "2010"), (2015, "2015"), (2020, "2020"), (2025, "2025")],
                 zero=True)
    footer(gt)
    return gf, gt, gi, gc


def contrib_chart(gc, x, y, w, h, years):
    """Colunas empilhadas de contribuição (p.p.), com positivos e negativos."""
    x0, y0, x1, y1 = b.plot(x, y, w, h, left=52, bottom=58)
    lo, hi = -4, 7
    ticks = [-4, -2, 0, 2, 4, 6]
    for v in ticks:
        yy = b.yscale(v, lo, hi, y0, y1)
        gc.append(b.line(x0, yy, x1, yy, stroke=b.GRID))
        gc.append(b.text(x0 - 6, yy + 4, f"{v:+.0f}" if v else "0", size=10, fill=b.MUTED, anchor="end"))
    zero = b.yscale(0, lo, hi, y0, y1)
    gc.append(b.line(x0, zero, x1, zero, stroke="#C3C2B7"))
    n = len(years)
    cw = (x1 - x0) / n * 0.64
    for i, yr in enumerate(years):
        xx = x0 + (i + 0.5) * (x1 - x0) / n - cw / 2
        pos = neg = 0.0
        for _, s, col in b.SECTORS:
            val = b.contrib[yr][s]
            hh = abs(val) / (hi - lo) * (y1 - y0)
            if val >= 0:
                gc.append(b.rect(xx, zero - pos - hh, cw, max(1, hh - 1.2), rx=1, fill=col))
                pos += hh
            else:
                gc.append(b.rect(xx, zero + neg, cw, max(1, hh - 1.2), rx=1, fill=col))
                neg += hh
    for yr in (2005, 2010, 2015, 2020, 2025):
        if yr in years:
            xx = x0 + (years.index(yr) + 0.5) * (x1 - x0) / n
            gc.append(b.text(xx, y1 + 16, str(yr), size=10, fill=b.MUTED, anchor="middle"))
    lx = x0
    for lab, _, col in b.SECTORS:
        gc.append(b.rect(lx, y1 + 28, 10, 10, rx=2, fill=col))
        gc.append(b.text(lx + 14, y1 + 37, lab, size=10, fill=b.INK2))
        lx += 14 + len(lab) * 5.6 + 18


def page_setores():
    gf, gt, gi, gc = [], [], [], []
    sidebar(gf, gt, "setores")
    page_head(gf, gt, "Setores", "Quem puxa o crescimento e como o peso muda ao longo do tempo")
    for x, lab in ((272, "Ano"), (464, "Grupo")):
        gi.append(b.rect(x, 112, 180, 80, rx=12, fill=CARD, stroke=BORDER))
        gi.append(b.text(x + 14, 136, lab, size=b.pt(10), fill=INK2))
        gi.append(b.rect(x + 14, 146, 152, 30, rx=6, fill=CARD, stroke=BORDER))
        gi.append(b.text(x + 24, 166, "Todos", size=b.pt(10), fill=INK))
        gi.append(b.text(x + 148, 166, "⌄", size=b.pt(10), fill=MUTED, anchor="middle"))

    card(gf, 272, 212, 600, 420)
    vtitle(gt, 272, 212, "Contribuição ao crescimento por setor e ano (p.p.)")
    contrib_chart(gc, 272, 212, 600, 420, list(range(2001, 2026)))

    card(gf, 892, 112, 356, 300); vtitle(gt, 892, 112, "Crescimento em 2026-T2 por subsetor")
    short = {
        "Indústrias extrativas": "Extrativas",
        "Indústrias de transformação": "Transformação",
        "Eletricidade e gás, água, esgoto, atividades de gestão de resíduos": "Eletricidade",
        "Construção": "Construção", "Comércio": "Comércio",
        "Transporte, armazenagem e correio": "Transporte",
        "Informação e comunicação": "Informação",
        "Atividades financeiras, de seguros e serviços relacionados": "Financeiras",
        "Atividades imobiliárias": "Imobiliárias",
        "Outras atividades de serviços": "Outros serviços",
        "Administração, saúde e educação públicas e seguridade social": "Administração",
    }
    items = []
    for s, grupo, g, sub in b.ranking:
        col = SERV if grupo == "Serviços" else (IND if grupo == "Indústria" else AGRO)
        items.append((short.get(s, sub), g, col))
    b.bar_chart(gc, 892, 112, 356, 300, items, -2, 13, [-2, 0, 5, 10], lambda v: f"{v:.0f}", [],
                horizontal=True, value_fmt=lambda v: f"{v:+.1f}")

    card(gf, 892, 428, 356, 204); vtitle(gt, 892, 428, "Participação no valor adicionado por ano")
    x0, y0, x1, y1 = b.plot(892, 428, 356, 204, left=40, bottom=44)
    for v in (0, 20, 40, 60, 80):
        yy = b.yscale(v, 0, 80, y0, y1)
        gc.append(b.line(x0, yy, x1, yy, stroke=b.GRID))
        gc.append(b.text(x0 - 6, yy + 4, f"{v}%", size=10, fill=b.MUTED, anchor="end"))
    for yr in (2000, 2005, 2010, 2015, 2020, 2025):
        xx = b.xscale(yr, 2000, 2025, x0, x1)
        gc.append(b.text(xx, y1 + 16, str(yr), size=10, fill=b.MUTED, anchor="middle"))
    for _, s, col in b.SECTORS:
        pts = [(y, b.shares[y][s]) for y in b.YEARS]
        d = " ".join(
            f"{'M' if i == 0 else 'L'}{b.xscale(y, 2000, 2025, x0, x1):.1f},"
            f"{b.yscale(v, 0, 80, y0, y1):.1f}" for i, (y, v) in enumerate(pts))
        gc.append(b.path(d, stroke=col, sw=2))
    lx = x0
    for lab, _, col in b.SECTORS:
        gc.append(b.rect(lx, y1 + 24, 10, 10, rx=2, fill=col))
        gc.append(b.text(lx + 14, y1 + 33, lab, size=10, fill=b.INK2))
        lx += 14 + len(lab) * 5.6 + 10
    footer(gt)
    return gf, gt, gi, gc


def page_sintese():
    gf, gt, gi, gc = [], [], [], []
    sidebar(gf, gt, "sintese")
    page_head(gf, gt, "Síntese", "Três achados e uma recomendação para o público do relatório")
    achados = [
        ("Serviços sustentam o crescimento",
         "O setor responde por 69,5% do valor adicionado e contribuiu com +1,25 p.p. do crescimento de 2025. É o setor decisivo para o nível de atividade, mas cresce a taxas moderadas: 2,41% a.a. entre 2000 e 2025."),
        ("Agropecuária é pequena, mas a mais dinâmica",
         "São 7,1% do valor adicionado e +0,78 p.p. em 2025. No longo prazo cresce 3,71% a.a., o maior ritmo entre os três setores; em 2026-T2 avança 6,8%."),
        ("Indústria perde peso e a transformação estagna",
         "A indústria caiu de 26,7% para 23,4% do valor adicionado em 25 anos e contribuiu com apenas +0,35 p.p. em 2025. Em 2026-T2, a transformação recua 0,9% enquanto a extrativa cresce 12,0%."),
    ]
    for i, (tit, body) in enumerate(achados):
        x = 272 + i * 330
        card(gf, x, 112, 314, 240)
        gt.append(b.text(x + 20, 146, str(i + 1), size=b.pt(24), weight=700, fill=SERV))
        gt.append(b.multiline(x + 20, 176, b.wrap(tit, 274, b.pt(11.5)), size=b.pt(11.5), weight=600, fill=INK))
        gt.append(b.multiline(x + 20, 224, b.wrap(body, 274, b.pt(9.2)), size=b.pt(9.2), fill=INK2,
                              lh=b.pt(9.2) * 1.5))

    card(gf, 272, 368, 640, 264)
    gt.append(b.text(292, 406, "Recomendação", size=b.pt(13), weight=600, fill=INK))
    rec = ("Priorizar a leitura do crescimento por setor, e não apenas o número do PIB. O PIB de 2025 cresceu 2,29%, mas a composição mostra serviços sustentando o nível e agropecuária puxando a margem. Para 2026, o avanço é positivo, porém concentrado em agropecuária, extrativa e informação/comunicação — a transformação industrial segue em queda. Como usar: comece pela visão geral para o nível, passe pela análise temporal para o ciclo e pela página de setores para identificar os motores. O ano de 2026 é parcial (apenas T1 e T2) e não deve ser lido como ano fechado.")
    gt.append(b.multiline(292, 442, b.wrap(rec, 600, b.pt(10.2)), size=b.pt(10.2), fill=INK2,
                          lh=b.pt(10.2) * 1.55))

    card(gf, 928, 368, 320, 264)
    gt.append(b.text(948, 406, "Números para lembrar", size=b.pt(13), weight=600, fill=INK))
    nums = [
        ("PIB nominal 2025", "R$ 12,74 tri"),
        ("PIB real 2025", "+2,29%"),
        ("CAGR 2000–2025", "2,26% a.a."),
        ("PIB 2026-T2", "+2,0% / +0,48%"),
        ("Serviços no VA", "69,5%"),
    ]
    yy = 446
    for lab, val in nums:
        gt.append(b.text(948, yy, lab, size=b.pt(9), fill=INK2))
        gt.append(b.text(1228, yy, val, size=b.pt(10), weight=600, fill=INK, anchor="end"))
        yy += 34
    footer(gt)
    return gf, gt, gi, gc


def page_design():
    gf, gt, gi, gc = [], [], [], []
    gf.append(b.rect(0, 0, 1280, 720, fill=MAIN_BG))
    sidebar(gf, gt, "visao_geral")
    gt.append(b.text(272, 56, "Design system · sidebar", size=b.pt(22), weight=600, fill=INK))
    gt.append(b.text(272, 80, "Cores, tipografia e componentes do novo layout. Tema 12 · Evandro Miguel.",
                     size=b.pt(10), fill=INK2))
    # cores
    gt.append(b.text(272, 124, "Sidebar e superfícies", size=b.pt(11), weight=600, fill=INK2))
    sw = [(SIDEBAR, "Sidebar #1D2134"), (SIDEBAR_2, "Item #272C46"), (HERO, "Hero #171B2C"),
          (HERO_CARD, "Card hero #222741"), (MAIN_BG, "Fundo #F4F5F7"), (CARD, "Cartão #FFFFFF")]
    for i, (col, lab) in enumerate(sw):
        x = 272 + i * 160
        gt.append(b.rect(x, 140, 144, 44, rx=8, fill=col, stroke=BORDER))
        gt.append(b.text(x, 200, lab, size=b.pt(8), fill=INK2))
    # cores de dados
    gt.append(b.text(272, 240, "Dados", size=b.pt(11), weight=600, fill=INK2))
    for i, (col, lab) in enumerate([(SERV, "Serviços #2A78D6"), (IND, "Indústria #EB6834"),
                                    (AGRO, "Agropecuária #1BAF7A"), (b.POS, "Positivo #006300"),
                                    (b.NEG, "Negativo #D03B3B")]):
        x = 272 + i * 190
        gt.append(b.rect(x, 256, 174, 40, rx=8, fill=col))
        gt.append(b.text(x, 312, lab, size=b.pt(8), fill=INK2))
    # tipografia
    gt.append(b.text(272, 356, "Tipografia (Segoe UI)", size=b.pt(11), weight=600, fill=INK2))
    types = [("Título de página", 22, 600, 392), ("Corpo", 12, 400, 428),
             ("Título de visual", 11, 600, 458), ("Rótulo", 9, 400, 484),
             ("Rodapé", 8, 400, 506)]
    for lab, size, weight, y in types:
        gt.append(b.text(272, y, "PIB brasileiro", size=b.pt(size), weight=weight, fill=INK))
        gt.append(b.text(540, y, f"{lab} · {size} pt · {b.pt(size)} px", size=b.pt(8), fill=MUTED))
    # componentes
    gt.append(b.text(730, 356, "Componentes", size=b.pt(11), weight=600, fill=INK2))
    # nav item ativo/inativo
    gf.append(b.rect(730, 376, 188, 44, rx=12, fill=SERV))
    icon(gf, 746, 389, "grid", "#FFFFFF")
    gt.append(b.text(774, 403, "Item ativo", size=11, weight=600, fill="#FFFFFF"))
    gf.append(b.rect(730, 428, 188, 44, rx=12, fill="none", stroke=BORDER))
    icon(gf, 746, 441, "line", SIDEBAR_TXT)
    gt.append(b.text(774, 455, "Item inativo", size=11, fill=INK2))
    # KPI
    gf.append(b.rect(940, 376, 232, 90, rx=12, fill=CARD, stroke=BORDER))
    gf.append(b.rect(941, 388, 4, 66, rx=2, fill=SERV))
    gt.append(b.text(956, 402, "PIB nominal 2025", size=b.pt(9), fill=INK2))
    gt.append(b.text(956, 446, "12,74", size=b.pt(28), weight=700, fill=SERV))
    # rodapé
    gf.append(b.line(272, 682, 1248, 682, stroke=BORDER))
    gt.append(b.text(272, 700, "Fonte: IBGE — SIDRA, tabelas 1620, 1621, 1846 e 5932. Acesso em 20/10/2026.",
                     size=b.pt(8), fill=MUTED))
    return gf, gt, gi, gc


PAGES = [
    ("01_capa", page_capa),
    ("02_visao_geral", page_visao),
    ("03_temporal", page_temporal),
    ("04_setores", page_setores),
    ("05_sintese", page_sintese),
]

if __name__ == "__main__":
    for name, fn in PAGES:
        data = fn()
        (FRAMES / f"{name}.svg").write_text(b.svg(*data), encoding="utf-8")
        (FUNDOS / f"{name}.svg").write_text(b.svg_fundo(data[0]), encoding="utf-8")
        print("[OK]", name)
    (FRAMES / "00_design_system.svg").write_text(b.svg(*page_design()), encoding="utf-8")
    print("[OK] 00_design_system")
    b.write_posicoes()
    b.write_preview()
