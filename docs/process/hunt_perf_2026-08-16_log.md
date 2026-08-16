# Performance and scale hunt, 2026-08-16

Frozen commit: 3b34364 (HEAD moved from 7bd34a6 to 3b34364 between my
first --prepare and my first probe; re-prepared).

## 01:10:40  iteration 1
TRIED:  perception.clashes cost against element count n and class count k,
        pure Python, no QGIS. n in 2,4,8,16,24; k in 1,5,20.
RESULT: confirmed quadratic in BOTH. n=8/k=20 406 ms; n=16/k=20 1744 ms
        (x4.3 for x2 n); n=24/k=20 4008 ms. k alone: n=24 k=1 10 ms,
        k=5 254 ms, k=20 4008 ms (x25 for x4 k). distance() recomputes
        the Lab conversion on every call and nothing is cached, so the
        call count is 3 visions * C(n,2) * k^2.
NEXT:   find whether n>=16 elements with k=20 classes is reachable from
        the dialog at all -- a 4 s freeze only matters if a real design
        can ask for it. Then find where _legibility_note is called from
        (dialog.py:5270 and :7311) and whether it blocks the GUI thread.

## 01:11:30  iteration 2
TRIED:  is a large k reachable? dialog.py:7184 only WARNS above 60 distinct
        values ("Is that field really categorical?"), it does not cap. Timed
        perception.clashes at k=60..500, and end-to-end generation with
        categorical elements.
RESULT: confirmed. Synthetic: n=2 k=60 0.13 s, k=120 0.52 s, k=250 2.25 s,
        k=500 9.13 s. Linear in element PAIRS: k=250 n=2/3/4 = 2.25/6.77/
        13.63 s for 1/3/6 pairs. End to end (QGIS, real renderers, 400-
        feature region, spacing 2000, 4 categorized elements on distinct
        fields, default ramps all DIFFERENT so the shared-ramp exemption
        never fires): generate+settle 2.15 s of which clashes was 1.88 s,
        with 91-95 classes per element. So k is bounded by TILES PER
        ELEMENT, not by 60, and tiles are capped at 200,000.
NEXT:   push spacing down so k reaches the high hundreds and measure the
        real freeze; the cost model is 12 us * 3 visions * pairs * k^2.

## 01:13:05  iteration 3
TRIED:  the table rebuild -- is it quadratic in element count? Timed the
        element-count change and one variable-combo edit at n=2,4,8,16,26
        (26 = catalog.MAX_ELEMENTS).
RESULT: ruled out. Rebuild after an n change: 1.2/1.0/1.1/1.1/1.4 ms.
        One variable edit: 10.5/17.2/27.1/39.2/58.0 ms -- linear, and
        58 ms at the largest design the plugin offers. _assignments()
        0.2..8.9 ms. Nothing here a user can feel.
NEXT:   back to the legibility check, and validate the quadratic at the
        k a real region reaches.

## 01:13:05  iteration 4
TRIED:  end-to-end freeze with a high-cardinality categorical field, and
        the k^2 law at k=500/1000/2000 on one element pair.
RESULT: confirmed. End to end in QGIS: 400-feature region, spacing 500,
        4 categorized elements, 401 classes each -- generate+settle
        36.75 s, of which perception.clashes was 35.70 s. The tiling
        itself was ~1.05 s. Per PAIR: k=250 2.25 s, k=500 9.11 s,
        k=1000 37.05 s (exactly x4 per doubling, three points).
        Cost = 12 us x 3 visions x pairs x k^2. Nothing on screen says
        anything during it: it runs inside _on_generated on the GUI
        thread after the worker has returned, so the progress bar is
        already gone.
NEXT:   the size guard's honesty, and whether the spacing it SUGGESTS
        passes on the second attempt; then region feature count, which
        the guard never looks at (it reads total_bounds only).

## 01:17:20  iteration 5
TRIED:  (a) does the spacing the size guard SUGGESTS pass on the second
        attempt? All 11 families x n=2,4,8,26 x spacings 50 and 200 over a
        200km square region: refuse, take the suggestion, rebuild the unit,
        re-estimate. (b) region feature count at FIXED bounds (the guard
        reads total_bounds only): 100, 1024, 4900 features, same 20km
        extent, same spacing.
RESULT: (a) ruled out -- 0 of the refusals were refused again.
        (b) ruled out -- generate+settle 1.16 / 1.31 / 1.51 s for 100 /
        1024 / 4900 features. Sub-linear; nothing a user feels.
        BUT (c) the same run shows the estimate UNDER-counting: est=1,162
        against 1,682 tiles actually produced, ratio 0.69. bridge.py:433
        promises "at or above the true one" and dialog.py:6267 calls it
        "slightly generous".
NEXT:   is the under-count systematic? Sweep families and spacings
        comparing est with the tiles actually made. If it is, the 200,000
        hard cap admits ~290,000 and the "roughly N tiles" number the user
        is shown is 30% low.

## 01:19:50  iteration 6
TRIED:  is the estimate's under-count of iteration 5 real? Re-ran the
        family sweep spying on the estimate THE GUARD ITSELF computes
        inside _generate, instead of one I computed before the unit
        rebuild had settled.
RESULT: ruled out, and iteration 5(c) was MY FIXTURE. The guard's own
        estimate is generous everywhere: 11 families x 2 spacings, ratio
        est/actual 1.90 to 2.72, never below 1. My earlier reading was
        taken from a self._unit that had not yet been rebuilt for the new
        spacing, so it was an estimate for a different design.
NEXT:   the live-update path. LIVE_UPDATE_MAX_TILES is 20,000, and the
        legibility check at dialog.py:7311 sits in _on_generated with no
        live/manual distinction -- so if it fires on live runs, the
        35 s freeze repeats on every tweak with no button press.

## 01:22:55  iteration 7
TRIED:  (a) does the LIVE path pay the legibility cost too? Same fixture
        as iteration 4 driven through _maybe_live_generate. (b) second,
        independent route: a 50 ms QTimer heartbeat across the whole run,
        to measure event-loop starvation rather than timing the function.
        (c) the ordinary graduated case at catalog.MAX_ELEMENTS.
RESULT: confirmed on all three. (a) live run: 36.23 s total, 35.18 s in
        clashes -- no button press involved, and it repeats on every
        tweak. (b) 9 heartbeats fired where ~700 were due; worst gap
        35.87 s, second worst 0.09 s. The Qt event loop is dead for the
        whole of it, so the indefinite progress bar cannot even animate:
        QGIS beachballs. (c) 26 elements, 20 classes, 325 pairs: 4.76 s;
        k=10 1.19 s; k=5 0.30 s.
NEXT:   re-check HEAD (still 3b34364, unmoved since my second --prepare)
        and report.
