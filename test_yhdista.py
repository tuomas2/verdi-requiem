"""Testit yhdista.py:n sanarivien normalisoinnille.

Sanarivin numero (`<lyric number>`) ratkaisee, monennelle tekstiriville tavu
piirtyy. OMR ja lähdetiedostot merkitsevät sen epäluotettavasti, ja yhden
fraasin hajoaminen kahdelle riville tekee stemmasta lukukelvottoman.
"""
import unittest
import xml.etree.ElementTree as ET

from yhdista import (DIES_IRAE_ALUT, DIES_IRAE_SIIRTYMAT, normalise_lyrics,
                     saumaraportti, verse_number)


def measure(*notes):
    """Rakenna tahti tiiviistä kuvauksesta.

    Kukin nuotti on (ääni, [(rivi, tavu), ...]); tyhjä lista = ei sanoja.
    """
    m = ET.Element("measure", {"number": "1"})
    for voice, lyrics in notes:
        n = ET.SubElement(m, "note")
        ET.SubElement(n, "voice").text = str(voice)
        for number, text in lyrics:
            ly = ET.SubElement(n, "lyric", {"number": str(number)})
            ET.SubElement(ly, "text").text = text
    return m


def rows(m):
    """Poimi tulos muodossa [(rivi, tavu), ...] nuottijärjestyksessä."""
    return [(ly.get("number"), ly.findtext("text"))
            for n in m.findall("note") for ly in n.findall("lyric")]


class VerseNumber(unittest.TestCase):
    def test_plain_and_prefixed_forms(self):
        self.assertEqual(verse_number("2"), 2)
        self.assertEqual(verse_number("part5verse2"), 2)
        self.assertEqual(verse_number(None), 1)
        self.assertEqual(verse_number(""), 1)


class SingleVoice(unittest.TestCase):
    """Yhdellä äänellä on yksi tekstirivi, olkoon numerointi mikä hyvänsä."""

    def test_mixed_numbers_collapse_to_row_one(self):
        # Osa I, tahti 108: OMR jakoi "e-le-i-son" kahdelle riville niin,
        # että "i" jäi riville 1 ja muut riville 2.
        m = measure((1, [(2, "le")]), (1, [(1, "i")]), (1, [(2, "son,")]))
        normalise_lyrics(m)
        self.assertEqual(rows(m), [("1", "le"), ("1", "i"), ("1", "son,")])

    def test_all_on_row_two_collapse_to_row_one(self):
        m = measure((1, [(2, "Te")]), (1, [(2, "de")]), (1, [(2, "cet")]))
        normalise_lyrics(m)
        self.assertEqual(rows(m), [("1", "Te"), ("1", "de"), ("1", "cet")])

    def test_already_on_row_one_is_untouched(self):
        m = measure((1, [(1, "Ky")]), (1, [(1, "ri")]), (1, [(1, "e")]))
        normalise_lyrics(m)
        self.assertEqual(rows(m), [("1", "Ky"), ("1", "ri"), ("1", "e")])

    def test_missing_voice_element_counts_as_voice_one(self):
        m = ET.Element("measure", {"number": "1"})
        for number, text in ((2, "hym"), (1, "nus,")):
            n = ET.SubElement(m, "note")
            ly = ET.SubElement(n, "lyric", {"number": str(number)})
            ET.SubElement(ly, "text").text = text
        normalise_lyrics(m)
        self.assertEqual(rows(m), [("1", "hym"), ("1", "nus,")])


class TwoLyricsOnOneNote(unittest.TestCase):
    """Kaksi tavua samalla nuotilla tarvitsee kaksi riviä, ei yhtä."""

    def test_stacked_lyrics_keep_their_rows(self):
        # Osa I, tahti 78: oikea "is." ja OMR:n roskatavu "S" samalla nuotilla.
        m = measure((1, [(1, "is."), (2, "S")]), (1, []))
        normalise_lyrics(m)
        self.assertEqual(rows(m), [("1", "is."), ("2", "S")])


class TwoVoices(unittest.TestCase):
    """Divisi: kaksi ääntä samalla viivastolla laulaa eri tekstiä."""

    def test_divisi_rows_are_kept_apart(self):
        # Lacrymosa, tahti 682: ääni 1 rivillä 1, ääni 2 rivillä 2.
        m = measure((1, [(1, "Pi")]), (1, [(1, "e")]),
                    (2, [(2, "La")]), (2, [(2, "cry")]))
        normalise_lyrics(m)
        self.assertEqual(rows(m),
                         [("1", "Pi"), ("1", "e"), ("2", "La"), ("2", "cry")])

    def test_inverted_divisi_rows_are_left_alone(self):
        # Rex tremendae, tahti 369: ääni 1 on rivillä 2 ja ääni 2 rivillä 1.
        # Rivien vaihtaminen ei ole tämän funktion tehtävä; tärkeää on, ettei
        # niitä yhdistetä samalle riville.
        m = measure((1, [(2, "sal")]), (2, [(1, "me,")]))
        normalise_lyrics(m)
        self.assertEqual(rows(m), [("2", "sal"), ("1", "me,")])


class NoLyrics(unittest.TestCase):
    def test_measure_without_lyrics_is_untouched(self):
        m = measure((1, []), (1, []))
        normalise_lyrics(m)
        self.assertEqual(rows(m), [])


class DiesIraenNumerointi(unittest.TestCase):
    """Alkunumerot ovat kuoron nuottikirjasta, eivät laskettuja.

    Nämä on naulattu tähän siksi, että aiemmin ne laskettiin lähdetiedostojen
    tahtimääristä ja olivat kuudessa kohdassa väärin. Jos joku laskee ne
    joskus uudelleen "oikein", tämä testi kaatuu.
    """

    KIRJA = {"02-Verdi-Dies_irae.mxl": 1, "03-Verdi-Tuba_mirum.mxl": 91,
             "04-Verdi-Mors_stupebit.mxl": 143,
             "05-Verdi-Liber_scriptus.mxl": 162,
             "06-Verdi-Quid_sum_miser.mxl": 271, "07-Verdi-Rex.mxl": 322,
             "08-Verdi_Recordare.mxl": 386, "09-Verdi_Ingemisco.mxl": 450,
             "10-Verdi_Confutatis.mxl": 507,
             "10b-Verdi_Dies_irae_paluu-OMR-korjattu.mxl": 573,
             "11-Verdi_Lacrymosa.mxl": 621}

    def test_alut_ovat_kirjan_mukaiset(self):
        self.assertEqual(DIES_IRAE_ALUT, self.KIRJA)

    def test_siirtyma_on_alkunumero_miinus_yksi(self):
        for tiedosto, alku in DIES_IRAE_ALUT.items():
            self.assertEqual(DIES_IRAE_SIIRTYMAT[tiedosto], alku - 1, tiedosto)


class Saumaraportti(unittest.TestCase):
    """Saumojen epäjatkuvuus on tarkoituksellista mutta ei saa jäädä piiloon."""

    def test_jatkuva_numerointi_ei_raportoi_mitaan(self):
        self.assertEqual(saumaraportti([("A", 1, 10), ("B", 11, 20)]), [])

    def test_paallekkaiset_numerot_raportoidaan(self):
        rivit = saumaraportti([("II·9", 507, 577), ("II·9b", 573, 623)])
        self.assertIn("5 numeroa toistuu", rivit[1])

    def test_puuttuvat_numerot_raportoidaan(self):
        rivit = saumaraportti([("II·2", 91, 139), ("II·3", 143, 164)])
        self.assertIn("3 numeroa puuttuu", rivit[1])

    def test_yksi_alue_ei_tuota_raporttia(self):
        self.assertEqual(saumaraportti([("A", 1, 10)]), [])


if __name__ == "__main__":
    unittest.main()
