#!/usr/bin/env python3
"""Merkitse stemmaan päivä, jona sen sisältö viimeksi muuttui.

Laulaja lataa stemman lukulaitteelleen ja kysyy puolen vuoden päästä, onko
hänellä uusin. Päiväys vastaa siihen kahdessa paikassa yhdestä lähteestä:
PDF:n ensimmäisen sivun vasemmassa ylälaidassa pienellä, ja sivustolla
latauslinkin alla. Sivusto lukee saman merkinnän `.mxl`-tiedostosta
(`lue`), joten sivu ei voi näyttää eri päivää kuin PDF.

    python3 paivays.py stemma-basso-1.mxl
    python3 paivays.py stemma-*.mxl

Ajetaan `sivuotsikot.py`:n jälkeen ja **viimeisenä ennen PDF:n tekoa**:
päivä kertoo siitä tiedostosta, joka renderöidään.

## Miksi päivä ei ole rakennuspäivä

`yhdista.py` kirjoittaa kaikki kahdeksan stemmaa alusta uusiksi joka
ajolla, joten "milloin tämä tiedosto rakennettiin" olisi jokaisessa
stemmassa tämä päivä myös silloin, kun kyseinen ääni ei ole muuttunut
kuukauteen. Se on juuri se kysymys johon päiväyksen pitäisi vastata, joten
päivä päätellään sisällöstä: uusi tiedosto verrataan gitin HEAD-versioon
päiväysmerkintä molemmista riisuttuna, ja jos ne ovat samat, vanha päivä
säilyy. Muuttunut stemma saa tämän päivän. Sivutuotteena uudelleenajo ei
tuota diffiä tiedostoon, jonka sisältö ei muuttunut.

Ilman gitiä (tai kun tiedosto ei ole vielä versionhallinnassa) merkitään
tämä päivä. Se on ainoa mitä silloin tiedetään.

## Miksi teksti on `<credit>` eikä `<direction>`

Sivun ylälaita ei kuulu millekään tahdille, ja `<credit>` on MusicXML:n
oma tapa sijoittaa tekstiä sivulle. Mitattu MuseScore 4.7.4:llä:

* `<credit-type>lyricist</credit-type>` kunnioittaa annettua
  `default-x`/`default-y`-paikkaa. Tyypitön credit ei: se ladottiin
  säveltäjän nimen päälle sivun oikeaan ylälaitaan.
* **Yksikin credit tiedostossa lopettaa otsikon ja säveltäjän johtamisen**
  `movement-title`- ja `creator`-alkioista — pelkän päiväyksen lisääminen
  siis pyyhki stemman otsikon sivulta. Siksi nekin kirjoitetaan
  crediteiksi, mutta ei käsin kirjoitetuin koordinaatein vaan
  **MuseScoren omasta viennistä poimittuina**: paikat tulevat silloin
  käytössä olevasta tyylistä eivätkä tämän tiedoston vakioista.
* Sivunvaihdot ja sivumäärä eivät muutu — credit on absoluuttisesti
  sijoitettu eikä vie tilaa nuotilta. Mitattu vertaamalla `new-page`
  -tahteja ennen ja jälkeen.

Poiminta vaatii, että vienti tehdään tiedostosta **ilman** omia
crediteitämme: kun ne ovat jo paikallaan, MuseScore vie ne takaisin eri
koordinaatein kuin millä se ne latoi. Siksi vanhat merkinnät poistetaan
ennen vientiä, ja uudelleenajo on turvallista.
"""

import copy
import datetime
import io
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

import polut
import sivuotsikot
from korjaa_sanat import load, save

# <credit-words id="paivays…">, jotta omat merkinnät löytyvät ja lähtevät
# pois. Kaikki tämän työkalun lisäämät creditit merkitään, myös viennistä
# poimitut otsikko ja säveltäjä: ne ovat yhtä lailla tämän jälki.
TUNNISTE = "paivays"
FONTTIKOKO = "7"
TEKSTI = "Päivitetty %s"


# ------------------------------------------------------------------ päivä

def suomeksi(iso):
    """2026-09-10 -> 10.9.2026."""
    v, k, p = (int(x) for x in iso.split("-"))
    return "%d.%d.%d" % (p, k, v)


def lue_root(root):
    """Puuhun merkitty päivä ISO-muodossa, tai None."""
    alkio = root.find("identification/encoding/encoding-date")
    return alkio.text if alkio is not None and alkio.text else None


def lue(mxl):
    """Tiedostoon merkitty päivä ISO-muodossa, tai None jos merkintää ei ole.

    Tämä on se, mitä sivusto lukee. Merkinnän paikka on MusicXML:n oma
    `encoding-date` eikä näkyvä teksti: sivun ei tarvitse jäsentää
    suomenkielistä päiväystä takaisin luvuiksi.
    """
    return lue_root(load(mxl))


# --------------------------------------------------------------- riisunta

def riisu(root):
    """Poista tämän työkalun merkinnät. Palauta poistettu päivä tai None."""
    for credit in list(root.findall("credit")):
        if any((w.get("id") or "").startswith(TUNNISTE)
               for w in credit.iter("credit-words")):
            root.remove(credit)
    paiva = None
    enc = root.find("identification/encoding")
    if enc is not None:
        for pvm in enc.findall("encoding-date"):
            paiva = pvm.text
            enc.remove(pvm)
        if not list(enc):
            root.find("identification").remove(enc)
    return paiva


def runko(root):
    """Puun sisältö ilman päiväysmerkintää, vertailukelpoisena tavujonona."""
    kopio = copy.deepcopy(root)
    riisu(kopio)
    return ET.tostring(kopio, encoding="UTF-8")


# ------------------------------------------------------------------- git

def gitin_versio(mxl):
    """HEAD:n versio stemmasta puuna, tai None jos sitä ei saa luettua.

    Kaikki virheet — ei gitiä, ei repoa, tiedosto ei vielä
    versionhallinnassa, rikkinäinen zip — johtavat samaan: vertailukohtaa
    ei ole, joten päiväksi tulee tämä päivä.
    """
    kohde = polut.polku(mxl).replace(os.sep, "/")
    try:
        ajo = subprocess.run(["git", "show", "HEAD:" + kohde],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return None
    if ajo.returncode != 0 or not ajo.stdout:
        return None
    try:
        with zipfile.ZipFile(io.BytesIO(ajo.stdout)) as z:
            nimi = next(n for n in z.namelist()
                        if not n.startswith("META-INF")
                        and n.lower().endswith(".xml"))
            return ET.fromstring(z.read(nimi))
    except (zipfile.BadZipFile, StopIteration, ET.ParseError):
        return None


def paatele_paiva(mxl, root, tanaan):
    """Vanha päivä jos sisältö on ennallaan, muuten tämä päivä."""
    vanha = gitin_versio(mxl)
    if vanha is None:
        return tanaan
    merkitty = lue_root(vanha)
    if merkitty and runko(vanha) == runko(root):
        return merkitty
    return tanaan


# --------------------------------------------------------------- creditit

def sijainti(vienti):
    """Päiväyksen paikka: vasen marginaali otsikon yläreunan korkeudella.

    Molemmat luetaan MuseScoren viennistä, jotta ne seuraavat tyyliä eivätkä
    jää tähän vakioiksi.
    """
    # Ensimmäinen sivu on pariton. Vertailu None:een on tässä pakollinen:
    # lapseton alkio on ElementTreessä epätosi, joten `a or b` ottaisi aina
    # jälkimmäisen.
    vasen = vienti.find("defaults/page-layout/"
                        "page-margins[@type='odd']/left-margin")
    if vasen is None:
        vasen = vienti.find("defaults/page-layout/page-margins/left-margin")
    ylareunat = [float(w.get("default-y")) for w in vienti.iter("credit-words")
                 if w.get("default-y")]
    if vasen is None or not ylareunat:
        raise SystemExit("MuseScoren vienti ei kerro sivun marginaalia tai "
                         "otsikon paikkaa — päiväystä ei voi sijoittaa")
    return vasen.text, max(ylareunat)


def paivays_credit(vienti, iso):
    """Pieni päiväys ensimmäisen sivun vasempaan ylälaitaan."""
    vasen, ylin = sijainti(vienti)
    credit = ET.Element("credit", {"page": "1"})
    # lyricist on ainoa tyyppi, jolla MuseScore latoi tekstin annettuun
    # paikkaan; ks. moduulin dokumentaatio.
    ET.SubElement(credit, "credit-type").text = "lyricist"
    sanat = ET.SubElement(credit, "credit-words", {
        "id": TUNNISTE,
        "default-x": vasen,
        "default-y": "%g" % ylin,
        "justify": "left",
        "valign": "top",
        "font-size": FONTTIKOKO})
    sanat.text = TEKSTI % suomeksi(iso)
    return credit


def lisaa_creditit(root, vienti, iso):
    """Kirjoita viennin otsikkocreditit takaisin ja päiväys niiden viereen."""
    otsikot = vienti.findall("credit")
    if not otsikot:
        raise SystemExit("MuseScoren vienti ei sisältänyt yhtään credittiä — "
                         "päiväys pyyhkisi stemman otsikon sivulta")
    for n, credit in enumerate(otsikot, 1):
        for sanat in credit.iter("credit-words"):
            sanat.set("id", "%s-otsikko%d" % (TUNNISTE, n))
    # MusicXML:n järjestys on … identification, defaults, credit*, part-list.
    kohta = list(root).index(root.find("part-list"))
    for credit in [*otsikot, paivays_credit(vienti, iso)]:
        root.insert(kohta, credit)
        kohta += 1


def merkitse_paiva(root, iso):
    """encoding-date identification-alkioon, sivustoa varten."""
    ident = root.find("identification")
    if ident is None:
        raise SystemExit("stemmasta puuttuu identification-alkio")
    enc = ident.find("encoding")
    if enc is None:
        enc = ET.SubElement(ident, "encoding")
    ET.SubElement(enc, "encoding-date").text = iso


# ------------------------------------------------------------------- ajo

def kasittele(mxl, tanaan=None):
    tanaan = tanaan or datetime.date.today().isoformat()
    root = load(mxl)
    if riisu(root) is not None:
        # Vienti on tehtävä puhtaasta tiedostosta, muuten MuseScore antaa
        # crediteille eri koordinaatit kuin millä se ne latoi.
        save(root, mxl, mxl)
    iso = paatele_paiva(mxl, root, tanaan)
    lisaa_creditit(root, sivuotsikot.vie_asettelu(mxl), iso)
    merkitse_paiva(root, iso)
    save(root, mxl, mxl)
    print("%s: %s%s" % (mxl, suomeksi(iso),
                        "" if iso == tanaan else " (sisältö ennallaan)"))
    return iso


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    for mxl in argv:
        kasittele(mxl)


if __name__ == "__main__":
    main(sys.argv[1:])
