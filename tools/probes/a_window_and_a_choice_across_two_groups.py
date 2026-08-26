"""Does a group carry its own ramp window, and does an explicit choice stick?

Two claims of the hunt round of 2026-08-25, both against the binding
and both reported by READING.

**A RAMP WINDOW CARRIED BETWEEN GROUPS.** `_apply_element_records`
writes `_ramp_ranges[tid]` only when the incoming record's window is
not the default, where its two siblings on the neighbouring lines
assign unconditionally:

    self._reverse_choices[tid] = bool(element.get("reverse"))
    self._class_choices[tid] = element.get("class_choice") or ""
    window = element.get("range_bounds")
    if window and tuple(window) != (0, 100):     # <- the asymmetry
      self._ramp_ranges[tid] = tuple(window)

Nothing else clears the record -- `_detach_from_the_group` empties the
layer ids and the signatures and not this -- so a window narrowed on
one group would survive onto a group whose own record says the ramp
runs end to end. That is a wrong map: the classes take their colours
from a stretch of ramp nobody chose for them.

**THE BINDING TAKES THE NEWEST GROUP.** Ruling 3 makes recency the
tie-break where a dataset owns several groups, and the combo re-emits
`layerChanged` whenever the project's layers churn -- which a run does
twice. The claim is that a deliberately chosen OLDER group would
therefore be taken away again by ordinary churn, which would make
ruling 1's chooser something the user cannot actually overrule.

BOTH ARE ASKED OF THE DIALOG'S OWN RECORDS AND OF THE MAP, because a
window that is merely recorded is not yet a wrong map, and a chooser
that reads right while the records point elsewhere is worse than one
that reads wrong.

Run it under QGIS's own Python:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \
            | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen
    "$QGIS_PY" -u tools/probes/a_window_and_a_choice_across_two_groups.py
"""
import importlib.util
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

from qgis.core import QgsApplication, QgsProject  # noqa: E402
from weavingspace_qgis.dialog import WeavingSpaceDialog  # noqa: E402

NARROW = (10, 40)


def main():
  """Narrow a window on one group, then work on another.

  Returns:
    0 when both claims come back clean, 1 when either is confirmed.
  """
  app = QgsApplication([], False)
  app.initQgis()
  project = QgsProject.instance()
  project.clear()
  rt._no_modal_dialogs()
  confirmed = []

  layer = rt.make_region_layer(n=4, cell=1000)
  layer.setName("Aotearoa")
  project.addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=rt._Iface())
  try:
    dlg.live_check.setChecked(False)
    dlg.layer_combo.setLayer(layer)
    rt._tick(500)
    tid = dlg._assignments()[0]["id"]

    # ---- GROUP ONE, with a narrowed ramp display range on element a
    dlg._ramp_ranges[tid] = NARROW
    dlg.spacing_spin.setValue(520)
    rt._generate_and_wait(dlg)
    rt._tick(400)
    first = dlg._group_name
    print(f"group one            {first!r}")
    print(f"  its window         {dlg._ramp_ranges.get(tid)}")

    # ---- GROUP TWO, made deliberately as its own, with NO window
    dlg._ramp_ranges.pop(tid, None)
    dlg.opt_new_group.setChecked(True)
    dlg.spacing_spin.setValue(560)
    rt._generate_and_wait(dlg)
    rt._tick(400)
    dlg.opt_new_group.setChecked(False)
    second = dlg._group_name
    print(f"group two            {second!r}")
    print(f"  its window         {dlg._ramp_ranges.get(tid)}")
    if first == second:
      print("\nCANNOT BE STAGED: the two runs did not make two groups.")
      return 1

    def choose(name):
      """Pick a group in the chooser the way a click does.

      Args:
        name: the group's own name, matched against the label's group
          half EXACTLY. Substring matching picked the wrong entry
          first time: an entry reading "WeavingSpace tiles 2 —
          Aotearoa" contains "WeavingSpace tiles", so asking for the
          older group selected the newer one and the leg then
          reported that an explicit choice had not survived churn it
          never met.

      Returns:
        True when the entry was found and activated.
      """
      combo = dlg.group_combo
      where = -1
      for i in range(combo.count()):
        label = combo.itemText(i)
        if label.split(" — ")[0].strip() == name:
          where = i
          break
      if where < 0:
        return False
      combo.setCurrentIndex(where)
      combo.activated.emit(where)
      rt._tick(700)
      return True

    def window_in(name):
      """What a group's own stamped record says its ramp window is."""
      from weavingspace_qgis.dialog import WORKING_STATE_PROPERTY
      import json as _json
      node = next((g for g in project.layerTreeRoot().findGroups()
                   if g.name() == name), None)
      raw = node.customProperty(WORKING_STATE_PROPERTY) if node else None
      if not raw:
        return "no record"
      for element in (_json.loads(raw).get("elements") or []):
        if element.get("id") == tid:
          return element.get("range_bounds")
      return "no such element"

    print(f"\nrecord of group one  window {window_in(first)}")
    print(f"record of group two  window {window_in(second)}")

    # ---- CLAIM: the window rides from group one to group two
    if not choose(first):
      print("group one is not on offer, so nothing can be asked")
      return 1
    print(f"\nchose group one      window {dlg._ramp_ranges.get(tid)}")
    carried_in = dlg._ramp_ranges.get(tid)
    if not choose(second):
      print("group two is not on offer, so nothing can be asked")
      return 1
    carried_out = dlg._ramp_ranges.get(tid)
    print(f"chose group two      window {carried_out}")
    if carried_in and tuple(carried_in) == NARROW \
        and carried_out and tuple(carried_out) == NARROW:
      confirmed.append(
        f"A RAMP WINDOW RODE BETWEEN GROUPS: element {tid!r} keeps "
        f"{tuple(carried_out)} on a group whose own record says the "
        f"ramp runs end to end, so its classes take their colours "
        f"from a stretch nobody chose for them")
    elif not carried_in or tuple(carried_in) != NARROW:
      confirmed.append(
        f"CANNOT BE ASKED: choosing group one gave back "
        f"{carried_in!r} rather than {NARROW}, so there was no "
        f"window to ride out again")

    # ---- CLAIM: an explicit older choice is taken away by churn
    if not choose(first):
      print("group one is not on offer for the second claim")
      return 1
    print(f"\nchose the OLDER      {dlg._group_name!r}")
    on_the_older = dlg._group_name
    older_node = next((g for g in project.layerTreeRoot().findGroups()
                       if g.name() == first), None)
    in_older = {c.layer().id() for c in (older_node.children() if older_node
                                         else [])
                if getattr(c, "layer", lambda: None)() is not None}
    print(f"  records name       {len(dlg._element_layer_ids)} layers, "
          f"{len(set(dlg._element_layer_ids.values()) & in_older)} of "
          f"them in the older group")
    # ORDINARY CHURN, which is what a run causes twice: the combo
    # re-emits `layerChanged` whenever the project's layers move.
    spare = rt.make_region_layer(n=2, cell=500, origin=(-50_000, 0))
    spare.setName("spare")
    project.addMapLayer(spare)
    rt._tick(400)
    project.removeMapLayer(spare.id())
    rt._tick(700)
    print(f"after layer churn    {dlg._group_name!r}")
    print(f"  records name       {len(dlg._element_layer_ids)} layers, "
          f"{len(set(dlg._element_layer_ids.values()) & in_older)} of "
          f"them in the older group")
    print(f"the chooser reads    {dlg.group_combo.currentText()!r}")
    if on_the_older == first and dlg._group_name != first:
      confirmed.append(
        f"AN EXPLICIT CHOICE DID NOT SURVIVE ORDINARY CHURN: the "
        f"user chose {first!r} and the dialog is on "
        f"{dlg._group_name!r}, so ruling 1's chooser names a map the "
        f"user cannot actually keep")
  finally:
    dlg.close()
    project.clear()

  if confirmed:
    print("\nCONFIRMED:")
    for one in confirmed:
      print(f"  - {one}")
    return 1
  print("\nNOT REPRODUCED: both claims came back clean.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
