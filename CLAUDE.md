# Verdi Requiem — working notes

Verdi's *Messa da Requiem* in MusicXML, assembled from 16 separate movement
files into one score, plus per-voice reading parts for choir practice.

**The user is a Finnish-speaking chorus bass.** Reply in Finnish. `YHDISTAMINEN.md`
(the user-facing handover doc) is in Finnish; this file is the technical
background for future sessions.

## What the user actually wants

Read their own chorus line while the rest of the choir and the piano reduction
still play, and carry a PDF of their line on a Boox e-reader. That drives every
design decision: measure numbers must match the printed rehearsal score, and
the reading part must be dense.

## Where things stand

Done and verified: the merge, the eight reading parts, the chorus **lyrics**
of the two OMR movements, a practice `.mscz` per singer, and — new — a
previously **entirely missing** ~50-measure passage (the second "Dies irae"
recall, between Confutatis and Lacrymosa) found, OMR'd, and wired in as
movement "II·9b". Its chorus-bass lyrics are checked; everything else about
it is not. Also new: Dies irae's ten sub-movements plus II·9b now number
continuously (1–706) instead of each restarting at 1, matching how the
choir's rehearsal book numbers that section — see *Open assumptions*.

Open, roughly in the order a singer would feel them:

| Open | Where to read up |
|---|---|
| **Notes** of movements 01, 14 and II·9b are still unproofread | *OMR recipe*, *The missing Dies irae recall*; the lyrics pass did not touch notes |
| Movement 01's Kyrie (from bar 91) still drops syllables | *What is left* — the OMR lost notes there, so it is note work, not text work |
| Movement 14 is weak throughout — 25–81 % matched, 71 bass notes still wordless | same |
| II·9b: Soprano/Alto/Tenor lyrics unchecked; its exact position vs. the choir book is still 3–5 measures uncertain | *The missing Dies irae recall* |
| 13 lyric changes reported but deliberately not applied | `python3 korjaa_sanat.py --kuiva` lists them |
| Movement I has no piano | *Movement I has no piano* |
| Five assumptions made without the rehearsal score | *Open assumptions* |

## Layout of the directory

| Pattern | What it is |
|---|---|
| `01…16-*.mxl` | Source movements, numbered by position in the whole work |
| `01-*.pdf`, `14-*.pdf` | Source PDFs for the two movements that had no MusicXML |
| `Verdi_10bDies_irae.pdf` | Source PDF for II·9b, the missing "Dies irae" recall (see below) |
| `*.omr` | Audiveris projects, for manual correction |
| `*-OMR-korjattu.mxl` | OMR'd sections with their chorus lyrics fixed from the PDFs |
| `Verdi-Requiem-koko.mxl` | Merged score, 15 staves, 1807 measures |
| `stemma-*.mxl` / `.pdf` | Eight choir reading parts |
| `stemmat-sisallys.txt` | Where each movement starts in all eight |
| `yhdista.py` | The merge tool; mapping table at the top |
| `korjaa_sanat.py` | Fixes OMR lyric errors against the source PDFs |
| `harjoitus.py` | Builds a practice .mscz: own voice as trumpet, rest hidden |
| `harjoitus-*.mscz` | The result, one per singer |
| `test_korjaa_sanat.py` | Its tests: `python3 -m unittest test_korjaa_sanat` |
| `fix-mxl.py` | Repairs missing measures in Audiveris exports |
| `tiivistys.mss` | MuseScore style: multimeasure rests |

**The hyphen/underscore in source names encodes provenance, so do not
normalise it.** Among the `Verdi*` files, `Verdi-*` came from a Sibelius 7.5.1
export dated 2017-10-10 (movements 02–07, 13) and `Verdi_*` from a CPDL Finale
2014 + Dolet batch dated 2015-05-11 (08–12, 15). `16-Libera_Me.mxl` follows
neither convention but belongs to the Sibelius batch. All are CPDL editions.

Movements 01 (Requiem & Kyrie) and 14 (Agnus Dei) existed only as PDFs and were
produced by OMR — they are **less reliable than the other 14**. Their chorus
**lyrics are now corrected** from the PDFs by `korjaa_sanat.py`; see below for
what that does and does not fix. The **notes still need proofreading**.

`yhdista.py` reads the corrected files. Changing those filenames means editing
three places: `MOVEMENTS`, the `MAPPING` keys, and `OMR_SOURCES`.

## Environment

- **MuseScore 4.7.4**, x86_64 running under Rosetta. Its CLI aborts outright on
  any score that would raise an import warning in the GUI — where the GUI offers
  "Ignore", the CLI just fails and writes nothing. `-f` overrides that; the
  generated files no longer need it, but the raw sources 05 and 16 still do.
  MuseScore has no built-in OMR — "Import PDF" opens musescore.com in a browser.
- `mutool` (mupdf-tools) installed via Homebrew. Used for rasterising and for
  reading text out of PDFs. `poppler` is *not* installed.
- **The MuseScore CLI aborts at teardown, nondeterministically.** Roughly two
  runs in three exit 134 (SIGABRT) with `mutex lock failed` *after* writing a
  complete PDF. It predates this work — the same file converts with exit 0 on
  a retry, and files from earlier commits abort identically. Verify output by
  page count, not by exit status, and do not put `mscore` under `set -e`.
- Tesseract language data for Audiveris lives in
  `~/Library/Application Support/AudiverisLtd/audiveris/tessdata` (eng, ita, lat).
- **Audiveris itself is not installed** — it ran from a temporary directory that
  is gone. Reinstall from github.com/Audiveris/audiveris releases
  (macOS arm64 `.dmg`, ~85 MB, bundled JRE). The DMG's licence prompt cannot be
  answered from a script; either open it in Finder or convert it first:
  `hdiutil convert X.dmg -format UDTO -o X && hdiutil attach X.cdr`.

## OMR recipe (if movements 01/14 are ever redone)

Both source PDFs are vector, not scans — no bitmap images, embedded music
fonts. That is the best case for OMR.

    # movement 01 — engraved with Mozart software, PDFBox reads it fine
    Audiveris -batch -transcribe -export \
      -constant org.audiveris.omr.image.ImageLoading.pdfResolution=450 \
      -output DIR -- 01-Verdi_Requiem.pdf

    # movement 14 — MusiXTeX; Audiveris's PDFBox cannot read its Type1 fonts,
    # so the music glyphs never reach the raster. Pre-rasterise instead:
    mutool draw -r 450 -c gray -o p%02d.png 14-Verdi_requiem_agnus-dei.pdf
    for f in p*.png; do sips -s format tiff "$f" --out "${f%.png}.tif"; done
    tiffutil -cat p*.tif -out 14.tif
    Audiveris -batch -transcribe -export -output DIR -- 14.tif

Hard-won details:

- **450 dpi, not 300 or 600.** Default 300 gave an interline of 13 px, far below
  what Audiveris needs; 600 exceeded its 20 Mpx per-sheet cap and the sheets
  were discarded. 450 lands at ~20 px interline, its optimum.
- **Tesseract data must come from the `tessdata` repo, not `tessdata_fast`.**
  Audiveris uses the legacy engine; LSTM-only files fail with
  "Could not initialize TessBaseAPI languages: eng in legacy mode" and you get
  zero lyrics.
- **Do not pass `-force` on a fresh book** — Audiveris throws an NPE in
  `Enum.compareTo`. `-print` also crashes in iText.
- Run `fix-mxl.py` on every Audiveris export: it emits parts with unequal
  measure counts (one measure missing mid-part), which makes MuseScore refuse
  the file entirely.

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
| ~~Measure numbers restart in every movement~~ — **settled**: Dies irae (02–11, incl. II·9b) now numbers 1–706 continuously; every other movement still restarts at 1 | The user confirmed the choir's rehearsal book numbers Dies irae continuously | Done — `NUMEROINTI_ALKAA_JOKA_OSASSA_YKKOSESTA = False`, offsets computed mechanically from each sub-movement's own measure count (verified against the actual files, not hand-summed) |
| Confutatis→Lacrymosa gap (II·9b) is 51 measures, computed at 578–628 (Lacrymosa starts 629) | Mechanical cumulative count from source files' own measure counts. Three other sources disagree by up to 5 measures on where this gap sits (PDF's own printed numbers say 573–623/624; the choir book itself said 621) | Get the choir book's own start numbers for Tuba mirum, Recordare, Confutatis (partly done — see *The missing Dies irae recall*) to find which sub-movement's own bar count differs from the book, and localise the gap properly |
| Sanctus chorus bass = Bass I | User has the higher of the two; Bass I is higher (median G3 vs D3) | Bass I enters at m. 2, Bass II at m. 4 |
| Movement 05 soloist = mezzo | File says "Soprano solo" but Liber scriptus is the mezzo aria | Musicological, not a data question |
| Movements 12, 15 soloist order | Parts are unnamed; inferred from standard score order | Compare with any full score |

## Verification habit that caught real bugs

Compute expected note counts per target staff directly from `MAPPING` and the
source files, then compare against the merged output. Every row must match
exactly. This found two silent data-loss bugs that looked fine on the page.
Do not hand-add the numbers — an early hand sum was wrong.

## Fixing OMR lyrics from the source PDFs

`korjaa_sanat.py` rewrites the chorus lyrics of movements 01 and 14 to match
their source PDFs. `--kuiva` reports without writing. Output goes to
`*-OMR-korjattu.mxl`; the OMR originals are never touched, so the pass is
repeatable if the OMR is ever redone for the piano.

**Both source PDFs carry their lyrics as real text**, not as glyph images —
`mutool draw -F stext` extracts them. This is the fact the whole approach
rests on, and it holds for movement 14 too: Audiveris could not read its
Type1 fonts but `mutool` can.

Results: coverage 83–91 % per voice in movement 01, 25–81 % in movement 14.
314 changes written: 142 corrections to existing lyrics and 172 syllables
added to notes that carried none. 13 further changes were reported as
uncertain and deliberately not applied.
**The chorus bass of movement 01 — the line the user reads — is 91 % with
zero uncertain changes**, and reads correct Latin through bar 90.

### Details that took measurement to get right

- **Lyrics are separated from staff labels by font size**, not by content.
  `4 Soli` and `Tutti` are the same Times-Roman as the lyrics, two points
  larger. The size is derived from the data — the most common size for that
  font — rather than hardcoded.
- **Word spacing must be measured from the previous glyph's right edge**, not
  from its origin. Movement 14's MusiXTeX positions every letter separately,
  and an origin-to-origin threshold turns a wide letter into a space
  (`d o - n a` instead of `do-na`).
- **Hyphenation is decided by majority across rows.** The same per-glyph
  positioning puts a hyphen's x after the wrong letter in some rows:
  `peccata` comes out `pecc-a-ta` in four rows of ten and `pec-ca-ta` in the
  other six, so the majority settles it. Only whole words vote — a fragment
  at a system edge is part of a word and says nothing about the whole. A
  repeated hyphen (`Chri--ste`) is the engraver's extension line, not a
  second break, so repeats are ignored; counting them as a distinct
  hyphenation let the extension line win the vote by one.
- **A lyric line is read verse-major, not note-major.** Audiveris put the
  `sotto voce` marking on verse 2 *under* the real syllables, so note-major
  reading interleaved `SOITO` and `VOCE` into `Re-qui-em` and broke the
  sequence at the third syllable. Extra verses are a separate pass.
- **Row selection is a global optimum, not a greedy scan.** For each PDF row
  the plausible positions are enumerated, then dynamic programming picks the
  largest compatible set — rows in order, positions non-overlapping. Candidate
  positions come from a syllable index, so the whole search is ~3 s.
- **Deletions only between matches, and only for a syllable the PDF does not
  know.** At a window edge the evidence is missing: the slot may be the next
  row's first syllable. And a syllable that occurs in the PDF is a real
  syllable, so deleting it would mean the alignment had drifted.
- **Flagging is case-sensitive, matching is not.** `Is` -> `Je` looks
  uncertain only because lowercase `is` occurs in every other bar inside
  `e-is`; capitalised `Is` occurs nowhere, so it is a clear fix.
- **Uncertain changes are reported, not applied.** Where the old text is also
  a word the PDF knows, the change may be drift. Checked by hand, three of
  five were wrong — e.g. `Chri` -> `e` would have made `Chri-ste` into
  `e-ste`. So they are listed and left alone.

### Adding lyrics the OMR never read, by x position

Audiveris kept `default-x` on every note, `width` on every measure, and the
system margins in `<print>`, so a note's position along its system is
computable. The PDF gives each syllable's position. The two coordinate
systems are linearly related, so a syllable can be attached to the note it
sits above — and **melismas need no special handling**: a note with no
syllable above it simply gets none.

- **The scale is global, the offset is per system.** Fitting both from one
  system's few anchors gives a slope off by ~0.008, which over a system's
  width is a whole note's spacing — that is exactly how the first syllable
  `ad` of bars 50–56 got dropped. The scale (0.306 for movement 01) is a
  property of the page setup, so it is taken as the median across systems
  with at least six anchors; then one anchor fixes the offset.
- **A syllable is never displaced.** It goes to the note nearest its
  predicted position or nowhere. Letting it fall to a neighbouring free note
  produced duplicates: `ti-bi bi red-de-tur`, `o-ra-ra{1-o-nem`.
- **If the nearest note already carries a word the PDF knows, leave it**; if
  it carries something the PDF does not know, that is OMR junk and gets
  replaced.
- **A syllable already sitting on a neighbouring note is not added again.**
  The predicted note can be empty while the syllable is in place one note
  over; that produced `qui tol-tol-lis`. The neighbour is checked across
  system boundaries, since a row can begin with the previous system's last
  syllable.
- **The whole system is skipped unless the assignment is monotone and
  injective.** When a row has more syllables than the system has notes — the
  OMR dropped notes, not just lyrics — filling produced `e-le-le-son` and
  `Chri-i-e-i-ste`. Ambiguity is a reason to do nothing.
- **The right row for a system is found by projection, not by index.** Every
  candidate row is fitted against the system's existing lyrics; the correct
  one is the one whose *remaining* syllables also land on notes. A row from
  the next system fits the same anchors but its other syllables land in
  empty space.

### Approaches tried and rejected, with the measurement

| Attempt | Result |
|---|---|
| Greedy cursor over rows | Drifted in repetitive text: deleted the real `Ky`, `ri`, `e` from the Kyrie. Also stalled — one garbled syllable at the cursor stopped the rest, tenor matched 8 slots of 128 |
| Fixed 85 % match threshold | Rejects short rows: one letter error in a five-syllable row is already 80 % |
| Window 4 slots longer than the row | A replace at the row's end swallowed the next row's slots; deleted the correct `pe` in bar 20 |
| Filling short gaps from the bracketing row | Never fires. Gaps always fall *between* two rows, never inside one |
| Larger window (6, 10 instead of 3) | Coverage fell, 400 -> 388 -> 387 matched slots |

### What is left, and why it needs a person

Two things, neither fixable by changing text.

**Dropped syllables.** The OMR read five syllables where there are six —
`ra-ti-nem` for `o-ra-ti-o-nem`. Slots are then fewer than syllables and no
one-to-one alignment exists. The report lists these as
`kohdistamatta tahdit N-M:`.

**Notes carrying no lyric at all.** Down from 44 to 23 in the chorus bass of
movement 01; some of those 24 are melismas that correctly have none. What
remains is the systems where the assignment was ambiguous — the row has more
syllables than the system has notes, meaning the OMR dropped notes as well as
lyrics. Those need a person in MuseScore, and they also need the *notes*
checked, so they are proofreading work either way.


## The missing Dies irae recall (II·9b)

Verdi's "Dies irae" theme returns three times: end of Liber scriptus, end of
Confutatis, and the start of Libera me. **The second return was entirely
missing from every source file** — Confutatis (`10-Verdi_Confutatis.mxl`)
ends cleanly on the soloist's "gere curam mei finis" and Lacrymosa
(`11-Verdi_Lacrymosa.mxl`) starts cold on "Lacrymosa dies illa", with nothing
between them in any of the 16 source files. It is not a separately titled
section in any standard listing (confirmed by web search and by the absence
of anything between the two on CPDL's own page), which is exactly why a
per-movement CPDL split would drop it — there is no title to hang a file on.

The user found a PDF containing it (`Verdi_10bDies_irae.pdf`, "Print to PDF"
export, vector text and noteheads — same good case as 01/14) and confirmed
against it that the passage is real, substantial content (SATB + piano, not
a one-bar transition).

### Recipe: OMR it exactly like movements 01/14

    Audiveris -batch -transcribe -export \
      -constant org.audiveris.omr.image.ImageLoading.pdfResolution=450 \
      -output DIR -- Verdi_10bDies_irae.pdf

Audiveris was not installed (see *Environment*); reinstalled from the 5.11.0
macOS arm64 `.dmg` via the `hdiutil convert`/`attach` trick, copied to
`/Applications`, quarantine cleared with `xattr -dr` (a handful of read-only
JRE license files refuse — harmless, they are not executables).

Output: 5 parts (`Voice`×4 + `Piano`), 51 measures, **equal counts across
parts** — `fix-mxl.py` was not needed this time. Structural cross-check: the
one long tied note in the bass (4 measures, impossible to read confidently
off a rendered image by eye) came out as G3, and independently matches where
a person would place it by ear from the image. That agreement is the reason
to trust OMR over eyeballing pixels for polyphonic passages — there is no way
to "hear" a static image to check a guess, but OMR gives a second, structurally
independent read.

**Do not try to eyeball pitches from a rendered page for anything beyond a
single already-known melodic line** (like the syllable/x-position work
above). A sustained chord tone in an inner voice has no reliable landmark at
screen resolution, and there is no way to verify a guess before it is already
written into a file. This was tried first, got stuck on exactly that note,
and was abandoned in favour of OMR mid-session.

Lyrics: added as a fourth `Source` entry to `korjaa_sanat.py`'s `SOURCES`
list — the pipeline needed zero code changes, only a new entry. The lyric
font in this PDF reports as `F3` under `mutool draw -F stext` (a generic
subset-font resource name, not a real family name like "Times-Roman"/
"Garamond" — `extract_rows` just needs the exact string `stext` reports, so
this is not a special case). Result: 109 changes, 0 uncertain proposals,
72 % matched in the chorus bass. The `kohdistamatta` lines in the dry-run
report for this file are stale/rejected-candidate noise, not real gaps —
checked every one against the actual note/lyric data and against the source
page images, and the chorus bass text is complete and correct start to
finish (the only notes without their own lyric are legitimate tie
continuations of an already-lyric'd note, or passing tones within a
syllable's note group, both normal). **Soprano/Alto/Tenor were not checked
this closely** — they show many more notes-without-lyric than the bass,
plausibly genuine melismas (the bass just holds one pedal tone through the
same passage where the upper voices have a triplet flourish) but not
verified one by one the way the bass was.

Wiring into `yhdista.py`: new file
`10b-Verdi_Dies_irae_paluu-OMR-korjattu.mxl`, inserted between Confutatis and
Lacrymosa in `MOVEMENTS` (numbered "II·9b", titled "Dies irae (kertaus)" —
there is no standard number for it, see above), a `MAPPING` entry
(P1–P4 → Kuoro S/A/T/B, P5 → Piano), and added to `OMR_SOURCES` for
documentation (that set is not actually read anywhere else in the script —
checked with `grep -rn OMR_SOURCES *.py` — so this is bookkeeping only, not
functional). Verified with the usual note-count comparison:
`Verdi-Requiem-koko.mxl` went from 1756 to 1807 measures (+51, exact), Kuoro
B from 1824 to 1888 notes, and the file still converts in MuseScore without
`-f` on the first try.

### Open: which measure numbers is this actually at

Dies irae now numbers continuously (`NUMEROINTI_ALKAA_JOKA_OSASSA_YKKOSESTA =
False`), with 10b's offset computed the same mechanical way as every other
sub-movement: the sum of the actual measure counts of 02–10 (577), verified
against the files themselves, not hand-summed. That places 10b at 578–628
and Lacrymosa's start at 629.

That computed 578 does not agree with three other numbers for this same
spot, none of which agree with each other either:

| Source | 10b starts at | Lacrymosa starts at |
|---|---|---|
| Computed from source files' own measure counts (what's in `yhdista.py` now) | 578 | 629 |
| User's rehearsal-score excerpt (first pass) | — | 624 |
| `Verdi_10bDies_irae.pdf`'s own printed numbers (573–623, confirmed both ends) | 573 | → would be 624 |
| User's actual choir book (second, later confirmation) | — | 621 |

The gap between the computed 578 and the PDF's own 573 (5 measures) is
*larger* than the gap already noted between the two book-adjacent readings,
624 and 621 (3 measures) — and it must sit somewhere in movements 02–10,
not in 10b itself, since 10b's own length (51 measures) is not in question.
**Do not guess at a fix.** This needs the same treatment as the rest of
*Open assumptions* above: get the choir book's own numbers for a few more
anchor points (Tuba mirum, Recordare, Confutatis starts — partly done
earlier in this same investigation, but not written down anywhere, so
gather them again) and localise which sub-movement's bar count disagrees
with the book before touching the offsets. None of this blocks day-to-day
use of the file as it stands now — the numbering is internally consistent
and continuous, just not yet proven to match the physical book digit for
digit past Confutatis.

### What is left here specifically

1. Soprano/Alto/Tenor lyrics for II·9b — same close-verification pass the
   bass already got (see above).
2. Notes for all four voices are OMR output, unproofread against the source
   PDF beyond the one structural spot-check (the tied G3). Same category as
   *What is left* for movements 01/14 below.
3. The measure-numbering disagreement above (computed 578 vs. the book).

## The practice file: one visible staff, everything still sounding

`harjoitus.py --stemma "Basso I"` converts the merged score to `.mscz`,
gives every staff an instrument, and hides all staves but the singer's.
The point is that hidden staves still play, so the singer hears the whole
work while reading one line.

Everything here was established by experiment, because MuseScore's file
format is not documented in the app and guessing is expensive:

- **A staff is hidden with `<show>0</show>` inside its `<Part>`** in the
  `.mscx`. Verified by counting glyphs in the exported PDF: the part's
  noteheads and lyrics disappear (Leland 500 → 395, lyric font 140 → 30).
- **Hidden staves still sound.** The MIDI exported from the patched and
  unpatched `.mscz` is note-for-note identical, all 16 tracks.
- **Setting the instrument takes three edits, and missing any one leaves
  the part sounding like a grand piano.** In the `.mscx`, both the
  `<instrumentId>` *element* and the `<Instrument id="...">` *attribute*,
  and in `audiosettings.json`, a track entry pinning the sound. The
  attribute is what `audiosettings.json` refers to; leaving it at
  `grand-piano` while changing only the element silently does nothing.
- **`audiosettings.json` is what the GUI actually plays.** A file coming
  out of MusicXML import has `"tracks": []`, and with that MuseScore plays
  everything as a grand piano no matter what the instruments say. Each
  track needs `partId` (the `<Part id>`), `instrumentId` (the
  `<Instrument id>` attribute) and an `in.resourceMeta` naming the sound:
  `presetProgram`, `presetName`, and `id` of the form `MS Basic\0\<program>`.
  Keep the `partId: "999"` metronome track. The shape was copied from a
  file MuseScore had written itself.
- **The instrument must not be set through MusicXML at all.** Writing
  `<score-instrument><instrument-name>` plus `<midi-program>` into every
  `<score-part>` got through for only two parts of fifteen — the rest
  imported as `keyboard.piano.grand`. Adding `<midi-channel>` changed
  nothing.
- **Instrument ids come from MuseScore's own templates** under
  `Contents/Resources/templates/`, which are unpacked `.mscx` directories:
  `voice.vocals` (program 52, choir aahs), `wind.reed.oboe` (68),
  `keyboard.piano` (0).

      grep -rho "<instrumentId>[^<]*" \
          "/Applications/MuseScore 4.app/Contents/Resources/templates" | sort -u

  That yields 63 ids, a subset of what MuseScore knows. For anything not in
  it, let MuseScore name it: put `<instrument-name>X</instrument-name>` in a
  MusicXML `<score-instrument>`, import once, and read the `instrumentId`
  back out of the `.mscx`. That is how `brass.trumpet.c` was found — it is
  absent from the templates, and unlike their `brass.trumpet.bflat` it does
  not transpose, which is what we want for a reading aid.
- **Staff name and instrument are independent.** The staff still reads
  "Kuoro B" while sounding as a trumpet, so no renaming is needed.
- **The brass staves sound as piano, deliberately.** Tuba mirum has a real
  D trumpet part; leaving it as a trumpet would blur it against the read
  line in the one movement where both play.
- MuseScore's `.mxl` → `.mscz` conversion loses about 1.8 % of the piano's
  MIDI notes (ties), independently of this script. Compare patched against
  unpatched `.mscz`, not against the `.mxl`, when checking for losses.

### The recipe, step by step

If `harjoitus.py` is gone or MuseScore's format has moved on, this is the
whole procedure. Every step was verified on MuseScore 4.7.4.

    # 1. merged score -> MuseScore format, multimeasure rests switched on
    mscore -S tiivistys.mss -o harjoitus.mscz Verdi-Requiem-koko.mxl

    # 2. .mscz is a zip; the score itself is the single .mscx inside
    unzip harjoitus.mscz -d work

Then edit `work/*.mscx`. Each staff is one `<Part ...> ... </Part>` block,
and the staff's name is the **first** `<trackName>` inside it — the
`<Instrument>` further down has a second, empty one. For every block:

- replace `<instrumentId>...</instrumentId>` with the wanted id
- replace `<program value="N"/>` with the wanted program number
- insert `<show>0</show>` straight after the opening `<Part ...>` tag for
  every staff that should be hidden

Repack keeping every other member byte-identical — `score_style.mss`,
`META-INF/container.xml`, the JSON settings and the thumbnail all have to
survive, or MuseScore will not open the file. Python's `zipfile` reading
all members and rewriting only the `.mscx` is the safe way; a plain
`zip -r` over an unpacked directory also works but is easy to get wrong.

**Verifying it.** Three checks, and the second one has a trap:

    # visibility — the hidden parts' glyphs vanish from the printed page
    mscore -o x.pdf harjoitus.mscz
    mutool draw -F stext -o - x.pdf 1 | grep -c '<char'

    # notes still sounding — compare the patched .mscz against the
    # UNPATCHED .mscz, never against MIDI exported from the .mxl
    mscore -o patched.mid harjoitus.mscz
    mscore -o plain.mid   unpatched.mscz

    # which sound each staff plays — MIDI export will NOT tell you, see below
    mscore -o rendered.mp3 harjoitus.mscz

**MIDI export is not a check of the sound.** It reads `<program value>`
from the `.mscx`, so it reported the right instruments while the GUI still
played every staff as a piano. That mistake shipped once. The sound the
user hears comes from `audiosettings.json`.

Rendering audio is the check that works. Do it on a short movement, not on
the merged score — the full 1756 bars take well over ten minutes. Patching
one part of `04-Verdi-Mors_stupebit.mxl` to trumpet and rendering both
versions gave two MP3s of identical length differing in 79 % of their
bytes, with the first difference at the point where the music starts.
Identical hashes would have meant the patch did nothing.

Counting Note On events by scanning bytes for `0x90..0x9F` **gives wrong
answers** — velocity and program bytes collide with the status range, and
two files with different instruments then appear to differ by tens of
notes. Parse properly: variable-length delta times, meta and sysex events
skipped by their declared length, and running status carried over. Done
that way the two files came out identical at 34 034 notes across 16
tracks, which is what proves the hidden staves still sound.
