# Stochastic session hunt, 2026-08-16 — log

Direction: STOCHASTIC SESSIONS. No hypothesis. Seeded random sequences of
user actions against the dialog, with a fixed set of invariants checked
after EVERY action. Brief generated with `--shape two-stores` because
`--shape stochastic` is not a choice the tool knows; two-stores is the
closest of the five, since most of these invariants ask which of two
records wins when they disagree.

Probes run through `tools/hunt_probe.py` against the frozen copy.
Driver: `scratchpad/hunt_driver.py` (seeded, replayable, shrinkable).

## 01:13:47  iteration 1
TRIED:  Built the driver and ran the negative controls first
        (`--selftest`), before any hunting: eleven invariants, each
        with a deliberate sabotage from outside the dialog.
RESULT: inconclusive — the control run SEGFAULTED (exit 245) at the
        third control. faulthandler named it: `dialog.py:505
        _live_dialog` <- `_retire_previous_instance` (dialog.py:6532)
        <- `WeavingSpaceDialog.__init__` (1041). Cause is the driver's
        own: my teardown called `deleteLater()` on the closed dialog,
        and the live-dialog record is an app PROPERTY holding a
        QObject pointer (`app.setProperty(_LIVE_KEY, dialog)`), so the
        next dialog's `__init__` read a dangling pointer. The code
        anticipates a destroyed predecessor and guards it with
        `except RuntimeError` around the ATTRIBUTE accesses, but the
        crash happens one line earlier, inside `_live_dialog()`
        itself. Observation kept; not claimed as a defect, because
        nothing a user does destroys that C++ object (the dialog is
        parented to the QGIS main window, and `unload()` only closes
        it).
NEXT:   Remove `deleteLater` from the driver's teardown — a user
        cannot do it — and re-run the controls. Frozen commit moved
        under me between --prepare and the first run: 7bd34a6 ->
        3b34364 (a sibling re-prepared the shared copy). All work from
        here is against 3b34364.

## 01:24:57  iteration 2
TRIED:  Re-ran the negative controls after removing my `deleteLater`.
        Eleven invariants: NOEXC, SETTLED, GROUPS, LAYERS,
        NOSELFREGION, RAMPSTORE, INTENT, RENDERKIND, OPACITY,
        ONELEGEND, ONELEGEND-CAT.
RESULT: confirmed (of the HUNT, not the plugin) — after three
        corrections, 11 of 11 controls fire. The three corrections
        were all mine and all instructive:
        (a) reading `layer_combo.exceptedLayerList()` segfaults once
            any layer has been removed from the project — QGIS keeps
            raw pointers there and does not clear them. The invariant
            now reads what the combo OFFERS (`layer_combo.layer(i)`).
        (b) `r.categories()[0].symbol()` segfaults: the category is a
            temporary and the symbol pointer dies with it.
        (c) ONELEGEND-CAT was SILENT on its first control — a hole in
            the hunt, not a sound invariant. With ~60 ramps on offer
            and four rows, no two elements ever land on the same ramp,
            so the state the invariant describes was never produced.
            The random ramp picker now draws from the first 8 of the
            row's own offerings (RAMP_POOL), so collisions are common.
            This is the same shape as the previous hunt's live-update
            hole, found the same way.
NEXT:   Batch 1, seeds 1-8 at 20 steps, to measure what a session
        costs before committing to a long run.

## 01:31:50  iteration 3
TRIED:  Batch 1, seeds 1-8 at 20 steps, with a coverage counter added
        so a motionless invariant cannot pass for a sound one.
RESULT: ruled out — 0 breaks in 8 sessions, but the COVERAGE reading
        is the finding: 160 checks, 94 of them with a map in step,
        RENDERKIND asked 372 times, ONELEGEND asked over a PAIR only
        3 times, ONELEGEND-CAT 0 times. The two invariants that speak
        to this project's settled "one colour means one thing" rule
        were effectively motionless. Cause: the dialog auto-assigns a
        DIFFERENT variable to each element, and random single-row
        picks over five fields, seven styles and a class count rarely
        realign them.
        Also, a sibling hunt running `hunt_probe.py --prepare` rmtree'd
        my region GeoPackage mid-batch (it lived under the harness's
        home). Moved out; sessions 2-8 of that run were lost to it.
NEXT:   Add `align` (every element on one variable and one style) and
        `align_ramp` to the action pool, and open 60% of sessions with
        them. Not a hypothesis: one variable across elements is what
        these maps are FOR.

## 01:36:03  iteration 4
TRIED:  Batch 1 re-run, seeds 1-8 at 20 steps, with the aligning
        moves in the pool.
RESULT: confirmed (coverage) and one break. ONELEGEND pairs 3 -> 411,
        ONELEGEND-CAT pairs 0 -> 17. Break on seed 7: RENDERKIND,
        "element c: table says Categorized, layer carries
        QgsSingleSymbolRenderer". Shrunk from 9 steps to TWO:
          align['landcover', 'Categorized']; variable[2, '---']
NEXT:   Read the row rather than guess.

## 01:38:57  iteration 5
TRIED:  Probed the shrunk state directly (p_unassigned.py): what do
        the cells of a row say once its variable goes back to "---"?
RESULT: ruled out as a defect — MY INVARIANT WAS WRONG. Row c reads
        var='---', style='Categorized' (enabled), ramp='Set1'
        (enabled), renderer QgsSingleSymbolRenderer. An element on
        "---" drawing as plain fill is a settled decision, and the
        style/ramp cells keeping their values is what lets a user
        switch the variable back and get their choice returned.
        Worth one line for the maintainer, no more: the Style and
        Colour ramp cells go on naming a style the element does not
        draw, with no greying, so the table describes an element that
        is drawing flat fill as "Categorized / Set1". Low confidence
        that anybody is harmed.
NEXT:   Gate RENDERKIND on the row carrying a variable, and run a
        real batch: seeds 100-159 at 25 steps.
