"""Which dataset does a run's output say it came from, if you switch mid-run?

CLAIM 3 of the hunt round of 2026-08-25, the second of the two that
decide whether the rest matter, and reported by READING:
`_stamp_working_state` takes `region` from the LAUNCH snapshot while
re-reading `elements` LIVE. A dataset changed while the tiling runs
would therefore file the NEW dataset's hand-picked colours and pinned
bounds under the OLD dataset's source -- and `_apply_element_records`
gates exactly those value-laden records on `here == record["region"]`,
so the gate that exists to stop one dataset's content reaching another
would wave them straight through. Ruling 8's leak arriving through the
record built to prevent inference.

THIS DRIVES IT INSTEAD, and it asks a wider question than the claim,
because reproducing claim 1 turned up a second store of the same fact
going the OTHER way. The landing reads `self.layer_combo.currentLayer()`
LIVE for `region_source` and stamps that onto every output layer as
`weavingspace_region`. So one act writes the dataset's identity twice,
from two different moments, and the two can disagree:

    the group's working state   region from the LAUNCH snapshot
    every output layer          region read LIVE at the landing

WHAT EACH OF THOSE DECIDES, so the harm is not abstract. The layer
stamp is what the chooser LABELS a group with (ruling 1), what
`_bind_group_to_dataset` matches a dataset's groups by (ruling 2), and
what the landing's own `theirs` check reads to refuse writing over a
map made from another dataset (ruling 5 of 2026-08-24). The record's
`region` is what `_apply_element_records` compares against before
letting pins and hand-picked colours through (ruling 8). Getting
either wrong is a wrong answer to a question somebody built a guard
for.

THE FIXTURE MAKES A LEAK VISIBLE AS CONTENT. B carries a column of the
SAME NAME as A's and DIFFERENT value strings, which is the shape the
GeoPackage boundary test of 2026-08-24 already uses: nothing tells
"same wards, next year" from "unrelated data with a coincident name",
so a value string of B's appearing in a record filed under A is a leak
whatever the intention.

Run it under QGIS's own Python:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \
            | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen
    "$QGIS_PY" -u tools/probes/\
a_dataset_changed_mid_run_files_under_the_wrong_one.py
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))
spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

from qgis.core import (QgsApplication, QgsFeature, QgsGeometry,  # noqa: E402
                       QgsPointXY, QgsProject, QgsVectorLayer)
from weavingspace_qgis.dialog import (WORKING_STATE_PROPERTY,  # noqa: E402
                                      WeavingSpaceDialog)

# B's own vocabulary. Nothing here appears in A, so any one of these
# strings found in a record filed under A is content that crossed.
SECRETS = ["patient_alpha", "patient_beta", "patient_gamma"]


def confidential_layer(origin=(900_000, 0), n=4, cell=1000):
  """A second dataset sharing A's column NAME and no value with it.

  Args:
    origin: (x, y) of the grid's lower-left corner, far from A's so
      the two cannot be confused for one region.
    n: grid side, so the layer holds n*n squares.
    cell: each square's side in map units.

  Returns:
    A memory layer carrying `v1` and a `landcover` column whose values
    are drawn from SECRETS. The shared column NAME is the point: the
    keep-by-name rule of 2026-08-21 makes an element follow it across
    a switch, so this is the ordinary journey rather than a contrived
    one.
  """
  from weavingspace_qgis import compat
  layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "confidential",
                         "memory")
  prov = layer.dataProvider()
  prov.addAttributes([compat.make_field("v1", float),
                      compat.make_field("landcover", str)])
  layer.updateFields()
  feats = []
  for i in range(n):
    for j in range(n):
      f = QgsFeature(layer.fields())
      ox, oy = origin
      ring = [QgsPointXY(ox + i * cell, oy + j * cell),
              QgsPointXY(ox + (i + 1) * cell, oy + j * cell),
              QgsPointXY(ox + (i + 1) * cell, oy + (j + 1) * cell),
              QgsPointXY(ox + i * cell, oy + (j + 1) * cell)]
      f.setGeometry(QgsGeometry.fromPolygonXY([ring]))
      f["v1"] = float(i)
      f["landcover"] = SECRETS[(i + j) % len(SECRETS)]
      feats.append(f)
  prov.addFeatures(feats)
  layer.updateExtents()
  return layer


def group_named(name):
  """The layer-tree group carrying this name, or None.

  Args:
    name: the group's name as the dialog recorded it.

  Returns:
    The QgsLayerTreeGroup, or None.
  """
  root = QgsProject.instance().layerTreeRoot()
  return next((g for g in root.findGroups() if g.name() == name), None)


def stamps_of(group):
  """Every distinct `weavingspace_region` the group's layers carry.

  Args:
    group: a QgsLayerTreeGroup, or None.

  Returns:
    A set of source strings. This is the stamp ruling 5's refusal
    reads, ruling 2's binding matches on, and ruling 1's chooser
    labels a group by -- so it is asked of the LAYERS rather than of
    the dialog, which is the thing under suspicion.
  """
  if group is None:
    return set()
  out = set()
  for child in group.children():
    layer = getattr(child, "layer", lambda: None)()
    if layer is not None:
      mark = layer.customProperty("weavingspace_region")
      if mark:
        out.add(mark)
  return out


def main():
  """Switch the dataset mid-run and read both stores of its identity.

  Returns:
    0 when the two stores agree and no value of B's is filed under A,
    1 when they disagree or content crossed. The exit code gates a fix.
  """
  app = QgsApplication([], False)
  app.initQgis()
  project = QgsProject.instance()
  project.clear()
  rt._no_modal_dialogs()

  A = rt.make_region_layer(n=4, cell=1000)
  A.setName("Aotearoa")
  B = confidential_layer()
  B.setName("Confidential")
  project.addMapLayer(A)
  project.addMapLayer(B)
  a_source, b_source = A.source(), B.source()

  dlg = WeavingSpaceDialog(iface=rt._Iface())
  dlg.live_check.setChecked(False)

  # ---- B FIRST, so it has hand-picked colours of its own to leak.
  dlg.layer_combo.setLayer(B)
  rt._tick(500)
  tid = next(iter(sorted(dlg._element_layer_ids)), None) or "a"
  assignments = dlg._assignments()
  tid = assignments[0]["id"] if assignments else "a"
  dlg._category_colours.setdefault(tid, {})["landcover"] = {
    SECRETS[0]: "#010203"}
  print(f"B's picks staged     {tid!r} landcover -> {SECRETS[0]}")

  # ---- A's OWN MAP, made while A is chosen, as any demo would.
  dlg.layer_combo.setLayer(A)
  rt._tick(900)
  dlg.spacing_spin.setValue(520)
  rt._generate_and_wait(dlg)
  rt._tick(400)
  a_group = dlg._group_name
  print(f"A's group            {a_group!r}")
  print(f"its stamps           {stamps_of(group_named(a_group)) == {a_source}}"
        f" (all say A)")

  # ---- THE RUN THAT IS LAUNCHED ON A AND LANDS WHILE B IS CHOSEN.
  dlg.spacing_spin.setValue(430)
  dlg._generate()
  if dlg._task is None:
    print("PREMISE FAILED: no task in flight, so nothing below means "
          "anything.")
    return 1
  print("a run is in flight   True (launched against A)")
  dlg.layer_combo.setLayer(B)          # an ordinary act, mid-run
  rt._tick(300)
  now = dlg.layer_combo.currentLayer()
  print(f"chooser now on       "
        f"{now.name() if now is not None else None!r}")
  if now is None or now.id() != B.id():
    print("PREMISE FAILED: the mid-run switch did not take, so the "
          "two moments never differed.")
    return 1

  rt._settle(dlg)
  rt._tick(600)

  landed = dlg._group_name
  node = group_named(landed)
  marks = stamps_of(node)
  raw = node.customProperty(WORKING_STATE_PROPERTY) if node else None
  record = json.loads(raw) if raw else {}
  recorded = record.get("region")

  print(f"\nthe run landed in    {landed!r}")
  print(f"layers stamped       "
        f"{'A' if marks == {a_source} else 'B' if marks == {b_source} else marks}")
  print(f"record says region   "
        f"{'A' if recorded == a_source else 'B' if recorded == b_source else recorded!r}")

  # DOES ANY OF B'S VOCABULARY SIT IN A RECORD FILED UNDER A? Asked of
  # the serialized record's own bytes, which is the same question the
  # GeoPackage boundary test asks of a file: whatever the intention,
  # a value string that crossed is a value string that crossed.
  crossed = sorted(s for s in SECRETS if raw and s in raw)
  print(f"B's values in the record  {crossed or 'none'}")

  faults = []
  if marks and recorded and marks != {recorded}:
    faults.append(
      f"the two stores of one fact disagree: the layers say "
      f"{'B' if marks == {b_source} else marks}, the record says "
      f"{'A' if recorded == a_source else recorded!r}")
  if crossed and recorded == a_source:
    faults.append(
      f"B's own value strings {crossed} are filed under A's source, "
      f"which is what `_apply_element_records` reads before letting "
      f"pins and hand-picked colours onto A's map and A's GeoPackage")
  if marks == {b_source}:
    faults.append(
      "A's tiles are stamped as B's, so the chooser labels A's map "
      "with B's name, the binding hands it to B, and ruling 5's "
      "refusal would let a B run write straight over it")

  # ---- AND THE CONSEQUENCE, DRIVEN RATHER THAN REASONED. A site
  # named by reading is a hypothesis, and so is a harm named by
  # reading: if A's tiles now answer to B, then choosing B and
  # pressing Generate should replace them. That is the map a user
  # loses, and it costs one more run to know rather than argue.
  a_tiles = {child.layer().id() for child in (node.children() if node else [])
             if getattr(child, "layer", lambda: None)() is not None}
  # THE SWITCH HAS TO BE A REAL ONE. The mid-run act above already
  # left the chooser on B, so asking for B again emits nothing, no
  # binding runs, and the leg would measure a journey nobody took --
  # the probe-that-cannot-reach-its-case shape this project has paid
  # for four times. Going by way of A makes the second choice move.
  dlg.layer_combo.setLayer(A)
  rt._tick(900)
  dlg.layer_combo.setLayer(B)
  rt._tick(900)
  print(f"\nchoosing B lands on  {dlg._group_name!r} "
        f"(A's tiles live in {landed!r})")
  print(f"the chooser reads    {dlg.group_combo.currentText()!r}")
  dlg.spacing_spin.setValue(610)
  rt._generate_and_wait(dlg)
  rt._tick(500)
  survived = {lid for lid in a_tiles if project.mapLayer(lid) is not None}
  print(f"A's tiles after B ran  {len(survived)} of {len(a_tiles)} survive")
  if a_tiles and len(survived) < len(a_tiles):
    faults.append(
      f"a run on B destroyed {len(a_tiles) - len(survived)} of "
      f"{len(a_tiles)} layers of tiles drawn from A -- the map a user "
      f"loses, and the harm ruling 5's refusal exists to prevent")

  if faults:
    print("\nCONFIRMED:")
    for fault in faults:
      print(f"  - {fault}")
    return 1
  print("\nNOT REPRODUCED: both stores name the same dataset and no "
        "value of B's was filed under A.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
