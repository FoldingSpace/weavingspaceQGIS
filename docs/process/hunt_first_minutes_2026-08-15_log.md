# Hunt log — the first five minutes, shape: unreachable (and its mirror)

Direction: **the first five minutes**. An empty QGIS, a plugin opened
with nothing loaded, a user who has not read the guide: Generate
pressed first, every tab clicked before anything is configured, a
design chosen with no data, data of the wrong geometry type added,
several layers added, the chosen one removed, live update left at its
default.

Shape hunted: **unreachable** — a guard whose precondition never
arrives — and its MIRROR: a guard that fires for a reason that is not
the reason (a message naming the wrong problem).

HEAD read: **c7b787cd91920493ebc01aa532b45d15c3c64f17**
("The macOS job finds the interpreter where QGIS actually puts it",
2026-08-15 13:28:44 -0700).

Working copy: `git archive HEAD` extracted to
`<scratchpad>/fm_head`. The shared tree has uncommitted work in
`weavingspace_qgis/dialog.py`, so nothing here is measured against the
working tree. Probe scripts live in the scratchpad; no repo source was
modified.

## 14:52:10  iteration 1  [perturbation]
TRIED:  Walk the first five minutes on an empty project against HEAD
        c7b787c: open the dialog cold, press Generate, click all four
        tabs, choose a design with no data, add a POINT layer, then add
        a POLYGON layer with NO attribute fields.
        (scratchpad/fm_p1.py, dialog.py:6043 `_generate`.)
RESULT: measured. Cold open is quiet (0 modals, 0 bar messages), live
        update defaults ON, table already holds 4 rows for the default
        design. Generate with nothing loaded -> "Choose a region layer."
        (right). All four tabs quiet. Design change with no data quiet.
        A point-only project leaves layer_combo.count()==0 (the polygon
        filter) and Generate still says "Choose a region layer."
        THE ONE THAT MISDIRECTS: a polygon layer with zero attribute
        fields is accepted as the region, every row's variable combo
        holds exactly ['---'] and nothing else, and Generate answers
        "Assign at least one variable in the Data & colours tab."
        That is the SAME sentence as the 0.24.2 report, reached by a
        different door: the guard at dialog.py:6106-6112 fires for a
        reason that is not the reason, and the tab it sends the user
        to has nothing in it to assign.
NEXT:   Establish harm and reachability. Is a fieldless polygon layer
        something a first-five-minutes user actually makes (QGIS "New
        Temporary Scratch Layer" with no fields added)? And is there a
        near-miss twin: a layer with features but no fields vs a layer
        with fields but no features. Probe both, plus several layers
        added and the chosen one removed.

