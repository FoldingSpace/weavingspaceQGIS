"""Holes you can see through, and whether they behave like a structure.

docs/process/the-topology-of-a-weave-and-its-holes.md settles that a
weave's strand classes come from the interlacement and not from the
polygons. That leaves ONE kind of thing where a tiling has two: a
tiling's structure has edges AND vertices, a weave read as strands has
only strands.

THE MAINTAINER'S QUESTION (2026-09-08) is whether the second kind is
the APERTURE -- a hole through the cloth -- and whether the daylight a
low aspect opens should count as one. Two readings are open:

  the gaps a dropped warp and a dropped weft leave WHERE THEY CROSS
    are holes through the cloth and belong in any weaving topology
  the daylight a narrow strand leaves is a fact about the drawing and
    should be disregarded, the structure being taken from the
    conceptual full-width weave

THE DISCRIMINATOR IS NOT A MATTER OF TASTE. An aperture left by two
dropped strands SURVIVES as the strand width goes to one; an aperture
opened by the strand width CLOSES. So the two readings can be told
apart by measurement rather than argued, and what the choice costs can
be measured too.

WHAT IT REPORTS, per weave and per aspect: how many apertures a
fundamental cell holds, how many CLASSES they fall into by the strands
that bound them, whether that class count holds as the aspect varies,
and which apertures are still there at an aspect just below one, which
are the ones the code rather than the drawing put there.

Run it in the reference venv, under the watchdog:

    python3 tools/watchdog.py --stall 600 --timeout 3600 -- \
      ./.venv-reference/bin/python3 \
      tools/probes/the_apertures_a_weave_leaves.py

NO TIMINGS ARE TAKEN; every figure is structural.
"""
import collections
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
import shapely.affinity  # noqa: E402

from weavingspace_qgis import catalog  # noqa: E402

SPACING = 1000.0
# 0.999 rather than 1.0: at exactly one the library fuses pieces that
# share a label and the design stops being the same design, which is
# measured in the report. Just below it the strands meet and nothing
# fuses, so what remains open is what the CODE left open.
ASPECTS = (0.999, 0.9, 0.75, 0.5, 0.25)
WEAVES = ("plain weave a|b", "twill weave a|b", "basket weave ab|cd",
          "twill weave a|b-", "plain weave ab-|cd-", "twill weave ab-|cd-")
# An aperture under a thousandth of a cell is a numerical sliver
# between two strands that meet, not a hole anybody could see through.
SLIVER = 1.0 / 1000.0


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


def lattice_of(unit) -> list:
  """The two shortest non-parallel translations the unit repeats by.

  Args:
    unit: a Tileable.

  Returns:
    A list of two (dx, dy) pairs.

  IT READS THE VECTORS' VALUES rather than looking them up by key: a
  lookup by `(1, 0)` and `(0, 1)` misses every hex-keyed family and
  draws one copy in silence, which this project has already paid for
  once in the dual's own overlay.
  """
  found = []
  for value in unit.vectors.values():
    dx, dy = value[0], value[1]
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
      continue
    found.append((dx, dy))
  found.sort(key=lambda v: v[0] ** 2 + v[1] ** 2)
  out = []
  for candidate in found:
    if not out:
      out.append(candidate)
      continue
    ax, ay = out[0]
    if abs(ax * candidate[1] - ay * candidate[0]) > 1e-6:
      out.append(candidate)
      break
  return out


def _in_the_repeat(point, vectors, origin) -> tuple:
  """Where a point sits inside one repeat, as a fraction of the lattice.

  Args:
    point: a shapely Point.
    vectors: the two lattice translations.
    origin: a Point to measure from.

  Returns:
    A pair of fractions in [0, 1), rounded, so two copies of one
    aperture answer the same pair and a distinct aperture answers a
    different one.

  THE ROUNDING IS THE TOLERANCE and is deliberately coarse: copies of
  one aperture agree to floating point, and two genuinely different
  apertures in a weave are at least a fraction of a cell apart.
  """
  (ax, ay), (bx, by) = vectors[0], vectors[1]
  determinant = ax * by - ay * bx
  if abs(determinant) < 1e-9:
    return (0.0, 0.0)
  dx, dy = point.x - origin.x, point.y - origin.y
  first = (dx * by - dy * bx) / determinant
  second = (ax * dy - ay * dx) / determinant
  return (round(first % 1.0, 3), round(second % 1.0, 3))


def apertures_of(unit, rings: int = 2) -> list:
  """The holes a patch of the design encloses, one repeat's worth.

  Args:
    unit: a Tileable, at the strand width in force.
    rings: how many rings of copies to lay around the middle one.

  Returns:
    A list of (polygon, bounding_ids) for the apertures whose centre
    lies in the middle fundamental cell, so each is counted once
    however many copies of the design enclose it.

  A HOLE HAS TO BE ENCLOSED TO BE A HOLE, which is why this lays a
  patch rather than asking one unit. Daylight that reaches the edge of
  a single unit is not an aperture; it is the same daylight continuing
  into the next copy, and asking one unit alone would count the design
  as one enormous hole. The interiors of the patch's union are exactly
  the ground you could see through.
  """
  tiles = [(g, str(i)) for g, i in
           zip(unit.tiles.geometry, unit.tiles["tile_id"])
           if g.geom_type == "Polygon"]
  vectors = lattice_of(unit)
  if len(vectors) < 2:
    return []
  placed = []
  for i in range(-rings, rings + 1):
    for j in range(-rings, rings + 1):
      dx = i * vectors[0][0] + j * vectors[1][0]
      dy = i * vectors[0][1] + j * vectors[1][1]
      for geometry, tile_id in tiles:
        placed.append((shapely.affinity.translate(geometry, dx, dy),
                       tile_id))
  patch = shapely.union_all([g for g, _i in placed])
  # AN APERTURE IS A COMPONENT OF THE DAYLIGHT THAT DOES NOT REACH THE
  # PATCH'S EDGE, taken by DIFFERENCE rather than from the union's own
  # interiors: a first version read `patch.interiors` and counted an
  # aperture only where its centroid fell in a box built from the
  # lattice vectors, and that box was not the fundamental cell. Four
  # weaves of six then answered exactly zero, which is the shape of an
  # instrument agreeing with itself; the same designs hold hundreds of
  # enclosed holes when the daylight is asked directly.
  frame = shapely.box(*patch.bounds).buffer(-1.2 * SPACING)
  daylight = frame.difference(patch)
  out, seen = [], set()
  for part in getattr(daylight, "geoms", [daylight]):
    if part.geom_type != "Polygon" or part.is_empty:
      continue
    if part.distance(frame.exterior) < 1.0:
      continue                      # it runs off the patch: not a hole
    # COUNTED BY ITS PLACE IN THE REPEAT, not by whether its centre
    # falls inside one drawn cell: an aperture straddling the cell's
    # edge is in or out according to where its centroid lands, which
    # made a plain weave report five apertures at one strand width and
    # one at another on a design with four crossing sites. Reducing
    # the centre modulo the lattice puts every copy of one aperture at
    # the same place, and the distinct places ARE the count per cell.
    at = _in_the_repeat(part.centroid, vectors, patch.centroid)
    if at in seen:
      continue
    seen.add(at)
    touching = sorted(tile_id for g, tile_id in placed
                      if g.distance(part) < SPACING / 1000.0)
    out.append((part, tuple(touching)))
  return out


def read(name: str, aspect: float) -> dict:
  """Measure one weave's apertures at one strand width.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.

  Returns:
    A dict of readings for one row of the report.
  """
  unit = catalog.make_unit(spec_for(name), spacing=SPACING, crs=None,
                           aspect=aspect)
  cell = unit.prototile.geometry[0].area
  found = apertures_of(unit)
  real = [(h, ids) for h, ids in found if h.area / cell > SLIVER]
  classes = collections.Counter(ids for _h, ids in real)
  return {
    "aspect": aspect,
    "apertures": len(real),
    "slivers": len(found) - len(real),
    "classes": len(classes),
    "shape": sorted(classes.values(), reverse=True),
    "area": sum(h.area for h, _i in real) / cell,
    "largest": max((h.area / cell for h, _i in real), default=0.0),
  }


def main() -> None:
  """Report each weave's apertures across the strand widths."""
  for name in WEAVES:
    print(f"\n=== {name} ===")
    rows = []
    for aspect in ASPECTS:
      try:
        row = read(name, aspect)
      except Exception as exc:                           # noqa: BLE001
        print(f"  aspect {aspect:<6} {type(exc).__name__}: {exc}")
        continue
      rows.append(row)
      print(f"  aspect {row['aspect']:<6} {row['apertures']:>3} apertures "
            f"({row['slivers']:>2} slivers dropped)  "
            f"{row['classes']:>2} class(es) {row['shape']}  "
            f"covering {row['area']:.4f} of a cell, largest "
            f"{row['largest']:.4f}")
    surviving = [r for r in rows if r["aspect"] == 0.999]
    if surviving:
      held = surviving[0]["apertures"]
      print(f"  AT FULL WIDTH {held} aperture(s) remain, so {held} of them "
            f"are what the CODE left open rather than the drawing")
    varying = {(r["classes"], tuple(r["shape"])) for r in rows
               if r["aspect"] < 0.999}
    if varying:
      print(f"  below full width the aperture classes are "
            f"{'INVARIANT' if len(varying) == 1 else 'MOVING'}")


if __name__ == "__main__":
  main()
