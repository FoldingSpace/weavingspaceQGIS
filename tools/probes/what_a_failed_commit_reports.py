"""Does a save whose commit fails say so, or say "Saved"?

A hunt reported on 2026-09-02 that when the GeoPackage commit does not
go through, the plugin reports a save, writes nothing, and repoints
every element layer at tables that are not there -- so the map on
screen becomes four empty layers and the tiles in memory are gone.

WHAT IT TURNS ON is that `data.CommitTransaction()`'s ANSWER is never
read. The rollback branch beside it clears `written`, saying at the
line that otherwise "the caller would repoint layers at tables that
went away"; the commit branch has an `except` that cannot fire,
because OGR reports this failure by RETURN VALUE rather than by
raising.

THIS TAKES A DIFFERENT ROUTE FROM THE HUNT'S, which held a sqlite
transaction inside the same process. A running QGIS serves its own
cached pages, and this project's own rule is that the second writer
must be a second PROCESS -- so the lock here is held by one, which is
also what a colleague, a script or a sync client would be.
"""
import os
import subprocess
import sys
import time

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtWidgets import QApplication  # noqa: E402
from osgeo import ogr  # noqa: E402

HOLDER = """
import sqlite3, sys, time
path, flag = sys.argv[1], sys.argv[2]
handle = sqlite3.connect(path, isolation_level=None)
handle.execute("BEGIN IMMEDIATE")
handle.execute("CREATE TABLE IF NOT EXISTS held (n INTEGER)")
open(flag, "w").write("held")
while time.time() < float(sys.argv[3]):
  time.sleep(0.05)
handle.execute("ROLLBACK")
handle.close()
"""


def tick(ms):
  """Pump the event loop for roughly ms milliseconds.

  Args:
    ms: how long to pump, in milliseconds.

  Returns:
    None.
  """
  end = time.monotonic() + ms / 1000.0
  while time.monotonic() < end:
    QApplication.processEvents()
    time.sleep(0.005)


def tiles_in(path):
  """The element tables a GeoPackage holds, released at once.

  Args:
    path: the file to read.

  Returns:
    A sorted list of `tiles_` table names, empty where it will not
    open.
  """
  source = ogr.Open(path)
  if source is None:
    return []
  names = [source.GetLayerByIndex(i).GetName()
           for i in range(source.GetLayerCount())]
  source = None
  return sorted(n for n in names if n.startswith("tiles_"))


def layers_still_hold_their_tiles(dlg):
  """Whether every element layer still yields features.

  Args:
    dlg: the dialog whose output layers to ask.

  Returns:
    A list of (layer name, is valid, features iterated). A layer whose
    table went out from under it answers valid True and yields
    nothing, which is why this iterates rather than trusting the
    count.
  """
  from qgis.core import QgsProject
  found = []
  for layer_id in dlg._element_layer_ids.values():
    layer = QgsProject.instance().mapLayer(layer_id)
    if layer is None:
      found.append(("<gone>", False, 0))
      continue
    seen = sum(1 for _f in layer.getFeatures())
    found.append((layer.name(), layer.isValid(), seen))
  return found


def run_one_arm(probe, name, lock_it, mode="immediate"):
  """Save into a file, with or without another process holding it.

  Args:
    probe: the probe kit's handle.
    name: the arm's name, also its file's name.
    lock_it: True to hold a transaction on the file while the save
      runs.
    mode: "immediate" for a WRITE lock held by a second PROCESS, which
      is what a colleague or a sync client would hold; "shared" for a
      READ transaction held IN THIS process, which lets the writes
      through and blocks only the COMMIT. The two reach different
      failures and only one of them is the claim.

  Returns:
    A dict of what the plugin said, what the file holds, and what the
    map's own layers still carry.
  """
  probe.clear()
  dlg, _layer, _tile_id = probe.dialog()
  dlg.live_check.setChecked(False)
  dlg.show()
  tick(200)
  probe.generate(dlg, spacing=700.0)

  spoken = []
  real_report = dlg._report_quietly

  def remember(text, *args, **kwargs):
    spoken.append(text)
    return real_report(text, *args, **kwargs)

  dlg._report_quietly = remember

  path = probe.path(f"{name}.gpkg")
  # THE FILE EXISTS FIRST, because a lock is held on a file rather
  # than on a name -- and because this is the ordinary case anyway: a
  # colleague's GeoPackage, or your own from an earlier session.
  made = ogr.GetDriverByName("GPKG").CreateDataSource(path)
  made.CreateLayer("notes")
  made = None

  holder = None
  reader = None
  flag = path + ".held"
  if lock_it and mode == "shared":
    # A SHARED READ LOCK, held here rather than by another process:
    # sqlite lets the writer work and refuses it the exclusive lock a
    # COMMIT needs, which is the state the claim is about.
    import sqlite3
    reader = sqlite3.connect(path, isolation_level=None)
    reader.execute("BEGIN")
    reader.execute("SELECT count(*) FROM sqlite_master").fetchone()
  elif lock_it:
    script = probe.path("hold_the_file.py")
    with open(script, "w") as handle:
      handle.write(HOLDER)
    # A CLEAN ENVIRONMENT, or the holder dies at bootstrap. This
    # process runs under QGIS's own interpreter with PYTHONHOME set,
    # and a system python3 that inherits it fails with "No module
    # named 'encodings'" -- which is this project's two-interpreters
    # trap, met inside a probe's own subprocess. It cost one run.
    holder = subprocess.Popen(
      ["/usr/bin/python3", script, path, flag, str(time.time() + 60)],
      env={"PATH": "/usr/bin:/bin"})
    for _ in range(200):
      if os.path.exists(flag):
        break
      time.sleep(0.05)

  premise = None
  if lock_it and mode == "shared":
    premise = "a shared read transaction is open on the file"
  elif lock_it:
    import sqlite3
    try:
      other = sqlite3.connect(path, timeout=0.3, isolation_level=None)
      other.execute("BEGIN IMMEDIATE")
      other.execute("ROLLBACK")
      other.close()
      premise = "the lock was NOT held: another writer got in"
    except Exception as trouble:                        # noqa: BLE001
      premise = f"the lock is held ({type(trouble).__name__})"

  dlg.gpkg_widget.setFilePath(path)
  from qgis.PyQt.QtWidgets import QMessageBox
  probe.suite.MODAL_ANSWERS["question"] = QMessageBox.StandardButton.Yes
  dlg._save_the_map()
  tick(400)

  layers = layers_still_hold_their_tiles(dlg)
  if reader is not None:
    reader.execute("ROLLBACK")
    reader.close()
  if holder is not None:
    holder.terminate()
    holder.wait(timeout=10)
  tick(200)

  return {
    "premise": premise,
    "said": spoken[-1:] ,
    "tiles in the file": tiles_in(path),
    "layers (name, valid, features)": layers,
  }


def main():
  """Drive both arms and say what a failed commit reports.

  Returns:
    None; everything is printed, and the last line is a sentinel.
  """
  probe = probe_kit.start()

  plain = run_one_arm(probe, "plain", lock_it=False)
  print("=== CONTROL: nothing is holding the file ===")
  for key, value in plain.items():
    print(f"    {key}: {value}")

  locked = run_one_arm(probe, "locked", lock_it=True)
  print("=== LOCKED: another process holds a write transaction ===")
  for key, value in locked.items():
    print(f"    {key}: {value}")

  shared = run_one_arm(probe, "shared", lock_it=True, mode="shared")
  print("=== SHARED: a read transaction blocks only the commit ===")
  for key, value in shared.items():
    print(f"    {key}: {value}")
  emptied_shared = [name for name, _v, seen in
                    shared["layers (name, valid, features)"] if seen == 0]
  said_shared = " ".join(shared["said"]).lower()
  if not shared["tiles in the file"] and "saved" in said_shared:
    print(f"    CLAIM REPRODUCES ON THIS ARM: nothing in the file, "
          f"{shared['said']}, and {len(emptied_shared)} layers now "
          f"yield nothing")

  print()
  emptied = [name for name, _valid, seen in
             locked["layers (name, valid, features)"] if seen == 0]
  said = " ".join(locked["said"]).lower()
  if (locked["premise"] or "").startswith("the lock was NOT held"):
    print("INCONCLUSIVE: nothing was holding the file, so the locked "
          "arm measured the ordinary journey")
  elif not locked["tiles in the file"] and emptied and "saved" in said:
    print(f"CLAIM REPRODUCES: the file holds no tiles, the plugin said "
          f"{locked['said']}, and {len(emptied)} of "
          f"{len(locked['layers (name, valid, features)'])} layers now "
          f"yield nothing -- the map on screen is gone")
  elif not locked["tiles in the file"] and "saved" not in said:
    print(f"THE SAVE FAILED AND SAID SO: {locked['said']}")
  else:
    print("CLAIM DOES NOT REPRODUCE HERE")
  print("both arms reported; teardown next")


if __name__ == "__main__":
  main()
