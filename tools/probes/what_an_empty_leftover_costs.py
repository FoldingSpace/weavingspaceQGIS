"""Does a stub left by a cancelled save make the file nobody's for ever?

A hunt reported on 2026-09-02 that a Cancel during the FIRST save into
a path leaves an empty GeoPackage there -- the writer creates the data
source before the transaction opens, so a `RollbackTransaction` cannot
undo the creation -- and that the plugin then never recognises that
file as its own again. Every remover scoped to "our own file" is off
from then on, so when the design later loses an element, that
element's table, its column name and its values stay in the file
somebody sends on, under a record naming only the survivors.

WHAT DECIDES IT is one line in `_save_the_map`:

    existed = os.path.exists(path) and os.path.getsize(path) > 0

A stub is 65,536 bytes and holds no layer at all, so it is NON-EMPTY
BY SIZE and empty by content -- and `_this_map_owns_the_file`'s own
docstring says an empty file "is nobody's and is decided by the
caller". This measures what the caller decides.

TWO ARMS, one process, each on its own path, differing only by the
cancel:
  CONTROL   save, shrink the design, save again -- the dropped
            elements' tables must go;
  STAGED    cancel the first save, save, shrink, save again.
"""
import os
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtCore import QTimer  # noqa: E402
from qgis.PyQt.QtGui import QCloseEvent  # noqa: E402
from qgis.PyQt.QtWidgets import (  # noqa: E402
  QApplication, QMessageBox, QPushButton)
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


def tiles_in(path):
  """The element tables a GeoPackage holds, read and released at once.

  Args:
    path: the file to read.

  Returns:
    A sorted list of table names beginning `tiles_`, empty where the
    file will not open. An instrument that holds a GeoPackage open
    changes what the next reading of it sees, so the handle is let go
    before returning.
  """
  source = ogr.Open(path)
  if source is None:
    return []
  found = [source.GetLayerByIndex(i).GetName()
           for i in range(source.GetLayerCount())]
  source = None
  return sorted(name for name in found if name.startswith("tiles_"))


def cancel_the_first_save(probe, dlg, window):
  """Press Save and stop it in the middle of its write.

  Args:
    probe: the probe kit's handle, for the modal answers.
    dlg: the dialog to drive.
    window: the stand-in for QGIS's main window, which the quit is
      delivered to.

  Returns:
    True where the cancel landed while the write was running, which is
    the premise everything after this depends on.
  """
  probe.suite.MODAL_ANSWERS["question"] = QMessageBox.StandardButton.Save
  at_the_press = {}
  watcher = QTimer()
  watcher.setInterval(10)

  def press_the_cancel():
    """Click Cancel once the write is genuinely under way."""
    if not getattr(dlg, "_saving_now", False):
      return
    waiting = getattr(dlg, "_waiting_window", None)
    if waiting is None:
      return
    for button in waiting.findChildren(QPushButton):
      at_the_press["saving_now"] = True
      button.click()
      watcher.stop()
      return

  watcher.timeout.connect(press_the_cancel)
  watcher.start()
  QTimer.singleShot(0, lambda: QApplication.sendEvent(window, QCloseEvent()))
  dlg._save_the_map()
  tick(400)
  watcher.stop()
  return bool(at_the_press.get("saving_now"))


def run_one_arm(probe, name, cancel_first):
  """Drive one arm to the end and report what the file keeps.

  Args:
    probe: the probe kit's handle.
    name: the arm's name, which is also its file's name.
    cancel_first: True to stop the first save in the middle.

  Returns:
    A dict of what happened at each step.
  """
  probe.clear()
  dlg, _layer, _tile_id = probe.dialog()
  dlg.live_check.setChecked(False)
  dlg.show()
  tick(200)
  dlg.n_spin.setValue(4)
  tick(200)
  probe.generate(dlg, spacing=700.0)

  window = probe.suite._a_window_that_counts_its_closes()
  dlg.iface = probe.suite._an_iface_with_a_main_window(window)
  dlg._watch_the_main_window() if hasattr(dlg, "_watch_the_main_window") \
    else None

  path = probe.path(f"{name}.gpkg")
  dlg.gpkg_widget.setFilePath(path)

  staged = None
  if cancel_first:
    staged = cancel_the_first_save(probe, dlg, window)
    tick(200)

  after_the_stub = {
    "file exists": os.path.exists(path),
    "bytes": os.path.getsize(path) if os.path.exists(path) else 0,
    "tiles": tiles_in(path),
  }

  # THE ORDINARY SAVE THAT FOLLOWS, which is where the ownership
  # question is asked and cached for the session.
  probe.suite.MODAL_ANSWERS["question"] = QMessageBox.StandardButton.Yes
  dlg._save_the_map()
  tick(400)
  owned = dlg._file_was_ours_when_met.get(dlg._gpkg_key(path))
  four = tiles_in(path)

  # AND THEN THE DESIGN LOSES TWO ELEMENTS, which is the act the drop
  # exists for: the tables of the elements that have gone must not
  # travel in the file somebody sends on.
  dlg.n_spin.setValue(2)
  tick(300)
  probe.generate(dlg, spacing=700.0)
  dlg.gpkg_widget.setFilePath(path)
  dlg._save_the_map()
  tick(400)
  two = tiles_in(path)

  return {
    "cancel landed mid-write": staged,
    "after the stub": after_the_stub,
    "ours when met": owned,
    "tables at four elements": four,
    "tables after shrinking to two": two,
  }


def main():
  """Drive both arms and say what the leftover costs.

  Returns:
    None; everything is printed, and the last line is a sentinel so a
    run that died at teardown can be told from one that stopped early.
  """
  probe = probe_kit.start()

  control = run_one_arm(probe, "control", cancel_first=False)
  print("=== CONTROL: nothing is cancelled ===")
  for key, value in control.items():
    print(f"    {key}: {value}")

  staged = run_one_arm(probe, "staged", cancel_first=True)
  print("=== STAGED: the first save is cancelled mid-write ===")
  for key, value in staged.items():
    print(f"    {key}: {value}")

  print()
  if not staged.get("cancel landed mid-write"):
    print("INCONCLUSIVE: the cancel never landed while the write was "
          "running, so this arm measured some other journey")
  else:
    left = [name for name in staged["tables after shrinking to two"]
            if name not in control["tables after shrinking to two"]]
    if left:
      print(f"CLAIM REPRODUCES: after the stub the file was "
            f"{staged['ours when met']!r} to us, and shrinking the "
            f"design left {left} behind where the control dropped them")
    else:
      print("CLAIM DOES NOT REPRODUCE HERE: both arms ended with the "
            "same tables, so the stub cost the drop nothing")
  print("both arms reported; teardown next")


if __name__ == "__main__":
  main()
