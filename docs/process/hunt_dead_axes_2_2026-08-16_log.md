# Hunt `dead-axes-2`: which of today's tests would pass with the behaviour broken

Direction: OUR OWN WORK. Roughly a dozen tests were written or
rewritten on 2026-08-16 alongside the fixes they guard. Each is
mutated per ASSERTION, not per test: the behaviour an assertion names
is broken in a frozen copy and the test is re-run to see whether it
notices.

Frozen copy `/var/folders/93/3nql803d21v_t9n6f1n8w6000000gn/T/weavingspace-hunt/dead-axes-2/tree`.
First frozen at 056d9f3; HEAD moved to d1a7d1e (`A pin the data moved
under is released, and said`) mid-run and the copy was re-prepared, so
everything below was re-measured at **d1a7d1e**. The working tree was
never edited; this log is the only file written there.

Method: `tools/hunt_probe.py --run tools/run_some.py <test names>`
against a mutated copy, restoring pristine sources between mutants.

## 11:05:00  iteration 1  [perturbation]

TRIED: `test_ordinary_data_keeps_qgis_s_own_breaks` — kill the guard in
`bridge._nudge_off_shared_bounds` (bridge.py:1676, `if not any(hi <= lo
...)` -> `if False`), so the nudge fires on ordinary data.
RESULT: ruled out — the test FAILED with its own message ("the nudge
fired on ordinary data"). Primary axis live.
NEXT: the assertion's subject is a FRESH call to the helper, not the
renderer the product hands back. Break the scope on the product path
instead.

## 11:12:00  iteration 2  [perturbation]

TRIED: same test — leave `_nudge_off_shared_bounds` untouched and add
an unscoped shrink of every finite-width upper bound immediately after
its call in `make_graduated_renderer` (bridge.py:2186). This is exactly
the harm the assertion's message names.
RESULT: **confirmed dead axis.** `test_ordinary_data_keeps_qgis_s_own_breaks`
PASSES. So do `test_a_repeated_value_reaches_the_class_that_means_it`
and `test_an_empty_class_keeps_its_place_and_its_colour`.
Second, independent route (`probe_nudge.py`, reading the renderer
through startRender/symbolForFeature/stopRender rather than through the
test): on 0..11 in five Quantile classes the pristine bounds are
`0..2.2 | 2.2..4.4 | 4.4..6.6 | 6.6..8.8 | 8.8..11` and every value is
drawn; under the mutant the bounds are all an ulp short and **11.0 gets
no symbol at all** — the map's maximum becomes a hole.
WHY IT CANNOT FAIL: after one nudge no range is degenerate any more, so
the second call the test makes returns 0 whatever the first one did.
The assertion measures an already-nudged renderer and asks whether
nudging it again does anything.
NEXT: the rest of that test's assertions, and the sibling
classification test.

## 11:20:00  iteration 3  [perturbation]

TRIED: `_nudge_off_shared_bounds(renderer)` at the product call site
replaced by `pass` — the nudge never runs.
RESULT: ruled out — `test_a_repeated_value_reaches_the_class_that_means_it`
FAILED ("the middle value draws #d8d8d8, not class 3"), and
`test_an_empty_class_keeps_its_place_and_its_colour` FAILED on its
darkest-swatch assertion. `test_ordinary_data_keeps_qgis_s_own_breaks`
passed, correctly (nothing is expected of it here).
NEXT: the ladder and unworn axes of the same test.

## 11:26:00  iteration 4  [perturbation]

TRIED: `bridge.unworn_classes` containment rule reverted to the
pre-2026-08-16 exclusive lower bound (bridge.py:1507).
RESULT: ruled out — FAILED on `unworn == [1, 3]` ("the hatching reports
[1, 2, 3, 4] unworn"). Axis live.

## 11:31:00  iteration 5  [perturbation]

TRIED: `quant_class_colours` sampling formula changed from
`i / (count - 1)` to `i / count`, so the expected ladder drifts from
QGIS's own.
RESULT: ruled out — FAILED on `colours == expected`. This assertion is
a genuine differential: at (0, 100) with no pin, `make_graduated_renderer`
does NOT recolour, so the renderer carries QGIS's colours and
`quant_class_colours` is an independent description of them.
(A separate mutant re-sampling the `elif` recolour branch changed
nothing, because that branch is not taken at (0, 100) without a pin —
recorded so nobody reads that as a dead axis.)
