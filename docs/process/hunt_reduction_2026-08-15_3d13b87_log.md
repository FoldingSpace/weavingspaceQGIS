# Hunt log — class-count reduction beside pinning; Unclassed clamp beside the graduated pin column

Direction: asymmetry / twins. HEAD 3d13b87. Started 2026-08-15.
Probes run under QGIS 4.0.3's own python via the scratchpad qpy.sh, against a
worktree copy of 3d13b87 (the shared tree has other agents' uncommitted edits
to bridge.py, dialog.py, tests/run_tests.py).

## 21:05:00  iteration 1  [logical]
TRIED:  Read the reduction path (bridge.py:1441-1466) beside the pinning path
        (bridge.py:1578-1672). The reduction counts `distinct` over the WHOLE
        column and compares it with the FULL k, both computed BEFORE pins are
        subtracted and before the subset string removes the samples inside the
        pinned classes. The pinning path then asks the classifier for
        k - pins classes from a strictly smaller pool.
RESULT: inconclusive on paper, but the asymmetry is explicit and contradicts a
        settled decision: bridge.pin_problem's docstring (bridge.py:950-956)
        and CLAUDE.md both say a pin leaving fewer distinct values than the
        remaining classes is DELIBERATELY not refused because "that draws
        fewer classes through the ordinary reduction and says so through
        few_values_message". The ordinary reduction cannot see the post-pin
        pool, and dialog.py:5305 / 5741 feed few_values_message the whole
        column's distinct count and the full k, so neither can fire.
NEXT:   construct a column where distinct >= k but the between-the-pins pool
        has fewer distinct values than k - pins, and measure the ranges the
        renderer ends up with; then read which symbol each feature actually
        gets with startRender, which is the route the HUNT-RECORD says is the
        only one that measures anything.

## 21:34:00  iteration 2  [perturbation]
TRIED:  redprobe1.py -- column [1,2,3,10,20,30,100] (7 distinct), Quantiles,
        k=5, Reds; once with no pins and once with pinned={"low":3,
        "high":30}. Route A: read the renderer's ranges and ask
        bridge.unworn_classes.
RESULT: confirmed. pin_problem(3, 30, values, 5) -> None (accepted). The
        renderer comes back with FIVE classes and class [2] 13.3333-16.6667
        holds no value: unworn_classes -> [2]. The middle pool between the
        pins is {10, 20}, two distinct values, asked for three classes.
        few_values_message("v", 7, 5) -> None, so nothing is said. Control:
        the same pool with no pins asked for 3 classes reduces to 2, as the
        settled decision says it should.
NEXT:   the second, independent route -- startRender and ask QGIS which
        symbol each feature actually gets, with no plugin code in the loop.

## 21:47:00  iteration 3  [perturbation]
TRIED:  redprobe2.py -- QgsRenderContext from QgsMapSettings, renderer
        cloned, startRender / symbolForFeature per feature / stopRender.
RESULT: confirmed by the independent route. QGIS paints four distinct
        colours across five classes: 1,2,3 -> #fff5f0; 10 -> #fcbba2;
        20,30 -> #cb1b1e; 100 -> #67000d. #fa694c (class [2]) is in the
        legend and on no tile. Against the honest count (same pins, k=4)
        three of seven values change colour: 10 #fcbba2 vs #fca082, 20 and
        30 #cb1b1e vs #e32f27. So the map differs as well as the legend.
        A second shape -- {1,5,9}, k=3, pinned high=5 -- draws a class
        labelled "1 - 1", the degenerate legend the constant-column rule
        exists to prevent; few_values_message again returns None.
NEXT:   check whether it reaches the user through the dialog, and date it.

## 21:56:00  iteration 4  [logical]
TRIED:  dialog.py:4520 (the pin gate) and bridge.seed_renderer:1971.
RESULT: confirmed reachable. The dialog validates a pin with exactly
        pin_problem(low, high, region values, assignment["k"]) and, on None,
        stores it and restyles; seed_renderer hands assignment["pinned"]
        straight to make_graduated_renderer. Both notice sites
        (dialog.py:5305 restyle, 5741 run) pass the WHOLE column's distinct
        count and the full k, so neither can fire on a post-pin pool.
        git log -S: the reduction landed in 4ee76fd and the pin path in
        48acb41, both 2026-08-14, reduction first -- so the asymmetry
        arrived with 48acb41, which taught the classifier a smaller pool
        without teaching the reduction about it. Nothing in docs/TEST-MAP.md
        pairs a pin with the reduction.
NEXT:   report. Hypotheses logged 4, ruled out 0, confirmed 1.
