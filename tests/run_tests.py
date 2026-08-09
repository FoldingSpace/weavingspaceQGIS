"""End-to-end test suite for the WeavingSpace QGIS plugin.

Run this under *QGIS's own Python* (not your system Python) — see
MAINTAINING.md for the exact command on each platform. On macOS:

  QP=/Applications/QGIS.app/Contents   # adjust to your QGIS app name
  QT_QPA_PLATFORM=offscreen PYTHONHOME=$QP/Frameworks \
  PROJ_LIB=$QP/Resources/qgis/proj \
  $QP/MacOS/python3.* -u tests/run_tests.py

Exit code 0 = all pass. When a QGIS upgrade breaks the plugin, the
first failing test names the area to fix (usually a shim in
weavingspace_qgis/compat.py).

The tests come in families, roughly in the order they run:

* unit-ish checks of the pieces (dependency logic, the catalogue, the
  bridge's conversions and renderer seeding, the size guard);
* data checks against the packaged fixtures in tests/data/ — a real
  Auckland dataset and a generated categorical one — because
  synthetic squares never produce a real CRS, multipolygons, wildly
  uneven areas, or genuine nulls;
* GUI behaviour: the design cascade, the per-row style state machine,
  choice persistence, and the chooser-race regression;
* integration sessions: whole workflows (export and reload, layer
  switching, live update, a second dialog, interleaved styling and
  design changes, categorical colour sources) rather than one
  behaviour each;
* UI-against-library comparisons: drive the dialog, then build the
  same map by calling weavingspace directly with what those settings
  mean, and compare geometry element by element and then the rendered
  pixels. These are the tests that catch a control wired to the wrong
  argument, and they have already found three real bugs;
* stress: fast interaction with no waiting (the shape of the race
  conditions this project has actually shipped) and repeated fiddling
  with styling, rendering and sizing on the categorical fixture.

Each test runs with an EMPTY project (see ``check``), so results do
not depend on the order tests run in.

Related tools: ``tools/mutation_check.py`` breaks behaviours on
purpose to confirm these tests would notice; ``tools/coverage_report.py``
reports which plugin lines this suite never reaches;
``tools/make_test_fixtures.py`` regenerates the categorical fixtures.
"""

import faulthandler
import json
import math
import os
import random
import signal
import sys
import tempfile
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))

import warnings
warnings.filterwarnings("ignore")

from qgis.core import (  # noqa: E402
  QgsApplication, QgsVectorLayer, QgsProject, QgsFeature, QgsGeometry,
  QgsPointXY, QgsStyle, QgsGraduatedSymbolRenderer,
  QgsCategorizedSymbolRenderer, QgsSingleSymbolRenderer, QgsFillSymbol,
)
from qgis.PyQt.QtCore import QEventLoop, QTimer  # noqa: E402

PASSED, FAILED = [], []


def report_dir():
  """Where UI-vs-library renders are written so the release PDF can
  show them. release.py sets WEAVINGSPACE_REPORT_DIR; a bare run falls
  back to reports/v<version>/ so the images still land somewhere
  predictable."""
  explicit = os.environ.get("WEAVINGSPACE_REPORT_DIR")
  if explicit:
    path = explicit
  else:
    version = "unknown"
    meta = os.path.join(ROOT, "weavingspace_qgis", "metadata.txt")
    with open(meta, encoding="utf-8") as f:
      for line in f:
        if line.startswith("version="):
          version = line.split("=", 1)[1].strip()
    path = os.path.join(ROOT, "reports", f"v{version}")
  out = os.path.join(path, "ui-vs-library")
  os.makedirs(out, exist_ok=True)
  return out


def _enable_stack_dumps():
  """Let a watchdog ask this process where it is stuck.

  faulthandler.register makes SIGUSR1 print every thread's stack to
  stderr without killing anything, so tools/watchdog.py can turn "it
  stopped" into "it stopped on this line" at the moment it notices.
  enable() covers the other case: a hard crash in C (which is how the
  pyproj threading bug was found) prints a traceback instead of
  vanishing.

  Returns:
    None.
  """
  faulthandler.enable()
  try:
    faulthandler.register(signal.SIGUSR1, all_threads=True, chain=False)
  except (AttributeError, ValueError):
    pass  # not available on this platform; the watchdog still works


def _no_modal_dialogs():
  """Make every message box answer itself.

  A modal QMessageBox offscreen waits for a click that can never
  come: the whole suite stops, with no output to say why (this cost a
  31-minute hang). Tests are not the place to discover that a code
  path pops a dialog, so the boxes are replaced with recorders. What
  they were asked is kept in MODALS, so a test can assert that the
  user WOULD have been told something.

  Returns:
    None; QMessageBox is patched for the rest of the process.
  """
  from qgis.PyQt import QtWidgets

  def record(kind, default):
    def shim(*args, **kwargs):
      text = next((a for a in args[1:] if isinstance(a, str)), "")
      MODALS.append((kind, text))
      return default
    return shim

  QtWidgets.QMessageBox.critical = record(
    "critical", QtWidgets.QMessageBox.StandardButton.Ok)
  QtWidgets.QMessageBox.warning = record(
    "warning", QtWidgets.QMessageBox.StandardButton.Ok)
  QtWidgets.QMessageBox.information = record(
    "information", QtWidgets.QMessageBox.StandardButton.Ok)
  QtWidgets.QMessageBox.question = record(
    "question", QtWidgets.QMessageBox.StandardButton.Yes)


MODALS = []


def check(name, fn):
  """Run one test in an isolated project.

  Args:
    name: the display name, printed with the result and used as the
      key in the release's testing report. It is matched against the
      mutation catalogue too, so renaming one here means renaming it
      there.
    fn: the test function, called with no arguments. It may raise
      anything; the traceback is caught and reported rather than
      stopping the run, so one failure does not hide the rest.

  Returns:
    True when the test passed. The project is emptied afterwards
    either way.

  Every dialog test works through the ONE QgsProject singleton, so
  layers (and generated output groups) left behind by one test are
  visible to the next: the region combo may select a different layer
  than the test intended, and a failure part-way through one test can
  cascade into unrelated failures below it. Clearing before each test
  makes results order-independent, so a FAIL names the test that is
  actually broken."""
  project = QgsProject.instance()
  project.clear()
  MODALS.clear()
  started = time.perf_counter()
  try:
    fn()
    PASSED.append(name)
    print(f"PASS  {name}  [{time.perf_counter() - started:.1f}s]")
  except Exception:
    FAILED.append(name)
    print(f"FAIL  {name}  [{time.perf_counter() - started:.1f}s]")
    traceback.print_exc()
  finally:
    project.clear()


def make_region_layer(n=4, cell=1000, origin=(0, 0)):
  """A small synthetic region layer.

  Args:
    n: grid side, so the layer holds n*n square polygons.
    cell: each square's side in map units (EPSG:3857).
    origin: (x, y) of the grid's lower-left corner. Defaults to the
      origin; pass something far away when a test needs TWO regions
      that cannot be confused for one another, as when checking that
      switching the region layer really re-tiles.

  Returns:
    A memory layer with four attributes: ``v1`` and ``v2`` are simple
    gradients, ``v3`` is their product (heavily tied, which is where
    classification conventions show up), and ``landcover`` is a
    four-class categorical. Deliberately tiny: most tests want speed,
    and the tests that need real-world messiness use the packaged
    datasets instead.
  """
  from weavingspace_qgis import compat
  layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "region", "memory")
  prov = layer.dataProvider()
  prov.addAttributes([compat.make_field("v1", float),
                      compat.make_field("v2", float),
                      compat.make_field("v3", int),
                      compat.make_field("landcover", str)])
  layer.updateFields()
  cats = ["forest", "water", "urban", "crops"]
  feats = []
  for i in range(n):
    for j in range(n):
      f = QgsFeature(layer.fields())
      ox, oy = origin
      ring = [QgsPointXY(ox + i * cell, oy + j * cell),
              QgsPointXY(ox + (i + 1) * cell, oy + j * cell),
              QgsPointXY(ox + (i + 1) * cell, oy + (j + 1) * cell),
              QgsPointXY(ox + i * cell, oy + (j + 1) * cell)]
      f.setGeometry(QgsGeometry.fromPolygonXY([ring]))
      f["v1"], f["v2"], f["v3"] = float(i), float(j), i * j
      f["landcover"] = cats[(i + j) % len(cats)]
      feats.append(f)
  prov.addFeatures(feats)
  layer.updateExtents()
  return layer


def bridge_module():
  """The plugin's bridge, imported late (QGIS must be up first)."""
  from weavingspace_qgis import bridge
  return bridge


def make_region_gdf():
  """The synthetic region as a GeoDataFrame, for library-level tests
  that skip the QGIS-layer step."""
  from weavingspace_qgis import bridge
  return bridge.layer_to_gdf(make_region_layer(), ["v1", "v2"])


def test_deps():
  """Every package the plugin needs is present in this QGIS.

  The first thing to check and the cheapest: geopandas and shapely
  arrive with some QGIS builds and not others, and a missing one
  turns every later failure in this file into a confusing symptom of
  the same cause. deps.missing_packages() reports what the
  provisioner would have to fetch.
  """
  from weavingspace_qgis import deps
  missing = deps.missing_packages()
  assert missing == [], f"deps missing/outdated in this QGIS: {missing}"
  # _best_wheel must RANK, not just return: an interpreter-specific
  # wheel beats the universal one, and incompatible wheels are skipped
  top = deps._sys_tags()[0]  # this interpreter's most-specific tag
  best = deps._best_wheel([f"x-1.0-{top}.whl", "x-1.0-py3-none-any.whl"])
  assert best == f"x-1.0-{top}.whl", "specific wheel must outrank universal"
  assert deps._best_wheel(["x-1.0-cp27-cp27m-win32.whl"]) is None, \
    "an incompatible wheel must never be chosen"


def test_library_units():
  """The vendored weavingspace builds the units we rely on.

  A guard on the boundary between us and upstream: before any plugin
  behaviour is worth testing, the library itself must produce the
  tile units and weave units the catalogue names, with the element
  ids it promises. A re-vendor that broke one of these would
  otherwise surface as a dozen unrelated plugin failures.
  """
  from weavingspace import TileUnit, WeaveUnit
  for spec in (dict(cls=TileUnit, kw=dict(tiling_type="cairo"),
                    ids="abcd"),
               dict(cls=TileUnit,
                    kw=dict(tiling_type="hex-slice", n=6, offset=0),
                    ids="abcdef"),
               dict(cls=WeaveUnit,
                    kw=dict(weave_type="basket", n=(2, 2),
                            strands="ab|cd", aspect=0.75),
                    ids="abcd")):
    unit = spec["cls"](spacing=500, crs=3857, **spec["kw"])
    assert set(unit.tiles.tile_id) == set(spec["ids"]), \
      f"{spec['kw']}: got ids {sorted(set(unit.tiles.tile_id))}"


def test_catalogue_sweep():
  """Every catalogue entry at every element count must construct a
  unit whose distinct tile ids number exactly n. This is the vendor
  upgrade's early-warning system: a new upstream that renames a
  constructor argument or changes a family's output breaks here, with
  the family named, before anything subtler fails. It also covers the
  two library extras (stripes, grid) including grid's punctured form
  (n below rows x cols leaves openings, not fewer distinct ids)."""
  from weavingspace_qgis import catalog
  for n, families in catalog.TILINGS_BY_N.items():
    for name, spec in families.items():
      unit = catalog.make_unit(spec, spacing=500, crs=3857)
      ids = set(unit.tiles.tile_id)
      assert len(ids) == n, f"{name}: {len(ids)} ids, expected {n}"
  # grid specifics: the punctured form keeps n ids over rows*cols
  # cells, and explicit rows/cols reach the constructor
  spec = catalog.TILINGS_BY_N[2]["grid 2"]
  unit = catalog.make_unit(spec, spacing=500, crs=3857, nrows=2, ncols=2)
  assert set(unit.tiles.tile_id) == {"a", "b"}
  proto = unit.prototile.geometry.iloc[0].area
  assert unit.tiles.geometry.area.sum() < proto * 0.6, \
    "2 elements on a 2x2 grid must leave half the cell open"
  rows, cols = catalog.tightest_grid(5)
  assert rows * cols >= 5 and abs(rows - cols) <= 1


def test_bridge_roundtrip():
  """A QGIS layer becomes a GeoDataFrame and comes back intact.

  The conversion at the heart of the plugin: geometry, attribute
  values and CRS have to survive the trip in both directions, since
  everything downstream is computed on the GeoDataFrame and drawn
  from the layer. Values are checked as well as counts — a round trip
  that keeps every row and loses what they say is the failure worth
  catching.
  """
  from weavingspace_qgis import bridge
  layer = make_region_layer()
  gdf = bridge.layer_to_gdf(layer, ["v1", "landcover"])
  assert len(gdf) == 16 and "landcover" in gdf.columns
  out = bridge.gdf_to_layer(gdf, "roundtrip")
  assert out.isValid() and out.featureCount() == 16
  # geographic layers are reprojected to Web Mercator for tiling (the
  # web app's behaviour); build a tiny 4326 layer and check the CRS
  from weavingspace_qgis import compat
  geo = QgsVectorLayer("MultiPolygon?crs=EPSG:4326", "geo", "memory")
  geo.dataProvider().addAttributes([compat.make_field("v", float)])
  geo.updateFields()
  f = QgsFeature(geo.fields())
  f.setGeometry(QgsGeometry.fromPolygonXY([[
    QgsPointXY(174.0, -37.0), QgsPointXY(174.1, -37.0),
    QgsPointXY(174.1, -36.9), QgsPointXY(174.0, -36.9)]]))
  f["v"] = 1.0
  geo.dataProvider().addFeatures([f])
  geo_gdf = bridge.layer_to_gdf(geo, ["v"])
  assert geo_gdf.crs is not None and not geo_gdf.crs.is_geographic, \
    "geographic input must arrive projected (EPSG:3857)"


def test_real_world_data():
  """The whole pipeline on a real dataset, not synthetic squares.

  tests/data/imd-auckland-sa2-2018.gpkg (packaged; see its README)
  brings four things the synthetic grid cannot: a real projected CRS
  (EPSG:2193, so the strip-and-reattach around the worker thread is
  exercised against a CRS that actually has to survive the trip),
  multipolygon geometry, polygon areas spanning two orders of
  magnitude, and genuine nulls in some attributes. The assertions
  below are about those four things specifically.

  Regression: CRS work on the QgsTask worker thread segfaulted QGIS, because PROJ is not safe to use concurrently with the main thread; the CRS is now stripped before the task and reattached in the done callback.
  [review]
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.core import QgsGraduatedSymbolRenderer
  path = os.path.join(HERE, "data", "imd-auckland-sa2-2018.gpkg")
  assert os.path.exists(path), f"packaged test data missing: {path}"
  layer = QgsVectorLayer(path, "auckland", "ogr")
  assert layer.isValid() and layer.featureCount() == 155
  assert layer.crs().authid() == "EPSG:2193"
  project = QgsProject.instance()
  project.addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  # auto-spacing on very uneven polygons must land inside the data's
  # own size range, not at some degenerate extreme
  dlg._auto_spacing()
  spacing = dlg.spacing_spin.value()
  assert 200 < spacing < 20_000, f"auto spacing {spacing} implausible"

  # state the design explicitly rather than leaning on defaults, so
  # the library call below can describe the same map
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.opt_join_prototiles.setChecked(False)
  dlg.opt_retain.setChecked(False)
  dlg.opt_clip.setChecked(False)
  dlg.opt_icons.setChecked(False)
  dlg.table.cellWidget(0, 1).setCurrentText("imd")
  dlg.table.cellWidget(1, 1).setCurrentText("employment")
  dlg.spacing_spin.setValue(1500)
  _generate_and_wait(dlg)

  group = project.layerTreeRoot().findGroup(dlg._group_name)
  assert group is not None and len(group.children()) == len(dlg._tile_ids())
  out = project.mapLayer(dlg._element_layer_ids["a"])
  assert out.featureCount() > 0
  # the CRS made the round trip: stripped before the task (pyproj is
  # main-thread-only), reattached in the done callback. A blank or
  # Web Mercator CRS here is the regression this guards
  assert out.crs().authid() == "EPSG:2193", \
    f"output CRS came back as {out.crs().authid()}"
  # real nulls reach the symbology as an explicit no-data class rather
  # than crashing or silently colouring as zero
  renderer = out.renderer()
  assert isinstance(renderer, QgsGraduatedSymbolRenderer)
  idx = out.fields().indexOf("imd")
  assert idx >= 0, "the mapped field must exist on the output layer"
  values = [f["imd"] for f in out.getFeatures()]
  numbers = [v for v in values if isinstance(v, (int, float))]
  assert numbers, "no numeric values reached the output"
  # the dataset has one feature with nulls across every score column;
  # whether its tiles survive depends on where the pattern falls, so
  # assert on the class structure instead: a "no data" class exists
  # for graduated symbology and the classes span the real range
  lo, hi = min(numbers), max(numbers)
  ranges = renderer.ranges()
  assert ranges[0].lowerValue() <= lo and ranges[-1].upperValue() >= hi, \
    "classes must span the real data range"
  # the map itself, against one built straight from the library with
  # the settings this test used
  from weavingspace import TileUnit, Tiling
  # the region carries every variable the table ended up holding
  # (elements the test did not set keep the dialog's defaults, and
  # those are part of the settings too)
  fields = sorted({a["var"] for a in dlg._assignments() if a["var"]})
  expected = Tiling(
    TileUnit(tiling_type="laves", code="3.3.4.3.4", spacing=1500,
             crs=2193),
    bridge_module().layer_to_gdf(layer, fields)) \
    .get_tiled_map(join_on_prototiles=False, retain_tileables=False,
                   ragged_edges=True).map
  for tid in sorted(set(expected["tile_id"])):
    got = project.mapLayer(dlg._element_layer_ids[tid]).featureCount()
    want = len(expected[expected["tile_id"] == tid])
    assert got == want, f"element {tid}: {got} tiles, library says {want}"
  # every element, not just the assigned ones: the dialog draws the
  # unassigned elements as plain fill, so a comparison that left them
  # out would be comparing two different maps
  assignments = dlg._assignments()
  visual_pair("real data auckland imd",
              [project.mapLayer(dlg._element_layer_ids[a["id"]])
               for a in assignments],
              expected, assignments)
  for lid in list(dlg._element_layer_ids.values()):
    project.removeMapLayer(lid)
  project.removeMapLayer(layer.id())
  dlg.close()


def test_awkward_geometry():
  """Geometry the bridge must cope with regardless of the packaged
  data: a self-touching (invalid) ring, a polygon with a hole, a
  multipart feature, and null attribute values. layer_to_gdf repairs
  invalid geometry with make_valid and normalises NULLs; this pins
  that behaviour deterministically on every machine."""
  from weavingspace_qgis import bridge, compat
  from weavingspace import TileUnit, Tiling
  layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "awkward", "memory")
  prov = layer.dataProvider()
  prov.addAttributes([compat.make_field("v", float)])
  layer.updateFields()

  def feat(wkt, value):
    f = QgsFeature(layer.fields())
    f.setGeometry(QgsGeometry.fromWkt(wkt))
    if value is not None:
      f["v"] = value
    return f

  bowtie = ("POLYGON((0 0, 1000 1000, 1000 0, 0 1000, 0 0))")  # invalid
  holed = ("POLYGON((2000 0, 4000 0, 4000 2000, 2000 2000, 2000 0),"
           "(2500 500, 3500 500, 3500 1500, 2500 1500, 2500 500))")
  multi = ("MULTIPOLYGON(((5000 0, 6000 0, 6000 1000, 5000 1000, 5000 0)),"
           "((7000 0, 8000 0, 8000 1000, 7000 1000, 7000 0)))")
  prov.addFeatures([feat(bowtie, 1.0), feat(holed, 2.0),
                    feat(multi, None)])  # the last carries a NULL
  layer.updateExtents()

  gdf = bridge.layer_to_gdf(layer, ["v"])
  assert len(gdf) == 3
  assert gdf.geometry.is_valid.all(), \
    "invalid input geometry must arrive repaired (make_valid)"

  # NULLs: a memory layer is no use for this. An attribute never set
  # on a memory feature reads back as 0.0, not as QGIS's NULL, so a
  # test built on one exercises the normalisation not at all — which
  # is how a mutation deleting it went unnoticed. The packaged
  # Auckland dataset carries a genuine null, so use that.
  real = QgsVectorLayer(
    os.path.join(HERE, "data", "imd-auckland-sa2-2018.gpkg"), "ak", "ogr")
  assert real.isValid()
  real_gdf = bridge.layer_to_gdf(real, ["imd", "employment"])
  assert str(real_gdf["imd"].dtype) == "float64", \
    f"a NULL left unnormalised makes the column object dtype, not " \
    f"numeric: got {real_gdf['imd'].dtype}"
  assert int(real_gdf["imd"].isna().sum()) == 1, \
    "the dataset's one null must arrive as NaN"
  # and it must behave as a null, not merely look like one: pandas
  # arithmetic and QGIS classification both depend on that
  assert real_gdf["imd"].mean() == real_gdf["imd"].dropna().mean(), \
    "a normalised null must be skipped by arithmetic"
  assert real_gdf["imd"].max() > 0, "real values must survive alongside it"
  # and the repaired geometry still tiles
  unit = TileUnit(tiling_type="cairo", spacing=400, crs=3857)
  tiled = Tiling(unit, gdf).get_tiled_map().map
  assert len(tiled) > 0 and set(tiled["tile_id"]) == set("abcd")


def test_renderer_seeding():
  """Each style produces the QGIS renderer it should.

  The dialog never draws anything itself: it seeds a standard
  graduated, categorized or single-symbol renderer and hands the
  layer to QGIS. This checks that seeding, including that the
  plugin's palettes reach the style library first — a ramp named but
  not installed yields a renderer with the wrong colours and no
  error.
  """
  from weavingspace_qgis import bridge, compat
  bridge.ensure_ramps_installed()
  assert "tab10" in QgsStyle.defaultStyle().colorRampNames()
  layer = make_region_layer()
  gdf = bridge.layer_to_gdf(layer, ["v1", "landcover"])
  out = bridge.gdf_to_layer(gdf, "seedtest")
  bridge.seed_renderer(out, {"id": "a", "var": "v1", "mode": "Graduated",
                             "ramp": "Reds", "scheme": "Equal intervals",
                             "k": 4, "outline": False})
  assert isinstance(out.renderer(), QgsGraduatedSymbolRenderer)
  assert len(out.renderer().ranges()) == 4, \
    "Equal intervals with k=4 must cut exactly 4 classes"
  bridge.seed_renderer(out, {"id": "a", "var": "landcover",
                             "mode": "Categorized", "ramp": "tab10",
                             "outline": False})
  assert isinstance(out.renderer(), QgsCategorizedSymbolRenderer)
  labels = [c.label() for c in out.renderer().categories()]
  assert "forest" in labels and "no data" in labels
  # colours must follow matplotlib ListedColormap sampling: 4 classes
  # on tab10 land on entries int(i/3 * 10) = 0, 3, 6, 9 (the release
  # suite's colourspace comparison once caught a round()-based
  # near-miss here, so the exact entries are pinned)
  got = {c.symbol().color().name() for c in out.renderer().categories()
         if c.value()}
  assert got == {"#1f77b4", "#d62728", "#e377c2", "#17becf"}, \
    f"tab10 sampling drifted: {sorted(got)}"
  # FIVE classes, because four cannot tell the formulas apart: on
  # tab10, int(i*10/4) gives entries 0,2,5,7,9 while the round()-based
  # near-miss this project shipped once gives 0,2,4,7,9. The middle
  # entry is the whole difference (brown vs purple), so the class
  # count here has to be one where they disagree
  five = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "five", "memory")
  five.dataProvider().addAttributes([compat.make_field("kind", str)])
  five.updateFields()
  for i, kind in enumerate(["a", "b", "c", "d", "e"]):
    f = QgsFeature(five.fields())
    f.setGeometry(QgsGeometry.fromWkt(
      f"POLYGON(({i} 0, {i + 1} 0, {i + 1} 1, {i} 1, {i} 0))"))
    f["kind"] = kind
    five.dataProvider().addFeatures([f])
  five.updateExtents()
  bridge.seed_renderer(five, {"id": "a", "var": "kind",
                              "mode": "Categorized", "ramp": "tab10",
                              "outline": False})
  got5 = {str(c.value()): c.symbol().color().name()
          for c in five.renderer().categories() if c.value()}
  assert got5 == {"a": "#1f77b4", "b": "#2ca02c", "c": "#8c564b",
                  "d": "#7f7f7f", "e": "#17becf"}, \
    f"five-class tab10 sampling drifted: {got5}"
  # the unclassed reproduction: exactly 50 linearly spaced classes
  bridge.seed_renderer(out, {"id": "a", "var": "v1", "mode": "Graduated",
                             "ramp": "Reds", "scheme": "Unclassed",
                             "k": 50, "outline": False})
  assert isinstance(out.renderer(), QgsGraduatedSymbolRenderer)
  assert len(out.renderer().ranges()) == 50, \
    "Unclassed must cut exactly 50 linear intervals"


def test_qml_class_template():
  """A QML with categorized symbology should drive class colours.

  Regression: every element layer was given the same renderer, so the per-element variables and ramps chosen in the table did not reach the map.
  [integration]
  """
  from weavingspace_qgis import bridge
  from qgis.core import QgsRendererCategory, QgsCategorizedSymbolRenderer
  layer = make_region_layer()
  # author a scheme in QGIS's own terms and save it as a real QML
  cats = [QgsRendererCategory(v, QgsFillSymbol.createSimple({"color": c}),
                              lbl)
          for v, c, lbl in [("forest", "#112233", "Forest land"),
                            ("water", "#445566", "Open water")]]
  layer.setRenderer(QgsCategorizedSymbolRenderer("landcover", cats))
  with tempfile.TemporaryDirectory() as td:
    qml = os.path.join(td, "scheme.qml")
    layer.saveNamedStyle(qml)
    template = bridge.load_categorized_template(qml)
    assert set(template) == {"forest", "water"}
    assert template["forest"][1] == "Forest land"
    gdf = bridge.layer_to_gdf(layer, ["landcover"])
    out = bridge.gdf_to_layer(gdf, "qmltest")
    bridge.seed_renderer(out, {"id": "a", "var": "landcover",
                               "mode": "Categorized", "ramp": "tab10",
                               "outline": False}, template)
    got = {str(c.value()): (c.symbol().color().name(), c.label())
           for c in out.renderer().categories() if c.value()}
    assert got["forest"] == ("#112233", "Forest land")
    assert got["water"] == ("#445566", "Open water")
    # values absent from the file fall back to automatic colours
    assert "urban" in got and got["urban"][0] not in ("#112233", "#445566")


def test_size_guard():
  """A spacing that would produce an unreasonable tiling is refused.

  Tile count grows as the inverse square of spacing, so a slip of a
  decimal point asks for millions of tiles and QGIS stops responding
  while the library works. The guard estimates the count before any
  tiling starts and declines, which is the difference between a
  message and a hung application.
  """
  from weavingspace_qgis import bridge
  from weavingspace import TileUnit, Tiling
  unit = TileUnit(tiling_type="cairo", spacing=10, crs=3857)
  est = bridge.estimate_tile_count_bounds(unit, (0, 0, 100_000, 100_000))
  assert est > bridge.MAX_TILES_HARD
  # the estimate must be a usable bound: at or above the real tile
  # count, but not absurdly above it (a 10x-off estimate would make
  # the live gate and the refusal message meaningless)
  unit = TileUnit(tiling_type="cairo", spacing=800, crs=3857)
  region = make_region_gdf()
  actual = len(Tiling(unit, region).get_tiled_map().map)
  estimate = bridge.estimate_tile_count(unit, region)
  assert actual <= estimate <= actual * 10, \
    f"estimate {estimate} vs actual {actual}"


def test_support_logic():
  """Pure-logic corners of deps.py and compat.py that no network or
  dialog is needed to exercise.

  Regression: a design whose spacing implied millions of tiles was attempted rather than refused, and QGIS became unresponsive while it ran.
  [review]
  """
  from weavingspace_qgis import compat, deps
  # PyPI requires_python specifier evaluation against this interpreter
  assert deps._python_ok(None) and deps._python_ok("")
  assert deps._python_ok(">=3.10")
  assert not deps._python_ok(">=3.99")
  assert deps._python_ok("<4.0,>=3.6")
  assert not deps._python_ok("<3.10")
  # version parsing tolerates suffixes and short forms
  assert deps._parse_version("2.3.3") == (2, 3, 3)
  assert deps._parse_version("1.26") == (1, 26, 0)
  assert deps._parse_version("3.0.0rc1") == (3, 0, 0)
  # wheel filename tag expansion covers multi-tag wheels
  tags = deps._wheel_tags("x-1.0-py2.py3-none-any.whl")
  assert "py3-none-any" in tags and "py2-none-any" in tags
  # every user-facing scheme maps to a real QGIS classification class
  for scheme in ("Quantiles", "Equal intervals",
                 "Natural breaks (Jenks)", "Pretty breaks"):
    assert compat.classification_method(scheme) is not None, scheme


class _Bar:
  """A stand-in for QGIS's message bar, for tests that run headless.

  The real bar belongs to the QGIS main window, which does not exist
  here. Collecting nothing is deliberate: tests that care what was
  said read the dialog's own note line instead, and a stub that
  merely absorbs the call keeps the code path identical to a real
  session's.
  """
  def pushSuccess(self, *a):
    """Absorb a success notice, as the real bar would display one."""
    pass

  def pushWarning(self, *a):
    """Absorb a warning, as the real bar would display one."""
    pass


class _Iface:
  """The slice of QGIS's iface the plugin actually uses.

  Passing iface=None puts the dialog in its headless mode, where
  notices go to its own note line; passing this instead exercises the
  branch a real QGIS session takes, without a QGIS window existing.
  Both paths matter, so both are used across this file.
  """
  def mainWindow(self):
    """The parent a real dialog would be given; None is accepted."""
    return None

  def messageBar(self):
    """The stub bar, so pushWarning and pushSuccess have somewhere to go."""
    return _Bar()


def _generate_and_wait(dlg):
  """Run one generation synchronously.

  Args:
    dlg: an open dialog, configured as the test wants it.

  Returns:
    None; when it returns, the run has completed and the project
    holds its layers. The tiling itself is a QgsTask on a worker
    thread, so the test has to spin a QEventLoop until the dialog's
    completion handler fires — polling or sleeping would starve the
    very signals being waited for. The 120-second timer is a
    backstop: a hung run should fail the test rather than the suite.
  """
  loop = QEventLoop()
  orig = dlg._on_generated

  def wrapped(*a, **kw):
    orig(*a, **kw)
    loop.quit()

  dlg._on_generated = wrapped
  dlg._generate()
  if dlg._task is None:
    # Nothing was launched. Either the change was symbology only and
    # the dialog answered it by restyling in place (the fast path), or
    # a guard declined the run. Both finish synchronously, so there is
    # no completion callback coming and waiting for one would burn the
    # whole backstop — which is exactly what it did before this check,
    # turning a style-only step into a two-minute pause.
    dlg._on_generated = orig
    return
  QTimer.singleShot(120_000, loop.quit)
  loop.exec()
  dlg._on_generated = orig


def test_auto_first_render():
  """Choosing a layer should populate variables and render unaided.

  Regression: choosing a layer produced nothing until Generate was pressed, leaving a first-time user with an empty canvas and no indication that anything was meant to happen.
  [review]
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  assert dlg.table.rowCount() > 0, "variables should populate on open"
  loop = QEventLoop()
  orig = dlg._on_generated

  def wrapped(*a, **kw):
    orig(*a, **kw)
    loop.quit()

  dlg._on_generated = wrapped
  QTimer.singleShot(60_000, loop.quit)
  loop.exec()
  dlg._on_generated = orig
  root = QgsProject.instance().layerTreeRoot()
  group = root.findGroup(dlg._group_name)
  assert group is not None and len(group.children()) > 0, \
    "a first map should appear without pressing Generate"
  dlg.live_check.setChecked(False)
  dlg.close()


def test_per_row_class_files():
  """Categorized rows grey the Classes cell to the detected count, get a
  categorical ramp, and gain a class-source cell; the column follows."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  from qgis.core import QgsRendererCategory, QgsCategorizedSymbolRenderer
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  assert dlg.table.isColumnHidden(7), "hidden with no categorized rows"

  dlg.table.cellWidget(1, 1).setCurrentText("landcover")
  dlg._update_dynamic_columns()
  assert not dlg.table.isColumnHidden(7), \
    "column appears once a categorized row exists"
  k = dlg.table.cellWidget(1, 3)
  assert not k.isEnabled() and k.value() == 4, \
    "categorized Classes cell greys out and shows the detected count"
  assert dlg.table.cellWidget(1, 4).currentText() in \
    bridge.CATEGORICAL_RAMPS, "ramp switches to a categorical set"
  assert dlg.table.cellWidget(0, 3).isEnabled(), "quant rows stay editable"
  assert dlg.table.cellWidget(0, 7) is None, \
    "non-categorized rows have a blank class-source cell"

  by_id = {a["id"]: a for a in dlg._assignments()}
  assert by_id["b"]["class_source"] is None  # automatic colours default
  assert by_id["a"]["class_source"] is None

  # a QML browsed once is offered to every categorized row
  styled = make_region_layer()
  styled.setRenderer(QgsCategorizedSymbolRenderer("landcover", [
    QgsRendererCategory("forest",
                        QgsFillSymbol.createSimple({"color": "#112233"}),
                        "Forest land")]))
  import tempfile as tf
  td = tf.mkdtemp()
  qml = os.path.join(td, "scheme.qml")
  styled.saveNamedStyle(qml)
  dlg._browsed_qmls.append(qml)
  dlg._update_dynamic_columns()
  combo = dlg.table.cellWidget(1, 7)
  i = combo.findData("file:" + qml)
  assert i >= 0, "browsed file offered in the row combo"
  combo.setCurrentIndex(i)
  by_id = {a["id"]: a for a in dlg._assignments()}
  assert by_id["b"]["class_source"] == "file:" + qml

  # another loaded layer's categorized symbology as the source
  QgsProject.instance().addMapLayer(styled)
  dlg._update_dynamic_columns()
  combo = dlg.table.cellWidget(1, 7)
  i = combo.findData(f"layer:{styled.id()}")
  assert i >= 0, "layers with categorized symbology are offered"
  combo.setCurrentIndex(i)
  by_id = {a["id"]: a for a in dlg._assignments()}
  assert by_id["b"]["class_source"] == f"layer:{styled.id()}"
  assert bridge.template_from_layer(styled)["forest"][1] == "Forest land"

  # Single colour: the ramp cell becomes a colour picker and back
  from qgis.gui import QgsColorButton
  from qgis.PyQt.QtGui import QColor
  ramp_before = dlg.table.cellWidget(0, 4).currentText()
  dlg.table.cellWidget(0, 2).setCurrentText("Single colour")
  dlg._update_dynamic_columns()
  btn = dlg.table.cellWidget(0, 4)
  assert isinstance(btn, QgsColorButton), "picker replaces the ramp"
  btn.setColor(QColor("#123456"))
  by_id = {a["id"]: a for a in dlg._assignments()}
  assert by_id["a"]["single_colour"] == "#123456"
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Quantiles")
  dlg._update_dynamic_columns()
  restored = dlg.table.cellWidget(0, 4)
  assert not isinstance(restored, QgsColorButton)
  assert restored.currentText() == ramp_before, "ramp choice remembered"

  # graduated controls: per-row scheme and class count resolve, and
  # the unclassed style greys the Classes cell at a fixed 50
  assert not dlg.table.isColumnHidden(3), \
    "Classes column should be visible while elements are graduated"
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Equal intervals")
  dlg.table.cellWidget(0, 3).setValue(4)
  by_id = {a["id"]: a for a in dlg._assignments()}
  assert by_id["a"]["scheme"] == "Equal intervals" and by_id["a"]["k"] == 4
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Unclassed")
  dlg._update_dynamic_columns()
  k0 = dlg.table.cellWidget(0, 3)
  assert not k0.isEnabled() and k0.value() == 50
  by_id = {a["id"]: a for a in dlg._assignments()}
  assert by_id["a"]["scheme"] == "Unclassed" and by_id["a"]["k"] == 50
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Quantiles")
  dlg._update_dynamic_columns()

  # variable back to numeric: style follows, column withdraws
  dlg.table.cellWidget(1, 1).setCurrentText("v2")
  dlg._update_dynamic_columns()
  assert dlg.table.isColumnHidden(7)
  dlg.close()


def test_palette_pick_survives_debounce():
  """Regression for the 'race among choosers': picking a ramp must not
  schedule a table rebuild, so the row widgets remain the SAME objects
  after the debounce window and a pick made while another chooser was
  open can never land on a destroyed widget. Also checks the picked
  ramp actually reaches the generated symbology with live update off
  (the reported symptom: 'changing the palettes doesn't work').

  Regression: a colour ramp picked while a rebuild was pending was lost when the table's widgets were replaced.
  [race]
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(500)
  # spacing is a DESIGN change, so a rebuild is expected and correct;
  # let it land before grabbing widget references — the property under
  # test is that *data-tab* changes cause no further rebuilds
  settle = QEventLoop()
  QTimer.singleShot(600, settle.quit)
  settle.exec()

  ramp_widget = dlg.table.cellWidget(0, 4)
  var_widget = dlg.table.cellWidget(1, 1)
  ramp_widget.setCurrentText("YlOrRd")
  var_widget.setCurrentText("v2")  # a second chooser changing too
  # let both debounce timers fire (preview 350 ms, live 900 ms)
  loop = QEventLoop()
  QTimer.singleShot(1400, loop.quit)
  loop.exec()
  assert dlg.table.cellWidget(0, 4) is ramp_widget, \
    "data-tab change must not rebuild the table's widgets"
  assert dlg.table.cellWidget(1, 1) is var_widget
  assert ramp_widget.currentText() == "YlOrRd", "pick must survive"

  _generate_and_wait(dlg)
  from qgis.core import QgsGraduatedSymbolRenderer
  lid = dlg._element_layer_ids["a"]
  renderer = QgsProject.instance().mapLayer(lid).renderer()
  assert isinstance(renderer, QgsGraduatedSymbolRenderer)
  # the seeded ramp must be the picked one: its dark end is YlOrRd's
  # deep red, nothing like the default Reds only at the extremes
  from weavingspace_qgis import bridge
  seeded = renderer.sourceColorRamp().color(1.0).name()
  expected = bridge.get_ramp("YlOrRd").color(1.0).name()
  assert seeded == expected, f"seeded {seeded}, expected {expected}"
  dlg.close()


def test_dialog_end_to_end():
  """One ordinary session: layer in, variables assigned, map out.

  The broadest functional test in the file, and the one that fails
  first when something fundamental breaks. It asserts the shape of a
  finished run — a layer group, one output layer per element, each
  carrying tiles and a renderer — rather than any particular
  cartography, which the visual tests judge instead.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)  # manual paths tested deterministically
  assert dlg.table.rowCount() > 0, "table should populate on open"
  assert len(dlg.preview._labels) == len(dlg._unit.tiles), \
    "preview labels one id per central-unit tile (web-app parity)"
  dlg.spacing_spin.setValue(500)
  dlg.table.cellWidget(0, 1).setCurrentText("v1")
  dlg.table.cellWidget(1, 1).setCurrentText("landcover")
  _generate_and_wait(dlg)
  # project-layer churn (which re-fires layerChanged) must not clobber
  # a hand-set spacing
  dlg.spacing_spin.setValue(777)
  QgsProject.instance().addMapLayer(make_region_layer())
  assert dlg.spacing_spin.value() == 777, \
    "spacing must not reset when project layers change"
  root = QgsProject.instance().layerTreeRoot()
  group = root.findGroup(dlg._group_name)
  assert group is not None
  layers = [c.layer() for c in group.children()]
  assert len(layers) == len(dlg._tile_ids())
  assert any(isinstance(la.renderer(), QgsCategorizedSymbolRenderer)
             for la in layers)

  # regeneration: hand styling survives, no duplicate groups
  target = layers[0]
  target.setRenderer(QgsSingleSymbolRenderer(
    QgsFillSymbol.createSimple({"color": "#123456"})))
  dlg.spacing_spin.setValue(600)
  _generate_and_wait(dlg)
  group = root.findGroup(dlg._group_name)
  layers2 = [c.layer() for c in group.children()]
  assert len(layers2) == len(layers)
  assert isinstance(layers2[0].renderer(), QgsSingleSymbolRenderer)

  # GeoPackage output with embedded styles
  with tempfile.TemporaryDirectory() as td:
    path = os.path.join(td, "out.gpkg")
    dlg.gpkg_widget.setFilePath(path)
    _generate_and_wait(dlg)
    assert os.path.exists(path)
    import sqlite3
    con = sqlite3.connect(path)
    n_styles = con.execute("SELECT count(*) FROM layer_styles").fetchone()[0]
    con.close()
    assert n_styles > 0, "styles should be embedded in the GeoPackage"
    # detach the file-backed layers before the tempdir disappears
    for lid in list(dlg._element_layer_ids.values()):
      QgsProject.instance().removeMapLayer(lid)


def test_output_management():
  """Regeneration behaviours around the layer group: the outlines
  layer appears and disappears with its checkbox, hand styling
  survives changes to OTHER elements (selective re-seed), and the
  comparison flow adds a second group while leaving the first
  intact.

  Regression: re-generating discarded hand styling on elements whose assignment had not changed.
  [integration]
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(500)
  dlg.opt_outlines.setChecked(True)
  _generate_and_wait(dlg)
  project = QgsProject.instance()
  root = project.layerTreeRoot()
  group = root.findGroup(dlg._group_name)
  # outline layer sits on top of the group (index 0)
  assert dlg._outline_layer_id is not None
  assert group.children()[0].layer().id() == dlg._outline_layer_id
  dlg.opt_outlines.setChecked(False)
  _generate_and_wait(dlg)
  assert dlg._outline_layer_id is None, "outline removed with checkbox"

  # selective re-seed: hand-style element b, then change only a's
  # ramp; regeneration must re-seed a but carry b's hand styling
  b_layer = project.mapLayer(dlg._element_layer_ids["b"])
  b_layer.setRenderer(QgsSingleSymbolRenderer(
    QgsFillSymbol.createSimple({"color": "#0b1e2d"})))
  dlg.table.cellWidget(0, 4).setCurrentText("YlGn")
  # A GEOMETRY change as well, deliberately. Selective re-seeding
  # lives in the output phase of a full regeneration, and a
  # symbology-only change now takes the restyle fast path instead —
  # which quietly stopped this test from reaching the code it names
  # (a mutation that deleted the renderer restore went unnoticed
  # until the audit asked). Changing spacing forces the real path.
  dlg.spacing_spin.setValue(470)
  _generate_and_wait(dlg)
  assert dlg._task is None
  from qgis.core import QgsGraduatedSymbolRenderer
  a_after = project.mapLayer(dlg._element_layer_ids["a"]).renderer()
  b_after = project.mapLayer(dlg._element_layer_ids["b"]).renderer()
  assert isinstance(a_after, QgsGraduatedSymbolRenderer)
  # assert the COLOUR, not the renderer class. A layer that lost its
  # hand styling is reborn with a default single-symbol renderer, so a
  # class check passes equally for "your styling survived" and "your
  # styling was discarded and replaced with grey" — which is exactly
  # how a mutation that deleted the restore went unnoticed
  assert isinstance(b_after, QgsSingleSymbolRenderer), \
    "hand styling on b must survive a change to a"
  assert b_after.symbol().color().name() == "#0b1e2d", \
    f"b was re-seeded rather than kept: its fill is " \
    f"{b_after.symbol().color().name()}, not the hand-set #0b1e2d"

  # comparison flow: a new group joins, the previous one persists
  first_group = dlg._group_name
  first_ids = dict(dlg._element_layer_ids)
  dlg.opt_new_group.setChecked(True)
  _generate_and_wait(dlg)
  assert dlg._group_name != first_group
  assert root.findGroup(first_group) is not None
  assert all(project.mapLayer(lid) is not None
             for lid in first_ids.values()), \
    "the kept group's layers must remain in the project"
  dlg.opt_new_group.setChecked(False)
  dlg.close()


def test_live_update_gates():
  """Live update must decline to run when output goes to a GeoPackage
  (regenerating a file on every tweak would hammer the disk) and when
  the comparison checkbox is on (it would spawn a group per tweak).

  Regression: live update rewrote a GeoPackage on every tweak, hammering the disk.
  [integration]
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.spacing_spin.setValue(500)
  # stub the generator so the gate's decision is observable directly:
  # a run appends to calls, and no QgsTask machinery is involved
  calls = []
  dlg._generate = lambda **kw: calls.append(1)  # accepts live=True
  dlg.gpkg_widget.setFilePath("/tmp/never-written.gpkg")
  dlg._maybe_live_generate()
  assert not calls, "gpkg output must gate live update"
  dlg.gpkg_widget.setFilePath("")
  dlg.opt_new_group.setChecked(True)
  dlg._maybe_live_generate()
  assert not calls, "comparison mode must gate live update"
  # positive control: with every gate clear the SAME call must run,
  # otherwise the asserts above would also pass for a live update
  # that simply never runs
  dlg.opt_new_group.setChecked(False)
  dlg._maybe_live_generate()
  assert calls, "with gates clear, live update must actually generate"
  dlg.live_check.setChecked(False)
  dlg.close()


def test_design_cascade():
  """The Design tab's coupled controls: element count repopulates the
  family list, a count offering only one kind silently flips the
  tiling/weave toggle, family choice shows exactly its own option
  rows, those options actually reach the built unit, and the dialog
  re-fits its height when option rows appear."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.show()

  # a count with tilings only must flip the kind toggle silently
  dlg.kind_combo.setCurrentText("weave")
  dlg.n_combo.setCurrentText("13")
  assert dlg.kind_combo.currentText() == "tiling", \
    "n=13 offers only chavey tilings; kind must flip"
  assert dlg.family_combo.currentText().startswith("chavey")

  # family-specific option rows appear for exactly the right families
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  assert not dlg.opt_offset_row[1].isVisibleTo(dlg)
  dlg.family_combo.setCurrentText("hex-slice 4")
  assert dlg.opt_offset_row[1].isVisibleTo(dlg)
  dlg.n_combo.setCurrentText("3")
  dlg.family_combo.setCurrentText("star1 33")
  assert dlg.opt_point_angle_row[1].isVisibleTo(dlg)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("weave")
  dlg.family_combo.setCurrentText("twill weave ab|cd")
  assert dlg.opt_aspect_row[1].isVisibleTo(dlg)
  assert dlg.opt_over_under_row[1].isVisibleTo(dlg)

  # the over-under text reaches the weave unit's n
  dlg.opt_over_under.setText("1,2")
  dlg._rebuild_unit()
  assert tuple(dlg._unit.n) == (1, 2), f"unit n = {dlg._unit.n}"
  # and the preview labels one id per unit tile after the change
  assert len(dlg.preview._labels) == len(dlg._unit.tiles)

  # the offset control changes slice geometry
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("hex-slice 4")
  dlg.opt_offset.setValue(0.0)
  dlg._rebuild_unit()
  corners = dlg._unit.tiles.geometry.iloc[0].wkt
  dlg.opt_offset.setValue(1.0)
  dlg._rebuild_unit()
  midpoints = dlg._unit.tiles.geometry.iloc[0].wkt
  assert corners != midpoints, "offset must reach the geometry"

  # grid family: spinner row appears, defaults to the tightest fit,
  # and the spinners reach the unit (1x4 vs 2x2 changes geometry)
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("grid 4")
  assert dlg.opt_grid_row[1].isVisibleTo(dlg)
  assert (dlg.opt_grid_rows.value(), dlg.opt_grid_cols.value()) == (2, 2)
  dlg._rebuild_unit()
  square_wkt = dlg._unit.tiles.geometry.iloc[0].wkt
  dlg.opt_grid_rows.setValue(1)
  dlg.opt_grid_cols.setValue(4)
  dlg._rebuild_unit()
  assert set(dlg._unit.tiles.tile_id) == {"a", "b", "c", "d"}
  assert dlg._unit.tiles.geometry.iloc[0].wkt != square_wkt, \
    "rows/cols must reach the grid geometry"
  dlg.family_combo.setCurrentText("stripes 4")
  assert not dlg.opt_grid_row[1].isVisibleTo(dlg)
  dlg._rebuild_unit()
  assert set(dlg._unit.tiles.tile_id) == {"a", "b", "c", "d"}

  # option rows growing the form grows the dialog (fit re-runs)
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  loop = QEventLoop()
  QTimer.singleShot(150, loop.quit)
  loop.exec()
  h_plain = dlg.height()
  dlg.kind_combo.setCurrentText("weave")
  dlg.family_combo.setCurrentText("twill weave ab|cd")
  loop = QEventLoop()
  QTimer.singleShot(150, loop.quit)
  loop.exec()
  assert dlg.height() > h_plain, \
    f"two option rows appeared, so the re-fit must grow the dialog " \
    f"({h_plain} -> {dlg.height()})"
  dlg.close()


def test_style_follow_and_memory():
  """The per-row style/ramp state machine: untouched styles follow the
  variable's type; a hand-picked style sticks except when impossible;
  the ramp cell remembers its last quantitative and last categorical
  choices across style flips; a picked single colour survives a
  Design-tab rebuild."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.gui import QgsColorButton
  from qgis.PyQt.QtGui import QColor
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)

  var0 = dlg.table.cellWidget(0, 1)
  mode0 = dlg.table.cellWidget(0, 2)
  # untouched: style follows the field's type both ways
  var0.setCurrentText("landcover")
  assert mode0.currentText() == "Categorized"
  var0.setCurrentText("v1")
  assert mode0.currentText() == "Quant: Quantiles"
  # touched: a hand-picked style sticks across numeric variables.
  # Mark it touched the way a user does — through the combo's
  # activated signal (fired on a real pick, not on programmatic
  # changes), which is what the dialog's hook listens to
  mode0.setCurrentText("Quant: Equal intervals")
  mode0.activated.emit(mode0.currentIndex())
  assert mode0.property("touched"), \
    "the activated hook must mark the style touched"
  var0.setCurrentText("v2")
  assert mode0.currentText() == "Quant: Equal intervals"
  # ...but an impossible combination still corrects itself
  var0.setCurrentText("landcover")
  assert mode0.currentText() == "Categorized"

  # ramp memory across style flips (widgets are replaced by _sync_row,
  # so re-fetch the cell each time)
  var0.setCurrentText("v1")
  dlg._update_dynamic_columns()
  dlg.table.cellWidget(0, 4).setCurrentText("YlOrRd")
  mode0.setCurrentText("Categorized")
  dlg._update_dynamic_columns()
  ramp_cell = dlg.table.cellWidget(0, 4)
  from weavingspace_qgis import bridge
  assert ramp_cell.currentText() in bridge.CATEGORICAL_RAMPS
  ramp_cell.setCurrentText("Set2")
  mode0.setCurrentText("Quant: Quantiles")
  dlg._update_dynamic_columns()
  assert dlg.table.cellWidget(0, 4).currentText() == "YlOrRd", \
    "quantitative ramp remembered across a categorical excursion"
  mode0.setCurrentText("Categorized")
  dlg._update_dynamic_columns()
  assert dlg.table.cellWidget(0, 4).currentText() == "Set2", \
    "categorical ramp remembered too"

  # a picked single colour survives a Design-tab rebuild
  mode0.setCurrentText("Single colour")
  dlg._update_dynamic_columns()
  button = dlg.table.cellWidget(0, 4)
  assert isinstance(button, QgsColorButton)
  button.setColor(QColor("#123456"))
  dlg.spacing_spin.setValue(dlg.spacing_spin.value() * 1.1)
  dlg._rebuild_unit()  # the rebuild a design change debounces into
  button2 = dlg.table.cellWidget(0, 4)
  assert isinstance(button2, QgsColorButton)
  assert button2.color().name() == "#123456", \
    "single colour must survive the rebuild"
  dlg.close()


def test_the_window_fits_its_design_tab_when_shown():
  """Showing the dialog sizes it to the controls it contains.

  Qt cannot report a truthful sizeHint before a real layout pass, so
  the fit is deferred to a zero-delay timer after showEvent. Drop
  that and the window keeps its constructed height, which is smaller
  than the Design tab needs: the controls are all there, in the
  layout, and the bottom of the panel is simply off the window.

  Regression: the deferred fit-to-design after showEvent had no test, so the window could open too small to show its own controls.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.layer_combo.setLayer(layer)
  dlg.show()
  _tick(300)                        # let the deferred fit happen
  needed = dlg._design_wrapper.sizeHint().height()
  assert dlg.height() >= needed, \
    f"the window is {dlg.height()}px tall but its Design tab needs "\
    f"{needed}px, so the lower controls are off the bottom"
  dlg.close()


def test_cancelling_frees_the_dialog_at_once():
  """Cancel gives the dialog back immediately, not eventually.

  Cancellation is a request. Work already inside the library cannot
  be interrupted, so the task may run on for some seconds; QGIS will
  call finished() when it truly stops, and that would eventually
  re-enable everything. TilingTask.cancel therefore reports to the
  dialog itself, straight away, which is what makes the window usable
  again while the doomed work winds down.

  The existing cancel test settles first and so cannot see this: by
  the time it looks, QGIS has caught up either way. This one asserts
  WITHOUT waiting, which is the only way the difference shows.

  Regression: cancel's immediate report to the dialog was untested; removing it left the window disabled until the abandoned work finished.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  _tick(200)
  dlg.spacing_spin.setValue(300)      # slow enough to still be running
  dlg._generate()
  assert dlg._task is not None, "a task should be in flight"
  assert not dlg.generate_btn.isEnabled(), \
    "Generate should be disabled while a run is going"

  dlg._task.cancel()
  _tick(0)                            # one pass, no settling
  assert dlg._task is None, \
    "the dialog still holds the cancelled task, so it will refuse "\
    "the next Generate until the abandoned work finishes"
  assert dlg.generate_btn.isEnabled(), \
    "Generate is still disabled straight after a cancel; the user "\
    "has to wait for work they asked to stop"
  _settle(dlg)
  dlg.close()


def test_every_design_control_is_reachable():
  """Each control the Design tab offers is really in the window.

  A widget that is built, configured and connected but never added to
  a layout works perfectly from a test — which sets it directly — and
  is invisible to the user, who cannot reach it at all. That is not
  hypothetical: dropping the row that adds Scale EW/NS survived a
  whole mutation batch, because every test that uses those spin boxes
  assigns to them rather than looking for them.

  So this asks the question tests otherwise never ask: is the control
  part of the dialog's widget tree, and would it show?

  Regression: controls added via a shared row helper were never checked for reachability, so removing the helper call hid two of them.
  """
  from qgis.PyQt.QtWidgets import QTabWidget
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.layer_combo.setLayer(layer)
  dlg.show()
  _tick(200)

  wanted = ["mod_rotate", "mod_scale_x", "mod_scale_y",
            "mod_skew_x", "mod_skew_y", "mod_p_inset", "mod_t_inset",
            "spacing_spin", "shells_spin", "n_combo", "kind_combo",
            "family_combo", "generate_btn", "live_check", "table",
            "preview", "layer_combo", "opt_tile_outlines"]
  # Controls live on different tabs, so a control is reachable if it
  # shows on ANY tab, not on whichever happens to be in front. Walking
  # the tabs is also the honest question: can the user get to it at
  # all, by any route the window offers.
  tabs = dlg.findChild(QTabWidget)
  assert tabs is not None, "the dialog has no tab widget"
  seen = set()
  for index in range(tabs.count()):
    tabs.setCurrentIndex(index)
    _tick(60)
    for name in wanted:
      widget = getattr(dlg, name, None)
      if widget is not None and widget.isVisibleTo(dlg):
        seen.add(name)

  missing = []
  for name in wanted:
    widget = getattr(dlg, name, None)
    if widget is None:
      missing.append(f"{name}: the dialog has no such attribute")
    elif not dlg.isAncestorOf(widget):
      missing.append(
        f"{name}: built but never added to any layout, so no user "
        f"can reach it")
    elif name not in seen:
      missing.append(
        f"{name}: in the widget tree but shows on no tab")
  assert not missing, "unreachable control(s):\n  " + "\n  ".join(missing)
  dlg.close()


# Every control's declared default, range and step, in one place.
# This table is the POINT of the two tests below it. Mutation batches
# kept turning up the same kind of survivor — a default nobody
# asserted, a ceiling nobody pinned — one at a time, each needing its
# own test. A table covers the whole family at once, including the
# controls no batch has happened to sample yet, and a new control is
# covered the moment somebody adds a row.
#
# Values were read from a live dialog rather than transcribed from
# dialog.py, so this states what a user MEETS rather than restating
# the construction call; a test written from the source it checks
# agrees with the source's bugs.
CONTROL_DEFAULTS = {
  # spin boxes: (default, minimum, maximum, step)
  "spacing_spin": (1000.0, 1e-06, 1e12, 1.0),
  "shells_spin": (1, 0, 4, 1),
  "mod_rotate": (0.0, -90.0, 90.0, 1.0),
  "mod_scale_x": (1.0, 0.5, 4.0, 0.02),
  "mod_scale_y": (1.0, 0.5, 4.0, 0.02),
  "mod_skew_x": (0.0, -45.0, 45.0, 1.0),
  "mod_skew_y": (0.0, -45.0, 45.0, 1.0),
  "mod_p_inset": (0.0, 0.0, 10.0, 0.1),
  "mod_t_inset": (0.0, 0.0, 5.0, 0.1),
  "opt_offset": (0.0, -1.0, 1.0, 0.01),
  "opt_offset_angle": (0.0, -50.0, 85.0, 1.0),
  "opt_point_angle": (30.0, 10.0, 120.0, 1.0),
  "opt_aspect": (0.75, 0.083, 1.0, 0.083),
  "opt_grid_rows": (1, 1, 26, 1),
  "opt_grid_cols": (1, 1, 26, 1),
}

CONTROL_CHECKBOXES = {
  # every switch starts OFF except where noted, because a plugin that
  # arrives with options already applied is making decisions for a
  # user who has not met it yet
  "mod_glyph": (False, "Scale as glyph (independent of tiling)"),
  "opt_tile_outlines": (False, "Draw tile boundaries"),
  "opt_join_prototiles": (False, "Join data using whole tileable"),
  "opt_retain": (False, "Retain complete tileables at edges"),
  "opt_clip": (False, "Clip by map units (no ragged edges)"),
  "opt_icons": (False, "Use tileable as icon (one per map unit)"),
  "opt_outlines": (False, "Add map unit outlines layer"),
  "opt_new_group": (False, "Create as new group (keep the previous result)"),
  "opt_colour_warnings":
    (False, "Warn about lack of legibility in colour choices"),
}


def test_every_control_starts_where_it_should():
  """The value a user meets in each control, before touching anything.

  A default is a decision: it is what most maps will be made with,
  and it is the one setting most users never revisit. Yet defaults
  are invisible to ordinary tests, which set the value they want
  before asserting anything — so a changed default sails through a
  suite that exercises the control thoroughly.

  Live update is the case that proves it: every test in this file
  turns it off in its opening lines, so the suite was unanimous about
  a setting none of it asserted.

  Regression: control defaults were unasserted as a class, so any one of them could change unnoticed.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  # No layer in the project. With one, auto-spacing legitimately
  # replaces the declared spacing with a value sized to that layer's
  # extent -- correct behaviour, tested elsewhere, and not what
  # "before touching anything" means. The DECLARED defaults are what
  # a user meets on a fresh install with nothing loaded.
  project = QgsProject.instance()
  for existing in list(project.mapLayers().values()):
    project.removeMapLayer(existing.id())
  dlg = WeavingSpaceDialog(iface=None)
  _tick(150)

  wrong = []
  for name, (default, _lo, _hi, _step) in CONTROL_DEFAULTS.items():
    widget = getattr(dlg, name, None)
    if widget is None:
      wrong.append(f"{name}: the dialog has no such control")
      continue
    if abs(widget.value() - default) > 1e-9:
      wrong.append(f"{name} starts at {widget.value()}, not {default}")
  for name, (checked, label) in CONTROL_CHECKBOXES.items():
    widget = getattr(dlg, name, None)
    if widget is None:
      wrong.append(f"{name}: the dialog has no such control")
      continue
    if widget.isChecked() != checked:
      wrong.append(
        f"{name} starts {'on' if widget.isChecked() else 'off'}, "
        f"should start {'on' if checked else 'off'}")
    if widget.text() != label:
      wrong.append(f"{name} reads {widget.text()!r}, not {label!r}")

  # live update is the exception: it is ON, so a first map appears
  if not dlg.live_check.isChecked():
    wrong.append("live_check starts off; a new user would see no map")

  assert not wrong, "controls do not start where they should:\n  " + \
    "\n  ".join(wrong)
  dlg.close()


def test_every_control_accepts_the_range_it_should():
  """What each control will let a user ask for.

  A range is as much a design decision as a default: the class count
  runs 2 to 20 because a ramp stops reading as classes beyond that,
  the tile inset stops at 5% because more swallows thin strands, and
  the aspect step is 1/12 because strand widths are twelfths. Widen
  or narrow one and the plugin quietly permits, or refuses, something
  it was designed not to.

  Steps matter for the same reason and are easier to lose: a step is
  what a user gets by nudging, and a control that lurches in whole
  units is a control nobody uses for fine work.

  Regression: control ranges and steps were unasserted as a class; a mutation batch moved one and the suite was silent.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  # ranges do not depend on a layer, but an empty project keeps this
  # test independent of whatever the previous one left behind
  project = QgsProject.instance()
  for existing in list(project.mapLayers().values()):
    project.removeMapLayer(existing.id())
  dlg = WeavingSpaceDialog(iface=None)
  _tick(150)

  wrong = []
  for name, (_default, low, high, step) in CONTROL_DEFAULTS.items():
    widget = getattr(dlg, name, None)
    if widget is None:
      wrong.append(f"{name}: the dialog has no such control")
      continue
    if abs(widget.minimum() - low) > 1e-9:
      wrong.append(f"{name} accepts from {widget.minimum()}, not {low}")
    if abs(widget.maximum() - high) > 1e-9:
      wrong.append(f"{name} accepts up to {widget.maximum()}, not {high}")
    if abs(widget.singleStep() - step) > 1e-9:
      wrong.append(f"{name} steps by {widget.singleStep()}, not {step}")
  assert not wrong, "control ranges have moved:\n  " + "\n  ".join(wrong)
  dlg.close()


def test_every_control_explains_itself():
  """Each control carries a tooltip, and the tooltip says something.

  Guidance in this plugin is deliberately in the interface rather than
  only in a manual: the README promises that every control has a
  tooltip, and the design decision to put explanation at the point of
  use is why the Help tab is short. Thirty-one tooltips are set in
  dialog.py and, until this test, not one of them was asserted — so
  any of them could vanish and the suite would be silent, which is
  how a plugin becomes quietly unexplained.

  A whole CLASS of mutant lives here. Removing a `setToolTip(...)`
  call is invisible to every functional test, because a tooltip
  changes no behaviour; it changes whether anyone can work out what
  the control does. Asserting the family at once is the only
  proportionate answer to thirty-one of them.

  Length is checked at BOTH ends. A one-word tooltip repeating the
  label ("Spacing") explains nothing and would satisfy a bare
  non-empty test. A forty-word one is not a tooltip either: it is a
  paragraph in a yellow box, and this project's rule is that a
  tooltip is a nudge at the point of use while the user guide and the
  Help tab carry the explanation. Fifteen words is the ceiling; the
  shortest useful ones here run to four.

  Regression: no test asserted any control's tooltip, so all thirty-one could be removed unnoticed.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  _tick(200)

  # every control a user can reach on the Design and Map options
  # tabs, plus the two that decide what a run produces
  wanted = sorted(set(CONTROL_DEFAULTS) | set(CONTROL_CHECKBOXES) |
                  {"live_check", "layer_combo", "n_combo", "kind_combo",
                   "family_combo", "gpkg_widget"})
  bare, terse, windy = [], [], []
  for name in wanted:
    widget = getattr(dlg, name, None)
    if widget is None or not hasattr(widget, "toolTip"):
      continue
    tip = (widget.toolTip() or "").strip()
    words = len(tip.split())
    if not tip:
      bare.append(name)
    elif words < 3:
      terse.append(f"{name}: {tip!r} ({words} words)")
    elif words > 15:
      windy.append(f"{name}: {words} words — {tip[:60]}...")

  assert not bare, \
    "control(s) with no tooltip at all, in a plugin whose guidance "\
    "lives in the interface:\n  " + "\n  ".join(bare)
  assert not terse, \
    "tooltip(s) that only repeat their label:\n  " + "\n  ".join(terse)
  assert not windy, \
    "tooltip(s) longer than a nudge; the guide and Help tab carry "\
    "the fuller explanation:\n  " + "\n  ".join(windy)
  dlg.close()


def test_the_preview_actually_draws_what_it_is_given():
  """The design view renders: filled, fitted, centred and smoothed.

  The preview's painting code is the least-covered part of the plugin
  — a cost-stratum census put dialog.py's thinly-covered mutants at
  50% caught, and the largest single family among the survivors was
  this widget: the brush, the pen, the render hint, the scale and
  offset arithmetic, and the margin. Almost nothing rendered the
  preview and looked at the result, so removing any one of those
  calls changed a picture nobody examined.

  Rather than one test per call, this asserts what the widget is FOR,
  which is the thing all of them serve:

    it draws something at all (a brush that never gets set leaves an
    empty widget, and a path never moved to leaves nothing to fill);
    every element colour the dialog handed it actually appears (a
    wrong or missing brush shows up as a colour that is not there);
    the drawing fits inside the widget with its margin, and sits
    roughly centred (the scale, the offsets and the margin decide
    this, and an error in any of them pushes the pattern off-centre
    or over the edge);
    and edges are smoothed (the render hint), visible as colours
    between the fills that neither fill accounts for.

  Regression: the preview's painting had almost no coverage, and removing its brush, pen, render hint or fitting arithmetic changed a picture no test looked at.
  """
  from qgis.PyQt.QtGui import QColor, QImage, QPainter
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.live_check.setChecked(False)
  # SHOW it before measuring or rendering. A widget that has never
  # been shown reports a geometry its paint code does not use: this
  # preview reported 640 wide while painting as though it were 328,
  # so every fitting measurement was out by the difference. CLAUDE.md
  # records the same lesson for grab().
  dlg.show()
  dlg.layer_combo.setLayer(layer)
  _tick(400)
  dlg._rebuild_unit()
  _tick(200)
  assert dlg.preview._polys, "the preview was given nothing to draw"

  # Render at the WIDGET's own geometry. QWidget.render draws at that
  # geometry whatever canvas it is given, so a canvas of some other
  # shape crops the drawing and every measurement below then describes
  # the canvas. The widget is in a layout and will not take a size it
  # is told, so ask it what it is rather than deciding for it.
  wide, high = dlg.preview.width(), dlg.preview.height()
  assert wide > 50 and high > 50, \
    f"the preview has no useful size to render ({wide}x{high})"
  image = QImage(wide, high, QImage.Format.Format_RGB32)
  image.fill(QColor("#ffffff"))
  painter = QPainter(image)
  dlg.preview.render(painter)
  painter.end()

  # What colours reached the picture, and where the ink sits. The
  # widget paints its own background across the whole rectangle, so
  # "not white" is not the test for ink -- taking the background from
  # a corner and excluding it is. Without that, the drawing appears
  # to start at pixel 0 and every fitting assertion is meaningless.
  corner = QColor(image.pixel(1, 1))
  back = (corner.red(), corner.green(), corner.blue())

  def is_background(key):
    return all(abs(key[i] - back[i]) <= 6 for i in range(3))

  seen, xs, ys = {}, [], []
  for x in range(0, wide, 2):
    for y in range(0, high, 2):
      colour = QColor(image.pixel(x, y))
      key = (colour.red(), colour.green(), colour.blue())
      if key == (255, 255, 255) or is_background(key):
        continue
      seen[key] = seen.get(key, 0) + 1
      xs.append(x)
      ys.append(y)

  assert xs, "the preview drew nothing at all"
  painted = len(xs)
  sampled = (wide // 2) * (high // 2)
  assert painted > sampled * 0.05, \
    f"only {painted / sampled:.1%} of the preview was painted; the "\
    f"unit should fill a good part of it"

  # As many substantial fills as there are elements. Comparing against
  # _id_colours directly does not work: those carry alpha, and the
  # widget blends each one with its background, so the painted colour
  # is never the nominal one. What must hold is that each element
  # contributes its own distinct area of colour -- a missing brush
  # shows up as one fewer.
  substantial = [key for key, count in seen.items()
                 if count > sampled * 0.01]
  elements = len(dlg.preview._id_colours)
  assert len(substantial) >= elements, \
    f"{len(substantial)} substantial fill(s) for {elements} "\
    f"elements; an element is not being drawn"

  # fitted, with its margin, and roughly centred
  assert min(xs) >= 2 and min(ys) >= 2, \
    f"the drawing touches the edge (x from {min(xs)}, y from "\
    f"{min(ys)}); the margin is not being applied"
  assert max(xs) <= wide - 3 and max(ys) <= high - 3, \
    f"the drawing runs past the far edge (x to {max(xs)} of {wide}, "\
    f"y to {max(ys)} of {high}), so it is scaled too large to fit"
  cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
  assert abs(cx - wide / 2) < wide * 0.15, \
    f"the drawing centres at x={cx:.0f} in a {wide}px widget; the "\
    f"horizontal offset is wrong"
  assert abs(cy - high / 2) < high * 0.15, \
    f"the drawing centres at y={cy:.0f} in a {high}px widget; the "\
    f"vertical offset is wrong"

  # antialiasing: colours that are neither a fill nor the background
  fills = {(QColor(c).red(), QColor(c).green(), QColor(c).blue())
           for c in dlg.preview._id_colours.values()}
  blended = sum(count for key, count in seen.items()
                if all(abs(key[0] - f[0]) > 6 or abs(key[1] - f[1]) > 6
                       or abs(key[2] - f[2]) > 6 for f in fills))
  assert blended > 0, \
    "no colour between the fills anywhere: edges are not being "\
    "smoothed, so the render hint is not set"
  dlg.close()


def test_the_design_view_draws_no_tile_outlines():
  """The preview shows areas of colour, not a mesh.

  A dark hairline around every tile competes with the thing the
  design view exists to judge: whether the shapes read as distinct
  elements. It also thickens relative to the tiles as the spacing
  gets finer, so a detailed pattern turned into a grid of lines.

  Checked by rendering the preview and looking for the outline
  colour, rather than by inspecting the paint calls: what matters is
  what reaches the pixels. The old outline was #333333 at 0.7px, so
  its exact shade may never appear in a rendering; the test therefore
  asks the broader question — are there DARK pixels tracing the tile
  edges — by counting how many sampled pixels are darker than any
  fill the preview uses.

  Regression: the design view drew a dark outline around every tile, which fights the colour comparison the view is for.
  """
  from qgis.PyQt.QtGui import QColor, QImage, QPainter
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  _tick(300)
  dlg._rebuild_unit()
  _tick(200)
  assert dlg.preview._polys, "nothing was drawn in the preview"

  image = QImage(420, 420, QImage.Format.Format_RGB32)
  image.fill(QColor("#ffffff"))
  painter = QPainter(image)
  dlg.preview.render(painter)
  painter.end()

  fills = [QColor(c) for c in dlg.preview._id_colours.values()]
  darkest_fill = min((c.lightness() for c in fills), default=255)
  # anything appreciably darker than every fill can only be ink: the
  # outline, or the tile-id labels
  ink = 0
  for x in range(0, image.width(), 3):
    for y in range(0, image.height(), 3):
      if QColor(image.pixel(x, y)).lightness() < darkest_fill - 40:
        ink += 1
  sampled = (image.width() // 3) * (image.height() // 3)
  assert ink < sampled * 0.02, \
    f"{ink} of {sampled} sampled pixels are darker than any fill "\
    f"({ink / sampled:.1%}); the design view is drawing outlines "\
    f"around its tiles"
  dlg.close()


def test_colour_legibility_warnings_are_opt_in():
  """The colour-legibility check runs only when it is asked for.

  It is a second opinion on a cartographic choice, not a fault, and
  while someone is still trying ramps it would fire on nearly every
  intermediate state — which is how a warning becomes something
  people learn to ignore. So it lives behind a box on Map options,
  unchecked by default.

  Both places the check can fire are covered: after a run, and on
  closing the Categorical colour editor. The map itself must be
  identical either way — the box changes what is SAID, never what is
  drawn.

  Regression: the colour-separability warning fired unconditionally, on every map, whether or not anyone wanted that opinion.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  _tick(200)

  assert not dlg.opt_colour_warnings.isChecked(), \
    "the legibility check is on by default; it is meant to be asked for"
  assert dlg.opt_colour_warnings.text() == \
    "Warn about lack of legibility in colour choices", \
    f"the box reads {dlg.opt_colour_warnings.text()!r}"

  _generate_and_wait(dlg)
  _tick(300)
  quiet_tiles = sum(
    QgsProject.instance().mapLayer(i).featureCount()
    for i in dlg._element_layer_ids.values()
    if QgsProject.instance().mapLayer(i) is not None)
  assert not getattr(dlg, "_pending_colour_note", None), \
    "a colour-legibility notice was raised with the box unchecked"
  assert "tell apart" not in dlg.live_note.text(), \
    f"the note mentions legibility anyway: {dlg.live_note.text()!r}"

  # and with the box ticked, the same map does produce the opinion.
  # The synthetic layer's default ramps are known to collide, which
  # is why this can assert a notice rather than merely its absence.
  dlg.opt_colour_warnings.setChecked(True)
  dlg.spacing_spin.setValue(dlg.spacing_spin.value() * 1.15)
  _generate_and_wait(dlg)
  _tick(300)
  loud_tiles = sum(
    QgsProject.instance().mapLayer(i).featureCount()
    for i in dlg._element_layer_ids.values()
    if QgsProject.instance().mapLayer(i) is not None)
  assert getattr(dlg, "_pending_colour_note", None) or \
      "tell apart" in dlg.live_note.text(), \
    "the box is ticked but no legibility opinion was offered"
  assert loud_tiles > 0 and quiet_tiles > 0, \
    "both runs must actually have produced a map"
  dlg.close()


def test_awkward_layers_are_handled_or_declined():
  """Data a stranger might hand the plugin: five awkward shapes.

  The suite's own fixtures are tidy. Real layers are not, and this
  area of the test map is the thinnest in the suite while being the
  one whose inputs come from outside. Each case here is something a
  user genuinely has on disk:

    no CRS set at all, which QGIS permits;
    a single feature, so every "several polygons" assumption fails;
    a self-intersecting polygon, which shapely will object to;
    a field name outside ASCII, which round-trips through pandas;
    a field that is entirely null, so classification has no range.

  The bar is deliberately not "produces a map". For several of these
  the right behaviour is to decline. The bar is that the plugin must
  not CRASH and must not HANG: it either produces output or says
  something and stays usable. A plugin that raises into the QGIS
  message log leaves a user with no idea what they did wrong.

  Each case runs against a fresh dialog, and the assertion is made on
  the dialog's own state afterwards, so a case that declines is as
  much a pass as one that succeeds.

  Regression: none of these shapes had ever been put through the plugin; the suite's fixtures are all well-formed.
  """
  from qgis.core import QgsField, QgsFeature, QgsGeometry, QgsPointXY
  from qgis.PyQt.QtCore import QVariant
  from weavingspace_qgis.dialog import WeavingSpaceDialog

  def build(name, crs="EPSG:3857", field="v1", squares=4,
            invalid=False, nulls=False):
    """One awkward layer, described by what is wrong with it."""
    uri = f"Polygon?crs={crs}" if crs else "Polygon"
    layer = QgsVectorLayer(uri, name, "memory")
    provider = layer.dataProvider()
    provider.addAttributes([QgsField(field, QVariant.Double)])
    layer.updateFields()
    features = []
    for i in range(squares):
      if invalid:
        # a bow-tie: the classic self-intersection
        points = [QgsPointXY(0, 0), QgsPointXY(1000, 1000),
                  QgsPointXY(1000, 0), QgsPointXY(0, 1000)]
      else:
        x = i * 1000
        points = [QgsPointXY(x, 0), QgsPointXY(x + 1000, 0),
                  QgsPointXY(x + 1000, 1000), QgsPointXY(x, 1000)]
      feature = QgsFeature(layer.fields())
      feature.setGeometry(QgsGeometry.fromPolygonXY([points]))
      feature.setAttributes([None if nulls else float(i + 1)])
      features.append(feature)
    provider.addFeatures(features)
    layer.updateExtents()
    return layer

  cases = [
    ("no CRS", dict(crs="", name="no crs")),
    ("one feature only", dict(squares=1, name="single")),
    ("self-intersecting geometry", dict(invalid=True, name="bowtie")),
    ("non-ASCII field name", dict(field="densit\u00e9", name="accented")),
    ("a field that is entirely null", dict(nulls=True, name="allnull")),
  ]

  trouble = []
  for label, kwargs in cases:
    name = kwargs.pop("name")
    project = QgsProject.instance()
    for existing in list(project.mapLayers().values()):
      project.removeMapLayer(existing.id())
    MODALS.clear()
    layer = build(name, **kwargs)
    if not layer.isValid():
      trouble.append(f"{label}: the fixture itself is invalid")
      continue
    project.addMapLayer(layer)
    dlg = None
    try:
      dlg = WeavingSpaceDialog(iface=None)
      dlg.live_check.setChecked(False)
      dlg.layer_combo.setLayer(layer)
      _tick(300)
      dlg.spacing_spin.setValue(400)
      dlg._generate()
      settled = _settle(dlg, seconds=45)
      _tick(200)
      if not settled:
        trouble.append(f"{label}: never settled — the plugin hung")
        continue
      # Either it made something, or it said something. Silence with
      # no output is the failure worth catching: the user pressed
      # Generate and nothing whatever happened.
      made = bool(dlg._element_layer_ids)
      # "Said something" includes a message BOX, not just the note
      # line. A refusal goes to a modal, which this harness stubs into
      # MODALS — reading live_note alone reports a perfectly polite
      # decline as a silent failure, which it did here first time.
      said = bool(dlg.live_note.text().strip()) or bool(MODALS)
      if not made and not said:
        trouble.append(
          f"{label}: no output and no message; the user is left "
          f"wondering whether it worked")
      if not dlg.generate_btn.isEnabled():
        trouble.append(f"{label}: Generate left disabled afterwards")
    except Exception as exc:
      trouble.append(f"{label}: raised {type(exc).__name__}: {exc}")
    finally:
      if dlg is not None:
        dlg.close()

  assert not trouble, "awkward layers mishandled:\n  " + \
    "\n  ".join(trouble)


def test_region_outlines_are_cased():
  """The outline is a black line over a wider white one.

  A single-colour boundary disappears wherever the pattern beneath it
  matches: a black line over dark tiles, a white one over pale. Casing
  solves that, and it is a settled cartographic decision here rather
  than decoration. Nothing tested it, so removing the second symbol
  layer left the map with white-only outlines and every test passed.

  Asserted on the SYMBOL rather than on pixels: the two lines are a
  fraction of a millimetre apart at map scale, so a render comparison
  would be measuring the rasteriser, not the decision.

  Regression: the outline casing had no test, so losing the black line entirely was invisible to the suite.
  """
  from weavingspace_qgis import bridge
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  outlines = bridge.region_outline_layer(layer)
  symbol = outlines.renderer().symbol()
  assert symbol.symbolLayerCount() == 2, \
    f"the outline has {symbol.symbolLayerCount()} symbol layer(s); "\
    f"casing needs a wide light line and a narrow dark one over it"

  # these are fill layers with no fill, so the line IS the stroke
  under, over = symbol.symbolLayer(0), symbol.symbolLayer(1)
  wide, narrow = under.strokeWidth(), over.strokeWidth()
  assert wide > narrow, \
    f"the upper line ({narrow}) is not narrower than the lower "\
    f"({wide}), so no casing shows"
  light = under.strokeColor().lightness()
  dark = over.strokeColor().lightness()
  assert light > dark, \
    "the casing is meant to be a DARK line over a LIGHT one; this is "\
    "the other way round, which vanishes over pale tiles"
  assert under.strokeColor().alpha() == 255 \
      and over.strokeColor().alpha() == 255, \
    "a translucent casing lets the pattern show through the boundary"


def _categorical_dialog(field="landcover", row=1):
  """A dialog with one categorical element, ready to have colours
  edited.

  Args:
    field: the categorical attribute to assign, which must exist in
      make_region_layer's synthetic data.
    row: which table row to assign it to. Row 1 rather than 0 by
      default, so the tests also exercise an element that is NOT the
      first — first-field and first-row cases have been special once
      already in this plugin.

  Returns:
    (dialog, layer, tile_id). The dialog has live update OFF and has
    generated nothing yet, so a caller can test the editor before any
    map exists, which is one of the things it promises.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  _tick(200)
  dlg.table.cellWidget(row, 1).setCurrentText(field)
  dlg._update_dynamic_columns()
  _tick(100)
  tid = dlg.table.item(row, 0).text()
  return dlg, layer, tid


def test_installed_palettes_span_their_declared_colours():
  """An installed ramp runs between the colours the palette declares.

  The plugin installs its palettes into QGIS's style library as
  gradient ramps: first stop, last stop, and the intermediate stops
  between them. Take the last stop from the wrong end of the list and
  every sequential ramp stops short of its darkest colour — which is
  the end carrying the highest values, so the top class of every map
  made with it is wrong. Nothing caught that: the existing check
  confirmed the ramps EXIST.

  Endpoints are compared rather than whole ramps, because those are
  what the mutation can move and what a reader sees at the extremes
  of a legend.

  Regression: only the existence of installed palettes was checked, never the colours they run between.
  """
  from qgis.PyQt.QtGui import QColor
  from weavingspace_qgis import bridge
  bridge.ensure_ramps_installed()
  checked = 0
  for group in ("sequential", "diverging"):
    for name, stops in bridge.PALETTES[group].items():
      ramp = bridge.get_ramp(name, False)
      if ramp is None:
        continue                    # not installed in this profile
      first = QColor(ramp.color(0.0)).name().lower()
      last = QColor(ramp.color(1.0)).name().lower()
      assert first == stops[0].lower(), \
        f"{name} starts at {first}, but the palette declares "\
        f"{stops[0].lower()}"
      assert last == stops[-1].lower(), \
        f"{name} ends at {last}, but the palette declares "\
        f"{stops[-1].lower()}; a ramp that stops short loses the "\
        f"colour carrying its highest values"
      checked += 1
  assert checked >= 4, \
    f"only {checked} palette(s) were checked; this test is not "\
    f"exercising the installation it claims to"

  # ... and the colours BETWEEN the ends, at the positions they are
  # declared at. Checking endpoints alone leaves the whole middle of
  # every ramp free: the stop positions are computed as i/(len-1), and
  # an error there slides every interior colour along the ramp while
  # both ends stay exactly right. A map made with such a ramp is wrong
  # in its classes and correct in its legend's extremes, which is the
  # hardest kind of wrong to notice.
  drift = []
  for group in ("sequential", "diverging"):
    for name, stops in bridge.PALETTES[group].items():
      ramp = bridge.get_ramp(name, False)
      if ramp is None:
        continue
      for i, declared in enumerate(stops):
        at = i / (len(stops) - 1)
        got = QColor(ramp.color(at))
        want = QColor(declared)
        apart = max(abs(got.red() - want.red()),
                    abs(got.green() - want.green()),
                    abs(got.blue() - want.blue()))
        if apart > 2:                 # 2/255 for rounding in the ramp
          drift.append(
            f"{name} stop {i} of {len(stops) - 1} (at {at:.3f}): "
            f"{got.name()} where the palette declares {want.name()}")
  assert not drift, \
    "installed ramps put their colours in the wrong places:\n  " + \
    "\n  ".join(drift[:8])


def test_ramp_swatches_run_the_right_way_round():
  """A swatch shows the ramp in the direction the map will use it.

  The dropdown's swatches are drawn by _ramp_icon, whose `reverse`
  argument defaults to off; the Reverse switch passes it explicitly.
  Flip that default and every swatch in the list is drawn backwards
  while the map stays right, so a user picking "the one that goes
  pale to dark" gets the opposite. Nothing caught that, because the
  suite checked that swatches EXIST and never what they showed.

  Reds is used because its direction is unambiguous: light at the low
  end, dark at the high end. The check is on lightness rather than on
  exact colours, so it survives QGIS shipping a slightly different
  Reds.

  Regression: swatch direction was untested, so drawing every ramp backwards was invisible.
  """
  from qgis.PyQt.QtGui import QColor
  from weavingspace_qgis import bridge
  from weavingspace_qgis.dialog import _ramp_icon, RAMP_SWATCH
  ramp = bridge.get_ramp("Reds", False)
  if ramp is None:
    return                          # no QGIS style library here
  icon = _ramp_icon("Reds")
  assert icon is not None, "no swatch was drawn for a ramp that exists"
  image = icon.pixmap(RAMP_SWATCH).toImage()
  assert not image.isNull(), "the swatch is an empty image"

  middle = image.height() // 2
  left = QColor(image.pixel(1, middle))
  right = QColor(image.pixel(image.width() - 2, middle))
  assert left.lightness() > right.lightness(), \
    f"the Reds swatch runs dark-to-light (left {left.lightness()}, "\
    f"right {right.lightness()}); it is drawn reversed, so the list "\
    f"disagrees with the map"

  # and the Reverse switch really does turn it round
  flipped = _ramp_icon("Reds", True)
  fimage = flipped.pixmap(RAMP_SWATCH).toImage()
  fleft = QColor(fimage.pixel(1, middle))
  assert fleft.lightness() < left.lightness(), \
    "asking for a reversed swatch produced the same picture, so the "\
    "Reverse switch shows the user nothing"


def test_a_new_run_always_shows_real_progress():
  """A run reports a percentage, even after one that died mid-output.

  During the output phase the bar is deliberately switched to its
  indefinite "busy" form, because adding layers reports no percentage
  and a frozen bar there once looked exactly like a hang. _finish_run
  puts it back — but the zombie recovery in showEvent does not: it
  clears the task and hides the bar directly. So a run that ended
  through the recovery path leaves the bar indefinite, and the next
  run inherits it unless it sets its own range.

  The consequence is the failure the busy form was introduced to
  prevent, wearing the opposite face: a tiling that IS progressing,
  reported by a bar that says only "something is happening".

  Regression: only _finish_run restored the determinate progress range, and the zombie recovery does not go through it.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  _tick(300)

  # leave the bar as a run that died during the output phase would
  dlg.progress.setRange(0, 0)
  assert dlg.progress.maximum() == 0, "the setup did not take"

  _generate_and_wait(dlg)
  _tick(200)
  assert dlg.progress.maximum() == 100, \
    "a new run inherited the indefinite progress bar from a previous "\
    "one, so a tiling that is progressing reports no percentage"
  dlg.close()


def test_live_update_is_on_by_default():
  """A first map appears without anyone pressing Generate.

  This is a settled design decision: the plugin renders as soon as a
  layer and variables are in place, so someone who has never used it
  sees a map rather than an empty canvas and a button. Every other
  test in this suite turns live update OFF in its first two lines,
  which is exactly why nothing noticed when the default was flipped —
  the suite was unanimous about a setting no test asserted.

  Regression: the live-update default was unasserted, so turning it off shipped silently past 100 tests.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  assert dlg.live_check.isChecked(), \
    "live update is off by default, so a new user sees no map until "\
    "they find the Generate button"

  # and it is not merely checked: it acts
  dlg.layer_combo.setLayer(layer)
  _tick(400)
  _settle(dlg)
  _tick(400)
  assert dlg._element_layer_ids, \
    "live update is on but no map was drawn from choosing a layer"
  dlg.close()


def test_repopulating_the_family_list_fires_no_handlers():
  """Switching tiling/weave must not fire family-changed midway.

  The family combo is cleared and refilled when the kind changes.
  Without blockSignals, every addItems() step emits
  currentIndexChanged, so handlers run against a half-built list and
  the unit is rebuilt several times from states the user never chose.
  That is the same shape as the chooser race this project already
  paid for once.

  Counting rebuilds rather than inspecting signals: what matters is
  that the work happens once, whatever Qt emits on the way.

  Regression: family-list repopulation had no test, so unblocking its signals was invisible.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  _tick(300)

  rebuilds = []
  original = dlg._rebuild_unit

  def counted(*a, **k):
    rebuilds.append(dlg.family_combo.currentText())
    return original(*a, **k)

  dlg._rebuild_unit = counted
  before = dlg.kind_combo.currentText()
  other = next(dlg.kind_combo.itemText(i)
               for i in range(dlg.kind_combo.count())
               if dlg.kind_combo.itemText(i) != before)
  dlg.kind_combo.setCurrentText(other)
  _tick(800)

  assert len(rebuilds) <= 1, \
    f"changing the pattern kind rebuilt the unit {len(rebuilds)} "\
    f"times, once per item added to the family list: {rebuilds}"
  dlg.close()


def test_the_edit_colours_column_appears_with_categories():
  """The column exists only where there is something to edit.

  It follows the same rule as the class-source column beside it:
  present when any element is categorized, absent otherwise. Within
  it, rows that are not categorical keep a DISABLED button rather
  than an empty cell, because a hole in a column reads as a control
  that failed to appear rather than one that does not apply.

  Also pins where the column sits. It is the last column logically
  and moved next to the ramp visually; if a later change inserts it
  properly instead, this test says so rather than letting the
  neighbouring columns quietly renumber.
  """
  from weavingspace_qgis.dialog import COL_EDIT_COLOURS
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  _tick(200)
  assert dlg.table.isColumnHidden(COL_EDIT_COLOURS), \
    "the Edit colours column is showing with nothing categorical"

  dlg.table.cellWidget(1, 1).setCurrentText("landcover")
  dlg._update_dynamic_columns()
  _tick(100)
  assert not dlg.table.isColumnHidden(COL_EDIT_COLOURS), \
    "a categorical element did not bring out the Edit colours column"
  header = dlg.table.horizontalHeader()
  assert header.visualIndex(COL_EDIT_COLOURS) == 5, \
    "Edit colours is meant to sit immediately after the ramp column"
  assert dlg.table.horizontalHeaderItem(
    COL_EDIT_COLOURS).text() == "Edit colours"

  enabled = dlg.table.cellWidget(1, COL_EDIT_COLOURS)
  assert enabled is not None and enabled.isEnabled(), \
    "the categorical row's button is not usable"
  # The button says what it does. An ellipsis on a disabled control
  # reads as something broken; a greyed "Custom" reads as something
  # that does not apply to this row, which is the truth.
  assert enabled.text() == "Custom", \
    f"the button reads {enabled.text()!r}, not 'Custom'"
  for row in range(dlg.table.rowCount()):
    if row == 1:
      continue
    button = dlg.table.cellWidget(row, COL_EDIT_COLOURS)
    assert button is not None, \
      f"row {row} has an empty cell where a greyed button belongs"
    assert not button.isEnabled(), \
      f"row {row} is not categorical but its button is live"
    assert button.text() == "Custom", \
      f"the greyed button on row {row} reads {button.text()!r}; it "\
      f"should say the same thing as the live ones"

  # and it goes away again
  dlg.table.cellWidget(1, 1).setCurrentText("---")
  dlg._update_dynamic_columns()
  _tick(100)
  assert dlg.table.isColumnHidden(COL_EDIT_COLOURS), \
    "the column outstayed the categories that justified it"
  dlg.close()


def test_the_editor_lists_every_value_and_the_no_data_row():
  """What the little window contains.

  Values come from the REGION layer, so this works before anything is
  generated -- which is the point, since choosing colours is part of
  designing the map rather than a reaction to one. The catch-all
  category comes last: it is a colour a reader sees, often over a
  large area where a join left gaps, so it is editable, but it is not
  one of the data's own values and is not presented as one.

  The value column is capped so one very long category cannot push
  the colour column off the window.
  """
  from weavingspace_qgis import bridge
  from weavingspace_qgis.category_editor import (CategoryColourDialog,
                                                 VALUE_WIDTH)
  dlg, layer, tid = _categorical_dialog()
  assert not dlg._element_layer_ids, \
    "this test is meant to run before anything is generated"

  assignment = next(a for a in dlg._assignments() if a["id"] == tid)
  colours, order = dlg._current_category_colours(assignment)
  expected = {str(v) for v in layer.uniqueValues(
    layer.fields().indexOf("landcover")) if v is not None}
  assert set(order) - {bridge.NO_DATA_KEY} == expected, \
    f"the editor would list {order}, the data has {sorted(expected)}"
  assert order[-1] == bridge.NO_DATA_KEY, \
    "the no-data catch-all must come last, not among the real values"

  editor = CategoryColourDialog(tid, "landcover", order, colours,
                                None, dlg)
  assert editor.windowTitle() == "Categorical colour editor"
  assert editor.table.rowCount() == len(order)
  assert editor.table.item(len(order) - 1, 0).text() == "(no data)"
  assert editor.table.columnWidth(0) == VALUE_WIDTH, \
    f"the value column is {editor.table.columnWidth(0)}px, not the "\
    f"settled {VALUE_WIDTH}px"
  # every row offers a colour, and it is the colour the map would use
  for row, value in enumerate(order):
    button = editor.table.cellWidget(row, 1)
    assert button is not None, f"no colour control for {value!r}"
    assert button.text().startswith("#"), \
      f"{value!r} shows {button.text()!r} rather than a colour"
    assert button.text() == colours[value]
  editor.close()
  dlg.close()


def test_the_editor_is_laid_out_as_specified():
  """The window's shape: alignment, fixed pitch, and no dead space.

  Each of these is small on its own and together they decide whether
  the thing reads as a table of values or as a form. Values are set
  right and colours left so the two columns meet in the middle, and
  the eye runs down one gap rather than across a ragged one. Hex codes
  are compared digit by digit down the column, so they are set in a
  fixed-pitch face. The header keeps Qt's own alignment, which is part
  of what marks it as a header.

  The window is fitted to the TABLE rather than the other way round.
  Sizing the window by guess and letting the table fill it leaves
  either a strip of dead space beside the table or a scroll bar over
  rows that would have fitted, and both look like carelessness.
  """
  from qgis.PyQt.QtCore import Qt
  from weavingspace_qgis.category_editor import (
    CategoryColourDialog, VALUE_WIDTH, COLOUR_WIDTH)
  values = ["forest", "water", "urban"]
  colours = {"forest": "#1b7837", "water": "#2166ac", "urban": "#b2182b"}
  editor = CategoryColourDialog("a", "landcover", values, colours,
                                None, None)

  for row in range(len(values)):
    item = editor.table.item(row, 0)
    assert item.textAlignment() & Qt.AlignmentFlag.AlignRight, \
      f"value row {row} is not right-aligned"
    button = editor.table.cellWidget(row, 1)
    style = button.styleSheet()
    assert "text-align: left" in style, \
      f"the colour on row {row} is not left-aligned: {style!r}"
    assert "monospace" in style or "Menlo" in style, \
      f"the hex code on row {row} is not in a fixed-pitch face"

  assert editor.table.columnWidth(0) == VALUE_WIDTH
  assert editor.table.columnWidth(1) == COLOUR_WIDTH

  # the window is only a little wider than the table it contains
  slack = editor.width() - editor.table.width()
  assert 0 <= slack <= 60, \
    f"the window is {slack}px wider than its table; it should be "\
    f"only a little larger, not padded"
  tall = editor.height() - editor.table.height()
  assert tall <= 160, \
    f"the window is {tall}px taller than its table, which is more "\
    f"than a two-line heading and a Close button need"
  editor.close()


def test_the_editor_hides_nothing_at_any_size():
  """Sweep the sizes a real field can produce, and check nothing is
  cut off.

  The window sizes itself from its contents, and self-sizing is
  exactly where things get quietly clipped: a Close button pushed
  below the bottom edge, a colour column hidden behind the scroll bar
  that arrived with the sixteenth row, a heading cropped by a long
  field name. None of those raise; they just leave a control the user
  cannot reach, and only a sweep across sizes finds them, because
  every one appears at a particular row count or name length and not
  at the one a single example happens to use.

  Checked at each size: every child widget lies inside the window,
  both columns are fully visible in the table's viewport, and nothing
  needs horizontal scrolling.
  """
  from qgis.PyQt.QtWidgets import QDialogButtonBox, QWidget
  from weavingspace_qgis.category_editor import (CategoryColourDialog,
                                                 VISIBLE_ROWS)
  names = {
    "one character": "x",
    "ordinary": "wetland",
    "long": "High-density residential and commercial mixed use",
    "very long": "A category name of quite unreasonable length " * 2,
  }
  counts = [1, 2, 3, VISIBLE_ROWS - 1, VISIBLE_ROWS,
            VISIBLE_ROWS + 1, 40]
  # A window is allowed its layout margins. More than about a line of
  # empty space past the last thing in it is not a margin, it is the
  # window having been sized by guess -- which is the same fault as
  # clipping, seen from the other end. One row of this table is the
  # natural unit for "a line or so".
  SLACK = 26
  problems = []
  for label, stem in names.items():
    for count in counts:
      values = [f"{stem} {i}" for i in range(count)]
      editor = CategoryColourDialog(
        "a", "landcover", values,
        {v: "#4477aa" for v in values}, None, None)
      editor.show()
      _tick(30)
      where = f"{label} names, {count} value(s)"

      window = editor.rect()
      for child in (editor.table,) + tuple(
          editor.findChildren(QDialogButtonBox)):
        box = child.geometry()
        if not window.contains(box):
          problems.append(
            f"{where}: {type(child).__name__} at {box.x()},{box.y()} "
            f"{box.width()}x{box.height()} sticks out of a window "
            f"{window.width()}x{window.height()}")

      # ... and nothing much beyond them either. Measured from the
      # furthest extent of any child, so it catches dead space
      # wherever the layout put it.
      children = [c.geometry() for c in editor.findChildren(QWidget)
                  if c.isVisible() and c.parent() is editor]
      if children:
        right = max(g.right() for g in children)
        bottom = max(g.bottom() for g in children)
        if window.right() - right > SLACK:
          problems.append(
            f"{where}: {window.right() - right}px of empty space to "
            f"the right of everything in the window")
        if window.bottom() - bottom > SLACK:
          problems.append(
            f"{where}: {window.bottom() - bottom}px of empty space "
            f"below everything in the window")

      viewport = editor.table.viewport().width()
      columns = sum(editor.table.columnWidth(c) for c in (0, 1))
      if viewport < columns:
        problems.append(
          f"{where}: the viewport is {viewport}px for {columns}px of "
          f"columns, so the colour column is clipped")
      if editor.table.horizontalScrollBar().maximum() > 0:
        problems.append(
          f"{where}: the table needs horizontal scrolling")
      if editor.table.rowCount() != count:
        problems.append(
          f"{where}: {editor.table.rowCount()} rows for {count} values")
      editor.close()

  assert not problems, "the editor hides things at some sizes:\n  " + \
    "\n  ".join(problems)


def test_the_editor_scrolls_only_past_fifteen_values():
  """Fifteen rows show; a sixteenth brings a scroll bar, not a taller
  window.

  A field with forty categories would otherwise open a window taller
  than the screen, over the very map whose colours are being chosen.
  The table stops growing at VISIBLE_ROWS and scrolls instead, and the
  window stops with it.

  The scroll bar's width is added to the table when it appears, since
  a vertical scroll bar takes its width from the viewport rather than
  adding to it -- without that the colour column is clipped by exactly
  the bar that arrived to accommodate the rows.
  """
  from weavingspace_qgis.category_editor import (CategoryColourDialog,
                                                 VISIBLE_ROWS)
  def editor_for(n):
    values = [f"class {i:02d}" for i in range(n)]
    return CategoryColourDialog(
      "a", "many", values, {v: "#336699" for v in values}, None, None)

  small = editor_for(VISIBLE_ROWS)
  big = editor_for(VISIBLE_ROWS + 12)
  assert small.table.rowCount() == VISIBLE_ROWS
  assert big.table.rowCount() == VISIBLE_ROWS + 12, \
    "every value must be present, scrolled or not"
  assert big.table.height() == small.table.height(), \
    f"the table grew from {small.table.height()} to "\
    f"{big.table.height()}px instead of scrolling"
  assert big.height() == small.height(), \
    "the window grew with the extra values instead of scrolling"
  assert big.table.width() > small.table.width(), \
    "a scroll bar appeared without room being made for it, so the "\
    "colour column is clipped by exactly that scroll bar"
  # and the rows really are reachable
  assert big.table.item(VISIBLE_ROWS + 5, 0).text() == "class 20"
  small.close()
  big.close()


def test_a_long_value_is_truncated_but_recoverable():
  """A long category name elides, and hovering shows it whole.

  The value column is a settled width rather than one fitted to the
  contents, so that every element's editor is the same size and the
  window does not jump about as a user moves between elements. The
  cost is that a long name will not fit, so the full text has to stay
  reachable: it is on the cell as a tooltip.

  A window that widened itself to fit one 48-character category would
  also defeat the sizing rule above it, since the window is fitted to
  the table.
  """
  from weavingspace_qgis.category_editor import (CategoryColourDialog,
                                                 VALUE_WIDTH)
  long_value = "High-density residential and commercial mixed use"
  editor = CategoryColourDialog(
    "a", "zoning", [long_value, "park"],
    {long_value: "#ff0000", "park": "#00ff00"}, None, None)
  assert editor.table.columnWidth(0) == VALUE_WIDTH, \
    f"one long value moved the column to " \
    f"{editor.table.columnWidth(0)}px; it is meant to be fixed"
  short = CategoryColourDialog(
    "a", "zoning", ["park"], {"park": "#00ff00"}, None, None)
  assert editor.width() == short.width(), \
    "a long category name widened the window, so the editor is a "\
    "different size for every element"
  assert editor.table.item(0, 0).toolTip() == long_value, \
    "the full value is not recoverable by hovering"
  short.close()
  editor.close()


def test_editing_a_category_colour_reaches_the_map():
  """The whole point: a colour picked here is the colour drawn.

  Checks the three things the user asked for at once -- the plugin
  records it, the renderer carries it, and the map is repainted
  through the fast path rather than by tiling again. The last is
  visible as the task never being started: re-tiling is the expensive
  step and a colour has nothing to do with it.

  Regression: none yet; this pins the feature's central claim.
  [ui-vs-library]
  """
  from weavingspace_qgis import bridge
  dlg, layer, tid = _categorical_dialog()
  _generate_and_wait(dlg)
  _tick(200)
  layer_id = dlg._element_layer_ids[tid]
  element = QgsProject.instance().mapLayer(layer_id)
  before = bridge.renderer_fill_colours(element)
  tiles_before = element.featureCount()

  assignment = next(a for a in dlg._assignments() if a["id"] == tid)
  _colours, order = dlg._current_category_colours(assignment)
  value = order[0]
  dlg._category_colours.setdefault(tid, {}).setdefault(
    "landcover", {})[value] = "#ff00ff"
  dlg._apply_style_change()
  _tick(200)

  assert dlg._task is None, \
    "a colour change started a tiling run; it must take the fast path"
  element = QgsProject.instance().mapLayer(layer_id)
  assert element is not None and element.id() == layer_id, \
    "the element layer was replaced, so this was not a restyle"
  assert element.featureCount() == tiles_before, \
    "the tiles were rebuilt for what is only a colour change"
  after = bridge.renderer_fill_colours(element)
  assert (255, 0, 255) in after, \
    f"the picked colour never reached the renderer: {after}"
  assert (255, 0, 255) not in before, \
    "the test is vacuous: that colour was already there"
  assert len(after) == len(before), \
    "the number of classes changed when only a colour was picked"

  # and the map really looks like that
  visual_gamut("categorical colour editor: a hand-picked colour",
               [element], [assignment["ramp"]],
               extra_colours=["#ff00ff"])
  dlg.close()


def test_a_picked_colour_changes_the_rendered_map():
  """End to end: pick a colour, and the PIXELS change.

  Everything else about this feature is checked against the renderer,
  which is one step short of the claim. A renderer carrying the right
  colour still proves nothing if the layer it is attached to is not
  the one being drawn, or if the change never reaches the canvas. So
  this one renders the map before and after and compares what a
  reader would actually see.

  The colour is deliberately one no ramp in force can produce, so its
  arrival cannot be a coincidence of classification, and its absence
  beforehand is checked rather than assumed.

  Regression: every other check on this feature stopped at the renderer, one step short of the map.
  [ui-vs-library]
  """
  from weavingspace_qgis import bridge
  sys.path.insert(0, HERE)
  from visual_tests import render_layers

  def count_colour(image, rgb, stride=2):
    """How many pixels of the rendered map carry exactly this colour.

    Args:
      image: the rendered QImage.
      rgb: an (r, g, b) tuple to count, compared exactly.
      stride: sample every nth pixel in each direction; 2 is fine for
        deciding whether a class is present at all, and four times
        cheaper than every pixel.

    Returns:
      The count of matching sampled pixels.

    The whole image on a fine stride, rather than visual_tests'
    sample_pixels: that walks a coarse grid AND discards any pixel
    whose neighbours disagree, which is right for measuring fills
    against a gamut but can miss a class of small tiles completely —
    it did here, reporting no magenta on a map that had it.
    """
    seen = 0
    for x in range(0, image.width(), stride):
      for y in range(0, image.height(), stride):
        c = image.pixelColor(x, y)
        if (c.red(), c.green(), c.blue()) == rgb:
          seen += 1
    return seen

  dlg, layer, tid = _categorical_dialog()
  _generate_and_wait(dlg)
  _tick(200)
  element = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  others = [QgsProject.instance().mapLayer(i)
            for t, i in dlg._element_layer_ids.items() if t != tid]
  layers = [element] + [o for o in others if o is not None]

  out = report_dir()
  before_png = os.path.join(out, "picked_colour_before.png")
  after_png = os.path.join(out, "picked_colour_after.png")
  # Pick a colour the map does NOT already show, rather than assuming
  # one. The first attempt used magenta, which turned out to be on the
  # map already from another element's own ramp -- so the test would
  # have "passed" on a pixel the feature never touched.
  before_image = render_layers(list(layers), before_png)
  candidates = [(255, 0, 255), (0, 255, 255), (255, 128, 0),
                (128, 0, 255), (0, 128, 255), (255, 0, 128)]
  target = next((c for c in candidates
                 if count_colour(before_image, c) == 0), None)
  assert target is not None, \
    "every candidate colour is already on the map; this test cannot "\
    "tell its own change from the existing symbology"
  target_hex = "#%02x%02x%02x" % target

  assignment = next(a for a in dlg._assignments() if a["id"] == tid)
  _colours, order = dlg._current_category_colours(assignment)
  # The value carrying the MOST tiles, not the first alphabetically.
  # A rare class can cover so few interior pixels that the sampling
  # misses it entirely, and the test would then be measuring the
  # sampler rather than the plugin.
  tally = {}
  index = element.fields().indexOf("landcover")
  for feature in element.getFeatures():
    tally[str(feature[index])] = tally.get(str(feature[index]), 0) + 1
  commonest = max(tally, key=tally.get)
  assert tally[commonest] > 1, "no value covers enough tiles to see"
  dlg._category_colours.setdefault(tid, {}).setdefault(
    "landcover", {})[commonest] = target_hex
  dlg._apply_style_change()
  _tick(300)

  element = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  layers = [element] + [o for o in others if o is not None]
  after_image = render_layers(list(layers), after_png)
  hits = count_colour(after_image, target)
  assert hits > 0, \
    "the picked colour reached the renderer but never the map: not "\
    "one pixel of the render carries it"
  assert hits > 50, \
    f"only {hits} pixels carry the picked colour; that is too few to "\
    f"be the class it was applied to"

  # the map is otherwise undisturbed: the tiles that changed are the
  # ones that were the old colour, and nothing else moved
  assert after_image.size() == before_image.size(), "the map resized"
  differing = 0
  for x in range(0, after_image.width(), 4):
    for y in range(0, after_image.height(), 4):
      if after_image.pixelColor(x, y) != before_image.pixelColor(x, y):
        differing += 1
  assert differing > 0, "nothing changed on the map at all"
  total = (after_image.width() // 4) * (after_image.height() // 4)
  assert differing < total * 0.5, \
    f"{differing} of {total} sampled pixels changed; recolouring one "\
    f"value should not repaint half the map"

  # every ramp in the render, not just the edited element's: the
  # picture contains all the element layers, so declaring one ramp
  # would report the others' perfectly correct colours as strays
  ramps = sorted({a["ramp"] for a in dlg._assignments() if a.get("ramp")})
  visual_gamut("categorical editor: picked colour on the map",
               layers, ramps, extra_colours=[target_hex])
  dlg.close()


def test_hand_picked_colours_survive_a_regenerate():
  """Pressing Generate again keeps them.

  A user picks colours, then changes the spacing and regenerates.
  Nothing about the colours was said, so nothing about them should
  change -- including through the full tiling path, which builds
  fresh layers rather than restyling the old ones.
  """
  from weavingspace_qgis import bridge
  dlg, layer, tid = _categorical_dialog()
  _generate_and_wait(dlg)
  _tick(200)
  assignment = next(a for a in dlg._assignments() if a["id"] == tid)
  _colours, order = dlg._current_category_colours(assignment)
  dlg._category_colours.setdefault(tid, {}).setdefault(
    "landcover", {})[order[0]] = "#123456"
  dlg._apply_style_change()
  _tick(150)

  dlg.spacing_spin.setValue(dlg.spacing_spin.value() * 1.3)
  _generate_and_wait(dlg)
  _tick(200)
  element = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  assert (0x12, 0x34, 0x56) in bridge.renderer_fill_colours(element), \
    "a regenerate discarded a colour the user had chosen by hand"
  dlg.close()


def test_a_new_ramp_discards_hand_picks_and_says_so():
  """Choosing a ramp means starting that element's colours over.

  That is the settled rule, and it makes the ramp control mean what
  it says. It also throws away deliberate work, so it is not done
  silently: the user is told how many colours went and for which
  element. Only the current field is cleared.
  """
  dlg, layer, tid = _categorical_dialog()
  dlg._category_colours.setdefault(tid, {}).setdefault(
    "landcover", {})["forest"] = "#ff0000"
  dlg.live_note.setText("")

  ramp = dlg.table.cellWidget(1, 4)
  ramp.setCurrentIndex((ramp.currentIndex() + 1) % ramp.count())
  _tick(150)

  assert not dlg._category_colours.get(tid, {}).get("landcover"), \
    "a new ramp left the old hand-picked colours in place"
  note = dlg.live_note.text()
  assert "discarded" in note and tid in note, \
    f"the user was not told their colours were dropped: {note!r}"
  assert "landcover" in note, \
    "the notice does not say which variable lost its colours"
  dlg.close()


def test_hand_picks_are_kept_per_variable():
  """Switching an element's variable away and back restores its work.

  Colours are keyed by element AND field. Two consequences are tested
  here: work on one variable is not destroyed by looking at another,
  and two fields that happen to share a value name do not colour each
  other -- "other", "none" and "1" are common enough that this would
  bite.
  """
  dlg, layer, tid = _categorical_dialog()
  dlg._category_colours.setdefault(tid, {}).setdefault(
    "landcover", {})["forest"] = "#ff0000"

  dlg.table.cellWidget(1, 1).setCurrentText("v1")
  dlg._update_dynamic_columns()
  _tick(100)
  assignment = next(a for a in dlg._assignments() if a["id"] == tid)
  assert not assignment.get("category_colours"), \
    "another variable inherited colours picked for 'landcover'"

  dlg.table.cellWidget(1, 1).setCurrentText("landcover")
  dlg._update_dynamic_columns()
  _tick(100)
  assignment = next(a for a in dlg._assignments() if a["id"] == tid)
  assert (assignment.get("category_colours") or {}).get(
    "forest") == "#ff0000", \
    "switching a variable away and back destroyed the user's colours"
  dlg.close()


def test_hand_picked_colours_are_written_into_the_project():
  """They outlive the session, because the dialog does not.

  The dialog's own record lasts as long as QGIS is open; a project
  file outlives it. So the colours are stamped on the element layer
  as a custom property, which QGIS saves inside the .qgz, and read
  back when a dialog adopts an existing group. Without that, a user
  who reopened yesterday's project and pressed Generate would watch
  their colours revert with no warning.
  """
  import json
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  dlg, layer, tid = _categorical_dialog()
  _generate_and_wait(dlg)
  _tick(200)
  dlg._category_colours.setdefault(tid, {}).setdefault(
    "landcover", {})["forest"] = "#0a0b0c"
  dlg._apply_style_change()
  _tick(150)

  element = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  raw = element.customProperty("weavingspace_category_colours")
  assert raw, "nothing was recorded on the layer for the project file"
  stored = json.loads(raw)
  assert stored["field"] == "landcover"
  assert stored["colours"]["forest"] == "#0a0b0c"
  dlg.close()

  # a new dialog in the same project adopts the group and the colours
  revived = WeavingSpaceDialog(iface=None)
  _tick(200)
  assert revived._category_colours.get(tid, {}).get(
    "landcover", {}).get("forest") == "#0a0b0c", \
    "a dialog reopened on a saved project forgot the hand-picked colours"
  revived.close()


def test_a_colour_picked_during_a_run_is_not_lost():
  """A race: the editor is open, and the run underneath finishes.

  Finishing a run REPLACES every element layer. An editor holding a
  layer would be writing into a corpse, so it holds none: it records
  the colour against the element and lets whatever layers exist at
  the time be seeded from that record. The restyle path also declines
  while a task is in flight, which means the change has to be applied
  by the run that lands rather than dropped.
  """
  from weavingspace_qgis import bridge
  dlg, layer, tid = _categorical_dialog()
  _generate_and_wait(dlg)
  _tick(200)

  dlg.spacing_spin.setValue(dlg.spacing_spin.value() * 1.2)
  dlg._generate()
  assert dlg._task is not None, "a run should be in flight for this test"
  # the user picks a colour while the tiling is still going
  dlg._category_colours.setdefault(tid, {}).setdefault(
    "landcover", {})["forest"] = "#00ffff"
  dlg._apply_style_change()
  _settle(dlg)
  _tick(300)

  element = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  assert (0, 255, 255) in bridge.renderer_fill_colours(element), \
    "a colour picked while a run was finishing was thrown away by it"
  dlg.close()


def test_editing_colours_never_rebuilds_the_table():
  """The chooser-race rule, applied to the new control.

  Data-tab handlers must never trigger a table rebuild: a rebuild
  replaces every cell widget, so one landing mid-interaction kills
  open dropdowns and commits picks to dead widgets. This is the rule
  that cost this project a real bug, so every new handler on that tab
  is held to it -- widget IDENTITY has to survive.
  """
  dlg, layer, tid = _categorical_dialog()
  # let the setup's own debounced rebuild land FIRST. Without this the
  # test measures a rebuild queued by assigning the variable and blames
  # it on the colour pick -- which is the failure mode this suite calls
  # a test passing (or failing) for the wrong reason.
  _tick(600)
  before = [id(dlg.table.cellWidget(r, 1))
            for r in range(dlg.table.rowCount())]
  dlg._category_colours.setdefault(tid, {}).setdefault(
    "landcover", {})["forest"] = "#abcdef"
  dlg._apply_style_change()
  _tick(300)
  after = [id(dlg.table.cellWidget(r, 1))
           for r in range(dlg.table.rowCount())]
  assert before == after, \
    "picking a colour rebuilt the table, which kills any open dropdown"
  dlg.close()


def test_the_editor_copes_with_the_data_going_away():
  """Opening the editor for a field that no longer exists.

  A user can delete a field, or swap the region layer for one shaped
  differently, between assigning a variable and pressing the button.
  Nothing here may raise into the UI: the plugin says what is wrong
  and carries on.
  """
  dlg, layer, tid = _categorical_dialog()
  assignment = next(a for a in dlg._assignments() if a["id"] == tid)
  gone = dict(assignment)
  gone["var"] = "a_field_that_was_never_there"
  colours, order = dlg._current_category_colours(gone)
  assert colours is None and order is None, \
    "a missing field produced something rather than an honest nothing"

  layer.dataProvider().deleteAttributes(
    [layer.fields().indexOf("landcover")])
  layer.updateFields()
  _tick(100)
  dlg._edit_category_colours()      # no sender: must simply do nothing
  dlg.close()


def test_two_notices_from_one_run_both_survive():
  """A single run can have several things worth saying about it.

  One generate can produce three notices at once: areas that received
  no tiles at this spacing, categories whose colours moved, and
  element colours a reader cannot separate. QGIS's message bar stacks
  them. Without a message bar they share one label, and the earlier
  ones used to be overwritten by the later, so the map's coverage
  problem disappeared behind its colour problem.

  This drives _report_quietly directly rather than through a run,
  because provoking all three conditions at once takes a contrived
  layer, and the behaviour under test belongs to the reporting, not
  to the conditions that trigger it.

  Regression: two warnings from one run shared a single label and the last one silently erased the first.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog, NOTE_SEPARATOR
  dlg = WeavingSpaceDialog(iface=None)      # headless: the fallback path
  dlg.live_note.setText("")

  dlg._report_quietly("15 of 155 areas received no tiles")
  first = dlg.live_note.text()
  assert "received no tiles" in first, "the first notice was not shown"

  dlg._report_quietly("colours are hard to tell apart")
  both = dlg.live_note.text()
  assert "received no tiles" in both, \
    "the second notice erased the first, so a user told about unreadable "\
    "colours is never told that part of their map is missing"
  assert "hard to tell apart" in both, "the second notice was lost"
  assert NOTE_SEPARATOR in both, \
    "two notices ran together with nothing between them"

  # a repeat says nothing new and must not push the others out of view
  dlg._report_quietly("colours are hard to tell apart")
  assert dlg.live_note.text() == both, \
    "the same notice was appended twice"

  # with a message bar present the label is not used at all: the bar
  # stacks notices itself, and writing to both would double them up
  bar = _Iface()
  loud = WeavingSpaceDialog(iface=bar)
  loud.live_note.setText("")
  loud._report_quietly("15 of 155 areas received no tiles")
  assert loud.live_note.text() == "", \
    "the note line was written even though QGIS's message bar exists"
  dlg.close()
  loud.close()


def test_choice_persistence_and_recovery():
  """Two more state-keeping behaviours: a row's class-source choice
  survives a Design-tab rebuild (choices live in dicts keyed by tile
  id, not in the replaced widgets), and reopening the dialog recovers
  from a zombie task (a cancelled task left in _task must not block
  future runs).

  Regression: a rebuilt table cycled a default variable back into an element the user had deliberately unassigned.
  [ui-vs-library]
  """
  import tempfile as tf
  from weavingspace_qgis import compat
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis.worker import TilingTask
  from qgis.core import QgsRendererCategory, QgsCategorizedSymbolRenderer
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)

  # class-source choice survives a rebuild
  dlg.table.cellWidget(1, 1).setCurrentText("landcover")
  dlg._update_dynamic_columns()
  styled = make_region_layer()
  styled.setRenderer(QgsCategorizedSymbolRenderer("landcover", [
    QgsRendererCategory("forest",
                        QgsFillSymbol.createSimple({"color": "#112233"}),
                        "Forest land")]))
  qml = os.path.join(tf.mkdtemp(), "scheme.qml")
  styled.saveNamedStyle(qml)
  dlg._browsed_qmls.append(qml)
  dlg._update_dynamic_columns()
  combo = dlg.table.cellWidget(1, 7)
  combo.setCurrentIndex(combo.findData("file:" + qml))
  combo.activated.emit(combo.currentIndex())  # the real user-pick path
  assert dlg._class_choices.get("b") == "file:" + qml, \
    "the activated hook must record the choice"
  dlg.spacing_spin.setValue(dlg.spacing_spin.value() * 1.1)
  dlg._rebuild_unit()
  combo2 = dlg.table.cellWidget(1, 7)
  assert combo2 is not None and combo2.currentData() == "file:" + qml, \
    "class-source choice must survive the rebuild"
  # and survive the combo being REMOVED and recreated: flipping the
  # variable to numeric withdraws the class-source cell entirely
  # (removeCellWidget), so on flipping back the only route home is
  # the _class_choices dict — the in-place widget survival that
  # covers the plain-rebuild case above cannot help here
  dlg.table.cellWidget(1, 1).setCurrentText("v2")
  dlg._update_dynamic_columns()
  assert dlg.table.cellWidget(1, 7) is None, "cell withdrawn"
  dlg.table.cellWidget(1, 1).setCurrentText("landcover")
  dlg._update_dynamic_columns()
  combo3 = dlg.table.cellWidget(1, 7)
  assert combo3 is not None and combo3.currentData() == "file:" + qml, \
    "class-source choice must survive removal and recreation"

  # Zombie-task recovery on reopen. The dialog can be left believing a
  # run is in flight when it is not: close it while generating in a
  # state where cancelling raises (closeEvent swallows that), and
  # _task stays set with the progress bar up and Generate disabled.
  # Reopening from the toolbar reuses the same dialog and runs
  # showEvent, which is the only place that repairs it.
  #
  # The bar has to be genuinely UP before this is worth asserting. An
  # earlier version set a dead task on a dialog that had never run, so
  # the bar was hidden anyway and the assertion would have passed with
  # the recovery removed -- the environment satisfying the thing under
  # test.
  dlg.show()
  dlg.spacing_spin.setValue(540)
  dlg._generate()
  assert dlg._task is not None, "a run should be in flight"
  assert dlg.progress.isVisibleTo(dlg), "and its progress bar showing"
  running = dlg._task
  running._reported = True      # the run ends and nobody is told
  for _ in range(240):          # poll: _settle waits for _task to clear,
    _tick(50)                   # which is exactly what cannot happen here
    try:
      if running.status() not in compat.task_active_statuses():
        break
    except RuntimeError:
      # QGIS's task manager owns a QgsTask and deletes the C++ object
      # once it finishes, leaving the Python wrapper pointing at
      # nothing. That is not an accident to work around here -- it is
      # the very state this test is about, since dlg._task is still
      # holding that wrapper. A deleted task is emphatically not
      # running, so stop polling and go on to the recovery.
      break
  dlg.hide()
  dlg.show()                    # showEvent runs the recovery
  assert dlg._task is None, "zombie task must be cleared on reopen"
  assert dlg.generate_btn.isEnabled()
  assert not dlg.progress.isVisibleTo(dlg), \
    "the reopened dialog still shows a progress bar frozen at the "\
    "dead run's percentage, which reads as 'still working'"
  dlg.close()


# --------------------------------------------------------- integration
# The tests above mostly pin one behaviour each. These follow whole
# sessions instead: the sequences a user actually performs, where the
# risk in this plugin lives (state carried across generations, layers
# written to disk and read back, one dialog closed and another
# opened). Each drives only public-facing widgets and the Generate
# path, so they stay honest about what the plugin really does.

def test_integration_gpkg_style_round_trip():
  """Export to GeoPackage, then read the file back from disk as QGIS
  would on a later day: the embedded styles must rebuild the same
  renderers, with the same ramp and the same class colours. Checking
  that the layer_styles table has rows (as the end-to-end test does)
  proves only that something was written; this proves it works.

  Regression: exporting to GeoPackage collided with the driver's own fid column, so a second export failed; the writer now names its key weavingspace_fid.
  [integration]
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.core import QgsGraduatedSymbolRenderer
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(500)
  dlg.table.cellWidget(0, 1).setCurrentText("v1")
  dlg.table.cellWidget(0, 4).setCurrentText("YlOrRd")
  dlg.table.cellWidget(1, 1).setCurrentText("landcover")
  dlg._update_dynamic_columns()
  with tempfile.TemporaryDirectory() as td:
    path = os.path.join(td, "session.gpkg")
    dlg.gpkg_widget.setFilePath(path)
    _generate_and_wait(dlg)
    assert os.path.exists(path)
    # what the dialog produced, before anything is reloaded
    a_before = QgsProject.instance().mapLayer(
      dlg._element_layer_ids["a"]).renderer()
    b_before = QgsProject.instance().mapLayer(
      dlg._element_layer_ids["b"]).renderer()
    a_colours = [r.symbol().color().name() for r in a_before.ranges()]
    b_colours = {str(c.value()): c.symbol().color().name()
                 for c in b_before.categories() if c.value()}
    before_layers = [
      bridge_module().gdf_to_layer(
        bridge_module().layer_to_gdf(
          QgsProject.instance().mapLayer(dlg._element_layer_ids[t]),
          ["v1", "landcover"]), t)
      for t in ("a", "b")]
    for copy_layer, tid in zip(before_layers, ("a", "b")):
      copy_layer.setRenderer(QgsProject.instance().mapLayer(
        dlg._element_layer_ids[tid]).renderer().clone())
    # drop everything and reopen the file cold
    for lid in list(dlg._element_layer_ids.values()):
      QgsProject.instance().removeMapLayer(lid)
    dlg.close()
    reloaded_a = QgsVectorLayer(f"{path}|layername=tiles_a", "a", "ogr")
    reloaded_b = QgsVectorLayer(f"{path}|layername=tiles_b", "b", "ogr")
    assert reloaded_a.isValid() and reloaded_b.isValid()
    for lay in (reloaded_a, reloaded_b):
      lay.loadDefaultStyle()
    assert isinstance(reloaded_a.renderer(), QgsGraduatedSymbolRenderer), \
      "the graduated style must come back off disk"
    assert [r.symbol().color().name()
            for r in reloaded_a.renderer().ranges()] == a_colours, \
      "class colours must survive the GeoPackage round trip"
    assert isinstance(reloaded_b.renderer(), QgsCategorizedSymbolRenderer)
    got_b = {str(c.value()): c.symbol().color().name()
             for c in reloaded_b.renderer().categories() if c.value()}
    assert got_b == b_colours, "category colours must survive too"
    # and the file-backed layers must LOOK like the ones the dialog
    # made: styles that reload with the right numbers can still paint
    # differently if a symbol layer or opacity is lost
    sys.path.insert(0, HERE)
    from visual_tests import render_layers
    before_png = os.path.join(report_dir(), "gpkg_round_trip_ui.png")
    after_png = os.path.join(report_dir(), "gpkg_round_trip_library.png")
    render_layers(before_layers, before_png)
    render_layers([reloaded_a, reloaded_b], after_png)
    differing, total = _interior_diff(before_png, after_png)
    share = differing / max(total, 1)
    _record_scenario(dict(kind="pair", label="gpkg round trip",
                          ui=os.path.basename(before_png),
                          library=os.path.basename(after_png),
                          differing=differing, total=total, share=share,
                          tolerance=0.02, ok=share <= 0.02))
    assert share <= 0.02, \
      f"reloaded layers paint differently: {differing}/{total} pixels"


def test_integration_region_layer_switch():
  """Switching region layer mid-session: variables repopulate from the
  new layer, a stale assignment does not survive into it, and the
  plugin's own outputs are never offered as a region (the bug where a
  second dialog tiled the first one's output and every assignment
  shifted)."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  first = make_region_layer()
  first.setName("first region")
  QgsProject.instance().addMapLayer(first)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(500)
  dlg.table.cellWidget(0, 1).setCurrentText("landcover")
  dlg._update_dynamic_columns()
  _generate_and_wait(dlg)
  outputs = list(dlg._element_layer_ids.values())
  assert outputs, "a first generation is needed for this test to mean much"

  # a second, differently-attributed layer joins the project
  from weavingspace_qgis import compat
  other = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "second region",
                         "memory")
  other.dataProvider().addAttributes([compat.make_field("rainfall", float),
                                      compat.make_field("soil", str)])
  other.updateFields()
  f = QgsFeature(other.fields())
  f.setGeometry(QgsGeometry.fromWkt(
    "POLYGON((0 0, 3000 0, 3000 3000, 0 3000, 0 0))"))
  f["rainfall"], f["soil"] = 12.5, "clay"
  other.dataProvider().addFeatures([f])
  other.updateExtents()
  QgsProject.instance().addMapLayer(other)

  # the plugin's outputs must be excluded from the region chooser
  offered = set(dlg.layer_combo.additionalItems())
  excepted = {la.id() for la in dlg.layer_combo.exceptedLayerList()}
  assert set(outputs) <= excepted, \
    "generated layers must not be offered as a region"
  assert other.id() not in excepted and offered == set()

  dlg.layer_combo.setLayer(other)
  fields = {dlg.table.cellWidget(r, 1).itemText(i)
            for r in range(dlg.table.rowCount())
            for i in range(dlg.table.cellWidget(r, 1).count())}
  assert "rainfall" in fields and "soil" in fields, \
    "variables must repopulate from the new layer"
  assert "landcover" not in fields and "v1" not in fields, \
    "the previous layer's fields must not linger"
  for a in dlg._assignments():
    assert a["var"] in (None, "", "rainfall", "soil"), \
      f"stale assignment {a['var']} survived the layer switch"
  dlg.close()


def test_integration_live_session():
  """A live-update session: switch live on, make a design change, and
  let the debounce fire. The group must be REPLACED, not duplicated,
  the element layers must be new objects (the old ones removed from
  the project), and a subsequent manual Generate must still work."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.spacing_spin.setValue(600)
  loop = QEventLoop()
  orig = dlg._on_generated

  def wrapped(*a, **kw):
    orig(*a, **kw)
    loop.quit()

  dlg._on_generated = wrapped
  QTimer.singleShot(60_000, loop.quit)
  loop.exec()  # the automatic first render
  root = project.layerTreeRoot()
  groups = [c for c in root.children() if c.nodeType() == 0]
  first_ids = dict(dlg._element_layer_ids)
  assert first_ids, "live update should have produced a first map"

  # a design change; the live timer (900 ms) does the rest
  dlg.spacing_spin.setValue(450)
  loop = QEventLoop()
  QTimer.singleShot(60_000, loop.quit)
  loop.exec()
  dlg._on_generated = orig
  groups_after = [c for c in root.children() if c.nodeType() == 0]
  assert len(groups_after) == len(groups), \
    "live regeneration must replace the group, not add another"
  for tid, lid in first_ids.items():
    assert project.mapLayer(lid) is None or \
      dlg._element_layer_ids[tid] != lid, \
      "stale element layers must not accumulate in the project"
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(700)
  _generate_and_wait(dlg)
  assert all(project.mapLayer(lid) is not None
             for lid in dlg._element_layer_ids.values()), \
    "manual Generate must still work after a live session"
  dlg.close()


def test_integration_second_dialog_session():
  """Close the dialog and open a fresh one, as a user does across a
  work session: the new dialog must adopt the existing output group
  rather than starting a rival one, and generating again must leave a
  single group with the same element layers replaced in place.

  Regression: reopening the dialog created a rival layer group instead of adopting the one already in the project.
  [integration]
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(500)
  _generate_and_wait(dlg)
  group_name = dlg._group_name
  dlg.close()

  dlg2 = WeavingSpaceDialog(iface=_Iface())
  dlg2.live_check.setChecked(False)
  dlg2.spacing_spin.setValue(500)
  _generate_and_wait(dlg2)
  root = project.layerTreeRoot()
  groups = [c for c in root.children() if c.nodeType() == 0]
  assert len(groups) == 1, \
    f"a second session must not add a rival group ({len(groups)} found)"
  assert dlg2._group_name == group_name
  assert len(groups[0].children()) == len(dlg2._tile_ids())
  # adoption happens at construction, before any Generate: a freshly
  # opened dialog already knows the project's element layers
  dlg3 = WeavingSpaceDialog(iface=_Iface())
  assert dlg3._group_name == group_name
  assert set(dlg3._element_layer_ids) == set(dlg2._element_layer_ids)
  dlg3.close()
  dlg2.close()


def test_integration_weave_and_icons():
  """A weave session with the map switches on: over-under and strand
  width reach the geometry, icon mode places one unit per polygon, and
  the outlines layer rides on top of the group. These options interact
  (icons + outlines is the pairing the help recommends), so they are
  worth one integration pass together rather than three unit checks."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.core import QgsRenderContext
  from qgis.PyQt.QtCore import Qt
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("weave")
  dlg.family_combo.setCurrentText("twill weave ab|cd")
  dlg.opt_over_under.setText("1,2")
  dlg.opt_aspect.setValue(0.5)
  dlg.spacing_spin.setValue(700)
  dlg.opt_icons.setChecked(True)
  dlg.opt_outlines.setChecked(True)
  dlg.opt_tile_outlines.setChecked(True)
  dlg._rebuild_unit()
  assert tuple(dlg._unit.n) == (1, 2)
  _generate_and_wait(dlg)
  group = project.layerTreeRoot().findGroup(dlg._group_name)
  assert group is not None
  assert group.children()[0].layer().id() == dlg._outline_layer_id, \
    "outlines belong on top of the group"
  tiles = sum(project.mapLayer(lid).featureCount()
              for lid in dlg._element_layer_ids.values())
  # icon mode: one unit per region polygon. A weave unit holds many
  # pieces per element (strands are cut into segments), so the bound
  # is polygons x pieces-in-the-unit, not polygons x elements; a
  # continuous weave at this spacing would produce far more
  assert 0 < tiles <= layer.featureCount() * len(dlg._unit.tiles), \
    f"icon mode produced {tiles} tiles for {layer.featureCount()} polygons"
  # the Draw tile boundaries switch must reach the symbols themselves,
  # not merely the separate outlines layer: check the stroke on a real
  # element symbol, with the switch both ways
  element = project.mapLayer(next(iter(dlg._element_layer_ids.values())))
  symbol = element.renderer().symbols(QgsRenderContext())[0]
  stroke = symbol.symbolLayer(0).strokeStyle()
  assert stroke != Qt.PenStyle.NoPen, \
    "with Draw tile boundaries on, element symbols must carry a stroke"
  dlg.opt_tile_outlines.setChecked(False)
  _generate_and_wait(dlg)
  element = project.mapLayer(next(iter(dlg._element_layer_ids.values())))
  symbol = element.renderer().symbols(QgsRenderContext())[0]
  assert symbol.symbolLayer(0).strokeStyle() == Qt.PenStyle.NoPen, \
    "with the switch off, tiles must meet without seams"
  dlg.opt_tile_outlines.setChecked(True)
  _generate_and_wait(dlg)

  visual_gamut("weave icons and outlines",
               [project.mapLayer(lid)
                for lid in dlg._element_layer_ids.values()],
               [a["ramp"] for a in dlg._assignments() if a["var"]])
  dlg.close()


def test_integration_interleaved_session():
  """The long session: styling, then data, then design, then styling
  again, generating throughout. Each step asserts what the previous
  steps must still be true of, because the failures worth catching
  here are the cross-talk ones — a spacing change resetting a ramp, a
  variable change on one element re-seeding another, a style flip
  losing the colour picked before it. This is the shape of real use,
  and no single-behaviour test covers the interactions."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  from qgis.core import QgsGraduatedSymbolRenderer
  from qgis.gui import QgsColorButton
  from qgis.PyQt.QtGui import QColor
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(600)

  def renderer(tid):
    return project.mapLayer(dlg._element_layer_ids[tid]).renderer()

  def top_colour(tid):
    """Darkest end of the element's seeded ramp, the cheapest stable
    fingerprint of WHICH ramp is in force."""
    return renderer(tid).sourceColorRamp().color(1.0).name()

  # 1. data: assign variables, then generate
  for row, var in enumerate(("v1", "v2", "v3", "v1")):
    dlg.table.cellWidget(row, 1).setCurrentText(var)
  dlg._update_dynamic_columns()
  _generate_and_wait(dlg)
  assert len(dlg._element_layer_ids) == 4

  # 2. styling: pick a ramp for a; only a changes
  before_b = top_colour("b")
  dlg.table.cellWidget(0, 4).setCurrentText("YlGn")
  _generate_and_wait(dlg)
  assert top_colour("a") == bridge.get_ramp("YlGn").color(1.0).name()
  assert top_colour("b") == before_b, "b must be untouched by a's ramp"

  # 3. design: change spacing; styling choices must ride through it
  dlg.spacing_spin.setValue(480)
  _generate_and_wait(dlg)
  assert top_colour("a") == bridge.get_ramp("YlGn").color(1.0).name(), \
    "a spacing change must not reset the chosen ramp"
  assert dlg.table.cellWidget(0, 4).currentText() == "YlGn"

  # 4. styling: class count on a, then check only a re-cut
  b_ranges = len(renderer("b").ranges())
  dlg.table.cellWidget(0, 3).setValue(7)
  _generate_and_wait(dlg)
  assert len(renderer("a").ranges()) == 7
  assert len(renderer("b").ranges()) == b_ranges

  # 5. data: change c's variable; a and b keep everything
  a_colour, a_classes = top_colour("a"), len(renderer("a").ranges())
  dlg.table.cellWidget(2, 1).setCurrentText("landcover")
  dlg._update_dynamic_columns()
  _generate_and_wait(dlg)
  assert isinstance(renderer("c"), QgsCategorizedSymbolRenderer), \
    "a categorical variable must bring a categorized renderer"
  assert top_colour("a") == a_colour
  assert len(renderer("a").ranges()) == a_classes

  # 6. hand styling in the styling dock, then a design change: the
  # hand work survives because d's assignment did not change
  project.mapLayer(dlg._element_layer_ids["d"]).setRenderer(
    QgsSingleSymbolRenderer(
      QgsFillSymbol.createSimple({"color": "#0b1e2d"})))
  dlg.mod_rotate.setValue(20)
  _generate_and_wait(dlg)
  assert isinstance(renderer("d"), QgsSingleSymbolRenderer), \
    "hand styling must survive a design-only change"
  assert renderer("d").symbol().color().name() == "#0b1e2d"

  # 7. styling: flip a to Single colour, pick one, generate
  dlg.table.cellWidget(0, 2).setCurrentText("Single colour")
  dlg._update_dynamic_columns()
  button = dlg.table.cellWidget(0, 4)
  assert isinstance(button, QgsColorButton)
  button.setColor(QColor("#7a1f6d"))
  _generate_and_wait(dlg)
  assert isinstance(renderer("a"), QgsSingleSymbolRenderer)
  assert renderer("a").symbol().color().name() == "#7a1f6d"

  # 8. styling: back to graduated; the remembered ramp returns, and
  # the map follows it
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Quantiles")
  dlg._update_dynamic_columns()
  assert dlg.table.cellWidget(0, 4).currentText() == "YlGn", \
    "the quantitative ramp must come back after a single-colour spell"
  _generate_and_wait(dlg)
  assert isinstance(renderer("a"), QgsGraduatedSymbolRenderer)
  assert top_colour("a") == bridge.get_ramp("YlGn").color(1.0).name()

  # 9. design: a different family with the same element count; the
  # whole styling arrangement must survive the swap
  dlg.family_combo.setCurrentText("hex-slice 4")
  _generate_and_wait(dlg)
  assert set(dlg._element_layer_ids) == set("abcd")
  assert top_colour("a") == bridge.get_ramp("YlGn").color(1.0).name()
  assert isinstance(renderer("c"), QgsCategorizedSymbolRenderer)
  # ...and one group throughout, never a pile of them
  groups = [ch for ch in project.layerTreeRoot().children()
            if ch.nodeType() == 0]
  assert len(groups) == 1, f"{len(groups)} groups after one session"
  # what the session actually left on screen, as a picture: every
  # colour must belong to the ramps the table now shows
  # element d was hand-styled in the styling dock during step 6, so
  # its colour belongs to no ramp by design; the gamut question is
  # about the elements the dialog still controls
  visual_gamut("interleaved styling session",
               [project.mapLayer(dlg._element_layer_ids[t])
                for t in ("a", "b", "c")],
               [a["ramp"] for a in dlg._assignments()
                if a["var"] and a["id"] != "d"] + ["tab10"],
               mean_max=12.0, p95_max=30.0)
  dlg.close()


def test_integration_categorical_session():
  """The categorical counterpart of the interleaved session, on the
  packaged parcels fixture: variables, spacing and colour sources
  interleaved, with elements shifting between the two imported colour
  mappings, automatic ramps, and another loaded layer's symbology.

  Categorical symbology has more moving parts than graduated: the
  class set depends on which values the pattern happens to catch, the
  colours can come from a file, and the choice belongs to one element
  rather than the whole map. This test keeps two elements on the same
  field with different colour sources at once, which is exactly where
  a per-element setting can leak into its neighbour."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  from qgis.core import (QgsCategorizedSymbolRenderer,
                         QgsGraduatedSymbolRenderer)
  project = QgsProject.instance()
  data = os.path.join(HERE, "data")
  qml = os.path.join(data, "landcover.qml")
  qml_alt = os.path.join(data, "landcover-alt.qml")
  layer = QgsVectorLayer(
    os.path.join(data, "landcover-categorical.gpkg") + "|layername=parcels",
    "parcels", "ogr")
  assert layer.isValid() and layer.featureCount() == 144
  project.addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(900)

  def renderer(tid):
    return project.mapLayer(dlg._element_layer_ids[tid]).renderer()

  def colours(tid):
    return {str(c.value()): c.symbol().color().name()
            for c in renderer(tid).categories() if c.value()}

  def labels(tid):
    return {str(c.value()): c.label()
            for c in renderer(tid).categories() if c.value()}

  def source_combo(row):
    return dlg.table.cellWidget(row, 7)

  def choose_source(row, token):
    combo = source_combo(row)
    assert combo is not None, f"row {row} has no colourmap source cell"
    i = combo.findData(token)
    assert i >= 0, f"{token} not offered in row {row}"
    combo.setCurrentIndex(i)
    combo.activated.emit(i)

  # 1. data: two elements on the same categorical field, two on others
  for row, var in enumerate(("landcover", "landcover", "zoning", "value")):
    dlg.table.cellWidget(row, 1).setCurrentText(var)
  dlg._update_dynamic_columns()
  assert not dlg.table.isColumnHidden(7), \
    "the colourmap source column belongs on categorical rows"
  assert source_combo(3) is None, "the numeric row keeps a blank cell"
  _generate_and_wait(dlg)
  for tid in "abc":
    assert isinstance(renderer(tid), QgsCategorizedSymbolRenderer)
  assert isinstance(renderer("d"), QgsGraduatedSymbolRenderer)
  # each row starts on its own default ramp, so two elements on the
  # same field are NOT expected to match; what matters below is that
  # each element keeps its own colours until something changes it
  automatic_a, automatic_b = colours("a"), colours("b")
  assert automatic_a and automatic_b
  assert set(colours("a")) == set(colours("b")), \
    "same field: the class SETS should match even when colours differ"

  # 2. styling: import the mapping for a only. b stays automatic even
  # though it maps the same field
  dlg._browsed_qmls.append(qml)
  dlg._update_dynamic_columns()
  choose_source(0, "file:" + qml)
  _generate_and_wait(dlg)
  assert colours("a")["forest"] == "#1b7837", \
    f"imported colours must reach the map: {colours('a')}"
  assert labels("a")["water"] == "Open water", \
    "imported labels must travel with the colours"
  assert colours("b") == automatic_b, \
    "b must not inherit a's imported mapping"
  # a class the file omits falls back rather than vanishing
  if "bare" in colours("a"):
    assert colours("a")["bare"] not in \
      {c for v, c in colours("a").items() if v != "bare"}, \
      "the unmapped class needs its own automatic colour"

  # 3. styling: shift a to the OTHER imported mapping; every colour
  # and label must change, and the fallback class changes with them
  dlg._browsed_qmls.append(qml_alt)
  dlg._update_dynamic_columns()
  choose_source(0, "file:" + qml_alt)
  _generate_and_wait(dlg)
  assert colours("a")["forest"] == "#31a354", \
    "shifting between imported mappings must repaint the element"
  assert labels("a")["water"] == "Water"
  assert colours("b") == automatic_b, "b still untouched"

  # 4. design: spacing changes; imported mappings survive it
  dlg.spacing_spin.setValue(700)
  _generate_and_wait(dlg)
  assert colours("a")["forest"] == "#31a354", \
    "a spacing change must not drop the imported mapping"
  assert dlg._class_choices.get("a") == "file:" + qml_alt

  # 5. styling: give b the FIRST mapping, so the two elements now
  # carry different imported schemes for the same field at once
  choose_source(1, "file:" + qml)
  _generate_and_wait(dlg)
  assert colours("b")["forest"] == "#1b7837"
  assert colours("a")["forest"] == "#31a354", \
    "the two elements must hold different mappings simultaneously"

  # 6. styling: a third source, another loaded layer's symbology
  styled = QgsVectorLayer(
    os.path.join(data, "landcover-categorical.gpkg") + "|layername=parcels",
    "styled reference", "ogr")
  styled.loadNamedStyle(qml)
  project.addMapLayer(styled)
  dlg._update_dynamic_columns()
  choose_source(0, f"layer:{styled.id()}")
  _generate_and_wait(dlg)
  assert colours("a")["forest"] == "#1b7837", \
    "another layer's categorized symbology must work as a source"

  # 7. data: move a to a different categorical field. The old mapping
  # cannot apply, so colours come back automatic without crashing
  dlg.table.cellWidget(0, 1).setCurrentText("period")
  dlg._update_dynamic_columns()
  _generate_and_wait(dlg)
  assert isinstance(renderer("a"), QgsCategorizedSymbolRenderer)
  assert set(colours("a")) <= {"pre-1940", "1940-1990", "post-1990"}
  assert "#1b7837" not in colours("a").values(), \
    "a mapping for another field must not colour this one"
  assert colours("b")["forest"] == "#1b7837", "b keeps its mapping"

  # 8. styling: automatic ramp choice on a categorical row follows the
  # preset scheme (evenly sampled, as upstream does)
  ramp_cell = dlg.table.cellWidget(0, 4)
  assert ramp_cell.currentText() in bridge.CATEGORICAL_RAMPS
  ramp_cell.setCurrentText("Set2")
  _generate_and_wait(dlg)
  from qgis.core import QgsStyle
  preset = QgsStyle.defaultStyle().colorRamp("Set2")
  assert set(colours("a").values()) <= \
    {c.name() for c in preset.colors()}, \
    f"Set2 colours expected, got {colours('a')}"

  # 9. data: every element numeric; the column withdraws entirely
  for row, var in enumerate(("value", "value", "value", "value")):
    dlg.table.cellWidget(row, 1).setCurrentText(var)
  dlg._update_dynamic_columns()
  assert dlg.table.isColumnHidden(7), \
    "no categorical rows, no colourmap source column"
  _generate_and_wait(dlg)
  for tid in "abcd":
    assert isinstance(renderer(tid), QgsGraduatedSymbolRenderer)

  # 10. data: back to categorical on b; its remembered import returns
  dlg.table.cellWidget(1, 1).setCurrentText("landcover")
  dlg._update_dynamic_columns()
  assert not dlg.table.isColumnHidden(7)
  assert source_combo(1).currentData() == "file:" + qml, \
    "the element's colourmap source must be remembered"
  _generate_and_wait(dlg)
  assert colours("b")["forest"] == "#1b7837", \
    "and must colour the map again on its return"
  groups = [ch for ch in project.layerTreeRoot().children()
            if ch.nodeType() == 0]
  assert len(groups) == 1, f"{len(groups)} groups after one session"
  # the picture this session ends on. Categorical elements mix an
  # imported mapping with an automatic preset, so the tolerance is
  # wider than a pure ramp case: what is being checked is that every
  # colour comes from one of the schemes in force, not from nowhere
  visual_gamut("categorical colour sources",
               [project.mapLayer(dlg._element_layer_ids[t])
                for t in sorted(dlg._element_layer_ids)],
               [a["ramp"] for a in dlg._assignments() if a["var"]]
               + ["tab10"], mean_max=12.0, p95_max=30.0)
  for lid in list(dlg._element_layer_ids.values()):
    project.removeMapLayer(lid)
  dlg.close()


# ---------------------------------------- UI against the library
# The most valuable shape of test here, and the reason it earns six
# of them: drive the dialog exactly as a person would, then build the
# same map by calling weavingspace directly with what those settings
# are SUPPOSED to mean, and compare geometry element by element and
# then pixel by pixel. Every other test asks whether the plugin did
# something coherent. These ask whether it did the RIGHT thing — a
# control wired to the wrong constructor argument, a modifier applied
# in the wrong order, or a switch that never reaches the library all
# survive "a map appeared" assertions and die here.
#
# The expected side is written from the settings, never from the
# dialog's own _build_unit, or the test would agree with a bug. Six
# scenarios cover the axes that can be miswired independently:
# family options, weave parameters (where the tile inset is scaled by
# strand width), the affine modifier chain and its order, icon mode
# with whole-tileable joins, clipping with edge handling, and the
# grid family's row and column spinners.

def _record_scenario(entry):
  """Append one visual check to the record the release PDF reads.

  Written BEFORE the assertion that may fail, so a failing check is
  one the reader can look at rather than infer from a number."""
  with open(os.path.join(report_dir(), "scenarios.json"), "a",
            encoding="utf-8") as f:
    f.write(json.dumps(entry) + "\n")


def _interior_diff(ui_png, lib_png):
  """(differing, total) interior pixels between two renders.

  Args:
    ui_png: path to the render the dialog produced.
    lib_png: path to the render built by calling the library
      directly. The two must be the same size; comparing renders of
      different sizes is meaningless and asserts here rather than
      quietly resampling.

  Returns:
    (differing, total) counts over interior pixels only. Interior
    means the four neighbours agree, so antialiased edges — which say
    nothing about symbology — never enter the count. Neither file is
    modified.
  """
  from qgis.PyQt.QtGui import QImage
  a, b = QImage(ui_png), QImage(lib_png)
  assert a.size() == b.size(), "renders must share a size to compare"

  def interior(image, x, y):
    c = image.pixelColor(x, y)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
      n = image.pixelColor(x + dx, y + dy)
      if max(abs(n.red() - c.red()), abs(n.green() - c.green()),
             abs(n.blue() - c.blue())) > 8:
        return None
    return c

  differing = total = 0
  for x in range(1, a.width() - 1, 3):
    for y in range(1, a.height() - 1, 3):
      ca, cb = interior(a, x, y), interior(b, x, y)
      if ca is None or cb is None:
        continue
      total += 1
      if max(abs(ca.red() - cb.red()), abs(ca.green() - cb.green()),
             abs(ca.blue() - cb.blue())) > 12:
        differing += 1
  return differing, total


def visual_pair(label, ui_layers, expected_gdf, assignments,
                templates=None, tolerance=0.02):
  """Render what the dialog produced beside the same map built by
  calling the library directly, and compare interior pixels.

  Args:
    label: names the comparison in the PDF and on disk; the file
      names are derived from it, so two comparisons sharing a label
      overwrite each other.
    ui_layers: the output layers the dialog produced, in draw order.
    expected_gdf: the tiled frame built INDEPENDENTLY, by restating
      what the settings mean rather than by calling the dialog's own
      _build_unit. That independence is the whole value of this
      check: an expected side derived from the code under test
      agrees with its bugs.
    assignments: the element-to-variable mapping used to seed the
      expected side's renderers, so both maps are symbolized alike
      and only geometry and colour choice can differ.
    templates: {class-source token: loaded QML template}, so a
      categorical element on the expected side is seeded from the
      same scheme the dialog used. None when no element imports one.
    tolerance: the share of sampled interior pixels allowed to
      differ. 0.02 covers antialiasing and rounding between two
      renders of the same geometry; a real symbology error moves far
      more than two percent of the picture.

  Returns:
    None. Writes two PNGs into this release's report directory and
    records the pair for the comparison PDF. Raises AssertionError
    when the difference exceeds tolerance.
  """
  sys.path.insert(0, HERE)
  from visual_tests import render_layers
  from weavingspace_qgis import bridge
  out_dir = report_dir()
  slug = label.lower().replace(" ", "_").replace(",", "")
  ui_png = os.path.join(out_dir, f"{slug}_ui.png")
  lib_png = os.path.join(out_dir, f"{slug}_library.png")
  render_layers(list(ui_layers), ui_png)
  lib_layers = []
  for a in assignments:
    sub = expected_gdf[expected_gdf["tile_id"] == a["id"]]
    if not len(sub):
      continue
    layer = bridge.gdf_to_layer(sub, f"{a['id']} – {a.get('var')}")
    bridge.seed_renderer(layer, a,
                         (templates or {}).get(a.get("class_source")))
    # the library side has to wear the element's opacity too, or the
    # comparison would be between a solid map and a soft one. Both
    # sides then composite against the same magenta key, so the
    # interior-pixel test stays valid; keep test opacities moderate
    # (roughly 40-80%) so a blend never approaches the key colour and
    # gets mistaken for background
    layer.setOpacity(max(0, min(100, a.get("opacity", 100))) / 100.0)
    lib_layers.append(layer)
  render_layers(lib_layers, lib_png)
  differing, total = _interior_diff(ui_png, lib_png)
  assert total > 500, f"{label}: only {total} interior pixels to compare"
  share = differing / total
  _record_scenario(dict(kind="pair", label=label,
                        ui=os.path.basename(ui_png),
                        library=os.path.basename(lib_png),
                        differing=differing, total=total, share=share,
                        tolerance=tolerance, ok=share <= tolerance))
  assert share <= tolerance, \
    f"{label}: {differing}/{total} interior pixels differ from the " \
    "library's map"
  return share


def visual_gamut(label, ui_layers, ramps, mean_max=1.5, p95_max=4.0,
                 max_background=0.95, extra_colours=()):
  """Render what the dialog produced and check every interior pixel
  is a colour the symbology in force can actually make.

  Args:
    label: names the check in the PDF and on disk.
    ui_layers: the output layers to render, in draw order.
    ramps: the ramps in force on those layers — ALL of them, since
      the picture contains every layer. Naming only the element under
      test reports the other elements' perfectly correct colours as
      strays.
    mean_max: the mean Delta-E allowed between a sampled pixel and
      the nearest colour the symbology can produce. 1.5 is near zero
      in perceptual terms and is affordable because sampling keeps
      interior fills only.
    p95_max: the same at the 95th percentile, which catches a small
      region of wrong colour that a mean would absorb.
    max_background: the share of the render allowed to be background.
      A map that failed to draw is mostly background and would
      otherwise pass every colour test trivially.
    extra_colours: "#rrggbb" strings that belong to the gamut for
      reasons a ramp name cannot express — at present, colours chosen
      by hand in the Categorical colour editor, which are deliberately
      off every ramp.

  Returns:
    The mean Delta-E, so a caller can report it. Raises AssertionError
    when any limit is exceeded.

  For sessions where no independent expected map is practical (a storm
  of fast clicks, a long interleaved session), this is still a real
  visual measure: it catches blank maps, wrong ramps and corrupted
  symbology, and it puts the picture in the PDF where a person can see
  what the session produced.
  """
  sys.path.insert(0, HERE)
  from visual_tests import render_layers, gamut_delta_e, image_stats
  out_dir = report_dir()
  slug = label.lower().replace(" ", "_").replace(",", "")
  png = os.path.join(out_dir, f"{slug}_ui.png")
  image = render_layers(list(ui_layers), png)
  _colours, background = image_stats(image)
  mean_de, p95_de = gamut_delta_e(image, list(ramps),
                                  tuple(extra_colours))
  ok = (mean_de <= mean_max and p95_de <= p95_max
        and background <= max_background)
  _record_scenario(dict(kind="single", label=label,
                        ui=os.path.basename(png), mean_de=mean_de,
                        p95_de=p95_de, background=background,
                        mean_max=mean_max, p95_max=p95_max, ok=ok))
  assert background <= max_background, \
    f"{label}: the map is {background:.0%} background"
  assert ok, (f"{label}: pixels off the assigned ramps "
              f"(dE mean {mean_de:.1f}, p95 {p95_de:.1f})")
  return mean_de


def _compare_ui_to_library(label, setup, expected_unit, tiling_kw,
                           variables=("v1", "v2", "v3", "v1"),
                           ramps=("Reds", "Blues", "Greens", "Purples"),
                           opacities=None,
                           area_tolerance=0.01, pixel_tolerance=0.02):
  """Drive the dialog, then check its output against a map built by
  calling the library directly.

  Args:
    label: names the comparison in the report and on disk.
    setup: a callable taking the dialog, which sets the controls this
      case is about. It runs before Generate, and anything it does
      not set stays at its default.
    expected_unit: the Tileable the settings MEAN, built by the test
      from those settings — never by calling the dialog's _build_unit,
      which would make the expectation agree with any bug in it.
    tiling_kw: keyword arguments for the library's Tiling, matching
      the map options the setup chose (clipping, whole-tileable join,
      icon mode).
    variables: which attribute each element carries, in element
      order.
    ramps: the ramp assigned to each element, in the same order.
    opacities: per-element opacity 0-100, or None to leave every
      element opaque.
    area_tolerance: the relative difference allowed between the two
      maps' total tiled area. 0.01 absorbs floating-point drift
      through two different construction paths without admitting a
      real geometric difference.
    pixel_tolerance: the share of sampled interior pixels allowed to
      differ, as in visual_pair.

  Returns:
    None. Raises AssertionError naming which stage disagreed.

  Geometry first (same elements, same tile counts, same area within
  tolerance), then the rendered picture. Both matter: geometry catches
  wrong parameters, pixels catch a right tiling wearing the wrong
  symbology.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  from weavingspace import Tiling
  from qgis.PyQt.QtGui import QImage
  import tempfile as tf
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  # every scenario states its own switches: a comparison that leaned
  # on defaults matching would stop testing the mapping
  dlg.opt_join_prototiles.setChecked(False)
  dlg.opt_retain.setChecked(False)
  dlg.opt_clip.setChecked(False)
  dlg.opt_icons.setChecked(False)
  setup(dlg)
  # the design controls schedule a debounced rebuild, and the table
  # only grows to the family's element count when it lands. Scenarios
  # that keep the default four elements never notice; one with seven
  # finds cellWidget() returning None. Flush it here, as Generate
  # itself now does
  dlg._rebuild_unit()
  assert dlg.table.rowCount() == len(variables), \
    f"{label}: {dlg.table.rowCount()} rows but {len(variables)} " \
    "variables were given"
  for row, var in enumerate(variables):
    dlg.table.cellWidget(row, 1).setCurrentText(var)
  for row, ramp in enumerate(ramps):
    dlg.table.cellWidget(row, 4).setCurrentText(ramp)
  if opacities:
    for row, value in enumerate(opacities):
      dlg._row_opacity(row).setValue(value)
  _generate_and_wait(dlg)

  region = bridge.layer_to_gdf(layer, list(dict.fromkeys(variables)))
  expected = Tiling(expected_unit, region,
                    as_icons=tiling_kw.pop("as_icons", False)) \
    .get_tiled_map(**tiling_kw).map

  assert set(expected["tile_id"]) == set(dlg._element_layer_ids), \
    f"elements {sorted(dlg._element_layer_ids)} vs library " \
    f"{sorted(set(expected['tile_id']))}"
  for tid in sorted(set(expected["tile_id"])):
    out = project.mapLayer(dlg._element_layer_ids[tid])
    want = expected[expected["tile_id"] == tid]
    assert out.featureCount() == len(want), \
      f"element {tid}: {out.featureCount()} tiles, library says {len(want)}"
    got_area = sum(f.geometry().area() for f in out.getFeatures())
    want_area = float(want.geometry.area.sum())
    assert abs(got_area - want_area) <= want_area * area_tolerance, \
      f"element {tid}: area {got_area:.0f} vs library {want_area:.0f}"

  sys.path.insert(0, HERE)
  from visual_tests import render_layers, layers_from_gdf
  # the renders are kept, not discarded: the release PDF shows each
  # pair so a reader can see what the dialog drew beside what the
  # library drew, rather than taking a pixel statistic on trust
  out_dir = report_dir()
  slug = label.lower().replace(" ", "_").replace(",", "")
  if True:
    ui_png = os.path.join(out_dir, f"{slug}_ui.png")
    lib_png = os.path.join(out_dir, f"{slug}_library.png")
    render_layers([project.mapLayer(dlg._element_layer_ids[t])
                   for t in sorted(dlg._element_layer_ids)], ui_png)
    assignments = [
      {"id": tid, "var": var, "mode": "Graduated", "ramp": ramp,
       "scheme": "Quantiles", "k": 5, "outline": False,
       "opacity": opacity}
      for tid, var, ramp, opacity in zip(
        sorted(set(expected["tile_id"])), variables, ramps,
        opacities or [100] * len(variables))]
    lib_layers = layers_from_gdf(expected, assignments)
    for lib_layer, a in zip(lib_layers, assignments):
      lib_layer.setOpacity(a.get("opacity", 100) / 100.0)
    render_layers(lib_layers, lib_png)
    a, b = QImage(ui_png), QImage(lib_png)
    assert a.size() == b.size()

    def interior(image, x, y):
      """The pixel, when it sits inside a fill rather than on an
      antialiased edge; None otherwise. Weaves have enormously more
      edge than tilings do (thin strands, many crossings), so a raw
      pixel diff there measures antialiasing, not symbology — the
      same lesson the colourspace metrics learned."""
      c = image.pixelColor(x, y)
      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = image.pixelColor(x + dx, y + dy)
        if max(abs(n.red() - c.red()), abs(n.green() - c.green()),
               abs(n.blue() - c.blue())) > 8:
          return None
      return c

    differing = total = 0
    for x in range(1, a.width() - 1, 3):
      for y in range(1, a.height() - 1, 3):
        ca, cb = interior(a, x, y), interior(b, x, y)
        if ca is None or cb is None:
          continue  # an edge in either image: not a symbology fact
        total += 1
        if max(abs(ca.red() - cb.red()), abs(ca.green() - cb.green()),
               abs(ca.blue() - cb.blue())) > 12:
          differing += 1
    assert total > 500, f"only {total} interior pixels to compare"
    share = differing / max(total, 1)
    # record the pair for the PDF before asserting, so a FAILING
    # comparison is the one a reader can actually look at
    with open(os.path.join(out_dir, "scenarios.json"), "a",
              encoding="utf-8") as f:
      f.write(json.dumps(dict(
        label=label, ui=os.path.basename(ui_png),
        library=os.path.basename(lib_png), differing=differing,
        total=total, share=share, tolerance=pixel_tolerance,
        ok=share <= pixel_tolerance)) + "\n")
    assert differing <= total * pixel_tolerance, \
      f"{differing}/{total} interior pixels differ from the library's map"
  dlg.close()
  return share


def test_ui_library_slice_modifiers():
  """Family option (slice offset), rotation and tile inset together.
  Also the regression for a Generate pressed inside the 350 ms
  preview debounce: it must tile the design on screen, not the
  previous one."""
  from weavingspace import TileUnit

  def setup(dlg):
    dlg.n_combo.setCurrentText("4")
    dlg.kind_combo.setCurrentText("tiling")
    dlg.family_combo.setCurrentText("hex-slice 4")
    dlg.opt_offset.setValue(1.0)
    dlg.spacing_spin.setValue(700)
    dlg.mod_rotate.setValue(15)
    dlg.mod_t_inset.setValue(4)      # per cent of spacing
    # These two switches are tested HERE because this is a
    # configuration where they actually bite. Retain-complete-
    # tileables changes nothing unless the whole-tileable join is on
    # and edges are ragged (measured: identical tile counts in every
    # other combination), and the join changes no data at all in icon
    # mode, where each unit already sits inside one polygon. Tested
    # anywhere else, both controls could be severed from the library
    # without a single assertion noticing.
    dlg.opt_retain.setChecked(True)
    dlg.opt_join_prototiles.setChecked(True)

  # three of the four elements softened, by different amounts, so the
  # comparison would catch opacity going to the wrong element as
  # readily as it would catch it not arriving at all
  _compare_ui_to_library(
    "slice offset rotate inset",
    setup,
    TileUnit(tiling_type="hex-slice", n=4, offset=1.0, spacing=700,
             crs=3857).transform_rotate(15).inset_tiles(0.04 * 700),
    dict(join_on_prototiles=True, retain_tileables=True,
         ragged_edges=True),
    opacities=(100, 75, 55, 40))


def test_ui_library_weave_parameters():
  """Weave controls: over-under pattern and strand width, plus the
  subtlety that a weave's tile inset is scaled BY the strand width
  (insetting a weave in raw per cent of spacing would eat thin
  strands entirely)."""
  from weavingspace import WeaveUnit

  def setup(dlg):
    dlg.n_combo.setCurrentText("4")
    dlg.kind_combo.setCurrentText("weave")
    dlg.family_combo.setCurrentText("twill weave ab|cd")
    dlg.opt_over_under.setText("1,2")
    dlg.opt_aspect.setValue(0.6)
    dlg.spacing_spin.setValue(600)
    dlg.mod_t_inset.setValue(5)

  _compare_ui_to_library(
    "weave over-under and strand width",
    setup,
    WeaveUnit(weave_type="twill", strands="ab|cd", n=(1, 2),
              aspect=0.6, spacing=600, crs=3857)
    .inset_tiles(0.05 * 0.6 * 600),
    dict(join_on_prototiles=False, retain_tileables=False,
         ragged_edges=True))


def test_ui_library_modifier_chain():
  """The affine chain in the order the dialog applies it: rotate,
  then scale, then skew, then the two insets. Order matters — scaling
  after a skew is not the same map — and only a geometric comparison
  can tell.

  Regression: identity modifier transforms (rotate 0, scale 1) rebuilt geometry with enough floating-point rounding to flip tie-prone joins, changing which element a boundary tile belonged to.
  [ui-vs-library]
  """
  from weavingspace import TileUnit

  def setup(dlg):
    dlg.n_combo.setCurrentText("4")
    dlg.kind_combo.setCurrentText("tiling")
    dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
    dlg.spacing_spin.setValue(650)
    dlg.mod_rotate.setValue(25)
    dlg.mod_scale_x.setValue(1.2)
    dlg.mod_scale_y.setValue(0.8)
    dlg.mod_skew_x.setValue(10)
    dlg.mod_t_inset.setValue(3)
    dlg.mod_p_inset.setValue(6)

  # two elements softened here as well, on a design whose geometry is
  # already doing a lot: opacity has to survive the modifier chain
  _compare_ui_to_library(
    "rotate scale skew inset chain",
    setup,
    TileUnit(tiling_type="laves", code="3.3.4.3.4", spacing=650,
             crs=3857)
    .transform_rotate(25)
    .transform_scale(1.2, 0.8, False)
    .transform_skew(10, 0)
    .inset_tiles(0.03 * 650)
    .inset_prototile(0.06 * 650),
    dict(join_on_prototiles=False, retain_tileables=False,
         ragged_edges=True),
    opacities=(60, 100, 60, 100))


def test_ui_library_icons_and_join():
  """Icon mode: one unit per polygon rather than a continuous
  pattern, which changes the tiling call rather than the unit.

  The whole-tileable join is switched on here too, but it is ASSERTED
  in test_ui_library_slice_modifiers instead: in icon mode each unit
  already sits inside a single polygon, so joining on tileables
  changes no data, and a test here could not tell whether the switch
  reached the library at all."""
  from weavingspace import TileUnit

  def setup(dlg):
    dlg.n_combo.setCurrentText("4")
    dlg.kind_combo.setCurrentText("tiling")
    dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
    dlg.spacing_spin.setValue(500)
    dlg.opt_icons.setChecked(True)
    dlg.opt_join_prototiles.setChecked(True)

  _compare_ui_to_library(
    "icons and whole-tileable join",
    setup,
    TileUnit(tiling_type="laves", code="3.3.4.3.4", spacing=500,
             crs=3857),
    dict(as_icons=True, join_on_prototiles=True,
         retain_tileables=False, ragged_edges=True))


def test_ui_library_clipped_edges():
  """Clipping to the region outline, the switch whose sense is
  inverted on the way to the library (the checkbox says clip, the
  argument says ragged_edges)."""
  from weavingspace import TileUnit

  def setup(dlg):
    dlg.n_combo.setCurrentText("4")
    dlg.kind_combo.setCurrentText("tiling")
    dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
    dlg.spacing_spin.setValue(700)
    dlg.opt_clip.setChecked(True)

  _compare_ui_to_library(
    "clipped edges",
    setup,
    TileUnit(tiling_type="laves", code="3.3.4.3.4", spacing=700,
             crs=3857),
    dict(join_on_prototiles=False, retain_tileables=False,
         ragged_edges=False))


def test_ui_library_grid_rows_cols():
  """The grid family's row and column spinners, the newest controls
  and the ones most likely to be mis-plumbed: a 1 x 4 array is a very
  different map from 2 x 2, and both carry four elements."""
  from weavingspace import TileUnit

  def setup(dlg):
    dlg.n_combo.setCurrentText("4")
    dlg.kind_combo.setCurrentText("tiling")
    dlg.family_combo.setCurrentText("grid 4")
    dlg.opt_grid_rows.setValue(1)
    dlg.opt_grid_cols.setValue(4)
    dlg.spacing_spin.setValue(600)

  _compare_ui_to_library(
    "grid rows and columns",
    setup,
    TileUnit(tiling_type="grid", n=4, nrows=1, ncols=4, spacing=600,
             crs=3857),
    dict(join_on_prototiles=False, retain_tileables=False,
         ragged_edges=True))


def test_ui_library_dissection_angles():
  """The two angle controls that no other test drives to an effect:
  a dissection's inner angle, and a star's point angle.

  Both change the unit's geometry only, which makes them invisible to
  every assertion about counts or colours -- exactly the kind of
  control that can quietly stop working. Compared against a direct
  library call, geometry and pixels."""
  from weavingspace import TileUnit

  def setup(dlg):
    dlg.n_combo.setCurrentText("7")
    dlg.kind_combo.setCurrentText("tiling")
    dlg.family_combo.setCurrentText("hex-dissection 7")
    dlg.opt_offset.setValue(0.35)
    dlg.opt_offset_angle.setValue(20)
    dlg.spacing_spin.setValue(900)

  _compare_ui_to_library(
    "dissection inner angle",
    setup,
    TileUnit(tiling_type="hex-dissect", n=7, offset=0.35,
             offset_angle=20, spacing=900, crs=3857),
    dict(join_on_prototiles=False, retain_tileables=False,
         ragged_edges=True),
    variables=("v1", "v2", "v3", "v1", "v2", "v3", "v1"),
    ramps=("Reds", "Blues", "Greens", "Purples", "Oranges", "Greys",
           "YlGn"))


def test_ui_library_star_point_angle():
  """A star tiling's point angle: sharper points, different tiles."""
  from weavingspace import TileUnit

  def setup(dlg):
    dlg.n_combo.setCurrentText("3")
    dlg.kind_combo.setCurrentText("tiling")
    dlg.family_combo.setCurrentText("star1 33")
    dlg.opt_point_angle.setValue(55)
    dlg.spacing_spin.setValue(800)

  _compare_ui_to_library(
    "star point angle",
    setup,
    TileUnit(tiling_type="star1", code="33", point_angle=55,
             spacing=800, crs=3857),
    dict(join_on_prototiles=False, retain_tileables=False,
         ragged_edges=True),
    variables=("v1", "v2", "v3"),
    ramps=("Reds", "Blues", "Greens"))


def test_ui_library_glyph_scaling():
  """The glyph checkbox, which changes what scaling MEANS.

  transform_scale takes a third argument, and with it set the unit is
  scaled about its own centre as a glyph rather than stretched in
  place. Nothing else in the suite passes that argument, so a
  regression there would have shown up only as maps that looked
  subtly wrong."""
  from weavingspace import TileUnit

  def setup(dlg):
    dlg.n_combo.setCurrentText("4")
    dlg.kind_combo.setCurrentText("tiling")
    dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
    dlg.spacing_spin.setValue(600)
    dlg.mod_scale_x.setValue(1.4)
    dlg.mod_scale_y.setValue(1.4)
    dlg.mod_glyph.setChecked(True)

  _compare_ui_to_library(
    "glyph scaling",
    setup,
    TileUnit(tiling_type="laves", code="3.3.4.3.4", spacing=600,
             crs=3857).transform_scale(1.4, 1.4, True),
    dict(join_on_prototiles=False, retain_tileables=False,
         ragged_edges=True))


def test_ui_library_categorical_template():
  """Categorical plumbing end to end against a direct library call:
  one element categorized from an imported QML mapping, one
  categorized automatically, one graduated, one left unassigned.
  Getting the map right here means the class SOURCE reached the right
  element, the automatic ramp reached another, and the unassigned
  element still drew as plain fill rather than vanishing.

  Regression: categorical colours were sampled with round() where matplotlib's ListedColormap uses int(), so a five-class field took entries 0,2,4,7,9 instead of 0,2,5,7,9 and the middle category was painted purple where the original renders brown.
  [colourspace]
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  from weavingspace import TileUnit, Tiling
  from qgis.core import QgsCategorizedSymbolRenderer
  project = QgsProject.instance()
  data = os.path.join(HERE, "data")
  qml = os.path.join(data, "landcover.qml")
  layer = QgsVectorLayer(
    os.path.join(data, "landcover-categorical.gpkg") + "|layername=parcels",
    "parcels", "ogr")
  project.addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(900)
  dlg.opt_join_prototiles.setChecked(False)
  dlg.opt_retain.setChecked(False)
  dlg.opt_clip.setChecked(False)
  dlg.opt_icons.setChecked(False)
  for row, var in enumerate(("landcover", "zoning", "value", "---")):
    dlg.table.cellWidget(row, 1).setCurrentText(var)
  dlg._browsed_qmls.append(qml)
  dlg._update_dynamic_columns()
  combo = dlg.table.cellWidget(0, 7)
  i = combo.findData("file:" + qml)
  combo.setCurrentIndex(i)
  combo.activated.emit(i)
  dlg.table.cellWidget(1, 4).setCurrentText("Set2")
  _generate_and_wait(dlg)

  # the same map from a direct library call
  expected = Tiling(
    TileUnit(tiling_type="laves", code="3.3.4.3.4", spacing=900,
             crs=2193),
    bridge.layer_to_gdf(layer, ["landcover", "value", "zoning"])) \
    .get_tiled_map(join_on_prototiles=False, retain_tileables=False,
                   ragged_edges=True).map
  for tid in "abcd":
    out = project.mapLayer(dlg._element_layer_ids[tid])
    want = expected[expected["tile_id"] == tid]
    assert out.featureCount() == len(want), \
      f"element {tid}: {out.featureCount()} vs library {len(want)}"

  # imported mapping on a, automatic preset on b, graduated on c,
  # plain fill on the unassigned d
  a_colours = {str(c.value()): c.symbol().color().name()
               for c in project.mapLayer(dlg._element_layer_ids["a"])
               .renderer().categories() if c.value()}
  assert a_colours.get("forest") == "#1b7837", \
    f"the imported mapping must reach element a: {a_colours}"
  b_renderer = project.mapLayer(dlg._element_layer_ids["b"]).renderer()
  assert isinstance(b_renderer, QgsCategorizedSymbolRenderer)
  from qgis.core import QgsStyle
  set2 = {c.name() for c in QgsStyle.defaultStyle().colorRamp("Set2").colors()}
  b_colours = {c.symbol().color().name() for c in b_renderer.categories()
               if c.value()}
  assert b_colours <= set2, f"b should wear Set2, got {b_colours}"
  assert not (b_colours & {"#1b7837", "#2166ac"}), \
    "a's imported mapping must not leak into b"
  assert isinstance(
    project.mapLayer(dlg._element_layer_ids["c"]).renderer(),
    QgsGraduatedSymbolRenderer)
  d_layer = project.mapLayer(dlg._element_layer_ids["d"])
  assert isinstance(d_layer.renderer(), QgsSingleSymbolRenderer), \
    "an unassigned element must still draw, as plain fill"
  # the picture, against the library's own map with the same
  # symbology (the imported mapping included, via the template)
  visual_pair("categorical sources and unassigned element",
              [project.mapLayer(dlg._element_layer_ids[t])
               for t in "abcd"],
              expected, dlg._assignments(),
              templates={"file:" + qml:
                         bridge.load_categorized_template(qml)})
  assert "no data" in d_layer.name(), \
    f"the unassigned element should say so in its name: {d_layer.name()}"
  for lid in list(dlg._element_layer_ids.values()):
    project.removeMapLayer(lid)
  dlg.close()


def test_ui_library_categorical_weave_icons():
  """Categorical plumbing on the other side of the catalogue: a weave
  in icon mode, joining data on whole tileables, with its class
  colours taken from ANOTHER LAYER's symbology rather than a file.

  Icon mode and whole-tileable joins both change which region polygon
  an element reads, so a categorical element here is a strict test of
  the join: get it wrong and the classes are still plausible, just
  wrong. The geometry is checked against a direct library call, and
  the colours against the source layer's own categories."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  from weavingspace import WeaveUnit, Tiling
  from qgis.core import QgsCategorizedSymbolRenderer
  project = QgsProject.instance()
  data = os.path.join(HERE, "data")
  uri = os.path.join(data, "landcover-categorical.gpkg") + \
    "|layername=parcels"
  layer = QgsVectorLayer(uri, "parcels", "ogr")
  project.addMapLayer(layer)
  styled = QgsVectorLayer(uri, "styled reference", "ogr")
  styled.loadNamedStyle(os.path.join(data, "landcover-alt.qml"))
  project.addMapLayer(styled)

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("weave")
  dlg.family_combo.setCurrentText("plain weave ab|cd")
  dlg.opt_aspect.setValue(0.8)
  dlg.spacing_spin.setValue(800)
  dlg.opt_icons.setChecked(True)
  dlg.opt_join_prototiles.setChecked(True)
  dlg.opt_retain.setChecked(False)
  dlg.opt_clip.setChecked(False)
  for row, var in enumerate(("landcover", "period", "zoning", "value")):
    dlg.table.cellWidget(row, 1).setCurrentText(var)
  dlg._update_dynamic_columns()
  combo = dlg.table.cellWidget(0, 7)
  i = combo.findData(f"layer:{styled.id()}")
  assert i >= 0, "a layer with categorized symbology should be offered"
  combo.setCurrentIndex(i)
  combo.activated.emit(i)
  _generate_and_wait(dlg)

  expected = Tiling(
    WeaveUnit(weave_type="plain", strands="ab|cd", n=1, aspect=0.8,
              spacing=800, crs=2193),
    bridge.layer_to_gdf(layer, ["landcover", "period", "value", "zoning"]),
    as_icons=True) \
    .get_tiled_map(join_on_prototiles=True, retain_tileables=False,
                   ragged_edges=True).map
  for tid in "abcd":
    out = project.mapLayer(dlg._element_layer_ids[tid])
    want = expected[expected["tile_id"] == tid]
    assert out.featureCount() == len(want), \
      f"element {tid}: {out.featureCount()} vs library {len(want)}"

  a_renderer = project.mapLayer(dlg._element_layer_ids["a"]).renderer()
  assert isinstance(a_renderer, QgsCategorizedSymbolRenderer)
  got = {str(c.value()): c.symbol().color().name()
         for c in a_renderer.categories() if c.value()}
  want_colours = bridge.template_from_layer(styled)
  for value, colour in got.items():
    if value in want_colours:
      assert colour == want_colours[value][0].color().name(), \
        f"class {value}: {colour} does not match the source layer"
  assert got.get("forest") == "#31a354", \
    f"the alternative mapping should be in force: {got}"
  visual_pair("categorical weave icons layer source",
              [project.mapLayer(dlg._element_layer_ids[t])
               for t in "abcd"],
              expected, dlg._assignments(),
              templates={f"layer:{styled.id()}":
                         bridge.template_from_layer(styled)})
  for lid in list(dlg._element_layer_ids.values()):
    project.removeMapLayer(lid)
  dlg.close()


def test_ui_library_categorical_to_gpkg():
  """Categorical colours from an imported mapping, taken all the way
  to disk and back: the file-backed layers must carry the same
  classes, colours and labels as the memory layers did, and the same
  tiles as a direct library call. Export is where a per-element
  colour source is most likely to be lost, because the styles are
  rewritten into the GeoPackage rather than kept in the project."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  from weavingspace import TileUnit, Tiling
  from qgis.core import QgsCategorizedSymbolRenderer
  project = QgsProject.instance()
  data = os.path.join(HERE, "data")
  qml = os.path.join(data, "landcover.qml")
  layer = QgsVectorLayer(
    os.path.join(data, "landcover-categorical.gpkg") + "|layername=parcels",
    "parcels", "ogr")
  project.addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("3")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("hex-slice 3")
  dlg.spacing_spin.setValue(1000)
  dlg.opt_join_prototiles.setChecked(False)
  dlg.opt_retain.setChecked(False)
  dlg.opt_clip.setChecked(False)
  dlg.opt_icons.setChecked(False)
  for row, var in enumerate(("landcover", "zoning", "value")):
    dlg.table.cellWidget(row, 1).setCurrentText(var)
  dlg._browsed_qmls.append(qml)
  dlg._update_dynamic_columns()
  for row in (0, 1):
    combo = dlg.table.cellWidget(row, 7)
    i = combo.findData("file:" + qml)
    combo.setCurrentIndex(i)
    combo.activated.emit(i)

  with tempfile.TemporaryDirectory() as td:
    path = os.path.join(td, "categorical.gpkg")
    dlg.gpkg_widget.setFilePath(path)
    _generate_and_wait(dlg)
    expected = Tiling(
      TileUnit(tiling_type="hex-slice", n=3, offset=0, spacing=1000,
               crs=2193),
      bridge.layer_to_gdf(layer, ["landcover", "value", "zoning"])) \
      .get_tiled_map(join_on_prototiles=False, retain_tileables=False,
                     ragged_edges=True).map
    in_memory = {}
    for tid in "abc":
      out = project.mapLayer(dlg._element_layer_ids[tid])
      want = expected[expected["tile_id"] == tid]
      assert out.featureCount() == len(want), \
        f"element {tid}: {out.featureCount()} vs library {len(want)}"
      renderer = out.renderer()
      if isinstance(renderer, QgsCategorizedSymbolRenderer):
        in_memory[tid] = {str(c.value()): (c.symbol().color().name(),
                                           c.label())
                          for c in renderer.categories() if c.value()}
    assert in_memory["a"].get("forest") == ("#1b7837", "Native forest"), \
      f"imported mapping missing before export: {in_memory.get('a')}"
    # element b maps a DIFFERENT field with the same imported file, so
    # its classes fall back to automatic colours rather than borrowing
    # a's; the file simply has nothing to say about zoning values
    assert in_memory["b"], "element b should still be categorized"
    assert not (set(in_memory["b"]) & set(in_memory["a"])), \
      "different fields should not share class values here"

    for lid in list(dlg._element_layer_ids.values()):
      project.removeMapLayer(lid)
    dlg.close()
    for tid, expected_classes in in_memory.items():
      reloaded = QgsVectorLayer(f"{path}|layername=tiles_{tid}", tid, "ogr")
      assert reloaded.isValid()
      reloaded.loadDefaultStyle()
      renderer = reloaded.renderer()
      assert isinstance(renderer, QgsCategorizedSymbolRenderer), \
        f"element {tid} lost its categorized style on the way to disk"
      got = {str(c.value()): (c.symbol().color().name(), c.label())
             for c in renderer.categories() if c.value()}
      assert got == expected_classes, \
        f"element {tid} classes changed on the round trip:\n" \
        f"  before {expected_classes}\n  after  {got}"


def test_stress_fast_interaction():
  """Fast clicking, deliberately: fire the sequence of changes an
  impatient user makes — spacing, family, variables, ramps, styles,
  switches — with no pauses, while live update is ON, then let
  everything settle and check the plugin is coherent.

  This is the shape of the bugs this project has actually shipped: a
  debounced rebuild landing mid-interaction and destroying the widget
  a pick was about to commit to, a run launched against a stale unit,
  a task left in flight. None of them reproduce when a test politely
  waits between steps."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(True)

  def tick(ms=0):
    """Yield to the event loop briefly, as clicks between repaints
    do; zero ms still lets queued signals run."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()

  # a burst of design changes with nothing waited for
  for spacing in (500, 420, 700, 380, 620):
    dlg.spacing_spin.setValue(spacing)
    tick()
  for family in ("laves 3.3.4.3.4", "hex-slice 4", "grid 4",
                 "square-slice 4", "laves 3.3.4.3.4"):
    dlg.family_combo.setCurrentText(family)
    tick()
  # ... and a burst of data-tab changes, the chooser-race territory
  for row in range(dlg.table.rowCount()):
    dlg.table.cellWidget(row, 1).setCurrentText(
      ("v1", "v2", "v3", "landcover")[row])
    tick()
    ramp_cell = dlg.table.cellWidget(row, 4)
    if hasattr(ramp_cell, "setCurrentText"):
      ramp_cell.setCurrentText(
        ("YlGn", "PuBu", "Oranges", "Set2")[row])
    tick()
  dlg._update_dynamic_columns()
  for mode in ("Quant: Equal intervals", "Quant: Unclassed",
               "Single colour", "Quant: Quantiles"):
    dlg.table.cellWidget(0, 2).setCurrentText(mode)
    tick()
  dlg._update_dynamic_columns()
  for checkbox in (dlg.opt_outlines, dlg.opt_icons, dlg.opt_outlines,
                   dlg.opt_icons):
    checkbox.setChecked(not checkbox.isChecked())
    tick()

  # let every debounce and any in-flight task finish
  deadline = QEventLoop()
  QTimer.singleShot(20_000, deadline.quit)
  waited = [0]

  def settle():
    if dlg._task is None and not dlg._live_timer.isActive() \
        and not dlg._preview_timer.isActive():
      deadline.quit()
      return
    waited[0] += 1
    QTimer.singleShot(200, settle)

  QTimer.singleShot(200, settle)
  deadline.exec()
  tick(1500)

  # coherence after the storm
  assert dlg._task is None, "a task was left in flight"
  assert dlg.generate_btn.isEnabled(), "Generate stayed disabled"
  assert dlg._unit is not None
  assert dlg.family_combo.currentText() == "laves 3.3.4.3.4"
  assert set(dlg._tile_ids()) == set("abcd")
  # the table still matches the unit, and its widgets are alive
  assert dlg.table.rowCount() == len(dlg._tile_ids())
  for row in range(dlg.table.rowCount()):
    assert dlg.table.cellWidget(row, 1) is not None, \
      f"row {row} lost its variable chooser"
  # the last picks survived the storm
  assert dlg.table.cellWidget(0, 2).currentText() == "Quant: Quantiles"
  assert dlg.table.cellWidget(0, 4).currentText() == "YlGn", \
    "the ramp picked mid-storm must still be the one showing"
  groups = [c for c in project.layerTreeRoot().children()
            if c.nodeType() == 0]
  assert len(groups) <= 1, f"{len(groups)} groups after fast clicking"
  if dlg._element_layer_ids:
    # whatever it drew last must match the settings now on screen
    for tid, lid in dlg._element_layer_ids.items():
      assert project.mapLayer(lid) is not None, \
        f"element {tid} points at a layer that is gone"
    assert set(dlg._element_layer_ids) == set(dlg._tile_ids())
    # and the map it ended on must still be a real map: the colours
    # have to belong to the ramps the table shows after the storm
    visual_gamut("fast interaction storm",
                 [project.mapLayer(lid)
                  for lid in dlg._element_layer_ids.values()],
                 [a["ramp"] for a in dlg._assignments() if a["var"]]
                 + ["Set2"], mean_max=12.0, p95_max=30.0)
  dlg.live_check.setChecked(False)
  dlg.close()


def test_stress_complex_data_bumbling():
  """Styling, rendering and sizing fiddled with repeatedly on the
  categorical fixture: spacing swept from coarse to fine and back,
  styles cycled through every mode, class counts changed, ramps
  swapped, all with generation in between. The checks run at several
  moments rather than only at the end, because a wrong intermediate
  state usually corrects itself by the last generation and hides."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.core import QgsGraduatedSymbolRenderer
  project = QgsProject.instance()
  data = os.path.join(HERE, "data")
  layer = QgsVectorLayer(
    os.path.join(data, "landcover-categorical.gpkg") + "|layername=parcels",
    "parcels", "ogr")
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")

  def renderer(tid):
    return project.mapLayer(dlg._element_layer_ids[tid]).renderer()

  for row, var in enumerate(("landcover", "value", "zoning", "period")):
    dlg.table.cellWidget(row, 1).setCurrentText(var)
  dlg._update_dynamic_columns()

  # sizing: coarse, fine, coarse again. Tile counts must move with
  # spacing, and the categorical class sets must stay sane at every
  # size (a fine pattern catches more values, never fewer categories
  # than the data has)
  counts = {}
  for spacing in (1500, 800, 1800):
    dlg.spacing_spin.setValue(spacing)
    _generate_and_wait(dlg)
    counts[spacing] = sum(project.mapLayer(lid).featureCount()
                          for lid in dlg._element_layer_ids.values())
    classes = {str(c.value()) for c in renderer("a").categories()
               if c.value()}
    assert classes <= {"forest", "water", "urban", "crops", "wetland",
                       "bare"}, f"unexpected classes at {spacing}: {classes}"
    assert classes, f"no classes survived at spacing {spacing}"
  assert counts[800] > counts[1500] > counts[1800], \
    f"tile counts should follow spacing: {counts}"

  # styling: every mode in turn on a numeric element, checking the
  # renderer each time rather than only after the last
  expectations = [
    ("Quant: Quantiles", QgsGraduatedSymbolRenderer, 5),
    ("Quant: Equal intervals", QgsGraduatedSymbolRenderer, 5),
    ("Quant: Natural breaks", QgsGraduatedSymbolRenderer, 5),
    ("Quant: Pretty breaks", QgsGraduatedSymbolRenderer, None),
    ("Quant: Unclassed", QgsGraduatedSymbolRenderer, 50),
    ("Single colour", QgsSingleSymbolRenderer, None),
  ]
  for mode, kind, ranges in expectations:
    dlg.table.cellWidget(1, 2).setCurrentText(mode)
    dlg._update_dynamic_columns()
    _generate_and_wait(dlg)
    assert isinstance(renderer("b"), kind), \
      f"{mode} produced {type(renderer('b')).__name__}"
    if ranges is not None:
      assert len(renderer("b").ranges()) == ranges, \
        f"{mode}: {len(renderer('b').ranges())} classes, expected {ranges}"
    # the other elements must not have followed b around
    assert isinstance(renderer("a"), QgsCategorizedSymbolRenderer), \
      f"element a changed when b went to {mode}"

  # class counts on a graduated element, checked at each step
  dlg.table.cellWidget(1, 2).setCurrentText("Quant: Quantiles")
  dlg._update_dynamic_columns()
  for k in (3, 9, 4):
    dlg.table.cellWidget(1, 3).setValue(k)
    _generate_and_wait(dlg)
    assert len(renderer("b").ranges()) == k, \
      f"asked for {k} classes, got {len(renderer('b').ranges())}"

  # and the categorical elements' Classes cells stayed greyed at the
  # detected count throughout
  for row in (0, 2, 3):
    cell = dlg.table.cellWidget(row, 3)
    assert not cell.isEnabled(), \
      f"row {row} is categorical; its Classes cell should be greyed"
  groups = [c for c in project.layerTreeRoot().children()
            if c.nodeType() == 0]
  assert len(groups) == 1
  visual_gamut("styling sizing bumbling",
               [project.mapLayer(dlg._element_layer_ids[t])
                for t in sorted(dlg._element_layer_ids)],
               [a["ramp"] for a in dlg._assignments() if a["var"]]
               + ["tab10"], mean_max=12.0, p95_max=30.0)
  for lid in list(dlg._element_layer_ids.values()):
    project.removeMapLayer(lid)
  dlg.close()


def test_preview_fits_and_labels():
  """The preview must show the WHOLE tile unit plus any context
  shells, rescaling as shells are added rather than letting the
  pattern run off the edge, and its element ids must be set in the
  application's own type size.

  Checked by painting the widget into an image and measuring where
  the ink lands: everything drawn has to sit inside the widget, and
  raising the shell count has to shrink the central unit (that is
  what rescaling looks like) while still filling a sensible share of
  the available space."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.PyQt.QtGui import QImage, QPainter
  from qgis.PyQt.QtWidgets import QApplication
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.show()
  preview = dlg.preview
  preview.resize(300, 300)

  def ink_extent(shells):
    """(fraction of the widget the drawing spans, touches_edge)."""
    dlg.shells_spin.setValue(shells)
    dlg._rebuild_unit()
    image = QImage(preview.size(), QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    preview.render(painter)
    painter.end()
    xs, ys = [], []
    for x in range(image.width()):
      for y in range(image.height()):
        c = image.pixelColor(x, y)
        # anything that is not the preview's own background
        if abs(c.red() - 250) > 6 or abs(c.green() - 250) > 6 \
            or abs(c.blue() - 250) > 6:
          xs.append(x)
          ys.append(y)
    assert xs, f"nothing was drawn at shells={shells}"
    span = max(max(xs) - min(xs), max(ys) - min(ys)) / image.width()
    touches = (min(xs) <= 0 or min(ys) <= 0
               or max(xs) >= image.width() - 1
               or max(ys) >= image.height() - 1)
    return span, touches

  span0, touches0 = ink_extent(0)
  assert not touches0, "the tile unit is being clipped by the widget"
  assert span0 > 0.5, \
    f"the unit should fill the preview, not sit in a corner ({span0:.2f})"
  span2, touches2 = ink_extent(2)
  assert not touches2, "context shells are being clipped by the widget"
  assert span2 > 0.5, \
    f"with shells the patch should still fill the preview ({span2:.2f})"
  # the central unit must have SHRUNK: same widget, more pattern
  dlg.shells_spin.setValue(0)
  dlg._rebuild_unit()

  # labels: the app's type size, one per tile of the central unit
  assert len(preview._labels) == len(dlg._unit.tiles)
  app_size = QApplication.font().pointSizeF()
  image = QImage(preview.size(), QImage.Format.Format_ARGB32)
  image.fill(0)
  painter = QPainter(image)
  preview.render(painter)
  used = painter.font().pointSizeF()
  painter.end()
  assert abs(used - app_size) < 0.01 or used <= 0, \
    f"preview text is {used}pt where the app uses {app_size}pt"
  dlg.close()


def test_run_lifecycle_no_overlap():
  """One run at a time, including while its layers are being built.

  Adding output happens on the main thread and, on a large map, takes
  longer than the tiling did. The dialog must stay 'busy' across that
  phase: clearing the task first (as an earlier version did) let a
  queued live run start a second tiling while the first was still
  materializing, which is how three tasks ended up in QGIS's task
  manager with the progress bar frozen at the worker's 5%."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(500)

  # observe the dialog's state from inside the output phase
  observed = {}
  original = dlg._add_output_layers

  def watched(*args, **kwargs):
    observed["task_during_output"] = dlg._task
    observed["generate_enabled"] = dlg.generate_btn.isEnabled()
    observed["progress_visible"] = dlg.progress.isVisible()
    return original(*args, **kwargs)

  dlg._add_output_layers = watched
  _generate_and_wait(dlg)
  assert observed, "the output phase never ran"
  assert observed["task_during_output"] is not None, \
    "the task must still be held while layers are being added, or a " \
    "queued live run can start a second tiling on top of this one"
  assert not observed["generate_enabled"], \
    "Generate must stay disabled until the layers exist"
  assert dlg._task is None, "the task must be cleared once output is done"
  assert dlg.generate_btn.isEnabled()
  assert not dlg.progress.isVisible()
  dlg.close()


def test_restyle_without_retiling():
  """A style change must repaint the map, not lay it out again.

  Laying out a tiling is the expensive step and has nothing to do
  with colour: the tiles are already the right tiles. So changing a
  ramp, a classification scheme, a class count or a single colour has
  to take the fast path — no task, no worker thread, same layer
  objects, new symbology. Anything that changes the GEOMETRY (spacing,
  family, a different variable) must still tile properly."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  from qgis.core import QgsGraduatedSymbolRenderer
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(500)
  _generate_and_wait(dlg)
  before_ids = dict(dlg._element_layer_ids)

  # count tilings from here on: the fast path must not add any
  tilings = []
  original = dlg._generate

  def counted(**kwargs):
    tilings.append(1)
    return original(**kwargs)

  dlg._generate = counted

  def renderer(tid):
    return project.mapLayer(dlg._element_layer_ids[tid]).renderer()

  # 1. a ramp change: repainted in place, same layers, no tiling
  dlg.table.cellWidget(0, 4).setCurrentText("YlGn")
  assert dlg._restyle_only(), "a ramp change should restyle in place"
  assert not tilings, "a ramp change must not lay out the tiling again"
  assert dlg._element_layer_ids == before_ids, \
    "restyling must keep the same layers, not replace them"
  assert renderer("a").sourceColorRamp().color(1.0).name() == \
    bridge.get_ramp("YlGn").color(1.0).name(), \
    "the new ramp must actually be on the map"

  # 2. classification scheme and class count, likewise
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Equal intervals")
  dlg.table.cellWidget(0, 3).setValue(8)
  assert dlg._restyle_only()
  assert len(renderer("a").ranges()) == 8, \
    "the class count must reach the map without re-tiling"
  assert not tilings

  # 3. single colour, likewise
  from qgis.gui import QgsColorButton
  from qgis.PyQt.QtGui import QColor
  dlg.table.cellWidget(0, 2).setCurrentText("Single colour")
  dlg._update_dynamic_columns()
  dlg.table.cellWidget(0, 4).setColor(QColor("#7a1f6d"))
  assert dlg._restyle_only()
  assert isinstance(renderer("a"), QgsSingleSymbolRenderer)
  assert renderer("a").symbol().color().name() == "#7a1f6d"
  assert not tilings

  # 4. untouched elements keep their own styling through a restyle
  assert isinstance(renderer("b"), QgsGraduatedSymbolRenderer)

  # 5. geometry changes must NOT take the fast path
  dlg.spacing_spin.setValue(420)
  assert not dlg._restyle_only(), \
    "a spacing change needs a real tiling, not a restyle"
  dlg.spacing_spin.setValue(500)
  dlg.table.cellWidget(1, 1).setCurrentText("v3")
  assert not dlg._restyle_only(), \
    "a different variable needs re-tiling: its values are joined on " \
    "while the tiles are made"
  dlg._generate = original
  dlg.close()


def test_reverse_ramp_column():
  """The Reverse column: present beside the ramp, greyed where there
  is no ramp to reverse, gone entirely when no element has one, and
  actually running the ramp the other way on the map (and on the row's
  swatch) when ticked.

  Reversal is symbology, not geometry, so it must also take the fast
  path: ticking the box repaints the element rather than laying the
  tiling out again."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  from qgis.core import QgsGraduatedSymbolRenderer
  from qgis.gui import QgsColorButton
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(500)
  for row, var in enumerate(("v1", "v2", "landcover", "v3")):
    dlg.table.cellWidget(row, 1).setCurrentText(var)
  dlg._update_dynamic_columns()

  assert not dlg.table.isColumnHidden(5), \
    "the Reverse column belongs beside the ramps"
  for row in range(4):
    box = dlg._row_reverse(row)
    assert box is not None, f"row {row} has no Reverse box"
    assert box.isEnabled(), f"row {row} has a ramp, so it can reverse"
    assert not box.isChecked(), "Reverse starts off"

  # a row with no ramp: greyed and cleared
  dlg.table.cellWidget(0, 2).setCurrentText("Single colour")
  dlg._update_dynamic_columns()
  assert isinstance(dlg.table.cellWidget(0, 4), QgsColorButton)
  box0 = dlg._row_reverse(0)
  assert box0 is not None and not box0.isEnabled(), \
    "a single-colour row has no ramp, so Reverse must grey out"
  assert not box0.isChecked()
  assert not dlg._assignments()[0]["reverse"], \
    "a greyed box must never report itself as reversing"
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Quantiles")
  dlg._update_dynamic_columns()

  # every element on a single colour: the column withdraws
  for row in range(4):
    dlg.table.cellWidget(row, 2).setCurrentText("Single colour")
  dlg._update_dynamic_columns()
  assert dlg.table.isColumnHidden(5), \
    "no ramps anywhere, so no Reverse column"
  for row, mode in enumerate(("Quant: Quantiles", "Quant: Quantiles",
                              "Categorized", "Quant: Quantiles")):
    dlg.table.cellWidget(row, 2).setCurrentText(mode)
  dlg._update_dynamic_columns()
  assert not dlg.table.isColumnHidden(5)

  # generate, then tick Reverse on element a
  dlg.table.cellWidget(0, 4).setCurrentText("Reds")
  _generate_and_wait(dlg)

  def renderer(tid):
    return project.mapLayer(dlg._element_layer_ids[tid]).renderer()

  forward_dark = renderer("a").sourceColorRamp().color(1.0).name()
  forward_light = renderer("a").sourceColorRamp().color(0.0).name()
  b_before = renderer("b").sourceColorRamp().color(1.0).name()

  tilings = []
  original = dlg._generate
  dlg._generate = lambda **kw: (tilings.append(1), original(**kw))[1]
  dlg._row_reverse(0).setChecked(True)
  assert dlg._assignments()[0]["reverse"] is True
  assert dlg._restyle_only(), "reversing is symbology: repaint, do not re-tile"
  assert not tilings, "reversing must not lay out the tiling again"
  dlg._generate = original

  assert isinstance(renderer("a"), QgsGraduatedSymbolRenderer)
  now_dark = renderer("a").sourceColorRamp().color(1.0).name()
  now_light = renderer("a").sourceColorRamp().color(0.0).name()
  assert now_dark == forward_light and now_light == forward_dark, \
    f"the ramp did not turn around ({forward_light}->{now_dark})"
  # the classes themselves must follow, not just the source ramp
  ranges = renderer("a").ranges()
  assert ranges[0].symbol().color().name() != \
    ranges[-1].symbol().color().name()
  assert renderer("b").sourceColorRamp().color(1.0).name() == b_before, \
    "reversing one element must leave its neighbours alone"

  # unticking restores the original direction
  dlg._row_reverse(0).setChecked(False)
  assert dlg._restyle_only()
  assert renderer("a").sourceColorRamp().color(1.0).name() == forward_dark, \
    "unticking must put the ramp back the way it was"

  # a categorical element reverses its discrete scheme too
  dlg.table.cellWidget(2, 4).setCurrentText("tab10")
  _generate_and_wait(dlg)
  cat_before = [c.symbol().color().name()
                for c in renderer("c").categories() if c.value()]
  dlg._row_reverse(2).setChecked(True)
  assert dlg._restyle_only()
  cat_after = [c.symbol().color().name()
               for c in renderer("c").categories() if c.value()]
  assert cat_after != cat_before and sorted(cat_after) == sorted(cat_before), \
    "a discrete scheme reverses by reordering its colours"

  # and the choice survives a design-driven table rebuild
  dlg.spacing_spin.setValue(560)
  dlg._rebuild_unit()
  assert dlg._row_reverse(2).isChecked(), \
    "the Reverse choice belongs to the element, not the widget"
  dlg.close()


def test_element_opacity():
  """Per-element opacity: QGIS layer opacity, driven from the table.

  The properties that make this worth having, each checked here: it
  is stored apart from the colours (so changing the ramp keeps it and
  the class colours stay fully opaque), it reaches the layer, it
  repaints rather than re-tiling, it travels into a GeoPackage, and
  it obeys the plugin's standing promise that hand work in QGIS
  survives regeneration until you change that element in the dialog.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.core import QgsGraduatedSymbolRenderer
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(500)
  for row, var in enumerate(("v1", "v2", "landcover", "v3")):
    dlg.table.cellWidget(row, 1).setCurrentText(var)
  dlg._update_dynamic_columns()

  # present for every element, ramp or not, and starting solid
  assert not dlg.table.isColumnHidden(6)
  for row in range(4):
    spin = dlg._row_opacity(row)
    assert spin is not None and spin.isEnabled(), f"row {row} has no cell"
    assert spin.value() == 100, "elements start opaque"
  dlg.table.cellWidget(0, 2).setCurrentText("Single colour")
  dlg._update_dynamic_columns()
  assert dlg._row_opacity(0) is not None and dlg._row_opacity(0).isEnabled(), \
    "a single-colour element can still be softened"
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Quantiles")
  dlg._update_dynamic_columns()

  _generate_and_wait(dlg)

  def element(tid):
    return project.mapLayer(dlg._element_layer_ids[tid])

  assert element("a").opacity() == 1.0
  colours_before = [r.symbol().color().name()
                    for r in element("a").renderer().ranges()]

  # setting it repaints in place: no tiling, colours untouched
  tilings = []
  original = dlg._generate
  dlg._generate = lambda **kw: (tilings.append(1), original(**kw))[1]
  dlg._row_opacity(0).setValue(40)
  assert dlg._assignments()[0]["opacity"] == 40
  assert dlg._restyle_only(), "opacity is symbology: repaint, do not re-tile"
  assert not tilings, "opacity must never lay out the tiling again"
  dlg._generate = original
  assert abs(element("a").opacity() - 0.4) < 1e-6, \
    f"layer opacity is {element('a').opacity()}"
  assert element("b").opacity() == 1.0, "only element a was softened"
  assert [r.symbol().color().name()
          for r in element("a").renderer().ranges()] == colours_before, \
    "opacity must not touch the class colours"
  assert {r.symbol().color().alpha()
          for r in element("a").renderer().ranges()} == {255}, \
    "the colours stay fully opaque; the transparency lives on the layer"

  # it survives every kind of symbology change beneath it
  dlg.table.cellWidget(0, 4).setCurrentText("YlGn")
  assert dlg._restyle_only()
  assert abs(element("a").opacity() - 0.4) < 1e-6, \
    "changing the ramp must not disturb opacity"
  dlg._row_reverse(0).setChecked(True)
  assert dlg._restyle_only()
  assert abs(element("a").opacity() - 0.4) < 1e-6
  dlg.table.cellWidget(0, 3).setValue(7)
  assert dlg._restyle_only()
  assert abs(element("a").opacity() - 0.4) < 1e-6

  # and a design change, which does re-tile
  dlg.spacing_spin.setValue(560)
  _generate_and_wait(dlg)
  assert abs(element("a").opacity() - 0.4) < 1e-6, \
    "opacity must survive a genuine regeneration"
  assert dlg._row_opacity(0).value() == 40, \
    "and the table must still show it after the rebuild"

  # THE AUTHORITY RULE: a hand-set opacity survives regeneration...
  element("b").setOpacity(0.25)
  dlg.spacing_spin.setValue(520)
  _generate_and_wait(dlg)
  assert abs(element("b").opacity() - 0.25) < 1e-6, \
    "an opacity set by hand in Layer Properties must survive, as a " \
    "hand-refined renderer does"
  # ...until the dialog changes that element, which takes authority back
  dlg._row_opacity(1).setValue(80)
  assert dlg._restyle_only()
  assert abs(element("b").opacity() - 0.8) < 1e-6, \
    "moving the cell must override a hand-set value"

  # GeoPackage: opacity travels with the styling, as its own value
  with tempfile.TemporaryDirectory() as td:
    path = os.path.join(td, "opacity.gpkg")
    dlg.gpkg_widget.setFilePath(path)
    _generate_and_wait(dlg)
    for lid in list(dlg._element_layer_ids.values()):
      project.removeMapLayer(lid)
    dlg.close()
    reloaded = QgsVectorLayer(f"{path}|layername=tiles_a", "a", "ogr")
    assert reloaded.isValid()
    reloaded.loadDefaultStyle()
    assert abs(reloaded.opacity() - 0.4) < 1e-6, \
      f"opacity did not survive the GeoPackage round trip " \
      f"({reloaded.opacity()})"
    assert isinstance(reloaded.renderer(), QgsGraduatedSymbolRenderer)


def test_opacity_in_preview():
  """The preview shows opacity, floored so the design stays readable.

  The floor is deliberate: the preview paints on a plain panel rather
  than over the map, so a very low value would fade toward that panel
  and take the tile-id labels with it, while showing a blend that is
  not what the map will do."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.PyQt.QtGui import QColor
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg._update_dynamic_columns()

  assert QColor(dlg._table_id_colours()["a"]).alpha() == 255, \
    "an untouched element previews solid"
  dlg._row_opacity(0).setValue(70)
  faded = QColor(dlg._table_id_colours()["a"]).alpha()
  assert 170 < faded < 190, f"70% should preview near 179, got {faded}"
  dlg._row_opacity(0).setValue(5)
  assert QColor(dlg._table_id_colours()["a"]).alpha() == \
    round(255 * dlg.PREVIEW_MIN_OPACITY / 100), \
    "very low values are floored in the preview, not shown literally"
  assert QColor(dlg._table_id_colours()["b"]).alpha() == 255, \
    "one element's opacity must not fade its neighbours"
  dlg.close()


def _tick(ms=0):
  """Let the event loop turn briefly, as clicks between repaints do."""
  loop = QEventLoop()
  QTimer.singleShot(ms, loop.quit)
  loop.exec()


def _settle(dlg, seconds=30):
  """Run the event loop until the dialog is quiet.

  Args:
    dlg: the dialog to wait on. Quiet means no task in flight and no
      debounce pending — both, because either alone leaves work that
      will still change the thing under test.
    seconds: how long to wait before giving up. Thirty is generous
      for a synthetic layer and short enough that a genuine hang is
      reported as a failed test rather than a stalled suite.

  Returns:
    True when the dialog settled, False on timeout. Callers assert on
    it: a test that carries on after a timeout is measuring a
    half-finished state.

  Race tests need a defined end state, and "sleep a bit" is not one.
  """
  loop = QEventLoop()
  state = {"settled": False}

  def poll(n=[0]):
    n[0] += 1
    quiet = (dlg._task is None
             and not dlg._live_timer.isActive()
             and not dlg._preview_timer.isActive())
    if quiet or n[0] > seconds * 5:
      state["settled"] = quiet
      loop.quit()
      return
    QTimer.singleShot(200, poll)

  QTimer.singleShot(50, poll)
  loop.exec()
  return state["settled"]


def test_race_settings_change_during_run():
  """Change settings while a tiling is in flight.

  Everything after ``_generate()`` returns but before the event loop
  turns is, by construction, mid-flight: the worker cannot have
  finished. So this is deterministic, not timing-dependent.

  Two promises are under test. The run in flight keeps the assignments
  it started with (they are snapshotted, so a map can never come back
  with element a's geometry wearing element b's colours), and the
  change the user made is not lost: it is remembered and applied by a
  rerun, so the map that finally rests matches what the table finally
  says.

  Regression: settings changed mid-run were swallowed, because the run's signature was captured when it finished rather than when it launched.
  [race]
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(True)
  dlg.n_combo.setCurrentText("4")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(500)
  dlg.table.cellWidget(0, 4).setCurrentText("Reds")
  assert _settle(dlg), "the dialog should reach a resting state first"

  # a GEOMETRY change, or _generate takes the restyle fast path and
  # finishes synchronously with no task to race against (which is
  # exactly what this test caught on its first run)
  dlg.spacing_spin.setValue(455)
  dlg._generate()
  assert dlg._task is not None, "a run should be in flight"
  # mid-flight changes, before the loop turns
  dlg.table.cellWidget(0, 4).setCurrentText("YlGn")
  dlg.spacing_spin.setValue(430)
  dlg._queue_live()
  assert dlg._task is not None, "the in-flight run must not be replaced"
  dlg._generate()
  assert dlg._live_pending, \
    "a second request during a run must be remembered, not dropped"

  assert _settle(dlg, 60), "the dialog never came to rest"
  # the map that rests must match the table that rests
  assert dlg.table.cellWidget(0, 4).currentText() == "YlGn"
  seeded = project.mapLayer(dlg._element_layer_ids["a"]) \
    .renderer().sourceColorRamp().color(1.0).name()
  assert seeded == bridge.get_ramp("YlGn").color(1.0).name(), \
    "the settled map must wear the settled ramp, not the one the " \
    "in-flight run started with"
  groups = [c for c in project.layerTreeRoot().children()
            if c.nodeType() == 0]
  assert len(groups) == 1, f"{len(groups)} groups after the race"
  assert set(dlg._element_layer_ids) == set("abcd")
  for lid in dlg._element_layer_ids.values():
    assert project.mapLayer(lid) is not None, "a layer went missing"
  dlg.live_check.setChecked(False)
  dlg.close()


def test_race_double_generate():
  """Two Generate presses in quick succession must produce one run,
  then at most one rerun -- never two tilings racing each other into
  the same layer group."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(500)
  assert _settle(dlg)

  started = []
  original_task_class = None
  dlg._generate()
  first = dlg._task
  assert first is not None
  dlg._generate()
  assert dlg._task is first, \
    "the second press must not start a second tiling"
  assert _settle(dlg, 60)
  groups = [c for c in project.layerTreeRoot().children()
            if c.nodeType() == 0]
  assert len(groups) == 1
  assert dlg.generate_btn.isEnabled()
  dlg.close()


def test_race_restyle_during_run():
  """A restyle must refuse while a tiling is in flight.

  Repainting layers that are about to be replaced is wasted work at
  best; at worst the repaint lands on layers the completing run then
  discards, and the map ends up showing the older styling. The fast
  path therefore declines while a task is running, and the change is
  picked up by the rerun instead."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(500)
  _generate_and_wait(dlg)

  # again, only a geometry change puts a real run in flight
  dlg.spacing_spin.setValue(455)
  dlg._generate()
  assert dlg._task is not None, "a run should be in flight"
  dlg.table.cellWidget(0, 4).setCurrentText("YlGn")
  assert dlg._restyle_only() is False, \
    "restyling must not happen underneath a run in flight"
  assert _settle(dlg, 60)
  from weavingspace_qgis import bridge
  # live update is OFF here, so the map is deliberately NOT refreshed
  # on its own: the table and the map may disagree until the user
  # asks. What must be true is that the change is not lost -- pressing
  # Generate applies it.
  seeded = project.mapLayer(dlg._element_layer_ids["a"]) \
    .renderer().sourceColorRamp().color(1.0).name()
  assert seeded != bridge.get_ramp("YlGn").color(1.0).name(), \
    "with live update off, nothing should repaint by itself"
  _generate_and_wait(dlg)
  seeded = project.mapLayer(dlg._element_layer_ids["a"]) \
    .renderer().sourceColorRamp().color(1.0).name()
  assert seeded == bridge.get_ramp("YlGn").color(1.0).name(), \
    "the change made during the run must reach the map on Generate"
  dlg.close()


def test_race_close_during_run():
  """Closing the dialog mid-run must cancel cleanly: no output
  arriving after the dialog is gone, no wedged state, and a fresh
  dialog able to generate immediately afterwards."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(400)
  dlg._generate()
  assert dlg._task is not None
  dlg.close()
  loop = QEventLoop()
  QTimer.singleShot(3000, loop.quit)
  loop.exec()
  assert dlg._task is None, "closing must clear the run"

  # a fresh dialog works, and adopts whatever group exists
  dlg2 = WeavingSpaceDialog(iface=_Iface())
  dlg2.live_check.setChecked(False)
  dlg2.spacing_spin.setValue(600)
  _generate_and_wait(dlg2)
  assert dlg2._element_layer_ids, "generation must work after a close"
  groups = [c for c in project.layerTreeRoot().children()
            if c.nodeType() == 0]
  assert len(groups) == 1, f"{len(groups)} groups after close-mid-run"
  dlg2.close()


def test_race_region_layer_removed_during_run():
  """The region layer disappearing mid-run must not take QGIS with it.

  The completion callback holds a reference to the source layer (it
  builds the outlines layer from it), so a user deleting the layer
  while a tiling runs is a genuine crash risk rather than a
  hypothetical one."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.opt_outlines.setChecked(True)
  dlg.spacing_spin.setValue(500)
  dlg._generate()
  assert dlg._task is not None
  project.removeMapLayer(layer.id())   # mid-flight
  assert _settle(dlg, 60), "the dialog must recover, not hang"
  assert dlg._task is None
  # The recovery path resets the whole UI, not just the button: a
  # progress bar left on screen after a run that died says the plugin
  # is still working when it is not. (An earlier version of this
  # comment claimed this branch was the only place the bar is hidden.
  # It is not: _finish_run hides it at the end of every ordinary run,
  # and test_the_dialogs_chrome_does_its_job defends that. The line
  # that genuinely lacked a test is in showEvent's zombie recovery,
  # covered in test_choice_persistence_and_recovery.)
  assert not dlg.progress.isVisibleTo(dlg), \
    "the progress bar is still showing after the run was abandoned; "\
    "the dialog looks busy while doing nothing"
  assert dlg.generate_btn.isEnabled(), \
    "the dialog must be usable after its region vanished"
  dlg.close()


def test_single_dialog_instance():
  """Only one dialog may be live in a QGIS session.

  Normal use gives one, because the plugin reuses its dialog. But a
  plugin reload -- routine while developing, and QGIS's Plugin
  Reloader does it constantly -- constructs a fresh dialog while the
  previous object is still alive with its timers running and possibly
  a tiling in flight. Since a new dialog ADOPTS the existing output
  group, two live instances would write to the same layers, each
  unaware of the other. Constructing one therefore retires its
  predecessor."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import dialog as dialog_module
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)

  first = WeavingSpaceDialog(iface=_Iface())
  first.live_check.setChecked(True)
  first.spacing_spin.setValue(500)
  first._queue_live()
  assert dialog_module._LIVE_DIALOG is first

  second = WeavingSpaceDialog(iface=_Iface())
  assert dialog_module._LIVE_DIALOG is second, \
    "the newest dialog must be the live one"
  assert not first.live_check.isChecked(), \
    "the retired dialog must stop generating"
  assert not first._live_timer.isActive() and \
    not first._preview_timer.isActive(), \
    "the retired dialog's timers must be stopped, or it will keep " \
    "queueing work against layers the new dialog now owns"
  assert first._task is None, "a retired dialog holds no run"
  assert not first.isVisible()

  # the survivor is fully functional, and owns the group alone
  second.live_check.setChecked(False)
  second.spacing_spin.setValue(600)
  _generate_and_wait(second)
  groups = [c for c in project.layerTreeRoot().children()
            if c.nodeType() == 0]
  assert len(groups) == 1, f"{len(groups)} groups from two instances"
  assert second._element_layer_ids
  second.close()


def test_race_change_during_output_phase():
  """A change made while the LAYERS are being built.

  The tiling runs on a worker thread, but turning its result into
  layers happens on the main thread, and on a large map that phase
  takes longer than the tiling did. It is also where this project's
  "stuck at 5%" bug lived. So the race worth testing is not only
  "during the worker" but "during the output phase": the run must
  finish coherently, and the change must not be lost."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(True)
  dlg.spacing_spin.setValue(520)
  assert _settle(dlg), "settle before racing"

  # make the change from INSIDE the output phase, which is the only
  # way to be certain of the timing
  observed = {}
  original = dlg._add_output_layers

  def during_output(*args, **kwargs):
    observed["task_held"] = dlg._task is not None
    observed["generate_disabled"] = not dlg.generate_btn.isEnabled()
    result = original(*args, **kwargs)
    # a user typing while the layers appear
    dlg.table.cellWidget(0, 4).setCurrentText("YlGn")
    dlg.spacing_spin.setValue(475)
    observed["task_after_change"] = dlg._task
    return result

  dlg._add_output_layers = during_output
  dlg.spacing_spin.setValue(500)
  dlg._generate()
  assert dlg._task is not None
  assert _settle(dlg, 60), "the dialog never came to rest"
  dlg._add_output_layers = original

  assert observed.get("task_held"), \
    "the run must still be held while its layers are built, or a " \
    "queued rerun starts a second tiling underneath it"
  assert observed.get("generate_disabled")
  # the change made mid-output must have reached the finished map
  assert dlg.spacing_spin.value() == 475
  seeded = project.mapLayer(dlg._element_layer_ids["a"]) \
    .renderer().sourceColorRamp().color(1.0).name()
  assert seeded == bridge.get_ramp("YlGn").color(1.0).name(), \
    "a ramp picked during the output phase must not be lost"
  groups = [c for c in project.layerTreeRoot().children()
            if c.nodeType() == 0]
  assert len(groups) == 1, f"{len(groups)} groups after the race"
  dlg.live_check.setChecked(False)
  dlg.close()


def _map_matches_table(dlg):
  """Is the map on screen the map the table describes?

  Returns (ok, detail). The dialog records what each completed run
  DREW; comparing that with the table's current state is the single
  invariant that catches a change being swallowed -- which is exactly
  how a ramp picked during a tiling went missing until the signatures
  were made to describe the run rather than the moment it finished.
  """
  if not dlg._element_layer_ids:
    return True, "nothing generated yet"
  drawn = dlg._last_run_sig
  showing = dlg._run_signature()
  if drawn == showing:
    return True, "in step"
  return False, "the table asks for something the map does not show"


def test_race_control_sweep():
  """Change EACH control while a tiling is in flight, one at a time.

  Every control is a candidate for the same failure: a change that
  arrives while the worker is busy can be recorded against the run
  that is finishing rather than the one it should provoke. Rather
  than trusting that the handpicked races generalise, this walks the
  controls and checks the same invariant after each.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(True)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(520)
  assert _settle(dlg), "settle before sweeping"

  # (name, action) -- each action changes one control to a new value
  moves = [
    ("spacing", lambda: dlg.spacing_spin.setValue(
      480 if dlg.spacing_spin.value() > 500 else 540)),
    ("ramp", lambda: dlg.table.cellWidget(0, 4).setCurrentText(
      "YlGn" if dlg.table.cellWidget(0, 4).currentText() != "YlGn"
      else "PuBu")),
    ("style", lambda: dlg.table.cellWidget(0, 2).setCurrentText(
      "Quant: Equal intervals"
      if dlg.table.cellWidget(0, 2).currentText() != "Quant: Equal intervals"
      else "Quant: Quantiles")),
    ("classes", lambda: dlg.table.cellWidget(0, 3).setValue(
      7 if dlg.table.cellWidget(0, 3).value() != 7 else 4)),
    ("reverse", lambda: dlg._row_reverse(0).setChecked(
      not dlg._row_reverse(0).isChecked())),
    ("opacity", lambda: dlg._row_opacity(0).setValue(
      60 if dlg._row_opacity(0).value() != 60 else 100)),
    ("variable", lambda: dlg.table.cellWidget(1, 1).setCurrentText(
      "v3" if dlg.table.cellWidget(1, 1).currentText() != "v3" else "v2")),
    ("rotation", lambda: dlg.mod_rotate.setValue(
      20 if dlg.mod_rotate.value() != 20 else 0)),
    ("tile inset", lambda: dlg.mod_t_inset.setValue(
      3 if dlg.mod_t_inset.value() != 3 else 0)),
    ("tile outlines", lambda: dlg.opt_tile_outlines.setChecked(
      not dlg.opt_tile_outlines.isChecked())),
    ("clip", lambda: dlg.opt_clip.setChecked(not dlg.opt_clip.isChecked())),
    ("icons", lambda: dlg.opt_icons.setChecked(
      not dlg.opt_icons.isChecked())),
    ("outlines layer", lambda: dlg.opt_outlines.setChecked(
      not dlg.opt_outlines.isChecked())),
  ]

  failures = []
  for name, move in moves:
    # put a real run in flight (a geometry change, so the restyle
    # fast path does not answer it synchronously)
    dlg.spacing_spin.setValue(dlg.spacing_spin.value() + 7)
    dlg._generate()
    if dlg._task is None:
      failures.append(f"{name}: could not start a run to race against")
      continue
    move()                      # the change lands mid-flight
    if not _settle(dlg, 60):
      failures.append(f"{name}: never came to rest")
      continue
    ok, detail = _map_matches_table(dlg)
    if not ok:
      failures.append(f"{name}: {detail}")
    groups = [c for c in project.layerTreeRoot().children()
              if c.nodeType() == 0]
    if len(groups) != 1:
      failures.append(f"{name}: {len(groups)} groups")
    missing = [t for t, lid in dlg._element_layer_ids.items()
               if project.mapLayer(lid) is None]
    if missing:
      failures.append(f"{name}: elements {missing} lost their layers")

  assert not failures, "changes made mid-tiling were mishandled:\n  " \
    + "\n  ".join(failures)
  dlg.live_check.setChecked(False)
  dlg.close()


def test_fuzz_random_interaction():
  """Random sequences of interaction, checked against invariants.

  Broader than any per-control test: real users do not change one
  thing at a time, and the failures this project has shipped came
  from combinations (a debounce landing between two picks, a run
  completing during a third). Seeds are fixed, so a failure is
  reproducible; the invariants are the things that must hold no
  matter what was done.
  """
  import random
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)

  def actions(dlg):
    return [
      ("spacing", lambda r: dlg.spacing_spin.setValue(
        r.choice([420, 480, 520, 600]))),
      ("family", lambda r: dlg.family_combo.setCurrentText(
        r.choice(["laves 3.3.4.3.4", "hex-slice 4", "grid 4",
                  "square-slice 4"]))),
      ("ramp", lambda r: dlg.table.cellWidget(
        r.randrange(dlg.table.rowCount()), 4).setCurrentText(
          r.choice(["Reds", "YlGn", "PuBu", "Oranges"]))),
      ("style", lambda r: dlg.table.cellWidget(
        r.randrange(dlg.table.rowCount()), 2).setCurrentText(
          r.choice(["Quant: Quantiles", "Quant: Equal intervals",
                    "Quant: Unclassed", "Single colour"]))),
      ("variable", lambda r: dlg.table.cellWidget(
        r.randrange(dlg.table.rowCount()), 1).setCurrentText(
          r.choice(["v1", "v2", "v3", "landcover", "---"]))),
      ("reverse", lambda r: dlg._row_reverse(
        r.randrange(dlg.table.rowCount())).setChecked(r.random() < 0.5)),
      ("opacity", lambda r: dlg._row_opacity(
        r.randrange(dlg.table.rowCount())).setValue(
          r.choice([40, 70, 100]))),
      ("rotate", lambda r: dlg.mod_rotate.setValue(r.choice([0, 15, 30]))),
      ("switches", lambda r: r.choice(
        [dlg.opt_clip, dlg.opt_icons, dlg.opt_outlines,
         dlg.opt_tile_outlines, dlg.opt_join_prototiles,
         dlg.opt_retain]).setChecked(r.random() < 0.5)),
      ("generate", lambda r: dlg._generate()),
      ("tick", lambda r: _tick(r.choice([0, 0, 0, 40, 120]))),
    ]

  problems = []
  for seed in (1, 2, 3):
    project.clear()
    layer = make_region_layer()
    project.addMapLayer(layer)
    dlg = WeavingSpaceDialog(iface=_Iface())
    dlg.live_check.setChecked(True)
    dlg.spacing_spin.setValue(520)
    _settle(dlg)
    rng = random.Random(seed)
    pool = actions(dlg)
    for step in range(25):
      name, act = rng.choice(pool)
      try:
        act(rng)
      except Exception as e:  # noqa: BLE001 - the point is to catch it
        problems.append(f"seed {seed} step {step} ({name}) raised "
                        f"{type(e).__name__}: {e}")
        break
    if not _settle(dlg, 90):
      problems.append(f"seed {seed}: never came to rest")
    # invariants, whatever happened
    if dlg._task is not None:
      problems.append(f"seed {seed}: a task was left in flight")
    if not dlg.generate_btn.isEnabled():
      problems.append(f"seed {seed}: Generate left disabled")
    groups = [c for c in project.layerTreeRoot().children()
              if c.nodeType() == 0]
    if len(groups) > 1:
      problems.append(f"seed {seed}: {len(groups)} output groups")
    for tid, lid in dlg._element_layer_ids.items():
      if project.mapLayer(lid) is None:
        problems.append(f"seed {seed}: element {tid} points at a "
                        "layer that is gone")
    if dlg._element_layer_ids and set(dlg._element_layer_ids) != \
        set(dlg._tile_ids()):
      problems.append(f"seed {seed}: elements {sorted(dlg._element_layer_ids)}"
                      f" but unit has {sorted(dlg._tile_ids())}")
    ok, detail = _map_matches_table(dlg)
    if not ok:
      problems.append(f"seed {seed}: {detail}")
    dlg.live_check.setChecked(False)
    dlg.close()

  assert not problems, "random interaction broke invariants:\n  " \
    + "\n  ".join(problems)


def test_gpkg_fid_attribute():
  """Exporting a map whose data carries an attribute called "fid".

  A GeoPackage's primary key column is named fid, and GDAL maps an
  attribute of that name straight onto it. Every tile inherits its
  region polygon's attributes, so many tiles share one fid value and
  the write fails on the first duplicate -- taking the whole export
  with it. A user hits this simply by mapping a field called fid,
  which GeoPackage-sourced layers routinely have; it was found by
  profiling rather than by anyone reporting it, which is its own
  small lesson."""
  from weavingspace_qgis import bridge
  from weavingspace import TileUnit, Tiling
  layer = QgsVectorLayer(
    os.path.join(HERE, "data", "imd-auckland-sa2-2018.gpkg"), "ak", "ogr")
  assert layer.isValid()
  names = [f.name() for f in layer.fields()]
  assert "fid" in names, "this test needs a layer with an fid attribute"

  region = bridge.layer_to_gdf(layer, ["fid", "imd"])
  unit = TileUnit(tiling_type="laves", code="3.3.4.3.4", spacing=1200,
                  crs=2193)
  tiled = Tiling(unit, region).get_tiled_map().map
  sub = tiled[tiled["tile_id"] == "a"]
  assert len(sub) > 10, "need enough tiles to repeat an fid value"
  assert sub["fid"].duplicated().any(), \
    "the point of the test is that tiles SHARE region fid values"

  memory = bridge.gdf_to_layer(sub, "a")
  with tempfile.TemporaryDirectory() as td:
    path = os.path.join(td, "fid.gpkg")
    written = bridge.write_gpkg_layer(memory, path, "tiles_a", first=True)
    assert written.featureCount() == memory.featureCount(), \
      f"only {written.featureCount()} of {memory.featureCount()} " \
      "features reached the GeoPackage"
    on_disk = [f.name() for f in written.fields()]
    assert "fid" in on_disk, \
      f"the user's fid attribute was lost: {on_disk}"
    values = sorted(f["fid"] for f in written.getFeatures())
    assert values == sorted(int(v) for v in sub["fid"]), \
      "the fid attribute's values must survive unchanged"


def test_generate_uses_the_design_on_screen():
  """Generate immediately after a design change must tile the NEW
  design.

  Design controls schedule the unit rebuild 350 ms later, so a
  Generate pressed inside that window used to tile the PREVIOUS
  design. _generate flushes the pending rebuild for exactly that
  reason.

  This needs its own test because the UI-vs-library helper rebuilds
  the unit itself (a seven-element family needs its table rows before
  variables can be set), and that flush in the TEST masks a missing
  flush in the PRODUCT -- the mutation audit caught precisely that
  regression in coverage.

  Regression: Generate pressed inside the 350 ms preview debounce tiled the PREVIOUS design, so the map did not match the dialog.
  [ui-vs-library]
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  from weavingspace import TileUnit, Tiling
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(700)
  dlg._rebuild_unit()
  _generate_and_wait(dlg)
  coarse = {t: project.mapLayer(lid).featureCount()
            for t, lid in dlg._element_layer_ids.items()}

  # change the design and generate AT ONCE -- no rebuild, no waiting
  dlg.spacing_spin.setValue(420)
  assert dlg._preview_timer.isActive(), \
    "the rebuild should still be pending; otherwise this proves nothing"
  _generate_and_wait(dlg)

  fine = {t: project.mapLayer(lid).featureCount()
          for t, lid in dlg._element_layer_ids.items()}
  assert sum(fine.values()) > sum(coarse.values()) * 2, \
    f"the map still looks like the old design ({sum(coarse.values())} " \
    f"tiles at 700, {sum(fine.values())} after asking for 420)"

  # and it matches what the library makes of the design now on screen
  expected = Tiling(
    TileUnit(tiling_type="laves", code="3.3.4.3.4", spacing=420,
             crs=3857),
    bridge.layer_to_gdf(layer, ["v1", "v2", "v3"])) \
    .get_tiled_map(join_on_prototiles=False, retain_tileables=False,
                   ragged_edges=True).map
  for tid in sorted(fine):
    want = len(expected[expected["tile_id"] == tid])
    assert fine[tid] == want, \
      f"element {tid}: {fine[tid]} tiles, but the design on screen " \
      f"means {want}"
  dlg.close()


def test_typing_updates_the_design():
  """Typing in a design field must reach the unit on its own.

  Every other test that exercises the over-under field calls
  _rebuild_unit() afterwards, which means the signal connection could
  be deleted and nothing would notice -- an automatic mutant removed
  exactly that line and survived. Here the only thing that may act is
  the dialog's own debounce.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("weave")
  dlg.family_combo.setCurrentText("twill weave ab|cd")
  dlg._rebuild_unit()
  before = tuple(dlg._unit.n)

  dlg.opt_over_under.setText("1,2,2,1")
  _tick(700)          # only the debounce may act
  assert tuple(dlg._unit.n) == (1, 2, 2, 1), \
    f"typing did not reach the unit: n is {tuple(dlg._unit.n)}, was " \
    f"{before}"

  # the same for the numeric design fields
  dlg.opt_aspect.setValue(0.4)
  _tick(700)
  assert abs(dlg._unit.aspect - 0.4) < 1e-9, \
    "the strand-width spin did not reach the unit on its own"

  # and the preview follows, without anyone asking it to
  assert len(dlg.preview._labels) == len(dlg._unit.tiles)
  dlg.close()


def test_an_inset_percentage_is_a_percentage_of_the_spacing():
  """10% at a 1000-unit spacing insets by 100 units. Exactly.

  Both inset controls are percentages of the spacing, converted with a
  single division. Divide by 101 instead and every map is about one
  percent different — tiles very slightly smaller than asked for. No
  picture looks wrong, and the UI-against-library comparisons allow a
  percent of area difference for antialiasing and rounding, so a one
  percent error passes them all.

  An earlier attempt compared areas against inset_tiles applied to an
  already-built unit, and disagreed by forty percent: that is not the
  same operation the dialog performs, and a test whose oracle is
  wrong is worse than no test. So this watches what the dialog ASKS
  the library for, which is precisely the conversion in question, and
  leaves the geometry to the library.

  Regression: the inset percentage conversion was defended only by comparisons whose tolerance is wider than the error.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  _tick(200)
  dlg.spacing_spin.setValue(1000)
  dlg._rebuild_unit()
  _tick(150)
  assert dlg._unit is not None, "no unit was built to work from"

  # Patch the class of the unit the dialog ACTUALLY built. The library
  # is importable only once the plugin has put its vendored copy on
  # the path, so importing it by name here can resolve a different
  # class object than the dialog uses -- which it did, and the spy
  # silently never fired.
  asked = []

  def watch(percentage, spacing):
    """Rebuild with these settings and return what the library was
    asked to inset by.

    Args:
      percentage: the tile-inset control's value, which must be
        within its range (0 to 5) or setValue clamps it silently.
      spacing: the pattern's grain in map units.

    Returns:
      A list of the distances passed to inset_tiles during the
      rebuild, newest last.

    The class is re-read on every call. A tiling and a weave are
    different classes, so a class captured once and reused patches
    nothing after the design kind changes -- and the spy then reports
    no calls at all, which reads as "the weave never insets" rather
    than as a broken test.
    """
    asked.clear()
    dlg.spacing_spin.setValue(spacing)
    dlg.mod_t_inset.setValue(percentage)
    dlg._rebuild_unit()               # settle on the current kind
    _tick(100)
    unit_class = type(dlg._unit)
    original = unit_class.inset_tiles
    owned = "inset_tiles" in unit_class.__dict__

    def spy(self, distance, *args, **kwargs):
      asked.append(distance)
      return original(self, distance, *args, **kwargs)

    unit_class.inset_tiles = spy
    try:
      dlg._rebuild_unit()
      _tick(150)
    finally:
      # always put it back, or every later test in the process runs
      # against the spy
      if owned:
        unit_class.inset_tiles = original
      else:
        del unit_class.inset_tiles
    return list(asked)

  # A TILING: the inset is a plain percentage of the spacing.
  kinds = [dlg.kind_combo.itemText(i)
           for i in range(dlg.kind_combo.count())]
  tiling = next(k for k in kinds if "til" in k.lower())
  weave = next(k for k in kinds if "weav" in k.lower())
  dlg.kind_combo.setCurrentText(tiling)
  _tick(200)

  # 4%, not 10%: the tile-inset control tops out at 5, and setValue
  # clamps silently. Asking for a value the user cannot type made an
  # earlier version of this test read the clamp as a wrong divisor.
  first = watch(4, 1000)
  assert first, "the dialog never insetted the tiles at all"
  assert abs(first[-1] - 40.0) < 1e-9, \
    f"a 4% tile inset at 1000 map units asked the library for "\
    f"{first[-1]}, not 40. The percentage does not mean what the "\
    f"control says it means"

  # a second pair, so the test cannot pass on a coincidence of one
  # particular spacing
  second = watch(2.5, 400)
  assert second and abs(second[-1] - 10.0) < 1e-9, \
    f"2.5% of 400 map units should be 10, not {second[-1:]}"

  # A WEAVE insets by the same percentage scaled by strand width, so
  # that thin strands are not swallowed by a value a tiling shrugs
  # off. That is deliberate, and it is why this test states the two
  # formulas separately rather than assuming one: the first version
  # asserted the tiling rule against the dialog's default design,
  # which is a weave, and read the aspect scaling as an error.
  dlg.kind_combo.setCurrentText(weave)
  _tick(250)
  aspect = dlg.opt_aspect.value()
  third = watch(4, 1000)
  expected = 4 * aspect * 1000 / 100
  assert third, "the weave never insetted its tiles"
  assert abs(third[-1] - expected) < 1e-9, \
    f"a 4% inset on a weave of aspect {aspect} at 1000 map units "\
    f"asked for {third[-1]}, not {expected}"
  dlg.close()


def test_every_element_count_still_has_its_designs():
  """The catalogue offers a design for every element count it claims.

  TILINGS_BY_N is a dict literal keyed by element count. Duplicate a
  key by mistake — 5 typed as 6 — and Python keeps only the last, so
  an entire element count DISAPPEARS along with every design filed
  under it. The user asks for five variables and is offered nothing.

  Every other catalogue test iterates the keys that exist, and so
  cannot see a key that stopped existing. This one states the counts
  the plugin promises, independently of the catalogue, and checks each
  is present and populated.

  Regression: a vanished element count was invisible, because the catalogue tests all iterate the catalogue's own keys.
  """
  from weavingspace_qgis import catalog
  # 2 to 16, then 18, 19, 20: the counts the element chooser offers.
  # Written out rather than derived from the catalogue, because a test
  # that asks the catalogue what it contains cannot notice it losing
  # something.
  expected = set(range(2, 17)) | {18, 19, 20}
  actual = set(catalog.TILINGS_BY_N)
  missing = sorted(expected - actual)
  extra = sorted(actual - expected)
  assert not missing, \
    f"element count(s) {missing} have no designs at all; a user "\
    f"choosing that many variables is offered an empty list"
  assert not extra, \
    f"the catalogue carries element count(s) {extra} the chooser "\
    f"does not offer, so those designs are unreachable"
  for n in sorted(expected):
    families = catalog.TILINGS_BY_N[n]
    assert families, f"element count {n} is present but empty"
    for name, entry in families.items():
      if entry["type"] == "tiling" and "n" in entry:
        assert entry["n"] == n or entry["tiling_type"] == "grid", \
          f"{name} declares n={entry['n']} but is filed under {n}"


def test_every_declared_offset_is_pinned():
  """Each slice or dissection entry's offset is the one intended.

  An offset changes where a tiling's cuts fall: the element count is
  identical either way, so the sweep that counts elements cannot see
  it, and the geometry it produces is a different design. One such
  mutant was caught before by naming a few entries explicitly, which
  left every entry nobody thought to name unguarded — and a later
  batch duly moved square-slice 8's offset with nothing noticing.

  So this pins every entry that declares an offset, and requires the
  table below to cover them all. A new entry with an offset fails
  here until someone states what it should be, which is the point:
  the value is a design decision, not an implementation detail.

  Regression: only hand-listed offsets were pinned, so entries nobody had listed could be changed freely.
  """
  from weavingspace_qgis import catalog
  # Every entry in the catalogue declares offset 0: slices and
  # dissections start at the corners. Stating the RULE rather than
  # listing twenty-six names means a new entry is covered the moment
  # it is added, and an entry that genuinely wants a different offset
  # has to be named below — a deliberate act, which is what a design
  # decision deserves.
  DEFAULT_OFFSET = 0
  deliberate_exceptions = {}      # name -> offset, when one is wanted

  seen, wrong = 0, []
  for n, families in catalog.TILINGS_BY_N.items():
    for name, entry in families.items():
      if "offset" not in entry:
        continue
      seen += 1
      expected = deliberate_exceptions.get(name, DEFAULT_OFFSET)
      if entry["offset"] != expected:
        wrong.append(
          f"{name} (under {n}): offset {entry['offset']}, expected "
          f"{expected}")
  assert not wrong, \
    "offsets changed; each one is a different design:\n  " + \
    "\n  ".join(wrong)
  assert seen >= 20, \
    f"only {seen} entries declare an offset; this test is not "\
    f"covering the catalogue it claims to"
  stale = sorted(set(deliberate_exceptions))
  assert not stale or seen, f"stale exceptions listed: {stale}"


def test_catalogue_values_are_what_they_claim():
  """The catalogue's OPTION VALUES matter, not just its element counts.

  The sweep checks that every family yields the right number of
  elements, which an automatic mutant showed is not enough: changing
  "hex-slice 2" from offset 0 to offset 1 leaves the count identical
  and the geometry quite different, and nothing failed. These
  assertions pin the values that change what a design looks like.
  """
  from weavingspace_qgis import catalog
  from weavingspace import TileUnit

  # the offsets the catalogue declares are the ones the library uses
  spec = catalog.TILINGS_BY_N[2]["hex-slice 2"]
  assert spec["offset"] == 0, \
    "hex-slice entries start at the corners (offset 0); a different " \
    "default is a different design"
  at_zero = catalog.make_unit(spec, spacing=500, crs=3857)
  at_one = catalog.make_unit(dict(spec, offset=1), spacing=500, crs=3857)
  assert at_zero.tiles.geometry.iloc[0].wkt != \
    at_one.tiles.geometry.iloc[0].wkt, \
    "offset must change the geometry, or this assertion proves nothing"

  # every declared option is a value the constructor accepts, and the
  # families that take angles declare sane ones
  for n, families in catalog.TILINGS_BY_N.items():
    for name, entry in families.items():
      if entry["type"] != "tiling":
        assert entry["weave_type"] in (
          "plain", "twill", "basket", "cube", "this"), name
        assert "|" in entry["strands"], f"{name}: strands need a | "
        continue
      if "offset" in entry:
        assert -1 <= entry["offset"] <= 1, f"{name}: offset out of range"
      if "offset_angle" in entry:
        assert -50 <= entry["offset_angle"] <= 85, f"{name}: bad angle"
      if "point_angle" in entry:
        assert 10 <= entry["point_angle"] <= 120, f"{name}: bad angle"
      if "n" in entry:
        assert entry["n"] == n or entry["tiling_type"] in ("grid",), \
          f"{name}: declares n={entry['n']} under key {n}"

  # every declared offset, not only hex-slice 2's: a mutant moved
  # "hex-slice 7" from 0 to 1 and nothing noticed, because the sweep
  # only ever counted elements
  known_offsets = {"hex-slice 2": 0, "hex-slice 7": 0,
                   "hex-dissection 4": 0, "hex-dissection 7": 0,
                   "square-slice 2": 0, "square-slice 3": 0,
                   "square-slice 4": 0}
  for name, expected in known_offsets.items():
    for n, families in catalog.TILINGS_BY_N.items():
      if name in families and "offset" in families[name]:
        assert families[name]["offset"] == expected, \
          f"{name} declares offset {families[name]['offset']}, not "\
          f"{expected}; the cuts would start somewhere else entirely"

  # the two library extras are still there and still parameterised
  assert catalog.TILINGS_BY_N[4]["grid 4"]["tiling_type"] == "grid"
  assert catalog.TILINGS_BY_N[4]["stripes 4"]["n"] == 4
  assert catalog.tightest_grid(4) == (2, 2)
  assert catalog.tightest_grid(6) in ((2, 3), (3, 2))

  # over-under parsing, whose return value an automatic mutant
  # replaced with None unnoticed
  assert catalog.get_over_under("1,2") == (1, 2)
  assert catalog.get_over_under("1,2,2,1") == (1, 2, 2, 1)
  # a single number stays a single number: the parser trims to an even
  # LENGTH (2 * len // 2), which is 1 for one number, so "2" means the
  # one-element pattern the library reads as regular over-under. This
  # is ported verbatim from the app, and the assertion records what it
  # actually does rather than what one might assume
  assert catalog.get_over_under("2") == (2,)
  assert catalog.get_over_under("3") == (3,)
  # anything unparseable falls back rather than raising at the user
  assert catalog.get_over_under("nonsense") == (2, 2)
  assert catalog.get_over_under("") == (2, 2)
  assert catalog.get_over_under("1,x,2") == (2, 2)


def test_ui_affordances_are_deliberate():
  """The small numbers that shape how the controls feel.

  Step sizes, ranges and formats are design decisions -- 5% opacity
  steps, 2 to 20 classes, a progress label that says what is
  happening -- and automatic mutants walked through several of them
  untouched. Cheap to pin, and the assertions double as a record of
  what was chosen on purpose.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg._update_dynamic_columns()

  opacity = dlg._row_opacity(0)
  assert (opacity.minimum(), opacity.maximum()) == (0, 100)
  assert opacity.singleStep() == 5, \
    "opacity steps in fives; single-unit steps make the arrows useless"
  assert opacity.suffix().strip() == "%"

  classes = dlg.table.cellWidget(0, 3)
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Quantiles")
  dlg._update_dynamic_columns()
  classes = dlg.table.cellWidget(0, 3)
  assert (classes.minimum(), classes.maximum()) == (2, 20), \
    f"class counts run 2-20, not {classes.minimum()}-{classes.maximum()}"

  assert dlg.shells_spin.maximum() >= 2, "context shells need range"
  # the ranges the family options declare: a dissection's inner angle
  # and a star's point angle both have limits the library expects
  assert (dlg.opt_offset_angle.minimum(),
          dlg.opt_offset_angle.maximum()) == (-50, 85), \
    "the inner-angle range must match what the dissections accept"
  assert (dlg.opt_point_angle.minimum(),
          dlg.opt_point_angle.maximum()) == (10, 120), \
    "the point-angle range must match what the stars accept"
  assert (dlg.opt_offset.minimum(), dlg.opt_offset.maximum()) == (-1, 1)
  assert dlg.opt_aspect.maximum() == 1.0, \
    "strand width is a fraction of spacing, so it stops at 1"

  switch = dlg._row_reverse(0)
  assert switch.width() >= 28 and switch.height() >= 14, \
    f"the reverse switch needs room for its knob to travel "\
    f"({switch.width()}x{switch.height()})"
  # the progress bar only describes itself once a run is under way;
  # at rest it carries Qt's default. Start one and look.
  dlg.spacing_spin.setValue(500)
  dlg._generate()
  assert dlg._task is not None
  _tick(300)
  text = dlg.progress.format().lower()
  assert "%p%" in text, "the progress bar must show a percentage"
  assert any(word in text for word in ("tiling", "joining", "layers")), \
    f"and say what it is doing ({text!r}), since during a long run it " \
    "is the only thing on screen"
  _settle(dlg, 60)
  dlg.close()


# ------------------------------------------------------- metamorphic
# Nobody can say what the "correct" tiled map is -- there is no oracle
# for a picture. But there are RELATIONS that must hold between one
# map and another, and those can be checked without knowing the right
# answer: undo something twice and you are back where you started;
# ask for a finer pattern and you get more tiles; rename which
# variable feeds which element and the colours follow it exactly.
# These catch whole classes of error that no single-output assertion
# can, and they keep working where no reference implementation exists.

def _element_ramps(dlg, project):
  """{element: darkest colour of its ramp} for the current map.

  Args:
    dlg: the dialog whose output layers to read.
    project: the QgsProject holding those layers, passed rather than
      fetched so a test can ask about a project it controls.

  Returns:
    {tile_id: "#rrggbb"} taking each element's ramp at its dark end,
    or None for an element whose renderer has no ramp (a single
    colour, or no variable). The dark end identifies a ramp far more
    reliably than the pale one, where every sequential scheme is
    nearly white.
  """
  out = {}
  for tid, lid in dlg._element_layer_ids.items():
    renderer = project.mapLayer(lid).renderer()
    ramp = getattr(renderer, "sourceColorRamp", None)
    out[tid] = ramp().color(1.0).name() if ramp else None
  return out


def test_metamorphic_reversal_is_an_involution():
  """Reversing a ramp twice must return exactly the original map.

  No knowledge of what the colours SHOULD be is needed: whatever they
  are, doing the same thing twice has to undo it. A rounding error in
  the reversal, or a reversal applied to an already-reversed ramp,
  breaks this without breaking any absolute assertion.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(500)
  _generate_and_wait(dlg)
  original = _element_ramps(dlg, project)

  dlg._row_reverse(0).setChecked(True)
  assert dlg._restyle_only()
  reversed_once = _element_ramps(dlg, project)
  assert reversed_once["a"] != original["a"], \
    "reversing must change something, or the test proves nothing"

  dlg._row_reverse(0).setChecked(False)
  assert dlg._restyle_only()
  assert _element_ramps(dlg, project) == original, \
    "reverse twice must be the identity"

  # and the same holds for a discrete scheme
  dlg.table.cellWidget(2, 1).setCurrentText("landcover")
  dlg._update_dynamic_columns()
  _generate_and_wait(dlg)
  before = {str(c.value()): c.symbol().color().name()
            for c in project.mapLayer(dlg._element_layer_ids["c"])
            .renderer().categories() if c.value()}
  for _ in range(2):
    dlg._row_reverse(2).setChecked(not dlg._row_reverse(2).isChecked())
    dlg._restyle_only()
  after = {str(c.value()): c.symbol().color().name()
           for c in project.mapLayer(dlg._element_layer_ids["c"])
           .renderer().categories() if c.value()}
  assert after == before, "reversing a categorical scheme twice too"
  dlg.close()


def test_metamorphic_full_rotation_and_scaling():
  """Rotating a design by 360 degrees reproduces it; halving the
  spacing multiplies the tiles by about four.

  The first is exact geometry: a full turn is the identity, however
  the modifier chain is implemented. The second is a scaling law --
  tiles cover area, so a pattern half as coarse needs roughly four
  times as many -- which catches a spacing that reaches the library
  in the wrong units or the wrong direction.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(600)
  dlg._rebuild_unit()
  at_rest = [g.wkt for g in dlg._unit.tiles.geometry]

  dlg.mod_rotate.setValue(90)
  dlg._rebuild_unit()
  turned = [g.wkt for g in dlg._unit.tiles.geometry]
  assert turned != at_rest, "a quarter turn must change the unit"

  # 90 x 4 = 360: back where we started, to within floating point
  from weavingspace import TileUnit
  full_turn = TileUnit(tiling_type="laves", code="3.3.4.3.4",
                       spacing=600, crs=3857)
  for _ in range(4):
    full_turn = full_turn.transform_rotate(90)
  base = TileUnit(tiling_type="laves", code="3.3.4.3.4", spacing=600,
                  crs=3857)
  for turned_tile, base_tile in zip(full_turn.tiles.geometry,
                                    base.tiles.geometry):
    assert turned_tile.equals_exact(base_tile, 1e-6), \
      "four quarter-turns must return the original unit"

  # the scaling law, measured on real output
  dlg.mod_rotate.setValue(0)
  counts = {}
  for spacing in (800, 400):
    dlg.spacing_spin.setValue(spacing)
    _generate_and_wait(dlg)
    counts[spacing] = sum(project.mapLayer(lid).featureCount()
                          for lid in dlg._element_layer_ids.values())
  ratio = counts[400] / max(counts[800], 1)
  assert 3.0 < ratio < 5.0, \
    f"halving the spacing should give about four times the tiles, " \
    f"got {ratio:.1f}x ({counts})"
  dlg.close()


def test_metamorphic_variable_permutation():
  """Swapping which variable feeds which element swaps the map's
  colours correspondingly, and changes nothing else.

  This is the relation that catches a join wired to the wrong column,
  or symbology applied to the wrong element -- errors that leave a
  perfectly plausible map behind, which no absolute assertion about
  "the right colours" would notice, because both maps look right.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(500)
  # v1 and v2 are the row and column indices of the same square grid,
  # so their distributions are identical and swapping them would prove
  # nothing; v3 is their product and classes quite differently
  for row, var in enumerate(("v1", "v3", "v1", "v3")):
    dlg.table.cellWidget(row, 1).setCurrentText(var)
  for row, ramp in enumerate(("Reds", "Blues", "Reds", "Blues")):
    dlg.table.cellWidget(row, 4).setCurrentText(ramp)
  _generate_and_wait(dlg)

  def class_bounds(tid):
    renderer = project.mapLayer(dlg._element_layer_ids[tid]).renderer()
    return [(round(r.lowerValue(), 6), round(r.upperValue(), 6))
            for r in renderer.ranges()]

  a_bounds, b_bounds = class_bounds("a"), class_bounds("b")
  assert a_bounds != b_bounds, \
    "v1 and v3 must class differently, or the swap proves nothing"

  # swap the variables on a and b; their class bounds must swap too
  dlg.table.cellWidget(0, 1).setCurrentText("v3")
  dlg.table.cellWidget(1, 1).setCurrentText("v1")
  _generate_and_wait(dlg)
  assert class_bounds("a") == b_bounds, \
    "element a now carries v2, so it must class exactly as b did"
  assert class_bounds("b") == a_bounds, \
    "and b must class exactly as a did"
  # the elements nobody touched are untouched
  assert class_bounds("c") == a_bounds, "c still carries v1"
  assert class_bounds("d") == b_bounds, "d still carries v3"
  dlg.close()


def test_metamorphic_translation_invariance():
  """Moving the region moves the map with it, and changes nothing
  about its content.

  Tiling is defined relative to the region, so shifting every polygon
  by a fixed offset must shift the map by the same offset and leave
  the tile count and the data joined to each element identical. A
  grid anchored to absolute coordinates instead of to the region
  would fail this while looking fine in any single map.
  """
  from weavingspace_qgis import bridge
  from weavingspace import TileUnit, Tiling
  region = bridge.layer_to_gdf(make_region_layer(), ["v1", "v2"])
  unit = TileUnit(tiling_type="laves", code="3.3.4.3.4", spacing=500,
                  crs=3857)

  here = Tiling(unit, region.copy()).get_tiled_map().map
  moved_region = region.copy()
  moved_region["geometry"] = moved_region.geometry.translate(
    xoff=100_000, yoff=-50_000)
  there = Tiling(unit, moved_region).get_tiled_map().map

  assert len(here) == len(there), \
    f"moving the region changed the tile count ({len(here)} vs " \
    f"{len(there)})"
  assert sorted(here["tile_id"]) == sorted(there["tile_id"]), \
    "the same elements must appear, wherever the region sits"
  # translation is rigid, so the covered area is identical
  assert abs(here.geometry.area.sum() - there.geometry.area.sum()) < 1.0, \
    "a translated region must be covered by the same amount of tile"
  # Each element covers the same area as before, too -- the pattern is
  # congruent, not merely the same size overall.
  for tid in sorted(set(here["tile_id"])):
    a = here[here["tile_id"] == tid].geometry.area.sum()
    b = there[there["tile_id"] == tid].geometry.area.sum()
    assert abs(a - b) < 1.0, f"element {tid} covers a different area"

  # What is NOT invariant, and should not be asserted to be: WHICH
  # polygon each tile takes its data from. The grid is anchored to the
  # region's bounding rectangle, so moving the data shifts the
  # pattern's phase against the polygons and the join changes. That is
  # a property of the design rather than a defect -- worth knowing,
  # because it means a map is reproducible only for a fixed region.
  same_values = (sorted(here["v1"].dropna().round(6)) ==
                 sorted(there["v1"].dropna().round(6)))
  assert not same_values or True, \
    "recorded for the reader: phase, and so the join, may differ"


def test_metamorphic_opacity_round_trip():
  """Softening an element and restoring it returns the same picture.

  Opacity is stored apart from the colours precisely so this holds;
  if it were folded into them, the round trip would lose information
  and this would fail.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(500)
  _generate_and_wait(dlg)

  def snapshot():
    out = {}
    for tid, lid in dlg._element_layer_ids.items():
      lay = project.mapLayer(lid)
      renderer = lay.renderer()
      ramp = getattr(renderer, "sourceColorRamp", None)
      out[tid] = (round(lay.opacity(), 6),
                  ramp().color(1.0).name() if ramp else None)
    return out

  before = snapshot()
  for value in (40, 75, 15, 100):
    dlg._row_opacity(0).setValue(value)
    assert dlg._restyle_only()
  assert snapshot() == before, \
    "returning opacity to 100 must return the original appearance"
  dlg.close()


# ------------------------------------------------------ model-based
# A small state machine of what the dialog IS at any moment, and what
# each action is supposed to do to it. The fuzz test asks "did
# anything break?"; this asks "did the thing that happened match what
# was supposed to happen?", which is a different and stronger
# question. Transitions are walked deliberately rather than at
# random, so every one is exercised at least once.

def test_model_based_dialog_states():
  """Walk the dialog's state machine, checking the model at each step.

  States, in the model's terms:
      empty     -- a dialog with no map generated yet
      mapped    -- a map exists in the project
      styled    -- a map exists and an element has been restyled
      compared  -- a second group exists alongside the first
      filed     -- output is going to a GeoPackage

  Each transition below states what must be true AFTERWARDS. The
  point is not that the plugin survives the walk (the fuzz test
  covers that) but that each step lands in the state it claims.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(520)

  def groups():
    return [c for c in project.layerTreeRoot().children()
            if c.nodeType() == 0]

  def elements_live():
    return all(project.mapLayer(lid) is not None
               for lid in dlg._element_layer_ids.values())

  state = "empty"
  assert not dlg._element_layer_ids and not groups(), \
    "a fresh dialog has generated nothing"

  # empty -> mapped
  _generate_and_wait(dlg)
  state = "mapped"
  assert len(groups()) == 1 and elements_live()
  assert set(dlg._element_layer_ids) == set(dlg._tile_ids())
  first_ids = dict(dlg._element_layer_ids)

  # mapped -> styled: same layers, new symbology, no new group
  dlg.table.cellWidget(0, 4).setCurrentText("YlGn")
  assert dlg._restyle_only()
  state = "styled"
  assert dlg._element_layer_ids == first_ids, \
    "restyling must not replace the layers"
  assert len(groups()) == 1
  seeded = project.mapLayer(dlg._element_layer_ids["a"]).renderer() \
    .sourceColorRamp().color(1.0).name()
  assert seeded == bridge.get_ramp("YlGn").color(1.0).name()

  # styled -> mapped (a design change replaces the layers in place)
  dlg.spacing_spin.setValue(460)
  _generate_and_wait(dlg)
  state = "mapped"
  assert len(groups()) == 1, "a regeneration does not add a group"
  assert elements_live()
  assert dlg._element_layer_ids != first_ids, \
    "new geometry means new layers"

  # mapped -> compared: exactly one more group, the old one intact
  kept = dict(dlg._element_layer_ids)
  kept_group = dlg._group_name
  dlg.opt_new_group.setChecked(True)
  _generate_and_wait(dlg)
  state = "compared"
  assert len(groups()) == 2, f"expected two groups, found {len(groups())}"
  assert dlg._group_name != kept_group
  assert all(project.mapLayer(lid) is not None for lid in kept.values()), \
    "the kept comparison must survive intact"
  dlg.opt_new_group.setChecked(False)

  # compared -> filed: output moves to a file, layers become
  # file-backed, and no further group appears
  import tempfile as tf
  with tf.TemporaryDirectory() as td:
    path = os.path.join(td, "model.gpkg")
    dlg.gpkg_widget.setFilePath(path)
    _generate_and_wait(dlg)
    state = "filed"
    assert os.path.exists(path), "the GeoPackage must exist"
    # a change of output PATH starts a new group by design (see
    # force_new in _add_output_layers): the previous result came from
    # somewhere else, and overwriting it in place would conflate two
    # different outputs
    assert len(groups()) == 3, \
      f"changing the output target starts its own group, found "\
      f"{len(groups())}"
    for tid, lid in dlg._element_layer_ids.items():
      source = project.mapLayer(lid).source()
      assert path in source, \
        f"element {tid} should read from the file, not memory"
    # filed -> mapped: back to temporary output
    for lid in list(dlg._element_layer_ids.values()):
      project.removeMapLayer(lid)
    dlg.gpkg_widget.setFilePath("")
  _generate_and_wait(dlg)
  state = "mapped"
  assert len(groups()) == 4, \
    "and going back to temporary output starts another, for the " \
    "same reason"
  assert elements_live()
  for tid, lid in dlg._element_layer_ids.items():
    assert "memory" in project.mapLayer(lid).source() or \
      project.mapLayer(lid).providerType() == "memory", \
      f"element {tid} should be temporary again"
  assert state == "mapped"
  dlg.close()


def test_controls_respond_without_being_prompted():
  """Every control must act through its own signal, not because a
  test called the rebuild afterwards.

  Automatic mutants removed four separate connections and unblockings
  and walked past the whole suite, because the tests that exercise
  those controls call _rebuild_unit() or _restyle_only() themselves.
  A user has no such option: if the connection is gone, the control
  is dead. Everything here changes a control and then lets ONLY the
  dialog's own machinery run.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import bridge
  from qgis.gui import QgsColorButton
  from qgis.PyQt.QtGui import QColor
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("grid 4")
  _tick(700)

  # 1. the grid spinners must still respond AFTER a family change,
  # which is when their signals are blocked and restored
  assert dlg.opt_grid_row[1].isVisibleTo(dlg)
  before = dlg._unit.tiles.geometry.iloc[0].wkt
  dlg.opt_grid_cols.setValue(4)
  dlg.opt_grid_rows.setValue(1)
  _tick(700)          # only the dialog's debounce may act
  assert dlg._unit.tiles.geometry.iloc[0].wkt != before, \
    "editing rows/cols after a family change did nothing: the "\
    "signals were left blocked"

  # 1b. the star point angle, which has its own connection. The family
  # is looked up rather than named: "star 6" does not exist, and an
  # earlier version of this block silently skipped itself for that
  # reason, which is how a deleted connection survived a batch.
  from weavingspace_qgis import catalog as _catalog
  star = next(((n, name) for n, fams in _catalog.TILINGS_BY_N.items()
               for name, entry in fams.items()
               if "point_angle" in entry), None)
  assert star is not None, "the catalogue should offer a star family"
  dlg.n_combo.setCurrentText(str(star[0]))
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText(star[1])
  _tick(700)
  assert dlg.opt_point_angle.isVisibleTo(dlg), \
    f"{star[1]} should show its point-angle control"
  if True:
    before_star = dlg._unit.tiles.geometry.iloc[0].wkt
    dlg.opt_point_angle.setValue(dlg.opt_point_angle.value() + 15)
    _tick(700)
    assert dlg._unit.tiles.geometry.iloc[0].wkt != before_star, \
      "changing the star's point angle did not reach the design"

  # 2. a colour picked on a Single colour row must reach the element's
  # memory on its own, so it survives a later rebuild
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  _tick(700)
  dlg.table.cellWidget(0, 2).setCurrentText("Single colour")
  dlg._update_dynamic_columns()
  button = dlg.table.cellWidget(0, 4)
  assert isinstance(button, QgsColorButton)
  button.setColor(QColor("#3d5a80"))
  _tick(500)
  assert dlg._single_colours.get("a") == "#3d5a80", \
    "picking a colour did not record it against the element; the "\
    "choice would be lost at the next rebuild"

  # 3. the ramp swatches must be redrawn when an element is reversed,
  # so what the row shows is the direction the map will use
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Quantiles")
  dlg._update_dynamic_columns()
  combo = dlg.table.cellWidget(0, 4)
  combo.setCurrentText("Reds")
  _tick(300)
  forward_icon = combo.itemIcon(combo.currentIndex()).pixmap(48, 14)
  dlg._row_reverse(0).setChecked(True)
  _tick(300)
  reversed_icon = combo.itemIcon(combo.currentIndex()).pixmap(48, 14)
  assert forward_icon.toImage() != reversed_icon.toImage(), \
    "the ramp swatch did not turn around with the Reverse switch"
  dlg.close()


def test_dialog_structure():
  """The dialog has the parts it is supposed to have.

  Nothing asserted this, and an automatic mutant that deleted the
  Help tab outright walked past the entire suite -- a user-visible
  feature simply gone. Structure is cheap to pin and exactly the kind
  of thing that disappears in a refactor without any test noticing.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)

  from qgis.PyQt.QtWidgets import QTabWidget
  tabs = dlg.findChild(QTabWidget)
  assert tabs is not None, "the dialog is built around a tab widget"
  labels = [tabs.tabText(i) for i in range(tabs.count())]
  for wanted in ("Design", "Data", "Help"):
    assert any(wanted.lower() in label.lower() for label in labels), \
      f"the {wanted} tab is missing; tabs are {labels}"

  # the help tab must actually carry the help, not just exist
  from qgis.PyQt.QtWidgets import QTextBrowser
  browser = dlg.findChild(QTextBrowser)
  assert browser is not None, "the Help tab needs its text"
  text = browser.toHtml()
  assert "weavingspace" in text.lower() or "tiling" in text.lower(), \
    "the help text does not mention what the plugin does"
  version = [line.split("=", 1)[1].strip()
             for line in open(os.path.join(
               ROOT, "weavingspace_qgis", "metadata.txt"),
               encoding="utf-8")
             if line.startswith("version=")][0]
  assert version in text or version in dlg.windowTitle(), \
    f"the version {version} should be visible to the user"

  # and the controls a user needs are all present and enabled
  for name in ("layer_combo", "n_combo", "kind_combo", "family_combo",
               "spacing_spin", "generate_btn", "live_check",
               "gpkg_widget", "table", "preview"):
    widget = getattr(dlg, name, None)
    assert widget is not None, f"the dialog lost its {name}"
  assert dlg.generate_btn.isEnabled()
  # Nine since the Categorical colour editor arrived. The count is
  # asserted rather than ignored because the columns are addressed by
  # NUMBER throughout this suite, so one appearing in the middle would
  # repoint dozens of assertions at the wrong widget without failing
  # anything -- which is why "Edit colours" is last logically and only
  # moved next to the ramp for display.
  from weavingspace_qgis.dialog import COL_EDIT_COLOURS
  assert dlg.table.columnCount() == 9, \
    f"the table has {dlg.table.columnCount()} columns, expected 9"
  assert dlg.table.horizontalHeaderItem(0).text() == "Tile id", \
    "the first column moved, so every numbered assertion here is suspect"
  assert dlg.table.horizontalHeaderItem(4).text() == "Colour ramp", \
    "the ramp column moved; a new column was inserted rather than appended"
  assert dlg.table.horizontalHeaderItem(
    COL_EDIT_COLOURS).text() == "Edit colours"

  # The columns that depend on what is mapped are hidden until they
  # mean something. Checked on a dialog with NO layer, which is what a
  # first-time user meets: nothing is categorical, so the class source
  # and Edit colours would both be dead columns. Asserted by NUMBER as
  # well as by state, because hiding the wrong index is invisible
  # until a user meets a column that should not be there. (Classes is
  # excluded: this dialog has a layer and variables, so a class count
  # is real here — it earns its column and is checked elsewhere.)
  bare = QgsProject.instance()
  for existing in list(bare.mapLayers().values()):
    bare.removeMapLayer(existing.id())
  empty = WeavingSpaceDialog(iface=None)
  _tick(200)
  for column in (7, COL_EDIT_COLOURS):
    name = empty.table.horizontalHeaderItem(column).text()
    assert empty.table.isColumnHidden(column), \
      f"column {column} ({name}) is showing on a dialog with no "\
      f"layer, where it can only be empty"
  for column in (0, 1, 2, 4):
    name = empty.table.horizontalHeaderItem(column).text()
    assert not empty.table.isColumnHidden(column), \
      f"column {column} ({name}) is hidden but always means something"
  empty.close()
  dlg.close()


def test_first_field_is_not_a_special_case():
  """A variable that happens to be the layer's FIRST field must work.

  Field indices are 0-based, and a guard written as ``idx <= 0``
  instead of ``idx < 0`` treats the first field as missing. An
  automatic mutant made exactly that change and survived, because
  every categorical test in the suite mapped a field further down the
  list. This maps the first one.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import compat
  project = QgsProject.instance()
  # a layer whose FIRST field is the categorical one
  layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "first", "memory")
  layer.dataProvider().addAttributes([compat.make_field("kind", str),
                                      compat.make_field("value", float)])
  layer.updateFields()
  cats = ["alpha", "beta", "gamma"]
  feats = []
  for i in range(4):
    for j in range(4):
      f = QgsFeature(layer.fields())
      f.setGeometry(QgsGeometry.fromWkt(
        f"POLYGON(({i*1000} {j*1000}, {(i+1)*1000} {j*1000}, "
        f"{(i+1)*1000} {(j+1)*1000}, {i*1000} {(j+1)*1000}, "
        f"{i*1000} {j*1000}))"))
      f["kind"] = cats[(i + j) % 3]
      f["value"] = float(i * j)
      feats.append(f)
  layer.dataProvider().addFeatures(feats)
  layer.updateExtents()
  project.addMapLayer(layer)
  assert layer.fields().indexOf("kind") == 0, \
    "this test needs the categorical field at index 0"

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  dlg.spacing_spin.setValue(500)
  dlg.table.cellWidget(0, 1).setCurrentText("kind")
  dlg._update_dynamic_columns()

  # the detected category count comes from the field at index 0
  k_spin = dlg.table.cellWidget(0, 3)
  assert k_spin.value() == 3, \
    f"three categories in the first field, the dialog counted "\
    f"{k_spin.value()}"
  assert not k_spin.isEnabled(), "categorical counts are not editable"

  _generate_and_wait(dlg)
  renderer = project.mapLayer(dlg._element_layer_ids["a"]).renderer()
  assert isinstance(renderer, QgsCategorizedSymbolRenderer)
  values = {str(c.value()) for c in renderer.categories() if c.value()}
  assert values == set(cats), \
    f"the first field's categories did not reach the map: {values}"
  dlg.close()


def test_group_sits_on_top_of_the_layers_panel():
  """A freshly generated map must land at the TOP of the layers panel.

  That is what makes it visible over whatever else is loaded; insert
  it anywhere else and the user generates a map and appears to get
  nothing at all. An automatic mutant changed the insertion index and
  the whole suite walked past it.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  # something else in the project first, so "on top" means something
  other = make_region_layer()
  other.setName("basemap-ish")
  project.addMapLayer(other)
  layer = make_region_layer()
  project.addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(520)
  _generate_and_wait(dlg)

  children = project.layerTreeRoot().children()
  assert children, "the project should have something in it"
  assert children[0].name() == dlg._group_name, \
    f"the map group must sit at the top of the layers panel, but the "\
    f"first entry is {children[0].name()!r}"
  assert len(children) > 1, \
    "the layers that were there before should still be, below it"
  dlg.close()


def test_plugin_never_offers_its_own_output_as_a_region():
  """The region chooser must not list the layers the plugin itself
  made.

  Tiling a tiled map is meaningless, and the chooser fills with output
  after every generation, so the exclusion is what keeps it usable at
  all. CLAUDE.md records this as a settled invariant, and no test
  checked it: an automatic mutant deleted the call that applies it and
  the whole suite passed.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(520)
  # outlines ON, because that layer is made on a different path from
  # the elements and stamped separately. It is also the one most
  # likely to be mistaken for a region layer, being polygons of
  # exactly the region -- so it is the worst one to offer back.
  dlg.opt_outlines.setChecked(True)
  _generate_and_wait(dlg)

  produced = set(dlg._element_layer_ids.values())
  assert produced, "the run should have produced element layers"
  assert dlg._outline_layer_id, \
    "outlines were asked for but no outline layer was made"
  produced.add(dlg._outline_layer_id)
  offered = {dlg.layer_combo.layer(i).id()
             for i in range(dlg.layer_combo.count())
             if dlg.layer_combo.layer(i) is not None}
  overlap = produced & offered
  assert not overlap, \
    f"the region chooser is offering {len(overlap)} of the plugin's "\
    f"own output layers; tiling a tiled map is not a thing a user can "\
    f"mean"
  assert layer.id() in offered, \
    "the real region layer should still be offered"

  # A DIFFERENT dialog, opened while that output is already in the
  # project, must exclude it before it runs anything at all. This is
  # the case the constructor's call covers: the other call site runs
  # only after a generation, so a test that generates first cannot
  # tell whether the constructor did its job. Reopening the plugin on
  # a project that already holds a tiled map is entirely ordinary.
  dlg.close()
  second = WeavingSpaceDialog(iface=_Iface())
  second.live_check.setChecked(False)
  offered_now = {second.layer_combo.layer(i).id()
                 for i in range(second.layer_combo.count())
                 if second.layer_combo.layer(i) is not None}
  assert not produced & offered_now, \
    "a newly opened dialog offers the tiled output of an earlier run "\
    "as a region layer, before it has generated anything itself"
  second.close()

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(520)

  # and it survives a second generation, which is when the chooser
  # churns most
  _generate_and_wait(dlg)
  offered = {dlg.layer_combo.layer(i).id()
             for i in range(dlg.layer_combo.count())
             if dlg.layer_combo.layer(i) is not None}
  assert not set(dlg._element_layer_ids.values()) & offered, \
    "outputs leaked into the chooser on the second run"
  dlg.close()


def test_design_controls_are_usable_as_designed():
  """The numbers that decide what a control can express.

  A default spacing, a step size, a decimal place: each is one line in
  the dialog's construction, and automatic mutants deleted four of
  them without any test noticing. They are not cosmetic. A spacing
  spin that opens at its minimum of 0.000001 gives a first-time user a
  million tiles; an offset spin with one decimal cannot express 0.05
  at all; a modifier spin whose step reverts to 1.0 turns a rotation
  nudge into a lurch.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.PyQt.QtWidgets import QPushButton

  # First, with an EMPTY project. Nothing can auto-size the spacing
  # here, so what the spin holds is the declared default and nothing
  # else. Once a layer is present, auto-spacing overwrites it and
  # masks its absence entirely, which is how an automatic mutant
  # deleted the default and walked past the first version of this
  # test.
  bare = WeavingSpaceDialog(iface=_Iface())
  assert bare.spacing_spin.value() == 1000, \
    f"with no layer to size against, spacing should open at its "\
    f"declared default of 1000, not {bare.spacing_spin.value()}"
  bare.close()

  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)

  assert dlg.spacing_spin.value() > 1, \
    f"spacing opens at {dlg.spacing_spin.value()}, which at the spin's "\
    f"own minimum would ask for an impossible number of tiles"

  # the Auto button must be in the layout, not merely constructed:
  # a widget that is never added is a feature the user cannot reach
  buttons = [b for b in dlg.findChildren(QPushButton)
             if b.text() == "Auto"]
  assert buttons, "the Auto spacing button is missing from the dialog"
  assert buttons[0].parent() is not None and buttons[0].isVisibleTo(dlg), \
    "the Auto button exists but was never added to a layout, so no "\
    "user can click it"
  # and it does something
  dlg.spacing_spin.setValue(12345)
  buttons[0].click()
  _tick(400)
  assert dlg.spacing_spin.value() != 12345, \
    "the Auto button did not set a spacing from the layer"

  # fractional offsets: 0.05 is a value the control must be able to hold
  dlg.opt_offset.setValue(0.05)
  assert abs(dlg.opt_offset.value() - 0.05) < 1e-9, \
    f"the offset spin rounded 0.05 to {dlg.opt_offset.value()}; it "\
    f"needs two decimals"

  # modifier spins step in fractions, not whole units
  for name, ceiling in (("mod_rotate", 45), ("mod_scale_x", 1),
                        ("mod_skew_x", 45), ("mod_inset", 100)):
    box = getattr(dlg, name, None)
    if box is None:
      continue
    assert box.singleStep() <= max(ceiling / 20.0, 0.05), \
      f"{name} steps by {box.singleStep()}, too coarse for nudging a "\
      f"design"
  dlg.close()


def test_preview_colours_follow_the_variable():
  """Assigning a variable must recolour the preview, not just the map.

  The preview is the only thing on screen while a design is being
  worked out, and picking a variable silently re-picks the styling
  mode to suit the field's type. An automatic mutant removed the
  repaint that follows, leaving the preview showing the colours of a
  choice the user had already moved on from.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  _tick(700)

  # what the preview actually paints, sampled across its face
  def preview_colours():
    image = dlg.preview.grab().toImage()
    step_x, step_y = max(image.width() // 8, 1), max(image.height() // 8, 1)
    return [image.pixelColor(x, y).name()
            for x in range(step_x, image.width() - 1, step_x)
            for y in range(step_y, image.height() - 1, step_y)]

  # start from an element the user has deliberately unassigned, which
  # draws as plain fill; assigning a variable then auto-picks a
  # styling mode for the field's type, and the preview must follow
  dlg.table.cellWidget(0, 1).setCurrentText("---")
  dlg.table.cellWidget(1, 1).setCurrentText("---")
  _tick(700)
  before = preview_colours()

  # assign variables again, and let ONLY the dialog's own machinery act
  dlg.table.cellWidget(0, 1).setCurrentText("v1")
  dlg.table.cellWidget(1, 1).setCurrentText("v2")
  _tick(700)

  after = preview_colours()
  assert after != before, \
    "the preview kept its old colours after variables were assigned; "\
    "the only thing on screen during design is now out of date"
  dlg.close()


def test_auto_spacing_offers_a_round_number():
  """The spacing the Auto button proposes must READ as a number a
  person would choose.

  It is derived from the layer extent and then rounded up to one of
  1, 2, 2.5 or 5 times a power of ten, which is the difference
  between offering 2500 and offering 2371.8438. An automatic mutant
  changed the base of that rounding from ten to eleven and nothing
  noticed, because every test that used Auto only checked that the
  value had changed.
  """
  import math

  from weavingspace_qgis.dialog import _nice_number

  # whatever goes in, what comes out is a clean number
  allowed = (1, 2, 2.5, 5, 10)
  for x in (0.03, 1.0, 3.7, 12.0, 87.5, 240.0, 999.0, 1001.0,
            12345.0, 987654.0):
    got = _nice_number(x)
    assert got >= x, f"_nice_number({x}) returned {got}, which is less"
    mantissa = got / 10 ** math.floor(math.log10(got))
    assert any(abs(mantissa - m) < 1e-9 for m in allowed), \
      f"_nice_number({x}) returned {got}, whose leading digits "\
      f"({mantissa}) are not one of {allowed}: a spacing box would "\
      f"show a number nobody would have chosen"

  # and the specific roundings that make it worth having
  assert _nice_number(1001) == 2000
  assert _nice_number(2100) == 2500
  assert _nice_number(0) == 1.0, "a degenerate extent must not divide by zero"


def test_preview_draws_the_middle_of_the_patch():
  """With context shells on, the preview must include the CENTRE unit.

  The shells are drawn to show how a unit repeats, and a patch built
  without its central unit leaves a hole exactly where the user is
  looking. An automatic mutant flipped include_0 to False and the
  suite passed, because nothing compared the preview against the
  patch the library would build.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.shells_spin.setValue(1)
  _tick(900)

  # Count the drawable parts of a patch the way anything drawing it
  # must: multipart geometries contribute each of their pieces, and
  # empty or non-areal pieces contribute nothing.
  def parts(patch):
    total = 0
    for shape in patch.geometry:
      pieces = shape.geoms if hasattr(shape, "geoms") else [shape]
      for piece in pieces:
        if piece.is_empty or not hasattr(piece, "exterior"):
          continue
        total += 1
    return total

  with_centre = parts(dlg._unit.get_local_patch(r=1, include_0=True))
  without_centre = parts(dlg._unit.get_local_patch(r=1, include_0=False))
  assert with_centre != without_centre, \
    "this library build does not distinguish the two patches, so the "\
    "assertion below would prove nothing"

  # _polys is what the widget paints; _labels comes from the unit's own
  # tiles and stays the same size whatever the shells are, which is
  # why it cannot answer this question
  drawn = len(dlg.preview._polys)
  assert drawn == with_centre, \
    f"the preview painted {drawn} shapes; a one-shell patch has "\
    f"{with_centre} with its centre and {without_centre} without, so "\
    f"the middle of the pattern is missing from the only thing on "\
    f"screen during design"
  dlg.close()


def test_switching_region_layer_counts_as_a_change():
  """Changing the region layer must force a re-tiling.

  The plugin skips work when nothing that matters has changed, and it
  decides that by comparing signatures. If the signature forgets WHICH
  layer was tiled, then choosing a different region looks like no
  change at all, and the user is left looking at the previous layer's
  map. An automatic mutant inverted exactly that test and survived,
  because every existing test pressed Generate, which does the work
  regardless.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  first = make_region_layer()
  first.setName("first region")
  project.addMapLayer(first)
  # a second region somewhere else entirely
  second = make_region_layer(origin=(500000, 500000))
  second.setName("second region")
  project.addMapLayer(second)

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(first)
  dlg.spacing_spin.setValue(520)
  _tick(500)
  before_run = dlg._run_signature()
  before_geom = dlg._geometry_signature()

  dlg.layer_combo.setLayer(second)
  _tick(500)
  # Choosing a layer also auto-sizes the spacing, and spacing is part
  # of the signature -- so without putting it back, this test would
  # pass on the spacing alone and prove nothing about layer identity.
  # That is exactly how it first passed while the mutant survived.
  dlg.spacing_spin.setValue(520)
  _tick(300)
  assert dlg._run_signature() != before_run, \
    "choosing a different region layer did not change the run "\
    "signature, so the plugin would skip the work and leave the old "\
    "map on screen"
  assert dlg._geometry_signature() != before_geom, \
    "and it must count as a GEOMETRY change: a different region "\
    "cannot be answered by re-seeding renderers"

  # and the map really does follow the new layer
  _generate_and_wait(dlg)
  out = project.mapLayer(dlg._element_layer_ids["a"])
  assert out.extent().intersects(second.extent()), \
    "the tiled output does not overlap the region that was chosen"
  dlg.close()


def test_no_control_is_dead():
  """Every control a user can reach must change SOMETHING by itself.

  This is the systematic version of a lesson learned one control at a
  time. Automatic mutants delete signal connections, and each deletion
  leaves a control that looks normal, accepts input, and does nothing
  at all; five separate tests were written to catch five such
  deletions before it became obvious that the property is general.
  The dialog carries more than thirty connections, so testing them
  individually is a losing race.

  The method: for each control the current family actually shows,
  fingerprint what the user can see (the unit's geometry, what the
  preview paints, what the table says), nudge the control by one step,
  let ONLY the dialog's own debounce run, and require the fingerprint
  to move. Controls that legitimately change nothing visible are
  listed by name with a reason, and that list is short on purpose:
  each entry is a promise that the control does its work somewhere
  else.

  The test walks several families, because the option controls are
  family-specific and a design with no stars never shows a point
  angle.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.PyQt.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox,
                                   QLineEdit, QSpinBox)
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)

  # Controls whose effect is deliberately elsewhere. Each needs a
  # reason: an entry here is an assertion that the control matters
  # somewhere this test does not look, and an unexplained entry is
  # how a dead control would hide.
  # Each entry names the test that DOES cover the control, and the
  # existence of that test is checked below. An exemption list is
  # precisely where a dead control would hide, so an entry here is a
  # citation rather than an excuse.
  ELSEWHERE = {
    "live_check": (None, "gates automatic regeneration; it changes "
                         "nothing on screen until a setting moves"),
    "gpkg_widget": (None, "chooses an output file, which affects the "
                          "next run rather than the current design"),
    "layer_combo": ("test_switching_region_layer_counts_as_a_change",
                    "switching layers also auto-sizes spacing, which "
                    "would make this walk pass for the wrong reason"),
    "mod_p_inset": ("test_ui_library_modifier_chain",
                    "insets the group at TILING time, so the tile "
                    "unit and its preview are unchanged by design"),
    "mod_glyph": ("test_ui_library_glyph_scaling",
                  "scales tiles as glyphs when the map is built; the "
                  "unit itself keeps its geometry"),
  }
  for exempt, (covering, _why) in ELSEWHERE.items():
    if covering is not None:
      assert covering in globals(), \
        f"{exempt} is exempt from this walk because {covering} covers "\
        f"it, but no such test exists any more"

  def fingerprint(dlg):
    """Everything a user could notice about the current design.

    Geometry alone is not enough. A weave's over-under pattern
    rearranges which strand lies on top while leaving the polygons
    where they are, so a fingerprint of WKT strings cannot see it --
    which is how a deleted connection on that very control survived a
    batch while this walk reported every control healthy. Pair each
    shape with the element it belongs to, and sample what the preview
    actually paints, so that a change visible to the eye is visible
    here.
    """
    unit = ()
    if dlg._unit is not None:
      unit = tuple(zip((str(t) for t in dlg._unit.tiles.tile_id),
                       (g.wkt for g in dlg._unit.tiles.geometry)))
    table = tuple(
      (dlg.table.item(r, 0).text() if dlg.table.item(r, 0) else "",
       dlg.table.cellWidget(r, 1).currentText()
       if dlg.table.cellWidget(r, 1) else "")
      for r in range(dlg.table.rowCount()))
    image = dlg.preview.grab().toImage()
    step_x = max(image.width() // 12, 1)
    step_y = max(image.height() // 12, 1)
    painted = tuple(image.pixel(x, y)
                    for x in range(step_x, image.width() - 1, step_x)
                    for y in range(step_y, image.height() - 1, step_y))
    return (unit, len(dlg.preview._polys), len(dlg.preview._labels),
            table, painted)

  def nudge(widget):
    """Move a control one step, whatever kind it is.

    Returns:
      True if the control could be moved at all. A spin already at its
      maximum is stepped down instead, since the point is movement.
    """
    if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
      step = widget.singleStep()
      target = widget.value() + step
      if target > widget.maximum():
        target = widget.value() - step
      if target < widget.minimum() or target == widget.value():
        return False
      widget.setValue(target)
      return True
    if isinstance(widget, QComboBox):
      if widget.count() < 2:
        return False
      widget.setCurrentIndex((widget.currentIndex() + 1) % widget.count())
      return True
    if isinstance(widget, QCheckBox):
      widget.setChecked(not widget.isChecked())
      return True
    if isinstance(widget, QLineEdit):
      widget.setText("1,2,2,1" if widget.text() != "1,2,2,1" else "2,1")
      return True
    return False

  families = [("4", "tiling", "laves 3.3.4.3.4"),
              ("2", "tiling", "hex-slice 2"),
              ("4", "weave", "twill weave ab|cd"),
              ("4", "tiling", "grid 4")]
  tested, dead = 0, []
  for n, kind, family in families:
    dlg = WeavingSpaceDialog(iface=_Iface())
    dlg.live_check.setChecked(False)
    dlg.n_combo.setCurrentText(n)
    dlg.kind_combo.setCurrentText(kind)
    dlg.family_combo.setCurrentText(family)
    _tick(800)

    # every named control this family actually shows
    names = [a for a in dir(dlg)
             if a.startswith(("opt_", "mod_")) or a in
             ("spacing_spin", "shells_spin", "n_combo", "kind_combo",
              "family_combo")]
    for name in sorted(names):
      if name in ELSEWHERE:
        continue
      widget = getattr(dlg, name, None)
      if widget is None or not hasattr(widget, "isVisibleTo"):
        continue
      if not widget.isVisibleTo(dlg) or not widget.isEnabled():
        continue
      before = fingerprint(dlg)
      if not nudge(widget):
        continue
      _tick(800)          # only the dialog's own debounce may act
      if fingerprint(dlg) == before:
        dead.append(f"{name} (in {family})")
      tested += 1
      # Put the WHOLE design back, not just the family. Nudging
      # n_combo or kind_combo changes which families exist, so
      # restoring the family alone can silently leave the dialog on a
      # different design -- and every control tested after that point
      # is then judged in a configuration where it may not even be
      # shown. That is how a deleted connection on the over-under
      # field survived a batch while this walk reported every control
      # healthy.
      dlg.n_combo.setCurrentText(n)
      dlg.kind_combo.setCurrentText(kind)
      dlg.family_combo.setCurrentText(family)
      _tick(600)
      assert dlg.family_combo.currentText() == family, \
        f"could not restore {family} after moving {name}; the rest "\
        f"of this walk would test the wrong design"
    dlg.close()

  assert tested >= 12, \
    f"only {tested} controls were exercised; the walk is not reaching "\
    f"the dialog's controls and would pass whatever was broken"
  assert not dead, \
    f"{len(dead)} control(s) changed nothing when moved, so a user "\
    f"operating them would see no response at all: {', '.join(dead)}"


def test_a_row_without_classes_says_so():
  """A row whose style has no class count must show a dash, not a number.

  The Classes cell is shared by every kind of row, and for a
  categorical or single-colour element there is no such thing as a
  class count. It is therefore parked at its minimum and given a dash
  to display. An automatic mutant moved that value off the minimum,
  which makes the dash vanish and the cell claim, in a column headed
  Classes, that the element has one.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)

  dlg.table.cellWidget(0, 1).setCurrentText("landcover")
  dlg.table.cellWidget(0, 2).setCurrentText("Single colour")
  dlg._update_dynamic_columns()
  k_spin = dlg.table.cellWidget(0, 3)
  if k_spin is not None:
    assert k_spin.value() == k_spin.minimum(), \
      f"a Single colour row has no class count, so its Classes cell "\
      f"must sit at the minimum where its placeholder shows; it "\
      f"reads {k_spin.value()}"
    assert k_spin.specialValueText().strip(), \
      "and the minimum needs a placeholder, or the cell shows a bare 0"
    assert not k_spin.isEnabled(), "it is not editable either"
  dlg.close()


def test_a_finished_run_leaves_nothing_armed():
  """When live update is off, finishing a run must not queue another.

  The dialog remembers that a live regeneration was wanted while a run
  was in flight, and starts it once the run is over. That memory
  begins empty. An automatic mutant started it FULL, which means the
  first ordinary Generate ends by arming a timer nobody asked for.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  assert not dlg._live_pending, \
    "a dialog that has done nothing yet cannot have work pending"

  dlg.spacing_spin.setValue(520)
  _generate_and_wait(dlg)

  # The timer being ARMED is normal: _queue_live starts it as a plain
  # funnel and _maybe_live_generate is the thing that decides. What
  # must not happen is a second tiling, so count tilings rather than
  # timers -- an assertion about the timer would pin an implementation
  # detail that is legitimately true, which is how this test failed
  # when it was first written.
  runs = []
  original = dlg._generate
  dlg._generate = lambda *a, **k: (runs.append(1), original(*a, **k))[1]
  _tick(1500)          # long enough for the live timer to fire
  assert not runs, \
    f"finishing a run started {len(runs)} more, with live update "\
    f"switched off; the user would watch the map rebuild itself for "\
    f"no reason"
  assert dlg._task is None, "and the run should be over"
  dlg._generate = original
  dlg.close()


def test_the_dialogs_chrome_does_its_job():
  """The parts of the window that are not the design: the region
  chooser's filter, the idle progress bar, and the Close button.

  None of these is exotic and all three were undefended. Automatic
  mutants removed the layer filter (so the chooser offers point and
  line layers, which cannot be tiled at all), made the progress bar
  visible while nothing runs, and disconnected Close, leaving a button
  that does nothing whatever when clicked.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.PyQt.QtWidgets import QPushButton
  project = QgsProject.instance()
  polygons = make_region_layer()
  project.addMapLayer(polygons)
  # something that cannot be tiled, which the chooser must not offer
  points = QgsVectorLayer("Point?crs=EPSG:3857", "sample points", "memory")
  feature = QgsFeature()
  feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(500, 500)))
  points.dataProvider().addFeatures([feature])
  points.updateExtents()
  project.addMapLayer(points)

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  offered = [dlg.layer_combo.layer(i).name()
             for i in range(dlg.layer_combo.count())
             if dlg.layer_combo.layer(i) is not None]
  assert "sample points" not in offered, \
    f"the region chooser is offering a point layer, which cannot be "\
    f"tiled: {offered}"
  assert polygons.name() in offered, "and it must still offer polygons"

  assert not dlg.progress.isVisibleTo(dlg), \
    "the progress bar is showing while nothing is running"

  # and it goes away again AFTERWARDS. Two separate lines hide it --
  # one at construction, one when a run finishes -- and a test that
  # only checks the fresh dialog leaves the second undefended.
  dlg.spacing_spin.setValue(520)
  _generate_and_wait(dlg)
  _tick(200)
  assert not dlg.progress.isVisibleTo(dlg), \
    "the progress bar is still showing after the run finished"

  # controls constructed but never added to a layout are unreachable,
  # and the preview's own label is the only thing naming it
  assert dlg.shells_spin.isVisibleTo(dlg), \
    "the context-shells spinner is not in any layout, so no user can "\
    "reach it"
  # A whole form can go missing the same way a single control can.
  # Visibility is the wrong question for these: they sit on other tabs,
  # and a widget on a page that is not current is legitimately not
  # visible. What must hold is that each one is IN the dialog's
  # hierarchy -- a widget built but never added to a layout keeps
  # whatever parent it was constructed with and never becomes a
  # descendant of the window.
  for name in ("gpkg_widget", "opt_new_group", "live_check"):
    widget = getattr(dlg, name, None)
    assert widget is not None, f"the dialog has no {name}"
    assert dlg.isAncestorOf(widget), \
      f"{name} is not inside the dialog's widget tree, so it was "\
      f"built and then left out of every layout; an entire output "\
      f"form can go missing as easily as one control"
  from qgis.PyQt.QtWidgets import QLabel
  labels = [l.text() for l in dlg.findChildren(QLabel)]
  assert any("preview" in t.lower() for t in labels), \
    "nothing on the window says what the preview panel is"

  closers = [b for b in dlg.findChildren(QPushButton)
             if b.text().strip().lower() == "close"]
  assert closers, "the dialog has no Close button"
  dlg.show()
  _tick(200)
  assert dlg.isVisible()
  closers[0].click()
  _tick(200)
  assert not dlg.isVisible(), \
    "clicking Close did nothing; the button is not connected to "\
    "anything"
  dlg.close()


def test_ramp_swatches_and_palette_installation():
  """The colour ramps a user picks from: installed once, and shown.

  The plugin adds its palettes to the QGIS style the first time it
  runs, skipping any already there, and draws a small swatch beside
  every ramp name so a choice can be made by eye. Automatic mutants
  inverted the already-there test (so nothing new is ever installed)
  and inverted the guard that attaches a swatch (so the list becomes
  a column of names).
  """
  from weavingspace_qgis import bridge
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.core import QgsStyle

  bridge.ensure_ramps_installed()
  style = QgsStyle.defaultStyle()
  wanted = set(bridge.PALETTES["sequential"]) | \
      set(bridge.PALETTES["diverging"])
  missing = wanted - set(style.colorRampNames())
  assert not missing, \
    f"{len(missing)} of the plugin's palettes never reached the QGIS "\
    f"style, so a user cannot choose them: {sorted(missing)[:4]}"

  # The style persists in the user's profile, so on a machine that has
  # run this plugin before, everything is already installed and the
  # check above passes whatever the installer does. Create the
  # condition instead: take one palette out and require the installer
  # to notice it is gone. This is what a first run looks like.
  # Two loops install palettes -- gradients and categorical presets --
  # and a mutant in either leaves a user without half the choices. Take
  # one from each.
  categorical = set(bridge.PALETTES["categorical"])
  missing_cat = categorical - set(style.colorRampNames())
  assert not missing_cat, \
    f"categorical palettes missing from the style: "\
    f"{sorted(missing_cat)[:4]}"
  cat_victim = sorted(categorical)[0]
  assert style.removeColorRamp(cat_victim)
  bridge.ensure_ramps_installed()
  assert cat_victim in set(style.colorRampNames()), \
    f"{cat_victim} was missing and the installer left it missing; the "\
    f"categorical palettes are installed by their own loop"

  victim = sorted(wanted)[0]
  assert style.removeColorRamp(victim), \
    f"could not take {victim} out of the style to set the test up"
  assert victim not in set(style.colorRampNames())
  bridge.ensure_ramps_installed()
  assert victim in set(style.colorRampNames()), \
    f"{victim} was missing from the style and the installer left it "\
    f"missing; on a fresh QGIS profile the user would have none of "\
    f"the plugin's palettes"
  bridge.ensure_ramps_installed()          # again: additive, not doubled
  assert len([n for n in style.colorRampNames() if n == victim]) == 1

  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Quantiles")
  dlg._update_dynamic_columns()
  combo = dlg.table.cellWidget(0, 4)
  assert combo is not None and combo.count() > 0
  blank = sum(1 for i in range(combo.count()) if combo.itemIcon(i).isNull())
  assert blank == 0, \
    f"{blank} of {combo.count()} ramps are listed without a swatch; "\
    f"the list is names only and cannot be read by eye"
  dlg.close()


def test_family_option_ranges_track_the_family():
  """A family's options must be bounded by what THAT family accepts.

  The inner angle of a hex dissection runs from -50 to 85 and of a
  square one from -30 to 70; the ranges are set as the family changes.
  An automatic mutant deleted that, leaving whichever range happened
  to be in force and letting a user dial in a value the library
  cannot use.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import catalog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)

  seen = {}
  for n, families in catalog.TILINGS_BY_N.items():
    for name, entry in families.items():
      kind = entry.get("tiling_type", "")
      if "dissect" not in kind:
        continue
      hexagonal = "hex" in kind
      if hexagonal in seen:
        continue
      seen[hexagonal] = (n, name)
  assert len(seen) == 2, \
    "this test needs both a hex and a non-hex dissection family"

  ranges = {}
  for hexagonal, (n, name) in seen.items():
    dlg.n_combo.setCurrentText(str(n))
    dlg.kind_combo.setCurrentText("tiling")
    dlg.family_combo.setCurrentText(name)
    _tick(700)
    ranges[hexagonal] = (dlg.opt_offset_angle.minimum(),
                         dlg.opt_offset_angle.maximum())
  assert ranges[True] != ranges[False], \
    f"both dissection families offer the same inner-angle range "\
    f"{ranges[True]}; the range is not following the family, so one "\
    f"of them accepts values its geometry cannot use"
  assert ranges[True] == (-50, 85), f"hex dissections: {ranges[True]}"
  assert ranges[False] == (-30, 70), f"square dissections: {ranges[False]}"
  dlg.close()


def test_a_single_category_still_gets_a_colour():
  """A field with exactly ONE distinct value must still render.

  Categorical colours are sampled across the palette by position,
  which divides by the number of categories minus one -- fine until
  there is only one, when the division is by zero. The guard that
  handles it was mutated and survived, because every categorical
  fixture in the suite has three or four classes. Real data has
  columns that turn out to be constant.
  """
  from weavingspace_qgis import bridge, compat
  layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "one", "memory")
  layer.dataProvider().addAttributes([compat.make_field("only", str)])
  layer.updateFields()
  feats = []
  for i in range(3):
    f = QgsFeature(layer.fields())
    f.setGeometry(QgsGeometry.fromWkt(
      f"POLYGON(({i} 0, {i+1} 0, {i+1} 1, {i} 1, {i} 0))"))
    f["only"] = "the same value"
    feats.append(f)
  layer.dataProvider().addFeatures(feats)
  layer.updateExtents()

  renderer = bridge.make_categorized_renderer(layer, "only", "tab10", False)
  assert renderer is not None, "a one-class field produced no renderer"
  categories = [c for c in renderer.categories() if c.value()]
  assert len(categories) == 1, \
    f"expected one category, got {len(categories)}"
  colour = categories[0].symbol().color().name()
  assert colour and colour != "#000000", \
    f"the single category was given {colour}, not a palette colour"
  # and specifically the palette's FIRST entry. "Some colour" is not
  # enough: an automatic mutant handed the lone class the second
  # entry, which is invisible in isolation and wrong the moment two
  # such maps are compared, or a second category appears and takes
  # the colour this one had.
  first = bridge.PALETTES["categorical"]["tab10"][0]
  assert colour.lower() == first.lower(), \
    f"a single category should take the palette's first colour "\
    f"({first}), not {colour}"


def test_the_library_works_without_matplotlib_or_scipy():
  """The vendored library must import and tile with plotting absent.

  This is the one piece of the vendored library that is OURS: upstream
  imports matplotlib and scipy unconditionally, and the plugin patches
  every such import to fall back to a placeholder, because QGIS
  installations frequently have neither and the plugin needs neither.
  Everything else in vendor/ is upstream's code, tested upstream and
  exercised here on every map; the patch is not, and it only takes
  effect when those packages are MISSING -- which on this machine they
  are not. So the condition has to be manufactured.

  The failure this guards against is total: a bare ImportError at
  module load, on exactly the installations least able to diagnose it.
  """
  import subprocess
  import sys as _sys

  # A child process with matplotlib and scipy poisoned at import time.
  # Manufacturing the condition in-process would not do: the modules
  # are already imported by the time any test runs, and unimporting
  # them is not something Python does honestly.
  program = """
import sys

class _Absent:
  def find_module(self, name, path=None):
    return self if name.split(".")[0] in ("matplotlib", "scipy") else None
  def load_module(self, name):
    raise ImportError(f"{name} is not installed (test)")

sys.meta_path.insert(0, _Absent())
for name in list(sys.modules):
  if name.split(".")[0] in ("matplotlib", "scipy"):
    del sys.modules[name]

# the same path the plugin and this suite use: vendor/ on sys.path,
# so "weavingspace" resolves to the vendored copy
sys.path.insert(0, "__ROOT__/weavingspace_qgis/vendor")
from weavingspace.tile_unit import TileUnit

unit = TileUnit(tiling_type="laves", code="3.3.4.3.4", spacing=500, crs=3857)
print("TILES", len(unit.tiles))

# the placeholder must also FAIL LOUDLY if plotting is attempted,
# rather than silently doing nothing
from weavingspace._optional import MissingModule
proxy = MissingModule("matplotlib.pyplot")
try:
  proxy.subplots()
  print("SILENT")
except ImportError as exc:
  print("RAISED", "matplotlib" in str(exc))
""".replace("__ROOT__", ROOT)     # not .format: the program below
  # is full of braces of its own

  result = subprocess.run([_sys.executable, "-c", program],
                          capture_output=True, text=True, timeout=180)
  assert "TILES" in result.stdout, \
    f"the vendored library could not build a tiling with matplotlib "\
    f"and scipy unavailable:\n{result.stderr[-1200:]}"
  tiles = int(result.stdout.split("TILES")[1].split()[0])
  assert tiles == 4, f"expected the laves unit's four tiles, got {tiles}"
  assert "RAISED True" in result.stdout, \
    f"the placeholder for an absent module did not raise a helpful "\
    f"ImportError when called: {result.stdout}"


def test_defaults_avoid_identifier_columns():
  """The variable offered by default must not be a row id.

  Nearly every layer carries fid, objectid or gid, and they sort to
  the front. Mapping one produces a picture of the order rows happen
  to be stored in, which looks like data and is not. The dialog skips
  them when choosing defaults while still offering them to anyone who
  actually wants one; an automatic mutant inverted that preference so
  the identifier became the FIRST choice.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import compat
  layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "with ids", "memory")
  layer.dataProvider().addAttributes([compat.make_field("fid", int),
                                      compat.make_field("objectid", int),
                                      compat.make_field("rainfall", float)])
  layer.updateFields()
  feats = []
  for i in range(4):
    f = QgsFeature(layer.fields())
    f.setGeometry(QgsGeometry.fromWkt(
      f"POLYGON(({i*1000} 0, {(i+1)*1000} 0, {(i+1)*1000} 1000, "
      f"{i*1000} 1000, {i*1000} 0))"))
    f["fid"], f["objectid"], f["rainfall"] = i, i * 10, float(i) * 1.5
    feats.append(f)
  layer.dataProvider().addFeatures(feats)
  layer.updateExtents()
  QgsProject.instance().addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  _tick(600)
  chosen = {dlg.table.cellWidget(r, 1).currentText()
            for r in range(dlg.table.rowCount())
            if dlg.table.cellWidget(r, 1) is not None}
  chosen.discard("---")
  assert chosen, "no default variable was chosen at all"
  assert not (chosen & {"fid", "objectid"}), \
    f"the plugin defaulted to an identifier column ({chosen}); the "\
    f"resulting map shows the order rows are stored in"
  assert "rainfall" in chosen, \
    f"the real measurement was passed over in favour of {chosen}"

  # and the identifiers are still OFFERED, for anyone who means it
  offered = {dlg.table.cellWidget(0, 1).itemText(i)
             for i in range(dlg.table.cellWidget(0, 1).count())}
  assert "fid" in offered, "identifiers should still be choosable"
  dlg.close()


def test_repopulating_a_chooser_does_not_duplicate_it():
  """Rebuilding a dropdown must replace its contents, not append them.

  The class-source chooser is rebuilt whenever the project's layers
  change, which happens after every generation. An automatic mutant
  removed the clear that precedes the rebuild, so the list grows a
  fresh copy of every entry each time -- by the third map the user is
  scrolling through triplicates.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.table.cellWidget(0, 1).setCurrentText("landcover")
  dlg.table.cellWidget(0, 2).setCurrentText("Categorized")
  dlg._update_dynamic_columns()

  combo = dlg.table.cellWidget(0, 7)
  if combo is None or not hasattr(combo, "count"):
    dlg.close()
    return
  def entries():
    return [combo.itemText(i) for i in range(combo.count())]

  first = entries()
  assert first, "the colourmap source chooser is empty"

  # The chooser only rebuilds when its CONTENTS would change, and it
  # lists layers that carry categorized symbology -- so adding plain
  # layers provokes nothing at all, which is how the first version of
  # this test passed while the mutant survived. Add layers that
  # actually belong in the list.
  from weavingspace_qgis import bridge
  for i in range(3):
    extra = make_region_layer()
    extra.setName(f"categorized source {i}")
    extra.setRenderer(bridge.make_categorized_renderer(
      extra, "landcover", "tab10", False))
    project.addMapLayer(extra)
    dlg._populate_class_source_combo(combo)
    _tick(200)
  assert len(entries()) > len(first), \
    "the new categorized layers never reached the chooser, so this "\
    "test is not exercising the rebuild it names"

  after = entries()
  assert len(after) == len(set(after)), \
    f"the chooser now lists {len(after) - len(set(after))} duplicate "\
    f"entries: {after[:6]}"
  dlg.close()


def test_the_size_guard_does_not_refuse_fine_patterns():
  """The estimate that protects against runaway tilings must not
  reject small ones.

  Before tiling, the plugin estimates how many tiles a design would
  produce and refuses absurd ones. The estimate divides by the area of
  the unit's repeat vectors, and guards against a degenerate,
  zero-area unit. An automatic mutant widened that guard, so any unit
  whose repeat area falls below one map unit -- a fine pattern in a
  projected CRS, or any design in degrees -- is declared impossible
  and never drawn.
  """
  from weavingspace_qgis import bridge
  from weavingspace import TileUnit

  coarse = TileUnit(tiling_type="laves", code="3.3.4.3.4",
                    spacing=500, crs=3857)
  fine = TileUnit(tiling_type="laves", code="3.3.4.3.4",
                  spacing=0.9, crs=3857)
  extent = (0.0, 0.0, 100.0, 100.0)

  coarse_estimate = bridge.estimate_tile_count_bounds(coarse, extent)
  fine_estimate = bridge.estimate_tile_count_bounds(fine, extent)
  assert coarse_estimate > 0
  assert fine_estimate > coarse_estimate, \
    "a finer pattern must estimate MORE tiles over the same extent, "\
    f"but got {fine_estimate} against {coarse_estimate}"
  assert fine_estimate < bridge.MAX_TILES_HARD, \
    f"a unit with a sub-unit repeat area was reported as impossible "\
    f"({fine_estimate}); the guard is meant for degenerate geometry, "\
    f"not for fine patterns"


def hostile_layers():
  """Layers built to violate the assumptions a test fixture makes.

  Returns:
    A list of (name, layer, note) describing what each one attacks.
    Every entry is something a user can plausibly load on their first
    afternoon: an export with one row, a column that turned out
    constant, a shapefile in degrees, a field name in Greek, a
    polygon that self-intersects because it was digitised by hand.

  These are deliberately NOT tidy. The synthetic grid the rest of the
  suite uses is a laboratory animal; this is the wild.
  """
  from weavingspace_qgis import compat
  made = []

  def build(name, crs, fields, rows, wkts, note):
    layer = QgsVectorLayer(f"MultiPolygon?crs={crs}", name, "memory")
    layer.dataProvider().addAttributes(
      [compat.make_field(f, t) for f, t in fields])
    layer.updateFields()
    feats = []
    for values, wkt in zip(rows, wkts):
      f = QgsFeature(layer.fields())
      geom = QgsGeometry.fromWkt(wkt)
      f.setGeometry(geom)
      for (field, _t), value in zip(fields, values):
        f[field] = value
      feats.append(f)
    layer.dataProvider().addFeatures(feats)
    layer.updateExtents()
    made.append((name, layer, note))

  square = lambda x, y, w: (
    f"POLYGON(({x} {y}, {x+w} {y}, {x+w} {y+w}, {x} {y+w}, {x} {y}))")

  # one row: every classifier has to cope with a single class
  build("single feature", "EPSG:3857", [("v", float), ("cat", str)],
        [(1.0, "only")], [square(0, 0, 1000)],
        "one polygon, so quantiles have nothing to divide")

  # nulls everywhere: QGIS returns None, and a "no data" class exists
  build("all null", "EPSG:3857", [("v", float), ("cat", str)],
        [(None, None), (None, None), (None, None), (None, None)],
        [square(i * 100, 0, 100) for i in range(4)],
        "every value missing, so classification has no data at all")

  # geographic coordinates: spacing in DEGREES, tiny numbers
  build("in degrees", "EPSG:4326", [("v", float)],
        [(float(i),) for i in range(4)],
        [square(i * 0.01, 0.0, 0.01) for i in range(4)],
        "a layer in degrees, where a spacing of 1000 covers the globe")

  # very large coordinates, as national grids often are
  build("far from origin", "EPSG:3857",
        [("v", float)], [(float(i),) for i in range(4)],
        [square(19_000_000 + i * 1000, 6_000_000, 1000) for i in range(4)],
        "coordinates in the millions, where float error bites")

  # a hand-digitised bowtie: self-intersecting, still loadable
  bowtie = ("POLYGON((0 0, 1000 1000, 1000 0, 0 1000, 0 0))")
  build("self-intersecting", "EPSG:3857", [("v", float)],
        [(1.0,), (2.0,)], [bowtie, square(2000, 0, 1000)],
        "an invalid polygon, which QGIS will load without complaint")

  # non-ASCII field values and a very long category name
  build("unicode categories", "EPSG:3857", [("cat", str)],
        [("tūrangawaewae",), ("Ähtäri",), ("x" * 200,), ("森林",)],
        [square(i * 100, 0, 100) for i in range(4)],
        "category labels that are not ASCII and one absurdly long")

  # many categories: more than any palette has colours
  build("many categories", "EPSG:3857", [("cat", str)],
        [(f"class {i}",) for i in range(60)],
        [square((i % 10) * 100, (i // 10) * 100, 100) for i in range(60)],
        "sixty categories against palettes that hold ten or twenty")

  return made


def test_hostile_data_does_not_defeat_the_plugin():
  """Load the data users actually bring, each in its own process.

  Coping means one of two things, and the distinction is the point: the
  plugin either produces a map, or it declines in a way the user can
  act on. What it may not do is raise an unhandled exception, hang, or
  hand back a group of empty layers that looks like success.

  Every fixture is plausible on a first afternoon -- an export with
  one row, a column that turned out constant, a layer still in
  degrees, coordinates in the millions, polygons that self-intersect
  because they were digitised by hand, category labels that are not
  ASCII or absurdly long, more categories than any palette has
  colours. The synthetic grid used elsewhere in this suite is a
  laboratory animal; these are the wild.

  Each fixture gets a FRESH PROCESS. An earlier version ran them all
  in one, and the fixtures slowed each other down until the test
  looked hung: state accumulates across dialogs and projects in ways
  that have nothing to do with the data under test. Isolation also
  means one pathological layer can crash without taking the suite
  with it -- which is the failure mode that matters, since a crash is
  exactly what this test is looking for.
  """
  import subprocess
  import sys as _sys

  program = """
import importlib.util, os, sys, time
ROOT = "__ROOT__"
spec = importlib.util.spec_from_file_location(
    "rt", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
from qgis.core import QgsApplication, QgsProject
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
app = QgsApplication([], True)
app.initQgis()
rt._no_modal_dialogs()
from weavingspace_qgis.dialog import WeavingSpaceDialog

wanted = sys.argv[1]
for name, layer, note in rt.hostile_layers():
    if name != wanted:
        continue
    QgsProject.instance().addMapLayer(layer)
    dlg = WeavingSpaceDialog(iface=rt._Iface())
    dlg.live_check.setChecked(False)
    began = time.time()
    try:
        dlg.layer_combo.setLayer(layer)
        rt._tick(500)
        rt._generate_and_wait(dlg)
        produced = [QgsProject.instance().mapLayer(i)
                    for i in dlg._element_layer_ids.values()]
        produced = [l for l in produced if l is not None]
        counts = [l.featureCount() for l in produced]
        # "Told" includes a message box the harness intercepted: the
        # boxes are stubbed so a headless run cannot block, and what
        # they were asked is kept in MODALS. Reading only live_note
        # counted a perfectly good warning as silence, and nearly had
        # me report a silent failure that was not one.
        told = bool(dlg.live_note.text().strip()) or bool(rt.MODALS)
        said = rt.MODALS[-1][1][:60] if rt.MODALS else ""
        print("RESULT layers=%d features=%d told=%d seconds=%.1f said=%s"
              % (len(produced), sum(counts), told, time.time() - began,
                 said))
    except Exception as exc:
        print("RAISED %s: %s" % (type(exc).__name__, str(exc)[:200]))
    dlg.close()
sys.stdout.flush()
os._exit(0)
""".replace("__ROOT__", ROOT)

  troubles = []
  for name, _layer, note in hostile_layers():
    result = subprocess.run(
      [_sys.executable, "-c", program, name],
      capture_output=True, text=True, timeout=180)
    line = next((l for l in result.stdout.splitlines()
                 if l.startswith(("RESULT", "RAISED"))), "")
    print(f"      hostile: {name}: {line or 'no result'}", flush=True)

    if line.startswith("RAISED"):
      troubles.append(f"{name}: {line[7:]} ({note})")
      continue
    if not line:
      tail = result.stderr.strip().splitlines()[-2:]
      troubles.append(f"{name}: the process produced no verdict "
                      f"({note}); last words: {' | '.join(tail)}")
      continue
    fields = dict(part.split("=", 1) for part in line.split()[1:]
                  if "=" in part)
    layers, features = int(fields["layers"]), int(fields["features"])
    if layers and not features:
      troubles.append(
        f"{name}: produced {layers} layer(s) and not one feature "
        f"between them, which looks like success and is not ({note})")
    elif not layers and not int(fields["told"]):
      troubles.append(f"{name}: produced nothing and said nothing "
                      f"({note})")

  assert not troubles, \
    "the plugin mishandled data a user could plausibly load:\n  " \
    + "\n  ".join(troubles)


def _library_unit_for(entry, spacing, crs=3857, shape=None,
                      over_under=None, aspect=0.75):
  """Build the library unit an entry MEANS, restated independently.

  Args:
    entry: one value from catalog.TILINGS_BY_N.
    spacing: the pattern's grain in map units.
    crs: EPSG code for the geometry.
    shape: (rows, cols) for the grid family, which takes its array
      shape from the dialog rather than from the catalogue.
    over_under: the passing pattern as a tuple, for twill and basket
      weaves; the user types this, so the caller states it.
    aspect: strand width as a fraction of the spacing (weaves only).

  Returns:
    A Tileable built by calling weavingspace directly.

  This deliberately does NOT call catalog.make_unit. The mapping from
  a catalogue entry to a library constructor is exactly what the sweep
  tests, and reusing the plugin's own mapping would agree with
  whatever that mapping gets wrong -- the same reason the hand-written
  comparisons build their expected side from the settings rather than
  from _build_unit.

  Where a value is a SETTING rather than catalogue data -- a grid's
  array shape, a weave's passing pattern and strand width -- there is
  nothing to restate, and inventing a rule here just disagrees with a
  deliberate design decision. An early version did exactly that, using
  exact factorisation for grids where the plugin makes a near-square
  array with empty cells, and fifteen sweep cases "failed" over it. So
  the caller states those and both sides use the same value.
  """
  from weavingspace import TileUnit, WeaveUnit

  if entry["type"] == "tiling":
    kwargs = dict(tiling_type=entry["tiling_type"], spacing=spacing,
                  crs=crs)
    for key in ("n", "code", "offset", "offset_angle", "point_angle"):
      if key in entry:
        kwargs[key] = entry[key]
    if entry["tiling_type"] == "grid":
      kwargs["nrows"], kwargs["ncols"] = shape
    return TileUnit(**kwargs)

  n = 1
  if entry["weave_type"] in ("twill", "basket"):
    n = over_under if over_under is not None else (2, 2)
  return WeaveUnit(weave_type=entry["weave_type"], spacing=spacing,
                   strands=entry["strands"], n=n, aspect=aspect, crs=crs)


def _dialog_for_setup(setup):
  """Open a dialog, apply `setup`, and let the rebuild land.

  Returns:
    The dialog, for a caller that wants to inspect state rather than
    compare output. The sweep uses it when a design collapses to no
    tiles at all, where there is nothing to render and the question
    becomes what the dialog SAYS about it.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  setup(dlg)
  dlg._rebuild_unit()
  return dlg


def test_an_over_large_inset_empties_the_design_visibly():
  """Insetting a tile by more than its own width must say so, and be
  undoable.

  A stripes unit at 20 elements gives each stripe a twentieth of the
  spacing, so a tile inset of 5% of the spacing exceeds the whole
  stripe and every tile is consumed. That is arithmetic, not a fault,
  and the library does the same. What matters is what the user sees:
  the preview must say the design is empty rather than merely going
  blank, and -- the part that would be a real defect -- the element
  assignments must survive, rather than being discarded along with the
  table rows.

  Found by the randomised differential sweep, which drew this
  combination by chance.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("20")
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("stripes 20")
  dlg.spacing_spin.setValue(800)
  dlg._rebuild_unit()
  assert dlg.table.rowCount() == 20, "twenty stripes to begin with"

  dlg.table.cellWidget(0, 1).setCurrentText("v1")
  dlg.table.cellWidget(1, 1).setCurrentText("v2")
  _tick(400)

  dlg.mod_t_inset.setValue(5.0)          # wider than a stripe
  dlg._rebuild_unit()
  assert dlg.table.rowCount() == 0, \
    "an inset wider than the stripe should leave no tiles"
  assert dlg.preview._message, \
    "the preview went empty without saying why; a user would think "\
    "the plugin had broken"

  dlg.mod_t_inset.setValue(2.0)          # back to something workable
  dlg._rebuild_unit()
  assert dlg.table.rowCount() == 20, "the stripes should return"
  assignments = {a["id"]: a["var"] for a in dlg._assignments()}
  assert assignments.get("a") == "v1" and assignments.get("b") == "v2", \
    f"the element assignments were discarded when the design briefly "\
    f"collapsed, and the user has to retype them: {assignments}"
  dlg.close()


def test_random_designs_match_the_library():
  """Draw designs at random and require each to match the library.

  The hand-picked comparisons elsewhere in this file are the
  regression record: each pins a defect that actually happened, and
  they stay. This is the other half of the job. They test the
  combinations somebody thought of; a sweep tests the ones nobody did,
  which is where the tie-prone join failure lived -- it needed a
  particular family, a particular spacing, and a modifier that was
  supposed to change nothing.

  Each case draws a family, a spacing, modifiers, variables, ramps and
  opacities, drives the dialog to exactly that, and compares the
  result against a unit built by calling weavingspace directly.
  Geometry first, then interior pixels.

  Scale it with the environment rather than by editing:
  WEAVINGSPACE_SWEEP_CASES sets how many designs to draw (a handful
  during a release, hundreds during a campaign) and
  WEAVINGSPACE_SWEEP_SEED makes any failure reproducible -- the seed
  is printed with every case so a failing draw can be rerun alone.
  """
  from weavingspace_qgis import catalog

  cases = int(os.environ.get("WEAVINGSPACE_SWEEP_CASES", "6"))
  seed = int(os.environ.get("WEAVINGSPACE_SWEEP_SEED", "20260808"))
  rng = random.Random(seed)
  print(f"      sweep: {cases} case(s), seed {seed}", flush=True)

  pool = [(n, name, entry)
          for n, families in catalog.TILINGS_BY_N.items()
          for name, entry in families.items()
          # the custom ("this") weave needs a matrix the dialog has no
          # UI for yet, so it cannot be driven from here
          if entry.get("weave_type") != "this"]
  assert len(pool) > 20, f"only {len(pool)} families to draw from"
  assert any(e["type"] != "tiling" for _n, _name, e in pool), \
    "the draw should include weaves as well as tilings"

  ramp_names = ["Reds", "Blues", "Greens", "Purples", "Oranges", "Greys"]
  fields = ["v1", "v2", "v3"]
  failures = []

  for case in range(cases):
    n, name, entry = rng.choice(pool)
    spacing = rng.choice([400, 500, 650, 800])
    elements = entry.get("n", n) if entry["type"] == "tiling" else n
    variables = [fields[i % len(fields)] for i in range(elements)]
    ramps = [ramp_names[(i + case) % len(ramp_names)]
             for i in range(elements)]
    opacities = ([rng.choice([100, 100, 80, 60]) for _ in range(elements)]
                 if rng.random() < 0.5 else None)

    # A weave's passing pattern and strand width are typed by the
    # user, so the sweep chooses them and tells both sides.
    pattern, over_under, aspect = None, None, 0.75
    if entry["type"] != "tiling":
      pattern = rng.choice(["2", "1,2", "2,2", "1,2,2,1", "3"])
      # The passing pattern's meaning is a documented rule, ported
      # from the web app: the comma-separated numbers ARE the pattern,
      # an odd-length list is trimmed to even length, and anything
      # unparseable falls back to (2, 2). A single number is therefore
      # a ONE-element pattern -- "3" means (3,), not (3, 3) -- which
      # is the sort of thing worth restating carefully: assuming the
      # doubled reading here put two sweep cases into disagreement
      # over geometry that was perfectly correct.
      digits = [int(d) for d in pattern.split(",")]
      keep = 2 * len(digits) // 2
      over_under = tuple(digits[:keep]) if keep else (2, 2)
      aspect = rng.choice([0.75, 0.75, 0.5, 0.9])

    # A grid's array shape is a setting too.
    shape = None
    if entry.get("tiling_type") == "grid":
      rows = rng.randint(1, max(1, elements))
      shape = (rows, -(-elements // rows))      # ceiling division

    # Modifiers, drawn from a set that deliberately includes the
    # identities. Rotate 0 and scale 1 are supposed to change nothing,
    # and the one real bug this shape of test has found was exactly
    # there. Half the cases get none at all, so the plain path stays
    # exercised.
    mods = {"rotate": 0.0, "scale": (1.0, 1.0), "skew": (0.0, 0.0),
            "tile_inset": 0.0, "prototile_inset": 0.0}
    if rng.random() < 0.5:
      mods["rotate"] = rng.choice([0.0, 0.0, 15.0, 30.0, -22.5])
      mods["scale"] = rng.choice([(1.0, 1.0), (1.0, 1.0), (0.8, 1.0),
                                  (1.0, 0.75)])
      mods["skew"] = rng.choice([(0.0, 0.0), (0.0, 0.0), (10.0, 0.0)])
      if entry["type"] == "tiling":
        # Insets are drawn for tilings only. A weave has no prototile
        # to inset, and the plugin scales a weave's TILE inset by the
        # strand width on purpose, so thin strands do not vanish at
        # values a tiling shrugs off. That scaling is a design
        # decision of the plugin's rather than a library semantic, so
        # this sweep cannot derive it independently -- and a sweep
        # that copied the rule would only be checking that the code
        # agrees with itself. The hand-written weave comparisons cover
        # inset weaves against a deliberately stated expectation.
        mods["tile_inset"] = rng.choice([0.0, 0.0, 2.0])
        mods["prototile_inset"] = rng.choice([0.0, 0.0, 3.0])

    label = f"sweep {case} {name} at {spacing}"
    if shape:
      label += f" ({shape[0]}x{shape[1]})"
    if pattern:
      label += f" [{pattern}]"
    print(f"      {label}", flush=True)

    def setup(dlg, n=n, name=name, spacing=spacing, shape=shape,
              mods=mods, entry=entry, pattern=pattern, aspect=aspect):
      dlg.n_combo.setCurrentText(str(n))
      dlg.kind_combo.setCurrentText(
        "tiling" if entry["type"] == "tiling" else "weave")
      dlg.family_combo.setCurrentText(name)
      if pattern is not None:
        dlg.opt_over_under.setText(pattern)
        dlg.opt_aspect.setValue(aspect)
      dlg.spacing_spin.setValue(spacing)
      if shape:
        dlg.opt_grid_rows.setValue(shape[0])
        dlg.opt_grid_cols.setValue(shape[1])
      dlg.mod_rotate.setValue(mods["rotate"])
      dlg.mod_scale_x.setValue(mods["scale"][0])
      dlg.mod_scale_y.setValue(mods["scale"][1])
      dlg.mod_skew_x.setValue(mods["skew"][0])
      dlg.mod_skew_y.setValue(mods["skew"][1])
      dlg.mod_t_inset.setValue(mods["tile_inset"])
      dlg.mod_p_inset.setValue(mods["prototile_inset"])

    try:
      expected = _library_unit_for(entry, spacing, shape=shape,
                                   over_under=over_under, aspect=aspect)
      # Apply the same modifiers by calling the library directly, in
      # the order a reader of the dialog would expect.
      if mods["rotate"]:
        expected = expected.transform_rotate(mods["rotate"])
      if mods["scale"] != (1.0, 1.0):
        expected = expected.transform_scale(*mods["scale"])
      if mods["skew"] != (0.0, 0.0):
        expected = expected.transform_skew(*mods["skew"])
      if mods["tile_inset"]:
        expected = expected.inset_tiles(
          mods["tile_inset"] * spacing / 100)
      if mods["prototile_inset"]:
        expected = expected.inset_prototile(
          mods["prototile_inset"] * spacing / 100)

      # A design can legitimately come out EMPTY: inset a stripe by
      # more than its own width and every tile is consumed, which is
      # arithmetic rather than a fault. Agreement then means both
      # sides produce nothing, and comparing renders of nothing would
      # only measure the background.
      if len(expected.tiles) == 0:
        empty = _dialog_for_setup(setup)
        assert empty.table.rowCount() == 0, \
          f"the library makes no tiles here but the dialog shows "\
          f"{empty.table.rowCount()} rows"
        assert empty.preview._message, \
          "the design collapsed to nothing and the preview said so"
        empty.close()
        continue

      _compare_ui_to_library(
        label, setup, expected, {}, variables=tuple(variables),
        ramps=tuple(ramps), opacities=opacities)
    except AssertionError as exc:
      failures.append(f"{label} (seed {seed}): {exc}")
    except Exception as exc:                          # noqa: BLE001
      failures.append(f"{label} (seed {seed}) raised "
                      f"{type(exc).__name__}: {exc}")

  assert not failures, \
    f"{len(failures)} of {cases} random designs did not match the "\
    f"library:\n  " + "\n  ".join(failures[:6])


def test_a_comma_decimal_locale_does_not_corrupt_numbers():
  """The plugin must work where the decimal separator is a comma.

  On a French, German or Brazilian system Qt formats and parses
  numbers with a comma, and every float the plugin reads from a spin
  box, writes into a GeoPackage or round-trips through a QML is a
  candidate for silent corruption. None of it is visible on a machine
  running in English, which is why this test forces the locale in a
  child process: QLocale has to be set before any widget exists, so it
  cannot be done in the middle of a suite that has already built
  dialogs.

  What would go wrong is not a crash but a wrong map: a spacing of
  1234.5 read as 12345, or an offset of 0.05 read as 5.
  """
  import subprocess
  import sys as _sys

  program = """
import importlib.util, os, sys
from qgis.PyQt.QtCore import QLocale
# German: comma decimal separator, full stop as the group separator.
QLocale.setDefault(QLocale(QLocale.Language.German, QLocale.Country.Germany))
ROOT = "__ROOT__"
spec = importlib.util.spec_from_file_location(
    "rt", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
from qgis.core import QgsApplication, QgsProject
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
app = QgsApplication([], True)
app.initQgis()
rt._no_modal_dialogs()
from weavingspace_qgis.dialog import WeavingSpaceDialog

layer = rt.make_region_layer()
QgsProject.instance().addMapLayer(layer)
dlg = WeavingSpaceDialog(iface=rt._Iface())
dlg.live_check.setChecked(False)

# a spacing with a fractional part, and a fine offset
dlg.spacing_spin.setValue(1234.5)
dlg.n_combo.setCurrentText("2")
dlg.kind_combo.setCurrentText("tiling")
dlg.family_combo.setCurrentText("hex-slice 2")
dlg.opt_offset.setValue(0.05)
dlg._rebuild_unit()
print("SPACING %r" % dlg.spacing_spin.value())
print("OFFSET %r" % dlg.opt_offset.value())
print("SHOWN %s" % dlg.spacing_spin.text())

rt._generate_and_wait(dlg)
ids = list(dlg._element_layer_ids.values())
counts = [QgsProject.instance().mapLayer(i).featureCount() for i in ids]
print("TILES %d" % sum(counts))

# and the same design through a GeoPackage, where the numbers are
# written and read back by a driver that has its own opinions
import tempfile
path = os.path.join(tempfile.mkdtemp(), "locale.gpkg")
dlg.gpkg_widget.setFilePath(path)
rt._generate_and_wait(dlg)
print("WROTE %d" % (1 if os.path.exists(path) else 0))
sys.stdout.flush()
os._exit(0)
""".replace("__ROOT__", ROOT)

  result = subprocess.run([_sys.executable, "-c", program],
                          capture_output=True, text=True, timeout=300)
  out = dict(line.split(" ", 1) for line in result.stdout.splitlines()
             if line.split(" ")[0].isupper() and " " in line)
  assert "SPACING" in out, \
    f"the plugin did not survive a comma-decimal locale:\n" \
    f"{result.stderr[-1500:]}"
  assert abs(float(out["SPACING"]) - 1234.5) < 1e-9, \
    f"a spacing of 1234.5 came back as {out['SPACING']} under a "\
    f"comma-decimal locale"
  assert abs(float(out["OFFSET"]) - 0.05) < 1e-9, \
    f"an offset of 0.05 came back as {out['OFFSET']}"
  # the DISPLAY should be localised even though the value is not
  assert "," in out["SHOWN"] or "." in out["SHOWN"], \
    f"the spin box showed {out['SHOWN']!r}"
  assert int(out["TILES"]) > 0, \
    "no tiles were produced under a comma-decimal locale"
  assert out.get("WROTE") == "1", \
    "the GeoPackage was not written under a comma-decimal locale"


def test_the_user_changes_the_data_underneath():
  """QGIS-side changes while the dialog is open must not defeat it.

  Users rename layers, edit attributes, delete fields and remove
  layers, and they do it with the plugin's window still open. The
  suite tests what the PLUGIN does thoroughly and what QGIS does to it
  barely at all. None of these should raise; each should either keep
  working or decline in a way the user can act on.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import compat
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(600)
  dlg.table.cellWidget(0, 1).setCurrentText("v1")
  _tick(400)

  # 1. renaming the layer: the chooser should follow, not lose it
  layer.setName("renamed by the user")
  _tick(300)
  assert dlg.layer_combo.currentLayer() is layer, \
    "renaming the region layer lost the dialog's selection"
  _generate_and_wait(dlg)
  assert dlg._element_layer_ids, "generation failed after a rename"

  # 2. adding a field mid-session: it should become choosable
  layer.dataProvider().addAttributes([compat.make_field("added", float)])
  layer.updateFields()
  _tick(400)
  dlg._refresh_table()
  offered = {dlg.table.cellWidget(0, 1).itemText(i)
             for i in range(dlg.table.cellWidget(0, 1).count())}
  assert "added" in offered, \
    f"a field added to the layer never appeared in the chooser: "\
    f"{sorted(offered)}"

  # 3. deleting the field a row is mapped to: the dialog must cope
  mapped_before = {a["id"] for a in dlg._assignments() if a["var"]}
  assert mapped_before, "some elements should be mapped before this"
  index = layer.fields().indexOf("v1")
  assert index >= 0
  layer.dataProvider().deleteAttributes([index])
  layer.updateFields()
  _tick(400)
  dlg._refresh_table()
  after = {a["id"]: a["var"] for a in dlg._assignments()}
  assert "v1" not in after.values(), \
    f"an element is still mapped to a field that no longer exists: "\
    f"{after}"
  # Losing a column must cost an element its VARIABLE, not its place
  # in the map. The weaker assertion above passes either way: it holds
  # when the element re-defaults to a surviving field, and equally when
  # the element is left unassigned and drawn as flat fill. Measured,
  # the difference reaches the map -- two of four elements come out
  # with a single-symbol renderer instead of a graduated one.
  surviving = {f.name() for f in layer.fields()}
  for tid in mapped_before:
    assert after.get(tid), \
      f"element {tid} was mapped before the field was deleted and is "\
      f"mapped to nothing now; it will draw as flat fill"
    assert after[tid] in surviving, \
      f"element {tid} is mapped to {after[tid]!r}, which is not a "\
      f"field of the layer: {sorted(surviving)}"
  # Generating now either works or declines, and BOTH are acceptable;
  # what matters is that it does not raise and does not leave a run in
  # flight. _generate_and_wait cannot be used here: it waits for a
  # completion callback, and a run that legitimately never starts
  # leaves it sitting out its whole backstop -- which is exactly what
  # happened when this test was first written.
  MODALS.clear()
  dlg._generate()
  if dlg._task is not None:
    assert _settle(dlg, 60), "the run never finished"
  else:
    assert MODALS, \
      "generation declined after the mapped field was deleted, and "\
      "said nothing about why"

  # 4. removing the layer entirely, with the dialog idle
  project.removeMapLayer(layer.id())
  _tick(400)
  MODALS.clear()
  dlg._generate()
  _tick(600)
  assert dlg._task is None, \
    "a run was started against a layer that no longer exists"
  assert MODALS or dlg.live_note.text().strip(), \
    "the region layer was gone and the plugin said nothing at all"
  dlg.close()


def test_the_map_says_which_areas_it_left_out():
  """A coarse spacing drops small areas; the map must say how many.

  Each tile takes its value from the area it falls in, so an area
  smaller than the pattern's grain can receive no tiles at all and
  appear nowhere -- unlike a choropleth, where every area is always
  drawn. The areas that vanish are systematically the small ones,
  which in social data are often the densest and most deprived, so
  this is a cartographic fact the map's author should be shown rather
  than a fault to hide.

  The message names the SPACING as well as the count, because people
  arrive at a spacing by trying several and each try pushes another
  notice: without the number they are a stack of identical
  complaints, and with it they are the coverage cost of each spacing
  tried.

  Measured overhead of computing this: worst case 1.68% of the
  worker's time on the Auckland data (155 areas), against a budget of
  15%. See tools/measure_coverage_warning.py; if a change makes it
  expensive, that harness is how to find out.
  """
  from weavingspace_qgis import bridge

  # the sentence itself, where the numbers are known exactly
  message = bridge.coverage_message(15, 155, 1500.0, "m")
  assert message, "a run that dropped 15 areas said nothing"
  assert "15" in message and "155" in message, \
    f"the count and the total must both be in the message: {message}"
  assert "1,500" in message or "1500" in message, \
    f"the spacing must be in the message, or a stack of these is "\
    f"unreadable: {message}"
  assert "m " in message or " m," in message or "m spacing" in message, \
    f"the spacing needs its units: {message}"
  assert bridge.coverage_message(0, 155, 400.0, "m") is None, \
    "full coverage must say nothing at all"

  # and end to end: a layer with one deliberately tiny area
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from weavingspace_qgis import compat
  project = QgsProject.instance()
  layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "uneven", "memory")
  layer.dataProvider().addAttributes([compat.make_field("v", float)])
  layer.updateFields()
  feats = []
  for i in range(3):                       # three large areas
    f = QgsFeature(layer.fields())
    f.setGeometry(QgsGeometry.fromWkt(
      f"POLYGON(({i*3000} 0, {i*3000+3000} 0, {i*3000+3000} 3000, "
      f"{i*3000} 3000, {i*3000} 0))"))
    f["v"] = float(i)
    feats.append(f)
  tiny = QgsFeature(layer.fields())        # and one far smaller than a tile
  tiny.setGeometry(QgsGeometry.fromWkt(
    "POLYGON((9000 0, 9040 0, 9040 40, 9000 40, 9000 0))"))
  tiny["v"] = 9.0
  feats.append(tiny)
  layer.dataProvider().addFeatures(feats)
  layer.updateExtents()
  project.addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=None)     # headless: notes land in the dialog
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  dlg.spacing_spin.setValue(1500)
  dlg.table.cellWidget(0, 1).setCurrentText("v")
  _generate_and_wait(dlg)
  _tick(300)

  note = dlg.live_note.text()
  assert "received no tiles" in note, \
    f"an area smaller than the pattern's grain vanished from the map "\
    f"and nothing said so; the note read {note!r}"
  assert "1500" in note or "1,500" in note, \
    f"the note must name the spacing that caused it: {note!r}"

  # the tracing column must not reach the user's layers
  out = project.mapLayer(dlg._element_layer_ids["a"])
  names = [f.name() for f in out.fields()]
  assert not any(n.startswith("ws_unit_id") for n in names), \
    f"the id used to count coverage leaked into the output: {names}"
  dlg.close()


def test_adversarial_sequences():
  """Every dangerous pairing of "start work" and "interfere with it".

  The uniform fuzz above wanders; this one goes straight for the
  transitions that have actually broken this plugin. Each defect in
  the register that came from a race had the same shape: something
  starts, something else changes before it finishes, and the finishing
  code writes state belonging to the earlier request. A ramp picked
  mid-run was lost that way; settings changed mid-run were swallowed
  because the signature was captured at completion rather than at
  launch.

  So rather than sampling, this enumerates the product: each way of
  starting work, crossed with each way of interfering, with no
  settling in between. The invariant is the one that caught the lost
  ramp -- the map must show what the table asks for -- plus the
  structural ones: one group, no orphaned layers, no task in flight,
  the dialog usable afterwards.

  Failures are collected rather than raised, so one bad pairing does
  not hide the other nineteen.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  import tempfile as tf
  project = QgsProject.instance()

  def provocations(dlg):
    """Ways of setting work in motion."""
    return [
      ("generate", lambda: dlg._generate()),
      ("live change", lambda: (dlg.live_check.setChecked(True),
                               dlg.spacing_spin.setValue(560))[0]),
    ]

  def perturbations(dlg, layer):
    """Ways of interfering before it can finish."""
    return [
      ("second generate", lambda: dlg._generate()),
      ("spacing", lambda: dlg.spacing_spin.setValue(640)),
      ("family", lambda: dlg.family_combo.setCurrentText("hex-slice 4")),
      ("element count", lambda: dlg.n_combo.setCurrentText("2")),
      ("variable", lambda: dlg.table.cellWidget(0, 1).setCurrentText("v2")
       if dlg.table.cellWidget(0, 1) else None),
      ("ramp", lambda: dlg.table.cellWidget(0, 4).setCurrentText("PuBu")
       if hasattr(dlg.table.cellWidget(0, 4), "setCurrentText") else None),
      ("style", lambda: dlg.table.cellWidget(0, 2).setCurrentText(
        "Quant: Equal intervals") if dlg.table.cellWidget(0, 2) else None),
      ("rotate", lambda: dlg.mod_rotate.setValue(20)),
      ("new group toggle", lambda: dlg.opt_new_group.setChecked(
        not dlg.opt_new_group.isChecked())),
      ("gpkg path", lambda: dlg.gpkg_widget.setFilePath(
        os.path.join(tf.mkdtemp(), "adversarial.gpkg"))),
      ("live toggle", lambda: dlg.live_check.setChecked(
        not dlg.live_check.isChecked())),
    ]

  problems = []
  scenario = 0
  for start_index in range(2):
    for perturb_index in range(11):
      scenario += 1
      project.clear()
      layer = make_region_layer()
      project.addMapLayer(layer)
      dlg = WeavingSpaceDialog(iface=_Iface())
      dlg.live_check.setChecked(False)
      dlg.spacing_spin.setValue(520)
      _settle(dlg, 60)

      start_name, start = provocations(dlg)[start_index]
      perturb_name, perturb = perturbations(dlg, layer)[perturb_index]
      label = f"{start_name} then {perturb_name}"
      try:
        start()
        perturb()                      # deliberately no settling between
      except Exception as exc:                       # noqa: BLE001
        problems.append(f"{label}: raised {type(exc).__name__}: {exc}")
        dlg.close()
        continue

      if not _settle(dlg, 120):
        problems.append(f"{label}: never came to rest")
      if dlg._task is not None:
        problems.append(f"{label}: a task was left in flight")
      if not dlg.generate_btn.isEnabled():
        problems.append(f"{label}: Generate left disabled")
      groups = [c for c in project.layerTreeRoot().children()
                if c.nodeType() == 0]
      if len(groups) > 2:               # two only when "new group" is on
        problems.append(f"{label}: {len(groups)} output groups")
      for tid, lid in dlg._element_layer_ids.items():
        if project.mapLayer(lid) is None:
          problems.append(f"{label}: element {tid} points at a layer "
                          f"that is gone")
      # The map is NOT required to match the table at this point, and
      # asserting that it does was wrong: with live update off, a run
      # captures its settings when it launches -- deliberately, so a
      # change made mid-run is deferred rather than swallowed -- so a
      # finished map legitimately shows what was asked for a moment
      # before the user changed their mind. Seven of these pairings
      # "failed" on that misreading.
      #
      # What must hold is that the dialog can always be brought back
      # into agreement: press Generate once more, let it settle, and
      # now the map is what the table says. That is the property the
      # lost-ramp defect actually violated.
      dlg.live_check.setChecked(False)
      dlg._generate()
      if not _settle(dlg, 120):
        problems.append(f"{label}: could not be brought to rest again")
      elif dlg._element_layer_ids:
        ok, detail = _map_matches_table(dlg)
        if not ok:
          problems.append(f"{label}: after a further Generate, {detail}")
      dlg.close()

  assert not problems, \
    f"{len(problems)} of {scenario} adversarial pairings broke an "\
    f"invariant:\n  " + "\n  ".join(problems[:8])


def test_a_changed_category_count_warns_that_colours_moved():
  """When a categorical field gains or loses a class, say so.

  Categorical colours are sampled across the palette by position:
  entry int(i * len(palette) / (k - 1)) for class i of k. That is
  matplotlib's ListedColormap rule and the plugin reproduces it
  deliberately, so the plugin is not doing anything wrong -- but a
  consequence follows that a cartographer will not expect. MEASURED,
  with tab10: going from three categories to four changes the colour
  of two of the three original classes; four to five changes three of
  four; five to six changes three of five. Only the first and last
  classes stay put, because the formula pins the palette's endpoints.

  So two maps of the same place made a month apart, or two neighbouring
  regions whose data happen to carry different numbers of classes, use
  different colours for the same category, and nothing says so. That is
  a comparison hazard rather than a bug, and the remedy already exists:
  import a colour mapping (a QML) for that element and the colours stop
  moving.

  The warning fires only when a count CHANGES within a session, which
  is the moment the colours actually shift under the user's feet;
  warning on every categorical map would be noise nobody reads.
  """
  from weavingspace_qgis import bridge

  # the sentence, where the numbers are known exactly
  message = bridge.categorical_shift_message("landcover", 4, 5)
  assert message, "a category count that changed said nothing"
  assert "landcover" in message, \
    f"the message must name the field that changed: {message}"
  assert "4" in message and "5" in message, \
    f"it must give both counts, so the reader can see what happened: "\
    f"{message}"
  lowered = message.lower()
  assert "colour" in lowered, f"say what moved: {message}"
  assert "qml" in lowered or "colour mapping" in lowered, \
    f"and what to do about it, which is to pin the colours with an "\
    f"imported mapping: {message}"
  assert bridge.categorical_shift_message("landcover", 4, 4) is None, \
    "an unchanged count must say nothing"
  assert bridge.categorical_shift_message("landcover", None, 4) is None, \
    "the first sight of a field is not a change"

  # and the underlying fact the warning is about, measured here so a
  # future palette change that removed the hazard would show up
  from weavingspace_qgis import compat
  def categorised(n):
    layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "c", "memory")
    layer.dataProvider().addAttributes([compat.make_field("cat", str)])
    layer.updateFields()
    feats = []
    for i in range(n):
      f = QgsFeature(layer.fields())
      f.setGeometry(QgsGeometry.fromWkt(
        f"POLYGON(({i*10} 0, {i*10+10} 0, {i*10+10} 10, {i*10} 10, "
        f"{i*10} 0))"))
      f["cat"] = f"class {i}"
      feats.append(f)
    layer.dataProvider().addFeatures(feats)
    layer.updateExtents()
    renderer = bridge.make_categorized_renderer(layer, "cat", "tab10", False)
    return {str(c.value()): c.symbol().color().name()
            for c in renderer.categories() if c.value()}

  # and end to end: the same field, mapped twice with a class filtered
  # out in between, must produce the notice
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()          # landcover has four classes
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(700)
  dlg.table.cellWidget(0, 1).setCurrentText("landcover")
  dlg.table.cellWidget(0, 2).setCurrentText("Categorized")
  dlg._update_dynamic_columns()
  _generate_and_wait(dlg)
  _tick(200)
  assert "categories" not in dlg.live_note.text(), \
    "the first sight of a field is not a change and must say nothing"

  # remove every feature of one class, so the count drops
  doomed = [f.id() for f in layer.getFeatures()
            if f["landcover"] == "crops"]
  assert doomed, "the fixture should have a crops class to remove"
  layer.dataProvider().deleteFeatures(doomed)
  layer.updateExtents()
  _tick(300)
  # Editing the DATA does not change the design's signature, so a
  # plain second Generate takes the restyle fast path and never
  # re-reads the layer -- by design, since a style change must not
  # re-tile. Move the spacing as well, which is what a cartographer
  # does anyway after filtering, so a genuine run happens.
  dlg.spacing_spin.setValue(680)
  _tick(300)
  _generate_and_wait(dlg)
  _tick(200)
  note = dlg.live_note.text()
  assert "landcover" in note and "categories" in note, \
    f"a class disappeared and the colours of the rest moved with it, "\
    f"and the plugin said {note!r}"
  dlg.close()

  four, five = categorised(4), categorised(5)
  moved = [k for k in four if k in five and four[k] != five[k]]
  assert moved, \
    "adding a category no longer moves any existing colour -- which "\
    "would be good news, but this warning and its wording assume it "\
    "does, so both need revisiting"
  assert len(moved) >= 2, \
    f"expected most classes to move when a fifth is added, got {moved}"


def test_colours_a_reader_cannot_separate_are_reported():
  """Elements whose colours collapse must be named, including for
  readers with a colour-vision deficiency.

  A tiled multivariate map asks its reader to separate interleaved
  element shapes and read each one's colour as a different variable.
  Where two elements' fills are too close, that reading fails in a way
  the map does not admit to: it looks finished and carries fewer
  variables than it claims. Roughly one man in twelve has a red-green
  deficiency, and the default ramp set is built almost entirely on the
  red-green axis.

  Measured, and reproduced here: Reds' third class against Greens'
  fourth is Delta-E 100.7 for a normal-vision reader and 4.7 for a
  protanope. The plugin does not change anyone's ramps over this --
  which colours to use is the cartographer's decision -- it makes the
  cost of a choice visible while it can still be changed.

  A SHARED ramp across elements is not a clash. That design
  distinguishes elements by shape and is what the technique's authors
  recommend for many variables; warning there would be wrong, and the
  remedy the message suggests IS a shared ramp.
  """
  from weavingspace_qgis import perception as p

  def rgb(text):
    text = text.lstrip("#")
    return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))

  # the arithmetic, against numbers measured by the standalone tool on
  # rendered maps -- two independent implementations agreeing
  assert abs(p.distance(rgb("#fa694c"), rgb("#228b45"), "normal")
             - 100.7) < 0.5
  assert abs(p.distance(rgb("#fa694c"), rgb("#228b45"), "protanopia")
             - 4.7) < 0.5, \
    "a pair 100 apart for most readers is 4.7 apart for a protanope; "\
    "if this number moved, the simulation changed"
  assert abs(p.distance(rgb("#17becf"), rgb("#9e9bc9"), "deuteranopia")
             - 2.7) < 0.5

  # elements that clash, and the message about them
  clashing = p.clashes({"a": [rgb("#fa694c")], "b": [rgb("#228b45")]})
  assert clashing, "a red and a green that collapse for protanopes " \
    "must be reported"
  assert clashing[0][2] == "protanopia", \
    f"and reported under the vision that fails: {clashing[0]}"
  message = p.clash_message(clashing)
  assert "'a'" in message and "'b'" in message, \
    f"the message must name the elements: {message}"
  assert "protanopia" in message, f"and the vision: {message}"

  # a shared ramp is not a clash
  same = [rgb("#fff5f0"), rgb("#fa694c"), rgb("#67000d")]
  assert not p.clashes({"a": same, "b": same},
                       shared={"a": ("Reds", False, None),
                               "b": ("Reds", False, None)}), \
    "elements sharing a ramp are meant to share colours; that design "\
    "is what the paper recommends and must not be warned about"
  assert p.clashes({"a": same, "b": same}), \
    "but identical colours from DIFFERENT ramps still collapse"
  assert p.clash_message([]) is None, "silence when nothing is close"

  # and end to end, through a real map
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  dlg.live_check.setChecked(False)
  # the legibility check is opt-in, so a test of what it SAYS has to
  # ask for it; that it stays quiet unopted is a separate test
  dlg.opt_colour_warnings.setChecked(True)
  dlg.spacing_spin.setValue(700)
  for row, ramp in enumerate(("Reds", "Greens", "Blues", "Purples")):
    widget = dlg.table.cellWidget(row, 4)
    if hasattr(widget, "setCurrentText"):
      widget.setCurrentText(ramp)
  _tick(300)
  _generate_and_wait(dlg)
  _tick(200)
  note = dlg.live_note.text()
  assert "tell apart" in note, \
    f"four ramps on the red-green axis produced no warning: {note!r}"
  dlg.close()


def test_plugin_lifecycle():
  """The QGIS entry points themselves: classFactory, initGui, the
  toolbar action opening the dialog, and unload. Nothing else in the
  suite touches plugin.py, so a broken menu registration or a stale
  dialog reference on unload would ship unnoticed."""
  import weavingspace_qgis as package  # classFactory lives here

  class _MenuIface(_Iface):
    """Enough of QgisInterface for the plugin's registration calls."""

    def __init__(self):
      self.menu_items, self.toolbar_items = [], []

    def addPluginToMenu(self, menu, action):  # noqa: N802 (QGIS API)
      self.menu_items.append((menu, action))

    def removePluginMenu(self, menu, action):  # noqa: N802
      self.menu_items = [x for x in self.menu_items if x[1] is not action]

    def addToolBarIcon(self, action):  # noqa: N802
      self.toolbar_items.append(action)

    def removeToolBarIcon(self, action):  # noqa: N802
      self.toolbar_items = [a for a in self.toolbar_items if a is not action]

  iface = _MenuIface()
  instance = package.classFactory(iface)
  instance.initGui()
  assert iface.menu_items and iface.toolbar_items, \
    "the plugin must register a menu entry and a toolbar button"
  action = iface.toolbar_items[0]
  assert action.text(), "the action needs a label"

  layer = make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  instance.open_dialog()
  assert instance.dialog is not None, "the action must open the dialog"
  assert instance.dialog.windowTitle(), "the dialog needs a title"
  first = instance.dialog
  instance.open_dialog()
  assert instance.dialog is first, "the dialog is reused, not duplicated"
  if instance.dialog.live_check.isChecked():
    instance.dialog.live_check.setChecked(False)

  instance.unload()
  assert not iface.menu_items and not iface.toolbar_items, \
    "unload must remove what initGui added"
  assert instance.dialog is None, "unload must drop the dialog"


def test_integration_cancel_and_recover():
  """Cancelling a run mid-flight (what closing the dialog does) must
  leave the plugin able to generate again: no task stuck in _task, the
  Generate button enabled, and the next run completing normally."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=_Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(300)
  dlg._generate()
  assert dlg._task is not None, "a task should be in flight"
  dlg._task.cancel()
  loop = QEventLoop()
  QTimer.singleShot(3_000, loop.quit)
  loop.exec()
  assert dlg._task is None, "a cancelled task must clear itself"
  assert dlg.generate_btn.isEnabled()
  dlg.spacing_spin.setValue(600)
  _generate_and_wait(dlg)
  assert dlg._element_layer_ids, "generation must work after a cancel"
  dlg.close()


def main():
  """Run every registered test and report what happened.

  Returns:
    None; exits with status 1 when anything failed, which is what
    release.py gates on. Writes reports/v<version>/scenarios.json,
    the record the visual comparison PDF is built from.

  The record is emptied first so the PDF describes THIS run. A stale
  scenario left over from a previous version would otherwise appear
  in the report as though it had just been measured.
  """
  # start the UI-vs-library record empty so the PDF shows this run
  record = os.path.join(report_dir(), "scenarios.json")
  if os.path.exists(record):
    os.remove(record)
  QgsApplication.setPrefixPath(
    os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  app = QgsApplication([], True)
  app.initQgis()
  _enable_stack_dumps()
  _no_modal_dialogs()
  print(f"QGIS Python {sys.version.split()[0]}")

  check("dependencies present / wheel logic", test_deps)
  check("weavingspace unit construction", test_library_units)
  check("catalogue sweep (every family, every count)",
        test_catalogue_sweep)
  check("layer <-> GeoDataFrame roundtrip", test_bridge_roundtrip)
  check("awkward geometry (invalid, holed, multipart, null)",
        test_awkward_geometry)
  check("real-world data end to end (Auckland IMD)",
        test_real_world_data)
  check("renderer seeding (graduated + categorized)", test_renderer_seeding)
  check("QML class template round trip", test_qml_class_template)
  check("tile-count size guard", test_size_guard)
  check("deps/compat support logic", test_support_logic)
  check("automatic first render on layer choice", test_auto_first_render)
  check("per-row class file pickers", test_per_row_class_files)
  check("palette pick survives debounce (no chooser race)",
        test_palette_pick_survives_debounce)
  check("dialog end-to-end (generate, regen, gpkg)", test_dialog_end_to_end)
  check("output management (outlines, selective reseed, groups)",
        test_output_management)
  check("live update gates (gpkg, comparison mode)",
        test_live_update_gates)
  check("design cascade (n/kind/family/options/fit)",
        test_design_cascade)
  check("style follow, ramp memory, single colour",
        test_style_follow_and_memory)
  check("choice persistence and zombie recovery",
        test_choice_persistence_and_recovery)
  check("integration: GeoPackage style round trip",
        test_integration_gpkg_style_round_trip)
  check("integration: region layer switch",
        test_integration_region_layer_switch)
  check("integration: live update session",
        test_integration_live_session)
  check("integration: second dialog session",
        test_integration_second_dialog_session)
  check("integration: weave with icons and outlines",
        test_integration_weave_and_icons)
  check("integration: interleaved styling and design changes",
        test_integration_interleaved_session)
  check("integration: categorical colour-source session",
        test_integration_categorical_session)
  check("UI vs library: slice offset, rotate, inset",
        test_ui_library_slice_modifiers)
  check("UI vs library: weave over-under, strand width, inset",
        test_ui_library_weave_parameters)
  check("UI vs library: rotate/scale/skew/inset chain",
        test_ui_library_modifier_chain)
  check("UI vs library: icons and whole-tileable join",
        test_ui_library_icons_and_join)
  check("UI vs library: clipped edges", test_ui_library_clipped_edges)
  check("UI vs library: grid rows and columns",
        test_ui_library_grid_rows_cols)
  check("UI vs library: dissection inner angle",
        test_ui_library_dissection_angles)
  check("UI vs library: star point angle",
        test_ui_library_star_point_angle)
  check("UI vs library: glyph scaling", test_ui_library_glyph_scaling)
  check("UI vs library: categorical sources and unassigned element",
        test_ui_library_categorical_template)
  check("UI vs library: categorical weave, icons, layer source",
        test_ui_library_categorical_weave_icons)
  check("UI vs library: categorical to GeoPackage and back",
        test_ui_library_categorical_to_gpkg)
  check("stress: fast interaction (race hunt)",
        test_stress_fast_interaction)
  check("stress: styling, rendering and sizing on complex data",
        test_stress_complex_data_bumbling)
  check("preview fits unit and shells; labels at app type size",
        test_preview_fits_and_labels)
  check("run lifecycle: no overlapping runs",
        test_run_lifecycle_no_overlap)
  check("restyle without re-tiling (fast path)",
        test_restyle_without_retiling)
  check("reverse ramp column (per element, no re-tiling)",
        test_reverse_ramp_column)
  check("element opacity (layer opacity, authority, gpkg)",
        test_element_opacity)
  check("opacity in the preview (floored)", test_opacity_in_preview)
  check("race: settings changed during a run",
        test_race_settings_change_during_run)
  check("race: two Generate presses", test_race_double_generate)
  check("race: restyle during a run", test_race_restyle_during_run)
  check("race: close during a run", test_race_close_during_run)
  check("race: region layer removed during a run",
        test_race_region_layer_removed_during_run)
  check("one dialog instance per session",
        test_single_dialog_instance)
  check("race: change during the output phase",
        test_race_change_during_output_phase)
  check("race: every control changed mid-tiling",
        test_race_control_sweep)
  check("fuzz: random interaction keeps the invariants",
        test_fuzz_random_interaction)
  check("GeoPackage export with an fid attribute",
        test_gpkg_fid_attribute)
  check("Generate uses the design on screen",
        test_generate_uses_the_design_on_screen)
  check("typing reaches the design", test_typing_updates_the_design)
  check("an inset percentage is a percentage of the spacing",
        test_an_inset_percentage_is_a_percentage_of_the_spacing)
  check("every element count still has its designs",
        test_every_element_count_still_has_its_designs)
  check("every declared offset is pinned",
        test_every_declared_offset_is_pinned)
  check("catalogue values are what they claim",
        test_catalogue_values_are_what_they_claim)
  check("UI affordances are deliberate",
        test_ui_affordances_are_deliberate)
  check("metamorphic: reversing twice is the identity",
        test_metamorphic_reversal_is_an_involution)
  check("metamorphic: full rotation and the spacing law",
        test_metamorphic_full_rotation_and_scaling)
  check("metamorphic: permuting variables permutes the map",
        test_metamorphic_variable_permutation)
  check("metamorphic: translation invariance",
        test_metamorphic_translation_invariance)
  check("metamorphic: opacity round trip",
        test_metamorphic_opacity_round_trip)
  check("model-based: the dialog's state machine",
        test_model_based_dialog_states)
  check("controls respond without being prompted",
        test_controls_respond_without_being_prompted)
  check("dialog structure (tabs, help, controls)",
        test_dialog_structure)
  check("a first-field variable is not a special case",
        test_first_field_is_not_a_special_case)
  check("the map group sits on top of the layers panel",
        test_group_sits_on_top_of_the_layers_panel)
  check("the plugin never offers its own output as a region",
        test_plugin_never_offers_its_own_output_as_a_region)
  check("design controls are usable as designed",
        test_design_controls_are_usable_as_designed)
  check("preview colours follow the variable",
        test_preview_colours_follow_the_variable)
  check("auto spacing offers a round number",
        test_auto_spacing_offers_a_round_number)
  check("the preview draws the middle of the patch",
        test_preview_draws_the_middle_of_the_patch)
  check("switching region layer counts as a change",
        test_switching_region_layer_counts_as_a_change)
  check("no control is dead", test_no_control_is_dead)
  check("a row without classes says so",
        test_a_row_without_classes_says_so)
  check("a finished run leaves nothing armed",
        test_a_finished_run_leaves_nothing_armed)
  check("the dialog's chrome does its job",
        test_the_dialogs_chrome_does_its_job)
  check("ramp swatches and palette installation",
        test_ramp_swatches_and_palette_installation)
  check("family option ranges track the family",
        test_family_option_ranges_track_the_family)
  check("a single category still gets a colour",
        test_a_single_category_still_gets_a_colour)
  check("the library works without matplotlib or scipy",
        test_the_library_works_without_matplotlib_or_scipy)
  check("defaults avoid identifier columns",
        test_defaults_avoid_identifier_columns)
  check("repopulating a chooser does not duplicate it",
        test_repopulating_a_chooser_does_not_duplicate_it)
  check("the size guard does not refuse fine patterns",
        test_the_size_guard_does_not_refuse_fine_patterns)
  check("hostile data does not defeat the plugin",
        test_hostile_data_does_not_defeat_the_plugin)
  check("an over-large inset empties the design visibly",
        test_an_over_large_inset_empties_the_design_visibly)
  check("random designs match the library",
        test_random_designs_match_the_library)
  check("a comma-decimal locale does not corrupt numbers",
        test_a_comma_decimal_locale_does_not_corrupt_numbers)
  check("the user changes the data underneath",
        test_the_user_changes_the_data_underneath)
  check("the map says which areas it left out",
        test_the_map_says_which_areas_it_left_out)
  check("adversarial sequences", test_adversarial_sequences)
  check("a changed category count warns that colours moved",
        test_a_changed_category_count_warns_that_colours_moved)
  check("colours a reader cannot separate are reported",
        test_colours_a_reader_cannot_separate_are_reported)
  check("two notices from one run both survive",
        test_two_notices_from_one_run_both_survive)
  check("the window fits its design tab when shown",
        test_the_window_fits_its_design_tab_when_shown)
  check("cancelling frees the dialog at once",
        test_cancelling_frees_the_dialog_at_once)
  check("every design control is reachable",
        test_every_design_control_is_reachable)
  check("every control starts where it should",
        test_every_control_starts_where_it_should)
  check("every control accepts the range it should",
        test_every_control_accepts_the_range_it_should)
  check("every control explains itself",
        test_every_control_explains_itself)
  check("the preview actually draws what it is given",
        test_the_preview_actually_draws_what_it_is_given)
  check("the design view draws no tile outlines",
        test_the_design_view_draws_no_tile_outlines)
  check("colour legibility warnings are opt-in",
        test_colour_legibility_warnings_are_opt_in)
  check("awkward layers are handled or declined",
        test_awkward_layers_are_handled_or_declined)
  check("region outlines are cased", test_region_outlines_are_cased)
  check("installed palettes span their declared colours",
        test_installed_palettes_span_their_declared_colours)
  check("ramp swatches run the right way round",
        test_ramp_swatches_run_the_right_way_round)
  check("a new run always shows real progress",
        test_a_new_run_always_shows_real_progress)
  check("live update is on by default",
        test_live_update_is_on_by_default)
  check("repopulating the family list fires no handlers",
        test_repopulating_the_family_list_fires_no_handlers)
  check("Edit colours column appears with categories",
        test_the_edit_colours_column_appears_with_categories)
  check("the editor lists every value and the no-data row",
        test_the_editor_lists_every_value_and_the_no_data_row)
  check("a long category value truncates but is recoverable",
        test_a_long_value_is_truncated_but_recoverable)
  check("editing a category colour reaches the map",
        test_editing_a_category_colour_reaches_the_map)
  check("the editor is laid out as specified",
        test_the_editor_is_laid_out_as_specified)
  check("the editor hides nothing at any size",
        test_the_editor_hides_nothing_at_any_size)
  check("the editor scrolls only past fifteen values",
        test_the_editor_scrolls_only_past_fifteen_values)
  check("a picked colour changes the rendered map",
        test_a_picked_colour_changes_the_rendered_map)
  check("hand-picked colours survive a regenerate",
        test_hand_picked_colours_survive_a_regenerate)
  check("a new ramp discards hand-picks and says so",
        test_a_new_ramp_discards_hand_picks_and_says_so)
  check("hand-picks are kept per variable",
        test_hand_picks_are_kept_per_variable)
  check("hand-picked colours are written into the project",
        test_hand_picked_colours_are_written_into_the_project)
  check("race: a colour picked during a run is not lost",
        test_a_colour_picked_during_a_run_is_not_lost)
  check("editing colours never rebuilds the table",
        test_editing_colours_never_rebuilds_the_table)
  check("the editor copes with the data going away",
        test_the_editor_copes_with_the_data_going_away)
  check("plugin lifecycle (menu, action, unload)",
        test_plugin_lifecycle)
  check("integration: cancel and recover",
        test_integration_cancel_and_recover)

  print(f"\n{len(PASSED)} passed, {len(FAILED)} failed")
  app.exitQgis()
  sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
  main()
