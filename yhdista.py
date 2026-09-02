#!/usr/bin/env python3
"""Yhdistä Verdin Requiemin osat yhdeksi MusicXML-partituuriksi.

Jokainen lähdetiedosto on oma osansa, ja niiden osastot kartoitetaan
yhteiseen viivastojoukkoon niin että sama ääni pysyy koko teoksen ajan
samalla rivillä. Dies iraen (osa II) alaosien tahtinumerointi juoksee
yhtenäisesti läpi koko osan; muualla numerointi alkaa joka osassa
ykkösestä.

Käyttö:  python3 yhdista.py [ulostulo.mxl]
"""

import copy
import sys
import zipfile
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------- kohdeviivastot
# (nimi, lyhenne, viivastoja, oletusavain kun osasto vaikenee koko osan)
TARGETS = [
    ("Solisti S",   "sS",   1, ("G", "2", None)),
    ("Solisti M-S", "sMS",  1, ("G", "2", None)),
    ("Solisti T",   "sT",   1, ("G", "2", "-1")),
    ("Solisti B",   "sB",   1, ("F", "4", None)),
    ("Kuoro S",     "S",    1, ("G", "2", None)),
    ("Kuoro A",     "A",    1, ("G", "2", None)),
    ("Kuoro T",     "T",    1, ("G", "2", "-1")),
    ("Kuoro B",     "B",    1, ("F", "4", None)),
    ("Kuoro S II",  "S II", 1, ("G", "2", None)),
    ("Kuoro A II",  "A II", 1, ("G", "2", None)),
    ("Kuoro T II",  "T II", 1, ("G", "2", "-1")),
    ("Kuoro B II",  "B II", 1, ("F", "4", None)),
    ("D-trumpetti", "D-tpt", 1, ("G", "2", None)),
    ("Trombone",    "Tbn",  1, ("F", "4", None)),
    ("Piano",       "Pno",  2, ("G", "2", None)),
]

# ---------------------------------------------------------------- osat
# (tiedosto, numero partituurissa, nimi)
MOVEMENTS = [
    ("01-Verdi_Requiem-kasin.mxl",                  "I",     "Requiem & Kyrie"),
    ("02-Verdi-Dies_irae.mxl",                      "II·1",  "Dies irae"),
    ("03-Verdi-Tuba_mirum.mxl",                     "II·2",  "Tuba mirum"),
    ("04-Verdi-Mors_stupebit.mxl",                  "II·3",  "Mors stupebit"),
    ("05-Verdi-Liber_scriptus.mxl",                 "II·4",  "Liber scriptus"),
    ("06-Verdi-Quid_sum_miser.mxl",                 "II·5",  "Quid sum miser"),
    ("07-Verdi-Rex.mxl",                            "II·6",  "Rex tremendae"),
    ("08-Verdi_Recordare.mxl",                      "II·7",  "Recordare"),
    ("09-Verdi_Ingemisco.mxl",                      "II·8",  "Ingemisco"),
    ("10-Verdi_Confutatis.mxl",                     "II·9",  "Confutatis"),
    ("10b-Verdi_Dies_irae_paluu-OMR-korjattu.mxl",  "II·9b", "Dies irae (kertaus)"),
    ("11-Verdi_Lacrymosa.mxl",                      "II·10", "Lacrymosa"),
    ("12-Verdi_Offertorio.mxl",                     "III",   "Offertorio"),
    ("13-Verdi-Sanctus.mxl",                        "IV",    "Sanctus"),
    ("14-Verdi_requiem_agnus-dei-OMR-korjattu.mxl", "V",     "Agnus Dei"),
    ("15-Verdi_Lux_aeterna.mxl",                    "VI",    "Lux aeterna"),
    ("16-Libera_Me.mxl",                            "VII",   "Libera me"),
]

# ---------------------------------------------------------------- kartoitus
# Arvo on lista viipaleita. Viipale on joko
#   "P4"                              koko osasto
#   ("P5", 1, 13)                     osasto vain tahdeista 1-13 (None = rajaton)
#   ("P5", 14, None, 1)               kuten yllä, mutta kohdeviivastolle 1
# Useampi viipale samassa listassa yhdistyy samalle riville.
MAPPING = {
    "01-Verdi_Requiem-kasin.mxl": {
        # Audiveris pilkkoi solistiviivastot useaan osastoon; ne yhdistetään.
        "Solisti S": ["P7", "P3", "P1"],
        "Solisti M-S": ["P8", "P4", "P2"],
        "Solisti T": ["P10", "P5", "P12"],
        "Solisti B": ["P11", "P6"],
        "Kuoro S": ["P13"], "Kuoro A": ["P14"],
        "Kuoro T": ["P15"], "Kuoro B": ["P16"],
        # P17 on tämän osan piano, mutta se on jätetty pois. Audiveriksen
        # tuottamassa pianostemmassa on tahteja, joihin MuseScoren moottori
        # kaatuu (Spanner::setTick2, ChordLayout::placeDots), ja soitto
        # pysähtyi tahtiin 81 kesken osaa. Paikkausyritykset rikkoivat
        # tiedoston muualta. Tälle riville tulee nyt taukoja; osassa I ei
        # siis ole pianosäestystä. Palautettavissa siivoamalla
        # 01-Verdi_Requiem.omr Audiveriksen käyttöliittymässä ja lisäämällä
        # tähän "Piano": ["P17"].
        # P9 on kokonaan tyhjä eikä sitä käytetä.
    },
    "02-Verdi-Dies_irae.mxl": {
        "Kuoro S": ["P1"], "Kuoro A": ["P2"], "Kuoro T": ["P3"], "Kuoro B": ["P4"],
        "Piano": ["P5"],
    },
    "03-Verdi-Tuba_mirum.mxl": {
        "Kuoro S": ["P1"], "Kuoro A": ["P2"], "Kuoro T": ["P3"], "Kuoro B": ["P4"],
        # Tässä osassa ei ole pianoa; säestys on kahdella vaskiviivastolla.
        "D-trumpetti": ["P5"], "Trombone": ["P6"],
    },
    "04-Verdi-Mors_stupebit.mxl": {"Solisti B": ["P1"], "Piano": ["P2"]},
    "05-Verdi-Liber_scriptus.mxl": {
        # Tiedostossa "Soprano solo", mutta Liber scriptus on mezzon aaria.
        "Solisti M-S": ["P1"],
        "Kuoro S": ["P2"], "Kuoro A": ["P3"], "Kuoro T": ["P4"], "Kuoro B": ["P5"],
        "Piano": ["P6"],
    },
    "06-Verdi-Quid_sum_miser.mxl": {
        "Solisti S": ["P1"], "Solisti M-S": ["P2"], "Solisti T": ["P3"], "Piano": ["P4"],
    },
    "07-Verdi-Rex.mxl": {
        "Solisti S": ["P1"], "Solisti M-S": ["P2"], "Solisti T": ["P3"], "Solisti B": ["P4"],
        "Kuoro S": ["P5"], "Kuoro A": ["P6"], "Kuoro T": ["P7"], "Kuoro B": ["P8"],
        "Piano": ["P9"],
    },
    "08-Verdi_Recordare.mxl": {
        "Solisti S": ["P1"], "Solisti M-S": ["P2"], "Piano": ["P3"],
    },
    "09-Verdi_Ingemisco.mxl": {"Solisti T": ["P1"], "Piano": ["P2"]},
    "10-Verdi_Confutatis.mxl": {"Solisti B": ["P1"], "Piano": ["P2"]},
    "10b-Verdi_Dies_irae_paluu-OMR-korjattu.mxl": {
        # Confutatiksen ja Lacrymosan välissä puuttunut "Dies irae" -paluu,
        # konelukemisella talteen otettu erillisestä lähde-PDF:stä
        # (Verdi_10bDies_irae.pdf, tahdit 573-623 alkuperäisessä numeroinnissa).
        "Kuoro S": ["P1"], "Kuoro A": ["P2"], "Kuoro T": ["P3"], "Kuoro B": ["P4"],
        "Piano": ["P5"],
    },
    "11-Verdi_Lacrymosa.mxl": {
        "Solisti S": ["P1"], "Solisti M-S": ["P2"], "Solisti T": ["P3"], "Solisti B": ["P4"],
        "Kuoro S": ["P5"], "Kuoro A": ["P6"], "Kuoro T": ["P7"],
        # P9 on kuorobasson divisi tahdeissa 54-56, samalle riville.
        "Kuoro B": ["P8", "P9"],
        "Piano": ["P10"],
    },
    "12-Verdi_Offertorio.mxl": {
        # P2 ja P3 ovat nimeämättömiä; järjestys päätelty partituurin tavasta.
        "Solisti S": ["P1"], "Solisti M-S": ["P2"], "Solisti T": ["P3"], "Solisti B": ["P4"],
        "Piano": ["P5"],
    },
    "13-Verdi-Sanctus.mxl": {
        "Kuoro S": ["P1"], "Kuoro A": ["P2"], "Kuoro T": ["P3"], "Kuoro B": ["P4"],
        "Kuoro S II": ["P5"], "Kuoro A II": ["P6"], "Kuoro T II": ["P7"], "Kuoro B II": ["P8"],
        "Piano": ["P9"],
    },
    "14-Verdi_requiem_agnus-dei-OMR-korjattu.mxl": {
        # P5 ja P6 ovat tahdeissa 1-13 sooloäänet (a cappella -alku) ja
        # tahdista 14 alkaen pianon kaksi viivastoa.
        "Solisti S": [("P5", 1, 13)],
        "Solisti M-S": [("P6", 1, 13)],
        "Kuoro S": ["P1"], "Kuoro A": ["P2"], "Kuoro T": ["P3"], "Kuoro B": ["P4"],
        "Piano": [("P5", 14, None, 1), ("P6", 14, None, 2)],
    },
    "15-Verdi_Lux_aeterna.mxl": {
        # Nimeämättömät osastot; Lux aeterna on mezzon, tenorin ja basson trio.
        "Solisti M-S": ["P1"], "Solisti T": ["P2"], "Solisti B": ["P3"], "Piano": ["P4"],
    },
    "16-Libera_Me.mxl": {
        "Solisti S": ["P1"],
        "Kuoro S": ["P2"], "Kuoro A": ["P3"], "Kuoro T": ["P4"], "Kuoro B": ["P5"],
        "Piano": ["P6"],
    },
}

# Otsikko kiinnitetään näihin riveihin: partituurin ylin rivi ja luettava bassorivi.
# Ilman jälkimmäistä otsikko katoaa kun muut viivastot piilotetaan.
# Yhden stemman tiedostossa otsikko tulee aina sille ainoalle riville.
TITLE_PARTS = ["Solisti S", "Kuoro B"]

# Laulajan stemmat. Kaksoiskuoro esiintyy vain Sanctuksessa, joten kuoro II:n
# laulaja lukee tavallista riviä kaikissa muissa osissa.
# Konelukemisella tuotetut osat: niiden tahtien pituudet normalisoidaan.
# Sanat on korjattu lähde-PDF:ää vasten, ks. korjaa_sanat.py.
OMR_SOURCES = {"01-Verdi_Requiem-kasin.mxl",
               "14-Verdi_requiem_agnus-dei-OMR-korjattu.mxl",
               "10b-Verdi_Dies_irae_paluu-OMR-korjattu.mxl"}

SANCTUS = "13-Verdi-Sanctus.mxl"
SINGER_PARTS = {
    "Sopraano I":     ("Kuoro S", "Kuoro S"),
    "Sopraano II":    ("Kuoro S", "Kuoro S II"),
    "Altto I":        ("Kuoro A", "Kuoro A"),
    "Altto II":       ("Kuoro A", "Kuoro A II"),
    "Tenori I":       ("Kuoro T", "Kuoro T"),
    "Tenori II":      ("Kuoro T", "Kuoro T II"),
    "Basso I":        ("Kuoro B", "Kuoro B"),
    "Basso II":       ("Kuoro B", "Kuoro B II"),
}

# Kunkin Dies iraen alaosan ensimmäisen tahdin numero **kuoron painetussa
# nuottikirjassa**. Nämä eivät ole laskettuja vaan kirjasta luettuja: laulaja
# tarkisti ne harjoituksissa 2026-09-02, ja niiden mukaan numerointi täsmää
# kirjan kanssa alaosan sisällä alusta loppuun.
#
# Aiemmin nämä laskettiin lähdetiedostojen omista tahtimääristä (alut 1, 92,
# 141, 163, 271, 324, 386, 450, 507, 578, 629), mikä oli kuudessa kohdassa
# väärin ja Lacrymosassa jo kahdeksan tahtia pielessä. CPDL:n osakohtaiset
# tiedostot eivät katkea samoista kohdista kuin kirja: viidessä saumassa
# meillä on tahteja, joita kirja laskee jo seuraavaan alaosaan, ja kolmessa
# saumassa kirjassa on tahteja, joita lähteissä ei ole lainkaan (tarkistettu
# vertaamalla saumojen musiikkia — kyse ei ole kahdennuksista). Siksi numerot
# eivät jatku saumojen yli aukottomasti; ks. `saumat()` alempana ja CLAUDE.md
# luku *2026-09-02 (later): the book's own bar numbers for Dies irae*.
NUMEROINTI_ALKAA_JOKA_OSASSA_YKKOSESTA = False
DIES_IRAE_ALUT = {
    "02-Verdi-Dies_irae.mxl": 1, "03-Verdi-Tuba_mirum.mxl": 91,
    "04-Verdi-Mors_stupebit.mxl": 143, "05-Verdi-Liber_scriptus.mxl": 162,
    "06-Verdi-Quid_sum_miser.mxl": 271, "07-Verdi-Rex.mxl": 322,
    "08-Verdi_Recordare.mxl": 386, "09-Verdi_Ingemisco.mxl": 450,
    "10-Verdi_Confutatis.mxl": 507,
    "10b-Verdi_Dies_irae_paluu-OMR-korjattu.mxl": 573,
    "11-Verdi_Lacrymosa.mxl": 621,
}
DIES_IRAE_SIIRTYMAT = {f: alku - 1 for f, alku in DIES_IRAE_ALUT.items()}

TARGETS_BY_NAME = [(t[0], t) for t in TARGETS]


def load(path):
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist()
                    if not n.startswith("META-INF") and n.lower().endswith(".xml"))
        return ET.fromstring(z.read(name))


def normalise(slices):
    """Muunna kartoituksen viipaleet muotoon (osasto, alku, loppu, viivasto)."""
    out = []
    for s in slices:
        if isinstance(s, str):
            out.append((s, None, None, 1))
        elif len(s) == 3:
            out.append((s[0], s[1], s[2], 1))
        else:
            out.append(s)
    return out


def covers(slice_, number):
    _, lo, hi, _ = slice_
    return (lo is None or number >= lo) and (hi is None or number <= hi)


def measure_meta(part):
    """Tahtinumero -> (divisions, beats, beat-type, sävellaji, aikamuutos, lajimuutos).

    Kaksi viimeistä kertovat, vaihtuuko tahtilaji tai sävellaji juuri tässä
    tahdissa. Vaikenevien viivastojen taukotahdit tarvitsevat tiedon, jotta
    ne julistavat muutoksen omalla rivillään — muuten MuseScore pitää tahtia
    vääränmittaisena eikä tiivistä taukoja.
    """
    meta = {}
    div, beats, btype, fifths = 4, 4, 4, 0
    for m in part.findall("measure"):
        time_changed = key_changed = False
        attrs = m.find("attributes")
        if attrs is not None:
            if attrs.findtext("divisions"):
                div = int(attrs.findtext("divisions"))
            t = attrs.find("time")
            if t is not None and t.findtext("beats"):
                beats = int(t.findtext("beats"))
                btype = int(t.findtext("beat-type"))
                time_changed = True
            k = attrs.find("key")
            if k is not None and k.findtext("fifths") is not None:
                fifths = int(k.findtext("fifths"))
                key_changed = True
        meta[m.get("number")] = (div, beats, btype, fifths, time_changed, key_changed)
    return meta


def rest_measure(number, div, beats, btype, staves):
    """Kokotahdin tauko. Kahdelle viivastolle tehdään tauko molempiin."""
    m = ET.Element("measure", {"number": number})
    dur = str(int(div * beats * 4 / btype))
    for staff in range(1, staves + 1):
        if staff > 1:
            b = ET.SubElement(m, "backup")
            ET.SubElement(b, "duration").text = dur
        note = ET.SubElement(m, "note")
        ET.SubElement(note, "rest").set("measure", "yes")
        ET.SubElement(note, "duration").text = dur
        ET.SubElement(note, "voice").text = str(staff)
        if staves > 1:
            ET.SubElement(note, "staff").text = str(staff)
    return m


# MusicXML vaatii <note>-elementin lapsille tämän järjestyksen. ET.SubElement
# lisäisi aina loppuun, jolloin esimerkiksi <staff> päätyisi <lyric>:n jälkeen
# ja tiedosto olisi skeeman vastainen.
NOTE_ORDER = [
    "grace", "cue", "chord", "pitch", "unpitched", "rest", "duration", "tie",
    "instrument", "footnote", "level", "voice", "type", "dot", "accidental",
    "time-modification", "stem", "notehead", "notehead-text", "staff", "beam",
    "notations", "lyric", "play", "listen",
]


def set_note_child(note, tag, text):
    """Aseta nuotin lapsielementti skeeman vaatimaan kohtaan."""
    e = note.find(tag)
    if e is None:
        e = ET.Element(tag)
        idx = NOTE_ORDER.index(tag)
        pos = len(list(note))
        for i, child in enumerate(list(note)):
            ci = NOTE_ORDER.index(child.tag) if child.tag in NOTE_ORDER else -1
            if ci > idx:
                pos = i
                break
        note.insert(pos, e)
    e.text = text
    return e


def ensure_filled(measure, div, beats, btype, staves):
    """Täytä sisällötön tahti kokotahdin tauolla.

    Audiveriksen vienti sisältää tahteja, joissa ei ole nuotteja eikä taukoja
    lainkaan. Sellainen tahti on kestoltaan nolla, mikä sekoittaa MuseScoren
    aikajanan: nuotit näkyvät mutta soitto pysähtyy siihen kuin seinään.
    """
    if measure.findall("note"):
        return 0
    dur = str(int(div * beats * 4 / btype))
    for staff in range(1, staves + 1):
        if staff > 1:
            backup = ET.SubElement(measure, "backup")
            ET.SubElement(backup, "duration").text = dur
        note = ET.SubElement(measure, "note")
        ET.SubElement(note, "rest").set("measure", "yes")
        ET.SubElement(note, "duration").text = dur
        ET.SubElement(note, "voice").text = str(staff)
        if staves > 1:
            ET.SubElement(note, "staff").text = str(staff)
    return 1


def measure_span(measure):
    """Tahdin pisin aikajana, backup- ja forward-siirtymät huomioiden."""
    pos = longest = 0
    for child in measure:
        if child.tag == "note":
            if child.find("chord") is not None or child.find("grace") is not None:
                continue
            pos += int(child.findtext("duration") or 0)
        elif child.tag == "backup":
            pos -= int(child.findtext("duration") or 0)
        elif child.tag == "forward":
            pos += int(child.findtext("duration") or 0)
        longest = max(longest, pos)
    return longest


def strip_spanners(measure):
    """Poista kaaret ja crescendot konelukemisen tuottamista tahdeista.

    Audiveris tuottaa kaaria ja crescendoja, joiden alku ja loppu eivät
    vastaa toisiaan. MuseScore kaatuu niihin (`Spanner::setTick2`) ja soitto
    pysähtyy kesken osan. Ne ovat pelkkiä merkintöjä, eivät säveliä tai
    rytmiä, joten poisto ei muuta soivaa sisältöä.
    """
    removed = 0
    for note in measure.findall("note"):
        notations = note.find("notations")
        if notations is None:
            continue
        for tag in ("slur", "glissando", "slide"):
            for e in notations.findall(tag):
                notations.remove(e)
                removed += 1
        if not list(notations):
            note.remove(notations)
    for direction in measure.findall("direction"):
        dtype = direction.find("direction-type")
        if dtype is not None and dtype.find("wedge") is not None:
            measure.remove(direction)
            removed += 1
    return removed


def blank_bad_measure(measure, div, beats, btype, staves):
    """Korvaa konelukemisen rikkoma pianotahti kokotahdin tauolla.

    Audiveris tuottaa tahteja, joiden sisältö ei vastaa tahtilajia. MuseScore
    kaatuu niihin (`Spanner::setTick2`, `ChordLayout::placeDots`) ja soitto
    pysähtyy kesken osan. Paikkaaminen ei onnistu luotettavasti, koska tauon
    oikea paikka riippuu äänestä ja viivastosta, joten koko tahti nollataan.
    Tätä sovelletaan vain pianoriviin: lauluäänissä nuotit ovat luettavaa
    sisältöä, eikä niiden tahdit ole kaataneet MuseScorea.
    """
    span = measure_span(measure)
    limit = int(div * beats * 4 / btype)
    if span == limit:
        return 0
    for child in list(measure):
        if child.tag in ("note", "backup", "forward"):
            measure.remove(child)
    dur = str(limit)
    for staff in range(1, staves + 1):
        if staff > 1:
            backup = ET.SubElement(measure, "backup")
            ET.SubElement(backup, "duration").text = dur
        note = ET.SubElement(measure, "note")
        ET.SubElement(note, "rest").set("measure", "yes")
        ET.SubElement(note, "duration").text = dur
        ET.SubElement(note, "voice").text = str(staff)
        if staves > 1:
            ET.SubElement(note, "staff").text = str(staff)
    return 1


def tag_staff(measure, staff):
    """Merkitse mitatun sisällön nuotit tietylle viivastolle."""
    for note in measure.findall("note"):
        set_note_child(note, "staff", str(staff))
    return measure


def has_notes(measure):
    return any(n.find("rest") is None for n in measure.findall("note"))


TYPE_QUARTERS = [
    ("maxima", 32), ("long", 16), ("breve", 8), ("whole", 4), ("half", 2),
    ("quarter", 1), ("eighth", 0.5), ("16th", 0.25), ("32nd", 0.125),
    ("64th", 0.0625), ("128th", 0.03125), ("256th", 0.015625),
]
QUARTERS = dict(TYPE_QUARTERS)


def dotted(base, dots):
    return base * (2 - 0.5 ** dots)


def type_for(quarters):
    for name, base in TYPE_QUARTERS:
        for dots in (0, 1, 2, 3):
            if abs(dotted(base, dots) - quarters) < 1e-9:
                return name, dots
    return None


def halved_note(note):
    """Onko nuotissa kaksinkertainen nuottiarvo puolella kestolla?

    Lähteissä 05 ja 16 pianostemman nuotilla on <time-modification> suhteella
    1:2^n, eli tyyppi on tuplasti kestoaan pidempi. Koodaus on laillista, mutta
    MuseScore laskee tahdin täyttymisen tyypeistä eikä huomioi kerrointa, joten
    se pitää tahtia liian pitkänä ja ilmoittaa tiedoston korruptoituneeksi.
    """
    tm = note.find("time-modification")
    if tm is None:
        return False
    actual = tm.findtext("actual-notes")
    normal = tm.findtext("normal-notes")
    if not actual or not normal or int(normal) != 1:
        return False
    n = int(actual)
    return n > 1 and (n & (n - 1)) == 0


def fix_halved_notes(measure, div, beats, btype):
    """Kirjoita kaksinkertaiset nuottiarvot vastaamaan todellista kestoa.

    Soiva tulos ei muutu; vain pianon nuottikuva niissä tahdeissa, joissa
    MuseScore muuten valittaisi. Palauttaa korjattujen nuottien määrän.
    """
    limit = div * beats * 4 / btype
    groups = {}
    for note in measure.findall("note"):
        if note.find("chord") is not None or note.find("grace") is not None:
            continue
        key = (note.findtext("staff") or "1", note.findtext("voice") or "1")
        groups.setdefault(key, []).append(note)

    fixed = 0
    for notes in groups.values():
        if not any(halved_note(n) for n in notes):
            continue
        actual = sum(int(n.findtext("duration") or 0) for n in notes)
        implied = sum(dotted(QUARTERS.get(n.findtext("type"), 0), len(n.findall("dot")))
                      for n in notes) * div
        if actual > limit or implied <= limit:
            continue  # ei ylivuotoa MuseScoren laskutavalla
        for note in notes:
            if not halved_note(note):
                continue
            if retype(note, div):
                note.remove(note.find("time-modification"))
                fixed += 1
    return fixed


def retype(note, div):
    """Aseta nuotin tyyppi ja pisteet vastaamaan sen kestoa."""
    want = type_for(int(note.findtext("duration") or 0) / div)
    if want is None or note.find("type") is None:
        return False
    name, dots = want
    note.find("type").text = name
    for d in note.findall("dot"):
        note.remove(d)
    for _ in range(dots):
        note.insert(list(note).index(note.find("type")) + 1, ET.Element("dot"))
    return True


def fix_rest_overflow(measure, div, beats, btype):
    """Korjaa pelkistä tauoista koostuvat äänet, joiden tyyppi on liian pitkä.

    Osassa 05 pianon ääni 2 koostuu tauoista, joiden tyyppi on kaksinkertainen
    kestoonsa nähden (kokotauko puolen tauon kestolla). MuseScore laskee
    täyttymisen tyypeistä ja pitää tahtia liian pitkänä. Tauolla ei ole
    sävelkorkeutta, joten sekä tyypin korjaus että ylimääräisen tauon
    lyhentäminen ovat musiikillisesti merkityksettömiä.
    """
    limit = div * beats * 4 / btype
    groups = {}
    for note in measure.findall("note"):
        if note.find("chord") is not None or note.find("grace") is not None:
            continue
        key = (note.findtext("staff") or "1", note.findtext("voice") or "1")
        groups.setdefault(key, []).append(note)

    fixed = 0
    for notes in groups.values():
        rests = [n for n in notes if n.find("rest") is not None]
        if not rests:
            continue
        implied = sum(dotted(QUARTERS.get(n.findtext("type"), 0), len(n.findall("dot")))
                      for n in notes) * div
        actual = sum(int(n.findtext("duration") or 0) for n in notes)
        if implied <= limit and actual <= limit:
            continue
        if len(rests) != len(notes):
            # Sekaryhmässä korjataan vain tauot, ja vain jos kestot mahtuvat
            # tahtiin. Ilman tuota vartijaa sääntö rikkoi ehjiä tahteja.
            if actual > limit:
                continue
            for note in rests:
                if retype(note, div):
                    fixed += 1
            continue
        for note in notes:
            if retype(note, div):
                fixed += 1
        excess = actual - limit
        for note in reversed(notes):
            if excess <= 0:
                break
            dur = int(note.findtext("duration"))
            if dur <= excess:
                measure.remove(note)
                excess -= dur
            else:
                note.find("duration").text = str(int(dur - excess))
                retype(note, div)
                excess = 0
            fixed += 1
    return fixed


def verse_number(value):
    """Poimi sanarivin numero. Lähteet käyttävät sekä muotoa "2" että
    "part5verse2"; sekamuoto samassa osastossa sekoittaa MuseScoren
    rivilaskennan, joten kaikki normalisoidaan pelkiksi numeroiksi."""
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if not digits:
        return 1
    return int(digits[-1]) if "verse" in (value or "") else int(digits)


def normalise_lyrics(measure):
    """Yhtenäistä sanarivien numerot ja siirrä eksyneet tavut pääriville.

    Yksi ääni laulaa yhtä tekstiä, joten jos tahdin kaikki tavut kuuluvat
    samalle äänelle eikä yksikään nuotti kanna kahta tavua, ne ovat yksi
    tekstirivi ja kuuluvat kaikki riville 1. Tämä ei ole kosmetiikkaa: OMR
    merkitsi osan I tahdissa 108 sanan "e-le-i-son" tavut riveille 2, 1 ja 2,
    ja stemmaan tuli kaksi puolikasta tekstiriviä keskeltä sanaa.

    Kahta poikkeusta ei yhdistetä. Kaksi tavua samalla nuotilla *tarvitsee*
    kaksi riviä, ja jos tahdissa on kaksi ääntä (divisi), rivit erottavat
    niiden erilliset tekstit toisistaan — esimerkiksi Lacrymosan tahdit
    682-684. Silloin jäljelle jää vanha sääntö: jos rivi 1 on kokonaan tyhjä,
    tavut nostetaan sille, koska MuseScore varaisi muuten tilan kaikille
    riveille ykkösestä siihen korkeimpaan ja työntäisi sanat kauas
    viivastosta.
    """
    by_note = [(note.findtext("voice") or "1", note.findall("lyric"))
               for note in measure.findall("note")]
    lyrics = [lyric for _voice, note_lyrics in by_note
              for lyric in note_lyrics]
    if not lyrics:
        return
    voices = {voice for voice, note_lyrics in by_note if note_lyrics}
    stacked = any(len(note_lyrics) > 1 for _voice, note_lyrics in by_note)
    if len(voices) == 1 and not stacked:
        for lyric in lyrics:
            lyric.set("number", "1")
        return
    numbers = [verse_number(lyric.get("number")) for lyric in lyrics]
    shift = 1 not in numbers
    for lyric, number in zip(lyrics, numbers):
        lyric.set("number", str(1 if shift else number))


def merge_voices(base, extras, div, beats, btype, staff=None):
    """Liitä päällekkäiset lähteet samalle riville omiksi äänikseen.

    Käytetään kun kaksi lähdeosastoa soi samassa tahdissa samalla rivillä,
    kuten Lacrymosan kuorobasson divisi.
    """
    out = copy.deepcopy(base)
    dur = str(int(div * beats * 4 / btype))
    voice = 1
    for note in out.findall("note"):
        set_note_child(note, "voice", "1")
    for extra in extras:
        voice += 1
        b = ET.Element("backup")
        ET.SubElement(b, "duration").text = dur
        out.append(b)
        for note in copy.deepcopy(extra).findall("note"):
            set_note_child(note, "voice", str(voice))
            if staff is not None:
                set_note_child(note, "staff", str(staff))
            out.append(note)
    return out


def combine_staves(number, pieces, div, beats, btype):
    """Kokoa kaksiviivastoinen tahti kahdesta yksiviivastoisesta lähteestä."""
    out = ET.Element("measure", {"number": number})
    dur = str(int(div * beats * 4 / btype))
    first = True
    for staff in (1, 2):
        src = pieces.get(staff)
        if not first:
            b = ET.SubElement(out, "backup")
            ET.SubElement(b, "duration").text = dur
        if src is None:
            note = ET.SubElement(out, "note")
            ET.SubElement(note, "rest").set("measure", "yes")
            ET.SubElement(note, "duration").text = dur
            ET.SubElement(note, "voice").text = str(staff)
            ET.SubElement(note, "staff").text = str(staff)
        else:
            for child in tag_staff(copy.deepcopy(src), staff):
                if child.tag in ("print", "barline"):
                    continue
                if child.tag == "attributes" and not first:
                    continue
                out.append(child)
        first = False
    return out


def build_attributes(div, beats, btype, clef, staves, fifths=0,
                     with_divisions=True, with_key=True, with_time=True,
                     with_clef=True):
    a = ET.Element("attributes")
    if with_divisions:
        ET.SubElement(a, "divisions").text = str(div)
    if with_key:
        k = ET.SubElement(a, "key")
        ET.SubElement(k, "fifths").text = str(fifths)
    if with_time:
        t = ET.SubElement(a, "time")
        ET.SubElement(t, "beats").text = str(beats)
        ET.SubElement(t, "beat-type").text = str(btype)
    if staves > 1 and with_divisions:
        ET.SubElement(a, "staves").text = str(staves)
    if not with_clef:
        return a
    sign, line, octave = clef
    for n in range(1, staves + 1):
        c = ET.SubElement(a, "clef")
        if staves > 1:
            c.set("number", str(n))
        ET.SubElement(c, "sign").text = "G" if (staves > 1 and n == 1) else ("F" if staves > 1 else sign)
        ET.SubElement(c, "line").text = "2" if (staves > 1 and n == 1) else ("4" if staves > 1 else line)
        if octave and staves == 1:
            ET.SubElement(c, "clef-octave-change").text = octave
    return a


def saumaraportti(alueet):
    """Kerro missä Dies iraen numerointi ei jatku saumojen yli aukottomasti.

    Alaosien alkunumerot tulevat kuoron nuottikirjasta (`DIES_IRAE_ALUT`),
    eivätkä CPDL:n osakohtaiset tiedostot katkea samoista kohdista kuin kirja.
    Siksi osa numeroista toistuu ja osa jää väliin. Se on tarkoituksellista —
    kirjan kanssa täsmääminen on tärkeämpää kuin katkeamaton juoksutus — mutta
    se ei saa olla hiljainen yllätys, joten se tulostetaan joka ajolla.
    """
    if len(alueet) < 2:
        return []
    rivit = []
    for (_, _, loppu), (nimi, alku, _) in zip(alueet, alueet[1:]):
        if alku <= loppu:
            rivit.append(f"  {nimi:6} alkaa {alku}, edellinen päättyi {loppu}"
                         f"  -> {loppu - alku + 1} numeroa toistuu")
        elif alku > loppu + 1:
            rivit.append(f"  {nimi:6} alkaa {alku}, edellinen päättyi {loppu}"
                         f"  -> {alku - loppu - 1} numeroa puuttuu lähteistä")
    if not rivit:
        return []
    return ["Dies iraen saumat (numerointi kirjan mukaan, ks. DIES_IRAE_ALUT):"] + rivit


def title_direction(label):
    d = ET.Element("direction", {"placement": "above"})
    dt = ET.SubElement(d, "direction-type")
    w = ET.SubElement(dt, "words")
    w.text = label
    w.set("font-size", "13")
    w.set("font-weight", "bold")
    return d


def main():
    args = sys.argv[1:]
    only = singer = None
    if "--vain" in args:
        i = args.index("--vain")
        only = [n.strip() for n in args[i + 1].split(",")]
        del args[i:i + 2]
    if "--stemma" in args:
        i = args.index("--stemma")
        singer = args[i + 1]
        del args[i:i + 2]
    out_path = args[0] if args else "Verdi-Requiem-koko.mxl"

    if singer:
        if singer not in SINGER_PARTS:
            raise SystemExit(f"tuntematon stemma: {singer}\n"
                             f"vaihtoehdot: {', '.join(SINGER_PARTS)}")
        normal, sanctus = SINGER_PARTS[singer]
        source = dict(TARGETS_BY_NAME)[normal]
        globals()["TARGETS"] = [(singer, singer, source[2], source[3])]
        globals()["MAPPING"] = {
            filename: {singer: rows.get(sanctus if filename == SANCTUS else normal, [])}
            for filename, rows in MAPPING.items()
        }
    else:
        targets = TARGETS if only is None else [t for t in TARGETS if t[0] in only]
        if not targets:
            raise SystemExit(f"tuntemattomat viivastot: {only}")
        globals()["TARGETS"] = targets

    root = ET.Element("score-partwise", {"version": "4.0"})
    work = ET.SubElement(root, "work")
    ET.SubElement(work, "work-title").text = "Messa da Requiem"
    if singer:
        # Stemman nimi otsikon alle, koska viivastojen nimet piilotetaan.
        ET.SubElement(root, "movement-title").text = f"Messa da Requiem \u00b7 {singer}"
    ident = ET.SubElement(root, "identification")
    cr = ET.SubElement(ident, "creator")
    cr.set("type", "composer")
    cr.text = "Giuseppe Verdi"

    part_list = ET.SubElement(root, "part-list")
    parts = {}
    for idx, (name, abbr, staves, _clef) in enumerate(TARGETS, start=1):
        pid = f"P{idx}"
        sp = ET.SubElement(part_list, "score-part", {"id": pid})
        pn = ET.SubElement(sp, "part-name")
        pn.text = name
        pa = ET.SubElement(sp, "part-abbreviation")
        pa.text = abbr
        if singer:
            # Yhden stemman tiedostossa nimi jokaisen rivin alussa on
            # pelkkää tilanhukkaa; se on jo otsikossa.
            pn.set("print-object", "no")
            pa.set("print-object", "no")
        parts[name] = ET.SubElement(root, "part", {"id": pid})

    warnings = []
    repaired = 0
    filled = 0
    evened = 0
    stats = {name: 0 for name, *_ in TARGETS}

    alueet = []
    for filename, numero, otsikko in MOVEMENTS:
        src = load(filename)
        src_parts = {p.get("id"): p for p in src.findall("part")}
        mapping = MAPPING.get(filename, {})

        ref = src_parts[max(src_parts, key=lambda k: len(src_parts[k].findall("measure")))]
        numbers = [m.get("number") for m in ref.findall("measure")]
        meta = measure_meta(ref)
        offset = 0
        if not NUMEROINTI_ALKAA_JOKA_OSASSA_YKKOSESTA:
            offset = DIES_IRAE_SIIRTYMAT.get(filename, 0)
        if filename in DIES_IRAE_ALUT:
            alueet.append((numero, offset + int(numbers[0]),
                           offset + int(numbers[-1])))

        for name, abbr, staves, clef in TARGETS:
            target = parts[name]
            slices = normalise(mapping.get(name, []))
            for slot, number in enumerate(numbers):
                div, beats, btype, fifths, time_changed, key_changed = \
                    meta.get(number, (4, 4, 4, 0, False, False))
                active = [s for s in slices if covers(s, int(number))]
                # Kerää kaikki tätä tahtia koskevat lähteet kohdeviivastoittain.
                found_by_staff = {}
                for pid, _lo, _hi, staff in active:
                    sp = src_parts.get(pid)
                    if sp is None:
                        warnings.append(f"{filename}: osastoa {pid} ei ole")
                        continue
                    found = next((m for m in sp.findall("measure")
                                  if m.get("number") == number), None)
                    if found is not None:
                        found_by_staff.setdefault(staff, []).append(found)

                # Nuotilliset voittavat tauot; useampi nuotillinen yhdistyy ääniksi.
                pieces, extras = {}, {}
                for staff, cands in found_by_staff.items():
                    live = [c for c in cands if has_notes(c)]
                    if live:
                        pieces[staff] = live[0]
                        extras[staff] = live[1:]
                    else:
                        pieces[staff] = cands[0]
                        extras[staff] = []

                split_piano = (
                    staves == 2 and active
                    and not any(src_parts[a[0]].find("measure/attributes/staves") is not None
                                for a in active))

                generated = not pieces
                if generated:
                    m = rest_measure(number, div, beats, btype, staves)
                elif split_piano:
                    m = combine_staves(number, pieces, div, beats, btype)
                else:
                    staff = next(iter(pieces))
                    if extras[staff]:
                        m = merge_voices(pieces[staff], extras[staff], div, beats, btype)
                    else:
                        m = copy.deepcopy(pieces[staff])
                    m.set("number", number)

                if offset:
                    m.set("number", str(int(number) + offset))

                # Lähteiden omat rivin- ja sivunvaihdot koskevat alkuperäistä
                # sivuasettelua eivätkä sovi yhdistettyyn partituuriin lainkaan.
                for pr in m.findall("print"):
                    m.remove(pr)

                filled += ensure_filled(m, div, beats, btype, staves)
                normalise_lyrics(m)
                repaired += fix_halved_notes(m, div, beats, btype)
                repaired += fix_rest_overflow(m, div, beats, btype)

                # Vaikeneva rivi ei peri lähteen tahtilajin ja sävellajin
                # vaihtoja, joten ne julistetaan tässä erikseen.
                if generated and slot > 0 and (time_changed or key_changed):
                    m.insert(0, build_attributes(
                        div, beats, btype, clef, staves, fifths=fifths,
                        with_divisions=False, with_key=key_changed,
                        with_time=time_changed, with_clef=False))

                if slot == 0:
                    attrs = m.find("attributes")
                    if attrs is None:
                        m.insert(0, build_attributes(div, beats, btype, clef,
                                                     staves, fifths=fifths))
                    else:
                        if attrs.find("divisions") is None:
                            ET.SubElement(attrs, "divisions").text = str(div)
                    pr = ET.Element("print")
                    pr.set("new-system", "yes")
                    m.insert(0, pr)
                    if name in TITLE_PARTS or len(TARGETS) == 1:
                        pos = 1 + (1 if m.find("attributes") is not None else 0)
                        m.insert(pos, title_direction(f"{numero}  {otsikko}"))
                if slot == len(numbers) - 1 and m.find("barline") is None:
                    bl = ET.SubElement(m, "barline", {"location": "right"})
                    ET.SubElement(bl, "bar-style").text = "light-heavy"

                stats[name] += sum(1 for n in m.findall("note") if n.find("rest") is None)
                target.append(m)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("META-INF/container.xml",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<container><rootfiles>'
                   '<rootfile full-path="score.xml" '
                   'media-type="application/vnd.recordare.musicxml+xml"/>'
                   "</rootfiles></container>\n")
        z.writestr("score.xml", ET.tostring(root, encoding="UTF-8", xml_declaration=True))

    total = len(next(iter(parts.values())).findall("measure"))
    print(f"kirjoitettu {out_path}")
    print(f"tahteja per viivasto: {total}")
    print("nuotteja riveittäin:")
    for name, *_ in TARGETS:
        print(f"  {name:14} {stats[name]:6}")
    if filled:
        print(f"täytetty {filled} sisällötöntä tahtia kokotahdin tauolla")
    if evened:
        print(f"tasattu {evened} vääränmittaista tahtia (konelukemisen osat)")
    if repaired:
        print(f"korjattu {repaired} kaksinkertaista nuottiarvoa (piano)")
    for rivi in saumaraportti(alueet):
        print(rivi)
    for w in dict.fromkeys(warnings):
        print("VAROITUS:", w)


if __name__ == "__main__":
    main()
