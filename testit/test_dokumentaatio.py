#!/usr/bin/env python3
"""Dokumentaation rakenteen testit.

`CLAUDE.md` oli 2767 riviä ja 164 kB, ja se ladattiin kokonaan joka
istunnon alussa. Se pilkottiin 2026-09-09 hakemistoksi, jonka luvut ovat
`docs/`-hakemistossa ja jonka toistuva työnkulku on skillinä. Jako pysyy
hyödyllisenä vain jos hakemisto pysyy pienenä ja viittaukset ehjinä —
kumpikin unohtuu käsin, joten ne testataan.
"""

import pathlib
import re
import unittest

JUURI = pathlib.Path(__file__).resolve().parent.parent

# Hakemistotiedoston koko raja. Se on nimenomaan hakemisto: jos se kasvaa
# yli tästä, joku luku kuuluu omaan tiedostoonsa docs/-hakemistoon.
CLAUDE_MD_RAJA = 150

SKILLI = JUURI / ".claude/skills/korvakuulokorjaus/SKILL.md"
LOKI = JUURI / "docs/tyopaivakirja"


def markdownit():
    """Kaikki repon omat .md-tiedostot; ei generoituja eikä sivuston omia."""
    tiedostot = [JUURI / n for n in ("CLAUDE.md", "README.md",
                                     "YHDISTAMINEN.md")]
    tiedostot += [p for p in sorted((JUURI / "docs").rglob("*.md"))
                  if p.parent.name != "suunnitelmat"]
    tiedostot.append(SKILLI)
    return tiedostot


class Hakemisto(unittest.TestCase):
    def test_claude_md_pysyy_hakemistona(self):
        rivit = (JUURI / "CLAUDE.md").read_text(encoding="utf-8").split("\n")
        self.assertLess(
            len(rivit), CLAUDE_MD_RAJA,
            f"CLAUDE.md on {len(rivit)} riviä. Se ladataan kokonaan joka "
            "istunnon alussa, joten pitkät luvut kuuluvat docs/-hakemistoon "
            "ja tänne vain viittaus niihin.")

    def test_hakemisto_viittaa_joka_docs_tiedostoon(self):
        """Tiedosto jota hakemisto ei mainitse jää lukematta."""
        teksti = (JUURI / "CLAUDE.md").read_text(encoding="utf-8")
        for p in sorted((JUURI / "docs").rglob("*.md")):
            suhteellinen = p.relative_to(JUURI).as_posix()
            if "suunnitelmat" in suhteellinen:
                continue          # niihin viitataan hakemistona
            with self.subTest(tiedosto=suhteellinen):
                # Työpäiväkirjan merkintöihin riittää viittaus sen
                # hakemistosivulta; muut mainitaan CLAUDE.md:ssä itse.
                lahde = teksti
                if p.parent.name == "tyopaivakirja" and p.name != "README.md":
                    lahde = (LOKI / "README.md").read_text(encoding="utf-8")
                self.assertIn(p.name, lahde)


class Viittaukset(unittest.TestCase):
    def test_jokainen_markdown_linkki_osoittaa_olemassa_olevaan(self):
        for tiedosto in markdownit():
            teksti = tiedosto.read_text(encoding="utf-8")
            for kohde in re.findall(r"\]\(([^)#\s]+)\)", teksti):
                if kohde.startswith(("http://", "https://", "mailto:")):
                    continue
                with self.subTest(tiedosto=tiedosto.name, linkki=kohde):
                    self.assertTrue(
                        (tiedosto.parent / kohde).exists(),
                        f"{tiedosto.relative_to(JUURI)} viittaa kohteeseen "
                        f"{kohde}, jota ei ole")

    def test_mikaan_ei_viittaa_claude_md_n_siirrettyihin_lukuihin(self):
        """Luku siirtyi docs/-hakemistoon, joten "CLAUDE.md:n luku X" harhauttaa.

        `CLAUDE.md`:n saa mainita ja siihen saa viitata — *Open*-taulukko on
        yhä siellä. Kiellettyä on viitata siihen luvulla, joka on siirretty
        pois. `docs/suunnitelmat/` on rajattu ulos: ne ovat 2026-09-04:n
        suunnitelmia ja kuvaavat tiedostoa sellaisena kuin se silloin oli.
        """
        siirretyt = {}
        for tiedosto in markdownit():
            if tiedosto.name == "CLAUDE.md":
                continue
            for rivi in tiedosto.read_text(encoding="utf-8").split("\n"):
                if re.match(r"#{1,2} \S", rivi):
                    siirretyt[rivi.lstrip("# ").strip()] = tiedosto.name

        for tiedosto in markdownit():
            if tiedosto.name == "CLAUDE.md":
                continue
            teksti = tiedosto.read_text(encoding="utf-8")
            for osuma in re.finditer(r"CLAUDE\.md", teksti):
                lahi = teksti[osuma.end():osuma.end() + 200]
                for otsikko, omistaja in siirretyt.items():
                    if len(otsikko) < 12 or omistaja == tiedosto.name:
                        continue
                    with self.subTest(tiedosto=tiedosto.name, luku=otsikko):
                        self.assertNotIn(
                            otsikko, lahi,
                            f"{tiedosto.relative_to(JUURI)} viittaa "
                            f"CLAUDE.md:n lukuun *{otsikko}*, joka on "
                            f"tiedostossa {omistaja}")

class Skilli(unittest.TestCase):
    def test_skillilla_on_nimi_ja_kuvaus(self):
        teksti = SKILLI.read_text(encoding="utf-8")
        self.assertTrue(teksti.startswith("---\n"))
        frontmatter = teksti.split("---")[1]
        self.assertIn("name: korvakuulokorjaus", frontmatter)
        self.assertIn("description:", frontmatter)

    def test_kuvaus_kertoo_milloin_skilli_otetaan_kayttoon(self):
        """Kuvaus on ainoa osa skillistä joka on kontekstissa aina.

        Jos se ei nimeä laukaisevia tilanteita, skilli ei lataudu silloin
        kun sitä tarvittaisiin.
        """
        frontmatter = SKILLI.read_text(encoding="utf-8").split("---")[1]
        for sana in ("syllable", "note", "korjaa_kasin.py"):
            with self.subTest(sana=sana):
                self.assertIn(sana, frontmatter)


class Tyopaivakirja(unittest.TestCase):
    def test_jokainen_merkinta_on_hakemistosivun_taulukossa(self):
        hakemisto = (LOKI / "README.md").read_text(encoding="utf-8")
        for p in sorted(LOKI.glob("*.md")):
            if p.name == "README.md":
                continue
            with self.subTest(merkinta=p.name):
                self.assertIn(f"({p.name})", hakemisto)

    def test_taulukko_ei_viittaa_puuttuvaan_merkintaan(self):
        hakemisto = (LOKI / "README.md").read_text(encoding="utf-8")
        for nimi in re.findall(r"\]\((20\d\d-[^)]+\.md)\)", hakemisto):
            with self.subTest(merkinta=nimi):
                self.assertTrue((LOKI / nimi).exists())

    def test_merkintojen_nimet_alkavat_paivamaaralla(self):
        for p in sorted(LOKI.glob("*.md")):
            if p.name == "README.md":
                continue
            with self.subTest(merkinta=p.name):
                self.assertRegex(p.name, r"^20\d\d-\d\d-\d\d-")


if __name__ == "__main__":
    unittest.main()
