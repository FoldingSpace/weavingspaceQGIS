# The tiling grid's disc is larger than any rotation needs

*A note offered to weavingspace, from the QGIS plugin that vendors it.
Measured 2026-09-04 against upstream 0.0.7.89 at commit 6190917.*

## What the code does now

`_TileGrid` lays its translation centres over a disc, and the
constructor's own docstring says why: "The tiling is extended
sufficiently to allow for its application at any rotation." The radius
is the distance from the centre to a **corner** of the region's
oriented bounding rectangle:

    corner = geom.Point(self.oriented_rect_to_tile.exterior.coords[0])
    radius = self.centre.distance(corner)

That promise is worth keeping — eight of the thirty-three
`get_tiled_map` call sites in the examples pass a non-zero rotation.

## Why the radius can be smaller without weakening it

Rotation about a point **preserves distance from that point**. So the
ground a tiling must cover to serve *any* rotation is only the radii
the region actually occupies — not the circumscribed disc of a
rectangle. A region touches its bounding rectangle's **edges** by
construction and its **corners** only by coincidence.

Taking the radius from the buffered hull the rectangle was built
around, rather than from the rectangle's corner, keeps the rotation
promise exactly and drops the placements that lie over ground nothing
occupies.

## The trap, which cost us a wrong first version

`_get_grid` takes its meshgrid origin from `extent_in_grid_space.bounds`:

    l = _l - (w - _w) / 2

so the extent does **two jobs** — it says which cells are wanted *and*
it phases the lattice. Shrink the one polygon and every tile moves by a
sub-cell offset. Measured on `crosses 4` at spacing 500: both radii
drew 2,772 tiles and **2,622 of them differed**, every one still
touching the region. Nothing was lost; the whole pattern had moved,
which is a different map rather than a cheaper one.

Worth knowing: the shift appears only when `ceil(2R)` changes by an odd
amount, so on roughly half of all designs a naive version looks
perfectly correct.

The fix is to keep the two jobs apart — the original extent still
phases the lattice, and a second, smaller one decides which cells are
wanted.

## What it is worth

Packaged Auckland data, 155 zones, EPSG:2193:

    placements kept          77.3% on average, best 66.7%
    Tiling() + get_tiled_map 1.152s -> 0.929s  (spacing 250)
      _TileGrid.__init__     0.411s -> 0.340s
      get_tiled_map          0.451s -> 0.366s  (fewer tiles reach it)

The overlay falls too, because the tiles that are never built are
exactly the ones it would have clipped away and discarded.

## How we checked it

`tools/probes/the_smaller_disc_tiles_the_same_map.py`, in the plugin's
repository: 8 designs x 2 spacings x 4 rotations (0, 30, 45, 90) =
**64 comparisons, 0 differing**, compared tile by tile on id and
geometry bytes rather than in aggregate.

We carry it as patch 4 in `tools/vendor_weavingspace.py`, which
re-applies it at every re-vendor and names itself if the anchor moves.
We would rather not carry it.
