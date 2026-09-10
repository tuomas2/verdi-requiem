*Part of the Verdi Requiem working notes — the index is [`CLAUDE.md`](../CLAUDE.md).*

# Layout of the directory

Since 2026-09-04 the data lives in four directories that follow the direction
the data flows; the scripts and their tables still speak bare filenames, and
`polut.py` derives the directory from the name. See *2026-09-04 (later)*.

| Directory | What it holds |
|---|---|
| `lahteet/` | Originals: CPDL `.mxl`, source PDFs, Audiveris projects, raw `-OMR.mxl`. Never edited |
| `johdetut/` | Everything the scripts generate: `-OMR-korjattu.mxl`, `-kasin.mxl`, `-piano.mxl`, the merged score |
| `stemmat/` | The eight reading parts and their contents listing |
| `harjoitus/` | Practice `.mscz`, **not** in version control — they are 3.2 MB each and rebuilt wholesale |
| `sivusto/` | Website sources: the shared stylesheet, `requiem.html`, part thumbnails |
| `docs/suunnitelmat/` | Design and implementation plans |
| `testit/` | The test suite |

| Pattern | What it is |
|---|---|
| `01…16-*.mxl` | Source movements, numbered by position in the whole work |
| `01-*.pdf`, `14-*.pdf` | Source PDFs for the two movements that had no MusicXML |
| `Verdi_10bDies_irae.pdf` | Source PDF for II·9b, the missing "Dies irae" recall (see below) |
| `Verdi_Lacymosa.pdf` | The printed source for movement 11, same CPDL edition as the `.mxl`. Not an `.mxl` source, but what the whole chorus bass was verified against — and it **prints its own bar numbers, 624–701**. Not an authority, though: it is wrong about the text at bars 657–665 and about one note at bar 653 |
| `*.omr` | Audiveris projects, for manual correction |
| `01-kuoropiano.musicxml` | Movement I's piano reduction, squeezed out of the choir's own MuseScore file by `kuoropiano.py --pura`. Third-party material of unknown authorship, kept here so the whole chain reproduces without `.local/musescore/`; its `<rights>` says so |
| `*-OMR-korjattu.mxl` | OMR'd sections with their chorus lyrics fixed from the PDFs |
| `*-kasin.mxl` | **Generated**, not hand-edited: `korjaa_kasin.py`'s output, the file `yhdista.py` actually reads for movements II·1, II·4, II·6, II·9b, II·10, IV and VII — and for movement 01 the input to `kuoropiano.py` rather than to `yhdista.py` |
| `01-Verdi_Requiem-piano.mxl` | **Generated** by `kuoropiano.py`: movement 01 with its piano staff replaced by the choir file's, and the whole file's `divisions` normalised to one value. This is what `yhdista.py` reads for movement I |
| `Verdi-Requiem-koko.mxl` | Merged score, 15 staves, 1807 measures |
| `stemma-*.mxl` / `.pdf` | Eight choir reading parts |
| `stemmat-sisallys.txt` | Where each movement starts in all eight |
| `sisallys.py` | Rebuilds that listing from the eight PDFs, and writes the same listing onto each part's first page as a clickable table of contents; run it after any re-render |
| `linkit.py` | The clickable contents: `--varaa` reserves the room in the `.mxl` **before** rendering, `lisaa` (driven by `sisallys.py`) draws it into the PDF with a link per row and PDF bookmarks. `--riisu` removes them, `--lue` reads them back |
| `yhdista.py` | The merge tool; mapping table at the top |
| `sivuotsikot.py` | Writes the running movement name over each page's first bar; run after `yhdista.py`, before rendering |
| `paivays.py` | Stamps the part with the date its content last changed — small, top left of page 1, and the same date read back by the site. Runs **last** before rendering |
| `korjaa_sanat.py` | Fixes OMR lyric errors against the source PDFs |
| `korjaa_kasin.py` | The hand-verified fixes on top of that, as a table; writes the `*-kasin.mxl` files |
| `kuoropiano.py` | Movement I's piano staff, taken from the choir's own MuseScore file by a proven bar mapping; writes `01-Verdi_Requiem-piano.mxl`. Runs **after** `korjaa_kasin.py` and **before** `yhdista.py`. `--pura` extracts the source from an `mscore` export (needs `.local/musescore/`) |
| `rajaa.py` | Rajaa PDF-sivun palan PNG:ksi ilman ulkoisia kirjastoja — se on ainoa tapa tehdä tarkistuksen viimeinen vaihe, sivun lukeminen kuvana yhteen viivastoon rajattuna. Ks. [`docs/ymparisto.md`](ymparisto.md) |
| `suomennos.py` | The Finnish glossary, the gloss placement, and the syllabic repair. `--teksti` prints a part's whole text as running prose |
| `nayta.py` | Prints a staff's notes, voices and **lyric rows** per bar — the first tool for any reported error |
| `harjoitus.py` | Builds a practice .mscz: own voice as trumpet, rest hidden |
| `harjoitus/*.mscz` | The result, one per singer. Gitignored |
| `testit/test_*.py` | Tests; all of them: `python3 -m unittest discover -s testit -t .` (433). Run from the repo root — the tests and the scripts both use relative paths |
| `fix-mxl.py` | Repairs missing measures in Audiveris exports |
| `tiivistys.mss` | MuseScore style for the reading parts: multimeasure rests, a bar number on every bar, extra air between systems |
| `.local/musescore/NN_name/` | The choir's own MuseScore practice files — correct notes and piano, no lyrics at all; see *The choir's own MuseScore practice files*. **Not in the repo**: authorship is unknown and the filenames carried singers' names, so they were kept out of the public history. They exist only on the user's own machine, and `.local/` is listed in `.git/info/exclude`. (Earlier notes call this directory plain `musescore/`; it moved under `.local/` on 2026-09-10.) |
| `polut.py` | Derives which of the four directories a bare filename belongs to |
| `luotettavuus.py` | Per movement × voice: what has been verified and what has not. Writes `LUOTETTAVUUS.md` |
| `LUOTETTAVUUS.md` | **Generated**, but committed: the table in readable form. What the site and `README.md` link to |
| `sivusto.py` | Builds the website into `_sivusto/`; CI runs the same command |

All the source `.mxl` and PDF files came from **CPDL's Requiem page**,
<https://www.cpdl.org/wiki/index.php/Requiem_(Giuseppe_Verdi)>, which is the
citation to give when the sources need one. (The site sits behind a Cloudflare
challenge, so `curl` gets a 403 — open it in a browser.)

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
