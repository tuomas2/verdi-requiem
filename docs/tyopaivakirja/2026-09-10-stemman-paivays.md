*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-10 (b): every part now says when it last changed

The singer asked for a modification date per part on the site, and the same
date small at the top of the PDF's first page. The reason is the Boox: a part
lives on the reader for months, and nothing on the page or on the site said
whether the file in hand was the current one.

It is one new script, `paivays.py`, run last before rendering, and one line
per part on the site.

## The date is not the build date

`yhdista.py` rewrites all eight parts from scratch on every run, so "when was
this file produced" would read today in all eight even when a voice has not
changed in a month — which is exactly the question the date is supposed to
answer. So the date is decided from the content: the new file is compared
against `git show HEAD:` of itself with the stamp taken off both sides, and if
they are equal the old date stays. A changed part gets today.

Consequences worth knowing, both of them intended:

* A fix that is never committed re-dates the part to today on every rebuild.
  That is correct — as far as git knows, the content did change.
* Rebuilding an unchanged part produces no diff at all, so the eight `.mxl`
  files stay quiet in `git status` unless something really moved.

Without git, or for a part not yet tracked, the date is today. That is all
that is known then.

## `<credit>`, and the two things MuseScore does with it

The top of a page belongs to no measure, so the stamp is not a `<direction>`
like `sivuotsikot.py`'s running heads but a `<credit>`, MusicXML's own way of
putting text on a page. Two measurements with MuseScore 4.7.4 shaped it:

* **An untyped credit ignores `default-x`/`default-y`.** It was typeset on
  top of the composer's name at the top right, whatever coordinates it was
  given. `<credit-type>lyricist</credit-type>` honours them, and page 1's
  left margin at the title's own height is where the date sits.
* **One credit in the file stops MuseScore deriving the title and the
  composer** from `movement-title` and `identification/creator` — adding the
  date alone wiped "Messa da Requiem · Basso I" and "Giuseppe Verdi" off
  page 1. So those two are written back as credits as well, but not with
  hand-written coordinates: they are **harvested from MuseScore's own
  export** of the same file, the trick `sivuotsikot.py` already uses for
  layout. Their positions therefore follow `tiivistys.mss`, not a constant in
  the script.

The harvest has to be done on a file **without** our credits: re-exporting a
file that already has them gives coordinates different from the ones
MuseScore actually laid out with (the title came back as `justify="right"` at
the composer's x). So a rerun strips first, then exports, then writes. That
makes the script idempotent, and a test pins it.

Page breaks and page count do not move — a credit is absolutely positioned
and takes no space from the music. Measured by comparing the `new-page`
measures of the export before and after, and the page counts of all eight
parts against `stemmat-sisallys.txt`: 18, 17, 16, 16, 17, 17, 16, 16, the
same as before.

## One stamp, two readers

The visible text is generated from `<identification><encoding><encoding-date>`
in the same file, and the site reads that element rather than the rendered
words — no parsing a Finnish date back into numbers, and no way for the page
to show a different day than the PDF it links to. `sivusto.py` prints it under
each download link in the smallest, palest type on the page; a part with no
stamp gets no date rather than a guessed one.

`testit/test_paivays.py` (23 tests) covers the date choice against a faked git
version, the strip/rewrite cycle, the credit set — including that the export's
own credits come along, which is the thing that would silently cost the title
— and that all eight published parts really carry a date.
