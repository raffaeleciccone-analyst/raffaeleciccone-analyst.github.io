"""Disegna le due figure delle schede Olist e coorti, leggibili alla larghezza della scheda.

Fino al 3/10/2026 le schede mostravano lo screenshot intero del cruscotto e della matrice:
ridotti a ~530 px il testo scendeva a 4-5 px e non si leggeva niente (revisione del 3/10/2026).
Qui ogni scheda ha UN grafico, con i numeri grandi; il clic porta ancora alla schermata
intera.

I numeri non sono ricopiati a mano:
  - Olist: ricalcolati dai CSV originali con le stesse regole del modello Power BI
    (ritardo per data, fasce di 02-Ordini.m, voto = media dei punteggi, negativa = <= 2,
    "prima del pacco" = prima risposta prima della consegna). Lo script si ferma se non
    ritrova le cifre pubblicate nel report.
  - coorti: medie per mese del calendario dalla matrice pubblicata nel repository, con lo
    stesso controllo contro RISULTATI.md.

Le figure sono 720x450: le schede ritagliano le immagini a 16:10 partendo dall'alto a
sinistra, e una figura gia' in 16:10 non perde niente.

Uso:  python grafici_vetrina.py
"""
from pathlib import Path

import pandas as pd

SITO = Path(r"C:/dev/raffaeleciccone-analyst.github.io")
OLIST = Path(r"C:/dev/_powerbi/dati_grezzi/csv")
COORTI = Path(r"C:/dev/clienti-che-tornano/risultati/matrice_retention.csv")

# gli stessi colori di grafico_tpi_eta.py e della pagina
INK, INK_SOFT, INK_FAINT = "#15191B", "#4E5658", "#828C8E"
ACCENT, ACCENT_SOFT, GRIGIO = "#16565C", "#8DB3B6", "#C3C8C9"
SANS = "Archivo,system-ui,sans-serif"
MONO = "ui-monospace,Consolas,monospace"
W, H = 720, 450


def virgola(x, dec=1):
    return f"{x:.{dec}f}".replace(".", ",")


def testo(x, y, s, size=15, fill=INK, anchor="start", font=SANS, weight=400, extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>{s}</text>')


def svg(corpo, titolo, desc):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'role="img" aria-labelledby="t d"><title id="t">{titolo}</title><desc id="d">{desc}</desc>'
            f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>' + "".join(corpo) + "</svg>")


# ── Olist: recensioni negative per fascia di consegna ─────────────────────
def olist():
    o = pd.read_csv(OLIST / "olist_orders_dataset.csv",
                    parse_dates=["order_delivered_customer_date", "order_estimated_delivery_date"])
    o = o[(o.order_status == "delivered") & o.order_delivered_customer_date.notna()].copy()
    o["g"] = (o.order_delivered_customer_date.dt.normalize()
              - o.order_estimated_delivery_date.dt.normalize()).dt.days
    o["f"] = pd.cut(o.g, [-10**6, -10, -5, 0, 3, 7, 15, 30, 10**6], labels=range(8)).astype(int)
    r = pd.read_csv(OLIST / "olist_order_reviews_dataset.csv", parse_dates=["review_answer_timestamp"])
    r = r.groupby("order_id").agg(voto=("review_score", "mean"),
                                  prima=("review_answer_timestamp", "min")).reset_index()
    x = o.merge(r, on="order_id", how="left")
    x["rec"] = x.voto.notna()
    x["neg"] = x.voto <= 2
    x["pp"] = x.rec & x.prima.notna() & (x.prima < x.order_delivered_customer_date)
    righe = []
    for f in range(8):
        s = x[x.f == f]
        den = s.rec.sum()
        prima = 100 * (s.neg & s.pp).sum() / den
        dopo = 100 * (s.neg & ~s.pp & s.rec).sum() / den
        righe.append((dopo, prima))

    # le cifre che il report pubblica: se non tornano, la figura non si scrive
    attese = {0: 8.9, 1: 9.6, 2: 11.3}
    for f, v in attese.items():
        assert round(sum(righe[f]), 1) == v, (f, righe[f])
    assert [round(righe[f][1], 1) for f in (3, 4, 5, 6, 7)] == [17.8, 63.0, 79.0, 81.7, 66.6]
    assert round(righe[3][0], 1) == 14.4 and round(righe[4][0], 1) == 4.6

    nomi = ["10+ gg in anticipo", "5-9 gg in anticipo", "0-4 gg in anticipo", "1-3 gg di ritardo",
            "4-7 gg di ritardo", "8-15 gg di ritardo", "16-30 gg di ritardo", "oltre 30 gg di ritardo"]
    L, R, T, passo, alto = 172, 58, 92, 41, 26
    larg = W - L - R
    c = [testo(24, 34, "Recensioni negative per fascia di consegna", 20, INK, weight=700),
         testo(24, 60, "Sugli ordini in ritardo quasi tutte le recensioni negative arrivano prima del pacco",
               14, INK_SOFT)]
    # legenda
    lx = 24
    for col, nome in [(GRIGIO, "in orario"), (ACCENT_SOFT, "in ritardo, col pacco"),
                      (ACCENT, "in ritardo, prima del pacco")]:
        c.append(f'<rect x="{lx}" y="{H-30}" width="12" height="12" fill="{col}"/>')
        c.append(testo(lx + 18, H - 20, nome, 13, INK_SOFT))
        lx += 34 + 7.2 * len(nome)
    for i, (dopo, prima) in enumerate(righe):
        y = T + i * passo
        c.append(testo(L - 12, y + alto * 0.72, nomi[i], 14, INK_SOFT, "end"))
        x0 = L
        if i < 3:
            w = larg * dopo / 100
            c.append(f'<rect x="{x0}" y="{y}" width="{w:.1f}" height="{alto}" fill="{GRIGIO}"/>')
        else:
            w1, w2 = larg * dopo / 100, larg * prima / 100
            c.append(f'<rect x="{x0}" y="{y}" width="{w1:.1f}" height="{alto}" fill="{ACCENT_SOFT}"/>')
            c.append(f'<rect x="{x0 + w1 + 1:.1f}" y="{y}" width="{max(w2 - 1, 0):.1f}" height="{alto}" fill="{ACCENT}"/>')
            w = w1 + w2
        c.append(testo(L + w + 8, y + alto * 0.72, virgola(dopo + prima) + "%", 15, INK,
                       weight=600))
    return svg(c, "Recensioni negative per fascia di consegna, Olist",
               "Recensioni negative per fascia di anticipo o ritardo della consegna su 95.824 ordini "
               "recensiti: 8,9%, 9,6% e 11,3% in orario; 32,2%, 67,6%, 80,0%, 82,1% e 67,8% in "
               "ritardo, quasi tutte scritte prima di ricevere il pacco.")


# ── coorti: retention per mese del calendario ──────────────────────────────
def coorti():
    m = pd.read_csv(COORTI)
    valori = []
    for _, r in m.iterrows():
        mese = int(r.coorte.split("-")[1])
        for k in range(1, 23):
            v = r[str(k)]
            if pd.notna(v):
                valori.append(((mese - 1 + k) % 12 + 1, v))
    medie = pd.DataFrame(valori, columns=["mese", "v"]).groupby("mese").v.mean()
    # RISULTATI.md, sezione 2
    pubblicate = [11.3, 12.0, 15.9, 15.4, 18.4, 17.3, 16.5, 15.6, 19.6, 21.7, 25.0, 13.8]
    assert [round(medie[i], 1) for i in range(1, 13)] == pubblicate, medie

    mesi = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
    L, R, T, B = 40, 24, 96, 62
    alto = H - T - B
    passo = (W - L - R) / 12
    larg = passo * 0.68
    top = 28.0
    c = [testo(24, 34, "Quanti clienti tornano, per mese del calendario", 20, INK, weight=700),
         testo(24, 60, "Media su tutte le coorti di un e-commerce UK, 2010-2011", 14, INK_SOFT),
         f'<line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" stroke="{INK}" stroke-width="1"/>']
    for i, nome in enumerate(mesi):
        v = medie[i + 1]
        h = alto * v / top
        x = L + i * passo + (passo - larg) / 2
        col = ACCENT if nome in ("nov",) else (INK_FAINT if nome == "feb" else GRIGIO)
        c.append(f'<rect x="{x:.1f}" y="{H-B-h:.1f}" width="{larg:.1f}" height="{h:.1f}" fill="{col}"/>')
        c.append(testo(x + larg / 2, H - B - h - 7, virgola(v), 14,
                       ACCENT if nome == "nov" else INK, "middle",
                       weight=700 if nome in ("nov", "feb") else 400))
        c.append(testo(x + larg / 2, H - B + 20, nome, 14, INK_SOFT, "middle"))
    c.append(testo(24, H - 14, "% di clienti di ogni coorte che compra in quel mese. Dicembre e "
                   "gennaio hanno un anno solo di dati.", 12, INK_FAINT))
    return svg(c, "Retention per mese del calendario",
               "Percentuale media di clienti che tornano a comprare, per mese del calendario: "
               "massimo a novembre (25,0%), minimo a gennaio e febbraio (11,3% e 12,0%).")


if __name__ == "__main__":
    for nome, f in [("ritardi-fasce.svg", olist), ("coorti-mesi.svg", coorti)]:
        (SITO / "assets" / nome).write_text(f(), encoding="utf-8")
        print("scritto", nome)
