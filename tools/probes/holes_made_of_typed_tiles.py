"""One hole, several kinds of tile: a canonical way to cut a weave's daylight.

Filling a thin weave's daylight with tiles gives it a topology, but the
classes then follow HOW the holes were cut, and the cut was arbitrary:
the pieces a boolean difference happens to return. The same ground cut
two ways gives six edge classes or 114.

THE PROPOSAL THIS PROBE TESTS (the maintainer's, 2026-09-08) is that a
hole is not of one kind. A single connected hole in a weave whose code
drops a strand is the missing strand's own band TOGETHER WITH the
ordinary aspect gaps flanking it, and those are different things that
happen to touch. Cut a hole into tiles by what each piece is FOR, and
the decomposition stops being arbitrary:

  the band a missing strand left empty, which the strands code names
  the daylight strand WIDTH opened, which divides again by the strand
    whose width opened it -- the nearest-strand share

Both cuts are canonical. The first comes from the code rather than from
geometry; the second is a nearest-site partition, which has no freedom
in it. Neither depends on where a difference operation chose to split.

WHAT IT MEASURES, per weave and per aspect: how many tiles of each kind
the daylight becomes, whether the typed tiling builds a topology, what
classes it has, and whether those hold still as the strand width
varies -- which is the test the arbitrary cut failed.

AND IT REPORTS WHAT THE TYPES BUY. With every hole tile carrying its
kind, an edge of the topology can be asked what it lies between: two
strands, a strand and its own daylight, or a strand and a dropped
strand's band. That is the distinction the whole exercise is for, and
it is available here without contracting or vetoing anything.

Run it in the reference venv, under the watchdog:

    python3 tools/watchdog.py --stall 400 --timeout 5400 -- \
      ./.venv-reference/bin/python3 \
      tools/probes/holes_made_of_typed_tiles.py

NO TIMINGS ARE TAKEN; every figure is structural. Where the library
refuses, the exception is printed rather than the sentence our own code
composes from it, which this project has been misled by once already.
"""
import copy
import faulthandler
import os
import signal
import sys
import traceback
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
WEAVES = ("plain weave a|b", "twill weave a|b", "twill weave a|b-",
          "plain weave ab-|cd-")
IMAGES = os.path.join(HERE, "docs", "process", "images", "holes-as-tiles")

STRAND_FILL = "#4c72b0"
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
    geometry: any shapely geometry.

  Returns:
    A list of Polygons, slivers under a square unit dropped.
  """
  if geometry is None or geometry.is_empty:
    return []
  return [g for g in getattr(geometry, "geoms", [geometry])
          if g.geom_type == "Polygon" and not g.is_empty and g.area > 1]


def typed_hole_tiles(strands, width, conscious) -> list:
  """Cut the daylight into tiles by what each piece is FOR.

  Args:
    strands: the weave's own tiles.
    width: the daylight strand width opened, as components.
    conscious: the band a missing strand left, as components.

  Returns:
    A list of (kind, polygon, owner) where kind is "aspect" or
    "dropped" and owner is the index of the strand whose width opened
    an aspect piece, or None for a dropped band.

  THE ASPECT DAYLIGHT DIVIDES BY WHOSE WIDTH OPENED IT. Every strand
  grows at the same rate and each piece of ground goes to whichever
  reaches it first, which is a nearest-strand assignment and needs no
  distance chosen in advance. A single buffer of half the nominal gap
  was tried and suits only a design whose gaps are all the same width:
  it left six pieces of a twill unclaimed while closing a plain weave
  exactly.

  A hole that spans both kinds therefore becomes SEVERAL tiles, which
  is the point: the band a person left empty and the daylight either
  side of it are different things that happen to touch.
  """
  out = []
  for band in conscious:
    out.append(("dropped", band, None))
  ground = shapely.union_all(width) if width else shapely.Polygon()
  if ground.is_empty:
    return out
  remaining = ground.difference(shapely.union_all(strands))
  step = SPACING / 40.0
  distance = step
  claimed = [[] for _ in strands]
  while not remaining.is_empty and distance <= SPACING * 2:
    for index, strand in enumerate(strands):
      if remaining.is_empty:
        break
      ring = strand.buffer(distance, join_style="mitre",
                           cap_style="square").intersection(remaining)
      pieces = parts_of(ring)
      if not pieces:
        continue
      claimed[index].extend(pieces)
      remaining = remaining.difference(shapely.union_all(pieces))
    distance += step
  for index, pieces in enumerate(claimed):
    if not pieces:
      continue
    for piece in parts_of(shapely.union_all(pieces)):
      out.append(("aspect", piece, index))
  return out


def read(name: str, aspect: float) -> dict:
  """Build the typed tiling of one weave at one strand width.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.

  Returns:
    A dict of readings, with `note` carrying the reason where a step
    refused and `trace` the unswallowed traceback where one raised.
  """
  row = {"name": name, "aspect": aspect, "note": "", "trace": ""}
  unit = catalog.make_unit(spec_for(name), spacing=SPACING, crs=None,
                           aspect=aspect)
  strands = [g for g in unit.tiles.geometry if g.geom_type == "Polygon"]
  kinds = te.daylight_by_kind(unit, spec_for(name), SPACING, aspect)
  typed = typed_hole_tiles(strands, parts_of(kinds["width"]),
                           parts_of(kinds["conscious"]))
  row["strands"] = len(strands)
  row["aspect_tiles"] = sum(1 for kind, _g, _o in typed if kind == "aspect")
  row["dropped_tiles"] = sum(1 for kind, _g, _o in typed if kind == "dropped")
  row["typed"] = typed
  row["strand_shapes"] = strands

  snapped = []
  for kind, polygon, owner in typed:
    try:
      fixed = tu.gridify(polygon)
    except Exception:                                  # noqa: BLE001
      continue
    for one in getattr(fixed, "geoms", [fixed]):
      if one.geom_type == "Polygon" and one.area > 1:
        snapped.append((kind, one, owner))
  row["snapped"] = snapped

  filled = copy.deepcopy(unit)
  filled.tiles = gpd.GeoDataFrame(
    {"tile_id": [f"s{i}" for i in range(len(strands))]
                + [f"{'d' if k == 'dropped' else 'w'}{i}"
                   for i, (k, _g, _o) in enumerate(snapped)]},
    geometry=list(strands) + [g for _k, g, _o in snapped],
    crs=unit.tiles.crs)
  gap, overlap, _left = te.plane_coverage(filled)
  row["gap"], row["overlap"] = gap, overlap
  try:
    filled._setup_regularised_prototile()
  except Exception as exc:                             # noqa: BLE001
    row["note"] = f"regularising raised {type(exc).__name__}: {str(exc)[:44]}"
    row["trace"] = traceback.format_exc(limit=4)
    return row
  Topology = te._topology_class()
  try:
    topology = Topology(filled, True)
  except Exception as exc:                             # noqa: BLE001
    row["note"] = f"{type(exc).__name__}: {str(exc)[:44]}"
    row["trace"] = traceback.format_exc(limit=6)
    return row
  edges = {e.label for e in topology.edges.values() if getattr(e, "label", "")}
  points = {v.label for v in topology.points.values()
            if getattr(v, "label", "")}
  row["edges"], row["vertices"] = len(edges), len(points)
  row["tiles"] = len(filled.tiles)
  return row


def figure(name: str, readings, path: str) -> None:
  """Draw the typed tiling at each aspect.

  Args:
    name: the catalogue key.
    readings: one `read` result per aspect.
    path: where to write the PNG.
  """
  figure_, axes = plt.subplots(1, len(readings), figsize=(4 * len(readings), 4.6))
  for axis, row in zip(axes, readings):
    for kind, polygon, _owner in row["typed"]:
      for part in getattr(polygon, "geoms", [polygon]):
        if part.geom_type != "Polygon" or part.is_empty:
          continue
        axis.add_patch(MplPolygon(
          list(part.exterior.coords), closed=True,
          facecolor=DROPPED_FILL if kind == "dropped" else ASPECT_FILL,
          edgecolor="#c8a15a" if kind == "dropped" else "#9a9a9a",
          linewidth=0.7))
    for strand in row["strand_shapes"]:
      axis.add_patch(MplPolygon(list(strand.exterior.coords), closed=True,
                                facecolor=STRAND_FILL, edgecolor="#20304a",
                                linewidth=0.5))
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title(f"aspect {row['aspect']}\n"
                   f"{row['strands']} strands, {row['aspect_tiles']} aspect, "
                   f"{row['dropped_tiles']} dropped\n"
                   f"{row.get('edges', '-')} edge classes, "
                   f"{row.get('vertices', '-')} vertex classes", fontsize=9)
    axis.relim()
    axis.autoscale()
  figure_.suptitle(f"{name}: the daylight cut into tiles by what each piece "
                   f"is for", fontsize=10)
  figure_.tight_layout(rect=(0, 0, 1, 0.88))
  figure_.savefig(path, dpi=140)
  plt.close(figure_)


def main() -> None:
  """Build the typed tiling across aspects and see whether it holds still."""
  os.makedirs(IMAGES, exist_ok=True)
  for name in WEAVES:
    print(f"\n=== {name} ===")
    readings, shapes = [], []
    for aspect in ASPECTS:
      row = read(name, aspect)
      readings.append(row)
      shapes.append((row.get("edges"), row.get("vertices")))
      print(f"  aspect {row['aspect']:<5} {row['strands']:>3} strands  "
            f"{row['aspect_tiles']:>3} aspect  {row['dropped_tiles']:>2} dropped  "
            f"gap {row['gap']:.6f} overlap {row['overlap']:.6f}  "
            f"{row.get('edges', '-')} edge / {row.get('vertices', '-')} vertex "
            f"classes  {row['note']}")
      if row["trace"]:
        print("      " + row["trace"].replace("\n", "\n      ")[:600])
    if all(s[0] is not None for s in shapes):
      print(f"  across aspects: "
            f"{'INVARIANT' if len(set(shapes)) == 1 else 'MOVES'}")
    figure(name, readings, os.path.join(
      IMAGES, f"typed-{name.replace(' ', '-').replace('|', '_')}.png"))
  print(f"\nfigures written to {IMAGES}")


if __name__ == "__main__":
  main()
