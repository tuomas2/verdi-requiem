# Julkinen repo ja sivusto — toteutussuunnitelma

> **Agenttityöskentelijälle:** PAKOLLINEN ALITAITO: käytä
> `superpowers:subagent-driven-development` (suositus) tai
> `superpowers:executing-plans` toteuttaaksesi tämän tehtävä kerrallaan.
> Askeleet on merkitty valintaruuduilla (`- [ ]`).

**Tavoite:** Tehdä tästä hakemistosta julkinen repo `tuomas2/verdi-requiem`
ja GitHub Pages -sivusto, ilman `musescore/`-hakemistoa missään muodossa.

**Arkkitehtuuri:** Nuottiaineisto siirtyy neljään hakemistoon, jotka vastaavat
datan kulkusuuntaa (`lahteet/` → `johdetut/` → `stemmat/`). Skriptien taulukot
säilyvät paljaine tiedostonimineen, ja uusi `polut.py` selvittää hakemiston
nimestä, joten muutettavia kohtia on noin 20 eikä 117. Sivusto generoidaan
`sivusto.py`:llä samoista vakioista jotka ohjaavat stemmojen tuotantoa, joten
sisällys ei voi ajautua niistä erilleen.

**Teknologiat:** Python 3.9 vakiokirjasto, MuseScore 4.7.4 CLI, `mutool`,
`git-filter-repo`, GitHub Actions.

**Spec:** `docs/suunnitelmat/2026-09-04-julkinen-repo-ja-sivusto.md`

## Yleiset reunaehdot

Nämä koskevat jokaista tehtävää.

- **Ei riippuvuuksia.** Vain Python 3.9 vakiokirjasto, kuten kaikki nykyiset
  skriptit. Ei `pip install` -rivejä uuteen koodiin.
- **Kaikki suomeksi.** Dokumentaatio, tulosteet, muuttujanimet uudessa
  koodissa ja commit-viestit. `CLAUDE.md` on ainoa englanninkielinen tiedosto
  ja se jää sellaiseksi.
- **`musescore/` ei mihinkään.** Ei työhakemistoon, ei historiaan, ei
  sivustolle. Ainoat sallitut maininnat ovat `korjaa_kasin.py`:n olemassa
  olevat kommentit, jotka kertovat mistä korjauksen todiste tuli.
- **Generoitua HTML:ää ei committoida.** `_sivusto/` on `.gitignore`ssa.
- **`.mxl`-tiedostoja ei verrata tavuina.** `zipfile.writestr` leimaa
  nykyhetken jokaiseen zip-merkintään, joten kaksi ajoa samasta datasta
  tuottavat eri tavut. Vertaa aina puretun `score.xml`:n sisältöä.
- **MuseScoren CLI kaatuu teardownissa noin joka kolmas ajo** (exit 134)
  kirjoitettuaan täyden PDF:n. Tarkista tulos sivumäärästä, älä
  paluuarvosta, äläkä laita `mscore`a `set -e`:n alle.
- **Testit:** `python3 -m unittest discover -p 'test_*.py'`. Lähtötaso 136.
- **Commit-viestit suomeksi**, syy rungossa, lopussa rivi
  `Claude-Session: https://claude.ai/code/session_01Tqe8F2oYZV9mDXKdqVYdff`.

---

## Tiedostorakenne

Uudet tiedostot:

| Tiedosto | Vastuu |
|---|---|
| `polut.py` | Hakemiston selvitys tiedostonimestä. Ei muuta. |
| `test_polut.py` | Säännön yksikkötestit ja olemassaolon ristiintarkistus |
| `luotettavuus.py` | Käsin ylläpidetty taulukko: mikä on tarkistettu |
| `test_luotettavuus.py` | Kattavuus: rivi jokaiselle osalle ja äänelle |
| `sivusto.py` | Sivuston generointi `_sivusto/`-hakemistoon |
| `test_sivusto.py` | Sivut syntyvät, sisällys vastaa stemmoja |
| `sivusto/tyyli.css` | Jaetut väri- ja typografiamuuttujat |
| `sivusto/requiem.html` | Latina–suomi-teksti, kopio nykyiseltä sivustolta |
| `README.md` | Julkinen esittely suomeksi |
| `LICENSE` | GPL-3.0-or-later |
| `.github/workflows/sivusto.yml` | Pages-julkaisu |

Muutettavat: `yhdista.py`, `korjaa_sanat.py`, `korjaa_kasin.py`,
`sisallys.py`, `harjoitus.py`, `nayta.py`, `sivuotsikot.py`, `.gitignore`,
`CLAUDE.md` (kehysteksti alkuun), `YHDISTAMINEN.md` (komentojen polut).

---

## Tehtävä 1: `polut.py` ja säännön testit

**Tiedostot:**
- Luo: `polut.py`
- Luo: `test_polut.py`

**Rajapinta:**
- Tuottaa: `polut.polku(nimi) -> str` ja `polut.hakemisto(nimi) -> str`.
  Vakiot `LAHTEET`, `JOHDETUT`, `STEMMAT`, `HARJOITUS` ovat merkkijonoja.
  Kaikki myöhemmät tehtävät käyttävät näitä.

Tässä tehtävässä ei siirretä yhtään tiedostoa. Sääntö kirjoitetaan ja
testataan ensin, jotta siirto tehdään valmiiksi testattua sääntöä vasten.

- [ ] **Askel 1: Kirjoita kaatuva testi**

`test_polut.py`:

```python
import unittest
import polut


class Saanto(unittest.TestCase):
    def test_lahde_menee_lahteisiin(self):
        self.assertEqual(polut.polku("04-Verdi-Mors_stupebit.mxl"),
                         "lahteet/04-Verdi-Mors_stupebit.mxl")

    def test_raaka_omr_on_lahde(self):
        self.assertEqual(polut.polku("01-Verdi_Requiem-OMR.mxl"),
                         "lahteet/01-Verdi_Requiem-OMR.mxl")

    def test_korjattu_omr_on_johdettu(self):
        self.assertEqual(polut.polku("01-Verdi_Requiem-OMR-korjattu.mxl"),
                         "johdetut/01-Verdi_Requiem-OMR-korjattu.mxl")

    def test_kasin_on_johdettu(self):
        self.assertEqual(polut.polku("11-Verdi_Lacrymosa-kasin.mxl"),
                         "johdetut/11-Verdi_Lacrymosa-kasin.mxl")

    def test_koko_partituuri_on_johdettu(self):
        self.assertEqual(polut.polku("Verdi-Requiem-koko.mxl"),
                         "johdetut/Verdi-Requiem-koko.mxl")

    def test_stemma_ja_sen_sisallys(self):
        self.assertEqual(polut.polku("stemma-basso-1.pdf"),
                         "stemmat/stemma-basso-1.pdf")
        self.assertEqual(polut.polku("stemmat-sisallys.txt"),
                         "stemmat/stemmat-sisallys.txt")

    def test_harjoitustiedosto(self):
        self.assertEqual(polut.polku("harjoitus-basso-1.mscz"),
                         "harjoitus/harjoitus-basso-1.mscz")

    def test_valmis_polku_palautetaan_sellaisenaan(self):
        # Komentoriviltä voi antaa minkä tahansa tiedoston.
        self.assertEqual(polut.polku("johdetut/Verdi-Requiem-koko.mxl"),
                         "johdetut/Verdi-Requiem-koko.mxl")
        self.assertEqual(polut.polku("/tmp/koe.mxl"), "/tmp/koe.mxl")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Askel 2: Aja testi ja varmista että se kaatuu**

Aja: `python3 -m unittest test_polut -v`
Odotus: FAIL, `ModuleNotFoundError: No module named 'polut'`

- [ ] **Askel 3: Kirjoita `polut.py`**

```python
#!/usr/bin/env python3
"""Mistä hakemistosta mikäkin nuottitiedosto löytyy.

Tiedostonimi kertoo sen itse. Projektin nimeämiskäytäntö on ollut sama
alusta asti: johdetut tiedostot päättyvät -kasin.mxl tai -OMR-korjattu.mxl,
stemmat alkavat sanalla stemma, ja kaikki muu on lähdeaineistoa. Kun
hakemisto luetaan nimestä, skriptien taulukot (MOVEMENTS, MAPPING,
korjaa_kasin.py:n Osa-rivit) säilyvät luettavina paljaine tiedostonimineen
eikä hakemistoa tarvitse toistaa yli sadassa kohdassa.

Tämä koskee vain nuottiaineistoa. Työkalutiedostoilla kuten tiivistys.mss
on omat vakionsa eikä niitä reititetä tämän kautta.
"""

import os

LAHTEET = "lahteet"
JOHDETUT = "johdetut"
STEMMAT = "stemmat"
HARJOITUS = "harjoitus"

# Johdetun tiedoston tunnistaa päätteestä tai alkuosasta.
JOHDETUN_PAATTEET = ("-kasin.mxl", "-OMR-korjattu.mxl")
KOKO_PARTITUURI = "Verdi-Requiem-koko"


def hakemisto(nimi):
    """Hakemisto, johon paljas tiedostonimi kuuluu."""
    if nimi.endswith(JOHDETUN_PAATTEET) or nimi.startswith(KOKO_PARTITUURI):
        return JOHDETUT
    if nimi.startswith("stemma"):
        return STEMMAT
    if nimi.startswith("harjoitus-"):
        return HARJOITUS
    return LAHTEET


def polku(nimi):
    """Täysi polku nuottitiedostolle.

    Jos nimessä on jo hakemisto, se palautetaan sellaisenaan — komentoriviltä
    pitää voida antaa mikä tahansa tiedosto mistä tahansa.
    """
    if os.sep in nimi or (os.altsep and os.altsep in nimi):
        return nimi
    return os.path.join(hakemisto(nimi), nimi)
```

- [ ] **Askel 4: Aja testi ja varmista että se menee läpi**

Aja: `python3 -m unittest test_polut -v`
Odotus: 8 testiä OK

- [ ] **Askel 5: Committoi**

```bash
git add polut.py test_polut.py
git commit -F - <<'EOF'
Lisää polut.py, joka lukee hakemiston tiedostonimestä

Hakemistorakenteen käyttöönotto vaatisi muuten etuliitteen 117
tiedostonimiliteraaliin, jotka ovat luettavissa taulukoissa. Nimeämiskäytäntö
kertoo hakemiston jo nyt, joten sääntö riittää ja taulukot säilyvät
ennallaan.

Claude-Session: https://claude.ai/code/session_01Tqe8F2oYZV9mDXKdqVYdff
EOF
```

---

## Tehtävä 2: Vertailukohta ennen siirtoa

**Tiedostot:**
- Luo: `<scratchpad>/vertailu.py` — **kertakäyttöinen**, ei committoida

**Rajapinta:**
- Tuottaa: `<scratchpad>/ennen.json`, jota tehtävä 3 käyttää.

Siirto ei saa muuttaa yhtään tulosta. Se todistetaan vertaamalla, ja
vertailukohta on otettava **ennen** kuin mitään siirretään.

- [ ] **Askel 1: Kirjoita vertailuskripti**

```python
#!/usr/bin/env python3
"""Kertakäyttöinen: ota sormenjälki ketjun tuloksista.

.mxl on zip, jonka merkintöihin zipfile leimaa kirjoitushetken, joten
tavuvertailu ei kelpaa. Verrataan puretun XML:n sisältöä.
"""
import hashlib, json, os, sys, zipfile


def sisalto(polku):
    if polku.endswith(".mxl"):
        with zipfile.ZipFile(polku) as z:
            nimi = next(n for n in z.namelist()
                        if not n.startswith("META-INF")
                        and n.lower().endswith(".xml"))
            data = z.read(nimi)
    else:
        data = open(polku, "rb").read()
    return hashlib.sha256(data).hexdigest()


def main(juuri, ulos):
    tulos = {}
    for hakemisto, _, tiedostot in os.walk(juuri):
        if ".git" in hakemisto or "musescore" in hakemisto:
            continue
        for t in tiedostot:
            if t.endswith((".mxl", ".txt")) and not t.startswith("."):
                tulos[t] = sisalto(os.path.join(hakemisto, t))
    json.dump(tulos, open(ulos, "w"), indent=1, sort_keys=True)
    print(f"{len(tulos)} tiedostoa -> {ulos}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
```

- [ ] **Askel 2: Aja ketju puhtaalta pöydältä ja ota sormenjälki**

```bash
cd /Users/tuomasairaksinen/verdi-requiem
python3 korjaa_sanat.py
python3 korjaa_kasin.py
python3 yhdista.py Verdi-Requiem-koko.mxl
for s in "Sopraano I:sopraano-1" "Sopraano II:sopraano-2" \
         "Altto I:altto-1" "Altto II:altto-2" \
         "Tenori I:tenori-1" "Tenori II:tenori-2" \
         "Basso I:basso-1" "Basso II:basso-2"; do
  python3 yhdista.py "stemma-${s#*:}.mxl" --stemma "${s%%:*}"
done
python3 "$SCRATCH/vertailu.py" . "$SCRATCH/ennen.json"
```

Odotus: tuloste kertoo noin 30 tiedostoa.

- [ ] **Askel 3: Varmista että työpuu on siisti**

Aja: `git status --porcelain`
Odotus: tyhjä tai vain `.mxl`-tiedostoja, joiden **sisältö** ei muuttunut.
Jos `git diff --stat` näyttää muutoksia, tarkista `vertailu.py`:llä ettei
sisältö muuttunut, ja palauta ne: `git checkout -- .`

Tämä askel on tärkeä: siirto pitää tehdä tilasta, joka vastaa committia.

---

## Tehtävä 3: Hakemistorakenne ja polkumuutokset

**Tiedostot:**
- Siirrä: kaikki nuottiaineisto neljään hakemistoon
- Muokkaa: `yhdista.py`, `korjaa_sanat.py`, `korjaa_kasin.py`,
  `sisallys.py`, `harjoitus.py`, `nayta.py`, `sivuotsikot.py`
- Muokkaa: `test_polut.py` (olemassaolon ristiintarkistus)
- Muokkaa: `test_yhdista.py`, `test_korjaa_sanat.py`, `test_korjaa_kasin.py`,
  `test_sivuotsikot.py`, `test_harjoitus.py` — vain jos ne avaavat tiedostoja

**Rajapinta:**
- Käyttää: `polut.polku` tehtävästä 1
- Tuottaa: hakemistorakenne, jota tehtävät 6–9 lukevat

- [ ] **Askel 1: Luo hakemistot ja siirrä tiedostot**

```bash
mkdir -p lahteet johdetut stemmat harjoitus
git mv 0*.mxl 1*.mxl lahteet/ 2>/dev/null
git mv *.pdf *.omr lahteet/
git mv 02-Verdi-Dies_irae.mscz 03-Verdi-Tuba_mirum.mscz 16-Libera_Me.mscz lahteet/
git mv lahteet/*-kasin.mxl lahteet/*-OMR-korjattu.mxl johdetut/
git mv Verdi-Requiem-koko.mxl johdetut/
git mv lahteet/stemma-*.pdf stemmat/ 2>/dev/null
git mv stemma-*.mxl stemmat/
git mv stemmat-sisallys.txt stemmat/
mv harjoitus-*.mscz harjoitus/ 2>/dev/null
git status --short | head -40
```

Odotus: `lahteet/` 28 tiedostoa, `johdetut/` 11, `stemmat/` 17.
Tarkista: `ls lahteet | wc -l; ls johdetut | wc -l; ls stemmat | wc -l`

- [ ] **Askel 2: Lisää olemassaolon ristiintarkistus `test_polut.py`:hyn**

Tämä on se testi, joka estää sääntöä jäämästä hiljaiseksi oletukseksi.

```python
import os
import korjaa_kasin
import korjaa_sanat
import sisallys
import yhdista


def taulukoiden_nimet():
    """Jokainen tiedostonimi, jonka jokin taulukko mainitsee."""
    nimet = set()
    nimet.update(t for t, _, _ in yhdista.MOVEMENTS)
    nimet.update(yhdista.MAPPING)
    nimet.update(yhdista.DIES_IRAE_ALUT)
    nimet.update(yhdista.OMR_SOURCES)
    nimet.add(yhdista.SANCTUS)
    for s in korjaa_sanat.SOURCES:
        nimet.update([s.mxl, s.pdf, s.out])
    for osa in korjaa_kasin.OSAT:
        nimet.update([osa.mxl, osa.out])
    nimet.update(pdf for _, pdf in sisallys.STEMMAT)
    nimet.add(sisallys.ULOS)
    return nimet


class Olemassaolo(unittest.TestCase):
    def test_jokainen_taulukon_nimi_loytyy_saannon_osoittamasta_paikasta(self):
        for nimi in sorted(taulukoiden_nimet()):
            with self.subTest(nimi=nimi):
                self.assertTrue(os.path.exists(polut.polku(nimi)),
                                f"{nimi} ei ole polussa {polut.polku(nimi)}")

    def test_tiedosto_ei_ole_kahdessa_hakemistossa(self):
        """Eksynyt kopio antaisi hiljaa väärän tuloksen."""
        kaikki = [polut.LAHTEET, polut.JOHDETUT, polut.STEMMAT, polut.HARJOITUS]
        for nimi in sorted(taulukoiden_nimet()):
            paikat = [h for h in kaikki if os.path.exists(os.path.join(h, nimi))]
            with self.subTest(nimi=nimi):
                self.assertEqual(len(paikat), 1, f"{nimi} löytyy: {paikat}")
```

- [ ] **Askel 3: Aja ja varmista että se kaatuu**

Aja: `python3 -m unittest test_polut -v`
Odotus: `Olemassaolo`-testit menevät läpi (tiedostot ovat jo paikoillaan),
mutta `import`it kaatuvat vasta jos skriptit eivät lataudu. Jos kaikki menee
läpi jo tässä, se on oikein — testi suojaa tästä eteenpäin.

- [ ] **Askel 4: Muuta avauskohdat käyttämään `polku()`:a**

Kohtia on vähän, koska taulukot ja avaukset ovat erillään. Jokaiseen
tiedostoon `import polut` ja:

`yhdista.py`:
```python
def load(path):
    with zipfile.ZipFile(polut.polku(path)) as z:
```
sekä `main()`:ssa ulostulo:
```python
    out_path = polut.polku(args[0] if args else "Verdi-Requiem-koko.mxl")
```
ja kirjoituskohdassa (rivi ~983) varmista hakemiston olemassaolo:
```python
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
```

`korjaa_sanat.py`: rivien 523, 536, 542 funktiot ottavat polun; kääri
`polut.polku()` niiden sisällä samaan tapaan.

`korjaa_kasin.py`: `main()`:ssa
```python
        root = load(polut.polku(mxl))
        ...
            save(root, polut.polku(mxl), polut.polku(out))
```
Huom: `print(f"{mxl} -> {out}")` jätetään paljaisiin nimiin, koska tuloste on
luettavampi niin.

`sisallys.py`: `open(polut.polku(ULOS), 'w')` ja PDF:ien avaus
`polut.polku(pdf)`.

`harjoitus.py`: `build()`:ssä `source` ja ulostulo `polut.polku()`:n läpi;
`TYYLI` **ei** — se on juuressa.

`nayta.py` ja `sivuotsikot.py`: komentoriviltä tuleva tiedostonimi
`polut.polku()`:n läpi. Koska `polku()` palauttaa valmiin polun sellaisenaan,
molemmat tavat toimivat.

- [ ] **Askel 5: Aja koko testijoukko**

Aja: `python3 -m unittest discover -p 'test_*.py'`
Odotus: 136 + 10 = noin 146 testiä, kaikki läpi.
Jos jokin testi avaa tiedoston suoraan nimellä, korjaa se `polut.polku()`:lla.

- [ ] **Askel 6: Aja koko ketju uudelleen ja vertaa**

```bash
python3 korjaa_sanat.py && python3 korjaa_kasin.py
python3 yhdista.py Verdi-Requiem-koko.mxl
for s in "Sopraano I:sopraano-1" "Sopraano II:sopraano-2" \
         "Altto I:altto-1" "Altto II:altto-2" \
         "Tenori I:tenori-1" "Tenori II:tenori-2" \
         "Basso I:basso-1" "Basso II:basso-2"; do
  python3 yhdista.py "stemma-${s#*:}.mxl" --stemma "${s%%:*}"
done
python3 "$SCRATCH/vertailu.py" . "$SCRATCH/jalkeen.json"
python3 - <<'EOF'
import json
a = json.load(open("$SCRATCH/ennen.json"))
b = json.load(open("$SCRATCH/jalkeen.json"))
erot = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
print("eroja:", len(erot))
for k in sorted(erot): print("  ", k, a.get(k, "-")[:8], b.get(k, "-")[:8])
EOF
```

**Odotus: `eroja: 0`.** Tämä on tehtävän hyväksymiskriteeri. Jos eroja on,
älä jatka — selvitä syy. Poikkeus: jos jokin tiedosto puuttuu toisesta
listasta pelkän hakemistonvaihdon takia, korjaa vertailu käyttämään
pelkkää tiedostonimeä avaimena (kuten yllä oleva `vertailu.py` tekee).

- [ ] **Askel 7: Renderöi yksi stemma ja tarkista silmällä**

```bash
python3 sivuotsikot.py stemma-basso-1.mxl
mscore -S tiivistys.mss -o stemmat/stemma-basso-1.pdf stemmat/stemma-basso-1.mxl
mutool info stemmat/stemma-basso-1.pdf | grep -i pages
```
Odotus: 16 sivua, sama kuin ennen. Paluuarvoa ei tarkisteta.

- [ ] **Askel 8: Päivitä `YHDISTAMINEN.md`:n komennot**

Kaikki `python3 yhdista.py …` -rivit toimivat ennallaan, koska `polku()`
hoitaa nimet. Tarkista silti tiedostolistaus luvussa *Tiedostot* ja lisää
hakemistot siihen.

- [ ] **Askel 9: Committoi**

```bash
git add -A
git commit -F - <<'EOF'
Järjestä nuottiaineisto neljään hakemistoon

Juuressa oli noin 70 tiedostoa sekaisin. Hakemistot vastaavat nyt datan
kulkusuuntaa: lahteet/ -> johdetut/ -> stemmat/. Skriptien taulukot
säilyivät ennallaan, koska polut.py lukee hakemiston tiedostonimestä.

Todistettu muuttumattomaksi: koko ketju ajettiin ennen ja jälkeen ja
johdettujen tiedostojen purettu XML on tavulleen sama. Itse .mxl-tavut
eroavat aina, koska zipfile leimaa niihin kirjoitushetken.

Claude-Session: https://claude.ai/code/session_01Tqe8F2oYZV9mDXKdqVYdff
EOF
```

---

## Tehtävä 4: `.gitignore` ja generoitujen binäärien poisto seurannasta

**Tiedostot:**
- Muokkaa: `.gitignore`

- [ ] **Askel 1: Lisää `.gitignore`een**

```
# Generoidut harjoitustiedostot: 3,2 MB kappale ja uusi kopio joka
# rakennuskerralla. Syntyvät komennolla harjoitus.py.
harjoitus/

# Sivuston paikallinen esikatselu; CI rakentaa julkaistavan version.
_sivusto/
```

- [ ] **Askel 2: Poista seurannasta, säilytä levyllä**

```bash
git rm --cached Verdi-Requiem-koko-oma.mscz
git rm --cached harjoitus/harjoitus-*.mscz 2>/dev/null || true
ls harjoitus/
```
Odotus: tiedostot ovat yhä levyllä.

- [ ] **Askel 3: Committoi**

```bash
git add .gitignore
git commit -F - <<'EOF'
Poista generoidut harjoitustiedostot versionhallinnasta

harjoitus-basso-1.mscz on 3,2 MB ja tallentui uutena kopiona joka
rakennuskerralla — noin kaksitoista versiota, eli suurin yksittäinen syy
siihen että .git on 124 MB. Tiedosto syntyy komennolla harjoitus.py.
Verdi-Requiem-koko-oma.mscz poistuu samalla; siihen ei viitata mistään.

Claude-Session: https://claude.ai/code/session_01Tqe8F2oYZV9mDXKdqVYdff
EOF
```

---

## Tehtävä 5: README, LICENSE ja `CLAUDE.md`:n kehysteksti

**Tiedostot:**
- Luo: `README.md`, `LICENSE`
- Muokkaa: `CLAUDE.md` (vain alkuun lisättävä kehys)

- [ ] **Askel 1: Hae GPL-3.0-teksti**

```bash
curl -sL https://www.gnu.org/licenses/gpl-3.0.txt -o LICENSE
head -3 LICENSE; wc -l LICENSE
```
Odotus: "GNU GENERAL PUBLIC LICENSE", noin 674 riviä.

- [ ] **Askel 2: Kirjoita `README.md`**

Rakenne täsmälleen tässä järjestyksessä. Luotettavuus on kolmantena, ei
alaviitteenä — se on lukijalle tärkein tieto ennen kuin hän lataa mitään.

```markdown
# Verdi: Messa da Requiem — kuorostemmat ja yhdistetty partituuri

Verdin *Messa da Requiem* MusicXML-muodossa: kuusitoista erillistä
osatiedostoa yhdistettynä yhdeksi partituuriksi, ja siitä tuotetut
kahdeksan kuorostemmaa harjoittelua varten.

Lähtökohta on kuorolaisen käytännön tarve: lukea omaa stemmaa niin että
muu kuoro ja pianosäestys kuuluvat, kantaa stemma mukana lukulaitteella,
ja löytää tahti jonka kuoronjohtaja huutaa. Siitä seuraa kaksi vaatimusta,
jotka ohjaavat kaikkea muuta: **tahtinumeroiden on täsmättävä kuoron oman
nuottikirjan kanssa** ja stemman on oltava tiivis.

## Mitä täältä saa

| | |
|---|---|
| `stemmat/stemma-*.pdf` | Kahdeksan stemmaa: S/A/T/B × I/II. Tahtinumero joka tahdin päällä, osan nimi joka sivun yläreunassa |
| `johdetut/Verdi-Requiem-koko.mxl` | Koko teos yhtenä partituurina, 15 viivastoa, 1807 tahtia |
| `stemmat/stemmat-sisallys.txt` | Miltä sivulta mikin osa alkaa kussakin stemmassa |
| `harjoitus.py` | Rakentaa harjoitustiedoston, jossa oma ääni soi trumpettina ja muut kuuluvat mutta eivät näy |

## Luotettavuus — lue tämä ennen kuin luotat nuottiin

**Vain kuorobasso on käyty järjestelmällisesti läpi.** Sopraano, altto ja
tenori ovat pääosin tarkistamatta, ja kahdessa osassa niissä on tiedettyjä
virheitä.

Syy on yksinkertainen: tekijä laulaa bassoa, ja jokainen virhe on löytynyt
joko laulamalla mukana tai vertaamalla sitä riviä riippumattomaan lähteeseen.

| Tila | Merkitys |
|---|---|
| ✔ varmistettu | Vertailtu riippumattomaan lähteeseen nuotti nuotilta tai tavu tavulta |
| ◑ osittain | Esimerkiksi sanat tarkistettu, nuotit eivät |
| ○ tarkistamatta | Ei tunnettuja virheitä, mutta ei myöskään tarkistettu |
| ⚠ puutteita | Tiedetään virheellistä sisältöä |

Osakohtainen taulukko on sivustolla ja tiedostossa `luotettavuus.py`.

Kaksi asiaa kannattaa tietää tarkistustyöstä, koska ne toistuivat:

- **Painettu nuotti ei ratkaise kaikkea.** Lacrymosan tahdeissa 657–665
  painettu CPDL-editio antaa kuorobassolle väärän tekstin, ja tahdissa 653
  väärän sävelen. Kummankin ratkaisi se, mitä muut äänet ja pianosäestys
  tekevät samalla iskulla.
- **Konelukemisen (OMR) tulos on eri luokkaa kuin muu aineisto.** Osat 01
  ja 14 sekä II·9b ovat PDF:stä koneluettuja, ja niiden nuotit ovat
  pääosin tarkistamatta.

## Miten sen toistaa

Tarvitset MuseScore 4:n komentoriviltä (`mscore`) ja `mutool`in
(`brew install mupdf-tools`). Python 3.9, ei riippuvuuksia.

```bash
python3 korjaa_sanat.py                       # OMR-osien sanat lähde-PDF:istä
python3 korjaa_kasin.py                       # käsin varmistetut korjaukset
python3 yhdista.py Verdi-Requiem-koko.mxl     # yhdistetty partituuri
python3 yhdista.py stemma-basso-1.mxl --stemma "Basso I"
python3 sivuotsikot.py stemma-basso-1.mxl     # osan nimi joka sivulle
mscore -S tiivistys.mss -o stemmat/stemma-basso-1.pdf stemmat/stemma-basso-1.mxl
python3 sisallys.py                           # sisällysluettelo
python3 -m unittest discover -p 'test_*.py'
```

`mscore` kaatuu noin joka kolmas ajo teardownissa kirjoitettuaan täyden
PDF:n. Tarkista tulos sivumäärästä, älä paluuarvosta.

## Hakemistot

| | |
|---|---|
| `lahteet/` | Alkuperäiset CPDL-tiedostot, lähde-PDF:t ja Audiveris-projektit. Näitä ei muokata |
| `johdetut/` | Skriptien tuottamat korjatut osat ja yhdistetty partituuri |
| `stemmat/` | Kahdeksan stemmaa ja niiden sisällysluettelo |
| `sivusto/` | Verkkosivuston lähteet |

## Nuottien alkuperä

Sävellys on public domainissa; Verdi kuoli 1901. Nuottiaineisto on CPDL:n
(Choral Public Domain Library) editioita kahdesta erästä, ja erän tunnistaa
tiedostonimen väliviivasta tai alaviivasta — **älä siis normalisoi niitä**:

- `Verdi-*` — Sibelius 7.5.1, 10.10.2017, osat 02–07, 13 ja 16.
- `Verdi_*` — Finale 2014 + Dolet, 11.5.2015, osat 08–12 ja 15. Nämä
  tiedostot sanovat itse: *"Copyright © 2009 by the Choral Public Domain
  Library (cpdl.org) — Edition may be freely distributed, duplicated,
  performed, or recorded."*

Lähde-PDF:ien (osat 01, 14, II·9b ja Lacrymosa) tekijätunnus on sama
`claud`/`Claude` kuin MusicXML-tiedostojen `<encoder>`-kentässä.

## Lisenssi

Skriptit ja tässä repossa kirjoitettu dokumentaatio: **GPL-3.0-or-later**,
ks. `LICENSE`. Lisenssi ei ulotu eikä voi ulottua CPDL:n editioihin, jotka
ovat oman lisenssinsä alaisia.

Kuoron omat MuseScore-harjoitustiedostot on jätetty pois kokonaan: niiden
tekijyys on tuntematon ja tiedostonimissä oli laulajien nimiä.

## Lue lisää

- [`YHDISTAMINEN.md`](YHDISTAMINEN.md) — miten yhdistäminen toimii ja mitä
  oletuksia siinä on tehty
- [`CLAUDE.md`](CLAUDE.md) — täydellinen tekninen työpäiväkirja: jokainen
  löydetty virhe, miten se löytyi ja mikä menetelmä toimi. Englanniksi
```

- [ ] **Askel 3: Lisää `CLAUDE.md`:n alkuun kehysteksti**

Ennen nykyistä ensimmäistä riviä:

```markdown
> **Mikä tämä tiedosto on.** Tämä on työpäiväkirja, jota on kirjoitettu
> istunto kerrallaan Claude Code -avusteisessa työssä, ja se on kirjoitettu
> ohjeeksi seuraavalle istunnolle — ei esittelyksi. Siksi se on englanniksi
> ja puhuu tekijästä kolmannessa persoonassa ("the user"): kyseessä on
> kuorolainen, joka laulaa bassoa ja lukee omaa stemmaansa.
>
> Se on silti tämän repon perusteellisin aineisto. Jos aiot parantaa
> nuotteja, lue erityisesti *Recipe: a singer reports a wrong syllable by
> ear* ja taulukko *Open* heti alusta — ne kertovat mistä kannattaa
> aloittaa ja mitkä menetelmät on jo kokeiltu ja hylätty.
```

- [ ] **Askel 4: Tarkista linkit**

Aja:
```bash
grep -o '\[.*\](\([^)h][^)]*\))' README.md | sed 's/.*(\(.*\))/\1/' | \
  while read f; do [ -e "$f" ] || echo "PUUTTUU: $f"; done
```
Odotus: ei tulostetta.

- [ ] **Askel 5: Committoi**

```bash
git add README.md LICENSE CLAUDE.md
git commit -F - <<'EOF'
Lisää README ja GPL-3.0-lisenssi

Repo on menossa julkiseksi, jotta joku muu voi jatkaa nuottien
parantamista. Siksi README nostaa luotettavuuden kolmanneksi luvuksi: vain
kuorobasso on käyty järjestelmällisesti läpi, ja se on lukijan tärkein tieto
ennen kuin hän lataa mitään.

CLAUDE.md sai alkuun kehyksen, joka kertoo miksi se on englanniksi ja miksi
se puhuu tekijästä kolmannessa persoonassa.

Claude-Session: https://claude.ai/code/session_01Tqe8F2oYZV9mDXKdqVYdff
EOF
```

---

## Tehtävä 6: `luotettavuus.py`

**Tiedostot:**
- Luo: `luotettavuus.py`, `test_luotettavuus.py`

**Rajapinta:**
- Käyttää: `yhdista.MOVEMENTS`, `yhdista.MAPPING`
- Tuottaa: `luotettavuus.tila(osanumero, aani) -> Tila`, jossa `Tila` on
  `namedtuple("Tila", "merkki nimi perustelu")`. `luotettavuus.AANET` on
  lista `["Kuoro S", "Kuoro A", "Kuoro T", "Kuoro B"]`. Tehtävä 7 käyttää
  näitä.

Suunnittelun ydin: **oletus plus poikkeukset**, ei 68 käsin kirjoitettua
riviä. Lisäksi "ei kuoroa" lasketaan `MAPPING`ista eikä ylläpidetä käsin.

- [ ] **Askel 1: Kirjoita kaatuva testi**

`test_luotettavuus.py`:

```python
import unittest
import luotettavuus
import yhdista


class Kattavuus(unittest.TestCase):
    def test_jokaiselle_osalle_ja_aanelle_on_tila(self):
        for _tiedosto, numero, _otsikko in yhdista.MOVEMENTS:
            for aani in luotettavuus.AANET:
                with self.subTest(osa=numero, aani=aani):
                    self.assertIsNotNone(luotettavuus.tila(numero, aani))

    def test_solistiosat_tunnistetaan_mappingista(self):
        # Mors stupebit on basson soolo; siinä ei ole kuoroa lainkaan.
        self.assertEqual(luotettavuus.tila("II·3", "Kuoro B").nimi, "ei kuoroa")
        # Lacrymosassa on.
        self.assertNotEqual(luotettavuus.tila("II·10", "Kuoro B").nimi,
                            "ei kuoroa")

    def test_varmistetut_ovat_ne_jotka_on_todella_tarkistettu(self):
        self.assertEqual(luotettavuus.tila("V", "Kuoro B").nimi, "varmistettu")
        self.assertEqual(luotettavuus.tila("II·10", "Kuoro B").nimi,
                         "varmistettu")

    def test_jokaisella_poikkeuksella_on_perustelu(self):
        for (osa, aani), t in luotettavuus.POIKKEUKSET.items():
            with self.subTest(osa=osa, aani=aani):
                self.assertTrue(t.perustelu.strip(), f"{osa}/{aani}")

    def test_poikkeukset_viittaavat_olemassa_oleviin_osiin(self):
        numerot = {n for _t, n, _o in yhdista.MOVEMENTS}
        for (osa, aani) in luotettavuus.POIKKEUKSET:
            with self.subTest(osa=osa, aani=aani):
                self.assertIn(osa, numerot)
                self.assertIn(aani, luotettavuus.AANET)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Askel 2: Aja ja varmista että se kaatuu**

Aja: `python3 -m unittest test_luotettavuus -v`
Odotus: FAIL, `ModuleNotFoundError: No module named 'luotettavuus'`

- [ ] **Askel 3: Kirjoita `luotettavuus.py`**

```python
#!/usr/bin/env python3
"""Mikä stemmoissa on tarkistettu ja mikä ei.

Tämä on ihmisen arvio eikä laskettu suure, joten se ylläpidetään käsin.
Lähde on CLAUDE.md:n työhistoria, johon jokainen tarkistus on kirjattu.

Rakenne on oletus plus poikkeukset: valtaosa on tarkistamatta, ja jokainen
poikkeus on kohta jossa on tehty oikeaa työtä. "Ei kuoroa" ei ole poikkeus
vaan lasketaan yhdista.MAPPINGista — solistiosat eivät tarvitse ylläpitoa.
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


def _v(perustelu):
    return Tila("✔", "varmistettu", perustelu)


def _o(perustelu):
    return Tila("◑", "osittain", perustelu)


def _p(perustelu):
    return Tila("⚠", "puutteita", perustelu)


def _t(perustelu):
    return Tila("○", "tarkistamatta", perustelu)


# (osanumero, ääni) -> Tila. Vain kohdat, joissa on tehty oikeaa työtä tai
# joissa tiedetään olevan vikaa.
POIKKEUKSET = {
    ("I", "Kuoro B"): _o(
        "Sanat korjattu lähde-PDF:ää vasten ja kahdeksan kohtaa varmistettu "
        "käsin kuulohavainnon perusteella. Nuotit ovat konelukemisen tulosta "
        "eikä niitä ole tarkistettu."),
    ("I", "Kuoro S"): _t(
        "Sanat korjattu automaattisesti lähde-PDF:ää vasten, peitto 83–91 %, "
        "mutta ei tarkistettu tavu tavulta. Nuotit konelukemisen tulosta."),
    ("II·1", "Kuoro B"): _o(
        "Nuotit vertailtu kuoron omaan tiedostoon koko 91 tahdin matkalta; "
        "yksi oktaavivirhe tahdissa 28 löytyi ja korjattiin. Sanoja ei ole "
        "erikseen tarkistettu."),
    ("II·4", "Kuoro B"): _o(
        "Nuotit vertailtu kuoron omaan tiedostoon: 174 tahtia 177:stä täsmää, "
        "ja kolme puuttunutta \"Dies irae\" -väliintuloa lisättiin. Sanoissa "
        "on ratkaisematon kohta, ks. Kuoro S."),
    ("II·4", "Kuoro S"): _p(
        "Sopraanon teksti tahdeissa 247–254 eroaa altosta, tenorista ja "
        "bassosta: sopraanolla on ylimääräisiä \"Dies irae\" -kertauksia siinä "
        "missä muut laulavat \"Solvet saeclum\" toisen kerran. Nuotit on "
        "varmistettu oikeiksi; kumpi teksti on oikea, ei ratkea ilman "
        "painettua nuottikirjaa."),
    ("II·6", "Kuoro B"): _t(
        "Yksi kuulemalla löytynyt sanavirhe korjattu tahdissa 366 "
        "(\"sal-va le\" → \"sal-va me\"). Muuten tarkistamatta."),
    ("II·9b", "Kuoro B"): _o(
        "Sanat tarkistettu lähde-PDF:ää vasten nuotti nuotilta. Nuotit ovat "
        "konelukemisen tulosta ja tarkistamatta yhtä rakenteellista "
        "pistokoetta lukuun ottamatta."),
    ("II·9b", "Kuoro S"): _t(
        "Konelukemisen tulosta. Sanoissa selvästi enemmän nuotteja ilman "
        "tavua kuin bassossa; osa on aitoja melismoja, mutta sitä ei ole "
        "tarkistettu yksitellen."),
    ("II·10", "Kuoro B"): _v(
        "Jokainen nuotti vertailtu kuoron omaan tiedostoon ja jokainen tavu "
        "painettuun lähde-PDF:ään nuottitarkkuudella. Lisäksi tahdeissa "
        "657–665 korjattiin teksti, joka on väärin myös painetussa "
        "editiossa; sen ratkaisi se, että sama aihe kantaa tekstiä "
        "\"hu-ic er-go\" tenorissa, altossa ja sopraanossa."),
    ("II·10", "Kuoro T"): _p(
        "Tekstiaukko tahdissa 688. Muuten tarkistamatta."),
    ("IV", "Kuoro B"): _t(
        "Yksi puuttunut tavu lisätty tahdeissa 99–100 (\"coe-li\"). Muuten "
        "tarkistamatta."),
    ("V", "Kuoro B"): _v(
        "Vertailtu kuoron omaan tiedostoon nuotti nuotilta koko 74 tahdin "
        "matkalta, ei yhtään eroa. 15 virhettä löytyi ja korjattiin, muun "
        "muassa neljä kokonaan tyhjää tahtia ja kaksi kohtaa joissa "
        "konelukija oli lukenut väärää viivastoa kuoron vaietessa."),
    ("V", "Kuoro S"): _p(
        "Konelukemisen tulosta ja selvästi kesken: sanapeitto 48–59 %, "
        "keksittyä sisältöä ja tyhjiä tahteja tahdeissa 59–74, ja teoksen "
        "loppusointu puuttuu kokonaan tahdista 72."),
    ("VII", "Kuoro B"): _o(
        "Nuotit vastaavat kuoron omaa tiedostoa yhtenä 67 tahdin lohkona "
        "(tahdit 44–110); ainoa poikkeama on divisi, jonka lähteet "
        "kirjoittavat eri tavoin. Muu osa ja sanat tarkistamatta."),
}

# Osat, joissa jokin ääni on ilman kuoroa, ovat samat joissa MAPPING ei
# kartoita sille ääntä. Sopraano II ja muut kuoro II:n rivit esiintyvät vain
# Sanctuksessa eivätkä kuulu tähän taulukkoon.
_TIEDOSTO = {numero: tiedosto for tiedosto, numero, _o in yhdista.MOVEMENTS}


def on_kuoroa(osanumero, aani):
    kartta = yhdista.MAPPING.get(_TIEDOSTO[osanumero], {})
    return aani in kartta


def tila(osanumero, aani):
    """Tarkistuksen tila yhdelle osalle ja äänelle."""
    if not on_kuoroa(osanumero, aani):
        return EI_KUOROA
    poikkeus = POIKKEUKSET.get((osanumero, aani))
    if poikkeus:
        return poikkeus
    # Sopraanon poikkeus koskee yleensä myös alttoa ja tenoria: samat
    # tiedostot, sama työ tekemättä.
    jaettu = POIKKEUKSET.get((osanumero, "Kuoro S"))
    if jaettu and aani in ("Kuoro A", "Kuoro T"):
        return jaettu
    return TARKISTAMATTA
```

- [ ] **Askel 4: Aja testit**

Aja: `python3 -m unittest test_luotettavuus -v`
Odotus: 5 testiä OK.

- [ ] **Askel 5: Tarkista taulukko silmällä**

```bash
python3 -c "
import luotettavuus as l, yhdista
for t, n, o in yhdista.MOVEMENTS:
    r = [l.tila(n, a).merkki for a in l.AANET]
    print(f'{n:6} {o:22} ' + '  '.join(r))
"
```
Odotus: kuusi riviä pelkkiä viivoja (solistiosat 04, 06, 08, 09, 10, 12, 15
— eli II·3, II·5, II·7, II·8, II·9, III, VI), ja `✔` vain riveillä V ja II·10
bassosarakkeessa. Jos jokin osa näyttää väärältä, korjaa `POIKKEUKSET`.

- [ ] **Askel 6: Committoi**

```bash
git add luotettavuus.py test_luotettavuus.py
git commit -F - <<'EOF'
Lisää luotettavuustaulukko: mikä on tarkistettu ja mikä ei

Ilman tätä stemmat näyttävät tasalaatuisilta eivätkä ole: vain kuorobasso on
käyty järjestelmällisesti läpi, ja osissa II·4, II·10 ja V tiedetään
sopraanossa tai tenorissa olevan virheitä.

Rakenne on oletus plus poikkeukset, jotta 68 solun taulukkoa ei tarvitse
ylläpitää käsin. Solistiosat lasketaan MAPPINGista.

Claude-Session: https://claude.ai/code/session_01Tqe8F2oYZV9mDXKdqVYdff
EOF
```

---

## Tehtävä 7: `sivusto.py` — runko, tyyli, etusivu ja luotettavuussivu

**Tiedostot:**
- Luo: `sivusto.py`, `test_sivusto.py`, `sivusto/tyyli.css`

**Rajapinta:**
- Käyttää: `luotettavuus.tila`, `luotettavuus.AANET`, `yhdista.MOVEMENTS`
- Tuottaa: `sivusto.rakenna(ulos="_sivusto")`, `sivusto.sivu(otsikko, sisalto,
  aktiivinen)` joka palauttaa täyden HTML-sivun merkkijonona. Tehtävät 8 ja 9
  lisäävät sivuja samaan runkoon.

- [ ] **Askel 1: Poimi tyylimuuttujat nykyisestä sivusta**

```bash
mkdir -p sivusto
curl -sL https://tuomasairaksinen.fi/requiem.html -o sivusto/requiem.html
sed -n '/^:root{/,/^}/p' sivusto/requiem.html
```
Odotus: `--paper:#ecebe4`, `--ink:#191512`, `--rubric:#9d1b18`,
`--serif:"EB Garamond"…`, `--sans:"Archivo"…` ja muut.

- [ ] **Askel 2: Kirjoita `sivusto/tyyli.css`**

Samat muuttujat kuin `requiem.html`:ssä, jotta sivusto näyttää yhdeltä
kokonaisuudelta. Fontit ladataan samasta paikasta.

```css
:root{
  --paper:#ecebe4; --paper-2:#e2e0d6;
  --ink:#191512; --ink-soft:rgba(25,21,18,.62);
  --rubric:#9d1b18; --rule:rgba(25,21,18,.16);
  --serif:"EB Garamond","Hoefler Text",Palatino,Georgia,serif;
  --sans:"Archivo","Helvetica Neue",Helvetica,Arial,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
     font-family:var(--sans);line-height:1.5}
.wrap{max-width:1100px;margin:0 auto;padding:0 1.25rem 6rem}
.bar{position:sticky;top:0;z-index:20;background:var(--paper);
     border-bottom:1px solid var(--rule)}
.bar-inner{max-width:1100px;margin:0 auto;padding:.5rem 1.25rem;
           display:flex;gap:1.25rem;flex-wrap:wrap;align-items:center}
.bar a{font-size:.68rem;font-weight:600;letter-spacing:.09em;
       text-transform:uppercase;text-decoration:none;color:var(--ink-soft);
       padding:.3rem .45rem}
.bar a:hover,.bar a[aria-current="page"]{color:var(--rubric)}
h1{font-family:var(--serif);font-weight:500;
   font-size:clamp(2.2rem,6vw,4rem);line-height:1;margin:0}
h2{font-family:var(--serif);font-weight:500;font-size:1.6rem;
   margin:2.5rem 0 .6rem}
table{border-collapse:collapse;width:100%;margin:1.2rem 0;font-size:.9rem}
th,td{text-align:left;padding:.45rem .6rem;
      border-bottom:1px solid var(--rule);vertical-align:top}
th{font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;
   color:var(--ink-soft);font-weight:600}
.merkki{font-size:1.05rem;text-align:center;width:2.2rem}
.perustelu{font-size:.82rem;color:var(--ink-soft)}
@media (max-width:600px){table{font-size:.8rem}}
```

- [ ] **Askel 3: Kirjoita kaatuva testi**

`test_sivusto.py`:

```python
import os
import tempfile
import unittest

import luotettavuus
import sivusto
import yhdista


class Runko(unittest.TestCase):
    def test_sivu_on_kokonainen_html(self):
        html = sivusto.sivu("Koe", "<p>sisältö</p>", "index.html")
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn("<html lang=\"fi\">", html)
        self.assertIn("tyyli.css", html)
        self.assertIn("<p>sisältö</p>", html)

    def test_aktiivinen_sivu_merkitaan(self):
        html = sivusto.sivu("Koe", "", "luotettavuus.html")
        self.assertIn('href="luotettavuus.html" aria-current="page"', html)


class Luotettavuussivu(unittest.TestCase):
    def test_jokainen_osa_on_taulukossa(self):
        html = sivusto.luotettavuussivu()
        for _t, numero, otsikko in yhdista.MOVEMENTS:
            with self.subTest(osa=numero):
                self.assertIn(otsikko, html)

    def test_kertoo_etta_vain_basso_on_varmistettu(self):
        html = sivusto.luotettavuussivu()
        self.assertIn("kuorobasso", html.lower())


class Rakennus(unittest.TestCase):
    def test_kaikki_sivut_syntyvat(self):
        with tempfile.TemporaryDirectory() as d:
            sivusto.rakenna(d)
            for nimi in ["index.html", "luotettavuus.html", "tyyli.css"]:
                with self.subTest(nimi=nimi):
                    self.assertTrue(os.path.exists(os.path.join(d, nimi)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Askel 4: Aja ja varmista että se kaatuu**

Aja: `python3 -m unittest test_sivusto -v`
Odotus: FAIL, `ModuleNotFoundError: No module named 'sivusto'`

- [ ] **Askel 5: Kirjoita `sivusto.py`**

```python
#!/usr/bin/env python3
"""Rakenna verkkosivusto stemmoista, teksteistä ja luotettavuustaulukosta.

Sivuston tiedot luetaan samoista vakioista, jotka ohjaavat stemmojen
tuotantoa, joten sisällys ei voi ajautua stemmoista erilleen.

Käyttö:  python3 sivusto.py [_sivusto]
"""

import html as _html
import os
import shutil
import sys

import luotettavuus
import polut
import yhdista

POHJA = "sivusto"

NAVI = [("index.html", "Etusivu"),
        ("teksti.html", "Teksti"),
        ("stemmat.html", "Stemmat"),
        ("luotettavuus.html", "Luotettavuus")]

FONTIT = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
          '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
          '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
          'family=EB+Garamond:ital,wght@0,400;0,500&family=Archivo:wght@400;600'
          '&display=swap">')


def e(teksti):
    return _html.escape(str(teksti))


def sivu(otsikko, sisalto, aktiivinen):
    """Kokonainen HTML-sivu yhteisellä navigaatiolla."""
    linkit = "".join(
        '<a href="%s"%s>%s</a>' % (t, ' aria-current="page"' if t == aktiivinen
                                   else "", e(nimi))
        for t, nimi in NAVI)
    return f"""<!DOCTYPE html>
<html lang="fi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(otsikko)} — Verdi: Messa da Requiem</title>
{FONTIT}
<link rel="stylesheet" href="tyyli.css">
</head>
<body>
<nav class="bar"><div class="bar-inner">{linkit}</div></nav>
<div class="wrap">
{sisalto}
</div>
</body>
</html>
"""


def luotettavuussivu():
    rivit = []
    for _tiedosto, numero, otsikko in yhdista.MOVEMENTS:
        solut = []
        for aani in luotettavuus.AANET:
            t = luotettavuus.tila(numero, aani)
            solut.append('<td class="merkki" title="%s">%s</td>'
                         % (e(t.nimi), t.merkki))
        perustelut = [luotettavuus.tila(numero, a) for a in luotettavuus.AANET]
        huomiot = sorted({t.perustelu for t in perustelut
                          if t.nimi not in ("tarkistamatta", "ei kuoroa")})
        rivit.append(
            "<tr><td><strong>%s</strong> %s</td>%s</tr>" %
            (e(numero), e(otsikko), "".join(solut)))
        if huomiot:
            rivit.append('<tr><td colspan="5" class="perustelu">%s</td></tr>'
                         % e(" ".join(huomiot)))

    otsikot = "".join('<th class="merkki">%s</th>' % a.replace("Kuoro ", "")
                      for a in luotettavuus.AANET)
    sisalto = f"""
<h1>Luotettavuus</h1>
<p>Vain <strong>kuorobasso</strong> on käyty järjestelmällisesti läpi.
Sopraano, altto ja tenori ovat pääosin tarkistamatta, ja kahdessa osassa
niissä on tiedettyjä virheitä. Syy on yksinkertainen: tekijä laulaa bassoa,
ja jokainen virhe on löytynyt joko laulamalla mukana tai vertaamalla sitä
riviä riippumattomaan lähteeseen.</p>
<table>
<thead><tr><th>Osa</th>{otsikot}</tr></thead>
<tbody>{''.join(rivit)}</tbody>
</table>
<p class="perustelu">✔ varmistettu · ◑ osittain · ○ tarkistamatta ·
⚠ puutteita · – ei kuoroa</p>
"""
    return sivu("Luotettavuus", sisalto, "luotettavuus.html")


def etusivu():
    sisalto = """
<h1>Messa da Requiem</h1>
<p>Verdin <em>Messa da Requiem</em> kuusitoista osatiedostoa yhdistettynä
yhdeksi partituuriksi, ja siitä tuotetut kahdeksan kuorostemmaa.</p>
<h2>Mistä aloittaa</h2>
<ul>
<li><a href="stemmat.html">Stemmat</a> — kahdeksan ääntä, tahtinumero joka
tahdin päällä</li>
<li><a href="teksti.html">Teksti</a> — latina ja suomi rinnakkain</li>
<li><a href="luotettavuus.html">Luotettavuus</a> — mikä on tarkistettu ja
mikä ei</li>
</ul>
"""
    return sivu("Etusivu", sisalto, "index.html")


def rakenna(ulos="_sivusto"):
    os.makedirs(ulos, exist_ok=True)
    shutil.copy(os.path.join(POHJA, "tyyli.css"), ulos)
    open(os.path.join(ulos, "index.html"), "w").write(etusivu())
    open(os.path.join(ulos, "luotettavuus.html"), "w").write(
        luotettavuussivu())
    return ulos


def main(argv):
    ulos = argv[0] if argv else "_sivusto"
    rakenna(ulos)
    print(f"kirjoitettu {ulos}/")


if __name__ == "__main__":
    main(sys.argv[1:])
```

- [ ] **Askel 6: Aja testit**

Aja: `python3 -m unittest test_sivusto -v`
Odotus: 5 testiä OK.

- [ ] **Askel 7: Katso sivu selaimessa**

```bash
python3 sivusto.py && open _sivusto/luotettavuus.html
```
Odotus: taulukko, jossa on 17 riviä, ✔-merkkejä kaksi bassosarakkeessa.

- [ ] **Askel 8: Committoi**

```bash
git add sivusto.py test_sivusto.py sivusto/tyyli.css
git commit -F - <<'EOF'
Lisää sivustogeneraattori, etusivu ja luotettavuussivu

Sivuston tiedot luetaan yhdista.py:n omista vakioista, joten sisällys ei voi
ajautua stemmoista erilleen. Ulkoasu käyttää samoja väri- ja
typografiamuuttujia kuin olemassa oleva latina-suomi-sivu.

Claude-Session: https://claude.ai/code/session_01Tqe8F2oYZV9mDXKdqVYdff
EOF
```

---

## Tehtävä 8: Stemmasivu

**Tiedostot:**
- Muokkaa: `sivusto.py`, `test_sivusto.py`

**Rajapinta:**
- Käyttää: `sivusto.sivu` tehtävästä 7, `polut.polku`
- Tuottaa: `sivusto.stemmasivu()`, `sivusto.lue_sisallys()`,
  `sivusto.tahtivalit()`

- [ ] **Askel 1: Kirjoita kaatuva testi**

Lisää `test_sivusto.py`:hyn:

```python
class Stemmasivu(unittest.TestCase):
    def test_sisallys_luetaan_tiedostosta(self):
        rivit = sivusto.lue_sisallys()
        self.assertIn("Agnus Dei", " ".join(r[1] for r in rivit))
        # Kahdeksan stemmaa, joten kahdeksan sivunumeroa riviä kohti.
        for _numero, _otsikko, sivut in rivit:
            self.assertEqual(len(sivut), 8)

    def test_sisallys_kattaa_kaikki_osat(self):
        rivit = sivusto.lue_sisallys()
        self.assertEqual(len(rivit), len(yhdista.MOVEMENTS))

    def test_tahtivalit_luetaan_partituurista(self):
        valit = sivusto.tahtivalit()
        # Dies irae numeroituu jatkuvasti; Lacrymosa päättyy tahtiin 701.
        self.assertEqual(valit["II·10"][1], 701)
        # Muut osat alkavat ykkösestä.
        self.assertEqual(valit["IV"][0], 1)

    def test_sivulla_on_latauslinkki_jokaiselle_stemmalle(self):
        html = sivusto.stemmasivu()
        for tiedosto in ["stemma-basso-1.pdf", "stemma-sopraano-2.pdf"]:
            with self.subTest(tiedosto=tiedosto):
                self.assertIn(tiedosto, html)
```

- [ ] **Askel 2: Aja ja varmista että se kaatuu**

Aja: `python3 -m unittest test_sivusto.Stemmasivu -v`
Odotus: FAIL, `AttributeError: module 'sivusto' has no attribute
'lue_sisallys'`

- [ ] **Askel 3: Toteuta `sivusto.py`:hyn**

```python
import re
import zipfile
import xml.etree.ElementTree as ET

STEMMAT = [("S I", "stemma-sopraano-1.pdf"), ("S II", "stemma-sopraano-2.pdf"),
           ("A I", "stemma-altto-1.pdf"), ("A II", "stemma-altto-2.pdf"),
           ("T I", "stemma-tenori-1.pdf"), ("T II", "stemma-tenori-2.pdf"),
           ("B I", "stemma-basso-1.pdf"), ("B II", "stemma-basso-2.pdf")]


def lue_sisallys():
    """(osanumero, otsikko, [8 sivunumeroa]) stemmat-sisallys.txt:stä.

    Tiedosto on sarakemuotoinen ja osanumero voi olla kiinni otsikossa
    ("II·9bDies irae"), joten rivi puretaan tunnettuja osanumeroita vasten
    eikä välilyönneillä.
    """
    numerot = [(numero, otsikko) for _t, numero, otsikko in yhdista.MOVEMENTS]
    rivit = []
    with open(polut.polku("stemmat-sisallys.txt"), encoding="utf-8") as f:
        teksti = f.read()
    for numero, otsikko in numerot:
        # Rivi alkaa osanumerolla ja päättyy kahdeksaan lukuun.
        kuvio = re.compile(r"^\s*%s\s*%s\s+((?:\d+\s+){7}\d+)\s*$"
                           % (re.escape(numero), re.escape(otsikko)),
                           re.MULTILINE)
        osuma = kuvio.search(teksti)
        if not osuma:
            raise SystemExit(
                f"stemmat-sisallys.txt: riviä osalle {numero} {otsikko} ei "
                f"löydy — aja python3 sisallys.py uudelleen")
        rivit.append((numero, otsikko, [int(x) for x in osuma.group(1).split()]))
    return rivit


def tahtivalit():
    """Osanumero -> (ensimmäinen, viimeinen) tahtinumero.

    Luetaan yhdistetyn partituurin omista <measure number> -arvoista eikä
    siitä taulukosta joka ne asetti — sama tarkistustapa kuin muualla.
    """
    with zipfile.ZipFile(polut.polku("Verdi-Requiem-koko.mxl")) as z:
        nimi = next(n for n in z.namelist()
                    if not n.startswith("META-INF") and n.lower().endswith(".xml"))
        juuri = ET.fromstring(z.read(nimi))
    osa = juuri.find("part")
    valit, nykyinen = {}, None
    otsikot = {yhdista.osaotsikko(n, o): n for _t, n, o in yhdista.MOVEMENTS}
    for tahti in osa.findall("measure"):
        for sanat in tahti.iter("words"):
            nimi = (sanat.text or "").strip()
            if nimi in otsikot:
                nykyinen = otsikot[nimi]
        if nykyinen is None:
            continue
        numero = int(tahti.get("number"))
        alku, loppu = valit.get(nykyinen, (numero, numero))
        valit[nykyinen] = (min(alku, numero), max(loppu, numero))
    return valit


def stemmasivu():
    sisallys = lue_sisallys()
    valit = tahtivalit()
    otsikot = "".join("<th>%s</th>" % e(nimi) for nimi, _pdf in STEMMAT)
    rivit = []
    for numero, otsikko, sivut in sisallys:
        alku, loppu = valit.get(numero, ("", ""))
        rivit.append(
            "<tr><td><strong>%s</strong> %s</td><td>%s–%s</td>%s</tr>"
            % (e(numero), e(otsikko), e(alku), e(loppu),
               "".join("<td>%d</td>" % s for s in sivut)))
    linkit = "".join(
        '<li><a href="stemmat/%s">%s</a></li>' % (pdf, e(nimi))
        for nimi, pdf in STEMMAT)
    sisalto = f"""
<h1>Stemmat</h1>
<p>Kahdeksan kuorostemmaa. Jokaisen tahdin päällä on tahtinumero ja jokaisen
sivun yläreunassa käynnissä olevan osan nimi, jotta yksittäisen tahdin
löytää kuoronjohtajan huudosta.</p>
<ul class="lataukset">{linkit}</ul>
<h2>Mistä osa alkaa</h2>
<p>Tahtinumerot ovat kuoron oman nuottikirjan mukaiset. Dies irae (osa II)
numeroituu yhtenäisesti 1–701; muut osat alkavat ykkösestä.</p>
<table>
<thead><tr><th>Osa</th><th>Tahdit</th>{otsikot}</tr></thead>
<tbody>{''.join(rivit)}</tbody>
</table>
"""
    return sivu("Stemmat", sisalto, "stemmat.html")
```

Lisää `rakenna()`:an:
```python
    open(os.path.join(ulos, "stemmat.html"), "w").write(stemmasivu())
    kohde = os.path.join(ulos, "stemmat")
    os.makedirs(kohde, exist_ok=True)
    for _nimi, pdf in STEMMAT:
        shutil.copy(polut.polku(pdf), kohde)
```

- [ ] **Askel 4: Aja testit**

Aja: `python3 -m unittest test_sivusto -v`
Odotus: 9 testiä OK. Jos `tahtivalit` palauttaa tyhjän, tarkista miten
osaotsikko on kirjoitettu partituuriin:
`python3 -c "import yhdista; print(yhdista.OSAOTSIKOT[:3])"`

- [ ] **Askel 5: Katso sivu selaimessa**

```bash
python3 sivusto.py && open _sivusto/stemmat.html
```
Odotus: taulukko, jossa Lacrymosan tahtiväli on 624–701 ja B I:n sivumäärät
vastaavat `stemmat/stemmat-sisallys.txt`:ää.

- [ ] **Askel 6: Committoi**

```bash
git add sivusto.py test_sivusto.py
git commit -F - <<'EOF'
Lisää stemmasivu tahtiväleineen

Tahtivälit luetaan yhdistetyn partituurin omista measure number -arvoista
eikä siitä taulukosta joka ne asetti, samalla tavalla kuin muutkin tämän
projektin tarkistukset.

Claude-Session: https://claude.ai/code/session_01Tqe8F2oYZV9mDXKdqVYdff
EOF
```

---

## Tehtävä 9: Tekstisivu

**Tiedostot:**
- Muokkaa: `sivusto.py`, `test_sivusto.py`, `sivusto/requiem.html`

**Rajapinta:**
- Tuottaa: `sivusto.tekstisivu()`

`requiem.html` on itsenäinen ja toimiva sivu. Sitä **ei refaktoroida**:
siihen lisätään vain navigaatiopalkki, ja se kopioidaan
`_sivusto/teksti.html`:ksi.

- [ ] **Askel 1: Kirjoita kaatuva testi**

```python
class Tekstisivu(unittest.TestCase):
    def test_navigaatio_on_lisatty(self):
        html = sivusto.tekstisivu()
        self.assertIn('href="stemmat.html"', html)

    def test_alkuperainen_sisalto_sailyy(self):
        html = sivusto.tekstisivu()
        alkuperainen = open("sivusto/requiem.html", encoding="utf-8").read()
        # Jokainen osa on yhä sivulla.
        for tunnus in ['id="i"', 'id="ii"', 'id="vii"']:
            with self.subTest(tunnus=tunnus):
                self.assertIn(tunnus, alkuperainen)
                self.assertIn(tunnus, html)
        # Sivun oma tyyli on koskematon.
        self.assertIn("--rubric:#9d1b18", html)
```

- [ ] **Askel 2: Aja ja varmista että se kaatuu**

Aja: `python3 -m unittest test_sivusto.Tekstisivu -v`
Odotus: FAIL, `AttributeError: … has no attribute 'tekstisivu'`

- [ ] **Askel 3: Toteuta**

```python
def tekstisivu():
    """requiem.html sellaisenaan, navigaatio lisättynä.

    Sivu on itsenäinen ja toimiva; siihen ei kosketa muuten. Navigaatio
    pujotetaan heti <body>:n jälkeen ja se saa oman tyylinsä mukaan, koska
    sivu ei lataa jaettua tyyliä.
    """
    with open(os.path.join(POHJA, "requiem.html"), encoding="utf-8") as f:
        html = f.read()
    linkit = "".join('<a href="%s">%s</a>' % (t, e(nimi))
                     for t, nimi in NAVI if t != "teksti.html")
    navi = ('<nav class="bar" style="position:static"><div class="bar-inner">'
            '<div class="jump">%s</div></div></nav>' % linkit)
    if "<body>" not in html:
        raise SystemExit("sivusto/requiem.html: <body>-tagia ei löydy")
    return html.replace("<body>", "<body>\n" + navi, 1)
```

Lisää `rakenna()`:an:
```python
    open(os.path.join(ulos, "teksti.html"), "w").write(tekstisivu())
```
ja `test_sivusto.Rakennus`-testin listaan `"teksti.html"`.

- [ ] **Askel 4: Aja testit**

Aja: `python3 -m unittest discover -p 'test_*.py'`
Odotus: noin 160 testiä, kaikki läpi.

- [ ] **Askel 5: Katso sivusto selaimessa**

```bash
python3 sivusto.py && open _sivusto/index.html
```
Odotus: navigaatio toimii kaikilla neljällä sivulla, tekstisivu näyttää
samalta kuin ennen mutta navigaatio päällä.

- [ ] **Askel 6: Committoi**

```bash
git add sivusto.py test_sivusto.py sivusto/requiem.html
git commit -F - <<'EOF'
Lisää latina-suomi-tekstisivu osaksi sivustoa

requiem.html tulee mukaan sellaisenaan; siihen lisätään vain navigaatio.
Toimivaa sivua ei refaktoroida jaetun tyylin päälle.

Claude-Session: https://claude.ai/code/session_01Tqe8F2oYZV9mDXKdqVYdff
EOF
```

---

## Tehtävä 10: Stemmojen pikkukuvat (valinnainen)

**Tiedostot:**
- Muokkaa: `sivusto.py`
- Luo: `sivusto/pikkukuvat/*.png`

Tämä on koristeellinen ja ensimmäinen karsittava, jos se hidastaa. CI:ssä ei
ole `mutool`ia, joten kuvat tehdään paikallisesti ja committoidaan.

- [ ] **Askel 1: Tee kuvat**

```bash
mkdir -p sivusto/pikkukuvat
for f in stemmat/stemma-*.pdf; do
  n=$(basename "$f" .pdf)
  mutool draw -r 40 -o "sivusto/pikkukuvat/$n.png" "$f" 1
done
ls -la sivusto/pikkukuvat/ | head
du -sh sivusto/pikkukuvat/
```
Odotus: kahdeksan PNG:tä, yhteensä alle 500 kB. Jos yli, laske `-r 40` →
`-r 30`.

- [ ] **Askel 2: Lisää ne stemmasivulle**

Korvaa `stemmasivu()`:n `linkit`-muuttuja:
```python
    linkit = "".join(
        '<li><a href="stemmat/%s"><img src="pikkukuvat/%s.png" alt="" '
        'width="120" loading="lazy"><span>%s</span></a></li>'
        % (pdf, pdf[:-4], e(nimi))
        for nimi, pdf in STEMMAT)
```
ja `rakenna()`:an kuvien kopiointi:
```python
    shutil.copytree(os.path.join(POHJA, "pikkukuvat"),
                    os.path.join(ulos, "pikkukuvat"), dirs_exist_ok=True)
```
sekä `tyyli.css`:ään:
```css
.lataukset{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:1.2rem}
.lataukset a{display:block;text-decoration:none;color:var(--ink);
             font-size:.75rem;text-align:center}
.lataukset img{display:block;border:1px solid var(--rule);background:#fff;
               margin-bottom:.4rem}
```

- [ ] **Askel 3: Tarkista ja committoi**

```bash
python3 sivusto.py && open _sivusto/stemmat.html
python3 -m unittest discover -p 'test_*.py'
git add sivusto.py sivusto/pikkukuvat sivusto/tyyli.css
git commit -F - <<'EOF'
Lisää stemmojen kansikuvat sivustolle

Kuvat tehdään paikallisesti mutoolilla, koska CI:ssä ei ole sitä eikä
MuseScorea.

Claude-Session: https://claude.ai/code/session_01Tqe8F2oYZV9mDXKdqVYdff
EOF
```

---

## Tehtävä 11: GitHub Actions -työnkulku

**Tiedostot:**
- Luo: `.github/workflows/sivusto.yml`

- [ ] **Askel 1: Kirjoita työnkulku**

```yaml
name: Julkaise sivusto

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  rakenna:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Aja testit
        # Sivuston testit eivät tarvitse MuseScorea; ne, jotka tarvitsevat,
        # ohittavat itsensä.
        run: python3 -m unittest discover -p 'test_*.py'
      - name: Rakenna sivusto
        run: python3 sivusto.py _sivusto
      - uses: actions/upload-pages-artifact@v3
        with:
          path: _sivusto

  julkaise:
    needs: rakenna
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Askel 2: Varmista että testit menevät läpi ilman MuseScorea**

```bash
which mscore && echo "paikallisesti on; CI:ssä ei"
python3 - <<'EOF'
import subprocess, sys
# Aja testit ympäristössä, josta mscore puuttuu.
import os
ymp = dict(os.environ, PATH="/usr/bin:/bin")
r = subprocess.run([sys.executable, "-m", "unittest", "discover",
                    "-p", "test_*.py"], env=ymp,
                   capture_output=True, text=True)
print(r.stderr[-3000:])
sys.exit(r.returncode)
EOF
```
Odotus: kaikki läpi. Jos jokin testi vaatii `mscore`a, lisää sille
`@unittest.skipUnless(shutil.which("mscore"), "vaatii MuseScoren")`.

- [ ] **Askel 3: Committoi**

```bash
git add .github/workflows/sivusto.yml
git commit -F - <<'EOF'
Lisää GitHub Pages -julkaisu

Sivusto rakennetaan CI:ssä eikä committoida, jotta se ei voi vanhentua
huomaamatta. PDF:t tulevat reposta sellaisinaan, koska niitä ei voi rakentaa
ilman MuseScorea.

Claude-Session: https://claude.ai/code/session_01Tqe8F2oYZV9mDXKdqVYdff
EOF
```

---

## Tehtävä 12: Historian uudelleenkirjoitus

**Tiedostot:** ei lähdekoodimuutoksia.

Tämä on tehtävistä ainoa peruuttamaton. **Varmuuskopio ensin.**

- [ ] **Askel 1: Ota täysi varmuuskopio**

```bash
cd /Users/tuomasairaksinen
cp -a verdi-requiem "$SCRATCH/verdi-requiem-varmuuskopio"
du -sh "$SCRATCH/verdi-requiem-varmuuskopio"
```
Odotus: noin 160 MB. **Älä jatka ennen kuin tämä on onnistunut.**

- [ ] **Askel 2: Asenna työkalu ja kirjaa lähtökoko**

```bash
brew install git-filter-repo
cd /Users/tuomasairaksinen/verdi-requiem
du -sh .git
git rev-list --count HEAD
```
Odotus: 124 MB, 47 + uudet commitit.

- [ ] **Askel 3: Aja poistot**

```bash
git filter-repo --invert-paths \
  --path musescore/ \
  --path-glob 'harjoitus-*.mscz' \
  --path-glob 'harjoitus/harjoitus-*.mscz' \
  --path Verdi-Requiem-koko-oma.mscz \
  --force
```

- [ ] **Askel 4: Tarkista että poisto onnistui**

```bash
git log --all --oneline | wc -l
git rev-list --objects --all | grep -ci musescore || echo "musescore: 0 osumaa"
git rev-list --objects --all | grep -c "harjoitus-.*\.mscz" || echo "mscz: 0"
git gc --prune=now --aggressive
du -sh .git
```
Odotus: `musescore: 0 osumaa`, `mscz: 0`, ja `.git` selvästi pienempi.
Jos se on yli 60 MB, syy on stemma-PDF:ien vanhoissa versioissa — kirjaa
luku ja kysy käyttäjältä ennen kuin karsit lisää.

- [ ] **Askel 5: Tarkista että työpuu on ehjä**

```bash
git status --short
python3 -m unittest discover -p 'test_*.py'
ls lahteet | wc -l; ls johdetut | wc -l; ls stemmat | wc -l
```
Odotus: työpuu siisti, kaikki testit läpi, hakemistot ennallaan.

---

## Tehtävä 13: Julkaisu

- [ ] **Askel 1: Luo repo ja työnnä**

```bash
gh repo create tuomas2/verdi-requiem --public \
  --description "Verdin Messa da Requiem: kuorostemmat ja yhdistetty partituuri" \
  --source=. --remote=origin
git push -u origin main
```

- [ ] **Askel 2: Kytke Pages päälle**

```bash
gh api -X POST repos/tuomas2/verdi-requiem/pages \
  -f 'build_type=workflow' || \
  echo "Kytke käsin: Settings > Pages > Source: GitHub Actions"
gh run list --limit 3
```

- [ ] **Askel 3: Tarkista julkaistu sivusto**

```bash
gh run watch
curl -sI https://tuomas2.github.io/verdi-requiem/ | head -1
curl -s https://tuomas2.github.io/verdi-requiem/luotettavuus.html | \
  grep -c "kuorobasso"
curl -sI https://tuomas2.github.io/verdi-requiem/stemmat/stemma-basso-1.pdf | \
  head -1
```
Odotus: `HTTP/2 200` kaikkiin, ja luotettavuussivulta löytyy maininta.

- [ ] **Askel 4: Tarkista ettei mitään ei-toivottua päätynyt julkiseksi**

```bash
gh api repos/tuomas2/verdi-requiem/git/trees/main?recursive=1 \
  --jq '.tree[].path' | grep -i "musescore\|mscz\|Lasse" || \
  echo "puhdas: ei musescore-jälkiä"
```
Odotus: `puhdas: ei musescore-jälkiä`. Poikkeus: `lahteet/`-hakemiston kolme
CPDL:n `.mscz`-tiedostoa (02, 03, 16) ovat sallittuja ja saavat näkyä.

---

## Itsetarkistus

**Spekin kattavuus.** Jokainen spekin luku vastaa tehtävää: luku 3
(rakenne) → tehtävä 3; luku 4 (polut) → tehtävät 1 ja 3; luku 5
(luotettavuus) → tehtävä 6; luku 6 (sivusto) → tehtävät 7–11; luku 7
(README/LICENSE) → tehtävä 5; luku 8 (historia) → tehtävä 12; luku 9
(testaus) → sisältyy jokaiseen. Spekin luku 10 (järjestys) toteutuu
tehtävien numeroinnissa.

**Nimien yhtenäisyys.** `polut.polku` ja `polut.hakemisto` (tehtävä 1)
esiintyvät samannimisinä tehtävissä 3, 7 ja 8. `luotettavuus.tila`,
`luotettavuus.AANET` ja `luotettavuus.POIKKEUKSET` (tehtävä 6) esiintyvät
samannimisinä tehtävissä 6 ja 7. `sivusto.sivu`, `sivusto.rakenna`,
`sivusto.STEMMAT` ja `sivusto.e` (tehtävä 7) esiintyvät samannimisinä
tehtävissä 8, 9 ja 10.

**Yksi tunnettu riippuvuus tehtävien välillä:** tehtävä 8 lukee
`stemmat-sisallys.txt`:ää ja `Verdi-Requiem-koko.mxl`:ää, joten tehtävän 3
on oltava valmis ensin. Tehtävä 10 riippuu tehtävästä 8.
