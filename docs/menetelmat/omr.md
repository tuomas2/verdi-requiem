*Part of the Verdi Requiem working notes — the index is [`CLAUDE.md`](../../CLAUDE.md).*

# Optical music recognition, and fixing its lyrics from the PDFs

Movements 01 (Requiem & Kyrie), 14 (Agnus Dei) and II·9b (the Dies irae
recall) existed only as PDFs and were produced by OMR, so they are **less
reliable than the other 14**. This file holds the recipe that produced them,
the PDF-driven pass that corrected their chorus lyrics, and what is still
left for a person.
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

## Fixing OMR lyrics from the source PDFs

`korjaa_sanat.py` rewrites the chorus lyrics of movements 01 and 14 to match
their source PDFs. `--kuiva` reports without writing. Output goes to
`*-OMR-korjattu.mxl`; the OMR originals are never touched, so the pass is
repeatable if the OMR is ever redone for the piano.

> **DO NOT run `korjaa_sanat.py` without reading this first.** Its `Source`
> entries read the OMR *originals* (`14-…-agnus-dei-OMR.mxl`) and rewrite the
> `-OMR-korjattu.mxl` files **from scratch**. Every manual fix since the
> original OMR lives only in the `-korjattu` files — movement 14's chorus-bass
> tacet spans and its 15 note/duration fixes — so a plain re-run **silently
> destroys them** and the loss shows up only as the old bugs reappearing in
> the reading part. **Movement 14 is the only one exposed, and that is now
> measured.** Movement 01's hand layer has been a table in `korjaa_kasin.py`
> since 2026-09-02; II·9b was listed here as exposed too, but it never was.
> Backing up all three `-korjattu` files, running the script and comparing the
> XML (2026-09-09): 01 and 10b come back **identical**, 14 does not — 570 058
> → 604 055 bytes, i.e. its tacet spans and note fixes are gone. Before
> re-running for movement 14: either diff the result against the committed
> `-korjattu` file and re-apply the manual work, or restore from git
> afterwards. Better, move its hand layer into `korjaa_kasin.py` the way
> movements 01, 11 and 10b's were — see *Recipe*, last section.

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

### Settled: which measure numbers this is actually at — **573–623**

This used to be the longest open question in this file: four sources gave four
different answers (computed 578, a first rehearsal-score reading 624, the
`Verdi_10bDies_irae.pdf`'s own printed 573–623, and the choir book's 621 for
Lacrymosa), and the advice was "do not guess at a fix, get the book's own
numbers for more anchor points".

That is exactly what happened on 2026-09-02: the singer read the book's start
number for every Dies irae sub-movement and handed them over. **10b is at
573–623, which is the 10b PDF's own printed numbering exactly** — the one
source that had been right all along — and the book's Lacrymosa *heading* is at
621, i.e. the book counts the last three bars of the 10b PDF as the start of
Lacrymosa. The computed 578 was wrong because the mechanical cumulative count
assumed CPDL's per-movement files break at the same bars the book does, and in
six places they do not. See *2026-09-02 (later): the book's own bar numbers for
Dies irae*.

**The trap that followed from that sentence** (found 2026-09-03): 621 is the
book's heading, not the number of the Lacrymosa **file's** first bar. The
Lacrymosa PDF prints its own numbers too, and they run **624–701** — continuous
with 10b's 573–623, with no overlap. `DIES_IRAE_ALUT` wants the file's first
bar, so Lacrymosa is 624. Numbering it 621 made every bar of the movement three
too low. See *2026-09-03 (c): Lacrymosa's three-bar shift*.

### What is left here specifically

1. Soprano/Alto/Tenor lyrics for II·9b — same close-verification pass the
   bass already got (see above).
2. Notes for all four voices are OMR output, unproofread against the source
   PDF beyond the one structural spot-check (the tied G3). Same category as
   *What is left* for movements 01/14 below.
3. ~~The measure-numbering disagreement~~ — settled, see above.
