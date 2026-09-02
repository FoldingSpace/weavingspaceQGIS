"""Can the waiting window ever be satisfied when the write is BELOW it?

A hunt reported on 2026-09-02 that closing the plugin window while the
map is being written, and answering the question's own default -- Save
-- freezes the waiting window for the whole `SAVE_WAIT_CEILING`,
because the hold spins on `_a_save_is_outstanding()` and `_saving_now`
is cleared only by the frame beneath it. The write cannot progress
while the hold pumps, so the condition can never come true.

THIS DRIVES THE OTHER DOOR. The hunt used the plugin window's close,
which asks a question first; this uses QGIS'S QUIT through the event
filter, which asks nothing at all and reaches the same hold.

THE CEILING IS SHORTENED TO SIX SECONDS AND THAT IS SAID OUT LOUD:
the real one is 180s, which is a hang-catcher rather than a budget,
and a probe that waits three minutes to prove a freeze is a probe
nobody runs. What is measured is whether the press ends at the CEILING
or at the save.
"""
import sys
import time

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtCore import QTimer  # noqa: E402
from qgis.PyQt.QtGui import QCloseEvent  # noqa: E402
from qgis.PyQt.QtWidgets import QApplication, QPushButton  # noqa: E402


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


def run_one_arm(probe, name, quit_during_the_write):
  """Save, with or without a quit delivered inside the write.

  Args:
    probe: the probe kit's handle.
    name: the arm's name, also its file's name.
    quit_during_the_write: True to send QGIS's Close from the write's
      own pump.

  Returns:
    A dict of how long the press took, what was true at the quit, and
    what the file holds.
  """
  probe.clear()
  window = probe.suite._a_window_that_counts_its_closes()
  iface = probe.suite._an_iface_with_a_main_window(window)
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  dlg = WeavingSpaceDialog(iface=iface)
  layer = probe.suite.make_region_layer()
  probe.project.addMapLayer(layer)
  dlg.live_check.setChecked(False)
  dlg.show()
  tick(200)
  dlg._generate()
  probe.suite._settle(dlg)

  # A HANG-CATCHER SHORTENED SO THE PROBE CAN RUN, said rather than
  # smuggled: the product's own ceiling is 180s.
  dlg.SAVE_WAIT_CEILING = 6.0
  path = probe.path(f"{name}.gpkg")
  dlg.gpkg_widget.setFilePath(path)

  at_the_quit = {}
  escape = QTimer()
  escape.setInterval(50)

  def let_it_go():
    """Press Cancel if the window is still up near the ceiling.

    Returns:
      None. Without this a frozen arm holds the probe for the whole
      ceiling; pressing at the end measures the freeze and then
      releases it.
    """
    waiting = getattr(dlg, "_waiting_window", None)
    if waiting is None:
      return
    if time.monotonic() - at_the_quit.get("shown at", 0.0) < 5.0:
      return
    for button in waiting.findChildren(QPushButton):
      button.click()
      escape.stop()
      return

  escape.timeout.connect(let_it_go)

  if quit_during_the_write:
    def deliver():
      """Send QGIS's Close from inside the write's own pump."""
      at_the_quit["saving_now"] = bool(getattr(dlg, "_saving_now", False))
      at_the_quit["shown at"] = time.monotonic()
      escape.start()
      QApplication.sendEvent(window, QCloseEvent())
    QTimer.singleShot(0, deliver)

  started = time.monotonic()
  dlg._save_the_map()
  took = time.monotonic() - started
  escape.stop()
  tick(200)

  from weavingspace_qgis import bridge
  tables = sorted(name for name in bridge.gpkg_tables(path)
                  if name.startswith("tiles_"))
  return {
    "the press took": round(took, 2),
    "at the quit": at_the_quit,
    "tables": tables,
    "closes seen": window.closes,
  }


def main():
  """Drive both arms and say whether the hold can be satisfied.

  Returns:
    None; everything is printed, and the last line is a sentinel.
  """
  probe = probe_kit.start()

  plain = run_one_arm(probe, "plain", quit_during_the_write=False)
  print("=== CONTROL: nothing interrupts the save ===")
  for key, value in plain.items():
    print(f"    {key}: {value}")

  held = run_one_arm(probe, "held", quit_during_the_write=True)
  print("=== QUIT delivered by the write's own pump ===")
  for key, value in held.items():
    print(f"    {key}: {value}")

  print()
  if not held["at the quit"].get("saving_now"):
    print("INCONCLUSIVE: the quit did not land during the write")
  elif held["the press took"] >= 5.0:
    print(f"CLAIM REPRODUCES: the press took {held['the press took']}s "
          f"against the control's {plain['the press took']}s -- the hold "
          f"waits for a flag only the frame beneath it can clear, so it "
          f"ends at the ceiling rather than at the save")
  else:
    print("CLAIM DOES NOT REPRODUCE HERE: the press ended at the save "
          "rather than at the ceiling")
  print("both arms reported; teardown next")


if __name__ == "__main__":
  main()
