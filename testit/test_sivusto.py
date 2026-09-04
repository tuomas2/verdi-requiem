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

    def test_valikossa_on_kaksi_sivua_ja_github(self):
        """Erillinen etusivu olisi väliporras. GitHub on mukana siksi, että
        aineiston parantaminen on osa projektin tarkoitusta."""
        self.assertEqual([nimi for _k, nimi, _s in sivusto.NAVI],
                         ["Stemmat", "Teksti", "GitHub"])
        self.assertIn(sivusto.GITHUB, [k for k, _n, _s in sivusto.NAVI])

    def test_jokaisella_valikkokohdalla_on_selite(self):
        for _kohde, nimi, selite in sivusto.NAVI:
            with self.subTest(nimi=nimi):
                self.assertTrue(selite.strip())

    def test_valikko_on_sama_molemmilla_sivuilla(self):
        """Tekstisivu sai aiemmin oman käsin kyhätyn valikkonsa, joka ehti
        jäädä jälkeen muista."""
        import re
        def kohteet(html):
            navi = html[html.index('<nav class="bar'):html.index("</nav>")]
            return re.findall(r'<a href="([^"]*)"[^>]*><b>([^<]*)</b>'
                              r'<i>([^<]*)</i>', navi)
        self.assertEqual(kohteet(sivusto.stemmasivu()),
                         kohteet(sivusto.tekstisivu()))

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

    def test_tunnetut_puutteet_johdetaan_taulukosta(self):
        """Maininta jäisi käsin kirjoitettuna jälkeen kun taulukko muuttuu."""
        self.assertEqual(sivusto.puutteelliset_osat(),
                         ["Liber scriptus", "Lacrymosa", "Agnus Dei"])
        self.assertIn("Agnus Dei", sivusto.luotettavuusteksti())

    def test_yksityiskohdat_ovat_linkin_takana_eivat_sivulla(self):
        """Sivun pitää pysyä kevyenä: erittely on repossa."""
        html = sivusto.stemmasivu()
        self.assertIn("luotettavuus.py", html)
        # Ei osakohtaista merkkitaulukkoa eikä perusteluja sivulla.
        self.assertNotIn("✔", html)
        self.assertNotIn("melisma", html)

    def test_lahde_on_linkitetty(self):
        """Aineisto on CPDL:n editioita; lähde kuuluu näkyä sivulla eikä
        vain repossa."""
        html = sivusto.stemmasivu()
        self.assertIn(sivusto.CPDL, html)
        self.assertIn("cpdl.org", sivusto.CPDL)

    def test_referenssiedition_nimi_nakyy(self):
        """Käytännössä tärkein yksittäinen tieto laulajalle: täsmäävätkö
        tahtinumerot siihen nuottiin joka hänellä on kädessä."""
        html = sivusto.stemmasivu()
        self.assertIn("Edition Peters", html)

    def test_ei_teknista_selostusta(self):
        """Sivu on laulajalle, ei kehittäjälle."""
        html = sivusto.stemmasivu()
        for tekninen in ["oktaavivirhe", "konelukemisen", "OMR", "sanapeitto"]:
            with self.subTest(sana=tekninen):
                self.assertNotIn(tekninen, html)


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

    def test_stemmat_kopioidaan_molemmissa_muodoissa(self):
        with tempfile.TemporaryDirectory() as d:
            sivusto.rakenna(d)
            for _nimi, pdf in sivusto.STEMMAT:
                for tiedosto in (pdf, pdf[:-4] + ".mxl"):
                    with self.subTest(tiedosto=tiedosto):
                        self.assertTrue(
                            os.path.exists(os.path.join(d, "stemmat", tiedosto)))

    def test_koko_partituuri_on_ladattavissa(self):
        with tempfile.TemporaryDirectory() as d:
            sivusto.rakenna(d)
            self.assertTrue(
                os.path.exists(os.path.join(d, "Verdi-Requiem-koko.mxl")))
            self.assertIn("Verdi-Requiem-koko.mxl", sivusto.stemmasivu())


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
        self.assertIn(sivusto.GITHUB, sivusto.tekstisivu())

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
