# Hunt 3: tests that cannot fail

## 03:42:46 setup
TRIED: read docs/TESTING.md + tests-that-can-fail skill; created worktree hunt3-suite at 8aebd09.
RESULT: 370 test functions in tests/run_tests.py (36k lines).
NEXT: static survey for dead axes, getattr/hasattr guards, empty-comparison risks.

## 03:49:30 test_design_choices_that_leave_nothing_to_colour  -- CONFIRMED DEAD (both axes)
TRIED: (a) inserted `raise RuntimeError` in dialog._legibility_note immediately AFTER the
opt-in gate; (b) separately, made ToggleSwitch.setChecked(True) raise.
RESULT: test PASSED under both breaks. Control tests failed correctly
(test_colour_legibility_warnings_are_opt_in under (a); test_reverse_ramp_column under (b)).
Cause (a): test writes `hasattr(dlg,"opt_warn_legibility")` -- real attribute is
`opt_colour_warnings`, so the warning is never switched on and the gated helper returns None.
Exactly the mod_tiles_inset shape.
Cause (b): `dlg._row_widgets(0)[4]` is cellWidget(row,5), the WRAPPER; hasattr(wrapper,
"setChecked") is False so the guard skips. Also unreachable by design: _sync_row greys AND
clears Reverse on a Single colour row, so _assignments would report reverse=False anyway.
NEXT: the *_under_an_open_colour_editor pair, the ramp-cell/table agreement tests.

## 03:53 attribute-name sweep (mechanical)
TRIED: AST scan of every hasattr/getattr string literal in tests/run_tests.py against all
plugin source. RESULT: exactly ONE plugin-attribute miss -- `opt_warn_legibility` (finding 1).
The other six are genuine Qt API probes. So the mod_tiles_inset shape is not widespread.

## 03:55 test_metamorphic_opacity_round_trip -- CONFIRMED DEAD AXIS
TRIED: replaced both `setOpacity(...)` calls in dialog.py (lines 4360, 5288) with `pass`, so
opacity never reaches any layer.
RESULT: test PASSED. Controls test_element_opacity and
test_an_opacity_set_before_a_run_agrees_with_one_set_after both FAILED correctly.
Cause: snapshot() records (layer.opacity(), top ramp colour); the test never asserts any
INTERMEDIATE value moved, so with opacity severed both sides read 1.0 and agree trivially.
NEXT: test_a_restyle_and_a_reseed_agree, the *_agrees/*_changes_nothing cluster.

## 04:00 three broad product breaks -- families held
TRIED: (1) `bridge.seed_renderer` removed from the _restyle_only fast path;
(2) `_stamp_category_colours` returns immediately; (3) `_report_quietly` returns immediately.
RESULT: (1) all 10 restyle/colour-editor tests FAILED (good). (2) 6 of 9 persistence tests
FAILED; the 3 passers are legitimately about other things. (3) 9 of 10 notice tests FAILED;
the one passer (test_the_cardinality_warning_fires_on_the_side_it_should) reaches its warning
by another route and still asserted its presence. No survivors.
NEXT: preview family, older-generation tests.

## 03:57 ui-vs-library switch severing -- all held
TRIED: severed three switches from the tiling call in dialog.py one at a time:
`retain = False`, `join_proto = False`, `ragged = True`.
RESULT: test_ui_library_slice_modifiers FAILED on both retain and join;
test_ui_library_clipped_edges FAILED on clip. test_ui_library_icons_and_join passed both
times, which its own docstring declares in advance. The "test a switch where it bites"
rule is holding.

## 03:58 close
Examined ~55 tests (read closely and/or run under a deliberate product break).
CONFIRMED cannot-fail: test_design_choices_that_leave_nothing_to_colour (both axes),
test_metamorphic_opacity_round_trip (dead axis).
Minor: test_metamorphic_translation_invariance ends `assert not same_values or True`,
an assertion that is true by construction (declared as a note to the reader).
Worktree left clean at 8aebd09.
