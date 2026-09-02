"""Whose coordinate system does a resume stamp, at EACH of the two doors?

Two hunts of round seven reported the same mechanism from opposite
directions on 2026-09-02: `_resume_from_gpkg`'s two stamps hand
`_stamp_working_state` a launch state of `region` and `output_path`
alone, so `region_crs` falls through to `_capture_working_state`'s
LIVE reading of whatever layer the region chooser happens to hold.
Where the recovery lands on nothing -- a colleague's file, a region
that has moved, a map drawn from data this machine never had -- the
record then names one dataset's region beside another dataset's
system, and `_wear_the_recorded_crs` FORCES that system onto a region
which declares its own correctly.

THIS IS THE VERIFICATION RATHER THAN THE CLAIM, and it differs from
both hunts deliberately, because a route that repeats theirs measures
their instrument as much as the product:

  - NOTHING IS MOVED ON DISK. The region is a MEMORY layer, so a
    later session cannot answer to its source however the filesystem
    is arranged: the failed recovery is staged by the ordinary fact
    that memory does not survive a session, not by renaming a file.
  - THE RECORD IS READ THROUGH THE PLUGIN'S OWN READER,
    `bridge.read_working_state`. One hunt read raw GDAL metadata and
    the other went to `gpkg_metadata` with sqlite3, both deliberately
    around the plugin; asking the reader every other consumer asks is
    the other half of that question.
  - THE STRANGER IS EPSG:27700, which is neither hunt's primary arm,
    so a record that follows it is reading the chooser rather than
    defaulting to anything.
  - AND BOTH DOORS ARE DRIVEN. Neither hunt drove the already-open
    branch, and this project's own rule is that a fix applied to a
    twin which does not have the fault is dead code reading as
    protection. The two branches differ in one way that bears
    directly on this: the already-open door finds a group that
    already carries a record, and `_stamp_working_state` CARRIES
    `region_crs` from an existing record in preference to the live
    reading. So the twin may be held by the carry -- which decides
    whether the repair belongs at one site or at two.

Run it with QGIS's own interpreter, from the checkout::

    unset PYTHONHOME PROJ_LIB QGIS_PREFIX_PATH
    set -a; eval "$(bash tools/macos_qgis_env.sh)"; set +a
    QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1 \\
      PYTHONPATH="$PWD:$PWD/tools" "$QGIS_PY" -u \\
      tools/probes/whose_crs_a_resume_writes_at_both_doors.py

It prints a completion sentinel, because a probe that dies at
interpreter teardown looks exactly like the product failing.
"""
import probe_kit

REGION = "EPSG:3857"      # what the map's own region declares
STRANGER = "EPSG:27700"   # an unrelated layer, in another system


def one_arm(probe, name, keep_the_region, keep_the_layers,
            the_file_says="as saved"):
  """Draw a map, come back to it later, and read what the file says.

  Args:
    probe: the `probe_kit.Probe` holding QGIS, the project and the
      temporary directory this arm writes into.
    name: names the arm and its own file.
    keep_the_region: True to leave the region layer in the project for
      the second session, so the recovery SUCCEEDS. False removes it,
      which is the colleague's-file case: nothing answers to the
      recorded source.
    keep_the_layers: True to leave the map's own element layers in the
      project, which is what makes `_resume_from_gpkg` take its
      ALREADY-OPEN branch; False removes them, so the fresh branch
      runs.
    the_file_says: what the FILE's own record carries when the resume
      reads it -- "as saved", "nothing" for a file written before
      `region_crs` existed, or an authid for a file written while the
      key was being filled in wrongly, which is every file this
      project saved between 2026-08-28 and the repairs of 2026-09-02.
      The group's own record is left alone, so this is the question
      of which of TWO stores the stamp should believe.

  Returns:
    A dict of what was measured: the file's `region_crs` as the first
    save left it and as the second save left it, the chooser at the
    moment of that second save, and which door ran.
  """
  from qgis.core import QgsProject, QgsCoordinateReferenceSystem
  from weavingspace_qgis import bridge
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  suite = probe.suite
  probe.clear()

  alpha = suite.make_region_layer()
  alpha.setName("alpha")
  alpha.setCrs(QgsCoordinateReferenceSystem(REGION))
  QgsProject.instance().addMapLayer(alpha)

  dlg = WeavingSpaceDialog(iface=suite._Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(alpha)
  suite._tick(300)
  # THE COPY IS OFF, or the recovery lands on the region inside the
  # file and the failed-recovery case cannot arise at all.
  dlg.opt_embed_source.setChecked(False)
  probe.generate(dlg, spacing=700.0)
  path = probe.path(f"{name}.gpkg")
  assert probe.save(dlg, path), f"PREMISE: {name} was never saved"
  first = (bridge.read_working_state(path) or {}).get("region_crs")
  assert first == REGION, (
    f"PREMISE: the file left the first save saying {first!r} rather "
    f"than {REGION}, so this arm cannot say whose system travelled")

  # ---- WHAT THE FILE SAYS WHEN THE RESUME READS IT. The group's own
  # record is untouched, so an arm that changes this is asking which
  # of the two stores the stamp believes.
  if the_file_says != "as saved":
    older = dict(bridge.read_working_state(path) or {})
    if the_file_says == "nothing":
      older.pop("region_crs", None)
    else:
      older["region_crs"] = the_file_says
    assert bridge.write_working_state(path, older), \
      "PREMISE: the file's record could not be staged"

  # ---- A LATER SESSION. The dialog is closed; what stays in the
  # project is the arm's own question.
  layer_ids = list(dlg._element_layer_ids.values())
  dlg.close()
  suite._tick(200)
  if not keep_the_layers:
    for layer_id in layer_ids:
      QgsProject.instance().removeMapLayer(layer_id)
  if not keep_the_region:
    QgsProject.instance().removeMapLayer(alpha.id())
  stranger = suite.make_region_layer(origin=(500000, 200000))
  stranger.setName("somebody else's basemap")
  stranger.setCrs(QgsCoordinateReferenceSystem(STRANGER))
  QgsProject.instance().addMapLayer(stranger)
  assert stranger.crs().authid() == STRANGER, \
    "PREMISE: the stranger did not take the system it was assigned"
  suite._tick(300)

  dlg = WeavingSpaceDialog(iface=suite._Iface())
  dlg.live_check.setChecked(False)
  suite._tick(200)
  # WHICH DOOR IS ABOUT TO RUN, asked the way the product asks it:
  # a group holding a layer whose source names this file.
  root = QgsProject.instance().layerTreeRoot()
  door = "fresh"
  for node in root.findGroups():
    for child in node.children():
      layer = getattr(child, "layer", lambda: None)()
      source = layer.source() if layer is not None else ""
      if source and source.split("|")[0].endswith(f"{name}.gpkg"):
        door = "already-open"
        break
    if door == "already-open":
      break

  dlg.resume_widget.setFilePath(path)
  dlg.load_button.click()
  suite._settle(dlg)
  suite._tick(400)
  chosen = dlg.layer_combo.currentLayer()
  chooser = (f"{chosen.name()} {chosen.crs().authid()}"
             if chosen is not None else "nothing")

  # ---- THE PRESS A PERSON MAKES NEXT: they have the map, so they
  # save it. This is the act that writes the record into the file.
  probe.save(dlg, path)
  suite._tick(300)
  second = (bridge.read_working_state(path) or {}).get("region_crs")
  region = (bridge.read_working_state(path) or {}).get("region")
  dlg.close()
  suite._tick(200)
  return {"door": door, "chooser": chooser, "first": first,
          "second": second, "region_is_alphas": "memory" in str(region)}


def main():
  """Drive the three arms and print what each door wrote.

  Returns:
    None. Prints one line per arm and a completion sentinel, so a run
    that died at teardown is distinguishable from one that finished.
  """
  probe = probe_kit.start()
  arms = (
    ("control-fresh", True, False, "as saved"),
    ("treated-fresh", False, False, "as saved"),
    ("treated-already-open", False, True, "as saved"),
    # ---- AND THE TWO STORES, ASKED AT THE DOOR THAT HAS BOTH. The
    # group's record is this map's own landing; the file's may be
    # older than `region_crs` or may carry the value the defect of
    # rows 16 and 22 wrote. A stamp that prefers the file over the
    # group destroys a good record with a bad one.
    ("older-file-already-open", False, True, "nothing"),
    ("wrong-file-already-open", False, True, STRANGER),
  )
  results = {}
  for name, keep_the_region, keep_the_layers, the_file_says in arms:
    results[name] = one_arm(probe, name, keep_the_region, keep_the_layers,
                            the_file_says)
    row = results[name]
    print(f"{name:22s} door={row['door']:12s} "
          f"chooser={row['chooser']:34s} "
          f"file: {row['first']} -> {row['second']}  "
          f"region still alpha's: {row['region_is_alphas']}")
  print()
  for name, row in results.items():
    verdict = ("as drawn" if row["second"] == REGION
               else f"THE CHOOSER'S ({row['second']})")
    print(f"{name:22s} the file's region_crs is {verdict}")
  print("\nPROBE COMPLETE: five arms reported, teardown next.")


main()
