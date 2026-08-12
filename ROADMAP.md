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

**Enable GitHub Pages**, once: Settings -> Pages -> Deploy from a
branch -> main, folder `/docs`. Until then the project page 404s and
the README links to nothing.

**An OSGeo user ID**, for submitting to plugins.qgis.org. It belongs
to a person rather than to the software; register at id.osgeo.org and
the plugin is owned by that account.

**Two things to say out loud in that submission**, both already true
and both better disclosed than discovered: the vendored MIT-licensed
library under `weavingspace_qgis/vendor/`, and `deps.py` fetching
wheels from PyPI when QGIS lacks them. Plugins get rejected for
hiding the second, not for doing it. Full detail in
docs/PUBLISHING.md.

**Two conversations with the upstream repository.** Whether the corrected
large-plain-weave note was sent (dev/upstream-note-large-plain-weaves.md
supersedes the first, which blamed a commit wrongly). And the
element-id ceiling below, which is upstream's decision rather than
ours.

## After the release, agreed sequence

**Dispatch the mutation instruments remotely** and triage what they
find into `pre-0.24.1rc1`. They report rather than gate, so nothing
here holds a release:

    bash tools/watch_remote_mutation.sh <branch> both v0.24.0

**Run the gallery experiment**, which is coded and has never been
run. It answers whether the visual gallery's Delta-E thresholds
survive a different font stack; if they do, the rendered report
becomes available on three QGIS versions instead of one.

    bash tools/watch_remote_mutation.sh <branch> gallery

## 0.24.1 — next

### Branch-backed

### Wanted, no code yet

**The catalogue sweep's seven flagged entries, judged alone
2026-08-12.** The remote sweep caught 159 of 166 and flagged seven
for a solo re-run, which is the procedure working: every one turned
out to be a different fault, and none of them was the suite being
weak.

THREE AMBIGUOUS ANCHORS — `idle-progress-bar` (3 matching sites),
`live-pending-initial` (3) and `category-colours-cleared-by-ramp` (2).
The tool refuses them rather than reporting a false SURVIVED, which
is the guard added in August doing its job, but the entries are
broken until each anchor is narrowed to the site its `why` describes
— exactly as `fit-to-design-on-show` was narrowed on 2026-08-10, and
the comment there is the model to copy.

`fit-to-design-on-show` IS RESOLVED as far as it can be, and the
answer is not a better test. `_fit_to_design` only calls `resize`,
and Qt refuses to shrink a window below its layout's minimum size —
so the window is already at least as tall as the Design tab needs
whether or not the deferred fit runs. HEIGHT CANNOT DISCRIMINATE
THIS MUTATION, which also means the original test was passing for a
reason unrelated to what it names. An attempt to add "shrink it while
hidden, show it again" failed on healthy code for exactly that reason
and was reverted; it would have been a test that fails either way,
which counts as a kill while proving nothing.

What the deferred fit actually adds beyond the layout minimum is the
WIDTH floor (`max(self.width(), 1180)`) and growing the height to
`sizeHint + 96` rather than merely to the minimum. So either the
entry is re-aimed at one of those observable properties, or it is
accepted as a redundant call site with the reason recorded — which
docs/MUTATION-TESTING.md says is a legitimate outcome, and is
probably the honest one here. Do not write a test that pins the
window's exact pixel height; that is the mutation bookkeeping the
same document forbids.

`family-list-signals-blocked` — DIAGNOSIS, not yet a verdict. The
test counts rebuilds and requires at most one; unblocking the signals
makes the handler run during the refill, but `_on_family_changed`
restarts a debounce timer, so the extra calls collapse into the same
single rebuild. That is the identical reasoning behind the one
equivalence already recorded in `tools/mutate_auto.py` (blocking the
over-under field during a family change), which was retired only
after showing the unit's n, every tile's WKT, the field text, the
table, the preview labels and all element assignments came out
identical.

So this needs the same demonstration before it may be called
equivalent, and docs/MUTATION-TESTING.md is explicit that "this looks
harmless" is how a score becomes a vanity metric. The thing to check
is whether `_on_family_changed` does anything besides queue work —
if it touches the table or element assignments while the list is
half-built, that IS observable and the test should look there rather
than at the rebuild count. If it genuinely only restarts a timer,
record the equivalence with the evidence and take it out of the
denominator.

ONE GENUINE SURVIVOR LEFT, and it is a claim about a TEST rather than
about the plugin. `fit-to-design-on-show`: the named test
`test_the_window_fits_its_design_tab_when_shown` does not fail when
the deferred fit in `showEvent` is removed — almost certainly because
construction already fitted the window, making this one of three
redundant call sites. The recipe is in docs/MUTATION-TESTING.md:
find the scenario only the mutated site can serve (hide the window,
change the design, show it again), or, if there is none, delete the
code rather than defend it. `family-list-signals-blocked`: the test
`test_repopulating_the_family_list_fires_no_handlers` does not fail
when `blockSignals(True)` becomes `False`, so it is not reaching what
it names.

ONE HARNESS LIMIT — `stage-log-says-it-is-running` cannot be judged
at all: it mutates `release.py`, and the sandbox clone the sweep
builds contains only the plugin package, so the run dies with
FileNotFoundError. Either the sandbox copies `release.py` and
`build.py` (it already does for the release-gate tests) or entries
outside the package are declared unjudgeable and skipped loudly. A
catalogue entry that cannot run is worse than one that fails,
because it is counted as neither.



**Write the tests for the ten survivors the guard found before it was
stopped.** This is the work that the incremental guard moving out of
the release path hands to 0.24.1, and it is the reason that move is
not a weakening. Measured 2026-08-11 against `pre-0.24.0`, 28 of 80
mutants judged, 16 killed:

    bridge.py:520    compare <= -> <      (6 covering tests)
    catalog.py:295   number 0 -> 1        (221)
    catalog.py:307   number 37 -> 38      (221)
    dialog.py:3068   number 0 -> 1        (3)
    dialog.py:3200   number 7 -> 8        (1)
    dialog.py:3345   compare == -> !=     (20)
    dialog.py:3391   compare == -> !=     (1)
    dialog.py:3508   call removed         (1)
    dialog.py:3630   compare == -> !=     (4)
    dialog.py:4385   number 1 -> 2        (153)

THE FAMILY READING WAS DONE 2026-08-12, before any test was written,
which docs/TESTING.md requires and which turned ten entries into five
pieces of work. Each line below was read in its source with the
covering tests beside it; no test has been written yet.

ONE IDIOM, NINE SITES — dialog.py:3391, 3630 and the block at 3504
that 3508 belongs to are three of them; a grep finds nine copies of
`next((a for a in self._assignments() if a["id"] == tile_id), None)`.
Flipping `==` to `!=` finds a DIFFERENT element, or None when the map
has one element, and the signature is then stamped against the wrong
id or not at all — so the restyle path re-seeds and discards whatever
the user changed in QGIS's own styling dock alongside the colours.

ALL THREE DONE 2026-08-12, each verified to kill:

* `test_a_dock_refinement_survives_the_next_restyle` — the
  categorized adoption. A stroke width set in the dock survives the
  next style change.
* `test_a_graduated_dock_refinement_survives_the_next_restyle` — the
  graduated twin, five identical lines away. Written separately
  because the catalogue REFUSED an anchor spanning both, which is
  also the argument: two identical pieces of code are two pieces of
  code, and a covering test for one says nothing about the other.
* `test_the_range_editor_repaints_with_its_own_elements_colours` —
  the one whose result a user reads directly. The editor paints what
  the dialog hands back, so the wrong lookup shows a list that is not
  about the element being edited.

Six of the nine copies are still unguarded, and nothing has sampled
them. Extracting `_assignment_for(tile_id)` would collapse all nine
to one site — worth doing when somebody is in that file anyway. It
adds no detection by itself, but it would mean one mutant instead of
nine, and the three faults above were each invisible until a mutant
happened to land on that particular copy.

A TABLE THAT STOPS ONE DICTIONARY SHORT — catalog.py:295. DONE
2026-08-12. `test_every_declared_offset_is_pinned` states the rule
rather than listing names, exactly as it should, but it looped over
`catalog.TILINGS_BY_N` alone while hex-slice and square-slice declare
their offsets in `GENERAL_TILINGS`. The existing loop was widened
rather than a second test written, and the kill verified as
`general-tilings-offset-moved`. Kept here only until the rest of the
family lands, because the lesson generalises: a table test that
covers one container of two fails in exactly the way the shape is
supposed to prevent.

A CONSTANT GUARDED ONLY AGAINST LARGE CHANGES — catalog.py:307. DONE
2026-08-12. `HEX_COLOURING_COUNTS` names 37, which sits above
MAX_ELEMENTS = 26, so the loop over the MENU never reached it. The
lists are measured facts about which arrangements the library
hand-builds and they go on the menu the day the ceiling rises, so
the rule is now applied to the declared lists as well as the offered
ones. Verified as `colouring-count-above-the-ceiling-moved`.

A SWATCH THAT MUST SHOW THE WHOLE RAMP — dialog.py:3200. DONE
2026-08-12, as `test_an_unclassed_swatch_reaches_both_ends_of_its_
ramp`, reading the icon rather than the intermediate list and
asserting both ends. Verified as `unclassed-swatch-stops-short`.

A NOTICE THE PLUGIN MUST NOT MAKE UP — dialog.py:3345. DONE
2026-08-12. Read in place the harm was sharper than this entry
guessed: the adoption path below counts colours that actually differ
and returns when there are none, so what the mutant reaches is the
RAMP-FOLLOWING branch. Widen a stroke in the dock and the plugin
announces "now follows the 'X' ramp chosen in QGIS", clears that
element's picks and restamps its signature. Verified as
`unchanged-colours-read-as-a-dock-recolour`.

TWO ACCEPTED, WITH THE REASONS, which docs/MUTATION-TESTING.md says
is a legitimate outcome and a campaign that never does it is chasing
a number.

`dialog.py:4385` is EQUIVALENT and is recorded in `EQUIVALENT` with a
mechanical demonstration: the enclosing `done` holds exactly two
references to `index`, the store and the `< 0` test, and -2 is as
negative as -1.

`bridge.py:520` is ACCEPTED. It widens the SUGGESTED spacing, not the
map, and the refusal it must agree with is `est >
bridge.MAX_TILES_HARD` at dialog.py:4236 — so exactly MAX_TILES_HARD
tiles is permitted by both, and `<` merely widens one further 2% step
at exact equality. Still a legal map, still under the guard. No harm
can be named, and this entry previously billed it as a boundary
comparison deciding what a map draws, which reading it in place
disproved.

`dialog.py:3068` is ACCEPTED, and the reason is that the honest
answer is "cannot say cheaply". `if count > 0` becoming `count > 1`
differs only at a class count of exactly 1. The class spinner's range
is set to (2, 20) in both places it is set, so for a Graduated row —
the only kind that reaches this line — count is 0 (no spinner) or 2
to 20, and 1 is unreachable. That is very probably an equivalence,
but demonstrating it means ruling out every ordering in which a row
arrives here carrying another mode's (0, 9999) range, and
docs/MUTATION-TESTING.md is explicit that a mutant which merely
LOOKS equivalent must not be declared one. At count 1 no user harm
can be stated either way: the healthy path drops picks whose class no
longer exists, the mutant leaves them, and the renderer has one class
regardless. Accepted rather than claimed.

**Resume does not understand a stage whose product is a FILE.**
`skip_if_already_done` reads back a stage's captured text, so it can
honestly skip the suite or the gallery. It cannot skip the per-test
coverage record, because that stage's value is the shard files the
merge consumes — and the merge deletes them on success. Skipping the
record therefore leaves the merge with nothing and aborts the run,
which is a trap rather than a saving. Give a stage an optional
declared ARTEFACT, and let it be skipped only when the artefact is
present; record and merge would then share
`reports/per-test-coverage.json` and skip or run as a pair. Found the
same night resume was built, by nearly falling into it.

**One watcher, not a fresh script each time.** Five separate watcher
faults in one day (2026-08-11), all in scripts written while
attention was on the thing being watched: one repeated itself, one
read a stale log after a restart, two matched the wrong process for
their CPU field, one reported the previous run's CI result. Each was
individually trivial and the pattern is not. A single supervised
watcher — resolve the log freshly, report change rather than state,
name the process it is measuring, stop when the thing it watches
ends — would have prevented all five.

**Ceilings sized from measurement rather than belief.** Three were
set wrong in one day, each producing a red result that meant nothing:
a forty-minute CI job limit against 52-54 minute legs, a
600-second per-test watchdog against a test that legitimately takes
855 under coverage, and the same watchdog against a suite whose costs
multiply by six when monitored. There is a general fix available:
have the suite record each test's duration and size the ceiling from
the slowest observed run rather than from a constant somebody chose.

**Element ids past 26.** Blocked upstream rather than here. Weaves are
specified as strings with one character per element (`abcdef-|ghijk-`),
so doubled letters have nowhere to go, and case-distinguished ids
collide on every path that folds case — GeoPackage table names,
case-insensitive filesystems, saved layer properties. Going further
means changing the weave string format upstream and in every stored
design. Worth raising with the weavingspace project before anyone
attempts it.

**Antivirus cost on the macOS suite, measured rather than assumed.**
Cisco Secure Endpoint was using ~26% of a core across two processes
while the suite ran, and this suite creates and deletes thousands of
short-lived files. One timed run with the scratch directory excluded
against one without would settle whether that is a real tax or
background noise.

**Audit the docstrings and inline comments across the whole
codebase.** The documentation standard says every reachable function
carries a docstring naming its inputs, its outputs and what was
mutated, and that comments sit at the points a reader would otherwise
stop and wonder. `check_standards.py` enforces the PRESENCE of those
things; nobody has read them for TRUTH since they were written.

That distinction matters here more than in most projects, because
this one's standard makes stale documentation actively harmful: a
docstring is the only account of why a line takes the shape it does,
and a wrong one is followed with confidence. A previous audit of a
much smaller surface found three outright lies -- libs "appended",
live update "after first Generate", a box that had been removed --
and the code has moved a great deal since.

What to look for, in order of harm: a docstring describing behaviour
that changed; a comment citing a measurement that has since been
re-measured (several dates and figures were revised today alone); a
"why" that names a bug now fixed, or a workaround now removed; and an
Args block that has drifted from the signature. Doing it per module
with the tests open beside it is the only way it stays honest.

**The note line's negative assertion.** DONE 2026-08-12.
`_notes_during_a_run` collects every distinct note across a window,
so "categories must NOT appear" can no longer be satisfied by a line
the plugin cleared a moment earlier. Measured honestly: the old
single read also fails against
`category-shift-cries-wolf-on-first-sight` on this machine, so the
change bought robustness in a slower harness rather than detection
today -- which is the failure that actually happened to the two
POSITIVE reads of the same line under the coverage recorder.

The rest of the sweep of `live_note` reads still stands. Most are
`bool(text) or bool(MODALS)` and are fine; the ones worth a second
look are any that assert an ABSENCE, since those are the shape that
silence satisfies.

**The progress chart draws stages the run will not execute.** Under
`--quick` it still lists the 31-minute coverage report among the
stages to come and adds it to the estimate, so the finishing time it
prints is about half an hour pessimistic. It misled twice on
2026-08-11. Display only -- no measurement is affected -- which is
why it was not fixed in the middle of a release.

**Backfill discovery shapes on the 33 bug-register entries** that
predate the convention.

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


**Badges on the README**, and the "minimalist faux 3d" button styling
the user mentioned. Both cosmetic, neither designed.

**The custom ("this") weave type**, with its tie-up, treadling and
threading matrices. Deprioritised rather than rejected: it needs a
matrix-entry UI and its own documentation.
