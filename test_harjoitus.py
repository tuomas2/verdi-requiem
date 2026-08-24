"""harjoitus.py:n testit. Aja: python3 -m unittest -v test_harjoitus"""
import unittest

from harjoitus import (SOUND, audio_settings, hide_others, instrument_for,
                       set_sounds)


def osasto(pid, nimi):
    """Yksi <Part> sellaisena kuin MuseScore sen tuonnista kirjoittaa."""
    return ('<Part id="%s"><trackName>%s</trackName>'
            '<Instrument id="grand-piano">'
            '<longName>%s</longName>'
            '<instrumentId>keyboard.piano.grand</instrumentId>'
            '<Channel><program value="0"/></Channel>'
            '</Instrument></Part>' % (pid, nimi, nimi))


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
        # Tuba mirumissa on oikea D-trumpettistemma. Se ei saa olla vaskea
        # lainkaan, koska luettava rivi on trumpetti ja ne sekoittuisivat
        # juuri siinä osassa jossa kuoro laulaa niiden kanssa.
        own = ("Kuoro B", "Kuoro B")
        for staff in ("D-trumpetti", "Trombone"):
            self.assertEqual(instrument_for(staff, own), SOUND["piano"], staff)

    def test_the_read_voice_does_not_transpose(self):
        # brass.trumpet.c on C-trumpetti. Pohjien brass.trumpet.bflat
        # transponoisi, jolloin luettava rivi soisi väärältä korkeudelta.
        self.assertEqual(SOUND["oma"].long, "brass.trumpet.c")


class TestSetSounds(unittest.TestCase):
    """Soitin asetetaan MuseScoren omaan tiedostoon eikä MusicXML:ään:
    MusicXML:n <instrument-name> meni läpi vain kahdelle osastolle
    viidestätoista, loput jäivät flyygeliksi."""

    def test_each_staff_gets_its_sound(self):
        mscx = (osasto("1", "Kuoro B") + osasto("2", "Kuoro T")
                + osasto("3", "Piano"))

        out = set_sounds(mscx, ("Kuoro B", "Kuoro B"))

        for nimi, want in (("Kuoro B", SOUND["oma"]),
                           ("Kuoro T", SOUND["kuoro"]),
                           ("Piano", SOUND["piano"])):
            block = out[out.index("<trackName>%s<" % nimi):]
            block = block[:block.index("</Part>")]
            self.assertIn("<instrumentId>%s</instrumentId>" % want.long, block)
            self.assertIn('<program value="%d"/>' % want.program, block)
            # Lyhyt tunniste ratkaisee soinnin; pelkkä elementti ei riitä.
            self.assertIn('<Instrument id="%s">' % want.short, block)

    def test_the_staff_name_is_not_touched(self):
        # Nimi ja soitin ovat eri asia: viivastolla lukee edelleen Kuoro B
        # vaikka se soi trumpettina.
        out = set_sounds(osasto("1", "Kuoro B"), ("Kuoro B", "Kuoro B"))
        self.assertIn("<longName>Kuoro B</longName>", out)
        self.assertIn("<trackName>Kuoro B</trackName>", out)


class TestAudioSettings(unittest.TestCase):
    """Pelkkä soitin ei riitä: ilman audiosettings.json:n raitoja MuseScore
    soittaa kaiken flyygelinä, koska tiedosto tulee tuonnista sellaisena."""

    def test_each_part_gets_a_pinned_sound(self):
        mscx = osasto("1", "Kuoro B") + osasto("2", "Kuoro T")

        settings = audio_settings(mscx, ("Kuoro B", "Kuoro B"))

        tracks = {t["partId"]: t for t in settings["tracks"]}
        for pid, want in (("1", SOUND["oma"]), ("2", SOUND["kuoro"])):
            self.assertEqual(tracks[pid]["instrumentId"], want.short)
            meta = tracks[pid]["in"]["resourceMeta"]
            self.assertEqual(meta["attributes"]["presetProgram"],
                             str(want.program))
            self.assertEqual(meta["attributes"]["presetName"], want.preset)
            self.assertEqual(meta["id"], "MS Basic\\%d\\%d" % (0, want.program))

    def test_the_metronome_track_is_kept(self):
        settings = audio_settings(osasto("1", "Kuoro B"),
                                  ("Kuoro B", "Kuoro B"))
        metronomi = [t for t in settings["tracks"] if t["partId"] == "999"]
        self.assertEqual(len(metronomi), 1)
        self.assertEqual(metronomi[0]["instrumentId"], "metronome")


class TestHideOthers(unittest.TestCase):
    def test_only_the_named_staves_stay_visible(self):
        # MuseScoren omassa muodossa osasto piilotetaan <show>0</show>:lla.
        # Piilotettu viivasto soi edelleen, mikä on koko idea.
        mscx = (osasto("1", "Kuoro B") + osasto("2", "Kuoro T")
                + osasto("3", "Piano"))

        out = hide_others(mscx, {"Kuoro B"})

        self.assertEqual(out.count("<show>0</show>"), 2)
        for pid, hidden in (("1", False), ("2", True), ("3", True)):
            block = out[out.index('<Part id="%s"' % pid):]
            block = block[:block.index("</Part>")]
            self.assertEqual("<show>0</show>" in block, hidden, pid)


if __name__ == "__main__":
    unittest.main()
