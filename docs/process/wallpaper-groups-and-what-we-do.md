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
