# Symmetry, three ways

Every edit in the Topology tab is aimed at a class rather than at a shape: you click one edge, and the plugin moves all the edges that are, in some sense, the same edge. What that sense is, and how we arrive at it, has never been set down for anybody who did not write the code. This note describes three ways of answering the question, compares them on measurements we can take today, and says what each costs to run rather than only what it costs in principle. Everything here was measured on one machine at commit `6d59e67`, by three probes now committed under `tools/probes/`, so any figure in it can be re-run and disagreed with.

## What the tab needs from a symmetry

Three things, and they pull in different directions. We need labels, so that a person can point at an edge and the plugin can record what they pointed at in a form that survives a GeoPackage and a week. We need those labels to be stable, since an edit list replays by label, and a label meaning one edge on Tuesday and another on Wednesday moves somebody's work quietly onto the wrong part of the design. And we would like to know, before anybody drags anything, which controls can do something at all: `push_vertex` moves nothing whatever on some designs, a fact we found by measurement and presently express as a rail of zero length. Each approach below supplies these three in different proportions, at prices that differ by three orders of magnitude.

## What we do now

The vendored library builds a `Topology`, and its transitivity classes are our labels. It reaches them geometrically. First it assembles candidate isometries: the two lattice translations that generate the repeat, the prototile's own symmetries, each tile's own symmetries, and the transforms carrying one tile onto another of the same shape. Then it tests each candidate against the tiling, keeps those that map it onto itself, and takes the orbits, so that tiles carried onto one another by a kept transform form one class, and likewise for vertices and edges. The labels `a`, `b`, `A`, `B` are those orbits, indexed. None of this is wrong, and nobody in the code calls it crystallography, but that is what it is; what is missing is not the group but any name for it and any use of its structure.

## Wallpaper groups

A pattern repeating across the plane has a symmetry group: the rigid motions (translations, rotations, reflections, glide reflections) that leave it looking exactly as it was. For a genuinely repeating pattern that group always contains two independent translations, and once those are present the possibilities collapse. There are seventeen such groups and no more, a result from the end of the nineteenth century that most people meeting it first find surprising, and every wallpaper, tiled floor and woven cloth belongs to one of them. They carry names like p4m and p6m, which say what the strongest rotation is and whether mirrors are present.

The collapse happens because translations constrain rotations. A five-fold rotation, repeated on a lattice, generates points closer together than the lattice spacing, which cannot be; only orders two, three, four and six survive. This is the crystallographic restriction, and for us it is practical rather than decorative, since it means a search for a design's symmetries is a small bounded search over a few rotation orders about a few candidate centres, in place of the open-ended matching we perform now.

Two further pieces of the apparatus bear directly on the tab. Transitivity classes, our labels, are exactly the orbits of the group, so both approaches are aiming at one object along different roads. And the site symmetry, sometimes called the stabiliser, is the subgroup of motions holding a particular point still: a vertex on a four-fold rotation centre is held by that rotation, a vertex on a mirror line by the reflection, a vertex in general position by nothing at all. Site symmetry is what tells us which controls are dead, and it does so by a small piece of linear algebra rather than by experiment, because a displacement respecting the symmetry must lie in the subspace every element of the stabiliser fixes.

## What the site symmetry predicts

We built six designs through `catalog.make_unit`, which is the door the dialog itself uses, read the group the library had assembled and the classes it derived, computed the site symmetry of each vertex class, and set all of that against what `push_vertex` does in practice.

| design | transforms found | rotation orders | classes | vertex class site symmetry | fixed space | `push_vertex` moves |
|---|---:|---|---|---|---|---|
| laves 3.3.4.3.4 | 24 | 2, 4 | 1 tile, `A B`, `a b` | A: two quarter turns | 0D | nothing |
| | | | | B: one mirror | 1D | nothing |
| hex-slice 3 | 27 | 3, 6 | 1 tile, `A B`, `a` | A: three-fold and mirrors | 0D | nothing |
| | | | | B: two mirrors | 0D | nothing |
| hex-slice 6 | 84 | 2, 3, 6 | 1 tile, `A`, `a` | six-fold and mirrors | 0D | 1.5e-09 |
| archimedean 4.8.8 | 18 | 2, 4 | 2 tiles, `A`, `a b` | none | 2D | 0.103 of the area |
| archimedean 3.12.12 | 32 | 2, 3, 6 | 2 tiles, `A`, `a b` | none | 2D | 0.130 of the area |

Two things fall out of that. Every rotation the library finds is of order two, three, four or six once its powers are reduced (the raw entries include turns of 240 and 300 degrees, which are powers of three-fold and six-fold rotations), so the crystallographic restriction holds exactly on our designs and a wallpaper search would enumerate the space we currently search blind. And site symmetry predicts what we had recorded as an arithmetic accident: `docs/TOPOLOGY.md` explains `push_vertex` moving nothing by the incident unit vectors cancelling, where the general statement is that a vertex whose stabiliser contains a rotation has only the zero displacement available to it. Every prediction of zero above meets a measured zero, and both predictions of free movement meet a motion of a tenth of the unit's area.

The prediction is necessary rather than sufficient, which is why the one-dimensional case was worth running. Laves class B sits on a single mirror, so a move along that mirror is allowed, and `push_vertex` still does nothing there because its own construction yields no displacement. A zero-dimensional answer proves a control dead; a one- or two-dimensional answer says only that nothing forbids it. We record one wrong reading of our own, since it read exactly like a finding: the first version of this test counted the elements of each stabiliser and predicted that archimedean 4.8.8 could not move, which the same run falsified at a tenth of the unit. What forbids a motion is not that something holds the point still but what its linear part does to a direction, so the test became the rank of the stacked matrices `L − I`. A count is not a fixed subspace.

## Crystallography's own answer

Everything so far treats symmetry as a question about geometry: propose motions, test them, take orbits. The crystallographic literature on tilings largely does not proceed that way. It encodes the tiling combinatorially, using Delaney–Dress symbols, due to Dress and Delaney and carried into working software by Delgado-Friedrichs, and reads the group off the encoding instead of searching for it.

The construction is easier than its name. Cut every tile into triangles by joining its centre to each vertex and to each edge midpoint, so that every triangle, called a chamber, records one incidence of a vertex, an edge and a tile; there are four chambers per edge. Each chamber has exactly three neighbours: one across the line to the tile's centre (same edge, other vertex), one across the line to the vertex (same vertex, other edge), and one across the edge itself (same vertex and edge, other tile). Those three swaps are involutions, since performing one twice returns you where you began. Add two integers recording how many times you must alternate a pair of swaps to come home, and the tiling is described. The symbol proper is that structure divided through by the symmetry group, leaving a handful of chambers carrying integer labels, with no coordinate anywhere in it.

The property that matters to us is testable, so we tested it. Our classes come from geometry, so an edit lowering the symmetry re-derives them, where a combinatorial encoding knows nothing of position and should not move. On `laves 3.3.4.3.4`, nudging one vertex class by five hundredths shifts a tenth of the unit's area and takes the classes from one tile, `A B`, `a b` to two tiles, `A B C`, `a b c d e`, while the combinatorial fingerprint is identical either side: the same tile corner counts, the same vertex degrees, the same edge incidences, the same 428 flags. On `archimedean 4.8.8` the same edit moves a quarter of the unit and neither answer changes, which is consistent rather than a counter-example. A symbol-based labelling would give us for nothing the stability that chaining currently works around. Our first attempt at that measurement found nothing at all, and the reason is worth keeping: it nudged every vertex class at once, which on laves amounts to translating the design, so every symmetry survived and both answers came back unchanged. One of this round's own hunts had already recorded that trap about its own fixtures. The committed probe now asserts that the ground moved before it reads anything.

## What each costs to run

Bounds are a shape rather than a price, and both alternatives are small enough to implement roughly and time. The wallpaper detection written for this note works modulo the lattice, which removes the boundary problem that makes a finite patch awkward: reduce every vertex into the fundamental cell, and a candidate isometry is a symmetry exactly when the reduced point set maps onto itself. Candidate centres are the vertices, the edge midpoints and the tile centres; candidate orders are two, three, four and six; candidate mirrors run through those centres along the lattice directions and their bisectors. The combinatorial timing builds the chambers and the two involutions the incidence answers directly. All three ran on the same designs, on this machine, in one pass.

| design | ours | wallpaper detection | chamber build | ours ÷ wallpaper | candidates tried | chambers |
|---|---:|---:|---:|---:|---:|---:|
| laves 3.3.4.3.4 | 0.78 s | 6.1 ms | 0.73 ms | 128× | 352 | 428 |
| hex-slice 3 | 0.36 s | 7.2 ms | 0.35 ms | 50× | 216 | 204 |
| hex-slice 4 | 0.31 s | 4.2 ms | 0.45 ms | 74× | 288 | 272 |
| hex-slice 6 | 1.83 s | 16.5 ms | 0.47 ms | 111× | 336 | 288 |
| archimedean 4.8.8 | 0.30 s | 3.6 ms | 0.47 ms | 84× | 208 | 284 |
| archimedean 3.12.12 | 0.94 s | 4.8 ms | 0.55 ms | 194× | 312 | 336 |
| archimedean 3.6.3.6 | 0.29 s | 3.8 ms | 0.44 ms | 77× | 216 | 264 |
| square-colouring 5 | 2.75 s | 8.2 ms | 0.72 ms | 335× | 360 | 432 |
| hex-colouring 4 | 4.05 s | 16.3 ms | 0.85 ms | 249× | 416 | 524 |
| hex-colouring 7 | 19.08 s | 23.8 ms | 1.17 ms | 803× | 728 | 696 |

The practical shape of the answer is three orders of magnitude, and it widens with the design: what we do costs between a third of a second and nineteen seconds, a bounded wallpaper enumeration costs between four and twenty-four milliseconds, and building the combinatorial structure costs under a millisecond and a half throughout. The ratio grows from 50 on the smallest design to 803 on the largest, which is the complexity difference showing up as wall clock rather than as notation.

Two honest deductions from those figures, since neither implementation is complete. The wallpaper timing tests the vertex set only, so it would accept a motion that moved an edge while fixing every vertex, and it omits glide reflections; a full implementation must test edges too and will cost more, though the number of candidates is unchanged and the per-candidate test stays a hash lookup. The chamber timing stops short of the canonical form, which is the quadratic step in the number of chamber orbits, and that number is small (single figures for the simpler cases) against the hundreds of chambers listed. So both columns are lower bounds. Even generously multiplied, neither approaches the seconds that the present method spends.

The nineteen seconds is worth its own sentence. `hex-colouring 7` was not among the designs anybody had timed: `docs/TOPOLOGY.md` records builds of 0.75 to 4.4 seconds, and that document is right that the cost tracks the shape rather than the element count, but nobody had run it far enough up the catalogue to find a design that takes nineteen. The Topology tab builds off the main thread, so this is not a frozen window, yet it is nineteen seconds before anybody can aim an edit.

## The bounds behind those numbers

For the present method, in the quantities that drive it (`n` core tiles, `c` corners across them, `V` vertices, `E` edges, `|S|` candidate transforms, `P(c)` for one polygon intersection):

| step | where | bound |
|---|---|---|
| build and index the patch | `Topology.__init__` | O(n·c) |
| candidate transforms from shapes | `ShapeMatcher`, pairwise within a shape group | O(n²·c) |
| drop duplicates | `_remove_duplicate_symmetries` | O(\|S\|²) |
| tile classes | `_find_tile_transitivity_classes` | O(\|S\|·n²·P(c)) |
| vertex classes | `_find_vertex_transitivity_classes` | O(\|S\|·V²) |
| edge classes | `_find_edge_transitivity_classes` | O(\|S\|·E²) |

The quadratic terms are not incidental: `_match_geoms_under_transform` scans the candidate partners linearly, once per transform per element, so every orbit question costs a sweep of everything else. With `|S|` itself growing as `n·c`, the dominant term is O(n·c·(V² + E²)), and since `V` and `E` are themselves O(n·c) here, the worst case is cubic in the size of the unit. That bound was checked as a ratio across the ten designs: per element the cost varies by a factor of thirty-six, while per `|S|(V² + E²)` it varies by 3.4, seven of the ten sitting between 1.9 and 3.9 microseconds. The residual is the tile term the ratio leaves out.

The wallpaper route replaces the linear scan with a hash lookup and the open-ended generation with a bounded enumeration: O(V + E + n) candidates, O(V) expected for each test, so O((V + E + n)·V) overall, with orbits then falling out of a union-find in near-linear time and each class's fixed subspace costing a rank of two-by-two matrices. The combinatorial route is O(E) to build the chambers and their involutions, O(D²) to canonicalise where `D` counts chamber orbits, and O(1) for the labels, because the quotient is the orbits. Everything in that last route is integer arithmetic, which is why no tolerance appears in it anywhere.

## Where each fails

Ours fails by being a search without a theory. The candidate set is whatever the prototile and the tiles happen to suggest, so a symmetry present in the tiling but in no single tile's own shape can be missed, and nothing about the result would look any different if it were. It also requires a gap-free tiling, which is why `Topology` refuses every weave at the default strand width and every design carrying a tile inset.

A wallpaper approach fails differently. Detection is tolerance-bound, and this geometry is floating point the library already has to clean, so a group found at one tolerance and not another is a label that flickers. After an edit the symmetry genuinely drops, one nudge taking laves from two edge classes to five in the measurement above, so recomputing the group each time moves the labels under the person, which is the fault chaining was adopted to avoid; the group would have to be computed once and then carried.

The combinatorial route fails on the same gap-free requirement as ours, so weaves stay outside it and the wallpaper route remains the only one of the three that reaches them. An edit changing incidence rather than position, inserting a vertex or merging edges at one, changes the symbol, and rightly so. The symbol carries no geometry at all, so adopting it means holding a combinatorial object and a geometric one and keeping them in step, in a codebase whose commonest defect has been exactly two stores of one fact disagreeing. And it is not available as a dependency: the reference implementation is Java, and the vendored library has no such code, so this would be an implementation here or upstream rather than an import.

## What is not measured

Whether the transform set the library assembles is a group. Nothing here tested closure under composition or inverses, and if it is merely a collection of matchings that happen to work, then what is said above about stabilisers is true of what we compute rather than of the design's own symmetry. The difference would surface first as a site symmetry reported smaller than it really is, which is to say as a control offered to somebody that nothing can move. That test needs no new machinery and would take an afternoon, and we would want it run whatever we then chose to build.
