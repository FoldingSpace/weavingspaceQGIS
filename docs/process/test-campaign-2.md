# Test campaign 2 — the slightly-lower-probability ring (designed 2026-08-09, late)

ORDER OF WORK (user instruction, 2026-08-09, revised): campaign 2,
then CAMPAIGN 3 IN FULL, and only then the whole-tree measurements
(full suite -> sharded catalogue sweep -> dev/overnight.sh) and rc5.
No measurement run and no candidate until both campaigns are done and
green: a tree still being edited cannot be measured, and a candidate
built from it would be a receipt for a tree nobody will ship.

PROGRESS: COMPLETE (2026-08-09). All fifteen tests written, run and green; item 16 left out by the user. Real defects found and fixed: the QGIS Natural-breaks SEGFAULT on non-finite values (worst of the night), NaN class bounds, legends labelled '0 - 0' at 1e-9, a spacing suggestion the guard itself refused, a BadZipFile escaping as a traceback, and the no-data grey making the legibility warning useless for categorical designs. Original text follows.

PROGRESS: RUNNING (user ordered execution the same night, and asked
that rc5 wait until all of it is done). Item 16 (far origin) LEFT OUT
by the user's decision, so the campaign is 15 tests. Area C item 6
settled by the user: a subset filter is CARRIED ACROSS a regeneration
(same promise as hand styling), reported only when the provider
refuses it. Area C DONE and green (3 tests, one real defect: filters
were silently discarded at every regeneration; mutation entry
user-filter-dies-at-regeneration proven). Also done ahead of the
campaign, on the user's instruction: every ramp swatch is now built
by one construction (_striped_icon) -- named ramps sampled into the
same eight equal stripes the Custom swatch draws, ends inclusive,
never narrowed by a display range because choosing a ramp resets it
-- with Reverse proven to turn BOTH kinds round (dropdown stripes
mirrored, Custom swatch following its permuted picks), two proven
mutation entries (swatches-built-two-ways, swatch-ignores-extra-
colours). Areas A, B, D, E, F, G, H are drafting concurrently as
append-scripts under dev/add_c2_*.py.

Ordered by the user while campaign 1's suite ran: think slightly out
of the box about where tests might still uncover bugs, and design the
next program. NOT STARTED — runs only after campaign 1's chain (suite
→ sharded catalogue sweep → overnight) has finished and been read.
Same binding rules as campaign 1 (see its header). The antimeridian
family stays excluded; one borderline item below is flagged for the
user's call.

## A. Determinism and tie-breaking — 2 tests

The join assigns each tile to the area it overlaps most, and a tie is
a coin flip unless something makes it not one. Bugs here are silent:
the map is plausible every time and merely DIFFERENT each time.

1. `test_the_same_settings_twice_give_the_same_map` — two cold runs,
   identical settings, byte-compared: tile geometries (WKB), joined
   values, renderer colours. Any nondeterminism (set iteration, dict
   order, rounding) fails loudly.
2. `test_exact_overlap_ties_break_the_same_way_every_time` — a region
   built so tiles straddle two areas at exactly 50/50; ten runs must
   agree with each other (the tie may fall either way, but the same
   way).

## B. Attribute values from the numeric edge — 2 tests

The float torture test covers GEOMETRY; nothing tortures the
ATTRIBUTES that classification eats.

3. `test_classification_survives_inf_nan_and_huge` — columns holding
   +inf, -inf, NaN, 1e308, -1e308, denormals: graduated (all
   schemes), Unclassed's 50-step interpolation, the constant
   detector, and the categorized mixed-type sort must each produce a
   map or decline in words — never NaN-poisoned breaks or a hang.
4. `test_extreme_magnitudes_render_readable_legends` — bounds and
   legend labels at 1e-9 and 1e12: no fifteen-digit labels, no "0 -
   0" classes that are really 1e-9 apart.

## C. The user's own hands on the output layers — 3 tests

Campaign 1 covered the styling dock. Users also FILTER and edit our
output directly, and each is a state the plugin never wrote.

5. `test_a_user_subset_filter_meets_the_null_workaround` — user sets
   a subset string on an element layer, then restyles: the null
   workaround combines and RESTORES the user's clause (the code
   claims to; nothing proves it), breaks computed over the filtered
   set, and the user's filter still in force afterwards.
6. `test_a_user_subset_does_not_silently_die_at_regeneration` —
   regeneration replaces layers; the user's filter dies with the old
   layer. Decide and pin the honest behaviour: carried across like
   hand styling, or reported as lost — never silently gone. (Small
   /grill-me question for the user before writing.)
7. `test_deleting_and_undoing_our_group_in_the_layers_panel` — user
   deletes the output group, then undoes (project-level
   resurrection): _element_layer_ids, the watcher connections and the
   next run must cope with layers that came back from the dead with
   their old ids.

## D. Qt event-loop pathologies — 2 tests

The debounces, the modal editor and QColorDialog nest event loops;
reentrancy is where "cannot happen" happens.

8. `test_timers_firing_under_the_open_colour_picker` — live and
   preview debounces expire while the editor's colour picker (a
   second nested modal) is up: no reentrant rebuild, no pick landing
   on a dead widget, records coherent after both close.
9. `test_unload_with_windows_open_and_work_in_flight` — plugin
   unloaded (as the reloader does) while the editor is open AND a run
   is mid-flight: no crash, task cancelled, no zombie timers firing
   into deleted C++ objects afterwards.

## E. Module identity after a plugin reload — 1 test

10. `test_a_reloaded_module_retires_the_old_dialog_cleanly` — reload
    the plugin MODULE (fresh class objects, as Plugin Reloader does),
    open a new dialog: the old instance's watchers and timers are
    inert, `_LIVE_DIALOG` gating still works across module
    identities (isinstance checks against a reloaded class are the
    classic trap), one group, no double notices.

## F. Estimates and guards tell the truth — 2 tests

11. `test_the_tile_estimate_is_honest_where_shapes_are_awkward` — the
    size guard's estimate versus actual tiles on a donut region, an
    L-shape, and a sparse archipelago: actual within a small factor
    of the estimate, in both directions — an estimate 10x low lets a
    "refused" workload through; 10x high refuses honest work.
12. `test_the_deps_installer_declines_a_corrupt_wheel` — deps.py
    against a truncated and a non-zip "wheel" in a local dir: no
    partial extraction left behind in libs/, a plain report, QGIS
    still usable (Linux users meet this path first).

## G. Style round trips that cross features — 2 tests

13. `test_a_qml_exported_here_reimports_here` — export an element's
    QML via QGIS's own save, choose it as a class source for another
    element: identical colours per value. Self-consistency between
    two features nobody tests together.
14. `test_default_ramp_pairs_pass_our_own_legibility_bar` — the
    DEFAULT_RAMPS and CAT_DEFAULT_RAMPS neighbours run through
    perception.clashes: the plugin's own defaults must not trip the
    plugin's own warning (checked at the bar the user can opt into).

## H. Report tooling robustness — 1 test

15. `test_the_report_generators_survive_hostile_docstrings` — the
    AST-driven testing-report/test-map/bug-register generators
    against a synthetic module holding raw strings, nested triple
    quotes, zero-arg lambdas and unicode docstrings: no crash, no
    silently dropped test.

## Borderline, the user's call — 1 test (flagged)

16. `test_far_from_origin_precision` — a region at Web-Mercator
    coordinates ~2e7 (far north, far east): insets, rounding and
    label anchors at reduced float resolution. Numeric rather than
    wraparound, but ADJACENT to the excluded antimeridian family, so
    it waits for an explicit yes.

Total: 15 tests firm + 1 flagged; one small /grill-me question (item
6's carried-versus-reported choice) before area C is written.
