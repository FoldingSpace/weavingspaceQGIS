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

## 15:14:40  iteration 2  [perturbation]
TRIED:  (G) OBEY the instruction on the fieldless polygon layer: set
        every variable combo to every item it offers, press Generate
        again. (H) the twin, a polygon layer WITH fields and ZERO
        features. (I) two polygon layers loaded, remove the one that is
        chosen. scratchpad/fm_p2.py.
RESULT: (G) CONFIRMED unfollowable. Every one of the four rows offers
        exactly ['---'] and nothing else; after cycling every combo
        through every item, `_assignments()` still has var=None on all
        four and Generate #2 repeats the identical sentence. The
        instruction names a tab that contains no way to obey it.
        (H) ruled out, and it is the ASYMMETRY that matters: a
        featureless layer is refused with "The selected layer has no
        (non-empty) polygon features." -- a sentence about the data.
        So the shape-of-data guard exists for one emptiness and not
        for the other.
        (I) NEW CANDIDATE, same shape. With two polygon layers loaded
        and 'alpha' chosen, removing 'alpha' produced NOTHING: no
        modal, no bar message. QgsMapLayerComboBox silently moved to
        'beta', and all four elements moved from v1 to v2 (measured in
        `_assignments()`). The removal notice at dialog.py:1616-1631
        is guarded by `if layer is None and self._had_a_layer`, so its
        precondition only arrives when the removed layer was the LAST
        polygon layer in the project. The `_adapt_to_the_layer` twin
        cannot speak either: `_on_layer_changed` rewrites
        `self._watched_fields` to the NEW layer's names before calling
        it (dialog.py:1610-1613), so `names == self._watched_fields`
        returns early and `lost` is never computed.
NEXT:   The harm turns on live update, which is ON by default. If the
        silent switch also triggers a live run, the user's existing
        map is replaced in place by a map of a different layer and a
        different column with nothing said. Probe that end to end and
        read the variable off the OUTPUT LAYER's renderer, not off
        the dialog.

## 15:41:05  iteration 3  [perturbation]
TRIED:  Take the removal case apart. Live update at its default, one
        case per fresh process, tracing `layer_combo.layerChanged` and
        reading the styled field off each OUTPUT LAYER's renderer
        rather than off the dialog. N = 2, 3, 4 layers; the chosen
        layer first, middle and last; a control removing a layer that
        is NOT the chosen one; and the single-layer case.
        scratchpad/fm_p5.py, fm_p6.py.
RESULT: CONFIRMED, deterministic, and it splits in two by how many
        polygon layers are left.
        N=1 (the guarded door): "The region layer was removed from the
        project, so there is nothing to map. Choose another layer."
        Correct, and it is the only arrangement that reaches it.
        N=2: layerChanged DOES fire. The dialog re-points at the
        survivor, re-defaults every element's variable, and live
        update re-tiles. Measured: the map went from
        ('a - income','income') x4 to ('a - rainfall','rainfall') x4,
        output layer ids all replaced, and the ONLY thing said was
        "'WeavingSpace tiles': 122 tiles across 4 element layers" --
        the same success line as the map it destroyed.
        N>=3: layerChanged fires NOT AT ALL (0 emissions over 11.5 s,
        4 arrangements, repeated). `layer_combo.currentLayer()` now
        returns a DIFFERENT layer, `dlg._watched_layer` is a deleted
        C++ object (RuntimeError on .name()), and the variable combos
        still read the OLD layer's column. The map on screen is now of
        a layer that no longer exists. Pressing Generate then dies at
        bridge.layer_to_gdf's `feat[f]` (bridge.py:281) with
        KeyError('income'), which dialog.py:6142 shows as
        `QMessageBox.critical(self, "WeavingSpace", str(e))` -- a
        modal whose entire text is `'income'`.
        Control: removing a layer that is not the chosen one changes
        nothing and says nothing. Correct.
        ROOT: the plugin has NO connection to
        QgsProject.layersRemoved (grep: zero hits in the package).
        Its only channel is layerChanged, and the notice behind it is
        guarded `if layer is None and self._had_a_layer`
        (dialog.py:1616), whose precondition arrives only when the
        removed layer was the LAST polygon layer. The existing suite
        case (tests/run_tests.py:4352 "the layer removed from the
        project") clears the project of every other layer first, so it
        can only ever walk through the guarded door.
NEXT:   Second independent route and a clean-project re-run, then
        write up. Reproduce the bare `'income'` modal by calling
        bridge.layer_to_gdf directly, with no dialog involved.

## 16:03:20  iteration 4  [logical: second route, and a moving HEAD]
TRIED:  Reach the same facts by mechanisms the first probes did not
        use, and re-run everything against the tree as it stands now,
        because HEAD moved under this hunt: c7b787c -> 65583e1, and
        65583e1 (0f6f5c0 before it) is the FIX for the very 0.24.2
        report that motivated this direction. scratchpad/fm_p7.py.
RESULT: CONFIRMED by a second route, and NOT stale.
        (a) The bare modal, with no dialog anywhere: calling
        `bridge.layer_to_gdf(layer_without_income, ["income"])`
        directly raises KeyError whose `str(e)` is exactly `'income'`
        -- and dialog.py:6142 passes `str(e)` straight to
        QMessageBox.critical. So the sentence the user reads after the
        silent switch is a quoted column name and nothing else.
        (b) Five sources of truth after removing one of three layers,
        read from QGIS rather than from the dialog's own records:
        layers alive = [layer_elevation, layer_rainfall]; the region
        combo (QGIS's own widget) says layer_rainfall, whose only
        field is 'rainfall'; `sip.isdeleted(dlg._watched_layer)` is
        True, so the plugin is still holding the deleted layer; all
        four table rows still claim 'income'; and all four output
        layers are still styled on 'income'. The control names a
        layer that has no such column: True.
        (c) Re-ran fm_p6 and fm_p2 against a fresh `git archive
        65583e1`: identical results. N=3 -> 0 layerChanged emissions,
        nothing said, modal `'income'`; N=2 -> map silently replaced,
        success bar only; fieldless layer -> ['---'] on every row and
        the same unfollowable sentence twice.
        Ruled out as fixture: clean project each run, one case per
        fresh process, a control (removing a layer that is not the
        chosen one) that changes nothing, and the guarded door (one
        layer) that speaks correctly.
NEXT:   Write up. Two claims, one strong (silent region switch, no
        layersRemoved connection, guard reachable only in the
        single-layer arrangement) and one weaker in harm (fieldless
        polygon layer answered with an instruction that cannot be
        obeyed). Dating: the notice arrived in ab94d4d (2026-08-09);
        `git log -S layersRemoved` returns NO commits ever, so the
        multi-layer silence has been there from the first commit.
