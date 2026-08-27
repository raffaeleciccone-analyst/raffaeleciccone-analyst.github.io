"""Allinea i numeri della vetrina a quelli che il sito pubblica davvero.

La scheda del Football Scout Index dice quanti giocatori ordina l'indice, quante
righe ha il database e quante verifiche sono pubblicate. Erano scritti a mano, e
si erano gia' staccati dai dati: 354 giocatori quando erano 356, 23.816 righe
quando erano 23.858.

Su un progetto che si vende sul rigore quello e' il difetto peggiore possibile:
e' la prima cosa che un valutatore attento puo' controllare in dieci secondi,
aprendo la demo accanto alla vetrina, ed e' l'unica in cui non c'e' margine di
spiegazione.

I numeri arrivano da dove arrivano quelli del sito — il payload pubblicato e la
sintesi delle verifiche — tranne le righe del database, che il sito non espone e
che quindi si contano dal database stesso.

Uso:  python aggiorna_numeri_vetrina.py            (anteprima)
      python aggiorna_numeri_vetrina.py --esegui    (scrive)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SITO = Path(r"C:/dev/raffaeleciccone-analyst.github.io")
PAGINA = SITO / "index.html"
SERIE_A = Path(r"C:/dev/serie-a-index")
MOTORE = Path(r"C:/dev/serie-a-index-engine")


def _righe_database() -> int | None:
    """Le righe giocatore-partita, contate dal database. None se non risponde."""
    try:
        sys.path.insert(0, str(MOTORE))
        import config
        import mysql.connector

        cx = mysql.connector.connect(host=config.DB_HOST, user=config.DB_USER,
                                     password=config.DB_PASSWORD,
                                     database=config.DB_NAME, connection_timeout=5)
        cur = cx.cursor()
        cur.execute("SELECT COUNT(*) FROM giocatore_partita")
        n = cur.fetchone()[0]
        cx.close()
        return int(n)
    except Exception as e:
        print(f"  database non raggiungibile ({type(e).__name__}): lascio le righe come stanno")
        return None


def _formatta(n: int) -> str:
    """23858 -> '23.858', come gia' scritto in pagina."""
    return f"{n:,}".replace(",", ".")


def main() -> None:
    esegui = "--esegui" in sys.argv

    payload = json.loads((SERIE_A / "payload.json").read_text(encoding="utf-8"))
    sintesi = json.loads((SERIE_A / "validazione_sintesi.json").read_text(encoding="utf-8"))
    qualificati = int(payload["n_giocatori"])
    verifiche = int(sintesi["n_verifiche"])
    righe = _righe_database()

    html = PAGINA.read_text(encoding="utf-8")
    originale = html

    # I giocatori qualificati: nel claim, nel corpo, nell'alt del grafico e nella
    # didascalia. Si cerca il numero vecchio accanto alla parola "giocatori",
    # cosi' non si tocca nessun altro numero della pagina.
    vecchi_gioc = sorted(set(re.findall(r"\b(\d{3})\s+giocatori", html)))
    for v in vecchi_gioc:
        if int(v) != qualificati:
            html = re.sub(r"\b%s(\s+giocatori)" % v, r"%d\1" % qualificati, html)

    # Le righe del database, sempre accanto alla parola "righe".
    if righe is not None:
        atteso = _formatta(righe)
        for v in sorted(set(re.findall(r"\b(\d{1,3}(?:\.\d{3})+)\s+righe", html))):
            if v != atteso:
                html = html.replace(f"{v} righe", f"{atteso} righe")
        # anche la forma "un database di 23.816 righe" nel claim e' coperta sopra

    print(f"  giocatori qualificati : {qualificati}")
    print(f"  verifiche pubblicate  : {verifiche}")
    print(f"  righe giocatore-partita: {righe if righe is not None else 'non letto'}")

    if html == originale:
        print("\n  I numeri in pagina sono gia' allineati.")
        return

    diff = [(a, b) for a, b in zip(originale.splitlines(), html.splitlines()) if a != b]
    print(f"\n  {len(diff)} righe da cambiare:")
    for a, b in diff[:8]:
        print(f"    - {a.strip()[:96]}")
        print(f"    + {b.strip()[:96]}")

    if not esegui:
        print("\nAnteprima soltanto. Rilancia con --esegui per scrivere.")
        return

    PAGINA.write_text(html, encoding="utf-8")
    print(f"\n{PAGINA} aggiornata.")


if __name__ == "__main__":
    main()
