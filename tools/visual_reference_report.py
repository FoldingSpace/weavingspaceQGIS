#!/usr/bin/env python3
"""Build a PDF comparing the visual-gallery renders to their reference.

Usage (from the repo root, in a Python that has geopandas AND
matplotlib — QGIS's own Python cannot be used, see below):

    python3 tools/visual_reference_report.py [reports/vX.Y.Z]

"What the renders should have been" is defined here as the output of
weavingspace's *own* matplotlib renderer (``TiledMap.render``), run on
the very same tile units, synthetic region, variables, and colour
ramps as the plugin's gallery cases. This is simultaneously the web
app's ground truth: MapWeaver runs this library (pinned at 0.0.7.59,
pinned) inside pyodide and draws through this same render call, so the
reference column shows what the web app would draw for these inputs,
without the browser in the loop. Each PDF page shows the reference beside the plugin's QGIS
render, with the case's acceptance criterion and the measured detail
from the gallery run underneath.

Beyond the pictures, each case is scored quantitatively in CIELAB
colourspace (Delta-E, the perceptual colour difference; ~2 is barely
noticeable): the two images' colour palettes are compared by mean
nearest-neighbour Delta-E in both directions (plugin colours must
exist in the reference and vice versa), and their content background
fractions are compared after cropping to content. Each case is scored
TWICE and both must pass. First for style fidelity, against a
reference classed the SAME way the case is -- quantiles judged as
quantiles, equal intervals as equal intervals, categorized as
categorical -- so every style the gallery uses is genuinely
exercised. Second for web-app parity, where the app's continuous
default is compared against the gallery's Quant: Unclassed render (50
linear intervals; saved as *_unclassed.png), because no classed map
can match a continuous one interior-for-interior. A case failing
EITHER comparison fails the step, and release.py then refuses to
build.

This paragraph said something else until 2026-08-12: that the
reference was always unclassed because mapclassify was absent, and
that the second comparison was a fallback tried only when classing
alone explained a failure. mapclassify is present in
.venv-reference, the reference is classed per case, and both
comparisons are mandatory. The comment beside the code has been
right the whole time.

WHY NOT QGIS'S PYTHON: macOS code-signing (library validation) refuses
to load PyPI wheels' C extensions into the signed QGIS process, so
matplotlib cannot run there; conversely this script needs no QGIS at
all. Run it in any environment where the vendored library works with
matplotlib installed (any virtualenv with geopandas and matplotlib).

Inputs: the plugin's PNGs and index.html from an existing gallery run
(tests/visual_tests.py, normally via release.py) in the report
directory. Output: visual-comparison.pdf in the same directory.
"""

import html
import json
import os
import re
import sys

os.environ.setdefault("MPLBACKEND", "Agg")  # no display needed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))

import warnings
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
import matplotlib.image as mpimg  # noqa: E402
import numpy as np  # noqa: E402

# comparison thresholds, calibrated against a known-good release with
# margin for antialiasing and renderer differences (values there sit
# around 1-3 dE / 0.02-0.06 background): mean nearest-neighbour dE per
# direction, and absolute difference in content background fraction
# Calibrated against interior-only sampling (edge blends excluded on
# both sides). The floor is the quantisation gap: the plugin's Quant:
# Unclassed cuts 50 discrete intervals while the reference ramp is
# truly continuous, so reference in-between colours sit up to half an
# interval from the nearest plugin colour (mean ~2-3, p90 ~4-5 on
# these ramps), plus small QGIS/matplotlib interpolation differences.
# Measured across the gallery (v0.16.x): means 2.1-3.5, p90 3.3-5.4,
# bg diff <= 0.05. Anything past these limits is real colour drift,
# not rendering noise.
MAX_MEAN_DE = 4.0
MAX_P90_DE = 7.0
MAX_BG_DIFF = 0.10


def srgb_to_lab(rgb):
  """sRGB (n x 3, 0..1) to CIELAB (D65); Euclidean distance in Lab
  approximates perceived colour difference (Delta-E 1976)."""
  c = np.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4,
               rgb / 12.92)
  m = np.array([[0.4124564, 0.3575761, 0.1804375],
                [0.2126729, 0.7151522, 0.0721750],
                [0.0193339, 0.1191920, 0.9503041]])
  xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
  f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz),
               xyz / (3 * (6 / 29) ** 2) + 4 / 29)
  return np.stack([116 * f[:, 1] - 16,
                   500 * (f[:, 0] - f[:, 1]),
                   200 * (f[:, 1] - f[:, 2])], axis=1)


def image_colours(path, max_pixels=20000):
  """(pixel Lab colours, unique-bin Lab palette, background fraction).

  The image is cropped to its content bounding box first (the two
  renderers frame their maps differently). Pixels are what one side is
  *weighted* by; the deduplicated 5-bit palette is what the other side
  is matched *against*. Weighting by pixels matters: antialiasing at
  polygon and strand edges creates hundreds of rare blend colours, and
  an unweighted unique-colour comparison lets that sliver of pixels
  dominate the score (a lesson from a visually identical twill pair
  scoring dE 11).

  Args:
    path: a PNG to measure, either the gallery's QGIS render of a
      case or the matplotlib render written by reference_render.
      Both sides must have been drawn on the magenta chroma-key
      canvas, because that is what tells map from background here.
    max_pixels: ceiling on how many interior pixels are kept. It
      bounds the nearest-neighbour search in palette_distance, whose
      cost is pixels x palette entries. Over the ceiling the sample
      is thinned by a constant stride rather than at random, so two
      runs over the same PNG give the same number; the 5-bit palette
      is derived from the thinned sample too, which is why the
      ceiling is set well above what the search needs.

  Returns:
    A tuple (pixels, palette, background_fraction). ``pixels`` is an
    n x 3 array of interior pixel colours in Lab — the side that
    gets weighted. ``palette`` is the same sample deduplicated into
    5-bit-per-channel bins and converted to Lab — the side that gets
    matched against. ``background_fraction`` is the share of the
    content-cropped image that is canvas, 0 to 1. Nothing is
    mutated; the file is only read.

  Raises:
    AssertionError: fewer than 100 pixels survived the
      uniform-neighbour filter, meaning the render is too small or
      too finely detailed for an interior-only metric to say
      anything. The fix is a larger dpi for that case (as the twill
      case already does), not a looser filter, since loosening it
      would let antialiased edge blends back into the sample and
      raise the noise floor for every case.
  """
  rgb = mpimg.imread(path)[:, :, :3]

  def is_canvas(a):
    # the magenta chroma key both renderers draw on (near-match, so
    # mostly-key edge blends count as background too)
    return (a[:, :, 0] > 0.92) & (a[:, :, 2] > 0.92) & (a[:, :, 1] < 0.08)

  content = ~is_canvas(rgb)
  rows, cols = np.any(content, axis=1), np.any(content, axis=0)
  rgb = rgb[np.argmax(rows):len(rows) - np.argmax(rows[::-1]),
            np.argmax(cols):len(cols) - np.argmax(cols[::-1])]
  content = ~is_canvas(rgb)
  background_fraction = 1.0 - content.mean()
  # measure only the pixels that matter: interior fills. A pixel
  # counts when its four neighbours agree with it (within a small
  # per-channel tolerance), which excludes the antialiased edge
  # pixels both renderers create along polygon and strand borders.
  # Those blends are rendering artifacts, not symbology, and with
  # them in the sample identical maps score dE ~2-4 (noise floor);
  # interior-only, identical symbology scores near zero, so the
  # thresholds can sit low enough that any real colour drift is an
  # unambiguous failure rather than a judgement call.
  core = rgb[1:-1, 1:-1]
  uniform = np.ones(core.shape[:2], dtype=bool)
  for dy, dx in ((0, 1), (2, 1), (1, 0), (1, 2)):
    shifted = rgb[dy:dy + core.shape[0], dx:dx + core.shape[1]]
    uniform &= np.abs(core - shifted).max(axis=2) <= (8 / 255)
  mask = uniform & ~is_canvas(core)
  pixels = core[mask]
  if len(pixels) < 100:
    raise AssertionError(
      f"{path}: only {len(pixels)} interior pixels — the render is "
      "too small or too busy for the interior-only metric; raise the "
      "render size for this case rather than loosening the filter")
  if len(pixels) > max_pixels:
    pixels = pixels[:: len(pixels) // max_pixels + 1]
  bins = np.unique((pixels * 31).astype(np.uint8), axis=0)
  return (srgb_to_lab(pixels), srgb_to_lab(bins / 31.0),
          float(background_fraction))


def palette_distance(path_a, path_b):
  """Pixel-weighted colour comparison of two renders: for each image,
  every sampled pixel's Delta-E to the nearest colour the *other*
  image contains, summarised as mean and 90th percentile, plus the
  background-fraction difference. Direction matters: a 5-class map's
  colours all lie on the continuous reference ramp (small a->b) while
  the reference's in-between colours are missing from it (large
  b->a) — exactly the signature the unclassed fallback exists for.

  Args:
    path_a: the PNG that supplies the "a" side of the returned
      numbers. compare() passes the PLUGIN render here, so a_to_b
      reads plugin-to-reference in the printed lines and the PDF.
    path_b: the PNG that supplies the "b" side; compare() passes the
      reference render written by reference_render.

  Returns:
    A dict of five floats, all measurements over the two files with
    nothing mutated: ``a_to_b`` and ``b_to_a``, the mean Delta-E
    from each image's sampled pixels to the nearest colour the other
    image contains; ``p90_a`` and ``p90_b``, the 90th percentile of
    those same two distance sets, which catches a small area of
    badly wrong colour that a mean would absorb; and ``bg_diff``,
    the absolute difference in content background fraction, which is
    how a lost or an extra gap between tiles shows up even when
    every colour present is correct.
  """
  pix_a, pal_a, bg_a = image_colours(path_a)
  pix_b, pal_b, bg_b = image_colours(path_b)

  def nn(pixels, palette):
    d = np.empty(len(pixels))
    for i in range(0, len(pixels), 4000):  # bounded memory
      chunk = pixels[i:i + 4000]
      d[i:i + len(chunk)] = np.sqrt(
        ((chunk[:, None, :] - palette[None, :, :]) ** 2)
        .sum(axis=2)).min(axis=1)
    return d

  d_ab, d_ba = nn(pix_a, pal_b), nn(pix_b, pal_a)
  return dict(a_to_b=float(d_ab.mean()), b_to_a=float(d_ba.mean()),
              p90_a=float(np.percentile(d_ab, 90)),
              p90_b=float(np.percentile(d_ba, 90)),
              bg_diff=abs(bg_a - bg_b))


def compare(reference_png, plugin_png):
  """Score one reference/plugin pair against the release thresholds.

  Args:
    reference_png: the render written here by reference_render, i.e.
      the original library's own matplotlib output for these inputs.
    plugin_png: the gallery's QGIS render of the same case — either
      the primary classed render or its *_unclassed.png sibling,
      depending on which comparison the caller is making.

  Returns:
    (ok, metrics). ``ok`` is True only when all five numbers sit
    inside MAX_MEAN_DE, MAX_P90_DE and MAX_BG_DIFF; a single number
    over its limit fails the case, and a failed case fails the whole
    step so release.py refuses to build. ``metrics`` is the dict
    from palette_distance, returned whether or not the case passed
    because the printed line and the PDF caption both show the
    measured values beside the limits. Nothing is mutated.

  The arguments are handed to palette_distance the other way round,
  plugin first, so that in the returned dict a_to_b means
  plugin-to-reference and b_to_a means reference-to-plugin. That is
  the direction every caption and printed line names, and getting it
  backwards would silently invert the classing signature the
  unclassed fallback is looking for.
  """
  m = palette_distance(plugin_png, reference_png)
  ok = (m["a_to_b"] <= MAX_MEAN_DE and m["b_to_a"] <= MAX_MEAN_DE
        and m["p90_a"] <= MAX_P90_DE and m["p90_b"] <= MAX_P90_DE
        and m["bg_diff"] <= MAX_BG_DIFF)
  return ok, m


def synthetic_region(n=6, cell=1000):
  """Identical to tests/visual_tests.synthetic_region (duplicated here
  because that module imports qgis at load time and this script must
  run without QGIS): an n x n grid of squares with smooth numeric
  fields and a categorical one.

  Args:
    n: cells per side, so the region is n x n polygons. Six is
      enough for a tiling to repeat several times across the region
      while keeping every case quick to render.
    cell: the side of one cell in the CRS's units (EPSG:3857
      metres). It sits well above the tile spacings used in CASES,
      which is what makes each region polygon carry many tiles
      rather than one — except in the icon case, where that ratio is
      the point.

  Returns:
    A freshly built GeoDataFrame in EPSG:3857 with one row per cell:
    ``va`` and ``vb`` rise along the two axes, ``vc`` is a radial
    bowl about the centre, ``vd`` is their sum, and ``landcover``
    cycles five class names so the categorical case always has every
    class present. Nothing is cached between calls, so one case
    cannot disturb another's region.

  Keeping this in step with tests/visual_tests.synthetic_region is a
  correctness requirement, not tidiness: the two sides of every
  comparison must be drawn from identical data, so a change there
  has to be repeated here.
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


def _reference_bins(region, variables, scheme, k):
  """The breaks a classed reference should use, or None.

  Args:
    region: the region GeoDataFrame the reference is tiled from.
    variables: the column each element maps, by position.
    scheme: the mapclassify scheme name the case asks for.
    k: the class count the case asks for.

  Returns:
    A list of upper bounds for mapclassify's UserDefined scheme, or
    None when this case cannot be given one -- in which case the
    caller falls back to letting TiledMap classify each subset, and
    the comparison carries a known, documented divergence.

  Computed here, over the REGION's values, rather than read off the
  plugin's renderers: a reference told the answer by the thing it is
  checking has stopped being a reference. mapclassify is geopandas'
  own classifier, so this is a second implementation of "quantiles
  over the whole column" and a plugin whose breaks are wrong by
  enough to move a tile still shows up as differing pixels.

  ONE case is refused, and it is a real limit rather than caution:
  mapclassify's bins reach TiledMap through render()'s **kwargs,
  which are broadcast to EVERY element, while _colourspecs carries
  the per-element scheme. So a case whose elements map DIFFERENT
  columns cannot be given one set of bins that is right for all of
  them, and asking for that would silently classify element b's
  column against element a's breaks. Those cases keep the per-subset
  reference; their divergence is bounded by how far a subset's
  quantiles sit from the whole column's, and the PDF shows it.
  """
  columns = {column for column in variables
             if column in getattr(region, "columns", ())
             and str(region[column].dtype) != "object"}
  if len(columns) != 1:
    return None
  column = columns.pop()
  try:
    import mapclassify
  except Exception:
    return None
  method = {"Quantiles": "Quantiles", "EqualInterval": "EqualInterval",
            "NaturalBreaks": "NaturalBreaks"}.get(scheme)
  if method is None:
    return None
  try:
    classifier = getattr(mapclassify, method)(region[column].dropna(), k=k)
    return [float(b) for b in classifier.bins]
  except Exception:
    return None


def reference_render(unit, png, ids, variables, cmaps,
                     categoricals=None, scheme=None, k=None, dpi=110,
                     **tiling_kw):
  """Render one case through the original library's own pipeline:
  Tiling -> TiledMap -> matplotlib figure, saved as a PNG.

  With scheme=None the render is the web app's default: continuous
  (unclassed) ramps. Passing a mapclassify scheme name ("Quantiles",
  "EqualInterval", "NaturalBreaks") and a class count k uses
  TiledMap's own classed path (schemes_to_use/n_classes), so the
  plugin's classed renders can be judged against a reference classed
  the same way rather than always leaning on the Quant: Unclassed
  reproduction.

  Args:
    unit: the tile unit (TileUnit or WeaveUnit) returned by the
      case's ``build`` entry — the same object the gallery tiles, so
      that only the renderer differs between the two sides.
    png: where to write the reference image. Overwritten if present.
    ids: the tile ids to symbolize, in order. A string works,
      "abcd" meaning elements a, b, c and d.
    variables: the region column each id is mapped to, matched to
      ``ids`` by position.
    cmaps: the colourmap for each id, again by position. These are
      matplotlib names ("Reds", "tab10", "RdBu") because this is the
      library's own renderer; the gallery's QGIS side uses the
      equivalently named QgsStyle ramps.
    categoricals: per-id flags marking a variable as qualitative.
      Left None, TiledMap infers it from the column's dtype, which
      is right for every case here except the land-cover one, where
      the flags are given explicitly.
    scheme: a mapclassify scheme name — "Quantiles",
      "EqualInterval" or "NaturalBreaks". Left None the render is
      continuous, which is the unclassed look. A bare string is
      broadcast across every id by TiledMap itself, so there is no
      need to repeat it per element.
    k: the class count to use with ``scheme``; None means 5, which
      matches the gallery's default. Ignored when scheme is None.
    dpi: output resolution. 110 is ample for solid fills, but a case
      whose geometry is thin (the twill's diagonal strands) must
      raise it or image_colours finds too few interior pixels and
      refuses to measure.
    **tiling_kw: passed straight through to Tiling. This is how
      ``as_icons=True`` reaches the icon case, where one unit is
      drawn per region polygon instead of tiled across the region.

  Returns:
    None. The effect is the PNG at ``png``. ``unit`` is not touched,
    but the TiledMap built here is configured in place and then
    discarded with its figure, so nothing leaks into the next case.

  Note the figure is closed explicitly rather than left to garbage
  collection: with a dozen cases and two renders each, matplotlib's
  global figure registry would otherwise hold every one of them open
  and warn about it partway through the run.
  """
  from weavingspace import Tiling
  region = synthetic_region()
  tm = Tiling(unit, region, **tiling_kw).get_tiled_map()
  tm.ids_to_map = list(ids)
  tm.vars_to_map = list(variables)
  tm.colors_to_use = list(cmaps)
  if categoricals is not None:
    tm.categoricals = list(categoricals)
  # ---- ONE CLASSIFICATION FOR THE WHOLE MAP, on both sides
  #
  # TiledMap classifies each element's SUBSET separately:
  # _plot_subsetted_gdf loops over the groups and hands each one to
  # plot() with its own scheme and k. The plugin stopped doing that on
  # 2026-08-14 -- four elements carrying one variable were coming out
  # with four different legends, so the same colour meant four
  # different numbers -- and cuts the breaks once, from the region's
  # values.
  #
  # Left alone, this comparison would therefore measure that
  # deliberate difference on every graduated case and report it as a
  # divergence, which is the fastest way to blunt the sharpest
  # instrument this project has. So the reference is told which
  # breaks to use, and the axis it stops testing is picked up by
  # test_one_variable_gets_one_legend_wherever_it_appears and by
  # QGIS's own classifier being asked the same question directly.
  #
  # Note what this does NOT do: the bins are computed HERE, by
  # mapclassify over the region's values, not read off the plugin's
  # renderers. So the comparison still fails if the plugin's breaks
  # are wrong -- they simply have to be wrong by enough to move a
  # tile into another class, which is exactly the threshold a
  # pixel comparison is fit to judge.
  numeric = [column for column in dict.fromkeys(variables)
             if column in region.columns
             and str(region[column].dtype) != "object"]
  if scheme is not None:
    bins = _reference_bins(region, variables, scheme, k or 5)
    if bins is not None:
      tm.schemes_to_use = "UserDefined"
      tm.n_classes = len(bins)
      kwargs["classification_kwds"] = {"bins": bins}
    else:
      tm.schemes_to_use = scheme  # broadcast to every id by TiledMap
      tm.n_classes = k or 5
  else:
    # The continuous render normalizes over each subset's own range.
    # Ours spreads the ramp over the whole column's range, so the
    # reference is given the same endpoints -- the unclassed twin of
    # the bins above, and the reason TiledMap exposes vmins/vmaxs at
    # all.
    if numeric:
      tm.vmins = [float(region[column].min())
                  if column in numeric else None for column in variables]
      tm.vmaxs = [float(region[column].max())
                  if column in numeric else None for column in variables]
  fig = tm.render(legend=False, figsize=(7, 7))
  # the same magenta chroma-key canvas as the gallery renders: no map
  # ramp produces it, so background detection is exact and near-white
  # data colours (diverging centres, pale sequential ends) are
  # measured instead of being mistaken for canvas
  for ax in fig.axes:
    ax.set_facecolor("#ff00ff")
  fig.savefig(png, dpi=dpi, bbox_inches="tight", facecolor="#ff00ff")
  plt.close(fig)


# One entry per image-producing gallery case, keyed by the case name
# used in tests/visual_tests.py (which also names the plugin's PNG).
# ``build`` returns the tile unit; the remaining fields drive the
# reference render and the caption.
def _laves_unit():
  """Laves 3.3.4.3.4, the Cairo-adjacent tiling the paper leans on:
  four tiles per unit for the four mapped variables, and near
  space-filling, so the comparison sees mostly data colour rather
  than background.
  """
  from weavingspace import TileUnit
  return TileUnit(tiling_type="laves", code="3.3.4.3.4",
                  spacing=500, crs=3857)


def _twill_unit():
  """A 1-over-2 twill whose strand specification skips one strand in
  each direction ("ab-|cd-"); with aspect 0.75 narrowing the strands
  as well, the weave deliberately leaves gaps, which is what makes
  this case a test of background as much as of colour.
  """
  from weavingspace import WeaveUnit
  return WeaveUnit(weave_type="twill", n=(1, 2), strands="ab-|cd-",
                   aspect=0.75, spacing=300, crs=3857)


def _hexcol_unit():
  """Hex-colouring with 7 tiles: the paper's out-of-step detector.
  Seven elements share one ramp here, so whether the variables agree
  or disagree reads as a single hue family across the map.
  """
  from weavingspace import TileUnit
  return TileUnit(tiling_type="hex-col", n=7, spacing=600, crs=3857)


def _slice_unit():
  """A square cut into four slices from its corners (offset=0). Its
  large flat slices give the interior-only metric plenty of pixels,
  which is why this is the carrier for the categorized land-cover
  case rather than a finer geometry.
  """
  from weavingspace import TileUnit
  return TileUnit(tiling_type="square-slice", n=4, offset=0,
                  spacing=700, crs=3857)


def _modified_unit():
  """The modifier chain from the library's notebooks, applied to the
  Laves case: rotate 30 degrees, then inset the prototile and the
  tiles. The insets open gaps between and within units, so this unit
  is expected to score a distinctly higher background fraction than
  the plain Laves one.
  """
  from weavingspace import TileUnit
  return TileUnit(tiling_type="laves", code="3.3.4.3.4",
                  spacing=500, crs=3857) \
    .transform_rotate(30).inset_prototile(40).inset_tiles(10)


def _icon_unit():
  """Hex-colouring with 4 tiles at a small spacing, used with
  ``as_icons=True``: one unit is drawn per region polygon instead of
  tiled across it, so the 400 m spacing against the region's 1000 m
  cells is what leaves visible background between the icons.
  """
  from weavingspace import TileUnit
  return TileUnit(tiling_type="hex-col", n=4, spacing=400, crs=3857)


FOUR = dict(ids="abcd", variables=["va", "vb", "vc", "vd"],
            cmaps=["Reds", "Blues", "Greens", "Purples"])


def _hex_slice_unit():
  """A hexagon cut into six pie slices from the edge midpoints rather
  than the corners (offset=1). The offset is the whole point of the
  case: it is the one control here that changes the geometry without
  changing the family or the count.
  """
  from weavingspace import TileUnit
  return TileUnit(tiling_type="hex-slice", n=6, offset=1,
                  spacing=600, crs=3857)


def _basket_unit():
  """A 2x2 basket weave, the other biaxial weave the catalogue leans
  on. Aspect 0.85 leaves slight gaps between strands, so the case
  exercises the same gap-and-ramp behaviour as the twill through a
  different weave matrix.
  """
  from weavingspace import WeaveUnit
  return WeaveUnit(weave_type="basket", n=2, strands="ab|cd",
                   aspect=0.85, spacing=350, crs=3857)


def _diverging_unit():
  """Laves 4.8.8, octagons with small squares between them, carrying
  the diverging-ramp case. The large octagon tiles give each
  diverging palette enough area to show both arms and its pale
  centre, which is where a mistaken background test would go wrong.
  """
  from weavingspace import TileUnit
  return TileUnit(tiling_type="laves", code="4.8.8",
                  spacing=550, crs=3857)

def _grid_unit():
  """A 2 x 3 grid asked for only 5 elements, so one cell per unit
  stays open. The puncture is deliberate library behaviour (the
  first n cells are filled), and the openings must show up as
  background in the comparison.
  """
  from weavingspace import TileUnit
  return TileUnit(tiling_type="grid", n=5, nrows=2, ncols=3,
                  spacing=600, crs=3857)


def _stripes_unit():
  """Four parallel bands per unit. Stripes is the second of the two
  library extras beyond the catalogue the web app carries, and the
  simplest geometry in the set, which makes it the cleanest colour
  comparison of the lot.
  """
  from weavingspace import TileUnit
  return TileUnit(tiling_type="stripes", n=4, spacing=600, crs=3857)


CASES = [
  dict(name="laves 3.3.4.3.4 four variables", build=_laves_unit,
       criterion="4 elements on 4 sequential ramps; near space-filling",
       **FOUR),
  dict(name="twill weave with gaps", build=_twill_unit,
       dpi=170,  # thin diagonal strands need pixels (see gallery case)
       scheme="EqualInterval",  # convention-free breaks: the gapped
       # strands subsample the region, so quantile-convention
       # differences between QGIS and mapclassify would change the
       # visible-class set here (see the gallery case's comment)
       criterion="strand skips + aspect 0.75 must leave visible gaps",
       **FOUR),
  dict(name="hex-colouring 7 shared ramp", build=_hexcol_unit,
       criterion="7 elements, ONE ramp: map stays in a single hue family",
       ids="abcdefg",
       variables=["va", "vb", "vc", "vd", "va", "vb", "vc"],
       cmaps=["Reds"] * 7),
  dict(name="categorized land cover", build=_slice_unit,
       criterion="element a categorical (one colour per land-cover "
                 "class); others graduated",
       ids="abcd", variables=["landcover", "va", "vb", "vd"],
       cmaps=["tab10", "Blues", "Greens", "Purples"],
       categoricals=[True, False, False, False]),
  dict(name="rotate and insets", build=_modified_unit,
       criterion="rotated 30°, group and tile insets open visible gaps",
       **FOUR),
  dict(name="tileable as icons", build=_icon_unit,
       criterion="one unit per region polygon; background between icons",
       ids="abcd", variables=["va", "vb", "vc", "vd"],
       cmaps=["Reds", "Blues", "Greens", "Purples"],
       tiling_kw=dict(as_icons=True)),
  dict(name="hex-slice with offset", build=_hex_slice_unit,
       scheme="EqualInterval",
       criterion="six midpoint-cut slices on six distinct ramps",
       ids="abcdef", variables=["va", "vb", "vc", "vd", "va", "vb"],
       cmaps=["Reds", "Blues", "Greens", "Purples", "Oranges", "Greys"]),
  dict(name="basket weave", build=_basket_unit,
       scheme="NaturalBreaks",
       criterion="2x2 basket over-under with slight gaps",
       **FOUR),
  # the two library-extra families: these have no web-app rendering at
  # all, so for them the "web-app parity" column is really "library
  # continuous rendering" — same code path, same meaning, one caveat
  # fewer readers should over-read
  dict(name="grid with an open cell", build=_grid_unit,
       scheme="EqualInterval",  # subsampled region: see the twill note
       criterion="5 of 6 cells filled; the opening repeats regularly",
       ids="abcde", variables=["va", "vb", "vc", "vd", "va"],
       cmaps=["Reds", "Blues", "Greens", "Purples", "Oranges"]),
  dict(name="stripes", build=_stripes_unit,
       criterion="four parallel bands per unit",
       **FOUR),
  dict(name="diverging ramps", build=_diverging_unit,
       criterion="diverging palette family on Laves 4.8.8",
       ids="abcd", variables=["vc", "vd", "va", "vb"],
       cmaps=["RdBu", "PiYG", "PuOr", "Spectral"]),
]


def gallery_details(report_dir):
  """Measured detail strings per case, scraped from the gallery run's
  index.html (its table rows carry name, detail, and verdict)."""
  details = {}
  path = os.path.join(report_dir, "index.html")
  if not os.path.exists(path):
    return details
  text = open(path, encoding="utf-8").read()
  for status, name, detail in re.findall(
      r'<tr class="(pass|fail)"><td>[A-Z]+</td>'
      r"<td>(.*?)</td><td>(.*?)</td>", text):
    details[html.unescape(name)] = (status.upper(), html.unescape(detail))
  return details


def main():
  """Build the comparison PDF for one report directory, and gate on it.

  Takes the report directory from argv[1], or falls back to the last
  entry under reports/. For every case in CASES it renders the
  reference through the original library, scores the gallery's PNGs
  against it, and lays out one PDF page per case; then it appends the
  UI-against-library pages that tests/run_tests.py recorded in
  ui-vs-library/scenarios.json. Those pages ask a different question
  (did the DIALOG produce the map its settings mean?) and are already
  scored by the time this script sees them — here they are only drawn
  and their verdicts folded into the exit status.

  Returns:
    Never returns normally: exits 1 if any comparison or recorded
    scenario failed, which is what makes release.py refuse to build,
    and 0 otherwise. On the way it writes visual-comparison.pdf plus
    the *_reference.png and *_reference_continuous.png files into the
    report directory, and prints one PASS/FAIL line per comparison so
    a failure is legible in the release log without opening the PDF.
  """
  report_dir = sys.argv[1] if len(sys.argv) > 1 else None
  if report_dir is None:
    reports = os.path.join(ROOT, "reports")
    if not os.path.isdir(reports):
      # checked BEFORE listing: os.listdir raises FileNotFoundError
      # first, so the helpful message below used to be unreachable
      sys.exit("no reports/ directory; run release.py first")
    versions = os.listdir(reports)
    if not versions:
      sys.exit("reports/ is empty; run release.py first")

    def as_version(name):
      """Sort key: the numeric parts of a vN.N.N directory name.

      Sorted as TEXT, "v0.9.0" comes after "v0.24.0" — nine beats two
      on the first differing character — so the newest release stops
      being the newest the moment a segment gains a digit, and the
      comparison is then made against the wrong release without
      saying so. Non-numeric names sort first and are effectively
      ignored.
      """
      parts = []
      for piece in name.lstrip("v").split("."):
        parts.append(int(piece) if piece.isdigit() else -1)
      return parts

    report_dir = os.path.join(reports, max(versions, key=as_version))
  details = gallery_details(report_dir)
  pdf_path = os.path.join(report_dir, "visual-comparison.pdf")

  failures = []
  with PdfPages(pdf_path) as pdf:
    for case in CASES:
      name = case["name"]
      stem = os.path.join(report_dir, name.replace(" ", "_"))
      ref_png = stem + "_reference.png"
      # two comparisons per case, both required to pass. FIRST, style
      # fidelity: the plugin's actual render against a reference
      # classed the SAME way (quantile cases judged as quantiles,
      # equal-interval as equal-interval, categorized as categorical),
      # so every style in the gallery is genuinely exercised. SECOND,
      # web-app parity: the app's default render is continuous, which
      # no classed map can match interior-for-interior; the gallery's
      # Quant: Unclassed render exists to reproduce that look and is
      # scored against a continuous reference.
      scheme = case.get("scheme", "Quantiles")
      k = case.get("k", 5)
      reference_render(case["build"](), ref_png, case["ids"],
                       case["variables"], case["cmaps"],
                       case.get("categoricals"), scheme=scheme, k=k,
                       dpi=case.get("dpi", 110),
                       **case.get("tiling_kw", {}))
      comparisons = [(stem + ".png", ref_png,
                      f"style fidelity ({scheme}, k={k})")]
      if os.path.exists(stem + "_unclassed.png"):
        cont_png = stem + "_reference_continuous.png"
        reference_render(case["build"](), cont_png, case["ids"],
                         case["variables"], case["cmaps"],
                         case.get("categoricals"),
                         dpi=case.get("dpi", 110),
                         **case.get("tiling_kw", {}))
        # in a mixed case only the graduated elements go continuous
        # on either side; categorical elements stay categorical in
        # both renders, so say so rather than implying a ramp over
        # qualitative classes
        mixed = any(case.get("categoricals") or ())
        comparisons.append(
          (stem + "_unclassed.png", cont_png,
           "web-app parity (continuous vs Quant: Unclassed"
           + ("; categorical elements stay categorical)" if mixed
              else ")")))
      results = []
      for plug_png, r_png, label in comparisons:
        if not os.path.exists(plug_png):
          continue
        ok_c, m = compare(r_png, plug_png)
        results.append((plug_png, r_png, label, ok_c, m))
        line = (f"{name} — {label}: "
                f"dE mean plugin→ref {m['a_to_b']:.1f} "
                f"(p90 {m['p90_a']:.1f}), "
                f"ref→plugin {m['b_to_a']:.1f} (p90 {m['p90_b']:.1f}), "
                f"bg diff {m['bg_diff']:.2f} "
                f"(limits mean {MAX_MEAN_DE}, p90 {MAX_P90_DE}, "
                f"bg {MAX_BG_DIFF})")
        print(f"{'PASS' if ok_c else 'FAIL'}  {line}")
      ok = bool(results) and all(r[3] for r in results)
      if not ok:
        failures.append(name)

      if not results:
        # No gallery PNG for this case, under either name. Say which
        # file is missing and carry on with the rest: plt.subplots(0,
        # 2) raises "Number of rows must be a positive integer, not
        # 0", which tells whoever is reading the release log nothing
        # at all about a missing render.
        print(f"      no gallery image for {name}: expected "
              f"{name}.png or {name}_unclassed.png in "
              f"{os.path.relpath(report_dir, ROOT)}")
        continue

      fig, axes = plt.subplots(len(results), 2,
                               figsize=(11, 6.2 * len(results)))
      axes = axes.reshape(len(results), 2)
      for row, (plug_png, r_png, label, ok_c, m) in enumerate(results):
        ref_title = ("reference: original Python library, continuous\n"
                     "(the MapWeaver web app's default look — the app\n"
                     "pins this library and this same TiledMap.render)"
                     if "parity" in label else
                     f"reference: original Python library\n"
                     f"classed to match ({scheme}, k={k})")
        measured = (f"dE mean {m['a_to_b']:.1f}/{m['b_to_a']:.1f}, "
                    f"p90 {m['p90_a']:.1f}/{m['p90_b']:.1f}, "
                    f"bg diff {m['bg_diff']:.2f} "
                    f"(limits {MAX_MEAN_DE}/{MAX_P90_DE}/"
                    f"{MAX_BG_DIFF})")
        for col, (png, title) in enumerate(
            ((r_png, ref_title),
             (plug_png, f"plugin: QGIS rendering — {label}\n"
                        f"{'PASS' if ok_c else 'FAIL'}: {measured}"))):
          ax = axes[row][col]
          if png and os.path.exists(png):
            ax.imshow(mpimg.imread(png))
          ax.set_title(title, fontsize=9)
          ax.axis("off")
      gallery_status, measured = details.get(name, ("?", ""))
      verdict = "PASS" if ok else "FAIL"
      fig.suptitle(f"{name}   [gallery {gallery_status} · "
                   f"colour comparison {verdict}]", fontsize=12)
      fig.text(0.5, 0.02,
               f"criterion: {case['criterion']}\n"
               f"gallery measured: {measured}",
               ha="center", fontsize=8, wrap=True)
      pdf.savefig(fig)
      plt.close(fig)

    # UI-against-library pages. The gallery cases above compare the
    # plugin's rendering pipeline with the original renderer; these
    # compare what the DIALOG produced, driven through its own
    # controls, with a map built by calling the library directly from
    # what those settings mean. Different question, same discipline,
    # and the reader should see both pictures rather than trust a
    # pixel statistic (tests/run_tests.py writes them).
    ui_dir = os.path.join(report_dir, "ui-vs-library")
    record = os.path.join(ui_dir, "scenarios.json")
    scenarios = []
    if os.path.exists(record):
      with open(record, encoding="utf-8") as f:
        scenarios = [json.loads(line) for line in f if line.strip()]
    for scenario in scenarios:
      if scenario.get("kind") == "single":
        # a session whose settings no independent call can restate
        # (a storm of fast clicks, a long interleaved session): the
        # picture is still checked, against the gamut of the ramps
        # in force rather than against a second render
        fig, ax = plt.subplots(figsize=(7.5, 7.0))
        png = os.path.join(ui_dir, scenario["ui"])
        if os.path.exists(png):
          ax.imshow(mpimg.imread(png))
        ax.axis("off")
        verdict = "PASS" if scenario["ok"] else "FAIL"
        fig.suptitle(f"session: {scenario['label']}   [{verdict}]",
                     fontsize=12)
        fig.text(0.5, 0.04,
                 "criterion: every interior pixel is a colour the "
                 "ramps in force can make\nmeasured: dE mean "
                 f"{scenario['mean_de']:.2f} (limit "
                 f"{scenario['mean_max']}), p95 "
                 f"{scenario['p95_de']:.2f} (limit "
                 f"{scenario['p95_max']}), background "
                 f"{100 * scenario['background']:.0f}%",
                 ha="center", fontsize=8, wrap=True)
        pdf.savefig(fig)
        plt.close(fig)
        print(f"{verdict}  session: {scenario['label']} — dE mean "
              f"{scenario['mean_de']:.2f}, p95 "
              f"{scenario['p95_de']:.2f}")
        if not scenario["ok"]:
          failures.append(f"session: {scenario['label']}")
        continue
      fig, axes = plt.subplots(1, 2, figsize=(11, 6.2))
      for ax, key, title in (
          (axes[0], "ui",
           "plugin: the map the DIALOG produced\n"
           "(driven through its own controls)"),
          (axes[1], "library",
           "reference: weavingspace called directly\n"
           "with what those settings mean")):
        png = os.path.join(ui_dir, scenario[key])
        if os.path.exists(png):
          ax.imshow(mpimg.imread(png))
        ax.set_title(title, fontsize=9)
        ax.axis("off")
      verdict = "PASS" if scenario["ok"] else "FAIL"
      fig.suptitle(f"UI vs library: {scenario['label']}   [{verdict}]",
                   fontsize=12)
      fig.text(0.5, 0.03,
               "criterion: identical tiles and areas element by "
               "element (checked in the functional suite), then "
               f"interior pixels\nmeasured: "
               f"{scenario['differing']}/{scenario['total']} interior "
               f"pixels differ ({100 * scenario['share']:.2f}%, limit "
               f"{100 * scenario['tolerance']:.0f}%)",
               ha="center", fontsize=8, wrap=True)
      pdf.savefig(fig)
      plt.close(fig)
      print(f"{verdict}  UI vs library: {scenario['label']} — "
            f"{scenario['differing']}/{scenario['total']} interior "
            f"pixels differ "
            f"({100 * scenario['share']:.2f}%, limit "
            f"{100 * scenario['tolerance']:.0f}%)")
      if not scenario["ok"]:
        failures.append(f"UI vs library: {scenario['label']}")
  print(f"wrote {pdf_path}")
  if failures:
    print(f"comparison FAILED for: {', '.join(failures)}")
  sys.exit(1 if failures else 0)


if __name__ == "__main__":
  main()
