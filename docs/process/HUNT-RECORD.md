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

Last updated 2026-08-13.

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
exactly that — a catalogue sweep returning 173 of 174 is real
assurance — but across 128 survivors here it has produced no product
defects, and a campaign budgeted as defect-hunting will disappoint.
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
| **Backwards from harm** | "What would a user be furious to lose, and how could the software do that to them?" | 1 | 2 | Found the worst defect in the project's history on its first run |
| **Instruments audit** | "Does each tool actually enforce the rule it claims?" | 1 | 5+ | Found the catalogue certifying tests that never ran |
| **Asymmetry / twins** | "What does this path do that its sibling does not?" | 3 | 6 | The most reliable code-reading direction here |
| **Suite dead axes** | "Which tests cannot fail?" | 1 | 3 | Two dead tests plus an always-true assertion |
| **Two stores of one fact** | "Which of these two records wins when they disagree?" | 2 | 3 | Yielded well; several claims needed narrowing on verification |
| **Unreachable branches** | "Which guard's precondition nothing produces?" | 1 | 2 | Also caught a red suite nobody had noticed |
| **One boundary but not another** | "Which crossing was not fixed alongside the ones that were?" | 2 | 2 | Strong on export/reopen; weaker on session boundaries |
| **Write-only state** | "What is written and read back by nobody?" | 1 | 1 | Also misjudged a real defect as harmless — see below |
| **Preview against map** | "Do two renderings of one design agree?" | 1 | 0* | Three claims, none yet independently verified |
| **Dialog against live layer** | "Does the plugin's belief match the layer?" | 1 | 0* | Two claims, none yet independently verified |
| **Stochastic sessions** | No question — random actions, invariants checked after each | 1 | 1 | 85+ sessions. Most "breaks" were its own fixture; found a defect present since the first commit |
| **Mutation sampling** | "Would the suite have noticed this change?" | many | **0** | 128 survivors, no product defects. It measures the SUITE |

\* Not zero because the hunt was weak — zero because verification is
the bottleneck and those claims are still queued. Update the row when
they are judged.

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

## Directions not yet tried

Written down so they are a decision rather than an oversight:

- **Against an external oracle** — the vendored library's own render,
  rather than one of our descriptions against another.
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
