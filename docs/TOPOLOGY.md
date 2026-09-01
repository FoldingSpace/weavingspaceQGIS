# The topology of the repeating unit: what is known, and what it cost to know

The Topology tab lets somebody take hold of the EDGES and VERTICES of
the tile unit and move them. This document is what has been measured
about that — the library underneath it, the costs, the traps, and the
rulings that settled its design. MAINTAINING.md describes how the tab
is built; this is the evidence under it.

**It is not geospatial topology.** No node/edge/face model of the map
on the ground; no claim that the stamped polygons share edges exactly.
It is the combinatorial and symmetry structure of the REPEATING UNIT,
a dozen tiles in unit space, where the map has seventy thousand. A tab
called "Topology" will be read by some GIS users as promising the
other thing, so it says on its face that it describes the repeating
unit and not the map.

## What a build costs, and why that decides the architecture

`Topology.__init__` is eager: eight setup passes and a dual graph, with
no lazy half to discount. Measured through the plugin's own
`catalog.make_unit`, three runs each, on 2026-08-31:

    laves 3.3.4.3.4      0.79 - 0.88 s
    hex-slice 6          1.89 - 1.95 s
    square-colouring 5   2.80 - 2.84 s

The cost tracks the SHAPE rather than the element count — n=5 is the
slowest of those and n=12 is not — so it cannot be bounded by the
element spinner. Against that, building the unit itself is 0.01-0.05 s
at every count up to 256, and the live debounce is 900 ms.

**THE RE-VENDOR DID NOT CHANGE IT.** Upstream 6190917 rewrote
`topology.py` by +179/-207, including "converted Topology code so only
Topology object references Tiles, Vertices, and Edges directly" and
the removal of custom deepcopy helpers. Measured on both checkouts in
one run: 0.79/1.90/2.81 s before, 0.81/1.89/2.80 s after. The refactor
was structural. Anyone hoping a re-vendor will make this cheap should
know it did not.

## Chaining, not rebuilding: the measurement that settled it

Until 2026-08-31 `apply` rebuilt a Topology between edits, on the
reading that upstream's caution — a transformed Topology "will
probably not be correctly labelled" — made the returned object unsafe
to aim the next edit with.

**THE MAINTAINER ASKED THE RIGHT QUESTION**: if the topology breaks,
can the next edit not be aimed with the LAST topology's labels
regardless? Measured that day, and the answer is yes, with two gains
besides.

    sequence                    rebuild between      chained
    nudge then nudge (laves)    area 250000.0        identical
                                perim 3863.723       3863.723
    rotate then nudge (laves)   IMPOSSIBLE           works: 246110.0
    nudge then nudge (hex-3)    perim 3464.109       3464.112
    rotate then nudge (hex-3)   IMPOSSIBLE           works

**What rebuilding cost.** `rotate_edge` routinely leaves a design with
gaps; `Topology` refuses a design with gaps; so the rebuild returned
None and EVERY LATER EDIT was refused for want of anything to aim at.
Chained, the same pair applies perfectly well.

**And it moved the labels under the person.** A fresh build re-derives
the transitivity classes, so "A" afterwards is not necessarily the A
that was clicked — which is why the two arms differ by a rounding on
hex-slice 3 and agree exactly on laves.

**Upstream's caution is about something else.** It warns that a
transformed object's labels may not match A FRESH BUILD. We do not
want a fresh build: the labels a person aims with should be the ones
they were shown. Measured over five chained edits on two designs, the
class list never moved (`a,b` and `A,B` throughout) and every
intermediate tileable stayed valid.

**What is NOT fed back** is the repair. `_make_drawable` mends what a
manipulation can emit — coincident vertices, mostly zigzag's — and the
mended copy is what is drawn and tiled, while the chain carries the
library's own object. The repair leaves every area unchanged to a part
in 1e9, so the two cannot drift in any way a map can show.

## Whether a design still HAS a topology, in 0.3 ms

A build answers it in seconds. The condition itself — do the tiles
still meet — is answerable by laying down one ring of repeats, unioning
them, and looking for interior rings: a hole in a patch IS a gap.

    state              gap ratio     cost      Topology builds?
    untouched          0.0           4.0 ms    yes
    after nudge        5.2e-10       4.9 ms    yes
    after rotate       1.2e-2        5.1 ms    NO

**AND THE OBVIOUS CHEAPER TEST IS WRONG.** Subtracting the union of the
tiles FROM the prototile costs 0.3 ms and reads perfectly — and reports
10.6 % of an untouched `laves 3.3.4.3.4` missing, because a unit's
tiles need not lie inside the particular polygon its prototile is, even
where the two have identical area. It was caught by the tab marking an
unedited design as broken, and confirmed by the tell this project knows
best: every unit measured returned the same number, including the one a
standalone run had just called sound.

Seven orders of clear air between the two answers, about two hundred
times cheaper than a build. So every edit in the change list can carry a mark saying
whether the design still carried a topology at that point — which is
what tells somebody how far back they would have to roll — and the
same subtraction yields the GAP GEOMETRY, so the invalid parts can be
drawn on the diagram rather than described.

## The two vertex manipulations could not move anything visible

Measured 2026-08-31, and it is the reason a maintainer clicking and
dragging nodes reported that nothing happened at all.

    control            at its maximum      share of a 707-unit design
    nudge_vertex       dx=dy=1.0  ->  1.414        0.20 %
    nudge_vertex       dx=0.5     ->  0.500        0.07 %
    push_vertex        push_d=1.0 ->  0.414        0.06 %

The library's `dx`, `dy` and `push_d` are ABSOLUTE displacements in the
unit's own coordinates; the controls offered them over -1 to 1 as
though they were fractions. The whole domain of both vertex controls
was therefore invisible — under a pixel on a 400-pixel drawing — and
the drag made it worse in the same direction, since the view reports a
drag as a fraction of the unit and hands the library 1.0 for a drag
clear across the picture.

This is the project's own rule that A CONTROL MUST BE ABLE TO REPRESENT
ITS DOMAIN, arriving in a new tab. The edge manipulations are
unaffected: their arguments are dimensionless, and at one control step
they move 1-6 % of the unit.

    laves 3.3.4.3.4    rotate_edge 15°   4.22 %
                       scale_edge 1.1    1.61 %
                       zigzag_edge       3.43 %
    hex-slice 3        rotate_edge 15°   5.21 %
    archimedean 4.8.8  rotate_edge 60°  28.05 %   (usually refused)

## What a rebuild does to the classes, if one happens

One vertex nudge on `laves 3.3.4.3.4`, then a rebuild from the edited
unit: edge classes go from `a, b` to `a, b, c, d, e, f, g, h, i, j` and
vertex classes from `A, B` to `A, B, C, D, E, F`. That is not a defect
— an edit breaks the symmetry the classes ARE — but it is why a
drawing that showed a rebuilt topology would fill the chooser with ten
classes after one edit. Chaining avoids the question entirely.

## The interaction, checked modality by modality

Driven through the widget's own mouse events on 2026-08-31, because a
control must act through its own signal:

    click a vertex        selects
    click an edge         selects
    drag a vertex         previews during, commits after
    drag an edge          previews during, commits after
    Apply (each verb)     records and moves the design
    Undo, Clear           move the design and the record

**Edges are properly clickable**, which had been in doubt: at 400, 600
and 900 px the hit test's 8 px reach leaves 107 of 107 edges with a
median clearance of 102 px along their length. `_distance_to_edge`
measures to the nearest point ON the line rather than to a disc at the
midpoint, which is what makes that true.

**What did NOT work** is the drawing: it never reflected an edit by any
route, because the panel was handed the topology built from the
UN-EDITED unit while the preview and the map drew from the edited one.
One fact, two stores, disagreeing on screen — and the reason the tab
was reported unusable.

## The dual is drawn once and the tiles are drawn many times

    design             tiles drawn    dual tiles drawn
    laves 3.3.4.3.4    36             6
    hex-slice 4        28             4

`topology.tiles` is a patch of repeats; `dual_tiles` is one repeat's
worth. So with the toggle on, the dual sits in the middle of a field of
tiles it does not cover. The tiling is periodic and the dual repeats on
the same lattice vectors, so this is a drawing gap rather than a fact
about duals.

## Three instrument faults, in one afternoon, all mine

Recorded because each read exactly like a finding about the product,
and this project counts a day whose findings are mostly its own
instruments as a day nobody should act on.

**A POINT TAKEN AS "THE FIRST IN THE TOPOLOGY" IS USUALLY OFF-SCREEN.**
The topology holds the whole patch — 72 points for a four-tile unit —
while the view's bounds come from the core tiles. Clicking the first
one reported "click a vertex: NOTHING MOVED". Take the thing nearest
the middle of the widget.

**AN EDGE'S `coords` ARE ITS ENDPOINTS, AND ITS ENDPOINTS ARE
VERTICES.** Measuring clearance at the coords alone gave 0.0 px for
every edge, on every design, at every size — and "0/107 edges are
clickable", which would have been a serious finding. The uniform
verdict is what gave it away. Sample ALONG the segments.

**A FAMILY TYPED IS NOT A FAMILY CHOSEN.** `archimedean 4.8.8` does not
exist at n=4, so `setCurrentText` did nothing and three designs
reported one topology, which read as a drawing that never rebuilt. Look
fixture names up in the catalogue.

## The rulings of 2026-08-31

The maintainer's, on meeting the tab in rc9 and finding it unusable:

1. **The drawing shows the design AS EDITED**, and each edit applies to
   the result of the last. "If you can't see what you're doing and
   manipulate it iteratively on the results of previous changes, it
   just doesn't make sense."
2. **The original may be ghosted underneath**, and a drag shows what it
   is changing as it happens.
3. **Labels are unambiguous and stable**, minted rather than
   re-derived, stored so that a reopened or resumed design picks up
   where it left off — across QGIS and GeoPackage roundtrips alike.
   Chaining gives this within a session by construction.
4. **Rollback of one or two edits** is an interface affordance, not a
   recomputation.
5. **Validity is shown rather than enforced**: which transformations
   were topologically sound is marked in the editor and the change
   list, so somebody can see how far back to roll, and the invalid
   parts are marked subtly on the diagram. Some editing still working
   when not all of it does is an acceptable state rather than an error.
6. **Everything must be reachable at realistic sizes**, which may mean
   a larger default window.
