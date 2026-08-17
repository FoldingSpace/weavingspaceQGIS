"""Profile the FIXED per-run cost of a large-spacing render.

The tester's narrowing decides the design: small spacings are not
slower, large "auto" spacing has lost its snap. Large spacing means
few tiles, so what dominates is whatever a run costs regardless of
size -- and that is what this drives, several runs at the spacing the
plugin picks for itself, with the tile count held near constant.

TWO TRAPS THIS PROJECT HAS ALREADY PAID FOR, avoided by construction.
`python -m cProfile -o` writes nothing here, because these harnesses
end in `os._exit` and cProfile dumps at interpreter shutdown -- so the
stats are dumped by this script before it exits. And the number to
read is the CALL COUNT, not the seconds: profiler overhead swamps the
totals, and on 2026-08-16 the self-time ratio understated a threefold
difference as 1.2x while the counts carried it exactly.

Env: WEAVINGSPACE_REPO (which tree to measure), PERF_OUT (where to
write the stats), PERF_RUNS (how many renders, default 6).
"""
import cProfile
import importlib.util
import os
import pstats
import sys

REPO = os.environ["WEAVINGSPACE_REPO"]
OUT = os.environ["PERF_OUT"]
RUNS = int(os.environ.get("PERF_RUNS", "6"))
os.chdir(REPO)
sys.path.insert(0, REPO)

spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

from qgis.core import QgsApplication, QgsProject          # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()
T._no_modal_dialogs()


def build():
  """A dialog on a region layer, at the spacing the plugin chooses."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  project.clear()
  T._tick(100)
  layer = T.make_region_layer(n=6)
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=T._Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  T._tick(400)
  return dlg


def renders(dlg, runs):
  """`runs` full runs at a LARGE spacing, tile count near constant.

  Args:
    dlg: an open dialog with a region layer already chosen.
    runs: how many full runs to drive.

  Returns:
    None; the dialog has run that many times when it returns.

  The spacing alternates by one metre so each press is a genuine
  geometry change -- a no-op run is skipped by the signature and would
  measure nothing -- while the tile count stays effectively the same,
  which is what keeps this a measurement of FIXED cost.
  """
  auto = dlg.spacing_spin.value()
  for i in range(runs):
    dlg.spacing_spin.setValue(auto + (i % 2))
    T._generate_and_wait(dlg)
    T._tick(120)


def main():
  """Warm, then profile the runs, then dump the stats before exiting."""
  dlg = build()
  auto = dlg.spacing_spin.value()
  renders(dlg, 1)                      # warm: imports, first tiling
  tiles = sum(1 for _ in ())
  ids = dict(dlg._element_layer_ids)
  project = QgsProject.instance()
  tiles = sum(project.mapLayer(i).featureCount()
              for i in ids.values() if project.mapLayer(i) is not None)
  print(f"auto spacing {auto}, {len(ids)} element layers, {tiles} tiles")

  profiler = cProfile.Profile()
  profiler.enable()
  renders(dlg, RUNS)
  profiler.disable()
  # dumped HERE, before anything can exit through os._exit
  profiler.dump_stats(OUT)
  stats = pstats.Stats(profiler)
  print(f"total calls profiled: {stats.total_calls}")
  print(f"wrote {OUT}")
  dlg.close()


main()
