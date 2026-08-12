# Test campaign 3 — the cartographic and human ring (queued 2026-08-09)

ORDER OF WORK (user instruction, 2026-08-09, revised): campaign 2,
then CAMPAIGN 3 IN FULL, and only then the whole-tree measurements
(full suite -> sharded catalogue sweep -> dev/overnight.sh) and rc5.
No measurement run and no candidate until both campaigns are done and
green: a tree still being edited cannot be measured, and a candidate
built from it would be a receipt for a tree nobody will ship.

PROGRESS: COMPLETE (2026-08-09). All ten tests written, run and
green (areas B, C, D, E, F, G). No plugin defect found by areas
B, C or F -- the vendoring tool really does reproduce the vendor,
all 57 documented commands exist with the flags they claim, the
receipt gate refuses as designed, and the GeoPackage opens
cleanly in a fresh process. The finding was a HARNESS one: the
modal recorder kept only window titles, so no test could ask
whether the user was told in words; fixed centrally and recorded
in docs/TESTING.md. Two behaviours pinned as deliberate rather
than fixed: after a region layer's data vanishes, recovery needs
a manual reassignment (the plugin cannot tell its own forced
'---' from the user's), and a run's landing legitimately uses the
launch snapshot, with the queued rerun clearing a vanished
element (with live update off, the orphan waits for Generate).

QUEUED by the user while campaign 2 ran: another creative campaign,
to follow it. NOT STARTED. Runs after campaign 2 is green and its
measurements (sharded catalogue sweep, overnight census) have been
read; rc5 waits for all of it (user instruction).

Where campaign 1 audited the software's CLAIMS and campaign 2 the
machine's edges, this one asks a different question: is the artefact
right? Lenses nobody has pointed at this plugin — the plugin as a
citizen of somebody else's QGIS, the project as a thing other people
will maintain, work that outlives the session it was made in, the
output as somebody else's input, and whether any of it can be undone
— plus three wild ones.
Same binding rules as campaigns 1 and 2 (their headers); the
antimeridian and far-origin families stay excluded.

## A. Removed (user instruction, 2026-08-09)

The three "map as a document a stranger reads" items -- the legend
naming variables and units, elements staying separable at print
scale, and identify returning a tile's own variable -- were dropped
from this campaign at the user's request before any were written.
Recorded rather than deleted so nobody re-derives them as a new idea:
they are legitimate questions, just not this campaign's.

## B. The plugin as a citizen of somebody else's QGIS — 4 tests

Every one of these is a thing a real QGIS user's session contains
that our fixtures never do.

1. `test_a_project_that_already_has_forty_layers` — the layer combo,
   the group adoption and the region choice under a busy project
   including layers named like ours, groups nested inside groups, and
   a layer whose name collides with the output group's.
2. `test_two_projects_in_one_session` — open project A, generate,
   open project B (QGIS keeps one QgsProject instance and swaps its
   contents): no records from A leak into B, no watcher fires into a
   layer that belongs to a closed project.
3. `test_the_plugin_under_a_non_english_locale` — QLocale set to
   German and to Arabic (RTL): numbers in notices and bounds parse
   and print, no layout inversion breaks the no-horizontal-scroll
   rule, nothing raises. Canadian-spelling rules still apply to our
   own strings.
4. `test_a_read_only_and_a_full_disk_output_path` — GeoPackage output
   to a read-only directory and to a path that fails mid-write:
   declines in words, leaves no half-written .gpkg adopted into the
   project, dialog still usable.

## C. The project as something others maintain — 3 tests

The tooling now rewrites shipped source, decides the mutation score
and writes into QGIS profiles. It is load-bearing and largely
unguarded.

5. `test_the_vendoring_tool_reproduces_the_current_vendor` — run
   tools/vendor_weavingspace.py against a pristine upstream checkout
   into a scratch tree and diff against what we ship: zero drift, or
   a named patch whose anchor moved. This is claimed in CLAUDE.md and
   was last verified by hand.
6. `test_every_documented_command_still_exists` — every shell command
   quoted in CLAUDE.md, MAINTAINING.md, docs/TESTING.md,
   docs/MUTATION-LOOP.md and PUBLISHING.md names a file that exists
   and a flag the script accepts (parse argparse, do not run them).
   Documentation that lies is worse than none.
7. `test_the_release_refuses_a_tree_it_did_not_measure` — the
    receipt gate from the outside: mutate one shipped byte after a
    candidate and assert release.py refuses and says which case;
    then restore and assert it proceeds. The gate is guarded by unit
    tests; this drives it end to end.

## D. Slightly wild — 3 tests

Low probability, high embarrassment.

8. `test_the_plugin_survives_its_own_output_as_input` — choose a
    previous run's element layer as the REGION layer. The combo
    excludes our own outputs by custom property; this asserts the
    exclusion holds after a project reopen (when the property comes
    back from a file) and that the guard cannot be walked round by
    renaming the layer.
9. `test_a_thousand_element_design_is_refused_gracefully` — ask for
    an element count and spacing whose product is absurd; the guard
    must refuse before any geometry work, in words, with the dialog
    usable — and must NOT refuse the largest design that is genuinely
    reasonable (both sides of the boundary, measured).
10. `test_concurrent_dialogs_in_two_qgis_windows` — QGIS supports
    multiple main windows; two dialogs adopting the same group in the
    same project is the double-watcher problem's bigger sibling.
    Pin what happens: one owner, the other deaf and saying so.

## E. Time, and work that outlives the session — 3 tests

The plugin's records live in a project file that outlives every
assumption they were written under. Nothing tests what happens when
the world moves on around a saved map.

11. `test_a_project_saved_by_an_older_plugin_still_opens` — build a
    project whose stamped records use the SHAPES a previous version
    wrote (the pre-quant categorical property alone; the legacy
    "__shared__" class-source token; a class-file path that no longer
    exists): the dialog opens, adopts what still means something,
    and says once what it could not honour. Forward compatibility is
    claimed by the adoption guards and never exercised as a version
    story.
12. `test_a_project_whose_region_layer_has_moved` — the .qgz reopens
    with its region layer's file renamed or gone. The plugin must
    not tile a corpse: it declines in words, leaves the group alone,
    and recovers when the user points at a live layer.
13. `test_a_run_started_before_a_change_lands_after_it` — the
    settled rule is that the launch snapshot decides the run. Drive
    a slow run and change the design mid-flight in ways that alter
    the ELEMENT SET (element count down, a variable unassigned):
    the landing must not create layers for elements that no longer
    exist, nor orphan the ones that do.

## F. The output as somebody else's input — 3 tests

Every map made here leaves for another tool. What we hand over is a
contract we have never checked from the outside.

14. `test_the_geopackage_opens_cleanly_in_a_fresh_process` — write
    output, then read the .gpkg in a NEW QGIS application process
    (subprocess): layers, styles, attribute names and the embedded
    symbology all arrive, with no dependence on the writing session.
15. `test_attribute_names_survive_the_round_trip` — unicode, spaces,
    reserved SQL words, names at the GeoPackage length limit, and
    two columns differing only in case: either preserved exactly or
    renamed with the user told, never silently truncated into a
    collision.
16. `test_the_output_carries_no_working_state` — a shipped layer's
    fields and custom properties hold what a reader needs and
    nothing internal: no ws_unit_id tracing column, no scratch
    properties, and every weavingspace_* property either documented
    or gone. What we stamp is a public interface.

## G. Undoing what the plugin did — 2 tests

The plugin adds, restyles and replaces. A user who wants any of it
undone has only QGIS's own tools, and we have never checked they
suffice.

17. `test_removing_the_group_leaves_the_project_clean` — delete the
    output group and assert nothing of ours survives: no orphan
    layers outside the group, no leftover custom properties on the
    USER's region layer, no timers or watchers still connected.
18. `test_a_second_dialog_after_a_manual_cleanup` — after that
    cleanup, a fresh dialog behaves like a first run rather than
    half-adopting ghosts: no records restored from nothing, no
    "Custom" cells with nothing behind them.

Total: 18 tests, after the removal above and the three areas added
at the user's request (E, F, G). Expected yield is lower per test
than campaigns 1 and 2 — that is the point of the ring — but items 5,
6 and 7 guard tooling that currently guards everything else, and the
ones I would bet on for real defects are item 2 (two projects in one
session), item 13 (an element set that changes mid-run) and item 16
(working state shipped as though it were data).
