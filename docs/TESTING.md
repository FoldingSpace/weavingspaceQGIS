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

## A red suite can mean the software got SLOWER, and reading it as a hang costs the diagnosis

2026-08-16. Every CI suite leg went red at once -- three Linux
versions and macOS -- with the same line: `STALL adversarial
sequences [no result after 600s]`, exit 2. The stacks were genuine and
pointed at real work, so the first reading was a hang in the newest
code on that path. That reading was wrong twice over, and both
corrections are worth keeping.

**The test passed in isolation, at both revisions.** 101s at HEAD, 78s
at v0.24.2, well inside the 600s ceiling. Nothing was hanging. What
had changed was CPU: 15s against 46s on the same test. Wall clock hid
it, because most of that time is the test waiting on debounces; the
project's own rule about diagnosing by CPU rather than elapsed time
applies to a SLOWDOWN exactly as it does to a stall.

**The stack names where time is SPENT, not what made it expensive.**
Profiling both revisions gave the answer the stacks could not: the
table was rebuilt 461 times at 0.24.2 and 1,282 times at HEAD, and
each rebuild redrew a ramp swatch for every ramp in the style library
for every row -- 306,558 draws, 311,613 style lookups and 2.45 million
`fillRect` calls in one test, against the 63 distinct swatches it
actually needs. The regression was a multiplier meeting an
already-expensive thing that nothing had ever cached.

Read call COUNTS rather than seconds when comparing two profiles: a
profiler's overhead swamps the totals, so the ratio of self-times
understated this threefold difference as 1.2x while the call counts
carried it exactly.

TWO TRAPS IN PROFILING THIS PROJECT AT ALL, both paid for that day.
`python -m cProfile -o file` writes NOTHING here, because the suite and
`tools/run_some.py` both end in `os._exit` and cProfile dumps at
interpreter shutdown -- the same trap that left
`tools/coverage_report.py` unable to write a report until 2026-08-13.
Write a driver that dumps the stats itself, before exiting. And a
plain `python3` invoked from a shell that has sourced the QGIS
environment inherits `PYTHONHOME` and dies on `No module named
'encodings'`; read profiles back with `env -i`.

THE FIX FOR A CEILING A HEALTHY RUN NOW REACHES IS NOT THE CEILING.
Raising 600s would have turned every leg green and hidden a threefold
cost increase on a path a user meets whenever the region layer
changes. A watchdog catches hangs; it is not a performance budget, and
that rule cuts in the inconvenient direction too.

## Assert the sentence the product composes, not a phrase copied out of it

2026-08-16, and it cost an afternoon of wrong diagnosis. A test
asserted `"no value" in said` about the missing-values notice. The
maintainer reworded that notice the same morning -- "have no value"
became "do not have finite numeric data", correctly, because the count
had widened to infinities, which are values and simply not finite
ones. The product was right; the test failed on EVERY platform.

It read as a WINDOWS fault for hours, and the reason is worth more
than the fix: Windows was the only leg anybody looked at. The macOS
leg produced 160 results and then stalled at another test without ever
reaching this one; the Linux legs' logs were never pulled, because
`gh run view --log-failed` returns nothing while a run is still in
progress and that emptiness was accepted as absence of evidence. A
platform-shaped symptom is not evidence of a platform-shaped cause,
and the way to tell is to run the test on the machine in front of you
before theorising about the one you cannot see.

The repair is general: compose the expected text from the same
function the product uses (`bridge.missing_values_message`) and assert
THAT appears. Rewording then moves the test with the product, and only
a notice that stops appearing can fail it. A phrase transcribed into a
test is a second copy of the wording with no mechanism keeping the two
in step -- which is the same fault as a derived document nobody
regenerates, in a smaller place.

Worth checking the siblings when you meet one: of five nearby
fragment assertions here, four still matched the product verbatim and
the fifth was composed at run time, so only the one had rotted. Ten
minutes to check, against another afternoon.

## A guard is not a guard until you have watched it fail

2026-08-16 produced two guards that were DEAD the moment they were
written, both by the same author on the same day the rule was being
written down, and both caught only by disabling the fix and re-running.

The first asserted that a helper returned zero when called a second
time, on an object the product had already put through it -- an
answer that could not depend on what the product did.

The second is the more instructive, because nothing about it looks
wrong. It drove two Generates at different spacings and required the
paired layer's renderer to cover every kind of absence the layer held.
Its FIXTURE gave every element all three kinds at every spacing, so
the case it was written for could not arise, and it passed with the
fix disabled. Rebuilt on a measured spacing pair -- at 1300 one
element carries two kinds, at 1100 it carries three -- it failed at
once, naming the element and the kind that would have painted nothing.

THE HABIT, and it costs a minute: after writing a guard, break the fix
and watch the guard fail. Not the behaviour it names in the abstract:
the actual line you just wrote. Both of these passed their first run,
which is exactly what made them worth suspecting -- and a fixture that
cannot exhibit the case is invisible in a green result.

**AND A GUARD THAT FAILS IS NOT YET A GUARD THAT IS RIGHT.** Later the
same day a cache test failed on its first run, saying the cache was
deaf to QGIS's style signals. The verdict was right and the premise
was wrong: it staged the library change with `addColorRamp`, and
measured on QGIS 4.0.3 that call emits NOTHING, while
`removeColorRamp` emits `rampRemoved` and `entityRemoved`. Had the
failure been taken at face value the "fix" would have been machinery
for a signal that does not exist. Probing which signals actually fire
took two minutes and turned the test into one that stages the change
through the call that emits AND asserts the silent one is harmless,
because a name never cached cannot be stale. When a new test fails,
establish that its premise is true before believing its conclusion --
the reflex to fix the product is as strong as the reflex to fix the
test, and both are wrong when the fixture is what is mistaken.

**A TEST CAN CHECK THE EXCEPTIONAL ROW AND NEVER THE ORDINARY ONE.**
The categorical editor's test asserted that the last row reads "(no
data)", that the column is the settled width, and that every row's
button carries the colour the map would use -- and never once tied an
ordinary row's LABEL to its value. So it passed while every row in
the window read "no data". Found because its catalogue entry SURVIVED
while the two beside it were caught, which is the catalogue doing the
job it exists for. When a test enumerates rows, ask whether it
asserts the thing the rows are FOR, or only the decoration around it.

## What a day of hunting one's own new code actually costs

2026-08-16, twenty-one hunts across six rounds, and the arithmetic is
worth writing down before anybody budgets another day like it.

FOURTEEN confirmed defects came out of the later rounds. ELEVEN were
in code written within the previous few hours; FIVE were inside
repairs for defects the same day's earlier hunts had found. Three
successive attempts at one fix were each withdrawn after a hunt
measured what they broke, and the third had passed a day's worth of
tests before it died.

What that means in practice, stated plainly because it is not the
usual picture of what hunting is for:

- **A hunt aimed at fresh work is part of writing the code**, not an
  audit of it. Aimed at old code the same directions returned little;
  aimed at the afternoon's work they returned defect after defect.
- **A repair is new code and deserves the same suspicion.** Five of
  fourteen were in fixes written hours earlier, including two in the
  fix for the defect a hunt had just reported.
- **The cost is not machine time, it is judgement.** Every claim has
  to be reproduced by a route the hunt did not use before it is
  believed, and that queue is the real limit on how many hunts are
  worth running at once.
- **Turning a hunt on our own TESTS pays at a steady rate.** Three
  rounds of it, on 26, 12 and 11 tests: six, two and two dead
  assertions. Roughly one test in five or six, every time, and in all
  three rounds the dead axis sat inside a test whose primary
  assertion was live and well aimed.

## Three ways to move a class boundary, and why none of them worked

2026-08-16, and the whole episode took an afternoon. It belongs in a
testing document rather than a design one because what it really
demonstrates is how a fix ships green.

THE PROBLEM IS REAL. QGIS gives a value to the FIRST range containing
it, inclusive at both ends. On a column with repeated values the
classifier returns degenerate ranges -- `1..1, 1..5, 5..5, 5..9, 9..9`
for `{1, 5, 9}` at k=5 -- and the degenerate ones above are
unreachable by construction. So the map draws its HIGHEST value in a
middle colour while the legend's darkest sits beside a range nothing
occupies, and a reader matching darkest to "high" reads it wrongly.

THREE FIXES, EACH WITHDRAWN.

*Reduce k to the number of distinct values.* Correct output, wrong
means: class i takes `ramp.color(i/(k-1))`, so a shorter ladder
re-spreads its survivors across the whole ramp. Five asked over four
distinct values drew the FOUR-class ladder exactly, and a column that
later gained a value re-coloured everything with nobody choosing
anything. Withdrawn on the maintainer's rule that an empty class is
invisible, not deleted.

*Shrink every finite-width upper bound by one ulp*, so a boundary
value falls into the degenerate range that means it. It moved the LAST
range too, whose upper bound is the column's maximum, so the largest
value belonged to no range and drew as NOTHING. Two hunts found it
independently within the hour.

*Shrink only where the next range is degenerate, by a relative margin
of 1e-9*, never the last range. This survived a day's tests and died
on two counts: a relative margin is an ABSOLUTE GAP, so at 2e12 it is
two thousand wide and a value a hundred below the bound was orphaned
and drawn as nothing; and above about 1e5 QGIS's own label formatter
PRINTS the margin, so a legend read `100,000,000,000 -
999,999,999,000`.

WHAT EACH ONE TAUGHT, and the third is the one worth carrying:

- a fix can be right about the symptom and wrong about the means, and
  the tell is what it moves that nobody asked it to move;
- a single hand-made fixture is one shape. `{1, 5, 9}` is degenerate
  at the TOP, which is the only arrangement in which the second fix's
  harm cannot appear, and it shipped green;
- MAGNITUDE IS A FIXTURE DIMENSION. Every fixture in this suite lived
  between 0 and about 50. The third fix was correct there and wrong at
  1e12 and at 1e-9, and nothing in the suite would ever have said so.
  When arithmetic depends on the size of a number, the sweep has to
  cross magnitudes, and `test_no_value_is_ever_orphaned_by_a_
  classification` now does.

WHAT SURVIVED. The reduction stayed withdrawn, because colour
stability is the property the maintainer asked for. The class bounds
are QGIS's own, untouched. The remaining wart -- a possibly empty
darkest class -- is left VISIBLE rather than cured: the swatch hatched
every class no tile wore until 2026-08-17, and since the maintainer
ruled that mark out it is `empty_classes_message` that says so, in
words, counted by `unworn_classes` from the ladder the map draws.
That attribution read `few_values_message` for a day and was wrong:
the reasoning is at `bridge.unworn_classes` and in CLAUDE.md. And the orphan sweep is kept as a permanent
invariant, since it caught two of the three attempts and is about any
classification rather than about any one of them.

## Four ways a test passed while the product was broken, 2026-08-16

A second round of the same measurement, on twelve tests written that
day, mutated PER ASSERTION: 28 mutants, ten tests killed everything,
two did not. One in six, near this project's standing one in five.
Both dead axes were in tests whose PRIMARY axis was live, which is now
the reliable finding — a test is not one assertion, and the first one
being well aimed says nothing about the rest.

The four shapes, three of which were new that day:

**A SECOND CALL TO A HELPER THE PRODUCT HAS ALREADY APPLIED cannot
see what the product did with it.** The bound-moving helper described
above (since withdrawn) was scoped to ladders holding a degenerate
range; the test asserted that calling it again returned zero. After the product's own call nothing
is degenerate, so it returns zero whatever happened. The scope was
then genuinely broken — every boundary value moved up a class on
ordinary data — and the test passed. Ask the MAP, not the helper.

**AN EXPECTATION READ BACK OFF THE OBJECT UNDER TEST MOVES WITH THE
BUG.** The repair for the above first read the class boundaries from
the renderer and checked each one's colour. Under a mutant that MOVES
those boundaries they matched no data value, the loop skipped every
case, and it passed again. Expectations come from the fixture and the
scheme, never from the thing being measured.

**A CLAIM THAT A NOTICE FIRES CANNOT BE TESTED BY SILENCE.** A test
whose subject is a warning was rewritten that morning to repair an
earlier dead axis, and the repair drove the dialog on a CLEAN fixture
and asserted nothing was said. Deleting the notice from the plugin
outright — the exact mutation named in its own docstring — still
passed. Every negative case needs its positive twin, driven until the
sentence appears.

**A SINGLE HAND-MADE FIXTURE IS ONE SHAPE, AND THE HARM LIVES IN THE
OTHERS.** That helper shipped green against `{1, 5, 9}`, whose top range
is degenerate — the one arrangement in which its defect cannot appear.
It was deleting the column's maximum from real maps, found within the
hour by two hunts independently. When a fix ships with one fixture,
vary the fixture BEFORE trusting the green: the replacement sweeps
five value sets across four schemes at three class counts and asserts
the combination count actually ran.

## TEST A CONTROL BY TYPING INTO IT, NOT BY `setValue`

2026-08-17, four defects in one day, every one of them a control
silently refusing what a person typed and every one invisible to the
test that guarded it.

`setValue` CLAMPS IN SILENCE. It never consults the validator, so it
cannot see a range that refuses a keystroke, a `decimals` too low to
hold the number, or a `valueChanged` handler rewriting the box while
somebody is still typing. All four guards drove `setValue` or
`stepBy`, all four passed throughout, and one docstring said in as
many words "dragging or stepping" -- so typing was never in view.

**HOW.** Walk the string character by character through the widget's
own `validate`, and require the whole of it to survive:

    kept = ""
    for character in typed:
      trial = kept + character
      state, _fixed, _pos = box.validate(trial, len(trial))
      if state in (QValidator.State.Acceptable,
                   QValidator.State.Intermediate):
        kept = trial
    assert kept == typed

Where a handler may rewrite the box mid-edit, that is not enough --
`validate` does not run the handler. Use `QTest.keyClicks` on the
line edit and a `Key_Return`, which is what a person does.

**AND ASSERT THE NUMBER THE MAP IS BUILT FROM**, not the number in the
box. The scale defect was found by reading tile centroids: the box and
the map can agree with each other and both be wrong about what was
typed.

**THE FAMILY IS WORTH ONE TABLE TEST.** `test_every_number_box_holds_
a_value_finer_than_its_step` walks every `QDoubleSpinBox` the dialog
owns, so a control added next year is covered by somebody adding a
widget rather than by somebody remembering. Its first draft demanded a
value one order finer than each box's step -- STRICTER THAN THE
MAINTAINER'S RULING of three decimal places -- and failed on a step of
0.083. A test inventing a contract nobody agreed is the same fault as
a test written around a defect, from the other side.

## A test can pass while registered nowhere

2026-08-18, writing the last of thirteen owed guards. `tools/run_some.py`
finds a test by FUNCTION NAME, walking the module rather than the
registration list, so a test runs perfectly well without ever being
handed to `check()`. The guard for the reversed-ramp defect ran green
that way while the edit meant to register it had silently missed its
anchor.

A guard that no suite run executes is the quietest way for one to be
worth nothing: it passes when you ask it directly, it appears in the
file, and it is absent from every release. Nothing in the local loop
would have said so -- `docs/TEST-MAP.md` is generated from the
registrations, so it would simply not have listed it, and nobody reads
a map to notice an absence.

TWO HABITS, both cheap. When you add a test, assert the registration
edit landed rather than assuming it -- a `replace` that matches
nothing is silent, and every insert in this session's tooling asserts
its own anchor for exactly that reason. And after adding a batch,
compare the count of `def test_` against the count of `check(` before
believing the batch is in.

## Where a guard's expectation should come from, when the product is the
## only thing that knows the answer

Thirteen guards were written in one sitting on 2026-08-18, and the
recurring difficulty was not what to assert but WHERE THE EXPECTED
VALUE MAY COME FROM. Three answers earned their place, in descending
preference.

**From the fixture and the settings**, which is the standing rule.
A pin of 6e-10 typed into a box must read back as 6e-10; a copied
ladder's interior breaks must still be in the record. Nothing is asked
of the code under test.

**From a PROPERTY of the domain that holds whatever the code
believes.** The reversed-ramp guard needed to know which way round a
ladder runs, and every function that could tell it is downstream of
the defect. A sequential ramp runs light to dark, so a forward ladder
has its palest class FIRST -- read off the rendered colours, true
whatever the plugin thinks, and usable as an oracle precisely because
the plugin has no say in it.

**From a second implementation the defect does not touch.** The design
view's guard compares the preview against what the element's own
RENDERER paints, built by `make_graduated_renderer` -- a different
path from the one under test, so a disagreement is a defect by
construction. Where the fix and the comparison share code, as the
deferring arm did, that arm must fall back to the fixture's own
colour instead.

AND WHERE NONE OF THE THREE IS AVAILABLE, SAY SO RATHER THAN
INVENTING ONE. The ledger carries a single row marked `prose` for a
sentence about which controls a row shows: a test asserting the
guide's wording would pin the WORDS rather than the truth, and would
fail the next time somebody rewrote the sentence correctly. What
guards it is the prose hunt that found it. An honest gap in a record
is worth more than a guard that measures nothing.

## Instrument WHICH rebuild writes the record, and the fourth attempt lands

The opacity defect of 2026-08-13 took four attempts across two
sessions, and the difference at the end was not cleverness. Three
attempts reasoned about where a stale value came from -- a flag read
in `_refresh_table`, a table cleared on project change, cell widgets
removed -- and each was reverted, one after running ten minutes
without reaching the case.

The fourth began by adding three dumps behind
`WEAVINGSPACE_ADOPT_DUMP`, in the clear, the rebuild and the adoption,
and running the real thing. One run printed the whole sequence:

    FORGET the last project
    PREV  a: table=100 dialog=<none>
    ADOPT a: layer=40 dialog=100

The clear WORKS. The table survives it, refills the records from the
outgoing project's cell widgets, and adoption then finds the user's
value and declines it. No amount of reading would have ordered those
three correctly, because the middle one is a rebuild nobody had
thought to suspect.

THE DUMPS ARE COMMITTED, behind the flag, and that is deliberate: the
instrument that names one defect is the instrument that names the
next, and this is the second time this project has recorded that
lesson (the first was `WEAVINGSPACE_SWEEP_DUMP`, two minutes to write
after a day of reconstructions). WHEN A FIX HAS BEEN REVERTED ONCE,
STOP FIXING AND START MEASURING.

## THE SECOND TRIGGER: when a fix AND its test are in, hunt that ground again

Stated as a step for the same reason as the one below it: the practice
was demonstrated on 2026-08-17 and would otherwise have stayed an
anecdote.

**WHEN.** A defect has been fixed, its regression test written, and its
catalogue entry proved. That is the moment the ground it sits on is
most worth re-hunting -- not the fix itself, which now has a guard, but
its NEIGHBOURHOOD.

**WHY, measured.** On 2026-08-17 nine defects were fixed in an
afternoon. Four were in code written that same afternoon, and THREE OF
THOSE FOUR WERE INSIDE FIXES for defects the earlier hunts had just
found. A repair is new code and deserves the same suspicion as any
other: five of fourteen defects on 2026-08-16 were in fixes written
hours earlier, including two in the fix for the defect a hunt had just
reported.

The other four that day were OLDER -- 10 August, 15 August, and two
from that morning -- and every one surfaced because a hunt was pointed
at the new work sitting beside them. Aimed at old code alone the same
directions had returned little; aimed next to fresh work they returned
defect after defect.

**HOW, and the aiming is the whole of it.** Relaunch NEAR the fix, not
ON it:

- name the fixed defect in the brief and forbid re-reporting it, so
  the hunt spends its budget on new ground;
- keep the SHAPE and move the AREA, or keep the area and change the
  shape -- the same shape in the same place finds the same thing;
- ask what the fix itself might have broken. Two of 2026-08-17's
  briefs carried an explicit check on the repair -- does the follow now
  stamp twice, does the new decimals floor harm a finer control -- and
  that is a question only somebody who knows the fix can ask;
- give each hunt an explicit list of what its siblings cover, and tell
  it to spend one line on an overlap rather than a report. Without
  that, several hunts converge on the loudest defect and the round
  returns one finding wearing six costumes.

**WHEN TO STOP.** When a round returns nothing new twice over, or when
the queue of claims waiting to be reproduced is longer than the day.
The cost of hunting is not machine time; it is the judgement needed to
reproduce every claim by a route the hunt did not use before believing
it.

## THE TRIGGER: point a hunt at a BATCH of new tests, per assertion

Everything below this heading was already known and written down. What
was missing was the moment at which somebody does it, so it read as a
good idea and got skipped exactly when it was most needed -- which is
what happened on 2026-08-17. This is that moment, stated as a step.

**WHEN.** A batch of tests written in one sitting, especially alongside
the fixes they guard. Three or more is a batch. The trigger fires on
the SITTING, not on any one test.

**WHAT IT IS NOT.** It is not a hunt per test, and it does not replace
the mutation catalogue. Every test still gets its catalogue entry, and
the entry is cheaper, faster and more reliable at the job it does:
proving the test fails when the behaviour it names is broken. Every
entry written on 2026-08-17 came back `caught`, and the catalogue took
about a minute each.

**WHAT THE CATALOGUE STRUCTURALLY CANNOT SEE**, which is the whole
reason this exists. An entry breaks ONE behaviour; the test's primary
assertion kills it; the entry reports `caught`. The second and third
assertions in that test are never exercised. Measured here three times
at roughly ONE IN FIVE OR SIX, and in all three rounds the dead axis
sat inside a test whose primary axis was live and well aimed.
2026-08-17 produced another: a pin test carried a passing catalogue
entry AND survived deleting the whole cell-rewrite loop it was written
to guard, because its helper read the spin boxes as well as the cells.

**HOW.** Mutate PER ASSERTION rather than per test. For each assertion
in the batch, break the narrowest thing it names and require that
assertion to fail. What it finds is a DEAD AXIS, and the repair is
usually an assertion that states its own premise or counts what it
actually compared -- `assert matched, "nothing was compared"` before
`assert not mismatches`.

**THE FINDINGS NEED A HUNT'S DISCIPLINE, because an adversarial reader
errs in both directions.** On 2026-08-17 a new guard demanded that
every number box hold a value one order finer than its own step. That
is STRICTER THAN THE MAINTAINER'S RULING of three decimal places, and
it failed on a modifier box whose step is 0.083. A test inventing a
contract nobody agreed is the same fault as a test written around a
defect, arriving from the opposite side, and the tell is identical: an
assertion failing on code nobody thinks is wrong. So reproduce by a
route the hunt did not use, and check the contract being asserted is
one somebody actually decided.

**WHAT IT IS WORTH, honestly.** Test-hunting protects the suite;
product-hunting protects the user. On 2026-08-17 nine product defects
came out of hunts aimed at behaviour and none from anything aimed at
tests. When there is only room for one, aim at the product. This
trigger is for the case where a batch of tests has just been written
fast and is about to be trusted.

## Tests written in haste, measured

2026-08-16. Fourteen tests were written in one day alongside the fixes
they guard, and a hunt afterwards mutated the behaviour each one names
to see whether it would notice. Eleven killed everything aimed at
them. THREE HAD DEAD SECONDARY AXES, which is about one in five and
matches this project's historical rate:

- a tile-count check that compared a sum WITH ITSELF -- twice. The
  first version was literal; the second compared `featureCount()`
  against the same two layers iterated, which a split that DROPS rows
  passes happily. It counts against an independent sibling now.
- `assert dlg._element_layer_ids[tid] == dlg._element_layer_ids[tid]`,
  a value read twice from one dict, which no mutation can disturb.
- a colour check that passed while the RECORD went from one
  hand-picked colour to four: the map was pixel-identical and the row
  silently stopped following the ramp it still named.

Two of the three were in tests whose PRIMARY axis was live and
well-aimed, which is the point worth keeping: a test is not one
assertion but several, and a live first assertion says nothing about
the ones after it. When a batch of tests is written quickly, point a
hunt at the tests rather than the product.

The same day produced three more fixture faults worth recognising on
sight: a layer never added to the project, so every element came back
unassigned; two chooser picks made back to back, which is the race
among choosers and loses both; and a fixture whose elements all sat on
an axis, where a half turn and a single mirror are indistinguishable.
Each was caught by an assertion that stated its own premise, which is
the cheapest guard there is.

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

## What has actually found defects here, and what has not

Worth stating before the shapes, because it decides where effort
should go. Counted over this project's life, nearly every real defect
came from a DIFFERENTIAL instrument -- two independent descriptions of
the same thing, compared, so that a disagreement is a defect by
construction and no oracle is needed.

The record: the docstring audit found TWO product defects in a
session with no machine time, by reading documentation against code.
The first Linux run found a defect invisible on any Mac, ramp names
colliding by case. `install_and_load` found a fault the first time
anything opened the artefact a user actually receives.
UI-against-library caught three bugs every "a map appeared" assertion
had walked past. The colourspace comparison against upstream's own
renderer caught a categorical sampling error where a plausible
derivation used `round()` for `int()`. Each is code against code,
machine against machine, prose against behaviour, or our render
against somebody else's.

Mutation testing is not on that list, and should not be expected on
it. It asks "would the suite have noticed?", which is a question about
the TESTS. It is worth running for exactly that -- a catalogue sweep
returning 173 caught and 1 accepted is real assurance that old tests
still reach what they name -- but a campaign of 128 survivors yielded one product
defect, and the sample did not find it; a differential probe did. Do
not budget mutation triage as defect-hunting. Budget it as suite
measurement, and spend the creative effort on new differentials.

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
as correct behaviour.** Three were found this way on 2026-08-13, all
in one evening, and none of them looked wrong. One asserted
`distinct >= k` before measuring, so the case where a column has fewer
values than classes was excluded by the test that would otherwise have
caught it. One switched from Quantiles to Equal intervals with a
comment explaining that four values cannot exhibit nine classes -- and
then asserted the nine ranges it got, five of which painted nothing.
The third set the mode to Categorized on a row that was ALREADY
Categorized, so the style flip it described never happened, and what
it actually asserted was that a ramp picked on a categorized row gets
thrown away: the defect, pinned as the contract.

The tell in all three is a workaround inside the test, written by
somebody who met the awkward behaviour, decided it was the fixture's
fault, and routed around it. So when a test contains an accommodation
-- a guard, a scheme swapped for another, a fixture narrowed to avoid
a case -- read the accommodation as a REPORT. It is somebody's note
that the software did something they did not expect. Ask whether they
were right that it was the fixture.

**A fix can be RIGHT and still be wrong to ship, and the blast radius
is the evidence.** On 2026-08-13 a real defect was fixed correctly --
a graduated renderer drawing more classes than the column has distinct
values, so swatches appear in the legend that no tile uses -- by the
same reduction upstream applies. Nineteen tests moved. That number was
the finding, not the inconvenience: the standard fixture gives four
distinct values and the suite's graduated tests ask for five, so the
whole suite sat on that boundary, and one of the nineteen said why in
as many words. `test_metamorphic_variable_permutation` requires that
"b must class exactly as a did", and an element LAYER holds only that
element's tiles -- so the reduction made the class count depend on
which tiles an element happened to receive, and two elements carrying
the same variable could draw different numbers of classes. On a map
whose purpose is reading elements against each other, that is a worse
fault than the one being fixed.

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
a test that passes for a reason nobody chose.** The reduction above was
put back on 2026-08-14, and putting it back exposed something older and
worse: class breaks were cut from each ELEMENT layer, which holds only
that element's tiles, so four elements carrying one variable drew four
different legends and one colour meant four different numbers. That had
been shipping. It survived every differential this project has because
the standard fixture asks for five classes over a column with four
distinct values -- and more classes than values collapses quantile
breaks onto the values themselves, which makes the elements agree
whatever the code does. `test_metamorphic_variable_permutation` was
passing on that accident, not on the behaviour it names.

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
its own sibling.** Three more defects came out on 2026-08-13, all
found by reading one code path beside the twin that does the same job
for the other styling mode, and asking what one does that the other
does not. A class colour picked during a run was destroyed when the
run landed, because the landing path re-read the categorical picks
and not the graduated ones. QGIS's own Classify over a
constant column raised IndexError inside a renderer signal handler,
because the categorized branch guards a case its graduated twin
walks straight into. A Reverse tick was discarded by any rebuild
happening while the switch was greyed, because one part of the
dialog preserved the record and another restored it from a report
that had never been about the record.

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
imagined. As of the first map: 145 tests, 35 guarding a real
defect. Those two numbers are the figures on the day the map
was first generated and are left as history; the CURRENT ones
are at the top of docs/TEST-MAP.md and docs/BUG-REGISTER.md,
which are regenerated at every release. A count written into
prose is true until somebody adds one.

Two things the map is deliberately NOT. It is not a coverage report —
`tools/coverage_report.py` says which lines ran. And it is not an
argument for splitting the file: coverage of intent is not the same
shape as file boundaries, and moving 500-odd functions risks silently
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

## Wait on the EVENT, not on a number of seconds

The third ceiling sized from this machine, 2026-08-16, and the fix
generalises past ceilings altogether.

`test_ui_affordances_are_deliberate` sampled the progress bar for
`10 * CONTENTION` seconds waiting for it to name its phase. CONTENTION
was then `2.5 if SHARD_COUNT > 1 else 1.0` -- it knew about SHARDING
and nothing about the PLATFORM, and CI runs the suite unsharded. So
that was a flat ten seconds on runners where neighbouring tests take
250.
Windows saw the bare `%p%` after 18.7s and failed; macOS finished the
whole test in 9.0s and passed. Same code, same assertion, two verdicts
decided by nothing but the machine.

Widening the constant would have been the obvious repair and the wrong
one, because no constant is right for both. THE PHASE TEXT IS SET FROM
THE FIRST PROGRESS REPORT, which the worker sends before any heavy
work, so the question "has it appeared yet" is only meaningful WHILE
THE RUN IS STILL GOING. Waiting on the task ending instead is faster
on a quick machine (it breaks the moment the text appears), patient on
a slow one, and STRICTER: a run that finishes having never named a
phase is a real failure rather than an expired clock. The absolute cap
that remains is a hang-catcher, sized well above the slowest figure
ever measured, and the failure message now says which of the two
happened.

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

**WINDOWS CANNOT STAGE "THE FILE WENT AWAY WHILE THE LAYER WAS OPEN",
and four tests here need exactly that.** The OGR provider holds a
GeoPackage open, and Windows refuses to delete or rename a file
another handle has, so the state those tests are about does not exist
there: the deleted-file case in `test_qgis_changes_around_the_plugin`,
the `test_qgis_still_calls_a_dead_layer_valid` canary, the third act
of `test_a_project_whose_region_layer_has_moved`, and the folder move
in `test_a_project_and_its_geopackage_move_together` -- the last of
which IS reachable, because clearing the project first releases the
handles, given a retry while Windows gets round to closing them.

Releasing the provider first is not a workaround: it destroys the
layer object these tests are about. So the first three announce
themselves through `_skip_loudly` and go on running on macOS and
Linux, where the premise is stageable.

Two things to keep straight when you meet the next one. A partial
skip must say WHICH PART went missing -- the moved-region test asserts
two whole acts before the one Windows cannot reach, and reporting it
as a skipped test would understate what ran. And this is a limit of
the PLATFORM, not of QGIS: the plugin's behaviour when a file
disappears is still tested, twice, on the machines that can produce
the situation. (Measured 2026-08-15, the first day the suite ran on
Windows at all.)

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
that test to fail.

Nothing runs the whole catalogue automatically, and this sentence used
to say the release did. It does not, deliberately -- the tool rewrites
source files, so it has no business inside a release -- and the claim
survived here for weeks because a rule that asserts its own
enforcement is believed and therefore never checked. What actually
happens: `--only <name>` proves each new entry as it is written, and
the whole catalogue is swept before a substantial release, sharded,
usually on GitHub (`tools/mutation_catalogue_sweep.py`,
docs/MUTATION-LOOP.md). Corrected 2026-08-13.

**Before believing a survivor is a gap, count the call sites.**
Deleting one of several redundant calls leaves the others to do the
work, so no test can discriminate and none should be contorted into
trying. `_update_layer_exclusions()` is called from THREE places -- the
constructor, project adoption, and after every run: deleting the constructor's call is invisible to
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

**AND WHERE IT DOES, THE TEST'S ANSWER CAN DEPEND ON HOW THE SUITE WAS
SHARDED.** 2026-08-17: `test_qml_class_template` names the ramp
"tab10" and never installed it, where its sibling three lines up does.
On this machine the profile was seeded years ago, so it passed; on the
mutation workflow's Linux container `get_ramp("tab10")` answered None
and the renderer builder raised. The part worth keeping is what sat
underneath: whether the ramp existed at all turned on whether some
EARLIER test in the same shard had installed the palettes, so the same
test could pass in one shard and fail in another with nothing about
the code changed. A test that needs a condition states it -- and when
a test depends on state some other test creates, sharding is what
turns that dependency from invisible into intermittent.

**AN INVARIANT CHECKED IMMEDIATELY CANNOT TELL A DEFECT FROM A
DEBOUNCE.** The same day, a stochastic hunt's top claim -- a row
saying Graduated over a categorized renderer, on seven independent
seeds -- did not reproduce on any of seven deliberate routes once each
was allowed to settle. This dialog debounces at 350 ms and 900 ms and
draws with the settings a run was LAUNCHED with, so between a style
change and the queued rerun landing the table and the map genuinely
disagree, correctly. Any invariant swept over random actions must wait
on the EVENT rather than checking on the spot, or it reports correct
behaviour on seed after seed and the seed count reads as evidence.
Full judgement in `docs/process/hunt-stochastic-2026-08-17.md`.

**And it can satisfy the thing MEASURING the test, which is worse.**
2026-08-15 produced three faults in one evening that this machine is
constitutionally unable to show, all masked by the same seeded
profile. `QGIS_PREFIX_PATH` had been wrong for months, so QGIS could
not find its own style database and started with NO RAMPS AT ALL --
invisible here, because the profile already held 63. Eight palettes
were dropped as duplicates of ramps a fresh QGIS does not have --
invisible for the same reason. And the colourspace gate had been
certifying colour fidelity against a library the plugin itself seeded
years earlier.

The technique that finds this class of fault is worth copying, and it
is cheap: **make the measurement somewhere nobody has been.** When
`tools/macos_qgis_env.sh` decides which prefix is right, it asks QGIS
how many ramps it can see with `QGIS_CUSTOM_CONFIG_PATH` pointed at a
throwaway directory. Asked with the developer's own profile, every
candidate answers "ramps present" and the measurement proves nothing
whatever -- it would have confirmed the wrong prefix as confidently as
the right one.

So when a check reads state that a person's machine accumulates --
a profile, a cache, a style library, a config directory, a login
session -- ask what it would say on a machine that has never run this
software. If the answer is "the same thing", the check is measuring
the developer rather than the software, and the way to fix it is a
fresh state rather than a stronger assertion.

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

**A test whose coverage depends on the machine it runs on reports the
machine, not the code.** The size guard's printed-spacing block read
the ambient `QLocale`, so the development Mac proved `en_US` and
nothing else. A container with no `LANG` gets Qt's C locale, which
returns `,` from `groupSeparator()` while carrying
`OmitGroupSeparator` — so `1500` there against `1,500` here, and the
suite failed on CI against correct code. The block now runs under the
ambient locale, `QLocale.c()` and German in turn, and removing the
one-line fix fails on the Mac rather than only on a runner. Ask of any
test that reads an ambient setting — locale, timezone, encoding, DPI —
which values it actually exercises, and name them.

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
since those commands name no `.py` file and so never displace the
owner. Bounded to twelve lines it produced one, also false: a
paragraph naming `ci_provision.py` to say it is NOT run, and a
`--check` seven lines later belonging to another script. The same-line
half still gates, because a flag quoted beside its own script needs no
guessing. A gate whose failures are mostly false is one people learn
to silence, and it takes the true failures with it.

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
high-dimensionally.

**THE SPACE IS FREE; ONLY THE SPINE AND THE SAMPLE COST.** Twelve
routes, nine shapes, three aftermaths and three schemes is a crossing
of nearly a thousand cells, and it runs in about two minutes, because
the spine is bounded deliberately and everything else is drawn under a
printed seed. Adding an axis multiplies the CROSSING and not the
runtime. This is the argument for reaching for a new axis rather than
economising on one: a magnitude axis added that day found a defect
that had been unreachable for weeks.

**PIN CELLS, NOT SHAPES.** The rule is that a cell which has ever
failed is tested forever. Promoting its whole SHAPE to the spine cost
twelve routes times two aftermaths -- twenty-four cells to pin what
was really four -- and took the test from 58 seconds to 169, making it
the most expensive in the suite. Four named cells took it back to 136.
A rule about cells, applied to shapes, buys redundancy rather than
coverage.

**COUNT THE SKIPS, AND ASSERT THEM.** A skipped cell reads exactly
like a passing one, and a route skipped in EVERY cell it was drawn for
is an axis that never ran -- which this project shipped once already,
in a hunt whose GeoPackage invariant executed zero times while the run
looked complete. Assert that no route was skipped everywhere, and that
most cells actually staged something.

**KEEP THE TALLY OF THE HARNESS'S OWN FAILURES.** Four in one day
here, each recorded at the line that fixes it: a floor contradicting
the ladder about to be typed; a paste expectation blind to Unclassed,
which is exempt from the distinct-value reduction; the same
expectation blind to a style pasted MID-RUN being preserved rather
than re-seeded; and a limit assertion blind to limits being INCLUSIVE,
so a tied column whose bottom class is all exactly the floor excludes
nothing and rightly does not move. A grid whose failures are mostly
its own is one nobody acts on.

**DRAW SAMPLES IN SEQUENCE, NOT IN A BATCH.** (Maintainer's
correction, 2026-08-19.) After a fix, one draw; only if it is clean do
you draw again; two clean in a row certifies. Launching two at once is
not the same evidence -- a failure in the first has to RESET the
count, and it cannot if the second was already running. Any change to
the code or the harness resets it too.

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
EVIDENCE OF ABSENCE. Write to a FILE, and prove the file gets written
in a case you know reaches the code.

**A PLAIN `python3` HEREDOC RUN AFTER SOURCING THE QGIS ENVIRONMENT
DIES AT BOOTSTRAP AND APPLIES NO EDIT.** `PYTHONHOME` points the
system interpreter at QGIS's framework and it fails with
`ModuleNotFoundError: No module named 'encodings'`. The test then runs
the UNMODIFIED file and its result is fiction. Two bisect results were
read as measurements before this was noticed. Use
`env -u PYTHONHOME -u PYTHONPATH python3` for edits, or edit before
sourcing. The same trap kills `release.py` and `mutation_check.py`.

**AN ANCHOR THAT MATCHES TWICE APPLIES NOTHING.** The categorized and
graduated handlers share identical text, and an edit anchored on the
shared phrase asserted, failed, and left the file untouched while the
run that followed reported a result. Assert the match count, and parse
the file after every edit before running anything.

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
written. This project already knows that background work locks the
tree, and that rule was written about a READER meeting a writer: a
suite or a sweep reading source while somebody edits it, which spoiled
two measurements in one night. It is also about two WRITERS meeting
each other, and that is worse, because both look like they worked.

The shape here: a "prove it red" run and a per-assertion hunt each
copy `dialog.py`, mutate it, run, and copy the file back. Launched
together, the hunt took the OTHER job's already-mutated file as its
"intact" copy, ran three probes against a tree neither of them meant,
restored the mutation, and reported three verdicts in the usual
format. Only its own `git diff --quiet` check, which said RESTORE
FAILED, said anything was wrong.

Two habits. Run mutating jobs SEQUENTIALLY, in one chain, however
tempting the parallelism -- they are measurements beside measurements,
which this project already forbids for census and suite. And have
every such job assert its restoration, because that assertion is the
only thing that distinguishes a collision from a clean run: the
verdicts themselves are perfectly well-formed either way.

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
bounding box, and its own comment says why: the over-estimate that
shape provoked was "exactly what makes the boundary affordable". When
the guard stopped measuring a circle round the box, the estimate fell
about tenfold, the boundary moved some three times finer, and the
"ordinary" map the test draws at eight times the boundary became fine
enough that tiles arrive near pixel-size. The gamut check sampled
mostly antialiased blends and reported dE 25.6 against ramps the map
was drawing perfectly.

**DO NOT DERIVE A VIEWING PARAMETER FROM A REFUSAL BOUNDARY.** That is
the transferable part. A spacing chosen to be legible and a spacing
chosen to sit on a cap are answers to unrelated questions, and tying
one to the other made a VISUAL check hostage to an ARITHMETIC change
somewhere else entirely. The repair takes the viewing spacing from the
dialog's own auto-fit -- legible by construction, and what a user
meets on opening the layer -- and asserts it is coarser than the
boundary, so "well inside the cap" cannot pass by accident.

The general question to ask of any fixture: **what is it exploiting?**
Where the answer is a behaviour somebody might one day improve, say so
at the fixture, so the next person meets an explanation rather than a
mystery.

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
on a quiet machine.

THREE EXPLANATIONS WERE TRIED AND TWO WERE COMFORTABLE. Contention, ruled
out by running it with nothing else on the machine. The disk, at 99%
with 589 MB of abandoned sandbox copies, which died on its own
arithmetic against a 926 GiB volume and changed nothing when cleared.
The sandbox itself, ruled out by BUILDING ONE BY HAND and running the
same test in it with the watchdog and its `--quiet` removed: 2.4
seconds, passed.

WHAT WAS LEFT WAS THE INTERPRETER, and it had been in plain sight:
the tool launched tests with `sys.executable`, which under this
project's own required invocation is the system python3, which has no
QGIS. Every test died at its first import and every entry read
`caught`.

THE HABIT, and it is cheap: when a tool and a hand-run disagree, RUN
THE TOOL'S INNER COMMAND YOURSELF with nothing suppressed. Every layer
that hides output -- a `--quiet`, a watchdog, a captured subprocess --
is a layer between you and the answer, and the diagnosis took four
attempts only because each theory was about something more interesting
than the command line actually being executed.

AND THE COROLLARY FOR ANY HARNESS YOU WRITE: ask what it reports when
the thing it drives cannot start. If that is indistinguishable from
success, it can only confirm, and a check that can only confirm is not
a check.
