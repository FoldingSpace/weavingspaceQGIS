"""Whose file does a PROMISED save write to, if you open a map while it waits?

The asymmetry hunt of round seven reported that `_save_the_map` refuses
a press while a queued run would redraw, and `_resume_from_gpkg` refuses
only while a TILING is in flight -- never while a save stands promised.
The resume then repoints `gpkg_widget`, and that is the widget
`_honour_a_queued_save` deliberately re-reads at the moment of the
write: "the press asked to save THIS MAP, and where it goes is whatever
the chooser says at the moment of the write."

So the question this asks is not whether the mechanism exists -- it is
plainly there in both methods -- but WHAT IT COSTS: is the person's own
map written late, or not at all, and what are they told.

THIS IS THE VERIFICATION AND IT DIFFERS FROM THE HUNT'S TWO ROUTES.
The hunt counted tiles with bare sqlite3, then read each file's own
working-state record and mtime. This one stages the deferral through
the LIVE REDRAW door rather than a topology build -- a different kind
of promise, which is the half of the mechanism the hunt did not vary --
and takes its verdict from the DESIGN each file's record names, which
says which map is in it rather than how many rows it has.

    unset PYTHONHOME PROJ_LIB QGIS_PREFIX_PATH
    set -a; eval "$(bash tools/macos_qgis_env.sh)"; set +a
    QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1 \\
      PYTHONPATH="$PWD:$PWD/tools" "$QGIS_PY" -u \\
      tools/probes/where_a_promised_save_lands_after_a_load.py
"""
import probe_kit


def spacing_in(path):
  """What the file's own record says the map was drawn at.

  Args:
    path: a saved GeoPackage.

  Returns:
    The spacing in its working-state record, or None where the file
    holds no record of ours.
  """
  from weavingspace_qgis import bridge
  record = bridge.read_working_state(path) or {}
  design = record.get("design") or {}
  return design.get("spacing")


def one_arm(probe, name, open_the_other_map):
  """Promise a save, optionally open somebody else's map, and read both.

  Args:
    probe: the `probe_kit.Probe` holding QGIS, the project and the
      temporary directory this arm writes into.
    name: names the arm and its files.
    open_the_other_map: True to press Load on a second map inside the
      window where our own save stands promised.

  Returns:
    A dict of what each file's record says afterwards, and what the
    plugin said.
  """
  from qgis.core import QgsProject
  suite = probe.suite
  probe.clear()

  # ---- SOMEBODY ELSE'S MAP, saved from its own dialog and left alone.
  theirs = probe.path(f"{name}-theirs.gpkg")
  dlg, _layer, _tid = probe.dialog()
  probe.generate(dlg, spacing=900.0)
  assert probe.save(dlg, theirs), "PREMISE: the other map was never saved"
  dlg.close()
  suite._tick(200)
  probe.clear()

  # ---- OUR OWN MAP, saved once so the file exists to compare against.
  mine = probe.path(f"{name}-mine.gpkg")
  dlg, _layer, _tid = probe.dialog()
  probe.generate(dlg, spacing=700.0)
  assert probe.save(dlg, mine), "PREMISE: our own map was never saved"
  first = spacing_in(mine)
  assert first == 700.0, f"PREMISE: the file says {first!r} rather than 700"

  # ---- THE PROMISE. Live update on, the design changed, so a re-tile
  # is COMING and a press inside that window is kept rather than
  # refused (the maintainer's ruling of 2026-08-29).
  dlg.live_check.setChecked(True)
  dlg.spacing_spin.setValue(520.0)
  suite._tick(50)
  dlg.save_button.click()
  suite._tick(50)
  promised = bool(getattr(dlg, "_save_pending", False))

  said_at_the_press = probe.said(dlg)
  if open_the_other_map and promised:
    dlg.resume_widget.setFilePath(theirs)
    dlg.load_button.click()
    suite._settle(dlg)
  suite._tick(1200)
  suite._settle(dlg)
  suite._tick(600)

  result = {"promised": promised,
            "mine": spacing_in(mine), "theirs": spacing_in(theirs),
            "still_owed": bool(getattr(dlg, "_save_pending", False)),
            "said": probe.said(dlg)[len(said_at_the_press):].strip()}
  dlg.close()
  suite._tick(200)
  return result


def main():
  """Both arms in one run, control first."""
  probe = probe_kit.start()
  for name, load in (("control", False), ("treated", True)):
    row = one_arm(probe, name, load)
    print(f"{name:8s} promised={row['promised']}  "
          f"mine's record={row['mine']}  theirs={row['theirs']}  "
          f"still owed={row['still_owed']}")
  print()
  print("A promised save is about the map that was on screen when the "
        "button was pressed; 520 in MINE is that promise kept, 700 is "
        "the promise lost, and 520 in THEIRS is it landing on the "
        "wrong file.")
  print("\nPROBE COMPLETE: both arms reported, teardown next.")


main()
