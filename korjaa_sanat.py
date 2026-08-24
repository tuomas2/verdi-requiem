#!/usr/bin/env python3
"""Korjaa konelukemisen sanoitusvirheet lähde-PDF:ää vasten.

Osat 01 ja 14 on luettu Audiveriksella PDF:stä, ja niiden sanoissa on
OCR-virheitä. Molempien PDF:ien sanat ovat kuitenkin oikeaa tekstiä eivät
kuvaa, joten oikea sanoitus saadaan poimittua suoraan lähteestä.
"""
import difflib
import re
import subprocess
import zipfile
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


def _norm(text):
    """Vertailumuoto: pieniksi kirjaimiksi ja välimerkit pois."""
    return text.lower().strip(VALIMERKIT + " ")


def align(syls, slots):
    """Kohdistaa PDF:n tavut olemassa oleviin tavupaikkoihin.

    Palauttaa slots-listan mittaisen listan tavoitetiloja: Syllable jos
    paikalle tulee sana, None jos paikalta poistetaan sana. Vertailu on
    tavutasoinen, joten konelukemisen kirjainvirhe näkyy korvauksena ja
    korvaus kirjoitetaan PDF:n mukaan.

    Kun paikkoja on tavuja enemmän, ylimääräiset jäävät Noneksi — se on
    tapaus jossa yksi tavu on pilkkoutunut kahdelle säkeistölle, tai jossa
    esitysmerkintä on luettu sanaksi. Kun tavuja on paikkoja enemmän,
    ylimääräiset jäävät sijoittamatta; niitä ei lisätä arvaamalla.

    Palauttaa myös montako paikkaa tuli käsitellyksi, jotta kursori osaa
    siirtyä myös poistettujen paikkojen yli. Ikkunan lopussa olevat
    paikat, joihin rivi ei ulotu, jäävät koskematta.
    """
    a = [_norm(s.text) for s in slots]
    b = [_norm(s.text) for s in syls]
    target = [None] * len(slots)

    consumed = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            a=a, b=b, autojunk=False).get_opcodes():
        if tag in ("equal", "replace"):
            for k in range(min(i2 - i1, j2 - j1)):
                target[i1 + k] = syls[j1 + k]
        if j2 > j1:
            consumed = max(consumed, i2)
    return target, consumed


@dataclass
class Match:
    """Yhden äänen kohdistuksen tulos."""

    target: list   # tavoitetila per paikka, pituus = paikkojen määrä
    reached: int   # montako paikkaa alusta tuli kohdistetuksi
    used: list     # rivit jotka tunnistettiin tämän äänen riveiksi
    skipped: list  # rivit jotka ohitettiin toisen äänen riveinä


# Ikkuna otetaan yhtä paikkaa tavumäärää pidempänä. Silloin rivin loppuun
# osuva ylimääräinen paikka mahtuu mukaan poistettavaksi, mutta ikkuna ei
# ulotu seuraavan rivin paikkoihin niin että ne katoaisivat.
SLACK = 1

# Osuman on alettava kursorin kohdalta. Pari paikkaa liukumaa sallitaan,
# koska konelukeminen on voinut rikkoa juuri rivin ensimmäisen tavun.
HEAD = 2


def _score(syls, slots):
    """Rivin osuvuus paikkoihin kursorista alkaen, parina.

    Ensimmäinen luku on se joka ratkaisee: kuinka suuri osa rivin tavuista
    osuu. Ankkurointi on olennainen — ilman sitä pitkä rivi voi saada
    korkean arvon osumalla ikkunan loppupäähän, ja tulla valituksi sitä
    riviä ennen jonka paikoille se ei kuulu.

    Toinen luku ratkaisee tasapelin. Samassa systeemissä äänet laulavat
    usein samat sanat mutta eri välimerkeillä, ja välimerkeistä PDF:n rivit
    eivät kerro kummalle ne kuuluvat. Silloin lähimmäksi konelukemisen omaa
    tekstiä osuva rivi on oikea: se on tämän äänen rivi.
    """
    a = [_norm(s.text) for s in slots]
    b = [_norm(s.text) for s in syls]
    blocks = [bl for bl in difflib.SequenceMatcher(
        a=a, b=b, autojunk=False).get_matching_blocks() if bl.size]
    if not blocks or blocks[0].a > HEAD or blocks[0].b > HEAD:
        return (0.0, 0.0)
    share = sum(bl.size for bl in blocks) / len(syls)
    exact = difflib.SequenceMatcher(
        a=[s.text for s in slots], b=[s.text for s in syls],
        autojunk=False).ratio()
    return (share, exact)


def match_part(rows, slots, threshold=0.55, lookahead=8):
    """Kohdistaa yhden äänen tavupaikat PDF:n riveihin.

    PDF:n rivit ovat kaikkien äänten rivejä sekaisin, järjestyksessä ylhäältä
    alas. Rivi hyväksytään kun se vastaa riittävän hyvin kursorin kohdalla
    olevia paikkoja, muuten se ohitetaan toisen äänen rivinä.

    Samassa systeemissä äänet laulavat usein samaa tekstiä, jolloin valinta
    niiden välillä on yhdentekevä. Siksi ehdokkaista otetaan paras eikä
    ensimmäinen: siellä missä tekstit eroavat, ero itse ratkaisee valinnan.

    Palauttaa Matchin. Sen reached kertoo mihin asti paikat tulivat
    kohdistetuiksi: sen jälkeen tuleva tyhjä tavoitetila ei tarkoita
    poistoa vaan sitä, ettei yksikään rivi ulottunut niin pitkälle.
    """
    target = [None] * len(slots)
    used, skipped = [], []
    cursor, i = 0, 0

    while i < len(rows) and cursor < len(slots):
        best = None
        for j in range(i, min(i + lookahead, len(rows))):
            syls = tokenise(rows[j].text)
            if not syls:
                continue
            score = _score(syls, slots[cursor:cursor + len(syls) + SLACK])
            if score[0] >= threshold and (best is None or score > best[0]):
                best = (score, j, syls)

        if best is None:
            skipped.append(rows[i])
            i += 1
            continue

        _, j, syls = best
        skipped.extend(rows[i:j])
        window = slots[cursor:cursor + len(syls) + SLACK]
        part, consumed = align(syls, window)
        target[cursor:cursor + consumed] = part[:consumed]
        cursor += consumed
        used.append(rows[j])
        i = j + 1

    return Match(target, cursor, used, skipped)


@dataclass
class Slot:
    """Yksi olemassa oleva tavupaikka: <lyric> jonkin nuotin alla."""

    measure: int
    note: ET.Element
    element: ET.Element

    @property
    def syllable(self):
        return Syllable(self.element.findtext("text") or "",
                        self.element.findtext("syllabic") or "single")


def load(path):
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist()
                    if not n.startswith("META-INF") and n.lower().endswith(".xml"))
        return ET.fromstring(z.read(name))


def find_part(root, part_id):
    return next(p for p in root.iter("part") if p.get("id") == part_id)


def read_slots(part):
    """Osaston tavupaikat järjestyksessä.

    Yksikkö on <lyric> eikä nuotti, koska konelukeminen on paikoin pannut
    yhden tavun puolikkaat samalle nuotille eri säkeistöiksi. Kohdistus
    tarvitsee ne erikseen.
    """
    slots = []
    for measure in part.iter("measure"):
        number = int(measure.get("number"))
        for note in measure.iter("note"):
            for lyric in note.iter("lyric"):
                slots.append(Slot(number, note, lyric))
    return slots
