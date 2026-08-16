# The hunt record: which directions found defects, and which did not

Every bug hunt this project has run, what it was pointed at, and what
came of it. It exists because the yield of a hunt turns almost
entirely on the DIRECTION it is pointed in, and that is not obvious in
advance — the single worst defect ever found here came from the first
hunt that stopped reading code and started from the user's losses,
after eight hunts reading code had walked past it.

**Keep this current.** The instructions for doing so are at the
bottom, and `tools/bug_hunt_brief.py` tells every hunt to come back
here. A record nobody updates becomes a record nobody trusts, and this
one earns its keep only while the numbers in it are real.

Last updated 2026-08-16, after SIX rounds in one day: three against
the No Data feature as it was written, then four aimed at the same
day's fixes, then six more after those. Twenty-one hunts in all.

THE DISTRIBUTION IS THE FINDING, and it sharpened as the day went on.
Of the later rounds' fourteen confirmed defects, ELEVEN were in code
written within the previous few HOURS, and five were inside repairs
for defects the earlier rounds had found. Three separate attempts at
one fix were each withdrawn after a hunt measured what they broke.
A hunt aimed at fresh work is not a check on old code; it is the
last stage of writing the new code, and this project should treat it
as part of the change rather than as an audit afterwards.

The earlier note, kept because its numbers are still the ones quoted
below: eleven hunts were launched across the first three rounds; the table below carries rows for the directions whose
findings were confirmed and acted on. IT IS NOT A COMPLETE ROSTER OF
THE ELEVEN, and saying so is the point of a record that counts against
itself: several hunts wrote their logs into session scratch that has
since been cleared, so their hypotheses-logged counts cannot be quoted
honestly and are not. What IS quoted is what was reproduced
independently and fixed.

The round is worth one summary line, because the distribution is the
finding. Of roughly seventeen confirmed defects across the three
rounds, THIRTEEN WERE IN CODE WRITTEN THAT SAME DAY, and three were
inside earlier fixes for the same feature. Hunting is usually
described as looking for old bugs; here it was overwhelmingly a check
on new work, and the directions that paid were the ones aimed at
shapes (a paired identity, an order, a record that outlives its
subject) rather than at features

## How to run one

Six steps. The whole thing costs an evening of machine time and a few
hours of yours, and the last step is the one that decides whether any
of it was worth doing.

**1. Choose a direction, not a place.** See below for what that
means, and read "The record" first: a direction already tried and
empty is worth knowing before you spend a night on it.

**2. Generate the brief.**

    python3 tools/bug_hunt_brief.py --shape asymmetry --area "worker.py and compat.py"

`--shape` is one of the structural questions the tool knows; `--area`
is what to point it at. Read the output before sending it. The brief
carries the confirmation protocol, the traps this project has already
paid for, and the calibration notes, and it tells the hunt to come
back and update this file.

**3. Give each hunt its own worktree.** Hunts edit product code to
prove a break, and they will collide with each other and with you:

    git worktree add /path/to/scratch/hunt-<name> HEAD

Editing a tree something else is reading spoiled two measurements in
one night here. This is not optional with more than one hunt running.

**4. Require a check-in log**, at a path you choose, appended to after
EVERY hypothesis and at least every fifteen minutes:

    ## HH:MM:SS  iteration N  [logical|perturbation]
    TRIED:  the hypothesis in one sentence, with file:line
    RESULT: confirmed / ruled out / inconclusive, with actual values
    NEXT:   what that makes you do, and why

The entry goes in BEFORE the next hypothesis starts. The times are
not the point — forcing a hypothesis to be written down before it is
chased is the point, and a log reconstructed at the end has none of
that. Tell the hunt you will check the timestamps, and check them:
two hunts here estimated theirs and it showed.

**5. Watch them.** See the next section.

**6. Verify everything yourself, by a route the hunt did not use.**
This is the step that cannot be delegated and is the real cost of the
method. Of the claims judged here, most survived, one evaporated
entirely, one was a right observation with a wrong severity call, and
one led to a fix that contradicted a settled decision a test had
guarded for months. Running more hunts does not raise throughput; it
lengthens this queue.

## Watching a running hunt

A subagent cannot interrupt itself to report, so the log is the only
window. Poll it on a fixed cadence and print one line per hunt —
entries so far, confirmations claimed, and the newest RESULT:

    S=/path/to/scratch
    while true; do
      sleep 900
      echo "---- check-in $(date -u +%H:%M:%S) ----"
      for f in <names>; do
        L="$S/hunt_${f}_log.md"
        if [ -f "$L" ]; then
          n=$(grep -c "^## " "$L" 2>/dev/null || echo 0)
          conf=$(grep -ci "^RESULT: *confirmed" "$L" 2>/dev/null || echo 0)
          echo "$f: $n entries, $conf confirmed | $(grep '^RESULT:' "$L" | tail -1 | cut -c1-140)"
        else
          echo "$f: NO LOG YET"
        fi
      done
    done

Three things this deliberately does, each of which this project got
wrong somewhere else first:

- **It reports a summary on a cadence, not every line.** One event per
  hypothesis across four hunts is forty notifications nobody reads.
- **It says NO LOG YET rather than staying silent.** Silence from a
  watcher is not evidence that anything is running; an absent log is
  a finding about the hunt, and one of the first things worth knowing.
- **It reads the log rather than the agent.** The agent's own
  transcript is enormous and reading it will drown you.

What to watch FOR, rather than just watching: the ratio of ruled-out
to confirmed. A hunt logging nothing but confirmations is not being
sceptical enough, and the number that predicted a good report here was
how many of its own hypotheses a hunt killed.

Stop the watcher when the hunts finish. A poller left running is the
same waste as a heartbeat nobody stops.

## How hunting compares with the other instruments

None of these replaces another; they fail in different directions.

**The regression suite** answers "is what we fixed still fixed". It
cannot find anything nobody has thought of, and by this project's own
record roughly one test in five, when written, cannot fail at all.
Hunting the SUITE is therefore its own direction, and a productive one.

**Mutation testing** answers "would the suite have noticed?". That is
a question about the tests, not the software. It is worth running for
exactly that — a catalogue sweep returning 173 caught and 1 accepted
is real assurance — but across 128 survivors here it has produced no
product defects, and a campaign budgeted as defect-hunting will disappoint.
Full argument in docs/MUTATION-TESTING.md.

**Differential tests** (UI against library, colourspace against
upstream's own render, project round trips) are the strongest
standing instrument this project has, because a disagreement is a
defect by construction and needs no oracle. Their weakness is that
somebody has to build each pair, and a pair with a motionless axis
silently checks nothing.

**The randomised sweep** finds what nobody suspected, which is its
whole value, and it is the only instrument here that has done so by
accident. Its weakness is that a failure is expensive to read: one
red sweep cost an afternoon of bisecting to establish that the
plugin was right and the fixture was dirty.

**A second machine** (the Linux CI leg) finds what is invisible where
you develop. Its first run found a defect no Mac could show.

**Hunting** is the only one of these that goes looking with a
hypothesis and no oracle at all. It is cheap in machine time and
expensive in judgement — every claim must be reproduced before it is
believed — and its yield depends almost entirely on the direction
chosen, which is why this file exists.

## What a "direction" means

A direction is not a place in the code. It is the QUESTION a hunt
asks, and the shape of answer it will accept. "Look at bridge.py" is a
place; "find a path whose twin does the same job differently" is a
direction. Two hunts pointed at the same file with different questions
find different things, and two hunts asking the same question in
different files find the same KIND of thing.

The record below is organised by question, because that is the
variable that mattered.

## The record

Counts are of defects CONFIRMED by independent reproduction, not of
claims made. A claim that did not survive checking is worse than
nothing, so it is counted against the hunt, not for it.

| Direction | Question it asks | Hunts | Confirmed | Notes |
| --- | --- | ---: | ---: | --- |
| **Backwards from harm** | "What would a user be furious to lose, and how could the software do that to them?" | 1 | 2 | Found the worst defect in the project's history on its first run. Its second claim — more classes than the column has values, so swatches appear that no tile uses — was confirmed and fixed on 2026-08-13 (evening), two probes later: the first errored, the second lacked a render context |
| **Instruments audit** | "Does each tool actually enforce the rule it claims?" | 1 | 6+ | Found the catalogue certifying tests that never ran, and (2026-08-13, evening) a documented command — the coverage report — that could never write a report at all, because the suite exits through os._exit |
| **Asymmetry / twins** | "What does this path do that its sibling does not?" | 5 | 9 | The most reliable code-reading direction here |
| **Suite dead axes** | "Which tests cannot fail?" | 1 | 3 | Two dead tests plus an always-true assertion |
| **Two stores of one fact** | "Which of these two records wins when they disagree?" | 3 | 4 | Yielded well; several claims needed narrowing on verification |
| **Unreachable branches** | "Which guard's precondition nothing produces?" | 2 | 3 | Also caught a red suite nobody had noticed |
| **One boundary but not another** | "Which crossing was not fixed alongside the ones that were?" | 3 | 5 | Strong on export/reopen. Two QML findings confirmed later: a file edited on disk never reaches the map, and a moved file is repainted away on the restyle path |
| **Write-only state** | "What is written and read back by nobody?" | 2 | 2 | Also misjudged a real defect as harmless — see below |
| **Preview against map** | "Do two renderings of one design agree?" | 1 | 1 | An unassigned element previewed in colour and drawn grey, confirmed and fixed. Its other claim — elements silently absent on dense designs — did NOT reproduce over ten configurations on 2026-08-13, and is counted against this direction |
| **Dialog against live layer** | "Does the plugin's belief match the layer?" | 1 | 2 | A column rename destroying categorical picks (fixed), and a provider-level edit invisible to both stores — kept as a documented LIMIT, and the docstring that claimed otherwise corrected |
| **Stochastic sessions** | No question — random actions, invariants checked after each | 1 | 2 | ~100 sessions. Most "breaks" were its own fixture; found a defect present since the first commit, and a crash it hit on three separate seeds |
| **Reduction beside pinning** | "Does the newer path re-ask the older path's question?" | 1 | 1 | Run 2026-08-15 as an asymmetry hunt over two paths that both change how many classes a map draws. Found the reduction counting the whole column while a pin had already removed a class and its samples |
| **The first five minutes** | "What does a user meet before anything is configured?" | 1 | 1 | Removing the region layer from a project holding three or more polygon layers emits no layerChanged at all, so the dialog holds a destroyed layer and says nothing. Confirmed in substance, NOT in detail: the hunt reported a KeyError modal, and what a second route measured was silence -- a Generate that produced no map and no refusal. Which of the two a user meets depends on whether the surviving layer carries the same column names |
| **Order of operations** | "What order does the suite always do this in, and what happens in the other order?" | 1 | **0** | Two claims, neither reproduced. A hand-typed spacing destroyed by the first Generate: measured at HEAD, the typed 250 survives, because the hunt read a commit PREDATING the fix for the field defect. A project opened under a showing dialog offering the plugin's own output as a region: not reproduced with live update on or off |
| **Suite fixtures as blind spots** | "Which fixture order could no user follow, and what happens in the user's order?" | 1 | 0 | Reproduced the shipped field defect independently and found a second door into it (swapping the region layer), both already closed at HEAD. Three further shapes measured EQUIVALENT to the fixture order, which is worth as much: nobody need re-check them |
| **Paired identity** | "A new artefact carries the identity of the thing it is paired with. What does every reader of that identity do now that two layers answer to one id?" | 1 | 2 | New 2026-08-16, and the most productive single question of that day. Found "Create as new group" deleting the KEPT result's no-data layers, and a GeoPackage style embedded before the opacity it was meant to carry. Its lesson went further than its findings: the sibling faults live in the per-element DICTS, and the tell is a reset list that names some records and not others |
| **Order of operations** (2nd) | "Which setting is acted on at LANDING but recorded from LAUNCH?" | 1 | 1 | Found `opt_outlines`, the only geometry-signature input the landing reads live, so toggling it mid-run cancels its own signature difference and the box goes permanently inert. Present since 0.23.0. Three sibling cases (opacity, ramp, style mode) measured EQUIVALENT, which is worth as much as the finding |
| **Write-only state** (2nd) | "Does each new record survive the journeys it must, and do the clear sites clear the same set?" | 1 | 1 | A project opened under an OPEN dialog: three symptoms, one cause. The lesson is the transferable part — enumerate what a clear site LEAVES, not what it clears, and drive the reopened-project journey with the dialog still open, which no existing test did |
| **Tests that cannot fail** | "Which of the tests just written would pass with the behaviour broken?" | 1 | 3 | Aimed at fourteen tests written the same day, all mutated. Eleven killed everything; three had dead secondary axes, including a tautology that had already been "fixed" once and a literal `x == x`. About one in five, which is this project's historical rate. Turned on our own work rather than the product, and worth repeating whenever a batch of tests is written in haste |
| **Mutation sampling** | "Would the suite have noticed this change?" | many | **0** | 128 survivors, no product defects. It measures the SUITE |
| **The classification nudge** | "What does shrinking every finite upper bound break?" | 1 | 1 | New 2026-08-16, pointed at a change three hours old. Found the nudge DELETING THE COLUMN'S MAXIMUM: the loop moved every finite-width range's upper bound including the LAST, whose upper bound is the maximum, so the largest value belonged to no range, drew as nothing, and a lower value wore the darkest colour. Confirmed by rendering onto a coloured ground, where that tile came back as the background |
| **Backwards from harm** (3rd) | "What would a user be furious to lose, among today's changes?" | 1 | (same defect) | Reached the SAME finding as the nudge hunt, independently and by a different route — it was forbidden to read the source and started from "a value drawn as a gap". Counted once, in the row above, because two hunts finding one defect is one defect. Recorded here because the independence is the evidence: three outings, three first-probe hits |
| **The absence categories** | "Does every reader of *what the classifier cannot place* agree with the split?" | 1 | 1 (+1 minor) | New 2026-08-16. The missing-values notice still counted NULLs alone: two NULLs and four infinities among 144 areas were reported as "2 of 144" while the map drew nine no-data tiles across seven areas, and an infinities-only column produced NO SENTENCE AT ALL. `_element_has_missing_values` had the same one-line scan. Fifth and sixth readers of a predicate widened that morning; the question now has one owner |
| **Tests that cannot fail** (2nd) | "Which of today's tests would pass with the behaviour broken?" | 1 | 2 | Twelve of the day's tests mutated PER ASSERTION, 28 mutants, ten killed everything. Two in twelve, holding this project's one-in-five. Both dead axes sat in tests whose primary axis was live, and one was in a test rewritten THAT MORNING to repair a dead axis — the repair asserted only silence, so deleting the notice outright still passed |
| **The class-bound margin** | "What does moving a class bound break that the last attempt did not?" | 1 | 2 | Third round against the same code in one day, and it paid twice: a RELATIVE margin is an ABSOLUTE gap, so at 2e12 it was two thousand wide and a real value a hundred below the bound was orphaned and drawn as nothing; and above ~1e5 QGIS's own formatter PRINTS the margin, so a legend read "100,000,000,000 - 999,999,999,000". The experiment was withdrawn entirely. Lesson: MAGNITUDE IS A FIXTURE DIMENSION -- every fixture in this suite lived between 0 and 50 |
| **Adoption on projectRead** | "What does a signal that restores state fail to restore?" | 1 | 2 | Aimed at wiring one hour old. Adoption took the group and not `_last_path`, so the next Generate saw a changed destination and built a SECOND group beside the one it had just adopted, both reading the same tables -- the double map the adoption exists to prevent, arriving through the adoption. Also found the connection unguarded and the read path running one of the constructor's three calls, so its own comment claiming parity with a fresh dialog was false |
| **The absence categories** (2nd) | "Does the record survive every journey the rendering now has?" | 1 | 2 (+1 minor) | The colour editor raised IndexError on ANY column holding an infinity -- a row builder still testing one key while its twin had been widened that morning -- so no colour on that element was reachable. And the value digest was built from finite values only, so a NULL edited to an infinity moved nothing, the paired layer kept last run's categories, and those tiles drew as holes |
| **The prose** | "Do the sentences a user reads still describe what the software does?" | 1 | 5 | UNTRIED until 2026-08-16 and productive on its first outing. A tooltip corrupted since 766cada and shipping ever since ("the sloleft step") -- invisible to `test_every_control_explains_itself`, which asks for existence, length and non-repetition, none of which a typo violates. A user guide claiming class bounds are not yours, false since pinning shipped in the same release. A changelog describing a half-fix replaced two hours earlier. It also reached the editor crash independently. Reading prose as CLAIMS finds what no test asserts |
| **Tests that cannot fail** (3rd) | "Which of today's tests would pass with the behaviour broken?" | 1 | 2 | 11 tests, 77 assertions, 41 aimed mutations, 39 killed at the intended line. Both dead axes were substring or fixture faults: `str(4) in "144 areas"` passed with the notice counting NULLs alone, and a MEMORY region layer round-tripped through a .qgz comes back valid with ZERO features, so the second Generate was refused and the closing assertions counted restored layers rather than fresh ones. Third round, third time both sat in tests whose primary axis was live |

**Two hunts, one defect, and it is counted once.** The nudge hunt and
the third backwards-from-harm outing found the same fault within the
hour, from opposite ends: one read the change and asked what it broke,
the other was forbidden the source and asked what a user would lose.
Recording both as findings would inflate the table; recording only one
would hide the more useful fact, which is that a code-reading
direction and a harm-first direction converged. The convergence is
also what made the claim safe to act on immediately.

Rows are updated as claims are judged, which is why several moved
after their hunt reported: a direction's number is what SURVIVED
verification, never what was claimed. One row moved DOWN that way —
backwards-from-harm was recorded at 2 on the strength of a claim
whose probe then errored before measuring anything, and a probe that
proves nothing must not be filed as a confirmation.

## What the record says, so far

**Direction beats effort.** Eight hunts reading code forward found
fourteen defects and none of them was the GeoPackage data loss, in
which choosing an existing .gpkg as the output destroyed every other
table in it. One hunt starting from "what would a user be angry to
lose" found it in its first hour. Its own ranked list had put that
harm THIRTEENTH of eighteen, guessed safe on the assumption that a
save dialog would guard it. The guess was wrong and the item was the
worst thing on the list — which argues for hunting in directions you
cannot rank in advance, not against it.

**Ask for a structural property, never for "a bug".** The two
best-performing directions ask whether something either is or is not
the case: does this path differ from its twin; does this tool enforce
this rule. An agent asked for that can say "no" and still have done
its job. An agent asked to find a bug is being asked to come back with
something, and it will. The first hunt run here without this framing
returned one claim that reproduced under no configuration tried.

**The instruments are worth auditing, and almost nobody does it.** A
defect in the plugin produces a wrong map. A defect in the tools
produces a wrong NUMBER that everybody then believes, which is worse
because it is invisible and trusted. The first audit of them found the
mutation catalogue reporting CAUGHT for entries whose named test does
not exist, because the lookup raises and the non-zero exit reads as a
kill — while the standards checker's regex validated the name by
reading only its first string literal. Two counting rules, wrong
together.

**The suite is a hunting ground, not just a net.** By this project's
own record, tests that cannot fail appear at roughly one in five. They
are worse than no test: they occupy the ground so nobody writes the
real one, and they report success forever. One sweep found two, plus
an `assert x or True`.

**Observations are more reliable than severity judgements.** The
write-only hunt correctly observed that an exported GeoPackage's saved
style carried an empty custom-properties block, and parked it as
costing "a colleague the tags, not the map". Those tags are what keep
plugin output out of the region chooser; without them the plugin
offers its own output as a region layer and the next map is tiled on
top of the last. The observation was exactly right and the triage was
wrong. Hunts report what they SAW; the maintainer decides severity.

**Verification is the bottleneck, and it is not optional.** Every
confirmed defect above cost an independent reproduction here, by a
route the hunt had not used. That is what keeps the count honest: of
the claims judged so far, most survived, one evaporated entirely, and
one had to be narrowed — a hunt reported a table-versus-map
disagreement, the fix made the map repaint unasked, and it turned out
to contradict a settled decision that a test had guarded for months.
Running more hunts does not raise throughput; it lengthens the queue.

**Repetition is the signal that separates a defect from a fixture
fault.** The randomised hunt's second real finding announced itself
by firing on three separate seeds in three separate batches -- an
emptied region layer making the dialog's fingerprint raise, from a
Qt slot, where nothing reports. Its fixture faults, by contrast, each
appeared once and then went away when the driver was corrected. So
when triaging a stochastic run, sort by how many independent seeds
produced the same shape before reading any of them; that ordering
would have put both real findings at the top and every false one
below.

**A queue of unjudged claims decays, and the decay is one-directional.**
The night of 2026-08-13 ended with seven reported findings nobody had
reproduced. Judging all seven the following evening took a few hours
and turned out this way: four confirmed and fixed, one confirmed and
kept as a stated limit, one deleted as unreachable code, and ONE that
did not reproduce at all. That last one had been recorded as "high
confidence" and, if true, as more serious than the item above it in
the list. Ten configurations later it is a claim that failed.
So the ratio to expect from an unjudged queue is roughly six in seven
real -- good enough that the queue is worth having, and far from good
enough to act on without checking. What makes the difference is that
the checking gets DONE: an unjudged claim keeps its stated confidence
forever, and confidence is the one thing reproduction can move.

**Two probes of mine proved nothing before the third one worked**, on
the same claim, and the reasons are worth naming because they are
generic. The first errored on a missing render context and was
recorded as untested. The second asked the renderer a question
without starting it, and got an answer that meant nothing. Only the
third -- startRender, ask which symbol each feature actually gets,
stopRender -- measured the thing. A probe that errors is not a
refutation, and a probe that returns without exercising the code is
worse, because it looks like one.

**Stochastic search works, and most of what it reports is its own
fault.** Eighty-five random sessions produced about a dozen invariant
breaks, of which one was a real defect — a ramp the dropdown offers
being refused while the user's hand-picked colours are destroyed for
it, present since the first commit and reachable in ordinary use. The
rest were the driver holding a reference to a layer it had deleted,
or intent it dropped itself. That ratio is the method's signature and
is not a criticism of it: no other direction here found something
that had survived every deliberate reading, and the price of that is
triage.

Three things made it work, and all three should be required of the
next one. **Seed everything and print the seed**, so a break is one
command to reproduce. **Shrink before reporting** — a forty-step
failure nobody can read is worth much less than a four-step one. And
**write negative controls**: sabotage the product deliberately, once
per invariant, and check each invariant actually fires. That last one
paid for itself here, because it exposed a hole in the hunt rather
than in the plugin — live update defaults to ON, and one invariant
was only checked when no run was possible, so four batches had barely
exercised it at all. An invariant that never fires is either sound or
broken, and only a control tells you which.

## 2026-08-15, third round: what a moving HEAD does to a hunt

Three hunts on the principle that a fixture must match the ORDER a
user works in. Between them, four claims and ONE defect.

**A hunt reads a commit; the tree does not stop for it.** Two of the
three read `c7b787c` and reported defects that `0f6f5c0` had already
fixed -- one of them the very field defect the fix was written for.
The existing rule (probe a `git archive HEAD` copy and stamp the
commit) was followed exactly, and it was not enough, because it makes
a hunt reproducible without making it CURRENT. The missing half: a
hunt re-reads HEAD before it reports, and says whether HEAD moved
under it. The one that did this caught its own two findings turning
into history and said so; the one that did not filed a fixed defect as
live, with high confidence, and cost an evening's verification.

**A verification's own fixture can hide the harm it is verifying.**
The first reproduction of the surviving finding gave every layer the
same column names, so removing the region layer silently tiled a
different region and looked harmless. The same probe with DIFFERENT
columns showed a Generate that did nothing at all. The rule this
project already has for tests -- when a test mutates a fixture, check
the mutation changed something -- applies to the probes that judge
hunts, and they are written faster and with less scrutiny.

**Equivalence is a finding worth reporting.** One hunt measured three
shapes as equivalent to the fixture order and said so. That is not a
null result: it is ground nobody need walk again, and it is the only
kind of answer that shrinks the queue rather than lengthening it.

## What the mechanics cost, measured 2026-08-15

The audit that produced the harness and the portfolio rule. The
numbers are kept because the changes only make sense against them, and
because anybody proposing to undo one should have to argue with the
measurement rather than with the conclusion.

**Token cost.** Three hunts in one round: 165,391, 193,261 and 215,315
tokens, over 58, 96 and 57 tool calls. 573,967 in total, for four
claims of which ONE survived verification. The two rounds before it
returned 1.17 and 1.25 confirmed defects per hunt against this round's
0.33 -- and the difference was not effort or mechanics but DIRECTION:
both earlier rounds were pointed at code written the same day.

**Setup rebuilt every time.** 373 one-shot probe scripts in one
session's scratchpad, median 79 lines, of which roughly forty were the
same boilerplate re-typed -- standing up QGIS, a project and a dialog.
Names ran `hd_probe1` to `hd_probe9` and `stores_probe1` to `8`: a
fresh file per hypothesis rather than a case on a runner. Order of
18,000 lines written and read back, comparable to one whole hunt.

**And the setup was WRONG.** Eleven hand-written shell wrappers, every
one of them setting `QGIS_PREFIX_PATH` to the doubled path that leaves
QGIS unable to find its style database. Those hunts probed a QGIS with
NO STOCK COLOUR RAMPS and none of them knew. This is the finding that
turned an efficiency audit into a correctness one: a shared harness
would have been wrong once instead of eleven times, and would have
been fixed for every future hunt the day the prefix was understood.

**Stale trees.** Two hunts of the three read a commit that a fix landed
on top of while they ran -- about 350,000 tokens, 60% of the round,
spent confirming defects that no longer existed. One of them filed the
very defect the fix had been written for, with high confidence.

**Unreadable logs.** Two of the three logs drifted out of the
`RESULT: confirmed` shape the supervision loop greps, so watching them
meant reading them whole. A format that is advisory is a format that
costs more to check than to follow.

The scratchpad itself held 30,580 files and 1.8 GB by the end of the
session -- disk rather than tokens, and harmless, but a fair measure
of how much of hunting had become file management.

## The portfolio rule, and why yield is the wrong thing to maximise

Added 2026-08-15 after auditing what hunting costs. Three hunts that
night spent 573,000 tokens between them and produced ONE confirmed
defect, against 1.17 and 1.25 per hunt in the two rounds before. The
obvious conclusion -- point every hunt at whatever scores best -- is
wrong, and the record above is the evidence.

FIVE OF THE THIRTEEN DIRECTIONS ARE THE SAME MOVE: asymmetry and
twins, two stores of one fact, one boundary but not another,
unreachable branches, write-only state. Each reads two code paths and
asks how they differ. They are efficient precisely because they are
pattern matches, and a pattern match finds only what the pattern has
a shape for. The portfolio drifted that way with nobody deciding it.

What the record says about the exceptions is sharper than any yield
figure. The worst defect this project has had -- an existing
GeoPackage chosen as output losing every other table in it -- came
from backwards-from-harm, AFTER eight code-reading hunts had walked
past it, and that hunt's own ranked list had put the harm thirteenth
of eighteen. The stochastic direction, at two confirmations from
about a hundred sessions, found something present since the first
commit that no deliberate reading had found. A process tuned on yield
cuts both of those first.

SO: hold about A THIRD of any round on directions that cannot
pattern-match -- backwards-from-harm, stochastic, and whatever is next
off the untried list -- and judge those on whether they find KINDS
nothing else finds, never on count. Rotate one untried direction per
round. Cross-platform divergence proved itself by accident on
2026-08-15, when a second machine found three faults no hunt would
have; that is the argument for the four still untried.

The sample is too small to tune further, and saying so is part of the
rule: one to five hunts per direction and single-digit confirmations
cannot distinguish 1.8 from 1.3. Rank crudely, spend the judgement on
the direction, and do not mistake the table for a model.

## Two hunts that should be TRIGGERED rather than chosen

Settled 2026-08-16, after a round in which three of four defects were
in code written that day. The yield of a direction is confounded with
the age of what it was pointed at: what repeats is not a clever
question but a productive question meeting FRESH WORK. So two of them
stop being choices and become triggers, fired at the same moment as a
push, with nothing waiting on what they find.

**A batch of tests written in haste gets a tests-that-cannot-fail
hunt.** Run twice now, on fourteen tests and then on twelve: six dead
axes between them, right on this project's one-in-five. That is a
rate, not a hunch, and a rate is a trigger.

**A fix that ships with a single hand-made fixture gets a hunt.** Paid
for on the day it was written down: the class-bound nudge shipped
green against one fixture whose shape was the only one immune to its
defect, and was deleting the column's maximum from real maps.

WHAT IS AND IS NOT AUTOMATED. The mechanical half — would the suite
have noticed this change — is `mutation.yml`'s incremental instrument,
which mutates only the lines that changed. It runs in its own workflow
precisely so it can never colour a push's status. The judgement half
is not automatable and is not pretended to be: an agent reading the
day's diff and asking what a user would lose is a hunt, and it is
dispatched by hand at the same moment.

NOTHING DEPENDS ON WHAT THEY FIND. Their output is a work list for the
next candidate, never a gate on this one, for the same reason the
new-code mutation guard stopped gating: a red that means "write some
tests over the next few days" is not a gate, and treating it as one
teaches people to route around it.

The portfolio rule still governs what ELSE runs. Triggering the two
above does not fill the slate: a third of any round's directions must
still be unable to pattern-match against the code, or the hunts
converge on the failure modes we already know how to see.

## Directions not yet tried

Written down so they are a decision rather than an oversight:

- ~~**Against an external oracle**~~ — TRIED 2026-08-16, twice, as the
  pixel-level hunts. Rendering the map and reading it, rather than
  asking the object graph, found the paired layer ignoring its
  element's opacity and then a hand-set opacity lost at every
  re-tile. Its technique is worth keeping: render the same scene on
  two backgrounds and opacity falls out per pixel without knowing any
  colour.
- **Cross-platform divergence** — the first Linux run found a defect
  invisible on any Mac. Nobody has hunted that seam deliberately.
- **The specification itself** — every hunt so far assumes the settled
  decisions are right and looks for code that fails them. None asks
  whether a settled decision is wrong.
- **Performance and scale** — a design that takes ten minutes and
  produces nothing is a harm, and nothing hunts for it.
- **The prose** — the user guide and help text make claims about
  behaviour; nobody has tested those claims as claims.

## How to update this record

Do this at the END of every hunt, before the findings are forgotten
and while the log is still on disk. It takes two minutes.

1. **Add or update the direction's row.** If the direction is new, add
   a row with its question. If it already exists, increase the hunt
   count and add any newly CONFIRMED defects. Confirmed means
   reproduced independently of the hunt that reported it, by a
   different route.
2. **Count claims, not impressions, and count against as well as
   for.** A claim that did not reproduce is recorded — in the notes
   column, in words. The value of this table depends on it being
   possible to look bad in.
3. **Write the lesson, not the incident.** If the hunt taught
   something about how to hunt, add it to "What the record says" as a
   short paragraph with the concrete evidence attached. If it taught
   nothing new, add nothing; a document that grows on every run stops
   being read.
4. **Move anything from "not yet tried" that you tried**, even if it
   found nothing. A direction tried and empty is more useful to the
   next person than a direction untried.
5. **Update `tools/bug_hunt_brief.py`'s calibration section** in the
   same pass. It carries the running tally that hunts themselves are
   told about, and the two must not drift.
6. **Say when.** Change the "Last updated" date at the top. A stale
   date is the only warning a reader gets.

The hunt logs live in the session scratchpad and do not survive. If a
hunt produced something worth keeping — a ranked harm list, an
invariant set, a reproduction worth rerunning — copy it into
`docs/process/` rather than leaving it in a temporary directory.


## 2026-08-15: seven defects, and a instrument that had gone quiet

Six hunts over one evening, all pointed at the pinned-bounds and
copy-to features added in 0.24.3. Seven defects confirmed here after
independent reproduction, every one of them a WRONG MAP rather than a
crash, and every one fixed with a regression test and a catalogue
entry that was proved to catch it.

Three lessons the directions themselves taught, worth more than the
individual finds.

**When one record holds two claims, test them COEXISTING.** The pin
record holds copied boundary VALUES and per-end pin FLAGS. Each
worked perfectly alone, which is exactly why nothing noticed that
together the pin did nothing: the button stayed down, the number was
stamped into the project, and the map did not move. Two of the seven
were this shape.

**When one door into a state is guarded and another is not, check the
unguarded door against every downstream guard sized for the guarded
one.** `pin_problem` refuses every pin on a constant column, so no
pin can put several classes on one value; a copy can, and the
colouring branch downstream had been written for the guarded door. It
left four of five classes on the placeholder grey they are built
with, and the element drew as no data.

**A hunt's OBSERVATIONS outrun its SEVERITY JUDGEMENTS, and its
arithmetic is worth re-deriving.** Every claim reproduced here in
substance; two did not reproduce in detail (a pool reported as two
values was three, a count reported as fifty was twenty), and one
claim was a designed behaviour with a real defect sitting inside it —
copying a ladder onto a column that cannot reach it is the feature
working, while the pin riding along unvalidated is not. Reproduce
independently before believing, and separate the part that is a
defect from the part that is the design.

**The instrument that had gone quiet.** Auditing the catalogue while
adding to it found SEVEN of 243 entries anchored on text that no
longer existed in the file they named. Such an entry matches nothing,
mutates nothing, finds no survivor and exits clean — it reports
nothing, which is indistinguishable from reporting success. Five had
gone silent in a rework the day before and two under the same
evening's fixes. `tools/check_standards.py` now reads every entry
with `ast` and fails when its anchor is absent; it caught one of this
evening's own fixes moving a line another entry stood on, within the
hour. One re-anchored entry then SURVIVED, which was the second half
of the finding: since the constant-column rework either of two
branches delivers the same result on a classed style, so mutating one
alone changed nothing the test could see.


## 2026-08-15, second round: four hunts on a feature five hours old

"Deferring to QGIS" was designed by `/grill-me` and built the same
evening. Four hunts were pointed at it before it had a full day's age:
its twins, its boundaries, races and two-stores, and awkward data.
Between them they found FIVE defects, every one of which reached the
map, and all five were fixed the same night.

The finds, because the pattern in them matters more than the count.
The restyle fast path had no deferral arm while the run-landing path
did -- found by TWO hunts independently, which is some evidence they
are reading real fault lines rather than each inventing one. An
element could never be taken back, because picking the style it had
before deferral restored the old signature exactly and both paths
then read "unchanged". A deferring element moved onto a text column
drew nothing at all, because the new mode string was not "Graduated"
and the text-field guard had never heard of it. And the row never
came back out of deferring when somebody changed their mind in the
dock, because reconciliation ran in one direction only.

**A NEW FEATURE IS THE BEST HUNTING GROUND THERE IS, and hours old is
not too early.** Every one of these five was introduced that evening.
Hunting a feature the day it is written costs a fraction of hunting
it a year later, and the hunts arrive while the person who wrote it
still remembers why.

**The strongest single lesson: when a commit adds a guard, grep its
TWIN before testing anything else.** Two of the five were a guard
added to one path and not to the identical path beside it, and in
both cases the suite's own new test walked through the guarded door.
A test written alongside a fix tends to exercise the route the fix
was written for.

**And the shape of the near-miss is worth as much as the finds.** One
hunt spent three iterations chasing a defect that was being fixed
underneath it in the shared working tree, and another wrongly refuted
a real finding because its probe imported the live tree rather than
HEAD. Both recorded it. The rule that follows: a hunt probes a `git
archive HEAD` copy, never the working tree, and stamps the commit it
read in every claim -- otherwise a sibling's uncommitted fix reads
exactly like a race, and an unfixed defect reads exactly like a fixed
one.
