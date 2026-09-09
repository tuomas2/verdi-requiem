*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-03 (b): three missing "Dies irae" interjections in Liber scriptus

The singer reported that bars 229, 231 and 233 should each have a short
`Di-es i-rae.` from the whole chorus, and that the bass part had nothing there
at all. They were right, and they were missing from **all four chorus voices**.

## What was there and what was missing

In Liber scriptus the chorus interrupts the mezzo's aria with a one-bar
figure — quarter rest, then a dotted eighth, a sixteenth and two quarters, all
on one note (S and A on D4, T and B on D3), text `Di-es i-rae.`
`05-Verdi-Liber_scriptus.mxl` has **three** of these, at local bars 16, 30 and
52 (continuous 177, 191, 213). The choir's own file has **six**. The other
three were whole-bar rests in every voice.

## Locating them: the mezzo is the anchor, not the bass

The choir file (`musescore/02_dies_irae`) is a condensed chorus-only cut of
`02`+`03`+`05`, so its bar numbers do not map to ours by any single offset —
matching its Bass 1 alone would have given a plausible-looking but wrong
answer. What settles it is that the file also carries the **Mezzo-soprano**
part, which is not condensed inside a stretch. Aligning the two mezzo lines
(`difflib` over per-bar pitch tuples) gives four clean blocks:

| choir bars | our local bars | offset |
|---|---|---|
| 120–125 | 12–17 | +108 |
| 126–130 | 26–30 | +100 |
| 132–135 | 49–52 | +83 |
| **136–177** | **64–105** | **+72** |

The last block is a 42-bar exact match, and the choir's six interjections sit
at 124, 130, 135, 140, 142 and 144. The first three land on our 16, 30 and 52 —
the ones we already have, which is the check that the mapping is right — and
140, 142, 144 land on local 68, 70, 72, i.e. **continuous 229, 231 and 233**.
Exactly the bars the singer named, arrived at from the other end.

## The fix invents nothing

All six occurrences are note-for-note identical in both files, in all four
voices. So the correction is a **copy of the part's own bar 52** into 68, 70
and 72 — new operation `kopioi_tahti` in `korjaa_kasin.py`, which refuses to
run unless the target is nothing but rests. Lyrics come along with the notes,
so `Di-es i-rae.` needed no typing and cannot be mis-hyphenated.

`05-Verdi-Liber_scriptus-kasin.mxl` is the new derived file; `yhdista.py` reads
it in place of the raw source (the filename is a key in **three** places —
`MOVEMENTS`, `MAPPING` and `DIES_IRAE_ALUT` — plus the pin in `test_yhdista.py`).

## And nothing else is missing there

Since the choir file was open anyway, its Bass 1 was diffed against our whole
`02`+`03`+`05` chorus bass, bar by bar. **174 of its 177 bars now match.** Of
the three that do not:

- Two (choir 117–118) are ours being *richer*, not poorer: we have `A3`+`C#4`
  as a chord where the choir file's Bass 1 has only the `C#4` — the divisi.
- One was a real single-note disagreement, flagged not fixed at the time: at
  II·1 bar 28, the last syllable `la,` of "Da-vid cum Sy-bil-la," is `A3` in
  our file and `A2` an octave lower in the choir's Bass 1 (their Bass 2 rests,
  so it is not a divisi). **Settled 2026-09-04 in the choir file's favour**:
  the singer reported the same thing by ear, and the figure is internally
  consistent — bars 32, 34 and 36 all drop the octave on the same cadence. See
  *2026-09-04*.

## Verification

- Note counts per staff: every chorus voice **+12** (4 notes × 3 bars), nothing
  else changed; measure count still 1807.
- Read back off the rendered `stemma-basso-1.pdf` page 4, which now shows
  `Di-es i-rae.` six times, at 177, 191, 213, 229, 231 and 233.
- The raw source is untouched and a test asserts it stays that way.
- 73 tests.
