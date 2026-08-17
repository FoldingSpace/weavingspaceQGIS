"""With Equal intervals and pins outside the data, are they still equal?

I claimed they would be. The pin mechanism cuts the scheme from the
samples BETWEEN the pins and then stretches the outermost computed
class to meet the pin, so the claim needs measuring rather than
reasoning about.

Two columns with DIFFERENT data ranges are given the SAME pins, which
is the maintainer's actual use: if a colour is to mean the same number
on both maps, the two ladders must come out identical.
"""
import importlib.util
import os
import sys

REPO = os.environ["WEAVINGSPACE_REPO"]
os.chdir(REPO)
sys.path.insert(0, REPO)

spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

from qgis.core import (QgsApplication, QgsFeature, QgsGeometry,   # noqa
                       QgsPointXY, QgsVectorLayer)

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()


def layer_of(values, name):
  """A one-column polygon layer holding these values.

  Args:
    values: the numbers to classify, one square each.
    name: what to call the layer, so two of them can be told apart.

  Returns:
    A memory QgsVectorLayer with a float field "v".
  """
  from weavingspace_qgis import compat
  layer = QgsVectorLayer("Polygon?crs=EPSG:2193", name, "memory")
  provider = layer.dataProvider()
  provider.addAttributes([compat.make_field("v", float)])
  layer.updateFields()
  rows = []
  for i, value in enumerate(values):
    feature = QgsFeature(layer.fields())
    feature.setAttribute("v", float(value))
    x = i * 10.0
    feature.setGeometry(QgsGeometry.fromPolygonXY([[
      QgsPointXY(x, 0), QgsPointXY(x + 9, 0),
      QgsPointXY(x + 9, 9), QgsPointXY(x, 9), QgsPointXY(x, 0)]]))
    rows.append(feature)
  provider.addFeatures(rows)
  layer.updateExtents()
  return layer


def ladder(values, name, scheme, pins):
  """The class bounds a column draws under a scheme and a pair of pins.

  Args:
    values: the column's values.
    name: a name for the layer, for the message.
    scheme: "Equal intervals" or "Quantiles".
    pins: the pin record, as make_graduated_renderer takes it.

  Returns:
    [(lower, upper), ...] rounded, in class order.
  """
  from weavingspace_qgis import bridge
  layer = layer_of(values, name)
  renderer = bridge.make_graduated_renderer(
    layer, "v", "Reds", scheme, 5, False, pinned=pins)
  return [(round(r.lowerValue(), 4), round(r.upperValue(), 4))
          for r in renderer.ranges()]


def main():
  """Two columns of different range, pinned alike, printed together."""
  pins = {"low": -5.0, "high": 40.0}
  a = [1.0, 2.0, 3.0, 5.0, 8.0, 13.0]          # narrow column
  b = [0.5, 9.0, 17.0, 25.0, 31.0, 38.0]       # wide column
  for scheme in ("Equal intervals", "Quantiles"):
    la = ladder(a, "a", scheme, pins)
    lb = ladder(b, "b", scheme, pins)
    print(f"\n{scheme}, both pinned to {pins['low']}..{pins['high']}")
    print(f"  column a {min(a)}..{max(a)}: {la}")
    print(f"  column b {min(b)}..{max(b)}: {lb}")
    widths = [round(hi - lo, 4) for lo, hi in la]
    print(f"  a's class widths: {widths}")
    print(f"  equal widths within a? "
          f"{len({w for w in widths if w > 0}) == 1}")
    print(f"  SAME LADDER on both columns? {la == lb}")


main()
