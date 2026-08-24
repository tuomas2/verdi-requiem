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

    Palauttaa (tavoitetilat, lo, hi). Väli lo:hi on se osa ikkunasta johon
    rivi ulottui; sen sisällä tyhjä tavoitetila tarkoittaa poistoa. Välin
    ulkopuolelle jäävät paikat eivät ole poistettavia vaan kohdistamattomia.

    Poisto tehdään vain osumien välissä. Ikkunan reunalla evidenssi
    puuttuu: sellainen paikka voi yhtä hyvin olla seuraavan rivin
    ensimmäinen tavu kuin roskaa, joten se jätetään koskematta. Osumien
    välissä oleva paikka sen sijaan on luettu sanaksi jotain joka ei ole
    sana — esitysmerkintä tai dynamiikkamerkki.

    Kun tavuja on paikkoja enemmän, ylimääräiset jäävät sijoittamatta;
    niitä ei lisätä arvaamalla.
    """
    a = [_norm(s.text) for s in slots]
    b = [_norm(s.text) for s in syls]
    target = [None] * len(slots)

    placed = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            a=a, b=b, autojunk=False).get_opcodes():
        if tag in ("equal", "replace"):
            for k in range(min(i2 - i1, j2 - j1)):
                target[i1 + k] = syls[j1 + k]
                placed.append(i1 + k)
    if not placed:
        return target, 0, 0
    return target, placed[0], placed[-1] + 1


@dataclass
class Match:
    """Yhden äänen kohdistuksen tulos."""

    target: list    # tavoitetila per paikka, pituus = paikkojen määrä
    handled: list   # tuliko paikka kohdistetuksi; vain näihin kirjoitetaan
    reached: int    # kuinka pitkälle kursori ehti
    used: list      # rivit jotka tunnistettiin tämän äänen riveiksi
    skipped: list   # rivit jotka ohitettiin toisen äänen riveinä


# Ikkuna otetaan tavumäärää pidempänä, jotta rivin tavujen väliin luetut
# roskasanat mahtuvat mukaan. Ikkunan lopun ylimääräisiä paikkoja ei
# poisteta, joten pituus ei ole vaarallinen — vain hyödyllinen.
SLACK = 3

# Kuinka monta parasta kohtaa riviä kohti otetaan valintaan mukaan.
TOP = 4

# Kuinka suuri osa rivin tavuista saa jäädä osumatta. Oikein kohdistuva rivi
# osuu lähes täysin, koska konelukeminen on enimmäkseen oikein; löysempi
# raja päästää läpi väärään toistoon liukuneen rivin.
TOLERANCE = 0.35

# Osuman on alettava ikkunan alusta. Pari paikkaa liukumaa sallitaan, koska
# konelukeminen on voinut rikkoa juuri rivin ensimmäisen tavun.
HEAD = 2


def _matched(syls, slots):
    """Montako rivin tavua osuu paikkoihin ikkunan alusta alkaen.

    Ankkurointi on olennainen: ilman sitä pitkä rivi voi saada korkean
    arvon osumalla ikkunan loppupäähän, ja tulla valituksi kohtaan jonne
    se ei kuulu.
    """
    a = [_norm(s.text) for s in slots]
    b = [_norm(s.text) for s in syls]
    blocks = [bl for bl in difflib.SequenceMatcher(
        a=a, b=b, autojunk=False).get_matching_blocks() if bl.size]
    if not blocks or blocks[0].a > HEAD or blocks[0].b > HEAD:
        return 0
    return sum(bl.size for bl in blocks)


def _accepts(matched, n, tolerance):
    """Riittääkö osuma rivin sijoittamiseen.

    Kiinteä osuusraja hylkäisi lyhyet rivit: viiden tavun rivissä yksikin
    kirjainvirhe pudottaa osuuden 80 prosenttiin. Siksi yksi virhe
    sallitaan aina ja pitkässä rivissä sallittu määrä kasvaa pituuden
    mukana. Kahta osumaa vähemmällä riviä ei sijoiteta lainkaan — yksi
    tavu osuisi mihin tahansa toistoon.
    """
    return matched >= 2 and n - matched <= max(1, round(tolerance * n))


def _exact(syls, slots):
    """Sama vertailu välimerkit mukaan lukien.

    Ratkaisee tasapelin. Samassa systeemissä äänet laulavat usein samat
    sanat mutta eri välimerkeillä, eivätkä PDF:n rivit kerro kummalle
    välimerkki kuuluu. Silloin lähimmäksi konelukemisen omaa tekstiä
    osuva rivi on tämän äänen rivi.
    """
    return difflib.SequenceMatcher(
        a=[s.text for s in slots], b=[s.text for s in syls],
        autojunk=False).ratio()


def _index(syllables):
    """Vertailumuoto -> ne paikat joissa se esiintyy."""
    index = {}
    for i, s in enumerate(syllables):
        index.setdefault(_norm(s.text), []).append(i)
    return index


def _candidate_starts(syls, index):
    """Ne aloituskohdat joissa rivi voi ankkuroitua.

    Osuman on alettava ikkunan alusta HEADin sisällä, joten jos rivin
    tavu k osuu paikkaan p, ikkunan alku on välillä p-HEAD..p. Muut
    kohdat eivät voi kelvata, joten niitä ei kannata pisteyttää.
    """
    starts = set()
    for k, syl in enumerate(syls[:HEAD + 1]):
        for p in index.get(_norm(syl.text), ()):
            for d in range(HEAD + 1):
                if p - d >= 0:
                    starts.add(p - d)
    return sorted(starts)


@dataclass(frozen=True)
class Placement:
    """Yksi mahdollinen kohta yhdelle riville."""

    row: int       # rivin järjestysnumero
    start: int     # ensimmäinen paikka jonka rivi kattaa
    end: int       # viimeisen kattamansa jälkeen
    weight: float  # osuneiden tavujen määrä, tasapeli tarkkuudella
    target: tuple  # tavoitetilat välille start..end


def _placements(rows, syllables, tolerance, top):
    """Parhaat mahdolliset kohdat jokaiselle riville."""
    index = _index(syllables)
    out = []
    for i, row in enumerate(rows):
        syls = tokenise(row.text)
        if not syls:
            continue
        found = []
        for start in _candidate_starts(syls, index):
            window = syllables[start:start + len(syls) + SLACK]
            matched = _matched(syls, window)
            if _accepts(matched, len(syls), tolerance):
                found.append((matched, start, window))
        found.sort(key=lambda f: -f[0])
        for matched, start, window in found[:top]:
            target, lo, hi = align(syls, window)
            if hi > lo:
                out.append(Placement(i, start + lo, start + hi,
                                     matched + _exact(syls, window),
                                     tuple(target[lo:hi])))
    return out


def _choose(placements):
    """Suurin yhteensopiva joukko kohtia.

    Rivien on oltava järjestyksessä ja kohtien menemättä päällekkäin.
    Ahne kursori valitsisi tässä peruuttamattomasti ja liukuisi väärään
    toistoon; nyt väärä kohta häviää oikealle, koska oikeat kohdat
    tukevat toisiaan ja väärä on niiden kanssa ristiriidassa.
    """
    if not placements:
        return []
    ps = sorted(placements, key=lambda p: (p.start, p.row))
    best = [p.weight for p in ps]
    prev = [-1] * len(ps)
    for j, pj in enumerate(ps):
        for i in range(j):
            if ps[i].end <= pj.start and ps[i].row < pj.row:
                if best[i] + pj.weight > best[j]:
                    best[j] = best[i] + pj.weight
                    prev[j] = i
    k = max(range(len(ps)), key=lambda j: best[j])
    chosen = []
    while k != -1:
        chosen.append(ps[k])
        k = prev[k]
    return chosen[::-1]


def match_part(rows, syllables, tolerance=TOLERANCE, top=TOP):
    """Kohdistaa yhden äänen tavupaikat PDF:n riveihin.

    PDF:n rivit ovat kaikkien äänten rivejä sekaisin, järjestyksessä
    ylhäältä alas. Rivi joka ei osu mihinkään on toisen äänen rivi.

    Palauttaa Matchin. Sen handled kertoo mitkä paikat tulivat
    kohdistetuiksi: muualla tyhjä tavoitetila ei tarkoita poistoa vaan
    sitä, ettei yksikään rivi ulottunut siihen.
    """
    known = vocabulary(rows)
    chosen = _choose(_placements(rows, syllables, tolerance, top))

    target = [None] * len(syllables)
    handled = [False] * len(syllables)
    for p in chosen:
        for k, want in enumerate(p.target):
            i = p.start + k
            # Poisto on oikea vain roskalle. Jos PDF tuntee tavun,
            # kohdistus on liukunut eikä paikkaa saa tyhjentää.
            if want is None and _norm(syllables[i].text) in known:
                continue
            target[i] = want
            handled[i] = True

    taken = {p.row for p in chosen}
    return Match(target, handled,
                 max((p.end for p in chosen), default=0),
                 [rows[p.row] for p in chosen],
                 [r for i, r in enumerate(rows) if i not in taken])


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


def _verse(lyric):
    try:
        return int(lyric.get("number") or 1)
    except ValueError:
        return 1


def _lyrics_by_verse(part):
    """Tuottaa (tahti, nuotti, sanarivit) jokaiselle sanoja kantavalle
    nuotille, sanarivit säkeistönumeron mukaan järjestettynä."""
    for measure in part.iter("measure"):
        number = int(measure.get("number"))
        for note in measure.iter("note"):
            lyrics = sorted(note.iter("lyric"), key=_verse)
            if lyrics:
                yield number, note, lyrics


def read_slots(part):
    """Osaston sanarivin tavupaikat järjestyksessä, yksi per nuotti.

    Sanarivi luetaan säkeistö kerrallaan eikä nuotti kerrallaan, joten
    pääjonoon kuuluu vain kunkin nuotin ensimmäinen sanarivi. Ylimääräiset
    säkeistöt saa read_extras.
    """
    return [Slot(number, note, lyrics[0])
            for number, note, lyrics in _lyrics_by_verse(part)]


def read_extras(part):
    """Nuottien ylimääräiset sanarivit järjestyksessä.

    Konelukeminen on pannut näille esitysmerkintöjä ("sotto voce")
    ja kahtia menneiden tavujen puolikkaita. Kuoro laulaa osissa 01 ja 14
    yhtä tekstiä, joten toista sanariviä ei niissä ole.
    """
    return [Slot(number, note, lyric)
            for number, note, lyrics in _lyrics_by_verse(part)
            for lyric in lyrics[1:]]


@dataclass(frozen=True)
class Change:
    """Yksi muutos raporttiin. after on None kun sana poistettiin."""

    measure: int
    before: str
    after: str


def apply_targets(slots, target, handled):
    """Kirjoittaa tavoitetilat XML:ään ja palauttaa tehdyt muutokset.

    Vain kohdistetut paikat käsitellään. Muualla tyhjä tavoitetila ei ole
    poisto vaan kohdistamaton paikka, ja se jätetään koskematta.
    """
    changes, touched = [], []
    for i, ok in enumerate(handled):
        if not ok:
            continue
        slot, want = slots[i], target[i]
        have = slot.syllable
        if want is None:
            slot.note.remove(slot.element)
            touched.append(slot.note)
            changes.append(Change(slot.measure, have.text, None))
        elif want != have:
            _set_lyric(slot.element, want)
            changes.append(Change(slot.measure, have.text, want.text))
    for note in touched:
        _renumber_verses(note)
    return changes


def vocabulary(rows):
    """Kaikki tavut jotka PDF:ssä esiintyvät, vertailumuodossa.

    Poisto on oikea vain roskalle. Jos tavu esiintyy PDF:ssä jossain, se on
    oikea tavu, ja sen poistaminen tarkoittaisi että kohdistus on liukunut.
    """
    return {_norm(s.text) for row in rows for s in tokenise(row.text)}


def remove_extras(extras, handled_notes):
    """Poistaa ylimääräiset sanarivit niiltä nuoteilta joiden pääsanarivi
    tuli kohdistetuksi.

    Ehto on olennainen: kohdistamattoman nuotin ylimääräinen sanarivi voi
    olla mitä tahansa, eikä sitä ole mitään perustetta poistaa.
    """
    changes, touched = [], []
    for slot in extras:
        if id(slot.note) in handled_notes:
            slot.note.remove(slot.element)
            touched.append(slot.note)
            changes.append(Change(slot.measure, slot.syllable.text, None))
    for note in touched:
        _renumber_verses(note)
    return changes


def _set_lyric(lyric, syllable):
    text = lyric.find("text")
    if text is None:
        text = ET.SubElement(lyric, "text")
    text.text = syllable.text

    syl = lyric.find("syllabic")
    if syl is None:
        # MusicXML vaatii <syllabic> ennen <text>.
        syl = ET.Element("syllabic")
        lyric.insert(list(lyric).index(text), syl)
    syl.text = syllable.syllabic


def _renumber_verses(note):
    """Numeroi nuotin jäljelle jääneet sanarivit ykkösestä alkaen.

    Ilman tätä poisto voi jättää nuotille pelkän säkeistön 2, ja yksikin
    korkea säkeistönumero saa MuseScoren varaamaan tilan kaikille sitä
    edeltäville sanariveille koko osan mitalta.
    """
    for n, lyric in enumerate(note.iter("lyric"), start=1):
        lyric.set("number", str(n))


@dataclass(frozen=True)
class Source:
    """Konelukemisella tuotettu osa ja se PDF josta se luettiin."""

    mxl: str
    pdf: str
    font: str          # PDF:n tekstifontti; sanat ovat sen yleisintä kokoa
    parts: tuple       # (osaston tunnus, nimi raporttiin)
    out: str


SOURCES = [
    Source(
        mxl="01-Verdi_Requiem-OMR.mxl",
        pdf="01-Verdi_Requiem.pdf",
        font="Times-Roman",
        parts=(("P13", "Kuoro S"), ("P14", "Kuoro A"),
               ("P15", "Kuoro T"), ("P16", "Kuoro B")),
        out="01-Verdi_Requiem-OMR-korjattu.mxl",
    ),
    Source(
        mxl="14-Verdi_requiem_agnus-dei-OMR.mxl",
        pdf="14-Verdi_requiem_agnus-dei.pdf",
        font="Garamond",
        parts=(("P1", "Kuoro S"), ("P2", "Kuoro A"),
               ("P3", "Kuoro T"), ("P4", "Kuoro B")),
        out="14-Verdi_requiem_agnus-dei-OMR-korjattu.mxl",
    ),
]


@dataclass
class PartReport:
    """Yhden osaston korjauksen tulos raporttia varten."""

    part: str
    name: str
    slots: int
    handled: int
    changes: list
    runs: list     # kohdistamattomat jaksot, kukin lista paikkoja
    used: list     # rivit jotka tunnistettiin tämän äänen riveiksi
    skipped: list  # rivit joille ei löytynyt paikkaa tästä äänestä


def _runs(slots, handled):
    """Kohdistamattomat paikat yhtenäisiksi jaksoiksi.

    Jakso kertoo yhden kohdan jota PDF:n rivit eivät kattaneet. Näitä
    syntyy siellä missä konelukeminen on pudottanut tavun kokonaan: silloin
    paikkoja on tavuja vähemmän eikä kohdistus voi olla yksi yhteen.
    """
    runs, run = [], []
    for slot, ok in zip(slots, handled):
        if ok:
            if run:
                runs.append(run)
                run = []
        else:
            run.append(slot)
    if run:
        runs.append(run)
    return runs


def correct(source, pages=None):
    """Korjaa yhden osan kuorosanat ja palauttaa (puu, raportti)."""
    root = load(source.mxl)
    rows = extract_rows(source.pdf, source.font, pages)

    report = []
    for part_id, name in source.parts:
        part = find_part(root, part_id)
        slots, extras = read_slots(part), read_extras(part)
        got = match_part(rows, [s.syllable for s in slots])
        changes = apply_targets(slots, got.target, got.handled)
        done = {id(s.note) for s, ok in zip(slots, got.handled) if ok}
        changes += remove_extras(extras, done)
        report.append(PartReport(part_id, name, len(slots),
                                 sum(got.handled), changes,
                                 _runs(slots, got.handled),
                                 got.used, got.skipped))
    return root, report
