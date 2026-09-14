# Upstream's Topology rewrite, measured against what the plugin carries

Written 2026-09-14, at the maintainer's prompting ("upstream has been working
on this, perhaps in a branch"), after a profile of the vendored `Topology`
showed it spending its time in per-object shapely calls inside Python loops and
before any patch to those loops was written. The rule it follows is this
project's own: check what upstream has done before reimplementing, and OFFER a
new version rather than taking one silently. Nothing here has been vendored.

Every figure below names its instrument, and every timing was taken under
QGIS 4.0.3's own Python (3.12.11, numpy 1.26.4), one design and one library per
process, in cpu seconds: `tools/probes/how_upstream_s_topology_rewrite_compares.py`.

## What the branch is

`origin/experimental` stands 17 commits past the 6190917 we vendor, at 329cd2f
(2026-09-11), and `main` has not moved. The rewrite is structural rather than a
tune-up: symmetries are found by snapping a set of check points onto the lattice
and asking which rotations (orders 6, 4, 3, 2) and which mirrors (along the
translation vectors and their bisectors) carry the check points onto
themselves; the radius-1 patch that the vendored code keeps and matches every
tile against is dropped once the vertices are found; a tile's centre is its
centroid (5e43dc2), which is the same observation as our patch 7; and `Tile`,
`Edge` and `Vertex` move to `elements.py`, with plotting in `topology_plot.py`.

## It is an order of magnitude faster, and it builds our weave scaffolds

Tilings at their catalogue defaults:

    design              vendored (6190917 + patches)   experimental   classes (e/v)
    laves 3.3.4.3.4                0.78 s                  0.19 s        2/2  both
    archimedean 4.8.8              0.30                    0.08          2/1  both
    hex-slice 3                    0.35                    0.08          1/2  both
    hex-slice 6                    1.83                    0.10          1/1  both
    hex-colouring 4                4.04                    0.19          1/1  both
    square-colouring 5             2.73                    0.15          1/1  both
    crosses 4                      1.44                    0.34          1/1 against 2/3
    hex-colouring 7               19.35                    0.32          1/1  both
    chavey K                      14.01                    0.54          5/3  both

Thin weaves at strand width 0.75, through the plugin's own scaffold, with the
holes cut by the measured cell and whole (docs/TOPOLOGY.md):

    design                  holes   vendored          experimental   classes (e/v)
    plain weave a|b         cut        3.5 s              0.9 s      10/7  both
                            whole      5.2                0.4         2/1  both
    twill weave a|b         cut       72.9                4.3         6/4 against 12/8
                            whole     71.7                4.2         6/4 against 12/8
    basket weave ab|cd      cut       29.2                6.7        31/21 both
                            whole     65.3                4.2         8/4  both
    plain weave abcd|efgh   cut       28.6                 --        31/21
                            whole    230.7                 --         2/1
    plain weave abcde|fghi  cut      228                 32.4       143/95 both
                            whole   >1800 (not done)     23.6         2/1 against 4/2

THE BRANCH BUILDS WHOLE HOLES WITHOUT PATCH 7, on every weave tried, which is
the construction our patch exists to make possible.

AND IT EXPOSES A REGRESSION IN OUR OWN WORK. Whole holes (74e821b) make the
vendored construction much slower on large plain weaves -- 28.6 to 230.7 s on
`plain weave abcd|efgh`, and more than half an hour of cpu on `plain weave
abcde|fghi`, where it took 228 s with the holes cut -- so the Topology tab of an
eight- or nine-element plain weave, which used to land in minutes, does not
land. That was a defect owed a repair before the next candidate whatever is
decided about the branch, and it is repaired: see "Patch 8" below.

## Where the two disagree

**`twill weave a|b`: 12 edge and 8 vertex classes against 6 and 4**, and
`plain weave abcde|fghi` with whole holes 4 and 2 against 2 and 1 (the vendored
figure taken with patch 8, which is the only way it finishes). 12 and 8 is
exactly what the plugin's own warp-and-weft refinement gives (orbits under the
direction-preserving subgroup, C-353), so the branch's symmetry group on a twill
lacks whatever carries warps onto wefts -- a diagonal mirror or a glide
reflection, neither of which the branch's mirror directions (parallel to the
translation vectors or along their bisectors) obviously reach. Not established:
which transform is missing, and whether the branch is wrong or deliberately
narrower. Worth asking upstream, with this design as the example.

**`crosses 4`: 2 edge and 3 vertex classes against 1 and 1.** Probably a
difference of DEFINITION rather than of symmetry. Measured from the geometry
alone, every one of the tiling's 16 vertices where four tiles meet has the same
figure (four right angles), which is consistent with the vendored single vertex
class; the tiling's other corners, where a convex corner meets a neighbour's
reflex one, have two tiles and are not tiling vertices. A count that includes
those corners would read three.

## What adopting it would cost the plugin

Audited by comparing the members of `Topology`, `Tile`, `Edge` and `Vertex`
between the two copies and searching the plugin for every one that went:

- **Two changes before it imports under QGIS at all**: `topology_plot.py`
  imports matplotlib unguarded (our patch family 1 gains a member), and
  `topology.py:510` calls `np.atan2`, which NumPy 1.26 has not -- `np.arctan2`
  is the same function in both, a one-line change worth offering upstream.
- **Our vendoring tool applied 13 of its 15 patches** before patch 8 existed;
  the two that did not are 1d (topology's matplotlib import, which moved) and 7
  (our centroid, which the branch has adopted), both made unnecessary by the
  branch, as patch 8 would be.
- **`tile_matching_transforms` comes back empty.** The warp-and-weft refinement
  (`keep_warp_and_weft_apart`, its pool of pairwise composites and the control
  that it reproduces the library's classes), the drawn symmetries and the
  `push_vertex` gate all read it. The branch keeps `orbits` instead, which is a
  classification rather than a set of transforms.
- **`base_ID` is gone from tiles, edges and vertices** (24 uses in the plugin),
  the patch copies it named no longer existing.
- **The dual moves out of `Topology`** (`dual_tiles`, `generate_dual`,
  `get_dual_tiles`, 6 uses) into `tiling_utils.get_dual_tile_unit`, whose own
  docstring says it is "not remotely guaranteed to work"; our `complete_dual`
  would have to be rebuilt on something.
- **`transform_geometry` takes `new_topology` and `apply_to_tiles` flags**
  ahead of the selector, and edges are keyed by their full vertex-ID lists.

## Patch 8: the regression's cause, and its repair on the vendor we carry

Profiled, the whole-holes build of `plain weave abcd|efgh` spent 312 of 333
seconds in `Topology._match_geoms_under_transform`, 243 of them in the edge-class
search: every comparison rebuilt the candidate edge's LineString to take its
centroid (4.3 million LineStrings) and re-applied the transform to the source
(3.7 million affine transforms), so the search grew as transforms x edges x
edges, and whole holes keep more transforms. Vendor patch 8 (`a7f59e3`) moves the
source once, holds an edge list's centroids, and asks one array
`shapely.distance` for the first candidate in order, skipping a tile candidate
only where its box cannot meet the source's. It builds the SAME topology --
every label, transitivity class and kept transform, on eleven designs, with a
sabotage control that reads DIFFERS
(`tools/probes/does_a_faster_match_build_the_same_topology.py`):

    design                          vendored   patch 8
    hex-colouring 7                   17.5 s     2.6 s
    chavey K                          12.6       6.5
    twill weave a|b, whole            69.4      13.1
    basket weave ab|cd, whole         63.1      13.8
    plain weave abcd|efgh, whole     235.3      21.3
    plain weave abcdef|ghijkl, whole  >600     164.8
    plain weave abcde|fghi, whole    >1800     197.5

PATCHES 9 AND 10 followed the next two profiles (`4a1e4d0`, `9a50b7f`): the
symmetry filter compared against every unique at once, and the two vertex scans
asking one array distance each, byte-identical in structure. With all three,
`plain weave abcde|fghi` with whole holes builds in 68.5 s, `hex-colouring 7` in
1.7 s, and `twill weave a|b` with whole holes in 6.2 s.

The edge lines built fall from 85,800 to 1,575 on `plain weave a|b`, which is
T x E + E for its 44 transforms and 35 base edges, and that count is what the
guard holds (`test_a_topology_match_does_its_work_once`).

## What this suggests, for the maintainer to decide

**FOR 0.24.4: PATCH 8, NOT THE BRANCH.** A re-vendor onto an unmerged branch
that changes six things the plugin leans on is not candidate-shaped work, and
the branch's own history carries a revert for breaking some tilings (5039818);
patch 8 closes the regression exactly, on the construction we have measured.

**FOR 0.24.5: TAKE THE REWRITE WHEN IT MERGES**, as its own piece of work with a
differential over the catalogue: still five times on the slowest tiling after
patches 8-10, nine-strand weave scaffolds in 24 s where they leave 68, and the
scaffolds building without patch 7 -- and retire patches 7 to 10 with it. Owed
before then, and upstream's to answer: the twill's missing symmetry, a way to
have the transforms back (or orbits the refinement can be rebuilt on), and the
`np.atan2` spelling.
