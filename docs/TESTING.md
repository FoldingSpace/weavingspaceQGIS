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

## How to add to this file

This file is binding and is read before a test is written or changed,
so it is kept short by a budget and a SHAPE that `tools/doc_archive.py`
checks at every push. Its first half is PROCEDURE -- the probe kit, the
test shapes, the matrix method, where an expectation may come from --
and is edited in place when the procedure changes. Its second half is
LESSONS, one section per theme: the harness, waits and moments,
fixtures, assertions and oracles, guards and the catalogue, the
product, tools. To add a lesson:

1. Find its theme and write it as ONE CLAUSE in the bullet it extends,
   with about one clause of evidence and its id -- "a leg that runs
   after the state it is about measures nothing (T-84)". Do not open
   with a date; the run, the wrong hypotheses and the measurement are
   the account.
2. Mint the id with `python3 tools/doc_archive.py --mint T "title"`,
   write the account under it in docs/TESTING-archived.md, and quote
   the id. The check refuses a stub nothing quotes.
3. Where no theme fits, use "Inbox: lessons not yet themed" at the end,
   which holds six at most; folding it into the themes is the pass.

A new `## ` section, a section past 120 lines, an inbox past six, or a
paragraph that opens with a date fails `tools/check_standards.py` with
the fix in the message. (Maintainer's ask, 2026-09-05: self-fixing at
low cost for whoever edits these documents next.)

## A PROBE HAS A KIT NOW, AND ITS TRAPS ARE IN IT

`tools/probe_kit.py` (2026-08-28) is the forty lines every probe was
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

## Where a guard's expectation should come from, when the product is the only thing that knows the answer

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

Nearly every real defect came from a DIFFERENTIAL: two independent
descriptions of one thing, compared, so a disagreement is a defect by
construction and no oracle is needed -- the docstring audit, the first
Linux run, the colourspace comparison against upstream's renderer.
Mutation testing is not on that list: a campaign of 128 survivors
yielded one product defect. Budget it as suite measurement and spend
the creative effort on new differentials (T-122). Where to point the
next one: this software's characteristic failure is a wrong map that
looks right, and the plugin describes one state in five places --
table, preview, map, colour editor, saved project -- so
`test_random_designs_keep_their_views_in_agreement` compares five axes,
and the shape to check FIRST in any sweep is a dead axis skipped behind
a guard: count what each axis compared and assert the count. (T-141.)

- A TEST CAN BE WRITTEN AROUND A DEFECT and then pin it as correct
  (T-123): read any accommodation inside a test -- a guard, a swapped
  scheme, a narrowed fixture -- as a REPORT that the software surprised
  somebody, and ask whether they were right that it was the fixture.
- A FIX CAN BE RIGHT AND STILL WRONG TO SHIP, and the blast radius is
  the evidence: nineteen tests moved, and one said why (T-124). Read
  the count as how deep an assumption runs, and read the tests before
  deciding they are all wrong.
- A DIFFERENTIAL CANNOT SEE A FAULT ITS EXPECTED SIDE SHARES:
  `visual_pair` builds both sides through `seed_renderer`, so removing
  the pin removed it from both. Ask which code the two sides share and
  assert separately whatever lives in it.
- A FIXTURE CAN HIDE A WHOLE CLASS OF DEFECT: five classes over four
  values collapse quantile breaks onto the values, so four element
  ladders agreed whatever the code did, and one colour meant four
  numbers from 0.23.0 on (T-125). When a premise is a relation between
  two runs, ask whether the FIXTURE is what makes it hold.
- A PROBE THAT RETURNS IS NOT A PROBE THAT MEASURED: a renderer asked
  without `startRender` answers something that looks exactly like data.
- THE CHEAPEST DIFFERENTIAL IS A PATH AGAINST ITS SIBLING: the
  categorical and graduated paths are near-twins written months apart,
  and reading one beside the other found three defects with no machine
  (T-126). Anchor each twin separately in the catalogue, and never
  write a rule that names one sibling.
- HUNTING is its own instrument: how to run one and which directions
  have paid are in docs/process/HUNT-RECORD.md.

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

When saving stopped being a side effect of drawing (2026-08-27), six
hundred and forty tests had been written against a plugin where setting
an output path made every Generate write the file; the ruling made
writing a separate press. What follows is what the conversion cost, what
it found, and the four ways a mechanical sweep goes wrong, because the
shape recurs whenever an act is split. **THE FAITHFUL CONVERSION IS THE
ONE THAT CHANGES NO TEST'S MEANING.** A run wrote whenever a path was
set, so a Save press inserted at exactly the moment the old write
happened reproduces the state each test was written against. (T-42.)

## WHAT "THE FILE DID NOT CHANGE" MEANS, MEASURED

It cost three drafts of one test (2026-08-27). **BYTES ARE NOT
A PROPERTY OF AN UNTOUCHED GEOPACKAGE.** A Generate after a Save leaves
every table, every feature count, every embedded style and the record
IDENTICAL while the file grows from 184,320 bytes to 356,352 -- sqlite
reorganising it as the layers that were reading it are replaced and let
go. (T-43.)

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

Extending the symbology matrix from three axes to four (2026-08-19,
at the maintainer's asking): interaction with QGIS -- class boundaries and
copy-paste -- is where this plugin's defects come from, so cover it
high-dimensionally. **THE SPACE IS FREE; ONLY THE SPINE AND THE SAMPLE
COST.** Twelve routes, nine shapes, three aftermaths and three schemes
is a crossing of nearly a thousand cells, and it runs in about two
minutes, because the spine is bounded deliberately and everything else
is drawn under a printed seed. (T-44.)

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

## THE HARNESS IS PART OF THE MEASUREMENT

Every runner sets `QT_QPA_PLATFORM=offscreen`, which supplies Sans
Serif at 9pt and assembles a window differently from cocoa; a desktop
supplies 13pt and the macOS style, whose form layouts do not stretch
where Fusion's do. A layout guard therefore measures the platform
unless it SETS the quantity the other machine has -- the font, the
style -- and reads the child's size afterwards; setting the font alone
half-works, which is worse than not working (T-1, T-2, T-4). The
accounts are T-134.

- A CHILD INHERITS THE SUITE'S ENVIRONMENT: `WEAVINGSPACE_TEST_SHARD`
  tells it it is shard two of three (T-25); a probe's own subprocess
  inherits `PYTHONHOME` and dies at `encodings`, so pass a chosen
  environment and assert the condition the child was launched to
  create; the mutation runner setdefaults `offscreen`, since two font
  entries came back UNJUDGEABLE without it; a sandbox carries every
  document the suite reads, and the list is derived rather than kept.
  A gate that cannot start is not a gate that answered: the secrets
  check under the QGIS environment exited 1 having checked nothing
  (T-110).
- SILENCE WITH EXIT 0 IS NOT A PASS: the suite ends through `os._exit`,
  so a piped PASS line is discarded while a failure's traceback
  survives (T-80); `print()` inside a Qt slot goes nowhere under
  captured output, so write to a FILE and prove it is written on a case
  that reaches the code (T-51).
- A SECOND MACHINE FINDS ASSUMPTIONS, not defects: sixty-nine of the
  first Linux run's seventy failures were one missing geopandas (T-21);
  nothing had ever unpacked the zip a user installs (T-22); a test's
  name is a hypothesis about its own failure, and was believed twice
  (T-23); a stack says where a process WAS, and the same test at 392,
  486 and 550 s on three legs of one round is the runner rather than
  the code (T-130); a red suite can mean the software got SLOWER, and
  reading it as a hang costs the diagnosis (T-7).

## A TEST THAT RESIZES A CHILD WIDGET HAS MEASURED NOTHING

(Three of four failed attempts at one guard, the same day, turned on
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

## WAITS, MOMENTS AND CEILINGS

The accounts are T-135.

- WAIT ON THE EVENT, NOT ON A NUMBER OF SECONDS: a flat ten seconds
  failed Windows at 18.7 and passed macOS at 9.0 on identical code, and
  waiting on the task ENDING is faster on a quick machine, patient on a
  slow one and stricter (T-131). THIS BINDS A PREMISE AS HARD AS AN
  ASSERTION: three tests changed a control, pumped a fixed fifty
  milliseconds and asserted the debounce was armed, and Windows failed
  that premise on three pushes of one night while every other platform
  passed -- a premise that pumps a fixed number of ticks is a bet on
  the machine, and it fails on the leg the suite is least able to
  reproduce. Where a repair's waiting branch CANNOT run at home, the
  targeted Windows run is what judges it (T-148). Keep the clock only to catch a hang: a
  ceiling is never a performance budget, every one is `CONTENTION`
  times a measured figure, and four shared wait helpers had no such
  factor, so an allowance sized on this Mac is one this Mac will never
  meet (T-24, T-113, T-88).
- A WAITER'S EXIT CONDITION MUST NOT BE ALREADY TRUE AT THE MOMENT OF
  ASKING. The absence of a build task is true before a build is queued
  as well as after it lands; a panel holding an answer holds the
  PREVIOUS one after a change queues a rebuild; "nothing outstanding"
  is not "it happened"; a queue made while a build is running starts no
  second one. Take a fingerprint before the act and wait for it to
  MOVE, bounded by a hang-catcher, and make quiet PERSIST -- three
  clear checks, 600 ms, longer than the queueing gap and shorter than
  the cheapest build (T-132, T-133, T-107, T-96). One owner answers "is
  it quiet", the repair belongs at the waiter and not at its
  twenty-one callers (T-100), and a waiter that gives up says what it
  was still waiting on -- and it counts a DEFERRED press as work still
  coming, since a Generate waiting for a topology replay leaves no
  task and no timer, and two dual tests read "nothing landed" under a
  loaded machine (T-146).
- A PREMISE ASKED IN THE SAME BREATH AS A SETTLE READS THE OLD STATE
  (T-91); staging and asserting are different moves (T-98); a reading
  taken after a fixed number of ticks, or before the aiming clicks, is
  a bet on the machine that CI loses and this Mac wins (T-104, T-112);
  a leg that runs after the state it is about measures nothing (T-84).
  Where a case depends on a window, close the window: put the state
  there by hand rather than hoping a race leaves it.
- A CLAIM ABOUT AN INTERVAL IS READ INSIDE THE INTERVAL: the drop's
  defect is the wrong picture BETWEEN release and landing, so the
  reading is taken one pump after the release and the landing is asked
  separately afterwards. And when one defect multiplies the things a
  reading could be about -- two output groups, one stale -- name the
  subject before the reading means anything.

## FIXTURES THAT CANNOT REACH THEIR OWN CASE

A harness cannot tell "the case did not arise" from "the case arose
and was fine", so every one of these read as a passing result. The
question that finds them: WHAT MUST THIS DEFECT HAVE, and can my
fixture supply it? Then assert the premise -- on the quantity the code
reads, off the thing rather than off what you handed it -- and watch it
fail before staging until it holds (T-45, T-56). The accounts are T-136.

- WHAT THE FIXTURE CANNOT SHARE OR MOVE: a memory layer cannot share a
  source string, so a source collision could not arise (T-121); a
  design on its defaults is the one the plugin would choose anyway, so
  a re-derivation is invisible; twelve values of zero multiplied by ten
  leave the maximum where it was; a `layer:` token vanishes with the
  layer it names where a `file:` token survives; a scheme staged on the
  field the default picks makes preference and coincidence
  indistinguishable; the packaged Auckland data has its nulls in the
  same six areas for every variable.
- WHAT THE PRODUCT REFUSES OR DERIVES: a setup that calls `reload()` is
  the one act that makes QGIS tell the truth about a moved file (T-55);
  a fixture that lets the plugin derive the thing under test passes
  through the live defect (T-61); one built to exploit a bug dies when
  the bug is fixed, which is the cheerful red (T-53); the design a test
  drives can refuse the case -- laves refuses the nudge archimedean
  records (T-92); a cell that cannot set its own stage says so rather
  than falling through with the previous cell's selection (T-93); build
  the fixture through the product's own door, since `catalog.make_unit`
  parses what `WeaveUnit(**spec)` cannot (T-87).
- THE CONTROL ARM: its own act can travel into the arm it controls --
  every arm picked one colour and the control's pick was saved into the
  file the second arm opened (T-5); a control that could not fail
  either is no control (T-106); a probe's control must move ONE term,
  and an instrument asks the product its own question rather than a
  second copy of its rule (T-111); two arms sharing one `QgsProject` is
  a contaminated control that reads as contention (T-90); a
  `QgsApplication` left unbound is collected on the next line and reads
  as the product crashing (T-95). An attribute that is a VIEW cannot be
  watched by rebinding it (T-3).
- THE JOURNEY THE HARNESS HOLDS: the kit's dialog switches live update
  OFF, so a probe measured a journey nobody takes and contradicted the
  person holding the failure, which is the tell; twelve resume tests
  unticked it too, and with the default a Load re-tiled the opened map
  away. Ask of any test family what it holds constant, and have one
  member drive the default and ASSERT that it is the default.
- NOTHING IN A HUNT'S REPRODUCTION IS INCIDENTAL until proven so: one
  entry took four fixtures, the last needing the opacity change the
  hunt's own journey had (T-70). A ceiling is the case, and filling
  PAST it measures the other path (T-89). Some defects need another
  PROCESS: stage what it LEAVES, since a fresh dialog does not own a
  colleague's file (T-85), and the shape of a lock decides which
  failure you meet -- a write lock fails the first feature, and only a
  shared read transaction reaches the commit.

## ASSERTIONS, ORACLES AND WHAT A READING IS

The accounts are T-137.

- ASSERT THE SENTENCE THE PRODUCT COMPOSES, never a phrase copied out
  of it: the maintainer reworded a notice and a test failed on every
  platform looking like a Windows fault (T-8); where the product now
  chooses between two sentences by mode, the filter chooses by the same
  condition. A name is pinned twice, as text and as a symbol, so grep
  for both (T-73). Aim at a drawing by asking the product, never by
  computing a point (T-101).
- A JUDGEMENT BEHIND AN `if` IS A GREEN THAT SAYS NOTHING (T-59):
  assert the premise first, watch it fail, then stage until it holds;
  read the premise off the WIDGET, since `decimals` clamps what you
  handed `setValue`; and assert what the failure you fear would change
  -- a re-seed reproduces a followed row's field and count and destroys
  only its colours. A property with an exact definition is asserted as
  that definition and not as a threshold: two consecutive prose lines
  ARE a wrapped paragraph.
- PROVE THE QUANTITY THE FAILURE MEASURES: a guard on
  `minimumSizeHint` passed four repairs that were inert on the platform
  measuring `width()` after `show()` (T-86). An oracle a never-shown
  window cannot answer, since `isVisible` is False whatever was set
  (T-83); one that reads a dependency's stored pointers reads freed
  memory (T-71); one can be green BECAUSE of the defect it will later
  catch (T-66); and a verdict is read with its oracle in one breath,
  since a control and the arithmetic behind it calling one function
  cannot disagree (T-102). Instrumentation must not be able to replace
  the verdict: a `[found]` block that can crash is evidence you will
  not have, and it reads every store a refusal can land in -- CLEARED
  before the act rather than sliced by length after it, since a
  bounded store's slice is empty at its ceiling (T-145).
- A CLAIM HAS A DIRECTION, AND A HARM NAMED BY READING IS A
  HYPOTHESIS: a reported drop ran the opposite way round when driven
  (T-120); three of nine hunt claims described the code correctly and
  cost nothing because a second mechanism answered first, and the
  honest finding is HELD REDUNDANTLY, which names what would have to
  move. A premise that fails elsewhere carries what HAPPENED, since the
  number was the whole diagnosis and the sentence did not say so
  (T-94). An invariant cannot be a fingerprint: ask whether the
  quantity is CONSERVED by the change it should see.
- A MEASUREMENT IS A MEASUREMENT ONLY UNDER ITS OWN CONDITIONS: a save
  timing that did not resolve nearly went into the source (T-6); a rate
  from too few draws was published twice in an hour (T-116); a
  prediction is an axis a wrong axis obeys faithfully -- the teardown
  abort was recorded as 4.0.0's and fired on stable (T-114); a
  correlation with your own commit is a hypothesis (T-105); one failure
  in fifteen runs was not flakiness (T-82); an estimate that stands on
  its input's shape is measured on more than one shape, since any
  single row of the four-model table would have justified a different
  answer. A uniform verdict is almost always the instrument, and can be
  the answer, which four platforms agreeing settled (T-109); when an
  instrument disagrees with a hand-run, run the tool's inner command
  yourself with nothing suppressed (T-54).
- RENDER THE GESTURE: a drawing's faults live on branches no reading
  walks and no assertion names. Drawing a drag mid-flight showed a
  ROTATE held at its limit saying "a deeper wave than this runs beyond
  the edges" -- one sentence written for every manipulation, reachable
  only when a drag passes the limit, and the same fault was still
  sitting in the refusal beside it telling somebody to ease back to a
  DEPTH. Ask of any message shared by a family which member's words it
  is in, and of any drawing what it looks like DURING the act rather
  than after it. (T-147.)
- AN INSTRUMENT IN THE USER'S HANDS BEATS SIX REPRODUCTIONS IN YOURS:
  a dump from the reporter's session answered in a minute (T-50). AN
  AUDIT READS EVERY STORE AFTER EVERY ACT: driving the Topology tab as
  a person does and printing which of twenty stores moved found three
  defects three green matrices had passed over, two of them only in
  the printed readings
  (`tools/probes/audit_the_topology_tab_as_a_person_meets_it.py`).
- A RULING THAT IS AN ORDER IS TWO CLAIMS, each with its own entry:
  "the save first, then the load" is satisfied by a deferred Load that
  never happens. Assert both answers when a rule has two, since the
  second is what catches a lazy repair -- a CRS must not move the key
  AND an inset must; a save is deferred with live update on AND
  honoured at once with it off. A prose gate is moved by prose: a
  triple-backtick fence inverts every inline span below it, so blank
  fenced blocks with spaces and never move the line numbers a failure
  quotes.

## GUARDS, ENTRIES AND THE CATALOGUE

The accounts are T-138.

- A GUARD IS NOT A GUARD UNTIL YOU HAVE WATCHED IT FAIL: two written
  the day the rule was being written down were dead on arrival (T-9);
  a test runs green under `run_some` while registered nowhere (T-14);
  a test with no catalogue entry is a test you believe (T-60); a matrix
  that passes first time has not been watched fail, and the entry over
  the save's in-place skip is what proves that matrix can go red. A
  guard's own first draft is where the next defect is -- a lookup by
  class bounds stopping at the first match (T-64).
- ONE ENTRY PER AXIS, and read which assertion fired: the catalogue
  proves a test's primary axis and cannot see the rest (T-63); a guard
  written twice cannot be killed at either half (T-62); of twenty-six
  axes two were dead and both subsumed (T-57); one in five tests
  written in haste has a dead secondary axis (T-12, T-19). Point a hunt
  at a batch of new tests, per assertion, and re-hunt the ground a fix
  and its test have just been laid on (T-17, T-18); a day hunting one's
  own new code finds most of its defects in that code (T-10).
- WHEN AN ENTRY SURVIVES, ASK IN THIS ORDER: did the mutation remove
  the behaviour at all -- anchor the whole decision, since a mutation
  that leaves the work in place is inert, and an inert mutation and a
  weak test report the same word and need opposite repairs (T-115),
  which asking GDAL what the file holds told apart; is the behaviour held
  redundantly, by a second writer your own round added or a ruling gave
  it -- break every route at once, and both answers came up the same
  night (T-74); and is the test still ARRIVING at the door -- a
  Generate that changes no geometry is a restyle and never lands
  (T-78), a conversion can edit the fixture an entry stood on (T-77),
  and a repair can close the journey its own guard drives (T-103). An
  entry that survives with the control run says which of the three was
  measured rather than a bare SURVIVED.
- A survivor can name the arm that was missing, since three exits are
  three journeys (T-118), and a guard can be aimed at a STATE without
  knowing what produces it (T-117). An anchor can be ambiguous by
  indentation alone (T-79); an entry's test name is ONE literal, since
  `ast` takes the first of a concatenation. A retired contract can go
  on passing because the absurd case fails fast (T-65); presence is not
  order (T-67); silence in a record has more than one reader (T-68).
- TEST A CONTROL BY TYPING INTO IT, NOT BY `setValue`, which clamps in
  silence (T-13); three ways to move a class boundary each shipped
  green (T-11); when a fix has been reverted once, stop fixing and
  instrument WHICH rebuild writes the record (T-16); four wrong
  hypotheses about a test preceded the product being in question, so
  bisect by disabling after one (T-58).
- GUARD THE SHAPE: a race has a shape and the shape recurs, so the
  family guard for `exists` then `remove` found a second instance
  within a minute and three probes a week later (T-81, T-99). A skip
  without a line is a cell that never existed (T-97). The switch matrix
  replaced one-axis journey tests and taught on its first run (T-47).
- A ROUND CAN PASS EVERY TEST IT WROTE AND BREAK FOUR IT DID NOT RUN
  (T-72): verify a change to a core path with the whole suite, and
  accept that the candidate is where that happens -- a dozen targeted
  tests apiece found zero of the actual breakage. And when a ruling
  NARROWS a control's range or its set of values, grep the suite for
  every premise that stages the old range before the candidate runs:
  a test set the zigzag count to 1 the night counts went even, and
  rc16's first build paid for it (T-143); rc17's first build paid
  EIGHT over eighteen repairs and a ruling, four of them the session's
  own instruments (T-145, T-146, C-338).

## WHAT THE TESTS TAUGHT ABOUT THE PRODUCT

The accounts are T-139; the rules bind in CLAUDE.md's records theme.

- A CLEANUP THAT WORKS BY SIDE EFFECT IS A CLEANUP NOBODY WROTE (T-46).
  A record is not what the user sees where a path edits widgets in
  place: clearing the record was half a fix because `_assignments`
  reads the widgets. A fix that keys on an ABSENT record enumerates
  every route to that absence, at the branch -- `old_id is None` also
  meant "opened before the data was loaded". When a repair gives one
  store a new write, enumerate every store that held the fact, since
  the file's record inherited the gap the group's write had closed
  (T-75).
- A MATRIX ASKS ABOUT RECORDS; ADD THE QUESTION ABOUT WHAT IS SEEN:
  three visual defects passed a thousand-cell crossing (T-48), and a
  guard for pixels fails three ways a guard for records does not,
  repairing the defect on its way past among them (T-49). Two records
  joined end to end have the shape of one (T-76). The ordinary act --
  close the plugin, open it again -- beats the ingenious route (T-69).
  A restore held by two writers is judged only where one does not run
  (T-108).
- A GETTER-SHAPED NAME IS NOT A GETTER; work added to a signal handler
  goes after what is already there, since an exception in a slot is
  swallowed; and a watcher records only what a person left behind, at
  rest.

## TOOLS, SCRIPTS AND RESTORES

Two jobs that MUTATE one file never run at once, and each asserts it
put the file back (T-52); a restore lives in a `finally` or a trap and
is verified by reading the file, because a timeout is one of the ways
it is skipped -- one left a deliberate no-op in shipped source.
Re-indenting a block is proved by stripping the indentation back and
requiring the original, character for character. A watcher is armed as
well as hand-run, and a pipe defeats either, since `tail` buffers to
EOF. One fix, two loops: when a fix is a filter, grep every place the
same comparison is made before believing one edit finished it. (T-140.)
And a gate that reads THIS machine's disk reports this machine: six
document lines naming three gitignored `dev/` files passed here and
reddened all six runner legs on rc16's commit, so the command gate
asks git whether a runner would have the file, with a control proving
the helper can answer, and a probe worth citing is committed under
`tools/probes/` rather than named from `dev/` (T-144.)

## Lessons, each paid for once

The section as it stood, with each lesson's account: T-142.

- WINDOWS CANNOT STAGE "THE FILE WENT AWAY WHILE THE LAYER WAS OPEN",
  so four tests skip there with the reason at the skip (T-26). A
  workaround for someone else's bug needs a canary (T-27). A tool that
  filters what it shows you can hide what you needed: `text_review.py`
  dropped every sentence opening with `{`.
- AN INVARIANT CAN DEMAND THE SOFTWARE GET IT WRONG (T-28); assert
  what must be true rather than the easiest observable nearby -- the
  plugin NOTICED a CRS change, though 500 stayed 500. A stub that
  collects nothing hides what passes through it (T-29); a fixed wait
  after a run is a guess about two races (T-30); "immediately" is one
  interleaving of many, and the dialog has two debounces (T-31); an
  invariant checked immediately cannot tell a defect from a debounce
  (T-37).
- A FIXTURE CAN MAKE A CASE VACUOUS WITHOUT FAILING -- Douglas-Peucker
  keeps every vertex of a square -- so assert that the mutation changed
  it; fingerprint the thing the user would notice, since tile count and
  extent survive a region reshaped inside its box. Tests run with an
  EMPTY project. A test that passes is not a test that works: six
  written to close gaps did not kill their mutants (T-32); count the
  call sites before believing a survivor is a gap (T-33); test a switch
  where it BITES; prefer one systematic test to many specific ones, and
  a control acts through its OWN signal (T-34).
- THE ENVIRONMENT CAN SATISFY THE THING UNDER TEST: a seeded profile
  makes a palette assertion pass whatever the installer does (T-35),
  the answer can depend on how the suite was sharded (T-36), and it can
  satisfy the thing MEASURING the test (T-38). Defaults are masked by
  what overrides them; look fixture names up rather than typing them;
  re-record the coverage record after any suite change; calibrate image
  metrics before their thresholds mean anything.
- A WAITER FIRST CHECKS THAT ANYTHING STARTED; diagnose a suspected
  hang by CPU rather than elapsed time; wholesale span rewrites of a
  test file drop assertions silently; grab widgets only after showing
  them; never run two full suites at once (T-39); no unconditional
  modal dialogs on generation paths.
- A TEST WHOSE COVERAGE DEPENDS ON THE MACHINE REPORTS THE MACHINE
  (T-40), and a reproduction is proved to reproduce -- `LC_ALL=C`
  exercised `en_US` twice, and `QLocale.setDefault` forces the thing
  itself. When an attribution is a guess, report rather than gate
  (T-41).

## Inbox: lessons not yet themed

A lesson that fits none of the themes above goes here as one clause
with its id, and this section holds six at most: past that the check
asks for them to be folded into the themes. It is empty now.
