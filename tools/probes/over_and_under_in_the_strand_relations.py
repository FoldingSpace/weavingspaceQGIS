"""Three ways of reading a weave's over and under, and why none works.

The relations between strands stay the size a tiling's classes are,
where anything computed from the absorbed polygons multiplies. But
adjacency is blind to the distinction a weave exists to make: it
records that two strands meet, not which passes over.

This probe tried to recover that from the geometry, three ways, and
keeps all three because the failures are the finding.

  DIRECT CONTACT, on the reading that the under strand is cut flush
    against the over strand's edge. It is not: a plain weave has ZERO
    contacts between its thin pieces at any aspect, the cut being set
    back across the daylight, and the two a twill shows come and go
    with the strand width.

  WHOSE CLAIMED GROUND REACHES THE OTHER'S EDGE, on the reading that
    the over strand covers the crossing at full width and so is handed
    that ground by the replacement attribution. It classifies parallel
    strands as passing over one another, leaves four relations of five
    unclassified, and stops being invariant.

  END-FACE AGAINST SIDE-FACE, on the reading that the cut strand meets
    the crossing end-on whether or not it touches. Every relation lands
    in the ambiguous band: five of five unclassified on a plain weave,
    at every aspect.

WHAT THAT SETTLES is not that the over and under cannot be had but that
the rendered geometry is the wrong place to look for them. Which strand
is cut at a crossing is decided by the strands code and the over-under
pattern BEFORE any polygon exists, and the library differences the
pieces accordingly. Measuring the result to recover the rule is
reverse-engineering something already in hand, and this is what it
costs.

The parallel to a tiling is closer than it looks. The library does not
measure pictures to find a tiling's classes either; it derives them
from the design's symmetries. A weave's combinatorics should likewise
come from its specification, with geometry used for what geometry is
good for -- which strands are adjacent, and where.

The relations and the attribution below stand; only the over-and-under
column is unreliable, and it is reported with its unclassified count so
that nobody reads a partial answer as a whole one.

Run it in the reference venv, under the watchdog:

    python3 tools/watchdog.py --stall 300 --timeout 3600 -- \
      ./.venv-reference/bin/python3 \
      tools/probes/over_and_under_in_the_strand_relations.py

NO TIMINGS ARE TAKEN; every figure is structural.
"""
import faulthandler
import math
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
import shapely.ops  # noqa: E402

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402

SPACING = 1000.0
NEARLY_SOLID = 0.999
ASPECTS = (0.9, 0.75, 0.5, 0.25)
WEAVES = ("plain weave a|b", "twill weave a|b", "basket weave ab|cd",
          "twill weave a|b-")
A_SEGMENT = 1.0
PARALLEL = 0.99


def spec_for(name):
  """The catalogue's own entry, looked up rather than typed.

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


def parts_of(geometry):
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


def axis_of(piece, width):
  """A strand piece's own direction, or None where it is not one.

  Args:
    piece: a strand polygon.
    width: the strand's width, which is aspect times spacing.

  Returns:
    A unit vector along the strand, or None where neither side of the
    piece is the strand's width.

  THE LONGER SIDE IS NOT THE AXIS. A weave cuts the strand passing
  under into pieces wider than they are long, so "longer" names the
  across direction on exactly the pieces this probe is about.
  """
  rect = piece.minimum_rotated_rectangle
  coords = list(rect.exterior.coords)[:5]
  if len(coords) < 3:
    return None
  first = (coords[1][0] - coords[0][0], coords[1][1] - coords[0][1])
  second = (coords[2][0] - coords[1][0], coords[2][1] - coords[1][1])
  one, two = math.hypot(*first), math.hypot(*second)
  if one < 1e-9 or two < 1e-9:
    return None
  if abs(one - width) < abs(two - width):
    along, length = second, two
  else:
    along, length = first, one
  return (along[0] / length, along[1] / length)


def direction_of(line):
  """The principal direction of a shared boundary.

  Args:
    line: the geometry two pieces share.

  Returns:
    A unit vector along its longest segment, or None where it has none.
    The longest segment is used rather than end-to-end, since a shared
    boundary may be several collinear pieces with a jog between them.
  """
  best, best_length = None, 0.0
  for part in getattr(line, "geoms", [line]):
    if not hasattr(part, "coords"):
      continue
    points = list(part.coords)
    for start, end in zip(points, points[1:]):
      length = math.hypot(end[0] - start[0], end[1] - start[1])
      if length > best_length:
        best, best_length = (end[0] - start[0], end[1] - start[1]), length
  if best is None or best_length < 1e-9:
    return None
  return (best[0] / best_length, best[1] / best_length)


def relations(name, aspect):
  """Every relation between the strands of one weave, over and under kept.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.

  Returns:
    A dict counting the relations and naming them by strand letter, and
    per strand how many neighbours it passes over and under.
  """
  spec = spec_for(name)
  thin = catalog.make_unit(spec, spacing=SPACING, crs=None, aspect=aspect)
  full = catalog.make_unit(spec, spacing=SPACING, crs=None,
                           aspect=NEARLY_SOLID)
  strands = list(thin.tiles.geometry)
  letters = [str(x) for x in thin.tiles.tile_id]
  width = aspect * SPACING
  axes = [axis_of(piece, width) for piece in strands]

  # The daylight goes to the strand it stands in for, so an alongside
  # relation can be seen at all.
  kinds = te.daylight_by_kind(thin, spec, SPACING, aspect)
  full_tiles = list(full.tiles.geometry)
  claimed = [[] for _ in strands]
  for piece in parts_of(kinds["width"]):
    best, best_area = None, 0.0
    for index in range(min(len(strands), len(full_tiles))):
      shared = piece.intersection(full_tiles[index]).area
      if shared > best_area:
        best, best_area = index, shared
    if best is not None:
      claimed[best].append(piece)
  absorbed = [shapely.union_all([s] + claimed[i])
              for i, s in enumerate(strands)]

  def facing(piece, axis, towards):
    """Whether a piece meets its neighbour end-on or side-on.

    Args:
      piece: the strand piece being asked about.
      axis: that piece's own direction, from `axis_of`.
      towards: the neighbouring piece, which fixes where to look.

    Returns:
      The fraction of the boundary nearest `towards` that runs ACROSS
      the piece's own axis, or None where nothing was found. Near 1
      means an end-face, which is where a strand was cut; near 0 means
      a side, where it runs past uninterrupted. In practice almost
      every reading lands between the two, which is why this test is
      recorded as a failure.
    """
    if axis is None:
      return None
    near = shapely.ops.nearest_points(piece, towards)[0]
    window = near.buffer(width * 0.6)
    edge = piece.boundary.intersection(window)
    total, across = 0.0, 0.0
    for part in getattr(edge, "geoms", [edge]):
      if not hasattr(part, "coords"):
        continue
      points = list(part.coords)
      for start, end in zip(points, points[1:]):
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        if length < 1e-9:
          continue
        unit = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
        along = abs(unit[0] * axis[0] + unit[1] * axis[1])
        total += length
        if along < 0.5:
          across += length
    return None if total == 0 else across / total

  over = [0] * len(strands)
  under = [0] * len(strands)
  crossings, alongside, unclassified = [], [], []
  for i in range(len(strands)):
    for j in range(i + 1, len(strands)):
      shared = absorbed[i].boundary.intersection(absorbed[j].boundary)
      if shared.is_empty or shared.length <= A_SEGMENT:
        continue
      face_i = facing(strands[i], axes[i], strands[j])
      face_j = facing(strands[j], axes[j], strands[i])
      if face_i is None or face_j is None:
        unclassified.append((letters[i], letters[j]))
        continue
      # The strand that meets the other END-ON was cut there, so it
      # passes under; the one presenting a side runs over the top.
      if face_i > 0.6 and face_j < 0.4:
        under[i] += 1
        over[j] += 1
        crossings.append((letters[j], "over", letters[i]))
      elif face_j > 0.6 and face_i < 0.4:
        under[j] += 1
        over[i] += 1
        crossings.append((letters[i], "over", letters[j]))
      elif face_i < 0.4 and face_j < 0.4:
        alongside.append(tuple(sorted((letters[i], letters[j]))))
      else:
        unclassified.append((letters[i], letters[j]))
  return {"aspect": aspect, "strands": len(strands),
          "crossings": crossings, "alongside": alongside,
          "unclassified": unclassified,
          "over": over, "under": under, "letters": letters}


def main():
  """Read the strand relations across aspects, with the over and under."""
  for name in WEAVES:
    print(f"\n=== {name} ===")
    shapes = []
    for aspect in ASPECTS:
      row = relations(name, aspect)
      kinds = sorted({(a, b) for a, _o, b in row["crossings"]})
      along = sorted(set(row["alongside"]))
      balance = sorted({(row["over"][i], row["under"][i])
                        for i in range(row["strands"])})
      shapes.append((tuple(kinds), tuple(along), tuple(balance)))
      print(f"  aspect {row['aspect']:<5} {row['strands']:>3} strands  "
            f"{len(row['crossings']):>3} crossings  "
            f"{len(row['alongside']):>3} alongside  "
            f"{len(row['unclassified']):>2} unclassified")
      print(f"      over/under kinds : {kinds}")
      print(f"      alongside kinds  : {along}")
      print(f"      (over, under) per strand: {balance}")
    print(f"  across aspects: "
          f"{'INVARIANT' if len(set(shapes)) == 1 else 'MOVES'}")


if __name__ == "__main__":
  main()
