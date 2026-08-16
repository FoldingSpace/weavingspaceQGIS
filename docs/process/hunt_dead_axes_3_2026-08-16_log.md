# Hunt log: dead-axes-3, 2026-08-16

Direction: **tests that cannot fail** (third outing). Target: the
tests written or rewritten on 2026-08-16, eleven of them named in the
brief. Frozen copy `ed7231f` via `tools/hunt_probe.py --prepare --name
dead-axes-3`; HEAD was still `ed7231f` when this was written, so
nothing here is a claim about an older tree.

Method: every named test run green first, then the PRODUCT behaviour
each assertion names broken one at a time in the frozen copy and the
test re-run. 41 distinct mutations. Where a test killed a mutant, the
traceback's line number was read so the kill could be attributed to an
ASSERTION rather than to the test — a kill at a later assertion says
nothing about the earlier one, which is how the first finding below
was reached.

Honest note on this log's shape: entries were written at the end of
each measured batch rather than before each hypothesis, so the times
below are batch times and not a per-hypothesis record. The record asks
for the latter and is right to.

---

## 18:5x  batch 0  [baseline]
TRIED:  all eleven named tests against the frozen copy, unmutated.
RESULT: 11 passed. 4 helper-level tests in 7s, 7 dialog-level in 22s
        — cheap enough to mutate per assertion rather than per test.
NEXT:   enumerate each test's assertions and find one product
        mutation per assertion.

## 19:0x  batch 1  [perturbation]  bridge-level behaviours
TRIED:  11 mutants — the nudge disabled, the nudge moving the last
        range (the defect of that morning), the nudge unscoped,
        the constant-column collapse removed, `unworn_classes`
        silenced, the ladder formula moved, `cannot_be_placed` blind
        to infinities, both dialog readers reverted to a NULL scan,
        the three absence kinds collapsed to one, the kind column
        dropped.
RESULT: every mutant killed by its owning test. Cross-runs against
        non-owning tests survived as expected (the nudge tests do not
        answer for each other's scope).
NEXT:   re-run the kills one test at a time to attribute each to a
        LINE, because a test that kills at assertion 6 says nothing
        about assertion 3.

## 19:1x  batch 2  [logical]  attribution
TRIED:  the same mutants, one test per run, reading the traceback.
RESULT: the attribution changed the picture once.
        `notice-counts-nulls-only` — the missing-values notice
        reverted to counting NULLs alone, which is the exact defect
        `test_every_reader_of_unplaceable_agrees_with_the_split` was
        written for — died at **line 20922**, the SECOND act
        (infinities alone). Lines 20890 and 20891, the first act's
        "was anything said" and "does it say FOUR", both passed.
        Line 20891 is the count axis. **CONFIRMED DEAD.**
NEXT:   measure the sentence rather than infer it.

## 19:2x  probe  [logical]  what the notice actually says
TRIED:  reproduced the test's first act and printed the sentence,
        clean and then with the NULL-only mutation.
RESULT: clean — "4 of 144 areas do not have finite numeric data".
        Mutated — "**1 of 144** areas ...", and
        `str(spoiled) in said[0]` is still **True**, because `"4"` is
        a substring of `"144"`. The fixture is
        `make_region_layer(n=12)` = 144 areas with 4 spoiled, so the
        total contains the digit the assertion is looking for. It
        would pass equally on "14 of 144" and "44 of 144".
        CONFIRMED by measurement, not by reasoning about the string.
NEXT:   the dialog-level tests.

## 19:3x  batch 3  [perturbation]  dialog-level behaviours
TRIED:  17 mutants — adoption off, the cleared project keeping its
        group, the pin not released / released silently / retired
        after stamping, the reopen merge back to a per-FIELD gap
        question, the stamp dropping the no-data key, the paired
        layer's hand renderer dropped and ungated, the icon notice
        deleted, the icon count reading `_element_layer_ids` alone,
        four separate mutations of the icon sentence, and the two
        directions of the absence-fill exclusion.
RESULT: 16 killed, each attributed to the assertion that names it.
        One anchor was not unique and wrote nothing (re-done in
        batch 4). No survivors.
NEXT:   the assertions no mutant had yet aimed at.

## 19:4x  batch 4  [perturbation]  the untouched assertions
TRIED:  7 mutants — the pin pop removed, the run always making a NEW
        group, `cannot_be_placed` refusing text, the split never
        splitting, a text column not split, the kind column lost on
        the way to the QGIS layer, the stamp dropping the class
        colours.
RESULT: 5 killed. TWO SURVIVED:
        - `group-always-new` survived
          `test_a_project_opened_under_an_open_dialog_is_taken_over`.
          That mutation makes the dialog build a second group instead
          of rebuilding the adopted one, which is word for word the
          harm the test's own message names.
        - `stamp-drops-class-colours` survived
          `test_a_no_data_colour_comes_home_beside_a_class_colour`.
          Ruled NOT a dead axis: line 21334 is a PREMISE, and the
          class colour comes home by a second route
          (`_adopt_row_symbology` recovers it from the renderer), which
          is what the docstring already says. It still fails if
          adoption breaks altogether.
NEXT:   find out why the group mutation is invisible.

## 19:4x  probe  [logical]  does the second Generate run at all?
TRIED:  instrumented `_get_or_make_group` with a print and ran the
        REAL test.
RESULT: **one call in the whole test.** The second Generate — the one
        after the reopen, the one the last three assertions are about
        — never reaches it. A second probe reproducing the test's
        steps shows why: `make_region_layer` is a MEMORY layer, and a
        memory layer written into a `.qgz` and read back is valid,
        keeps its four fields and holds **0 features**. So the
        reopened region has nothing to tile, the run is refused, the
        message bar stays empty, and `_element_layer_ids` is
        byte-identical before and after.
        The layers the last two assertions count are the ones RESTORED
        FROM THE FILE. **CONFIRMED DEAD** (two assertions, lines 20346
        and 20350).
NEXT:   close the few remaining assertions.

## 19:4x  batch 5  [perturbation]  the last gaps
TRIED:  3 mutants — the paired layer carrying one kind though the
        column is present, the paired layer never registered, and
        `pin_problem` never firing.
RESULT: all three killed, at lines 21212, 21379/21203 and 21266.
NEXT:   report.

---

## Findings

**1. `test_every_reader_of_unplaceable_agrees_with_the_split`, line
20891.** `assert str(spoiled) in said[0]` is a SUBSTRING test for
`"4"` against a sentence whose total is `144`. Restoring the exact
defect — the notice counting NULLs alone — makes it say "1 of 144" and
the assertion still holds. The test kills the mutant, but at line
20922 (the infinities-alone act), so the count axis named in its own
Regression line is dead. Cure: compare the number, not a substring —
e.g. assert the sentence starts `f"{spoiled} of "`, or parse the
leading integer.

**2. `test_a_project_opened_under_an_open_dialog_is_taken_over`, lines
20346 and 20350.** The final act cannot observe a run. The region
layer is a memory layer, and a memory layer round-tripped through a
`.qgz` comes back with 0 features, so the second Generate is refused
and produces nothing. `_get_or_make_group` is called ONCE in the whole
test. The two assertions therefore describe the layers the file
restored, and a dialog that always builds a NEW group rather than
rebuilding the adopted one — the harm the assertion's own message
names — leaves the test green. Cure: give the reopened project a
layer whose data survives the save (a GeoPackage, as
`test_a_project_and_its_geopackage_move_together` does), and assert
the output layers are NEW (different ids, or a feature count matching
the new spacing) rather than merely present.

**2b. The same journey, the same inertness, in the sibling.**
`test_a_project_opened_under_an_open_dialog_is_not_drawn_over` (also
written today, outside the brief's eleven) drives the identical
save/clear/reopen/Generate sequence with the same memory-layer
fixture. Measured the same way: `_get_or_make_group` is called ONCE in
that test too, so its closing `assert not doubled` (line 20434) is
also observing restored layers rather than a run. Its earlier
assertions (20402, 20406) are live — `forget-keeps-the-group` kills at
20402. Reported for completeness; it is the same cure.

Both dead axes sit in tests whose primary axis is live — the adoption
assertion at 20329 and the infinities act at 20922 both kill. That is
now the third round in a row where every dead axis had a live sibling
above it.

## Not independently challenged (stated, not claimed dead)

- `test_a_repeated_value...` lines 20828/20831 (a value arriving later
  lands in the gap). No product mutation isolates them: everything
  that moves those bounds trips an earlier assertion first. Related
  observation: the design rule that an empty class must never be given
  a hatched SYMBOL is not covered here, because a hatch changes the
  symbol's fill style and not `symbol.color()`, which is all
  `_drawn_colours` reads.
- `test_no_placeholder_fill_is_ever_a_clash` line 29774
  (`found[0][3] < 1.0`). Raising the threshold enough to reorder the
  reported pairs trips the fixture premise at 29711 first.
- The count guards (`checked == 60`, `checked == 4`, `seen == 3`) and
  the fixture premises are not product axes by construction. They are
  doing their job and are not counted as dead.

## Denominator

11 tests, 77 assertions, **41 distinct product mutations**. 39 killed
by their owning test at the intended assertion. 1 survivor was a dead
axis (finding 2, two assertions); 1 survivor was a premise with a
second legitimate route and is not a fault. Finding 1 was NOT a
survivor — the test killed that mutant at a later line, and only the
line attribution and a direct measurement of the sentence exposed it.

**Three dead assertions in 77, in 2 of 11 tests.** Against the
project's standing one-in-five per TEST, this batch is better than
average — which is what one would expect of a batch two hunts have
already been through, and the two that were left are both in the
newest work of the day.

## Lesson for the record

**A kill is evidence about ONE assertion, and it is the assertion the
traceback names.** Both previous outings of this direction ran per
assertion and still measured survival per TEST. Finding 1 was
invisible to that: the mutant died, the test looked sound, and the
dead axis was three lines above the one that killed. Read the line
number, and when the killed line is not the one the mutation was aimed
at, the aimed-at line is unmeasured.

**`in` is not `==`, and a fixture with 144 areas contains every digit
of 4.** Two of the shapes this project already knows — a substring
containment and a fixture whose numbers overlap — met, and neither is
visible while reading the test.

**A round trip through a `.qgz` is not a round trip for a memory
layer.** Any test whose journey is save → clear → read and then
EXPECTS a run to produce something needs a file-backed fixture. Worth
grepping the suite for the other tests on that journey.
