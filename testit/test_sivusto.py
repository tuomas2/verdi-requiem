#!/usr/bin/env python3
"""Sivustogeneraattorin testit.

Sivuston tiedot luetaan samoista vakioista jotka ohjaavat stemmojen
tuotantoa, joten testien tärkein tehtävä on varmistaa ettei mikään osa katoa
matkalla ja että sivunumerot vastaavat oikeasti tuotettuja stemmoja.
"""

import os
import tempfile
import unittest

import luotettavuus
import sivusto
import suomennos
import yhdista


def johdantoteksti(html):
    """Otsikkokappaleen teksti ilman merkkausta ja rivinvaihtoja.

    Kappale on ladottu lähteessä usealle riville, joten pelkkä assertIn
    lauseeseen osuisi rivinvaihtoon eikä tekstiin.
    """
    import re
    alku = html.index('class="standfirst"')
    osa = html[html.index(">", alku) + 1:html.index("</header>")]
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", osa)).strip()


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

    def test_valikon_luokka_ei_tormaa_tekstisivun_omiin_tyyleihin(self):
        """requiem.html:llä on omat .bar- ja .bar-inner-sääntönsä. Kun
        valikolla oli sama luokkanimi, niistä vuoti justify-content ja
        valikko renderöityi eri levyisenä eri sivuilla."""
        oma = open("sivusto/requiem.html", encoding="utf-8").read()
        for luokka in ("valikko", "valikko-sisus"):
            with self.subTest(luokka=luokka):
                self.assertNotIn("." + luokka, oma)

    def test_valikon_ainoa_ero_sivujen_valilla_on_asemointi(self):
        """Tekstisivulla on jo oma tarttuva palkkinsa, joten kaksi
        päällekkäin tarttuvaa peittäisi sisältöä. Muuta eroa ei saa olla."""
        a = sivusto.VALIKKO_TYYLI
        b = sivusto.VALIKKO_TYYLI_STAATTINEN
        self.assertEqual(a.replace(".valikko{position:sticky;top:0;z-index:20;",
                                   ".valikko{position:static;"), b)

    def test_jokaisella_valikkokohdalla_on_selite(self):
        for _kohde, nimi, selite in sivusto.NAVI:
            with self.subTest(nimi=nimi):
                self.assertTrue(selite.strip())

    def test_valikko_on_sama_molemmilla_sivuilla(self):
        """Tekstisivu sai aiemmin oman käsin kyhätyn valikkonsa, joka ehti
        jäädä jälkeen muista."""
        import re
        def kohteet(html):
            navi = html[html.index('<nav class="valikko'):
                        html.index("</nav>")]
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

    def test_kertoo_etta_vain_basso_on_varmistettu(self):
        self.assertIn("kuorobasso", sivusto.stemmasivu().lower())

    def test_varaus_on_ominaisuuslistan_rivi(self):
        """Ominaisuudet ja varaus samassa listassa, ei kahdessa paikassa.

        Aiemmin sama asia sanottiin sekä omassa laatikossaan että
        otsikkokappaleessa, ja kappale toisti muutenkin listan lupaukset.
        """
        html = sivusto.stemmasivu()
        self.assertIn("<dt%s>%s</dt>" % (' class="huomio"', sivusto.VIRHEET),
                      html)
        self.assertIn(sivusto.luotettavuusteksti(), html)
        self.assertNotIn('class="varoitus"', html)

    def test_johdanto_kertoo_varauksen_ennen_latauslinkkeja(self):
        """Latauslista on ominaisuuslistan yläpuolella, joten varauksesta
        pitää näkyä lyhennetty muistutus jo otsikkokappaleessa."""
        html = sivusto.stemmasivu()
        self.assertIn("pääosin tarkistamatta", johdantoteksti(html))
        self.assertLess(html.index("tarkistamatta"),
                        html.index('class="lataukset"'))

    def test_tunnetut_puutteet_johdetaan_taulukosta(self):
        """Maininta jäisi käsin kirjoitettuna jälkeen kun taulukko muuttuu."""
        self.assertEqual(sivusto.puutteelliset_osat(),
                         ["Requiem & Kyrie", "Liber scriptus", "Lacrymosa",
                          "Agnus Dei"])
        self.assertIn("Agnus Dei", sivusto.luotettavuusteksti())

    def test_yksityiskohdat_ovat_linkin_takana_eivat_sivulla(self):
        """Sivun pitää pysyä kevyenä: erittely on repossa.

        Linkki menee generoituun md-tiedostoon eikä lähdekoodiin: lukija
        haluaa taulukon, ei Pythonia.
        """
        html = sivusto.stemmasivu()
        self.assertIn(luotettavuus.MD_TIEDOSTO, html)
        self.assertNotIn("luotettavuus.py", html)
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


class Ominaisuudet(unittest.TestCase):
    """Stemmojen ominaisuuslista.

    Luvut listalla ovat johdettuja: käsin kirjoitettu sivumäärä tai
    tahtiväli jäisi jälkeen seuraavassa muutoksessa, ja sivu lupaa ne
    lukijalle.
    """

    @classmethod
    def setUpClass(cls):
        cls.html = sivusto.stemmasivu()

    def test_lista_on_latauslistan_jalkeen_ja_partituurin_edella(self):
        self.assertIn("Ominaisuudet", self.html)
        self.assertLess(self.html.index('class="lataukset"'),
                        self.html.index("Ominaisuudet"))
        self.assertLess(self.html.index("Ominaisuudet"),
                        self.html.index("Koko partituuri"))

    def test_sivumaarat_luetaan_sisallystiedostosta(self):
        sivut = sivusto.sivumaarat()
        self.assertTrue(sivut)
        self.assertIn(f"{min(sivut)}\u2013{max(sivut)} sivua", self.html)

    def test_dies_iraen_tahtivali_lasketaan_lahteista(self):
        alku, loppu = sivusto.dies_irae_vali()
        self.assertEqual((alku, loppu), (1, 701))
        self.assertIn(f"{alku}\u2013{loppu}", self.html)

    def test_suomennoksen_fonttikoko_tulee_moduulista(self):
        # Sivu ei saa kertoa eri kokoa kuin se, jolla suomennos ladotaan.
        self.assertIn(suomennos.KOKO.replace(".", ",") + " pt", self.html)

    def test_jokaisella_kohdalla_on_nimi_ja_selitys(self):
        nimet = self.html.count("<dt>")
        self.assertEqual(nimet, self.html.count("<dd>"))
        self.assertGreaterEqual(nimet, 5)


class Johdantokappale(unittest.TestCase):
    """Otsikkokappale on tiivistelmä sivun sisällöstä.

    Se oli ennen yksi irrallinen lause, joka toisti ominaisuuslistan
    lupaukset sanasta sanaan. Tiivistelmä kertoo saman asian ylemmältä
    tasolta: mitä sivulta saa, mihin se on tehty ja missä kunnossa se on.
    """

    @classmethod
    def setUpClass(cls):
        cls.teksti = johdantoteksti(sivusto.stemmasivu())

    def test_on_muutaman_lauseen_mittainen(self):
        lauseita = self.teksti.count(". ") + self.teksti.count(".\n")
        self.assertGreaterEqual(lauseita, 2)
        self.assertLessEqual(lauseita, 5)

    def test_kertoo_mita_sivulta_saa(self):
        for asia in ["PDF", "MusicXML", "partituuri"]:
            with self.subTest(asia=asia):
                self.assertIn(asia, self.teksti)

    def test_ei_toista_listan_yksityiskohtia(self):
        """Tiivistelmä pysyy ylemmällä tasolla: mitat, pistekoot ja
        tahtivälit ovat ominaisuuslistan asia, eivät johdannon."""
        for yksityiskohta in [" mm", " pt", "1–701", "29,3"]:
            with self.subTest(yksityiskohta=yksityiskohta):
                self.assertNotIn(yksityiskohta, self.teksti)

    def test_referenssiedition_nimi_tulee_moduulista(self):
        self.assertIn(luotettavuus.REFERENSSI, self.teksti)


class Muotoilu(unittest.TestCase):
    def test_sivuille_ei_jaa_muotoilemattomia_paikkamerkkeja(self):
        """f-merkin unohtaminen mallipohjasta ei näy mitenkään ennen kuin
        sivulla lukee {CPDL} — ja se ehti kerran julkaisuun asti."""
        import re
        for nimi, html in [("stemmat", sivusto.stemmasivu()),
                           ("teksti", sivusto.tekstisivu())]:
            jaljelle = re.findall(r"\{[A-Za-z_][A-Za-z_0-9.()\[\]]*\}", html)
            with self.subTest(sivu=nimi):
                self.assertEqual(jaljelle, [])

    def test_otsikkotyylit_ovat_samat_kuin_tekstisivulla(self):
        """Tekstisivu on itsenäinen omine tyyleineen, joten yhteinen ulkoasu
        on ylläpidettävä eikä se seuraa itsestään.

        Molemmat otsikkotasot ovat mukana: h2 yhtenäistettiin tekstisivun
        mittaan samalla kun stemmasivun sans-versaali h3 poistui.
        """
        import re
        def koko(css, valitsin):
            osuma = re.search(valitsin + r"\{[^}]*font-size:\s*([^;}]+)",
                              css, re.S)
            return osuma.group(1).strip() if osuma else None
        with open("sivusto/tyyli.css", encoding="utf-8") as f:
            jaettu = f.read()
        with open("sivusto/requiem.html", encoding="utf-8") as f:
            oma = f.read()
        for valitsin in ["h1", "h2"]:
            with self.subTest(valitsin=valitsin):
                self.assertIsNotNone(koko(jaettu, valitsin))
                self.assertEqual(koko(jaettu, valitsin), koko(oma, valitsin))

    def test_sivulla_on_yksi_otsikkotaso_luvuille(self):
        """Ominaisuudet oli ainoa h3 ja ainoa sans-versaaliotsikko: se yksin
        sai sivun näyttämään kahden tyylin sekoitukselta."""
        html = sivusto.stemmasivu()
        self.assertNotIn("<h3", html)
        self.assertEqual(html.count("<h2>"), 4)


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
    def test_sivulla_on_latauslinkki_jokaiselle_stemmalle(self):
        html = sivusto.stemmasivu()
        for _nimi, pdf in sivusto.STEMMAT:
            with self.subTest(pdf=pdf):
                self.assertIn(pdf, html)
                self.assertIn(pdf[:-4] + ".mxl", html)

    def test_ei_sisallystaulukkoa(self):
        """Taulukko oli kohinaa: sivunumerot ovat stemman omassa PDF:ssä ja
        osan nimi on joka sivun yläreunassa. Tahtinumeroinnin tarkistus
        elää test_yhdista.py:ssä."""
        html = sivusto.stemmasivu()
        self.assertNotIn("Mistä osa alkaa", html)
        self.assertNotIn("<table", html)


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
