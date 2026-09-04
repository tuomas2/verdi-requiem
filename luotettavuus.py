#!/usr/bin/env python3
"""Mikä stemmoissa on tarkistettu ja mikä ei.

Tämä on ihmisen arvio eikä laskettu suure, joten se ylläpidetään käsin.
Lähde on CLAUDE.md:n työhistoria, johon jokainen tarkistus on kirjattu.

Rakenne on oletus plus poikkeukset: valtaosa on tarkistamatta, ja jokainen
poikkeus on kohta jossa on tehty oikeaa työtä tai jossa tiedetään olevan
vikaa. "Ei kuoroa" ei ole poikkeus vaan lasketaan yhdista.MAPPINGista, joten
solistiosat eivät tarvitse ylläpitoa lainkaan.

Merkintä on lupaus lukijalle. Älä merkitse mitään varmistetuksi ilman että
se on vertailtu riippumattomaan lähteeseen nuotti nuotilta tai tavu tavulta.
"""

from collections import namedtuple

import yhdista

Tila = namedtuple("Tila", "merkki nimi perustelu")

AANET = ["Kuoro S", "Kuoro A", "Kuoro T", "Kuoro B"]

EI_KUOROA = Tila("–", "ei kuoroa",
                 "Osassa ei ole kuoroa lainkaan; sen laulavat solistit.")
TARKISTAMATTA = Tila("○", "tarkistamatta",
                     "Ei tunnettuja virheitä, mutta ei myöskään "
                     "järjestelmällisesti tarkistettu.")

# Painettu vertailunuotti, jota vasten kuorobasso on käyty läpi ja jonka
# mukaiset tahtinumerot ovat.
REFERENSSI = "Edition Peters"

# Kuorobasso on se rivi, jota tekijä itse lukee. Se on käyty läpi käsin
# Edition Petersin painosta vasten ja laulettu läpi harjoituksissa; virheitä
# on löytynyt kymmeniä ja ne on korjattu.
#
# Tämä ei ole sama asia kuin ✔, joka tarkoittaa koko osan järjestelmällistä
# vertailua nuotti nuotilta ja tavu tavulta. Kumpikin tapa löytää sitä mitä
# toinen ei: laulaen löytyvät myös editiovirheet, joita painetun sivun
# tarkistus ei voi löytää, ja järjestelmällisellä vertailulla se mitä korva
# ei huomaa, kuten yksittäinen puuttuva tavu melisman sisällä.
KUORO_B_OLETUS = Tila(
    "◑", "käyty läpi",
    f"Käyty läpi käsin {REFERENSSI}in painosta vasten, sekä nuotit että "
    "sanat, ja laulettu läpi harjoituksissa; löytyneet virheet on korjattu. "
    "Ei kuitenkaan käyty järjestelmällisesti läpi nuotti nuotilta koko osan "
    "matkalta.")


def _varmistettu(perustelu):
    return Tila("✔", "varmistettu", perustelu)


def _osittain(perustelu):
    return Tila("◑", "osittain", perustelu)


def _puutteita(perustelu):
    return Tila("⚠", "puutteita", perustelu)


def _tarkistamatta(perustelu):
    return Tila("○", "tarkistamatta", perustelu)


# Ylemmät äänet jakavat useimmiten saman kohtalon: sama tiedosto, sama työ
# tekemättä. Basso ei koskaan, koska se on ainoa erikseen läpikäyty ääni.
SAT = ("Kuoro S", "Kuoro A", "Kuoro T")

# (osanumero, äänet) -> Tila. Vain kohdat, joissa on tehty oikeaa työtä tai
# joissa tiedetään olevan vikaa. Kaikki muu on TARKISTAMATTA.
#
# Äänet luetellaan aina eksplisiittisesti. Aiemmin sopraanon merkintä
# levitettiin automaattisesti altolle ja tenorille, mikä oli väärin II·4:ssä:
# siellä juuri sopraano poikkeaa muista, eli altto ja tenori ovat
# erimielisyydessä sillä puolella joka näyttää oikealta.
_POIKKEUKSET = {
    ("I", ("Kuoro B",)): _osittain(
        "Sanat korjattu lähde-PDF:ää vasten ja kahdeksan kohtaa varmistettu "
        "käsin, useimmat laulajan kuulohavainnon perusteella. Nuotit ovat "
        "konelukemisen tulosta eikä niitä ole tarkistettu."),
    ("I", SAT): _tarkistamatta(
        "Sanat korjattu koneellisesti lähde-PDF:ää vasten, peitto 83–91 %, "
        "mutta ei tarkistettu tavu tavulta. Nuotit konelukemisen tulosta."),

    ("II·1", ("Kuoro B",)): _osittain(
        "Nuotit vertailtu kuoron omaan tiedostoon koko 91 tahdin matkalta; "
        "ainoa ero oli oktaavivirhe tahdissa 28, ja se korjattiin. Sanoja ei "
        "ole erikseen tarkistettu."),

    ("II·4", ("Kuoro B",)): _osittain(
        "Nuotit vertailtu kuoron omaan tiedostoon: 174 tahtia 177:stä täsmää, "
        "ja kolme puuttunutta yhden tahdin \"Dies irae\" -väliintuloa "
        "lisättiin. Sanoissa on ratkaisematon kohta, ks. sopraano."),
    ("II·4", ("Kuoro S",)): _puutteita(
        "Sopraanon teksti tahdeissa 247–254 eroaa altosta, tenorista ja "
        "bassosta: sopraanolla on ylimääräisiä \"Dies irae\" -kertauksia "
        "siinä missä muut laulavat \"Solvet saeclum\" toisen kerran. Nuotit "
        "on varmistettu oikeiksi kaikilla neljällä äänellä, joten kyse on "
        "vain tekstistä. Kumpi on oikea, ei ratkea ilman painettua "
        "nuottikirjaa."),

    ("II·6", ("Kuoro B",)): Tila(
        "◑", "käyty läpi",
        "Käyty läpi Edition Petersiä vasten ja laulettu harjoituksissa; yksi kuulemalla löytynyt sanavirhe "
        "korjattu tahdissa 366 (\"sal-va le\" → \"sal-va me\")."),

    ("II·9b", ("Kuoro B",)): _osittain(
        "Sanat tarkistettu lähde-PDF:ää vasten nuotti nuotilta. Nuotit ovat "
        "konelukemisen tulosta ja tarkistamatta yhtä rakenteellista "
        "pistokoetta lukuun ottamatta."),
    ("II·9b", SAT): _tarkistamatta(
        "Konelukemisen tulosta. Nuotteja ilman tavua on selvästi enemmän kuin "
        "bassossa; osa on aitoja melismoja, mutta sitä ei ole tarkistettu "
        "yksitellen."),

    ("II·10", ("Kuoro B",)): _varmistettu(
        "Jokainen nuotti vertailtu kuoron omaan tiedostoon ja jokainen tavu "
        "painettuun lähde-PDF:ään nuottitarkkuudella. Lisäksi tahdeissa "
        "657–665 korjattiin teksti, joka on väärin myös painetussa "
        "editiossa: sen ratkaisi se, että sama aihe kantaa samassa "
        "imitaatiossa tekstiä \"hu-ic er-go\" tenorilla, altolla ja "
        "sopraanolla."),
    ("II·10", ("Kuoro T",)): _puutteita(
        "Tekstiaukko tahdissa 688. Muuten tarkistamatta."),

    ("IV", ("Kuoro B",)): Tila(
        "◑", "käyty läpi",
        "Käyty läpi Edition Petersiä vasten ja laulettu harjoituksissa; puuttunut tavu lisätty tahdeissa "
        "99–100 (\"coe-li\"), ja sama puute korjattiin altolta ja "
        "tenorilta. Huomaa että Sanctuksessa Basso II lukee kaksoiskuoron "
        "toista riviä (Kuoro B II), jota tämä taulukko ei kata."),

    ("V", ("Kuoro B",)): _varmistettu(
        "Vertailtu kuoron omaan tiedostoon nuotti nuotilta koko 74 tahdin "
        "matkalta, ei yhtään eroa. 15 virhettä löytyi ja korjattiin, muun "
        "muassa neljä kokonaan tyhjää tahtia ja kaksi kohtaa joissa "
        "konelukija oli lukenut väärää viivastoa kuoron vaietessa."),
    ("V", SAT): _puutteita(
        "Konelukemisen tulosta ja selvästi kesken: sanapeitto 48–59 %, "
        "keksittyä sisältöä ja tyhjiä tahteja tahdeissa 59–74, ja teoksen "
        "loppusointu puuttuu kokonaan tahdista 72."),

    ("VII", ("Kuoro B",)): _osittain(
        "Nuotit vastaavat kuoron omaa tiedostoa yhtenä 67 tahdin lohkona "
        "(tahdit 44–110); ainoa poikkeama on divisi, jonka kaksi lähdettä "
        "kirjoittavat eri tavoin. Muu osa ja sanat tarkistamatta."),
}

POIKKEUKSET = {(osa, aani): t
               for (osa, aanet), t in _POIKKEUKSET.items()
               for aani in aanet}

# Osanumerosta lähdetiedostoon, jotta MAPPINGista voi kysyä onko kuoroa.
_TIEDOSTO = {numero: tiedosto for tiedosto, numero, _otsikko in yhdista.MOVEMENTS}


def on_kuoroa(osanumero, aani):
    """Laulaako tämä ääni tässä osassa lainkaan.

    Luetaan MAPPINGista eikä ylläpidetä käsin: jos osan kartoitus muuttuu,
    tämä seuraa perässä itsestään.
    """
    return aani in yhdista.MAPPING.get(_TIEDOSTO[osanumero], {})


def tila(osanumero, aani):
    """Tarkistuksen tila yhdelle osalle ja äänelle."""
    if not on_kuoroa(osanumero, aani):
        return EI_KUOROA
    poikkeus = POIKKEUKSET.get((osanumero, aani))
    if poikkeus:
        return poikkeus
    if aani == "Kuoro B":
        return KUORO_B_OLETUS
    return TARKISTAMATTA


def taulukko():
    """Koko taulukko riveinä: (osanumero, otsikko, [Tila per ääni])."""
    return [(numero, otsikko, [tila(numero, a) for a in AANET])
            for _tiedosto, numero, otsikko in yhdista.MOVEMENTS]


if __name__ == "__main__":
    for numero, otsikko, tilat in taulukko():
        print(f"{numero:6} {otsikko:24} " + "  ".join(t.merkki for t in tilat))
