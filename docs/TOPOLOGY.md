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

**AND A SAVE USED TO WAIT FOR ONE, ON THE THREAD THAT PAINTS.** Until
2026-09-01 `_write_or_drop_the_topology` built a topology
synchronously inside the write, where the file already carried a motif
whose design had moved. Measured that day, both arms in one run: on
`hex-colouring 7` the save took 27.53s of which the build was 27.22,
and a 50 ms heartbeat recorded its longest gap at 27.29s -- the window
went twenty-seven seconds without repainting, buttons down, the bar
frozen on whatever it last said. `laves 3.3.4.3.4` froze for 1.05s,
which is the control that says the instrument moves. The build is
queued off the main thread now and the PRESS waits for it, through the
deferred-save machinery of 2026-08-29.

**AND THE PLUGIN IS NOT WHY IT IS SLOW HERE, WHICH WAS WORTH
MEASURING.** The library's author reports `chavey K` at about 10s and
`hex-colouring 7` at about half that, in a notebook on a MacBook Air
-- not a faster machine than this one. Decomposed on 2026-09-01 at
load 6-7, with QGIS 4.0.3's own Python 3.12.11, shapely 2.1.2 and
numpy 1.26.4:

    design             make_unit   deepcopy   our build   bare Topology   TileUnit direct
    laves 3.3.4.3.4      0.007s     0.000s      0.83s         0.81s           0.855s
    hex-colouring 7      0.043s     0.000s     21.23s        23.11s          21.291s
    chavey K             0.013s     0.000s     17.03s        14.35s          14.510s

Our wrapper costs nothing: the deepcopy and the CRS strip are
unmeasurable, and `topology_edits.build` reads the same as a bare
`Topology(unit, True)` within the noise, in both directions. Nor is it
`catalog.make_unit`: built the way a NOTEBOOK builds it, straight
through `TileUnit(**spec)` with the library's own defaults, the times
are the same again. The cost is `Topology.__init__` in this
environment.

**THE ORDERING IS INVERTED, AND NO MACHINE EXPLAINS THAT.** He has
chavey K the dearer of the two, at 10s against about 5; we have it the
cheaper, at 14.5 against 21. A slower interpreter scales both and
keeps the order. So at least part of the gap is a difference in the
LIBRARY rather than in the hardware -- his own rewrite of
`topology.py` was +179/-207 -- or in what his timing covers, since
`Topology.__init__` runs `generate_dual()` eagerly and a cell timing
only the constructor would not show it.

**AND THAT READING WAS RIGHT: IT IS THE LIBRARY, MEASURED 2026-09-01.**
The maintainer supplied the fact that made it separable -- he is on
shapely 2.0.6 and numpy 2.4.4 where QGIS 4.0.3 bundles shapely 2.1.2
and numpy 1.26.4 -- so there were three candidate causes rather than
one, and five arms of `tools/probes/what_a_topology_build_costs_
upstream.py` take them apart. Each arm times ONE checkout under ONE
set of dependencies, three runs per design, sequentially on an idle
machine, and asserts that the library which answered is the one named
on its command line.

    library                interpreter / numpy    hex-col 7   chavey K
    our vendor             3.12.11 / 1.26.4         18.79       13.24
    upstream main, clean   3.12.11 / 1.26.4         18.88       13.26
    upstream experimental  3.12.11 / 1.26.4          9.47       10.08
    our vendor             3.14.6  / 2.5.1          10.18        8.33
    upstream experimental  3.14.6  / 2.5.1           4.87        6.47

THREE THINGS FALL OUT, each from a pair differing in one thing.
OUR PATCHES COST NOTHING: our vendor against a clean upstream main on
the same interpreter is 18.79 against 18.88 and 13.24 against 13.26,
so the matplotlib-optional family and the pandas idiom are not on this
path. THE INTERPRETER AND NUMPY TOGETHER ROUGHLY HALVE BOTH and KEEP
THE ORDER -- 18.79 to 10.18, 13.24 to 8.33 -- which is exactly what a
faster machine would do and is why hardware could never have explained
the inversion. AND THE EXPERIMENTAL BRANCH INVERTS IT, on either
interpreter: 18.88 to 9.47 while chavey K barely moves, so
`hex-colouring 7` becomes the CHEAPER of the two. Upstream's own
commit message for `1961b6a` says "Topology construction - now a bit
quicker", and it means it.

SO THE ANSWER IS THAT HE IS RUNNING A DIFFERENT LIBRARY, not a
different machine and not a different wrapper. Arm five -- the branch
on the newer stack -- gives chavey K 6.47 and hex-colouring 7 4.87
against his report of about 10 and about half that: the same ordering,
his hex-colouring figure almost exactly, and chavey K faster here,
which both his shapely 2.0.6 and an Air would push the other way.
WHAT IS STILL OPEN is the smaller of the two questions owed him --
whether his timing covers `generate_dual`, which the constructor runs
eagerly -- and it now matters less, since the ordering it was offered
to explain is explained.

**AND WHAT A RE-VENDOR WOULD BUY IS MEASURED RATHER THAN HOPED.**
Under QGIS's own python, which is the configuration the plugin
actually gets, the branch takes `hex-colouring 7` from 18.9s to 9.5s.
That is a factor of two on the worst design in the catalogue -- the
one this document and the symmetry note both single out -- for no
change of ours. It is not a reason to take an unmerged branch: it
carries a revert saying a change to the potential-symmetries listing
"broke topology construction for some tilings", and its own first
commit says the plugin can ignore it until it merges. It is a reason
to take it the day it merges, and to re-run these five arms then.

What does NOT turn on the answer is the shape of the defect the
deferral cures: a build whose cost nobody bounds, inside a write, on
the thread that paints.

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

## The instruments, and what each answers

All committed under `tools/probes/`, because the one that names a
defect is the one that names the next. Run each with the checkout on
the path:

    PYTHONUNBUFFERED=1 QT_QPA_PLATFORM=offscreen "$QGIS_PY" <probe>

    does_every_topology_interaction_work   every modality driven
      through the widget's own mouse events, reporting which of four
      stores moved -- the selection, the drawing, the design, the
      record. A row that moves the design and not the drawing is the
      fault of 2026-08-31; a row that moves nothing is a dead control.
    can_edits_chain_without_rebuilding     rebuild-between against
      chained, on the sequences that tell them apart.
    can_a_vertex_edit_be_seen_at_all       what the vertex controls can
      express at their maximum, against the design's own span.
    how_far_would_the_highlight_sit_from_the_ink   what each
      manipulation moves, at one control step and at four.
    do_edited_labels_still_mean_the_same_thing     what a rebuild from
      an edited unit does to the class labels.
    does_the_tab_show_what_it_knows        the ghost, the gap geometry
      and the change list's marks, read off the widget.
    draw_the_handles                       renders the drawing with an
      edge and then a vertex held, and writes the pixels out, because
      "perceivable" is a visual claim.
    can_a_topology_edit_survive_an_inset   whether an inset refuses a
      topology, whether editing the plain unit and insetting the
      result works, and whether a tear stays visible once an inset has
      opened gaps of its own. Three arms; the third carries the number
      the validity ruling turns on.
    the_re_vendor_moved_no_map             two checkouts compared
      design by design, which is the only thing that asks whether a
      re-vendor moved what the library DRAWS.

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

## Making the interaction perceivable

The maintainer's standard, 2026-08-31: it "should be easy to use and
easy to learn for users", it "has to be perceivable", and "hover states
aren't as good as shapes that make sense ... like visually make sense
for what they do".

**THE VIEW WAS FITTING THE PATCH AND NOT THE UNIT**, and that was the
largest single cost to perceivability. `topology.tiles` is the unit AND
its neighbouring copies — 36 tiles for a four-tile design on laves
3.3.4.3.4 — so the thing being edited was drawn at about a third of the
size the panel could give it. Every class label overlapped its
neighbour and the handles arrived as a cluster of rings a few pixels
across. It fits the unit's own tiles now (`n_tiles`, the library's own
count) and lets the copies run off the edges, which is what context is
for.

**THE HANDLES ARE PICTURES OF WHAT THEY DO.** They were a square, a
circle and a diamond, whose meanings existed only in the code. A hover
label was the obvious repair and is the wrong one: a hover has to be
discovered before it can teach anything, and a first-time reader never
hovers. So each handle is drawn as a small glyph of its own effect — a
double-headed arrow ALONG the edge for stretch, a curved arrow for
turn, a wave for zigzag, a four-way cross for a vertex — on a white-
rimmed seat, because a mark that competes with vertex and edge labels
on a crowded drawing is a mark nobody finds. Twelve pixels rather than
eight, since the glyph is the point.

**EVERY MANIPULATION IS REACHABLE ON THE DRAWING**, which was the
maintainer's next sentence — "all interactions in that topology image,
not just one". An edge carries three handles and a vertex carried one:
`push_vertex` existed only behind the chooser and the Apply button, so
one of the five things the tab can do was absent from the thing it does
them on. A vertex now carries two, and they LOOK like the different
gestures they are — a nudge is free and two-dimensional, a push runs
along the one direction the design chooses, so the push handle sits on
a drawn RAIL. Where the design gives it nowhere to go there is no
handle at all: on `laves 3.3.4.3.4` and `hex-slice 3` the incident
edges are symmetric and the unit vectors cancel to 1.5e-9, so the
control genuinely cannot move that design, and a handle that looks live
and does nothing is worse than an absent one.

**AND THE TEST FOR "NOWHERE TO GO" BELONGS IN UNIT COORDINATES.** The
first version asked whether the rail was at least a pixel long on
screen, which called a working control dead: `push_d = 1.0` returns
0.414 unit coordinates on archimedean 4.8.8, and at the zoom the panel
uses that is half a pixel. Asked of the vector itself, the two answers
are 0.414 against 1.5e-9 — nine orders apart, with nothing to tune.

**AND A HANDLE IS A POSITION, NOT A DISTANCE TRAVELLED.** Turning
travel into a parameter needs a LEVER, and a lever is a gain factor
nobody can see, so it can only be tuned by guessing — and it was wrong
twice: half the edge's length made a 34px drag invert the edge, and the
full length still turned a 35px drag into a scale factor of 0.28. The
end handle starts half a length from the edge's middle, so where the
pointer has taken it IS a polar coordinate about that middle: the scale
factor is how much further out it sits, the rotation is the angle it
now makes. Nothing to tune, the edge follows the pointer exactly, and
the handle doubles as a readout because it already sits where the
current value puts it.

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
7. **The interaction must be easy to use and easy to learn, and it has
   to be perceivable** — and "hover states aren't as good as shapes
   that make sense ... like visually make sense for what they do".
8. **Every manipulation is reachable on the drawing**, not just one.

## What was NOT taken from the audit, and why

The audit of 2026-08-30 recorded two designs. The first — a handle is a
POSITION rather than a delta — is built, and its reasoning is above.

**THE SECOND IS DELIBERATELY NOT BUILT.** It proposed merging scale and
rotate into ONE end handle, on the ground that moving an endpoint is
exactly (angle, length) in polar coordinates about the midpoint, which
would remove a handle and the crowding with it. That is true, and it
loses something the maintainer's later standard makes decisive: one
handle would then have to say TWO things, and the whole reason the
glyphs work is that each is a picture of a single effect. A drag on a
merged handle would also record two edits from one gesture, which is
honest but makes the change list harder to read back and harder to roll
back through.

So the crowding was answered the other way, by giving the handles room:
the view fits the unit rather than the patch, the seats are 12px, and
the three edge handles sit at 0 and 30 pixels of perpendicular offset
rather than 0 and 16. If the merged handle is ever wanted, this is the
argument it has to beat.

## Reachable at realistic sizes, and what carried it

The maintainer asked that everything be clickable at realistic sizes,
"maybe that means making the window a little larger by default". Two
things were wrong and neither could be seen from the source.

THE DRAWING HAD 180px OF AN 825px WINDOW. The view's floor was 180 and
the column of controls beside it takes its own preferred width, so the
floor was not a floor but the whole allowance: the thing this tab
exists to edit was drawn at a fifth of the window it sits in. Raising
it to 420 without giving the control column a floor of its own MOVED
THE COMPLAINT rather than answering it, and measurably so -- 71px of
viewport for content wanting 271. The horizontal scrollbar is
deliberately off, so a column narrower than its content does not
scroll, it CLIPS.

TWO HANDLES CLOSER THAN TWICE THE REACH MAKE ONE UNREACHABLE
EVERYWHERE, not merely fiddly, because the hit test returns the first
within reach and the order is fixed. Rotate and zigzag are pushed along
the same normal from an edge's end and its middle, so at equal offsets
their separation is HALF THE EDGE'S SCREEN LENGTH: 20.4px inside a 26px
reach on two designs of three, costing 23 edges apiece their zigzag
handle. They stand at different offsets now, which makes the separation
hypotenuse(half the length, 30) instead.

PUTTING THE ZIGZAG ON THE OTHER SIDE WAS TRIED FIRST AND IS WORSE. A
negative offset separates it from rotate just as well and lands it
where the VERTICES are -- and handles are tested before vertices, so
while an edge was held the vertex under that handle could not be
clicked at all. The interaction matrix caught it within minutes, which
is the second time that test has paid for itself in a day.

### Why no entry stands on the separation

Four attempts to make one bite, and the fourth measurement is the
answer rather than a fifth attempt. Both fixes bear on the same
outcome and EITHER ALONE IS SUFFICIENT, so a tool that applies one
replacement cannot make the assertion fail. As the worst
rotate-to-zigzag gap against the 26px needed: as it stands 41.5px;
with the offsets matched but the floor kept, 28.7px; with the floor
removed but the offsets kept, 32.7px; with both undone, 12.9px. The
sites are ninety lines apart, so no anchor spans them, and the honest
record is the measurement written at the test. The figure to watch is
28.7 -- the offsets are headroom on a margin of 2.7px.

### A widget inside a layout does not keep a size you give it

Three of those four attempts failed on this alone. Resizing the view
to its own floor is undone on the next layout pass, because the layout
hands it whatever is left over; the WINDOW is the lever, and the
window's own minimum is what pins the drawing in practice -- measured
at 1025x450, below which it will not go, holding the view at 420x346
however small a size it is asked for.

And the sweep looking for the design with the shortest drawn edges
returned 68.9px for ten designs in a row, which is this project's own
rule arriving again: a uniform verdict is almost always the
instrument, and it was not worth debugging once the question had been
answered another way.

## What a drag means, settled 2026-09-01

Four faults in one gesture, found by three hunts and repaired the same
day. They are listed together because each was invisible while the
others stood.

**The preview and the commit disagreed by the span of the unit.**
`in_map_units` had one caller, in `apply`, so the commit converted a
recorded fraction into map units and the preview did not: 70.71 map
units against 0.10 on laves 3.3.4.3.4 at a tenth of the unit. Nothing
seemed to happen while dragging, and the design jumped on release.

**The view and the model divided by different spans.** The view used
the unit's WIDTH where the model uses `max(width, height)`, which is
1.268x on laves and exactly 1.000x on a square unit, so every design
tried by hand hid it.

**The frame moved under the gesture.** `_fit` re-measures the drawn
extent at every paint, and during a drag the drawn thing is the
preview, so the transform became an output of what the drag was
changing. Held still through six repaints, a recorded nudge climbed
0.104, 0.207, 0.280, 0.318, 0.342, 0.356 while the scale fell 0.6138
to 0.5541. It is frozen for the length of a gesture and resumes at the
drop.

**And a dragged value escaped its own control.** Both vertex branches
assigned it straight into the record where the edge branch clamps, so
a drag past the range recorded a number its box would not show.

**Which design a claim is driven on decides whether it can be seen.**
The clamp shows on `archimedean 4.8.8` and not on laves, where the
library refuses an oversized nudge first; the frame drift shows when a
VERTEX is held and not when an EDGE is scaled, since only the first
grows the extent the fit re-measures. Both first probes came back
clean.

## The dual repeats on whatever lattice the tileable has

`_lattice_offsets` read `vectors` by the keys `(1, 0)` and `(0, 1)`.
A hex tileable keys the same dictionary by three-element coordinates,
so both lookups missed and the fallback drew the dual once, in the
middle of a field of tiles it does not cover, on every hex-keyed
family. It now takes the two shortest non-parallel translations out of
the values, which does not care how they are named: hex-slice 6 goes
from one position to nine, and laves, hex-colouring 4 and
square-colouring 5 are unmoved at nine, which is the control that says
the change did not simply make every answer nine.

## The dual, completed, and the two library defects behind its holes

Field report 5 against rc15 said "Map the dual" gave an error while
the tab drew the dual perfectly well. Driven on 2026-09-05 (probes
`dev/probes/fr5_*`, arms A to M; the measurements are R-79 in
ROADMAP-archived.md), the box asked the tab for a topology OF the dual
and the library refused; and the map itself had holes. Two defects in
the vendored library, measured on the default design:

    generate_dual holds        6 dual tiles (one per vertex)
    get_dual_tiles returns     4 rows   -- labelled with the SOURCE's
                                          tile ids sliced to the count
    those 4 cover              77% of the cell
    all 6, library centres     99.77%  -- polylabel run per copy lands
                                          about a unit apart, slivers
                                          along every shared edge
    all 6, consistent centres  100.000000%, and Topology(dual) BUILDS

The library builds the snub-square tiling from its own catalogue
entry, which is what said the refusal was the dual's construction and
not the tiling. `complete_dual` takes each copy's centre as its base
tile's centre translated, and upstream is asked for both fixes in
docs/process/upstream-note-the-dual-is-truncated-and-drifts.md.

The box became a button, "Generate the dual and tile it", landing the
dual in `<group> — dual`; the rulings are in CLAUDE.md and the
mechanism in MAINTAINING.md. And a design's gaps are a different
question from the dual's: insets are already built before, and a
weave's strand width is baked into strand construction, which is the
R-40 boundary.

## Duals chain, and the way back is the chooser

A press on a dual's own group used to be refused, the store being a
boolean that could not say "twice" and a second press having landed
a byte-identical copy of the first dual under `-- dual -- dual`. The
maintainer ruled on 2026-09-06 that duals chain. The record carries
one frozen edit list per dualisation, the build applies each level's
edits and takes the dual once per level, and the shelf key, the
topology stamp and both signatures carry the DEPTH rather than the
box. Measured on the default design: `laves 3.3.4.3.4` dualises to
the snub square and back to the Cairo tiling, congruent tile for
tile (four pentagons of 62500, edges 149.4 and 204.1) and displaced
by 63 units, so a second press is a round trip there; on an edited
design it is not, since the dual straightens a zigzag edge. The way
back to any earlier geometry is that geometry's own group in the
chooser, which a dual press leaves untouched; a dual group's own
topology edits shelve one level deeper and are what the next dual is
taken of. Two faults in the first build are in C-334: the unit
is rebuilt by the box's toggle, which a second press never fires, and
a depth marker in the edit key deferred the press.

## The crest is half of h, and the picture said otherwise until round eight

The library's `zigzag_between_points` scales its sine by `h * r / 2`:
`h` is the wave's peak-to-peak width as a fraction of the edge, so the
crest sits `h / 2` of the edge's length out on either side. Rulings 1,
3 and 5 put the handle on the first peak and ghosted the wave through
it, and both were drawn at the WHOLE of `h` -- agreeing with each
other, held to that by a test, and agreeing with nothing the map
received. Measured 2026-09-06 by driving the tab through its boxes
and Apply and then reading the edited unit's own polygon: on the
default design at h=0.4 the handle sat 0.400 of the edge out and the
unit's crest was 0.190 of it. `_CREST_OF_H` in topology_tab.py is the
one scale now, read by the handle, the ghost, the drag's inverse and
the amplitude deadband, and a differential test takes the library's
own crest as the oracle. The default smoothness (3) samples the sine
about 5% short of its peak; the picture draws the true peak and that
difference is left to the map. Found by round eight's specification
hunt, which asked whether a settled rule was true of the dependency
it cites rather than whether code obeyed the rule (C-320). And the
SIDE was wrong as well as the size: the screen normal the handle and
the ghost stood on was the mirror of the library's first lobe once
the view's y-flip is counted, found the same morning by the hunt
aimed at the crest repair, whose differential compared absolute
values and could not see it; the normal is `(rise, -run)` now and the
differential asserts the signed first lobe through the flip (C-324).
And since the evening of 2026-09-06 the Amplitude box SHOWS the
crest's distance while holding `h`: the maintainer chose the box
that converts on its face over one that changes what every saved
record's `h` means (C-337).

## The general audit of 2026-09-05, and what it found

The maintainer asked, after field report 5, that the tab be audited
"more generally to make sure it functions as expected". The shape of
the audit is the thing worth keeping: every control and every handle
driven on the packaged Auckland data in the order a person meets them,
with LIVE UPDATE AT ITS DEFAULT, and about twenty stores read after
every act -- the selection owner, the class combo, the tick list, the
drawing's chosen thing, the verb chooser and its boxes, the edit list
and its marks, the note and the working sentence, the symmetry line,
the dual button and its label, both live-update boxes, the shelf, the
panel's drawn unit, the dialog's unit and the map's own digest. The
probes are `tools/probes/audit_the_topology_tab_as_a_person_meets_it.py`
and its second and third passes beside it, with `tab_audit_kit.py`
carrying the aimer and the drag; the logs are under `dev/audit-logs/`.

**Three defects, all invisible to reading and to the three matrices
that drive this tab.**

THE ZIGZAG'S AMPLITUDE WAS A DELTA WHERE ITS COUNT WAS A POSITION.
`_drag_argument` computed `h` as the drag's travel across the edge
divided by its length, while the count beside it was computed from
where the handle sat. Driven: typed 0.3, one pixel along the edge
previewed 0.010; eight pixels along -- the gesture that steps the
count -- recorded n 1 and h 0.01; five pixels further out recorded
0.07 rather than 0.37. The handle's own position is `-h * length` on
the unit-space normal (the view takes its normal in screen space,
where y points down), so `h` is now `|-h * length + across| / length`,
and the same arms read 0.300, 0.300 with n 1, 0.373 and 0.184.

A ZIGZAG'S CORNERS WERE SELECTABLE AS A VERTEX OF NO CLASS. One zigzag
at n=2 with smoothness 3 takes the default design from 72 points to
279, and the 207 new ones carry no label. `_nearest` offered them
like any vertex and the painter drew a seat on each, so a click on one
put the selection at `("vertex", "")`: the chooser grew a row reading
"0 of 2 vertex classes", nothing was ticked, no handle appeared and
Apply returned in silence. Both now skip a point with no label, and
the click falls through to the edge the corner lies on.

THE DUAL'S SYMMETRY CHANGED WITH THE SPACING. The first pass saw the
dual group's topology carry ten edge classes, four vertex classes,
`C1` on every tile and no symmetries at a spacing of 2900; the third
pass, at 3000, saw three, one, `D4` on the squares and four rotation
centres. Built directly across spacings
(`dev/probes/audit_dual_symmetry_by_spacing.py`):

    spacing    edge classes   vertex classes   rotations   mirrors
    500        3              1                4           0
    1000       3              1                2           4
    2900       10             4                0           0
    3000       3              1                4           0
    5000       3              1                4           0

The dual's corners are the source tiles' centres, and the library's
`Tile.centre` is `polylabel` at its default tolerance of one map unit,
so each of the four base tiles carried noise of about half a per cent
of the spacing and the noise differed between them.
`dev/probes/audit_dual_centre_options.py` tried three centres across
the same spacings: the library's, the centroid, and polylabel at one
part in a thousand million of the tile's own size. Both alternatives
give ONE answer at every spacing -- two edge classes, one vertex
class, four rotations, eight mirrors, which is the class structure of
the catalogue's own `archimedean 3.3.4.3.4` -- and only the relative
polylabel gives equilateral triangles (`D3`), the centroid giving
isosceles ones (`D1`), because the Cairo pentagon's centroid is not its
incentre. `_exact_centre` keeps the library's choice of the incentre
and changes only its precision. Guarded by the dual differential,
which now asks the two spacings that disagreed to agree with each
other and with the catalogue's snub square.

**Two things measured and reported, and settled by the grilling later
the same day** (maintainer's decisions, 2026-09-05): the count box
offers EVEN COUNTS ONLY, 2 to 8, a typed odd count settling up to the
next even one, on the library's own word; and the readout's clamp
stands, the box carrying the count past where the drag is exact. A
third decision from the same grilling sized the amplitude's click
threshold from the glyph -- half a 12px seat of travel from where the
handle was grabbed -- since 1% of the edge's length was under a pixel
on the edges below, so a click that slipped a pixel recorded an
invisible wave and rebuilt the topology.

AN ODD ZIGZAG COUNT OPENS A GAP, on one class and not the other:

    class a   n=1..5   gap 1e-11 throughout, sound
    class b   n=1      0.63%   not sound
              n=2      1e-11   sound
              n=3      0.40%   not sound
              n=4      1e-11   sound
              n=5      0.35%   not sound

The library's `zigzag_edge` says in its own docstring that it "will
only work correctly if n is even", the `start` parameter being "a
temporary hack" toward odd counts. The tab reports it honestly -- the
row reads "from here the tiles no longer meet" and the mark agrees
before and after a Save and Load -- so this is ruling 5 working
(validity shown rather than enforced). Since the grilling the box no
longer offers an odd count; a record carrying one from before is still
applied, and still reported.

THE COUNT READOUT'S CLAMP BITES AT THE WINDOW'S OWN SIZE. The zigzag
handle sits on the first peak, `length / (2n)` along, and is held 15px
clear of the vertices, so above some count it stops moving with the
count and the box's tooltip says so (ruling 4). On the default design
at the window's floor of about 1034x458 the two edge classes draw at
94px and 69px, and the readout is exact only to n=3 and n=2; at
1500x950 they draw at 236px and 173px, exact to n=7 and n=5. Ruling 6
asked that everything be reachable at realistic sizes; this is the
measurement of where the tab stands.

SETTLED ON 2026-09-06 BY INTERPOLATING THE COUNT. The specification
hunt measured the stops against the deadband -- from four the next
lay 0.042 and 0.021 of the edge away against a deadband of 0.10, so
four and six could be typed and never dragged to -- and the
maintainer ruled that the handle's place along the edge interpolates
the even counts between two seats, 0.25 and 0.60 of the edge, two on
its own first crest and eight clear of the end handles (a first form
reached 0.85 and met the scale handle at the window's floor). The
stops are 0.117 of the edge apart, every count
is one drag away, and the clamp above bites only on an edge too short
for the seats. The handle no longer sits on the first crest; the
ghost still does, at the library's pitch (C-336).

**What the audit found sound**, kept so the next one need not redo
it: a click on a vertex or an edge moves the owner, the combo, the
list and the drawing together and changes no verb of the wrong kind;
shift-click and the tick list add and remove classes and refuse to
empty the selection; every combo row moves the other three stores;
each verb shows its own boxes, remembers its numbers across a verb
change and across a landing; every handle previews while the pointer
is down, records at the drop, keeps its picture until the landing,
and moves the drawn unit, the dialog's unit and the map together with
one mark per edit and the shelf in step; Apply records what was typed
with its alphabet; Undo and Clear return the unit and the map to the
pre-edit digest exactly; the eight toggles move the view's own flags;
the two live-update boxes move each other; with live update off an
Apply moves the drawing and not the map and Generate then draws it;
the dual button lands `<group> — dual` with its label, its own shelf
key and its own edits, and the source comes back untouched; and a
Save carries the unit, the dual and the edit list into the file, from
which a fresh dialog loads the edited design with the same mark.

## Rotating and scaling an edge without tearing the tiling

The library's `rotate_edge` and `scale_edge` move an edge's endpoints
about its own midpoint and write the shared vertices back
last-write-wins, which pulls the units apart: measured 2026-09-07, the
per-edge result builds no topology on `laves 3.3.4.3.4`, `archimedean
4.8.8` or either `hex-slice` design. The plugin reroutes both through
`topology_edits._move_edges_vertex_consistent`, which moves each shared
vertex once, by a single lattice-periodic displacement, so the tiling
stays edge-to-edge. Where a design's symmetry forces that displacement
to zero the edit correctly moves nothing and names the symmetry, since
the per-edge move there is a torn non-tiling rather than a rotation.

The change also exposed a blind spot in `gaps()`, which finds only holes
enclosed within a patch and so called a per-edge rotate of hex-slice 3
sound while its units had separated. `plane_coverage` measures the
coverage of one fundamental cell instead, catching a gap that opens onto
the surrounding space as readily as an enclosed one; the soundness mark
and the validity hatch read it now.

The whole investigation, with the alternatives weighed (the library's
per-edge move, a per-edge move whose slivers are absorbed into
neighbours, and the vertex-consistent move), the measurement that
reframed it, and the images, is in
`docs/process/rotating-and-scaling-an-edge-without-tearing-the-tiling.md`.
It ships in the experimental tab as a candidate for testing, and may yet
be reshaped.

## How deep a zigzag an edge can carry, and what the search costs

Measured 2026-09-07, driving `topology_edits` in the reference venv with
no QGIS in the way. The ceiling is the largest `h` that still lays out,
found by bisection against the same two steps `apply` takes -- the
transform, then `_make_drawable` -- so it cannot disagree with the
refusal it replaces.

    n=2   class a   h 1.172 (crest 0.586)   class b   none in range
    n=4   class a   h 0.594 (crest 0.297)   class b   none in range
    n=6   class a   h 0.422 (crest 0.211)   class b   none in range

IT TIGHTENS WITH THE COUNT rather than being a property of the class
alone, which is why a ceiling cached per class would be wrong: the key
is class, count and smoothness together.

WHAT THE SEARCH COSTS, and it is what decides where the clamp may run:
0.07 s where the cap lays out and one probe settles it, up to 1.40 s
where it must bisect eight times. Against that, ONE DRAG FRAME ALREADY
COSTS 158 ms for its transform and one probe 161 ms, since a probe IS
that transform plus a cheap repair -- so the live drag holds the last
value that laid out and computes no ceiling at all, while the commit
pays the bisection only on an edit that would otherwise be lost.

AND THE PREMISE THE CLAMP WAS FIRST ARGUED FROM WAS FALSE. It was put
to the maintainer that an over-deep wave leaves a self-intersecting
tile which `make_valid` silently rewrites. The raw tiles are VALID at
every amplitude on both classes; what happens past the limit is a clean
refusal with the design untouched. The clamp replaces a refusal rather
than preventing a corruption (C-342).

## What a tear looks like, and why a hull will not measure it

`plane_coverage` decides whether a tiling has torn by measuring ONE
fundamental cell, which is enough to decide and not enough to draw:
on a per-edge rotate of the default design it is 4 pieces of ground
against the 21 that are actually torn. `tears_in_the_patch` answers the
wider question at the same cost, 8.1 ms against 9.0, because the patch
is already laid to measure the single cell.

A HULL IS THE TRAP, and the first version fell into it. Taking the
covered union's convex hull, eroding it by one cell and subtracting
reported 1,000,000 units of tear on an UNTOUCHED `laves 3.3.4.3.4` --
exactly one cell's worth -- because a patch is a finite piece of an
infinite tiling and its outer edge is ragged, so the space between the
outermost tiles and any hull round them is not damage. Hatching it
paints a sound design as broken at its border. A block of whole
fundamental cells is interior BY CONSTRUCTION: no boundary to erode,
nothing to tune. Its guard asserts both halves, that a sound design
hatches nothing and a torn one hatches more than one cell shows.

## A stall caught live, and what it ruled out

Sampled 2026-09-07 while a single test sat at 15 s of CPU in 162 s of
elapsed at 0%, using `sample <pid>`, which takes every thread's stack
and disturbs nothing -- SIGUSR1 would have killed `run_some` outright
for want of a faulthandler. Four threads:

    main                  QEventLoop::exec, inside the suite's own wait
    NSEventThread         idle
    two pool threads      start_wqthread -> __workq_kernreturn, parked

SO NO WORKER WAS EXECUTING ANYTHING, and the main thread was blocked in
a wait that was legitimate for something that never arrived. It does
NOT separate "QGIS never started it" from "it finished and was never
handed back", since both look identical from outside; that is what
`TilingTask.where_the_work_got_to()` is for, and reading it needs to be
inside the process. It did not reproduce on CI, which is consistent
with everything else known about this fault.

AND ONE INFERENCE HAD TO BE WITHDRAWN. The sample shows a single
`_PyEval_EvalFrameDefault` frame, which reads as a shallow Python
stack and is not: CPython 3.12 does not take a C frame for a
Python-to-Python call, so one such frame hides a stack of any depth. A
native sample says WHERE a process is blocked and never WHO called it.

## What round nine measured, 2026-09-07 (night)

Twelve defects closed in one round of hunts, all in the tab and all in
work of the previous two days. The ledger is
`docs/process/defects-2026-09-07.md`; what belongs here is the
evidence, since this document is what the next person opens when they
want the numbers rather than the story.

**THE PREVIEW DREW A DIFFERENT MOVE FROM THE ONE THE DROP MADE.**
C-341 reformulated `rotate_edge` and `scale_edge` to move each shared
vertex once; that went into `apply` alone, and three callers must
agree with it. On `laves 3.3.4.3.4` class `a`, one fundamental cell:

    edit                    the preview drew        the drop records
    rotate_edge  15 deg     gap 1.7785% ovl 0.222%  gap 0% ovl 0%
    rotate_edge  60 deg     RAISED GEOSException    gap 0% ovl 0%
    scale_edge   sf 1.5     gap 0.8911% ovl 8.216%  gap 0% ovl 0%
    zigzag_edge  (CONTROL)  gap 0%      ovl 0%      gap 0% ovl 0%

The control is what makes the rest readable: zigzag is not rerouted,
so both routes are the same call there and agree.
`move_as_applied` is the one owner now.

**THE GHOST DREW TWICE THE WAVE'S FREQUENCY.**
`zigzag_between_points` samples a sine at `n*pi` over `2n+1` points,
so it crests at the ODD multiples of `length/(2n)` and crosses ZERO at
the even ones. The ghost put a full-amplitude point at every multiple:
2n-1 lobes, and at the default n=2 a trailing lobe on the wrong side.
At h=0.4 it drew `(.25,+.2)(.50,-.2)(.75,+.2)` where the map gets
`(.25,+.2)(.50,0)(.75,-.2)`. Corrected, the two agree exactly at n=2
and n=4 in position and sign.

**THE PUSH RAIL CARRIED A GAIN NOBODY COULD SEE, and it took three
repairs to remove.** `push_vertex` returns `push_d` times the sum of
the unit vectors at the vertex, whose length belongs to the vertex:

    design                push 0.1 moves   nudge 0.1 moves   ratio
    archimedean 4.8.8            0.0536            0.1293   0.4142
    laves 3.3.4.3.4              0.0000            0.1414   0.0000
    hex-slice 3                  0.0000            0.1155   0.0000

The zeroes are the symmetry the rail already suppresses. `push_d` is a
DISTANCE by ruling, so the drag divides by that gain -- and the gain
must be measured on ONE store: read live it fell 0.4142, 0.3827,
0.3470, 0.3138, 0.2660, 0.2001, 0.1029 over seven frames as the
preview moved the neighbours; frozen at the press but taken off the
preview, a second drag after a landing-free pause read 0.2143; and
taken off the held design while the VERTEX stayed on the preview,
0.0884 where a landing between gave 0.1495. `push_vertex` reads the
vertex's point from its ARGUMENT and its neighbours from the
TOPOLOGY, so both halves must come from one store.

**A DUPLICATED PATCH TILE MADE FIVE SOUND DESIGNS READ AS BROKEN.**
`plane_coverage`'s overlap term is summed tile area minus the union's,
which cannot tell two tiles from one counted twice, and
`get_local_patch` hands the same tile back twice on `square-colouring
3` and `chavey H`, `I`, `J`, `K` -- 5 of 1,168. Untouched,
`square-colouring 3` read overlap 0.2222 and `still_has_a_topology`
False. Deduplicated by exact geometry it reads 0.00000000.

**AND THE ONLY DESIGNS THAT LEGITIMATELY DO NOT TILE ARE `grid N` AT
HIGH COUNTS.** A sweep of all 1,168 at spacing 1000 found 18 of them
with a genuine gap of 0.004 to 0.059 and no duplicated tiles -- the
grid extra leaving a remainder, which the tab reports honestly.

**WHAT PATCH RADIUS THE TEAR-FINDER NEEDS, and why it is asked rather
than computed.** The block of cells must lie inside the patch or its
corners hang over ground with no tiles and are hatched as damage:

    design               needs r   block half-diag   lattice step
    laves 3.3.4.3.4            2            2121.3         1000.0
    archimedean 4.8.8          2            2121.3         1000.0
    hex-colouring 4            2            1500.0         1000.0
    hex-slice 3                3            2598.1         1000.0
    hex-slice 6                3            2598.1         1000.0
    square-colouring 3         3            2598.1          816.5
    chavey H, I, J, K          5            2598.1         1000.0

`hex-slice 3` and `chavey H` share a lattice, a cell AND a block and
need 3 and 5, so nothing here predicts it. The patch is asked whether
it holds the block and grows until it does, tested against its own
outline with the holes filled -- a tear is a hole INSIDE that outline,
while ground beyond it is where the patch stopped.

**AND THE HATCH IS NO LONGER FREE.** It lays its own patches now, one
per radius tried: 9.5 ms on `laves 3.3.4.3.4`, 138 ms on `hex-slice
3`, 133 ms on `chavey H`, measured on designs torn by a per-edge
rotate, which is the only case that reaches it -- once per landing,
on the branch where the coverage figure has already said the design is
torn.

## An inset takes the tab away, and it need not: measured 2026-09-08

`Topology` needs a gap-free tiling, so a tile or group inset refuses
the tab outright. THE INSETS ARE THE LAST TWO STEPS OF `_build_unit`'s
chain -- `make_unit`, rotate, scale, skew, `inset_tiles`,
`inset_prototile` -- and every step before them preserves the tiling,
so the un-inset design is one call back rather than lost. The
instrument is `tools/probes/can_a_topology_edit_survive_an_inset.py`,
driven in `.venv-reference` with no QGIS in the way, and it takes no
timings deliberately: the candidate's suite held the machine, and a
structural answer is honest under contention where a timing is not.

Today's refusal reproduces at 1% and 5% tile inset on `laves
3.3.4.3.4`, `archimedean 4.8.8` and `hex-slice 3`. Editing the PLAIN
unit and insetting the result works on all three, across zigzag,
rotate and nudge, at 1% and 5% tile inset and 1%, 5% and 10% group
inset: no empty tile, no invalid geometry, areas falling with the
inset as they should. Zigzag was the case expected to shatter, an
inset being a negative buffer and a zigzagged tile concave; it does
not.

**AND THE VALIDITY JUDGEMENT MUST RUN ON THE SKELETON**, which is
arithmetic rather than taste. On `laves 3.3.4.3.4` class `b`, the
class the audit's table says tears on an odd count:

    state                          gap of one cell
    zigzag n=2 skeleton (sound)           0.000000
       + inset 1%                         0.077946
       + inset 5%                         0.358133
    zigzag n=3 skeleton (TORN)            0.010781
       + inset 1%                         0.088401
       + inset 5%                         0.370981

The tear's own contribution is CONSERVED at about 0.011 of a cell
whether or not an inset sits over it, and swamped as a FRACTION: at 5%
a torn design reads 0.371 against a sound design's 0.358. Anything
judging the INSET design against a threshold therefore calls every
inset design catastrophically torn, which is row 5 of round nine
arriving again at scale.

**WEAVES ARE A DIFFERENT PROBLEM.** A plain weave and a twill carry a
topology at aspect 1.0 and neither does at the default 0.75; strand
width is an argument to `make_unit` rather than a transform applied
afterwards, so there is no un-thinned unit to edit and thin later.
That is the R-40 boundary with a measurement under it. A strands code
carrying a hyphen has no topology even at 1.0, the gap being
deliberate.

THE FIRST SWEEP MEASURED NOTHING and is worth the line: it drove class
`a`, where odd counts are sound at every count the table above lists,
so it produced a negative that could not have been positive. Vary the
class as well as the design before believing one.

## A weave has no topology, and what it would take: 2026-09-08

A weave's strands are narrower than their cells, so the design has
gaps and the tab refuses. Three routes through solidity were measured
and all fail -- an inset shortens where thinning lengthens (40% wrong
on `plain weave a|b`), `aspect == 1` fuses same-label pieces so a
twill's 16 tiles become 2, and at aspect 0.999 a millionth of a cell
of gap still refuses. What works is scaffolding the daylight: on
`twill weave a|b` at 0.75, 16 strand tiles plus 16 filler give gap
0.000000 and overlap 0.000000, `Topology` builds with six edge and
four vertex classes, an edit applies, and dropping the filler leaves
the original 16 tiles valid. EVERY FILLER PIECE NEEDS ITS OWN ID:
`_setup_regularised_prototile()` dissolves by `tile_id` and `Topology`
takes corners through `shape.exterior`, so merged filler is a
multi-part tile the library refuses. Sharing one id left `plain weave
a|b` and `twill weave a|b-` failing; with distinct ids all three
build, edit, and give their strand tiles back valid.

AND A CLASS-AIMED EDIT DOES NOT GIVE A RIBBON. The scaffolding abuts a
strand at every crossing, so a long side is four edges on a plain weave
and five on a twill; the two sides share no class at all on a plain
weave, and where they do share one the phase turns on whether that
class's segments sit opposite each other. On one twill, under one
selector: class `c` is aligned and the width swings 0.0% while the
centreline travels 6.3% of the strand's width, and class `b` is
staggered and the width swings 19.0%. A swing of twice the centreline's
travel is one side moving; the constant reading is the exact one, since
two edges displaced by the same graph function leave every chord at the
original width, while a swing is a chord on a fixed axis and reads
slightly wide on a sloped edge.

The instruments are `tools/probes/can_a_weave_carry_a_topology.py` and
`tools/probes/what_a_class_aimed_edit_does_to_a_ribbon.py`. The full
record, the dead ends and what weaving asks of an edit are in
docs/process/weaving-and-topology.md; the rulings are C-347.

## Symmetry, and what a crystallographic reading would give

`docs/process/wallpaper-groups-and-what-we-do.md` sets out what the
transitivity classes we aim edits with actually are, what a wallpaper
group would add, and what the combinatorial encoding crystallography
uses would add beyond that -- with the costs measured rather than
bounded: what we do takes 0.29 to 19.08 seconds across ten designs, a
bounded symmetry enumeration takes 3.6 to 23.8 milliseconds, and
building the combinatorial structure takes under 1.2 milliseconds.

The finding that bears on this tab directly: **site symmetry predicts
which manipulations can move which classes.** A vertex whose
stabiliser contains a rotation has only the zero displacement
available to it, which is why `push_vertex` moves nothing on laves
3.3.4.3.4 and hex-slice 3 and a tenth of the unit on archimedean
4.8.8. That is a rule rather than the arithmetic accident recorded
above it, and it would let a dead control be greyed out with a reason
instead of drawing a rail of zero length. It is necessary and not
sufficient: laves class B has a one-dimensional fixed space and its
own construction still yields nothing.

**And `hex-colouring 7` takes 19.8 seconds to build a topology**,
against the 0.75 to 4.4 seconds recorded above. The cost tracks the
number of distinct shapes and their corners, which this document
already said; nobody had run it far enough up the catalogue to meet a
design where you wait that long before an edit can be aimed.

## A build that lands while you are dragging

Found on 2026-09-01, from CI rather than here. `show_topology` clears
the drag's preview and the chosen thing -- both belong to the topology
being replaced -- so a build finishing under the pointer snapped the
drawing back to the design the person had already moved away from and
dropped the highlight showing what the gesture was aimed at, while the
drop went on to commit the edit anyway.

It reproduces about one run in eight on this machine and failed all
three CI platforms at once, on the drag guard's own premise: "the drag
drew no preview at all", 730 passed and 1 failed on macOS, Linux 4.0.3
and Linux 4.0.0 alike.

**The panel holds a landing until the drop.** Where the gesture
committed an edit the held landing is discarded, because that record
makes the dialog chain and land again within the tick and drawing the
older design first would be a flicker; where it committed nothing,
the held landing is the one that draws. Both halves carry a catalogue
entry, since either alone leaves a tab that either wipes a gesture or
goes on drawing a design the plugin has already replaced.

## What is drawn between the drop and the landing

The section above is about a landing arriving DURING a gesture. This is
the window AFTER it, which none of those repairs touches, and it is
what the maintainer reported against 0.24.4rc15: "it reverts for a
second and then a few seconds later updates correctly".

`_commit_the_drag` opened with `show_preview(None)`, so the edited
geometry was cleared AT THE DROP -- and the rebuild that answers an
edit is asynchronous, so until it landed `_drawn` fell back to
`_topology`, which is the UN-EDITED design. MEASURED on the default
design, `laves 3.3.4.3.4`: the old design stood for **1.676 seconds**,
and the settled drawing's fingerprint was IDENTICAL to what the preview
had been showing -- the right picture was on screen, was thrown away,
and was recomputed. Against the build costs in the first section of
this document, on `hex-colouring 7` that is nineteen seconds of the
wrong design under somebody's hand.

**THE PREVIEW IS KEPT WHERE AN EDIT WAS RECORDED**, and the landing
clears it: `show_topology` sets `_preview = None` as its own third
line, and every route to an answer passes through it. So the preview
stands exactly as long as there is nothing better to draw, which is
what a preview is for.

**AND EVERY PATH THAT RECORDS NOTHING STILL CLEARS AT ONCE.** There no
landing is coming, so a preview left standing draws an edit the change
list denies -- the fault `show_preview` was split from `show_topology`
to prevent. That is why this is a decision per exit rather than one
line moved, and the three exits are three JOURNEYS: a press that never
grabbed anything leaves at the first, a selection the tab cannot act on
at the second, a gesture with no travel at the third. An entry aimed at
the third SURVIVED until the guard grew an arm that walked it, because
its discard arm was a click -- which leaves at the first.

WHAT IS LEFT OPEN DELIBERATELY is a record with no rebuild behind it:
the preview then goes on showing what the person asked for, which
agrees with the change list, where reverting would show a design the
list denies.

## A build the task manager never starts

Measured 2026-09-04, from the topology matrix's one failing cell: "the
tab neither built a topology nor said why not, so somebody is left in
front of a panel that never answers".

    manager: count=1 active=1 'WeavingSpace topology' Queued
    global thread pool: active=0 max=8      <- means nothing; see below
    python threads: ['MainThread']          <- means nothing; see below

**TWO OF THOSE THREE LINES ARE NOT EVIDENCE, MEASURED 2026-09-07.** Put
to QGIS 4.0.3 with a task deliberately held inside `run()`,
`QThreadPool.globalInstance().activeThreadCount()` reads 0 and
`threading.enumerate()` reads `['MainThread']` while that worker is
demonstrably live -- QGIS's task workers do not go through the pool
Python can see, and a foreign Qt thread is not a `threading` thread. A
faulthandler dump DOES see it, two thread blocks against one, so the
dump is the only thread reading here that can tell a running worker from
an absent one. The `Queued` status is what carries the finding below;
the two lines above are kept as the record of what was read, marked so
nobody leans on them again.

The build is QUEUED AND NEVER STARTED. Against the
figures at the top of this document that is not a slow design and not a
worker holding a thread: later dialogs' builds answered in 1.4s on the
same design while that one sat for 133 seconds, and the queued tasks
accumulated.

**THE TAB SAYS SO NOW**, after `TOPOLOGY_START_CEILING_MS`. The
sentence goes in the NOTE, which means "the answer, or why there is
none", so every waiter that reads it gets a real answer instead of
sitting out its ceiling on silence. It asks about STARTING and never
about duration -- a build under way is `Running` however long it takes,
so the nineteen seconds of `hex-colouring 7` cannot reach it -- and it
SAYS rather than cancels, because a pool genuinely busy with another
plugin's work is a legitimate reason to wait and the sentence is still
true there.

**THE CAUSE IS NOT KNOWN.** Four failures in eighty-six attempts here,
clustered in one twenty-minute window and absent from runs of 30, 16
and 12 afterwards, so it is not yet a condition anybody can stage --
which is why the guard is aimed at the STATE the stall leaves, and its
test stages that with a QgsTask never handed to the manager. The
discriminator that would say who owns it rides in
`tools/probes/how_often_a_build_never_starts.py`: at the stall it adds
a second task and reads whether the stuck one then starts. It has not
yet caught one.

## What the tab gained on 2026-09-01

Four features were approved earlier, scoped into 0.24.4 by a grilling
on this date, and built the same day. ROADMAP.md carries the reasoning
and the measurements; what a reader of this document needs is what
each means here. Every one carries a registered test and catalogue
entries proved `caught`.

**Selecting several classes at once.** A modified click -- shift,
control or command -- adds and removes a class on the drawing, and a
tick list beside the chooser confirms the selection, each following
the other. `TopologyPanel._selection` is the one owner; the combo, the
list and the drawing follow it, and Apply, the drag preview and the
drop all ask it. The combo grows one temporary row -- "2 of 3 vertex
classes" -- for a subset it does not list, rather than naming one
class while an edit would move two. The record needs nothing -- an edit's `classes`
is already a string selector, and the library matches `label in
selector` -- and the case is rarer than it sounds: across a 48-design
spread most designs carry one or two classes of each kind, so the
existing per-class entries and the "every" entry already cover every
subset on most of the catalogue.

**Symmetries drawn, and edits gated by them.** `Topology` already
holds `tile_matching_transforms`, and upstream's own plot goes through
matplotlib, which cannot run inside the signed QGIS process on macOS
-- so the drawing is ours, in the view's painter, from upstream's
data. The gate is the finding in
`docs/process/wallpaper-groups-and-what-we-do.md`: a vertex whose
stabiliser contains a rotation has only the zero displacement
available, which is why `push_vertex` moves nothing on laves
3.3.4.3.4 or hex-slice 3. A control that cannot move the selection is
greyed with its reason rather than offering a rail of zero length, and
because the rule is necessary rather than sufficient the gate says
what it measured.

**The dual promoted to a tiling of its own, behind "Map the dual
instead".** `Topology.get_dual_
tiles()` gives a frame with tile ids whose ground covers the same
lattice, but `Tileable.__init__` dispatches on `tiling_type` and has
no path for supplied geometry, so building one means setting the
fields upstream's own setup would set. It goes in behind one function
with a canary that fails the day the library grows a real
constructor, and the same work goes upstream as a patch.

**And the catalogue learns that a name is not an identity.** `cairo`
and `laves 3.3.4.3.4` draw the same ground -- symmetric difference
0.000 -- so the entry gains the common name as a LABEL while the
record goes on storing the catalogue key, which is what keeps every
saved file readable.
