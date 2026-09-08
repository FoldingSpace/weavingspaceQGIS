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

## The second refusal was mine, and naming it took the limit away

The first run of the scaffolding left two weaves of three refusing,
with a message that is not the gap one -- "this design's tiles meet,
but the library could not work out its structure" -- and that was
written up as a fact about weaves whose reach was unknown. It was a
fact about my filler.

`build` swallows the library's exception to compose that sentence, so
the diagnosis was one traceback away:

    File "weavingspace/tiling_utils.py", line 166, in get_corners
      corners = [geom.Point(pt) for pt in shape.exterior.coords]
    AttributeError: 'MultiPolygon' object has no attribute 'exterior'

`_setup_regularised_prototile()` DISSOLVES THE TILES BY `tile_id`, so
filler pieces sharing one id merge into a multi-part tile, and
`Topology` must take corners from every tile. Give each piece its own
id, and explode any multi-part the gap geometry arrives as, and
nothing merges:

    design              shared id      distinct ids   filler dropped
    plain weave a|b     no (1 multi)   YES            4 tiles, valid
    twill weave a|b     YES            YES           16 tiles, valid
    twill weave a|b-    no (1 multi)   YES            8 tiles, valid

THE TWILL WAS NOT DIFFERENT IN KIND. It passed because its daylight
happened to merge into single polygons; the other two happened not to.
A property of the scaffolding read as a property of weaves, and it
would have gone into the roadmap as an unknown of unknown size had the
maintainer not asked for the limit to be surpassed rather than
recorded.

THE GENERAL FORM, which this project has paid for in other clothes: a
refusal composed by our own code is a SENTENCE, not a diagnosis, and
where it swallows the exception the first move is to unswallow it.
`_why_not` is honest -- it says the tiles meet and the library could
not work out the structure, both true -- and it cannot say WHY,
because it never sees the reason either.

## The rate over the whole catalogue: 65 of 77

Three designs is not a rate, so the scaffolding was put to every weave
entry the catalogue holds, with the round trip judged in full: the
topology has to build, an edit has to apply, and dropping the filler
has to give back exactly the strand tiles that went in, all valid.

    topology built      65/77
    edit applied        65/77
    round trip closed   65/77

The twelve that do not are TWO SHAPES rather than a scatter, which is
what makes them worth chasing rather than accepting. Ten are twills
with richer over-under patterns -- `a|b- 3`, `a|b 4`, `a|b 1,2,2,1` --
and two are triaxial cube weaves raising `GEOSException`, which is a
different failure and is still undiagnosed.

## The ten twills are upstream's, and two hypotheses died first

Unswallowing the exception again -- the move that worked above -- gave
the same `KeyError` on all four twills sampled, from `get_edges`,
which looks a tile's own edge ids up in the topology's `edges` dict.

TWO HYPOTHESES OF MINE WERE REFUTED BY THEIR OWN CONTROLS, which is
the only reason the third is worth anything. T-JUNCTIONS: a filler
piece abutting two strands has no vertex at their shared corner, so
the tiles do not meet vertex-to-vertex -- except that the design which
BUILDS has 45 of them. PRECISION: the gap geometry comes out of a
boolean difference and might miss the library's grid -- except that
`gridify`ing every filler piece changed nothing and there are no
near-duplicate vertices anywhere, at any epsilon tried.

WHAT THE INSTRUMENT SHOWED. The `edges` dict was replaced with a
subclass that records deletions and changes nothing else:

    missing edge key                     (241, 238)
    edges deleted during construction    21
    was the missing key deleted?         yes
    was its reverse deleted?             no
    is its reverse still present?        no
    tiles still naming the deleted edge  tile 92

So the edge is deleted and a tile goes on naming it, and it is not a
direction convention, since neither orientation survives. That is
upstream's to mend, and the note is
`upstream-note-an-edge-is-deleted-while-a-tile-still-names-it.md`.

AND THE FIRST INSTRUMENTED RUN MEASURED NOTHING, worth the line: the
watching dict was never installed, because the subclass that was meant
to swap it in did nothing at all. It printed the same `KeyError` as
the plain run and read exactly like a result.

The sweep took about fifty minutes of one core and printed nothing
until it ended, because its output went through a `grep` that
block-buffers to a file. That is the project's own "an empty log is
not evidence of absence" met in a probe written an hour after quoting
it; a long sweep prints per design.

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

## A strand's long side is FOUR OR FIVE edges, and the class selector cannot aim at a ribbon

Ruling 3 says a manipulation moves a strand's two long edges IN PHASE,
and that was recorded as unbuildable until the edges could be
identified. An earlier reading here concluded that they identify
themselves -- that both long edges of a strand share one class, so the
selector the tab already has would name both sides together. THAT
CONCLUSION IS WITHDRAWN. It listed a strand tile's edges without
separating the two SIDES, and separating them reverses the answer on a
plain weave. `tools/probes/what_a_class_aimed_edit_does_to_a_ribbon.py`
is the measurement, and it reports each side apart.

A LONG SIDE IS NOT ONE EDGE. The scaffolding abuts a strand at every
crossing, so each side is cut into segments, each carrying its own
class:

    plain a|b, strand piece     4 edges a side, 1250 long:
                                + j250 i750 c125 a125
                                - b250 e750 f125 h125
    twill a|b, full piece       5 edges a side, 2250 long:
                                + a250 f750 c250 b750 e250
                                - e250 b750 c250 f750 a250
    twill a|b, under piece      1 edge a side, 250 long: d, d

WHETHER THE TWO SIDES SHARE A CLASS AT ALL DEPENDS ON THE WEAVE. The
twill's two sides carry the same five classes; the plain weave's carry
`{a,c,i,j}` against `{b,e,f,h}` and share NOTHING. So on a plain weave
every class-aimed edit moves exactly one side of a ribbon.

AND WHERE A CLASS IS ON BOTH SIDES, WHAT DECIDES THE PHASE IS WHETHER
ITS TWO SEGMENTS SIT OPPOSITE EACH OTHER. Measured along the strand
from its centre, on the twill's full-length piece:

    class c   + at (-125, 125)      - at (-125, 125)      ALIGNED
    class b   + at (125, 875)       - at (-875, -125)     STAGGERED
    class a   + at (-1125, -875)    - at (875, 1125)      STAGGERED

SO THE ANSWER IS NEITHER OF THE TWO THE QUESTION OFFERED. A zigzag
aimed at an ALIGNED class moves both sides together and the ribbon
undulates at constant width; aimed at a STAGGERED one it moves one side
at a time and the ribbon pinches and swells. Both happen on one design,
under one selector, at one strand width:

    twill, class c    width 750.0-750.0  swing 0.0%   centreline 6.3%
    twill, class d    width 750.0-750.0  swing 0.0%   centreline 6.3%
    twill, class b    width 678.7-821.3  swing 19.0%  centreline 9.5%
    twill, class f    width 678.7-821.3  swing 19.0%  centreline 9.5%
    plain, class e    width 626.4-821.3  swing 26.0%  centreline 9.5%
    control, no edit  width 750.0-750.0  swing  0.0%  centreline 0.0%

A SWING OF TWICE THE CENTRELINE'S TRAVEL IS THE SIGNATURE OF ONE SIDE
MOVING, which is what the staggered rows read, and it is why the
stagger was MEASURED rather than left as the arithmetic that suggested
it. The constant reading is the exact one and is what the conclusion
rests on: two edges displaced by the same graph function leave every
chord at the original width. The swings are not exact amplitudes, since
the width is a chord on a fixed axis and a sloped edge reads slightly
wide.

WHAT THAT COSTS RULING 3. The class selector cannot deliver a ribbon of
constant width, on any weave measured, because the classes are a fact
about the tiling's symmetry and a ribbon is not. An edit aimed at a
STRAND is a different selector from an edit aimed at a class, and
building one is work nobody has scoped. The alternative the ruling
already points at is the longer-run answer below, where the strand
follows a path and the question does not arise.

AND AN AREA DIGEST CANNOT ANSWER ANY OF IT, a zigzag conserving area
whichever way the edges move -- which this project already records
about a different measurement of the same manipulation.

TWO INSTRUMENT FAULTS, BOTH MINE. A topology `Tile` carries `label`,
not `tile_id`, so an early run matched no strand tile and printed an
empty list that read exactly like "no strands found". And the width
probe first took each piece's LONGER side as the strand's axis, which
is right for a full piece and wrong for the under-piece a weave cuts
750 across by 250 along -- so those rows came back transposed, and a
strand 750 wide reported a constant width of 250. The across extent is
`aspect * spacing` on every piece, over or under, so that is what picks
the axis now, and the probe refuses a piece where neither side is that
width rather than measuring the wrong direction quietly.

## The cube weaves are diagnosed, and it is ONE root wearing two faces

They were recorded here as the only undiagnosed weave failures. Driven
with the exception UNSWALLOWED -- because a refusal our own code
composes is a sentence rather than a diagnosis, which this record
already says once -- all three fail inside the SAME library call:

    a--|b--|c--   AttributeError: 'MultiPolygon' object has no
                  attribute 'exterior', from `get_corners`
    a-b|c-d|e-f   GEOSException: unable to assign free hole to a shell
    abc|def|ghi   at -433.01270299999999 1000.000002

`get_clean_polygon` ends `return gridify(geom.Polygon(corners))`, and
`gridify` is `shapely.set_precision` at `RESOLUTION = 1e-06`. That call
is both failures: it RAISES on some input, and on other input it SPLITS
a pinched polygon and hands back a MultiPolygon that `get_corners` asks
for `.exterior` on the very next line.

THE DECISIVE READING IS THAT THE SAME TILE IS FINE IN THE FRAME. Of a
154-shape patch, two clean to multi-part, and both are copies of one
filler piece:

    shape 53 = tile 'z0', copy 2
      before  Polygon, area 378886.116, 8 corners, valid
      after   MultiPolygon, 2 parts, losing 0.000750 of area
      the same tile in the base frame cleans to a Polygon

So a lattice translation moves a near-pinch onto the precision grid,
and whether a copy survives is a property of the OFFSET rather than of
the tile. Nothing about triaxiality is special except that its offsets
are irrational multiples of the resolution.

TWO REPAIRS WERE TRIED, ONE TERM AT A TIME, AND ONLY ONE MOVED
ANYTHING. Snapping the filler to the library's own grid before handing
it over takes `a-b|c-d|e-f` past the GEOSException entirely -- so that
half is ours to avoid. Exploding multi-part tiles after regularising
does NOT help, and its own control says why: the multi-part count in
the frame goes to zero and the same exception still fires, because the
geometry that raises is made downstream, in the patch, by the cleaner.
A repair aimed at the object you can see rather than the object that
raises is dead code that reads as protection.

WHAT IS OURS AND WHAT IS UPSTREAM'S. Ours is not to hand the library
filler that pinches at 1e-06. Upstream's is that `get_clean_polygon`
may return a multi-part and `get_corners` assumes it cannot, which any
tiling with a pinched tile can reach and which arrives as an
`AttributeError` about `.exterior` rather than as anything a reader
would connect to precision. That is written up in
docs/process/upstream-note-a-cleaned-polygon-may-be-multi-part.md and
is owed a SENDING rather than a repair.

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
the notation. Its own roadmap entry follows from that. (Built
2026-09-08; the entry that remains is the cap and the designing tab.)

**AND THE SCAFFOLDING CAN REACH A TWO-LETTER CLASS LABEL, WHICH THE
CLASS MACHINERY DOES NOT SURVIVE.** The library labels transitivity
classes `a`..`z` and then `aa`, `ab`, with its own comment reading
"note that it is inconceivable that this many labels will ever be
needed" -- and a scaffolded `basket weave ab|cd` carries 36 edge
classes. Two things break there. `topology_edits.classes` returns the
labels JOINED INTO ONE STRING, which cannot be split back once any
label is two characters; and the library matches a selector with
`label in selector`, so aiming at `aa` also moves the class `a`. IT IS
NOT A LIVE DEFECT: the eight most intricate designs this project's own
measurements single out carry one to five edge classes, `chavey K`
highest at five, so nothing on the shipped path is near the ceiling.
The scaffolding is what multiplies the count, so whatever is built on
it settles this first -- a class is a LABEL rather than a character,
and the selector needs a boundary the library does not give it.

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

The instruments are
`tools/probes/can_a_weave_carry_a_topology.py`, for whether a weave can
carry a topology at all, and
`tools/probes/what_a_class_aimed_edit_does_to_a_ribbon.py`, for what an
edit then does to the ribbon. Both are committed, because a figure with
no instrument beside it is folklore.
