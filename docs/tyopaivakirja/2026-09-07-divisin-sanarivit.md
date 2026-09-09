*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-07: the divisi's two lyric rows were the wrong way round

The singer reported that in Lacrymosa bars 677–679 "Basso 1 and Basso 2's words
are completely backwards — 'Pi-e Je-su' should be lower, now it is upper". They
were right, and this is the first report in this file that is about **layout as
content**: nothing was misspelled, misplaced on a note, or missing.

## What was wrong

The chorus bass staff carries two voices there (the divisi fixed on
2026-09-03), and each sings its own text:

| Voice | Notes | Text | Lyric row |
|---|---|---|---|
| upper (`P9`, merged voice 2) | `F3 Bes3 C4 Des4 …` | "Pi-e Je-su Do-mi-ne," | **2** → now 1 |
| lower (`P8`, merged voice 1) | `Bes2 Aes2 G2 Ges2 F2` | "Pi-e Je-su" | **1** → now 2 |

MuseScore prints row 1 above row 2, so the reading part put the **lower** voice's
words on the **upper** row. Two independent things say that is backwards. The
source page 11 prints the upper voice's words *above* the bass staff and the
lower voice's *below* — the same order, and the reason the upper voice's row was
mistaken for the chorus tenor's back in 2026-09-03. And a singer reading a
divisi staff reads the rows top-down as the voices sit top-down; there is
nothing else in the part to say which row is theirs.

## Why the source file has it inverted, and why that is not a source bug

`11-Verdi_Lacrymosa.mxl` keeps the two voices as two separate `<part>`s (`P8`,
`P9`). Each numbers its own lyrics with nothing to compare against, and their
`default-y` values (−80 for `P8`, −97 for `P9`) say the same thing the numbers
do. In the source that is harmless, because the two parts are never on one
staff. It becomes wrong only in `yhdista.py`'s merged staff — which is exactly
the situation `korjaa_kasin.py` exists for, so the fix is six table rows, not a
tool change.

## The fix

New operation `("sanarivi", vanha, uusi)` in `korjaa_kasin.py`: move a whole
measure's syllables from one lyric row to another, asserting the row they are on
now. It also drops `default-y`, for the same reason `korkeus` drops it and
`kesto` drops `default-x` — the value was computed for the row the syllables
are leaving, and MuseScore lays them out by itself.

Three rows per part, bars 54–56 (continuous 677–679): `P9` 2 → 1, `P8` 1 → 2.
**Both halves are needed**, and swapping only one would have been worse than
doing nothing: `normalise_lyrics` lifts everything to row 1 when a measure has
no row-1 syllable at all, so moving `P8` to row 2 alone would have collapsed
both voices' texts onto one row.

## Verification

- The merged score differs from the previous build in **exactly 11 places**, all
  of them a `<lyric>`'s row number on the same note — compared per note as
  (measure, index, pitch, duration, voice, lyrics) across every part. Nothing
  else in 1807 bars moved.
- 188 tests. `test_divisin_sanarivit_ovat_aanten_mukaisessa_jarjestyksessa`
  pins the row per voice, and a companion test pins that `P8` is on row 1
  *everywhere else* — row 2 is a three-bar exception, not a new normal.
- Both bass parts re-rendered, 16 pages each, unchanged;
  `stemmat-sisallys.txt` byte-identical. The full score converts without `-f`
  (363 pages).
- Read back off `stemma-basso-1.pdf` page 8 as an image: the upper row now
  reads "Pi - e Je - su Do - mi - ne," and the lower "Pi - e Je - - su".
