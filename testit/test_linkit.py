#!/usr/bin/env python3
"""Testit stemman klikattavalle sisällysluettelolle.

Luettelo tarvitsee kaksi asiaa onnistuakseen: MuseScoren pitää varata sille
tila sivun 1 yläosasta (`varaa`, ennen renderöintiä) ja ladonnan pitää
löytää se tila sivulta (`tila`, `kaista`). Kolme asiaa voi mennä rikki
huomaamatta: varaus voi kadota tiedostosta, ladonta voi ryömiä nuotin tai
säveltäjän nimen päälle, ja linkki voi osoittaa väärään sivuun. Kaikki
kolme on tässä — ensin ladonta keksityllä sivulla, sitten valmis PDF, josta
linkit luetaan takaisin.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

import linkit
from korjaa_sanat import load

PDF = os.path.join("stemmat", "stemma-basso-1.pdf")
MXL = os.path.join("stemmat", "stemma-basso-1.mxl")

# Keksitty sivu 1: otsikkolohko riveillä 42-63, säveltäjän nimi oikealla
# 84-94, varattu tyhjä tila 95-279 ja ensimmäinen viivastoviiva 280. Samat
# mitat kuin varatussa stemmassa, mutta ilman mutoolia.
LEVEYS = 595.0
VIIVASTO_Y = 280


def keksitty_sivu(viivasto=VIIVASTO_Y):
    rivit = [None] * (viivasto + 100)
    for y in range(42, 64):
        rivit[y] = (42.0, 440.0)          # päiväys ja otsikko
    for y in range(84, 95):
        rivit[y] = (482.0, 553.0)         # Giuseppe Verdi
    for y in range(viivasto, len(rivit)):
        rivit[y] = (42.0, 553.0)          # viivasto
    return rivit


def osat(n=17):
    """Osalista, jonka nimet ja sivut ovat oikean stemman mittaisia."""
    nimet = ["Requiem & Kyrie", "Dies irae", "Tuba mirum", "Mors stupebit",
             "Liber scriptus", "Quid sum miser", "Rex tremendae", "Recordare",
             "Ingemisco", "Confutatis", "Dies irae (kertaus)", "Lacrymosa",
             "Offertorio", "Sanctus", "Agnus Dei", "Lux aeterna", "Libera me"]
    numerot = ["I", "II·1", "II·2", "II·3", "II·4", "II·5", "II·6", "II·7",
               "II·8", "II·9", "II·9b", "II·10", "III", "IV", "V", "VI", "VII"]
    sivut = [1, 3, 4, 4, 5, 5, 5, 6, 6, 7, 7, 7, 8, 8, 10, 11, 11]
    return list(zip(numerot, nimet, sivut))[:n]


class Mitat(unittest.TestCase):
    """Vakioleveys joka merkille: ladonnan säännöt eivät riipu fontista,
    ja testi pysyy mutoolista riippumattomana."""

    def setUp(self):
        linkit._mitat.clear()
        linkit._mitat.update({c: 0.5 for c in
                              [chr(i) for i in range(32, 127)] + list("·äöåé")})

    def tearDown(self):
        linkit._mitat.clear()


class Tila(Mitat):
    def test_tila_alkaa_otsikkolohkon_alta_ja_loppuu_viivastoon(self):
        vasen, oikea, ylin, alin = linkit.tila(keksitty_sivu(), LEVEYS)
        self.assertEqual((vasen, oikea), (42.0, 553.0))
        self.assertEqual((ylin, alin), (64.0, float(VIIVASTO_Y)))

    def test_tyhja_sivu_kaataa(self):
        with self.assertRaises(SystemExit):
            linkit.tila([None] * 50, LEVEYS)

    def test_sivu_ilman_viivastoa_kaataa(self):
        """Ilman viivastoa ei tiedetä, missä nuotti alkaa."""
        rivit = [None] * 50
        rivit[10] = (42.0, 100.0)
        with self.assertRaises(SystemExit):
            linkit.tila(rivit, LEVEYS)

    def test_kaista_valitsee_saveltajan_nimen_alapuolen(self):
        """Nimi katkaisee kaistan; luettelo latoutuu isompaan puolikkaaseen."""
        rivit = keksitty_sivu()
        y0, y1 = linkit.kaista(rivit, 64.0, float(VIIVASTO_Y))
        self.assertEqual((y0, y1), (95 + linkit.RESERVI,
                                    VIIVASTO_Y - linkit.RESERVI))

    def test_kaista_ei_loyda_tilaa_taydelta_sivulta(self):
        rivit = [(42.0, 553.0)] * 200
        y0, y1 = linkit.kaista(rivit, 64.0, 150.0)
        self.assertLessEqual(y1 - y0, 0)


class Varaus(Mitat):
    def test_varaus_kasvaa_osien_maaran_mukana(self):
        self.assertGreater(linkit.varauksen_rivit(17),
                           linkit.varauksen_rivit(8))

    def test_varaus_riittaa_luettelon_korkeuteen(self):
        rivit = linkit.varauksen_rivit(17)
        self.assertGreaterEqual(rivit * linkit.VARAUS_RIVI,
                                linkit.korkeus(17))

    def test_varaustekstissa_on_nakymatonta_sisaltoa(self):
        """Pelkkä tyhjä rivi ei vie MuseScoressa korkeutta — mitattu."""
        d = linkit.varaus_direction(3)
        w = d.find("direction-type/words")
        self.assertEqual(w.get("color"), "#FFFFFF")
        self.assertEqual(w.get("id"), linkit.VARAUS_TUNNISTE)
        self.assertEqual(w.text.split("\n"), ["."] * 3)

    def test_riisu_varaus_ei_koske_muihin_directioneihin(self):
        root = ET.fromstring(
            '<score-partwise><part><measure number="1">'
            '<direction><direction-type><words>I  Requiem &amp; Kyrie'
            '</words></direction-type></direction>'
            '</measure></part></score-partwise>')
        root.find("part/measure").append(linkit.varaus_direction(2))
        self.assertTrue(linkit.riisu_varaus(root))
        jaljella = root.findall("part/measure/direction")
        self.assertEqual(len(jaljella), 1)
        self.assertEqual(jaljella[0].find("direction-type/words").text,
                         "I  Requiem & Kyrie")
        self.assertFalse(linkit.riisu_varaus(root))


@unittest.skipUnless(os.path.exists(MXL), "vaatii rakennetun stemman")
class VarausTiedostoon(Mitat):
    def setUp(self):
        super().setUp()
        self.hakemisto = tempfile.mkdtemp()
        self.mxl = os.path.join(self.hakemisto, "stemma.mxl")
        shutil.copy(MXL, self.mxl)

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.hakemisto)

    def varaukset(self):
        return [d for d in load(self.mxl).iter("direction")
                if any((w.get("id") or "") == linkit.VARAUS_TUNNISTE
                       for w in d.iter("words"))]

    def test_varaus_tulee_osan_otsikon_jalkeen(self):
        """Ennen otsikkoa varaus jättäisi otsikon irti viivastostaan."""
        linkit.varaa(self.mxl, 17)
        lapset = list(load(self.mxl).find("part/measure"))
        directionit = [i for i, e in enumerate(lapset) if e.tag == "direction"]
        oma = [i for i in directionit
               if any((w.get("id") or "") == linkit.VARAUS_TUNNISTE
                      for w in lapset[i].iter("words"))]
        self.assertEqual(oma, [max(directionit)])

    def test_uudelleenajo_ei_kasaa_varauksia(self):
        linkit.varaa(self.mxl, 17)
        linkit.varaa(self.mxl, 17)
        self.assertEqual(len(self.varaukset()), 1)


class Ladonta(Mitat):
    def setUp(self):
        super().setUp()
        self.rivit = keksitty_sivu()
        self.mitta = linkit.tila(self.rivit, LEVEYS)

    def test_kaikki_osat_omalla_rivillaan_omassa_jarjestyksessaan(self):
        ladotut, laatikot = linkit.asettele(osat(), self.rivit, self.mitta)
        self.assertEqual(len(laatikot), 17)
        self.assertEqual([s for _x0, _y0, _x1, _y1, s in laatikot],
                         [s for _n, _nimi, s in osat()])
        # Ensimmäinen ladottu rivi on otsikko, loput osien rivejä.
        self.assertEqual(ladotut[0][3], linkit.OTSIKKO)
        for (numero, nimi, sivu), rivi in zip(osat(), ladotut[1:]):
            with self.subTest(osa=numero):
                self.assertTrue(rivi[3].startswith("%s  %s" % (numero, nimi)))
                self.assertTrue(rivi[3].endswith(" %d" % sivu))

    def test_rivit_ovat_kaistan_sisalla_eivatka_musteen_paalla(self):
        _ladotut, laatikot = linkit.asettele(osat(), self.rivit, self.mitta)
        y0, y1 = linkit.kaista(self.rivit, self.mitta[2], self.mitta[3])
        for x0, ry0, x1, ry1, _s in laatikot:
            with self.subTest(laatikko=(x0, ry0)):
                self.assertGreaterEqual(ry0, y0)
                self.assertLessEqual(ry1, y1)
                self.assertAlmostEqual(ry1 - ry0, linkit.RIVI)
                self.assertLessEqual(
                    x1, linkit.vapaa(self.rivit, ry0, ry1, x0, x1) + 0.01)

    def test_linkin_laatikko_on_koko_rivin_levyinen(self):
        """Sormella osuminen on koko syy siihen, miksi laatikko ei ole
        pelkän tekstin mittainen."""
        _ladotut, laatikot = linkit.asettele(osat(), self.rivit, self.mitta)
        leveydet = {round(x1 - x0, 2) for x0, _y0, x1, _y1, _s in laatikot}
        self.assertEqual(len(leveydet), 1)
        self.assertGreaterEqual(leveydet.pop(), 200.0)

    def sarakkeet(self, laatikot):
        return {x0 for x0, _y0, _x1, _y1, _s in laatikot}

    def test_varattu_tila_riittaa_tavoitepalstamaaraan(self):
        _ladotut, laatikot = linkit.asettele(osat(), self.rivit, self.mitta)
        self.assertEqual(len(self.sarakkeet(laatikot)), linkit.SARAKKEITA)

    def test_ahdas_tila_jakaa_useampaan_palstaan(self):
        """Useampi palsta on matalampi, joten se mahtuu kun tavoite ei."""
        rivit = keksitty_sivu(viivasto=230)
        mitta = linkit.tila(rivit, LEVEYS)
        _ladotut, laatikot = linkit.asettele(osat(), rivit, mitta)
        self.assertEqual(len(laatikot), 17)
        self.assertGreater(len(self.sarakkeet(laatikot)), linkit.SARAKKEITA)

    def test_varaamatta_jaanyt_tila_kaataa_ja_neuvoo(self):
        """Ilman `--varaa`-askelta tilaa on parikymmentä pistettä."""
        rivit = keksitty_sivu(viivasto=120)
        mitta = linkit.tila(rivit, LEVEYS)
        with self.assertRaises(SystemExit) as e:
            linkit.asettele(osat(), rivit, mitta)
        self.assertIn("--varaa", str(e.exception))

    def test_palstat_tayttyvat_lukujarjestyksessa(self):
        """Vasen palsta ensin ylhäältä alas, sitten seuraava."""
        _ladotut, laatikot = linkit.asettele(osat(), self.rivit, self.mitta)
        rivilla = -(-17 // linkit.SARAKKEITA)
        self.assertEqual(laatikot[0][0], laatikot[rivilla - 1][0])
        self.assertLess(laatikot[0][1], laatikot[rivilla - 1][1])
        self.assertGreater(laatikot[rivilla][0], laatikot[0][0])
        self.assertEqual(laatikot[rivilla][1], laatikot[0][1])

    def test_sivunumero_asettuu_rivin_oikeaan_reunaan(self):
        """Täytepisteet lasketaan fontin mitoista, joten rivi täyttyy."""
        teksti = linkit.rivin_teksti("II·9b", "Dies irae (kertaus)", 7, 300.0)
        self.assertLessEqual(linkit.leveys(teksti, linkit.KOKO), 300.0)
        self.assertGreater(linkit.leveys(teksti, linkit.KOKO), 290.0)
        self.assertIn(".", teksti)


class Virta(Mitat):
    def test_teksti_pakenee_pdf_merkkijonoksi(self):
        self.assertEqual(linkit._pdf_teksti("(x)\\y"), "\\(x\\)\\\\y")
        self.assertEqual(linkit._pdf_teksti("II·9b"), "II\\2679b")

    def test_virta_vaihtaa_fonttikoon_vain_kun_se_muuttuu(self):
        virta = linkit.virta([(42.0, 700.0, 11.0, "Sisällys"),
                              (42.0, 686.0, 9.5, "eka"),
                              (42.0, 672.0, 9.5, "toka")])
        self.assertEqual(virta.count(" Tf"), 2)
        self.assertEqual(virta.count(" Tm ("), 3)
        self.assertIn("1 0 0 1 42.00 686.00 Tm (eka) Tj", virta)
        # Kääre: teksti alkaa omalla q:lla ja päättyy Q:hon, jotta se ei
        # jätä graafista tilaa jälkeensä.
        self.assertTrue(virta.startswith("q\n"))
        self.assertTrue(virta.rstrip().endswith("Q"))


def on_mutool():
    try:
        subprocess.run(["mutool", "-v"], capture_output=True)
        return True
    except FileNotFoundError:
        return False


@unittest.skipUnless(on_mutool() and os.path.exists(PDF),
                     "vaatii mutoolin ja rakennetun stemman")
class ValmisPdf(unittest.TestCase):
    """Kirjoitettu linkki on väite; tässä se luetaan tiedostosta takaisin."""

    @classmethod
    def setUpClass(cls):
        cls.hakemisto = tempfile.mkdtemp()
        cls.pdf = os.path.join(cls.hakemisto, "stemma.pdf")
        shutil.copy(PDF, cls.pdf)
        # Repoon talletetussa stemmassa luettelo on jo. Vertailukohta on se
        # sivu, jolla sitä ei ole, joten kopio riisutaan ensin — ja samasta
        # syystä tila mitataan riisutusta eikä valmiista.
        linkit.riisu(cls.pdf)
        cls.alkuteksti = cls.sivun_teksti(cls.pdf)
        cls.sivuja = cls.sivumaara(cls.pdf)
        rivit, lev, _kork = linkit.musterivit(cls.pdf)
        mitta = linkit.tila(rivit, lev)
        cls.kaista = linkit.kaista(rivit, mitta[2], mitta[3])
        linkit.lisaa(cls.pdf, osat())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.hakemisto)

    @staticmethod
    def sivun_teksti(pdf, sivu=1):
        return subprocess.run(["mutool", "draw", "-F", "txt", "-o", "-", pdf,
                               str(sivu)], capture_output=True,
                              text=True).stdout

    @staticmethod
    def sivumaara(pdf):
        return subprocess.run(["mutool", "pages", pdf], capture_output=True,
                              text=True).stdout.count("page ")

    def test_joka_osalla_on_linkki_oikealle_sivulle(self):
        luettu = linkit.lue(self.pdf)
        self.assertEqual([l["uri"] for l in luettu["linkit"]],
                         ["#page=%d" % s for _n, _nimi, s in osat()])

    def test_joka_osalla_on_kirjanmerkki_oikealle_sivulle(self):
        luettu = linkit.lue(self.pdf)
        self.assertEqual([(m["nimi"], m["uri"]) for m in luettu["merkit"]],
                         [("%s  %s" % (n, nimi), "#page=%d" % s)
                          for n, nimi, s in osat()])

    def test_linkit_ovat_mitatussa_tyhjassa_kaistassa(self):
        """Laatikko ei saa olla nuotin, otsikon eikä säveltäjän nimen päällä."""
        y0, y1 = self.kaista
        for l in linkit.lue(self.pdf)["linkit"]:
            x0, ry0, x1, ry1 = l["rect"]
            with self.subTest(uri=l["uri"]):
                self.assertGreater(x1, x0)
                self.assertGreaterEqual(ry0, y0 - 1)
                self.assertLessEqual(ry1, y1 + 1)

    def test_sivumaara_ei_muutu(self):
        """Ladonta ei saa työntää nuottia eteenpäin — tila on jo varattu."""
        self.assertEqual(self.sivumaara(self.pdf), self.sivuja)

    def test_uudelleenajo_tuottaa_saman_tiedoston(self):
        koko = os.path.getsize(self.pdf)
        linkit.lisaa(self.pdf, osat())
        self.assertEqual(os.path.getsize(self.pdf), koko)
        self.assertEqual(len(linkit.lue(self.pdf)["linkit"]), len(osat()))

    def test_riisu_palauttaa_sivun_ennalleen(self):
        pdf = os.path.join(self.hakemisto, "riisuttu.pdf")
        shutil.copy(PDF, pdf)
        linkit.riisu(pdf)
        vertailu = self.sivun_teksti(pdf)
        linkit.lisaa(pdf, osat())
        self.assertNotEqual(self.sivun_teksti(pdf), vertailu)
        linkit.riisu(pdf)
        self.assertEqual(self.sivun_teksti(pdf), vertailu)
        luettu = linkit.lue(pdf)
        self.assertEqual((luettu["linkit"], luettu["merkit"]), ([], []))

    def test_riisu_toistamiseen_ei_tee_mitaan_pahaa(self):
        """Poisto tiedostosta, jossa ei ole mitään poistettavaa."""
        pdf = os.path.join(self.hakemisto, "koskematon.pdf")
        shutil.copy(PDF, pdf)
        linkit.riisu(pdf)
        linkit.riisu(pdf)
        self.assertEqual(self.sivun_teksti(pdf), self.alkuteksti)
        self.assertEqual(self.sivumaara(pdf), self.sivuja)


if __name__ == "__main__":
    unittest.main()
