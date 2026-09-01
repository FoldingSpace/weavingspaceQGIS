"""If the tab drew the EDITED motif, how far off would the handles be?

The measurement that decides the maintainer's report of 2026-08-31 --
"basically the left doesn't reflect the changes ... and thus it's
impossible to use".

WHAT IS ALREADY SETTLED, by the sibling probe run the same hour: the
edited unit's own rebuilt topology carries DIFFERENT classes (one
vertex nudge takes laves 3.3.4.3.4 from two edge classes to ten), and
some edits leave a unit with no topology at all. So the drawing cannot
be "the edited topology" -- the chooser would fill with classes the
replay cannot use.

WHAT IS LEFT is the arrangement that keeps both halves honest: draw the
edited GEOMETRY as the ink, and keep the UN-EDITED topology as what is
labelled, hit-tested and handled. The classes then never move, and a
person sees what they made. Its one cost is that the handles and the
highlight sit where the un-edited outline was, so the question is
simply HOW FAR, and that is a number rather than an opinion.

HOW IT IS MEASURED. For each manipulation, the largest distance any
tile's boundary moves (Hausdorff, which is the worst case a person
would see) as a fraction of the unit's own span. A vertex handle drawn
at the old position sits at most that far from the new ink.

TWO SIZES OF EDIT, because one step is what a click gives and several
is what a drag gives: the control's own step, and four of them.

    cd <checkout> && PYTHONUNBUFFERED=1 QT_QPA_PLATFORM=offscreen \\
      "$QGIS_PY" how_far_would_the_highlight_sit_from_the_ink.py
"""

import os
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
from weavingspace_qgis import deps                          # noqa: E402
deps.add_paths()

from weavingspace_qgis import catalog, topology_edits       # noqa: E402

DESIGNS = [("laves 3.3.4.3.4", 4), ("hex-slice 3", 3),
           ("archimedean 4.8.8", 2)]


def span(unit):
  """The unit's own width, which every offset is expressed against."""
  x0, y0, x1, y1 = unit.tiles.total_bounds
  return max(x1 - x0, y1 - y0)


def worst_move(before, after):
  """The furthest any tile's boundary moved, tile by tile.

  Args:
    before: the un-edited unit.
    after: the edited one.

  Returns:
    The largest Hausdorff distance between corresponding tiles, or
    None when the two cannot be corresponded. Hausdorff rather than
    centroid distance because what a person sees is the WORST gap
    between the old outline and the new one, which is exactly where a
    handle drawn on the old outline would sit.
  """
  a = before.tiles.reset_index(drop=True)
  b = after.tiles.reset_index(drop=True)
  if len(a) != len(b):
    return None
  return max(float(ga.hausdorff_distance(gb))
             for ga, gb in zip(a.geometry, b.geometry))


for family, n in DESIGNS:
  spec = catalog.TILINGS_BY_N[n].get(family)
  if spec is None:
    print(f"\n--- {family} n={n}: not in the catalogue at that count ---")
    continue
  unit = catalog.make_unit(spec, spacing=500.0, crs=3857)
  built, why = topology_edits.build(unit)
  print(f"\n=== {family} n={n} (span {span(unit):.1f}) ===")
  if built is None:
    print(f"  no topology: {why}")
    continue
  topology = built["topology"] if isinstance(built, dict) else built
  edges = sorted({e.label for e in topology.edges.values()
                  if getattr(e, "label", None)})
  points = sorted({v.label for v in topology.points.values()
                   if getattr(v, "label", None)})

  for how, spec_of in topology_edits.MANIPULATIONS.items():
    target = (points[0] if spec_of["target"] == "vertex" else edges[0])
    for many in (1, 4):
      args = {}
      for name, _label, low, high, step, _dp in spec_of["args"]:
        value = step * many
        # Whole-number arguments are counts, and a count of eight
        # zigzags is not four times a count of two in any sense a
        # person means; clamp to the control's own range.
        args[name] = min(max(value, low), high)
        if name in topology_edits._WHOLE:
          args[name] = float(int(args[name]))
      edited, refusals = topology_edits.apply(topology, [
        {"classes": target, "how": how, "args": args}])
      if edited is None:
        print(f"  {how:<13} x{many}  refused: {refusals}")
        continue
      moved = worst_move(unit, edited)
      if moved is None:
        print(f"  {how:<13} x{many}  tiles cannot be corresponded")
        continue
      share = moved / span(unit)
      # A REFUSAL AND A NO-OP READ THE SAME IN A DISTANCE. `apply`
      # can hand back the unchanged unit with a reason, and a first
      # pass that printed only the distance reported both as "moves
      # NOTHING" -- which is this project's own rule that a check
      # must say what it FOUND rather than which branch it reached.
      note = ""
      if refusals:
        note = f"  <- REFUSED: {refusals}"
      elif moved < 1e-6:
        note = "  <- applied and moved NOTHING"
      print(f"  {how:<13} x{many}  args {args}  worst move {moved:9.3f} "
            f"= {share * 100:6.2f}%{note}")
