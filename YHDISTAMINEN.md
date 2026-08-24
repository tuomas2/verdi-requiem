# Verdin Requiemin yhdistäminen yhdeksi partituuriksi

## Tiedostot

| Tiedosto | Sisältö |
|---|---|
| `Verdi-Requiem-koko.mxl` | Koko teos, 15 viivastoa, 1756 tahtia |
| `stemma-*.mxl` / `stemma-*.pdf` | Kahdeksan kuorostemmaa, 13-14 sivua kukin |
| `stemmat-sisallys.txt` | Osien alkusivut kaikissa kahdeksassa |
| `tiivistys.mss` | Tyylitiedosto: taukotahtien tiivistys |
| `yhdista.py` | Yhdistämisskripti, kartoitustaulukko tiedoston alussa |
| `fix-mxl.py` | Korjaa Audiveris-viennistä puuttuvat tahdit |

## Työnkulku

Harjoitteluun avaa **`Verdi-Requiem-koko.mxl`** MuseScoressa ja piilota muut
viivastot kuin oma äänesi. Piilotetut viivastot soivat edelleen, joten kuulet
koko kuoron ja pianon vaikka luet vain omaa riviäsi.

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
nuotit ja sanat eivät ole yhtä luotettavia kuin muiden. Sanoissa on OCR-virheitä
kuten "V0-tum in Is-ru-sa-lem" ja "ra-t1-nem me-am". Nämä kaksi osaa pitää
oikaisulukea nuottia vasten. Muut 14 osaa tulevat julkaisukuntoisista lähteistä.

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
