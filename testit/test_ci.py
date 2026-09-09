#!/usr/bin/env python3
"""CI-workflowien testit.

Testit ajettiin ennen askeleena "Julkaise sivusto" -workflowssa, joka
käynnistyi vain mainissa ja pull requesteissa: muissa haaroissa ei ollut
ajoa lainkaan, ja punainen rasti luki "julkaisu hajosi" vaikka vika oli
testeissä. Nyt ne ovat oma workflow, jota julkaisu kutsuu.

Nämä testit pinnaavat sen rakenteen. Ne lukevat YAML:n tekstinä eivätkä
`yaml`-moduulilla: repo on puhdasta vakiokirjastoa eikä CI asenna
riippuvuuksia, joten `import yaml` kaatuisi juuri siellä missä sen pitäisi
toimia.
"""

import pathlib
import re
import unittest

JUURI = pathlib.Path(__file__).resolve().parent.parent
TESTIT_YML = JUURI / ".github/workflows/testit.yml"
SIVUSTO_YML = JUURI / ".github/workflows/sivusto.yml"

# Komento on kirjoitettu muistiin kolmessa paikassa (README, skilli,
# CLAUDE.md); CI:n on ajettava täsmälleen sama.
TESTIKOMENTO = "python3 -m unittest discover -s testit -t ."


def teksti(polku):
    return polku.read_text(encoding="utf-8")


class Testityo(unittest.TestCase):
    def test_workflow_on_olemassa(self):
        self.assertTrue(TESTIT_YML.exists(), "testit.yml puuttuu")

    def test_ajaa_saman_komennon_kuin_dokumentaatio(self):
        self.assertIn(TESTIKOMENTO, teksti(TESTIT_YML))

    def test_ajetaan_myos_muissa_haaroissa_kuin_mainissa(self):
        """Tämä oli koko muutoksen syy: haarat jäivät ilman ajoa."""
        t = teksti(TESTIT_YML)
        self.assertIn("branches-ignore: [main]", t)
        self.assertIn("workflow_call:", t,
                      "julkaisun on voitava kutsua tätä, muuten main jää "
                      "testaamatta")

    def test_readmen_lupaama_python_versio_on_matriisissa(self):
        """README lupaa version; CI on ainoa paikka jossa lupaus tarkistuu."""
        luvattu = re.search(r"Python (\d+\.\d+), ei riippuvuuksia",
                            teksti(JUURI / "README.md"))
        self.assertIsNotNone(luvattu, "README ei enää kerro Python-versiota")
        self.assertIn(f"'{luvattu.group(1)}'", teksti(TESTIT_YML),
                      f"README lupaa Python {luvattu.group(1)}, mutta CI ei "
                      "aja sitä")

    def test_mutool_asennetaan(self):
        """15 testiä kaatuu exit 127:ään ilman sitä; mitattu."""
        self.assertIn("mupdf-tools", teksti(TESTIT_YML))


class Julkaisu(unittest.TestCase):
    def test_julkaisu_ei_voi_ohittaa_testeja(self):
        """Vanhentunut LUOTETTAVUUS.md on testi, ja se on lupaus lukijalle."""
        t = teksti(SIVUSTO_YML)
        self.assertIn("uses: ./.github/workflows/testit.yml", t)
        # julkaise -> rakenna -> testit
        self.assertRegex(t, r"rakenna:\s*\n\s*needs: testit")
        self.assertRegex(t, r"julkaise:\s*\n\s*needs: rakenna")

    def test_sivuston_rakennus_ei_asenna_mutoolia(self):
        """Mitattu: sivusto.py rakentuu ilman mutoolia ja MuseScorea."""
        self.assertNotIn("mupdf-tools", teksti(SIVUSTO_YML))

    def test_testeja_ei_ajeta_kahdesti(self):
        """Sama commit testattaisiin kahdesti jos molemmat laukeaisivat.

        `testit.yml` jättää mainin väliin ja `sivusto.yml` hoitaa sen
        kutsumalla; pull requestit tulevat vain `sivusto.yml`:n kautta.
        """
        self.assertNotIn("pull_request", teksti(TESTIT_YML))
        self.assertIn("pull_request", teksti(SIVUSTO_YML))

    def test_julkaisu_on_yha_rajattu_julkiseen_repoon(self):
        """Privaatissa repossa deploy-pages kaatuisi virheeseen Not Found."""
        self.assertIn("github.event.repository.visibility == 'public'",
                      teksti(SIVUSTO_YML))


if __name__ == "__main__":
    unittest.main()
