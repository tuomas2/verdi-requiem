*Part of the Verdi Requiem working notes — the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# Työpäiväkirja

Yksi tiedosto per istunto, vanhimmasta uusimpaan. Merkinnät viittaavat toisiinsa
päivämäärällä (*2026-09-03 (c)*, *2026-09-04*) — alla oleva taulukko kertoo minkä
tiedoston mikä nimi tarkoittaa. Osa myöhemmästä merkinnästä **kumoaa** aiemman;
sellainen on aina merkitty molempiin päihin.

| Merkintä | Tiedosto | Mitä tapahtui |
|---|---|---|
| *2026-08-28* | [`2026-08-28-lacrymosan-kuorobasso.md`](2026-08-28-lacrymosan-kuorobasso.md) | Lacrymosan kuorobasson viimeiset ~30 tahtia: väärä tai puuttuva teksti **luotetussa CPDL-lähteessä**, ei OMR:ssä |
| *2026-08-31* | [`2026-08-31-kolme-korvakuulohavaintoa.md`](2026-08-31-kolme-korvakuulohavaintoa.md) | Kolme korvakuulolta raportoitua kohtaa: Lacrymosa 669 (solistin rivi kuoron viivastolla), Agnus Dei 27–58 (OMR luki väärän viivaston), Liber scriptus 239 (yhä auki) |
| *2026-08-31 (later)* | [`2026-08-31-agnus-dei-kuorobasso.md`](2026-08-31-agnus-dei-kuorobasso.md) | Agnus Dein `Kuoro B` verrattu kuorotiedostoon koko osan yli: 15 virhettä, nolla eroa jäljellä |
| *2026-09-02* | [`2026-09-02-tahtinumerot-ja-osa-i.md`](2026-09-02-tahtinumerot-ja-osa-i.md) | Tahtinumero joka tahtiin, ja neljä osan I kuorobasson sanakorjausta (yksi niistä `yhdista.py`:n bugi) |
| *2026-09-02 (later)* | [`2026-09-02-dies-iraen-tahtinumerot.md`](2026-09-02-dies-iraen-tahtinumerot.md) | Dies iraen osien alkutahdit luetaan kirjasta, ei lasketa: kuusi yhdestätoista oli väärin |
| *2026-09-03* | [`2026-09-03-ilmaa-systeemien-valiin.md`](2026-09-03-ilmaa-systeemien-valiin.md) | Systeemiväli 25,1 → 29,3 mm lyijykynämerkinnöille |
| *2026-09-03 (b)* | [`2026-09-03-liber-scriptus-dies-irae.md`](2026-09-03-liber-scriptus-dies-irae.md) | Kolme ”Di-es i-rae.”-välihuutoa puuttui kaikista neljästä kuoroäänestä |
| *2026-09-03 (c)* | [`2026-09-03-lacrymosan-kolmen-tahdin-siirtyma.md`](2026-09-03-lacrymosan-kolmen-tahdin-siirtyma.md) | Lacrymosan tahtinumerot olivat kolme liian pieniä; koko kuorobasso tarkistettu nuotti- ja tavutasolla, ja painettu laitos osoittautui väärässä tahdeissa 657–665 |
| *2026-09-04* | [`2026-09-04-kahdeksan-korvakuulohavaintoa.md`](2026-09-04-kahdeksan-korvakuulohavaintoa.md) | Kahdeksan korvakuulohavaintoa, kaikki todellisia; osan nimi joka sivun ylälaitaan; edellisen päivän verdikti tahdista 653 kumottiin |
| *2026-09-04 (later)* | [`2026-09-04-julkinen-repo.md`](2026-09-04-julkinen-repo.md) | Repo valmisteltiin julkaisuun: neljä datahakemistoa, `polut.py`, sivusto, historian uudelleenkirjoitus |
| *2026-09-07* | [`2026-09-07-divisin-sanarivit.md`](2026-09-07-divisin-sanarivit.md) | Divisin kaksi sanariviä olivat väärinpäin — ensimmäinen raportti joka koski taittoa, ei tavua |
| *2026-09-07 (b)* | [`2026-09-07-luotettavuustaulukko.md`](2026-09-07-luotettavuustaulukko.md) | Luotettavuustaulukko generoiduksi ja commitoiduksi `LUOTETTAVUUS.md`:ksi |
| *2026-09-07 (b)* | [`2026-09-07-savellaji-tyhjassa-tahdissa.md`](2026-09-07-savellaji-tyhjassa-tahdissa.md) | Palautusmerkki tyhjässä tahdissa oli väärään tahtiin merkitty sävellajin purku; nuottifontin glyyfit mittanauhana |
| *2026-09-09* | [`2026-09-09-suomennokset.md`](2026-09-09-suomennokset.md) | Suomennos joka latinan sanan alle, ja `--teksti`, joka löysi neljä päiviä painunutta virhettä |

## Where things stand

Tämä on kertomusmuotoinen tilannekuva, joka on kasvanut istunto kerrallaan. Se
kertoo mitä on tehty ja varmistettu; **mitä on kesken**, on `CLAUDE.md`:n
*Open*-taulukossa.

Done and verified: the merge, the eight reading parts, the chorus **lyrics**
of the two OMR movements, a practice `.mscz` per singer, and — new — a
previously **entirely missing** ~50-measure passage (the second "Dies irae"
recall, between Confutatis and Lacrymosa) found, OMR'd, and wired in as
movement "II·9b". Its chorus-bass lyrics are checked; everything else about
it is not. Also new: Dies irae's ten sub-movements plus II·9b now number
continuously instead of each restarting at 1, matching how the
choir's rehearsal book numbers that section — and since 2026-09-02 the
sub-movements' start numbers are the book's own, read from it, not computed. Also
new: **movement 11's own chorus bass (Kuoro B) had ~30 measures of wrong or
missing lyrics near the end** — not an OMR file, a genuine bug in the
original CPDL source, undetected until now — found and fixed; see
*Lacrymosa's chorus bass: wrong text, not missing measures*. Also new: three
more chorus-bass spots the user flagged by ear, cross-checked against the
choir's own MuseScore files and (where available) source PDFs — two fixed
(Lacrymosa bar 669's "eis requiem" was the soloists' line copied into the
chorus stave by mistake; Agnus Dei bar 27's wrong clef/register was OMR
reading the wrong staff after the chorus drops out for a solo passage), one
left open pending the physical score; see *2026-08-31: three more chorus-bass
spots the user flagged by ear*. Also new, and the biggest single result so far
for the line the user actually reads: **Agnus Dei's `Kuoro B` has been compared
against the choir's own MuseScore file across the whole movement and now matches
it note for note, with zero differences** — 15 defects found and fixed, closing
the bars 59–74 item that the previous session left open as needing a re-OMR (it
did not); see *2026-08-31 (later): Agnus Dei's chorus bass, whole movement
verified against the choir file*. And new after the choir's first rehearsals:
**the reading parts now print a bar number over every bar** (and the bar range
over every multimeasure rest), because the singer needs to find a single bar on
the conductor's call; plus four chorus-bass lyric fixes in movement I that the
user heard as wrong, one of which was a real `yhdista.py` bug that split a word
across two lyric lines — see *2026-09-02: bar numbers on every bar, and movement
I's chorus-bass lyrics*. Movement 01's hand-corrected file **stopped being a
hand-edited artefact** at the same time: it is now generated by
`korjaa_kasin.py` from a table of eight verified edits, so the whole chain from
the source PDFs to the reading part is reproducible. More by-ear reports are
expected weekly; the method for handling them efficiently is written up in
*Recipe: a singer reports a wrong syllable by ear*. Three more results came out
of the same week. **Dies irae's bar numbers are now the choir book's own**,
read from it rather than computed — six of the eleven sub-movement starts had
been wrong, by up to eight bars at Lacrymosa, which also settles the
longest-running open question in this file; see *2026-09-02 (later)*. The
reading parts got **more air between systems** for pencil marks (25.1 → 29.3 mm)
— *2026-09-03*. And **three chorus "Di-es i-rae." interjections that were
missing from all four voices** in Liber scriptus (bars 229, 231, 233) were
located against the choir file and filled in — *2026-09-03 (b)*. And the
biggest of the week: **Lacrymosa's bar numbers were all three too low**, because
`DIES_IRAE_ALUT` had been given the bar where the book prints the *Lacrymosa
heading* (621) instead of the number the CPDL file's first bar gets (624) — the
two differ only in this one sub-movement, and four other seams may hide the same
mistake. While the singer had asked anyway, **Lacrymosa's whole chorus bass was
then verified**: notes against the choir file (2 differences, both resolved in
our file's favour by the printed page) and every syllable against the source PDF
at note resolution, which closes a long-standing "best-guess melisma placements"
item and found **two** real defects — the divisi upper voice's leftover text at
bars 677–679, and, reported by the singer while this was being written, nine
bars (657–665) where the bass's text should be "huic ergo parce Deus" three
times. That second one is in the **printed edition** too, so no amount of
checking against the page would have found it; what confirmed it was that the
identical motif carries "hu-ic er-go" in the tenor, alto and soprano. Movement 11's hand layer moved into `korjaa_kasin.py` at the same time,
so only movement 14 is still a hand-edited artefact — see *2026-09-03 (c):
Lacrymosa's three-bar shift*.

And newest, 2026-09-04: **eight more by-ear reports, all eight real**, spread
across five movements — two notes an octave too high (II·1 bar 28 and VII bar
72, the same Dies irae figure in two places), a `le,` for `me,` in "sal-va me"
(II·6 bar 366), and three missing syllables (IV bars 99–100 `coe`, VII bar 98
`di-es`, VII bar 274 `ae`). One of the seven is a **reversal of a verdict this
file reached a day earlier**: Lacrymosa bar 653 was checked on 2026-09-03,
found to differ from the choir file, and settled in our file's favour *because
the printed page proves it* — and the page does print G♮, but the bass soloist,
the piano reduction and the harmony in that same file all say C. The lesson
gets sharper: a printed accidental is strong evidence about which note the
engraver drew and none at all about whether he drew the right one. Bar 274 was
a **`yhdista.py` bug**, not data: two syllables on one note (an elision, "mor-te
ae-ter-na") were written by the source as two lyrics with the same verse number,
and MuseScore silently printed only one of them. Four more movements (02, 07,
13, 16) got their first `korjaa_kasin.py` tables, so six of the seven touched
movements are now reproducible and only movement 14 is still hand-edited. The
feature the singer asked for at the same time is in: **every page now carries
the running movement name over its first bar**, at no cost in pages. The three
things that batch had flagged but not fixed — Libera me bar 88's rhythm, and
the same missing syllables in the alto and tenor — were then confirmed and
fixed too, so **Libera me's chorus bass now matches the choir file as one
67-bar block** where it used to match in three pieces. See *2026-09-04*.

And newest, 2026-09-07: **Lacrymosa's divisi had its two lyric rows the wrong
way round** at bars 677–679 — the lower voice's text printed above the upper
voice's, which is backwards both from the source page and from how a singer
reads a divisi staff. The first report in this file that is about layout rather
than about a syllable, and the fix is a new `korjaa_kasin.py` operation,
`sanarivi`. See *2026-09-07*.

And newest, 2026-09-07 (b): a singer's report about **a natural sign standing
in an empty bar** (movement I, bar 59) turned out to be a misplaced **key
signature**: the one-flat key is cancelled at bar 56 on the source page, and
the OMR recorded the cancellation three bars later, at the start of the next
system. That is a whole-file property, not one staff's, so it needed a table of
its own — `SAVELLAJIT` in `korjaa_kasin.py`. The measurement that settled it
reads the **music font's own glyphs** out of the PDF text layer, which is a new
tool in this project and cheap; the same measurement found a second, bigger
instance of the identical OMR failure that is **not** fixed: movement I's
chorus soprano and alto carry the three-sharp key seven bars too long, so their
notes in bars 28–34 are read with sharps that are not there. See
*2026-09-07 (b)*.

And newest, 2026-09-09: **every Latin word now carries its Finnish
translation under it**, in a smaller font, for learning Latin while singing —
the same word-for-word translation the site's text page already had, placed at
the point in the music where the word is sung. It costs the bass parts nothing
and the eight together two pages. Building it needed a real algorithm, because
a gloss goes under a *word* and `syllabic` lies in places: the first version
printed "joka" in the middle of the word requiem, since `qui` is real Latin.
The rule that shipped treats the chain marks as evidence rather than truth.
And the new `python3 suomennos.py --teksti` prints a part's whole text as
running prose, gloss under Latin — a check that cannot be made from the
notation, and the one that found **four defects that had been printing for
days or years**: Lacrymosa's hyphens broken by the 2026-09-03 word rewrite,
`callamitatis`, `no-mi-ni`, and a syllable stranded on lyric row 6 in three
parts. See *2026-09-09*.
