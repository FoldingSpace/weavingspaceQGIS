"""Does ledger row 35 still reproduce, and what does it cost?

THE CLAIM. If somebody else saves the shared file while your map is
open, your Save reports success and leaves the GeoPackage with NO map
in it. The mechanism named is the skip in `_save_the_map`: a layer
whose source string already names a table in this file is treated as
already saved, and nothing asks whether that table is still THERE --
so every element is skipped, the names go into `written_names` as
though they had been written, and the stale-table drop then removes
what the file does hold.

THE JOURNEY HAD TO BE REBUILT ONCE, and the first version is worth
recording because it looked like a clean answer. It had the parent
create the file and the colleague save into it afterwards -- and a
colleague meeting somebody else's GeoPackage does not own it, so
their drop returns at its first line and their map is simply ADDED
beside the parent's. Nothing of the parent's was ever removed, so the
precondition the whole claim rests on -- a layer pointing at a table
that is no longer there -- never existed. The file must be the
COLLEAGUE'S, opened by the parent with Load, and changed by the
colleague while the parent holds it open.

IT ALSO FOUND SOMETHING ELSE ON THE WAY, kept here because it is a
finding rather than an artefact of the wrong journey: in that
arrangement the parent's own Save silently REMOVED the colleague's
`tiles_b_v1`, a table added to a file the parent owns. That is
measured separately by `audit_a_save_removes_a_guests_table.py`.

WHAT THIS PROBE IS AND IS NOT. It drives the journey and prints what
it finds; it decides nothing. Where the file comes back with no
element table the row stands and the harm is a person's map destroyed
by their own Save. Where it comes back holding a map, the row needs
re-reading rather than re-fixing.

THE CONTROL RUNS FIRST AND ITS ANSWER IS NOT SUCCESS. A second save
with nobody else touching the file must leave the map intact -- the
ordinary "open, change something, save" journey, which was itself
broken once. Without it, an empty file at the end could as easily be
the press failing for reasons of its own.
"""

import os
import subprocess
import sys
import time

sys.path.insert(0, os.environ.get("WS_REPO", os.getcwd()))

from tools.probe_kit import start                      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def a_map_in(names) -> bool:
  """Does this list of tables hold a map anybody could open?

  Args:
    names: table names as `probe.tables` returns them.

  Returns:
    True where at least one element table is present. A pair table
    does not count: `tiles_a_v1_no_data` on its own is a set of holes
    belonging to nothing, which is the orphan case row 46 was about.
  """
  return any(name.startswith("tiles_") and not name.endswith("_no_data")
             for name in names)


def wait_for(flag, seconds=300) -> bool:
  """Poll for one of the colleague's signals.

  Args:
    flag: the path they touch.
    seconds: the ceiling. Generous, because the colleague is a whole
      QGIS starting up and drawing a map; a ceiling a healthy run can
      reach is worse than none.

  Returns:
    True where it appeared, False on the ceiling.
  """
  until = time.monotonic() + seconds
  while time.monotonic() < until:
    if os.path.exists(flag):
      return True
    time.sleep(0.25)
  return False


def load(probe, dlg, path):
  """Open the shared file the way a person does.

  Args:
    probe: the running `Probe`.
    dlg: this process's dialog.
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
    "PREMISE: the Load brought back no map, so there is none to lose"


def main():
  """Drive a colleague's save into a file this map has open.

  Returns:
    None; it prints, and the verdict is the line beginning OPEN,
    CLOSED, PARTLY or INCONCLUSIVE.

  THE CONTROL RUNS FIRST AND ITS ANSWER IS NOT SUCCESS: an ordinary
  second save, with nobody else acting, must leave the map intact. An
  empty file at the end would otherwise be indistinguishable from a
  press that failed for reasons of its own.
  """
  probe = start()
  path = probe.path("shared.gpkg")
  ready, go = probe.path("ready-1"), probe.path("go-2")
  colleague = subprocess.Popen(
    [sys.executable, os.path.join(HERE, "colleague_saves_into.py"),
     path, ready, go],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

  from weavingspace_qgis.dialog import WeavingSpaceDialog
  dlg = WeavingSpaceDialog(iface=probe.suite._Iface())
  try:
    dlg.live_check.setChecked(False)
    if not wait_for(ready):
      print("  INCONCLUSIVE: the colleague never created the file")
      colleague.kill()
      print(colleague.communicate()[0][-2000:])
      return
    print(f"  the colleague's file holds {probe.tables(path)}")

    # ---- I OPEN THEIR MAP
    load(probe, dlg, path)
    reading = sorted(
      (layer.source().split("layername=", 1)[-1].split("|")[0]
       for layer in (probe.project.mapLayer(i or "")
                     for i in dlg._element_layer_ids.values())
       if layer is not None and "layername=" in layer.source()))
    print(f"  I opened it; my layers read {reading}")

    # ---- THE CONTROL: my own save, with nobody else touching it
    assert probe.save(dlg, path), "CONTROL: my save of their map was refused"
    control = probe.tables(path)
    print(f"  control, my save with nobody else acting: {control}")
    print(f"  control holds a map: {a_map_in(control)}"
          + ("" if a_map_in(control) else
             "  <-- THE CONTROL IS BROKEN, so nothing below means "
             "anything about row 35"))

    # ---- THE TREATMENT: they change their design and save, while my
    # map is open and my layers go on pointing at their old tables.
    open(go, "w").close()
    out = colleague.communicate(timeout=600)[0]
    for line in out.splitlines():
      if line.startswith("COLLEAGUE:"):
        print(f"  {line}")
    if colleague.returncode != 0:
      print(f"  INCONCLUSIVE: the colleague exited {colleague.returncode}")
      print(out[-2000:])
      return
    between = probe.tables(path)
    print(f"  after their second save the file holds {between}")
    orphaned = [name for name in reading if name not in between]
    print(f"  tables my layers point at that are no longer there: "
          f"{orphaned}")
    if not orphaned:
      print("  INCONCLUSIVE: their save left every table my layers "
            "read, so the precondition the claim rests on was never "
            "reached")
      return

    # ---- WHAT IS LEFT OF THE ORPHANED LAYER, which is what decides
    # what a repair can honestly DO. If a layer whose table has been
    # dropped still yields its features, the save can write it afresh
    # and nobody loses anything; if it yields nothing, the data is
    # gone from under us and writing it would replace a real table
    # with an empty one -- a repair worse than the defect. The cheap
    # answers are asked with the expensive one beside them, because a
    # provider's count is a cached answer and this project has read
    # one as the world before (ledger row 32).
    for tid, layer_id in sorted(dlg._element_layer_ids.items()):
      layer = probe.project.mapLayer(layer_id or "")
      if layer is None:
        continue
      table = layer.source().split("layername=", 1)[-1].split("|")[0]
      if table not in orphaned:
        continue
      got = sum(1 for _ in layer.getFeatures())
      print(f"  element {tid}, whose table {table} has gone: "
            f"isValid={layer.isValid()}, "
            f"provider valid={layer.dataProvider().isValid()}, "
            f"featureCount={layer.featureCount()}, "
            f"features actually yielded={got}")

    # ---- ...AND I PRESS SAVE, believing my map is still mine
    ok = probe.save(dlg, path)
    after = probe.tables(path)
    print(f"  my save reported: {ok}")
    print(f"  said: {probe.said(dlg)[-240:]!r}")
    print(f"  the file now holds: {after}")
    if not a_map_in(after):
      print("  OPEN: my Save emptied the file -- no element table at "
            "all, so neither map can be opened by anybody")
    elif any(name in after for name in orphaned):
      print("  CLOSED here: my own tables were written back")
    else:
      print(f"  PARTLY: the file still holds {sorted(after)}, which "
            f"is not the map I saved")
  finally:
    dlg.close()
    if colleague.poll() is None:
      colleague.kill()


main()
