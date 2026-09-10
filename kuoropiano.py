#!/usr/bin/env python3
"""Pianoriisu kuoron omasta MuseScore-tiedostosta osan I pianoviivastolle.

**Miksi tämä on olemassa.** Osassa I ei ole ollut pianoa lainkaan. Sitä on
lähteessä — konelukema tuotti osastoon `P17` 1912 nuottia — mutta osasto on
jätetty `yhdista.py`:n `MAPPING`ista pois, koska MuseScoren moottori kaatuu
siihen (`Spanner::setTick2`, `ChordLayout::placeDots`) ja soitto pysähtyi
tahtiin 81. Kuoron oma MuseScore-tiedosto sisältää saman pianoriisun käsin
kirjoitettuna, joten tämä skripti korvaa koko osaston sillä. Se ei siis täytä
tyhjiötä vaan **korvaa tunnetusti rikkinäisen osaston**, ja kaatumista
aiheuttava sisältö katoaa kokonaan.

**Kartoitus, ja miksi se on todistettu eikä arvattu.** Kuoron tiedostot ovat
kuoron oma tiivistetty leikkaus, joten niiden tahdit eivät vastaa meidän
tahteja läpi osan. Kartoitus mitattiin 2026-09-10 kahdella toisistaan
riippumattomalla tavalla, jotka antoivat saman vastauksen:

  1. **Kuoroäänet.** Tahdin tunniste on kaikkien neljän kuoroäänen sisältö
     puolisävelaskeleina, joten kaksi tahtia vastaavat toisiaan vain jos
     kaikki neljä ääntä ovat samaa mieltä. Osumia 59 siirtymällä 0 ja 23
     siirtymällä +11.
  2. **Piano itse.** Konelukemamme piano on väärässä siellä täällä mutta
     tunnistaa tahdin: sen ja kuoron pianon sävelten Jaccard-osuvuus on
     lohkoittain 0,86-0,90, ja romahtaa nollaan heti lohkon rajalla.

Kuoron tiedosto merkitsee jokaisen leikkaussaumansa **tyhjällä
pianotahdilla**, ja se antoi rajat tahdin tarkkuudella: sen t.79 on tyhjä, ja
sitä ennen siirtymä on 0, sen jälkeen +11. Sauman selitys on, että kuoro
leikkasi pois meidän tahdit 79-89 — solistijakson, jossa kuoro on vaiti.

**Tahdit 29-55 ovat tyhjiä molemmissa tiedostoissa.** Piano ei siis vaikene
niissä kartoituksen takia: se ei yksinkertaisesti soita siellä (kuoron
a cappella -jakso). Aukkoa ei siis synny.

**Aukko syntyy tahdeissa 79-90 ja 139-140.** Kuoron tiedostossa ei ole niitä
lainkaan, joten ne jäävät tauoksi. Ne ovat juuri sitä solistijaksoa, jossa
piano soittaa ja jossa laulaja laskee taukoja, eli aukko on ikävässä
paikassa; se on kirjattu `TODO.md`:hen.

**Sävellajit täsmäävät, ja se on vahvistus meidän omille korjauksille.**
Kuoron piano vaihtaa sävellajin tahdeissa 17, 28, 56 ja 67 (3 ristiä, yksi b,
purku, 3 ristiä) — täsmälleen samoissa tahdeissa kuin meidän tiedostomme
niiden jälkeen kun sävellajin paikka korjattiin 2026-09-07 ja 2026-09-10.
Riippumattomasti käsin kirjoitettu tiedosto on siis samaa mieltä.

**Käsintehtyyn lähteeseen suhtaudutaan varauksella.** Kuoron tiedostot ovat
laulajien itsensä tekemiä, joten niiden johdonmukaisuutta ei oleteta vaan
tarkistetaan: jokaisen kirjoitetun tahdin jokaisen äänen kestojen summa
tarkistetaan tahdin omaa pituutta vasten, ja ajo kaatuu jos yksikin tahti ei
täyty täsmälleen. Osasta I mitattiin lisäksi, ettei siinä ole yhtään
oktaavieroa kahden lähteen välillä (osassa 10b niitä on kuusi, ja siksi sitä
ei kopioida tässä).

Lähdetiedosto `lahteet/01-kuoropiano.musicxml` on kuoron tiedostosta puristettu
pelkkä pianoviivasto; se on versionhallinnassa, jotta koko ketju on
toistettavissa ilman `.local/musescore/`-hakemistoa. Puristus itse:

    python3 kuoropiano.py --pura <mscore-vienti.musicxml> 01

Käyttö:  python3 kuoropiano.py [--kuiva]
"""

import copy
import math
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import polut
from korjaa_kasin import find_part, load, save

# Tahdin pituus jaotuksissa (divisions=12, 4/4) — osan I ainoa aikamerkintä.
TAHDIN_PITUUS = 48


@dataclass(frozen=True)
class Piano:
    """Yhden osan pianoviivaston korvaaminen kuoron tiedoston omalla."""

    mxl: str        # kohde, josta luetaan (korjaa_kasin.py:n tulos)
    out: str        # tulos, jonka yhdista.py lukee
    osasto: str     # pianon osasto kohdetiedostossa
    piano: str      # lahteet/-tiedosto, josta piano luetaan
    tahteja: int    # montako tahtia tuloksessa pitää olla
    jaksot: tuple   # ("kuoro", lo, hi) tai ("tauko", montako)


OSA_I = Piano(
    mxl="01-Verdi_Requiem-kasin.mxl",
    out="01-Verdi_Requiem-piano.mxl",
    osasto="P17",
    piano="01-kuoropiano.musicxml",
    tahteja=140,
    jaksot=(
        # Siirtymä 0: kuoron t.1-78 ovat meidän t.1-78. Näistä t.29-55 ovat
        # tyhjiä molemmissa, eli piano ei soita siellä.
        ("kuoro", 1, 78),
        # Meidän t.79-90: solistijakso, jonka kuoro leikkasi pois. Kuoron
        # oma sauman merkki on sen tyhjä t.79, joka jää tähän väliin
        # käyttämättä.
        ("tauko", 12),
        # Siirtymä +11: kuoron t.80-127 ovat meidän t.91-138.
        ("kuoro", 80, 127),
        # Meidän t.139-140: kuoron tiedosto loppuu tahtiin 127.
        ("tauko", 2),
    ),
)

PIANOT = (OSA_I,)


def lue_piano(nimi):
    """Lähdetiedoston ainoa osasto ja sen tahdit numeron mukaan."""
    root = ET.parse(polut.polku(nimi)).getroot()
    parts = root.findall("part")
    assert len(parts) == 1, f"{nimi}: odotettiin yhtä osastoa, on {len(parts)}"
    return {m.get("number"): m for m in parts[0].findall("measure")}


def tyhja_malli(tahdit):
    """Tyhjä tahti mallina: lähteen oma tyhjä tahti, ei käsin kyhätty.

    Tyhjän tahdin rakenne monen viivaston osastossa ei ole itsestään selvä
    (kokotahdin tauko per viivasto ja `backup` niiden väliin), joten se
    otetaan lähteestä eikä kirjoiteta itse.
    """
    for m in tahdit.values():
        if m.find("attributes") is not None or m.find("direction") is not None:
            continue
        notes = m.findall("note")
        if notes and all(n.find("rest") is not None for n in notes):
            return m
    raise AssertionError("lähteessä ei ole yhtään pelkkää tyhjää tahtia")


def siisti(measure):
    """Poista lähteen oma taitto ja asemointi; MuseScore laskee ne uudelleen.

    `<print>` kantaa kuoron tiedoston sivunvaihdot, jotka eivät liity meidän
    sivutukseen lainkaan, ja `default-x`/`default-y` on laskettu sen omalle
    sivuleveydelle.
    """
    for p in measure.findall("print"):
        measure.remove(p)
    measure.attrib.pop("width", None)
    for e in measure.iter():
        e.attrib.pop("default-x", None)
        e.attrib.pop("default-y", None)
        e.attrib.pop("relative-x", None)
        e.attrib.pop("relative-y", None)
    return measure


def kulje(measure):
    """Kulje tahdin läpi kursorilla ja palauta (ulottuma, nuottien loput).

    Kestoja ei voi laskea äänittäin yhteen: ääni voi tulla sisään kesken
    tahtia `<forward>`in takaa, jolloin sen nuottien summa on pienempi kuin
    tahdin pituus vaikka tahti on täysin kunnossa. Ensimmäinen versio tästä
    tarkistuksesta teki juuri sen virheen ja hylkäsi kuoron tiedoston tahdin
    12, jossa ääni 6 alkaa vasta toiselta iskulta.

    MusicXML kirjoittaa äänet peräkkäin ja siirtää kursoria `<backup>`- ja
    `<forward>`-alkioilla, joten oikea tapa on seurata kursoria.
    """
    kohta, ulottuma, loput = 0, 0, []
    for e in measure:
        if e.tag == "note":
            if e.find("chord") is not None:
                continue          # soinnun toinen sävel ei siirrä kursoria
            kohta += int(e.findtext("duration") or 0)
            loput.append((e.findtext("voice") or "1", kohta))
        elif e.tag == "backup":
            kohta -= int(e.findtext("duration") or 0)
        elif e.tag == "forward":
            kohta += int(e.findtext("duration") or 0)
        ulottuma = max(ulottuma, kohta)
    return ulottuma, loput


def tarkista(measure, numero, mista):
    """Kaadu jos tahti ei täyty täsmälleen.

    Tämä on se tarkistus, joka pitää käsintehtyä lähdettä kurissa. Kuoron
    tiedostot ovat laulajien itsensä tekemiä, joten niiden johdonmukaisuutta
    ei oleteta: jos jokin tahti on liian lyhyt tai pitkä, ajo pysähtyy sen
    sijaan että viallinen tahti menisi hiljaa partituuriin.
    """
    ulottuma, loput = kulje(measure)
    assert ulottuma == TAHDIN_PITUUS, (
        f"t.{numero} ({mista}): tahti ulottuu {ulottuma} jaotukseen, "
        f"pitäisi olla {TAHDIN_PITUUS}")
    for aani, loppu in loput:
        assert loppu <= TAHDIN_PITUUS, (
            f"t.{numero} ({mista}): ääni {aani} jatkuu {loppu} jaotukseen, "
            f"tahdin yli")


def jaotus(part):
    """Osaston divisions-arvot tahdeittain, alkaen ensimmäisestä ilmoituksesta."""
    ulos, d = {}, None
    for m in part.findall("measure"):
        t = m.findtext("attributes/divisions")
        if t:
            d = int(t)
        ulos[m.get("number")] = d
    return ulos


def yhtenaista_jaotus(root):
    """Kirjoita koko tiedosto yhdelle divisions-arvolle.

    **Miksi.** `yhdista.py` lukee osan `divisions`-arvon yhdestä
    viitaosastosta — siitä, jolla on eniten tahteja — ja käyttää sitä kaikille
    kohderiveille. Osassa 01 viitaosasto on lauluääni, jolla jaotus on 4,
    mutta kuoron piano käyttää arvoa 12. Silloin yhdistäjän itse tekemät
    kokotahdin tauot saavat keston 16 eikä 48, ja MuseScore pitää tahtia
    vääränmittaisena: `mscore` kieltäytyy koko partituurista ilman `-f`:ää.
    Tämä löytyi juuri niin — puolittamalla, ja ensimmäinen kuoron tahti
    riitti kaatamaan sen.

    Kohdearvo on kaikkien ilmoitettujen arvojen pienin yhteinen jaettava,
    joten skaalaus on aina kokonaisluku. Osassa 01 arvot ovat 4 ja 12, joten
    kohde on 12 ja kertoimet 3 ja 1.
    """
    arvot = set()
    for part in root.findall("part"):
        arvot.update(v for v in jaotus(part).values() if v)
    kohde = 1
    for v in arvot:
        kohde = kohde * v // math.gcd(kohde, v)

    muutettu = 0
    for part in root.findall("part"):
        d = None
        for m in part.findall("measure"):
            attrs = m.find("attributes")
            if attrs is not None and attrs.findtext("divisions"):
                d = int(attrs.findtext("divisions"))
                attrs.find("divisions").text = str(kohde)
            assert d, f"t.{m.get('number')}: divisions puuttuu"
            kerroin = kohde // d
            assert kerroin * d == kohde, "jaotus ei ole tasajaollinen"
            if kerroin == 1:
                continue
            for e in list(m.iter("duration")):
                e.text = str(int(e.text) * kerroin)
                muutettu += 1
    return kohde, muutettu


def sovella(piano):
    """Rakenna kohdeosaston tahdit uudelleen ja palauta seloste."""
    root = load(piano.mxl)
    part = find_part(root, piano.osasto)
    vanhat = part.findall("measure")
    assert len(vanhat) == piano.tahteja, (
        f"{piano.osasto}: {len(vanhat)} tahtia, odotettiin {piano.tahteja}")

    lahde = lue_piano(piano.piano)
    malli = tyhja_malli(lahde)

    uudet, kuoroista, tauoista = [], 0, 0
    for jakso in piano.jaksot:
        if jakso[0] == "kuoro":
            _, lo, hi = jakso
            for n in range(lo, hi + 1):
                m = lahde.get(str(n))
                assert m is not None, f"lähteessä ei ole tahtia {n}"
                uudet.append(siisti(copy.deepcopy(m)))
                tarkista(uudet[-1], n, "kuoron tiedosto")
                kuoroista += 1
        elif jakso[0] == "tauko":
            for _ in range(jakso[1]):
                uudet.append(siisti(copy.deepcopy(malli)))
                tauoista += 1
        else:
            raise AssertionError(f"tuntematon jakso {jakso[0]}")

    assert len(uudet) == piano.tahteja, (
        f"jaksot antavat {len(uudet)} tahtia, odotettiin {piano.tahteja}")

    # Tahtinumerot ovat kohteen omat, eivät lähteen.
    for m, vanha in zip(uudet, vanhat):
        m.set("number", vanha.get("number"))

    for m in vanhat:
        part.remove(m)
    for m in uudet:
        part.append(m)

    kohde, muutettu = yhtenaista_jaotus(root)

    return root, (f"{piano.osasto}: {kuoroista} tahtia kuoron tiedostosta, "
                  f"{tauoista} tauoksi; jaotus yhtenäistetty arvoon {kohde} "
                  f"({muutettu} kestoa skaalattu)")


def main(argv):
    if "--pura" in argv:
        i = argv.index("--pura")
        pura(argv[i + 1], argv[i + 2])
        return
    dry = "--kuiva" in argv
    for piano in PIANOT:
        root, seloste = sovella(piano)
        print(f"{piano.mxl} + {piano.piano} -> {piano.out}")
        print("  " + seloste)
        if dry:
            print("  (kuiva ajo, mitään ei kirjoitettu)")
        else:
            save(root, piano.mxl, piano.out)
            print(f"  kirjoitettu {piano.out}")


def pura(vienti, osa):
    """Puristа mscore-viennistä pelkkä pianoviivasto lähdetiedostoksi.

    Tämä ajetaan kertaluonteisesti ja vaatii `.local/musescore/`-hakemiston,
    jota ei ole versionhallinnassa. Tulos on, ja siksi koko muu ketju toimii
    ilman sitä.
    """
    root = ET.parse(vienti).getroot()
    nimet = {p.get("id"): (p.findtext("part-name") or "").strip()
             for p in root.findall("part-list/score-part")}
    pid = next(p for p, n in nimet.items() if n == "Piano")

    uusi = ET.Element("score-partwise", {"version": "4.0"})
    ident = ET.SubElement(uusi, "identification")
    ET.SubElement(ident, "rights").text = (
        "Kuoron oma MuseScore-harjoitustiedosto; tekijä tuntematon. "
        "Puristettu pelkäksi pianoviivastoksi.")
    enc = ET.SubElement(ident, "encoding")
    ET.SubElement(enc, "software").text = "kuoropiano.py --pura"
    plist = ET.SubElement(uusi, "part-list")
    sp = ET.SubElement(plist, "score-part", {"id": "P1"})
    ET.SubElement(sp, "part-name").text = "Piano"
    osasto = copy.deepcopy(next(p for p in root.findall("part")
                                if p.get("id") == pid))
    osasto.set("id", "P1")
    uusi.append(osasto)
    ulos = polut.polku(f"{osa}-kuoropiano.musicxml")
    ET.indent(uusi, space="  ")
    ET.ElementTree(uusi).write(ulos, encoding="UTF-8", xml_declaration=True)
    print(f"kirjoitettu {ulos} "
          f"({len(osasto.findall('measure'))} tahtia)")


if __name__ == "__main__":
    main(sys.argv[1:])
