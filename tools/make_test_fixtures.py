#!/usr/bin/env python3
"""Generate the packaged categorical test fixtures.

Run under QGIS's own Python (the same environment the test suite
uses), from the repository root:

    QT_QPA_PLATFORM=offscreen ... <qgis python> tools/make_test_fixtures.py

It writes three files into tests/data/, all committed so the suite
never has to build them at test time:

* ``landcover-categorical.gpkg`` — a 12 x 12 grid of parcels in
  EPSG:2193 (a real projected CRS, like the Auckland dataset) carrying
  three categorical fields of different shapes: ``landcover`` with six
  classes in patchy blocks, ``zoning`` with four, ``period`` with three
  ordered-looking labels, plus one numeric field and a deliberate
  scattering of nulls in every column. Categorical symbology has more
  ways to go wrong than graduated symbology does — class sets change
  when the pattern moves, labels come from files, nulls need their own
  class — so the categorical integration test wants data with those
  shapes rather than the four tidy classes of the synthetic grid.
* ``landcover.qml`` and ``landcover-alt.qml`` — two importable
  colour mappings for the same ``landcover`` field, with colours and
  labels chosen to be unmistakable in a test (``#1b7837`` "Native
  forest" in the first, ``#31a354`` "Forest" in the second). They
  cover different class sets on purpose: the first omits ``bare`` and
  the second omits ``wetland``, so switching an element from one
  mapping to the other must change both the colours and which class
  falls back to an automatic colour. Having two of them is the point
  — the categorical integration test shifts an element between
  imported mappings, and between elements, which one file could not
  exercise.

Regenerate only when the fixtures need to change; the tests assert on
the exact colours and labels below, so a regeneration means updating
those assertions too.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "tests", "data")

from qgis.core import (  # noqa: E402
  QgsApplication, QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem,
  QgsCoordinateTransformContext, QgsFeature, QgsFillSymbol, QgsGeometry,
  QgsPointXY, QgsRendererCategory, QgsVectorFileWriter, QgsVectorLayer,
)

# value -> (colour, label) for each importable mapping. Each omits a
# different class, so a class the file does not mention falls back to
# an automatic colour and the two mappings differ in WHICH class that
# is: landcover.qml has no "bare", landcover-alt.qml has no "wetland".
QML_CLASSES = {
  "forest": ("#1b7837", "Native forest"),
  "water": ("#2166ac", "Open water"),
  "urban": ("#b2182b", "Built-up"),
  "crops": ("#f4a582", "Cropland"),
  "wetland": ("#762a83", "Wetland"),
}
QML_CLASSES_ALT = {
  "forest": ("#31a354", "Forest"),
  "water": ("#6baed6", "Water"),
  "urban": ("#969696", "Urban"),
  "crops": ("#fdae6b", "Crops"),
  "bare": ("#252525", "Bare ground"),
}

LANDCOVER = ["forest", "water", "urban", "crops", "wetland", "bare"]
ZONING = ["residential", "rural", "industrial", "reserve"]
PERIOD = ["pre-1940", "1940-1990", "post-1990"]


def build_layer(n=12, cell=500, x0=1_750_000.0, y0=5_910_000.0):
  """The parcel grid, in New Zealand Transverse Mercator (EPSG:2193),
  placed over Auckland so the fixture sits somewhere real. Classes are
  assigned in blocks rather than by cycling, so neighbouring parcels
  usually agree and a tiled map of them has visible regions rather
  than noise; every column gets a few nulls.

  Args:
    n: parcels along each side, so the layer holds n * n features.
      Keep it a multiple of 3: classes are assigned in 3 x 3 blocks
      and a remainder would leave a ragged strip of odd classes along
      two edges.
    cell: parcel size in metres. EPSG:2193 is a metric projection, so
      this is literal ground distance, and it sets the scale the
      tiling's spacing has to be chosen against.
    x0: easting of the grid's lower-left corner, in EPSG:2193 metres.
    y0: northing of that same corner. The defaults put the fixture
      over Auckland rather than at the projection origin, so anything
      rendered from it looks like somewhere.

  Returns:
    A new QgsVectorLayer on QGIS's "memory" provider — a layer that
    lives in this process only, with no file behind it — named
    "parcels", carrying n * n square features and the four fields
    landcover, zoning, period and value. Nothing is written to disk;
    the caller does that. Roughly one feature in 23 has all four
    fields left NULL, which is what gives the categorical tests a
    no-data class to symbolise.
  """
  from weavingspace_qgis import compat
  layer = QgsVectorLayer("MultiPolygon?crs=EPSG:2193", "parcels", "memory")
  prov = layer.dataProvider()
  prov.addAttributes([compat.make_field("landcover", str),
                      compat.make_field("zoning", str),
                      compat.make_field("period", str),
                      compat.make_field("value", float)])
  layer.updateFields()
  feats = []
  for i in range(n):
    for j in range(n):
      f = QgsFeature(layer.fields())
      x, y = x0 + i * cell, y0 + j * cell
      f.setGeometry(QgsGeometry.fromPolygonXY([[
        QgsPointXY(x, y), QgsPointXY(x + cell, y),
        QgsPointXY(x + cell, y + cell), QgsPointXY(x, y + cell)]]))
      # blocky assignment: 3x3 neighbourhoods share a class
      block = (i // 3) + (j // 3) * (n // 3)
      if (i * n + j) % 23:  # a scattering of nulls in every column
        f["landcover"] = LANDCOVER[block % len(LANDCOVER)]
        f["zoning"] = ZONING[(block // 2) % len(ZONING)]
        f["period"] = PERIOD[(i + j) % len(PERIOD)]
        f["value"] = float((i - n / 2) ** 2 + (j - n / 2) ** 2)
      feats.append(f)
  prov.addFeatures(feats)
  layer.updateExtents()
  return layer


def write_gpkg(layer, path):
  """Save a layer as the single-table GeoPackage the suite loads.

  Args:
    layer: the in-memory layer to persist, normally build_layer()'s.
    path: absolute destination for the .gpkg. main() removes any
      existing file first rather than relying on the writer's
      overwrite behaviour, since what a GeoPackage write does to a
      file that is already there (replace it, or add a table beside
      the old one) depends on the options and the GDAL version.

  Returns:
    Nothing; writes the file. The table inside is always called
    "parcels", regardless of the file name, because the tests open it
    by layer name.

  Raises:
    AssertionError: when the writer reports anything but NoError. The
    call returns either a status code or a (code, message) tuple
    depending on QGIS build, hence the unpacking; failing loudly
    matters because a half-written fixture would be committed and
    then puzzle someone months later.
  """
  options = QgsVectorFileWriter.SaveVectorOptions()
  options.driverName = "GPKG"
  options.layerName = "parcels"
  result = QgsVectorFileWriter.writeAsVectorFormatV3(
    layer, path, QgsCoordinateTransformContext(), options)
  code = result[0] if isinstance(result, tuple) else result
  assert code == QgsVectorFileWriter.WriterError.NoError, result


def write_qml(layer, path, classes):
  """Save a categorized renderer as a QML the plugin can read as a
  'Categ colourmap src'. Saving through QGIS itself (rather than
  hand-writing XML) keeps the fixture in whatever format this QGIS
  version reads back.

  Args:
    layer: the parcel layer, used only as the thing QGIS will
      serialise a style from. Its renderer IS replaced, so callers
      writing several mappings from one layer get the last one left
      in place; that is harmless here because the GeoPackage is
      written before any of this.
    path: absolute destination for the .qml.
    classes: the mapping this file encodes, {value: (colour, label)},
      where value is a landcover value as it appears in the data and
      colour is a hex string. Values absent from the mapping are
      absent from the file, which is deliberate: the plugin must then
      fall back to an automatic colour for them, and the two fixtures
      omit different values so a test can tell which mapping is in
      force.

  Returns:
    Nothing; writes the QML and leaves the layer carrying a
    categorized renderer on the "landcover" field.

  Raises:
    AssertionError: with QGIS's own message when the style will not
      save.
  """
  categories = [
    QgsRendererCategory(value,
                        QgsFillSymbol.createSimple({"color": colour}),
                        label)
    for value, (colour, label) in classes.items()]
  layer.setRenderer(QgsCategorizedSymbolRenderer("landcover", categories))
  ok, message = layer.saveNamedStyle(path)
  assert ok, message


def main():
  """Build the fixtures and write all three files into tests/data/.

  Starts a headless QGIS application first, because everything here
  goes through QGIS's own object model: a plain Python process can
  import qgis.core but the providers, the vector writer and the style
  machinery only exist once QgsApplication has been initialised.
  QGIS_PREFIX_PATH says where that installation lives and falls back
  to /usr, which is right on Linux; on macOS the launcher script sets
  it to the app bundle.

  Returns:
    Nothing; overwrites tests/data/landcover-categorical.gpkg,
    landcover.qml and landcover-alt.qml, printing each. The
    GeoPackage is written BEFORE any renderer is attached, so the
    committed fixture carries geometry and attributes only and the
    two QML files remain the sole source of imported colours.
  """
  QgsApplication.setPrefixPath(
    os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  app = QgsApplication([], False)
  app.initQgis()
  sys.path.insert(0, ROOT)
  os.makedirs(DATA, exist_ok=True)
  layer = build_layer()
  gpkg = os.path.join(DATA, "landcover-categorical.gpkg")
  if os.path.exists(gpkg):
    os.remove(gpkg)
  write_gpkg(layer, gpkg)
  for name, classes in (("landcover.qml", QML_CLASSES),
                        ("landcover-alt.qml", QML_CLASSES_ALT)):
    write_qml(layer, os.path.join(DATA, name), classes)
    print(f"wrote {os.path.join(DATA, name)}")
  print(f"wrote {gpkg} ({layer.featureCount()} features)")
  app.exitQgis()


if __name__ == "__main__":
  main()
