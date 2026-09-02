"""Can the per-layer repointing be made cheap, or only rarer?

THE SAVE'S LARGEST TERM is `compat.point_layer_at` -- 1.60s of a 4.5s
wall at 64 elements -- and it is the one a single OGR session cannot
obviously batch, because every layer genuinely needs its own provider.
Two of the three terms (`write_gpkg_layer` and
`save_style_to_database`) can be collapsed into one session; if this
one cannot, the rewrite closes two thirds of a quadratic and leaves a
quadratic behind, which is worth knowing BEFORE the writer is rewritten
rather than after.

WHAT THE FIRST PROBE RULED OUT. Holding a python-side `ogr.Open`
handle across the act saves nothing (0.91-1.02 of the plain cost), so
GDAL's own shared cache does not answer it. But QGIS's OGR provider
keeps its OWN connection pool, keyed by dataset, in C++ -- a different
thing entirely from a handle taken through the python bindings. If
holding a QGIS LAYER on the file warms that pool, the repair is a line
rather than a rewrite.

Four arms, at six file sizes, all in one run: a fresh layer and a
`setDataSource` repoint, each with nothing held and with a QGIS layer
on the same file held open.
"""

import contextlib
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
    path: where to write it, removed first if present.
    layers: how many tables to put in it.

  Returns:
    None. Tiny tables on purpose: the question is what the NUMBER of
    layers costs, and real geometry would measure the data instead.
  """
  from osgeo import ogr, osr
  # ASKED FOR, NOT ASKED ABOUT. Two of these processes running at
  # once both see the file, both remove it, and the second dies with
  # FileNotFoundError before measuring anything -- which is the shape
  # `test_nothing_asks_whether_a_file_exists_before_removing_it`
  # scans this tree for, and which cost a coverage shard its whole run
  # on 2026-08-28. Not caring is the only thing that fixes it.
  with contextlib.suppress(FileNotFoundError):
    os.remove(path)
  data = ogr.GetDriverByName("GPKG").CreateDataSource(path)
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


def a_memory_layer():
  """One throwaway memory layer to repoint, matching the product's case.

  Returns:
    A valid in-memory QgsVectorLayer. `point_layer_at` is always
    called on a layer that already exists and is being moved onto the
    file, never on a fresh object, so timing a fresh construction
    would be timing a different act.
  """
  from qgis.core import QgsVectorLayer
  layer = QgsVectorLayer("Point?crs=EPSG:3857&field=n:integer",
                         "held", "memory")
  assert layer.isValid(), "PREMISE: the memory layer did not build"
  return layer


def time_fresh(path: str, repeats: int, warm) -> float:
  """Milliseconds per fresh QgsVectorLayer built on one table.

  Args:
    path: the GeoPackage.
    repeats: how many to build and average over.
    warm: a QGIS layer already reading from this file, held for the
      length of the loop, or None. This is the arm asking about QGIS's
      own provider pool rather than GDAL's dataset cache.

  Returns:
    The mean milliseconds.
  """
  from qgis.core import QgsVectorLayer
  started = time.monotonic()
  for i in range(repeats):
    layer = QgsVectorLayer(f"{path}|layername=table_{i:04d}", "p", "ogr")
    assert layer.isValid(), f"PREMISE: table_{i:04d} did not open"
    layer = None
  spent = time.monotonic() - started
  assert warm is None or warm.isValid()      # keep it alive to here
  return spent * 1000.0 / repeats


def time_repoint(path: str, repeats: int, warm) -> float:
  """Milliseconds per `compat.point_layer_at` onto one table.

  Args:
    path: the GeoPackage.
    repeats: how many repoints to average over.
    warm: a QGIS layer already reading from this file, held for the
      length of the loop, or None.

  Returns:
    The mean milliseconds. The product's own function is called rather
    than a copy of it, so this measures what the save actually does --
    a spy that stands in for the call measures the spy.
  """
  from weavingspace_qgis import compat
  layers = [a_memory_layer() for _ in range(repeats)]
  started = time.monotonic()
  for i, layer in enumerate(layers):
    ok = compat.point_layer_at(layer, path, f"table_{i:04d}")
    assert ok, f"PREMISE: the repoint onto table_{i:04d} did not take"
  spent = time.monotonic() - started
  assert warm is None or warm.isValid()      # keep it alive to here
  layers = None
  return spent * 1000.0 / repeats


def main():
  """Time four arms across six file sizes and print the table.

  Returns:
    None; it prints. The share columns are the finding: a figure near
    1.00 means the warm pool does not help and the third term stays
    per-layer whatever the writer does.
  """
  from qgis.core import QgsApplication, QgsVectorLayer
  # BOUND TO A NAME, and that is not style. Left unbound the
  # application is collected on the next line and the process dies of
  # a segmentation fault with two nullptr warnings and nothing else --
  # which reads exactly like a defect in what is being measured.
  # (Mine, 2026-09-01, on the first run of this probe.)
  app = QgsApplication([], False)
  QgsApplication.initQgis()
  assert app is not None

  work = tempfile.mkdtemp(prefix="ws-repoint-cost-")
  rows = []
  for count in COUNTS:
    path = os.path.join(work, f"k{count}.gpkg")
    build(path, count)
    repeats = min(REPEATS, count)
    row = {"layers": count}
    row["fresh"] = time_fresh(path, repeats, None)
    row["repoint"] = time_repoint(path, repeats, None)
    warm = QgsVectorLayer(f"{path}|layername=table_0000", "warm", "ogr")
    assert warm.isValid(), "PREMISE: the warm layer did not open"
    row["fresh_warm"] = time_fresh(path, repeats, warm)
    row["repoint_warm"] = time_repoint(path, repeats, warm)
    warm = None
    rows.append(row)
    print(f"  k={count:<4} fresh {row['fresh']:6.1f}  "
          f"repoint {row['repoint']:6.1f} ms", flush=True)

  print()
  print("=" * 78)
  print("WHAT ATTACHING ONE LAYER COSTS, against the file's layer count")
  print("=" * 78)
  print(f"  {'layers in the file':<34}"
        + "".join(f"{r['layers']:>9}" for r in rows))
  print(f"  {'-' * 34}" + "-" * (9 * len(rows)))
  for key, label in (("fresh", "fresh QgsVectorLayer (ms)"),
                     ("fresh_warm", "  ...with a QGIS layer held (ms)"),
                     ("repoint", "compat.point_layer_at (ms)"),
                     ("repoint_warm", "  ...with a QGIS layer held (ms)")):
    print(f"  {label:<34}" + "".join(f"{r[key]:>9.2f}" for r in rows))

  print()
  print("  RATIOS against the reading before. 2.0 per doubling is what")
  print("  makes a per-layer loop quadratic in the element count.")
  for key, label in (("fresh", "fresh QgsVectorLayer"),
                     ("fresh_warm", "  ...layer held"),
                     ("repoint", "compat.point_layer_at"),
                     ("repoint_warm", "  ...layer held")):
    ratios = ["    -" if i == 0 else f"{rows[i][key] / rows[i - 1][key]:>5.1f}"
              for i in range(len(rows))]
    print(f"  {label:<34}" + "".join(f"{r:>9}" for r in ratios))

  print()
  print("  WHAT A WARM QGIS LAYER SAVES, as a fraction of the plain")
  print("  cost. Near 1.00 means the provider pool does not answer this")
  print("  and the third term stays per-layer whatever the writer does.")
  for plain, warm, label in (("fresh", "fresh_warm", "fresh QgsVectorLayer"),
                             ("repoint", "repoint_warm",
                              "compat.point_layer_at")):
    shares = [f"{rows[i][warm] / rows[i][plain]:>5.2f}"
              if rows[i][plain] else "    -" for i in range(len(rows))]
    print(f"  {label:<34}" + "".join(f"{s:>9}" for s in shares))

  print()
  print("  AND WHAT THE WHOLE LOOP WOULD COST at each size, which is")
  print("  the figure a person actually waits for: n repoints into a")
  print("  file that by then holds n tables.")
  for key, label in (("repoint", "n x point_layer_at (s)"),
                     ("repoint_warm", "  ...layer held (s)")):
    print(f"  {label:<34}"
          + "".join(f"{r['layers'] * r[key] / 1000.0:>9.1f}" for r in rows))


main()
