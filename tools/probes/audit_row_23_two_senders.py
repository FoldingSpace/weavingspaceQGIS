"""Does ledger row 23 still reproduce, and where exactly does it bite?

THE CLAIM. Open two maps sent by two people, go back to the first
through the group chooser, and it is re-tiled from the SECOND sender's
data; the next Save writes it over the first sender's file. And the
resume stamps the group with the sender's own unreachable path rather
than the source recovery actually landed on.

WHAT THIS PROBE IS AND IS NOT. It drives the shortest journey that
would exhibit the fault and prints what it finds; it decides nothing.
Where a reading comes back clean the row needs re-reading rather than
re-fixing, and where it cannot reach its case it says so, because a
probe that cannot reach its case reports good news.

THE TWO DATASETS CANNOT BE CONFUSED. `make_region_layer` takes an
`origin` for exactly this purpose, and the second is put half a
million map units away -- so the question "which sender's data was
this map tiled from" is answered by where the tiles ARE, not by an
attribute either dataset might share.

THE SENDERS EMBED THEIR SOURCE, which is the case the claim is about:
a recipient cannot reach the path a sender's file records, so the
resume recovers the data from the copy in the file and the two facts
-- what the record says and what recovery landed on -- come apart.
That coming-apart is the second half of the claim and is measured
here separately from the first, because they could perfectly well
have different answers.
"""

import os
import sys

sys.path.insert(0, os.environ.get("WS_REPO", os.getcwd()))

from tools.probe_kit import start                      # noqa: E402

A_ORIGIN = (0, 0)
B_ORIGIN = (500000, 500000)


def centre_of_the_tiles(probe, dlg):
  """Where on the ground this map's tiles actually are.

  Args:
    probe: the running `Probe`.
    dlg: the dialog whose output layers to measure.

  Returns:
    An (x, y) pair from the combined extent of every element layer,
    or None where nothing is drawn. It is the discriminator this
    probe rests on: the two senders' regions are half a million units
    apart, so the centre says whose data a map was tiled from without
    reading a single attribute.
  """
  boxes = []
  for layer_id in dlg._element_layer_ids.values():
    layer = probe.project.mapLayer(layer_id or "")
    if layer is not None:
      boxes.append(layer.extent())
  if not boxes:
    return None
  whole = boxes[0]
  for box in boxes[1:]:
    whole.combineExtentWith(box)
  return (round(whole.center().x()), round(whole.center().y()))


def whose(point):
  """Which sender's ground a point sits on.

  Args:
    point: an (x, y) pair, or None.

  Returns:
    "A", "B", or a description of why neither -- so a reading that
    lands somewhere unexpected is reported as unexpected rather than
    quietly attributed to one of them.
  """
  if point is None:
    return "nothing drawn"
  x, y = point
  if abs(x - A_ORIGIN[0]) < 100000 and abs(y - A_ORIGIN[1]) < 100000:
    return "A"
  if abs(x - B_ORIGIN[0]) < 100000 and abs(y - B_ORIGIN[1]) < 100000:
    return "B"
  return f"neither, at {point}"


def send(probe, path, origin, field):
  """One sender: draw a map from their own data and save it with the
  source included.

  Args:
    probe: the running `Probe`.
    path: the GeoPackage this sender writes.
    origin: where their region sits, which is what tells the two
      senders' data apart.
    field: the column they symbolise.

  Returns:
    None. Leaves the project EMPTY, so the next sender -- and the
    recipient after them -- meets a project holding nobody else's
    layers, which is what a person opening a file they were sent
    really has.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = probe.suite.make_region_layer(origin=origin)
  layer.setName(f"region at {origin}")
  probe.project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=probe.suite._Iface())
  try:
    dlg.live_check.setChecked(False)
    dlg.layer_combo.setLayer(layer)
    probe.suite._tick(300)
    dlg.table.cellWidget(1, 1).setCurrentText(field)
    dlg._update_dynamic_columns()
    probe.suite._tick(200)
    dlg.opt_embed_source.setChecked(True)
    probe.generate(dlg, spacing=700.0)
    assert probe.save(dlg, path), f"PREMISE: the sender's save to {path} failed"
    print(f"  sender at {origin} wrote {probe.tables(path)}")
  finally:
    dlg.close()
  probe.clear()


def load(probe, dlg, path):
  """Open a sent file the way a recipient does.

  Args:
    probe: the running `Probe`.
    dlg: the recipient's dialog.
    path: the file to open.

  Returns:
    None. Raises where nothing came back, since everything after this
    is about a map that has to exist.
  """
  dlg.resume_widget.setFilePath(path)
  dlg._load_pressed()
  probe.suite._settle(dlg, seconds=60)
  probe.suite._tick(400)
  assert dlg._element_layer_ids, \
    f"PREMISE: opening {os.path.basename(path)} brought back no map"


def record_of(probe, name):
  """The working state stamped on a group, read from the layer tree.

  Args:
    probe: the running `Probe`.
    name: the group's name.

  Returns:
    The decoded record, or {} where there is none. Read through the
    node's custom property rather than through the dialog, because
    the claim is about what was STAMPED, and asking the dialog would
    ask the thing under test.
  """
  import json
  from weavingspace_qgis.dialog import WORKING_STATE_PROPERTY
  node = next((g for g in probe.project.layerTreeRoot().findGroups()
               if g.name() == name), None)
  if node is None:
    return {}
  raw = node.customProperty(WORKING_STATE_PROPERTY) or ""
  try:
    return json.loads(raw) if raw else {}
  except ValueError:
    return {}


def main():
  """Drive two senders, two files, and the return to the first.

  Returns:
    None; it prints, and the verdict is the line beginning OPEN,
    CLOSED or INCONCLUSIVE. It decides nothing: a clean reading is a
    reason to look rather than a reason to delete a ledger row.

  THE CHOOSER IS MATCHED WITH THE SUITE'S OWN HELPER and never with
  `in`. Both senders' embedded regions come back under one name, so
  both groups are named for it and the second carries a counter --
  which makes the first group's name a PREFIX of the second's. A
  substring match selected the wrong row on this probe's first run,
  and it then measured the second group generating from the second
  dataset, which is correct behaviour, and reported it as the defect.
  """
  probe = start()
  a_path, b_path = probe.path("from_alice.gpkg"), probe.path("from_bob.gpkg")
  print("SENDERS")
  send(probe, a_path, A_ORIGIN, "landcover")
  send(probe, b_path, B_ORIGIN, "v1")

  print("\nRECIPIENT")
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  dlg = WeavingSpaceDialog(iface=probe.suite._Iface())
  try:
    dlg.live_check.setChecked(False)
    load(probe, dlg, a_path)
    a_group = dlg._group_name
    a_here = dlg.layer_combo.currentLayer()
    print(f"  opened A: group {a_group!r}, data in force "
          f"{a_here.name() if a_here is not None else None!r}, tiles on "
          f"{whose(centre_of_the_tiles(probe, dlg))}'s ground")
    stamped = record_of(probe, a_group)
    print(f"  A's group records region={stamped.get('region')!r}")
    print(f"  ...and the data recovery landed on "
          f"{a_here.source() if a_here is not None else None!r}")
    if a_here is not None and stamped.get("region"):
      from weavingspace_qgis.dialog import same_source
      agree = same_source(a_here.source(), stamped["region"])
      print(f"  the stamp and what is in force agree: {agree}"
            + ("" if agree else
               "  <-- the second half of the claim: the group is "
               "stamped with a path this machine cannot reach"))

    load(probe, dlg, b_path)
    b_group = dlg._group_name
    b_here = dlg.layer_combo.currentLayer()
    print(f"  opened B: group {b_group!r}, data in force "
          f"{b_here.name() if b_here is not None else None!r}, tiles on "
          f"{whose(centre_of_the_tiles(probe, dlg))}'s ground")
    if a_group == b_group:
      print("  INCONCLUSIVE: both files landed in ONE group, so there "
            "is no returning to the first and nothing below is about "
            "the claim")
      return

    # ---- THE RETURN, through the chooser, which is the claim's door
    #
    # THE LABEL IS MATCHED WITH THE SUITE'S OWN HELPER, NOT WITH `in`.
    # Both senders' embedded regions come back under one name, so both
    # groups are named for it and the second carries a counter -- which
    # makes A's name a PREFIX of B's. A substring test therefore
    # selected B's row and the probe measured B's group generating from
    # B's data, which is correct behaviour, and reported it as the
    # claim. An instrument that cannot reach its case reports good
    # news; this one reported bad news about the wrong thing, which is
    # the same fault facing the other way. Measured 2026-08-29.
    wanted = next((i for i in range(dlg.group_combo.count())
                   if probe.suite._label_names_group(
                     dlg.group_combo.itemText(i), a_group)), -1)
    if wanted < 0:
      print(f"  INCONCLUSIVE: A's group {a_group!r} is not on offer "
            f"among {[dlg.group_combo.itemText(i) for i in range(dlg.group_combo.count())]}")
      return
    dlg.group_combo.setCurrentIndex(wanted)
    dlg.group_combo.activated.emit(wanted)        # what a click sends
    probe.suite._tick(900)
    back = dlg.layer_combo.currentLayer()
    print(f"\n  back on A's group: dialog holds {dlg._group_name!r}, "
          f"data in force {back.name() if back is not None else None!r}")
    if dlg._group_name != a_group:
      # THE PREMISE IS CHECKED RATHER THAN ASSUMED, because the first
      # run of this probe selected the wrong row and every reading
      # below it was about a journey nobody took.
      print(f"  INCONCLUSIVE: the click did not land on A's group "
            f"{a_group!r}, so nothing below is about the return")
      return
    print(f"  the next Save would write to "
          f"{dlg.gpkg_widget.filePath()!r}")
    print(f"  (A's own file is {os.path.basename(a_path)}, B's is "
          f"{os.path.basename(b_path)})")

    # ---- AND WHAT A GENERATE WOULD DRAW, which is the harm itself
    probe.generate(dlg, spacing=700.0)
    ground = whose(centre_of_the_tiles(probe, dlg))
    print(f"  after Generate the tiles sit on {ground}'s ground")
    if ground == "B":
      print("  OPEN: returning to A's map re-tiled it from B's data")
      if dlg.gpkg_widget.filePath() == a_path:
        print("  ...and the next Save writes that over A's own file")
    elif ground == "A":
      print("  CLOSED here: the return re-tiled A's map from A's data")
    else:
      print(f"  INCONCLUSIVE: the tiles landed on {ground}")
  finally:
    dlg.close()


main()
