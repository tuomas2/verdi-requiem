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

## Layout of the directory

| Pattern | What it is |
|---|---|
| `01…16-*.mxl` | Source movements, numbered by position in the whole work |
| `01-*.pdf`, `14-*.pdf` | Source PDFs for the two movements that had no MusicXML |
| `*.omr` | Audiveris projects for those two, for manual correction |
| `Verdi-Requiem-koko.mxl` | Merged score, 15 staves, 1756 measures |
| `stemma-*.mxl` / `.pdf` | Eight choir reading parts |
| `stemmat-sisallys.txt` | Where each movement starts in all eight |
| `yhdista.py` | The merge tool; mapping table at the top |
| `fix-mxl.py` | Repairs missing measures in Audiveris exports |
| `tiivistys.mss` | MuseScore style: multimeasure rests |

**The hyphen/underscore in source names encodes provenance, so do not
normalise it.** Among the `Verdi*` files, `Verdi-*` came from a Sibelius 7.5.1
export dated 2017-10-10 (movements 02–07, 13) and `Verdi_*` from a CPDL Finale
2014 + Dolet batch dated 2015-05-11 (08–12, 15). `16-Libera_Me.mxl` follows
neither convention but belongs to the Sibelius batch. All are CPDL editions.

Movements 01 (Requiem & Kyrie) and 14 (Agnus Dei) existed only as PDFs and were
produced by OMR — their notes and lyrics are **less reliable than the other 14**
and still need proofreading against the PDFs.

## Environment

- **MuseScore 4.7.4**, x86_64 running under Rosetta. Its CLI aborts outright on
  any score that would raise an import warning in the GUI — where the GUI offers
  "Ignore", the CLI just fails and writes nothing. `-f` overrides that; the
  generated files no longer need it, but the raw sources 05 and 16 still do.
  MuseScore has no built-in OMR — "Import PDF" opens musescore.com in a browser.
- `mutool` (mupdf-tools) installed via Homebrew. Used for rasterising and for
  reading text out of PDFs. `poppler` is *not* installed.
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
| Measure numbers restart in every movement | The rehearsal score was not available | Check whether the book numbers Dies irae 1–655 continuously |
| Sanctus chorus bass = Bass I | User has the higher of the two; Bass I is higher (median G3 vs D3) | Bass I enters at m. 2, Bass II at m. 4 |
| Movement 05 soloist = mezzo | File says "Soprano solo" but Liber scriptus is the mezzo aria | Musicological, not a data question |
| Movements 12, 15 soloist order | Parts are unnamed; inferred from standard score order | Compare with any full score |

## Verification habit that caught real bugs

Compute expected note counts per target staff directly from `MAPPING` and the
source files, then compare against the merged output. Every row must match
exactly. This found two silent data-loss bugs that looked fine on the page.
Do not hand-add the numbers — an early hand sum was wrong.
