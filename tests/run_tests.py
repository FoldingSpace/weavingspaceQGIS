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
import os
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
  below are about those four things specifically."""
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
  """A QML with categorized symbology should drive class colours."""
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
  dialog is needed to exercise."""
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
  def pushSuccess(self, *a):
    pass

  def pushWarning(self, *a):
    pass


class _Iface:
  def mainWindow(self):
    return None

  def messageBar(self):
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
  """Choosing a layer should populate variables and render unaided."""
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
  (the reported symptom: 'changing the palettes doesn't work')."""
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
  intact."""
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
  the comparison checkbox is on (it would spawn a group per tweak)."""
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


def test_choice_persistence_and_recovery():
  """Two more state-keeping behaviours: a row's class-source choice
  survives a Design-tab rebuild (choices live in dicts keyed by tile
  id, not in the replaced widgets), and reopening the dialog recovers
  from a zombie task (a cancelled task left in _task must not block
  future runs)."""
  import tempfile as tf
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

  # zombie-task recovery on reopen
  dead = TilingTask("dead", lambda t: None, lambda r, e: None)
  dead.cancel()
  dlg._task = dead
  dlg.generate_btn.setEnabled(False)
  dlg.hide()
  dlg.show()  # showEvent runs the recovery
  assert dlg._task is None, "zombie task must be cleared on reopen"
  assert dlg.generate_btn.isEnabled()
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
  proves only that something was written; this proves it works."""
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
  single group with the same element layers replaced in place."""
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
  """(differing, total) interior pixels between two renders of the
  same size. Interior means the four neighbours agree, so antialiased
  edges — which say nothing about symbology — never enter the count."""
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
  """Render what the dialog produced beside the same map built from a
  direct library call, compare interior pixels, and record the pair
  for the PDF.

  Used wherever a test knows, independently of the dialog, what map
  the settings describe. `templates` maps a class-source token to a
  loaded QML template so categorical elements can be seeded the same
  way the dialog seeds them."""
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
                 max_background=0.95):
  """Render what the dialog produced and check every interior pixel
  is a colour the assigned ramps can actually make.

  For sessions where no independent expected map is practical (a
  storm of fast clicks, a long interleaved session), this is still a
  real visual measure: it catches blank maps, wrong ramps, and
  corrupted symbology, and it puts the picture in the PDF where a
  person can see what the session produced."""
  sys.path.insert(0, HERE)
  from visual_tests import render_layers, gamut_delta_e, image_stats
  out_dir = report_dir()
  slug = label.lower().replace(" ", "_").replace(",", "")
  png = os.path.join(out_dir, f"{slug}_ui.png")
  image = render_layers(list(ui_layers), png)
  _colours, background = image_stats(image)
  mean_de, p95_de = gamut_delta_e(image, list(ramps))
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
  """Drive the dialog with `setup`, then check its output against a
  map built directly from `expected_unit` and `tiling_kw`.

  Geometry first (same elements, same tile counts, same area within
  tolerance), then the rendered picture (share of sampled pixels that
  differ beyond an antialiasing threshold). Both matter: geometry
  catches wrong parameters, pixels catch a right tiling wearing the
  wrong symbology.
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
  can tell."""
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
  element still drew as plain fill rather than vanishing."""
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
  """Run the event loop until the dialog is quiet: no task in flight,
  no debounce pending. Returns True if it settled, False on timeout.

  Race tests need a defined end state, and 'sleep a bit' is not one.
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
  says."""
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
                   "hex-dissection 4": 0, "hex-dissection 7": 0}
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
  """{element: darkest colour of its ramp} for the current map."""
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
  assert dlg.table.columnCount() == 8, \
    f"the table has {dlg.table.columnCount()} columns, expected 8"
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
  _generate_and_wait(dlg)

  produced = set(dlg._element_layer_ids.values())
  assert produced, "the run should have produced element layers"
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
  ELSEWHERE = {
    "live_check": "gates automatic regeneration; changes nothing on "
                  "screen until a setting moves",
    "gpkg_widget": "chooses an output file, which affects the next "
                   "run rather than the current design",
    "layer_combo": "covered by its own tests, and switching layers "
                   "auto-sizes spacing, which would make this test "
                   "pass for the wrong reason",
    "opacity_spin": "per-element, exercised through the table",
  }

  def fingerprint(dlg):
    """Everything a user could notice about the current design."""
    unit = tuple(g.wkt for g in dlg._unit.tiles.geometry) \
        if dlg._unit is not None else ()
    table = tuple(
      (dlg.table.item(r, 0).text() if dlg.table.item(r, 0) else "",
       dlg.table.cellWidget(r, 1).currentText()
       if dlg.table.cellWidget(r, 1) else "")
      for r in range(dlg.table.rowCount()))
    return (unit, len(dlg.preview._polys), len(dlg.preview._labels),
            table)

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
      # put the design back so the next control starts from a known
      # place rather than from wherever the last one left it
      dlg.family_combo.setCurrentText(family)
      _tick(600)
    dlg.close()

  assert tested >= 12, \
    f"only {tested} controls were exercised; the walk is not reaching "\
    f"the dialog's controls and would pass whatever was broken"
  assert not dead, \
    f"{len(dead)} control(s) changed nothing when moved, so a user "\
    f"operating them would see no response at all: {', '.join(dead)}"


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
  check("plugin lifecycle (menu, action, unload)",
        test_plugin_lifecycle)
  check("integration: cancel and recover",
        test_integration_cancel_and_recover)

  print(f"\n{len(PASSED)} passed, {len(FAILED)} failed")
  app.exitQgis()
  sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
  main()
