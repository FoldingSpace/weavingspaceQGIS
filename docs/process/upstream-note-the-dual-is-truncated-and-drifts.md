# The dual tiling: two small defects in `Topology`, with measurements

*A note for the weavingspace project, written 2026-09-05 from the QGIS
plugin that vendors it. Everything below was measured against the
vendored tree at `0.0.7.89 (6190917)`, on `laves 3.3.4.3.4` at spacing
500 unless a design is named.*

*The plugin works around both in one function of its own,
`topology_edits.complete_dual`, and carries a canary,
`test_the_library_still_truncates_and_drifts_the_dual`, that asks the
library directly whether each defect is still there -- so the day
either is fixed upstream the suite says so and the workaround comes
out. Nothing here waits on an answer.*

`generate_dual` already carries the note that it still needs "to
ensure that this finds a set of dual tiles that exhaust the plane". As
far as we can measure, the vertex selection is fine: `dual_tiles` holds
one polygon per vertex of the unit on every design we tried. What
stops the dual exhausting the plane is two things downstream of it.

## 1. `get_dual_tiles` returns as many rows as the SOURCE has tiles

    def get_dual_tiles(self) -> gpd.GeoDataFrame:
      n = len(self.dual_tiles)
      return gpd.GeoDataFrame(
        data = {"tile_id": list(self.tileable.tiles.tile_id)[:n]},
        geometry = gpd.GeoSeries(self.dual_tiles.values()),
        crs = self.tileable.crs)

The `tile_id` column is the source's ids sliced to the dual's count,
so wherever the dual has MORE tiles than its source the data column is
shorter than the geometry, and pandas aligns the frame to the data:
the frame has as many rows as the source has tiles, and the rest of
the dual is dropped without a word.

A dual has one tile per vertex of the unit, which by Euler on the
torus is `edges - faces`, and that exceeds the source's tile count on
many designs. Measured, `dual_tiles` against `get_dual_tiles()`:

    laves 3.3.4.3.4       6 held    4 returned    covers 77% of the cell
    archimedean 4.8.8     4 held    2 returned    covers 50%
    hex-colouring 3       6 held    3 returned    covers 50%
    hex-slice 4           4 held    4 returned    covers 100%
    square-slice 4        2 held    2 returned    covers 100%

The three short ones are exactly the designs whose dual has more
tiles than the source. Labelling the dual's tiles with their own ids
-- `a`, `b`, `c` in vertex order, say -- rather than the source's
would return every row.

## 2. Tile centres drift between copies, so adjacent dual tiles disagree about their shared edge

A dual tile's corners are the centres of the tiles around its vertex,
and `Tile.centre` comes from `tiling_utils.get_incentre`, which for a
polygon that is not regular returns `polylabel.polylabel(shape)`. That
is a numerical search, and run separately on two copies of one tile
it lands in slightly different places: on the default design the
largest difference between a copy's centre and its base tile's centre
translated is about a unit at spacing 500.

Two consequences. Adjacent dual tiles share an edge between two tile
centres, and where the two tiles each computed that edge from a
different copy the edges do not coincide: with every dual row present
the default design's dual still left four slivers totalling 577 units
in a 250,000-unit cell, 0.23%, lying along dual edges. And
`Topology(dual)` -- the dual promoted to a `TileUnit` -- then raised
`ValueError: not enough values to unpack (expected 2, got 1)` in
`get_updated_edges_from_merge`, because the corner matching works at
`RESOLUTION = 1e-6` and those corners are a unit apart. The same
tiling built from the catalogue's own `archimedean 3.3.4.3.4` builds
perfectly well, which is what said the refusal was the dual's
construction and not the tiling.

Taking each copy's centre as its BASE tile's centre translated by the
copy's offset -- the two shapes' centroids differ by exactly the
translation -- removes both: coverage becomes 1.000000 on every design
tried, and `Topology` builds a topology of the dual of each of them,
the default design included. For regular polygons `get_incentre`
already returns the centroid, which is why the hex-slice families
never showed either symptom.

## What we carry meanwhile

`complete_dual(topology)` builds the frame from `dual_tiles` with
translation-consistent centres, and both the map and the GeoPackage's
`weavingspace_dual_no_crs` table come from it. It is deleted, and
`get_dual_tiles()` used directly, when the canary above fails.
