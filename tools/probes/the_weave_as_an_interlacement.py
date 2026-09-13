"""A weave's structure taken from the interlacement, not from the polygons.

Every construction in
docs/process/the-topology-of-a-weave-and-its-holes.md works on the
RENDERED design, and the rendered design is a projection: a flat map
cannot show one ribbon lying on another, so the strand passing under is
cut, and the over-and-under -- the thing a weave is -- is exactly what
the picture throws away. Three attempts to recover it from those
polygons all failed, which in hindsight is what should have been
expected.

THIS TAKES THE CONCEPTUAL OBJECT INSTEAD (the maintainer's framing,
2026-09-08). In the model, strands are CONTINUOUS ribbons that really
do pass over and under one another; the flat design is a shadow of
that. The information survives one layer below the geometry, in the
library's `Loom`, whose `indices` are the crossing sites and whose
`orderings` are the layer order at each -- and none of it depends on
the strand width, the inset, or how any hole was cut, because no
polygon has been drawn yet.

What is built here is a model, not a reading of the library's output.
The loom supplies the crossings; the structure is ours:

  a STRAND is a whole ribbon, named by its letter and its direction,
    and it is continuous even where the drawing cuts it
  a CROSSING is a site where two strands meet, carrying which of them
    passes over
  a FLOAT is a run of crossings a strand rides over without dipping,
    which is what a weaver means by the structure of a cloth
  a MISSING strand is absent from the model rather than being a hole in
    it, since the code says it was never threaded

The comparison that matters is with a tiling, whose classes are few and
come from the design's symmetries rather than from measurement. Here
they come from the code, which is the same kind of source.

Run it in the reference venv; it touches no geometry and is quick:

    ./.venv-reference/bin/python3 \
      tools/probes/the_weave_as_an_interlacement.py
"""
import os
import sys
import warnings

import matplotlib
matplotlib.use("Agg")

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "weavingspace_qgis", "vendor"))
warnings.filterwarnings("ignore", category=RuntimeWarning)

from weavingspace_qgis import catalog  # noqa: E402
from weavingspace import weave_matrices  # noqa: E402
from weavingspace._loom import Loom  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

IMAGES = os.path.join(HERE, "docs", "process", "images", "holes-as-tiles")
WARP_COLOUR = "#4c72b0"
WEFT_COLOUR = "#dd8452"

WEAVES = ("plain weave a|b", "twill weave a|b", "twill weave ab|cd",
          "basket weave ab|cd", "twill weave a|b-", "plain weave ab-|cd-")
TILINGS = ("laves 3.3.4.3.4", "archimedean 4.8.8")


def spec_for(name):
  """The catalogue's own entry, looked up rather than typed.

  Args:
    name: the catalogue key.

  Returns:
    The spec dict.

  Raises:
    KeyError: where no entry of that name exists.
  """
  for entries in catalog.TILINGS_BY_N.values():
    if name in entries:
      return entries[name]
  raise KeyError(name)


def loom_for(spec):
  """The crossing sites and layer orders a weave's code implies.

  Args:
    spec: the catalogue entry, carrying `strands`, `weave_type` and the
      over-under `n`.

  Returns:
    (loom, warp, weft) with the two strand lists as the code gives
    them, hyphens included so a missing strand can be told from a
    threaded one.

  NO GEOMETRY IS BUILT. This is the specification turned into its
  crossings, which is all the model needs.
  """
  code = str(spec.get("strands", ""))
  runs = code.split("|")
  warp = list(runs[0]) if runs else []
  weft = list(runs[1]) if len(runs) > 1 else []
  # THE CATALOGUE STORES `n` AS TYPED, e.g. "2" or "1,2,2,1", and the
  # library wants an int or a tuple. `catalog.get_over_under` is the
  # parser the plugin already uses, so it is called rather than a
  # second one written here that could disagree with it.
  over_under = catalog.get_over_under(str(spec.get("n", "2")))
  kind = spec.get("weave_type", "plain")
  if kind == "basket":
    # A basket takes a single number, where a twill takes the whole
    # over-under run; passing the run gives `TypeError: can't multiply
    # sequence by non-int`. The first term is what the catalogue means.
    over_under = (over_under[0] if isinstance(over_under, (tuple, list))
                  else over_under)
  matrix = weave_matrices.get_weave_pattern_matrix(
    weave_type=kind, n=over_under, warp=warp, weft=weft)
  return Loom(matrix), warp, weft


def interlacement(spec):
  """The over-and-under structure of one weave, read from its code.

  Args:
    spec: the catalogue entry.

  Returns:
    A dict carrying the crossings, each strand's cyclic sequence of
    over and under, and the classes those sequences fall into.

  WHICH END OF AN ORDERING IS THE TOP is the library's convention and
  is not assumed here. The sequences are built consistently from it and
  the answer is checked against what the weave is known to be: a plain
  weave must alternate, and a twill of n=2 must ride over two at a
  time. A convention read the wrong way round would swap every over for
  an under and leave the STRUCTURE identical, which is why the classes
  below are safe even though the absolute sense is the library's.
  """
  loom, warp, weft = loom_for(spec)
  crossings = []
  for site, order in zip(loom.indices, loom.orderings):
    if not isinstance(order, tuple) or len(order) < 2:
      # One layer or none: a site where a strand was never threaded.
      crossings.append((site, None))
      continue
    crossings.append((site, order[-1]))
  sequences = {}
  for site, top in crossings:
    if top is None:
      continue
    row, column = site[0], site[1]
    # Axis 0 runs along one coordinate and axis 1 along the other, so a
    # strand is named by the coordinate it does NOT vary along.
    sequences.setdefault(("axis0", row), []).append(top == 0)
    sequences.setdefault(("axis1", column), []).append(top == 1)
  classes = {}
  for key, runs in sequences.items():
    signature = min(tuple(runs[i:] + runs[:i]) for i in range(len(runs)))
    classes.setdefault(signature, []).append(key)
  return {"crossings": crossings, "sequences": sequences,
          "classes": classes, "warp": warp, "weft": weft,
          "dimensions": loom.dimensions}


def shifts_along(sequences, axis):
  """How far each strand's pattern is offset from its neighbour's.

  Args:
    sequences: the per-strand over-and-under, keyed by (axis, index).
    axis: which axis to walk, "axis0" or "axis1".

  Returns:
    The cyclic shift between each consecutive pair of strands on that
    axis, as a tuple, or None where there are fewer than two.

  WHY THIS IS NEEDED. The per-strand sequence alone cannot tell a twill
  from a basket: both ride over two and under two, so both read `UUOO`
  with a float of two. What distinguishes them is the PHASE between
  neighbouring strands -- a twill steps by one each time, which is what
  makes its diagonal, while a basket repeats in blocks. A structure
  that cannot separate two weaves anybody can tell apart by eye is not
  yet describing the weave.
  """
  keys = sorted(k for k in sequences if k[0] == axis)
  if len(keys) < 2:
    return None
  out = []
  for first, second in zip(keys, keys[1:]):
    one, two = sequences[first], sequences[second]
    if len(one) != len(two) or not one:
      out.append(None)
      continue
    found = None
    for shift in range(len(one)):
      if list(one[shift:] + one[:shift]) == list(two):
        found = shift
        break
    out.append(found)
  return tuple(out)


def longest_float(sequence):
  """The longest run a strand rides over without dipping.

  Args:
    sequence: the strand's cyclic over-and-under, as booleans.

  Returns:
    The longest run of True, counted cyclically, which is what a weaver
    means by a float.
  """
  if not sequence or not any(sequence):
    return 0
  doubled = list(sequence) * 2
  best = run = 0
  for value in doubled:
    run = run + 1 if value else 0
    best = max(best, run)
  return min(best, len(sequence))


def draw_interlacement(axis, spec, title):
  """Draw a weave's over-and-under as the grid a weaver would read.

  Args:
    axis: the matplotlib axis.
    spec: the catalogue entry.
    title: what to put above it.

  A filled cell is a crossing where the warp rides over; an empty one is
  where the weft does. This is the loom's own matrix, not a rendering of
  any polygon.
  """
  found = interlacement(spec)
  rows = max(site[0] for site, _t in found["crossings"]) + 1
  columns = max(site[1] for site, _t in found["crossings"]) + 1
  for site, top in found["crossings"]:
    i, j = site[0], site[1]
    if top is None:
      axis.add_patch(Rectangle((j, rows - 1 - i), 1, 1, facecolor="#f2f2f2",
                               edgecolor="#bbbbbb", linewidth=0.6))
      continue
    axis.add_patch(Rectangle(
      (j, rows - 1 - i), 1, 1,
      facecolor=WARP_COLOUR if top == 0 else WEFT_COLOUR,
      edgecolor="#ffffff", linewidth=1.0))
  axis.set_xlim(0, columns)
  axis.set_ylim(0, rows)
  axis.set_aspect("equal")
  axis.axis("off")
  axis.set_title(title, fontsize=9, pad=8)


def figure_the_three_families(path):
  """Figure: plain, twill and basket, and the phase that separates them.

  Args:
    path: where to write the PNG.
  """
  names = ("plain weave a|b", "twill weave ab|cd", "basket weave ab|cd")
  figure, axes = plt.subplots(1, 3, figsize=(10.5, 4.0))
  for axis, name in zip(axes, names):
    spec = spec_for(name)
    found = interlacement(spec)
    steps = shifts_along(found["sequences"], "axis0")
    pattern = "".join("O" if x else "U"
                      for x in sorted(found["classes"])[0])
    draw_interlacement(axis, spec,
                       f"{name}\n{pattern}, float "
                       f"{longest_float(sorted(found['classes'])[0])}\n"
                       f"phase steps {steps}")
  figure.suptitle("The interlacement, read from the code: a filled cell is "
                  "a crossing the warp rides over", fontsize=10)
  figure.tight_layout(rect=(0, 0, 1, 0.88))
  figure.savefig(path, dpi=140)
  plt.close(figure)


def figure_what_the_projection_loses(path):
  """Figure: continuous ribbons that cross, beside the flat design.

  Args:
    path: where to write the PNG.

  The left panel is the conceptual object, drawn the way a link diagram
  is drawn: every strand runs unbroken, and the one passing UNDER is
  interrupted at the crossing to show that it goes beneath. The right
  panel is what a flat map can hold, where that interruption becomes a
  real cut in a real polygon and the reason for it is no longer
  recoverable.
  """
  figure, axes = plt.subplots(1, 2, figsize=(9.0, 4.4))
  width, gap = 0.34, 0.16
  for axis, conceptual in zip(axes, (True, False)):
    for i in range(3):
      for j in range(3):
        warp_over = (i + j) % 2 == 0
        # Warp runs vertically at x = j, weft horizontally at y = i.
        for horizontal in (True, False):
          on_top = warp_over != horizontal
          colour = WEFT_COLOUR if horizontal else WARP_COLOUR
          if horizontal:
            x0, y0, w, h = j - 0.5, i - width / 2, 1.0, width
          else:
            x0, y0, w, h = j - width / 2, i - 0.5, width, 1.0
          if on_top:
            axis.add_patch(Rectangle((x0, y0), w, h, facecolor=colour,
                                     edgecolor="#333333", linewidth=0.7,
                                     zorder=3))
          elif conceptual:
            # Under, and drawn as a link diagram does: broken at the
            # crossing so the break MEANS passing beneath.
            back = width / 2 + gap
            if horizontal:
              axis.add_patch(Rectangle((x0, y0), 0.5 - back, h,
                                       facecolor=colour, edgecolor="#333333",
                                       linewidth=0.7, zorder=1))
              axis.add_patch(Rectangle((j + back, y0), 0.5 - back, h,
                                       facecolor=colour, edgecolor="#333333",
                                       linewidth=0.7, zorder=1))
            else:
              axis.add_patch(Rectangle((x0, y0), w, 0.5 - back,
                                       facecolor=colour, edgecolor="#333333",
                                       linewidth=0.7, zorder=1))
              axis.add_patch(Rectangle((x0, i + back), w, 0.5 - back,
                                       facecolor=colour, edgecolor="#333333",
                                       linewidth=0.7, zorder=1))
          else:
            # The flat design: the same break, but now it is a cut edge
            # of a polygon and nothing records why it is there.
            back = width / 2
            if horizontal:
              axis.add_patch(Rectangle((x0, y0), 0.5 - back, h,
                                       facecolor=colour, edgecolor="#333333",
                                       linewidth=0.7, zorder=1))
              axis.add_patch(Rectangle((j + back, y0), 0.5 - back, h,
                                       facecolor=colour, edgecolor="#333333",
                                       linewidth=0.7, zorder=1))
            else:
              axis.add_patch(Rectangle((x0, y0), w, 0.5 - back,
                                       facecolor=colour, edgecolor="#333333",
                                       linewidth=0.7, zorder=1))
              axis.add_patch(Rectangle((x0, i + back), w, 0.5 - back,
                                       facecolor=colour, edgecolor="#333333",
                                       linewidth=0.7, zorder=1))
    axis.set_xlim(-0.6, 2.6)
    axis.set_ylim(-0.6, 2.6)
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title("the weave as it is: ribbons that cross,\nthe break "
                   "meaning one passes beneath" if conceptual else
                   "the weave as a flat map can hold it:\nthe break is a "
                   "cut, and says nothing", fontsize=9)
  figure.suptitle("What the projection loses", fontsize=10)
  figure.tight_layout(rect=(0, 0, 1, 0.88))
  figure.savefig(path, dpi=140)
  plt.close(figure)


def main():
  """Report the interlacement structure, with tilings for scale."""
  os.makedirs(IMAGES, exist_ok=True)
  figure_what_the_projection_loses(
    os.path.join(IMAGES, "what-the-projection-loses.png"))
  figure_the_three_families(
    os.path.join(IMAGES, "the-interlacement-of-three-families.png"))
  print(f"figures written to {IMAGES}\n")
  print("=== tilings, for scale: classes come from symmetry ===")
  from weavingspace_qgis import topology_edits as te
  for name in TILINGS:
    unit = catalog.make_unit(spec_for(name), spacing=1000.0, crs=None)
    topology, _why = te.build(unit)
    edges = {e.label for e in topology.edges.values() if e.label}
    points = {v.label for v in topology.points.values() if v.label}
    print(f"  {name:22} {len(edges)} edge / {len(points)} vertex classes")

  for name in WEAVES:
    spec = spec_for(name)
    found = interlacement(spec)
    strands = len(found["sequences"])
    floats = sorted({longest_float(s) for s in found["sequences"].values()})
    print(f"\n=== {name} ===")
    print(f"  code {str(spec.get('strands','')):12} "
          f"loom {found['dimensions']}  "
          f"{len(found['crossings'])} crossing sites")
    print(f"  {strands} strands in the model, "
          f"{len(found['classes'])} strand class(es) by interlacement")
    print(f"  longest float per class: {floats}")
    for axis in ("axis0", "axis1"):
      print(f"  phase steps along {axis}: "
            f"{shifts_along(found['sequences'], axis)}")
    for signature, members in sorted(found["classes"].items(),
                                     key=lambda kv: -len(kv[1])):
      pattern = "".join("O" if x else "U" for x in signature)
      print(f"    {pattern:<12} {len(members)} strand(s): "
            f"{[f'{a}{b}' for a, b in members]}")


if __name__ == "__main__":
  main()
