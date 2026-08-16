# Hunt: dead axes in the tests written for 0.24.3

Hunt name `dead-axes`. Frozen copy
`$TMPDIR/weavingspace-hunt/dead-axes/tree` at **1acaddc**; HEAD was
1acaddc at the start and 1acaddc at the report, so it did not move
under me. Nothing in the shared working tree was edited; every
mutation was applied to the frozen copy and reverted immediately
(`scratchpad/mutate.py` restores in a `finally`).

Method: for each test, and for each assertion in it separately, break
the behaviour that assertion names in the frozen copy and run the test
with `tools/hunt_probe.py --run tools/run_some.py <name>`. A test is
credited as live only where a mutation made it FAIL with a message
about the right thing.

---

## 07:56:11  iteration 1

Q: does every test defined for 0.24.3 actually execute?

`tests/run_tests.py` registers tests by hand, one `check("name", fn)`
per test, and CI runs `python3 tests/run_tests.py` (ci.yml lines 241,
538, 719) — that is, `main()`. Static route: parse the file, collect
top-level `test_*` defs, collect the names referenced by `check(...)`.
449 defined, 430 registered, **19 never registered**, each with
exactly one reference in the whole file (its own `def`).

Independent route, execution rather than parsing: `probe_registered.py`
imports the suite, replaces `check` with a recorder, patches `os._exit`
(the suite ends with it) and calls the real `main()`.

    MEASURE main() offered 430 registrations; 449 top-level tests
    defined; 19 never offered

Third route, the project's own tool: `docs/TEST-MAP.md`, regenerated at
9f90293, already prints these 19 under "Not registered — these never
run". Nothing gates on that section, so it has been true and unread.

The 19 (all of them 0.24.3 work, 2026-08-15 and 2026-08-16):

    test_a_class_that_cannot_be_pinned_says_so_in_its_cell
    test_moving_a_bound_off_its_computed_value_pins_it
    test_a_destroyed_dialog_cannot_be_reached_by_a_layer_it_made
    test_an_area_with_no_value_is_drawn_rather_than_left_as_a_hole
    test_no_data_is_one_more_colour_in_the_element_s_editor
    test_the_removal_notice_survives_the_chooser_moving_first
    test_a_negative_scale_factor_mirrors_the_design
    test_keeping_a_result_keeps_both_halves_of_every_element
    test_a_geopackage_carries_the_no_data_opacity_it_was_given
    test_swapping_two_variables_re_cuts_both_splits
    test_the_colour_editor_opens_on_a_column_with_no_values
    test_an_element_sitting_wholly_on_missing_values_still_draws
    test_a_project_opened_under_an_open_dialog_is_not_drawn_over
    test_a_project_opened_under_an_open_dialog_keeps_its_no_data_layers
    test_icon_mode_says_when_an_element_has_no_icon_for_an_area
    test_both_halves_of_an_element_fade_together
    test_changing_to_a_graduated_style_cuts_the_split_it_needs
    test_a_reopened_plugin_does_not_mistake_a_no_data_layer_for_its_element
    test_a_graduated_dock_recolour_survives_the_plugin_being_shut

RESULT: confirmed — 19 tests written for 0.24.3 never execute in the
suite or in CI. Counted three ways (AST reference count, executed
`main()`, and TEST-MAP's own generator), all agreeing on the same 19.

## 07:58:40  iteration 2

Q: do the 19 at least pass when they are run, or are they also broken?

Ran all 19 through `tools/run_some.py` in the frozen copy (one was run
separately first). 18 + 1 = 19 PASS, 0 FAIL. So they are healthy tests
that were simply never wired in — which is why nobody noticed.

RESULT: ruled out — the 19 are not failing tests hidden by
non-registration. They are working tests protecting nothing.

## 08:00:05  iteration 3

Q: what does the non-registration cost beyond the tests themselves?

`tools/mutation_check.py` names a killing test per mutant and verifies
by calling `rt.check(test, getattr(rt, test))` directly (line 3141),
which works whether or not `main()` registers it. Of its 292
catalogue entries, **19 name one of the never-run tests as their only
killer** — two apiece for the destroyed-dialog, the graduated dock
recolour and the negative scale factor. Those 19 mutants are recorded
as caught and would survive a real CI run.

RESULT: confirmed — the mutation catalogue reports 19 mutants as
covered on the strength of tests the suite never runs.

## 08:02:31  iteration 4

Q: today's test 1 — `test_a_hatched_class_hatches_only_itself`,
two assertions.

Axis A, the premise (`len(changed) > 20`). Broke it by making
`_striped_icon` skip the hatching loop (`for index in []`).
FAIL: "hatching class 0 changed only 0 pixels".

Axis B, the subject (`not strayed`). Broke it by deleting the
`setClipRect` — the original defect. FAIL: "hatching class 0 of 5 put
ink in pixel columns [14..28], outside its own stripe (0.0 to 12.8)".

Counted: 5 classes x 64x18 pixels compared against a plain swatch;
both axes compare rendered pixels against an independently computed
stripe interval, nothing against itself.

RESULT: ruled out — both axes live.

## 08:04:12  iteration 5

Q: today's test 2 — the three axes added to
`test_the_report_generators_survive_hostile_docstrings`.

Each of the three tools was reverted to the unanchored matcher, one at
a time, and the test run:

- `tools/test_map.py` `re.search(r"^[ \t]*Regression:", ...)` →
  `"Regression:" in doc`. FAIL: "the map and the register must agree
  about which tests guard a defect; the map marks
  ['test_nested_triple_quotes', 'test_raw_string_docstring',
  'test_says_it_has_no_regression_line', 'test_unicode_docstring']".
- `tools/bug_register.py`, anchor dropped. FAIL: "a docstring that
  NAMES the marker in a sentence ... was registered as guarding a
  defect".
- `tools/check_standards.py`, anchor dropped. FAIL: "the standards
  check demands a [shape] tag for a docstring that carries no defect
  line", naming both `test_nested_triple_quotes` and
  `test_says_it_has_no_regression_line`.

The HOW-map guard added beside the standards axis
(`assert not [p for p in problems if "HOW map" in p]`) is backed by a
real `problems.append("...HOW map could not be read...")` in
`check_regression_shapes`, so the "did the check run at all" question
has an answer rather than a silence.

Counted: the fixture defines 6 module-level tests; the map axis
compares a 4-element set against a 2-element expectation, the register
axis a whole set (not only absences), the standards axis a list of
problems.

RESULT: ruled out — all three of today's added axes live.

## 08:05:50  iteration 6

Q: today's test 3 — `test_support_logic`'s docstring change.

The change removes a `[unrecorded]` tag that only existed to satisfy
the unanchored matcher. It asserts nothing new; the behaviour it
depends on is the three anchors proved live in iteration 5. Its own
body (compat/deps) is untouched by 0.24.3.

RESULT: ruled out — not a test axis; a docstring correction whose
guard is iteration 5's fixture case.

## 08:07:20  iteration 7

Q: the coverage-notice pair. Does
`test_the_coverage_notice_counts_what_the_map_is_missing` compare two
independent things, in both of its loop's branches?

Measured what the axis actually compares by printing it (test
unmodified otherwise):

    MEASURE as_icons=False claimed=5 missing=5 present=15 total=20
    MEASURE as_icons=True  claimed=6 missing=6 present=14 total=20

So neither branch is vacuous (a fixture with nothing missing would let
`claimed = 0` pass against `missing = 0` with no notice at all).
`missing` is read off the output layers' attributes; `claimed` off the
sentence. Broke the tiled count (`coverage["missing"] - 1`): FAIL,
"claims 4 ... map is missing 5".

RESULT: ruled out — live, and the fixture does exhibit the case in
both modes.

## 08:08:35  iteration 8

Q: is the ICON-mode branch of that notice tested by anything?

The icon branch posts a different sentence, from
`bridge.icon_coverage_message`, and the test above greps for
"received no tiles" — which is `coverage_message`'s wording, produced
in icon mode too. So the icon sentence is never read by it.

Mutation 1: `missing_here = max(1, unit_count - featureCount() - 1)`
— the icon shortfall count made wrong.
PASS, PASS (coverage-notice test and icon test both).

Mutation 2: `note = None` where the dialog builds the icon sentence —
the notice removed from the plugin entirely.
PASS, PASS.

`test_icon_mode_says_when_an_element_has_no_icon_for_an_area` calls
`bridge.icon_coverage_message({"a": 12, "b": 12}, 144, 6000.0, "m")`
with a hand-written dict and asserts on the wording. It never opens a
dialog. Every reference to `icon_coverage_message` in the whole test
tree is inside that one test (2 lines); `mutation_check.py` aims no
mutant at it.

RESULT: **confirmed — dead axis.** The test named for the icon-mode
coverage notice cannot fail for the regression it names: the dialog
can stop reporting the notice altogether, or report a wrong count, and
it passes. It is a unit test of the sentence with an undriven caller —
the exact "unit-tested mechanism plus an undriven caller is a
motionless axis" shape the copy-hatching test's own docstring warns
about. And it never runs anyway (iteration 1).

## 08:09:10  iteration 9

Q: `test_unclassed_never_announces_a_reduction`, four assertions.

- Broke the Unclassed exemption (`if unclassed:` → `if False:`) in
  `bridge.classes_the_map_will_draw`. FAIL: "Unclassed was reduced to
  12". (Kills axes 1 and 4.)
- Broke `few_values_message` (always `None`). FAIL: "a classed row
  over three distinct values stopped reporting its reduction". (Kills
  axis 3, the deliberately-opposite end.)

The same silencing mutation also failed
`test_a_copied_ladder_is_not_reported_as_a_reduction`
("a column with fewer values than classes went unexplained").

RESULT: ruled out — both ends live, in two tests.

## 08:09:45  iteration 10

Q: `test_the_constant_notice_counts_the_users_areas`, two assertions.

Reverted the branch to the tiled frame (`constant_source = None`).
FAIL: "the map draws 2 classes and the user was told every area holds
one value: ['... Every area has the same value for 'v' ...']". The
premise assertion (`len(ranges) > 1`) is what makes that reading mean
something and it is stated first.

RESULT: ruled out — live.

## 08:10:05  iteration 11

Q: `test_a_reopened_project_cannot_overwrite_yesterdays_geopackage`,
four assertions.

Reverted the guard to session memory (dropped `would_replace or`).
FAIL: "yesterday's map was overwritten: {'a': 41, 'b': 40, 'c': 41,
'd': 40} became {'a': 113, 'b': 112, 'c': 113, 'd': 112}". `before`
and `after` are both read from the file with a fresh `QgsVectorLayer`,
not from the dialog, so `after == before` is not a value against
itself. The two premise assertions (`before` non-empty,
`second._last_path is None`) state the staging.

RESULT: ruled out — live.

## 08:10:30  iteration 12

Q: `test_a_copy_hatches_the_classes_it_leaves_unreachable`,
four assertions.

Put the swatch back before the restyle (swapped `_restyle_only()` and
`_refresh_preview_colours()`). FAIL: "the swatch was built hatching []
where the map leaves [2, 3, 4] unreachable". The comparison is between
what the swatch was built WITH (recorded through a wrapper that still
calls the original) and `bridge.unworn_classes` computed from the
drawn renderer's bounds — two sources, and the test says in its own
docstring why it does not assert on the mechanism's return value.

RESULT: ruled out — live.

## 08:10:50  iteration 13

Q: `test_a_pinned_bound_can_hold_the_numbers_a_column_carries`,
two assertions across three ladders.

Restored the fixed range (`box.setRange(-1e12, 1e12)`). FAIL: "on
areas in square metres, a bound of 1875000000000.0 came back as
1000000000000.0 (range -1e12 to 1e12, 0 decimals)".

Note on the second assertion, `box.minimum() <= upper <=
box.maximum()`: it executes, and compares real numbers, but it cannot
fail independently — any box that cannot bracket the value has already
clamped it, so the first assertion fires first. Subsumed rather than
dead; harmless, and worth knowing it adds no coverage.

RESULT: ruled out — the axis that matters is live.

## 08:11:10  iteration 14

Q: `test_a_scale_control_steps_over_zero`, four assertions.

Reversed the direction of travel in `_skip_zero_scale`
(`-step if previous > 0` → `step if previous > 0`). FAIL: "stepping
down from 0.02 stopped at 0.02; a user travelling downward must pass
zero". The same mutation left the (never-run)
`test_a_negative_scale_factor_mirrors_the_design` passing, which is
right — that one is about the sign reaching the library, not about
stepping.

RESULT: ruled out — live.

## 08:11:30  iteration 15

Q: `test_the_legibility_check_agrees_with_its_own_distance`,
three assertions.

Changed the hoisted arithmetic in `perception.clashes` from Euclidean
to a mean absolute difference. FAIL: "the search reports 0.9787 where
distance() gives 1.9009; the hoisted arithmetic has drifted".

Counted: axis 1 compares one reported minimum against 2x2x|VISIONS|
calls to `distance`; axis 3 compares 200 random colour pairs x
|VISIONS|. Axis 3 re-implements the hoisted form from `_to_lab` and
`_as_dichromat`, so it cannot see a fault in those primitives (both
sides would move together) — but that is not what it claims to check,
and a change to `distance` itself is caught. Axis 3 is only reached
when axis 1 passes.

RESULT: ruled out — live for what it names.

## 08:11:50  iteration 16

Q: `test_a_reopened_plugin_adopts_the_group_it_last_wrote`,
seven assertions.

Inverted the group ranking (`rank = -int(tail)`), reproducing "adopt
the oldest". FAIL: "the reopened dialog took over the KEPT result,
which the next Generate would overwrite", with both id lists printed.
Its five premise assertions each state their own staging, which is why
the failure names the right thing.

RESULT: ruled out — live.

## 08:12:00  iteration 17 — read but not mutated

Examined by reading only, no mutation run, so no verdict is claimed
for them here: `test_a_pin_still_works_on_a_copied_ladder`,
`test_a_copy_leaves_one_number_in_every_control`,
`test_a_new_project_does_not_inherit_the_last_one_s_pins`,
`test_a_copy_leaves_behind_a_pin_the_data_cannot_carry`,
`test_a_pin_leaves_no_class_for_a_tile_to_miss`,
`test_a_copy_from_unclassed_leaves_the_chosen_count_alone`,
`test_a_copied_ladder_on_one_value_still_wears_its_ramp`,
`test_pinning_redraws_the_window_it_was_typed_into`,
`test_a_refused_pin_reverts_and_says_so`. None shows a
compared-with-itself or silently-skipped shape on the face of it;
every one of them states at least one premise before its subject.

RESULT: inconclusive — not measured. This is where the next hunt in
this direction should start.

---

## Tally

Tests examined with a mutation run: 13 registered + 19 run-but-
unregistered.

- Dead axis, confirmed: **1** —
  `test_icon_mode_says_when_an_element_has_no_icon_for_an_area`
  (iteration 8), which is also one of the 19 that never run.
- Whole tests that cannot fail because they never execute:
  **19** (iterations 1–3), plus 19 mutation-catalogue entries whose
  only named killer is one of them.
- Killed everything aimed at them (the denominator): 12 —
  the hatched swatch (2 axes), the hostile-docstring generators
  (3 axes), the coverage notice (both modes), Unclassed reductions
  (2 ends), the constant notice, the reopened GeoPackage, the copy
  hatching, the pinned bound box, the scale control, the legibility
  hoist, the reopened group.
- One subsumed assertion noted (iteration 13), not dead.

## For docs/process/HUNT-RECORD.md

| **Tests that cannot fail** (2nd) | "Which of the tests written for 0.24.3 would pass with the behaviour broken — and which are never run at all?" | 17 | claimed 2 | Aimed at the 0.24.3 batch rather than one day's. One dead axis: the icon-mode coverage notice is asserted only as a helper called with a hand-written dict, so the dialog can drop the notice entirely and it passes. The larger finding is one level up: 19 of the 449 tests are defined and never registered in `main()`, so they run nowhere — nearly the whole No Data, reopen-under-an-open-dialog and negative-scale feature set — and 19 mutation-catalogue entries name one of them as their only killer. `docs/TEST-MAP.md` has been printing them under "these never run" and nothing gates on it. Lesson: before mutating assertions, check that the test executes; `check()`-by-hand registration is a dead axis at whole-test scale, and the cheapest guard is an assertion in the suite that every top-level `test_*` is registered |
