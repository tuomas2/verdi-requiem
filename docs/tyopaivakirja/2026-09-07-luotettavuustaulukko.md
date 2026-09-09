*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-07 (b): the reliability table is now a committed Markdown file

The site's one link to the reliability detail pointed at
`luotettavuus.py` on GitHub — a reader who wanted to know how far to trust
their part landed in Python source, with the table spread across a dict of
`namedtuple`s. `luotettavuus.py` now **generates `LUOTETTAVUUS.md`** and the
site, `README.md` and the recipe link there instead.

`markdown()` builds the whole file: the marks and their meanings, the
17 × 4 grid of marks, and the per-movement justifications. Three details worth
keeping:

- **The legend is data, not prose.** `MERKINNAT` lists the five marks with a
  generic description each, and a test asserts that every mark `tila()` can
  return appears in it — a new mark cannot reach the file unexplained.
- **Voices with the same justification are grouped.** The three upper voices
  usually share one, and repeating it three times per movement would bury the
  places where they differ. The grouping is by identical `Tila`, in `AANET`
  order, so `II·4`'s soprano stays on its own row where it belongs.
- **The defaults are stated once, in the intro and in *Perustelut*, and the
  per-movement list holds only the exceptions.** That is the same shape the
  table itself has, so the generated file cannot drift from it.

The file is generated **and committed**, so GitHub renders it directly.
That combination can go stale, so `test_luotettavuus.py` compares the
committed bytes against `markdown()` and names the fix in the failure message
(`aja python3 luotettavuus.py`). CI runs the tests, so a stale file is caught
before it is published.

`polut.py` is deliberately not used for the output path: it routes score
files, and this is documentation at the repo root.

## Verification

- 193 tests (188 before, +5).
- The site builds and its only reliability link now reads
  `blob/main/LUOTETTAVUUS.md`; a test pins that `luotettavuus.py` no longer
  appears in the page at all, and the existing test that the page carries no
  per-movement marks (`✔`) still passes.
