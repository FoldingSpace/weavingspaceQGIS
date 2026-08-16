# Hunt log — harm-2, 2026-08-16

Direction: backwards from harm. Frozen copy at commit 056d9f3
(`/var/folders/93/.../weavingspace-hunt/harm-2/tree`). Working tree never edited.

Harms I set out from, before reading any source:
1. My hand styling / filter on the No Data layer is destroyed by a Generate.
2. My hand-picked No data colour does not come back when I reopen.
3. A tile with a real value is drawn as a hole (or a hole drawn as a value).
4. A colour means two things because the class ladder moved.
5. My opacity spin box says one thing and the map does another.

## 09:05:00  iteration 1

HYPOTHESIS (harm 3). Today's nudge shrinks the upper bound of every
finite-width range by one ulp. The LAST range's upper bound is the data
maximum. If the nudge touches the last range, the highest value in the
column belongs to no class at all, and QGIS draws a feature with no
matching range as NOTHING. A user's highest-value tiles become holes,
while the legend still shows a top class for them.

PROBE `p1_top_value.py`: four value sets x three schemes through
`bridge.make_graduated_renderer(..., k=5)`; for each distinct value, ask
whether any range contains it (`lo <= v <= hi`, QGIS's own inclusive test).

RESULT: confirmed (first route). The data MAXIMUM is homeless in 3 of 4
sets under Quantiles and 4 of 4 under Jenks. Equal intervals never
produces a degenerate range on these sets, so nothing is nudged and
nothing is lost — which is the scope working as documented.

    Quantiles  [1]*6+[2,3,4,5]   homeless=[5.0]
      ranges  ... ('3.2000000000000002', '4.9999999999999991')
      labels  ... '3.2 - 5'
    Jenks      [10]*8+[20,30]    homeless=[30.0]
      labels  ... '20 - 30'

The 1,5,9 case in the docstring is exactly the case where the top range
is DEGENERATE, so it is left alone and nothing goes missing. That is the
only case measured when the nudge was written, and
`_few_values_layer()` is that same 1,5,9 in both new tests — which is
why nineteen newly registered tests are green over this.

## 09:22:00  iteration 2

SECOND, INDEPENDENT ROUTE. Nothing that reads `renderer.ranges()`:
render the layer through `QgsMapRendererParallelJob` onto a blue
background and read the PIXEL over each tile's centre.

PROBE `p2_pixels.py`, values `[10]*8 + [20, 30]`, Reds, Quantiles, k=5.

RESULT: confirmed. Tile 9, value 30 — the column's maximum — renders
`#0000ff`, the background. It is a hole in the map. Tile 8, value 20,
wears `#67000d`, the DARKEST class, so a reader matching darkest to
highest reads 20 as the top of the data and never sees the 30 at all.

## 09:35:00  iteration 3

Does it reach the path the DIALOG uses — breaks cut once from the whole
region column through `bridge.classification_source` and handed to each
element as `classify_from`?

PROBE `p3_dialog_path.py`: region column `[10]*8 + [20, 30]`, one
element carrying 10, 20, 30.

RESULT: confirmed. Legend reads `10 - 10, 10 - 10, 10 - 10, 10 - 12,
12 - 30`; 10 -> class 1, 20 -> class 5, 30 -> NO CLASS. And the
plugin's own emptiness signal says nothing about it:
`unworn_classes` reports [1, 2, 3], because class 5 is occupied by the
20. The user gets no notice, no hatching, no legend difference — just a
missing tile.

HEAD MOVED under me mid-hunt: 056d9f3 -> d1a7d1e (`A pin the data moved
under is released, and said`). Re-froze and re-ran all three probes at
d1a7d1e; `_nudge_off_shared_bounds` is untouched by that commit and all
three results are identical. The claim is about **d1a7d1e**.

## Harms ruled out

RESULT: ruled out — "the nudge moves ordinary boundary values". Equal
intervals produced no degenerate range on any of the four sets, so
`moved == 0` and no bound shifts. The scope is doing its job; the
failure is entirely inside the scope, at its top end.

RESULT: ruled out — "the nudge fires where the classifier is healthy".
Same measurement: three of twelve scheme/data pairs left every bound
alone.

## Not pursued (no time, and worth someone's next hour)

- The No Data layer's new absence-kind column against a hand-set filter
  that names it.
- Whether the carried-opacity fix has the same twin problem on the
  categorical half as on the graduated half.
