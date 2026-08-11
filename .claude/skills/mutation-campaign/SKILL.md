---
name: mutation-campaign
description: Run a mutation-testing campaign to measure and genuinely improve how good a test suite is — sampling mutants, triaging survivors, verifying that new tests actually fail, and deciding when a score can be defended. Use this whenever the user wants to know whether their tests are any good, asks about mutation testing or mutation score, says coverage looks high but they don't trust it, wants to raise a mutation score toward a target, or is writing tests to close gaps that a mutation tool found. Also use it when someone proposes to accept a surviving mutant as "equivalent", or asks how many mutants they need to sample — both are places where a campaign quietly turns into a vanity metric.
derived_from:
  - path: docs/MUTATION-LOOP.md
    sha256: b4f0a48e0483327563ba5b291a11a1e7904c598a5ce5920a333d630871269fa5
  - path: docs/MUTATION-TESTING.md
    sha256: 3afab0494ec033d810a461b55a22854db699effcb6394b2c8e9c6e1e27505b0a
---

# Running a mutation campaign

Coverage says a line ran. It cannot say whether anyone would notice if
that line were wrong. Mutation testing asks the second question by
breaking the code on purpose and seeing whether the suite complains.

The score it produces is trivially easy to inflate, and most of this
skill is about not doing that. A number that rose while the software
stayed the same is worse than no number, because it gets used as
evidence.

## The cycle

1. Record which lines each test executes.
2. Sample mutants at random and run, against each, only the tests that
   cover its line.
3. Read the result honestly: the rate, the per-module split, and any
   run that timed out rather than concluded.
4. Triage every survivor.
5. Write the tests the real gaps deserve.
6. **Verify each new test fails** when the fault it names is present.
7. Return to 1, because the suite has changed.

Steps 1 and 6 are the ones people skip, and skipping either produces
numbers that mean nothing. Budget an hour per cycle and expect
several; roughly two thirds of the time is triage and test-writing
rather than machine time.

## Verify the kill, every time

**A test that passes is not a test that works.** It has to fail when
the behaviour it names is broken, and the only way to know is to break
it.

Keep a catalogue of hand-picked mutations, each naming the test that
must fail under it, and run it as part of the release. Sweep it in
FOUR SHARDS by default, not serially -- judgements are independent,
so four processes finish in about a quarter of the time, and the
same default applies to any long job made of independent units. When the
catalogue outgrows a serial sweep — well over a hundred entries here
— shard it across concurrent clones: mutation JUDGING parallelises
safely (measured: three workers, identical verdicts), which full test
suites do not, and that asymmetry is what makes a sharded sweep sound
while two suites at once stay forbidden. The price is per-entry times
inflating under contention, so a sweep is a SCREEN: anything flagged,
and anything suspiciously slow, is re-run alone before its verdict is
believed, and the sweep never runs beside a release's gates or a
census — one measurement at a time is how each stays a measurement.
(This project: tools/mutation_catalogue_sweep.py, and the sweep
section of docs/MUTATION-LOOP.md.) In one campaign
six tests were written to close gaps, verified to pass, and then
failed to kill the very mutants they were written for. Three separate
tests turned out to pass for the wrong reason:

- one because switching a layer also auto-sized a spacing value, and
  the spacing was part of what the test compared, so the test passed
  on the spacing while the fault sat untouched;
- one because it selected a configuration name that did not exist, so
  a visibility guard silently skipped its own assertions;
- one because it asserted an implementation detail that was
  legitimately true whether or not the fault was present.

None of these is exotic. All three would have shipped as protection
that did not exist.

## Before triaging, suspect the catalogue

A survivor is a claim about the TESTS, and the claim is false often
enough to check first. Three ways a hand-picked entry lies while
looking healthy, all found in one sweep:

- **an ambiguous anchor** — the tool replaces the first occurrence,
  so an anchor matching several places mutates one site while its
  siblings keep the behaviour alive; the entry reports SURVIVED
  whatever the tests do. Make the tool REFUSE an anchor that matches
  more than once; it is a silent failure otherwise, and the loud
  version costs one line;
- **an entry naming a test that cannot reach it** — a guard in name
  only. Ask what the named test actually executes;
- **a redundant call site** — the same duty done twice means deleting
  one leaves the other to cover it. The answer is a scenario only the
  mutated site can serve, or, if there is none, deleting the code.

Count the call sites and read the named test before concluding the
suite is weak. Five of thirteen survivors in that sweep were the
first kind alone.

## Triaging a survivor

Five kinds, needing different answers.

**A real gap.** Most survivors, especially early. Write the test the
behaviour deserves, phrased as what a user would lose, never aimed at
the mutated token. Asserting `columnWidth(3) == 55` raises the score
and improves nothing.

**A weak assertion.** The test reaches the code and does not care
enough. Strengthen it where it bites.

**A test that no longer reaches what it names.** Refactors do this
silently. Fix the test, not the score.

**A redundant call site.** Deleting one of several identical calls
leaves the others to do the work, so no test can discriminate and none
should be contorted into trying. Count the call sites *before*
believing a survivor is a gap. Sometimes the distinction is real and
interesting: one call in a constructor and another after every run
look identical until you ask which one matters when the window is
opened on an already-populated project. Sometimes the second call is
genuinely redundant, and then the honest fix is to delete the code
rather than defend it — the score rises and the software gets smaller.

**Equivalent.** No observable difference, so no test can catch it and
it leaves the denominator. This needs *evidence*: apply the mutation,
then compare everything a test could see. Be slow to reach for it. A
mutant that looked equivalent — a "work pending" flag initialised full
rather than empty — turned out to cause a second, unwanted rebuild
after every user-triggered one. Declaring it equivalent when the first
test failed would have excused a real defect.

Anything accepted without a test needs its reason written down. "It
requires a state the interface cannot produce" is a reason. "It seems
harmless" is not.

## Reading a batch honestly

Four outcomes, and they are not interchangeable:

- **killed** — a test failed. The suite noticed.
- **survived** — triage it.
- **stalled** — the program genuinely stopped (no CPU, no output).
  That is a real detection via a watchdog, and counts as caught.
  Confirm it by re-running that mutant alone.
- **timeout** — the wall-clock ceiling was reached. **Not a verdict.**
  Exclude it from the rate entirely.

That last distinction matters more than it sounds. One campaign
recorded four "stalls" at 313–314 seconds against a 300-second
ceiling, all running the same 66 tests: not four hangs, one ceiling
hit four times, because mutants on heavily-covered lines get confirmed
against a large test set. Counting those as caught converts machine
load into mutation score. Scale the ceiling with the number of tests
being run, and treat a crop of timeouts as a sign the ceiling needs
raising rather than the tests improving.

Always read the per-module breakdown. A blended figure lets
deterministic logic hide behind UI plumbing: pure-computation modules
have run at 100% in the same batch where the interface layer sat at
54%, and that difference is the entire story of where work is needed.

## Sample size is a lever, not a formality

Quote a confidence bound, not the raw fraction. Nineteen kills out of
twenty looks like 95%, but a suite whose true rate is 75% produces
that result often enough that the fraction cannot support a claim.
Use an exact Clopper–Pearson lower limit, and take the two-sided
95% interval's lower limit rather than the one-sided bound — the
flattering convention is the same thumb on the scale in a different
guise.

`scripts/sample_size.py` computes what a given target requires, and
crucially, how likely a good suite is to achieve it:

| n | kills needed | observed | true 0.75 | true 0.80 | true 0.85 |
|--:|-------------:|---------:|----------:|----------:|----------:|
|   30 |  27 | 90.0% |  4% | 12% | 32% |
|  100 |  80 | 80.0% | 15% | 56% | 93% |
|  150 | 117 | 78.0% | 23% | 77% | 99% |
|  300 | 226 | 75.3% | 48% | 98% | 100% |

Read the 0.85 column first. **A suite that genuinely catches 85% of
mutants fails to certify on a batch of thirty about two-thirds of the
time.** Small batches are the right instrument for steering — they
find gaps cheaply — and the wrong instrument for concluding anything.

So the endgame has two levers doing different work. Raising the true
rate makes the *software* better and is the only lever that helps when
the rate is genuinely below target: no sample size certifies 0.72, a
larger sample merely establishes 0.72 more precisely. Raising n makes
the *measurement* sharper and is what converts an already-good suite
into a defensible claim. Improve until the estimate is comfortably
clear of the target, then spend the hours on one large certification
sample.

Draw that sample in a single run rather than pooling several: one run
draws distinct mutants, separate seeds can resample the same ones, and
pooling is only legitimate if the suite did not change in between —
exactly the discipline hardest to keep across several hours.

## Integrity hazards

**Stale coverage.** The record of which tests touch which lines
decides which tests are even offered the chance to notice a mutant.
Tests missing from it cannot kill anything, so a stale record
overstates survivors and ignores precisely the newest work. Re-record
after any change to the suite; make the tool refuse to sample against
a stale record rather than trusting anyone to remember. A targeted
re-judge of named mutants can proceed with a warning, since it
estimates no rate.

**A failing test inflates the score.** If any test fails on unmutated
code, every mutant it covers looks killed. Confirm the suite is green
before sampling. A control run — no mutation applied, same tests —
catches a broken harness that would otherwise report a perfect score.

**Re-judging is not sampling.** Re-running named mutants says whether
a known gap is closed. Only a fresh sample estimates the rate. Never
quote one as the other.

## Certification

End the campaign with a certification batch: run after the suite stops
changing, with no fixes made during it, on mutants never seen before.
Improvement rounds cannot certify themselves — measuring against
mutants you have already fixed against is circular.

Record the rate, the bound, the per-module split, the timeout count,
and which version of the suite produced it. A mutation score is a
property of a suite and expires the moment the suite changes.

Then write up the whole campaign including the bad batches. A record
that shows only the good rounds is not a record.

## Adapting this to a project

Substitute four things: the mutation generator (any tool that mutates
source and reports per-mutant verdicts), the per-test coverage
recorder, the test runner invocation, and the sandbox mechanism that
keeps mutations off the real tree. The rest — triage, verify-the-kill,
the timeout distinction, the statistics — is independent of language
and framework.

Two implementation notes worth copying. Run each mutant in a
throwaway copy of the tree, so an interrupted campaign cannot leave a
deliberately broken line behind; this is not hypothetical, a killed
audit did exactly that before sandboxing existed. And run mutants
concurrently, each worker with its own copy and its own process:
measured, six mutants took thirteen minutes serially and seven with
three workers, with identical verdicts, though per-mutant times
inflate 15–50% under contention.
