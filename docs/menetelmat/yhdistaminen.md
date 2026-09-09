*Part of the Verdi Requiem working notes — the index is [`CLAUDE.md`](../../CLAUDE.md).*

# Merging the 16 movements, and the eight reading parts

What `yhdista.py` had to learn to turn 16 CPDL movement files into one score
and eight single-voice reading parts. Everything here was measured, and
several rules were tried and reverted — those are recorded too, because
repeating them is the expensive mistake.
## The eight choir parts

`yhdista.py --stemma "Basso I"` builds one singer's part; `--vain "Kuoro B"`
picks any staff verbatim. The eight are Sopraano/Altto/Tenori/Basso × I/II.

The I/II split is **not** a matter of taking the `Kuoro X II` staff: Verdi's
double choir exists only in the Sanctus. A Coro II singer reads the ordinary
line in the other fifteen movements. `SINGER_PARTS` encodes that as
(normal staff, Sanctus staff), and the pairs were verified to differ in the
Sanctus and nowhere else.

Staff names are hidden in these files with `print-object="no"` on
`<part-name>` and `<part-abbreviation>` — a label on every system wastes width
in a single-staff part, and dropping it saved a page or two per voice. The
MuseScore style keys for this do **not** work: both
`hideInstrumentNameIfOneInstrument` and `firstSystemInstNameVisibility` /
`subsequentSystemInstNameVisibility` were tried via `-S` and had no effect.
The part name goes in `<movement-title>` instead, as "Messa da Requiem · X";
MuseScore renders `<movement-title>` as the visible title and ignores
`<work-title>` when both are present.

## Merging: things that were learned the hard way

- **MuseScore does honour MusicXML `<measure number>`**, so per-movement
  numbering restarts need no section breaks. This was verified, not assumed.
- **Strip the sources' own `<print>` elements.** They carry the original page
  layout and make a single-staff part four times longer. (141 → 26 pages.)
- **Silent staves must repeat the reference part's time and key changes.**
  Otherwise rest durations change with nothing declaring why, MuseScore treats
  the measures as wrong-length, and multimeasure rests silently stop working.
- **Normalise lyric verse numbers.** Sources mix `1` and `part5verse1`; and a
  single stray syllable on verse 6 makes MuseScore reserve six lyric lines for
  a whole movement. (18 → 14 pages.)
- **`<note>` children have a required order.** `ET.SubElement` appends, which
  puts `<staff>` after `<lyric>` and produces hundreds of schema violations —
  use `set_note_child`.
- Validate against the schema when something is off:
  `xmllint --noout --schema musicxml.xsd score.xml`, with the two remote
  imports in the .xsd repointed to local copies.

## The "corrupted file" warning — fixed, but know why it existed

Sources 05 and 16 made MuseScore report "Voice too long" / "Incomplete
measure" and declare the file corrupt. Neither converts on its own without
`-f`. Their piano parts encode notes as a doubled note value at half the
duration, via `<time-modification>` with `normal-notes=1` and a power-of-two
`actual-notes`. The encoding is legal and the durations are correct, but
MuseScore computes measure fill from note *types* and ignores that factor.

`yhdista.py` now repairs this during the merge (`fix_halved_notes`,
`fix_rest_overflow`): where a voice overflows by MuseScore's type-based
reckoning while its durations fit the measure, the note types are rewritten to
match their durations and the modification is dropped. Roughly 1770 notes,
piano staves only. Sounding result is identical — verified by comparing note
counts per staff before and after.

The merged score and all eight parts now convert **without `-f`**.

Two rules were tried and reverted because they made things worse:
retyping rests in mixed note/rest groups without checking that the durations
fit (32 warnings became 100), and retyping any rest whose type disagrees with
its duration (99 warnings — that mismatch is legal in tuplets and odd meters).
The guard that matters is `implied > limit and actual <= limit`.

## Movement I has no piano — and why patching it is a trap

Playback stopped dead at measure 81 while the notes still displayed. The cause
was the Audiveris piano of movement 01 (`P17`): it contains measures whose
content does not match the time signature, and MuseScore's engine asserts on
them (`Spanner::setTick2`, `ChordLayout::placeDots`). Note that this is
*separate* from the corruption warning — the file loaded with zero warnings and
still would not play past bar 81.

`P17` is therefore commented out of `MAPPING`. Movement I plays with voices
only. Everything else, including movement 14's OMR piano, is fine. Verified by
exporting MIDI and measuring its length: 81 → 1699 measures.

Four patch attempts were tried and all made things worse; do not repeat them:

| Attempt | Result |
|---|---|
| Pad short measures with a trailing rest | Rest lands in the wrong voice/staff in two-staff piano measures; whole file failed to load |
| Same, restricted to single-voice measures | Created a 19/16 measure in a *vocal* part |
| Blank malformed piano measures entirely | Removing notes removed slur/wedge endings, leaving dangling spanners |
| Strip slurs and wedges from OMR movements | No effect on playback at all |

To restore the piano, clean `01-Verdi_Requiem.omr` in the Audiveris GUI, export
fresh, and re-add `"Piano": ["P17"]`.

**Check playback by exporting MIDI, not by opening the score.** A file can load
with no warnings and still stop playing:
`mscore -o x.mid score.mxl`, then measure the longest track in ticks.

## Open assumptions

These were chosen without the information needed to settle them. All are one
line to change in `yhdista.py`; see `YHDISTAMINEN.md` for how.

| Assumption | Why | How to settle |
|---|---|---|
| ~~Measure numbers restart in every movement~~ — **settled**: Dies irae (02–11, incl. II·9b) numbers 1–701 continuously; every other movement still restarts at 1 | The user confirmed the choir's rehearsal book numbers Dies irae continuously | Done — `NUMEROINTI_ALKAA_JOKA_OSASSA_YKKOSESTA = False`, and since 2026-09-02 the per-sub-movement start numbers are read from the book itself (`DIES_IRAE_ALUT`), not computed |
| ~~Confutatis→Lacrymosa gap (II·9b) is 51 measures, computed at 578–628~~ — **settled**: II·9b is at 573–623 and the Lacrymosa **file** starts at 624 (the book's Lacrymosa *heading* is at 621, three bars earlier, inside the 10b file) | Two independent PDFs print their own continuous numbers | Done — see *2026-09-02 (later)* and *2026-09-03 (c): Lacrymosa's three-bar shift* |
| Sanctus chorus bass = Bass I | User has the higher of the two; Bass I is higher (median G3 vs D3) | Bass I enters at m. 2, Bass II at m. 4 |
| Movement 05 soloist = mezzo | File says "Soprano solo" but Liber scriptus is the mezzo aria | Musicological, not a data question |
| Movements 12, 15 soloist order | Parts are unnamed; inferred from standard score order | Compare with any full score |

## Verification habit that caught real bugs

Compute expected note counts per target staff directly from `MAPPING` and the
source files, then compare against the merged output. Every row must match
exactly. This found two silent data-loss bugs that looked fine on the page.
Do not hand-add the numbers — an early hand sum was wrong.
