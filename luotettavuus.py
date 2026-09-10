#!/usr/bin/env python3
"""Mikä stemmoissa on tarkistettu ja mikä ei.

Tämä on ihmisen arvio eikä laskettu suure, joten se ylläpidetään käsin.
Lähde on docs/tyopaivakirja/, johon jokainen tarkistus on kirjattu.

Rakenne on oletus plus poikkeukset: valtaosa on tarkistamatta, ja jokainen
poikkeus on kohta jossa on tehty oikeaa työtä tai jossa tiedetään olevan
vikaa. "Ei kuoroa" ei ole poikkeus vaan lasketaan yhdista.MAPPINGista, joten
solistiosat eivät tarvitse ylläpitoa lainkaan.

Merkintä on lupaus lukijalle. Älä merkitse mitään varmistetuksi ilman että
se on vertailtu riippumattomaan lähteeseen nuotti nuotilta tai tavu tavulta.

Tämä tiedosto on taulukon lähde, mutta ei se muoto jota luetaan: sivusto ja
README viittaavat tiedostoon LUOTETTAVUUS.md, jonka tämä skripti kirjoittaa.
Muokkaa siis taulukkoa täällä ja aja `python3 luotettavuus.py` perässä; testi
kaatuu jos md-tiedosto on jäänyt jälkeen.

Käyttö:  python3 luotettavuus.py [--kuiva]
"""

import sys
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
        "käsin, useimmat laulajan kuulohavainnon perusteella. Lisäksi yhden "
        "b:n purku siirretty tahtiin 56, jonne lähdesivu sen painaa; "
        "konelukema oli merkinnyt sen kolme tahtia myöhemmäksi. Nuotit "
        "vertailtu kuoron omaan tiedostoon tahdeissa 1–78: kaksi eroa, "
        "kumpikin ratkesi lähdesivun hyväksi (t.35 palautusmerkki, t.52 "
        "nouseva kromatiikka). Kyrie tahdista 79 eteenpäin on vertailematta, "
        "koska kuorotiedoston tahdit eivät siellä osu meidän tahteihin. "
        "Laulaja luki 2026-09-10 nuottikirjasta kaksi näistä: t.35:n "
        "palautusmerkki on kirjassa, ja t.51–52:n tavu \"nis\" on tahdin 51 "
        "toisella nuotilla jatkoviivan kanssa — molemmat nyt kolmen lähteen "
        "varassa."),
    ("I", ("Kuoro S", "Kuoro A")): _osittain(
        "Sanat korjattu koneellisesti lähde-PDF:ää vasten, peitto 83–91 %, "
        "mutta ei tarkistettu tavu tavulta; \"et lux per-pe-tu-a\" korjattu "
        "käsin tahdeissa 21–22. Nuotit vertailtu kuoron omaan tiedostoon "
        "tahdeissa 1–78 ja jokainen ero mitattu lähdesivun nuottifontin "
        "koordinaateista: konelukemisen sävellajivirhe tahdeissa 28–34 (\"Te "
        "decet hymnus\" ristillisenä) korjattu, seitsemän säveltä, ja "
        "sopraanon t.76 Ces5 → C5. Kyrie tahdista 79 eteenpäin on "
        "vertailematta. Yksi ero jäi auki: alton t.77 on lähdesivulla Gis5, "
        "mutta kuorotiedosto laulaa Gis4:n, ja hyppy kuulostaa "
        "painovirheeltä."),
    ("I", ("Kuoro T",)): _osittain(
        "Sanat korjattu koneellisesti lähde-PDF:ää vasten, peitto 83–91 %, "
        "mutta ei tarkistettu tavu tavulta; \"et lux per-pe-tu-a\" ja "
        "\"lu-ce-at\" korjattu käsin. Nuotit vertailtu kuoron omaan "
        "tiedostoon tahdeissa 1–78: t.43 puuttunut risti lisätty (C5 → "
        "Cis5), ja kaksi muuta eroa ratkesi lähdesivun hyväksi. Kyrie "
        "tahdista 79 eteenpäin on vertailematta."),

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
        "Käyty läpi Edition Petersiä vasten ja laulettu harjoituksissa. "
        "Kolme kuulemalla löytynyttä sanavirhettä korjattu: tahti 366 "
        "(\"sal-va le\" → \"sal-va me\") sekä tahdit 340–341 ja 362–363, "
        "joissa säkeistön kolmesta säkeestä toistui yksi liikaa ja yksi "
        "puuttui. Divisin sanarivit tahdeissa 367–369 olivat päittäin ja "
        "ykkösbasson teksti viivaston yläpuolella; korjattu. Nuotit "
        "vertailtu kuoron omaan tiedostoon koko osan matkalta: ainoa ero oli "
        "tahti 343, jonka koruäänenä oli iso terssi puolisävelaskeleen "
        "sijasta, ja se korjattiin."),
    ("II·6", ("Kuoro S", "Kuoro A")): _osittain(
        "Nuotit vertailtu kuoron omaan tiedostoon koko osan matkalta: ei "
        "yhtään sävelerhoa. Sanoja ei ole tarkistettu."),
    ("II·6", ("Kuoro T",)): _osittain(
        "Nuotit vertailtu kuoron omaan tiedostoon koko osan matkalta. "
        "Viivastolla on kolme ääntä, joten vertailu koskee ylintä; ainoa ero "
        "oli tahti 353, joka oli oktaavia liian korkealla, ja se "
        "korjattiin — tenori ja basso laulavat siinä unisonossa. Sanoja ei "
        "ole tarkistettu."),

    ("II·9b", ("Kuoro B",)): _varmistettu(
        "Sanat tarkistettu lähde-PDF:ää vasten nuotti nuotilta. Nuotit "
        "vertailtu kuoron omaan tiedostoon koko 51 tahdin matkalta: ainoa ero "
        "oli tahti 607, jonka \"di-es\" oli konelukemassa puhtaana G:nä, ja "
        "laulaja luki 2026-09-10 nuottikirjasta G♭:n — korjattu kuoron "
        "tiedoston mukaiseksi. Tahtiin 607 on lisätty myös dynamiikkamerkintä "
        "p, jota lähteessä ei ollut."),
    ("II·9b", SAT): _tarkistamatta(
        "Konelukemisen tulosta. Nuotteja ilman tavua on selvästi enemmän kuin "
        "bassossa; osa on aitoja melismoja, mutta sitä ei ole tarkistettu "
        "yksitellen. Sanan \"Sy-bil-la\" tavutus korjattu kaikilta neljältä "
        "ääneltä ja altolta lisätty puuttunut \"cum\"."),

    ("II·10", ("Kuoro B",)): _varmistettu(
        "Jokainen nuotti vertailtu kuoron omaan tiedostoon ja jokainen tavu "
        "painettuun lähde-PDF:ään nuottitarkkuudella. Lisäksi tahdeissa "
        "657–665 korjattiin teksti, joka on väärin myös painetussa "
        "editiossa: sen ratkaisi se, että sama aihe kantaa samassa "
        "imitaatiossa tekstiä \"hu-ic er-go\" tenorilla, altolla ja "
        "sopraanolla. Tahtien 681–698 tavuviivat olivat rikki 2026-09-03 "
        "lähtien — tavut ja niiden paikat oikein, mutta ketjumerkinnät "
        "korvattujen sanojen mukaiset, joten stemmassa luki \"re qui em,\" "
        "erillisinä sanoina. Korjattu 2026-09-09."),
    ("II·10", ("Kuoro T",)): _puutteita(
        "Tekstiaukko tahdissa 688. Muuten tarkistamatta."),

    ("IV", ("Kuoro B",)): Tila(
        "◑", "käyty läpi",
        "Käyty läpi Edition Petersiä vasten ja laulettu harjoituksissa; puuttunut tavu lisätty tahdeissa "
        "99–100 (\"coe-li\"), ja sama puute korjattiin altolta ja "
        "tenorilta. Huomaa että Sanctuksessa Basso II lukee kaksoiskuoron "
        "toista riviä (Kuoro B II), jota tämä taulukko ei kata."),

    ("V", ("Kuoro B",)): _osittain(
        "Nuotit vertailtu kuoron omaan tiedostoon nuotti nuotilta koko 74 "
        "tahdin matkalta, ei yhtään eroa. 15 virhettä löytyi ja korjattiin, "
        "muun muassa neljä kokonaan tyhjää tahtia ja kaksi kohtaa joissa "
        "konelukija oli lukenut väärää viivastoa kuoron vaietessa. "
        "Sanat sen sijaan eivät ole tavu tavulta tarkistettuja: kuoron "
        "tiedostossa ei ole sanoja lainkaan, ja tehty tarkistus on ollut "
        "\"kantaako joka nuotti tavun\", mikä ei näe väärää tavua. "
        "2026-09-10 laulaja kuuli tahdeista 40-42 sellaisen: konelukema oli "
        "kopioinut bassolle ylä-äänten \"do-na, do-na\" -kuvion, kun bassolla "
        "on siellä yksi melisma."),
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


# Merkkien selitteet lukijalle. Nämä ovat yleisiä kuvauksia merkinnän
# tasosta; osakohtaiset perustelut tulevat POIKKEUKSISTA.
MERKINNAT = [
    ("✔", "varmistettu",
     "Koko osa vertailtu riippumattomaan lähteeseen nuotti nuotilta ja tavu "
     "tavulta."),
    ("◑", "käyty läpi / osittain",
     "Tehty oikeaa tarkistustyötä, mutta ei koko osaa järjestelmällisesti; "
     "ks. osakohtainen perustelu."),
    ("○", "tarkistamatta", TARKISTAMATTA.perustelu),
    ("⚠", "puutteita", "Tiedetään virheellistä tai puuttuvaa sisältöä."),
    ("–", "ei kuoroa", EI_KUOROA.perustelu),
]

# Repon juuressa, ei polut.py:n kautta: se reitittää nuottiaineistoa, ja
# tämä on dokumentaatiota.
MD_TIEDOSTO = "LUOTETTAVUUS.md"

# Lyhenne otsikkoriville; koko nimi olisi taulukossa turhan leveä.
_LYHENNE = {"Kuoro S": "S", "Kuoro A": "A", "Kuoro T": "T", "Kuoro B": "B"}


def _rivit_perusteluihin(numero):
    """Osan poikkeukset ryhmiteltyinä: (äänet, Tila) samalla perustelulla.

    Sama perustelu koskee usein kolmea ylempää ääntä, ja kolme kertaa
    toistettuna se olisi vain luettavan tekstin tiellä.
    """
    ryhmat = []
    for aani in AANET:
        poikkeus = POIKKEUKSET.get((numero, aani))
        if not poikkeus or not on_kuoroa(numero, aani):
            continue
        if ryhmat and ryhmat[-1][1] == poikkeus:
            ryhmat[-1][0].append(aani)
        else:
            ryhmat.append(([aani], poikkeus))
    return ryhmat


def markdown():
    """LUOTETTAVUUS.md kokonaisuudessaan.

    Sivusto ja README viittaavat tähän eivätkä lähdekoodiin: taulukon
    lukijalla ei ole asiaa Pythonin sisään.
    """
    o = []
    o.append("# Mikä stemmoissa on tarkistettu")
    o.append("")
    o.append("<!-- Generoitu tiedosto: `python3 luotettavuus.py`. "
             "Muokkaa `luotettavuus.py`:tä, älä tätä. -->")
    o.append("")
    o.append("Tämä taulukko on ihmisen arvio eikä laskettu suure: sen lähde on "
             "työpäiväkirja")
    o.append("[`docs/tyopaivakirja/`](docs/tyopaivakirja/), johon jokainen "
             "tarkistus on kirjattu. Merkintä on lupaus")
    o.append("lukijalle — mitään ei ole merkitty varmistetuksi ilman että se on "
             "vertailtu")
    o.append("riippumattomaan lähteeseen nuotti nuotilta tai tavu tavulta.")
    o.append("")
    o.append(f"Vertailunuotti on **{REFERENSSI}**, jota vasten kuorobasso on "
             "käyty läpi ja jonka")
    o.append("mukaiset stemmojen tahtinumerot ovat.")
    o.append("")
    o.append("**Kuorobasso on käyty läpi, muut äänet eivät.** Syy on "
             "yksinkertainen: tekijä laulaa")
    o.append("bassoa. Basso on siksi oletuksena ◑ ja muut äänet ○.")
    o.append("")

    o.append("## Merkinnät")
    o.append("")
    o.append("| Tila | Merkitys |")
    o.append("|---|---|")
    for merkki, nimi, selite in MERKINNAT:
        o.append(f"| {merkki} {nimi} | {selite} |")
    o.append("")

    o.append("## Osa kerrallaan")
    o.append("")
    o.append("| Osa | Nimi | " + " | ".join(_LYHENNE[a] for a in AANET) + " |")
    o.append("|---|---|" + "---|" * len(AANET))
    for numero, otsikko, tilat in taulukko():
        o.append(f"| {numero} | {otsikko} | "
                 + " | ".join(t.merkki for t in tilat) + " |")
    o.append("")

    o.append("## Perustelut")
    o.append("")
    o.append("Vain ne kohdat, joissa on tehty oikeaa tarkistustyötä tai joissa "
             "tiedetään olevan")
    o.append("vikaa. Muut ovat oletuksia: kuorobasso ◑, muut äänet ○.")
    o.append("")
    o.append(f"**Kuorobasso, oletus ({KUORO_B_OLETUS.merkki} "
             f"{KUORO_B_OLETUS.nimi}).** {KUORO_B_OLETUS.perustelu}")
    o.append("")
    for _tiedosto, numero, otsikko in yhdista.MOVEMENTS:
        ryhmat = _rivit_perusteluihin(numero)
        if not ryhmat:
            continue
        o.append(f"### {numero} {otsikko}")
        o.append("")
        for aanet, t in ryhmat:
            aanet = ", ".join(_LYHENNE[a] for a in aanet)
            o.append(f"- **{aanet} — {t.merkki} {t.nimi}:** {t.perustelu}")
        o.append("")
    return "\n".join(o).rstrip("\n") + "\n"


def main(argv):
    teksti = markdown()
    if "--kuiva" in argv:
        print(teksti, end="")
        return
    with open(MD_TIEDOSTO, "w", encoding="utf-8") as f:
        f.write(teksti)
    print(f"kirjoitettu {MD_TIEDOSTO}")


if __name__ == "__main__":
    main(sys.argv[1:])
