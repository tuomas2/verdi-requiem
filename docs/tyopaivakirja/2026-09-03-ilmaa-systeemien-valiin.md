*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-03: air between systems, for pencil marks

The singer wanted roughly half a centimetre more between staff systems, to
write in during rehearsal. Measured before and after rather than eyeballed
(`mutool draw` at 200 dpi, then finding the rows of the image that are mostly
dark — that is where the staff lines are):

| | system pitch | systems/page | B I pages |
|---|---|---|---|
| before | 25.1 mm | 10 | 14 |
| **now** (`minSystemSpread` 11.5) | **29.3 mm** | 9 | 16 |
| next step up (13.0) | 33.7 mm | 8 | 18 |

The staff itself is 7.0 mm tall (spatium 1.75 mm, MuseScore's default), so the
writable band between systems went from 18 mm to 22 mm.

Two things worth knowing before touching this again:

- **`minSystemDistance` does nothing here.** The obvious-looking key was tried
  first and changed neither the spacing nor the page count. With vertical
  justification on, `minSystemSpread` is what decides how many systems are
  packed onto a page; the leftover height is then divided evenly. Only that
  one key is in the style file.
- **The value is a threshold, not a distance.** Because the page is justified,
  anything between about 11 and 12.9 gives the same 29.3 mm — you are choosing
  9 systems per page, not a millimetre figure. That is why the request for
  "+5 mm" landed on +4.2 mm: there is no setting between 29.3 and 33.7.

Page margins were left at 15 mm deliberately. Trimming them would buy back
about a third of a system per page, but the margin is itself annotation space,
which is the whole point of the change.
