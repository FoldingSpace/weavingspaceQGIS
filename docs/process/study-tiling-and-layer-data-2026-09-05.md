# Study: is there a better way of structuring the tiling and layer data?

(The maintainer's question of 2026-09-05, recorded in ROADMAP.md: "for
efficiency or for fewer defects -- the tiled frame, the per-element
layers and their twins, the records keyed by tile id, the group's
working state". This is an audit that names candidates with a
measurement each. No code was written for it, and none should be in
the same breath as a candidate.)

## What exists, and where each fact lives

A map is one `GeoDataFrame` the worker returns (the TILED FRAME), split
at the landing into one QGIS layer per element plus a no-data twin
where a graduated renderer cannot place some rows. The per-element
CHOICES -- variable, style, ramp, Reverse, class count, class source,
colours, pins, opacity -- live in the dialog as dicts keyed by tile id;
the group's WORKING STATE is those choices plus the design, serialised
to JSON on the group's custom property and, at a Save, into the
GeoPackage's `gpkg_metadata`; every output layer carries STAMPS
(`weavingspace_region` and its element's record) as custom properties;
field-keyed memory is banked PER DATASET; the tiled frame is cached
per geometry key since 2026-09-05.

Measured on `dialog.py` at `c2f89b1`:

    per-element dicts keyed by tile id                 28
    read / write sites, twelve of them sampled        166 / 73
    customProperty sites (stamps)                      50
    writers of the working state                        4
    callers of _geometry_signature                      9
    enumerations of "what a design is"                  5
      (_geometry_signature, _run_signature, _signature,
       WORKING_STATE_DESIGN/ELEMENT, _capture_design)

The defect shape that follows from this is the one CLAUDE.md's records
theme is made of: ONE FACT IN SEVERAL STORES, two of them disagreeing
after an ordinary act. Of the 58 defects in the ledger of 2026-08-28,
54 are in `dialog.py`, and the three narrowings of the geometry
signature each shipped a wrong map that looked right.

## Candidates, cheapest and most durable first

**C4. ONE FIELD TABLE FROM WHICH EVERY SIGNATURE AND WHITELIST IS
DERIVED.** Five enumerations of a design's terms exist, each a hand-kept
list, and `_capture_design` was extracted on 2026-08-31 precisely
because a second definition had drifted. A single table -- field name,
whether it changes the tiles, whether it is symbology, whether it
persists, which moment it is about -- would generate all five, and
adding a control would be one row. Measurement: the terms were widened
three times for a topology edit, the dual and the per-element split's
field, and each fix landed in one function while a second copy went
stale. Cost: small, mechanical, and it removes a class of defect rather
than an instance. Risk: nil to behaviour, since the derived tuples
must equal the current ones, which the suite's signature tests assert.

**C1. ONE ELEMENT RECORD PER ELEMENT.** A dataclass with the fields of
`WORKING_STATE_ELEMENT` replaces the 28 dicts; the whitelist becomes
the class's fields, the restore iterates them, and the "widen the
whitelist in the same commit" rule that has been written down four
times stops needing to be remembered. Measurement: 239 read-and-write
sites across the twelve dicts sampled, so this is a wide edit; the
per-dataset banks become one dict of records rather than a swap of
several. Risk: the rule that WHERE A PATH EDITS IN PLACE THE WIDGETS
ARE THE STATE (`_assignments` reads the combo) means the record must
become what `_assignments` reads, or the split between record and
widget survives with a new name.

**C3. A TILED-MAP VALUE OBJECT.** The frame, its key, the per-element
slices and the twin membership computed once per run and consumed by
the landing. Measurement: `_add_output_layers` is 1,152 lines and reads
the frame, the assignments and some twenty dicts; `split_out_the_no_data`
decides membership per element, and a variable switch moves 0.0% of
tiles on the packaged data and 20.2% on a multi-source shape. The
variable-switch fast path the rulings of 2026-09-05 owe becomes a diff
between two such values, which is the differential those rulings
demand before any code.

**C2. THE GROUP RECORD AS THE ONLY WRITER OF THE LAYER STAMPS.** Stamps
would be derived from the record at every landing rather than written
by four routes. Measurement: 50 customProperty sites and the resume
defect of 2026-09-02, where the group was stamped and the layers were
not. Risk: adoption reads stamps from projects written by earlier
versions, so the stamp stays as a READ format and gains one writer.

## What is not recommended

Moving any per-element state onto a layer or a layer field: ruling 6
of 2026-08-25 holds the file's privacy BY CONSTRUCTION only because the
cache is a plain object on the dialog, and both alternatives were
refused with their reasons (ROADMAP-archived.md, R-89). And a rewrite
in the same breath as a candidate: every one of these touches the
landing, which carries most of this project's rulings, and the suite
has 816 tests, and 527 of the catalogue's 764 entries are anchored on
`dialog.py` lines, each of which a move re-anchors.

## Order

C4, then C1, then C3, with C2 riding on C1. Each begins with the
differential the rulings already require -- feature by feature, field
names included -- run before and after, since the characteristic
failure here is a wrong map that looks right.
