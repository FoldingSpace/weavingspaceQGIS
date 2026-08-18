# Hunt log: the design preview against the map it promises

Direction: the design preview against the map it promises.
Shape: two-stores.
Frozen tree: /var/folders/93/.../weavingspace-hunt/preview-vs-map/tree.
HEAD moved twice under this hunt: 0299c77 -> c924391 -> 5b9d385. The
tree was re-frozen each time and every claim below was re-measured at
5b9d385. Neither intervening commit touched `_table_id_colours` or
`_element_is_deferring`.

## Reading first

CLAUDE.md settled decisions, docs/TESTING.md, docs/TEST-MAP.md and
docs/process/HUNT-RECORD.md read before probing. The record already
counts one confirmed finding in this direction (an unassigned element
previewed in colour and drawn grey, 2026-08-13, fixed) and one claim
that did not reproduce.

Known-deliberate and therefore not defects: opacity floored at
PREVIEW_MIN_OPACITY; "---" draws NO_DATA_FILL; no tile outline in the
design view; shells default 1; the previewed colour is a
REPRESENTATIVE and owes no particular class an equality
(`test_the_preview_agrees_with_the_map_it_predicts` says so).

Candidate two-stores seams found by reading:

* `_table_id_colours` (dialog.py:7424) is the preview's store. It asks
  `a["mode"]`/`a["ramp"]` and calls `bridge.ramp_swatch_colour`.
* `_ramp_cell_icon`'s deferring branch (dialog.py:5385) is the row's
  store, and it samples the LAYER through `bridge.renderer_fill_colours`.
  Those two describe one element and only one of them follows QGIS.

## 14:05:12  iteration 1

Hypothesis: an element restyled in QGIS's Symbology panel into a
renderer no row can name ("deferring") keeps its old ramp colour in
the design view, because `_table_id_colours` has no deferring branch
while the row's swatch does.

Drove a rule-based #00aa44 onto element b's layer and emitted
styleChanged, the way the deferring tests do. Row read "Deferring to
QGIS", ramp combo still read "Blues", `renderer_fill_colours` gave
(0,170,68), and `_table_id_colours` gave #3c8bc2 before AND after.

RESULT: confirmed

## 14:19:40  iteration 2

Second, independent route: rendered PIXELS on both sides, on a project
cleared first and asserted empty. Map through
QgsMapRendererParallelJob over the four output layers; design view
through `preview.grab()`. Neither reading passes through
`_table_id_colours`.

Map painted 49,440 px of #00aa44 and 0 px of #3c8bc2. The design view
painted 15,470 px of #3c8bc2 and 0 px of #00aa44.

RESULT: confirmed

## 14:31:05  iteration 3

Bounding, three arms on one fixture. (A) A NAMEABLE restyle in QGIS
(graduated, Greens): the preview moved #3c8bc2 -> #3ca458, because
`_row_follows_the_renderer` ends in `_refresh_preview_colours`. So the
follow path is sound and the finding is scoped to deferral. (B) The
deferring disagreement SURVIVES a spacing change and a full Generate:
durable, not a missed repaint. (C) A plain single symbol mixed in the
dock diverges too, but that sits under the settled rule that single
symbols are not followed and the row makes no claim -- reported as
context, not as a finding.

RESULT: confirmed (A sound, B durable, C out of scope)

## 14:44:20  iteration 4

The rest of the preview's promises, so the report can say what was
ruled out. Shells: preview polygon count equals
`unit.get_local_patch(r=shells)` at 0/1/2/3 (4, 36, 100, 196). Labels:
all four tile-id anchors lie inside a tile of their own id. Reverse:
the previewed colour stays on the source ramp either way, which is the
settled contract.

RESULT: ruled out

## 14:52:47  iteration 5

Same iteration turned up a second instance of the ONE fault: the
preview ignores `a["range_bounds"]`, the Ramp Display Range. Narrowed
to 0-20% through the four lines the editor's own `range_changed`
runs, the element paints near-white pinks across the map
(#fff5f0 ... #fdcab5) and the design view goes on painting #e7342a.
Pixels both sides: map 8,692 px of #fff5f0 and 0 of #e7342a; design
view 15,460 px of #e7342a and 0 of #fff5f0. 142/255 from ANY pixel the
element paints.

RESULT: confirmed

## 15:06:30  iteration 6

Handback. `tools/probes/preview_paints_colours_the_map_does_not.py`
runs both arms in one go at 5b9d385, each on a project cleared and
asserted empty, both sides read as pixels.

RESULT: confirmed
