*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-10: the choir files come back, and movement I's chorus notes get a second source

The user put the choir's 77 `.mscz` files back on the machine, under
`.local/musescore/`, and asked for every fix that the available evidence
supports. That unblocked the item this file has been carrying since
2026-09-07 — *movement I's soprano and alto read bars 28–34 in the wrong
key, found by measurement, not fixed* — and three more besides.

Eleven pitches changed, fourteen syllables were rewritten, five junk
syllables removed and one added. Every one of them is backed by **two
independent sources**, and the two disagree often enough that the session's
real result is the method for deciding between them.

## The files, and where they live now

The batch arrived flat in `.local/musescore/` and was sorted into the eight
folders the notes already name (`01_requiem` … `08_libera_me_2`) by the number
in each filename; the counts came out 10 + 11 + 11 + 11 + 11 + 7 + 10 + 6 = 77,
which is the same 77 as 2026-08-30. `.local/` is already in
`.git/info/exclude`, so nothing of it can reach the public history — the
reason it is kept out is in [`hakemistot.md`](../hakemistot.md).

Four whole scores were converted for this session:
`mscore -f -o x.musicxml "…/Verdi Requiem N …mscz"` for `01_requiem`,
`03_rex_tremendae`, `04_dies_irae_2` and `06_agnus_dei`. All four exited 0
with `-f`.

## The comparison, and the three things it has to get right

A throwaway script extracts one staff as a token per note and runs
`difflib.SequenceMatcher`. Three details decide whether its output is
information or noise, and each of them produced a false alarm before it was
handled:

- **Enharmonic spelling.** Our sources write `Aes3` where the choir file
  writes `Gis3`. Comparing spellings reports a difference; comparing
  semitones does not. Movement I's tenor alone had two of these (t.61
  `Aes3`/`Gis3` and t.72 `Bes3`/`Ais3`), and they vanished the moment the
  comparison normalised to a MIDI number.
- **Divisi.** Where a staff carries two voices, the second voice looks like
  extra notes. Movement 07's soprano and alto each showed four "extra" notes
  and the bass six, all of them voice 2 or chord members. Filtering to voice 1
  and folding chord tones into the preceding token removed all of them.
  Movement 07's chorus tenor carries **three** voices (the choir file has
  Tenor 1–3), so there the comparison is against the top note only.
- **Octave.** Our chorus tenor is written an octave above the choir file's.
  Without a shift the tenor comparison scores 0.109 and is worthless; with it,
  0.934.

And one rule that was already written down and is worth restating because it
decided what could *not* be concluded: **never quote a bar number that came
out of an alignment against these files.** They are a condensed chorus-only
cut. In movement I the bars line up exactly up to 78 and then stop lining up
somewhere in the Kyrie — our bar 95 sits against their 97 — so every
"difference" the aligner reported from bar 79 onward was noise, and the Kyrie
is still unverified.

## Reading single notes off the printed page, without rendering it

Where our file and the choir file disagreed, the arbiter was the source PDF.
The method is the one from *2026-09-07 (b)* — the music is text, so
`mutool draw -F stext` gives every notehead an exact coordinate — but it had
only ever been used for key signatures, where counting identical glyphs is
enough. For a single notehead the y has to be turned into a pitch, and that
needs a calibration. It is two constants, both measured:

- A **treble clef `&` sits with its baseline on B4** and a **bass clef `%` on
  D3**. Nothing was assumed: on page 2 the three sharps of the key signature
  land at exactly F5, C5 and G5 above every treble clef when read this way,
  which is where a three-sharp signature is drawn.
- One diatonic step is **1.5625 pt** (= the 12.6 pt font's staff space / 2).

With those, `y → pitch` is arithmetic, and the bar a glyph stands in comes
from the OMR's own `<measure width>` values scaled by 0.306, exactly as
before. The check that the whole apparatus works: the chorus bass's bar 52
came out `Bb2 C3 C3 C#3` from the page, which is what our file says, and bars
50–58 reproduced the diary's own earlier x values (55 at 331, 56 at 367,
57 at 407, 58 at 468) to the point.

## What changed

### Movement I: the key signature and the seven notes it damaged

The 2026-09-07 measurement said the change to F major belongs to bar 28, and
that the file has it there in the chorus tenor and bass and at bar **35** in
the other fifteen parts. Both halves are now fixed:

- The signature moved, in all fifteen parts, by a second `Savellaji` row. The
  operation grew a `valmiit` field for the two parts that already had it in
  the right bar — it does not skip them silently, it asserts that they carry
  the change at bar 28 and none at bar 35, so the list cannot rot.
- The pitches Audiveris wrote under the wrong key were corrected: soprano
  t.28 `F#4 F#4` and t.34 `C#5`, alto t.32 `F#4 G#4` and t.33 `G#4 F#4`.
  Seven notes, and the choir file's soprano and alto agree with our file on
  **every other note in the movement up to bar 78** — those seven were the
  entire difference. The rest of bars 28–34 (`D5 E5`, `A4`, `E4 A4`) needed
  nothing, which is itself a check: D, E and A are the three notes a
  three-sharp key does not touch.

### Movement I: two more notes, and eight the page defends

The choir file reported fourteen differences in bars 1–78. Four of them are
the key damage above — seven notes in four bars — and the other ten were
adjudicated one at a time against the page:

| Voice | Bar | Ours | Choir | Page says | Verdict |
|---|---|---|---|---|---|
| S | 47 | C5 C5 C5 | C5 B4 C5 | three C5 | ours |
| S | 50 | Bb4 Bb4 | C5 Bb4 | two B (flat by key) | ours |
| S | 76 | **Cb5** | C5 | natural, then C5 | **fixed → C5** |
| S | 77 | E5 | B4 | E5 | ours |
| A | 77 | G#5 | G#4 | G5 | ours, but see below |
| T | 22 | A4 ×3 | A#3 ×3 | three A, no accidental | ours |
| T | 33 | Bb4 | B3 | B, no accidental, key has one flat | ours |
| T | 43 | **C5** | C#5 | sharp, then C5 | **fixed → C#5** |
| B | 35 | B3 | Bb3 | natural, then B | ours |
| B | 52 | Bb2 C3 C3 C#3 | Bb2 B2 C3 C#3 | Bb2 C3 C3 C#3 | ours |

Two real defects, both of them an accidental the OMR misread: a natural read
as a flat, and a sharp dropped. The other eight are the choir file's own
readings, and the page is unambiguous about each.

**Alto bar 77 is left open on purpose.** The page prints G5 — measured, and
the height is that of the key signature's own G♯ — so our file matches what
the engraver drew. But the alto's line there is `C4 E4 A4 | G♯5 | A4`, a major
seventh up and a minor seventh back down, and it crosses a third above the
soprano's E5; the choir file's G♯4 is a semitone lower neighbour resolving
upward, which is what the phrase wants. This is exactly the Lacrymosa 653
situation — *a printed accidental is strong evidence about which note the
engraver drew and none at all about whether he drew the right one* — and it
is not the user's own line, so it waits for someone who can ask the
conductor.

### Movement I: fourteen syllables in the soprano, alto and tenor

The three upper voices had never been touched. `korjaa_sanat.py` had already
tried and reported where it gave up, and the gaps clustered in one place: the
line **"et lux per-pe-tu-a"**, which all four voices sing twice, in the same
bars, to the same figure. The chorus bass is already correct there, so each
correction could be read straight off the neighbouring staff — and the source
PDF's four chorus text rows for that system all read
`-pe-tu-a, et lux per-pe-tu-a lu-ce-at …`, so the printed page says the same
thing a third time.

| Voice | Bar | Was | Is |
|---|---|---|---|
| S | 21 | `lg},` `ux` | `et` `lux` |
| S | 22 | `tll` | `tu` |
| A | 21 | `eh,` `luX` `er` | `et` `lux` `per` |
| A | 22 | `pe.` | `pe` |
| T | 17, 18, 19 | `e` `ux` `er` | `et` `lux` `per` |
| T | 67, 70 | `e` `e` | `et` `pe` |
| T | 76 | `In-ce-at` | `lu-ce-at` |

Two more classes came with them. The **soprano's whole "Te decet hymnus"**
(bars 35–41) sat on lyric row 2 and its bar 59 `Re-qui-em,` had the middle
syllable alone on row 2 — the word split across two printed text lines, the
same defect as the bass's bar 108 in *2026-09-04*, but in the data. The
**alto** had syllables scattered over lyric rows 1, 2, 4, 5, 6 and 8, and the
**alto and tenor** each carried a dynamic mark (`PPP`, `ppp`) as a syllable on
top of a real one at bar 136.

Row 2 is raised per bar by `sanarivi`, which grew the ability to take a note
index — without it the mixed bars (row 1 and row 2 in the same bar) cannot be
touched at all, because the whole-bar form rightly refuses them. The alto and
tenor use `yksi_sanarivi`, which works once the dynamic is gone; the soprano
cannot, because two of its notes are in voice 2 and the guard against
overlapping lyrics fires.

One of the thirteen suggestions `korjaa_sanat.py` reports but does not apply
turned out to be right and two turned out to be **wrong**, which is the first
time that list has been adjudicated at all:

- Alto t.37 `at` → `et` — applied. The PDF's alto row reads `et ti-bi`.
- Alto t.39 `ti` → `vo` — rejected and pinned by a test. The alto's own row
  repeats `ti-bi red-de-tur`; it is the tenor that goes on to `vo-tum`.
- Soprano t.134 `Chri` → `e` — rejected. All four chorus rows on page 10 read
  `Chri--ste, Chri--ste` and then `e-le-i-son.`, so the second `Chri` is real.

### Movement 07 (Rex tremendae): two notes, and a clean bill for S and A

The item this became possible for was named at the end of *2026-09-09 (d)*.
The choir file's bars are offset by six from ours (they have six bars our file
does not, at the start), and after that everything lines up.

- **Chorus bass: one difference in 174 notes**, and it is real. Bar 343
  (local 22) is the middle of three identical ornaments — main note, semitone
  below, main note back — and the file reads `Ces4 Aes3 Ces4` where t.342 has
  `Bes3 A3 Bes3` and t.344 `C4 B3 C4`. A major third where the neighbours have
  a semitone. Fixed to `Bes3`. Three witnesses: the choir file, the two
  neighbouring bars, and the fact that the main notes rise Bes3–Ces4–C4 so the
  lower neighbour rises with them.
- **Chorus tenor: one difference**, also real. Tenor and bass sing "sal-va me"
  three times in unison at t.348–353, `C#3 C#3 C#3`, `E3 E3 E3`, `C3 C3 C3`;
  the tenor's last note was `C4`, an octave up. Four witnesses: our own bass in
  the same bar, the choir file's Tenor 1, and the two earlier repetitions,
  which both end on the note they start on.
- **Chorus soprano and alto: zero differences.** Their only apparent ones were
  the three-note-versus-two-note spelling of the same "sal-va" ornament, which
  is a notation difference in the choir's arrangement, not a pitch.

### Movement II·9b: "Sy-bil-la" was three words

All four voices printed `Sy bil-la,`. The cause is in the source PDF's own
text layer: of the four chorus rows on page 4, three read `Sy-bil--la,` and
the top one reads `Sy bil--la,` with the first hyphen missing, so
`korjaa_sanat.py`'s hyphenation vote never saw the word as one word in any
voice. Three rows out of four and the word itself (Sibylla) settle it. The
alto was also missing `cum` entirely; its bar has the same three slots as the
soprano's and the bass's, both of which carry `cum` on the second, so the
place is read rather than guessed. **The chorus tenor's missing `cum` was left
alone** — its bar has four notes, not three, so no other voice can say which
one the syllable belongs on.

### Movement V (Agnus Dei): the engraver's name, sung

`suomennos.py`'s broken-word list had carried `reutenauer` for two days, and
the text page printed it. It is the credit line **"A. Reutenauer"** at the
foot of page 5 of the source PDF — 767 pt down the page, far below the lowest
staff — which Audiveris read as two syllables and hung on the piano's bass
staff at bar 68. `P5` had a `¢|¢` on it at bar 31 from the same class of
mistake. Both gone.

This gave movement 14 **its first `korjaa_kasin.py` table**, and with it the
`-kasin.mxl` file that every other corrected movement has; `yhdista.py` now
reads that instead of the `-OMR-korjattu.mxl`. It does **not** remove the
standing hazard — the movement's older hand fixes still live only inside
`-OMR-korjattu.mxl`, so `korjaa_sanat.py` would still destroy them — but new
fixes no longer add to the pile.

## Verification

- **Per-staff note counts, computed from `MAPPING` and the sources and
  compared against the merged score**: all fifteen rows match exactly
  (chorus 1842 / 1810 / 1908 / 1813, piano 22312, and so on). This is the
  check that has twice found silent data loss.
- The seven key-signature-damage notes and the two accidental fixes were
  re-compared against the choir file afterwards: movement I's soprano and
  alto no longer differ anywhere in bars 1–78 except alto 77, and Rex
  tremendae's chorus bass no longer differs anywhere at all.
- All eight parts rebuilt; page counts 18/17/16/16/17/17/16/16, unchanged.
  One line of `stemmat-sisallys.txt` moved: Agnus Dei now starts on page 10
  rather than 9 in **Altto II**, because the alto's corrected bars 28–34 take
  slightly different width. No part gained or lost a page.
- The five `-kasin.mxl` files this session does not touch (02, 05, 11, 13, 16)
  were regenerated and came out **byte-identical as extracted XML**, so the
  two new operations touch nothing else.
- The full score converts without `-f`, **390** pages against the 391 recorded
  on 2026-09-09. One page fewer, cause not established; no reading part
  changed its page count, and the note-count check above rules out lost
  content.
- `python3 suomennos.py --teksti stemma-basso-1.mxl` read through: the bass's
  movement I text is clean prose. Gloss coverage 4588/4765 → **4601/4763**
  words, and the broken-form list 176 words in 77 forms → **162 in 68**.
- **343 tests** (306 before, +37): the `valmiit` field's three guards, the
  note-indexed `sanarivi`'s four, and whole-file tests that pin every
  syllable, lyric row, pitch and removal above — including the two rejected
  suggestions, so that nobody "fixes" them later.

## What is left here

- **Movement I's Kyrie (bars 79–140) is unverified**, and the choir file
  cannot verify it as things stand: the two files' bars stop corresponding
  somewhere around bar 94. Establishing that mapping — the way *2026-09-03
  (c)* did for Lacrymosa — would settle the largest remaining stretch of the
  movement, and the aligner already reports six candidate differences there
  that are currently indistinguishable from noise.
- **Alto bar 77**, above: the page and the music disagree.
- **Movement 07's S/A/T words** are still unchecked, and the movement has no
  source PDF. The bass's "same figure, wrong line of the stanza" slip could
  sit in any of them, and only a cross-voice reading would find it.
- **Movement V's S/A/T** are still the worst part of the score (word coverage
  48–59 %, fabricated content in bars 59–74). The choir file covers only 44 of
  the movement's 74 bars, so it can help with part of it.
- **Movement II·9b's notes**: the choir file reports five candidate
  differences (S t.27 and t.33, A t.40, T t.30 and t.36, B t.35), and four of
  them are a G against a G♭. The source PDF uses a subset font with private
  codepoints, so the glyph method needs its accidentals identified by counting
  before it can arbitrate — the same one-off identification page 3 of movement
  01 needed.
- The **ten remaining** `korjaa_sanat.py` suggestions it declines to apply.
  Three are now decided; the rest are all in movement 14, where the PDF's own
  text layer is sloppy (`do-na e is`, `do-do-e-is`).
- The **eleven other choir folders' worth of material** is still unexplored:
  `02_dies_irae`, `05_sanctus`, `07_libera_me` and `08_libera_me_2` have never
  been compared voice by voice, only in the four targeted spots earlier
  sessions used them for.
