"""Testit käsin todennetuille korjauksille.

Painopiste on turvassa: korjaus osoittaa tahtiin ja nuotti-indeksiin, joten
jos lähdetiedosto muuttuu, korjaus voisi osua hiljaa väärään paikkaan. Siksi
jokaisen toimenpiteen pitää kaatua kun lähtötilanne ei ole odotettu.
"""
import unittest
import xml.etree.ElementTree as ET

from korjaa_kasin import OSA_I, Osa, load, find_part, sovella, yksi_sanarivi


def osa(korjaukset, yksi_rivi=False):
    return Osa(mxl="-", out="-", osasto="P1", nimi="testi",
               yksi_sanarivi=yksi_rivi, korjaukset=tuple(korjaukset))


def part(*measures):
    """Rakenna osasto: measures on lista tahteja, tahti lista nuotteja.

    Nuotti on (korkeus tai None, [(rivi, syllabic, tavu), ...]) tai
    lisäksi ääni: (korkeus, lyriikat, ääni).
    """
    p = ET.Element("part", {"id": "P1"})
    for i, notes in enumerate(measures, start=1):
        m = ET.SubElement(p, "measure", {"number": str(i)})
        for note in notes:
            pitch, lyrics = note[0], note[1]
            voice = note[2] if len(note) > 2 else "1"
            n = ET.SubElement(m, "note")
            if pitch is None:
                ET.SubElement(n, "rest")
            else:
                pe = ET.SubElement(n, "pitch")
                ET.SubElement(pe, "step").text = pitch[0]
                ET.SubElement(pe, "octave").text = pitch[1]
            ET.SubElement(n, "voice").text = voice
            for number, syllabic, text in lyrics:
                ly = ET.SubElement(n, "lyric", {"number": number})
                ET.SubElement(ly, "syllabic").text = syllabic
                ET.SubElement(ly, "text").text = text
    return p


def rows(p):
    return [(m.get("number"), i, ly.get("number"), ly.findtext("syllabic"),
             ly.findtext("text"))
            for m in p.findall("measure")
            for i, n in enumerate(m.findall("note"))
            for ly in n.findall("lyric")]


class Toimenpiteet(unittest.TestCase):
    def test_poista_tavu(self):
        p = part([("C3", [("1", "end", "is."), ("2", "single", "S")])])
        sovella(p, osa([("1", 0, "poista", "S")]))
        self.assertEqual(rows(p), [("1", 0, "1", "end", "is.")])

    def test_lisaa_tavu(self):
        p = part([("C3", []), ("D3", [])])
        sovella(p, osa([("1", 1, "lisaa", "middle", "i")]))
        self.assertEqual(rows(p), [("1", 1, "1", "middle", "i")])

    def test_aseta_tavu_vaihtaa_tekstin_ja_syllabicin(self):
        p = part([("C3", [("2", "end", "i")])])
        sovella(p, osa([("1", 0, "aseta", "i", "end", "son,")]))
        self.assertEqual(rows(p), [("1", 0, "2", "end", "son,")])

    def test_poista_nuotti(self):
        p = part([("C3", []), (None, [])])
        sovella(p, osa([("1", 1, "poista_nuotti", "rest")]))
        self.assertEqual(len(p.find("measure").findall("note")), 1)

    def test_tavun_siirto_on_poisto_ja_lisays(self):
        p = part([("C3", [("1", "end", "nis")])], [("D3", [])])
        sovella(p, osa([("1", 0, "poista", "nis"),
                        ("2", 0, "lisaa", "end", "nis")]))
        self.assertEqual(rows(p), [("2", 0, "1", "end", "nis")])


class Vartijat(unittest.TestCase):
    """Väärään paikkaan osuva korjaus on pahempi kuin pysähtynyt ajo."""

    def test_tuntematon_tahti_kaataa(self):
        p = part([("C3", [])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("9", 0, "lisaa", "single", "x")]))

    def test_liian_suuri_nuottiindeksi_kaataa(self):
        p = part([("C3", [])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 5, "lisaa", "single", "x")]))

    def test_poisto_kaataa_jos_tavua_ei_ole(self):
        p = part([("C3", [("1", "single", "muu")])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "poista", "S")]))

    def test_lisays_kaataa_jos_nuotilla_on_jo_tavu(self):
        p = part([("C3", [("1", "single", "jo")])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "lisaa", "single", "uusi")]))

    def test_asetus_kaataa_jos_vanha_teksti_on_eri(self):
        p = part([("C3", [("1", "end", "muu")])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "aseta", "i", "end", "son,")]))

    def test_nuotin_poisto_kaataa_jos_kohde_ei_ole_tauko(self):
        p = part([("C3", []), ("D3", [])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 1, "poista_nuotti", "rest")]))

    def test_tuntematon_toimenpide_kaataa(self):
        p = part([("C3", [])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "hoksaa", "x")]))


class YksiSanarivi(unittest.TestCase):
    def test_nostaa_kaikki_riville_yksi(self):
        p = part([("C3", [("2", "begin", "Te")]),
                  ("D3", [("2", "end", "cet")])])
        yksi_sanarivi(p)
        self.assertEqual([r[2] for r in rows(p)], ["1", "1"])

    def test_kieltaytyy_jos_nuotilla_on_kaksi_tavua(self):
        # Kaksi tavua samalla nuotilla tarvitsee kaksi riviä; yhdistäminen
        # panisi ne päällekkäin.
        p = part([("C3", [("1", "end", "is."), ("2", "single", "S")])])
        with self.assertRaises(AssertionError):
            yksi_sanarivi(p)

    def test_kieltaytyy_jos_viivastolla_on_kaksi_aanta(self):
        # Divisi: kaksi ääntä laulaa eri tekstiä, rivit erottavat ne.
        p = part([("C3", [("1", "begin", "Pi")], "1"),
                  ("F3", [("2", "begin", "La")], "2")])
        with self.assertRaises(AssertionError):
            yksi_sanarivi(p)


class OsaIKokonaisuutena(unittest.TestCase):
    """Ajo oikeaa lähdetiedostoa vasten: laulajan raportoimat kohdat."""

    @classmethod
    def setUpClass(cls):
        root = load(OSA_I.mxl)
        cls.part = find_part(root, OSA_I.osasto)
        sovella(cls.part, OSA_I)
        cls.bars = {m.get("number"): m.findall("note")
                    for m in cls.part.findall("measure")}

    def tavu(self, tahti, nuotti):
        ly = self.bars[tahti][nuotti].findall("lyric")
        return None if not ly else (ly[0].get("number"),
                                    ly[0].findtext("syllabic"),
                                    ly[0].findtext("text"))

    def test_omnis_nis_on_tahdin_52_viimeisella_nuotilla(self):
        self.assertEqual(self.tavu("51", 0), ("1", "begin", "om"))
        self.assertIsNone(self.tavu("51", 1))
        self.assertEqual(self.tavu("52", 3), ("1", "end", "nis"))

    def test_tahti_108_eleison_on_yhdella_sanarivilla(self):
        self.assertEqual(self.tavu("107", 3), ("1", "begin", "e"))
        self.assertEqual(self.tavu("108", 0), ("1", "middle", "le"))
        self.assertEqual(self.tavu("108", 1), ("1", "middle", "i"))
        self.assertEqual(self.tavu("108", 2), ("1", "end", "son,"))

    def test_tahdit_125_130_kaksi_eleisonia_neljalle_nuotille(self):
        self.assertEqual(self.tavu("125", 0), ("1", "begin", "e"))
        self.assertEqual(self.tavu("126", 0), ("1", "middle", "le"))
        self.assertEqual(self.tavu("126", 1), ("1", "middle", "i"))
        self.assertEqual(self.tavu("127", 0), ("1", "end", "son,"))
        self.assertEqual(self.tavu("127", 1), ("1", "begin", "e"))
        self.assertEqual(self.tavu("128", 0), ("1", "middle", "le"))
        self.assertEqual(self.tavu("129", 0), ("1", "middle", "i"))
        self.assertEqual(self.tavu("130", 0), ("1", "end", "son,"))

    def test_tahdissa_78_ei_ole_roskatavua(self):
        self.assertEqual(self.tavu("78", 0), ("1", "end", "is."))
        self.assertEqual(len(self.bars["78"][0].findall("lyric")), 1)

    def test_tahti_54_on_taydellinen_eika_yli(self):
        kestot = [int(n.findtext("duration")) for n in self.bars["54"]]
        self.assertEqual(sum(kestot), 16)

    def test_kaikki_tavut_ovat_sanarivilla_yksi(self):
        rivit = {ly.get("number") for m in self.part.findall("measure")
                 for n in m.findall("note") for ly in n.findall("lyric")}
        self.assertEqual(rivit, {"1"})


if __name__ == "__main__":
    unittest.main()
