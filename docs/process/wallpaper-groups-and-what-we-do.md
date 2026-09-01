# Wallpaper groups, crystallography, and what this plugin actually does

Measured 2026-09-01 at commit `6d59e67`, by
`tools/probes/does_site_symmetry_predict_what_can_move.py`. It asks whether a wallpaper-group approach could
determine the symmetries and topology we use in the Topology tab, how
that compares with what the vendored library already does, and how
both compare with the crystallographic treatment the same mathematics
has in its own literature.

The short answer is that we are already doing crystallography without
naming it, that naming it would buy one thing worth having
immediately, and that one question underneath all of it has not been
measured and should be before anybody builds anything.

## What the library does today

`Topology` does not classify a design into a wallpaper group. It
**assembles candidate isometries and keeps the ones that work**:

- the two lattice translations, from `tileable.get_vectors()`;
- the prototile's own symmetries, from `ShapeMatcher(ptile)`;
- each tile's own symmetries;
- the shape-matching transforms between tiles in one shape group,

with duplicates removed by `_remove_duplicate_symmetries`. The
transitivity classes are then the orbits of tiles, vertices and edges
under whichever candidates map the tiling to itself. The labels an
edit is aimed with — `a`, `b`, `A`, `B` — are those orbits, indexed.

So the group is computed. What is missing is its NAME and its
STRUCTURE, and the second of those is where the value is.

## What was measured

Six designs, built through `catalog.make_unit` — the door the dialog
uses — and read through `topology_edits`.

| design | transforms found | rotation orders | classes | vertex class site symmetry | fixed space | `push_vertex` moves |
|---|---|---|---|---|---|---|
| laves 3.3.4.3.4 | 24 | 2, 4 | 1 tile, `A B`, `a b` | A: ±90° | 0D | — |
| | | | | B: one mirror | 1D | — |
| hex-slice 3 | 27 | 3, 6 | 1 tile, `A B`, `a` | A: 3-fold and mirrors | 0D | — |
| | | | | B: two mirrors | 0D | — |
| hex-slice 6 | 84 | 2, 3, 6 | 1 tile, `A`, `a` | 6-fold and mirrors | 0D | 1.5e-09 |
| archimedean 4.8.8 | 18 | 2, 4 | 2 tiles, `A`, `a b` | trivial | 2D | **0.103 of the area** |
| archimedean 3.12.12 | 32 | 2, 3, 6 | 2 tiles, `A`, `a b` | trivial | 2D | **0.130 of the area** |

Two findings come out of that table.

**The crystallographic restriction holds exactly.** Once the powers are
reduced — the raw 240°, 270° and 300° entries are elements of order 3,
4 and 6 — every rotation found is of order 2, 3, 4 or 6, which is the
restriction a periodic pattern obeys. A wallpaper approach would
therefore be enumerating precisely the space the present code searches
blind.

**Site symmetry predicts what a manipulation can move.**
docs/TOPOLOGY.md records that `push_vertex` moves nothing on laves
3.3.4.3.4 and hex-slice 3 because the incident unit vectors cancel,
measured at 1.5e-9. The crystallographic statement is stronger and
needs no arithmetic about neighbours: **a displacement must lie in the
fixed subspace of the vertex's site symmetry.** A rotation of order two
or more in the stabiliser leaves only the zero vector; two distinct
mirrors likewise; a single mirror leaves a line; a trivial stabiliser
leaves the plane. Every 0D prediction above matches a measured zero,
and both 2D predictions match a motion of a tenth of the unit's area.

**And it is necessary rather than sufficient**, which is why the 1D
case was worth running. Laves class B has a single mirror, so a move
along that mirror is permitted — and `push_vertex` still produces
nothing there, because that construction's own resultant vanishes. 0D
proves a control is dead; 1D or 2D says only that it is not forbidden.

**One wrong reading, recorded because it was mine.** The first version
of this test counted stabiliser ELEMENTS and predicted that archimedean
4.8.8 could not move, which the measurement immediately falsified: one
transform fixes that vertex and it moves by a tenth of the unit. What
forbids a move is not that something fixes the point but what its
linear part does to a direction, so the test became the rank of the
stacked `L - I` matrices. A count is not a fixed subspace.

## What each step costs

Written as bounds derived from the loops, and then CHECKED against a
measurement, because a complexity claim nobody ran is the same kind of
statement as a site named by reading.

The quantities: `n` core tiles, `c` corners over those tiles, `V`
tiling vertices and `E` edges in the core, `|S|` candidate transforms,
and `P(c)` the cost of a polygon intersection test.

### What we do now

| step | where | bound |
|---|---|---|
| build the patch and index it | `Topology.__init__` | O(n·c) |
| assign vertex and edge base IDs | `_assign_*_base_IDs` | O(n·c) |
| candidate transforms: lattice | `get_vectors` | O(1), four or six of them |
| candidate transforms: prototile and per-tile self-matches | `ShapeMatcher`, KMP over corner codes | O(n·c) |
| candidate transforms: pairwise within a shape group | `get_polygon_matches` | O(n²·c) |
| drop duplicates | `_remove_duplicate_symmetries` | O(\|S\|²) |
| tile classes | `_find_tile_transitivity_classes` | O(\|S\|·n²·P(c)) |
| vertex classes | `_find_vertex_transitivity_classes` | O(\|S\|·V²) |
| edge classes | `_find_edge_transitivity_classes` | O(\|S\|·E²) |
| the dual | `generate_dual` | O(V + E) |

The quadratic in V and E is not incidental: `_match_geoms_under_transform`
is a LINEAR SCAN over the candidate partners, once per transform per
element, so every orbit question costs a sweep of everything else.
With `|S|` itself O(n·c), the dominant term is

    O( n·c · (V² + E²) )

and since V and E are themselves O(n·c) on these designs, the worst
case is cubic in the size of the unit.

### The measurement that checks it

Ten designs, built through `catalog.make_unit`, timed with the
monotonic clock. If the bound has the right shape then time divided by
`|S|(V² + E²)` is roughly constant while time divided by `n` is not.

| design | n | c | \|S\| | V | E | build s | s/n | µs per \|S\|(V²+E²) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| laves 3.3.4.3.4 | 4 | 20 | 24 | 72 | 107 | 0.79 | 0.197 | 1.97 |
| hex-slice 3 | 3 | 12 | 27 | 31 | 51 | 0.36 | 0.121 | 3.78 |
| hex-slice 4 | 4 | 16 | 10 | 41 | 68 | 0.32 | 0.079 | 5.01 |
| hex-slice 6 | 6 | 18 | 84 | 31 | 72 | 1.99 | 0.331 | 3.85 |
| archimedean 4.8.8 | 2 | 12 | 18 | 54 | 71 | 0.31 | 0.153 | 2.14 |
| archimedean 3.12.12 | 3 | 18 | 32 | 64 | 84 | 0.95 | 0.317 | 2.66 |
| archimedean 3.6.3.6 | 3 | 12 | 16 | 40 | 66 | 0.30 | 0.100 | 3.14 |
| square-colouring 5 | 5 | 20 | 96 | 64 | 108 | 2.79 | 0.559 | 1.85 |
| hex-colouring 4 | 4 | 24 | 112 | 96 | 131 | 4.41 | 1.103 | 1.49 |
| hex-colouring 7 | 7 | 42 | 216 | 126 | 174 | 19.76 | 2.823 | 1.98 |

**Per element the cost varies by a factor of 36; per `|S|(V²+E²)` it
varies by 3.4, and seven of the ten sit between 1.9 and 3.9 µs.** So
the bound is the right shape, and the residual spread is the tile term
`O(|S|·n²·P(c))` this ratio leaves out — polygon intersections are the
expensive test and the cheap designs carry proportionally more of them.

It also settles a practical fact that was not previously written down:
**`hex-colouring 7` takes 19.8 seconds to build a topology**, against
the 0.75–4.4 s docs/TOPOLOGY.md records. The cost tracks `|S|`, which
grows with `n·c`, so the ceiling is not the element spinner but the
number of distinct shapes and their corners.

### What a wallpaper approach would cost

| step | method | bound |
|---|---|---|
| the lattice | already known from `get_vectors` | O(1) |
| candidate rotation centres | vertices, edge midpoints, tile centroids, cell fractions; orders restricted to 2, 3, 4, 6 | O(V + E + n) candidates |
| pre-filter a candidate | compare the multiset of neighbour distances about the centre | O(1) amortised, kills most candidates |
| test one surviving isometry | transform V points, look each up in a hash grid | O(V) expected, O(V log V) with a tree |
| candidate reflection axes | directions fixed by the lattice and the rotation orders found | O(V + E) candidates, same test |
| name the group | match generators against the seventeen | O(1), a table |
| orbits of vertices and edges | union-find under g generators, g ≤ 6 | O((V + E)·g·α) — near linear |
| site symmetry per class | stabiliser is at most the point group, order ≤ 12 | O(1) per class |
| fixed subspace per class | rank of the stacked 2×2 matrices `L − I` | O(1) per class |

The whole detection is therefore **O((V + E + n)·V)** worst case and
near linear in practice, against the present **O(|S|·(V² + E²))**. The
saving is not a constant factor: it comes from replacing a linear scan
per element per transform with a hash lookup, and from enumerating a
bounded candidate set instead of generating one blind.

**What that predicts, stated as a prediction rather than a
measurement.** For `hex-colouring 7` the present work term is about
216 × (126² + 174²) ≈ 1.0 × 10⁷ element tests. The wallpaper route
needs roughly (V + E + n)·V ≈ 3.9 × 10⁴ point lookups plus about
1.8 × 10³ union-find operations. The per-operation costs are similar —
both are an affine transform and a distance — so the expectation is
two to three orders of magnitude fewer tests, and seconds becoming
milliseconds. **Nobody has built it, so that figure is arithmetic on
the bounds and not a timing.**

### What the crystallographic step adds, and what it costs

Once the group and a normalised cell are in hand, classifying a point
by Wyckoff position is a table lookup after reducing its coordinates
into the cell: **O(V + E)** for the whole design, with the site
symmetry and multiplicity coming with the entry rather than being
computed. The asymmetric unit is then O(1) to state and O(V + E) to
select representatives for.

So the expensive step in every version of this is finding the group.
Everything the crystallography is FOR — which control is dead, which
displacement is allowed, what the minimal editable piece is — is
linear or constant once you have it.

## What a wallpaper-group approach would add

Naming is the least of it. Three things follow from holding the group
as a group rather than as a bag of matrices.

**A dead control can be greyed out with a reason, before it is tried.**
Today `push_vertex` draws a rail of zero length where the design
cancels it, which was itself a measured repair. With site symmetry in
hand the tab can say that a vertex sits on a 4-fold rotation and
nothing can move it — and say the same of an EDGE, whose midpoint site
symmetry governs whether a zigzag may be asymmetric or must be
antisymmetric about that point. Nobody has measured the edge case yet.

**The asymmetric unit is the honest thing to edit and to store.** A
plane group's fundamental domain is the minimal piece from which the
group regenerates everything, so editing there is
edit-once-replicate-everywhere by construction, and it is a smaller and
more durable record than a list of manipulations aimed at class
labels. That bears directly on the thing chaining works around: labels
move when a design's symmetry drops after an edit, while an asymmetric
unit plus a group is stable under its own edits.

**Colour symmetry is the same machinery, and we already have the
switch.** `ignore_tile_id_labels` is exactly the choice between the
uncoloured group and the colour-preserving subgroup. Our maps colour
tiles by element, so the group that matters for "one colour means one
thing" is the colour-preserving one, and the k-colour wallpaper groups
are the settled theory for it. Nothing in the code currently says which
of the two groups it is reasoning about at any moment.

## Where each approach breaks

**Ours breaks by being a search without a theory.** The candidate set
is whatever the prototile and the tiles happen to suggest, so a
symmetry present in the TILING but in no single tile's own shape can be
missed — and there is no way to notice, because the answer looks the
same either way. It also requires a gap-free tiling, which is why
`Topology` refuses every weave at the default aspect and every design
carrying a tile inset.

**A wallpaper approach breaks differently, and in ways worth naming
before anybody builds it.**

Detection is tolerance-bound, and this geometry is floating point the
library already has to clean; a group found at one tolerance and not
another is a label that flickers.

After an edit the symmetry genuinely drops — one nudge takes laves
from two edge classes to ten — so recomputing the group after every
edit moves the labels under the person, which is the exact fault
chaining was adopted to avoid. The group would have to be computed
once and CARRIED, with edits expressed relative to it.

And a weave is not a tiling, so isohedral machinery does not apply to
it. The pattern is still periodic, though, which means the wallpaper
group EXISTS for weaves where `Topology` refuses to answer at all.
That is the one place the new approach reaches ground the old one
cannot.

## What is worth building, and what is not yet decided

The cheap, high-value piece is not a classifier. It is **the fixed
subspace per class, computed from the transforms already found** —
about twenty lines, no new dependency, no re-vendor — which turns
three of this project's measured curiosities into a stated rule and
lets the tab explain a dead control rather than drawing an invisible
rail.

Naming the group properly, and moving class labels to standard
crystallographic ones, is a decision rather than a task: it changes
what is stored in every saved file and what a person is shown, so it
belongs in a grilling rather than in a commit.

## What was NOT measured, and it matters

**Whether the transform set is a GROUP.** Nothing here tested closure
under composition or inverses. If it is merely a set of matchings that
happen to work, then everything above about stabilisers is true of what
we COMPUTE and not necessarily of the design's true symmetry group, and
the difference would show up first as a site symmetry that is too
small — a control reported movable that nothing can move. That test is
short and should come before any of the work above.
