"""harjoitus.py:n testit. Aja: python3 -m unittest -v test_harjoitus"""
import unittest

from harjoitus import SOUND, hide_others, instrument_for, set_sounds


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


    def test_brass_sounds_nothing_like_the_read_voice(self):
        # Tuba mirumissa on oikea D-trumpettistemma. Se ei saa olla
        # vaskea lainkaan, koska luettava rivi on trumpetti ja ne
        # sekoittuisivat juuri siinä osassa jossa kuoro laulaa niiden
        # kanssa.
        own = ("Kuoro B", "Kuoro B")
        for staff in ("D-trumpetti", "Trombone"):
            self.assertEqual(instrument_for(staff, own), SOUND["piano"], staff)


def osasto(nimi):
    return ('<Part id="x"><trackName>%s</trackName>'
            '<Instrument id="grand-piano">'
            '<longName>%s</longName>'
            '<instrumentId>keyboard.piano.grand</instrumentId>'
            '<Channel><program value="0"/></Channel>'
            '</Instrument></Part>' % (nimi, nimi))


class TestSetSounds(unittest.TestCase):
    """Soitin asetetaan MuseScoren omaan tiedostoon eikä MusicXML:ään:
    MusicXML:n <instrument-name> meni läpi vain kahdelle osastolle
    viidestätoista, loput jäivät flyygeliksi."""

    def test_each_staff_gets_its_sound(self):
        mscx = osasto("Kuoro B") + osasto("Kuoro T") + osasto("Piano")

        out = set_sounds(mscx, ("Kuoro B", "Kuoro B"))

        for nimi, want in (("Kuoro B", SOUND["oma"]),
                           ("Kuoro T", SOUND["kuoro"]),
                           ("Piano", SOUND["piano"])):
            block = out[out.index("<trackName>%s<" % nimi):]
            block = block[:block.index("</Part>")]
            self.assertIn("<instrumentId>%s</instrumentId>" % want[0], block)
            self.assertIn('<program value="%d"/>' % want[1], block)

    def test_the_staff_name_is_not_touched(self):
        # Nimi ja soitin ovat eri asia: viivastolla lukee edelleen Kuoro B
        # vaikka se soi trumpettina.
        out = set_sounds(osasto("Kuoro B"), ("Kuoro B", "Kuoro B"))
        self.assertIn("<longName>Kuoro B</longName>", out)
        self.assertIn("<trackName>Kuoro B</trackName>", out)


class TestHideOthers(unittest.TestCase):
    def test_only_the_named_staves_stay_visible(self):
        # MuseScoren omassa muodossa osasto piilotetaan <show>0</show>:lla.
        # Piilotettu viivasto soi edelleen, mikä on koko idea.
        mscx = ('<Part id="1"><Staff/><trackName>Kuoro B</trackName></Part>'
                '<Part id="2"><Staff/><trackName>Kuoro T</trackName></Part>'
                '<Part id="3"><Staff/><trackName>Piano</trackName></Part>')

        out = hide_others(mscx, {"Kuoro B"})

        self.assertEqual(out.count("<show>0</show>"), 2)
        for pid, hidden in (("1", False), ("2", True), ("3", True)):
            block = out[out.index('<Part id="%s"' % pid):]
            block = block[:block.index("</Part>")]
            self.assertEqual("<show>0</show>" in block, hidden, pid)


if __name__ == "__main__":
    unittest.main()
