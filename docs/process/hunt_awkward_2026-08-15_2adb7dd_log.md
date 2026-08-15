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

## 15:36:05  iteration 3  [perturbation]
TRIED:  Tree moved under me (HEAD 0305787, dialog.py modified by another
        agent), so everything from here runs against a pinned copy of
        2adb7dd exported with `git archive` into
        scratchpad/hunt-awkward. Probe p4_empty.py: for 10 columns x
        every pin position sitting exactly ON a data value x k in
        {3,5,8} x Quantiles/Equal interval, count classes NO tile can
        occupy, split into PINNED-EMPTY and MIDDLE-EMPTY, with the
        unpinned column as control.
RESULT: 102 PINNED-EMPTY, 46 MIDDLE-EMPTY, and NEITHER is a defect.
        PINNED-EMPTY is a settled decision (CLAUDE.md, bridge.py:1664:
        "a pinned class holding no samples is a deliberate statement
        about where a reader's eye should start"). It is where the
        low/high asymmetry lives -- pinning HIGH at the column maximum
        leaves (max, max], which nothing can occupy, while pinning LOW
        at the minimum gives [min, min], which the minimum occupies --
        but that is QGIS's containment rule and the decision above, not
        a fault. Every MIDDLE-EMPTY family reproduces with pinned=None:
        e.g. "on bound" [1,2,3,5,5,5,5,5,9,10] unpinned, k=3,
        Quantiles -> [(1,5),(5,5),(5,10)], class 1 empty. Frequent
        repeated values, not pins.
NEXT:   Arithmetic in this area looks sound. Move to the CONTROL that
        sets a pin, and ask whether it can represent the numbers an
        awkward column carries.

## 15:38:40  iteration 4  [logical then perturbation]
TRIED:  category_editor._bound_box (category_editor.py:534-541) gives
        every pinnable bound a QDoubleSpinBox with setDecimals(6) and
        setRange(-1e12, 1e12), while the READ-ONLY cells beside it in
        the same row print through _format_bound with "%.10g". Its own
        docstring says the range is "wide open ... because what is
        legal is decided by the map's own data ... a range set here
        would refuse a number for a reason this window cannot explain".
        Probe p5_spinbox.py builds the real CategoryColourDialog on
        three ladders and reads the widgets.
RESULT: CONFIRMED, measured. Province-scale areas in square metres
        (ladder [(1.1e11,5.4e11),(5.4e11,1.54e12),(1.54e12,9.1e12)]):
        the last row's read-only cell prints "1.54e+12" and the
        editable box on that same row holds 1000000000000.0. Driving
        the pin the way a user does (pin.setChecked(True), which is
        what a click emits) pinned 1.0e12 -- not the break the row was
        showing. On a rate column [(1e-9,4e-7),(4e-7,8.5e-7),
        (8.5e-7,3e-6)] the low box shows 0.0 for a bound of 4e-07 and
        the high box shows 1e-06 for a bound of 8.5e-07. The ordinary
        column is faithful, so the two ends of one window can disagree
        depending only on magnitude.
NEXT:   Two more things to nail: real KEYSTROKES rather than setValue,
        and whether the substituted number reaches the map.

## 15:41:30  iteration 5  [perturbation]
TRIED:  p7_typing.py -- QTest.keyClicks into the box's line edit, then
        Return, on the ladder whose last class begins at 1.875e12.
        p6_reaches_map.py -- twenty province-scale areas through
        bridge.make_graduated_renderer, pinned at the break the user
        was looking at versus pinned at what the control pinned, then
        each value placed under QGIS's own containment rule.
RESULT: CONFIRMED, and worse than the display fault. Typing
        "3000000000000" (3e12) leaves the box holding 300000000000.0
        (3e11) -- the validator swallows the digit that would cross the
        ceiling and the pin record takes 3e11 with no message at all.
        A factor of TEN, silently, through the one control whose
        docstring promises "a typed number is either honoured or
        visibly rejected and never quietly changed into a different
        one". Second route, the map: pinning the last class at
        1.875e12 gives [(2.1e10,2.83e11),(2.83e11,1.117e12),
        (1.117e12,1.875e12),(1.875e12,9.1e12)]; pinning at the 1.0e12
        the control produced gives [(2.1e10,6.7e10),(6.7e10,3.817e11),
        (3.817e11,1.0e12),(1.0e12,9.1e12)] -- 11 of the 20 areas change
        class. pin_problem accepts both, so nothing refuses and nothing
        is said.
        Introduced by 12f8c3d ("The pin reaches the map, by a glyph and
        two dresses", 2026-08-14), the commit that added the control;
        still present in the live tree at 0305787
        (category_editor.py:537-538).
NEXT:   Report. Ruled out along the way and worth recording: the
        subset-clause interaction (the null clause and the pin clause
        compose correctly, and `> low` / `< high` match QGIS's
        containment at both ends); the notice against the map
        (classes_the_map_will_draw agreed with the renderer everywhere
        except Pretty breaks, which disagrees unpinned too); and the
        backwards Jenks class, which is QGIS's own and reproduces with
        no plugin code in the process.
