"""Génère les graphiques SVG des performances P1."""

import csv
from pathlib import Path
from xml.sax.saxutils import escape

SOURCE = Path("docs/benchmark_p1_full.csv")


def plot(mode, rows):
    width, height = 900, 510
    left, top, bottom = 100, 85, 400
    plot_height = bottom - top
    maximum = max(
        float(r["moyenne_ms"]) + float(r["ecart_type_ms"])
        for r in rows
    ) * 1.25

    def y(value):
        return bottom - value / maximum * plot_height

    color = "#3478bd" if mode == "simple" else "#159477"
    title = (
        "Recherche simple"
        if mode == "simple"
        else "Recherche Regex"
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="450" y="38" text-anchor="middle" '
        f'font-family="Arial" font-size="24" font-weight="bold">'
        f'{title}, 1 700 livres</text>',
        '<text x="450" y="63" text-anchor="middle" '
        'font-family="Arial" font-size="14" fill="#555">'
        'Temps moyen ± écart-type, 20 répétitions</text>',
    ]

    for tick in range(5):
        value = maximum * tick / 4
        py = y(value)
        parts.append(
            f'<line x1="{left}" y1="{py:.1f}" '
            f'x2="855" y2="{py:.1f}" stroke="#ddd"/>'
        )
        parts.append(
            f'<text x="88" y="{py + 5:.1f}" text-anchor="end" '
            f'font-family="Arial" font-size="13">'
            f'{value:.0f}</text>'
        )

    parts.append(
        f'<line x1="{left}" y1="{bottom}" x2="855" '
        f'y2="{bottom}" stroke="#333"/>'
    )

    for index, row in enumerate(rows):
        mean = float(row["moyenne_ms"])
        std = float(row["ecart_type_ms"])
        cx = left + (index + 0.5) * 250
        bar_top = y(mean)

        parts.append(
            f'<rect x="{cx - 57:.1f}" y="{bar_top:.1f}" '
            f'width="114" height="{bottom - bar_top:.1f}" '
            f'fill="{color}"/>'
        )

        high = y(mean + std)
        low = y(max(0, mean - std))

        parts.extend([
            f'<line x1="{cx}" y1="{high:.1f}" '
            f'x2="{cx}" y2="{low:.1f}" '
            f'stroke="#222" stroke-width="2"/>',
            f'<line x1="{cx-12}" y1="{high:.1f}" '
            f'x2="{cx+12}" y2="{high:.1f}" '
            f'stroke="#222" stroke-width="2"/>',
            f'<line x1="{cx-12}" y1="{low:.1f}" '
            f'x2="{cx+12}" y2="{low:.1f}" '
            f'stroke="#222" stroke-width="2"/>',
            f'<text x="{cx}" y="430" text-anchor="middle" '
            f'font-family="Arial" font-size="16">'
            f'{escape(row["requete"])}</text>',
            f'<text x="{cx}" y="455" text-anchor="middle" '
            f'font-family="Arial" font-size="13" fill="#444">'
            f'{mean:.2f} ± {std:.2f} ms</text>',
        ])

    parts.append(
        '<text x="25" y="245" text-anchor="middle" '
        'transform="rotate(-90 25 245)" '
        'font-family="Arial" font-size="15">'
        'Temps (ms)</text>'
    )
    parts.append("</svg>")

    output = Path(f"docs/benchmark_p1_{mode}.svg")
    output.write_text("\n".join(parts), encoding="utf-8")
    print(f"Graphique créé : {output}")


def main():
    with SOURCE.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    for mode in ("simple", "regex"):
        selected = [r for r in rows if r["mode"] == mode]
        if not selected:
            raise RuntimeError(f"Aucune mesure pour {mode}")
        plot(mode, selected)


if __name__ == "__main__":
    main()
