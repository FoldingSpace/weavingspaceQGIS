# Hunt log — ONE VARIABLE GETS ONE LEGEND, shape: asymmetry

Read at commit 8ebd2a3f37db23fcd7bf7d5a84f150484a3a9b99, probed in a
`git archive HEAD` copy at
/private/tmp/claude-501/-Users-luke-claude-scratch/9a569ef7-3f5e-4a44-8ecf-716f080f3573/scratchpad/tree
(the live working tree is being edited by another session and was not
touched). All times UTC.

## 19:05:50  iteration 0  [logical]
TRIED:  Read the settled decisions (CLAUDE.md 1200-1250 at 8ebd2a3),
        HUNT-RECORD.md, and the two seams named in the area:
        bridge.classification_source (bridge.py:1398),
        make_graduated_renderer (bridge.py:1449),
        dialog._classification_values (dialog.py:2366) and its six
        call sites.
RESULT: inconclusive — orientation only. Both re-seeding paths pass
        the same source: the restyle fast path at dialog.py:5774 and
        the run-landing path at dialog.py:7017 both call
        `bridge.seed_renderer(..., self._classification_values(
        a.get("var")))`. Preview (dialog.py:3987) and the dock trial
        (dialog.py:4509) do too. No asymmetry there.
NEXT:   The graduated path's TWIN is the categorized path. Read
        make_categorized_renderer (bridge.py:2006) beside
        make_graduated_renderer.

## 19:07:20  iteration 1  [logical]
TRIED:  The twin. `make_graduated_renderer` (bridge.py:1449) cuts
        breaks from `classify_from`, the region-wide scratch layer.
        `make_categorized_renderer` (bridge.py:2006) takes
        `layer.uniqueValues(idx)` — the ELEMENT layer — and colours
        category i at ramp position i/(n-1) (bridge.py:2077/2083),
        where n is that ELEMENT's distinct count. `seed_renderer`
        (bridge.py:2178) passes classify_from to the graduated branch
        only; the docstring says so on purpose. So a categorical
        variable's legend is still cut per element, exactly as the
        graduated one was until 2026-08-14.
RESULT: inconclusive so far. Probe 1
        (scratchpad/probe_cat_legend.py, n=12 region, one RARE cell,
        spacing 1200, laves 3.3.4.3.4, 4 elements all on `lc`):
        every element caught all five values (113/112/113/112 tiles
        of 144 cells), so all four legends agree on POSITION. My
        colour comparison was the wrong measure — elements
        deliberately wear different ramps (tab10/Set2/Set1/Pastel1),
        so different colours there is the design, not the defect.
NEXT:   Compare ramp POSITION, not colour, the way
        test_one_variable_gets_one_legend_wherever_it_appears does,
        and use a spacing coarse enough that an element MISSES a
        value. Sweep spacing.

## 19:08:30  iteration 2  [perturbation]
TRIED:  probe_cat_legend2.py — same 12x12 synthetic region, one RARE
        cell, comparing RAMP POSITION per value across elements at
        spacings 3000 / 4500 / 6000.
RESULT: CONFIRMED at 6000. Elements draw 1, 2, 3 and 4 classes over
        the same column: 'water' sits at rung 0 in element a, rung 1
        in b and rung 3 in d; 'forest' at rung 0 in b and rung 1 in c.
        Route 1 (renderer.categories()) and route 2 (startRender +
        originalSymbolForFeature over every tile) give identical
        answers. 3000 and 4500 agree by accident — every element
        happened to catch the same values.
NEXT:   6 tiles per element is a degenerate map. Reproduce on the
        PACKAGED fixture at an ordinary spacing, or it is a curiosity.

## 19:09:40  iteration 3  [perturbation]
TRIED:  probe_cat_legend3.py — tests/data/landcover-categorical.gpkg
        (144 features; landcover = forest 25, urban 27, crops 27,
        water 25, wetland 17, bare 16, null 7), laves 3.3.4.3.4, n=4,
        spacing 2000, every element on `landcover`.
RESULT: CONFIRMED on real fixture data at an ordinary spacing.
        Elements a/b/c get 13/12/13 tiles and 6 classes; element d
        gets 12 tiles and 5 — it caught no `bare` tile. Every one of
        d's remaining classes is therefore one rung lower than the
        same value's rung in a, b and c (water 4 vs 3, crops 1 vs 0,
        urban 3 vs 2, forest 2 vs 1, wetland 5 vs 4). Both routes
        agree. The Classes cell reads 6 for every row, including d.
NEXT:   Elements wear different ramps by default, so "different
        colour" is not yet harm. Put two elements on the SAME ramp —
        an ordinary thing to want — and see whether one colour comes
        to mean two values.

## 19:10:30  iteration 4  [perturbation]
TRIED:  probe_cat_legend4.py — as above but every row driven to
        ramp `tab10` through `combo.activated.emit(index)`, the way a
        user picks it.
RESULT: CONFIRMED, and this is the harm. a/b/c legend:
        bare #1f77b4, crops #2ca02c, forest #9467bd, urban #e377c2,
        water #bcbd22, wetland #17becf. Element d legend:
        crops #1f77b4, forest #2ca02c, urban #8c564b, water #7f7f7f,
        wetland #17becf. So on ONE map:
          #1f77b4 means 'bare' in a, b, c and 'crops' in d
          #2ca02c means 'crops' in a, b, c and 'forest' in d
        Route 2 (startRender over every tile) paints exactly those
        colours. Fresh process, project.clear() first, nothing else
        had run — so not a fixture artefact.
NEXT:   Locate it in source and date it.

## 19:11:10  iteration 5  [logical]
TRIED:  Where and since when.
RESULT: bridge.py:2042-2045 in `make_categorized_renderer` —
        `values = sorted(layer.uniqueValues(idx) ...)` where `layer`
        is the ELEMENT layer — and bridge.py:2077/2083, which colour
        category i from `n = len(values)`, that element's own count.
        `seed_renderer` (bridge.py:2178-2182) passes `classify_from`
        to the graduated branch only. Commit 4ee76fd (2026-08-14,
        "One legend for one variable, wherever it appears") added
        classify_from to the graduated path and left the categorized
        twin as it was at 3bd5f52 (v0.23.0, initial commit), so the
        categorical half of the rule has never held.
NEXT:   Sweep the other questions in the brief and record what was
        ruled out.

## 19:13:00  note on the times above
Entries 2-5 were appended to this file in ONE write at 19:11:17 UTC,
after the four probes had run back to back; the times in their headers
are when each hypothesis was formed and its probe run, not when the
text was typed. Recording that here rather than leaving timestamps
that would not survive being checked. Entries 0 and 1 were written
before the work they describe, as the protocol asks.

## 19:17:30  iteration 6  [perturbation]
TRIED:  probe_grad_checks.py — the four questions the brief named,
        on the GRADUATED half. n=12 region, laves 3.3.4.3.4, spacing
        1200, all four elements on v3.
RESULT: all RULED OUT.
        (a) Run-landing: one ladder across all four elements,
            [(0,4.0),(4.0,14.2),(14.2,30.0),(30.0,55.0),(55.0,121.0)].
            After a style-only change (Quant: Equal intervals), which
            takes the restyle fast path, still one ladder across all
            four, [(0,24.2)...(96.8,121.0)] — and byte-identical to a
            ladder built independently by calling
            bridge.make_graduated_renderer with
            bridge.classification_source over the region column
            directly. Same source, both paths.
        (b) Moving element a to `v1` gives it
            [(0,2.2),(2.2,4.4),(4.4,6.6),(6.6,8.8),(8.8,11.0)], which
            matches the independently computed whole-region v1
            ladder exactly; b, c, d keep the v3 ladder. The new
            column's map-wide breaks, not the old ones.
        (c) Unclassed: 50 classes on every element, first (0, 2.42),
            last (118.58, 121.0), against a column running 0 to 121.
            The whole column's range, not one element's.
        (d) The cache key at dialog.py:2418 is (layer id, field,
            _layer_fingerprint(), _data_version). The fingerprint
            carries feature count, extent, field names and CRS, so a
            subset string or an edit through QGIS moves it; the one
            thing it cannot see is a rewrite straight through the
            data provider, which CLAUDE.md already records as a
            stated limit rather than a defect. Not claiming it.
NEXT:   Report. One finding: the categorized twin of the rule.

## 19:18:00  summary
Hypotheses logged: 6.  Ruled out: 5 (both re-seeding paths, the
variable change, Unclassed, the cache key).  Claimed: 1 — a
categorical variable's legend is still cut per element, so on the
packaged fixture at spacing 2000 with every element on tab10, tab10's
#1f77b4 means 'bare' in three elements and 'crops' in the fourth.
Reproduce with:
  bash scratchpad/qpy.sh scratchpad/probe_cat_legend4.py
(the probe scripts live in the scratchpad, not the repo; no repo
source was modified and `git status` is clean apart from this log).
