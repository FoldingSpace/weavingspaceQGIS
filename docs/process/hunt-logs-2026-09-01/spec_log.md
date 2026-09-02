## 07:31:00  iteration 1  [logical]
TRIED:  Read the brief, CLAUDE.md's topology entries and docs/TOPOLOGY.md, looking for a ruling whose justification is a checkable fact about the vendored library.
RESULT: inconclusive -- shortlisted four: dx/dy/push_d are "ABSOLUTE displacements in the unit's own coordinates" (topology_edits.py:104), `n_tiles` "is the library's own count of the unit's own tiles" (topology_tab.py:369), "the library filters supplied kwargs" (topology_edits.py:54), and the re-vendor timing claim.
NEXT:   Read the vendored topology.py for nudge_vertex/push_vertex, because the units claim is the one with a whole control's domain resting on it.

## 07:44:00  iteration 2  [logical]
TRIED:  Is the units claim true? weavingspace_qgis/vendor/weavingspace/topology.py:1488 nudge_vertex -> affine.translate(point, dx, dy); :1467 push_vertex -> push_d * sum(unit vectors).
RESULT: ruled out (the claim is TRUE) -- both are absolute displacements in unit coordinates, exactly as topology_edits.py:100-125 says.
NEXT:   Follow the REPAIR that claim justified. topology_edits.py:120-124 asserts "the multiplication happens at THE ONE PLACE the unit is known" and "a drag already reports itself as a fraction of the unit, so the two now agree by construction". Grep every site that hands arguments to the library and check that "one place" is one.

## 07:45:00  iteration 3  [logical]
TRIED:  Does every path that calls transform_geometry pass through in_map_units? grep: in_map_units is called at topology_edits.py:433 only (inside apply). topology_tab.py:1655 (_on_dragging, the drag PREVIEW) calls self._topology.transform_geometry(..., **whole_where_needed(args)) with args["dx"]/["dy"]/["push_d"] set from the raw drag fractions at :1639-1641.
RESULT: confirmed by reading -- the preview is the second place the library is handed these arguments and it does NOT scale them, so a vertex drag previews at 1/span of what it commits (span ~707 on the design the ruling was measured on). Also noted: the drag's own span is the view's WIDTH (topology_tab.py:1084) while in_map_units uses max(width, height) of unit.tiles.total_bounds (topology_edits.py:141) -- so "agree by construction" is false a second time on any non-square unit.
NEXT:   Measure it. Probe A: same fraction through the preview call and through edits.apply, compare displacement. Probe B (independent route): drive the widget's own mouse events and read the previewed geometry against the committed design.

## 07:46:00  iteration 4  [perturbation]
TRIED:  Measure the gap. Probe A ran the SAME argument mapping through the preview call (topology.transform_geometry with raw fractions, as topology_tab.py:1655 does) and through topology_edits.apply, on laves 3.3.4.3.4 at spacing 500 (span 707.1).
RESULT: confirmed -- nudge_vertex dx=0.2: preview moves 0.2000 map units (0.028% of the unit), commit moves 141.4214 map units (20.0%). Ratio 707.1x, exactly the span.
NEXT:   Reach it a second way, through the widget's own mouse events, because a library-level comparison is not what a person does.

## 07:47:00  iteration 5  [perturbation]
TRIED:  Drive a real drag: click the vertex nearest the middle, grab its nudge handle, QTest.mousePress/mouseMove 30px/mouseRelease, and measure the PREVIEWED unit during the drag against the DESIGN after the drop (both by hausdorff against the starting unit).
RESULT: confirmed, second route -- recorded edit {'classes':'B','how':'nudge_vertex','args':{'dx':0.0876,'dy':0.0}}; preview during the drag moved 0.0876 map units = 0.05 px on a 420px view; the design after the drop moved 61.98 map units = 36.8 px. Ratio 707.1x. The drag is invisible until the button comes up.
NEXT:   Check the second half of the same sentence -- whether the drag's span and in_map_units's span are even the same number.

## 07:48:00  iteration 6  [logical]
TRIED:  The drag divides by the view's WIDTH (topology_tab.py:1084, `_bounds[2]-_bounds[0]`); in_map_units multiplies by max(width, height) of unit.tiles.total_bounds (topology_edits.py:141). Measured both on four designs at spacing 500.
RESULT: confirmed -- laves 3.3.4.3.4 is 557.68 x 707.11, so a committed nudge overshoots the pointer by 1.268x; archimedean 3.12.12 by 1.134x; hex-slice 3 and archimedean 4.8.8 are 1.000x because they are wider than tall. So "the two now agree by construction" (topology_edits.py:123) is false twice over, and the square-unit designs are exactly the examples that would hide it.
NEXT:   Stop rule met. Re-read HEAD (b9551f5, unmoved) and report. Both faults entered with 7d5c589, "The topology tab draws what you just did to it", 2026-08-31, the same commit that introduced _SPAN_RELATIVE.
