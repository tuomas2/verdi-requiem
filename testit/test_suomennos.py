"""Testit latinan sanojen suomennokselle ja tavutuksen korjaukselle.

Kaksi asiaa, jotka on helppo rikkoa huomaamatta. Sanan **jako** ratkaisee,
mihin suomennos osuu ja onko se oikea — väärin jaettu "re-qui-em" tuotti
kerran suomennoksen "joka" keskelle sanaa, koska `qui` on itsessään latinaa.
Ja suomennoksen **sanarivi** ratkaisee, montako tekstiriviä MuseScore varaa:
rivi 11 paisutti Basso I:n 16 sivusta 21:een.
"""
import unittest
import xml.etree.ElementTree as ET

import suomennos
from suomennos import (KOKO, RIKKI, SANASTO, jaa_sanoiksi, korjaa_tavutus,
                       lisaa, normalisoi, sanarivi, tavut, tavutus, tavuvirta)


def osasto(*tahdit):
    """Rakenna osasto tiiviistä kuvauksesta.

    Kukin tahti on lista nuotteja, ja nuotti on lista tavuja: (syllabic,
    teksti) tai (syllabic, teksti, sanarivi).
    """
    part = ET.Element("part", {"id": "P1"})
    for numero, nuotit in enumerate(tahdit, start=1):
        m = ET.SubElement(part, "measure", {"number": str(numero)})
        for tavuja in nuotit:
            n = ET.SubElement(m, "note")
            ET.SubElement(n, "voice").text = "1"
            for tavu in tavuja:
                syllabic, teksti = tavu[0], tavu[1]
                rivi = tavu[2] if len(tavu) > 2 else 1
                ly = ET.SubElement(n, "lyric", {"number": str(rivi)})
                ET.SubElement(ly, "syllabic").text = syllabic
                ET.SubElement(ly, "text").text = teksti
    return part


def partituuri(part):
    root = ET.Element("score-partwise")
    root.append(part)
    return root


def sanat_ja_liput(part):
    return [(sana, [t[1] for t in palat], sanastosta)
            for sana, palat, sanastosta in jaa_sanoiksi(tavuvirta(part))]


def suomennokset(part):
    """[(tahti, nuotin indeksi, sanarivi, teksti)] lisätyistä suomennoksista."""
    tulos = []
    for m in part.findall("measure"):
        for i, n in enumerate(m.findall("note")):
            for ly in n.findall("lyric"):
                text = ly.find("text")
                if text is not None and text.get("font-size"):
                    tulos.append((m.get("number"), i, ly.get("number"),
                                  text.text))
    return tulos


class Sanasto(unittest.TestCase):

    def test_avaimet_ovat_normalisoidussa_muodossa(self):
        # Tavut kantavat pilkkuja ja isoja alkukirjaimia ("Dies", "irae,"),
        # ja haku tehdään normalisoidusta muodosta. Avain, joka ei ole
        # normalisoitu, ei siis koskaan osu.
        for avain in SANASTO:
            self.assertEqual(avain, normalisoi(avain))

    def test_yksikaan_suomennos_ei_ole_tyhja(self):
        for avain, arvo in SANASTO.items():
            self.assertTrue(arvo.strip(), avain)

    def test_sama_muoto_ei_ole_seka_sanastossa_etta_rikki_listalla(self):
        # RIKKI on lista muodoista, joita ei *pidäkään* suomentaa. Jos muoto
        # olisi molemmissa, listat olisivat eri mieltä siitä, onko se sana.
        self.assertEqual(set(SANASTO) & set(RIKKI), set())


class Tavut(unittest.TestCase):

    def test_tavu_luetaan_syllabicin_ja_tekstin_parina(self):
        ly = ET.fromstring('<lyric number="1"><syllabic>begin</syllabic>'
                           "<text>Re</text></lyric>")
        self.assertEqual(tavut(ly), [("begin", "Re")])

    def test_elisio_on_kaksi_tavua_yhdessa_lyriikassa(self):
        # "mor-te ae-ter-na": "te" ja "ae" ovat samalla nuotilla, ja
        # yhdista.merge_elisions kirjoittaa ne yhdeksi <lyric>-alkioksi.
        ly = ET.fromstring('<lyric number="1"><syllabic>end</syllabic>'
                           "<text>te</text><elision> </elision>"
                           "<syllabic>begin</syllabic><text>ae</text></lyric>")
        self.assertEqual(tavut(ly), [("end", "te"), ("begin", "ae")])

    def test_pelkka_jatkoviiva_ei_ole_tavu(self):
        # Melisman jatkoa merkitsevä <lyric> ilman tekstiä katkaisisi sanan,
        # jos se laskettaisiin tavuksi.
        ly = ET.fromstring('<lyric number="1"><extend/></lyric>')
        self.assertEqual(tavut(ly), [])


class SanojenJako(unittest.TestCase):
    """Sana luetaan tavujen teksteistä, ei `syllabic`-merkinnöistä."""

    def test_ehja_ketju_luetaan_sanaksi(self):
        part = osasto([[("begin", "Re")], [("middle", "qui")],
                       [("end", "em,")]])
        self.assertEqual(sanat_ja_liput(part),
                         [("Requiem,", ["begin", "middle", "end"], True)])

    def test_rikkinainen_ketju_luetaan_silti_sanaksi(self):
        # Lacrymosan tahdit 688-689: "re" ja "qui" on merkitty erillisiksi
        # sanoiksi ja "em," niitä seuraavaksi jatkoksi. Sanasto tunnistaa
        # kokonaisuuden.
        part = osasto([[("single", "re")], [("single", "qui")],
                       [("middle", "em,")]])
        self.assertEqual(sanat_ja_liput(part),
                         [("requiem,", ["single", "single", "middle"], True)])

    def test_qui_ei_jaa_omaksi_sanakseen_requiemin_keskelta(self):
        # Tämä on se vika, jonka takia sanat luetaan pisin ensin: `qui` on
        # oikeaa latinaa ("joka"), joten stemmaan tulostui "joka" keskelle
        # sanaa requiem.
        part = osasto([[("single", "re")], [("single", "qui")],
                       [("middle", "em,")]])
        self.assertNotIn("qui", [normalisoi(s) for s, _, _ in
                                 sanat_ja_liput(part)])

    def test_kahta_eri_sanaa_ei_liiteta_yhteen(self):
        part = osasto([[("single", "dies")], [("single", "irae,")]])
        self.assertEqual([s for s, _, _ in sanat_ja_liput(part)],
                         ["dies", "irae,"])

    def test_tuntematon_sana_luetaan_lipuista(self):
        # Konelukemisen "perpetlla" ei ole sanastossa, joten ainoa tieto
        # sanan rajoista on `syllabic`.
        part = osasto([[("begin", "per")], [("middle", "petl")],
                       [("end", "la")], [("single", "et")]])
        self.assertEqual(sanat_ja_liput(part),
                         [("perpetlla", ["begin", "middle", "end"], False),
                          ("et", ["single"], True)])

    def test_single_ei_ime_seuraavia_tavuja(self):
        part = osasto([[("single", "xyz")], [("middle", "abc")]])
        self.assertEqual([s for s, _, _ in sanat_ja_liput(part)],
                         ["xyz", "abc"])

    def test_sana_ylittaa_tahtiviivan(self):
        part = osasto([[("begin", "do")]], [[("end", "na")]])
        self.assertEqual([s for s, _, _ in sanat_ja_liput(part)], ["dona"])


class TavutuksenKorjaus(unittest.TestCase):
    """`syllabic` korjataan sanajaon mukaiseksi, jotta väliviivat piirtyvät."""

    def test_tavutus_antaa_ketjun(self):
        self.assertEqual(tavutus(1), ["single"])
        self.assertEqual(tavutus(2), ["begin", "end"])
        self.assertEqual(tavutus(3), ["begin", "middle", "end"])

    def test_rikkinainen_ketju_korjataan(self):
        part = osasto([[("single", "re")], [("single", "qui")],
                       [("middle", "em,")]])
        muutettu = korjaa_tavutus(partituuri(part))
        self.assertEqual(sum(muutettu.values()), 3)
        self.assertEqual([ly.findtext("syllabic")
                          for m in part.findall("measure")
                          for n in m.findall("note")
                          for ly in n.findall("lyric")],
                         ["begin", "middle", "end"])

    def test_tekstit_eivat_muutu(self):
        part = osasto([[("single", "re")], [("single", "qui")],
                       [("middle", "em,")]])
        korjaa_tavutus(partituuri(part))
        self.assertEqual([ly.findtext("text")
                          for m in part.findall("measure")
                          for n in m.findall("note")
                          for ly in n.findall("lyric")],
                         ["re", "qui", "em,"])

    def test_ehjaa_ketjua_ei_kosketa(self):
        part = osasto([[("begin", "Re")], [("middle", "qui")],
                       [("end", "em,")]])
        self.assertEqual(korjaa_tavutus(partituuri(part)),
                         suomennos.collections.Counter())

    def test_tuntemattoman_sanan_merkintoihin_ei_kosketa(self):
        # Ilman sanaston osumaa ei tiedetä, kuuluvatko tavut yhteen.
        part = osasto([[("single", "per")], [("single", "petl")],
                       [("single", "la")]])
        korjaa_tavutus(partituuri(part))
        self.assertEqual([ly.findtext("syllabic")
                          for m in part.findall("measure")
                          for n in m.findall("note")
                          for ly in n.findall("lyric")],
                         ["single", "single", "single"])


class Sanarivi(unittest.TestCase):

    def test_tavallinen_tahti_saa_rivin_kaksi(self):
        part = osasto([[("single", "dies")]])
        self.assertEqual(sanarivi(part.find("measure")), 2)

    def test_divisitahti_saa_rivin_kolme(self):
        # Lacrymosan tahdit 677-679: kaksi ääntä, kaksi tekstiä riveillä 1
        # ja 2. Rivi 2 kirjoittaisi alemman äänen tekstin päälle.
        part = osasto([[("single", "Pi", 1), ("single", "Pi", 2)]])
        self.assertEqual(sanarivi(part.find("measure")), 3)


class Suomennos(unittest.TestCase):

    def test_suomennos_tulee_sanan_ensimmaiselle_nuotille(self):
        part = osasto([[("begin", "Re")], [("middle", "qui")],
                       [("end", "em,")]])
        lisaa(partituuri(part))
        self.assertEqual(suomennokset(part), [("1", 0, "2", "lepo")])

    def test_suomennos_saa_vaakasiirron(self):
        # Ilman siirtoa MuseScore keskittää suomennoksen nuotinpään
        # kohdalle, jolloin tavuaan pidempi sana alkaa tavun vasemmalta
        # puolelta.
        part = osasto([[("single", "dies")]])
        lisaa(partituuri(part))
        ly = part.find("measure/note/lyric[@number='2']")
        self.assertIsNotNone(ly.get("relative-x"))

    def test_suomennos_on_pienemmalla_fontilla(self):
        # MuseScoren tyyliavain lyricsEvenFontSize ei toimi (mitattu), joten
        # koko on tavun omassa <text>-alkiossa.
        part = osasto([[("single", "dies")]])
        lisaa(partituuri(part))
        ly = part.find("measure/note/lyric[@number='2']")
        self.assertEqual(ly.find("text").get("font-size"), KOKO)
        self.assertEqual(ly.get("placement"), "below")

    def test_suomennos_ei_koskaan_tule_riville_yksi(self):
        part = osasto([[("single", "dies")]])
        lisaa(partituuri(part))
        for rivi, in [(r,) for _t, _i, r, _s in suomennokset(part)]:
            self.assertNotEqual(rivi, "1")

    def test_saman_tahdin_sanat_saavat_saman_sanarivin(self):
        # Tämä on se vika, joka paisutti stemman 16 sivusta 21:een: rivi
        # laskettiin uudelleen joka sanalle, ja oma suomennos oli mukana
        # laskennassa, joten toinen sana valui riville 3, kolmas neljälle.
        part = osasto([[("single", "dies")], [("single", "irae,")],
                       [("single", "dies")], [("single", "illa,")]])
        lisaa(partituuri(part))
        self.assertEqual({rivi for _t, _i, rivi, _s in suomennokset(part)},
                         {"2"})

    def test_rikkinainen_sana_ei_saa_suomennosta(self):
        # "perpettua" on konelukemisen tuottama muoto sanasta perpetua, eikä
        # sille ole oikeaa suomennosta — se on vika, ei sana. (Sama vika
        # muodossa "perpetlla" korjattiin 2026-09-10, joten sitä ei ole
        # enää RIKKI-listalla eikä siihen voi nojata testissä.)
        part = osasto([[("single", "perpettua")]])
        tulos = lisaa(partituuri(part))
        self.assertEqual(tulos.lisatty, 0)
        self.assertEqual(tulos.rikki["perpettua"], 1)

    def test_tuntematon_sana_paatyy_varoitukseksi(self):
        part = osasto([[("single", "xyzzy")]])
        tulos = lisaa(partituuri(part))
        self.assertEqual(tulos.puuttuvat["xyzzy"], 1)
        self.assertTrue(any("VAROITUS" in r
                            for r in suomennos.raportti(tulos)))

    def test_vain_ensimmaisen_sanarivin_teksti_suomennetaan(self):
        # Divisissä molemmat äänet laulavat usein samat sanat. Yksi
        # suomennosrivi riittää; kaksi olisi sama teksti kahdesti.
        part = osasto([[("single", "Pie", 1), ("single", "Pie", 2)]])
        lisaa(partituuri(part))
        self.assertEqual(len(suomennokset(part)), 1)


class Vaakatasaus(unittest.TestCase):
    """Suomennos alkaa samasta kohdasta kuin latinan ensimmäinen tavu.

    Siirto lasketaan mitatuista merkkileveyksistä, joten nämä tarkistavat
    säännön eivätkä yksittäisiä pistemääriä: leveystaulukko on mittaustulos
    ja saa muuttua, sääntö ei.
    """

    def test_siirto_asettaa_vasemmat_reunat_kohdakkain(self):
        # Tämä on koko laskennan määritelmä. Tavun vasen reuna on
        # keskitys(tavu) päässä nuotinpäästä ja suomennoksen
        # keskitys(suomi, KOKO_PIENI); siirto vie jälkimmäisen edellisen
        # kohdalle.
        siirto = suomennos.tasaus("lu", "loistakoon")
        self.assertAlmostEqual(
            suomennos.keskitys("loistakoon", suomennos.KOKO_PIENI)
            - siirto * suomennos.KYMMENYS,
            suomennos.keskitys("lu"))

    def test_pitka_suomennos_siirtyy_oikealle(self):
        # "lu-ce-at" / "loistakoon": keskitettynä suomennos alkoi 10,6
        # pistettä ennen tavuaan, edellisen sanan alta.
        self.assertGreater(suomennos.tasaus("lu", "loistakoon"), 0)

    def test_tavua_lyhyempi_suomennos_siirtyy_vasemmalle(self):
        self.assertLess(suomennos.tasaus("et", "ja"), 0)

    def test_loppuvalimerkki_ei_vaikuta_keskitykseen(self):
        # MuseScore keskittää "nam," kuin "nam" — mitattu. Ilman tätä
        # sääntöä pilkkuun päättyvä tavu menisi 1,4 pistettä vinoon.
        self.assertAlmostEqual(suomennos.keskitys("nam,"),
                               suomennos.keskitys("nam"))

    def test_alkuvalimerkki_ei_ole_osa_keskitettavaa_sanaa(self):
        # Sanaston yleisin apusana on "-ssa": yhdysviiva piirtyy sanan
        # vasemmalle puolelle, mutta MuseScore keskittää vain "ssa"-osan.
        self.assertGreater(suomennos.keskitys("-ssa"),
                           suomennos.keskitys("ssa"))

    def test_pelkka_valimerkki_keskitetaan_kokonaan(self):
        self.assertIsNotNone(suomennos.keskitys("-"))

    def test_tuntematon_merkki_jattaa_suomennoksen_keskitetyksi(self):
        # Arvattu leveys siirtäisi sanan väärään paikkaan arvaamattomasti;
        # keskitetty on väärässä paikassa ennustettavasti.
        self.assertIsNone(suomennos.tasaus("na\u2020m", "lepo"))

    def test_elisio_jattaa_suomennoksen_keskitetyksi(self):
        # Elisiossa yhdessä <lyric>-alkiossa on kaksi tavua ja MuseScore
        # piirtää väliin oman yhdysmerkkinsä, jota ei ole mitattu.
        ly = ET.fromstring('<lyric number="1"><syllabic>end</syllabic>'
                           '<text>te</text><elision> </elision>'
                           '<syllabic>begin</syllabic><text>ae</text></lyric>')
        self.assertIsNone(suomennos.tavun_teksti(ly))


class KokoPartituuri(unittest.TestCase):
    """Kaksi muuttumatonta ehtoa valmiissa partituurissa.

    Nämä lukevat käännetyn partituurin, joka on versionhallinnassa. Ne
    pitävät sanaston ja RIKKI-listan ajan tasalla ilman että kukaan muistaa
    tarkistaa niitä: uusi tai väärin kirjoitettu sana ilmoittautuu itse.
    """

    @classmethod
    def setUpClass(cls):
        cls.tulos = lisaa(suomennos.load("Verdi-Requiem-koko.mxl"))

    def test_jokainen_sana_on_joko_suomennettu_tai_tunnettu_rikkinaiseksi(self):
        self.assertEqual(dict(self.tulos.puuttuvat), {},
                         "lisää sana sanastoon tai RIKKI-listaan")

    def test_jokainen_tavun_merkki_on_leveystaulukossa(self):
        # Ilman leveyttä suomennos jää keskitetyksi. Uusi merkki tulee
        # tavallisesti konelukemisen roskana, mutta se on silti mitattava,
        # ei arvattava — mittaustapa on työpäiväkirjan merkinnässä
        # 2026-09-09 (c).
        root = suomennos.load("Verdi-Requiem-koko.mxl")
        merkit = {m
                  for ly in root.iter("lyric")
                  for teksti in ly.findall("text")
                  if not teksti.get("font-size")
                  for m in (teksti.text or "")}
        merkit |= {m for suomi in SANASTO.values() for m in suomi}
        self.assertEqual(merkit - set(suomennos.LEVEYDET), set(),
                         "mittaa puuttuvan merkin leveys, älä arvaa")

    def test_tasaamatta_jaavat_vain_elisiot(self):
        root = suomennos.load("Verdi-Requiem-koko.mxl")
        elisiot = sum(1 for ly in root.iter("lyric")
                      if len(ly.findall("text")) > 1)
        self.assertEqual(self.tulos.tasaamatta, elisiot)

    def test_rikki_listalla_ei_ole_turhia_riveja(self):
        # Kun rikkinäinen tavutus korjataan lähteestä, rivi pitää poistaa —
        # muuten lista lakkaa olemasta luettelo todellisista vioista.
        self.assertEqual(set(RIKKI) - set(self.tulos.rikki), set(),
                         "poista korjatut rivit suomennos.RIKKI:stä")
