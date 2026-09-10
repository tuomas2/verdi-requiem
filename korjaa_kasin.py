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
import copy
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from dataclasses import dataclass

from korjaa_sanat import find_part, load, save
# Sanarivin numero luetaan ennen yhdista.py:n normalisointia, joten
# lähteen oma kirjoitusasu ("2" tai "part8verse2") on vielä näkyvissä.
from suomennos import rivinumero


@dataclass(frozen=True)
class Osa:
    """Yksi osa: mistä luetaan, mihin kirjoitetaan, mitä korjataan."""

    mxl: str            # lähde, jota ei koskaan muokata
    out: str            # tulos, jonka yhdista.py lukee
    osasto: str         # osaston tunnus lähteessä
    nimi: str           # viivaston nimi raporttiin
    yksi_sanarivi: bool  # nostetaanko kaikki tavut sanariville 1
    korjaukset: tuple   # (tahti, nuotti, toimenpide, argumentit...)


@dataclass(frozen=True)
class Savellaji:
    """Sävellajin vaihdon siirto väärästä tahdista oikeaan.

    Tämä ei ole yhden viivaston korjaus vaan koko tiedoston. Sävellaji on
    merkitty jokaisen osaston omaan tahtiin erikseen, joten jos vaihto
    siirretään vain kuorobassossa, partituurin viivastot vaihtavat
    sävellajia eri tahdeissa — ja stemmat keskenään eri kohdassa.
    """

    mxl: str            # lähde, jota ei koskaan muokata
    out: str            # tulos, jonka yhdista.py lukee
    siirrot: tuple      # (väärä tahti, oikea tahti, fifths)
    valmiit: tuple = ()  # osastot joissa vaihto on jo oikeassa tahdissa


# Toimenpiteet:
#   ("poista", teksti)                  poista tavu, jonka teksti on tämä
#   ("lisaa", syllabic, teksti)         lisää tavu nuotille jolla ei ole
#   ("aseta", vanha, syllabic, teksti)  korvaa tavu toisella
#   ("tavutus", "Do-na e-is ...")        korjaa tavuketju tahdista eteenpäin
#   ("jatka",)                          lisää tavuun melisman jatkoviiva
#   ("korkeus", vanha, uusi)            vaihda nuotin korkeus, esim. "A3"->"A2"
#   ("kesto", vanha, uusi)              vaihda nuottiarvo, esim.
#                                       "256/quarter" -> "192/eighth."
#                                       (piste per pisteellisyys)
#   ("lisaa_aksentti",)                 lisää aksentti nuotille jolla ei ole
#   ("poista_aksentti",)                poista nuotin aksentti
#   ("poista_nuotti", kuvaus)           poista nuotti tai tauko
#   ("lisaa_tauko", arvo, summa)        lisää tauko nuotin i ETEEN, esim.
#                                       "8/half", ja tarkista että äänen
#                                       kestojen summa on jäljestäpäin annettu
#                                       summa — tauon lisäys muuttaa tahdin
#                                       pituutta, joten oikea pituus pitää
#                                       sanoa ääneen eikä päätellä
#   ("sanarivi", vanha, uusi)           siirrä tahdin tavut toiselle
#                                       sanariville, esim. "2" -> "1"
#   ("vaihda_sanarivit", a, b)          vaihda kahden sanarivin tavut
#                                       keskenään, esim. "1" <-> "2"
#   ("dynamiikka", merkki)              lisää dynamiikkamerkintä tahdin
#                                       alkuun, esim. "p"
#   ("kopioi_tahti", lähdetahti)        korvaa tauolla oleva tahti toisen
#                                       tahdin sisällöllä, sanat mukaan lukien
# Nuotti on indeksi tahdin <note>-alkioissa, tauot mukaan luettuina, tai None
# kun toimenpide koskee koko tahtia.
#
# Sävellajin vaihdon paikka ei ole yhden viivaston asia, joten se ei kulje
# `korjaukset`-rivillä vaan `SAVELLAJIT`-taulukossa OSAT:n jäljessä.
#
# `kesto` muuttaa tahdin sisäistä jakoa, joten sovella() tarkistaa jokaisesta
# tahdista jota se koskee, että äänen kestojen summa on jäljestäpäin sama kuin
# ennen: rytmin uudelleenjako ei saa lyhentää eikä pidentää tahtia.

OSA_I = Osa(
    mxl="01-Verdi_Requiem-OMR-korjattu.mxl",
    out="01-Verdi_Requiem-kasin.mxl",
    osasto="P16",
    nimi="Kuoro B",
    # Kuorobassolla on osan I PDF:ssä yksi tekstirivi alusta loppuun, mutta
    # konelukema hajotti 55 tavua riville 2.
    yksi_sanarivi=True,
    korjaukset=(
        # Sivu 2: tahdissa 40 on vain puolinuotti B♭3 tavulla "ex", eli tahti
        # on 2/4 neljästä neljäsosasta. Alusta puuttuu puolitauko: kuoron
        # omassa tiedostossa tahti on puolitauko + B♭3, ja kuorotenorin oma
        # "ex" on tahdin 39 neljännellä iskulla, joten porrastettu sisääntulo
        # on juuri sitä mitä musiikki tekee. Sisääntulo kuuluu kolmannelle
        # iskulle. Löytyi 2026-09-10 pianokartoituksen sivutuotteena; tahtien
        # 1-78 sävelvertailu ei voinut löytää tätä, koska puuttuva tauko ei
        # muuta yhtään säveltä.
        ("40", 0, "lisaa_tauko", "8/half", "16"),

        # Sivu 2: "o-ra-ti-o-nem me-am," päättyy tähän, joten "am" on sanan
        # viimeinen tavu eikä keskimmäinen. Väärä syllabic jättää tavuviivan
        # roikkumaan seuraavan tavun perään.
        ("49", 0, "aseta", "am", "end", "am"),

        # Sivu 3: "ad te om-nis ca-ro ve-ni-et." Laulaja pyysi 2026-09-02
        # melisman tavulle "om", jolloin "nis" siirtyi tahdin 52 viimeiselle
        # nuotille — mutta lähde-PDF merkitsi sen toisin päin, ja se kirjattiin
        # kommenttiin yhtenä rivinä peruttavaksi. 2026-09-10 laulaja luki
        # kuoron nuottikirjaa: "nis" on tahdin 51 toisella nuotilla ja
        # jatkoviiva sen perässä ulottuu tahdin 52 viimeiseen nuottiin asti.
        # Kirja on siis PDF:n kannalla. Lähde merkitsee tavun jo oikein, joten
        # siirtorivit ovat poissa ja jäljelle jää melisman jatkoviiva.
        ("51", 1, "jatka"),

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

# Osan I kuorosopraano, altto ja tenori. Kuorobasson tekstin korjaukset ovat
# yllä; nämä kolme jäivät 2026-09-09 asti koskematta. Kaksi eri lähdettä
# todistaa kaiken alla olevan, eikä kummankaan lukemista tarvitse arvata:
#
#   * Lähde-PDF:n oma tekstikerros. `korjaa_sanat.py` lukee sen jo, mutta
#     sen kohdistus liukui näissä paikoissa, joten se jätti tavut ennalleen
#     ("kohdistamatta"-rivit sen raportissa). Sanarivit ovat PDF:ssä
#     järjestyksessä ylhäältä alas, ja kolmannen järjestelmän neljä
#     kuororiviä sivulla 1 lukevat kaikki "-pe-tu-a, et lux per-pe-tu-a
#     lu-ce-at ...", eli sama säe joka äänessä.
#   * Kuoron oma MuseScore-tiedosto (musescore/01_requiem), jossa ei ole
#     sanoja lainkaan mutta sävelet ovat oikein.
#
# Sanat: konelukema hajotti sanan "et lux per-pe-tu-a" tavuja kolmessa
# äänessä. Kuorobasso ja tenori laulavat sen tahdeissa 17-19 ja 21-22,
# sopraano ja altto samat tahdit — sama kuvio, sama teksti, ja bassossa se
# on jo oikein, joten jokainen korjaus on luettavissa suoraan viereiseltä
# viivastolta.
OSA_I_SOPRAANO = Osa(
    mxl=OSA_I.mxl,
    out=OSA_I.out,
    osasto="P13",
    nimi="Kuoro S",
    # Sopraanolla on tavuja kahdella äänellä (t.65 "Do-mi" on äänessä 2),
    # joten yksi_sanarivi ei kelpaa: sen tarkistus estää nostamisen, kun
    # päällekkäisyys olisi mahdollinen. Rivit siirretään tahti kerrallaan.
    yksi_sanarivi=False,
    korjaukset=(
        # Sivu 2, 1. järjestelmä: "Te de-cet hym-nus, De-us in Si-on, et
        # ti-bi red-de-tur vo-". Koko säe on konelukemassa sanarivillä 2,
        # joten stemmaan tulostuu tyhjä ylärivi ja teksti sen alle.
        ("35", None, "sanarivi", "2", "1"),
        ("36", None, "sanarivi", "2", "1"),
        ("38", None, "sanarivi", "2", "1"),
        ("39", None, "sanarivi", "2", "1"),
        ("40", None, "sanarivi", "2", "1"),
        ("41", None, "sanarivi", "2", "1"),

        # Sivu 3, 2. järjestelmä: "Re-qui-em," — keskimmäinen tavu yksin
        # rivillä 2, eli sana katkeaa kahdelle tekstiriville. Sama vika kuin
        # kuorobasson tahdissa 108 (2026-09-04), mutta datassa eikä
        # yhdista.py:ssä.
        ("59", 2, "sanarivi", "2", "1"),

        # Sivu 1, 3. järjestelmä: "et lux per-pe-tu-a".
        ("21", 0, "aseta", "lg},", "single", "et"),
        ("21", 1, "aseta", "ux", "single", "lux"),
        ("22", 1, "aseta", "tll", "middle", "tu"),

        # Sivu 2, 1. järjestelmä, tahdit 28-34: konelukema luki tämän
        # jakson kolmen ristin sävellajissa, koska se näki F-duurin vaihdon
        # vasta seuraavan järjestelmän alusta (ks. SAVELLAJIT). Sävellaji on
        # syy, väärät sävelet vahinko: kuoron oma tiedosto laulaa "Te de-cet
        # hym-nus" F-duurissa, ja se on näiden seitsemän nuotin ainoa ero
        # koko osan sopraanossa ja altossa.
        ("28", 0, "korkeus", "Fis4", "F4"),
        ("28", 1, "korkeus", "Fis4", "F4"),
        ("34", 0, "korkeus", "Cis5", "C5"),

        # Sivu 4, tahti 76, neljäs nuotti: konelukema luki palautusmerkin
        # b:ksi ja kirjasi Ces5:n. Sivu 4 mitattuna (nuottifontin merkit,
        # ks. SAVELLAJIT-kommentti) sopraanoviivastolla on tahdin 76 x:llä
        # 304,6 palautusmerkki ja x:llä 307,9 nuottipää C5:n korkeudella.
        # Kuoron oma tiedosto laulaa saman C5:n palautusmerkillä.
        ("76", 3, "korkeus", "Ces5", "C5"),
    ),
)

OSA_I_ALTTO = Osa(
    mxl=OSA_I.mxl,
    out=OSA_I.out,
    osasto="P14",
    nimi="Kuoro A",
    # Altossa tavut ovat yhdellä äänellä mutta kuudella sanarivillä (1, 2,
    # 4, 5, 6, 8): konelukema numeroi rivit uudelleen aina kun se hukkasi
    # ketjun. Yksikään nuotti ei kanna kahta tavua sen jälkeen kun t.136:n
    # dynamiikkamerkintä on poistettu, joten kaikki nousevat riville 1.
    yksi_sanarivi=True,
    korjaukset=(
        # Sivu 10: "PPP" on dynamiikkamerkintä, ei tavu. Konelukema pani sen
        # sanariville 2 saman nuotin päälle jolla on tavu "e".
        ("136", 0, "poista", "PPP"),

        # Sivu 1, 3. järjestelmä: "et lux per-pe-tu-a".
        ("21", 0, "aseta", "eh,", "single", "et"),
        ("21", 1, "aseta", "luX", "single", "lux"),
        ("21", 2, "aseta", "er", "begin", "per"),
        ("22", 0, "aseta", "pe.", "middle", "pe"),

        # Sivu 2, 2. järjestelmä: altto laulaa "-us in Si-on, et ti-bi
        # red-de-tur, ti-bi red-de-tur", joten tahdin 37 tavu on "et".
        # HUOM: `korjaa_sanat.py` ehdottaa samaan tahtiin tätä ja lisäksi
        # t.39 "ti" -> "vo", jota se ei sovella. Toinen ehdotus on väärä —
        # PDF:n alttorivi kertaa "ti-bi red-de-tur" eikä jatka sanaan
        # "vo-tum" — joten vain tämä kirjataan.
        ("37", 1, "aseta", "at", "single", "et"),

        # Tahdit 32-33, sama sävellajin aiheuttama vahinko kuin sopraanolla.
        ("32", 0, "korkeus", "Fis4", "F4"),
        ("32", 1, "korkeus", "Gis4", "G4"),
        ("33", 0, "korkeus", "Gis4", "G4"),
        ("33", 1, "korkeus", "Fis4", "F4"),
    ),
)

OSA_I_TENORI = Osa(
    mxl=OSA_I.mxl,
    out=OSA_I.out,
    osasto="P15",
    nimi="Kuoro T",
    yksi_sanarivi=True,
    korjaukset=(
        # Sivu 10: dynamiikkamerkintä tavuna, kuten altolla.
        ("136", 0, "poista", "ppp"),

        # Sivu 1, 2. järjestelmä: "et lux per-".
        ("17", 2, "aseta", "e", "single", "et"),
        ("18", 0, "aseta", "ux", "single", "lux"),
        ("19", 2, "aseta", "er", "begin", "per"),

        # Sivu 3, 3. järjestelmä: "et lux per-pe-tu-a" toisen kerran.
        ("67", 2, "aseta", "e", "single", "et"),
        ("70", 0, "aseta", "e", "middle", "pe"),

        # Sivu 4: "lu-ce-at e-is." — konelukema luki l:n ja u:n isoksi I:ksi
        # ja n:ksi. Kaikki neljä kuororiviä lukevat siinä järjestelmässä
        # "lu-ce-at e-is.".
        ("76", 1, "aseta", "In", "begin", "lu"),

        # Sivu 2, tahti 43, toinen nuotti: risti puuttuu. Sivu mitattuna
        # tenoriviivastolla on x:llä 181,4 risti ja heti sen perässä x:llä
        # 185,3 nuottipää C5:n korkeudella; tahti 43 alkaa x:llä 146.
        # Kuoron oma tiedosto laulaa Cis5:n, ja sen ja meidän tenorin
        # tahdit 39-46 täsmäävät muuten nuotti nuotilta.
        ("43", 1, "korkeus", "C5", "Cis5"),
    ),
)

# Dies irae (II·1), tahti 28. Laulaja raportoi 2026-09-04, että tahdin toinen
# nuotti on oktaavia alempi A. Sama havainto oli jo kirjattu avoimena
# 2026-09-03: kuoron oma tiedosto (musescore/02_dies_irae) laulaa siellä A2:n
# ja sen Bass 2 on tauolla, joten kyse ei ole divisistä.
#
# Kaksi asiaa vahvistaa lukeman. Ensin: kuorotiedoston Bass 1 ja meidän P4
# täsmäävät koko osan 91 tahdista 90:ssä ja tahti 28 on niiden AINOA ero.
# Toiseksi kuvio on osan sisällä johdonmukainen: sama "puolinuotti + oktaavia
# alempi kahdeksasosa" -kadenssi toistuu tahdeissa 32 (C4->C3), 34
# (Bes3->Bes2) ja 36 (Aes3->Aes2). Tahti 24 (A3->A3) ei putoa oktaavia, ja
# sekin on molemmissa tiedostoissa sama — eli poikkeus on aito eikä vika.
# Osalla 02 ei ole lähde-PDF:ää, joten silmällä tarkistettavaa sivua ei ole.
OSA_II1 = Osa(
    mxl="02-Verdi-Dies_irae.mxl",
    out="02-Verdi-Dies_irae-kasin.mxl",
    osasto="P4",
    nimi="Kuoro B",
    yksi_sanarivi=False,
    korjaukset=(
        ("28", 1, "korkeus", "A3", "A2"),   # "Sy-bil-la," viimeinen tavu
    ),
)

# Liber scriptus, paikalliset tahdit 68, 70 ja 72 (juoksevat 229, 231 ja 233):
# kuoron lyhyt "Di-es i-rae." -välihuudahdus puuttui kokonaan kaikilta
# neljältä ääneltä. Lähdetiedostossa on kolme näistä kuudesta (paikalliset
# 16, 30 ja 52) ja loput kolme olivat pelkkää taukoa.
#
# Puuttuvat kohdat paikannettiin kuoron omasta tiedostosta
# (musescore/02_dies_irae): sen basso laulaa kuusi kertaa yksittäisen tahdin
# mittaisen kuvion, ja sen mezzostemma osuu meidän mezzoomme 42 tahtia
# putkeen (kuorotiedoston 136-177 = paikalliset 64-105), joten kuorotiedoston
# tahdit 140, 142 ja 144 ovat yksikäsitteisesti paikalliset 68, 70 ja 72.
# Kaikki kuusi esiintymää ovat molemmissa tiedostoissa nuotilleen samat
# (S ja A D4:llä, T ja B D3:lla), joten korjaus on olemassa olevan tahdin
# kopio eikä mitään tarvitse keksiä.
LIBER_SCRIPTUS_MALLI = "52"
LIBER_SCRIPTUS_PUUTTUVAT = ("68", "70", "72")
OSAT_II4 = [
    Osa(mxl="05-Verdi-Liber_scriptus.mxl",
        out="05-Verdi-Liber_scriptus-kasin.mxl",
        osasto=pid, nimi=nimi, yksi_sanarivi=False,
        korjaukset=tuple((tahti, None, "kopioi_tahti", LIBER_SCRIPTUS_MALLI)
                         for tahti in LIBER_SCRIPTUS_PUUTTUVAT))
    for pid, nimi in (("P2", "Kuoro S"), ("P3", "Kuoro A"),
                      ("P4", "Kuoro T"), ("P5", "Kuoro B"))
]

# Rex tremendae (II·6). Paikalliset tahdit ovat juokseva miinus 321.
#
# 1. Tahti 45 (juokseva 366). Laulaja raportoi, että tahdin ensimmäisellä
#    nuotilla pitää olla "me" eikä "le" — teksti on "sal-va me".
#    Kirjoitusvirhe lähdetiedostossa, ja se näkyy siitä että kuorosopraano
#    (P5) laulaa samassa tahdissa samalla iskulla "me,". Basson ympäristö on
#    jo oikein: t.44 "sal-va", t.45 "sal-va", t.46 "me,".
#
# 2. Tahdit 19-20 ja 41-42 (juoksevat 340-341 ja 362-363). Laulaja raportoi
#    2026-09-09, että kuorobasso laulaa t.340-341 "qui sal-van-dos sal-vas
#    gra-tis" eikä kolmatta kertaa "Rex tre-men-dae ma-je-sta-tis", ja
#    t.362-363 "sal-va me fons pi-e-ta-tis" eikä toista kertaa "qui
#    sal-van-dos sal-vas gra-tis". Kumpikin on säkeistön oma järjestys:
#    "Rex tremendae majestatis, qui salvandos salvas gratis, salva me fons
#    pietatis."
#
#    Osalla 07 ei ole lähde-PDF:ää, joten silmällä tarkistettavaa sivua ei
#    ole. Tiedosto todistaa kumpaakin kohtaa itse:
#
#      * Kuvio on kaikissa neljässä paikassa sama — kuusi nuottia tahdissa,
#        kaksi seuraavassa — ja kumpikin säe on kahdeksan tavua. Sekä
#        tavutus että välimerkit kopioidaan tiedoston omista paikoista,
#        joissa juuri nämä säkeet ovat jo tälle kuviolle merkittyinä:
#        t.360-361 "qui sal-van-dos sal-vas gra-tis," ja t.344-345 "sal-va
#        me, fons pi-e-ta-tis,". Mitään ei siis keksitä.
#      * Korjattuna kumpikin jakso lukee säkeistön läpi kertaamatta yhtä
#        säettä kolmesti: t.336-341 "Rex ... Rex ... qui salvandos salvas
#        gratis" ja t.356-363 "rex ... rex ... qui salvandos salvas gratis
#        ... salva me fons pietatis". Ennen korjausta ensimmäinen säe oli
#        kolmesti ja toinen kahdesti, ja kolmas säe puuttui ensimmäisestä
#        jaksosta kokonaan.
#      * Muut kuoroäänet eivät laula näitä säkeitä lainkaan — ne ovat samaan
#        aikaan "sal-va me" -huudoissa — joten äänten välinen vertailu ei
#        tähän päde. Vertailukohta on osan sisällä.
#
#    Kummankin säkeen viimeinen tavu jää ilman riviä: se on molemmissa
#    säkeissä jo "tis," ja syllabic "end".
#
# 3. Tahdit 46-48 (juoksevat 367-369), divisin sanarivit. Ks. rivien oma
#    kommentti taulukossa.
OSA_II6 = Osa(
    mxl="07-Verdi-Rex.mxl",
    out="07-Verdi-Rex-kasin.mxl",
    osasto="P8",
    nimi="Kuoro B",
    yksi_sanarivi=False,
    korjaukset=(
        # t.340-341: "Rex tremendae majestatis" -> "qui salvandos salvas
        # gratis" (tavutus t.360-361:stä).
        ("19", 0, "aseta", "Rex", "single", "qui"),
        ("19", 1, "aseta", "tre", "begin", "sal"),
        ("19", 2, "aseta", "men", "middle", "van"),
        ("19", 3, "aseta", "dae", "end", "dos"),
        ("19", 4, "aseta", "ma", "begin", "sal"),
        ("19", 5, "aseta", "je", "end", "vas"),
        ("20", 0, "aseta", "sta", "begin", "gra"),

        # t.362-363: "qui salvandos salvas gratis" -> "salva me fons
        # pietatis" (tavutus t.344-345:stä).
        ("41", 0, "aseta", "qui", "begin", "sal"),
        ("41", 1, "aseta", "sal", "end", "va"),
        ("41", 2, "aseta", "van", "single", "me,"),
        ("41", 3, "aseta", "dos", "single", "fons"),
        ("41", 4, "aseta", "sal", "begin", "pi"),
        ("41", 5, "aseta", "vas", "middle", "e"),
        ("42", 0, "aseta", "gra", "middle", "ta"),

        ("45", 0, "aseta", "le,", "single", "me,"),

        # Divisi t.367-369 (paikalliset 46-48): sanarivit olivat päittäin,
        # ja tässä ne olivat sen lisäksi eri puolilla viivastoa. Ylä-ääni
        # (ykkösbasso, tahdin ääni 1) oli rivillä 2, ja lähteen oma
        # default-y="38" nosti sen tavut viivaston YLÄPUOLELLE; ala-äänen
        # (kakkosbasso) rivi 1 jäi default-y="-79":llä alapuolelle. Laulaja
        # raportoi 2026-09-09, että ykkösbasson osuus on viivaston
        # yläpuolella ja kuuluisi johdonmukaisesti alapuolelle,
        # kakkosbasson tekstin yläpuolelle.
        #
        # Sama vika ja sama ratkaisu kuin Lacrymosan t.677-679 (2026-09-07,
        # ks. OSA_II10_DIVISI): rivi kertoo kummasta äänestä on kyse, joten
        # se on sisältöä eikä asettelua, ja ylä-ääni kuuluu ylemmälle
        # riville. Erona on että tässä molemmat äänet ovat samassa
        # osastossa, joten rivit vaihdetaan yhdellä rivillä eikä kahden
        # osaston `sanarivi`-siirroilla.
        #
        # T.369 on mukana, vaikka laulaja mainitsi 367-368: siinä molempien
        # äänten tavu on sama "me,", joten järjestys ei näy — mutta rivin 2
        # default-y nostaisi ykkösbasson "me,":n yhä viivaston yläpuolelle
        # kahden alapuolisen tahdin jälkeen.
        ("46", None, "vaihda_sanarivit", "1", "2"),    # t.367
        ("47", None, "vaihda_sanarivit", "1", "2"),    # t.368
        ("48", None, "vaihda_sanarivit", "1", "2"),    # t.369

        # T.22 (juokseva 343), toinen nuotti. Kuvio on kolme kertaa sama:
        # päänuotti, puolisävelaskel alta, päänuotti takaisin. T.21
        # "Bes3 A3 Bes3" ja t.23 "C4 B3 C4" ovat sitä, mutta t.22 lukee
        # "Ces4 Aes3 Ces4" — alanuotti on iso terssi eikä puolisävelaskel.
        # Kolme todistetta: kuoron oma tiedosto (musescore/03_rex_tremendae)
        # laulaa Bes3:n, viereiset tahdit kertovat kuvion, ja päänuottien
        # sarja nousee Bes3 - Ces4 - C4, joten alanuotti nousee mukana.
        # Tämä on osan 07 kuorobasson AINOA sävelero kuorotiedostoon
        # nähden koko osassa (174 nuottia).
        ("22", 1, "korkeus", "Aes3", "Bes3"),
    ),
)

# Rex tremendae (II·6), kuorotenori. Tenoriviivastolla on kolme ääntä
# (kuoron omassa tiedostossa Tenor 1-3), joten sointuja ei voi verrata
# suoraan; ylin ääni vastaa Tenor 1:tä ja täsmää 150 nuotista kaikissa
# paitsi yhdessä.
#
# T.32 (juokseva 353), ensimmäinen nuotti. Tenori ja basso laulavat
# t.27-32 unisonossa "sal-va me" kolmesti: C#3 C#3 C#3, E3 E3 E3, C3 C3
# C3. Tenorin kolmannen kerran viimeinen nuotti on C4, oktaavia liian
# korkealla. Neljä todistetta: oma kuorobasso t.32 laulaa C3:n, kuoron oma
# tiedoston Tenor 1 laulaa C3:n, ja kaksi edellistä kertaa (t.28, t.30)
# päättyvät samaan säveleen kuin alkavat.
OSA_II6_TENORI = Osa(
    mxl=OSA_II6.mxl,
    out=OSA_II6.out,
    osasto="P7",
    nimi="Kuoro T",
    yksi_sanarivi=False,
    korjaukset=(
        ("32", 0, "korkeus", "C4", "C3"),
    ),
)

# Dies irae (kertaus) (II·9b), paikallinen tahti 35 = juokseva 607. Laulaja
# pyysi 2026-09-09 tahdin alkuun p:n. Kuorobasson viivastolla lukee tässä
# vaiheessa yhä ff, joka on merkitty t.575:een eikä vaihdu koko osassa
# kertaakaan — ja juuri niin laulaja sen kuvasikin ("se tulee aika fortella
# sitä ennen mut se on hiljaa").
#
# Vaihdos on lähteessä olemassa, mutta väärällä viivastolla laulajan
# kannalta: piano (P5) saa ff:n t.604 ja p:n t.606. Kuoro on t.606 tauolla,
# joten sen oma merkintä kuuluu tuloon eli tahtiin 607. Kuoroäänten
# dynamiikka on tässä osassa muutenkin konelukemisen varassa ja vaillinainen
# — S/T/piano saavat f:n t.593, kuorobasso ei — joten puuttuva merkki on
# odotettava eikä yllättävä.
#
# Tämä on osan 10b ensimmäinen käsin todennettu korjaus, ja se tarvitsi
# osalle oman kerroksen: aiemmin sen ainoa johdettu tiedosto oli
# -OMR-korjattu.mxl, jonka `korjaa_sanat.py` kirjoittaa alusta joka ajolla.
# Nyt ketju on 10b-...-OMR.mxl -> -OMR-korjattu.mxl -> -kasin.mxl, sama kuin
# osalla I, ja tämä merkintä säilyy korjaa_sanat-ajon yli.
#
# Sivuhavainto samasta työstä, mitattuna: osan 10b -OMR-korjattu.mxl on
# puhdas johdannainen. `korjaa_sanat.py`-ajo tuottaa sen tavulleen samana,
# joten toisin kuin dokumentaatio on kuukauden sanonut, siinä ei ole
# käsimuokkauksia hukattavana — vaarassa on vain osa 14. Ks.
# docs/menetelmat/omr.md.
# Sanan "Sy-bil-la" tavuviiva puuttuu kaikista neljästä äänestä: tavu "Sy"
# on merkitty itsenäiseksi sanaksi ja "bil" seuraavan sanan alkuun, joten
# stemmaan tulostuu "Sy bil-la,". Syy on lähde-PDF:n omassa tekstikerroksessa:
# neljästä sanarivistä kolme lukee "Sy-bil--la," ja yksi (ylin) "Sy bil--la,"
# ilman ensimmäistä viivaa, joten `korjaa_sanat.py`:n tavutusäänestys ei
# nähnyt sanaa yhtenä lainkaan ja jätti "Sy":n itsenäiseksi joka äänessä.
# Kolme riviä neljästä ja sana itse (Sibylla) kertovat oikean tavutuksen.
SYBILLA = (
    ("27", 2, "aseta", "Sy", "begin", "Sy"),
    ("28", 0, "aseta", "bil", "middle", "bil"),
)

OSA_II9B = Osa(
    mxl="10b-Verdi_Dies_irae_paluu-OMR-korjattu.mxl",
    out="10b-Verdi_Dies_irae_paluu-kasin.mxl",
    osasto="P4",
    nimi="Kuoro B",
    yksi_sanarivi=False,
    korjaukset=(
        ("35", None, "dynamiikka", "p"),               # t.607

        # t.607, tavut "di-es". Konelukema antoi molemmille nuotille puhtaan
        # G:n; kuoron oma MuseScore-tiedosto laulaa G♭:n. Sävellaji on -2
        # (B♭, E♭), joten G♭ vaatii painetun b-merkin, eikä tämän osan
        # lähde-PDF:n etumerkkejä pysty lukemaan koordinaateista (osajoukko-
        # fontti, private-use-koodipisteet). 2026-09-10 laulaja luki kohdan
        # kuoron nuottikirjasta: siellä on G♭. Kuoron tiedosto oli oikeassa.
        ("35", 0, "korkeus", "G3", "Ges3"),
        ("35", 1, "korkeus", "G3", "Ges3"),
    ) + SYBILLA,
)

OSAT_II9B_SAT = [
    Osa(mxl=OSA_II9B.mxl, out=OSA_II9B.out, osasto=pid, nimi=nimi,
        yksi_sanarivi=False,
        korjaukset=SYBILLA + lisaa)
    for pid, nimi, lisaa in (
        ("P1", "Kuoro S", ()),
        # Altolta puuttuu sana "cum" kokonaan. Tahdin rakenne on sama kuin
        # sopraanolla ja bassolla — tauko, nuotti, nuotti — ja niissä "cum"
        # on toisella nuotilla, joten paikka ei ole arvaus. PDF:n neljä
        # sanariviä lukevat kaikki "te-ste Da-vid cum Sy-bil--la,".
        # Kuorotenorin sama puute on jätetty auki: sen tahdissa on neljä
        # nuottia eikä kolme, joten tavun paikkaa ei voi lukea muista
        # äänistä.
        ("P2", "Kuoro A", (("27", 1, "lisaa", "single", "cum"),)),
        ("P3", "Kuoro T", ()),
    )
]

# Lacrymosa (II·10). Sanakerros on CPDL:n lähteessä väärä kahdessa äänessä,
# ja kyse ei ole konelukemasta: tämä tiedosto tulee Finale + Dolet -erästä,
# jota pidettiin luotettavana.
#
# 1. Kuorobasso P8, tahdit 54-75. Tiedostossa lukee siellä osan OMAN aiemman
#    kohdan teksti ("La-cry-mo-sa di-es il-la ... hu-ic er-go par-ce") niiden
#    tahtien päällä, jotka oikeasti laulavat "do-na e-is re-qui-em ... A-men."
#    Nuotit ovat alla oikein; vain tavut ovat väärät.
#
# 2. Divisin ylä-ääni P9, tahdit 54-56. Sama vika, ja se jäi aiemmin
#    korjaamatta, koska lähde-PDF:n oikeaa sanariviä ei tunnistettu: sivulla 11
#    kuorobasson viivastolla on kaksi ääntä ja kaksi sanariviä, ja ylä-äänen
#    sanat ("Pi-e Je-su Do-mi-ne,") on painettu viivaston YLÄPUOLELLE, mistä
#    ne on helppo lukea tenorin riviksi. Ala-äänen "Pi-e Je-su" on alapuolella.
#
# Kaikki 50 tavua on todennettu lähde-PDF:ää (Verdi_Lacymosa.pdf) vasten tavu
# tavulta eikä vain tekstijonona. PDF:n sanat ovat oikeaa tekstiä, joten
# jokaisen tavun x on mitattavissa; muiden äänten sanarivit toimivat
# viivaimena, jolla kuorobasson tavun paikka ennustetaan nuotin default-x:stä.
# Jokainen tavu osuu lähimmin juuri sille nuotille jolle se on merkitty.
# Menetelmä: CLAUDE.md, *Lacrymosa: koko kuorobasso todennettu lähdesivuja
# vasten*.
#
# Tahtinumerot ovat tiedoston omia (lokaaleja). Kommenttien t.NNN on kuoron
# nuottikirjan juokseva numero, eli lokaali + 623.
OSA_II10_KUORO_B = Osa(
    mxl="11-Verdi_Lacrymosa.mxl",
    out="11-Verdi_Lacrymosa-kasin.mxl",
    osasto="P8",
    nimi="Kuoro B",
    yksi_sanarivi=False,
    korjaukset=(
        # --- t.653: painettu sivu on väärässä, kaikki muu sanoo C ---
        #
        # Laulaja raportoi 2026-09-04, että "De-us."-sanan viimeinen nuotti on
        # C eikä G. Tämä oli 2026-09-03 tarkistettu ja ratkaistu VÄÄRIN meidän
        # hyväksi: lähde-PDF:n sivu 6 painaa kuorobasson viivastolle G:n
        # palautusmerkillä (todettu kuvasta uudelleen, siinä ei ole
        # lukuvirhettä), ja koska Des-duurissa C ei tarvitse merkkiä mutta G
        # tarvitsee, painettu merkki näytti todistavan G:n.
        #
        # Kaikki muu sanoo C, ja kolme näistä on tästä samasta tiedostosta:
        #   * bassosolisti P4 laulaa tahdit 28-29 nuotilleen samat kuin
        #     kuorobasso ja päättyy C3:een — kuoro kaksintaa solistit tässä
        #     jaksossa unisonossa, ja kuorotenori P7 päättyy samaan G4:ään
        #     kuin tenorisolisti P3, joten muissa äänissä kaksinnus pitää.
        #   * pianon vasen käsi soittaa t.30 ensimmäisellä iskulla C2+C3.
        #   * sointu on C7 (kuoro S/A E4, T G4, pianon oikea käsi Bes5-E6-G6):
        #     G:llä perussävel jäisi kokonaan kuorosta pois.
        #   * kuoron oma tiedosto (musescore/04_dies_irae_2) laulaa C3:n.
        # Painettu palautusmerkki poistuu korjauksen mukana; C on Des-duurissa
        # merkitön. Jos kirja joskus osoittaa G:tä, tämä rivi kääntyy takaisin.
        ("30", 0, "korkeus", "G3", "C3"),              # t.653

        # --- lähde-PDF:n sivut 7-9: kolme kertaa "huic ergo parce Deus" ---
        #
        # Laulaja raportoi 2026-09-03, että tahdista 657 alkaen kuorobasso
        # laulaa "hu-ic er-go par-ce De-us" kolme kertaa (657-658, 660-663,
        # 663-665), ei "La-cry-mo-sa ... di-es il-la". Lähde-PDF painaa tähän
        # "La-cry-mo-sa,", eli **lähde-editio itse on väärässä**, ei vain
        # .mxl-tiedosto. Siksi tämä ei ole yhden laulajan muistikuvaa vasten
        # yhden lähteen sanaa, ja se tarkistettiin nuoteista:
        #
        # Kohta on limittäinen kuoron tulo samalle kuviolle: neljäsosa, kaksi
        # sidottua kahdeksasosaa, kaksi kahdeksasosaa. Kuorobasson t.658
        # (F3 Bes3 C4 Des4 Bes3) on sävel sävelestä sama kuvio kuin kuoron
        # tenorin t.657 (F4 Bes4 C5 Des5 Bes4), ja t.657 sama kuvio C3:lta.
        # Sama kuvio esiintyy myös altolla t.658 ja sopraanolla t.659 — ja
        # kaikilla kolmella sen sanat ovat "hu-ic er-go". Sama kuvio samassa
        # limityksessä kantaa samat sanat, joten bassonkin sanat ovat ne.
        # Lisäksi S/A/T laulavat "huic ergo parce Deus" koko jakson 656-668
        # läpi, ja basson oma jatko t.664-665 on jo "er-go par-ce De-us,":
        # korjauksen jälkeen kaikki neljä ääntä ovat samassa tekstissä.
        #
        # Kyse on samasta virhelajista kuin osan jo dokumentoidussa viassa
        # (osan oma aiempi "Lacrymosa dies illa" -teksti myöhempien tahtien
        # päällä) — vain kauempana alussa ja myös painetussa nuotissa.
        # Tavujen PAIKAT ovat lähdesivun mukaiset ja tarkistetut; vain sanat
        # vaihtuvat. Jos kuoron nuottikirja joskus osoittaa toisin, nämä 18
        # riviä palauttavat vanhan tekstin päinvastaisina.
        ("34", 0, "aseta", "La", "begin", "hu"),       # t.657
        ("34", 1, "aseta", "cry", "end", "ic"),        # t.657
        ("34", 1, "jatka"),                            # melisma Ges3:n yli
        ("34", 3, "aseta", "mo", "begin", "er"),       # t.657
        ("34", 4, "aseta", "sa,", "end", "go"),        # t.657
        ("35", 0, "aseta", "la", "begin", "par"),      # t.658
        ("35", 1, "aseta", "cry", "end", "ce"),        # t.658
        ("35", 1, "jatka"),                            # melisma C4:n yli
        ("35", 3, "aseta", "mo", "begin", "De"),       # t.658
        ("35", 4, "aseta", "sa", "end", "us,"),        # t.658
        ("37", 0, "aseta", "di", "begin", "hu"),       # t.660
        ("37", 2, "aseta", "es", "end", "ic"),         # t.660
        ("38", 0, "aseta", "il", "begin", "er"),       # t.661
        ("38", 2, "aseta", "la,", "end", "go"),        # t.661
        ("39", 0, "aseta", "di", "begin", "par"),      # t.662
        ("39", 1, "aseta", "es", "end", "ce"),         # t.662
        ("40", 0, "aseta", "il", "begin", "De"),       # t.663
        ("40", 1, "aseta", "la.", "end", "us,"),       # t.663
        # Kolmas tulo alkaa kesken tahtia 663, eikä enää virkkeen alusta:
        # iso alkukirjain pois.
        ("40", 2, "aseta", "Hu", "begin", "hu"),       # t.663
        # Jakson viimeinen tavu: piste, kuten kuoron tenorilla samassa
        # tahdissa. Pitkä taukojakso 666-676 seuraa.
        ("42", 0, "aseta", "us,", "end", "us."),       # t.665

        # --- lähde-PDF:n sivu 11 ---
        ("54", 0, "aseta", "par", "begin", "Pi"),      # t.677
        ("54", 1, "aseta", "ce", "end", "e"),          # t.677
        ("55", 0, "aseta", "De", "begin", "Je"),       # t.678
        ("56", 0, "aseta", "us", "end", "su"),         # t.679

        # Divisin sanarivit olivat päittäin: tämä ala-ääni oli ylemmällä
        # rivillä ja ylä-ääni alemmalla. Sivu 11 painaa ne toisin päin —
        # ylä-äänen sanat viivaston yläpuolelle, tämän ala-äänen alapuolelle
        # — ja niin ne myös luetaan. Ks. OSA_II10_DIVISI.
        ("54", None, "sanarivi", "1", "2"),            # t.677
        ("55", None, "sanarivi", "1", "2"),            # t.678
        ("56", None, "sanarivi", "1", "2"),            # t.679

        # Laulaja pyysi 2026-09-09 tahdin 677 alkuun p:n: kuorobasso tulee
        # sisään yhdentoista tahdin tauon jälkeen (666-676), ja tulo on
        # hiljainen. Lähteessä sitä ei ole tällä viivastolla, mutta sama
        # jakso on merkitty hiljaiseksi joka muualla: kuorosopraano (P5) saa
        # pp:n t.678, neljä solistia t.679 ja piano p:n t.679; kuoron oma
        # seuraava merkintä on mf vasta t.681, eli tämä jakso on sitä
        # hiljaisempi. Merkki on laulajan pyytämä p eikä naapureiden pp;
        # jos kuoron nuottikirja sanoo pp, tämä rivi vaihtaa merkin.
        ("54", None, "dynamiikka", "p"),               # t.677

        # --- sivu 12 ---
        ("58", 1, "aseta", "La", "begin", "Do"),       # t.681
        ("58", 3, "aseta", "cry", "middle", "na"),     # t.681
        ("58", 4, "aseta", "mo", "middle", "e"),       # t.681
        ("58", 5, "aseta", "sa", "end", "is"),         # t.681
        ("58", 6, "aseta", "di", "begin", "re"),       # t.681
        ("58", 7, "aseta", "es", "end", "qui"),        # t.681
        ("59", 0, "aseta", "il", "begin", "em,"),      # t.682
        ("59", 2, "aseta", "la,", "end", "do"),        # t.682
        ("59", 3, "aseta", "qua", "single", "na"),     # t.682
        ("59", 4, "aseta", "re", "begin", "e"),        # t.682
        ("60", 0, "aseta", "sur", "middle", "is,"),    # t.683
        ("60", 2, "aseta", "get", "end", "pi"),        # t.683
        ("60", 3, "aseta", "ex", "single", "e"),       # t.683

        # --- sivu 13 ---
        ("61", 0, "aseta", "fa", "begin", "Je"),       # t.684
        ("61", 1, "aseta", "vil", "middle", "su"),     # t.684
        ("61", 2, "aseta", "la,", "end", "Do"),        # t.684
        ("61", 4, "aseta", "ju", "begin", "mi"),       # t.684
        ("62", 0, "aseta", "di", "middle", "ne,"),     # t.685
        ("62", 2, "aseta", "can", "middle", "do"),     # t.685
        # "na" on tahdin 62 palkitun kahdeksasosaparin ENSIMMÄISELLÄ
        # nuotilla ja jatkoviiva juoksee toisen yli — niin sivu 13 sen
        # painaa. Tämä on koko osan ainoa tavu, jonka x jää lähemmäs
        # naapurinuottia kuin omaansa, joten se katsottiin kuvasta.
        ("62", 3, "aseta", "dus", "end", "na"),        # t.685
        ("63", 0, "aseta", "ho", "begin", "e"),        # t.686
        ("63", 1, "aseta", "mo", "end", "is"),         # t.686
        ("63", 4, "aseta", "us,", "end", "qui"),       # t.686
        ("64", 0, "aseta", "ju", "begin", "em,"),      # t.687

        # --- sivu 14: tahdissa 65 kaksi nuottia oli kokonaan ilman tavua ---
        ("65", 1, "lisaa", "single", "re"),            # t.688
        ("65", 2, "lisaa", "single", "qui"),           # t.688
        ("66", 0, "aseta", "di", "middle", "em,"),     # t.689
        ("67", 1, "aseta", "can", "middle", "re"),     # t.690
        ("67", 2, "aseta", "dus", "end", "qui"),       # t.690
        ("68", 0, "aseta", "ho", "begin", "em,"),      # t.691

        # --- sivu 15 ---
        ("70", 1, "aseta", "mo", "end", "do"),         # t.693
        ("70", 2, "aseta", "re", "begin", "na"),       # t.693
        ("71", 0, "aseta", "us,", "end", "e"),         # t.694
        ("71", 1, "aseta", "hu", "begin", "is"),       # t.694
        ("71", 2, "aseta", "ic", "end", "re"),         # t.694
        ("71", 3, "aseta", "er", "begin", "qui"),      # t.694
        ("72", 0, "aseta", "go", "end", "em."),        # t.695

        # --- sivu 16: kaikki kahdeksan ääntä laulavat "A - men." ---
        ("74", 0, "aseta", "par", "single", "A"),      # t.697
        ("75", 0, "aseta", "ce", "end", "men."),       # t.698

        # --- tavuketju koko jaksolle 681-698 ---
        #
        # Yllä olevat `aseta`-rivit vaihtoivat sanat mutta jättivät kunkin
        # tavun `syllabic`-merkinnän siltä sanalta, jonka ne korvasivat:
        # "La-cry-mo-sa"-sanan `middle` jäi sanan "do-na" toiselle tavulle.
        # Ketju hajosi, ja stemmaan tulostui "Do-na-e-is" ja "re qui em,"
        # ilman väliviivoja. Vika oli painetussa stemmassa 2026-09-03
        # lähtien; se löytyi kun suomennos ei tunnistanut sanoja (ks.
        # suomennos.py).
        #
        # Tavujen tekstit ja paikat ovat lähdesivujen 12-16 mukaiset ja
        # tarkistettu 2026-09-03 nuottitarkkuudella; tämä rivi ei muuta
        # niitä, vaan tarkistaa ne ja korjaa vain ketjumerkinnät. Sana
        # kerrallaan luettuna jakso on juuri se, mikä stemmasta luetaan
        # takaisin.
        ("58", None, "tavutus",
         "Do-na e-is re-qui-em, do-na e-is, pi-e Je-su Do-mi-ne, "
         "do-na e-is re-qui-em, re-qui-em, re-qui-em, "
         "do-na e-is re-qui-em. A-men."),
    ),
)

OSA_II10_DIVISI = Osa(
    mxl="11-Verdi_Lacrymosa.mxl",
    out="11-Verdi_Lacrymosa-kasin.mxl",
    osasto="P9",
    nimi="Kuoro B (divisin ylä-ääni)",
    # Sanarivi 2 on tässä aito: viivastolla on kaksi ääntä eri rytmeissä,
    # joten tavut eivät mahdu samalle riville. Siksi ei yksi_sanarivi.
    yksi_sanarivi=False,
    korjaukset=(
        # Sivu 11, sanat viivaston yläpuolella. Nuotit ovat oikein — ne
        # täsmäävät kuoron oman tiedoston (musescore/04_dies_irae_2) toiseen
        # bassoääneen — ja tavut osuvat 1:1 samoille nuoteille kuin väärä
        # teksti, mikä tarkistettiin PDF:n x-koordinaateista.
        ("54", 0, "aseta", "La", "begin", "Pi"),       # t.677
        ("54", 1, "aseta", "cry", "end", "e"),         # t.677
        ("54", 3, "aseta", "mo", "begin", "Je"),       # t.677
        ("55", 0, "aseta", "sa", "end", "su"),         # t.678
        ("55", 2, "aseta", "di", "begin", "Do"),       # t.678
        ("55", 3, "aseta", "es", "middle", "mi"),      # t.678
        ("56", 0, "aseta", "il", "end", "ne,"),        # t.679

        # Ylä-ääni ylemmälle sanariville. Laulaja raportoi 2026-09-07, että
        # tahtien 677-679 kaksi sanariviä ovat päittäin: stemmassa ylärivillä
        # luki ala-äänen "Pi-e Je-su" ja alarivillä tämän ylä-äänen "Pi-e
        # Je-su Do-mi-ne,". Lähdesivu 11 painaa ne juuri toisin päin, ja
        # ylempi rivi kuuluu ylemmälle äänelle muutenkin. Lähdetiedoston oma
        # järjestys (default-y -80 ja -97) oli tässä väärin päin, koska
        # osastot ovat siellä erillisiä eikä kumpikaan tiedä toisestaan.
        ("54", None, "sanarivi", "2", "1"),            # t.677
        ("55", None, "sanarivi", "2", "1"),            # t.678
        ("56", None, "sanarivi", "2", "1"),            # t.679
    ),
)

# Sanctus (IV), tahdit 99-100. Laulaja raportoi, että sana "cae-li" puuttuu:
# rivi kuuluu "ple-ni sunt cae-li et ter-ra". Tahdin 99 kokonuotilla ei ollut
# tavua lainkaan ja tahdin 100 "li" oli merkitty yksitavuiseksi (single),
# joten stemmassa luki "sunt _ li et ter-ra".
#
# Kuoro I:n sopraano (P1) on samoissa tahdeissa oikein — "coe" t.99, "li"
# t.100 — ja altolta, tenorilta ja bassolta puuttuu kaikilta sama "coe".
# Kirjoitusasu on tässä lähteessä "coe" eikä "cae" (niin myös osan aiemmassa
# samassa lauseessa t.27), joten pysytään tiedoston omassa asussa.
#
# Kuoro II (P5-P8) laulaa samassa kohdassa "Ho-san-na," eikä siihen kosketa.
SANCTUS_COELI = (("99", 0, "lisaa", "begin", "coe"),
                 ("100", 0, "aseta", "li", "end", "li"))  # single -> end
OSAT_IV = [
    Osa(mxl="13-Verdi-Sanctus.mxl",
        out="13-Verdi-Sanctus-kasin.mxl",
        osasto=pid, nimi=nimi, yksi_sanarivi=False,
        korjaukset=SANCTUS_COELI)
    for pid, nimi in (("P2", "Kuoro A"), ("P3", "Kuoro T"), ("P4", "Kuoro B"))
]


# Kuoro II:n basso, Sanctus t.71: "in no-mi-ni" -> "in no-mi-ne". Lause on
# "qui venit in nomine Domini", ja sama tiedosto kirjoittaa sen oikein sekä
# Kuoro I:n bassossa (t.65) että tämän oman äänen jatkossa (t.72-73
# "Do-mi-ni"). Löytyi kun suomennos ei tunnistanut sanaa; virhe näkyy Basso
# II:n stemmassa painettuna. Tämä ei kuulu OSAT_IV:ään: se on niiden kolmen
# äänen taulukko, joilta puuttui "coe", eikä Kuoro II laula sitä lausetta.
OSA_IV_KUORO_B_II = Osa(
    mxl="13-Verdi-Sanctus.mxl",
    out="13-Verdi-Sanctus-kasin.mxl",
    osasto="P8",
    nimi="Kuoro B II",
    yksi_sanarivi=False,
    korjaukset=(("71", 3, "aseta", "ni", "end", "ne"),),
)

# Libera me (VII), kuorobasso. Kolme eri vikaa.
#
# 1. Tahti 72, toinen nuotti oktaavia alempi A. Sama kuvio ja sama vika kuin
#    Dies iraen tahdissa 28 (ks. OSA_II1): osan alku on Dies irae -teeman
#    kolmas paluu. Kuoron oma tiedosto (musescore/07_libera_me) laulaa siellä
#    A2:n ja sen Bass 2 on tauolla. Kohdistus on yksikäsitteinen: sopraanon
#    stemma osuu kuorotiedoston mezzoon yhtenä 127 tahdin lohkona (meidän
#    44-170 = kuoron 11-137), ja sillä siirrolla basso täsmää muualla
#    tahdista tahtiin. Tahti 68 on sama kuvio A3->A3 ja se täsmää — eli
#    poikkeus on aito, kuten Dies iraen tahdissa 24.
#
# 2. Tahti 88, väärä rytmi. Kohta on kuorobasson yksinlaulua (S, A ja T ovat
#    tauolla t.87-89), ja kuorotiedoston vastaava tahti 55 jakaa sen toisin:
#
#      meillä   Ges. Ges16  F♩     Ees. Ees16  D♩    "ma gna et  a ma ra"
#      kuorolla Ges. Ges16  F. F16 Ees♩ D♩           "ma gna et  a ma ra"
#
#    eli toinen pisteellinen kuvio tulee tavuille "et a" eikä "a ma". Molemmat
#    täyttävät tahdin ja molemmat sopivat sanoihin, joten tämä jäi ensin vain
#    kirjatuksi; laulaja vahvisti 2026-09-04 että kuorotiedosto on oikeassa.
#    Kuorotiedostoa on lupa uskoa juuri tässä: sen tahdit 54 ja 56 (= meidän
#    87 ja 89) ovat nuotilleen, etumerkilleen ja aksentilleen samat kuin
#    meidän, eli ero on täsmälleen yhden tahdin mitassa.
#
#    Aksentit tulevat samasta lähteestä: kuorotiedostossa ne ovat iskuilla
#    (nuotit 0, 2, 4, 5) eikä uudella 16-osalla ole aksenttia. Meillä ne
#    olivat vanhan rytmin iskuilla (0, 2, 3, 5), joten aksentti siirtyy
#    nuotilta 3 nuotille 4. Tavut pysyvät samoilla nuoteilla.
#
# 3. Tahti 98, sanan "di-es" molemmat tavut puuttuivat kokonaan. Laulaja
#    sanoi tahdiksi 93, mutta 93 laulaa "il-la," ja on oikein; hän kertoi
#    myös tavut menevän tahdin ensimmäiselle ja kolmannelle nuotille, ja
#    juuri tahti 98 on lähistön ainoa kolmen nuotin tahti ilman sanoja.
#    Sanat jatkuvat tahdista 99 "ma-gna," eli "di-es mag-na" — juuri niin
#    kuin laulaja sanoi. Kuoroaltto (P3) laulaa tahdissa 98 saman kuvion
#    samalla jaolla ("di" 1. nuotille, 3. nuotille "es", välinuotti
#    melismana), ja basson oma tahti 100 on rakenteeltaan identtinen.
OSA_VII = Osa(
    mxl="16-Libera_Me.mxl",
    out="16-Libera_Me-kasin.mxl",
    osasto="P5",
    nimi="Kuoro B",
    yksi_sanarivi=False,
    korjaukset=(
        ("72", 1, "korkeus", "A3", "A2"),   # "di-es il-la," viimeinen tavu
        # t.88: F♩ -> F. + Ees. -> F16, ja Ees16 -> Ees♩
        ("88", 2, "kesto", "256/quarter", "192/eighth."),
        ("88", 3, "korkeus", "Ees3", "F3"),
        ("88", 3, "kesto", "192/eighth.", "64/16th"),
        ("88", 3, "poista_aksentti"),
        ("88", 4, "kesto", "64/16th", "256/quarter"),
        ("88", 4, "lisaa_aksentti"),
        ("98", 0, "lisaa", "begin", "di"),
        ("98", 2, "lisaa", "end", "es"),
        # t.85: "cal-la-mi-ta-tis" -> "ca-la-mi-ta-tis". Sana on
        # calamitatis yhdellä l:llä; lähteessä ensimmäinen tavu on "cal",
        # joten stemmaan tulostui "callamitatis". Löytyi kun suomennos ei
        # tunnistanut sanaa (ks. suomennos.py).
        ("85", 2, "aseta", "cal", "begin", "ca"),
    ),
)

# Sama puuttuva "di-es" myös kuorotenorilla. Sillä tahdissa 98 on kaksi
# nuottia eikä kolmea, joten tavut tulevat molemmille — täsmälleen niin kuin
# tenorin omassa tahdissa 100, joka on nuotilleen sama kuvio.
OSA_VII_TENORI = Osa(
    mxl="16-Libera_Me.mxl",
    out="16-Libera_Me-kasin.mxl",
    osasto="P4",
    nimi="Kuoro T",
    yksi_sanarivi=False,
    korjaukset=(
        ("98", 0, "lisaa", "begin", "di"),
        ("98", 1, "lisaa", "end", "es"),
    ),
)

# Osan 14 (Agnus Dei) korjaukset on aikanaan tehty suoraan lähdetiedostoon,
# joten sillä ei ole omaa Osa-riviä. Jos se joskus puretaan tänne, ks.
# CLAUDE.md, *Recipe*-luvun viimeinen kappale.
# Agnus Dei (V). Tämän osan sanakorjaukset ovat toistaiseksi leivottuja
# suoraan `14-...-OMR-korjattu.mxl`:ään (ks. CLAUDE.md:n varoitus), mutta
# uudet korjaukset kirjataan tänne, ja `yhdista.py` lukee tämän tuloksen.
#
# P5 ja P6 ovat tahdeissa 1-13 sooloäänet ja tahdista 14 pianon kaksi
# viivastoa. Pianoviivastolla ei ole sanoja, joten jokainen tavu siellä on
# konelukemisen roskaa:
#
#   * P6 t.68 kantaa tavut "A." ja "Reutenauer". Ne ovat nuottipainoksen
#     alalaidan kaivertajamerkintä: lähde-PDF:n tekstikerroksessa sama
#     "A. Reutenauer" on sivun 5 alimpana rivinä y:llä 767, kaukana
#     alimmasta viivastosta.
#   * P5 t.31 kantaa tavun "¢|¢", joka ei ole sana lainkaan.
#
# Kuorobasso (P4) t.40-43: lähdesivu 3, 2. järjestelmä (tahdit 40-45).
# Laulaja: "tahdissa 40 pitäisi olla do-, joka loppuu tahdin 43 ensimmäiseen
# nuottiin (tai oikeastaan na-tavu jatkuu vielä toiseen nuottiin asti)."
# Konelukema oli kopioinut bassolle ylä-äänten "do-na, do-na" -kuvion:
# tahdissa 41 luki "na," ja tahdissa 42 "do". Bassolla on niissä pelkkä
# melisma.
#
# Mitattu lähde-PDF:n tekstikerroksesta, ei silmällä. Sivun 3 toisen
# järjestelmän neljä sanariviä x-koordinaatteineen (`mutool draw -F stext`,
# Garamond 10; kuorobasso on 4. viivasto, bassoavain x:llä 27, tavurivi
# y:llä 425):
#
#   S: Do-@45 na,@96 do-@172 na@231 e-@259 is@278 do-@305 na@392 …
#   T: Do-@45 na@120  do-@172 na@232 e@259  is@305 re-@362 qui-@392 …
#   B: Do-@45         na@259 e-@305 is@329 re-@362 qui-@392 em,@438 do-@529 na.@553
#
# Tahdit alkavat x:illä 40->45, 41->96, 42->172, 43->259, 44->362, 45->529
# (basson nuottipäät: kaksi kokonuottia 45 ja 96, kaksi puolinuottia 172 ja
# 208, sitten 259 pisteellinen neljäsosa + 290 kahdeksasosa + 305 + 329).
# Basson rivillä ei siis ole tavua x:ien 45 ja 259 välissä lainkaan: "Do-"
# tahdissa 40, melisma tahtien 41-42 yli, "na" tahdin 43 ensimmäisellä
# nuotilla ja sen melisma toisella. Ylä-äänet laulavat "do-na," kahdesti,
# basso kerran — juuri niin kuin laulaja sen kuuli.
#
# Tahdin 43 tavut ("na" nuotilla 0, "e" nuotilla 2, "is" nuotilla 3) ovat jo
# oikein, joten vain "Do":n syllabic muuttuu ja kaksi roskatavua lähtee.
#
# Samalla t.42:n toisen nuotin piste. Se näkyi vasta kun korjattu tahti
# katsottiin kuvana: nuotti on `<type>half</type><dot/>` mutta
# `<duration>24</duration>`, eli MuseScore piirtää pisteellisen puolinuotin
# ja laskee puolinuotin. Kolme riippumatonta asiaa sanoo, ettei pistettä ole:
# tahtilaji on 4/4 eikä puoli + pisteellinen puoli mahdu siihen (2+3=5),
# kuoron oma tiedosto (musescore/06_agnus_dei, sen t.23 = meidän t.42) laulaa
# kaksi tavallista puolinuottia, ja tiedoston oma kesto on 24. Lähdesivu
# kuitenkin *piirtää* pisteen (sivu 3, x 211, y 403) — sama tilanne kuin
# Lacrymosan t.653: painettu merkki kertoo mitä kaivertaja piirsi eikä sitä,
# oliko se oikein. Tämä on koko kuorobasson ainoa pisteen ja keston
# ristiriita — kaikissa kuudessa viivastossa yhteensä ei ole toista.
OSAT_V = [
    Osa(mxl="14-Verdi_requiem_agnus-dei-OMR-korjattu.mxl",
        out="14-Verdi_requiem_agnus-dei-kasin.mxl",
        osasto="P4", nimi="Kuoro B", yksi_sanarivi=False,
        korjaukset=(("40", 0, "aseta", "Do", "begin", "Do"),
                    ("41", 0, "poista", "na,"),
                    ("42", 0, "poista", "do"),
                    ("42", 1, "kesto", "24/half.", "24/half"))),
    Osa(mxl="14-Verdi_requiem_agnus-dei-OMR-korjattu.mxl",
        out="14-Verdi_requiem_agnus-dei-kasin.mxl",
        osasto="P5", nimi="Piano 1 / Solisti S", yksi_sanarivi=False,
        korjaukset=(("31", 1, "poista", "¢|¢"),)),
    Osa(mxl="14-Verdi_requiem_agnus-dei-OMR-korjattu.mxl",
        out="14-Verdi_requiem_agnus-dei-kasin.mxl",
        osasto="P6", nimi="Piano 2 / Solisti M-S", yksi_sanarivi=False,
        korjaukset=(("68", 2, "poista", "A."),
                    ("68", 3, "poista", "Reutenauer"))),
]

OSAT = ([OSA_I, OSA_I_SOPRAANO, OSA_I_ALTTO, OSA_I_TENORI, OSA_II1]
        + OSAT_II4
        + [OSA_II6, OSA_II6_TENORI, OSA_II9B] + OSAT_II9B_SAT
        + [OSA_II10_KUORO_B, OSA_II10_DIVISI] + OSAT_IV
        + [OSA_IV_KUORO_B_II] + OSAT_V
        + [OSA_VII_TENORI, OSA_VII])


# Osan I sivu 3, 1. järjestelmä (tahdit 50–58): yhden b:n sävellaji puretaan
# palautusmerkeillä tahdin 56 alussa. Konelukema ei nähnyt purkua vaan luki
# sävellajin uudestaan vasta seuraavan järjestelmän alusta ja kirjasi vaihdon
# tahtiin 59 — kolme tahtia myöhässä, keskelle bassostemman taukoa, mistä
# laulaja sen huomasi ("tahdissa 59 on palautusmerkki, ja tahti on tyhjä").
#
# Mitattu PDF:n omasta tekstikerroksesta, ei silmällä: `mutool draw -F stext`
# antaa nuottifontin (Mozart9) merkit koordinaatteineen, ja palautusmerkkejä
# on kuusi peräkkäin samalla x:llä 368 — yksi kullakin kuudella viivastolla,
# täsmälleen sävellajimerkinnän y-korkeuksilla. Tahti 56 alkaa x:llä 367
# (leveydet lähteen omista <measure width>-arvoista, kerroin 0,306), tahti 59
# vasta seuraavassa järjestelmässä. Sama menetelmä vahvistaa, että tahdin 67
# kolme ristiä ovat oikeassa tahdissa, joten vain tämä yksi vaihto siirtyy.
#
# Sama vika kolme tahtia aiemmin ja seitsemän tahdin verran isompana: sivun 2
# ensimmäisessä järjestelmässä kolmen ristin sävellaji puretaan ja yksi b
# asetetaan x:llä 138-147, ja tahti 28 alkaa x:llä 135. Vaihto kuuluu siis
# tahtiin 28. Konelukema kirjasi sen tahtiin 28 vain kuorotenoriin (P15) ja
# kuorobassoon (P16) ja muissa viidessätoista osastossa tahtiin 35, seuraavan
# järjestelmän alkuun. Siirto on pelkkä merkintä eikä muuta yhtään
# sävelkorkeutta — sen aiheuttama vahinko on korjattu erikseen sopraanon ja
# alton `korkeus`-riveillä.
SAVELLAJIT = (
    Savellaji(mxl=OSA_I.mxl, out=OSA_I.out, siirrot=(("59", "56", 0),)),
    Savellaji(mxl=OSA_I.mxl, out=OSA_I.out, siirrot=(("35", "28", -1),),
              valmiit=("P15", "P16")),
)


def lyriikat(note):
    return note.findall("lyric")


def teksti(lyric):
    return lyric.findtext("text")


def uusi_lyric(syllabic, text):
    ly = ET.Element("lyric", {"number": "1"})
    ET.SubElement(ly, "syllabic").text = syllabic
    ET.SubElement(ly, "text").text = text
    return ly


# Dynamiikan kirjoitusasu on MusicXML:n oma elementin nimi. Lista on
# tarkoituksella lyhyt: kirjoitusvirhe taulukossa tuottaisi elementin, jota
# MuseScore ei tunne, ja merkintä katoaisi hiljaa.
DYNAMIIKAT = ("ppp", "pp", "p", "mp", "mf", "f", "ff", "fff")


def uusi_dynamiikka(merkki, sisennys):
    """<direction>, joka painaa dynamiikkamerkin viivaston yläpuolelle.

    Lauluviivastolla sanat ovat viivaston alla, joten merkintä kuuluu
    yläpuolelle — niin lähteet itse tekevät (11-Verdi_Lacrymosa P8 t.58).
    `default-y` jätetään pois, jotta MuseScore asemoi sen itse, samasta
    syystä kuin `korkeus` ja `sanarivi` pudottavat omansa.

    `sisennys` on tahdin lasten sisennys ("\n" + välilyönnit). Näissä
    tiedostoissa sisennys on ET:llä alkioiden text- ja tail-kentissä, ja
    ilman sitä lisätty merkintä tulostuisi yhtenä rivinä keskelle diffiä.
    """
    d = ET.Element("direction", {"placement": "above"})
    dt = ET.SubElement(d, "direction-type")
    ET.SubElement(ET.SubElement(dt, "dynamics"), merkki)
    ET.indent(d, space="  ", level=len(sisennys.lstrip("\n")) // 2)
    d.tail = sisennys
    return d


def lasten_sisennys(measure):
    """Tahdin lasten sisennys, tai järkevä oletus jos tiedosto on tiivis."""
    return (measure.text if measure.text and measure.text.startswith("\n")
            else "\n      ")


def ennen_nuotteja(measure):
    """Kohta, johon tahtiin lisättävä <direction> kuuluu.

    <direction> vaikuttaa sitä seuraaviin nuotteihin, joten se menee
    ensimmäisen nuotin eteen — mutta <print>:n ja <attributes>:n jälkeen.
    """
    nuotit = measure.findall("note")
    return list(measure).index(nuotit[0]) if nuotit else len(measure)


# Korkeuden kirjoitusasu on sama kuin nayta.py:n tulosteessa, jotta laulajan
# raportin tarkistanut voi kopioida sen suoraan taulukkoon: Bes3, Fis4, C3.
MERKIT = {"-2": "eses", "-1": "es", "1": "is", "2": "isis"}
ALTERIT = {v: k for k, v in MERKIT.items()}


def kuvaa(note):
    """Nuotin tunniste virheilmoituksia varten, esim. "Bes3" tai "rest"."""
    pitch = note.find("pitch")
    if pitch is None:
        return "rest"
    alter = pitch.findtext("alter")
    return (pitch.findtext("step") + MERKIT.get(alter, alter or "")
            + pitch.findtext("octave"))


def lue_korkeus(teksti):
    """"Bes3" -> ("B", "-1", "3"). Kääntää kuvaa():n tuloksen takaisin."""
    assert len(teksti) >= 2, f"korkeus on vähintään sävel ja oktaavi: {teksti!r}"
    step, loput = teksti[0], teksti[1:]
    assert step in "ABCDEFG", f"tuntematon sävel {teksti!r}"
    merkki, oktaavi = loput[:-1], loput[-1]
    assert oktaavi.isdigit(), f"tuntematon oktaavi {teksti!r}"
    assert merkki in ALTERIT or merkki == "", f"tuntematon etumerkki {teksti!r}"
    return step, ALTERIT.get(merkki), oktaavi


def kuvaa_kesto(note):
    """Nuottiarvo muodossa "192/eighth." — kesto, tyyppi ja pisteet."""
    return "%s/%s%s" % (note.findtext("duration"), note.findtext("type"),
                        "." * len(note.findall("dot")))


def aseta_kesto(note, teksti):
    """Kirjoita nuottiarvo uudelleen.

    default-x on nuotin vaakasijainti, joka on laskettu VANHALLE rytmille,
    joten se poistetaan samasta syystä kuin korkeuden vaihdossa default-y.
    Palkkeja ei tarvitse laskea: nämä lähteet eivät kirjoita <beam>-alkioita
    lainkaan, joten MuseScore palkittaa itse.
    """
    kesto, loput = teksti.split("/")
    tyyppi = loput.rstrip(".")
    pisteet = len(loput) - len(tyyppi)
    assert kesto.isdigit(), f"tuntematon kesto {teksti!r}"
    note.find("duration").text = kesto
    note.find("type").text = tyyppi
    for dot in note.findall("dot"):
        note.remove(dot)
    # <dot> tulee MusicXML:ssä heti <type>:n jälkeen.
    kohta = list(note).index(note.find("type")) + 1
    for i in range(pisteet):
        note.insert(kohta + i, ET.Element("dot"))
    note.attrib.pop("default-x", None)


def articulations(note):
    return note.find("notations/articulations")


def kestosummat(measure):
    """Äänittäin soivien kestojen summa. Soinnun toiset sävelet eivät soi
    peräkkäin, joten ne jätetään pois."""
    summat = {}
    for note in measure.findall("note"):
        if note.find("chord") is not None:
            continue
        aani = note.findtext("voice") or "1"
        summat[aani] = summat.get(aani, 0) + int(note.findtext("duration") or 0)
    return summat


def aseta_korkeus(note, teksti):
    """Kirjoita nuotin korkeus uudelleen ja pudota vanhan asemointivihjeet.

    <accidental> on painettu etumerkki, <stem> varren suunta ja default-y
    nuottipään pystysijainti — kaikki kolme on laskettu VANHALLE korkeudelle,
    joten ne poistetaan ja MuseScore laskee ne uudelleen. Etumerkin se päättää
    <alter>:sta ja sävellajista, joten oikea merkki tulee silti näkyviin.
    """
    step, alter, oktaavi = lue_korkeus(teksti)
    pitch = note.find("pitch")
    assert pitch is not None, "tauolla ei ole korkeutta"
    for lapsi in list(pitch):
        pitch.remove(lapsi)
    ET.SubElement(pitch, "step").text = step
    if alter is not None:
        ET.SubElement(pitch, "alter").text = alter
    ET.SubElement(pitch, "octave").text = oktaavi
    for turha in ("accidental", "stem"):
        for e in note.findall(turha):
            note.remove(e)
    note.attrib.pop("default-y", None)


def siirra_savellaji(root, mista, mihin, fifths, valmiit=()):
    """Siirrä sävellajin vaihto tahdista toiseen kaikissa osastoissa.

    <key> siirretään, ei kopioida: vanhaan tahtiin jäävä vaihto merkitsisi
    sävellajin vaihtuvan kahdesti. Muu <attributes>-sisältö jää paikalleen,
    koska se kuvaa sitä tahtia eikä sävellajia.

    `valmiit` on niiden osastojen tunnukset, joissa konelukema sattui
    näkemään vaihdon jo oikeassa tahdissa. Niitä ei siirretä, mutta ne
    tarkistetaan: vaihto on kohdetahdissa ja lähtötahdissa ei ole toista.
    Ilman tarkistusta lista voisi vanhentua huomaamatta.
    """
    selosteet = []
    for part in root.findall("part"):
        pid = part.get("id")
        tahdit = {m.get("number"): m for m in part.findall("measure")}
        vanha, uusi = tahdit.get(mista), tahdit.get(mihin)
        assert vanha is not None, f"{pid}: tahtia {mista} ei ole"
        assert uusi is not None, f"{pid}: tahtia {mihin} ei ole"

        if pid in valmiit:
            assert uusi.findtext("attributes/key/fifths") == str(fifths), (
                f"{pid} t.{mihin}: sävellajia {fifths} ei ole, "
                f"vaikka osasto on merkitty valmiiksi")
            assert vanha.find("attributes/key") is None, (
                f"{pid} t.{mista}: sävellajin vaihto on, "
                f"vaikka osasto on merkitty valmiiksi")
            selosteet.append(f"{pid}: sävellaji {fifths} oli jo t.{mihin}")
            continue

        attrs = vanha.find("attributes")
        key = None if attrs is None else attrs.find("key")
        assert key is not None, f"{pid} t.{mista}: sävellajin vaihtoa ei ole"
        assert key.findtext("fifths") == str(fifths), (
            f"{pid} t.{mista}: odotettiin sävellajia {fifths}, "
            f"on {key.findtext('fifths')}")
        assert uusi.find("attributes/key") is None, (
            f"{pid} t.{mihin}: sävellajin vaihto on jo")

        attrs.remove(key)
        if len(attrs) == 0:
            vanha.remove(attrs)

        kohde = uusi.find("attributes")
        if kohde is None:
            kohde = ET.Element("attributes")
            # <attributes> vaikuttaa sitä seuraaviin nuotteihin, joten se
            # menee ensimmäisen nuotin eteen mutta <print>:n jälkeen.
            nuotit = uusi.findall("note")
            kohta = list(uusi).index(nuotit[0]) if nuotit else len(uusi)
            uusi.insert(kohta, kohde)
            # Nämä tiedostot ovat sisennettyjä, ja sisennys on ET:llä
            # alkioiden text- ja tail-kenttiä. Ilman tätä siirretty vaihto
            # näkyisi diffissä yhtenä sotkuisena rivinä.
            sisennys = uusi.text if uusi.text and uusi.text.startswith("\n") else "\n      "
            kohde.text, kohde.tail, key.tail = sisennys + "  ", sisennys, sisennys
        # MusicXML:ssä <key> tulee heti <divisions>:n jälkeen ja ennen muita.
        kohde.insert(1 if kohde.find("divisions") is not None else 0, key)
        selosteet.append(f"{pid}: sävellaji {fifths} siirretty "
                         f"t.{mista} -> t.{mihin}")
    return selosteet


def sovella(part, osa):
    """Aja osan korjaukset osastoon ja palauta selosteet."""
    tahdit = {m.get("number"): m for m in part.findall("measure")}
    selosteet = []

    # Rytmin uudelleenjako ei saa muuttaa tahdin pituutta; otetaan lähtöarvot
    # talteen ennen kuin mitään on kirjoitettu.
    ennen = {t: kestosummat(tahdit[t]) for t, _i, laji, *_ in osa.korjaukset
             if laji == "kesto" and t in tahdit}

    for tahti, i, laji, *args in osa.korjaukset:
        measure = tahdit.get(tahti)
        assert measure is not None, f"tahtia {tahti} ei ole"
        notes = measure.findall("note")
        if i is None:
            note = None
        else:
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
            # Pelkkä syllabicin vaihto ei näy tekstissä, ja kuiva ajo, joka
            # sanoo "'Do' -> 'Do'", ei kerro mitä se aikoo tehdä.
            vanha_syllabic = ly[0].find("syllabic").text
            ly[0].find("syllabic").text = syllabic
            ly[0].find("text").text = text
            if text == odotettu and syllabic != vanha_syllabic:
                selosteet.append(f"t.{tahti}: {text!r} {vanha_syllabic} "
                                 f"-> {syllabic}")
            else:
                selosteet.append(f"t.{tahti}: {odotettu!r} -> {text!r}")

        elif laji == "jatka":
            # Melisma: tavu jatkuu seuraavalle nuotille, ja <extend/> piirtää
            # sen jatkoviivan. Ilman tätä sanan viimeinen tavu (syllabic
            # "end") jää roikkumaan ilman merkkiä siitä että sitä lauletaan
            # yhä. Tavuviivaa se ei korvaa — se syntyy syllabicista.
            ly = lyriikat(note)
            assert len(ly) == 1, (
                f"t.{tahti} nuotti {i}: odotettiin yhtä tavua, "
                f"on {len(ly)}")
            assert ly[0].find("extend") is None, (
                f"t.{tahti} nuotti {i}: jatkoviiva on jo")
            ET.SubElement(ly[0], "extend")
            selosteet.append(f"t.{tahti}: jatkoviiva tavulle "
                             f"{teksti(ly[0])!r}")

        elif laji == "korkeus":
            odotettu, uusi = args
            assert kuvaa(note) == odotettu, (
                f"t.{tahti} nuotti {i}: odotettiin {odotettu}, "
                f"on {kuvaa(note)}")
            aseta_korkeus(note, uusi)
            selosteet.append(f"t.{tahti}: {odotettu} -> {uusi}")

        elif laji == "kesto":
            odotettu, uusi = args
            assert kuvaa_kesto(note) == odotettu, (
                f"t.{tahti} nuotti {i}: odotettiin {odotettu}, "
                f"on {kuvaa_kesto(note)}")
            aseta_kesto(note, uusi)
            selosteet.append(f"t.{tahti}: nuottiarvo {odotettu} -> {uusi}")

        elif laji == "lisaa_aksentti":
            art = articulations(note)
            assert art is None or art.find("accent") is None, (
                f"t.{tahti} nuotti {i}: aksentti on jo")
            if art is None:
                notations = note.find("notations")
                if notations is None:
                    notations = ET.SubElement(note, "notations")
                art = ET.SubElement(notations, "articulations")
            ET.SubElement(art, "accent")
            selosteet.append(f"t.{tahti}: lisätty aksentti nuotille {i}")

        elif laji == "poista_aksentti":
            art = articulations(note)
            accents = [] if art is None else art.findall("accent")
            assert accents, f"t.{tahti} nuotti {i}: aksenttia ei ole"
            for accent in accents:
                art.remove(accent)
            selosteet.append(f"t.{tahti}: poistettu aksentti nuotilta {i}")

        elif laji == "kopioi_tahti":
            (lahde,) = args
            malli = tahdit.get(lahde)
            assert malli is not None, f"lähdetahtia {lahde} ei ole"
            # Kohteen pitää olla pelkkää taukoa. Jos siellä on nuotteja,
            # ollaan väärässä tahdissa eikä täytetä aukkoa vaan tuhotaan
            # musiikkia — silloin on parempi kaatua.
            assert notes and all(n.find("rest") is not None for n in notes), (
                f"t.{tahti}: ei ole pelkkä tauko, ei täytetä")
            kohta = list(measure).index(notes[0])
            for n in notes:
                measure.remove(n)
            for offset, n in enumerate(malli.findall("note")):
                measure.insert(kohta + offset, copy.deepcopy(n))
            selosteet.append(f"t.{tahti}: kopioitu tahdista {lahde} "
                             f"({len(malli.findall('note'))} nuottia)")

        elif laji == "sanarivi":
            # Koko tahdin tavut siirtyvät riviltä toiselle. Divisissä rivi
            # kertoo kummasta äänestä on kyse, joten se on sisältöä eikä
            # asettelua: ylä-ääni kuuluu ylemmälle riville. `default-y` on
            # laskettu vanhalle riville, joten se pudotetaan samasta syystä
            # kuin `korkeus` pudottaa omansa — MuseScore asettelee itse.
            # Indeksi rajaa siirron yhteen nuottiin. Sitä tarvitaan, kun
            # tahdissa on tavuja kahdella rivillä: konelukema pudotti sanan
            # keskimmäisen tavun riville 2 ja jätti muut riville 1, jolloin
            # sana katkeaa kahdelle tekstiriville.
            vanha, uusi = args
            ly = [x for n in ([note] if note is not None else notes)
                  for x in lyriikat(n)]
            assert ly, f"t.{tahti}: ei tavuja siirrettäväksi"
            on = sorted({x.get("number") for x in ly})
            assert on == [vanha], (
                f"t.{tahti}: odotettiin sanariviä {vanha!r}, on {on}")
            for x in ly:
                x.set("number", uusi)
                x.attrib.pop("default-y", None)
            selosteet.append(f"t.{tahti}: sanarivi {vanha} -> {uusi} "
                             f"({len(ly)} tavua)")

        elif laji == "vaihda_sanarivit":
            # Kaksi sanariviä vaihtaa keskenään koko tahdin verran. Tämä on
            # `sanarivi`:n divisiversio: kun molemmat äänet ovat samassa
            # osastossa, rivejä ei voi siirtää yksitellen — ensimmäinen
            # siirto törmäisi toiseen riviin.
            #
            # Numerot luetaan normalisoituina, mutta kirjoitetaan takaisin
            # lähteen omassa kirjoitusasussa ("part8verse1"): sekamuoto
            # samassa osastossa sekoittaa MuseScoren rivilaskennan.
            a, b = args
            ryhmat = {}
            for x in (x for n in notes for x in lyriikat(n)):
                ryhmat.setdefault(str(rivinumero(x)), []).append(x)
            assert sorted(ryhmat) == sorted([a, b]), (
                f"t.{tahti}: odotettiin sanarivit {sorted([a, b])}, "
                f"on {sorted(ryhmat)}")
            raaka = {rivi: xs[0].get("number") for rivi, xs in ryhmat.items()}
            for rivi, toinen in ((a, b), (b, a)):
                for x in ryhmat[rivi]:
                    x.set("number", raaka[toinen])
                    x.attrib.pop("default-y", None)
            selosteet.append(
                f"t.{tahti}: sanarivit {a} <-> {b} "
                f"({len(ryhmat[a])} + {len(ryhmat[b])} tavua)")

        elif laji == "dynamiikka":
            # Dynamiikkamerkintä tahdin alkuun. Tämä ei korjaa lähdettä vaan
            # lisää siihen jotain, jota siinä ei ole, joten se kuuluu
            # perustella kommentissa yhtä tarkasti kuin tavukorjaus.
            (merkki,) = args
            assert merkki in DYNAMIIKAT, (
                f"tuntematon dynamiikka {merkki!r}, ei ole {DYNAMIIKAT}")
            on = [c.tag for d in measure.findall("direction")
                  for dy in d.findall("direction-type/dynamics") for c in dy]
            assert not on, f"t.{tahti}: dynamiikka on jo ({on})"
            measure.insert(ennen_nuotteja(measure),
                           uusi_dynamiikka(merkki, lasten_sisennys(measure)))
            selosteet.append(f"t.{tahti}: lisätty dynamiikka {merkki}")

        elif laji == "tavutus":
            # Korjaa `syllabic`-merkinnät annetun sanajaon mukaisiksi
            # tahdista eteenpäin. Tavujen tekstit tarkistetaan, mutta niitä
            # ei muuteta.
            #
            # Tämä on olemassa siksi, että `aseta`-rivi kantaa sen sanan
            # ketjumerkinnän, jonka se korvasi: kun 2026-09-03 Lacrymosan
            # tahtien 681-694 sanat vaihdettiin, "La-cry-mo-sa"-sanan
            # `middle` jäi sanan "do-na" toiseksi tavuksi. Ketju hajosi, ja
            # stemmaan tulostui "Do-na-e-is" ja "re qui em," ilman
            # väliviivoja. Rivi kertoo koko lauseen kerralla, joten se on
            # luettavissa ja tarkistaa itse jokaisen tavun.
            (jako,) = args
            odotetut = [(sana, tavu, len(sana.split("-")), j)
                        for sana in jako.split()
                        for j, tavu in enumerate(sana.split("-"))]
            # Melisman jatkoviiva on oma <lyric> ilman tekstiä; se ei ole
            # tavu eikä kuulu virtaan.
            virta = [(m, ly) for m in part.findall("measure")
                     if int(m.get("number")) >= int(tahti)
                     for n in m.findall("note") for ly in lyriikat(n)
                     if teksti(ly) is not None]
            assert len(virta) >= len(odotetut), (
                f"t.{tahti}: {len(odotetut)} tavua annettu, "
                f"tiedostossa {len(virta)}")
            muutettu = 0
            for (m, ly), (sana, tavu, montako, j) in zip(virta, odotetut):
                assert teksti(ly) == tavu, (
                    f"t.{m.get('number')}: odotettiin tavua {tavu!r} "
                    f"(sanassa {sana!r}), on {teksti(ly)!r}")
                oikea = ("single" if montako == 1 else
                         "begin" if j == 0 else
                         "end" if j == montako - 1 else "middle")
                elem = ly.find("syllabic")
                if elem is None:
                    elem = ET.Element("syllabic")
                    ly.insert(0, elem)
                if elem.text != oikea:
                    elem.text = oikea
                    muutettu += 1
            selosteet.append(f"t.{tahti}: tavutus, {muutettu} merkintää "
                             f"korjattu ({len(odotetut)} tavua tarkistettu)")

        elif laji == "lisaa_tauko":
            # Konelukema pudottaa taukoja, ja silloin tahti jää lyhyeksi:
            # nuotti soi tahdin alusta vaikka sen pitäisi soida vasta
            # myöhemmältä iskulta. Painetulla sivulla haitta on pieni, koska
            # MuseScore asettelee yksinäisen nuotin suunnilleen oikeaan
            # kohtaan, mutta harjoitustiedostossa se soi väärällä iskulla.
            #
            # Odotettu summa annetaan riviltä eikä päätellä: tämä on ainoa
            # toimenpide joka tarkoituksella muuttaa tahdin pituutta, joten
            # oikea pituus on juuri se asia, joka pitää sanoa ja tarkistaa.
            arvo, summa = args
            aani = note.findtext("voice") or "1"
            tauko = ET.Element("note")
            ET.SubElement(tauko, "rest")
            kesto, loput = arvo.split("/")
            tyyppi = loput.rstrip(".")
            ET.SubElement(tauko, "duration").text = kesto
            ET.SubElement(tauko, "voice").text = aani
            ET.SubElement(tauko, "type").text = tyyppi
            for _ in range(len(loput) - len(tyyppi)):
                ET.SubElement(tauko, "dot")
            measure.insert(list(measure).index(note), tauko)
            nyt = kestosummat(measure).get(aani)
            assert nyt == int(summa), (
                f"t.{tahti}: äänen {aani} summa on {nyt}, odotettiin {summa}")
            selosteet.append(f"t.{tahti}: lisätty tauko {arvo} nuotin {i} "
                             f"eteen (äänen {aani} summa nyt {nyt})")

        elif laji == "poista_nuotti":
            (odotettu,) = args
            assert kuvaa(note) == odotettu, (
                f"t.{tahti} nuotti {i}: odotettiin {odotettu}, "
                f"on {kuvaa(note)}")
            measure.remove(note)
            selosteet.append(f"t.{tahti}: poistettu ylimääräinen {odotettu}")

        else:
            raise AssertionError(f"tuntematon toimenpide {laji}")

    for tahti, summat in ennen.items():
        nyt = kestosummat(tahdit[tahti])
        assert nyt == summat, (
            f"t.{tahti}: kestojen summa muuttui {summat} -> {nyt}; "
            f"rytmin uudelleenjaon pitää täyttää tahti täsmälleen")

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
    # Sama tiedosto voi saada korjauksia useaan osastoon; luetaan ja
    # kirjoitetaan se kerran.
    tiedostoittain = OrderedDict()
    for osa in list(OSAT) + list(SAVELLAJIT):
        tiedostoittain.setdefault((osa.mxl, osa.out), []).append(osa)

    for (mxl, out), osat in tiedostoittain.items():
        root = load(mxl)
        print(f"{mxl} -> {out}")
        for osa in osat:
            if isinstance(osa, Savellaji):
                print("  sävellajit (kaikki osastot)")
                for mista, mihin, fifths in osa.siirrot:
                    for s in siirra_savellaji(root, mista, mihin, fifths,
                                              osa.valmiit):
                        print("    " + s)
                continue
            selosteet = sovella(find_part(root, osa.osasto), osa)
            print(f"  {osa.osasto} ({osa.nimi})")
            for s in selosteet:
                print("    " + s)
        if dry:
            print("  (kuiva ajo, mitään ei kirjoitettu)")
        else:
            save(root, mxl, out)
            print(f"  kirjoitettu {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
