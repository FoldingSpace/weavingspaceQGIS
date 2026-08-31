"""Does picking an output group while a tiling runs destroy that map?

CLAIM 1 of the hunt round of 2026-08-25, and the first of the two that
decide whether the rest matter. It was reported by READING: the
in-flight guard `if self._task is not None` sits in
`_bind_group_to_dataset` and in neither of the two other methods that
reach the same work, `_on_group_chosen` and `_resume_from_gpkg`. This
project's rule is that a site named by reading is a HYPOTHESIS, and
that it reads exactly like one somebody proved -- so this drives the
product instead, through the control's own signal, and reads the
layer tree afterwards.

THE HARM THE READING PREDICTS, stated before the measurement so it is
falsifiable. `_take_over_group` clears `_element_layer_ids` and adopts
the chosen group's layers into it. `_add_output_layers` reads that
same dict as `old_ids` when the run lands, and removes every layer it
names. So a group chosen mid-run would have its own layers removed by
a run that was never about it, while the group the run WAS about is
left orphaned in the project with nothing claiming it.

WHAT WOULD REFUTE IT, and either answer is worth having. The chooser
might be disabled during a run, in which case no user can reach this;
`activated` might not be connected to the handler; or the landing
might re-derive its group from something other than the records this
repoints. Each is checked and printed rather than assumed.

AND ONE OF THEM DID, WHICH IS WHY THERE ARE TWO LEGS. Measured
2026-08-26: picking ANOTHER DATASET'S group mid-run destroys nothing,
because the landing already refuses to write into a group whose
`weavingspace_region` stamps name a different dataset -- ruling 5 of
2026-08-24, arriving from a direction it was not written for, and
emptying `old_ids` so nothing is removed. The behaviour is held
REDUNDANTLY there, which this project's own rule says to establish
before concluding a guard is missing.

THAT PROTECTION CANNOT ANSWER FOR TWO GROUPS OF ONE DATASET, and
A-B-A has made that an ordinary state since ruling 2. The stamps say
the same thing about both, so nothing distinguishes the group the run
was launched against from the one chosen underneath it. The second
leg is that case, and it is the one to read.

WHY `activated.emit` AND NOT `setCurrentIndex` ALONE: setting a
combo's index programmatically emits `currentIndexChanged` and NOT
`activated`, which is the signal a click sends and the one the handler
is connected to. Driving the wrong one measures a path nobody is on --
this project's own rule about testing through the events a real
interaction sends.

Run it under QGIS's own Python:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \
            | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen
    "$QGIS_PY" -u tools/probes/a_group_chosen_mid_run_deletes_its_map.py
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


def layers_of(group):
  """The ids of the layers a layer-tree group currently holds.

  Args:
    group: a QgsLayerTreeGroup, or None.

  Returns:
    A set of layer id strings, empty when the group is None or holds
    nothing. Asked of the TREE rather than of the dialog's records,
    deliberately: the records are the thing under suspicion here, so
    reading them would be asking the accused for an alibi.
  """
  if group is None:
    return set()
  return {child.layer().id() for child in group.children()
          if getattr(child, "layer", lambda: None)() is not None}


def group_named(name):
  """The layer-tree group with this name, or None.

  Args:
    name: the group's name as the dialog recorded it.

  Returns:
    The QgsLayerTreeGroup, or None when no group carries that name.
    A name is a LABEL in this project and never an identity, which is
    fine here because the probe is the only thing renaming anything.
  """
  root = QgsProject.instance().layerTreeRoot()
  return next((g for g in root.findGroups() if g.name() == name), None)


def a_leg(dlg, project, run_on, victim_group, spacing, label):
  """Start a run on one dataset and pick another group underneath it.

  Args:
    dlg: the dialog, already holding output for both groups.
    project: the QgsProject, read for whether a layer still exists.
    run_on: the region layer the run is launched against.
    victim_group: the name of the group to choose mid-run.
    spacing: what to tile at. Given per leg rather than derived from
      whatever the spinner holds, because choosing a group RESTORES
      that group's spacing -- so a leg deriving its own number from
      the box can land on the value the previous leg already tiled
      at, and the run then takes the restyle fast path. Measured
      2026-08-26: both legs computed 464.8 and the second staged
      nothing at all.
    label: how this leg names itself in the printout.

  Returns:
    True when the chosen group came through with every layer it had,
    False when the run removed any of them -- or when the leg could
    not be staged at all, since a leg that did not reach its own case
    must never be read as good news.
  """
  print(f"\n---- {label}")
  before = layers_of(group_named(victim_group))
  dlg.layer_combo.setLayer(run_on)
  rt._tick(900)
  print(f"working on           {dlg._group_name!r}")
  print(f"{victim_group!r} holds  {len(before)} layers")
  if not before:
    print("CANNOT BE STAGED: the group to be chosen is empty, so "
          "nothing below would mean anything.")
    return False

  # A spacing change is a GEOMETRY term, so this cannot take the
  # restyle fast path and leave nothing in flight to interfere with.
  del rt.MODALS[:]
  del rt.BAR_MESSAGES[:]
  dlg.spacing_spin.setValue(spacing)
  rt._tick(300)
  # ASSERT THE PREMISE BEFORE THE ACT. `_generate` takes the restyle
  # fast path when the geometry signature has not moved, and a leg
  # that quietly restyles instead of tiling measures nothing while
  # looking exactly like one that did.
  moves = dlg._geometry_signature() != dlg._last_geometry_sig
  print(f"spacing              {spacing:.1f}, geometry moves {moves}")
  dlg._generate()
  if dlg._task is None:
    # SAY WHAT WAS FOUND, not which assertion was reached: a leg that
    # cannot stage its own case is a fact about the probe, and the
    # only way to fix it is to know which door closed.
    print(f"PREMISE FAILED: no task was in flight after Generate at "
          f"spacing {spacing:.1f}, so the journey this leg is about "
          f"never began.")
    print(f"  modals           {rt.MODALS[-3:]}")
    print(f"  message bar      {rt.BAR_MESSAGES[-3:]}")
    print(f"  live note        {dlg.live_note.text()!r}")
    return False
  print("a run is in flight   True")

  # WHAT A CLICK SENDS. The chooser is not disabled during a run --
  # only the Generate button is -- so this is an ordinary act.
  combo = dlg.group_combo
  wanted = next((i for i in range(combo.count())
                 if victim_group in combo.itemText(i)), -1)
  offered = [combo.itemText(i) for i in range(combo.count())]
  print(f"on offer             {offered}")
  if wanted < 0:
    print(f"UNREACHABLE BY THIS DOOR: {victim_group!r} is not in the "
          f"chooser while a run is in flight.")
    return False
  combo.setCurrentIndex(wanted)
  combo.activated.emit(wanted)
  rt._tick(200)
  print(f"records now name     {len(dlg._element_layer_ids)} layers")

  rt._settle(dlg)
  rt._tick(500)

  alive = {lid for lid in before if project.mapLayer(lid) is not None}
  print(f"after the landing    {len(alive)} of {len(before)} of "
        f"{victim_group!r}'s layers survive")
  print(f"the run landed in    {dlg._group_name!r}")
  if len(alive) < len(before):
    print(f"CONFIRMED: {len(before) - len(alive)} of {len(before)} "
          f"layers destroyed by a run that was not about them.")
    return False
  return True


def main():
  """Drive both legs and print what survived each.

  Returns:
    0 when choosing a group mid-run leaves every map intact, 1 when
    any leg lost layers or could not be staged. The exit code is the
    point: this can gate the fix.
  """
  app = QgsApplication([], False)
  app.initQgis()
  project = QgsProject.instance()
  project.clear()
  rt._no_modal_dialogs()

  A = rt.make_region_layer(n=4, cell=1000)
  A.setName("Aotearoa")
  B = rt.make_region_layer(n=4, cell=1000, origin=(900_000, 0))
  B.setName("Bermuda")
  project.addMapLayer(A)
  project.addMapLayer(B)

  dlg = WeavingSpaceDialog(iface=rt._Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(A)
  rt._tick(300)
  dlg.spacing_spin.setValue(520)
  rt._generate_and_wait(dlg)
  rt._tick(300)
  a_first = dlg._group_name

  # A SECOND GROUP FOR A, through the door the user has for it. This
  # is what makes the same-dataset leg a real question: since ruling 2
  # a demo of several datasets in a row leaves exactly this state.
  # THE CHOOSER IS THE ONLY DOOR since 2026-08-30; the
  # "Create as new group" checkbox this probe used was retired.
  from weavingspace_qgis.dialog import NEW_GROUP_LABEL
  _index = dlg.group_combo.findText(NEW_GROUP_LABEL)
  assert _index >= 0, "the chooser offers no 'Create new' entry"
  dlg.group_combo.setCurrentIndex(_index)
  dlg.group_combo.activated.emit(_index)
  dlg.spacing_spin.setValue(560)
  rt._generate_and_wait(dlg)
  rt._tick(300)
  a_second = dlg._group_name

  dlg.layer_combo.setLayer(B)
  rt._tick(700)
  dlg.spacing_spin.setValue(700)
  rt._generate_and_wait(dlg)
  rt._tick(300)
  b_group = dlg._group_name

  print(f"A's first group     {a_first!r}")
  print(f"A's second group    {a_second!r}")
  print(f"B's group           {b_group!r}")
  if len({a_first, a_second, b_group}) != 3:
    print("\nTHE FIXTURE CANNOT SHOW THE HARM: the three runs did not "
          "make three distinct groups.")
    return 1

  # LEG ONE: another dataset's group. The stamps can answer here.
  ok_one = a_leg(dlg, project, A, b_group, 464.8,
                 "another dataset's group, chosen mid-run")
  # LEG TWO: the same dataset's OTHER group, where the stamps say the
  # same thing about both and cannot tell them apart.
  ok_two = a_leg(dlg, project, A, a_first, 383.5,
                 "the same dataset's other group, chosen mid-run")

  if ok_one and ok_two:
    print("\nNOT REPRODUCED by either route: every layer survived.")
    return 0
  print("\nTHE CLAIM STANDS on at least one route above.")
  return 1


if __name__ == "__main__":
  sys.exit(main())
