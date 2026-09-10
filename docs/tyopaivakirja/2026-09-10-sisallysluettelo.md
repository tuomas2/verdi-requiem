*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-10 (e): a clickable table of contents on the part's first page

The singer asked whether the PDF could carry a clickable contents list on
page 1 — "if it is possible at all" — taking minimal room and certainly not a
page of its own. Halfway through it came back: *not quite that minimal, it may
take half a page*. Both versions were built, and the second one is what
shipped: seventeen rows, movement number, name, dot leader and page number,
each row a full-width link, plus the same seventeen as PDF bookmarks.

It is one new script, [`linkit.py`](../../linkit.py), and `sisallys.py` — which
already knew which page each movement starts on — drives its second half.

## The first version, and why it was thrown away

MusicXML cannot express a link at all, so the contents had to be written into
the finished PDF. The minimal version needed nothing else: page 1 already has
empty space under the title, and two flowed lines of 6.5 pt text fit there
without moving a single note. The layout was measured rather than guessed —
page 1 rasterised at 72 dpi (1 pixel = 1 point), the ink's left and right edge
read off every pixel row, and the text flowed into the rows that were free.
That measurement survived into the shipped version and is what finds the free
space now.

What did not survive is the typography: two dense lines of seventeen entries
separated by `·` is a list you read, not a list you tap.

## Making room, and the four ways that do not

Half a page cannot be taken from the whitespace that happens to be there — the
music has to move down, and only MuseScore can move it. Four attempts,
measured with MuseScore 4.7.4:

| Attempt | Result |
|---|---|
| `<print><system-layout><top-system-distance>` — MusicXML's own element for exactly this | **Ignored.** 200 and 400 tenths both gave a layout identical to none at all |
| Ten empty lines (`"\n"` × 10) in a `<words>` above measure 1 | **No height.** Whitespace-only text reserves nothing |
| A single space at `font-size="100"` | **No height either** |
| Ten lines of real text at 9 pt | **91 pt of room**, and the page count did not change |

So room is reserved by text that has a glyph on it, and `color="#FFFFFF"`
makes it invisible. `linkit.py --varaa` writes one `<direction>` above the
first measure whose `<words>` is *n* lines of `.`, and one 9 pt line pushes the
first staff line down by **about 10.5 pt**. The exact figure does not matter:
`lisaa` measures the finished page and lays the list into what it actually
finds, and if the room is not there it exits with the reason.

Two more measurements shaped the step:

* **The reservation goes after the movement heading**, not before it. Inserted
  first, the heading `I  Requiem & Kyrie` ended up at the top of the page,
  some two hundred points above the staff it belongs to.
* **It costs no pages.** With 10, 20, 24 and 28 reserved lines the bass part
  stayed at 16 pages, because `tiivistys.mss`'s `minSystemSpread` is a
  *minimum* and the rest of the page is shared out evenly: page 1 gives up two
  systems and the other pages have the slack to take them. Over all eight
  parts the cost of the shipped reservation (27 lines, ~283 pt) is **one page
  in one voice** — S II went 17 → 18.

Because the reservation moves page breaks, `--varaa` has to run **before**
`sivuotsikot.py`, which computes the running heads from those breaks. That is
now step 6 of the chain in `YHDISTAMINEN.md`.

## Writing into the PDF, with the only tool that can

`mutool run` — mupdf's JS build — is installed here, and it is the only thing
on this machine that can edit a PDF. Three additions per part: a content
stream with the text, one `/Link` annotation per row with a `/GoTo` to the
right page, and an `/Outlines` tree for the reader's own contents menu.
The text is an embedded Times-Roman (`doc.addSimpleFont`), and its own
`encodeCharacter`/`advanceGlyph` give the metrics, so the dot leaders are
computed from the font rather than eyeballed.

Two traps cost time:

* **MuseScore's own content stream leaves a transform in force.** Qt writes
  `0.06 0 0 -0.06 0 842 cm` at the stream's top level, outside its own `q`/`Q`
  pairs, so text appended after it came out at 6 % size and upside down —
  invisible, and the annotations were fine, which made it look like a font
  problem. The fix is to wrap the old content in a `q` … `Q` of our own; its
  `q`/`Q` counts are balanced (1603 each, measured), so one `Q` restores the
  page's own coordinates.
* **A missing dictionary key is JS `null`, not a null object**, so
  `o.get(key).isBoolean()` throws instead of answering false. And
  `outlineIterator.insert` leaves the cursor *after* the item it inserted, so
  bookmarks must be fed in reading order — fed in reverse, the whole list came
  out backwards.

## Why every step undoes itself first

The list contains **all seventeen movement names on page 1**, and
`sisallys.py` finds a movement's starting page by looking for its name in each
page's text. Left in place, the next run would report every movement as
starting on page 1 — and then write that into the list itself.

So both halves strip their own work before doing it again: the reservation is
found by `id="sisallysvaraus"`, the PDF objects by the key `/VerdiSisallys`,
never by position. `sisallys.py` strips before it reads the text and lays the
list out after, in that order, and a re-run produces a byte-identical file.
`python3 linkit.py --lue stemma-basso-1.pdf` reads back what a reader will
see — 17 links and 17 bookmarks with their target pages — because a written
link is a claim until something reads it out of the file again.

## What is left

Whether the Boox honours either of them. Link annotations and PDF bookmarks
are both ordinary PDF, mupdf renders them and `--lue` finds them, but the only
proof that matters is a tap on the singer's own reader. That question is now
in [`TODO.md`](../../TODO.md).
