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

**REMOVE THE HATCHING FROM THE RAMP SWATCHES.** The maintainer's
ruling, 2026-08-17: users are not used to it, so it confuses rather
than helps. The swatches only -- the Pin column is not in scope.

It reverses part of the 2026-08-16 entry in CLAUDE.md, which asked a
different question: whether two hatchings could be told apart from
each other. This one says the mark is not legible to somebody meeting
it. Correct that entry rather than arguing with it.

What comes out with it: the hatching in the swatch painter,
`test_a_hatched_class_hatches_only_itself`,
`test_a_copy_hatches_the_classes_it_leaves_unreachable`, their
catalogue entries, and the hatching passages in CLAUDE.md,
`docs/USER-GUIDE.md` and `metadata.txt`. `unworn_classes` stays --
other code asks it which classes are empty -- and the comment in
`pin_problem` that cites the swatch's hatching as how an unworn class
shows needs its wording corrected in the same commit, since it will
no longer be true.

**DONE 2026-08-17 AND DELETED FROM HERE: equal intervals are equal.**
The middle is cut over the span the pins declare rather than cut from
each column's data and stretched to reach the pin. Two columns pinned
alike now draw the same ladder, Unclassed rides the same rule at fifty
steps, and quantiles is deliberately untouched. Guarded by
`test_equal_intervals_stay_equal_under_a_pin` and two catalogue
entries, both proved caught; the rule is in CLAUDE.md and the
reasoning at the code. `tools/probes/equal_intervals_under_pins.py`
still reproduces the before-and-after in about a minute.

FOUND WHILE PROVING IT, and worth more than the fix: the full suite
had been red since yesterday's pin relaxation.
`test_a_pin_that_cannot_be_drawn_is_refused` still asserted that a
bound outside the data is refused, which the maintainer had reversed
that morning. The relaxation came with a new test of its own and
nobody grepped for the older test standing on the opposite claim. No
CI round could see it, because the roadmap blocked a candidate and
nothing had been pushed.

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

**THE INTERACTIVE LOOP, MEASURED AT LAST -- AND IT IS NOT SLOWER.**
Reported 2026-08-17: the plugin feels slower, and then narrowed by the
tester to the sentence that mattered most -- *tiling at small spacings
does not seem any slower, but the snappy interactive feel at large
"auto" spacing has gone* -- and narrowed again by the maintainer, who
said the complaint is not about one release at all. It is that the
plugin USED TO BE efficient, responsive and easy to ITERATE with.

SO ONE INTERACTIVE TICK WAS PROFILED, against v0.24.0, which is the
oldest version this repository holds and the nearest thing to the one
the tester remembers. `tools/probes/one_interaction.py`, four elements
at the auto spacing of 500, CPU milliseconds per tick:

    tick                        v0.24.0     HEAD
    nudge a design number          57.8     35.2
    nudge the weave unit           58.1     40.4
    pick a different ramp          15.1     18.1
    rebuild the table              87.3     60.1
    nudge, live update ON         225.2    224.1

Python calls across the four cheap ticks: 1,191,851 then 991,486, so
HEAD makes SEVENTEEN PER CENT FEWER. Three of five ticks are markedly
cheaper, the expensive one is unchanged, and picking a ramp costs
three milliseconds more.

**THE PLUGIN'S INTERACTIVE LOOP IS NOT SLOWER THAN v0.24.0. It is
faster.** Two further things were ruled out by measurement rather than
by argument. The DEBOUNCES are identical in both trees, 350 ms for the
preview and 900 ms for a live run, so the wait before anything happens
has not moved. And PROJECT SIZE does not matter: 61 layers in the
project instead of one changed nothing measurable, which retires the
`findLayer`-walks-the-tree suspicion the earlier entry raised about
`_group_of_our_layers`.

WHAT THE ABSOLUTE FIGURES SAY, and nobody had ever measured them.
Nudging a control with live update on -- the tick a real user makes --
costs about 225 ms of CPU inside about 1.7 SECONDS of wall clock. Some
900 ms of that is the live debounce and another 350 the preview one,
so roughly two thirds of what a person waits is deliberate delay
rather than work. If iteration should feel snappier, THAT is the
lever, and it is a design question rather than a regression to hunt:
what should the debounces be, should the preview and the live run
share one, and should a run that is about to be superseded be
cancelled sooner.

TWO ARTEFACTS ON THE WAY, both caught by making the probe print its
own premise, and both worth knowing because they are the same shape.
The live tick first read 3.6x WORSE at HEAD; v0.24.0 had in fact run
no tiling at all on any of those ticks, so the figure compared a whole
run against a debounce. The cause was two-layered -- live update there
waits for a first Generate where a later version does not, and the
four earlier ticks left the dialog in a state where that tree produced
no output. A probe that quietly measures the wrong thing announces
nothing; the fix was to print how many ticks ran a task and how many
tiles resulted, which is now in the probe and would fail loudly.

STILL OPEN, and it is the honest limit: this is one fixture, four
elements, 612 tiles, on one machine. The tester's own region and
spacing were never asked for. If the feeling persists on a real
project the next measurement is his project, not this one.

**DONE 2026-08-17 AND DELETED FROM HERE: the significant figures.**
`_limit_the_figures_on_show` sweeps every number box at construction
and sizes it from its own step, capped at three figures; spacing,
which no single setting suits, is sized from the layer when one is
chosen. The maintainer's rule and both exemptions are in CLAUDE.md,
where they bind the next control somebody adds; the reasoning is at
the two methods. What follows was the entry, kept until this session
only because its last paragraph claimed the spacing half was still
owed after the commit that landed it -- which is the drift this file
exists to prevent, arriving in the file itself.

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
