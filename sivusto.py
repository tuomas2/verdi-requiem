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

# Kaksi sivua riittää, ja stemmat on niistä se jota luetaan: se on etusivu.
NAVI = [("index.html", "Stemmat"),
        ("teksti.html", "Teksti")]

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


# ------------------------------------------------------------------ alaviite

def alaviite():
    """Teoksen ja aineiston tausta sivun lopussa.

    Oma etusivunsa tälle olisi väliporras, joka pitää klikata pois tieltä
    ennen kuin pääsee siihen mitä sivustolta haetaan.
    """
    return """
<h2>Mistä tämä on peräisin</h2>
<p>Sävellys on public domainissa; Verdi kuoli 1901. Nuottiaineisto on CPDL:n
(Choral Public Domain Library) editioita, jotka saa vapaasti levittää ja
esittää. Kuusitoista erillistä osatiedostoa on yhdistetty yhdeksi
partituuriksi, ja stemmat on tuotettu siitä. Tahtinumerointi on sovitettu
Edition Petersin painokseen, jota vasten kuorobasso on myös käyty läpi.</p>
<p>Lähtökohta on kuorolaisen käytännön tarve: lukea omaa stemmaa niin että muu
kuoro ja pianosäestys kuuluvat, kantaa stemma mukana lukulaitteella, ja löytää
yksittäinen tahti kun kuoronjohtaja huutaa numeron.</p>
<p>Lähdekoodi, koko työn dokumentaatio ja ohjeet aineiston uudelleenluontiin:
<a href="https://github.com/tuomas2/verdi-requiem">github.com/tuomas2/verdi-requiem</a>.
Skriptit ja dokumentaatio ovat GPL-3.0-lisenssin alaisia.</p>
"""


# ----------------------------------------------------------- luotettavuus

def luotettavuusvaroitus():
    """Kärkiteksti, joka luetaan ennen kuin stemma ladataan."""
    return """
<div class="varoitus">
<p><strong>Kuorobasso on käyty läpi, muut äänet eivät.</strong> Basso on
käyty läpi käsin <strong>Edition Petersin</strong> painosta vasten ja
laulettu läpi harjoituksissa, ja kahdessa osassa lisäksi vertailtu nuotti
nuotilta riippumattomaan lähteeseen. Sopraano, altto ja tenori ovat pääosin
tarkistamatta, ja kahdessa osassa niissä on tiedettyjä virheitä. Syy on
yksinkertainen: tekijä laulaa bassoa. Alla olevasta taulukosta näkee osa
osalta, mihin kunkin äänen kohdalla voi luottaa.</p>
</div>
"""


def luotettavuusselitteet():
    """Merkkien selitykset ja se, mitä tarkistustyö opetti."""
    return """
<p class="selitteet">✔ varmistettu — koko osa vertailtu riippumattomaan
lähteeseen nuotti nuotilta ja tavu tavulta · ◑ käyty läpi — käyty läpi käsin
painettua editiota vasten ja laulettu harjoituksissa, mutta ei
järjestelmällisesti nuotti nuotilta · ○ tarkistamatta — ei tunnettuja
virheitä, mutta ei myöskään tarkistettu · ⚠ puutteita — tiedetään
virheellistä sisältöä · – osassa ei ole kuoroa</p>

<h2>Mitä tarkistustyö opetti</h2>
<p><strong>Painettu nuotti ei ratkaise kaikkea.</strong> Lacrymosan tahdeissa
657–665 painettu CPDL-editio antaa kuorobassolle väärän tekstin ja tahdissa
653 väärän sävelen. Kumpikin paljastui vasta siitä, mitä muut äänet ja
pianosäestys tekevät samalla iskulla. Painettu etumerkki kertoo varmasti minkä
nuotin kaivertaja piirsi — ei mitään siitä, oliko se oikea.</p>
<p><strong>Konelukemisen tulos on eri luokkaa kuin muu aineisto.</strong> Osat
I ja V sekä II·9b on luettu koneellisesti PDF:stä, ja niiden nuotit ovat
pääosin tarkistamatta.</p>
"""


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
    """Stemmat, sisällys ja luotettavuus yhtenä sivuna.

    Sivunumerot ovat stemmaa kohti (S I, S II, ...) ja luotettavuus ääntä
    kohti (S, A, T, B), eli kaksi stemmaa ääntä kohti. Ne yhdistyvät samaan
    soluun: koko teoksessa on tasan yksi kohta, jossa saman äänen kaksi
    stemmaa ovat eri sivuilla, joten toinen luku näytetään vain silloin.
    """
    sisallys = lue_sisallys()
    valit = tahtivalit()
    pikkukuvat = os.path.isdir(os.path.join(POHJA, "pikkukuvat"))

    def lataus(nimi, pdf):
        kuva = ('<img src="pikkukuvat/%s.png" alt="" width="110" '
                'loading="lazy">' % pdf[:-4]) if pikkukuvat else ""
        return ('<li><a href="stemmat/%s">%s<span>%s</span></a></li>'
                % (pdf, kuva, e(nimi)))

    linkit = "".join(lataus(nimi, pdf) for nimi, pdf in STEMMAT)
    otsikot = "".join('<th class="aani">%s</th>' % e(a.replace("Kuoro ", ""))
                      for a in luotettavuus.AANET)

    rivit = []
    for numero, otsikko, sivut in sisallys:
        alku_t, loppu_t = valit.get(numero, ("", ""))
        solut = []
        for i, aani in enumerate(luotettavuus.AANET):
            ensimmainen, toinen = sivut[2 * i], sivut[2 * i + 1]
            sivu_teksti = (str(ensimmainen) if ensimmainen == toinen
                           else "%d/%d" % (ensimmainen, toinen))
            t = luotettavuus.tila(numero, aani)
            solut.append('<td class="aani"><span class="sivu">%s</span>'
                         '<span class="merkki" title="%s">%s</span></td>'
                         % (e(sivu_teksti), e(t.nimi), t.merkki))
        rivit.append(
            '<tr><td><strong>%s</strong> %s</td><td class="luku">%s–%s</td>%s</tr>'
            % (e(numero), e(otsikko), e(alku_t), e(loppu_t), "".join(solut)))

        # Perustelu vain siellä missä on jotain kerrottavaa.
        huomiot = []
        for aani in luotettavuus.AANET:
            t = luotettavuus.tila(numero, aani)
            if t.perustelu in (luotettavuus.TARKISTAMATTA.perustelu,
                               luotettavuus.EI_KUOROA.perustelu):
                continue
            lyhenne = aani.replace("Kuoro ", "")
            if huomiot and huomiot[-1][1] == t.perustelu:
                huomiot[-1][0].append(lyhenne)
            else:
                huomiot.append(([lyhenne], t.perustelu))
        if huomiot:
            teksti = " ".join("<strong>%s:</strong> %s"
                              % (e("/".join(lyhenteet)), e(perustelu))
                              for lyhenteet, perustelu in huomiot)
            rivit.append('<tr class="selite"><td colspan="6" '
                         'class="perustelu">%s</td></tr>' % teksti)

    sisalto = f"""
<h1>Messa da Requiem</h1>
<p class="johdanto">Verdin <em>Messa da Requiem</em>, kahdeksan kuorostemmaa
harjoittelua varten. Jokaisen tahdin päällä on tahtinumero ja jokaisen sivun
yläreunassa käynnissä olevan osan nimi, jotta yksittäisen tahdin löytää
kuoronjohtajan huudosta.</p>

{luotettavuusvaroitus()}

<ul class="lataukset">{linkit}</ul>

<h2>Osat, tahdit ja luotettavuus</h2>
<p><strong>Tahtinumerot täsmäävät Edition Petersin painoksen kanssa.</strong>
Dies irae eli osa II
numeroituu yhtenäisesti läpi kaikkien alaosiensa; muut osat alkavat
ykkösestä. Kunkin äänen sarakkeessa on <strong>sivunumero</strong> siinä
stemmassa ja <strong>merkki</strong> siitä, kuinka tarkistettu ääni on. Kaksi
lukua tarkoittaa, että I- ja II-stemma ovat eri sivuilla.</p>
<div class="vieritin">
<table class="sisallys">
<thead><tr><th>Osa</th><th class="luku">Tahdit</th>{otsikot}</tr></thead>
<tbody>{''.join(rivit)}</tbody>
</table>
</div>
{luotettavuusselitteet()}
{alaviite()}
"""
    return sivu("Stemmat", sisalto, "index.html")


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

    for nimi, teksti in [("index.html", stemmasivu()),
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
