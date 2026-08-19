"""Does the size guard refuse a design the library draws happily?

Ledger row 23. Reported by the maintainer on 2026-08-19 as a
performance comparison and answered as a refusal: the plugin declines
the exact design their own upstream script renders in about twelve
seconds.

WHAT THIS MEASURES, and it is a differential rather than a guess.
`bridge.estimate_tile_count` mirrors `_TileGrid`: it covers a CIRCLE
enclosing the region's bounding rectangle and steps across it with the
unit's two translation vectors. `Tiling` then CLIPS to the polygons.
Where the data is sparse inside its own extent -- which most real data
is -- the circle is mostly empty and the estimate counts tiles that
are never made.

It takes the region file as an ARGUMENT because the dataset that
provoked it is the maintainer's own and does not live in this
repository; any sparse polygon layer will do.

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \
            | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen
    "$QGIS_PY" -u tools/probes/the_size_guard_counts_an_empty_circle.py \
        <region.gpkg> [layername] [n] [spacing]
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

from qgis.core import QgsApplication, QgsProject, QgsVectorLayer  # noqa: E402
from weavingspace_qgis import bridge                              # noqa: E402
from weavingspace_qgis.dialog import WeavingSpaceDialog           # noqa: E402


def main():
  """Read the guard's estimate beside what the library really draws.

  Returns:
    0 when the estimate is within twice what is drawn, 1 when it is
    not. Deliberately generous: the estimate is documented as "cheap
    and slightly generous", and what is asked here is whether it is
    answering the right QUESTION.
  """
  if len(sys.argv) < 2:
    print(__doc__)
    return 2
  path = sys.argv[1]
  name = sys.argv[2] if len(sys.argv) > 2 else None
  n = int(sys.argv[3]) if len(sys.argv) > 3 else 23
  spacing = float(sys.argv[4]) if len(sys.argv) > 4 else 10000.0

  app = QgsApplication([], False)
  app.initQgis()
  rt._no_modal_dialogs()
  QgsProject.instance().clear()
  uri = f"{path}|layername={name}" if name else path
  layer = QgsVectorLayer(uri, "region", "ogr")
  if not layer.isValid():
    print(f"THE LAYER DID NOT LOAD from {uri!r}; nothing was measured")
    return 2
  QgsProject.instance().addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=rt._Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  rt._tick(300)
  dlg.kind_combo.setCurrentText("Tiling")
  rt._tick(250)
  # N BEFORE THE FAMILY: picking n repopulates the family list, whose
  # entries carry the count in their names ("grid 23"), so a family
  # chosen first is silently reset to the first entry.
  dlg.n_combo.setCurrentText(str(n))
  rt._tick(500)
  dlg.family_combo.setCurrentText(f"grid {n}")
  rt._tick(500)
  dlg.spacing_spin.setValue(spacing)
  rt._tick(600)
  if dlg._unit is None:
    print("NO UNIT was built, so nothing can be asked of the guard")
    return 2

  fields = [f.name() for f in layer.fields() if f.isNumeric()][:n]
  region = bridge.layer_to_gdf(layer, sorted(set(fields)))
  guess = bridge.estimate_tile_count(dlg._unit, region)

  from weavingspace import Tiling
  drawn = len(Tiling(dlg._unit, region).get_tiled_map(
      join_on_prototiles=False, rotation=0).map)

  print(f"areas in the region : {layer.featureCount():,}")
  print(f"guard estimate      : {guess:,}")
  print(f"library draws       : {drawn:,}")
  if drawn:
    print(f"overestimate        : {guess / drawn:.1f}x")
  del rt.MODALS[:]
  dlg._generate()
  waited = 0
  while dlg._task is not None and waited < 120000:
    rt._tick(200)
    waited += 200
  rt._tick(300)
  refusals = [text for kind, text in rt.MODALS if kind == "critical"]
  print(f"element layers made : {len(dlg._element_layer_ids)}")
  if refusals:
    print(f"REFUSED             : {refusals[-1]!r}")
  dlg.close()
  return 1 if (refusals or (drawn and guess > 2 * drawn)) else 0


if __name__ == "__main__":
  sys.exit(main())
