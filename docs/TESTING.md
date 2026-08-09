# Testing this plugin: what works, and what has already failed

This is the consolidated record of how testing is done here and, more
usefully, of the ways it has gone wrong. Nearly every rule below was
paid for once already. Read it before writing or changing tests.
`docs/MUTATION-TESTING.md` covers the campaign that keeps the suite
honest and what we promise about its score;
`docs/MUTATION-LOOP.md` is the runbook for actually running that
campaign, from launching a cycle to the stopping rule. CLAUDE.md makes
all three binding.

The suite lives in `tests/run_tests.py` (behaviour), `tests/visual_tests.py`
(a rendered gallery, scored in a perceptual colourspace), and
`tools/` (coverage, mutation, standards, secrets). Everything runs
under QGIS's own Python; `release.py` gates on all of it.

## The test shapes that earn their keep

**UI against library.** The highest-value shape here: drive the
dialog, then build the same map by calling weavingspace directly with
what those settings MEAN, and compare geometry element by element and
then interior pixels. Three real bugs came out of this that every "a
map appeared" assertion had passed over: Generate inside the 350 ms
preview debounce tiled the PREVIOUS design; identity modifier
transforms (rotate 0, scale 1) rebuilt geometry with enough rounding
to flip tie-prone joins; and a rebuilt table cycled a default variable
back into an element the user had deliberately unassigned. Write the
expected side from the settings, never from `_build_unit`, or the test
agrees with the bug.

**Visual, wherever a map is produced.** Two forms: `visual_pair` when
the settings can be restated independently, and `visual_gamut` when
they cannot, which asserts every interior pixel is a colour the
symbology in force can make. A map-producing test that only counts
features is not finished.

The gamut is the colours the map is ENTITLED to use, which is not the
same as the colours on its ramps. That distinction did not matter
until the Categorical colour editor arrived, since the ramps were the
whole of it; a hand-picked colour is deliberately off every ramp,
which is the reason someone picks one. So `visual_gamut` takes
`extra_colours`, and a test covering hand-picked colours passes them.
Widening the gamut this way is not a loosening: the check still fails
on a blank map, a wrong ramp or corrupted symbology, and the pairwise
test does the positive work of proving the right colour reached the
right element. Recorded here because the alternative — quietly
exempting these tests from the visual rule — is how a rule decays
into a habit.

**Test the FAMILY, not the member.** When a mutation batch turns up
the same kind of survivor repeatedly — a default nobody asserted, a
range nobody pinned, a tooltip nobody read — the answer is one
table-driven test over the whole family, not one example test per
survivor. `CONTROL_DEFAULTS` and `CONTROL_CHECKBOXES` in
tests/run_tests.py pin twenty-four controls' defaults, ranges, steps
and labels in two tests; `test_every_control_explains_itself` covers
thirty-six tooltips; `test_every_declared_offset_is_pinned` states
the rule ("every offset is 0") rather than listing twenty-six names.
A new control or entry is covered the moment somebody adds a row, and
a whole class of mutant dies at once.

Evidence for the shape: across three batches, 37 of 50 survivors came
from just two operators, "call removed" and "number changed", and
almost every one was a default, a constant, a catalogue value or a
configuration call. Fixing those individually took most of a day and
covered only what had been sampled; the tables cover what has not
been sampled yet.

**What a table test IS, stated plainly, because it is easy to
overclaim.** A table of defaults, ranges and steps is REGRESSION
protection, not correctness testing. It cannot tell you a default is
wrong today; it can only tell you it changed. An earlier version of
this section claimed that reading the values from a live object rather
than transcribing them from the source stops the table agreeing with
the code's bugs — that was wrong. Reading from a live object is still
deriving the expectation from the implementation, by another route.
The justification for these tables is that the values are design
decisions recorded in CLAUDE.md and a silent change to one is a real
regression; it is not that they verify anything.

That has a consequence for the mutation score, and it should be said
out loud. A table kills numeric mutants very cheaply: `20 -> 21` dies
because a line says 20, which is one step from asserting that 20
equals 20. **The score rises further than the detection ability
does.** When a round adds table tests, expect the rate to improve for
two different reasons, and do not read the whole improvement as the
suite getting better at noticing bugs. Where it matters, classify
which mutants newly died: those caught by behavioural tests (the
preview must draw, cancel must return the dialog, a ramp must produce
its declared colours) are detection; those caught by a pinned
constant are regression cover.

Watch, too, what the environment supplies: the declared spacing
default is 1000, but a dialog built with a layer present shows 500,
because auto-spacing legitimately sized it to that layer. The table
asserts what a user meets on a fresh dialog with an empty project,
and the auto-spacing behaviour is a separate test.

**Integration sessions over single behaviours.** The failures in this
plugin live in state carried across generations, so a session that
changes styling, then variables, then spacing, then styling again
finds what a dozen isolated tests do not. Check at several MOMENTS
inside a session, not only at the end: a wrong intermediate state
usually corrects itself by the last generation and hides.

**Races, in three layers, because they catch different things.**
Handpicked races for known-dangerous moments (mid-flight settings
change, two Generates, restyle during a run, close during a run,
region layer deleted mid-run); a sweep changing EVERY control while a
tiling is in flight, since any control can be swallowed the same way;
and a seeded fuzz test firing random action sequences against
invariants. The invariant that matters most is that the map matches
what the table asks for: it is what caught a ramp picked mid-run being
lost.

**Metamorphic and model-based tests**, where no oracle exists: relations
that must hold between two runs (translating the region translates the
map; doubling spacing quarters the tile count), and a state machine
whose transitions are checked against the dialog's actual behaviour.

## Lessons, each paid for once

**Tests must run with an EMPTY project.** Everything shares the one
QgsProject singleton, so a test that leaves layers behind changes
which layer the next dialog picks. A single real failure once cascaded
into four unrelated ones.

**A test that passes is not a test that works.** It must FAIL when the
behaviour it names is broken. This is the most expensive lesson here:
in one session, six tests were written to close gaps that automatic
mutants had found, verified to pass, and then re-judged against those
same mutants — and most of them did not kill. Passing was never the
question. Every test written to close a mutation gap gets an entry in
`tools/mutation_check.py`, which breaks the behaviour and requires
that test to fail; the release runs it.

**Before believing a survivor is a gap, count the call sites.**
Deleting one of several redundant calls leaves the others to do the
work, so no test can discriminate and none should be contorted into
trying. `_update_layer_exclusions()` is called both in the constructor
and after every run: deleting the constructor's call is invisible to
any test that generates first, and visible only to a dialog opened on
a project that already holds output. That distinction is the whole
test. Where the second call site turns out to be genuinely redundant,
delete the code rather than defend it.

**Test a switch where it BITES.** Measured, not assumed:
retain-complete-tileables changes nothing unless the whole-tileable
join is on and edges are ragged; the join changes no data at all in
icon mode. Both were "covered" by tests in configurations where
severing the control from the library changed nothing.

**Prefer one systematic test to many specific ones, where the property
is general.** Automatic mutants delete signal connections, and each
deletion leaves a control that looks normal, accepts input and does
nothing whatever. Five separate tests were written for five such
deletions before it became obvious that the property is general and
that `dialog.py` carries more than thirty connections: testing them
one at a time is a losing race. `test_no_control_is_dead` walks every
control each family shows, nudges it by one step, lets only the
dialog's own debounce run, and requires something visible to move.
Controls whose effect is genuinely elsewhere are exempt BY NAME, each
citing the test that does cover it, and the test asserts those cited
tests still exist -- an exemption list is exactly where a dead control
would hide, so an entry there is a citation and not an excuse.

**A control must act through its OWN signal.** Tests that change a
control and then call `_rebuild_unit()` themselves prove nothing: the
connection could be deleted and the test would still pass. A user has
no such option. Change the control and let only the dialog's own
debounce run.

**The environment can satisfy the thing under test.** QGIS stores
colour ramps in the user's profile, so on a machine that has run the
plugin before, its palettes are already installed and a test that
merely asserts they are present passes no matter what the installer
does. Create the condition the test needs -- remove one palette, then
require the installer to put it back -- rather than assuming a clean
machine. The same caution applies anywhere state outlives the process:
the QGIS style, the plugin's own settings, a GeoPackage left behind by
an earlier test.

**Defaults are masked by the things that override them.** The 1000 m
spacing default is invisible in any test that loads a layer, because
auto-spacing immediately overwrites it. Assert a default where nothing
can supersede it — for that one, an empty project.

**Look up fixture names rather than typing them.** A test that selected
the family "star 6", which does not exist, silently skipped its own
assertions behind an `isVisibleTo` guard, and a deleted signal
connection survived a whole batch because of it. Where a test needs a
family with a particular option, find it in the catalogue.

**Re-record `tools/coverage_per_test.py` after ANY suite change.** The
record decides which tests are offered the chance to notice a mutant,
so a stale one silently excludes every test written since it was made.
The error is one-directional: survivors are overstated and the newest
work is exactly what gets ignored. `mutate_auto.py` now refuses to run
against a stale record.

**Image metrics need calibrating against known-good output before
their thresholds mean anything.** Unweighted unique-colour comparisons
are dominated by antialiasing blends — a visually identical pair once
scored ΔE 11. Weight by pixels, and sample interiors.

**A waiter must first check that anything STARTED.** When the restyle
fast path landed, every style-only step sat out a 120-second backstop
waiting for a callback that was never coming; two tests went from
seven seconds to twenty minutes and the release looked hung. If a code
path can now finish synchronously, the waiter has to know.

**Diagnose a suspected hang by CPU, not elapsed time.** A process
burning two minutes of CPU across forty minutes of wall clock is
blocked, not busy, and that distinction points straight at the cause.

**Wholesale span-rewrites of a test file silently DROP assertions, and
absent tests pass.** A graduated-controls block vanished this way
unnoticed. Prefer targeted edits, and grep afterwards for the
assertions you believe exist.

**Grab widgets only after showing them.** Qt lays out lazily;
`grab()` on a never-shown dialog renders phantom sizes and unreliable
visibility. Probe state programmatically, screenshot after `show()`,
and let a legitimate rebuild settle before capturing widget
references.

**Never run two full suites at once**, but do parallelise short runs.
Two QGIS processes tiling and rendering slow each other to a crawl and
the result reads as a hang; one release was abandoned at forty minutes
for exactly this. Mutation judging is different work: measured, six
mutants took thirteen minutes serially and seven with three workers,
with identical verdicts. Per-mutant times still inflate 15-50%, so
watch the stall count — a mutant slowed past the watchdog's patience
is recorded as caught, which means contention can quietly flatter a
mutation score.

**No unconditional modal dialogs on generation paths.** A QMessageBox
blocks a headless run; one hung the suite for thirty-one minutes. The
harness patches QMessageBox and the plugin reports quietly instead.
