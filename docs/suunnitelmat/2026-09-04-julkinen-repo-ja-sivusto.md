# Julkinen repo ja verkkosivusto

Suunnitelma 2026-09-04. Tila: hyväksyttävänä.

## 1. Tavoite

Tehdä tästä hakemistosta julkinen git-repo (`tuomas2/verdi-requiem`) ja sen
rinnalle GitHub Pages -sivusto, joka tarjoaa aineiston myös selattavassa
muodossa.

Julkaisun tarkoitus on, että **joku muu voi jatkaa nuottien parantamista**.
Se ohjaa kahta ratkaisua: `CLAUDE.md` tulee mukaan sellaisenaan, koska se on
työn perusteellisin kuvaus, ja sivustolle tulee luotettavuussivu, joka kertoo
suoraan mikä on tarkistettu ja mikä ei — muuten seuraava tekijä ei tiedä mistä
aloittaa.

Rajaus: `musescore/` ei tule mukaan missään muodossa, ei työhakemistoon eikä
historiaan.

## 2. Lähtötilanne, mitattuna

| Asia | Arvo |
|---|---|
| Repon koko | 160 MB, josta `.git` 124 MB |
| Committeja | 47, ei remotea |
| `musescore/` | 77 tiedostoa, 12 MB, **seurannassa historiassa** |
| Tiedostonimiliteraaleja skripteissä | 117 yhdeksässä tiedostossa |
| Testejä | 136 |
| Juuressa tiedostoja | ~70 |

Historian painavimmat kohteet: `harjoitus-basso-1.mscz` noin 12 versiona à
3,1 MB, `Verdi-Requiem-koko-oma.mscz` 3,1 MB, kolme `.omr`-projektia 8,7 MB.

Salaisuustarkistus tehty: ei sähköposteja, avaimia eikä henkilönimiä
`*.md`- tai `*.py`-tiedostoissa. Julkaistavien PDF:ien `Author` on tyhjä.
Ainoat henkilönimet olivat `musescore/`-hakemiston tiedostonimissä, ja se
jää pois.

## 3. Hakemistorakenne

```
README.md              suomeksi, uusi
LICENSE                GPL-3.0-or-later
CLAUDE.md              tekninen työpäiväkirja, uusi kehysteksti alkuun
YHDISTAMINEN.md        käyttäjän dokumentaatio, ennallaan
*.py                   komennot ja testit, pysyvät juuressa
polut.py               uusi, hakemistovakiot ja nimenselvitys
tiivistys.mss

lahteet/               16 alkuperäistä .mxl, 2 raakaa -OMR.mxl,
                       4 lähde-PDF:ää, 3 .omr-projektia, 3 CPDL:n .mscz
johdetut/              *-OMR-korjattu.mxl, *-kasin.mxl, Verdi-Requiem-koko.mxl
stemmat/               8 × .mxl, 8 × .pdf, stemmat-sisallys.txt
harjoitus/             *.mscz, ei versionhallinnassa
sivusto/               generaattorin pohjat, tyylit, requiem.html
docs/suunnitelmat/     tämä tiedosto
.github/workflows/     sivusto.yml
```

Hakemistojen nimet vastaavat datan kulkusuuntaa:

    lahteet/ ──korjaa_sanat.py──> johdetut/
    lahteet/ ─┐
              ├─korjaa_kasin.py─> johdetut/
    johdetut/ ┘
    johdetut/ ──yhdista.py──────> johdetut/ (koko partituuri) ja stemmat/

### Mikä jää pois versionhallinnasta

- `harjoitus-*.mscz` — 3,2 MB kappale, syntyy komennolla
  `python3 harjoitus.py --stemma "Basso I"`. Juuri näiden toistuva
  tallentaminen paisutti historian. Jos ne halutaan kuorolaisille
  ladattaviksi, oikea paikka on GitHub Releases.
- `Verdi-Requiem-koko-oma.mscz` — 3,1 MB, ei viittauksia missään.
  Jää levylle, poistuu seurannasta ja historiasta.
- `_sivusto/` — sivuston paikallinen esikatselu.

## 4. Polkujen selvitys: sääntö, ei 117 muokkausta

Naiivi tapa olisi lisätä hakemistoetuliite jokaiseen 117 literaaliin. Se on
virhealtista ja rumentaa taulukot, joissa tiedostonimet ovat nyt luettavina
riveinä (`MOVEMENTS`, `MAPPING`, `korjaa_kasin.py`:n `Osa`-rivit).

Sen sijaan uusi `polut.py` selvittää hakemiston nimestä. Projektin oma
nimeämiskäytäntö kertoo sen jo nyt:

```python
LAHTEET  = Path("lahteet")
JOHDETUT = Path("johdetut")
STEMMAT  = Path("stemmat")

def polku(nimi):
    """Johdettu tiedosto johdetut/-hakemistoon, muut lahteet/-hakemistoon."""
    if nimi.endswith(("-kasin.mxl", "-OMR-korjattu.mxl")) \
       or nimi.startswith("Verdi-Requiem-koko"):
        return JOHDETUT / nimi
    if nimi.startswith("stemma"):
        return STEMMAT / nimi
    return LAHTEET / nimi
```

Taulukot säilyvät ennallaan paljaine tiedostonimineen; vain käyttökohdat
kutsuvat `polku()`:a. Muutettavia kohtia on noin 20 eikä 117.

`polku()` koskee **vain nuottiaineistoa**. Työkalutiedostoilla on omat
vakionsa jo nyt eikä niitä reititetä sen kautta: `tiivistys.mss` on
`harjoitus.py`:n ja `sivuotsikot.py`:n `TYYLI`-vakio ja jää juureen.

**Sääntö ei saa jäädä hiljaiseksi oletukseksi.** `test_polut.py` vaatii, että
jokainen skriptien taulukoissa mainittu tiedostonimi selviää tiedostoon, joka
on olemassa täsmälleen siinä hakemistossa jonka sääntö sanoo. Väärään
hakemistoon eksynyt tiedosto kaatuu testissä eikä tuota hiljaa väärää tulosta.

### Hyväksymiskriteeri

Testien läpimeno ei riitä. Siirron jälkeen ajetaan koko ketju alusta loppuun
ja verrataan tulos siirtoa edeltävään:

```
korjaa_sanat.py → korjaa_kasin.py → yhdista.py (koko + 8 stemmaa)
  → sivuotsikot.py → mscore → sisallys.py
```

`.mxl`-tiedostoja **ei voi verrata tavuina**, ja tämä on mitattu eikä
oletettu: `yhdista.py` kirjoittaa ne `zipfile.writestr`illä, joka leimaa
nykyhetken jokaiseen zip-merkintään, joten kaksi peräkkäistä ajoa samasta
datasta tuottavat eri tavut. Vertailu tehdään siis **puretusta
`score.xml`:stä**, joka on se sisältö jolla on merkitystä — sen on oltava
tavulleen sama. `stemmat-sisallys.txt` verrataan suoraan tavuina. PDF:t
verrataan sivumäärältä ja tekstikerroksen sisällöltä, koska niidenkin
metatiedoissa on aikaleima.

Sivuhuomio, ei osa tätä työtä: kiinteä `date_time` zip-merkinnöissä tekisi
`.mxl`-tuloksesta toistettavan, mikä olisi julkisessa repossa siisti
ominaisuus. Se muuttaisi kaikkien johdettujen tiedostojen tavut kertaalleen,
joten se kuuluu omaksi committikseen tämän jälkeen — ei sekaan, jossa se
peittäisi siirron aiheuttamat erot.

## 5. Luotettavuusdata

Uusi `luotettavuus.py` sisältää käsin ylläpidetyn taulukon: osa × ääni →
tila, yhden rivin perustelu ja päiväys. Tieto on ihmisen arvio eikä laskettu
suure, joten se kirjoitetaan `CLAUDE.md`:n työhistoriasta, jossa jokainen
tarkistus on kirjattu.

Tilat:

| Merkki | Tila | Merkitys |
|---|---|---|
| `✔` | varmistettu | Vertailtu riippumattomaan lähteeseen nuotti nuotilta tai tavu tavulta |
| `◑` | osittain | Esimerkiksi sanat tarkistettu, nuotit eivät |
| `○` | tarkistamatta | Ei tunnettuja virheitä, mutta ei myöskään tarkistettu |
| `⚠` | tunnettuja puutteita | Tiedetään virheellistä sisältöä |

Esimerkkirivejä (lopullinen taulukko täytetään toteutuksessa):

| Osa | Kuoro B | S / A / T |
|---|---|---|
| V Agnus Dei | `✔` koko osa vertailtu kuorotiedostoon, 15 virhettä korjattu | `⚠` OMR, sanapeitto 48–59 %, keksittyä sisältöä tahdeissa 59–74 |
| II·10 Lacrymosa | `✔` nuotit kuorotiedostoa vastaan, sanat painetusta sivusta tavutarkkuudella | `○` |
| I Requiem & Kyrie | `◑` sanat tarkistettu PDF:stä, nuotit OMR-tulosta | `○` |
| II·9b Dies irae (kertaus) | `◑` sanat tarkistettu, nuotit tarkistamatta | `○` |

`test_luotettavuus.py` vaatii rivin jokaiselle `OSAOTSIKOT`-listan osalle ja
jokaiselle neljälle äänelle, jotta uusi osa ei voi jäädä hiljaa merkitsemättä.

Sivuston luotettavuussivun yläreunassa sanotaan suoraan: kuorobasso on ainoa
systemaattisesti varmistettu ääni, muut ovat epävarmempia.

## 6. Sivusto

### Sivut

| Sivu | Sisältö | Datan lähde |
|---|---|---|
| `index.html` | Mikä tämä on, mistä aloittaa, linkit | käsin kirjoitettu |
| `teksti.html` | Latina–suomi rinnakkain | `sivusto/requiem.html` |
| `stemmat.html` | 8 stemmaa, sisällystaulukko, latauslinkit | `stemmat-sisallys.txt`, `OSAOTSIKOT`, koko partituurin tahtinumerot |
| `luotettavuus.html` | Mikä on tarkistettu | `luotettavuus.py` |

Menetelmädokumentaatiolle ei tule omaa sivua; `YHDISTAMINEN.md` ja
`CLAUDE.md` luetaan repossa.

### Generaattori

`sivusto.py`, pelkkää vakiokirjastoa kuten muutkin skriptit.

- Osajako ja otsikot luetaan `yhdista.py`:n vakioista (`OSAOTSIKOT`,
  `MOVEMENTS`, `DIES_IRAE_ALUT`), ei toisteta käsin.
- Tahtivälit lasketaan yhdistetyn partituurin omista `<measure number>`
  -arvoista, ei taulukosta joka asetti ne. Sama tarkistustapa kuin muualla
  projektissa.
- Sivunumerot luetaan `stemmat-sisallys.txt`:stä.
- `python3 sivusto.py` kirjoittaa `_sivusto/`-hakemistoon paikallista
  esikatselua varten; sama komento ajetaan CI:ssä.

Sisällystaulukko ei siis voi ajautua erilleen stemmoista, koska molemmat
tulevat samasta lähteestä.

### Ulkoasu

Väri- ja typografiamuuttujat otetaan nykyisestä `requiem.html`:stä
(EB Garamond + Archivo, paperinvärinen pohja, punainen rubriikki) jaettuun
`sivusto/tyyli.css`:ään. **`requiem.html` itse jää sisällöltään
koskemattomaksi**; siihen lisätään vain navigointilinkki muihin sivuihin.
Toimivaa sivua ei refaktoroida.

Stemmasivulle tehdään kustakin stemmasta ensimmäisen sivun pikkukuva
(`mutool draw`). Kuvat committoidaan `sivusto/pikkukuvat/`-hakemistoon, koska
CI:ssä ei ole `mutool`ia eikä MuseScorea. Tämä on koristeellinen lisä ja
ensimmäinen karsittava kohta, jos se osoittautuu hankalaksi.

### Julkaisu

`.github/workflows/sivusto.yml`: ajaa `sivusto.py`:n, kopioi stemma-PDF:t
mukaan ja julkaisee `actions/upload-pages-artifact` +
`actions/deploy-pages` -pareilla.

Generoitua HTML:ää **ei committoida**. Muuten se vanhenee huomaamatta, mikä
on täsmälleen se ongelma jota tämä projekti muuten välttää.

PDF:iä ei voi rakentaa CI:ssä, koska MuseScorea ei siellä ole; ne tulevat
reposta sellaisinaan.

## 7. README ja LICENSE

README suomeksi, tässä järjestyksessä:

1. Mikä tämä on
2. Mitä täältä saa — 8 stemmaa PDF:nä, yhdistetty partituuri, harjoitustiedosto
3. **Luotettavuus** — heti kärkeen, ei alaviitteeksi
4. Miten sen toistaa — ympäristö ja komennot järjestyksessä
5. Hakemistorakenne
6. Nuottien alkuperä ja lisenssi
7. Linkit `YHDISTAMINEN.md`:hen ja `CLAUDE.md`:hen

`LICENSE` = GPL-3.0-or-later. Se kattaa skriptit ja itse kirjoitetun
dokumentaation. Nuotteihin se ei ulotu eikä voi ulottua.

Nuottien alkuperä READMEssä, varmennettu tiedostojen metatiedoista:

- **CPDL-erä** (osat 08–12, 15), Finale 2014 + Dolet, 2015-05-11. Tiedostot
  sanovat itse: *"Copyright © 2009 by the Choral Public Domain Library
  (cpdl.org) — Edition may be freely distributed, duplicated, performed, or
  recorded."*
- **Sibelius-erä** (osat 02–07, 13, 16), Sibelius 7.5.1, 2017-10-10.
  `<rights>` on tyhjä, mutta `<encoder>` on `claud` — sama CPDL-editoija kuin
  PDF-lähteissä.
- **PDF-lähteet** (01, 14, 10b, Lacrymosa): `Author` on `Claude`/`claud`,
  vuosilta 2006–2021.
- Verdi kuoli 1901, joten sävellys on public domainissa.
- `musescore/` on jätetty pois, koska sen tekijyys on tuntematon ja
  tiedostonimissä on kuorolaisten nimiä.

## 8. Historian uudelleenkirjoitus

Kaksi erillistä operaatiota, jotka on syytä pitää erillään.

**Poistot kirjoitetaan historiaan uusiksi** `git-filter-repo`:lla
(`brew install git-filter-repo`, ei asennettuna):

- `musescore/**`
- `harjoitus-*.mscz`
- `Verdi-Requiem-koko-oma.mscz`

**Siirrot tehdään tavallisena committina**, ei historiaan. Jos polut
nimettäisiin uusiksi läpi historian, vanhat commitit muuttuisivat sisäisesti
ristiriitaisiksi: puussa lukisi `lahteet/01-Verdi_Requiem.mxl` mutta saman
commitin `yhdista.py`:ssä edelleen `01-Verdi_Requiem.mxl`. Tavallisena
siirtona jokainen historian commit pysyy itsensä kanssa yhtäpitävänä.

Ennen ajoa koko hakemistosta otetaan täysi kopio. Ajon jälkeen tarkistetaan,
ettei `musescore`-merkkijono esiinny missään historian objektissa.

`.git`:n lopullista kokoa ei luvata etukäteen, vaan se mitataan. Jos se jää
yli 60 MB:n, syy on generoiduissa stemma-PDF:issä (8 × 300 kB × noin 10
uudelleenrenderöintiä) ja asiaan palataan erikseen.

## 9. Testaus

Uudet testit:

- `test_polut.py` — jokainen taulukoissa mainittu tiedostonimi selviää
  hakemistoon, jossa tiedosto oikeasti on
- `test_luotettavuus.py` — rivi jokaiselle osalle ja äänelle
- `test_sivusto.py` — jokainen osa esiintyy sisällystaulukossa, sivunumerot
  vastaavat `stemmat-sisallys.txt`:ää, jokainen sivu syntyy

Olemassa olevat 136 testiä pysyvät vihreinä. Kokonaismäärä nousee arviolta
150:een.

## 10. Järjestys

1. `polut.py`, hakemistorakenne, polkumuutokset — ketju ajetaan ja verrataan
   tavulleen
2. README ja LICENSE
3. `luotettavuus.py`, `sivusto.py`, tyylit, testit
4. Actions-työnkulku
5. `git-filter-repo` varmuuskopion jälkeen — viimeisenä, jotta se ajetaan
   vain kerran
6. Julkaisu GitHubiin nimellä `tuomas2/verdi-requiem`

## 11. Oletukset, jotka voi joutua korjaamaan

| Oletus | Miten muutetaan |
|---|---|
| `tuomasairaksinen.fi/requiem.html` jää ennalleen; sivustolle tulee siitä kopio | Jos vanha osoite halutaan ohjata uuteen, se on yksi rivi vanhalla sivustolla — ei tässä repossa |
| Harjoitustiedostoja ei julkaista ladattavina | Jos halutaan, ne viedään GitHub Releasesiin, ei repoon |
| `CLAUDE.md` julkaistaan sellaisenaan, vain kehysteksti lisätään | Teksti puhuu "the userista" 32 kertaa; laajempi uudelleenkirjoitus olisi oma työnsä ja riskeeraisi virheitä 124 kB:n dokumentissa |
| Pikkukuvat committoidaan, koska CI:ssä ei ole `mutool`ia | Jos ei haluta binäärejä repoon, stemmasivu tulee ilman pikkukuvia |
