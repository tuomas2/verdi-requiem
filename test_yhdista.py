"""Testit yhdista.py:n sanarivien normalisoinnille.

Sanarivin numero (`<lyric number>`) ratkaisee, monennelle tekstiriville tavu
piirtyy. OMR ja lähdetiedostot merkitsevät sen epäluotettavasti, ja yhden
fraasin hajoaminen kahdelle riville tekee stemmasta lukukelvottoman.
"""
import unittest
import xml.etree.ElementTree as ET

from yhdista import normalise_lyrics, verse_number


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


if __name__ == "__main__":
    unittest.main()
