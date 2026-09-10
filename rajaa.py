#!/usr/bin/env python3
"""Rajaa PDF-sivun pala PNG-kuvaksi ilman ulkoisia kirjastoja.

**Miksi tämä on olemassa.** Korjauksen tarkistus loppuu aina siihen, että
valmis sivu luetaan takaisin kuvana, ja se pitää tehdä yhteen viivastoon
rajattuna 450 dpi:llä: koko sivu samalla tarkkuudella on lukukelvoton ja 200
dpi on liian karkea tavulle nuottipään päällä. Sen ohjeen antaa skilli
`korvakuulokorjaus`, mutta rajaamiseen ei tässä ympäristössä ole työkalua:
`mutool draw` osaa rasteroida mutta ei rajata, eikä koneella ole PIL:iä,
ImageMagickia, `pdftoppm`:ia eikä `pymupdf`:ää. Tämä tiedosto tekee sen
kolmella standardikirjaston moduulilla: `mutool draw -F ppm` antaa raa'an
bittikartan, josta pala leikataan, ja PNG kirjoitetaan `zlib`illä käsin.

Koordinaatit ovat PDF-pisteitä ja y kasvaa alaspäin — samassa muodossa kuin
`mutool draw -F stext` ne antaa, joten kohta löytyy laskemalla eikä
silmämääräisesti. Tavallinen kulku on siis:

    mutool draw -F stext -o s.xml stemmat/stemma-basso-1.pdf 7
    # etsi s.xml:stä tahtinumeron 607 bbox -> x=131, y=225
    python3 rajaa.py stemmat/stemma-basso-1.pdf 7 30 215 290 295 t607.png

Käyttö:  python3 rajaa.py <pdf> <sivu> <x0> <y0> <x1> <y1> <ulos.png> [dpi]
"""

import struct
import subprocess
import sys
import zlib

DPI = 450


def lue_ppm(data):
    """Pura `mutool draw -F ppm` -tuloste: (leveys, korkeus, pikselit)."""
    kentat, i = [], 0
    while len(kentat) < 4:                    # P6, leveys, korkeus, maksimi
        while data[i:i + 1].isspace():
            i += 1
        j = i
        while not data[j:j + 1].isspace():
            j += 1
        kentat.append(data[i:j])
        i = j
    assert kentat[0] == b"P6", f"odotettiin P6-muotoa, on {kentat[0]!r}"
    assert kentat[3] == b"255", f"odotettiin 8-bittistä, on {kentat[3]!r}"
    return int(kentat[1]), int(kentat[2]), data[i + 1:]


def png(leveys, korkeus, rivit):
    """Pakkaamaton totuus PNG:ksi: 8-bittinen RGB, suodatin 0."""
    def lohko(tunnus, sisalto):
        return (struct.pack(">I", len(sisalto)) + tunnus + sisalto
                + struct.pack(">I", zlib.crc32(tunnus + sisalto)))

    ihdr = struct.pack(">IIBBBBB", leveys, korkeus, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + lohko(b"IHDR", ihdr)
            + lohko(b"IDAT", zlib.compress(b"".join(rivit), 9))
            + lohko(b"IEND", b""))


def rajaa(pdf, sivu, x0, y0, x1, y1, ulos, dpi=DPI):
    raaka = subprocess.run(
        ["mutool", "draw", "-r", str(dpi), "-F", "ppm", "-o", "-",
         pdf, str(sivu)], capture_output=True, check=True).stdout
    leveys, korkeus, pikselit = lue_ppm(raaka)

    s = dpi / 72.0
    cx0, cy0 = max(0, int(x0 * s)), max(0, int(y0 * s))
    cx1, cy1 = min(leveys, int(x1 * s)), min(korkeus, int(y1 * s))
    assert cx1 > cx0 and cy1 > cy0, (
        f"rajaus on tyhjä: {(cx0, cy0, cx1, cy1)} kuvassa {leveys}x{korkeus}")

    # PNG haluaa joka rivin eteen suodatintavun.
    rivit = [b"\x00" + pikselit[(y * leveys + cx0) * 3:(y * leveys + cx1) * 3]
             for y in range(cy0, cy1)]
    with open(ulos, "wb") as f:
        f.write(png(cx1 - cx0, cy1 - cy0, rivit))
    return cx1 - cx0, cy1 - cy0


def main(argv):
    if len(argv) not in (7, 8):
        raise SystemExit(__doc__)
    pdf, sivu, x0, y0, x1, y1, ulos = argv[:7]
    dpi = int(argv[7]) if len(argv) == 8 else DPI
    w, h = rajaa(pdf, int(sivu), *(float(v) for v in (x0, y0, x1, y1)),
                 ulos=ulos, dpi=dpi)
    print(f"kirjoitettu {ulos} ({w}x{h} pikseliä, {dpi} dpi)")


if __name__ == "__main__":
    main(sys.argv[1:])
