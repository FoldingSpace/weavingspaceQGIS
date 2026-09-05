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

---

# And a second, opt-in step: let a caller name its rotations

The reduction above keeps the promise to serve **any** rotation. A
caller that knows it will never rotate can do better still, and the
change is additive.

## The shape

    Tiling(tileable, region, as_icons=False, rotations=None)

`None` means "any" and is exactly today's behaviour, so nothing changes
for a caller that does not know. Given a tuple, the wanted ground stops
being a disc: a tiling rotated by *r* about the centre puts the tile
placed at *p* at rot(*p*), so the placements worth laying are those
whose image lands on the region — *p* ∈ rot⁻¹(buffered region), unioned
over the angles declared. With `rotations=(0,)` that is the region's
own shape.

## What it is worth, and what it costs when broken

    placements kept   63.8% of what the reduction above already keeps
                      (so about half the original)
    worker            0.929s -> 0.796s at spacing 250
                      (1.152s before either change)
    at rotation 0     12 comparisons, 0 differing

**It is a promise the caller can break, and we drove that
deliberately.** A tiling told `(0,)` and then asked for 45 or 90
degrees comes back **short at the edges** — in 12 of 12 cases at
spacing 250. Worth knowing for anyone testing it: a small design at a
coarse spacing does **not** show this. `basket weave ab|cd` at spacing
500 came back identical at 30 degrees, because few placements and a
nearly round wanted area leave nothing to lose.

## Why the plugin can make the promise

Its Rotate modifier calls `unit.transform_rotate`, which turns the
prototile and **re-derives the translation vectors** — the whole
lattice turns before the grid is laid. Your `rotation` argument turns a
finished tiling about the grid centre instead. Same picture, a
different point in the pipeline.

Proved by `tools/probes/the_rotation_hint_keeps_the_map.py`, which
drives both the honest arm and the broken one.
