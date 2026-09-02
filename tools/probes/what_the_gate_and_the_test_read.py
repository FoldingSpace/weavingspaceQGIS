"""Does the symmetry gate read the SAME topology the test's oracle does?

CI failed `the symmetries are drawn and gate what cannot move` on the
Linux 4.0.3 leg with "class B has 1 free direction(s) and its push is
greyed", while the same test passed on stable, on macOS and here. The
product and the test call ONE function -- `directions_a_class_may_move`
-- so a disagreement cannot come from the arithmetic; it can only come
from the two readings being about DIFFERENT OBJECTS. This measures
whether `panel._topology` moves under the test between the moment the
verdict is taken and the moment the oracle is computed.

It drives the dialog exactly as the test does, including the same
waiter, and prints the identity of the topology at every step.
"""
import sys
import time

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from weavingspace_qgis import topology_edits  # noqa: E402


def tick(app, ms):
  """Pump the event loop for roughly ms milliseconds.

  Args:
    app: the QgsApplication whose events to process.
    ms: how long to keep pumping, in milliseconds. It is a floor
      rather than a budget: a build landing inside the window will
      take as long as it takes.

  Returns:
    None.
  """
  end = time.monotonic() + ms / 1000.0
  while time.monotonic() < end:
    app.processEvents()
    time.sleep(0.005)


def wait_for_the_topology(dlg, app, seconds=40.0):
  """The suite's own waiter, copied so this measures what it measures.

  Args:
    dlg: the dialog whose Topology tab to wait on.
    app: the QgsApplication, since a probe pumps the loop itself.
    seconds: a ceiling that catches a hang rather than budgeting the
      work, sized well above the slowest build measured here.

  Returns:
    True where the panel holds a topology or has said why it holds
    none, False where neither ever happened.

  It returns as soon as the panel holds an ANSWER -- which the suite's
  own docstring for the OTHER waiter says may be the previous
  design's. That sentence is the hypothesis under test.
  """
  deadline = time.monotonic() + seconds
  while time.monotonic() < deadline:
    panel = getattr(dlg, "topology_panel", None)
    if panel is None:
      return False
    if panel._topology is not None:
      return True
    if (panel.note.text() or "").strip():
      return True
    tick(app, 200)
  return False


def picture(dlg):
  """What the panel holds right now, as a printable line."""
  panel = dlg.topology_panel
  topology = panel._topology
  if topology is None:
    return "topology=None"
  labels = topology_edits.classes(topology).get("vertex", "")
  free = {
    label: topology_edits.directions_a_class_may_move(
      topology, "vertex", label)
    for label in labels}
  return (f"topology=0x{id(topology):x} vertex={labels!r} free={free} "
          f"task={getattr(dlg, '_topology_task', None) is not None} "
          f"wanted={bool(getattr(dlg, '_topology_wanted', False))}")


def main():
  """Drive both arms and print what each reading was about.

  Returns:
    None; everything is printed. The CONTROL arm is the test's own
    sequence with the tab settled, where the two readings agree; the
    STAGED arm changes the design and reads before the new build
    lands, which is the condition a loaded runner supplies for itself.
    The last line is a sentinel, so a run that died at teardown is
    distinguishable from one that stopped early.
  """
  probe = probe_kit.start()
  app = probe.suite.QgsApplication.instance()
  dlg, _layer, _tile_id = probe.dialog()
  dlg.opt_experimental.setChecked(True)
  dlg.live_check.setChecked(False)
  dlg.show()
  tick(app, 200)

  print("=== the test's own sequence ===")
  dlg.n_spin.setValue(4)
  tick(app, 200)
  print(f"  after n=4            {picture(dlg)}")
  probe.suite._choose_family(dlg, "laves 3.3.4.3.4")
  tick(app, 300)
  print(f"  after family chosen  {picture(dlg)}")

  arrived = wait_for_the_topology(dlg, app)
  print(f"  waiter returned {arrived}")
  print(f"  AT VERDICT TIME      {picture(dlg)}")

  panel = dlg.topology_panel
  verdicts = {}
  seen_at_verdict = {}
  for label in topology_edits.classes(panel._topology).get("vertex", ""):
    panel._select_classes("vertex", label)
    tick(app, 100)
    index = panel.how_combo.findData("push_vertex")
    item = panel.how_combo.model().item(index)
    verdicts[label] = item.isEnabled()
    # WHAT THE GATE ITSELF WAS LOOKING AT, in the same breath as the
    # verdict, which is the reading the test takes later and separately.
    seen_at_verdict[label] = (
      id(panel._topology),
      topology_edits.directions_a_class_may_move(
        panel._topology, "vertex", label))
  print(f"  verdicts             {verdicts}")
  print(f"  free at verdict      {seen_at_verdict}")

  # ---- now let everything settle, and ask again.
  for _ in range(200):
    if (getattr(dlg, "_topology_task", None) is None
        and not getattr(dlg, "_topology_wanted", False)):
      break
    tick(app, 200)
  tick(app, 500)
  print(f"  AFTER QUIET          {picture(dlg)}")

  free_after = {
    label: topology_edits.directions_a_class_may_move(
      panel._topology, "vertex", label)
    for label in verdicts}
  print(f"  free at assert time  {free_after}")

  print()
  disagreed = [
    label for label, enabled in verdicts.items()
    if enabled != (free_after[label] > 0)]
  print(f"THE TEST'S ASSERTION would fail for: {disagreed or 'nothing'}")
  moved = [label for label in verdicts
           if seen_at_verdict[label][1] != free_after[label]]
  print(f"CLASSES WHOSE FREEDOM CHANGED between the two readings: "
        f"{moved or 'none'}")
  print(f"TOPOLOGY IDENTITY at verdict "
        f"{set(v[0] for v in seen_at_verdict.values())} against "
        f"0x{id(panel._topology):x} at assert time")

  # ---- STAGED: the condition a slower runner supplies for itself.
  # `_wait_for_the_topology` returns as soon as the panel holds an
  # ANSWER, and an answer left over from the PREVIOUS design is an
  # answer. So put a topology in the panel, change the design, and
  # take the verdicts before the new build lands -- which is what a
  # loaded Linux runner does without being asked.
  print()
  print("=== STAGED: verdicts taken while the new build is still coming ===")
  before = id(panel._topology)
  dlg.n_spin.setValue(2)
  tick(app, 50)
  probe.suite._choose_family(dlg, "archimedean 4.8.8")
  tick(app, 50)
  print(f"  right after the switch {picture(dlg)}")
  staged_verdicts = {}
  together = {}
  for label in "AB":
    panel._select_classes("vertex", label)
    tick(app, 20)
    index = panel.how_combo.findData("push_vertex")
    if index < 0:
      continue
    item = panel.how_combo.model().item(index)
    staged_verdicts[label] = item.isEnabled()
    # THE REPAIRED DISCIPLINE: the oracle read in the same breath as
    # the verdict, from the topology the gate itself just consulted.
    together[label] = topology_edits.directions_a_class_may_move(
      panel._topology, "vertex", label)
  held_at = id(panel._topology)
  print(f"  verdicts on the design in hand {staged_verdicts}")

  for _ in range(300):
    if (getattr(dlg, "_topology_task", None) is None
        and not getattr(dlg, "_topology_wanted", False)
        and id(panel._topology) != held_at):
      break
    tick(app, 200)
  tick(app, 500)
  print(f"  after the new build landed {picture(dlg)}")
  staged_free = {
    label: topology_edits.directions_a_class_may_move(
      panel._topology, "vertex", label)
    for label in staged_verdicts}
  staged_bad = [label for label, enabled in staged_verdicts.items()
                if enabled != (staged_free[label] > 0)]
  print(f"  free at assert time {staged_free}")
  print(f"  TOPOLOGY MOVED: 0x{before:x} -> 0x{held_at:x} -> "
        f"0x{id(panel._topology):x}")
  print(f"  SPLIT READING (what CI met) fails for: {staged_bad or 'nothing'}")
  same_breath_bad = [label for label, enabled in staged_verdicts.items()
                     if enabled != (together[label] > 0)]
  print(f"  free in the same breath {together}")
  print(f"  SAME-BREATH READING (the repair) fails for: "
        f"{same_breath_bad or 'nothing'}")

  probe.clear()
  print("both arms reported; teardown next")


if __name__ == "__main__":
  main()
