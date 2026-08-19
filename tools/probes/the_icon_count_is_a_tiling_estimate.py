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
  print(f"guard estimates     {guard:,}")
  print(f"icon mode draws     {drawn:,}")
  print(f"hard ceiling        {bridge.MAX_TILES_HARD:,}")
  print(f"confirm threshold   {bridge.MAX_TILES_CONFIRM:,}")
  print(f"refused outright    {guard > bridge.MAX_TILES_HARD}")
  print(f"asks 'are you sure' {guard > bridge.MAX_TILES_CONFIRM}")
  print(f"live update paused  {guard > bridge.LIVE_UPDATE_MAX_TILES}")

  if drawn and guard > 10 * drawn:
    print(f"\nTHE GUARD IS ANSWERING ABOUT A TILING. It estimates "
          f"{guard:,} where icon mode draws {drawn:,}, a factor of "
          f"{guard / drawn:,.0f}. The spacing decides how big an icon "
          f"is, not how many there are.")
    return 1
  print("\nThe guard's answer is the right order for what is drawn.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
