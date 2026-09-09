*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# Lacrymosa's chorus bass: wrong text, not missing measures

Found 2026-08-28, while cross-checking the new continuous numbering against a
second Lacrymosa PDF the user located for comparison (`Verdi_Lacymosa.pdf`,
another "Print to PDF" export, same CPDL edition, vector text — the same good
case as 01/14/II·9b). The user first noticed their own reading part ends on
"par-ce" where the reference PDF ends on "A-men" — i.e. the *last* two
measures looked wrong. Checking properly showed the real damage was much
bigger.

**This file is not one of the OMR movements.** `11-Verdi_Lacrymosa.mxl` came
from the CPDL Finale 2014 + Dolet batch like 10 other movements, and was
believed reliable. It wasn't, for one voice: the chorus bass (`Kuoro B`, the
line the user reads) had its final ~30 measures' text either **silent where
the real part sings**, or **carrying the wrong words** — apparently a chunk of
its own much-earlier "Lacrymosa dies illa...huic ergo parce" text got
duplicated onto later measures that actually carry "dona eis requiem...
Amen". The notes/rhythm were mostly fine underneath; only the lyric layer (and
a handful of wholly-missing measures) was wrong. This is a plain authoring bug
in a "trusted" source file, unrelated to OMR — it had been sitting undetected
since the original merge.

## How it was found and fixed

1. Compared `11-Verdi_Lacrymosa.mxl`'s `Kuoro B` (P8) lyric stream against
   every other voice in the same file (`P1`–`P7`): all seven others reach
   "...dona eis requiem. Amen."; only `P8` stopped at "...huic ergo parce"
   with three trailing rest measures.
2. OMR'd the new PDF whole (`Audiveris -batch -transcribe -export
   -constant ...pdfResolution=450`, same recipe as always) — 16 pages, 10
   staves per system where the full choir is active, so a ~22-minute run,
   much longer than the 51-measure II·9b job.
3. **The OMR part numbering is not stable across the piece.** This PDF's
   layout hides inactive staves (it opens with just 2 of the eventual 10:
   Mezzosoprano solo + Bass solo, with Soprano/Tenor solo and the four chorus
   parts entering one at a time as the fugato progresses). Audiveris's "P8"
   therefore does *not* reliably mean chorus bass in the early measures — it
   only stabilises once the full 8-voice texture is established partway in
   (confirmed measure-for-measure against page images). Trusting OMR's
   part-N labelling blindly from measure 1 would have been wrong.
4. Where OMR's `P8` and the source's `P8` had matching notes but conflicting
   lyrics, **direct visual inspection of the actual page settled it**, not
   OMR's OCR and not the source file's say-so alone: rendered the relevant
   pages at 200–250 dpi and read the chorus-bass staff (identifiable as the
   4th of 4, or 8th of 8, visible bass-clef vocal staff — soloists-then-chorus
   in both groupings) directly. This caught things neither source had right:
   OMR's own OCR mangled several short syllables (`D0`→`Do`, `qu1`→`qui`,
   `J`→`Je`, `me,`→`ne,` — the familiar single-letter-miss failure mode from
   the lyrics-fixing work on 01/14) and missed the "A" of "Amen" outright
   (confirmed by eye on the final page: all 8 vocal staves sing "A - - - men"
   together on the closing chord, chorus bass included, both notes G3).
5. Patched only what was actually wrong: added the ~18 notes at measures
   46–51 that the source had as bare rests (copied from OMR, divisions
   rescaled ×2 to match the source's own `divisions=4`), and rewrote the
   lyric *text* — not the notes, which already matched — for measures 54–56
   and 58–75. Measures 1–45, 52–53, and 76–78 were already correct and left
   untouched.
6. A companion divisi part (`P9`, "the chorus-bass divisi at 54–56" from the
   *Merging* notes) already had the right notes for that spot and needed no
   change — confirmed by the fact that its notes independently matched
   OMR's second voice at those measures exactly.

## Verification

Per-part note counts in `11-Verdi_Lacrymosa.mxl` were compared before/after:
only `Kuoro B` changed (+18 notes, from the added measures; every other part,
including the divisi `P9`, identical). Re-running `yhdista.py` reproduced
that same +18 in the merged score's `Kuoro B` total (1888→1906) with the
overall measure count unchanged at 1807 — i.e. content filled in, nothing
added or removed elsewhere. The file converts in MuseScore without `-f`
(checked directly, not just via the merged score). The corrected reading
part was rendered and read back: `stemma-basso-1.pdf` now shows "...re-qui-em,
re-qui-em, do-na e-is-re-qui-em. **A men.**" where it previously showed
"...par-ce." at the same spot.

## What is still open here

~~A few individual syllable-to-note placements *inside* melismas are
best-effort reconstructions, not confirmed note-by-note against the page.~~
**Closed 2026-09-03**: every syllable of this movement's chorus bass is now
confirmed against the printed page at note resolution, by measuring the
syllables' x coordinates rather than by eye. See *2026-09-03 (c)*.

**Soprano/Alto/Tenor and the soloists in this same file were not audited.**
Only chorus bass was checked this closely, because it is the line the user
reads; the same class of bug (duplicated/misplaced lyric text) could in
principle exist elsewhere in this "trusted" batch of 10 movements and would
not necessarily be caught by anything currently in this pipeline.
