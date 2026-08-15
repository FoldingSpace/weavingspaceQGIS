# Hunt log: pinned bounds and copied ladders over awkward data

HEAD 2adb7dd. Shape: asymmetry. Area: pinned bounds and copied ladders
over columns holding nulls, infinities and NaN, negatives, one value,
two values, values spanning many orders of magnitude, integers, and a
column whose values all sit exactly on a pinned bound.

Probes run under QGIS 4.0.3's own python via the scratchpad `qpy.sh`.
No repo source is edited; probe scripts live in the scratchpad.

## 15:28:19  iteration 0  [logical]
TRIED:  Read the brief, CLAUDE.md's settled decisions on pins, copies,
        the null workaround and the reduction rules, HUNT-RECORD.md's
        2026-08-15 entry (seven defects already fixed tonight), and
        bridge.make_graduated_renderer / _apply_pinned_bounds /
        pin_problem / classes_the_map_will_draw / fitted_breaks /
        unworn_classes as a set.
RESULT: inconclusive — orientation only. Three candidate asymmetries
        written down before any code runs:
        (a) the LABEL PRECISION block (bridge.py:1530-1549) asks
            span/k over the WHOLE column, and is evaluated BEFORE pins
            narrow the pool (bridge.py:1642-1679). A pin can squeeze
            the middle into a range far smaller than span/k, so the
            very "legend lying about its own map" the block exists to
            prevent looks reachable again through the pin door.
        (b) the subset clause uses `> low` and `< high`
            (bridge.py:1728-1731), which matches QGIS's containment
            (first range inclusive at the bottom, others lower-
            exclusive) at the LOW end but leaves a value exactly equal
            to the HIGH pin outside the class the user named.
        (c) `awkward` tests `abs(v) > 1e307` while `finite_values`
            tests `math.isfinite`, so 1e308 is filtered out of the
            classifier but still supplies `largest` to
            _apply_pinned_bounds.
NEXT:   Build one probe that, over a grid of awkward columns x pins x
        schemes, checks the three invariants a user would notice: the
        notice count (classes_the_map_will_draw) against the renderer's
        actual class count; the ladder monotonic and contiguous; and
        every finite value falling in some class. Then chase whichever
        breaks.

## 15:31:10  iteration 1  [perturbation]
TRIED:  Grid probe (scratchpad/p1_grid.py): 10 awkward columns x up to 7
        pin sets x k in {2,3,5,8} x 4 schemes, ~700 renderers built
        through bridge.make_graduated_renderer with the same
        classification source the dialog hands it, each checked for
        count-told vs count-drawn, gaps, backwards classes, values
        falling in no class, and duplicate labels. Every pin was put
        through pin_problem first, so only pins the dialog would ACCEPT
        were measured.
RESULT: 100 flags, and almost all of them are NOT pin-specific. The two
        big families both reproduce with pinned=None:
        - "Pretty breaks" tells a different count from what it draws
          (e.g. plain column, k=8, no pins: told 8, drew 9). QGIS's
          pretty breaks chooses its own count; the notice cannot
          predict it. Same with and without pins.
        - Duplicate labels under Jenks at k=8 over 10 distinct values
          (['1 - 1','1 - 1','1 - 1','1 - 2',...]) -- again identical
          with no pins.
        Exactly ONE structural break was pin-only:
        orders column [1e-6,1e-5,1e-4,1e-2,1,1e2,1e4,1e6,1e7,1e8],
        low pin 1e-4, k=8, Jenks -> class 7 is (1e8, 1e7), a class
        whose lower bound is ABOVE its upper. Label reads
        "100,000,000 - 10,000,000"; no value can occupy it; 1e8 (the
        column maximum) is drawn in class 6 alongside 1e7.
NEXT:   Second route: drive QGIS's classifier directly, with no plugin
        code, over exactly the seven samples the pin filter leaves, to
        see whether the backwards class is QGIS's or ours.

## 15:32:40  iteration 2  [perturbation]
TRIED:  scratchpad/p3_qgis_direct.py -- QgsGraduatedSymbolRenderer.
        updateClasses driven straight, no bridge import: (A) the seven
        middle values in a bare memory layer, k=7 Jenks; (B) the full
        ten with the plugin's own subset string applied; (C)(D) the
        full ten unfiltered and with the null clause only.
RESULT: RULED OUT as a plugin defect. A and B are byte-identical and
        both end (1e8, 1e7): QGIS's own Jenks returns a backwards final
        range whenever k equals the number of distinct values on a
        column spread over many orders of magnitude. C and D (k=7 over
        10 distinct) are fine. So this is a QGIS/mapclassify fault the
        pin merely makes easier to reach -- the pin removes samples, so
        k-pins lands exactly on the middle's distinct count. Worth
        reporting to the maintainer as a dependency note, not as a
        defect in this code.
NEXT:   The brief's own steer: the exact boundary. Take a value that
        sits EXACTLY on a pinned bound all the way through the dialog
        and ask which class its tiles are drawn in, against what the
        control says the pin means.
