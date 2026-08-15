# Hunt log: fixture setup order no user could follow

Direction: the suite's own fixtures as a source of blind spots — setup
sequences no user could perform, state seeded directly into records rather
than driven through controls, and dialogs constructed after the state they
are supposed to react to. Shape: asymmetry.

Commit read: **c7b787cd91920493ebc01aa532b45d15c3c64f17** ("The macOS job
finds the interpreter where QGIS actually puts it"), probed via
`git archive HEAD` into
`<scratchpad>/fixorder`. The live tree had an uncommitted
modification to `weavingspace_qgis/dialog.py` at hunt start; nothing in this
log was measured against it.

## 20:35:38  iteration 0  [survey]
TRIED:  Count the recurring fixture shapes in tests/run_tests.py at HEAD.
RESULT: 299 `WeavingSpaceDialog(...)` constructions; 293 `addMapLayer` calls;
        the near-universal order is `project.addMapLayer(layer)` THEN
        `WeavingSpaceDialog(iface=...)`. Direct record writes cluster on
        `_generated`, `_ranges[tid]`, `_layers`, `_choices[tid]`,
        `_colours[tid][field]`, `_bounds[...]`, `_pinned*`.
NEXT:   Read how the dialog populates the region chooser and the variable
        table, then drive the user's order (dialog first, layer after) and
        measure.

## 20:42:04  iteration 1  [logical]
TRIED:  Shape 1 — `project.addMapLayer(layer)` BEFORE `WeavingSpaceDialog(...)`
        (dialog.py:1056 calls `_on_layer_changed()` by hand at the end of
        `__init__`). Drive the user's order instead: construct the dialog with
        an empty project, then add the polygon layer.
RESULT: **confirmed, and it is the reported field defect.** One case per
        PROCESS (two dialogs in one process cross-talk through the project
        singleton and spoiled the first two readings — recorded as a fixture
        fault of my own).
          A, fixture order: spacing 500.0, vars ['v1','v2','v3','v1'],
             dropdown offers ['---','v1','v2','v3','landcover'],
             modes all "Quant: Quantiles".
          B, user order:    spacing 1000.0 (the default, never derived),
             vars ['---','---','---','---'], dropdown offers ONLY ['---'],
             modes all "Single colour" — while the Region layer box shows
             the layer.
        Mechanism, traced at class level in an isolated process:
        `QgsMapLayerComboBox` emits `layerChanged` with arg None while
        `currentIndex()` is still -1 and `count()` is already 1. dialog.py:1598
        `_on_layer_changed` runs there, reads `currentLayer() -> None`,
        rebuilds the table off `_layer_fields() -> []`, and skips
        `_auto_spacing` (guarded `layer is not None`, dialog.py:1632). The
        combo then settles to index 0 WITHOUT a second emission, so nothing
        rebuilds. Exactly "the layer chooser had not settled when the table
        was built".
NEXT:   Does it recover when a design control is touched? And read the harm
        off the MAP (renderer + element layer fields), not the table.

## 20:45:20  iteration 2  [logical]
TRIED:  Second, INDEPENDENT route for shape 1 — read the MAP rather than the
        table. Generate in each order and inspect the output layers'
        renderers. Plus: does the dialog recover if the user touches a design
        control?
RESULT: **confirmed on the map.**
          A, fixture order: 4 output layers, QgsGraduatedSymbolRenderer on
             'v1'(4 classes), 'v2'(4), 'v3'(5), 'v1'(4).
          B, user order:    **0 output layers.** Generate produces nothing.
        Recovery: touching a design control (spacing) DOES repopulate the
        dropdown (['---','v1','v2','v3','landcover']) but every element stays
        on '---' and Generate still yields 0 layers. dialog.py:3234-3238 —
        `_refresh_table` treats a previous var of None as "deliberately
        unassigned" and refuses to cycle a default back in.
NEXT:   How many doors reach that state? Try the ordinary mid-session moves.

## 20:46:00  iteration 3  [logical]
TRIED:  Variants of when the layer arrives, each in its own process on a clean
        project. C: a first polygon layer present, a second added and picked.
        D: the region layer REMOVED and a replacement loaded. E: two layers at
        construction, user switches the combo.
RESULT:  C — **equivalent to the fixture order.** offered list intact, vars
             ['v1','v2','v3','v1'] kept, spacing re-derived 500 -> 2000. No
             defect; nobody need re-check this one.
         E — **equivalent.** Same as C. No defect.
         D — **confirmed, and likelier than B in real use.** After removal the
             table rebuilds with no fields (offered=['---'], vars all '---');
             the replacement then restores the OFFERED list but every element
             stays unassigned forever. A user who reloads an edited region
             layer loses all four variable assignments silently.
        So B and D are one defect with two doors: `_refresh_table` cannot tell
        "the user chose ---" from "there was no layer when this row was
        built", and any rebuild with `_layer_fields() == []` writes the
        user's choice away permanently.
        Settled decision checked: CLAUDE.md says an element left on "---"
        stays unassigned and draws as flat fill — that is about a CHOICE. It
        also says losing a COLUMN re-defaults to a surviving field. Losing the
        LAYER doing the opposite is the asymmetry.
        WHEN IT STARTED: `git log -S` on both the sticky-unassigned branch and
        the `_auto_spacing` guard returns 3bd5f52 (2026-08-07), the initial
        commit. Present since 0.23.0.
NEXT:   Shape 2 — records written directly where a user moves a control
        (`_pinned_bounds.setdefault(...)`, 17 sites; `_class_counts[tid] = N`).

## 20:49:10  iteration 4  [logical]
TRIED:  Shape 2 — a pin SEEDED into `_pinned_bounds` (17 sites in the suite,
        e.g. run_tests.py:7984, 8023) against the same pin driven through the
        control a user has: the Customize button, `box.setValue(v)`,
        `pin.setChecked(True)`.
RESULT: **EQUIVALENT for a reachable bound, and that is a finding — nobody
        need re-check it.** Pin low=10.0 on v3, n=12, k=5:
          record  -> _pinned_bounds {'low': 10.0}; ranges
                     [(0,10),(10,22),(22,38),(38,62.25),(62.25,121)];
                     stamped {"pinned": {"low": 10.0}}
          control -> byte-identical on all three, refused=False.
        Both leave the swatch cache in the same state.
        ONE asymmetry, and it is a blind spot in the SUITE rather than a
        defect in the plugin. With an IMPOSSIBLE bound (low=500 on a column
        whose max is 121):
          control -> REFUSED. _pinned_bounds empty, nothing stamped.
          record  -> written anyway; the ladder is the unpinned one, so the
                     pin does nothing, AND the layer is stamped
                     "pinned": {"low": 500.0} — a bound the map has not got.
        The record route bypasses `pin_problem` (dialog.py:4753). No second,
        unguarded door found for it, so no harm is claimed; what it means is
        that a fixture seeding this record can assert behaviour on a state no
        user reaches.
NEXT:   Shape 3, and then the notice a user actually gets in B and D.

## 20:50:05  iteration 5  [logical]
TRIED:  Shape 3 — the suite calls `dlg._generate()` (a private method) rather
        than pressing Generate, ~299 times.
RESULT: **ruled out by reading the one line the button adds.**
        dialog.py:1434 is `clicked.connect(lambda: self._generate())`, and
        `_generate` carries its own `if self._task is not None` guard at
        6057. The button's only extra state is being disabled during a run
        (6233/6744), which the guard already enforces. Equivalent.
        (Read, not measured — stated so it is not mistaken for a measurement.)

## 20:50:41  iteration 6  [logical]
TRIED:  What is the user actually TOLD in B and D, and what does the map show?
RESULT: Both raise the modal "Assign at least one variable in the Data &
        colours tab." — in B against a dropdown that offers only '---', so
        the user is told to do something the dialog will not let them do.
        D is worse on the map and is the strongest reading of the day. With
        live update on (the default), the dialog had already drawn the first
        region. After the swap, the table says every element is '---' while
        FOUR output layers sit on the canvas named "a – v1", "b – v2",
        "c – v3", "d – v1", each a QgsGraduatedSymbolRenderer. Second route,
        the EXTENT: all four span (-298,-298)-(4298,4298) — the OLD 4x4@1000
        region, not the 8x8@2000 replacement (0..16000). So the canvas shows
        a tiled map of the previous region, the table contradicts it, and
        Generate refuses.
NEXT:   Nothing further; writing the report.

## 20:52:22  iteration 7  [verification — HEAD MOVED UNDER THE HUNT]
TRIED:  Before reporting, re-check the tree's HEAD. It had advanced from
        c7b787c to **65583e1d36cb4eb0cbbbc655c64eb52723b98c07** ("Finding
        QGIS's Python is not the same as being able to start it") while this
        hunt ran, and `git diff c7b787c..HEAD -- weavingspace_qgis/dialog.py`
        is 55 lines. Re-archived at 65583e1 into `<scratchpad>/fixorder2` and
        re-ran every case.
RESULT: **Shape 1 is ALREADY FIXED at the current HEAD, both doors.** The
        maintainer's commit adds `_settle_layer_choice` (a `singleShot(0)` at
        the end of `_on_layer_changed` that rebuilds when the chooser landed
        after the signal) AND a `_fieldless_build` flag so a table built with
        no fields is not mistaken for the user's "---". Its own comment names
        the same field report of 2026-08-15 and the same cause.
        Measured at 65583e1:
          B — spacing 500.0, vars ['v1','v2','v3','v1'], 4 output layers,
              no modal. Identical to the fixture order A.
          D — assignments restored on the replacement, and the map re-tiles
              over the NEW region: extent (-1192,-1192)-(17192,17192), the
              8x8@2000 replacement, not the old 0..4300.
          C, E — unchanged, still equivalent.
        So this hunt independently reproduced the shipped defect and the door
        the fix's own commit message does not mention (D, swapping the region
        layer), and confirms the fix closes both. NOTHING IS CLAIMED AS A LIVE
        DEFECT.
NEXT:   None. Report written. Tree left clean apart from this log.
