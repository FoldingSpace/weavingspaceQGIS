---
name: second-machine
description: Run an established codebase somewhere other than the machine it grew up on — a CI runner, a colleague's laptop, a container, a different OS or language version — and read what breaks correctly. Use this when adding CI to a project that has never had it, when a suite that passes locally fails elsewhere, when someone reports a problem you cannot reproduce, and when deciding which checks belong on the second machine rather than the first. Also use it before concluding that a second-machine failure is a defect in your code: most are assumptions, and telling those apart is the whole skill.
---

# What a second machine finds

A suite that has only ever run in one place is measuring that place
as much as it is measuring the software. The value of a second
machine is not redundancy. It is that assumptions become visible,
and they are invisible by construction: an assumption nothing has
ever violated leaves no trace in the code, the tests or the docs.

Expect the first run to fail badly and expect most of it to be
environment rather than defect. In one project's first CI run,
seventy tests failed; **sixty-nine were one missing package**. Six
rounds later it was green, and across all of them exactly one real
product defect surfaced. That ratio is normal and is not an argument
against the exercise — those assumptions were unfalsifiable until
something else ran the code.

## Read the whole log before diagnosing

The most expensive mistake available is summarising a failure and
then reasoning from the summary. A write-up of that first run named
two failing tests as "two real platform failures" and sent the next
session hunting a threading bug that never existed. The log said 3
passed, 70 failed, and the two named tests were simply the first two
somebody's eye landed on.

Count the failures. Group them by message. One cause usually wears
many costumes.

## The five kinds, in the order they appear

**The environment supplies something you never knew you depended
on.** Missing packages, a different Python, absent fonts, no display,
a different filesystem. The tell is a large number of failures with
one message. Fix at the cause, not per-test.

The subtler version is a path that only ever worked by luck: a
package that was importable because the repository happened to be on
`sys.path`, a wheel directory added by whichever module got imported
first. On the original machine the luck is indistinguishable from
design.

**Identifiers that differ only in case.** This appears wherever a
name leaves the language and enters a filesystem, a database, a
table name, an archive. One project met it three times in a day:
element ids past 26 running into `A` beside `a`, colour ramp names
where the platform shipped `Cividis` against the code's `cividis`,
and two data columns differing only in case that a GeoPackage cannot
hold. Whenever an identifier crosses out of your process, ask what
happens when something downstream folds its case.

Worth noting the shape of the ramp bug, because it generalises: the
installer checked existence case-INSENSITIVELY and the lookup matched
EXACTLY. Neither half was wrong alone. Two rules about the same
names, disagreeing, is the bug — and the machine that ships only one
casing can never show it.

**Documentation naming something the repository does not contain.**
Commands recommending a file that is gitignored, a script that lives
only in your working tree, a path from your home directory. Only
somebody who is not you can find these, and a clean checkout is the
first entity that qualifies.

**A crash with nothing to say.** A subprocess dying in C leaves an
exit code and two empty streams. Enable a fault handler and print a
line per phase BEFORE you need them: three lines up front against a
full remote round afterwards. And know that an empty stdout beside a
signal is not evidence the process was silent — it is equally
evidence that the buffer died with it. Flush, or exit without
teardown, or you will diagnose a crash that already told you the
answer.

**Ceilings sized for the wrong machine.** Timeouts, retries and
watchdogs encode how long healthy work takes on the machine they were
written on — which is the fastest one the job will ever meet. See
below.

**State your own machine has quietly accumulated.** The subtlest of
the five, because it hides faults rather than causing them. A user
profile, a style or template library, a package cache, a config
directory, a keychain, a login session: anything the software wrote
once and then found again. On the original machine the software works
because of something it did months ago, and nothing distinguishes
that from working by design.

One project met three of these in a single evening, all masked by one
profile. A path variable had been wrong for months, so the
application could not find its own resource database and started with
none of its stock colour ramps — invisible, because the developer's
profile already held them. Eight of those resources had then been
deleted from the software as "duplicates the platform already
provides" — invisible for the same reason. And the visual regression
gate had been certifying fidelity against a library the software
itself had seeded years earlier, so it was comparing the software
with its own past output and calling it agreement.

Each was found within an hour of a runner with an empty profile
existing, and not one could have been found before.

## Measure configuration somewhere nobody has been

The remedy for accumulated state is not a stronger assertion. It is
choosing a fresh state to measure in, and most tools give you one for
a line: a throwaway home or config directory, a temporary profile, a
container, `--no-rc`, a clean database.

Make the tool that decides a setting prove it there. One project's
setup script now picks its platform prefix by asking the application
how many resources it can see with its config directory pointed at a
`mktemp -d`. Asked with the developer's own profile, every candidate
answers "plenty" — so the measurement would have confirmed the wrong
setting exactly as confidently as the right one. In a fresh
directory, the wrong candidates answer zero and the right one answers
thirty-five.

The general question, worth asking of any check that reads
machine-accumulated state: **what would this say on a machine that
has never run our software?** If the answer is "the same thing", it
is measuring the developer, not the software.

## Deduplicate against what the platform HAS, not what it can make

A specific and expensive confusion, worth its own line because it
reads as obviously correct while being wrong.

When you drop something from your own software because "the platform
already provides it", the question is what the platform actually
HOLDS, not what its API is capable of producing. One project removed
thirty-five bundled colour palettes as duplicates, having compared
its list against the platform's list of scheme names it can
SYNTHESIZE. Eight of those schemes were not present as resources at
all: the platform could generate them on request but had no entry
under that name, so looking one up returned nothing. The eight
removed were, as it happens, the whole of one category — every
palette meant for categorical data, gone from every fresh install.

Ask the dependency for its inventory, not for its capabilities, and
prefer to ask it at run time on a machine with nothing in it.

## Ceilings are the most common own goal

A limit a healthy run can reach produces a red result that means
nothing, and a red result that means nothing is how people learn to
ignore red results. Sized from the wrong machine, three times in one
day on one project:

- a job limit of forty minutes against legs that take 52–54;
- a per-test watchdog of ten minutes against a test measured at 855
  seconds elsewhere;
- the same watchdog against a suite whose per-test costs multiply by
  six when run under coverage instrumentation.

The rule: **size from the slowest MEASURED figure, then multiply**,
and treat spread as data. The same code taking 392, 486 and 550
seconds on three legs of one run tells you the environment varies by
40%, and the ceiling has to clear all of it.

## Choosing what belongs on the second machine

Not everything should move. The test is whether a failure there would
be actionable.

**Belongs**: anything that exercises code the first machine cannot
reach (a provisioning path that only fires where a dependency is
absent), anything about the ARTEFACT rather than the source, and
anything cheap that fails for reasons nobody has to interpret —
packaging, metadata, link resolution.

**Does not belong**: checks whose thresholds were tuned to one
machine's rendering, fonts or timing. They will fail for reasons that
mean nothing.

**And be suspicious of a check that is red by design.** One audit
tool reported a version mismatch that the release process mends
itself, so gating pushes on it would have been permanently red.
Either give the tool a mode that asks only the questions with
actionable answers, or leave it out.

## The artefact nobody opened

Ask what the user actually receives, and whether anything has ever
opened THAT — not the source it was built from. A project whose every
test imported from the working tree had never once unpacked its own
release archive and loaded it the way its users do. That check found
a fault on its first run.

## Read a second-machine failure as a question, not a verdict

Before concluding the code is wrong, work out which of these it is:
an assumption the original machine satisfied; a genuine platform
defect; or a test encoding one machine's environment. The three need
completely different responses, and the evidence that distinguishes
them is usually a measurement rather than an argument.

When a platform defect looks likely, reproduce it with YOUR code out
of the way before compensating for it. One suspected platform crash
turned out to be a borrowed pointer in the test harness; the
reproduction script written to blame the platform is what proved it
innocent.
