def _read_asset(name: str) -> str:
    """
    Legge un file JS dagli assets e lo restituisce come stringa,
    con le sequenze che rompono l'inline HTML opportunamente escaapate.

    Problema: se il JS contiene "</script>" (anche senza ">"),
    o "<!--", o alcuni caratteri Unicode speciali, il browser
    chiude il tag <script> in anticipo o si confonde.

    Soluzione: escape di tutte le sequenze problematiche note,
    secondo le specifiche HTML5 per i tag <script> inline.
    """
    js = (_ASSETS_DIR / name).read_text(encoding="utf-8")

    # 1. Escape di "</script" (CON O SENZA ">") — la più critica.
    #    Il backslash in JS non fa nulla davanti a "/", quindi il codice
    #    resta semanticamente identico ma l'HTML non vede "</script".
    js = js.replace("</script", "<\\/script")

    # 2. Escape di "<!--" che apre un commento HTML
    js = js.replace("<!--", "<\\!--")

    # 3. Escape dei line separator Unicode (U+2028 e U+2029)
    #    Sono validi in JS ma NON in HTML/JSON — rompono il parsing
    js = js.replace("\u2028", "\\u2028")
    js = js.replace("\u2029", "\\u2029")

    return js
