*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-02: bar numbers on every bar, and movement I's chorus-bass lyrics

The choir's first rehearsals happened, and the user came back with one feature
request and three lyric complaints, all in movement I and all heard by ear
while singing.

## Bar numbers on every bar

`tiivistys.mss` — the style used for the eight reading parts, and through
`harjoitus.py` for the practice `.mscz` too — now also sets

    <showMeasureNumber>1</showMeasureNumber>
    <showMeasureNumberOne>1</showMeasureNumberOne>
    <measureNumberSystem>0</measureNumberSystem>
    <measureNumberInterval>1</measureNumberInterval>
    <mmRestShowMeasureNumberRange>1</mmRestShowMeasureNumberRange>

`measureNumberSystem` is the switch that matters: 1 means "only at the start of
a system", which was the default and the thing the user was fighting. With it
off, `measureNumberInterval` 1 numbers every bar. `mmRestShowMeasureNumberRange`
prints the span under a compressed rest (`[79–93]`), which is redundant with the
per-bar numbers but free and reassuring.

Cost: **exactly one page per part** (B I 13 → 14, and +1 for each of the other
seven; the 2026-09-03 spacing change added more on top). It is not the range line and it is not the font size — rendering with
`mmRestShowMeasureNumberRange` off, and again with `measureNumberFontSize` 6,
both still gave 14 pages. It is the vertical space the number row itself takes
above each system.

## The three lyric complaints

The user reported these by bar number "from the bass part", which is worth
noting: they had to count from each system's start to do it, which is precisely
why they asked for the numbers. Two of the three were dead-on, which is a good
reason to trust their bar numbers when they give them.

**Bar 108, "e-le-i-son" printed on two lyric lines — a real `yhdista.py` bug.**
The user guessed the cause exactly ("maybe you can see the confusion in the
xml"). Audiveris had put the syllables of one word on lyric verses 2, 1 and 2.
`normalise_lyrics` was supposed to catch that, but its rule was *per measure*
and only fired when the measure had **no** verse-1 syllable at all — so a
measure that mixed them kept the split, and the part printed `le … son,` on one
row and `i` alone on the row below.

The fix is a better rule, and finding the right one needed measurement, not
taste. Collapsing every verse to 1 part-wide would have been wrong: `Kuoro B`
also carries genuine second lyric lines at bars 367–369 (Rex tremendae) and
677–679 (the Lacrymosa divisi), where **two voices share the staff and sing
different words**. The discriminator that separates the two cases cleanly is
the `<voice>` element:

| Case | Voices with lyrics | A note with 2 lyrics | Verdict |
|---|---|---|---|
| I m108 `le`/`i`/`son,` | 1 | no | one text line → all to verse 1 |
| I m78 `is.` + junk `S` | 1 | **yes** | two rows are needed → leave |
| Rex m367–369, Lacr. m677–679 | **2** | no | divisi, two real texts → leave |

So: *if all of a measure's lyrics belong to one voice and no note carries two
of them, they are one text line and all belong on row 1; otherwise fall back to
the old "lift to row 1 only if row 1 is empty" rule.* `test_yhdista.py` (new,
9 tests) pins all three rows of that table.

Effect beyond the reported bug: it also lifted 3 syllables in `Kuoro S`, 3 in
`Kuoro A` (including the stray verse-**8** one) and 7 in `Kuoro T` onto row 1.
Every one was checked and every one is a real syllable (`qui`, `in`, `bi`,
`lu`, `rae,`, `di`, `es`), not OMR junk.

**Bars 126 and 129, two missing `i` syllables — confirmed against the PDF.**
The user said "son" belongs on the first note of bar 127 and the next
`e-le-i-son` must spread over four notes ending on the single note of bar 130.
Page 9 (system 2, bars 126–128) and page 10 (system 1, bars 129–135) of
`01-Verdi_Requiem.pdf` show exactly that, syllable over notehead: 126 = `le`,
`i`; 127 = `son,`, `e`; 128 = `le`; 129 = `i`; 130 = `son,`. Our file had `i`
one note late in both phrases and no `son,` in the first. Fixed.

**Bar 51, "om-nis" — done as asked, but the source PDF disagrees.** The user
wants `nis` on the last note of bar 52, i.e. the melisma sung on `om`.
`01-Verdi_Requiem.pdf` page 3 prints it the other way: `om` on bar 51 beat 1,
`nis` on beat 3, and the extension line running through bar 52 to `ca` — the
melisma on the `i` of `nis`. Both are sung; which one a choir uses is the
conductor's call, and the user is the one in the room. Applied their version;
`om` stays `syllabic="begin"` so MuseScore draws `om – – – nis` across the
melisma by itself, no `<extend/>` needed. **One line to revert** if the
rehearsal score says otherwise: move the `<lyric>` back from bar 52's fourth
note to bar 51's second.

## Also fixed, not reported: the stray `S` at bar 78

`Kuoro B` bar 78 carried OMR junk — a lone `S` on verse 2, sitting under the
real `is.` on the same note. It is visible in the old `stemma-basso-1.pdf` page
1. Page 4 of the source PDF has nothing there. Deleted. (This is the one case
where the new `normalise_lyrics` rule deliberately does *not* help: two lyrics
on one note need two rows, so the rule leaves them alone and the junk had to go
from the data.)

## Where the fixes live

All four data fixes are in `01-Verdi_Requiem-kasin.mxl`, part `P16`, edited
directly — that file is the hand-corrected copy `yhdista.py` reads and
`korjaa_sanat.py` never writes (it writes `-OMR-korjattu.mxl`), so this is the
safe layer. All 31 remaining verse-2 syllables in `P16` were set to verse 1 at
the same time: the chorus bass has a single text line everywhere in this
movement's PDF, and `normalise_lyrics` was already promoting all but two of
them anyway, so the output change is only the two that mattered.

## Verification

- Per-staff note counts unchanged across the board (`Kuoro B` 1801 before and
  after) — only lyrics moved. Measure count still 1807.
- The merged score and all eight parts convert without `-f`; full score 362
  pages.
- 41 tests pass (32 before, +9 new).
- Read back off the rendered `stemma-basso-1.pdf`, not just from the data:
  page 1 shows `om – – nis` and no stray `S`, page 2 shows `e-le-i-son` on one
  row at 107–108 and the corrected syllables at 125–130.
- All eight parts, `stemmat-sisallys.txt` and `harjoitus-basso-1.mscz`
  regenerated.
