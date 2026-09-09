*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-08-31: three more chorus-bass spots the user flagged by ear

The user, singing along, flagged three specific spots as sounding wrong.
Method for all three: pitch/rhythm-match the project's `Kuoro B` (and, where
relevant, the other voices) against the choir's own MuseScore files
(`musescore/`, see below — converted to MusicXML with `mscore -o x.musicxml
file.mscz`) using the same `difflib.SequenceMatcher` approach as the
MuseScore-comparison work, then, where a source PDF exists, confirm visually
by rendering pages (`mutool draw -r 250`) rather than trusting pitch-matching
alone — same discipline as the Lacrymosa fix above.

## Fixed: Lacrymosa bar 669, "eis requiem" was the soloists' line, not the chorus's

`11-Verdi_Lacrymosa.mxl`, `Kuoro B` (`P8`), continuous bars 669–674 (local
46–51) — exactly the six bars the original Lacrymosa fix (above) had
*added* from OMR to replace bare rests. Turned out that addition was wrong:
those six bars' notes and lyrics ("e-is re-qui-em, pi-e Je-su Do-mi-ne,")
are pitch-for-pitch, syllable-for-syllable identical to `Solisti B` (`P4`) at
the same bars — i.e. the earlier fix copied the **soloist's** line into the
chorus stave. Confirmed two independent ways: `musescore/04_dies_irae_2`'s
chorus `Bass 1`/`Bass 2` are both bare rests for the whole span (zero
counterpart — a pure insertion with nothing to match), and
`Verdi_Lacymosa.pdf` pages 9–10 show, rendered, that only the vocal-quartet
soloists sing "eis requiem, pie Jesu Domine, dona eis, dona" here — the
chorus staves are tacet and re-enter only on "Pi-e Je-su Do-mi-ne" a few
bars later (already correct in our file, ~bar 677, matching the user's own
"from 677 on it looks right"; they said 682, in the numbering of the day).
**Fixed**: bars 46–51 replaced with plain
whole-bar rests, matching what was there before the original fix. Verified:
file converts and exports MIDI cleanly; merged score's `Kuoro B` count drops
by exactly 18 (the notes that were removed).

~~Still open: the divisi `P9` at bars 54–56~~ — **fixed 2026-09-03**, and the
reasoning below about why it looked hard was the thing that was wrong. `P9`
carried the leftover "Lacrymosa dies illa..." duplicate text (the same bug
class as the original fix, just never scrubbed from the divisi part). Its
*notes* are confirmed correct (they match the choir's own `Bass 1` closely —
note the two parts' PDF/MuseScore roles cross momentarily here: generally
`P8`↔Bass 1 and `P9`↔Bass 2 by pitch-match ratio over the whole movement, but
at this one spot `P8` sits on what the choir file calls `Bass 2` and `P9` on
`Bass 1` — a real voice-crossing, not a bug).

The note said the fix needed "a proper syllable placement, not a blind copy",
because `P9`'s rhythm (5+4+1 notes) doesn't map onto `P8`'s "Pi-e Je-su"
(2+2+1). **That was the wrong comparison.** `P9` does not sing `P8`'s text: the
source page prints a *separate* lyric row for it, above the staff, reading
"Pi-e Je-su Do-mi-ne," — seven syllables, which map 1:1 onto exactly the seven
notes that carried the wrong text. Checked against the page's own x
coordinates, not guessed. See *2026-09-03 (c)*.

## Fixed: Agnus Dei bars 27–58, OMR read the wrong staff every time the chorus drops out

`14-Verdi_requiem_agnus-dei-OMR-korjattu.mxl`, `Kuoro B` (`P4`). The user
first flagged bar 27 (spurious treble clef); checking further, the same bug
recurs at bar 46, and a related content gap runs through bar 58 — the whole
back half of the movement needed the same treatment.

The piece's structure (confirmed by rendering
`14-Verdi_requiem_agnus-dei.pdf` pages 2–4 directly, and cross-checked
against `musescore/06_agnus_dei`'s independently-made chorus `Bass 1`/
`Bass 2`, which are silent across the same spans): "Agnus Dei... qui tollis
peccata mundi, dona" is stated three times, alternating soloists-only
(S + M-S, no chorus staff printed at all) with full chorus. Bars 1–13
(soloists) were already known and handled in `MAPPING`. The other two
soloist-only stretches were not: **bars 27–35** and **bars 46–58**. OMR
didn't know either was soloists-only: it inserted a spurious `<clef>`
(treble G-2, no `clef-octave-change`, part is otherwise bass clef
throughout) at the start of each — bar 27 and bar 46 — and filled the bars
with notes a fourth-to-sixth too high.

One more wrinkle at the first chorus-tacet boundary: bars 36–39, right after
the clef nominally reverts to F-4 at bar 40, turned out to be **also**
fabricated — not a register error this time, but OMR mechanically copying
the `Kuoro T` line down an octave into `Kuoro B`. Both staves *look*
plausible in isolation (same rhythm, correctly hyphenated Latin, matching
octave-parallel motion — the kind of thing that's easy to wave through), but
rendering `14-Verdi_requiem_agnus-dei.pdf` page 3 at 400 dpi and cropping
just the clef of that system settled it: **both** of the two staves printed
there are treble clef, i.e. two tenor-range voices (`Kuoro S`/`Kuoro A` are
independently confirmed resting there too) — there is no bass-clef staff
in the source at bars 36–39 at all. `Kuoro B` doesn't enter for real until
bar 40.

**Fixed**: bars 27–39 and 46–58 all replaced with plain whole-bar rests
(clef elements removed, `<print>` system-layout kept where present — that's
real page-layout data, not the bug). Bars 40–41, previously *entirely
contentless* (`<measure>` with no note at all — a separate, older OMR gap
that `yhdista.py`'s `ensure_filled` was silently papering over with a rest
during the merge, so it never surfaced as an error) were filled with the two
plain whole notes (C3, C3) that `musescore/06_agnus_dei`'s chorus `Bass 1`
has at exactly that point, immediately before the already-correct bar 42 —
lyrics "Do-"/"na," fitted from the untouched `Kuoro S` part's phrasing at the
equivalent spot. Bar 42's first note was also missing its lyric entirely
(bar 43 already started mid-word, `syllabic="end"` on "na", with no "do"
anywhere before it) — added as `begin:"do"`. Verified: converts cleanly
(`mscore`, 6 pages, exit 0), rendered pages show the bass staff correctly
silent for both tacet stretches while the solo staves continue, and correct
again from bar 40; merged score's `Kuoro B` count changed from 1861 to 1795
(22 fabricated notes removed at 36–39, more at 46–58, 2 real notes added at
40–41 — `ensure_filled`'s "empty measures patched" count dropped from 28 to
26, exactly matching the two bars that got real content instead).

**Bars 59–74 — SUPERSEDED, see the next section.** The paragraph below is
kept because its diagnosis of *why the manual attempt failed* is still
correct and worth not repeating; its conclusion ("needs a re-OMR") turned out
to be wrong. The passage was settled the same day without re-OMR, by
comparing against the choir file instead of reading pixels.

**Still not fixed — bars 59–74 (rest of the movement):** the same class of
problem continues, but attempts to nail it down by reading the PDF pixel by
pixel (even cropped at 400 dpi, isolating just the bass-clef staff's own
text row per system) produced **inconsistent bar-boundary reads on repeat
attempts** — a rare admission-worthy point, but real: two crops of the same
passage were read as starting on different words. Worse, `Kuoro S`/`Kuoro
A`/`Kuoro T` — otherwise the reliable anchors used everywhere else in this
fix — themselves show unexplained rests and zero-content measures in this
same stretch (bars 65–74 especially, including the identical "entirely
contentless measure" bug at 72 in *three* parts, not just bass). That's a
different, probably wider OMR failure than the "wrong staff read at a
solo/tutti boundary" pattern diagnosed above, and guessing at a fix here —
across four voices, without a reliable independent source for any of
them — would be exactly the kind of pixel-eyeballing this project's own
rules warn against. `musescore/06_agnus_dei`'s chorus `Bass 1`/`Bass 2` do
give a clean, confirmed 6-measure chunk of real notes (whole, whole, half+
half, ...) that structurally must map to somewhere around bars 59–64 — but
without a reliable bar-anchor at the far end, committing it to specific bar
numbers would be a guess. **Needs a proper re-OMR of this page range**
(`Audiveris -batch -transcribe -export` on a fresh 450 dpi rasterisation of
pages 4–5, same recipe as everywhere else in this file) rather than another
manual attempt.

## Open, unresolved: Liber scriptus ~bar 239, how many times does the bass sing "Dies irae"?

Continuous bar 239 falls at the end of `05-Verdi-Liber_scriptus.mxl` (local
bar 78/108, continuous 239–266) — the *first* of the piece's three "Dies
irae" theme returns (the other two are II·9b and the Confutatis→Lacrymosa
gap, both above). The user recalled the bass singing "Dies irae" six times
here (from the choir's own MuseScore file); the current text has it three
times (239–240, 258–260, 261–266) plus "Dies illa" twice (241–242, 256–257).

Pitch-matched **every voice** (S/A/T/B) against `musescore/02_dies_irae`'s
equivalent `Bass 1`/`Soprano 1` across the whole passage (continuous
234–266): **all four voices' notes match the choir source exactly**, note
for note — nothing is missing or extra. So this is purely a "which words
under which notes" question, not a notes problem, and MuseScore's own files
carry no lyrics at all, so they can't settle it further.

The one concrete lead: Alto/Tenor/Bass sing "Solvet saeclum in favilla"
*twice* (bars 247–250 and 251... continuous 247–254, before "Teste David cum
Sybilla"), while Soprano, at the same bars, instead has extra "Dies irae,
dies illa" repeats and skips the second "solvet saeclum"/"teste David"
entirely. Soprano's own notes there are independently confirmed correct
(matched the choir source too) — so it's a real, different melodic line, not
corruption — but the *text* disagreement between Soprano and A/T/B is
unresolved. **Needs the physical rehearsal score**, bars 247–254 (Liber
scriptus local 86–93), checked against both readings above.
