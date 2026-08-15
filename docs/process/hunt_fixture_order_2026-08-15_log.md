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
