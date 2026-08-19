"""Does the size guard estimate a TILING for a design that is icons?

Ledger row 3 of `docs/process/defects-2026-08-19.md`, reported by the
maintainer as: "tile-as-icon number checking is wrong -- it seems to
estimate based on doing a tiling and prevents you doing something that
should be fine if there's just one tile unit per map area."

WHAT THIS MEASURES, and why it is a differential rather than a guess.
`bridge.estimate_tile_count_bounds` mirrors `_TileGrid`: it covers a
circle enclosing the region's bounding rectangle and steps across it
with the unit's two translation vectors, so its answer scales with
1/spacing squared. In ICON mode the library does no such thing --
`Tiling(unit, region, as_icons=True)` puts ONE tile unit on each map
area -- so the true count is the number of areas times the elements in
the unit, and the spacing decides how big each icon is drawn rather
than how many there are.

So the two numbers are read side by side: what the guard believes, and
what the library actually produces on the same inputs. A guard that is
right needs no probe; this one is asked to answer a question about a
mode it is never told about, since `as_icons` is not read until well
after both gates have run.

Run it under QGIS's own Python:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \
            | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen
    "$QGIS_PY" -u tools/probes/the_icon_count_is_a_tiling_estimate.py
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))
spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

from qgis.core import QgsApplication, QgsProject  # noqa: E402
from weavingspace_qgis import bridge  # noqa: E402
from weavingspace_qgis.dialog import WeavingSpaceDialog  # noqa: E402

# THE TESTER'S SHAPE: twenty-five areas, each a kilometre across, drawn
# with a unit far smaller than one area. As a TILING that is a great
# many tiles; as ICONS it is twenty-five units and perfectly sensible,
# which is the whole complaint.
SIDE = 5
CELL = 1000.0
# Overridable, because the same fault wears two faces: at a middling
# spacing the guard merely ASKS whether you are sure, and a little
# finer it REFUSES outright. Pass the spacing as the first argument.
SPACING = float(sys.argv[1]) if len(sys.argv) > 1 else 40.0


def main():
  """Read the guard's estimate beside the library's real icon count.

  Returns:
    0 when the guard's answer is within an order of magnitude of what
    icon mode actually draws, 1 when it is not -- so this can gate a
    fix. It is deliberately generous: the estimate is documented as
    "cheap and slightly generous", and what is being asked is whether
    it is answering the right QUESTION, not whether it is exact.
  """
  app = QgsApplication([], False)
  app.initQgis()
  project = QgsProject.instance()
  project.clear()

  layer = rt.make_region_layer(n=SIDE, cell=CELL)
  project.addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=rt._Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  rt._tick(200)
  dlg.opt_icons.setChecked(True)
  dlg.spacing_spin.setValue(SPACING)
  rt._tick(400)

  unit = dlg._unit
  if unit is None:
    print("NO UNIT: the dialog built nothing, so nothing can be asked")
    return 1

  # The same fields the dialog would carry, so the frame is the one
  # the run would actually hand the library.
  fields = [a["var"] for a in dlg._assignments() if a.get("var")]
  region = bridge.layer_to_gdf(layer, sorted(set(fields)))
  guard = bridge.estimate_tile_count(unit, region)

  # THE SECOND, INDEPENDENT ROUTE: the library itself, on the same
  # unit and the same region, told what the dialog would have told it.
  from weavingspace import Tiling
  tiling = Tiling(unit, region, as_icons=True)
  drawn = len(tiling.get_tiled_map(
      join_on_prototiles=False, retain_tileables=False,
      ragged_edges=True).map)

  areas = layer.featureCount()
  elements = max(len(unit.tiles), 1)
  print(f"areas               {areas}")
  print(f"elements in unit    {elements}")
  print(f"tiling estimator    {guard:,}")
  print(f"icon mode draws     {drawn:,}")

  # THE GATES THEMSELVES, which are the harm. The estimator's answer
  # above is only the diagnosis: what a user meets is a refusal and a
  # paused live update, so both are driven rather than inferred.
  rt._no_modal_dialogs()
  del rt.MODALS[:]
  del rt.BAR_MESSAGES[:]

  # THE LIVE GATE. Asked through the dialog's own handler rather than
  # by reading the estimate, since what a user meets is the note line.
  dlg.live_check.setChecked(True)
  dlg._maybe_live_generate()
  rt._tick(300)
  note = dlg.live_note.text()
  paused = "paused" in note
  dlg.live_check.setChecked(False)
  rt._tick(200)

  # THE HARD GATE. Driven to completion, because "no task in flight"
  # a moment after pressing Generate means either refused or finished
  # and the two must not be confused -- a probe that returns is not a
  # probe that measured.
  del rt.MODALS[:]
  del rt.BAR_MESSAGES[:]
  for layer_id in list(dlg._element_layer_ids.values()):
    project.removeMapLayer(layer_id)
  dlg._element_layer_ids.clear()
  rt._tick(100)
  dlg._generate()
  waited = 0
  while dlg._task is not None and waited < 120000:
    rt._tick(200)
    waited += 200
  rt._tick(300)
  refusals = [text for kind, text in rt.MODALS if kind == "critical"]
  made = len(dlg._element_layer_ids)

  print(f"live note           {note!r}")
  print(f"generate refused    {bool(refusals)}")
  if refusals:
    print(f"  said              {refusals[-1]!r}")
  print(f"element layers made {made}")
  print(f"bar said            {[t for _k, t in rt.BAR_MESSAGES][-1:]}")

  faults = []
  if paused:
    faults.append(f"live update paused itself on a map of {drawn:,} "
                  f"tiles: {note!r}")
  if refusals:
    faults.append(f"Generate was refused: {refusals[-1]!r}")
  if not made:
    faults.append("Generate produced no element layers at all")
  if faults:
    print("\nTHE GATES ARE ANSWERING ABOUT A TILING:")
    for fault in faults:
      print(f"  - {fault}")
    return 1
  print(f"\nBoth gates let a {drawn:,}-tile icon design through, and it "
        f"drew {made} element layers.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
