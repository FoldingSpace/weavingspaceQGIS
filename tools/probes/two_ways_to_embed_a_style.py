"""Does a style written in one session say the same as QGIS's own?

`bridge.embed_styles` writes the `layer_styles` rows itself, in one
OGR session, because doing it through QGIS's per-layer call opens the
GeoPackage once per element -- 32.97s of a 79.9s save at the
256-element ceiling, growing 3.5x per doubling.

WRITING SOMEBODY ELSE'S FORMAT IS THE RISK, and it lands on what a
colleague receives.

THE COMPARISON HAS TO BE OF ONE LAYER, AT ONE MOMENT, BY TWO ROUTES.
A first version of this probe saved the map twice and rebuilt the
layers for the second arm -- copying the renderer, the opacity and
the custom properties onto fresh objects -- and duly reported that
the two QMLs differed by about fifty characters. That was the
REBUILT LAYER differing from the original, not the writer: a control
arm is a second fixture and it inherits whatever you put in it.

So each layer here has BOTH routes applied to it, into the SAME file,
under two style names, and the two stored documents are compared. The
only thing that differs between them is the code that wrote them.
"""

import os
import sys

sys.path.insert(0, os.environ.get("WS_REPO", os.getcwd()))

from tools.probe_kit import start                      # noqa: E402

COUNTS = tuple(int(n) for n in
               os.environ.get("WS_STYLE_COUNTS", "4,12").split(","))
BY_QGIS = "PROBE_qgis_route"
BY_US = "PROBE_session_route"


def a_saved_map(probe, elements: int, spacing: float):
  """Draw and save a map; return the dialog, its path and its jobs.

  Args:
    probe: the running `Probe`.
    elements: how many elements the design should carry.
    spacing: map units between repeats.

  Returns:
    ``(dialog, path, jobs)`` where jobs is the (layer, table) list the
    save wrote, or ``(None, None, None)`` where the count is not
    offered. The layers are left reading from the file, which is the
    state both style routes are asked in.
  """
  from qgis.core import QgsProject
  from weavingspace_qgis import bridge
  probe.clear()
  dlg, _layer, _tid = probe.dialog()
  if not (dlg.n_spin.minimum() <= elements <= dlg.n_spin.maximum()):
    dlg.close()
    return None, None, None
  dlg.n_spin.setValue(elements)
  probe.suite._tick(600)
  dlg.spacing_spin.setValue(spacing)
  probe.suite._generate_and_wait(dlg)
  assert len(dlg._element_layer_ids) == elements, (
    f"PREMISE: asked for {elements} and drew "
    f"{len(dlg._element_layer_ids)}")
  path = probe.path(f"styles_{elements}.gpkg")
  assert probe.save(dlg, path), "PREMISE: the save failed"

  project = QgsProject.instance()
  tables = dict(getattr(dlg, "_element_tables", {}) or {})
  jobs = []
  for tid in sorted(dlg._element_layer_ids, key=bridge.element_order):
    name = tables.get(tid) or bridge.element_table_name(
      tid, (dlg._assignment_for(tid) or {}).get("var"))
    for layer_id, table in (
        (dlg._element_layer_ids.get(tid), name),
        (dlg._no_data_layer_ids.get(tid), f"{name}_no_data")):
      layer = project.mapLayer(layer_id) if layer_id else None
      if layer is not None:
        jobs.append((layer, table))
  assert jobs, "PREMISE: the saved map produced no layers"
  return dlg, path, jobs


def stored(path: str, style_name: str):
  """The styleQML and styleSLD stored under one style name, by table.

  Args:
    path: the GeoPackage to read, opened read only and released.
    style_name: which `styleName` to collect.

  Returns:
    A dict from table name to ``(qml, sld)``.
  """
  from osgeo import ogr
  out = {}
  data = ogr.Open(path, 0)
  assert data is not None, f"PREMISE: {path} would not open"
  try:
    result = data.ExecuteSQL(
      "SELECT f_table_name, styleQML, styleSLD, useAsDefault, "
      "description, f_geometry_column, f_table_catalog, f_table_schema, "
      "owner FROM layer_styles WHERE styleName = '%s'"
      % style_name.replace("'", "''"))
    if result is None:
      return out
    for row in result:
      out[row.GetField("f_table_name")] = {
        "qml": row.GetField("styleQML"),
        "sld": row.GetField("styleSLD"),
        "useAsDefault": row.GetField("useAsDefault"),
        "description": row.GetField("description"),
        "geometry_column": row.GetField("f_geometry_column"),
        "catalog": row.GetField("f_table_catalog"),
        "schema": row.GetField("f_table_schema"),
        "owner": row.GetField("owner"),
      }
    data.ReleaseResultSet(result)
  finally:
    data = None
  return out


def first_difference(a: str, b: str) -> str:
  """Where two documents first diverge, with a little either side.

  Args:
    a: one document.
    b: the other.

  Returns:
    A short sentence naming the offset and quoting both. A length is
    not a diagnosis -- this project has read "differs by fifty
    characters" as a defect in a writer when it was a difference in
    the fixture -- so the report says WHAT differs.
  """
  if a is None or b is None:
    return f"one is missing (qgis={a is not None}, session={b is not None})"
  for i, (x, y) in enumerate(zip(a, b)):
    if x != y:
      return (f"at character {i}: qgis {a[max(0, i - 30):i + 40]!r} "
              f"against session {b[max(0, i - 30):i + 40]!r}")
  return f"one is longer ({len(a)} against {len(b)})"


def main():
  """Apply both style routes to each layer and compare what was stored.

  Returns:
    None; it prints. Every difference is named rather than the first.
  """
  probe = start()
  from weavingspace_qgis import bridge, compat

  clean = True
  for elements in COUNTS:
    print(f"---- {elements} elements", flush=True)
    dlg, path, jobs = a_saved_map(probe, elements, 900.0)
    if dlg is None:
      print(f"     ({elements} is not on offer)")
      continue

    # TWO FILES, ONE LAYER, ITS OWN NAME. A first version wrote both
    # routes into one file under two style names, and reported two
    # differences that were both the probe's: the SLD embeds the
    # LAYER'S NAME, which the renaming had changed, and `useAsDefault`
    # flipped because our own writer correctly demotes the other rows
    # on the table. Neither said anything about the writer.
    # So the file is COPIED and each route writes into its own copy,
    # with the layer left exactly as it is. `save_style_to_database`
    # writes into whatever file the LAYER reads from, which is why
    # QGIS's route gets the original and ours gets the copy.
    import shutil
    ours_path = probe.path(f"session_{elements}.gpkg")
    shutil.copyfile(path, ours_path)
    bridge.embed_styles(ours_path, jobs)
    for layer, _table in jobs:
      compat.save_style_to_database(layer, layer.name()[:30],
                                    bridge.SEEDED_BY_US)

    theirs = {}
    ours = {}
    for layer, table in jobs:
      name = layer.name()[:30]
      theirs.update(stored(path, name))
      ours.update(stored(ours_path, name))
    assert theirs, "PREMISE: QGIS's own route stored nothing to compare"
    assert ours, "PREMISE: the session route stored nothing to compare"

    faults = []
    if set(theirs) != set(ours):
      faults.append(
        f"different tables: only qgis {sorted(set(theirs) - set(ours))[:3]}, "
        f"only session {sorted(set(ours) - set(theirs))[:3]}")
    for table in sorted(set(theirs) & set(ours)):
      a, b = theirs[table], ours[table]
      if a["qml"] != b["qml"]:
        faults.append(f"{table}: styleQML {first_difference(a['qml'], b['qml'])}")
      if a["sld"] != b["sld"]:
        faults.append(f"{table}: styleSLD {first_difference(a['sld'], b['sld'])}")
      for column in ("useAsDefault", "description", "geometry_column",
                     "catalog", "schema", "owner"):
        if a[column] != b[column]:
          faults.append(f"{table}: {column} is {a[column]!r} "
                        f"against {b[column]!r}")

    dlg.close()
    probe.clear()

    if faults:
      clean = False
      print(f"     {len(faults)} DIFFERENCE(S) over "
            f"{len(set(theirs) & set(ours))} tables:")
      for line in faults[:8]:
        print(f"       - {line[:300]}")
      if len(faults) > 8:
        print(f"       ... and {len(faults) - 8} more")
    else:
      print(f"     {len(ours)} rows written identically by both routes",
            flush=True)

  print()
  print("=" * 78)
  print("THE TWO STYLE ROUTES AGREE" if clean else
        "THE TWO STYLE ROUTES DISAGREE -- listed above")
  print("=" * 78)


main()
