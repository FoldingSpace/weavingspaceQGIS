# Running the mutation-score improvement loop

This is the runbook. `docs/MUTATION-TESTING.md` says what the score
means and what we promise about it; this file says how to actually run
a campaign, including the parts that are nobody's idea of interesting
and that cost real hours when they were learned the first time.

Run it when the score is unknown or stale, before a substantial
release, or after a body of work large enough that the incremental
guard on changed lines is not reassurance enough. A campaign is hours,
not minutes, so it is worth setting up properly rather than driving
each step by hand.

## The shape of it

One cycle, repeated until the target holds:

1. record per-test coverage;
2. sample a batch of mutants;
3. read the result honestly (rate, per module, timeouts, stalls);
4. triage every survivor into one of five kinds;
5. write the tests the real gaps deserve;
6. VERIFY each test kills, by adding it to the hand-picked catalogue;
7. go back to 1, because the suite has changed.

Step 6 is not optional and step 1 is not housekeeping. Skipping either
produces numbers that mean nothing, which this project has now
demonstrated twice.

## Running a cycle

    tools/loop/cycle.sh <seed> [sample] [workers]      # e.g. 5 30 3

That records coverage, samples the batch, and runs the incremental
guard against the previous release tag. Logs land in `$LOOP_LOGS`
(default `/tmp/weavingspace-loop`), one per stage, each stage
announcing itself with a timestamp.

Two or three workers. Each gets its own sandbox and its own QGIS
process, so nothing is shared. Measured here: six mutants took
thirteen minutes serially and seven with three workers, with identical
verdicts. Choose the number from CORES and from what contention does
to the VERDICTS, not from memory: per-mutant times inflate fifteen to
fifty per cent under load, and a mutant slowed past the watchdog's
patience is recorded as caught, so pushing the worker count until the
machine groans can quietly flatter the score. Watch the stall and
timeout counts, and back off when they rise.

Rough timings: coverage record about ten minutes, a batch of thirty
about fifteen minutes at three workers, triage and test-writing
longer than both. Budget an hour per cycle and expect several.

## Supervision

The machine should never be idle waiting for someone to notice, and a
watcher must report CHANGE, not state. Three things run alongside:

**A stage monitor** emitting each new line of the cycle's logs —
stage transitions, kill rates, thresholds, tracebacks. Track an offset
per file and print only what is new. A monitor that greps a whole log
each pass re-reports the same historical failure every cycle, which
makes the current state unreadable; one that polls for a string the
tool never prints stays silent forever. Both have happened here, the
second for twelve hours.

**A heartbeat**, every ten minutes: what is running, batch progress,
the latest rate, whether any watcher has stuck, and CPU against
elapsed for each worker, which is what distinguishes a blocked job
from a busy one. Take a FRESH reading each time. Reporting a cached number with an honest
timestamp still presents stale state as current.

**`tools/loop/health.sh`**, run whenever something feels quiet. It
covers the three failure modes that have actually occurred:

  * a watcher looping on a condition that can never be true;
  * a job alive but blocked — the tell is CPU time far below elapsed
    time, so both are printed side by side;
  * a job FINISHED whose result nobody claimed, leaving the machine
    idle. This is the most common and the least visible.

It prints the last line of every recent log verbatim, whatever it
says. Grepping only for expected progress patterns once made an
informative 350-byte log ("STALE COVERAGE: ... re-record first") look
empty, and a job that had refused to start look like one that was
never launched.

## Sweeping the hand-picked catalogue before a substantial release

The campaign above samples automatic mutants; the CATALOGUE
(`tools/mutation_check.py`) is the other instrument, and before a
substantial release the whole of it is re-run, because a refactor
elsewhere can quietly stop an old test from reaching the behaviour it
names and only re-breaking everything finds that. At well over a
hundred entries a serial sweep costs hours, so it is sharded:

    python3 tools/mutation_catalogue_sweep.py            # 4 shards

    python3 tools/mutation_catalogue_sweep.py --shards 2

Four shards is the DEFAULT for every long job here made of
INDEPENDENT units, not a tuning choice: the differential sweep takes
WEAVINGSPACE_SWEEP_SHARD=i/4 the same way, and both finish in about a
quarter of the time. See MAINTAINING.md.

Mutation judging parallelises safely — measured here: three workers,
identical verdicts — which full suites do not; that asymmetry is the
whole reason the sweep can be sharded while two suites at once remain
forbidden. The price is per-entry times inflating 15–50% under
contention, so the sweep prints its slowest entries and anything
marked ATTENTION is re-run ALONE before being believed: a mutant
slowed past a timeout can read as caught while it merely stalled.

**READ THAT FLAG'S DEFINITION BEFORE READING ITS NAME, because the
paragraph above is what a reader takes it for and it is only half.**
The sweep's own line is `verdict = "caught" if proc.returncode == 0
else "ATTENTION"`, so ATTENTION covers everything that is not a clean
kill: a SURVIVOR, an entry the tool REFUSED to judge, a crash, and a
stall. Contention is the least of those and, measured, the rarest. The
word SURVIVED never appears in a sweep log at all, which matters
because the obvious sanity check — grep the log for survivors —
answers a reassuring zero however bad the news is.
MEASURED 2026-08-27, the first full sweep of the 0.24.4 branch: 516 of
559 caught and 43 flagged, which at four shards read like contention
and was nothing of the kind. Re-run one at a time on an idle machine
the 43 came back **0 caught, 34 survived, 9 unjudgeable** — every one
of the nine an AMBIGUOUS ANCHOR, which is the tool refusing rather
than failing. So the solo re-run is not a tie-breaker against
contention; it is what turns one word into the three different
findings it is hiding, and each of the three needs a different act.
AND JUDGE THE SURVIVORS AGAINST THE LAST RELEASE before deciding what
they mean. Of those 34, thirty-three survived at `v0.24.3` as well, so
the catalogue had been losing entries quietly for a version while its
headline count went on describing 559 entries as though each held
something. Exactly one was the branch's doing. A sweep that reports a
number without that comparison cannot tell drift from a regression,
and the two are different work: drift is a round of its own, a
regression belongs to the change that caused it.
Never run the sweep beside a release's gates or beside the census;
one measurement at a time is how each stays a measurement. (Added
2026-08-09, the first night the catalogue was too large to sweep
serially in the time available.)

## Running either instrument on somebody else's machine

Both instruments want a machine to themselves for a long time: the
catalogue sweep is hours even in four shards, and the incremental
guard must record per-test coverage before it can mutate anything.
Run either here and the development machine is gone for the
afternoon, which in practice means they are run rarely -- and an
instrument used rarely is one whose findings arrive too late to act
on. So both can run on GitHub instead:

    bash tools/watch_remote_mutation.sh <branch> catalogue
    bash tools/watch_remote_mutation.sh <branch> incremental v0.24.0
    bash tools/watch_remote_mutation.sh <branch> both v0.24.0
    bash tools/watch_remote_mutation.sh <branch> catalogue v0.24.0 stable

ONE QGIS, and the CONTROL version by default rather than the current
one. These runs ask whether the TESTS still catch what they claim,
which is a property of the suite rather than of QGIS, so a version
matrix pays several times over for one answer. The control is the
default for two reasons: triage happens on the maintainer's machine,
and a survivor that will not reproduce on the QGIS you have is
painful for no reason; and `stable` is a MOVING tag, so pinning to it
would make two sweeps incomparable, a changed rate ambiguous between
the suite drifting and the tag moving -- the same reason a re-census
is a controlled before/after only while the source is unchanged. The
fourth argument asks a different version deliberately, which is worth
doing when the question really is whether a newer QGIS has stopped an
entry reaching its behaviour.

The script dispatches `.github/workflows/mutation.yml` and watches it
to the end, reporting CHANGE rather than state, reporting every
terminal outcome rather than only success, and treating its own
silence as a signal: no run appearing within two minutes means the
run was never created, usually because the workflow file is not on
that branch -- `workflow_dispatch` only offers workflows present on
the ref.

Three properties of that workflow are deliberate and should not be
tidied away.

**It is a separate workflow, and its status is its own.** These runs
answer "how good is the suite" and "has a refactor stopped an old
test reaching what it names". Neither should colour a candidate's
status, and neither should make anybody wait.

THIS PARAGRAPH SAID "IT NEVER RUNS ON PUSH" UNTIL 2026-08-19, and that
had been false since 2026-08-16, when the INCREMENTAL instrument was
deliberately triggered on every `pre-*` push -- the question "would the
suite have noticed what just changed" being worth asking of fresh work
every time. The workflow's own header comment carried the same false
sentence, fifteen lines above the trigger contradicting it.
IT WAS FOUND THE WAY THESE THINGS ARE. A pre-candidate push produced a
mutation run nobody expected; a watcher took the NEWEST run on the
branch and reported its verdict as the candidate's; and asking GitHub
directly showed TWO runs where the documents predicted one.
WHAT DOES NOT CHANGE is everything the separation is for: the steps
carry `continue-on-error`, the incremental guard is asked WITHOUT
`--require`, nothing in the release path reads it, and a red here means
"write some tests this week". SO A MUTATION RUN GOING RED ON A
PRE-CANDIDATE PUSH IS NOT A BLOCKED CANDIDATE -- and anybody watching a
branch must read the WORKFLOW NAME beside the conclusion before saying
what failed. A watcher taking `--limit 1` reads whichever workflow
finished last, which on a `pre-*` branch is the wrong one by design.

**It REPORTS rather than gates.** The steps carry
`continue-on-error`, and the incremental guard is asked WITHOUT
`--require`, unlike the copy release.py runs. A number that stops a
run belongs beside the gates; a number that informs the next round
belongs here. The findings are in the artifacts, not in the exit
status.

**The sweep is split across MACHINES as well as processes.**
`--slice i/n` takes a share of the catalogue round-robin, so each of
four runners gets a mixture of cheap and expensive entries rather
than one drawing the whole slow tail, and each still shards four ways
internally. The listing floor is applied to the WHOLE catalogue
rather than to a slice, or sharding would trip the very check that
exists to catch a broken listing.

The same workflow carried an EXPERIMENT, and on 2026-08-12 it
answered its question, so it is now a fact rather than an experiment:

    bash tools/watch_remote_mutation.sh <branch> gallery

**The visual gallery's thresholds are NOT tuned to one machine's
fonts.** It had been kept out of the push workflow on that belief for
months. Measured: 13 of 13 cases pass on QGIS 4.0.0, 4.0.3 and
stable, and the Linux renders agree with the library's own output at
dE mean 0.3 to 0.5 and p95 1.0 to 1.1 -- the same figures this
project's Mac produces, and far below the ~2.3 that is a
just-noticeable difference. The gallery now runs in ci.yml as its own
job on every push, fifty-five seconds in parallel.

Two things about how that answer arrived are worth keeping.

The doubt was already written down here, and it was right: the
gallery's SIBLINGS (`visual_pair` and `visual_gamut`) had been
running inside the suite on three Linux versions all along and had
never complained about a font. A belief with evidence against it,
left untested because testing it seemed expensive, cost months of a
gate nobody had.

And the first run of the experiment measured the wrong thing
entirely. All thirteen cases failed identically on all three
versions with ModuleNotFoundError, because `tests/visual_tests.py`
never put `libs/` on `sys.path` -- the same fix `tests/run_tests.py`
had received the day before. An experiment that fails uniformly is
usually broken rather than informative; read the failure before
reading the result.

What has NOT moved, and why: the Lab reference comparison, for the
same font reason and with no sibling evidence to doubt it; and the
incremental guard as a per-push GATE, because the coverage record it
needs costs a whole suite run under monitoring and would lengthen
every push. A gate that is red for reasons nobody can act on is one
people learn to route around, which is the same argument in every
case.

### The new-code guard moved out here too, and why

Until 2026-08-11 the incremental guard ran inside every candidate
with `--require 70`, and stopped the release below it. It does not
any more: `release.py` prints what it would have sampled and names
the dispatch command, and the run happens here, reporting.

The evening it changed, it ran fifty minutes against 2,274 changed
lines and reached 61.5%. Three separate things were wrong with it as
a gate, and the threshold being inconvenient was not one of them.

**It measured the wrong thing.** A single blended figure over changed
lines is precisely what docs/MUTATION-TESTING.md says not to quote:
deterministic logic runs high, Qt plumbing runs low, and a release
that is mostly dialog wiring is dragged down by its own shape. Per
module that run was bridge 4/5 and dialog 10/17 — a fair picture, and
a useless single number.

**It cost more than a candidate can carry.** Two mutants sat
twenty-one minutes each and timed out; three more ran past twenty
minutes against covering sets of 153 and 221 tests. Fifty minutes
bought 28 verdicts of 80, and the sample scales with the diff, so a
big release is exactly when it is slowest.

**And its red meant "write tests over the next few days".** That is a
work list, not a gate. A gate whose failure cannot be acted on before
the artefact ships is one people learn to route around — the same
argument this project already made for keeping the visual gallery and
the catalogue sweep out of the release path.

The per-test coverage record followed it out of the candidate the
same evening, for the same reason and with less argument: its only
consumer is `tools/mutate_auto.py`, so once the guard ran elsewhere
the record was twenty-two minutes per candidate spent producing a
file nothing in that candidate opened. It is still required and still
recorded where it is USED -- the remote run makes its own, and a
local campaign records one first, re-recording whenever the suite
changes, because a stale record overstates survivors. A stage kept in
the critical path to feed something that has left is habit rather
than evidence.

What is NOT claimed: that the survivors do not matter. Ten came out
of that half-run and they are the 0.24.1 test-writing list. What
changed is where the number is produced and what it is allowed to
stop.

**A remote run that exits `success` may have measured NOTHING.** On
2026-08-13 a dispatched census showed `success` in `gh run list` and
its artifact held sixteen lines, all of them a refusal: 13 tests were
absent from the coverage record, so the tool declined to sample and
said so. Nothing was measured, and the run list said it went fine.
Two other artifacts from that week had never been opened at all; of
the three, two turned out to say nothing and the third carried a real
finding. So OPEN THE ARTIFACT, every time, including when the tick is
green -- the exit status describes the workflow, not the measurement.
A run that answers nothing still has to be opened to find that out.

**Read the results as work for the NEXT release.** A survivor is a
claim about the tests, and the claim is false often enough to check
first -- count the call sites and read the named test before
concluding the suite is weak. The natural home for what these runs
find is the following candidate, not the one already through its
gates.

## Reading a batch honestly

Four outcomes, and they are not interchangeable:

**killed** — a test failed. The suite noticed.

**survived** — no test failed. Triage it.

**stalled** — the watchdog saw no CPU and no output for forty seconds:
the program really stopped, which is a genuine detection and counts as
caught. Verify it by re-running that mutant ALONE. Batch four's single
stall reproduced at exactly fifty seconds serially, so it was real.

**timeout** — the wall-clock ceiling was reached. This is NOT a
verdict and is excluded from the rate. Counting timeouts as caught
lets machine load flatter the suite; counting them as survivors blames
the tests for a scheduling decision. Batch five produced four
"stalls" at 313-314 seconds, all running the same 66 tests: not four
hangs, one ceiling, hit four times. The ceiling now scales at fifteen
seconds per test, and a crop of timeouts means it needs raising again
rather than that the tests need improving.

Always read the per-module breakdown. A blended figure lets
deterministic logic hide behind Qt plumbing: `bridge.py`, `catalog.py`
and `worker.py` have run at 100% while `dialog.py` sat at 54%, and
that difference is the whole story of where work is needed.

## Triage by DEMONSTRATION, not by imagining a harm

Do this before writing anything:

    <qgis python> tools/prove_equivalent.py \
        --file weavingspace_qgis/dialog.py --line 1710 \
        --old '      combo.blockSignals(True)' \
        --new '      combo.blockSignals(False)' \
        --scenario a_working_session

It copies the tree, applies the one line, drives the same scenario
against both, and compares everything a test could see -- the whole
dialog's state, every cell widget, and the counts of unit rebuilds and
preview refreshes. Scenarios live in
`tools/equivalence_scenarios.py`; add one when the watched line is
not reached.

**Why this comes first, with the numbers.** Triage by reading the code
and imagining what a user would lose was measured over one campaign:
of eight harms so imagined, SIX were false. Each cost a test written,
run, disproved and withdrawn. The two that held were found by this
instrument instead -- and one of them was a shipped defect that a
narrow comparison had already declared harmless.

It is also the cheap end of the tool shed. A mutant on a heavily
covered line is confirmed against every test that reaches it: 1,410
seconds against 164 tests, 1,763 against 220. This runs in under a
minute. Since most of the pool sits at that expensive end, probing
first and paying for the full confirmation only when something moved
is what makes that ground affordable at all.

**Read the verdicts exactly.**

*IDENTICAL* is evidence for an EQUIVALENT entry, and it is only as
wide as the snapshot and only for that scenario. Quote both.

*DIFFERS* names the dimension that moved. Assert THAT. It is the
difference between a test aimed at a behaviour and a test aimed at a
mutated token, and the tool hands you the behaviour for nothing.

*VACUOUS* means the mutated line never ran, so the two trees were
never given the chance to differ. This is the guard that matters
most: without it, a scenario that misses its line produces two
identical snapshots and looks exactly like a proof of equivalence.
It is the ambiguous-anchor fault in different clothes, and for the
same reason the tool refuses an anchor matching more than once --
two `blockSignals` sites here were textually identical for two lines,
one equivalent and one hiding a real defect.

**Not everything that differs is a gap.** Three sites came back with
one line moving, `preview_refreshes` 8 against 9, and state otherwise
identical: one extra repaint. That is not equivalence, so it does not
leave the denominator -- but the only test that could catch it would
count how often a private method ran, which is pinning an
implementation detail. Those are ACCEPTED, and lower the rate
honestly.

## Triaging a survivor

Five kinds, needing different answers:

**A real gap.** Most survivors, especially early. Write the test the
behaviour deserves — phrased as what a user would lose, never aimed at
the mutated token — then verify it kills.

**A weak assertion.** The test reaches the code and does not care
enough. Strengthen it where it bites.

**A test that no longer reaches what it names.** Refactors do this
silently. Fix the test, not the score.

**A redundant call site.** Deleting one of several identical calls
leaves the others to do the work, so no test can discriminate and none
should be contorted into trying. Count the call sites BEFORE believing
a survivor is a gap: `_update_layer_exclusions()` has two and
`_refresh_preview_colours()` had six when this was written and has
fifteen now, which is the point rather than an aside: a number about
the code is true until somebody adds one, and a census on 2026-08-12
turned up five survivors on that call whose harm could not be stated
after three attempts. Sometimes the distinction is
real and interesting — the constructor's exclusion call matters only
for a dialog opened on a project that already holds output — and
sometimes the second call is genuinely redundant, in which case delete
the code rather than defend it.

**Accepted.** Something real changes and no test we can write can
reach it -- a defence whose occasion lives outside the harness. Mark
the catalogue entry `accepted=True`, which is NOT `equivalent=True`:
equivalence claims nothing observable changed, acceptance claims
nothing observable can be reached. Both are expected to survive, and
both announce a CATCH as news, since a catch means the claim has
expired. Reach for this only after a real attempt: three separate
attempts to make `fit-to-design-on-show` testable failed before it was
accepted, and the third was made a year's worth of sessions later by
somebody who had not read that the first two existed.

**Equivalent.** No observable difference, so no test can catch it and
it leaves the denominator. This needs EVIDENCE — apply the mutation in
a sandbox and compare everything a test could see — recorded in
`EQUIVALENT` in `tools/mutate_auto.py`, where `check_standards.py`
enforces that each entry carries both an argument and a demonstration.
Be slow to reach for this. A mutant that looked equivalent (a live
flag initialised full) turned out to cause an extra tiling run after
every Generate; declaring it equivalent when the first test failed
would have excused a real defect.

Anything you accept without a test needs its reason written down. "It
requires a UI state the dialog cannot produce" is a reason. "It seems
harmless" is not.

## Verify the kill, every time

A test that passes is not a test that works. Add each new test to
`tools/mutation_check.py` as a `dict(name=..., file=..., old=...,
new=..., test=..., why=...)`, then run:

    <qgis python> tools/mutation_check.py --only <name>

ONE NAME PER RUN: `--only` given twice keeps the LAST, judges that one
entry, and prints "Checking 1 mutations" -- which reads exactly like a
full run of the set you asked for. Loop over the names in the shell if
you have several. (Measured 2026-08-27, having passed four names and
been told about one.)

It must report `caught`. This is the single most valuable habit in the
loop. In one session six tests were written to close gaps, verified to
pass, and then failed to kill the very mutants they were written for.
Three separate tests turned out to pass for the wrong reason: one
because switching a layer also auto-sizes spacing and spacing was in
the signature, one because a family name that does not exist made the
test skip itself behind a visibility guard, and one because it
asserted an implementation detail that was legitimately true.

**THE CATALOGUE'S REAL VALUE IS CATCHING YOUR OWN NEW GUARDS.** On
2026-08-19 it caught THREE in one sitting, all written that evening to
close defects a maintainer had just reported: one that repaired the
mutation on its way past by calling `show()` and `raise_()`, one that
ran where nothing was marked so its loop never executed, and one that
drove the icon builder while the dialog asked for half of what it
should. Each read exactly like a guard that works, each was written by
somebody who had just measured the defect, and none of them would have
been found by rereading. Prove every new entry the moment you write
it, and treat a SURVIVED verdict on your own fresh guard as the normal
case rather than a surprise.

## Integrity hazards, all of them observed here

**Stale coverage.** The record decides which tests are offered the
chance to notice a mutant, so tests missing from it cannot kill
anything. The error is one-directional: survivors overstated, newest
work ignored. `mutate_auto.py` refuses to SAMPLE against a stale
record; do not reach for `--allow-stale-coverage` to make that
message go away. A targeted `--only` re-judge proceeds with a warning
instead, because it asks whether specific known mutants are caught
rather than estimating a rate -- read those verdicts in that light,
since a survivor there may be untested by the RECORD rather than by
the suite.

**Do not edit tests while a cycle is queued.** Every test written
invalidates the coverage record the queued run depends on, and the run
then refuses to start, which reads as a job that died. This happened
twice in one campaign. Either let the cycle finish before writing
tests, or order the chain so coverage is recorded inside it, after the
editing is done.

**The environment carries state, and it can make a mutant
unobservable.** QGIS keeps its colour ramps in the user's profile, so
on a machine that has run the plugin before, the palettes are already
installed and a mutant that breaks installation changes nothing a test
can see. The test has to CREATE the condition -- remove one palette,
then require the installer to notice it is gone, which is what a first
run actually looks like. Before accepting that a mutant is
unobservable, ask whether the environment is quietly satisfying the
thing under test.

**Read the verdict lines carefully.** `mutation_check.py` prints
`caught` indented and `SURVIVED` at the margin. A grep written for one
will silently drop the other, and two unverified entries were nearly
recorded as kills that way. Prefer reading the tool's own summary
line to matching its formatting.

**A failing test inflates the score.** If any test fails on unmutated
code, every mutant it covers looks killed. Confirm the suite is green
before a batch. `--control` applies no mutation and requires the
sampled test sets to pass; use it after touching the harness.

**Contention converts into score.** See timeouts above.

**Sampling and re-judging answer different questions.** `--only
file:line` re-judges named mutations, which says whether a KNOWN gap
is closed. Only a fresh sample can estimate the rate. Never quote a
re-judged set as a batch result.

## The stopping rule

Quote the bound, not the fraction. `mutate_auto.py` prints an exact
Clopper-Pearson lower limit of the two-sided 95% interval, which is
the conservative convention deliberately.

What it takes to defend "at least 70%":

| mutants | kills needed | observed rate | bound |
|--------:|-------------:|--------------:|------:|
|      20 |           19 |           95% | 75.1% |
|      30 |           27 |           90% | 73.5% |
|      40 |           34 |           85% | 70.2% |
|      60 |           50 |           83% | 71.5% |
|     100 |           80 |           80% | 70.8% |

Choose the size from the rate the improvement rounds are converging
to. But that table understates the problem, because it asks only what
result would suffice, not how likely a good suite is to produce it.
The probability of CERTIFYING, given a true rate:

| n | kills needed | observed | true 0.75 | true 0.80 | true 0.85 |
|--:|-------------:|---------:|----------:|----------:|----------:|
|   30 |  27 | 90.0% |  4% | 12% | 32% |
|   60 |  50 | 83.3% |  9% | 32% | 72% |
|  100 |  80 | 80.0% | 15% | 56% | 93% |
|  150 | 117 | 78.0% | 23% | 77% | 99% |
|  300 | 226 | 75.3% | 48% | 98% | 100% |

Read the 0.85 column first. A suite that genuinely catches 85% of
mutants FAILS to certify on thirty of them about two-thirds of the
time, because 27/30 is a demanding result even when the underlying
rate is good. Batches of thirty are the right size for steering --
they find gaps cheaply -- and the wrong size for certifying anything.

So the endgame has two levers and they do different work. Raising the
true rate makes the SOFTWARE better and is the only lever that helps
when the rate is genuinely below target: no sample size will certify
0.72, and a bigger sample merely establishes 0.72 more precisely.
Raising n makes the MEASUREMENT sharper and is what converts an
already-good suite into a defensible claim. Improve until the point
estimate is comfortably clear of the target -- around 0.85 -- then
spend the hours on a large certification sample rather than hoping a
batch of thirty comes up 27.

Draw the certification sample in ONE run (`--sample 150`) rather than
pooling several. A single run draws distinct mutants from the shuffled
pool; separate seeds can resample the same mutant, and pooling is only
legitimate if the suite did not change between batches, which is
exactly the discipline hardest to keep over several hours. At three
workers, 150 mutants is a couple of hours; that is the cheapest part
of this whole exercise.

The campaign ends with a CERTIFICATION batch: run after the suite
stops changing, with no fixes made during it, on mutants never seen
before. Improvement rounds cannot certify themselves — measuring
against mutants you have already fixed against is circular. Record the
rate, the bound, the per-module split, the timeout count, and the
suite stamp the tool prints.

Then update the campaign history table in `docs/MUTATION-TESTING.md`,
including the bad batches. A record that shows only the good rounds is
not a record.

## What a cycle actually costs, from this campaign

Batches of thirty at two or three workers ran fifteen to twenty-seven
minutes; the coverage record about ten; triage, test-writing and
kill-verification longer than the machine time in every cycle. Roughly
two thirds of the elapsed hours were the human-shaped half, and most
of the wasted time was neither: it was the machine standing idle
between stages because nobody noticed a job had finished, which is why
the supervision section above exists at all.

Per batch, expect eight to fifteen survivors early on, most of them
real gaps rather than curiosities. Expect one or two of the tests you
write to pass without discriminating; that is normal and is exactly
what step 6 is for.

## Run it with QGIS's Python, and it will stop you if you do not

`tools/mutation_check.py` is invoked with `env -u PYTHONHOME -u
PYTHONPATH python3`, because a plain `python3` that has inherited the
QGIS environment dies at bootstrap. That is right for the MODULE and
was wrong for the TESTS it launches: until 2026-08-19 it ran each one
with `sys.executable`, which under that invocation is the system
python3 -- an interpreter with no QGIS in it. Every test died at
`import qgis.core`, and a test that fails is scored `caught`, so the
catalogue reported success for seventeen entries in a row.

So source the environment first, which exports `QGIS_PY`:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \
            | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen
    env -u PYTHONHOME -u PYTHONPATH python3 tools/mutation_check.py --only <name>

The tool now REFUSES to judge anything when the interpreter it would
use cannot import qgis, and names the command above.

THAT REFUSAL FIRED EVERY TIME FOR A DAY, and the reason is the same
trap wearing the other face. `env -u PYTHONHOME` is right for the
MODULE and fatal for the CHILD: the macOS cask's interpreter carries
the paths of the machine it was built on and cannot start without a
PYTHONHOME, so the guard's own probe -- inheriting the stripped
environment -- reported that QGIS_PY had no QGIS when nobody had told
it where its standard library lives. Found 2026-08-19 by meeting the
refusal on a machine where the tests demonstrably ran.
So `tools/macos_qgis_env.sh` exports the value TWICE, once as
PYTHONHOME for whoever sources it and once as QGIS_PYTHONHOME for
whoever must strip the first and hand it to a child, and
`mutation_check.child_environment` puts it back for the probe and for
every test it launches. A copy under a second name is not tidiness; it
is the only thing that survives `env -u`.
ASK OF ANY GUARD YOU ADD what it does when the thing it checks is
fine and the CHECK is broken. This one could only refuse, which is
the mirror of the fault it was written to fix -- that one could only
confirm. It also runs each
test unmutated once, cached per test name, and reports UNJUDGEABLE
rather than a kill it cannot justify -- so an entry whose test cannot
pass in that harness is never counted as a guard.
