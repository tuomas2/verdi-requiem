*Part of the Verdi Requiem working notes — the index is [`CLAUDE.md`](../../CLAUDE.md).*

# The choir's own MuseScore practice files

2026-08-30: the user handed over a folder of 8 zip files, unzipped and sorted
by content into `01_requiem/` … `08_libera_me_2/` (they
had arrived named only by download order — one zip's folder actually held
five other movements' worth of zips). They live under **`.local/musescore/`**
since 2026-09-10, when the same 77 files came back onto the machine and were
sorted into the same eight folders by the number in each filename; earlier
notes and code comments say plain `musescore/` and mean this. One zip's
filenames were mangled
(`AIIyl<0x84>.mscz`); the bytes decode correctly as **cp850**, giving
`AIIylä.mscz` — `unzip`'s default cp437 guess is wrong for this batch.

**Per the user, these have correct notes and a correct piano reduction, but
no lyrics, and don't necessarily cover everything.** Confirmed independently:
zero `<Lyrics>` tags in any of the 8 whole-score files. Origin and authorship
are unknown — not yet asked, since the point right now was only to look, not
to act.

Each folder holds one `NN name.mscz` whole score plus, for most, an
`..._stemmapohja.mscz` and several per-voice exports (`... B1.mscz`,
`... B2.mscz`, one hand-named for a singer, e.g. `... B2_Lasse.mscz`). The
per-voice files carry the **full instrumentation**, identical part list to
the whole score — so whatever isolates the voice is a visibility/mute
setting inside the file, not a stripped-down score. That is the same idea
`harjoitus.py` uses (hidden-but-sounding staves), done by hand in the
MuseScore GUI, apparently independently. Not verified in detail — which
staves are actually hidden or muted was not checked.

**These are not full movements — they are the choir's own condensed,
chorus-only rehearsal cut**, each file concatenating only the passages
where the chorus itself sings and skipping solo-only stretches entirely.
That is not a guess: it falls out of comparing pitch sequences (see method
below).

| Choir file | Measures | What it is |
|---|---|---|
| `1 Requiem` | 127 | ≈ `01-Verdi_Requiem-kasin.mxl` (140 measures) — same movement, not yet clear why the count differs; content matches closely (see below) |
| `2 Dies irae` | 177 | `02` (Dies irae) + `03` (Tuba mirum) + `05` (Liber scriptus) concatenated, skipping `04` (Mors stupebit — solo bass, no chorus) |
| `3 Rex tremendae` | 64 | ≈ `07-Verdi-Rex.mxl` (62 measures) alone |
| `4 Dies irae 2` | 96 | `10b` (Dies irae kertaus, all 51 measures) run into the opening of `11` (Lacrymosa) — the chorus's next entrance after Recordare/Ingemisco/Confutatis, all solo-only and skipped |
| `5 Sanctus` | 136 | ≈ `13-Verdi-Sanctus.mxl` (139 measures) — measure counts close, pitch not checked |
| `6 Agnus Dei` | 44 | Same tune as `14` (74 measures, OMR), but shorter — see below |
| `7 Libera me` + `8 Libera me 2` | 137 + 239 = 376 | `16-Libera_Me.mxl` (421 measures) split into two rehearsal halves — confirmed, see below |

## Method: pitch-sequence matching, no lyrics needed

Since neither side has reliable lyrics in the relevant spots, movements were
identified and compared by extracting each file's chorus-bass line as a bare
pitch sequence (step+alter+octave per note, chord tones and durations
ignored, rests kept as a placeholder) and running `difflib.SequenceMatcher`
between candidates. The choir files were read via `mscore -o out.musicxml`
(add `-f` for `1_requiem` and `8_libera_me_2` — both hit the documented
"aborts without `-f`" CLI behaviour; `1_requiem` then still exits 134 at
teardown the way `mscore` always nondeterministically does, but the
`.musicxml` it writes first is complete and parses fine — same "check the
output, not the exit code" rule as everywhere else in this file).

The choir's "Bass 1" staff is the one that lines up with this project's
`Kuoro B`; "Bass 2", where present, was empty rests in every file checked —
a placeholder row, not a second real line.

### Three corrections to the method, 2026-09-10

Run voice by voice rather than only on the bass, the naive version produces
more false alarms than findings. Each of these produced one before it was
handled, and each is cheap:

- **Compare semitones, not spellings.** Our sources write `Aes3` where the
  choir file writes `Gis3`. Map each token to a MIDI number first; movement
  I's tenor alone had two differences that were nothing but this.
- **Filter to voice 1 and fold chord tones into the preceding token.** A
  divisi second voice looks like a run of extra notes, and a chord member
  looks like a *wrong* note — the most alarming possible false positive.
  Movement 07's soprano, alto and bass each showed four to six of these.
  Where our staff carries three voices (movement 07's tenor, against the
  choir's Tenor 1–3), compare the top note only.
- **Shift the tenor an octave.** Our chorus tenor is written an octave above
  the choir file's. Movement I's tenor scores 0.109 unshifted and 0.934
  shifted.

And the standing rule, restated because it decided what could *not* be
concluded on 2026-09-10: **never quote a bar number that came out of an
alignment against these files.** In movement I the bars correspond exactly up
to 78 and then stop — our bar 95 sits against their 97 — so every difference
the aligner reported from bar 79 on is noise, and the Kyrie stays unverified
until someone establishes the mapping the way *2026-09-03 (c)* did for
Lacrymosa.

### When the two sources disagree

Often, and not always in the choir file's favour. Of fourteen differences in
movement I's bars 1–78, seven notes were our OMR's key-signature damage, two
were real defects in our file, and **eight were the choir file's own
readings**, each contradicted by the printed page. The arbiter is the source
PDF read as text — see the recipe skill, *Reading a single notehead off the
page* — where the movement has a source PDF at all. Movements 02, 03, 05, 07,
11, 13 and 16 do not, so there a disagreement can only be settled by what the
other staves and the piano are doing on that beat.

And where neither works, there is the book. II·9b bar 607 was the first note
decided that way (*2026-09-10 (c)*): its source PDF's accidentals are
unreadable, the harmony was ambiguous, and the singer read the printed page in
one glance — **G♭, the choir file's reading, not ours**. That is the first time
the choir file has been shown right at a named note that could not be settled
any other way, and it is worth remembering when weighing the eight times it was
shown wrong in movement I: these files are a real second source, not a
tiebreaker to be overruled by default.

## What the matching actually found

- **Movement 1: 95 % pitch match**, project's `01` `Kuoro B` (P16, 287 notes)
  against the choir's `Bass 1` (275 notes). The differences are specific and
  actionable, not noise:
  - ~~**Measures 79–93 are bare rests in `01-Verdi_Requiem-kasin.mxl`'s
    chorus bass, with real notes in the choir file at the same spot**~~ —
    **retracted 2026-09-02, this was a false alarm.** Page 5 of
    `01-Verdi_Requiem.pdf` shows those bars given to the four *soloists*
    ("Soprano" / "Tenor" / "Bass" cues printed over their staves); the four
    chorus staves are tacet and enter at bar 94, which is exactly what our
    file has. The bar numbers in this comparison came from a `difflib`
    alignment of two files of different lengths (127 vs. 140 bars) and are
    approximate — treat them as "somewhere near", never as bar numbers.
  - ~~Four smaller single-note mismatches worth a manual check~~ — **all four
    resolved 2026-09-10**, and none of them was a defect in our file. Bars 35
    (`B3`/`Bb3`) and 52 (`C3`/`B2`) were measured off the printed page, which
    prints a natural in the first and `Bb2 C3 C3 C#3` in the second: ours,
    twice. The two around 116 and 124–126 were the comparison folding a
    divisi chord into one token, not disagreements at all.
  - The 13-measure count difference (127 vs. 140) is not explained yet.
- **Rex tremendae: 95.2 % match** against `07-Verdi-Rex.mxl` alone — this one
  isn't an OMR movement, so it mainly validates the method and the "Bass 1 =
  Kuoro B" identification rather than finding anything new.
- **`4 Dies irae 2` contains `10b`'s content almost entirely** (ratio 0.51
  against a theoretical max of 0.53 for a 94-note sequence fully contained in
  a 259-note one), then continues into material matching `11-Verdi_Lacrymosa`
  (0.75 against the *whole* 207-note Lacrymosa bass, not just its opening).
  **This is a second, independently-made source for `II·9b`** — currently
  the only note source for that movement is a single unproofread OMR pass —
  and it may carry exactly the kind of choir-book measure anchor that *Open
  assumptions* and *The missing Dies irae recall* say is still missing.
- **Agnus Dei: same tune, but the choir file is shorter** (44 vs. 74
  measures, 111 vs. 199 bass notes) than `14`'s OMR. Partly explained: `14`'s
  chorus bass rests for its first 13 measures (the soprano/mezzo-solo a
  cappella opening, per the `MAPPING` comment for that file) while the choir
  file only has 3 measures of lead-in rest — consistent with the same
  "chorus-only cut" pattern seen elsewhere. That accounts for maybe 10
  measures of the 30-measure gap; the rest is not yet localised.
- **`7 Libera me` + `8 Libera me 2`, concatenated in that order, match
  `16-Libera_Me.mxl`'s chorus bass at 96.4 %** — strong confirmation this
  pair is simply the whole movement split into two rehearsal halves, and,
  unlike the others above, mainly a validation that `16` is already sound
  rather than a source of new fixes.
- `2 Dies irae` was identified (`02`+`03`+`05` concatenated, ratio 0.88) but
  not compared note-by-note the way movement 1 was — none of `02`, `03`, `05`
  are OMR movements, so there's less at stake there.

## Thoughts on how this could be used — not started

1. ~~Highest value, most concrete: use the choir's `Bass 1` line to fill
   `01`'s measures 79–93~~ — there is nothing to fill, see the retraction
   above, and the four flagged single-note spots are resolved (2026-09-10,
   above). What remains in movement I is the **Kyrie**, bars 79–140, where the
   two files' bars do not correspond.
2. Use `4 Dies irae 2` to cross-check `II·9b`'s currently-unproofread notes,
   and possibly to help pin down its position relative to Confutatis/
   Lacrymosa (the *Open: which measure numbers* question) — it's chorus-book
   material, which is exactly the kind of anchor that's been missing.
3. ~~Before trusting Agnus Dei for anything, work out the rest of that
   30-measure gap~~ — **done, and it was harmless**: all 30 bars are
   solo-passage trimming, accounted for span by span in *2026-08-31 (later)*.
   The original note, for context: it might be more solo-passage trimming
   (harmless) or it
   might be a real content difference.
4. ~~Same pitch-matching method, systematically, for the S/A/T lines too~~ —
   **done for movements 01 and 07 on 2026-09-10**, which found and fixed the
   soprano's and alto's wrong key in movement I and one octave error in
   movement 07's tenor. Movements 14 and II·9b have been run but not yet
   adjudicated: II·9b reports five candidates, four of them a G against a G♭.
   `02_dies_irae`, `05_sanctus`, `07_libera_me` and `08_libera_me_2` have not
   been run voice by voice at all.
5. This comparison used pitch only, no rhythm — good enough to identify a
   passage and spot wrong notes, not a substitute for a real duration-aware
   proofreading pass.
6. Worth asking the user at some point who made these files and whether
   there's a canonical/most current copy, before leaning on them for fixes.
