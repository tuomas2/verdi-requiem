*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-03 (c): Lacrymosa's three-bar shift, and its chorus bass verified whole

The singer reported that Lacrymosa's bar numbers were all wrong: the book has
the chorus bass entering at **645** and the "men" of "A-men" at **698**, but
the reading part had them at 642 and 695. They also said the section "has been
problematic before, has had various fixes, and is still a mess" — which was
fair, and the reason was one wrong number, not the fixes.

## Root cause: a heading number used as a file's first-bar number

`DIES_IRAE_ALUT` holds, per sub-movement, **the number the source file's first
bar gets**. Lacrymosa's entry was 621, which is where the *book prints the
Lacrymosa heading*. The CPDL Lacrymosa file starts three bars later: the book's
621–623 are the last three bars of the 10b file. So every bar of the movement
came out three too low. The right value is **624**.

For ten of the eleven sub-movements the heading and the file's first bar are the
same bar, which is exactly why the distinction was invisible — and the
2026-09-02 section that introduced the table said "the first bar number per
sub-movement", wording that reads correct either way.

## The evidence, three independent strands

1. **Both source PDFs print their own bar numbers, and they are continuous.**
   `mutool draw -F stext` pulls them straight out of the text layer: 10b prints
   577, 581, 585 … 617 at its system starts, Lacrymosa prints 629, 634, 638 …
   697. Counting the bars in the first and last systems from the rendered page
   (5 bars in Lacrymosa page 1's first system, 5 on page 16) closes both ends:
   **10b is 573–623, Lacrymosa 624–701**, no overlap and no gap.
2. **The singer's two numbers only work with 624.** File-local bar 22 is the
   bass entry and local 75 carries "men."; 624 + 21 = 645 and 624 + 74 = 698.
   With 621 they were 642 and 695, exactly what the part showed.
3. **The 10b→Lacrymosa seam becomes continuous** (623 → 624), so one of the
   five overlaps `saumaraportti` complains about disappears — with a mechanism,
   not by fiat.

## The same trap probably affects four more seams

`saumaraportti` still reports four overlapping seams (II·2 by 1, II·4 by 3,
II·6 by 2, II·9b by 5) and three gaps. The 2026-09-02 section concluded these
are genuine structural differences, having checked that the overlapping bars
are not duplicated music. **That check does not distinguish the two
explanations.** If the next file starts *after* the book's heading — Lacrymosa's
case — the overlap is an artefact of the table, the music is continuous, and
nothing is duplicated. The comparison would look exactly the same either way.

This cannot be settled from here: there is no source PDF for those movements
and the choir's MuseScore files are condensed cuts with their own numbering. It
needs **one bar number from inside each sub-movement** — "which bar does the
chorus bass enter in Rex tremendae" — never the heading, which is the number
that misled us. Recorded as an open item and as a question in
`YHDISTAMINEN.md`.

## The chorus bass, checked from the first bar to the last

The singer asked for the whole section to be checked against the MuseScore
files. Two passes, and they answer different questions:

**Notes, against `musescore/04_dies_irae_2`.** The bar mapping had to be
established first, and the naive alignment lies: `difflib` on per-bar pitch
signatures matched Lacrymosa's bars 1–21 to the choir file's 28–48 because both
sides are *all rests* there, and empty bars all look alike. Aligning the piano
and the soloists instead gives two clean offsets, +27 then +21, and the arithmetic
then closes exactly: the choir file is 10b's bars 1–48 followed by Lacrymosa's
22–47 and 54–75, i.e. 48 + 26 + 22 = 96 bars, with 10b's last 3, Lacrymosa's
chorus-silent 1–21 and 48–53, and its 3-bar postlude trimmed — 30 bars, and
78 − 30 = 48. Over the 48 compared bars, folding chord members and comparing
`P8`+`P9` against `Bass 1`+`Bass 2` as a pair, **two differences**:

| Bar | Ours | Choir file | Settled by the page |
|---|---|---|---|
| 653 | `G3` quarter | `C3` | ~~**ours** — and the printed natural proves it~~ — **wrong, reversed 2026-09-04**: the page really does print G♮, but the page is the only thing that says so. See *2026-09-04* |
| 689 | `F3` half | `F3` quarter | **ours** — page 14 prints a half note |

So one note was already right and the choir file differs; the other was the
choir file being right and the printed page wrong.

**Lyrics, against `Verdi_Lacymosa.pdf`, at note resolution.** This is the pass
that closes the "melisma-internal placements are best-guess" item, and it needed
a method rather than more squinting.

- **The PDF's lyrics are real text**, and `mutool`'s own `<line>` elements are
  already roughly syllable-sized, so syllables come out with an x coordinate
  each. Do **not** rebuild syllables from individual chars by gap width — that
  is the "measure from the previous glyph's right edge" trap from the movement
  14 work, and a first attempt using char origins split every word into letters.
- **Match a PDF lyric row to a part by its vertical order, not by its text.**
  All eight voices sing the same words in many places — page 16 is eight rows of
  "A - men." — so content cannot identify a row. The staff order is fixed
  (soloists S/Mz/T/B, then chorus S/A/T/B), so order identifies the row and
  content then *verifies* it.
- **The other voices' rows are a ruler.** Pair each ruler row's syllables in
  order with that part's own syllables, giving pairs of (note `default-x`, PDF
  x). Fit one slope per page from those pairs *centred within each bar* — the
  file's own system breaks are not the PDF's, so pairs cannot be pooled across a
  system — then predict where each chorus-bass syllable should print.
- **The decisive test is nearest-note, not residual size.** Residuals run up to
  9 pt because a syllable's x is its text's left edge and syllable widths vary,
  while notes sit 12–50 pt apart. Asking "which note's prediction is this
  syllable closest to" is scale-free. **Every syllable in the movement lands on
  the note it is written on**, with one apparent exception (bar 685's "na"),
  which the rendered page then showed printed exactly as the file has it: under
  the first of a beamed pair with the extension line over the second.

**One real defect, and it had been misdiagnosed.** The divisi upper voice `P9`
at bars 677–679 carried the leftover "La-cry-mo-sa di-es il-" text. The earlier
note said fixing it needed "a proper syllable placement, not a blind copy",
because `P9`'s 5+4+1 notes do not map onto `P8`'s "Pi-e Je-su". But `P9` does
not sing `P8`'s words: page 11 prints a **separate lyric row for it above the
staff**, reading "Pi-e Je-su Do-mi-ne," — and those seven syllables land, by the
x-coordinate test, on precisely the seven notes that carried the wrong text.
A 1:1 substitution after all. The row was easy to miss because a lyric row
above a staff reads as belonging to the staff above it; that is also how it
first got attributed to the chorus tenor.

## And then: bars 657–665, where the printed edition itself is wrong

While the above was being written the singer read the corrected part and
reported one more thing: from bar 657 the chorus bass should sing **"hu-ic
er-go par-ce De-us" three times** (657–658, then twice more ending at 665),
not "La-cry-mo-sa … di-es il-la". They were right, and this one matters more
than its size, because **the source PDF prints the wrong text too**. Page 7
shows "La-cry - mo-sa," under the chorus bass in plain type. So the
page-by-page verification above passed these bars while they were wrong.

**What settles it is internal consistency, not the page.** The passage is an
imitative stretto: one motif — quarter, two slurred eighths, two eighths —
entering successively, with the edition's own cue labels *IInd Bass*, *Ist
Bass*, *IInd Tenor*, *Ist Tenor* marking the entries. The bass's bar 658
(`F3 Bes3 C4 Des4 Bes3`) is note for note the chorus tenor's bar 657
(`F4 Bes4 C5 Des5 Bes4`) two octaves down; bar 657 is the same motif from
`C3`. The same motif appears in the alto at 658 and the soprano at 659. **In
tenor, alto and soprano it carries "hu-ic er-go".** One motif in one stretto
carries one text, so the bass's does too. Two further checks agree: S/A/T sing
"huic ergo parce Deus" throughout 656–668, and the bass's *own* continuation at
664–665 already read "er-go par-ce De-us," — after the fix all four voices are
finally on the same words.

This is the same error class as the movement's already-documented bug (its own
earlier "Lacrymosa dies illa" text sitting on later bars), reaching further back
and, unlike the earlier instance, present in the print as well. 18 more `aseta`
rows; the syllable *positions* are unchanged and page-verified, only the words
move. The table also gained a `jatka` operation, which adds a lyric's
`<extend/>`, so the two new melismas print their continuation line the way the
tenor's equivalent does in the source.

## The lesson: verifying against the print cannot catch an editorial error

The x-coordinate method above is a strong check and it is now the standard for
this project, but it answers exactly one question: *does our file say what the
printed source says?* Where the engraver himself put the wrong words under the
notes, it will confirm the error with full confidence — which is precisely what
happened here, on the same bars, in the same session.

What caught it was a singer reading along, and what *confirmed* it was a check
of a different kind: **the same figure, in the same passage, must carry the same
text in every voice.** That check needs no external source at all. It is worth
running deliberately whenever a part's text looks odd, and it is cheap enough to
automate — find repeated pitch/rhythm figures across the four chorus staves
within a bar window and flag those whose syllables disagree. Not built yet, and
the obvious first place to point it is movement 11's Soprano/Alto/Tenor, which
nobody has audited.

## Movement 11's hand layer moved into `korjaa_kasin.py`

`11-Verdi_Lacrymosa.mxl` is again CPDL's untouched export, and `yhdista.py`
reads a generated `11-Verdi_Lacrymosa-kasin.mxl`. The table is 50 rows: 43
reproducing the earlier hand edits to `P8` (41 `aseta`, 2 `lisaa` — all
lyric-only; the notes were never touched), 18 more for the 657–665 stretto and
7 for `P9`. Every row
asserts the old syllable, so a stale row stops the run.

Two details worth keeping: the raw source had to be restored from the **first**
commit that added it, past two later hand-edit commits, one of which was a
single `syllabic` change (`begin` → `single`, to stop a runaway hyphen) that a
one-commit-back restore would have silently dropped. And the acceptance test is
the migration's whole point: regenerating reproduced the previously hand-edited
file exactly, with the 7 intended `P9` edits as the only difference.

## Verification

- Note counts per staff and the 1807-bar total identical before and after —
  both changes are numbering and lyrics only.
- Dies irae now spans 1–701; `saumaraportti` prints 7 lines, not 8.
- Merged score and all eight parts convert without `-f`; page counts unchanged,
  `stemmat-sisallys.txt` unchanged.
- 85 tests (73 before, +12), including a test pinning *why* Lacrymosa's 624
  differs from the book's 621 — 621 looks right and has been wrong once — and
  one pinning the three "huic ergo parce Deus" statements against the printed
  edition's own wrong text.
- Read back off the rendered `stemma-basso-1.pdf`: page 7 shows II·9b closing on
  a `[613–623]` rest, the II·10 heading at 624, a `[624–644]` rest and the bass
  entering at **645**; page 8 shows the divisi's two lyric rows at 677–679 and
  "A men." at **697–698**.
