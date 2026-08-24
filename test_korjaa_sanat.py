"""korjaa-sanat.py:n testit. Aja: python3 -m unittest -v"""
import unittest

from korjaa_sanat import Row, Syllable, extract_rows, tokenise


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


if __name__ == "__main__":
    unittest.main()
