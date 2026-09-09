*Part of the Verdi Requiem working notes — this is one dated session entry. The index of all of them is [`README.md`](README.md); the project index is [`CLAUDE.md`](../../CLAUDE.md).*

# 2026-09-09 (b): the notes were split up, and the tests got their own CI

Two housekeeping changes, both prompted by the same observation: the project
had grown past the shape its own tooling assumed.

## `CLAUDE.md` was 2767 lines, and all of it loaded every session

It had become the single file holding every method, every dated finding and
the recurring recipe — 164 kB, about 45 000 tokens read before a session had
been asked anything. It is now a 104-line index: what the user wants, the
*Open* table, the four data directories, the two footguns that must always be
visible, and a pointer per chapter.

**`@import` would not have helped.** Claude Code inlines imported files at
startup, so `@docs/…` improves readability and saves exactly nothing. What
loads lazily is a plain path reference, which is read when needed, and a
skill, whose description line is in context while its body is not. That is
why the references are ordinary paths and why the recipe became a skill.

    docs/tyopaivakirja/     14 dated entries + an index page that also
                            carries *Where things stand*
    docs/menetelmat/        omr, yhdistaminen, kuorotiedostot, harjoitus
    docs/hakemistot.md      the files and the scripts
    docs/ymparisto.md       MuseScore, mutool, Audiveris
    .claude/skills/korvakuulokorjaus/
                            *Recipe: a singer reports a wrong syllable by
                            ear* — loads by itself on a report

**Nothing was rewritten**: lines moved verbatim and only heading levels rose.
Verified by counting rather than by reading — of the old file's 2285 distinct
lines, 28 are absent from the union of the new ones, and all 28 are intended
(the rewritten preamble, the *Open* table's right-hand column now pointing at
paths, one heading that had been broken across two lines, the test count, and
one reworded sentence).

`testit/test_dokumentaatio.py` keeps the split honest: the index stays under
150 lines, every `docs/` file is mentioned somewhere that leads to it, every
markdown link resolves, and nothing points at a `CLAUDE.md` chapter that has
moved. It earned its keep immediately — the work-log index's links were
missing the date prefix, and `docs/suunnitelmat/` had to be excluded as
history rather than as live pointers.

## The tests did run in CI, but not as CI

The tests were a step inside `sivusto.yml` ("Julkaise sivusto"), which
triggers on `push: [main]` and `pull_request`. Two consequences, both real:
**a push to any other branch got no run at all** — and this repo works in
branches — and a failure showed up as a red *publish* job, which is not what
broke.

They are now `.github/workflows/testit.yml`, and `sivusto.yml` calls it with
`workflow_call` and hangs `rakenna: needs: testit` off it, so the site still
cannot publish untested code. That matters specifically because a stale
`LUOTETTAVUUS.md` is a test, and that table is a promise to the reader.

Triggers are arranged so no commit is tested twice: `testit.yml` takes
`push` with `branches-ignore: [main]`, and main and pull requests arrive
through the call.

- **`mupdf-tools` is genuinely a CI dependency, not only a dev-container
  one.** Measured by putting a `mutool` that exits 127 first on `PATH`:
  exactly **15 tests** error out, 241 pass. That is the number the old
  workflow's comment claimed, so the claim was right.
- **The site build needs neither `mutool` nor MuseScore.** Measured the same
  way — `sivusto.py` writes the whole site with both missing. So the apt
  install moved to the test job and the build job installs nothing.
- **Python 3.9 is in the matrix** because `README.md` promises it and CI is
  the only place that promise can be checked. `ast.parse(…,
  feature_version=(3, 9))` over all 22 modules reports no 3.9 syntax errors
  and there are no 3.10+ stdlib APIs in use, so it is expected to pass — but
  it has not been observed passing, see below.
- Cancelling is on per branch, and deliberately **off** on main: there the
  workflow runs as the publish run's first job, and cancelling it would abort
  a deployment that `sivusto.yml` was written to let queue instead.

`testit/test_ci.py` pins all of that, including that the test command matches
the one the documentation gives and that README's promised Python version is
the one the matrix runs. It reads the YAML as text on purpose: the repo has no
dependencies and CI installs none, so `import yaml` would fail exactly where
it needed to work.

## Not verified

The workflows have **not been observed running.** The container's egress
allowlist deliberately excludes `github.com` (see `.jailbee/config.yaml`) and
`gh` is unauthenticated here, so nothing could be pushed or dispatched. The
YAML parses and the structure is pinned by tests; the first real run is the
first push.
