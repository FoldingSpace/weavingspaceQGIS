"""Insets, aspect and missing strands: three absences that look alike.

A thin weave's drawing is full of empty ground, and the eye cannot
tell one kind of emptiness from another. Three mechanisms open it, and
they are different KINDS of thing:

  an INSET is a distance applied to the finished unit, after the
    design is built, and is a display setting rather than a fact
    about the weave
  an ASPECT gap is the daylight a strand narrower than its spacing
    leaves, incidental to the design and not removable by rebuilding
    at 1.0, which fuses same-label pieces into a different design
  a MISSING STRAND is declared by a hyphen in the strands code, and
    is the one absence the specification itself asserts

This probe draws all three at once on a weave that has all three, so
the claim in the report is a picture rather than a sentence, and it
draws the second figure the report needs: what makes an edit
admissible on a weave, which is not what makes one admissible on a
tiling.

Run it in the reference venv:

    ./.venv-reference/bin/python3 tools/probes/three_kinds_of_absence.py

NO TIMINGS ARE TAKEN. The first figure is measured from the library;
the second is a schematic, drawn from coordinates written here, and
says so in its caption so nobody quotes it as a measurement.
"""
import faulthandler
import os
import signal
import sys
import warnings

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "weavingspace_qgis", "vendor"))

warnings.filterwarnings("ignore", category=RuntimeWarning)
faulthandler.register(signal.SIGUSR1)

import shapely  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402

SPACING = 1000.0
ASPECT = 0.6
INSET = 0.10
WEAVE = "plain weave ab-|cd-"
IMAGES = os.path.join(HERE, "docs", "process", "images", "holes-as-tiles")

STRAND_FILL = "#4c72b0"
INSET_FILL = "#b4c7e7"
ASPECT_FILL = "#dcdcdc"
DROPPED_FILL = "#f0c987"


def spec_for(name: str) -> dict:
  """The catalogue's own entry for a weave, looked up rather than typed.

  Args:
    name: the catalogue key.

  Returns:
    The spec dict `catalog.make_unit` takes.

  Raises:
    KeyError: where no entry of that name exists.
  """
  for entries in catalog.TILINGS_BY_N.values():
    if name in entries:
      return entries[name]
  raise KeyError(name)


def parts_of(geometry) -> list:
  """A geometry's non-trivial polygonal components.

  Args:
    geometry: any shapely geometry, or None.

  Returns:
    A list of Polygons, slivers under a square unit dropped.
  """
  if geometry is None or geometry.is_empty:
    return []
  return [g for g in getattr(geometry, "geoms", [geometry])
          if g.geom_type == "Polygon" and not g.is_empty and g.area > 1]


def parts_of_any(geometry) -> list:
  """A geometry's polygonal components, keeping the small ones.

  Args:
    geometry: any shapely geometry.

  Returns:
    A list of Polygons. `parts_of` drops slivers because a boolean
    difference on real geometry leaves them; a schematic's cut ribbon
    pieces are small on purpose, so nothing is dropped here.
  """
  if geometry is None or geometry.is_empty:
    return []
  return [g for g in getattr(geometry, "geoms", [geometry])
          if g.geom_type == "Polygon" and not g.is_empty]


def draw(axis, polygons, fill, edge) -> None:
  """Paint a list of polygons onto an axis in one colour.

  Args:
    axis: the matplotlib axis to paint on.
    polygons: shapely Polygons; anything else is skipped.
    fill: face colour.
    edge: outline colour.

  Returns:
    None. The axis is mutated.
  """
  for polygon in polygons:
    if polygon.geom_type != "Polygon" or polygon.is_empty:
      continue
    axis.add_patch(MplPolygon(list(polygon.exterior.coords), closed=True,
                              facecolor=fill, edgecolor=edge, linewidth=0.6))


def the_three_absences(path: str) -> dict:
  """Draw one weave's daylight coloured by which mechanism opened it.

  Args:
    path: where to write the PNG.

  Returns:
    A dict of the areas found, as fractions of the unit's own extent,
    so the figure's caption can quote numbers taken here rather than
    numbers remembered.

  THE INSET RING IS MEASURED AS A DIFFERENCE, un-inset strand minus
  inset strand, which is exactly what an inset does and needs no
  assumption about how the library implements it. Each layer is
  painted from its exterior alone, so the ring pieces are drawn BEFORE
  the strands rather than over them: a ring is a polygon with a hole,
  and a filled exterior would hide the strand it surrounds.
  """
  spec = spec_for(WEAVE)
  unit = catalog.make_unit(spec, spacing=SPACING, crs=None, aspect=ASPECT)
  inset = unit.inset_tiles(INSET * SPACING)
  thick = [g for g in unit.tiles.geometry if g.geom_type == "Polygon"]
  thin = [g for g in inset.tiles.geometry if g.geom_type == "Polygon"]
  kinds = te.daylight_by_kind(unit, spec, SPACING, ASPECT)

  ring = shapely.union_all(thick).difference(shapely.union_all(thin))
  width = parts_of(kinds["width"])
  conscious = parts_of(kinds["conscious"])

  figure, axes = plt.subplots(1, 4, figsize=(15.5, 4.4))
  strands_last = (thin, STRAND_FILL, "#20304a")
  panels = (
    ("the design as drawn", [(parts_of(ring), INSET_FILL, "#8fa8cd"),
                             (width, ASPECT_FILL, "#9a9a9a"),
                             (conscious, DROPPED_FILL, "#c8a15a"),
                             strands_last]),
    ("the inset ring, a display setting",
     [(parts_of(ring), INSET_FILL, "#8fa8cd"), strands_last]),
    ("the aspect daylight, incidental",
     [(width, ASPECT_FILL, "#9a9a9a"), strands_last]),
    ("the missing strands, declared",
     [(conscious, DROPPED_FILL, "#c8a15a"), strands_last]),
  )
  for axis, (title, layers) in zip(axes, panels):
    for polygons, fill, edge in layers:
      draw(axis, polygons, fill, edge)
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title(title, fontsize=9, pad=8)
    axis.relim()
    axis.autoscale()
  figure.suptitle(f"{WEAVE} at aspect {ASPECT} with a {int(INSET * 100)}% "
                  f"tile inset: three mechanisms, one look", fontsize=10)
  figure.tight_layout(rect=(0, 0, 1, 0.88))
  figure.savefig(path, dpi=140)
  plt.close(figure)

  total = shapely.union_all(thick + width + conscious).area
  return {
    "strands": len(thick),
    "inset_area": ring.area / total,
    "aspect_area": shapely.union_all(width).area / total if width else 0.0,
    "dropped_area": (shapely.union_all(conscious).area / total
                     if conscious else 0.0),
  }


def _ribbon(x0, y0, x1, y1, half):
  """A straight ribbon of constant width between two points.

  Args:
    x0, y0: one end of the centreline.
    x1, y1: the other end.
    half: half the ribbon's width.

  Returns:
    A shapely Polygon, mitred so the ends are square.
  """
  return shapely.LineString([(x0, y0), (x1, y1)]).buffer(
    half, cap_style="flat", join_style="mitre")


def _interlacement(warp_xs, weft_ys, half=0.22):
  """Cut two families of ribbons against each other into a woven picture.

  Args:
    warp_xs: the vertical strands' positions, in order of identity.
    weft_ys: the horizontal strands' positions, in order of identity.
    half: half a ribbon's width.

  Returns:
    A pair of lists, the warps and the wefts, each strand cut where it
    passes beneath the other family.

  OVER AND UNDER IS DECIDED BY IDENTITY RATHER THAN BY POSITION, warp
  i riding over weft j where i + j is even. That is what makes the
  third panel say something: move a strand past its neighbour and the
  pattern it carries goes with it, so two strands lying side by side
  can end up riding over the same warps, which is a different cloth
  rather than the same cloth drawn differently.
  """
  warps = [_ribbon(x, -0.7, x, 3.7, half) for x in warp_xs]
  wefts = [_ribbon(-0.7, y, 3.7, y, half) for y in weft_ys]
  cut_warps, cut_wefts = [], []
  for i, warp in enumerate(warps):
    piece = warp
    for j, weft in enumerate(wefts):
      if (i + j) % 2:
        piece = piece.difference(weft.buffer(0.015))
    cut_warps.append(piece)
  for j, weft in enumerate(wefts):
    piece = weft
    for i, warp in enumerate(warps):
      if not (i + j) % 2:
        piece = piece.difference(warp.buffer(0.015))
    cut_wefts.append(piece)
  return cut_warps, cut_wefts


def what_makes_an_edit_admissible(path: str) -> None:
  """Draw the condition an edit on a weave has to meet.

  Args:
    path: where to write the PNG.

  Returns:
    None; the PNG is written.

  THIS FIGURE IS A SCHEMATIC. Its coordinates are written here rather
  than read from the library, because the point is a condition on
  edits and not a measurement of any particular design; the caption in
  the report says so.
  """
  warp_xs = (0.6, 1.8, 3.0)
  panels = (
    ("as built", (0.6, 1.8, 3.0), None, "#4c72b0"),
    ("a strand nudged, keeping its place in the order",
     (0.6, 2.3, 3.0), 1.8, "#4c72b0"),
    ("a strand carried past its neighbour: a different cloth",
     (0.6, 3.65, 3.0), 1.8, "#b04c58"),
  )
  figure, axes = plt.subplots(1, 3, figsize=(12.5, 4.6))
  for axis, (title, weft_ys, ghost, colour) in zip(axes, panels):
    warps, wefts = _interlacement(warp_xs, weft_ys)
    for warp in warps:
      draw(axis, parts_of_any(warp), "#c8ccd4", "#8a8f99")
    for index, weft in enumerate(wefts):
      fill = colour if index == 1 else "#8fa8cd"
      draw(axis, parts_of_any(weft), fill, "#20304a")
    if ghost is not None:
      axis.add_patch(MplPolygon(
        list(_ribbon(-0.7, ghost, 3.7, ghost, 0.22).exterior.coords),
        closed=True, facecolor="none", edgecolor="#9a9a9a", linewidth=0.8,
        linestyle=(0, (4, 3))))
    axis.set_xlim(-0.75, 3.75)
    axis.set_ylim(-0.75, 4.1)
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title(title, fontsize=9, pad=8)
  figure.suptitle("What an edit must preserve on a weave is the "
                  "interlacement, not the cover", fontsize=10)
  figure.tight_layout(rect=(0, 0, 1, 0.88))
  figure.savefig(path, dpi=140)
  plt.close(figure)


def main() -> None:
  """Write both figures and print what the first one measured."""
  os.makedirs(IMAGES, exist_ok=True)
  found = the_three_absences(os.path.join(IMAGES, "three-kinds-of-absence.png"))
  print(f"{WEAVE} at aspect {ASPECT}, tile inset {INSET:.2f} of the spacing")
  print(f"  strand pieces           {found['strands']}")
  print(f"  inset ring              {found['inset_area']:.4f} of the ground")
  print(f"  aspect daylight         {found['aspect_area']:.4f}")
  print(f"  missing strands' bands  {found['dropped_area']:.4f}")
  what_makes_an_edit_admissible(
    os.path.join(IMAGES, "what-an-edit-must-preserve.png"))
  print(f"\nfigures written to {IMAGES}")


if __name__ == "__main__":
  main()
