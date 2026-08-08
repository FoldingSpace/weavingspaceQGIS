#!/usr/bin/env python3
"""Are the elements of a rendered pattern still telling themselves apart?

A tiled or woven map answers a different question from a choropleth. It
asks a reader to hold several variables at once, which they can only do
if the pattern's elements stay separable at a glance -- and separable
not merely for the maintainer looking at the render, but for the eight
percent or so of male readers with a red-green colour vision
deficiency. Nothing in the functional suite asks that. The gallery
checks that every pixel sits ON the ramp it was assigned
(tests/visual_tests.py's gamut criterion), which is a question about
correctness; this asks a question about legibility, and a map can pass
the first while failing the second.

Run under QGIS's own Python, from the repository root:

    QT_QPA_PLATFORM=offscreen \\
    PYTHONHOME=/Applications/QGIS-final-4_0_3.app/Contents/Frameworks \\
    PROJ_LIB=/Applications/QGIS-final-4_0_3.app/Contents/Resources/qgis/proj \\
    QGIS_PREFIX_PATH=/Applications/QGIS-final-4_0_3.app/Contents/MacOS \\
    /Applications/QGIS-final-4_0_3.app/Contents/MacOS/python3.12 \\
    tools/perceptual_check.py reports/v0.22.0/*.png

Nothing here needs a QgsApplication: QImage decodes a PNG on its own,
and the rest is numpy. The only QGIS-shaped dependency is the sampling
and colourspace code borrowed from tests/visual_tests.py, imported
rather than copied so the two cannot drift apart.

WHAT IT MEASURES, and in what order:

1. Interior fill colours. Sampling reuses visual_tests.sample_pixels,
   which keeps a pixel only when its four neighbours agree with it.
   This project has already paid for the alternative: an unweighted
   comparison over every pixel is dominated by antialiasing, because a
   thin strand is mostly edge, and edge pixels are blends of two fills
   that exist nowhere in the symbology. Interior pixels are then
   grouped into the distinct colours actually present and WEIGHTED by
   how many pixels each covers, so a colour occupying a tenth of the
   map and a colour surviving on forty stray pixels are not treated as
   equals.
2. The minimum pairwise CIELAB Delta-E among those colours, under
   normal vision and then under simulated deuteranopia and
   protanopia. The minimum is the right statistic because legibility
   fails at its weakest pair: a palette with nineteen well-separated
   colours and one collapsed pair is a palette a reader will misread.
3. A pass or fail against a threshold (--threshold, default 10). The
   process exits non-zero when any pair falls below it under any of
   the three visions, so a release can gate on this later.

WHAT IT CANNOT SEE. The render is all it has, so it does not know
which element or which class a colour came from -- it reports hex
values and the share of the map each covers. A pair that collapses may
be two classes within one element's ramp (expected, and read as a
sequence rather than as a contrast) or two different elements' colours
(a real problem). Reading the flagged hex values back against the
case's assigned ramps is a human step, and a short one.
"""

import argparse
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _visual_tests():
  """The gallery module, loaded by path, for its sampling helpers.

  Returns:
    The imported tests/visual_tests.py module object, from which this
    tool uses ``sample_pixels`` (interior-pixel sampling),
    ``srgb_to_lab`` (the project's one sRGB-to-CIELAB conversion) and
    ``_is_background`` (the magenta chroma-key test).

  Why by path rather than ``import tests.visual_tests``: tests/ has no
  __init__.py, so it is not a package; and importing the real module
  rather than copying twenty lines of it is the point. The sampling
  rule (four neighbours must agree) and the Lab conversion are shared
  with the release gallery on purpose, so that a change to either
  cannot leave this tool measuring something subtly different from
  what the gallery measures.
  """
  path = os.path.join(ROOT, "tests", "visual_tests.py")
  spec = importlib.util.spec_from_file_location("visual_tests", path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


# --------------------------------------------------- colour vision models

# Viénot, Brettel & Mollon (1999), "Digital video colourmaps for
# checking the legibility of displayed text", Color Research and
# Application 24(4), 243-252. That paper simplifies Brettel, Viénot &
# Mollon (1997) for the two red-green dichromacies: where the 1997
# algorithm projects onto two half-planes meeting at the neutral axis,
# the 1999 paper shows that for protanopia and deuteranopia a SINGLE
# plane suffices, which makes the whole simulation one 3x3 matrix
# applied in LMS cone space. (The simplification does not hold for
# tritanopia, which is why this tool does not offer it -- a
# single-plane tritan simulation would be wrong, and a wrong number is
# worse here than a missing one.)
#
# The transform below is the paper's: linear RGB -> LMS, collapse the
# missing cone's response onto the remaining two, LMS -> linear RGB.
# It must be applied to LINEAR light, not to gamma-encoded sRGB values:
# the dichromat's confusion lines are straight in a linear cone space
# and curved in an encoded one, so simulating on encoded values gives
# plausible-looking pictures with the wrong distances in them.

RGB_TO_LMS = [[17.8824, 43.5161, 4.11935],
              [3.45565, 27.1554, 3.86714],
              [0.0299566, 0.184309, 1.46709]]

# Substitution matrices, in LMS. Protanopia lacks the L cone, so the L
# response is reconstructed from M and S; deuteranopia lacks M and
# reconstructs it from L and S. Coefficients are the paper's, fitted so
# that the neutral axis and the blue/yellow anchors are preserved --
# which is what makes a simulated white still white.
LMS_PROTAN = [[0.0, 2.02344, -2.52581],
              [0.0, 1.0, 0.0],
              [0.0, 0.0, 1.0]]
LMS_DEUTAN = [[1.0, 0.0, 0.0],
              [0.494207, 0.0, 1.24827],
              [0.0, 0.0, 1.0]]

# The three visions this tool reports, in the order they are printed.
# "normal" is the identity and is not a model of anything; it is the
# baseline the other two are read against.
VISIONS = ("normal", "deuteranopia", "protanopia")


def simulate_vision(rgb, vision):
  """Rendered colours as a dichromat would see them.

  Args:
    rgb: an (n, 3) array of sRGB values on 0..255, as read from the
      render -- the fill colours the plugin actually put on the map.
    vision: "normal", "deuteranopia" or "protanopia". "normal" returns
      the input unchanged, so callers can loop over VISIONS without a
      special case.

  Returns:
    An (n, 3) array of sRGB values on 0..255: the colours a display
    would have to show a reader with normal vision for them to receive
    the same signal a dichromat receives from the original. Values are
    clipped into gamut, because the projection can land outside the
    sRGB cube and a negative primary is not a colour anything can
    show.

  Raises:
    ValueError: on an unknown vision name, rather than silently
      returning the input, which would quietly turn a typo into a
      passing check.

  The round trip through gamma encoding is deliberate: this returns
  sRGB on 0..255 so its output feeds ``srgb_to_lab`` -- the project's
  single Lab conversion -- exactly as unsimulated colours do. One
  linearize/encode pair is wasted per call, on at most a few dozen
  colours, which is a fair price for having one conversion in the
  codebase rather than two.
  """
  import numpy as np
  if vision == "normal":
    return np.asarray(rgb, dtype=float)
  if vision == "deuteranopia":
    substitution = np.array(LMS_DEUTAN)
  elif vision == "protanopia":
    substitution = np.array(LMS_PROTAN)
  else:
    raise ValueError(f"unknown vision {vision!r}")

  c = np.asarray(rgb, dtype=float) / 255.0
  # sRGB electro-optical transfer function, same piecewise form as
  # visual_tests.srgb_to_lab uses; kept here rather than imported
  # because that function goes all the way to Lab in one step
  linear = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
  to_lms = np.array(RGB_TO_LMS)
  # inverted numerically rather than transcribed: the published
  # inverse matrix is quoted to six figures in several places and a
  # digit slip in it would show up as a small, plausible, wrong
  # Delta-E rather than as an obvious failure
  from_lms = np.linalg.inv(to_lms)
  simulated = linear @ to_lms.T @ substitution.T @ from_lms.T
  simulated = np.clip(simulated, 0.0, 1.0)
  encoded = np.where(simulated > 0.0031308,
                     1.055 * simulated ** (1 / 2.4) - 0.055,
                     12.92 * simulated)
  return encoded * 255.0


# ------------------------------------------------------- sampling the map

def is_near_white(rgb):
  """Is this sampled colour the paper the map is printed on?

  Args:
    rgb: one (3,) sRGB triple on 0..255.

  Returns:
    True when the colour is effectively unrendered white -- canvas,
    an outline's white casing, a legend panel -- and so is not one of
    the pattern's fills.

  The test is deliberately severe (every channel at 254 or above, and
  neutral to within one count) because the mistake it guards against
  is the expensive one. Sequential ramps legitimately END in very pale
  data colours: matplotlib's Reds begins at #fff5f0, Blues at #f7fbff,
  Greens at #f7fcf5, Purples at #fcfbfd. Those are element colours a
  reader is meant to distinguish, they are what a first class looks
  like on the map, and they are exactly the colours most at risk of
  collapsing into one another -- so a comfortable "is it pale?" test
  would silently discard the finding this tool exists to make. A
  looser version of this function was written first and dropped the
  palest Purples class alone, which flattered the very case it should
  have condemned. The chroma-key magenta background is handled
  separately, by the gallery's own ``_is_background``.
  """
  return min(rgb) >= 254 and (max(rgb) - min(rgb)) <= 1


def fill_colours(image, visual, sample=250, tolerance=1.0,
                 min_share=0.005):
  """The distinct fill colours a render actually contains, with weights.

  Args:
    image: a QImage of a rendered map.
    visual: the loaded visual_tests module (see ``_visual_tests``),
      supplying the sampling and Lab conversion this reuses.
    sample: sampling density passed through to
      ``visual_tests.sample_pixels`` -- the grid step is
      ``width // sample``, so 250 on a 700px render samples every
      second pixel. Higher is slower and finds more small fills.
    tolerance: Delta-E below which two sampled colours are treated as
      the same fill. It has to sit far below the reporting threshold,
      and 1 is chosen rather than something roomier for a reason worth
      stating plainly: anything this function merges can never be
      reported as a failing pair, so a generous tolerance would
      silently swallow the WORST results -- two fills a reader cannot
      separate at all would come back as one colour and a shorter
      list. An early version at 3 did exactly that to the palest
      Blues and Purples classes. QGIS fills are flat, so identical
      fills arrive byte-identical and a tolerance of 1 has nothing to
      do but absorb the occasional rounding; on the four-ramp gallery
      cases it recovers exactly the twenty classes the symbology
      defines.
    min_share: drop any colour covering less than this fraction of the
      sampled interior pixels. This is the pixel-count weighting doing
      its work. A handful of survivors from a strand corner is not a
      colour a reader reads, and letting such specks into the pairwise
      minimum would report collapses that nobody could see in the
      first place.

  Returns:
    A tuple (colours, shares, sampled) where colours is an (m, 3)
    array of sRGB fills on 0..255, shares is an (m,) array of the
    fraction of sampled interior pixels each covers (summing to at
    most 1, since dropped specks are not redistributed), and sampled
    is the number of interior pixels the sample found. Colours come
    back ordered by share, largest first.

  Clustering is greedy and weighted rather than k-means: k is exactly
  what we do not know in advance (a case may show four ramps of five
  classes, or a categorical set, or one shared ramp), and starting
  from the most-covering colour and absorbing near neighbours into it
  gives cluster centres that sit on the colours the symbology actually
  produced instead of between them.
  """
  import numpy as np
  pixels = visual.sample_pixels(image, sample=sample)
  if len(pixels) == 0:
    return np.empty((0, 3)), np.empty((0,)), 0
  keep = np.array([not is_near_white(px) for px in pixels])
  pixels = pixels[keep]
  if len(pixels) == 0:
    return np.empty((0, 3)), np.empty((0,)), 0

  # exact duplicates first: a flat fill contributes thousands of
  # identical triples, and collapsing them turns the clustering below
  # from a problem in pixels into a problem in dozens of colours
  unique, counts = np.unique(pixels, axis=0, return_counts=True)
  order = np.argsort(-counts)
  unique, counts = unique[order], counts[order]
  lab = visual.srgb_to_lab(unique)

  centres, weights, members = [], [], []
  for i in range(len(unique)):
    placed = False
    for j, centre_lab in enumerate(centres):
      if np.sqrt(((lab[i] - centre_lab) ** 2).sum()) <= tolerance:
        weights[j] += counts[i]
        members[j].append(i)
        placed = True
        break
    if not placed:
      centres.append(lab[i])
      weights.append(counts[i])
      members.append([i])

  total = counts.sum()
  out_rgb, out_share = [], []
  for j, member_idx in enumerate(members):
    share = weights[j] / total
    if share < min_share:
      continue
    # the cluster's colour is its pixel-weighted mean in sRGB, which
    # for a cluster spanning at most `tolerance` Delta-E is within
    # rounding of the weighted mean in Lab and is directly comparable
    # to a ramp stop a maintainer can look up
    w = counts[member_idx][:, None]
    out_rgb.append((unique[member_idx] * w).sum(axis=0) / w.sum())
    out_share.append(share)
  if not out_rgb:
    return np.empty((0, 3)), np.empty((0,)), int(total)
  out_rgb = np.array(out_rgb)
  out_share = np.array(out_share)
  order = np.argsort(-out_share)
  return out_rgb[order], out_share[order], int(total)


# --------------------------------------------------- the legibility test

def pair_distances(colours, visual, vision):
  """Every pairwise Delta-E among a render's fills, under one vision.

  Args:
    colours: an (m, 3) array of sRGB fills on 0..255, as returned by
      ``fill_colours``.
    visual: the loaded visual_tests module, for ``srgb_to_lab``.
    vision: one of VISIONS; the fills are simulated through it before
      the distances are taken.

  Returns:
    A list of (delta_e, i, j) with i < j, sorted closest pair first --
    so element [0] is the render's weakest link under this vision and
    the caller does not have to search for it. Empty when fewer than
    two colours were found.

  Delta-E here is CIE76, plain Euclidean distance in Lab, matching the
  gallery's gamut criterion. Its known weaknesses (it overstates
  differences among saturated blues and understates them among
  saturated reds, which CIE94 and CIEDE2000 were introduced to fix)
  argue for reading the number as a screening statistic rather than as
  a measurement, which is also why the threshold below sits well above
  any just-noticeable difference.
  """
  import numpy as np
  if len(colours) < 2:
    return []
  lab = visual.srgb_to_lab(simulate_vision(colours, vision))
  out = []
  for i in range(len(lab)):
    for j in range(i + 1, len(lab)):
      out.append((float(np.sqrt(((lab[i] - lab[j]) ** 2).sum())), i, j))
  out.sort()
  return out


def check_image(path, visual, threshold=10.0, sample=250,
                tolerance=1.0, min_share=0.005):
  """Measure one rendered map and decide whether it passes.

  Args:
    path: a PNG written by the release gallery (reports/v*/), or any
      other render.
    visual: the loaded visual_tests module.
    threshold: the Delta-E floor for "a reader can tell these apart at
      a glance". See ``main`` for why the default is 10.
    sample, tolerance, min_share: passed through to ``fill_colours``.

  Returns:
    A dict with keys: ``path``; ``colours`` (m x 3 sRGB array);
    ``shares`` (m,); ``sampled`` (interior pixels used); ``pairs``
    (vision name -> the sorted list from ``pair_distances``);
    ``worst`` (vision name -> minimum Delta-E, or None when fewer than
    two colours were found); ``failures`` (list of (vision, delta_e,
    i, j) below threshold, closest first, across all visions); and
    ``error`` (a string when the file could not be read, otherwise
    absent). Nothing is written to disk and nothing is mutated.
  """
  from qgis.PyQt.QtGui import QImage
  image = QImage(path)
  if image.isNull():
    return {"path": path, "error": "could not be read as an image"}
  colours, shares, sampled = fill_colours(
    image, visual, sample=sample, tolerance=tolerance,
    min_share=min_share)
  result = {"path": path, "colours": colours, "shares": shares,
            "sampled": sampled, "pairs": {}, "worst": {},
            "failures": []}
  for vision in VISIONS:
    pairs = pair_distances(colours, visual, vision)
    result["pairs"][vision] = pairs
    result["worst"][vision] = pairs[0][0] if pairs else None
    result["failures"] += [(vision, d, i, j) for d, i, j in pairs
                           if d < threshold]
  # closest first, so a reader of the printed report meets the most
  # serious collapse before the marginal ones
  result["failures"].sort(key=lambda f: f[1])
  return result


# ------------------------------------------------------------- reporting

def hex_of(rgb):
  """An sRGB triple on 0..255 as the #rrggbb a maintainer can look up
  against a ramp definition in palettes.json."""
  return "#" + "".join(f"{int(round(v)):02x}" for v in rgb)


def print_report(result, threshold, max_pairs=10):
  """Print one render's findings as a table.

  Args:
    result: a dict from ``check_image``.
    threshold: the Delta-E floor in force, printed so the table is
      readable on its own.
    max_pairs: how many sub-threshold pairs to list before saying how
      many were suppressed. A collapsed palette can produce dozens,
      and the closest few are the ones worth acting on.

  Returns:
    None. Output goes to stdout.
  """
  name = os.path.basename(result["path"])
  print(f"\n{name}")
  print("-" * max(len(name), 60))
  if "error" in result:
    print(f"  {result['error']}")
    return
  colours, shares = result["colours"], result["shares"]
  if len(colours) == 0:
    print("  no interior fill pixels found (blank or all-background "
          "render?)")
    return
  print(f"  {result['sampled']:,} interior pixels sampled, "
        f"{len(colours)} fill colours at or above "
        f"{100 * shares.min():.1f}% coverage")
  swatches = [f"{hex_of(c)} {100 * s:4.1f}%"
              for c, s in zip(colours, shares)]
  for start in range(0, len(swatches), 4):
    print("    " + "   ".join(swatches[start:start + 4]))

  print()
  print(f"  {'vision':<14}{'min ΔE':>8}   {'closest pair':<20}"
        f"{'pairs < ' + str(threshold):>14}")
  for vision in VISIONS:
    pairs = result["pairs"][vision]
    if not pairs:
      print(f"  {vision:<14}{'n/a':>8}")
      continue
    d, i, j = pairs[0]
    below = sum(1 for p in pairs if p[0] < threshold)
    pair_text = f"{hex_of(colours[i])} / {hex_of(colours[j])}"
    flag = "  FAIL" if below else ""
    print(f"  {vision:<14}{d:8.1f}   {pair_text:<20}{below:>14}{flag}")

  if result["failures"]:
    print(f"\n  pairs below ΔE {threshold}:")
    for vision, d, i, j in result["failures"][:max_pairs]:
      print(f"    {vision:<14}ΔE {d:5.1f}   "
            f"{hex_of(colours[i])} ({100 * shares[i]:.1f}%) / "
            f"{hex_of(colours[j])} ({100 * shares[j]:.1f}%)")
    hidden = len(result["failures"]) - max_pairs
    if hidden > 0:
      print(f"    ... and {hidden} more")


def print_summary(results, threshold):
  """Print the across-files table and return the number that failed.

  Args:
    results: the list of dicts from ``check_image``, in the order the
      files were given.
    threshold: the Delta-E floor in force.

  Returns:
    How many renders had at least one pair below threshold under at
    least one vision (unreadable files count as failures -- a check
    that cannot see its input has not passed).
  """
  print("\n" + "=" * 72)
  print(f"{'render':<38}{'normal':>10}{'deuter.':>10}{'protan.':>10}"
        f"{'':>4}")
  failed = 0
  for r in results:
    name = os.path.basename(r["path"])[:37]
    if "error" in r:
      print(f"{name:<38}{'unreadable':>30}{'  FAIL':>6}")
      failed += 1
      continue
    cells = ""
    for vision in VISIONS:
      worst = r["worst"][vision]
      cells += f"{'n/a':>10}" if worst is None else f"{worst:>10.1f}"
    bad = bool(r["failures"])
    failed += bad
    print(f"{name:<38}{cells}{'  FAIL' if bad else '  ok':>6}")
  print("=" * 72)
  print(f"{len(results) - failed}/{len(results)} renders keep every "
        f"pair of fill colours at least ΔE {threshold} apart under "
        f"normal, deuteranopic and protanopic vision.")
  return failed


def main():
  """Parse arguments, check each render, exit non-zero on any failure.

  The exit status is the point of the tool: 0 when every render keeps
  every pair of its fill colours at or above the threshold under all
  three visions, 1 when any pair collapses (or any file could not be
  read), 2 when no files were given. That makes it usable as a release
  gate without any further plumbing.

  On the default threshold of 10. A CIE76 Delta-E of roughly 2.3 is
  the classic just-noticeable difference, measured between large
  patches shown side by side under controlled light -- conditions
  nothing about these maps resembles. Here the colours appear as small
  interleaved elements, each surrounded by OTHER colours rather than
  by a neutral surround, at whatever size and on whatever display the
  reader has; simultaneous contrast then shifts each element's
  apparent colour according to its neighbours. A margin several times
  the laboratory JND is the usual response to that, and 10 is the
  figure this project already uses in the gallery's own documentation
  for "clearly different". It is a working convention, not a law:
  CIE76 is not perceptually uniform (it exaggerates differences among
  saturated blues and understates them elsewhere), and simulated
  dichromacy has lost a dimension, so a distance measured in it is a
  screening statistic. Treat a number just under the threshold as an
  invitation to look at the map, and a number near zero as a finding.
  """
  parser = argparse.ArgumentParser(
    description="Check rendered maps for element colours that a "
                "reader -- including a reader with a red-green colour "
                "vision deficiency -- could not tell apart.")
  parser.add_argument("pngs", nargs="*",
                      help="rendered PNGs, e.g. reports/v0.22.0/*.png")
  parser.add_argument("--threshold", type=float, default=10.0,
                      help="Delta-E floor for two fills to count as "
                           "distinguishable (default 10)")
  parser.add_argument("--sample", type=int, default=250,
                      help="sampling density; the grid step is "
                           "width // sample (default 250)")
  parser.add_argument("--cluster-tolerance", type=float, default=1.0,
                      help="Delta-E within which sampled colours are "
                           "one fill; must stay well below "
                           "--threshold, since merged colours cannot "
                           "be reported as a failing pair (default 1)")
  parser.add_argument("--min-share", type=float, default=0.005,
                      help="ignore fills covering less than this "
                           "fraction of sampled interior pixels "
                           "(default 0.005)")
  parser.add_argument("--max-pairs", type=int, default=10,
                      help="how many failing pairs to list per render "
                           "(default 10)")
  args = parser.parse_args()
  if not args.pngs:
    parser.print_usage()
    print("give at least one rendered PNG")
    return 2

  visual = _visual_tests()
  results = []
  for path in args.pngs:
    result = check_image(path, visual, threshold=args.threshold,
                         sample=args.sample,
                         tolerance=args.cluster_tolerance,
                         min_share=args.min_share)
    results.append(result)
    print_report(result, args.threshold, max_pairs=args.max_pairs)
  failed = print_summary(results, args.threshold)
  return 1 if failed else 0


if __name__ == "__main__":
  sys.exit(main())
