# Thirty-six places a bug might be hiding

Written 2026-08-13, at the maintainer's request: PLAUSIBLE rather than
likely. The point is not to predict where defects are — the two found
this week were both somewhere nobody predicted — but to enumerate
ground nothing currently walks over, so that walking it is a decision
rather than an accident.

Each entry says what to do and **what a disagreement would mean**,
because an idea without a failure condition is a wish. Entries marked
DONE were written on the day this list was made; entries marked
COVERED already have a test and are listed so nobody rediscovers them.

The bias of the list is deliberate and comes from evidence. Of the
defects this project has actually found, nearly all came from
comparing two independent descriptions of one fact, and the richest
comparisons cross a BOUNDARY — a save, an export, a process, a
machine. Three same-session differentials found nothing across
seventy-five designs; the first one to cross a serialisation boundary
found a defect on its first run. So the round-trip and export ideas
are at the top, and the "does this widget work" ideas are at the
bottom.

## Across a serialisation boundary

1. **DONE** — a project round trip changes nothing a user chose.
   Found the opacity defect: the layer kept 60%, the table said 100%,
   and the next restyle would have pushed 100% onto the map.
2. A GeoPackage written, reopened in a FRESH project, compared against
   the layers it came from. Disagreement means what a colleague
   receives is not what you see, which is the whole promise of the
   export.
3. A project round trip where the class-source QML has since MOVED.
   The element should fall back to automatic colours and say so, not
   carry stale colours silently.
4. A project round trip after the region layer is renamed on disk.
   The dialog should report the loss rather than offering an empty
   chooser.
5. A project saved with live update ON, reopened: nothing should
   generate until the user asks, or reopening a project quietly costs
   a tiling.
6. **COVERED** (test_a_qml_exported_here_reimports_here) — a QML
   written here reimports here.
7. A GeoPackage path with spaces and non-ASCII characters. GDAL and
   Qt disagree about encoding often enough that this is worth one
   test.
8. Two projects opened in sequence, each with output: the second must
   not adopt the first's stamped records.

## Data that is legal and awkward

9. A region layer with exactly ONE feature. Every per-feature
   statistic has a degenerate case there.
10. A field that is entirely NULL. Class breaks over nothing must
    refuse rather than produce one empty class.
11. A field whose values are all the same STRING — one category, the
    categorical twin of the constant-column case already guarded. The
    QUANTITATIVE side of that family widened on 2026-08-13: fewer
    distinct values than classes now collapses to the value count, so
    the categorical twin is the remaining half.
12. A field with mixed types after a join (numbers stored as text).
    The quantitative/categorical decision turns on the field's
    declared type, which a join can make a lie.
13. Field names that are SQL keywords, or carry spaces and accents.
    They travel through GeoPackage table names, where they are
    quoted, truncated or rejected.
14. Field names long enough for GeoPackage to truncate. Two fields
    truncating to the same name is the case that bites.
15. A region layer with zero features.
16. Duplicate geometries in the region: two features covering the
    same ground, where "which area does this tile fall in" has no
    single answer.
17. A category count either side of the sixty that triggers the
    cardinality warning.
18. Class counts at both ends of the declared 2..20.

## Interaction and timing

19. Changing the ELEMENT COUNT while the colour editor is open. The
    editor holds a tile id that may no longer exist.
20. Opening the colour editor on an element whose field is deleted in
    QGIS while the window is open.
21. Undoing a region edit WHILE a run is in flight, so the run lands
    against data that has been rolled back underneath it.
22. Two rapid generates with different FAMILIES, so the second run's
    output must not inherit the first's element ids.
23. **COVERED** (test_the_plugin_is_unloaded_during_a_run).
24. Switching between two region layers that have identical field
    names but different values — the dialog must not carry colours
    across, since picks are keyed by element and field alone.
25. A restyle triggered while the GeoPackage is being written.
26. The output group deleted from the layers panel mid-run.

## The map itself

27. Opacity zero. A fully transparent element is legal, and the
    legibility check compares colours that nobody can see.
28. Reverse on a SINGLE COLOUR element, where there is no ramp to
    reverse.
29. Unclassed over a constant column: fifty linear steps across no
    range at all.
30. A spacing exactly at the size guard's refusal boundary, from both
    sides.
31. An element left unassigned in a design where every OTHER element
    carries the same field.
32. **DONE** — tile boundaries on, with an inset large enough that
    tiles vanish. Found a real defect: a partial collapse reached the
    user as the library's own "make_valid=False ... invalid input
    geometries", and a total collapse as "Assign at least one
    variable". Both now name the inset
    (test_an_inset_that_eats_the_design_says_so).

## Integrative sessions, which is where state accumulates

33. Design, generate, style by hand in QGIS, save, reopen,
    regenerate: the hand styling must survive the whole circuit, not
    just each step.
34. A session that changes every control once, in a random order,
    with a generate after each: the map must agree with the table at
    every step, not only at the end.
35. Generate, export, delete the project's layers, reopen the
    GeoPackage, and generate again into the same file.
36. A long session under live update with the region edited
    repeatedly, checking that exactly one run follows each settled
    change — no lost edits and no runaway.

## 0.24.3: a test plan for pinned bounds and copied classifications

Written 2026-08-14 at the maintainer's request, after asking whether
the suite was thick around the two new features. It was not: the first
question they asked -- races -- turned up a real defect within the
hour, which is the argument for planning this rather than adding tests
where they occur to somebody.

The plan is organised by the DIMENSIONS this project's record says
find things, not by the feature's parts. Each row says what is being
asked, what a failure would mean, and where it stands.

### The dimensions, and where each stands

| Dimension | The question | Status |
| --- | --- | --- |
| Arithmetic | do pins and copies produce the ladder they promise, in every scheme? | DONE: pinned bounds, refusals, fitting, all four schemes and Unclassed |
| Races | is a choice made WHILE A RUN IS IN FLIGHT destroyed when it lands? | found a real defect; test written |
| Rebuilds | does a choice survive the table being rebuilt 350 ms later? | test written |
| Round trips | do the values AND the flags come home from a .qgz? | pins done; copies written |
| The other boundary | does a colleague opening the GeoPackage see what you see? | written |
| Awkward data | nulls, one value, two values, NaN, infinities, under a pin | written |
| Live path | is a pin recorded but never drawn, because the tick returns early? | written |
| Metamorphic | copy a to b to a: does the map drift? | written |
| Absence | do the controls stay out of categorical dress? | DONE |
| Appearance | can a reader tell a pinned glyph from an unpinned one? | DONE |

### Still to write, in the order they are worth writing

1. **Two editors in one session.** Pin element a, close, open b, copy
   a onto b, reopen a. The editor is modal to the plugin only and the
   dialog owns every record, so nothing should leak between windows;
   this project has had a retired dialog adopt a live one's edits.
2. **A pin against a variable change.** Pins are keyed by element AND
   field: switching away and back must restore them, and switching to
   a DIFFERENT column must not apply one column's numbers to another's
   data. That is the shape that destroyed categorical picks on a
   column rename.
3. **A pin under the class-source path.** Categorical elements have no
   pins, but an element can move between styles; a QML imported while
   a pin is recorded must not resurrect it on the way back.
4. **The differential sweep.** Add pins and copies to
   `test_random_designs_keep_their_views_in_agreement`, which already
   drives random designs and compares the table against the map. A
   pinned row is a new way for those two to disagree.
5. **The visual pair.** A pinned element rendered against the library
   with the same bins, so the pin is checked in PIXELS and not only in
   renderer numbers. This project's characteristic failure is a wrong
   map that looks right.
6. **Undo-shaped sequences.** Pin, unpin, pin again, change the count,
   copy, release: an integration session, checked at several MOMENTS
   rather than only at the end, because a wrong intermediate state
   usually corrects itself by the last generation and hides.

### Hunting is the SECOND layer, not the method

The deliberate work above comes first and does most of it. Hunting
goes round the outside of it, pointed at what a written test cannot
reach: it asks a structural question with no oracle, and its yield
turns almost entirely on the direction chosen (docs/process/
HUNT-RECORD.md). Reaching for it first would be spending an evening
of judgement on ground a differential covers in an afternoon.

So it is layered, and the order matters:

**First**, the dimensions above -- they are cheap, they are
repeatable, and each failure names its own cause.

**Then** three directions, chosen because the record says they pay and
because they fit code this new:

- **asymmetry and twins**, the most reliable code-reading direction
  here at six confirmed. The new code is FULL of pairs: the pin column
  against the Unclassed clamp, the run landing against the restyle
  path, the values against the flags, the swatch box against the
  hatch. The race defect found today was exactly one of these, and it
  was found by a question rather than by a test;
- **two stores of one fact**, three confirmed. The record now holds
  boundary values AND pin flags, and the layer holds a stamp of both
  beside a renderer that already carries the breaks. Which wins when
  they disagree is a question nobody has asked of this code;
- **one boundary but not another**, four confirmed and strong on
  export and reopen. Pins cross the project file and the GeoPackage;
  copies cross both plus the element-to-element hop, which is a
  boundary this plugin has never had before.

**Not** backwards-from-harm, which found the worst defect in this
project's history but is aimed at what a USER would be furious to
lose. That question is worth asking of the plugin as a whole, on its
own evening, not of one version's two features.

Every claim a hunt makes is reproduced here by a different route
before it is believed, and a claim that does not survive is recorded
against its direction. That verification is the real cost and is why
hunting is a layer rather than a first resort.

### How this is run, because the mechanics decide whether it gets done

**Shard it, watch it, then leave it.** Three shards over the suite,
each in its own process, in a WORKTREE checked out at the commit under
test so the tree stays editable while it runs:

    git worktree add ../ws-suite <commit>
    WEAVINGSPACE_TEST_SHARD=i/3 <qgis python> tests/run_tests.py

**Give every run its own log names.** `run_<HHMMSS>_shard<i>.log`, not
`shard<i>.log`. Two runs of one shard once appended to the same file
here and the counts stopped making sense; see CLAUDE.md.

**Arm the watcher in the same breath as the launch**, reporting CHANGE
rather than state: each new FAIL as it appears, then the totals when
the last process exits. It must name the BRANCH and COMMIT in every
line, because a watcher outlived its branch on this project and
announced a verdict about work nobody was doing.

**Verify each new test can fail.** Every one gets an entry in
`tools/mutation_check.py` and must report `caught`. Roughly one test in
five here cannot fail when first written, and the catalogue caught one
of this feature's own tests passing on an accident of spacing.

**Do not run the suite beside another measurement.** One at a time is
what keeps each a measurement; contention inflates per-test times by
15-50% and has changed verdicts.

### When this is finished

When every row above is DONE or deliberately struck out with a reason,
every new test reports `caught`, and a full sharded run is green at the
commit that will become the candidate. Not before, and the roadmap
entry for the features is already deleted -- so this plan is what
stands in for it.
