# Hunt log — unreachable branches on the pinned/copied classification path

Direction: **unreachable branches**. Area: `bridge.pin_problem`,
`bridge.fitted_breaks`, `bridge.unworn_classes`, `bridge.set_class_bounds`,
and every refusal `_copy_classification` and the pin column in
`category_editor.py` can return. HEAD 3d13b87.

Working copy: `git archive 3d13b87` extracted to
`<scratchpad>/head-copy` — the shared tree has uncommitted work from
another agent in `bridge.py`/`dialog.py`, so measurements are taken
against HEAD, not against the working tree.

## 22:34:10  iteration 1  [logical]
TRIED:  Static enumeration of every refusal on the area's paths.
        bridge.pin_problem R1 "no values to pin against", R2 "must be a
        number", R3 "must sit between A and B", R4 "first class must end
        below", R5 "a k-class scheme has k-1 boundaries", R6 "leave
        nothing between them"; dialog._copy_classification C1 "That
        element has no variable to classify", C2 "This element has no
        classes to copy", C3 "A single class has no breaks to copy".
RESULT: inconclusive on harm, but two structural facts established by
        reading. (a) R2 needs a non-finite bound; the only producer is
        category_editor._bound_box, a QDoubleSpinBox with
        setRange(-1e12, 1e12), so no non-finite value can arrive ->
        R2 unreachable, harmless. (b) After R5 passes, asked-pins >= 1
        always, so make_graduated_renderer's wants_middle=False and the
        whole `if middle:`-less arm of _apply_pinned_bounds is dead for
        every dialog-validated pin. Also harmless.
NEXT:   Harmless dead guards are not defects by the brief's bar. Go
        after the settled decision that has a visible consequence:
        "a copied ladder can leave classes the receiving column cannot
        reach ... the swatch HATCHES the stripes no tile uses so the
        emptiness is visible rather than silent". bridge.unworn_classes
        is unit-tested; dialog._unworn_stripes (dialog.py:3874) has
        three early returns and its docstring promises a fallback to
        the region's values that the code does not contain. If nothing
        upstream produces the state it needs, the emptiness IS silent.

## 22:41:55  iteration 2  [perturbation]
TRIED:  Does the hatching reach the user? Probe
        scratchpad/probe_unworn.py: n=12 region, element a on v3
        (0..121), element b on v1 (0..11), Generate, then
        _copy_classification("a", "b"), then read _unworn_stripes.
RESULT: ruled out. Measured: copy accepted (refusal None), record
        {'breaks': [4.0, 14.2, 30.0, 55.0]}, target map bounds
        [(0,4),(4,14.2),(14.2,30),(30,55),(55,55)], element values
        0..11, bridge.unworn_classes DIRECT = [2, 3, 4],
        dialog._unworn_stripes = [2, 3, 4]. The hatching is reachable
        and correct. The docstring's "fallback to the region's values"
        is still absent from the code, but that costs a swatch before
        the first Generate, not a map.
NEXT:   Turn to the colouring guard that the copied path shares with
        the constant-column rule. bridge.make_graduated_renderer paints
        copied classes via set_class_bounds, which leaves every class
        at the placeholder "#c0c0c0", and relies on the recolour below
        (`elif ((lo, hi) != (0, 100) or pins)`) to give them ramp
        colours. But `if distinct == 1 and count:` takes precedence and
        colours ONLY class 0. A copied ladder onto a CONSTANT column
        has distinct == 1 and count == len(copied) > 1, so classes
        1..n-1 would keep the placeholder grey. Note the asymmetry that
        makes this the shape asked for: pin_problem REFUSES a pin on a
        constant column (R6 -- nothing between the bounds), so the pin
        door is guarded; the copy door reaches the same state unguarded.
        Probe it.

## 23:05:20  iteration 3  [perturbation]
TRIED:  bridge level, no dialog. scratchpad/probe_grey.py calls
        make_graduated_renderer on a column that is 7.0 everywhere,
        four ways.
RESULT: CONFIRMED. Measured, HEAD 3d13b87, QGIS 4.0.3:
        - constant column, no copy: one class "7 - 7" at #fa694c (the
          ramp middle). Correct, and the settled behaviour.
        - constant column + copied ladder [4, 14.2, 30, 55], no
          hand-picked colours: classes
          (4,4)#fa694c / (4,14.2)#c0c0c0 / (14.2,30)#c0c0c0 /
          (30,55)#c0c0c0 / (55,55)#c0c0c0.
          The value 7 lands in class 1 by QGIS's own containment rule,
          so every tile paints #c0c0c0 -- the placeholder
          set_class_bounds (bridge.py:1123) puts on a class before the
          caller colours it.
        - same, WITH the positional colours a copy carries: all five
          classes coloured. That is what hides it.
        - control, a VARIED column with the same copied ladder: all
          five classes get proper Reds colours. So it is `distinct`
          and nothing else.
        Mechanism: bridge.py:1594 sets `pins = 1` precisely to "force
        the full recolour below", but bridge.py:1652
        `if distinct == 1 and count:` wins the if/elif and recolours
        class 0 ONLY. That guard's condition is right for a
        classification the software COMPUTED (which collapses to k=1),
        and the copied ladder at bridge.py:1590 has already written
        five classes into the renderer before it runs.
NEXT:   Prove it reaches a user through the dialog, and read it off the
        MAP rather than off the renderer.

## 23:19:40  iteration 4  [perturbation]
TRIED:  scratchpad/probe_dialog_grey.py -- the whole thing driven as a
        user does. n=12 region plus a constant column vc=7.0; element a
        on v3, element b on vc; Generate; Copy to... a->b; then pick a
        new ramp for b (Greens, through `activated`, since a
        categorical ramp is refused on a graduated row -- Accent was
        my first try and correctly did nothing); Generate.
RESULT: CONFIRMED, twice, each in a fresh process on a project cleared
        first. Element b's OUTPUT LAYER renderer:
          class 0: 4.0 - 4.0     #73c478
          class 1: 4.0 - 14.2    #c0c0c0
          class 2: 14.2 - 30.0   #c0c0c0
          class 3: 30.0 - 55.0   #c0c0c0
          class 4: 55.0 - 55.0   #c0c0c0
        SECOND, INDEPENDENT ROUTE -- a real
        QgsMapRendererParallelJob render of that layer, 300x300,
        sampling every third pixel: 1911 pixels of #c0c0c0 against
        7352 of white background and no Greens colour anywhere. The
        element is flat placeholder grey.
        Meanwhile the table's ramp cell reads "Greens", and the row is
        NOT marked Custom (the picks were destroyed with the ramp
        choice, as settled), so nothing on screen says the map has
        left the ramp.
        Also measured in the LIVE working tree (which carries another
        agent's in-flight pin-on-copy fix): identical.
NEXT:   Establish the asymmetry and the date.

## 23:26:05  iteration 5  [logical]
TRIED:  Is the same state reachable through the PIN door, and when did
        the copy door open? scratchpad/probe_pindoor.py, plus git log -S.
RESULT: The pin door is GUARDED. On a constant column pin_problem
        refuses every pin: at 7 -> "Those bounds leave nothing between
        them to divide into classes."; at 6 or 8 -> "The lower class
        bound must sit between 7 and 7, which is what the data
        covers." So a pin can never put more than one class on a
        distinct==1 column. The copy door has no equivalent check.
        WHEN: the copied-ladder short-circuit arrived in 205fecd
        (2026-08-14, "A copied ladder, fitted to the column that
        receives it"); the `distinct == 1` colouring arm predates it
        in 4ee76fd the same day. So the defect was born with the copy
        feature, in 0.24.3, and is in HEAD now.
NEXT:   Report. On the ASSIGNED shape (unreachable) the honest answer
        is two dead branches with no harm in them -- pin_problem's
        "must be a number" (no QDoubleSpinBox can produce a non-finite
        value) and _apply_pinned_bounds' wants_middle=False arm (R5
        guarantees asked-pins >= 1). Neither costs a user anything.
        What is worth reporting is the MIRROR.
