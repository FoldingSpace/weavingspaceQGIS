# A constructor for a Tileable from tiles you already have

*A note for the weavingspace project, written 2026-09-01 from the QGIS
plugin that vendors it, and SENT the same day by the maintainer.
Everything below was measured against the vendored tree at
`0.0.7.89 (6190917)`.*

*What happens next is not ours to decide, and we are not waiting on it
to know: `test_the_library_still_cannot_build_a_unit_from_tiles` asks
the library directly whether the gap is still there, so the day a
constructor arrives -- in either of the shapes below, or a third we
did not think of -- the suite says so and the workaround comes out.*

## What we wanted to do

Tile a map with the DUAL of a design rather than with the design. The
dual is already there: `Topology.generate_dual()` fills `dual_tiles`
and `get_dual_tiles()` hands back a GeoDataFrame with `tile_id`, and
because the dual of a periodic tiling repeats on the same lattice, the
source unit's own vectors describe it exactly.

## What stopped us

There is no way to say "here are the tiles and the vectors, make me a
Tileable". `Tileable.__init__` takes keyword arguments, writes them
onto the instance, and delegates to `_setup_tiles()`, which dispatches
on `tiling_type`:

    match self.tiling_type:
      case "cairo":
        return geometries._setup_cairo(self)
      ...

An unrecognised type returns a message, and `__init__` then calls
`_setup_default_tileable()` — so a `tiles=` keyword is accepted,
stored, and quietly overwritten by a default unit. We measured that
rather than assuming it.

## What we did instead, and why we would rather not

We copy the source Tileable, replace its `tiles` frame with the dual's,
re-derive the prototile from the vectors and call
`_setup_regularised_prototile()`. That is reaching into the library's
own construction from outside it, which is exactly the boundary this
plugin otherwise keeps: behaviour that belongs to the tiling belongs
upstream.

It does work. Measured through `Tiling(...).get_tiled_map()` over a
3 km region at spacing 500: the promoted dual lays 181 tiles for
`laves 3.3.4.3.4`, 203 for `hex-slice 4`, 146 for `hex-slice 3` and 84
for `archimedean 4.8.8`. What we cannot do from outside is keep it
working: the four lines we lean on are private, and any change to how
a unit is set up will break them silently.

## What we suggest

Either of these would let us delete our version:

1. **`TileUnit.from_tiles(tiles, vectors, **kwargs)`** — a classmethod
   that builds a unit from a GeoDataFrame carrying `tile_id` and a
   set of translation vectors, doing whatever `_setup_tiles` would
   have done afterwards (the prototile, the regularised prototile, the
   CRS and spacing bookkeeping).

2. **`Topology.dual_as_tileable()`** — the same thing for the one case
   we actually want, which has the advantage that the vectors do not
   have to be passed at all: the dual's lattice is the source's.

We would be glad to send either as a patch; say which shape you would
accept and it will follow. The plugin's own version, with the
measurements and the fallback behaviour, is in
`weavingspace_qgis/topology_edits.py` under `dual_as_tileable`.

## How you will know we have stopped needing it

Our suite carries a canary,
`test_the_library_still_cannot_build_a_unit_from_tiles`, which asserts
that the gap is still there — it looks for `TileUnit.from_tiles`, for
`Topology.dual_as_tileable`, and for a `tiles=` keyword the setup
honours. The day any of those exists, that test fails, and the failure
is the signal to delete our assembly and use yours.

## One thing that is not a request

`Topology.plot_tiling_symmetries` draws through matplotlib. We cannot
call it: macOS code-signing refuses PyPI C extensions inside the signed
QGIS process, so the plugin has no matplotlib at all and draws
everything itself. That is our constraint rather than a fault in the
library, and we mention it only because it is why we read
`tile_matching_transforms` directly rather than asking you to draw. The
data in those Transform objects — the kind, the angle, the centre —
was enough to draw the rotation centres and mirror lines ourselves.
