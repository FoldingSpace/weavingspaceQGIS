"""Do a resumed map's LAYERS say which dataset they came from?

A hunt reported on 2026-09-02 that opening a self-contained
GeoPackage and then churning the project's polygon layers makes the
dialog let go of the group it just opened, so the next Generate builds
a rival beside it and the next Save writes that rival into the same
tables.

THE MECHANISM IT NAMES IS A ONE-FACT-TWO-STORES SHAPE, which is this
project's commonest. A resume stamps the GROUP's record with the
region the recovery LANDED ON -- deliberately, since a self-contained
file records the SENDER's own path and nothing on the recipient's
machine answers to it. It does not re-stamp the LAYERS, and
`_our_groups` asks the layers. So `theirs` comes back empty, and
`_bind_group_to_dataset` detaches.

TWO QUESTIONS, AND THE SECOND IS THE ONE THAT DECIDES WHOSE DEFECT
THIS IS. The hunt drove the ALREADY-OPEN door, which gained
`_landed_this_session` hours earlier, and read the layer tree and the
file after a Save. This asks instead:

  what do the layers' own `weavingspace_region` stamps say, against
  the source the recovery landed on -- which is the mechanism rather
  than its outcome;
  and does the FRESH door do the same? That branch has set
  `_landed_this_session` since 2026-08-28, so if it detaches too, the
  defect is older than either repair and belongs on the stamp rather
  than on the flag.

BOTH ARMS OPEN A FILE WITH THE SOURCE EMBEDDED, because that is what
makes the recovery land on the copy inside the file rather than on a
layer already in the project -- the state where the record and the
layers can disagree at all.
"""
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtWidgets import QApplication  # noqa: E402


def output_groups(dlg):
  """Every layer-tree group holding one of this plugin's layers.

  Args:
    dlg: the dialog, for the property name its layers carry.

  Returns:
    A list of (group name, how many of our layers it holds). Asked of
    the layer TREE rather than of the dialog's own records, so a
    second group cannot hide behind a chooser that names one.
  """
  from qgis.core import QgsProject
  root = QgsProject.instance().layerTreeRoot()
  found = []
  for node in root.children():
    if not hasattr(node, "children"):
      continue
    ours = 0
    for child in node.children():
      layer = getattr(child, "layer", lambda: None)()
      if layer is not None and layer.customProperty(
          "weavingspace_tile_id"):
        ours += 1
    if ours:
      found.append((node.name(), ours))
  return found


def run_one_arm(probe, name, already_open):
  """Save a self-contained map, open it, and read the stamps.

  Args:
    probe: the probe kit's handle.
    name: the arm's name, which is also its file's name.
    already_open: True to press Load while the map's own layers are
      still in the project; False to clear them first.

  Returns:
    A dict of what the layers' stamps say, what the group's record
    says, whether the binding held the group, and how many output
    groups exist after a Generate.
  """
  probe.clear()
  from qgis.core import QgsProject
  dlg, _layer, _tile_id = probe.dialog()
  dlg.live_check.setChecked(False)
  dlg.show()
  # THE SOURCE GOES IN THE FILE, which is what makes the recovery land
  # on the copy inside it rather than on a layer already open.
  dlg.opt_embed_source.setChecked(True)
  probe.generate(dlg, spacing=700.0)
  path = probe.path(f"{name}.gpkg")
  assert probe.save(dlg, path), f"PREMISE: {name} was never saved"

  # THE SENDER'S OWN LAYER GOES, in BOTH arms, and this is the whole
  # of the fixture. `_recover_the_source` has three routes and the
  # first is a layer already open; with the region layer still in the
  # project it takes that one, the stamps agree with the chooser, and
  # the probe reports health about a journey it never drove. My first
  # run did exactly that. A recipient does not have the sender's
  # layer, which is what the copy inside the file is FOR.
  for found in list(QgsProject.instance().mapLayers().values()):
    if found.customProperty("weavingspace_tile_id"):
      continue
    if found.customProperty("weavingspace_output"):
      continue
    QgsProject.instance().removeMapLayer(found.id())
  for _ in range(20):
    QApplication.processEvents()

  if not already_open:
    for layer_id in list(dlg._element_layer_ids.values()):
      QgsProject.instance().removeMapLayer(layer_id)
    for _ in range(20):
      QApplication.processEvents()

  # THE PLUGIN IS REOPENED, so the flag is not set by the drawing.
  dlg.close()
  for _ in range(20):
    QApplication.processEvents()
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  dlg = WeavingSpaceDialog(iface=probe.suite._Iface())
  dlg.live_check.setChecked(False)
  dlg.show()
  for _ in range(40):
    QApplication.processEvents()

  dlg.resume_widget.setFilePath(path)
  dlg.load_button.click()
  probe.suite._settle(dlg)
  for _ in range(40):
    QApplication.processEvents()

  chosen_now = dlg.layer_combo.currentLayer()
  landed_here = chosen_now.source() if chosen_now is not None else ""
  assert path in str(landed_here), (
    f"PREMISE: the recovery landed on {landed_here!r} rather than on "
    f"the copy inside the file, so the record and the layers cannot "
    f"disagree and this arm measures nothing")

  stamps = []
  for layer_id in dlg._element_layer_ids.values():
    layer = QgsProject.instance().mapLayer(layer_id)
    if layer is not None:
      stamps.append(layer.customProperty("weavingspace_region"))
  chosen = dlg.layer_combo.currentLayer()
  in_force = chosen.source() if chosen is not None else None

  # WHAT THE BINDING ANSWERS, asked of the product rather than
  # recomputed here: it is the method that decides whether the dialog
  # keeps the group it has just opened.
  held_before = dlg._current_group_name() \
      if hasattr(dlg, "_current_group_name") else None
  bound = dlg._bind_group_to_dataset()
  for _ in range(20):
    QApplication.processEvents()

  # AND THE HARM: a Generate after the binding has let go builds a
  # rival group beside the map that was opened.
  dlg._generate()
  probe.suite._settle(dlg)
  groups = output_groups(dlg)

  return {
    "layers say": sorted({str(s) for s in stamps}),
    "recovery landed on / chooser holds": in_force,
    "stamps match the region in force": bool(
      stamps and in_force and all(s == in_force for s in stamps)),
    "binding held the group": bound,
    "group before the binding": held_before,
    "output groups after a Generate": groups,
  }


def main():
  """Drive both doors and say whether the stamps agree.

  Returns:
    None; everything is printed, and the last line is a sentinel.
  """
  probe = probe_kit.start()

  for name, already in (("fresh", False), ("already", True)):
    where = "already-open" if already else "fresh"
    print(f"=== {where.upper()} DOOR, a self-contained file ===")
    found = run_one_arm(probe, name, already)
    for key, value in found.items():
      print(f"    {key}: {value}")
    if len(found["output groups after a Generate"]) > 1:
      print(f"    -> A RIVAL GROUP: {len(found['output groups after a Generate'])} "
            f"groups hold this plugin's layers, so the opened map is "
            f"no longer the one a Save will write")
    else:
      print("    -> one group: the opened map is still the one in hand")
  print("both doors reported; teardown next")


if __name__ == "__main__":
  main()
