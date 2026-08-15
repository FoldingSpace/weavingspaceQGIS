# Hunt log — class-count REDUCTION and REVERSE-recovered-on-reopen

Commit read: **8ebd2a3** (`git archive HEAD` copy at
`$SCRATCH/at8ebd2a3`; the live working tree was never read or run).
Shape: two-stores. Started 2026-08-15.

Probes live in the scratchpad and import the archive copy only.

## 00:00:00  iteration 0  [reading]
TRIED:  read CLAUDE.md's reduction/constant-column decisions,
        HUNT-RECORD.md, bridge.classes_the_map_will_draw /
        few_values_message / make_graduated_renderer,
        dialog._legend_size_note / _ramp_match / _recover_from_renderer
        / _copy_classes_to.
RESULT: mapped the two stores. For REDUCTION: `k` (the ask) lives in
        the spin box's `user_k` and in `_class_counts`; the drawn count
        lives on the renderer. `classes_the_map_will_draw` is the
        settled single answer and has exactly ONE consumer
        (dialog.py:3535). For REVERSE: `_reverse_choices` vs the
        renderer's sourceColorRamp, reconciled by `_ramp_match`
        (dialog.py:4165) at dialog.py:3620.
NEXT:   two candidate consumers that still read the ASK —
        dialog.py:4821 (`_copy_classes_to`'s "lost" notice compares the
        target's `_class_counts` against `source.get("k")`) and
        dialog.py:3727 (`_recover_from_renderer` writes the DRAWN band
        count into `_class_counts`, the record whose own comment at
        dialog.py:3262 says it is "only ever written by a user moving
        the spinner"). Probe both under QGIS.

## 00:35:00  iteration 1  [perturbation]  REVERSE
TRIED:  does `_ramp_match` (dialog.py:4165) still recognise a reversed
        ramp after the ramp has crossed the project-file SERIALISATION
        boundary? Swept all 63 library ramps x {plain, reversed}
        through QgsSymbolLayerUtils.saveColorRamp/loadColorRamp and
        back into `_ramp_match`.
RESULT: partly confirmed, but NOT reachable by a user.
        - All 51 QgsGradientColorRamp ramps survive both ways: 0
          mismatches.
        - All 12 QgsPresetSchemeColorRamp ramps FAIL when reversed:
          `bridge.get_ramp` blanks the colour labels
          (`setColors([(c, "") ...])`, bridge.py ~line 1523), the
          empty `preset_color_name_N` properties are DROPPED by the
          XML writer, and `_ramp_match` then answers (None, False)
          instead of (name, True). Measured: Accent, Dark2, Paired,
          Pastel1, Pastel2, Set1, Set2, Set3, tab10, tab20, tab20b,
          tab20c.
        - RULED OUT as a defect: the preset set is EXACTLY
          bridge.CATEGORICAL_RAMPS (measured, both directions of the
          set difference are empty), a graduated row refuses a
          categorical ramp, and `_sync_row` disables Reverse on a
          Categorized row (dialog.py:2902). So no dialog route puts a
          reversed preset ramp on a layer.
        - Two benign alias collisions: gist_yarg answers "binary" and
          gray answers "gist_gray" (identical definitions in QgsStyle),
          in both directions. The map is right; only the combo's name
          differs from the one picked.
NEXT:   leave REVERSE; it is sound where it is reachable. Turn to the
        reduction and the copied-ladder interaction.

## 00:52:00  iteration 2  [logical + perturbation]  REDUCTION
TRIED:  `bridge.classes_the_map_will_draw` documents that "a copied
        ladder's breaks decide their own count and never come through
        here" (bridge.py:1152) -- but `dialog._legend_size_note`
        (dialog.py:3535) hands it `assignment["pinned"]` WHOLE, breaks
        included, and the function reads only "low"/"high". So on an
        element carrying a copied ladder the notice counts the column
        against the ask while the map draws the ladder.
RESULT: CONFIRMED, two independent routes at 8ebd2a3.
        Route A (bridge only, no dialog): column {1,5,9}, ask 5,
        pinned={"breaks":[2,4,6,8]}. make_graduated_renderer returns
        FIVE ranges; classes_the_map_will_draw -> (3, False);
        few_values_message -> "'v' has 3 distinct values, so it draws
        as 3 classes, not 5."  Constant column (7 everywhere) + the
        same ladder: FIVE ranges drawn, constant_field_message still
        says "draws as one class".
        Route B (dialog, real copy): four elements, source on a
        16-distinct column at k=5, target on a 3-distinct column.
        `_copy_classification('a','b')` -> spinner 5, _class_counts 5,
        assignment k=5, `_current_graduated_classes` FIVE classes
        (1-3, 3-6, 6-9, 9-12, 12-12) -- and `_legend_size_note` still
        returns "'poor' has 3 distinct values, so it draws as 3
        classes, not 5."
NEXT:   confirm the sentence actually reaches the message bar on the
        restyle path after a real Generate, and read the drawn count
        off the real output LAYER rather than off a preview renderer.

## 01:20:00  iteration 3  [end to end]  REDUCTION
TRIED:  the third and decisive route -- a REAL Generate, then the copy,
        with the class count read off the real output LAYER's renderer
        and the sentence taken from the message bar rather than from a
        helper.
RESULT: CONFIRMED at 8ebd2a3. Region of 16 areas; element 'a' on a
        16-distinct column at k=5, element 'b' on a 3-distinct column
        (values 1, 5, 9) at k=5. Generate settles.
          before the copy: layer 'b' renderer has 3 ranges, message bar
            "'poor' has 3 distinct values, so it draws as 3 classes,
            not 5."  -- true.
          after "Copy to..." from 'a': layer 'b' renderer has FIVE
            ranges (1-3, 3-6, 6-9, 9-12, 12-12), spinner 5,
            _class_counts 5, assignment k 5 -- and the message bar
            repeats "'poor' has 3 distinct values, so it draws as 3
            classes, not 5."
        Four stores say five; the one sentence the user reads says
        three. The restyle path (dialog.py:5818) is the site that
        fires it, and a copy always goes through _apply_style_change.
        Not a settled decision: CLAUDE.md's pinned-bounds entry says a
        copied ladder's unreachable classes are KEPT and hatched, so
        five IS the intended map and the sentence is the wrong one.
        n == 1 instance of the same fault: on a constant column
        carrying a ladder the map draws five classes (CLAUDE.md
        records the same measurement) while the notice says one.
        Fixture ruled out: route A used no dialog at all and a fresh
        QgsProject per process; route C ran a clean project with only
        the region layer in it.
WHEN:   the copy feature, d342fd2. 2adb7dd then rewrote both notice
        sites onto `classes_the_map_will_draw` to make the count
        PIN-aware, and did not make it LADDER-aware -- the docstring
        asserts a copied ladder "never comes through here", but
        `_legend_size_note` passes `assignment["pinned"]` whole and
        the function reads only "low"/"high".
NEXT:   report. Tree left clean apart from this log.
