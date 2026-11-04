#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera frames SVG 1280x720 para o Figma a partir do layout do PBIP.

Uso:
    python figma/_gerar_frames.py
"""
from __future__ import annotations

import csv
import glob
import html
import json
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
DADOS = PROJ / "dados"
OUT = PROJ / "figma"
FRAMES = OUT / "frames"
FRAMES.mkdir(parents=True, exist_ok=True)

# ---------------- palette / type ----------------
SERV, IND, AGRO, SUPPORT = "#2A78D6", "#EB6834", "#1BAF7A", "#EDA100"
PURPLE = "#6250D6"
INK, INK2, MUTED = "#0B0B0B", "#52514E", "#898781"
GRID, SURF, CARD = "#E1E0D9", "#F9F9F7", "#FFFFFF"
POS, NEG = "#006300", "#D03B3B"
FONT = "Segoe UI"


def pt(v: float) -> float:
    """Converte pontos do Power BI para pixels a 96 dpi."""
    return round(v * 4 / 3, 1)


# ---------------- svg helpers ----------------
def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def rect(x, y, w, h, rx=0, fill="none", stroke="none", sw=1, opacity=None):
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{o}/>')


def line(x1, y1, x2, y2, stroke=GRID, sw=1, opacity=None):
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{sw}"{o}/>')


def text(x, y, s, size=12, fill=INK, weight=400, anchor="start", opacity=None):
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{o}>{esc(s)}</text>')


def multiline(x, y, lines, size=12, fill=INK, weight=400, lh=None, anchor="start"):
    lh = lh or size * 1.45
    return "".join(text(x, y + i * lh, ln, size=size, fill=fill, weight=weight, anchor=anchor)
                   for i, ln in enumerate(lines))


def wrap(s: str, width: float, size: float, factor: float = 0.53) -> list[str]:
    maxc = max(8, int(width / (size * factor)))
    words, lines, cur = s.split(), [], ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= maxc:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def path(d, stroke="none", fill="none", sw=1, opacity=None):
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<path d="{d}" stroke="{stroke}" fill="{fill}" stroke-width="{sw}"{o}/>'


# ---------------- data ----------------
def load(name: str) -> list[dict]:
    with open(DADOS / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


vol = load("fato_pib_volume.csv")
saz = load("fato_pib_volume_sazonal.csv")
cur = load("fato_pib_corrente.csv")
dim = {r["serie"]: r for r in load("dim_serie.csv")}
PIB, VA = "PIB a preços de mercado", "Valor adicionado a preços básicos"
YEARS = list(range(2000, 2026))


def annual(rows: list[dict], serie: str) -> dict[int, float]:
    out: dict[int, list[float]] = {}
    for r in rows:
        if r["serie"] == serie:
            out.setdefault(int(r["ano"]), []).append(float(r["valor"]))
    return {y: sum(v) / len(v) for y, v in out.items()}


def qval(rows: list[dict], serie: str, y: int, q: int):
    for r in rows:
        if r["serie"] == serie and int(r["ano"]) == y and int(r["trimestre"]) == q:
            return float(r["valor"])
    return None


def qseries(rows: list[dict], serie: str) -> list[tuple[float, float]]:
    d = {}
    for r in rows:
        if r["serie"] == serie:
            d[(int(r["ano"]), int(r["trimestre"]))] = float(r["valor"])
    return sorted((y + (q - 1) / 4, v) for (y, q), v in d.items())


pib_ann = annual(vol, PIB)
pib_q = qseries(vol, PIB)
pib_saz_q = qseries(saz, PIB)
qoq = [(t1, (v1 / v0 - 1) * 100) for (t0, v0), (t1, v1) in zip(pib_saz_q, pib_saz_q[1:])]
yoy = {y: pib_ann[y] / pib_ann[y - 1] - 1 for y in YEARS[1:]}

SECTORS = [
    ("Serviços", "Serviços - total", SERV),
    ("Indústria", "Indústria - total", IND),
    ("Agropecuária", "Agropecuária - total", AGRO),
]
sector_ann = {s: annual(vol, s) for _, s, _ in SECTORS}
shares = {y: {s: annual(cur, s)[y] / annual(cur, VA)[y] * 100 for _, s, _ in SECTORS} for y in YEARS}
contrib = {}
for y in YEARS[1:]:
    contrib[y] = {}
    for _, s, _ in SECTORS:
        g = sector_ann[s][y] / sector_ann[s][y - 1] - 1
        w = annual(cur, s)[y - 1] / annual(cur, VA)[y - 1]
        contrib[y][s] = g * w * 100


def series_growth(s: str, y1: int, q1: int, y0: int, q0: int):
    a, b = qval(vol, s, y1, q1), qval(vol, s, y0, q0)
    return (a / b - 1) * 100 if a and b else None


ranking = []
for s, r in dim.items():
    if r["nivel"] == "Subsetor":
        g = series_growth(s, 2026, 2, 2025, 2)
        if g is not None:
            ranking.append((s, r["grupo"], g, r["subgrupo"]))
ranking.sort(key=lambda x: -x[2])


# ---------------- primitives ----------------
def base(gf, gt, gi, title, subtitle, active):
    gf.append(rect(0, 0, 1280, 720, fill=SURF))
    gf.append(rect(0, 0, 1280, 4, fill=SERV))
    gt.append(text(32, 38, title, size=pt(22), weight=600))
    gt.append(text(32, 64, subtitle, size=pt(10), fill=INK2))
    gf.append(line(32, 682, 1248, 682, stroke=GRID))
    gt.append(text(32, 700, "Fonte: IBGE — SIDRA, tabelas 1620, 1621, 1846 e 5932 (Contas Nacionais Trimestrais). Acesso em 20/10/2026. Projeto BI · Tema 12 · Evandro Miguel.", size=pt(8), fill=MUTED))
    labels = [("Capa", "capa"), ("Visão geral", "visao_geral"), ("Temporal", "temporal"),
              ("Setores", "setores"), ("Síntese", "sintese")]
    for i, (lab, key) in enumerate(labels):
        x, y, w, h = 736 + i * 104, 18, 96, 28
        on = key == active
        gi.append(rect(x, y, w, h, rx=6, fill=SERV if on else CARD, stroke="none" if on else GRID))
        gi.append(text(x + w / 2, y + 18.5, lab, size=pt(9), fill="#FFFFFF" if on else INK2, anchor="middle"))


def shell(gf, x, y, w, h, accent=None):
    gf.append(rect(x, y, w, h, rx=8, fill=CARD, stroke=GRID))
    if accent:
        gf.append(rect(x + 1, y + 12, 4, h - 24, rx=2, fill=accent))


def vtitle(gt, x, y, s):
    gt.append(text(x + 12, y + 22, s, size=pt(11), weight=600, fill=INK2))


def kpi(gf, gt, gc, x, y, w, h, label, value, color, accent):
    shell(gf, x, y, w, h, accent)
    for i, ln in enumerate(wrap(label, w - 32, pt(10))[:2]):
        gt.append(text(x + 16, y + 28 + i * 16, ln, size=pt(10), fill=INK2))
    gc.append(text(x + 16, y + 84, value, size=pt(30), weight=700, fill=color))


def plot(x, y, w, h, left=52, right=14, top=40, bottom=30):
    return x + left, y + top, x + w - right, y + h - bottom


def yscale(v, lo, hi, y0, y1):
    return y1 - (v - lo) / (hi - lo) * (y1 - y0)


def xscale(t, lo, hi, x0, x1):
    return x0 + (t - lo) / (hi - lo) * (x1 - x0)


def line_chart(gc, x, y, w, h, pts, color, lo, hi, ticks, fmt, xlabels, zero=False, bands=None, lw=2):
    x0, y0, x1, y1 = plot(x, y, w, h)
    if bands:
        for a, b, lab in bands:
            xa = xscale(a, pts[0][0], pts[-1][0], x0, x1)
            xb = xscale(b, pts[0][0], pts[-1][0], x0, x1)
            gc.append(rect(xa, y0, max(1, xb - xa), y1 - y0, fill=NEG, opacity=0.05))
            gc.append(text((xa + xb) / 2, y0 - 4, lab, size=9, fill=MUTED, anchor="middle"))
    for v in ticks:
        yy = yscale(v, lo, hi, y0, y1)
        gc.append(line(x0, yy, x1, yy, stroke=GRID))
        gc.append(text(x0 - 6, yy + 4, fmt(v), size=10, fill=MUTED, anchor="end"))
    for t, lab in xlabels:
        xx = xscale(t, xlabels[0][0], xlabels[-1][0], x0, x1)
        gc.append(text(xx, y1 + 16, lab, size=10, fill=MUTED, anchor="middle"))
    if zero and lo <= 0 <= hi:
        yz = yscale(0, lo, hi, y0, y1)
        gc.append(line(x0, yz, x1, yz, stroke="#C3C2B7"))
    d = " ".join(
        f"{'M' if i == 0 else 'L'}{xscale(t, pts[0][0], pts[-1][0], x0, x1):.1f},"
        f"{yscale(v, lo, hi, y0, y1):.1f}"
        for i, (t, v) in enumerate(pts))
    gc.append(path(d, stroke=color, sw=lw))


def bar_chart(gc, x, y, w, h, items, lo, hi, ticks, fmt, xlabels, horizontal=False, value_fmt=None):
    value_fmt = value_fmt or (lambda v: f"{v:+.1f}")
    x0, y0, x1, y1 = plot(x, y, w, h, left=110 if horizontal else 58, bottom=40)
    if horizontal:
        for v in ticks:
            xx = xscale(v, lo, hi, x0, x1)
            gc.append(line(xx, y0, xx, y1, stroke=GRID))
            gc.append(text(xx, y1 + 16, fmt(v), size=10, fill=MUTED, anchor="middle"))
        n = len(items)
        bw = min(18, (y1 - y0) / max(1, n) * 0.62)
        for i, (lab, val, col) in enumerate(items):
            yy = y0 + (i + 0.5) * (y1 - y0) / n
            xz = xscale(0, lo, hi, x0, x1)
            xv = xscale(val, lo, hi, x0, x1)
            gc.append(text(x0 - 8, yy + 4, lab, size=10, fill=INK2, anchor="end"))
            gc.append(rect(min(xz, xv), yy - bw / 2, max(1, abs(xv - xz)), bw, rx=3, fill=col))
            gc.append(text(xv + (6 if val >= 0 else -6), yy + 4, value_fmt(val),
                           size=10, fill=INK, anchor="start" if val >= 0 else "end"))
        xz = xscale(0, lo, hi, x0, x1)
        gc.append(line(xz, y0, xz, y1, stroke="#C3C2B7"))
    else:
        for v in ticks:
            yy = yscale(v, lo, hi, y0, y1)
            gc.append(line(x0, yy, x1, yy, stroke=GRID))
            gc.append(text(x0 - 6, yy + 4, fmt(v), size=10, fill=MUTED, anchor="end"))
        n = len(items)
        bw = (x1 - x0) / max(1, n) * 0.66
        yz = yscale(0, lo, hi, y0, y1)
        for i, (lab, val, col) in enumerate(items):
            xx = x0 + (i + 0.5) * (x1 - x0) / n
            yv = yscale(val, lo, hi, y0, y1)
            gc.append(rect(xx - bw / 2, min(yz, yv), bw, max(1, abs(yv - yz)), rx=2, fill=col))
        gc.append(line(x0, yz, x1, yz, stroke="#C3C2B7"))
        for lab, _ in xlabels:
            try:
                idx = int(lab) - 2001
            except ValueError:
                continue
            if 0 <= idx < n:
                xx = x0 + (idx + 0.5) * (x1 - x0) / n
                gc.append(text(xx, y1 + 16, lab, size=10, fill=MUTED, anchor="middle"))


def stacked_columns(gc, x, y, w, h, years, data):
    x0, y0, x1, y1 = plot(x, y, w, h, left=40, bottom=52)
    for v in (0, 50, 100):
        yy = yscale(v, 0, 100, y0, y1)
        gc.append(line(x0, yy, x1, yy, stroke=GRID))
        gc.append(text(x0 - 6, yy + 4, f"{v}%", size=10, fill=MUTED, anchor="end"))
    n = len(years)
    cw = (x1 - x0) / n * 0.68
    for i, yr in enumerate(years):
        xx = x0 + (i + 0.5) * (x1 - x0) / n - cw / 2
        base_y = y1
        for _, s, col in SECTORS:
            hh = data[yr][s] / 100 * (y1 - y0)
            gc.append(rect(xx, base_y - hh, cw, max(1, hh - 1.2), rx=2, fill=col))
            base_y -= hh
    for yr in (2000, 2005, 2010, 2015, 2020, 2025):
        if yr in years:
            xx = x0 + (years.index(yr) + 0.5) * (x1 - x0) / n
            gc.append(text(xx, y1 + 16, str(yr), size=10, fill=MUTED, anchor="middle"))
    lx = x0
    for lab, _, col in SECTORS:
        gc.append(rect(lx, y1 + 28, 10, 10, rx=2, fill=col))
        gc.append(text(lx + 14, y1 + 37, lab, size=10, fill=INK2))
        lx += 14 + len(lab) * 5.6 + 18


def table(gc, gt, x, y, w, h, cols, rows, widths, highlight=None, font=12, row_h=38, title=None):
    xx, yy = x + 16, y + (42 if title else 16)
    if title:
        vtitle(gt, x, y, title)
    gc.append(rect(xx, yy, w - 32, 28, rx=2, fill="#F3F2EE"))
    cx = xx
    for c, ww in zip(cols, widths):
        anchor = "end" if c != cols[0] else "start"
        gc.append(text(cx + (ww - 10 if anchor == "end" else 10), yy + 19, c,
                       size=pt(9), fill=INK2, weight=600, anchor=anchor))
        cx += ww
    gc.append(line(xx, yy + 28, xx + w - 32, yy + 28, stroke=GRID))
    for ri, row in enumerate(rows):
        ry = yy + 28 + ri * row_h
        if highlight is not None and ri == highlight:
            gc.append(rect(xx, ry, w - 32, row_h, fill="#EAF1FB"))
        cx = xx
        for ci, (val, ww) in enumerate(zip(row, widths)):
            anchor = "end" if ci > 0 else "start"
            fill = INK
            if ci > 0 and isinstance(val, str):
                if val.startswith("+"):
                    fill = POS
                elif val.startswith("−") or val.startswith("-"):
                    fill = NEG
            gc.append(text(cx + (ww - 10 if anchor == "end" else 10), ry + row_h * 0.66,
                           val, size=font, fill=fill, anchor=anchor))
            cx += ww
        gc.append(line(xx, ry + row_h, xx + w - 32, ry + row_h, stroke=GRID, opacity=0.7))


# ---------------- pages ----------------
def page_capa():
    gf, gt, gi, gc = [], [], [], []
    gf.append(rect(0, 0, 1280, 720, fill=SURF))
    gf.append(rect(0, 0, 1280, 4, fill=SERV))
    pts = pib_q
    x0, y0, x1, y1 = 880, 180, 1200, 520
    lo, hi = min(v for _, v in pts), max(v for _, v in pts)
    d = " ".join(
        f"{'M' if i == 0 else 'L'}{xscale(t, pts[0][0], pts[-1][0], x0, x1):.1f},"
        f"{yscale(v, lo, hi, y0, y1):.1f}" for i, (t, v) in enumerate(pts))
    gf.append(path(d + f" L{x1:.1f},{y1:.1f} L{x0:.1f},{y1:.1f} Z", fill=SERV, opacity=0.07))
    gf.append(path(d, stroke=SERV, sw=2.5, opacity=0.35))
    gf.append(rect(68, 150, 4, 72, rx=2, fill=SERV))
    gf.append(rect(80, 380, 320, 112, rx=8, fill=CARD, stroke=GRID))
    gf.append(rect(81, 392, 4, 88, rx=2, fill=SERV))

    gt.append(text(80, 204, "PIB Brasileiro", size=pt(44), weight=700))
    gt.append(text(80, 252, "Evolução e participação setorial · 2000-T1 a 2026-T2", size=pt(20), fill=INK2))
    q = wrap("Como o PIB brasileiro evoluiu e como os principais setores participaram desse desempenho?", 780, pt(14))
    gt.append(multiline(80, 320, q, size=pt(14), fill=INK))
    gt.append(text(96, 410, "PIB nominal 2025 · R$ trilhões", size=pt(10), fill=INK2))
    gc.append(text(96, 458, "12,74", size=pt(32), weight=700, fill=SERV))
    note = wrap("Dados públicos. O relatório usa índices de volume para o crescimento real e valores correntes apenas para participação e nível.", 520, pt(9))
    gt.append(multiline(80, 522, note, size=pt(9), fill=INK2))
    gt.append(text(880, 548, "PIB real · índice 1995 = 100 · 2000–2026", size=pt(9), fill=MUTED))

    for i, (lab, _) in enumerate((("Visão geral", ""), ("Temporal", ""), ("Setores", ""), ("Síntese", ""))):
        x, y, w, h = 80 + i * 196, 566, 180, 40
        primary = i == 0
        gi.append(rect(x, y, w, h, rx=6, fill=SERV if primary else CARD, stroke="none" if primary else GRID))
        gi.append(text(x + w / 2, y + 25, lab, size=pt(11), fill="#FFFFFF" if primary else INK2, anchor="middle"))
    gt.append(text(32, 700, "Fonte: IBGE — SIDRA, tabelas 1620, 1621, 1846 e 5932 (Contas Nacionais Trimestrais). Acesso em 20/10/2026. Projeto BI · Tema 12 · Evandro Miguel.", size=pt(8), fill=MUTED))
    return gf, gt, gi, gc


def page_visao():
    gf, gt, gi, gc = [], [], [], []
    base(gf, gt, gi, "Visão geral", "O nível de atividade, o crescimento e o peso de cada setor", "visao_geral")
    cards = [
        ("PIB nominal 2025 · R$ trilhões", "12,74", SERV, SERV),
        ("PIB real 2025 · variação anual", "+2,29%", POS, AGRO),
        ("Crescimento real médio · % a.a.", "2,26%", IND, IND),
        ("Serviços no valor adicionado · 2025", "69,5%", PURPLE, PURPLE),
    ]
    for i, (lab, val, col, acc) in enumerate(cards):
        kpi(gf, gt, gc, 32 + i * 308, 80, 292, 96, lab, val, col, acc)

    shell(gf, 32, 196, 592, 220)
    vtitle(gt, 32, 196, "Composição do valor adicionado por ano")
    stacked_columns(gc, 32, 196, 592, 220, YEARS, shares)

    shell(gf, 656, 196, 592, 220)
    vtitle(gt, 656, 196, "Contribuição ao crescimento de 2025 (p.p.)")
    items = [(lab, contrib[2025][s], col) for lab, s, col in SECTORS]
    bar_chart(gc, 656, 196, 592, 220, items, 0, 1.4, [0, 0.5, 1.0], lambda v: f"{v:.1f}", [],
              horizontal=True, value_fmt=lambda v: f"{v:+.2f}")

    shell(gf, 32, 432, 1216, 232)
    rows = []
    for lab, s, _ in SECTORS:
        p = annual(cur, s)[2025] / annual(cur, VA)[2025] * 100
        g = series_growth(s, 2026, 2, 2025, 2)
        rows.append([lab, f"{p:.1f}%", f"{contrib[2025][s]:+.2f} p.p.", f"{g:+.1f}%"])
    table(gc, gt, 32, 432, 1216, 232,
          ["Setor", "Participação 2025", "Contribuição 2025", "Crescimento 2026-T2"],
          rows, [280, 300, 320, 300], font=14, row_h=42, title="Setores em números")
    gc.append(text(64, 650, "2026-T2 = variação contra 2025-T2. Participação e contribuição usam valores correntes; crescimento usa índice de volume.",
                   size=pt(8), fill=MUTED))
    return gf, gt, gi, gc


def page_temporal():
    gf, gt, gi, gc = [], [], [], []
    base(gf, gt, gi, "Análise temporal", "2000-T1 a 2026-T2 · 2026 tem apenas dois trimestres", "temporal")

    shell(gf, 32, 80, 700, 270)
    vtitle(gt, 32, 80, "PIB real — índice de volume (1995 = 100)")
    line_chart(gc, 32, 80, 700, 270, pib_q, SERV, 90, 210, [90, 120, 150, 180, 210],
               lambda v: f"{v:.0f}",
               [(2000, "2000"), (2005, "2005"), (2010, "2010"), (2015, "2015"), (2020, "2020"), (2025, "2025")],
               bands=[(2015, 2016.99, "2015–16"), (2020, 2020.99, "2020")])

    shell(gf, 748, 80, 500, 270)
    vtitle(gt, 748, 80, "Crescimento real por ano (%)")
    items = [(str(y), yoy[y] * 100, POS if yoy[y] >= 0 else NEG) for y in YEARS[1:]]
    bar_chart(gc, 748, 80, 500, 270, items, -5, 8, [-5, 0, 5], lambda v: f"{v:.0f}",
              [(2001, "2001"), (2005, "2005"), (2010, "2010"), (2015, "2015"), (2020, "2020"), (2025, "2025")])

    shell(gf, 32, 366, 700, 276)
    vtitle(gt, 32, 366, "Índice de volume por setor")
    x0, y0, x1, y1 = plot(32, 366, 700, 276)
    for v in (90, 130, 170, 210, 250):
        yy = yscale(v, 90, 260, y0, y1)
        gc.append(line(x0, yy, x1, yy, stroke=GRID))
        gc.append(text(x0 - 6, yy + 4, f"{v}", size=10, fill=MUTED, anchor="end"))
    for yr in (2000, 2005, 2010, 2015, 2020, 2025):
        xx = xscale(yr, 2000, 2025, x0, x1)
        gc.append(text(xx, y1 + 16, str(yr), size=10, fill=MUTED, anchor="middle"))
    for _, s, col in SECTORS:
        pts = [(y, sector_ann[s][y]) for y in YEARS]
        d = " ".join(
            f"{'M' if i == 0 else 'L'}{xscale(y, 2000, 2025, x0, x1):.1f},"
            f"{yscale(v, 90, 260, y0, y1):.1f}" for i, (y, v) in enumerate(pts))
        gc.append(path(d, stroke=col, sw=2))
    lx = x0
    for lab, _, col in SECTORS:
        gc.append(rect(lx, y1 + 28, 10, 10, rx=2, fill=col))
        gc.append(text(lx + 14, y1 + 37, lab, size=10, fill=INK2))
        lx += 14 + len(lab) * 5.6 + 18

    shell(gf, 748, 366, 500, 276)
    vtitle(gt, 748, 366, "Variação contra o trimestre anterior (%)")
    line_chart(gc, 748, 366, 500, 276, qoq, SERV, -12, 6, [-12, -9, -6, -3, 0, 3, 6],
               lambda v: f"{v:.0f}",
               [(2000, "2000"), (2005, "2005"), (2010, "2010"), (2015, "2015"), (2020, "2020"), (2025, "2025")],
               zero=True)
    return gf, gt, gi, gc


def page_setores():
    gf, gt, gi, gc = [], [], [], []
    base(gf, gt, gi, "Setores", "Quem puxa o crescimento e como o peso muda ao longo do tempo", "setores")

    for x, lab in ((32, "Ano"), (228, "Grupo")):
        gi.append(rect(x, 80, 180, 80, rx=8, fill=CARD, stroke=GRID))
        gi.append(text(x + 12, 104, lab, size=pt(10), fill=INK2))
        gi.append(rect(x + 12, 114, 156, 30, rx=4, fill=CARD, stroke=GRID))
        gi.append(text(x + 22, 134, "Todos", size=pt(10), fill=INK))
        gi.append(text(x + 152, 134, "⌄", size=pt(10), fill=MUTED, anchor="middle"))

    shell(gf, 32, 176, 760, 464)
    rows = []
    for y in range(2000, 2026):
        row = [str(y)]
        for _, s, _ in SECTORS:
            row.append(f"{contrib[y][s]:+.2f}" if y in contrib else "—")
        rows.append(row)
    table(gc, gt, 32, 176, 760, 464,
          ["Ano", "Agropecuária", "Indústria", "Serviços"], rows,
          [100, 210, 210, 210], highlight=25, font=10, row_h=15.0,
          title="Contribuição ao crescimento por setor e ano")

    shell(gf, 808, 80, 440, 300)
    vtitle(gt, 808, 80, "Crescimento em 2026-T2 por subsetor")
    short = {
        "Indústrias extrativas": "Extrativas",
        "Indústrias de transformação": "Transformação",
        "Eletricidade e gás, água, esgoto, atividades de gestão de resíduos": "Eletricidade",
        "Construção": "Construção",
        "Comércio": "Comércio",
        "Transporte, armazenagem e correio": "Transporte",
        "Informação e comunicação": "Informação",
        "Atividades financeiras, de seguros e serviços relacionados": "Financeiras",
        "Atividades imobiliárias": "Imobiliárias",
        "Outras atividades de serviços": "Outros serviços",
        "Administração, saúde e educação públicas e seguridade social": "Administração",
    }
    items = []
    for s, grupo, g, sub in ranking:
        col = SERV if grupo == "Serviços" else (IND if grupo == "Indústria" else AGRO)
        items.append((short.get(s, sub), g, col))
    bar_chart(gc, 808, 80, 440, 300, items, -2, 13, [-2, 0, 5, 10], lambda v: f"{v:.0f}", [],
              horizontal=True, value_fmt=lambda v: f"{v:+.1f}")

    shell(gf, 808, 396, 440, 244)
    vtitle(gt, 808, 396, "Participação no valor adicionado por ano")
    x0, y0, x1, y1 = plot(808, 396, 440, 244, left=40, bottom=46)
    for v in (0, 20, 40, 60, 80):
        yy = yscale(v, 0, 80, y0, y1)
        gc.append(line(x0, yy, x1, yy, stroke=GRID))
        gc.append(text(x0 - 6, yy + 4, f"{v}%", size=10, fill=MUTED, anchor="end"))
    for yr in (2000, 2005, 2010, 2015, 2020, 2025):
        xx = xscale(yr, 2000, 2025, x0, x1)
        gc.append(text(xx, y1 + 16, str(yr), size=10, fill=MUTED, anchor="middle"))
    for _, s, col in SECTORS:
        pts = [(y, shares[y][s]) for y in YEARS]
        d = " ".join(
            f"{'M' if i == 0 else 'L'}{xscale(y, 2000, 2025, x0, x1):.1f},"
            f"{yscale(v, 0, 80, y0, y1):.1f}" for i, (y, v) in enumerate(pts))
        gc.append(path(d, stroke=col, sw=2))
    lx = x0
    for lab, _, col in SECTORS:
        gc.append(rect(lx, y1 + 26, 10, 10, rx=2, fill=col))
        gc.append(text(lx + 14, y1 + 35, lab, size=10, fill=INK2))
        lx += 14 + len(lab) * 5.6 + 14
    return gf, gt, gi, gc


def page_sintese():
    gf, gt, gi, gc = [], [], [], []
    base(gf, gt, gi, "Síntese", "Três achados e uma recomendação para o público do relatório", "sintese")
    achados = [
        ("Serviços sustentam o crescimento",
         "O setor responde por 69,5% do valor adicionado e contribuiu com +1,25 p.p. do crescimento de 2025. É o setor decisivo para o nível de atividade, mas cresce a taxas moderadas: 2,41% a.a. entre 2000 e 2025."),
        ("Agropecuária é pequena, mas a mais dinâmica",
         "São 7,1% do valor adicionado e +0,78 p.p. em 2025. No longo prazo cresce 3,71% a.a., o maior ritmo entre os três setores; em 2026-T2 avança 6,8%."),
        ("Indústria perde peso e a transformação estagna",
         "A indústria caiu de 26,7% para 23,4% do valor adicionado em 25 anos e contribuiu com apenas +0,35 p.p. em 2025. Em 2026-T2, a transformação recua 0,9% enquanto a extrativa cresce 12,0%."),
    ]
    for i, (tit, body) in enumerate(achados):
        x = 32 + i * 400
        shell(gf, x, 96, 384, 250)
        gt.append(text(x + 20, 132, str(i + 1), size=pt(26), weight=700, fill=SERV))
        gt.append(multiline(x + 20, 164, wrap(tit, 344, pt(13)), size=pt(13), weight=600, fill=INK))
        gt.append(multiline(x + 20, 216, wrap(body, 344, pt(10)), size=pt(10), fill=INK2, lh=pt(10) * 1.5))

    shell(gf, 32, 372, 760, 290)
    gt.append(text(52, 410, "Recomendação", size=pt(14), weight=600, fill=INK))
    rec = ("Priorizar a leitura do crescimento por setor, e não apenas o número do PIB. O PIB de 2025 cresceu 2,29%, mas a composição mostra serviços sustentando o nível e agropecuária puxando a margem. Para 2026, o avanço é positivo, porém concentrado em agropecuária, extrativa e informação/comunicação — a transformação industrial segue em queda. Como usar: comece pela visão geral para o nível, passe pela análise temporal para o ciclo e pela página de setores para identificar os motores. O ano de 2026 é parcial (apenas T1 e T2) e não deve ser lido como ano fechado.")
    gt.append(multiline(52, 446, wrap(rec, 720, pt(11)), size=pt(11), fill=INK2, lh=pt(11) * 1.55))

    shell(gf, 808, 372, 440, 290)
    gt.append(text(828, 410, "Números para lembrar", size=pt(14), weight=600, fill=INK))
    nums = [
        ("PIB nominal 2025", "R$ 12,74 trilhões"),
        ("PIB real 2025", "+2,29%"),
        ("CAGR 2000–2025", "2,26% a.a."),
        ("PIB 2026-T2", "+2,0% YoY · +0,48% QoQ"),
        ("Serviços no VA", "69,5%"),
    ]
    yy = 450
    for lab, val in nums:
        gt.append(text(828, yy, lab, size=pt(10), fill=INK2))
        gt.append(text(1228, yy, val, size=pt(11), weight=600, fill=INK, anchor="end"))
        yy += 36
    return gf, gt, gi, gc


def page_design():
    gf, gt, gi, gc = [], [], [], []
    gf.append(rect(0, 0, 1280, 720, fill=SURF))
    gf.append(rect(0, 0, 1280, 4, fill=SERV))
    gt.append(text(32, 50, "Design system · PIB Brasileiro", size=pt(26), weight=700))
    gt.append(text(32, 76, "Cores, tipografia e componentes usados nos cinco frames. Tema 12 · Evandro Miguel.", size=pt(10), fill=INK2))

    gt.append(text(32, 120, "Cores", size=pt(12), weight=600, fill=INK2))
    swatches = [
        (SERV, "Serviços", "#2A78D6"), (IND, "Indústria", "#EB6834"),
        (AGRO, "Agropecuária", "#1BAF7A"), (SUPPORT, "Apoio", "#EDA100"),
        (PURPLE, "Apoio 2", "#6250D6"), (POS, "Positivo", "#006300"), (NEG, "Negativo", "#D03B3B"),
    ]
    for i, (col, lab, hx) in enumerate(swatches):
        x = 32 + i * 172
        gt.append(rect(x, 136, 156, 56, rx=6, fill=col))
        gt.append(text(x, 214, lab, size=pt(9), weight=600))
        gt.append(text(x, 230, hx, size=pt(8), fill=MUTED))

    gt.append(text(32, 272, "Superfícies e tinta", size=pt(12), weight=600, fill=INK2))
    surfaces = [
        (SURF, "Fundo #F9F9F7"), (CARD, "Cartão #FFFFFF"), (GRID, "Borda #E1E0D9"),
        (INK, "Texto #0B0B0B"), (INK2, "Secundário #52514E"), (MUTED, "Rótulo #898781"),
    ]
    for i, (col, lab) in enumerate(surfaces):
        x = 32 + i * 200
        gt.append(rect(x, 288, 184, 44, rx=6, fill=col, stroke=GRID))
        gt.append(text(x, 352, lab, size=pt(9), fill=INK2))

    gt.append(text(32, 372, "Tipografia (Segoe UI)", size=pt(12), weight=600, fill=INK2))
    types = [
        ("Capa", 44, 700, 445),
        ("Título de página", 22, 600, 488),
        ("Subtítulo", 20, 400, 526),
        ("Corpo", 12, 400, 558),
        ("Título de visual", 11, 600, 586),
        ("Rótulo / eixo", 9, 400, 610),
        ("Rodapé", 8, 400, 632),
    ]
    for lab, size, weight, y in types:
        gt.append(text(32, y, "PIB brasileiro", size=pt(size), weight=weight))
        gt.append(text(480, y, f"{lab} · {size} pt · {pt(size)} px", size=pt(8), fill=MUTED))

    gt.append(text(700, 400, "Componentes", size=pt(12), weight=600, fill=INK2))
    gf.append(rect(700, 420, 292, 96, rx=8, fill=CARD, stroke=GRID))
    gf.append(rect(701, 432, 4, 72, rx=2, fill=SERV))
    gt.append(text(716, 450, "PIB nominal 2025 · R$ trilhões", size=pt(10), fill=INK2))
    gt.append(text(716, 500, "12,74", size=pt(30), weight=700, fill=SERV))
    gf.append(rect(1010, 420, 96, 28, rx=6, fill=SERV))
    gt.append(text(1058, 439, "Ativo", size=pt(9), fill="#FFFFFF", anchor="middle"))
    gf.append(rect(1114, 420, 96, 28, rx=6, fill=CARD, stroke=GRID))
    gt.append(text(1162, 439, "Inativo", size=pt(9), fill=INK2, anchor="middle"))
    gf.append(rect(700, 532, 292, 120, rx=8, fill=CARD, stroke=GRID))
    gt.append(text(712, 556, "Título do visual", size=pt(11), weight=600, fill=INK2))
    gf.append(path("M712,620 L760,600 L808,608 L856,580 L904,588 L952,560", stroke=SERV, sw=2))
    gf.append(rect(1010, 500, 180, 80, rx=8, fill=CARD, stroke=GRID))
    gt.append(text(1022, 524, "Ano", size=pt(10), fill=INK2))
    gf.append(rect(1022, 534, 156, 30, rx=4, fill=CARD, stroke=GRID))
    gt.append(text(1032, 554, "Todos", size=pt(10), fill=INK))
    gf.append(line(32, 682, 1248, 682, stroke=GRID))
    gt.append(text(32, 700, "Fonte: IBGE — SIDRA, tabelas 1620, 1621, 1846 e 5932. Acesso em 20/10/2026.", size=pt(8), fill=MUTED))
    return gf, gt, gi, gc


# ---------------- write ----------------
def svg(gf, gt, gi, gc):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">\n'
        '<g id="fundo">' + "".join(gf) + '</g>\n'
        '<g id="titulos">' + "".join(gt) + '</g>\n'
        '<g id="interativos">' + "".join(gi) + '</g>\n'
        '<g id="conteudo">' + "".join(gc) + '</g>\n'
        '</svg>\n'
    )


PAGES = [
    ("01_capa", page_capa),
    ("02_visao_geral", page_visao),
    ("03_temporal", page_temporal),
    ("04_setores", page_setores),
    ("05_sintese", page_sintese),
]


def svg_fundo(gf):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">\n'
        '<g id="fundo">' + "".join(gf) + '</g>\n'
        '</svg>\n'
    )


def write_posicoes():
    """CSV com as posições reais dos visuais no PBIP, para alinhar no Power BI."""
    rows = []
    pattern = str(PROJ / "powerbi" / "pib_brasileiro" / "pib_brasileiro.Report" / "definition" / "pages" / "*" / "visuals" / "*" / "visual.json")
    for p in sorted(glob.glob(pattern)):
        d = json.load(open(p, encoding="utf-8"))
        v, pos = d["visual"], d["position"]
        title = ""
        try:
            title = v["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"].strip("'")
        except Exception:
            pass
        obs = ""
        rows.append({
            "pagina": Path(p).parts[-4],
            "visual": d["name"],
            "tipo": v.get("visualType", ""),
            "x": pos["x"], "y": pos["y"], "largura": pos["width"], "altura": pos["height"],
            "titulo": title,
            "observacao": obs,
        })
    with open(OUT / "posicoes.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("[OK] posicoes.csv")


def write_preview():
    html_doc = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Preview — PIB Brasileiro</title>
<style>
body{font-family:Segoe UI,Arial,sans-serif;background:#111;color:#eee;margin:0;padding:32px}
h1{font-size:22px;margin:0 0 6px}p{color:#aaa;margin:0 0 28px}
h2{font-size:15px;margin:36px 0 12px;color:#ddd}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(560px,1fr));gap:20px}
figure{margin:0;background:#1b1b1b;border:1px solid #333;border-radius:10px;overflow:hidden}
img{display:block;width:100%;height:auto}
figcaption{padding:10px 14px;font-size:12px;color:#bbb}
a{color:#7ab7ff}
</style></head><body>
<h1>PIB Brasileiro — frames e fundos</h1>
<p>Frames completos (mock) e versões de fundo com a sidebar e os cartões, sem títulos, valores, gráficos ou botões de conteúdo. Abra os SVG para ver em 1280×720.</p>
<h2>Frames completos</h2><div class="grid">
<figure><img src="frames/01_capa.svg" alt="Capa"><figcaption>01 · Capa</figcaption></figure>
<figure><img src="frames/02_visao_geral.svg" alt="Visão geral"><figcaption>02 · Visão geral</figcaption></figure>
<figure><img src="frames/03_temporal.svg" alt="Análise temporal"><figcaption>03 · Análise temporal</figcaption></figure>
<figure><img src="frames/04_setores.svg" alt="Setores"><figcaption>04 · Setores</figcaption></figure>
<figure><img src="frames/05_sintese.svg" alt="Síntese"><figcaption>05 · Síntese</figcaption></figure>
<figure><img src="frames/00_design_system.svg" alt="Design system"><figcaption>00 · Design system</figcaption></figure>
</div>
<h2>Fundos para o Power BI (sidebar e cartões; sem títulos, valores, gráficos ou segmentadores)</h2><div class="grid">
<figure><img src="fundos/01_capa.svg" alt="Fundo capa"><figcaption>01 · Capa</figcaption></figure>
<figure><img src="fundos/02_visao_geral.svg" alt="Fundo visão geral"><figcaption>02 · Visão geral</figcaption></figure>
<figure><img src="fundos/03_temporal.svg" alt="Fundo temporal"><figcaption>03 · Análise temporal</figcaption></figure>
<figure><img src="fundos/04_setores.svg" alt="Fundo setores"><figcaption>04 · Setores</figcaption></figure>
<figure><img src="fundos/05_sintese.svg" alt="Fundo síntese"><figcaption>05 · Síntese</figcaption></figure>
</div>
</body></html>
"""
    (OUT / "preview.html").write_text(html_doc, encoding="utf-8")
    print("[OK] preview.html")


if __name__ == "__main__":
    FUNDOS = OUT / "fundos"
    FUNDOS.mkdir(exist_ok=True)
    for name, fn in PAGES:
        data = fn()
        (FRAMES / f"{name}.svg").write_text(svg(*data), encoding="utf-8")
        (FUNDOS / f"{name}.svg").write_text(svg_fundo(data[0]), encoding="utf-8")
        print("[OK]", name)
    (FRAMES / "00_design_system.svg").write_text(svg(*page_design()), encoding="utf-8")
    print("[OK] 00_design_system")
    write_posicoes()
    write_preview()
