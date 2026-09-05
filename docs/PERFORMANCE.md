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

## The four stages nothing had measured, 2026-09-04

The breakdown above stops at the tiling and the layer building. The
stages around them -- seeding renderers, the preview rebuild, and the
GeoPackage write a Save performs -- had never been measured at all.
`tools/probes/what_a_generate_spends_its_time_on.py` drives a real
dialog Generate and then a real Save on the packaged Auckland data and
attributes cumulative profiler time to named stages, ONE SPACING PER
PROCESS for the reason the section above gives.

        spacing 500 (2,753 drawn)               generate     save
        worker: Tiling() + get_tiled_map          0.363s
          get_tiled_map (overlay and join)        0.155s
        landing: _add_output_layers               0.241s
          gdf_to_layer (frame -> QGIS layer)      0.159s
          seed_renderer (symbology)               0.028s
        preview: _rebuild_unit                    0.022s
        save: _save_the_map                                  0.304s
          write_gpkg_layers                                  0.144s
          point_layer_at                                     0.035s

        spacing 250 (10,502 drawn)              generate     save
        worker: Tiling() + get_tiled_map          1.034s
          Tiling.__init__ (constructor total)     0.654s
            _TileGrid.__init__ (lays the grid)    0.388s
          get_tiled_map (overlay and join)        0.378s
        landing: _add_output_layers               0.322s
          gdf_to_layer (frame -> QGIS layer)      0.239s
          seed_renderer (symbology)               0.030s
          split_out_the_no_data (the twins)       0.007s
          _update_layer_exclusions (the combo)    0.025s
        preview: _rebuild_unit                    0.024s
        save: _save_the_map                                  0.568s
          write_gpkg_layers                                  0.418s
          point_layer_at                                     0.048s

    Re-measured 2026-09-04 AFTER the conversion rewrite below, with the
    two constructors told apart. `gdf_to_layer` fell from 0.587s to
    0.239s in situ, which is the 2.3x arriving where a user meets it,
    and the landing halved with it.

AND THE PROBE HAD A STAGE THAT NAMED NOTHING. `split_absent` is not a
function; the no-data split is `bridge.split_out_the_no_data`. A name
that matches nothing contributes nothing, falls under the printing
floor, and is INDISTINGUISHABLE from a stage that is genuinely cheap --
so the row never appeared and the work read as free, while this
document honestly listed the twin split as unmeasured the whole time
the probe claimed to measure it. The probe REFUSES a stage naming a
function that does not exist now, checked against the source rather
than the profile, since a function that exists and was not called is a
legitimate absence. Measured at last, the twins cost 0.007s.

THE SYMBOLOGY IS NOT A COST, which is the plainest finding and the one
that stops an optimisation nobody needed: seeding four renderers costs
hundredths of a second and does not grow with the map, because the work
is per element rather than per tile. `_rebuild_unit` behind the preview
is 0.022s at both sizes for the same reason. Neither is worth touching.

THE SAVE IS ROUGHLY THREE QUARTERS WRITING, and `point_layer_at` is
0.035s for eight layers at both spacings -- flat because the ELEMENT
count is flat, which is consistent with the 2026-09-01 measurement that
the repointing is the residue the single-session rewrite deliberately
left. It is the term that goes quadratic at the 256-element ceiling,
not at eight.

**THE FIRST VERSION OF THIS TABLE DROVE BOTH SPACINGS IN ONE PROCESS**,
which is the trap the section above this one exists to record, made by
somebody who had just written it down. The rows are re-measured; what
the correction was worth is a METHOD rather than a number, since single
samples on a busy machine move by more than the difference did.

**AND THAT ROW WAS A DOUBLE COUNT, WHICH TOOK TWO GOES TO ESTABLISH.**
`Tiling.__init__` reported TWO calls against the worker's one while
`dialog.py` holds exactly one construction site. The matcher was
suspected, and this document then recorded it as CLEARED -- on the
strength of an ambiguity guard that was never in the file. The edit
reported success, the probe ran, the guard did not fire, and the
absence of a complaint was read as a verdict; it is not in that
commit, in HEAD, or in the working tree. A GUARD YOU HAVE NOT WATCHED
FIRE IS A GUARD YOU HAVE NOT GOT, and this is that rule arriving
through an edit that silently did not land rather than through a test
that could not fail.
WRITTEN, IT FIRES AT ONCE: `tile_map.py` defines `__init__` twice --
`_TileGrid` at line 112 and `Tiling` at 272 -- and the grid is built
INSIDE the constructor, so the row was summing a child into its
parent. Disambiguated by DEF LINE, which is how a class is named to a
profiler that knows only (file, line, function), both come back with
ONE call each and the arithmetic closes: 0.654s for the constructor of
which 0.388s is the grid, against the 1.059s the merged row claimed.
The tables above are re-measured accordingly.

## Converting the frame into QGIS layers, measured 2026-09-04

`gdf_to_layer` is the largest single term at spacing 150, so
`tools/probes/what_gdf_to_layer_spends_its_time_on.py` asks what its
microseconds are. It builds a real tiled frame through the product's
own door, then times the shipped function against a parametrised copy,
ONE ARM PER PROCESS with each arm's own shipped baseline beside it, and
compares the two layers FEATURE BY FEATURE -- geometry WKB and every
attribute -- because a conversion that changes what the map holds is a
cartographic decision rather than an optimisation.

    10,526 tiles, 13 attribute columns, spacing 250

    arm                    shipped      arm   us/feat   against control
    shipped gdf_to_layer    0.636s        --     60.4   --
    none (control)              --    0.715s     67.9   1.00x
    + batched WKB               --    0.664s     63.1   1.08x
    + multi in C++              --    0.519s     49.3   1.38x
    + positional attributes     --    0.559s     53.1   1.28x
    + per-column casts          --    0.681s     64.7   1.05x
    all four                    --    0.274s     26.0   2.61x

EVERY ARM IS EXACT: identical feature by feature, at 10,526 features,
on every row. That is what makes this an optimisation rather than a
ruling.

TWO CHANGES CARRY IT AND TWO DO NOT. Not constructing a shapely
MultiPolygon for every plain polygon -- QGIS converts in C++ through
`convertToMultiType` -- is the largest single term at 1.38x, and
setting attributes POSITIONALLY through `setAttributes` rather than
`feat[c] = v`, which does a field-name lookup per attribute per
feature, is 1.28x. Batching the WKB into one shapely call is 1.08x and
deciding the null-and-cast question once per COLUMN is 1.05x; neither
would be worth a line on its own, and both compose.

THE CONTROL IS THE ROW TO READ THE OTHERS AGAINST, not the shipped
function. The parametrised copy is about 12% SLOWER than what ships,
because it pays for its own flag checks -- so the individual arms are
quoted against it and the honest end-to-end figure is the 2.29x the
all-four arm scores against the shipped function in the same process.

AND THE 60 MICROSECONDS PER FEATURE REPRODUCES INDEPENDENTLY, which is
what says the method is sound: the generation profile above reached the
same figure through cProfile on a different frame, and this probe
reaches it on the wall clock.

**AND IT IS BUILT, MEASURED ON ITS OWN AFTERWARDS.** All four went
into `bridge.gdf_to_layer` on 2026-09-04. Re-run against the shipped
function, the probe's own baseline column is what says so: 0.270 to
0.286s across six children where it read 0.617 to 0.658 before, at 26.6
microseconds per feature against 60.4 -- and the all-four arm now
scores 0.97x, because it and the shipped function are the same code.
Every arm is still identical feature by feature.

WHAT IT IS WORTH END TO END IS STILL DIVISION RATHER THAN MEASUREMENT
and is not quoted as a figure: `gdf_to_layer` was 45% of a Generate at
spacing 150, so removing 56% of it is about a quarter off the whole.
The tables ABOVE describe the old function and are left as the
measurement they were -- a Generate has not been re-profiled end to end
since, and that is owed before any of those rows is quoted as current.

THE GUARD IS `test_the_faster_conversion_draws_the_same_layer`, which
compares the rewrite against the previous implementation kept beside
it, feature by feature over geometry bytes and every attribute. Its
fixture reaches what the tiling data could not: a MultiPolygon, a
GeometryCollection carrying a polygon, one carrying none, an empty
geometry, a missing one, and a null in each of three column kinds --
because the arms were measured on tiles that are all plain polygons
with no nulls, so every other branch would otherwise have shipped
unproved.

AND THREE CATALOGUE ENTRIES STAND ON IT, one per property the rewrite
put at risk rather than one per change that made it faster: the plain
polygon's promotion to multi, a WKB landing at its own row's index so a
skipped row cannot shift the rows after it, and the attributes landing
in the order the fields were declared. Each is aimed at the line where
the answer is DECIDED, and each was proved `caught` on 2026-09-04.
The middle one is the characteristic failure of this software wearing a
batch conversion: a map that looks entirely plausible and is wrong.

AND THE ARMS CONTAMINATED EACH OTHER UNTIL THEY WERE SEPARATED. Run in
one process, every arm keeps a ten-thousand-feature memory layer with a
spatial index alive for the exactness check, so later arms pay for
earlier ones: the all-four arm read 27.5 then 40.3 microseconds per
feature across two runs while the shipped baseline held steady. One arm
per process settles it, and the shipped column staying inside 0.617 to
0.658 across six children is what says so.

## PATCH 4 IS BUILT: the grid disc, measured 2026-09-04

The first of the two library-side reductions above is carried as patch
4 in `tools/vendor_weavingspace.py` (four edits, one idea) and offered
upstream in
`docs/process/upstream-note-the-grid-disc-is-larger-than-it-needs.md`.

    spacing 250                    before patch 4   after
    worker                                 1.152s   0.929s
      Tiling.__init__ (total)              0.698s   0.561s
        _TileGrid (lays the grid)          0.411s   0.340s
      get_tiled_map (overlay)              0.451s   0.366s
    placements kept                          100%    77.3%

THE OVERLAY FALLS WITHOUT BEING TOUCHED, which is the part worth
keeping: the placements that are never laid are exactly the tiles the
overlay would have clipped away and discarded, so the saving lands
twice.

EXACT AT EVERY ROTATION: 8 designs x 2 spacings x 4 rotations (0, 30,
45, 90) is 64 comparisons and NOT ONE TILE DIFFERS, compared on id and
geometry bytes by
`tools/probes/the_smaller_disc_tiles_the_same_map.py`.

**THE FIRST VERSION WAS NOT EXACT, AND HALF OF ALL DESIGNS WOULD HAVE
HIDDEN IT.** `_get_grid` phases its meshgrid from the extent's own
bounds, so one smaller polygon doing both jobs shifts every tile:
`crosses 4` at spacing 500 drew 2,772 tiles both ways with 2,622
differing, every one still touching the region -- nothing lost, the
whole pattern moved. The origin is `centre - ceil(2R)/2`, so the shift
appears only when `ceil(2R)` changes by an ODD amount, and on
`hex-slice 4` the two radii happened to agree. A guard written on that
design reported the phase fault as INERT, which reads exactly like a
test too weak to notice it; the fixture names `crosses 4` and says why.

## PATCH 5 IS BUILT TOO: the plugin declares its rotation

    spacing 250            before   patch 4   patches 4+5
    worker                 1.152s    0.929s        0.796s
      Tiling.__init__      0.698s    0.561s        0.434s
        _TileGrid          0.411s    0.340s        0.271s
      get_tiled_map        0.451s    0.366s        0.360s
    placements kept          100%     77.3%         ~49%

`rotations=None` is the default and is patch 4's behaviour exactly, so
an upstream caller that does not know loses nothing. THE PLUGIN CAN SAY
`(0,)` HONESTLY, and that is a fact about its own design rather than a
convenience: the Rotate modifier calls `unit.transform_rotate`, which
turns the prototile and RE-DERIVES the translation vectors, so the
lattice turns before the grid is laid -- where the library's argument
turns a finished tiling about the grid centre.

AND THE PROMISE BITES WHEN BROKEN, driven rather than argued: a tiling
told `(0,)` and asked for 45 or 90 degrees comes back SHORT at the
edges in 12 of 12 cases at spacing 250. A small design at a coarse
spacing does NOT show it -- `basket weave ab|cd` at 500 came back
identical at 30 -- so the guard stages the fine case and says why.

## The three columns, measured 2026-09-04

`tools/probes/what_the_proposed_grid_filters_would_keep.py` measures
the two proposed reductions at ONE spacing rather than borrowing the
figures taken at another, and the before/now columns were taken with
ONE INSTRUMENT over both arms -- the pre-rewrite `bridge.py` from
7004e23 run under today's probe -- because quoting the old table's own
numbers would compare two INSTRUMENTS rather than two versions, and
that instrument was wrong in the two ways recorded above.

    spacing 250, 10,502 drawn        before      now   proposed
    worker                           1.101s   1.152s     ~0.37s
      Tiling.__init__ (total)        0.687s   0.698s     ~0.24s
        _TileGrid (lays the grid)    0.414s   0.411s     ~0.14s
      get_tiled_map (overlay)        0.412s   0.451s     ~0.13s
    landing: _add_output_layers      0.736s   0.331s      0.331s
      gdf_to_layer                   0.633s   0.246s      0.246s
    preview: _rebuild_unit           0.025s   0.025s      0.025s
    save: _save_the_map              0.601s   0.559s      0.559s
      write_gpkg_layers              0.430s   0.424s      0.424s

    a Generate (worker+landing+preview)
                                     1.862s   1.508s     ~0.73s

THE UNTOUCHED ROWS ARE THE CONTROL, and they are what says the first
two columns differ by the code rather than by the machine: the grid at
0.414 against 0.411, the twins at 0.006 against 0.007, the combo at
0.027 against 0.026, the preview identical, the write at 0.430 against
0.424. That spread is also the noise floor -- about 10% on the worker
rows, which is why `get_tiled_map` reads HIGHER after a change that
cannot touch it, and why no conclusion is drawn from a difference
smaller than that.

**THE THIRD COLUMN IS ARITHMETIC AND MUST NOT BE QUOTED AS A
MEASUREMENT.** What is measured is the FACTORS, on this data at this
spacing: 8,109 grid placements today, 6,402 (78.9%) keeping the
promise to serve any rotation, 2,791 (34.4%) where the rotation is
known to be zero, which for this plugin it always is; and route A at
0.296s against route B at 0.228s with ZERO tiles assigned differently,
60.1% of the touching tiles being interior. The column composes them
by assuming the constructor's cost is proportional to placements and
the overlay's to the tiles reaching it. NOTHING IS BUILT, and the
assumption is the part a first attempt would find wrong.

THE LANDING AND THE SAVE DO NOT MOVE, which is the useful half of the
projection: `gdf_to_layer` only ever sees tiles that survived clipping,
so constricting the grid cannot touch it. The whole of the remaining
prize is in the worker, and after it the largest term this repository
owns outright is the Save's write at 0.424s -- never decomposed.

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
