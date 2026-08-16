# Hunt log: races between QGIS and the plugin over one fact

Hunt name `races-qgis-pins`, 2026-08-16. Frozen at **1acaddc** via
`tools/hunt_probe.py --prepare --name races-qgis-pins`; every probe
runs in that copy at
`$TMPDIR/weavingspace-hunt/races-qgis-pins/tree`. No file in the
shared working tree is edited by this hunt except this log.

DIRECTION: a pinned bound, a copied ladder, the hatching and the No
data split are records the plugin holds; QGIS holds a renderer and a
layer that are also the truth. What happens when QGIS acts on one
while the plugin acts on the other, concurrently or not.

## 14:59:50  iteration 0  [logical]
TRIED:  Orientation. Read the brief, HUNT-RECORD.md (the rows for
        "Dialog against live layer", "Order of operations",
        "Two stores of one fact"), the in-flight hunt log
        (2026-08-15, 2adb7dd) and the swatch hunt log, plus
        dialog.py's pin/copy/hatch/no-data neighbourhood
        (`_edit_quant_colours` 5106+, `_copy_classification` 5265+,
        `_unworn_stripes` 4468, `_on_layer_style_edited` 4703,
        `_graduated_layer_edited` 4906, `_restyle_only` 6430,
        `_add_no_data_layer` 6334, `_add_output_layers` 7637+).
RESULT: n/a. Ground already walked, so not to be re-walked: a pin or
        a copy made UNDERNEATH a run in flight (36 hand-picked pairs
        + 22 seeded sessions, all converge, and the round trip
        through .qgz and .gpkg carries both); the hatching cached
        unhatched (fixed, `_apply_style_change` now restyles first);
        the editor's stale ladder (fixed, `pin_changed` returns the
        settled ladder).
NEXT:   Three hypotheses that all ask "which store wins", each with
        QGIS as the other actor rather than the plugin's own timers.
        H1 the paired no-data layer's opacity against the row's spin
        box across a re-tile; H2 a pin against QGIS's own Classify;
        H3 a dock recolour of the PAIRED layer, which no watcher is
        connected to.

## 15:18:40  iteration 1  [logical]
TRIED:  H1 by reading. dialog.py:6413 `_add_no_data_layer` writes
        `layer.setOpacity(hand_opacity if hand_opacity is not None
        else <the row's spin box>)`, and dialog.py:7813-7815 fills
        `old_no_data_opacity[tid]` with `paired_before.opacity()`
        UNCONDITIONALLY, for every element that had a paired layer.
        So "the user set this by hand in QGIS" is INFERRED from the
        layer rather than recorded, and the inference is true of every
        paired layer that exists. Its twin forty lines up does record
        it: the element layer only keeps `old_layer_opacity[tid]`
        inside the `unchanged or carried_while_deferring` branch, so
        the SIGNATURE decides who wins there.
RESULT: inconclusive by reading; predicts that a re-tile carrying an
        opacity change leaves the element faded and its no-data twin
        solid.
NEXT:   measure it.

## 15:22:10  iteration 2  [perturbation]
TRIED:  p1_nodata_opacity.py. Clean project, 4x4 region, v3 with 3
        NULLs, all four elements on v3, live update OFF. Generate
        (spacing 400). Then element 'a' opacity spinner 100 -> 40 AND
        spacing 400 -> 360 (a geometry change, so a re-tile), then
        Generate.
RESULT: CONFIRMED. After run 1 every element and twin reads
        (1.0, 1.0). After run 2 element 'a' reads 0.4 and its
        no-data layer reads 1.0, with the row's spinner saying 40.
        b, c, d unchanged at (1.0, 1.0). This is the exact harm the
        method's own comment names -- "an element faded to 40% drew
        its missing-value areas at full strength" -- through the door
        the fix for it opened.
NEXT:   a second, independent route, and the file that leaves the
        machine.

## 15:29:30  iteration 3  [perturbation]
TRIED:  p2_gpkg_cold.py. Same sequence with a GeoPackage output (which
        gates live update off by itself, so this is the ordinary
        setting for anyone exporting). Then the dialog closed, the
        project CLEARED, and each table opened COLD as a plain
        QgsVectorLayer with no dialog in the process.
RESULT: CONFIRMED by the second route. In the project: element 0.4,
        paired 1.0. From the file alone: `tiles_a` valid, 112
        features, opacity 0.4; `tiles_a_no_data` valid, 24 features,
        opacity 1.0. The map that leaves the machine draws 24 solid
        tiles over a layer faded to 40%.
NEXT:   when did it start, and does anything heal it.

## 15:33:05  iteration 4  [logical]
TRIED:  `git log -S hand_opacity -- weavingspace_qgis/dialog.py`.
RESULT: Introduced by 920369c ("An empty column draws as no data, and
        three of my own tests could not fail"), 11 commits before
        HEAD, which is the fix for the pixel hunt's "a hand-set
        opacity lost at every re-tile". The line it replaced was the
        unconditional `layer.setOpacity(<row's spin box>)`, so before
        that commit the paired layer always followed the row and this
        case was right. A defect inside an earlier fix for the same
        feature, which is the pattern HUNT-RECORD notes for this
        round.
NEXT:   reachability -- does live update ON avoid it, and does a later
        style change heal it? Then on to H2 (a pin against QGIS's own
        Classify) and H3 (a dock recolour of the paired layer).

## 15:47:20  iteration 5  [perturbation]
TRIED:  p3_reach_and_heal.py -- four questions about H1's reach, each
        on its own fresh fixture and a cleared project.
RESULT: (a) live update ON, both changes inside one 900 ms debounce:
        DIVERGES, (0.4, 1.0). Live update does not save anybody.
        (b) live ON with the opacity allowed to settle first: (0.4,
        0.4) both before and after the re-tile -- so the window is one
        debounce wide, or unbounded with live update off (which is
        forced for GeoPackage output).
        (c) any later style-only change HEALS the project copy back to
        (0.4, 0.4). The divergence is transient in the session and
        permanent in whatever was written while it stood, which is
        what iteration 3 read out of the .gpkg.
        (d) NEGATIVE CONTROL: an opacity genuinely hand-set on the
        paired layer in QGIS (0.7) survives a re-tile that carries no
        opacity change. So 920369c's promise is real and a fix must
        keep it -- reverting that commit is not the answer; telling a
        carried-over value from a chosen one is.
NEXT:   H2, the pin against QGIS's own Classify.

## 15:56:40  iteration 6  [perturbation]
TRIED:  H2. p4_pin_vs_classify.py. Clean project, v3 with NO nulls so
        the null workaround is out of the picture. Generate; pin the
        low bound at 30 (written where `pin_changed` writes it) and
        restyle; then QGIS's Graduated panel Classify, done the way
        the panel does it -- clone the layer's renderer,
        `updateClasses(layer, mode, n)`, `setRenderer`.
RESULT: CONFIRMED as a divergence, DESIGN CALL UNCLEAR. Positive
        control good: the pin reached the map, (1,30)(30,31). After
        Classify the map draws (1,17)(17,31); `_pinned_bounds` still
        says {'low': 30.0}; `_current_graduated_classes` still returns
        (1,30)(30,31); the swatch still boxes the pinned end; the bar
        said NOTHING; and an explicit Generate does not put it back,
        because `_last_signatures` never moved.
        The mechanism is dialog.py:4961 -- `_graduated_layer_edited`
        compares COLOURS only, and a Classify with the same ramp and
        count returns the same five colours over different bounds, so
        the branch commented "our own seeding, or an edit that changed
        nothing" takes an edit that changed every break. The
        docstring's enumeration of what is deliberately left alone
        names the CLASS COUNT and the FIELD; bounds are not in it.
        NOT CLAIMED as a defect: CLAUDE.md already records that
        Classify reverts the plugin's breaks, and the signature rule
        preserving dock work is settled. What is new is only that the
        dialog goes on stating the pin, silently, forever. Reported as
        an observation for the maintainer to weigh, not as a claim.
NEXT:   H3, the paired layer against the dock.

## 16:04:10  iteration 7  [perturbation]
TRIED:  H3, first attempt (p5_dock_vs_paired.py).
RESULT: INCONCLUSIVE -- MY OWN FIXTURE. Its positive control (the same
        recolour on the ELEMENT layer, which must be adopted) did not
        fire, so nothing it said could be believed. p6_diagnose.py
        found why: the control ran after I had moved the class-count
        spinner, so `_current_graduated_classes` returned 6 colours
        against the layer's 5 and the count guard at dialog.py:4963
        returned before adoption. Driven cleanly the control is
        perfect -- picks {'0': '#ff00ff'} and "Element 'a' keeps the 1
        colour(s) set in QGIS".
        p6 also SEGFAULTED first time, at
        `list(er.ranges())[0].symbol()`: the documented
        temporary-frees-its-ranges trap, met by writing the anti-
        pattern into a probe while quoting it in the log. Bind the
        list.
NEXT:   H3 again, with the control driven properly.

## 16:12:30  iteration 8  [perturbation]
TRIED:  p7_paired_dock_colour.py. Generate with a no-data split;
        recolour the PAIRED layer in the dock (categorized renderer,
        `updateCategorySymbol`, `setRenderer` -- the signal a real
        dock edit sends); then a style change and a Generate, which
        takes the restyle fast path.
RESULT: CONFIRMED. As generated the paired layer is #dddddd; after the
        dock recolour it is #ff00ff and the bar says NOTHING; it is
        recorded nowhere (`_quant_colours[tid]['v3'][NO_DATA_KEY]` is
        None); after the restyle it is #dddddd again and the only
        notice is "restyled a (no re-tiling needed)". The identical
        act on the element layer beside it is adopted, recorded and
        announced (p6). `_watch_element_layer` (dialog.py:4617) is
        connected to element layers only, and
        `_restyle_no_data_layer` (dialog.py:6285) calls setRenderer
        unconditionally. This is CLAUDE.md's own paired-artefact
        lesson -- "every writer that maintained the original has a
        twin that does not" -- through the reader half.
NEXT:   re-read HEAD and report.

## 16:24:00  iteration 9  [perturbation]
TRIED:  p8_repeat.py -- H1 on a DIFFERENT fixture and a different
        geometry change: 6x6 region, cell 800, five nulls, opacity 25
        rather than 40, and the DESIGN FAMILY moved rather than the
        spacing. First attempt proved nothing (the family I chose was
        the one already selected, so no geometry change and no
        re-tile); it now asserts its own premise -- geometry signature
        moved, and the element's layer id changed -- before reading
        anything.
RESULT: CONFIRMED again: laves 3.3.4.3.4 -> crosses 4, spinner 25,
        element 0.25 and paired 1.0. Three independent fixtures, two
        different geometry changes, two live-update settings.

## 16:27:30  iteration 10  [close]
TRIED:  `hunt_probe.py --status`; `git status`.
RESULT: HEAD is 1acaddc and has NOT moved since --prepare, so every
        claim above is about the current tree. `git status` shows only
        untracked hunt logs -- this one and three siblings' -- and no
        source file anywhere was edited by this hunt. Every probe
        lives in the session scratchpad (common.py, p1..p8) and each
        is one `tools/hunt_probe.py --run` away.

CLAIMED: one defect (H1). One observation not claimed as a defect
(H2). One confirmed asymmetry offered with lower confidence (H3).
Hypotheses logged: 3, plus one killed as my own fixture (p5) and one
premise-failure caught by its own assertion (p8's first run).
