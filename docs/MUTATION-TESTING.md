# Mutation testing: what we measure, and what we promise

Coverage tells you a line ran. It cannot tell you whether anyone would
notice if that line were wrong. Mutation testing asks the second
question directly: change the code so it misbehaves, and see whether
the suite complains. A mutant the tests fail to notice marks a
behaviour nothing is really guarding, whatever the coverage report
says.

This document records how the campaign is run here and, more
importantly, the rules that keep the resulting number honest. A
mutation score is trivially easy to inflate — narrow the operators,
call awkward survivors "equivalent", write assertions that pin the
mutated token — and a score inflated that way is worse than no score,
because it is used as evidence.

## The two harnesses

`tools/mutation_check.py` holds hand-picked mutations, one per
behaviour somebody believed was guarded. It is a regression record of
our own guards: break the behaviour, confirm the test fails. All 41
entries are currently caught (one is marked equivalent, with its
reasoning). Its kill rate measures the chooser's judgement, not the
suite, so it is not the measurement.

`tools/mutate_auto.py` is the measurement. It walks the syntax tree of
the plugin source, generates every mutation its operators permit
(currently 1,049 of them), samples with a seeded shuffle, and runs
against each mutant only the tests whose recorded coverage touches its
line — usually seconds rather than the minutes a full suite run costs.
Everything happens in a throwaway APFS clone of the tree, so an
interrupted campaign cannot leave a deliberately broken line behind.
That is not hypothetical: a killed audit did exactly that once, before
the sandbox existed.

## What the score is

Mutants caught, divided by mutants tried, with proven-equivalent
mutants removed from the denominator before sampling rather than
counted as failures.

A mutant that makes the tests **hang** counts as caught. A hang is a
test noticing, via the watchdog, that the program stopped behaving —
it is a real signal, not a courtesy. Mutants on lines that **no test
reaches** are reported separately as uncovered rather than as
survivors: nothing failed because nothing looked, and folding those
into either column would misdescribe the suite.

## The commitments

These are the rules that make the number mean something. They are
listed here so that breaking one is a visible act rather than a quiet
convenience.

**A survivor is closed with the test the behaviour deserves, never a
test aimed at the mutated token.** Before writing anything, state the
harm a user would experience if the mutation shipped. If that sentence
cannot be written, it is not a gap — resolve it as equivalent, or
accept it and say why. Asserting `columnWidth(3) == 55` would raise
the score and improve nothing; every test added in this campaign is
one we would have wanted anyway. The Help tab that had silently
vanished, the output group that must sit at the top of the layers
panel, a layer's first field being treated as missing: mutants found
those, and the tests that close them read as behaviour, not as
mutation bookkeeping.

**Prefer deleting the line to defending it.** When a survivor marks
code that does not earn its keep — an unreachable defensive branch, a
duplicated default — remove the code. The score rises and the software
gets smaller. Writing a test to protect code that should not exist is
the worst available outcome, and it is the one a score target quietly
encourages.

**Equivalence requires evidence.** An equivalent mutant changes no
observable behaviour, so no test can catch it and it does not belong
in the denominator. But "this looks harmless" is how a mutation score
becomes a vanity metric. Every entry in `EQUIVALENT` (in
`tools/mutate_auto.py`) carries both an argument and a demonstration:
the mutation is applied in a sandbox and everything a test could see
is compared. The one current entry — blocking the over-under field's
signals during a family change — was retired only after showing that
the unit's `n`, every tile's WKT, the field text, the table, the
preview labels and all element assignments came out identical, because
the unblocked path merely restarts a debounce timer that was already
running.

**Exclusions are declared in the source and kept narrow.** Operators
are listed in the module docstring alongside what is deliberately not
mutated, so removing an awkward operator is a documented change rather
than a silent one. The only behavioural exclusion is table column
widths in pixels: 55 becoming 56 is invisible, and the only test that
could catch it would pin exact pixel values and break on every
legitimate layout tweak. An earlier draft of this exclusion covered
"pixel geometry" generally and was wrong — it would have swallowed the
dialog's computed height, the preview canvas minimum, and `setSpacing`,
which in this application is a distance in metres, not a layout gap.
Geometry here usually means the map, not the chrome.

**Rates are reported per module, never only blended.** `bridge.py` and
`catalog.py` are deterministic computation where a high rate is
reachable and cheap; the dialog's Qt wiring will always run lower,
because some of it is plumbing whose failure modes are genuinely hard
to observe. A single averaged figure lets the logic hide behind the
plumbing — exactly the weakness worth knowing about. The tool prints
the breakdown whenever a sample spans more than one file.

**Certification happens out of sample.** Every batch so far has been an
improvement round: sample, find gaps, fix them. Re-measuring against
mutants already fixed against is circular, and the resulting number
means nothing. The campaign therefore ends with a single certification
batch, run after the suite stops changing, with no fixes made during
it. The tool stamps every rate with how many tests ran and when the
suite was last edited, because a mutation score is a property of a
suite and expires the moment the suite changes. (A checksum would
detect edits too, but nobody here is forging test results — the
question a reader actually has is "is this still current?", and a date
and a count answer it where a hex digest does not.)

**Quote the bound, not the fraction.** Nineteen kills out of twenty
looks like 95%, but a suite whose true rate is 75% produces that
result often enough that the raw fraction cannot support a claim. The
tool prints an exact Clopper–Pearson bound, using the lower limit of
the two-sided 95% interval — deliberately the conservative reading,
since a one-sided bound reads several points higher on the same data
and picking the flattering convention is the same thumb on the scale
in a different guise.

**The whole campaign gets reported, including the bad batches.**

## Sizing a certification batch

What it takes to defend "the true kill rate is at least 70%", by the
conservative bound above:

| mutants | kills needed | observed rate | bound |
|--------:|-------------:|--------------:|------:|
|      20 |           19 |           95% | 75.1% |
|      30 |           27 |           90% | 73.5% |
|      40 |           34 |           85% | 70.2% |
|      60 |           50 |           83% | 71.5% |
|     100 |           80 |           80% | 70.8% |
|     150 |          117 |           78% | 70.5% |

The table is the reason not to fix the sample size in advance. A
suite that is genuinely near 90% can certify on 30 mutants; one near
80% needs a hundred, and no amount of wishing shrinks that. Choose the
size from the rate the improvement rounds are converging to, and if
the honest answer is a hundred mutants and several hours, spend them.

## Running it

The full procedure -- cycles, supervision, triage, the integrity
hazards and the stopping rule -- is `docs/MUTATION-LOOP.md`. What
follows is the mechanics of the tool itself.

```
QT_QPA_PLATFORM=offscreen PYTHONHOME=... <qgis python> \
    tools/mutate_auto.py --sample 30 --seed 3
```

Run `tools/coverage_per_test.py` first WHENEVER the suite has changed.
This is not housekeeping. The per-test line record is what makes each
mutant cost seconds instead of minutes, and it is also what decides
which tests get the chance to notice a mutation: a test that is not in
the record is never selected, no matter how squarely it covers the
line. Batch three was run against a record of 59 tests when the suite
held more, so every test written during the campaign was invisible to
the harness, and at least two of the reported survivors are lines that
an existing test asserts on directly. A stale record does not make the
score noisy, it makes it wrong in one direction: survivors are
overstated and the suite is flattered by its own newest work being
ignored.

`--workers N` judges N mutants at once, each in its own sandbox and
its own QGIS process, so no two workers share a mutation, a
QgsProject, or a temporary directory.

Measured on this project's machine (eight cores), six mutants at a
fixed seed: thirteen minutes serially, seven minutes with three
workers, and the two runs returned IDENTICAL verdicts on every
mutant, which is the check that matters. Contention is real and
visible in the per-mutant times, which inflated by fifteen to fifty
per cent (one went from 176 to 261 seconds) exactly as CLAUDE.md's
warning about concurrent QGIS processes predicts; the wall clock
still nearly halves, because the alternative is those same processes
idling one at a time.

Two workers is the standing default here, and the reason is memory
rather than cores: a worker is only about half a gigabyte, but the
development machine runs with swap nearly exhausted, and a run killed
at mutant nineteen of twenty has cost more than it saved. Raise it if
the machine has room.

`--only file:line,file:line` re-judges named mutations instead of
sampling. This is how an earlier batch's survivors get a second
hearing after the suite has been strengthened, which is a different
question from sampling fresh mutants and should not be mixed with it:
re-judged verdicts say whether a KNOWN gap has been closed, and only
a fresh sample can estimate the rate. Run `--control` after any change to the harness itself: it
applies no mutation and requires the sandboxed tests to pass. A 100%
kill rate means nothing if the harness fails everything, which is not
a hypothetical either — an early run reported a perfect score because
display names and function names had drifted apart and every test set
was empty.

## Keeping new code from eroding it quietly

A campaign measures the suite as it stands. It says nothing about the
code written next week, and rerunning hours of sampling on every
change is not a habit anyone keeps. The routine guard is therefore a
different, cheaper question, asked every release:

    tools/mutate_auto.py --since v0.22.0 --require 70

`--since` takes git's own diff and keeps only the mutations that fall
on lines added or changed since that revision. On an ordinary change
that is a handful of mutants and a few minutes, because the cost is
proportional to the change rather than to the codebase. `--require`
makes it a gate: below the threshold the release stops, on the
grounds that code arriving with tests that do not defend it is how a
score decays without anyone deciding to let it.

`release.py` runs this against the previous release tag, after
re-recording per-test coverage so that tests written alongside the
new code can actually be selected. Samples smaller than five are
reported without being held to a threshold, since a rate over three
mutants is not a rate. The first release, having no previous tag,
skips it and says so.

What this does NOT do is replace the periodic full campaign. Changed
lines are where new gaps arrive, but old code drifts too: a
refactor elsewhere can quietly stop a test reaching what it names.
Full sampling still answers "how good is the suite", and the
incremental gate answers "is this week's work defended". They are
different questions and the cheap one does not subsume the expensive
one.

## Measuring cheaply, and the traps in doing so

A mutant's cost is the size of its covering set, and that cost is
wildly uneven: of 2,579 covered lines, 30% are touched by one to three
tests and 33% by seventy-one or more. Three consequences shape how the
tool runs.

**Order each mutant's tests, likeliest killer first.** The cheap first
pass takes only the first `--max-tests` of the covering set, so the
ORDER decides whether a kill is found cheaply or the mutant survives
to a full confirming run. `rank_covering_tests` sorts by word overlap
between the mutated line and the test's name, then by how few lines
the test covers (a focused test is likelier to assert about this line
than a long integration session that passes through it). This cannot
change a verdict — a mutant is judged by exactly the tests that reach
it either way — only how soon the verdict arrives.

**Census a cost stratum rather than sampling everything.**
`--max-cost N` keeps only mutants covered by N tests or fewer and runs
EVERY one, so that stratum's rate is exact and carries no sampling
error. The output says so in the rate line itself, and says how many
reachable mutants were NOT measured. A stratum rate quoted as the
plugin's rate would be the most flattering mistake this tool could
make, which is why the scope travels inside the number.

**Re-run timeouts alone before discarding them.** A timeout is not a
verdict, so it is excluded — and every excluded run is work paid for
and nothing learnt. Batches 8 and 10 lost four each, almost all
mutants on heavily covered lines competing with three other workers.
The retry runs them one at a time with the ceiling tripled; whatever
finishes becomes a real verdict. It cannot flatter the score, since a
retry is as free to return "survived" as "killed".

## The measurement keeps flattering itself, and that is the pattern

Four separate defects, all the same shape: a number quietly favouring
the suite. Worth listing together, because the lesson is not any one
of them but that this KEEPS HAPPENING and should be actively hunted.

1. **Timeouts counted as kills** (batch 5). Four runs at 313-314s
   against a 300s ceiling were scored as caught, taking the batch from
   an honest 63% to 73%. Fixed by separating exit 124 from 125.
2. **A wall-clock watchdog through a sleeping machine** (batch 8).
   `time.time()` advances while a laptop sleeps, so a closed lid looked
   exactly like a hang and four verdicts were discarded. Fixed by
   moving every clock reading to `time.monotonic()`, which on macOS
   stops with the machine.
3. **Branch coverage keyed on colliding offsets.** Instruction offsets
   restart at zero in every code object, so a quarter of `bridge.py`'s
   decisions shared a key with an unrelated function; merged
   destinations made decisions look taken both ways when they were
   not, inflating the branch figure in every release report. Fixed by
   keying on the code object as well.
4. **Per-module rates counting timeouts as kills.** The headline
   excluded them; the by-module breakdown did not, so batch 10's
   modules summed to 77/100 against a headline of 73/96 — the
   discarded runs reappearing as successes in the one place a reader
   looks to find the weakest module. Fixed, and the per-module figures
   reported for batches 8 and 10 were wrong by that amount.

Three of the four were found by reading the code with fresh attention
rather than by any test, and the fourth by arithmetic that did not add
up. When a number here looks good, check how it is counted.

## Campaign history

| batch | mutants | caught | rate | what it taught |
|------:|--------:|-------:|-----:|----------------|
| hand-picked | 41 | 41 | 100% | measures our judgement, not the suite |
| auto 1 | 15 | 8 | 53% | catalogue option VALUES were unasserted; typed input reached the unit only because tests rebuilt it themselves |
| auto 2 | 20 | 7 | 35% | whole controls worked only because tests called the rebuild; the Help tab could be deleted unnoticed; a layer's first field was a boundary case |
| auto 3 | 30 | 15 | 50% | the region chooser could offer the plugin's own output; the spacing default and the Auto button could vanish; a catalogue offset could move. Understated: run against a stale coverage record, so the campaign's own new tests were never selected |
| auto 4 | 30 | 19 | 63% | lower limit 43.9% |
| auto 5 | 30 | 19 | 63% | first reported as 73%: four runs at 313–314s against a 300s ceiling had been counted as kills. Re-judged once timeouts were separated from verdicts. The batch that taught us machine load can raise a score |
| auto 6 | 30 | 23 | 77% | lower limit 57.7%, the best bound in the campaign until batch 8 |
| auto 7 | 30 | 20 | 67% | lower limit 47.2% |
| auto 8 | 60 | 41/56 | 73% | lower limit 60%, n=56. Four runs discarded to a machine that slept mid-batch (fixed: the watchdog now uses a monotonic clock). Every survivor was a DEFAULT, an INITIALISATION or a mark set once and read elsewhere; not one was in the tiling logic or the colour mathematics |
| auto 9 | 60 | 48/60 | 80% | CERTIFICATION: lower limit 68%, n=60, against a suite of 120. No code changed while it ran. All sixty judged — no timeouts, the first batch to lose nothing to the machine |
| auto 10 | 100 | 73/96 | 76% | **lower limit 66%, n=96**, against a suite of 123. Run to push the bound past 70% by sample size alone; it did not, because the rate fell from 80% to 76% and a lower rate eats the gain. A larger sample tightens an interval around WHATEVER rate turns up — it is not a ratchet, and this is the batch that proved it here |

The decline from 53% to 35% was not a regression. Batch two happened
to sample the dialog's wiring, where the suite was weakest, and that
is what a random sample is for. Both batches produced tests worth
having on their own terms, which is the actual return on the exercise
— the score is the instrument, not the product.

Rates from different batches are NOT pooled. Each measures a different
suite, because the campaign changes the suite between batches; adding
them together would produce a number that describes nothing that ever
existed. The claim to quote is a single batch's lower limit, and the
one to quote now is **68%, from batch 9** — the certification batch,
run with the suite frozen and nothing changed underneath it.

Where that leaves the 70% goal, stated precisely, because the two
readings of it differ. The measured kill rate sits in the high
seventies — 80% over batch 9's sixty mutants, 76% over batch 10's
ninety-six. The 95% lower limit is 68% and 66% respectively. Both
kinds of number are true and they answer different questions: the
suite very probably does catch about three or four mutants in five,
and the evidence is not yet enough to promise 70% with 95%
confidence.

Batch 10 was run on the theory that this was a sampling problem
rather than a testing one: at 80%, a hundred mutants would put the
lower limit above 70%. It did not, because the rate came in at 76%
instead, and a lower rate eats the gain from the larger sample. The
lesson is worth keeping, because it is easy to get backwards: a
bigger sample tightens the interval around WHATEVER rate turns up. It
is not a ratchet, and no amount of sampling turns a 76% suite into a
defensible 70% floor with room to spare — that takes killing more
mutants.

Two batches at 80% and 76% are also a useful reminder that a single
batch's rate carries real noise: with n=60, a suite whose true rate is
78% will report anywhere from about 67% to 88% one time in twenty.
Neither batch is evidence that the suite got worse.

Batch 8 also shows why sample size matters more than kill rate. Its
raw 73% is barely above batch 6's 77%, yet its lower limit is 60%
against batch 6's 57.7% — because 56 judged mutants pin the interval
far better than 30. Doubling the sample bought more confidence than
four batches of test-writing bought rate.

One caveat belongs with that number. Each worker runs from a sandbox
copy taken when the batch STARTS, so tests written while a batch runs
are not in it. Eight tests were added during batch 8, several closing
its own survivors, and none of them could affect its rate. The 60% is
therefore a floor under a suite that has since improved, which is the
honest direction for a bound to be wrong in — and the reason the
campaign certifies out of sample rather than mid-flight.
