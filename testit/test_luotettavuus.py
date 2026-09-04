#!/usr/bin/env python3
"""Luotettavuustaulukon testit.

Taulukko on käsin ylläpidettävä ihmisen arvio, joten sitä ei voi johtaa
datasta. Testit varmistavat sen sijaan, ettei mikään osa tai ääni jää
hiljaa merkitsemättä ja ettei taulukko viittaa osiin joita ei ole.
"""

import unittest

import luotettavuus
import yhdista


class Kattavuus(unittest.TestCase):
    def test_jokaiselle_osalle_ja_aanelle_on_tila(self):
        for _tiedosto, numero, _otsikko in yhdista.MOVEMENTS:
            for aani in luotettavuus.AANET:
                with self.subTest(osa=numero, aani=aani):
                    self.assertIsNotNone(luotettavuus.tila(numero, aani))

    def test_solistiosat_tunnistetaan_mappingista(self):
        # Mors stupebit on basson soolo; siinä ei ole kuoroa lainkaan.
        self.assertEqual(luotettavuus.tila("II·3", "Kuoro B").nimi, "ei kuoroa")
        # Lacrymosassa on.
        self.assertNotEqual(luotettavuus.tila("II·10", "Kuoro B").nimi,
                            "ei kuoroa")

    def test_varmistetut_ovat_ne_jotka_on_todella_tarkistettu(self):
        """Agnus Dei ja Lacrymosa ovat ainoat kokonaan läpikäydyt.

        Kumpikin vertailtiin kuoron omaan tiedostoon nuotti nuotilta. Jos
        tämä testi kaatuu siksi että jokin muu on merkitty varmistetuksi,
        tarkista että työ on oikeasti tehty — merkintä on lupaus lukijalle.
        """
        varmistetut = {(osa, aani)
                       for (osa, aani), t in luotettavuus.POIKKEUKSET.items()
                       if t.nimi == "varmistettu"}
        self.assertEqual(varmistetut, {("V", "Kuoro B"), ("II·10", "Kuoro B")})

    def test_jokaisella_poikkeuksella_on_perustelu(self):
        for (osa, aani), t in luotettavuus.POIKKEUKSET.items():
            with self.subTest(osa=osa, aani=aani):
                self.assertTrue(t.perustelu.strip(), f"{osa}/{aani}")

    def test_poikkeukset_viittaavat_olemassa_oleviin_osiin(self):
        numerot = {n for _t, n, _o in yhdista.MOVEMENTS}
        for (osa, aani) in luotettavuus.POIKKEUKSET:
            with self.subTest(osa=osa, aani=aani):
                self.assertIn(osa, numerot)
                self.assertIn(aani, luotettavuus.AANET)

    def test_poikkeus_ei_koske_osaa_jossa_ei_ole_kuoroa(self):
        """Poikkeus solistiosaan olisi merkki siitä että taulukko on
        vanhentunut suhteessa MAPPINGiin."""
        for (osa, aani) in luotettavuus.POIKKEUKSET:
            with self.subTest(osa=osa, aani=aani):
                self.assertTrue(luotettavuus.on_kuoroa(osa, aani),
                                f"{osa}/{aani}: poikkeus mutta ei kuoroa")


class Kuorobasso(unittest.TestCase):
    """Basso on ainoa ääni, jolla on oletuksena jokin muu tila kuin
    tarkistamatta: se on käyty läpi Edition Petersin painosta vasten."""

    def test_bassolla_ei_ole_tarkistamattomia_osia(self):
        for _t, numero, _o in yhdista.MOVEMENTS:
            t = luotettavuus.tila(numero, "Kuoro B")
            with self.subTest(osa=numero):
                self.assertNotEqual(t.nimi, "tarkistamatta")

    def test_muilla_aanilla_on(self):
        tilat = {luotettavuus.tila(n, a).nimi
                 for _t, n, _o in yhdista.MOVEMENTS
                 for a in ("Kuoro S", "Kuoro A", "Kuoro T")}
        self.assertIn("tarkistamatta", tilat)

    def test_referenssiedition_nimi_on_yhdessa_paikassa(self):
        """Sivusto ja README nimeävät saman edition; jos se muuttuu, se
        muuttuu täältä."""
        self.assertEqual(luotettavuus.REFERENSSI, "Edition Peters")
        self.assertIn(luotettavuus.REFERENSSI,
                      luotettavuus.KUORO_B_OLETUS.perustelu)


class Perustelut(unittest.TestCase):
    def test_kuorobasso_on_ainoa_jolla_on_varmistettuja_osia(self):
        """README ja sivusto väittävät tätä; testi pitää väitteen totena."""
        for (_osa, aani), t in luotettavuus.POIKKEUKSET.items():
            if t.nimi == "varmistettu":
                self.assertEqual(aani, "Kuoro B")


if __name__ == "__main__":
    unittest.main()
