#!/usr/bin/env python3
"""Rakenna verkkosivusto stemmoista, teksteistä ja luotettavuustaulukosta.

Sivuston tiedot luetaan samoista vakioista, jotka ohjaavat stemmojen
tuotantoa (yhdista.MOVEMENTS, luotettavuus.POIKKEUKSET) ja valmiista
tuotoksista (stemmat-sisallys.txt, yhdistetty partituuri), joten sisällys ei
voi ajautua stemmoista erilleen.

Käyttö:  python3 sivusto.py [_sivusto]

Tulos ei ole versionhallinnassa: CI rakentaa julkaistavan version samalla
komennolla. Näin sivusto ei voi vanhentua huomaamatta.
"""

import html as _html
import os
import re
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET

import luotettavuus
import polut
import yhdista

POHJA = "sivusto"

# Oma verkkotunnus. GitHub Pages lukee sen julkaistavasta hakemistosta, joten
# tiedosto kirjoitetaan tuotokseen eikä pelkästään Pagesin asetuksiin — näin
# se ei katoa jos asetukset nollautuvat. Vaatii DNS:ään CNAME-tietueen, joka
# osoittaa tuomas2.github.io:hon.
VERKKOTUNNUS = "requiem.tuomasairaksinen.fi"

NAVI = [("index.html", "Etusivu"),
        ("teksti.html", "Teksti"),
        ("stemmat.html", "Stemmat"),
        ("luotettavuus.html", "Luotettavuus")]

STEMMAT = [("S I", "stemma-sopraano-1.pdf"), ("S II", "stemma-sopraano-2.pdf"),
           ("A I", "stemma-altto-1.pdf"), ("A II", "stemma-altto-2.pdf"),
           ("T I", "stemma-tenori-1.pdf"), ("T II", "stemma-tenori-2.pdf"),
           ("B I", "stemma-basso-1.pdf"), ("B II", "stemma-basso-2.pdf")]

FONTIT = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
          '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
          '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
          'family=EB+Garamond:ital,wght@0,400;0,500&family=Archivo:wght@400;600'
          '&display=swap">')


def e(teksti):
    return _html.escape(str(teksti))


def sivu(otsikko, sisalto, aktiivinen):
    """Kokonainen HTML-sivu yhteisellä navigaatiolla."""
    linkit = "".join(
        '<a href="%s"%s>%s</a>'
        % (tiedosto, ' aria-current="page"' if tiedosto == aktiivinen else "",
           e(nimi))
        for tiedosto, nimi in NAVI)
    return f"""<!DOCTYPE html>
<html lang="fi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(otsikko)} — Verdi: Messa da Requiem</title>
{FONTIT}
<link rel="stylesheet" href="tyyli.css">
</head>
<body>
<nav class="bar"><div class="bar-inner">{linkit}</div></nav>
<div class="wrap">
{sisalto}
</div>
</body>
</html>
"""


# ------------------------------------------------------------------ etusivu

def etusivu():
    sisalto = """
<h1>Messa da Requiem</h1>
<p class="johdanto">Verdin <em>Messa da Requiem</em>: kuusitoista erillistä
osatiedostoa yhdistettynä yhdeksi partituuriksi, ja siitä tuotetut kahdeksan
kuorostemmaa harjoittelua varten.</p>

<p>Lähtökohta on kuorolaisen käytännön tarve: lukea omaa stemmaa niin että muu
kuoro ja pianosäestys kuuluvat, kantaa stemma mukana lukulaitteella, ja löytää
yksittäinen tahti kun kuoronjohtaja huutaa numeron. Siitä seuraa kaksi
vaatimusta: tahtinumeroiden on täsmättävä kuoron oman nuottikirjan kanssa, ja
stemman on oltava tiivis.</p>

<h2>Mistä aloittaa</h2>
<ul>
<li><a href="stemmat.html">Stemmat</a> — kahdeksan ääntä ladattavina, ja
mistä sivulta mikin osa alkaa</li>
<li><a href="teksti.html">Teksti</a> — koko messun latinankielinen teksti ja
suomennos rinnakkain</li>
<li><a href="luotettavuus.html">Luotettavuus</a> — mikä on tarkistettu ja
mikä ei. <strong>Lue tämä ennen kuin luotat nuottiin</strong></li>
</ul>

<h2>Aineiston alkuperä</h2>
<p>Sävellys on public domainissa; Verdi kuoli 1901. Nuottiaineisto on
CPDL:n (Choral Public Domain Library) editioita, jotka saa vapaasti levittää
ja esittää. Skriptit ja dokumentaatio ovat GPL-3.0-lisenssin alaisia.</p>
<p>Lähdekoodi, koko työn dokumentaatio ja ohjeet aineiston uudelleenluontiin:
<a href="https://github.com/tuomas2/verdi-requiem">github.com/tuomas2/verdi-requiem</a>.</p>
"""
    return sivu("Etusivu", sisalto, "index.html")


# ----------------------------------------------------------- luotettavuus

def luotettavuussivu():
    rivit = []
    for numero, otsikko, tilat in luotettavuus.taulukko():
        solut = "".join('<td class="merkki" title="%s">%s</td>'
                        % (e(t.nimi), t.merkki) for t in tilat)
        rivit.append("<tr><td><strong>%s</strong> %s</td>%s</tr>"
                     % (e(numero), e(otsikko), solut))
        # Perustelut vain siellä missä on jotain kerrottavaa: oletustila ja
        # solistiosat eivät ansaitse omaa riviään.
        huomiot = []
        for aani, t in zip(luotettavuus.AANET, tilat):
            if t.nimi in ("tarkistamatta", "ei kuoroa") and t.perustelu in (
                    luotettavuus.TARKISTAMATTA.perustelu,
                    luotettavuus.EI_KUOROA.perustelu):
                continue
            lyhenne = aani.replace("Kuoro ", "")
            if (lyhenne, t.perustelu) not in [(l, p) for l, p in huomiot]:
                huomiot.append((lyhenne, t.perustelu))
        # Sama perustelu usealla äänellä kootaan yhdeksi maininnaksi.
        koottu = []
        for lyhenne, perustelu in huomiot:
            if koottu and koottu[-1][1] == perustelu:
                koottu[-1][0].append(lyhenne)
            else:
                koottu.append(([lyhenne], perustelu))
        if koottu:
            teksti = " ".join("<strong>%s:</strong> %s"
                              % (e("/".join(lyhenteet)), e(perustelu))
                              for lyhenteet, perustelu in koottu)
            rivit.append('<tr class="selite"><td colspan="5" '
                         'class="perustelu">%s</td></tr>' % teksti)

    otsikot = "".join('<th class="merkki">%s</th>' % e(a.replace("Kuoro ", ""))
                      for a in luotettavuus.AANET)
    sisalto = f"""
<h1>Luotettavuus</h1>
<p class="johdanto">Vain <strong>kuorobasso</strong> on käyty
järjestelmällisesti läpi. Sopraano, altto ja tenori ovat pääosin
tarkistamatta, ja kahdessa osassa niissä on tiedettyjä virheitä.</p>

<p>Syy on yksinkertainen: tekijä laulaa bassoa, ja käytännössä jokainen virhe
on löytynyt joko laulamalla mukana harjoituksissa tai vertaamalla juuri sitä
riviä riippumattomaan lähteeseen.</p>

<p>Kaksi asiaa toistui tarkistustyössä. <strong>Painettu nuotti ei ratkaise
kaikkea:</strong> Lacrymosan tahdeissa 657–665 painettu CPDL-editio antaa
kuorobassolle väärän tekstin ja tahdissa 653 väärän sävelen, ja kumpikin
paljastui vasta siitä mitä muut äänet ja pianosäestys tekevät samalla
iskulla. <strong>Konelukemisen tulos on eri luokkaa kuin muu aineisto:</strong>
osat I ja V sekä II·9b on luettu koneellisesti PDF:stä, ja niiden nuotit ovat
pääosin tarkistamatta.</p>

<div class="vieritin">
<table>
<thead><tr><th>Osa</th>{otsikot}</tr></thead>
<tbody>{''.join(rivit)}</tbody>
</table>
</div>
<p class="selitteet">✔ varmistettu — vertailtu riippumattomaan lähteeseen
nuotti nuotilta tai tavu tavulta · ◑ osittain — esimerkiksi sanat tarkistettu,
nuotit eivät · ○ tarkistamatta — ei tunnettuja virheitä, mutta ei myöskään
tarkistettu · ⚠ puutteita — tiedetään virheellistä sisältöä · – osassa ei ole
kuoroa</p>
"""
    return sivu("Luotettavuus", sisalto, "luotettavuus.html")


# --------------------------------------------------------------- stemmat

def lue_sisallys():
    """(osanumero, otsikko, [8 sivunumeroa]) stemmat-sisallys.txt:stä.

    Tiedosto on sarakemuotoinen ja osanumero voi olla kiinni otsikossa
    ("II·9bDies irae (kertaus)", koska numerolle on varattu tasan viisi
    merkkiä), joten rivi puretaan tunnettuja osia vasten eikä välilyönneillä.
    """
    with open(polut.polku("stemmat-sisallys.txt"), encoding="utf-8") as f:
        teksti = f.read()
    rivit = []
    for _tiedosto, numero, otsikko in yhdista.MOVEMENTS:
        kuvio = re.compile(r"^\s*%s\s*%s\s+((?:\d+\s+){7}\d+)\s*$"
                           % (re.escape(numero), re.escape(otsikko)),
                           re.MULTILINE)
        osuma = kuvio.search(teksti)
        if not osuma:
            raise SystemExit(
                f"stemmat-sisallys.txt: riviä osalle {numero} {otsikko} ei "
                f"löydy — aja python3 sisallys.py uudelleen")
        rivit.append((numero, otsikko,
                      [int(x) for x in osuma.group(1).split()]))
    return rivit


def tahtivalit():
    """Osanumero -> (ensimmäinen, viimeinen) tahtinumero.

    Luetaan yhdistetyn partituurin omista <measure number> -arvoista eikä
    siitä taulukosta joka ne asetti — sama tarkistustapa kuin muualla
    projektissa. Osanvaihdos tunnistetaan osaotsikosta, joka on kirjoitettu
    osan ensimmäisen tahdin päälle.
    """
    with zipfile.ZipFile(polut.polku("Verdi-Requiem-koko.mxl")) as z:
        nimi = next(n for n in z.namelist()
                    if not n.startswith("META-INF")
                    and n.lower().endswith(".xml"))
        juuri = ET.fromstring(z.read(nimi))

    otsikosta_numeroon = {yhdista.osaotsikko(numero, otsikko): numero
                          for _t, numero, otsikko in yhdista.MOVEMENTS}
    valit = {}
    for osa in juuri.findall("part"):
        nykyinen = None
        for tahti in osa.findall("measure"):
            for sanat in tahti.iter("words"):
                teksti = (sanat.text or "").strip()
                if teksti in otsikosta_numeroon:
                    nykyinen = otsikosta_numeroon[teksti]
            if nykyinen is None:
                continue
            try:
                numero = int(tahti.get("number"))
            except (TypeError, ValueError):
                continue
            alku, loppu = valit.get(nykyinen, (numero, numero))
            valit[nykyinen] = (min(alku, numero), max(loppu, numero))
    return valit


def stemmasivu():
    sisallys = lue_sisallys()
    valit = tahtivalit()
    pikkukuvat = os.path.isdir(os.path.join(POHJA, "pikkukuvat"))

    def lataus(nimi, pdf):
        kuva = ('<img src="pikkukuvat/%s.png" alt="" width="110" '
                'loading="lazy">' % pdf[:-4]) if pikkukuvat else ""
        return ('<li><a href="stemmat/%s">%s<span>%s</span></a></li>'
                % (pdf, kuva, e(nimi)))

    linkit = "".join(lataus(nimi, pdf) for nimi, pdf in STEMMAT)
    otsikot = "".join('<th class="luku">%s</th>' % e(nimi)
                      for nimi, _pdf in STEMMAT)
    rivit = []
    for numero, otsikko, sivut in sisallys:
        alku, loppu = valit.get(numero, ("", ""))
        rivit.append(
            '<tr><td><strong>%s</strong> %s</td><td class="luku">%s–%s</td>%s</tr>'
            % (e(numero), e(otsikko), e(alku), e(loppu),
               "".join('<td class="luku">%d</td>' % s for s in sivut)))

    sisalto = f"""
<h1>Stemmat</h1>
<p class="johdanto">Kahdeksan kuorostemmaa. Jokaisen tahdin päällä on
tahtinumero ja jokaisen sivun yläreunassa käynnissä olevan osan nimi, jotta
yksittäisen tahdin löytää kuoronjohtajan huudosta.</p>

<ul class="lataukset">{linkit}</ul>

<h2>Mistä osa alkaa</h2>
<p>Tahtinumerot ovat kuoron oman nuottikirjan mukaiset. Dies irae eli osa II
numeroituu yhtenäisesti läpi kaikkien alaosiensa; muut osat alkavat
ykkösestä. Sivunumerot ovat kunkin stemman omassa PDF:ssä.</p>
<div class="vieritin">
<table>
<thead><tr><th>Osa</th><th class="luku">Tahdit</th>{otsikot}</tr></thead>
<tbody>{''.join(rivit)}</tbody>
</table>
</div>
"""
    return sivu("Stemmat", sisalto, "stemmat.html")


# ---------------------------------------------------------------- teksti

def tekstisivu():
    """requiem.html sellaisenaan, navigaatio lisättynä.

    Sivu on itsenäinen ja toimiva, joten siihen ei kosketa muuten. Navigaatio
    pujotetaan heti <body>:n jälkeen ja se saa tyylinsä mukanaan, koska sivu
    ei lataa jaettua tyylitiedostoa.
    """
    with open(os.path.join(POHJA, "requiem.html"), encoding="utf-8") as f:
        html = f.read()
    if "<body>" not in html:
        raise SystemExit("sivusto/requiem.html: <body>-tagia ei löydy")
    linkit = "".join(
        '<a href="%s" style="font-family:var(--sans);font-size:.68rem;'
        'font-weight:600;letter-spacing:.09em;text-transform:uppercase;'
        'text-decoration:none;color:var(--ink-soft);padding:.3rem .45rem">'
        '%s</a>' % (tiedosto, e(nimi))
        for tiedosto, nimi in NAVI if tiedosto != "teksti.html")
    navi = ('<nav class="bar" style="position:static">'
            '<div class="bar-inner"><div class="jump">%s</div></div></nav>'
            % linkit)
    return html.replace("<body>", "<body>\n" + navi, 1)


# -------------------------------------------------------------- rakennus

def rakenna(ulos="_sivusto"):
    os.makedirs(ulos, exist_ok=True)
    shutil.copy(os.path.join(POHJA, "tyyli.css"), ulos)

    for nimi, teksti in [("index.html", etusivu()),
                         ("luotettavuus.html", luotettavuussivu()),
                         ("stemmat.html", stemmasivu()),
                         ("teksti.html", tekstisivu())]:
        with open(os.path.join(ulos, nimi), "w", encoding="utf-8") as f:
            f.write(teksti)

    with open(os.path.join(ulos, "CNAME"), "w", encoding="utf-8") as f:
        f.write(VERKKOTUNNUS + "\n")

    kohde = os.path.join(ulos, "stemmat")
    os.makedirs(kohde, exist_ok=True)
    for _nimi, pdf in STEMMAT:
        shutil.copy(polut.polku(pdf), kohde)

    kuvat = os.path.join(POHJA, "pikkukuvat")
    if os.path.isdir(kuvat):
        kohde = os.path.join(ulos, "pikkukuvat")
        os.makedirs(kohde, exist_ok=True)
        for tiedosto in os.listdir(kuvat):
            shutil.copy(os.path.join(kuvat, tiedosto), kohde)
    return ulos


def main(argv):
    ulos = argv[0] if argv else "_sivusto"
    rakenna(ulos)
    print(f"kirjoitettu {ulos}/")


if __name__ == "__main__":
    main(sys.argv[1:])
