"""Does pressing Load arm the protections a landing arms?

A hunt reported on 2026-09-02 that `_resume_from_gpkg` has two
branches for one button and only one of them records that a map has
been opened. The FRESH branch sets `_landed_this_session`, under a
comment naming exactly what its absence cost on 2026-08-28; the
ALREADY-OPEN branch -- the door a person takes when the map's layers
are still in the project, which is what reopening a saved project
gives them -- does not.

`switched_from_work = switched and self._landed_this_session`. So on
that door a change of region dataset reads as a FIRST CHOICE:
`_begin_new_dataset` never runs, the output path stays pointed at the
file just opened, nothing is said, and the next Generate and Save put
the other dataset's tiles into the first map's own file.

THIS MEASURES THE ASYMMETRY RATHER THAN THE LOSS, which is the
difference from the hunt's route. The hunt drove the whole journey to
its end and read the tiles' extents back with stdlib sqlite3 -- and
said honestly that a control WITHOUT the press reaches the same end
state, since the flag is False after any project read. So the claim is
not "this journey loses a map" but "the PRESS does not arm what its
twin arms", and the thing to compare is the two doors against each
other, on one journey, reading what the switch does:

  the flag itself, which is what `switched_from_work` asks;
  the OUTPUT PATH after the switch, which `_begin_new_dataset` clears
    so that a Generate cannot land in the file just opened;
  and whether anything was SAID, since a cleared path is announced.

TWO ARMS, one process, one journey, differing only in whether the
map's layers are already in the project when Load is pressed.
"""
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtWidgets import QApplication  # noqa: E402


def run_one_arm(probe, name, already_open):
  """Save a map, open it through one door, then switch dataset.

  Args:
    probe: the probe kit's handle.
    name: the arm's name, which is also its file's name.
    already_open: True to press Load while the map's own layers are
      still in the project, which is the door under test; False to
      clear them first, which is the fresh branch.

  Returns:
    A dict of the flag, the output path before and after the switch,
    and what the plugin said about the switch.
  """
  probe.clear()
  dlg, layer, _tile_id = probe.dialog()
  dlg.live_check.setChecked(False)
  dlg.show()
  probe.generate(dlg, spacing=700.0)
  path = probe.path(f"{name}.gpkg")
  assert probe.save(dlg, path), f"PREMISE: {name} was never saved"

  # A SECOND DATASET TO SWITCH TO, added now so both arms have one.
  from qgis.core import QgsProject
  other = probe.suite.make_region_layer(origin=(50000, 50000))
  other.setName(f"other-{name}")
  QgsProject.instance().addMapLayer(other)

  if not already_open:
    # THE FRESH DOOR: the map's own layers are gone, which is what a
    # person has after opening a different project, or after removing
    # the group. `_resume_from_gpkg` then takes its other branch.
    for layer_id in list(dlg._element_layer_ids.values()):
      QgsProject.instance().removeMapLayer(layer_id)
    for _ in range(20):
      QApplication.processEvents()

  # THE PLUGIN IS REOPENED BEFORE THE PRESS, and this arrangement is
  # the whole of the fixture. `_add_output_layers` sets
  # `_landed_this_session` when a map LANDS, so a probe that draws a
  # map and then presses Load in the same window has the flag set by
  # the drawing and can measure nothing about the press. The journey
  # the claim is about starts with a person who has yesterday's map in
  # front of them -- a project read, or the plugin closed and opened
  # again, which is the door `_adopt_existing_group` exists for and
  # which its own docstring calls something users do constantly.
  # My first run of this probe missed it and reported both doors
  # sound; the tell was that the control could not fail either.
  dlg.close()
  for _ in range(20):
    QApplication.processEvents()
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  dlg = WeavingSpaceDialog(iface=probe.suite._Iface())
  dlg.live_check.setChecked(False)
  dlg.show()
  for _ in range(40):
    QApplication.processEvents()
  assert not getattr(dlg, "_landed_this_session", False), (
    "PREMISE: the reopened dialog already counts a landing, so the "
    "press cannot be what arms anything")

  dlg.resume_widget.setFilePath(path)
  dlg.load_button.click()
  for _ in range(60):
    QApplication.processEvents()

  before = dlg.gpkg_widget.filePath()
  flag = bool(getattr(dlg, "_landed_this_session", False))

  spoken = []
  real_report = dlg._report_quietly

  def remember(text, *args, **kwargs):
    spoken.append(text)
    return real_report(text, *args, **kwargs)

  dlg._report_quietly = remember
  # THE SWITCH IS DRIVEN THROUGH THE CHOOSER, which is what a person
  # moves and what carries the switch machinery; setting a record
  # would measure the record.
  dlg.layer_combo.setLayer(other)
  for _ in range(60):
    QApplication.processEvents()

  return {
    "landed_this_session after the Load": flag,
    "output path before the switch": bool(before),
    "output path after the switch": bool(dlg.gpkg_widget.filePath()),
    "said about the switch": spoken[-2:],
    "region in force": dlg.layer_combo.currentLayer().name()
    if dlg.layer_combo.currentLayer() is not None else None,
  }


def main():
  """Drive both doors and say whether they arm the same things.

  Returns:
    None; everything is printed, and the last line is a sentinel.
  """
  probe = probe_kit.start()

  fresh = run_one_arm(probe, "fresh", already_open=False)
  print("=== FRESH: the map's layers are not in the project ===")
  for key, value in fresh.items():
    print(f"    {key}: {value}")

  already = run_one_arm(probe, "already", already_open=True)
  print("=== ALREADY OPEN: the map's own layers are still there ===")
  for key, value in already.items():
    print(f"    {key}: {value}")

  print()
  if not fresh["landed_this_session after the Load"]:
    print("INCONCLUSIVE: the fresh door did not arm it either, so "
          "there is no asymmetry to measure and the control failed")
  elif not already["landed_this_session after the Load"]:
    print(f"CLAIM REPRODUCES: the fresh door records the map as this "
          f"session's work and the already-open door does not, so the "
          f"switch away from it kept the output path "
          f"({already['output path after the switch']}) and said "
          f"{already['said about the switch']}")
  else:
    print("BOTH DOORS ARM IT: the asymmetry is closed")
  print("both arms reported; teardown next")


if __name__ == "__main__":
  main()
