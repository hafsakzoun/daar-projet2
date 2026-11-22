"""Graphiques SVG des benchmarks V2 (sans dependance externe).

Usage : python3 scripts/plot_benchmark_v2.py docs/benchmarks_v2
Lit les CSV produits par backend/scripts/benchmark_v2.py et ecrit les SVG
dans le meme dossier. Barres / points = moyenne, traits = +/- un ecart-type.
"""

import csv
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

# Couleurs des courbes, toujours dans le meme ordre.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
FONT = "font-family='Helvetica, Arial, sans-serif'"

W, H = 760, 440
LEFT, RIGHT, TOP, BOTTOM = 76, 150, 78, 368


def read(path):
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def nice_max(value):
    """Plus petit maximum dont le quart est un pas 'rond' (1, 2, 5 x 10^n)."""
    if value <= 0:
        return 4
    raw = value / 4
    exponent = 10 ** math.floor(math.log10(raw))
    for step in (1, 2, 5, 10):
        if raw <= step * exponent:
            return 4 * step * exponent
    return 40 * exponent


def fmt(value):
    if value >= 1000:
        return f"{value:,.0f}".replace(",", " ")
    if value >= 10:
        return f"{value:.0f}"
    return f"{value:g}"


def frame(title, subtitle, ylabel, ymax):
    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>",
        f"<rect width='100%' height='100%' fill='{SURFACE}'/>",
        f"<text x='{LEFT}' y='32' {FONT} font-size='18' font-weight='600' fill='{INK}'>{escape(title)}</text>",
        f"<text x='{LEFT}' y='54' {FONT} font-size='12.5' fill='{MUTED}'>{escape(subtitle)}</text>",
    ]
    for i in range(5):
        value = ymax * i / 4
        y = BOTTOM - (BOTTOM - TOP) * i / 4
        parts.append(f"<line x1='{LEFT}' x2='{W - RIGHT}' y1='{y}' y2='{y}' stroke='{GRID}' stroke-width='1'/>")
        parts.append(f"<text x='{LEFT - 8}' y='{y + 4}' text-anchor='end' {FONT} font-size='11' fill='{MUTED}'>{fmt(value)}</text>")
    parts.append(
        f"<text transform='translate(18 {(TOP + BOTTOM) / 2}) rotate(-90)' text-anchor='middle' "
        f"{FONT} font-size='11.5' fill='{MUTED}'>{escape(ylabel)}</text>"
    )
    return parts


def legend(parts, names):
    x = W - RIGHT + 24
    for i, name in enumerate(names):
        y = TOP + 6 + i * 22
        parts.append(f"<rect x='{x}' y='{y - 9}' width='12' height='12' rx='2' fill='{SERIES[i]}'/>")
        parts.append(f"<text x='{x + 18}' y='{y + 1}' {FONT} font-size='12' fill='{INK}'>{escape(name)}</text>")


def line_chart(path, title, subtitle, xlabel, ylabel, xs, series, xformat=fmt):
    """series : {nom: [(moyenne, ecart_type), ...]} aligne sur xs."""
    ymax = nice_max(max(m + s for points in series.values() for m, s in points) * 1.05)
    parts = frame(title, subtitle, ylabel, ymax)
    x0, x1 = LEFT + 16, W - RIGHT - 16
    xmax = max(xs)

    def px(x):
        return x0 + (x1 - x0) * x / xmax

    def py(y):
        return BOTTOM - (BOTTOM - TOP) * y / ymax

    for x in xs:
        parts.append(f"<text x='{px(x)}' y='{BOTTOM + 18}' text-anchor='middle' {FONT} font-size='11' fill='{MUTED}'>{xformat(x)}</text>")
    parts.append(f"<text x='{(x0 + x1) / 2}' y='{BOTTOM + 40}' text-anchor='middle' {FONT} font-size='11.5' fill='{MUTED}'>{escape(xlabel)}</text>")
    parts.append(f"<line x1='{LEFT}' x2='{W - RIGHT}' y1='{BOTTOM}' y2='{BOTTOM}' stroke='{MUTED}' stroke-width='1'/>")

    for i, (name, points) in enumerate(series.items()):
        color = SERIES[i]
        coords = [(px(x), py(m)) for x, (m, _) in zip(xs, points)]
        parts.append(
            f"<polyline points='{' '.join(f'{a:.1f},{b:.1f}' for a, b in coords)}' fill='none' "
            f"stroke='{color}' stroke-width='2' stroke-linejoin='round' stroke-linecap='round'/>"
        )
        for x, (m, s) in zip(xs, points):
            if s > 0:
                parts.append(f"<line x1='{px(x)}' x2='{px(x)}' y1='{py(m - s)}' y2='{py(m + s)}' stroke='{color}' stroke-width='1.5' opacity='0.55'/>")
            parts.append(f"<circle cx='{px(x)}' cy='{py(m)}' r='4' fill='{color}' stroke='{SURFACE}' stroke-width='2'><title>{escape(name)} : {m:.1f} ms ± {s:.1f}</title></circle>")
    if len(series) > 1:
        legend(parts, list(series))
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")
    print("->", path)


def bar_chart(path, title, subtitle, ylabel, groups, series):
    """series : {nom: [(moyenne, ecart_type) par groupe]}."""
    ymax = nice_max(max(m + s for points in series.values() for m, s in points) * 1.05)
    parts = frame(title, subtitle, ylabel, ymax)
    x0, x1 = LEFT + 10, W - RIGHT - 10
    slot = (x1 - x0) / len(groups)
    bar = min(46, slot * 0.7 / len(series))
    gap = 2

    def py(y):
        return BOTTOM - (BOTTOM - TOP) * y / ymax

    for g, group in enumerate(groups):
        center = x0 + slot * (g + 0.5)
        start = center - (len(series) * bar + (len(series) - 1) * gap) / 2
        for i, (name, points) in enumerate(series.items()):
            m, s = points[g]
            x = start + i * (bar + gap)
            top = py(m)
            height = BOTTOM - top
            radius = min(4, height / 2)
            parts.append(
                f"<path d='M{x},{BOTTOM} V{top + radius} Q{x},{top} {x + radius},{top} "
                f"H{x + bar - radius} Q{x + bar},{top} {x + bar},{top + radius} V{BOTTOM} Z' fill='{SERIES[i]}'>"
                f"<title>{escape(name)}, {escape(group)} : {m:.1f} ms ± {s:.1f}</title></path>"
            )
            if s > 0:
                cx = x + bar / 2
                parts.append(f"<line x1='{cx}' x2='{cx}' y1='{py(m - s)}' y2='{py(m + s)}' stroke='{INK}' stroke-width='1.2'/>")
                parts.append(f"<line x1='{cx - 4}' x2='{cx + 4}' y1='{py(m + s)}' y2='{py(m + s)}' stroke='{INK}' stroke-width='1.2'/>")
            parts.append(f"<text x='{x + bar / 2}' y='{top - 6 if s == 0 else py(m + s) - 6}' text-anchor='middle' {FONT} font-size='10.5' fill='{INK}'>{fmt(m)}</text>")
        parts.append(f"<text x='{center}' y='{BOTTOM + 18}' text-anchor='middle' {FONT} font-size='11.5' fill='{INK}'>{escape(group)}</text>")
    parts.append(f"<line x1='{LEFT}' x2='{W - RIGHT}' y1='{BOTTOM}' y2='{BOTTOM}' stroke='{MUTED}' stroke-width='1'/>")
    legend(parts, list(series))
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")
    print("->", path)


def mean_std(row):
    return float(row["moyenne_ms"]), float(row["ecart_type_ms"])


def main(folder):
    folder = Path(folder)

    rows = read(folder / "volume.csv")
    xs = sorted({int(r["livres"]) for r in rows})
    words = list(dict.fromkeys(r["requete"] for r in rows))
    line_chart(
        folder / "volume.svg",
        "Recherche par mot-clé selon la taille du corpus",
        "Index V2 PostgreSQL, moyenne ± écart-type",
        "Nombre de livres indexés", "Temps de réponse (ms)", xs,
        {w: [mean_std(r) for x in xs for r in rows if r["requete"] == w and int(r["livres"]) == x] for w in words},
    )

    rows = read(folder / "automate.csv")
    xs = sorted({int(r["termes"]) for r in rows})
    patterns = list(dict.fromkeys(r["motif"] for r in rows))
    line_chart(
        folder / "automate.svg",
        "Automate RegEx selon la taille du vocabulaire",
        "Parcours des racines de l'index, moyenne ± écart-type",
        "Termes parcourus (milliers)", "Temps de parcours (ms)", xs,
        {p: [mean_std(r) for x in xs for r in rows if r["motif"] == p and int(r["termes"]) == x] for p in patterns},
        xformat=lambda x: f"{x / 1000:.0f}",
    )

    rows = read(folder / "comparaison.csv")
    regex = [r for r in rows if r["experience"] == "regex"]
    groups = list(dict.fromkeys(r["requete"] for r in regex))
    bar_chart(
        folder / "regex_comparaison.svg",
        "Recherche RegEx : automate vs PostgreSQL",
        "1 700 livres, temps total de la requête, moyenne ± écart-type",
        "Temps de réponse (ms)", groups,
        {
            "Automate (Python)": [mean_std(r) for g in groups for r in regex if r["requete"] == g and r["variante"] == "automate"],
            "Regex PostgreSQL": [mean_std(r) for g in groups for r in regex if r["requete"] == g and r["variante"] == "postgresql"],
        },
    )
    tri = [r for r in rows if r["experience"] == "tri"]
    groups = list(dict.fromkeys(r["requete"] for r in tri))
    bar_chart(
        folder / "tri.svg",
        "Coût du classement : occurrences vs PageRank",
        "Recherche par mot-clé, 1 700 livres, moyenne ± écart-type",
        "Temps de réponse (ms)", groups,
        {
            "Fréquence normalisée": [mean_std(r) for g in groups for r in tri if r["requete"] == g and r["variante"] == "occurrences"],
            "PageRank": [mean_std(r) for g in groups for r in tri if r["requete"] == g and r["variante"] == "pagerank"],
        },
    )

    rows = read(folder / "charge.csv")
    xs = [int(r["clients"]) for r in rows]
    line_chart(
        folder / "charge_latence.svg",
        "Test de charge HTTP : latence",
        "20 requêtes /api/v1/search par client, moyenne ± écart-type",
        "Clients simultanés", "Latence (ms)", xs,
        {"Latence moyenne": [mean_std(r) for r in rows]},
    )
    line_chart(
        folder / "charge_debit.svg",
        "Test de charge HTTP : débit",
        "Requêtes traitées par seconde (un seul processus uvicorn)",
        "Clients simultanés", "Débit (requêtes / s)", xs,
        {"Débit": [(float(r["debit_req_s"]), 0.0) for r in rows]},
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/benchmarks_v2")
