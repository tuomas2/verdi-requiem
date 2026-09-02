# Verdin Requiemin yhdistäminen yhdeksi partituuriksi

## Tiedostot

| Tiedosto | Sisältö |
|---|---|
| `Verdi-Requiem-koko.mxl` | Koko teos, 15 viivastoa, 1807 tahtia |
| `stemma-*.mxl` / `stemma-*.pdf` | Kahdeksan kuorostemmaa, kaikki ajan tasalla (II·9b mukana, tahtinumerointi juoksee Dies iraen läpi) |
| `stemmat-sisallys.txt` | Osien alkusivut kaikissa kahdeksassa, ajan tasalla |
| `sisallys.py` | Rakentaa tuon luettelon uudelleen valmiista stemma-PDF:istä |
| `tiivistys.mss` | Tyylitiedosto: taukotahtien tiivistys, tahtinumero joka tahtiin, väljyys rivien välissä |
| `harjoitus-*.mscz` | Harjoittelutiedosto: oma ääni trumpettina, muut piilossa |
| `yhdista.py` | Yhdistämisskripti, kartoitustaulukko tiedoston alussa |
| `harjoitus.py` | Rakentaa harjoittelutiedoston yhdelle laulajalle |
| `korjaa_sanat.py` | Korjaa osien 01, 14 ja II·9b:n kuorosanat lähde-PDF:ää vasten |
| `korjaa_kasin.py` | Käsin todennetut korjaukset (osa I, Liber scriptus), taulukkona |
| `nayta.py` | Näyttää viivaston nuotit, äänet ja sanarivit tahdeittain |
| `fix-mxl.py` | Korjaa Audiveris-viennistä puuttuvat tahdit |
| `Verdi_10bDies_irae.pdf` | II·9b:n lähde-PDF (käyttäjän löytämä) |
| `10b-Verdi_Dies_irae_paluu-OMR*.mxl` | II·9b, konelukemisen tulos ja sanakorjattu versio |
| `*-kasin.mxl` | **Skriptin tuottamia**, ei käsin muokattuja: `korjaa_kasin.py`:n tulos, ja juuri nämä `yhdista.py` lukee osista I ja II·4 |

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
    "/Applications/MuseScore 4.app/Contents/MacOS/mscore" \
        -S tiivistys.mss -o stemma-basso-1.pdf stemma-basso-1.mxl
    python3 harjoitus.py --stemma "Basso I"       # 5. harjoittelutiedosto

Vaiheet 4 ja 5 toistetaan kullekin tarvittavalle äänelle. Yksittäiset
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
ja mistä tietää onko vika datassa vai skriptissä — on `CLAUDE.md`:n luvussa
*Recipe: a singer reports a wrong syllable by ear*.

Jos kokonainen kohta puuttuu eikä kyse ole vain tavusta, sama taulukko osaa
kopioida valmiin tahdin toisaalta samasta stemmasta (`kopioi_tahti`) — niin
korjattiin Liber scriptuksen puuttuneet "Di-es i-rae." -välihuudahdukset
tahdeissa 229, 231 ja 233.

Osien 11 (Lacrymosa) ja 14 (Agnus Dei) korjaukset on aikanaan tehty suoraan
lähdetiedostoon, joten niillä ei vielä ole vastaavaa taulukkoa.

## Tarkistettavaa harjoituksissa

Kolme kohtaa on jätetty tietoisesti auki: ne ratkeavat kuoron nuottikirjasta
tai kapellimestarilta, eivät tiedostoja tutkimalla. Jokainen on yhden rivin
muutos `korjaa_kasin.py`:ssä.

| Kohta | Mitä stemmassa nyt lukee | Mitä pitää tarkistaa |
|---|---|---|
| I, t. 51-52 | `om – – nis`, eli melisma tavulla "om" ja "nis" tahdin 52 viimeisellä nuotilla — pyyntösi mukaan | Lähde-PDF merkitsee toisin päin: "nis" tahdin 51 kolmannelle iskulle ja melisma sen jälkeen. Kumpaa kuoro laulaa? |
| II·1, t. 28 | "Da-vid cum Sy-bil-la," viimeinen tavu `la,` on **A3** | Kuoron omassa MuseScore-tiedostossa se on oktaavia alempi **A2**. Osalle 02 ei ole lähde-PDF:ää, joten kumpikaan ei ole varmistettavissa täältä käsin. |
| II·4, t. 247-254 | Altto, tenori ja basso laulavat "Solvet saeclum in favilla" kahdesti | Sopraanolla on samassa kohdassa sen sijaan ylimääräiset "Dies irae, dies illa" -toistot. Nuotit on tarkistettu oikeiksi kaikilla äänillä; kyse on vain siitä, kumpi teksti on oikea. |

## Tahtinumerointi

Numerointi alkaa joka pääosassa (I, III, IV, V, VI, VII) ykkösestä. Poikkeus
on osa II, Dies irae: sen kymmenen alaosaa ja II·9b juoksevat yhtenäisesti
1:stä 698:aan, koska kuoron nuottikirja numeroi Dies iraen niin. MuseScore
kunnioittaa MusicXML:n tahtinumeroita, joten osiorajoja ei tarvita kummassakaan
tapauksessa.

Toteutus on `yhdista.py`:n `DIES_IRAE_ALUT`-taulukko ja kytkin

    NUMEROINTI_ALKAA_JOKA_OSASSA_YKKOSESTA = False

Taulukossa on **kunkin alaosan ensimmäisen tahdin numero kuoron
nuottikirjassa**, kirjasta luettuna (2026-09-02), ei laskettuna:

    II·1 Dies irae 1, II·2 Tuba mirum 91, II·3 Mors stupebit 143,
    II·4 Liber scriptus 162, II·5 Quid sum miser 271, II·6 Rex tremendae 322,
    II·7 Recordare 386, II·8 Ingemisco 450, II·9 Confutatis 507,
    II·9b Dies irae (kertaus) 573, II·10 Lacrymosa 621

Aiemmin nämä laskettiin lähdetiedostojen omista tahtimääristä, ja kuusi
yhdestätoista oli väärin — Lacrymosassa jo kahdeksan tahtia. CPDL:n
osakohtaiset tiedostot eivät katkea samoista kohdista kuin kirja, joten
numerointi ei jatku saumojen yli aukottomasti: viidessä saumassa muutama
numero toistuu ja kolmessa muutama puuttuu lähteistä. `yhdista.py` tulostaa
nämä joka ajolla. Lukustemmoissa se ei näy, koska kaikki toistuvat tahdit
ovat kuorolle taukoa ja katoavat taukopalkkeihin. Ks. `CLAUDE.md`:
**2026-09-02 (later): the book's own bar numbers for Dies irae**.

Huom: jos vanhoissa muistiinpanoissa on Dies iraen tahtinumeroita ennen
2026-09-02, ne ovat vanhassa numeroinnissa — Lacrymosasta vähennetään 8,
II·9b:stä 5, Rex tremendaesta 2, Tuba mirumista ja Liber scriptuksesta 1,
ja Mors stupebitiin lisätään 2.

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

Sarakkeessa on tahtien määrä. Dies iraen numerointi juoksee 1:stä 698:aan
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
ja muut äänet eivät vielä ole. Ks. `CLAUDE.md`: **Fixing OMR lyrics** ja
**The missing Dies irae recall (II·9b)** tekniselle taustalle.

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
tahdista 72. Tekninen tausta: `CLAUDE.md` -> **2026-08-31 (later): Agnus Dei's
chorus bass, whole movement verified**.

**Poikkeus edelliseen: Lacrymosan (11) kuorobassolla oli aito virhe, ei
OMR:stä johtuva.** Rivin loppupuolella (n. 30 tahtia) oli joko tyhjää tai
väärää tekstiä — sanat vaikuttivat kopioituneen väärään kohtaan alkuperäisen
tiedoston teossa. Löytyi ja korjattiin 2026-08-28 vertaamalla toiseen,
käyttäjän löytämään Lacrymosa-PDF:ään. Tekninen tausta: `CLAUDE.md` ->
**Lacrymosa's chorus bass: wrong text, not missing measures**. Muiden äänten
(Sopraano/Altto/Tenori, solistit) samaa tiedostoa ei ole tarkistettu yhtä
tarkasti — sama virhetyyppi voisi periaatteessa olla muuallakin näissä 14
"luotettavassa" osassa.

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

## Kartoituksen erikoistapaukset

**Osa I** (Audiveris pilkkoi solistiviivastot): Solisti S = P7+P3+P1,
M-S = P8+P4+P2, T = P10+P5+P12, B = P11+P6. Kuoro = P13–P16. P9 on tyhjä.
Nimetyt osastot ("Sop.", "Mex.", "83.") ovat solisteja, koska Audiveris luki
partituurin nimilaput; nimeämättömät "Voice"-osastot ovat kuoro.

**Osa V**: P5 ja P6 ovat tahdeissa 1–13 sopraano- ja mezzosoolo (a cappella
-alku) ja tahdista 14 alkaen pianon kaksi viivastoa. Kartoitus jakaa ne tahtien
mukaan.

**Osa II·10 Lacrymosa**: P9 on kuorobasson divisi tahdeissa 54–56, ja se
yhdistetään kuorobassoriville omaksi äänekseen.

## Sanojen korjaus

Osien 01 ja 14 sanoissa oli konelukemisen virheitä kuten `Is-ru-sa-lem`,
`Te dc-cet` ja `V0-tum`, ja paikoin esitysmerkintä oli luettu sanaksi
(`sotto voce` → `SOITO` / `VOCE`, `PPP`, `morendo`). Molempien lähde-PDF:ien
sanat ovat kuitenkin **oikeaa tekstiä eivät kuvaa**, joten oikea sanoitus
saadaan luettua suoraan lähteestä.

    python3 korjaa_sanat.py            # korjaa ja kirjoita
    python3 korjaa_sanat.py --kuiva    # näytä raportti, älä kirjoita mitään

Tulos menee tiedostoihin `01-Verdi_Requiem-OMR-korjattu.mxl` ja
`14-Verdi_requiem_agnus-dei-OMR-korjattu.mxl`, ja `yhdista.py` käyttää niitä.
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
