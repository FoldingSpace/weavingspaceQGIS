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
verdicts. Three is affordable when the machine has memory to spare and
two is the safer default, since a worker costs 0.6-0.9 GB and this
machine often runs with swap nearly exhausted. A campaign killed at
mutant nineteen of twenty costs more than the parallelism saved.

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
the latest rate, whether any watcher has stuck, free swap. Take a
FRESH reading each time. Reporting a cached number with an honest
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

Mutation judging parallelises safely — measured here: three workers,
identical verdicts — which full suites do not; that asymmetry is the
whole reason the sweep can be sharded while two suites at once remain
forbidden. The price is per-entry times inflating 15–50% under
contention, so the sweep prints its slowest entries and anything
marked ATTENTION is re-run ALONE before being believed: a mutant
slowed past a timeout can read as caught while it merely stalled.
Never run the sweep beside a release's gates or beside the census;
one measurement at a time is how each stays a measurement. (Added
2026-08-09, the first night the catalogue was too large to sweep
serially in the time available.)

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
`_refresh_preview_colours()` has six. Sometimes the distinction is
real and interesting — the constructor's exclusion call matters only
for a dialog opened on a project that already holds output — and
sometimes the second call is genuinely redundant, in which case delete
the code rather than defend it.

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

It must report `caught`. This is the single most valuable habit in the
loop. In one session six tests were written to close gaps, verified to
pass, and then failed to kill the very mutants they were written for.
Three separate tests turned out to pass for the wrong reason: one
because switching a layer also auto-sizes spacing and spacing was in
the signature, one because a family name that does not exist made the
test skip itself behind a visibility guard, and one because it
asserted an implementation detail that was legitimately true.

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
