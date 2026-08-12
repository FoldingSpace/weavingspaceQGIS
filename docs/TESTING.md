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

## The differential sweep: reproducing and sharding

Three environment variables, all added 2026-08-10 while chasing a
divergence that took a day:

    WEAVINGSPACE_SWEEP_SEED=20260808     the run's random seed
    WEAVINGSPACE_SWEEP_CASES=1700        how many designs it drew
    WEAVINGSPACE_SWEEP_ONLY=589          examine only these cases
    WEAVINGSPACE_SWEEP_SHARD=0/4         examine every fourth case
    WEAVINGSPACE_SWEEP_DUMP=1            dump both sides' renderers

Every case is DRAWN whichever of these is set -- drawing is
microseconds, tiling and rendering are the minutes -- so a selected
or sharded run produces designs identical to the full one. That is
what makes the results comparable, and it is why ONLY refuses a case
beyond CASES rather than widening silently: a reproduction that
changes its own context is worthless.

Four shards cover 1,700 cases in about a quarter of the time. Sweep
cases are independent renders, so they parallelise the way mutation
judgements do and not the way a whole suite does.

## Instrument the code under test, never replace it

Two of the four false diagnoses in one day's bug hunt came from
probes that monkey-patched the very function being studied. A spy
that stands in for the comparison helper does not assign the ramps
the helper assigns, so it "discovered" that the dialog was using its
default ramps -- which was true of the spy's run and false of every
real one. The reading looked like evidence and was an artefact.

If you must observe a function's innards, add a dump INSIDE it behind
an environment flag and run the real thing. It costs three lines,
it cannot drift from what actually runs, and it can be left in place
for the next investigation. The dump that finally named the bug
(`WEAVINGSPACE_SWEEP_DUMP`) took two minutes to write after a day of
reconstructions that each had to be argued about.

The same applies to reproductions: a selector that quietly widens a
run's case count changes the run it claims to reproduce. Make such
tools REFUSE rather than adapt.

## A seeded sweep's case numbers mean nothing across seeds

The differential sweep draws its designs from a seed that varies per
run, and numbers the cases within that run. So "case 259 failed" and
"case 259 now passes" are statements about two DIFFERENT designs
unless the seed matched, and treating one as evidence about the other
is comparing two things that merely look comparable. That error cost
a wrong conclusion sent to an upstream maintainer on 2026-08-10.

Rules that follow, and they are cheap:

- **read the seed out of the log before comparing runs.** It is
  printed beside every case;
- to re-test a specific failure, pin the SAME seed
  (`WEAVINGSPACE_SWEEP_SEED=<n>`) rather than trusting case numbers;
- when reporting a sweep result to anyone, quote the seed with it.

The same caution applies to any sampled instrument here: a census is
exact for its stratum, a sample is not, and neither is comparable
with a differently-drawn one.

## The modal recorder keeps the sentence, not only the title

`_no_modal_dialogs` replaces every QMessageBox with a recorder, and
what it records is `(kind, "title text")` -- both strings joined. It
kept only the FIRST string until 2026-08-09, which is the window
TITLE, so every entry read "WeavingSpace" and no test could ask the
question that matters: was the user told, in words, what went wrong?
A campaign-3 test had to widen the shim itself before it could
assert that, which is the signal that a harness limit has become a
test's problem. If you find yourself patching QMessageBox inside a
test, fix the recorder instead.

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

## Finding your way around 9,000 lines

The suite is one file. `docs/TEST-MAP.md` is its index, generated by
`tools/test_map.py` from the suite itself and rebuilt at every
release, so it cannot describe a suite that no longer exists. Read it
before adding a test: it shows which areas are thin, and it is the
fastest way to find whether something is already covered.

The column worth scanning is **guarding a real defect** — tests whose
docstring carries a `Regression:` line, meaning that defect actually
happened here. A test without one guards ground we imagined rather
than ground we fell through. An area with many tests and few
Regression lines is not necessarily well tested; it may only be well
imagined. As of the first map: 145 tests, 35 guarding a real defect.

Two things the map is deliberately NOT. It is not a coverage report —
`tools/coverage_report.py` says which lines ran. And it is not an
argument for splitting the file: coverage of intent is not the same
shape as file boundaries, and moving 130 functions risks silently
dropping one from the safety net that guards everything else. If the
file is ever split, verify it by comparing the registered-name list
and the pass/fail set before and after; they must match exactly.

## What a second machine finds, and why it could not be found here

The first Linux CI run (2026-08-11) failed seventy tests. Every one
was real, none was a plugin bug in the ordinary sense, and not one
could have been found on the development machine at any effort. They
are worth listing by KIND, because the kinds recur:

**The environment supplies something you never noticed depending
on.** Sixty-nine of the seventy were one missing geopandas: the
`qgis/qgis` images ship QGIS and nothing else. A later round found
the same thing wearing a better disguise -- a child process reporting
"no tiles were produced under a comma-decimal locale" when what had
actually happened was `ModuleNotFoundError`. The suite put ROOT and
`vendor/` on `sys.path` but never `libs/`; that path arrived only
when something imported `weavingspace_qgis` early enough, which
happened by luck in the parent and never in a child. On a machine
whose QGIS already carries geopandas the omission cannot show.

**Identifiers that differ only in case.** Three separate instances in
one day. QGIS on Linux ships `Cividis` where this plugin's table says
`cividis`, and the installer skipped it case-insensitively while the
lookup matched exactly -- so four palettes were unavailable to every
Linux user with the chooser still offering them. Element ids past 26
run into `A` beside `a`. GeoPackage column names collide the same
way. Whenever an identifier leaves Python -- into a filename, a
table name, a style library -- ask what happens when case stops
distinguishing two of them.

**Documentation naming something no clone contains.** Three documents
told a maintainer to iterate with a subset runner that lived in the
gitignored working-notes directory, so the command they recommended
named a file no clone contained. It is `tools/run_some.py` now. Only
somebody who was not us could ever have found out, and CI was the
first checkout that was not this machine.

That paragraph broke the same test twice, which is the part worth
keeping: writing the HISTORY of a moved file quoted the old path
again, and `test_every_documented_command_still_exists` refuses any
quoted path that does not exist -- rightly, since it cannot tell a
recommendation from a reminiscence. Describe a path that has gone;
do not quote it.

**A crash with nothing to say.** QGIS 4.2.1 segfaulted reading one of
our GeoPackages: exit -11, both streams empty. `faulthandler.enable()`
in the child turns that into a stack, and a `STEP` line before each
phase narrows it further. Add both to any child process before you
need them; after a crash it is a fifty-minute round to add them.

The general rule: **a suite that has only ever run in one place is
measuring that place as much as the software.** The value of the
second machine is not redundancy, it is that the assumptions become
visible.

## The artefact nobody opened

Every test here imported the plugin from the CHECKOUT. The release
built a zip and never opened it. So the first thing a user does --
unpack the archive into a QGIS profile and let QGIS call
classFactory -- was the one thing neither machine tested, on either
platform, at any point in this project's life.

That gap is invisible from inside the suite, because everything the
suite needs is already on sys.path. The failures it hides are
specific: an archive whose shape the plugin manager refuses, a file
the packing rule forgot, an import that only ever worked because the
repository happened to be importable, an `unload` that leaves a menu
entry pointing at code QGIS has dropped. None of those can fail a
test that never leaves the working tree.

`tools/install_and_load.py` does what QGIS does, in QGIS's order, and
runs on every push in its own CI job. It found a fault on its first
run -- in its own stub, which had guessed at the interface methods
the plugin calls rather than reading them. That is worth keeping as
the lesson: **a stub written from memory tests your memory.** The
methods were four greps away.

The general form, and it is worth asking of any project: what does
the user receive, and has anything ever opened THAT? Not the source
it was built from -- the thing in their hands.

## A test's name is a hypothesis about its own failure

`test_a_comma_decimal_locale_does_not_corrupt_numbers` failed for two
CI rounds. It was not a locale fault; the child could not import
geopandas and fell over at the first assertion it reached, which
happened to be about tiles. The name and the message together told a
confident, wrong story, and it was believed twice.

Two habits follow, both cheap:

- **Say what you found, not which assertion you reached.** The
  message now carries the layer count, the per-layer features, the
  spacing as stored and as shown, what the user was told, the C
  numeric locale and the exception from building the unit directly.
  It diagnosed itself on the next run. Where a round of feedback
  costs forty minutes, a message that only names the assertion is a
  guarantee of guessing twice.
- **A failing assertion is evidence about ONE line.** Everything
  else in the docstring is a hypothesis that has not been tested,
  including the part that names the test.

The same shape appears in a subtler form: an assertion message that
CONTRADICTS its own subject. The stale element-count test said "the
catalogue carries counts the chooser does not offer" when the chooser
offered them perfectly well, and the handover recorded a real
user-facing gap that never existed.

## A stack pointing at your newest change is a hypothesis

The per-test watchdog fired on a stalled test and printed the main
thread's stack, which ran straight through a function changed an hour
earlier -- the case-insensitive ramp lookup, which really did query
the style database once per ramp icon per row. Everything fit, and it
was wrong: measured, that lookup costs 0.024 ms, so even thousands of
them are milliseconds against a ten-minute stall.

What actually explained it was in the timings nobody had looked at:
the same test took 392s, 486s and 550s on three legs of ONE round, on
identical code. The spread is the runner.

A stack tells you where a process WAS, which is not why it was slow.
Before accepting the obvious culprit, measure it -- and prefer
evidence that varies independently of the suspect, like the same code
timed on three machines. The cache was kept because it is right on
its own terms, and labelled in its commit as not the cause, because
the next person will otherwise read the fix as the diagnosis.

## Ceilings, and the two ways to get them wrong

A watchdog exists to catch a HANG. It is not a performance budget,
and every time it is used as one it produces a red result that means
nothing -- which is how people learn to ignore red results.

Both mistakes were made on 2026-08-11, hours apart:

- a forty-minute CI job limit, sized against the twenty-four-minute
  macOS suite, forgetting that the Linux legs are slower and that a
  provisioning step downloads a scientific stack first. All three
  legs took 52-54 minutes; one was cancelled at forty, mid-run;
- a six-hundred-second per-test watchdog against a test already
  measured at 550 on a Linux runner. It passed inside the ceiling by
  ten per cent, then stalled on the next round.

The rule: size a ceiling from the SLOWEST figure ever measured, not
from the machine in front of you, and multiply. Where a test is
legitimately long -- these two sweep an action across several debounce
boundaries, so their cost is mostly waiting -- give it a named
allowance with the measurement written beside it, as `_stall_ceiling`
does. A ceiling with a reason can be raised by whoever meets it; a
bare number gets doubled by whoever is annoyed by it.

## A child process inherits the suite's own environment

A test that spawns a child gives it this process's environment, and
this process is not the plain one you ran while writing the test. In a
release the suite is SHARDED, so `WEAVINGSPACE_TEST_SHARD=2/3` is set;
a child that reads that variable is told it is shard two of three and
behaves accordingly. A new test of the coverage recorder asserted on
the unsharded filename, passed every time it was run on its own, and
failed inside the release -- the one place it had to work -- costing a
candidate on 2026-08-11 after the whole suite had run.

The habit that follows is cheap: when a test launches a child, pass an
environment you CHOSE rather than the one you inherited. Remove the
variables the suite sets, then set back exactly what the case needs,
and write a case for each value that matters. Verifying the test under
the conditions it will actually meet is the other half -- running it
alone proves it works alone.

The general form is the same trap as "the environment can satisfy the
thing under test", arriving from the opposite direction: there, state
outside the test made a check vacuous; here, state outside the test
made a sound check fail.

## One fix, two loops

The palette test was narrowed to ramps this plugin installed, and
failed on the next round at a different assertion in the same test --
the interior-stops check, a separate loop that had not been narrowed.
A half-applied fix reads as progress, because the failure MOVES. When
a fix is a filter or a guard, grep for every place the same
comparison is made before believing one edit finished it.

## Lessons, each paid for once

**A workaround for someone else's bug needs a canary.** When this
plugin works around a defect in QGIS, the workaround outlives every
memory of why it exists and becomes folklore nobody dares touch. So
each one gets a test that asserts THE BUG, going straight to the
dependency with the plugin out of the way
(`test_qgis_still_counts_nulls_as_zero` is the model). While it
passes, the workaround is earning its place. When it fails, the
upstream bug is fixed and the suite has just told you so. The failure
message must say that in as many words, and must say "do not relax
this assertion", because the reflex on a red suite is to make it
green and that reflex would hide exactly the change the test exists
to report.

**A tool that filters what it shows you can hide what you needed to
see.** `text_review.py` skipped any string starting with `{`, to
avoid format keys — and thereby dropped every user-facing sentence
opening with an interpolated value, three of which were live. The
tool's own docstring said a false negative ships unread text, which
is what happened. When a heuristic decides what a human reviews,
check what it is throwing away, not just what it keeps.

**An invariant can demand that the software get it wrong.** The
sequence test asserted that every edit changes the map. Two of its
steps then failed, and both times the plugin was right and the test
was not. Dropping the only mapped column leaves nothing assigned, so
the run is refused and the previous map stays -- correctly, and out
loud. Reprojecting a 3857 layer to 4326 gives back the SAME map,
because geographic layers are reprojected to Web Mercator before
tiling, so the tiles arrive where they began. A sweeping invariant
("everything changes the map") is comfortable to write and will
quietly encode a misunderstanding; state the expected behaviour per
step, and when a step surprises you, work out which of the two of you
is wrong before changing either.

**Assert what must be true, not the easiest observable nearby.** The
same test asserted that the spacing NUMBER changes when the CRS does.
It does not: reprojecting the same ground re-derives the same
metre-equivalent spacing, so 500 stays 500 -- which is the
degrees-against-metres equivalence holding. What must be true is that
the plugin NOTICED, so the assertion is on the dialog's record of the
CRS.

**A stub that collects nothing hides whatever passes through it.** The
message-bar stub absorbed its calls and returned a FRESH instance per
`messageBar()` call, on the reasoning that a test wanting to know what
was said could read the dialog's note line instead. That reasoning was
wrong twice over. `_report_quietly` writes to the note line only when
there is NO iface, so the path a real user is on went nowhere
observable; and after a run the note line is cleared within a second
anyway, because adding output layers makes the layer combo re-emit,
which queues a live render, whose first act is to clear it. Every
notice the plugin raises after a run — areas that received no tiles,
categories whose colours moved, a constant column — was therefore
invisible to the suite in both paths at once, and the coverage notice
had been shipping unverified for months. `_Bar` now records into
`BAR_MESSAGES`, which `check` clears per test. A stub exists to keep
the code path identical, not to swallow the evidence.

**A fixed wait after a run is a guess about two races.** The note
line is transient by design -- adding output layers makes the layer
combo re-emit, which queues work whose first act is to clear it -- so
a test that runs the loop for a fixed 200 ms and then reads it is
betting on which lands first. That bet held for months in the plain
suite and lost under the COVERAGE RECORDER, where every step costs
about six times as much: one test passed at 19:37 and the identical
code failed at 20:01 in the recorded run, aborting a candidate forty
minutes in. Sample instead (`_note_after_a_run`), keep the strongest
thing seen, and let the assertion quote it. Sampling cannot hide a
defect, since a notice that never appears still fails; it only stops
the read landing on the wrong side of the clear.

The general form: **any test whose timing was tuned in one harness
will be re-tuned by another.** The recorder, a sharded run and a
loaded machine are all different harnesses, and this suite runs in
all three.

**"Immediately" is one interleaving out of many.** Race tests here
fired their second action with no delay, which only ever exercises the
state before any debounce has fired. The dialog has two debounces (350
ms preview, 900 ms live) and a task whose completion does main-thread
work, so an action at 400 ms meets a different machine from one at 0
ms, and one at 1,000 ms meets a third.
`test_staggered_actions_during_a_run` sweeps a delay across both
boundaries for each action. When adding a race test, ask which
*stages* exist, not merely whether two things can happen at once.

**A fixture can make a case vacuous without failing.** The first
version of the simplify case built square regions — and Douglas-
Peucker keeps every vertex of a square, so "simplify" returned the
identical polygon and the test asserted that an unchanged region gave
an unchanged map. It passed for a while as a fix was being written,
proving nothing. The polygons now carry a notch that simplification
actually removes. Whenever a test mutates a fixture, check that the
mutation CHANGED it.

**Fingerprint the thing the user would notice.** That same test
compared tile count and extent, both of which survive a region being
reshaped inside its own bounding box, while the map genuinely changes
because each tile has drawn from a different area. The fingerprint now
reads the VALUES joined onto the tiles. A comparison that cannot see
the defect is not a weaker test, it is a passing one.



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
