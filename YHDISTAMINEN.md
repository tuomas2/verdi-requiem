# Verdin Requiemin yhdistäminen yhdeksi partituuriksi

## Tiedostot

| Tiedosto | Sisältö |
|---|---|
| `Verdi-Requiem-koko.mxl` | Koko teos, 15 viivastoa, 1756 tahtia |
| `stemma-*.mxl` / `stemma-*.pdf` | Kahdeksan kuorostemmaa, 13-14 sivua kukin |
| `stemmat-sisallys.txt` | Osien alkusivut kaikissa kahdeksassa |
| `tiivistys.mss` | Tyylitiedosto: taukotahtien tiivistys |
| `harjoitus-*.mscz` | Harjoittelutiedosto: oma ääni trumpettina, muut piilossa |
| `yhdista.py` | Yhdistämisskripti, kartoitustaulukko tiedoston alussa |
| `harjoitus.py` | Rakentaa harjoittelutiedoston yhdelle laulajalle |
| `korjaa_sanat.py` | Korjaa osien 01 ja 14 kuorosanat lähde-PDF:ää vasten |
| `fix-mxl.py` | Korjaa Audiveris-viennistä puuttuvat tahdit |

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
    python3 yhdista.py Verdi-Requiem-koko.mxl     # 2. partituuri
    python3 yhdista.py stemma-basso-1.mxl --stemma "Basso I"   # 3. stemmat
    "/Applications/MuseScore 4.app/Contents/MacOS/mscore" \
        -S tiivistys.mss -o stemma-basso-1.pdf stemma-basso-1.mxl
    python3 harjoitus.py --stemma "Basso I"       # 4. harjoittelutiedosto

Vaiheet 3 ja 4 toistetaan kullekin tarvittavalle äänelle. Yksittäiset
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

Sisällysluettelon sivunumerot on poimittu valmiista PDF:stä, joten päivitä
`stemmat-sisallys.txt` jos sivutus muuttuu.

## Viivastot

Solisti S / M-S / T / B, Kuoro S / A / T / **B** / S II / A II / T II / B II,
D-trumpetti, Trombone, Piano (2 viivastoa).

Kuoro B on se rivi jota luetaan. Kuoro S II – B II esiintyvät vain Sanctuksessa
(kaksoiskuoro) ja vasket vain Tuba mirumissa, jossa ei ole pianoa lainkaan.

## Tahtinumerointi

Numerointi säilyy lähdetiedostojen mukaisena, eli **alkaa joka osassa ykkösestä**.
MuseScore kunnioittaa MusicXML:n tahtinumeroita, joten osiorajoja ei tarvita.

Tämä on oletus, joka on tehty ilman kuoron nuottikirjaa. Jos kirja numeroikin
Dies iraen yhtenäisesti läpi, aseta `yhdista.py`:ssä

    NUMEROINTI_ALKAA_JOKA_OSASSA_YKKOSESTA = False

jolloin `DIES_IRAE_SIIRTYMAT` lisää alaosiin vakiosiirtymän ja numerointi juoksee
1–655 koko numeron II läpi.

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
| II | Dies irae (10 alaosaa) | 655 |
| III | Offertorio | 222 |
| IV | Sanctus | 139 |
| V | Agnus Dei | 74 |
| VI | Lux aeterna | 105 |
| VII | Libera me | 421 |
| | **Yhteensä** | **1756** |

Kuorobasso vaikenee kokonaan osissa II·3 Mors stupebit, II·5 Quid sum miser,
II·7 Recordare, II·8 Ingemisco, II·9 Confutatis, III Offertorio ja VI Lux
aeterna — ne ovat soolonumeroita. Se ei ole virhe.

## Tunnetut rajoitukset

**Osat I ja V ovat konelukemisen tulosta** (Audiveris PDF:stä), joten niiden
nuotit ja sanat eivät ole yhtä luotettavia kuin muiden. Muut 14 osaa tulevat
julkaisukuntoisista lähteistä.

Sanat on nyt korjattu koneellisesti lähde-PDF:ää vasten, ks. **Sanojen
korjaus** alla. Nuotteja se ei koske: ne pitää edelleen oikaisulukea.

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
Konelukemisen alkuperäisiin tiedostoihin ei kosketa, joten korjaus on
ajettavissa uudelleen jos konelukeminen joskus tehdään uusiksi.

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
