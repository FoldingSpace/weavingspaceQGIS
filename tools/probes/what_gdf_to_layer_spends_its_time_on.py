"""Where `bridge.gdf_to_layer` spends its time, and what a faster one costs.

The generation profile of 2026-09-04 put `gdf_to_layer` at 45% of a
Generate at spacing 150 -- the largest single term, ahead of the tiling
itself -- running at about 60 microseconds per drawn feature. This probe
asks what those microseconds are, and whether a vectorised conversion
returns the SAME LAYER.

Both arms run in ONE process on ONE frame, because a comparison across
two runs on a busy machine is not a measurement. The frame is built
through the product's own door (`catalog.make_unit`, then `Tiling`), not
by handing the library a raw spec, since the product is where the
defaults are chosen.

EXACTNESS IS THE POINT, NOT THE SECONDS. A conversion that changes what
the map holds is a cartographic decision rather than an optimisation, so
the arms are compared feature by feature -- geometry WKB and every
attribute -- and the probe reports the first disagreement rather than a
count.

    PYTHONPATH="$PWD:$PWD/weavingspace_qgis/vendor" \
      QT_QPA_PLATFORM=offscreen "$QGIS_PY" \
      tools/probes/what_gdf_to_layer_spends_its_time_on.py [spacing]
"""

import math
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGION = os.path.join(ROOT, "tests", "data", "imd-auckland-sa2-2018.gpkg")
SPACING = float(sys.argv[1]) if len(sys.argv) > 1 else 250.0


def build_frame(spacing):
  """A real tiled frame, through the door the dialog uses."""
  import geopandas as gpd
  from weavingspace_qgis import catalog
  from weavingspace.tile_map import Tiling

  region = gpd.read_file(REGION)
  # By SPEC through the product's own door, matched by prefix, because a
  # catalogue key may carry its own count and a name is not an identity.
  named = [k for k in catalog.TILINGS_BY_N[4] if k.startswith("laves 3.3.4.3.4")]
  assert named, "PREMISE: the catalogue offers no laves 3.3.4.3.4 at n=4"
  unit = catalog.make_unit(catalog.TILINGS_BY_N[4][named[0]],
                           spacing=spacing, crs=region.crs)
  tiling = Tiling(unit, region)
  frame = tiling.get_tiled_map(prioritise_tiles=True).map
  return frame


# ---------------------------------------------------------------- arm A

def current(gdf, name):
  """The shipped conversion, called as the plugin calls it.

  Args:
    gdf: the frame to convert.
    name: the layer name to give the result.

  Returns:
    Whatever `bridge.gdf_to_layer` returns, imported here rather than
    reimplemented so the baseline is the code that actually ships.
  """
  from weavingspace_qgis import bridge
  return bridge.gdf_to_layer(gdf, name)


# ---------------------------------------------------------------- arm B
def _coerce(v, kind, pd, NULL):
  """The shipped per-value decision, kept so an arm can pay for it.

  Args:
    v: the value as pandas handed it back.
    kind: `int`, `float` or `str` -- the column's declared kind.
    pd: the pandas module, passed in so this stays import-free.
    NULL: QGIS's own null sentinel.

  Returns:
    The value cast to the column's kind, or NULL where it is missing.
  """
  import math as _m
  if v is None or (isinstance(v, float) and _m.isnan(v)) or v is pd.NA:
    return NULL
  if kind is int:
    return int(v)
  if kind is float:
    return float(v)
  return str(v)




def convert(gdf, name, batch_wkb=True, multi_in_cpp=True,
            positional_attrs=True, column_casts=True):
  """The same layer, with the per-feature Python work lifted out.

  Four changes, each aimed at one term the decomposition below names:

  1. WKB for the whole column in ONE shapely call rather than one
     `.wkb` per object;
  2. no shapely MultiPolygon is CONSTRUCTED for a plain polygon --
     QGIS converts in C++ through `convertToMultiType`;
  3. attributes set POSITIONALLY with `setAttributes`, where `feat[c]`
     does a field-name lookup per attribute per feature;
  4. the null-and-cast decision made once per COLUMN rather than once
     per value.

  A GeometryCollection still takes the old path, because only the
  polygonal parts are kept and that is a per-object question.

  Args:
    gdf: the frame to convert.
    name: the layer name to give the result.
    batch_wkb: take the whole column's WKB in one shapely call.
    multi_in_cpp: let QGIS promote a polygon to multi, rather than
      building a shapely MultiPolygon for it.
    positional_attrs: set attributes by POSITION rather than by name.
    column_casts: decide the null-and-cast question once per column.

  Returns:
    A memory layer that must be identical, feature by feature, to what
    `bridge.gdf_to_layer` returns for the same frame -- which is what
    the probe asserts rather than assumes.
  """
  import pandas as pd
  import shapely
  from shapely.geometry import MultiPolygon, Polygon
  from qgis.core import (QgsCoordinateReferenceSystem, QgsFeature,
                         QgsGeometry, QgsVectorLayer, NULL)
  from weavingspace_qgis.bridge import _make_field

  crs_str = ""
  if gdf.crs is not None:
    authid = gdf.crs.to_authority()
    crs_str = f"?crs={authid[0]}:{authid[1]}" if authid \
      else f"?crs=wkt:{gdf.crs.to_wkt()}"
  layer = QgsVectorLayer(f"MultiPolygon{crs_str}", name, "memory")
  if gdf.crs is None:
    layer.setCrs(QgsCoordinateReferenceSystem())
  provider = layer.dataProvider()

  columns = [c for c in gdf.columns if c != gdf.geometry.name]
  kinds = {}
  for c in columns:
    if pd.api.types.is_integer_dtype(gdf[c]):
      kinds[c] = int
    elif pd.api.types.is_float_dtype(gdf[c]):
      kinds[c] = float
    else:
      kinds[c] = str
  provider.addAttributes([_make_field(c, kinds[c]) for c in columns])
  layer.updateFields()
  fields = layer.fields()

  geoms = gdf.geometry.values
  type_ids = shapely.get_type_id(geoms)      # 3 polygon, 6 multipolygon
  missing = shapely.is_missing(geoms)
  empty = shapely.is_empty(geoms)
  # to_wkb refuses a missing geometry, so ask only where there is one.
  wkbs = [None] * len(geoms)
  wanted = [i for i in range(len(geoms)) if not missing[i] and not empty[i]]
  if wanted:
    if batch_wkb:
      produced = shapely.to_wkb(geoms[wanted])
      for slot, i in enumerate(wanted):
        wkbs[i] = produced[slot]
    else:
      for i in wanted:                     # one .wkb per object, as shipped
        wkbs[i] = geoms[i].wkb

  # ONE decision per column, not one per value.
  cols = []
  for c in columns:
    series = gdf[c]
    kind = kinds[c]
    if not column_casts:
      cols.append(series.tolist())         # decided per VALUE below
      continue
    if kind is str:
      values = [None if v is None or v is pd.NA
                or (isinstance(v, float) and math.isnan(v)) else str(v)
                for v in series.tolist()]
    else:
      cast = int if kind is int else float
      values = [None if v is None or v is pd.NA
                or (isinstance(v, float) and math.isnan(v)) else cast(v)
                for v in series.tolist()]
    cols.append(values)

  feats = []
  for i in range(len(geoms)):
    if wkbs[i] is None:
      continue
    tid = type_ids[i]
    if tid == 3 or tid == 6:
      geom = QgsGeometry()
      if tid == 3 and not multi_in_cpp:
        geom.fromWkb(MultiPolygon([geoms[i]]).wkb)   # shapely builds it
      else:
        geom.fromWkb(wkbs[i])
        if tid == 3:
          geom.convertToMultiType()
    else:
      shp = geoms[i]
      polys = [g for g in getattr(shp, "geoms", []) if isinstance(g, Polygon)]
      if not polys:
        continue
      geom = QgsGeometry()
      geom.fromWkb(MultiPolygon(polys).wkb)
    feat = QgsFeature(fields)
    feat.setGeometry(geom)
    if positional_attrs:
      row = []
      for c_i, col in enumerate(cols):
        v = col[i]
        if column_casts:
          row.append(NULL if v is None else v)
        else:
          row.append(_coerce(v, kinds[columns[c_i]], pd, NULL))
      feat.setAttributes(row)
    else:
      for c_i, c in enumerate(columns):    # by NAME, as shipped
        v = cols[c_i][i]
        feat[c] = (NULL if v is None else v) if column_casts \
          else _coerce(v, kinds[c], pd, NULL)
    feats.append(feat)
  provider.addFeatures(feats)
  layer.updateExtents()
  provider.createSpatialIndex()
  return layer


# ------------------------------------------------------- the comparison

def describe(layer):
  """Everything a caller could read back, in feature order."""
  rows = []
  for f in layer.getFeatures():
    rows.append((f.geometry().asWkb().data(), list(f.attributes())))
  return rows


def first_disagreement(a, b):
  """The first row the two arms describe differently, or None.

  Args:
    a: rows from `describe`, the reference arm.
    b: rows from `describe`, the arm under test.

  Returns:
    A sentence naming the first disagreement -- a differing count, a
    differing geometry or differing attributes -- or None where the two
    agree at every feature. The FIRST is reported rather than a count,
    because one disagreement already settles the question.
  """
  if len(a) != len(b):
    return f"feature COUNT differs: {len(a)} against {len(b)}"
  for i, (ra, rb) in enumerate(zip(a, b)):
    if ra[0] != rb[0]:
      return f"row {i}: geometry differs ({len(ra[0])}b against {len(rb[0])}b)"
    if ra[1] != rb[1]:
      return f"row {i}: attributes {ra[1]} against {rb[1]}"
  return None


def timed(fn, gdf, name):
  """Run one conversion and report what it cost.

  Args:
    fn: the conversion to call, as `fn(gdf, name)`.
    gdf: the frame to convert.
    name: the layer name to give the result.

  Returns:
    (seconds, layer). The clock is MONOTONIC, because a laptop closed
    mid-run advances the wall clock while accumulating no cpu, and this
    project measures durations on the monotonic clock for that reason.
  """
  start = time.monotonic()          # monotonic: a closed lid must not count
  layer = fn(gdf, name)
  return time.monotonic() - start, layer


ARMS = [
  ("none (control)", dict(batch_wkb=False, multi_in_cpp=False,
                          positional_attrs=False, column_casts=False)),
  ("+ batched WKB", dict(batch_wkb=True, multi_in_cpp=False,
                         positional_attrs=False, column_casts=False)),
  ("+ multi in C++", dict(batch_wkb=False, multi_in_cpp=True,
                          positional_attrs=False, column_casts=False)),
  ("+ positional attrs", dict(batch_wkb=False, multi_in_cpp=False,
                              positional_attrs=True, column_casts=False)),
  ("+ per-column casts", dict(batch_wkb=False, multi_in_cpp=False,
                              positional_attrs=False, column_casts=True)),
  ("all four", dict(batch_wkb=True, multi_in_cpp=True,
                    positional_attrs=True, column_casts=True)),
]


def run_one_arm(index):
  """Time ONE arm against the shipped function, in a process of its own.

  Every arm builds a memory layer of ten thousand features WITH A
  SPATIAL INDEX and keeps it alive for the exactness check, so arms run
  in one process pay for each other's memory: measured, the last arm
  moved 27.5 to 40.3 microseconds per feature between two runs while the
  shipped baseline held steady. One arm per process removes the
  question, exactly as one spacing per process does for the stage table
  in docs/PERFORMANCE.md.

  The shipped baseline is re-measured HERE rather than passed in, so the
  ratio is taken between two things this process timed.
  """
  from qgis.core import QgsApplication
  QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  app = QgsApplication([], False)        # BOUND: an unbound one is collected
  app.initQgis()
  label, flags = ARMS[index]
  frame = build_frame(SPACING)
  assert len(frame) > 1000, f"PREMISE: only {len(frame)} tiles, too few"

  current(frame.head(50), "warm")        # neither arm pays another's import
  convert(frame.head(50), "warm", **flags)

  ship = min(timed(current, frame, f"s{k}")[0] for k in range(3))
  _t, layer_shipped = timed(current, frame, "s_ref")
  mine = min(timed(lambda g, nm: convert(g, nm, **flags), frame, f"m{k}")[0]
             for k in range(3))
  _t, layer_mine = timed(lambda g, nm: convert(g, nm, **flags), frame, "m_ref")

  n = layer_shipped.featureCount()
  verdict = first_disagreement(describe(layer_shipped), describe(layer_mine))
  print(f"ROW\t{label}\t{ship:.3f}\t{mine:.3f}\t{n}\t"
        f"{'identical' if verdict is None else verdict}")
  print(f"CHILD COMPLETE: {label}")


def main():
  """One arm per process, each with its own shipped baseline."""
  assert os.path.exists(REGION), f"PREMISE: no region fixture at {REGION}"

  if len(sys.argv) > 2:
    run_one_arm(int(sys.argv[2]))
    return

  print(f"gdf_to_layer, spacing {SPACING:g}, ONE ARM PER PROCESS")
  print(f"\n  {'arm':<22} {'shipped':>9} {'arm':>9} {'us/feat':>9} "
        f"{'ratio':>7}  exact?")
  for i, (label, _flags) in enumerate(ARMS):
    finished = subprocess.run(
      [sys.executable, os.path.abspath(__file__), str(SPACING), str(i)],
      capture_output=True, text=True, check=False)
    row = [l for l in finished.stdout.split("\n") if l.startswith("ROW\t")]
    if not row or "CHILD COMPLETE" not in finished.stdout:
      print(f"  {label:<22} CHILD DID NOT COMPLETE "
            f"(exit {finished.returncode})")
      print((finished.stderr or finished.stdout)[-600:])
      continue
    _tag, lab, ship, mine, n, exact = row[0].split("\t")
    ship, mine, n = float(ship), float(mine), int(n)
    print(f"  {lab:<22} {ship:8.3f}s {mine:8.3f}s "
          f"{mine / max(n, 1) * 1e6:8.1f} {ship / mine:6.2f}x  {exact}")

  print("\nEach row's ratio is between two timings taken in ONE process;")
  print("the shipped column varying across rows is the machine, not a fault.")
  print("\nPROBE COMPLETE: every arm ran in its own process.")


main()
