#!/usr/bin/env python3
"""Latinan sanojen suomennos stemman toiselle sanariville.

Tarkoitus on latinan opiskelu laulamisen ohessa: sama idea kuin
`sivusto/requiem.html`:n rinnakkaisessa suomennoksessa, mutta siinä
kohdassa nuottia, jossa sana lauletaan. Käännökset on poimittu siitä
samasta suomennoksesta, joka on tarkoituksella sanatarkka ja seuraa
latinan sanajärjestystä.

**Suomen sana ei tavutu eikä sitä tavuteta.** Koko sana tulee latinan sanan
ensimmäisen tavun alle, myös silloin kun latinan sana venyy melisman yli
usean tahdin matkalle:

    ex  -  au  -  di        o - ra - ti - o - nem
    kuule                   rukous

Kolme asiaa, jotka piti mitata ennen kuin tämä toimi:

- **Fonttikoko tulee tavun mukana, ei tyylitiedostosta.** MuseScoren
  tyyliavain `lyricsEvenFontSize` ei tee mitään: kun se asetettiin 6:een ja
  `lyricsOddFontSize` 14:ään, *molemmat* rivit tulivat 14 pt:llä. Toimiva
  tapa on MusicXML:n `<text font-size="...">` tavun sisällä. Mitattu
  lukemalla renderöidyn PDF:n tekstikerros (`mutool draw -F stext`), ei
  katsomalla kuvaa.
- **Suomennos ei maksa sivuja.** Basso I pysyi 16-sivuisena. Kokeiltiin myös
  pahin tapaus, jossa kaikki 708 sanaa saivat 11 merkin täytesanan: silti 16
  sivua. Rivi mahtuu tilaan, joka on jo varattu tahtinumeroille ja
  sanoille.
- **Suomennos alkaa samasta kohdasta kuin latinan tavu**, ei keskitettynä
  sen alle. MuseScore keskittää joka tavun nuotinpään kohdalle, joten
  tavuaan pidempi suomennos alkoi edellisen sanan alta ja lukija joutui
  arvaamaan, kumman sanan käännös se on: "lu-ce-at"-tavun alla oleva
  "loistakoon" alkoi 10,6 pistettä ennen tavuaan. Siirto tehdään
  MusicXML:n <lyric relative-x>:llä ja lasketaan mitatuista
  merkkileveyksistä (LEVEYDET). Mediaanivirhe putosi 4,3 pisteestä 0,2:een.
- **Sanarivi on yksi enemmän kuin tahdissa on käytössä**, ei kiinteä 2.
  Lacrymosan tahdeissa 677-679 kuoron basso on divisi ja sen kaksi ääntä
  laulavat eri tekstiä riveillä 1 ja 2 (ks. CLAUDE.md, 2026-09-07), joten
  siellä suomennos menee riville 3. Kiinteä 2 olisi kirjoittanut alemman
  äänen tekstin päälle.

`yhdista.py` kutsuu tätä viimeisenä vaiheena, `normalise_lyrics`:n jälkeen —
se nostaa eksyneet tavut riville 1 eikä osaisi erottaa suomennosta niistä.
Lipulla `--ei-suomennosta` koko vaihe jää pois.

Ilman argumentteja tämä tiedosto on raporttityökalu: se kertoo, mitkä
partituurin sanat eivät ole sanastossa.

    python3 suomennos.py                     # koko partituuri
    python3 suomennos.py stemma-basso-1.mxl  # yksi stemma

Lipulla --teksti se tulostaa tekstin juoksevana proosana, suomennos latinan
alla ja tuntemattomat sanat kaarisulkeissa. Se on tarkistus, jota
nuottikuvasta ei voi tehdä: koko teksti kerralla luettuna väärä suomennos ja
rikkinäinen tavutus ("re qui em" ilman väliviivoja) näkyvät heti.

    python3 suomennos.py --teksti stemma-basso-1.mxl
"""
import collections
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

import polut

# Suomennoksen fonttikoko pisteinä; latina on 10 pt.
KOKO = "6.5"

# Sanasto on sanamuoto -> suomennos, eli sama muoto käännetään koko teoksessa
# samoin. Se on tietoinen valinta: apusanat joutuvat kompromissiin (`in` on
# aina "-ssa", vaikka "in favilla" on "tuhkaan"), mutta taulukko pysyy yhtenä
# 120 rivin listana eikä paisu tahtikohtaisiksi poikkeuksiksi.
#
# Kommentit ovat requiem.html:n omia rivejä, jotta käännöstä voi verrata
# lähteeseensä lukemalla, ei etsimällä.
SANASTO = {
    # I Requiem & Kyrie
    # "Requiem aeternam dona eis, Domine" | "Ikuinen lepo anna heille, Herra"
    "requiem": "lepo",
    "aeternam": "ikuinen",
    "dona": "anna",
    "eis": "heille",
    "domine": "Herra",
    # "et lux perpetua luceat eis" | "ja ainainen valo loistakoon heille"
    "et": "ja",
    "lux": "valo",
    "perpetua": "ainainen",
    "luceat": "loistakoon",
    # "Te decet hymnus, Deus, in Sion" | "Sinulle sopii ylistysvirsi, Jumala,
    # Siionissa"
    "te": "sinulle",
    "decet": "sopii",
    "hymnus": "ylistysvirsi",
    "deus": "Jumala",
    "in": "-ssa",
    "sion": "Siion",
    # "et tibi reddetur votum in Jerusalem" | "ja sinulle maksetaan lupaus
    # Jerusalemissa"
    "tibi": "sinulle",
    "reddetur": "maksetaan",
    "votum": "lupaus",
    "jerusalem": "Jerusalem",
    # "Exaudi orationem meam" | "Kuule rukoukseni"
    "exaudi": "kuule",
    "orationem": "rukous",
    "meam": "minun",
    # "ad te omnis caro veniet" | "sinun tykösi tulee kaikki liha"
    "ad": "tykö",
    "omnis": "kaikki",
    "caro": "liha",
    "veniet": "tulee",
    # "Kyrie eleison" / "Christe eleison" | "Herra, armahda" / "Kristus,
    # armahda"
    "kyrie": "Herra",
    "christe": "Kristus",
    "eleison": "armahda",

    # II Dies irae
    # "Dies irae, dies illa" | "Vihan päivä, se päivä"
    "dies": "päivä",
    "irae": "vihan",
    "illa": "se",
    # "solvet saeclum in favilla" | "hajottaa maailman tuhkaan"
    "solvet": "hajottaa",
    "saeclum": "maailman",
    "favilla": "tuhka",
    # "teste David cum Sibylla" | "todistajana Daavid Sibyllan kanssa"
    "teste": "todistajana",
    "david": "Daavid",
    "cum": "kanssa",
    "sybilla": "Sibylla",
    # "Quantus tremor est futurus" | "Kuinka suuri vapina on oleva"
    "quantus": "kuinka suuri",
    "tremor": "vapina",
    "est": "on",
    "futurus": "oleva",
    # "quando judex est venturus" | "kun tuomari on tuleva"
    "quando": "kun",
    "judex": "tuomari",
    "venturus": "tuleva",
    # "cuncta stricte discussurus!" | "kaiken tarkoin tutkiva!"
    "cuncta": "kaiken",
    "stricte": "tarkoin",
    "discussurus": "tutkiva",
    # "Tuba mirum spargens sonum" | "Torvi, joka levittää ihmeellistä ääntä"
    "tuba": "torvi",
    "mirum": "ihmeellistä",
    "spargens": "levittäen",
    "sonum": "ääntä",
    # "per sepulcra regionum" | "maiden hautojen halki"
    "per": "kautta",
    "sepulchra": "haudat",
    "regionum": "maiden",
    # "coget omnes ante thronum" | "ajaa kaikki valtaistuimen eteen"
    "coget": "ajaa",
    "omnes": "kaikki",
    "ante": "eteen",
    "thronum": "valtaistuimen",
    # "Rex tremendae majestatis" | "Kauhistuttavan majesteetin kuningas"
    "rex": "kuningas",
    "tremendae": "kauhistuttavan",
    "majestatis": "majesteetin",
    # "qui salvandos salvas gratis" | "joka pelastat lahjaksi ne, jotka on
    # pelastettava"
    "qui": "joka",
    "salvandos": "pelastettavat",
    "salvas": "pelastat",
    "gratis": "lahjaksi",
    # "salva me, fons pietatis" | "pelasta minut, laupeuden lähde"
    "salva": "pelasta",
    "me": "minut",
    "fons": "lähde",
    "pietatis": "laupeuden",
    # "Recordare, Jesu pie" | "Muista, hurskas Jeesus"
    "jesu": "Jeesus",
    "pie": "hurskas",
    # "Lacrymosa dies illa" | "Kyynelinen on se päivä"
    "lacrymosa": "kyynelinen",
    # "qua resurget ex favilla" | "jona nousee tuhkasta"
    "qua": "jona",
    "resurget": "nousee",
    "ex": "-sta",
    # "judicandus homo reus" | "syyllinen ihminen tuomittavaksi"
    "judicandus": "tuomittavaksi",
    "homo": "ihminen",
    "reus": "syyllinen",
    # "Huic ergo parce, Deus" | "Säästä siis häntä, Jumala"
    "huic": "häntä",
    "ergo": "siis",
    "parce": "säästä",
    # "dona eis requiem. Amen." | "anna heille lepo. Amen."
    "amen": "amen",

    # IV Sanctus
    # "Sanctus, Sanctus, Sanctus, Dominus Deus Sabaoth" | "Pyhä, pyhä, pyhä,
    # Herra Jumala Sebaot"
    "sanctus": "pyhä",
    "dominus": "Herra",
    "sabaoth": "Sebaot",
    # "Pleni sunt coeli et terra gloria tua" | "Täynnä ovat taivaat ja maa
    # sinun kunniaasi"
    "pleni": "täynnä",
    "sunt": "ovat",
    "coeli": "taivaat",
    "terra": "maa",
    "gloria": "kunnia",
    "tua": "sinun",
    # "Hosanna in excelsis" | "Hoosianna korkeuksissa"
    "hosanna": "hoosianna",
    "excelsis": "korkeuksissa",
    # "Benedictus qui venit in nomine Domini" | "Siunattu olkoon hän, joka
    # tulee Herran nimessä"
    "benedictus": "siunattu",
    "venit": "tulee",
    "nomine": "nimessä",
    "domini": "Herran",

    # V Agnus Dei
    # "Agnus Dei, qui tollis peccata mundi" | "Jumalan Karitsa, joka otat pois
    # maailman synnit"
    "agnus": "karitsa",
    "dei": "Jumalan",
    "tollis": "otat pois",
    "peccata": "synnit",
    "mundi": "maailman",
    # "dona eis requiem sempiternam" | "anna heille iankaikkinen lepo"
    "sempiternam": "iankaikkinen",

    # VII Libera me
    # "Libera me, Domine, de morte aeterna" | "Vapauta minut, Herra,
    # iankaikkisesta kuolemasta"
    "libera": "vapauta",
    "de": "-sta",
    "morte": "kuolema",
    "aeterna": "ikuinen",
    # "in die illa tremenda" | "sinä kauhistuttavana päivänä"
    "die": "päivänä",
    "tremenda": "kauhistuttava",
    # "quando coeli movendi sunt et terra" | "kun taivaat ja maa on määrä
    # liikuttaa"
    "movendi": "liikutettavat",
    # "dum veneris judicare saeculum per ignem" | "kun tulet tuomitsemaan
    # maailman tulella"
    "dum": "kun",
    "veneris": "tulet",
    "judicare": "tuomitsemaan",
    "saeculum": "maailman",
    "ignem": "tuli",
    # "calamitatis et miseriae" | "onnettomuuden ja kurjuuden"
    "calamitatis": "onnettomuuden",
    "miseriae": "kurjuuden",
    # "dies magna et amara valde" | "päivä suuri ja sangen katkera"
    "magna": "suuri",
    "amara": "katkera",
    "valde": "sangen",
    # "Tremens factus sum ego et timeo" | "Minä olen tullut vapisevaksi ja
    # pelkään"
    "tremens": "vapisevaksi",
    "factus": "tullut",
    "sum": "olen",
    "ego": "minä",
    "timeo": "pelkään",
    # "dum discussio venerit atque ventura ira" | "kun tutkinta on tuleva ja
    # viha, joka on tuleva"
    "discussio": "tutkinta",
    "venerit": "on tuleva",
    "atque": "ja",
    "ventura": "tuleva",

    # Tästä alkaen sanat, joita kuoro ei laula. Ne ovat partituurin
    # solistiviivastoilla, eivät missään kahdeksassa stemmassa, mutta ilman
    # niitä puolet partituurista jäisi puolitiehen suomennetuksi ja
    # raportti täyttyisi varoituksista, jotka eivät koskaan johda mihinkään.

    # II·3 Mors stupebit (basso)
    # "Mors stupebit et natura" | "Kuolema hämmästyy ja luonto"
    "mors": "kuolema",
    "stupebit": "hämmästyy",
    "natura": "luonto",
    # "cum resurget creatura, judicanti responsura" | "kun luotu nousee ylös
    # vastaamaan tuomitsevalle"
    "creatura": "luotu",
    "judicanti": "tuomitsevalle",
    "responsura": "vastaamaan",

    # II·4 Liber scriptus (mezzo)
    # "Liber scriptus proferetur" | "Kirjoitettu kirja tuodaan esiin"
    "liber": "kirja",
    "scriptus": "kirjoitettu",
    "proferetur": "tuodaan esiin",
    # "in quo totum continetur" | "johon kaikki on sisällytetty"
    "quo": "johon",
    "totum": "kaikki",
    "continetur": "sisältyy",
    # "unde mundus judicetur" | "jonka mukaan maailma tuomitaan"
    "unde": "josta",
    "mundus": "maailma",
    "judicetur": "tuomitaan",
    # "Judex ergo cum sedebit" | "Kun tuomari siis istuutuu"
    "sedebit": "istuutuu",
    # "quidquid latet apparebit" | "kaikki mikä on kätkössä tulee ilmi"
    "quidquid": "mikä ikinä",
    "latet": "on kätkössä",
    "apparebit": "tulee ilmi",
    # "nil inultum remanebit" | "mikään ei jää kostamatta"
    "nil": "mikään ei",
    "inultum": "kostamatta",
    "remanebit": "jää",

    # II·5 Quid sum miser (kvartetti)
    # "Quid sum miser tunc dicturus?" | "Mitä minä kurja olen silloin sanova?"
    "quid": "mitä",
    "miser": "kurja",
    "tunc": "silloin",
    "dicturus": "sanova",
    # "Quem patronum rogaturus" | "Ketä puolustajaa olen pyytävä"
    "quem": "ketä",
    "patronum": "puolustajaa",
    "rogaturus": "pyytävä",
    # "cum vix justus sit securus?" | "kun tuskin vanhurskas on turvassa?"
    "vix": "tuskin",
    "justus": "vanhurskas",
    "sit": "olisi",
    "securus": "turvassa",

    # II·7 Recordare (sopraano ja mezzo)
    # "Recordare, Jesu pie" | "Muista, hurskas Jeesus"
    "recordare": "muista",
    # "quod sum causa tuae viae" | "että minä olen sinun tiesi syy"
    "quod": "että",
    "causa": "syy",
    "tuae": "sinun",
    "viae": "tiesi",
    # "ne me perdas illa die" | "älä hukuta minua sinä päivänä"
    "ne": "älä",
    "perdas": "hukuta",
    # "Quaerens me, sedisti lassus" | "Minua etsien istuit uupuneena"
    "quaerens": "etsien",
    "sedisti": "istuit",
    "lassus": "uupuneena",
    # "redemisti crucem passus" | "lunastit ristin kärsittyäsi"
    "redemisti": "lunastit",
    "crucem": "ristin",
    "passus": "kärsittyäsi",
    # "tantus labor non sit cassus" | "niin suuri vaiva älköön olkoon turha"
    "tantus": "niin suuri",
    "labor": "vaiva",
    "non": "ei",
    "cassus": "turha",
    # "Juste judex ultionis" | "Koston vanhurskas tuomari"
    "juste": "vanhurskas",
    "ultionis": "koston",
    # "donum fac remissionis ante diem rationis" | "tee anteeksiannon lahja
    # ennen tilinteon päivää"
    "donum": "lahja",
    "fac": "tee",
    "remissionis": "anteeksiannon",
    "diem": "päivää",
    "rationis": "tilinteon",

    # II·8 Ingemisco (tenori)
    # "Ingemisco tamquam reus" | "Huokaan kuin syyllinen"
    "ingemisco": "huokaan",
    # Nuotissa on muoto "tanquam", requiem.html:ssä "tamquam"; sama sana.
    "tanquam": "kuin",
    "tamquam": "kuin",
    # "culpa rubet vultus meus" | "syyllisyydestä punoittavat kasvoni"
    "culpa": "syyllisyydestä",
    "rubet": "punoittavat",
    "vultus": "kasvot",
    "meus": "minun",
    # "supplicanti parce, Deus" | "säästä rukoilevaa, Jumala"
    "supplicanti": "rukoilevaa",
    # "Qui Mariam absolvisti" | "Sinä joka vapautit Marian synneistä"
    "mariam": "Marian",
    "absolvisti": "vapautit",
    # "et latronem exaudisti" | "ja kuulit ryövärin"
    "latronem": "ryövärin",
    "exaudisti": "kuulit",
    # "mihi quoque spem dedisti" | "annoit toivon myös minulle"
    "mihi": "minulle",
    "quoque": "myös",
    "spem": "toivon",
    "dedisti": "annoit",
    # "Preces meae non sunt dignae" | "Rukoukseni eivät ole arvollisia"
    "preces": "rukoukset",
    "meae": "minun",
    "dignae": "arvollisia",
    # "sed tu bonus fac benigne" | "mutta sinä hyvä, tee armollisesti"
    "sed": "mutta",
    "tu": "sinä",
    "bonus": "hyvä",
    "benigne": "armollisesti",
    # "ne perenni cremer igne" | "ettei minua poltettaisi ikuisessa tulessa"
    "perenni": "ikuisessa",
    "cremer": "poltettaisi",
    "igne": "tulessa",
    # "Inter oves locum praesta" | "Suo minulle paikka lampaiden joukossa"
    "inter": "joukossa",
    "oves": "lampaiden",
    "locum": "paikka",
    "praesta": "suo",
    # "et ab haedis me sequestra" | "ja erota minut vuohista". Nuotissa
    # "hoedis", requiem.html:ssä "haedis".
    "ab": "-sta",
    "hoedis": "vuohista",
    "haedis": "vuohista",
    "sequestra": "erota",
    # "statuens in parte dextra" | "asettaen minut oikealle puolelle"
    "statuens": "asettaen",
    "parte": "puolelle",
    "dextra": "oikealle",

    # II·9 Confutatis (basso)
    # "Confutatis maledictis" | "Kun kirotut on tuomittu vaikenemaan"
    "confutatis": "vaiennettuina",
    "maledictis": "kirotut",
    # "flammis acribus addictis" | "ankariin liekkeihin määrätyt"
    "flammis": "liekkeihin",
    "acribus": "ankariin",
    "addictis": "määrätyt",
    # "voca me cum benedictis" | "kutsu minut siunattujen kanssa"
    "voca": "kutsu",
    "benedictis": "siunattujen",
    # "Oro supplex et acclinis" | "Rukoilen nöyränä ja kumartuneena"
    "oro": "rukoilen",
    "supplex": "nöyränä",
    "acclinis": "kumartuneena",
    # "cor contritum quasi cinis" | "sydän murtuneena kuin tuhka"
    "cor": "sydän",
    "contritum": "murtuneena",
    "quasi": "kuin",
    "cinis": "tuhka",
    # "gere curam mei finis" | "pidä huolta lopustani"
    "gere": "pidä",
    "curam": "huolta",
    "mei": "minun",
    "finis": "lopusta",

    # III Offertorio (kvartetti)
    # "Domine Jesu Christe, Rex gloriae" | "Herra Jeesus Kristus, kunnian
    # kuningas"
    "gloriae": "kunnian",
    # "libera animas omnium fidelium defunctorum" | "vapauta kaikkien
    # uskovien vainajien sielut"
    "animas": "sielut",
    "omnium": "kaikkien",
    "fidelium": "uskovien",
    "defunctorum": "vainajien",
    # "de poenis inferni et de profundo lacu" | "helvetin vaivoista ja
    # syvästä kuilusta"
    "poenis": "vaivoista",
    "inferni": "helvetin",
    "profundo": "syvästä",
    "lacu": "kuilusta",
    # "Libera eas de ore leonis" | "Vapauta ne leijonan suusta"
    "eas": "ne",
    "ore": "suusta",
    "leonis": "leijonan",
    # "ne absorbeat eas tartarus" | "ettei manala niitä nielaisisi"
    "absorbeat": "nielaisisi",
    "tartarus": "manala",
    # "ne cadant in obscurum" | "etteivät ne putoaisi pimeyteen"
    "cadant": "putoaisi",
    "obscurum": "pimeyteen",
    # "sed signifer sanctus Michael" | "vaan lipunkantaja pyhä Mikael"
    "signifer": "lipunkantaja",
    "michael": "Mikael",
    # "repraesentet eas in lucem sanctam" | "johdattakoon ne pyhään valoon"
    "repraesentet": "johdattakoon",
    "lucem": "valoon",
    "sanctam": "pyhään",
    # "quam olim Abrahae promisisti et semini ejus" | "jonka aikoinaan
    # lupasit Abrahamille ja hänen jälkeläisilleen"
    "quam": "jonka",
    "olim": "aikoinaan",
    "abrahae": "Abrahamille",
    "promisisti": "lupasit",
    "semini": "jälkeläisille",
    "ejus": "hänen",
    # "Hostias et preces tibi, Domine, laudis offerimus" | "Uhreja ja
    # rukouksia me kannamme sinulle, Herra, ylistyksen uhreja"
    "hostias": "uhreja",
    "laudis": "ylistyksen",
    "offerimus": "kannamme",
    # "Tu suscipe pro animabus illis" | "Ota sinä ne vastaan niiden sielujen
    # puolesta"
    "suscipe": "ota vastaan",
    "pro": "puolesta",
    "animabus": "sielujen",
    "illis": "niiden",
    # "quarum hodie memoriam facimus" | "joita tänään muistamme"
    "quarum": "joiden",
    "hodie": "tänään",
    "memoriam": "muistoa",
    "facimus": "teemme",
    # "Fac eas, Domine, de morte transire ad vitam" | "Anna niiden, Herra,
    # siirtyä kuolemasta elämään"
    "transire": "siirtyä",
    "vitam": "elämään",

    # VI Lux aeterna (mezzo, tenori, basso)
    # "cum sanctis tuis in aeternum" | "pyhiesi kanssa iankaikkisesti"
    "sanctis": "pyhiesi",
    "tuis": "sinun",
    "aeternum": "iankaikkisuuteen",
    # "quia pius es" | "sillä sinä olet laupias". `es` jää ilman
    # suomennosta: kuoron stemmoissa sama muoto on aina "di-es"-sanan
    # katkennut jälkiosa, ja yksi käännös muotoa kohti ei voi olla
    # molempia. Ks. RIKKI["es"].
    "quia": "sillä",
    "pius": "laupias",
}

# Nämä "sanat" eivät ole latinaa vaan seurausta rikkinäisestä tavuketjusta:
# `syllabic` sanoo `single` tai `begin` keskellä sanaa, ja sanoja tavuista
# kokoava lukija näkee siksi kaksi sanaa yhden sijaan ("A" + "gnus"). Osa on
# lähteen kirjoitusvirheitä ("callamitatis", "Hosana").
#
# Ne on luetteloitu tässä, jotta raportti erottaa ne uudesta sanasta:
# tuntematon sana, joka EI ole tässä listassa, on joko sanastosta puuttuva
# käännös tai uusi vika. Lista on siis samalla tehtävälista — ks. CLAUDE.md,
# kohta "Suomennos paljasti rikkinäiset tavuketjut".
RIKKI = {
    # Katkennut tavuketju: sanan osat luetaan erillisinä sanoina.
    "a": "A-gnus / A-men",
    "gnus": "A-gnus",
    "e": "e-is / e-le-i-son",
    "is": "e-is",
    "ele": "e-le-i-son",
    "elei": "e-le-i-son",
    "leison": "e-le-i-son",
    "ison": "e-le-i-son",
    "son": "e-le-i-son",
    "le": "e-le-i-son",
    "i": "e-le-i-son",
    "do": "do-na",
    "na": "do-na",
    "di": "di-es",
    "es": "di-es",
    "dirae": "di-es i-rae",
    "rae": "i-rae",
    "il": "il-la",
    "la": "il-la",
    "quiem": "re-qui-em",
    "em": "re-qui-em",
    "ternam": "ae-ter-nam",
    "tatis": "pie-ta-tis",
    "ro": "ca-ro",
    "o": "o-ra-ti-o-nem",
    "vo": "vo-tum",
    "ira": "i-rae",
    "domi": "Do-mi-ne",
    # Kaksi sanaa kirjoitettu yhteen: edellisen sanan loppu ja seuraavan alku
    # samaan tavuun tai ilman sanarajaa.
    "dodoeis": "do-na e-is",
    "doena": "do-na",
    "doila": "do-na il-la",
    "requiemem": "re-qui-em",
    "requiemna": "re-qui-em do-na",
    # Kirjoitus- ja konelukuvirheitä lähteessä.
    "hosana": "Hosanna",
    "perpettua": "perpetua",
    "d": "?",
    # Solistiviivastot, samat viat. Suurin osa on osien 01 ja 14
    # konelukemisen jälkeä, ja "Kyrie eleison" on niistä pahin: se hajoaa
    # kymmeneen eri muotoon.
    "ky": "Ky-ri-e",
    "kyr": "Ky-ri-e",
    "kye": "Ky-ri-e",
    "kyre": "Ky-ri-e",
    "krie": "Ky-ri-e",
    "eles": "e-le-i-son",
    "eson": "e-le-i-son",
    "eleson": "e-le-i-son",
    "elelson": "e-le-i-son",
    "elej": "e-le-i-son",
    "elesomf": "e-le-i-son",
    "feleison": "e-le-i-son",
    "chri": "Chri-ste",
    "ste": "Chri-ste",
    "christele": "Chri-ste e-le-i-son",
    "elesonchriste": "e-le-i-son Chri-ste",
    "ila": "il-la",
    "degnus": "A-gnus De-i",
    "munna": "mun-di do-na",
    "doquiem": "do-na re-qui-em",
    "creatuta": "creatura",
    "dictutus": "dicturus",
    "ultioonis": "ultionis",
    "praessta": "praesta",
    "amas": "?",
    "ma": "?",
    "r": "?",
    "cis": "?",
    "fii": "?",
    "moren": "?",
    # Nuotinnusmerkintä luettu tavuksi. Kaivertajan nimi "A. Reutenauer"
    # osan V pianoviivastolla ja osan I kuoroäänten "PPP" olivat samaa
    # sarjaa; ne on poistettu 2026-09-10 (korjaa_kasin.py, OSAT_V ja
    # OSA_I_ALTTO/OSA_I_TENORI), joten niitä ei ole enää tässä.
    "p": "dynamiikkamerkintä, ei tavu",
    "pp": "dynamiikkamerkintä, ei tavu",
}


def normalisoi(sana):
    """Sanamuoto sanaston avaimeksi: pelkät kirjaimet, pienellä.

    Tavut kantavat pilkkuja, pisteitä ja huutomerkkejä ("irae," "omnes."
    "discussurus!"), ja sama sana esiintyy sekä isolla että pienellä
    alkukirjaimella riippuen siitä, aloittaako se rivin.
    """
    return re.sub(r"[^A-Za-zÀ-ÿ]", "", sana or "").lower()


def rivinumero(lyric):
    """Sanarivin numero. Lähteet kirjoittavat sen sekä muodossa "2" että
    "part5verse2"; yhdista.verse_number normalisoi ne, mutta tämä luetaan
    myös suoraan lähdetiedostoista, joten sama sietokyky tarvitaan tässä."""
    numerot = "".join(ch for ch in (lyric.get("number") or "1") if ch.isdigit())
    if not numerot:
        return 1
    return int(numerot[-1]) if "verse" in (lyric.get("number") or "") \
        else int(numerot)


def tavut(lyric):
    """Yhden <lyric>-alkion tavut järjestyksessä: [(syllabic, teksti)].

    Yleensä yksi tavu, mutta elisio on yksi <lyric>, jossa on kaksi
    syllabic/text-paria <elision>-alkion erottamana — "mor-te ae-ter-na"
    laulaa "te" ja "ae" samalla kahdeksasosalla (ks. yhdista.merge_elisions).
    Pelkän <extend/>-alkion sisältävä lyriikka on melisman jatkoviiva eikä
    tavu lainkaan, ja se jää tyhjänä listana pois.
    """
    parit = []
    syllabic = None
    for lapsi in lyric:
        if lapsi.tag == "syllabic":
            syllabic = lapsi.text
        elif lapsi.tag == "text":
            parit.append((syllabic or "single", lapsi.text or ""))
            syllabic = None
    return [(syl, teksti) for syl, teksti in parit if teksti.strip()]


# Kuinka monta tavua yritetään lukea yhdeksi sanaksi. Pisin sanastossa oleva
# sana on viisitavuinen ("o-ra-ti-o-nem", "ca-la-mi-ta-tis"), joten kuusi
# riittää varmuudella.
SANA_PISIN = 6


def tavuvirta(part, rivi=1):
    """Osaston yhden sanarivin tavut järjestyksessä.

    Palauttaa listan (teksti, syllabic, lyric, note, measure). Tahdit
    luetaan yhtenä jonona, koska sana ylittää tahtiviivan.
    """
    virta = []
    for measure in part.findall("measure"):
        for note in measure.findall("note"):
            for lyric in note.findall("lyric"):
                if rivinumero(lyric) != rivi:
                    continue
                for syllabic, teksti in tavut(lyric):
                    virta.append((teksti, syllabic, lyric, note, measure))
    return virta


def lippujen_mukaan(virta, i):
    """Sanan pituus `syllabic`-merkintöjen mukaan, tai None jos ketju on rikki.

    Ehjä ketju on `single` yksinään tai `begin` + `middle`×n + `end`. Mikä
    tahansa muu — `middle` ilman aloitusta, `begin` josta puuttuu `end` —
    tarkoittaa, ettei merkinnöistä saa sanan rajoja.
    """
    if virta[i][1] == "single":
        return 1
    if virta[i][1] != "begin":
        return None
    for j in range(i + 1, min(len(virta), i + SANA_PISIN)):
        if virta[j][1] == "end":
            return j - i + 1
        if virta[j][1] != "middle":
            return None
    return None


def jaa_sanoiksi(virta, sanasto=None):
    """Jaa tavuvirta sanoiksi. Palauttaa [(sana, tavut, sanastosta)].

    Tämä on tiedoston tärkein päätös, ja se tehtiin mittaamalla — kahdesti,
    koska ensimmäinen ratkaisu oli väärä kahdella eri tavalla.

    Aluksi sanat koottiin `syllabic`-merkinnöistä, kuten pitäisi voida
    tehdä. Lacrymosan tahdeissa 681-694 ne ovat sekaisin: "re" ja "qui" on
    merkitty `single`-tavuiksi ja niitä seuraava "em," `middle`:ksi. Lukija
    näki kolme sanaa yhden sijaan, ja koska `qui` on oikeaa latinaa,
    stemmaan tulostui suomennos "joka" keskelle sanaa requiem. Väärä
    suomennos on pahempi kuin puuttuva.

    Toinen versio jätti merkinnät kokonaan huomiotta ja luki sanat pelkästä
    sanastosta, pisin osuma ensin. Se kaatui testiin: konelukemisen
    "per-petl-la" alkaa sanalla `per`, joka on sanastossa ("kautta"), joten
    rikkinäisestä sanasta olisi tullut väärä suomennos aivan samalla
    tavalla.

    Merkinnät ovat siis todiste, eivät totuus:

    1. Jos merkinnät antavat ehjän sanan ja se on sanastossa, se on sana.
       Näin lukee suurin osa teoksesta, ja `dies`+`irae` pysyy kahtena
       sanana vaikka sanastossa olisi sana `diesirae`.
    2. Muuten merkinnät ovat epäluotettavat, ja sanastosta etsitään
       **pidempää** osumaa kuin merkinnät antavat. "re"(1) -> `requiem`(3)
       korjautuu, mutta "per-petl-la"(3) ei voi kutistua sanaksi `per`(1).
    3. Jos pidempää osumaa ei ole, sana saa **jakautua** — mutta vain jos
       jokainen sen tavu peittyy sanaston sanalla. Lacrymosan tahdissa 681
       "Do-na-e-is" on merkitty yhdeksi sanaksi, ja se jakautuu sanoiksi
       `dona` + `eis`. "per-petl-la" ei jakaudu, koska "petl" ei ole sana.
    4. Muuten jäljelle jää merkintöjen antama sana. Se ei ole sanastossa,
       joten se päätyy raporttiin — mikä on oikea lopputulos rikkinäiselle
       sanalle.
    """
    sanasto = SANASTO if sanasto is None else sanasto

    def sana(i, n):
        return normalisoi("".join(t[0] for t in virta[i:i + n]))

    def peitto(i, n):
        """Jaa tavut i..i+n sanaston sanoiksi niin että kaikki peittyvät.

        Palauttaa palojen pituudet tai None. Ehto on tarkoituksella tiukka:
        *jokaisen* tavun on kuuluttava johonkin sanaston sanaan. Pelkkä
        alkuosan osuma ei riitä, koska muuten konelukemisen "per-petl-la"
        jakautuisi sanaksi `per` ("kautta") ja kahdeksi roskatavuksi — juuri
        se väärä suomennos, jota vältetään.
        """
        if n == 0:
            return []
        for pituus in range(min(n, SANA_PISIN), 0, -1):
            if sana(i, pituus) not in sanasto:
                continue
            loppu = peitto(i + pituus, n - pituus)
            if loppu is not None:
                return [pituus] + loppu
        return None

    tulos = []
    i = 0
    while i < len(virta):
        lippujen = lippujen_mukaan(virta, i)
        if lippujen and sana(i, lippujen) in sanasto:
            n, sanastosta = lippujen, True
        else:
            pidempi = 0
            for ehdokas in range(min(SANA_PISIN, len(virta) - i),
                                 lippujen or 0, -1):
                if sana(i, ehdokas) in sanasto:
                    pidempi = ehdokas
                    break
            if pidempi:
                n, sanastosta = pidempi, True
            elif lippujen and (jako := peitto(i, lippujen)) and len(jako) > 1:
                # Ketju on liian pitkä: lähde merkitsi kaksi sanaa yhdeksi
                # ("Do-na-e-is" Lacrymosan tahdissa 681). Jaetaan, koska
                # jokainen tavu löytyy sanastosta.
                n, sanastosta = jako[0], True
            elif lippujen:
                n, sanastosta = lippujen, False
            else:
                # Ketju on rikki eikä sanastosta löydy mitään: yksi tavu.
                n, sanastosta = 1, sana(i, 1) in sanasto
        tulos.append(("".join(t[0] for t in virta[i:i + n]),
                      virta[i:i + n], sanastosta))
        i += n
    return tulos


def sanarivi(measure):
    """Sanarivin numero suomennokselle: yksi enemmän kuin tahdissa on käytössä.

    Melkein aina 2. Divisitahdissa, jossa kaksi ääntä laulaa eri tekstiä
    riveillä 1 ja 2, tulos on 3 — muuten suomennos kirjoittuisi alemman
    äänen tekstin päälle.

    **Luetaan tahtia kohti kerran, ennen kuin siihen lisätään mitään.** Jos
    tämä kutsutaan uudelleen sanan lisäämisen jälkeen, oma suomennos on
    laskennassa mukana ja seuraava sana valuu riviä alemmas: mitattuna
    Basso I sai rivejä yhdelletoista asti, MuseScore varasi tilan niille
    kaikille ja stemma paisui 16 sivusta 21:een.
    """
    kaytossa = {1}
    for note in measure.findall("note"):
        for lyric in note.findall("lyric"):
            kaytossa.add(rivinumero(lyric))
    return max(kaytossa) + 1


# --- Suomennoksen vaakatasaus --------------------------------------------
#
# MuseScore keskittää joka tavun nuotinpään kohdalle, myös suomennoksen.
# Suomen sana on melkein aina latinan tavua pidempi, joten keskitettynä se
# alkaa tavun vasemmalta puolelta ja ryömii edellisen sanan alle:
# "lu-ce-at"-tavun alla "loistakoon" alkoi 10,6 pistettä ennen tavua, ja
# lukija joutui arvaamaan kumman sanan käännös se on. Laulaja pyysi, että
# suomennos alkaa samasta kohdasta kuin ensimmäinen tavu. Siirto tehdään
# MusicXML:n <lyric relative-x>:llä.
#
# Kolme mitattua vakiota. Kaikki kolme luettiin renderöidyn PDF:n
# tekstikerroksesta (`mscore` + `mutool draw -F stext`), ei arvattu:
#
# - MuseScore ei tottele <lyric justify="left">:iä eikä <lyric default-x>:ää.
#   `relative-x` toimii, ja sen yksikkö on 0,2835 pt = 0,1 mm — ei
#   nuottiviivaväli, kuten MusicXML:n "tenths" antaisi olettaa. Mitattu
#   arvoilla 10 ja 20 sekä koesuoritteessa että valmiissa stemmassa.
# - Tavun renderöity koko on 10,02 pt ja suomennoksen 6,48 pt, vaikka
#   pyydetyt koot ovat 10 ja 6,5.
#
# Nämä pätevät `tiivistys.mss`:n nuottikoolla. Jos tyylitiedosto joskus
# muuttaa nuottiviivaväliä, luvut on mitattava uudelleen.
KOKO_ISO = 10.02
KOKO_PIENI = 6.48
KYMMENYS = 0.2835

# Edwin-kirjasimen merkkileveydet: merkki -> (etenemä, vasen sivulaakeri)
# pisteinä koossa KOKO_ISO. Mitattu kalibrointipartituurista, jossa joka
# riville tuli yksi merkkijono kahdesti — ylärivi latinan koossa, alarivi
# suomennoksen — jolloin rivien vasempien reunojen erotus antaa keskityksen
# ilman että kirjasintiedostoa tarvitsee lukea (MuseScore pitää Edwinin
# omien resurssiensa sisällä, eikä koneessa ole fontToolsia). Etenemä tulee
# jonosta "nXn" eikä "XX", koska "ff" on ligatuuri ja antaisi f:lle väärän
# leveyden. Merkki "$" puuttuu tarkoituksella: MuseScore korvaa sen
# nuottimerkillä eikä sitä voi mitata.
LEVEYDET = {
    'A': (7.133, -0.082), 'a': (5.265, -0.340), 'B': (7.133, +0.088),
    'b': (5.265, +0.000), 'C': (7.133, +0.003), 'c': (4.416, -0.085),
    'D': (7.642, +0.088), 'd': (5.604, -0.255), 'E': (7.133, +0.172),
    'e': (4.925, -0.000), 'F': (6.454, -0.082), 'f': (3.227, -0.679),
    'G': (7.642, -0.252), 'g': (5.265, -0.170), 'H': (8.322, +0.003),
    'h': (6.114, -0.000), 'I': (3.906, -0.085), 'i': (3.057, -0.085),
    'J': (5.265, -0.085), 'j': (2.547, +0.594), 'K': (7.642, -0.422),
    'k': (5.944, -0.085), 'L': (6.454, -0.167), 'l': (3.057, -0.000),
    'M': (9.341, +0.003), 'm': (8.831, +0.003), 'N': (8.152, +0.003),
    'n': (6.114, -0.085), 'O': (7.642, -0.082), 'o': (4.925, -0.000),
    'P': (6.454, -0.082), 'p': (5.435, -0.085), 'Q': (7.642, -0.252),
    'q': (5.265, -0.340), 'R': (7.133, -0.252), 'r': (4.416, -0.085),
    'S': (6.114, -0.170), 's': (4.585, -0.085), 'T': (6.114, -0.337),
    't': (3.736, -0.170), 'U': (7.642, -0.252), 'u': (6.114, -0.000),
    'V': (7.133, -0.082), 'v': (4.925, -0.255), 'W': (9.680, -0.082),
    'w': (7.133, -0.337), 'X': (6.793, -0.167), 'x': (5.265, -0.085),
    'Y': (6.793, -0.167), 'y': (4.755, -0.255), 'Z': (6.114, -0.000),
    'z': (4.755, +0.000), 'Ä': (7.133, -0.082), 'ä': (5.265, -0.340),
    'Å': (7.133, -0.082), 'å': (5.265, -0.340), 'æ': (7.812, -0.167),
    'è': (4.925, -0.000), 'é': (4.925, -0.000), 'Ö': (7.642, -0.082),
    'ö': (4.925, -0.000), 'ü': (6.114, -0.000), 'œ': (8.322, +0.003),
    'ﬁ': (6.114, -0.000), 'ﬂ': (6.114, -0.000), ' ': (2.717, +0.000),
    '!': (2.887, -0.085), '"': (3.736, -0.085), '#': (5.265, -0.170),
    '%': (8.322, -0.082), '&': (8.152, -0.082), "'": (1.868, -0.085),
    '(': (3.227, +0.000), ')': (3.227, -0.170), '*': (4.925, -0.000),
    '+': (5.944, -0.085), ',': (2.717, -0.085), '-': (3.227, -0.085),
    '.': (2.717, -0.085), '/': (2.717, -0.085), '0': (5.265, -0.170),
    '1': (5.265, -0.340), '2': (5.265, -0.085), '3': (5.265, -0.170),
    '4': (5.265, -0.170), '5': (5.265, -0.085), '6': (5.265, -0.255),
    '7': (5.265, -0.170), '8': (5.265, -0.085), '9': (5.265, -0.085),
    ':': (2.717, -0.170), ';': (2.717, -0.170), '<': (5.944, -0.085),
    '=': (5.944, -0.085), '>': (5.944, -0.085), '?': (4.416, +0.000),
    '@': (7.303, -0.082), '[': (3.227, -0.170), '\\': (5.944, -0.085),
    ']': (3.227, +0.000), '^': (5.944, -0.085), '_': (4.925, -0.085),
    '`': (3.227, +0.340), '{': (3.227, -0.170), '|': (5.944, -0.170),
    '}': (3.227, +0.000), '~': (5.944, -0.085), '¢': (5.265, -0.085),
    '–': (5.604, +0.085), '—': (10.020, -0.000), '‘': (1.868, -0.170),
    '’': (1.698, -0.170), '“': (3.736, -0.085), '”': (3.736, -0.085),
}


def keskitys(teksti, koko=KOKO_ISO):
    """Etäisyys nuotinpään keskeltä tekstin vasempaan reunaan, pisteinä.

    MuseScore keskittää tavun ohittaen alku- ja loppuvälimerkit: "nam,"
    asettuu kuin "nam", ja ",nam" kuin "nam" jonka eteen on työnnetty
    pilkku. Mitattu; ilman tätä sääntöä pilkkuun päättyvä tavu menisi 1,4
    pistettä vinoon.

    Palauttaa None, jos jokin merkki puuttuu taulukosta. Silloin tasaus
    jätetään tekemättä — keskitetty suomennos on väärässä paikassa, mutta
    arvattu leveys olisi väärässä paikassa arvaamattomasti.
    """
    if not teksti or any(m not in LEVEYDET for m in teksti):
        return None
    alku, loppu = 0, len(teksti)
    while alku < loppu and not teksti[alku].isalpha():
        alku += 1
    while loppu > alku and not teksti[loppu - 1].isalpha():
        loppu -= 1
    if alku == loppu:          # pelkkää välimerkkiä
        alku, loppu = 0, len(teksti)
    etu = sum(LEVEYDET[m][0] for m in teksti[:alku])
    ydin = sum(LEVEYDET[m][0] for m in teksti[alku:loppu])
    return (koko / KOKO_ISO) * (etu + ydin / 2 - LEVEYDET[teksti[0]][1])


def tavun_teksti(lyric):
    """Se teksti, jonka MuseScore keskittää: <lyric>-alkion koko sisältö.

    Elisiossa alkiossa on kaksi tavua ja MuseScore piirtää niiden väliin
    oman yhdysmerkkinsä, jonka leveyttä ei ole mitattu. Silloin palautetaan
    None ja suomennos jää keskitetyksi. Koko partituurissa elisioita on
    viisi, joten mittaaminen olisi työtä ilman näkyvää tulosta.
    """
    tekstit = lyric.findall("text")
    return tekstit[0].text if len(tekstit) == 1 else None


def tasaus(tavu, suomi):
    """<lyric relative-x> kymmenyksinä, tai None jos leveyttä ei tiedetä."""
    a = keskitys(suomi, KOKO_PIENI)
    b = keskitys(tavu, KOKO_ISO)
    if a is None or b is None:
        return None
    return (a - b) / KYMMENYS


def uusi_lyric(numero, suomennos, koko=KOKO, siirto=None):
    lyric = ET.Element("lyric", {"number": str(numero), "placement": "below"})
    if siirto is not None:
        lyric.set("relative-x", f"{siirto:.2f}")
    ET.SubElement(lyric, "syllabic").text = "single"
    text = ET.SubElement(lyric, "text")
    text.set("font-size", koko)
    text.text = suomennos
    return lyric


# <note>:n lapsilla on pakollinen järjestys, ja <lyric> tulee <notations>:n
# jälkeen mutta <play>/<listen>:n edelle (ks. yhdista.NOTE_ORDER). Loppuun
# lisääminen on siis oikein paitsi jos nuotilla on jompikumpi niistä.
LYRICIN_JALKEEN = ("play", "listen")


def kiinnita(note, lyric):
    for i, lapsi in enumerate(list(note)):
        if lapsi.tag in LYRICIN_JALKEEN:
            note.insert(i, lyric)
            return
    note.append(lyric)


def tavutus(montako):
    """Sanan tavujen oikeat `syllabic`-arvot, kun tavuja on `montako`."""
    if montako == 1:
        return ["single"]
    return ["begin"] + ["middle"] * (montako - 2) + ["end"]


def korjaa_tavutus(root, sanasto=None):
    """Korjaa `syllabic`-merkinnät sanastosta luetun sanajaon mukaisiksi.

    Tämä ei ole suomennosta varten vaan sen takia, että väärä `syllabic`
    näkyy laulajalle: Lacrymosan tahdit 688-689 tulostuivat muodossa
    "re qui em," ilman väliviivoja, koska tavut oli merkitty erillisiksi
    sanoiksi. Vika on stemmassa ilman suomennostakin.

    Korjataan vain sanat, jotka sanasto tunnistaa — silloin tiedetään, että
    tavut kuuluvat yhteen. Tuntemattoman sanan merkintöihin ei kosketa,
    koska mitään parempaa tietoa ei ole.

    Sanaa ei jaeta eikä yhdistetä uudelleen: vain ketjumerkinnät muuttuvat.
    "re"+"qui"+"em," pysyy kolmena tavuna kolmella nuotilla, mutta niistä
    tulee begin+middle+end, ja MuseScore piirtää väliviivat itse.
    """
    muutettu = collections.Counter()
    for part in root.findall("part"):
        for sana, palat, sanastosta in jaa_sanoiksi(tavuvirta(part), sanasto):
            if not sanastosta:
                continue
            for (_teksti, vanha, lyric, _note, measure), uusi in zip(
                    palat, tavutus(len(palat))):
                if vanha == uusi:
                    continue
                elem = lyric.find("syllabic")
                if elem is None:
                    elem = ET.Element("syllabic")
                    lyric.insert(0, elem)
                elem.text = uusi
                muutettu[normalisoi(sana)] += 1
    return muutettu


Tulos = collections.namedtuple(
    "Tulos", "lisatty sanoja puuttuvat rikki kokoamatta tasaamatta")


def lisaa(root, sanasto=SANASTO, koko=KOKO):
    """Lisää suomennokset partituurin joka osastoon.

    Palauttaa Tuloksen, jonka `puuttuvat` on se osa raportista, joka vaatii
    ihmisen: sanamuoto jota ei ole sanastossa eikä RIKKI-listassa.
    """
    lisatty = 0
    sanoja = 0
    tasaamatta = 0
    puuttuvat = collections.Counter()
    rikki = collections.Counter()
    kokoamatta = collections.Counter()
    for part in root.findall("part"):
        rivit = {}
        for sana, palat, sanastosta in jaa_sanoiksi(tavuvirta(part), sanasto):
            sanoja += 1
            muoto = normalisoi(sana)
            if not muoto:
                continue
            if not sanastosta:
                kokoamatta[muoto] += 1
                (rikki if muoto in RIKKI else puuttuvat)[muoto] += 1
                continue
            suomi = sanasto[muoto]
            note, measure = palat[0][3], palat[0][4]
            if id(measure) not in rivit:
                rivit[id(measure)] = sanarivi(measure)
            numero = rivit[id(measure)]
            # Kaksi sanaa voi alkaa samalta nuotilta (elisio). Sama rivi
            # kahdesti yhdellä nuotilla piirtyisi vain kertaalleen, joten
            # jälkimmäinen menee riviä alemmas.
            varatut = {rivinumero(lyric) for lyric in note.findall("lyric")}
            while numero in varatut:
                numero += 1
            siirto = tasaus(tavun_teksti(palat[0][2]), suomi)
            tasaamatta += siirto is None
            kiinnita(note, uusi_lyric(numero, suomi, koko, siirto))
            lisatty += 1
    return Tulos(lisatty, sanoja, puuttuvat, rikki, kokoamatta, tasaamatta)


def raportti(tulos):
    """Rivit, jotka yhdista.py tulostaa ajon lopussa."""
    rivit = [f"suomennettu {tulos.lisatty}/{tulos.sanoja} sanaa "
             f"({100 * tulos.lisatty // max(1, tulos.sanoja)} %)"]
    if tulos.tasaamatta:
        rivit.append(f"  {tulos.tasaamatta} suomennosta jäi keskitetyksi "
                     f"(elisio tai merkki, jota ei ole LEVEYDET-taulukossa)")
    if tulos.rikki:
        rivit.append(f"  {sum(tulos.rikki.values())} sanaa jäi ilman "
                     f"suomennosta rikkinäisen tavutuksen takia "
                     f"({len(tulos.rikki)} eri muotoa, ks. suomennos.RIKKI)")
    for muoto, kerrat in tulos.puuttuvat.most_common():
        rivit.append(f"  VAROITUS: {muoto!r} ei ole sanastossa ({kerrat}x)")
    return rivit


# Tuntematon sana merkitään näillä, jotta se erottuu juoksevasta tekstistä
# silmäillen. Käytetään kaarisulkeita, koska nuottien tavut kantavat itse
# pilkkuja ja pisteitä.
EPAILYTTAVA = "\u00ab%s\u00bb"


def painettuna(palat):
    """Sana niin kuin se painuu: tavut väliviivoin, kuten `syllabic` sanoo.

    Tämä on tavutusvirheiden tarkistuksen koko pointti. Jos ketju on rikki,
    tavut tulostuvat erillisinä sanoina ("re qui em") juuri niin kuin ne
    näkyvät stemmassa — eikä virhettä tarvitse etsiä XML:stä.
    """
    osat = []
    for i, (teksti, syllabic, _ly, _note, _m) in enumerate(palat):
        osat.append(teksti)
        if i < len(palat) - 1:
            osat.append("-" if syllabic in ("begin", "middle") else " ")
    return "".join(osat)


def teksti_riveina(part, leveys=78, sanasto=None):
    """Osaston teksti juoksevana proosana, suomennos latinan alla.

    Tarkoitus on lukea koko teksti kerralla läpi: väärä suomennos ja
    rikkinäinen tavutus näkyvät proosassa heti, kun taas nuottikuvasta ne
    pitää etsiä sivu kerrallaan.
    """
    rivit = []
    la, fi, alku = "", "", None
    for sana, palat, sanastosta in jaa_sanoiksi(tavuvirta(part), sanasto):
        if alku is None:
            alku = palat[0][4].get("number")
        muoto = painettuna(palat)
        if not sanastosta:
            muoto = EPAILYTTAVA % muoto
        suomi = (SANASTO if sanasto is None else sanasto).get(normalisoi(sana), "")
        pituus = max(len(muoto), len(suomi)) + 1
        if len(la) + pituus > leveys:
            rivit.append((alku, la.rstrip(), fi.rstrip()))
            la, fi, alku = "", "", palat[0][4].get("number")
        la += muoto.ljust(pituus)
        fi += suomi.ljust(pituus)
    if la.strip():
        rivit.append((alku, la.rstrip(), fi.rstrip()))
    return rivit


def tulosta_teksti(root, leveys=78):
    for part in root.findall("part"):
        nimi = part.get("id")
        print(f"=== {nimi}")
        for tahti, la, fi in teksti_riveina(part, leveys):
            print(f"t.{tahti:>4}  {la}")
            if fi.strip():
                print(f"        {fi}")
            print()


def load(path):
    with zipfile.ZipFile(polut.polku(path)) as z:
        nimet = [n for n in z.namelist()
                 if n.endswith(".xml") and "META-INF" not in n]
        for nimi in nimet:
            data = z.read(nimi)
            if b"score-partwise" in data[:4000]:
                return ET.fromstring(data)
    raise SystemExit(f"{path}: ei löytynyt score-partwise-tiedostoa")


def main(argv):
    teksti = "--teksti" in argv
    if teksti:
        argv = [a for a in argv if a != "--teksti"]
    root = load(argv[0] if argv else "Verdi-Requiem-koko.mxl")
    if teksti:
        tulosta_teksti(root)
        return
    tulos = lisaa(root)
    for rivi in raportti(tulos):
        print(rivi)
    if tulos.rikki:
        print("\nsanat, joita ei saatu kokoon (suomennos.RIKKI):")
        for muoto, kerrat in tulos.rikki.most_common():
            print(f"  {muoto:14s} {kerrat:4d}  pitäisi olla {RIKKI[muoto]}")


if __name__ == "__main__":
    main(sys.argv[1:])
