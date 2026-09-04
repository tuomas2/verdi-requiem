"""Testit käsin todennetuille korjauksille.

Painopiste on turvassa: korjaus osoittaa tahtiin ja nuotti-indeksiin, joten
jos lähdetiedosto muuttuu, korjaus voisi osua hiljaa väärään paikkaan. Siksi
jokaisen toimenpiteen pitää kaatua kun lähtötilanne ei ole odotettu.
"""
import unittest
import xml.etree.ElementTree as ET

from korjaa_kasin import (OSA_I, OSA_II1, OSA_II6, OSA_II10_DIVISI,
                          OSA_II10_KUORO_B, OSA_IV, OSA_VII, OSAT_II4,
                          Osa, find_part, kuvaa, load, lue_korkeus, sovella,
                          yksi_sanarivi)


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
        self.assertEqual(self.tavut(self.b, "74"), [("1", "single", "A")])
        self.assertEqual(self.tavut(self.b, "75"), [("1", "end", "men.")])

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
        self.assertEqual(self.tavut(self.div, "56"), [("2", "end", "ne,")])

    def test_divisin_tavut_pysyvat_sanarivilla_kaksi(self):
        # Viivastolla on kaksi ääntä eri rytmeissä: rivit erottavat ne.
        rivit = {ly.get("number") for m in self.div.findall("measure")
                 for n in m.findall("note") for ly in n.findall("lyric")}
        self.assertEqual(rivit, {"2"})

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

    def test_sanctus_laulaa_coeli_et_terra(self):
        self.assertEqual(self.tavut(OSA_IV, "99"), [("begin", "coe")])
        self.assertEqual(self.tavut(OSA_IV, "100"),
                         [("end", "li"), ("single", "et")])

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

    def test_libera_me_tahti_93_ei_muutu(self):
        """Laulaja sanoi tahdiksi 93, mutta 93 on oikein ja 98 oli väärä.

        Tämä on tässä ettei numeroa 93 korjattaisi myöhemmin "laulajan
        mukaan": 93 laulaa "il-la," aivan kuten saman kuvion 68 ja 72.
        """
        self.assertEqual(self.tavut(OSA_VII, "93"),
                         [("begin", "il"), ("end", "la,")])

    def test_lahdetiedostoja_ei_muuteta(self):
        for osa_, tahti, odotus in ((OSA_IV, "99", []),
                                    (OSA_VII, "98", [])):
            p = find_part(load(osa_.mxl), osa_.osasto)
            tahdit = {m.get("number"): m for m in p.findall("measure")}
            with self.subTest(osa=osa_.mxl):
                self.assertEqual([ly.findtext("text")
                                  for n in tahdit[tahti].findall("note")
                                  for ly in n.findall("lyric")], odotus)


if __name__ == "__main__":
    unittest.main()
