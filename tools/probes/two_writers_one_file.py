"""Do the per-layer writer and the single-session one make the same file?

REWRITING A WRITER PUTS THE RISK ON THE ONE THING THAT MUST NOT BREAK
-- what a colleague receives -- so the rewrite is only as good as the
differential under it. This is that differential, and it is this
project's favourite shape: two independent descriptions of one thing,
compared, so a disagreement is a defect by construction and no oracle
is needed.

It draws ONE map, writes it BOTH ways into two files, and compares
what the two files CONTAIN rather than what they weigh: the tables
they hold, each table's declared geometry type and CRS, every column's
name, type, subtype, width and precision, the feature counts, and then
every feature's attributes and geometry, matched by the plugin's own
FID column.

WHY BYTES ARE NOT THE COMPARISON. Two GeoPackages holding identical
data differ in bytes routinely -- sqlite reorganises pages, and a
value just written lives in the write-ahead log beside the file rather
than in it. This project has already measured a file growing from
184,320 to 356,352 bytes across a run that wrote nothing. Compare what
the file HOLDS.
"""

import os
import sys
import time

sys.path.insert(0, os.environ.get("WS_REPO", os.getcwd()))

from tools.probe_kit import start                      # noqa: E402

COUNTS = tuple(int(n) for n in
          os.environ.get("WS_WRITER_COUNTS", "4,12,24").split(","))


def a_region_with_gaps(probe):
  """A region layer whose `v1` column really is NULL in places.

  Args:
    probe: the running `Probe`, for its temporary directory.

  Returns:
    A file-backed QgsVectorLayer, added to the project.

  IT GOES THROUGH A FILE, and that is not fastidiousness. A value
  never set on a MEMORY feature reads back as 0.0 rather than as
  QGIS's NULL -- the suite records that at its own awkward-data
  fixture -- so a memory layer cannot stage the one thing this
  fixture exists for. Written through OGR and read back, the nulls
  are nulls.

  WHY THE DIFFERENTIAL NEEDS IT. Without missing values the plugin
  writes no `_no_data` twin at all and never reaches the branch that
  writes a null, so the comparison covers neither -- which is exactly
  what the first run of this probe measured: three mutations, and the
  one that removed null handling could not be seen. A fixture that
  cannot exhibit the case is invisible in a green result.
  """
  from osgeo import ogr, osr
  from qgis.core import QgsProject, QgsVectorLayer
  path = probe.path("gappy_region.gpkg")
  if os.path.exists(path):
    os.remove(path)
  data = ogr.GetDriverByName("GPKG").CreateDataSource(path)
  crs = osr.SpatialReference()
  crs.ImportFromEPSG(3857)
  crs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
  layer = data.CreateLayer("region", crs, ogr.wkbMultiPolygon)
  for name, kind in (("v1", ogr.OFTReal), ("v2", ogr.OFTReal),
                     ("v3", ogr.OFTInteger), ("landcover", ogr.OFTString)):
    layer.CreateField(ogr.FieldDefn(name, kind))
  kinds = ["forest", "water", "urban", "crops"]
  cell = 1000
  definition = layer.GetLayerDefn()
  for i in range(4):
    for j in range(4):
      feature = ogr.Feature(definition)
      # EVERY THIRD AREA HAS NO VALUE, which is what puts tiles onto
      # the twin and nulls into the tables. Not all of them: an
      # element whose column is empty everywhere takes a different
      # path entirely, and that is a different case from this one.
      if (i + j) % 3 == 0:
        feature.SetFieldNull(0)
      else:
        feature.SetField("v1", float(i + j))
      feature.SetField("v2", float(j))
      feature.SetField("v3", i * j)
      feature.SetField("landcover", kinds[(i + j) % len(kinds)])
      ring = ogr.Geometry(ogr.wkbLinearRing)
      for x, y in ((i * cell, j * cell), ((i + 1) * cell, j * cell),
                   ((i + 1) * cell, (j + 1) * cell),
                   (i * cell, (j + 1) * cell), (i * cell, j * cell)):
        ring.AddPoint(float(x), float(y))
      polygon = ogr.Geometry(ogr.wkbPolygon)
      polygon.AddGeometry(ring)
      multi = ogr.Geometry(ogr.wkbMultiPolygon)
      multi.AddGeometry(polygon)
      feature.SetGeometry(multi)
      layer.CreateFeature(feature)
      feature = None
  layer = None
  data = None

  found = QgsVectorLayer(f"{path}|layername=region", "gappy region", "ogr")
  assert found.isValid(), "PREMISE: the gappy region would not open"
  QgsProject.instance().addMapLayer(found)
  return found


def a_drawn_map(probe, elements: int, spacing: float, gaps: bool):
  """Draw a map of `elements` elements and hand back its dialog.

  Args:
    probe: the running `Probe`.
    elements: how many elements the design should carry.
    spacing: map units between repeats.
    gaps: build it over a region whose values are missing in places,
      so the map carries no-data twins and null attributes.

  Returns:
    The dialog, still open, with its layers in the project -- or None
    where the count is not offered. The premise that the map really
    carries that many elements is asserted, since a comparison of two
    writers on a map that is not the one claimed says nothing.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  probe.clear()
  if gaps:
    layer = a_region_with_gaps(probe)
    dlg = WeavingSpaceDialog(iface=probe.suite._Iface())
    dlg.live_check.setChecked(False)
    dlg.layer_combo.setLayer(layer)
    probe.suite._tick(300)
  else:
    dlg, _layer, _tid = probe.dialog()
  if not (dlg.n_spin.minimum() <= elements <= dlg.n_spin.maximum()):
    dlg.close()
    return None
  dlg.n_spin.setValue(elements)
  probe.suite._tick(600)
  dlg.spacing_spin.setValue(spacing)
  probe.suite._generate_and_wait(dlg)
  drew = len(dlg._element_layer_ids)
  assert drew == elements, (
    f"PREMISE: asked for {elements} elements and drew {drew}")
  return dlg


def jobs_from(dlg):
  """The (layer, table) pairs a save would write for this map.

  Args:
    dlg: a dialog holding a drawn map.

  Returns:
    A list of pairs in element order, element table then its no-data
    twin, exactly as `_save_the_map`'s own loop composes them -- built
    from the dialog's records rather than invented here, so the two
    arms are handed the same work.
  """
  from qgis.core import QgsProject
  from weavingspace_qgis import bridge
  project = QgsProject.instance()
  tables = dict(getattr(dlg, "_element_tables", {}) or {})
  out = []
  for tid in sorted(dlg._element_layer_ids, key=bridge.element_order):
    name = tables.get(tid)
    if not name:
      assignment = dlg._assignment_for(tid) or {}
      name = bridge.element_table_name(tid, assignment.get("var"))
    for layer_id, table in (
        (dlg._element_layer_ids.get(tid), name),
        (dlg._no_data_layer_ids.get(tid), f"{name}_no_data")):
      layer = project.mapLayer(layer_id) if layer_id else None
      if layer is not None:
        out.append((layer, table))
  return out


def describe(path: str):
  """Everything about a GeoPackage the two writers could disagree on.

  Args:
    path: the file to read. It is opened READ ONLY and released before
      returning, because an instrument that holds a file open changes
      what the next reader sees.

  Returns:
    A dict from table name to a description of that table: its
    declared geometry type and CRS authority, its columns as
    (name, type, subtype, width, precision), its feature count, and
    every feature as (attributes, geometry WKB) keyed by the plugin's
    own FID column.
  """
  from osgeo import ogr
  from weavingspace_qgis.bridge import GPKG_FID_COLUMN
  out = {}
  data = ogr.Open(path, 0)
  assert data is not None, f"PREMISE: {path} would not open"
  try:
    for index in range(data.GetLayerCount()):
      layer = data.GetLayer(index)
      definition = layer.GetLayerDefn()
      crs = layer.GetSpatialRef()
      columns = []
      for i in range(definition.GetFieldCount()):
        field = definition.GetFieldDefn(i)
        columns.append((field.GetName(), field.GetType(),
                        field.GetSubType(), field.GetWidth(),
                        field.GetPrecision()))
      rows = {}
      layer.ResetReading()
      for feature in layer:
        key = feature.GetFID()
        if GPKG_FID_COLUMN in [c[0] for c in columns]:
          key = feature.GetField(GPKG_FID_COLUMN)
        values = tuple(
          feature.GetField(i) if feature.IsFieldSet(i)
          and not feature.IsFieldNull(i) else None
          for i in range(definition.GetFieldCount()))
        geometry = feature.GetGeometryRef()
        rows[key] = (values,
                     None if geometry is None else geometry.ExportToWkb())
      out[layer.GetName()] = {
        "geometry_type": definition.GetGeomType(),
        "crs": None if crs is None else crs.GetAuthorityCode(None),
        "columns": columns,
        "count": layer.GetFeatureCount(),
        "rows": rows,
      }
  finally:
    data = None
  return out


def compare(old, new, elements):
  """Name every way the two files differ, or report none.

  Args:
    old: the description of the file the per-layer writer made.
    new: the description of the file the single-session writer made.
    elements: the element count, for the report.

  Returns:
    A list of sentences. Reporting EVERY difference rather than the
    first is what makes a failure a work list; a single "they differ"
    is not actionable.
  """
  faults = []
  # WHICH TABLES: `layer_styles` is written by the style pass rather
  # than by either writer, so it is compared only for presence.
  if set(old) != set(new):
    only_old = sorted(set(old) - set(new))
    only_new = sorted(set(new) - set(old))
    if only_old:
      faults.append(f"tables the session writer did not make: {only_old}")
    if only_new:
      faults.append(f"tables only the session writer made: {only_new}")
  for table in sorted(set(old) & set(new)):
    a, b = old[table], new[table]
    if a["geometry_type"] != b["geometry_type"]:
      faults.append(f"{table}: geometry type {a['geometry_type']} "
                    f"against {b['geometry_type']}")
    if a["crs"] != b["crs"]:
      faults.append(f"{table}: CRS {a['crs']} against {b['crs']}")
    if a["columns"] != b["columns"]:
      faults.append(f"{table}: columns differ\n"
                    f"      per-layer: {a['columns']}\n"
                    f"      session  : {b['columns']}")
    if a["count"] != b["count"]:
      faults.append(f"{table}: {a['count']} features against {b['count']}")
      continue
    if set(a["rows"]) != set(b["rows"]):
      faults.append(f"{table}: the feature keys differ")
      continue
    wrong_values = [k for k in a["rows"]
                    if a["rows"][k][0] != b["rows"][k][0]]
    if wrong_values:
      k = wrong_values[0]
      faults.append(
        f"{table}: {len(wrong_values)} of {len(a['rows'])} features "
        f"carry different attributes, e.g. key {k}:\n"
        f"      per-layer: {a['rows'][k][0]}\n"
        f"      session  : {b['rows'][k][0]}")
    wrong_shapes = [k for k in a["rows"]
                    if a["rows"][k][1] != b["rows"][k][1]]
    if wrong_shapes:
      faults.append(
        f"{table}: {len(wrong_shapes)} of {len(a['rows'])} features "
        f"carry different geometry")
  return faults


def main():
  """Write one map both ways at three element counts and compare.

  Returns:
    None; it prints. It asserts nothing at the end deliberately -- the
    report is the product, and a probe that stops at the first fault
    hides the rest of a work list.
  """
  probe = start()
  from weavingspace_qgis import bridge

  clean = True
  timings = []
  for gaps in (False, True):
    print()
    print(f"#### a region {'WITH MISSING VALUES' if gaps else 'that is complete'}",
          flush=True)
    for elements in COUNTS:
      print(f"---- {elements} elements", flush=True)
      dlg = a_drawn_map(probe, elements, 900.0, gaps)
      if dlg is None:
        print(f"     ({elements} is not on offer)")
        continue
      jobs = jobs_from(dlg)
      assert jobs, "PREMISE: the map produced no layers to write"
      # THE PREMISE THE FIRST RUN OF THIS PROBE LACKED. Without
      # missing values no twin is written and the null branch is never
      # reached, so the gappy arm is worth nothing unless it really is
      # gappy -- which is how a mutation removing null handling came
      # back invisible.
      twins = [name for _l, name in jobs if name.endswith("_no_data")]
      if gaps:
        assert twins, (
          "PREMISE: the gappy region produced no no-data twin, so this "
          "arm covers neither the twin tables nor the null branch")
      else:
        assert not twins, (
          "PREMISE: the complete region produced a twin, so the two "
          "arms are not the contrast this probe claims")

      # BOTH ARMS IN ONE RUN, back to back, which is the only honest
      # way to compare them: this machine has been running QGIS all
      # session, and single samples taken minutes apart moved a
      # 32-element save between 1.1s and 2.9s on identical code. A
      # measurement that does not resolve is not a measurement.
      old_path = probe.path(f"per_layer_{elements}_{int(gaps)}.gpkg")
      started = time.monotonic()
      fresh = True
      for layer, table in jobs:
        bridge.write_gpkg_layer(layer, old_path, table, first=fresh,
                                open_after=False)
        fresh = False
      per_layer_seconds = time.monotonic() - started

      new_path = probe.path(f"session_{elements}_{int(gaps)}.gpkg")
      started = time.monotonic()
      written, trouble = bridge.write_gpkg_layers(jobs, new_path,
                                                  recreate=True)
      session_seconds = time.monotonic() - started
      timings.append((elements, gaps, len(jobs), per_layer_seconds,
                      session_seconds))
      if trouble:
        clean = False
        print(f"     the session writer reported trouble: {trouble}")
      missing = {name for _l, name in jobs} - written
      if missing:
        clean = False
        print(f"     the session writer did not write: {sorted(missing)}")

      dlg.close()
      probe.clear()

      faults = compare(describe(old_path), describe(new_path), elements)
      if faults:
        clean = False
        print(f"     {len(faults)} DIFFERENCE(S) at {elements} elements:")
        for line in faults:
          print(f"       - {line}")
      else:
        print(f"     {len(jobs)} tables ({len(twins)} of them twins) "
              f"identical in every column, count, value and geometry",
              flush=True)

  print()
  print("=" * 78)
  print("WHAT THE SESSION COSTS AGAINST THE PER-LAYER LOOP")
  print("=" * 78)
  print(f"  {'elements':>9}{'gaps':>7}{'tables':>8}"
        f"{'per-layer':>12}{'session':>10}{'times':>8}")
  for elements, gaps, tables, old, new in timings:
    speed = (old / new) if new > 0 else float("inf")
    print(f"  {elements:>9}{'yes' if gaps else 'no':>7}{tables:>8}"
          f"{old:>11.2f}s{new:>9.2f}s{speed:>7.1f}x")
  print()
  print("  Both arms run back to back inside ONE process on the same")
  print("  map, which is what makes the ratio mean anything on a")
  print("  machine that has been busy all session.")

  print()
  print("=" * 78)
  print("THE TWO WRITERS AGREE" if clean else
        "THE TWO WRITERS DISAGREE -- the differences are listed above")
  print("=" * 78)


main()
