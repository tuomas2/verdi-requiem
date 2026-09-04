#!/usr/bin/env python3
"""Polkujen selvityksen testit.

Sääntö ratkaisee, mistä hakemistosta mikäkin nuottitiedosto luetaan, joten
väärä sääntö lukisi hiljaa väärää tiedostoa. Siksi tässä on sekä säännön
yksikkötestit että ristiintarkistus siitä, että jokainen skriptien
taulukoissa mainittu tiedosto on oikeasti siinä hakemistossa jonka sääntö
osoittaa.
"""

import os
import unittest

import polut


class Saanto(unittest.TestCase):
    def test_lahde_menee_lahteisiin(self):
        self.assertEqual(polut.polku("04-Verdi-Mors_stupebit.mxl"),
                         "lahteet/04-Verdi-Mors_stupebit.mxl")

    def test_raaka_omr_on_lahde(self):
        self.assertEqual(polut.polku("01-Verdi_Requiem-OMR.mxl"),
                         "lahteet/01-Verdi_Requiem-OMR.mxl")

    def test_korjattu_omr_on_johdettu(self):
        self.assertEqual(polut.polku("01-Verdi_Requiem-OMR-korjattu.mxl"),
                         "johdetut/01-Verdi_Requiem-OMR-korjattu.mxl")

    def test_kasin_on_johdettu(self):
        self.assertEqual(polut.polku("11-Verdi_Lacrymosa-kasin.mxl"),
                         "johdetut/11-Verdi_Lacrymosa-kasin.mxl")

    def test_koko_partituuri_on_johdettu(self):
        self.assertEqual(polut.polku("Verdi-Requiem-koko.mxl"),
                         "johdetut/Verdi-Requiem-koko.mxl")

    def test_lahde_pdf_ei_ole_johdettu(self):
        # Nimi alkaa samalla tavalla kuin CPDL:n lähteet; ei saa sekoittua
        # koko partituuriin.
        self.assertEqual(polut.polku("Verdi_Lacymosa.pdf"),
                         "lahteet/Verdi_Lacymosa.pdf")

    def test_stemma_ja_sen_sisallys(self):
        self.assertEqual(polut.polku("stemma-basso-1.pdf"),
                         "stemmat/stemma-basso-1.pdf")
        self.assertEqual(polut.polku("stemmat-sisallys.txt"),
                         "stemmat/stemmat-sisallys.txt")

    def test_harjoitustiedosto(self):
        self.assertEqual(polut.polku("harjoitus-basso-1.mscz"),
                         "harjoitus/harjoitus-basso-1.mscz")

    def test_valmis_polku_palautetaan_sellaisenaan(self):
        # Komentoriviltä pitää voida antaa mikä tahansa tiedosto.
        self.assertEqual(polut.polku("johdetut/Verdi-Requiem-koko.mxl"),
                         "johdetut/Verdi-Requiem-koko.mxl")
        self.assertEqual(polut.polku("/tmp/koe.mxl"), "/tmp/koe.mxl")



def taulukoiden_nimet():
    """Jokainen tiedostonimi, jonka jokin skriptin taulukko mainitsee."""
    import korjaa_kasin
    import korjaa_sanat
    import sisallys
    import yhdista

    nimet = set()
    nimet.update(t for t, _, _ in yhdista.MOVEMENTS)
    nimet.update(yhdista.MAPPING)
    nimet.update(yhdista.DIES_IRAE_ALUT)
    nimet.update(yhdista.OMR_SOURCES)
    nimet.add(yhdista.SANCTUS)
    for s in korjaa_sanat.SOURCES:
        nimet.update([s.mxl, s.pdf, s.out])
    for osa in korjaa_kasin.OSAT:
        nimet.update([osa.mxl, osa.out])
    nimet.update(pdf for _nimi, pdf in sisallys.STEMMAT)
    nimet.add(sisallys.ULOS)
    return nimet


class Olemassaolo(unittest.TestCase):
    """Sääntö ei saa jäädä hiljaiseksi oletukseksi.

    Jos jokin tiedosto on muualla kuin sääntö osoittaa, ajo lukisi väärää
    tiedostoa tai kaatuisi vasta ketjun puolivälissä. Tämä kaataa sen heti.
    """

    def test_jokainen_taulukon_nimi_loytyy_saannon_osoittamasta_paikasta(self):
        for nimi in sorted(taulukoiden_nimet()):
            with self.subTest(nimi=nimi):
                self.assertTrue(os.path.exists(polut.polku(nimi)),
                                f"{nimi} ei ole polussa {polut.polku(nimi)}")

    def test_tiedosto_ei_ole_kahdessa_hakemistossa(self):
        """Eksynyt kopio antaisi hiljaa väärän tuloksen."""
        kaikki = [polut.LAHTEET, polut.JOHDETUT, polut.STEMMAT, polut.HARJOITUS]
        for nimi in sorted(taulukoiden_nimet()):
            paikat = [h for h in kaikki
                      if os.path.exists(os.path.join(h, nimi))]
            with self.subTest(nimi=nimi):
                self.assertEqual(len(paikat), 1, f"{nimi} löytyy: {paikat}")

if __name__ == "__main__":
    unittest.main()
