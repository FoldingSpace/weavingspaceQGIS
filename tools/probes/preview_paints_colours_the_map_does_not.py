"""The design view paints colours the map never paints.

WHAT A USER LOSES. They generate a map, refine one element in QGIS's
Symbology panel -- which the plugin acknowledges, and which the row's
own ramp swatch follows -- and then go back to the design view to
judge the pattern while they nudge the spacing. A quarter of that
picture is painted in a colour the map does not contain, and the
colour the map DOES paint appears in it nowhere. The same happens
after narrowing the Ramp Display Range: the element goes near-white on
the map and stays strong red in the design view. Somebody judges the
design from a picture the map does not honour, which is exactly what
the design view exists to prevent.

WHY. `dialog._table_id_colours` (dialog.py:7424) is the preview's
store and it asks only the ROW: the mode, the single colour, and
`bridge.ramp_swatch_colour(a["ramp"])`, which is `get_ramp(name).
color(0.65)`. Two things the map is drawn from never reach it.

  * DEFERRAL. `_ramp_cell_icon`'s deferring branch (dialog.py:5385)
    samples the LAYER through `bridge.renderer_fill_colours`, because
    "the plugin no longer decides those colours and the row must still
    describe the map" (settled with the maintainer, 2026-08-15).
    `_table_id_colours` has no such branch, so it goes on reading the
    disabled ramp combo -- the very control that branch exists because
    it cannot be trusted. One fact, two descriptions, one of them
    following QGIS.
  * THE RAMP DISPLAY WINDOW. `a["range_bounds"]` rides every graduated
    row and decides where in the ramp the classes sample;
    `bridge.graduated_class_colours` (bridge.py:1939) already knows
    how. `ramp_swatch_colour` takes 0.65 of the whole ramp whatever
    the window says.

`_row_follows_the_renderer` calls `_refresh_preview_colours` and the
nameable-restyle path is therefore FINE -- a ramp changed in QGIS to
one the plugin can name moves the preview correctly. The gap is where
the row stops being able to name what the layer holds.

Present since deferral landed in e01896b (2026-08-15) for the first
arm; `_table_id_colours` has never read `range_bounds`.

Both sides are read as RENDERED PIXELS, not as records: the map
through QgsMapRendererParallelJob, the design view through
`preview.grab()`. Neither reading passes through the record that is
wrong.

    python3 tools/hunt_probe.py --prepare --name preview-vs-map
    python3 tools/hunt_probe.py --name preview-vs-map \\
      --run tools/probes/preview_paints_colours_the_map_does_not.py
"""
import collections
import importlib.util
import os
import sys

REPO = os.path.dirname(os.path.dirname(
  os.path.dirname(os.path.abspath(__file__))))
os.chdir(REPO)
sys.path.insert(0, REPO)
spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

from qgis.core import (QgsApplication, QgsMapRendererParallelJob,  # noqa: E402
                       QgsMapSettings, QgsProject)
from qgis.PyQt.QtCore import QEventLoop, QSize                     # noqa: E402
from qgis.PyQt.QtGui import QColor                                 # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()

from weavingspace_qgis.dialog import WeavingSpaceDialog            # noqa: E402

KEY = "#ff00ff"


def painted(layers):
  """Every colour the MAP puts on screen, by pixel count.

  Args:
    layers: the output layers to render, in drawing order.

  Returns:
    Counter of "#rrggbb" -> pixels, the chroma key excluded.
  """
  settings = QgsMapSettings()
  settings.setLayers(layers)
  settings.setBackgroundColor(QColor(KEY))
  extent = layers[0].extent()
  for lyr in layers[1:]:
    extent.combineExtentWith(lyr.extent())
  settings.setExtent(extent)
  settings.setOutputSize(QSize(400, 400))
  settings.setDestinationCrs(layers[0].crs())
  job = QgsMapRendererParallelJob(settings)
  loop = QEventLoop()
  job.finished.connect(loop.quit)
  job.start()
  loop.exec()
  image = job.renderedImage()
  tally = collections.Counter()
  for y in range(image.height()):
    for x in range(image.width()):
      name = QColor(image.pixel(x, y)).name()
      if name != KEY:
        tally[name] += 1
  return tally


def previewed(dlg):
  """Every colour the DESIGN VIEW puts on screen, by pixel count.

  Args:
    dlg: a SHOWN dialog, since grabbing a never-shown widget is
      unreliable.

  Returns:
    Counter of "#rrggbb" -> pixels, the panel's own #fafafa included.
  """
  image = dlg.preview.grab().toImage()
  tally = collections.Counter()
  for y in range(image.height()):
    for x in range(image.width()):
      tally[QColor(image.pixel(x, y)).name()] += 1
  return tally


def fixture(row, field):
  """A generated four-element design, in a project of its own.

  Args:
    row: which table row to give a variable to.
    field: the column that row carries.

  Returns:
    (project, dialog, tile_id of that row).
  """
  project = QgsProject.instance()
  project.clear()
  assert not project.mapLayers(), "the project was not clean"
  layer = T.make_region_layer(n=12)
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=T._Iface())
  dlg.show()
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  T._tick(300)
  dlg.table.cellWidget(row, 1).setCurrentText(field)
  T._tick(200)
  dlg.spacing_spin.setValue(1200)
  T._generate_and_wait(dlg)
  return project, dlg, dlg.table.item(row, 0).text()


def verdict(tag, dlg, project, tile_id, wanted):
  """Print what each side paints, and whether they share the colour.

  Args:
    tag: which arm this is.
    dlg: the shown dialog.
    project: the QgsProject holding the outputs.
    tile_id: the element under test.
    wanted: the colour the MAP is expected to paint for it, or None to
      report the element's commonest map colour instead.

  Returns:
    None; prints.
  """
  outs = [project.mapLayer(i) for i in dlg._element_layer_ids.values()]
  outs = [o for o in outs if o is not None]
  drawn = painted(outs)
  shown = previewed(dlg)
  element = project.mapLayer(dlg._element_layer_ids[tile_id])
  mine = painted([element])
  if wanted is None:
    wanted = mine.most_common(1)[0][0]
  claimed = QColor(dlg._table_id_colours()[tile_id]).name()
  gap = min(max(abs(QColor(claimed).red() - QColor(c).red()),
                abs(QColor(claimed).green() - QColor(c).green()),
                abs(QColor(claimed).blue() - QColor(c).blue()))
            for c in mine)
  print(f"\n--- {tag}  (element {tile_id}, row reads "
        f"'{dlg.table.cellWidget(dlg._row_for_element(tile_id), 2).currentText()}')")
  print(f"  map paints        {wanted}: {drawn.get(wanted, 0)} px")
  print(f"  design view has   {wanted}: {shown.get(wanted, 0)} px")
  print(f"  design view paints {claimed}: {shown.get(claimed, 0)} px")
  print(f"  map has            {claimed}: {drawn.get(claimed, 0)} px")
  print(f"  the previewed colour is {gap}/255 from ANY pixel this "
        f"element paints on the map")


# ---- ARM ONE: the element is restyled in QGIS and begins deferring
project, dlg, tid = fixture(1, "v3")
element = project.mapLayer(dlg._element_layer_ids[tid])
element.setRenderer(T._rule_based_renderer("#00aa44"))
element.styleChanged.emit()
T._tick(600)
verdict("restyled in QGIS's Symbology panel", dlg, project, tid, "#00aa44")
dlg.close()

# ---- ARM TWO: the Ramp Display Range is narrowed to the palest fifth
#      (the editor's own `range_changed` does exactly these four
#      lines; `_clear_quant_customization` is a no-op with no picks)
project, dlg, tid = fixture(0, "v1")
dlg._ramp_ranges[tid] = (0, 20)
dlg._custom_swatch_cache.pop(tid, None)
dlg._apply_style_change()
T._tick(600)
verdict("Ramp Display Range narrowed to 0-20%", dlg, project, tid, None)
dlg.close()
QgsProject.instance().clear()
