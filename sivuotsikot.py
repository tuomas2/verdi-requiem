#!/usr/bin/env python3
"""Kirjoita jokaisen sivun ensimmäisen tahdin päälle käynnissä olevan osan nimi.

Laulaja selailee stemmaa harjoituksissa, ja osan nimi näkyy vain siellä missä
osa alkaa — keskeltä osaa avatulla sivulla ei ole mitään, mikä kertoisi onko
kyse Lacrymosasta vai Libera mestä. Tämä lisää sivun vasempaan ylälaitaan
kursiivin "II·10  Lacrymosa" -tyyppisen otsikon, tahtinumeroiden yläpuolelle.

    python3 sivuotsikot.py stemma-basso-1.mxl
    python3 sivuotsikot.py stemma-*.mxl

Ajetaan `yhdista.py`:n jälkeen ja ennen PDF:n tekoa. Tiedostoa muokataan
paikallaan; uudelleenajo on turvallista, koska vanhat otsikot poistetaan
ensin.

## Miksi tämä on erillinen kaksivaiheinen työkalu

Sivunvaihdot eivät ole tiedostossa vaan MuseScore laskee ne, joten "sivun
ensimmäinen tahti" ei ole tiedettävissä ennen taittoa. Siksi asettelu
kysytään MuseScorelta: `mscore -o x.musicxml` kirjoittaa lasketun taiton
`<print new-page="yes">` -alkioina, ja niistä sivualut luetaan suoraan.
Sitten otsikot kirjoitetaan ja taitto kysytään uudelleen: jos sivualut
muuttuivat, kierros toistetaan. Mitattu tulos on että ne eivät muutu —
otsikko mahtuu tahtinumerorivin yläpuolelle olevaan tyhjään tilaan eikä
sivumäärä kasva — mutta silmukka on silti tässä, koska sitä ei voi tietää
etukäteen tyylin muuttuessa.

Kokeiltu ja hylätty: `<credit page="N">`, joka on MusicXML:n oma tapa
sijoittaa tekstiä tietylle sivulle ja olisi asettelusta riippumaton.
MuseScore 4.7.4 ei tuo niitä lainkaan — sivuille 2 ja 3 asetetut credit-
tekstit eivät päätyneet PDF:ään. Myös MuseScoren ylätunniste kokeiltiin: se
on sivukohtainen mutta sen teksti on koko tiedostossa sama, eikä siihen ole
"käynnissä oleva osa" -makroa.
"""
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import yhdista
from korjaa_sanat import load, save

MSCORE = os.environ.get(
    "MSCORE", "/Applications/MuseScore 4.app/Contents/MacOS/mscore")
TYYLI = "tiivistys.mss"
TUNNISTE = "sivuotsikko"      # <words id="sivuotsikkoN">, jotta ne löytyvät
KIERROSRAJA = 5


def vie_asettelu(mxl):
    """Anna MuseScoren taittaa tiedosto ja palauta sen MusicXML-vienti.

    Vienti sisältää lasketun sivu- ja järjestelmäjaon <print>-alkioina.
    """
    with tempfile.TemporaryDirectory() as tmp:
        ulos = os.path.join(tmp, "asettelu.musicxml")
        subprocess.run([MSCORE, "-S", TYYLI, "-o", ulos, mxl],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # mscore kaatuu purkautuessaan noin joka kolmannella ajolla vaikka
        # tiedosto on kirjoitettu kokonaan, joten paluuarvoa ei katsota vaan
        # tulos. Sama sääntö kuin muuallakin tässä projektissa.
        if not os.path.exists(ulos):
            raise SystemExit(f"mscore ei kirjoittanut vientiä tiedostosta {mxl}")
        return ET.parse(ulos).getroot()


def sivualut(root):
    """Niiden tahtien indeksit, joista uusi sivu alkaa. Ensimmäinen on 0."""
    part = root.find("part")
    alut = [0]
    for i, m in enumerate(part.findall("measure")):
        if any(pr.get("new-page") == "yes" for pr in m.findall("print")):
            alut.append(i)
    return sorted(set(alut))


def poista_otsikot(part):
    """Poista tämän työkalun aiemmin lisäämät otsikot."""
    poistettu = 0
    for m in part.findall("measure"):
        for d in list(m.findall("direction")):
            for w in d.findall("direction-type/words"):
                if (w.get("id") or "").startswith(TUNNISTE):
                    m.remove(d)
                    poistettu += 1
                    break
    return poistettu


def osittain(part):
    """Tahdin indeksi -> voimassa oleva osan otsikko.

    Osanvaihdos tunnistetaan `yhdista.OSAOTSIKOT`-listan tarkasta tekstistä
    eikä fontista: lähteissä on omia lihavoituja ohjetekstejä ("Alle",
    "4 soli"), jotka fonttihaku poimisi osanvaihdoksiksi. Löytynyt jono
    tarkistetaan koko listaa vasten, joten jos tunnistus joskus menee
    rikki, ajo pysähtyy sen sijaan että otsikot menisivät väärin.
    """
    odotetut = yhdista.OSAOTSIKOT
    nykyinen, tulos, loydetyt = None, [], []
    for m in part.findall("measure"):
        for w in m.findall("direction/direction-type/words"):
            if w.text in odotetut:
                nykyinen = w.text
                loydetyt.append(w.text)
        tulos.append(nykyinen)
    if loydetyt != odotetut:
        raise SystemExit(
            "osaotsikoita ei tunnistettu odotetussa järjestyksessä:\n"
            f"  löytyi:    {loydetyt}\n  odotettiin: {odotetut}")
    return tulos


def otsikko_direction(teksti, n):
    """Kursiivi pikkuotsikko sivun ensimmäisen tahdin päälle."""
    d = ET.Element("direction", {"placement": "above"})
    dt = ET.SubElement(d, "direction-type")
    w = ET.SubElement(dt, "words", {"id": f"{TUNNISTE}{n}",
                                    "font-size": "9",
                                    "font-style": "italic"})
    w.text = teksti
    return d


def lisaa_otsikot(part, alut):
    """Kirjoita otsikko joka sivualkuun. Palauta (lisätyt, ohitetut)."""
    ms = part.findall("measure")
    nimet = osittain(part)
    lisatty = ohitettu = 0
    for j, i in enumerate(alut, 1):
        m = ms[i]
        if any(w.text in yhdista.OSAOTSIKOT
               for w in m.findall("direction/direction-type/words")):
            # Osa alkaa juuri tästä tahdista, joten iso otsikko on jo
            # paikallaan eikä sen viereen tarvita toistoa.
            ohitettu += 1
            continue
        if nimet[i] is None:
            ohitettu += 1
            continue
        # Otsikko sijoitetaan tahdin alkuun, mutta <print> ja <attributes>
        # ovat MusicXML:ssä ennen muita alkioita.
        kohta = 0
        for k, lapsi in enumerate(m):
            if lapsi.tag in ("print", "attributes"):
                kohta = k + 1
        m.insert(kohta, otsikko_direction(nimet[i], j))
        lisatty += 1
    return lisatty, ohitettu


def kasittele(mxl):
    root = load(mxl)
    parts = root.findall("part")
    if len(parts) != 1:
        raise SystemExit(f"{mxl}: sivuotsikot vain yksiviivastoiseen "
                         f"stemmaan, tässä on {len(parts)} viivastoa")
    part = parts[0]
    if poista_otsikot(part):
        save(root, mxl, mxl)

    alut = sivualut(vie_asettelu(mxl))
    for kierros in range(1, KIERROSRAJA + 1):
        poista_otsikot(part)
        lisatty, ohitettu = lisaa_otsikot(part, alut)
        save(root, mxl, mxl)
        uudet = sivualut(vie_asettelu(mxl))
        if uudet == alut:
            print(f"{mxl}: {len(alut)} sivua, {lisatty} otsikkoa "
                  f"({ohitettu} ohitettu, osa alkaa sivun ensimmäisestä "
                  f"tahdista)")
            return
        print(f"{mxl}: otsikot siirsivät sivunvaihdot, kierros {kierros}")
        alut = uudet
    raise SystemExit(f"{mxl}: sivunvaihdot eivät vakiintuneet "
                     f"{KIERROSRAJA} kierroksella")


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    for mxl in argv:
        kasittele(mxl)


if __name__ == "__main__":
    main(sys.argv[1:])
