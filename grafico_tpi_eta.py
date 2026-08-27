"""Genera il grafico TPI/eta' per la vetrina, dal CSV pubblicato del Serie A Scout Index.

Uso:  python grafico_tpi_eta.py
Legge:   C:/dev/serie-a-index/serie_a_tpi_2025-26.csv   (i qualificati pubblicati)
Scrive:  C:/dev/raffaeleciccone-analyst.github.io/assets/tpi-eta.svg

Il grafico e' SVG generato dai dati, non un'immagine disegnata a mano: rilanciando lo
script dopo un aggiornamento del CSV, la figura in pagina si aggiorna da sola. I colori
sono quelli di index.html, cosi' il grafico non sembra incollato da un altro posto.

Scrive DENTRO il repo del sito, non in una cartella accanto allo script. Prima
finiva in ./assets: rigenerarlo non cambiava niente in pagina finche' qualcuno
non copiava il file a mano, e infatti il sito ha portato per giorni un grafico
piu' vecchio di quello che lo script produceva.
"""

import csv
from pathlib import Path

CSV = Path(r"C:/dev/serie-a-index/serie_a_tpi_2025-26.csv")
SITO = Path(r"C:/dev/raffaeleciccone-analyst.github.io")
OUT = SITO / "assets" / "tpi-eta.svg"

# palette di index.html
INK, INK_SOFT, INK_FAINT = "#15191B", "#4E5658", "#828C8E"
RULE, ACCENT, PAPER2 = "#D9D9D2", "#16565C", "#EFEFEB"

W, H = 720, 430
L, R, T, B = 56, 18, 22, 48          # margini
X0, X1 = 18.0, 42.0                  # eta'
Y0, Y1 = -1.4, 2.0                   # TPI
GIOVANE = 23.0                       # soglia "ancora rivendibile"
SOGLIA_TPI = 0.40                    # sopra: gia' nella parte alta dell'indice

px = lambda e: L + (e - X0) / (X1 - X0) * (W - L - R)
py = lambda t: T + (Y1 - t) / (Y1 - Y0) * (H - T - B)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    righe = []
    with CSV.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            e, t = num(r["eta"]), num(r["TPI_totale"])
            if e is not None and t is not None:
                righe.append((r["giocatore"], r["squadra"], r["ruolo"], e, t))

    giovani = sorted(
        [x for x in righe if x[3] <= GIOVANE and x[4] >= SOGLIA_TPI], key=lambda x: -x[4]
    )
    massimo = max(righe, key=lambda x: x[4])

    s = []
    add = s.append
    add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'role="img" aria-labelledby="t-tpi d-tpi" style="width:100%;height:auto">')
    # Il conteggio si conta. Era "354" scritto qui dentro, e questo e' il nome
    # che uno screen reader annuncia al posto della figura: l'unico testo che
    # sostituisce il grafico per chi non lo vede, ed era gia' sbagliato di due.
    add(f'<title id="t-tpi">Indice TPI per eta\u0300, {len(righe)} giocatori di Serie A</title>')
    add(f'<desc id="d-tpi">Grafico a dispersione: in orizzontale l\u2019eta\u0300, in verticale '
        f'l\u2019indice TPI. La parte alta e\u0300 occupata quasi tutta da giocatori fra i 27 e '
        f'i 31 anni. La fascia evidenziata a sinistra raccoglie i {len(giovani)} giocatori '
        f'fino a {GIOVANE:.0f} anni che stanno gia\u0300 sopra {SOGLIA_TPI}.</desc>')

    # fascia dei giovani
    add(f'<rect x="{px(X0):.1f}" y="{T}" width="{px(GIOVANE)-px(X0):.1f}" '
        f'height="{H-T-B}" fill="{PAPER2}"/>')

    # griglia
    for t in (-1, 0, 1, 2):
        y = py(t)
        forte = t == 0
        add(f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" '
            f'stroke="{INK_FAINT if forte else RULE}" stroke-width="{1 if forte else 0.8}"'
            f'{"" if forte else ' stroke-dasharray="2 3"'}/>')
        add(f'<text x="{L-9}" y="{y+3.5:.1f}" text-anchor="end" font-family="ui-monospace,'
            f'Consolas,monospace" font-size="10" fill="{INK_FAINT}">{t:+d}</text>')
    for e in (20, 25, 30, 35, 40):
        x = px(e)
        add(f'<text x="{x:.1f}" y="{H-B+16}" text-anchor="middle" font-family="ui-monospace,'
            f'Consolas,monospace" font-size="10" fill="{INK_FAINT}">{e}</text>')

    # punti
    for nome, _sq, _ruolo, e, t in righe:
        if not (X0 <= e <= X1):
            continue
        giovane = e <= GIOVANE and t >= SOGLIA_TPI
        add(f'<circle cx="{px(e):.1f}" cy="{py(t):.1f}" r="{4.2 if giovane else 2.8}" '
            f'fill="{ACCENT if giovane else INK_SOFT}" '
            f'opacity="{0.95 if giovane else 0.28}"/>')

    # etichette: il primo dell'indice, piu' i tre giovani piu' alti
    def etichetta(nome, e, t, dx, dy, ancora="start"):
        add(f'<text x="{px(e)+dx:.1f}" y="{py(t)+dy:.1f}" text-anchor="{ancora}" '
            f'font-family="Archivo,system-ui,sans-serif" font-size="11" font-weight="500" '
            f'fill="{INK}">{nome}</text>')

    # Posizionate a mano e non in ciclo: i primi due della fascia giovane stanno a
    # 1.04 e 1.00 di TPI, cioe' a quattro pixel l'uno dall'altro, e con lo stesso
    # scostamento le due scritte si sovrappongono. Il secondo va a sinistra.
    etichetta(massimo[0], massimo[3], massimo[4], -9, 4, "end")
    posti = [(9, 4, "start"), (-9, 4, "end"), (9, 4, "start")]
    for (nome, _sq, _r, e, t), (dx, dy, anc) in zip(giovani[:3], posti):
        etichetta(nome, e, t, dx, dy, anc)

    # assi
    add(f'<line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" stroke="{INK}" stroke-width="1"/>')
    add(f'<text x="{W-R}" y="{H-B+34}" text-anchor="end" font-family="ui-monospace,Consolas,'
        f'monospace" font-size="10" letter-spacing="0.08em" fill="{INK_FAINT}">'
        f'ET\u00c0 AL 20 AGOSTO 2026</text>')
    add(f'<text x="{L-9}" y="{T-8}" text-anchor="end" font-family="ui-monospace,Consolas,'
        f'monospace" font-size="10" letter-spacing="0.08em" fill="{INK_FAINT}">TPI</text>')
    add(f'<text x="{px(X0)+8:.1f}" y="{T+16}" font-family="ui-monospace,Consolas,monospace" '
        f'font-size="10" letter-spacing="0.06em" fill="{ACCENT}">FINO A {GIOVANE:.0f} ANNI</text>')
    add("</svg>")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(s), encoding="utf-8")
    print(f"scritto {OUT}  ({len(righe)} giocatori, {len(giovani)} nella fascia evidenziata)")
    print("i tre etichettati:", ", ".join(f"{g[0]} ({g[3]:.0f}, TPI {g[4]:.2f})" for g in giovani[:3]))
    print("massimo assoluto:", f"{massimo[0]} ({massimo[3]:.0f}, TPI {massimo[4]:.2f})")


if __name__ == "__main__":
    main()
