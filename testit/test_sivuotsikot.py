"""Testit sivukohtaiselle osaotsikolle.

Otsikko kirjoitetaan sen tahdin päälle, josta sivu alkaa, eli väärä
osanvaihdoksen tunnistus panisi väärän osan nimen sivun ylälaitaan. Siksi
tunnistus tarkistetaan koko `yhdista.OSAOTSIKOT`-listaa vasten ja se
kaatuu ennemmin kuin arvaa. MuseScorea nämä testit eivät kutsu; taiton
lukeminen testataan valmiista <print>-alkioista.
"""
import unittest
import xml.etree.ElementTree as ET

import yhdista
from sivuotsikot import (lisaa_otsikot, osittain, poista_otsikot, sivualut)


def otsikkosanat(m, teksti, lihava=True):
    d = ET.SubElement(m, "direction", {"placement": "above"})
    dt = ET.SubElement(d, "direction-type")
    w = ET.SubElement(dt, "words")
    if lihava:
        w.set("font-size", "13")
        w.set("font-weight", "bold")
    w.text = teksti
    return d


def part(otsikot, sivualkuja=(), tahteja=None):
    """Osasto, jossa otsikot on sanakirja tahti-indeksi -> otsikkoteksti.

    `sivualkuja` on niiden tahti-indeksien joukko, joille kirjoitetaan
    <print new-page="yes">, eli MuseScoren viennin muoto.
    """
    if tahteja is None:
        tahteja = max([*otsikot, *sivualkuja, 0]) + 1
    p = ET.Element("part", {"id": "P1"})
    for i in range(tahteja):
        m = ET.SubElement(p, "measure", {"number": str(i + 1)})
        if i in sivualkuja:
            ET.SubElement(m, "print", {"new-page": "yes"})
        if i in otsikot:
            otsikkosanat(m, otsikot[i])
        ET.SubElement(m, "note")
    return p


def score(p):
    root = ET.Element("score-partwise")
    root.append(p)
    return root


def kaikki_osat(tahteja_per_osa=1, hantaa=0):
    """Osasto, jossa kaikki osat alkavat peräkkäin.

    `osittain` vaatii löytävänsä koko `yhdista.OSAOTSIKOT`-listan, joten
    testien osaston pitää sisältää ne kaikki.
    """
    otsikot = {i * tahteja_per_osa: t
               for i, t in enumerate(yhdista.OSAOTSIKOT)}
    n = len(yhdista.OSAOTSIKOT) * tahteja_per_osa
    return part(otsikot, tahteja=n + hantaa), otsikot


class Sivualut(unittest.TestCase):
    def test_ensimmainen_tahti_on_aina_sivualku(self):
        self.assertEqual(sivualut(score(part({}, tahteja=5))), [0])

    def test_new_page_alkiot_luetaan(self):
        p = part({}, sivualkuja={3, 7}, tahteja=10)
        self.assertEqual(sivualut(score(p)), [0, 3, 7])


class Osanvaihdoksen_tunnistus(unittest.TestCase):
    def test_otsikko_jatkuu_seuraavaan_vaihdokseen(self):
        p, _ = kaikki_osat(tahteja_per_osa=4)
        nimet = osittain(p)
        self.assertEqual(nimet[:4], [yhdista.OSAOTSIKOT[0]] * 4)
        self.assertEqual(nimet[4:8], [yhdista.OSAOTSIKOT[1]] * 4)
        self.assertEqual(nimet[-1], yhdista.OSAOTSIKOT[-1])

    def test_lahteen_oma_lihavoitu_ohjeteksti_ei_ole_osanvaihdos(self):
        """Lähteissä on omia lihavoituja sanoja ("Alle", "4 soli").

        Pelkkä fonttihaku poimi ne osanvaihdoksiksi, ja Libera men
        viimeiselle sivulle tuli otsikoksi "Alle". Siksi tunnistus katsoo
        tekstiä eikä fonttia.
        """
        p, _ = kaikki_osat(tahteja_per_osa=4)
        otsikkosanat(p.findall("measure")[2], "Alle")
        otsikkosanat(p.findall("measure")[3], "4 soli", lihava=False)
        self.assertEqual(osittain(p)[:4], [yhdista.OSAOTSIKOT[0]] * 4)

    def test_puuttuva_osa_kaataa(self):
        # Jos tunnistus menee rikki, ajo pysähtyy eikä kirjoita väärin.
        p = part({0: yhdista.OSAOTSIKOT[0]}, tahteja=3)
        with self.assertRaises(SystemExit):
            osittain(p)

    def test_vaara_jarjestys_kaataa(self):
        p = part(dict(enumerate(reversed(yhdista.OSAOTSIKOT))),
                 tahteja=len(yhdista.OSAOTSIKOT))
        with self.assertRaises(SystemExit):
            osittain(p)


class Otsikoiden_lisays(unittest.TestCase):
    def setUp(self):
        # Kaikki osat peräkkäin, yksi tahti kumpaakin, ja lopuksi häntä.
        self.otsikot = {i: t for i, t in enumerate(yhdista.OSAOTSIKOT)}
        self.n = len(yhdista.OSAOTSIKOT)

    def part(self, tahteja):
        return part(self.otsikot, tahteja=tahteja)

    def tekstit(self, p):
        return [w.text for m in p.findall("measure")
                for w in m.findall("direction/direction-type/words")
                if (w.get("id") or "").startswith("sivuotsikko")]

    def test_otsikko_kirjoitetaan_sivualkuun(self):
        p = self.part(self.n + 3)
        lisatty, ohitettu = lisaa_otsikot(p, [self.n + 1])
        self.assertEqual((lisatty, ohitettu), (1, 0))
        self.assertEqual(self.tekstit(p), [yhdista.OSAOTSIKOT[-1]])

    def test_osan_alkaessa_sivulta_otsikkoa_ei_toisteta(self):
        # Iso lihava otsikko on jo paikallaan.
        p = self.part(self.n + 3)
        lisatty, ohitettu = lisaa_otsikot(p, [0, 3])
        self.assertEqual((lisatty, ohitettu), (0, 2))
        self.assertEqual(self.tekstit(p), [])

    def test_otsikko_tulee_printin_ja_attributesin_jalkeen(self):
        p = self.part(self.n + 2)
        m = p.findall("measure")[self.n + 1]
        ET.SubElement(m, "print")
        lisaa_otsikot(p, [self.n + 1])
        self.assertEqual([e.tag for e in m][:3], ["note", "print", "direction"])

    def test_uudelleenajo_ei_kahdenna(self):
        p = self.part(self.n + 3)
        lisaa_otsikot(p, [self.n + 1])
        self.assertEqual(poista_otsikot(p), 1)
        lisaa_otsikot(p, [self.n + 1])
        self.assertEqual(self.tekstit(p), [yhdista.OSAOTSIKOT[-1]])

    def test_poisto_ei_kosketa_isoja_otsikoita(self):
        p = self.part(self.n + 3)
        lisaa_otsikot(p, [self.n + 1])
        poista_otsikot(p)
        self.assertEqual(osittain(p)[0], yhdista.OSAOTSIKOT[0])
        self.assertEqual(self.tekstit(p), [])


if __name__ == "__main__":
    unittest.main()
