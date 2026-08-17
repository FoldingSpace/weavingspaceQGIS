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

## 0.24.3 — next

Work done straight on `pre-0.24.3rc1` rather than on a `for-` branch,
because it is this version's work and not a parking place. Delete each
entry as it lands.

### Wanted

Two entries were DELETED here on 2026-08-16 having landed, which is
what this file asks for: the `test_adversarial_sequences` stall (four
routes into a rebuild that a retired dialog kept open; 1,282 rebuilds
down to 173, below v0.24.2's own 461) and both Windows failures (a
notice assertion that had rotted against a reworded sentence, and a
sampling window sized for this Mac). Each is guarded, and each guard
was proved against the broken fix. The reasoning they produced is in
CLAUDE.md and docs/TESTING.md, where it binds; a roadmap nobody prunes
becomes a diary.

FIXED 2026-08-17 and deleted from here: opening the plugin on a saved
project silently replaced the saved map. Adoption already recovered
the file from the adopted layers' own sources; the file widget was
simply never told, and an empty widget is BOTH the condition that lets
live update run and the condition that sends output to memory. One
method, called after `_build_ui` and again on File > Open, makes the
two records agree. Guarded by
`test_reopening_a_saved_project_does_not_replace_its_map`, which
stages it WITH LIVE UPDATE ON -- the setting every other adoption test
disables and every user has -- and was proved by removing the call.

The first attempt at that fix silently did nothing, because it set the
widget inside `_adopt_existing_group`, which runs BEFORE `_build_ui`
in the constructor. The guard caught it, which is what a guard written
before believing the fix is for.

THREE ENTRIES WERE DELETED HERE ON 2026-08-17 having been settled,
which is what this file asks for. The group rename making a second
group over the same tables: fixed through both doors, guarded by
`test_a_renamed_group_is_still_the_group_the_next_run_replaces` and
`test_a_renamed_group_is_adopted_when_the_plugin_reopens`, and the
lookup now asks the layers rather than the name. The missing ramp
raising from inside `make_categorized_renderer`: fixed on both twins,
announced to the user, and the test that found it now installs the
palette it names instead of relying on a seeded profile. And the
stochastic hunt's seven-seed claim, which was JUDGED AND DID NOT
REPRODUCE on any of seven deliberate routes -- the judgement, and the
lesson about seed counts that came out of it, are in
`docs/process/hunt-stochastic-2026-08-17.md` and the hunt record.

### Reported by the maintainer against rc5, owed by rc6

DONE 2026-08-17 and deleted from here: a class bound may now sit
outside the data it classifies, so one pair of limits can be given to
several variables. Guarded by
`test_a_pin_may_sit_outside_the_data_it_classifies`, which found that
relaxing `pin_problem` was only half of it -- `_apply_pinned_bounds`
built the outer class from the column's own extreme, so the ladder
snapped back to the data and the accepted number changed nothing.

STILL OWED FROM IT: the settled-decisions paragraph in CLAUDE.md
names the four refusals together, which is how "outside the data"
came to look like one of the undrawable three. Correct it there with
the maintainer's ruling beside it.

**EQUAL INTERVALS MUST ACTUALLY BE EQUAL, AND UNCLASSED WITH THEM.**
The maintainer's rule, 2026-08-17: with Equal intervals or Unclassed
every class has the SAME WIDTH, and the one exception is a PINNED
end, whose class takes whatever width the user's bound gives it.

MEASURED AND CURRENTLY FALSE. Two columns, 1..13 and 0.5..38, both
pinned to -5..40 at k=5:

    Equal intervals, column a: -5, 5, 9, 40 -- widths 0, 10, 4, 31, 0
    Equal intervals, column b: -5, 13, 25.5, 40

The middle classes are not equal to each other, and the two columns
do not agree. The cause is the mechanism rather than the arithmetic:
the scheme cuts `k - pins` classes from the samples BETWEEN the pins,
which is each column's own data, and `_apply_pinned_bounds` then
STRETCHES the outermost computed class out to meet the pin. That
stretch is what destroys equality, and it was put there for a good
reason -- without it a gap opens between the pin and where the data
resumes, and a value arriving there later paints as no data.

So the fix is to cut the intervals FROM THE PIN rather than cutting
them from the data and stretching afterwards. Equal intervals over
the span the pins declare gives equal widths by construction, closes
the gap without a stretch, and makes two columns with the same pins
draw the same ladder -- which is the whole point of setting the same
limits on both.

THIS ALSO SETTLES THE QUESTION I ANSWERED WRONGLY. Told that wide
limits plus Equal intervals would make a colour mean the same number
on every map, I said yes; the measurement above says no, and the rule
here is what would make it true. Unclassed rides the same rule, its
fifty steps spanning the pinned range rather than the column's.

**AWAITING THE MAINTAINER'S EYE, not code: the ghost numbers.** The
cause is removed -- the Unclassed table is no longer composited
through a `QGraphicsOpacityEffect`, and fades per item through the
palette's disabled colour instead. Guarded by
`test_the_unclassed_list_fades_without_a_graphics_effect` and by the
catalogue entry `the-unclassed-list-is-not-composited`, which puts the
effect back and is caught.

WHAT THE SUITE CANNOT SAY is whether the ghosts have gone, because
they live in the window system's backing store where `grab()` cannot
look. **This entry stays open until somebody scrolls that window on a
real screen.** The original report follows, unedited, so the check has
something to check against.

**GHOST NUMBERS BEHIND THE UNCLASSED EDITOR'S CLASS BOUNDS.** Reported
2026-08-17 against rc5, with a screenshot: a second, faint set of
bounds painted behind the live ones in the Lower and Upper columns,
offset by about a row.

STRONGLY INDICATED, NOT YET PROVEN. `locked=unclassed`
(dialog.py), and the locked branch puts a `QGraphicsOpacityEffect` on
`self.table`. A graphics effect renders its source into an offscreen
pixmap while `QAbstractScrollArea` scrolls by BLITTING, so the cached
source and the blitted viewport disagree -- which matches the
screenshot exactly, where each ghost is the value one row away.
Measured that the preconditions hold: the effect is there at 0.45 and
the table scrolls (max 35 with fifty classes).

What could NOT be shown is the artefact itself. `grab()` repaints
cleanly and offscreen showed 0 of 32,900 sampled pixels differing
between a scrolled and a force-repainted render, exactly as predicted
before the run -- the fault lives in the window system's backing
store, where this suite cannot look. So the fix (fade the ITEMS
through the palette's disabled text colour rather than compositing the
whole table through an effect) must be confirmed by the maintainer on
a real screen, and the guard can only assert the cause is gone rather
than that the symptom is.

**THE PLUGIN IS SLOWER IN rc5, AND THE TESTER NOTICED.** Reported
2026-08-17, and then narrowed by the tester in the sentence that
matters most here: *tiling at small spacings does not seem any
slower, but the snappy interactive feel at large "auto" spacing has
gone.*

READ THAT CAREFULLY, BECAUSE IT NAMES THE SHAPE. Large spacing means
FEW tiles, so the tiling itself is cheap and what dominates a run is
its FIXED cost. Small spacing means many tiles, where the tiling
swamps everything and a fixed cost disappears into it. A regression
visible at large spacing and invisible at small is therefore
per-RUN overhead, not per-tile work -- and with live update firing on
a 900 ms debounce while somebody drags a control, a fixed cost is
paid over and over.

That rules out most of the tiling path by inspection and points at
what every run does regardless of size. Profile a LARGE-spacing live
render, not a small-spacing Generate, or the measurement will be
taken where the effect is known to hide.

MEASURE, DO NOT GUESS. This project already spent a day on a
performance regression whose obvious culprit was innocent, and the
technique that worked is written down: profile the SAME operation at
two revisions and diff the CALL COUNTS, not the seconds. Counts are
immune to profiler overhead and to whatever else the machine is
doing; on 2026-08-16 the self-time ratio understated a threefold
difference as 1.2x while the counts carried it exactly. The two
revisions here are `569aefb` (rc4) and `6c7af51` (rc5).

Candidates from this session's own work, all of them PER-RUN and so
all of them consistent with the shape above, listed to be ruled out
rather than assumed:

- `_group_of_our_layers` runs THREE times per run -- at launch, in
  `_get_or_make_group`, and again for `renamed_mid_run` -- and each
  call asks `root.findLayer()` for up to nine layer ids. `findLayer`
  walks the layer tree, so the cost rises with how many layers the
  user's project holds, which is invisible on a fixture of four and
  is not invisible on a real project;
- the missing-ramp notice asks `bridge.get_ramp(name)` once per
  assignment per run, and `get_ramp` queries the style database and
  CLONES the ramp. A lookup was measured at 0.024 ms in another
  context, which would make this negligible -- but that figure was
  taken for a different question and should not be reused here;
- `_newest_output_group` now examines every top-level group's
  children, though only at construction.

**THE QUESTION WAS MIS-SCOPED, AND THAT IS THE MOST IMPORTANT LINE
HERE.** Clarified by the maintainer after the measurement below: the
tester is not reporting an rc4-to-rc5 regression. He is lamenting
that the plugin USED TO BE efficient, responsive and easy to ITERATE
with, and no longer feels that way. That is a drift over many
versions and a complaint about the interactive loop, not about one
release and not about Generate.

So the measurement below answers a real question -- did this release
make it worse -- and not the one being asked. What the asked question
needs instead:

- profile ONE INTERACTIVE TICK, not a run: nudging a spinner,
  changing a ramp, a table rebuild, a preview redraw. "Easy to
  iterate with" lives in the 350 ms and 900 ms debounces, and a
  Generate measurement says almost nothing about them;
- baseline against a version he remembers as SNAPPY -- 0.23.x or
  0.24.0 -- rather than against last night's candidate;
- and read ABSOLUTE costs, not only deltas. A loop can be slow
  without any release having made it slower, and this project has
  already found one such thing by accident: a ramp swatch redrawn
  306,558 times in a single test, uncached since it was written.
  Nobody has ever measured what one interaction costs.

**MEASURED 2026-08-17 AGAINST rc4, AND ALL THREE SUSPECTS ARE
INNOCENT.** Six
full runs at the auto spacing in each tree, profiled, compared by
call count: `569aefb` 1,390,561 calls against `6c7af51` 1,391,768.
**+1,207, or +0.09%.** This session's additions are visible and
minute -- `ramp_or_default` 20 calls, `get_ramp` 60 to 80,
`_group_of_our_layers` 15, `findLayer` 15, `same_destination` 5 --
about ninety calls across six runs.

SO THE PYTHON SIDE IS FLAT, and that redirects the hunt rather than
closing it. A slowdown a person can feel, with call counts unchanged,
means the SAME calls are costing more: Qt and C++ work, repaints, or
something outside this path altogether. The next measurement is
therefore CPU and wall clock per run at both revisions, not counts --
the opposite of the advice that solved the last performance
regression, and for the opposite reason.

Two honest limits on the above. The fixture's auto spacing came out
at 500 with 612 tiles over four elements, which may not be the "large
auto spacing" the tester means; ask what region and what spacing, or
the measurement may be taken where the effect is not. And the
comparison first reported hundreds of large increases that were an
artefact of keying the diff on LINE NUMBERS -- every function in a
file that gained six hundred lines looks new -- which is worth
knowing because the artefact was entirely convincing until each
"increase" turned out to have a matching disappearance at the same
count.

The largest genuine deltas after that correction, neither obviously
costly and both unexplained: `QTableWidget.item` 144 to 860, and
`setEnabled` 144 to 250.

**MOSTLY DONE 2026-08-17, WITH SPACING PARKED AND STILL WRONG.**
`_limit_the_figures_on_show` sweeps every `QDoubleSpinBox` at
construction and sets its decimals from its own `singleStep`, capped
at three significant figures. Measured after: spacing aside, the
angles read "0" and "30" where one of them used to read "0.00", the
insets "0.0", the offset "0.00", scale "1.00", aspect "0.750". Nothing
shows more than three decimals.

SPACING IS EXEMPT AND STILL SHOWS SIX, deliberately and visibly. Its
range is 1e-6 to 1e12 -- twelve orders of magnitude -- so no single
`decimals` suits both a floor plan at half a metre and a country at
fifty kilometres, and the sweep runs at CONSTRUCTION while
auto-spacing sets the value afterwards from the layer. Left to the
rule it took 0 decimals from its step of 1, which would have rounded
a legitimate 0.5 m spacing away: a worse fault than the one being
fixed, and one the standard fixture at 500 m would never have shown.

WHAT IT NEEDS is the rule re-applied whenever the value changes,
which is a small hook on a signal that already fires -- but it is a
hook on the interactive path, and it was not worth adding at the end
of a long session without room to measure what it costs there. That
is the remaining work.

**SILLY NUMBERS OF SIGNIFICANT FIGURES THROUGHOUT THE INTERFACE.**
Reported 2026-08-17: spacing shows six decimal places in metres, and
the ramp bound boxes show nine. Measured across the plugin, every
control decides for itself and in five different ways --
`spacing_spin.setDecimals(6)`, `opt_offset` step 0.01 with 2,
`opt_aspect` step 0.083 with 3, `opt_offset_angle` with a step of 1
and no decimals set at all (so Qt's default 2, giving "0.00"
degrees), the modifier boxes with a local `3 if step < 1 else 1`, and
six QDoubleSpinBoxes in dialog.py that set nothing.

**THE MAINTAINER'S RULE, 2026-08-17: AT MOST THREE SIGNIFICANT
FIGURES DISPLAYED, unless there is good reason otherwise.** That is
the decision; what follows is how to carry it out and the one place
it needs care.

Note it is SIGNIFICANT FIGURES and not decimal places, which is the
stronger and more useful rule: it bounds what a reader has to take in
whatever the magnitude, where a decimals rule lets 1234.567 through
at four decimals and clips 0.0008 to nothing. A spin box, though,
carries a fixed `decimals` while its value's magnitude varies, so the
implementation is to choose decimals from the control's OWN SCALE so
that ordinary values land at three figures: spacing in the hundreds
gets 0, an aspect around 1 gets 2, an offset in 0..1 gets 3.

An earlier suggestion here was to derive decimals from the control's
`singleStep`, which the modifier boxes already do locally
(`3 if step < 1 else 1`). Keep that as the FLOOR rather than the
rule: a box must not show digits its own step cannot reach, and it
must not show more than three figures either. Where the two
disagree, the step is what should change, so one number per control
governs both.

One pass over `findChildren(QDoubleSpinBox)` at construction costs
microseconds once and nothing per repaint, and a control added later
is right without anybody remembering -- which the current
five-rules-in-five-places arrangement is not. Today: spacing at six
decimals in metres, the ramp bound boxes at nine, `opt_offset_angle`
at Qt's default two so degrees read "0.00", and six boxes setting
nothing at all.

THE GOOD REASON, AND IT IS REAL: a control holding a number a PERSON
TYPED, or one taken from the data, must not round it away. The
class-bound boxes size their decimals from the data deliberately
(catalogue entry `the-bound-box-is-sized-from-the-data`), and
clipping a pinned bound of -0.9276 to -0.928 would change the value
the map is drawn from and stamp the rounded number into the project.
So the cap governs SETTINGS a user chooses in round numbers, and a
box that must hold an arbitrary measured value declares its exemption
at the site, with the reason written there. Anything exempt should
still be as tight as it honestly can be: nine decimals on a bound of
-7.5 is not faithfulness, it is noise.

Nothing else outstanding. `CONTENTION` gained its platform term on
2026-08-16 and the entry that stood here is deleted: every timing
allowance is now `CONTENTION * WEAVINGSPACE_TEST_SLOWNESS`, each CI
job declares its own figure with the reason beside it, and
`test_every_ceiling_widens_for_a_slow_machine` fails both when the
suite stops reading the declaration and when a job stops making one.
The figures themselves (Linux 3, macOS 2, Windows 4) are round and
conservative rather than measured, which is said at each of them: the
ratio of the slowest measured runs of one test on both machines is
what should replace them, and nobody has recorded one yet.

## 0.24.4 — after this one

### Wanted

Deferred from 0.24.3 on 2026-08-15. All three are MEASUREMENT: they
say how good the suite is rather than whether the plugin is right,
so none of them blocks an artefact.

**ANSWERED and deleted from here on 2026-08-16.** The rebuild count
was retired dialogs: four routes into `_rebuild_unit` that a dialog
kept open after the user had finished with it, the last of them the
layer combo's own re-emission rather than a project signal. Fixed and
guarded; 1,282 rebuilds down to 173. Kept as one line only because
this entry said the question "changes no artefact", and it turned out
to be the direct cause of a red suite on three platforms -- deferring
it was the wrong call, made on a local measurement too cheap to show
the effect.

**FOR STUDY: warn when a test asserts a string that also appears in
shipped source.** Added 2026-08-16, deliberately as a question rather
than a rule. That is exactly what rotted that day: a test asserted
`"no value" in said`, the maintainer reworded the notice to "do not
have finite numeric data", and the test failed on every platform while
looking like a Windows fault -- a second copy of the wording with no
mechanism keeping the two in step. The repair was to compose the
expected text from the same function the product uses.

What is NOT known is whether a checker can tell that fragment from a
coincidence. Tests legitimately assert on words that appear in source
for unrelated reasons, so this would have to WARN rather than fail,
and a warning nobody can act on is one people learn to ignore -- which
this project has written down twice about other instruments. The study
is: run the comparison over the current suite, count how many hits are
real and how many are noise, and only then decide whether it earns a
place. If the noise is heavy the honest outcome is to drop it and keep
the practice in docs/TESTING.md, where it already is.

**Give the stochastic hunt an exported-file invariant that RUNS.** Added
2026-08-16. A hunt over 105 checked steps reported its five axes:
holes 103, tile totals 103, opacity pairing 23, values-on-no-data 23,
and the GeoPackage comparison ZERO. That last axis never executed, so
a green run said nothing whatever about the exported file while
looking like full coverage. Counting what each invariant actually
compared is the practice worth keeping; an axis that never runs is
indistinguishable from one that always passes.

**Sampling the six unsampled assignment-lookup copies.** Deferred here
from 0.24.2 deliberately: it is measurement rather than
defect-finding, and the night of 2026-08-13 put mutation sampling at
zero product defects across 128 survivors. `_assignment_for` now holds
the lookup, so a future mutant has one place to land.

**Three things the 2026-08-13 instruments audit left undone**, all of
them about tools that produce numbers people then believe. (The
fourth landed on 2026-08-15: `check_standards` now reads every
catalogue entry with `ast` and fails when its anchor is absent, after
seven entries were found anchored on text that no longer existed. It
is asked at push time rather than inside `mutation_check`, which is
where the original entry wanted it -- a sweep run by hand still gets
no preflight, and that is the part left standing.)
`check_standards` compares only the COUNTS in the derived
documents where the generators' own `--check` catches more. Three
`EQUIVALENT` entries exclude nothing. And `mutate_auto`'s watchdog
ignores a child's CPU, so it can score a live mutant as stalled --
the same shape as the two stalls that turned out to be hiding
survivors, which is why the campaign work list also asks that a stall
not count toward a printed rate until it has been re-judged alone.

**Two mutation measurements, neither of them defect-finding.** The
expensive stratum, which nothing has ever measured -- 1,172 of the
1,488 reachable mutants, and the cheap stratum's 59% says nothing
about them. And a certification batch, once the suite stops changing,
since improvement rounds cannot certify themselves.

## Waiting on the upstream project

Blocked on the weavingspace project rather than on this repository, so
no release waits for it.

**Element ids past 26.** Weaves are specified as strings with one
character per element (`abcdef-|ghijk-`), so doubled letters have
nowhere to go, and case-distinguished ids collide on every path that
folds case. That last part is now measured rather than argued: writing
`tiles_a` and then `tiles_A` into one GeoPackage leaves a SINGLE table
holding the second element's data, and both writes report success
(2026-08-14). Going further means changing the weave string format
upstream and in every stored design.

**Two conversations to have.** Whether the corrected large-plain-weave
note was sent (`docs/process/upstream-note-large-plain-weaves.md`
supersedes the first, which blamed a commit wrongly), and the
element-id ceiling above, which is upstream's decision rather than
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
