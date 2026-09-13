"""A weave's structure where only a MISSING STRAND counts as a gap.

Three ways of giving a thin weave a structure have been measured, and
all three treat the daylight as something to be filled or bridged:

  hole as tile      the classes then follow how the holes were cut
  contract          decomposition-free, but only an adjacency, and the
                    hyphen makes no difference to it
  veto              a missing strand does not SEPARATE anything, so
                    there is nothing for a veto to withhold

This probe tries the fourth, which is the maintainer's framing rather
than a fourth tweak of the same idea (2026-09-08): in a weaving world
the gaps that are REAL are the missing strands, and the gaps that come
from aspect or inset are not gaps at all but an artefact of how wide we
chose to draw the yarn. So rather than filling the incidental daylight,
ABSORB it -- grow each strand until it meets its neighbours -- and let
the only uncovered ground be the slot where a strand was left out.

Nothing then needs vetoing. An incidental gap cannot license a
connection because it no longer exists, and a missing strand is a hole
in the design rather than a rule about the graph.

WHAT IT MEASURES, per weave and per aspect:

  whether growing each strand by half the incidental gap actually
    closes it, and at what overlap -- the honest failure here is
    strands overrunning each other at a crossing
  what ground is left over, and whether it IS the conscious gap, which
    is the claim the whole construction rests on
  whether a topology can then be built, with the dropped slots filled
    as tiles that stand for holes
  and whether the classes hold still as the strand width varies, which
    is what the earlier constructions could not manage

Run it in the reference venv, under the watchdog:

    python3 tools/watchdog.py --stall 300 --timeout 3600 -- \
      ./.venv-reference/bin/python3 \
      tools/probes/absorbing_the_incidental_gaps.py

NO TIMINGS ARE TAKEN; every figure is structural.
"""
import copy
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

import geopandas as gpd  # noqa: E402
import shapely  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402
import weavingspace.tiling_utils as tu  # noqa: E402

SPACING = 1000.0
ASPECTS = (0.9, 0.75, 0.5, 0.25)
PLAIN = "plain weave a|b"
TWILL = "twill weave a|b"
HYPHEN = "twill weave a|b-"
WIDE_HYPHEN = "plain weave ab-|cd-"
IMAGES = os.path.join(HERE, "docs", "process", "images", "holes-as-tiles")

STRAND_FILL = "#4c72b0"
HOLE_FILL = "#f0c987"


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
    geometry: any shapely geometry.

  Returns:
    A list of Polygons, slivers under a square unit dropped.
  """
  if geometry is None or geometry.is_empty:
    return []
  return [g for g in getattr(geometry, "geoms", [geometry])
          if g.geom_type == "Polygon" and not g.is_empty and g.area > 1]


def nearest_strand_share(strands, daylight, reach: float,
                         order=None) -> list:
  """Give every piece of daylight to the strand it lies nearest.

  Args:
    strands: the weave's own tiles.
    daylight: the components of the INCIDENTAL daylight only.
    reach: half the incidental gap, which is how far a strand must grow
      to meet the one facing it.
    order: the order in which contested ground is claimed, for the
      control that asks whether the order matters. None means the
      strands' own order.

  Returns:
    One polygon per strand: the strand together with the daylight
    allotted to it. The pieces do not overlap.

  HOW IT IS DONE, and why not by a single buffer. Every strand grows at
  the same rate, and each piece of ground goes to whichever reaches it
  first, until no incidental daylight is left. That is a nearest-strand
  assignment and needs no reach chosen in advance -- which matters,
  because a single mitred buffer of half the NOMINAL gap closes a plain
  weave's uniform daylight exactly and leaves a twill's alone: six
  pieces of ground survived on a design with no hyphen in it, which the
  probe reported as ground that was never meant to be left.

  A sampled Voronoi was tried first and is worse. It assigns the same
  ground but with STEPPED boundaries where the true partition between
  facing strands is a straight midline, and the library's regularising
  step raised on those steps at two aspects of four.

  WHAT REMAINS ARBITRARY is the ground two strands reach at the same
  moment. It is settled by order, so `order` exists to let a caller ask
  whether that arbitrariness reaches the answer.
  """
  if not daylight:
    return list(strands)
  ground = shapely.union_all(daylight)
  others = shapely.union_all(strands)
  allotted = [shapely.union_all([strand]) for strand in strands]
  remaining = ground.difference(others)
  indices = list(order if order is not None else range(len(strands)))
  step = max(reach, 1.0) / 8.0
  distance = step
  while not remaining.is_empty and distance <= max(reach, 1.0) * 12:
    for index in indices:
      if remaining.is_empty:
        break
      ring = strands[index].buffer(
        distance, join_style="mitre", cap_style="square").intersection(remaining)
      pieces = parts_of(ring)
      if not pieces:
        continue
      allotted[index] = shapely.union_all([allotted[index]] + pieces)
      remaining = remaining.difference(shapely.union_all(pieces))
    distance += step
  return allotted


def absorbed(name: str, aspect: float, order=None) -> dict:
  """Give a weave's strands the daylight their own width opened.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.
    order: the order in which strands claim ground two of them reach at
      the same moment, for the control that asks whether that
      arbitrariness reaches the answer. None means the strands' own
      order.

  Returns:
    A dict of readings: the enlarged strands, the ground left over, the
    conscious gap for comparison, and the coverage figures.

  ONLY THE INCIDENTAL DAYLIGHT IS ABSORBED. The slot a hyphen leaves is
  passed over, so it survives as the one real hole in the design, which
  is the whole point of the construction.
  """
  unit = catalog.make_unit(spec_for(name), spacing=SPACING, crs=None,
                           aspect=aspect)
  strands = [g for g in unit.tiles.geometry if g.geom_type == "Polygon"]
  kinds = te.daylight_by_kind(unit, spec_for(name), SPACING, aspect)
  width = parts_of(kinds["width"])
  conscious = parts_of(kinds["conscious"])
  reach = (1.0 - aspect) * SPACING / 2.0
  fat = nearest_strand_share(strands, width, reach, order=order)
  wider = copy.deepcopy(unit)
  # DISTINCT IDS, or the regularising step dissolves the pieces that
  # share a label the moment the growth makes them touch -- which is
  # how this construction collapsed into "build at aspect 1.0" on its
  # first run, reporting two tiles where the weave has sixteen.
  wider.tiles = gpd.GeoDataFrame(
    {"tile_id": [f"s{i}" for i in range(len(fat))]},
    geometry=fat, crs=unit.tiles.crs)
  gap, overlap, left_over = te.plane_coverage(wider)
  return {"name": name, "aspect": aspect, "unit": unit, "strands": strands,
          "fat": fat, "reach": reach,
          "gap": gap, "overlap": overlap,
          "left_over": parts_of(left_over), "conscious": conscious}


def is_the_left_over_the_conscious_gap(reading) -> tuple:
  """Whether the ground the growth did not reach is exactly the hyphen's.

  Args:
    reading: an `absorbed` result.

  Returns:
    (share, sentence). The share is the left-over ground's area as a
    fraction of the conscious gap's, so 1.0 means the growth closed
    every incidental gap and left the deliberate one open. Where the
    weave's code has no hyphen the conscious gap is empty and the
    left-over ground should be too.
  """
  left = sum(p.area for p in reading["left_over"])
  meant = sum(p.area for p in reading["conscious"])
  if meant == 0:
    return (0.0 if left == 0 else float("inf"),
            "no hyphen; nothing should be left over"
            if left == 0 else f"NOTHING WAS MEANT TO BE LEFT, yet {left:.0f} is")
  return left / meant, f"{left:.0f} left of {meant:.0f} meant"


def structure_of(reading) -> dict:
  """Build a topology of the absorbed design, its holes filled as tiles.

  Args:
    reading: an `absorbed` result.

  Returns:
    A dict with the tile count and the class counts, or the reason
    there is none. THE HOLES ARE STILL FILLED, because the library
    cannot hold a design with a hole in it -- but they are filled with
    tiles that stand for the missing strands rather than for the
    incidental daylight, which is the whole difference.
  """
  pieces = []
  for hole in reading["left_over"]:
    try:
      snapped = tu.gridify(hole)
    except Exception:                                  # noqa: BLE001
      continue
    pieces.extend(g for g in getattr(snapped, "geoms", [snapped])
                  if g.geom_type == "Polygon" and g.area > 1)
  unit = copy.deepcopy(reading["unit"])
  unit.tiles = gpd.GeoDataFrame(
    {"tile_id": [f"s{i}" for i in range(len(reading["fat"]))]
                + [f"hole{i}" for i in range(len(pieces))]},
    geometry=list(reading["fat"]) + pieces, crs=unit.tiles.crs)
  try:
    unit._setup_regularised_prototile()
  except Exception as exc:                             # noqa: BLE001
    return {"note": f"regularising raised {type(exc).__name__}"}
  topology, why = te.build(unit)
  if topology is None:
    return {"note": why[:56], "tiles": len(unit.tiles), "holes": len(pieces)}
  edges = {e.label for e in topology.edges.values() if getattr(e, "label", "")}
  points = {v.label for v in topology.points.values()
            if getattr(v, "label", "")}
  return {"tiles": len(unit.tiles), "holes": len(pieces),
          "edges": len(edges), "vertices": len(points), "note": ""}


def figure(name: str, readings, path: str) -> None:
  """Draw the absorbed design at each aspect, holes picked out.

  Args:
    name: the catalogue key.
    readings: one `absorbed` result per aspect.
    path: where to write the PNG.
  """
  figure_, axes = plt.subplots(1, len(readings), figsize=(4 * len(readings), 4.4))
  for axis, reading in zip(axes, readings):
    for polygon in reading["fat"]:
      for part in getattr(polygon, "geoms", [polygon]):
        if part.geom_type != "Polygon" or part.is_empty:
          continue
        axis.add_patch(MplPolygon(list(part.exterior.coords), closed=True,
                                  facecolor=STRAND_FILL, edgecolor="#20304a",
                                  linewidth=0.5))
    for hole in reading["left_over"]:
      axis.add_patch(MplPolygon(list(hole.exterior.coords), closed=True,
                                facecolor=HOLE_FILL, edgecolor="#c8a15a",
                                linewidth=0.8))
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title(f"aspect {reading['aspect']}\n"
                   f"grown by {reading['reach']:.0f}\n"
                   f"gap {reading['gap']:.4f}  overlap {reading['overlap']:.4f}",
                   fontsize=9)
    axis.relim()
    axis.autoscale()
  figure_.suptitle(f"{name}: the incidental daylight absorbed, so only a "
                   f"missing strand is left as a hole", fontsize=10)
  figure_.tight_layout(rect=(0, 0, 1, 0.88))
  figure_.savefig(path, dpi=140)
  plt.close(figure_)


def main() -> None:
  """Absorb, check what is left, and see whether the structure holds still."""
  os.makedirs(IMAGES, exist_ok=True)
  for name in (PLAIN, TWILL, HYPHEN, WIDE_HYPHEN):
    print(f"\n=== {name} ===")
    readings, shapes = [], []
    for aspect in ASPECTS:
      reading = absorbed(name, aspect)
      share, sentence = is_the_left_over_the_conscious_gap(reading)
      built = structure_of(reading)
      readings.append(reading)
      shapes.append((built.get("edges"), built.get("vertices")))
      print(f"  aspect {aspect:<5} grew {reading['reach']:>6.1f}  "
            f"gap {reading['gap']:.6f}  overlap {reading['overlap']:.6f}  "
            f"left {len(reading['left_over'])} piece(s)  "
            f"[{sentence}]")
      print(f"                 topology: "
            f"{built.get('tiles', '-')} tiles, {built.get('holes', '-')} holes, "
            f"{built.get('edges', '-')} edge classes, "
            f"{built.get('vertices', '-')} vertex classes  {built['note']}")
    if all(s[0] is not None for s in shapes):
      print(f"  across aspects: "
            f"{'INVARIANT' if len(set(shapes)) == 1 else 'MOVES'}")
    figure(name, readings, os.path.join(
      IMAGES, f"absorbed-{name.replace(' ', '-').replace('|', '_')}.png"))
  print(f"\nfigures written to {IMAGES}")


if __name__ == "__main__":
  main()
