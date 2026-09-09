*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-07 (b): a natural in an empty bar, and the music font as a ruler

The singer reported that movement I bar 59 shows a natural sign in the chorus
bass, and that it looks pointless because the bar is nothing but a rest. The
sign is not pointless — it is a key-signature cancellation, and cancellations
are printed whether or not the bar sings. It was in the **wrong bar**: the
source page cancels the one flat at bar **56**, and the OMR recorded the
cancellation three bars later.

## Why the OMR got it wrong, and why the mistake is invisible

Every printed system repeats the key signature at its left edge, and Audiveris
reads it there every time. Movement 01's systems on page 3 start at bars 50, 59
and 66, and the file carries a `<key>` in exactly those bars plus 17, 27, 28,
35, 67, 74, 91, 99, 106, 115, 124 and 129 — i.e. a `<key>` at nearly every
system start, almost all of them repeating the key that was already in force.
Harmless duplicates, except where one of them is the first the OMR noticed of a
change that happened **earlier in the previous system**. Then the change moves
to the system break, and nothing in the file looks wrong: bar 59's entry is a
perfectly ordinary key signature and every bar after it is in the right key.
Only bars 56–58 are wrong, and only for a reader who compares with the page.

## The measurement: read the music font, not the picture

The project's standing rule is *confirm a named hypothesis, never derive
content from pixels*. For a key signature there is a third way that is better
than either, and it is new here: **these PDFs carry the music itself as text**.
`mutool draw -F stext` returns every glyph of the music font `Mozart9` with a
quad, so a clef, a flat, a sharp and a natural each have an exact x and y.

    mutool draw -F stext -o p3.stext 01-Verdi_Requiem.pdf 3

The glyph codes have to be identified once, and counting does it without
guessing: on page 3 the character `&` occurs 12 times and `%` 6 times, and
12 + 6 = 18 = three systems × six staves, so those are the treble and bass
clefs. `+` occurs 18 times at three x values 3 pt apart at the left edge of the
bottom system — the three sharps of that system's key signature. `.` occurs six
times at a **single** x, one per staff, at exactly the y values the previous
system's flats sat at: the cancellation. So `.` is the natural, `+` the sharp,
`-` the flat.

The x of those six naturals is 368. The bar they stand in comes from the OMR's
own `<measure width>` values, summed along the system and scaled by 0.306 (the
constant the lyric work already measured for this movement): bar 50 begins at
64, 55 at 331, **56 at 367**, 57 at 407, 58 at 468. Bar 56, to a point. No
image was rendered to reach that, and there is nothing to squint at.

Two checks with the same method, both of which had to come out right before the
first was believed:

- **Page 3's second key change is correct as the file has it.** 18 sharps stand
  at x 121–128 in the bottom system, whose first bar 66 begins at x 64 — so
  they are mid-system, at bar 67, exactly where the file puts them. The
  rendered page agrees: bar 66 finishes the soprano's "- ne," and then comes a
  double bar and three sharps.
- **Page 1's change to three sharps is correct too**, 18 sharps at x 368–374 in
  the middle system, where bar 17 begins at 367.

So exactly one key change in the movement is misplaced, and it is the one the
singer's eye landed on.

## The fix is a whole-file table, not a `korjaukset` row

A key signature is written into **every part separately** — all 17 in this
file. `korjaa_kasin.py`'s `Osa` rows target one `osasto`, and moving the change
in `P16` alone would have fixed the bass part while leaving the full score's
fifteen staves changing key in two different bars. So the operation gets a
table of its own:

    SAVELLAJIT = (
        Savellaji(mxl=OSA_I.mxl, out=OSA_I.out, siirrot=(("59", "56", 0),)),
    )

`siirra_savellaji` **moves** the `<key>`, it does not copy it — a copy would
mean the key changes twice — and it asserts, per part, that the old bar really
carries that key and that the new bar does not. The rest of the old
`<attributes>` stays where it is: bar 59's `<staff-details>` describes bar 59,
not the key. Where the target bar has no `<attributes>` at all (none of the 17
did) one is created before the first note, since `<attributes>` governs what
follows it.

## The same error, bigger, in the soprano and alto — found, not fixed

The same measurement on page 2 shows the three-sharp key cancelled and one flat
set at x 138–147, and bar 28 begins at x 135. So the change to F major belongs
to bar 28. The file has it at bar 28 in `P15` and `P16` — chorus tenor and
bass — and at bar **35** in the other fifteen parts, the next system start.
Same failure, seven bars instead of three.

**This one is not a key-signature fix, and moving the signature alone would
make it worse.** Audiveris reads pitches under the key it believes is in force,
so `P13` and `P14` read bars 28–34 with three sharps and wrote what they
believed: the chorus soprano's "Te decet hymnus" is `F#4 F#4 C#5 D5 E5` and the
alto's `F#4 G#4 A4 G#4 F#4 E4 A4`, where the bass and tenor have plain F major
(`F3 G3 A3 G3 F3 E3 D3 C3 …`). The wrong signature is the cause; the wrong
pitches are the damage, and they have to be re-read from the page. Recorded as
an open item and in `luotettavuus.py`, which now separates movement I's
soprano and alto (⚠, this defect named) from its tenor (○, unaffected).

## What the singer actually gains

The natural now stands at bar 56, where the source prints it and where the
"4 Soli" section begins, and bars 58–59 — two rests with a key change wedged
between them — collapse into one `[58–59]` block. One stray bar fewer on the
page, and the part's key signatures now agree with the printed score from bar
50 to bar 67.

## Verification

- Compared per note as (pitch, duration, voice, lyrics) keyed by (part,
  measure, index): **34 202 notes in the merged score, zero differences**. The
  only changes anywhere are 30 key signatures, 15 staves × (bar 59 → bar 56).
  In `01-…-kasin.mxl` it is 34, 17 parts × the same move.
- The six other `-kasin.mxl` files came out **identical** as extracted XML, so
  the new code path touches nothing else.
- Merged score converts without `-f`, 363 pages, unchanged. All eight parts
  re-rendered; page counts unchanged (S I/S II/T II 17, rest 16) and
  `stemmat-sisallys.txt` byte-identical.
- 205 tests (193 before, +12): the operation's guards, and a pin that movement
  I's cancellation is at 56 in all 17 parts while 17 and 67 stay put. Bar 59 is
  the file's own reading and looks right, which is why it is worth pinning.
- Read back off the rendered `stemma-basso-1.pdf` page 1 as an image: bar 55
  ends "et.", a double bar and the natural stand at 56, 57 sings "Re-qui-em,"
  and 58–59 are one rest block.
