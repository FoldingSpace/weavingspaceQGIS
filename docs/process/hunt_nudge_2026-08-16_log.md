# Hunt: the class-bound nudge and the withdrawn class reduction

Hunt name `nudge`. Frozen copy at commit 056d9f3
(`/var/folders/93/3nql803d21v_t9n6f1n8w6000000gn/T/weavingspace-hunt/nudge/tree`).
Working tree never edited except for this log.

## 09:05:00  iteration 1

HYPOTHESIS. `_nudge_off_shared_bounds` (bridge.py:1620) shrinks the upper
bound of EVERY finite-width range once ANY range is degenerate. The top
range's upper bound is the column's MAXIMUM. If the top range is
finite-width while a degenerate range sits lower down, the maximum value
ends up above every range, so `symbolForFeature` returns None and the
tile is not drawn at all. The docstring's own worked example ({1,5,9},
Quantiles) ends in a degenerate 9..9, which hides this; the shipped test
`test_a_repeated_value_reaches_the_class_that_means_it` uses only that
scheme and that fixture.

PROBE. `p1.py`: five value-sets x four schemes at k=5, bounds printed
and every feature asked through startRender/symbolForFeature/stopRender
on an empty QgsProject per case.

RESULT: confirmed
Undrawn maxima found in six of twenty cases. Notably on the suite's own
fixture (1,1,5,5,9,9) under **Natural breaks (Jenks)**: bounds end
`5 .. 8.9999999999999982` and the two features holding 9.0 get no
symbol. Also Quantiles on [1,2,5,5,5,5,5,8,20] -> top range
`6.2 .. 19.999999999999996`, 20.0 undrawn. Equal intervals and Pretty
breaks produce no degenerate ranges on these fixtures, so the nudge
never fires there.

## 09:40:00  iteration 2

HYPOTHESIS. If the harm is real it must be visible in an actual RENDER,
not only in `symbolForFeature` -- a second, independent route.

PROBE. `p2.py`: the same fixture (1,1,5,5,9,9) under Natural breaks
(Jenks), k=5, rendered through `QgsMapRendererSequentialJob` onto a
magenta background at 600x90, one pixel sampled per tile.

RESULT: confirmed
Tiles read `#fafafa, #fafafa, #050505, #050505, #ff00ff, #ff00ff`. The
two tiles holding the column's MAXIMUM paint nothing at all -- holes in
the map. Worse, 5.0 paints `#050505`, the DARKEST class, whose legend
label reads "5 - 9". So the legend offers a class for 9, the darkest
swatch is worn by 5, and 9 is not drawn.

## 09:55:00  iteration 3

HYPOTHESIS. How wide is it -- schemes, k from 2 to 20, negatives,
1e-9, 1e12, nulls and infinities?

PROBE. `p3.py`, then `p4.py` which re-runs the same matrix with
`_nudge_off_shared_bounds` monkeypatched to a no-op and DIFFS, so the
nudge's own contribution is isolated.

RESULT: confirmed, with scope
Caused by the nudge: Jenks on (1,1,5,5,9,9) at k=2,3,4,5; Jenks on the
same values scaled to 1e12 at k=3,4,5; Quantiles AND Jenks on
[1,2,5,5,5,5,5,8,20] at every k from 3 (resp. 4) to 20. Adding a null
and an infinity to the column changes nothing -- the split hides them,
the loss is identical.

RESULT: ruled out -- negative values
[-9,-9,-5,-5,-1,-1]: 0 of 76 (scheme, k) pairs lose a value. The top
range there is degenerate, so the top bound never moves.

RESULT: ruled out -- Equal intervals, and Pretty breaks in general
Neither produces a degenerate range on these fixtures, so the nudge
returns 0 and no bound moves.

RESULT: ruled out (not mine) -- Pretty breaks at 1e-9, k=6..8
Every value undrawn, but `p4.py` shows the same loss WITHOUT the nudge.
Pre-existing, and outside this hunt's claim.

## 10:10:00  iteration 4

HEAD moved under the hunt: 056d9f3 -> d1a7d1e ("A pin the data moved
under is released, and said"). That commit does not touch
`_nudge_off_shared_bounds`. Re-prepared and re-ran `p2.py` and `p5.py`
against d1a7d1e.

RESULT: confirmed at d1a7d1e
`p5.py`, the same fixture with and without the nudge:

    nudge=False: {1.0: class 1, 5.0: class 4, 9.0: class 5}
    nudge=True:  {1.0: class 1, 5.0: class 5, 9.0: NO SYMBOL}

Two harms from one cause. The nudge is SCOPED by "is any range
degenerate" but APPLIED to every finite-width range, including the top
one, whose upper bound is the column's maximum -- so the maximum falls
out of the ladder. And where the range above a nudged bound is NOT
degenerate, the boundary value is pushed UP one class, which is exactly
what bridge.py's own "WHY IT IS SCOPED" paragraph says must never
happen. Jenks was correct here before the nudge.

SITE. `weavingspace_qgis/bridge.py`, `_nudge_off_shared_bounds`, the
loop at lines 1673-1678: `for index, (lo, hi) in enumerate(bounds): if
hi > lo: renderer.updateRangeUpperValue(index, nextafter(hi, -inf))`.
It moves a bound whether or not the range above it is degenerate, and
it moves the last one.
