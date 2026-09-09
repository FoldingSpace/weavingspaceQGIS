"""What gluing a hole's sides means, drawn for a reader who has not met it.

The maintainer's construction (2026-09-08) for treating a weave's
aspect gaps as though they were not there is a QUOTIENT: the hole stays
in the drawing and is declared away in the structure, its opposite
sides read as touching and its four corners as one point. Nothing
moves, which is what makes it work where every geometric neutralisation
of the strand width failed.

This draws the operation rather than describing it, and draws the
triaxial case beside it, where "opposite" names nothing and the rule
has to be stated in terms of a strand's DIRECTION instead.

IT IS A SCHEMATIC. Every coordinate is written here rather than read
from the library, because the subject is an operation on a structure
and not a measurement of any design.

    ./.venv-reference/bin/python3 \
      tools/probes/what_a_quotient_does_to_a_hole.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMAGES = os.path.join(HERE, "docs", "process", "images", "holes-as-tiles")

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402

WARP = "#4c72b0"
WEFT = "#8fa8cd"
THIRD = "#6a9a63"
HOLE = "#e8e2d4"
INK = "#20304a"


def ribbon(axis, x0, y0, x1, y1, half, colour):
  """A straight ribbon of constant width, drawn on an axis.

  Args:
    axis: the matplotlib axis.
    x0, y0, x1, y1: the centreline's ends.
    half: half the ribbon's width.
    colour: the face colour.

  Returns:
    None; the axis is mutated.
  """
  length = math.hypot(x1 - x0, y1 - y0)
  if length == 0:
    return
  nx, ny = -(y1 - y0) / length * half, (x1 - x0) / length * half
  axis.add_patch(MplPolygon(
    [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
     (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)],
    closed=True, facecolor=colour, edgecolor=INK, linewidth=0.8))


def tick(axis, x0, y0, x1, y1, count, colour=INK):
  """Mark an edge with one or two arrowheads, the usual gluing notation.

  Args:
    axis: the matplotlib axis.
    x0, y0, x1, y1: the edge's ends, the arrow pointing from first to
      second.
    count: how many arrowheads, which is what says WHICH pair of edges
      is glued to which.
    colour: the arrow colour.

  Returns:
    None; the axis is mutated.
  """
  for step in range(count):
    at = 0.42 + 0.16 * step
    axis.annotate(
      "", xytext=(x0 + (x1 - x0) * (at - 0.06), y0 + (y1 - y0) * (at - 0.06)),
      xy=(x0 + (x1 - x0) * at, y0 + (y1 - y0) * at),
      arrowprops=dict(arrowstyle="-|>", color=colour, lw=1.4,
                      mutation_scale=15))


def corners(axis, points, filled=False):
  """Draw a hole's corners, open where they are still distinct.

  Args:
    axis: the matplotlib axis.
    points: the corner positions.
    filled: True once they have been identified to one point.

  Returns:
    None; the axis is mutated.
  """
  for x, y in points:
    axis.plot([x], [y], marker="o", markersize=9,
              markerfacecolor=INK if filled else "white",
              markeredgecolor=INK, markeredgewidth=1.6, zorder=5)


def main() -> None:
  """Draw the four panels and write the figure."""
  os.makedirs(IMAGES, exist_ok=True)
  figure, axes = plt.subplots(1, 4, figsize=(19.0, 5.2))

  # 1: the hole as a tile
  axis = axes[0]
  for y, c in ((-1.4, WEFT), (1.4, WEFT)):
    ribbon(axis, -3.2, y, 3.2, y, 0.7, c)
  for x, c in ((-1.4, WARP), (1.4, WARP)):
    ribbon(axis, x, -3.2, x, 3.2, 0.7, c)
  axis.add_patch(MplPolygon([(-0.7, -0.7), (0.7, -0.7), (0.7, 0.7),
                             (-0.7, 0.7)], closed=True, facecolor=HOLE,
                            edgecolor=INK, linewidth=1.2))
  corners(axis, [(-0.7, -0.7), (0.7, -0.7), (0.7, 0.7), (-0.7, 0.7)])
  axis.set_title("as a tile: the hole has four sides and four\n"
                 "corners, and the structure counts them all",
                 fontsize=9, pad=8)

  # 2: the identification
  axis = axes[1]
  for y, c in ((-1.4, WEFT), (1.4, WEFT)):
    ribbon(axis, -3.2, y, 3.2, y, 0.7, c)
  for x, c in ((-1.4, WARP), (1.4, WARP)):
    ribbon(axis, x, -3.2, x, 3.2, 0.7, c)
  axis.add_patch(MplPolygon([(-0.7, -0.7), (0.7, -0.7), (0.7, 0.7),
                             (-0.7, 0.7)], closed=True, facecolor=HOLE,
                            edgecolor=INK, linewidth=1.2))
  tick(axis, -0.7, -0.7, 0.7, -0.7, 1)
  tick(axis, -0.7, 0.7, 0.7, 0.7, 1)
  tick(axis, -0.7, -0.7, -0.7, 0.7, 2)
  tick(axis, 0.7, -0.7, 0.7, 0.7, 2)
  corners(axis, [(-0.7, -0.7), (0.7, -0.7), (0.7, 0.7), (-0.7, 0.7)])
  axis.set_title("the gluing: sides carrying the same arrow are\n"
                 "declared one side, and the corners one point",
                 fontsize=9, pad=8)

  # 3: what it means
  axis = axes[2]
  for y, c in ((-0.7, WEFT), (0.7, WEFT)):
    ribbon(axis, -3.2, y, 3.2, y, 0.7, c)
  for x, c in ((-0.7, WARP), (0.7, WARP)):
    ribbon(axis, x, -3.2, x, 3.2, 0.7, c)
  corners(axis, [(0.0, 0.0)], filled=True)
  # THE LINKS CROSS THE SEAM THEY ARE ABOUT, rather than standing off
  # to the side where they read as dimension lines.
  axis.annotate("", xytext=(-1.15, 1.9), xy=(1.15, 1.9),
                arrowprops=dict(arrowstyle="<|-|>", color="#b04c58", lw=1.8,
                                mutation_scale=14))
  axis.annotate("", xytext=(1.9, -1.15), xy=(1.9, 1.15),
                arrowprops=dict(arrowstyle="<|-|>", color="#b04c58", lw=1.8,
                                mutation_scale=14))
  axis.set_title("what it says: the two warps are adjacent and\n"
                 "the two wefts are, and the corners are one point",
                 fontsize=9, pad=8)

  # 4: the triaxial case
  axis = axes[3]
  # THE THREE RIBBONS STAND OFF FAR ENOUGH TO LEAVE A TRIANGLE: at a
  # smaller offset they overlap so heavily that the aperture stops
  # reading as one, which the first draft of this panel did.
  for angle, colour in ((90, WARP), (210, WEFT), (330, THIRD)):
    radians = math.radians(angle)
    cx, cy = math.cos(radians) * 1.35, math.sin(radians) * 1.35
    ribbon(axis, cx - math.sin(radians) * 3.6, cy + math.cos(radians) * 3.6,
           cx + math.sin(radians) * 3.6, cy - math.cos(radians) * 3.6,
           0.52, colour)
  triangle = [(math.cos(math.radians(a)) * 0.96,
               math.sin(math.radians(a)) * 0.96) for a in (30, 150, 270)]
  axis.add_patch(MplPolygon(triangle, closed=True, facecolor=HOLE,
                            edgecolor=INK, linewidth=1.2))
  corners(axis, triangle)
  axis.set_title("triaxially there are no opposite sides: the rule\n"
                 "is that two sides glue where their strands share a\n"
                 "direction, which here no two do",
                 fontsize=9, pad=8)

  for axis in axes:
    axis.set_xlim(-3.4, 3.4)
    axis.set_ylim(-3.4, 3.4)
    axis.set_aspect("equal")
    axis.axis("off")
  figure.suptitle("A quotient declares parts of a structure to be one "
                  "part. Nothing is moved and nothing is deleted.",
                  fontsize=11)
  figure.tight_layout(rect=(0, 0, 1, 0.90))
  path = os.path.join(IMAGES, "what-a-quotient-does.png")
  figure.savefig(path, dpi=140)
  plt.close(figure)
  print(f"figure written to {path}")


if __name__ == "__main__":
  main()
