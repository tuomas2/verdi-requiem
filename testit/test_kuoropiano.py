"""Testit kuoron pianoriisun siirtämiselle osan I pianoviivastolle.

Painopiste on kahdessa asiassa, jotka kumpikin purivat kehitysvaiheessa:

1. **Käsintehtyä lähdettä ei oleteta johdonmukaiseksi.** Kuoron tiedostot ovat
   laulajien itsensä tekemiä, joten jokainen siirretty tahti tarkistetaan
   erikseen. Tarkistuksen pitää kulkea tahdin läpi kursorilla eikä laskea
   kestoja äänittäin yhteen: ensimmäinen versio teki juuri sen ja hylkäsi
   kuoron kunnossa olevan tahdin 12, jossa yksi ääni tulee sisään
   `<forward>`in takaa.

2. **Jaotuksen (`divisions`) pitää olla koko tiedostossa sama.** `yhdista.py`
   lukee sen yhdestä viitaosastosta ja käyttää kaikille riveille, joten
   poikkeava piano tuottaa vääränmittaisia taukotahteja ja `mscore`
   kieltäytyy koko partituurista ilman `-f`:ää.
"""
import unittest
import xml.etree.ElementTree as ET

import kuoropiano
from kuoropiano import (OSA_I, jaotus, kulje, tarkista, tyhja_malli,
                        yhtenaista_jaotus)


def tahti(numero, notes, attrs=None):
    """Tahti, jonka nuotti on (kesto, ääni) tai ("backup", kesto)."""
    m = ET.Element("measure", {"number": numero})
    if attrs is not None:
        a = ET.SubElement(m, "attributes")
        ET.SubElement(a, "divisions").text = str(attrs)
    for note in notes:
        if note[0] in ("backup", "forward"):
            e = ET.SubElement(m, note[0])
            ET.SubElement(e, "duration").text = str(note[1])
            continue
        kesto, aani = note
        n = ET.SubElement(m, "note")
        ET.SubElement(n, "duration").text = str(kesto)
        ET.SubElement(n, "voice").text = aani
    return m


def osasto(tahdit):
    p = ET.Element("part", {"id": "P1"})
    for m in tahdit:
        p.append(m)
    return p


class Kursori(unittest.TestCase):
    def test_summa_lasketaan_kursorilla_eika_aanittain(self):
        # Ääni 2 alkaa vasta puolesta tahdista, joten sen kestojen summa on
        # 24 vaikka tahti on 48 pitkä. Tahti on kunnossa.
        m = tahti("1", [(48, "1"), ("backup", 48), ("forward", 24),
                        (24, "2")])
        self.assertEqual(kulje(m)[0], 48)
        tarkista(m, "1", "testi")     # ei kaadu

    def test_soinnun_toinen_savel_ei_siirra_kursoria(self):
        m = ET.Element("measure", {"number": "1"})
        for i in range(2):
            n = ET.SubElement(m, "note")
            if i:
                ET.SubElement(n, "chord")
            ET.SubElement(n, "duration").text = "48"
            ET.SubElement(n, "voice").text = "1"
        self.assertEqual(kulje(m)[0], 48)

    def test_lyhyt_tahti_kaataa(self):
        with self.assertRaises(AssertionError):
            tarkista(tahti("1", [(36, "1")]), "1", "testi")

    def test_pitka_tahti_kaataa(self):
        with self.assertRaises(AssertionError):
            tarkista(tahti("1", [(60, "1")]), "1", "testi")

    def test_tahdin_yli_jatkuva_aani_kaataa(self):
        # Ulottuma on oikea, mutta yksi ääni jatkuu tahdin yli. Ilman tätä
        # tarkistusta kaksi virhettä voisi kumota toisensa.
        m = tahti("1", [(48, "1"), ("backup", 24), (48, "2")])
        with self.assertRaises(AssertionError):
            tarkista(m, "1", "testi")


class Jaotus(unittest.TestCase):
    def test_jaotus_periytyy_seuraaviin_tahteihin(self):
        p = osasto([tahti("1", [(48, "1")], attrs=12), tahti("2", [(48, "1")])])
        self.assertEqual(jaotus(p), {"1": 12, "2": 12})

    def test_yhtenaistaminen_skaalaa_kestot(self):
        root = ET.Element("score-partwise")
        root.append(osasto([tahti("1", [(16, "1")], attrs=4)]))
        root.append(osasto([tahti("1", [(48, "1")], attrs=12)]))
        kohde, muutettu = yhtenaista_jaotus(root)
        self.assertEqual(kohde, 12)
        self.assertEqual(muutettu, 1)
        kestot = [n.findtext("duration") for n in root.iter("note")]
        self.assertEqual(kestot, ["48", "48"])
        self.assertEqual([e.text for e in root.iter("divisions")], ["12", "12"])

    def test_yhtenaistaminen_skaalaa_myos_backupin(self):
        # Kursorin siirrot ovat samassa yksikössä kuin kestot, joten ne on
        # skaalattava mukana tai äänet menevät päällekkäin.
        root = ET.Element("score-partwise")
        root.append(osasto([tahti("1", [(16, "1"), ("backup", 16), (16, "2")],
                                  attrs=4)]))
        root.append(osasto([tahti("1", [(48, "1")], attrs=12)]))
        yhtenaista_jaotus(root)
        self.assertEqual(root.find("part/measure/backup/duration").text, "48")

    def test_kohde_on_pienin_yhteinen_jaettava(self):
        root = ET.Element("score-partwise")
        root.append(osasto([tahti("1", [(8, "1")], attrs=8)]))
        root.append(osasto([tahti("1", [(12, "1")], attrs=12)]))
        self.assertEqual(yhtenaista_jaotus(root)[0], 24)


class TyhjanMalli(unittest.TestCase):
    def test_malli_on_lahteen_oma_tyhja_tahti(self):
        tyhja = ET.Element("measure", {"number": "9"})
        n = ET.SubElement(tyhja, "note")
        ET.SubElement(n, "rest")
        ET.SubElement(n, "duration").text = "48"
        malli = tyhja_malli({"1": tahti("1", [(48, "1")]), "9": tyhja})
        self.assertIs(malli, tyhja)

    def test_kaataa_jos_tyhjaa_tahtia_ei_ole(self):
        with self.assertRaises(AssertionError):
            tyhja_malli({"1": tahti("1", [(48, "1")])})


class OsaIKokonaisuutena(unittest.TestCase):
    """Ajo oikeaa lähdettä vasten: kartoitus ja sen rajat."""

    @classmethod
    def setUpClass(cls):
        cls.root, cls.seloste = kuoropiano.sovella(OSA_I)
        cls.part = kuoropiano.find_part(cls.root, OSA_I.osasto)
        cls.tahdit = cls.part.findall("measure")
        cls.lahde = kuoropiano.lue_piano(OSA_I.piano)

    def test_tahtien_maara_ei_muutu(self):
        self.assertEqual(len(self.tahdit), 140)
        self.assertEqual([m.get("number") for m in self.tahdit],
                         [str(n) for n in range(1, 141)])

    def test_kartoitus_kattaa_126_tahtia_ja_14_jaa_tauoksi(self):
        # 78 + 48 kuoron tiedostosta, 12 + 2 tauoksi. Jos jaksot muuttuvat,
        # tämä kertoo sen heti.
        self.assertIn("126 tahtia kuoron tiedostosta", self.seloste)
        self.assertIn("14 tauoksi", self.seloste)

    def savelet(self, m):
        return [(p.findtext("step"), p.findtext("alter"), p.findtext("octave"))
                for p in m.iter("pitch")]

    def test_siirtyma_on_nolla_tahtiin_78_asti(self):
        for n in (1, 17, 56, 78):
            with self.subTest(tahti=n):
                self.assertEqual(self.savelet(self.tahdit[n - 1]),
                                 self.savelet(self.lahde[str(n)]))

    def test_siirtyma_on_yksitoista_tahdista_91(self):
        for n in (91, 100, 138):
            with self.subTest(tahti=n):
                self.assertEqual(self.savelet(self.tahdit[n - 1]),
                                 self.savelet(self.lahde[str(n - 11)]))

    def test_aukot_ovat_taukoa(self):
        # Kuoron tiedostossa ei ole meidän tahteja 79-90 eikä 139-140.
        for n in list(range(79, 91)) + [139, 140]:
            with self.subTest(tahti=n):
                m = self.tahdit[n - 1]
                self.assertEqual(self.savelet(m), [])
                self.assertTrue(m.findall("note"))
                self.assertTrue(all(x.find("rest") is not None
                                    for x in m.findall("note")))

    def test_tahdit_29_55_ovat_tyhjia_myos_lahteessa(self):
        # Piano ei soita siellä lainkaan (kuoron a cappella -jakso), joten
        # tyhjyys ei ole kartoituksen aukko. Jos tämä kaatuu, aukkojen
        # laskenta on väärin.
        for n in (29, 40, 55):
            with self.subTest(tahti=n):
                self.assertEqual(self.savelet(self.lahde[str(n)]), [])

    def test_jaotus_on_koko_tiedostossa_sama(self):
        arvot = {v for part in self.root.findall("part")
                 for v in jaotus(part).values()}
        self.assertEqual(arvot, {12})

    def test_jokainen_tahti_tayttyy(self):
        for m in self.tahdit:
            with self.subTest(tahti=m.get("number")):
                tarkista(m, m.get("number"), "tulos")

    def test_lahdetiedostoa_ei_muuteta(self):
        alkup = kuoropiano.load(OSA_I.mxl)
        m = kuoropiano.find_part(alkup, OSA_I.osasto).findall("measure")[0]
        self.assertEqual(m.findtext("attributes/divisions"), "4")


if __name__ == "__main__":
    unittest.main()
