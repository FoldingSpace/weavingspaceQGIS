"""Does a Save pressed while a build is coming write the motif or not?

A hunt reported on 2026-09-02 that pressing Save during a topology
build writes a GeoPackage with no motif and no dual, recording
`topology_written: False`, while the same press a second later writes
both. `_a_topology_is_owed` asks THE FILE -- somebody who has never
opened the Topology tab has no unit table and is owed nothing, which
is the cost ruling of 2026-08-30 -- so on a first save nothing is
owed, the press is not deferred, and `_write_or_drop_the_topology`
finds the panel holding the PREVIOUS design's topology and declines.

THE QUESTION THIS ASKS IS NARROWER THAN THE CLAIM. Not whether a save
should start a build (the ruling says no), but whether it should wait
for one ALREADY RUNNING for the design being saved. Two arms
differing only by a pause, driven through the Save BUTTON and read
through the file's own record.
"""
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtWidgets import QApplication  # noqa: E402
from osgeo import ogr  # noqa: E402


def tick(ms):
  """Pump the event loop for roughly ms milliseconds.

  Args:
    ms: how long to pump, in milliseconds.

  Returns:
    None.
  """
  import time
  end = time.monotonic() + ms / 1000.0
  while time.monotonic() < end:
    QApplication.processEvents()
    time.sleep(0.005)


def settle_the_tab(dlg, seconds=90.0):
  """Wait until no topology build is outstanding.

  Args:
    dlg: the dialog whose tab to settle.
    seconds: a hang-catcher rather than a budget.

  Returns:
    True where the tab went quiet, False where it never did.
  """
  import time
  deadline = time.monotonic() + seconds
  while time.monotonic() < deadline:
    building = getattr(dlg, "_topology_task", None) is not None
    queued = bool(getattr(dlg, "_topology_wanted", False))
    if not building and not queued:
      return True
    tick(200)
  return False


def what_the_file_holds(path):
  """The tables and the record a GeoPackage carries.

  Args:
    path: the file to read.

  Returns:
    (sorted table names, the working-state record or None). The OGR
    handle is released before the record is read, since an instrument
    holding a GeoPackage open changes what the next reading sees.
  """
  from weavingspace_qgis import bridge
  source = ogr.Open(path)
  names = []
  if source is not None:
    names = sorted(source.GetLayerByIndex(i).GetName()
                   for i in range(source.GetLayerCount()))
  source = None
  return names, bridge.read_working_state(path)


def run_one_arm(probe, name, pause):
  """Draw, change the design, press Save with or without a pause.

  Args:
    probe: the probe kit's handle.
    name: the arm's name, which is also its file's name.
    pause: True to let the tab go quiet before pressing Save.

  Returns:
    A dict of what was true at the press and what the file holds.
  """
  probe.clear()
  dlg, _layer, _tile_id = probe.dialog()
  dlg.opt_experimental.setChecked(True)
  dlg.live_check.setChecked(False)
  dlg.show()
  tick(200)
  dlg.n_spin.setValue(4)
  tick(200)
  probe.suite._choose_family(dlg, "laves 3.3.4.3.4")
  tick(300)
  assert settle_the_tab(dlg), "PREMISE: the first build never landed"
  panel = dlg.topology_panel
  assert panel._topology is not None, \
    "PREMISE: this design carries no topology, so nothing is owed"

  # THE DESIGN MOVES, which re-queues a build -- and the map is drawn
  # again, so the tiles are of the NEW design whatever the motif says.
  dlg.spacing_spin.setValue(900.0)
  tick(200)
  probe.generate(dlg, spacing=900.0)

  if pause:
    assert settle_the_tab(dlg), "PREMISE: the second build never landed"
    tick(200)

  at_the_press = {
    "a build is running": getattr(dlg, "_topology_task", None) is not None,
    "a build is queued": bool(getattr(dlg, "_topology_wanted", False)),
  }
  path = probe.path(f"{name}.gpkg")
  probe.save(dlg, path)
  tick(300)
  # A DEFERRED PRESS IS STILL A PRESS: wait for it to be honoured
  # before reading, or a repair that defers would read as one that
  # wrote nothing.
  for _ in range(150):
    if not getattr(dlg, "_save_pending", False):
      break
    tick(200)
  settle_the_tab(dlg)
  tick(300)

  names, record = what_the_file_holds(path)
  return {
    "at the press": at_the_press,
    "motif tables": [n for n in names if n.startswith("weavingspace_")],
    "topology_written": (record or {}).get("topology_written"),
  }


def main():
  """Drive both arms and say whether the press outran its build.

  Returns:
    None; everything is printed, and the last line is a sentinel.
  """
  probe = probe_kit.start()

  hurried = run_one_arm(probe, "hurried", pause=False)
  print("=== HURRIED: Save pressed while the build is still coming ===")
  for key, value in hurried.items():
    print(f"    {key}: {value}")

  patient = run_one_arm(probe, "patient", pause=True)
  print("=== PATIENT: the same press, after the tab goes quiet ===")
  for key, value in patient.items():
    print(f"    {key}: {value}")

  print()
  outstanding = (hurried["at the press"]["a build is running"]
                 or hurried["at the press"]["a build is queued"])
  if not outstanding:
    print("INCONCLUSIVE: no build was outstanding at the hurried press, "
          "so both arms measured the same journey")
  elif hurried["motif tables"] != patient["motif tables"]:
    print(f"CLAIM REPRODUCES: the hurried press wrote "
          f"{hurried['motif tables']} where the patient one wrote "
          f"{patient['motif tables']}, on one act and a race nobody "
          f"can see")
  else:
    print("CLAIM DOES NOT REPRODUCE HERE: both presses left the same "
          "motif tables")
  print("both arms reported; teardown next")


if __name__ == "__main__":
  main()
