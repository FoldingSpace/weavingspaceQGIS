# Roadmap

What is going into which version, and what is merely wanted. Two
kinds of entry live here and the difference matters:

**Branch-backed** — the work exists, on a branch named
`for-<version>/<slug>`. The release process finds those branches by
name and refuses to build a candidate for a version while any of them
is unmerged, so nothing written for a release can be forgotten out of
it. Merging is the act that closes the entry.

**Wanted** — no code, sometimes no design. Recorded so that a good
idea survives the session that had it, which is the failure this file
exists to prevent: the ones that were only ever mentioned in a
conversation are gone.

Both kinds are checked before a candidate. An entry under the version
being released must be DONE, MERGED, or deliberately moved to a later
section — and moving it is a decision for the maintainer, not
something the release script may do on anyone's behalf.

Delete an entry when it lands. This file describes what is still
owed, and an entry nobody removes turns it into a diary.

## How to use this file

**WHEN.** The moment you notice something you are not doing now. That
is the whole discipline, and the failure it prevents is specific:
the ideas this project has actually lost are the ones that were
mentioned once, in a conversation, while somebody was busy with
something else. An entry costs thirty seconds and does not need to be
good.

**A thing you are NOT going to build yet** goes under the version you
think it belongs to, as a bold-titled paragraph saying what it is and
why it is not being done now. No branch, no design, no estimate.

**A thing you have BUILT for a later version** gets a branch:

    git branch for-0.24.1/<short-slug>          # name it for its version
    # work on it, or cherry-pick what is already written

then a paragraph naming that branch. Say what must be TRUE BEFORE IT
MERGES if anything must -- a verification, a measurement, a decision
somebody owes. That sentence is the reason the entry exists rather
than the branch alone: a branch cannot tell you it is unfinished.

**Deferring** is moving an entry to a later section. It is the
maintainer's decision and no tool will make it, which is why
`tools/check_roadmap.py` refuses rather than reschedules.

**Deleting** is what you do when it lands. A roadmap nobody prunes
turns from a statement of what is owed into a diary of what once was.

**The phrase the checker reads is "nothing outstanding"**, in the
version's own section, and it means nothing outstanding IN CODE. A
section may still list process items underneath -- an account
somebody must register, a setting in a web UI, a conversation with
another project -- and those do not block a candidate, because a zip
should not be held up by a GitHub Pages setting. Work that would
CHANGE THE SOFTWARE does block, and belongs above that line or on a
branch.

**Every version with a branch must have a section.** The checker
enforces it: a `for-<version>/*` branch whose version is not
described here is work parked with nothing to say what it is, which
is how a branch becomes archaeology.

---

## Needs the maintainer, not the assistant

**An OSGeo user ID**, for submitting to plugins.qgis.org. It belongs
to a person rather than to the software; register at id.osgeo.org and
the plugin is owned by that account.

**Two things to say out loud in that submission**, both already true
and both better disclosed than discovered: the vendored MIT-licensed
library under `weavingspace_qgis/vendor/`, and `deps.py` fetching
wheels from PyPI when QGIS lacks them. Plugins get rejected for
hiding the second, not for doing it. Full detail in
docs/PUBLISHING.md.

**DECIDED 2026-08-13, and mostly done.** The maintainer's answer:
preserve the row across a save where we can, and where we cannot,
reload the classes, count them, and call the row Custom. Implemented
the same day — the ramp and the class count are read back off the
renderer QGIS saved, which stores nothing new and treats the layer as
the authority exactly as opacity does; where no library ramp draws
what the layer draws, the class colours are recovered positionally
and the row reads Custom, which it already meant. The class count
also gained the per-element store every other control in that table
has had since the settled decision; it alone had been riding on a
widget property, which survives a rebuild and not a reopen.

What is LEFT is Reverse, and it is smaller than it looks. Reversing
produces a ramp clone matching no name in the library, so the flag
cannot be recognised from a renderer — but such an element comes back
as Custom carrying its actual class colours, so the map is exactly
preserved and no control claims a ramp that is not what is drawn.
Only the knowledge that those colours came from reversing is lost.
Closing it properly means teaching `_ramp_name_matching` to spot a
reversed clone; worth doing, not urgent, and the canary in
`test_a_project_round_trip_changes_nothing_a_user_chose` names it.
The scheme (Quantiles against Natural breaks) cannot be recovered
from breaks at all and is not attempted.

**The original question, kept for the reasoning.**
Measured 2026-08-13, with a canary now holding the answer in
`test_a_project_round_trip_changes_nothing_a_user_chose`: the ramp,
the reverse flag and the class count do NOT come back. They live in
session dictionaries nothing persists, while the layer carries all
three inside a renderer QGIS saves faithfully — so a reopened
project shows a table describing a map that is not on screen, and
since `_adopt_existing_group` leaves `_last_signatures` empty, the
next Generate re-seeds from the table and OVERWRITES the map. That
is the opacity defect fixed the same morning, one column to the
left, which is why it is a decision rather than a bug report: the
same reasoning applied to opacity says fix it, and it was found by
making three axes of that test live for the first time.

Three ways to go, and the choice is the maintainer's because it
settles what the plugin promises a saved project means:

- **Read it back off the renderer**, as opacity now is. Stores
  nothing new and became cheap the moment categorized renderers
  started recording their source ramp (also 2026-08-13). Recovers
  the ramp and the class count. Reverse needs ramp matching to
  recognise a reversed clone first, which it cannot do today; a
  scheme cannot be recovered from breaks at all.
- **Stamp the row** onto the layer as a custom property, like the
  hand-picked colours. Recovers everything including the scheme, at
  the cost of a second store of a fact the renderer already holds —
  which is the shape that produced today's other three defects.
- **Say it plainly instead**: the design tool starts fresh and the
  styling lives on the layers. Defensible, and already half the
  contract for variables, but then the table must not be allowed to
  overwrite the map on the next Generate, so `_last_signatures`
  needs adopting too.

Whichever way it goes, remove the names from `NOT_YET_RESTORED` so
the test starts requiring them.

## Open findings from the 2026-08-13 hunts

Every one of these was REPORTED by a hunt and is recorded here with
its status, so that nothing is lost between "an agent said so" and
"somebody checked". The full method record is in
docs/process/HUNT-RECORD.md. Verified means reproduced independently
of the hunt that reported it, by a different route.

**VERIFIED AND FIXED 2026-08-13 (evening).** `tools/coverage_report.py`
could never write a report. The suite ends in `os._exit`, which raises
no `SystemExit`, so `write_report`, the printed summary and the exit
status were all unreachable: you ran the documented command, waited out
the whole suite, and got nothing, with nothing to say why. Four
documents name that command. Fixed the way its sibling already does it
-- stand in for `os._exit` and write on the way through -- and proved
end to end by running it over one shard, which exercises the identical
exit path in a minute rather than forty. Unlike the per-test recorder,
a non-zero status still writes the report, with the status quoted in
the summary line: that record feeds a measurement where a partial file
understates survivors, this one is a description for a person.

**VERIFIED HERE 2026-08-13, fixed:** an unassigned element was
PREVIEWED in colour and DRAWN grey. Measured at preview #e7342a
against a map drawing (221, 221, 221). `_table_id_colours` asked
about the MODE before the variable while `seed_renderer` asks
`if not var` first; the preview now uses the map's order. Guarded by
`test_an_unassigned_element_previews_as_it_draws`.

**VERIFIED HERE 2026-08-13, NOT fixed, and both need a decision.**

- An edit made straight through the DATA PROVIDER is invisible to
  both of the dialog's stores. Measured: after rewriting every `v1`
  value through `dataProvider().changeAttributeValues`, the tiles
  still carried the old values and a full Generate changed nothing --
  a silent no-op. The fingerprint (count, extent, field names, CRS)
  does not move and no watched signal fires. This is a DECISION
  rather than an obvious bug: following it means either polling the
  data or widening the fingerprint to something that costs a scan,
  and the docstring at dialog.py:1484 currently claims the case is
  covered, so at minimum that claim must change. Scripts and other
  plugins write this way routinely.
- Losing a column destroys hand-picked CATEGORICAL colours silently,
  while the graduated twin survives. Measured: after renaming the
  field, `_category_colours` was empty and `_quant_colours` intact.
  The categorical path pops the record directly instead of going
  through `_clear_category_colours`, which is what announces every
  other such loss -- so the fix is small, but which losses are worth
  announcing is a judgement about how chatty the notice line should
  be, and the same rename may be a user's undo a second later.

**VERIFIED HERE, from the stochastic hunt: a ramp you are OFFERED is
refused, and your hand-picked colours are destroyed for it.**

**DECIDED, THEN FIXED ON THE THIRD ATTEMPT (2026-08-13, evening).**
The maintainer's answer was: cartographer beware. Leave the dropdown
offering every ramp (#1 is the user's choice); the real fault is #2,
destroying hand-picks for a change that does not happen; and #3 needs
no separate fix, because once the pick is honoured a ramp change
really has occurred and the notice becomes true.

The fix that worked is the one this entry had recorded as untried:
`_synced_modes` remembers the renderer kind each element was last
SYNCED in, and `_sync_row` swaps the ramp only when that has moved.
A mode change still earns its substitution; a pick made on a row
already in its mode is left alone. It does not depend on which Qt
signal arrives first, which is where the two earlier attempts died
(recording the pick in the combo's general change handler made a mode
change look deliberate; moving it to `activated` created a
signal-ordering race). Guarded by
`test_a_ramp_you_are_offered_is_the_ramp_you_get`, whose second half
asserts the mode-change swap SURVIVES, and by catalogue entry
`ramp-swap-only-on-a-mode-change`.

Two things came out of it that were not the defect.

The ramp memory moved off the combo widget (`last_quant`/`last_cat`)
into `_ramp_memory`, keyed by tile id like every other per-element
choice. The widget properties survive a style flip and not a table
rebuild, and any design change rebuilds the table 350 ms later, so a
ramp crossed over before that landed came back as a positional
default. That was the stochastic hunt's second finding, folded in
here because it is the same three lines.

And `test_style_follow_and_memory` turned out to be a DEAD AXIS. Its
"ramp memory across style flips" block set the mode to Categorized on
a row that was already Categorized, so the flip never happened, and
what it actually asserted was that a quantitative ramp picked on a
categorized row gets thrown away -- the defect above, pinned as
correct behaviour. The row is put into a quantitative mode first now,
and the block asserts what its own comment always claimed.

**VERIFIED AND FIXED:** `dialog._layer_fingerprint` raised
`ValueError: cannot convert float NaN to integer` on an emptied
region layer. QGIS reports an empty extent with DBL_MAX sentinels
rather than zeros, so rounding the bounds meets NaN. Reached from the
live path and both signatures, all from Qt slots, so the raise went
to a console nobody has open. The hunt hit it on three separate
seeds (356, 401, 409) before anybody looked at it deliberately.
Guarded by `test_an_emptied_region_layer_does_not_raise`.

**THE QML CLASS SOURCE, all three tested 2026-08-13.** Measured with
a real .qml on disk, reading the colours off the renderer:

- **A QML edited on disk never reaches the map.** FIXED 2026-08-13
  (evening). Both signatures carried the file's TOKEN and nothing
  about its contents, so a rewritten scheme left every signature
  equal and Generate repainted nothing. `_class_source_stamp` now
  carries modification time and size, which is cheap enough to ask on
  every debounce tick where a hash is not. A file that has GONE
  deliberately keeps its last stamp rather than moving the signature,
  because losing a file is not an edit and the settled behaviour
  there is to keep the map. Guarded by
  `test_an_edited_class_source_reaches_the_map` and catalogue entry
  `class-source-contents-are-in-the-signature`.
- **A moved QML is repainted away on the RESTYLE path.** FIXED
  2026-08-13 (evening). The restyle path swallowed the load failure
  and seeded from nothing, painting automatic colours over the user's
  scheme with no notice and the cell still naming the file; its
  re-tile twin collected the same failure and warned. It now leaves
  that element's colours alone and reports which file, while still
  applying the change that triggered the restyle -- usually opacity,
  and refusing that too would turn one unreadable file into a row
  whose controls do nothing. Guarded by
  `test_a_moved_class_source_survives_a_restyle` and
  `an-unreadable-class-source-keeps-its-colours`.
- **A class source chosen while a run is in flight is not applied by
  the landing run.** CONFIRMED as an observation, and DELIBERATELY
  NOT FIXED, because it is the same shape as the ramp case that was
  fixed and then reverted the same night: with live update off the
  plugin never repaints unasked, so the choice is DEFERRED rather
  than lost and the next Generate applies it. What must be checked
  before this is called a defect is whether the CELL goes on naming
  the QML while the map ignores it -- that is the ramp-cell fault,
  which was real -- and that was not measured here.

**EVERY REPORTED FINDING IS NOW JUDGED (2026-08-13, evening).** The
list below was the queue of claims nobody had reproduced. It is
emptied here rather than deleted, because what did NOT reproduce is
as much a part of the record as what did.

- An unassigned element PREVIEWED in colour and DRAWN grey. CONFIRMED
  and fixed earlier the same day; see above.
- **Elements silently absent from the map on dense designs. NOT
  REPRODUCED**, and this is the one claim that failed. Ten
  configurations were driven end to end: stripes, grid, hex-slice and
  square-slice at n=26, plus stripes at n=20, over a four-cell and a
  six-cell region at spacings of 1500, 2000 and 3000. Every one
  produced an element layer for every table row, and no layer was
  empty -- feature counts ran 1 to 9 per element. The report said 18
  layers for 26 rows. Whatever produced that reading, it was not any
  of these. Recorded as a claim that did not survive checking, which
  the hunt record counts against its direction rather than for it.
- **A reopened project loses an imported class source.** CONFIRMED and
  FIXED. `_adopt_row_symbology` recovered a graduated element's
  colours positionally when no library ramp drew them, and returned
  having recovered nothing for the categorized twin five lines away.
  A named ramp is not proof the ramp decides the colours, either: a
  categorized renderer built from a QML records a source ramp (since
  this morning, so QGIS's own panel can show one) while the template
  overrides it. The adoption now asks the real seeding code what that
  ramp would draw and keeps only the colours it does not explain, so
  an ordinary ramp still comes back as a ramp and one hand-picked
  colour comes back as one hand-picked colour. Guarded by
  `test_a_reopened_project_keeps_an_imported_class_scheme` and
  `categorized-adoption-recovers-its-colours`. The class SOURCE itself
  is still not restored, and that stays a stated limit: nothing
  stamps the file token, so the row reads "Automatic colours" while
  the map keeps the scheme.
- An edit made straight through the DATA PROVIDER is invisible to
  both of the dialog's stores. CONFIRMED, and kept as a documented
  LIMIT by the maintainer's decision; the docstring that claimed the
  case was covered has been corrected.
- Losing a column destroys hand-picked CATEGORICAL colours. CONFIRMED
  and fixed earlier the same day.
- **Fewer distinct values than classes. CONFIRMED and FIXED.**
  Measured with a render context this time, which is what the earlier
  probe lacked: k=5 over {1, 5, 9} gave five ranges, two of them
  degenerate, three colours on the map, and the highest value drawn
  mid-grey while the legend's black sat beside a range nothing
  occupied. `make_graduated_renderer` now reduces k to the number of
  distinct finite values, which is what upstream's own
  `_plot_subsetted_gdf` does and what the constant-column collapse
  already did at n=1. Unclassed is exempt: its fifty steps reproduce
  a continuous ramp and are not a class count anybody chose. The user
  is told, as the constant case is. Guarded by
  `test_a_legend_never_shows_a_class_the_map_does_not_have` and
  `classes-never-outnumber-the-values`.
  Two tests had been WRITTEN AROUND this defect, and both are now
  fixed rather than exempted: one asserted `distinct >= k` before
  measuring, and one switched to Equal intervals on the belief that
  only quantiles collapsed, then asserted nine ranges that five of
  which painted nothing.
- **`bridge.py:223-225` is unreachable. CONFIRMED, and DELETED.**
  `invert` is defined on `QgsColorRamp` itself rather than on the
  subclasses, so `hasattr(ramp, "invert")` is true for every ramp
  QGIS defines and for any subclass a plugin might register --
  measured on all six built-in classes and on a bare subclass. The
  fallback was also the worst of the three branches: rebuilding a
  discrete scheme as a two-stop gradient would have thrown away every
  colour between the ends. Deleted rather than defended, per the
  standing rule.

**INSTRUMENTS, verified and partly fixed.** The mutation catalogue
reported CAUGHT for entries whose named test does not exist; three
broken entries were repaired and all 213 now validate. What is NOT
done: the validation is a script that was run once, and belongs in
the tool as a preflight that refuses to judge a broken entry. Also
outstanding from that audit -- nothing actually RUNS the catalogue
though two documents say the release does; `check_standards` compares
only counts for the derived documents while the generators' own
`--check` catches more; three EQUIVALENT entries exclude nothing; the
mutate_auto watchdog ignores a child's CPU and can score a live
mutant as stalled.

**A PERMANENT FALSE ALARM IN THE CATALOGUE, fixed 2026-08-13
(evening).** The remote catalogue sweep of 2026-08-12 returned 173 of
174 and flagged `fit-to-design-on-show` as NEEDS ATTENTION. Nobody
re-judged it, which is what the doctrine requires before believing a
flagged verdict; doing so found a genuine survivor, and then found
that the maintainer had ACCEPTED it permanently on 2026-08-10 with
the reasoning written directly above the entry. So the sweep was
flagging a settled decision, every time, forever -- and a warning
that fires on a settled decision is how people learn to stop reading
warnings. Entries now carry `accepted=True` beside the existing
`equivalent=True`, which are not the same claim: equivalence says
nothing observable changed, acceptance says something real changed
that no test we can write can reach. Both are expected to survive;
only being CAUGHT is news, and it is announced as such, because that
means the acceptance can be withdrawn. The sweep reads the child's
own verdict rather than inferring one from the exit code, and the
summary line no longer calls an expected survivor a kill.

A third attempt at a discriminating assertion failed like the two
before it, and the measurement is worth keeping: Qt clamps the window
to its own minimumSizeHint on show (634px) whatever the constructor
left it at (560px), and the tick brings it to 453px with or without
that call site. The test's docstring claimed the opposite and now
records what was measured.

## 0.24.1 — next

### Branch-backed

### Wanted, no code yet

nothing outstanding.

The docstring audit was done on 2026-08-12 and is deleted rather than
marked done, as this file says to do. What it found is worth one line
each, because the pattern will recur: two PRODUCT defects, not just
stale prose -- 0.24.1's only user-visible change never reached a
user, and two modal dialogs sat on a path that forbids them -- plus a
rule in check_standards.py that asserted its own enforcement and had
none.

The mechanisable quarter of it is now permanent:
check_args_blocks_match_signatures runs with the other standards
checks, and found a gap in its first run. The other three kinds --
behaviour that changed, a measurement since re-measured, a why naming
a bug now fixed -- need reading, and were read.

## 0.24.2 — next

### Branch-backed

### Wanted, no code yet

nothing outstanding.

The changelog entry was REWRITTEN on 2026-08-13 (evening) against the
actual diff, which is the step docs/PUBLISHING.md says never to skip:
the approved version predated nineteen defect fixes and described
none of them, including a GeoPackage export that destroyed the rest
of the user's file. It sits in the text-review queue, where only the
maintainer may approve it.

The incremental mutation run is TRIAGED, and there was nothing in it.
Dispatched against `pre-0.24.1rc1` on 2026-08-12, it sampled one
mutant of the four its 153 changed lines carried -- three were
unreached by any test -- and killed it. Read 2026-08-13; the artifact
had been sitting unopened. A run that answers nothing still has to be
opened to find that out, which is the whole reason it is recorded
here rather than assumed.

Sampling the six unsampled assignment-lookup copies is DEFERRED to
0.24.3, and deliberately: it is measurement rather than
defect-finding, and the night of 2026-08-13 put mutation sampling at
zero product defects across 128 survivors. `_assignment_for` now
holds the lookup, so a future mutant has one place to land.

## 0.24.2 — waiting on somebody else

Everything here is blocked on the upstream weavingspace project
rather than on this repository, which is why it is not 0.24.1: a
release should not wait on a conversation we do not control. Moved
here 2026-08-12 at the maintainer's instruction.

### Wanted, no code yet

**Element ids past 26.** Blocked upstream rather than here. Weaves are
specified as strings with one character per element (`abcdef-|ghijk-`),
so doubled letters have nowhere to go, and case-distinguished ids
collide on every path that folds case — GeoPackage table names,
case-insensitive filesystems, saved layer properties. Going further
means changing the weave string format upstream and in every stored
design. Worth raising with the weavingspace project before anyone
attempts it.

**Two conversations with the upstream repository.** Whether the corrected
large-plain-weave note was sent (dev/upstream-note-large-plain-weaves.md
supersedes the first, which blamed a commit wrongly). And the
element-id ceiling below, which is upstream's decision rather than
ours.

## Later, or never

**Deriving the aggregate coverage from the per-test record** (was
`for-0.24.1/coverage-dedupe`, commit 34dab50bd0cd, branch deleted
2026-08-12). It made `coverage_report --from-record` write the
aggregate from what the per-test recorder already collected, so the
suite would not run twice under monitoring.

Dropped because its premise went away the same week it would have
landed: both coverage stages left the release path, so nothing
automatic measures twice any more. What remains is a saving for
somebody who deliberately wants the per-test record AND the aggregate
report in one sitting, which is rare and chosen. Against that it
needed a rebase across three files that were rewritten the night
before -- the recorder now writes only what a shard ran and survives
the suite's os._exit, the merger now salvages an empty-duplicate set
-- and a careless rebase would have silently undone one of those. Its
own precondition, a derived report compared against a measured one,
was never met either.

The commit is recoverable by hash if the premise returns, which it
would if the aggregate report ever went back into an automatic
process.


**A "two views of one truth" differential campaign.** Recorded here
rather than started, because it is a session's work and the case for
it is an argument about where effort pays rather than a defect
waiting to be fixed.

The plugin describes the same state in several places that must agree
-- the table, the design preview, the generated map, the colour
editor, and the saved project. Drive random designs, snapshot every
view, and require them to agree. A disagreement is a defect by
construction, so it needs no oracle and does not depend on the suite
being any good.

The case for it, in the record rather than in principle: nearly every
real defect this project has found came from comparing two
independent descriptions of the same thing (docs/TESTING.md, "What has
actually found defects here"), and the defect found on 2026-08-13 was
precisely a table-against-map disagreement that survived because
nothing compared those views systematically.

PART OF THIS IS NOW BUILT, which narrows what is left rather than
closing it. `test_random_designs_keep_their_views_in_agreement` covers
three of the pairs below -- the ramp cell, the row's assignment, and
the preview -- across random designs. What it does NOT cross is a
BOUNDARY, and the boundary crossings are where this project's evidence
says the value is: the saved project, the GeoPackage, and the colour
editor's listing. Those are the three worth building next.
`tools/equivalence_scenarios.py` dumps most of what they need.

The pairs, and what a disagreement would MEAN, which is the part that
needs deciding rather than coding:

- the ramp cell against the element layer's actual renderer. A
  disagreement means the table is lying about the map. This is where
  the 2026-08-13 defect lived, and the cell read Custom while the map
  wore a clean ramp;
- the row's assignment (variable, style, class count) against the
  renderer's field and classes. A disagreement means the chooser
  describes a map the plugin did not draw, which is the failure
  "a quantitative style never stands on text" already guards at one
  point only;
- the design preview's colours against the element layers'. A
  disagreement means somebody judged a design from a picture the map
  does not honour;
- the colour editor's listing against the renderer's categories. A
  disagreement means the editor offers values the map lacks, or hides
  values it has;
- a saved project reloaded against the state before saving. A
  disagreement means stored work was lost or altered in the round
  trip;
- a GeoPackage reopened against the layers in the project. A
  disagreement means what a colleague receives is not what you see,
  which is the whole promise of the export.

Note what is NOT on that list: anything requiring an oracle. Every
pair is two descriptions the software itself produces, so the test
needs no expected value, no fixture of correct answers, and no
judgement about what a good map looks like. That is what makes it
cheap to run over random designs and what makes a failure
unambiguous.

Two cheaper differentials worth doing alongside, both nearly free now:
re-run the claims audit mechanically over the whole tree, since stale
prose reliably marks where behaviour drifted and that is where both of
2026-08-12's product defects came from; and a save-reload-compare,
because stored state is where hostile stored properties live.

**Badges on the README**, and the "minimalist faux 3d" button styling
the user mentioned. Both cosmetic, neither designed.

**The custom ("this") weave type**, with its tie-up, treadling and
threading matrices. Deprioritised rather than rejected: it needs a
matrix-entry UI and its own documentation.
