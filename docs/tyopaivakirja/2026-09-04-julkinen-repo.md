*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-04 (later): the repository was prepared for publication

The user asked to make this directory a public repo (`tuomas2/verdi-requiem`)
with a GitHub Pages site, explicitly so that **someone else can carry on
improving the scores**. That purpose drove two decisions: `CLAUDE.md` ships
as-is because it is the most thorough account of the work, and the site leads
with a reliability page, because without one the eight parts look uniform and
they are not.

## The directory now has four data directories, and the rule that made it cheap

    lahteet/   originals: 16 CPDL .mxl, 2 raw -OMR.mxl, 4 source PDFs,
               3 Audiveris projects, 3 CPDL .mscz. Never edited
    johdetut/  *-OMR-korjattu.mxl, *-kasin.mxl, Verdi-Requiem-koko.mxl
    stemmat/   8 parts + stemmat-sisallys.txt
    harjoitus/ practice .mscz, not in version control

The naive approach would have prefixed 117 filename literals. They live in
readable tables (`MOVEMENTS`, `MAPPING`, `korjaa_kasin.py`'s `Osa` rows), so
prefixing them would have been both error-prone and ugly. Instead **`polut.py`
derives the directory from the name**, which the project's own naming
convention already encodes: `-kasin.mxl` and `-OMR-korjattu.mxl` are derived,
`stemma*` is a part, everything else is a source. The tables were left
untouched and only **17 call sites** changed — the scripts keep their filenames
and their opening code in separate places, which is what made this work.

`polku()` returns a path containing a separator unchanged, so every command
still accepts either a bare name or a full path.

**The rule must not stay a silent assumption.** `test_polut.py` asserts that
every filename mentioned in any table resolves to a file that exists in
exactly the directory the rule names, and that it exists in only one of the
four. A stray copy would otherwise be read silently instead of the intended
file.

## `.mxl` output is not byte-reproducible, and the plan was wrong about it

The acceptance criterion for the move was "the chain produces identical
output". The first version of it compared bytes, which cannot work:
`yhdista.py` writes with `zipfile.writestr`, which stamps **the current time**
into every zip entry, so two runs over identical data differ. Measured, not
assumed — two zips written 1.2 s apart have different hashes and different
`date_time` values.

The comparison is therefore over the **extracted `score.xml`**. Done that way,
37 files came out identical before and after the move, zero differences.

A fixed `date_time` would make `.mxl` output reproducible, which would be a
nice property for a public repo. Not done: it would change every derived
file's bytes once, and doing it inside the move commit would have hidden
exactly the differences the comparison was there to catch.

## `sivuotsikot.py` is deterministic, which made the check cheap

Worth knowing, because it is not obvious for a script whose output depends on
MuseScore's computed layout: re-running it on a freshly merged part reproduced
the committed file's content exactly, in five seconds per part. So the "whole
chain" comparison really can cover the whole chain, page labels included.

## The `korjaa_sanat.py` trap caught the plan itself

The implementation plan instructed running `korjaa_sanat.py` to take the
before-comparison. That would have **silently destroyed** movement 14's and
II·9b's hand fixes — the exact failure this file already warns about — and
worse, it would have recorded the damaged state as the baseline. Caught on the
critical read-through before executing. The chain is now compared without it,
and the script is exercised with `--kuiva`, which writes nothing.

The warning at *Fixing OMR lyrics from the source PDFs* is therefore not
theoretical, and it is now repeated in `README.md` where a new contributor
will see it.

## `luotettavuus.py`: default plus exceptions, and one wrong generalisation

The reliability table is 17 movements × 4 voices = 68 cells, but it is not 68
hand-written rows. It is a default (`tarkistamatta`) plus 15 exceptions, and
"no chorus in this movement" is **computed from `MAPPING`** rather than
maintained — so the seven solo movements need no upkeep at all.

The first version also propagated a soprano entry to alto and tenor, on the
reasoning that the upper voices share a fate. That is true in movements I,
II·9b and V, and **wrong in II·4**, where the soprano is precisely the voice
that disagrees with the other three — the propagation marked alto and tenor as
defective for a reason that is an argument in their favour. Voices are now
listed explicitly in every exception.

`test_luotettavuus.py` pins that `varmistettu` appears **only** for `Kuoro B`
in movements V and II·10, because the mark is a promise to the reader.

## The reference edition is named at last: Edition Peters

Every earlier section in this file says "the choir's rehearsal book" without
naming it. It is **Edition Peters**, and that matters in two ways.

It is what `DIES_IRAE_ALUT` was derived from, so **the parts' bar numbers match
Edition Peters** — which is the single most practical fact for a singer holding
a score, and it is now stated on the site, in `README.md` and in `yhdista.py`'s
own comment.

It is also what the chorus bass has been checked against by hand, notes and
text both, on top of being sung through in rehearsals. That is why
`luotettavuus.py` gives `Kuoro B` a default of its own (`◑ käyty läpi`) rather
than `tarkistamatta`: the bass has no unchecked movements. It is deliberately
**not** promoted to `✔`, which is reserved for a whole movement compared note
by note and syllable by syllable. The two kinds of evidence find different
things — singing finds the editorial errors that checking against the printed
page cannot, and systematic comparison finds what the ear misses, such as one
absent syllable inside a melisma. `luotettavuus.REFERENSSI` holds the name in
one place, and a test pins it.

## The site

`sivusto.py`, standard library only, four pages: front, the Latin/Finnish
text, parts, reliability. Two things are read rather than restated:
bar ranges come from the merged score's own `<measure number>` values (so
`tahtivalit()["II·10"]` returning `(624, 701)` independently confirms the
whole numbering chain), and page numbers come from `stemmat-sisallys.txt`.
The contents table therefore cannot drift from the parts.

`requiem.html` — the user's own Latin/Finnish page — is included verbatim with
only a navigation bar injected after `<body>`. It is not refactored onto the
shared stylesheet; the visual consistency comes from the new pages adopting
*its* colour and type tokens instead.

Built in CI and **not committed**, so it cannot go stale unnoticed. The
workflow installs `mupdf-tools` because 15 tests read source PDFs with
`mutool`; MuseScore is not needed, since no test invokes it and the parts'
PDFs come from the repo.

The site is destined for **requiem.tuomasairaksinen.fi**, so `sivusto.py`
writes a `CNAME` file into the output. Setting the custom domain in the Pages
settings alone would work until those settings are reset; a file in the
published directory is the durable form. It still needs a DNS `CNAME` record
pointing at `tuomas2.github.io`.

The deploy job is gated on `github.event.repository.visibility == 'public'`.
The repo starts private, and `deploy-pages` fails with a bare "Not Found" in a
private repo — a permanently red CI that says nothing useful. Keying the
condition to visibility means nothing has to be remembered: publication starts
working by itself when the repo is made public (Pages still has to be switched
on once, Settings → Pages → Source: GitHub Actions).

The tests live in `testit/`, run from the repo root:
`python3 -m unittest discover -s testit -t .`. The `-t .` keeps the root on
`sys.path` so `import yhdista` works, and `testit/__init__.py` exists because
Python 3.9's `discover` refuses a start directory that is not importable.

## History: removals rewritten, moves not

`musescore/` was tracked from early on, so `git rm` was not enough.
`git-filter-repo` removed `musescore/**`, `harjoitus-*.mscz` and
`Verdi-Requiem-koko-oma.mscz` from all 59 commits — plus one thing the plan had
missed, a 3.0 MB `harjoitus-basso-1.mscz.autosave` committed before
`*.autosave` was added to `.gitignore`. Found by grepping the object database
for what should not be there, which is the check worth repeating.

**The directory moves were made as an ordinary commit, deliberately.** Renaming
paths throughout history would have left every old commit internally
inconsistent: the tree would say `lahteet/01-Verdi_Requiem.mxl` while the same
commit's `yhdista.py` still said `01-Verdi_Requiem.mxl`. As a plain `git mv`,
every historical commit stays self-consistent and runnable.

Result: `.git` 127 MB → 51 MB, working tree 162 MB → 75 MB, all 59 commits
preserved. A second `filter-repo` pass rewrote the author address from the
user's work email to their personal one; `user.email` is now also set globally,
which was safe because it had never been set globally at all — the work address
was this repo's own local setting.

## Verification

- 169 tests (136 before, +33).
- The chain reproduces identical extracted XML before and after the move and
  after both history rewrites; 1807 measures throughout.
- Object database greps clean for `musescore`, `autosave` and `koko-oma`; the
  three remaining `.mscz` are CPDL's own sources in `lahteet/`.
- The repo was **not published**: the user does that themselves. Everything up
  to and including the history rewrite is done.
