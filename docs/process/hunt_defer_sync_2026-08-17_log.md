# Hunt: controls switched off while an element defers to QGIS

Shape: two-stores. Area: `dialog._refresh_deferring_rows`, and in
particular the exit path added on 2026-08-17 that clears the
`disabled_by_deferring` mark, re-enables the control and then hands
the row to `_sync_row`.

Frozen at 1866338 (`tools/hunt_probe.py --name defer_sync`), which was
still HEAD when this was written. Probes in the session scratchpad:
`p1_cycle.py`, `p2_single.py`, `p3_edges.py`, `p4_pixels.py`,
`p5_control.py`. Nothing in the shared tree was edited.

## 09:41:12  iteration 1

Read the change, `_sync_row`, `_row_mode`, and all five callers of
`_refresh_deferring_rows`. Three records describe one control's
enabled state on this path: the mark, the widget's own `isEnabled`,
and the row's rules inside `_sync_row`. A fourth describes it in
words -- the tooltip -- and nothing on the exit path touches it.

RESULT: inconclusive (reading only; hypotheses below).

## 09:58:40  iteration 2

`p1_cycle.py`: a Graduated row with a class count of 7, ramp Greens,
Reverse ticked, driven through THREE defer/undefer cycles by putting
a rule-based renderer on the element layer and then restoring the
plugin's own clone. Snapshot of every renderer column, the spinner's
range and `user_k`, the ramp text, the switch, the class source, and
of `_class_counts` / `_ramp_choices` / `_reverse_choices` /
`_class_choices` / `_synced_modes` / `_assignments`.

Nothing the user set moved. Cycle 2 and cycle 3 were identical to
cycle 1, so there is no drift. `_sync_row` ran exactly ONCE per
transition (three calls for three cycles), all on the affected row --
no rebuild storm.

RESULT: ruled out (class count, ramp, reverse tick, class source,
drift, and call count).

## 10:04:05  iteration 3

Same probe, tooltips. Coming OUT of deferral the Classes spinner, the
ramp cell and the Reverse cell are re-enabled but still read
"Styled in QGIS; set it in the Layer Styling panel." The Edit-colours
button is the only one restored, and only because `_sync_row` sets its
tooltip unconditionally. The Classes spinner's own text ("Number of
classes; categorized rows show how many categories were found.") is
gone until the next table rebuild.

RESULT: confirmed (minor; a live control telling the user to go and
set it somewhere the next Generate will overwrite).

## 10:19:33  iteration 4

`p3_edges.py`. (A) A Categorized row, whose Classes spinner and
Reverse switch are disabled for their OWN reasons, in and out of
deferral: neither was marked on the way in, so neither was switched
on on the way out. The guard holds. (B) The element's field deleted
in QGIS while it defers: the row re-defaults its variable correctly
and comes back enabled. Both cases ended on a row whose count came
from the layer rather than from `_class_counts`, but the renderer I
restored was the pre-edit one, so that is my fixture and, where it is
not, it belongs to `_row_follows_the_renderer` rather than here.

RESULT: ruled out (already-disabled controls); inconclusive (the
field-deleted case, for fixture reasons).

## 10:41:57  iteration 5

`p2_single.py`. The exit branch is not scoped the way
`_row_follows_the_renderer` was scoped this morning. An element that
defers, and is then given a plain fill in QGIS's dock, has its row
switched to "Single colour" -- which changes the assignment, so the
signature guard no longer protects it. `_sync_row`, running behind
that, replaces the ramp cell with a colour button and writes
`_single_colours[tid]`, so the table now positively asserts a colour
the map does not have. Hand-mixed `#0b1e2d`; the next Generate drew
`#3c8bc2`. Re-run with `_sync_row` silenced (HEAD~1's behaviour): the
map is destroyed the same way, so today's line makes the TABLE lie
but is not the cause of the loss.

RESULT: confirmed.

## 10:52:20  iteration 6

`p4_pixels.py`: the same run scored off the rendered image rather
than the renderer object. Before Generate, 1,764 sampled interior
pixels are `#0b1e2d`. After, 1,926 are `#3c8bc2` and `#0b1e2d` does
not appear at all.

RESULT: confirmed (second, independent route).

## 11:03:48  iteration 7

`p5_control.py`: the identical dock edit on an element that never
deferred. The row stays on "Quant: Equal intervals" and the pixels
stay `#0b1e2d` through the next Generate, which is the settled rule
and is what `test_hand_styling_survives` asserts. So the deferral
round trip is the whole difference.

RESULT: confirmed (cause isolated to the exit branch,
`dialog.py:6810-6838`).
