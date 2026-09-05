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

The full account behind each lesson is in `TESTING-archived.md`, by the
id the lesson quotes (T-31): the run that produced it, the wrong
hypotheses, the measurements. Every lesson's rule is still here. Read the
archive when you are about to do the thing a lesson warns against and
want to know what it cost. See docs/DOC-ARCHIVING.md.

## A PROBE HAS A KIT NOW, AND ITS TRAPS ARE IN IT

2026-08-28. `tools/probe_kit.py` is the forty lines every probe was
re-typing -- QGIS up, an empty project, a dialog, a held temporary
directory, the modal shim, both message stores, a sqlite reader that
does not hold the file open.

IT IS A CORRECTNESS TOOL RATHER THAN A CONVENIENCE. An audit counted
373 one-shot probe scripts in one session, roughly forty lines of each
the same setup -- and eleven hand-written wrappers all setting
`QGIS_PREFIX_PATH` to a doubled path, so those hunts probed a QGIS with
no colour ramps and none of them knew. A shared harness is wrong once
instead of eleven times. (T-119.)

WHAT IT DOES NOT DO is decide anything for you. `probe.dialog()`
switches live update OFF and says at its own docstring that this is a
decision to revisit, because the product's default is ON and a whole
family of resume tests was found driving a setting no user holds.
`moved()` and `unchanged()` are there to make a premise cheap to
assert, which is the one habit that catches the rest.

Run a probe with the checkout on the path, or the kit cannot import
itself:

    PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 "$QGIS_PY" my_probe.py

## A SURVIVOR CAN BE REPORTING A JOURNEY, NOT A WEAK TEST

2026-08-29. An entry over the stamping guard SURVIVED, and the test it
named was sharp and its assertions were live. What it was reporting
was simpler: that test presses Generate, and the code the entry stands
on is only reached by a STYLE CHANGE, so the journey never went near
it. Giving the test one more leg -- pick a colour on the map in
question, require the colleague's layers to carry no record of it --
made the entry catch first time.

This file already carries "when an entry survives, ask whether the
behaviour has two implementations before asking whether the test is
weak". What this adds is the third possibility, and it is the
commonest of the three in a suite this size: the test is fine, nothing
is redundant, and the DOOR the entry stands at is one the test does
not open. The tell is that the entry's site and the test's acts have
no path between them -- which is a question about the product, not
about the assertions, and reading the test again will never answer it.

## THE HARNESS'S STYLE IS PART OF THE MEASUREMENT, EXACTLY AS ITS FONT IS

2026-08-30, and it is the font lesson below arriving through a
different property of the same widget stack. The maintainer reported
that every control on the Design tab ran the width of the window. Two
binding documents named the cause: a QFormLayout stretches its field
column. (T-1.)

## A GUARD CAN CHECK WHAT A COLUMN NEEDS AND NOT WHAT A WINDOW DOES

2026-08-29, and it is the sharpest thing about measuring a layout
here. Every runner and every CI job sets `QT_QPA_PLATFORM=offscreen`,
which supplies Sans Serif at 9pt; a desktop supplies the system font at
13pt. The obvious repair for a guard that measures the wrong font is to
SET the font -- and it half works, which is worse than not working at
all. (T-2.)

## AN ATTRIBUTE THAT IS A VIEW CANNOT BE WATCHED BY REBINDING IT

2026-08-28. A probe replaced `dialog._category_colours` with a dict
subclass that logs every write, to find out who records a follower's
inherited colours as somebody's hand-picks. It reported nothing at all:
no writes, and an empty record at the end -- while the probe that had
measured the defect an hour earlier read the same record holding all
four colours. (T-3.)

## THE HARNESS SETTING EVERY RUNNER SETS IS PART OF THE MEASUREMENT

2026-08-28. The suite was launched by hand, three shards, without
`QT_QPA_PLATFORM=offscreen` -- which `tests/run_tests_macos.sh` sets,
`release.py` sets, and the CI jobs set. Three layout tests failed at
once, all saying the assembled window is 1334px against a 1280 ceiling.
Nothing about the layout had changed in the package since a candidate
whose report shows all three passing. (T-4.)

## A CONTROL ARM'S OWN ACT CAN TRAVEL INTO THE ARM IT CONTROLS

2026-08-28, verifying a claim that a colour picked on a map opened
with Load never reaches the map. The probe had three arms -- a map drawn
in this session, the same map opened with Load, and one adopted by
reopening the plugin -- and every arm picked THE SAME COLOUR. The
control arm's pick was saved into the file the second arm opened. (T-5.)

## A CLAIM HAS A DIRECTION, AND CHECKING IT IS NOT OPTIONAL

2026-08-28. A hunt reported that a Save drops a no-data twin's table
while its element's survives. Driving the same panel act gave the
OPPOSITE: the element's table went and the twin stayed. Same mechanism,
same harm class, reversed. (T-120.)

This file already says a HARM named by reading is a hypothesis, and
CLAUDE.md says that of one fact written twice you ask which writer had
a reason. This is the same rule pointed at a report: **of one claim,
ask which way round it runs, and drive it before believing either
half.** It costs one probe and it is the difference between fixing a
defect and moving the half that was already correct.

## A MEASUREMENT THAT DOES NOT RESOLVE IS NOT A MEASUREMENT

Same day, and it nearly put a false number into the source. A hunt
measured a Save going from 22.4s to 16.2s at 128 elements, and from 134s
to 90s at 256, by dropping an OGR open the code discards anyway. The
change was made and both figures were written at the site as its
justification. (T-6.)

## A FIXTURE THAT CANNOT SHARE A SOURCE CANNOT SHOW A SOURCE COLLISION

Same day, three probes deep into one claim about the group chooser
emptying the region combo. Two probes came back clean on both arms, and
the FIXTURE was the reason: `make_region_layer` is a MEMORY layer, and
a memory URI is not something anything else can be built on -- so the
two layers never shared a source string and the collision the claim is
about could not arise. On the packaged Auckland GeoPackage it
reproduced immediately. (T-121.)

This is the fixture-that-cannot-exhibit-the-case trap in its plainest
clothes, and the question that finds it quickly is: **what does this
defect need two things to SHARE, and can my fixture make them share
it?** Where the answer is a path, a file or a provider, the synthetic
grid is the wrong fixture whatever else it has going for it.

## A red suite can mean the software got SLOWER, and reading it as a hang costs the diagnosis

2026-08-16. Every CI suite leg went red at once -- three Linux
versions and macOS -- with the same line: `STALL adversarial sequences
[no result after 600s]`, exit 2. The stacks were genuine and pointed at
real work, so the first reading was a hang in the newest code on that
path. (T-7.)

## Assert the sentence the product composes, not a phrase copied out of it

2026-08-16, and it cost an afternoon of wrong diagnosis. A test
asserted `"no value" in said` about the missing-values notice. The
maintainer reworded that notice the same morning -- "have no value"
became "do not have finite numeric data", correctly, because the count
had widened to infinities, which are values and simply not finite ones.
(T-8.)

## A guard is not a guard until you have watched it fail

2026-08-16 produced two guards that were DEAD the moment they were
written, both by the same author on the same day the rule was being
written down, and both caught only by disabling the fix and re-running.
The first asserted that a helper returned zero when called a second
time, on an object the product had already put through it -- an answer
that could not depend on what the product did. (T-9.)

## What a day of hunting one's own new code actually costs

2026-08-16, twenty-one hunts across six rounds, and the arithmetic is
worth writing down before anybody budgets another day like it. FOURTEEN
confirmed defects came out of the later rounds. ELEVEN were in code
written within the previous few hours; FIVE were inside repairs for
defects the same day's earlier hunts had found. (T-10.)

## Three ways to move a class boundary, and why none of them worked

2026-08-16, and the whole episode took an afternoon. It belongs in a
testing document rather than a design one because what it really
demonstrates is how a fix ships green. THE PROBLEM IS REAL. QGIS gives a
value to the FIRST range containing it, inclusive at both ends. (T-11.)

## Four ways a test passed while the product was broken, 2026-08-16

A second round of the same measurement, on twelve tests written that
day, mutated PER ASSERTION: 28 mutants, ten tests killed everything, two
did not. One in six, near this project's standing one in five. Both dead
axes were in tests whose PRIMARY axis was live, which is now the
reliable finding — a test is not one assertion, and the first one being
well aimed says nothing about the rest. (T-12.)

## TEST A CONTROL BY TYPING INTO IT, NOT BY `setValue`

2026-08-17, four defects in one day, every one of them a control
silently refusing what a person typed and every one invisible to the
test that guarded it. `setValue` CLAMPS IN SILENCE. It never consults
the validator, so it cannot see a range that refuses a keystroke, a
`decimals` too low to hold the number, or a `valueChanged` handler
rewriting the box while somebody is still typing. (T-13.)

## A test can pass while registered nowhere

2026-08-18, writing the last of thirteen owed guards.
`tools/run_some.py` finds a test by FUNCTION NAME, walking the module
rather than the registration list, so a test runs perfectly well without
ever being handed to `check()`. The guard for the reversed-ramp defect
ran green that way while the edit meant to register it had silently
missed its anchor. (T-14.)

## Where a guard's expectation should come from, when the product is the
## only thing that knows the answer

Thirteen guards were written in one sitting on 2026-08-18, and the
recurring difficulty was not what to assert but WHERE THE EXPECTED VALUE
MAY COME FROM. Three answers earned their place, in descending
preference.

**From the fixture and the settings**, which is the standing rule. A pin
of 6e-10 typed into a box must read back as 6e-10; a copied ladder's
interior breaks must still be in the record. Nothing is asked of the
code under test.

**From a PROPERTY of the domain that holds whatever the code believes.**
Used where every function that could answer is downstream of the defect:
a sequential ramp runs light to dark, so a forward ladder has its palest
class FIRST -- read off the rendered colours, true whatever the plugin
thinks, and usable as an oracle precisely because the plugin has no say
in it.

**From a second implementation the defect does not touch**, so that a
disagreement is a defect by construction. Where the fix and the
comparison share code, that arm must fall back to the fixture's own
colour instead.

AND WHERE NONE OF THE THREE IS AVAILABLE, SAY SO RATHER THAN INVENTING
ONE. An honest gap in a record is worth more than a guard that measures
nothing: a test asserting the guide's wording would pin the WORDS rather
than the truth, and would fail the next time somebody rewrote the
sentence correctly. (T-15.)

## Instrument WHICH rebuild writes the record, and the fourth attempt lands

The opacity defect of 2026-08-13 took four attempts across two
sessions, and the difference at the end was not cleverness. Three
attempts reasoned about where a stale value came from -- a flag read in
`_refresh_table`, a table cleared on project change, cell widgets
removed -- and each was reverted, one after running ten minutes without
reaching the case. WHEN A FIX HAS BEEN REVERTED ONCE, STOP FIXING AND
START MEASURING. (T-16.)

## THE SECOND TRIGGER: when a fix AND its test are in, hunt that ground again

Stated as a step for the same reason as the one below it: the practice
was demonstrated on 2026-08-17 and would otherwise have stayed an
anecdote. **WHEN.** A defect has been fixed, its regression test
written, and its catalogue entry proved. That is the moment the ground
it sits on is most worth re-hunting -- not the fix itself, which now has
a guard, but its NEIGHBOURHOOD. **WHY, measured.** On 2026-08-17 nine
defects were fixed in an afternoon. (T-17.)

## THE TRIGGER: point a hunt at a BATCH of new tests, per assertion

Everything below this heading was already known and written down. What
was missing was the moment at which somebody does it, so it read as a
good idea and got skipped exactly when it was most needed -- which is
what happened on 2026-08-17. This is that moment, stated as a step.
**WHEN.** A batch of tests written in one sitting, especially alongside
the fixes they guard. (T-18.)

## Tests written in haste, measured

2026-08-16. Fourteen tests were written in one day alongside the fixes
they guard, and a hunt afterwards mutated the behaviour each one names
to see whether it would notice. Eleven killed everything aimed at them.
THREE HAD DEAD SECONDARY AXES, which is about one in five and matches
this project's historical rate: - a tile-count check that compared a sum
WITH ITSELF -- twice. (T-19.)

## The differential sweep: reproducing and sharding

Three environment variables, all added 2026-08-10 while chasing a
divergence that took a day: WEAVINGSPACE_SWEEP_SEED=20260808 the run's
random seed WEAVINGSPACE_SWEEP_CASES=1700 how many designs it drew
WEAVINGSPACE_SWEEP_ONLY=589 examine only these cases
WEAVINGSPACE_SWEEP_SHARD=0/4 examine every fourth case
WEAVINGSPACE_SWEEP_DUMP=1 dump both sides' renderers Every case is DRAWN
whichever of these is set -- drawing is microseconds, tiling and
rendering are the minutes -- so a selected or sharded run produces
designs identical to the full one. (T-20.)

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

## What has actually found defects here, and what has not

Worth stating before the shapes, because it decides where effort
should go. Counted over this project's life, nearly every real defect
came from a DIFFERENTIAL instrument -- two independent descriptions of
the same thing, compared, so that a disagreement is a defect by
construction and no oracle is needed.

The record, and every one of them is code against code, machine
against machine, prose against behaviour, or our render against
somebody else's: the docstring audit found two product defects with no
machine time at all, the first Linux run found ramp names colliding by
case, and the colourspace comparison against upstream's own renderer
caught a categorical sampling error where a plausible derivation used
`round()` for `int()`.

Mutation testing is not on that list and should not be expected on it.
It asks "would the suite have noticed?", which is a question about the
TESTS -- worth running for exactly that, but a campaign of 128
survivors yielded one product defect and the sample did not find it.
Budget it as suite measurement, and spend the creative effort on new
differentials. (T-122.)

**Where to point the next one.** This software's characteristic
failure is a wrong map that looks like a right one, and the plugin
describes the same state in several places that must agree: the table,
the design preview, the generated map, the colour editor, and the
saved project. The defect found on 2026-08-13 was exactly a
disagreement between the table and the map, and it survived because
nothing compared those views systematically. Something does now:
`test_random_designs_keep_their_views_in_agreement` sweeps random
designs and compares five axes -- the row's field, its mode, its ramp
(allowing for a reversed clone, which matches no name in the library),
and the preview's colour against what the map's own ramp can make.
Two of those axes were dead when it was written, silently skipped
behind guards, which is the shape to check for FIRST in any sweep:
count what each axis actually compared and assert the count.
`tools/equivalence_scenarios.py` dumps the views a wider version would
need.

**A test can be WRITTEN AROUND a defect, and then it pins the defect
as correct behaviour.** Three were found this way in one evening and
none of them looked wrong -- one asserted `distinct >= k` before
measuring, so the case where a column has fewer values than classes was
excluded by the test that would otherwise have caught it. (T-123.)

The tell in all three is a workaround inside the test, written by
somebody who met the awkward behaviour, decided it was the fixture's
fault, and routed around it. So when a test contains an accommodation
-- a guard, a scheme swapped for another, a fixture narrowed to avoid
a case -- read the accommodation as a REPORT. It is somebody's note
that the software did something they did not expect. Ask whether they
were right that it was the fixture.

**A fix can be RIGHT and still be wrong to ship, and the blast radius
is the evidence.** A real defect was fixed correctly -- a graduated
renderer drawing more classes than the column has distinct values -- and
NINETEEN TESTS MOVED. That number was the finding, not the
inconvenience: one of the nineteen said why in as many words, and what
it knew was that the reduction made an element's class count depend on
which tiles it happened to receive, so two elements carrying the same
variable could draw different numbers of classes. (T-124.)

It was reverted the same night, with the measurement kept and the
question a real fix must settle first written down. The habit worth
copying: when a change moves an unexpected number of tests, read the
count as a statement about how deep an assumption runs, and read the
tests themselves before deciding they are all wrong. One of them
usually knows something.

**A differential cannot see a fault its EXPECTED SIDE shares.** The
pinned-element test renders the dialog's map beside one built by
calling the library directly, and its catalogue entry SURVIVED:
removing the pin from `seed_renderer` removed it from both sides at
once, so the two pictures agreed while the map was wrong. `visual_pair`
builds its expected side through the same `seed_renderer` the UI side
goes through, which is convenient and is exactly the independence the
shape is supposed to have.

The rule that follows is cheap and applies to every pair here: ask
which code the two sides SHARE, and assert separately anything that
lives in it. That test now checks the pinned bounds on the map before
it compares pictures, and the entry reports `caught`. Four tests use
`visual_pair`; the same question is worth asking of each, since the
value of the shape is that a disagreement is a defect by construction
-- and shared code is how the disagreement never arrives.

**A fixture can make a whole class of defect invisible, and the tell is
a test that passes for a reason nobody chose.** Putting that reduction
back exposed something older and worse, which had been shipping: class
breaks were cut from each ELEMENT layer, so four elements carrying one
variable drew four different legends and one colour meant four
different numbers. It survived every differential here because the
standard fixture asks for five classes over a column with four distinct
values, and more classes than values collapses quantile breaks onto the
values themselves -- so the elements agree whatever the code does. (T-125.)

Two habits follow. When a test's premise is a relation between two
runs, ask what makes the relation hold: if the answer is a property of
the FIXTURE rather than of the code, the test is passing for the wrong
reason and will go on passing through the defect it was written for.
And when a change makes a long-passing test fail, read the failure as
evidence about the world before assuming it is evidence about the
change -- here the change was right and the failure was a defect it had
uncovered.

**Verify a change to a CORE PATH with the whole suite, and accept that
the candidate is where that happens.** The reduction above was checked
against a subset and against a full suite that PREDATED it. The
candidate caught it twelve minutes in, on the third gate, exactly as
the cheapest-first ordering intends -- which is the argument for going
straight to `release.py --rc` rather than an argument against it. What
is NOT safe is believing a subset says anything about a path that most
of the suite runs through.

**A probe that returns is not a probe that measured.** Three attempts
were needed on one claim the same evening. The first errored on a
missing render context and was recorded, correctly, as proving
nothing. The second asked a renderer which symbol each feature would
get WITHOUT starting it, and got an answer that meant nothing while
looking exactly like data. Only the third -- startRender, ask,
stopRender -- measured the thing. An erroring probe announces itself;
a probe that quietly answers the wrong question does not, and it is
the more dangerous of the two.

**The cheapest differential has no instrument at all: a path against
its own sibling.** Three more defects came out of reading one code path
beside the twin that does the same job for the other styling mode, and
asking what one does that the other does not -- among them a class
colour picked during a run being destroyed at the landing, because the
landing path re-read the categorical picks and not the graduated ones. (T-126.)

None of these needed a machine. They need the question asked
deliberately, because the shapes are invisible while reading either
site alone -- each looks perfectly reasonable on its own, and only
the PAIR is wrong. Two things make this project unusually rich in
them: the categorical and graduated paths are near-twins written
months apart, and a dialog that shows the same state in five places
has ten pairs to disagree.

Two multipliers worth knowing. Where the pair is enforced by nothing
but attention, the catalogue must anchor each twin SEPARATELY -- a
single anchor covering both reports SURVIVED whatever the tests do,
since mutating one leaves the other doing the work. And when a rule
in CLAUDE.md names one of a pair, that phrasing is itself the
hazard: the re-read rule was written down, correctly, five days
before its twin was found missing, and it was written as a rule
about CATEGORY colours. A rule that names one sibling will be read
as a rule about one sibling.

**Hunting, as a distinct instrument.** Sixteen product defects came
out of one night of directed hunts on 2026-08-13, including one that
destroyed the user's own data and had been shipping since 0.23.0.
How to run one, how to watch it, which directions have paid and which
have not, and how the method compares with the suite, mutation
testing and the sweep: docs/process/HUNT-RECORD.md. The brief is
generated by tools/bug_hunt_brief.py.

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
every tooltip the dialog sets;
`test_every_declared_offset_is_pinned` states
the rule ("every offset is 0") rather than listing twenty-six names.
A new control or entry is covered the moment somebody adds a row, and
a whole class of mutant dies at once.

Evidence for the shape: across three batches, 37 of 50 survivors came
from just two operators, and almost every one was a default, a
constant, a catalogue value or a configuration call. The tables cover
what has not been sampled yet. (T-127.)

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

That has a consequence for the mutation score. A table kills numeric
mutants very cheaply -- `20 -> 21` dies because a line says 20, which is
one step from asserting that 20 equals 20 -- so **the score rises
further than the detection ability does.** When a round adds table
tests, classify which mutants newly died: those caught by behavioural
tests are detection, those caught by a pinned constant are regression
cover. (T-128.)

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

## Finding your way around 51,000 lines

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
imagined. The CURRENT counts are at the top of docs/TEST-MAP.md and
docs/BUG-REGISTER.md, which are regenerated at every release; a count
written into prose is true until somebody adds one. (T-129.)

Two things the map is deliberately NOT. It is not a coverage report —
`tools/coverage_report.py` says which lines ran. And it is not an
argument for splitting the file: coverage of intent is not the same
shape as file boundaries, and moving 500-odd functions risks silently
dropping one from the safety net that guards everything else. If the
file is ever split, verify it by comparing the registered-name list
and the pass/fail set before and after; they must match exactly.

## What a second machine finds, and why it could not be found here

The first Linux CI run (2026-08-11) failed seventy tests. Every one
was real, none was a plugin bug in the ordinary sense, and not one could
have been found on the development machine at any effort. They are worth
listing by KIND, because the kinds recur: **The environment supplies
something you never noticed depending on.** Sixty-nine of the seventy
were one missing geopandas: the `qgis/qgis` images ship QGIS and nothing
else. (T-21.)

## The artefact nobody opened

Every test here imported the plugin from the CHECKOUT. The release
built a zip and never opened it. So the first thing a user does --
unpack the archive into a QGIS profile and let QGIS call classFactory --
was the one thing neither machine tested, on either platform, at any
point in this project's life. (T-22.)

## A test's name is a hypothesis about its own failure

`test_a_comma_decimal_locale_does_not_corrupt_numbers` failed for two
CI rounds. It was not a locale fault; the child could not import
geopandas and fell over at the first assertion it reached, which
happened to be about tiles. The name and the message together told a
confident, wrong story, and it was believed twice. (T-23.)

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
Before accepting the obvious culprit, measure it -- and prefer evidence
that varies independently of the suspect, like the same code timed on
three machines. The suspected cache was kept, and labelled in its
commit as not the cause, because the next person will otherwise read
the fix as the diagnosis. (T-130.)

## Wait on the EVENT, not on a number of seconds

The third ceiling sized from this machine, 2026-08-16, and the fix
generalises past ceilings altogether.

`test_ui_affordances_are_deliberate` sampled the progress bar for a
flat ten seconds on runners where neighbouring tests take 250: Windows
failed at 18.7s and macOS passed at 9.0s, the same code and the same
assertion decided by nothing but the machine. Widening the constant
would have been the obvious repair and the wrong one, because no
constant is right for both. Waiting on the task ENDING instead is
faster on a quick machine, patient on a slow one, and STRICTER: a run
that finishes having never named a phase is a real failure rather than
an expired clock. (T-131.)

Ask of any timed wait: is there an EVENT that means "the answer is in
now"? A task clearing, a signal arriving, a file appearing. Where
there is, wait on that and keep the clock only to catch a hang. Where
there is not, size from the slowest measured figure and multiply --
and remember that a contention factor tuned for parallelism says
nothing about a slower machine.

The second half of that repair landed later the same day and is why
the paragraph above reads in the past tense: CONTENTION is now
`(2.5 if SHARD_COUNT > 1 else 1.0) * SLOWNESS`, where SLOWNESS comes
from `WEAVINGSPACE_TEST_SLOWNESS` and each CI job declares its own
figure with the reason beside it (Linux 3, macOS 2, Windows 4, all of
them round and conservative rather than measured).
`test_every_ceiling_widens_for_a_slow_machine` fails both when the
suite stops reading the declaration and when a job stops making one.
So a ceiling now widens for a slow machine as well as for a sharded
one -- which does not retire the rule above, since a declared factor
is still somebody's guess about a machine they cannot see.

## Ceilings, and the two ways to get them wrong

A watchdog exists to catch a HANG. It is not a performance budget, and
every time it is used as one it produces a red result that means nothing
-- which is how people learn to ignore red results. Both mistakes were
made on 2026-08-11, hours apart: - a forty-minute CI job limit, sized
against the twenty-four-minute macOS suite, forgetting that the Linux
legs are slower and that a provisioning step downloads a scientific
stack first. (T-24.)

## A child process inherits the suite's own environment

A test that spawns a child gives it this process's environment, and
this process is not the plain one you ran while writing the test. In a
release the suite is SHARDED, so `WEAVINGSPACE_TEST_SHARD=2/3` is set; a
child that reads that variable is told it is shard two of three and
behaves accordingly. (T-25.)

## One fix, two loops

The palette test was narrowed to ramps this plugin installed, and
failed on the next round at a different assertion in the same test --
the interior-stops check, a separate loop that had not been narrowed.
A half-applied fix reads as progress, because the failure MOVES. When
a fix is a filter or a guard, grep for every place the same
comparison is made before believing one edit finished it.

## Lessons, each paid for once

**WINDOWS CANNOT STAGE "THE FILE WENT AWAY WHILE THE LAYER WAS OPEN",
and four tests here need exactly that.** The OGR provider holds a
GeoPackage open, and Windows refuses to delete or rename a file another
handle has, so the state those tests are about does not exist there: the
deleted-file case in `test_qgis_changes_around_the_plugin`, the
`test_qgis_still_calls_a_dead_layer_valid` canary, the third act of
`test_a_project_whose_region_layer_has_moved`, and the folder move in
`test_a_project_and_its_geopackage_move_together` -- the last of which
IS reachable, because clearing the project first releases the handles,
given a retry while Windows gets round to closing them. (T-26.)

**A workaround for someone else's bug needs a canary.** When this plugin
works around a defect in QGIS, the workaround outlives every memory of
why it exists and becomes folklore nobody dares touch. (T-27.)

**A tool that filters what it shows you can hide what you needed to
see.** `text_review.py` skipped any string starting with `{`, to
avoid format keys — and thereby dropped every user-facing sentence
opening with an interpolated value, three of which were live. The
tool's own docstring said a false negative ships unread text, which
is what happened. When a heuristic decides what a human reviews,
check what it is throwing away, not just what it keeps.

**An invariant can demand that the software get it wrong.** The sequence
test asserted that every edit changes the map. Two of its steps then
failed, and both times the plugin was right and the test was not.
(T-28.)

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
was said could read the dialog's note line instead. (T-29.)

**A fixed wait after a run is a guess about two races.** The note line
is transient by design -- adding output layers makes the layer combo
re-emit, which queues work whose first act is to clear it -- so a test
that runs the loop for a fixed 200 ms and then reads it is betting on
which lands first. (T-30.)

**"Immediately" is one interleaving out of many.** Race tests here fired
their second action with no delay, which only ever exercises the state
before any debounce has fired. The dialog has two debounces -- the
preview one, which is a FLOOR that widens to whatever the last rebuild
cost, and the live one -- and a task whose completion does main-thread
work, so an action arriving after the preview fires meets a different
machine from one at 0 ms, and one arriving after the live interval meets
a third. (T-31.)

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
behaviour it names is broken. This is the most expensive lesson here: in
one session, six tests were written to close gaps that automatic mutants
had found, verified to pass, and then re-judged against those same
mutants — and most of them did not kill. (T-32.)

**Before believing a survivor is a gap, count the call sites.** Deleting
one of several redundant calls leaves the others to do the work, so no
test can discriminate and none should be contorted into trying. (T-33.)

**Test a switch where it BITES.** Measured, not assumed:
retain-complete-tileables changes nothing unless the whole-tileable
join is on and edges are ragged; the join changes no data at all in
icon mode. Both were "covered" by tests in configurations where
severing the control from the library changed nothing.

**Prefer one systematic test to many specific ones, where the property
is general.** Automatic mutants delete signal connections, and each
deletion leaves a control that looks normal, accepts input and does
nothing whatever. (T-34.)

**A control must act through its OWN signal.** Tests that change a
control and then call `_rebuild_unit()` themselves prove nothing: the
connection could be deleted and the test would still pass. A user has
no such option. Change the control and let only the dialog's own
debounce run.

**The environment can satisfy the thing under test.** QGIS stores colour
ramps in the user's profile, so on a machine that has run the plugin
before, its palettes are already installed and a test that merely
asserts they are present passes no matter what the installer does.
(T-35.)

**AND WHERE IT DOES, THE TEST'S ANSWER CAN DEPEND ON HOW THE SUITE WAS
SHARDED.** 2026-08-17: `test_qml_class_template` names the ramp "tab10"
and never installed it, where its sibling three lines up does. (T-36.)

**AN INVARIANT CHECKED IMMEDIATELY CANNOT TELL A DEFECT FROM A
DEBOUNCE.** The same day, a stochastic hunt's top claim -- a row saying
Graduated over a categorized renderer, on seven independent seeds -- did
not reproduce on any of seven deliberate routes once each was allowed to
settle. (T-37.)

**And it can satisfy the thing MEASURING the test, which is worse.**
2026-08-15 produced three faults in one evening that this machine is
constitutionally unable to show, all masked by the same seeded profile.
(T-38.)

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
for exactly this. (T-39.)

**No unconditional modal dialogs on generation paths.** A QMessageBox
blocks a headless run; one hung the suite for thirty-one minutes. The
harness patches QMessageBox and the plugin reports quietly instead.

**A test whose coverage depends on the machine it runs on reports the
machine, not the code.** The size guard's printed-spacing block read the
ambient `QLocale`, so the development Mac proved `en_US` and nothing
else. (T-40.)

**Prove that your reproduction reproduces.** The first attempt at that
one set `LC_ALL=C`, ran green, and looked like a fix confirmed. It was
not: macOS QGIS takes `QLocale` from system preferences and never
reads the environment, so the reproduction had exercised `en_US`
twice. A fix whose "proof" is a run that could not have failed is an
unproven fix with a receipt. Reproduce by forcing the thing itself —
`QLocale.setDefault` — and confirm the broken version fails before
believing the fixed one passes.

**When an attribution is a guess, report rather than gate.** The
documented-command check reads flags quoted without their script and
attributes them to the script the document last named. Unbounded, that
produced 31 findings of which nearly all were `git`'s and `gh`'s flags,
since those commands name no `.py` file and so never displace the owner.
(T-41.)

## Testing a PROMISE: synthetic shapes crossed with conditions

Some defects are not a bug in a function but a hole in a promise. "Edit
the symbology in QGIS and the plugin follows" is one: it is not one
behaviour but a family, and a family fails one member at a time.

**ONE BIG CHANGE IS NOT COVERAGE OF MANY SMALL ONES.** The guard that
existed for that promise pasted a renderer with a different field, a
different class count AND a different ramp at once, and passed — while
a tester retyping a single class boundary found nothing followed at
all. A route that only ever moves three things together can never show
which of the three is carrying the behaviour. When a promise covers a
family of actions, enumerate the ATOMIC actions; the compound one
passes for whichever reason happens to be intact.

**SYNTHETIC SHAPES ARE CHOSEN FOR FAILURE MODES, NOT FOR BEING
REALISTIC.** The nine columns crossed against those routes are each
there because something once broke on that shape: evenly spread,
heavily tied, cubic-skewed, bimodal with an empty band, a quarter
nulls, constant, two distinct values against five classes, spanning
negative to positive, and around 1e9. A smooth continuous column is
the case that always worked, so a suite made only of pretty numbers
tests the code's easy half. Generating the data also means the fixture
can be shaped to the question — and a synthetic column spread from 3.1
to 79.1 reproduced a tester's screenshot to the decimal, which no
sample of their real data was needed for.

**A FIXTURE THAT CANNOT MOVE CANNOT SHOW THAT SOMETHING MOVED IT.**
The first attempt at this used `make_region_layer`, whose `v1` holds
four distinct values; against five classes the classifier reduces and
any adopted ladder collapses back to the computed one. The fix could
be neither proved nor disproved for an afternoon. Before trusting a
green cell, ask whether that cell COULD have gone red.

**A FIXTURE'S CHOICE MUST DIFFER FROM THE DEFAULT THE MUTATION
FALLS BACK TO.** 2026-08-24: the entry proving that a re-defaulting
element PREFERS a field it has shown before was mutated to ignore the
preference -- and survived, because the fixture had staged its scheme
on the very field the cycling default picks for that row, so the
mutation landed on the same column by accident and restored the same
scheme. Preference and coincidence were indistinguishable by
construction. When a behaviour is "X wins over default Y", the
fixture must stage an X that is NOT Y, and assert that premise so a
refactor of the default cannot quietly restore the coincidence.

**ARRIVAL AND SURVIVAL ARE DIFFERENT PROMISES**, so "what happens
next" is an axis of its own: each edit is checked immediately AND
after a re-Generate. This project's older defects lived in the second
— a change that reached the map and the table and was gone by the next
run, or by a reopen.

**SPINE PLUS ROTATION, NOT THE FULL CROSSING.** Full factorial is how
you find surprises the first time; as a permanent suite member it
grows with every new route until somebody skips it, and a skipped
guard is worth nothing. So: every ROUTE runs against two canonical
shapes under both aftermaths EVERY time, since a route that stops
being exercised is the quietest way to lose coverage; the remaining
cells are SAMPLED under a seed the failure message prints, so anything
it catches is reproducible by re-running with that seed. The whole
crossing stays behind an environment flag for when something changes
structurally. Measured 2026-08-18: 36 cells in 58 seconds, against 140
cells in 3m30s for the full grid.

**REPORT EVERY CELL, NOT THE FIRST FAILURE.** "Some things do not
work" is not actionable; a named list of route, shape and aftermath is
a work list. Collect and assert once at the end.

**EXPECTATIONS MUST BE SHAPE-AWARE BEFORE ANYTHING IS SAMPLED.** A
pasted class count is a REQUEST, not a promise — a column cannot be
cut into more classes than it has distinct values, so a constant
column collapses a three-class paste to one BY DESIGN. Expecting three
there reported correct behaviour as a defect. That matters more under
sampling than under full crossing: a false alarm that appears in every
run is merely annoying, while one that appears in a RANDOM SUBSET of
runs is indistinguishable from flakiness, and flakiness is how a suite
stops being read.

**THE HARNESS WILL AUTHOR ITS OWN FAILURES, AND THEY MUST BE COUNTED.**
This one produced three before it produced a real finding: a segfault
of its own making (`deleteClass` on a one-class renderer crashes QGIS
rather than raising — a constant column draws exactly one class), a
rounding mismatch between how it staged a number and how it read one
back, and the shape-blind expectation above. NONE was the plugin.
Keep a tally: a matrix whose failures are mostly its own is a matrix
nobody will act on.

**PROVE IT FAILS BEFORE COUNTING IT GREEN.** Remove the fix and watch
the grid go red — 17 of 36 cells here, each naming route, shape,
aftermath and wanted-against-got — then restore and confirm green. A
green matrix that cannot go red is an expensive way to feel covered.

**ANY CELL THAT EVER FAILS JOINS THE SPINE PERMANENTLY.** A regression
seen once is tested forever; the rotation then only ever covers ground
with no known history.

## CONVERTING A SUITE WHEN ONE ACT SPLITS INTO TWO

2026-08-27, when saving stopped being a side effect of drawing. Six
hundred and forty tests had been written against a plugin where setting
an output path made every Generate write the file; the ruling made
writing a separate press. What follows is what the conversion cost, what
it found, and the four ways a mechanical sweep goes wrong, because the
shape recurs whenever an act is split. **THE FAITHFUL CONVERSION IS THE
ONE THAT CHANGES NO TEST'S MEANING.** A run wrote whenever a path was
set, so a Save press inserted at exactly the moment the old write
happened reproduces the state each test was written against. (T-42.)

## WHAT "THE FILE DID NOT CHANGE" MEANS, MEASURED

Also 2026-08-27, and it cost three drafts of one test. **BYTES ARE NOT
A PROPERTY OF AN UNTOUCHED GEOPACKAGE.** A Generate after a Save leaves
every table, every feature count, every embedded style and the record
IDENTICAL while the file grows from 184,320 bytes to 356,352 -- sqlite
reorganising it as the layers that were reading it are replaced and let
go. (T-43.)

## A MATRIX THAT PASSES FIRST TIME HAS NOT BEEN WATCHED FAIL

The save matrix came back green on its first run, over nine routes and
two shapes and three aftermaths. This file already says to break the
fix and watch the guard fail; what made it easy here is that the fix
WAS a mutation: the in-place skip, deleted, turns "save twice" into
OGR refusing to overwrite a layer with itself, and the matrix went red
at once. An entry over that line is now what proves the matrix can
fail -- so the catalogue and the matrix guard each other, which is
worth more than either alone.

AND TWO ROUTES ADDED AFTER IT WAS GREEN FOUND THE WORST DEFECT OF THE
DAY. Reading the writer end to end, rather than the tests, turned up
two journeys nobody had crossed: saving to a DIFFERENT file, and
saving a map that was LOADED rather than drawn. The second destroyed
the file it was saving. A matrix is a crossing of what somebody
thought of; the routes it lacks are found by reading the code it
tests, not by looking at the matrix.

## REACH FOR THE MATRIX FIRST when writing or improving a test

**This is the default shape for any test about a BEHAVIOUR FAMILY, not
a specialist technique.** Before writing a single-case test, ask
whether the thing under test is one behaviour or a family of them.
"Edit the symbology in QGIS and the plugin follows", "a project
reopens as it was saved", "a number you type is the number used" are
all families, and a family fails one member at a time. A single case
passes for whichever member happens to be intact and tells you nothing
about the rest.

The shape, and it is cheap: enumerate the ATOMIC actions as routes,
cross them with SYNTHETIC data shapes chosen for failure modes, and
add an axis for WHAT HAPPENS NEXT. Run a spine of every route against
two canonical shapes every time, sample the remainder under a printed
seed, and keep the full crossing behind a flag. Measured on the
symbology matrix: 36 cells in 58 seconds, against a suite whose
slowest single test is 118.

**When improving an EXISTING test, the same question applies with more
force**, because a test that already passes is the most likely place
for a hole to hide. The guard for the symbology promise pasted a
renderer with a different field, class count AND ramp at once and had
passed for weeks; a tester retyping one boundary found that nothing
followed. Widening that test into a matrix is what turned one green
tick into a 36-cell grid that fails 17 ways when the fix is removed.

Signs you should be writing a matrix rather than a case:
- the behaviour has a name a user would recognise as a promise;
- you find yourself writing "and also" in the test's docstring;
- the fixture has one shape and the production data has many;
- the thing can be done more than one way in the UI;
- arrival is easy to check and PERSISTENCE is the part you keep
  meaning to get to.

## A matrix may balloon, because you are SAMPLING anyway

2026-08-19, extending the symbology matrix from three axes to four at
the maintainer's asking: interaction with QGIS -- class boundaries and
copy-paste -- is where this plugin's defects come from, so cover it
high-dimensionally. **THE SPACE IS FREE; ONLY THE SPINE AND THE SAMPLE
COST.** Twelve routes, nine shapes, three aftermaths and three schemes
is a crossing of nearly a thousand cells, and it runs in about two
minutes, because the spine is bounded deliberately and everything else
is drawn under a printed seed. (T-44.)

## FIVE WAYS A PROBE OR A CELL FAILED TO REACH ITS OWN CASE IN ONE DAY

2026-08-26, judging nine hunt claims. Every one of these reads exactly
like a passing result, which is why they are listed together: the common
shape is not carelessness but that a harness has no way of telling "the
case did not arise" from "the case arose and was fine". **A FIXTURE THAT
STAGES SOMETHING THE PRODUCT WOULD NEVER KEEP.** A probe pinned a class
bound on a CATEGORICAL element. (T-45.)

## A HARM NAMED BY READING IS A HYPOTHESIS, EXACTLY LIKE A SITE

Also 2026-08-26. This file and CLAUDE.md both already say that a SITE
named by reading reads exactly like one somebody proved. Judging nine
hunt claims produced the other half: three of them described the code
CORRECTLY -- a guard really was missing from two of three doors, an
embedded region really does load under a source string the gate can
never match -- and not one of the three costs a user anything, because
in every case a second mechanism answers first.

The tell is that the claim stops at the line. A guard is missing:
therefore what? Walk it. If the answer is a map deleted, drive it and
watch the map go; this project confirmed exactly that for a different
claim the same day, four layers of one dataset's tiles removed by a
run on another. If you cannot reach a loss, the honest finding is
that the behaviour is HELD REDUNDANTLY, which is a different and more
useful sentence than "the claim was wrong" -- it names what would
have to move before the asymmetry starts costing something.

## A CLEANUP THAT WORKS BY SIDE EFFECT IS A CLEANUP NOBODY WROTE

2026-08-25, and it is the best lesson of a night that found seven
defects. `_forget_the_last_project` clears every field-keyed record when
a project is replaced, and its list had been missing the scheme shelf
since the shelf existed. A hunt LOOKED at that omission earlier the same
night and ruled it benign -- correctly, and it measured why: the bank
swap ran with None on a project replacement and emptied the view on its
way past. (T-46.)

## A RECORD IS NOT WHAT THE USER SEES, WHERE A PATH EDITS IN PLACE

2026-08-25, found by a hunt an hour after the matrix, the tests and
the entries had all agreed the code was right. `_adapt_to_the_layer`
-- the door taken when a column is deleted in QGIS -- may not rebuild
the table, because a rebuild mid-interaction is the race this project
has already paid for. So it edits widgets in place. The fix for "a
dropped column takes its whole scheme" shelved the RECORDS there and
stopped, and every record-level check passed: the ramp record was
popped, the count record was popped. The MAP still drew the old ramp,
because `_assignments` reads the WIDGETS.

**WHERE A PATH EDITS IN PLACE, THE WIDGETS ARE THE STATE.** Ask of
any fix that clears a record whether the thing the user sees reads
that record or the control. This project's own reading rule already
says to drive the product and read the pixels; the sharper version is
that a record and a widget are TWO STORES, and clearing one is
half a fix.

## A FIX THAT KEYS ON AN ABSENT RECORD MUST ENUMERATE EVERY ROUTE TO
## THAT ABSENCE

Also 2026-08-25, and it is the same night's most transferable line.
The per-dataset banks merge records written before any dataset
identity exists into the first bank, because a reopened project's
adoption writes stamps before the chooser settles. `old_id is None`
was written to mean exactly that. It also means "the plugin was
opened before the data was loaded" -- a route nobody listed -- and on
that route the branch filed one dataset's hand-picked colours, keyed
by its own value strings, into the NEXT dataset's bank, its map and
its saved project.

The fix was one line at the other site that binds the identity. The
lesson is the question that was not asked: when a branch fires on the
ABSENCE of a record, enumerate every way the record can be absent,
and write the list at the branch.

## THE SWITCH MATRIX, AND WHAT ITS FIRST RUN TAUGHT

2026-08-25, built when the maintainer asked whether the day's changes
were in the matrices, and they were not: the dataset-switch rulings had
journey tests, one axis each, which is exactly the arrangement the
matrix default exists to replace. Routes (plain, same-schema,
shared-name, column-deleted, return, pre-landing, mid-run) crossed with
staged state (derived, touched scheme, picks and pins, path set) crossed
with aftermath (immediate, generate, return); a spine of every route
against the two states with the most to lose, the plain route against
everything, and a seeded sample of the rest. (T-47.)

## A MATRIX ASKS ABOUT RECORDS; ADD THE QUESTION ABOUT WHAT IS SEEN

2026-08-19, and it is the sharpest thing the day taught. Three defects
landed in one evening and the symbology matrix -- twelve routes, nine
shapes, three aftermaths, three schemes, close to a thousand cells --
caught none of them: - a clear mark drawn into pixels its own QLineEdit
covers, so it had never been visible on any build; - a ceiling somebody
had set with no edge to draw a mark on, because the swatch enumerated
two of the record's four ends; - a bound of 1e9 elided out of a box
sized for 1.56. THE CROSSING WAS NEVER THE PROBLEM. The routes were all
there and all exercised: "paste a foreign style", "set a ceiling", "copy
to another element". (T-48.)

## THREE WAYS A GUARD FOR A VISUAL THING PASSES ON A BROKEN PRODUCT

2026-08-19, all three in one sitting, all three caught by the mutation
catalogue rather than by reading. They are worth knowing on sight,
because a guard about PIXELS fails in ways a guard about records does
not. **IT REPAIRS THE DEFECT ON ITS WAY PAST.** The first attempt at
asserting the clear mark was drawn hid the mark and showed it again to
get a before-and-after contrast -- and `show()` and `raise_()` are
exactly what the mutation removed. (T-49.)

## AN INSTRUMENT IN THE USER'S HANDS BEATS SIX REPRODUCTIONS IN YOURS

The same evening, and it is the most useful hour of the day. A
maintainer reported a class recoloured in QGIS reaching the map and
neither the swatch nor the colour editor. SIX reproductions were built
here -- live update on and off, the edit landing mid-run and at rest,
against their OWN dataset -- and every one of them worked. (T-50.)

## Bisect by DISABLING, not by reasoning

When a change breaks a test and the cause is not obvious after ONE
hypothesis, stop reasoning and bracket it. Insert an early `return` at
successive points through the new code and run the failing test at
each: the first point that turns PASS into FAIL contains the culprit.
On 2026-08-18 this bracketed a defect to a single statement -- the
store -- after four separate theories had each been plausible, each
been implemented, and each been wrong.

The same method works one level up: to decide WHICH FILE is at fault,
swap the whole file for its last-good version and re-run. That settled
`dialog.py` versus `tests/run_tests.py` in a single run.

**Then log what the culprit does, not what you think it does.** The
store here wrote breaks `[1.0, 1.4, 2.6, 3.0]` -- the plugin's own
ladder, recorded as though a user had typed it. No amount of reading
would have produced that string.

## Instrumentation that lies, and how it lied here

**`print()` INSIDE A QT SIGNAL HANDLER GOES NOWHERE** under a test
that captures output. A dump placed in the suspect method stayed empty
through every failing run, which read as proof the method never ran; a
later call-site bisect proved it ran every time. AN EMPTY LOG IS NOT
EVIDENCE OF ABSENCE. Write to a FILE, and prove the file gets written in
a case you know reaches the code. **A PLAIN `python3` HEREDOC RUN AFTER
SOURCING THE QGIS ENVIRONMENT DIES AT BOOTSTRAP AND APPLIES NO EDIT.**
`PYTHONHOME` points the system interpreter at QGIS's framework and it
fails with `ModuleNotFoundError: No module named 'encodings'`. (T-51.)

## Two rules the fix itself produced

**A GETTER-SHAPED NAME IS NOT A GETTER.**
`_current_graduated_classes` reads like an accessor and BUILDS a
renderer through `bridge.make_graduated_renderer`. Check what a method
does before calling it from a signal handler.

**WORK ADDED TO A SIGNAL HANDLER MUST NOT PRECEDE THE WORK ALREADY
THERE.** An exception inside a Qt slot is swallowed, so anything
inserted ahead of existing logic can cancel it silently and leave no
trace. Add at the end, and contain your own failure.

**AND ONLY RECORD WHAT A PERSON LEFT BEHIND.** A watcher that adopts
state from a layer must run only at REST: not while the dialog is
writing renderers, not while a run is in flight, and not while a
landing is still being reconciled. During any of those the record and
the layer are transiently out of step, and what sits on the layer is
nobody's decision.

## Two jobs that MUTATE one file must never run at once

2026-08-19, and it is the tree-lock rule reaching further than it was
written. This project already knows that background work locks the tree,
and that rule was written about a READER meeting a writer: a suite or a
sweep reading source while somebody edits it, which spoiled two
measurements in one night. (T-52.)

## A catalogue entry's test name must be ONE string literal

`tools/mutation_check.py` entries are read by `check_standards` with
`ast`, which takes the first literal of an implicit concatenation. A
name split for line length therefore concatenates correctly at RUN
time -- so the entry proves `caught` and looks healthy -- while the
standards check reports a test that does not exist. Found 2026-08-19,
and the confusing part is that both halves are telling the truth about
different things. Keep the name on one line, and shorten the test's
name if the line will not fit.

## A FIXTURE BUILT TO EXPLOIT A BUG DIES WHEN THE BUG IS FIXED

2026-08-19, and it is the cheerful version of a red suite. The size
guard's boundary test stands on nine islands filling 5% of their own
bounding box, and its own comment says why: the over-estimate that shape
provoked was "exactly what makes the boundary affordable". (T-53.)

## When ONE notice becomes TWO, every test that filters on its wording
## needs to know which

Also 2026-08-19. Icon mode was given its own coverage sentence, on the
ruling that "appear nowhere on the map" is FALSE of an area that has an
icon drawn from its neighbour. An older test looked for the tiling
wording in BOTH modes, found no notice in icon mode, read the count as
zero, and reported six areas unaccounted for -- a failure that
described nothing.

This suite already knows to compose an expected sentence from the
function the product uses rather than transcribing it. What today adds
is that the function may now be a CHOICE of functions: the filter has
to pick the same one the product picked, from the same condition. Where
a message splits by mode, by platform or by data shape, a test that
knows only one of them is a test that has quietly stopped covering the
other.

## The whole suite is where a core-path change gets verified, and the
## numbers from today say why

Two changes landed on paths nearly everything runs through -- the value
cache every element's digest routes through, and the size estimate that
gates every Generate and every live update. Each was proved by its own
new guard, its catalogue entries and a handful of neighbouring tests:
perhaps a dozen tests apiece, all green.

The full suite then found two reds, neither of them reachable from any
test aimed at either change, and neither a defect in the plugin: both
were FIXTURES the changes had moved out from under. They had been red
for several commits and nobody knew, because the suite had not been run
since that morning.

The rule this project already has -- verify a change to a core path
with the whole suite, and accept that the candidate is where that
happens -- is unchanged. What today supplies is the ratio: a dozen
targeted tests apiece, zero of the actual breakage found.

## MEASURE EVERY CANDIDATE FORMULA, ON MORE THAN ONE SHAPE

The size guard needed a new way to estimate covered ground, and the
first one written was measured 2% UNDER within the hour by the guard
written beside it. Four models were then compared against what the
library really draws, on two shapes chosen because a region is not one
thing -- adjacent cells cut from a raster share edges needing no
allowance, separated cells each carry their own:

    model                     adjacent cells   separated cells
    bounding-box edge              1.20x           0.98x  UNDER
    each polygon's perimeter       6.25x           2.38x
    dissolved boundary             1.28x           1.68x

Only the third is generous on both. Any ONE of those rows, taken alone,
would have justified a different answer -- and the first row is exactly
what a single dense fixture would have shown. When an estimate stands
on the shape of its input, the sweep crosses shapes or it proves
nothing, which is the same argument this file already makes about
magnitude.

## When an instrument disagrees with a hand-run, believe the hand-run

2026-08-19. A guard proved VACUOUS by hand -- it drove a path the
product now refuses, so its comparison could not move whatever the
mutation did -- came back `caught` from the mutation catalogue, twice,
on a quiet machine. THREE EXPLANATIONS WERE TRIED AND TWO WERE
COMFORTABLE. Contention, ruled out by running it with nothing else on
the machine. THE HABIT, and it is cheap: when a tool and a hand-run
disagree, RUN THE TOOL'S INNER COMMAND YOURSELF with nothing suppressed.
(T-54.)

## A TEST WHOSE SETUP REFRESHES THE THING UNDER TEST PASSES FOREVER

2026-08-20, and it is the data-provider face of a shape this file
already records twice. `test_a_project_whose_region_layer_has_moved`
covers a GeoPackage that goes while the layer is open, and it calls
`second.reload()` before it asks a single question. That call is the ONE
act that makes QGIS tell the truth about a moved file -- measured on
4.0.3, an open layer whose file has moved answers `isValid()` True,
`dataProvider().isValid()` True and `featureCount()` with its last good
number, and only after a reload does the provider admit False. (T-55.)

## A REPRODUCTION THAT CANNOT REACH THE CASE REPORTS GOOD NEWS

2026-08-20, and it is the third face of a shape this file already
carries twice. A hunt claimed that a second signal adopts colours a
first correctly declined. The probe written to check it drove the edit,
waited, fired a bare repaint, and read the record: clean. AND THE
CHEAPEST CURE IS THE ONE THIS FILE ALREADY PRESCRIBES: assert the
premise. (T-56.)

## TWO DEAD AXES OUT OF TWENTY-SIX, AND BOTH WERE SUBSUMED

The per-assertion hunt of 2026-08-20, at four tests written the day
before, each already carrying a proved catalogue entry. Nineteen
mutations; two assertions could not fail. Neither was a product fault
and neither is the usual shape: - an assertion naming a REAL contract
that this test cannot reach -- `assert dlg._task is None` guards against
launching a run over a dead layer, and survives deleting the guard,
because the conversion refuses that fixture unaided. (T-57.)

## FOUR WRONG HYPOTHESES ABOUT MY OWN TEST BEFORE THE PRODUCT WAS IN
## QUESTION

2026-08-20, writing a guard for a moved region layer. This file
already says to bisect by disabling rather than reasoning after ONE
hypothesis fails. Four failed, each plausible, each costing a run: - a
missing `bridge` import -- a real fault in the test, and the only one of
the four that announced itself honestly; - a 600 ms wait, blamed on the
style debounce. (T-58.)

## A JUDGEMENT BEHIND AN `if` IS A GREEN THAT SAYS NOTHING

2026-08-20, twice within the hour, in two tests written by the same
hand minutes apart. Both wrote the interesting assertion inside a
conditional -- "if the element kept the column AND is still categorical,
then require the question" -- and both PASSED without the branch ever
executing, because the fixture's columns held a handful of values and
the condition was false. **A CONDITIONAL ASSERTION IS AN ASSERTION THAT
MAY NOT EXIST.** It reads like coverage, it costs a line, and its green
is indistinguishable from a green where the case never arose. (T-59.)

## A TEST WITH NO CATALOGUE ENTRY IS A TEST YOU BELIEVE

Also 2026-08-20. Two registered tests landed that day guarding
behaviour believed to be ALREADY CORRECT -- the dataset-switch rules,
recorded as found sound rather than broken -- so there was no fix to
break and no entry was written. Nobody had watched either fail. That is
a different thing from a test that has been proved, and the suite cannot
tell them apart: both are green lines in the same list. (T-60.)

## A FIXTURE THAT LETS THE PLUGIN DERIVE THE THING UNDER TEST

2026-08-20, and it is the fixture-that-cannot-move trap wearing new
clothes. Two tests guarded the rule that a change of region dataset
KEEPS an element's setup where the new data has a column of that name
and DROPS it where it does not. Both passed. Both were vacuous, and the
defect they were written for was live the whole time: a categorical
scheme a user had picked rode onto a column of areas in square metres
and drew a colour for each. (T-61.)

## A GUARD MAY BE WRITTEN TWICE, AND THEN NEITHER HALF CAN BE KILLED

Also 2026-08-20, found by the catalogue within the hour. Two entries
written that night SURVIVED, and neither was reporting a weak test. The
rule that a dropped setup takes its style with it was written at BOTH
places `_refresh_table` touches it: the branch restoring a remembered
style, and the flag recording that style as somebody's choice. (T-62.)

## AN ENTRY PER AXIS, NOT PER TEST -- AND READ WHICH ASSERTION FIRED

2026-08-20, the per-assertion round at three tests written that day.
This file already says the catalogue proves a test's PRIMARY axis and
structurally cannot see the rest. What this round adds is the remedy,
which costs one entry each and is worth the minute. **THE MASKING IS
ORDINARY, NOT EXCEPTIONAL.** The catch-all test carries three axes: the
wrong SENTENCE, the lost RECORD, and the colour's SURVIVAL across a
re-tile. (T-63.)

## A GUARD'S OWN FIRST DRAFT IS WHERE THE NEXT DEFECT IS

Also 2026-08-20. A fix for a real defect shipped with four passing
tests around it, and the fix itself was wrong: a lookup by class BOUNDS
returned on the first match, and a ladder may hold several classes with
identical bounds -- a constant column, a tied column, `{1, 5, 9}` at
k=5. QGIS's `addClass` then inserts another degenerate `(0.0, 0.0)`
class, which collides with any fixture whose first real class is also
degenerate, so the plugin's own colour was compared against a
placeholder grey and adopted as somebody's hand-pick. (T-64.)

## A RETIRED CONTRACT CAN GO ON PASSING BECAUSE THE ABSURD CASE FAILS FAST

2026-08-26, and it cost the first candidate of this branch. The size
ceiling stopped being a refusal on 2026-08-25 -- the maintainer ruled
that a size is a question rather than a verdict -- and the work list
item that went with it, "update the tests that assert a refusal and say
why the expectation moved", was ticked. (T-65.)

## AN ORACLE CAN BE GREEN BECAUSE OF THE DEFECT IT WILL LATER CATCH

Same evening, the switch matrix's `mid-run/touched-scheme/generate`
cell. It snapshots dataset A's element layers, launches a second run ON
A, switches the chooser to B mid-tiling, waits for that run to land,
generates on B, and requires the snapshot to survive. Driven stage by
stage: the in-flight run REPLACES A's map in place -- four new layers,
same group, same region stamp -- which is the settled contract, and the
Generate on B then builds its own group and leaves all four of A's
alone. (T-66.)

## PRESENCE IS NOT ORDER, AND A LATE CALL IS WORSE THAN A MISSING ONE

2026-08-26, and four hunts of eight found it independently, which is
the most this method has ever converged here. A branch was missing a
call its twin makes. The repair added it -- and put it after the
restore, where the twin puts it before and SAYS WHY AT ITS OWN CALL
SITE: a variable cannot be restored to a column the region layer in
force does not have. (T-67.)

## SILENCE IN A RECORD HAS MORE THAN ONE CAUSE; ASK WHICH READER MADE IT

Also 2026-08-26, and it is the other half of the same evening. A
repair taught a restore to CLEAR a record when the incoming one is
silent about it -- right, and the cure for a real defect three hunts had
reported. But `_assignments` reports the pins, the hand-picked class
colours and the ramp window as empty for any row NOT WEARING GRADUATED,
and the categorical colours as empty for any row not wearing
Categorized. (T-68.)

## A FIXTURE ON ITS DEFAULTS LANDS ON THE RIGHT ANSWER BY ACCIDENT

Three fixtures in a row failed to make a reordering visible on
2026-08-26, and one reason recurred: the design under test was the one
the plugin would have chosen anyway. Re-deriving an element's variable
against a different dataset is only VISIBLE where the derived answer
differs from the recorded one, and a fixture left on its defaults
cannot tell the two apart. A hunt recorded exactly the same thing
about its own first attempt the same evening.

This is the fixture-that-cannot-move trap wearing the plainest clothes
it has: ASK WHAT YOUR FIXTURE LEAVES TO A DEFAULT, and stage something
the default cycle does not produce. Then assert that you did -- the
premise is one line and it is what stops the fixture drifting back.

## THE ORDINARY ACT IS A BETTER ROUTE TO A DEFECT THAN THE INGENIOUS ONE

2026-08-26 (night), and it is the clearest thing the consistency sweep
taught. Sixteen hunts had just finished on this tree, aimed with care at
the code written that day, and they found eleven defects in it. An hour
later a sweep that does nothing clever -- it closes the plugin window
and opens it again -- found that every hand-chosen variable, style, ramp
and class count was lost, and had been since 2026-08-25. THE ACT IS IN
THE CODE'S OWN DOCSTRING. `_adopt_existing_group` says it exists for "a
dialog opened later in a QGIS session (the plugin closed and reopened,
which users do constantly)". (T-69.)

## A FIXTURE THAT MULTIPLIES ZERO BY TEN

Same evening, and it is the plainest premise failure this file has.
A probe asked whether the map follows when the DATA changes: it
multiplied twelve values by ten, pressed Generate, and reported that
the ladder had not moved. The twelve were the first twelve features,
whose values are zero, so the column's maximum never changed and the
map was right to stand still.

The repair is one line -- read the column's maximum before and after
and require it to have MOVED -- and it turned a reported defect into a
clean result: the map follows the data exactly. THE RULE THIS PROJECT
ALREADY HAS is that when a test mutates a fixture, it must assert the
mutation changed something. What this adds is that the assertion has
to be on the QUANTITY THE CODE READS. Twelve rows changed is a fact
about the fixture; the maximum moving is a fact about what the
classifier will see, and only the second one makes the case arise.

## WHEN A DEFECT MAKES A LATER READING AMBIGUOUS, FIX THE READING FIRST

Also that evening. A session was found to leave TWO output groups, one
of them a stale memory copy. A separate probe then reported that the
group's record held a class count of five where the row and the map
said six -- and it was reading whichever group came last out of the
layer tree, which was the stale one. Asked of the group the dialog
says it is working in, all three agreed.

So when one defect multiplies the things a reading could be ABOUT,
every later measurement on that ground needs to name its subject
before it means anything. This project already says a watcher must
name what it watches; a probe reading a record is the same rule
wearing different clothes.

## NOTHING IN A HUNT'S REPRODUCTION IS INCIDENTAL UNTIL PROVEN SO

2026-08-26 (night). One catalogue entry took FOUR fixtures before it
could catch, and every failure was a different mechanism quietly keeping
the behaviour the mutation was supposed to break: ramp defaults
re-seeded are ramp defaults again, so the worn colours must DIFFER from
what a re-seed would draw; the reconciliation drain had adopted the
QML's colours as hand-picks, which are re-read at every landing and keep
the map whatever the arm under test does, so the race's LOSING side had
to be staged by emptying the record; and the unchanged-assignment carry
kept the old renderer until a SECOND control moved the style signature
-- the hunt's own journey had an opacity change in it, and the fixture
had dropped it as incidental. (T-70.)

## AN ORACLE THAT READS A DEPENDENCY'S STORED POINTERS READS FREED MEMORY

2026-08-26, and it is the freed-temporary trap wearing its most
convincing disguise yet. A test asked whether the plugin keeps its own
output out of the region chooser, and read
`layer_combo.exceptedLayerList()` -- the list the combo was HANDED.
Under the mutation those entries are the stale pre-resume layers, whose
C++ objects are gone, so reading their ids was undefined: it answered
plausible stale ids on one run and SEGFAULTED on the next. (T-71.)

## A FIXTURE'S TOKEN CAN VANISH WITH THE THING IT NAMES

Same day. A test for the landing's unreadable-class-source arm staged
the source as a `layer:` token and then removed that layer to make it
unreadable -- and the combo, rebuilt, no longer offered the token at
all, so the ROW forgot the choice and the arm under test never fired.
The test passed while measuring nothing.

A `file:` token is the fixture that can move: delete the file and the
row still names it, which is the state the arm exists for. The tell
is general -- **when a fixture makes something unreachable, ask
whether the CHOICE survives the unreachability, or whether your setup
has quietly removed the subject as well.**

## A REDUNDANCY YOUR OWN FIX CREATED WILL SWALLOW AN ENTRY

Also 2026-08-26, and it is the sharpest of the round's entry-proof
lessons. An entry over the resume's group stamp SURVIVED, and the
test was not weak: the same round had taught the switch door to stamp
the group on the way out of a dataset, so the fixture's strip -- made
BEFORE the switch -- was quietly re-written before the resume ran,
and the resume's own stamp could be deleted with nothing noticing.

Moving the strip to AFTER the switch left the branch under test as
the only writer between the strip and the assertion, and the entry
caught at once. So: **when an entry stops catching, ask what YOU
added this round that now writes the same fact.** A survivor is a
question about the whole set of writers, not only about the test.

## INSTRUMENTATION MUST NOT BE ABLE TO REPLACE THE VERDICT

The same day's diagnosis block for a Windows-only failure read every
layer's validity and source -- objects whose C++ halves may be gone,
since that is the state under test. A raise there would have handed
back a traceback about the instrument instead of the assertion, which
is this project's own probe-side trap arriving inside a test that
only ever fails on a machine nobody here can drive.

Each reading is taken on its own now, and its own failure is recorded
as a finding ("unreadable (...)") rather than thrown. **A `[found]`
block is evidence, and evidence that can crash is evidence you will
not have on the run that mattered.**

AND IT MUST READ EVERY STORE A REFUSAL CAN LAND IN. That failure
looked like a run that did nothing, because the message bar was
empty -- and one of the eight exits from `_generate` refuses through
a QMessageBox, which the suite's shim records in MODALS. Reading one
store and concluding silence is harness fault eleven of this
project's own ledger, met again.

## A ROUND CAN PASS EVERY TEST IT WROTE AND BREAK FOUR IT DID NOT RUN

2026-08-26, and it is the plainest measurement this file has of what a
targeted run is worth. Round nine fixed fifteen defects, wrote a test
for each, proved twenty catalogue entries, and was verified by running
those tests and their neighbours. It shipped FOUR REGRESSIONS. The
mutation workflow's coverage leg -- which runs the whole suite, for its
own reasons -- named them: green at the commit before, red at the
round's own commit, four tests, every one reproducible here on the first
attempt. (T-72.)

## A TEST THAT PINS A NAME PINS IT TWICE: AS TEXT AND AS A SYMBOL

2026-08-26, and it cost a release gate. Output groups were given names
carrying their dataset, and the suite was swept for the old name by
grepping the literal. Six sites turned up and were mended. The
candidate's own suite then failed on two tests that pin the same name
through `GROUP_BASE_NAME`, which no search for the string could ever
have found. (T-73.)

## BOTH BRANCHES OF THAT QUESTION CAME UP THE SAME NIGHT

The rule for a survivor is to break every route at once: if the test
fails, the axis is live and redundantly held; if it passes, the
assertion is the problem after all. Two entries were judged that way on
2026-08-26 and they came out on opposite sides, which is worth recording
because the reflex is to expect one answer. (T-74.)

## AN ENTRY CAN STOP CATCHING BECAUSE A RULING GAVE THE FACT A SECOND
## WRITER

Same day. The entry over the categorical attribution walk was proved
`caught` when it was written, and survived a day later -- not because
the test had weakened, but because the maintainer's ruling had added a
deliberate second writer of the same fact, so breaking the walk alone
changed nothing observable.

The procedure this file already prescribes is what settled it: break
every route AT ONCE. Both broken, the test fails, at the catch-all
colour -- so the axis is live and REDUNDANTLY HELD. The entry was
retired and the redundancy written at the test, which is the honest
record, and better than an entry that can only ever be red.

## WHEN A REPAIR GIVES ONE STORE A NEW WRITE, ENUMERATE EVERY STORE

The last two findings of 2026-08-26 were the same shape as each other,
and it is the shape this project meets most often. A restyle was taught
to write the GROUP's record, with a comment arguing exactly why. The
FILE's record was given its write hours later, by a different commit, on
the landing path alone -- so it inherited the very gap the first write
had closed. (T-75.)

## TWO RECORDS JOINED END TO END HAVE THE SHAPE OF ONE

(2026-08-27, row 31 of that day's ledger.) The changelog is one text
shown by two renderers, and the test written for exactly that danger
reads the current version's entry and requires an opening paragraph
followed by bold bullets. Every assertion in it passed on a body that
was nine tenths another release: the 0.24.4 entry had swallowed the
whole of 0.24.3, because opening the new section indented the previous
version's header with its `changelog=` prefix still on it and the
boundary is a lookahead for a line beginning with digits. (T-76.)

## AN ENTRY GOES BLIND WHEN A CONVERSION EDITS ITS TEST'S FIXTURE

2026-08-27, and it is the sharpest single finding of the branch's full
catalogue sweep, because it is the only one of forty-three survivors
that this branch caused. `an-embedded-source-is-an-opt-in` mutates the
plugin into embedding the region data ALWAYS, and its test is what
proves that unticking "Include the source data" keeps a private copy of
somebody's data out of a file they send on. (T-77.)

## FOUR WAYS A TEST DID NOT REACH THE JOURNEY ITS ENTRY NAMED

2026-08-28, deciding all thirty-four survivors of the branch's full
catalogue sweep. Eleven of them were this: the test is sound, its
assertions are sharp, and the journey it drives never touches the code
the entry stands on. Each is worth knowing on sight, because each reads
as a weak test and none is. **A GENERATE THAT CHANGES NO GEOMETRY IS A
RESTYLE.** Picking a style back, choosing a ramp, moving a class count:
none of them re-tiles, so `_generate` takes the fast path and the
LANDING never runs. (T-78.)

## ASSERT WHAT A RE-SEED WOULD NOT REPRODUCE

Same round, and it cost two withdrawn assertions. A followed row has
already been brought up to its layer's field and class count, so
re-seeding the element reproduces BOTH -- and a test asserting them
passes whether the renderer was preserved or repainted. What a re-seed
destroys is the COLOURS, and those are the discriminator.

The general form is this file's own rule about the easiest observable
nearby, arriving where the record and the map agree: before asserting
a property, ask what the failure you fear would do to it. If the
answer is "nothing", it is not the property to assert.

## STAGE THE CONDITION, THEN ASSERT THE PREMISE OUT LOUD

`if gaps_first:` guarded the assertion that would have caught a
mutated dedup key, and the fixture left the first element with no
empty classes, so it never ran. Taking the judgement out from behind
the `if` turned the test red -- correctly -- and the repair was to
STAGE the condition: both elements are given a class count high
enough to leave gaps, and the premise says so in words. Two counts
were tried before one worked, which is cheaper than an assertion that
cannot fire.

This project already carries "a judgement behind an `if` is a green
that says nothing". What this adds is the order of operations: assert
the premise FIRST, watch it fail, then stage until it holds.

## AN ANCHOR CAN BE AMBIGUOUS BY INDENTATION ALONE

Same sweep, nine entries returning no verdict at all: `mutation_check`
refuses an entry whose `old` text matches more than one place, on the
sound ground that mutating the first would leave the others doing the
work. Seven were genuine duplicates, the ordinary consequence of this
branch copying lines that entries stood on. (T-79.)

## ASSERT THE STRUCTURE, NOT A WIDTH

Also 2026-08-27, writing the guard for a release body that must not be
hard-wrapped. The first draft looked for prose lines shorter than
sixty characters, on the reasoning that a wrapped paragraph's last
line stops short. It is wrong in both directions: it fires on a
legitimately short paragraph, and it misses a wrapped paragraph whose
final line happens to run long.

The property is structural and exact. In Markdown a paragraph ends at
a blank line, so TWO CONSECUTIVE PROSE LINES ARE a wrapped paragraph,
whatever they measure. The rewritten guard walks the body tracking
whether the previous line was prose, and names every offending pair.

The general form: when a check reaches for a threshold, ask whether
the thing being checked has an exact definition somewhere. A
heuristic over a measurable quantity is usually a definition nobody
looked up, and its false positives teach people to ignore it.

## SILENCE WITH EXIT 0 IS NOT A PASS

The same evening, three attempts at one red-and-green proof, every
failure in the instrument. `tests/run_tests.py` ends through `os._exit`,
so when stdout is a PIPE rather than a terminal it is block-buffered and
the buffered `PASS <name>` is discarded — `tools/run_some.py` exits 0
having printed nothing at all, while a FAILURE's traceback reaches
unbuffered stderr and survives. (T-80.)

## GUARD THE SHAPE, AND READ THE FILE WHOLE

2026-08-28. A sharded coverage recorder lost a whole shard at startup
to `if os.path.exists(x): os.remove(x)` -- three processes, all seeing
the file, two removing it, the third dying with FileNotFoundError before
running a single test. The one-site repair was obvious. The GUARD was
the interesting decision, and it found a second instance within a
minute. **A RACE HAS A SHAPE, AND THE SHAPE IS WHAT RECURS.** A
regression test pinned to the reported line would pass forever while the
next person writes the same two lines somewhere else -- and they will,
because asking whether a file exists before removing it reads as
carefulness. (T-81.)

## THE DEFAULT A TEST FAMILY UNTICKS IS THE DEFAULT NOBODY TESTS

2026-08-28, round ten, and it is the cheapest question in this
document. Twelve tests here resume a saved map and every one of them
unticks live update, which is ON by default. So the whole family was
driven at a setting no user is holding -- and with the default, a
Load re-tiled the opened map into memory a second later and left the
saved file's own layers out of the project, which reopened empty.

The hunt that found it swept a delay across all four of this dialog's
windows first -- the preview debounce, the live debounce, the repaint
drain and the echo guard -- and ruled every one of them out. The
hiding place was not a race. It was a control the suite holds at a
value a person does not.

**SO ASK OF ANY TEST FAMILY WHAT IT HOLDS CONSTANT**, and for each,
whether a user holds it there. Where the answer is no, one test in the
family drives the default deliberately and ASSERTS that it is the
default, so the day somebody changes it the test says so rather than
quietly changing what it covers.

## ASSERT THE PREMISE OFF THE THING, NOT OFF WHAT YOU ASKED FOR

Same round, and it cost one run of a check written to prove a fix.
A guard swept magnitudes through a spin box and compared what came
back against the number it had passed to `setValue`. `decimals` clamps,
so at 0.000123456 the box never held the number at all and the check
reported the widget losing something my own fixture had lost.

Reading the premise off the WIDGET -- what does it hold now that I
have set it -- turned four false losses into none and left the real
one standing. This is the same rule as counting what you compared,
arriving where a value is transformed on its way in: **the premise is
what the system actually has, never what you handed it.**

## ONE FAILURE IN FIFTEEN RUNS WAS NOT FLAKINESS

2026-08-28, and it is the most expensive reading this file could have
got wrong, because every cheap explanation was available and all of them
were comfortable. A per-test coverage re-record failed one test of 645,
in a shard running beside two others on a loaded machine. (T-82.)

## AN ORACLE A NEVER-SHOWN WINDOW CANNOT ANSWER

The guard for the save's progress bar asserted `not
progress.isVisible()` before the save and again after it, and BOTH
halves passed with the repair mutated away. Offscreen -- which is every
runner and every CI job here -- a widget in a window nobody has called
`show()` on answers False to `isVisible` whatever anybody set, so the
assertion was true of the fixed software, of the broken software, and of
software that had never had a progress bar at all. (T-83.)

## A LEG THAT RUNS AFTER THE STATE IT IS ABOUT

A test may drive exactly the right act and still assert nothing,
because the step before it destroyed the condition. The re-tile leg of
`test_taking_an_element_back_from_qgis_restyles_at_once` asserted that a
taken-back element is re-seeded rather than inheriting the dock's
renderer -- and it ran on the element the arm ABOVE had just reclaimed,
whose layer therefore wore the plugin's own renderer. (T-84.)

## STAGE WHAT A SECOND PROCESS LEAVES, NOT THE SECOND PROCESS

Some defects need another program: a colleague saving the shared
GeoPackage while your map is open cannot be driven from one process,
because a running QGIS serves its own cached pages of a file and because
the stale-table drop is gated on the file being the saver's own -- a
fresh dialog meeting somebody else's file does not own it, so its drop
returns at the first line and the precondition never exists. (T-85.)

## PROVE THE QUANTITY THE FAILURE MEASURES

A guard can be careful, pass, and be about something else. The ceiling
guard of 2026-08-29 measured `minimumSizeHint().width()`. The tests
failing on Windows measured `dlg.width()` after `show()`. Four different
repairs to the window's width each made that guard pass, and every one
of them was inert or wrong on the platform that was red -- the guard
could not tell, because a minimum is not a preferred size and a window
opens at the latter. (T-86.)

## BUILD THE FIXTURE THROUGH THE PRODUCT'S OWN DOOR

2026-08-29, and it produced two probes with OPPOSITE answers, both
mine, before the variable neither was controlling turned up. Asked
whether the vendored `Topology` works on weaves, the first probe built
units by handing the catalogue's raw spec straight to
`WeaveUnit(**spec)`. Twill and basket died IN THE CONSTRUCTOR --
`catalog.TILINGS_BY_N` stores a weave's passing pattern as the string a
person types, `1,2,2,1`, and `catalog.make_unit` is what parses it
through `get_over_under` -- so two of the four were reported as
unsupported by the library when they had never been built at all.
(T-87.)

## A TEST THAT LOCATES A MOMENT BY COUNTING IS RE-AIMED BY A SLOWER MACHINE

2026-08-31, found by CI's coverage leg on the candidate's own commit
and by nothing here: `a topology landing does not strand a live tick`
passed three times out of three locally and failed on Linux under the
per-test recorder, where every step costs several times what it costs on
this Mac. (T-88.)

## A probe that cannot reach its own case (2026-08-31)

Three of the day's findings were probes, not products, and all three
had the same shape: the instrument was aimed a little to one side of the
thing it was about, and it reported health. **A ceiling is the case, and
filling PAST it measures the other path.** The Messages log trims at
500. A log already at 500 keeps its ROW COUNT UNCHANGED on the next
message, so every cell write is an overwrite -- which is what makes a
`ResizeToContents` column re-measure. (T-89.)

## The mutation runner needs the suite's own platform (2026-08-31)

`tools/mutation_check.py` is documented as `env -u PYTHONHOME -u
PYTHONPATH python3 tools/mutation_check.py`, which passes no
`QT_QPA_PLATFORM` -- while every other way of running a test sets
`offscreen`. Most entries do not care. An entry whose test measures
LAYOUT does, because offscreen and cocoa assemble a window
differently, and two font entries came back UNJUDGEABLE reading
exactly like broken tests. `child_environment()` now `setdefault`s
`QT_QPA_PLATFORM=offscreen`, so the trap is closed in the tool.

The general question for any harness: which environment variables does
the SUITE set that this harness does not, and which of them could
change an answer rather than merely a speed?

## Restore in a `finally`, and check the restore ran (2026-08-31)

A proof that a guard can fail works by breaking the product, running
the test, and putting the product back. On this day one such run was
launched as a single shell chain whose last step was the restore --
and the command timed out at ten minutes, so the kill landed between
the run and the restore and left a deliberate no-op in shipped source.
Nothing but the next `git status` would have said so.

Write the restore so it cannot be skipped: a `finally`, a trap, or a
separate command issued immediately and verified by reading the file
back. This project's own rule already says a mutating job must ASSERT
that it put the file back; the addition is that a TIMEOUT is one of
the ways it fails to.

## Five instrument faults in one day, every one already written here

2026-08-31, round five. Counted because a day whose findings are
mostly its own instruments is a day nobody should act on -- and because
every one of these was made by somebody who had read the entry
describing it that morning. **TWO ARMS SHARING ONE `QgsProject` IS A
CONTAMINATED CONTROL, AND IT READS AS MACHINE CONTENTION.** A two-arm
probe ran its control first; the treatment's dialog then met the
control's output layers and its topology never built, so the arm died on
its own premise. (T-90.)

## A ceiling is the case, and a fence is the boundary

Two more from the same day, both about a check that stops seeing.

**A TRIPLE-BACKTICK FENCE SHIFTS EVERY INLINE SPAN BELOW IT.** Such a
three backticks; a span pattern needs a non-backtick between a pair, so
the third becomes an opener and everything after it inverts -- real
spans read as prose, prose reads as spans. A gate reading documents for
quoted commands therefore went blind from the first fence onward, and
its per-document check could not catch that, because a document
contributing SOMETHING passes. Blank fenced blocks with SPACES, so
every offset and every quoted line number is unchanged.

**AND THE FIX MUST NOT MOVE THE LINE NUMBERS A FAILURE QUOTES.**
Removing the fenced text instead of blanking it would shorten the copy
and move every line number below, so a failure would name the wrong
line -- worse than not reporting it, because somebody would go and
look.

## Assert both answers when a rule has two, and the second is usually
## the one that catches the repair

Three guards written that day each assert a pair, and in each case the
second half is what stops a lazy repair passing:

- a CRS must NOT move the file's topology key, AND a tile inset and a
  rotation still MUST -- a key insensitive to everything would be a
  worse fault than the one being cured;
- a Save must be deferred with live update ON, AND honoured at once
  with it off -- a repair that simply stopped deferring would pass half
  and destroy the behaviour the maintainer's ruling asked for;
- a file's motif must be PRESENT after a design change, AND its key
  must have MOVED -- keeping the old pair satisfies the first alone and
  is the exact fault that preceded this one.

## A sandbox must carry every document the suite reads

`tools/sandbox.py` copied CLAUDE.md and MAINTAINING.md and not README.md
or ROADMAP.md, though `DOCUMENTED_COMMAND_DOCS` names all four. A test
reading either died with FileNotFoundError inside the sandbox, so its
catalogue entries came back UNJUDGEABLE -- counted as neither caught
nor survived, which is the state that list's own comment already calls
worse than a failure. Found while proving an entry whose test reads
README.md.
ASK OF ANY HARNESS THAT COPIES A TREE what the tests it runs actually
open, and prefer to derive that list rather than keep it by hand.

## A PREMISE ASKED IN THE SAME BREATH AS A SETTLE READS THE OLD STATE

(2026-08-31.) A guard waited for the topology build to go quiet and
then asserted, on the next line, that the design no longer carried a
topology. It failed -- while a direct measurement of the very same
dialog said it should pass, which sent the diagnosis after a
contradiction that did not exist. (T-91.)

## A TEST THAT RESIZES A CHILD WIDGET HAS MEASURED NOTHING

(Same day, and three of four failed attempts at one guard turned on
this alone.) A widget inside a layout does not keep a size handed to
it: the layout gives it whatever is left over on the next pass, so a
resize to its own floor is gone before anything can read it.

Drive the WINDOW, which is what a person drags, and then READ the
child's size rather than assuming it took. The window's own minimum is
what pins a pane in practice, and it is composed from every pane's
floor plus whatever sits beside them -- so a mutation lowering one
child's floor can change nothing observable at all, and its entry
survives while the code is genuinely wrong-headed.

The same caution reaches any test that asserts about a size, a
position or a hit target: those are all downstream of a layout pass
that has its own opinion.

## THE DESIGN A TEST DRIVES CAN REFUSE THE CASE, AND A CLEAN RESULT THEN MEANS NOTHING

2026-09-01, twice in one afternoon, and both of my first probes came
back clean on real defects. A vertex drag past its control's range
records an out-of-range value on `archimedean 4.8.8` and CANNOT on
`laves 3.3.4.3.4`: there the library refuses a nudge that large, the
preview raises, and the handler clears the record, which is correct.
(T-92.)

## AN ENTRY THAT SURVIVES WITH THE CONTROL RUN IS A TEST THAT HAS STOPPED ARRIVING

Same day. `a-changed-file-is-never-swept` was re-anchored onto the
call as it now reads and then SURVIVED. The prescribed discriminator
is to break every route at once: both the `if not vanished` skip and
the remembered ownership answer were mutated together, in a script
whose restore is verified byte for byte, and the named test still
PASSED. That rules out both of the usual readings -- the axis is not
weak and it is not redundantly held -- and leaves the third: the test
is no longer reaching that case at all.

**AND THE ENTRY SAYS SO RATHER THAN REPORTING A BARE SURVIVED.** The
comment at the entry records the control and names re-staging that
journey as owed work. An entry quietly reporting SURVIVED is worth
less than one that says which of the three possibilities was measured.

## A MUTATION THAT LEAVES THE WORK IN PLACE IS INERT, AND READS AS A WEAK TEST

Same day, on the dual's lattice. The entry replaced the two lines
above a loop with the old key lookup -- and the loop below still
filled the same two names, so nothing changed and the entry SURVIVED.
Anchored on the WHOLE DECISION, from the assignment through the
`break`, it caught at once. When an entry survives, ask first whether
the mutation actually removed the behaviour: killing the site
outright is the discriminator, and this project already carries it
from the other direction.

## STAGE A CONDITION THAT A RACE WOULD OTHERWISE DECIDE

Same day, in a guard of my own that failed one way alone and the other
way in a batch. It waited for a design change with the experimental
box off to leave a STALE topology in the panel, which is the journey
the defect needs -- but whether a build queued earlier had landed by
then depends on the machine, so the premise failed as "the topology
moved" in a batch and as "nothing is stale" when run alone. The
repair was to put the previous design's topology and dual back by
hand, in one line, which is the same state arrived at without a race.
Where a case depends on a window, close the window; a premise about a
window is still a bet on the machine.

## A CELL THAT CANNOT SET ITS OWN STAGE MUST SAY SO IN ITS OWN WORDS

2026-09-01, from Windows, and the message it produced was a sentence
about the PRODUCT that happens to describe correct behaviour. The
topology matrix aims each cell at a vertex or an edge drawn inside the
widget, and fell through with whatever the previous cell had selected
when it could not find one. (T-93.)

## A PREMISE THAT FAILS ELSEWHERE MUST CARRY WHAT HAPPENED, NOT WHAT IT EXPECTED

2026-09-01, from one Linux shard. `test_topology_edits_come_back_from_
the_file` failed its own premise with "the edits moved nothing, so a
roundtrip that preserved nothing would pass -- both (4, 250000.0,
3863.703)". The number is the whole diagnosis and the sentence did not
say so: it equals the PLAIN design rather than the rotated one, which
means the replay handed back the original -- both edits refused --
rather than the reading being taken early, which is the other and much
likelier-sounding explanation. **SO A PREMISE ABOUT A REPLAY REPORTS THE
REPLAY.** It now carries the ground after the first edit alone, the
per-edit marks `topology_edits.apply` returns, and the sentence the
panel was given, so the next occurrence names its own cause. (T-94.)

## FOUR INSTRUMENT FAULTS IN ONE ROUND, AND WHAT EACH LOOKED LIKE

2026-09-01, rewriting the save and the load. Counted because a day
whose findings are mostly its own instruments is a day nobody should act
on, and because every one of these read as a finding about the PRODUCT
first. **A `QgsApplication` LEFT UNBOUND IS COLLECTED ON THE NEXT
LINE.** The probe died of a segmentation fault with two nullptr warnings
and nothing else -- which is indistinguishable from the thing being
measured crashing. (T-95.)

## AN INERT MUTATION AND A WEAK TEST, TOLD APART BY ASKING THE FORMAT

Same day. A mutation removing `SetFieldNull` from a writer survived a
differential that compares every attribute of every feature. The
prescribed discriminator is to ask whether the mutation removed the
behaviour at all -- and asked of GDAL, a feature written with
`SetFieldNull` and one whose field is never set BOTH read back as set,
null and None. The two produce the identical row in a GeoPackage, so no
comparison of what the file HOLDS can tell them apart.

The line is kept, because it is the explicit spelling of the intent and
costs nothing, and the measurement is written at the site -- so an
entry standing there and reporting SURVIVED is read as the inert
mutation it is rather than as a test too weak to notice. Those two look
identical and need opposite repairs.

## RE-INDENTING A LONG BLOCK: PROVE THE BODY DID NOT MOVE

Wrapping a ninety-line loop in a try/finally means re-indenting every
line of it, and a wholesale span rewrite is how this project has twice
taken a neighbour with it. Doing it by hand is the risk; doing it
mechanically is not enough on its own.

The cheap proof is to strip the indentation back off afterwards and
require the result to equal the original text, character for
character, before anything is written. That catches a line eaten, a
line duplicated and a blank line mangled, none of which a parse check
would notice -- a file that parses can still be missing a statement.

## A WAITER THAT RETURNS ON A STALE ANSWER, AND A QUEUE THAT DEFERS

2026-09-01, two tests that passed alone every time and failed in a
three-shard run. Both were read as timing; neither was, and in both
cases the mechanism is a branch somebody can point at. **A QUEUE MADE
WHILE A BUILD IS RUNNING DOES NOT START A SECOND.** `_queue_topology`
sets `_topology_wanted` and returns, and the landing re-queues -- which
says a build is coming all over again. (T-96.)

## A SKIP WITHOUT A LINE IS A CELL THAT NEVER EXISTED

Same day, and it is the sharpest thing the label/key separation
taught. The topology matrix guards each cell with "is this family on
offer", and asked it of the chooser's TEXT -- the label, which since
that morning may carry a common name. Every renamed design was therefore
skipped, and skipped WITHOUT a line in the record of what was passed
over: the count came back 15 of 35 and named ONE skip of nineteen.
(T-97.)

## STAGING AND ASSERTING ARE NOT THE SAME MOVE, AND I CONFUSED THEM

2026-09-01, an hour after writing the entry above about closing a
window rather than sampling it. The repair to `the topology tab says
when it is working` waited for the topology to have an answer and then
ASSERTED, on the next line, that no build was outstanding. (T-98.)

## A FAMILY GUARD EARNS ITS KEEP ON FILES THAT DID NOT EXIST YET

2026-09-01. The guard written on 2026-08-28 for `if os.path.exists(x):
os.remove(x)` -- the race that cost a coverage shard its entire run,
three processes seeing the file, two removing it, the third dying before
a single test -- went red on the mutation workflow's coverage leg and
named THREE probes by file and line. (T-99.)

## ONE OWNER FOR "IS IT QUIET", AND THE TEST THAT MUST NOT ASK IT

2026-09-01, found by CI on a candidate's own commit and costing that
candidate. Three tests carried the same premise -- "the chosen vertex
offers no handle to drag" -- and all three staged it the same way: wait
with `_wait_for_the_topology`, click a vertex, tick, read the handles.
(T-100.)

## AIM AT A DRAWING BY ASKING THE PRODUCT, NOT BY COMPUTING A POINT

2026-09-01, found by reading a superseded CI round rather than by any
failure here. `test_several_classes_can_be_moved_together` aimed its
shift-click at "a vertex of the second class" by taking the FIRST such
vertex drawn inside the widget. One Linux leg failed it with the
selection left exactly where the plain click had put it, while this Mac
passed every time. (T-101.)

## READ A VERDICT AND ITS ORACLE IN ONE BREATH

2026-09-02, found by CI on a candidate's own commit and the second
suite fault to spend one. `the symmetries are drawn and gate what cannot
move` failed on the Linux 4.0.3 leg with "class B has 1 free
direction(s) and its push is greyed" -- a disagreement between a control
and the arithmetic behind it that CANNOT HAPPEN, because the tab and the
test call the same function. (T-102.)

## A REPAIR CAN MOVE THE JOURNEY ITS OWN GUARD DRIVES

2026-09-02, three times in one campaign day, and it is the most
expensive shape of the round because every instance looks like a passing
test. **A GUARD IS STAGED ON A JOURNEY, AND A REPAIR CAN CLOSE THAT
JOURNEY.** A cancel pressed during a write was guarded by delivering a
close from the write's own pump, which opened the waiting window.
(T-103.)

## A PROBE'S OWN SUBPROCESS INHERITS THE QGIS ENVIRONMENT

2026-09-02. A probe needed a second PROCESS to hold a lock, because a
running QGIS serves its own cached pages and this project's rule is
that the second writer must be one. It launched `/usr/bin/python3`
without an environment, which inherited `PYTHONHOME` from the QGIS
interpreter it was running under and died at "No module named
'encodings'" -- the two-interpreters trap this project has recorded
twice, arriving inside an instrument.

WHAT MADE IT SURVIVABLE was the premise. The probe asked, separately,
whether the lock was actually held; it reported that another writer
had got in, so the arm was INCONCLUSIVE rather than clean. Without
that line the run would have read as "the claim does not reproduce",
which is the most expensive answer a probe can give.

**SO PASS A CHOSEN ENVIRONMENT TO ANY CHILD** -- `env={"PATH":
"/usr/bin:/bin"}` is enough -- and assert the condition the child was
launched to create, rather than assuming the launch worked.

## THE SHAPE OF A LOCK DECIDES WHICH FAILURE YOU MEET

Same day, and it nearly cost a real defect. Asked to reproduce "the
commit fails", the obvious staging is to lock the file -- and a WRITE
lock held by another process makes the FIRST FEATURE fail, which the
code already reports correctly and honestly. Only a SHARED READ
transaction lets every table through and refuses the commit itself.

Both are "the file is locked" in ordinary speech and they exercise
different halves of the code. When a claim names a failure at a
particular STEP, stage the failure at that step: ask what the step
needs that the others do not -- here, the exclusive lock a commit
takes and a write does not.

## THREE PREMISES THAT WERE BETS ON THE MACHINE

2026-09-02, all three found by CI and none by this machine, and they
had between them spent candidates while passing here every time. The
shape is one: A READING TAKEN AFTER A FIXED NUMBER OF TICKS RATHER THAN
AFTER THE THING IT IS ABOUT HAS HAPPENED. **A RACE THE FIXTURE HOPED TO
WIN.** `a save waits for a build already coming` needs a topology build
still outstanding at the press, and relied on the one the design change
queued not having landed yet. (T-104.)

## A CORRELATION WITH YOUR OWN COMMIT IS A HYPOTHESIS

Same day, and it is the cheapest half-hour of the round. CI went red
on three legs at a commit of mine, having been GREEN on every job at the
commit before it. Everything fitted: three legs failing at once is this
project's own tell for a claim about the CODE rather than about timing,
and the commit had changed how a save decides its table names. (T-105.)

## FOUR FIXTURES THAT COULD NOT REACH THEIR OWN CASE, IN ONE DAY

Same day, mine, counted because a day whose findings are mostly its
own instruments is a day nobody should act on -- and because every one
of them was caught by a premise or a control rather than by reading. **A
CONTROL THAT COULD NOT FAIL EITHER.** A probe comparing the two Load
doors reported both sound, because it drew and saved a map in the same
window it then pressed Load in -- and a LANDING sets the very flag the
press was supposed to set. (T-106.)

## A WAITER ANSWERS "IS ANYTHING OUTSTANDING", WHICH IS NOT "DID IT HAPPEN"

2026-09-02, and it had spread to ten registered tests before anybody
asked what the sentence beside it claimed. `_the_topology_tab_is_quiet`
returns True when no build is in flight, none is queued behind one and
no working sentence is up. A test then staged its ground with assert
_the_topology_tab_is_quiet(dlg), \ "PREMISE: no topology was built, so
there are no classes to aim at" and read the panel three lines later.
(T-107.)

## A RESTORE HELD BY TWO WRITERS CAN ONLY BE JUDGED WHERE ONE DOES NOT RUN

Same day, and it took an entry SURVIVING TWICE to find the second
writer. A save takes a layer's subset off to write the map, because
`getFeatures()` honours one, and puts it back. An owed line said the
restore assertion could not fail because the already-saved skip means a
filtered layer is never written -- true, and only half of it. (T-108.)

## A UNIFORM VERDICT CAN BE THE ANSWER RATHER THAN THE INSTRUMENT

2026-09-02, and it corrects a cause this file had carried since
2026-09-01. This document's oldest tell is that a result which comes
back the same for every input is almost always the instrument.
`tools/ci_probe_the_ topology_aim.py` reported the SAME numbers on Linux
4.0.0, Linux 4.0.3, Linux stable and macOS -- 420x462, `Sans Serif` at
9pt, class A four drawn and three reachable, class B eight of eight,
both classes held. (T-109.)

## A GATE THAT CANNOT START IS NOT A GATE THAT ANSWERED

Same day, inside a commit chain. `check_no_secrets` exited 1 and the
commit correctly did not run -- and it had found nothing: the shell had
sourced the QGIS environment, so a plain `python3` inherited PYTHONHOME
and died at "No module named 'encodings'". Re-asked under `env -u
PYTHONHOME -u PYTHONPATH python3` it checks 321 files clean. (T-110.)


## A RULING THAT IS AN ORDER IS TWO CLAIMS, AND ONE ENTRY CANNOT HOLD IT

(2026-09-02, ledger row 26.) "The save happens first, then the load"
reads as one sentence and is two behaviours. A repair that defers the
Load and never performs it satisfies every reading of the first half:
the promised save lands on the right file, the other map is untouched,
and the only thing wrong is a button that did nothing.

SO THE GUARD ASSERTS BOTH, and each half carries its OWN catalogue
entry -- one mutating the deferral so the Load ignores the promise,
one making the deferred Load never happen. Two entries rather than one
deliberately, for the reason this file already gives about a record's
write and its read: an entry a sibling can satisfy reports `caught`
about nothing.

THE TELL FOR THE FAMILY: when a decision is phrased as an ORDER, or as
"X, then Y", count the verbs. Each is a promise somebody can break on
its own.

## A PROBE'S CONTROL MUST MOVE ONE TERM, AND AN INSTRUMENT MUST ASK
## THE PRODUCT ITS OWN QUESTION

(2026-09-02, verifying the shelf key's blindness to the dual, and both
faults were in one probe.) ITS CONTROL CHANGED THE DESIGN IT WAS
COMPARING AGAINST. The control for "an ordinary design change moves the
shelf key" moved the ELEMENT COUNT -- which repopulates the family list
and lands on whatever that count offers, so `hex-slice 4#4` became
`square-colouring 5#5` and every reading after it was about a design
nobody had chosen. (T-111.)

## A WATCHER IS ARMED AS WELL AS HAND-RUN, AND A PIPE DEFEATS EITHER

(2026-09-02, the twenty-fifth watcher fault here, and the lesson was
written into this file the same morning.) A watcher hand-run into a
pipe printed nothing, which is recorded above. Hours later the same
watcher was ARMED as `script | tail -40`, to keep its output short --
and `tail` buffers to EOF, so a watcher running perfectly well printed
nothing at all and the maintainer asked why it did not work.

THE RULE HAD BEEN LEARNED AT ONE MOMENT AND APPLIED THERE. Arming is a
second moment with its own habits, and the pipe arrived as a tidiness
measure rather than as plumbing. Redirect to a FILE and read the file;
where the harness reports a background job's output, remember that a
pipe flushes when the job EXITS, which for a watcher is exactly too
late to be a watcher.


## A READING TAKEN BEFORE THE AIMING IS A BET ON THE MACHINE

2026-09-02, found by CI's coverage leg on rc13's own commit and by
nothing here. `a build that lands mid drag does not wipe the gesture`
failed on its MAIN assertion this time rather than on a premise -- "the
panel adopted a new topology mid-gesture" -- 256 passed and 1 failed on
one shard of three, each shard naming the same total of 772, while the
same test passed in that candidate's own local suite at 4.8s against the
runner's 11.7s. (T-112.)

## AN ALLOWANCE SIZED ON THIS MAC IS AN ALLOWANCE THIS MAC WILL NEVER MEET

Every ceiling in this suite is `CONTENTION` times something -- 2.5 for
a sharded run multiplied by each platform's declared slowness, so a
three-shard Linux job is given seven and a half times this machine's
patience. FOUR SHARED WAIT HELPERS HAD NO SUCH FACTOR:
`_wait_for_the_topology`, `_the_topology_tab_is_quiet`,
`_settle_topology` (which counts ticks rather than seconds) and
`_settle` itself, the oldest and most-called of the four. (T-113.)

## A PREDICTION IS AN AXIS, AND A WRONG AXIS IS OBEYED FAITHFULLY

2026-09-03, and it is the best argument this file has for writing down
HOW a thing was measured rather than only what was concluded. An abort
in the harness's own teardown -- `corrupted double-linked list`, exit
134, at `check`'s `project.clear()` on the line after a test PASSED --
was recorded on 2026-09-01 as belonging to QGIS 4.0.0: "the abort is
4.0.0's alone -- 4.0.3 and stable were green on the same tree". (T-114.)


## A PROBE WITH LIVE UPDATE OFF MEASURES A JOURNEY NOBODY TAKES

2026-09-04, verifying a field report that an edit's drawing reverts for
a second after the drop. The probe reported something stronger and
wrong: that the edit never reached the drawing at all.

The kit's own dialog helper switches live update OFF and says at its
docstring that this is a decision to revisit, because the product's
default is ON. With it off nothing rebuilds, so the edit sat in the
record and the drawing never moved -- a journey the person reporting
the defect was not on.

**THE TELL WAS THE DISAGREEMENT WITH THE REPORT.** They said it
corrects itself after a few seconds; the probe said it never corrects.
Where a measurement contradicts the person holding the failure, suspect
the measurement first -- this file already says a reproduction that
will not reproduce is a signal about the DIFFERENCE between two
sessions, and a control the harness holds at a value nobody holds is
the commonest such difference.

## AND A WAITER THAT RETURNS WHEN THE PANEL HOLDS AN ANSWER NEVER WAITS
## FOR ONE TO ARRIVE

Same probe, same run, and the two faults together produced one
confident wrong answer. The settle asked "is a build in flight, is one
queued, does the panel hold a topology" -- and the panel was still
holding the one from BEFORE the drag, while the rebuild had not yet
been queued. So it returned at once and the reading was taken before
anything could have happened.

**WAIT FOR THE THING TO MOVE, BOUNDED BY A HANG-CATCHER**, not for the
absence of outstanding work. Rewritten to wait until the drawn
fingerprint differs from the one taken before the press, the same probe
measured the revert exactly: the old design stays up for 1.676s and the
settled drawing is IDENTICAL to what the preview had been showing all
along.

This is the fifth site of one mechanism in this suite and the first
found from a field report rather than from a runner.

## AN INERT MUTATION AND A WEAK TEST BOTH REPORT SURVIVED, AND ONE ROUND
## PRODUCED BOTH

2026-09-04, proving two entries over one patch. They needed opposite
repairs and reading either alone would have suggested the wrong one.
**THE INERT ONE WAS RESCUED BY THE PATCH'S OWN GUARD.** The entry
widened a spatial predicate so that tiles which merely touch a zone
would be treated as lying inside it. (T-115.)

## A RATE FROM TOO FEW DRAWS, PUBLISHED TWICE IN ONE HOUR

(2026-09-04, chasing the topology matrix's one failing cell, and both
were mine.) The cell reproduced on the SECOND of two attempts and was
written up as DETERMINISTIC. The next run of the same probe answered in
1.43 seconds both times. Then a two-arm comparison came back 2 of 8 at
HEAD against 0 of 8 at the commit before that session's tiling patches,
which reads exactly like a verdict on those patches -- and HEAD then
produced 0 of 16 on its own, which disposes of it. (T-116.)

## A GUARD CAN BE AIMED AT A STATE WITHOUT KNOWING WHAT PRODUCES IT

(Same day, and it is the other half of the entry above.) The stall's
CAUSE is undiagnosed: QGIS accepts a topology build, leaves it Queued
and never starts it, four times in eighty-six attempts and then not at
all in thirty. A condition nobody can stage cannot be tested, and this
project's rule is to close the window rather than count how often it
opens -- so the window was not the target. (T-117.)

## A SURVIVOR NAMED THE ARM THAT WAS MISSING

(2026-09-04, repairing the drop that cleared its own preview.)
`_commit_the_drag` has three exits that record nothing, and each must
clear the preview. An entry was aimed at the third -- the no-travel
test, which is what a person meets when they take hold of a handle and
think better of it -- and it came back SURVIVED. It was not a weak test.
(T-118.)

## A CLAIM ABOUT AN INTERVAL IS READ INSIDE THE INTERVAL

(Same day.) The drop's defect is that the wrong picture is drawn
BETWEEN the release and the landing. A guard that settles first reads
the answer that arrives afterwards -- which is correct in both arms --
and passes whatever happened in between.

So the reading is taken ONE PUMP after the release, and the landing is
asked separately, afterwards, whether what was kept on screen was what
the edit produced. Two readings at two moments, because the claim has
two halves: the picture was right during the interval, and it was not a
lie about where the design ended up.
