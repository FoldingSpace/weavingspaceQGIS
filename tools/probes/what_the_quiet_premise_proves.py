"""What "the tab is quiet" proves, and what it does not.

`test_several_classes_can_be_moved_together` stages its ground with

    assert _the_topology_tab_is_quiet(dlg), \
      "PREMISE: no topology was built, so there are no classes to aim at"

and reads `panel._topology` three lines later. The sentence claims a
build HAPPENED FOR THIS DESIGN; the function answers whether anything
is OUTSTANDING, which is a different question and is trivially true
before a build has been queued at all.

WHY THAT IS REACHABLE RATHER THAN THEORETICAL. `_queue_topology` runs
inside `_rebuild_unit`, which fires on the PREVIEW DEBOUNCE -- an
interval that is a FLOOR of `PREVIEW_DEBOUNCE_MS` and widens to
whatever the last rebuild cost, deliberately, so a slower machine or a
costlier design widens it back on its own. The test ticks 300 ms after
choosing its family. Where the floor has widened past that, the rebuild
has not run, nothing is queued, and the tab is quiet by never having
started.

WHAT THE PANEL THEN HOLDS IS THE PREVIOUS DESIGN'S ANSWER, because
ticking the experimental box queues a build DIRECTLY rather than
through the debounce. So there are two harms and they need telling
apart, which is what the three arms below are for:

  control    the interval left alone: the rebuild runs inside the
             tick, the chosen design's build lands, and the premise is
             true AND says something
  stale      the interval widened past the tick, from a design that
             HAS a topology: quiet answers True while the panel holds
             the OTHER design's classes, so the test aims its clicks
             with labels the drawing on screen does not carry
  absent     the same, from a design that has NO topology at all --
             an inset opens gaps and `Topology` needs a gap-free
             tiling. `panel._topology` is None, and
             `topology_edits.classes` raises AttributeError, which is
             the failure a reader actually meets three lines below a
             premise that passed.

Run it with the checkout and `tools/` on the path:

    PYTHONPATH="$PWD:$PWD/tools" PYTHONUNBUFFERED=1 \
      QT_QPA_PLATFORM=offscreen "$QGIS_PY" \
      tools/probes/what_the_quiet_premise_proves.py
"""
import probe_kit


def one_arm(probe, first_design, inset, widen_to):
  """Drive the test's own opening, from one design onto laves.

  Args:
    probe: the kit's handle, holding QGIS and an empty project.
    first_design: the catalogue key to settle on BEFORE the family the
      test wants. This is what the panel is holding when the premise
      is put.
    inset: per cent of the spacing to inset each tile by while
      settling that first design, which is what `mod_t_inset` takes.
      Any inset opens gaps, and `Topology` refuses a design with gaps
      -- which is how the "absent" arm reaches a panel holding None
      rather than a stale answer.
    widen_to: milliseconds to report the last rebuild as having cost,
      or None to leave that reading alone. THE LEVER IS
      `_last_rebuild_ms` RATHER THAN THE TIMER, because `_queue_preview`
      re-derives the interval from it on every change -- setting the
      timer directly is undone by the very next keystroke, measured
      here as an interval of 152 where 4000 had just been asked for.
      `_preview_wait` bounds the answer at `PREVIEW_DEBOUNCE_CEILING_MS`,
      which is 350 against the test's own 300 ms tick, so this stages
      what a rebuild costing a third of a second does on its own.

  Returns:
    A dict of what the arm measured: what the panel held before the
    change, whether the tab reported quiet, whether anything was ever
    queued, and what reading the classes off the panel does -- which
    is the line the test reaches three below its premise.
  """
  from weavingspace_qgis import topology_edits
  from tests.run_tests import _choose_family, _tick            # noqa: PLC0415
  from tests.run_tests import _the_topology_tab_is_quiet       # noqa: PLC0415

  dlg, _layer, _tid = probe.dialog()
  dlg.opt_experimental.setChecked(True)
  dlg.live_check.setChecked(False)
  dlg.show()
  _tick(200)

  # THE DESIGN THE PANEL IS HOLDING WHEN THE PREMISE IS PUT. Settled
  # first, so an arm differs from its control in the debounce alone
  # and not in how much has happened before it.
  _choose_family(dlg, first_design)
  dlg.mod_t_inset.setValue(inset)
  _tick(400)
  _the_topology_tab_is_quiet(dlg, seconds=90.0)
  panel = dlg.topology_panel
  try:
    before = topology_edits.classes(panel._topology)
  except Exception as exc:                                     # noqa: BLE001
    before = type(exc).__name__

  # THE ONE THING THAT DIFFERS BETWEEN AN ARM AND ITS CONTROL.
  if widen_to is not None:
    dlg._last_rebuild_ms = float(widen_to)

  # The test's own opening, verbatim: four elements, laves, 300 ms.
  # `_choose_family` is the product's own door, which is what the
  # suite uses; `setCurrentText` selects nothing in silence.
  dlg.mod_t_inset.setValue(0.0)
  dlg.n_spin.setValue(4)
  _choose_family(dlg, "laves 3.3.4.3.4")
  _tick(300)

  quiet = _the_topology_tab_is_quiet(dlg, seconds=90.0)
  reading = {
    "settled first on": f"{first_design}, inset {inset}",
    "what the panel held then": before,
    "the interval the timer held": dlg._preview_timer.interval(),
    "the timer was still pending": dlg._preview_timer.isActive(),
    "quiet said": quiet,
    "a build was queued": bool(getattr(dlg, "_topology_wanted", False)),
    "a build is in flight": getattr(dlg, "_topology_task", None) is not None,
    "the panel holds a topology": panel._topology is not None,
  }
  try:
    reading["classes read"] = topology_edits.classes(panel._topology)
  except Exception as exc:                                     # noqa: BLE001
    reading["classes read"] = f"{type(exc).__name__}: {exc}"
  return reading


def main():
  """Run three arms in one process and print what each measured."""
  probe = probe_kit.start()
  arms = (("control", "hex-slice 4", 0.0, None),
          ("stale", "hex-slice 4", 0.0, 400),
          ("absent", "hex-slice 4", 2.0, 400))
  for name, first_design, inset, widen_to in arms:
    probe.clear()
    reading = one_arm(probe, first_design, inset, widen_to)
    print(f"---- {name}")
    for key, value in reading.items():
      print(f"     {key}: {value}")
  # A SENTINEL, because an instrument that dies after reporting looks
  # exactly like the thing it measures dying.
  print("---- three arms reported, teardown next")


if __name__ == "__main__":
  main()
