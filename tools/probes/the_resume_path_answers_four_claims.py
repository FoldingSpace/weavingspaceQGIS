"""Four claims about resuming a saved map, driven rather than read.

Claims 4, 7, 9 and 10 of the hunt round of 2026-08-25, all against
`_resume_from_gpkg` and all reported by READING. They are judged
together because they share a fixture and because three of them are
cheap once the fourth is staged.

**EMBEDDING DEFEATS THE GATE IT NEEDS** (found independently by TWO
hunts, which is the strongest signal this method produces).
`_apply_element_records` lets pins and hand-picked colours through
only when `here == record["region"]`, and the embedded recovery loads
the region as `<file>|layername=weavingspace_region` -- a string that
can never equal the source recorded when the map was made. So the one
journey embedding exists for would be the one journey that drops the
work. Ruling 8's gate doing precisely its job on precisely the wrong
case.

**RESUMING ONE FILE TWICE MAKES TWO GROUPS.** Nothing asks whether
this file is already open, and the group is made unconditionally from
the first free name. Two groups over one set of tables is the double
map that adoption exists to prevent, arriving through a new door.

**THE COUNT IN THE MESSAGE INCLUDES THE PAIRED LAYERS.** Everything
matching `tiles_` is loaded and counted, and a paired no-data layer's
table is `<table>_no_data`, so a four-element design can announce
eight element layers.

**THE CHOOSER MOVES OUTSIDE THE GUARD.** `_recover_the_source` selects
a region layer BEFORE `_selecting_a_group` is set, where its twin
`_on_group_chosen` sets the flag first. A resume could therefore be
read as a change of dataset, which clears the output path, arms a
fresh group and can put the design-floor question on screen -- in the
middle of opening a file.

WHAT IS ASKED OF EACH, and none of it is asked of the dialog's own
records where a layer or a file can be read instead: the map's own
renderers for the colours, the layer tree for the groups, the message
bar for what the user was told, and the modal recorder for what they
were asked.

Run it under QGIS's own Python:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \
            | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen
    "$QGIS_PY" -u tools/probes/the_resume_path_answers_four_claims.py
"""
import importlib.util
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))
spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

from qgis.core import QgsApplication, QgsProject  # noqa: E402
from weavingspace_qgis import bridge  # noqa: E402
from weavingspace_qgis.dialog import WeavingSpaceDialog  # noqa: E402

PICKED = "#0a0b0c"


def main():
  """Stage one embedded saved map and put all four questions to it.

  Returns:
    0 when every claim is refuted, 1 when any is confirmed. Each is
    reported separately, because "some of this is wrong" is not a work
    list.
  """
  app = QgsApplication([], False)
  app.initQgis()
  project = QgsProject.instance()
  project.clear()
  rt._no_modal_dialogs()
  folder = tempfile.mkdtemp(prefix="weavingspace_resume_probe_")
  region_path = os.path.join(folder, "region.gpkg")
  map_path = os.path.join(folder, "map.gpkg")
  confirmed = []

  try:
    # A FILE-BACKED REGION, because a memory layer's source() encodes
    # its fields and would make by-reference recovery answer for a
    # reason that has nothing to do with the rule under test.
    memory = rt.make_region_layer(n=4, cell=1000)
    # ONE MISSING VALUE, so the map really carries a paired no-data
    # layer. Without it the count claim cannot be asked at all: this
    # project measured fifteen configurations on clean data and not
    # one produced a twin, so the twin has to be staged rather than
    # hoped for.
    memory.startEditing()
    first = next(memory.getFeatures())
    memory.changeAttributeValue(
      first.id(), memory.fields().indexOf("v1"), None)
    memory.commitChanges()
    region = bridge.write_gpkg_layer(
      bridge.gdf_to_layer(
        bridge.layer_to_gdf(memory, ["v1", "v2", "landcover"]), "region"),
      region_path, "region", first=True)
    assert region is not None and region.isValid(), "no region on disk"
    project.addMapLayer(region)

    dlg = WeavingSpaceDialog(iface=rt._Iface())
    dlg.live_check.setChecked(False)
    dlg.layer_combo.setLayer(region)
    rt._tick(500)
    assignments = dlg._assignments()
    tid = assignments[0]["id"]
    pinned_tid = assignments[1]["id"] if len(assignments) > 1 else tid
    # A HAND-PICKED COLOUR AND A PIN: the two records the gate under
    # test is there to stop crossing datasets, and the two a user
    # would be furious to lose on the one journey embedding is for.
    #
    # ON DIFFERENT ELEMENTS, DELIBERATELY. A pin names a class
    # BOUNDARY, which a categorical row does not have -- so pinning
    # the element carrying `landcover` staged a record the plugin
    # would never keep, and its absence afterwards proved nothing
    # whatever. Measured 2026-08-26, and it is the fixture-that-cannot-
    # exhibit-its-case trap wearing a colour scheme.
    dlg.table.cellWidget(0, 1).setCurrentText("landcover")
    dlg.table.cellWidget(1, 1).setCurrentText("v1")
    rt._tick(400)
    dlg._category_colours.setdefault(tid, {})["landcover"] = {
      "forest": PICKED}
    # `low` IS the pin: `_pins_in_force` reads whether it is not None,
    # and there is no separate flag key. An earlier draft staged
    # `low_pinned: True` beside it, which the plugin correctly dropped
    # -- and its absence afterwards read exactly like a lost record.
    dlg._pinned_bounds.setdefault(pinned_tid, {})["v1"] = {"low": 1.5}
    box = getattr(dlg, "opt_embed_source", None)
    if box is None:
      print("NO EMBED CONTROL: the opt-in this probe is about does "
            "not exist, so nothing below would mean anything.")
      return 1
    box.setChecked(True)
    dlg.gpkg_widget.setFilePath(map_path)
    dlg.spacing_spin.setValue(540)
    rt._generate_and_wait(dlg)
    rt._tick(500)
    elements = len(dlg._element_layer_ids)
    print(f"elements in the map  {elements}")
    stored = bridge.read_working_state(map_path)
    print(f"source embedded      {bool((stored or {}).get('region_embedded'))}")
    if not (stored or {}).get("region_embedded"):
      print("THE OPT-IN DID NOT TAKE: nothing below would mean "
            "anything.")
      return 1
    dlg.close()

    # THE FILE ARRIVES WITHOUT ITS PROJECT AND WITHOUT ITS SOURCE,
    # which is the whole point of embedding. The region file is
    # removed rather than merely deselected, so by-reference recovery
    # cannot answer and the embedded copy is the only route left.
    project.clear()
    os.remove(region_path)
    rt._tick(200)

    dlg = WeavingSpaceDialog(iface=rt._Iface())
    dlg.live_check.setChecked(False)
    rt._tick(300)
    del rt.MODALS[:]
    del rt.BAR_MESSAGES[:]
    opened = dlg._resume_from_gpkg(map_path)
    rt._tick(600)
    said = " ".join(text for _kind, text in rt.BAR_MESSAGES)
    print(f"\nresumed              {opened}")
    print(f"said                 {said!r}")
    print(f"asked                {[t for _k, t in rt.MODALS]}")
    if not opened:
      print("THE RESUME REFUSED, so nothing below can be asked.")
      return 1

    # ---- CLAIM: embedding defeats the gate it needs
    picks = dlg._category_colours.get(tid, {}).get("landcover") or {}
    pins = dlg._pinned_bounds.get(pinned_tid, {}).get("v1") or {}
    here = dlg.layer_combo.currentLayer()
    here_source = here.source() if here is not None else None
    print(f"the region came back {here.name() if here else None!r}")
    print(f"  as                 {here_source!r}")
    print(f"  recorded as        {(stored or {}).get('region')!r}")
    print(f"  the gate sees them {'the same' if here_source == (stored or {}).get('region') else 'DIFFERENT'}")
    print(f"hand-picked colours  {picks or 'none'}")
    print(f"pinned bounds        {pins or 'none'}")
    if picks.get("forest") != PICKED or not pins:
      confirmed.append(
        "EMBEDDING DEFEATS ITS OWN PURPOSE: the source came back from "
        "inside the file, so `here` reads "
        "'<file>|layername=weavingspace_region' and can never equal "
        "the recorded source -- the gate dropped the hand-picked "
        "colours and the pins on the one journey embedding exists for")

    # ---- CLAIM: the chooser moves outside the guard
    if dlg.gpkg_widget.filePath() != map_path:
      confirmed.append(
        f"THE OUTPUT PATH DID NOT SURVIVE THE RESUME: the box reads "
        f"{dlg.gpkg_widget.filePath()!r}")
    if rt.MODALS:
      confirmed.append(
        f"A RESUME PUT A QUESTION ON SCREEN: {[t for _k, t in rt.MODALS]}")
    if "cleared" in said.lower():
      confirmed.append(
        f"A RESUME TOLD THE USER SOMETHING WAS CLEARED: {said!r}")

    # ---- CLAIM: the count includes the paired layers
    root = project.layerTreeRoot()
    ours = [g for g in root.findGroups()
            if any(getattr(c, "layer", lambda: None)() is not None
                   and c.layer().customProperty("weavingspace_output")
                   for c in g.children())]
    in_group = len(ours[0].children()) if ours else 0
    paired = sum(
      1 for c in (ours[0].children() if ours else [])
      if getattr(c, "layer", lambda: None)() is not None
      and c.layer().customProperty("weavingspace_no_data"))
    claimed = "".join(ch for ch in said.split("element layers")[0]
                      if ch.isdigit())
    print(f"layers in the group  {in_group} ({paired} of them paired)")
    print(f"the message claims   {claimed!r} element layers")
    if claimed and paired and int(claimed) != in_group - paired:
      confirmed.append(
        f"THE RESUME MESSAGE OVERSTATES WHAT CAME BACK: it says "
        f"{claimed} element layers where {in_group - paired} elements "
        f"came back and {paired} of the layers are their paired "
        f"no-data twins")

    # ---- CLAIM: resuming one file twice makes two groups
    before = len(root.findGroups())
    del rt.BAR_MESSAGES[:]
    again = dlg._resume_from_gpkg(map_path)
    rt._tick(600)
    after = len(root.findGroups())
    print(f"\ngroups before/after  {before} -> {after} (resumed again: "
          f"{again})")
    if after > before:
      confirmed.append(
        f"RESUMING ONE FILE TWICE MADE {after - before} MORE GROUP(S) "
        f"over the same tables: two maps of one file, and the next "
        f"Generate writes into the file both of them draw from")

    dlg.close()
  finally:
    project.clear()
    shutil.rmtree(folder, ignore_errors=True)

  if confirmed:
    print("\nCONFIRMED:")
    for one in confirmed:
      print(f"  - {one}")
    return 1
  print("\nNOT REPRODUCED: all four claims came back clean.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
