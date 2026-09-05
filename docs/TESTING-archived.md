# Archive: TESTING.md

The full accounts cut out of `TESTING.md` by the archiving pass
(docs/DOC-ARCHIVING.md). Nothing here is a rule you must read
before working: `TESTING.md` carries every rule and the headline
of every lesson. This file carries the episode each one came
out of -- what was measured, what was tried first, what the
superseded form of a rule was.

READ IT WHEN `TESTING.md` points you here by id (T-1,
T-2, ...), when a rule surprises you and you want to
know what it cost, or when you are about to change a rule and
need to know what it was built to prevent. Ids are stable:
quote them, do not renumber them.

## Index

- **T-1** — THE HARNESS'S STYLE IS PART OF THE MEASUREMENT, EXACTLY AS ITS FONT IS  <sub>Lessons about testing, in full</sub>
- **T-2** — A GUARD CAN CHECK WHAT A COLUMN NEEDS AND NOT WHAT A WINDOW DOES  <sub>Lessons about testing, in full</sub>
- **T-3** — AN ATTRIBUTE THAT IS A VIEW CANNOT BE WATCHED BY REBINDING IT  <sub>Lessons about testing, in full</sub>
- **T-4** — THE HARNESS SETTING EVERY RUNNER SETS IS PART OF THE MEASUREMENT  <sub>Lessons about testing, in full</sub>
- **T-5** — A CONTROL ARM'S OWN ACT CAN TRAVEL INTO THE ARM IT CONTROLS  <sub>Lessons about testing, in full</sub>
- **T-6** — A MEASUREMENT THAT DOES NOT RESOLVE IS NOT A MEASUREMENT  <sub>Lessons about testing, in full</sub>
- **T-7** — A red suite can mean the software got SLOWER, and reading it as a hang costs the...  <sub>Lessons about testing, in full</sub>
- **T-8** — Assert the sentence the product composes, not a phrase copied out of it  <sub>Lessons about testing, in full</sub>
- **T-9** — A guard is not a guard until you have watched it fail  <sub>Lessons about testing, in full</sub>
- **T-10** — What a day of hunting one's own new code actually costs  <sub>Lessons about testing, in full</sub>
- **T-11** — Three ways to move a class boundary, and why none of them worked  <sub>Lessons about testing, in full</sub>
- **T-12** — Four ways a test passed while the product was broken, 2026-08-16  <sub>Lessons about testing, in full</sub>
- **T-13** — TEST A CONTROL BY TYPING INTO IT, NOT BY `setValue`  <sub>Lessons about testing, in full</sub>
- **T-14** — A test can pass while registered nowhere  <sub>Lessons about testing, in full</sub>
- **T-15** — Where a guard's expectation should come from, when the product is the only thing...  <sub>Lessons about testing, in full</sub>
- **T-16** — Instrument WHICH rebuild writes the record, and the fourth attempt lands  <sub>Lessons about testing, in full</sub>
- **T-17** — THE SECOND TRIGGER: when a fix AND its test are in, hunt that ground again  <sub>Lessons about testing, in full</sub>
- **T-18** — THE TRIGGER: point a hunt at a BATCH of new tests, per assertion  <sub>Lessons about testing, in full</sub>
- **T-19** — Tests written in haste, measured  <sub>Lessons about testing, in full</sub>
- **T-20** — The differential sweep: reproducing and sharding  <sub>Lessons about testing, in full</sub>
- **T-21** — What a second machine finds, and why it could not be found here  <sub>Lessons about testing, in full</sub>
- **T-22** — The artefact nobody opened  <sub>Lessons about testing, in full</sub>
- **T-23** — A test's name is a hypothesis about its own failure  <sub>Lessons about testing, in full</sub>
- **T-24** — Ceilings, and the two ways to get them wrong  <sub>Lessons about testing, in full</sub>
- **T-25** — A child process inherits the suite's own environment  <sub>Lessons about testing, in full</sub>
- **T-26** — WINDOWS CANNOT STAGE "THE FILE WENT AWAY WHILE THE LAYER WAS OPEN", and four tests...  <sub>Lessons, each paid for once, in full</sub>
- **T-27** — A workaround for someone else's bug needs a canary  <sub>Lessons, each paid for once, in full</sub>
- **T-28** — An invariant can demand that the software get it wrong  <sub>Lessons, each paid for once, in full</sub>
- **T-29** — A stub that collects nothing hides whatever passes through it  <sub>Lessons, each paid for once, in full</sub>
- **T-30** — A fixed wait after a run is a guess about two races  <sub>Lessons, each paid for once, in full</sub>
- **T-31** — "Immediately" is one interleaving out of many  <sub>Lessons, each paid for once, in full</sub>
- **T-32** — A test that passes is not a test that works  <sub>Lessons, each paid for once, in full</sub>
- **T-33** — Before believing a survivor is a gap, count the call sites  <sub>Lessons, each paid for once, in full</sub>
- **T-34** — Prefer one systematic test to many specific ones, where the property is general  <sub>Lessons, each paid for once, in full</sub>
- **T-35** — The environment can satisfy the thing under test  <sub>Lessons, each paid for once, in full</sub>
- **T-36** — AND WHERE IT DOES, THE TEST'S ANSWER CAN DEPEND ON HOW THE SUITE WAS SHARDED  <sub>Lessons, each paid for once, in full</sub>
- **T-37** — AN INVARIANT CHECKED IMMEDIATELY CANNOT TELL A DEFECT FROM A DEBOUNCE  <sub>Lessons, each paid for once, in full</sub>
- **T-38** — And it can satisfy the thing MEASURING the test, which is worse  <sub>Lessons, each paid for once, in full</sub>
- **T-39** — Never run two full suites at once, but do parallelise short runs  <sub>Lessons, each paid for once, in full</sub>
- **T-40** — A test whose coverage depends on the machine it runs on reports the machine, not the...  <sub>Lessons, each paid for once, in full</sub>
- **T-41** — When an attribution is a guess, report rather than gate  <sub>Lessons, each paid for once, in full</sub>
- **T-42** — CONVERTING A SUITE WHEN ONE ACT SPLITS INTO TWO  <sub>Lessons about testing, in full (continued)</sub>
- **T-43** — WHAT "THE FILE DID NOT CHANGE" MEANS, MEASURED  <sub>Lessons about testing, in full (continued)</sub>
- **T-44** — A matrix may balloon, because you are SAMPLING anyway  <sub>Lessons about testing, in full (continued)</sub>
- **T-45** — FIVE WAYS A PROBE OR A CELL FAILED TO REACH ITS OWN CASE IN ONE DAY  <sub>Lessons about testing, in full (continued)</sub>
- **T-46** — A CLEANUP THAT WORKS BY SIDE EFFECT IS A CLEANUP NOBODY WROTE  <sub>Lessons about testing, in full (continued)</sub>
- **T-47** — THE SWITCH MATRIX, AND WHAT ITS FIRST RUN TAUGHT  <sub>Lessons about testing, in full (continued)</sub>
- **T-48** — A MATRIX ASKS ABOUT RECORDS; ADD THE QUESTION ABOUT WHAT IS SEEN  <sub>Lessons about testing, in full (continued)</sub>
- **T-49** — THREE WAYS A GUARD FOR A VISUAL THING PASSES ON A BROKEN PRODUCT  <sub>Lessons about testing, in full (continued)</sub>
- **T-50** — AN INSTRUMENT IN THE USER'S HANDS BEATS SIX REPRODUCTIONS IN YOURS  <sub>Lessons about testing, in full (continued)</sub>
- **T-51** — Instrumentation that lies, and how it lied here  <sub>Lessons about testing, in full (continued)</sub>
- **T-52** — Two jobs that MUTATE one file must never run at once  <sub>Lessons about testing, in full (continued)</sub>
- **T-53** — A FIXTURE BUILT TO EXPLOIT A BUG DIES WHEN THE BUG IS FIXED  <sub>Lessons about testing, in full (continued)</sub>
- **T-54** — When an instrument disagrees with a hand-run, believe the hand-run  <sub>Lessons about testing, in full (continued)</sub>
- **T-55** — A TEST WHOSE SETUP REFRESHES THE THING UNDER TEST PASSES FOREVER  <sub>Lessons about testing, in full (continued)</sub>
- **T-56** — A REPRODUCTION THAT CANNOT REACH THE CASE REPORTS GOOD NEWS  <sub>Lessons about testing, in full (continued)</sub>
- **T-57** — TWO DEAD AXES OUT OF TWENTY-SIX, AND BOTH WERE SUBSUMED  <sub>Lessons about testing, in full (continued)</sub>
- **T-58** — FOUR WRONG HYPOTHESES ABOUT MY OWN TEST BEFORE THE PRODUCT WAS IN QUESTION  <sub>Lessons about testing, in full (continued)</sub>
- **T-59** — A JUDGEMENT BEHIND AN `if` IS A GREEN THAT SAYS NOTHING  <sub>Lessons about testing, in full (continued)</sub>
- **T-60** — A TEST WITH NO CATALOGUE ENTRY IS A TEST YOU BELIEVE  <sub>Lessons about testing, in full (continued)</sub>
- **T-61** — A FIXTURE THAT LETS THE PLUGIN DERIVE THE THING UNDER TEST  <sub>Lessons about testing, in full (continued)</sub>
- **T-62** — A GUARD MAY BE WRITTEN TWICE, AND THEN NEITHER HALF CAN BE KILLED  <sub>Lessons about testing, in full (continued)</sub>
- **T-63** — AN ENTRY PER AXIS, NOT PER TEST -- AND READ WHICH ASSERTION FIRED  <sub>Lessons about testing, in full (continued)</sub>
- **T-64** — A GUARD'S OWN FIRST DRAFT IS WHERE THE NEXT DEFECT IS  <sub>Lessons about testing, in full (continued)</sub>
- **T-65** — A RETIRED CONTRACT CAN GO ON PASSING BECAUSE THE ABSURD CASE FAILS FAST  <sub>Lessons about testing, in full (continued)</sub>
- **T-66** — AN ORACLE CAN BE GREEN BECAUSE OF THE DEFECT IT WILL LATER CATCH  <sub>Lessons about testing, in full (continued)</sub>
- **T-67** — PRESENCE IS NOT ORDER, AND A LATE CALL IS WORSE THAN A MISSING ONE  <sub>Lessons about testing, in full (continued)</sub>
- **T-68** — SILENCE IN A RECORD HAS MORE THAN ONE CAUSE; ASK WHICH READER MADE IT  <sub>Lessons about testing, in full (continued)</sub>
- **T-69** — THE ORDINARY ACT IS A BETTER ROUTE TO A DEFECT THAN THE INGENIOUS ONE  <sub>Lessons about testing, in full (continued)</sub>
- **T-70** — NOTHING IN A HUNT'S REPRODUCTION IS INCIDENTAL UNTIL PROVEN SO  <sub>Lessons about testing, in full (continued)</sub>
- **T-71** — AN ORACLE THAT READS A DEPENDENCY'S STORED POINTERS READS FREED MEMORY  <sub>Lessons about testing, in full (continued)</sub>
- **T-72** — A ROUND CAN PASS EVERY TEST IT WROTE AND BREAK FOUR IT DID NOT RUN  <sub>Lessons about testing, in full (continued)</sub>
- **T-73** — A TEST THAT PINS A NAME PINS IT TWICE: AS TEXT AND AS A SYMBOL  <sub>Lessons about testing, in full (continued)</sub>
- **T-74** — BOTH BRANCHES OF THAT QUESTION CAME UP THE SAME NIGHT  <sub>Lessons about testing, in full (continued)</sub>
- **T-75** — WHEN A REPAIR GIVES ONE STORE A NEW WRITE, ENUMERATE EVERY STORE  <sub>Lessons about testing, in full (continued)</sub>
- **T-76** — TWO RECORDS JOINED END TO END HAVE THE SHAPE OF ONE  <sub>Lessons about testing, in full (continued)</sub>
- **T-77** — AN ENTRY GOES BLIND WHEN A CONVERSION EDITS ITS TEST'S FIXTURE  <sub>Lessons about testing, in full (continued)</sub>
- **T-78** — FOUR WAYS A TEST DID NOT REACH THE JOURNEY ITS ENTRY NAMED  <sub>Lessons about testing, in full (continued)</sub>
- **T-79** — AN ANCHOR CAN BE AMBIGUOUS BY INDENTATION ALONE  <sub>Lessons about testing, in full (continued)</sub>
- **T-80** — SILENCE WITH EXIT 0 IS NOT A PASS  <sub>Lessons about testing, in full (continued)</sub>
- **T-81** — GUARD THE SHAPE, AND READ THE FILE WHOLE  <sub>Lessons about testing, in full (continued)</sub>
- **T-82** — ONE FAILURE IN FIFTEEN RUNS WAS NOT FLAKINESS  <sub>Lessons about testing, in full (continued)</sub>
- **T-83** — AN ORACLE A NEVER-SHOWN WINDOW CANNOT ANSWER  <sub>Lessons about testing, in full (continued)</sub>
- **T-84** — A LEG THAT RUNS AFTER THE STATE IT IS ABOUT  <sub>Lessons about testing, in full (continued)</sub>
- **T-85** — STAGE WHAT A SECOND PROCESS LEAVES, NOT THE SECOND PROCESS  <sub>Lessons about testing, in full (continued)</sub>
- **T-86** — PROVE THE QUANTITY THE FAILURE MEASURES  <sub>Lessons about testing, in full (continued)</sub>
- **T-87** — BUILD THE FIXTURE THROUGH THE PRODUCT'S OWN DOOR  <sub>Lessons about testing, in full (continued)</sub>
- **T-88** — A TEST THAT LOCATES A MOMENT BY COUNTING IS RE-AIMED BY A SLOWER MACHINE  <sub>Lessons about testing, in full (continued)</sub>
- **T-89** — A probe that cannot reach its own case (2026-08-31)  <sub>Lessons about testing, in full (continued)</sub>
- **T-90** — Five instrument faults in one day, every one already written here  <sub>Lessons about testing, in full (continued)</sub>
- **T-91** — A PREMISE ASKED IN THE SAME BREATH AS A SETTLE READS THE OLD STATE  <sub>Lessons about testing, in full (continued)</sub>
- **T-92** — THE DESIGN A TEST DRIVES CAN REFUSE THE CASE, AND A CLEAN RESULT THEN MEANS NOTHING  <sub>Lessons about testing, in full (continued)</sub>
- **T-93** — A CELL THAT CANNOT SET ITS OWN STAGE MUST SAY SO IN ITS OWN WORDS  <sub>Lessons about testing, in full (continued)</sub>
- **T-94** — A PREMISE THAT FAILS ELSEWHERE MUST CARRY WHAT HAPPENED, NOT WHAT IT EXPECTED  <sub>Lessons about testing, in full (continued)</sub>
- **T-95** — FOUR INSTRUMENT FAULTS IN ONE ROUND, AND WHAT EACH LOOKED LIKE  <sub>Lessons about testing, in full (continued)</sub>
- **T-96** — A WAITER THAT RETURNS ON A STALE ANSWER, AND A QUEUE THAT DEFERS  <sub>Lessons about testing, in full (continued)</sub>
- **T-97** — A SKIP WITHOUT A LINE IS A CELL THAT NEVER EXISTED  <sub>Lessons about testing, in full (continued)</sub>
- **T-98** — STAGING AND ASSERTING ARE NOT THE SAME MOVE, AND I CONFUSED THEM  <sub>Lessons about testing, in full (continued)</sub>
- **T-99** — A FAMILY GUARD EARNS ITS KEEP ON FILES THAT DID NOT EXIST YET  <sub>Lessons about testing, in full (continued)</sub>
- **T-100** — ONE OWNER FOR "IS IT QUIET", AND THE TEST THAT MUST NOT ASK IT  <sub>Lessons about testing, in full (continued)</sub>
- **T-101** — AIM AT A DRAWING BY ASKING THE PRODUCT, NOT BY COMPUTING A POINT  <sub>Lessons about testing, in full (continued)</sub>
- **T-102** — READ A VERDICT AND ITS ORACLE IN ONE BREATH  <sub>Lessons about testing, in full (continued)</sub>
- **T-103** — A REPAIR CAN MOVE THE JOURNEY ITS OWN GUARD DRIVES  <sub>Lessons about testing, in full (continued)</sub>
- **T-104** — THREE PREMISES THAT WERE BETS ON THE MACHINE  <sub>Lessons about testing, in full (continued)</sub>
- **T-105** — A CORRELATION WITH YOUR OWN COMMIT IS A HYPOTHESIS  <sub>Lessons about testing, in full (continued)</sub>
- **T-106** — FOUR FIXTURES THAT COULD NOT REACH THEIR OWN CASE, IN ONE DAY  <sub>Lessons about testing, in full (continued)</sub>
- **T-107** — A WAITER ANSWERS "IS ANYTHING OUTSTANDING", WHICH IS NOT "DID IT HAPPEN"  <sub>Lessons about testing, in full (continued)</sub>
- **T-108** — A RESTORE HELD BY TWO WRITERS CAN ONLY BE JUDGED WHERE ONE DOES NOT RUN  <sub>Lessons about testing, in full (continued)</sub>
- **T-109** — A UNIFORM VERDICT CAN BE THE ANSWER RATHER THAN THE INSTRUMENT  <sub>Lessons about testing, in full (continued)</sub>
- **T-110** — A GATE THAT CANNOT START IS NOT A GATE THAT ANSWERED  <sub>Lessons about testing, in full (continued)</sub>
- **T-111** — A PROBE'S CONTROL MUST MOVE ONE TERM, AND AN INSTRUMENT MUST ASK THE PRODUCT ITS OWN...  <sub>Lessons about testing, in full (continued)</sub>
- **T-112** — A READING TAKEN BEFORE THE AIMING IS A BET ON THE MACHINE  <sub>Lessons about testing, in full (continued)</sub>
- **T-113** — AN ALLOWANCE SIZED ON THIS MAC IS AN ALLOWANCE THIS MAC WILL NEVER MEET  <sub>Lessons about testing, in full (continued)</sub>
- **T-114** — A PREDICTION IS AN AXIS, AND A WRONG AXIS IS OBEYED FAITHFULLY  <sub>Lessons about testing, in full (continued)</sub>
- **T-115** — AN INERT MUTATION AND A WEAK TEST BOTH REPORT SURVIVED, AND ONE ROUND PRODUCED BOTH  <sub>Lessons about testing, in full (continued)</sub>
- **T-116** — A RATE FROM TOO FEW DRAWS, PUBLISHED TWICE IN ONE HOUR  <sub>Lessons about testing, in full (continued)</sub>
- **T-117** — A GUARD CAN BE AIMED AT A STATE WITHOUT KNOWING WHAT PRODUCES IT  <sub>Lessons about testing, in full (continued)</sub>
- **T-118** — A SURVIVOR NAMED THE ARM THAT WAS MISSING  <sub>Lessons about testing, in full (continued)</sub>


## Lessons about testing, in full
- **T-119** — The 373 probes, the eleven doubled prefixes, and the four faults of one evening  <sub>Lessons, in full</sub>

- **T-120** — The claim that ran the other way, and what went in the ledger instead  <sub>Lessons, in full</sub>

- **T-121** — The three clean probes, and the memory URI that could not collide  <sub>Lessons, in full</sub>

- **T-122** — What each differential instrument actually found, one by one  <sub>Lessons, in full</sub>

- **T-123** — The three tests written around a defect, and what each pinned  <sub>Lessons, in full</sub>

- **T-124** — The nineteen tests the reduction moved, and the one that knew why  <sub>Lessons, in full</sub>

- **T-125** — The fixture accident test_metamorphic_variable_permutation was passing on  <sub>Lessons, in full</sub>

- **T-126** — The three sibling-path defects of 2026-08-13, each in full  <sub>Lessons, in full</sub>

- **T-127** — The 37-of-50 survivor breakdown behind the table-test shape  <sub>Lessons, in full</sub>

- **T-128** — Why a table test flatters a mutation score, and the spacing default that proves it  <sub>Lessons, in full</sub>

- **T-129** — The first test map's counts, kept as history  <sub>Lessons, in full</sub>

- **T-130** — The 0.024ms ramp lookup that fitted the stall perfectly and was innocent  <sub>Lessons, in full</sub>

- **T-131** — The contention factor that knew about sharding and nothing about the platform  <sub>Lessons, in full</sub>


### T-1 — THE HARNESS'S STYLE IS PART OF THE MEASUREMENT, EXACTLY AS ITS FONT IS

<sub>Cut from `TESTING.md`, lines 70–109 of the
2026-09-05 revision.</sub>

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

### T-2 — A GUARD CAN CHECK WHAT A COLUMN NEEDS AND NOT WHAT A WINDOW DOES

<sub>Cut from `TESTING.md`, lines 111–140 of the
2026-09-05 revision.</sub>

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

### T-3 — AN ATTRIBUTE THAT IS A VIEW CANNOT BE WATCHED BY REBINDING IT

<sub>Cut from `TESTING.md`, lines 142–163 of the
2026-09-05 revision.</sub>

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

### T-4 — THE HARNESS SETTING EVERY RUNNER SETS IS PART OF THE MEASUREMENT

<sub>Cut from `TESTING.md`, lines 165–196 of the
2026-09-05 revision.</sub>

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

### T-5 — A CONTROL ARM'S OWN ACT CAN TRAVEL INTO THE ARM IT CONTROLS

<sub>Cut from `TESTING.md`, lines 198–225 of the
2026-09-05 revision.</sub>

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

### T-6 — A MEASUREMENT THAT DOES NOT RESOLVE IS NOT A MEASUREMENT

<sub>Cut from `TESTING.md`, lines 246–269 of the
2026-09-05 revision.</sub>

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

### T-7 — A red suite can mean the software got SLOWER, and reading it as a hang costs the...

<sub>Cut from `TESTING.md`, lines 291–335 of the
2026-09-05 revision.</sub>

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

### T-8 — Assert the sentence the product composes, not a phrase copied out of it

<sub>Cut from `TESTING.md`, lines 337–367 of the
2026-09-05 revision.</sub>

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

### T-9 — A guard is not a guard until you have watched it fail

<sub>Cut from `TESTING.md`, lines 369–417 of the
2026-09-05 revision.</sub>

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

### T-10 — What a day of hunting one's own new code actually costs

<sub>Cut from `TESTING.md`, lines 419–448 of the
2026-09-05 revision.</sub>

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

### T-11 — Three ways to move a class boundary, and why none of them worked

<sub>Cut from `TESTING.md`, lines 450–512 of the
2026-09-05 revision.</sub>

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

### T-12 — Four ways a test passed while the product was broken, 2026-08-16

<sub>Cut from `TESTING.md`, lines 514–555 of the
2026-09-05 revision.</sub>

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

### T-13 — TEST A CONTROL BY TYPING INTO IT, NOT BY `setValue`

<sub>Cut from `TESTING.md`, lines 557–598 of the
2026-09-05 revision.</sub>

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

### T-14 — A test can pass while registered nowhere

<sub>Cut from `TESTING.md`, lines 600–621 of the
2026-09-05 revision.</sub>

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

### T-15 — Where a guard's expectation should come from, when the product is the only thing...

<sub>Cut from `TESTING.md`, lines 623–658 of the
2026-09-05 revision.</sub>

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

### T-16 — Instrument WHICH rebuild writes the record, and the fourth attempt lands

<sub>Cut from `TESTING.md`, lines 660–688 of the
2026-09-05 revision.</sub>

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

### T-17 — THE SECOND TRIGGER: when a fix AND its test are in, hunt that ground again

<sub>Cut from `TESTING.md`, lines 690–735 of the
2026-09-05 revision.</sub>

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

### T-18 — THE TRIGGER: point a hunt at a BATCH of new tests, per assertion

<sub>Cut from `TESTING.md`, lines 737–788 of the
2026-09-05 revision.</sub>

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

### T-19 — Tests written in haste, measured

<sub>Cut from `TESTING.md`, lines 790–820 of the
2026-09-05 revision.</sub>

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

### T-20 — The differential sweep: reproducing and sharding

<sub>Cut from `TESTING.md`, lines 822–842 of the
2026-09-05 revision.</sub>

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

### T-21 — What a second machine finds, and why it could not be found here

<sub>Cut from `TESTING.md`, lines 1218–1269 of the
2026-09-05 revision.</sub>

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

### T-22 — The artefact nobody opened

<sub>Cut from `TESTING.md`, lines 1271–1296 of the
2026-09-05 revision.</sub>

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

### T-23 — A test's name is a hypothesis about its own failure

<sub>Cut from `TESTING.md`, lines 1298–1323 of the
2026-09-05 revision.</sub>

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

### T-24 — Ceilings, and the two ways to get them wrong

<sub>Cut from `TESTING.md`, lines 1391–1413 of the
2026-09-05 revision.</sub>

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

### T-25 — A child process inherits the suite's own environment

<sub>Cut from `TESTING.md`, lines 1415–1436 of the
2026-09-05 revision.</sub>

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


## Lessons, each paid for once, in full

### T-26 — WINDOWS CANNOT STAGE "THE FILE WENT AWAY WHILE THE LAYER WAS OPEN", and four tests...

<sub>Cut from `TESTING.md`, lines 1449–1472 of the
2026-09-05 revision.</sub>

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

### T-27 — A workaround for someone else's bug needs a canary

<sub>Cut from `TESTING.md`, lines 1474–1485 of the
2026-09-05 revision.</sub>

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

### T-28 — An invariant can demand that the software get it wrong

<sub>Cut from `TESTING.md`, lines 1495–1506 of the
2026-09-05 revision.</sub>

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

### T-29 — A stub that collects nothing hides whatever passes through it

<sub>Cut from `TESTING.md`, lines 1516–1530 of the
2026-09-05 revision.</sub>

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

### T-30 — A fixed wait after a run is a guess about two races

<sub>Cut from `TESTING.md`, lines 1532–1548 of the
2026-09-05 revision.</sub>

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

### T-31 — "Immediately" is one interleaving out of many

<sub>Cut from `TESTING.md`, lines 1550–1560 of the
2026-09-05 revision.</sub>

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

### T-32 — A test that passes is not a test that works

<sub>Cut from `TESTING.md`, lines 1585–1602 of the
2026-09-05 revision.</sub>

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

### T-33 — Before believing a survivor is a gap, count the call sites

<sub>Cut from `TESTING.md`, lines 1604–1612 of the
2026-09-05 revision.</sub>

**Before believing a survivor is a gap, count the call sites.**
Deleting one of several redundant calls leaves the others to do the
work, so no test can discriminate and none should be contorted into
trying. `_update_layer_exclusions()` is called from THREE places -- the
constructor, project adoption, and after every run: deleting the constructor's call is invisible to
any test that generates first, and visible only to a dialog opened on
a project that already holds output. That distinction is the whole
test. Where the second call site turns out to be genuinely redundant,
delete the code rather than defend it.

### T-34 — Prefer one systematic test to many specific ones, where the property is general

<sub>Cut from `TESTING.md`, lines 1620–1632 of the
2026-09-05 revision.</sub>

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

### T-35 — The environment can satisfy the thing under test

<sub>Cut from `TESTING.md`, lines 1640–1648 of the
2026-09-05 revision.</sub>

**The environment can satisfy the thing under test.** QGIS stores
colour ramps in the user's profile, so on a machine that has run the
plugin before, its palettes are already installed and a test that
merely asserts they are present passes no matter what the installer
does. Create the condition the test needs -- remove one palette, then
require the installer to put it back -- rather than assuming a clean
machine. The same caution applies anywhere state outlives the process:
the QGIS style, the plugin's own settings, a GeoPackage left behind by
an earlier test.

### T-36 — AND WHERE IT DOES, THE TEST'S ANSWER CAN DEPEND ON HOW THE SUITE WAS SHARDED

<sub>Cut from `TESTING.md`, lines 1650–1661 of the
2026-09-05 revision.</sub>

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

### T-37 — AN INVARIANT CHECKED IMMEDIATELY CANNOT TELL A DEFECT FROM A DEBOUNCE

<sub>Cut from `TESTING.md`, lines 1663–1673 of the
2026-09-05 revision.</sub>

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

### T-38 — And it can satisfy the thing MEASURING the test, which is worse

<sub>Cut from `TESTING.md`, lines 1675–1700 of the
2026-09-05 revision.</sub>

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

### T-39 — Never run two full suites at once, but do parallelise short runs

<sub>Cut from `TESTING.md`, lines 1746–1754 of the
2026-09-05 revision.</sub>

**Never run two full suites at once**, but do parallelise short runs.
Two QGIS processes tiling and rendering slow each other to a crawl and
the result reads as a hang; one release was abandoned at forty minutes
for exactly this. Mutation judging is different work: measured, six
mutants took thirteen minutes serially and seven with three workers,
with identical verdicts. Per-mutant times still inflate 15-50%, so
watch the stall count — a mutant slowed past the watchdog's patience
is recorded as caught, which means contention can quietly flatter a
mutation score.

### T-40 — A test whose coverage depends on the machine it runs on reports the machine, not the...

<sub>Cut from `TESTING.md`, lines 1760–1770 of the
2026-09-05 revision.</sub>

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

### T-41 — When an attribution is a guess, report rather than gate

<sub>Cut from `TESTING.md`, lines 1781–1791 of the
2026-09-05 revision.</sub>

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


## Lessons about testing, in full (continued)

### T-42 — CONVERTING A SUITE WHEN ONE ACT SPLITS INTO TWO

<sub>Cut from `TESTING.md`, lines 1888–1947 of the
2026-09-05 revision.</sub>

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

### T-43 — WHAT "THE FILE DID NOT CHANGE" MEANS, MEASURED

<sub>Cut from `TESTING.md`, lines 1949–1976 of the
2026-09-05 revision.</sub>

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

### T-44 — A matrix may balloon, because you are SAMPLING anyway

<sub>Cut from `TESTING.md`, lines 2032–2078 of the
2026-09-05 revision.</sub>

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

### T-45 — FIVE WAYS A PROBE OR A CELL FAILED TO REACH ITS OWN CASE IN ONE DAY

<sub>Cut from `TESTING.md`, lines 2080–2125 of the
2026-09-05 revision.</sub>

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

### T-46 — A CLEANUP THAT WORKS BY SIDE EFFECT IS A CLEANUP NOBODY WROTE

<sub>Cut from `TESTING.md`, lines 2146–2168 of the
2026-09-05 revision.</sub>

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

### T-47 — THE SWITCH MATRIX, AND WHAT ITS FIRST RUN TAUGHT

<sub>Cut from `TESTING.md`, lines 2207–2231 of the
2026-09-05 revision.</sub>

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

### T-48 — A MATRIX ASKS ABOUT RECORDS; ADD THE QUESTION ABOUT WHAT IS SEEN

<sub>Cut from `TESTING.md`, lines 2233–2276 of the
2026-09-05 revision.</sub>

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

### T-49 — THREE WAYS A GUARD FOR A VISUAL THING PASSES ON A BROKEN PRODUCT

<sub>Cut from `TESTING.md`, lines 2278–2307 of the
2026-09-05 revision.</sub>

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

### T-50 — AN INSTRUMENT IN THE USER'S HANDS BEATS SIX REPRODUCTIONS IN YOURS

<sub>Cut from `TESTING.md`, lines 2309–2334 of the
2026-09-05 revision.</sub>

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

### T-51 — Instrumentation that lies, and how it lied here

<sub>Cut from `TESTING.md`, lines 2355–2377 of the
2026-09-05 revision.</sub>

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

### T-52 — Two jobs that MUTATE one file must never run at once

<sub>Cut from `TESTING.md`, lines 2398–2420 of the
2026-09-05 revision.</sub>

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

### T-53 — A FIXTURE BUILT TO EXPLOIT A BUG DIES WHEN THE BUG IS FIXED

<sub>Cut from `TESTING.md`, lines 2433–2458 of the
2026-09-05 revision.</sub>

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

### T-54 — When an instrument disagrees with a hand-run, believe the hand-run

<sub>Cut from `TESTING.md`, lines 2519–2550 of the
2026-09-05 revision.</sub>

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

### T-55 — A TEST WHOSE SETUP REFRESHES THE THING UNDER TEST PASSES FOREVER

<sub>Cut from `TESTING.md`, lines 2552–2586 of the
2026-09-05 revision.</sub>

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

### T-56 — A REPRODUCTION THAT CANNOT REACH THE CASE REPORTS GOOD NEWS

<sub>Cut from `TESTING.md`, lines 2588–2622 of the
2026-09-05 revision.</sub>

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

### T-57 — TWO DEAD AXES OUT OF TWENTY-SIX, AND BOTH WERE SUBSUMED

<sub>Cut from `TESTING.md`, lines 2624–2650 of the
2026-09-05 revision.</sub>

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

### T-58 — FOUR WRONG HYPOTHESES ABOUT MY OWN TEST BEFORE THE PRODUCT WAS IN QUESTION

<sub>Cut from `TESTING.md`, lines 2652–2698 of the
2026-09-05 revision.</sub>

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

### T-59 — A JUDGEMENT BEHIND AN `if` IS A GREEN THAT SAYS NOTHING

<sub>Cut from `TESTING.md`, lines 2700–2728 of the
2026-09-05 revision.</sub>

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

### T-60 — A TEST WITH NO CATALOGUE ENTRY IS A TEST YOU BELIEVE

<sub>Cut from `TESTING.md`, lines 2730–2750 of the
2026-09-05 revision.</sub>

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

### T-61 — A FIXTURE THAT LETS THE PLUGIN DERIVE THE THING UNDER TEST

<sub>Cut from `TESTING.md`, lines 2752–2781 of the
2026-09-05 revision.</sub>

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

### T-62 — A GUARD MAY BE WRITTEN TWICE, AND THEN NEITHER HALF CAN BE KILLED

<sub>Cut from `TESTING.md`, lines 2783–2817 of the
2026-09-05 revision.</sub>

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

### T-63 — AN ENTRY PER AXIS, NOT PER TEST -- AND READ WHICH ASSERTION FIRED

<sub>Cut from `TESTING.md`, lines 2819–2859 of the
2026-09-05 revision.</sub>

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

### T-64 — A GUARD'S OWN FIRST DRAFT IS WHERE THE NEXT DEFECT IS

<sub>Cut from `TESTING.md`, lines 2861–2883 of the
2026-09-05 revision.</sub>

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

### T-65 — A RETIRED CONTRACT CAN GO ON PASSING BECAUSE THE ABSURD CASE FAILS FAST

<sub>Cut from `TESTING.md`, lines 2885–2937 of the
2026-09-05 revision.</sub>

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

### T-66 — AN ORACLE CAN BE GREEN BECAUSE OF THE DEFECT IT WILL LATER CATCH

<sub>Cut from `TESTING.md`, lines 2939–2974 of the
2026-09-05 revision.</sub>

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

### T-67 — PRESENCE IS NOT ORDER, AND A LATE CALL IS WORSE THAN A MISSING ONE

<sub>Cut from `TESTING.md`, lines 2976–3015 of the
2026-09-05 revision.</sub>

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

### T-68 — SILENCE IN A RECORD HAS MORE THAN ONE CAUSE; ASK WHICH READER MADE IT

<sub>Cut from `TESTING.md`, lines 3017–3047 of the
2026-09-05 revision.</sub>

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

### T-69 — THE ORDINARY ACT IS A BETTER ROUTE TO A DEFECT THAN THE INGENIOUS ONE

<sub>Cut from `TESTING.md`, lines 3064–3091 of the
2026-09-05 revision.</sub>

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

### T-70 — NOTHING IN A HUNT'S REPRODUCTION IS INCIDENTAL UNTIL PROVEN SO

<sub>Cut from `TESTING.md`, lines 3126–3153 of the
2026-09-05 revision.</sub>

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

### T-71 — AN ORACLE THAT READS A DEPENDENCY'S STORED POINTERS READS FREED MEMORY

<sub>Cut from `TESTING.md`, lines 3155–3178 of the
2026-09-05 revision.</sub>

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

### T-72 — A ROUND CAN PASS EVERY TEST IT WROTE AND BREAK FOUR IT DID NOT RUN

<sub>Cut from `TESTING.md`, lines 3230–3260 of the
2026-09-05 revision.</sub>

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

### T-73 — A TEST THAT PINS A NAME PINS IT TWICE: AS TEXT AND AS A SYMBOL

<sub>Cut from `TESTING.md`, lines 3262–3283 of the
2026-09-05 revision.</sub>

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

### T-74 — BOTH BRANCHES OF THAT QUESTION CAME UP THE SAME NIGHT

<sub>Cut from `TESTING.md`, lines 3285–3313 of the
2026-09-05 revision.</sub>

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

### T-75 — WHEN A REPAIR GIVES ONE STORE A NEW WRITE, ENUMERATE EVERY STORE

<sub>Cut from `TESTING.md`, lines 3330–3350 of the
2026-09-05 revision.</sub>

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

### T-76 — TWO RECORDS JOINED END TO END HAVE THE SHAPE OF ONE

<sub>Cut from `TESTING.md`, lines 3352–3380 of the
2026-09-05 revision.</sub>

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

### T-77 — AN ENTRY GOES BLIND WHEN A CONVERSION EDITS ITS TEST'S FIXTURE

<sub>Cut from `TESTING.md`, lines 3382–3419 of the
2026-09-05 revision.</sub>

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

### T-78 — FOUR WAYS A TEST DID NOT REACH THE JOURNEY ITS ENTRY NAMED

<sub>Cut from `TESTING.md`, lines 3421–3461 of the
2026-09-05 revision.</sub>

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

### T-79 — AN ANCHOR CAN BE AMBIGUOUS BY INDENTATION ALONE

<sub>Cut from `TESTING.md`, lines 3491–3522 of the
2026-09-05 revision.</sub>

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

### T-80 — SILENCE WITH EXIT 0 IS NOT A PASS

<sub>Cut from `TESTING.md`, lines 3543–3572 of the
2026-09-05 revision.</sub>

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

### T-81 — GUARD THE SHAPE, AND READ THE FILE WHOLE

<sub>Cut from `TESTING.md`, lines 3574–3609 of the
2026-09-05 revision.</sub>

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

### T-82 — ONE FAILURE IN FIFTEEN RUNS WAS NOT FLAKINESS

<sub>Cut from `TESTING.md`, lines 3646–3701 of the
2026-09-05 revision.</sub>

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

### T-83 — AN ORACLE A NEVER-SHOWN WINDOW CANNOT ANSWER

<sub>Cut from `TESTING.md`, lines 3703–3725 of the
2026-09-05 revision.</sub>

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

### T-84 — A LEG THAT RUNS AFTER THE STATE IT IS ABOUT

<sub>Cut from `TESTING.md`, lines 3727–3753 of the
2026-09-05 revision.</sub>

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

### T-85 — STAGE WHAT A SECOND PROCESS LEAVES, NOT THE SECOND PROCESS

<sub>Cut from `TESTING.md`, lines 3755–3778 of the
2026-09-05 revision.</sub>

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

### T-86 — PROVE THE QUANTITY THE FAILURE MEASURES

<sub>Cut from `TESTING.md`, lines 3780–3806 of the
2026-09-05 revision.</sub>

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

### T-87 — BUILD THE FIXTURE THROUGH THE PRODUCT'S OWN DOOR

<sub>Cut from `TESTING.md`, lines 3808–3839 of the
2026-09-05 revision.</sub>

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

### T-88 — A TEST THAT LOCATES A MOMENT BY COUNTING IS RE-AIMED BY A SLOWER MACHINE

<sub>Cut from `TESTING.md`, lines 3841–3927 of the
2026-09-05 revision.</sub>

## A TEST THAT LOCATES A MOMENT BY COUNTING IS RE-AIMED BY A SLOWER MACHINE

2026-08-31, found by CI's coverage leg on the candidate's own commit
and by nothing here: `a topology landing does not strand a live tick`
passed three times out of three locally and failed on Linux under the
per-test recorder, where every step costs several times what it costs
on this Mac.

THE ASSERTION READ `seen[1]` -- the SECOND call to `_generate` -- on
the assumption that the topology landing's re-press is the second one.
Measured here with a probe that recorded the CALLER of each call
rather than counting them, the journey makes FOUR calls, and two of
them arrive from timers whose order is timing's to choose:

    [0] live=True   the test's own press
    [1] live=False  a timer
    [2] live=False  _maybe_live_generate
    [3] live=False  a timer

The competing caller is the LIVE TIMER. When it fires before the
topology build lands -- which is what a slower machine buys -- the
second call is its call, at which `_live_pending` is still True
perfectly correctly, and the assertion is about a mechanism it was
never written for. The failure sentence then describes the wrong
thing, confidently, which is this file's own "a test's name is a
hypothesis about its own failure" arriving at a POSITION instead.

THE PRODUCT WAS INNOCENT AND THAT WAS PROVED, not assumed: the
landing clears the flag before re-pressing, and the catalogue entry
standing on that assignment still reports `caught` after the repair.
A repair that had quietly disarmed the guard would have looked
identical from the suite.

THE REPAIR IS TO CLOSE THE WINDOW, not to widen a wait. The flag is
what every reader downstream consults, so stopping the live timer
stages the condition and removes the only competing caller, leaving
the landing's re-press the only thing that can answer. And the test
now records WHO called and refuses to judge a call from
`_maybe_live_generate`, so if a competitor ever returns it says which
mechanism it met rather than failing about the other one.

AND IT WAS REPRODUCED HERE ON DEMAND, which turned a remote failure
into a staged condition. The runners have one thing this Mac does not:
a live tick landing BEFORE the topology build. Setting that quantity
directly -- starting the live timer at zero instead of waiting for a
slower machine to do it -- reproduces the CI failure every time, and
the two arms in one run say the whole thing:

    ARM A  timer fired at once   seen[1] = _maybe_live_generate,
                                 live_pending True   -> old test FAILS
    ARM B  timer stopped         seen[1] = a timer,
                                 live_pending False  -> both pass

`tools/probes/a_live_tick_racing_the_topology_landing.py` is that
measurement, committed, because the instrument that names one defect
is the one that names the next. Its arms run in ONE process and each
clears the project first, since two arms sharing a QgsProject is how a
control gets contaminated -- which cost two wrong readings earlier the
same day.

ASK OF ANY TEST THAT READS A MOMENT: does it NAME that moment, or
count to it? Where it counts, the count is a claim about how many
things happen first, and that is a claim about the machine.

AND A SIBLING THE SAME DAY, from the same Windows runner: a premise
that reads ONE fact where TWO must hold names neither. `a save is
deferred only when a run is really coming` asserted that a design
change had armed the live timer, and failed that premise on Windows
having passed it on the previous round -- with no way to tell whether
the SPACING had moved or the ARMING had not. A spin box clamps in
silence, and that one spans 1e-6 to 1e12 with its own text rules, so
"I called setValue" is not "the value changed". The premise is two
assertions now and the message says which half went.
WHAT WAS RULED OUT RATHER THAN GUESSED: the arming is SYNCHRONOUS --
`_queue_preview` calls `_queue_live` on its own last line -- so a
longer wait would have cured nothing, and the reach for one would have
been a fix invented for a cause nobody had found. Recording that the
cause is still open is worth more than a repair that happens to go
green.
AND SLOWNESS ALONE DOES NOT REPRODUCE IT HERE, which narrows what is
left rather than closing it. The one thing that runner has more of is
time, so ten busy loops were started -- load average about twelve --
and the test passed three times out of three under them. So this is
not the counting fault above wearing different clothes; something
about that PLATFORM, or a far rarer interleaving, is still unaccounted
for. A direction tried and empty is worth more to the next person than
a direction untried.

### T-89 — A probe that cannot reach its own case (2026-08-31)

<sub>Cut from `TESTING.md`, lines 3929–3961 of the
2026-09-05 revision.</sub>

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

### T-90 — Five instrument faults in one day, every one already written here

<sub>Cut from `TESTING.md`, lines 3993–4038 of the
2026-09-05 revision.</sub>

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

### T-91 — A PREMISE ASKED IN THE SAME BREATH AS A SETTLE READS THE OLD STATE

<sub>Cut from `TESTING.md`, lines 4087–4113 of the
2026-09-05 revision.</sub>

## A PREMISE ASKED IN THE SAME BREATH AS A SETTLE READS THE OLD STATE

(2026-08-31.) A guard waited for the topology build to go quiet and
then asserted, on the next line, that the design no longer carried a
topology. It failed -- while a direct measurement of the very same
dialog said it should pass, which sent the diagnosis after a
contradiction that did not exist.

The waiter returns when no build is IN FLIGHT. The edited unit is
adopted a beat after that. So the premise was asking about the
UN-EDITED design and answering, quite correctly, that it still had a
topology.

ORDER A PREMISE BEHIND THE EVIDENCE THAT THE ACT LANDED. Assert first
that the thing moved, then assert what follows from its having moved:

    _settle_topology(dlg, seconds=40)
    _settle(dlg)
    _tick(250)
    after_one = ground(dlg._unit)
    assert after_one != plain, \
      "PREMISE: the rotation has not reached the dialog's unit yet"
    assert not still_has_a_topology(dlg._unit), "PREMISE: ..."

Two contradictory measurements of one object are usually two moments
rather than two answers, and the cheapest way to tell is to make the
test say which moment it is standing in.

### T-92 — THE DESIGN A TEST DRIVES CAN REFUSE THE CASE, AND A CLEAN RESULT THEN MEANS NOTHING

<sub>Cut from `TESTING.md`, lines 4133–4153 of the
2026-09-05 revision.</sub>

## THE DESIGN A TEST DRIVES CAN REFUSE THE CASE, AND A CLEAN RESULT THEN MEANS NOTHING

2026-09-01, twice in one afternoon, and both of my first probes came
back clean on real defects.

A vertex drag past its control's range records an out-of-range value
on `archimedean 4.8.8` and CANNOT on `laves 3.3.4.3.4`: there the
library refuses a nudge that large, the preview raises, and the
handler clears the record, which is correct. And a drag's frame drifts
when a VERTEX is held and not when an EDGE is scaled, because only the
first grows the drawn extent that the paint-time fit re-measures.
Either probe, stopped at its first design, would have been filed as a
refutation of a claim that was true.

**SO VARY THE DESIGN BEFORE BELIEVING A NEGATIVE**, and where the
answer turns on which design is driven, NAME the design in the guard
and assert the premise that makes the case arise -- here, that the
preview survived the oversized drag at all, and that the manipulation
chosen grows the extent. A test that silently drives the design where
the case cannot occur is the fixture-that-cannot-exhibit-the-case
trap, arriving through the catalogue rather than through the data.

### T-93 — A CELL THAT CANNOT SET ITS OWN STAGE MUST SAY SO IN ITS OWN WORDS

<sub>Cut from `TESTING.md`, lines 4195–4224 of the
2026-09-05 revision.</sub>

## A CELL THAT CANNOT SET ITS OWN STAGE MUST SAY SO IN ITS OWN WORDS

2026-09-01, from Windows, and the message it produced was a sentence
about the PRODUCT that happens to describe correct behaviour.

The topology matrix aims each cell at a vertex or an edge drawn inside
the widget, and fell through with whatever the previous cell had
selected when it could not find one. The verb list narrows to the
selection -- by design, since select-then-act is what the tab is built
on -- so a fixture that could not aim reported "nudge_vertex is not
offered while holding a edge", twice, which reads as a dead control
and is the tab working exactly as ruled. A cell that cannot stage its
own case now says `FIXTURE:` and names what it could not aim at.

**AND A SETTLE RETURNS BEFORE THE RESULT IS ADOPTED**, which is the
other half of the same red. `_settle_topology` waits for the build to
stop being in flight and the panel takes the new unit a beat later, so
a reading taken straight behind it asks the question before the answer
exists: `design` moved, `drawn` did not, on two platforms, in cells
this machine passes every time. The repair is to wait for the STORES
THE CELL IS ABOUT to move, bounded, rather than for a fixed time -- a
cell that never moves them still fails, and fails with what it saw.

**AND A WIDGET INSIDE A LAYOUT DOES NOT KEEP A SIZE YOU HAND IT**, so
`view.resize(600, 600)` was decoration: measured with the call,
without it, and with the WINDOW driven to 1200x900, the drawing is
420x462 every time. It matters because the aiming is over what is
drawn INSIDE the widget, so a believed size that is not the size is
how a cell quietly stops being able to aim on a machine whose fonts
are wider.

### T-94 — A PREMISE THAT FAILS ELSEWHERE MUST CARRY WHAT HAPPENED, NOT WHAT IT EXPECTED

<sub>Cut from `TESTING.md`, lines 4226–4249 of the
2026-09-05 revision.</sub>

## A PREMISE THAT FAILS ELSEWHERE MUST CARRY WHAT HAPPENED, NOT WHAT IT EXPECTED

2026-09-01, from one Linux shard. `test_topology_edits_come_back_from_
the_file` failed its own premise with "the edits moved nothing, so a
roundtrip that preserved nothing would pass -- both (4, 250000.0,
3863.703)". The number is the whole diagnosis and the sentence did not
say so: it equals the PLAIN design rather than the rotated one, which
means the replay handed back the original -- both edits refused --
rather than the reading being taken early, which is the other and much
likelier-sounding explanation.

**SO A PREMISE ABOUT A REPLAY REPORTS THE REPLAY.** It now carries the
ground after the first edit alone, the per-edit marks
`topology_edits.apply` returns, and the sentence the panel was given,
so the next occurrence names its own cause. This is the project's
standing rule -- say what was FOUND, not which assertion was reached --
applied where it bites hardest, on a machine nobody here can drive.

**AND A FAILURE THAT APPEARS ON ONE TREE AND NOT ANOTHER IS ABOUT THE
MACHINE UNTIL PROVED OTHERWISE.** The same test passed on the commit
before, whose product code is byte-identical; the difference was the
runner. That is not a reason to shrug -- an intermittent failure is
still a case somebody can meet -- but it does say the instrument comes
before the theory.

### T-95 — FOUR INSTRUMENT FAULTS IN ONE ROUND, AND WHAT EACH LOOKED LIKE

<sub>Cut from `TESTING.md`, lines 4251–4298 of the
2026-09-05 revision.</sub>

## FOUR INSTRUMENT FAULTS IN ONE ROUND, AND WHAT EACH LOOKED LIKE

2026-09-01, rewriting the save and the load. Counted because a day
whose findings are mostly its own instruments is a day nobody should
act on, and because every one of these read as a finding about the
PRODUCT first.

**A `QgsApplication` LEFT UNBOUND IS COLLECTED ON THE NEXT LINE.** The
probe died of a segmentation fault with two nullptr warnings and
nothing else -- which is indistinguishable from the thing being
measured crashing. Bind it to a name.

**A MUTATION PROVER'S CHILD NEEDS THE QGIS ENVIRONMENT PASSED
EXPLICITLY, and without it the CONTROL fails too.** An edit script must
run under `env -u PYTHONHOME -u PYTHONPATH python3`, which is exactly
the environment a QGIS child cannot start in -- so a prover that let
the child inherit its own reported DISAGREEMENT on every arm, including
the unmutated control. Three "the mutation was caught" verdicts were
worthless. A treatment whose control also fails has measured nothing,
and the tell was the uniform verdict.

**A FIXTURE WITH NO MISSING VALUES CANNOT SEE A NULL BEING LOST.** The
differential between two writers was green, and proving it could go red
found that one of three mutations -- the one removing null handling --
was invisible: the fixture had no NULLs, so no `_no_data` twin was
written and the branch that stores a null was never reached. The
fixture now goes through a FILE, because a value never set on a memory
feature reads back as 0.0 rather than as QGIS's NULL, and it asserts
the premise both ways: the gappy arm must produce twins and the
complete arm must not.

**A CONTROL ARM THAT REBUILDS ITS SUBJECT MEASURES THE REBUILD.**
Comparing two ways of writing a style, the first version saved the map
twice and reconstructed the layers for the second arm -- copying the
renderer, the opacity and the custom properties onto fresh objects --
and reported about fifty characters of difference in every document.
That was the rebuilt layer differing from the original. Asked properly
-- ONE layer, its own name, two copies of the file, so the only thing
that differs is the code under test -- the two routes agree on every
column.

**AND THE SECOND VERSION OF THAT COMPARISON WAS WRONG A DIFFERENT
WAY**, which is worth knowing because it looked like a finding. Running
both routes into ONE file under two style names reported two
differences, and both were the probe's: an SLD embeds the LAYER'S NAME,
which the renaming had changed, and `useAsDefault` flipped because our
own writer correctly demotes the other rows on a table. Ask of any
difference whether your fixture could have produced it.

### T-96 — A WAITER THAT RETURNS ON A STALE ANSWER, AND A QUEUE THAT DEFERS

<sub>Cut from `TESTING.md`, lines 4329–4360 of the
2026-09-05 revision.</sub>

## A WAITER THAT RETURNS ON A STALE ANSWER, AND A QUEUE THAT DEFERS

2026-09-01, two tests that passed alone every time and failed in a
three-shard run. Both were read as timing; neither was, and in both
cases the mechanism is a branch somebody can point at.

**A QUEUE MADE WHILE A BUILD IS RUNNING DOES NOT START A SECOND.**
`_queue_topology` sets `_topology_wanted` and returns, and the landing
re-queues -- which says a build is coming all over again. So a test
that chose a family, waited for an answer and then read the tab's own
"working" sentence was reading the SECOND build's, queued by its own
call and started after the first landed. On a fast machine the
debounce's build is already home before the test asks, and there is no
second build at all.

**AND `_settle_topology` RETURNS AS SOON AS THE PANEL HOLDS AN
ANSWER**, which it may already have held from the PREVIOUS design. A
test that changed the design, called it, and then ticked a fixed 400ms
was betting that a build it never waited for would finish inside those
ticks.

THE REPAIR IN BOTH CASES IS TO CLOSE THE WINDOW, which this file
already prescribes: settle the dialog so the test's own queue is the
only one in flight and assert that premise out loud; and wait on the
EVENT the test is about -- here the promise being kept -- with a
ceiling that catches a hang rather than budgeting the work.

**AND THE TELL THAT IT IS NOT THE CLOCK** is that the mechanism can be
NAMED. Ask which branch produces the wrong reading and whether a
person could point at it; where the answer is a real line, staging is
available and a longer wait is the wrong repair. A fix invented for a
cause nobody found passes for the same reason a slower machine fails.

### T-97 — A SKIP WITHOUT A LINE IS A CELL THAT NEVER EXISTED

<sub>Cut from `TESTING.md`, lines 4362–4391 of the
2026-09-05 revision.</sub>

## A SKIP WITHOUT A LINE IS A CELL THAT NEVER EXISTED

Same day, and it is the sharpest thing the label/key separation
taught. The topology matrix guards each cell with "is this family on
offer", and asked it of the chooser's TEXT -- the label, which since
that morning may carry a common name. Every renamed design was
therefore skipped, and skipped WITHOUT a line in the record of what
was passed over: the count came back 15 of 35 and named ONE skip of
nineteen.

The test's own machinery was right about everything else: it counts
skips, it fails when a route is skipped in every cell it was drawn
for, and it fails when most cells staged nothing. What defeated all
three was a `continue` that incremented a counter and told the reader
nothing.

**SO EVERY SKIP CARRIES ITS REASON, AND THE ONES ADDED LATER MOST OF
ALL.** A skip written beside the assertion that reports skips will be
reported; one written at the top of a loop, as a cheap guard about the
fixture, is exactly the one that goes quiet -- and it is the one a
reader least expects, because the accounting below it looks thorough.
This is the no-silent-caps rule met INSIDE a test that already keeps
it everywhere else.

**AND THE QUESTION IS SWEPT, NOT THE PHRASING.** Six sites in this
suite named a design where it does not exist or read a label as an
identity, and only one of the six was found by the search that found
the first. What they share is the QUESTION -- which design is this --
and the sweep that finds them is for every reader of the family
chooser, not for the string that happened to break.

### T-98 — STAGING AND ASSERTING ARE NOT THE SAME MOVE, AND I CONFUSED THEM

<sub>Cut from `TESTING.md`, lines 4393–4419 of the
2026-09-05 revision.</sub>

## STAGING AND ASSERTING ARE NOT THE SAME MOVE, AND I CONFUSED THEM

2026-09-01, an hour after writing the entry above about closing a
window rather than sampling it. The repair to `the topology tab says
when it is working` waited for the topology to have an answer and then
ASSERTED, on the next line, that no build was outstanding. That is a
bet wearing a premise's clothes: a queue made while a build runs is
deferred and re-queued at the landing, so whether the tab is quiet at
that instant depends on the machine. Red twice in three runs of one
process -- and red on the PREMISE, which reads as the fixture being
wrong rather than as the repair being.

**THE DISTINCTION IS ONE WORD AND IT IS THE WHOLE OF IT.** To STAGE a
condition is to make it true and then proceed: wait, bounded, until
the tab is actually quiet. To ASSERT it is to demand that it already
be true and fail otherwise. A premise should assert what the test's
own setup has MADE true, never what the machine happened to arrange --
and the tell is that the assertion names something with a timer behind
it.

The repaired version waits until the build has landed and the sentence
has cleared, with a ceiling that catches a hang rather than budgeting
the work, and only then asserts. Four runs of four. This file already
says to close the window rather than measure how often you land in it;
what this adds is that a premise is exactly where that rule is
easiest to break, because a premise LOOKS like the safe kind of
assertion.

### T-99 — A FAMILY GUARD EARNS ITS KEEP ON FILES THAT DID NOT EXIST YET

<sub>Cut from `TESTING.md`, lines 4421–4443 of the
2026-09-05 revision.</sub>

## A FAMILY GUARD EARNS ITS KEEP ON FILES THAT DID NOT EXIST YET

2026-09-01. The guard written on 2026-08-28 for `if os.path.exists(x):
os.remove(x)` -- the race that cost a coverage shard its entire run,
three processes seeing the file, two removing it, the third dying
before a single test -- went red on the mutation workflow's coverage
leg and named THREE probes by file and line. All three were written
that same morning, for the save-and-load measurements, by somebody who
had read the entry describing the fault.

**THIS IS THE ARGUMENT FOR GUARDING THE SHAPE RATHER THAN THE SITE,
stated as a measurement rather than as a principle.** A regression
test pinned to the reported line would have passed forever while three
new instances arrived in one morning. The guard scans, so it found
them; it reads each file WHOLE, because the shape spans two lines and
no per-line grep can see it; and it counts what it scanned, because a
walk that finds nothing and a walk that looked at nothing are the same
green.

AND THE REPAIR WAS MADE AS A FAMILY, not where CI met it. All three
sites took the same two lines, and the local partial run had never
reached that test at all -- so mending the one the remote named would
have left two standing in instruments this project runs by hand.

### T-100 — ONE OWNER FOR "IS IT QUIET", AND THE TEST THAT MUST NOT ASK IT

<sub>Cut from `TESTING.md`, lines 4445–4477 of the
2026-09-05 revision.</sub>

## ONE OWNER FOR "IS IT QUIET", AND THE TEST THAT MUST NOT ASK IT

2026-09-01, found by CI on a candidate's own commit and costing that
candidate. Three tests carried the same premise -- "the chosen vertex
offers no handle to drag" -- and all three staged it the same way:
wait with `_wait_for_the_topology`, click a vertex, tick, read the
handles. That waiter returns as soon as the panel holds an ANSWER, a
queue made while a build is RUNNING is deferred and re-queued at the
landing, and `show_topology` clears the chosen thing on its way past.
So a build arriving in the tick after the click takes away the very
selection the premise is about.

**THE THIRD NARROW LOOP IS THE SIGNAL TO FIX THE QUESTION.** Two of
these had already been mended one at a time, in place, with inline
waits. `_the_topology_tab_is_quiet` asks it once -- no build in
flight, none queued behind one, no working sentence up -- with a
ceiling that catches a hang rather than budgeting the work.

**AND ONE OF THE THREE MUST NOT USE IT, which the same change proved
by breaking it.** `test_a_build_that_lands_mid_drag_does_not_wipe_the
_gesture` is ABOUT a landing arriving under a pointer, so draining the
queued build ahead of its click changes the sequence the rest of it
depends on. A control arm settled it in minutes: three runs of three
pass without the settle there, and the committing arm fails with it,
saying the panel adopted a new topology mid-gesture.

That is this file's own rule -- when you add a step to a sequence, ask
what it resets -- arriving on the person who had re-read it that
morning, and it is the second time in one day that a repair of mine
needed the same suspicion as the defect. A shared helper is right;
applying it everywhere the phrase matches is not. **Ask of each site
whether the condition being staged is the thing the test is about,
because where it is, staging it away is deleting the test.**

### T-101 — AIM AT A DRAWING BY ASKING THE PRODUCT, NOT BY COMPUTING A POINT

<sub>Cut from `TESTING.md`, lines 4479–4539 of the
2026-09-05 revision.</sub>

## AIM AT A DRAWING BY ASKING THE PRODUCT, NOT BY COMPUTING A POINT

2026-09-01, found by reading a superseded CI round rather than by any
failure here. `test_several_classes_can_be_moved_together` aimed its
shift-click at "a vertex of the second class" by taking the FIRST such
vertex drawn inside the widget. One Linux leg failed it with the
selection left exactly where the plain click had put it, while this
Mac passed every time.

THE PRODUCT WAS INNOCENT AND THE MECHANISM IS ORDINARY.
`mousePressEvent` tests HANDLES first -- they sit on whatever is
already selected and are the smaller target -- and takes the NEAREST
thing otherwise. So a point drawn on the class you want can land on
the previous selection's own handle, or nearer a neighbour, and select
nothing at all.

**AND THE FONTS ARE NOT THE VARIABLE, WHICH THE PROBE MEASURED AND
THIS PARAGRAPH USED TO GET WRONG.** It said which vertex that is true
of "is decided by the drawn layout, and so by the fonts, which is why
one runner sees it and one machine does not". Read off
`tools/ci_probe_the_topology_aim.py` on 2026-09-02, across Linux
4.0.0, Linux 4.0.3, Linux stable and macOS, every leg reports the SAME
drawing at 420x462, the same `Sans Serif` at 9pt, class A with four
vertices drawn and THREE a click would reach, and class B with eight
of eight. Nothing about the layout varies -- offscreen supplies one
font everywhere and the window's own minimum pins the drawing, which
MAINTAINING.md already records at 1025x450.

WHAT DOES VARY IS THE SELECTION AT THE MOMENT OF THE CLICK. The one
unreachable seat is unreachable because a HANDLE sits over it, and
handles sit on whatever is ALREADY SELECTED -- so the aim depends on
what the panel was holding when the press arrived, which a build
landing between the aim and the click changes. That is timing, and it
is the mechanism the same day's other repairs closed. A uniform
verdict across four platforms is usually the instrument; here it is
the answer, and it says the explanation to keep is the one about
handles rather than the one about fonts.

**SO ASK THE VIEW'S OWN HIT TEST BEFORE CLICKING.** The aimer offers
every candidate and keeps the first the product agrees about -- no
handle over it, and `_nearest` naming the class wanted. A fixture that
cannot aim then fails on its own premise instead of reporting the
plugin as broken, which is the difference between a work list and a
wrong diagnosis. This file already says to drive a control through its
own signal; the sharper version for anything DRAWN is that computing
where a thing is on screen is not the same question as where a click
would reach it.

AND THE REPAIR WAS PROVED BY STAGING THE RUNNER'S CONDITION rather
than waiting for it. With a handle declared over the first candidate,
the old aimer selects nothing and the selection stays `('vertex',
'A')` -- the runner's own message -- while the new one holds both
classes; the control arm has both working on the ordinary drawing.
Two arms, one run, one process, each clearing the project first.

THE WINDOW WAS TRIED AS THE LEVER AND IS NOT ONE. At 1025x450,
1200x700, 1400x900 and 1600x1000 the drawing measures 420x462 every
time, because the window's own minimum pins it -- so a sweep over
sizes returns one verdict for every input, which is this file's oldest
tell for an instrument that is varying nothing. The lever had to be
the hit test itself.

### T-102 — READ A VERDICT AND ITS ORACLE IN ONE BREATH

<sub>Cut from `TESTING.md`, lines 4541–4585 of the
2026-09-05 revision.</sub>

## READ A VERDICT AND ITS ORACLE IN ONE BREATH

2026-09-02, found by CI on a candidate's own commit and the second
suite fault to spend one. `the symmetries are drawn and gate what
cannot move` failed on the Linux 4.0.3 leg with "class B has 1 free
direction(s) and its push is greyed" -- a disagreement between a
control and the arithmetic behind it that CANNOT HAPPEN, because the
tab and the test call the same function.

IT COULD HAPPEN BECAUSE THEY CALLED IT ABOUT TWO DIFFERENT OBJECTS.
The test took its verdicts in one loop and computed its oracle in a
second loop afterwards, and a topology build landed in between -- so
the greying described the design that was in hand and the freedom
described the one that arrived. Nothing about the product was wrong
and nothing about the arithmetic was wrong.

**THE WAITER WAS THE FIRST HALF.** `_wait_for_the_topology` returns as
soon as the panel holds an ANSWER, and an answer left over from the
PREVIOUS design is an answer. `_the_topology_tab_is_quiet` is the one
that asks whether anything is still coming, and it exists because four
tests met this a site at a time; this is the fifth, and it was found on
a runner rather than here.

**AND READING THEM TOGETHER IS THE SECOND**, which is the part that
generalises past topology. Where a test compares a CONTROL against a
MEASUREMENT, take both in the same breath from the same object.
Waiting is what stops the state moving; reading together is what makes
the comparison mean something if it moves anyway. Two loops over one
subject are two readings of two subjects the moment anything lands
between them.

MEASURED, BOTH ARMS IN ONE RUN, by staging the condition rather than
chasing its frequency
(`tools/probes/what_the_gate_and_the_test_read.py`): put a topology in
the panel, change the design, take the verdicts before the new build
lands. Split, the assertion fails for class A while every control is
correct; taken together, it holds. The control arm -- the ordinary
sequence, settled -- agrees throughout, which is what says the probe
can answer either way.

AND THE TELL WAS IN THE PAIR OF FAILURES RATHER THAN IN EITHER. Two
Linux legs went red on ONE TEST EACH, and they were DIFFERENT tests,
with stable, macOS and Windows green. One test failing on three legs
is a claim about the code; different tests failing on one leg apiece
is a claim about timing.

### T-103 — A REPAIR CAN MOVE THE JOURNEY ITS OWN GUARD DRIVES

<sub>Cut from `TESTING.md`, lines 4587–4622 of the
2026-09-05 revision.</sub>

## A REPAIR CAN MOVE THE JOURNEY ITS OWN GUARD DRIVES

2026-09-02, three times in one campaign day, and it is the most
expensive shape of the round because every instance looks like a
passing test.

**A GUARD IS STAGED ON A JOURNEY, AND A REPAIR CAN CLOSE THAT
JOURNEY.** A cancel pressed during a write was guarded by delivering a
close from the write's own pump, which opened the waiting window. The
freeze repair later made the hold DECLINE there -- correctly -- so the
window no longer appears on that route and the guard's premise could
no longer be met. The behaviour it names is still reachable, through
the DEFERRED press, where the write runs inside the hold's own pump;
the test was re-staged there and still catches. THE TELL IS A PREMISE
FAILING WHILE THE PRODUCT IS RIGHT, and the answer is to ask which
journeys still reach the behaviour rather than to weaken the premise.

**AND TWO ENTRIES WERE PUT TO SLEEP BY THE SAME REPAIR.** Both
conditions that the earlier repairs added became REDUNDANT once the
hold could not run beneath a writer: with the nesting gone, the hold's
branch always executes after the act has ended, so mutating either
condition changed nothing any test could see. Both were retired with
their measurements, both lines kept as defence in depth, and what
would reopen each written where it stood. This project already records
that a ruling which gives a fact a second writer puts an older entry
to sleep; what this adds is that YOUR OWN REPAIR, hours old, is such a
ruling.

**A SURVIVING ENTRY IS A QUESTION ABOUT THE JOURNEY BEFORE IT IS A
QUESTION ABOUT THE ASSERTION.** The flag-lifetime entry survived twice
before it caught: first because the guard cancelled between tables,
where the writer clears the flag itself, and then because the press
landed a moment too late, after the act had ended. What made it bite
was staging the press SYNCHRONOUSLY at the seam -- a wrapper that
calls the real writer and then presses -- rather than from a timer,
which measures how fast the machine is.

### T-104 — THREE PREMISES THAT WERE BETS ON THE MACHINE

<sub>Cut from `TESTING.md`, lines 4658–4693 of the
2026-09-05 revision.</sub>

## THREE PREMISES THAT WERE BETS ON THE MACHINE

2026-09-02, all three found by CI and none by this machine, and they
had between them spent candidates while passing here every time. The
shape is one: A READING TAKEN AFTER A FIXED NUMBER OF TICKS RATHER
THAN AFTER THE THING IT IS ABOUT HAS HAPPENED.

**A RACE THE FIXTURE HOPED TO WIN.** `a save waits for a build already
coming` needs a topology build still outstanding at the press, and
relied on the one the design change queued not having landed yet. It
failed its own FIXTURE on three legs of one round and on two rounds
before that. It queues a build EXPLICITLY now, which puts the dialog
in exactly the state the behaviour is about with no race to lose.

**A SETTLE THAT RETURNS BEFORE THE RESULT IS ADOPTED**, counted at
250ms. `_settle_topology` returns when no build is in flight and the
edited unit is adopted a beat later, which is longer on Windows than
here. It waits for the dialog's own unit to MOVE now, bounded by a
hang-catcher -- and the failure quotes the ground it found, because
equalling the un-edited design means the edit was REFUSED rather than
slow, and those need different repairs.

**A PASS THAT RUNS THROUGH A `singleShot`**, counted at 400ms. The
Design tab's alignment pass had the two label columns 51px apart at
13pt on the macOS runner where this machine reads 0 at every size. It
is waited for now -- and the wait cannot blunt the assertion, since a
pass that never runs exhausts the ceiling and fails, which is the
difference between waiting for an event and widening a tolerance. That
distinction had already been paid for once on this very line, where
eight pixels of slack made it blind to a 3px fault.

**THE GENERAL RULE IS THIS FILE'S OWN AND IT KEEPS BEING RE-LEARNED:**
where a case depends on a window, close the window. What these three
add is that a PREMISE is the easiest place to break it, because a
premise looks like the safe kind of assertion -- and a premise that
fails on a runner reads as a broken fixture rather than as a bet.

### T-105 — A CORRELATION WITH YOUR OWN COMMIT IS A HYPOTHESIS

<sub>Cut from `TESTING.md`, lines 4695–4715 of the
2026-09-05 revision.</sub>

## A CORRELATION WITH YOUR OWN COMMIT IS A HYPOTHESIS

Same day, and it is the cheapest half-hour of the round. CI went red
on three legs at a commit of mine, having been GREEN on every job at
the commit before it. Everything fitted: three legs failing at once is
this project's own tell for a claim about the CODE rather than about
timing, and the commit had changed how a save decides its table names.

TWO THINGS ANSWERED IT AND NEITHER WAS AN ARGUMENT. The mechanism: the
repair runs INSIDE the Save press, and the failing assertion is a
premise read BEFORE that press, so it cannot have moved the reading.
And the record: the same test had already failed on two earlier
commits, so the fully green run in between was the LUCKY one rather
than the fixed one.

**SO BEFORE BELIEVING A RED THAT FOLLOWS YOUR CHANGE, ASK THE HISTORY
WHETHER IT IS NEW.** One `gh` call over the branch's earlier runs
turns "my repair broke three legs" into "this premise has been losing
a race for three rounds", and those want opposite work. This project
already says a stack pointing at your newest change is a hypothesis;
a RED RUN pointing at it is the same hypothesis wearing a verdict.

### T-106 — FOUR FIXTURES THAT COULD NOT REACH THEIR OWN CASE, IN ONE DAY

<sub>Cut from `TESTING.md`, lines 4717–4750 of the
2026-09-05 revision.</sub>

## FOUR FIXTURES THAT COULD NOT REACH THEIR OWN CASE, IN ONE DAY

Same day, mine, counted because a day whose findings are mostly its
own instruments is a day nobody should act on -- and because every one
of them was caught by a premise or a control rather than by reading.

**A CONTROL THAT COULD NOT FAIL EITHER.** A probe comparing the two
Load doors reported both sound, because it drew and saved a map in the
same window it then pressed Load in -- and a LANDING sets the very
flag the press was supposed to set. The plugin is reopened before the
press now. The tell was that the control arm was as green as the
treatment.

**A FIXTURE HOLDING THE THING IT MEANT TO REMOVE.** A probe about a
self-contained file left the SENDER'S own region layer in the project,
so `_recover_the_source` took its first route -- a layer already open
-- and the two stores it was written to compare agreed. A recipient
does not have that layer, which is what the copy inside the file is
FOR.

**TWO ARMS ON THEIR DEFAULTS AGREE BY ACCIDENT.** The guard for the
table-naming repair drew both of its maps without touching a variable,
so the names matched whatever the code did and its catalogue entry
SURVIVED against a test that was otherwise sound. One element is put
on another variable now, with a premise asserting the sent file
carries a table named for it.

**AND AN ORACLE KEYED BY A NAME NOBODY CHECKED.** The same probe read
the file's own record with `entry.get("tid")`, where the record keys an
element `id`, so that axis answered nothing at all while the probe
reported a finding from its other one. `WORKING_STATE_ELEMENT` is the
record's real definition and is where a key is read from, never from
memory -- which this project has now written down for the fifth time,
about a fifth reader.

### T-107 — A WAITER ANSWERS "IS ANYTHING OUTSTANDING", WHICH IS NOT "DID IT HAPPEN"

<sub>Cut from `TESTING.md`, lines 4752–4793 of the
2026-09-05 revision.</sub>

## A WAITER ANSWERS "IS ANYTHING OUTSTANDING", WHICH IS NOT "DID IT HAPPEN"

2026-09-02, and it had spread to ten registered tests before anybody
asked what the sentence beside it claimed.

`_the_topology_tab_is_quiet` returns True when no build is in flight,
none is queued behind one and no working sentence is up. A test then
staged its ground with

    assert _the_topology_tab_is_quiet(dlg), \
      "PREMISE: no topology was built, so there are no classes to aim at"

and read the panel three lines later. The function cannot answer that
sentence: a tab which has NEVER BUILT ANYTHING is quiet, trivially.

**AND IT WAS REACHABLE RATHER THAN THEORETICAL, WHICH IS THE HALF THAT
MATTERS.** The build is queued inside `_rebuild_unit`, which fires on
the preview debounce -- an interval that is a FLOOR and widens to
whatever the last rebuild cost, up to a ceiling of 350 ms against the
200-300 ms every caller ticks. Staged by reporting a rebuild as having
cost 400 ms, three arms with the control first: the panel held the
PREVIOUS design's classes (`abcd`/`ABC` where the design in force has
`ab`/`AB`), and where that previous design had no topology at all it
held None and the next line raised `AttributeError`.

**THE LEVER WAS NOT THE TIMER.** Setting the interval directly came
back as 152 where 4000 had just been asked for, because
`_queue_preview` re-derives it from `_last_rebuild_ms` on every
change. A quantity the product recomputes is not a quantity you can
set; find the input it recomputes it FROM.

**THE REPAIR IS AT THE QUESTION, NOT THE SITE.** A pending rebuild is
the fourth way something can still be coming, and every one of the ten
callers had the same weakness -- the third-narrow-loop rule arriving
before the third loop rather than after it. The one test whose subject
IS a landing under a pointer deliberately does not ask, so widening
the helper could not delete it; checked rather than assumed.

**AND A PREMISE ASSERTS WHAT THE SETUP MADE TRUE.** Waiting until the
tab is quiet STAGES a condition; asserting the panel HOLDS a topology
is the claim the sentence was making. Where a helper answers a
narrower question than its callers need, the callers assert the rest.

### T-108 — A RESTORE HELD BY TWO WRITERS CAN ONLY BE JUDGED WHERE ONE DOES NOT RUN

<sub>Cut from `TESTING.md`, lines 4795–4824 of the
2026-09-05 revision.</sub>

## A RESTORE HELD BY TWO WRITERS CAN ONLY BE JUDGED WHERE ONE DOES NOT RUN

Same day, and it took an entry SURVIVING TWICE to find the second
writer.

A save takes a layer's subset off to write the map, because
`getFeatures()` honours one, and puts it back. An owed line said the
restore assertion could not fail because the already-saved skip means
a filtered layer is never written -- true, and only half of it. On the
RE-TILE arm the subset genuinely does come off, and the assertion
still could not fail: the REPOINTING loop restores each subset as it
goes, two hundred lines above the `finally` that also does.

**SO THE `finally`'S OWN ROUTE IS THE ONE NOTHING DROVE**, and it is
the one its comment names: a save that never reaches the repointing. A
cancelled write rolls back and RETURNS, so there the `finally` is the
only restorer left -- and a person who stops a save would otherwise
find their Layer Properties filter silently cleared.

The rule this joins is already here -- when an entry survives, ask
whether the behaviour has two implementations before asking whether
the test is weak. What this adds is where to look for the second one:
NOT beside the first. Both writers of this fact are in the same
method, two hundred lines apart, and reading either alone shows
nothing wrong.

**AND THE ARM IS STAGED AT THE SEAM.** The writer asks `should_stop`
between tables, so the flag is set by wrapping the module attribute
`dialog.py` itself holds and letting the real writer run -- no timer,
which would be a bet on the machine.

### T-109 — A UNIFORM VERDICT CAN BE THE ANSWER RATHER THAN THE INSTRUMENT

<sub>Cut from `TESTING.md`, lines 4826–4857 of the
2026-09-05 revision.</sub>

## A UNIFORM VERDICT CAN BE THE ANSWER RATHER THAN THE INSTRUMENT

2026-09-02, and it corrects a cause this file had carried since
2026-09-01.

This document's oldest tell is that a result which comes back the same
for every input is almost always the instrument. `tools/ci_probe_the_
topology_aim.py` reported the SAME numbers on Linux 4.0.0, Linux
4.0.3, Linux stable and macOS -- 420x462, `Sans Serif` at 9pt, class A
four drawn and three reachable, class B eight of eight, both classes
held. By the tell alone that reads as a probe varying nothing.

It is not. Offscreen supplies one font on every runner and the
window's own minimum pins the drawing, so the drawn layout genuinely
cannot vary -- and THAT is the finding, because three documents said
the failure was "decided by the drawn layout, and so by the fonts".
The one unreachable seat has a HANDLE over it; handles are hit-tested
first and sit on whatever is ALREADY SELECTED; so what differs between
runs is the selection at the press, which is timing.

**THE DISCRIMINATOR IS WHETHER THE QUANTITY COULD HAVE VARIED.** Ask
what would have to be different for the number to move. Where the
answer is "nothing on any machine we run", a uniform verdict is a
measurement rather than a broken instrument -- and it is then evidence
ABOUT the explanations on offer.

**AND A CAUSE NAMED BY READING SPREADS.** That one had reached
docs/TESTING.md and two sites in the suite before anything measured
it, which is this file's own rule about a SITE named by reading,
arriving at a CAUSE. When you write down WHY something differs between
machines, say how you know -- and if the answer is "I read the code",
the probe costs one CI round you were going to spend anyway.

### T-110 — A GATE THAT CANNOT START IS NOT A GATE THAT ANSWERED

<sub>Cut from `TESTING.md`, lines 4859–4879 of the
2026-09-05 revision.</sub>

## A GATE THAT CANNOT START IS NOT A GATE THAT ANSWERED

Same day, inside a commit chain. `check_no_secrets` exited 1 and the
commit correctly did not run -- and it had found nothing: the shell
had sourced the QGIS environment, so a plain `python3` inherited
PYTHONHOME and died at "No module named 'encodings'". Re-asked under
`env -u PYTHONHOME -u PYTHONPATH python3` it checks 321 files clean.

It failed SAFE, which is the right direction and is why this cost
nothing. But the same trap in the other direction is this project's
oldest: a harness whose failure to start is indistinguishable from
success can only confirm. Ask of any gate you have just seen go red
whether it RAN -- a secrets check reporting a Python bootstrap error
has not audited anything, and a red you cannot explain is worth one
command before it is worth an hour.

**AND THE SAME BUFFERING TRAP REACHES A WATCHER.** Hand-running one
into a PIPE printed nothing at all before its timeout, because printf
to a pipe is block-buffered; into a FILE it printed twenty-seven
lines. Hand-run a watcher before arming it -- and hand-run it THE WAY
IT WILL BE ARMED, or the rehearsal measures the rehearsal.

### T-111 — A PROBE'S CONTROL MUST MOVE ONE TERM, AND AN INSTRUMENT MUST ASK THE PRODUCT ITS OWN...

<sub>Cut from `TESTING.md`, lines 4901–4922 of the
2026-09-05 revision.</sub>

## A PROBE'S CONTROL MUST MOVE ONE TERM, AND AN INSTRUMENT MUST ASK
## THE PRODUCT ITS OWN QUESTION

(2026-09-02, verifying the shelf key's blindness to the dual, and both
faults were in one probe.)

ITS CONTROL CHANGED THE DESIGN IT WAS COMPARING AGAINST. The control
for "an ordinary design change moves the shelf key" moved the ELEMENT
COUNT -- which repopulates the family list and lands on whatever that
count offers, so `hex-slice 4#4` became `square-colouring 5#5` and
every reading after it was about a design nobody had chosen. A family
change moves one term and is the honest control. This is the
select-then-act fault in an instrument: a step that looks like it is
about one thing resets another.

AND ITS KEY WAS A SECOND IMPLEMENTATION. The probe computed the key
itself, mirroring the signature as it stood -- so after the repair
widened that signature the probe went on printing the OLD answer, and
the repair read as absent. Asking the product's own method is what
made the picture unambiguous, and it is the same rule the defect
itself is about: a reimplementation is a second definition, and the
day one of them moves they disagree.

### T-112 — A READING TAKEN BEFORE THE AIMING IS A BET ON THE MACHINE

<sub>Cut from `TESTING.md`, lines 4941–4985 of the
2026-09-05 revision.</sub>

## A READING TAKEN BEFORE THE AIMING IS A BET ON THE MACHINE

2026-09-02, found by CI's coverage leg on rc13's own commit and by
nothing here. `a build that lands mid drag does not wipe the gesture`
failed on its MAIN assertion this time rather than on a premise --
"the panel adopted a new topology mid-gesture" -- 256 passed and 1
failed on one shard of three, each shard naming the same total of 772,
while the same test passed in that candidate's own local suite at 4.8s
against the runner's 11.7s.

THE PRODUCT WAS INNOCENT AND THAT WAS STAGED RATHER THAN ARGUED. The
test captured its subject -- the topology the panel holds -- BEFORE the
clicks that find a handle to drag, and those clicks tick the event
loop, while this test deliberately does not drain the queued build
first, its whole subject being a landing that arrives under a pointer.
A landing in the clicking window is adopted CORRECTLY, no gesture being
in progress yet; the captured value then goes stale and the assertion
reports correct behaviour as the defect, in a sentence that says
"mid-gesture" about a landing that happened before the gesture.
Measured both arms in one run by
`tools/probes/which_moment_the_drag_guard_reads.py`, each clearing the
project first: with a landing delivered before the press the old
reading FAILS and a reading taken at the press HOLDS, and in BOTH arms
the mid-gesture landing is refused, so the hold was never at fault.

THE REPAIR IS A MOMENT, NOT A WAIT. The subject is read inside the
helper that performs the press, so nothing can move it between the two
-- a landing arriving while the pointer is down is held rather than
applied, which is the behaviour under test. Adding a settle instead
would have been the obvious repair and is the wrong one: this test's
siblings drain the queue and it must not, measured 2026-09-01 at three
runs of three.

AND THE GUARD WAS RE-PROVED RATHER THAN ASSUMED. All three catalogue
entries standing on it -- the hold, the held landing being applied, and
its discard where the gesture committed -- came back `caught` after the
repair. A repair to a test is exactly where a guard quietly stops
being able to fail.

THE TELL FOR THE FAMILY: an assertion whose message names a MOMENT
("mid-gesture", "after the landing", "once the run had finished") is
making a claim about when its own reading was taken. Ask what could
have moved that value between the reading and the act, and where the
answer is "anything the event loop delivers", take the reading at the
act.

### T-113 — AN ALLOWANCE SIZED ON THIS MAC IS AN ALLOWANCE THIS MAC WILL NEVER MEET

<sub>Cut from `TESTING.md`, lines 4987–5025 of the
2026-09-05 revision.</sub>

## AN ALLOWANCE SIZED ON THIS MAC IS AN ALLOWANCE THIS MAC WILL NEVER MEET

Every ceiling in this suite is `CONTENTION` times something -- 2.5 for
a sharded run multiplied by each platform's declared slowness, so a
three-shard Linux job is given seven and a half times this machine's
patience. FOUR SHARED WAIT HELPERS HAD NO SUCH FACTOR:
`_wait_for_the_topology`, `_the_topology_tab_is_quiet`,
`_settle_topology` (which counts ticks rather than seconds) and
`_settle` itself, the oldest and most-called of the four.

WHAT IT COST WAS A CANDIDATE. On 2026-09-02 rc14's 4.0.3 leg failed `a
drag is measured in the frame it began in` on its premise after ninety
seconds, 771 passed and 1 failed of one shard of three -- while the
NEXT topology test on that same runner passed in 4.3 seconds. A tab
that is healthy four seconds later was never hung; only the allowance
was this machine's.

THE REPAIR IS A SHAPE GUARD RATHER THAN FOUR EDITS.
`test_every_shared_waiter_widens_for_a_slow_machine` parses this file,
collects every module-level helper whose name says it waits, and
requires each to mention `CONTENTION` in its own body. It DERIVES its
list, because a hand-kept one drifts the first time somebody adds a
fifth -- the fault this project has already recorded of `USER_FACING`
and of `sandbox.INCLUDE_FILES` -- and it COUNTS what it scanned,
since a walk that finds no waiters and a walk that looked at nothing
are the same green.

IT PROVED ITSELF ON ITS FIRST RUN, which is the only evidence a new
guard's liveness ever has: three waiters had just been repaired by
hand and it immediately named a FOURTH nobody had looked at.

AND A FAILING PREMISE MUST SAY WHICH TERM WAS OUTSTANDING.
"a topology build never stopped being outstanding" names four possible
causes and reports none of them, so the runner's ninety seconds bought
no information at all. `_why_the_topology_tab_is_busy` reads all four
-- a build in flight, another queued behind it, the working sentence
still up, a preview rebuild pending -- and both premise sites now
carry its answer. A premise that fires on a machine nobody can log
into is the one place where the message IS the measurement.

### T-114 — A PREDICTION IS AN AXIS, AND A WRONG AXIS IS OBEYED FAITHFULLY

<sub>Cut from `TESTING.md`, lines 5027–5067 of the
2026-09-05 revision.</sub>

## A PREDICTION IS AN AXIS, AND A WRONG AXIS IS OBEYED FAITHFULLY

2026-09-03, and it is the best argument this file has for writing down
HOW a thing was measured rather than only what was concluded.

An abort in the harness's own teardown -- `corrupted double-linked
list`, exit 134, at `check`'s `project.clear()` on the line after a test
PASSED -- was recorded on 2026-09-01 as belonging to QGIS 4.0.0: "the
abort is 4.0.0's alone -- 4.0.3 and stable were green on the same
tree". The same note predicted, in advance and admirably, that if it
returned the honest next step was to skip BY VERSION rather than to
guess again at a destruction order.

IT RETURNED, AND THE PREDICTION WAS OBEYED EXACTLY. The skip was written
gated on `(4, 0, 0)`, deliberately narrow, failing toward RUNNING the
test on an unknown version. On the next round the abort fired on
`stable` instead, on the same test with the same signature, while 4.0.0
went green because it was skipped.

THREE ROUNDS, THREE SINGLE LEGS, A DIFFERENT ONE EACH TIME. That is the
shape of something INTERMITTENT following the door -- a provider whose
GeoPackage was moved out from under it, destroyed in a shared teardown
-- rather than something belonging to a version. Two data points had
been read as a version fact, and every later step inherited it: the
gate, its comment, three documents, and a candidate's worth of
attention.

**A PREDICTION NAMES AN AXIS AS WELL AS AN ACTION.** "Skip by version"
carries a claim -- that version is what varies -- and the action can be
implemented perfectly while the claim is wrong. So when you write down
what to do if something recurs, write down WHAT WOULD HAVE TO BE TRUE
for that to be the right thing, and check it when the day comes. Here
one question would have done it: has this ever fired on more than one
leg, and were those legs the same version?

**AND RETIRING A DOOR RETIRES WHAT STOOD ON IT.** Skipping that door
left `the-source-gone-restyle-repaints-the-preview` unable to fail:
measured the same day, SURVIVED in the same run that its two siblings
came back `caught`. It was retired with its measurement and with what
would reopen it. When a test stops driving a journey, judge every entry
whose site that journey was the only route to.

### T-115 — AN INERT MUTATION AND A WEAK TEST BOTH REPORT SURVIVED, AND ONE ROUND PRODUCED BOTH

<sub>Cut from `TESTING.md`, lines 5110–5139 of the
2026-09-05 revision.</sub>

## AN INERT MUTATION AND A WEAK TEST BOTH REPORT SURVIVED, AND ONE ROUND
## PRODUCED BOTH

2026-09-04, proving two entries over one patch. They needed opposite
repairs and reading either alone would have suggested the wrong one.

**THE INERT ONE WAS RESCUED BY THE PATCH'S OWN GUARD.** The entry
widened a spatial predicate so that tiles which merely touch a zone
would be treated as lying inside it. That makes the join's key
non-unique, which trips the patch's own overlapping-zones fallback, so
the split declines and the answer is unchanged. It bit only when the
predicate and the guard were mutated TOGETHER -- break every route at
once rather than writing a fifth entry.

**THE WEAK ONE WAS TELLING THE TRUTH ABOUT THE TEST.** Dropping the
interior tiles from the lookup leaves them joined to no zone and they
vanish from the map -- and the guard could not see it, because it
asserted that every DRAWN tile was assigned correctly and never that
every tile the clip would place was DRAWN. A shorter map is still a
correct one tile for tile. It asserts completeness now.

**AND ITS ANCHOR NEEDED A RAW STRING.** The line it stands on ends in a
backslash, and a non-raw anchor collapses that into a line
continuation, so the entry matched nothing and reported SURVIVED about
a mutation it had never applied. Recorded 2026-08-29 and now paid for
twice.

THE ORDER TO ASK IN, when an entry survives: did the mutation remove
the behaviour at all; is the behaviour held redundantly; is the test
reaching that journey; and only then, is the assertion weak.

### T-116 — A RATE FROM TOO FEW DRAWS, PUBLISHED TWICE IN ONE HOUR

<sub>Cut from `TESTING.md`, lines 5141–5175 of the
2026-09-05 revision.</sub>

## A RATE FROM TOO FEW DRAWS, PUBLISHED TWICE IN ONE HOUR

(2026-09-04, chasing the topology matrix's one failing cell, and both
were mine.)

The cell reproduced on the SECOND of two attempts and was written up as
DETERMINISTIC. The next run of the same probe answered in 1.43 seconds
both times.

Then a two-arm comparison came back 2 of 8 at HEAD against 0 of 8 at
the commit before that session's tiling patches, which reads exactly
like a verdict on those patches -- and HEAD then produced 0 of 16 on
its own, which disposes of it. The final count was four failures in
eighty-six attempts, about 4.7%: sixteen attempts at that rate EXPECT
less than one, so the control arm was never capable of saying anything
and the comparison was decorative from the moment it was drawn.

**ASK HOW MANY DRAWS WOULD BE NEEDED TO TELL YOUR RATE FROM ZERO**
before reporting one. It is one line of arithmetic and it is the
difference between a measurement and a story.

AND THE RUN STAGED TO SETTLE IT WAS VOID FOR A SEPARATE REASON. One arm
met a load average of 13 and the other 250, because the load staged was
not the only load on the machine. A comparison whose CONDITIONS are not
printed beside its numbers is not one anybody can check -- so each arm
prints its own load average now, and the arms are run twice in reversed
order so drift falls on both equally.

**AN INTERMITTENT DEFECT'S ARMS ARE THE LAST THING TO TRUST AND ITS
MECHANISM THE FIRST.** What actually settled this was a single reading
taken at the moment of failure -- the task `Queued`, the thread pool
`active=0`, no Python worker thread alive -- which no amount of
rate-chasing would have produced, and which is what the repair was then
aimed at. Reach for the instrument that reads STATE at the failure
before the one that counts failures.

### T-117 — A GUARD CAN BE AIMED AT A STATE WITHOUT KNOWING WHAT PRODUCES IT

<sub>Cut from `TESTING.md`, lines 5177–5201 of the
2026-09-05 revision.</sub>

## A GUARD CAN BE AIMED AT A STATE WITHOUT KNOWING WHAT PRODUCES IT

(Same day, and it is the other half of the entry above.)

The stall's CAUSE is undiagnosed: QGIS accepts a topology build, leaves
it Queued and never starts it, four times in eighty-six attempts and
then not at all in thirty. A condition nobody can stage cannot be
tested, and this project's rule is to close the window rather than
count how often it opens -- so the window was not the target. The STATE
it leaves was: a task the dialog believes is in flight, reading Queued.

**THAT STATE IS STAGEABLE EVEN THOUGH THE CONDITION IS NOT.** A QgsTask
never handed to the task manager reads Queued for ever, deterministic
and free, and it is the state exactly. The guard was therefore measured
before it was written, and its test asserts a property rather than
waiting for weather.

WHAT KEEPS SUCH A GUARD HONEST IS SCOPE AND WORDING, and all three
matter. It asks about STARTING and never about duration, so nothing
slow can reach it. It SAYS rather than cancels, so a pool busy with
another plugin's work gets a sentence that is still true. And the
OPPOSITE ANSWER IS ASSERTED SEPARATELY, because a rule with two answers
is taken for one by whoever meets the first: a build under way must NOT
be reported as never started, or the tab tells somebody their healthy
nineteen-second design was abandoned. Two entries, one per answer.

### T-118 — A SURVIVOR NAMED THE ARM THAT WAS MISSING

<sub>Cut from `TESTING.md`, lines 5203–5224 of the
2026-09-05 revision.</sub>

## A SURVIVOR NAMED THE ARM THAT WAS MISSING

(2026-09-04, repairing the drop that cleared its own preview.)

`_commit_the_drag` has three exits that record nothing, and each must
clear the preview. An entry was aimed at the third -- the no-travel
test, which is what a person meets when they take hold of a handle and
think better of it -- and it came back SURVIVED.

It was not a weak test. The test's discard arm was a CLICK on a vertex,
which never grabs anything, so it leaves at the drop's FIRST exit and
the mutated line is not on its route at all: an INERT mutation, wearing
the appearance of a test too weak to notice one. This document already
carries the discriminator for telling those apart; what this adds is
the shape that produces them most often.

**A FUNCTION'S EARLY EXITS ARE JOURNEYS, NOT LINES.** Three `return`s
in one method looked like three lines of one path, and they are three
different things a person can do. An arm that grabs a handle and lets
go without moving walks the third, and the entry then catches. Before
writing an entry on an early exit, ask which ACT reaches it, and check
your test performs that act rather than a neighbouring one.

### T-119 — The 373 probes, the eleven doubled prefixes, and the four faults of one evening

<sub>Cut from `TESTING.md`, lines 30–45 of the 2026-09-05 revision.</sub>

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

### T-120 — The claim that ran the other way, and what went in the ledger instead

<sub>Cut from `TESTING.md`, lines 112–122 of the 2026-09-05 revision.</sub>

2026-08-28. A hunt reported that a Save drops a no-data twin's table
while its element's survives. Driving the same panel act -- delete one
element's row from the group, press Save -- gave the OPPOSITE: the
element's table went and the twin stayed, leaving a set of
missing-value areas belonging to an element the map does not have.

Same mechanism, same harm class, reversed. What was fixed and recorded
is the direction that was MEASURED, and the claim's own direction is
noted in the ledger as not reproduced.

### T-121 — The three clean probes, and the memory URI that could not collide

<sub>Cut from `TESTING.md`, lines 133–145 of the 2026-09-05 revision.</sub>

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

### T-122 — What each differential instrument actually found, one by one

<sub>Cut from `TESTING.md`, lines 356–377 of the 2026-09-05 revision.</sub>

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

### T-123 — The three tests written around a defect, and what each pinned

<sub>Cut from `TESTING.md`, lines 388–400 of the 2026-09-05 revision.</sub>

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

### T-124 — The nineteen tests the reduction moved, and the one that knew why

<sub>Cut from `TESTING.md`, lines 401–416 of the 2026-09-05 revision.</sub>

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

### T-125 — The fixture accident test_metamorphic_variable_permutation was passing on

<sub>Cut from `TESTING.md`, lines 433–445 of the 2026-09-05 revision.</sub>

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

### T-126 — The three sibling-path defects of 2026-08-13, each in full

<sub>Cut from `TESTING.md`, lines 470–483 of the 2026-09-05 revision.</sub>

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

### T-127 — The 37-of-50 survivor breakdown behind the table-test shape

<sub>Cut from `TESTING.md`, lines 547–554 of the 2026-09-05 revision.</sub>

Evidence for the shape: across three batches, 37 of 50 survivors came
from just two operators, "call removed" and "number changed", and
almost every one was a default, a constant, a catalogue value or a
configuration call. Fixing those individually took most of a day and
covered only what had been sampled; the tables cover what has not
been sampled yet.

### T-128 — Why a table test flatters a mutation score, and the spacing default that proves it

<sub>Cut from `TESTING.md`, lines 563–581 of the 2026-09-05 revision.</sub>

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

### T-129 — The first test map's counts, kept as history

<sub>Cut from `TESTING.md`, lines 605–612 of the 2026-09-05 revision.</sub>

As of the first map: 145 tests, 35 guarding a real
defect. Those two numbers are the figures on the day the map
was first generated and are left as history; the CURRENT ones
are at the top of docs/TEST-MAP.md and docs/BUG-REGISTER.md,
which are regenerated at every release. A count written into
prose is true until somebody adds one.

### T-130 — The 0.024ms ramp lookup that fitted the stall perfectly and was innocent

<sub>Cut from `TESTING.md`, lines 651–662 of the 2026-09-05 revision.</sub>

What actually explained it was in the timings nobody had looked at:
the same test took 392s, 486s and 550s on three legs of ONE round, on
identical code. The spread is the runner.

A stack tells you where a process WAS, which is not why it was slow.
Before accepting the obvious culprit, measure it -- and prefer
evidence that varies independently of the suspect, like the same code
timed on three machines. The cache was kept because it is right on
its own terms, and labelled in its commit as not the cause, because
the next person will otherwise read the fix as the diagnosis.

### T-131 — The contention factor that knew about sharding and nothing about the platform

<sub>Cut from `TESTING.md`, lines 666–688 of the 2026-09-05 revision.</sub>

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

