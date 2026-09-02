"""Does a topology edit survive into the next project?

`_forget_the_last_project` empties every record keyed by tile id when
QgsProject says `cleared`, which fires on File > New and immediately
before File > Open. `_scheme_memory` joined that list on 2026-08-25,
after a scheme shelved in the project you CLOSED redrew a column in
the project you OPENED. `_topology_shelf` is not in it, and nothing
clears the panel's own edit list.

MEASURED AT THE RECORDS RATHER THAN AT THE GEOMETRY, which is the
route the hunt did not take: it drove the whole journey and compared
per-element perimeters and vertex counts in the next project's map.
This reads the SHELF and the PANEL across the clear, with
`_scheme_memory` beside them as the CONTROL -- a record that is in the
list, so a run where it survives too would be saying the clear never
happened rather than that the shelf is missing from it.

Then the harm is walked to its end in the same run: the design is
chosen again in the emptied project and the unit's own ground is
compared with a control dialog that never edited anything.

Run it with BOTH the checkout and this directory's parent on the path:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \\
      | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1
    PYTHONPATH="$PWD:$PWD/tools" "$QGIS_PY" -u \\
      tools/probes/what_a_new_project_leaves_on_the_shelf.py
"""

import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from probe_kit import start  # noqa: E402

DESIGN = "laves 3.3.4.3.4"          # carries a topology at inset zero


def ground(unit):
  """The unit's own area and perimeter, to a part in a thousand.

  Args:
    unit: the tileable the dialog is drawing from, or None.

  Returns:
    (area, perimeter) rounded, or None. Rounded because the question
    is whether an edit reached this design at all, and the answer is
    orders of magnitude rather than a last bit.
  """
  if unit is None or getattr(unit, "tiles", None) is None:
    return None
  shapes = unit.tiles.geometry
  return (round(float(shapes.area.sum()), 3),
          round(float(shapes.length.sum()), 3))


def edit_the_topology(probe, dlg):
  """Tick the experiments, wait for a build, and apply one edit.

  Args:
    probe: the harness, for its suite's own helpers.
    dlg: the dialog to drive.

  Returns:
    The number of edits the panel holds afterwards. Raises where the
    tab could not be brought to a state an edit can be aimed from,
    because a fixture that cannot aim measures nothing.
  """
  suite = probe.suite
  suite._choose_family(dlg, DESIGN)
  suite._tick(300)
  dlg.opt_experimental.setChecked(True)
  assert suite._the_topology_tab_is_quiet(dlg), \
    "PREMISE: no topology was built, so there is nothing to edit"
  panel = dlg.topology_panel
  assert panel.class_combo.count(), \
    "PREMISE: the tab offers no class, so an edit cannot be aimed"
  # AN EDIT THAT MOVES THE DESIGN, CHOSEN RATHER THAN TAKEN. The first
  # index of each chooser is a VERTEX class and `push_vertex`, whose
  # displacement on this design is exactly zero -- the incident unit
  # vectors cancel, which docs/TOPOLOGY.md measures at 1.5e-9. A
  # fixture aimed there records an edit and changes nothing, so the
  # journey afterwards cannot show anything being carried.
  before = ground(dlg._unit)
  chosen = None
  for index in range(panel.class_combo.count()):
    panel.class_combo.setCurrentIndex(index)
    suite._tick(120)
    for how in range(panel.how_combo.count()):
      if str(panel.how_combo.itemData(how)) in ("zigzag_edge",
                                                "rotate_edge",
                                                "scale_edge"):
        panel.how_combo.setCurrentIndex(how)
        suite._tick(120)
        chosen = (panel.class_combo.currentText(),
                  panel.how_combo.itemData(how))
        break
    if chosen:
      break
  assert chosen, \
    "PREMISE: the tab offers no edge manipulation on this design"
  panel.apply_button.click()
  suite._tick(400)
  assert suite._the_topology_tab_is_quiet(dlg), \
    "PREMISE: the edit's own rebuild never settled"
  after = ground(dlg._unit)
  assert after != before, (
    f"PREMISE: {chosen} changed nothing about the design "
    f"({before} -> {after}), so nothing can be seen to be carried "
    f"into the next project")
  return len(panel.edits())


def main():
  """Drive the journey and print what each record held at each step.

  Returns:
    None. It prints a sentinel once the arms have reported and the
    teardown is over, because an instrument that dies after reporting
    looks exactly like the thing it measures dying.
  """
  probe = start()
  print("WHAT A NEW PROJECT LEAVES ON THE SHELF")
  dlg, _layer, tid = probe.dialog()
  try:
    made = edit_the_topology(probe, dlg)
    assert made, "PREMISE: the Apply recorded no edit at all"
    # A SCHEME BESIDE IT, as the control: `_scheme_memory` IS in the
    # clear list, so if it survives too the clear never ran and this
    # probe is measuring its own fixture.
    dlg._scheme_memory[(tid, "v1")] = {"mode": "Categorized"}
    edited = ground(dlg._unit)
    print(f"    before the clear : shelf={len(dlg._topology_shelf)} "
          f"panel={len(dlg.topology_panel.edits())} "
          f"scheme={len(dlg._scheme_memory)} ground={edited}")

    # ---- FILE > NEW, which is the act, and which QGIS reports by
    # clearing the project.
    probe.project.clear()
    probe.suite._tick(600)
    print(f"    after the clear  : shelf={len(dlg._topology_shelf)} "
          f"panel={len(dlg.topology_panel.edits())} "
          f"scheme={len(dlg._scheme_memory)}")

    # ---- AND THE NEXT PROJECT'S MAP, drawn from the same design in
    # the same window, against a dialog that never edited anything.
    fresh = probe.suite.make_region_layer()
    probe.project.addMapLayer(fresh)
    dlg.layer_combo.setLayer(fresh)
    probe.suite._tick(400)
    probe.suite._choose_family(dlg, DESIGN)
    probe.suite._tick(600)
    carried = ground(dlg._unit)

    probe.clear()
    control, _l, _t = probe.dialog()
    try:
      probe.suite._choose_family(control, DESIGN)
      probe.suite._tick(600)
      untouched = ground(control._unit)
    finally:
      control.close()

    print(f"    the next project : ground={carried}")
    print(f"    a control's      : ground={untouched}")
    print()
    print(f"  the shelf survived the clear : "
          f"{len(dlg._topology_shelf) > 0}")
    print(f"  the panel kept its edits     : "
          f"{len(dlg.topology_panel.edits()) > 0}")
    print(f"  the scheme memory survived   : "
          f"{len(dlg._scheme_memory) > 0}   (the control: must be False)")
    print(f"  the next project's unit      : "
          f"{'DIFFERS from a control' if carried != untouched else 'matches a control'}")
  finally:
    dlg.close()
  print("REPORTED, teardown complete.")


main()
