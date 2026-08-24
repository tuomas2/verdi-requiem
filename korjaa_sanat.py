#!/usr/bin/env python3
"""Korjaa konelukemisen sanoitusvirheet lähde-PDF:ää vasten.

Osat 01 ja 14 on luettu Audiveriksella PDF:stä, ja niiden sanoissa on
OCR-virheitä. Molempien PDF:ien sanat ovat kuitenkin oikeaa tekstiä eivät
kuvaa, joten oikea sanoitus saadaan poimittua suoraan lähteestä.
"""
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass

VALIMERKIT = ",.;:!?"


@dataclass(frozen=True)
class Syllable:
    """Yksi tavu: teksti välimerkkeineen ja asema sanassa."""

    text: str
    syllabic: str  # single | begin | middle | end


def tokenise(row):
    """Pilkkoo PDF:stä poimitun sanarivin tavuiksi.

    PDF:n välistys on epätasaista — tavuviivan ympärillä on välilyönti
    milloin sattuu — joten välit siivotaan ensin pois viivan ja välimerkin
    ympäriltä. Sen jälkeen sanaraja on välilyönti ja tavuraja viiva.
    """
    s = re.sub(r"\s*-\s*", "-", row)
    s = re.sub(r"\s+([" + VALIMERKIT + r"])", r"\1", s)

    out = []
    for word in s.split():
        parts = word.split("-")
        # Tyhjä osa alussa tarkoittaa että sana jatkaa edellistä tavua,
        # tyhjä lopussa että tavu jatkuu seuraavaan.
        jatkaa_alussa = parts[0] == ""
        jatkuu_lopussa = parts[-1] == ""
        core = [p for p in parts if p]

        for i, p in enumerate(core):
            viiva_ennen = jatkaa_alussa if i == 0 else True
            viiva_jalkeen = jatkuu_lopussa if i == len(core) - 1 else True
            if viiva_ennen and viiva_jalkeen:
                syllabic = "middle"
            elif viiva_jalkeen:
                syllabic = "begin"
            elif viiva_ennen:
                syllabic = "end"
            else:
                syllabic = "single"
            out.append(Syllable(p, syllabic))
    return out


@dataclass(frozen=True)
class Row:
    """Yhden äänen sanat yhdessä systeemissä."""

    page: int
    y: float
    text: str


def _clean(s):
    """Siivoaa välit tavuviivan ja välimerkin ympäriltä."""
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"\s+([" + VALIMERKIT + r"])", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def _stext(pdf_path, pages):
    cmd = ["mutool", "draw", "-F", "stext", "-o", "-", pdf_path]
    if pages:
        cmd.append(",".join(str(p) for p in pages))
    done = subprocess.run(cmd, capture_output=True, check=True)
    return ET.fromstring(done.stdout)


def extract_rows(pdf_path, font, pages=None):
    """Poimii sanarivit PDF:stä, yksi rivi per ääni per systeemi.

    Sanat ovat samaa fonttia kuin viivastomerkinnät ("4 Soli", "Tutti"),
    mutta pienempää kokoa. Koko päätellään aineistosta: se on tämän fontin
    yleisin, koska sanoja on merkintöjä enemmän.
    """
    root = _stext(pdf_path, pages)

    sizes = Counter()
    for f in root.iter("font"):
        if f.get("name") == font:
            sizes[round(float(f.get("size")), 2)] += len(list(f.iter("char")))
    if not sizes:
        return []
    lyric_size = sizes.most_common(1)[0][0]

    rows = []
    for i, page in enumerate(root.iter("page")):
        number = pages[i] if pages else i + 1
        by_baseline = {}
        for f in page.iter("font"):
            if f.get("name") != font:
                continue
            if round(float(f.get("size")), 2) != lyric_size:
                continue
            size = float(f.get("size"))
            for ch in f.iter("char"):
                quad = [float(v) for v in ch.get("quad").split()]
                y = round(float(ch.get("y")), 1)
                by_baseline.setdefault(y, []).append(
                    (quad[0], quad[2], ch.get("c"), size))

        for y in sorted(by_baseline):
            out, edge = [], None
            for left, right, c, size in sorted(by_baseline[y]):
                # Väli päätellään edellisen merkin oikeasta reunasta, ei
                # sen alusta: leveä kirjain ei ole väli.
                if edge is not None and left - edge > 0.15 * size:
                    out.append(" ")
                out.append(c)
                edge = right
            text = _clean("".join(out))
            if text:
                rows.append(Row(number, y, text))
    return rows
