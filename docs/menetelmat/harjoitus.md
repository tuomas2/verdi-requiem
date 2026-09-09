*Part of the Verdi Requiem working notes — the index is [`CLAUDE.md`](../../CLAUDE.md).*

# The practice file: one visible staff, everything still sounding

`harjoitus.py --stemma "Basso I"` converts the merged score to `.mscz`,
gives every staff an instrument, and hides all staves but the singer's.
The point is that hidden staves still play, so the singer hears the whole
work while reading one line.

Everything here was established by experiment, because MuseScore's file
format is not documented in the app and guessing is expensive:

- **A staff is hidden with `<show>0</show>` inside its `<Part>`** in the
  `.mscx`. Verified by counting glyphs in the exported PDF: the part's
  noteheads and lyrics disappear (Leland 500 → 395, lyric font 140 → 30).
- **Hidden staves still sound.** The MIDI exported from the patched and
  unpatched `.mscz` is note-for-note identical, all 16 tracks.
- **Setting the instrument takes three edits, and missing any one leaves
  the part sounding like a grand piano.** In the `.mscx`, both the
  `<instrumentId>` *element* and the `<Instrument id="...">` *attribute*,
  and in `audiosettings.json`, a track entry pinning the sound. The
  attribute is what `audiosettings.json` refers to; leaving it at
  `grand-piano` while changing only the element silently does nothing.
- **`audiosettings.json` is what the GUI actually plays.** A file coming
  out of MusicXML import has `"tracks": []`, and with that MuseScore plays
  everything as a grand piano no matter what the instruments say. Each
  track needs `partId` (the `<Part id>`), `instrumentId` (the
  `<Instrument id>` attribute) and an `in.resourceMeta` naming the sound:
  `presetProgram`, `presetName`, and `id` of the form `MS Basic\0\<program>`.
  Keep the `partId: "999"` metronome track. The shape was copied from a
  file MuseScore had written itself.
- **The instrument must not be set through MusicXML at all.** Writing
  `<score-instrument><instrument-name>` plus `<midi-program>` into every
  `<score-part>` got through for only two parts of fifteen — the rest
  imported as `keyboard.piano.grand`. Adding `<midi-channel>` changed
  nothing.
- **Instrument ids come from MuseScore's own templates** under
  `Contents/Resources/templates/`, which are unpacked `.mscx` directories:
  `voice.vocals` (program 52, choir aahs), `wind.reed.oboe` (68),
  `keyboard.piano` (0).

      grep -rho "<instrumentId>[^<]*" \
          "/Applications/MuseScore 4.app/Contents/Resources/templates" | sort -u

  That yields 63 ids, a subset of what MuseScore knows. For anything not in
  it, let MuseScore name it: put `<instrument-name>X</instrument-name>` in a
  MusicXML `<score-instrument>`, import once, and read the `instrumentId`
  back out of the `.mscx`. That is how `brass.trumpet.c` was found — it is
  absent from the templates, and unlike their `brass.trumpet.bflat` it does
  not transpose, which is what we want for a reading aid.
- **Staff name and instrument are independent.** The staff still reads
  "Kuoro B" while sounding as a trumpet, so no renaming is needed.
- **The brass staves sound as piano, deliberately.** Tuba mirum has a real
  D trumpet part; leaving it as a trumpet would blur it against the read
  line in the one movement where both play.
- MuseScore's `.mxl` → `.mscz` conversion loses about 1.8 % of the piano's
  MIDI notes (ties), independently of this script. Compare patched against
  unpatched `.mscz`, not against the `.mxl`, when checking for losses.

## The recipe, step by step

If `harjoitus.py` is gone or MuseScore's format has moved on, this is the
whole procedure. Every step was verified on MuseScore 4.7.4.

    # 1. merged score -> MuseScore format, multimeasure rests switched on
    mscore -S tiivistys.mss -o harjoitus.mscz Verdi-Requiem-koko.mxl

    # 2. .mscz is a zip; the score itself is the single .mscx inside
    unzip harjoitus.mscz -d work

Then edit `work/*.mscx`. Each staff is one `<Part ...> ... </Part>` block,
and the staff's name is the **first** `<trackName>` inside it — the
`<Instrument>` further down has a second, empty one. For every block:

- replace `<instrumentId>...</instrumentId>` with the wanted id
- replace `<program value="N"/>` with the wanted program number
- insert `<show>0</show>` straight after the opening `<Part ...>` tag for
  every staff that should be hidden

Repack keeping every other member byte-identical — `score_style.mss`,
`META-INF/container.xml`, the JSON settings and the thumbnail all have to
survive, or MuseScore will not open the file. Python's `zipfile` reading
all members and rewriting only the `.mscx` is the safe way; a plain
`zip -r` over an unpacked directory also works but is easy to get wrong.

**Verifying it.** Three checks, and the second one has a trap:

    # visibility — the hidden parts' glyphs vanish from the printed page
    mscore -o x.pdf harjoitus.mscz
    mutool draw -F stext -o - x.pdf 1 | grep -c '<char'

    # notes still sounding — compare the patched .mscz against the
    # UNPATCHED .mscz, never against MIDI exported from the .mxl
    mscore -o patched.mid harjoitus.mscz
    mscore -o plain.mid   unpatched.mscz

    # which sound each staff plays — MIDI export will NOT tell you, see below
    mscore -o rendered.mp3 harjoitus.mscz

**MIDI export is not a check of the sound.** It reads `<program value>`
from the `.mscx`, so it reported the right instruments while the GUI still
played every staff as a piano. That mistake shipped once. The sound the
user hears comes from `audiosettings.json`.

Rendering audio is the check that works. Do it on a short movement, not on
the merged score — the full 1756 bars take well over ten minutes. Patching
one part of `04-Verdi-Mors_stupebit.mxl` to trumpet and rendering both
versions gave two MP3s of identical length differing in 79 % of their
bytes, with the first difference at the point where the music starts.
Identical hashes would have meant the patch did nothing.

Counting Note On events by scanning bytes for `0x90..0x9F` **gives wrong
answers** — velocity and program bytes collide with the status range, and
two files with different instruments then appear to differ by tens of
notes. Parse properly: variable-length delta times, meta and sysex events
skipped by their declared length, and running status carried over. Done
that way the two files came out identical at 34 034 notes across 16
tracks, which is what proves the hidden staves still sound.
