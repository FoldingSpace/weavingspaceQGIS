"""Visual release gallery: render canonical weavingspace outputs.

Run under QGIS's own Python (release.py does this; see MAINTAINING.md
for the manual command). Each case builds a tile unit, tiles a
synthetic region through the plugin's own bridge code, symbolizes it,
renders the map to a PNG, and checks coarse image properties. The
point is twofold:

* regression: the canonical looks of the core library (the Laves
  tiling the paper favours, weaves with visible gaps, the shared-ramp
  reading, categorized classes, the modifier chain, icon mode) must
  survive plugin and upstream changes — a wrong-but-nonempty map
  passes functional tests and only a picture catches it;
* reporting: the PNGs plus pass/fail results are written into an HTML
  report per version (reports/v<version>/), a human-checkable record
  of what each release actually drew.

Image checks come at two strictness levels. Coarse ones (colour
counts, background fractions) catch blank, monochrome, or gap-less
renders. On top of those, colourspace criteria measure CIELAB
distance (Delta-E, the standard perceptual colour difference; ~2 is
just noticeable, ~10 is clearly different): every sampled non-
background pixel must sit close to a colour that the assigned ramps
can actually produce, which catches wrong-ramp, wrong-palette, and
corrupted-symbology bugs that coarse counts miss. Sampling keeps only
interior fills — a pixel counts when its four neighbours agree with
it — so antialiased edge blends never enter the measurement and the
thresholds can sit near zero (mean < 1.5, p95 < 4): the measurement
is made on the stuff that matters, and any excursion is real colour
drift rather than platform rendering noise. Each numeric case also
saves a second render using the plugin's "Quant: Unclassed" style
(50 linear intervals) as *_unclassed.png; the reference-comparison
step (tools/visual_reference_report.py) uses those when quantile
classing alone explains a mismatch with the unclassed reference.

QGIS pieces used here, for weavingspace-minded readers:
QgsMapSettings describes a map view (layers, extent, size, background);
QgsMapRendererParallelJob draws it off-screen into a QImage without any
visible window, signalling ``finished`` when done — a QEventLoop waits
for that signal. Everything else comes from the plugin's bridge module.
"""

import base64
import html
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))
# ...and libs/, where a QGIS lacking the scientific stack keeps the
# wheels it was given. tests/run_tests.py gained this on 2026-08-11
# and this file did not, which is the "one fix, two loops" shape
# docs/TESTING.md warns about: the same defect in a second harness,
# invisible on a machine whose QGIS already carries geopandas.
#
# It cost the gallery experiment its first run (2026-08-12). CI
# provisioned successfully -- "every requirement is now met" -- and
# then all thirteen cases failed with ModuleNotFoundError on
# geopandas, on all three QGIS versions, because the renders never
# looked where the wheels had been put. The experiment was supposed
# to measure whether Delta-E thresholds survive a different font
# stack and instead measured a path bug.
try:
  from weavingspace_qgis import deps as _deps
  _deps.add_paths()
except Exception:      # a tree without the package is a different fault
  pass                 # and the imports below will say so far better

import warnings
warnings.filterwarnings("ignore")

from qgis.core import (  # noqa: E402
  QgsApplication, QgsMapRendererParallelJob, QgsMapSettings,
)
from qgis.PyQt.QtCore import QEventLoop, QSize  # noqa: E402
from qgis.PyQt.QtGui import QColor  # noqa: E402

RESULTS = []  # dicts: name, ok, detail, seconds, png (path or None)


# ------------------------------------------------------- colourspace helpers

def srgb_to_lab(rgb):
  """sRGB (n x 3, 0..255) to CIELAB via linear RGB and XYZ (D65).

  Textbook conversion, kept dependency-free (numpy only, which QGIS
  ships). Lab is used because Euclidean distance there approximates
  perceived colour difference (Delta-E 1976).
  """
  import numpy as np
  c = np.asarray(rgb, dtype=float) / 255.0
  c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
  m = np.array([[0.4124564, 0.3575761, 0.1804375],
                [0.2126729, 0.7151522, 0.0721750],
                [0.0193339, 0.1191920, 0.9503041]])
  xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])  # D65 white point
  f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz),
               xyz / (3 * (6 / 29) ** 2) + 4 / 29)
  lab = np.empty_like(f)
  lab[:, 0] = 116 * f[:, 1] - 16
  lab[:, 1] = 500 * (f[:, 0] - f[:, 1])
  lab[:, 2] = 200 * (f[:, 1] - f[:, 2])
  return lab


def sample_pixels(image, sample=140):
  """Interior fill colours on a sample grid, as an (n, 3) array.

  Only pixels whose four neighbours agree with them (within a small
  per-channel tolerance) are kept: antialiased blends along polygon
  edges are rendering artifacts, not symbology, and admitting them
  forces loose thresholds that could hide real colour drift. With
  edges excluded, every sampled colour should be one the assigned
  ramps actually produce, so gamut_delta_e can demand near-zero.

  Args:
    image: a QImage as render_layers returns it — drawn on the
      magenta chroma key, since a pixel counts as background by
      being that colour and not by being pale.
    sample: how many sample points to aim for along each edge, which
      sets the stride (width // sample). 140 over the usual 700-pixel
      render takes every fifth pixel: dense enough that one
      mis-symbolized element cannot hide between the samples, cheap
      enough to run on every case. Raising it costs pixel reads, not
      accuracy, since five neighbouring reads happen per sample.

  Returns:
    An (n, 3) float array of RGB triples, one row per surviving
    interior pixel, unordered — every caller reduces it to distances
    over the whole set. An empty (0, 3) array when the render is all
    background or all edge blend, which callers treat as a failure
    rather than as a clean result. The image is only read.
  """
  import numpy as np
  out = []
  w, h = image.width(), image.height()
  for x in range(1, w - 1, max(1, w // sample)):
    for y in range(1, h - 1, max(1, h // sample)):
      c = image.pixelColor(x, y)
      if _is_background(c):
        continue
      rgb = (c.red(), c.green(), c.blue())
      if any(max(abs(image.pixelColor(x + dx, y + dy).red() - rgb[0]),
                 abs(image.pixelColor(x + dx, y + dy).green() - rgb[1]),
                 abs(image.pixelColor(x + dx, y + dy).blue() - rgb[2]))
             > 8 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
        continue  # an edge blend, not an interior fill
      out.append(rgb)
  return np.array(out) if out else np.empty((0, 3))


def ramp_gamut(ramp_names, steps=64):
  """Every colour the given ramps can produce (interpolated stops from
  palettes.json). No blend forgiveness: sample_pixels now keeps only
  interior fills, so every sampled colour must sit ON a ramp — a
  colour that needs a white blend to be explained is a real defect.

  Args:
    ramp_names: ramp names as an assignment dict carries them
      ("Reds", "RdBu", "tab10"), looked up in bridge.PALETTES under
      sequential, then diverging, then categorical. A name in none of
      them contributes nothing rather than raising: a case may
      legitimately name a ramp QGIS supplies but the plugin does not
      install.
    steps: how finely a continuous ramp is sampled between its stops.
      64 is well above the class counts the gallery uses (5, or 50 in
      the unclassed variants), so any class colour has a near
      neighbour here and the Delta-E left over from sampling alone
      stays far under the 1.5 threshold the cases assert. Categorical
      palettes ignore it: their stops ARE the whole gamut, and
      interpolating between them would invent colours no renderer can
      draw and so forgive a wrong-entry bug.

  Returns:
    An (n, 3) float RGB array: the union over every named ramp, plus
    one row for bridge.NO_DATA_FILL (#dddddd), the grey drawn for
    features a class scheme does not match — legitimate map colour
    that belongs to no ramp. bridge.PALETTES is only read.
  """
  import numpy as np
  from weavingspace_qgis import bridge
  colours = []
  for name in ramp_names:
    # The ramp IN FORCE, read from the style library, before the
    # plugin's declared table. The two can differ legitimately: a
    # palette whose name QGIS already carries is deliberately not
    # installed, so the map is painted with QGIS's version while
    # bridge.PALETTES still describes ours. Measuring the map against
    # the table then reports a defect where the plugin did exactly
    # what it was designed to do -- which is what happened on Linux,
    # where QGIS ships Greys starting #fafafa against our #ffffff
    # (CI, 2026-08-11). The question this function answers is whether
    # every pixel is a colour the symbology CAN make, so the
    # symbology is the thing to ask.
    live = bridge.get_ramp(name, False)
    if live is not None:
      colours.append(np.array(
        [[c.red(), c.green(), c.blue()]
         for c in (live.color(i / (steps - 1)) for i in range(steps))],
        dtype=float))
      continue
    stops = (bridge.PALETTES["sequential"].get(name)
             or bridge.PALETTES["diverging"].get(name)
             or bridge.PALETTES["categorical"].get(name) or [])
    rgb = np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)]
                    for c in stops], dtype=float)
    if len(rgb) == 0:
      continue
    if name in bridge.PALETTES["categorical"]:
      colours.append(rgb)  # discrete sets are their own gamut
    else:
      t = np.linspace(0, len(rgb) - 1, steps)
      idx = np.minimum(t.astype(int), len(rgb) - 2)
      frac = (t - idx)[:, None]
      colours.append(rgb[idx] * (1 - frac) + rgb[idx + 1] * frac)
  colours.append(np.array([[221.0, 221.0, 221.0]]))  # no-data grey
  return np.vstack(colours)


def gamut_delta_e(image, ramp_names, extra_colours=()):
  """(mean, p95) Delta-E from sampled map pixels to the nearest colour
  the assigned symbology can produce; small values mean every pixel is
  explained by the intended symbology.

  Args:
    image: the rendered QImage to measure.
    ramp_names: the ramps in force on the layers that were drawn —
      every one of them, since the picture contains every layer.
      Naming only some reports the others' correct colours as strays.
    extra_colours: "#rrggbb" strings that belong to the gamut for
      reasons a ramp name cannot express; see below.

  Returns:
    (mean, p95) Delta-E over the sampled interior pixels, or
    (999.0, 999.0) when nothing could be sampled, which is itself a
    failure worth reporting rather than an average over no data.

  `extra_colours` are "#rrggbb" strings belonging to the gamut for
  reasons a ramp name cannot express -- at present, colours chosen by
  hand in the Categorical colour editor. Those are deliberately NOT on
  any ramp, which is the whole reason someone picks one, so a check
  that only knew about ramps would report a correct map as broken.
  "The colours in force" always meant the colours the map is entitled
  to use; until hand-picking existed, the ramps were the whole of it.
  """
  import numpy as np
  pixels = sample_pixels(image)
  if len(pixels) == 0:
    return 999.0, 999.0
  lab_pix = srgb_to_lab(pixels)
  gamut = list(ramp_gamut(ramp_names)) + [
    tuple(int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    for c in extra_colours]
  lab_gamut = srgb_to_lab(gamut)
  d = np.sqrt(((lab_pix[:, None, :] - lab_gamut[None, :, :]) ** 2)
              .sum(axis=2)).min(axis=1)
  return float(d.mean()), float(np.percentile(d, 95))


def synthetic_region(n=6, cell=1000):
  """A GeoDataFrame region the tests can rely on: an n x n grid of
  squares carrying smooth numeric fields (two gradients, a radial
  bump, a diagonal) plus a categorical land-cover-ish field. Smooth
  fields make classed symbology produce visibly banded maps, which the
  colour-count checks depend on.

  Args:
    n: the grid is n x n squares, so n * n region polygons. Six gives
      36, enough that a five-class scheme fills every class from
      every field, few enough that tiling it stays quick even at the
      finer spacings the weave cases use.
    cell: the side of one square in CRS units, here EPSG:3857 metres.
      1000 against the 300-700 spacings the cases pass to the units
      puts several tile units inside every polygon, so an element's
      colour comes from many polygons and a banding fault shows as a
      pattern rather than as one odd tile.

  Returns:
    A fresh GeoDataFrame in EPSG:3857 (a metric CRS, so spacings read
    as metres) with square geometries and five attribute columns: va
    = column index, vb = row index, vc = squared distance from the
    centre (the radial bump), vd = i + j (the diagonal), and
    landcover, one of five class names cycled over the cells. Every
    call builds a new frame; nothing is cached, so a case that
    mutates its region cannot affect another.
  """
  import geopandas as gpd
  import shapely.geometry as geom
  polys, va, vb, vc, vd, cat = [], [], [], [], [], []
  cats = ["forest", "water", "urban", "crops", "wetland"]
  for i in range(n):
    for j in range(n):
      polys.append(geom.box(i * cell, j * cell,
                            (i + 1) * cell, (j + 1) * cell))
      va.append(float(i))
      vb.append(float(j))
      vc.append(float((i - n / 2) ** 2 + (j - n / 2) ** 2))
      vd.append(float(i + j))
      cat.append(cats[(i * n + j) % len(cats)])
  return gpd.GeoDataFrame(
    {"va": va, "vb": vb, "vc": vc, "vd": vd, "landcover": cat},
    geometry=polys, crs="EPSG:3857")


# The canvas colour, as a module constant so that one other caller can
# change it. tools/make_site_images.py renders these same cases onto
# white for the README and the project page: the published pictures
# are then the very maps the suite checks, rather than a second set
# drawn by a second code path that could drift from it. Measurement
# keeps the magenta, for the reason given in render_layers.
BACKGROUND = "#ff00ff"


def render_layers(layers, path, size=700):
  """Draw layers to a PNG without a window, and return the image.

  Args:
    layers: QGIS layers, FIRST drawn on top (QGIS's own convention).
    path: where to write the PNG.
    size: the square canvas edge in pixels. Thin-strand designs need
      more of them: interior-pixel measurements want fills several
      pixels wide, or every pixel is an antialiased edge.

  Returns:
    The QImage, so a caller can measure it without reading the file
    back.
  """
  settings = QgsMapSettings()
  settings.setLayers(layers)
  # chroma-key background: magenta is a colour no map ramp produces,
  # so "background" is an exact test rather than a near-white
  # heuristic — which matters because diverging ramps (RdBu's centre,
  # sequential ramps' pale ends) legitimately produce near-white DATA
  # colours that a white canvas would silently swallow
  settings.setBackgroundColor(QColor(BACKGROUND))
  extent = layers[0].extent()
  for lyr in layers[1:]:
    extent.combineExtentWith(lyr.extent())
  settings.setExtent(extent.buffered(extent.width() * 0.02))
  settings.setOutputSize(QSize(size, size))
  settings.setDestinationCrs(layers[0].crs())
  job = QgsMapRendererParallelJob(settings)
  loop = QEventLoop()
  job.finished.connect(loop.quit)
  job.start()
  loop.exec()
  image = job.renderedImage()
  image.save(path)
  return image


def image_stats(image, sample=120):
  """Coarse image facts on a sample grid: how many distinct colours,
  and what fraction of pixels is the magenta key background.

  These are the blunt checks that catch a blank, monochrome or
  gap-less render; the colourspace criteria in gamut_delta_e are what
  catch a wrong-but-plausible one.

  Args:
    image: a QImage from render_layers, on the chroma-key canvas.
    sample: points to aim for along each edge, giving a stride of
      width // sample. 120 is coarser than sample_pixels uses, which
      is the right trade here: these two numbers are thresholded
      loosely (more than a dozen colours, so much background), so
      paying for a denser grid would buy no extra certainty.

  Returns:
    (colours, background_fraction). ``colours`` counts distinct
    non-background colours after each channel is bucketed in eights
    (32 levels per channel): unlike sample_pixels this grid keeps
    edge blends, and at full precision every antialiased pixel would
    count as its own colour and the number would say nothing. Ramp
    classes differ by far more than one bucket, so real classes still
    count separately. ``background_fraction`` is chroma-key pixels
    over all sampled pixels, which is how the weave and inset cases
    assert that gaps are visible. The image is only read.
  """
  colours, background = set(), 0
  w, h = image.width(), image.height()
  step_x, step_y = max(1, w // sample), max(1, h // sample)
  total = 0
  for x in range(0, w, step_x):
    for y in range(0, h, step_y):
      c = image.pixelColor(x, y)
      if _is_background(c):
        background += 1
      else:
        colours.add((c.red() // 8, c.green() // 8, c.blue() // 8))
      total += 1
  return len(colours), background / max(total, 1)


def _is_background(c):
  """Is this pixel the chroma-key canvas? Near-match, so edge blends
  that are mostly key still read as background."""
  return c.red() > 235 and c.blue() > 235 and c.green() < 20


def tiled_layers(unit, region, assignments, out_dir, name, **tiling_kw):
  """The plugin's own pipeline, minus the dialog: tile the region with
  the unit, split by tile_id, seed renderers, return the layers.

  Going through bridge rather than through TiledMap.render is the
  point of the gallery: what is on trial is the plugin's conversion
  and symbology, with the library's own geometry taken as given.

  Args:
    unit: a weavingspace TileUnit or WeaveUnit, already built with
      its spacing and crs, exactly as the dialog's _build_unit would
      hand one over.
    region: the GeoDataFrame to tile, synthetic_region() in every
      case here.
    assignments: one plugin assignment dict per tile element, in draw
      order; ``grad`` builds the graduated ones. Only the keys
      bridge.seed_renderer reads matter, and ``id`` must match a
      tile_id the unit produces. An element with no tiles in the
      result is skipped rather than becoming an empty layer.
    out_dir: unused. Every call site passes one (None throughout the
      gallery, since these layers are never written to disk); the
      cases keep the argument only because they all spell the call
      the same way.
    name: unused, likewise — a label for the case, not read here.
    tiling_kw: forwarded verbatim to Tiling, so the cases drive the
      same constructor the dialog does; as_icons=True is the only one
      the gallery passes.

  Returns:
    (layers, tiled_gdf). ``layers`` are QGIS memory layers with
    renderers already seeded, in assignment order — which is
    top-to-bottom on the map, since render_layers draws the first
    layer on top. ``tiled_gdf`` is TiledMap.map, the whole tiling
    with its tile_id column, returned so a case can re-split it for
    the unclassed variant without tiling a second time. The layers
    are created only; nothing is added to the QgsProject, so no case
    can leave state behind for the next one.
  """
  from weavingspace import Tiling
  from weavingspace_qgis import bridge
  tm = Tiling(unit, region, **tiling_kw).get_tiled_map()
  layers = []
  for a in assignments:
    sub = tm.map[tm.map["tile_id"] == a["id"]]
    if len(sub) == 0:
      continue
    layer = bridge.gdf_to_layer(sub, f"{a['id']} – {a.get('var')}")
    # The breaks come from the WHOLE region's values (2026-08-14),
    # so the gallery's library-side layers are seeded the same way
    # the plugin seeds its own -- otherwise every graduated case here
    # would compare a map classified once against four subsets
    # classified four ways and report the difference as a defect.
    bridge.seed_renderer(layer, a, None, _region_values(region, a))
    layers.append(layer)
  return layers, tm.map


def grad(aid, var, ramp, scheme="Quantiles", k=5):
  """Shorthand for a graduated assignment dict (see dialog._assignments
  for the full key inventory; only seeding-relevant keys needed here).

  Args:
    aid: the tile element's id ("a", "b", ...), matching a value in
      the tiling's tile_id column.
    var: the region column mapped onto that element ("va".."vd").
    ramp: the colour ramp name, spelled as the plugin installs it in
      QgsStyle and as ramp_gamut looks it up, so a case's assertion
      and its symbology cannot disagree about which ramp is meant.
    scheme: the classification, spelled as the dialog spells it —
      "Quantiles", "Equal intervals", "Natural breaks (Jenks)" or
      "Unclassed". The gallery spreads these across cases on purpose;
      case_twill_gaps and case_grid_punctured say why they cannot use
      the quantile default.
    k: how many classes the scheme cuts.

  Returns:
    A new dict, safe for a case to copy and edit (the unclassed
    variants do exactly that). ``outline`` is always False: an
    outline stroke draws a colour belonging to no ramp through the
    middle of every fill, which would put edge pixels where
    interior-only sampling expects fills and defeat the gamut check.
  """
  return {"id": aid, "var": var, "mode": "Graduated", "ramp": ramp,
          "scheme": scheme, "k": k, "outline": False}


def _region_values(region, assignment):
  """Every value of one element's column, across the whole region.

  Args:
    region: the region GeoDataFrame the map was tiled from, or None.
    assignment: the element's assignment dict; its ``var`` names the
      column.

  Returns:
    A list with one entry per area, or None when there is no region
    or the element carries no such column -- which leaves
    seed_renderer classifying the element's own tiles.

  Graduated breaks are cut once for the whole map rather than per
  element (see bridge.make_graduated_renderer), so a library-side
  layer seeded without this classifies a subset and differs from the
  plugin's map for a reason that is not a defect.
  """
  var = assignment.get("var")
  if region is None or not var or var not in getattr(region, "columns", ()):
    return None
  return list(region[var])


def layers_from_gdf(gdf, assignments, region=None):
  """Split an already-tiled GeoDataFrame into per-element layers with
  seeded renderers (the tail of the plugin pipeline, reusable for the
  unclassed variant without re-tiling).

  Args:
    gdf: an already-tiled frame, the second half of what tiled_layers
      returned, still carrying its tile_id column.
    assignments: the per-element assignment dicts to seed from; an
      element whose id matches no row is skipped, exactly as in
      tiled_layers.

  Returns:
    A list of fresh memory layers in assignment order. Fresh matters:
    the caller keeps its original layers untouched, so a restyled
    variant can be rendered without disturbing the render the case
    already measured. Nothing is added to the QgsProject.
  """
  from weavingspace_qgis import bridge
  layers = []
  for a in assignments:
    sub = gdf[gdf["tile_id"] == a["id"]]
    if len(sub):
      layer = bridge.gdf_to_layer(sub, f"{a['id']} – {a.get('var')}")
      bridge.seed_renderer(layer, a, None, _region_values(region, a))
      layers.append(layer)
  return layers


def render_unclassed_variant(gdf, assignments, png, region=None):
  """Render the same tiling with the GRADUATED elements switched to
  the plugin's Quant: Unclassed style (50 linear intervals), for
  comparison against the web app's continuous default.

  Categorical elements are left categorized on purpose. Running
  qualitative classes up a continuous ramp would assert an order the
  data does not have, and it would compare against nothing: the
  reference render keeps those elements categorical too (the
  comparison passes each case's `categoricals` through). So in a
  mixed case the "_unclassed" file means "continuous where continuous
  makes sense", not "everything ramped".

  Args:
    gdf: the tiled frame the case already measured, re-split here
      rather than re-tiled, so the two renders differ in symbology
      alone and any difference the comparison finds is a difference
      in classing.
    assignments: the case's own assignments; the Graduated ones are
      copied with scheme "Unclassed" and k 50, and everything else is
      passed through as it stands.
    png: where to write the variant, by convention the case's own
      path with "_unclassed" before the extension, since
      tools/visual_reference_report.py finds these by that name.
    region: the region the map was tiled from. Unclassed is fifty
      equal intervals over the column's range, and that range is
      taken across the WHOLE map rather than per element (2026-08-14)
      -- so without this an element that missed the largest value
      would spread its ramp over a shorter range and the same colour
      would mean two things.

  Returns:
    None. The side effect is the PNG; the assignments handed in are
    not modified (the variant is built from copies), and no layer
    outlives the call.
  """
  variant = [dict(a, scheme="Unclassed", k=50)
             if a.get("mode") == "Graduated" else a for a in assignments]
  # Every gallery case tiles the SAME fixture (see tiled_layers), so
  # defaulting to it here keeps the eleven call sites unchanged while
  # still cutting the ramp's range across the whole map rather than
  # per element. A caller tiling something else passes its own.
  render_layers(
    layers_from_gdf(gdf, variant,
                    synthetic_region() if region is None else region),
    png)


def check(name, fn, out_dir):
  """Run one visual case; record pass/fail, timing, and its PNG.

  Args:
    name: the case's title as the report and the console show it;
      spaces become underscores in the PNG's filename, so two cases
      must not differ by spacing alone.
    fn: the case function. It takes the PNG path, draws and measures
      the map, and returns a short detail string for the report;
      failure reaches here as an exception, since the cases assert
      their criteria rather than returning a verdict.
    out_dir: the release's report directory (reports/v<version>),
      where the PNG is written beside index.html.

  Returns:
    None. Appends one dict to the module-level RESULTS, which
    write_report and main both read afterwards. Every case is
    recorded whether it passed or not: a failure here is a result to
    publish, not a reason to stop, so one broken case still leaves a
    gallery showing the other twelve. A case that raised before
    saving anything records png=None, and the report simply shows no
    image for it.

  The exception is caught broadly on purpose. A case can fail through
  an assertion, through the library, or through QGIS refusing an
  operation, and all three are the same news to a reader of the
  report; the traceback is kept (limit=3, enough to name the failing
  assertion and its caller) as the detail so nothing is swallowed.
  """
  png = os.path.join(out_dir, name.replace(" ", "_") + ".png")
  t0 = time.perf_counter()
  try:
    detail = fn(png)
    RESULTS.append(dict(name=name, ok=True, detail=detail or "",
                        seconds=time.perf_counter() - t0,
                        png=png if os.path.exists(png) else None))
    print(f"PASS  {name} :: {detail or ''}")
  except Exception:
    RESULTS.append(dict(name=name, ok=False,
                        detail=traceback.format_exc(limit=3),
                        seconds=time.perf_counter() - t0,
                        png=png if os.path.exists(png) else None))
    print(f"FAIL  {name}")
    traceback.print_exc()


# ---------------------------------------------------------------- the cases

def case_laves(png):
  """The paper's favourite: Laves 3.3.4.3.4 (Cairo-adjacent), four
  variables on four distinct sequential ramps."""
  from weavingspace import TileUnit
  unit = TileUnit(tiling_type="laves", code="3.3.4.3.4",
                  spacing=500, crs=3857)
  layers, gdf = tiled_layers(
    unit, synthetic_region(),
    [grad(*args) for args in
     (("a", "va", "Reds"), ("b", "vb", "Blues"),
      ("c", "vc", "Greens"), ("d", "vd", "Purples"))],
    None, "laves")
  assert sorted(set(gdf["tile_id"])) == ["a", "b", "c", "d"]
  image = render_layers(layers, png)
  colours, background = image_stats(image)
  # four ramps x five classes should read as a rich, near-space-filling
  # pattern: many colours, little background inside the frame
  assert colours > 12, f"only {colours} colours"
  assert background < 0.45, f"{background:.0%} background"
  # colourspace: every pixel must be explainable by the four ramps
  mean_de, p95_de = gamut_delta_e(
    image, ["Reds", "Blues", "Greens", "Purples"])
  assert mean_de < 1.5 and p95_de < 4, \
    f"pixels off the assigned ramps (dE mean {mean_de:.1f}, "\
    f"p95 {p95_de:.1f})"
  render_unclassed_variant(
    gdf, [grad(*args) for args in
          (("a", "va", "Reds"), ("b", "vb", "Blues"),
           ("c", "vc", "Greens"), ("d", "vd", "Purples"))],
    png.replace(".png", "_unclassed.png"))
  return (f"{len(gdf)} tiles, {colours} colours, "
          f"ramp dE mean {mean_de:.1f}/p95 {p95_de:.1f}")


def case_twill_gaps(png):
  """A twill weave with strand skips and aspect < 1: the weave look
  depends on the gaps, so the background must show through inside the
  pattern (this is what the aspect control and '-' skips are *for*)."""
  from weavingspace import WeaveUnit
  unit = WeaveUnit(weave_type="twill", n=(1, 2), strands="ab-|cd-",
                   aspect=0.75, spacing=300, crs=3857)
  # equal intervals, deliberately: QGIS and mapclassify draw quantile
  # bin edges by different conventions on tie-heavy data, and this is
  # the one case where that shows — gapped strands subsample the
  # region, so not every class appears and the visible-class SET can
  # differ between renderers. Equal-interval breaks are min-max
  # arithmetic, identical in both; quantile conventions stay covered
  # by the fully-visible cases (laves, hex-colouring, ...).
  layers, gdf = tiled_layers(
    unit, synthetic_region(),
    [grad(a, v, r, scheme="Equal intervals") for a, v, r in
     (("a", "va", "Reds"), ("b", "vb", "Blues"),
      ("c", "vc", "Greens"), ("d", "vd", "Purples"))],
    None, "twill")
  # thin diagonal strands: render larger so interior-only
  # sampling sees true fills, not flat blend gradients
  image = render_layers(layers, png, size=1100)
  colours, background = image_stats(image)
  assert background > 0.10, \
    f"no weave gaps visible ({background:.0%} background)"
  assert colours > 10, f"only {colours} colours"
  mean_de, p95_de = gamut_delta_e(
    image, ["Reds", "Blues", "Greens", "Purples"])
  assert mean_de < 1.5 and p95_de < 4, \
    f"pixels off the assigned ramps (dE mean {mean_de:.1f}, "\
    f"p95 {p95_de:.1f})"
  render_unclassed_variant(
    gdf, [grad(*args) for args in
          (("a", "va", "Reds"), ("b", "vb", "Blues"),
           ("c", "vc", "Greens"), ("d", "vd", "Purples"))],
    png.replace(".png", "_unclassed.png"))
  return (f"{len(gdf)} strand pieces, {background:.0%} gaps, "
          f"ramp dE mean {mean_de:.1f}")


def case_shared_ramp(png):
  """The paper's 'out-of-step detector': hex-colouring 7 with every
  element on ONE shared ramp (Reds), so agreement reads as a single
  hue family; the check is that nearly all non-background pixels are
  red-dominant."""
  from weavingspace import TileUnit
  unit = TileUnit(tiling_type="hex-col", n=7, spacing=600, crs=3857)
  assignments = [grad(aid, var, "Reds") for aid, var in
                 zip("abcdefg", ["va", "vb", "vc", "vd", "va", "vb", "vc"])]
  layers, gdf = tiled_layers(unit, synthetic_region(), assignments,
                             None, "shared")
  assert len(set(gdf["tile_id"])) == 7
  image = render_layers(layers, png)
  # colourspace form of the shared-ramp property: with ONE ramp
  # assigned everywhere, every pixel must sit near the Reds gamut;
  # a stray second ramp shows up as a large p95 immediately
  mean_de, p95_de = gamut_delta_e(image, ["Reds"])
  assert mean_de < 1.5 and p95_de < 4, \
    f"map strays off the single shared ramp (dE mean {mean_de:.1f}, "\
    f"p95 {p95_de:.1f})"
  render_unclassed_variant(
    gdf, assignments, png.replace(".png", "_unclassed.png"))
  return (f"7 elements, one ramp, dE to Reds gamut mean "
          f"{mean_de:.1f}/p95 {p95_de:.1f}")


def case_categorized(png):
  """Categorical symbology (the plugin's ground the web app lacks):
  land-cover classes on one element of a square slice, checked for one
  colour per class."""
  from weavingspace import TileUnit
  from weavingspace_qgis import bridge
  unit = TileUnit(tiling_type="square-slice", n=4, offset=0,
                  spacing=700, crs=3857)
  assignments = [
    {"id": "a", "var": "landcover", "mode": "Categorized",
     "ramp": "tab10", "outline": False},
    grad("b", "va", "Blues"), grad("c", "vb", "Greens"),
    grad("d", "vd", "Purples")]
  layers, gdf = tiled_layers(unit, synthetic_region(), assignments,
                             None, "categorized")
  from qgis.core import QgsCategorizedSymbolRenderer
  cat_layer = layers[0]
  renderer = cat_layer.renderer()
  assert isinstance(renderer, QgsCategorizedSymbolRenderer)
  labels = [c.label() for c in renderer.categories()]
  assert "forest" in labels and "no data" in labels
  image = render_layers(layers, png)
  colours, _ = image_stats(image)
  assert colours > 10, f"only {colours} colours"
  mean_de, p95_de = gamut_delta_e(
    image, ["tab10", "Blues", "Greens", "Purples"])
  assert mean_de < 1.5 and p95_de < 4, \
    f"pixels off the assigned palettes (dE mean {mean_de:.1f}, "\
    f"p95 {p95_de:.1f})"
  # the unclassed variant must leave THIS element categorized: a
  # continuous ramp over land-cover classes would invent an order
  variant = [dict(a, scheme="Unclassed", k=50)
             if a.get("mode") == "Graduated" else a for a in assignments]
  variant_layers = layers_from_gdf(gdf, variant)
  assert isinstance(variant_layers[0].renderer(),
                    QgsCategorizedSymbolRenderer), \
    "qualitative data must stay categorized in the unclassed variant"
  render_unclassed_variant(
    gdf, assignments, png.replace(".png", "_unclassed.png"))
  return (f"classes: {', '.join(sorted(set(labels) - {'no data'}))}; "
          f"dE mean {mean_de:.1f}")


def case_modifiers(png):
  """The notebook's modifier chain: rotate 30, inset the prototile and
  the tiles. Insetting opens gaps between and within units, so the
  background fraction must rise relative to the un-inset Laves case."""
  from weavingspace import TileUnit
  unit = TileUnit(tiling_type="laves", code="3.3.4.3.4",
                  spacing=500, crs=3857) \
    .transform_rotate(30).inset_prototile(40).inset_tiles(10)
  layers, gdf = tiled_layers(
    unit, synthetic_region(),
    [grad(*args) for args in
     (("a", "va", "Reds"), ("b", "vb", "Blues"),
      ("c", "vc", "Greens"), ("d", "vd", "Purples"))],
    None, "modifiers")
  image = render_layers(layers, png)
  colours, background = image_stats(image)
  # the modifier chain must not change WHICH colours appear, only
  # where: same gamut criterion as the un-inset cases
  mean_de, p95_de = gamut_delta_e(
    image, ["Reds", "Blues", "Greens", "Purples"])
  assert mean_de < 1.5 and p95_de < 4, \
    f"pixels off the assigned palettes (dE mean {mean_de:.1f}, "\
    f"p95 {p95_de:.1f})"
  assert background > 0.08, \
    f"insets not visible ({background:.0%} background)"
  render_unclassed_variant(
    gdf, [grad(*args) for args in
          (("a", "va", "Reds"), ("b", "vb", "Blues"),
           ("c", "vc", "Greens"), ("d", "vd", "Purples"))],
    png.replace(".png", "_unclassed.png"))
  return f"rotated + inset, {background:.0%} gaps"


def case_icons(png):
  """Icon mode (as_icons=True): one tileable per region polygon at its
  centre, so the tile count is bounded by polygons x unit size and
  plenty of background remains between icons."""
  from weavingspace import TileUnit
  unit = TileUnit(tiling_type="hex-col", n=4, spacing=400, crs=3857)
  region = synthetic_region()
  layers, gdf = tiled_layers(
    unit, region,
    [grad(*args) for args in
     (("a", "va", "Reds"), ("b", "vb", "Blues"),
      ("c", "vc", "Greens"), ("d", "vd", "Purples"))],
    None, "icons", as_icons=True)
  assert len(gdf) <= len(region) * len(unit.tiles) * 2, "too many tiles"
  image = render_layers(layers, png)
  colours, background = image_stats(image)
  assert background > 0.3, f"icons filled the map ({background:.0%} bg)"
  render_unclassed_variant(
    gdf, [grad(*args) for args in
          (("a", "va", "Reds"), ("b", "vb", "Blues"),
           ("c", "vc", "Greens"), ("d", "vd", "Purples"))],
    png.replace(".png", "_unclassed.png"))
  return f"{len(gdf)} tiles as icons"


def case_hex_slice_offset(png):
  """The slice family with a non-default offset: a hexagon cut into
  six pie slices starting from edge midpoints (offset=1) rather than
  corners. Checks the offset control actually reaches the geometry:
  with six elements on six distinct ramps the map must be rich and
  space-filling, and every colour on-ramp."""
  from weavingspace import TileUnit
  unit = TileUnit(tiling_type="hex-slice", n=6, offset=1,
                  spacing=600, crs=3857)
  ramps = ["Reds", "Blues", "Greens", "Purples", "Oranges", "Greys"]
  # equal intervals rather than quantiles: the release comparison
  # judges each case under its own declared style, so the gallery
  # spreads styles across cases instead of testing quantiles six ways
  assignments = [grad(aid, var, ramp, scheme="Equal intervals")
                 for aid, var, ramp in
                 zip("abcdef", ["va", "vb", "vc", "vd", "va", "vb"],
                     ramps)]
  layers, gdf = tiled_layers(unit, synthetic_region(), assignments,
                             None, "hexslice")
  assert len(set(gdf["tile_id"])) == 6
  image = render_layers(layers, png)
  colours, background = image_stats(image)
  assert colours > 15, f"only {colours} colours"
  assert background < 0.4, f"{background:.0%} background"
  mean_de, p95_de = gamut_delta_e(image, ramps)
  assert mean_de < 1.5 and p95_de < 4, \
    f"pixels off the assigned ramps (dE mean {mean_de:.1f})"
  render_unclassed_variant(gdf, assignments,
                           png.replace(".png", "_unclassed.png"))
  return f"6 slices, {colours} colours, ramp dE mean {mean_de:.1f}"


def case_basket(png):
  """A basket weave (the other biaxial weave type the catalogue leans
  on): 2x2 over-under with slight gaps; checks the basket matrix path
  and that gaps and ramps behave as in the twill case."""
  from weavingspace import WeaveUnit
  unit = WeaveUnit(weave_type="basket", n=2, strands="ab|cd",
                   aspect=0.85, spacing=350, crs=3857)
  assignments = [grad(a, v, r, scheme="Natural breaks (Jenks)")
                 for a, v, r in
                 (("a", "va", "Reds"), ("b", "vb", "Blues"),
                  ("c", "vc", "Greens"), ("d", "vd", "Purples"))]
  layers, gdf = tiled_layers(unit, synthetic_region(), assignments,
                             None, "basket")
  image = render_layers(layers, png)
  colours, background = image_stats(image)
  assert 0.03 < background < 0.5, f"{background:.0%} background"
  mean_de, p95_de = gamut_delta_e(
    image, ["Reds", "Blues", "Greens", "Purples"])
  assert mean_de < 1.5 and p95_de < 4, \
    f"pixels off the assigned ramps (dE mean {mean_de:.1f})"
  render_unclassed_variant(gdf, assignments,
                           png.replace(".png", "_unclassed.png"))
  return f"{len(gdf)} pieces, {background:.0%} gaps, dE {mean_de:.1f}"


def case_grid_punctured(png):
  """The grid family (a library extra beyond the web app's catalogue):
  five elements on a 2 x 3 array, so one cell per unit stays open —
  the punctured form is deliberate library behaviour (the first n
  cells are filled) and the openings must show as background."""
  from weavingspace import TileUnit
  unit = TileUnit(tiling_type="grid", n=5, nrows=2, ncols=3,
                  spacing=600, crs=3857)
  ramps = ["Reds", "Blues", "Greens", "Purples", "Oranges"]
  # equal intervals for the same reason as the twill case: the open
  # cell subsamples the region, and QGIS and mapclassify break
  # quantile ties differently, which would change the visible-class
  # set. Quantiles stay covered by the space-filling cases.
  assignments = [grad(a, v, r, scheme="Equal intervals")
                 for a, v, r in
                 zip("abcde", ["va", "vb", "vc", "vd", "va"], ramps)]
  layers, gdf = tiled_layers(unit, synthetic_region(), assignments,
                             None, "grid")
  assert set(gdf["tile_id"]) == set("abcde")
  image = render_layers(layers, png)
  colours, background = image_stats(image)
  assert colours > 12, f"only {colours} colours"
  assert background > 0.06, \
    f"the empty sixth cell must show through ({background:.0%} bg)"
  mean_de, p95_de = gamut_delta_e(image, ramps)
  assert mean_de < 1.5 and p95_de < 4, \
    f"pixels off the assigned ramps (dE mean {mean_de:.1f})"
  render_unclassed_variant(gdf, assignments,
                           png.replace(".png", "_unclassed.png"))
  return (f"5 of 6 cells filled, {background:.0%} background, "
          f"ramp dE mean {mean_de:.1f}")


def case_stripes(png):
  """The stripes family (the other library extra): four parallel
  bands per unit. The bands are straight and axis-aligned, so this
  also pins the degenerate-geometry end of the tiling code."""
  from weavingspace import TileUnit
  unit = TileUnit(tiling_type="stripes", n=4, spacing=600, crs=3857)
  ramps = ["Reds", "Blues", "Greens", "Purples"]
  assignments = [grad(a, v, r) for a, v, r in
                 zip("abcd", ["va", "vb", "vc", "vd"], ramps)]
  layers, gdf = tiled_layers(unit, synthetic_region(), assignments,
                             None, "stripes")
  assert set(gdf["tile_id"]) == set("abcd")
  image = render_layers(layers, png)
  colours, background = image_stats(image)
  assert colours > 12, f"only {colours} colours"
  assert background < 0.35, f"{background:.0%} background"
  mean_de, p95_de = gamut_delta_e(image, ramps)
  assert mean_de < 1.5 and p95_de < 4, \
    f"pixels off the assigned ramps (dE mean {mean_de:.1f})"
  render_unclassed_variant(gdf, assignments,
                           png.replace(".png", "_unclassed.png"))
  return f"4 bands, {colours} colours, ramp dE mean {mean_de:.1f}"


def case_diverging(png):
  """Diverging ramps (RdBu, PiYG): the palette family for values with
  a meaningful midpoint; checks the diverging entries of the palette
  set survive the ramp installation and seeding paths."""
  from weavingspace import TileUnit
  unit = TileUnit(tiling_type="laves", code="4.8.8",
                  spacing=550, crs=3857)
  assignments = [grad(aid, var, ramp) for aid, var, ramp in
                 zip("abcd", ["vc", "vd", "va", "vb"],
                     ["RdBu", "PiYG", "PuOr", "Spectral"])]
  layers, gdf = tiled_layers(unit, synthetic_region(), assignments,
                             None, "diverging")
  image = render_layers(layers, png)
  colours, background = image_stats(image)
  assert colours > 12, f"only {colours} colours"
  mean_de, p95_de = gamut_delta_e(
    image, ["RdBu", "PiYG", "PuOr", "Spectral"])
  assert mean_de < 1.5 and p95_de < 4, \
    f"pixels off the diverging ramps (dE mean {mean_de:.1f})"
  render_unclassed_variant(gdf, assignments,
                           png.replace(".png", "_unclassed.png"))
  return f"diverging ramps, {colours} colours, dE mean {mean_de:.1f}"


def case_qml_template(png):
  """A class scheme supplied as a template (the QML/donor-layer path)
  must put its EXACT colours on the map: build a template with three
  unmistakable colours, seed a categorized element from it, and check
  each appears in the render within a tight Delta-E."""
  import numpy as np
  from weavingspace import TileUnit
  from weavingspace_qgis import bridge
  from qgis.core import QgsFillSymbol
  target_hex = {"forest": "#123456", "water": "#a05e0c",
                "urban": "#0c7d5a"}
  template = {value: (QgsFillSymbol.createSimple({"color": colour,
                                                  "outline_style": "no"}),
                      value)
              for value, colour in target_hex.items()}
  unit = TileUnit(tiling_type="square-slice", n=4, offset=0,
                  spacing=700, crs=3857)
  from weavingspace import Tiling
  tm = Tiling(unit, synthetic_region()).get_tiled_map()
  assignments = [
    {"id": "a", "var": "landcover", "mode": "Categorized",
     "ramp": "tab10", "outline": False},
    grad("b", "va", "Blues"), grad("c", "vb", "Greens"),
    grad("d", "vd", "Purples")]
  layers = []
  for a in assignments:
    sub = tm.map[tm.map["tile_id"] == a["id"]]
    layer = bridge.gdf_to_layer(sub, a["id"])
    bridge.seed_renderer(layer, a,
                         template if a["id"] == "a" else None)
    layers.append(layer)
  image = render_layers(layers, png)
  pixels = sample_pixels(image)
  lab_pix = srgb_to_lab(pixels)
  for value, colour in target_hex.items():
    rgb = [[int(colour[i:i + 2], 16) for i in (1, 3, 5)]]
    lab_target = srgb_to_lab(np.array(rgb, dtype=float))
    nearest = np.sqrt(((lab_pix - lab_target) ** 2).sum(axis=1)).min()
    assert nearest < 2.5, \
      f"template colour {colour} ({value}) absent from render " \
      f"(nearest dE {nearest:.1f})"
  return f"template colours {', '.join(target_hex.values())} all on map"


def case_size_guard(png):
  """What was learned the hard way: pathological spacings must be
  refused before they reach GEOS. No image for this one."""
  from weavingspace import TileUnit
  from weavingspace_qgis import bridge
  unit = TileUnit(tiling_type="cairo", spacing=10, crs=3857)
  est = bridge.estimate_tile_count_bounds(unit, (0, 0, 100_000, 100_000))
  assert est > bridge.MAX_TILES_HARD
  spacing = bridge.min_reasonable_spacing(unit, synthetic_region(), 10)
  assert spacing > 10
  return f"estimate {est:,} blocked; suggested spacing {spacing:,.0f}"


# ------------------------------------------------------------------ report

def plugin_version():
  """The version this run belongs to, read from metadata.txt.

  Returns:
    The version string ("1.4.0"), or "unknown" when the file carries
    no version= line. Nothing is written.

  metadata.txt is the single place the version lives — QGIS's plugin
  manager reads that same file — so it is parsed here rather than
  duplicated. The parse is deliberately a line scan instead of a
  ConfigParser: this runs under QGIS's Python before anything else is
  known to be importable, and the file is a flat list of key=value.
  A missing version yields "unknown" rather than raising, so a
  metadata fault costs a badly named report directory and not the
  whole gallery.
  """
  meta = os.path.join(ROOT, "weavingspace_qgis", "metadata.txt")
  with open(meta, encoding="utf-8") as f:
    for line in f:
      if line.startswith("version="):
        return line.split("=", 1)[1].strip()
  return "unknown"


def write_report(out_dir, functional_summary=""):
  """One self-contained HTML page per release: environment, functional
  summary (passed in by release.py), and the visual gallery with PNGs
  embedded as data URIs so the file has no side-car dependencies.

  Args:
    out_dir: the release's report directory, where index.html is
      written and where the PNGs already sit.
    functional_summary: the PASS/FAIL tail of the functional suite,
      which release.py captured and left in functional.txt; main
      reads it back and passes it here. Empty when the gallery is run
      by hand, in which case the page simply shows an empty
      functional section rather than pretending the suite passed.

  Returns:
    The path of the page written. The RESULTS list is read, not
    changed, so calling this twice writes the same page twice.

  The PNGs are inlined as base64 data URIs rather than referenced, so
  the page survives being copied or attached to a GitHub Release on
  its own — a report whose pictures depend on neighbouring files
  loses them the first time someone moves it. The cost is roughly a
  third more bytes per image, which is why reports/ is not committed.
  """
  version = plugin_version()
  rows = []
  for r in RESULTS:
    img = ""
    if r["png"] and os.path.exists(r["png"]):
      data = base64.b64encode(open(r["png"], "rb").read()).decode()
      img = (f'<img src="data:image/png;base64,{data}" '
             'style="max-width:340px">')
    status = "PASS" if r["ok"] else "FAIL"
    rows.append(
      f'<tr class="{status.lower()}"><td>{status}</td>'
      f'<td>{html.escape(r["name"])}</td>'
      f'<td>{html.escape(r["detail"])}</td>'
      f'<td>{r["seconds"]:.1f}s</td><td>{img}</td></tr>')
  ok = sum(1 for r in RESULTS if r["ok"])
  page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>WeavingSpace release report v{version}</title>
<style>
body {{ font: 14px/1.5 system-ui, sans-serif; margin: 24px; }}
table {{ border-collapse: collapse; }}
td {{ border: 1px solid #ccc; padding: 6px 10px; vertical-align: top; }}
tr.pass td:first-child {{ background: #d7ecd9; }}
tr.fail td:first-child {{ background: #f3c9c9; }}
pre {{ white-space: pre-wrap; }}
</style></head><body>
<h1>WeavingSpace release report — v{version}</h1>
<p>{time.strftime('%Y-%m-%d %H:%M')} · Python {sys.version.split()[0]}
· visual: {ok}/{len(RESULTS)} passed</p>
<h2>Functional suite</h2><pre>{html.escape(functional_summary)}</pre>
<h2>Visual gallery</h2>
<table><tr><td></td><td>case</td><td>detail</td><td>time</td>
<td>render</td></tr>{''.join(rows)}</table>
</body></html>"""
  path = os.path.join(out_dir, "index.html")
  with open(path, "w", encoding="utf-8") as f:
    f.write(page)
  return path


def main():
  """Run every case under a headless QGIS and write the release report.

  Returns:
    Nothing; exits the process, 0 when every case passed and 1 when
    any failed, which is the signal release.py gates on. Writes one
    PNG per case (two for the numeric ones, counting the unclassed
    variant) plus index.html into reports/v<version>/, and installs
    the plugin's ramps into this process's QgsStyle.

  QGIS has to be started by hand here because this is a plain script,
  not a plugin running inside the application: setPrefixPath tells
  the libraries where their resources live (QGIS_PREFIX_PATH is set
  by the launcher script, since it differs per platform and per
  install), and initQgis loads the providers a memory layer needs.
  The QgsApplication is constructed with GUI enabled — the second
  argument — because the renderer wants a QPainter and Qt's font
  machinery; QT_QPA_PLATFORM=offscreen keeps it from needing a
  display. exitQgis at the end releases those providers cleanly.

  Ramps are installed before any case runs: seed_renderer looks its
  ramp up by name in QgsStyle, so without this every graduated
  element would fall back and every colourspace check would fail for
  one shared reason, hiding whatever the cases were actually meant to
  find.
  """
  QgsApplication.setPrefixPath(
    os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  app = QgsApplication([], True)
  app.initQgis()

  out_dir = os.path.join(ROOT, "reports", f"v{plugin_version()}")
  os.makedirs(out_dir, exist_ok=True)

  from weavingspace_qgis import bridge
  bridge.ensure_ramps_installed()

  check("laves 3.3.4.3.4 four variables", case_laves, out_dir)
  check("twill weave with gaps", case_twill_gaps, out_dir)
  check("hex-colouring 7 shared ramp", case_shared_ramp, out_dir)
  check("categorized land cover", case_categorized, out_dir)
  check("rotate and insets", case_modifiers, out_dir)
  check("tileable as icons", case_icons, out_dir)
  check("hex-slice with offset", case_hex_slice_offset, out_dir)
  check("basket weave", case_basket, out_dir)
  check("grid with an open cell", case_grid_punctured, out_dir)
  check("stripes", case_stripes, out_dir)
  check("diverging ramps", case_diverging, out_dir)
  check("QML template colours on map", case_qml_template, out_dir)
  check("size guard", case_size_guard, out_dir)

  functional = ""
  summary_file = os.path.join(out_dir, "functional.txt")
  if os.path.exists(summary_file):
    functional = open(summary_file, encoding="utf-8").read()
  report_path = write_report(out_dir, functional)

  failed = [r["name"] for r in RESULTS if not r["ok"]]
  print(f"\nvisual: {len(RESULTS) - len(failed)} passed, "
        f"{len(failed)} failed")
  print(f"report: {report_path}")
  app.exitQgis()
  sys.exit(1 if failed else 0)


if __name__ == "__main__":
  main()
