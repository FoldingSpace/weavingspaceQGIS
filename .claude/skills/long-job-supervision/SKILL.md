---
name: long-job-supervision
description: Supervise work that outlasts a single turn — test suites, builds, training runs, migrations, batch jobs — so the machine stays busy, finished work gets picked up immediately, and a stuck job is caught in minutes rather than hours. Use this whenever you start something long in the background, whenever a user asks for periodic status updates or says "keep going without me", whenever you are about to write a watcher or poll loop, and whenever a job seems to be taking longer than it should. Also use it before reporting that something is "still running" — that claim is worth exactly as much as the reading behind it.
derived_from:
  - path: docs/MUTATION-LOOP.md
    sha256: 7a230dcf1019dc2c6820402813041391c69a74041eddd0a3ef1b0fa333d179f4
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
process so nothing is shared, and watch memory rather than cores: a
campaign killed at unit nineteen of twenty costs more than the
parallelism saved. The asymmetry to respect: independent short
judgements shard well, but two timing-sensitive jobs (two full test
suites, a suite beside a mutation batch, anything beside a census)
degrade each other into false hangs and flattered scores — schedule
those serially, event-driven on each other's completion rather than
on a clock, so a quiet evening is used and a busy one is not
double-booked.

## Resource pressure

Check the resource that is actually scarce, not the one that is easy
to measure. On one machine the workers were only 0.5 GB each while
system swap sat at 22.8 GB of 23.5 GB used — the constraint was
everything else running, not the job. Readings there are also
volatile: free swap moved between 0.4 GB and 4.3 GB within minutes as
the OS resized its file, so a single favourable reading is not
headroom you can bank.

## Adapting this to a project

Substitute the process-matching pattern in the health check, the log
directory, and whatever resource matters on your machine (swap, disk,
GPU memory, API quota). The rules — wait on the process, report
change not state, CPU versus elapsed, fresh readings, chain the next
stage — carry over unchanged.
