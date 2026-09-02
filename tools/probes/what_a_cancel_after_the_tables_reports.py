"""What does the waiting window say about a cancel it could not serve?

A hunt reported on 2026-09-02 that "Cancel the save" pressed once the
tables are in -- during the styling or the repointing, which the save
itself measures at 13.0s at the 256-element ceiling -- writes the map
anyway and then reports that it was not written. It drove the cancel
from the STYLES pump and read the file with stdlib sqlite3.

THIS TAKES A LATER SEAM AND THREE OTHER ORACLES. The press is
delivered from the REPOINTING pump -- `compat.point_layer_at`, one
phase further on, where the styles are already embedded as well -- and
what is read is the file through OGR, the SENTENCES in the order they
were said, and the element layers' own sources. The last is the half
that says what the person is left holding: a save that reaches its
repointing has backed their map with the file, so a sentence claiming
nothing was written is false about the project as well as the file.

WHAT MAKES THE CLAIM ABOUT THE SENTENCE RATHER THAN THE SAVE. Nothing
can stop a write past the last table: `write_gpkg_layers` asks
`should_stop` BETWEEN tables and the transaction is already committed.
That is settled and correct. What is not is the hold reporting the
answer to a question only the writer can ask -- it resumes, finds
`_saving_now` cleared by the writer that has just FINISHED, and cannot
tell that from a wait where nothing ever started.

TWO ARMS, one process, each on its own file:
  EARLY  the press delivered between tables, which is the journey the
         button was built for -- the rollback lands and the writer's
         own sentence is the true one;
  LATE   the press delivered from the repointing, which is the claim.
"""
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtCore import QTimer  # noqa: E402
from qgis.PyQt.QtWidgets import QApplication  # noqa: E402
from qgis.PyQt.QtWidgets import QMessageBox, QPushButton  # noqa: E402
from osgeo import ogr  # noqa: E402


def tables(path):
  """The element tables the file holds, read through OGR.

  Args:
    path: the file to read.

  Returns:
    A sorted list of `tiles_` table names, empty where it will not
    open. OGR rather than sqlite3 deliberately: the hunt read this
    with sqlite3, and a second reader is what makes the reading
    independent rather than a second run of one instrument.
  """
  source = ogr.Open(path)
  if source is None:
    return []
  names = [source.GetLayerByIndex(i).GetName()
           for i in range(source.GetLayerCount())]
  source = None
  return sorted(n for n in names if n.startswith("tiles_"))


def press_the_cancel(dlg):
  """Click the waiting window's Cancel, where a person would.

  Args:
    dlg: the dialog holding the window for the length of the wait.

  Returns:
    True where a button was found and clicked. The window is built
    inside `_hold_until_the_save_lands` and held on `_waiting_window`
    for exactly this reason -- a window built inside a method is a
    window no test can press.
  """
  window = getattr(dlg, "_waiting_window", None)
  if window is None:
    return False
  for child in window.findChildren(QPushButton):
    if "cancel" in child.text().lower():
      child.click()
      return True
  return False


def run_one_arm(probe, name, when):
  """Drive one arm and report the file, the sentences and the layers.

  Args:
    probe: the probe kit's handle.
    name: the arm's name, which is also its file's name.
    when: "early" to press between tables, "late" to press from the
      repointing pump.

  Returns:
    A dict of what the writer was asked, what the file holds, what was
    said in order, and which element layers now read from the file.
  """
  probe.clear()
  dlg, _layer, _tile_id = probe.dialog()
  dlg.live_check.setChecked(False)
  dlg.show()
  probe.generate(dlg, spacing=700.0)

  spoken = []
  real_report = dlg._report_quietly

  def remember(text, *args, **kwargs):
    spoken.append(text)
    return real_report(text, *args, **kwargs)

  dlg._report_quietly = remember

  from weavingspace_qgis import bridge as bridge_module
  from weavingspace_qgis import compat as compat_module
  asked = []
  pressed = {"done": False, "at": None}
  real_writer = bridge_module.write_gpkg_layers
  real_point = compat_module.point_layer_at

  def watched_writer(*args, **kwargs):
    """Record every answer the writer's stop callback gives."""
    stop = kwargs.get("should_stop")
    if stop is not None:
      def remember_answer():
        answer = stop()
        asked.append(bool(answer))
        if when == "early" and not pressed["done"]:
          # BETWEEN TABLES, which is the one moment the flag is read.
          pressed["done"] = True
          pressed["at"] = "between tables" if press_the_cancel(dlg) \
              else None
        return answer
      kwargs["should_stop"] = remember_answer
    return real_writer(*args, **kwargs)

  def watched_point(*args, **kwargs):
    """Press from the repointing, one phase past the styles."""
    if when == "late" and not pressed["done"]:
      pressed["done"] = True
      pressed["at"] = "repointing" if press_the_cancel(dlg) else None
    return real_point(*args, **kwargs)

  bridge_module.write_gpkg_layers = watched_writer
  compat_module.point_layer_at = watched_point

  # THE WAIT IS STAGED THE WAY A PERSON REACHES IT: a promise the
  # plugin has made and not yet kept, then a close, which opens the
  # waiting window -- and the queued save then runs INSIDE that
  # window's own pump, which is where the button is live.
  probe.suite.MODAL_ANSWERS["question"] = QMessageBox.StandardButton.Save
  path = probe.path(f"{name}.gpkg")
  dlg.gpkg_widget.setFilePath(path)
  dlg._save_pending = True
  QTimer.singleShot(0, dlg.close)
  for _ in range(200):
    QApplication.processEvents()

  from qgis.core import QgsProject
  reads = []
  for layer_id in dlg._element_layer_ids.values():
    layer = QgsProject.instance().mapLayer(layer_id)
    if layer is not None and path in layer.source():
      reads.append(layer.name())

  bridge_module.write_gpkg_layers = real_writer
  compat_module.point_layer_at = real_point
  return {
    "pressed at": pressed["at"],
    "should_stop answered": asked,
    "tables": tables(path),
    "said": spoken[-3:],
    "layers reading from the file": reads,
  }


def main():
  """Drive both arms and say whether the claim reproduces.

  Returns:
    None; everything is printed, and the last line is a sentinel so a
    run that died at teardown can be told from one that stopped early.
  """
  probe = probe_kit.start()

  early = run_one_arm(probe, "early", "early")
  print("=== EARLY: the press lands between tables ===")
  for key, value in early.items():
    print(f"    {key}: {value}")
  assert early["pressed at"], \
    "PREMISE: no Cancel was pressed, so this arm measured nothing"

  late = run_one_arm(probe, "late", "late")
  print("=== LATE: the press lands during the repointing ===")
  for key, value in late.items():
    print(f"    {key}: {value}")

  print()
  said = " ".join(late["said"]).lower()
  claimed = "was not written" in said
  if late["pressed at"] is None:
    print("INCONCLUSIVE: the late arm never found a window to press")
  elif late["tables"] and claimed:
    print(f"CLAIM REPRODUCES: the file holds {len(late['tables'])} "
          f"tables and {len(late['layers reading from the file'])} "
          f"layers read from it, and the person was told the map was "
          f"not written")
  elif late["tables"] and not claimed:
    print("THE SENTENCE IS THE WRITER'S: the save completed and only "
          "the save spoke about it")
  else:
    print(f"INCONCLUSIVE: tables={late['tables']} said={late['said']}")
  print("both arms reported; teardown next")


if __name__ == "__main__":
  main()
