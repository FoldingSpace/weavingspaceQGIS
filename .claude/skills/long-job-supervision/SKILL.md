---
name: long-job-supervision
description: Supervise work that outlasts a single turn — test suites, builds, training runs, migrations, batch jobs — so the machine stays busy, finished work gets picked up immediately, and a stuck job is caught in minutes rather than hours. Use this whenever you start something long in the background, whenever a user asks for periodic status updates or says "keep going without me", whenever you are about to write a watcher or poll loop, and whenever a job seems to be taking longer than it should. Also use it before reporting that something is "still running" — that claim is worth exactly as much as the reading behind it.
derived_from:
  - path: docs/MUTATION-LOOP.md
    sha256: 40ae6ab8dfd7497c02fbcfd14713817d1fb8130ffd52b57b7ae1e58d6c7fcf60
---

# Supervising work that outlasts a turn

Long-running work fails in three ways that all look identical from the
outside, because all three look like silence:

1. **A watcher looping on a condition that can never be true.** It
   polls forever while the thing it watches finished long ago.
2. **A job alive but blocked.** The process exists, so everything
   looks fine, but it is waiting rather than working.
3. **A job finished whose result nobody claimed.** The machine goes
   idle and stays idle until someone thinks to look.

The third is the most common and the least visible. In one session it
cost fourteen idle minutes at a stretch; the first cost twelve hours.

## Two rules for watchers

**Wait on the process ending, not on log text you predicted.** A
watcher polling for `"tests recorded"` ran for twelve hours because
the tool actually prints `"recorded 75 tests"` — the same words in the
other order. Its fallback pattern missed the failure too: the crash
line read `Fatal Python error` and the pattern was a case-sensitive
`Error`. Silence from a watcher is not evidence the work is still
running.

If a log genuinely must be matched, make the alternation broad enough
to catch the failure modes as well as the success line, and
case-insensitive. Ask before arming it: *if this job crashed right
now, would my filter emit anything?* If not, widen it.

**A watcher must report change, not state.** A monitor that greps a
whole log each pass re-reports the same historical failure every
cycle, as though it were news, which makes the current situation
unreadable. Track an offset per file and emit only what is new.

**And expect to get watchers wrong, because of WHEN they are
written.** Five distinct watcher faults occurred in a single day on
one project, every one in a script written while attention was on
the thing being watched rather than on the watching: one repeated a
finished result every thirty minutes; one read the previous run's log
after a restart, reporting a dead job's stage beside a live job's
uptime; two matched the wrong process for their CPU field and
reported a busy job as idle; one reported a CI result from a run that
had been superseded. Each was individually trivial; the pattern is
not, and it is the same pattern each time — a throwaway script,
written in a hurry, for something more interesting than itself.

The remedy is to stop writing them fresh. One watcher that resolves
its log at each pass, names the process it measures, reports change,
and stops when its subject ends, beats five bespoke ones. If you
catch yourself writing the sixth, that is the signal.

The two failures are mirror images — one goes silent forever, the
other repeats itself endlessly — and both leave you unable to tell
what is happening now.

## Diagnosing a suspected stall

**Compare CPU time against elapsed time.** A process burning two
minutes of CPU across forty minutes of wall clock is blocked, not
busy, and that single ratio points straight at the cause. Print both
side by side in any status output; neither number means much alone.

Before concluding a job is stuck, check the plainest explanations
first: is the log growing, and is the last line an error message
rather than progress? A job that refused to start writes an
explanation and exits in a second, which is easy to mistake for a job
that died silently — especially if you grep for the progress lines you
expected instead of reading what is actually there.

## The health check

`scripts/health.sh` is a starting point: running work with elapsed and
CPU side by side, watcher loops with their ages, recent logs with
their staleness *and their last line verbatim*, finished-but-unclaimed
results, and leftover scratch directories.

The last-line-verbatim part is not decoration. Grepping only for
expected progress patterns once made an informative 350-byte log
("STALE COVERAGE: ... re-record first") look empty, and a job that had
politely refused to start look like one that was never launched.

Run it whenever things feel quiet, and specifically before saying
anything is still running.

## Heartbeats

**Arm the watcher AS YOU START THE JOB, in the same breath.** Not
afterwards, not when someone asks. The rule below was written on
2026-08-10 and broken the same evening: a ninety-minute sweep was
launched with no watcher, and the user had to ask for one. Writing a
rule and applying it are different acts, and the gap between them is
where the idle hours live. So make it mechanical -- launching a long
job has exactly three steps, in this order:

1. can it be SHARDED? FOUR is the default here when the answer is
   yes. Independent units (mutation judgements, sweep
   cases, per-file work) parallelise; timing-sensitive whole-suite
   runs do not. Four shards turn ninety minutes into twenty-five;
2. arm the watcher, with a filter covering failure as well as
   progress;
3. only then go and do something else.

Skipping step 1 costs hours of wall clock; skipping step 2 costs the
hours between finishing and being noticed.

**Run one whenever work outlasts a turn, not only when asked.** A
thirty-minute beat is the default for anything measured in hours. This
is not reporting etiquette; it is a defect-finding instrument, and it
earns its place by what it catches rather than by what it announces.
In one night of long jobs, four faults were found by beats and none by
waiting for completion: a sweep reporting "4/4 shards done" from logs
left by a run killed hours earlier; a catalogue sweep announcing
"CLEAN" after judging one entry of 156, because its listing crashed
under an environment variable and nothing checked the count; a census
started against a tree that had since changed, beside a SECOND census
launched by a chain; and a worker from an abandoned run still grinding
and writing into the log the new run was appending to. Every one of
those would have produced a number somebody believed. None was
visible in the final "done" line.

So the beat asks: what is running, with CPU against elapsed; progress
against the total; the newest result; and -- the part that does the
catching -- **is what I am reading actually from THIS run?** Check the
age of any file you summarise against the start of the work it claims
to describe.

Set the interval by how fast the state changes, then leave it alone:
half an hour suits stage-shaped work (a suite, a census, a batch),
because it is long enough that each beat carries news and short enough
that a stall is caught while it still costs minutes.

**Take a fresh reading each time.** Reporting a cached number with an
honest timestamp still presents stale state as current: a status
labelled 10:21 and posted at 10:31 reads as live, and the label
documents the staleness rather than curing it. If the reading is more
than a minute old, take another.

## Keeping the machine busy

Idle time between stages is the largest avoidable cost, and it comes
almost entirely from a person having to notice that something
finished.

**Chain the next stage behind the current one** rather than waiting to
be told. A single background script that runs stage after stage,
announcing each with a timestamp, gives a watcher something to report
and leaves no gap where nothing runs.

**Do the work that does not need the machine while the machine is
busy.** Triage, drafting, documentation and analysis cost nothing and
fill exactly the time a long job takes.

**Do not edit the inputs of a queued job.** If a chained stage depends
on a file you are actively changing — a coverage record, a config, a
fixture — the stage will refuse to start or, worse, run against
something inconsistent. Order the chain so the parts that consume your
edits are recorded inside it, after the editing is done.

**Parallelism is worth measuring rather than assuming.** Six units of
work took thirteen minutes serially and seven with three workers, with
identical results — but per-unit times inflated 15–50% under
contention. Give each worker its own scratch directory and its own
process so nothing is shared, and pick the worker count from the
level at which the RESULTS were shown to match a serial run — not
from a memory reading, which on some systems measures the OS
resizing a file rather than headroom running out. The asymmetry to
respect: independent short
judgements shard well, but two timing-sensitive jobs (two full test
suites, a suite beside a mutation batch, anything beside a census)
degrade each other into false hangs and flattered scores — schedule
those serially, event-driven on each other's completion rather than
on a clock, so a quiet evening is used and a busy one is not
double-booked.

## Sharding: the partition must be exact, and you must check

Sharding is the cheapest speedup available for work made of
independent units — a suite of order-independent tests went from 32
minutes to 11 on three processes, on a machine that had seven idle
cores while one worked.

It is also easy to get subtly wrong in a way that produces a WRONG
ANSWER rather than a slow one, so three rules:

**Deal round-robin, not in blocks.** Contiguous slices give one
worker the slow tail. Every nth unit gives each a mixture.

**Verify the partition, by construction and at runtime.** Each shard
should report how many units it was offered, and those numbers must
agree. On the first sharded run of one suite they read 285, 285 and
286 — and slices that disagree about the size of the whole are not a
partition, so something ran twice or not at all. The cause was a
nested registration: one test registered a probe of its own, which
consumed a slot, shifted every later unit into a different shard and
was itself skipped in two shards out of three. Anything that
registers work from INSIDE a unit needs exempting from the count.

**A merge step must refuse a partial or overlapping result.** Missing
shard, duplicate keys, disagreeing totals: all of them produce output
that looks healthy. Where the merged artefact feeds a later
measurement, a silent gap is worse than a crash — an incomplete
coverage record, for instance, never offers the missing tests the
chance to notice anything, and overstates the result in one
direction only.

**Widen every ceiling while sharding.** Concurrent processes inflate
per-unit times by 15-50%; a ceiling sized on a quiet machine becomes
a false stall on a busy one.

## What must NOT be sharded

A MEASUREMENT beside another measurement. Two timing-sensitive runs
degrade each other, and where the thing being measured is time — a
suite with debounces, a benchmark, anything with races — contention
does not merely slow it, it changes the answer. Failing tests touch
fewer lines; slow ones trip watchdogs; a mutation batch loses mutants
to timeouts and reports a better score than the tests earned.

The asymmetry to hold onto: independent short JUDGEMENTS shard well,
whole timing-sensitive runs do not.

## Before sharding, ask whether the work should exist

The largest saving is usually not parallelism. Two stages of one
release ran the same suite under the same instrumentation, differing
only in whether they attributed results per-test or in aggregate:
ninety minutes for two views of one measurement. Sharding would have
cut that to thirty. Deriving one from the other cut it to nothing.

Parallelising duplicated work makes the duplication cheaper and
permanent. Look for it first.

## Ceilings catch hangs, and nothing else

Every timeout is a claim about how long healthy work takes, and the
claim is usually made from the machine in front of you. That machine
is the fastest one the job will ever run on.

Two ceilings were set and both were wrong within hours (2026-08-11):
a forty-minute CI job limit sized against a twenty-four-minute local
suite, where the remote legs took 52-54 and one was cancelled
mid-run; and a ten-minute per-test watchdog against a test already
measured at 550 seconds elsewhere, which passed by ten per cent and
stalled on the next round. Each produced a red result that meant
nothing, and a red result that means nothing is how a gate gets
ignored.

- **Size from the slowest MEASURED figure, then multiply.** Not from
  a guess, and not from your own machine.
- **Treat spread as data.** The same code took 392s, 486s and 550s on
  three legs of one run: that spread is the environment, and the
  ceiling has to clear all of it.
- **Give a legitimately long unit a named allowance with its
  measurement written beside it.** A bare number gets doubled by
  whoever is annoyed by it; a number with a reason gets raised by
  whoever meets it, deliberately.
- **A watchdog is not a performance budget.** If you want to know
  that something got slower, measure it and report; do not enforce it
  with a killer whose only vocabulary is "hung".

## A long job that blocks, against one that reports

Before putting a long measurement in front of a deadline, ask what
happens when it comes back red. If the honest answer is "we write
tests over the next few days", it is a work list rather than a gate,
and putting it in the blocking path costs you the release AND, in
time, the instrument — gates that cannot be satisfied get routed
around.

One project ran a mutation guard inside every release: fifty minutes,
a sample that scaled with the size of the change, and a threshold it
missed at 61.5%. It stopped a candidate whose software had passed
everything else. Two of its units timed out at twenty-one minutes
apiece, so it could not even finish inside the window it was gating.

The fix was not a lower threshold. It was moving the measurement out
of the blocking path onto other hardware, where it REPORTS, and
triaging what it finds into the next release. The number stayed; what
changed was what it is allowed to stop.

Signs a long job belongs outside the critical path: its cost scales
with the size of the change, so it is slowest exactly when the work is
biggest; its result is a blended figure over things with genuinely
different characteristics; nobody can act on a failure before the
deadline it guards.

## Clocks: durations monotonic, timestamps wall

A sleeping machine advances the wall clock while accumulating no cpu.
Those two readings together are exactly the signature of a hang, so a
wall-clock watchdog kills healthy work that was carried to a meeting
-- which is what would have happened to a release here, had the clock
not been changed an hour earlier. `time.monotonic()` stops with the
machine on macOS.

So: every duration, allowance and progress figure reads the monotonic
clock; wall clock is kept only where a human compares it with their
watch. Never subtract one from the other, and watch for the mix
appearing in TEST FIXTURES after the code is fixed -- two here staged
wall-clock starts against monotonic code and only failed once the
code started caring.

The wider lesson: this exact defect was found and fixed in one tool,
and a tool written afterwards repeated it. A lesson recorded in one
place does not travel to the next by itself.

## Instrument before you need it

A child process that dies in C leaves an exit code and two empty
streams. `faulthandler.enable()` plus a printed line per phase turns
that into a named call, and both are three lines added in advance --
against a full remote round, here fifty minutes, added afterwards.

The same holds for any message that will be read from somewhere else:
report what was FOUND, not which assertion you reached. A child that
could not import its dependencies once failed an assertion about
tiles, and was diagnosed for two rounds as a locale defect because
the message named only the assertion.

## Resource pressure

Check the resource that is actually scarce, and first check that the
number you are reading measures scarcity at all. Swap on macOS does
not: the OS grows and shrinks its swap file on demand, so "4.8 GB of
5.1 GB used" describes the size of the file it currently keeps, not
headroom about to run out, and readings move by gigabytes within
minutes for that reason alone. Throttling a job on that signal costs
real time and buys nothing.

What does bear on a long job is CPU against elapsed, per worker,
which separates blocked from busy. And where the job is a
MEASUREMENT rather than a task, the thing to watch is whether
contention changes the ANSWER — a mutation worker slowed past a
watchdog is recorded as caught, so an overloaded machine reports a
better score, not merely a slower run.

## Adapting this to a project

Substitute the process-matching pattern in the health check, the log
directory, and whatever resource genuinely constrains your machine
(disk, GPU memory, API quota — and check that the reading measures
scarcity before you throttle on it). The rules — wait on the process, report
change not state, CPU versus elapsed, fresh readings, chain the next
stage — carry over unchanged.
