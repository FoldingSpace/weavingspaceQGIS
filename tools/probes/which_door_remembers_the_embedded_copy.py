"""Does an adopted map remember that its file carried the data?

`_embed_or_drop_the_source` asks the checkbox first, and where it is
untouched it asks a per-FILE memory instead: `_embedded_when_resumed`,
added 2026-08-28 so that a recipient who has never touched the box
cannot strip a copy the sender deliberately included. The reasoning is
written at the line and is right.

THAT MEMORY HAS ONE WRITER, in `_recover_the_source`, which only the
two RESUME branches call. Adoption -- the door a person takes by
reopening the plugin over a project that already holds the map -- goes
through `_point_the_chooser_at` and writes nothing. The box is back at
its default there, `_embed_touches` is zero, and the drop written for
the act of unticking fires for the act's ABSENCE.

TWO DOORS, ONE FILE, WHICH IS WHAT SAYS WHOSE DEFECT IT IS. The hunt
that reported this drove the reopen and read the file's bytes. This
drives BOTH doors on the same file in one run and reads the DECISION's
own inputs at the moment of the press -- what the box says, what the
memory holds -- beside what the file ends up with, so a difference
names the door rather than the journey.

Run it with BOTH the checkout and this directory's parent on the path:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \\
      | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1
    PYTHONPATH="$PWD:$PWD/tools" "$QGIS_PY" -u \\
      tools/probes/which_door_remembers_the_embedded_copy.py
"""

import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from probe_kit import start  # noqa: E402


def a_self_contained_file(probe, path):
  """Draw a map, tick "Include the source data", and save it.

  Args:
    probe: the harness, whose project this clears first.
    path: where the sender's file should go.

  Returns:
    None. Raises where the copy did not reach the file, since a
    fixture that never embedded anything cannot show it being lost.
  """
  from weavingspace_qgis import bridge
  probe.clear()
  dlg, _layer, _tid = probe.dialog()
  try:
    probe.generate(dlg, spacing=700.0)
    dlg.opt_embed_source.setChecked(True)
    assert probe.save(dlg, path), "PREMISE: the sender's save failed"
    held = bridge.gpkg_tables(path)
    assert bridge.REGION_TABLE_NAME in held, \
      f"PREMISE: the sender's file carries no copy of the data: {held}"
    record = bridge.read_working_state(path) or {}
    assert record.get("region_embedded"), \
      "PREMISE: the file's own record does not say it is self-contained"
  finally:
    dlg.close()


def arm(probe, name, door):
  """Open the sender's file by one door, press Save, and read both.

  Args:
    probe: the harness.
    name: names the arm and its own copy of the sender's file.
    door: "load" to press Load, or "adopt" to open a NEW dialog over
      the project the map is already in, which is what reopening the
      plugin does.

  Returns:
    (what the box said, what the memory held, whether the copy
    survived).
  """
  import shutil
  from weavingspace_qgis import bridge
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  probe.clear()
  sender = probe.path("sender.gpkg")
  path = probe.path(f"{name}.gpkg")
  shutil.copyfile(sender, path)

  dlg, _layer, _tid = probe.dialog()
  try:
    if door == "load":
      dlg.resume_widget.setFilePath(path)
      dlg.load_button.click()
      probe.suite._tick(600)
      working = dlg
    else:
      # THE MAP IS OPENED FIRST so there is a group to adopt, and then
      # a NEW dialog is built over that project -- which is what
      # reopening the plugin does, and is the door the memory's own
      # writer is never on.
      dlg.resume_widget.setFilePath(path)
      dlg.load_button.click()
      probe.suite._tick(600)
      dlg.close()
      working = WeavingSpaceDialog(iface=probe.suite._Iface())
      working.live_check.setChecked(False)
      probe.suite._tick(600)
    assert working._element_layer_ids, \
      f"PREMISE: the {door} door opened no map, so nothing is staged"
    box = working.opt_embed_source.isChecked()
    memory = working._embedded_when_resumed.get(
      working._gpkg_key(path), ("no entry", None))
    working.gpkg_widget.setFilePath(path)
    probe.suite.press_save(working, path)
    survived = bridge.REGION_TABLE_NAME in bridge.gpkg_tables(path)
    print(f"  {name} ({door}):")
    print(f"    the box says          : {box}")
    print(f"    the memory holds      : {memory}")
    print(f"    the copy survived     : {survived}")
    return box, memory, survived
  finally:
    try:
      working.close()
    except Exception:
      pass


def main():
  """Drive both doors on one file and print the verdicts.

  Returns:
    None. It prints a sentinel once both arms have reported and the
    teardown is over, because an instrument that dies after reporting
    looks exactly like the thing it measures dying.
  """
  probe = start()
  print("WHICH DOOR REMEMBERS THE EMBEDDED COPY")
  a_self_contained_file(probe, probe.path("sender.gpkg"))
  _b1, _m1, load = arm(probe, "byload", "load")
  _b2, _m2, adopt = arm(probe, "byadopt", "adopt")
  print()
  print(f"  the Load door kept the sender's copy   : {load}")
  print(f"  the adoption door kept it              : {adopt}")
  print("BOTH ARMS REPORTED, teardown complete.")


main()
