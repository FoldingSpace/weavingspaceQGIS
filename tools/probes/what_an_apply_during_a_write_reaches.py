"""Do the OTHER acting controls reach a record captured after the write?

Taking the Load button down closed the door the claim named. The
enumeration beside it found more buttons live during a write: the
Topology tab's Apply, Undo and Clear, and Auto. The record
`_save_the_map` writes is captured AFTER the element loop, so the
question is whether any of them reaches it.

  CONTROL  a plain second save, nothing pressed.
  APPLY    a topology Apply delivered by the write's own pump.
  AUTO     the Auto spacing button, likewise.

Read afterwards: the file's own record, and its tables.
"""
import sys
import probe_kit
sys.path.insert(0, probe_kit._repo_root())
from probe_kit import start  # noqa: E402


def arm(probe, name, press):
  """Save twice, pressing one acting control from inside the pump.

  Args:
    probe: the harness, whose project each arm clears first.
    name: names the arm and its own file.
    press: None for the control, "apply" for a topology Apply, or
      "spacing" for a design change typed into the spacing box. Both
      are delivered at the second element's beat, immediately before
      the `processEvents` that makes a click deliverable, and staged
      synchronously rather than from a timer -- which would measure
      how fast the machine is.

  Returns:
    The file's own working-state record, read back after the save.
  """
  from weavingspace_qgis import bridge
  s = probe.suite
  probe.clear()
  dlg, _layer, _tid = probe.dialog()
  path = probe.path(f"{name}.gpkg")
  try:
    dlg.opt_experimental.setChecked(True)
    dlg.show(); s._tick(200)
    s._choose_family(dlg, "laves 3.3.4.3.4"); s._tick(300)
    assert s._the_topology_tab_is_quiet(dlg), "PREMISE: no topology built"
    probe.generate(dlg, spacing=700.0)
    assert probe.save(dlg, path), "PREMISE: the first save failed"
    panel = dlg.topology_panel
    # aim an edge manipulation, ready to fire from inside the pump
    for i in range(panel.class_combo.count()):
      panel.class_combo.setCurrentIndex(i); s._tick(60)
      done = False
      for h in range(panel.how_combo.count()):
        if str(panel.how_combo.itemData(h)) in ("zigzag_edge",
                                                "rotate_edge"):
          panel.how_combo.setCurrentIndex(h); s._tick(60); done = True
          break
      if done:
        break

    real_set = dlg.progress.setValue
    state = {"beat": 0}
    def watched(value):
      """Press the arm's control at the second element's beat."""
      state["beat"] += 1
      out = real_set(value)
      if state["beat"] == 2 and press == "apply":
        panel.apply_button.click()
      if state["beat"] == 2 and press == "spacing":
        # THE AUTO BUTTON IS A LOCAL, so the spacing box is driven
        # instead -- the same design change by the control a person
        # types into rather than the one that computes for them.
        dlg.spacing_spin.setValue(1300.0)
      return out
    dlg.progress.setValue = watched
    try:
      s.press_save(dlg, path)
    except AssertionError as refused:
      print(f"    the save reported: {str(refused)[:90]}")
    finally:
      dlg.progress.setValue = real_set
    s._tick(400)
    record = bridge.read_working_state(path) or {}
    design = record.get("design") or {}
    assert design, ("PREMISE: the file's record carries no design at "
                    "all, so a comparison of its terms says nothing")
    print(f"  {name}: design keys={sorted(design)[:4]} "
          f"spacing={design.get('spacing')} "
          f"family={design.get('family_combo')} "
          f"edits={len(record.get('topology_edits') or [])} "
          f"motif={'weavingspace_unit_no_crs' in bridge.gpkg_tables(path)} "
          f"panel_edits={len(panel.edits())}")
    return record
  finally:
    dlg.close()


probe = start()
print("WHAT AN ACTING CONTROL PRESSED DURING A WRITE REACHES")
arm(probe, "control", press=None)
arm(probe, "apply", press="apply")
arm(probe, "spacing", press="spacing")
print("ALL THREE ARMS REPORTED, teardown complete.")
