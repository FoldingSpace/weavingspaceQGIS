"""What a whole Generate costs, stage by stage, and what a Save adds.

THE TILING IS NOT THE WHOLE RUN, and until 2026-09-03 nothing here had
measured the rest. `tools/probes/what_the_tiled_map_costs.py` attributes
`get_tiled_map`; `tools/probes/interaction_cost.py` measures the fixed
per-run cost on a small synthetic region. What neither says is where a
REAL Generate on REAL data spends its seconds once the tiles exist:
converting them to QGIS layers, seeding renderers, splitting off the
no-data twins, stamping the layer tree, and -- on a Save -- writing the
GeoPackage.

IT DRIVES THE DIALOG rather than calling the bridge directly, because
the product is where the arguments are parsed and the defaults chosen,
and a fixture that supplies the thing under test measures nothing about
how the product produces it.

IT READS CUMULATIVE TIME PER FUNCTION from one profiled press, which is
the shape `where_the_load_spends_its_time.py` established here: the
seconds are spent inside QGIS's and GEOS's C++, so self time attributes
almost nothing and cumulative attributes the ACT.

AND THE ABSOLUTE FIGURES ARE INFLATED BY THE PROFILER. What is being
asked is the SHARE each stage takes, not its wall clock; where a wall
figure is wanted, the sibling probe measures it unprofiled.

    unset PYTHONHOME PROJ_LIB QGIS_PREFIX_PATH
    set -a; eval "$(bash tools/macos_qgis_env.sh)"; set +a
    QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1 \\
      "$QGIS_PY" -u tools/probes/what_a_generate_spends_its_time_on.py
"""
import cProfile
import importlib.util
import os
import pstats
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGION = os.path.join(ROOT, "tests", "data", "imd-auckland-sa2-2018.gpkg")
SPACINGS = (500, 250)

# THE STAGES, named by the function that performs each, so a reader can
# check the attribution rather than trust a label. Ordered as a run
# performs them.
STAGES = [
  ("worker: Tiling() + get_tiled_map", "dialog.py", "work"),
  ("  Tiling.__init__ (lays the grid)", "tile_map.py", "__init__"),
  ("  get_tiled_map (overlay and join)", "tile_map.py", "get_tiled_map"),
  ("landing: _add_output_layers", "dialog.py", "_add_output_layers"),
  ("  gdf_to_layer (frame -> QGIS layer)", "bridge.py", "gdf_to_layer"),
  ("  seed_renderer (symbology)", "bridge.py", "seed_renderer"),
  ("  make_graduated_renderer", "bridge.py", "make_graduated_renderer"),
  ("  make_categorized_renderer", "bridge.py", "make_categorized_renderer"),
  ("  split_absent (the no-data twins)", "bridge.py", "split_absent"),
  ("  stamp_working_state", "dialog.py", "_stamp_working_state"),
  ("preview: _rebuild_unit", "dialog.py", "_rebuild_unit"),
  ("save: _save_the_map", "dialog.py", "_save_the_map"),
  ("  write_gpkg_layers", "bridge.py", "write_gpkg_layers"),
  ("  point_layer_at", "compat.py", "point_layer_at"),
  ("  embed_style", "bridge.py", "embed_style"),
]


def harness():
  """The suite's own helpers, loaded as a module.

  Returns:
    The `tests/run_tests.py` module. Loaded rather than re-implemented
    because its dialog fixtures, its modal shim and its waiters are the
    ones every other measurement here uses, and a second copy of them
    would drift.
  """
  spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


def cumulative(stats, basename, name):
  """Cumulative seconds for one function, summed over its call sites.

  Args:
    stats: a `pstats.Stats` from one profiled press.
    basename: the file the function lives in, e.g. "bridge.py".
    name: the function's own name.

  Returns:
    (seconds, calls). Zero where the function never ran, which is a
    finding rather than a gap -- a stage that does not appear did not
    happen on this journey.
  """
  total, calls = 0.0, 0
  for func, (_cc, nc, _tt, ct, _callers) in stats.stats.items():
    filename, _line, fname = func
    if os.path.basename(filename) == basename and fname == name:
      total += ct
      calls += nc
  return total, calls


def one_run(T, spacing, folder):
  """Profile a Generate and then a Save, at one spacing.

  Args:
    T: the harness module.
    spacing: tile spacing in map units.
    folder: a directory to save into.

  Returns:
    (generate stats, save stats, tiles drawn).
  """
  from qgis.core import QgsProject, QgsVectorLayer
  from weavingspace_qgis.dialog import WeavingSpaceDialog

  project = QgsProject.instance()
  project.clear()
  T._tick(100)
  region = QgsVectorLayer(REGION, "auckland", "ogr")
  assert region.isValid(), f"PREMISE: {REGION} did not load"
  project.addMapLayer(region)

  dlg = WeavingSpaceDialog(iface=T._Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(region)
  T._tick(400)
  dlg.spacing_spin.setValue(spacing)
  T._tick(300)

  generate = cProfile.Profile()
  generate.enable()
  T._generate_and_wait(dlg)
  generate.disable()

  drawn = sum(
    project.mapLayer(i).featureCount()
    for i in dlg._element_layer_ids.values()
    if project.mapLayer(i) is not None)

  path = os.path.join(folder, f"map_{int(spacing)}.gpkg")
  dlg.out_edit.setFilePath(path)
  T._tick(200)
  save = cProfile.Profile()
  save.enable()
  T.press_save(dlg, path)
  save.disable()

  dlg.close()
  T._tick(100)
  return pstats.Stats(generate), pstats.Stats(save), drawn


def main():
  """Two spacings, each in its own dialog, generate then save."""
  assert os.path.exists(REGION), f"PREMISE: no region fixture at {REGION}"
  from qgis.core import QgsApplication
  QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  app = QgsApplication([], False)      # BOUND: an unbound one is collected
  app.initQgis()
  T = harness()
  T._no_modal_dialogs()

  folder = tempfile.mkdtemp(prefix="ws_generate_cost_")
  for spacing in SPACINGS:
    gen, save, drawn = one_run(T, spacing, folder)
    print(f"\n--- spacing {spacing}: {drawn} features drawn")
    print(f"    {'stage':<38} {'generate':>10} {'save':>10}   calls")
    for label, basename, name in STAGES:
      g, gc = cumulative(gen, basename, name)
      s, sc = cumulative(save, basename, name)
      if g > 0.002 or s > 0.002:
        print(f"    {label:<38} {g:9.3f}s {s:9.3f}s   {gc + sc}")
  print("\nShares rather than wall clock: the profiler inflates every "
        "figure, and the sibling probe measures the wall unprofiled.")
  print("\nPROBE COMPLETE: both spacings reported, teardown next.")


main()
