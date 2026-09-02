"""Does a Save name an opened map's tables, or the last map's?

A hunt reported on 2026-09-02 that a person who draws a map, then
opens a saved one with Load, then presses Save, gets a file whose
element table is NAMED for one variable and HOLDS another -- and the
table the sender wrote is dropped.

WHAT IT TURNS ON. `_element_tables` is written only by a landing and
cleared by nothing, so a session that has drawn any map carries the
names of THAT map. The save takes its names from that record, and the
layer's own source -- which the code beside it calls "the only witness
that has not been through this session" -- is consulted ONLY for
elements the record does not mention. An opened map's elements share
their ids with the drawn one's, so the record answers for all of them
and the witness is never asked.

THIS READS THE FILE DIFFERENTLY FROM THE HUNT, which used stdlib
sqlite3 over `sqlite_master` and `PRAGMA table_info`. Here the tables
and their columns come through OGR, and the second oracle is the
FILE'S OWN RECORD: `bridge.read_working_state` says which variable
each element was saved with, so a table whose name disagrees with the
record is a file that contradicts itself -- which is the harm in the
terms of the ruling it breaks, rather than in the terms of a column.

TWO ARMS, one process, each on its own pair of files, and the control
is the whole of the discrimination:
  CONTROL  open the saved map with NOTHING drawn first, so the record
           is empty and the witness is asked;
  TREATED  draw a map first, which fills the record with the other
           map's names.
"""
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtWidgets import QApplication  # noqa: E402
from osgeo import ogr  # noqa: E402


def tables_and_columns(path):
  """Every element table in the file, with the columns it holds.

  Args:
    path: the GeoPackage to read.

  Returns:
    {table name: [field names]}, through OGR and released at once --
    a different reader from the hunt's sqlite3, so a disagreement
    cannot be one instrument's.
  """
  source = ogr.Open(path)
  if source is None:
    return {}
  found = {}
  for index in range(source.GetLayerCount()):
    layer = source.GetLayerByIndex(index)
    name = layer.GetName()
    if not name.startswith("tiles_"):
      continue
    definition = layer.GetLayerDefn()
    found[name] = [definition.GetFieldDefn(i).GetName()
                   for i in range(definition.GetFieldCount())]
  source = None
  return found


def run_one_arm(probe, name, draw_first):
  """Save a map, open another, save again, and read the file.

  Args:
    probe: the probe kit's handle.
    name: the arm's name, which its two files are named after.
    draw_first: True to draw a map in this session before pressing
      Load, which is what fills `_element_tables`.

  Returns:
    A dict of the file's tables before and after the second save, what
    its own record says each element's variable is, and any table
    whose name disagrees with that record.
  """
  probe.clear()
  from weavingspace_qgis import bridge
  dlg, _layer, _tile_id = probe.dialog()
  dlg.live_check.setChecked(False)
  dlg.show()

  # THE MAP THAT IS SENT, saved and then taken out of the project so
  # the Load door has something to open that this session did not
  # draw.
  probe.generate(dlg, spacing=700.0)
  # A DIFFERENT VARIABLE ON ONE ELEMENT, because the name follows the
  # variable an element displays -- so two maps whose elements carry
  # different columns are what makes a wrong name visible at all.
  sent = probe.path(f"{name}-sent.gpkg")
  assert probe.save(dlg, sent), f"PREMISE: {name}'s map was never sent"
  before = tables_and_columns(sent)
  assert before, "PREMISE: the sent file holds no element tables"

  from qgis.core import QgsProject
  for layer_id in list(dlg._element_layer_ids.values()):
    QgsProject.instance().removeMapLayer(layer_id)
  for _ in range(20):
    QApplication.processEvents()

  # THE PLUGIN IS REOPENED BETWEEN THE TWO MAPS, which is what makes
  # the arms differ at all. `_element_tables` is filled by any landing
  # and cleared by nothing, so a probe that draws the sent map and
  # then presses Load in the SAME window has the record filled by its
  # own fixture -- my first run asserted its way out of exactly that,
  # which is what a premise is for.
  dlg.close()
  for _ in range(20):
    QApplication.processEvents()
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  dlg = WeavingSpaceDialog(iface=probe.suite._Iface())
  dlg.live_check.setChecked(False)
  dlg.show()
  for _ in range(40):
    QApplication.processEvents()

  if draw_first:
    # A MAP DRAWN IN THIS SESSION, which is what fills the record the
    # save reads its names from. The variables differ from the sent
    # map's, or the two would agree by accident.
    dlg.n_spin.setValue(4)
    for _ in range(10):
      QApplication.processEvents()
    probe.generate(dlg, spacing=900.0)
    assert getattr(dlg, "_element_tables", None), (
      "PREMISE: drawing a map left the table record empty, so this "
      "arm is the control wearing the treatment's name")
    for layer_id in list(dlg._element_layer_ids.values()):
      QgsProject.instance().removeMapLayer(layer_id)
    for _ in range(20):
      QApplication.processEvents()
  else:
    assert not getattr(dlg, "_element_tables", None), (
      "PREMISE: the record is not empty, so the witness would not be "
      "asked and this arm is not a control")

  dlg.resume_widget.setFilePath(sent)
  dlg.load_button.click()
  probe.suite._settle(dlg)
  for _ in range(40):
    QApplication.processEvents()

  probe.save(dlg, sent, overwrite=True)
  for _ in range(40):
    QApplication.processEvents()

  after = tables_and_columns(sent)
  record = bridge.read_working_state(sent) or {}
  # THE RECORD'S OWN KEYS, read from `WORKING_STATE_ELEMENT` rather
  # than guessed: the element is keyed "id" and its column "var". My
  # first run guessed "tid" and this oracle silently answered nothing,
  # which is the dead-axis fault this project counts -- an instrument
  # that cannot speak reads exactly like one with nothing to say.
  says = {entry.get("id"): entry.get("var")
          for entry in (record.get("elements") or [])}
  disagreeing = []
  for table in after:
    for tid, var in says.items():
      if not tid or not var:
        continue
      if table.startswith(f"tiles_{tid}_") and not table.endswith(var):
        disagreeing.append((table, tid, var))
  return {
    "tables before": sorted(before),
    "tables after": sorted(after),
    "the file's record says": says,
    "names disagreeing with the record": disagreeing,
    "tables the second save removed": sorted(set(before) - set(after)),
  }


def main():
  """Drive both arms and say whether the claim reproduces.

  Returns:
    None; everything is printed, and the last line is a sentinel.
  """
  probe = probe_kit.start()

  control = run_one_arm(probe, "control", draw_first=False)
  print("=== CONTROL: nothing drawn before the Load ===")
  for key, value in control.items():
    print(f"    {key}: {value}")

  treated = run_one_arm(probe, "treated", draw_first=True)
  print("=== TREATED: a map drawn first ===")
  for key, value in treated.items():
    print(f"    {key}: {value}")

  print()
  if control["tables the second save removed"]:
    print("INCONCLUSIVE: the control lost tables too, so this is not "
          "about the record at all")
  elif (treated["tables the second save removed"]
        or treated["names disagreeing with the record"]):
    print(f"CLAIM REPRODUCES: the treated arm removed "
          f"{treated['tables the second save removed']} and left "
          f"{len(treated['names disagreeing with the record'])} table "
          f"name(s) contradicting the file's own record, where the "
          f"control did neither")
  else:
    print("THE WITNESS IS ASKED: both arms kept the sent map's tables")
  print("both arms reported; teardown next")


if __name__ == "__main__":
  main()
