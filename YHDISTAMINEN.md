# Verdin Requiemin yhdistäminen yhdeksi partituuriksi

## Tiedostot

Nuottiaineisto on neljässä hakemistossa, jotka vastaavat datan kulkusuuntaa:
`lahteet/` → `johdetut/` → `stemmat/`. Skriptit ja niiden taulukot puhuvat
paljaista tiedostonimistä; `polut.py` selvittää hakemiston nimestä, joten
komennot toimivat sekä nimellä että täydellä polulla.

| Hakemisto | Sisältö |
|---|---|
| `lahteet/` | Alkuperäiset CPDL-tiedostot, lähde-PDF:t ja Audiveris-projektit. Näitä ei muokata |
| `johdetut/` | Skriptien tuottamat korjatut osat ja yhdistetty partituuri |
| `stemmat/` | Kahdeksan stemmaa ja sisällysluettelo |
| `harjoitus/` | Harjoittelutiedostot, eivät versionhallinnassa |

| Tiedosto | Sisältö |
|---|---|
| `Verdi-Requiem-koko.mxl` | Koko teos, 15 viivastoa, 1807 tahtia |
| `stemma-*.mxl` / `stemma-*.pdf` | Kahdeksan kuorostemmaa, kaikki ajan tasalla (II·9b mukana, tahtinumerointi juoksee Dies iraen läpi, osan nimi joka sivun ylälaidassa, latinan sanojen suomennos tavujen alla) |
| `stemmat-sisallys.txt` | Osien alkusivut kaikissa kahdeksassa, ajan tasalla |
| `sisallys.py` | Rakentaa tuon luettelon uudelleen valmiista stemma-PDF:istä |
| `tiivistys.mss` | Tyylitiedosto: taukotahtien tiivistys, tahtinumero joka tahtiin, väljyys rivien välissä |
| `harjoitus-*.mscz` | Harjoittelutiedosto: oma ääni trumpettina, muut piilossa |
| `yhdista.py` | Yhdistämisskripti, kartoitustaulukko tiedoston alussa |
| `sivuotsikot.py` | Kirjoittaa käynnissä olevan osan nimen joka sivun ensimmäisen tahdin päälle |
| `harjoitus.py` | Rakentaa harjoittelutiedoston yhdelle laulajalle |
| `korjaa_sanat.py` | Korjaa osien 01, 14 ja II·9b:n kuorosanat lähde-PDF:ää vasten |
| `korjaa_kasin.py` | Käsin todennetut korjaukset (osat I, II·1, II·4, II·6, II·10, IV ja VII), taulukkona — tavut, korkeudet, rytmi, sanarivit, tavutus, sävellajin paikka |
| `suomennos.py` | Latinan sanojen suomennos tavujen alle, tavutuksen korjaus, ja `--teksti` tulostaa koko tekstin juoksevana proosana |
| `nayta.py` | Näyttää viivaston nuotit, äänet ja sanarivit tahdeittain |
| `fix-mxl.py` | Korjaa Audiveris-viennistä puuttuvat tahdit |
| `polut.py` | Kertoo mistä hakemistosta mikäkin nuottitiedosto löytyy |
| `Verdi_10bDies_irae.pdf` | II·9b:n lähde-PDF (käyttäjän löytämä) |
| `10b-Verdi_Dies_irae_paluu-OMR*.mxl` | II·9b, konelukemisen tulos ja sanakorjattu versio |
| `*-kasin.mxl` | **Skriptin tuottamia**, ei käsin muokattuja: `korjaa_kasin.py`:n tulos, ja juuri nämä `yhdista.py` lukee osista I, II·1, II·4, II·6, II·10, IV ja VII |

## Työnkulku

Harjoitteluun avaa **`harjoitus-basso-1.mscz`** MuseScoressa. Siinä on kaikki
valmiina: oma rivi on ainoa näkyvä ja soi **trumpettina**, muut kuoroäänet
soivat vaimeana kuorona, solistit oboena ja piano pianona. Piilotetut
viivastot soivat edelleen, joten kuulet koko teoksen vaikka luet vain omaa
riviäsi. Taukotahdit ovat tiivistetyt, joten omat pitkät tauot eivät vie
sivuja.

Toiselle äänelle:

    python3 harjoitus.py --stemma "Altto II"    # -> harjoitus-altto-2.mscz

Vaihtoehdot ovat samat kahdeksan kuin stemmoissa. Kuoro II:n laulajalla
näkyviä viivastoja on kaksi, koska kaksoiskuoro esiintyy vain Sanctuksessa.

Soittimet ovat `harjoitus.py`:n alussa `SOUND`-taulukossa, jos haluat vaihtaa
ne. Tunnisteet ovat MuseScoren omia, esimerkiksi `brass.trumpet.c`,
`voice.vocals`, `wind.reed.oboe`, `keyboard.piano`.

> **Viivaston nimi ja soitin ovat eri asia.** Viivastolla lukee edelleen
> "Kuoro B" vaikka se soi trumpettina.

Jos haluat mieluummin rakentaa asettelun itse, avaa
**`Verdi-Requiem-koko.mxl`** ja piilota viivastot käsin.

Lukulaitteelle mene oma **`stemma-*.pdf`**. Kahdeksan stemmaa kattavat koko
kuoron: `sopraano-1`, `sopraano-2`, `altto-1`, `altto-2`, `tenori-1`,
`tenori-2`, `basso-1`, `basso-2`. Numero tarkoittaa kuoroa I tai II, ja sillä
on merkitystä vain Sanctuksessa — muissa 15 osassa I- ja II-stemmat ovat
identtiset.

Kun olet kerran asetellut partituurin mieleiseksesi MuseScoressa (piilotetut
viivastot, fonttikoot, sivuasettelu), **tallenna se .mscz-muotoon** ja jatka
siitä. MusicXML ei säilytä noita asetuksia.

> Tee tahtinumerointipäätös ennen kuin panostat .mscz-asetteluun. Skriptin
> uudelleenajo tuottaa uuden .mxl-tiedoston, eikä se tuo mukanaan .mscz:ään
> tekemiäsi asetteluja.

## Uudelleenluonti

Jos lähdeaineisto muuttuu, aja koko ketju **tässä järjestyksessä** —
`yhdista.py` lukee `korjaa_sanat.py`:n tuottamia tiedostoja, ja
`harjoitus.py` lukee yhdistettyä partituuria:

    python3 korjaa_sanat.py                       # 1. sanat PDF:stä
    python3 korjaa_kasin.py                       # 2. todennetut korjaukset
    python3 yhdista.py Verdi-Requiem-koko.mxl     # 3. partituuri
    python3 yhdista.py stemma-basso-1.mxl --stemma "Basso I"   # 4. stemmat
    python3 sivuotsikot.py stemma-basso-1.mxl     # 5. sivujen osaotsikot
    python3 paivays.py stemma-basso-1.mxl         # 6. päiväys ensimmäiselle sivulle
    "/Applications/MuseScore 4.app/Contents/MacOS/mscore" \
        -S tiivistys.mss -o stemma-basso-1.pdf stemma-basso-1.mxl
    python3 harjoitus.py --stemma "Basso I"       # 7. harjoittelutiedosto
    python3 sisallys.py                           # 8. sisällysluettelo
    python3 suomennos.py --teksti stemma-basso-1.mxl   # 9. lue teksti läpi

Vaihe 6 on viimeinen ennen PDF:ää: se merkitsee stemmaan päivän, jona sen
sisältö viimeksi muuttui, ja lataa sen pienellä ensimmäisen sivun vasempaan
ylälaitaan. Päivä ei ole rakennuspäivä vaan verrataan gitissä olevaan
versioon, joten muuttumaton stemma pitää vanhan päivänsä. Sivusto lukee
saman merkinnän `.mxl`-tiedostosta latauslinkin alle.

Vaihe 9 on tarkistus eikä tuota mitään: se tulostaa stemman tekstin
juoksevana proosana, ja väärä suomennos tai rikkinäinen tavutus näkyy siinä
heti. Ks. *Latinan sanojen suomennos*.

Vaiheet 4-7 toistetaan kullekin tarvittavalle äänelle; `sivuotsikot.py` ja
`paivays.py` ottavat monta tiedostoa kerralla (`python3 sivuotsikot.py
stemma-*.mxl`). Yksittäiset
komennot ovat alla.

    # koko partituuri, 15 viivastoa
    python3 yhdista.py Verdi-Requiem-koko.mxl

    # yksi kuorostemma (vaihtoehdot: Sopraano I/II, Altto I/II, Tenori I/II, Basso I/II)
    python3 yhdista.py stemma-basso-1.mxl --stemma "Basso I"

    # PDF lukulaitteelle
    "/Applications/MuseScore 4.app/Contents/MacOS/mscore" \
        -S tiivistys.mss -o stemma-basso-1.pdf stemma-basso-1.mxl

    # yksi mielivaltainen viivasto partituurista, esim. solisti tai piano
    python3 yhdista.py solisti-tenori.mxl --vain "Solisti T"

`tiivistys.mss` on tyylitiedosto, joka kytkee **taukotahtien tiivistämisen**
päälle: peräkkäiset tyhjät tahdit yhdistyvät yhdeksi taukopalkiksi, jossa lukee
tahtien määrä. Esimerkiksi Quid sum miser, jossa kuorobasso vaikenee kokonaan,
kutistuu yhdeksi 52 tahdin palkiksi. Vaikutus on 26 sivusta 19:ään. Osien
otsikot ja kaksoistahtiviivat katkaisevat tiivistyksen, joten osanvaihdot ja
tahtinumeroinnin nollaukset säilyvät.

Sama tiedosto kytkee myös **tahtinumeron jokaiseen tahtiin** viivaston
yläpuolelle, ei vain rivin ensimmäiseen, ja tiivistetyn taukopalkin alle sen
tahtivälin (`[79-93]`). Harjoituksissa etsitään yksittäistä tahtia, ja rivin
alusta laskeminen on hidasta ja menee helposti yhden pieleen. Hinta on yksi
sivu lisää kussakin kahdeksassa stemmassa (B I 13 -> 14 sivua; alla oleva
rivinvälin väljennys nosti sen edelleen 16:een).

Kolmas asetus on **rivinväli**: `minSystemSpread` 11,5 antaa nuottirivien
väliksi 29,3 mm oletuksen 25,1 mm sijaan, eli noin puoli senttiä lisää tilaa
käsimerkinnöille. Arvo on portaittainen — se ratkaisee montako riviä sivulle
mahtuu (9 oletuksen 10 sijaan) ja loppu jaetaan tasan, joten väliarvot eivät
tuota väliarvoja. Seuraava porras on 13,0 eli 33,7 mm ja 8 riviä sivulle.
Hinta 11,5:stä on 1-2 sivua stemmaa kohti; B I on nyt 16 sivua.

Sama tyyli käyttöliittymässä: Format -> Style -> Load Style -> `tiivistys.mss`.
Jätä tyyli pois koko partituurin PDF:stä; tiivistys on tarkoitettu yhden
stemman lukemiseen, ei partituuriin.

## Osan nimi joka sivulla

`sivuotsikot.py` kirjoittaa **käynnissä olevan osan nimen** joka sivun
ensimmäisen tahdin päälle kursiivilla, tahtinumeroiden tasalle:

    13   VII  Libera me    154        155 ...

Iso lihava osaotsikko kertoo vain siitä sivulta, josta osa alkaa; keskeltä
osaa avatulta sivulta ei aiemmin nähnyt onko kyse Lacrymosasta vai Libera
mestä. Jos osa alkaa juuri sivun ensimmäisestä tahdista, otsikkoa ei toisteta
— iso otsikko on jo paikallaan.

Ajetaan `yhdista.py`:n jälkeen ja ennen PDF:n tekoa. Tiedostoa muokataan
paikallaan ja uudelleenajo on turvallista.

**Miksi tämä on erillinen komento eikä tyyliasetus.** Sivunvaihdot eivät ole
tiedostossa vaan MuseScore laskee ne, joten "sivun ensimmäinen tahti" ei ole
tiedettävissä ennen taittoa. Skripti kysyy taiton MuseScorelta (`mscore -o
x.musicxml` kirjoittaa lasketun sivujaon), kirjoittaa otsikot ja kysyy taiton
uudelleen; jos otsikot siirsivät sivunvaihtoja, kierros toistetaan. Kahdessa
sopraanostemmasta kahdeksasta niin todella kävi, ja toinen kierros riitti.
Sivumäärä ei kasvanut yhdessäkään stemmassa — otsikko mahtuu tahtinumerorivin
tasalle.

`--stemma` rakentaa laulajan stemman: kaksoiskuoro esiintyy vain Sanctuksessa,
joten esimerkiksi `Sopraano II` lukee tavallista sopraanoriviä kaikissa muissa
osissa ja II-kuoron riviä Sanctuksessa. Stemmatiedostoissa viivaston nimi on
piilotettu (`print-object="no"`), koska yhden rivin tiedostossa se on pelkkää
tilanhukkaa; nimi on otsikossa.

`--vain` ottaa pilkulla erotellun listan viivastonimiä, esimerkiksi
`--vain "Kuoro B,Piano"` jos haluat bassostemman pianosäestyksen kanssa.

Sisällysluettelon sivunumerot poimitaan valmiista PDF:istä, joten aja
`python3 sisallys.py` aina kun stemmat on renderöity uudelleen — se kirjoittaa
`stemmat-sisallys.txt`:n uudestaan.

## Latinan sanojen suomennos

`suomennos.py` kirjoittaa **jokaisen latinan sanan alle sen suomennoksen**
pienemmällä fontilla (6,5 pt latinan 10 pt:n alla). Tarkoitus on latinan
opiskelu laulamisen ohessa, eli sama idea kuin `sivusto/requiem.html`:n
rinnakkaisessa suomennoksessa — mutta siinä kohdassa nuottia, jossa sana
lauletaan:

    ex  -  au  -  di        o - ra - ti - o - nem
    kuule                   rukous

Suomen sana ei tavutu eikä sitä tavuteta: koko sana tulee latinan sanan
**ensimmäisen tavun alle**, myös silloin kun latinan sana venyy melisman yli
usean tahdin matkalle. `yhdista.py` tekee tämän viimeisenä vaiheena, ja
lipulla `--ei-suomennosta` se jää pois.

Käännökset ovat samat kuin tekstisivulla, ja ne on poimittu siitä: sanasto on
sanamuoto → suomennos, eli sama muoto käännetään koko teoksessa samoin. Se on
tietoinen valinta. Apusanat joutuvat siksi kompromissiin — `in` on aina
"-ssa", vaikka "in favilla" on "tuhkaan" — mutta taulukko pysyy yhtenä
listana eikä paisu tahtikohtaisiksi poikkeuksiksi. Sanasto kattaa koko
teoksen, myös solistien tekstit, joita mikään kahdeksasta stemmasta ei laula.

**Sivumäärä ei kasvanut basson stemmoissa lainkaan** ja koko kahdeksan
stemman joukossa kaksi sivua: suomennosrivi mahtuu pääosin tilaan, joka on jo
varattu. Mitattu, ei arvattu — samoin kuin se, että fonttikoko on pakko
kirjoittaa tavun omaan `<text font-size>`-määreeseen: MuseScoren tyyliavain
`lyricsEvenFontSize` ei tee mitään.

### Tekstin lukeminen läpi juoksevana proosana

    python3 suomennos.py --teksti stemma-basso-1.mxl

tulostaa stemman koko tekstin virkkeinä, suomennos latinan alla ja tavuviivat
niin kuin ne painuvat:

    t. 688  re-qui-em, re-qui-em, do-na e-is   re-qui-em. A-men.
            lepo       lepo       anna  heille lepo       amen

Tämä on tarkistus, jota nuottikuvasta ei voi tehdä. Kun koko teksti on
luettavissa kerralla, väärä suomennos ja rikkinäinen tavutus näkyvät heti;
nuottikuvasta ne pitää etsiä sivu kerrallaan. Tuntemattomat sanat tulostuvat
kaarisulkeissa (`«per-pe-tll-a»`), ja ne ovat käytännössä aina konelukemisen
virheitä. Ilman `--teksti`-lippua sama komento antaa pelkän
kattavuusraportin.

Bassostemmoissa kattavuus on 100 % — jokainen sana tunnistetaan ja saa
suomennoksen. Sopraanossa, altossa ja tenorissa se on 95–96 %, ja koko
puuttuva osa on osan I konelukemisen roskaa (`lg},`, `ux`, `per-pe-tll-a`),
eli samaa vikaa jonka `LUOTETTAVUUS.md` jo kertoo.

### Tavutuksen korjaus

Sama sanasto korjaa myös **tavuviivat**, ja se on stemman virhe suomennoksesta
riippumatta. Lacrymosan tahdissa 688 sana "requiem" oli kirjoitettu kolmeksi
erilliseksi tavuksi, joten stemmassa luki `re qui em,` ilman väliviivoja. Kun
sanasto tunnistaa, että kolme tavua ovat yksi sana, ketjumerkinnät
(`syllabic`) korjataan sen mukaisiksi. Tuntemattoman sanan merkintöihin ei
kosketa, koska mitään parempaa tietoa ei ole.

Tämä löysi kolme oikeaa vikaa, jotka olivat painetussa stemmassa:

- **Lacrymosan tahdit 681–698**: tavuviivat rikki, koska sanojen vaihdon
  yhteydessä 2026-09-03 jokainen tavu peri korvatun sanan ketjumerkinnän.
  Korjattu `korjaa_kasin.py`:n uudella `tavutus`-rivillä, joka kertoo koko
  lauseen tavutuksen kerralla ja tarkistaa jokaisen tavun tekstin.
- **Libera me, tahti 85**: `cal-la-mi-ta-tis`, oikein `ca-la-mi-ta-tis`.
- **Sanctus, tahti 71, Kuoro II:n basso**: `in no-mi-ni`, oikein
  `in no-mi-ne`.

Ja neljäs, joka maksoi kolmelle stemmalle sivun jo ennen suomennosta: Dies
iraen tahdissa 5 sopraanon, alton ja tenorin ylä-äänen tavu oli merkitty
sanariville **6**, joten rivit 3–5 olivat tyhjiä mutta veivät silti tilan.
`yhdista.py` tiivistää nyt tahdin käytössä olevat sanarivit järjestyksessä
1..n.

## Viivastot

Solisti S / M-S / T / B, Kuoro S / A / T / **B** / S II / A II / T II / B II,
D-trumpetti, Trombone, Piano (2 viivastoa).

Kuoro B on se rivi jota luetaan. Kuoro S II – B II esiintyvät vain Sanctuksessa
(kaksoiskuoro) ja vasket vain Tuba mirumissa, jossa ei ole pianoa lainkaan.

## Jos kuulet stemmassa väärän tavun

Kerro tahtinumero ja mitä siinä pitäisi lukea — numerot ovat nyt jokaisen
tahdin päällä, joten niitä ei tarvitse laskea rivin alusta. Korjaus tehdään
näin:

    python3 nayta.py stemma-basso-1.mxl 126 130

näyttää mitä datassa oikeasti on (myös sanarivin numeron, jota ei näe
nuottikuvasta), ja korjaus kirjataan `korjaa_kasin.py`:n taulukkoon riviksi,
ei suoraan tiedostoon. Sen jälkeen `python3 korjaa_kasin.py` ja normaali
uudelleenluonti. Jokainen korjaus tarkistaa lähtötilanteen ja kaatuu, jos
lähde on muuttunut, joten korjaus ei voi hiljaa osua väärään tahtiin.

Tarkempi menetelmä — miten kohta todennetaan lähde-PDF:stä ennen kirjaamista
ja mistä tietää onko vika datassa vai skriptissä — on skillissä
`.claude/skills/korvakuulokorjaus/SKILL.md`.

Jos kokonainen kohta puuttuu eikä kyse ole vain tavusta, sama taulukko osaa
kopioida valmiin tahdin toisaalta samasta stemmasta (`kopioi_tahti`) — niin
korjattiin Liber scriptuksen puuttuneet "Di-es i-rae." -välihuudahdukset
tahdeissa 229, 231 ja 233.

Taulukko osaa myös **vaihtaa nuotin korkeuden** (`korkeus`), jos kuulet
väärän sävelen eikä väärän tavun — niin korjattiin Dies iraen tahti 28 ja
Libera men tahti 72, joissa sanan viimeinen tavu on oktaavia alempana kuin
tiedostossa luki. Jos vika on **rytmissä**, siihen on `kesto` (nuottiarvo,
esim. `"256/quarter"` -> `"192/eighth."`, piste per pisteellisyys) sekä
`lisaa_aksentti` ja `poista_aksentti`. Niillä korjattiin Libera men tahti 88.

Rytmiä muutettaessa taulukko tarkistaa itse, että tahdin pituus säilyy:
kestojen summa lasketaan ennen ja jälkeen, ja ajo kaatuu jos se muuttui. Siksi
rytmirivit tulevat aina pareittain tai ryhminä — yksi rivi yksinään ei voi olla
kelvollinen korjaus.

Osan 14 (Agnus Dei) korjaukset on aikanaan tehty suoraan lähdetiedostoon,
joten sillä ei vielä ole vastaavaa taulukkoa. Muut korjatut osat on purettu
taulukoksi: osa I ja osa 11 (Lacrymosa) 2026-09-02/03, ja osat 02 (Dies
irae), 07 (Rex tremendae), 13 (Sanctus) ja 16 (Libera me) 2026-09-04. Niiden
lähteet ovat jälleen koskemattomia CPDL-vientejä.

## Tarkistettavaa harjoituksissa

Kolme kohtaa on jätetty tietoisesti auki: ne ratkeavat kuoron nuottikirjasta
tai kapellimestarilta, eivät tiedostoja tutkimalla. Jokainen on yhden rivin
muutos `korjaa_kasin.py`:ssä.

| Kohta | Mitä stemmassa nyt lukee | Mitä pitää tarkistaa |
|---|---|---|
| I, t. 51-52 | `om – – nis`, eli melisma tavulla "om" ja "nis" tahdin 52 viimeisellä nuotilla — pyyntösi mukaan | Lähde-PDF merkitsee toisin päin: "nis" tahdin 51 kolmannelle iskulle ja melisma sen jälkeen. Kumpaa kuoro laulaa? |
| II·10, t. 653 | "De-us." viimeinen nuotti on **C**, pyyntösi mukaan | Lähde-PDF painaa tähän kuorobassolle **G:n palautusmerkillä**. C:n puolesta ovat sinun korvasi, kuoron oma tiedosto, saman tiedoston bassosolisti (laulaa jakson unisonossa ja päättyy C:hen) ja pianon vasen käsi (C2+C3). Jos kirja sanoo G, yksi rivi kääntää sen takaisin. |
| II·4, t. 247-254 | Altto, tenori ja basso laulavat "Solvet saeclum in favilla" kahdesti | Sopraanolla on samassa kohdassa sen sijaan ylimääräiset "Dies irae, dies illa" -toistot. Nuotit on tarkistettu oikeiksi kaikilla äänillä; kyse on vain siitä, kumpi teksti on oikea. |

Neljäs, pienempi: **Sanctuksessa kirjoitusasu on "coe-li" eikä "cae-li"**.
Lähdetiedosto käyttää coe-asua kaikkialla (myös t. 27), joten pysyttiin
siinä; jos kirja kirjoittaa cae, se on kahden rivin muutos joka ääni.

Puuttunut "coe" on korjattu altolle, tenorille ja bassolle (sopraano oli jo
oikein), ja Libera men tahdin 98 puuttunut "di-es" bassolle ja tenorille.
Sopraano ja altto olivat siinä jo oikein.

Neljäs kohta on kokonaisen alaosan numerointi, ja siihen auttaisi eniten yksi
tieto kirjasta. Lacrymosassa paljastui 2026-09-03, että kirjan osio-otsikon
tahtinumero ei kertonut mistä tahdista **tiedosto** alkaa — ero oli kolme
tahtia, ja koko osan numerointi oli sen verran pielessä. Sama voi koskea
Tuba mirumia, Liber scriptusta, Rex tremendaeta, Quid sum miseriä ja
Recordarea, joiden saumoista `yhdista.py` raportoi päällekkäisiä numeroita.

Sen ratkaisee **tahtinumero alaosan sisältä**, ei sen otsikosta: esimerkiksi
mistä tahdista kuorobasso aloittaa Rex tremendaessa, tai minkä tahdin
kohdalla jokin selvä sana on. Yksi numero alaosaa kohti riittää.

## Tahtinumerointi

Numerointi alkaa joka pääosassa (I, III, IV, V, VI, VII) ykkösestä. Poikkeus
on osa II, Dies irae: sen kymmenen alaosaa ja II·9b juoksevat yhtenäisesti
1:stä 701:een, koska kuoron nuottikirja numeroi Dies iraen niin. MuseScore
kunnioittaa MusicXML:n tahtinumeroita, joten osiorajoja ei tarvita kummassakaan
tapauksessa.

Toteutus on `yhdista.py`:n `DIES_IRAE_ALUT`-taulukko ja kytkin

    NUMEROINTI_ALKAA_JOKA_OSASSA_YKKOSESTA = False

Taulukossa on **kunkin alaosan lähdetiedoston ensimmäisen tahdin numero**
kuoron nuottikirjan numeroinnissa, kirjasta luettuna (2026-09-02), ei
laskettuna:

    II·1 Dies irae 1, II·2 Tuba mirum 91, II·3 Mors stupebit 143,
    II·4 Liber scriptus 162, II·5 Quid sum miser 271, II·6 Rex tremendae 322,
    II·7 Recordare 386, II·8 Ingemisco 450, II·9 Confutatis 507,
    II·9b Dies irae (kertaus) 573, II·10 Lacrymosa 624

**Lacrymosan 624 ei ole kirjan osio-otsikon tahti.** Kirjassa Lacrymosa-otsikko
on tahdissa 621, mutta CPDL:n Lacrymosa-tiedosto alkaa kolme tahtia sen
jälkeen: kirjan tahdit 621–623 ovat 10b-tiedoston kolme viimeistä tahtia.
Taulukkoon kuuluu tiedoston ensimmäisen tahdin numero, siis 624. Tämä oli
kertaalleen väärin, ja se näkyi siten että koko Lacrymosan numerointi oli
kolme tahtia liian pieni. Nyt kuorobasso aloittaa tahdista 645 ja "A-men"-sanan
"men" on tahdissa 698, kuten kirjassa.

Käytännön seuraus: stemmassa **II·10-otsikko on tahdissa 624**, vaikka kirjassa
se on 621. Tahtinumerot täsmäävät kirjaan, otsikon paikka poikkeaa kolme
tahtia. Se ei haittaa laulaessa, koska kuoro on tahdeissa 621–623 taukona ja
ne katoavat II·9b:n taukopalkkiin.

Aiemmin nämä laskettiin lähdetiedostojen omista tahtimääristä, ja kuusi
yhdestätoista oli väärin — Lacrymosassa jo kahdeksan tahtia. CPDL:n
osakohtaiset tiedostot eivät katkea samoista kohdista kuin kirja, joten
numerointi ei jatku saumojen yli aukottomasti: viidessä saumassa muutama
numero toistuu ja kolmessa muutama puuttuu lähteistä. `yhdista.py` tulostaa
nämä joka ajolla. Lacrymosan sauma oli aiemmin näiden joukossa ja on nyt
jatkuva (623 → 624); on hyvin mahdollista että loput neljä päällekkäisyyttä
ovat samaa vikaa, mutta se ratkeaa vain tahtinumerolla alaosan **sisältä**
— osio-otsikon numero ei riitä. Lukustemmoissa se ei näy, koska kaikki toistuvat tahdit
ovat kuorolle taukoa ja katoavat taukopalkkeihin. Ks. `docs/tyopaivakirja/2026-09-02-dies-iraen-tahtinumerot.md`.

Huom: jos vanhoissa muistiinpanoissa on Dies iraen tahtinumeroita ennen
2026-09-02, ne ovat vanhassa numeroinnissa — Lacrymosasta vähennetään 8,
II·9b:stä 5, Rex tremendaesta 2, Tuba mirumista ja Liber scriptuksesta 1,
ja Mors stupebitiin lisätään 2. Lacrymosan osalta on lisäksi 2026-09-02 ja
2026-09-03 välillä kirjattuja numeroita, jotka ovat kolme liian pieniä:
niihin **lisätään 3**.

## Oletukset jotka voi joutua korjaamaan

| Kohta | Oletus | Muutos |
|---|---|---|
| Sanctuksen kuorobasso | Basso I | `MAPPING`-taulukossa vaihda `"Kuoro B": ["P4"]` -> `["P8"]` |
| Osan 05 solisti | Mezzo (tiedostossa "Soprano solo", mutta Liber scriptus on mezzon aaria) | `"Solisti M-S"` -> `"Solisti S"` |
| Osien 12 ja 15 nimeämättömät solistit | Järjestys partituurin tavan mukaan | vaihda osastojen `P`-tunnukset |

Basso I ja Basso II erottuvat sisääntulosta: Basso I aloittaa tahdissa 2,
Basso II tahdissa 4, molemmat sävelellä C3 sanalla "San-ctus".

## Osien pituudet

| Numero | Osa | Tahteja |
|---|---|---:|
| I | Requiem & Kyrie | 140 |
| II | Dies irae (10 alaosaa + II·9b) | 706 |
| III | Offertorio | 222 |
| IV | Sanctus | 139 |
| V | Agnus Dei | 74 |
| VI | Lux aeterna | 105 |
| VII | Libera me | 421 |
| | **Yhteensä** | **1807** |

Sarakkeessa on tahtien määrä. Dies iraen numerointi juoksee 1:stä 701:een
eikä 706:aan, koska alaosien saumoissa muutama numero toistuu ja muutama
puuttuu — ks. **Tahtinumerointi** yllä.

Kuorobasso vaikenee kokonaan osissa II·3 Mors stupebit, II·5 Quid sum miser,
II·7 Recordare, II·8 Ingemisco, II·9 Confutatis, III Offertorio ja VI Lux
aeterna — ne ovat soolonumeroita. Se ei ole virhe.

**II·9b "Dies irae (kertaus)"** on uusi, 51 tahdin osa Confutatiksen ja
Lacrymosan välissä. Se puuttui aiemmin kokonaan — Verdin "Dies irae"
-teema palaa täällä toisen kerran (kolmesta), eikä sillä ole omaa nimeä
missään tavallisessa osaluettelossa, joten se ei ollut minkään
lähdetiedostomme mukana. Löytyi erillisestä PDF:stä ja luettiin koneellisesti
samalla tavalla kuin osat I ja V. Kuorobasson sanat on tarkistettu; nuotit
ja muut äänet eivät vielä ole. Ks. `docs/menetelmat/omr.md`, luvut **Fixing OMR
lyrics** ja **The missing Dies irae recall (II·9b)**, tekniselle taustalle.

## Tunnetut rajoitukset

**Osat I ja V ovat konelukemisen tulosta** (Audiveris PDF:stä), joten niiden
nuotit ja sanat eivät ole yhtä luotettavia kuin muiden. Muut 14 osaa tulevat
julkaisukuntoisista lähteistä.

Sanat on nyt korjattu koneellisesti lähde-PDF:ää vasten, ks. **Sanojen
korjaus** alla. Nuotteja se ei koske: ne pitää edelleen oikaisulukea.

**Poikkeus: osan V (Agnus Dei) kuorobasso on nyt oikaisuluettu kokonaan.**
Koko rivi tahdista 1 tahtiin 74 on verrattu kuoron omaan MuseScore-tiedostoon
(`musescore/06_agnus_dei`), ja se täsmää nyt **nuotti nuotilta, ilman yhtään
eroa** — lisäksi jokainen 74 tahdista on nyt tahtilajin mukaan täysimittainen.
Korjattuja kohtia oli 15: neljä tahtia oli kokonaan tyhjä (t. 59, 60, 69 ja
72 — näistä 72 on teoksen loppusointu, joten osa loppui aiemmin kesken
sanaan "do"), kuudessa tahdissa oli väärä kesto, kahdesta puuttui korukuvio
ja kahdesta tavu. Nyt stemma päättyy oikein sanoihin "do – na.".

Muita ääniä (Sopraano/Altto/Tenori) samasta osasta **ei ole tarkistettu** — ne
ovat yhä konelukemisen tuloksena, ja niiltä puuttuu mm. sama loppusointu
tahdista 72. Tekninen tausta:
`docs/tyopaivakirja/2026-08-31-agnus-dei-kuorobasso.md`.

**Poikkeus edelliseen: Lacrymosan (11) kuorobassolla oli aito virhe, ei
OMR:stä johtuva.** Rivin loppupuolella (n. 30 tahtia) oli väärää tekstiä —
osan oma aiempi sanoitus oli kopioitunut väärään kohtaan alkuperäisen
tiedoston teossa. Löytyi 2026-08-28 vertaamalla toiseen, käyttäjän löytämään
Lacrymosa-PDF:ään.

**Lacrymosan kuorobasso on nyt tarkistettu kokonaan** (2026-09-03), koska
pyysit sitä: nuotit kuoron omaa MuseScore-tiedostoa vasten kaikki 48
laulettua tahtia, ja sanat lähde-PDF:ää vasten sivu sivulta niin, että
jokaisen tavun paikka tarkistettiin nuotti nuotilta PDF:n
x-koordinaateista. Nuottieroja oli kaksi ja molemmat ratkesivat lähde-PDF:n
hyväksi (tahdissa 653 on G3, tahdissa 689 puolinuotti), eli tiedosto oli
oikeassa ja kuoron oma tiedosto poikkeaa.

Kaksi aitoa virhettä löytyi ja korjattiin:

- **Divisin ylä-ääni tahdeissa 677–679** lauloi "La-cry-mo-sa di-es il-" kun
  oikea teksti on "Pi-e Je-su Do-mi-ne,". Lähde-PDF painaa sen ylä-äänen
  sanat viivaston yläpuolelle, mistä ne oli aiemmin luettu tenorin riviksi.
- **Tahdit 657–665**, sinun raporttisi mukaan: kuorobasso laulaa
  "hu-ic er-go par-ce De-us" kolme kertaa, ei "La-cry-mo-sa … di-es il-la".
  Tässä **lähde-PDF itse on väärässä** — se painaa "La-cry-mo-sa," — joten
  sivuja vasten vertaaminen ei olisi ikinä löytänyt tätä. Varmistus tuli
  nuoteista: kohta on limittäinen tulo samalle kuviolle, ja tenorilla,
  altolla ja sopraanolla sen sanat ovat "hu-ic er-go". Basson oma jatko
  tahdeissa 664–665 oli jo "er-go par-ce De-us,", eli korjauksen jälkeen
  kaikki neljä ääntä ovat samassa tekstissä.

Tekninen tausta:
`docs/tyopaivakirja/2026-08-28-lacrymosan-kuorobasso.md` ja
`docs/tyopaivakirja/2026-09-03-lacrymosan-kolmen-tahdin-siirtyma.md`.

Muiden äänten (Sopraano/Altto/Tenori, solistit) samaa tiedostoa ei ole
tarkistettu yhtä tarkasti — sama virhetyyppi voisi periaatteessa olla
muuallakin näissä 14 "luotettavassa" osassa.

**MuseScore ilmoitti aiemmin tiedoston korruptoituneeksi.** Se on korjattu.
Syy oli lähteissä 05 ja 16: niiden pianostemmassa on nuotteja, joissa on
kaksinkertainen nuottiarvo puolella kestolla (`<time-modification>` 2:1).
Koodaus on laillista ja kestot ovat oikein, mutta MuseScore laskee tahdin
täyttymisen nuottityypeistä eikä huomioi kerrointa.

`yhdista.py` korjaa tämän yhdistämisen yhteydessä: noin 1770 pianonuotin
tyyppi kirjoitetaan vastaamaan todellista kestoa. Soiva tulos ei muutu, ja
nuottimäärät tarkistettiin rivi riviltä ennen ja jälkeen. Kuoro- ja
solistiriveihin ei kosketa lainkaan.

Nyt sekä partituuri että kaikki kahdeksan stemmaa kääntyvät **ilman `-f`-lippua**.

**Osassa I ei ole pianosäestystä.** Sen pianostemma tuli konelukemisesta, ja
siinä on tahteja, joihin MuseScoren moottori kaatuu: tiedosto avautui ilman
varoitusta mutta soitto pysähtyi tahtiin 81 kuin seinään. Neljä eri
paikkausyritystä rikkoi tiedoston muualta, joten pianorivi jätettiin osasta I
pois ja sen tilalla on taukoja. Lauluäänet soivat normaalisti. Palautus
onnistuu siivoamalla `01-Verdi_Requiem.omr` Audiveriksessa ja lisäämällä
kartoitukseen takaisin `"Piano": ["P17"]`.

Soivuuden voi tarkistaa MIDI-viennillä: `mscore -o x.mid Verdi-Requiem-koko.mxl`.
Nyt se ulottuu 1699 tahtiin; aiemmin 81:een.

## Sävellajin vaihto väärässä tahdissa

Osan I bassostemmassa oli **palautusmerkki tahdissa 59**, jossa basso on
tauolla. Merkki ei ole turha — se purkaa yhden b:n sävellajin, ja purku
piirretään aina, lauloipa tahdissa kukaan tai ei — mutta se oli **kolme tahtia
liian myöhässä**: lähdesivu purkaa sävellajin tahdissa 56.

Syy on konelukemisessa. Jokainen painettu järjestelmä toistaa sävellajin
vasemmassa reunassaan, ja Audiveris lukee sen sieltä joka kerta. Osan I sivun 3
järjestelmät alkavat tahdeista 50, 59 ja 66, ja jos vaihto tapahtuu kesken
järjestelmän eikä konelukema huomaa sitä, se kirjautuu vasta seuraavan
järjestelmän alkuun. Tiedostossa se ei näytä miltään: tahdin 59 merkintä on
aivan tavallinen ja kaikki sen jälkeen on oikein. Vain tahdit 56–58 ovat
väärässä sävellajissa.

Paikka mitattiin PDF:n omasta tekstikerroksesta. Näissä lähteissä myös
**nuottikuva on fonttia**, joten `mutool draw -F stext` antaa jokaiselle
avaimelle, etumerkille ja tauolle tarkan koordinaatin; sivulla 3 on kuusi
palautusmerkkiä samalla x:llä 368, yksi kutakin kuutta viivastoa kohti, ja
tahti 56 alkaa x:llä 367. Mitään ei tarvinnut katsoa kuvasta. Sama mittaus
vahvisti, että sivun 3 toinen vaihto (kolme ristiä, tahti 67) ja sivun 1
vaihto (tahti 17) ovat tiedostossa jo oikein.

Korjaus on `korjaa_kasin.py`:n `SAVELLAJIT`-taulukossa eikä `korjaukset`-
rivinä, koska sävellaji on merkitty **jokaiseen osastoon erikseen**: jos se
siirtyisi vain kuorobassossa, partituurin viivastot vaihtaisivat sävellajia eri
tahdeissa. Siirto myös tarkistaa jokaisesta osastosta, että vanha tahti
todella kantaa sen sävellajin ja uusi ei kanna mitään.

Stemmassa näkyvä muutos: palautusmerkki on nyt tahdissa 56, siinä kohdassa
missä "4 Soli" -jakso alkaa, ja tahdit 58–59 tiivistyvät yhdeksi
`[58–59]`-taukoruuduksi, koska niiden välissä ei enää ole sävellajin vaihtoa.

**Sama vika on korjaamatta sopraanolla ja altolla.** Osan I sivulla 2
sävellaji vaihtuu yhteen b:hen tahdissa 28, ja niin tiedostossa on tenorilla ja
bassolla — mutta muilla viisitoista osastolla vaihto on tahdissa 35, seuraavan
järjestelmän alussa. Tätä ei voi korjata siirtämällä sävellajia, koska
konelukema on lukenut *nuotit* uskomassaan sävellajissa: kuorosopraanon "Te
decet hymnus" on tahdeissa 28–34 `Fis4 Fis4 Cis5 D5 E5` ja alton
`Fis4 Gis4 A4 Gis4 Fis4 E4 A4`, kun tenori ja basso laulavat puhdasta
F-duuria. Ristit ovat seurausta, ja korjaus vaatii nuottien lukemisen sivulta
uudelleen. Merkitty `LUOTETTAVUUS.md`:hen.

## Sanarivien yhtenäistäminen

Lähteet numeroivat sanarivit eri tavoin: osa käyttää muotoa `1`, osa muotoa
`part5verse1`. Sekamuoto samassa osastossa sekoittaa MuseScoren rivilaskennan,
joten `normalise_lyrics` muuttaa kaikki pelkiksi numeroiksi.

Lisäksi Dies iraessa ja Libera messä oli yksittäinen tavu ("la," sanasta
"Sy-bil-la") merkittynä **säkeistölle 6**, vaikka samalla nuotilla ei ollut
tekstiä rivillä 1 lainkaan. MuseScore varaa silloin tilan kaikille kuudelle
sanariville, mikä työntää sanat kauas viivastosta ja väljentää koko osan.
Sääntö on siksi: jos tahdissa ei ole yhtään tavua rivillä 1, siirretään
kaikki sen tavut riville 1. Aidot moniriviset kohdat säilyvät, koska niissä
rivi 1 on käytössä — esimerkiksi Rex tremendaen tahdit 46-48, joissa divisi
laulaa kahta tekstiä yhtä aikaa.

Vaikutus kuorobasson PDF:ään oli 18 sivusta 14:ään.

**Kaksi tavua samalla nuotilla.** Peräkkäisten sanojen tavut voivat osua
samalle nuotille — Libera men tahdissa 274 "mor-te ae-ter-na" laulaa "te" ja
"ae" samalla kahdeksasosalla. Lähde kirjoittaa ne kahdeksi tavuksi, joilla on
**sama** sanarivin numero, ja MuseScore piirtää silloin vain toisen: stemmassa
luki "mor - te" ja "ae" katosi kokonaan. `merge_elisions` yhdistää ne yhdeksi
tavuksi, jonka osat erottaa `<elision>`, ja tulos on "mor - te ae-". Sama
tarkistus poistaa lähteen kahdennuksen (osan 16 tahti 416 laulaa "me," kaksi
kertaa samalla nuotilla).

Elisiomerkki on **rikkumaton välilyönti**, ei tavallinen välilyönti eikä
sidekaari: MuseScore 4.7.4 pudottaa tavallisen välilyönnin tuonnissa, jolloin
tavut painuvat yhteen muotoon "teae", ja sidekaari käy samoin.

## Kartoituksen erikoistapaukset

**Osa I** (Audiveris pilkkoi solistiviivastot): Solisti S = P7+P3+P1,
M-S = P8+P4+P2, T = P10+P5+P12, B = P11+P6. Kuoro = P13–P16. P9 on tyhjä.
Nimetyt osastot ("Sop.", "Mex.", "83.") ovat solisteja, koska Audiveris luki
partituurin nimilaput; nimeämättömät "Voice"-osastot ovat kuoro.

**Osa V**: P5 ja P6 ovat tahdeissa 1–13 sopraano- ja mezzosoolo (a cappella
-alku) ja tahdista 14 alkaen pianon kaksi viivastoa. Kartoitus jakaa ne tahtien
mukaan.

**Osa II·10 Lacrymosa**: P9 on kuorobasson divisi tahdeissa 54–56 (juoksevat
677–679), ja se yhdistetään kuorobassoriville omaksi äänekseen. Stemmassa
siinä on siksi kaksi sanariviä: **ylemmällä** ylä-äänen "Pi-e Je-su
Do-mi-ne," ja **alemmalla** ala-äänen "Pi-e Je-su". Niin lähde-PDF:kin sen
painaa — ylä-äänen sanat viivaston yläpuolelle.

Lähdetiedosto on tässä toisin päin, ja se on tarkoituksella korjattu
`korjaa_kasin.py`:ssä (`sanarivi`-toimenpide): P8 ja P9 ovat lähteessä kaksi
erillistä osastoa, jotka kumpikin numeroivat omat tavunsa toisesta tietämättä,
joten ala-ääni päätyi riville 1 ja ylä-ääni riville 2. Yhdellä viivastolla
rivijärjestys kertoo kummasta äänestä on kyse, ja väärin päin se johtaa
laulajan harhaan — niin kävikin, ja siitä tämä korjaus alkoi.

## Sanojen korjaus

Osien 01 ja 14 sanoissa oli konelukemisen virheitä kuten `Is-ru-sa-lem`,
`Te dc-cet` ja `V0-tum`, ja paikoin esitysmerkintä oli luettu sanaksi
(`sotto voce` → `SOITO` / `VOCE`, `PPP`, `morendo`). Molempien lähde-PDF:ien
sanat ovat kuitenkin **oikeaa tekstiä eivät kuvaa**, joten oikea sanoitus
saadaan luettua suoraan lähteestä.

    python3 korjaa_sanat.py            # korjaa ja kirjoita
    python3 korjaa_sanat.py --kuiva    # näytä raportti, älä kirjoita mitään

Tulos menee tiedostoihin `01-Verdi_Requiem-OMR-korjattu.mxl` ja
`14-Verdi_requiem_agnus-dei-OMR-korjattu.mxl`. Osalla 14 on 2026-09-10
lähtien myös oma `korjaa_kasin.py`-taulukko, joka kirjoittaa
`14-Verdi_requiem_agnus-dei-kasin.mxl`:n, ja `yhdista.py` lukee sitä.
Konelukemisen alkuperäisiin tiedostoihin ei kosketa.

> **Varoitus: älä aja `korjaa_sanat.py`:tä ajattelematta.** Se lukee
> konelukemisen *alkuperäiset* tiedostot ja kirjoittaa `-OMR-korjattu.mxl`:t
> kokonaan uudelleen. Kaikki käsin tehdyt korjaukset — osan V kuorobasson
> taukojaksot ja sen 15 nuotti- ja kestokorjausta — ovat vain näissä
> `-korjattu`-tiedostoissa, joten pelkkä uudelleenajo **pyyhkii ne pois**, ja
> huomaat sen vasta kun vanhat virheet ilmestyvät takaisin stemmaan. Jos
> sanojen korjaus on ajettava uudelleen, vertaa tulosta committoituun
> tiedostoon ja tee käsin tehdyt korjaukset uudelleen — tai palauta tiedosto
> gitistä jälkikäteen.

### Mitä se korjasi

| Osasto | Tavuja | Kohdistettu | Korjattu | Lisätty | Ehdotuksia | Yhä ilman sanaa |
|---|---:|---:|---:|---:|---:|---:|
| I Kuoro S | 141 | 84 % | 26 | 15 | 1 | 57 |
| I Kuoro A | 115 | 83 % | 23 | 22 | 3 | 49 |
| I Kuoro T | 128 | 83 % | 26 | 14 | 1 | 48 |
| **I Kuoro B** | **131** | **91 %** | **17** | **22** | **0** | **23** |
| V Kuoro S | 37 | 81 % | 11 | 13 | 2 | 53 |
| V Kuoro A | 28 | 25 % | 9 | 23 | 1 | 50 |
| V Kuoro T | 79 | 65 % | 15 | 31 | 5 | 72 |
| V Kuoro B | 68 | 37 % | 15 | 32 | 0 | 71 |

"Korjattu" on olemassa olevan sanan muuttaminen, "lisätty" sanan
antaminen nuotille jolla ei ollut sanaa lainkaan. Viimeinen sarake on
nuottien määrä joilla ei vieläkään ole sanaa — osa niistä on melismoja
joilla ei kuulukaan olla.

Kuorobasson rivi osasta I lukee korjauksen jälkeen tahtiin 90 asti
virheetöntä latinaa:

    Re-qui-em, re-qui-em ae-ter-nam, et lux per-pe-tu-a et lux
    per-pe-tu-a lu-ce-at e-is. Te de-cet hym-nus, De-us in Si-on et
    ti-bi red-de-tur vo-tum in Je-ru-sa-lem; ex-au-di o-ra-ti-o-nem
    me-am, o-ra-ti-o-nem me-am, ad te om-nis ca-ro ve-ni-et.
    Re-qui-em, re-qui-em ae-ter-nam, et lux per-pe-tu-a et lux
    per-pe-tu-a lu-ce-at e-is.

Konelukemisen jäljiltä siinä luki `Is-ru-sa-lem`, `Te dc-cet`,
`V0-tum`, `ra-ti-nem` — ja tahdit 50–56 olivat kokonaan ilman sanoja.
Kyriessä (tahdista 91) on vielä puutteita, useimmiten puuttuva `i`
sanassa `e-le-i-son`.

### Ehdotukset: 13 kohtaa joita ei sovellettu

Yhteensä kirjoitettiin 314 muutosta: 142 olemassa olevan sanan korjausta ja
172 tavua nuoteille joilla ei ollut sanaa.

Raportti erottaa muutokset ehdotuksista. **Ehdotuksia ei kirjoiteta
tiedostoon.** Ne ovat kohtia joissa myös vanha teksti oli PDF:n tuntema sana,
eli sanan vaihtuminen toiseksi sanaksi — se voi olla aito korjaus tai
kohdistuksen liukumista. Käsin tarkistettuna kolme viidestä oli väärin,
esimerkiksi sopraanon tahti 134, jossa `Chri` → `e` olisi tehnyt sanasta
`Chri-ste` muodon `e-ste`. Siksi ne vain raportoidaan.

Kuorobassossa ei ole yhtään ehdotusta, eli sen 14 muutosta ovat kaikki
sellaisia joissa vanha teksti oli roskaa.

### Mitä jäi korjaamatta

Kaksi asiaa, ja kumpaakaan ei voi korjata tekstiä muuttamalla.

**Pudonneet tavut.** Konelukeminen on paikoin lukenut viisi tavua kuuden
sijaan, esimerkiksi `ra-ti-nem` kun oikein on `o-ra-ti-o-nem`. Silloin
paikkoja on tavuja vähemmän eikä kohdistus voi olla yksi yhteen. Raportti
listaa nämä kohdat rivillä `kohdistamatta tahdit N-M:`.

**Nuotit joilla ei ole sanaa lainkaan.** Nämä lisätään nyt PDF:n
x-sijainnin perusteella, ks. alla. Kuorobassossa niitä oli 44 ja on enää
23, joista osa on melismoja joilla ei kuulukaan olla sanaa.

Loput jäävät niihin systeemeihin joissa sovitus ei ole yksikäsitteinen —
rivillä on enemmän tavuja kuin systeemissä nuotteja, mikä tarkoittaa että
konelukeminen on pudottanut myös nuotteja. Ne on lisättävä käsin.

### Miten se toimii

1. `mutool draw -F stext` poimii PDF:n tekstin sijainteineen. Sanat
   erottuvat viivastomerkinnöistä (`4 Soli`, `Tutti`) fonttikoolla, joka
   päätellään aineistosta: se on tekstifontin yleisin koko.
2. Merkit ryhmitellään peruslinjan y-koordinaatilla, jolloin yksi rivi on
   yhden äänen sanat yhdessä systeemissä. Väli päätellään edellisen merkin
   **oikeasta reunasta**, koska osan 14 MusiXTeX asemoi joka kirjaimen
   erikseen ja leveä kirjain näyttäisi muuten väliltä.
3. Rivi pilkotaan tavuiksi: sanaraja on välilyönti ja tavuraja viiva, ja
   viivan asema kertoo `syllabic`-arvon (single/begin/middle/end).
   Tavutus päätetään enemmistöllä: osan V ladonta asemoi viivan paikoin
   väärän kirjaimen jälkeen, jolloin `peccata` poimitaan neljällä
   rivillä kymmenestä muodossa `pecc-a-ta` ja kuudella oikein
   `pec-ca-ta`. Vain kokonaiset sanat äänestävät.
4. Sanarivi luetaan MusicXML:stä **säkeistö kerrallaan** eikä nuotti
   kerrallaan. Konelukeminen pani `sotto voce` -merkinnän säkeistölle 2
   oikeiden tavujen alle, ja nuotti kerrallaan luettuna se katkaisi jonon.
5. Jokaiselle riville etsitään mahdolliset kohdat ja niistä valitaan
   dynaamisella ohjelmoinnilla suurin yhteensopiva joukko: rivit
   järjestyksessä, kohdat päällekkäin menemättä. Väärä kohta häviää
   oikealle, koska oikeat kohdat tukevat toisiaan.
6. Poisto tehdään vain osumien välissä ja vain tavulle jota PDF ei tunne.
7. Nuoteille joilla ei ole sanaa lainkaan sana haetaan **x-sijainnin**
   perusteella. Audiveris säilytti nuottien `default-x`:n, tahtien
   leveydet ja systeemien marginaalit, joten nuotin paikka rivillä on
   laskettavissa, ja PDF:stä saadaan tavun paikka. Koordinaatistot ovat
   lineaarisessa suhteessa; mittakaava (0,306) otetaan mediaanina
   kaikista systeemeistä ja siirtymä systeemikohtaisesti niistä
   tavuista jotka jo osuivat. Sitten tavu menee sille nuotille jonka
   yllä se on. **Melisma ratkeaa itsestään**: nuotti jonka yllä ei ole
   tavua jää ilman sanaa.

### Miksi ratkaisu on tällainen

Ahne kohdistus kokeiltiin ensin ja se hylättiin: se liukui toistuvassa
tekstissä väärään kohtaan ja poisti Kyriestä oikeat tavut `Ky`, `ri`, `e`,
ja se juuttui — yksi roskatavu kursorin kohdalla pysäytti loppuosan, ja
tenorista kohdistui 8 paikkaa 128:sta.

Kolme muuta yritystä hylättiin mittausten perusteella:

| Yritys | Tulos |
|---|---|
| Kiinteä osuusraja 85 % | Hylkäsi lyhyet rivit: viiden tavun rivissä yksikin kirjainvirhe pudottaa osuuden 80 prosenttiin |
| Ikkuna 4 paikkaa tavumäärää pidempi | Rivin loppuun osuva korvaus nieli seuraavan rivin paikat; tahdin 20 oikea `pe` poistui |
| Lyhyiden aukkojen täyttö osumien välistä | Ei laukea kertaakaan: aukot ovat aina eri rivien välissä, eivät saman rivin sisällä |
| Mittakaava sovitettuna systeemin omista ankkureista | Kolmesta lähekkäisestä pisteestä ekstrapolointi systeemin toiseen päähän heittää tavun verran; `ad` jäi pois |
| Tavun siirto viereiselle vapaalle nuotille kun oma on varattu | Tuotti kaksoiskappaleita: `ti-bi bi red-de-tur`, `o-ra-ra{1-o-nem` |
| Täyttö ilman järjestystarkistusta | Kyriestä tuli `e-le-le-son` ja `Chri-i-e-i-ste` |

## Harjoittelutiedoston rakentaminen

    python3 harjoitus.py --stemma "Basso I"

Skripti tekee kolme asiaa:

1. Muuntaa `Verdi-Requiem-koko.mxl`:n MuseScoren muotoon tyylillä
   `tiivistys.mss`, jolloin **taukotahtien tiivistys** on päällä.
2. Asettaa jokaiselle viivastolle soittimen: oma ääni trumpetti, muut
   kuoroäänet choir aahs, solistit oboe, piano ja vasket piano.
3. Piilottaa kaikki viivastot paitsi oman.

Ajossa menee noin 15 sekuntia, josta lähes kaikki on MuseScoren muunnos.

### Soittimen vaihtaminen

Soittimet ovat `harjoitus.py`:n alussa:

    SOUND = {
        "oma":     ("brass.trumpet.c", 56),   # se rivi jota luetaan
        "kuoro":   ("voice.vocals", 52),      # choir aahs
        "solisti": ("wind.reed.oboe", 68),
        "piano":   ("keyboard.piano", 0),
    }

Ensimmäinen arvo on MuseScoren soitintunniste ja toinen ohjelmanumero.
Numero on **nollapohjainen** kuten MuseScoressa, ei yksipohjainen kuten
MusicXML:ssä — trumpetti on siis 56 eikä 57.

Tunnisteita saa MuseScoren omista pohjatiedostoista, joita on 63:

    grep -rho "<instrumentId>[^<]*" \
        "/Applications/MuseScore 4.app/Contents/Resources/templates" | sort -u

Se on kuitenkin vain osa MuseScoren listasta. Jos etsimäsi ei ole siellä,
anna MuseScoren kertoa se itse: kirjoita soittimen nimi johonkin
MusicXML-tiedostoon ja katso mitä tuonti tuotti. Juuri niin löytyi
`brass.trumpet.c`, jota pohjissa ei ole — ja se on **C-trumpetti**, joka
ei transponoi, toisin kuin pohjien `brass.trumpet.bflat`.

Muutoksen jälkeen aja skripti uudelleen; se ylikirjoittaa `.mscz`:n.

### Miksi vasket soivat pianona

Tuba mirumissa on oikea D-trumpettistemma. Jos se soisi trumpettina, se
sekoittuisi luettavaan riviin juuri siinä osassa jossa kuoro laulaa sen
kanssa, joten vasket saavat pianon.

### Tarkistus

Tulos tarkistettiin kolmella mittauksella:

| Mitä | Tulos |
|---|---|
| Näkyvyys | 15 viivastosta 14 piilotettu, Kuoro B näkyvissä |
| Soivuus | MIDI patchatusta ja patchaamattomasta tiedostosta **nuotilleen identtinen** |
| Soittimet | Kuoro B `c-trumpet` / Trumpet 56, kuoro `voice` / Choir Aahs 52, solistit `oboe` / Oboe 68, muut `piano` |

> Soitin vaatii kolme merkintää: `<instrumentId>`-elementin,
> `<Instrument id>`-attribuutin ja `audiosettings.json`:n raidan. Jos yksi
> puuttuu, viivasto soi flyygelinä. Ensimmäisessä versiossa niin kävikin,
> koska MIDI-vienti näytti soittimet oikein mutta käyttöliittymän soitto
> tulee eri polkua.

Pianoraidoissa on noin 1,8 % vähemmän nuotteja kuin suoraan `.mxl`:stä
viedyssä MIDIssä. Ero syntyy MuseScoren omassa `.mxl` → `.mscz`
-muunnoksessa eikä tässä skriptissä — patchattu ja patchaamaton `.mscz`
antavat identtisen MIDIn.

Itse voit tarkistaa tuloksen avaamalla tiedoston ja painamalla play:
näkyvissä pitää olla yksi viivasto, ja soinnista pitää erottua trumpetti
kuoron seasta. Jos MuseScoren päivitys joskus rikkoo tiedoston, aja
skripti uudelleen — lähdeaineistoon se ei koske.
