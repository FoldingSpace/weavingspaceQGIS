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
only case measured when the nudge was written.
