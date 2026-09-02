"""Does a Save AS name tables for the map being saved, or the last drawn?

`_save_the_map` seeds its table names from `_element_tables`, which a
LANDING fills and nothing clears, and then asks the layer's own source
for every element -- but only where that layer reads from THE FILE
BEING SAVED TO. A Save AS reads a different file, so the witness is
answered None by construction (its own docstring says so), and the
stale record decides alone.

  CONTROL  nothing drawn first, so the record is empty and the names
           are composed from the map being saved.
  TREATED  a map drawn first, with a DIFFERENT variable on the same
           element, so the record has an answer for an element it has
           never seen.

The oracle is the file contradicting itself: its own record says which
variable each element was saved with, so a table named for another one
is a file that disagrees with its own description. Read through OGR.
"""
import sys
import probe_kit
sys.path.insert(0, probe_kit._repo_root())
from probe_kit import start  # noqa: E402


def element_tables(path):
  """The element tables a file holds, twins aside.

  Args:
    path: the GeoPackage to read.

  Returns:
    A sorted list of names, read through OGR and released at once --
    an instrument that holds the file open changes what the next
    reading sees.
  """
  from osgeo import ogr
  src = ogr.Open(path)
  if src is None:
    return []
  names = sorted(src.GetLayerByIndex(i).GetName()
                 for i in range(src.GetLayerCount()))
  src = None
  return [n for n in names
          if n.startswith("tiles_") and not n.endswith("_no_data")]


def arm(probe, name, draw_first):
  """Send a map, open it, save it elsewhere, and read both stores.

  Args:
    probe: the harness, whose project each arm clears first.
    name: names the arm and its own three files.
    draw_first: True to draw a map of my own -- with a DIFFERENT
      variable on the same element -- before opening theirs, which is
      what fills the record with an answer for an element it has
      never seen.

  Returns:
    The tables in the copy whose names disagree with the copy's own
    record, which is the file contradicting its own description.
  """
  from weavingspace_qgis import bridge
  s = probe.suite
  probe.clear()
  # ---- SOMEBODY ELSE'S MAP, saved with landcover on row 1.
  sender, _layer, _tid = probe.dialog()
  sent = probe.path(f"{name}-sent.gpkg")
  try:
    probe.generate(sender, spacing=700.0)
    assert probe.save(sender, sent), "PREMISE: the sender's save failed"
    print(f"  {name}: sent holds {element_tables(sent)}")
  finally:
    sender.close()
  probe.clear()

  # ---- MY SESSION.
  mine, layer, _tid2 = probe.dialog()
  out = probe.path(f"{name}-copy.gpkg")
  try:
    if draw_first:
      # A MAP OF MY OWN, with a DIFFERENT variable on the same row, so
      # the record answers differently from the file being saved.
      mine.table.cellWidget(1, 1).setCurrentText("v2")
      mine._update_dynamic_columns()
      s._tick(150)
      probe.generate(mine, spacing=900.0)
      drawn = probe.path(f"{name}-mine.gpkg")
      assert probe.save(mine, drawn), "PREMISE: my own save failed"
      assert mine._element_tables, "PREMISE: the record stayed empty"
      print(f"    drew first, record={sorted(mine._element_tables.items())}")
    mine.resume_widget.setFilePath(sent)
    mine.load_button.click()
    s._tick(700)
    assert mine._element_layer_ids, "PREMISE: the Load opened no map"
    # ---- AND SAVE IT SOMEWHERE ELSE.
    assert probe.save(mine, out), "the Save As was refused"
    record = bridge.read_working_state(out) or {}
    says = {str(e.get("id")): e.get("var")
            for e in (record.get("elements") or []) if isinstance(e, dict)}
    tables = element_tables(out)
    wrong = [t for t in tables
             if t.split("tiles_", 1)[1].split("_", 1)[0] in says
             and t != bridge.element_table_name(
               t.split("tiles_", 1)[1].split("_", 1)[0],
               says[t.split("tiles_", 1)[1].split("_", 1)[0]])]
    print(f"    the copy holds {tables}")
    print(f"    its record says {says}")
    print(f"    tables disagreeing with the record: {wrong}")
    return wrong
  finally:
    mine.close()


probe = start()
print("WHAT A SAVE AS CALLS THE TABLES")
control = arm(probe, "control", draw_first=False)
treated = arm(probe, "treated", draw_first=True)
print()
print(f"  control disagreements : {control}   (must be none)")
print(f"  treated disagreements : {treated}")
print("BOTH ARMS REPORTED, teardown complete.")
