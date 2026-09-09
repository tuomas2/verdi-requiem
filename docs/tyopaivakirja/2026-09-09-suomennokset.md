*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-09: a Finnish gloss under every Latin word

The singer asked whether each word's Finnish translation could be printed
under the lyrics in a smaller font — same idea as `sivusto/requiem.html`'s
parallel translation, but at the point in the music where the word is sung,
for learning Latin while singing. It can, it costs almost nothing, and
building it found four real defects that were already in the printed parts.

`suomennos.py` is the new module: a glossary, the placement, and a
proofreading tool. `yhdista.py` calls it last, `--ei-suomennosta` turns it
off.

## Three measurements that decided the design

- **The font size must ride on the syllable, not the style file.**
  MuseScore's `lyricsEvenFontSize` does nothing: set to 6 with
  `lyricsOddFontSize` 14, *both* rows came out at 14 pt. What works is
  MusicXML's `<text font-size="6.5">` inside the `<lyric>`. Measured by
  reading the rendered PDF's text layer (`mutool draw -F stext`), not by
  looking at the page.
- **It costs almost no pages.** Both bass parts stayed at 16, and the eight
  together went 131 → 133 pages (S I and T I one each). The worst case was
  measured first, before any glossary existed: every one of the bass part's
  708 words given an 11-character placeholder still fitted in 16 pages. The
  gloss row lives in space the bar-number row already reserves.
- **The gloss row is one more than the measure already uses, and it must be
  computed once per measure.** The first version recomputed it per word, so
  its own gloss counted: the second word in a measure fell to row 3, the
  third to row 4, and Basso I reached **row 11**. MuseScore then reserves
  space for eleven lyric rows and the part went 16 → 21 pages. This is the
  same trap as the documented "stray verse 6" one, self-inflicted.

## The glossary: one translation per word form

`SANASTO` is 280 entries of word form → Finnish, seeded from
`requiem.html`, whose translation is deliberately word-for-word and follows
the Latin word order — so it is the right source, but the alignment is not
automatic (*ad te omnis caro veniet* → "sinun tykösi tulee kaikki liha"
reorders), and every entry was checked against its own line, which is quoted
in the comment above it.

One translation per form was the singer's choice when asked. Function words
therefore compromise: `in` is always "-ssa" even where "in favilla" is
"tuhkaan". The alternative — per-bar exceptions — was offered and declined,
and the table stays one readable list.

The **whole work** is covered, soloists included, though no reading part
sings their text: the singer's call was "if it comes semi-free, put it in so
it shows in the MusicXML". Without it, half the full score would be
half-glossed and the report would fill with warnings nobody would act on.
Vocabulary: 195 distinct forms in the eight chorus parts, 206 more in the
soloists' text.

## Reading the words is harder than it looks, and getting it wrong is worse than not doing it

A gloss goes under a *word*, so words have to be assembled from syllables —
and `syllabic` lies in places. The rule went through three versions, each
killed by a measurement:

1. **Assemble from `syllabic`.** Correct in principle, and it works for most
   of the work. But Lacrymosa's bars 681–694 have "re" and "qui" marked
   `single` and the following "em," `middle`, so the reader saw three words
   where there is one — and because `qui` is real Latin, **the part printed
   "joka" in the middle of the word requiem**. A wrong gloss is worse than a
   missing one.
2. **Ignore `syllabic`, take the longest glossary match.** Fixed Lacrymosa
   and died in a unit test: OMR's "per-petl-la" begins with `per`, which is
   in the glossary ("kautta"), so a garbled word would have produced a
   confident wrong gloss in exactly the same way.
3. **Treat the marks as evidence, not truth**, which is what shipped:
   - if the marks give a complete word and it is in the glossary, that is the
     word — so `dies`+`irae` stay two words;
   - otherwise look for a **longer** glossary match, so "re"(1) becomes
     `requiem`(3) but "per-petl-la"(3) can never shrink to `per`(1);
   - otherwise let the word **split**, but only if *every* one of its
     syllables is covered by a glossary word — "Do-na-e-is" becomes
     `dona`+`eis`, while "per-petl-la" does not split because "petl" is not a
     word;
   - otherwise keep what the marks say, unrecognised, and report it.

`RIKKI` lists the 77 forms that even this cannot assemble — OMR garble
("perpetlla", "lg}"), a dynamic marking read as a syllable, and the CPDL
editor's name printed as a lyric in the chorus tenor (movement I bar 68).
Two tests keep the list honest: no word in the score may be unknown to both
`SANASTO` and `RIKKI`, and no `RIKKI` entry may be unused. The second one
fired four times during this work, each time because a fix had made an entry
obsolete.

## The check the singer asked for: read the whole text as prose

    python3 suomennos.py --teksti stemma-basso-1.mxl

prints the part's text as running sentences, the gloss under the Latin and
the hyphens exactly as they print, with unknown words in guillemets:

    t. 688  re-qui-em, re-qui-em, do-na e-is   re-qui-em. A-men.
            lepo       lepo       anna  heille lepo       amen

This is the check that cannot be done from the notation. The singer asked for
it twice — once for the Finnish ("read it back printed, as Finnish text on
its own, so there are no more silly mistakes") and once for the Latin ("to
find those hyphenation errors") — and both were right to ask: **it found
every defect below.** Coverage is 100 % in both bass parts and 95–96 % in
S/A/T, where the whole remainder is movement I's OMR garble.

## Four defects that were in the printed parts

The gloss did not cause any of these; it made them visible.

| Defect | Where | Fix |
|---|---|---|
| `syllabic` marks scrambled, so "requiem" printed as `re qui em,` without hyphens and "dona eis" as `Do-na-e-is` | Lacrymosa 681–698, chorus bass | new `korjaa_kasin.py` operation `tavutus` |
| `cal-la-mi-ta-tis` for `ca-la-mi-ta-tis` | Libera me bar 85, chorus bass | one `aseta` row |
| `in no-mi-ni` for `in no-mi-ne` | Sanctus bar 71, Kuoro B II | one `aseta` row |
| a syllable on lyric row **6**, rows 3–5 empty but reserved | Dies irae 5/9/15/19 and Libera me 49/53/59/63, chorus S/A/T | new general rule in `yhdista.py` |

**The Lacrymosa one has a cause worth remembering.** When that movement's
words were rewritten on 2026-09-03, each `aseta` row replaced the syllable's
*text* and kept the `syllabic` of the word it replaced: "La-cry-mo-sa"'s
`middle` stayed on "do-na"'s second syllable. The syllables and their
positions were right — page-verified at note resolution — and the chain marks
were wrong, which is a thing that verification pass could not see. It had
been printing that way for six days.

The new operation takes the whole sentence's hyphenation in one row:

    ("58", None, "tavutus",
     "Do-na e-is re-qui-em, do-na e-is, pi-e Je-su Do-mi-ne, "
     "do-na e-is re-qui-em, re-qui-em, re-qui-em, "
     "do-na e-is re-qui-em. A-men."),

It asserts every syllable's text and changes only the marks — 29 of 40
syllables were wrong. One readable row beats 29 edited ones, and it must come
**after** the `aseta` rows that set the texts, since it asserts the final
state. Its guard earned its keep twice while being written: once on a
melisma's extend-only `<lyric>` (not a syllable, must be skipped), once when
the row was accidentally placed in the preceding `Osa`.

**Row compaction is the fourth fix and it is a tool rule, not a table.**
`normalise_lyrics` now renumbers a measure's lyric rows to 1..n preserving
order. The source (Sibelius + Dolet) writes the upper voice's syllable as
`part1verse6`, and rows 3–5 then take space while empty. That had cost three
parts a page since long before this work, and it would have pushed the gloss
to row 7.

## Verification

- Compared per note as (pitch, duration, voice, type, lyrics) keyed by
  (part, measure index, note index): **62 075 notes before and after, and
  not one pitch, duration or note type changed.** The differences are 4 533
  glosses added, 176 corrected `syllabic`/row values, and exactly the two
  intended syllable texts.
- 247 tests (205 before, +42).
- Merged score and all eight parts convert without `-f`. Page counts
  18/17/16/16/17/17/16/16; `stemmat-sisallys.txt` regenerated, and the
  practice `.mscz` rebuilt.
- Read back off the rendered PDFs as images: `stemma-basso-1.pdf` page 8 now
  prints `Do-na e-is re-qui-em,` with its hyphens and `anna heille lepo`
  under it, and `stemma-sopraano-1.pdf` page 1 shows the gloss row with no
  wasted lyric rows above it.
- The site's parts page gained an **Ominaisuudet** list the singer asked for,
  with every number derived rather than written: page counts from
  `stemmat-sisallys.txt`, the Dies irae range from `DIES_IRAE_ALUT` plus the
  last sub-movement's own measure count (1–701, which independently matches
  the pin in `test_yhdista.py`), the font size from `suomennos.KOKO`.

## What is left here

- Movement I's chorus S/A/T still carry the OMR garble the text dump now
  names exactly (`lg},`, `ux`, `per-pe-tll-a`, `In-ce-at`, `Ky n-e`, and the
  editor's name `Reutenauer` at bar 68). Each is one `korjaa_kasin.py` row
  once someone reads the source page; the list is `python3 suomennos.py`'s
  own output.
- The same `tavutus` treatment probably applies to movements 01 and 14's
  S/A/T, whose chains were never audited.
- The glossary's compromises are one line each to change if the singer wants
  a different reading; `in`, `per`, `de`, `te` and `ex` are the ones that
  lose the most.
