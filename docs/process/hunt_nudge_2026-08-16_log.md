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
