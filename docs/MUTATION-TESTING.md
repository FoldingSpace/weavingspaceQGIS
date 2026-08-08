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

```
QT_QPA_PLATFORM=offscreen PYTHONHOME=... <qgis python> \
    tools/mutate_auto.py --sample 30 --seed 3
```

Run `tools/coverage_per_test.py` first if the suite has changed; the
per-test line record is what makes each mutant cost seconds instead of
minutes. Run `--control` after any change to the harness itself: it
applies no mutation and requires the sandboxed tests to pass. A 100%
kill rate means nothing if the harness fails everything, which is not
a hypothetical either — an early run reported a perfect score because
display names and function names had drifted apart and every test set
was empty.

## Campaign history

| batch | mutants | caught | rate | what it taught |
|------:|--------:|-------:|-----:|----------------|
| hand-picked | 41 | 41 | 100% | measures our judgement, not the suite |
| auto 1 | 15 | 8 | 53% | catalogue option VALUES were unasserted; typed input reached the unit only because tests rebuilt it themselves |
| auto 2 | 20 | 7 | 35% | whole controls worked only because tests called the rebuild; the Help tab could be deleted unnoticed; a layer's first field was a boundary case |

The decline from 53% to 35% was not a regression. Batch two happened
to sample the dialog's wiring, where the suite was weakest, and that
is what a random sample is for. Both batches produced tests worth
having on their own terms, which is the actual return on the exercise
— the score is the instrument, not the product.
