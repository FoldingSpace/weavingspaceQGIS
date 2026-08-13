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
    categorical twin of the constant-column case already guarded.
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
32. Tile boundaries on, with an inset large enough that tiles vanish.

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
