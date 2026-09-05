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
import ast
import os
import pstats
import subprocess
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
  ("  Tiling.__init__ (constructor total)", "tile_map.py", "__init__", 272),
  ("  _TileGrid.__init__ (lays the grid)", "tile_map.py", "__init__", 112),
  ("  get_tiled_map (overlay and join)", "tile_map.py", "get_tiled_map"),
  ("landing: _add_output_layers", "dialog.py", "_add_output_layers"),
  ("  gdf_to_layer (frame -> QGIS layer)", "bridge.py", "gdf_to_layer"),
  ("  seed_renderer (symbology)", "bridge.py", "seed_renderer"),
  ("  make_graduated_renderer", "bridge.py", "make_graduated_renderer"),
  ("  make_categorized_renderer", "bridge.py", "make_categorized_renderer"),
  ("  split_out_the_no_data (the twins)", "bridge.py",
   "split_out_the_no_data"),
  ("  _get_or_make_group (the layer tree)", "dialog.py",
   "_get_or_make_group"),
  ("  _update_layer_exclusions (the combo)", "dialog.py",
   "_update_layer_exclusions"),
  ("  _layers_removed (the signal cascade)", "dialog.py",
   "_layers_removed"),
  ("  _apply_element_records", "dialog.py", "_apply_element_records"),
  ("  stamp_working_state", "dialog.py", "_stamp_working_state"),
  ("  stamp_category_colours", "dialog.py", "_stamp_category_colours"),
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



def every_stage_names_a_real_function():
  """Refuse a stage whose function does not exist in the file it names.

  Returns:
    Nothing. Raises AssertionError naming every bad stage.

  WHY THIS EXISTS. The stage `split_absent` was carried here from
  2026-09-03 to 2026-09-04 and there is no such function -- the
  no-data split is `bridge.split_out_the_no_data`. A name that matches
  nothing contributes nothing, falls under the printing floor, and is
  INDISTINGUISHABLE from a stage that is genuinely cheap: the row
  simply does not appear, and a reader concludes the work is free.
  That is this project's own "a check that can only confirm is not a
  check", arriving inside the instrument rather than inside a gate,
  and docs/PERFORMANCE.md honestly listed the twin split as unmeasured
  the whole time the probe claimed to measure it.

  The check is over the SOURCE rather than over the profile, because a
  function that exists and was not CALLED on this journey is a
  legitimate absence and a name that does not exist is a defect in this
  file. Only the second is refusable.
  """
  root = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
  wanted = {}
  for stage in STAGES:
    _label, basename, name = stage[0], stage[1], stage[2]
    wanted.setdefault(basename, set()).add(name)
  missing = []
  for basename, names in wanted.items():
    found = set()
    for folder in ("weavingspace_qgis",
                   os.path.join("weavingspace_qgis", "vendor",
                                "weavingspace")):
      path = os.path.join(root, folder, basename)
      if not os.path.exists(path):
        continue
      tree = ast.parse(open(path, encoding="utf-8").read())
      for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
          found.add(node.name)
    missing += [f"{basename}:{n}" for n in sorted(names - found)]
  assert not missing, (
    "these stages name functions that do not exist, so each would "
    "report NOTHING and read as a stage that costs nothing: "
    + ", ".join(missing))


def cumulative(stats, basename, name, line=None):
  """Cumulative seconds for one function, summed over its call sites.

  Args:
    stats: a `pstats.Stats` from one profiled press.
    basename: the file the function lives in, e.g. "bridge.py".
    name: the function's own name.
    line: the line its `def` sits on, where the file defines that name
      more than once. Omitted means "any", which is right wherever the
      name is unique and refused below where it is not -- cProfile
      keys on (file, line, function) and knows nothing about classes,
      so a def line is the only way to say WHICH `__init__`.

  Returns:
    (seconds, calls). Zero where the function never ran, which is a
    finding rather than a gap -- a stage that does not appear did not
    happen on this journey. (-1.0, n) where n functions of that name
    matched, which the caller must report rather than sum.
  """
  total, calls, seen = 0.0, 0, []
  for func, (_cc, nc, _tt, ct, _callers) in stats.stats.items():
    filename, defined_at, fname = func
    if os.path.basename(filename) == basename and fname == name \
       and (line is None or defined_at == line):
      total += ct
      calls += nc
      seen.append((defined_at, fname))
  # AMBIGUITY IS A FAULT, NOT A SUM. `tile_map.py` defines __init__
  # twice -- _TileGrid at 112 and Tiling at 272 -- and _TileGrid is
  # built INSIDE Tiling's constructor, so a match on basename plus
  # "__init__" sums a child into its parent and reports a stage that
  # costs roughly twice what it does. Naming the class is not possible
  # here: cProfile keys on (file, line, function) and knows nothing
  # about classes, so the honest answer is to REFUSE and make the
  # caller disambiguate by line.
  if len(seen) > 1:
    return -1.0, len(seen)
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
  dlg.gpkg_widget.setFilePath(path)
  T._tick(200)
  save = cProfile.Profile()
  save.enable()
  T.press_save(dlg, path)
  save.disable()

  dlg.close()
  T._tick(100)
  return pstats.Stats(generate), pstats.Stats(save), drawn


def one_spacing(spacing):
  """Measure ONE size and print its block. Runs in a child process."""
  from qgis.core import QgsApplication
  QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  app = QgsApplication([], False)      # BOUND: an unbound one is collected
  app.initQgis()
  T = harness()
  T._no_modal_dialogs()
  folder = tempfile.mkdtemp(prefix="ws_generate_cost_")
  gen, save, drawn = one_run(T, spacing, folder)
  print(f"--- spacing {spacing}: {drawn} features drawn")
  print(f"    {'stage':<38} {'generate':>10} {'save':>10}   calls")
  shown = 0
  for stage in STAGES:
    label, basename, name = stage[0], stage[1], stage[2]
    at = stage[3] if len(stage) > 3 else None
    g, gc = cumulative(gen, basename, name, at)
    s_, sc = cumulative(save, basename, name, at)
    if g < 0 or s_ < 0:
      print(f"    {label:<38}  AMBIGUOUS: {max(gc, sc)} functions in "
            f"{basename} are called {name}")
      continue
    if g > 0.002 or s_ > 0.002:
      print(f"    {label:<38} {g:9.3f}s {s_:9.3f}s   {gc + sc}")
      shown += 1
  print(f"CHILD COMPLETE: spacing {spacing}, {shown} stage(s) over the floor")


def main():
  """One spacing per process, because a stage table run in one process
  inflates with position -- 2.160s at spacing 350 where a fresh process
  reports 0.250, measured 2026-09-03 and written up in
  docs/PERFORMANCE.md. The first version of THIS probe drove both
  spacings in one process and its second row was therefore not a
  measurement; that is the same fault the sibling probe was already
  built to avoid.

  The child INHERITS this process's environment deliberately: it needs
  the same QGIS interpreter and prefix, so a chosen-environment child
  (the usual rule for subprocesses here) would not start at all.
  """
  assert os.path.exists(REGION), f"PREMISE: no region fixture at {REGION}"
  every_stage_names_a_real_function()

  if len(sys.argv) > 1:
    one_spacing(float(sys.argv[1]))
    return

  print("generation stages, ONE SPACING PER PROCESS")
  for spacing in SPACINGS:
    finished = subprocess.run(
      [sys.executable, os.path.abspath(__file__), str(spacing)],
      capture_output=True, text=True, check=False)
    body = [l for l in finished.stdout.split("\n")
            if l.startswith("---") or l.startswith("    ")]
    if any("CHILD COMPLETE" in l for l in finished.stdout.split("\n")):
      print("\n" + "\n".join(body))
    else:
      # A child that says nothing is not a child that measured nothing.
      print(f"\n--- spacing {spacing}: CHILD DID NOT COMPLETE "
            f"(exit {finished.returncode})")
      print(finished.stdout[-800:] or "(no stdout)")
      print(finished.stderr[-800:] or "(no stderr)")

  print("\nShares rather than wall clock: the profiler inflates every "
        "figure, and the sibling probe measures the wall unprofiled.")
  print("\nPROBE COMPLETE: every spacing ran in its own process.")


main()
