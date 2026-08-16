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

## 12:05:00  iteration 6  [note]

HEAD moved twice under this hunt: 056d9f3 -> d1a7d1e -> 7ed95d7
(`The nudge deleted the column's maximum from the map`, which narrowed
`_nudge_off_shared_bounds` and added `test_the_nudge_never_orphans_a_value`)
-> 013ca8f (`Five readers of one question, given one owner`). The copy
was re-prepared each time. **Everything below, and both dead axes, were
re-measured at 013ca8f.**

## 12:14:00  iteration 7  [perturbation]

TRIED: the scope mutant again, now that the nudge has been narrowed —
nudge every finite-width range EXCEPT the last (so no value is
orphaned and the new sibling test has nothing to say), on the product
path, leaving `_nudge_off_shared_bounds` itself pristine.
RESULT: **confirmed, dead axis stands at 013ca8f.**
`test_ordinary_data_keeps_qgis_s_own_breaks` PASSES.
`test_the_nudge_never_orphans_a_value` PASSES.
`test_a_repeated_value_reaches_the_class_that_means_it` PASSES.
Second route, `probe_break.py`, Equal intervals over 0..10 at k=5:
pristine bounds `0..2 | 2..4 | 4..6 | 6..8 | 8..10` and 2.0 draws
#ffffff, 4.0 #d8d8d8, 6.0 #979797, 8.0 #505050. Under the mutant every
boundary value moves up exactly one class — 2.0 #d8d8d8, 4.0 #979797,
6.0 #505050, 8.0 #000000. Four of eleven values change colour on an
ordinary map and no test notices.

## 12:22:00  iteration 8  [perturbation]

TRIED: `test_a_hatched_class_hatches_only_itself`, both assertions.
(a) `for index in hatched:` -> `for index in []:`, so nothing is drawn;
(b) the `setClipRect` removed, which is the shipped regression.
RESULT: ruled out — (a) FAILED on "changed only 0 pixels", (b) FAILED
naming pixel columns 14..28 outside the stripe. Both axes live.

## 12:30:00  iteration 9  [perturbation]

TRIED: `test_icon_mode_says_when_an_element_has_no_icon_for_an_area`.
(a) the per-element count reverted to `element.featureCount()` alone
(dialog.py, the shipped miscount);
(b) `note = None` where the icon notice is raised — i.e. the notice
deleted from the plugin outright, which is the EXACT mutation this
test's own docstring says walked past its previous version.
RESULT: (a) ruled out — FAILED, naming the self-refuting sentence.
(b) **confirmed dead axis.** The test PASSES with the feature deleted.
Its dialog half asserts only that nothing is said when nothing is
missing; the positive case is asserted against
`bridge.icon_coverage_message` with a hand-written dict, exactly as
before the rewrite. `grep` over the suite: `icon_coverage_message` and
"no icon" appear in no other test, so the whole feature is
unguarded.
Second route, `probe_icon.py` (144-unit region, four elements, icon
mode at 6,000): pristine draws 20,736 | 20,592 | 20,736 | 20,592 areas
and the bar carries "elements b, d have no icon for up to 144 of
20,736 areas"; under the mutant the same counts, and the bar carries
nothing.

## 12:40:00  iterations 10-16  [perturbation, batched]

Every remaining assertion of the day's tests, one mutant each.
All RESULT: ruled out (the test failed, naming the right thing).

- `test_the_spinner_outranks_a_value_the_dialog_itself_wrote` —
  `old_no_data_opacity.get(tid) if kept_by_hand else None` ->
  ungated. FAILED: paired half at 1.0 against a spinner reading 40.
- `test_a_hand_styled_no_data_layer_survives_a_re_tile` — BOTH
  directions. Hand renderer never carried -> FAILED (#dddddd for
  #ff00ff); hand renderer ALWAYS carried -> FAILED (the editor's
  #00ff00 never reaches the map). A fix in either direction alone is
  caught.
- `test_a_no_data_colour_comes_home_beside_a_class_colour` — the
  stamp merge given back its field-wide gap question. FAILED: came
  back holding {'0': '#123456'} alone.
- `test_the_split_tells_the_kinds_of_absence_apart` — five mutants:
  kinds collapsed to no-value (FAILED), infinities not split
  (FAILED, 4 rows kept), a text column never split (FAILED),
  `ws_absence` dropped before the frame becomes a layer (FAILED),
  a row dropped in the split (FAILED). Five for five.
- `test_an_infinity_alone_still_asks_for_the_split` —
  `_column_has_nulls` reverted to NULL alone (FAILED, no paired
  layer after the style change); kinds collapsed (FAILED); the
  Graduated-only gate removed (FAILED).
- `test_a_repeated_value_reaches_the_class_that_means_it` — nudge
  removed (FAILED on the middle value), `unworn_classes` reverted to
  the exclusive lower bound (FAILED, [1,2,3,4] reported), ramp
  formula `i/(count-1)` -> `i/count` (FAILED on the ladder).
- `test_an_empty_class_keeps_its_place_and_its_colour` — nudge
  removed. FAILED on the darkest-swatch assertion.
- `test_the_report_generators_survive_hostile_docstrings` — five
  mutants, all FAILED: the `Regression:` pattern unanchored in
  `tools/bug_register.py`, in `tools/test_map.py`, and in
  `tools/check_standards.py`; the HOW map made unreadable; one
  `check()` registration deleted from `main()` (the converse
  assertion named the test by name).
  Not separately exercised: `set(by_test) == {...}` is a widening of
  the assertion two lines above it and fires second. Belt and braces
  rather than dead.
- `test_real_world_data` (the both-halves recount) — the split made
  to drop a row, and `_add_no_data_layer` never called. Both FAILED
  on the `assert dlg._no_data_layer_ids` premise, which is what stops
  the new arithmetic from being the old equality in disguise.

## 12:52:00  iteration 17  [logical]

TRIED: `test_integration_second_dialog_session`, whose count also
became `len(_tile_ids()) + len(_no_data_layer_ids)` today.
RESULT: inconclusive-by-construction. Its fixture has no missing
values — the test's own comment says so — so the added term is
identically zero and the assertion is exactly the one it replaced.
With `_add_no_data_layer` never called at all, it PASSES. Not a dead
axis (the original equality is live), but the new term is decoration
on this fixture and should not be read as coverage of the split.

## Tally

TWELVE of today's tests mutated, 28 mutants, per assertion rather than
per test. TEN killed everything aimed at them. TWO have a dead
secondary axis:

- `test_ordinary_data_keeps_qgis_s_own_breaks` — the assertion that
  is the entire point of the test cannot fail, because its subject is
  a fresh call to `_nudge_off_shared_bounds` on a renderer the product
  has already nudged.
- `test_icon_mode_says_when_an_element_has_no_icon_for_an_area` — the
  rewritten dialog half asserts silence only, so deleting the notice
  from the plugin still leaves it green, which is the same fault the
  rewrite was made to repair.

Two in twelve, against three in fourteen last time. The project's
one-in-five holds.
