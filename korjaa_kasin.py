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


@dataclass(frozen=True)
class Osa:
    """Yksi osa: mistä luetaan, mihin kirjoitetaan, mitä korjataan."""

    mxl: str            # lähde, jota ei koskaan muokata
    out: str            # tulos, jonka yhdista.py lukee
    osasto: str         # osaston tunnus lähteessä
    nimi: str           # viivaston nimi raporttiin
    yksi_sanarivi: bool  # nostetaanko kaikki tavut sanariville 1
    korjaukset: tuple   # (tahti, nuotti, toimenpide, argumentit...)


# Toimenpiteet:
#   ("poista", teksti)                  poista tavu, jonka teksti on tämä
#   ("lisaa", syllabic, teksti)         lisää tavu nuotille jolla ei ole
#   ("aseta", vanha, syllabic, teksti)  korvaa tavu toisella
#   ("jatka",)                          lisää tavuun melisman jatkoviiva
#   ("korkeus", vanha, uusi)            vaihda nuotin korkeus, esim. "A3"->"A2"
#   ("kesto", vanha, uusi)              vaihda nuottiarvo, esim.
#                                       "256/quarter" -> "192/eighth."
#                                       (piste per pisteellisyys)
#   ("lisaa_aksentti",)                 lisää aksentti nuotille jolla ei ole
#   ("poista_aksentti",)                poista nuotin aksentti
#   ("poista_nuotti", kuvaus)           poista nuotti tai tauko
#   ("kopioi_tahti", lähdetahti)        korvaa tauolla oleva tahti toisen
#                                       tahdin sisällöllä, sanat mukaan lukien
# Nuotti on indeksi tahdin <note>-alkioissa, tauot mukaan luettuina, tai None
# kun toimenpide koskee koko tahtia.
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
        # Sivu 2: "o-ra-ti-o-nem me-am," päättyy tähän, joten "am" on sanan
        # viimeinen tavu eikä keskimmäinen. Väärä syllabic jättää tavuviivan
        # roikkumaan seuraavan tavun perään.
        ("49", 0, "aseta", "am", "end", "am"),

        # Sivu 3: "ad te om-nis ca-ro ve-ni-et." Laulaja pyysi melisman
        # tavulle "om", jolloin "nis" tulee vasta tahdin 52 viimeiselle
        # nuotille. HUOM: lähde-PDF merkitsee sen toisin päin — "nis" tahdin
        # 51 kolmannelle iskulle ja melisma sen jälkeen. Jos kuoron
        # nuottikirja on PDF:n kannalla, nämä kaksi riviä vaihdetaan päittäin.
        ("51", 1, "poista", "nis"),
        ("52", 3, "lisaa", "end", "nis"),

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

# Rex tremendae (II·6), paikallinen tahti 45 = juokseva 366. Laulaja raportoi,
# että tahdin ensimmäisellä nuotilla pitää olla "me" eikä "le" — teksti on
# "sal-va me". Kirjoitusvirhe lähdetiedostossa, ja se näkyy siitä että
# kuorosopraano (P5) laulaa samassa tahdissa samalla iskulla "me,". Basson
# ympäristö on jo oikein: t.44 "sal-va", t.45 "sal-va", t.46 "me,".
OSA_II6 = Osa(
    mxl="07-Verdi-Rex.mxl",
    out="07-Verdi-Rex-kasin.mxl",
    osasto="P8",
    nimi="Kuoro B",
    yksi_sanarivi=False,
    korjaukset=(
        ("45", 0, "aseta", "le,", "single", "me,"),
    ),
)

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
OSAT = ([OSA_I, OSA_II1] + OSAT_II4
        + [OSA_II6, OSA_II10_KUORO_B, OSA_II10_DIVISI] + OSAT_IV
        + [OSA_VII_TENORI, OSA_VII])


def lyriikat(note):
    return note.findall("lyric")


def teksti(lyric):
    return lyric.findtext("text")


def uusi_lyric(syllabic, text):
    ly = ET.Element("lyric", {"number": "1"})
    ET.SubElement(ly, "syllabic").text = syllabic
    ET.SubElement(ly, "text").text = text
    return ly


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
            ly[0].find("syllabic").text = syllabic
            ly[0].find("text").text = text
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
    for osa in OSAT:
        tiedostoittain.setdefault((osa.mxl, osa.out), []).append(osa)

    for (mxl, out), osat in tiedostoittain.items():
        root = load(mxl)
        print(f"{mxl} -> {out}")
        for osa in osat:
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
