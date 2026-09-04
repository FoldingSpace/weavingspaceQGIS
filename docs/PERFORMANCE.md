# What this plugin's time is spent on, and which ideas are worth taking

Performance findings were scattered across four binding documents before
this one existed -- the tiling speed-up in ROADMAP.md, topology build
costs in docs/TOPOLOGY.md, the save's quadratic in MAINTAINING.md, and
the profiling traps in CLAUDE.md. That is this project's own commonest
defect shape, one fact in several stores, so measured costs and open
ideas live here from 2026-09-03 and the other documents point at it.

TWO RULES GOVERN EVERY ENTRY, both paid for already. A figure with no
instrument beside it is folklore, so each names the probe that produced
it and the date. And a speed-up that changes what the map SAYS is a
cartographic decision rather than an optimisation, so each says whether
it is answer-preserving.

## Where a map's time goes, measured 2026-09-03

`tools/probes/what_the_tiled_map_costs.py`, on the packaged Auckland
data (155 zones, EPSG:2193), `laves 3.3.4.3.4`, through the same door
the dialog uses -- `catalog.make_unit`, then `Tiling(unit, region)`,
then `get_tiled_map`, whose own `debug=True` timings it reads rather
than replacing anything. ONE SPACING PER PROCESS, for the reason below.

    spacing     tiles   get_tiled_map   of which the overlay
       1200     1,988          0.072s      0.059s
        800     3,892          0.111s      0.089s
        500     8,932          0.159s      0.127s
        350    17,248          0.250s      0.197s
        250    32,436          0.399s      0.308s
        150    86,768          0.913s      0.691s
        100   191,184          1.839s      1.365s   (74%)

THE OVERLAY IS THE COST and everything else is noise beside it --
preparing the data, computing areas, dropping columns and performing the
lookup together come to hundredths of a second even at 191,184 tiles.
BUT IT SCALES WELL: 96 times the tiles for 23 times the overlay, which
is sub-linear, so there is no runaway term to hunt. The figures at
86,768 and 191,184 agree with the ones recorded when the `idxmax` patch
landed (0.94s and 1.91s), which is what says the method is sound.

**AND A STAGE TABLE RUN IN ONE PROCESS INFLATES WITH POSITION.** The
first version of this measurement drove all four spacings in a single
process and reported 2.160s at spacing 350 where a fresh process reports
0.250 -- a factor of nine, growing with each spacing measured before it.
Profiled, the same call took 0.277s, and the disagreement between the
timer and the profiler is what gave it away. The cause is not
established (allocator or GC pressure after earlier tilings are the
candidates) and does not need to be: MEASURE ONE SIZE PER PROCESS. This
project's own rule is that a comparison across two runs on a busy
machine is not a measurement; the sharper form is that a series of sizes
inside ONE run is not a series of measurements.

## And the tiling is not the largest cost -- the QGIS side is

Measured 2026-09-03 on the same data, one size per process, timing the
three stages a Generate actually performs:

    spacing    tiles   Tiling()  get_tiled_map  gdf_to_layer   drawn features
        500    8,932     0.157s        0.147s        0.173s            2,759
        250   32,436     0.491s        0.372s        0.627s           10,526
        150   86,768     1.231s        0.865s        1.728s           28,619

CONVERTING THE RESULT INTO QGIS LAYERS IS THE BIGGEST SINGLE TERM --
45% at spacing 150 against 32% for the tiling and 23% for the map --
and it runs at a steady 60 microseconds per DRAWN feature.

WHICH DECIDES WHAT THE GRID WORK IS WORTH. `gdf_to_layer` only ever
sees tiles that survived clipping, so constricting the grid does not
touch it: the 66% falls on `Tiling()` and the overlay alone, taking
spacing 150 from about 3.8s to about 2.5s. Worth doing, and after it
the layer conversion dominates by some distance.

AND A FIXED COST SITS UNDER ALL OF IT, from
`tools/probes/interaction_cost.py` at 612 tiles where the tiling is
negligible: about 0.075s per render in `_add_output_layers`, of which
`removeMapLayer` is 0.027s, plus about 0.073s in the signal cascade a
layer change sets off -- `_layers_removed`, `_update_layer_exclusions`,
`setExceptedLayerList` -- and about 0.042s rebuilding the preview. That
is QGIS-side churn rather than cartography, and it is the floor under
every run however small the map.

WHAT IS NOT MEASURED HERE, and is owed before this counts as a full
breakdown: renderer seeding, the no-data twin split, the layer-tree and
stamping work, and the GeoPackage write on a Save.

## The overlay computes an argmax and throws its geometry away

In the `prioritise_tiles` path -- the default -- the fragments exist
only to carry an area:

    overlaps = self.region.overlay(join_layer, make_valid = False)
    overlaps[area_name] = overlaps.geometry.area
    lookup = overlaps.iloc[overlaps.groupby("joinUID")[area_name]
                           .agg("idxmax")][["joinUID", id_var]]

Nothing downstream draws those fragments. So the question is not how to
intersect faster but how to reach the same argmax with fewer clips.

### The interior/boundary split: exact, and it halves the overlay

A tile lying wholly inside one zone has a foregone argmax -- the
fragment is the tile, its area is the tile's area, and the winner is
that zone. Route A is what the library does; route B assigns the
interior by a `within` join and clips only what is left.

    spacing    tiles    outside  touching  interior (share)  route A  route B  differ
        350   17,248     11,786     5,462    2,643 (48.4%)    0.198s   0.166s       0
        150   86,768     58,149    28,619   21,275 (74.3%)    0.748s   0.413s       0
        100  191,184    127,500    63,684   52,279 (82.1%)    1.385s   0.679s       0

TWO THINGS THAT DECIDE WHETHER IT IS WORTH BUILDING. It is EXACT -- not
one tile of 63,684 is assigned differently, at any size measured -- and
that is what separates it from the centroid approximation refused on
2026-08-31, which changes which zone 4.4% of tiles take their data from
and is therefore a cartographic decision rather than an optimisation.
And ITS VALUE RISES WITH THE MAP: the interior share goes 48%, 74%, 82%
as the tiles get finer, so it pays most exactly where the seconds are.
At 191,184 tiles it halves the overlay, which is about 38% off the whole
of `get_tiled_map`.

AN EARLIER READING OF THIS WAS WRONG AND IS CORRECTED HERE. The interior
share was first quoted as 95%, carried across from the "4.4% of tiles
straddle" figure measured on other data at another scale, and then
measured at 15% by an instrument that counted tiles OUTSIDE the region
as straddlers. Neither number was about this question.

### The larger prize is the two thirds that are never wanted

At every spacing measured, about two thirds of the tiles lie wholly
outside the region -- 127,500 of 191,184 at spacing 100. They are built
by `Tiling()`, carried into the overlay, clipped away and discarded, so
they cost twice.

WHY THEY EXIST AT ALL, measured rather than assumed. `TileGrid` lays its
placements over a DISC centred on the region, with radius the distance
from the centre to a corner of the oriented bounding rectangle. On this
data that is 528.4 km2 of ground for a 155 km2 region, and the waste is
two factors multiplied: 1.70x for the disc over its own rectangle, and
2.00x because a coastline is not a rectangle -- 3.41x together, against
a measured 3.16x (5,462 of 17,248 tiles touch).

AND THE DISC IS DELIBERATE, WHICH IS THE PART THAT DECIDES THE REPAIR.
`Tiling.__init__`'s own docstring says it: "The tiling is extended
sufficiently to allow for its application at any rotation." The grid is
built in the CONSTRUCTOR, while `rotation` is chosen later at
`get_tiled_map`, so the constructor cannot know whether a rotation is
coming and a rotation-invariant extent is the only safe answer.

UPSTREAM REALLY DOES ROTATE, so this cannot simply be taken out.
Counted across upstream's own examples on 2026-09-03: 33 call sites of
`get_tiled_map`, of which EIGHT pass a non-zero rotation -- 30, 20, 10
and 45 degrees, plus two computed. The GWR examples, the weave-map
tests and the cairo example all rely on it.

THIS PLUGIN NEVER DOES, AND THE REASON IS THAT IT ROTATES EARLIER.
There is exactly one call site, in `dialog.py`, and it passes no
rotation. The Rotate MODIFIER calls `unit.transform_rotate(angle)` with
`independent_of_tiling` at its default, which rotates the prototile and
RE-DERIVES THE TRANSLATION VECTORS -- so the whole lattice turns before
the grid is laid, where the library's argument turns the finished tiling
about the grid centre. The same visual effect at a different point in
the pipeline, and it means this plugin's tiling rotation is always zero,
which is what lets it claim the larger of the two reductions below.
(Whether the plugin should ALSO expose the library's own rotation is a
separate question and a real one: the two coincide only while the unit's
vectors travel with it, and `independent_of_tiling=True` is a third
behaviour the plugin does not offer.)

AND THERE ARE TWO REDUCTIONS, NOT ONE, which the first reading of this
missed by treating the disc as all-or-nothing. (Maintainer's
correction, 2026-09-03: allow for the rotation and there is still a
substantial reduction.)

THE FIRST NEEDS NO API CHANGE AND KEEPS THE PROMISE EXACTLY. Rotation
about the centre PRESERVES DISTANCE FROM THE CENTRE, so the ground a
tiling must cover to serve ANY rotation is only the radii the region
actually occupies -- not the circumscribed disc. Today's radius is
centre-to-CORNER of the oriented rectangle; a region touches its
rectangle's EDGES, as every region does, and rarely its corners.
Measured: 12,970 m today against 10,960 m to the furthest point of the
region, so 3,228 placements of 4,312 -- a quarter off, exact, for every
caller including upstream's eight rotating examples. Where the centre
falls OUTSIDE the region -- a ring, an archipelago, a coastal strip --
the inner radius cuts more again, and the requirement is an annulus
rather than a disc; Auckland's centre is inside its region, so there is
no inner saving in this measurement.

    radius used today (rectangle corner)   12,970 m   528.4 km2   4,312 placements
    radius the region actually reaches     11,207 m   394.6 km2   3,228 placements  (75%)
    the region's own shape, rotation known             --         1,473 placements  (34%)

AND THE FILTER IS NOT THE COST -- THE FILTER IS ITSELF A SAVING.
(Maintainer's question, 2026-09-03: would constricting the grid cost
more than it saves?) Measured at spacing 350, over the same 5,625
candidate placements:

    filter                              cost    placements   tiles    downstream saved
    today: Point() then .within(disc)  63.6 ms      4,312   17,248     --
    any rotation: a numpy radius test   0.0 ms      3,228   12,912    ~123 ms
    rotation known: contains_xy         0.4 ms      1,473    5,892    ~321 ms

TODAY'S FILTER IS A PYTHON LOOP -- 5,625 shapely `Point()` objects and
5,625 `.within()` calls, which is about a fifth of `Tiling()`'s whole
291 ms. Both replacements are vectorised C over numpy arrays, so the
STRICTER test is the CHEAPER one and the accounting is a saving on both
sides rather than a trade. Keeping rotation fully general saves the
63.6 ms and about 123 ms besides, with no API change and no output
change; with the rotation known it is about 385 ms of a 541 ms map.

THAT IS THE REAL FORCE OF THE LATTICE FRAMING, and it is not the one
this document first recorded. Integer division and modulus do not
merely select fewer cells: they put every candidate in a numpy array,
where "which cells does the region reach" is a comparison rather than a
per-object geometric predicate.

ONE FIGURE IS DIVISION RATHER THAN MEASUREMENT and should not be quoted
without building it: the "downstream saved" column costs each avoided
tile at the average tile's share of `Tiling()` plus the overlay. That is
fair for the overlay and probably generous for construction, where the
per-tile geometry is uniform but the frame assembly is not.

THE SECOND IS THE OPT-IN HINT, not a replacement: a
constructor argument saying what rotation the caller will ask for, with
today's behaviour as the default. Told that no rotation is coming, the
grid can filter its placements against the region's own geometry --
which `_get_grid` ALREADY does, through
`p.within(self.extent_in_grid_space)`; only the polygon is wrong for
this case. Measured on this data with the region buffered by the
prototile's own reach (247 m, its centroid-to-corner distance): 1,473
placements wanted of 4,312, so 5,892 tiles built instead of 17,248, a
66% cut that falls on `Tiling()` AND the overlay together.
(Maintainer's suggestion, 2026-09-03.)

THREE THINGS WOULD HAVE TO BE GOT RIGHT, and they are where a first
attempt fails. A TILE IS NOT CONFINED TO ITS CELL -- insets, zigzag
edges and non-convex elements reach into neighbours, so the test is each
tile's bounding box in lattice coordinates with a one-cell margin; a
centroid or a bare cell index misses cases and produces a plausible
wrong map, which is this software's characteristic failure. THE LATTICE
SURVIVES THE MODIFIERS ONLY AS AN AFFINE ONE, so rotation and skew make
it an inverse affine transform and then floor and modulus. AND
`overlay(make_valid=False)` MAY BE DOING REPAIR the hand-rolled path
would not, so whatever replaces it is compared tile by tile rather than
in aggregate -- which is what the split above did, and why its zero is
worth more than its seconds.

## What has already been taken, and what was refused

**TAKEN: the join lookup's pandas idiom** (patch 3 in
`tools/vendor_weavingspace.py`, 2026-08-31). `.agg(pd.Series.idxmax)`
passes a FUNCTION and defeats pandas' cython path, falling back to
`_aggregate_series_pure_python`, which walks every group in Python;
`.agg("idxmax")` is the same answer by the fast path. Measured 41x to
191x on the aggregation, and `get_tiled_map` from 2.68s to 0.94s at
86,768 tiles. Ties break identically, staged rather than hoped for.

**REFUSED: the centroid lookup.** A centroid `sjoin` answers in 0.17s
against the overlay's 1.44s at 191,184 tiles and is a DIFFERENT RULE: it
cannot say which zone a tile mostly lies in, and 8,467 tiles (4.4%)
straddle a boundary. Swapping it changes which zone those tiles take
their data from, which is the maintainer's decision and not an
optimisation. The library offers it as
`use_centroid_lookup_approximation` and the plugin does not pass it.

**MEASURED AND NOT WORTH IT: keeping a python-side GeoPackage handle
alive across a save** (2026-09-01). 0.91 to 1.02 of the plain cost, so
GDAL's shared dataset cache is not the lever; the repair had to be a
genuine single OGR session, and was.

## The costs that are known and are somebody else's

**`Topology.__init__` is eager and expensive**: 0.8s to 21s depending on
the design's shape rather than its element count, with `hex-colouring 7`
the worst in the catalogue. Decomposed across five arms in
docs/TOPOLOGY.md, which shows the cost belongs to the LIBRARY rather
than to this machine or to our wrapper, and that upstream's experimental
branch roughly halves it.

**Saving and loading were quadratic in the element count** and are not
any more, bar one measured residue: pointing each layer at its own table
needs a provider apiece, about 33 seconds at the 256-element ceiling.
The account is in MAINTAINING.md under the save's three doors.
