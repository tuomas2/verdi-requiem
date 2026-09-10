*Part of the Verdi Requiem working notes — the index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-10 (d): movement I gets a piano, from the choir's own file

The user's question — "how easy would it be to copy the piano out of the choir
files?" — turned into the answer "easy in two movements, and here is one of
them done". Movement I now has a piano staff for the first time. Along the way:
one defect in the bass line the singer reads, one trap in `yhdista.py` that
cost an hour and is now guarded, and a mapping result that unblocks the
largest open item in movement I.

The user's own caveat shaped the whole design: **the choir's MuseScore files
are hand-made, so their consistency should not be assumed.** That is why every
grafted bar is checked rather than trusted, and why movement 10b was mapped
and then deliberately not copied.

## What movement I's missing piano actually was

Not missing — **rejected.** Audiveris produced 1912 notes for `P17`, and
`yhdista.py`'s `MAPPING` comment says why they are not used: MuseScore's engine
crashes on some of them (`Spanner::setTick2`, `ChordLayout::placeDots`) and
playback stopped dead at bar 81. Four patch attempts had been tried and all
made things worse (see [`docs/menetelmat/yhdistaminen.md`](../menetelmat/yhdistaminen.md)).

So the choir file is not filling a void, it is **replacing a known-bad part** —
and because the replacement is total, the crash-inducing content is not in the
file at all. That reframing is what made this worth doing: the risk of a wrong
note in a piano reduction is small next to the certainty of no piano.

## The bar mapping: align bars, not a note stream

The choir files are the choir's own condensed cut, so their bars do not
correspond to ours throughout. The method that worked, and which is now
written up in [`docs/menetelmat/kuorotiedostot.md`](../menetelmat/kuorotiedostot.md):

**A bar's signature is all four chorus voices' content in semitones.** Two bars
correspond only if all four voices agree, so the mapping checks itself. This is
the direct answer to the standing rule in this project — *never quote a bar
number that came out of a `difflib` alignment* — because these numbers do not
come out of an alignment's approximate middle, they come out of four
independent agreements.

Two details each produced a wrong answer first, and both are worth knowing:

- **Rests must come out of the signature.** The same empty bar is one whole
  rest on one side and two half rests on the other. With rests in, movement I's
  bars 15–65 were reported as *not* corresponding — the opposite of what this
  file already knew about them.
- **Then empty bars must come out of the alignment.** With rests dropped, an
  empty bar's signature is `((),(),(),())` and matches any other empty bar.
  That is what aligned movement 10b's tacet tail against Lacrymosa's opening
  on the first attempt: the tool built to avoid the trap walked into it.

Where the chorus is silent, **the piano is the anchor.** Our OMR piano is wrong
here and there but it identifies a bar: the Jaccard overlap of the two pianos'
pitch sets runs 0.86–0.92 inside a block and collapses to 0.00 one bar past its
edge. That is how movement 10b's boundary was pinned to bar 40 exactly, where
the chorus-only method had said 39.

And the structural key, which removed the last guesswork: **the choir files
mark every splice with an empty piano bar.** Segmenting on those gives the
blocks with no thresholds at all.

| Movement | Mapping | Coverage |
|---|---|---|
| 01 | ours 1–78 ↔ theirs 1–78; ours 91–138 ↔ theirs 80–127 (**+11**) | 126/140 |
| 10b | ours 1–40 ↔ theirs 1–40 | 40/51 |
| 14 | ours 14–26 ↔ 4–16 (+10); 37–45 ↔ 18–26 (+19); 56–72 ↔ 28–44 (+28) | 39/74 |

Movement 01's +11 is the soloists' passage the choir cut (our bars 79–89).
**Bars 29–55 are empty in both files** — the piano simply does not play in the
chorus's a cappella stretch — so they are not a gap. The real gaps are our
79–90 and 139–140, fourteen bars, which stay rests.

Movement 14's middle block looked too weakly anchored to use (two matching
chorus bars), and the chorus settled it anyway: our 37–39 are tacet in soprano,
alto and bass on both sides and 40–45 match note for note, so the block's
position is forced. Our chorus **tenor** has content in 37–39 where the choir
file has rests, and it is a duplicate of a figure belonging elsewhere — one
more instance of the fabricated content that movement's S/A/T is known for.

## Why 10b was mapped and then not copied

Because the user's caveat deserved a measurement rather than a nod. Each bar
was compared not only as-is but also at **±12 semitones**, so a systematic
register disagreement could not hide:

| Movement | Same | Close | **Octave apart** | Other |
|---|---|---|---|---|
| 01 | 63 | 27 | **0** | 7 |
| 10b | 17 | 8 | **6** | 9 |
| 14 | 25 | 7 | **1** | 4 |

Movement 01 has no register disagreement anywhere — which is exactly the
reassurance needed to take a hand-made source wholesale. **Movement 10b has
six**, and five of them are the right hand of the opening descending figure.
Our source is an OMR of a printed edition and the choir file is hand-entered;
nothing in either says which octave the reduction belongs in. That is one
question for someone with a score, not six problems, and it is in `TODO.md`.
Its bars 6–8 are a different matter and not a matter of taste: our piano has 3,
1 and 1 notes where the choir file has 8, 8 and 7.

## The trap: `divisions` is read from one part and used for all

With the graft in, `mscore` began refusing the **whole score** without `-f`,
deterministically, saying only "corrupted" and naming no bar. Bisecting the
graft found that the very first choir bar was enough to trigger it, which
pointed at structure rather than content.

`measure_meta` reads `divisions` from **one reference part** — the one with the
most measures — and that single value is used for every target row of the
movement. The choir piano uses 12 and movement I's voices use 4, so the whole
bar rests `yhdista.py` generates for the piano row came out **16 long in a bar
that is 48 long**. Legal-looking XML, silently wrong, and fatal three steps
later.

Three things came out of it:

- `kuoropiano.py` **normalises the whole movement file to one `divisions`** —
  the LCM of everything declared, so the rescale is always integral (movement
  01: 4 and 12 → 12, factors 3 and 1). This also removes a pre-existing oddity,
  since movement 01 had been mixing 4 and 12.
- `yhdista.py` gained **`tarkista_jaotus`**, which reports the mismatch. It
  reports rather than crashes, and that was not the first design: as an
  assertion it immediately stopped the build on **ten** source parts that have
  had the same mismatch for as long as the merge has existed (movement 08's
  `P3`, Lacrymosa's `P2`/`P9`/`P10`, and six more) without ever causing harm.
  The mismatch only bites where the merger has to synthesise content into that
  very bar.
- `yhdista.py` also gained **`tarkista_mitat`**, which walks every finished
  measure with a cursor and reports any whose extent does not match its own
  declared divisions and time signature. That is the check that would have
  named the bar in one line. It reports **552** wrong-length bars in the
  finished score, all pre-existing, all tolerated by MuseScore — so it prints a
  summary rather than a list, and a test pins movement I's piano at zero.

**Sum durations with a cursor, not per voice.** The first version of the
per-bar check added up each voice's durations and required the bar length,
which rejected the choir file's perfectly good bar 12 — a voice there enters on
beat 2 from behind a `<forward>`, so its notes sum to 36 in a 48-long bar. The
right walk follows `<backup>` and `<forward>` and takes the maximum position
reached. The same mistake is easy to make twice, so it is in both docstrings.

## Found on the way: movement I bar 40 is half a bar long

The chorus bass's bar 40 held one half note, `B♭3` on "ex", and nothing else —
2/4 of a 4/4 bar. The choir file has **a half rest and then the `B♭3`**, and
the chorus tenor's own "ex" is on beat 4 of bar 39, so a staggered entry is
what the music does. On the page the harm was small, because MuseScore lays a
lone note out near where it belongs and simply draws no rest. In the practice
`.mscz` the note **sounded two beats early**.

This sat inside the stretch this file calls verified, and it is not a
contradiction but a gap in what was verified: bars 1–78 were compared **pitch
by pitch**, and a missing rest changes no pitch. "The notes match" and "the bar
is right" are different claims.

Fixing it needed a new `korjaa_kasin.py` operation, `lisaa_tauko`, which
inserts a rest before a named note. It is the only operation that
*deliberately* changes a bar's length, so the row states the expected total and
the operation checks it:

    ("40", 0, "lisaa_tauko", "8/half", "16"),

## And a by-product bigger than the piano: the Kyrie is unblocked

`CLAUDE.md` has listed movement I's Kyrie (bars 79–140) as unverifiable because
the two files "stop corresponding around bar 94". They do not: they correspond
perfectly at **+11** from our bar 91, and the break at 79 is the soloists'
passage. At that offset the Kyrie leaves **13 candidate bars** — 96, 103, 105,
115–118, 120–121, 123–126 — and the other 32 match in all four voices. Those 13
were previously indistinguishable from noise. This is desk work against two
files, not a question for the rehearsal book.

## Verification

- **398 tests** (372 before). New: `testit/test_kuoropiano.py` (20) covering
  the cursor walk, the divisions normalisation, the empty-bar template and the
  whole-file mapping with its boundaries; `Jaotusansa` and `OsanIPiano` in
  `test_yhdista.py` pinning both new checks and movement I's piano at zero
  wrong-length bars; four in `test_korjaa_kasin.py` for `lisaa_tauko`,
  including that a wrong expected total crashes.
- **Per-staff note counts**: chorus 1842 / 1810 / 1908 / 1813 unchanged, piano
  **22312 → 23932**, and the difference is exactly the choir piano's 1620
  notes. Nothing else moved.
- **The merged score's piano compared bar by bar against
  `lahteet/01-kuoropiano.musicxml`**: all 126 mapped bars identical in pitch
  content, and all 14 gap bars rests. This is what settled that the pipeline's
  own rest-type repairs (`fix_rest_overflow`, 6 bars) change notation and not
  content — the `repaired` counter had jumped by 93 while the divisions bug was
  live and settled at **+6** once it was fixed.
- `mscore` converts the full score **without `-f`**, twice in a row, **397**
  pages against 390 — the seven new pages are movement I's piano staff.
- **MIDI export**: the Piano track now runs the full length of the score,
  the same as the vocal tracks. Before the choir's piano it stopped at bar 81.
  That is this project's documented way to check playback, and it is the one
  that matters for the practice files.
- All eight reading parts rebuilt (they carry no piano, but movement I's
  durations changed unit): page counts **18/17/16/16/17/17/16/16**, unchanged,
  and `stemmat-sisallys.txt` unchanged. All eight practice `.mscz` rebuilt —
  those *do* carry the piano, which is the point.
- Bar 40 read back off the rendered PDF at 450 dpi: half rest, then the `B♭3`
  with "ex" under it.
- The seven `-kasin.mxl` files this session does not touch came back
  **byte-identical as extracted XML**.
