"""An element's opacity, when the project is OPENED and not the dialog.

Measured at 5b9d385. Confirmed.

`_adopt_category_colours` recovers a layer's opacity into
`_opacity_choices` (dialog.py:4436), and it is reached through
`_adopt_existing_group` by TWO doors. The constructor's door runs BEFORE
`_build_ui`, so there is no table and no Opacity cell, and `_sync_row`
builds one from the recovered number. `_on_project_read`'s door runs with
the table already built -- its own comment says "Here the widget DOES
exist" -- and `_sync_row` only ever MAKES that cell:

    if row_id and self._row_opacity(row) is None:      # dialog.py:3907
      self.table.setCellWidget(row, 6, self._make_opacity_spin(
        row_id, self._opacity_choices.get(row_id, 100)))

`setRowCount` does not clear cell widgets and nothing else does either, so
the surviving spin keeps the number it had; `_refresh_table` then writes
the record back FROM that spin (dialog.py:4324), and `_assignments` reads
the spin (dialog.py:7023). The recovered number is therefore write-only on
that door, and the next Generate paints the dialog's number onto the map.

The RAMP is the control: the same adoption call recovers it and it comes
back correctly, so the door works and only the Opacity cell cannot hear
it. The second route is the .qgz bytes, read with zipfile and a regex --
no QGIS, no dialog.

    python3 tools/hunt_probe.py --prepare --name opacity-door
    python3 tools/hunt_probe.py --name opacity-door \
        --run tools/probes/opacity_lost_when_a_project_opens.py
"""

import importlib.util
import os
import re
import shutil
import sys
import tempfile
import zipfile

REPO = os.environ.get("WEAVINGSPACE_REPO") or os.getcwd()
os.chdir(REPO)
sys.path.insert(0, REPO)

spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer,   # noqa
                       QgsVectorFileWriter)

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()

from weavingspace_qgis.dialog import WeavingSpaceDialog              # noqa


def in_the_file(path, tid):
  """Element `tid`'s opacity as the saved project FILE holds it.

  Args:
    path: a .qgz written by QgsProject.write.
    tid: the element id, e.g. "a".

  Returns:
    A list of "<layer name>=<opacity>" strings, one per element layer
    carrying that id, or a note saying the file holds no such layer.
    Read straight out of the zip so the answer owes nothing to QGIS or
    to the dialog -- the paired no-data layer is skipped, since it
    carries its element's id too.
  """
  with zipfile.ZipFile(path) as archive:
    name = [n for n in archive.namelist() if n.endswith(".qgs")][0]
    text = archive.read(name).decode("utf-8", "replace")
  out = []
  for chunk in text.split("<maplayer")[1:]:
    body = chunk.split("</maplayer>")[0]
    if "weavingspace_tile_id" not in body \
        or f'"{tid}"' not in body or "weavingspace_no_data" in body:
      continue
    found = re.search(r"<layerOpacity>([\d.]+)</layerOpacity>", body) \
        or re.search(r'opacity="([\d.]+)"', body)
    layer = re.search(r'name="(tiles_[a-z]+[^"]*)"', body)
    out.append(f"{layer.group(1) if layer else '?'}="
               f"{found.group(1) if found else 'not stated'}")
  return out or "no such layer in the file"


def region_on_disk(folder, name):
  """A region layer as a FILE, so a reopened project can find it.

  Args:
    folder: a temporary directory to write into.
    name: the GeoPackage's file name.

  Returns:
    The layer, already added to the project. Memory layers do not
    survive a .qgz, which is the whole reason this exists.
  """
  path = os.path.join(folder, name)
  options = QgsVectorFileWriter.SaveVectorOptions()
  options.driverName = "GPKG"
  options.layerName = "region"
  QgsVectorFileWriter.writeAsVectorFormatV3(
    T._editable_region(), path, QgsProject.instance().transformContext(),
    options)
  layer = QgsVectorLayer(f"{path}|layername=region", "region", "ogr")
  assert layer.isValid(), "the region did not survive being written"
  QgsProject.instance().addMapLayer(layer)
  return layer


def run(dlg):
  """Press Generate and wait for the run to land.

  Args:
    dlg: the dialog.

  Returns:
    None. Raises through an assert if the run never settles.
  """
  dlg._generate()
  assert T._settle(dlg, seconds=90), "the run never settled"
  T._tick(300)


def seen(dlg, tid):
  """What the USER sees in that element's row.

  Args:
    dlg: the dialog.
    tid: the element id.

  Returns:
    (opacity percent, ramp name) read off the cell widgets -- the same
    opacity value `_assignments` reads and pushes onto the layer.
  """
  row = dlg._row_for_element(tid)
  return (dlg.table.cellWidget(row, 6).value(),
          dlg.table.cellWidget(row, 4).currentText())


def drawn(tid):
  """What the MAP draws, asked of the project rather than the dialog.

  Args:
    tid: the element id.

  Returns:
    The element layer's own opacity as a percent, or None when the
    project holds no such layer.
  """
  for lyr in QgsProject.instance().mapLayers().values():
    if lyr.customProperty("weavingspace_tile_id") == tid \
        and not lyr.customProperty("weavingspace_no_data"):
      return round(lyr.opacity() * 100)
  return None


folder = tempfile.mkdtemp(prefix="ws_opacity_door_")
try:
  QgsProject.instance().clear()
  layer = region_on_disk(folder, "one.gpkg")
  dlg = WeavingSpaceDialog(iface=T._Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  T._tick(300)
  dlg.gpkg_widget.setFilePath(os.path.join(folder, "map_one.gpkg"))
  dlg.spacing_spin.setValue(500)
  run(dlg)
  tid = dlg.table.item(0, 0).text()
  dlg.table.cellWidget(0, 6).setValue(40)      # as a user does
  combo = dlg.table.cellWidget(0, 4)
  combo.setCurrentText("Blues")
  combo.activated.emit(combo.currentIndex())   # the ramp, as a real pick
  T._tick(200)
  run(dlg)
  one = os.path.join(folder, "one.qgz")
  assert QgsProject.instance().write(one), "the project would not save"
  print(f"C0 project ONE saved: seen {seen(dlg, tid)}, drawn {drawn(tid)}%, "
        f"in the file {in_the_file(one, tid)}")

  # File > New, and a second map in the dialog the user never closed
  QgsProject.instance().clear()
  T._tick(300)
  two = region_on_disk(folder, "two.gpkg")
  dlg.layer_combo.setLayer(two)
  T._tick(400)
  dlg.gpkg_widget.setFilePath(os.path.join(folder, "map_two.gpkg"))
  # this map is to be solid: a deliberate choice about the SECOND map
  dlg.table.cellWidget(0, 6).setValue(100)
  T._tick(200)
  run(dlg)
  print(f"C1 second map, element {tid} deliberately solid: "
        f"seen {seen(dlg, tid)}, drawn {drawn(tid)}%")

  # File > Open, back to the first
  assert QgsProject.instance().read(one), "project ONE would not reopen"
  T._tick(1500)
  print(f"C2 project ONE reopened: seen {seen(dlg, tid)}, "
        f"drawn {drawn(tid)}%")

  run(dlg)
  after = os.path.join(folder, "one_after.qgz")
  assert QgsProject.instance().write(after), "the project would not re-save"
  print(f"C3 after one Generate: drawn {drawn(tid)}%, "
        f"in the file {in_the_file(after, tid)}")
  dlg.close()
finally:
  QgsProject.instance().clear()
  shutil.rmtree(folder, ignore_errors=True)
