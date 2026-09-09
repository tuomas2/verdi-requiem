*Part of the Verdi Requiem working notes — the index is [`CLAUDE.md`](../CLAUDE.md).*

# Environment

- **MuseScore 4.7.4**, x86_64 running under Rosetta. Its CLI aborts outright on
  any score that would raise an import warning in the GUI — where the GUI offers
  "Ignore", the CLI just fails and writes nothing. `-f` overrides that; the
  generated files no longer need it, but the raw sources 05 and 16 still do.
  MuseScore has no built-in OMR — "Import PDF" opens musescore.com in a browser.
- `mutool` (mupdf-tools) installed via Homebrew. Used for rasterising and for
  reading text out of PDFs. `poppler` is *not* installed.
- **The MuseScore CLI aborts at teardown, nondeterministically.** Roughly two
  runs in three exit 134 (SIGABRT) with `mutex lock failed` *after* writing a
  complete PDF. It predates this work — the same file converts with exit 0 on
  a retry, and files from earlier commits abort identically. Verify output by
  page count, not by exit status, and do not put `mscore` under `set -e`.
- Tesseract language data for Audiveris lives in
  `~/Library/Application Support/AudiverisLtd/audiveris/tessdata` (eng, ita, lat).
- **Audiveris itself is not installed** — it ran from a temporary directory that
  is gone. Reinstall from github.com/Audiveris/audiveris releases
  (macOS arm64 `.dmg`, ~85 MB, bundled JRE). The DMG's licence prompt cannot be
  answered from a script; either open it in Finder or convert it first:
  `hdiutil convert X.dmg -format UDTO -o X && hdiutil attach X.cdr`.
