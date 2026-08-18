# Hunt: what a lifted refusal lets downstream (one-boundary)

Frozen copy: /var/folders/.../weavingspace-hunt/lifted-downstream/tree
HEAD moved four times under this hunt: e2976b0 -> 413c186 -> 0c13aa7
-> d5aa26b -> 257b37d. Every claim below re-run at 257b37d.

## 09:10:00  iteration 1
Q: is the legend's LABEL PRECISION sized from the data rather than
from the ladder a pin declares? (bridge.py ~2171-2185 takes log10 of
the DATA's span/k.)
RESULT: confirmed as an arithmetic fact, NOT reported as a defect.
Two elements pinned to the same 6e-10..40 draw the identical ladder
and print different legends: 'rate' reads '0.0000000006 - 13.33333'
and 'pct' reads '0 - 13.3333', so pct's first two classes both begin
at "0". Harm is a coarse legend on a column whose own box cannot
produce such a pin anyway; not worth the maintainer's time.

## 09:35:00  iteration 2
Q: does `classes_the_map_will_draw` lack the Equal-intervals-cut-from-
the-pin exemption `make_graduated_renderer` gained on 2026-08-17?
RESULT: confirmed in the code, ruled out as harm. It has no `scheme`
argument, so it still reduces. `_legend_size_note` cross-checks against
`_classes_nothing_wears` once an output layer exists and the measured
answer wins, so the wrong sentence can only be said before the first
Generate.

## 09:55:00  iteration 3
Q: does a bound of a wildly different magnitude survive the project
save / style round trip? (p3_roundtrip.py)
RESULT: ruled out. QGIS writes 'f' with 15 decimals: 6e-10 goes out as
"0.000000000600000" and comes back bit-identical; no feature changes
class. Breaks below ~1e-15 would round to zero; no realistic column.

## 10:20:00  iteration 4
Q: sweep four columns x five schemes x six pin placements for broken
ladders (p2_sweep.py): backwards classes, gaps, unplaced values, one
colour for many classes.
RESULT: ruled out. Every ladder contiguous and monotonic, every value
placed. Sixteen "count != k" rows are all the documented pin-pool
reduction, or Pretty breaks choosing its own count.

## 10:45:00  iteration 5
Q: with a pin now legally outside the data, do the plugin's own
reports agree with the map? (p4_dialog.py, real dialog, mode driven
through `activated`.)
RESULT: ruled out. Record, stamp, Classes cell, notice, unworn list
and swatch pixels all agree with the layer's renderer.

## 11:15:00  iteration 6
Q: `_retire_an_undrawable_pin` (dialog.py:4487) asks `pin_problem` of
every record. `make_graduated_renderer` (bridge.py:2306) deliberately
does NOT under a copied ladder. Does the unguarded door destroy a copy?
RESULT: confirmed (p5_copy.py). Copy a 5-class ladder pinned at 10 and
90 onto an element whose column has a hole between 10 and 90. The copy
checks each flag ALONE and both pass; the landing asks both TOGETHER
and gets "Those bounds leave nothing between them to divide into
classes", so the WHOLE record is popped -- copied breaks included.
Record is None immediately after the copy; the next Generate draws
0..20.1, 20.1..40.2 ... instead of the copied 0..10, 10..36.7 ...

## 11:35:00  iteration 7
Q: second, independent route, with no dialog in it (p6_second_route.py).
RESULT: confirmed. `make_graduated_renderer` handed exactly the popped
record draws the copied ladder; handed None it draws the scheme's own.
Four of five boundaries differ. Control: a record holding `breaks` and
no flags survives, which isolates the flags as the trigger.
Started at d1a7d1e (2026-08-16), the commit that added the retirement.
