#!/usr/bin/env python3
"""Rakentaa harjoittelutiedoston yhdelle laulajalle.

Oma ääni soi trumpettina ja näkyy ainoana viivastona; muut soivat mutta
ovat piilossa. Taukotahdit tiivistyvät, joten omat tauot eivät vie sivuja.

MuseScore erottaa viivaston *nimen* ja *soittimen*: viivastolla lukee
edelleen "Kuoro B" vaikka se soi trumpettina.
"""
import re
import subprocess
import sys
import zipfile

from yhdista import SINGER_PARTS

# (MuseScoren soitintunniste, ohjelmanumero) — tunnisteet on poimittu
# MuseScoren omista pohjatiedostoista, ohjelmanumero on nollapohjainen
# kuten MuseScoren <program value>, ei MusicXML:n yksipohjainen.
SOUND = {
    "oma":     ("brass.trumpet.c", 56),   # se rivi jota luetaan
    "kuoro":   ("voice.vocals", 52),      # choir aahs
    "solisti": ("wind.reed.oboe", 68),
    "piano":   ("keyboard.piano", 0),
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
    # Tuba mirumin vasket soivat pianona. Ne eivät saa olla vaskea
    # lainkaan, koska luettava rivi on trumpetti ja ne sekoittuisivat
    # juuri siinä osassa jossa kuoro laulaa niiden kanssa.
    return SOUND["piano"]


def set_sounds(mscx, own):
    """Asettaa jokaisen osaston soittimen MuseScoren omassa tiedostossa.

    Tämä tehdään täällä eikä MusicXML:ssä, koska MusicXML:n
    <instrument-name> meni MuseScoren tuonnissa läpi vain kahdelle
    osastolle viidestätoista — loput jäivät flyygeliksi riippumatta
    siitä oliko mukana <midi-channel> vai ei.

    Viivaston nimeen ei kosketa: nimi ja soitin ovat MuseScoressa eri
    asia, joten viivastolla lukee edelleen "Kuoro B" vaikka se soi
    trumpettina.
    """
    out, at = [], 0
    for match in re.finditer(r"<Part\b[^>]*>", mscx):
        end = mscx.index("</Part>", match.end())
        block = mscx[match.end():end]
        name = re.search(r"<trackName>([^<]*)</trackName>", block)
        if name is None:
            continue
        sound, program = instrument_for(name.group(1), own)
        block = re.sub(r"<instrumentId>[^<]*</instrumentId>",
                       "<instrumentId>%s</instrumentId>" % sound, block)
        block = re.sub(r'<program value="\d+"\s*/>',
                       '<program value="%d"/>' % program, block)
        out.append(mscx[at:match.end()])
        out.append(block)
        at = end
    out.append(mscx[at:])
    return "".join(out)


def hide_others(mscx, visible):
    """Piilottaa kaikki viivastot paitsi nimetyt.

    MuseScoren omassa muodossa osasto piilotetaan <show>0</show>:lla.
    Piilotettu viivasto soi edelleen, mikä on koko idea: kuulet koko
    kuoron ja pianon vaikka luet vain omaa riviäsi.
    """
    out, at = [], 0
    for match in re.finditer(r'<Part\b[^>]*>', mscx):
        end = mscx.index("</Part>", match.end())
        name = re.search(r"<trackName>([^<]*)</trackName>",
                         mscx[match.end():end])
        out.append(mscx[at:match.end()])
        if name is not None and name.group(1) not in visible:
            out.append("<show>0</show>")
        at = match.end()
    out.append(mscx[at:])
    return "".join(out)


MSCORE = "/Applications/MuseScore 4.app/Contents/MacOS/mscore"
LAHDE = "Verdi-Requiem-koko.mxl"
TYYLI = "tiivistys.mss"


def slug(voice):
    """'Basso I' -> 'basso-1', samaan tapaan kuin stemmatiedostoissa."""
    name, number = voice.rsplit(" ", 1)
    return "%s-%s" % (name.lower(), {"I": "1", "II": "2"}[number])


def _mscore(*args):
    """MuseScoren komentorivi.

    Poistumiskoodia ei katsota: se kaatuu satunnaisesti sammutusvaiheessa
    (134) kirjoitettuaan tiedoston valmiiksi. Tulos tarkistetaan
    tiedostosta.
    """
    subprocess.run([MSCORE] + list(args), capture_output=True)


def build(voice, source=LAHDE, style=TYYLI):
    """Rakentaa harjoittelutiedoston yhdelle laulajalle."""
    own = SINGER_PARTS[voice]
    out = "harjoitus-%s.mscz" % slug(voice)

    _mscore("-S", style, "-o", out, source)
    if not zipfile.is_zipfile(out):
        raise SystemExit("MuseScore ei kirjoittanut tiedostoa %s" % out)

    with zipfile.ZipFile(out) as z:
        score = next(n for n in z.namelist() if n.endswith(".mscx"))
        members = [(n, z.read(n)) for n in z.namelist()]

    mscx = dict(members)[score].decode("utf-8")
    mscx = hide_others(set_sounds(mscx, own), set(own))

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in members:
            z.writestr(name, mscx.encode("utf-8") if name == score else data)
    return out


def main(argv):
    if "--stemma" not in argv:
        raise SystemExit('käyttö: python3 harjoitus.py --stemma "Basso I"')
    voice = argv[argv.index("--stemma") + 1]
    if voice not in SINGER_PARTS:
        raise SystemExit("tuntematon ääni %r, vaihtoehdot: %s"
                         % (voice, ", ".join(sorted(SINGER_PARTS))))
    out = build(voice)
    näkyy = " ja ".join(sorted(set(SINGER_PARTS[voice])))
    print("kirjoitettu %s" % out)
    print("  näkyvissä: %s, soi trumpettina" % näkyy)
    print("  muut viivastot piilossa mutta soivat")


if __name__ == "__main__":
    main(sys.argv[1:])
