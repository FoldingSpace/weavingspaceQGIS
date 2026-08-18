"""Second route: bridge KEEPS exactly the record the dialog throws away.

No dialog at all here -- the renderer is asked directly for the map it
would draw from the copied record, and `pin_problem` is asked the two
questions the two sites ask.
"""
import os
import sys
sys.path.insert(0, os.getcwd())
from qgis.core import QgsApplication, QgsVectorLayer, QgsFeature
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
app = QgsApplication([], False)
app.initQgis()

from weavingspace_qgis import bridge

# a column with a hole from 10 to 90, which is where the two sites part
VALUES = [0.0, 0.5, 2.0, 5.0, 8.5, 95.0, 97.0, 99.0, 100.5]
RECORD = {"breaks": [10.0, 36.666666666666664, 63.333333333333336, 90.0],
          "low": 10.0, "high": 90.0}

lyr = QgsVectorLayer("Polygon?crs=EPSG:3857&field=v:double", "t", "memory")
feats = []
for v in VALUES:
  f = QgsFeature(lyr.fields())
  f.setAttribute("v", float(v))
  feats.append(f)
lyr.dataProvider().addFeatures(feats)

print("what the COPY asks (each flag alone):",
      repr(bridge.pin_problem(RECORD["low"], None, VALUES, 5)), "|",
      repr(bridge.pin_problem(None, RECORD["high"], VALUES, 5)))
print("what the LANDING asks (both, with the ladder):",
      repr(bridge.pin_problem(RECORD["low"], RECORD["high"], VALUES, 5,
                              RECORD["breaks"])))

r = bridge.make_graduated_renderer(
  lyr, "v", "Reds", "Equal intervals", 5, False, False, (0, 100), None,
  VALUES, dict(RECORD))
print("\nthe map bridge draws from that record (copy KEPT):")
for x in r.ranges():
  print(f"   [{x.lowerValue():.6g}, {x.upperValue():.6g}] "
        f"{x.symbol().color().name()}")

r2 = bridge.make_graduated_renderer(
  lyr, "v", "Reds", "Equal intervals", 5, False, False, (0, 100), None,
  VALUES, None)
print("\nthe map after the dialog has popped the record:")
for x in r2.ranges():
  print(f"   [{x.lowerValue():.6g}, {x.upperValue():.6g}] "
        f"{x.symbol().color().name()}")

app.exitQgis()
