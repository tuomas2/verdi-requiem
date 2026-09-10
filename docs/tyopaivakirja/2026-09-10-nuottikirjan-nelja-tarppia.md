*Part of the Verdi Requiem working notes — the index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-10 (c): four questions taken to the rehearsal book

The previous session ended with a list of things that could only be settled by
looking at the physical Edition Peters, written as **named questions** rather
than "what does it say here" — four of them in the user's own line, one glance
each. The user answered all four. Two were defects, two were confirmations,
and one of the confirmations closes an assumption that had been open since the
merge was built.

The book has arbitrated before — *2026-09-02 (later)* read the Dies irae
sub-movements' start numbers out of it — but never a pitch. That is what makes
bar 607 worth its own section: it is the first note in the score whose spelling
neither source PDF nor harmony could settle, and the book settled it in one
look.

## The two defects

### II·9b bar 607: the choir file was right, and it is a G♭

Local bar 35, `Kuoro B`. Our file read `G3 G3` under "di-es"; the choir's own
MuseScore file sings `G♭3 G♭3`. The key is two flats (B♭, E♭), so a G♭ is a
**printed** accidental, not one the key signature supplies — and this
movement's source PDF uses a subset font with private-use codepoints, so the
glyph method that settles this kind of question elsewhere (see *2026-09-10*,
*Reading a single notehead off the page*) cannot read its accidentals at all
without a one-off identification pass. That is exactly why this note went on
the list for the book.

The book prints the flat. Two rows in `OSA_II9B`:

    ("35", 0, "korkeus", "G3", "Ges3"),
    ("35", 1, "korkeus", "G3", "Ges3"),

`aseta_korkeus` drops the OMR's `<accidental>` and `<stem>` and lets MuseScore
decide the printed sign from `alter` plus the key, which comes out right: the
part now prints a flat on the first note and nothing on the second, since the
bar already carries it.

**This makes II·9b's chorus bass the third voice in the score to reach ✔**,
after Lacrymosa's and Agnus Dei's.
Its syllables were already checked against the source PDF note by note; its
notes are now compared against the choir file across all 51 bars, and this was
the only difference. Re-run after the fix, the two files disagree nowhere: the
apparent differences at bars 32–33 are our staff's chord (`E♭3` under the
choir's `B♭3`, one note folded into the other), and the run at bars 49–51 is
the choir file continuing into Lacrymosa, which our movement does not.

### Movement I bars 51–52: "om-nis" goes back the way the page prints it

On 2026-09-02 the user asked for the melisma on "om", which moved "nis" to the
last note of bar 52. The source PDF printed it the other way, and that
session's entry recorded the disagreement and said which single line to revert
if the book ever settled it. The book settles it: **"nis" is on bar 51's second
note, with an extension line running to the last note of bar 52.**

So the two transfer rows are gone — the source file marks the syllable
correctly by itself — and what is left is the extension line, which the source
did not draw:

    ("51", 1, "jatka"),

The part now prints `ad te om – nis________ ca-ro`, the line ending under bar
52's `C♯`. This is what the earlier entry promised would be one line of work,
and it was.

## The two confirmations

**Movement I bar 35, "vo-tum": the natural is there.** Our reading is `B3 B3`
(B natural), the choir file sings `B♭`. The printed source page draws a
natural, measured from the music font on 2026-09-10, and the book draws one
too. Three sources now, no change needed. This was on the list precisely
because it was cheap: a confirmation, not an open question.

**Sanctus: the user is Bass I.** Bass I enters at bar 2, Bass II at bar 4, and
the user enters at bar 2. `SINGER_PARTS` maps `Basso I` to the Sanctus's
`Kuoro B` (part `P4`, which does enter at bar 2) and `Basso II` to `Kuoro B II`
(`P8`, bar 4). The mapping is right, which means the reader has been on the
correct staff in the double-chorus movement all along. This was one of the five
assumptions listed in [`docs/menetelmat/yhdistaminen.md`](../menetelmat/yhdistaminen.md)
as made without the book, and the consequence of getting it wrong would have
been the worst of any of them — a whole movement read off the wrong line — so
it is worth being explicit that it is now checked rather than assumed.

## What the fix at 607 says about the four notes it did not touch

Four of the six candidate differences in II·9b were a G against a G♭, which is
why the previous session called the pattern systematic-looking rather than
random. One of the four is now decided, in the choir file's favour. The other
three are in voices the user does not read, and they were not asked about — but
the piano staff on the same beat now takes them a long way, which is the
sharper of the two cross-checks this project uses (*2026-09-04*, *Lacrymosa
653*):

- **Bar 605 (local 33), soprano.** Ours `G5`, choir file `G♭5`. The piano's
  chord on that beat is `G♭5 B♭5 E♭6 G6` — E♭ minor, except for that last
  note, which is a G natural inside a chord whose own third is G♭. One of the
  two spellings in that chord is OMR damage, and the three-note E♭ minor
  reading is the majority. The soprano doubles the piano's top note.
- **Bar 612 (local 40), alto.** Ours `G4 G♭4`, choir file `G♭4 G♭4`. Bass `A3`,
  tenor `E♭5`, soprano `C5`, piano `E♭4 G♭4 D♭5` — an A diminished seventh
  (A, C, E♭, G♭), of which the alto's G♭ is the missing member and a G natural
  is not a member at all.
- **Bar 608 (local 36), tenor**, `B♭3` against the choir file's `A3`, and
  **bar 599 (local 27), soprano**, `C5` against `D5`, are not part of the G/G♭
  pattern and have no such argument behind them.

None of this is applied. The piano in this movement comes out of the same OMR
pass as the voices, so it is not an independent source in the way the choir
file is; what it does supply is the internal-inconsistency argument (a chord
cannot hold both G♭ and G), and that is an argument, not a measurement. All
four stay on the list, and they all still sit on the same spread of the book.

## Verification

- **367 tests** (366 before). The pin that said `nis` is on bar 52's fourth
  note now says bar 51's second, and asserts the `<extend>` and that bar 52
  carries no syllable at all; the II·9b whole-file test pins both `G♭`s and the
  matching assertion that the source file still reads plain `G`.
- **Per-staff note counts from `MAPPING` against the merged score**: chorus
  1842 / 1810 / 1908 / 1813, piano 22312 — identical to 2026-09-10, so nothing
  moved. Neither fix adds or removes a note.
- The full score converts without `-f`, **390** pages, unchanged.
- Both bass parts rebuilt, page headers and date stamp re-run, PDFs rendered
  and **looked at** at 450 dpi cropped to the staff: bar 607 prints the flat
  and the `p`, and bars 51–52 print the extension line to the end of the bar.
- `python3 suomennos.py --teksti stemma-basso-1.mxl` read through; the movement
  I text is still clean prose.
- The seven `-kasin.mxl` files this session does not touch were regenerated and
  came back **byte-identical as extracted XML**, so the three new rows touch
  nothing else. (They are restored from git rather than committed, since the
  zip metadata differs even when the content does not.)
- `stemmat-sisallys.txt` unchanged: page counts still 18/17/16/16/17/17/16/16.

## The lesson

The value here is not in the two fixes. It is that a question shaped as *"is
there a flat in front of these two notes?"* costs the singer one glance and
comes back unambiguous, while *"check bar 607"* costs a rehearsal break and
comes back as a maybe. Four questions, four answers, same evening. The list
in `TODO.md` is worth keeping in that shape, and it is worth keeping short:
the four that were answered were the four that named exactly what to look at.
