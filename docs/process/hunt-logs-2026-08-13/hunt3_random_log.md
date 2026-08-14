# Hunt 3 — stochastic random-session hunt, log

Worktree: scratchpad/hunt3-random (created from HEAD 8aebd09).
Method: long random sessions against the dialog, invariants checked after
EVERY action. Seeds printed with every failure. Every session starts from
`QgsProject.instance().clear()` plus a fresh region layer.

## 03:42 UTC — start
Read CLAUDE.md (partial, first 977 lines), docs/TESTING.md in full,
tools/bug_hunt_brief.py in full. Read the existing fuzz
(`test_fuzz_random_interaction`, 25 steps, 3 seeds) and
`test_adversarial_sequences` so this hunt goes beyond them: they check
task-settled, group count, element-layer existence and map-matches-table
only.

## 03:46 UTC — writing the driver
Invariants planned (each gets a name so a fire can be counted):
A settled; B every element has a live layer; C every output layer in our
group has a table row; D no plugin output offered as a region layer;
E when the map is in step with the table: renderer kind, class count,
ramp colours, layer opacity all match the table; F nothing written into
the project when no run was asked for; G a setting the user chose is
still what the table says (opacity / ramp / class count / variable).
Sessions: 15-40 actions drawn from ~25 action kinds including save,
reopen, export, delete-a-layer, edit-the-region.

## 03:52 UTC — negative control before any hunting
`hunt_driver.py --selftest` breaks each property on purpose from
outside the dialog and requires its invariant to notice. All seven
fire. An invariant that has never fired in a clean run is otherwise
indistinguishable from one that cannot fire.

## 03:53 UTC — batch 1, seeds 1-12 (12 sessions, 25-40 steps)
10 "breaks", most of them mine:
- 8 x B (element without layer) after the DRIVER deleted an output
  layer or the group. That is the user's own act and the dialog is
  entitled to a stale record until the next run lands. Fixture fault;
  B now tolerates it until a new run arrives.
- 1 x driver crash (it held a reference to a layer it had just
  deleted). Fixture fault.
- seed 6: G ramp forgotten, element b, "ramp set to Reds, table now
  says Set2" after switching that row to Categorized. The swap itself
  is deliberate (`_sync_row`). Chased anyway -- see 03:56.
- seed 10: the DRIVER's own probe raised ValueError out of
  `dialog._layer_fingerprint` (`round(NaN)`). Not a fixture fault: that
  method is on the Generate path. Chased -- see 03:55.

## 03:55 UTC — FINDING 1 confirmed (empty region layer)
`repro_empty_region.py` and `repro_filtered_region.py`. Three routes to
one state: a scratch layer with no features, a region emptied in an
edit session, and a filter matching nothing. Once a map exists,
Generate raises ValueError inside `_geometry_signature` ->
`_layer_fingerprint` (dialog.py:1525) before any guard, the exception
dies at the Qt slot boundary (confirmed via sys.excepthook), and the
user is told NOTHING. The plugin already knows how to refuse this in
words -- `test_an_empty_region_layer...` asserts it -- but only on the
route where no map has been drawn yet.

## 03:56 UTC — FINDING 2 confirmed (a ramp lost through Categorized)
`repro_ramp_memory.py`. Purples -> Categorized -> back = Purples. Put
an ordinary design change in the middle and it comes back Blues, a
default. The crossed-over ramp is remembered as a PROPERTY ON THE
COMBO WIDGET (`last_quant`/`last_cat`, dialog.py:2606-2614) while every
other per-element choice is keyed by tile id so it survives a rebuild.
Second route: the renderer paints Blues.

## 04:03 UTC — batch 3 abandoned, fixture corrected
Seeds 202/203 fired H (state unreadable) three steps in, both at "save
and reopen". Cause: the region was a MEMORY layer, whose features do
not travel in a .qgz, so the reopened project met an empty region --
the same NaN, but reached by a fixture fault rather than by the
plugin. The driver now writes its region to a GeoPackage first. Seeds
202-204 are clean under the corrected fixture. Selftest re-run: all
seven still fire. Batch 4 launched, seeds 300-359.

## 04:06 UTC — batch 4 running (8 of 60 sessions, no breaks yet)
Sessions so far: 12 (batch 1, fixture faults) + 3 (202-204) + 8 = 23.
Confirmed findings: 2. Seeds quoted: 6 and 10 (batch 1) are the two
that led to them; both now have hand-written minimal reproductions,
which beat a shrunk plan.

Read `_queue_preview` and `_rebuild_unit` while waiting: ANY Design-tab
change (spacing included) rebuilds the table 350 ms later, which is
what destroys the widget properties behind finding 2. So the sequence
is more ordinary than the repro made it look. To be re-measured
through the control's own signal when batch 4 is off the machine --
two QGIS processes tiling at once slow each other to a crawl.

Also noted for the report, not a separate finding: the same empty
region makes the LIVE path say "live update paused (about 200,001
tiles)" -- the estimate is computed from a null extent, so the user is
told the map is too big when the layer is in fact empty.

Housekeeping: added negative controls for F and for the two G checks
that had none. `hunt_driver.py` was edited while batch 4 was running;
the running process had already loaded the module, so its behaviour is
the version launched at 04:03.

## 04:19 UTC — batch 4 at 45 of 60, three breaks, all one shape
Seeds 310, 330, 333: "G ramp forgotten" fired on the ramp action
ITSELF -- element a, ramp set to YlGn, table says tab10 (330: PuBu ->
tab10; 333: YlGn -> Set2). Not the deliberate style swap: the driver
drops the ramp intent whenever a style change crosses the
quantitative/categorical divide, so these are picks reverted with no
style change at all.

Read the path rather than guessing: the ramp combo's `changed`
-> `_refresh_preview_colours` -> `_queue_live` ->
`_update_dynamic_columns` -> `_sync_row` for EVERY row, synchronously,
and `_sync_row` swaps a non-categorical ramp off a categorized row.
So the dropdown on a categorized row offers every sequential ramp and
keeps none of them. Two harms to check: the pick never sticks, and
`changed` fires `_clear_category_colours` first, so the reverted pick
may still destroy the element's hand-picked colours. Reproduction
written (`repro_categorical_ramp_pick.py`), to be run when batch 4 is
off the machine.

Sessions so far: 12 + 3 + 45 = 60. Breaks that are candidate defects: 4
(one H, three G-ramp of the same shape).

## 04:30 UTC — batch 4 finished: 60 sessions, 5 breaks
3 x G ramp (seeds 310, 330, 333), 1 x H NaN (seed 356, at "reopen
dialog" after the region had been emptied earlier in the session),
1 x driver crash (a stale reference to the second region layer after
a project reopen -- fixture fault, fixed).

## 04:30 UTC — FINDING 3 confirmed (a ramp refused, colours destroyed)
`repro_categorical_ramp_pick.py` on a clean project. Element a,
landcover, Categorized, one hand-picked colour (#123456 for forest).
The user chooses YlGn from the dropdown, which offers it. Result: the
cell reads tab10, `_ramp_choices` and `_assignments` say tab10, the
hand-pick is GONE, and the message bar says "Choosing a new colour
ramp ... discarded 1 colour(s) you had picked by hand" -- for a ramp
change that never happened. Second route: the drawn layer's renderer
carries the tab10 ramp exactly (#1f77b4 ...) and forest paints
#d62728, not #123456. Site: `_sync_row` dialog.py:2602-2620, reached
from `_queue_live` -> `_update_dynamic_columns` on every data-tab
change. Both that call and the swap date from the initial commit.

## 04:33 UTC — negative controls extended, final batch launched
All TEN sabotages now fire, including F. Finding F's control also
found a hole in the hunt: live update defaults to ON, and F is only
checked when no run is possible, so batches 1-4 exercised it barely at
all. Each session in batch 5 (seeds 400-424) decides its live state at
the start instead.

## 04:37 UTC — batch 5 stopped short at 9 sessions
Seeds 400-408 ran; the driver was killed with the waiter watching it
(shared process group), not by a fault of its own -- the log ends
mid-run with no summary and no traceback. Breaks: seed 401 (H NaN, at
"reopen dialog" after the region had been emptied earlier), seeds 406
and 408 (G ramp, the categorized-row revert). Both already confirmed
findings; nothing new.

Batch 6 launched detached, seeds 409-424. Running total: 12 + 4 + 3 +
60 + 9 = 88 sessions.

(The entry that stood here was written BEFORE batch 6 finished and
carried a timestamp nobody had read off a clock. Removed rather than
corrected: an estimated time in this log is exactly the slip the brief
names. The real entry is below.)

## PENDING — batch 6, seeds 409-424
Three confirmed defects, each with a standalone reproduction in the
worktree
(`repro_empty_region.py`, `repro_filtered_region.py`,
`repro_ramp_memory.py`, `repro_categorical_ramp_pick.py`) plus
`hunt_driver.py` itself.

Invariants that NEVER fired on a real session: A (settled / no task in
flight / Generate usable), B, C, D, E in all four forms (renderer
kind, class count, ramp, opacity), F, and G for opacity, classes and
variable. Every one of them was proved able to fire by deliberate
sabotage from outside the dialog (`--selftest`), so I read them as
sound rather than as dead checks. E is the strongest of those
readings: over roughly two thousand checked states, whenever the
signatures said the map was in step with the table, it was.
