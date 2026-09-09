*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-08-31 (later): Agnus Dei's chorus bass, whole movement verified

The user asked for the obvious next thing: compare `Kuoro B` of movement 14
against the choir's own file **from the first bar to the last**, rather than
chasing one flagged spot at a time. That closed the bars 59–74 item the
section above had left open as "needs a re-OMR" — **it did not need one**.

## Result: an exact match

`14-Verdi_requiem_agnus-dei-OMR-korjattu.mxl`'s `Kuoro B` (`P4`) now agrees
with `musescore/06_agnus_dei`'s chorus `Bass 1`+`Bass 2` **note for note over
all 74 bars, with zero differences**, and every one of those 74 bars is
metrically valid (4/4, four beats). 15 defects were found and fixed:

| Bar | Defect | Fix |
|---|---|---|
| 4 | full-measure rest with `duration` 36, not 48 | duration corrected |
| 16, 23 | missing grace note (acciaccatura) `F3` before the bar's last `E3` | grace note added |
| 26, 63 | measure only 3 beats long | trailing quarter rest added |
| 42 | `B2` written as `duration` 36 with `type` half — measure 5 beats | duration corrected to 24 |
| 59 | measure held a clef and **no note at all**; should be a whole note | `C3` whole + syllable "Do" |
| 60 | **entirely contentless** `<measure .../>` | `C3` whole + "na," |
| 62 | `E3` carried no syllable | "e" added |
| 64 | 2 beats, missing its bracketing rests | quarter rest added at each end |
| 67 | 3 beats — the `G3` fell a beat early | quarter rest inserted before it |
| 68 | `G2` carried no syllable | "e" added |
| 69 | **entirely contentless** | `Ab2` whole + "is," |
| 72 | **entirely contentless** — the movement's final chord | `C3` whole + "na." |
| 74 | **entirely contentless** | full-measure rest |

Before the fix the reading part ended on an unterminated "do" at bar 71; it
now ends "do – na." on a whole note, and bars 73–74 collapse into a clean
2-bar multimeasure rest.

## The methodological lesson: never pitch-compare without chord members

The first pass of this comparison **reported two wrong-pitch findings that
were not real**: bars 45 and 64 appeared to have `G2 C3` where the choir file
had `F3 E3` / `G3 G3`. Both are **divisi chords**, and the comparison script
was walking `<note>` elements while skipping any with a `<chord>` child — so
it saw only each chord's first (lower) note and never the upper one, which was
correct all along.

What settled it is worth keeping: the choir file's **`Bass 2`** has
`r G2 C3 r` at exactly its bars 26 and 36 — and those are the **only two bars
in the whole movement where `Bass 2` sings at all**. Two independent files
agreeing on a two-bar divisi that occurs nowhere else is not a coincidence.
So: when comparing pitches, either fold chord members into the comparison or
compare `Bass 1` and `Bass 2` as a pair. A skipped chord member does not look
like missing data, it looks like a **wrong note**, which is the most alarming
and most misleading possible false positive.

## Why this worked where the previous manual attempt failed

The earlier attempt tried to *derive* the content from the rendered page and
got inconsistent bar-boundary reads. This pass never asked the page to
produce content. It used the choir file to form one specific hypothesis per
bar ("is there a whole note here, and is it `C3`?") and used the page only to
confirm or refute it. Confirming a named hypothesis at 200 dpi is reliable;
deriving pitches from pixels is not — that asymmetry is the whole trick, and
it is the same discipline the *Lacrymosa* fix used.

Two things made it cheap:

- **This PDF prints its bar numbers**, boxed at each system start (50, 55, 59,
  63, 68 on pages 4–5). They agree with the file's own `<measure number>`
  exactly. That is a free, unambiguous anchor, and the previous attempt's
  "inconsistent bar-boundary reads" problem simply does not arise once you
  read the printed number instead of counting barlines.
- **`<print>` elements give the OMR's own page/system layout**, so the page
  holding any bar is computable before rendering anything:
  page 1 = 1–20, 2 = 21–35, 3 = 36–49, 4 = 50–62, 5 = 63–74.

## Third independent confirmation of the tacet fix

The previous session's most invasive change — replacing OMR's fabricated
notes at bars 27–39 and 46–58 with plain rests — is now confirmed a third
time. The choir file rests across exactly the same three spans, and page 4
prints only **two** vocal staves for bars 50–58 (the S + M-S soloists) before
the chorus's four staves reappear at bar 59.

## And it explains the 30-measure gap

*The choir's own MuseScore practice files* below asks why the choir's Agnus
Dei is 44 bars against our 74, and warns not to trust it until that is
explained. It is now explained exactly, and it is pure chorus-only trimming:

| Our tacet span | Choir's | Bars trimmed |
|---|---|---|
| 1–13 | 1–3 | 10 |
| 27–39 | 17–20 | 9 |
| 46–58 | 27–30 | 9 |
| 73–74 | (none) | 2 |

10 + 9 + 9 + 2 = **30**, and 74 − 44 = 30. Nothing is missing from either
file.

## Verification

- Per-part note counts before/after: only `P4` changed, **+6** (4 whole notes,
  2 grace notes) — `P1`, `P2`, `P3`, `P5`, `P6` byte-for-byte identical in
  count, measure count unchanged at 74.
- `mscore` converts the movement with no warnings and **without `-f`**, 6 pages.
- The merge reproduced the same +6: `Kuoro B` 1795 → 1801, total measures
  unchanged at 1807, and `ensure_filled`'s "contentless measures patched"
  count fell from 26 to 21 — exactly the five measures that got real content
  (59, 60, 69, 72, 74).
- All eight reading parts and the practice `.mscz` were re-rendered (seven of
  the eight had been stale since the *Lacrymosa bar 669* fix). `stemmat-
  sisallys.txt` was regenerated; `B I`/`B II` are now 13 pages, not 14.
- 32 tests pass.
- The result was read back off `stemma-basso-1.pdf` page 9 as a rendered
  image, not just from the data.

## Still open here: Soprano, Alto, Tenor

Only the bass was done. The other three chorus voices of movement 14 are
still OMR output and still visibly wrong in the same stretch: `Kuoro T` has a
contentless bar at 60, and all of `Kuoro S`/`Kuoro A`/`Kuoro T` have one at
72, so the final chord is missing from three of the four voices. Lyric
coverage is 48–59 % for them against the bass's 66 % (and the bass's
remaining 29 wordless notes are melisma-internal notes and chord second
notes, which correctly carry none). The same method applies unchanged — the
choir file has `Soprano`, `Alto`, `Tenor 1` and `Tenor 2` — and the offsets
worked out above (−10, −19, −28, −28) should carry straight over.
