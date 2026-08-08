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
fractions are compared after cropping to content. The reference is
*unclassed* (the web app's default; classed rendering in TiledMap
needs mapclassify, absent here) while the gallery's primary renders
use quantile classes, so a case is scored first against the quantile
render and, when only the classing explains a failure, against the
gallery's Quant: Unclassed render (50 linear intervals; saved by the
gallery as *_unclassed.png) — mirroring how a user reproduces the web
app's continuous look in the plugin. A case failing against both
renders fails the step, and release.py then refuses to build.

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
  scoring dE 11)."""
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
  b->a) — exactly the signature the unclassed fallback exists for."""
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
  """(ok, metrics) for one reference/plugin pair."""
  m = palette_distance(plugin_png, reference_png)
  ok = (m["a_to_b"] <= MAX_MEAN_DE and m["b_to_a"] <= MAX_MEAN_DE
        and m["p90_a"] <= MAX_P90_DE and m["p90_b"] <= MAX_P90_DE
        and m["bg_diff"] <= MAX_BG_DIFF)
  return ok, m


def synthetic_region(n=6, cell=1000):
  """Identical to tests/visual_tests.synthetic_region (duplicated here
  because that module imports qgis at load time and this script must
  run without QGIS): an n x n grid of squares with smooth numeric
  fields and a categorical one."""
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
  reproduction."""
  from weavingspace import Tiling
  tm = Tiling(unit, synthetic_region(), **tiling_kw).get_tiled_map()
  tm.ids_to_map = list(ids)
  tm.vars_to_map = list(variables)
  tm.colors_to_use = list(cmaps)
  if categoricals is not None:
    tm.categoricals = list(categoricals)
  if scheme is not None:
    tm.schemes_to_use = scheme  # broadcast to every id by TiledMap
    tm.n_classes = k or 5
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
  from weavingspace import TileUnit
  return TileUnit(tiling_type="laves", code="3.3.4.3.4",
                  spacing=500, crs=3857)


def _twill_unit():
  from weavingspace import WeaveUnit
  return WeaveUnit(weave_type="twill", n=(1, 2), strands="ab-|cd-",
                   aspect=0.75, spacing=300, crs=3857)


def _hexcol_unit():
  from weavingspace import TileUnit
  return TileUnit(tiling_type="hex-col", n=7, spacing=600, crs=3857)


def _slice_unit():
  from weavingspace import TileUnit
  return TileUnit(tiling_type="square-slice", n=4, offset=0,
                  spacing=700, crs=3857)


def _modified_unit():
  from weavingspace import TileUnit
  return TileUnit(tiling_type="laves", code="3.3.4.3.4",
                  spacing=500, crs=3857) \
    .transform_rotate(30).inset_prototile(40).inset_tiles(10)


def _icon_unit():
  from weavingspace import TileUnit
  return TileUnit(tiling_type="hex-col", n=4, spacing=400, crs=3857)


FOUR = dict(ids="abcd", variables=["va", "vb", "vc", "vd"],
            cmaps=["Reds", "Blues", "Greens", "Purples"])


def _hex_slice_unit():
  from weavingspace import TileUnit
  return TileUnit(tiling_type="hex-slice", n=6, offset=1,
                  spacing=600, crs=3857)


def _basket_unit():
  from weavingspace import WeaveUnit
  return WeaveUnit(weave_type="basket", n=2, strands="ab|cd",
                   aspect=0.85, spacing=350, crs=3857)


def _diverging_unit():
  from weavingspace import TileUnit
  return TileUnit(tiling_type="laves", code="4.8.8",
                  spacing=550, crs=3857)

def _grid_unit():
  from weavingspace import TileUnit
  return TileUnit(tiling_type="grid", n=5, nrows=2, ncols=3,
                  spacing=600, crs=3857)


def _stripes_unit():
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
  report_dir = sys.argv[1] if len(sys.argv) > 1 else None
  if report_dir is None:
    versions = sorted(os.listdir(os.path.join(ROOT, "reports")))
    if not versions:
      sys.exit("no reports/ directory; run release.py first")
    report_dir = os.path.join(ROOT, "reports", versions[-1])
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
