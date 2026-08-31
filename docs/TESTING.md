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

## A PROBE HAS A KIT NOW, AND ITS TRAPS ARE IN IT

2026-08-28. `tools/probe_kit.py` is the forty lines every probe was
re-typing -- QGIS up, an empty project, a dialog, a held temporary
directory, the modal shim, both message stores, a sqlite reader that
does not hold the file open.

IT IS A CORRECTNESS TOOL RATHER THAN A CONVENIENCE, and the numbers
are why. An audit on 2026-08-15 counted 373 one-shot probe scripts in
one session, median 79 lines, roughly forty of them the same setup --
and eleven hand-written wrappers all setting `QGIS_PREFIX_PATH` to a
doubled path, so those hunts probed a QGIS with no colour ramps and
none of them knew. A shared harness is wrong once instead of eleven
times. The round of 2026-08-28 then produced four more of the same
kind in one evening, every one of them mine and every one already
written down somewhere in this file: a modal shim never installed, so
a probe hung offscreen on a real QMessageBox; a message store read
after the helper that blanks it; a `_temp_dir()` context manager
garbage-collected out from under an open GeoPackage; and a fixture
that cleared the very record its control arm depended on, forcing the
defect into both arms.

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
different property of the same widget stack.

The maintainer reported that every control on the Design tab ran the
width of the window. Two binding documents named the cause: a
QFormLayout stretches its field column. Measured on both trees in one
run, under the harness this project actually uses, EVERY CONTROL
ALREADY SAT AT ITS OWN HINT BEFORE THE REPAIR -- nothing stretched,
and the first guard written for the fix passed on the unrepaired code.

**WHETHER A FIELD COLUMN STRETCHES IS DECIDED BY THE STYLE.** The
macOS style's default `fieldGrowthPolicy` is `FieldsStayAtSizeHint`;
Fusion's is `AllNonFixedFieldsGrow`. A bare QApplication in the suite
takes the macOS style on this machine; QGIS ships Fusion as a style
people select. Under Fusion the same tree drew a strand width between
0.083 and 1.0 at 1013px against a hint of 63.

So the report was real, the cause was real, and the harness could see
none of it. THE GUARD SETS THE STYLE NOW, restoring it in a `finally`,
which is the same move as setting a font to reach a column
measurement: ask what the other machine has more of, and set that
quantity directly.

TWO THINGS TO CARRY. **Ask what a harness supplies that a user does
not** -- this project already knows the answer for `QT_QPA_PLATFORM`
and for the font, and the STYLE is a third with the same shape and its
own defaults. And **a stated cause that nobody measured reads exactly
like a measured one**: the sentence had reached ROADMAP.md and
MAINTAINING.md and was repeated into code comments before anything
checked it, which is this project's own rule about a site named by
reading, arriving at a CAUSE instead of a location.

AND THE FIRST READING WAS TAKEN TOO EARLY, which is what made the
wrong cause look confirmed. A single `processEvents()` after `show()`
reported the region chooser at 861px with a hint of 33; pumped
properly it reads 53 and 53. `sizeHint` is stale before a real layout
pass, and so is `width()` -- so a width read one event after showing
is a measurement of a half-assembled window.

## A GUARD CAN CHECK WHAT A COLUMN NEEDS AND NOT WHAT A WINDOW DOES

2026-08-29, and it is the sharpest thing about measuring a layout
here. Every runner and every CI job sets `QT_QPA_PLATFORM=offscreen`,
which supplies Sans Serif at 9pt; a desktop supplies the system font
at 13pt. The obvious repair for a guard that measures the wrong font
is to SET the font -- and it half works, which is worse than not
working at all.

`QApplication.setFont` reproduces the metrics a WIDGET asks for:
`sizeHintForColumn` moves, the header hints move, and a column's own
requirement can be checked anywhere. It does NOT reproduce the window
assembly: the dialog's minimum size hint reads 1279px at both 9pt and
13pt, offscreen printing "does not support propagateSizeHints", while
cocoa gives 1334. So half the layout rule is checkable everywhere and
the other half is checkable nowhere any runner can go.

**SAY WHICH HALF A GUARD HOLDS, AT THE GUARD.** The window's ceiling
now rests on a measurement written at the constant rather than on a
check, and the test says that in as many words -- because a layout
test that asserts three properties and can only see two reads as
though it saw three.

AND THE FIGURE I QUOTED CAME FROM THE HARNESS FONT. The same day I
offered "the Colour ramp cell is 172px for a 64px swatch and a name"
as evidence of slack. At 9pt it has 8px spare; at 13pt it is 10px
short, and the table as a whole is 149px short rather than 22px over.
A measurement taken under the harness is a measurement about the
harness, and quoting one as though it were about the product is the
same fault as reading a stale log -- with the date replaced by a font.

## AN ATTRIBUTE THAT IS A VIEW CANNOT BE WATCHED BY REBINDING IT

2026-08-28. A probe replaced `dialog._category_colours` with a dict
subclass that logs every write, to find out who records a follower's
inherited colours as somebody's hand-picks. It reported nothing at
all: no writes, and an empty record at the end -- while the probe
that had measured the defect an hour earlier read the same record
holding all four colours.

The dict is a VIEW INTO A PER-DATASET BANK (ruling 8, 2026-08-24):
`_swap_dataset_memory` rebinds the attribute to whichever bank the
dataset in force owns, so the watcher was dropped at the first swap
and every later write went to the real dict. An instrument that
answers "nothing happened" because it was replaced is the silent-log
fault wearing an attribute's clothes.

**BEFORE WATCHING AN ATTRIBUTE, ASK WHO ELSE ASSIGNS IT.** Where
something rebinds it -- a bank swap, a project change, a reset -- the
watch has to go INSIDE the code that writes (a dump behind a flag,
which this project already prescribes) rather than around the object.
And read the tell: a watcher that logs zero writes while another
reading shows the value moving is reporting on itself.

## THE HARNESS SETTING EVERY RUNNER SETS IS PART OF THE MEASUREMENT

2026-08-28. The suite was launched by hand, three shards, without
`QT_QPA_PLATFORM=offscreen` -- which `tests/run_tests_macos.sh` sets,
`release.py` sets, and the CI jobs set. Three layout tests failed at
once, all saying the assembled window is 1334px against a 1280
ceiling. Nothing about the layout had changed in the package since a
candidate whose report shows all three passing.

The cause was the font. Offscreen gives Sans Serif 9pt; cocoa gives
the system font at 13pt, every label and combo is wider, and the
window's minimum comes out 54px over. Measured both ways on one tree,
which is what turned "three mysterious failures" into one sentence.

TWO LESSONS, and the second is the more useful.

**A RUN LAUNCHED BY HAND IS A DIFFERENT HARNESS.** When every other
runner sets an environment variable, that variable is part of what the
suite MEANS, and a hand-launched run without it measures something
else. Copy the launcher rather than the command -- or better, run the
launcher.

**AND THE ACCIDENT WAS A FINDING.** The 1280 promise is about the
narrowest screen a user has, and every instrument here verifies it
under a 9pt font no desktop uses; at the system font the three
priorities the rule sets out cannot all hold. So the mis-launch
measured the one place nobody had measured. This project's own rule is
to make a measurement somewhere nobody has been; the mirror of it is
that a check reading a setting the ENVIRONMENT supplies may be reading
somewhere nobody IS. Recorded for the maintainer in the ledger rather
than fixed, because which of three settled priorities gives is a
decision.

## A CONTROL ARM'S OWN ACT CAN TRAVEL INTO THE ARM IT CONTROLS

2026-08-28, verifying a claim that a colour picked on a map opened
with Load never reaches the map. The probe had three arms -- a map
drawn in this session, the same map opened with Load, and one adopted
by reopening the plugin -- and every arm picked THE SAME COLOUR.

The control arm's pick was saved into the file the second arm opened.
So that arm compared a colour with itself, reported a repaint that had
happened before it ran, and the claim was nearly recorded as not
reproducing. On a clean tree with one colour per arm, both opened maps
stood still.

**A CONTROL ARM IS A SECOND FIXTURE, AND IT INHERITS THE FIRST.**
Wherever arms share a file, a project, a layer or a record, ask what
the earlier arm LEFT there, and give each arm a value nothing else in
the probe could have produced. Then assert the value is absent before
you stage it: one line, and it is what tells "the act worked" from
"the act was already done".

TWO MORE THINGS THE SAME PROBE GOT WRONG, both caught by the control
rather than by reading. It drove the RAMP combo where the act in
question is the colour EDITOR's -- and a ramp picked with live update
off deliberately does not repaint, so the control came back silent and
correct. And it picked a CATEGORY colour on a quantitative row, which
the map is right to ignore. Both read exactly like the defect. A
control arm that must succeed is the cheapest way to find out that a
probe is measuring its own fixture.

## A CLAIM HAS A DIRECTION, AND CHECKING IT IS NOT OPTIONAL

2026-08-28. A hunt reported that a Save drops a no-data twin's table
while its element's survives. Driving the same panel act -- delete one
element's row from the group, press Save -- gave the OPPOSITE: the
element's table went and the twin stayed, leaving a set of
missing-value areas belonging to an element the map does not have.

Same mechanism, same harm class, reversed. What was fixed and recorded
is the direction that was MEASURED, and the claim's own direction is
noted in the ledger as not reproduced.

This file already says a HARM named by reading is a hypothesis, and
CLAUDE.md says that of one fact written twice you ask which writer had
a reason. This is the same rule pointed at a report: **of one claim,
ask which way round it runs, and drive it before believing either
half.** It costs one probe and it is the difference between fixing a
defect and moving the half that was already correct.

## A MEASUREMENT THAT DOES NOT RESOLVE IS NOT A MEASUREMENT

Same day, and it nearly put a false number into the source. A hunt
measured a Save going from 22.4s to 16.2s at 128 elements, and from
134s to 90s at 256, by dropping an OGR open the code discards anyway.
The change was made and both figures were written at the site as its
justification.

Measured here, on this machine, the effect did not exist: 4.12s against
3.72s at 64 elements, and at 128 the supposedly faster arm came back
SLOWER, 15.73s against 14.72s. Single samples on a machine that had been
running QGIS all evening tell you nothing in either direction.

**THE CHANGE STAYED AND THE CLAIM WENT.** It is defensible on what is
actually true of it -- it does not build an object that is discarded by
construction -- and the docstring now says what was and was not
established, with the hunt's figures attributed to the hunt. A
performance justification you have not reproduced is somebody else's
measurement wearing your commit message.

The habit: when you change something FOR a number, reproduce the number
first, on the machine you are on, with both arms in one run. If it does
not resolve, say so and find another reason to want the change -- or
drop it.

## A FIXTURE THAT CANNOT SHARE A SOURCE CANNOT SHOW A SOURCE COLLISION

Same day, three probes deep into one claim. The group chooser was
reported to land on the OUTLINES layer, which is built on the region's
own source, and so empty the region combo. Two probes came back clean
on both arms.

The fixture was the reason. `make_region_layer` is a MEMORY layer, and
a memory URI is not something anything else can be built on -- so the
two layers never shared a source string and the collision the claim is
about could not arise. On the packaged Auckland GeoPackage it
reproduced immediately, with a control arm (outlines off) staying
clean.

This is the fixture-that-cannot-exhibit-the-case trap in its plainest
clothes, and the question that finds it quickly is: **what does this
defect need two things to SHARE, and can my fixture make them share
it?** Where the answer is a path, a file or a provider, the synthetic
grid is the wrong fixture whatever else it has going for it.

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
state before any debounce has fired. The dialog has two debounces --
the preview one, which is a FLOOR that widens to whatever the last
rebuild cost, and the live one -- and a task whose completion does
main-thread work, so an action arriving after the preview fires meets
a different machine from one at 0 ms, and one arriving after the live
interval meets a third.
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
was allowed to settle. This dialog debounces twice before drawing and
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
hundred and forty tests had been written against a plugin where
setting an output path made every Generate write the file; the ruling
made writing a separate press. What follows is what the conversion
cost, what it found, and the four ways a mechanical sweep goes wrong,
because the shape recurs whenever an act is split.

**THE FAITHFUL CONVERSION IS THE ONE THAT CHANGES NO TEST'S MEANING.**
A run wrote whenever a path was set, so a Save press inserted at
exactly the moment the old write happened reproduces the state each
test was written against. Fifty-eight went in by script that way.
What must NOT be converted mechanically is the test whose subject is
the act itself -- when it happens, what refuses it, what is said --
because there the assertion has CHANGED rather than moved. Twenty-four
of those were re-decided by hand.

**AND A DISJUNCTION IS WHERE A CONVERSION GOES QUIETLY GREEN.** Two
tests asserted "the plugin warned OR the file is unchanged", which was
a real question while a run wrote. Under a ruling that stops anything
writing, the second limb is true on every route for ever, and both
tests would have passed while measuring nothing. WHEN A RULING REMOVES
A BEHAVIOUR, GREP THE SUITE FOR ASSERTIONS JOINED BY `or`: each is a
place where one limb may have become free.

**FOUR WAYS THE SWEEP ITSELF WAS WRONG, each found by the suite and
then swept for as a CLASS rather than mended where it was met.** That
last part is the discipline: every one of these was a family with
between one and two members, and finding the others cost a ten-line
script each time.

*It keyed on a variable name rather than on the object.* The script
tracked which dialog held an output path by the name `dlg`, and a
function that builds a SECOND dialog under the same name inherited the
first one's state -- so a press landed in a leg that is deliberately
memory-mode. Swept by re-running the analysis with `X = Dialog(`
resetting the state: one other candidate, and it was a false positive.

*The tests that never named a path were invisible to it.* A dialog
that ADOPTS a reopened project gets its path from the layers, so no
`setFilePath` appears in the function at all and a sweep keyed on that
call has nothing to see. Those tests then assert that the map still
reads from its file after a run -- true when a run wrote. Swept by
asking a different question: every `_reads_from` assertion whose most
recent preceding act is a generate rather than a save.

*It put the press where the old write was, not where the test's
subject is.* A pinned-bounds test set its pin AFTER the generate, so a
press inserted at the generate wrote the file before the thing the
test is about had happened. Swept by looking for a file READ that
follows a style change that follows a press.

*And one failure was not the conversion at all.* A test failed in the
full suite and passed alone: the region chooser had not settled on a
second dataset before the run. That is a fixed-tick bet on how loaded
the machine is, and the cure is this file's own rule -- wait on the
EVENT. It now waits for the chooser to hold the layer and says what it
found if it never does, which turned a silent flake into the sentence
that named a real defect underneath it.

## WHAT "THE FILE DID NOT CHANGE" MEANS, MEASURED

Also 2026-08-27, and it cost three drafts of one test.

**BYTES ARE NOT A PROPERTY OF AN UNTOUCHED GEOPACKAGE.** A Generate
after a Save leaves every table, every feature count, every embedded
style and the record IDENTICAL while the file grows from 184,320 bytes
to 356,352 -- sqlite reorganising it as the layers that were reading it
are replaced and let go. A byte comparison there measures the file
system rather than the plugin, and it fails on a run that wrote
nothing at all. Compare what the file HOLDS.

**AND A VALUE JUST WRITTEN IS NOT IN THE FILE YET.** It lives in
sqlite's write-ahead log beside it, so OGR reads it back perfectly
while a byte search of the `.gpkg` finds nothing. A byte-level claim
about a file is only meaningful once everything has let go -- and then
it should be made about every file that TRAVELS, since the log and the
shared-memory file sit next to it until the close folds them in.

**SO "DID THE PRESS WRITE" HAS THREE ANSWERS AND TWO ARE WRONG.**
Asking whether the file EXISTS is true of a file somebody else wrote,
so a save the user declined was reported as one that happened. Asking
whether its BYTES moved fails the opposite way: saving an unchanged
map twice leaves them identical. What a person actually goes by is
what the plugin SAYS, so that is what the helper reads -- with the
file's state as a cross-check in both directions, since a plugin that
reports a save and leaves no file, or writes without a word, is a
defect this helper must not smooth over on its way past.

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

## FIVE WAYS A PROBE OR A CELL FAILED TO REACH ITS OWN CASE IN ONE DAY

2026-08-26, judging nine hunt claims. Every one of these reads exactly
like a passing result, which is why they are listed together: the
common shape is not carelessness but that a harness has no way of
telling "the case did not arise" from "the case arose and was fine".

**A FIXTURE THAT STAGES SOMETHING THE PRODUCT WOULD NEVER KEEP.** A
probe pinned a class bound on a CATEGORICAL element. A pin names a
class boundary, a categorical row has none, so the plugin correctly
kept nothing -- and the absence afterwards read as a record the code
had lost.

**A KEY THE RECORD DOES NOT HAVE.** The same probe staged
`low_pinned: True` beside the bound, on the reasonable belief that a
per-end flag lives beside the value. It does not: `low` IS the pin,
and `_pins_in_force` asks whether it is not None. The plugin dropped
an invention and the drop read as a defect. BEFORE READING AN ABSENCE
AS A LOSS, CHECK THE RECORD HAS THAT KEY AT ALL.

**A SUBSTRING MATCH THAT PICKED THE WRONG THING.** A cell asked the
chooser for the group named "WeavingSpace tiles" and got "WeavingSpace
tiles 2", which contains it -- so a leg about whether an OLDER choice
survives selected the newer one and then reported that a choice had
not survived churn it never met. Where labels are built by
concatenation, match the PART, not the whole.

**TWO DRAFTS OF ONE CELL THAT COULD NOT REACH ITS CASE, and the
catalogue caught both.** The cell needed the layer combo to re-emit
`layerChanged`. Adding and removing a spare polygon layer does that
when the project holds ONE dataset and does nothing when it holds
two, so the first draft staged no re-emission at all. Driving a RUN
instead cannot show it either, because the landing makes the chosen
group the NEWEST in the tree, and the reading under test -- ask only
about the newest group -- then answers correctly by accident. The
cell drives the re-emission itself now, which is the mechanism the
rule is about. TWO GREEN CELLS, TWO DIFFERENT REASONS THE CASE COULD
NOT ARISE, and only the mutation entry could tell.

**AND AN ORACLE THAT READ CORRECT BEHAVIOUR AS THE HARM.** A test
captured a group's layer ids after its first route and asked at the
end whether they had survived. The routes in between are the same
dataset's own runs on the same group, and replacing that map in place
is exactly what they are for. THE HARM MUST BE MEASURED WHERE IT
WOULD HAPPEN, not from a snapshot taken before several legitimate
replacements.

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
defects. `_forget_the_last_project` clears every field-keyed record
when a project is replaced, and its list had been missing the scheme
shelf since the shelf existed. A hunt LOOKED at that omission earlier
the same night and ruled it benign -- correctly, and it measured why:
the bank swap ran with None on a project replacement and emptied the
view on its way past. Three hours later a fix elsewhere stopped the
swap running on an empty chooser, and the omission became a leak, a
scheme from the project you closed redrawing a column in the project
you opened.

**A LIST THAT IS WRONG BUT MASKED IS STILL WRONG.** When you find a
record emptied by something other than the code that owns it, write
the entry anyway, and say at the site that the other thing is not
what keeps it true. The mask is not a defence; it is a countdown.

**AND A RULED-OUT FINDING IS RULED OUT AGAINST A TREE.** This
project's hunt briefs already ask what was ruled out and why. What
this adds: a ruling-out is only as durable as the code it measured,
so when a fix lands near ground a hunt cleared, the clearing is worth
re-reading rather than trusting.

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
were in the matrices, and they were not: the dataset-switch rulings
had journey tests, one axis each, which is exactly the arrangement
the matrix default exists to replace. Routes (plain, same-schema,
shared-name, column-deleted, return, pre-landing, mid-run) crossed
with staged state (derived, touched scheme, picks and pins, path set)
crossed with aftermath (immediate, generate, return); a spine of
every route against the two states with the most to lose, the plain
route against everything, and a seeded sample of the rest. Cells
report together, the count is asserted, and the mid-run cells assert
their own premise -- a run still in flight at the switch -- rather
than judging a different journey when the window is missed.

**ITS FIRST RUN FOUND TWO BROKEN CELLS, AND THE ORACLE WAS WHAT WAS
BROKEN.** Both were the column-deleted route failing the
no-absent-fields invariant -- which is the no-leakage ruling's
invariant, and that ruling is about OTHER datasets' fields. A field
the SAME dataset just lost keeps its idle records by the settled
renamed-column rule, so its return can restore them. The matrix
forced the two rules to be stated with their boundary, which is worth
as much as a defect: an invariant written broader than its ruling
reads as coverage and is actually a false alarm waiting to teach
somebody to ignore it.

## A MATRIX ASKS ABOUT RECORDS; ADD THE QUESTION ABOUT WHAT IS SEEN

2026-08-19, and it is the sharpest thing the day taught. Three defects
landed in one evening and the symbology matrix -- twelve routes, nine
shapes, three aftermaths, three schemes, close to a thousand cells --
caught none of them:

- a clear mark drawn into pixels its own QLineEdit covers, so it had
  never been visible on any build;
- a ceiling somebody had set with no edge to draw a mark on, because
  the swatch enumerated two of the record's four ends;
- a bound of 1e9 elided out of a box sized for 1.56.

THE CROSSING WAS NEVER THE PROBLEM. The routes were all there and all
exercised: "paste a foreign style", "set a ceiling", "copy to another
element". What the matrix could COMPLAIN about was the whole of the
gap. Read its own vocabulary -- "took the copy and was never stamped",
"its spinner does not show", "draws no classes at all" -- and every
one is a record, a layer, a stamp or a notice. NOTHING IN IT EVER
LOOKED AT A PICTURE, and nothing asked whether a number it could see
could be typed back. A grid of a thousand cells cannot catch a mark
nobody can see, because it never looks.

**SO EVERY CELL NOW ASKS TWO MORE QUESTIONS**, and they ride the state
the cell has already staged rather than needing an axis of their own:
everything the record holds is MARKED where the user would look for
it, and every number the record holds is DISPLAYED IN FULL and types
back to itself through the control's own validator.
`_unseen_or_untypable` is that check, called from the symbology
matrix's passing exits and from the copy matrix's verdict.

**WHAT BELONGS IN A CELL AND WHAT BELONGS IN ONE TEST.** The cell asks
what varies with the cell -- these values, this shape, this route. The
per-END distinctness of the four marks does not vary with the cell, so
it is asserted once, in `test_the_swatch_marks_every_end_a_person_set`,
and the matrix does not pay for it a thousand times.

**THE GENERAL FORM, which is the part to carry to the next matrix:**
ask what a cell is ALLOWED TO NOTICE before adding cells. An axis that
crosses a question the verdict cannot ask is an axis that cannot fail.
This project's characteristic defect is a wrong map that looks like a
right one; its second characteristic defect is a control that is right
and cannot be seen or reached, and only the first of those had ever
been in a matrix's vocabulary.

## THREE WAYS A GUARD FOR A VISUAL THING PASSES ON A BROKEN PRODUCT

2026-08-19, all three in one sitting, all three caught by the mutation
catalogue rather than by reading. They are worth knowing on sight,
because a guard about PIXELS fails in ways a guard about records does
not.

**IT REPAIRS THE DEFECT ON ITS WAY PAST.** The first attempt at
asserting the clear mark was drawn hid the mark and showed it again to
get a before-and-after contrast -- and `show()` and `raise_()` are
exactly what the mutation removed. The test mended the product, then
measured the mended product, and reported success. ASK OF ANY SETUP
STEP WHETHER IT WOULD UNDO THE BREAK YOU ARE LOOKING FOR.

**IT HAS NOTHING TO LOOK AT.** Its replacement ran after the
surrounding test had given every bound back, so no box was marked, the
loop body never executed, and an empty `unseen` list asserted nothing
at all. The repair is the cheapest one this file knows: COUNT WHAT YOU
LOOKED AT and assert the count.

**IT DRIVES THE MECHANISM AND NOT THE CALLER.** The swatch guard
handed edge pairs straight to the icon builder, proving that the
DRAWING works while the dialog went on asking for two ends of four. A
unit-tested mechanism with an undriven caller is a motionless axis --
this project already had that lesson from `unworn_classes`, and it
recurred inside a test written to close a defect of exactly that kind.

**THE COMMON CURE** is to drive the product and read the pixels, and
to state the check as its inverse: not "the mark is drawn" but "name
anything that draws nothing".

## AN INSTRUMENT IN THE USER'S HANDS BEATS SIX REPRODUCTIONS IN YOURS

The same evening, and it is the most useful hour of the day. A
maintainer reported a class recoloured in QGIS reaching the map and
neither the swatch nor the colour editor. SIX reproductions were built
here -- live update on and off, the edit landing mid-run and at rest,
against their OWN dataset -- and every one of them worked.

What settled it was two dumps behind `WEAVINGSPACE_ADOPT_DUMP`, in the
shipped source, and one run by the person holding the failure. The
dump was EMPTY of both lines: the plugin had never been told. Its
`styleChanged` hook is connected in exactly two places, a run landing
and a group being adopted, and that session's Generate had failed, so
nothing was watched.

THE LESSON IS NOT "ADD LOGGING". It is that a reproduction which will
not reproduce is a signal about the DIFFERENCE between the two
sessions, and the cheapest way to find that difference is to measure
the session that is actually broken. Budget the instrument early: it
costs three lines and it is the only thing that can answer.

AND AN EMPTY DUMP IS EVIDENCE ONLY WHEN THE DUMP IS KNOWN TO WORK.
That one was trusted because other `_dump` lines appeared in the same
terminal, and because both missing lines had been seen on this machine
against the same data. Without those two facts it would have been the
silent-log fault this file already records.

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

## A TEST WHOSE SETUP REFRESHES THE THING UNDER TEST PASSES FOREVER

2026-08-20, and it is the data-provider face of a shape this file
already records twice.

`test_a_project_whose_region_layer_has_moved` covers a GeoPackage that
goes while the layer is open, and it calls `second.reload()` before it
asks a single question. That call is the ONE act that makes QGIS tell
the truth about a moved file -- measured on 4.0.3, an open layer whose
file has moved answers `isValid()` True, `dataProvider().isValid()`
True and `featureCount()` with its last good number, and only after a
reload does the provider admit False. It is also the one act a user
never performs. So the test had been exercising the honest path for as
long as it had existed, while the path a maintainer actually walks was
uncovered, and the plugin duly refused a run in terms of the wrong
thing (ledger row 32).

THE FAMILY, now three deep and each arriving in different clothes: a
visual guard that called `show()` and `raise_()` on the mark whose
hiding was the mutation; a guard whose fixture gave every element all
three kinds of absence, so the case it was written for could not
arise; and this one, where a refresh call stands between the fixture
and the question.

**READ A TEST'S ARRANGEMENT FOR CALLS THAT REFRESH, RESET, REOPEN OR
REPAIR.** A setup step is not neutral just because it comes before the
assertions. Ask of each one whether the defect could survive it, and
where it could not, that step IS the test's subject and has to move
after the question or go.

THE REPLACEMENT ASSERTS ITS OWN PREMISE, which is what stops it
rotting the other way: it requires the stale answers to still be
stale, so a future QGIS that starts reporting honestly fails this test
and asks to be rewritten, rather than passing quietly while covering a
case that can no longer arise.

## A REPRODUCTION THAT CANNOT REACH THE CASE REPORTS GOOD NEWS

2026-08-20, and it is the third face of a shape this file already
carries twice.

A hunt claimed that a second signal adopts colours a first correctly
declined. The probe written to check it drove the edit, waited, fired
a bare repaint, and read the record: clean. The claim looked wrong.

It was the probe. The repaint landed 0.9 seconds after the edit, and
the code under test drops a repaint arriving within ONE SECOND of a
style signal for the same element -- an echo guard added the same day.
The probe could not reach the case it was written for. The hunt's own
probe waited 1.4 seconds and reproduced immediately; widening the gap
turned one hand-picked colour into four, with the user's displaced a
class.

THE FAMILY, now four deep and each arriving in different clothes: a
setup step that repairs the defect (`show()`, `reload()`); a fixture
that cannot exhibit the case (a square that Douglas-Peucker will not
simplify, a ceiling outside the data); a guard that runs where there
is nothing to look at; and now a TIMING that falls inside a window the
product deliberately ignores.

**SO WHEN A PROBE DISAGREES WITH A CLAIM, SUSPECT THE PROBE FIRST**,
and specifically ask what the code under test does with the timing,
the ordering and the debounces you happened to choose. This dialog has
four such windows now -- the preview debounce, the live one, a 300 ms repaint
drain, and a 1 s echo -- and a reproduction that lands inside one of
them measures the window rather than the software.

AND THE CHEAPEST CURE IS THE ONE THIS FILE ALREADY PRESCRIBES: assert
the premise. A probe that checked "the second signal actually reached
the handler" before reading the record would have failed loudly
instead of passing quietly.

## TWO DEAD AXES OUT OF TWENTY-SIX, AND BOTH WERE SUBSUMED

The per-assertion hunt of 2026-08-20, at four tests written the day
before, each already carrying a proved catalogue entry. Nineteen
mutations; two assertions could not fail. Neither was a product fault
and neither is the usual shape:

- an assertion naming a REAL contract that this test cannot reach --
  `assert dlg._task is None` guards against launching a run over a
  dead layer, and survives deleting the guard, because the conversion
  refuses that fixture unaided. A second line of defence behind a
  first that is not under test here;
- an assertion SUBSUMED BY A STRONGER ONE two lines below it, created
  by strengthening the test: `assert not adopted_template` cannot be
  the failing assertion once `assert not picks` sits beneath it.

**THE SECOND IS THE INTERESTING ONE**, because strengthening a test is
how it arrived. When you add a broader assertion, the narrower one
above it may stop being able to fail -- so read what you have made
redundant, and either delete it or move it where it still bites. A
dead axis created by an improvement is still a dead axis.

The rate, one in thirteen, is better than this project's standing one
in five or six. That is not evidence the practice can be skipped: all
four tests had been through the catalogue first, which proves the
PRIMARY axis and structurally cannot see the rest, and both dead axes
sat behind live primaries exactly as every previous round found.

## FOUR WRONG HYPOTHESES ABOUT MY OWN TEST BEFORE THE PRODUCT WAS IN
## QUESTION

2026-08-20, writing a guard for a moved region layer. This file
already says to bisect by disabling rather than reasoning after ONE
hypothesis fails. Four failed, each plausible, each costing a run:

- a missing `bridge` import -- a real fault in the test, and the only
  one of the four that announced itself honestly;
- a 600 ms wait, blamed on the style debounce. Widening it to 1600 ms
  changed nothing;
- the ramp picked was **Accent**, a qualitative palette, and a
  graduated row auto-swaps those away. The test was measuring a
  correct refusal;
- live update was OFF, where "preserve, do not repaint" means the map
  is CORRECT not to move. The test was demanding that the software get
  it wrong, which is a shape this file already names.

Only then did the measurements name the real site, and it was not
where the ledger had put it: `_restyle_only()` called by hand
repainted perfectly, while the route to it never arrived.

**AND THE SITE WRITTEN DOWN NEXT WAS ALSO WRONG.** This section said
for a day that `_generate`'s availability check stands in front of the
restyle fast path and refuses silently on a live run. Both halves are
false. A debounced tick never reaches `_generate`: `_maybe_live_
generate` holds ten gates of its own and the sixth asks the same
question. And it is not silent -- it says the map cannot be updated,
which is worse than saying nothing, because the sentence is false and
sends the reader to their data.

What settled it was one dump line per gate, run once:

    LIVE-GATE source-gone

**THE LESSON IS NOT "TEST FIXTURES ARE HARD".** It is that each of the
four was a question about the HARNESS, and answering them one at a
time is exactly the reasoning the bisect rule exists to replace. A
probe that says which gate returned would have cost one run and
answered all four at once -- and that is what finally did.

**AND A SITE NAMED BY READING IS A HYPOTHESIS.** The wrong location
travelled into four binding documents in a single documentation round
before anything measured it, where it reads exactly like a location
somebody proved. The rule that follows is the bisect rule wearing
different clothes: when you write down WHERE a defect is, say how you
know -- and if the answer is "I read the code", spend the one run.

## A JUDGEMENT BEHIND AN `if` IS A GREEN THAT SAYS NOTHING

2026-08-20, twice within the hour, in two tests written by the same
hand minutes apart. Both wrote the interesting assertion inside a
conditional -- "if the element kept the column AND is still
categorical, then require the question" -- and both PASSED without the
branch ever executing, because the fixture's columns held a handful of
values and the condition was false.

**A CONDITIONAL ASSERTION IS AN ASSERTION THAT MAY NOT EXIST.** It
reads like coverage, it costs a line, and its green is indistinguishable
from a green where the case never arose. This file already carries the
shape twice -- a guard that runs where there is nothing to look at, and
a fixture that cannot exhibit its case -- and this is the same fault
arriving through control flow rather than through data.

**TWO CURES, AND USE BOTH.** Count what you looked at and assert the
count, which is the cheapest guard this project knows. And make at
least ONE assertion unconditional, so a cell always says something:
here it became "the element came out on a column the new dataset
actually carries", which holds whichever branch the plugin took.

**AND WHERE THE CONDITION IS A THRESHOLD, STAGE THE CONDITION.** Both
of these needed a column with more distinct values than
`bridge.MANY_CATEGORIES`, which in this fixture family means ten
thousand polygons and minutes of tiling to prove an `if`. Lowering the
constant for the length of the test and restoring it in `finally` is
the same move as removing a palette to test the installer: it stages
the case rather than inflating the fixture.

## A TEST WITH NO CATALOGUE ENTRY IS A TEST YOU BELIEVE

Also 2026-08-20. Two registered tests landed that day guarding
behaviour believed to be ALREADY CORRECT -- the dataset-switch rules,
recorded as found sound rather than broken -- so there was no fix to
break and no entry was written. Nobody had watched either fail.

That is a different thing from a test that has been proved, and the
suite cannot tell them apart: both are green lines in the same list.
Where a test guards ground that was already sound, the entry has to be
aimed at the MACHINERY it depends on, or the test is a statement of
belief with a passing tick beside it.

**AND SITTING DOWN TO WRITE THOSE ENTRIES IS WHAT FOUND THE DEFECT.**
Neither test was guarding sound ground. Both were vacuous, for the
reason in the section below, and the behaviour they named was broken
at three doors while three binding documents said it had been
measured. So the rule is stronger than it looked when it was written:
an unproved test is not merely unproved, it is a test whose PREMISE
nobody has checked either -- and the cheapest way to check the premise
is to try to kill it.

## A FIXTURE THAT LETS THE PLUGIN DERIVE THE THING UNDER TEST

2026-08-20, and it is the fixture-that-cannot-move trap wearing new
clothes. Two tests guarded the rule that a change of region dataset
KEEPS an element's setup where the new data has a column of that name
and DROPS it where it does not. Both passed. Both were vacuous, and
the defect they were written for was live the whole time: a
categorical scheme a user had picked rode onto a column of areas in
square metres and drew a colour for each.

The fixture assigned a variable and never touched the STYLE chooser.
`_refresh_table` restores a style only where somebody chose it and
otherwise RE-DERIVES one from the column's type -- so on every switch
the plugin recomputed a quantitative style for the new numeric column,
which is the right answer arrived at for a reason that has nothing to
do with the rule. Nothing was retained, so nothing could be wrongly
retained.

**ASK WHAT YOUR FIXTURE LEAVES TO A DEFAULT.** A test about RETAINING
something must first make that something worth retaining, and the way
to do it is to drive the control a user drives -- here `activated` on
the style combo, which is what marks the choice as theirs. A setting
the product would arrive at by itself is invisible in a green result,
exactly like a fixture whose values cannot move.

**AND THE TELL WAS IN THE TEST ALREADY.** Both had written their
interesting assertion behind an `if`, which is the section above, and
both `if`s were false for this same reason. A conditional assertion
and a fixture that cannot exhibit its case are two faces of one fault:
the test never reached the question it names.

## A GUARD MAY BE WRITTEN TWICE, AND THEN NEITHER HALF CAN BE KILLED

Also 2026-08-20, found by the catalogue within the hour. Two entries
written that night SURVIVED, and neither was reporting a weak test.

The rule that a dropped setup takes its style with it was written at
BOTH places `_refresh_table` touches it: the branch restoring a
remembered style, and the flag recording that style as somebody's
choice. Each is sufficient alone, because a change of region dataset
rebuilds the table TWICE -- once from the chooser and once from the
queued settle -- and the second pass reads what the first left. So a
mutation of either half is invisible: the other answers one rebuild
later and every observable comes out right.

The catch-all colour's SURVIVAL across a re-Generate is the same shape
through different machinery. The landing CARRIES the old renderer
where the element's assignment has not changed, and where it does not,
the renderer is rebuilt from the record. Each was mutated alone and
the test went on passing; broken TOGETHER it failed at once, naming
the grey it had been repainted. Redundant is not dead.

**WHEN AN ENTRY SURVIVES, ASK WHETHER THE BEHAVIOUR HAS TWO
IMPLEMENTATIONS BEFORE ASKING WHETHER THE TEST IS WEAK.** The reflex
is to strengthen the test, and here there was nothing to strengthen.
Break every route AT ONCE: if the test fails, the axis is live and
redundantly held, and the honest record is a note at the test rather
than an entry that can only ever be red. If it passes, the assertion
is the problem after all.

**AND THE SURVIVOR STILL EARNED ITS KEEP**, which is the part worth
carrying: asking why one could not be killed is what turned up the
THIRD door into the same ruling -- a column deleted in QGIS, where
`_adapt_to_the_layer` re-points the row before the rebuild can notice
anything is missing. That door has one implementation, one line, and
an entry that catches.

## AN ENTRY PER AXIS, NOT PER TEST -- AND READ WHICH ASSERTION FIRED

2026-08-20, the per-assertion round at three tests written that day.
This file already says the catalogue proves a test's PRIMARY axis and
structurally cannot see the rest. What this round adds is the remedy,
which costs one entry each and is worth the minute.

**THE MASKING IS ORDINARY, NOT EXCEPTIONAL.** The catch-all test
carries three axes: the wrong SENTENCE, the lost RECORD, and the
colour's SURVIVAL across a re-tile. Under the one mutation that
matters -- the fix removed -- the sentence assertion fires FIRST and
the other two are never reached. The entry reported `caught` and
exactly one axis was proved.

**SO WRITE AN ENTRY FOR EACH AXIS, AIMED AT THE NARROWEST THING THAT
ASSERTION NAMES.** Skipping the catch-all in the ADOPT walk leaves
every sentence correct and loses the one colour the user changed, so
it proves the record axis and nothing else. Painting the scheme name
while the Custom flag is set leaves the flag correct and puts no ink
on screen, so it proves the pixel axis. Each is a one-line mutation.

**AND RUN THE MUTATION BY HAND ONCE, TO SEE WHICH LINE FIRES.** The
catalogue reports `caught` without saying where, so a masked axis is
invisible in its output. A single run printing the failing assertion
is what turned "this test is guarded" into "one of its three axes is
guarded".

**WHAT STAYS UNPROVEN SHOULD BE SAID.** The survival axis here is
still masked by the record axis, and is written down as unproven
rather than counted as guarded: a guard nobody has watched fail is a
guard nobody should count.

**AND "NO ONE-LINE MUTATION REACHES IT" IS USUALLY WRONG.** The two
list-integrity assertions on the scheme cell were recorded as
unreachable for about an hour -- that "Custom" never becomes an ITEM,
and that the index stays on the last-picked scheme. Both have an
obvious one-liner, and both are the implementation somebody would
plausibly have written instead: `addItem("Custom")` when the flag goes
on, and `setCurrentIndex(-1)` beside it. Each proved its assertion
first time. Before recording an axis as unprovable, try writing the
WRONG implementation rather than a mutation of the right one.

## A GUARD'S OWN FIRST DRAFT IS WHERE THE NEXT DEFECT IS

Also 2026-08-20. A fix for a real defect shipped with four passing
tests around it, and the fix itself was wrong: a lookup by class
BOUNDS returned on the first match, and a ladder may hold several
classes with identical bounds -- a constant column, a tied column,
`{1, 5, 9}` at k=5. QGIS's `addClass` then inserts another degenerate
`(0.0, 0.0)` class, which collides with any fixture whose first real
class is also degenerate, so the plugin's own colour was compared
against a placeholder grey and adopted as somebody's hand-pick.

The four tests could not see it because every one of them asked about
the RECORD after the fact, and the record was consistent with either
answer. What found it was PRINTING THE STORE at each stage and reading
it -- the same instrument-the-code prescription this file already
carries, reached only after the tests had said everything was fine.

**COUNT THE DEGENERATE CASE INTO ANY FIXTURE THAT INDEXES BY VALUE.**
Bounds, breaks, category values: wherever a lookup keys on something
the data can repeat, the fixture must contain a repeat, and the test
must ASSERT it does. This one now requires `len(set(bounds)) <
len(bounds)` before it draws any conclusion, so a fixture without the
collision fails loudly instead of passing vacuously.

## A RETIRED CONTRACT CAN GO ON PASSING BECAUSE THE ABSURD CASE FAILS FAST

2026-08-26, and it cost the first candidate of this branch. The size
ceiling stopped being a refusal on 2026-08-25 -- the maintainer ruled
that a size is a question rather than a verdict -- and the work list
item that went with it, "update the tests that assert a refusal and
say why the expectation moved", was ticked. FOUR TESTS STILL ASSUMED A
REFUSAL, and every one of them was green.

**THE HARNESS SUPPLIED THE WRONG ARM.** `_no_modal_dialogs` answers
`question` with **Yes** unless a test stages otherwise, so a suite that
trips the size guard consents to the run on the user's behalf. Every
one of those four tests was therefore driving the "go on" arm at
spacings asking for 36,086,505 tiles and for
36,000,000,086,453,551,104.

**AND THE ABSURD ONE COLLAPSES FASTER THAN THE MERELY ENORMOUS ONE.**
Measured that evening: declining either settles in 0.9 s; accepting the
36-million-tile run had not settled in 93 s, while the 3.6e19 one dies
almost at once. So the case chosen to be MOST extreme was the one that
looked most like a guard working, and the moderate one -- the only one
slow enough to outlast a ninety-second ceiling -- was the only one that
ever went red. It went red on Linux and Windows and on neither Mac,
which reads as a platform fault and is nothing of the kind.

**THE SWEEP MISSED THEM BECAUSE THEY REACH THE GUARD SIDEWAYS.** The
tests mended when the ruling landed were the ones a search for the
refusal's own vocabulary turned up. These reach it through the SPACING
BOX, and their prose talks about spin boxes and extremes. This is
"targeted runs cannot find what they do not name" arriving in a place
this file had not seen it: not a fix applied to some instances of a
set, but an EXPECTATION left standing wherever the ruling's words do
not appear.

Three habits follow, and the first two are cheap.

WHEN A RULING CHANGES WHAT A GUARD DOES, GREP FOR THE CONDITION RATHER
THAN FOR THE VOCABULARY. Every test that can reach the band, whatever
it calls it -- here, every test that sets a spacing small enough or a
region large enough.

ASK WHAT THE HARNESS ANSWERS ON YOUR BEHALF. A shim that must answer
something answers the same thing every time, and that answer becomes an
invisible fixture. `MODAL_ANSWERS` exists precisely so a test can stage
the other arm, and a test that never stages one is asserting whatever
the shim happens to prefer. The refusal arm of every question this
plugin asks was unreachable from the suite until 2026-08-20 for the
same reason.

AND A TEST THAT WAITS ON AN IMPOSSIBLE JOB IS TIMING THE MACHINE. If a
case can only pass when a run the user was warned about fails quickly
enough, it is a performance budget wearing a guard's clothes. Stage the
answer that stops the run, and let a separate test own the arithmetic.

## AN ORACLE CAN BE GREEN BECAUSE OF THE DEFECT IT WILL LATER CATCH

Same evening, the switch matrix's `mid-run/touched-scheme/generate`
cell. It snapshots dataset A's element layers, launches a second run
ON A, switches the chooser to B mid-tiling, waits for that run to land,
generates on B, and requires the snapshot to survive.

Driven stage by stage: the in-flight run REPLACES A's map in place --
four new layers, same group, same region stamp -- which is the settled
contract, and the Generate on B then builds its own group and leaves
all four of A's alone. The protection the cell exists to check holds
perfectly. The snapshot is simply older than a legitimate replacement,
which is the oracle fault recorded above under "the harm must be
measured where it would happen".

WHAT MAKES IT WORTH ITS OWN ENTRY is why it was green before. Until the
same day, `_add_output_layers` took `weavingspace_region` from the
region CHOOSER as the run landed, so an A run landing under a B chooser
stamped B, the landing's own refusal saw a group whose stamps
disagreed, and it built a RIVAL group instead of replacing anything --
so the snapshot survived. The cell was passing because of the very
defect the branch had just fixed, and it went red the moment the code
became correct.

So: WHEN A FIX MAKES A LONG-PASSING TEST FAIL, ASK WHETHER THE TEST WAS
STANDING ON THE DEFECT. This file already says to read such a failure
as evidence about the world before assuming it is evidence about the
change; the sharper version is that a green oracle may be measuring a
side effect nobody chose, and the fix removes its footing rather than
breaking it.

AND THE REPAIRED CELL IS STRONGER THAN THE ONE IT REPLACES. Re-reading
the set to protect after the in-flight landing, with the premise
asserted -- the replacement produced as many layers as it took away --
leaves a cell that would go red under the old stamp behaviour, where
the version it replaces went green.

## PRESENCE IS NOT ORDER, AND A LATE CALL IS WORSE THAN A MISSING ONE

2026-08-26, and four hunts of eight found it independently, which is
the most this method has ever converged here.

A branch was missing a call its twin makes. The repair added it -- and
put it after the restore, where the twin puts it before and SAYS WHY
AT ITS OWN CALL SITE: a variable cannot be restored to a column the
region layer in force does not have. Four consequences followed, and
each hunt found a different one: every element's variable re-derived
against the wrong dataset, so the table described a map the layers did
not draw; a `same_data` test computed against the stale chooser, so
pins and categorical colours were skipped outright; the group then
stamped with that loss; and an adoption running while the memory bank
still belonged to the OTHER dataset, putting one map's hand-picked
value strings into that dataset's bank and its file.

**THE REPAIR TURNED VISIBLY WRONG INTO INVISIBLY WRONG**, which is a
hunt's own phrase and the reason this has its own section. Before it,
the chooser sat on the wrong dataset and a person could see that.
After it, the recovery happened -- just too late to govern anything --
and every symptom moved inside the records.

This project already carries the rule ("when a fix is inserted into an
existing sequence, check its ORDER against the twin, not merely that
the line is present"). What this adds is the tell: WHEN A TWIN'S CALL
SITE CARRIES A COMMENT, THE COMMENT IS USUALLY ABOUT THE POSITION. A
repair that copies the call and not the comment has copied the half
that does not encode the reasoning.

**AND THE ENTRY FOR IT COULD NOT BE MADE TO CATCH.** Three fixtures
were built to make the REORDERING visible and all three passed, since
`_adopt_existing_group` restores variables and picks from the layers'
own stamps -- so on any journey where the map's own region layer is
still in the project, the late recovery is covered by accident. After
three attempts the approach was wrong, not the constant: the entry is
aimed at the call's ABSENCE instead, which is the state the branch
actually shipped in, and the ORDER is recorded as guarded by the four
reproductions rather than by the catalogue. Say which of the two you
have when you write the entry. An accidental cover is a countdown.

## SILENCE IN A RECORD HAS MORE THAN ONE CAUSE; ASK WHICH READER MADE IT

Also 2026-08-26, and it is the other half of the same evening.

A repair taught a restore to CLEAR a record when the incoming one is
silent about it -- right, and the cure for a real defect three hunts
had reported. But `_assignments` reports the pins, the hand-picked
class colours and the ramp window as empty for any row NOT WEARING
GRADUATED, and the categorical colours as empty for any row not
wearing Categorized. So a record is silent about them whenever the
element is merely on ANOTHER STYLE, which is not the same claim as
"this group has none" -- and the clearing destroyed a pinned bound
belonging to an element somebody had switched to categories, stamping
its absence so that a reopen could not recover it.

**BEFORE CLEARING ON AN ABSENCE, ASK WHAT MAKES THE RECORD ABSENT.**
This file already says to ask what an absent key MEANS when a guard
reads one; the sharper version, when you are about to DELETE on that
absence, is to enumerate every reader that can produce it. Here there
were two: a person who chose nothing, and a mode that cannot carry the
thing at all.

**AND THE FIX WAS INERT UNTIL THE WHITELIST KNEW ABOUT IT.** The
clearing needed the element's MODE, and `mode` was not in
`WORKING_STATE_ELEMENT` -- the list that is the record's real
definition. A key missing from it is dropped in silence, so the gate
read None, decided "not graduated", and cleared nothing at all. Two
tests went red saying a record had ridden onto a group that never had
one, which is how it was found. WIDEN THE WHITELIST IN THE SAME COMMIT
AS THE CODE THAT READS IT -- this project has written that down twice
before, about `_adopt_dock_bounds` and about the copy.

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
taught. Sixteen hunts had just finished on this tree, aimed with care
at the code written that day, and they found eleven defects in it. An
hour later a sweep that does nothing clever -- it closes the plugin
window and opens it again -- found that every hand-chosen variable,
style, ramp and class count was lost, and had been since 2026-08-25.

THE ACT IS IN THE CODE'S OWN DOCSTRING. `_adopt_existing_group` says
it exists for "a dialog opened later in a QGIS session (the plugin
closed and reopened, which users do constantly)". Nothing was hidden;
what was missing was somebody DOING it and then reading every store.

**SO ENUMERATE WHAT A PERSON DOES, NOT WHAT A DEFECT MIGHT BE.** The
shapes this project hunts for -- an asymmetry, two stores of one fact,
a boundary crossed once -- are all questions about the CODE, and they
are answered by reading it. The complementary question is a list of
acts: open, close, reopen, save, choose, switch, delete, rename,
press the button twice. It is short, it is finite, and every item on
it is something the software promises to survive.

**AND A BOUNDARY CROSSING IS AN ACT WITH THE INVARIANT REVERSED.** A
control act must CHANGE something -- one that changed nothing passes
every invariant while proving nothing. A crossing must change NOTHING:
closing a window is not an edit, and neither is saving a file. That
one flag is what let a single harness judge controls, QGIS-side edits
and boundaries together, and the boundaries are where it went red.

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
could catch, and every failure was a different mechanism quietly
keeping the behaviour the mutation was supposed to break: ramp
defaults re-seeded are ramp defaults again, so the worn colours must
DIFFER from what a re-seed would draw; the reconciliation drain had
adopted the QML's colours as hand-picks, which are re-read at every
landing and keep the map whatever the arm under test does, so the
race's LOSING side had to be staged by emptying the record; and the
unchanged-assignment carry kept the old renderer until a SECOND
control moved the style signature -- the hunt's own journey had an
opacity change in it, and the fixture had dropped it as incidental.

The rule that survives the episode: when a fixture is built from a
hunt's reproduction, carry EVERY act the hunt performed until each
omission is proven harmless. A reproduction is a measured path
through half a dozen interacting keepers, and the acts that look like
scaffolding are usually the ones disabling a keeper the entry needs
disabled.

AND THE AMBIGUOUS-ANCHOR REFUSAL DID ITS JOB TWICE THE SAME NIGHT: an
entry anchored on a call that two sites now share was refused rather
than silently mutating the first -- once fixed by anchoring at the
shared HELPER (which kills both sites' protection at one line), and
once by widening the anchor with a neighbouring line unique to the
site the test actually drives. Prefer the helper where one exists:
a helper anchor cannot be split again by a third call site.

## AN ORACLE THAT READS A DEPENDENCY'S STORED POINTERS READS FREED MEMORY

2026-08-26, and it is the freed-temporary trap wearing its most
convincing disguise yet. A test asked whether the plugin keeps its
own output out of the region chooser, and read
`layer_combo.exceptedLayerList()` -- the list the combo was HANDED.
Under the mutation those entries are the stale pre-resume layers,
whose C++ objects are gone, so reading their ids was undefined: it
answered plausible stale ids on one run and SEGFAULTED on the next.
An entry over that oracle is flaky by construction, and its verdicts
were worthless in both directions.

THE REPAIR IS ALSO THE BETTER QUESTION. What the promise is about is
what the chooser OFFERS, so the test now walks the combo's own items
and asks which layers a user could pick. That is the user-facing
claim, it touches only live objects, and it made the entry catch
first time.

**ASK WHETHER YOUR ORACLE READS WHAT THE DEPENDENCY WAS TOLD OR WHAT
IT NOW SHOWS.** The first is a record that can outlive its subjects;
the second is what the person meets. This project already knows that
`ranges()` and `categories()` hand back copies and that a temporary
frees its contents -- this is the same family reached through a
widget's own accessor rather than a renderer's.

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
mutation workflow's coverage leg -- which runs the whole suite, for
its own reasons -- named them: green at the commit before, red at the
round's own commit, four tests, every one reproducible here on the
first attempt.

THE FOUR WERE NOT SUBTLE. Open the plugin in a project that already
holds a map and every row came up blank, on "Single colour", beside
layers plainly drawn from a column; Generate then refused for want of
a variable. That is the commonest journey there is, and the round that
broke it had eight hunts pointed at the same code.

**A HUNT ASKS WHAT MIGHT BE BROKEN; THE SUITE ASKS WHAT IS.** Both
rounds of hunts here were aimed at the fresh work and found real
defects in it, which is what this file already promises they do. What
neither can do is notice that a repair has broken a promise made
somewhere else -- and neither can the catalogue, which proves the
entry's own test.

**AND A TEST NOBODY RUNS CAN BE CONTRADICTED WITHOUT ANYBODY
NOTICING.** One of the four was a new test asserting the OPPOSITE of a
registered one about the same journey: the round-nine test required a
record to stay empty, the older test required it to be filled. Both
were green in their own runs; nothing but the whole suite puts the two
in the same room. When a fix changes what a record holds, grep the
suite for other tests that read that record before writing a new one.

## A TEST THAT PINS A NAME PINS IT TWICE: AS TEXT AND AS A SYMBOL

2026-08-26, and it cost a release gate. Output groups were given
names carrying their dataset, and the suite was swept for the old name
by grepping the literal. Six sites turned up and were mended. The
candidate's own suite then failed on two tests that pin the same name
through `GROUP_BASE_NAME`, which no search for the string could ever
have found.

Both were repaired to state their rule rather than the string, and
both are better tests for it: one asks the PROJECT which groups it
holds rather than comparing against a constant that happened to match,
and the other asserts the thing it was really about, that a first run
gets no counter appended. Neither will move again when the convention
does.

**THE HABIT IS CHEAP: when a test compares against a name, ask whether
the name has a symbol, and sweep for both.** And when an assertion
pins a literal that the product composes, prefer stating the rule --
this file's own standing advice about composing an expected sentence
from the function the product uses, arriving at a name instead of a
notice.

## BOTH BRANCHES OF THAT QUESTION CAME UP THE SAME NIGHT

The rule for a survivor is to break every route at once: if the test
fails, the axis is live and redundantly held; if it passes, the
assertion is the problem after all. Two entries were judged that way
on 2026-08-26 and they came out on opposite sides, which is worth
recording because the reflex is to expect one answer.

The categorical attribution entry FAILED with both routes broken, so
its axis is live and its redundancy was written at the test.

The landing's refusal to write over another dataset's map PASSED with
both routes broken -- so nothing was redundant and the test had simply
stopped reaching the case. What protects that journey now is the
BINDING: the run lands in the group the dialog is working in, and
after a switch the dialog is not working in the other dataset's group
at all. The refusal is a second line of defence behind it, which is a
perfectly good thing to have and not something a test was watching.
The repair is the one this file already prescribes for a guard nobody
has watched fail: DRIVE THE DOOR THE GUARD IS ABOUT. The test now puts
the dialog inside a group whose layers say they came from another
dataset -- what a reopened two-dataset project looks like from the
inside -- and requires the landing to build beside it. The entry
catches again.

**A FIRST LINE OF DEFENCE MOVING IN FRONT OF A GUARD LOOKS EXACTLY
LIKE THE GUARD WORKING.** When a fix lands near an older protection,
the older one's entry is worth re-judging: it may have stopped being
reachable without anybody weakening it.

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
and it is the shape this project meets most often.

A restyle was taught to write the GROUP's record, with a comment
arguing exactly why. The FILE's record was given its write hours
later, by a different commit, on the landing path alone -- so it
inherited the very gap the first write had closed. The file's STYLES
were updated by a restyle and its RECORD was not, so the file
disagreed with itself and a colleague opening it resumed a design the
user had abandoned.

And a record restored by a group switch was read by nobody, because
the WIDGET that `_assignments` reads was repopulated without being
re-selected from it -- the fix its neighbour in the same table had
been given eight days earlier.

So: when you mend one store of a fact, list every store that already
held it, and check each. The list is usually short and it is never
empty; the second store is the one nobody is looking at.

## TWO RECORDS JOINED END TO END HAVE THE SHAPE OF ONE

(2026-08-27, row 31 of that day's ledger.) The changelog is one text
shown by two renderers, and the test written for exactly that danger
reads the current version's entry and requires an opening paragraph
followed by bold bullets. Every assertion in it passed on a body that
was nine tenths another release: the 0.24.4 entry had swallowed the
whole of 0.24.3, because opening the new section indented the previous
version's header with its `changelog=` prefix still on it and the
boundary is a lookahead for a line beginning with digits.

An entry twice as long as it should be still opens with a paragraph
and still continues in bullets. Shape is preserved by concatenation,
which is what makes a shape assertion blind here -- and blind in the
one direction that ships another release's notes under this one's
heading.

So where a tool cuts one record out of a document holding several,
assert the CUT rather than the shape: that the piece stops where the
next one starts, and that it carries none of its neighbour's
furniture -- no second header, no field name, nothing that only
appears at a boundary. The widened guard walks every version header in
the field and asks that of each, and the catalogue entry
`an-entry-stops-where-the-next-version-starts` stands on the boundary
itself, so a boundary quietly relaxed is a red suite rather than a
release page nobody rereads.

The same question is worth putting to any test of a parser, a
splitter or a section extractor: what does it assert about the END?

## AN ENTRY GOES BLIND WHEN A CONVERSION EDITS ITS TEST'S FIXTURE

2026-08-27, and it is the sharpest single finding of the branch's full
catalogue sweep, because it is the only one of forty-three survivors
that this branch caused.

`an-embedded-source-is-an-opt-in` mutates the plugin into embedding
the region data ALWAYS, and its test is what proves that unticking
"Include the source data" keeps a private copy of somebody's data out
of a file they send on. It caught at `v0.24.3`. It survives now, and
the code it guards is correct: the day's Save conversion inserted
`opt_embed_source.setChecked(True)` into that test's fixture, so the
test ticks the box, and a mutation that embeds always is invisible to
a test that asked for embedding.

That is this file's own rule — A FIXTURE'S CHOICE MUST DIFFER FROM THE
DEFAULT THE MUTATION FALLS BACK TO — arriving by a route the rule did
not anticipate. Nobody wrote a bad fixture. A mechanical sweep across
six hundred tests changed one line of an unrelated test's setup, which
is exactly what a faithful conversion is supposed to do, and the
casualty was a guard three thousand lines away that nothing connected
to it.

**SO WHEN A CONVERSION TOUCHES FIXTURES EN MASSE, RE-JUDGE THE
CATALOGUE, NOT ONLY THE SUITE.** A green suite says the conversion
preserved what the tests assert. It cannot say whether they can still
FAIL, and that is the question the catalogue exists to answer.

**AND THE REPAIR TOOK TWO MOVES, WHICH IS THE OTHER HALF.** Re-aiming
the entry at the test that stages the box UNTICKED was the obvious fix
and was not enough: it still survived, because the day's ruling had
given the fact a SECOND WRITER. `_embed_or_drop_the_source` asks the
box itself and drops the table on the other arm, so the callee's guard
is never reached on the journey that matters, and mutating it changes
nothing a test can see. Anchored at the CALLER, where the decision now
lives, it catches. Ask of any re-aimed entry whether the site it names
is still the site that DECIDES, or has become a second line of defence
behind one.

## FOUR WAYS A TEST DID NOT REACH THE JOURNEY ITS ENTRY NAMED

2026-08-28, deciding all thirty-four survivors of the branch's full
catalogue sweep. Eleven of them were this: the test is sound, its
assertions are sharp, and the journey it drives never touches the code
the entry stands on. Each is worth knowing on sight, because each
reads as a weak test and none is.

**A GENERATE THAT CHANGES NO GEOMETRY IS A RESTYLE.** Picking a style
back, choosing a ramp, moving a class count: none of them re-tiles, so
`_generate` takes the fast path and the LANDING never runs. A test
that says "and then Generate" may therefore never reach the landing's
own rules -- the plugin says so itself, `GEN-GATE restyled-instead`,
which is why those exits were made to name themselves. Nudge the
spacing when the landing is the subject.

**A CLASSIFY ON A CONSTANT COLUMN NOW DEFERS.** The follow path drops
out at `DROP <tid> deferring` above the count guard, so a test written
when that route reached the guard no longer does. When a ruling
changes what a journey MEANS, the tests that drove it keep passing and
stop arriving.

**SELECTING THE LAYER THAT IS ALREADY SELECTED STAGES NO CHOICE.** A
reopened dialog has adopted its own output and its region with it, so
`setLayer(region)` fires nothing and any clause about what a first
choice means is unreachable. Pick something else first.

**A TEST CAN ONLY TELL WHERE A VALUE IS READ FROM WHEN THE TWO SOURCES
DISAGREE.** The deferral-opacity arms set the cell to 30 and re-tiled,
by which time the LAYER also held 0.3 -- so taking the cell's number
and taking the old layer's gave the same answer and the entry could
not fail either way. With live update off the map is deliberately not
repainted, which makes the disagreement stageable rather than a race:
move the cell to 60, leave the layer at 0.3, and the landing has to
choose.

**AND THE PAIRS RULE BITES THE GUARD AS WELL AS THE PRODUCT.** A
handler with two follow exits, one per styling path, was guarded by a
test that drove only the categorized one; its graduated twin's entry
could never fail. The docstring of that very test says the twin
asymmetry produced most of its week's defects.

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
branch copying lines that entries stood on.

TWO WERE NOT AMBIGUOUS IN THE CODE AT ALL. A match is a SUBSTRING, and
eight spaces of indentation sit inside ten -- so an anchor written for
a statement at one nesting level also matched its more deeply nested
twin a few lines away, in the same method, doing the same thing on the
other arm of a branch. Nothing had been copied; the anchor had always
been able to match twice and nothing had noticed until a second twin
appeared. Bind the line ABOVE, which differs, rather than reaching for
more of the statement itself.

**AND THE GATE DOES NOT ASK THIS.** `check_standards` fails when a
catalogue anchor is ABSENT and says nothing when it is ambiguous --
so nine entries reported nothing while every gate was green, which is
the gate-that-checks-half-of-what-it-names shape met inside the
checker written to catch that shape in others. Whether it should also
require uniqueness is a change to a release gate and therefore the
maintainer's; it is recorded in the 2026-08-27 ledger rather than
done.

**WHERE THE SITE IS NOT OBVIOUS, THE TEST'S DOCSTRING SETTLES IT.**
The kept-result entry reads by its name like `_detach_from_the_group`;
its test says `_get_or_make_group` outright, in the sentence
explaining what went wrong. Narrowing nine anchors by reasoning from
their names would have aimed at least one of them at the wrong method
and produced a confident, wrong `caught`.

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
failure in the instrument.

`tests/run_tests.py` ends through `os._exit`, so when stdout is a
PIPE rather than a terminal it is block-buffered and the buffered
`PASS <name>` is discarded — `tools/run_some.py` exits 0 having
printed nothing at all, while a FAILURE's traceback reaches unbuffered
stderr and survives. So the green half of a proof reads as an empty
log and a zero exit, which is indistinguishable from a runner that
never started. `PYTHONUNBUFFERED=1` is what makes the verdict reach
the pipe. This is the same `os._exit` that stopped
`tools/coverage_report.py` writing a report until 2026-08-13.

AND THE TWO INTERPRETERS ARE NOT INTERCHANGEABLE, which cost the other
two attempts. A test runs under `$QGIS_PY`; an edit script and
`mutation_check` run under `env -u PYTHONHOME -u PYTHONPATH python3`.
Swapping them fails in two directions that both look like a broken
test: `env -u ... python3` hands back the SYSTEM interpreter, which
dies at `import qgis`, and a bare `python3` under a sourced QGIS
environment dies at `Failed to import encodings` having applied no
edit — so the run that follows measures unmodified code and reports
fiction.

THE COMMON CURE is the one this file already prescribes for probes:
keep the WHOLE output rather than filtering to the lines you expect,
and say out loud when a phase produced nothing. A filter that matches
nothing is indistinguishable from a run that said nothing, and here it
hid a traceback for two rounds.

## GUARD THE SHAPE, AND READ THE FILE WHOLE

2026-08-28. A sharded coverage recorder lost a whole shard at startup
to `if os.path.exists(x): os.remove(x)` -- three processes, all seeing
the file, two removing it, the third dying with FileNotFoundError
before running a single test. The one-site repair was obvious. The
GUARD was the interesting decision, and it found a second instance
within a minute.

**A RACE HAS A SHAPE, AND THE SHAPE IS WHAT RECURS.** A regression
test pinned to the reported line would pass forever while the next
person writes the same two lines somewhere else -- and they will,
because asking whether a file exists before removing it reads as
carefulness. The test therefore scans `tests/` and `tools/` for the
pattern and names every site. It went red immediately on
`tools/make_test_fixtures.py`, a script likelier to be run once and by
hand, which is exactly the site a targeted repair leaves standing and
exactly the site nobody would think to check.

**AND IT HAD TO READ EACH FILE WHOLE.** The pattern spans two lines,
so no per-line grep can see it -- which is how it survived every audit
this project has run over these same files. When a test looks for a
shape rather than a token, ask whether the shape fits on one line
before reaching for a line-oriented search.

**COUNT WHAT YOU SCANNED.** The test asserts it examined more than a
handful of files, because a walk that finds nothing and a walk that
looked at nothing are the same green -- this file's oldest and
cheapest rule, arriving in a lint-shaped test rather than a loop over
widgets.

**AND THE RED CAME FOR FREE.** A guard written for a defect that is
already fixed has to be watched failing, usually by breaking the fix
again. This one never needed that: the second site was still broken
when the test was first run, so its first execution WAS the red proof,
and the fix that followed turned it green.

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
got wrong, because every cheap explanation was available and all of
them were comfortable.

A per-test coverage re-record failed one test of 645, in a shard
running beside two others on a loaded machine. The candidate's own
suite had passed that test an hour before. It passed alone under the
plain harness; alone under the recorder's own instrumentation, twice;
and nine times over across three concurrent copies. Fourteen clean
runs against one failure, in a suite whose slowest tests wait on
debounces, is the exact shape of a timing-tuned test meeting a
different harness -- which this file already warns about twice.

**THE TELL WAS IN WHAT THE FAILURE SURVIVED.** `_settle` waits on the
EVENT -- no task in flight, no live timer, no preview timer -- and
reports a timeout in different words than the ones in the log. So the
dialog had genuinely finished, and the surplus layers were still
there afterwards. A test that read too early produces a different
sentence; this one had waited for quiet and then found the map
disagreeing with the table. **Ask what a failure SURVIVED before
ascribing it to timing**: a race the test merely lost cannot outlive
the thing settling.

**STAGE THE CONDITION; DO NOT MEASURE HOW OFTEN YOU LAND IN IT.** The
suite's case puts a run in flight, waits about 150 ms, and presses
Generate hoping the run is still going -- which on a fast machine it
is not, so the case silently becomes a different journey. Chasing the
frequency cost two full re-records and answered nothing. A probe that
asserted `_task is not None` in the same breath as the press
reproduced the defect FIRST TIME, on both arms, deterministically,
and the same staging is what the new guard uses. Where a case depends
on a window, close the window rather than sampling it.

**AND THE DEFECT WAS REAL AND THE SUITE'S RATHER THAN A USER'S**,
which is the correction this section needed and did not get until the
hunt round of the same evening measured it. The Generate button is
disabled for the whole of a run, so nothing a person does can enter
`_generate` with a task in flight; what does is the suite, which calls
the method directly here and in `test_race_double_generate`. The
mechanism below is exact and the fix is right as defence in depth. The
sentence that was wrong is the one claiming a person met it -- written
into four documents and into a candidate's tester notes before anybody
asked whether the journey was drivable. Measure the REACHABILITY as
separately as you measure the mechanism; one probe reading
`generate_btn.isEnabled()` mid-run settles it in five minutes. With
live update off, a
Generate pressed during a run was queued on the live-rerun flag and
handed to the live path, which returns whenever live update is off --
so the press was remembered and discarded in silence, leaving the
previous run's elements on the map under a table asking for a
different design. The suite reached that ground only when a machine
was slow enough to put the press inside the run. **A test that fails
rarely is a test that reaches something rarely, and what it reaches
may be a defect rather than a window.**

## AN ORACLE A NEVER-SHOWN WINDOW CANNOT ANSWER

The guard for the save's progress bar asserted `not
progress.isVisible()` before the save and again after it, and BOTH
halves passed with the repair mutated away. Offscreen -- which is
every runner and every CI job here -- a widget in a window nobody has
called `show()` on answers False to `isVisible` whatever anybody set,
so the assertion was true of the fixed software, of the broken
software, and of software that had never had a progress bar at all.

`setVisible` moves the explicit hidden flag, and `isHidden` is a
question such a window CAN answer. That is the whole repair.

What found it was the catalogue: the entry SURVIVED and said so. What
would not have found it is reading, because the assertion is
perfectly sensible-looking and the test passed. This project already
carries the rule from the drawing side -- `grab()` of a never-shown
dialog renders unreliable visibility, so probe state programmatically
-- and this is the same fact met from the ASKING side.

**Before asserting on a widget's appearance, ask whether an unshown
window can distinguish the two answers.** Geometry, enablement,
hidden-ness and text all survive; visibility, focus and paint do not.

## A LEG THAT RUNS AFTER THE STATE IT IS ABOUT

A test may drive exactly the right act and still assert nothing,
because the step before it destroyed the condition. The re-tile leg
of `test_taking_an_element_back_from_qgis_restyles_at_once` asserted
that a taken-back element is re-seeded rather than inheriting the
dock's renderer -- and it ran on the element the arm ABOVE had just
reclaimed, whose layer therefore wore the plugin's own renderer. The
landing had nothing rule-based to carry, so the assertion held
whatever the gate said. The catalogue triage of 2026-08-28 recorded
it as one of two bad trades at the time it was written, which is the
right way to leave a known-weak leg: named, not quietly kept.

**The repair was an ORDER, not another assertion.** Put the element
back into QGIS's hands; move the SPACING FIRST, so the restyle path
declines and the layer still holds the dock's renderer; only then
pick the style back; then run. Pick first and the restyle re-seeds in
place, and the re-tile that follows meets an element that was never
deferring.

Both premises are asserted out loud -- that the element is deferring
again, and that its layer still holds the dock's renderer at the
moment the run starts -- so the arm cannot drift back to measuring
nothing without saying so.

Ask of any multi-arm test: what STATE does this leg need, and does
the arm before it consume that state?

## STAGE WHAT A SECOND PROCESS LEAVES, NOT THE SECOND PROCESS

Some defects need another program: a colleague saving the shared
GeoPackage while your map is open cannot be driven from one process,
because a running QGIS serves its own cached pages of a file and
because the stale-table drop is gated on the file being the saver's
own -- a fresh dialog meeting somebody else's file does not own it,
so its drop returns at the first line and the precondition never
exists. The AUDIT for that defect therefore ran a whole second QGIS,
with a two-file rendezvous, and it was worth every second: the first
arrangement of it measured a journey where nothing was ever removed.

The SUITE does not do that, and should not. What a colleague leaves
behind is a FILE STATE -- our element's table gone, theirs in its
place -- and that state is stageable through the plugin's own file
machinery in a second. The rule this project already has for windows
applies to processes too: where a case depends on something you
cannot schedule, close the window rather than measuring how often you
land in it.

**Use the expensive instrument to learn what state to stage, then
stage it.** An audit that needs two processes is a good audit; a
registered test that needs two processes is a test that will be
quarantined the first time it is slow.

## PROVE THE QUANTITY THE FAILURE MEASURES

A guard can be careful, pass, and be about something else.

The ceiling guard of 2026-08-29 measured `minimumSizeHint().width()`.
The tests failing on Windows measured `dlg.width()` after `show()`.
Four different repairs to the window's width each made that guard
pass, and every one of them was inert or wrong on the platform that
was red -- the guard could not tell, because a minimum is not a
preferred size and a window opens at the latter.

Rewriting the guard to measure `dlg.width()` after `show()` did two
things at once. It reproduced the fault LOCALLY, at 3587px, in a state
that had been declared unreachable on this machine and needed one line
to reach -- set every column to 400px, and this machine is in the
position wide fonts put Windows in. And it made the next repair
testable here rather than by pushing to a runner and waiting.

**Ask of any guard: is this the number the red run prints?** Where it
is not, the guard is about something else, however reasonable it
looks. A guard that passes on four wrong repairs is not a weak guard;
it is a guard aimed at a different question.

The corollary is the cheaper half: **before saying a case cannot be
reproduced here, ask what the other machine has more of** -- wider
fonts, a slower disk, a different locale -- **and set that quantity
directly.** The fixture that reaches it is usually one line.

## BUILD THE FIXTURE THROUGH THE PRODUCT'S OWN DOOR

2026-08-29, and it produced two probes with OPPOSITE answers, both
mine, before the variable neither was controlling turned up.

Asked whether the vendored `Topology` works on weaves, the first probe
built units by handing the catalogue's raw spec straight to
`WeaveUnit(**spec)`. Twill and basket died IN THE CONSTRUCTOR --
`catalog.TILINGS_BY_N` stores a weave's passing pattern as the string
a person types, `1,2,2,1`, and `catalog.make_unit` is what parses it
through `get_over_under` -- so two of the four were reported as
unsupported by the library when they had never been built at all. A
fixture that cannot be constructed has measured nothing.

Rebuilt through `catalog.make_unit`, which is the door the dialog
itself uses, ALL FOUR failed instead -- and that reversal was the
useful signal rather than the answer. The two probes differed in more
than the door: `make_unit` also supplies `aspect=0.75`, the plugin's
own default, where the direct call took the library's. Sweeping that
one parameter settled it in a minute: aspect 1.0 carries a topology
and 0.95, 0.9 and 0.75 do not, because `Topology` requires a GAP-FREE
tiling and opening a weave up is exactly what aspect does. The same
answer arrives on the tiling side through the inset controls.

**TWO HABITS.** Build fixtures through the function the PRODUCT calls,
not through the library underneath it, because the product is where
the arguments are parsed and the defaults are chosen -- and those
defaults are frequently the thing under test without anybody saying
so. And when two of your own probes disagree, do not pick the
likelier: find what differs between them and vary it alone. Here the
disagreement was worth more than either verdict, since it named a
constraint neither probe had been looking for.

## A probe that cannot reach its own case (2026-08-31)

Three of the day's findings were probes, not products, and all three
had the same shape: the instrument was aimed a little to one side of
the thing it was about, and it reported health.

**A ceiling is the case, and filling PAST it measures the other
path.** The Messages log trims at 500. A log already at 500 keeps its
ROW COUNT UNCHANGED on the next message, so every cell write is an
overwrite -- which is what makes a `ResizeToContents` column
re-measure. A probe that filled to 560 made the count CHANGE on the
next message, took the cheap rebuild path, and read 4.8ms where the
real case reads 8,563ms. The catalogue entry aimed at the repair duly
SURVIVED. Fill to exactly the boundary, and say in the test why that
number and not a rounder one.

**A baseline inserted into a sequence can reset the sequence.** The
topology matrix chooses a class, chooses a verb, then clicks Apply.
A baseline Generate was added between the choosing and the click; it
lands a topology build whose landing resets the class combo and
refills the verb list, so every chosen EDGE verb became
`push_vertex`. Three cells could not fail. The demonstration is the
technique worth copying: break the three manipulations into no-ops
and check the verdicts MOVE -- they did not, while the sibling cell
under the same mutation went red.

**A control arm that also fails has measured nothing, and a treatment
that shares a route with its control measures the route.** An entry
mutating one of three callers of a gate survived, because changing
the element count repopulates the family list and the family handler
re-asks anyway. Aim an entry at the line where the answer is DECIDED,
not at a door into it; keep the other doors as defence in depth and
say so at the entry.

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

2026-08-31, round five. Counted because a day whose findings are mostly
its own instruments is a day nobody should act on -- and because every
one of these was made by somebody who had read the entry describing it
that morning.

**TWO ARMS SHARING ONE `QgsProject` IS A CONTAMINATED CONTROL, AND IT
READS AS MACHINE CONTENTION.** A two-arm probe ran its control first;
the treatment's dialog then met the control's output layers and its
topology never built, so the arm died on its own premise. That was
reported -- twice, out loud, before it was measured -- as six
concurrent hunts saturating the machine. It reproduced identically with
the machine idle. `QgsProject.instance().clear()` at the top of each
arm settled it in one line.
ASK OF ANY MULTI-ARM PROBE WHAT THE ARM BEFORE IT LEFT BEHIND, and
prefer an explanation you can test over one you can feel.

**A DISCRIMINATOR MUST NOT DISTURB THE THING IT DISCRIMINATES.** With
live update off the map deliberately does not follow the table, so
"saved the map on screen" and "did nothing at all" leave the same tiles
in the file. Deleting the file first to make its reappearance
meaningful left the layers naming a table that no longer existed, so
the save refused for a reason nothing to do with the defect. What
discriminated without disturbing anything was WHAT THE PLUGIN SAYS.

**A FILTER MATCHING A PHRASE COPIED OUT OF THE PRODUCT IS RETUNED BY
THE APPROVAL PIPELINE.** An arm counted messages containing `"cannot
carry"`; the maintainer reworded that notice the same afternoon,
`text_review --apply` wrote the new words into the source, and the
filter matched nothing -- so the arm counted zero and its "at most
once" assertion could not fail. Match on what a sentence is ABOUT (the
control's name) where there is no function to compose it from.

**A REPAIR THAT ENABLES A GUARDED WRITE MUST SUPPLY WHAT THE WRITE
DEMANDS.** Stopping a gate refusing a write changed nothing observable
three times running, because the write itself then declined for a
reason written at the write rather than at the gate. The only evidence
was a dump line behind a flag.

**A WIDENED PATTERN MUST BE RUN AGAINST THE CLEAN TREE.** Widening a
version check to match a claim rather than one phrasing of it caught
the planted fault AND produced two false alarms on a document that
names other versions correctly. A gate whose failures are mostly false
is one people learn to silence, so it was scoped to the files whose job
is to state the fact, with the reason at the line.

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

