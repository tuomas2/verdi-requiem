*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-04: seven by-ear reports, and a running movement name per page

The singer read along in rehearsal and reported seven spots plus one feature
request, then confirmed an eighth from this session's own findings. All eight
were real. Six were in movements that had **never had a hand-corrections
table** — 02 (Dies irae), 07 (Rex tremendae), 13 (Sanctus) and 16 (Libera
me) — so those four moved into `korjaa_kasin.py`, and only movement 14 is
still a hand-edited artefact.

| Reported | What was wrong | Settled by |
|---|---|---|
| II·1 t.28, 2nd note an octave lower | `A3` where the choir file has `A2` | the only difference in all 91 bars, plus the same cadence dropping the octave at 32/34/36 |
| II·6 t.366, "me" not "le" | `le,` — a typo for `me,` in "sal-va me" | the chorus soprano sings `me,` on the same beat |
| II·10 t.653, C not G | `G3`♮ | the bass **soloist** and the piano's left hand, in the same file |
| IV t.99–100, "cae-li" missing | t.99 carried no syllable at all | Soprano I has it; A/T/B all lack the same `coe` |
| VII t.72, 2nd note an octave lower | `A3` where the choir file has `A2` | same figure as II·1 t.28 — Libera me opens with the Dies irae theme |
| VII t.98, "di-es" missing | both syllables absent | the alto's identical bar, and the bass's own t.100 |
| VII t.274, "ae" missing | two `<lyric>` on one note, **same** verse number | a `yhdista.py` bug, not data — see below |
| VII t.88, wrong rhythm | second dotted figure on "a ma" instead of "et a" | the choir file, whose neighbouring bars are identical to ours — flagged first, confirmed by the singer, then fixed |

## The one that had been checked and got the wrong answer: Lacrymosa 653

*2026-09-03 (c)* compared this movement's chorus bass against the choir file,
found two differences and resolved **both** in our file's favour. One of those
two was wrong, and the reasoning that made it wrong is worth keeping:

> 653 · ours `G3` · choir `C3` · **ours** — and the printed natural proves it:
> in D♭ major a `C` needs no accidental, a `G` does.

The page really does print G with a natural, re-read from the image and not
misread. But **everything else says C, and three of those live in the same
file**:

- The **bass soloist** (`P4`) doubles the chorus bass at the unison through
  bars 651–652 note for note, and ends on `C3`. The chorus tenor likewise
  doubles the tenor soloist and both end on `G4` — so the doubling holds
  everywhere except this one note, in this one staff.
- The **piano's left hand** plays `C2`+`C3` on that beat.
- The chord is C7 (chorus S/A on `E4`, T on `G4`, piano right hand
  `Bes5-E6-G6`). With the chorus bass on G the root is missing from the choir
  entirely.
- The choir's own MuseScore file has `C3`, and the singer's rehearsal book
  evidently does too.

So the printed CPDL edition has an engraving error in one staff, of the same
kind as the "Lacrymosa dies illa" text error nine bars later — plausibly a
copyist taking the note from the tenor staff, which is where the G♮ belongs.

**The lesson, sharpened.** *2026-09-03 (c)* already concluded that verifying
against the print cannot catch an editorial error. What this adds: when the
print disagrees with the rest of the same file, **the rest of the file wins**,
and the check that decides it is the one that needs no external source at all
— does this note fit what the other staves and the piano reduction are doing
on the same beat? A printed accidental is strong evidence about *which note
the engraver drew*, and no evidence at all about whether he drew the right
one. The 2026-09-03 pass stopped at the first of those questions.

## Two syllables on one note: the part silently dropped one

Bar 274 of Libera me sings "mor-te ae-ter-na" with `te` and `ae` on the same
eighth — an elision. The Sibelius/Dolet source writes that as **two
`<lyric>` elements with the same verse number** on one note, and MuseScore
renders only one of them: the part read "mor - te" and `ae` was simply not on
the page. The source is right about the music, so this is a tool bug, and the
fix is `merge_elisions` in `yhdista.py`: same-verse lyrics on one note are
merged into a single `<lyric>` whose parts are separated by `<elision>`.

Three details that took measurement:

- **The elision character must be a non-breaking space** (U+00A0). A plain
  space is dropped on import and the syllables collide into `teae`; the
  undertie U+203F comes out the same way. Measured by rendering all three and
  reading the PDF's text layer.
- **The same check catches a duplicate.** Movement 16's bar 416 has `me,`
  twice on one note with the same verse number. That is not an elision, it is
  a source error, so the second one is dropped rather than merged.
- Only three notes in the whole work are affected (movement 16's bars 274 in
  two parts, and 416), but the rule belongs in the tool: a data fix would have
  left the soprano soloist's identical bar broken.

Running `merge_elisions` before `normalise_lyrics` also makes the latter more
accurate: "a note carries two lyrics" now means "two rows are genuinely
needed" rather than "possibly an elision".

## A running movement name at the top of every page

The singer's request: *"if every page said, above the first bar, which section
is running, it would help browsing."* The big bold movement title only appears
where a movement starts, so a page opened mid-movement said nothing.

`sivuotsikot.py` writes it, in italic at the bar-number height, and skips the
pages where the movement starts at the first bar (the big title is already
there). Cost: **zero pages** — the label fits in space the bar-number row
already reserves, and all eight parts kept their page counts and
`stemmat-sisallys.txt` came out byte-identical.

**Page breaks are not in the file**, so "the first bar of a page" cannot be
known before layout. Two approaches were tried and one works:

| Approach | Result |
|---|---|
| `<credit page="N">` — MusicXML's own way to place text on a given page, and layout-independent | **MuseScore 4.7.4 ignores it.** Credits set for pages 2 and 3 never reached the PDF |
| MuseScore's page header — is per page | Its text is one string for the whole file, and there is no "current section" macro |
| **Ask MuseScore for the layout, then write the labels** | Works. `mscore -o x.musicxml` exports the *computed* layout as `<print new-page="yes">`, so page starts are read straight out of it |

The two-pass loop is not theoretical: on **two of the eight parts the labels
moved the page breaks**, and the script noticed and did a second round. It
iterates to a fixed point and fails loudly after five rounds.

**Movement detection is by exact text, not by font.** `yhdista.py` now exposes
`osaotsikko()` and `OSAOTSIKOT`, and the label is matched against that list.
The first attempt looked for bold `<words>` and picked up the sources' own
bold directions — Libera me's last page got the heading **"Alle"**. `nayta.py`
had the same bug and now shares the same list; its movement column used to
print `[Alle]` and `[4 soli]`.

## Verification

- Per-staff note counts and the 1807-bar total identical before and after,
  every row — the two pitch changes and five lyric changes move nothing.
- All eight parts and the full score convert without `-f`. Part page counts
  unchanged (S I/S II/T II 17, rest 16); `stemmat-sisallys.txt` unchanged. The
  full score went 362 → 363 pages, from the three syllables that are now
  actually printed.
- 136 tests (85 before, +51), including one pinning *why* Lacrymosa 653 is C
  against its own printed page, one pinning that the first statement of the
  octave-drop figure (II·1 t.24, VII t.68) correctly does **not** drop — it is
  the same in both files, so it must not be "fixed" later — and one pinning
  bar 88's whole rewritten bar, accents included, against the choir file.
- Read back off the rendered `stemma-basso-1.pdf` as images, all seven spots:
  t.28 and t.72 now leap the octave down, t.366 reads "sal-va me,", t.653 sits
  a fifth lower with no natural, t.99–101 read "coe-li et ter-ra", t.98–99
  "di-es ma-gna," and t.274–275 "mor - te ae-ter - na,".

## Three more, from the same conversation

The three items this batch had flagged but not fixed were all confirmed and
fixed the same day.

**Libera me bar 88's rhythm.** Ours was `(♪.♪ ♩)(♪.♪ ♩)`, the choir file
`(♪.♪)(♪.♪) ♩ ♩` — the second dotted figure belongs to "et a", not "a ma".
Both fill the bar and both fit the text, so it had been recorded and left; the
singer confirmed the choir file is right. **This is the case where the choir
file may be believed on rhythm**, because its neighbouring bars 54 and 56 (our
87 and 89) are identical to ours down to the accidentals and the accents, so
the disagreement is exactly one bar wide. The passage is chorus-bass solo (S/A/T
rest through 87–89), so the other voices cannot help, and there is no source
PDF for movement 16.

The choir file settled the **accents** too, which is why it was worth reading
rather than reasoning about: its accents sit on the four beats (notes 0, 2, 4,
5) and the new sixteenth carries none. Ours were on the old rhythm's beats
(0, 2, 3, 5), so one accent moved from note 3 to note 4. The six syllables stay
on the same six notes.

That needed three new operations in `korjaa_kasin.py` — `kesto` (note value,
written `"256/quarter"` → `"192/eighth."`, a period per dot), `lisaa_aksentti`
and `poista_aksentti`. `kesto` drops the note's `default-x` for the same reason
`korkeus` drops `default-y`: it was computed for the old rhythm. Beams needed no
bookkeeping — these sources write no `<beam>` elements at all, so MuseScore
beams by itself.

**`kesto` carries its own safety net.** A single row always looks plausible
while silently lengthening or shortening the bar, so `sovella` snapshots the
per-voice duration sum of every measure a `kesto` row touches and asserts it is
unchanged afterwards. In practice that means rhythm rows come in pairs or
larger groups; the tests are written that way because a lone row cannot be a
valid correction.

**The same gaps in the other voices.** Sanctus bars 99–100 were missing `coe`
in the alto and tenor as well as the bass (the soprano was right all along, and
Choir II sings "Ho-san-na" there and was left alone), and Libera me bar 98 was
missing `di-es` in the chorus tenor. Both are now fixed for all the affected
voices. The tenor's bar 98 has **two** notes where the bass has three, so its
two syllables go one per note — exactly as its own bar 100 already had them.

## Still open from this batch

- The singer said **bar 93** for the missing "di-es"; the bar was **98**. Bar
  93 is correct as it stands ("il-la,"), and the detail that located 98 was
  their own — "on the first and third notes", which only 98 fits. A test pins
  93 so it is not "corrected" later.
- Libera me's chorus bass now matches the choir file **as one 67-bar block**
  (our 44–110) where it used to match in three pieces broken at 72 and 88. The
  only remaining discrepancy in the whole overlap is bars 111–112, and that is
  not a difference: it is the divisi, written as chords by us and as
  `Bass 1`/`Bass 2` by them.
