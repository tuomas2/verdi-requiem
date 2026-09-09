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
| [`LUOTETTAVUUS.md`](LUOTETTAVUUS.md) | Per movement × voice: what has been verified and what has not. **Generated** by `luotettavuus.py`, but committed |

## Open, roughly in the order a singer would feel them

| Open | Where to read up |
|---|---|
| **Notes** of movements 01 and II·9b are still unproofread (movement 14's `Kuoro B` is now done; its S/A/T are not) | [`docs/menetelmat/omr.md`](docs/menetelmat/omr.md); the lyrics pass did not touch notes |
| Movement 01's chorus-bass **text** now reads complete (86 % of its notes carry a syllable; the 15 that do not are melisma-internal). Its **notes** are still unproofread, and S/A/T are untouched | [`2026-09-02-tahtinumerot-ja-osa-i.md`](docs/tyopaivakirja/2026-09-02-tahtinumerot-ja-osa-i.md) |
| Movement 01's chorus **soprano and alto** read bars 28–34 in the wrong key (three sharps instead of one flat), so their pitches there are wrong — `Fis4`/`Cis5` against the bass's plain F major. Found by measurement, not fixed: the key signature is only the cause, the pitches themselves are what has to be re-read | [`2026-09-07-savellaji-tyhjassa-tahdissa.md`](docs/tyopaivakirja/2026-09-07-savellaji-tyhjassa-tahdissa.md), *The same error, bigger* |
| Movement 14's `Kuoro B` is **settled** — notes match the choir file exactly, all 74 bars are metrically valid, 29 remaining wordless notes are melisma-internal or chord second notes. Its **Soprano/Alto/Tenor are not**: 48–59 % of their notes carry no syllable, and they still show fabricated content and contentless measures in bars 59–74 | [`2026-08-31-agnus-dei-kuorobasso.md`](docs/tyopaivakirja/2026-08-31-agnus-dei-kuorobasso.md) |
| II·9b: Soprano/Alto/Tenor lyrics unchecked (its position is **settled**: 573–623, from the choir book) | [`docs/menetelmat/omr.md`](docs/menetelmat/omr.md), *The missing Dies irae recall* |
| Lacrymosa's `Kuoro B` is **settled** — every note checked against the choir file, every syllable against the printed page at note resolution, plus one nine-bar stretch where the printed edition itself was wrong. Its **Soprano/Alto/Tenor and soloists are not**, and the chorus tenor already shows one text gap at bar 688 | [`2026-09-03-lacrymosan-kolmen-tahdin-siirtyma.md`](docs/tyopaivakirja/2026-09-03-lacrymosan-kolmen-tahdin-siirtyma.md) |
| The "same figure must carry the same text in every voice" check found a defect the printed page could not, and the sharper version — "does this note fit what the other staves and the piano are doing on this beat" — reversed a wrong verdict. Neither is automated, and movement 11's S/A/T is the obvious first target | [`2026-09-03-lacrymosan…`](docs/tyopaivakirja/2026-09-03-lacrymosan-kolmen-tahdin-siirtyma.md), *The lesson*; [`2026-09-04-kahdeksan…`](docs/tyopaivakirja/2026-09-04-kahdeksan-korvakuulohavaintoa.md), *Lacrymosa 653* |
| Four Dies irae sub-movements (II·2, II·4, II·6, II·7 seams) may carry the same off-by-a-few numbering Lacrymosa had. Needs one bar number from **inside** each, not its heading | [`2026-09-03-lacrymosan…`](docs/tyopaivakirja/2026-09-03-lacrymosan-kolmen-tahdin-siirtyma.md), *The same trap* |
| Liber scriptus: the "user recalls 6" half is **solved** (six one-bar interjections, three of which were missing — see [`2026-09-03-liber-scriptus-dies-irae.md`](docs/tyopaivakirja/2026-09-03-liber-scriptus-dies-irae.md)); the Soprano-vs-A/T/B text disagreement at bars 247–254 is still unresolved without the physical score | [`2026-08-31-kolme-korvakuulohavaintoa.md`](docs/tyopaivakirja/2026-08-31-kolme-korvakuulohavaintoa.md) |
| Movement I's chorus S/A/T carry OMR garble the text dump now names exactly (`lg},`, `ux`, `per-pe-tll-a`, `In-ce-at`, the editor's name `Reutenauer` at bar 68). One `korjaa_kasin.py` row each once someone reads the source page | [`2026-09-09-suomennokset.md`](docs/tyopaivakirja/2026-09-09-suomennokset.md), *What is left here*; the list is `python3 suomennos.py`'s own output |
| 13 lyric changes reported but deliberately not applied | `python3 korjaa_sanat.py --kuiva` lists them |
| Movement I has no piano | [`docs/menetelmat/yhdistaminen.md`](docs/menetelmat/yhdistaminen.md), *Movement I has no piano* |
| Five assumptions made without the rehearsal score | [`docs/menetelmat/yhdistaminen.md`](docs/menetelmat/yhdistaminen.md), *Open assumptions* |
| A second, independent note source (`musescore/`) turned up — now used for four targeted fixes, still not exhaustively explored beyond that | [`docs/menetelmat/kuorotiedostot.md`](docs/menetelmat/kuorotiedostot.md) |

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

## Two things to know before running anything

**`korjaa_sanat.py` can silently destroy work.** Its `Source` entries read the
OMR *originals* and rewrite the `-OMR-korjattu.mxl` files **from scratch**.
Movements 14 and II·9b still carry hand fixes that live only in those files, so
a plain re-run loses them and the loss shows up only as old bugs reappearing in
a reading part. Movement 01 is safe: its hand layer is a table in
`korjaa_kasin.py`. Details and the way out are in
[`docs/menetelmat/omr.md`](docs/menetelmat/omr.md).

**Compute expected note counts per staff from `MAPPING` and the sources, then
compare against the merged output.** Every row must match exactly. That habit
found two silent data-loss bugs that looked fine on the page. Do not hand-add
the numbers — an early hand sum was wrong.

Tests, from the repo root: `python3 -m unittest discover -s testit -t .` (267).
