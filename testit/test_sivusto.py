#!/usr/bin/env python3
"""Sivustogeneraattorin testit.

Sivuston tiedot luetaan samoista vakioista jotka ohjaavat stemmojen
tuotantoa, joten testien tärkein tehtävä on varmistaa ettei mikään osa katoa
matkalla ja että sivunumerot vastaavat oikeasti tuotettuja stemmoja.
"""

import os
import tempfile
import unittest

import sivusto
import yhdista


class Runko(unittest.TestCase):
    def test_sivu_on_kokonainen_html(self):
        html = sivusto.sivu("Koe", "<p>sisältö</p>", "index.html")
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn('<html lang="fi">', html)
        self.assertIn("tyyli.css", html)
        self.assertIn("<p>sisältö</p>", html)

    def test_aktiivinen_sivu_merkitaan(self):
        html = sivusto.sivu("Koe", "", "index.html")
        self.assertIn('href="index.html" aria-current="page"', html)

    def test_navigaatiossa_on_kaksi_sivua(self):
        """Erillinen etusivu olisi väliporras, joka pitää klikata pois
        tieltä ennen kuin pääsee siihen mitä sivustolta haetaan."""
        self.assertEqual([nimi for _t, nimi in sivusto.NAVI],
                         ["Stemmat", "Teksti"])

    def test_otsikko_siistitaan(self):
        """Osien nimissä on &-merkki (Requiem & Kyrie), joka on pakattava."""
        html = sivusto.sivu("Requiem & Kyrie", "", "index.html")
        self.assertIn("Requiem &amp; Kyrie", html)
        self.assertNotIn("Requiem & Kyrie", html)


class Luotettavuus(unittest.TestCase):
    """Luotettavuustieto on osa stemmasivua, ei omaa sivuaan: se on juuri se
    mitä stemman lataajan pitää tietää ennen latausta."""

    def test_jokainen_osa_on_taulukossa(self):
        html = sivusto.stemmasivu()
        for _t, _numero, otsikko in yhdista.MOVEMENTS:
            with self.subTest(osa=otsikko):
                # & on pakattu HTML:ssä.
                self.assertIn(otsikko.replace("&", "&amp;"), html)

    def test_kertoo_etta_vain_basso_on_varmistettu(self):
        self.assertIn("kuorobasso", sivusto.stemmasivu().lower())

    def test_selittaa_merkit(self):
        html = sivusto.stemmasivu()
        for merkki in ["✔", "◑", "○", "⚠"]:
            with self.subTest(merkki=merkki):
                self.assertIn(merkki, html)

    def test_jokaisen_aanen_tila_nakyy_taulukossa(self):
        """Merkin pitää olla samassa solussa sivunumeron kanssa, ei erillään:
        muuten sivun ja luotettavuuden yhdistäminen jäi tekemättä."""
        html = sivusto.stemmasivu()
        # Agnus Dei: basso varmistettu sivulla 10, ylemmät äänet puutteelliset.
        self.assertIn('<span class="sivu">10</span>'
                      '<span class="merkki" title="varmistettu">✔</span>', html)
        self.assertIn('<span class="sivu">10</span>'
                      '<span class="merkki" title="puutteita">⚠</span>', html)

    def test_referenssiedition_nimi_nakyy(self):
        """Käytännössä tärkein yksittäinen tieto laulajalle: täsmäävätkö
        tahtinumerot siihen nuottiin joka hänellä on kädessä."""
        html = sivusto.stemmasivu()
        self.assertIn("Edition Peters", html)

    def test_perustelut_ovat_mukana(self):
        html = sivusto.stemmasivu()
        self.assertIn("Lacrymosa", html)
        self.assertIn("oktaavivirhe", html)


class Rakennus(unittest.TestCase):
    def test_kaikki_sivut_syntyvat(self):
        with tempfile.TemporaryDirectory() as d:
            sivusto.rakenna(d)
            for nimi in ["index.html", "teksti.html", "tyyli.css"]:
                with self.subTest(nimi=nimi):
                    self.assertTrue(os.path.exists(os.path.join(d, nimi)))

    def test_oma_verkkotunnus_kirjoitetaan(self):
        """Ilman CNAME-tiedostoa oma domain lakkaa toimimasta hiljaa, jos
        Pagesin asetukset nollautuvat."""
        with tempfile.TemporaryDirectory() as d:
            sivusto.rakenna(d)
            with open(os.path.join(d, "CNAME"), encoding="utf-8") as f:
                self.assertEqual(f.read().strip(), sivusto.VERKKOTUNNUS)

    def test_etusivu_on_stemmasivu(self):
        with tempfile.TemporaryDirectory() as d:
            sivusto.rakenna(d)
            with open(os.path.join(d, "index.html"), encoding="utf-8") as f:
                self.assertIn("stemma-basso-1.pdf", f.read())

    def test_stemmojen_pdf_t_kopioidaan(self):
        with tempfile.TemporaryDirectory() as d:
            sivusto.rakenna(d)
            for _nimi, pdf in sivusto.STEMMAT:
                with self.subTest(pdf=pdf):
                    self.assertTrue(
                        os.path.exists(os.path.join(d, "stemmat", pdf)))


class Stemmasivu(unittest.TestCase):
    def test_sisallys_luetaan_tiedostosta(self):
        rivit = sivusto.lue_sisallys()
        self.assertIn("Agnus Dei", " ".join(r[1] for r in rivit))
        for _numero, _otsikko, sivut in rivit:
            self.assertEqual(len(sivut), 8)

    def test_sisallys_kattaa_kaikki_osat(self):
        self.assertEqual(len(sivusto.lue_sisallys()), len(yhdista.MOVEMENTS))

    def test_tahtivalit_luetaan_partituurista(self):
        valit = sivusto.tahtivalit()
        # Dies irae numeroituu jatkuvasti; Lacrymosa on sen viimeinen alaosa.
        self.assertEqual(valit["II·10"], (624, 701))
        # Muut osat alkavat ykkösestä.
        self.assertEqual(valit["IV"][0], 1)
        self.assertEqual(valit["I"][0], 1)

    def test_tahtivalit_kattaa_kaikki_osat(self):
        valit = sivusto.tahtivalit()
        for _t, numero, _o in yhdista.MOVEMENTS:
            with self.subTest(osa=numero):
                self.assertIn(numero, valit)

    def test_sivulla_on_latauslinkki_jokaiselle_stemmalle(self):
        html = sivusto.stemmasivu()
        for _nimi, pdf in sivusto.STEMMAT:
            with self.subTest(pdf=pdf):
                self.assertIn(pdf, html)


class Tekstisivu(unittest.TestCase):
    def test_navigaatio_on_lisatty(self):
        self.assertIn('href="index.html"', sivusto.tekstisivu())

    def test_ei_jaanyt_linkkeja_poistettuihin_sivuihin(self):
        """Luotettavuus ja etusivu sulautuivat stemmasivuun; rikkinäinen
        linkki jäisi muuten huomaamatta, koska sivut kyllä rakentuvat."""
        for html in [sivusto.stemmasivu(), sivusto.tekstisivu()]:
            self.assertNotIn("luotettavuus.html", html)
            self.assertNotIn("stemmat.html", html)

    def test_alkuperainen_sisalto_sailyy(self):
        html = sivusto.tekstisivu()
        for tunnus in ['id="i"', 'id="ii"', 'id="vii"']:
            with self.subTest(tunnus=tunnus):
                self.assertIn(tunnus, html)
        # Sivun oma tyyli on koskematon.
        self.assertIn("--rubric:#9d1b18", html)


if __name__ == "__main__":
    unittest.main()
