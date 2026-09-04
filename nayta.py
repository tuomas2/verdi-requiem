#!/usr/bin/env python3
"""Näytä yhden viivaston nuotit ja sanat tahdeittain.

Ensimmäinen työkalu joka otetaan käteen kun laulaja sanoo "tahdissa 126 on
väärä tavu": .mxl on zipattua XML:ää eikä sitä lueta silmällä, ja MuseScoren
avaaminen kertoo vain mitä sivulla näkyy, ei mitä datassa lukee — esimerkiksi
sanarivin numero (`number`) ratkaisee monta vikaa eikä näy nuottikuvassa.

    python3 nayta.py stemma-basso-1.mxl 126 130
    python3 nayta.py 01-Verdi_Requiem-kasin.mxl 126 130 --osasto P16
    python3 nayta.py Verdi-Requiem-koko.mxl 682 684 --osasto "Kuoro B"

Ilman --osastoa otetaan tiedoston ainoa viivasto. Osaston voi antaa joko
tunnuksella (P16) tai nimellä (Kuoro B). Ilman tahtivälejä listataan
viivastot.

Tulosteen kentät nuottia kohti:

    Cis3/4/quarter/tie<  v1  [1 end 'nis']
    |    | |       |     |   |  |    |
    |    | |       |     |   |  |    tavu
    |    | |       |     |   syllabic: single/begin/middle/end
    |    | |       |     sanarivi — muu kuin 1 tarkoittaa toista tekstiriviä
    |    | |       |     ääni; kaksi ääntä samalla viivastolla on divisi
    |    | |       sidonta: < alkaa, > päättyy
    |    | nuottiarvo (type)
    |    kesto (duration) — vertaa tahdin summaa divisions*tahtilajiin
    korkeus, tai rest; + edessä tarkoittaa soinnun toista säveltä
"""
import sys
import zipfile
import xml.etree.ElementTree as ET

import polut
import yhdista


def load(path):
    if path.lower().endswith(".mxl"):
        with zipfile.ZipFile(polut.polku(path)) as z:
            name = next(n for n in z.namelist()
                        if not n.startswith("META-INF")
                        and n.lower().endswith(".xml"))
            return ET.fromstring(z.read(name))
    return ET.parse(path).getroot()


def nimet(root):
    """Osaston tunnus -> nimi."""
    return {sp.get("id"): sp.findtext("part-name")
            for sp in root.findall("part-list/score-part")}


def valitse(root, haku):
    parts = root.findall("part")
    if haku is None:
        if len(parts) != 1:
            raise SystemExit("anna --osasto; viivastoja on %d" % len(parts))
        return parts[0]
    for p in parts:
        if p.get("id") == haku or nimet(root).get(p.get("id")) == haku:
            return p
    raise SystemExit("tuntematon osasto: %s" % haku)


def kuvaa_nuotti(note):
    pitch = note.find("pitch")
    if pitch is None:
        teksti = "rest"
    else:
        alter = pitch.findtext("alter")
        merkki = {"1": "is", "-1": "es", "2": "isis", "-2": "eses"}
        teksti = (pitch.findtext("step") + merkki.get(alter, alter or "")
                  + pitch.findtext("octave"))
    if note.find("chord") is not None:
        teksti = "+" + teksti
    osat = [teksti, note.findtext("duration") or "?",
            note.findtext("type") or "-"]
    sidonta = "".join("<" if t.get("type") == "start" else ">"
                      for t in note.findall("tie"))
    if sidonta:
        osat.append("tie" + sidonta)
    rivi = "/".join(osat) + "  v" + (note.findtext("voice") or "?")
    for ly in note.findall("lyric"):
        rivi += "  [%s %s %r]" % (ly.get("number") or "?",
                                  ly.findtext("syllabic") or "-",
                                  ly.findtext("text"))
        if ly.find("extend") is not None:
            rivi += "+jatke"
    return rivi


def main(argv):
    osasto = None
    if "--osasto" in argv:
        i = argv.index("--osasto")
        osasto = argv[i + 1]
        del argv[i:i + 2]
    if not argv:
        raise SystemExit(__doc__)

    root = load(argv[0])
    if len(argv) < 3:
        for pid, nimi in nimet(root).items():
            p = next((x for x in root.findall("part") if x.get("id") == pid),
                     None)
            n = len(p.findall("measure")) if p is not None else 0
            print("%-6s %-12s %4d tahtia" % (pid, nimi, n))
        return

    part = valitse(root, osasto)
    lo, hi = int(argv[1]), int(argv[2])
    # Tahtinumerot alkavat joka pääosassa alusta, joten sama numero osuu
    # yhdistetyssä tiedostossa moneen kohtaan. yhdista.py kirjoittaa osan
    # otsikon osan ensimmäiseen tahtiin; poimitaan se, jotta tulosteesta
    # näkee kummasta tahdista 126 on kyse.
    #
    # Otsikko tunnistetaan tekstistä eikä fontista: lähteissä on omia
    # lihavoituja ohjetekstejä ("Alle", "4 soli"), ja fonttihaku näytti niitä
    # osan nimenä — Libera men tahti 274 luki "[Alle]".
    osa = ""
    for m in part.findall("measure"):
        for w in m.findall("direction/direction-type/words"):
            if w.text in yhdista.OSAOTSIKOT:
                osa = w.text
        numero = int(m.get("number"))
        if not lo <= numero <= hi:
            continue
        notes = m.findall("note")
        summa = sum(int(n.findtext("duration") or 0) for n in notes
                    if n.find("chord") is None)
        print("t.%-5s %-24s (kestot yhteensä %d)"
              % (numero, osa and "[" + osa + "]", summa))
        for i, note in enumerate(notes):
            print("   %2d  %s" % (i, kuvaa_nuotti(note)))


if __name__ == "__main__":
    main(sys.argv[1:])
