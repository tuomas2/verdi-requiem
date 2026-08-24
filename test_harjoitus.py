"""harjoitus.py:n testit. Aja: python3 -m unittest -v test_harjoitus"""
import unittest

from harjoitus import SOUND, instrument_for, set_instruments
from korjaa_sanat import load


class TestInstrumentChoice(unittest.TestCase):
    def test_read_voice_gets_its_own_instrument(self):
        own = ("Kuoro B", "Kuoro B")
        self.assertEqual(instrument_for("Kuoro B", own), SOUND["oma"])
        self.assertEqual(instrument_for("Kuoro T", own), SOUND["kuoro"])
        self.assertEqual(instrument_for("Solisti S", own), SOUND["solisti"])
        self.assertEqual(instrument_for("Piano", own), SOUND["piano"])

    def test_choir_two_belongs_to_a_choir_two_singer_only(self):
        # Basso II lukee tavallista riviä 15 osassa ja II-kuoron riviä
        # Sanctuksessa, joten molemmat viivastot ovat hänen omiaan.
        self.assertEqual(
            instrument_for("Kuoro B II", ("Kuoro B", "Kuoro B II")),
            SOUND["oma"])
        self.assertEqual(
            instrument_for("Kuoro B II", ("Kuoro B", "Kuoro B")),
            SOUND["kuoro"])


    def test_brass_does_not_share_the_read_voice_instrument(self):
        # Tuba mirumissa on oikea D-trumpettistemma. Jos se soisi
        # trumpettina, se sekoittuisi luettavaan riviin juuri siinä
        # osassa jossa kuoro laulaa sen kanssa.
        own = ("Kuoro B", "Kuoro B")
        for staff in ("D-trumpetti", "Trombone"):
            self.assertNotEqual(instrument_for(staff, own), SOUND["oma"], staff)
            self.assertEqual(instrument_for(staff, own), SOUND["vaski"], staff)
        self.assertNotEqual(SOUND["vaski"][0], "Trombone")


class TestSetInstruments(unittest.TestCase):
    def test_every_staff_gets_its_instrument_and_keeps_its_name(self):
        root = load("Verdi-Requiem-koko.mxl")
        set_instruments(root, ("Kuoro B", "Kuoro B"))

        got = {}
        for sp in root.iter("score-part"):
            got[(sp.findtext("part-name") or "").strip()] = (
                sp.findtext("score-instrument/instrument-name"),
                int(sp.findtext("midi-instrument/midi-program")))
        self.assertEqual(got["Kuoro B"], SOUND["oma"])
        self.assertEqual(got["Kuoro T"], SOUND["kuoro"])
        self.assertEqual(got["Solisti B"], SOUND["solisti"])
        self.assertEqual(got["Piano"], SOUND["piano"])
        # Nimi on eri asia kuin soitin: viivastolla lukee edelleen Kuoro B.
        self.assertIn("Kuoro B", got)


if __name__ == "__main__":
    unittest.main()
