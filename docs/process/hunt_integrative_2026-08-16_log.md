# Hunt log — `integrative`, 2026-08-16

Direction: long sessions mixing every 0.24.3 feature, checked at
several MOMENTS inside the session rather than only at the end.

Frozen at `1acaddc` via `tools/hunt_probe.py --prepare --name
integrative`. HEAD was still `1acaddc` when this log was written; it
did not move under the hunt. Every probe ran in
`$TMPDIR/weavingspace-hunt/integrative/tree`, never in the working
tree. Probes live in the session scratchpad
(`.../scratchpad/sess.py`, `p1`–`p6`), with `sess.py` holding the
scaffolding and the invariant bank so each probe is the twenty lines
that state its question.

Every case begins from an EMPTY `QgsProject` (`sess.clean_project()`)
and clears it again at the end.

---

## 07:31:04  iteration 1

Question: does the scaffolding drive the dialog the way a user does,
and does each invariant actually RUN rather than skip?

Probe `p1_smoke.py`: 5 moments — generate, pin, copy, class count,
opacity. Two invariants fired. Both were the probe's own fault: with
live update off, a control change does not reach the map until
Generate, so the map legitimately lagged the table. Driver corrected
to press Generate (or to let the live debounce fire and settle) before
each check.

RESULT: ruled out — the two apparent breaks were the fixture.

## 07:44:22  iteration 2

Question: does a 35-step session interleaving every 0.24.3 feature
break any invariant at any moment?

Probe `p2_session.py`. Steps: assign four variables; ramp; opacity;
pin low; pin high; hand-pick a class colour; copy a→b; change b's
class count (the copy degrades to its pins, correctly — the record
went from `{breaks:[…], low:7.0}` to `{low:7.0}`); swap a's and b's
variables where BOTH columns carry nulls; b to Single colour and back
to Quantiles (the no-data split goes and returns); Reverse; a Quant:
Unclassed excursion and back; family; spacing; live update on for a
rotate and an opacity change; c onto a metres-squared column and
pinned there at 1.259e6; copy c→d; d given a numeric column and copied
onto again; outlines on and off; "Create as new group" and off; region
layer switched away and back; ramp, class count, opacity, Categorized
and Equal interval to finish.

35 moments, no invariant broke.

RESULT: ruled out — no defect on this path.

## 07:58:10  iteration 3

Question: the previous session swapped between two region layers whose
columns held similar numbers. What happens when the new region layer
carries the SAME column names over values three orders of magnitude
larger, with a pin and a copied ladder in force?

Probe `p3_session.py`, 17 moments. At the swap the `pin-on-map`
invariant fired and went on firing for six consecutive moments:

    a/v1: low pinned at 7.0, map's first class ends at 12000.0
    a/v1: high pinned at 28.0, map's last class starts at 33000.0

The dialog still held `_pinned_bounds['a']['v1'] = {'low': 7.0,
'high': 28.0}` while the map drew plain quantiles over 5000–40000.
Switching back to the original layer restored the pin correctly, so
the record's keying by element AND field is right; what is wrong is
what the dialog says while the pin cannot be carried.

RESULT: confirmed — carried to iteration 4 for a second route.

## 08:02:51  iteration 4

Question: is that the map being wrong, or the controls? And is the
region-layer swap the only door?

Probe `p4_stale_pin.py`, two doors, each from a clean project:
(A) region layer swapped for one whose `v1` runs 5000–40000;
(B) the same column RETYPED in QGIS's editing session, which is the
door `bridge.make_graduated_renderer`'s own comment was written for.

Both doors, identically:

  * the map is RIGHT — `bridge.py:1901-1904` drops a pin the data can
    no longer carry, judged by the same `pin_problem` a typed bound
    faces, and `pin_problem` refuses the same number outright: "The
    lower class bound must sit between 5000 and 40000, which is what
    the data covers."
  * `_pinned_bounds` still holds `{'low': 7.0}`;
  * the Colour ramp cell still carries its pinned display, so the
    swatch goes on BOXING the end that says "this end is yours";
  * the element layer is still stamped
    `weavingspace_quant_style: {"pinned": {"low": 7.0}}`;
  * nothing is said. The message bar carried only the ordinary
    tile-count and missing-value notices.

`bridge.py:1890-1892` says of this drop: "`pin_problem` is the same
judge the typed bound faces, asked again of the values as they now
are; the DIALOG reports the loss, since bridge draws maps and says
nothing." Grepping every `_report_quietly` and every write of
`_pinned_bounds` in `dialog.py` finds no such site. The dialog has no
counterpart to the drop: `_on_layer_changed` (dialog.py:1782) clears
`_cat_count_cache` and `_nulls_cache` and nothing else, and the
data-version bump reaches the signature but never the pin record.

RESULT: confirmed.

## 08:06:33  iteration 5

Question: a second, INDEPENDENT route — does the stale number survive
into the saved project, so a fresh dialog in a fresh session also
shows a bound the map does not have?

Probe `p5_roundtrip.py`: pin at 7.0, retype the column so it cannot be
carried, Generate, `project.write()` to a .qgz, clear the project
entirely, `project.read()` it back, open a NEW dialog.

    pinned record  : {'a': {'v1': {'low': 7.0}}}
    a: first class ends at 12000.0
       ramp cell shows a pin? True

The number is read back off the layer's own custom property, not out
of any surviving in-memory state, so this is a different mechanism
from iteration 4 reaching the same fact.

RESULT: confirmed.

## 08:08:12  iteration 6

Question: when did it start, and is it a settled decision?

`git log -S "low_pin = high_pin = None" -- weavingspace_qgis/bridge.py`
names `de5f90e` (2026-08-15), "Two fixes toward a data edit reaching
the map". That commit adds the drop and states plainly "No test yet
for either fix". So the defect is not the drop — the drop is right —
it is that the drop landed without the dialog counterpart its own
comment promises. Not in ROADMAP.md, not in CLAUDE.md's settled
decisions; CLAUDE.md's rule reads the other way, that a bound outside
the data is among the things REFUSED. `docs/BUG-REGISTER.md:78` records
the same SHAPE as a defect at a different door: "a pin set on an
element carrying a copied classification was recorded, stamped and
shown as set while the map ignored it".

RESULT: confirmed.

## 08:09:20  iteration 7

Question: does anything else break in a session built round different
variables, a different family and a different spacing?

Probe `p6_session.py`, 35 moments. No invariant broke.

RESULT: ruled out.

---

## Steps run, and how many times each invariant ACTUALLY ran

Seven invariants were asserted at every moment. The counts are summed
over the four session probes (p1: 5 moments, p2: 35, p3: 17, p6: 35 —
**92 moments in all**), and a "run" is one element at one moment, so
one moment contributes up to four runs per invariant.

| invariant | ran | skipped |
|---|---:|---:|
| the map's class breaks match what the table says | 332 | 36 |
| a pinned bound is on the map | 76 | 292 |
| every no-data layer pairs exactly one element layer and shares its opacity | 368 | 0 |
| hatched classes are the ones no tile wears | 332 | 36 |
| layers in the group = elements + splits + outlines | 92 | 0 |
| no element layer is orphaned | 92 | 0 |
| a hand-picked class colour is the colour that class draws in | 36 | 202 |

Nothing scored zero. The thinnest axis is the hand-picked colour one
(36 runs), because a pick survives only until the next ramp or scheme
change clears it by design; the pin axis skips whenever no element
currently carries a pin on its current field, which is most elements
most of the time.

Every skip is a state that did not offer the axis, not a silent pass.
`nodata-pairing`, `group-layer-count` and `no-orphans` never skip at
all, which is what makes their zeros meaningful.

## Traps met

* Two invariant fires in iteration 1 were the probe's own driving: with
  live update off the map is MEANT to lag the table.
* The no-data layer's renderer is a `QgsCategorizedSymbolRenderer`, not
  a single-symbol one (bridge.py:2623, deliberately — it puts the words
  "no data" in the legend), so reading its colour needs `symbols()`.
* `_copy_classification('c','d')` is accepted onto a categorized
  element, which looks alarming until you find `_copy_targets` filters
  categorized rows out of the dropdown, so no user can reach it. Not
  reported.

## Row for HUNT-RECORD.md

| **Long sessions, checked at every moment** | No question — every 0.24.3 feature interleaved, seven invariants asserted after each step and each one COUNTED | 7 | 1 (claimed) | 92 moments across four sessions. Only one axis fired, and only at one ingredient: a pin whose data has moved. Two clean 35-step sessions are the other half of the result. Lesson: the axis that catches something is the one asserting that a CONTROL and the MAP agree, and it fires only if the session makes the data move under a setting the user already made — changing settings against fixed data found nothing in 70 moments. Counting runs per invariant was worth its cost: the hand-picked-colour axis ran 36 times against the no-data axis's 368, which no pass/fail summary would have shown |
