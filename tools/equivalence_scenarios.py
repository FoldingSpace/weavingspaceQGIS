#!/usr/bin/env python3
"""Drive one scenario and report everything a test could see.

    <qgis python> tools/equivalence_scenarios.py <tree> <scenario> \\
        <watched file> <watched line>

Run by tools/prove_equivalent.py, once against a clean checkout and
once against a mutated copy. It prints a marker followed by JSON
holding two things: the SNAPSHOT, and whether the watched line
actually ran.

The snapshot is deliberately WIDE rather than aimed at any particular
mutation. Aiming it would repeat the error the whole campaign exists
to avoid -- looking only where you already expect to find something.
The cost of that was measured: a mutant here looked equivalent under a
narrow comparison and was not, because what it moved was every
element's remembered single colour, which sits in the run signature,
so a column added in QGIS would have discarded the user's own styling.
Nothing about that was in the dimension being watched at the time.

It reads the dialog's own state and the widgets' own accessors, and
never stands in for the code under study: a probe that replaces the
function it measures measures the probe, which cost this project two
false diagnoses in one day.

It also counts WORK, not only outcome -- unit rebuilds and preview
refreshes -- because a duplicate rebuild leaves identical state, so an
end-state comparison cannot see the very thing several guards in this
dialog claim to prevent. Those counters are installed on the CLASS
before any dialog exists: a signal connection holds the original bound
method, so wrapping an instance attribute would count direct calls and
silently miss every signal-driven one.

Adding a scenario: write a function taking the loaded run_tests
module, drive the dialog the way a user would, and return
``snapshot(dlg)``. Register it in SCENARIOS. A scenario earns its keep
by REACHING lines other scenarios do not -- the watched-line guard in
prove_equivalent will tell you when it does not.
"""
import json
import os
import sys


def snapshot(dlg):
  """Everything observable about a dialog, as JSON-able data.

  Args:
    dlg: the dialog to read.

  Returns:
    A dict whose keys are stable, so two runs compare key by key, and
    whose values are strings and numbers, so the comparison cannot
    turn on object identity -- which differs between processes for
    reasons having nothing to do with any mutation.
  """
  out = {}
  out["assignments"] = [
    {k: str(v) for k, v in sorted(a.items())} for a in dlg._assignments()]
  out["category_colours"] = json.loads(json.dumps(
    dlg._category_colours, default=str, sort_keys=True))
  out["ramp_ranges"] = json.loads(json.dumps(
    getattr(dlg, "_ramp_ranges", {}), default=str, sort_keys=True))
  out["preview_colours"] = json.loads(json.dumps(
    dlg._table_id_colours(), default=str, sort_keys=True))
  out["note"] = dlg.live_note.text()
  out["rows"] = dlg.table.rowCount()
  out["columns"] = dlg.table.columnCount()
  out["hidden_columns"] = [c for c in range(dlg.table.columnCount())
                           if dlg.table.isColumnHidden(c)]

  cells = []
  for row in range(dlg.table.rowCount()):
    entry = {}
    item = dlg.table.item(row, 0)
    entry["id"] = item.text() if item is not None else None
    for col in range(1, dlg.table.columnCount()):
      widget = dlg.table.cellWidget(row, col)
      if widget is None:
        entry[f"c{col}"] = None
        continue
      bits = [type(widget).__name__]
      if hasattr(widget, "currentText"):
        bits.append(widget.currentText())
      if hasattr(widget, "count"):
        bits.append("items=" + "|".join(
          widget.itemText(i) for i in range(widget.count())))
      if hasattr(widget, "isChecked"):
        bits.append(f"checked={widget.isChecked()}")
      if hasattr(widget, "value"):
        bits.append(f"value={widget.value()}")
      bits.append(f"enabled={widget.isEnabled()}")
      entry[f"c{col}"] = " ".join(str(b) for b in bits)
    cells.append(entry)
  out["cells"] = cells

  for name in ("n_combo", "kind_combo", "family_combo", "spacing_spin",
               "shells_spin", "live_check", "opt_over_under",
               "opt_grid_rows", "opt_grid_cols"):
    widget = getattr(dlg, name, None)
    if widget is None:
      continue
    if hasattr(widget, "currentText"):
      out[name] = widget.currentText()
    elif hasattr(widget, "isChecked"):
      out[name] = widget.isChecked()
    elif hasattr(widget, "text"):
      out[name] = widget.text()
    else:
      out[name] = widget.value()
    out[name + "_enabled"] = widget.isEnabled()
  out["unit_elements"] = (len(dlg._unit.tiles) if dlg._unit is not None
                          else None)
  return out


def scenario_a_working_session(rt):
  """The broad one: most of what somebody does in a sitting.

  Deliberately wide, because a scenario's value is the lines it
  reaches and one good session serves many mutants where a bespoke
  scenario serves one. It picks a layer, changes the element count and
  the kind, chooses families that drive different option rows, sets a
  variable and a style, and lets each change settle.

  Returns:
    The snapshot after everything has settled.
  """
  from qgis.core import QgsProject
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = rt.make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  rt._tick(400)

  dlg.n_combo.setCurrentText("4")
  rt._tick(200)
  dlg.kind_combo.setCurrentText("tiling")
  rt._tick(200)
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  rt._tick(300)
  dlg.spacing_spin.setValue(500)
  rt._tick(200)

  def choose(row, column, text):
    combo = dlg.table.cellWidget(row, column)
    if combo is None or not hasattr(combo, "findText"):
      return
    index = combo.findText(text)
    if index < 0:
      return
    combo.setCurrentIndex(index)
    combo.activated.emit(index)
    rt._tick(200)

  choose(0, 1, "v1")
  choose(1, 1, "landcover")
  choose(0, 2, "Quant: Quantiles")
  dlg.n_combo.setCurrentText("2")
  rt._tick(300)
  dlg.kind_combo.setCurrentText("weave")
  rt._tick(200)
  dlg.family_combo.setCurrentText("twill weave a|b")
  rt._tick(500)

  taken = snapshot(dlg)
  dlg.close()
  return taken


def scenario_a_column_appears(rt):
  """A field added in QGIS, which refills every variable chooser."""
  from weavingspace_qgis import compat
  dlg, layer, tid = rt._categorical_dialog()
  dlg._category_colours.setdefault(tid, {}).setdefault(
    "landcover", {})["forest"] = "#ff0000"
  rt._tick(200)
  layer.dataProvider().addAttributes(
    [compat.make_field("unrelated", float)])
  layer.updateFields()
  rt._tick(600)
  taken = snapshot(dlg)
  dlg.close()
  return taken


def scenario_a_table_rebuild(rt):
  """A categorized element with hand-picks, then the table rebuilt."""
  dlg, layer, tid = rt._categorical_dialog()
  dlg._category_colours.setdefault(tid, {}).setdefault(
    "landcover", {})["forest"] = "#ff0000"
  rt._tick(200)
  dlg.n_combo.setCurrentText("5")
  rt._tick(800)
  taken = snapshot(dlg)
  dlg.close()
  return taken


SCENARIOS = {
  "a_working_session": scenario_a_working_session,
  "column_appears": scenario_a_column_appears,
  "table_rebuild": scenario_a_table_rebuild,
}


def main():
  """Run the named scenario, watching one line, and print the result.

  Returns:
    None. Prints ``---PROBE---`` followed by JSON carrying the
    snapshot and whether the watched line ran. The marker exists
    because QGIS writes freely to stdout, so the caller needs a place
    to start reading rather than a hope that the output is clean.
  """
  tree, which, watched_file, watched_line = sys.argv[1:5]
  watched_line = int(watched_line)
  os.chdir(tree)
  sys.path.insert(0, tree)

  import importlib.util
  spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(tree, "tests", "run_tests.py"))
  rt = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(rt)

  from qgis.core import QgsApplication, QgsProject
  QgsApplication.setPrefixPath(
    os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  app = QgsApplication([], True)
  app.initQgis()
  rt._no_modal_dialogs()
  QgsProject.instance().clear()

  # Watch the mutated line. Without this a scenario that never reaches
  # it produces two identical snapshots and looks like a proof of
  # equivalence, which is the same fault as an ambiguous anchor
  # wearing different clothes.
  target = os.path.join(tree, watched_file)
  reached = {"hit": False}
  mon = sys.monitoring
  tool = mon.COVERAGE_ID
  mon.use_tool_id(tool, "equivalence-probe")

  def on_line(code, lineno):
    if lineno == watched_line and code.co_filename == target:
      reached["hit"] = True
    return None     # never DISABLE: the line may be reached again

  mon.register_callback(tool, mon.events.LINE, on_line)
  mon.set_events(tool, mon.events.LINE)

  # Count work as well as outcome, on the CLASS so signal-driven calls
  # are counted too (see the module docstring).
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  counts = {"rebuild": 0, "refresh": 0}
  for attr, key in (("_rebuild_unit", "rebuild"),
                    ("_refresh_preview_colours", "refresh")):
    original = getattr(WeavingSpaceDialog, attr)

    def counted(self, *a, _o=original, _k=key, **kw):
      counts[_k] += 1
      return _o(self, *a, **kw)

    setattr(WeavingSpaceDialog, attr, counted)

  taken = SCENARIOS[which](rt)
  mon.set_events(tool, 0)
  mon.free_tool_id(tool)
  taken["rebuilds"] = counts["rebuild"]
  taken["preview_refreshes"] = counts["refresh"]

  print("---PROBE---")
  print(json.dumps({"snapshot": taken, "reached": reached["hit"]}))


if __name__ == "__main__":
  main()
