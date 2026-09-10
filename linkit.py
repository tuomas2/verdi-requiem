#!/usr/bin/env python3
"""Klikattava sisällysluettelo stemman ensimmäiselle sivulle.

**Mitä laulaja pyysi.** Lukulaitteella pitää pystyä hyppäämään siihen osaan,
jota kuoro juuri harjoittelee, eikä selaamalla kuutta sivua. Luettelo ei saa
viedä omaa sivuaan, mutta tilaa se saa ottaa noin puoli sivua.

Työ on kahdessa päässä, ja järjestys on pakollinen:

1. **`--varaa`** ennen renderöintiä. Luettelo tarvitsee tyhjää tilaa sivun 1
   yläosasta, ja sen voi tehdä vain MuseScore taittaessaan sivun. Tila
   varataan valkoisella tekstillä ensimmäisen tahdin yläpuolelle: se ei näy,
   mutta MuseScore laskee sen korkeuden taittoon ja työntää ensimmäisen
   viivaston alaspäin.
2. **`lisaa`** renderöinnin jälkeen (ajaa `sisallys.py`). Se mittaa sivulta,
   mihin tyhjä tila jäi, latoo luettelon sinne ja lisää linkit.

**Mitä mitattiin ja mikä hylättiin.** MusicXML:n oma
`<print><system-layout><top-system-distance>` on juuri tätä varten, mutta
**MuseScore 4.7.4 ei välitä siitä lainkaan** — arvot 200 ja 400 antoivat
molemmat tismalleen saman taiton kuin ilman. Sama koski tyhjiä rivejä
(`"\\n"` × 10) ja välilyöntiä 100 pt:n fontilla: pelkkä tyhjä merkki ei vie
korkeutta. Tilaa varaa vain **oikeaa tekstiä sisältävä rivi**, ja siksi
varaus on rivejä, joilla on piste. Väri `#FFFFFF` tekee siitä näkymättömän.
Mitattu 9 pt:n rivi työntää viivastoa **noin 10,5 pt**; tarkka arvo ei ole
tärkeä, koska `lisaa` mittaa tuloksen sivulta eikä luota laskuun — ja jos
tila ei riitä, se kaatuu ja kertoo, että `--varaa` on ajamatta.

Varaus tulee osan otsikon (`I  Requiem & Kyrie`) **jälkeen** tahdin
alkioissa. Se on mitattu: ennen otsikkoa lisätty varaus jättää otsikon
sivun ylälaitaan kaksisataa pistettä irti omasta viivastostaan.

**Sivumäärä ei kasvanut.** Mitattu basso I:llä: 10, 20, 24 ja 28 varausriviä
antavat kaikki 16 sivua, koska `tiivistys.mss`:n `minSystemSpread` on
vähimmäisväli ja loput sivun tilasta jaetaan tasan — sivulta 1 jää pois
kaksi riviä, jotka mahtuvat muiden sivujen väljyyteen.

Luettelo lisätään PDF:ään kolmena asiana:

* **teksti** omana sisältövirtanaan sivulle 1 (upotettu Times-Roman, ei
  nuottifonttia — Edwin on Type0/Identity-H, jonka glyfitunnuksia ei saa
  käsin kirjoitettuun virtaan järkevästi),
* **linkkiannotaatio** joka rivin päälle koko rivin levyisenä (`/GoTo`
  kyseiselle sivulle), jotta sitä osuu sormella,
* **PDF:n kirjanmerkit** (`/Outlines`) samoista osista. Ne eivät vie sivulta
  tilaa lainkaan ja lukuohjelmat näyttävät ne omana sisällysvalikkonaan.

**Idempotenssi.** Sekä varaus että lisäys tunnistavat oman jälkensä
merkinnästä eivätkä paikasta: varauksen `<credit-words id="sisallysvaraus">`
-tyylinen tunniste ja PDF-olioiden avain `/VerdiSisallys`. Uudelleenajo
poistaa vanhan ensin, joten se tuottaa saman tuloksen.

Se on myös pakollista: luettelo sisältää **kaikkien** osien nimet sivulla 1,
joten `sisallys.py`:n sivuhaku löytäisi jokaisen osan sivulta 1, jos vanhaa
luetteloa ei riisuttaisi ennen tekstin lukemista. Sen tekee `sisallys.py`.

Käyttö yhdelle stemmalle (`sisallys.py` tekee jälkipuolen kaikille
kahdeksalle):

    python3 linkit.py --varaa stemma-basso-1.mxl   # ennen mscorea
    python3 linkit.py stemma-basso-1.pdf           # renderöinnin jälkeen
    python3 linkit.py --riisu stemma-basso-1.pdf   # pelkkä poisto
    python3 linkit.py --lue stemma-basso-1.pdf     # mitä PDF:ssä lukee
"""

import json
import math
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import polut
import rajaa
from korjaa_sanat import load, save

# Oma avain jokaisessa PDF:ään lisätyssä oliossa ja oma tunniste varauksen
# tekstissä. Poisto etsii nämä eikä arvaa paikasta, joten se ei voi viedä
# mukanaan MuseScoren omaa sisältöä.
MERKKI = "VerdiSisallys"
FONTTIAVAIN = "FSis"
VARAUS_TUNNISTE = "sisallysvaraus"

FONTTI = "Times-Roman"
OTSIKKO = "Sisällys"
OTSIKKO_KOKO = 11.0
KOKO = 9.5              # luettelorivin teksti
RIVI = 14.0             # luettelorivin korkeus, myös linkin korkeus
LEVEYS = 330.0          # luettelon leveys; kapeampi jos tila ei riitä
SARAKEVALI = 18.0
TAYTE = " ."            # täytepisteet nimen ja sivunumeron väliin
RESERVI = 4.0           # piste tyhjän kaistan reunoihin

# Varaus: valkoisen tekstin rivikoko, ja mitattu paljonko yksi sen rivi
# työntää ensimmäistä viivastoa alaspäin.
VARAUS_KOKO = "9"
VARAUS_RIVI = 10.5
VARAUS_LISA = 1         # riviä väljyyttä, ks. varauksen_rivit

DPI = 72                # 1 pikseli = 1 piste, joten mittaus on pisteitä
MUSTE = 200             # tätä tummempi pikseli on mustetta (0-255)
VIIVASTO = 0.6          # rivi, jonka muste ulottuu tämän osan yli sivun
                        # leveydestä, on ensimmäinen viivastoviiva

# Fontin mitat kysytään mupdf:ltä kerran; ne eivät riipu PDF:stä.
_mitat = {}


# --------------------------------------------------------------- mutool run

def aja_js(lahde, *argumentit):
    """Aja mupdf-JS ja palauta sen tuloste. Virhe kaataa selkeästi."""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(lahde)
        nimi = f.name
    try:
        ajo = subprocess.run(["mutool", "run", nimi, *argumentit],
                             capture_output=True, text=True)
    finally:
        os.unlink(nimi)
    if ajo.returncode != 0 or "Error:" in ajo.stderr:
        raise SystemExit("mutool run epäonnistui:\n" + ajo.stderr.strip())
    return ajo.stdout


def mitat():
    """Merkin etenemä em-yksikköinä (1.0 = fonttikoko), välimuistista."""
    if not _mitat:
        merkit = [chr(c) for c in range(32, 127)] + ["·", "ä", "ö", "å", "é"]
        js = ("var f = new Font(%s);\n"
              "var out = {};\n"
              "var m = %s;\n"
              "for (var i = 0; i < m.length; i++)\n"
              "    out[m[i]] = f.advanceGlyph(f.encodeCharacter("
              "m[i].charCodeAt(0)));\n"
              "print(JSON.stringify(out));\n"
              % (json.dumps(FONTTI), json.dumps(merkit)))
        _mitat.update(json.loads(aja_js(js)))
    return _mitat


def leveys(teksti, koko):
    m = mitat()
    return sum(m[c] for c in teksti) * koko


# ------------------------------------------------------- varaus (ennen mscorea)

def varauksen_rivit(maara):
    """Montako valkoista riviä tarvitaan, kun luettelossa on `maara` osaa.

    `VARAUS_LISA` on se osa varatusta tilasta, jota luettelo ei saa
    käyttöönsä: säveltäjän nimi jää kaistan sisään ja katkaisee sen, joten
    ylin pala menee hukkaan. Loppu on väljyyttä nuottiin päin — ja jos
    lasku menee silti pieleen, `lisaa` mittaa sen sivulta ja kaatuu.
    """
    return int(math.ceil(korkeus(maara) / VARAUS_RIVI)) + VARAUS_LISA


def riisu_varaus(root):
    """Poista aiempi varaus puusta. Palauta True jos jotain poistettiin."""
    poistettu = False
    for measure in root.iter("measure"):
        for d in list(measure.findall("direction")):
            if any((w.get("id") or "") == VARAUS_TUNNISTE
                   for w in d.iter("words")):
                measure.remove(d)
                poistettu = True
    return poistettu


def varaus_direction(rivit):
    """Näkymätön teksti, jonka korkeus on se tila jonka luettelo saa."""
    d = ET.Element("direction", {"placement": "above"})
    dt = ET.SubElement(d, "direction-type")
    w = ET.SubElement(dt, "words", {"id": VARAUS_TUNNISTE,
                                    "font-size": VARAUS_KOKO,
                                    "color": "#FFFFFF"})
    # Pelkkä tyhjä ei vie korkeutta — piste vie. Ks. moduulin ohje.
    w.text = "\n".join(["."] * rivit)
    return d


def varaa(mxl, maara=None, rivit=None):
    """Varaa sivun 1 yläosasta tila luettelolle. Ajetaan ennen `mscore`a.

    Varaus tulee ensimmäisen tahdin **viimeisen** directionin jälkeen, jotta
    osan otsikko jää viivastonsa viereen eikä sivun ylälaitaan.
    """
    rivit = rivit if rivit is not None else varauksen_rivit(maara or 0)
    root = load(mxl)
    riisu_varaus(root)
    measure = root.find("part/measure")
    if measure is None:
        raise SystemExit("%s: ensimmäistä tahtia ei löydy" % mxl)
    lapset = list(measure)
    kohta = max([i for i, e in enumerate(lapset)
                 if e.tag == "direction"] or [-1]) + 1
    measure.insert(kohta, varaus_direction(rivit))
    save(root, mxl, mxl)
    print("  %s: varattu %d riviä (~%d pt) sisällysluettelolle"
          % (mxl, rivit, rivit * VARAUS_RIVI))
    return rivit


# ------------------------------------------------------------------ mittaus

def musterivit(pdf, sivu=1):
    """Sivun jokaisen pisterivin musteen (vasen, oikea) reuna, tai None.

    Rasterointi on ainoa mittaus, joka näkee sekä tekstin että viivat:
    `mutool draw -F stext` kertoo tekstin laatikot mutta ei viivastoa,
    eikä nuotin yläreuna ole tekstiä. Se ei myöskään näe varauksen
    valkoista tekstiä, mikä on juuri oikein: sen tila on vapaata.
    """
    raaka = subprocess.run(
        ["mutool", "draw", "-r", str(DPI), "-F", "ppm", "-o", "-",
         polut.polku(pdf), str(sivu)], capture_output=True, check=True).stdout
    lev, kork, pikselit = rajaa.lue_ppm(raaka)
    rivit = []
    for y in range(kork):
        alku = y * lev * 3
        rivi = pikselit[alku:alku + lev * 3:3]      # punainen kanava riittää
        x0 = x1 = None
        for x, arvo in enumerate(rivi):
            if arvo < MUSTE:
                x0 = x if x0 is None else x0
                x1 = x
        rivit.append(None if x0 is None else (float(x0), float(x1 + 1)))
    return rivit, float(lev), float(kork)


def tila(rivit, leveys_sivu):
    """Sivun 1 yläosan tyhjä kaista: (vasen, oikea, ylin y, alin y).

    Ylin on otsikkolohkon alareuna: sivun ylin musteryhmä on päiväys ja
    otsikko samoilla riveillä. Alin on ensimmäisen viivastoviivan yläpuoli
    — viivasto on ainoa, jonka muste ulottuu yli sivun leveydestä. y kasvaa
    alaspäin, kuten `mutool draw -F stext`:ssä.
    """
    vasemmat = [r[0] for r in rivit if r]
    oikeat = [r[1] for r in rivit if r]
    if not vasemmat:
        raise SystemExit("sivu 1 on tyhjä — ei mitään mihin sisällys suhteutuu")
    vasen, oikea = min(vasemmat), max(oikeat)

    y = next(i for i, r in enumerate(rivit) if r)        # otsikkolohkon alku
    while y < len(rivit) and rivit[y]:                   # ja sen loppu
        y += 1
    for i in range(y, len(rivit)):
        r = rivit[i]
        if r and r[1] - r[0] > VIIVASTO * leveys_sivu:
            return vasen, oikea, float(y), float(i)
    raise SystemExit("sivulta 1 ei löydy viivastoa — sisällys ei tiedä "
                     "mihin se saa loppua")


def kaista(rivit, ylin, alin):
    """Pisin täysin musteeton jakso välillä [ylin, alin]: (y0, y1).

    Säveltäjän nimi on keskellä kaistaa, joten kaista jakautuu kahtia ja
    luettelo latoutuu isompaan puolikkaaseen — ei nimen päälle eikä sitä
    väistelemään.
    """
    paras = (0.0, 0.0)
    alku = None
    for y in range(int(ylin), int(alin) + 1):
        if y >= len(rivit) or rivit[y] is None:
            alku = y if alku is None else alku
            if y + 1 - alku > paras[1] - paras[0]:
                paras = (float(alku), float(y + 1))
        else:
            alku = None
    return paras[0] + RESERVI, paras[1] - RESERVI


# ------------------------------------------------------------------ ladonta

def korkeus(maara, sarakkeita=1):
    """Luettelon korkeus pisteinä, otsikko mukaan luettuna."""
    rivilla = int(math.ceil(maara / float(sarakkeita))) if maara else 0
    return OTSIKKO_KOKO * 1.8 + rivilla * RIVI + 2 * RESERVI


def rivin_teksti(numero, nimi, sivu, leveys_rivi):
    """Osan rivi: numero, nimi, täytepisteet ja sivunumero oikeaan reunaan."""
    nimio = "%s  %s" % (numero, nimi)
    numero_teksti = str(sivu)
    vapaana = (leveys_rivi - leveys(nimio + " ", KOKO)
               - leveys(" " + numero_teksti, KOKO))
    pisteita = max(0, int(vapaana / leveys(TAYTE, KOKO)))
    return "%s %s %s" % (nimio, TAYTE * pisteita, numero_teksti)


def asettele(kohdat, rivit, mitta):
    """Sijoita luettelo mitattuun tilaan. Palauta (rivit, laatikot).

    `rivit` on ladottavat tekstirivit (x, perusviivan y, koko, teksti) ja
    `laatikot` linkkien laatikot (x0, y0, x1, y1, sivu) — samassa
    y-alaspäin-koordinaatistossa kuin mittaus.
    """
    vasen, oikea, ylin, alin = mitta
    y0, y1 = kaista(rivit, ylin, alin)
    kaytettava = oikea - vasen
    for sarakkeita in (1, 2, 3):
        if korkeus(len(kohdat), sarakkeita) <= y1 - y0:
            break
    else:
        raise SystemExit(
            "sivun 1 tyhjä tila on vain %d pt eikä luettelo mahdu siihen. "
            "Onko `python3 linkit.py --varaa %s` ajamatta ennen mscorea?"
            % (y1 - y0, "stemma-*.mxl"))
    sarake = min(LEVEYS, (kaytettava - (sarakkeita - 1) * SARAKEVALI)
                 / sarakkeita)

    ladotut = [(vasen, y0 + OTSIKKO_KOKO, OTSIKKO_KOKO, OTSIKKO)]
    laatikot = []
    rivilla = int(math.ceil(len(kohdat) / float(sarakkeita)))
    for i, (numero, nimi, sivu) in enumerate(kohdat):
        x = vasen + (i // rivilla) * (sarake + SARAKEVALI)
        y = y0 + OTSIKKO_KOKO * 1.8 + (i % rivilla) * RIVI
        raja = vapaa(rivit, y, y + RIVI, x, x + sarake)
        if raja < x + sarake:
            raise SystemExit("sisällysluettelon rivi %d osuu musteeseen" % i)
        ladotut.append((x, y + KOKO, KOKO,
                        rivin_teksti(numero, nimi, sivu, sarake)))
        laatikot.append((x, y, x + sarake, y + RIVI, sivu))
    return ladotut, laatikot


def vapaa(rivit, y0, y1, vasen, oikea):
    """Rivinauhan vapaa oikea reuna: musteen vasemmalle puolelle asti."""
    raja = oikea
    for i in range(max(0, int(y0)), min(len(rivit), int(y1) + 1)):
        r = rivit[i]
        if r and vasen <= r[1] and r[0] - RESERVI < raja:
            raja = r[0] - RESERVI
    return raja


# ------------------------------------------------------------------ PDF

def _pdf_teksti(s):
    """PDF-merkkijono WinAnsi-tavuina; ei-ASCII oktaalina."""
    ulos = ""
    for tavu in s.encode("cp1252"):
        if tavu in b"\\()":
            ulos += "\\" + chr(tavu)
        elif 32 <= tavu < 127:
            ulos += chr(tavu)
        else:
            ulos += "\\%03o" % tavu
    return ulos


def virta(ladotut):
    """Sisältövirta: yksi Tj per rivi, PDF:n koordinaatistossa (y ylös)."""
    osat = ["q", "BT"]
    koko = None
    for x, y, rivikoko, rivi in ladotut:
        if rivikoko != koko:
            osat.append("/%s %g Tf" % (FONTTIAVAIN, rivikoko))
            koko = rivikoko
        osat.append("1 0 0 1 %.2f %.2f Tm (%s) Tj" % (x, y, _pdf_teksti(rivi)))
    osat += ["ET", "Q"]
    return "\n".join(osat) + "\n"


# JS on yhtenä palana, jotta kaikki PDF-kirurgia tapahtuu yhdellä
# avauksella ja yhdellä tallennuksella. Tiedot tulevat JSON-literaalina.
JS = r"""
var SPEC = %(spec)s;
var MERKKI = %(merkki)s, FONTTIAVAIN = %(avain)s;

var doc = Document.openDocument(SPEC.sisaan);
var sivu = doc.loadPage(0);
var olio = sivu.getObject();

// Puuttuva avain on mupdf:n JS:ssä null eikä null-olio, joten sitä ei voi
// kysyä ilman tarkistusta.
function omani(o) {
    if (!o || !o.isDictionary || !o.isDictionary()) return false;
    return o.get(MERKKI) !== null;
}

// ---- riisu: kaikki tämän työkalun jäljet pois
var sisalto = olio.get("Contents");
if (sisalto.isArray()) {
    for (var i = sisalto.length - 1; i >= 0; i--)
        if (omani(sisalto.get(i))) sisalto.delete(i);
}
var annot = olio.get("Annots");
if (annot.isArray()) {
    for (var i = annot.length - 1; i >= 0; i--)
        if (omani(annot.get(i))) annot.delete(i);
}
var res = olio.get("Resources");
if (res.isDictionary() && res.get("Font").isDictionary())
    res.get("Font").delete(FONTTIAVAIN);
var juuri = doc.getTrailer().get("Root");
if (omani(juuri.get("Outlines"))) juuri.delete("Outlines");

if (SPEC.lisaa) {
    // ---- teksti omaan sisältövirtaansa
    var fontti = doc.addSimpleFont(new Font(SPEC.fontti), "Latin");
    if (!res.isDictionary()) { res = doc.newDictionary(); olio.put("Resources", res); }
    if (!res.get("Font").isDictionary()) res.put("Font", doc.newDictionary());
    res.get("Font").put(FONTTIAVAIN, fontti);

    // MuseScoren (Qt:n) oma virta jättää voimaan muunnoksen
    // "0.06 0 0 -0.06 0 842 cm" — se on virran ylimmällä tasolla eikä sen
    // q/Q-parien sisällä, joten perään lisätty teksti latoutuisi
    // 0.06-kertaisena ja ylösalaisin. Siksi vanha sisältö kääritään pariin
    // q … Q, jonka jälkeen koordinaatisto on sivun oma. Mitattu: q- ja
    // Q-käskyt ovat Qt:n virrassa tasapainossa (1603 kummankin).
    var alku = doc.addStream("q\n", {});
    alku.put(MERKKI, true);
    var virta = doc.addStream("Q\n" + SPEC.virta, {});
    virta.put(MERKKI, true);
    var lista = doc.newArray();
    lista.push(alku);
    if (sisalto.isArray())
        for (var i = 0; i < sisalto.length; i++) lista.push(sisalto.get(i));
    else
        lista.push(olio.get("Contents"));
    lista.push(virta);
    olio.put("Contents", lista);
    sisalto = olio.get("Contents");

    // ---- linkki joka rivin päälle
    if (!annot.isArray()) { olio.put("Annots", doc.newArray()); annot = olio.get("Annots"); }
    for (var i = 0; i < SPEC.linkit.length; i++) {
        var l = SPEC.linkit[i];
        var d = doc.newDictionary();
        d.put("Type", doc.newName("Annot"));
        d.put("Subtype", doc.newName("Link"));
        var r = doc.newArray();
        r.push(l.rect[0]); r.push(SPEC.korkeus - l.rect[3]);
        r.push(l.rect[2]); r.push(SPEC.korkeus - l.rect[1]);
        d.put("Rect", r);
        var b = doc.newArray();
        b.push(0); b.push(0); b.push(0);
        d.put("Border", b);
        var dest = doc.newArray();
        dest.push(doc.findPage(l.sivu - 1));
        dest.push(doc.newName("XYZ"));
        dest.push(doc.newNull()); dest.push(doc.newNull()); dest.push(doc.newNull());
        d.put("Dest", dest);
        d.put(MERKKI, true);
        annot.push(doc.addObject(d));
    }

    // ---- kirjanmerkit
    // insert jättää kohdistimen lisätyn kohdan jälkeen, joten osat menevät
    // sisään omassa järjestyksessään — käänteinen syöttö kääntäisi luettelon.
    var it = doc.outlineIterator();
    for (var i = 0; i < SPEC.merkit.length; i++)
        it.insert({title: SPEC.merkit[i].nimi,
                   uri: "#page=" + SPEC.merkit[i].sivu});
    juuri.get("Outlines").put(MERKKI, true);
}

doc.save(SPEC.ulos, "compress,garbage=compact");
print("ok");
"""


def kirjoita(pdf, spec):
    """Aja PDF-kirurgia ja korvaa tiedosto vasta onnistuneella tuloksella."""
    kohde = polut.polku(pdf)
    tmp = kohde + ".uusi"
    spec = dict(spec, sisaan=kohde, ulos=tmp, fontti=FONTTI)
    try:
        aja_js(JS % {"spec": json.dumps(spec, ensure_ascii=False),
                     "merkki": json.dumps(MERKKI),
                     "avain": json.dumps(FONTTIAVAIN)})
        os.replace(tmp, kohde)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def riisu(pdf):
    """Poista tämän työkalun lisäykset. Turvallinen myös koskemattomalle."""
    kirjoita(pdf, {"lisaa": False})


# Takaisinluku on oma askel: kirjoitettu linkki on vasta väite, ja tämä on
# se, mitä lukuohjelma tiedostosta näkee.
LUE_JS = r"""
var doc = Document.openDocument(%(pdf)s);
var linkit = doc.loadPage(0).getLinks(), ulos = {"linkit": [], "merkit": []};
for (var i = 0; i < linkit.length; i++)
    ulos.linkit.push({rect: linkit[i].getBounds(), uri: linkit[i].getURI()});
var it = doc.outlineIterator();
do {
    var m = it.item();
    if (m) ulos.merkit.push({nimi: m.title, uri: m.uri});
} while (it.next() >= 0);
print(JSON.stringify(ulos));
"""


def lue(pdf):
    """Mitä PDF:ssä lukee: sivun 1 linkit ja kirjanmerkit.

    Linkin laatikko on samassa y-alaspäin-koordinaatistossa kuin mittaus ja
    kohde muodossa `#page=N`, joten ladonnan tulos on tarkistettavissa
    tiedostosta eikä vain muistista.
    """
    return json.loads(aja_js(LUE_JS % {"pdf": json.dumps(polut.polku(pdf))}))


def lisaa(pdf, kohdat, riisuttu=False):
    """Latoo ja kirjoita luettelo. `kohdat` on [(numero, nimi, sivu)].

    Vanhat lisäykset on riisuttava ennen kuin tila mitataan, tai luettelo
    latoisi itsensä oman edellisen versionsa päälle. `riisuttu=True` kertoo,
    että kutsuja teki sen jo — `sisallys.py` tekee, koska se lukee samasta
    tiedostosta myös osien alkusivut.
    """
    kohdat = [(n, nimi, s) for n, nimi, s in kohdat if s]
    if not kohdat:
        raise SystemExit("%s: yhdenkään osan sivua ei tiedetä" % pdf)
    if not riisuttu:
        riisu(pdf)
    rivit, lev, kork = musterivit(pdf)
    ladotut, laatikot = asettele(kohdat, rivit, tila(rivit, lev))
    kirjoita(pdf, {
        "lisaa": True,
        "korkeus": kork,
        "virta": virta([(x, kork - y, koko, r) for x, y, koko, r in ladotut]),
        "linkit": [{"rect": [x0, y0, x1, y1], "sivu": s}
                   for x0, y0, x1, y1, s in laatikot],
        "merkit": [{"nimi": "%s  %s" % (n, nimi), "sivu": s}
                   for n, nimi, s in kohdat]})
    print("  %s: sisällys %d riviä, %d linkkiä ja kirjanmerkkiä"
          % (pdf, len(laatikot), len(laatikot)))
    return ladotut, laatikot


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    if argv[0] == "--varaa":
        from yhdista import MOVEMENTS
        for mxl in argv[1:]:
            varaa(mxl, len(MOVEMENTS))
        return
    if argv[0] == "--riisu":
        for pdf in argv[1:]:
            riisu(pdf)
            print("  %s: sisällys poistettu" % pdf)
        return
    if argv[0] == "--lue":
        for pdf in argv[1:]:
            tiedot = lue(pdf)
            print("%s: %d linkkiä, %d kirjanmerkkiä"
                  % (pdf, len(tiedot["linkit"]), len(tiedot["merkit"])))
            for m in tiedot["merkit"]:
                print("  %-28s %s" % (m["nimi"], m["uri"]))
        return
    import sisallys
    for pdf in argv:
        sisallys.lisaa_yhteen(pdf)


if __name__ == "__main__":
    main(sys.argv[1:])
