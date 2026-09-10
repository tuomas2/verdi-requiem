#!/usr/bin/env python3
"""Stemman päiväysmerkinnän testit.

Päiväys on lupaus lukijalle: "tämän saman tiedoston sisältö muuttui
viimeksi silloin". Lupaus rikkoutuu kahdella tavalla, ja molemmat ovat
hiljaisia. Päivä voi vanhentua — stemma muuttui mutta merkintä ei — tai
päivä voi olla tuore turhaan, jolloin laulaja lataa saman nuotin uudelleen.
Kummankin varalta verrataan sisältöä eikä katsota kelloa, ja se vertailu
testataan tässä.

Toinen puoli on se, ettei päiväys saa maksaa mitään sivulla: MuseScore
lopettaa otsikon johtamisen `movement-title`-alkiosta heti kun tiedostossa
on yksikin credit, joten päiväyksen mukana on kirjoitettava takaisin myös
otsikko ja säveltäjä. Sitä vartioi `Creditit`-luokan testi.

MuseScorea nämä testit eivät kutsu; viennin tilalla on sen muotoinen puu.
"""

import unittest
import xml.etree.ElementTree as ET

import paivays
import sivusto
from sivusto import STEMMAT


def stemma(paiva=None, creditit=()):
    """Stemman muotoinen puu: otsikot, identification, part-list, part."""
    root = ET.Element("score-partwise")
    ET.SubElement(ET.SubElement(root, "work"), "work-title").text = "Requiem"
    ET.SubElement(root, "movement-title").text = "Requiem · Basso I"
    ident = ET.SubElement(root, "identification")
    ET.SubElement(ident, "creator", {"type": "composer"}).text = "Verdi"
    for c in creditit:
        root.append(c)
    ET.SubElement(root, "part-list")
    ET.SubElement(ET.SubElement(root, "part", {"id": "P1"}), "measure")
    if paiva:
        paivays.merkitse_paiva(root, paiva)
    return root


def vienti(creditteja=2, vasen="85.7143", ylin=1611.01):
    """MuseScoren viennin muoto: sivumarginaalit ja lasketut creditit."""
    root = ET.Element("score-partwise")
    marginaalit = ET.SubElement(
        ET.SubElement(ET.SubElement(root, "defaults"), "page-layout"),
        "page-margins", {"type": "odd"})
    ET.SubElement(marginaalit, "left-margin").text = vasen
    for i, (tyyppi, y) in enumerate([("title", ylin),
                                     ("composer", ylin - 120)][:creditteja]):
        c = ET.SubElement(root, "credit", {"page": "1"})
        ET.SubElement(c, "credit-type").text = tyyppi
        ET.SubElement(c, "credit-words", {"default-y": "%g" % y}).text = tyyppi
    return root


def paivaykset(root):
    """Tämän työkalun lisäämien credittien tekstit."""
    return [w.text for w in root.iter("credit-words")
            if (w.get("id") or "") == paivays.TUNNISTE]


class Muoto(unittest.TestCase):
    def test_suomeksi(self):
        self.assertEqual(paivays.suomeksi("2026-09-10"), "10.9.2026")
        self.assertEqual(paivays.suomeksi("2026-12-01"), "1.12.2026")

    def test_merkitty_paiva_luetaan_takaisin(self):
        self.assertEqual(paivays.lue_root(stemma("2026-09-10")), "2026-09-10")

    def test_merkitsematon_stemma_ei_valehtele_paivaa(self):
        self.assertIsNone(paivays.lue_root(stemma()))


class Riisunta(unittest.TestCase):
    def test_omat_merkinnat_lahtevat_pois(self):
        root = stemma("2026-09-10")
        paivays.lisaa_creditit(root, vienti(), "2026-09-10")
        self.assertEqual(paivays.riisu(root), "2026-09-10")
        self.assertEqual(root.findall("credit"), [])
        self.assertIsNone(root.find("identification/encoding"))

    def test_vieras_credit_jaa_paikalleen(self):
        """Riisunta tunnistaa omansa id:stä eikä pyyhi mitä ei tuntenut."""
        vieras = ET.Element("credit", {"page": "1"})
        ET.SubElement(vieras, "credit-words").text = "jonkun muun teksti"
        root = stemma(creditit=[vieras])
        paivays.riisu(root)
        self.assertEqual(len(root.findall("credit")), 1)

    def test_runko_ei_nae_paivaysta(self):
        """Vertailun perusta: päiväys itse ei saa näyttää muutokselta."""
        tyhja = stemma()
        merkitty = stemma("2026-09-10")
        paivays.lisaa_creditit(merkitty, vienti(), "2026-09-10")
        self.assertEqual(paivays.runko(tyhja), paivays.runko(merkitty))

    def test_runko_nakee_sisallon(self):
        muuttunut = stemma()
        muuttunut.find("part/measure").set("number", "2")
        self.assertNotEqual(paivays.runko(stemma()), paivays.runko(muuttunut))


class Paivanvalinta(unittest.TestCase):
    """Päivä tulee sisällöstä, ei kellosta.

    `yhdista.py` kirjoittaa kaikki kahdeksan stemmaa uusiksi joka ajolla,
    joten rakennuspäivä olisi jokaisessa stemmassa tämä päivä silloinkin
    kun ääni ei ole muuttunut kuukauteen.
    """

    def setUp(self):
        self.oikea = paivays.gitin_versio

    def tearDown(self):
        paivays.gitin_versio = self.oikea

    def valeversio(self, root):
        paivays.gitin_versio = lambda _mxl: root

    def test_ennallaan_oleva_stemma_pitaa_vanhan_paivan(self):
        self.valeversio(stemma("2026-08-31"))
        self.assertEqual(
            paivays.paatele_paiva("stemma-basso-1.mxl", stemma(), "2026-09-10"),
            "2026-08-31")

    def test_muuttunut_stemma_saa_taman_paivan(self):
        vanha = stemma("2026-08-31")
        vanha.find("part/measure").set("number", "2")
        self.valeversio(vanha)
        self.assertEqual(
            paivays.paatele_paiva("stemma-basso-1.mxl", stemma(), "2026-09-10"),
            "2026-09-10")

    def test_ilman_vertailukohtaa_merkitaan_tama_paiva(self):
        """Ei gitiä tai tiedosto vasta syntynyt: muuta ei tiedetä."""
        self.valeversio(None)
        self.assertEqual(
            paivays.paatele_paiva("stemma-basso-1.mxl", stemma(), "2026-09-10"),
            "2026-09-10")

    def test_paivaton_vertailukohta_ei_kelpaa_paivaksi(self):
        self.valeversio(stemma())
        self.assertEqual(
            paivays.paatele_paiva("stemma-basso-1.mxl", stemma(), "2026-09-10"),
            "2026-09-10")


class Creditit(unittest.TestCase):
    def test_otsikko_ja_saveltaja_kirjoitetaan_mukaan(self):
        """Yksikin credit lopettaa otsikon johtamisen movement-titlestä.

        Jos viennin creditit jätettäisiin pois, päiväys pyyhkisi stemman
        otsikon ja säveltäjän sivulta. Mitattu MuseScore 4.7.4:llä.
        """
        root = stemma()
        paivays.lisaa_creditit(root, vienti(), "2026-09-10")
        tyypit = [c.findtext("credit-type") for c in root.findall("credit")]
        self.assertEqual(tyypit, ["title", "composer", "lyricist"])

    def test_credititon_vienti_pysayttaa_ajon(self):
        with self.assertRaises(SystemExit):
            paivays.lisaa_creditit(stemma(), vienti(creditteja=0), "2026-09-10")

    def test_kaikki_lisatyt_creditit_ovat_tunnistettavia(self):
        """Muuten uudelleenajo kasaisi niitä päällekkäin."""
        root = stemma()
        paivays.lisaa_creditit(root, vienti(), "2026-09-10")
        for sanat in root.iter("credit-words"):
            with self.subTest(teksti=sanat.text):
                self.assertTrue((sanat.get("id") or "")
                                .startswith(paivays.TUNNISTE))

    def test_uudelleenajo_ei_kasaa_creditteja(self):
        root = stemma()
        for _ in range(3):
            paivays.riisu(root)
            paivays.lisaa_creditit(root, vienti(), "2026-09-10")
        self.assertEqual(len(root.findall("credit")), 3)

    def test_creditit_tulevat_ennen_part_listia(self):
        """MusicXML:n järjestys; väärässä paikassa MuseScore ei lue niitä."""
        root = stemma()
        paivays.lisaa_creditit(root, vienti(), "2026-09-10")
        tagit = [c.tag for c in root]
        viimeinen = max(i for i, t in enumerate(tagit) if t == "credit")
        self.assertGreater(viimeinen, tagit.index("identification"))
        self.assertLess(viimeinen, tagit.index("part-list"))

    def test_paivays_on_ensimmaisella_sivulla_pienella(self):
        root = stemma()
        paivays.lisaa_creditit(root, vienti(), "2026-09-10")
        credit = root.findall("credit")[-1]
        sanat = credit.find("credit-words")
        self.assertEqual(credit.get("page"), "1")
        self.assertEqual(sanat.text, "Päivitetty 10.9.2026")
        self.assertEqual(sanat.get("font-size"), paivays.FONTTIKOKO)
        self.assertLess(float(paivays.FONTTIKOKO), 12,
                        "päiväyksen pitää olla pienempi kuin nuottiteksti")

    def test_paivays_on_lyricist_koska_vain_se_tottelee_paikkaa(self):
        """Tyypitön credit ladottiin säveltäjän nimen päälle. Mitattu."""
        root = stemma()
        paivays.lisaa_creditit(root, vienti(), "2026-09-10")
        self.assertEqual(root.findall("credit")[-1].findtext("credit-type"),
                         "lyricist")

    def test_paikka_luetaan_viennista_eika_vakioista(self):
        """Tyylin muuttuessa paikan pitää seurata perässä itsestään."""
        root = stemma()
        paivays.lisaa_creditit(root, vienti(vasen="120", ylin=1500),
                               "2026-09-10")
        sanat = root.findall("credit")[-1].find("credit-words")
        self.assertEqual(sanat.get("default-x"), "120")
        self.assertEqual(sanat.get("default-y"), "1500")
        self.assertEqual(sanat.get("valign"), "top")


class Stemmatiedostot(unittest.TestCase):
    def test_jokaisessa_julkaistussa_stemmassa_on_paiva(self):
        """Merkitsemätön stemma jää sivustolla ilman päiväystä äänettä."""
        for _nimi, pdf in STEMMAT:
            mxl = pdf[:-4] + ".mxl"
            with self.subTest(stemma=mxl):
                self.assertRegex(paivays.lue(mxl) or "", r"^20\d\d-\d\d-\d\d$")


class Sivustolla(unittest.TestCase):
    def test_paivays_nakyy_latauslinkin_yhteydessa(self):
        html = sivusto.stemmasivu()
        for _nimi, pdf in STEMMAT:
            iso = paivays.lue(pdf[:-4] + ".mxl")
            with self.subTest(stemma=pdf):
                self.assertIn('<time datetime="%s">päivitetty %s</time>'
                              % (iso, paivays.suomeksi(iso)), html)

    def test_sivun_paiva_on_sama_kuin_tiedoston(self):
        """Sivu lukee saman merkinnän kuin mikä PDF:ään ladottiin."""
        self.assertIn(paivays.suomeksi(paivays.lue("stemma-basso-1.mxl")),
                      sivusto.paivamaara("stemma-basso-1.pdf"))

    def test_puuttuva_stemma_ei_kaada_sivua(self):
        self.assertEqual(sivusto.paivamaara("stemma-ei-tallaista.pdf"), "")


if __name__ == "__main__":
    unittest.main()
