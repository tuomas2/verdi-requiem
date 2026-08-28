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


def _split(text):
    """Pilkkoo siivotun sanarivin tavuiksi indekseineen.

    Sanaraja on välilyönti ja tavuraja viiva, ja viivan asema kertoo
    tavun aseman sanassa. Indeksi on tavun ensimmäisen merkin paikka
    tekstissä; sen kautta tavu löytää x-sijaintinsa.
    """
    out = []
    i = 0
    while i < len(text):
        if text[i] == " ":
            i += 1
            continue
        j = text.index(" ", i) if " " in text[i:] else len(text)

        parts, at = [], i
        for piece in text[i:j].split("-"):
            parts.append((piece, at))
            at += len(piece) + 1
        jatkaa_alussa = parts[0][0] == ""
        jatkuu_lopussa = parts[-1][0] == ""
        core = [(p, k) for p, k in parts if p]

        for n, (p, k) in enumerate(core):
            viiva_ennen = jatkaa_alussa if n == 0 else True
            viiva_jalkeen = jatkuu_lopussa if n == len(core) - 1 else True
            if viiva_ennen and viiva_jalkeen:
                syllabic = "middle"
            elif viiva_jalkeen:
                syllabic = "begin"
            elif viiva_ennen:
                syllabic = "end"
            else:
                syllabic = "single"
            out.append((Syllable(p, syllabic), k))
        i = j
    return out


def tokenise(row):
    """Pilkkoo PDF:stä poimitun sanarivin tavuiksi.

    PDF:n välistys on epätasaista — tavuviivan ympärillä on välilyönti
    milloin sattuu — joten välit siivotaan ensin pois viivan ja välimerkin
    ympäriltä.
    """
    return [s for s, _ in _split(_clean(row))]


def syllables_with_x(row):
    """Rivin tavut ja kunkin x-sijainti PDF:n koordinaatistossa."""
    return [(s, row.xs[k]) for s, k in _split(row.text)]


@dataclass(frozen=True)
class Row:
    """Yhden äänen sanat yhdessä systeemissä."""

    page: int
    y: float
    text: str
    xs: tuple = ()   # x-sijainti per tekstin merkki


def _clean_chars(pairs):
    """Siivoaa välit tavuviivan ja välimerkin ympäriltä, sijainnit mukana.

    Palauttaa (teksti, x per merkki). Sijainnit kulkevat mukana, koska
    tavun x-sijainti ratkaisee sen nuotin johon tavu kuuluu.
    """
    tight = []
    for c, x in pairs:
        if c.isspace():
            if tight and not tight[-1][0].isspace():
                tight.append((" ", x))
        else:
            tight.append((c, x))

    out = []
    for i, (c, x) in enumerate(tight):
        if c == " ":
            after = tight[i + 1][0] if i + 1 < len(tight) else ""
            before = out[-1][0] if out else ""
            if after == "-" or before == "-" or after in VALIMERKIT:
                continue
        out.append((c, x))

    while out and out[0][0] == " ":
        out.pop(0)
    while out and out[-1][0] == " ":
        out.pop()
    return "".join(c for c, _ in out), [x for _, x in out]


def _clean(s):
    return _clean_chars([(c, 0.0) for c in s])[0]


def _pattern(word):
    """Sanan tavutus: ne kirjainindeksit joiden jälkeen on viiva.

    Toistuva viiva samassa kohdassa on kaivertajan jatkoviiva eikä toinen
    tavuraja — "Chri--ste" tavuttuu kuten "Chri-ste" — joten toistot
    jätetään huomiotta. Muuten jatkoviiva näyttäisi eri tavutukselta ja
    voisi voittaa äänestyksen.
    """
    cuts, letters = set(), 0
    for c in word:
        if c == "-":
            cuts.add(letters)
        else:
            letters += 1
    return tuple(sorted(cuts))


def _key(word):
    """Sanan kirjaimet ilman viivoja ja välimerkkejä, pienellä."""
    return word.replace("-", "").strip(VALIMERKIT).lower()


def hyphenations(rows):
    """Yleisin tavutus kullekin kokonaiselle sanalle.

    Osan 14 MusiXTeX asemoi joka kirjaimen erikseen, ja tavuviivan x osuu
    paikoin väärän kirjaimen jälkeen: sana "peccata" poimitaan neljällä
    rivillä kymmenestä muodossa "pecc-a-ta". Sama sana on kuitenkin
    oikein kuudella rivillä, joten enemmistö kertoo oikean tavutuksen.

    Vain kokonaiset sanat äänestävät. Systeemin alussa tai lopussa oleva
    katkelma on osa sanaa eikä kerro koko sanan tavutusta.
    """
    seen = {}
    for row in rows:
        for word in row.text.split():
            if word.startswith("-") or word.endswith("-"):
                continue
            key = _key(word)
            if len(key) > 1:
                seen.setdefault(key, Counter())[_pattern(word)] += 1
    return {key: counts.most_common(1)[0][0] for key, counts in seen.items()}


def _rehyphenate(chars, pattern):
    """Kirjoittaa sanan uudelleen annetulla tavutuksella.

    Kirjaimet pitävät oman x-sijaintinsa; vain viivat siirtyvät, eikä
    niiden sijainnilla ole merkitystä — tavun x tulee sen ensimmäisestä
    kirjaimesta.
    """
    letters = [(c, x) for c, x in chars if c != "-"]
    out, cuts = [], set(pattern)
    for k, (c, x) in enumerate(letters):
        out.append((c, x))
        if k + 1 in cuts and c not in VALIMERKIT:
            out.append(("-", x))
    return out


def _consistent(rows):
    """Yhtenäistää tavutuksen: sama sana tavutetaan kaikkialla samoin."""
    patterns = hyphenations(rows)
    fixed = []
    for row in rows:
        chars, word, out = list(zip(row.text, row.xs)), [], []
        for pair in chars + [(" ", 0.0)]:
            if pair[0] != " ":
                word.append(pair)
                continue
            text = "".join(c for c, _ in word)
            want = patterns.get(_key(text))
            if (word and not text.startswith("-") and not text.endswith("-")
                    and want is not None and want != _pattern(text)):
                word = _rehyphenate(word, want)
            out.extend(word)
            out.append(pair)
            word = []
        out.pop()
        fixed.append(Row(row.page, row.y, "".join(c for c, _ in out),
                         tuple(x for _, x in out)))
    return fixed


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
                    out.append((" ", left))
                out.append((c, left))
                edge = right
            text, xs = _clean_chars(out)
            if text:
                rows.append(Row(number, y, text, tuple(xs)))
    return _consistent(rows)


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

# Puuttuvien sanojen lisäys. Mittakaava PDF:n ja MusicXML:n välillä on
# ~0,3; näiden ulkopuolinen sovitus tarkoittaa että parit ovat vääriä.
MIN_SCALE = 0.2
MAX_SCALE = 0.5

# Kuinka suuren osan rivin tavuista on osuttava systeemin nuoteille, jotta
# rivi kelpaa sen systeemin riviksi.
MIN_HITS = 0.85

# Montako jo osuvaa sanaa systeemissä tarvitaan, jotta sen kulmakerroin
# otetaan mukaan mittakaavan mediaaniin.
MIN_ANCHORS = 6

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


def save(root, template, path):
    """Kirjoittaa puun .mxl-tiedostoksi templaten muita jäseniä myöten.

    .mxl on zip, jossa META-INF/container.xml osoittaa varsinaiseen
    XML-tiedostoon. Ilman containeria MuseScore ei tunnista tiedostoa,
    joten muut jäsenet kopioidaan sellaisenaan.
    """
    with zipfile.ZipFile(template) as z:
        score = next(n for n in z.namelist()
                     if not n.startswith("META-INF") and n.lower().endswith(".xml"))
        members = [(n, z.read(n)) for n in z.namelist()]

    body = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in members:
            z.writestr(name, body if name == score else data)


def find_part(root, part_id):
    return next(p for p in root.iter("part") if p.get("id") == part_id)


@dataclass
class NoteAt:
    """Yksi soiva nuotti sijainteineen."""

    measure: int
    system: int
    x: float
    note: ET.Element

    @property
    def lyrics(self):
        return list(self.note.iter("lyric"))


def read_notes(part):
    """Osaston soivat nuotit systeemeittäin ja x-sijainteineen.

    Audiveris säilytti nuottien default-x:n, tahtien leveydet ja
    <print>-elementeissä systeemien vasemmat marginaalit, joten nuotin
    paikka rivillä on laskettavissa. Laskenta alkaa alusta joka
    systeemissä, joten x on vertailukelpoinen vain systeemin sisällä.

    Soinnun lisäsävelet jätetään pois: ne ovat samalla x:llä kuin
    soinnun ensimmäinen nuotti eivätkä kanna omaa tavua.
    """
    notes = []
    system, left = -1, 0.0
    for measure in part.iter("measure"):
        number = int(measure.get("number"))
        printing = measure.find("print")
        if printing is not None and (printing.get("new-page") == "yes"
                                     or printing.find("system-layout") is not None):
            system += 1
            margin = printing.find("system-layout/system-margins/left-margin")
            left = float(margin.text) if margin is not None else 0.0
        for note in measure.iter("note"):
            if note.find("rest") is not None or note.find("chord") is not None:
                continue
            x = note.get("default-x")
            if x is not None:
                notes.append(NoteAt(number, max(system, 0), left + float(x), note))
        left += float(measure.get("width") or 0)
    return notes


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
    """Yksi muutos raporttiin. after on None kun sana poistettiin.

    hyphen on (ennen, jälkeen) niissä muutoksissa joissa tavutus muuttui.
    Ilman sitä raportti näyttäisi rivejä muotoa 'ae' -> 'ae', joissa mikään
    ei silminnähden muutu.
    """

    measure: int
    before: str
    after: str
    hyphen: tuple = ()


def apply_targets(slots, target, handled, spelled=frozenset()):
    """Kirjoittaa tavoitetilat XML:ään.

    Palauttaa (muutokset, ehdotukset). Ehdotuksia ei kirjoiteta: ne ovat
    muutoksia joissa vanhakin teksti on PDF:n tuntema sana, ja sellainen
    voi olla kohdistuksen liukumista. Käsin tarkistettuna kolme viidestä
    oli väärin, joten niitä ei sovelleta.

    Vain kohdistetut paikat käsitellään. Muualla tyhjä tavoitetila ei ole
    poisto vaan kohdistamaton paikka, ja se jätetään koskematta.
    """
    changes, proposals, touched = [], [], []
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
            hyphen = ((have.syllabic, want.syllabic)
                      if have.syllabic != want.syllabic else ())
            change = Change(slot.measure, have.text, want.text, hyphen)
            if _uncertain(change, spelled):
                proposals.append(change)
                continue
            _set_lyric(slot.element, want)
            changes.append(change)
    for note in touched:
        _renumber_verses(note)
    return changes, proposals


def vocabulary(rows):
    """Kaikki tavut jotka PDF:ssä esiintyvät, vertailumuodossa.

    Poisto on oikea vain roskalle. Jos tavu esiintyy PDF:ssä jossain, se on
    oikea tavu, ja sen poistaminen tarkoittaisi että kohdistus on liukunut.
    Tämä on kirjainkoosta riippumaton, koska poistossa kannattaa olla
    varovainen.
    """
    return {_norm(s.text) for row in rows for s in tokenise(row.text)}


def spellings(rows):
    """Kaikki tavut PDF:ssä sellaisina kuin ne on kirjoitettu.

    Tarkistettavaksi merkitseminen katsoo kirjainkokoa, koska iso
    alkukirjain kertoo sanan alusta. "is" esiintyy joka toisessa tahdissa
    sanassa "e-is", mutta "Is" ei kertaakaan — joten "Is" -> "Je" on selvä
    korjaus eikä epävarma.
    """
    return {s.text.strip(VALIMERKIT) for row in rows
            for s in tokenise(row.text)}


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
    Source(
        mxl="10b-Verdi_Dies_irae_paluu-OMR.mxl",
        pdf="Verdi_10bDies_irae.pdf",
        font="F3",
        parts=(("P1", "Kuoro S"), ("P2", "Kuoro A"),
               ("P3", "Kuoro T"), ("P4", "Kuoro B")),
        out="10b-Verdi_Dies_irae_paluu-OMR-korjattu.mxl",
    ),
]


@dataclass
class PartReport:
    """Yhden osaston korjauksen tulos raporttia varten."""

    part: str
    name: str
    slots: int
    handled: int
    changes: list    # sovelletut muutokset
    proposals: list  # muutokset joita ei sovellettu, tarkistettavaksi
    runs: list     # kohdistamattomat jaksot, kukin lista paikkoja
    used: list     # rivit jotka tunnistettiin tämän äänen riveiksi
    skipped: list  # rivit joille ei löytynyt paikkaa tästä äänestä


def _slope(pairs):
    """Pienimmän neliösumman kulmakerroin nuotin x:stä tavun x:ään."""
    n = len(pairs)
    if n < 2:
        return None
    sx = sum(a for a, _ in pairs)
    sy = sum(b for _, b in pairs)
    sxx = sum(a * a for a, _ in pairs)
    sxy = sum(a * b for a, b in pairs)
    div = n * sxx - sx * sx
    if abs(div) < 1e-6:
        return None
    return (n * sxy - sx * sy) / div


def _median(values):
    values = sorted(values)
    return values[len(values) // 2] if values else None


def _anchors(notes, syls):
    """Parit (nuotin x, tavun x) niistä sanoista jotka jo osuvat."""
    have = [(n, (n.lyrics[0].findtext("text") or "")) for n in notes
            if n.lyrics]
    if not have:
        return []
    matcher = difflib.SequenceMatcher(a=[_norm(t) for _, t in have],
                                      b=[_norm(s.text) for s, _ in syls],
                                      autojunk=False)
    return [(have[block.a + k][0].x, syls[block.b + k][1])
            for block in matcher.get_matching_blocks()
            for k in range(block.size)]


def scale_of(rows, systems):
    """Mittakaava PDF:n ja MusicXML:n koordinaatistojen välillä.

    Yhden systeemin muutamasta ankkurista sovitettu kulmakerroin heittää
    sen verran, että ekstrapolointi systeemin toiseen päähän menee tavun
    verran ohi. Mittakaava on kuitenkin sivuasettelun ominaisuus eikä
    systeemikohtainen, joten se otetaan mediaanina kaikista systeemeistä
    joissa on tarpeeksi ankkureita.
    """
    slopes = []
    for notes in systems:
        best = None
        for row in rows:
            syls = syllables_with_x(row)
            pairs = _anchors(notes, syls)
            if len(pairs) < MIN_ANCHORS:
                continue
            slope = _slope(pairs)
            if slope and MIN_SCALE <= slope <= MAX_SCALE:
                if best is None or len(pairs) > best[0]:
                    best = (len(pairs), slope)
        if best:
            slopes.append(best[1])
    return _median(slopes)


def _beside(notes, index, syllable):
    """Onko sama tavu jo naapurinuotilla.

    Ennustettu nuotti voi olla tyhjä vaikka tavu on jo paikallaan yhtä
    nuottia sivussa. Ilman tätä syntyi "qui tol-tol-lis": tavu lisättiin
    tyhjälle nuotille jo olevan viereen.

    Naapuria katsotaan yli systeemirajan, koska rivi voi alkaa edellisen
    systeemin viimeisellä tavulla.
    """
    for k in (index - 1, index + 1):
        if 0 <= k < len(notes) and notes[k].lyrics:
            text = notes[k].lyrics[0].findtext("text") or ""
            if _norm(text) == _norm(syllable.text):
                return True
    return False


def _spacing(notes):
    """Nuottien tyypillinen väli systeemissä."""
    gaps = sorted(b.x - a.x for a, b in zip(notes, notes[1:]) if b.x > a.x)
    return gaps[len(gaps) // 2] if gaps else 0.0


def _row_for_system(rows, notes, spacing, scale):
    """Etsii sen PDF-rivin joka selittää systeemin nuotit parhaiten.

    Mittakaava on tiedossa, joten systeemissä jo olevat sanat riittävät
    ratkaisemaan siirtymän. Oikea rivi tunnistuu siitä, että sen
    *kaikki* tavut osuvat systeemin nuoteille: väärän systeemin rivi
    sovittuu samoihin ankkureihin mutta sen loput tavut osuvat tyhjään.
    """
    best = None
    for row in rows:
        syls = syllables_with_x(row)
        if not syls:
            continue
        pairs = _anchors(notes, syls)
        if not pairs:
            continue
        offset = _median([x - scale * nx for nx, x in pairs])
        hits = sum(1 for _, x in syls
                   if min(abs(scale * n.x + offset - x) for n in notes)
                   <= spacing * scale / 2)
        if hits < len(syls) * MIN_HITS:
            continue
        if best is None or (hits, len(pairs)) > (best[0], best[1]):
            best = (hits, len(pairs), row, syls, offset)
    return best[2:] if best else None


def fill_missing(part, rows, known=frozenset()):
    """Lisää PDF:n tavut nuoteille joilla ei ole sanaa lainkaan.

    Konelukeminen jätti paikoin kokonaisia jaksoja lukematta. Teksti on
    PDF:ssä, ja x-sijainti kertoo kummankin puolen: tavu menee sille
    nuotille jonka yllä se on. Melisma ei häiritse, koska nuotti jonka
    yllä ei ole tavua jää ilman.

    Tavua ei siirretä: se menee sille nuotille joka on sitä lähinnä, tai
    ei mihinkään. Jos se nuotti kantaa jo sanaa jonka PDF tuntee, sana on
    oikea ja tavu jätetään. Jos se kantaa roskaa, roska korvataan.
    Siirtäminen viereiselle vapaalle nuotille tuottaisi kaksoiskappaleita
    kuten "ti-bi bi red-de-tur".
    """
    every = read_notes(part)
    place = {id(n.note): i for i, n in enumerate(every)}
    grouped = {}
    for note in every:
        grouped.setdefault(note.system, []).append(note)
    systems = [notes for _, notes in sorted(grouped.items())]

    scale = scale_of(rows, systems)
    if scale is None:
        return [], []

    added, skipped = [], []
    for notes in systems:
        if not any(not n.lyrics for n in notes):
            continue
        spacing = _spacing(notes)
        if spacing <= 0:
            continue
        found = _row_for_system(rows, notes, spacing, scale)
        if found is None:
            continue
        _, syls, offset = found

        plan = []
        for syllable, x in syls:
            want = (x - offset) / scale
            near = min(notes, key=lambda n: abs(n.x - want))
            if abs(near.x - want) > spacing / 2 or _beside(every, place[id(near.note)],
                                                           syllable):
                plan.append((syllable, None))
            else:
                plan.append((syllable, near))

        # Sijoitusten on oltava järjestyksessä eikä sama nuotti saa saada
        # kahta tavua. Muuten sovitus ei ole yksikäsitteinen — niin käy
        # kun rivillä on enemmän tavuja kuin systeemissä nuotteja — ja
        # täyttäminen tuottaisi kaksoiskappaleita kuten "e-le-le-son".
        landed = [n for _, n in plan if n is not None]
        if (len(landed) != len({id(n.note) for n in landed})
                or any(a.x >= b.x for a, b in zip(landed, landed[1:]))):
            skipped.append(notes)
            continue

        for syllable, near in plan:
            if near is None:
                continue
            if near.lyrics:
                have = near.lyrics[0].findtext("text") or ""
                if _norm(have) in known or _norm(have) == _norm(syllable.text):
                    continue
                _set_lyric(near.lyrics[0], syllable)
                added.append(Change(near.measure, have, syllable.text))
            else:
                lyric = ET.SubElement(near.note, "lyric")
                lyric.set("number", "1")
                _set_lyric(lyric, syllable)
                added.append(Change(near.measure, "", syllable.text))
    return added, skipped


def _uncertain(change, spelled):
    """Onko muutos sellainen joka kannattaa tarkistaa käsin.

    Aito korjaus vaihtaa roskan sanaksi. Jos vanhakin teksti on sana jonka
    PDF tuntee, muutos voi olla kohdistuksen liukumista — tai aito korjaus
    kuten "at" -> "et", koska "at" esiintyy sanassa "lu-ce-at". Kumpi,
    sitä ei ratkaista koneella; se merkitään katsottavaksi.

    Pelkkä välimerkkiero ei ole tällainen: "nam ," -> "nam," on siivousta,
    ja sellaiset hukuttaisivat listaan ne muutokset jotka on syytä katsoa.
    """
    return (change.after is not None
            and _norm(change.before) != _norm(change.after)
            and change.before.strip(VALIMERKIT) in spelled)


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
    known, spelled = vocabulary(rows), spellings(rows)

    report = []
    for part_id, name in source.parts:
        part = find_part(root, part_id)
        slots, extras = read_slots(part), read_extras(part)
        got = match_part(rows, [s.syllable for s in slots])
        changes, proposals = apply_targets(slots, got.target, got.handled,
                                           spelled)
        done = {id(s.note) for s, ok in zip(slots, got.handled) if ok}
        changes += remove_extras(extras, done)
        filled, ambiguous = fill_missing(part, rows, known)
        changes += filled
        changes.sort(key=lambda c: c.measure)
        proposals.sort(key=lambda c: c.measure)
        report.append(PartReport(part_id, name, len(slots),
                                 sum(got.handled), changes, proposals,
                                 _runs(slots, got.handled),
                                 got.used, got.skipped))
    return root, report


def format_report(source, report):
    """Raportti riveinä. Jokainen muutos näkyy, mikään ei muutu hiljaa."""
    out = ["%s  <-  %s" % (source.mxl, source.pdf)]
    changes = proposals = 0

    for part in report:
        out.append("")
        out.append("  %-9s %-6s %3d tavua, kohdistettu %d (%.0f %%)"
                   % (part.name, part.part, part.slots, part.handled,
                      100.0 * part.handled / max(part.slots, 1)))
        for change in part.changes:
            if change.after is None:
                what = "-> poistettu"
            elif change.before == change.after:
                what = "   tavutus %s -> %s" % change.hyphen
            else:
                what = "-> %r" % change.after
            out.append("    tahti %3d  %-14r %s"
                       % (change.measure, change.before, what))

        if part.proposals:
            out.append("    ei sovellettu, tarkista käsin:")
            for change in part.proposals:
                out.append("      tahti %3d  %-14r -> %r"
                           % (change.measure, change.before, change.after))
        for run in part.runs:
            out.append("    kohdistamatta tahdit %d-%d: %s"
                       % (run[0].measure, run[-1].measure,
                          " ".join(s.syllable.text for s in run)))
        changes += len(part.changes)
        proposals += len(part.proposals)

    out.append("")
    out.append("  %d muutosta kirjoitettu, %d ehdotusta tarkistettavaksi"
               % (changes, proposals))
    return out


def main(argv):
    dry = "--kuiva" in argv
    for source in SOURCES:
        root, report = correct(source)
        print("\n".join(format_report(source, report)))
        if dry:
            print("  (kuiva ajo, mitään ei kirjoitettu)")
        else:
            save(root, source.mxl, source.out)
            print("  kirjoitettu %s" % source.out)
        print()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
