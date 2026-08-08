# Test data

`imd-auckland-sa2-2018.gpkg` — Index of Multiple Deprivation scores and
domain sub-scores for Auckland statistical area 2 units, 2018, as
distributed with the weavingspace library itself
(`examples/data/` in github.com/DOSull/weavingspace). It is packaged
here so the real-data test always runs rather than skipping on
machines where the file happens to be absent.

Why this file and not more synthetic squares: 155 features in a real
projected CRS (EPSG:2193), multipolygon geometry, areas spanning two
orders of magnitude, and genuine null values in some attributes.
Between them those exercise paths the synthetic grid never reaches —
the CRS strip-and-reattach around the worker thread, the "no data"
class, and auto-spacing on polygons of wildly uneven size.

It is not shipped in the plugin zip; `build.py` packages only
`weavingspace_qgis/`.

`landcover-categorical.gpkg`, `landcover.qml`, `landcover-alt.qml` —
generated fixtures for the categorical tests, built by
`tools/make_test_fixtures.py` (run it again only when they need to
change; the tests assert on the exact colours and labels). The
GeoPackage is a 12 x 12 parcel grid in EPSG:2193 with three
categorical fields of different shapes, one numeric field, and nulls
in every column. The two QML files are importable colour mappings for
the same field, covering different class sets on purpose, so a test
can shift an element from one mapping to the other, and hold two
elements on different mappings at once.
