# Hunt log: weird-data — the 0.24.3 features on columns nobody would design a fixture around, 2026-08-16

Brief: `python3 tools/bug_hunt_brief.py --area "the 0.24.3 features on
columns nobody would design a fixture around"` (shape: asymmetry), read
in full. CLAUDE.md's settled decisions, its "NULLs are kept out of class
breaks" entry, docs/TESTING.md's four rules, docs/TEST-MAP.md and the
hostile-data section of docs/BUG-REGISTER.md read before starting.

Frozen tree:
`/var/folders/93/3nql803d21v_t9n6f1n8w6000000gn/T/weavingspace-hunt/weird-data/tree`
at **1acaddc**. Probes run via `python3 tools/hunt_probe.py --run <probe>`.
The working tree was never edited except for this log.

DIRECTION: point the 0.24.3 arithmetic (pinned bounds, copied ladders,
the map-wide distinct-value reduction, the No data split, hatching,
negative/zero scale, the icon-mode coverage notice) at columns no
fixture would contain: all-NULL, one-null-in-a-thousand, all-identical,
two distinct values under five classes, 1e-9..1.6e-8 and 1e12..1.6e13,
inf/-inf/NaN, negative only, text-where-a-number-is-expected, all-zero;
then the same columns with a pin on them, a ladder copied onto them,
and a no-data split cut through them. Plus a one-feature region layer,
a layer with no CRS, scale factor exactly zero, and a spacing so coarse
some elements get no tiles.

KNOWN AND NOT A FINDING: QGIS 4.0.3 segfaulting on Jenks over NaN, and
QGIS counting NULL as zero in class breaks. Both are documented
workarounds with canary tests.

## Reading pass, before any probe

Candidates written down before measuring, so a confirmation cannot be
retro-fitted:

- **H1 (icon-mode coverage notice x the No data split).** dialog.py:7057
  computes `missing_here = unit_count - element.featureCount()` over
  `self._element_layer_ids`, which (dialog.py:8049) names ONLY the
  graduated half of an element. `split_out_the_no_data` moves the rows
  whose value is NULL onto a SECOND layer (dialog.py:7896, 8035), so an
  icon-mode element whose column has any gaps has a short featureCount
  by construction. Predicted harm: a false notice naming elements as
  missing icons for areas that in fact carry an icon drawn as no data.
  `test_icon_mode_says_when_an_element_has_no_icon_for_an_area` tests
  only `bridge.icon_coverage_message` in isolation — the exact
  "unit-tested mechanism plus an undriven caller" shape CLAUDE.md
  names.
- **H2 (infinities are neither classified nor split).** `split_out_the
  _no_data` uses `frame[field].isna()` (bridge.py:2560), which is False
  for +/-inf, while `make_graduated_renderer`'s subset clause
  (bridge.py:1989) excludes them from the breaks. An inf row would
  therefore stay on the graduated layer and match no class: a hole, the
  exact harm the split exists to prevent.
- **H3 (the k-reduction runs before pin_problem inside the renderer).**
  bridge.py:1741-1760 reduces `k` to the distinct count, and
  bridge.py:1903 then asks `pin_problem(..., asked=k)` with the REDUCED
  k, whereas the dialog asked it with the row's own count
  (dialog.py:5204). A pin the dialog accepted could be silently dropped
  by the renderer.
- **H4 (numeric-looking text).** `distinct_numeric_count` accepts any
  value `float()` will take, including the string "5";
  `pin_problem`, `classes_the_map_will_draw` and `unworn_classes` all
  require `isinstance(v, (int, float))`. Three readers of one column,
  two rules.
- **H5 (label precision on tiny and huge magnitudes).** bridge.py:1775
  builds `finite` with `abs(float(v)) <= 1e307` and then
  `needed = ceil(-log10(step)) + 2`, capped at 15. At 1e-9..1.6e-8 that
  wants 11 decimals; check the labels QGIS actually writes.

## 07:59:10  iteration 1  [logical]
TRIED:  H1 — icon mode over a column with ONE NULL in 36 areas. Probe
        `p_icon_gap.py`: 6x6 region, `_layer_with_a_gap(n=6, "v1")`,
        all four elements on v1, Quant default, spacing 400, icons on.
RESULT: confirmed. Each element carries 35 graduated + 1 no-data tile =
        36 of 36 areas, i.e. no element is missing an icon for
        anything. The message bar nevertheless read
        "At 400 m spacing, elements a, b, c, d have no icon for up to 1
        of 36 areas, which other elements still draw." — beside
        "1 of 36 areas have no value for 'v1'. They draw as no data".
        Two notices, from one run, contradicting each other; and the
        icon sentence names ALL FOUR elements while claiming other
        elements draw the area, which cannot be true of a set that is
        all of them.
NEXT:   second independent route (pixels, not featureCount), and a
        control run with no NULLs to rule out my own fixture.

## 08:01:35  iteration 2  [perturbation]
TRIED:  H1's second route — PIXELS, not featureCount — plus a control
        with no NULLs. Probe `p_icon_pixels.py` renders each element
        over the bounding box of the one area whose v1 is NULL,
        graduated half alone and then the element entire, on a magenta
        chroma-key canvas; then repeats the whole run on
        `make_region_layer(n=6)`, which has no gaps.
RESULT: confirmed, independently. With the gap: graduated half alone
        paints 0.000 of that area on all four elements; the element
        ENTIRE paints 0.043 / 0.044 / 0.043 / 0.043 — identical to the
        control run's 0.043 / 0.044 / 0.043 / 0.043 for the same area
        with a value. The icon is there. The control run raised NO icon
        notice at all, so neither the spacing, the fixture nor the
        6x6 region explains it: the notice is caused by the NULL alone.
NEXT:   date it, then move on to the rest of the hostile columns.

## 08:02:24  iteration 3  [logical]
TRIED:  when did it start — `git log -S icon_coverage_message` and
        `-S split_out_the_no_data` on dialog.py.
RESULT: confirmed. The split arrived in dd112bf (2026-08-15); the icon
        notice in a330bb5 (2026-08-16), so the notice was written into
        a tree that already had paired layers. Its immediate parent is
        9de8028, "Every count against the library now counts both
        halves of an element" — which fixed three counting sites of
        exactly this shape (in the TEST suite, via `_element_halves`)
        and was followed the same morning by a new counting site in
        PRODUCT code that counts one half.
NEXT:   the hostile columns themselves, at bridge level first.

## 08:04:40  iteration 4  [perturbation]
TRIED:  the hostile columns through the 0.24.3 arithmetic at bridge
        level (probe `p_columns.py`): all-NULL, one-null-in-twelve,
        all-identical, two-distinct, 1e-9..1.2e-8, 1e12..1.2e13,
        inf/-inf/NaN, negative-only, all-zero, zero-and-negatives —
        each plain, with a low pin, with both pins, and with a ladder
        [20,40,60,80] copied onto it. Compared what
        `classes_the_map_will_draw` / `few_values_message` SAY against
        the ranges, labels and colours `make_graduated_renderer`
        actually produces, and `unworn_classes` on top.
RESULT: ruled out, and worth recording as SAFE, for every one of them.
        The notice and the renderer agreed on the class count in every
        case that reaches a map. Specifically measured safe:
        - all identical -> 1 class "7 - 7", coloured from the ramp
          MIDDLE (#fa694c), notice fires; both pins refused with the
          right sentences.
        - all zero -> the same, 1 class "0 - 0", pins refused.
        - two distinct, k=5 -> 2 classes, notice "2 distinct values …
          not 5"; a low pin at the minimum still draws 2.
        - 1e-9..1.2e-8 -> labels carry 10 significant decimals
          ("0.000000001 - 0.0000000032"), NOT the "0 - 0" the label
          precision block exists to prevent. H5 ruled out.
        - 1e12..1.2e13 -> grouped labels, no precision loss, pins
          exact to 3 s.f. of the break.
        - negative only and zero-with-negatives -> breaks, labels and
          the reduction all correct; a pin on the negatives reduces
          from 5 to 3 and SAYS so, with the "between its pinned
          bounds" wording.
        - a copied ladder [20,40,60,80] onto every one of them keeps
          its five classes, fits the outer edges to the receiving
          column, collapses the outer class the documented way, and
          `unworn_classes` names exactly the classes the column cannot
          reach.
        - all-NULL: `classes_the_map_will_draw` says 5 while the
          renderer builds 0 ranges, but that combination never reaches
          a map — `seed_renderer` intercepts it via
          `_anything_to_classify` and draws no-data, and
          `few_values_message` returns None at distinct >= asked. Not
          a finding.
NEXT:   H2, the one shape the sweep could not see from bridge level:
        infinities are not NaN, so does the No data split catch them?

## 08:06:21  iteration 5  [logical]
TRIED:  H2 end to end. Probe `p_inf_hole.py`: a 6x6 region whose v1
        holds +inf, -inf, NaN and NULL in four different areas and
        ordinary values elsewhere; full Generate; then each of those
        four areas rendered on a magenta chroma-key canvas with BOTH
        halves of every element switched on.
RESULT: confirmed. Painted fraction over each area, four elements:
          +inf     0.000  0.032  0.000  0.024
          -inf     0.000  0.033  0.000  0.033
          NaN      0.285  0.280  0.271  0.210
          NULL     0.285  0.242  0.271  0.282
          control  0.258  0.293  0.272  0.255
        The NaN and NULL areas are drawn (the split caught them); the
        two INFINITY areas are holes — the residue is neighbouring
        tiles bleeding into the bounding box. And the only notice the
        run raised was "1 of 36 areas have no value for 'v1'", when
        FOUR areas hold nothing a class can place and TWO of them are
        absent from the map.
NEXT:   a second route that does not use pixels, and a check that an
        infinity survives a real file rather than only the memory
        provider.

## 08:08:05  iteration 6  [logical]
TRIED:  H2's second route, with no pixels in it (probe
        `p_inf_route2.py`): write the hostile region to a real
        GeoPackage with QgsVectorFileWriter, reopen it through OGR,
        drive the dialog off the FILE-BACKED layer, then ask each
        element's renderer `symbolForFeature` per tile.
RESULT: confirmed, independently and more strongly.
        - the GeoPackage stores and returns the infinities unchanged:
          `[inf, -inf, None, None, 0.0]`. (NaN became NULL through
          GPKG, which is why the null count rises to 2.) So this is
          not a memory-provider artefact and reaches a file a user
          could be handed.
        - per element: graduated=239 tiles, no_data=14 tiles, and
          `symbolForFeature` answers None for {'-inf': 8, 'inf': 8}
          — sixteen tiles per element, all of them on the GRADUATED
          layer, none on the no-data layer.
        - the notice read "2 of 36 areas have no value for 'v1'";
          four areas hold nothing a class can place.
        `frame[field].isna()` (bridge.py:2560) is False for +/-inf,
        while the subset clause at bridge.py:1989 keeps them out of
        the breaks — so the split's own stated harm, "an unpainted
        area is a HOLE", is reproduced by the one input it does not
        catch. `test_classification_survives_inf_nan_and_huge` and
        `test_hostile_numbers_are_handled_or_declined` both check that
        the BREAKS survive an infinity; neither asks whether the ROW
        is drawn.
NEXT:   the remainder of the direction, as a sweep.

## 08:09:00  iteration 7  [perturbation]
TRIED:  the rest of the direction in one probe (`p_sweep.py`): a
        region layer of ONE feature; a layer with NO CRS; a text
        column under a Quant style; a scale factor typed as exactly
        zero, then a negative one; and the maximum spacing the box
        allows.
RESULT: ruled out — all five SAFE.
        - one feature: 36 tiles per element, k collapsed to 1, and
          "Every area has the same value for 'v1'" said. Correct.
        - no CRS: the output layers come back with authid '' — the
          EPSG:4326 invention the register already names does not
          recur — and the map is tiled in the layer's own coordinates
          with no warning, as settled.
        - text column: the row resolves to Categorized and the map is
          categorized. NOTE: my first attempt used
          `setCurrentIndex`, which produced no notice and looked like
          a defect; driven the way a user drives it (`activated`) the
          bar says "'landcover' holds text, so it is drawn as
          categories rather than a range of values." The brief's
          warning about driving controls was right, and this is the
          case where it caught me.
        - scale zero: `_skip_zero_scale` holds against all three
          doors — setValue(0.0) -> -0.02, setValue(-0.0) -> +0.02,
          and typing "0" into the line edit + interpretText ->
          -0.02. A negative scale of -1.0 tiles and draws normally
          (14,162 tiles, four elements, correct class reduction).
        - maximum spacing (1e12 m over a 6km region): two of the four
          elements get no layer at all, and the bar says "34 of 36
          areas received no tiles and appear nowhere on the map",
          which is loud enough that nobody would read the map as
          finished.

## 08:09:31  iteration 8  [perturbation]
TRIED:  H1 again with a GENUINE icon shortfall alongside the null, to
        see whether the number the user reads is merely inflated or
        wholly invented (probe `p_last.py`, spacings 400 / 1400 /
        2000, icons on, one NULL in 36).
RESULT: confirmed, and worse than iteration 1 showed. At every
        spacing each element's two halves sum to 36 of 36 areas —
          400:  a 35+1  b 35+1  c 35+1  d 35+1
          1400: a 35+1  b 36+0  c 35+1  d 34+2
          2000: a 34+2  b 36+0  c 36+0  d 34+2
        — so no element is short of an icon anywhere, yet the notice
        fired at all three spacings, and the ELEMENTS IT NAMES CHANGE
        WITH THE SPACING (a,b,c,d then a,c,d then a,d) purely because
        of how many pieces each element's no-data half took. A user
        tuning the spacing therefore watches the "shortfall" appear
        to improve as they coarsen it, which is the opposite of the
        real relationship — and the sentence exists precisely so that
        several spacings can be compared side by side.

## 08:09:31  HEAD check
HEAD is 1acaddc, the same commit `--prepare` froze at 07:58. It did
not move under this hunt; every measurement above is about 1acaddc.

## Findings claimed

**1. In icon mode, any missing value produces a false "no icon" notice
naming elements that are not short of anything.**
`dialog.py:7057` computes `unit_count - element.featureCount()` over
`self._element_layer_ids`, which names only the GRADUATED half of an
element (`dialog.py:8049`); the rows whose value is missing live on the
paired no-data layer (`dialog.py:7896`, `8035-8037`,
`_no_data_layer_ids`). Reproduced at iterations 1, 2 and 8; second
route was pixels, and a control run with no NULLs raised no notice at
all. Introduced by a330bb5 (2026-08-16), whose immediate parent 9de8028
is "Every count against the library now counts both halves of an
element". The suite's own `_element_halves` helper is the thing this
site needed and did not use.

**2. An area whose value is an infinity is drawn by nothing, and the
count of areas "with no value" does not include it.**
`bridge.py:2560` splits on `frame[field].isna()`, which is False for
+/-inf, while `bridge.py:1989` keeps infinities out of the class
breaks — so those tiles stay on the graduated layer and
`symbolForFeature` answers None for every one of them. Measured
sixteen such tiles per element, 0.000 painted over those areas against
0.26 for a control area, on a region reopened from a GeoPackage that
stored the infinities unchanged. `dialog.py:7146-7148` counts only
`is None or str(...) == "NULL"`, so the notice said "2 of 36" where
four areas hold nothing a class can place and two of them are holes.

## Ruled out, so nobody need re-check them

all-NULL column; one-null-in-twelve; all-identical; all-zero; two
distinct values under five classes; 1e-9..1.2e-8; 1e12..1.2e13;
negative-only; zero-and-negatives — each plain, with a low pin, with
both pins, and with a ladder copied onto it (iteration 4). A region
layer of one feature; a layer with no CRS; a text column under a Quant
style; a scale factor typed as exactly zero; a negative scale factor; a
spacing so coarse that two of four elements receive no tiles
(iteration 7). Label precision on tiny and huge magnitudes (H5).
H3 (the k-reduction running before `pin_problem` inside
`make_graduated_renderer`) is unreachable in practice: the only shape
that would expose it — two distinct values with both ends pinned —
is already refused by the "nothing between them to divide" clause at
`bridge.py:1175`, in both the dialog's call and the renderer's.
H4 (numeric-looking text: `distinct_numeric_count` accepts "5" while
`pin_problem`, `classes_the_map_will_draw` and `unworn_classes` demand
`isinstance(v, (int, float))`) is likewise unreachable, because a text
field never reaches the graduated path at all — the correction in
`_assignments` gets there first, and iteration 7 confirms it fires and
says so.
