---
name: tests-that-can-fail
description: Write tests that would actually fail if the behaviour they name were broken, and catch the ones that cannot. Use this whenever you write or review a test, whenever a new test passes on the first run, whenever a test asserts something a guard clause might have skipped, whenever you are testing a UI through code rather than through the events a real interaction sends, and whenever a suite is green but nobody trusts it. Also use it when a test fails and your first instinct is that the test is wrong — sometimes it is, and telling the two cases apart is the whole skill.
---

# Tests that can fail

A test that passes proves nothing on its own. It might be exercising
the behaviour it names, or it might be skipping it, asserting
something that is true either way, or demanding something the
software is right to refuse. All four look identical in a green run.

These are the failure modes, in the order they actually occur, each
with the check that catches it.

## The guard that skips the whole test

The commonest vacuous test is defensive code doing its job:

```python
combo = table.cellWidget(row, 3)
if combo is not None and hasattr(combo, "setCurrentText"):
    combo.setCurrentText("Blues")     # never runs
...
assert after == before                # trivially true
```

If the widget is not what you assumed, every guard skips, nothing is
set, and the comparison holds because nothing happened. This passes
forever and tests nothing.

**Count what you did, and assert the count.**

```python
touched = 0
for row in rows:
    ...
    touched += 1
assert touched, "nothing was set, so the comparison below proves nothing"
```

Any loop with a `continue`, any conditional assignment, any
`if x is not None` in a test body needs this. It is two lines and it
is the highest-yield habit in this document.

## Asserting the nearest observable rather than what must be true

You want to check the plugin noticed a change, so you assert that a
number moved. Then it does not move — and the software is right,
because reprojecting the same ground re-derives the same spacing.

**State the property, not its most convenient symptom.** If what
matters is "the plugin noticed", assert the record it keeps, not a
downstream number that may legitimately be unchanged.

## An invariant that demands the software get it wrong

Sweeping invariants are comfortable to write and quietly encode
misunderstandings. "Every edit changes the map" sounds unarguable
until:

- dropping the last mapped column leaves nothing assigned, so the run
  is correctly refused and the previous map correctly stays;
- reprojecting to a CRS that gets reprojected back yields the same
  map, correctly.

**When a step surprises you, work out which of you is wrong before
changing either.** Then state the expectation per step, and say in
the message which steps must NOT change and why.

## Driving the code through a path no user takes

Setting a widget's value programmatically is not what a click does. A
click emits a signal that sets state — a "the user chose this
deliberately" flag, a modification marker — and code branches on that
state. Set the value directly and you exercise a path nobody is on.

```python
mode.setCurrentText("Quant: Quantiles")     # no signal
index = mode.findText("Quant: Quantiles")   # what a click does
mode.setCurrentIndex(index)
mode.activated.emit(index)
```

**Ask what the real interaction emits, and emit it.** Where you
deliberately want the other path — the state a restored session or a
future code path could produce — say so in a comment, because the two
look identical.

The same applies to visibility: a widget in a dialog that was never
shown reports `isVisible() == False` for everything, so assertions
built on it are vacuous in one direction and wrong in the other. Use
`isVisibleTo(parent)`.

## A fixture that cannot exhibit the behaviour

A test simplified its geometry to squares, then asserted that
simplifying them changed the map. Douglas–Peucker keeps every vertex
of a square, so "simplify" returned the identical polygon and the
test asserted that an unchanged region gives an unchanged map. It
passed while a fix was being written and proved nothing.

**When a test mutates a fixture, assert that the mutation CHANGED
it** before asserting what followed.

**The same trap catches the throwaway probe you write to VERIFY a
claim, and there it is likelier**, because a probe is written in a
hurry, run once, and believed. One written to judge a reported defect
— removing the item a tool was pointed at — built every fixture item
with identical field names. So the tool silently carried on with a
different item, the probe saw a perfectly ordinary success, and the
claim was nearly recorded as not reproducing. Rebuilt with the fields
differing, as any real data would, the same probe showed the
operation doing nothing at all.

Before believing a probe that says "no defect here", ask what its
fixture had to be like for the harm to show, and whether it was.

## A comparison too coarse to see the defect

Tile count and bounding box both survive a region being reshaped
inside its own extent, while the map genuinely changes because each
tile drew from a different area.

**Fingerprint the thing a user would notice**, not the thing that is
easy to measure. If a wrong map and a right map produce the same
number, that number is not the test.

## Reading the answer at the wrong moment

Transient state gets cleared by whatever happens next. A notice
raised during an edit was gone by the time the test read it, because
finishing the run queued a refresh that cleared the line.

**Read at the moment the thing is true**, not at the end. And when a
stub swallows what you need to observe, make the stub record instead
of absorbing — a stub exists to keep the code path identical, not to
eat the evidence.

## The proof: break it and watch it fail

Everything above is a heuristic. There is one actual proof, and it is
cheap:

**Undo the fix in a sandbox and require the test to fail.**

Do this for every test that guards a real defect. In a project with a
mutation harness, that means an entry in the catalogue; without one,
it means reverting the fix by hand and running the test once.

Two of the tests written in one session here passed with the
behaviour deliberately broken, and both had been reviewed and
believed. Only mutating the code found them. Expect a rate like that
— it is not carelessness, it is what untested tests are.

## When a test fails, decide whose fault it is

The reflex is to fix the test. Before touching it, ask which of these
it is:

1. the software is wrong — fix the software;
2. the test's expectation was wrong — fix the expectation, and say
   in a comment what you had misunderstood, because the next person
   will assume the same thing;
3. the test's fixture or driving was wrong — fix those, and check
   whether the test was passing vacuously before.

Relaxing an assertion to get a green suite is only ever right in case
2, and then it is not relaxing, it is correcting.

## A note on tests you write for a suite you do not trust

If a suite is green and nobody believes it, do not start by adding
tests. Break things and see what survives: revert a fix, delete a
line, invert a condition. Whatever stays green tells you where the
suite is decorative — and that is a better guide to what to write
next than any amount of thinking about what might be untested.
