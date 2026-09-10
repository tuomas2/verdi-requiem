#!/usr/bin/env python3
"""Rakenna verkkosivusto stemmoista, teksteistä ja luotettavuustaulukosta.

Sivuston tiedot luetaan samoista vakioista, jotka ohjaavat stemmojen
tuotantoa (yhdista.MOVEMENTS, luotettavuus.POIKKEUKSET), joten sivu ei voi
väittää aineistosta muuta kuin mitä siitä tiedetään.

Käyttö:  python3 sivusto.py [_sivusto]

Tulos ei ole versionhallinnassa: CI rakentaa julkaistavan version samalla
komennolla. Näin sivusto ei voi vanhentua huomaamatta.
"""

import html as _html
import os
import shutil
import sys

import luotettavuus
import paivays
import suomennos
import polut
import yhdista

POHJA = "sivusto"

# Oma verkkotunnus. GitHub Pages lukee sen julkaistavasta hakemistosta, joten
# tiedosto kirjoitetaan tuotokseen eikä pelkästään Pagesin asetuksiin — näin
# se ei katoa jos asetukset nollautuvat. Vaatii DNS:ään CNAME-tietueen, joka
# osoittaa tuomas2.github.io:hon.
VERKKOTUNNUS = "requiem.tuomasairaksinen.fi"

GITHUB = "https://github.com/tuomas2/verdi-requiem"
# Virheilmoitukset menevät tiketeiksi eivätkä sähköpostiin: tiketti säilyy,
# näkyy muille lukijoille ja pysyy auki kunnes korjaus on tehty. Molemmat
# osoitteet johdetaan GITHUBista, jottei repon siirto jätä puolta linkeistä
# vanhaan paikkaan.
TIKETIT = GITHUB + "/issues"
UUSI_TIKETTI = TIKETIT + "/new"
CPDL = "https://www.cpdl.org/wiki/index.php/Requiem_(Giuseppe_Verdi)"

# Kaksi sivua riittää, ja stemmat on niistä se jota luetaan: se on etusivu.
# Kun kohtia on näin vähän, jokainen mahtuu kertomaan mihin se vie.
# GitHub on mukana siksi, että aineiston parantaminen on osa tämän projektin
# tarkoitusta: kaikilla stemmoilla ei vielä ole luotettavia nuotteja, ja
# tiketit ovat se kanava jota pitkin virheet tulevat tietoon.
NAVI = [("index.html", "Stemmat", "kahdeksan ääntä, PDF ja MusicXML"),
        ("teksti.html", "Teksti", "mitä olet laulamassa, suomeksi"),
        (GITHUB, "GitHub", "lähteet ja virheiden ilmoitus")]

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
<section class="lohko">
<h2>Mistä tämä on peräisin</h2>
<p class="tausta">Sävellys on public domainissa; Verdi kuoli 1901.
Nuottiaineisto on peräisin
<a href="{CPDL}">CPDL:n (Choral Public Domain Library) Requiem-sivulta</a>:
sen editiot saa vapaasti levittää ja esittää. Kuusitoista erillistä
osatiedostoa on yhdistetty yhdeksi partituuriksi, ja stemmat on tuotettu
siitä. Tahtinumerointi on sovitettu {e(luotettavuus.REFERENSSI)}in
painokseen, jota vasten kuorobasso on myös käyty läpi.</p>
<p class="tausta">Lähtökohta on kuorolaisen käytännön tarve: lukea omaa
stemmaa niin että muu kuoro ja pianosäestys kuuluvat, kantaa stemma mukana
lukulaitteella, ja löytää yksittäinen tahti kun kuoronjohtaja huutaa
numeron.</p>
<p class="tausta">Lähdekoodi, koko työn dokumentaatio ja ohjeet aineiston
uudelleenluontiin:
<a href="{GITHUB}">github.com/tuomas2/verdi-requiem</a>.
Skriptit ja dokumentaatio ovat GPL-3.0-lisenssin alaisia.</p>
</section>
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
    """Mitä on tarkistettu ja mitä ei — ominaisuuslistan yksi selitys.

    Tämä on ominaisuus muiden joukossa eikä oma laatikkonsa: laulaja lukee
    listan läpi valitessaan stemmaa, ja lyhennetty muistutus on jo
    otsikkokappaleessa latauslinkkien yläpuolella. Kaksi rinnakkaista
    versiona samasta asiasta oli sivun ainoa toisteinen kohta.

    Linkki menee generoituun LUOTETTAVUUS.md:hen eikä luotettavuus.py:hyn:
    taulukon lukijalla ei ole asiaa Pythonin sisään, ja GitHub näyttää
    md-tiedoston valmiiksi taulukoituna.
    """
    puutteet = [e(o) for o in puutteelliset_osat()]
    maininta = ""
    if puutteet:
        # "a, b ja c" — pilkut väliin, viimeisen eteen ja.
        luettelo = (puutteet[0] if len(puutteet) == 1
                    else ", ".join(puutteet[:-1]) + " ja " + puutteet[-1])
        maininta = (" Erityisesti näissä osissa on ylemmissä äänissä "
                    "tiedettyjä virheitä: %s." % luettelo)
    return (
        f"Kuorobasso on tarkistettu käsin {e(luotettavuus.REFERENSSI)}in "
        "painosta vasten ja laulettu läpi harjoituksissa; sopraano, altto ja "
        f"tenori ovat pääosin tarkistamatta.{maininta} Syy on yksinkertainen: "
        "tekijä laulaa bassoa. Osakohtainen erittely siitä mitä on "
        f'tarkistettu ja miten: <a href="{GITHUB}/blob/main/'
        f'{luotettavuus.MD_TIEDOSTO}">{e(luotettavuus.MD_TIEDOSTO)}</a>. '
        f'Löytämäsi virheen voi ilmoittaa: <a href="#{ANKKURI}">'
        'Löysitkö virheen?</a>')


# ------------------------------------------------------------ korjaukset

# Ankkuri on vakio, koska luotettavuusvaraus linkittää tähän lukuun: kaksi
# käsin kirjoitettua tunnistetta ehtisi erkaantua toisistaan.
ANKKURI = "virheet"

# Mitä raportissa pitää olla, jotta sen perusteella voi tehdä korjauksen.
# Järjestys on se, jossa korjaaja niitä tarvitsee: ensin mistä kohdasta on
# kyse, sitten mikä siinä on vikana, ja lopuksi mistä sen tietää.
RAPORTIN_OSAT = [
    ("Ääni ja tahtinumero",
     "Kumpi stemma (esimerkiksi <span class=\"koodi\">A II</span>) ja minkä "
     "tahdin. Numero on jokaisen tahdin päällä, joten sitä ei tarvitse "
     "laskea rivin alusta."),
    ("Säe ja tavu",
     "Sanavirheessä se latinan säe, jota kohta laulaa, ja tavu jonka "
     "kohdalla vika on — <i>“qui salvandos salvas gratis”, sana "
     "salvandos</i>. Pelkkä tahtinumero ei riitä, kun sama säe toistuu "
     "osassa monta kertaa."),
    ("Täsmällinen ohje korjaukseen",
     "Mitä stemmassa lukee nyt ja mitä siinä pitäisi lukea: <i>“tahdin 653 "
     "toinen nuotti on h, pitäisi olla c”</i> tai <i>“tahdeista 340–341 "
     "puuttuu säe ja edellinen on kahteen kertaan”</i>. Tämä on raportin "
     "tärkein kohta: sen varassa korjaus joko voidaan tehdä tai ei."),
    ("Mistä tiedät",
     "Mikä painos, kuoron nuottikirja tai äänite kertoo miten sen kuuluu "
     "mennä. Muistikuvakin kelpaa, kunhan se on merkitty muistikuvaksi: "
     "korjausta ei tehdä ennen kuin se on varmistettu jostain, ja tieto "
     "siitä mistä tarkistaa säästää sen työn."),
]


def korjaukset():
    """Kutsu ilmoittaa virheistä — ja miten ilmoitus kannattaa kirjoittaa.

    Tämä on oma lukunsa eikä alaviitteen lause siksi, että se on ainoa
    kohta koko sivustolla, jossa lukijalta pyydetään jotain. Ylemmät äänet
    ovat tarkistamatta, eikä tekijä yksin bassoa laulaen niitä tarkista:
    ainoa tie eteenpäin on se, että joku joka laulaa stemman ilmoittaa
    mitä siinä on vikana.

    Toinen kanava on WhatsApp, koska siellä kuoro jo puhuu — mutta sivulle
    ei kirjoiteta nimeä, numeroa eikä ryhmän nimeä: sivusto on julkinen, ja
    kuorolaiset tietävät kenelle viesti menee ilman että se on tässä.
    """
    osat = "".join("<dt>%s</dt><dd>%s</dd>" % (nimi, teksti)
                   for nimi, teksti in RAPORTIN_OSAT)
    return f"""
<section class="lohko" id="{ANKKURI}">
<h2>Löysitkö virheen?</h2>
<p>Korjausilmoitukset ovat tervetulleita, ja
<strong>erityisesti muista äänistä kuin bassosta</strong>: sopraano, altto
ja tenori ovat pääosin tarkistamatta, ja virheen huomaa käytännössä vain
se, joka laulaa stemman. Yksi ilmoitettu tahti auttaa tässä enemmän kuin
mikään uusi ominaisuus.</p>
<p>Ilmoitukset mieluiten GitHubiin tiketiksi:
<a href="{UUSI_TIKETTI}">tee uusi tiketti</a> tai katso
<a href="{TIKETIT}">jo ilmoitetut</a>. Tiketti on sähköpostia parempi
siksi, että se säilyy, näkyy muillekin lukijoille ja pysyy auki siihen
asti kun korjaus on tehty ja stemma rakennettu uudelleen.</p>
<p>Mitä ilmoituksessa tarvitaan:</p>
<dl class="ominaisuudet">{osat}</dl>
<p class="tausta">Mieluiten yksi virhe per tiketti: ne korjataan ja
suljetaan yksitellen. Jos GitHub-tunnusta ei ole, kelpaa yhtä hyvin
WhatsApp-viesti tekijälle — samat tiedot tarvitaan siinäkin.</p>
</section>
"""


# --------------------------------------------------------------- stemmat

def sivumaarat():
    """Stemmojen sivumäärät stemmat-sisallys.txt:n omalta viimeiseltä riviltä.

    Luetaan eikä kirjoiteta käsin: sivumäärä muuttuu joka kerta kun jotain
    lisätään stemmaan, ja käsin kirjoitettu luku jäisi jälkeen.
    """
    polku = os.path.join("stemmat", "stemmat-sisallys.txt")
    if not os.path.exists(polku):
        return []
    for rivi in reversed(open(polku, encoding="utf-8").read().splitlines()):
        if rivi.strip().startswith("sivuja"):
            return [int(x) for x in rivi.split()[1:]]
    return []


def dies_irae_vali():
    """Dies iraen tahtiväli, laskettuna eikä kirjoitettuna.

    Alku on yhdista.DIES_IRAE_ALUT:n pienin luku ja loppu viimeisen
    alaosan aloitus plus sen oman lähdetiedoston tahtimäärä. Numerot ovat
    kuoron nuottikirjan omat, joten niitä ei arvata kahteen paikkaan.
    """
    alut = yhdista.DIES_IRAE_ALUT
    viimeinen = max(alut, key=alut.get)
    root = suomennos.load(viimeinen)
    tahteja = max(len(p.findall("measure")) for p in root.findall("part"))
    return min(alut.values()), alut[viimeinen] + tahteja - 1


# Luotettavuusvarauksen otsikko ominaisuuslistalla. Vakiona siksi, että sekä
# rivi että sen korostusluokka tunnistetaan samasta nimestä.
VIRHEET = "Voi sisältää virheitä"


def ominaisuudet():
    """Mitä stemmoissa on. Luvut johdetaan, jotta ne eivät jää jälkeen."""
    sivut = sivumaarat()
    laajuus = (f"{min(sivut)}–{max(sivut)} sivua" if sivut else "tiivis")
    alku, loppu = dies_irae_vali()
    kohdat = [
        # Listan kärjessä eikä lopussa: se on stemman ominaisuus siinä missä
        # muutkin, ja se joka lataa stemman saa tietää sen ensin.
        (VIRHEET, luotettavuusteksti()),
        ("Tahtinumero joka tahdissa",
         "Numero jokaisen tahdin päällä, ei vain rivin alussa, ja "
         "tiivistetyn tauon päällä sen tahtiväli (<span "
         "class=\"koodi\">[79–93]</span>). Kuoronjohtajan huutaman tahdin "
         "löytää laskematta rivin alusta."),
        ("Osan nimi joka sivulla",
         "Käynnissä olevan osan nimi sivun ensimmäisen tahdin päällä, joten "
         "keskeltä avattu sivu kertoo itse, missä osassa ollaan."),
        (f"Tahtinumerot {e(luotettavuus.REFERENSSI)}in mukaan",
         f"Dies irae numeroituu yhtenäisesti {alku}–{loppu} niin kuin "
         "kuoron nuottikirjassa; muut osat alkavat ykkösestä. Tämä on koko "
         "hankkeen tärkein yksittäinen vaatimus."),
        ("Latinan sanojen suomennos",
         "Jokaisen latinan sanan alla sen suomennos pienemmällä "
         f"({e(suomennos.KOKO.replace('.', ','))} pt) — sanatarkka ja "
         "latinan sanajärjestystä seuraava, sama käännös kuin tekstisivulla. "
         "Suomen sana tulee kokonaisena latinan sanan ensimmäisen tavun "
         "alle, myös silloin kun sana venyy monelle nuotille, eikä sitä "
         "tavuteta. Se myös <i>alkaa</i> samasta kohdasta kuin tavu, ei "
         "keskitettynä sen alle, jotta näkyy kumman sanan käännös se on."),
        ("Vain oma ääni",
         f"Muut äänet ja pianosäestys eivät ole mukana, ja useamman tahdin "
         f"tauot ovat yhtenä palkkina, joten stemma on {laajuus} eikä "
         f"noin 150 niin kuin koko {e(luotettavuus.REFERENSSI)}in nuotti."),
        ("Tilaa käsimerkinnöille",
         "Nuottirivien väli on 29,3 mm ja marginaali 15 mm, eli "
         "harjoituksissa tehdyille merkinnöille jää noin 22 mm kaistale "
         "rivien väliin. Mitattu, ei arvattu."),
        ("MusicXML PDF:n rinnalla",
         "Sama sisältö lähdemuodossa: avautuu esimerkiksi MuseScorella, "
         "sanat ja suomennokset mukana, joten stemmaa voi muokata itse tai "
         "kuunnella sen läpi."),
    ]
    # Virherivi on listan ainoa varaus, ja se erottuu värillä: muuten se
    # hukkuisi kahdeksan lupauksen joukkoon juuri siksi että se on niiden
    # seassa.
    def rivi(nimi, teksti):
        luokka = ' class="huomio"' if nimi == VIRHEET else ""
        return "<dt%s>%s</dt><dd%s>%s</dd>" % (luokka, nimi, luokka, teksti)

    rivit = "".join(rivi(nimi, teksti) for nimi, teksti in kohdat)
    return (f'<h2>Ominaisuudet</h2>\n'
            f'<dl class="ominaisuudet">{rivit}</dl>')


def paivamaara(pdf):
    """Milloin tämän stemman sisältö viimeksi muuttui.

    Luetaan `.mxl`:stä, johon `paivays.py` merkitsi sen — samasta
    merkinnästä kuin PDF:n ensimmäisen sivun päiväys, joten sivu ja tiedosto
    eivät voi kertoa eri päivää. Merkitsemätön stemma jää ilman päiväystä:
    arvattu päivä olisi huonompi kuin ei mitään.
    """
    mxl = pdf[:-4] + ".mxl"
    if not os.path.exists(polut.polku(mxl)):
        return ""
    iso = paivays.lue(mxl)
    if not iso:
        return ""
    return ('<span class="paivays"><time datetime="%s">päivitetty %s</time>'
            "</span>" % (e(iso), e(paivays.suomeksi(iso))))


def stemmasivu():
    """Stemmat ja lataukset — sivuston pääsivu."""
    pikkukuvat = os.path.isdir(os.path.join(POHJA, "pikkukuvat"))

    def lataus(nimi, pdf):
        kuva = ('<img src="pikkukuvat/%s.png" alt="" width="110" '
                'loading="lazy">' % pdf[:-4]) if pikkukuvat else ""
        return ('<li><a class="stemma" href="stemmat/%s">%s<span>%s</span></a>'
                '<span class="muodot"><a href="stemmat/%s">PDF</a> · '
                '<a href="stemmat/%s">MusicXML</a></span>%s</li>'
                % (pdf, kuva, e(nimi), pdf, pdf[:-4] + ".mxl",
                   paivamaara(pdf)))

    linkit = "".join(lataus(nimi, pdf) for nimi, pdf in STEMMAT)

    koko = "Verdi-Requiem-koko.mxl"
    sisalto = f"""
<header class="masthead">
<p class="eyebrow">Giuseppe Verdi · 1874</p>
<h1>Messa da Requiem<em>kahdeksan kuorostemmaa harjoittelua varten</em></h1>
<p class="standfirst">Jokainen kuoroääni omana tiedostonaan, PDF:nä
luettavaksi ja MusicXML:nä muokattavaksi, ja niiden rinnalla koko partituuri.
Stemmassa on vain oma ääni, tahtinumero joka tahdissa
{e(luotettavuus.REFERENSSI)}in painoksen mukaan ja latinan sanojen suomennos
nuottien alla — niin että harjoituksissa löytää huudetun tahdin ja tietää
mitä on laulamassa. Nuottiaineisto on koottu CPDL:n vapaista editioista, ja
siitä on käyty käsin läpi kuorobasso; <strong>muut äänet ovat pääosin
tarkistamatta</strong>.</p>
</header>

<section class="lohko">
<h2>Stemmat</h2>
<ul class="lataukset">{linkit}</ul>
</section>

<section class="lohko">
{ominaisuudet()}
</section>

{korjaukset()}

<section class="lohko">
<h2>Koko partituuri</h2>
<p>Kaikki viisitoista viivastoa yhtenä tiedostona, 1807 tahtia:
<a href="{koko}">{koko}</a> (MusicXML, avautuu esimerkiksi MuseScorella).</p>
</section>

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
