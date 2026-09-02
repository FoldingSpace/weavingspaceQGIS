"""Does answering "Close" to the save question stop the save?

TWO HUNTS REPORTED THIS INDEPENDENTLY on 2026-09-02, from opposite
directions -- one reading the day's own repairs, one asking which of
the live path's gates has a precondition nothing produces -- and both
read the harm off the FILE, with stdlib sqlite3 and with OGR.

`closeEvent` asks "This map has not been saved yet. Save it before
closing?" whenever `_a_save_is_outstanding()`, and that predicate
deliberately merges two facts: `_save_pending`, a promise made and not
yet kept, and `_saving_now`, the keeping of it. The Close arm answers
only the first -- it clears the promise and reports "Closed without
saving" -- so during a WRITE it clears a flag that is already False,
says nothing was written, and the write goes on to completion.

THIS TAKES A THIRD ORACLE, because a claim two probes have measured
one way is worth measuring another. It reads neither the file's tables
nor its bytes:

  THE PROJECT'S OWN LAYERS. A save that runs to the end repoints every
  element layer at the file through `compat.point_layer_at`. So after
  a close the person declined to save through, the map in their
  project is BACKED BY the file they said not to write -- which is a
  harm neither hunt named and which no reading of the file can show.

  AND THE SENTENCES IN ORDER. `_report_quietly` is wrapped, so the
  contradiction is read as a sequence rather than as a final state:
  "Closed without saving; the map is still in the project." followed
  by "Saved to ...".

TWO ARMS, one process, each on its own file:
  PROMISED  Close answered while the save is only PROMISED, which is
            the journey the sentence was written for. It must be true
            there, or the repair below would be curing a sentence that
            was never wrong;
  WRITING   Close answered inside the write's own pump, which is the
            claim.
"""
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtCore import QTimer  # noqa: E402
from qgis.PyQt.QtWidgets import QApplication  # noqa: E402
from qgis.PyQt.QtWidgets import QMessageBox  # noqa: E402


def where_the_layers_read_from(dlg, path):
  """Which of the map's element layers now read from this file.

  Args:
    dlg: the dialog whose output layers to ask.
    path: the file the save was aimed at.

  Returns:
    A list of (layer name, reads from the file) pairs. The question is
    asked of the layer's own `source()`, which is what a repointing
    moves and what a reopened project would follow -- so a layer
    reading from the file is a layer the save landed on, whatever the
    file itself holds.
  """
  from qgis.core import QgsProject
  found = []
  for layer_id in dlg._element_layer_ids.values():
    layer = QgsProject.instance().mapLayer(layer_id)
    if layer is None:
      found.append(("<gone>", False))
      continue
    found.append((layer.name(), path in layer.source()))
  return found


def run_one_arm(probe, name, interrupt):
  """Drive one arm and report the sentences and where the layers read.

  Args:
    probe: the probe kit's handle.
    name: the arm's name, which is also its file's name.
    interrupt: "promised" to deliver the close before the write opens
      the file, or "writing" to deliver it from the write's own pump.

  Returns:
    A dict of the sentences said, where each element layer reads from,
    and the two flags read at the moment the close was delivered --
    which is the premise, since the claim is about a question asked on
    `_saving_now` and answered about `_save_pending`.
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

  # THE ANSWER IS THE POINT OF THIS PROBE. The mid-write cancel was
  # measured through the SAVE arm, which reaches the hold; this is
  # the other arm, which is meant to mean "do not save".
  probe.suite.MODAL_ANSWERS["question"] = QMessageBox.StandardButton.Close

  at_the_close = {}
  real_close = dlg.closeEvent

  def watched_close(event):
    """Record what was outstanding at the instant the close arrived.

    Args:
      event: Qt's close event, passed straight through.

    Returns:
      Whatever the real handler returns. The readings are taken BEFORE
      it runs, because the handler is what clears them.
    """
    at_the_close["saving_now"] = bool(getattr(dlg, "_saving_now", False))
    at_the_close["save_pending"] = bool(getattr(dlg, "_save_pending",
                                                False))
    return real_close(event)

  dlg.closeEvent = watched_close

  path = probe.path(f"{name}.gpkg")
  dlg.gpkg_widget.setFilePath(path)

  # DELIVERED AT THE FIRST PUMP INSIDE THE WRITE for the treatment.
  # `_save_the_map` turns the event loop once per element behind its
  # progress bar, so a zero timer armed here fires there -- which is
  # what puts the close's own frame BELOW the write rather than after
  # it. The promised arm arms the same timer before the press, where
  # nothing has opened the file.
  if interrupt == "promised":
    dlg._save_pending = True
    QTimer.singleShot(0, dlg.close)
    for _ in range(40):
      QApplication.processEvents()
  else:
    QTimer.singleShot(0, dlg.close)
    dlg._save_the_map()
    for _ in range(60):
      QApplication.processEvents()

  reads = where_the_layers_read_from(dlg, path)
  dlg.closeEvent = real_close
  return {
    "at the close": at_the_close,
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

  promised = run_one_arm(probe, "promised", "promised")
  print("=== PROMISED: Close answered before anything is written ===")
  for key, value in promised.items():
    print(f"    {key}: {value}")

  writing = run_one_arm(probe, "writing", "writing")
  print("=== WRITING: Close answered inside the write's own pump ===")
  for key, value in writing.items():
    print(f"    {key}: {value}")

  print()
  landed = [name for name, reads in
            writing["layers reading from the file"] if reads]
  said = " ".join(writing["said"]).lower()
  # EITHER SENTENCE MEANS THE PERSON DECLINED, and the probe has to
  # read both or it can only report the world it was written in. Before
  # the repair this arm says "Closed without saving"; after it the
  # WRITER speaks instead, because the rollback is what happened and
  # ours could not have been true past the last table.
  declined = ("closed without saving" in said
              or "the save was stopped" in said)
  if landed and declined:
    print(f"CLAIM REPRODUCES: the person was told the map was not "
          f"saved, and {len(landed)} of "
          f"{len(writing['layers reading from the file'])} element "
          f"layers now read from the file they declined to write")
  elif not landed and declined:
    print("THE CLOSE STOPPED THE SAVE: no layer reads from that file")
  else:
    print(f"INCONCLUSIVE: said={writing['said']}")
  print("both arms reported; teardown next")


if __name__ == "__main__":
  main()
