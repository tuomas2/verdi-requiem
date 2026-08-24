#!/usr/bin/env python3
"""Rakentaa harjoittelutiedoston yhdelle laulajalle.

Oma ääni soi trumpettina ja näkyy ainoana viivastona; muut soivat mutta
ovat piilossa. Taukotahdit tiivistyvät, joten omat tauot eivät vie sivuja.

MuseScore erottaa viivaston *nimen* ja *soittimen*: viivastolla lukee
edelleen "Kuoro B" vaikka se soi trumpettina.
"""
import xml.etree.ElementTree as ET

from korjaa_sanat import load, save

# (nimi MusicXML:ään, General MIDI -ohjelmanumero 1-128)
# Nimestä MuseScore päättelee soittimen; ohjelmanumero on varmistus.
SOUND = {
    "oma":     ("Trumpet", 57),      # se rivi jota luetaan
    "kuoro":   ("Choir Aahs", 53),
    "solisti": ("Oboe", 69),
    # Tuba mirumissa on oikea D-trumpettistemma. Se ei saa soida
    # trumpettina, koska se sekoittuisi luettavaan riviin juuri siinä
    # osassa jossa kuoro laulaa sen kanssa.
    "vaski":   ("Brass Section", 62),
    "piano":   ("Piano", 1),
}


def instrument_for(staff, own):
    """Minkä soittimen tämä viivasto saa.

    own on (tavallinen viivasto, Sanctuksen viivasto) — kaksoiskuoro
    esiintyy vain Sanctuksessa, joten kuoro II:n laulajalla omia
    viivastoja on kaksi.
    """
    if staff in own:
        return SOUND["oma"]
    if staff.startswith("Solisti"):
        return SOUND["solisti"]
    if staff.startswith("Kuoro"):
        return SOUND["kuoro"]
    if staff in ("D-trumpetti", "Trombone"):
        return SOUND["vaski"]
    return SOUND["piano"]


# <score-part>-lapsilla on pakollinen järjestys; soitinelementit tulevat
# nimien jälkeen ja MIDI-elementti oman määrittelynsä jälkeen.
PART_ORDER = [
    "identification", "part-link", "part-name", "part-name-display",
    "part-abbreviation", "part-abbreviation-display", "group",
    "score-instrument", "player", "midi-device", "midi-instrument",
]


def _place(parent, tag):
    """Lisää lapsi skeeman vaatimaan kohtaan eikä loppuun."""
    child = ET.Element(tag)
    after = PART_ORDER[:PART_ORDER.index(tag) + 1]
    at = 0
    for i, existing in enumerate(parent):
        if existing.tag in after:
            at = i + 1
    parent.insert(at, child)
    return child


def set_instruments(root, own):
    """Antaa jokaiselle viivastolle soittimen soittoa varten.

    Viivaston nimeen ei kosketa: MuseScore lukee soittimen
    <score-instrument>-elementistä, joten viivastolla lukee edelleen
    "Kuoro B" vaikka se soi trumpettina.
    """
    for part in root.iter("score-part"):
        staff = (part.findtext("part-name") or "").strip()
        name, program = instrument_for(staff, own)

        for tag in ("score-instrument", "midi-device", "midi-instrument"):
            for old in part.findall(tag):
                part.remove(old)

        ident = part.get("id") + "-I1"
        score = _place(part, "score-instrument")
        score.set("id", ident)
        ET.SubElement(score, "instrument-name").text = name

        midi = _place(part, "midi-instrument")
        midi.set("id", ident)
        ET.SubElement(midi, "midi-program").text = str(program)
