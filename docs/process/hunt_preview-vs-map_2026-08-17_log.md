# Hunt log: the design preview against the map it promises

Direction: the design preview against the map it promises.
Shape: two-stores.
Frozen tree: /var/folders/93/.../weavingspace-hunt/preview-vs-map/tree at 0299c77.

## Reading first

CLAUDE.md settled decisions, docs/TESTING.md, docs/TEST-MAP.md and
docs/process/HUNT-RECORD.md read before probing. The record already
counts one confirmed finding in this direction (an unassigned element
previewed in colour and drawn grey, 2026-08-13, fixed) and one claim
that did not reproduce.

Known-deliberate and therefore not defects: opacity floored at
PREVIEW_MIN_OPACITY; "---" draws NO_DATA_FILL; no tile outline in the
design view; shells default 1.

Candidate two-stores seams found by reading:

* `_table_id_colours` (dialog.py:7424) is the preview's store. It asks
  `a["mode"]`/`a["ramp"]` and calls `bridge.ramp_swatch_colour`.
* `_ramp_cell_icon`'s deferring branch (dialog.py:5385) is the row's
  store, and it samples the LAYER through `bridge.renderer_fill_colours`.
  Those two describe one element and only one of them follows QGIS.
