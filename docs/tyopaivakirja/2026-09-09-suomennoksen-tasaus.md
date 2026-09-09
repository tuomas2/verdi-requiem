*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-09 (c): the gloss starts where the syllable starts

The singer read the new Finnish gloss row (*2026-09-09*) and asked one
question: can the Finnish word **start** at the same place as the Latin
syllable instead of being centred on it? It can. It took one measured
constant, one measured character table, and one MuseScore rule nobody had
written down.

The complaint is real and it is worst exactly where the gloss matters most.
MuseScore centres every syllable on its notehead, gloss included, and the
Finnish word is almost always the longer of the two — so `loistakoon` under
`lu-` of *lu-ce-at* began **10,6 pt to the left of its own syllable**, under
the previous word, and the reader had to guess which Latin word it belonged
to. Median offset over the whole bass part: 4,1 pt.

## Three ways that do not work, each killed by a render

- **`<lyric justify="left">`** — MusicXML has the attribute; MuseScore's
  importer ignores it. Measured: the syllable landed within 0,2 pt of where
  it lands with no attribute at all.
- **`<lyric default-x>`** — ignored the same way.
- **`lyricsEvenAlign` / `lyricsOddAlign` set to `left`** — this one *works*,
  which is worth recording because *2026-09-09* concluded from
  `lyricsEvenFontSize` that the even/odd style keys do nothing. They are not
  uniformly dead: alignment obeys, font size does not. It was still rejected,
  for two reasons. It anchors the text at the **notehead's left edge**, not
  at the syllable's, so a wide syllable still starts 3–7 pt further left. And
  the gloss's row number is not fixed — `sanarivi` gives it one more than the
  measure already uses — so an odd/even rule would hit the Latin row wherever
  the gloss lands on row 3.

What works is `<lyric relative-x>`. **Its unit is 0,2835 pt = 0,1 mm**, not a
staff space as MusicXML's name "tenths" suggests; measured at 10 and 20 both
in a four-note test file and in the finished part, and identical in both.

## Reading Edwin's character widths without the font file

The shift is `(where the gloss's left edge is) − (where the syllable's is)`,
so both texts have to be measured. MuseScore keeps Edwin inside its own
resources — there is no font file on disk, `fc-list` finds nothing, and the
machine has neither fontTools nor PIL — and the only copies available are
subsets embedded in the PDFs themselves.

The way around it is to let MuseScore do the measuring. The calibration score
puts one string per system and prints it **twice**: the upper row at the
Latin size, the lower at the gloss size. Both are centred on the same
notehead, so the difference of their left edges is the centring distance
scaled by the size ratio, and one line of arithmetic gives it at either size:

    L(10,02 pt) = (x_alarivi − x_ylärivi) / (1 − 6,48/10,02)

No font parsing, no notehead position, no absolute origin — only a difference
of two numbers read out of `mutool draw -F stext`. Two details had to be right:

- **The rendered sizes are 10,02 pt and 6,48 pt**, not the 10 and 6,5 that
  were asked for.
- **Per-character advances come from `nXn`, not from `XX`.** `ff` is a
  ligature in Edwin, and the doubled-letter method therefore gave `f` an
  advance of 2,88 pt instead of 3,23 — a 0,85 pt error in every word starting
  with an f. The check that caught it was predicting `offerimus` and `of` from
  the table and comparing against their own measurement.

The result is `suomennos.LEVEYDET`, 106 characters as (advance, left side
bearing). It is a measurement, not a font dump: if a new character turns up
in a lyric, a test fails and says to measure it rather than guess it.

## The rule MuseScore actually uses

Centring is not on the whole string. **Leading and trailing non-letters are
excluded from the centred part but still drawn.** Measured:

| string | centring distance | what it means |
|---|---|---|
| `nam` | 10,28 pt | |
| `nam,` | 10,30 pt | the comma is not centred |
| `nam.` `nam;` `nam!` `nam-` | 10,30 pt | nor is any of these |
| `na,m` | 11,72 pt | a comma *inside* the word is |
| `,nam` | 13,09 pt | centred as `nam`, then pushed right by a comma |

Without that rule every syllable ending in a comma — and the parts are full
of them — would sit 1,4 pt out. `keskitys()` implements it directly, and it
also handles the glossary's own leading hyphens (`in` → `-ssa`).

## What it bought, measured on the part the singer reads

487 gloss/syllable pairs in `stemma-basso-1.pdf` could be matched between the
old and the new render (the pages whose system breaks moved are excluded, so
that both sides describe the same layout):

| | before | after |
|---|---|---|
| median distance between the two left edges | 4,08 pt | **0,23 pt** |
| mean | 5,04 pt | 0,74 pt |
| within 0,5 pt | 6,6 % | **76,2 %** |

## The residual is MuseScore's, not the arithmetic's

About one gloss in twenty is still 3–7 pt out, and it is not the model: in
those places **MuseScore has moved the Latin syllable off its notehead**. At
bar 43 of movement I the gloss `minun` sits on the notehead's centre to
0,04 pt, and the syllable `me` sits 3,55 pt to the right of it — its left edge
exactly on the notehead's left edge. It is not the dash, not the melisma and
not the barline: a test file reproducing the same syllables, the same
`syllabic` chain and the same bar boundary centres them normally. It only
happens under the real part's spacing, which is not known until the layout
runs, so it cannot be predicted at build time. Left alone and written down.

Elisions are left centred too — one `<lyric>` holding two syllables with
MuseScore's own connector between them, whose width has not been measured.
There are five in the whole score, and a test asserts that they are the only
ones the alignment skips.

## The cost is one page, and not in a bass part

Shifting a gloss right widens what it occupies on its right, so MuseScore
spaces the notes a little further apart. Built with and without the shift,
everything else identical:

    S I 18   S II 17   A I 16   A II 16   T I 17   T II 17→18   B I 16   B II 16

`Tenori II` gains a page; the seven others do not, and both bass parts stay at
16. `stemmat-sisallys.txt` and the site were regenerated for it.

## Verification

- 283 tests (272 before, +11). Eleven are new: the shift's definition (the
  two left edges coincide by construction), the punctuation rule, the
  elision case, the unknown-character case, and two whole-score invariants —
  every character in every syllable and every glossary entry has a measured
  width, and the only glosses left centred are the elisions.
- All eight parts and the merged score convert without `-f`.
- The before/after comparison above is the check the change was made for, and
  it was done at note resolution rather than by looking at a page.
