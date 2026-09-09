"""Testit käsin todennetuille korjauksille.

Painopiste on turvassa: korjaus osoittaa tahtiin ja nuotti-indeksiin, joten
jos lähdetiedosto muuttuu, korjaus voisi osua hiljaa väärään paikkaan. Siksi
jokaisen toimenpiteen pitää kaatua kun lähtötilanne ei ole odotettu.
"""
import unittest
import xml.etree.ElementTree as ET

from korjaa_kasin import (Osa, OSA_I, OSA_I_ALTTO, OSA_I_SOPRAANO,
                          OSA_I_TENORI, OSA_II1, OSA_II6, OSA_II6_TENORI,
                          OSA_II9B, OSA_II10_DIVISI, OSA_II10_KUORO_B,
                          OSA_VII, OSA_VII_TENORI, OSAT_II4, OSAT_II9B_SAT,
                          OSAT_IV, OSAT_V, SAVELLAJIT, Osa,
                          find_part, kuvaa, kuvaa_kesto, load, lue_korkeus,
                          siirra_savellaji, sovella, yksi_sanarivi)


OSA_IV = next(o for o in OSAT_IV if o.osasto == "P4")   # Kuoro B


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

    def test_kopioi_tahti_tuo_nuotit_ja_sanat(self):
        p = part([("C3", [("1", "begin", "Di")]), ("C3", [("1", "end", "es")])],
                 [(None, [])])
        sovella(p, osa([("2", None, "kopioi_tahti", "1")]))
        self.assertEqual(rows(p),
                         [("1", 0, "1", "begin", "Di"), ("1", 1, "1", "end", "es"),
                          ("2", 0, "1", "begin", "Di"), ("2", 1, "1", "end", "es")])

    def test_kopioi_tahti_kaataa_jos_kohteessa_on_nuotteja(self):
        # Jos kohde ei ole pelkkä tauko, ollaan väärässä tahdissa ja
        # kopiointi tuhoaisi musiikkia.
        p = part([("C3", [])], [("D3", [])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("2", None, "kopioi_tahti", "1")]))

    def test_kopioi_tahti_kaataa_jos_lahdetta_ei_ole(self):
        p = part([(None, [])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", None, "kopioi_tahti", "9")]))

    def test_jatka_lisaa_melisman_jatkoviivan(self):
        p = part([("C3", [("1", "end", "ic")])])
        sovella(p, osa([("1", 0, "jatka")]))
        ly = p.find("measure/note/lyric")
        self.assertIsNotNone(ly.find("extend"))

    def test_tavun_siirto_on_poisto_ja_lisays(self):
        p = part([("C3", [("1", "end", "nis")])], [("D3", [])])
        sovella(p, osa([("1", 0, "poista", "nis"),
                        ("2", 0, "lisaa", "end", "nis")]))
        self.assertEqual(rows(p), [("2", 0, "1", "end", "nis")])

    def test_korkeus_vaihtaa_oktaavin(self):
        p = part([("A3", [("1", "end", "la,")])])
        sovella(p, osa([("1", 0, "korkeus", "A3", "A2")]))
        n = p.find("measure/note")
        self.assertEqual(n.findtext("pitch/step"), "A")
        self.assertEqual(n.findtext("pitch/octave"), "2")
        self.assertIsNone(n.find("pitch/alter"))
        # Tavu ei liiku korkeuden mukana.
        self.assertEqual(rows(p), [("1", 0, "1", "end", "la,")])

    def test_korkeus_pudottaa_vanhan_korkeuden_asemointivihjeet(self):
        # <accidental>, <stem> ja default-y on laskettu vanhalle korkeudelle:
        # Lacrymosan t.653 G:llä oli painettu palautusmerkki, joka olisi
        # C:llä väärä, ja varren suunta kääntyy oktaavihypyssä.
        p = part([("G3", [])])
        n = p.find("measure/note")
        n.set("default-y", "-35")
        ET.SubElement(n, "accidental").text = "natural"
        ET.SubElement(n, "stem").text = "up"
        sovella(p, osa([("1", 0, "korkeus", "G3", "C3")]))
        self.assertIsNone(n.find("accidental"))
        self.assertIsNone(n.find("stem"))
        self.assertNotIn("default-y", n.attrib)

    def test_korkeus_kirjoittaa_etumerkin_alteriksi(self):
        p = part([("C3", [])])
        sovella(p, osa([("1", 0, "korkeus", "C3", "Bes2")]))
        n = p.find("measure/note")
        self.assertEqual((n.findtext("pitch/step"), n.findtext("pitch/alter"),
                          n.findtext("pitch/octave")), ("B", "-1", "2"))
        # <pitch>:n lasten järjestys on MusicXML:ssä sidottu.
        self.assertEqual([e.tag for e in n.find("pitch")],
                         ["step", "alter", "octave"])


def rytmi_part(*notes):
    """Osasto yhdellä tahdilla; nuotti on (korkeus, "192/eighth.", aksentti).

    part() ei kirjoita kestoja lainkaan, koska sanakorjaukset eivät niitä
    tarvitse; rytmin ja aksentin toimenpiteet tarvitsevat.
    """
    p = ET.Element("part", {"id": "P1"})
    m = ET.SubElement(p, "measure", {"number": "1"})
    for pitch, kesto, aksentti in notes:
        n = ET.SubElement(m, "note")
        pe = ET.SubElement(n, "pitch")
        ET.SubElement(pe, "step").text = pitch[0]
        ET.SubElement(pe, "octave").text = pitch[1]
        d, loput = kesto.split("/")
        ET.SubElement(n, "duration").text = d
        ET.SubElement(n, "voice").text = "1"
        ET.SubElement(n, "type").text = loput.rstrip(".")
        for _ in range(len(loput) - len(loput.rstrip("."))):
            ET.SubElement(n, "dot")
        if aksentti:
            ET.SubElement(ET.SubElement(ET.SubElement(n, "notations"),
                                        "articulations"), "accent")
    return p


class Rytmi(unittest.TestCase):
    """Nuottiarvon ja aksentin vaihto, Libera men tahdin 88 tapaus."""

    # Tahdin pituus tarkistetaan, joten kestoja vaihdetaan aina pareittain:
    # yksi rivi yksinään ei voi olla kelvollinen korjaus.
    PARI = (("1", 0, "kesto", "256/quarter", "192/eighth."),
            ("1", 1, "kesto", "64/16th", "128/eighth"))

    def rytmipari(self):
        return rytmi_part(("F3", "256/quarter", False),
                          ("E3", "64/16th", False))

    def test_kesto_vaihtaa_arvon_ja_lisaa_pisteen(self):
        p = self.rytmipari()
        sovella(p, osa(self.PARI))
        n, m = p.findall("measure/note")
        self.assertEqual([kuvaa_kesto(n), kuvaa_kesto(m)],
                         ["192/eighth.", "128/eighth"])
        # <dot> tulee MusicXML:ssä heti <type>:n jälkeen.
        self.assertEqual([e.tag for e in n],
                         ["pitch", "duration", "voice", "type", "dot"])
        self.assertNotIn("dot", [e.tag for e in m])

    def test_kesto_poistaa_pisteen(self):
        p = rytmi_part(("F3", "192/eighth.", False), ("E3", "64/16th", False))
        sovella(p, osa([("1", 0, "kesto", "192/eighth.", "64/16th"),
                        ("1", 1, "kesto", "64/16th", "192/eighth.")]))
        self.assertEqual([kuvaa_kesto(n) for n in p.findall("measure/note")],
                         ["64/16th", "192/eighth."])

    def test_kesto_pudottaa_default_x_n(self):
        # Vaakasijainti on laskettu vanhalle rytmille.
        p = self.rytmipari()
        p.find("measure/note").set("default-x", "164")
        sovella(p, osa(self.PARI))
        self.assertNotIn("default-x", p.find("measure/note").attrib)

    def test_tahdin_pituus_tarkistetaan(self):
        """Rytmin uudelleenjako ei saa lyhentää eikä pidentää tahtia.

        Tämä on koko `kesto`-toimenpiteen turvaverkko: yksittäinen rivi
        näyttää aina järkevältä, mutta ryhmän summan pitää täsmätä.
        """
        p = rytmi_part(("F3", "256/quarter", False),
                       ("E3", "256/quarter", False))
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "kesto", "256/quarter", "192/eighth.")]))

    def test_tahdin_pituus_kelpaa_kun_summa_sailyy(self):
        p = self.rytmipari()
        sovella(p, osa(self.PARI))
        self.assertEqual(sum(int(n.findtext("duration"))
                             for n in p.findall("measure/note")), 320)

    def test_aksentti_pois_ja_takaisin(self):
        p = rytmi_part(("E3", "192/eighth.", True), ("E3", "64/16th", False))
        sovella(p, osa([("1", 0, "poista_aksentti"),
                        ("1", 1, "lisaa_aksentti")]))
        akseneja = [len(n.findall("notations/articulations/accent"))
                    for n in p.findall("measure/note")]
        self.assertEqual(akseneja, [0, 1])

    def test_aksentin_lisays_kaataa_jos_se_on_jo(self):
        p = rytmi_part(("E3", "256/quarter", True))
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "lisaa_aksentti")]))

    def test_aksentin_poisto_kaataa_jos_sita_ei_ole(self):
        p = rytmi_part(("E3", "256/quarter", False))
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "poista_aksentti")]))

    def test_kesto_kaataa_jos_vanha_arvo_on_eri(self):
        # Summa säilyisi, joten kaatumisen syy on nimenomaan lähtötilanne.
        p = self.rytmipari()
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "kesto", "192/eighth.", "256/quarter"),
                            ("1", 1, "kesto", "64/16th", "64/16th")]))


class Korkeudenluku(unittest.TestCase):
    """Kirjoitusasu on sama kuin nayta.py:n tulosteessa, jotta laulajan
    raportin tarkistanut voi kopioida sen suoraan taulukkoon."""

    def test_edestakainen(self):
        for teksti in ("C3", "A2", "Bes3", "Fis4", "Ceses2", "Gisis3"):
            with self.subTest(teksti=teksti):
                p = part([("C3", [])])
                sovella(p, osa([("1", 0, "korkeus", "C3", teksti)]))
                self.assertEqual(kuvaa(p.find("measure/note")), teksti)

    def test_tuntematon_asu_kaataa(self):
        for teksti in ("H3", "C", "Cb3", "C3x"):
            with self.subTest(teksti=teksti):
                with self.assertRaises(AssertionError):
                    lue_korkeus(teksti)


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

    def test_jatka_kaataa_jos_tavua_ei_ole(self):
        p = part([("C3", [])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "jatka")]))

    def test_jatka_kaataa_jos_jatkoviiva_on_jo(self):
        p = part([("C3", [("1", "end", "ic")])])
        sovella(p, osa([("1", 0, "jatka")]))
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "jatka")]))

    def test_korkeus_kaataa_jos_vanha_korkeus_on_eri(self):
        p = part([("A3", [])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "korkeus", "A2", "A3")]))

    def test_korkeus_kaataa_tauolla(self):
        p = part([(None, [])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "korkeus", "rest", "A2")]))

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


class SanarivinSiirto(unittest.TestCase):
    """`sanarivi` siirtää koko tahdin tai indeksillä yhden nuotin tavut."""

    def test_siirtaa_koko_tahdin(self):
        p = part([("C3", [("2", "begin", "Te")]), ("D3", [("2", "end", "cet")])])
        sovella(p, osa([("1", None, "sanarivi", "2", "1")]))
        self.assertEqual([r[2] for r in rows(p)], ["1", "1"])

    def test_indeksi_siirtaa_vain_yhden_nuotin(self):
        # Konelukema pudotti sanan keskimmäisen tavun riville 2; koko tahdin
        # siirto kaatuisi, koska rivit ovat sekaisin.
        p = part([("C3", [("1", "begin", "Re")]),
                  ("D3", [("2", "middle", "qui")]),
                  ("E3", [("1", "end", "em,")])])
        sovella(p, osa([("1", 1, "sanarivi", "2", "1")]))
        self.assertEqual([r[2] for r in rows(p)], ["1", "1", "1"])

    def test_indeksi_kaataa_jos_rivi_on_eri(self):
        p = part([("C3", [("1", "begin", "Re")]),
                  ("D3", [("2", "middle", "qui")])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", 0, "sanarivi", "2", "1")]))

    def test_koko_tahti_kaataa_jos_rivit_ovat_sekaisin(self):
        p = part([("C3", [("1", "begin", "Re")]),
                  ("D3", [("2", "middle", "qui")])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", None, "sanarivi", "2", "1")]))


def dynamiikat(m):
    return [(d.get("placement"), c.tag)
            for d in m.findall("direction")
            for dy in d.findall("direction-type/dynamics") for c in dy]


class VaihdetutSanarivit(unittest.TestCase):
    """`vaihda_sanarivit` on `sanarivi`:n divisiversio.

    Kun molemmat äänet ovat samassa osastossa, rivejä ei voi siirtää
    yksitellen: ensimmäinen siirto törmäisi toiseen riviin.
    """

    def puu(self):
        return part([("C4", [("1", "begin", "sal")], "1"),
                     ("G3", [("2", "single", "me,")], "2")])

    def test_vaihtaa_rivit_keskenaan(self):
        p = self.puu()
        sovella(p, osa([("1", None, "vaihda_sanarivit", "1", "2")]))
        self.assertEqual(rows(p), [("1", 0, "2", "begin", "sal"),
                                   ("1", 1, "1", "single", "me,")])

    def test_kirjoittaa_lahteen_oman_kirjoitusasun(self):
        # Sekamuoto ("2" ja "part8verse2" samassa osastossa) sekoittaa
        # MuseScoren rivilaskennan, joten vaihto käyttää sitä asua joka
        # kohderivillä jo on.
        p = part([("C4", [("part8verse1", "begin", "sal")], "1"),
                  ("G3", [("part8verse2", "single", "me,")], "2")])
        sovella(p, osa([("1", None, "vaihda_sanarivit", "1", "2")]))
        self.assertEqual([r[2] for r in rows(p)],
                         ["part8verse2", "part8verse1"])

    def test_pudottaa_default_y_n(self):
        # Arvo on laskettu sille riville jolta tavu lähtee — lähteessä
        # ylä-äänen rivi 2 oli default-y="38" eli viivaston YLÄPUOLELLA.
        p = self.puu()
        for ly in p.findall("measure/note/lyric"):
            ly.set("default-y", "38")
        sovella(p, osa([("1", None, "vaihda_sanarivit", "1", "2")]))
        for ly in p.findall("measure/note/lyric"):
            self.assertNotIn("default-y", ly.attrib)

    def test_kaataa_jos_toista_rivia_ei_ole(self):
        p = part([("C4", [("1", "begin", "sal")], "1")])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", None, "vaihda_sanarivit", "1", "2")]))

    def test_kaataa_jos_tahdissa_on_kolmas_rivi(self):
        p = part([("C4", [("1", "begin", "sal")], "1"),
                  ("G3", [("2", "single", "me,")], "2"),
                  ("E3", [("3", "single", "pelasta")], "2")])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", None, "vaihda_sanarivit", "1", "2")]))


class Dynamiikka(unittest.TestCase):
    def test_lisaa_merkinnan_tahdin_alkuun(self):
        p = part([("C4", [])])
        sovella(p, osa([("1", None, "dynamiikka", "p")]))
        m = p.find("measure")
        self.assertEqual(dynamiikat(m), [("above", "p")])
        # <direction> vaikuttaa sitä seuraaviin nuotteihin, joten se kuuluu
        # ensimmäisen nuotin eteen.
        self.assertEqual([c.tag for c in m], ["direction", "note"])

    def test_yllapitaa_sisennyksen(self):
        # Sisennys on ET:llä text- ja tail-kentissä; ilman sitä merkintä
        # tulostuisi yhtenä rivinä keskelle diffiä.
        p = part([("C4", [])])
        m = p.find("measure")
        m.text = "\n      "
        sovella(p, osa([("1", None, "dynamiikka", "p")]))
        d = m.find("direction")
        self.assertEqual(d.tail, "\n      ")
        self.assertEqual(d.text, "\n        ")

    def test_kaataa_tuntemattomasta_merkista(self):
        p = part([("C4", [])])
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", None, "dynamiikka", "piano")]))

    def test_kaataa_jos_merkinta_on_jo(self):
        p = part([("C4", [])])
        sovella(p, osa([("1", None, "dynamiikka", "p")]))
        with self.assertRaises(AssertionError):
            sovella(p, osa([("1", None, "dynamiikka", "pp")]))


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


class LiberScriptusKokonaisuutena(unittest.TestCase):
    """Puuttuva "Di-es i-rae." kaikilla neljällä äänellä, oikeaa lähdettä vasten."""

    KUVIO = [(None, 256), ("D", 192), ("D", 64), ("D", 256), ("D", 256)]
    SANAT = ["Di", "es", "i", "rae."]

    def test_kaikki_nelja_aanta_saavat_kuvion_tahteihin_68_70_72(self):
        for lahde in OSAT_II4:
            root = load(lahde.mxl)
            p = find_part(root, lahde.osasto)
            sovella(p, lahde)
            tahdit = {m.get("number"): m for m in p.findall("measure")}
            oktaavi = "4" if lahde.nimi in ("Kuoro S", "Kuoro A") else "3"
            for numero in ("68", "70", "72"):
                notes = tahdit[numero].findall("note")
                with self.subTest(aani=lahde.nimi, tahti=numero):
                    self.assertEqual(len(notes), 5)
                    self.assertIsNotNone(notes[0].find("rest"))
                    for n, (step, kesto) in zip(notes, self.KUVIO):
                        self.assertEqual(n.findtext("duration"), str(kesto))
                        if step:
                            self.assertEqual(n.findtext("pitch/step"), step)
                            self.assertEqual(n.findtext("pitch/octave"), oktaavi)
                    self.assertEqual(
                        [n.findtext("lyric/text") for n in notes[1:]], self.SANAT)

    def test_lahdetiedostoa_ei_muuteta(self):
        # Korjaus kirjoittaa aina uuteen tiedostoon; lähde pysyy taukoina.
        root = load(OSAT_II4[0].mxl)
        p = find_part(root, "P5")
        tahdit = {m.get("number"): m for m in p.findall("measure")}
        for numero in ("68", "70", "72"):
            notes = tahdit[numero].findall("note")
            self.assertTrue(all(n.find("rest") is not None for n in notes))


class LacrymosaKokonaisuutena(unittest.TestCase):
    """Väärä sanakerros CPDL:n lähteessä, oikeaa lähdetiedostoa vasten.

    Tahtinumerot ovat tiedoston omia; juokseva numero on lokaali + 623.
    """

    @classmethod
    def setUpClass(cls):
        root = load(OSA_II10_KUORO_B.mxl)
        cls.b = find_part(root, "P8")
        cls.div = find_part(root, "P9")
        sovella(cls.b, OSA_II10_KUORO_B)
        sovella(cls.div, OSA_II10_DIVISI)

    @staticmethod
    def tavut(part, tahti):
        m = next(m for m in part.findall("measure") if m.get("number") == tahti)
        return [(ly.get("number"), ly.findtext("syllabic"), ly.findtext("text"))
                for n in m.findall("note") for ly in n.findall("lyric")
                if ly.findtext("text")]

    def test_loppuu_amen_eika_parce(self):
        # Laulajan alkuperäinen havainto: stemma päättyi "par-ce".
        # "A" on sanan "A-men." ensimmäinen tavu, siis `begin` — se oli
        # `single`, jolloin stemmaan tulostui "A men." ilman väliviivaa.
        self.assertEqual(self.tavut(self.b, "74"), [("1", "begin", "A")])
        self.assertEqual(self.tavut(self.b, "75"), [("1", "end", "men.")])

    def test_tavuketju_on_ehja_koko_loppujaksossa(self):
        """Tahdit 58-75: jokainen sana alkaa `begin`illä ja päättyy `end`iin.

        Tämä oli rikki 2026-09-03 lähtien: `aseta`-rivit vaihtoivat sanat
        mutta jättivät korvattujen sanojen ketjumerkinnät, joten stemmaan
        tulostui "Do-na-e-is" ja "re qui em," ilman väliviivoja.
        """
        virta = [(s, t) for tahti in [str(n) for n in range(58, 76)]
                 for _r, s, t in self.tavut(self.b, tahti)]
        sanat, kesken = [], []
        for syllabic, text in virta:
            if syllabic == "single":
                self.assertEqual(kesken, [], f"{text!r} katkaisi sanan")
                sanat.append(text)
            elif syllabic == "begin":
                self.assertEqual(kesken, [], f"{text!r} katkaisi sanan")
                kesken = [text]
            else:
                self.assertTrue(kesken, f"{text!r} ilman sanan alkua")
                kesken.append(text)
                if syllabic == "end":
                    sanat.append("".join(kesken))
                    kesken = []
        self.assertEqual(kesken, [])
        self.assertEqual(
            " ".join(sanat),
            "Dona eis requiem, dona eis, pie Jesu Domine, "
            "dona eis requiem, requiem, requiem, dona eis requiem. Amen.")

    def test_huic_ergo_parce_deus_kolme_kertaa(self):
        """Tahdit 34-42 (juoksevat 657-665): sama teksti kolmesti.

        Lähde-editio painaa tähän "La-cry-mo-sa ... di-es il-la", mutta se on
        editiovirhe: kohta on limittäinen tulo samalle kuviolle, ja
        tenori/altto/sopraano laulavat siinä "hu-ic er-go". Laulaja raportoi
        saman kuoron nuottikirjasta.
        """
        self.assertEqual([t for _, _, t in self.tavut(self.b, "34")],
                         ["hu", "ic", "er", "go"])
        self.assertEqual([t for _, _, t in self.tavut(self.b, "35")],
                         ["par", "ce", "De", "us,"])
        loput = [t for tahti in ("37", "38", "39", "40", "41", "42")
                 for _, _, t in self.tavut(self.b, tahti)]
        self.assertEqual(loput, ["hu", "ic", "er", "go", "par", "ce",
                                 "De", "us,", "hu", "ic", "er", "go",
                                 "par", "ce", "De", "us."])

    def test_melismojen_jatkoviivat_tahdeissa_34_ja_35(self):
        for tahti in ("34", "35"):
            m = next(x for x in self.b.findall("measure")
                     if x.get("number") == tahti)
            ly = m.findall("note")[1].find("lyric")
            with self.subTest(tahti=tahti):
                self.assertIsNotNone(ly.find("extend"))

    def test_dona_eis_requiem_tahdeissa_58_59(self):
        self.assertEqual([t for _, _, t in self.tavut(self.b, "58")],
                         ["Do", "na", "e", "is", "re", "qui"])
        self.assertEqual([t for _, _, t in self.tavut(self.b, "59")],
                         ["em,", "do", "na", "e"])

    def test_tahdin_65_kaksi_tavutonta_nuottia_saivat_tavun(self):
        self.assertEqual([t for _, _, t in self.tavut(self.b, "65")],
                         ["re", "qui"])

    def test_divisin_ylaaani_laulaa_pie_jesu_domine(self):
        # Lähde-PDF:n sivu 11: ylä-äänen sanat viivaston yläpuolella.
        self.assertEqual(
            [t for _, _, t in self.tavut(self.div, "54")], ["Pi", "e", "Je"])
        self.assertEqual(
            [t for _, _, t in self.tavut(self.div, "55")], ["su", "Do", "mi"])
        self.assertEqual(self.tavut(self.div, "56"), [("1", "end", "ne,")])

    def test_divisin_sanarivit_ovat_aanten_mukaisessa_jarjestyksessa(self):
        """Ylä-ääni ylemmälle riville, ala-ääni alemmalle (t.54-56).

        Naulattu siksi, että lähdetiedosto on tässä toisin päin: se on
        kaksi erillistä osastoa, kumpikin numeroi omat tavunsa tietämättä
        toisesta, ja niin ala-ääni päätyi riville 1 ja ylä-ääni riville 2.
        Stemmassa ne osuvat samalle viivastolle, jolloin rivijärjestys
        kertoo kummasta äänestä on kyse — ja laulaja luki sen väärin päin.
        Lähdesivu 11 painaa ylä-äänen sanat viivaston yläpuolelle.
        """
        for tahti in ("54", "55", "56"):
            with self.subTest(tahti=tahti):
                self.assertEqual(
                    {r for r, _, _ in self.tavut(self.div, tahti)}, {"1"})
                self.assertEqual(
                    {r for r, _, _ in self.tavut(self.b, tahti)}, {"2"})

    def test_tahti_677_saa_pianon(self):
        """Laulajan pyyntö: yhdentoista tahdin tauon jälkeinen tulo on hiljaa.

        Lähteessä merkintää ei ole tällä viivastolla, mutta sama jakso on
        merkitty hiljaiseksi joka muualla: kuorosopraano pp t.678, solistit
        ja piano t.679, ja kuoron oma seuraava merkintä on mf vasta t.681.
        """
        m = next(m for m in self.b.findall("measure") if m.get("number") == "54")
        self.assertEqual(dynamiikat(m), [("above", "p")])
        # Ennen ensimmäistä nuottia, mutta <print>:n jälkeen.
        tagit = [c.tag for c in m]
        self.assertLess(tagit.index("direction"), tagit.index("note"))

    def test_kuorobasso_on_muualla_sanarivilla_yksi(self):
        # Rivi 2 on P8:lla vain divisin kolmessa tahdissa; muuten se laulaa
        # yksin ja kuuluu ylimmälle riville.
        poikkeus = {"54", "55", "56"}
        rivit = {m.get("number"): {ly.get("number") for n in m.findall("note")
                                   for ly in n.findall("lyric")}
                 for m in self.b.findall("measure")}
        for tahti, r in rivit.items():
            if r and tahti not in poikkeus:
                with self.subTest(tahti=tahti):
                    self.assertEqual(r, {"1"})

    def test_lahdetiedostoa_ei_muuteta(self):
        # Lähde on CPDL:n koskematon vienti ja siinä on edelleen väärä teksti.
        root = load(OSA_II10_KUORO_B.mxl)
        self.assertEqual(self.tavut(find_part(root, "P8"), "75"),
                         [("1", "end", "ce")])
        self.assertEqual([t for _, _, t in self.tavut(find_part(root, "P9"), "54")],
                         ["La", "cry", "mo"])

    def test_tahti_653_on_c_eika_g(self):
        """Painettu sivu 6 on tässä väärässä, ks. korjauksen kommentti.

        Naulattu siksi, että tämä kohta on kertaalleen tarkistettu ja
        ratkaistu G:n hyväksi juuri siksi että painettu palautusmerkki
        näytti todistavan sen. Tiedoston sisäiset todisteet — bassosolisti
        ja pianon vasen käsi — sanovat C.
        """
        p = find_part(load(OSA_II10_KUORO_B.mxl), "P8")
        tahdit = {m.get("number"): m for m in p.findall("measure")}
        alkuun = tahdit["30"].findall("note")[0]
        self.assertEqual(kuvaa(alkuun), "G3")
        self.assertEqual(alkuun.findtext("accidental"), "natural")

        p = find_part(load(OSA_II10_KUORO_B.mxl), "P8")
        sovella(p, OSA_II10_KUORO_B)
        tahdit = {m.get("number"): m for m in p.findall("measure")}
        korjattu = tahdit["30"].findall("note")[0]
        self.assertEqual(kuvaa(korjattu), "C3")
        self.assertIsNone(korjattu.find("accidental"))
        # Sama sävel kuin bassosolistilla, joka laulaa jakson unisonossa.
        solisti = find_part(load(OSA_II10_KUORO_B.mxl), "P4")
        soolo = {m.get("number"): m for m in solisti.findall("measure")}
        self.assertEqual(kuvaa(soolo["30"].findall("note")[0]), "C3")


class Tavutus(unittest.TestCase):
    """`tavutus` korjaa ketjumerkinnät annetun sanajaon mukaisiksi.

    Operaatio on olemassa siksi, että `aseta` kantaa korvatun sanan
    ketjumerkinnän: kun Lacrymosan sanat vaihdettiin 2026-09-03,
    "La-cry-mo-sa"-sanan `middle` jäi sanan "do-na" toiselle tavulle ja
    stemmaan tulostui "Do-na-e-is" ja "re qui em," ilman väliviivoja.
    """

    @staticmethod
    def osasto(*tavut):
        """(tahti, syllabic, teksti) -> osasto, yksi nuotti per tavu."""
        part = ET.Element("part", {"id": "P1"})
        tahdit = {}
        for tahti, syllabic, text in tavut:
            m = tahdit.get(tahti)
            if m is None:
                m = tahdit[tahti] = ET.SubElement(part, "measure",
                                                  {"number": tahti})
            n = ET.SubElement(m, "note")
            ly = ET.SubElement(n, "lyric", {"number": "1"})
            if syllabic is not None:
                ET.SubElement(ly, "syllabic").text = syllabic
            if text is not None:
                ET.SubElement(ly, "text").text = text
        return part

    @staticmethod
    def ketju(part):
        return [(ly.findtext("syllabic"), ly.findtext("text"))
                for m in part.findall("measure") for n in m.findall("note")
                for ly in n.findall("lyric")]

    def aja(self, part, jako, tahti="1"):
        osa = Osa(mxl="x", out="y", osasto="P1", nimi="X",
                  yksi_sanarivi=False,
                  korjaukset=((tahti, None, "tavutus", jako),))
        return sovella(part, osa)

    def test_ketju_korjautuu_sanajaon_mukaiseksi(self):
        part = self.osasto(("1", "middle", "Do"), ("1", "single", "na"),
                           ("2", "begin", "e"), ("2", "middle", "is"))
        self.aja(part, "Do-na e-is")
        self.assertEqual(self.ketju(part),
                         [("begin", "Do"), ("end", "na"),
                          ("begin", "e"), ("end", "is")])

    def test_kolmitavuinen_saa_middlen(self):
        part = self.osasto(("1", "single", "re"), ("1", "single", "qui"),
                           ("1", "middle", "em,"))
        self.aja(part, "re-qui-em,")
        self.assertEqual([s for s, _t in self.ketju(part)],
                         ["begin", "middle", "end"])

    def test_yksitavuinen_on_single(self):
        part = self.osasto(("1", "begin", "et"))
        self.aja(part, "et")
        self.assertEqual(self.ketju(part), [("single", "et")])

    def test_tekstit_eivat_muutu(self):
        part = self.osasto(("1", "middle", "Do"), ("1", "single", "na"))
        self.aja(part, "Do-na")
        self.assertEqual([t for _s, t in self.ketju(part)], ["Do", "na"])

    def test_vaara_tavu_pysayttaa_ajon(self):
        # Hiljaa väärään paikkaan osuva korjaus on pahempi kuin pysähtynyt
        # ajo: rivi tarkistaa jokaisen tavun tekstin.
        part = self.osasto(("1", "begin", "Do"), ("1", "end", "na"))
        with self.assertRaises(AssertionError) as e:
            self.aja(part, "e-is")
        self.assertIn("odotettiin tavua", str(e.exception))

    def test_liian_pitka_jako_pysayttaa_ajon(self):
        part = self.osasto(("1", "begin", "Do"), ("1", "end", "na"))
        with self.assertRaises(AssertionError) as e:
            self.aja(part, "Do-na e-is")
        self.assertIn("tavua annettu", str(e.exception))

    def test_melisman_jatkoviiva_ohitetaan(self):
        # Pelkän <extend/>:n sisältävä lyriikka ei ole tavu; jos se
        # laskettaisiin, jako siirtyisi yhden askeleen väärään kohtaan.
        part = self.osasto(("1", "middle", "Do"), ("1", None, None),
                           ("1", "single", "na"))
        self.aja(part, "Do-na")
        self.assertEqual(self.ketju(part),
                         [("begin", "Do"), (None, None), ("end", "na")])


class DiesIraeJaLiberaMeSamaKuvio(unittest.TestCase):
    """Sama "puolinuotti + oktaavia alempi kahdeksasosa" kahdessa osassa.

    Laulaja raportoi kummankin erikseen (II·1 t.28 ja VII t.72), ja
    kuorotiedostot vahvistivat kummankin. Kuvion ensimmäinen esiintymä
    (t.24 ja t.68) EI putoa oktaavia kummassakaan osassa, ja se on
    molemmissa tiedostoissa niin — poikkeus on aito eikä vika, joten se
    naulataan tähän ettei sitä "korjata" myöhemmin.
    """

    def kuvio(self, osa_, tahti):
        p = find_part(load(osa_.mxl), osa_.osasto)
        sovella(p, osa_)
        tahdit = {m.get("number"): m for m in p.findall("measure")}
        return [kuvaa(n) for n in tahdit[tahti].findall("note")[:2]]

    def test_dies_iraen_tahti_28_putoaa_oktaavin(self):
        self.assertEqual(self.kuvio(OSA_II1, "28"), ["A3", "A2"])

    def test_dies_iraen_tahti_24_ei_putoa(self):
        self.assertEqual(self.kuvio(OSA_II1, "24"), ["A3", "A3"])

    def test_libera_men_tahti_72_putoaa_oktaavin(self):
        self.assertEqual(self.kuvio(OSA_VII, "72"), ["A3", "A2"])

    def test_libera_men_tahti_68_ei_putoa(self):
        self.assertEqual(self.kuvio(OSA_VII, "68"), ["A3", "A3"])


class MuutOsatKokonaisuutena(unittest.TestCase):
    """Rex tremendae, Sanctus ja Libera me oikeita lähdetiedostoja vasten."""

    def tavut(self, osa_, tahti):
        p = find_part(load(osa_.mxl), osa_.osasto)
        sovella(p, osa_)
        tahdit = {m.get("number"): m for m in p.findall("measure")}
        return [(ly.findtext("syllabic"), ly.findtext("text"))
                for n in tahdit[tahti].findall("note")
                for ly in n.findall("lyric")]

    def test_rex_tremendae_laulaa_salva_me(self):
        # t.44-46 = juokseva 365-367: "sal-va me, sal-va me,"
        self.assertEqual(self.tavut(OSA_II6, "45"),
                         [("single", "me,"), ("begin", "sal"), ("end", "va")])

    def test_rex_tremendae_lahteessa_on_le(self):
        p = find_part(load(OSA_II6.mxl), "P8")
        tahdit = {m.get("number"): m for m in p.findall("measure")}
        self.assertEqual(tahdit["45"].findtext("note/lyric/text"), "le,")

    def test_sanctus_laulaa_coeli_et_terra_kaikilla_kolmella(self):
        # Sama puute altolla, tenorilla ja bassolla; sopraano oli jo oikein.
        for osa_ in OSAT_IV:
            with self.subTest(aani=osa_.nimi):
                self.assertEqual(self.tavut(osa_, "99"), [("begin", "coe")])
                self.assertEqual(self.tavut(osa_, "100")[0], ("end", "li"))
        self.assertEqual([o.osasto for o in OSAT_IV], ["P2", "P3", "P4"])

    def test_sanctus_sopraano_oli_jo_oikein(self):
        p = find_part(load(OSA_IV.mxl), "P1")
        tahdit = {m.get("number"): m for m in p.findall("measure")}
        self.assertEqual(tahdit["99"].findtext("note/lyric/text"), "coe")

    def test_sanctus_kuoro_ii_laulaa_hosannaa_eika_koskettu(self):
        # P5-P8 laulaa samassa kohdassa eri tekstiä.
        osastot = {o.osasto for o in OSAT_IV}
        self.assertTrue(osastot.isdisjoint({"P5", "P6", "P7", "P8"}))

    def test_sanctus_kirjoitusasu_on_lahteen_oma(self):
        # Sama lause t.27 kirjoittaa "coe", ei "cae"; pysytään siinä.
        p = find_part(load(OSA_IV.mxl), "P4")
        tahdit = {m.get("number"): m for m in p.findall("measure")}
        self.assertIn("coe", [ly.findtext("text")
                              for n in tahdit["27"].findall("note")
                              for ly in n.findall("lyric")])

    def test_libera_me_tahti_98_laulaa_dies(self):
        # Tavut tulevat 1. ja 3. nuotille; 2. on melisman sisällä.
        p = find_part(load(OSA_VII.mxl), OSA_VII.osasto)
        sovella(p, OSA_VII)
        tahdit = {m.get("number"): m for m in p.findall("measure")}
        notes = tahdit["98"].findall("note")
        self.assertEqual([n.findtext("lyric/text") for n in notes],
                         ["di", None, "es"])
        # Sama jako kuin basson omassa tahdissa 100.
        notes = tahdit["100"].findall("note")
        self.assertEqual([n.findtext("lyric/text") for n in notes],
                         ["di", None, "es"])

    def test_libera_me_tahti_88_saa_kuorotiedoston_rytmin(self):
        """Toinen pisteellinen kuvio tulee tavuille "et a" eikä "a ma".

        Kohta on kuorobasson yksinlaulua, eikä osalle 16 ole lähde-PDF:ää,
        joten ainoa toinen lähde on kuoron oma tiedosto. Sen tahti 55 on
        tämä, ja sen naapuritahdit 54 ja 56 ovat meidän 87 ja 89 nuotilleen
        ja aksentilleen samat — ero on täsmälleen yhden tahdin mitassa.
        """
        p = find_part(load(OSA_VII.mxl), OSA_VII.osasto)
        sovella(p, OSA_VII)
        tahdit = {m.get("number"): m for m in p.findall("measure")}
        notes = tahdit["88"].findall("note")
        self.assertEqual([kuvaa(n) for n in notes],
                         ["Ges3", "Ges3", "F3", "F3", "Ees3", "D3"])
        self.assertEqual([kuvaa_kesto(n) for n in notes],
                         ["192/eighth.", "64/16th", "192/eighth.",
                          "64/16th", "256/quarter", "256/quarter"])
        # Aksentit iskuilla, ei uudella 16-osalla.
        self.assertEqual([bool(n.findall("notations/articulations/accent"))
                          for n in notes],
                         [True, False, True, False, True, True])
        # Tavut pysyivät samoilla nuoteilla ja tahti täyttyy täsmälleen.
        self.assertEqual([n.findtext("lyric/text") for n in notes],
                         ["ma", "gna", "et", "a", "ma", "ra"])
        self.assertEqual(sum(int(n.findtext("duration")) for n in notes), 1024)

    def test_libera_me_tenori_saa_saman_dies_kuin_basso(self):
        p = find_part(load(OSA_VII_TENORI.mxl), OSA_VII_TENORI.osasto)
        sovella(p, OSA_VII_TENORI)
        tahdit = {m.get("number"): m for m in p.findall("measure")}
        # Tenorilla on tahdissa 98 kaksi nuottia, ei kolmea kuin bassolla.
        self.assertEqual([n.findtext("lyric/text")
                          for n in tahdit["98"].findall("note")], ["di", "es"])
        # Sama kuvio ja sama jako kuin tenorin omassa tahdissa 100.
        self.assertEqual([n.findtext("lyric/text")
                          for n in tahdit["100"].findall("note")], ["di", "es"])

    def test_libera_me_tahti_93_ei_muutu(self):
        """Laulaja sanoi tahdiksi 93, mutta 93 on oikein ja 98 oli väärä.

        Tämä on tässä ettei numeroa 93 korjattaisi myöhemmin "laulajan
        mukaan": 93 laulaa "il-la," aivan kuten saman kuvion 68 ja 72.
        """
        self.assertEqual(self.tavut(OSA_VII, "93"),
                         [("begin", "il"), ("end", "la,")])

    def test_lahdetiedostoja_ei_muuteta(self):
        for osa_, tahti, odotus in ((OSA_IV, "99", []),
                                    (OSA_VII, "98", []),
                                    (OSA_VII_TENORI, "98", [])):
            p = find_part(load(osa_.mxl), osa_.osasto)
            tahdit = {m.get("number"): m for m in p.findall("measure")}
            with self.subTest(osa=osa_.mxl):
                self.assertEqual([ly.findtext("text")
                                  for n in tahdit[tahti].findall("note")
                                  for ly in n.findall("lyric")], odotus)


def savellajipuu(*osastot):
    """Puu, jossa jokaisella osastolla on tahdit 1-3 ja sävellaji annetussa.

    osasto on (id, tahti tai None, fifths).
    """
    root = ET.Element("score-partwise")
    for pid, tahti, fifths in osastot:
        p = ET.SubElement(root, "part", {"id": pid})
        for numero in ("1", "2", "3"):
            m = ET.SubElement(p, "measure", {"number": numero})
            if numero == tahti:
                a = ET.SubElement(m, "attributes")
                ET.SubElement(ET.SubElement(a, "key"), "fifths").text = str(fifths)
                ET.SubElement(a, "staff-details")
            ET.SubElement(ET.SubElement(m, "note"), "rest")
    return root


def savellajit(root):
    return {(p.get("id"), m.get("number")): m.findtext("attributes/key/fifths")
            for p in root.findall("part") for m in p.findall("measure")
            if m.find("attributes/key") is not None}


class SavellajinSiirto(unittest.TestCase):
    """Sävellajin vaihto siirtyy koko tiedostossa tai ei ollenkaan."""

    def test_siirtyy_kaikissa_osastoissa(self):
        root = savellajipuu(("P1", "3", 0), ("P2", "3", 0))
        siirra_savellaji(root, "3", "2", 0)
        self.assertEqual(savellajit(root), {("P1", "2"): "0", ("P2", "2"): "0"})

    def test_vanhaan_tahtiin_ei_jaa_vaihtoa_mutta_muu_jaa(self):
        root = savellajipuu(("P1", "3", 0))
        siirra_savellaji(root, "3", "2", 0)
        vanha = root.findall("part/measure")[2]
        self.assertIsNone(vanha.find("attributes/key"))
        self.assertIsNotNone(vanha.find("attributes/staff-details"))

    def test_attributes_menee_nuottien_edelle(self):
        root = savellajipuu(("P1", "3", 0))
        siirra_savellaji(root, "3", "2", 0)
        uusi = root.findall("part/measure")[1]
        self.assertEqual([c.tag for c in uusi], ["attributes", "note"])

    def test_tyhjaksi_jaanyt_attributes_poistetaan(self):
        root = savellajipuu(("P1", "3", 0))
        vanha = root.findall("part/measure")[2]
        vanha.find("attributes").remove(vanha.find("attributes/staff-details"))
        siirra_savellaji(root, "3", "2", 0)
        self.assertIsNone(vanha.find("attributes"))

    def test_kaataa_jos_vaihtoa_ei_ole(self):
        root = savellajipuu(("P1", "3", 0), ("P2", None, 0))
        with self.assertRaises(AssertionError):
            siirra_savellaji(root, "3", "2", 0)

    def test_kaataa_jos_savellaji_on_eri(self):
        root = savellajipuu(("P1", "3", -1))
        with self.assertRaises(AssertionError):
            siirra_savellaji(root, "3", "2", 0)

    def test_kaataa_jos_kohteessa_on_jo_vaihto(self):
        root = savellajipuu(("P1", "3", 0))
        m = root.findall("part/measure")[1]
        a = ET.SubElement(m, "attributes")
        ET.SubElement(ET.SubElement(a, "key"), "fifths").text = "0"
        with self.assertRaises(AssertionError):
            siirra_savellaji(root, "3", "2", 0)

    def test_kaataa_jos_tahtia_ei_ole(self):
        root = savellajipuu(("P1", "3", 0))
        with self.assertRaises(AssertionError):
            siirra_savellaji(root, "3", "9", 0)

    def test_valmis_osasto_jaa_ennalleen(self):
        # P2:lla vaihto on jo kohdetahdissa 2; sitä ei siirretä.
        root = savellajipuu(("P1", "3", 0), ("P2", "2", 0))
        siirra_savellaji(root, "3", "2", 0, valmiit=("P2",))
        self.assertEqual(savellajit(root), {("P1", "2"): "0", ("P2", "2"): "0"})

    def test_valmis_kaataa_jos_vaihtoa_ei_ole_kohteessa(self):
        root = savellajipuu(("P1", "3", 0), ("P2", "3", 0))
        with self.assertRaises(AssertionError):
            siirra_savellaji(root, "3", "2", 0, valmiit=("P2",))

    def test_valmis_kaataa_jos_lahtotahdissa_on_yha_vaihto(self):
        root = savellajipuu(("P1", "3", 0), ("P2", "2", 0))
        m = root.findall("part")[1].findall("measure")[2]
        a = ET.SubElement(m, "attributes")
        ET.SubElement(ET.SubElement(a, "key"), "fifths").text = "0"
        with self.assertRaises(AssertionError):
            siirra_savellaji(root, "3", "2", 0, valmiit=("P2",))


class OsanISavellajit(unittest.TestCase):
    """Osan I purku on tahdissa 56, ei 59, oikeaa lähdetiedostoa vasten.

    Lähde-PDF:n sivu 3 painaa kuusi palautusmerkkiä x:llä 368, ja tahti 56
    alkaa x:llä 367; tahti 59 on vasta seuraavan järjestelmän ensimmäinen.
    Konelukema luki sävellajin uudestaan järjestelmän alusta ja kirjasi
    vaihdon sinne. Naulattu siksi, että 59 on tiedoston oma lukema ja
    näyttää siltä oikealta, ja koska laulaja luki purun tyhjästä tahdista.
    """

    @classmethod
    def setUpClass(cls):
        cls.savellajit = [s for s in SAVELLAJIT if s.mxl == OSA_I.mxl]
        cls.root = load(OSA_I.mxl)
        for s in cls.savellajit:
            for mista, mihin, fifths in s.siirrot:
                siirra_savellaji(cls.root, mista, mihin, fifths, s.valmiit)

    def test_siirtoja_on_kaksi(self):
        self.assertEqual([s.siirrot for s in self.savellajit],
                         [(("59", "56", 0),), (("35", "28", -1),)])

    def test_f_duuri_alkaa_tahdista_28_kaikissa_osastoissa(self):
        # Sivun 2 mitattu purku ja b ovat x:llä 138-147 ja tahti 28 alkaa
        # x:llä 135. Konelukema kirjasi vaihdon tahtiin 35 viidessätoista
        # osastossa ja tahtiin 28 vain kuorotenoriin ja -bassoon.
        merkityt = savellajit(self.root)
        for pid in [p.get("id") for p in self.root.findall("part")]:
            with self.subTest(osasto=pid):
                self.assertEqual(merkityt.get((pid, "28")), "-1")
                self.assertIsNone(merkityt.get((pid, "35")))

    def test_valmiiksi_merkityt_ovat_kuorotenori_ja_basso(self):
        (_, f_duuri) = self.savellajit
        self.assertEqual(f_duuri.valmiit, ("P15", "P16"))
        # Ja lähteessä ne todella ovat jo tahdissa 28, muut eivät.
        merkityt = savellajit(load(OSA_I.mxl))
        self.assertEqual(merkityt.get(("P15", "28")), "-1")
        self.assertEqual(merkityt.get(("P16", "28")), "-1")
        self.assertEqual(merkityt.get(("P13", "35")), "-1")
        self.assertIsNone(merkityt.get(("P13", "28")))

    def test_kaikki_seitsemantoista_osastoa_vaihtavat_tahdissa_56(self):
        merkityt = savellajit(self.root)
        osastot = [p.get("id") for p in self.root.findall("part")]
        self.assertEqual(len(osastot), 17)
        for pid in osastot:
            with self.subTest(osasto=pid):
                self.assertEqual(merkityt.get((pid, "56")), "0")
                self.assertIsNone(merkityt.get((pid, "59")))

    def test_muut_vaihdot_pysyvat_paikallaan(self):
        # Sivu 1 antaa kolme ristiä tahtiin 17 ja sivu 3 tahtiin 67; kumpikin
        # on mitattu samalla tavalla ja kumpikin oli jo oikein.
        merkityt = savellajit(self.root)
        self.assertEqual(merkityt[("P16", "17")], "3")
        self.assertEqual(merkityt[("P16", "67")], "3")

    def test_lahdetiedostoa_ei_muuteta(self):
        merkityt = savellajit(load(OSA_I.mxl))
        self.assertEqual(merkityt[("P16", "59")], "0")
        self.assertNotIn(("P16", "56"), merkityt)


class RexTremendaeKokonaisuutena(unittest.TestCase):
    """Osa II·6 oikeaa lähdetiedostoa vasten. Juokseva numero on lokaali + 321."""

    @classmethod
    def setUpClass(cls):
        cls.part = find_part(load(OSA_II6.mxl), OSA_II6.osasto)
        sovella(cls.part, OSA_II6)

    @staticmethod
    def tavut(part, tahti):
        m = next(m for m in part.findall("measure") if m.get("number") == tahti)
        return [(ly.get("number"), ly.findtext("syllabic"), ly.findtext("text"))
                for n in m.findall("note") for ly in n.findall("lyric")
                if ly.findtext("text")]

    def teksti(self, *tahdit):
        return " ".join(t for tahti in tahdit
                        for _, _, t in self.tavut(self.part, tahti))

    def test_kumpikin_jakso_lukee_sakeiston_lapi(self):
        """Säkeistö on kolme säettä, ja jokainen kuuluu jaksoon kertaalleen.

        Ennen korjausta ensimmäinen säe oli t.336-341 kolmesti ja kolmas
        säe puuttui, ja t.362-363 kertasi toisen säkeen. Naulattu siksi,
        että lähdetiedostossa kaikki neljä paikkaa ovat samaa kuviota eikä
        kuvio itse kerro kumpi säe siinä on.
        """
        # t.336-341: Rex ... Rex ... qui salvandos salvas gratis
        self.assertEqual(self.teksti("15", "16"),
                         "Rex tre men dae ma je sta tis,")
        self.assertEqual(self.teksti("17", "18"),
                         "Rex tre men dae ma je sta tis,")
        self.assertEqual(self.teksti("19", "20"),
                         "qui sal van dos sal vas gra tis,")
        # t.356-363: rex ... rex ... qui salvandos ... salva me fons pietatis
        self.assertEqual(self.teksti("35", "36"),
                         "rex tre men dae ma je sta tis,")
        self.assertEqual(self.teksti("39", "40"),
                         "qui sal van dos sal vas gra tis,")
        self.assertEqual(self.teksti("41", "42"),
                         "sal va me, fons pi e ta tis,")

    def test_tavutus_on_kopioitu_tiedoston_omista_paikoista(self):
        # Kumpikin säe on jo tiedostossa tälle samalle kuviolle
        # merkittynä; korjaus ei keksi tavutusta vaan toistaa sen.
        for korjattu, malli in (("19", "39"), ("20", "40"),
                                ("41", "23"), ("42", "24")):
            with self.subTest(tahti=korjattu):
                self.assertEqual(self.tavut(self.part, korjattu),
                                 self.tavut(self.part, malli))

    def test_divisin_sanarivit_ovat_aanten_mukaisessa_jarjestyksessa(self):
        """Ylä-ääni (ykkösbasso) riville 1, ala-ääni riville 2 (t.367-369).

        Lähde on toisin päin, ja sen lisäksi eri puolilla viivastoa: rivin 2
        default-y="38" nosti ylä-äänen tavut viivaston yläpuolelle. Sama vika
        kuin Lacrymosan t.677-679, mutta yhdessä osastossa kahden sijaan.
        """
        for tahti in ("46", "47", "48"):
            with self.subTest(tahti=tahti):
                m = next(m for m in self.part.findall("measure")
                         if m.get("number") == tahti)
                rivit = {n.findtext("voice"): {ly.get("number")
                                               for ly in n.findall("lyric")}
                         for n in m.findall("note") if n.findall("lyric")}
                self.assertEqual(rivit["1"], {"part8verse1"})
                self.assertEqual(rivit["2"], {"part8verse2"})
                self.assertEqual(
                    [ly.get("default-y") for ly in m.findall("note/lyric")],
                    [None] * len(m.findall("note/lyric")))

    def test_lahdetiedostoa_ei_muuteta(self):
        alkuperainen = find_part(load(OSA_II6.mxl), OSA_II6.osasto)
        self.assertEqual(self.tavut(alkuperainen, "19")[0],
                         ("part8verse1", "single", "Rex"))


class OsanIKuorosopraanoAlttoJaTenori(unittest.TestCase):
    """Osan I kolme muuta kuoroääntä: sanat, sanarivit ja sävelet.

    Kaikki alla oleva on todennettu kahdesta lähteestä: lähde-PDF:n
    tekstikerroksesta ja nuottifontin merkkien koordinaateista, sekä kuoron
    omasta MuseScore-tiedostosta. Naulattu, koska korjaukset osoittavat
    nuotti-indeksiin ja tämä osa on konelukema.
    """

    @classmethod
    def setUpClass(cls):
        root = load(OSA_I.mxl)
        cls.osat = {}
        for osa_ in (OSA_I_SOPRAANO, OSA_I_ALTTO, OSA_I_TENORI):
            part = find_part(root, osa_.osasto)
            sovella(part, osa_)
            cls.osat[osa_.nimi] = part

    def tavu(self, nimi, tahti, nuotti):
        m = next(m for m in self.osat[nimi].findall("measure")
                 if m.get("number") == tahti)
        ly = m.findall("note")[nuotti].findall("lyric")
        return None if not ly else (ly[0].get("number"),
                                    ly[0].findtext("syllabic"),
                                    ly[0].findtext("text"))

    def savel(self, nimi, tahti, nuotti):
        m = next(m for m in self.osat[nimi].findall("measure")
                 if m.get("number") == tahti)
        return kuvaa(m.findall("note")[nuotti])

    def test_sopraano_laulaa_et_lux_perpetua(self):
        self.assertEqual(self.tavu("Kuoro S", "21", 0), ("1", "single", "et"))
        self.assertEqual(self.tavu("Kuoro S", "21", 1), ("1", "single", "lux"))
        self.assertEqual(self.tavu("Kuoro S", "22", 1), ("1", "middle", "tu"))

    def test_altto_laulaa_et_lux_perpetua(self):
        self.assertEqual(self.tavu("Kuoro A", "21", 0), ("1", "single", "et"))
        self.assertEqual(self.tavu("Kuoro A", "21", 1), ("1", "single", "lux"))
        self.assertEqual(self.tavu("Kuoro A", "21", 2), ("1", "begin", "per"))
        self.assertEqual(self.tavu("Kuoro A", "22", 0), ("1", "middle", "pe"))

    def test_tenori_laulaa_et_lux_perpetua_kahdesti(self):
        self.assertEqual(self.tavu("Kuoro T", "17", 2), ("1", "single", "et"))
        self.assertEqual(self.tavu("Kuoro T", "18", 0), ("1", "single", "lux"))
        self.assertEqual(self.tavu("Kuoro T", "19", 2), ("1", "begin", "per"))
        self.assertEqual(self.tavu("Kuoro T", "67", 2), ("1", "single", "et"))
        self.assertEqual(self.tavu("Kuoro T", "70", 0), ("1", "middle", "pe"))

    def test_tenori_laulaa_luceat(self):
        self.assertEqual(self.tavu("Kuoro T", "76", 1), ("1", "begin", "lu"))

    def test_alton_tahdissa_37_on_et(self):
        self.assertEqual(self.tavu("Kuoro A", "37", 1), ("1", "single", "et"))

    def test_alton_tahti_39_kertaa_tibi_reddeturin(self):
        # `korjaa_sanat.py` ehdottaa tähän "vo":ta eikä sovella sitä.
        # Ehdotus on väärä, joten tavu naulataan ennalleen.
        self.assertEqual(self.tavu("Kuoro A", "39", 3), ("1", "single", "ti"))

    def test_dynamiikkamerkinnat_eivat_ole_tavuina(self):
        for nimi in ("Kuoro A", "Kuoro T"):
            with self.subTest(aani=nimi):
                m = next(m for m in self.osat[nimi].findall("measure")
                         if m.get("number") == "136")
                self.assertEqual(
                    [ly.findtext("text") for n in m.findall("note")
                     for ly in n.findall("lyric")], ["e", "le", "i"])

    def test_sopraanon_te_decet_on_sanarivilla_yksi(self):
        for tahti, nuotti, odotus in ((("35"), 0, ("1", "begin", "hym")),
                                      (("41"), 2, ("1", "begin", "vo")),
                                      (("59"), 2, ("1", "middle", "qui"))):
            with self.subTest(tahti=tahti):
                self.assertEqual(self.tavu("Kuoro S", tahti, nuotti), odotus)

    def test_alton_ja_tenorin_tavut_ovat_kaikki_sanarivilla_yksi(self):
        for nimi in ("Kuoro A", "Kuoro T"):
            with self.subTest(aani=nimi):
                rivit = {ly.get("number")
                         for m in self.osat[nimi].findall("measure")
                         for n in m.findall("note") for ly in n.findall("lyric")}
                self.assertEqual(rivit, {"1"})

    def test_tahdit_28_34_ovat_f_duurissa(self):
        # Konelukema luki ne kolmen ristin sävellajissa; kuoron oma tiedosto
        # ja siirretty sävellaji kertovat F-duurin.
        self.assertEqual([self.savel("Kuoro S", "28", i) for i in (0, 1)],
                         ["F4", "F4"])
        self.assertEqual(self.savel("Kuoro S", "34", 0), "C5")
        self.assertEqual([self.savel("Kuoro A", "32", i) for i in (0, 1)],
                         ["F4", "G4"])
        self.assertEqual([self.savel("Kuoro A", "33", i) for i in (0, 1)],
                         ["G4", "F4"])

    def test_tahdit_28_34_muut_savelet_pysyvat(self):
        # A ja E eivät ole ristillisiä kolmen ristin sävellajissa, joten
        # niiden on täytynyt olla oikein jo ennen korjausta.
        self.assertEqual([self.savel("Kuoro S", "34", i) for i in (1, 2)],
                         ["D5", "E5"])
        self.assertEqual(self.savel("Kuoro A", "32", 2), "A4")
        self.assertEqual([self.savel("Kuoro A", "34", i) for i in (0, 1)],
                         ["E4", "A4"])

    def test_sopraanon_luceat_paattyy_c_duurin_ceehen(self):
        self.assertEqual([self.savel("Kuoro S", "76", i) for i in (1, 2, 3)],
                         ["E4", "A4", "C5"])

    def test_tenorin_tahdissa_43_on_risti(self):
        self.assertEqual([self.savel("Kuoro T", "43", i) for i in (0, 1)],
                         ["D5", "Cis5"])

    def test_lahdetiedostoa_ei_muuteta(self):
        alkuperainen = find_part(load(OSA_I.mxl), "P13")
        m = next(m for m in alkuperainen.findall("measure")
                 if m.get("number") == "21")
        self.assertEqual(m.findall("note")[0].findtext("lyric/text"), "lg},")


class RexTremendaenSavelet(unittest.TestCase):
    """Kaksi säveltä, jotka kuoron oma tiedosto ja kuvio itse todistavat."""

    @classmethod
    def setUpClass(cls):
        root = load(OSA_II6.mxl)
        cls.basso = find_part(root, OSA_II6.osasto)
        sovella(cls.basso, OSA_II6)
        cls.tenori = find_part(root, OSA_II6_TENORI.osasto)
        sovella(cls.tenori, OSA_II6_TENORI)

    @staticmethod
    def savelet(part, tahti):
        m = next(m for m in part.findall("measure") if m.get("number") == tahti)
        return [kuvaa(n) for n in m.findall("note")]

    def test_basson_alanuotti_on_puolisavelaskel(self):
        # Kolme kertaa sama kuvio: päänuotti, puolisävelaskel alta, takaisin.
        self.assertEqual(self.savelet(self.basso, "21")[:2], ["Bes3", "A3"])
        self.assertEqual(self.savelet(self.basso, "22")[:2], ["Ces4", "Bes3"])
        self.assertEqual(self.savelet(self.basso, "23")[:2], ["C4", "B3"])

    def test_tenori_ja_basso_ovat_unisonossa(self):
        # "sal-va me" kolmesti t.27-32; tenorin kolmas kerta oli oktaavia
        # liian korkealla.
        for tahti in ("28", "30", "32"):
            with self.subTest(tahti=tahti):
                self.assertEqual(self.savelet(self.tenori, tahti)[0],
                                 self.savelet(self.basso, tahti)[0])
        self.assertEqual(self.savelet(self.tenori, "32")[0], "C3")


class AgnusDeinPianoviivastot(unittest.TestCase):
    """Osa V: kaivertajan nimi ja roskamerkki pianoviivastolla sanoina."""

    @classmethod
    def setUpClass(cls):
        root = load(OSAT_V[0].mxl)
        cls.osastot = {}
        for osa_ in OSAT_V:
            part = find_part(root, osa_.osasto)
            sovella(part, osa_)
            cls.osastot[osa_.osasto] = part

    def tavut(self, pid, tahti):
        m = next(m for m in self.osastot[pid].findall("measure")
                 if m.get("number") == tahti)
        return [ly.findtext("text") for n in m.findall("note")
                for ly in n.findall("lyric")]

    def test_kaivertajan_nimi_on_poissa(self):
        self.assertEqual(self.tavut("P6", "68"), [])

    def test_roskamerkki_on_poissa(self):
        self.assertEqual(self.tavut("P5", "31"), [])

    def test_soolojen_sanat_tahdeissa_1_13_jaavat(self):
        # P5 ja P6 ovat tahdeissa 1-13 sooloäänet; vain tahdista 14 ne ovat
        # pianoa, ja vain siellä tavu on roskaa.
        self.assertEqual(self.tavut("P5", "1"), ["A", "gnus"])
        self.assertEqual(self.tavut("P6", "13"), ["qui", "em"])

    def test_lahdetiedostoa_ei_muuteta(self):
        alkuperainen = find_part(load(OSAT_V[1].mxl), "P6")
        m = next(m for m in alkuperainen.findall("measure")
                 if m.get("number") == "68")
        self.assertEqual([ly.findtext("text") for n in m.findall("note")
                          for ly in n.findall("lyric")], ["A.", "Reutenauer"])


class DiesIraenKertausKokonaisuutena(unittest.TestCase):
    """Osa II·9b: yksi merkintä, mutta se avaa osalle oman korjauskerroksen.

    Juokseva numero on lokaali + 572.
    """

    @classmethod
    def setUpClass(cls):
        cls.part = find_part(load(OSA_II9B.mxl), OSA_II9B.osasto)
        sovella(cls.part, OSA_II9B)

    def tahti(self, numero):
        return next(m for m in self.part.findall("measure")
                    if m.get("number") == numero)

    def test_tahti_607_saa_pianon(self):
        self.assertEqual(dynamiikat(self.tahti("35")), [("above", "p")])

    def test_viivastolla_lukee_muuten_yha_ff(self):
        # Merkintä on tarpeen juuri siksi, ettei viivastolla ole mitään
        # t.575:n ff:n jälkeen: laulaja lukee ff:ää ja laulaa hiljaa.
        merkityt = [(m.get("number"), dynamiikat(m))
                    for m in self.part.findall("measure") if dynamiikat(m)]
        self.assertEqual(merkityt, [("3", [("above", "ff")]),
                                    ("35", [("above", "p")])])

    def test_lahdetiedostoa_ei_muuteta(self):
        alkuperainen = find_part(load(OSA_II9B.mxl), OSA_II9B.osasto)
        m = next(m for m in alkuperainen.findall("measure")
                 if m.get("number") == "35")
        self.assertEqual(dynamiikat(m), [])


class Sybilla(unittest.TestCase):
    """"Sy-bil-la" on yksi sana kaikissa neljässä äänessä.

    Lähde-PDF:n neljästä sanarivistä kolme painaa "Sy-bil--la," ja yksi
    "Sy bil--la," ilman ensimmäistä tavuviivaa, joten `korjaa_sanat.py`:n
    tavutusäänestys ei nähnyt sanaa yhtenä lainkaan.
    """

    @classmethod
    def setUpClass(cls):
        root = load(OSA_II9B.mxl)
        cls.osastot = {}
        for osa_ in [OSA_II9B] + OSAT_II9B_SAT:
            part = find_part(root, osa_.osasto)
            sovella(part, osa_)
            cls.osastot[osa_.nimi] = part

    def tavut(self, nimi, tahti):
        m = next(m for m in self.osastot[nimi].findall("measure")
                 if m.get("number") == tahti)
        return [(ly.findtext("syllabic"), ly.findtext("text"))
                for n in m.findall("note") for ly in n.findall("lyric")]

    def test_sybilla_on_yksi_sana_joka_aanessa(self):
        for nimi in ("Kuoro S", "Kuoro A", "Kuoro T", "Kuoro B"):
            with self.subTest(aani=nimi):
                self.assertIn(("begin", "Sy"), self.tavut(nimi, "27"))
                self.assertEqual(self.tavut(nimi, "28"),
                                 [("middle", "bil"), ("end", "la,")])

    def test_altto_saa_puuttuvan_cumin(self):
        self.assertEqual(self.tavut("Kuoro A", "27"),
                         [("single", "cum"), ("begin", "Sy")])

    def test_sopraano_ja_basso_lauloivat_cumin_jo(self):
        for nimi in ("Kuoro S", "Kuoro B"):
            with self.subTest(aani=nimi):
                self.assertEqual(self.tavut(nimi, "27"),
                                 [("single", "cum"), ("begin", "Sy")])


if __name__ == "__main__":
    unittest.main()
