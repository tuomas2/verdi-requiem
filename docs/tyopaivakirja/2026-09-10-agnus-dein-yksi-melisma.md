*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-10 (g): Agnus Dei 40–43, and what a ✔ was promising that it had not done

The singer, by ear:

> agnus dei basson tahdissa 40-43 pitäisi olla 40 tahdissa do- joka loppuu 43
> tahdin ensimmäiseen nuottiin (tai oikeastaan jatkuu na tavu vielä toiseen
> nuottiin asti).

Right on all counts. The part read `Do` (40) `na,` (41) `do` (42) `na` (43) —
two "dona"s where the bass sings one, with a two-bar melisma in between.

## The measurement

Bars 40–45 are page 3, system 2 of the source PDF (computed from the OMR
file's own `<print new-page>` / `<print new-system>`, not by thumbing). The
page's own text layer names the syllables and their x, so the four chorus
voices' lyric rows can be read side by side without rendering anything —
`mutool draw -F stext`, font Garamond 10, the chorus bass being the fourth
vocal staff (bass clef at x = 27, its lyric row at y = 425):

    S: Do-@45 na,@96 do-@172 na@231 e-@259 is@278 do-@305 na@392 …
    T: Do-@45 na@120  do-@172 na@232 e@259  is@305 re-@362 qui-@392 …
    B: Do-@45         na@259 e-@305 is@329 re-@362 qui-@392 em,@438 do-@529 na.@553

Bars start at x = 45, 96, 172, 259, 362, 529 (the bass's own noteheads: two
whole notes at 45 and 96, two halves at 172 and 208, then bar 43's dotted
quarter at 259, an eighth at 290, and quarters at 305 and 329). **The bass's
row has nothing at all between x = 45 and x = 259.** The upper voices sing
"do-na," twice, the bass once — exactly as reported, and the reason the
machine read it wrong is now visible too: it copied the upper voices' figure
onto the bass staff.

Three rows into `korjaa_kasin.py`'s `OSAT_V`, which got its first chorus-voice
entry (`P4`) at the same time: `Do` from `single` to `begin`, and the two
stray syllables out.

## The dot that only the rendered page showed

The rebuilt bar, read back as an image at 450 dpi, printed bar 42 as **half +
dotted half** — five beats in a 4/4 bar. In the file the note is
`<type>half</type><dot/>` with `<duration>24</duration>`: MuseScore draws a
dotted half and counts a half. Three independent things say there is no dot —
the bar is 4/4 and 2 + 3 does not fit it, the choir's own file
(`musescore/06_agnus_dei`, its bar 23 = our bar 42) has two plain halves, and
our own duration is 24 — while the source page does *draw* the dot (page 3,
x 211, y 403). Same situation as Lacrymosa 653: the printed mark says what
the engraver drew and nothing about whether he was right. Fixed with a `kesto`
row, `"24/half." -> "24/half"`.

It is the only dot-vs-duration contradiction in the movement: all six staves,
zero others. A test pins that, so a re-run cannot quietly grow a second one.

**This is the check that found it.** Not the note comparison, not the page —
looking at the finished bar as a picture. Every session that skipped that step
has shipped something, and this one was three bars from doing the same.

## What the entry is really about: the ✔ was an overclaim

Agnus Dei's chorus bass has been marked **✔ varmistettu** since 2026-08-31,
on the strength of a note-for-note comparison against the choir's own
MuseScore file over all 74 bars with zero differences left. That part is true
and stands. But `luotettavuus.py`'s own definition of ✔ is "the whole movement
compared note for note **and syllable for syllable**", and the syllables were
never compared to anything:

- the choir's files carry **no lyrics at all**, so the second source cannot
  arbitrate a syllable;
- the check that was actually run was "does every note carry a syllable" — it
  accounted for 29 wordless notes as melisma-internal or chord second notes —
  and **that check cannot see a wrong syllable.** Bars 41 and 42 both carried
  one. They just carried the tenor's.

So the entry is now **◑**, with the reason spelled out, and the test that pins
the ✔ set names Agnus Dei as the one that came off it and why. Two movements
keep ✔: Lacrymosa and II·9b, both of which did have their words checked
against the source page at note resolution.

The next step is obvious and was started here and stopped: read the chorus
bass's lyric row off all five source pages the same way and compare it to the
file, syllable by syllable. It stalled on the thing the recipe already warns
about — **the staff count changes from system to system**. The soloists' a
cappella opening has two staves, the systems where the chorus rests have four
(two soloists plus piano), and the ones where it sings have six; and on page 4
the bottom system's vocal staves have no clef glyph in the text layer at all,
so "the fourth staff from the top" is not a rule that holds. Identifying the
chorus bass staff per system is the work, and it is worth its own sitting —
it would settle the words of the line the singer actually reads for a whole
movement.
