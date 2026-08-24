"""korjaa-sanat.py:n testit. Aja: python3 -m unittest -v"""
import unittest

from korjaa_sanat import (Row, Syllable, align, extract_rows, match_part,
                          tokenise)


class TestTokenise(unittest.TestCase):
    def test_hyphens_and_spaces_around_them_are_normalised(self):
        # Kuoro B, osan 01 toinen systeemi. PDF:n välistys on epätasaista:
        # tavuviivan ympärillä on välilyönti milloin sattuu.
        self.assertEqual(
            tokenise("- ter - nam , et lux per -"),
            [
                Syllable("ter", "middle"),
                Syllable("nam,", "end"),
                Syllable("et", "single"),
                Syllable("lux", "single"),
                Syllable("per", "begin"),
            ],
        )


class TestExtractRows(unittest.TestCase):
    def test_lyric_rows_of_first_page(self):
        rows = extract_rows("01-Verdi_Requiem.pdf", "Times-Roman", pages=[1])
        # Kolme systeemiä x neljä ääntä. "4 Soli" ja "Tutti" ovat samaa
        # fonttia mutta isompaa kokoa, eivätkä ne ole sanoja.
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[0].text, "Re-qui-em, re-qui-em ae-")
        self.assertEqual(rows[0].page, 1)

    def test_glyph_spacing_survives_cramped_engraving(self):
        # Osan 14 MusiXTeX asemoi joka kirjaimen erikseen, joten naiivi
        # kirjainvälin kynnys tuottaa väliä sanojen sisälle.
        rows = extract_rows("14-Verdi_requiem_agnus-dei.pdf", "Garamond", pages=[2])
        self.assertEqual(rows[0].text, "do-na, do-na e-is, do-na e-is re-qui-em.")


class TestAlign(unittest.TestCase):
    """align palauttaa jokaiselle olemassa olevalle tavupaikalle sen
    tavoitetilan: Syllable tai None, joka tarkoittaa ettei paikalla ole
    sanaa lainkaan."""

    def test_two_lyrics_on_one_note_become_one(self):
        # Tahti 19: Audiveris pilkkoi "per" kahtia ja pani puolikkaat eri
        # säkeistöille, "er" säkeistölle 1 ja "p" säkeistölle 2.
        slots = [Syllable("et", "single"), Syllable("lux", "single"),
                 Syllable("er", "begin"), Syllable("p", "single")]
        syls = [Syllable("et", "single"), Syllable("lux", "single"),
                Syllable("per", "begin")]
        target, consumed = align(syls, slots)
        self.assertEqual(target, [
            Syllable("et", "single"), Syllable("lux", "single"),
            Syllable("per", "begin"), None,
        ])
        # Myös poistettu paikka on käsitelty, jotta kursori siirtyy sen yli.
        self.assertEqual(consumed, 4)


class TestMatchPart(unittest.TestCase):
    def test_bass_is_matched_without_soprano_text_leaking_in(self):
        # Sivu 1: systeemissä 1 neljä ääntä laulavat samaa, joten valinta on
        # yhdentekevä. Systeemissä 2 sopraanolla on "do-na, do-na e-is,
        # Do-mi-ne," jota muilla ei ole, ja se ei saa vuotaa bassoon.
        rows = extract_rows("01-Verdi_Requiem.pdf", "Times-Roman", pages=[1])

        # Kuoro B:n tavupaikat konelukemisen jäljiltä, tahdit 7-19.
        slots = [
            Syllable("Re", "begin"), Syllable("qui", "middle"),
            Syllable("em,", "end"),
            Syllable("re", "begin"), Syllable("qui", "middle"),
            Syllable("em", "end"), Syllable("ae", "begin"),
            Syllable("ter", "middle"), Syllable("nam,", "end"),
            Syllable("et", "single"), Syllable("lux", "single"),
            Syllable("er", "begin"), Syllable("p", "single"),
        ]
        target, _, _ = match_part(rows, slots)

        self.assertEqual([s.text if s else None for s in target], [
            "Re", "qui", "em,", "re", "qui", "em", "ae",
            "ter", "nam,", "et", "lux", "per", None,
        ])
        self.assertEqual(target[11], Syllable("per", "begin"))


if __name__ == "__main__":
    unittest.main()
