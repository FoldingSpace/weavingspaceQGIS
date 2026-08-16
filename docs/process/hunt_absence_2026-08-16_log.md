# Hunt `absence`: the three kinds of unplaceable value on the No Data layer

Direction: today's widening of the No Data split from `isna()` to "what
the classifier cannot place", and the plugin-owned `ws_absence` column
the paired layer now carries. Everything AROUND the half-built part:
the paired renderer being single-symbol is known and next, and is not
reported here.

Frozen copy `/var/folders/93/3nql803d21v_t9n6f1n8w6000000gn/T/weavingspace-hunt/absence/tree`.
First frozen at **056d9f3**; HEAD moved twice under this run (to
d1a7d1e, then to 7ed95d7) and the copy was re-prepared each time. The
confirmed finding below was first seen at d1a7d1e and re-measured at
**7ed95d7**, where the line is unchanged. The working tree was never
edited; this log is the only file written there.

Method: `tools/hunt_probe.py --run <probe>`, probes kept in the
session scratchpad with a six-line prelude that starts QGIS exactly as
`tools/run_some.py` does and clears the project and the message bar.

## 10:05:00  iteration 1  [read]

TRIED: read `bridge.split_out_the_no_data`, `ABSENCE_KINDS`,
`dialog._needs_a_no_data_split`, `_column_has_nulls`,
`_element_has_missing_values`, `column_has_values`, the coverage and
icon-mode notice loops, and CLAUDE.md's "Adding a thing that PAIRS
with an existing thing". Enumerated every reader of the question "does
this column hold something the classifier cannot place".
RESULT: inconclusive — four readers found, each phrasing it its own
way: the split (isna | non-finite), `_column_has_nulls` (NULL, NaN,
inf — widened today), `column_has_values` (`notna()`), the
missing-values notice (NULL only), `_element_has_missing_values`
(NULL only). Three of the five disagree with the split.
NEXT: measure each disagreement for user-visible harm.

## 10:12:00  iteration 2  [probe p1, p2, p4]

TRIED: an element whose column holds ONLY infinities.
`column_has_values` uses `notna()`, which is True of an infinity, so
the all-missing guard in `split_out_the_no_data` is skipped and the
element's own layer is left with zero rows — the outcome the comment
at bridge.py:2747 calls harmful for the empty-column case. Measured at
bridge level (kept 0 / gone 4, against kept 4 / gone 0 for an all-NULL
column) and through a full Generate with and without a GeoPackage.
RESULT: ruled out — real disagreement, no harm. All four elements
reported `element 0, paired 153` and the map still PAINTS: the tiles
draw in the no-data fill from the paired layer, which is
pixel-for-pixel what the all-NULL branch produces from the element
layer (`distinct_numeric_count` skips non-finite, so an unsplit
all-inf element would take the same `_anything_to_classify` False arm).
The export wrote `tiles_a` with 0 rows and `tiles_a_no_data` with 153
without raising. Cosmetic; not reported.
NEXT: the notices, which are where a count can contradict the map.

## 10:24:00  iteration 3  [probe p3]

TRIED: does `ws_absence` survive a GeoPackage write and a cold reopen?
Generated with a mixed column (2 NULL, 4 +inf, 3 -inf) to a .gpkg, read
the paired layer back through QGIS AND through sqlite3 with the plugin
and QGIS out of the way.
RESULT: ruled out — the column survives intact. sqlite reports
`ws_absence` present on `tiles_a_no_data` with `neg-infinity 3,
no-value 2, pos-infinity 4`, and `v1` on that table still carrying
`(None, 2), (-inf, 3), (inf, 4)`. The three kinds and the values that
produced them both make it into the file.

## 10:33:00  iteration 4  [probe p5]  ** the finding **

TRIED: the missing-values notice against the map it describes, on
three fixtures of 144 areas.
RESULT: **confirmed** — dialog.py:7310 counts `feature[field] is None
or str(feature[field]) == "NULL"`, which is the pre-widening
predicate. Measured:
  * 2 NULL + 4 infinities: bar says "2 of 144 areas have no value for
    'v1'. They draw as no data, outside the class breaks." The map
    draws 9 no-data tiles from 6 spoiled areas.
  * 4 infinities, no NULL: **the bar says nothing at all**, while 7
    tiles are drawn on the paired layer.
  * 2 NULL only (control): "2 of 144", and 2 no-data tiles. Agrees.
A stored NaN is caught by the same gap (`str(nan) == "nan"`), so the
sentence has undercounted since the No Data layer landed and today's
widening made it undercount a second kind.
NEXT: reach the same fact without the attribute predicate.

## 10:38:00  iteration 5  [probe p6, second route]

TRIED: count how many of the USER'S OWN AREAS the map actually draws
as no data, spatially — `pointOnSurface` of every tile on the paired
layer, tested for containment against the region features. A different
mechanism from the attribute scan the notice uses.
RESULT: confirmed — 7 distinct user areas carry no-data tiles (6 of
them spoiled, the seventh a tile straddling a boundary), against the
2 the bar claims. The disagreement does not depend on which route is
used to read the map.

## 10:44:00  iteration 6  [probe p7]

TRIED: (a) the paired layer and `ws_absence` across a project save,
`clear()` and reload; (b) whether the colour editor offers its No data
row before a first Generate on a column whose only gaps are
infinities.
RESULT (a): ruled out — after the reload both paired layers come back
with `ws_absence`, with their kinds (`neg-infinity`, `pos-infinity`)
and with the no-data fill (221,221,221). The boundary is clean.
RESULT (b): confirmed, minor — `_element_has_missing_values`
(dialog.py:6432) is the FIFTH reader and also scans for NULL alone:
False before Generate, True after, on the same unchanged column. So
the No data row is missing from the colour editor until a map exists,
on exactly the columns today's change was about. Reported as a
secondary instance of the same one-line shape, not as its own defect.

## Ruled out, for the next hunt

* `ws_absence` through a GeoPackage write and reopen (iteration 3) and
  through a project save and reload (iteration 6).
* An empty element layer beside a full paired one, and its empty
  `tiles_*` table, on an all-infinity column (iteration 2). Real
  predicate disagreement in `column_has_values`, no harm on the map.
* The icon-mode notice: it already sums BOTH halves
  (dialog.py:7205ff), so infinities on the paired layer do not make it
  fabricate a shortfall.
* The colour editor's list and the legibility check: the paired
  renderer is still single-symbol, so the two placeholder fills in
  `ABSENCE_KINDS` reach no renderer and no clash check can see them
  yet. Nothing to test until the renderer lands — but the pair
  `#8c9fc7` / `#c78c8c` is where to look the moment it does.
* `_column_has_nulls` against the split: agrees on NULL, NaN and both
  infinities. The one route by which they could still differ is a TEXT
  column holding "inf" (to_numeric coerces it, the isinstance guard
  does not), and that column can never be Graduated, so `field_here`
  is None and no split is attempted.
