"""Which dataset's CRS does a group's record name?

`WORKING_STATE_EDGES` carries a comment saying `region_crs` "is
carried wherever `region` is carried and asked for nowhere else".
`_stamp_working_state` carries `("design",) + WORKING_STATE_EDGES`,
which is design, output_path and region -- and NOT region_crs, which
therefore falls through to the LIVE reading in
`_capture_working_state`. The switch-out stamp hands over
`launch_state={"region": <the outgoing layer's source>}` precisely
because the chooser already holds the incoming one, so that writer
takes `region` from the dataset being left and `region_crs` from the
dataset being arrived at.

TWO HUNTS REACHED THIS FROM OPPOSITE DIRECTIONS on 2026-09-02 -- one
asking what a Save writes that nothing reads back, one asking which of
three stores wins -- and both read the harm off the FILE. This reads
the GROUP'S OWN RECORD instead, at each step of the journey, because
that is the store where the two halves first disagree and it says
WHICH writer is the wrong one rather than only that the file is wrong.

THE JOURNEY IS THROUGH THE GROUP CHOOSER, which is the control a
person uses to come back to a map, rather than through a bare switch:

  CONTROL  draw on A, save, and read the record. Nothing else happens.
  TREATED  draw on A, save, glance at B in another system through the
           region chooser, come back to A's map through the GROUP
           chooser, and save again.

Run it with BOTH the checkout and this directory's parent on the path:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \\
      | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1
    PYTHONPATH="$PWD:$PWD/tools" "$QGIS_PY" -u \\
      tools/probes/which_crs_the_record_carries.py
"""

import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from probe_kit import start  # noqa: E402

OTHER = "EPSG:2193"          # New Zealand Transverse Mercator, a long
                             # way from the fixture's own EPSG:3857


def a_second_dataset(probe, name):
  """Another region layer, in a system somebody has assigned.

  Args:
    probe: the harness, whose suite supplies the fixture.
    name: what to call the layer, so the two cannot be confused.

  Returns:
    The layer, already added to the project. Its CRS is ASSIGNED
    rather than declared by a file, which is the ordinary act the
    `region_crs` key exists for.
  """
  from qgis.core import QgsCoordinateReferenceSystem
  layer = probe.suite.make_region_layer(origin=(500000, 500000))
  layer.setName(name)
  layer.setCrs(QgsCoordinateReferenceSystem(OTHER))
  probe.project.addMapLayer(layer)
  return layer


def the_groups_record(dlg):
  """What the group this dialog is working in says about its region.

  Args:
    dlg: the dialog to ask.

  Returns:
    (the record's `region`, its `region_crs`), or (None, None) where
    there is no group or no record.
  """
  from qgis.core import QgsProject
  group = dlg._group_of_our_layers(QgsProject.instance().layerTreeRoot())
  record = dlg._read_working_state(group) if group is not None else None
  if not isinstance(record, dict):
    return None, None
  return record.get("region"), record.get("region_crs")


def arm(probe, name, glance_at_another):
  """Drive one arm and print what each store says about the region.

  Args:
    probe: the harness, whose project this clears first.
    name: names the arm and its own file.
    glance_at_another: True to point the region chooser at a second
      dataset in another system and come back through the GROUP
      chooser, which is what a person does to return to a map.

  Returns:
    (the file's `region`, the file's `region_crs`).
  """
  from weavingspace_qgis import bridge
  probe.clear()
  dlg, first, _tid = probe.dialog()
  first.setName("alpha")
  path = probe.path(f"{name}.gpkg")
  try:
    probe.generate(dlg, spacing=700.0)
    assert probe.save(dlg, path), "PREMISE: the first save failed"
    region, crs = the_groups_record(dlg)
    print(f"  {name}:")
    print(f"    after the first save   region={_short(region)} "
          f"crs={crs}")
    assert crs == first.crs().authid(), \
      f"PREMISE: the record already disagrees with alpha ({crs})"

    if glance_at_another:
      other = a_second_dataset(probe, "beta")
      assert other.crs().authid() == OTHER, \
        "PREMISE: the second dataset did not take the assigned system"
      dlg.layer_combo.setLayer(other)
      probe.suite._tick(400)
      region, crs = the_groups_record(dlg)
      print(f"    after the glance       region={_short(region)} "
            f"crs={crs}")
      # ...AND BACK TO THE MAP THROUGH THE GROUP CHOOSER, which is the
      # control a person uses rather than the region chooser.
      chosen = False
      for index in range(dlg.group_combo.count()):
        from weavingspace_qgis.dialog import NEW_GROUP_LABEL
        if dlg.group_combo.itemText(index) != NEW_GROUP_LABEL:
          dlg.group_combo.setCurrentIndex(index)
          dlg.group_combo.activated.emit(index)
          chosen = True
          break
      assert chosen, "PREMISE: the chooser offers no group to come back to"
      probe.suite._tick(400)
      region, crs = the_groups_record(dlg)
      print(f"    after coming back      region={_short(region)} "
            f"crs={crs}")

    assert probe.save(dlg, path), "the second save was refused"
    record = bridge.read_working_state(path) or {}
    in_file = (record.get("region"), record.get("region_crs"))
    print(f"    the FILE says          region={_short(in_file[0])} "
          f"crs={in_file[1]}")
    print(f"    alpha really is        {first.crs().authid()}")
    return in_file
  finally:
    dlg.close()


def _short(source):
  """The tail of a source string, so a line stays readable.

  Args:
    source: a layer source, or None.

  Returns:
    A short string naming the layer.
  """
  if not source:
    return "None"
  text = str(source)
  return text.split("&")[0][-46:]


def main():
  """Drive both arms in one process and print the verdicts.

  Returns:
    None. It prints a sentinel once both arms have reported and the
    teardown is over, because an instrument that dies after reporting
    looks exactly like the thing it measures dying.
  """
  probe = start()
  print("WHICH CRS THE RECORD CARRIES")
  control = arm(probe, "control", glance_at_another=False)
  treated = arm(probe, "treated", glance_at_another=True)
  print()
  for label, (region, crs) in (("control", control),
                               ("treated", treated)):
    verdict = "agree" if crs == "EPSG:3857" else "DISAGREE"
    print(f"  {label}: the file's region is alpha's and its crs is "
          f"{crs} -> {verdict}")
  print("BOTH ARMS REPORTED, teardown complete.")


main()
