---
name: dependency-bug-workaround
description: Work around a bug in a library, framework or platform you do not control, in a way that is safe to ship and can be removed when they fix it. Use this whenever a dependency behaves wrongly and you are about to compensate for it, whenever you find yourself writing "QGIS/pandas/the API does X so we have to Y", whenever a comment says "workaround" or "hack around", and whenever you meet an existing workaround and cannot tell whether it is still needed. Also use it before deciding to reimplement a dependency's behaviour yourself, which is the tempting and usually wrong response.
---

# Working around somebody else's bug

A workaround is a debt with no due date. It is written in a hurry, it
becomes invisible within a week, and it outlives the bug it was
written for — so a year later nobody dares remove it because nobody
can say what it was for. Meanwhile the dependency quietly fixed the
thing, and your code is now compensating for a problem that no longer
exists.

The procedure below costs about twenty minutes more than the hasty
version and produces a workaround that removes itself from your
attention until the day it should go.

## 1. Prove it is really theirs

Before anything else, reproduce the misbehaviour with your own code
out of the way — call the dependency directly, in a script that does
nothing else. Most suspected upstream bugs are not.

Then check whether it is really the dependency or one particular
configuration of it. Try a second backend, provider, driver or
platform if the dependency has them. A defect that appears with an
in-memory fixture and vanishes with a real file is your fixture's
defect, and fixing the dependency's "bug" would be fixing nothing.

**Record the measurement with a version and a date.** "QGIS counts
NULL as zero" is folklore in six months; "QGIS 4.0.3, measured
2026-08-09, identical on the memory provider and on GeoPackage
through OGR" is evidence somebody can re-check.

Look for self-contradiction while you are there — it sharpens the
report and sometimes finds the real rule. If `minimumValue()` ignores
nulls while the classifier counts them as zero, the dependency
disagrees with itself, and that is worth stating.

## 2. Prefer correcting the INPUT to replacing the behaviour

The tempting fix is to do the job yourself. Resist it when the
dependency's job is large.

Ask: can I hand it different input and let it do its own work? A
filter, a cast, a normalisation, a copy with the awkward rows
removed. That keeps their algorithms — including the parts you have
not thought about — and leaves you maintaining one line instead of
four algorithms.

The alternative is worse than it looks. Reimplementing quantiles,
equal intervals, Jenks and pretty breaks means owning four algorithms
forever AND inventing new ways to disagree with the panel the user
opens next. Every place your arithmetic differs from theirs becomes a
bug report you cannot close.

Reimplement only when the behaviour is small, exactly specified, and
you can state the rule in a sentence.

## 3. Fix at the narrowest point, on something you own

Apply the workaround at the single place the wrong behaviour enters
your system, not at every call site, and prefer to manipulate objects
you created over objects the user gave you.

Filtering a layer you generated is safe. Filtering the user's own
data is a different act and needs saying out loud.

Whatever you mutate, put it back — and test that you put it back.
The failure modes of a workaround are usually worse than the bug: a
filter left applied, a setting not restored, a temporary file kept.
Assert the restoration explicitly, including the case where the
caller had already set the thing you are overriding.

**Fall through when the workaround cannot be applied.** If the
mechanism you rely on is unavailable, do the un-worked-around thing
rather than failing. A slightly wrong result beats no result.

## 4. Comment it with its own removal criteria

At the fix, in the code, write:

- what the dependency does wrong, concretely, with the numbers;
- the version and date you measured it;
- why the fix takes this shape rather than the obvious one;
- **what will be true when this can be deleted**, and the name of the
  test that will tell you.

The last line is what makes it removable by somebody who was not
there.

## 5. Write a canary test that asserts THEIR bug

This is the step that makes the difference, and it is the one people
skip.

Write a test that reproduces the upstream defect **directly, with
your code out of the way**, and asserts that it is still broken.
While it passes, your workaround is still earning its place. When it
fails, the dependency has been fixed and your suite has just told you
so.

The failure message must say all of this, because the reflex on a red
suite is to make it green:

```
GOOD NEWS, PROBABLY: <dependency> no longer <does the wrong thing>.
The workaround in <function> is now redundant and can be deleted
along with this test. Do NOT relax this assertion to make the suite
green — that hides the very change this test exists to report.
```

Name it so its purpose survives being read in a hurry:
`test_qgis_still_counts_nulls_as_zero`, not `test_null_handling`.

## 6. Decide what the user is told

Separate the two questions: is the OUTPUT now correct, and does the
user need to know something?

Often the workaround fixes the output silently and that is right. But
if the underlying situation is something a person would want to know
— data with gaps, a feature unavailable on their platform — say it
plainly, and keep saying it after the workaround is removed. That
message is about their situation, not about the bug.

Ask also what a user can do that would defeat the workaround. If
pressing a button in the dependency's own UI recomputes the thing you
corrected, your fix survives normal use and reverts on that action.
That is usually acceptable — but it must be a known and documented
consequence, not a surprise, and it is another reason the message
matters.

## What to write down, and where

- the measurement, with version and date, at the fix;
- the removal criteria, at the fix;
- the canary test, named for the bug;
- a line in the project's settled-decisions document saying the
  workaround exists, why this shape, and that its failure is good
  news.

## Signs you have got it wrong

- The workaround has no test that would notice its removal.
- The comment explains the code rather than the bug.
- You cannot say what would have to be true to delete it.
- You reimplemented something large and now maintain two versions of
  a specification you do not own.
- The dependency's object is left mutated after your call returns.
