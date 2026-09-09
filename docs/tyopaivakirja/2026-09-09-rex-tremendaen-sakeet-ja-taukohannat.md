*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-09 (d): Rex tremendae's three lines, two piano marks, and a row of paper per movement

Five reports in one batch, all from the chorus bass, and for the first time
three of the five are about **notation the source never had** rather than
about a syllable in the wrong place: two missing dynamics and a whole class of
wasted paper. The count of things `korjaa_kasin.py` can do went from eleven to
thirteen.

## 1. Rex tremendae: the stanza's three lines, one of them printed twice

The singer reported that bars **340–341** should read "qui sal-van-dos sal-vas
gra-tis" and bars **362–363** "sal-va me fons pi-e-ta-tis". Both were true, and
both were the same mistake: the file repeats one line of the stanza and drops
the next.

The stanza is three lines — *Rex tremendae majestatis, / qui salvandos salvas
gratis, / salva me fons pietatis* — and the chorus bass sings each of them to
the **same figure**: six notes in one bar, two in the next. That is why the
error is invisible from the notes and why OMR or a copyist can slide a line
without leaving a trace. Before the fix:

| Bars | Was | Is |
|---|---|---|
| 336–337, 338–339 | Rex tremendae majestatis (×2) | unchanged |
| 340–341 | Rex tremendae majestatis (**third time**) | qui salvandos salvas gratis |
| 356–359 | rex tremendae majestatis (×2) | unchanged |
| 360–361 | qui salvandos salvas gratis | unchanged |
| 362–363 | qui salvandos salvas gratis (**second time**) | salva me fons pietatis |

Movement 07 has no source PDF, so there is no page to look at. The file
proves both spots by itself, three ways:

- **The figure is the same in all four places and each line is eight
  syllables**, so nothing about the music decides which line belongs where —
  but the file already carries *both* lines on this same figure elsewhere:
  bars 360–361 "qui sal-van-dos sal-vas gra-tis," and 344–345 "sal-va me,
  fons pi-e-ta-tis,". Hyphenation and punctuation were copied from those,
  not invented. A test pins that the corrected bars are syllable-for-syllable
  identical to their models.
- **Corrected, each passage reads the stanza through** without repeating any
  line three times, and the third line stops being missing from the first
  passage entirely.
- **The other three chorus voices are no help here and that is itself
  informative** — they are in the "sal-va me" interjections throughout, so
  the cross-voice check that found the Lacrymosa defect (*2026-09-03 (c)*)
  does not apply. The comparison had to be within the movement.

21 differences in `07-…-kasin.mxl`, all of them a syllable's text or
`syllabic` on a note whose pitch, duration and voice are untouched.

## 2. The divisi's rows again — and this time above the staff

Bars **367–369** are a chorus-bass divisi, and the singer reported that Bass
I's text sits **above** the staff while Bass II's is below, and asked for both
below, Bass I on top.

This is the same defect as Lacrymosa 677–679 (*2026-09-07*) with one extra
twist. The source has the upper voice on lyric row 2 and the lower on row 1 —
backwards, since MuseScore prints row 1 above row 2 — and on top of that the
row-2 syllables carry the source's own `default-y="38"`, a **positive** offset
that puts them above the staff. So the two voices were not merely in the wrong
order, they were on opposite sides of the staff.

The Lacrymosa fix does not work here. There the two voices are two separate
`<part>`s, so `sanarivi` could move each one's row on its own. Here both
voices are in the same part, and moving row 1 to row 2 would land on top of
the syllables already there. New operation:

    ("vaihda_sanarivit", "1", "2")     # koko tahdin rivit keskenään

It swaps the two rows in one step, asserts that exactly those two rows are
present, and drops `default-y` for the same reason `korkeus` and `sanarivi`
drop theirs — the value was computed for the row the syllables are leaving.
It writes the numbers back in **the source's own spelling** (`part8verse1`,
not `1`): a mixed spelling inside one part confuses MuseScore's row counting,
which is why `yhdista.verse_number` exists at all.

Bar 369 is in the fix although the singer said 367–368. Both voices sing
"me," there, so the order does not show — but its row-2 `default-y` would
have kept Bass I's "me," above the staff after two bars below it.

## 3. Two missing dynamics, and where the mark really was

The singer asked for a **p** at the start of bar **607** and bar **677**: both
are quiet entrances, and in both the staff still shows a much older loud mark.

Bar 607 is the clearer case, and the source says what happened. In
`10b-…-OMR-korjattu.mxl` the chorus bass has `ff` at bar 575 and **nothing
after it in the whole movement**, while the piano has `ff` at 604 and **`p` at
606**. The dynamic change is in the file — it is just on the accompaniment
staff. The chorus rests through 606, so its own mark belongs on the entrance,
bar 607. The singer's description ("it comes in pretty forte before that but
it's quiet") is exactly what the part printed.

Bar 677 is Lacrymosa's "Pie Jesu Domine", the chorus bass entering after
eleven bars of rest. The staff has no mark; the neighbours all say quiet —
chorus soprano `pp` at 678, the four soloists at 679, piano `p` at 679 — and
the chorus's own next mark is `mf` only at 681. The mark written is the
singer's **p**, not the neighbours' `pp`, and the table row says so, so it is
one word to change if the choir book disagrees.

New operation:

    ("dynamiikka", "p")                # merkintä tahdin alkuun

Above the staff, where the sources put their own (lyrics are below), with no
`default-y` so MuseScore places it. The allowed marks are a short list, so a
typo stops the run instead of writing an element MuseScore silently ignores.

## 4. Movement 10b gets a table — and the warning about it turns out to be wrong

Bar 607's fix needed somewhere to live, and II·9b had no `Osa` row: its only
derived file was `-OMR-korjattu.mxl`, which `korjaa_sanat.py` rewrites from
scratch. So the movement got the same two-layer chain as movement I:

    10b-…-OMR.mxl → (korjaa_sanat) → 10b-…-OMR-korjattu.mxl
                  → (korjaa_kasin) → 10b-…-kasin.mxl

That is five mechanical edits in `yhdista.py` (`MOVEMENTS`, `MAPPING`,
`OMR_SOURCES`, `DIES_IRAE_ALUT`) and its pinned test, plus one `Osa` row.

Then the standing warning got measured instead of believed. `CLAUDE.md` and
[`docs/menetelmat/omr.md`](../menetelmat/omr.md) have said since 2026-08 that
**movements 14 and II·9b** carry hand fixes that live only in their
`-OMR-korjattu.mxl`, so a plain `korjaa_sanat.py` run destroys them. Backing
up all three `-korjattu` files, running the script and comparing the XML:

| File | After a plain re-run |
|---|---|
| `01-…-OMR-korjattu.mxl` | identical |
| `10b-…-OMR-korjattu.mxl` | **identical** |
| `14-…-OMR-korjattu.mxl` | **differs, 570 058 → 604 055 bytes** |

So II·9b was never at risk — it is a pure derivative, and the warning applies
to **movement 14 alone**. Movement 14's exposure is real and large. The
warning is now narrowed everywhere it appears; the check took two minutes and
had been carried as a caveat for weeks.

## 5. A row of paper per movement, wherever the singer falls silent early

The last report was a question rather than a defect: bar **383** is a single
empty bar that takes a **whole system**, the block **613–623** takes another,
"and there are some others" — could anything be done, and would deleting the
empty bar be reasonable?

Deleting it would not: 383 is a bar the conductor can call, and 384–385 are
already missing from the sources. The cause is elsewhere, and it is a
side-effect of a deliberate rule. Every movement starts a new system so its
title can be found by flipping pages. When the singer's part falls silent
before a movement ends, those trailing rest bars cannot join the next
movement's system — and if they do not fit on the previous one either, they
get a system of their own, stretched to full width.

Measured across all eight parts, asking MuseScore for the computed layout
(the trick `sivuotsikot.py` already uses): **10–12 of every part's ~140
systems held no note at all.** Most of those are honest — a movement the
chorus is tacet for is one heading and one multimeasure rest, and that row is
the information. The waste is the tails: 383, 613–623, 269, 701, 137–139,
72–74.

The fix is one condition, in `yhdista.py`:

> Drop a movement's forced `new-system` when the previous movement ends in
> rest-only bars **and has at least one sounding note.**

The second half is what keeps it from going too far. Without it, consecutive
tacet movements would collapse onto one row with their headings side by side
— for the chorus, II·7, II·8 and II·9 are all silent, and their three titles
would share a system. With it, only the tails move.

**It cannot make a part longer.** A tail either had a system to itself, which
is now saved, or sat at the end of one, and moves to the start of the next —
the same number of systems either way. Measured, per part, systems before →
after: 140→136, 139→135, 142→137, 139→134, 142→139, 141→136, 137→133,
143→140. Rest-only systems 10–12 → 6–8. Tenori II lost a page (18 → 17) and
no part gained one; several movements now start a page earlier.

Two variants were tried on one part and the simpler won. Adding a forced
break at the tail's first bar, on top of removing the one at the movement
start, gave the same page count and put bars 383 and 613–623 on exactly the
systems removal alone had put them on: MuseScore breaks there by itself, and
the forced break bought nothing. So the tool only ever removes a break, never
adds one — which is also why it cannot make a part longer.

It runs for single-part outputs only. In the full score a system break is
shared by all fifteen staves, so the condition would have to hold for every
one of them at once — and it never does, because the piano plays across the
movement seams.

## Verification

- The whole 1807-bar score differs from the previous build in **23 places**,
  every one of them in `Kuoro B` and in the nine bars intended, compared per
  note as (measure, index, pitch, duration, voice, lyrics, dynamics). No
  pitch, duration or voice changed anywhere. Note counts per staff identical.
- Both bass parts re-read as images at bars 340–341, 362–363, 367–369, 607
  and 677: the text is right, the divisi's rows are the right way up and both
  below the staff, and both `p`s are over the right barline.
- `python3 suomennos.py --teksti stemma-basso-1.mxl` reads the corrected
  passages as prose: "Rex tremendae majestatis, Rex tremendae majestatis, qui
  salvandos salvas gratis, salva, salva me …" and "… qui salvandos salvas
  gratis, salva me, fons pietatis, fons pietatis …".
- All eight parts rebuilt, page counts 18/17/16/16/17/17/16/16 — one fewer
  than before on Tenori II, unchanged elsewhere. `stemmat-sisallys.txt`
  updated accordingly.
- The full score converts without `-f` (391 pages).
- 306 tests. New: five for `vaihda_sanarivit`, four for `dynamiikka`, six for
  `yhdista_taukohannat`, and whole-file tests that pin Rex tremendae's three
  lines against their models in the same movement and II·9b's two dynamics.

## What is left here

- Movement 07's **notes** are still unchecked against a second source, and
  `musescore/03_rex_tremendae` (64 bars against the file's 62) exists for
  exactly that. The same "same figure, different line" slip that hit the text
  twice could have hit a pitch.
- Movement 07's **S/A/T** were not looked at. If the bass had one line
  printed twice, they may too.
- Movement 14 is now the **only** movement whose hand layer is at risk from
  `korjaa_sanat.py`, and the way out is the one movements 01 and 11 took: diff
  the hand-edited file against its raw source and write the differences into
  an `Osa`. Its diff includes note-level fixes and two tacet spans.
