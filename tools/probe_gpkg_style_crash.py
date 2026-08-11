#!/usr/bin/env python3
"""Ask whether QGIS itself crashes reading a style back out of a GeoPackage.

    <qgis python> tools/probe_gpkg_style_crash.py

WHY THIS EXISTS. On QGIS 4.2.1 a fresh process died with SIGSEGV at
``list(renderer.ranges())``, after ``loadDefaultStyle()`` on a
GeoPackage this plugin had written (Linux CI, 2026-08-11). Three
explanations fit that evidence and they lead to completely different
work: a defect in QGIS that reaches users, a defect in QGIS that only
our test provokes, or something wrong with the style this plugin
writes. Guessing between them would be guessing about a crash.

So this probe does what the dependency-workaround procedure requires
first: it reproduces the situation WITH THE PLUGIN OUT OF THE WAY.
Nothing here imports weavingspace_qgis. It builds an ordinary memory
layer, gives it an ordinary QgsGraduatedSymbolRenderer, writes it to a
GeoPackage with QGIS's own writer, saves the style into the file the
way QGIS does, and then -- in THIS process, having freed nothing --
reads it back and walks the ranges.

Reading the result:

  every step printed and "PROBE OK" at the end
      plain QGIS does not crash on this. The fault involves something
      the plugin does differently: compare what it writes (the style
      XML in layer_styles, the renderer's symbol types) against what
      this probe writes.

  a crash before "PROBE OK"
      QGIS crashes on its own output, and the last STEP line names the
      call. That is an upstream defect: report it with this file
      attached, narrow the plugin's use of the same call, and treat
      `bridge.renderer_fill_colours` as reachable on that version.

Exit status: 0 when every step completed, non-zero when a step raised.
A SIGSEGV kills the process outright, which is the answer this probe
exists to obtain and cannot be caught.
"""
import faulthandler
import os
import sys
import tempfile

faulthandler.enable()


def step(message):
  """Announce a phase, flushed, so a crash says how far it got.

  Args:
    message: what is about to be attempted.

  Returns:
    None. Flushed deliberately: a segfault discards whatever is still
    buffered, and an empty log beside a signal is indistinguishable
    from a process that never started.
  """
  print(f"STEP {message}", flush=True)


def main():
  """Build, write, reload and walk a graduated style, announcing each step.

  Returns:
    None. Exits non-zero if any step raises; a segfault ends the
    process without returning, which is itself the finding.
  """
  from qgis.core import (
    QgsApplication, QgsCoordinateTransformContext, QgsFeature,
    QgsField, QgsGeometry, QgsGradientColorRamp, QgsGraduatedSymbolRenderer,
    QgsPointXY, QgsVectorFileWriter, QgsVectorLayer)
  from qgis.PyQt.QtCore import QMetaType
  from qgis.PyQt.QtGui import QColor

  step("starting QGIS")
  QgsApplication.setPrefixPath(
    os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  app = QgsApplication([], False)
  app.initQgis()
  print(f"QGIS {__import__('qgis.core', fromlist=['Qgis']).Qgis.QGIS_VERSION}",
        flush=True)

  folder = tempfile.mkdtemp(prefix="probe-gpkg-")
  path = os.path.join(folder, "probe.gpkg")

  step("building a plain memory layer")
  layer = QgsVectorLayer("Polygon?crs=EPSG:3857", "probe", "memory")
  layer.dataProvider().addAttributes(
    [QgsField("value", QMetaType.Type.Double)])
  layer.updateFields()
  features = []
  for i in range(20):
    feature = QgsFeature(layer.fields())
    x = i * 10.0
    feature.setGeometry(QgsGeometry.fromPolygonXY([[
      QgsPointXY(x, 0), QgsPointXY(x + 10, 0),
      QgsPointXY(x + 10, 10), QgsPointXY(x, 10), QgsPointXY(x, 0)]]))
    feature.setAttributes([float(i)])
    features.append(feature)
  layer.dataProvider().addFeatures(features)
  layer.updateExtents()

  step("seeding a graduated renderer, QGIS's own way")
  renderer = QgsGraduatedSymbolRenderer.createRenderer(
    layer, "value", 5, QgsGraduatedSymbolRenderer.Mode.EqualInterval,
    layer.renderer().symbol().clone(),
    QgsGradientColorRamp(QColor("#fff5f0"), QColor("#67000d")))
  layer.setRenderer(renderer)

  step("writing the GeoPackage")
  options = QgsVectorFileWriter.SaveVectorOptions()
  options.driverName = "GPKG"
  options.layerName = "probe"
  written = QgsVectorFileWriter.writeAsVectorFormatV3(
    layer, path, QgsCoordinateTransformContext(), options)
  code = written[0] if isinstance(written, tuple) else written
  if code != QgsVectorFileWriter.WriterError.NoError:
    sys.exit(f"could not write the GeoPackage: {written}")

  step("reopening it from the file")
  reopened = QgsVectorLayer(path + "|layername=probe", "probe", "ogr")
  if not reopened.isValid():
    sys.exit("the GeoPackage did not reopen; the probe proves nothing")
  reopened.setRenderer(renderer.clone())

  step("saving the style INTO the GeoPackage")
  reopened.saveStyleToDatabase("probe", "probe style", True, "")

  step("reopening again, cold")
  cold = QgsVectorLayer(path + "|layername=probe", "probe", "ogr")
  if not cold.isValid():
    sys.exit("the second open failed; the probe proves nothing")

  step("loadDefaultStyle")
  cold.loadDefaultStyle()

  step("layer.renderer() -- BORROWED, as the crashing child did")
  borrowed = cold.renderer()
  print(f"renderer is {type(borrowed).__name__}", flush=True)

  step("list(renderer.ranges()) on the borrowed pointer")
  held = list(borrowed.ranges()) if hasattr(borrowed, "ranges") else []
  print(f"{len(held)} ranges", flush=True)

  step("reading each range's symbol colour")
  colours = [item.symbol().color().name() for item in held]
  print(f"colours {colours}", flush=True)

  step("the same again through a CLONE, for comparison")
  owned = cold.renderer().clone()
  cloned = [item.symbol().color().name() for item in list(owned.ranges())]
  print(f"cloned colours {cloned}", flush=True)

  print("PROBE OK: plain QGIS survived every step", flush=True)
  sys.stdout.flush()
  app.exitQgis()
  os._exit(0)


if __name__ == "__main__":
  main()
