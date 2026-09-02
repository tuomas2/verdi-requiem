#!/usr/bin/env python3
"""Käsin todennetut korjaukset, jotka automaatti ei löydä.

`korjaa_sanat.py` korjaa konelukemisen sanat lähde-PDF:ää vasten mekaanisesti.
Sen jälkeen jää joukko virheitä, joita mikään automaatti ei löydä: tavu
väärällä nuotilla, kokonaan puuttuva tavu, konelukemisen roskatavu,
ylimääräinen tauko. Ne löytyvät vain kun laulaja kuulee kohdan väärin tai
kun jotain verrataan silmällä lähdesivuun, ja ne luetellaan tässä yksitellen.

Aiemmin nämä muokattiin suoraan .mxl-tiedostoon eikä niitä voinut tuottaa
uudelleen. Nyt koko ketju on toistettava:

    korjaa_sanat.py  ->  *-OMR-korjattu.mxl     (PDF:n sanat, mekaanisesti)
    korjaa_kasin.py  ->  *-kasin.mxl            (tämä, todennetut korjaukset)
    yhdista.py       ->  partituuri ja stemmat

Jokainen korjaus tarkistaa lähtötilanteen ja kaatuu, jos syöte on muuttunut
odottamattomasti. Se on tarkoituksellista: hiljaa väärään paikkaan osuva
korjaus on pahempi kuin pysähtynyt ajo.

    python3 korjaa_kasin.py            # kirjoittaa tiedostot
    python3 korjaa_kasin.py --kuiva    # kertoo mitä tekisi

Uuden korjauksen lisääminen: kirjoita rivi oikean `Osa`:n `korjaukset`-listaan
ja perustele se kommentissa lähdesivun numerolla. Uuden osan lisääminen: uusi
`Osa` `OSAT`-listaan ja `yhdista.py`:n `MOVEMENTS` osoittamaan sen `out`-
tiedostoon. Menetelmä eli miten korjaus todennetaan ennen kirjaamista on
`CLAUDE.md`:ssä, luku *Recipe: a singer reports a wrong syllable by ear*.
"""
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from korjaa_sanat import find_part, load, save


@dataclass(frozen=True)
class Osa:
    """Yksi osa: mistä luetaan, mihin kirjoitetaan, mitä korjataan."""

    mxl: str            # lähde, jota ei koskaan muokata
    out: str            # tulos, jonka yhdista.py lukee
    osasto: str         # osaston tunnus lähteessä
    nimi: str           # viivaston nimi raporttiin
    yksi_sanarivi: bool  # nostetaanko kaikki tavut sanariville 1
    korjaukset: tuple   # (tahti, nuotti, toimenpide, argumentit...)


# Toimenpiteet:
#   ("poista", teksti)                  poista tavu, jonka teksti on tämä
#   ("lisaa", syllabic, teksti)         lisää tavu nuotille jolla ei ole
#   ("aseta", vanha, syllabic, teksti)  korvaa tavu toisella
#   ("poista_nuotti", kuvaus)           poista nuotti tai tauko
# Nuotti on indeksi tahdin <note>-alkioissa, tauot mukaan luettuina.

OSA_I = Osa(
    mxl="01-Verdi_Requiem-OMR-korjattu.mxl",
    out="01-Verdi_Requiem-kasin.mxl",
    osasto="P16",
    nimi="Kuoro B",
    # Kuorobassolla on osan I PDF:ssä yksi tekstirivi alusta loppuun, mutta
    # konelukema hajotti 55 tavua riville 2.
    yksi_sanarivi=True,
    korjaukset=(
        # Sivu 2: "o-ra-ti-o-nem me-am," päättyy tähän, joten "am" on sanan
        # viimeinen tavu eikä keskimmäinen. Väärä syllabic jättää tavuviivan
        # roikkumaan seuraavan tavun perään.
        ("49", 0, "aseta", "am", "end", "am"),

        # Sivu 3: "ad te om-nis ca-ro ve-ni-et." Laulaja pyysi melisman
        # tavulle "om", jolloin "nis" tulee vasta tahdin 52 viimeiselle
        # nuotille. HUOM: lähde-PDF merkitsee sen toisin päin — "nis" tahdin
        # 51 kolmannelle iskulle ja melisma sen jälkeen. Jos kuoron
        # nuottikirja on PDF:n kannalla, nämä kaksi riviä vaihdetaan päittäin.
        ("51", 1, "poista", "nis"),
        ("52", 3, "lisaa", "end", "nis"),

        # Konelukema jätti tahtiin 54 ylimääräisen 16-osatauon, jolloin tahti
        # on 17/16 pitkä. Nuotit itse ovat oikein (12 + 4 = 16).
        ("54", 2, "poista_nuotti", "rest"),

        # Sivu 4: kuorobasson rivillä lukee "lu-ce-at e - - - is." eikä
        # mitään S-kirjainta. Konelukema oli pudottanut yksinäisen "S":n
        # oikean "is."-tavun päälle omalle sanariville.
        ("78", 0, "poista", "S"),

        # Sivu 9, 2. järjestelmä: tahdin 126 molemmilla puolinuoteilla on
        # tavu ("le", "i") ja "son," on tahdin 127 ensimmäisellä nuotilla.
        # Konelukema oli myöhässä yhden nuotin.
        ("126", 1, "lisaa", "middle", "i"),
        ("127", 0, "aseta", "i", "end", "son,"),

        # Sivu 10, 1. järjestelmä: tahti 129 kantaa tavun "i" ja tahti 130
        # tavun "son,". Sama myöhästyminen kuin edellä.
        ("129", 0, "lisaa", "middle", "i"),
    ),
)

# Osien 11 (Lacrymosa) ja 14 (Agnus Dei) vastaavat korjaukset on aikanaan
# tehty suoraan lähdetiedostoon, joten niillä ei ole omaa Osa-riviä. Jos ne
# joskus puretaan tänne, ks. CLAUDE.md, *Recipe*-luvun viimeinen kappale.
OSAT = [OSA_I]


def lyriikat(note):
    return note.findall("lyric")


def teksti(lyric):
    return lyric.findtext("text")


def uusi_lyric(syllabic, text):
    ly = ET.Element("lyric", {"number": "1"})
    ET.SubElement(ly, "syllabic").text = syllabic
    ET.SubElement(ly, "text").text = text
    return ly


def kuvaa(note):
    """Nuotin tunniste virheilmoituksia varten."""
    pitch = note.find("pitch")
    if pitch is None:
        return "rest"
    return (pitch.findtext("step") + (pitch.findtext("alter") or "")
            + pitch.findtext("octave"))


def sovella(part, osa):
    """Aja osan korjaukset osastoon ja palauta selosteet."""
    tahdit = {m.get("number"): m for m in part.findall("measure")}
    selosteet = []

    for tahti, i, laji, *args in osa.korjaukset:
        measure = tahdit.get(tahti)
        assert measure is not None, f"tahtia {tahti} ei ole"
        notes = measure.findall("note")
        assert i < len(notes), f"t.{tahti}: nuottia {i} ei ole ({len(notes)})"
        note = notes[i]

        if laji == "poista":
            (odotettu,) = args
            osuu = [ly for ly in lyriikat(note) if teksti(ly) == odotettu]
            assert osuu, f"t.{tahti} nuotti {i}: tavua {odotettu!r} ei ole"
            for ly in osuu:
                note.remove(ly)
            selosteet.append(f"t.{tahti}: poistettu tavu {odotettu!r}")

        elif laji == "lisaa":
            syllabic, text = args
            assert not lyriikat(note), (
                f"t.{tahti} nuotti {i}: kantaa jo tavun "
                f"{teksti(lyriikat(note)[0])!r}")
            note.append(uusi_lyric(syllabic, text))
            selosteet.append(f"t.{tahti}: lisätty tavu {text!r}")

        elif laji == "aseta":
            odotettu, syllabic, text = args
            ly = lyriikat(note)
            assert len(ly) == 1 and teksti(ly[0]) == odotettu, (
                f"t.{tahti} nuotti {i}: odotettiin {odotettu!r}, "
                f"on {[teksti(x) for x in ly]}")
            ly[0].find("syllabic").text = syllabic
            ly[0].find("text").text = text
            selosteet.append(f"t.{tahti}: {odotettu!r} -> {text!r}")

        elif laji == "poista_nuotti":
            (odotettu,) = args
            assert kuvaa(note) == odotettu, (
                f"t.{tahti} nuotti {i}: odotettiin {odotettu}, "
                f"on {kuvaa(note)}")
            measure.remove(note)
            selosteet.append(f"t.{tahti}: poistettu ylimääräinen {odotettu}")

        else:
            raise AssertionError(f"tuntematon toimenpide {laji}")

    if osa.yksi_sanarivi:
        selosteet.append(yksi_sanarivi(part))
    return selosteet


def yksi_sanarivi(part):
    """Nosta kaikki tavut sanariville 1.

    Rivi 2 olisi aito vain jos jokin nuotti kantaisi kahta tavua yhtä aikaa
    tai viivastolla olisi kaksi ääntä; kumpikin tarkistetaan, koska muuten
    tavut menisivät päällekkäin samalle riville.
    """
    paallekkain = [(m.get("number"), teksti(ly))
                   for m in part.findall("measure")
                   for n in m.findall("note") if len(lyriikat(n)) > 1
                   for ly in lyriikat(n)]
    assert not paallekkain, f"kaksi tavua samalla nuotilla: {paallekkain}"
    aanet = {n.findtext("voice") or "1" for m in part.findall("measure")
             for n in m.findall("note") if lyriikat(n)}
    assert len(aanet) <= 1, f"tavuja usealla äänellä: {sorted(aanet)}"

    siirretty = 0
    for m in part.findall("measure"):
        for n in m.findall("note"):
            for ly in lyriikat(n):
                if ly.get("number") != "1":
                    ly.set("number", "1")
                    siirretty += 1
    return f"sanarivit: {siirretty} tavua nostettu riville 1"


def main(argv):
    dry = "--kuiva" in argv
    for osa in OSAT:
        root = load(osa.mxl)
        selosteet = sovella(find_part(root, osa.osasto), osa)
        print(f"{osa.mxl} -> {osa.out}, {osa.osasto} ({osa.nimi})")
        for s in selosteet:
            print("  " + s)
        if dry:
            print("  (kuiva ajo, mitään ei kirjoitettu)")
        else:
            save(root, osa.mxl, osa.out)
            print(f"  kirjoitettu {osa.out}")


if __name__ == "__main__":
    main(sys.argv[1:])
