# Verdi: Messa da Requiem — kuorostemmat ja yhdistetty partituuri

Verdin *Messa da Requiem* MusicXML-muodossa: kuusitoista erillistä
osatiedostoa yhdistettynä yhdeksi partituuriksi, ja siitä tuotetut kahdeksan
kuorostemmaa harjoittelua varten.

**Aineisto selattavassa muodossa: [requiem.tuomasairaksinen.fi](https://requiem.tuomasairaksinen.fi)**
— stemmat, koko messun teksti latinaksi ja suomeksi, ja osakohtainen tieto
siitä mikä on tarkistettu ja mikä ei.

Lähtökohta on kuorolaisen käytännön tarve: lukea omaa stemmaa niin että muu
kuoro ja pianosäestys kuuluvat, kantaa stemma mukana lukulaitteella, ja
löytää yksittäinen tahti kun kuoronjohtaja huutaa numeron. Siitä seuraa kaksi
vaatimusta, jotka ohjaavat kaikkea muuta: **tahtinumeroiden on täsmättävä
kuoron oman nuottikirjan kanssa**, ja stemman on oltava tiivis.

## Mitä täältä saa

| | |
|---|---|
| `stemmat/stemma-*.pdf` | Kahdeksan stemmaa: S/A/T/B × I/II. Tahtinumero joka tahdin päällä, käynnissä olevan osan nimi joka sivun yläreunassa |
| `johdetut/Verdi-Requiem-koko.mxl` | Koko teos yhtenä partituurina: 15 viivastoa, 1807 tahtia |
| `stemmat/stemmat-sisallys.txt` | Miltä sivulta mikin osa alkaa kussakin kahdeksassa stemmassa |
| `harjoitus.py` | Rakentaa harjoittelutiedoston, jossa oma ääni soi trumpettina ja muut kuuluvat mutta eivät näy |

## Luotettavuus — lue tämä ennen kuin luotat nuottiin

**Kuorobasso on käyty läpi, muut äänet eivät.** Basso on käyty läpi käsin
**Edition Petersin** painosta vasten ja laulettu läpi harjoituksissa, ja
kahdessa osassa lisäksi vertailtu nuotti nuotilta riippumattomaan lähteeseen.
Sopraano, altto ja tenori ovat pääosin tarkistamatta, ja kolmessa osassa
niissä on tiedettyjä virheitä: Liber scriptus, Lacrymosa ja Agnus Dei.

Syy on yksinkertainen: tekijä laulaa bassoa.

**Tahtinumerot täsmäävät Edition Petersin painoksen kanssa.** Dies irae
numeroituu yhtenäisesti läpi kaikkien alaosiensa; muut osat alkavat
ykkösestä.

| Tila | Merkitys |
|---|---|
| ✔ varmistettu | Koko osa vertailtu riippumattomaan lähteeseen nuotti nuotilta ja tavu tavulta |
| ◑ käyty läpi | Käyty läpi käsin painettua editiota vasten ja laulettu harjoituksissa, mutta ei järjestelmällisesti nuotti nuotilta |
| ○ tarkistamatta | Ei tunnettuja virheitä, mutta ei myöskään tarkistettu |
| ⚠ puutteita | Tiedetään virheellistä sisältöä |

Osakohtainen taulukko on tiedostossa [`luotettavuus.py`](luotettavuus.py) ja
luettavassa muodossa sivustolla.

Kaksi asiaa kannattaa tietää tarkistustyöstä, koska ne toistuivat:

- **Painettu nuotti ei ratkaise kaikkea.** Lacrymosan tahdeissa 657–665
  painettu CPDL-editio antaa kuorobassolle väärän tekstin, ja tahdissa 653
  väärän sävelen. Kumpikin paljastui vasta siitä, mitä muut äänet ja
  pianosäestys tekevät samalla iskulla. Painettu etumerkki kertoo varmasti
  minkä nuotin kaivertaja piirsi — ei mitään siitä, oliko se oikea.
- **Konelukemisen (OMR) tulos on eri luokkaa kuin muu aineisto.** Osat 01
  (Requiem & Kyrie) ja 14 (Agnus Dei) sekä II·9b ovat PDF:stä koneluettuja,
  ja niiden nuotit ovat pääosin tarkistamatta.

## Miten sen toistaa

Tarvitset MuseScore 4:n komentoriviltä (`mscore`) ja `mutool`in
(`brew install mupdf-tools`). Python 3.9, ei riippuvuuksia.

```bash
python3 korjaa_sanat.py --kuiva                # OMR-osien sanat: raportoi vain
python3 korjaa_kasin.py                        # käsin todennetut korjaukset
python3 yhdista.py Verdi-Requiem-koko.mxl      # yhdistetty partituuri
python3 yhdista.py stemma-basso-1.mxl --stemma "Basso I"
python3 sivuotsikot.py stemma-basso-1.mxl      # osan nimi joka sivulle
mscore -S tiivistys.mss -o stemmat/stemma-basso-1.pdf stemmat/stemma-basso-1.mxl
python3 sisallys.py                            # sisällysluettelo
python3 -m unittest discover -s testit -t .
```

Kaksi varoitusta, jotka ovat maksaneet aikaa:

- **`korjaa_sanat.py` ilman `--kuiva`-lippua kirjoittaa `-OMR-korjattu.mxl`
  -tiedostot alusta uusiksi**, ja osien 14 ja II·9b käsin tehdyt korjaukset
  elävät vain noissa tiedostoissa. Ajo tuhoaa ne hiljaa. Osat 01, 02, 05, 07,
  11, 13 ja 16 ovat turvassa, koska niiden käsityö on taulukkona
  `korjaa_kasin.py`:ssä.
- **`mscore` kaatuu noin joka kolmas ajo sammutusvaiheessa** (exit 134)
  kirjoitettuaan täyden PDF:n. Tarkista tulos sivumäärästä, älä
  paluuarvosta, äläkä laita sitä `set -e`:n alle.

## Hakemistot

Nuottiaineisto on neljässä hakemistossa, jotka vastaavat datan kulkusuuntaa.
Skriptit puhuvat paljaista tiedostonimistä; `polut.py` selvittää hakemiston
nimestä, joten komennot toimivat sekä nimellä että täydellä polulla.

| | |
|---|---|
| `lahteet/` | Alkuperäiset CPDL-tiedostot, lähde-PDF:t ja Audiveris-projektit. Näitä ei muokata |
| `johdetut/` | Skriptien tuottamat korjatut osat ja yhdistetty partituuri |
| `stemmat/` | Kahdeksan stemmaa ja niiden sisällysluettelo |
| `sivusto/` | Verkkosivuston lähteet |
| `testit/` | Testit. Aja repon juuresta, koska polut ovat suhteellisia |

    lahteet/ ──korjaa_sanat.py──> johdetut/
    lahteet/ ─┐
              ├─korjaa_kasin.py─> johdetut/
    johdetut/ ┘
    johdetut/ ──yhdista.py──────> johdetut/ (koko partituuri) ja stemmat/

## Nuottien alkuperä

Sävellys on public domainissa; Verdi kuoli 1901. Nuottiaineisto on CPDL:n
(Choral Public Domain Library) editioita kahdesta erästä, ja erän tunnistaa
tiedostonimen väliviivasta tai alaviivasta — **niitä ei siis pidä
normalisoida**:

- `Verdi-*` — Sibelius 7.5.1, 10.10.2017. Osat 02–07, 13 ja 16.
- `Verdi_*` — Finale 2014 + Dolet, 11.5.2015. Osat 08–12 ja 15. Nämä
  tiedostot sanovat itse: *"Copyright © 2009 by the Choral Public Domain
  Library (cpdl.org) — Edition may be freely distributed, duplicated,
  performed, or recorded."*

Lähde-PDF:ien (osat 01, 14, II·9b ja Lacrymosa) tekijätunnus on sama
`claud`/`Claude` kuin MusicXML-tiedostojen `<encoder>`-kentässä, eli sama
CPDL-editoija.

## Lisenssi

Skriptit ja tässä repossa kirjoitettu dokumentaatio: **GPL-3.0-or-later**,
ks. [`LICENSE`](LICENSE). Lisenssi ei ulotu eikä voi ulottua CPDL:n
editioihin, jotka ovat oman lisenssinsä alaisia.

Kuoron omat MuseScore-harjoitustiedostot on jätetty pois kokonaan: niiden
tekijyys on tuntematon ja tiedostonimissä oli laulajien nimiä. Niitä on
käytetty tarkistuslähteenä, ja `korjaa_kasin.py`:n kommentit kertovat missä.

## Lue lisää

- [`YHDISTAMINEN.md`](YHDISTAMINEN.md) — miten yhdistäminen toimii, mitä
  oletuksia siinä on tehty ja miten ne muutetaan
- [`CLAUDE.md`](CLAUDE.md) — täydellinen tekninen työpäiväkirja: jokainen
  löydetty virhe, miten se löytyi, ja mitkä menetelmät kokeiltiin ja
  hylättiin. Englanniksi
