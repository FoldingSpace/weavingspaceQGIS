"""Which controls stay live while a save is writing, and what one costs.

MAINTAINING.md says of the save's pump: "Turning the event loop is
exactly what would otherwise let somebody press Save or Generate into
a half-written file, so both controls go down for the duration." Two
controls. The interface has a THIRD button on that row -- Load, added
2026-08-27 -- and `_resume_from_gpkg` guards `self._task is not None`
and nothing about a save.

TWO QUESTIONS, ASKED SEPARATELY, because this project has already
paid for measuring a mechanism and assuming its reachability:

  FIRST, WHICH CONTROLS ARE LIVE. Every beat of the write is sampled
  for what a person could actually press. That is a question about the
  interface and needs no defect to be interesting.

  THEN, WHAT ONE COSTS. A Load is driven from inside the pump at a
  LATE beat rather than the first -- a different seam from the hunt's
  -- and the file is read through OGR, with each element layer asked
  what it now reads from.

The control arm is the same save with nothing pressed, so a difference
is the press rather than the journey.

Run it with BOTH the checkout and this directory's parent on the path:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \\
      | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1
    PYTHONPATH="$PWD:$PWD/tools" "$QGIS_PY" -u \\
      tools/probes/which_controls_are_live_while_writing.py
"""

import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from probe_kit import start  # noqa: E402

WATCHED = ("save_button", "load_button", "generate_btn")


def sample_the_controls(dlg, beats):
  """Record which watched controls are live, once per call.

  Args:
    dlg: the dialog being driven.
    beats: a list to append this reading to.

  Returns:
    None.
  """
  beats.append({name: getattr(dlg, name).isEnabled()
                for name in WATCHED
                if getattr(dlg, name, None) is not None})


def arm(probe, name, press_load_at):
  """Save a map, optionally pressing Load from inside the write's pump.

  Args:
    probe: the harness, whose project this clears first.
    name: names the arm and its own files.
    press_load_at: the beat at which to press Load -- a number, or
      None for the control. Counted from one, so a late beat is a
      different seam from the hunt's first-pump click.

  Returns:
    (the beats sampled, what the file holds, where each element layer
    reads from, what the record says).
  """
  from weavingspace_qgis import bridge
  probe.clear()
  dlg, _layer, _tid = probe.dialog()
  other = probe.path(f"{name}-other.gpkg")
  mine = probe.path(f"{name}-mine.gpkg")
  beats = []
  try:
    # ---- A FIRST MAP, SAVED SOMEWHERE ELSE, so there is a map to
    # open. It is drawn at a different spacing so the two are
    # distinguishable by tile count alone.
    probe.generate(dlg, spacing=600.0)
    assert probe.save(dlg, other), "PREMISE: the other map did not save"
    # ---- THEN THE MAP IN FRONT OF THEM, going to its own file.
    probe.generate(dlg, spacing=1200.0)
    assert probe.save(dlg, mine), "PREMISE: the first save of mine failed"

    # ---- AND THE PRESS THAT IS THE SUBJECT, delivered by the write's
    # OWN pump: the writer is wrapped, so what is sampled is what the
    # product was doing at that moment rather than what a timer
    # happened to catch.
    # THE SEAM IS THE PROGRESS BAR'S OWN BEAT, which the loop moves
    # once per element at the TOP of its body, immediately before the
    # `processEvents` that makes a click deliverable. `write_gpkg_
    # layers` is one call now -- the single OGR session of
    # 2026-09-01 -- so wrapping THAT would sample once and say nothing
    # about the rest of the act.
    real_set = dlg.progress.setValue
    state = {"beat": 0}

    def watched_beat(value):
      """Sample the controls at each element's beat, then press."""
      state["beat"] += 1
      sample_the_controls(dlg, beats)
      out = real_set(value)
      if press_load_at is not None and state["beat"] == press_load_at:
        dlg.resume_widget.setFilePath(other)
        dlg.load_button.click()
      return out

    dlg.progress.setValue = watched_beat
    try:
      dlg.gpkg_widget.setFilePath(mine)
      probe.suite.press_save(dlg, mine)
    except AssertionError as refused:
      print(f"    the second save reported: {str(refused)[:110]}")
    finally:
      dlg.progress.setValue = real_set

    record = bridge.read_working_state(mine) or {}
    reads = sorted({
      (probe.project.mapLayer(lid).source().split("layername=")[-1]
       if probe.project.mapLayer(lid) is not None else "gone")
      for lid in dlg._element_layer_ids.values()})
    return beats, sorted(probe.tables(mine)), reads, record
  finally:
    dlg.close()


def main():
  """Drive both arms in one process and print the verdicts.

  Returns:
    None. It prints a sentinel once both arms have reported and the
    teardown is over, because an instrument that dies after reporting
    looks exactly like the thing it measures dying.
  """
  probe = start()
  print("WHICH CONTROLS ARE LIVE WHILE A SAVE IS WRITING")
  beats, tables, reads, record = arm(probe, "control", press_load_at=None)
  print("  control:")
  for index, beat in enumerate(beats, 1):
    print(f"    beat {index}: {beat}")
  print(f"    tables      : {tables}")
  print(f"    layers read : {reads}")
  print(f"    record says : path={str(record.get('output_path'))[-24:]!r} "
        f"spacing={(record.get('design') or {}).get('spacing_spin')}")

  beats2, tables2, reads2, record2 = arm(probe, "loaded", press_load_at=2)
  print("  a Load pressed at the second table:")
  print(f"    tables      : {tables2}")
  print(f"    layers read : {reads2}")
  print(f"    record says : path={str(record2.get('output_path'))[-24:]!r} "
        f"spacing={(record2.get('design') or {}).get('spacing_spin')}")
  live = [name for name, on in (beats[0] if beats else {}).items() if on]
  print()
  print(f"  live during the write: {live}")
  print("BOTH ARMS REPORTED, teardown complete.")


main()
