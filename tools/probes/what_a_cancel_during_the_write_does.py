"""Does Cancel stop a write that is already running, or only say so?

A hunt reported on 2026-09-02 that a cancel pressed while
`_save_the_map` is WRITING leaves the map written anyway and the
person told "Saved", because the hold's own frame is nested BELOW the
write: `_hold_until_the_save_lands` clears `_save_cancelled` on its
way out, and the suspended writer then reads False and carries on.
The comment at that line says the opposite -- "the pump that delivered
the click sits inside that write" -- which is true of the ordinary
deferred press and false of this one.

THIS TAKES THE OTHER DOOR. The hunt drove QGIS's QUIT through the
event filter and read the file with stdlib sqlite3; this drives the
PLUGIN WINDOW's own close, which reaches the same hold from
`closeEvent`, and reads the file through OGR. Two doors and two
readers, so a disagreement cannot be one probe's fixture.

THREE ARMS, one process, each on its own file:
  CONTROL    save with nothing interrupting it -- the tables must be
             there, or the arms below measure a save that never
             worked;
  PROMISED   cancel while the save is only PROMISED, which is the
             journey the button was built for -- nothing written;
  WRITING    cancel delivered inside the write's own pump, which is
             the claim.
"""
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtCore import QTimer  # noqa: E402
from qgis.PyQt.QtWidgets import QApplication, QPushButton  # noqa: E402
from osgeo import ogr  # noqa: E402


def tables(path):
  """What the GeoPackage holds, read through OGR and let go at once.

  Args:
    path: the file to read.

  Returns:
    {layer name: feature count}, empty where the file will not open.
    OGR rather than sqlite3 deliberately: the hunt that reported this
    read it with sqlite3, and a second reader is what makes the
    reading independent rather than a second run of one instrument.
  """
  source = ogr.Open(path)
  if source is None:
    return {}
  found = {}
  for index in range(source.GetLayerCount()):
    layer = source.GetLayerByIndex(index)
    found[layer.GetName()] = layer.GetFeatureCount()
  source = None
  return found


def press_cancel_when_the_window_appears(dlg, when, said):
  """Click "Cancel the save" as soon as the waiting window exists.

  Args:
    dlg: the dialog being driven.
    when: "promised" to press as soon as the window is up, "writing"
      to press only once `_saving_now` is True, which is what makes
      the two arms differ by the MOMENT rather than by the act.
    said: a dict this fills in with what was true at the press, so the
      arm can assert its own premise instead of hoping.

  Returns:
    The QTimer, which the caller must keep alive: a timer nobody holds
    is collected and never fires, which reads exactly like a button
    that does nothing.
  """
  timer = QTimer()
  timer.setInterval(10)

  def look():
    window = getattr(dlg, "_waiting_window", None)
    if window is None:
      return
    if when == "writing" and not getattr(dlg, "_saving_now", False):
      return
    for button in window.findChildren(QPushButton):
      if "cancel" in button.text().lower():
        said["saving_now_at_the_press"] = bool(
          getattr(dlg, "_saving_now", False))
        said["pending_at_the_press"] = bool(
          getattr(dlg, "_save_pending", False))
        button.click()
        timer.stop()
        return

  timer.timeout.connect(look)
  timer.start()
  return timer


def run_one_arm(probe, name, interrupt):
  """Drive one arm and report what the file holds and what was said.

  Args:
    probe: the probe kit's handle.
    name: the arm's name, which is also its file's name.
    interrupt: None for the control, or "promised"/"writing" for the
      moment at which the close and the cancel are delivered.

  Returns:
    A dict of what happened: the tables, the sentences, and the
    premise readings taken at the press.
  """
  probe.clear()
  dlg, _layer, _tile_id = probe.dialog()
  dlg.live_check.setChecked(False)
  dlg.show()
  probe.generate(dlg, spacing=700.0)

  # WHAT THE WRITER ITSELF SAW, measured at the SEAM rather than by
  # reading the code: the real `write_gpkg_layers` is called, with its
  # `should_stop` argument wrapped so every answer it gives is
  # recorded. Replacing the function under test would measure the
  # stand-in; wrapping its argument measures the product.
  from weavingspace_qgis import bridge as bridge_module
  asked = []
  real_writer = bridge_module.write_gpkg_layers

  def watched_writer(*args, **kwargs):
    stop = kwargs.get("should_stop")
    if stop is not None:
      def remember_answer():
        answer = stop()
        asked.append(bool(answer))
        return answer
      kwargs["should_stop"] = remember_answer
    return real_writer(*args, **kwargs)

  bridge_module.write_gpkg_layers = watched_writer

  # EVERYTHING THE PLUGIN SAYS, collected at the one door rather than
  # off the message bar: a probe reading `said()` can come back empty
  # because a live tick clears the note before its own gate.
  spoken = []
  real_report = dlg._report_quietly

  def remember(text, *args, **kwargs):
    spoken.append(text)
    return real_report(text, *args, **kwargs)

  dlg._report_quietly = remember

  # THE CLOSE ASKS BEFORE IT HOLDS, and the answer is what routes it:
  # "Save" reaches `_hold_until_the_save_lands`, "Close" drops the
  # promise instead. Staging Save is what makes this the same room the
  # hunt reached through QGIS's quit, which asks nothing.
  from qgis.PyQt.QtWidgets import QMessageBox
  probe.suite.MODAL_ANSWERS["question"] = QMessageBox.StandardButton.Save

  path = probe.path(f"{name}.gpkg")
  # THE BUTTON READS THE WIDGET, so the widget is what a probe sets --
  # handing the path to the method instead would drive a journey
  # nobody is on.
  dlg.gpkg_widget.setFilePath(path)
  at_the_press = {}
  keep_alive = None
  if interrupt is not None:
    keep_alive = press_cancel_when_the_window_appears(
      dlg, interrupt, at_the_press)
    if interrupt == "writing":
      # DELIVERED AT THE FIRST PUMP INSIDE THE WRITE. `_save_the_map`
      # turns the event loop once per element behind its progress
      # bar, so a zero timer armed here fires there -- which is what
      # puts the hold's frame BELOW the write rather than after it.
      QTimer.singleShot(0, dlg.close)
    else:
      QTimer.singleShot(0, dlg.close)

  dlg._save_the_map()
  for _ in range(60):
    QApplication.processEvents()

  found = tables(path)
  if keep_alive is not None:
    keep_alive.stop()
  bridge_module.write_gpkg_layers = real_writer
  return {
    "tables": {k: v for k, v in found.items()
               if k.startswith("tiles_")},
    "said": spoken[-2:],
    "premise": at_the_press,
    "asked": asked,
  }


def main():
  """Drive the three arms and say whether the claim reproduces.

  Returns:
    None; everything is printed, and the last line is a sentinel so a
    run that died at teardown can be told from one that stopped early.
  """
  probe = probe_kit.start()

  control = run_one_arm(probe, "control", None)
  print("=== CONTROL: nothing interrupts the save ===")
  print(f"    tables {control['tables']}")
  print(f"    said   {control['said']}")
  assert control["tables"], \
    "PREMISE: the plain save wrote nothing, so the arms below mean nothing"

  promised = run_one_arm(probe, "promised", "promised")
  print("=== PROMISED: cancel before the write opens the file ===")
  print(f"    at the press {promised['premise']}")
  print(f"    tables {promised['tables']}")
  print(f"    said   {promised['said']}")

  writing = run_one_arm(probe, "writing", "writing")
  print("=== WRITING: cancel delivered inside the write's own pump ===")
  print(f"    at the press {writing['premise']}")
  print(f"    tables {writing['tables']}")
  print(f"    said   {writing['said']}")
  print(f"    the writer asked should_stop and was told {writing['asked']}")

  print()
  if not writing["premise"].get("saving_now_at_the_press"):
    print("INCONCLUSIVE: the press never landed while `_saving_now`, so "
          "this arm measured the promised journey again rather than the "
          "one claimed")
  elif writing["tables"]:
    print(f"CLAIM REPRODUCES: cancelled during the write and the file "
          f"holds {writing['tables']}, with the plugin saying "
          f"{writing['said']}")
  else:
    print("CLAIM DOES NOT REPRODUCE HERE: the cancelled write left no "
          "tables, which is what the button promises")
  print("all three arms reported; teardown next")


if __name__ == "__main__":
  main()
