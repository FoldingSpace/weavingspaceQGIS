# Editing a weave's structure: what was tried, and what it taught

The Topology tab refuses a weave. A weave's strands are narrower than
the cells they ride in, an inset opens gaps, `Topology` needs a
gap-free tiling, and so the tab is unavailable on more than half the
catalogue's designs. This is the record of an evening spent asking
whether that is a fact about weaves or an artefact of how they are
built, kept because the dead ends are worth more than the conclusion.

It is a WORKING RECORD rather than a specification. The rulings it
produced are in CLAUDE.md, the compact account is C-347, and what is
owed before anything is built is in ROADMAP.md.

## The question, and the two forms it took

The maintainer asked, first, whether a weave could be TEMPORARILY
MODIFIED so that a topology build becomes possible and sensical. Then,
once the measurements were in, they sharpened it into the question that
actually governs: not "is it possible as-is" but "what does it take to
make it sensible and in the spirit of an application to weaving".

The second question is the one this document is organised around,
because the first has an answer that is technically yes and
cartographically useless.

## What the library actually does, read rather than probed

`_get_cell_strands(width, coords, orientation, n_slices)` builds a
cell's strands DIRECTLY FROM THE GRID at the requested width. It takes
`sf = 2 - width` for the biaxial case, scales the cell by `sf`, cuts
slices of total width `w * spacing` across it, intersects them with
the expanded cell and rotates them to the strand's orientation.

Two consequences follow, and neither is visible from outside:

**A THIN STRAND IS NOT A NARROWED WIDE ONE.** Both are generated from
the grid. Measured on `plain weave a|b` at spacing 1000, the real 0.75
strand piece is **750 x 1250** -- narrower ACROSS its own axis and
LONGER ALONG it than the 1000-unit cell it belongs to, because `sf`
extends it into its neighbours. That overlap is what keeps a ribbon
continuous where two cells meet.

**AND `aspect == 1` TAKES A DIFFERENT PATH THROUGH ASSEMBLY.**
`_get_weave_tiles_gdf` buffers, dissolves by `tile_id` and explodes
when the aspect is exactly 1, so same-label pieces that touch FUSE
into one polygon; below 1 they cannot touch and stay separate.

## Four things tried, and why three failed

**1. BUILD SOLID, EDIT, THEN THIN.** Refuted by the assembly path
above. A `twill weave a|b` has 16 tiles at aspect 0.75 and **2** at
1.0, and its six edge classes when solid are boundaries between fused
regions rather than between strand pieces. An edit made there is aimed
at something the real weave does not contain. (`plain weave a|b` keeps
its four tiles either way, so this fails on some weaves and not all,
which is worse than failing on all.)

**2. BUILD NEARLY SOLID, SO THE COMBINATORICS SURVIVE.** Refuted by
measurement. The gap is a cliff rather than a slope:

    aspect    tiles   gap of one cell   topology
    1.0           4        0.00000000   yes
    0.999         4        0.00000100   NO
    0.99          4        0.00010000   NO
    0.95          4        0.00250000   NO
    0.75          4        0.06250000   NO

A millionth of a cell is still a gap. There is no tolerance to exploit.

**3. THIN BY INSETTING THE SOLID WEAVE**, which is tempting because the
plugin already applies an inset to weaves, scaled by aspect. Refuted
arithmetically: `inset_tiles(125)` on the solid weave gives pieces of
**750 x 750** against the real thin weave's **750 x 1250**, a
symmetric difference of **40%** of the real weave. An inset SHORTENS
where thinning LENGTHENS. The ribbons stop being continuous, which is
the one property that makes a weave a weave.

**4. SCAFFOLD THE DAYLIGHT, TAKE THE TOPOLOGY, DROP THE SCAFFOLDING.**
The maintainer's own construction, and it works. Fill the gaps between
strands with filler tiles under a reserved id, build the topology of
the resulting gap-free tiling, aim the edit at a strand class, and
remove the filler afterwards. Measured on `twill weave a|b` at 0.75:

    16 strand tiles + 16 filler  ->  32 tiles
    coverage: gap 0.000000, overlap 0.000000
    Topology BUILDS: 6 edge classes, 4 vertex classes
    a zigzag aimed at a strand class applies
    dropping the filler leaves the original 16 tiles, all valid

That is the round trip the first three attempts could not close.

## What scaffolding does NOT yet do

One of three weaves tried is not a rate, and the two failures refuse
for a DIFFERENT reason than the one this was built to remove:

    design              filled coverage        topology
    plain weave a|b     gap 0, overlap 0       NO
    twill weave a|b     gap 0, overlap 0       yes
    twill weave a|b-    gap 0, overlap 0       NO

Both failures say "this design's tiles meet, but the library could not
work out its structure", which is not the gap refusal. Diagnosing that
second refusal is the first thing owed; until it is understood, the
size of the family this serves is unknown.

## The conscious gaps are named by the strands code, not by geometry

A weave has two kinds of daylight and they must be treated
differently: the gap that strand WIDTH opens, which the filler should
close, and the gap a hyphen in the strands code opens, which is a
deliberate absence and must stay open.

Two geometric tests for telling them apart were tried and both were
wrong. The answer needs no geometry at all: `strands="a|b-"` states
which positions carry a strand and which carry nothing, so the filler
is generated FROM THE CODE and a position marked `-` is never filled.
A declarative fact should not be inferred from the shapes it produces.

## What weaving asks of an edit

The unit of meaning in a weave is the STRAND, not the tile. A strand
is a continuous ribbon of roughly constant width that passes over and
under others, and that constancy is what makes it read as yarn rather
than as a row of quadrilaterals.

So an edge-aimed edit -- what the tab does for tilings, and what
scaffolding would let it do for weaves -- is the wrong level. Moving
one edge of one piece gives a ribbon wider in some places than others,
which is torn paper rather than weaving, and is the kind of result
that comes back as a defect report rather than being used.

**A MANIPULATION THEREFORE MOVES A STRAND'S TWO LONG EDGES IN PHASE**,
so the ribbon undulates at constant width. Whether those two edges are
identifiable from the topology's classes is UNMEASURED and is the
second thing owed.

**AND THE OVER AND UNDER SURVIVES AN EDIT MADE AFTERWARDS.**
`get_visible_cell_strands` bakes visibility into the polygons at
construction, differencing each layer against the mask of the one
above, so pieces arrive already clipped and an edit inherits the
crossings. The constraint that follows is worth stating rather than
discovering: an edit must not move a strand ACROSS a crossing.

## The longer-run answer, which is a different feature

Undulating a ribbon by moving its edges is a way of approximating what
weaving actually does. The authentic version is that the strand
follows a PATH: the grid the strands ride on carries the undulation,
the width stays a property of the ribbon, and no filler, no topology
and no dropping step is needed at any strand width.

That needs `_weave_grid` to take a path rather than an orientation,
which is upstream's rather than ours, and it is recorded as the
long-run goal rather than as work anybody has scoped.

## Two things found on the way, unrelated to the question

**`_shallow_copy_with_tiles` CANNOT COPY A WEAVEUNIT.**
`WeaveUnit._setup_regularised_prototile()` takes no `override`
argument where `TileUnit`'s does, so the supplied-geometry workaround
this project already leans on for the dual is silently tiling-only.
Anything built on it for weaves widens it first.

**AND THERE IS NO STRANDS-CODE INPUT IN THE DIALOG.** The 77 weave
entries in `catalog.py` carry their codes baked in, and the family
list is the only way to reach one, while docs/USER-GUIDE.md teaches
the notation. Its own roadmap entry follows from that.

## My own instruments, tallied apart

Two were wrong and both were caught by their own output, which is the
only reason the conclusions above are not built on them.

**THE FIRST GAP MEASURE SUBTRACTED THE TILES FROM THE PROTOTILE**,
which docs/TOPOLOGY.md already records as reading 10.6% of an
untouched design missing, "because a unit's tiles need not lie inside
the particular polygon its prototile is". The tell was a twill whose
SOLID gap came back larger than its thin one, which is impossible.
`plane_coverage`'s third return is the gap geometry and is the
instrument that answers.

**AND A CLAIM WAS MADE FROM A REFUSAL WITHOUT ASKING WHY IT REFUSED.**
It was reported to the maintainer that a conscious gap survives aspect
1.0 as a gap, on the strength of `build()` returning None. Measured,
`twill weave a|b-` at 1.0 has gap 0.000000 and OVERLAP 0.125000: the
hyphen shows up as an overlap, not a gap. The claim was directionally
useful and factually wrong, and it is the reason the strands-code
answer above is better than either geometric test.

The instrument is
`tools/probes/can_a_weave_carry_a_topology.py`, committed because a
figure with no instrument beside it is folklore.
