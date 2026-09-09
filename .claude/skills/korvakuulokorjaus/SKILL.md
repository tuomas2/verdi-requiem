---
name: korvakuulokorjaus
description: >
  Use when the singer reports a wrong, missing or extra syllable, a wrong
  note, a wrong rhythm, a stray accidental or a layout error in the Verdi
  Requiem scores — anything heard or seen while reading a part. Holds the
  proven method: which layer the fix belongs in (korjaa_kasin.py table vs.
  yhdista.py bug vs. korjaa_sanat.py), how to locate the bar and page
  arithmetically, the confirm-a-hypothesis rule, the cross-checks, and the
  rebuild-and-verify commands. Trigger on reports like "bar 653 should be C",
  "the part is missing a syllable", "these words are backwards", or Finnish
  equivalents ("tahdissa 88 on väärä rytmi", "sana puuttuu").
---

# Recipe: a singer reports a wrong syllable by ear

*References below of the form* **2026-09-03 (c)** *are dated work-log entries;
`docs/tyopaivakirja/README.md` maps each date to its file. The method chapters
are in `docs/menetelmat/`.*

More of these are coming — the choir rehearses weekly and the user reads along.
This is the method that has worked, in order, with the traps that cost time
when they were skipped. It is written for the chorus bass because that is the
line the user reads, but nothing in it is bass-specific.

## 0. Decide which layer the fix belongs in — before touching anything

| Symptom | Layer | File |
|---|---|---|
| Movement I chorus bass: wrong/missing/extra syllable | hand-corrections table | `korjaa_kasin.py`, `OSA_I.korjaukset` |
| Movement 02 (II·1 Dies irae) | hand-corrections table | `korjaa_kasin.py`, `OSA_II1` |
| Liber scriptus (II·4), any voice | hand-corrections table | `korjaa_kasin.py`, `OSAT_II4` |
| Movement 07 (II·6 Rex tremendae) | hand-corrections table | `korjaa_kasin.py`, `OSA_II6` |
| Movement 11 (Lacrymosa), any voice | hand-corrections table | `korjaa_kasin.py`, `OSA_II10_KUORO_B` / `OSA_II10_DIVISI` |
| Movement 13 (IV Sanctus) | hand-corrections table | `korjaa_kasin.py`, `OSA_IV` |
| Movement 16 (VII Libera me) | hand-corrections table | `korjaa_kasin.py`, `OSA_VII` |
| Any movement: the source file is right but the **part** is wrong | tool bug | `yhdista.py` + a test |
| Movements 14/II·9b: wrong syllable | still baked into the source `.mxl` | see the last section below |
| A passage is **missing entirely** | copy it from `musescore/` if the figure already exists elsewhere in the part | `kopioi_tahti`, see *2026-09-03 (b)* |
| Systematic OCR text error in an OMR movement | PDF-driven pass | `korjaa_sanat.py` |
| A **key signature** in the wrong bar (a stray natural or sharp over a rest) | whole-file table, **not** a `korjaukset` row — every staff carries the change | `korjaa_kasin.py`, `SAVELLAJIT` |
| A word printed **without its hyphens** (`re qui em,`), or two words run together (`Do-na-e-is`) | the syllables are right and `syllabic` is wrong; one row gives the whole sentence's hyphenation | `korjaa_kasin.py`, a `tavutus` row |
| A **wrong or missing Finnish gloss** | glossary, not score data | `suomennos.py`, `SANASTO` |

A movement without a table yet is one `Osa` row away from having one: point
`mxl` at the untouched source, `out` at a new `-kasin.mxl`, and add the file
name to `yhdista.py`'s `MOVEMENTS`, `MAPPING`, `DIES_IRAE_ALUT` (Dies irae
sub-movements only), `SANCTUS` (movement 13 only) and the pin in
`test_yhdista.py`. Four movements moved over that way on 2026-09-04.

**The source-vs-part check is one command and it settles the layer question:**

    python3 nayta.py 01-Verdi_Requiem-kasin.mxl 108 108 --osasto P16
    python3 nayta.py stemma-basso-1.mxl 108 108

If the two agree, the data is wrong. If they differ, `yhdista.py` is wrong —
that is exactly how the bar 108 two-lyric-rows bug was caught, and a data fix
would have papered over it while leaving S/A/T broken.

## 1. Read the data, never the page, first

`nayta.py` prints notes with pitch, duration, tie, voice and **lyric row** per
bar. The lyric row (`number`) and the voice are invisible in the printed music
but decide several whole classes of bug, so guessing from a PDF or from
MuseScore's window cannot find them.

Measure numbers repeat — every main movement restarts at 1 (Dies irae is the
exception, 1–701 continuous) — so `nayta.py` prints the movement title beside
each hit. Check you are looking at the movement the singer meant.

## 2. Trust the singer's bar number, but locate the bar independently

Since 2026-09-02 the parts number every bar, so a reported number is reliable.
Reports from before that were counted from the system start and can be off by
one — and one of the three in that batch had an obvious digit slip (`165` for
`125`). Confirm by the **words**, not the number: if the singer says
"e-le-i-son starting at 125" and bar 125 does start one, you have the right
bar.

## 3. Find the page arithmetically, then render

Do not thumb through the PDF. Two ways, both exact:

- The OMR files keep the source's own `<print new-page>` / `<print
  new-system>`, so the page holding any bar is computable. For movement 01:
  page 3 = 50–73, 7 = 106–114, 9 = 124–128, 10 = 129–140.
- The source PDFs print their own bar number at each system start (movement
  01 at 50, 59, 66 …). Read that number rather than counting barlines — the
  Agnus Dei 59–74 attempt failed precisely by counting.

Then `mutool draw -r 200` for orientation and `-r 450` cropped to one staff to
read it. 450 dpi cropped to a single staff's own lyric row is the setting that
works; a full page at 450 is unreadable at review size and 200 dpi is too
coarse for a syllable over a notehead.

**For a symbol rather than a syllable, do not render at all.** These PDFs
carry the music itself as font glyphs, so `mutool draw -F stext` gives every
clef, accidental and rest an exact coordinate — and combining that x with the
bar's own x, computed from the OMR's `<measure width>` values, names the bar a
symbol stands in without anyone looking at a picture. That is how the movement
01 key signatures were settled; see *2026-09-07 (b)*.

## 4. Confirm a named hypothesis; never derive content from pixels

This is the whole trick and it is worth restating every time. Ask *"is there a
syllable over this notehead, and is it `i`?"* — not *"what is written here?"*.
Confirming a named guess at 200–450 dpi is reliable. Deriving pitches, bar
boundaries or text from a rendered page is not, and has produced
self-contradictory reads on repeat attempts (Agnus Dei bars 59–74).

Identify the right staff by counting from the top and checking the clef and
the printed cue labels. **The staff count changes from page to page** in
movement 01: the four soloists' staves are omitted where they are silent, so
"the 8th staff" is not stable. On page 3 there are four vocal staves (chorus
only); on pages 7 and 9 there are eight (soloists then chorus).

## 5. Cross-check against a second source when one exists

- The other three chorus voices in the same file — they usually sing the same
  words at the same bars, and a lone disagreement is a strong signal.
- `musescore/` — correct notes and piano, **no lyrics at all**, and it is a
  condensed chorus-only cut. It settles note questions, never text questions.
  **Never quote a bar number obtained from a `difflib` alignment against it**;
  the two sides have different lengths and the alignment's numbers are
  approximate. That is exactly how the phantom "movement 01 is missing bars
  79–93" claim got into this file for a week.
- When comparing pitches, fold chord members in, or compare `Bass 1` and
  `Bass 2` as a pair. A skipped `<chord>` member does not look like missing
  data, it looks like a **wrong note** — the most alarming possible false
  positive.

## 6. Write the fix as a table row, not as an edit

Add a line to `korjaa_kasin.py` with the source page number in the comment.
Each operation asserts its own precondition, so a fix that would land on the
wrong note stops the run instead of silently corrupting a bar. Then:

    python3 korjaa_kasin.py --kuiva      # lue mitä se aikoo tehdä
    python3 korjaa_kasin.py

If the singer's reading disagrees with the source PDF, **do it their way and
say so in the comment** — they are the one in the room with the conductor —
but record what the PDF says so it is one line to revert. Bar 51's `om-nis` is
the standing example.

## 7. Rebuild, then read the result back as an image

    python3 korjaa_sanat.py            # vain jos PDF-sanat muuttuivat
    python3 korjaa_kasin.py
    python3 yhdista.py Verdi-Requiem-koko.mxl
    python3 yhdista.py stemma-basso-1.mxl --stemma "Basso I"
    python3 sivuotsikot.py stemma-basso-1.mxl    # sivujen osaotsikot
    mscore -S tiivistys.mss -o stemmat/stemma-basso-1.pdf stemmat/stemma-basso-1.mxl
    python3 harjoitus.py --stemma "Basso I"
    python3 sisallys.py                # jos sivumäärät muuttuivat
    python3 luotettavuus.py            # jos luotettavuustaulukko muuttui
    python3 sivusto.py                 # jos sivustolle näkyvä tieto muuttui

The Python commands take bare filenames — `polut.py` finds the directory. Only
`mscore` needs a real path, since it knows nothing about the convention.

**A fix that changes what a voice is worth also belongs in `luotettavuus.py`.**
That table is what the site tells a reader about how far to trust each part,
and it is the one thing in this pipeline that no test can derive from the data.
Run `python3 luotettavuus.py` after editing it — `LUOTETTAVUUS.md` is generated
but committed, and a test fails if it is stale.

`sivuotsikot.py` must run **after** `yhdista.py` (which rewrites the file from
scratch) and **before** rendering. It runs `mscore` itself, twice per part, to
read the computed page layout back.

Then render the finished part and **look at it**. Every session that skipped
this shipped something. Checks that have caught real problems:

- Per-staff note counts before and after. A lyric-only change must leave every
  count identical; anything else means content moved.
- `mscore` converts without `-f`.
- **`python3 suomennos.py --teksti <part>` — read the whole text as prose.**
  Cheap, and it catches what the page cannot: a word missing its hyphens, two
  words run together, a gloss that makes no sense. It found four defects the
  first time it was run.
- `python3 -m unittest discover -s testit -t .` — 265 tests.

## The one movement not yet in the table

Movement 14 (Agnus Dei) still has its fixes written straight into
`14-…-OMR-korjattu.mxl`, so that file is a hand-edited artefact and git is the
only record of what was changed. Movements 01 and 11 were in the same state
(01 until 2026-09-02, 11 until 2026-09-03) and both moved over. Movements 02,
07, 13 and 16 never had hand edits at all — they got their first tables on
2026-09-04, which needed no migration, only a new `Osa` row each.

**The method, twice proven.** Diff the hand-edited file against the file it was
derived from — a throwaway script comparing pitch, duration and lyric per note,
keyed by `(part, measure, note index)` — and write each difference into a new
`Osa` entry. Then the acceptance test writes itself: regenerate from the rawest
input and diff the result against the file the hand edits had produced. It must
come out identical except for the changes you *meant* to add. Movement 01
reproduced byte for byte; movement 11's 43 rows reproduced its file exactly,
with the 7 intended new edits as the only difference. Restore the raw source
from git at the same time (`git show <first commit>:<file> > <file>`) — for
movement 11 that meant going back past *two* earlier hand-edit commits, one of
which was a single `syllabic` change easy to miss.

Movement 14's diff will be larger — it includes note-level fixes and two tacet
spans — but the danger warning above `korjaa_sanat.py` disappears for each
movement that moves over.
