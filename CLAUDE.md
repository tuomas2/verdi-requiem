> **Mikä tämä tiedosto on.** Tämä on hakemisto Claude Code -avusteisen työn
> muistiinpanoihin: mitä tekijä haluaa, mikä on kesken, ja mistä tiedostosta
> mikin luku löytyy. Se on englanniksi ja puhuu tekijästä kolmannessa
> persoonassa ("the user"): kyseessä on kuorolainen, joka laulaa bassoa ja
> lukee omaa stemmaansa.
>
> Itse aineisto — jokainen löydetty virhe, miten se löytyi, ja mitkä
> menetelmät kokeiltiin ja hylättiin — on `docs/`-hakemistossa, ja
> päivätty työpäiväkirja tiedostossa
> [`docs/tyopaivakirja/README.md`](docs/tyopaivakirja/README.md). Se on
> pilkottu tänne 2026-09-09; ennen sitä kaikki oli tässä yhdessä
> tiedostossa, ja `git log CLAUDE.md` näyttää mistä mikä rivi tuli.
>
> Jos aiot parantaa nuotteja, lue skilli
> [`.claude/skills/korvakuulokorjaus/SKILL.md`](.claude/skills/korvakuulokorjaus/SKILL.md)
> ja alla oleva taulukko *Open* — ne kertovat mistä kannattaa aloittaa.
> Yleiskuva on suomeksi tiedostoissa `README.md` ja `YHDISTAMINEN.md`.

# Verdi Requiem — working notes

Verdi's *Messa da Requiem* in MusicXML, assembled from 16 separate movement
files into one score, plus per-voice reading parts for choir practice.

**The user is a Finnish-speaking chorus bass.** Reply in Finnish. `YHDISTAMINEN.md`
(the user-facing handover doc) is in Finnish; these notes are the technical
background for future sessions.

## What the user actually wants

Read their own chorus line while the rest of the choir and the piano reduction
still play, and carry a PDF of their line on a Boox e-reader. That drives every
design decision: measure numbers must match the printed rehearsal score, and
the reading part must be dense.

## Where to read what

Nothing below is loaded until it is needed. Read the file the task points at
before touching anything — every one of them holds approaches that were tried
and rejected, with the measurement that killed them, and repeating those is
the single most expensive mistake available here.

| File | What it holds |
|---|---|
| [`docs/tyopaivakirja/README.md`](docs/tyopaivakirja/README.md) | **Start here for context.** The narrative state of the work, plus one file per session, newest last. Dated entries cross-reference each other by date; that page maps the dates to files |
| [`.claude/skills/korvakuulokorjaus/SKILL.md`](.claude/skills/korvakuulokorjaus/SKILL.md) | **The recipe for a reported error** — which layer the fix belongs in, how to locate the bar and page, the confirm-a-hypothesis rule, the rebuild commands. Loads by itself when the singer reports something |
| [`docs/hakemistot.md`](docs/hakemistot.md) | Every filename and script, what each is for, the four data directories, the CPDL provenance of the sources |
| [`docs/ymparisto.md`](docs/ymparisto.md) | MuseScore 4.7.4 and its CLI's nondeterministic abort, `mutool`, Audiveris, Tesseract data |
| [`docs/menetelmat/omr.md`](docs/menetelmat/omr.md) | OMR of movements 01/14/II·9b, and the whole PDF-driven lyric-fixing method (`korjaa_sanat.py`) with its measurements |
| [`docs/menetelmat/yhdistaminen.md`](docs/menetelmat/yhdistaminen.md) | The eight parts, what the merge had to learn, the "corrupted file" warning, why movement I has no piano, the open assumptions |
| [`docs/menetelmat/kuorotiedostot.md`](docs/menetelmat/kuorotiedostot.md) | The choir's own MuseScore files: correct notes, no lyrics, condensed cut. The second source, and how to compare against it without lying to yourself |
| [`docs/menetelmat/harjoitus.md`](docs/menetelmat/harjoitus.md) | The practice `.mscz`: one visible staff, everything still sounding, and what MuseScore's file format demanded |
| [`docs/suunnitelmat/`](docs/suunnitelmat/) | Design and implementation plans |
| [`TODO.md`](TODO.md) | **The questions only the printed rehearsal book can answer**, in Finnish and addressed to the singer, cheapest first. Written as named questions ("is there a flat in front of these two notes?") because that is what comes back answered; keep it short and keep the answered ones in their own section |
| [`LUOTETTAVUUS.md`](LUOTETTAVUUS.md) | Per movement × voice: what has been verified and what has not. **Generated** by `luotettavuus.py`, but committed |

## Open, roughly in the order a singer would feel them

| Open | Where to read up |
|---|---|
| **Notes** of movement 01: only bars 1–78 are done (all four chorus voices, against the choir file and the printed page); its **Kyrie, bars 79–140, is not** — and the choir file cannot settle it until someone works out the bar mapping, which stops corresponding around bar 94. Movement 14's `Kuoro B` is done; its S/A/T are not | [`2026-09-10-kuorotiedostot-ja-osan-i-savelet.md`](docs/tyopaivakirja/2026-09-10-kuorotiedostot-ja-osan-i-savelet.md); [`docs/menetelmat/omr.md`](docs/menetelmat/omr.md) |
| Movement 01's chorus-bass **text** now reads complete (86 % of its notes carry a syllable; the 15 that do not are melisma-internal). Its **notes** are now checked against the choir file for bars 1–78 (two differences, both resolved in our favour by the printed page, and the printed book confirmed one of them on 2026-09-10 along with bars 51–52's `om-nis`, which went back to the source page's placement). S/A/T got their first text work 2026-09-10 — the line "et lux per-pe-tu-a", and the soprano's whole "Te decet hymnus" lifted off lyric row 2 — but are still far from proofread | [`2026-09-02-tahtinumerot-ja-osa-i.md`](docs/tyopaivakirja/2026-09-02-tahtinumerot-ja-osa-i.md), [`2026-09-10-kuorotiedostot-ja-osan-i-savelet.md`](docs/tyopaivakirja/2026-09-10-kuorotiedostot-ja-osan-i-savelet.md) |
| Movement 01's chorus **alto, bar 77**: the printed page draws `Gis5` — measured from the music font, at the height of the key signature's own G♯ — and the choir file sings `Gis4`. Ours matches the page, but the leap is a major seventh up and a minor seventh back down, crossing a third above the soprano, so the page may be wrong as it was at Lacrymosa 653. Needs the conductor, not another measurement. (The soprano's and alto's **wrong key in bars 28–34** was the same row until 2026-09-10; it is now fixed, seven notes) | [`2026-09-10-kuorotiedostot-ja-osan-i-savelet.md`](docs/tyopaivakirja/2026-09-10-kuorotiedostot-ja-osan-i-savelet.md), *two more notes*; [`2026-09-07-savellaji-tyhjassa-tahdissa.md`](docs/tyopaivakirja/2026-09-07-savellaji-tyhjassa-tahdissa.md), *The same error, bigger* |
| Movement 14's `Kuoro B` is **settled** — notes match the choir file exactly, all 74 bars are metrically valid, 29 remaining wordless notes are melisma-internal or chord second notes. Its **Soprano/Alto/Tenor are not**: 48–59 % of their notes carry no syllable, and they still show fabricated content and contentless measures in bars 59–74 | [`2026-08-31-agnus-dei-kuorobasso.md`](docs/tyopaivakirja/2026-08-31-agnus-dei-kuorobasso.md) |
| II·9b: Soprano/Alto/Tenor lyrics unchecked. Its position is **settled** (573–623, from the choir book) and its `Kuoro B` is **settled too** — words against the source PDF note by note, notes against the choir file over all 51 bars, zero differences left | [`docs/menetelmat/omr.md`](docs/menetelmat/omr.md), *The missing Dies irae recall*; [`2026-09-10-nuottikirjan-nelja-tarppia.md`](docs/tyopaivakirja/2026-09-10-nuottikirjan-nelja-tarppia.md) |
| Lacrymosa's `Kuoro B` is **settled** — every note checked against the choir file, every syllable against the printed page at note resolution, plus one nine-bar stretch where the printed edition itself was wrong. Its **Soprano/Alto/Tenor and soloists are not**, and the chorus tenor already shows one text gap at bar 688 | [`2026-09-03-lacrymosan-kolmen-tahdin-siirtyma.md`](docs/tyopaivakirja/2026-09-03-lacrymosan-kolmen-tahdin-siirtyma.md) |
| The "same figure must carry the same text in every voice" check found a defect the printed page could not, and the sharper version — "does this note fit what the other staves and the piano are doing on this beat" — reversed a wrong verdict. Neither is automated, and movement 11's S/A/T is the obvious first target | [`2026-09-03-lacrymosan…`](docs/tyopaivakirja/2026-09-03-lacrymosan-kolmen-tahdin-siirtyma.md), *The lesson*; [`2026-09-04-kahdeksan…`](docs/tyopaivakirja/2026-09-04-kahdeksan-korvakuulohavaintoa.md), *Lacrymosa 653* |
| Movement 07 (II·6 Rex tremendae): its chorus bass had **one line of the stanza printed twice and the next one missing**, twice over (bars 340–341, 362–363) — found by ear, fixed. Its **notes** are now compared against the choir file over the whole movement: one difference in 174 notes, and it was real (bar 343, a lower neighbour a major third below instead of a semitone). The chorus tenor had one too (bar 353, an octave up where tenor and bass are in unison); soprano and alto came out clean. Only its **S/A/T words** are still unchecked, and the movement has no source PDF to read them from | [`2026-09-09-rex-tremendaen-sakeet-ja-taukohannat.md`](docs/tyopaivakirja/2026-09-09-rex-tremendaen-sakeet-ja-taukohannat.md) |
| Four Dies irae sub-movements (II·2, II·4, II·6, II·7 seams) may carry the same off-by-a-few numbering Lacrymosa had. Needs one bar number from **inside** each, not its heading | [`2026-09-03-lacrymosan…`](docs/tyopaivakirja/2026-09-03-lacrymosan-kolmen-tahdin-siirtyma.md), *The same trap* |
| Liber scriptus: the "user recalls 6" half is **solved** (six one-bar interjections, three of which were missing — see [`2026-09-03-liber-scriptus-dies-irae.md`](docs/tyopaivakirja/2026-09-03-liber-scriptus-dies-irae.md)); the Soprano-vs-A/T/B text disagreement at bars 247–254 is still unresolved without the physical score | [`2026-08-31-kolme-korvakuulohavaintoa.md`](docs/tyopaivakirja/2026-08-31-kolme-korvakuulohavaintoa.md) |
| The named OMR garble in movement I's chorus S/A/T is **fixed 2026-09-10** (`lg},`, `ux`, `per-pe-tll-a`, `In-ce-at`, and `Reutenauer` — which turned out to be the engraver's credit line at the foot of movement 14's source page, sitting on that movement's *piano* staff, not movement I's tenor). 68 broken forms remain, down from 77, and they are what is left of this item | [`2026-09-09-suomennokset.md`](docs/tyopaivakirja/2026-09-09-suomennokset.md), *What is left here*; [`2026-09-10-kuorotiedostot-ja-osan-i-savelet.md`](docs/tyopaivakirja/2026-09-10-kuorotiedostot-ja-osan-i-savelet.md); the list is `python3 suomennos.py`'s own output |
| 13 lyric changes reported but deliberately not applied. Three are now decided: alto I t.37 `at`→`et` applied, and alto I t.39 `ti`→`vo` and soprano I t.134 `Chri`→`e` shown **wrong** against the PDF's own text rows and pinned by tests. The report still says 13, because the script reads the untouched originals | `python3 korjaa_sanat.py --kuiva` lists them; [`2026-09-10-kuorotiedostot-ja-osan-i-savelet.md`](docs/tyopaivakirja/2026-09-10-kuorotiedostot-ja-osan-i-savelet.md) |
| Movement I has no piano — and **the choir files have one** (`01_requiem`: 1620 notes over 127 bars; `04_dies_irae_2`: 1739 over 96). The user's idea 2026-09-10, recorded and not started: copy the piano out of the choir files where they cover a movement, both to fill this gap and to turn the piano into an *independent* arbiter for note questions — which is exactly what it is not today, since ours comes out of the same OMR pass as the voices. Blocked on a per-movement bar mapping (their cut is condensed; movement I is 127 bars against our 140 and stops corresponding around 94) and on asking about provenance before unknown-authorship material goes into a public repo | [`docs/menetelmat/yhdistaminen.md`](docs/menetelmat/yhdistaminen.md), *Movement I has no piano*; [`docs/menetelmat/kuorotiedostot.md`](docs/menetelmat/kuorotiedostot.md); [`TODO.md`](TODO.md), *Isoimmat voitot* |
| Four assumptions made without the rehearsal score. The fifth — that the Sanctus's chorus bass is Bass I, the one whose consequence would have been a whole movement read off the wrong staff — is **settled 2026-09-10**: the singer enters at bar 2 and `Kuoro B` is the staff that enters at bar 2 | [`docs/menetelmat/yhdistaminen.md`](docs/menetelmat/yhdistaminen.md), *Open assumptions*; [`2026-09-10-nuottikirjan-nelja-tarppia.md`](docs/tyopaivakirja/2026-09-10-nuottikirjan-nelja-tarppia.md) |
| The second, independent note source now lives in **`.local/musescore/`** and is still out of the repo. Four of its eight folders have been compared voice by voice — `01_requiem`, `03_rex_tremendae`, `04_dies_irae_2`, `06_agnus_dei` — and the other four (`02_dies_irae`, `05_sanctus`, `07_libera_me`, `08_libera_me_2`) only in the four targeted spots earlier sessions used them for | [`docs/menetelmat/kuorotiedostot.md`](docs/menetelmat/kuorotiedostot.md), [`2026-09-10-kuorotiedostot-ja-osan-i-savelet.md`](docs/tyopaivakirja/2026-09-10-kuorotiedostot-ja-osan-i-savelet.md) |
| II·9b's **notes** in S/A/T: seven candidate differences against the choir file remain (S t.599, t.605, t.608, t.612; A t.612; T t.602, t.608) now that the bass's t.607 is fixed. **Three of them are a dropped flat and are near-certain** — S t.605 `G♭5`, S t.612 `D♭5`, A t.612 `G♭4` — because our own piano staff plays that flat on the same beat and, at t.605, contradicts itself by spelling both `G♭5` and `G6` in one E♭-minor chord. They are not applied: the piano comes out of the same OMR pass, so it is an argument and not a measurement, and a photograph of that one spread would settle all seven. The source PDF cannot arbitrate at all — subset font, private codepoints | [`2026-09-10-nuottikirjan-nelja-tarppia.md`](docs/tyopaivakirja/2026-09-10-nuottikirjan-nelja-tarppia.md); [`2026-09-10-kuorotiedostot-ja-osan-i-savelet.md`](docs/tyopaivakirja/2026-09-10-kuorotiedostot-ja-osan-i-savelet.md), *What is left here* |

## The four data directories

`polut.py` derives the directory from a bare filename, so every script and
table speaks bare names. The full inventory is in
[`docs/hakemistot.md`](docs/hakemistot.md).

| Directory | What it holds |
|---|---|
| `lahteet/` | Originals: CPDL `.mxl`, source PDFs, Audiveris projects, raw `-OMR.mxl`. **Never edited** |
| `johdetut/` | Everything the scripts generate: `-OMR-korjattu.mxl`, `-kasin.mxl`, the merged score |
| `stemmat/` | The eight reading parts and their contents listing |
| `harjoitus/` | Practice `.mscz`, **not** in version control |
| `sivusto/` | Website sources |
| `.local/musescore/` | The choir's own MuseScore files, the second note source. Outside `polut.py`, **not** in version control, and excluded in `.git/info/exclude` — authorship is unknown and the filenames carry singers' names |

## Two things to know before running anything

**`korjaa_sanat.py` can silently destroy work — in exactly one movement.** Its
`Source` entries read the OMR *originals* and rewrite the `-OMR-korjattu.mxl`
files **from scratch**. Movement 14 carries hand fixes that live only in that
file, so a plain re-run loses them and the loss shows up only as old bugs
reappearing in a reading part. Since 2026-09-10 that movement does have a
`korjaa_kasin.py` table of its own (`OSAT_V`, writing
`14-…-kasin.mxl`), so new fixes are safe — but the **older** hand edits are
still baked into `-OMR-korjattu.mxl` and the hazard stands until they are
diffed into the table. Movements 01 and II·9b are safe, and that was
measured on 2026-09-09 rather than assumed: a plain re-run reproduces their
`-korjattu` files identically, and their hand layers are tables in
`korjaa_kasin.py`. Details and the way out are in
[`docs/menetelmat/omr.md`](docs/menetelmat/omr.md).

**Compute expected note counts per staff from `MAPPING` and the sources, then
compare against the merged output.** Every row must match exactly. That habit
found two silent data-loss bugs that looked fine on the page. Do not hand-add
the numbers — an early hand sum was wrong.

Tests, from the repo root: `python3 -m unittest discover -s testit -t .` (366).
