# Test campaign, ordered 2026-08-09 (late night)

PROGRESS: BUILD PHASE COMPLETE. All areas done and green — A(3,
one real bug: tiles-as-areas notice), B(3), C(4, two real bugs:
mid-run dock adoption, retired-dialog watcher), D(3), E(3), F(2),
G(7), H(sample scaling + test, loud skip, stage logs, final charts,
baseline tag pre-0.24.0, CLAUDE.md), item 0 (instrumentation flake)
— plus, mid-campaign, the user's legibility report: the opt-in gate
verified sound on every drivable path, the old guard test found
VACUOUS on its silent side and strengthened (clashing fixture,
positive control, exact count), and a real duplicate found and fixed
(checked-box warnings reached a real bar twice). Five proven
mutation entries this campaign (mid-run-dock-edit-forgotten,
retired-dialog-keeps-watching, missing-count-counts-tiles,
legibility-check-ignores-the-box, legibility-warning-arrives-twice).
Suite now 250 tests, 52 guarding real defects. LATE ADDITIONS, all
proven: the user's second legibility sighting -> the gate now lives
inside _legibility_note (single choke point, every caller inherits
it); spatial indexes (memory layers indexed at creation, GPKG
SPATIAL_INDEX explicit, and the stale provider-cache on the first
GPKG layer fixed with reloadData after all writes -- the new test
caught that); the _finish_run re-examination gained a
signature-equality guard after it broke three race tests by adopting
a mid-run USER change as a dock edit (the guard: only re-examine
elements whose table state has not moved). Suite counts: 251
registered checks, 54 guarding real defects. REMAINING: the gated
chain (suite -> sharded sweep -> overnight) is ARMED in one
background command that stops at the first red stage; then the
wrap-up report, then campaign 2 (designed, in
dev/test-campaign-2-2026-08-09.md, NOT started) on the user's go.

User instruction, verbatim in effect: when tonight's RC finishes, go
down this list and DO NOT TERMINATE until all of it is done — add the
tests, see whether they pass, fix the bugs they find. Only AFTERWARDS
run the prescheduled measurements (the sharded catalogue sweep, then
dev/overnight.sh), and the antimeridian/units area is explicitly
EXCLUDED. This file is the durable copy of the plan; if the session
compacts, resume from here.

Standing rules apply throughout: docs/TESTING.md and
.claude/skills/tests-that-can-fail before writing; every new
behaviour changed while fixing gets a mutation-check entry proved to
fail; any new user-facing string goes to the text-review queue for
the USER to approve (never self-approve); regenerate TEST-MAP and
BUG-REGISTER at the end; suite edits only while nothing re-imports
run_tests.py.

## A. Legend and notice honesty — 3 tests

1. `test_every_legend_says_what_its_map_does` — table-driven family
   over the seedable renderer matrix (graduated: quantiles, equal,
   jenks, pretty, unclassed; categorized; single) × data pathologies
   (well-formed, constant, nulled, heavily tied, high-cardinality):
   legend labels arithmetically match their breaks, class count is
   what the table promised, no duplicate or empty labels, the
   catch-all is labelled, a single class wears the window midpoint.
2. `test_every_notice_describes_the_map_it_came_from` — family over
   the notice-producing paths (constant column, missing values,
   discarded picks/colours, restored display range, follows-ramp,
   keeps-colours, no-classes-to-colour, areas left out): each
   notice's numbers and names match the map state it describes.
3. `test_a_restyle_and_a_reseed_agree` — metamorphic: legend and
   colours after the restyle fast path equal those after a full
   regeneration of the same settings.

## B. QGIS edit sessions and undo — 3 tests

4. `test_an_edit_session_rolled_back_changes_nothing` — startEditing,
   change values, rollBack with the dialog open: record, signatures
   and map unchanged; no spurious regeneration.
5. `test_a_committed_edit_session_reaches_the_map` — in-session
   changeAttributeValues + commitChanges: the fingerprint notices and
   the regenerated map carries the new values.
6. `test_undo_inside_a_session_behaves_like_rollback` — edit, undo to
   clean, commit: equivalent to never having edited.

## C. Watcher interleavings — 4 tests (bug fixes expected)

7. `test_a_dock_edit_while_the_editor_is_open` — styleChanged lands
   while the colour editor is open: record stays coherent, no crash,
   Custom correct after close.
8. `test_a_dock_edit_during_a_run_is_not_lost` — KNOWN GAP: a dock
   edit mid-run is ignored by the watcher (_task guard) and the
   landing run preserves the renderer without adopting it, so the
   cell is not Custom. Fix: after _add_output_layers, re-examine
   preserved layers and adopt divergence once.
9. `test_a_retired_dialog_stops_watching` — SUSPECTED BUG: a retired
   instance's styleChanged connections may still fire alongside the
   live dialog's (double adoption, double notices). Fix: gate or
   disconnect on retirement.
10. `test_staggered_dock_edits_during_a_run` — delay sweep across run
    phases; invariant: record converges to the layer, exactly one
    notice per real divergence.

## D. Persistence as hostile input — 3 tests

11. `test_hostile_stored_properties_never_break_adoption` — corpus of
    malformed weavingspace_category_colours / weavingspace_quant_style
    payloads (bad JSON, wrong types, missing/extra keys, lo>hi,
    out-of-range indexes, huge, unicode): dialog opens, adopts
    nothing partial, never crashes.
12. `test_a_hostile_class_source_leaves_automatic_colours` — corpus
    of broken QMLs (truncated XML, wrong renderer type, empty,
    non-UTF8): element falls back to automatic, told once, no crash.
13. `test_stamped_records_round_trip_through_a_real_qgz` — save an
    actual .qgz with customization, reload it cold, everything
    restored (goes beyond the custom-property unit tests: the whole
    file cycle).

## E. Long-session drift and soak — 3 tests

14. `test_a_long_session_accumulates_no_stale_state` — scripted long
    sequence (families up/down, picks, ranges, reverses, generates):
    per-element dicts bounded, one group, no orphan layers, one
    notice per event.
15. `test_element_count_round_trip_restores_customization` — n 6→4→6:
    the absent elements' picks and ranges return by design; pin it as
    deliberate.
16. `test_repeated_generates_hold_the_project_steady` — thirty
    memory-mode generates: layer count constant, group count one,
    combo lists stable.

## F. Canaries for QGIS lies — 2 tests

17. `test_qgis_still_gives_a_bare_memory_layer_4326` — asserts the
    BUG (a CRS-less memory layer URI acquires EPSG:4326), so the day
    QGIS fixes it, the gdf_to_layer workaround is revisited on
    purpose. Model: test_qgis_still_counts_nulls_as_zero.
18. `test_qgis_still_calls_a_dead_layer_valid` — asserts isValid()
    stays True after the file behind a layer is deleted and reloaded
    (without touching extent(), which segfaults): the reason the
    plugin fingerprints contents instead of trusting validity.

## G. Creative additions — 7 tests

19. `test_the_dialog_is_keyboard_navigable` — tab order reaches every
    control; focus is never trapped.
20. `test_switches_and_editor_answer_the_keyboard` — Space toggles
    the Reverse switch; Esc closes the editor without losing picks
    (and flushes a pending range).
21. `test_the_window_survives_being_resized_small` — user-shrunk
    window: minimums clamp, no control clipped, the no-horizontal-
    scroll invariant holds.
22. `test_a_cancel_storm_leaves_a_usable_dialog` — ten rapid
    Generate/Cancel alternations: no zombie task, button enabled,
    map matches the last completed run.
23. `test_bound_columns_format_sanely_in_any_locale` — quant editor
    bounds under a comma-decimal locale and extreme magnitudes:
    deterministic strings, no exceptions, stamped JSON unaffected.
24. `test_the_help_tab_names_real_controls` — every control name the
    help text mentions exists in the dialog (docs-vs-UI drift).
25. `test_perception_warnings_point_the_right_way` — golden pairs:
    a known-confusable colour pair flags, a known-distinct pair does
    not, under normal vision and both deficiencies.

## H. Housekeeping folded into the campaign

26. release.py: mutation-guard sample scales with the diff (floor 12,
    ~1 per 20 changed lines, cap 80) as a pure function WITH ITS OWN
    TEST (the 26th new test); failed stages persist their full output
    to a file named in the abort message. Update the CLAUDE.md bullet.
    ALSO (user instruction, same night): the progress chart must list
    only stages that will actually run this invocation — a finished
    run showing ".." phantom rows (cached venv, skipped guard) reads
    as unfinished; a SKIPPED stage prints loudly why; and the
    baseline tag pre-0.24.0 now exists at a4119a2 so the guard fires
    from the next gate run onward (full releases tag at release.py's
    line ~682, so the chain continues by itself). Session process:
    during long stages the assistant RELAYS the ten-minute chart to
    the user rather than leaving it in the log.
27. Regression: lines added for tonight's two real defects (the
    watchdog's missing threading import; the editor's post-close
    debounce tick), then BUG-REGISTER regenerated.
28. Backfill discovery-shape labels on register entries as they are
    touched — thirty of forty-six read "unrecorded".

## Afterwards, in order

Full functional suite green → sharded catalogue sweep
(tools/mutation_catalogue_sweep.py) → dev/overnight.sh immediately →
report per-test results, survivors, and anything the campaign's bug
fixes changed for the user's next review pass. rc5 only after the
user has seen the results.
