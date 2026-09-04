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

GITHUB = "https://github.com/tuomas2/verdi-requiem"
CPDL = "https://www.cpdl.org/wiki/index.php/Requiem_(Giuseppe_Verdi)"

# Kaksi sivua riittää, ja stemmat on niistä se jota luetaan: se on etusivu.
# Kun kohtia on näin vähän, jokainen mahtuu kertomaan mihin se vie.
# GitHub on mukana siksi, että aineiston parantaminen on osa tämän projektin
# tarkoitusta: kaikilla stemmoilla ei vielä ole luotettavia nuotteja.
NAVI = [("index.html", "Stemmat", "kahdeksan ääntä, PDF ja MusicXML"),
        ("teksti.html", "Teksti", "mitä olet laulamassa, suomeksi"),
        (GITHUB, "GitHub", "lähteet ja nuottien parantaminen")]

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


# Valikon tyyli on tässä eikä tyyli.css:ssä, koska sama valikko upotetaan myös
# requiem.html:ään, joka ei lataa jaettua tyyliä — se on itsenäinen sivu omine
# tyyleineen. Yksi lähde takaa että valikko on molemmilla sivuilla sama.
#
# Luokka on `valikko` eikä `bar`, ja se on tärkeää: requiem.html:llä on omat
# .bar- ja .bar-inner-sääntönsä, ja niistä vuoti aiemmin justify-content
# injektoituun valikkoon. Tekstisivun valikko levisi koko leveydelle ja
# stemmasivun ei. Oma luokkanimi sulkee vuodon kokonaan.
VALIKKO_TYYLI = """<style>
.valikko{position:sticky;top:0;z-index:20;background:var(--paper,#ecebe4);
         border-bottom:1px solid var(--rule,rgba(25,21,18,.16))}
.valikko-sisus{max-width:1100px;margin:0 auto;padding:.55rem 1.25rem;
               display:flex;flex-wrap:wrap;gap:.75rem 1.25rem;
               align-items:flex-start;justify-content:space-between}
.valikko a{text-decoration:none;display:block;padding:.15rem 0;
           font-family:var(--sans,system-ui,sans-serif)}
.valikko a b{display:block;font-size:.72rem;font-weight:600;
             letter-spacing:.09em;text-transform:uppercase;
             color:var(--ink-soft,rgba(25,21,18,.62))}
.valikko a i{display:block;font-style:normal;font-size:.68rem;line-height:1.3;
             color:var(--ink-soft,rgba(25,21,18,.62));opacity:.75;
             margin-top:.1rem}
.valikko a:hover b,.valikko a:hover i{color:var(--rubric,#9d1b18)}
.valikko a[aria-current="page"] b{color:var(--rubric,#9d1b18)}
.valikko a[aria-current="page"] i{opacity:.9}
@media (max-width:560px){
  .valikko-sisus{gap:.6rem 1rem;justify-content:flex-start}
  .valikko a i{display:none}
}
</style>"""

# Tekstisivulla on jo oma tarttuva palkkinsa, joten kaksi päällekkäin
# tarttuvaa peittäisi sisältöä. Tämä on ainoa ero sivujen valikoissa.
VALIKKO_TYYLI_STAATTINEN = VALIKKO_TYYLI.replace(
    ".valikko{position:sticky;top:0;z-index:20;", ".valikko{position:static;")


def navigaatio(aktiivinen):
    """Sama valikko molemmilla sivuilla, selitteineen."""
    linkit = "".join(
        '<a href="%s"%s><b>%s</b><i>%s</i></a>'
        % (kohde, ' aria-current="page"' if kohde == aktiivinen else "",
           e(nimi), e(selite))
        for kohde, nimi, selite in NAVI)
    return ('<nav class="valikko"><div class="valikko-sisus">%s</div></nav>'
            % linkit)


def sivu(otsikko, sisalto, aktiivinen):
    """Kokonainen HTML-sivu yhteisellä navigaatiolla."""
    return f"""<!DOCTYPE html>
<html lang="fi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(otsikko)} — Verdi: Messa da Requiem</title>
{FONTIT}
<link rel="stylesheet" href="tyyli.css">
{VALIKKO_TYYLI}
</head>
<body>
{navigaatio(aktiivinen)}
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
    return f"""
<h2>Mistä tämä on peräisin</h2>
<p>Sävellys on public domainissa; Verdi kuoli 1901. Nuottiaineisto on peräisin
<a href="{CPDL}">CPDL:n (Choral Public Domain Library) Requiem-sivulta</a>:
sen editiot saa vapaasti levittää ja esittää. Kuusitoista erillistä
osatiedostoa on yhdistetty yhdeksi partituuriksi, ja stemmat on tuotettu
siitä. Tahtinumerointi on sovitettu Edition Petersin painokseen, jota vasten
kuorobasso on myös käyty läpi.</p>
<p>Lähtökohta on kuorolaisen käytännön tarve: lukea omaa stemmaa niin että muu
kuoro ja pianosäestys kuuluvat, kantaa stemma mukana lukulaitteella, ja löytää
yksittäinen tahti kun kuoronjohtaja huutaa numeron.</p>
<p>Lähdekoodi, koko työn dokumentaatio ja ohjeet aineiston uudelleenluontiin:
<a href="https://github.com/tuomas2/verdi-requiem">github.com/tuomas2/verdi-requiem</a>.
Skriptit ja dokumentaatio ovat GPL-3.0-lisenssin alaisia.</p>
"""


# ----------------------------------------------------------- luotettavuus

def puutteelliset_osat():
    """Osat, joissa jokin ylempi ääni on tiedetysti virheellinen.

    Johdetaan taulukosta eikä kirjoiteta käsin, jotta maininta ei jää
    jälkeen kun taulukko muuttuu.
    """
    osat = []
    for _tiedosto, numero, otsikko in yhdista.MOVEMENTS:
        if any(luotettavuus.tila(numero, a).nimi == "puutteita"
               for a in ("Kuoro S", "Kuoro A", "Kuoro T")):
            osat.append(otsikko)
    return osat


def luotettavuusteksti():
    """Lyhyt varoitus. Yksityiskohdat ovat repossa, josta ne on luettukin."""
    puutteet = [e(o) for o in puutteelliset_osat()]
    maininta = ""
    if puutteet:
        # "a, b ja c" — pilkut väliin, viimeisen eteen ja.
        luettelo = (puutteet[0] if len(puutteet) == 1
                    else ", ".join(puutteet[:-1]) + " ja " + puutteet[-1])
        maininta = (" Erityisesti näissä osissa on ylemmissä äänissä "
                    "tiedettyjä virheitä: %s." % luettelo)
    return f"""
<div class="varoitus">
<p><strong>Kuorobasso on käyty läpi, muut äänet eivät.</strong> Basso on
tarkistettu käsin {e(luotettavuus.REFERENSSI)}in painosta vasten ja laulettu
läpi harjoituksissa; sopraano, altto ja tenori ovat pääosin
tarkistamatta.{maininta} Syy on yksinkertainen: tekijä laulaa bassoa.</p>
<p class="perustelu">Osakohtainen erittely siitä mitä on tarkistettu ja
miten: <a href="{GITHUB}/blob/main/luotettavuus.py">luotettavuus.py</a>.</p>
</div>
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
    """Stemmat, lataukset ja sisällys — sivuston pääsivu.

    Sivunumerot ovat stemmaa kohti (S I, S II, ...), mutta koko teoksessa on
    tasan yksi kohta jossa saman äänen kaksi stemmaa ovat eri sivuilla, joten
    ne mahtuvat neljään sarakkeeseen kahdeksan sijaan.
    """
    sisallys = lue_sisallys()
    valit = tahtivalit()
    pikkukuvat = os.path.isdir(os.path.join(POHJA, "pikkukuvat"))

    def lataus(nimi, pdf):
        kuva = ('<img src="pikkukuvat/%s.png" alt="" width="110" '
                'loading="lazy">' % pdf[:-4]) if pikkukuvat else ""
        return ('<li><a class="stemma" href="stemmat/%s">%s<span>%s</span></a>'
                '<span class="muodot"><a href="stemmat/%s">PDF</a> · '
                '<a href="stemmat/%s">MusicXML</a></span></li>'
                % (pdf, kuva, e(nimi), pdf, pdf[:-4] + ".mxl"))

    linkit = "".join(lataus(nimi, pdf) for nimi, pdf in STEMMAT)
    otsikot = "".join('<th class="aani">%s</th>' % e(a.replace("Kuoro ", ""))
                      for a in luotettavuus.AANET)

    rivit = []
    for numero, otsikko, sivut in sisallys:
        alku_t, loppu_t = valit.get(numero, ("", ""))
        solut = []
        for i in range(len(luotettavuus.AANET)):
            ensimmainen, toinen = sivut[2 * i], sivut[2 * i + 1]
            solut.append('<td class="aani">%s</td>'
                         % e(ensimmainen if ensimmainen == toinen
                             else "%d/%d" % (ensimmainen, toinen)))
        rivit.append(
            '<tr><td><strong>%s</strong> %s</td><td class="luku">%s–%s</td>%s</tr>'
            % (e(numero), e(otsikko), e(alku_t), e(loppu_t), "".join(solut)))

    koko = "Verdi-Requiem-koko.mxl"
    sisalto = f"""
<header class="masthead">
<h1>Messa da Requiem</h1>
<p class="johdanto">Verdin <em>Messa da Requiem</em>, kahdeksan kuorostemmaa
harjoittelua varten. Jokaisen tahdin päällä on tahtinumero ja jokaisen sivun
yläreunassa käynnissä olevan osan nimi, jotta yksittäisen tahdin löytää
kuoronjohtajan huudosta. <strong>Tahtinumerot täsmäävät
{e(luotettavuus.REFERENSSI)}in painoksen kanssa.</strong></p>
</header>

{luotettavuusteksti()}

<h2>Stemmat</h2>
<ul class="lataukset">{linkit}</ul>

<h2>Koko partituuri</h2>
<p>Kaikki viisitoista viivastoa yhtenä tiedostona, 1807 tahtia:
<a href="{koko}">{koko}</a> (MusicXML, avautuu esimerkiksi MuseScorella).</p>

<h2>Mistä osa alkaa</h2>
<p>Dies irae eli osa II numeroituu yhtenäisesti läpi kaikkien alaosiensa; muut
osat alkavat ykkösestä. Sarakkeissa on sivunumero kunkin äänen stemmassa;
kaksi lukua tarkoittaa, että I- ja II-stemma ovat eri sivuilla.</p>
<div class="vieritin">
<table class="sisallys">
<thead><tr><th>Osa</th><th class="luku">Tahdit</th>{otsikot}</tr></thead>
<tbody>{''.join(rivit)}</tbody>
</table>
</div>
{alaviite()}
"""
    return sivu("Stemmat", sisalto, "index.html")


# ---------------------------------------------------------------- teksti

def tekstisivu():
    """requiem.html sellaisenaan, yhteinen valikko lisättynä.

    Sivu on itsenäinen ja toimiva omine tyyleineen, joten sitä ei
    refaktoroida jaetun tyylin päälle. Valikko tulee samasta lähteestä kuin
    muillakin sivuilla, jotta se on varmasti sama.
    """
    with open(os.path.join(POHJA, "requiem.html"), encoding="utf-8") as f:
        html = f.read()
    if "<body>" not in html:
        raise SystemExit("sivusto/requiem.html: <body>-tagia ei löydy")
    lisays = VALIKKO_TYYLI_STAATTINEN + "\n" + navigaatio("teksti.html")
    return html.replace("<body>", "<body>\n" + lisays, 1)


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
        shutil.copy(polut.polku(pdf[:-4] + ".mxl"), kohde)
    shutil.copy(polut.polku("Verdi-Requiem-koko.mxl"), ulos)

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
