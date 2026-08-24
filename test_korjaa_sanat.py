"""korjaa-sanat.py:n testit. Aja: python3 -m unittest -v"""
import os
import tempfile
import unittest
import zipfile

from korjaa_sanat import (Change, Row, Syllable, align, apply_targets,
                          extract_rows, find_part, load, match_part,
                          read_extras, read_slots, remove_extras,
                          syllables_with_x, tokenise)
from korjaa_sanat import SOURCES, correct, save, vocabulary


def longest_gap(part_report):
    """Pisin yhtenäinen kohdistamaton jakso paikkoja."""
    return max((len(run) for run in part_report.runs), default=0)


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

    def test_row_carries_the_x_position_of_every_syllable(self):
        # Tavun paikka nuotilla ratkeaa x-sijainnista, joten poiminnan on
        # säilytettävä se. Sivun 1 systeemin 1 alin rivi on kuorobasso, ja
        # sen ensimmäinen tavu "Re" alkaa x=266.
        rows = extract_rows("01-Verdi_Requiem.pdf", "Times-Roman", pages=[1])
        pairs = syllables_with_x(rows[3])

        self.assertEqual([s.text for s, _ in pairs],
                         ["Re", "qui", "em,", "re", "qui", "em", "ae"])
        xs = [x for _, x in pairs]
        self.assertEqual(round(xs[0]), 266)
        self.assertEqual(xs, sorted(xs))

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
        target, lo, hi = align(syls, slots)
        self.assertEqual(target[lo:hi], [
            Syllable("et", "single"), Syllable("lux", "single"),
            Syllable("per", "begin"),
        ])
        # Neljäs paikka on ikkunan reunalla: se voi olla seuraavan rivin
        # ensimmäinen tavu, joten sitä ei poisteta vaan raportoidaan.
        self.assertEqual((lo, hi), (0, 3))


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
        got = match_part(rows, slots)

        self.assertEqual([s.text if s else None for s in got.target], [
            "Re", "qui", "em,", "re", "qui", "em", "ae",
            "ter", "nam,", "et", "lux", "per", None,
        ])
        self.assertEqual(got.target[11], Syllable("per", "begin"))


class TestTieBreak(unittest.TestCase):
    def test_punctuation_is_not_taken_from_a_tied_voice(self):
        # Systeemissä 3 sopraano, altto ja basso laulavat samat sanat mutta
        # eri välimerkeillä: sopraanolla "e-is," ja bassolla "e-is.". Sanojen
        # perusteella rivit ovat tasapelissä, joten basso ei saa sopraanon
        # pilkkua tilalle.
        rows = extract_rows("01-Verdi_Requiem.pdf", "Times-Roman")
        slots = read_slots(find_part(load("01-Verdi_Requiem-OMR.mxl"), "P16"))
        got = match_part(rows, [s.syllable for s in slots])

        i = next(k for k, s in enumerate(slots)
                 if s.measure == 26 and s.syllable.text == "is.")
        self.assertTrue(got.handled[i])
        self.assertEqual(got.target[i].text, "is.")


class TestReadSlots(unittest.TestCase):
    def test_main_line_holds_one_syllable_per_note(self):
        part = find_part(load("01-Verdi_Requiem-OMR.mxl"), "P16")
        slots = read_slots(part)
        self.assertEqual(
            [(s.measure, s.syllable.text) for s in slots
             if 17 <= s.measure <= 19],
            [(17, "et"), (18, "lux"), (19, "er")],
        )

    def test_extra_verses_are_kept_out_of_the_main_line(self):
        # Tenorin tahdissa 7 esitysmerkintä "sotto voce" on luettu
        # säkeistöksi 2 oikeiden tavujen alle. Sanarivi luetaan säkeistö
        # kerrallaan eikä nuotti kerrallaan, joten roska ei kuulu
        # pääjonoon: siellä se katkaisisi kohdistuksen heti alkuun.
        part = find_part(load("01-Verdi_Requiem-OMR.mxl"), "P15")
        self.assertEqual([s.syllable.text for s in read_slots(part)[:5]],
                         ["Re", "qui", "em,", "re", "qui"])
        self.assertEqual([s.syllable.text for s in read_extras(part)[:2]],
                         ["SOITO", "VOCE"])


class TestApplyTargets(unittest.TestCase):
    def test_rewritten_slot_gets_both_text_and_syllabic(self):
        part = find_part(load("01-Verdi_Requiem-OMR.mxl"), "P16")
        slots = read_slots(part)
        target = [s.syllable for s in slots]
        i = next(k for k, s in enumerate(slots)
                 if s.measure == 19 and s.syllable.text == "er")
        target[i] = Syllable("per", "begin")

        changes, _ = apply_targets(slots, target, [True] * len(slots))

        self.assertEqual(changes, [Change(19, "er", "per")])
        self.assertEqual(slots[i].element.findtext("text"), "per")
        self.assertEqual(slots[i].element.findtext("syllabic"), "begin")

    def test_slots_beyond_reached_are_not_touched(self):
        part = find_part(load("01-Verdi_Requiem-OMR.mxl"), "P16")
        slots = read_slots(part)
        total = len(list(part.iter("lyric")))

        changes, _ = apply_targets(slots, [None] * len(slots),
                                   [False] * len(slots))

        self.assertEqual(changes, [])
        self.assertEqual(len(list(part.iter("lyric"))), total)


class TestRemoveExtras(unittest.TestCase):
    def test_extra_verse_is_removed_only_on_handled_notes(self):
        part = find_part(load("01-Verdi_Requiem-OMR.mxl"), "P16")
        slots, extras = read_slots(part), read_extras(part)
        main = next(s for s in slots
                    if s.measure == 19 and s.syllable.text == "er")
        self.assertEqual(next(s.syllable.text for s in extras
                              if s.measure == 19), "p")

        changes = remove_extras(extras, {id(main.note)})

        self.assertEqual(changes, [Change(19, "p", None)])
        lyrics = list(main.note.iter("lyric"))
        self.assertEqual(len(lyrics), 1)
        self.assertEqual(lyrics[0].findtext("text"), "er")
        self.assertEqual(lyrics[0].get("number"), "1")
        # Muiden nuottien ylimääräiset jäivät koskematta.
        self.assertEqual(len(read_extras(part)), len(extras) - 1)


class TestCorrect(unittest.TestCase):
    def test_garbled_slot_does_not_stall_the_rest_of_the_part(self):
        # P15:n alussa on roskaa jota PDF:ssä ei ole. Aiemmin kursori pysähtyi
        # siihen ja loput 120 paikkaa jäivät yhdeksi aukoksi. Kohdistamaton
        # kohta on aina jäljellä siellä missä konelukeminen on pudottanut
        # tavun, mutta aukon pitää olla paikallinen eikä koko loppuosa.
        source = next(s for s in SOURCES if s.mxl.startswith("01"))
        _, report = correct(source)
        for part in report:
            self.assertLess(longest_gap(part), 30, part.name)

    def test_capitalised_syllable_is_judged_case_sensitively(self):
        # Basson tahti 35: konelukeminen luki "Je-ru-sa-lem" muodossa
        # "Is-ru-sa-lem". Pienaakkosin "is" esiintyy PDF:ssä joka toisessa
        # tahdissa sanassa "e-is", mutta isolla alkukirjaimella sanan alussa
        # ei kertaakaan. Tämä ei siis ole epävarma vaan selvä korjaus.
        source = next(s for s in SOURCES if s.mxl.startswith("01"))
        _, report = correct(source)
        bass = next(pr for pr in report if pr.part == "P16")
        fix = next(c for c in bass.changes
                   if c.measure == 35 and c.before == "Is")
        self.assertEqual(fix.after, "Je")
        self.assertNotIn(fix, bass.proposals)

    def test_uncertain_change_is_proposed_but_not_applied(self):
        # Sopraanon tahti 134: 'Chri' -> 'e' tekisi sanasta "Chri-ste"
        # muodon "e-ste". Kun sekä vanha että uusi ovat PDF:n tuntemia
        # sanoja, kohdistus voi olla liukunut — käsin tarkistettuna kolme
        # viidestä tällaisesta oli väärin. Niitä ei sovelleta vaan
        # ehdotetaan.
        source = next(s for s in SOURCES if s.mxl.startswith("01"))
        root, report = correct(source)
        soprano = next(pr for pr in report if pr.part == "P13")

        self.assertIn(134, [c.measure for c in soprano.proposals])
        self.assertNotIn(134, [c.measure for c in soprano.changes])
        m134 = next(m for m in find_part(root, "P13").iter("measure")
                    if m.get("number") == "134")
        self.assertEqual([ly.findtext("text") for ly in m134.iter("lyric")],
                         ["Chri"])

    def test_punctuation_only_change_is_not_flagged(self):
        # Tarkistettavaksi merkitään ne joissa sana vaihtuu toiseksi sanaksi.
        # Konelukemisen "nam ," -> "nam," on pelkkä välimerkkisiivous, ja
        # sellaiset hukuttaisivat listaan ne muutokset jotka on syytä katsoa.
        source = next(s for s in SOURCES if s.mxl.startswith("01"))
        _, report = correct(source)
        soprano = next(pr for pr in report if pr.part == "P13")
        siivous = next(c for c in soprano.changes
                       if c.measure == 61 and c.before == "nam ,")
        self.assertEqual(siivous.after, "nam,")
        self.assertNotIn(siivous, soprano.proposals)

    def test_a_syllable_the_pdf_knows_is_never_deleted(self):
        # Poisto on oikea vain roskalle: esitysmerkinnälle, dynamiikalle,
        # kirjainsotkulle. Jos tavu esiintyy PDF:ssä, se on oikea tavu, ja
        # sen poistaminen olisi kohdistuksen liukumista — ei korjaus.
        for source in SOURCES:
            rows = extract_rows(source.pdf, source.font)
            known = vocabulary(rows)
            _, report = correct(source)
            for pr in report:
                for change in pr.changes:
                    if change.after is None:
                        self.assertNotIn(change.before.lower().strip(",.;:!?"),
                                         known, "%s tahti %d" % (pr.name, change.measure))

    def test_bass_misreads_are_fixed_and_no_notes_are_lost(self):
        source = next(s for s in SOURCES if s.mxl.startswith("01"))
        before = len(list(find_part(load(source.mxl), "P16").iter("note")))

        root, report = correct(source)

        bass = find_part(root, "P16")
        # Korjaus koskee vain sanoja, joten nuottien määrä ei muutu.
        self.assertEqual(len(list(bass.iter("note"))), before)
        m28 = next(m for m in bass.iter("measure") if m.get("number") == "28")
        self.assertEqual([ly.findtext("text") for ly in m28.iter("lyric")],
                         ["Te", "de", "cet"])


class TestSave(unittest.TestCase):
    def test_saved_file_keeps_corrections_and_stays_a_valid_mxl(self):
        source = next(s for s in SOURCES if s.mxl.startswith("01"))
        root, _ = correct(source)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "korjattu.mxl")
            save(root, source.mxl, out)

            bass = find_part(load(out), "P16")
            m28 = next(m for m in bass.iter("measure")
                       if m.get("number") == "28")
            self.assertEqual([ly.findtext("text") for ly in m28.iter("lyric")],
                             ["Te", "de", "cet"])
            with zipfile.ZipFile(out) as z:
                # Ilman containeria MuseScore ei tunnista tiedostoa.
                self.assertIn("META-INF/container.xml", z.namelist())


if __name__ == "__main__":
    unittest.main()
