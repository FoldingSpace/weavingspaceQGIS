# `get_clean_polygon` may return a MultiPolygon, and `get_corners` asks it for `.exterior`

A note for the weavingspace project, in the same spirit as the five
beside it: a small, reproducible inconsistency, with the measurement
that found it and no request attached beyond "is this what you
intend?".

## What happens

Two lines of `Topology._initialise_points_into_tiles` disagree about
what a shape can be:

    shapes = self.tileable.get_local_patch(r = 1, include_0 = True).geometry
    shapes = [tiling_utils.get_clean_polygon(s) for s in shapes]
    ...
    corners = tiling_utils.get_corners(shape, repeat_first = False)

`get_clean_polygon` ends with `return gridify(geom.Polygon(corners))`,
and `gridify` is `shapely.set_precision(gs, grid_size = RESOLUTION)`.
`set_precision` MAY SPLIT a polygon that pinches at the grid's scale,
so the cleaner can hand back a `MultiPolygon`. `get_corners` then does

    corners = [geom.Point(pt) for pt in shape.exterior.coords]

and raises `AttributeError: 'MultiPolygon' object has no attribute
'exterior'`.

The same call has a second failure mode on other input, from the same
`set_precision`:

    shapely.errors.GEOSException: TopologyException: unable to assign
    free hole to a shell at -433.01270299999999 1000.000002

## What was measured, rather than read

A `Tileable` whose tiles include some thin, many-cornered pieces, at
`RESOLUTION = 1e-06`. Of a 154-shape local patch, two shapes clean to
multi-part, and both are copies of ONE tile:

    shape  53 is tile 'z0' (copy 2)
      before  Polygon, area 378886.116, 8 corners, valid True
      after   MultiPolygon, 2 parts, areas [81189.882, 297696.234]
      the split loses 0.000750 of area

    the same tile in the BASE FRAME cleans to a Polygon

That last line is the whole of it. The tile is fine where it sits; two
of its seven translated copies are not. The polygon is valid before the
snap and valid after `get_corners` rebuilds it -- the split is
`set_precision`'s alone, and it is a pinch collapsing rather than a
change of shape, which is why the area moves by less than a thousandth
of a unit.

So a lattice translation is enough to move a near-pinch onto the
precision grid, and whether a given copy survives is a property of the
offset rather than of the tile.

## Why this is reported rather than worked around

It can be worked around from outside, by not handing the library
geometry that pinches at 1e-06 -- and that is what the caller here will
do. But the disagreement is INSIDE the library and does not depend on
who supplied the tiles: any tiling with a tile that pinches at the
resolution can reach it, and the failure arrives as an
`AttributeError` about `.exterior` rather than as anything a reader
would connect to precision.

Two shapes of fix suggest themselves, and which is right is the
project's own call. `get_corners` could take the largest part, or
raise something that names the cause. Or `get_clean_polygon` could
promise a single part -- taking the largest part of what
`set_precision` returns -- so that its own name is true.

## How to reproduce

The caller is a QGIS plugin that vendors this library; the shapes are
gap-filling pieces added to a weave so that `Topology` will accept it.
Nothing about the reproduction needs the plugin: it needs a `Tileable`
with a tile that pinches at `RESOLUTION`, and a patch big enough to
include a translated copy that lands on the grid.
