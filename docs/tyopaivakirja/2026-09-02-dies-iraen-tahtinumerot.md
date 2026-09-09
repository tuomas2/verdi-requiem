*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-02 (later): the book's own bar numbers for Dies irae

The singer read the choir's rehearsal book and handed over the start bar of
every Dies irae sub-movement. This settles the single longest-running open
question in this file and **changes bar numbers that earlier sections quote**
— see the translation table at the end.

## What changed

`yhdista.py` no longer computes the offsets. `DIES_IRAE_ALUT` now holds the
book's own first-bar number per sub-movement, and the offset is that minus one:

| Sub-movement | computed (old) | book (now) | shift |
|---|---|---|---|
| II·1 Dies irae | 1 | 1 | — |
| II·2 Tuba mirum | 92 | **91** | −1 |
| II·3 Mors stupebit | 141 | **143** | +2 |
| II·4 Liber scriptus | 163 | **162** | −1 |
| II·5 Quid sum miser | 271 | 271 | — |
| II·6 Rex tremendae | 324 | **322** | −2 |
| II·7 Recordare | 386 | 386 | — |
| II·8 Ingemisco | 450 | 450 | — |
| II·9 Confutatis | 507 | 507 | — |
| II·9b Dies irae (kertaus) | 578 | **573** | −5 |
| II·10 Lacrymosa | 629 | **621** → *see below* | −8 |

Six of eleven were wrong, and the error grew to eight bars by Lacrymosa. Note
that 573 is exactly what `Verdi_10bDies_irae.pdf` prints on its own pages — the
source that had been right all along while three other readings disagreed.

> **Corrected 2026-09-03: Lacrymosa's value is 624, not 621.** 621 is where the
> book prints the *Lacrymosa heading*; the CPDL Lacrymosa **file** starts three
> bars later. This section's own framing — "the first bar number per
> sub-movement" — hid the distinction, and it cost the singer three weeks of
> wrong bar numbers in the one movement they were reading. Everything else in
> this section stands. See *2026-09-03 (c): Lacrymosa's three-bar shift*.

## Why the mechanical count was wrong, and why it cannot be fixed by counting

The old offsets were cumulative sums of each source file's own measure count.
That assumes CPDL's per-movement split falls on the same bar as the book's, and
in eight of the ten seams it does not. Measured directly:

- Five seams **overlap**: our earlier sub-movement runs past where the book
  starts the next one (by 1, 3, 2, 5 and 3 bars).
- Three seams have a **gap**: the book has bars that no source file contains
  (3, 1 and 2 bars).

Net, our Dies irae holds 8 more bars than the book counts. This was checked
rather than assumed: the music at every overlapping seam was compared bar by
bar — all parts together, and then the piano parts alone — and **none of it
matches**. So the extra bars are not duplicated content that could be trimmed,
and the gaps are not bars we could recover; the two sets of files simply carve
the piece up differently. Adding or deleting bars would therefore lose or
invent music, so the numbering is fixed per sub-movement instead and the seams
are left discontinuous.

## The seams are discontinuous, and that is deliberate

`yhdista.py` prints the discontinuities on every run (`saumaraportti`) so they
cannot become a silent surprise:

    Dies iraen saumat (numerointi kirjan mukaan, ks. DIES_IRAE_ALUT):
      II·2   alkaa 91, edellinen päättyi 91  -> 1 numeroa toistuu
      II·3   alkaa 143, edellinen päättyi 139  -> 3 numeroa puuttuu lähteistä
      …

**In the reading parts this is invisible**, and that was verified before
committing to the approach: in every one of the five overlapping seams, the
earlier sub-movement's overlapping bars are **chorus rests in all four voices**.
They disappear into a multimeasure rest, and the singer sees nothing but a
section change. The one bar where a chorus voice does sing on a repeated number
is Dies irae's own bar 91 (the final "…surus!"), and the bar it repeats —
Tuba mirum's first — is a chorus rest. Rendered `stemma-basso-1.pdf` page 6
shows the worst case, the five-bar Confutatis→II·9b overlap: a rest block
`[548–576]`, bar 577 rest, then the II·9b title and `573`.

The gaps are equally harmless: all three fall where the following sub-movement
has no chorus at all (Mors stupebit, Quid sum miser, Recordare). Padding them
with rest bars was considered and rejected — it would invent silence the score
does not have, and the practice `.mscz` plays through those seams.

## Translation table for older notes in this file

Every continuous Dies irae bar number written here before 2026-09-02 uses the
old numbering. All such references have been renumbered in place, but if an
old number turns up in a commit message, a comment or the user's memory:

| In | subtract |
|---|---|
| Tuba mirum, Liber scriptus | 1 |
| Rex tremendae | 2 |
| II·9b | 5 |
| Lacrymosa | 8 |
| Mors stupebit | **add** 2 |
| all others | unchanged |

So the old "Lacrymosa bar 674" is now 669, "682–684" is 677–679, "Liber
scriptus bar 240" is 239, and "Rex 369–371" is 367–369.

**A second renumbering hit Lacrymosa on 2026-09-03**: every Lacrymosa number
written between 2026-09-02 and then is three too low, so **add 3**. Combining
both passes, an original pre-2026-09-02 Lacrymosa number changes by −5, not −8.
Numbers quoted in this file have been renumbered in place; the two that moved
twice are "666", now 669, and "674–676", now 677–679.

## Verification

- All eleven sub-movements start on the number the table gives them, read back
  out of the merged score's own `<measure number>` values, not from the table
  that set them. *(Ten of those are the book's section start; Lacrymosa's is
  three bars later — the 2026-09-03 correction above.)*
- Dies irae now spans 1–698 (was 1–706). *(1–701 after the 2026-09-03
  Lacrymosa correction.)*
- Note counts per staff unchanged — only numbering moved. Measure count 1807.
- All eight parts re-rendered; page counts unchanged except T I (15 → 14).
- `test_yhdista.py` pins the book numbers so nobody recomputes them
  "correctly" again, and pins the seam report. 68 tests.
