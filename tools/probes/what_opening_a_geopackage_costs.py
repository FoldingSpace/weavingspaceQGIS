"""Does opening a GeoPackage cost time proportional to its layers?

THE CLAIM THIS TESTS is the one every entry about the quadratic save
rests on: "each opens the GeoPackage, and opening one costs time
proportional to the layers already in it". That sentence has been
written into four documents and was inferred from the SHAPE of the
save's own growth rather than measured directly. A cause named by
reading is a hypothesis, exactly like a site.

AND IT ASKS A SECOND QUESTION THE ANSWER TURNS ON. GDAL keeps a
SHARED DATASET CACHE, so a handle held open for the length of an act
may make every later open of the same path cheap -- which would close
the quadratic without rewriting anything about what the file
CONTAINS. That is the difference between a repair and a rewrite, so
it is worth ten minutes before choosing.

It builds files of k tiny layers and times, for each k: a plain OGR
update open, the same with a handle already held, and a
QgsVectorLayer built on one table, which is what `point_layer_at`
costs. No plugin code is involved -- the point is to ask GDAL and
QGIS directly, with our own code out of the way.
"""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.environ.get("WS_REPO", os.getcwd()))

COUNTS = (8, 16, 32, 64, 128, 256)
REPEATS = 12


def build(path: str, layers: int) -> None:
  """Write a GeoPackage holding `layers` one-feature tables.

  Args:
    path: where to write it. Removed first if present, so each file is
      built from nothing and the timing below is not measuring a
      previous run's leftovers.
    layers: how many tables to put in it.

  Returns:
    None. The tables are deliberately TINY -- one point, one integer
    column -- because the question is what the number of LAYERS costs
    to open, and a file whose layers held real geometry would measure
    the size of the data instead.
  """
  from osgeo import ogr, osr
  if os.path.exists(path):
    os.remove(path)
  driver = ogr.GetDriverByName("GPKG")
  data = driver.CreateDataSource(path)
  crs = osr.SpatialReference()
  crs.ImportFromEPSG(3857)
  for i in range(layers):
    layer = data.CreateLayer(f"table_{i:04d}", crs, ogr.wkbPoint)
    layer.CreateField(ogr.FieldDefn("n", ogr.OFTInteger))
    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetField("n", i)
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(float(i), float(i))
    feature.SetGeometry(point)
    layer.CreateFeature(feature)
    feature = None
    layer = None
  data = None


def time_opens(path: str, repeats: int, hold: bool) -> float:
  """Milliseconds per OGR update-mode open of one file.

  Args:
    path: the GeoPackage to open.
    repeats: how many opens to average over. More than one because a
      single sample on a machine that has been running QGIS all
      evening tells you nothing in either direction.
    hold: keep one handle open across the whole loop. That is the
      arm asking whether GDAL's shared cache makes a later open cheap;
      the handle is taken BEFORE the clock starts, so its own cost is
      not in the figure.

  Returns:
    The mean milliseconds an open took. The handle is released before
    returning, so the next reading starts from a cold file rather than
    inheriting this one's cache.
  """
  from osgeo import ogr
  held = ogr.Open(path, 1) if hold else None
  started = time.monotonic()
  for _ in range(repeats):
    data = ogr.Open(path, 1)
    assert data is not None, f"PREMISE: could not open {path}"
    data = None
  spent = time.monotonic() - started
  held = None
  return spent * 1000.0 / repeats


def time_layers(path: str, repeats: int, hold: bool) -> float:
  """Milliseconds per QgsVectorLayer built on one table of the file.

  Args:
    path: the GeoPackage.
    repeats: how many layers to build and average over.
    hold: keep one OGR handle open across the loop, as above.

  Returns:
    The mean milliseconds. This is the shape `compat.point_layer_at`
    pays per element -- `setDataSource` goes through the same OGR
    provider -- and it was the largest of the three per-layer terms in
    the save's own baseline, at 1.60s of a 4.5s wall at 64 elements.
  """
  from osgeo import ogr
  from qgis.core import QgsVectorLayer
  held = ogr.Open(path, 1) if hold else None
  started = time.monotonic()
  for i in range(repeats):
    layer = QgsVectorLayer(f"{path}|layername=table_{i:04d}",
                           "probe", "ogr")
    assert layer.isValid(), f"PREMISE: table_{i:04d} did not open"
    layer = None
  spent = time.monotonic() - started
  held = None
  return spent * 1000.0 / repeats


def main():
  """Time both questions across six file sizes and print the table.

  Returns:
    None; it prints. Six sizes rather than two because the question is
    the SHAPE of the growth and two points fit any line you like --
    the same reason the save's own instrument takes four.
  """
  from qgis.core import QgsApplication
  app = QgsApplication([], False)
  QgsApplication.initQgis()

  work = tempfile.mkdtemp(prefix="ws-open-cost-")
  rows = []
  for count in COUNTS:
    path = os.path.join(work, f"k{count}.gpkg")
    build(path, count)
    size = os.path.getsize(path) / 1024.0
    rows.append({
      "layers": count,
      "kb": size,
      "open": time_opens(path, REPEATS, hold=False),
      "open_held": time_opens(path, REPEATS, hold=True),
      "layer": time_layers(path, min(REPEATS, count), hold=False),
      "layer_held": time_layers(path, min(REPEATS, count), hold=True),
    })
    print(f"  k={count:<4} built {size:8.0f} KB", flush=True)

  print()
  print("=" * 78)
  print("WHAT ONE OPEN COSTS, against how many layers the file holds")
  print("=" * 78)
  head = "".join(f"{r['layers']:>9}" for r in rows)
  print(f"  {'layers in the file':<34}{head}")
  print(f"  {'file size (KB)':<34}"
        + "".join(f"{r['kb']:>9.0f}" for r in rows))
  print(f"  {'-' * 34}" + "-" * (9 * len(rows)))
  for key, label in (("open", "ogr.Open update (ms)"),
                     ("open_held", "  ...with a handle held (ms)"),
                     ("layer", "QgsVectorLayer on one table (ms)"),
                     ("layer_held", "  ...with a handle held (ms)")):
    print(f"  {label:<34}"
          + "".join(f"{r[key]:>9.2f}" for r in rows))

  print()
  print("  RATIOS against the reading before. 2.0 means the cost of an")
  print("  open DOUBLES when the file's layer count doubles, which is")
  print("  what makes a per-layer loop quadratic in the element count.")
  for key, label in (("open", "ogr.Open update"),
                     ("open_held", "  ...handle held"),
                     ("layer", "QgsVectorLayer"),
                     ("layer_held", "  ...handle held")):
    ratios = ["    -" if i == 0 else f"{rows[i][key] / rows[i - 1][key]:>5.1f}"
              for i in range(len(rows))]
    print(f"  {label:<34}" + "".join(f"{r:>9}" for r in ratios))

  print()
  print("  WHAT A HELD HANDLE SAVES, as a fraction of the plain cost. A")
  print("  figure near 1.00 means GDAL's shared cache does not help and")
  print("  the repair has to be a single session rather than a held one.")
  for plain, held, label in (("open", "open_held", "ogr.Open update"),
                             ("layer", "layer_held", "QgsVectorLayer")):
    shares = [f"{rows[i][held] / rows[i][plain]:>5.2f}"
              if rows[i][plain] else "    -" for i in range(len(rows))]
    print(f"  {label:<34}" + "".join(f"{s:>9}" for s in shares))


main()
