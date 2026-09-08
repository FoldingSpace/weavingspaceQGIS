"""Does the strand structure stay the size a tiling's does?

A tiling's topology is small: `laves 3.3.4.3.4` has two edge classes
and two vertex classes, and an edit is aimed at one of them. Any
account of a weave's structure has to be comparable, or the labels are
counting our method rather than the design. The typed tiling is not:
thirty edge classes for a plain weave of four strands, and 195 for a
twill, because every hole tile brings its own edges.

WHAT THIS MEASURES is the structure left when the incidental daylight
is absorbed into the strand it stands in for, rather than kept as
tiles. The attribution is by REPLACEMENT -- which strand would have
covered that ground at full width -- taken against the same weave built
just under aspect 1.0, so nothing fuses and no distance is measured.

The question is whether that structure is small, whether it holds still
as the strand width varies, and whether it is of the same order as a
tiling's. Tilings are built alongside as the yardstick.

Where the library refuses, the exception is printed rather than the
sentence our own code composes from it.

Run it in the reference venv, under the watchdog:

    python3 tools/watchdog.py --stall 300 --timeout 3600 -- \
      ./.venv-reference/bin/python3 \
      tools/probes/does_a_weave_topology_stay_small.py

NO TIMINGS ARE TAKEN; every figure is structural.
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

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402
import weavingspace.tiling_utils as tu  # noqa: E402

SPACING = 1000.0
NEARLY_SOLID = 0.999
ASPECTS = (0.9, 0.75, 0.5, 0.25)
WEAVES = ("plain weave a|b", "twill weave a|b", "basket weave ab|cd",
          "twill weave a|b-")
TILINGS = ("laves 3.3.4.3.4", "archimedean 4.8.8", "hex-slice 3")


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


def classes_of(topology):
  """How many distinct edge and vertex classes, counted as labels.

  Args:
    topology: a built Topology.

  Returns:
    (edges, vertices) as integers. Counted as LABELS, since past
    twenty-six classes the library issues two-letter ones and the
    length of a joined string stops being a count.
  """
  edges = {e.label for e in topology.edges.values() if getattr(e, "label", "")}
  points = {v.label for v in topology.points.values()
            if getattr(v, "label", "")}
  return len(edges), len(points)


def absorbed_by_replacement(name, aspect):
  """A weave whose incidental daylight has gone to the strands it replaces.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.

  Returns:
    (unit, unattributed) -- the design with each strand enlarged by the
    ground it stands in for, and how many pieces of daylight found no
    owner. The conscious gap a hyphen leaves is NOT absorbed: it stays
    uncovered, and is filled afterwards as a tile that stands for a
    hole, since the library cannot hold a design with a hole in it.
  """
  spec = spec_for(name)
  thin = catalog.make_unit(spec, spacing=SPACING, crs=None, aspect=aspect)
  full = catalog.make_unit(spec, spacing=SPACING, crs=None,
                           aspect=NEARLY_SOLID)
  kinds = te.daylight_by_kind(thin, spec, SPACING, aspect)
  incidental = parts_of(kinds["width"])
  conscious = parts_of(kinds["conscious"])
  strands = list(thin.tiles.geometry)
  full_tiles = list(full.tiles.geometry)
  claimed = [[] for _ in strands]
  unattributed = 0
  for piece in incidental:
    best, best_area = None, 0.0
    for index in range(min(len(strands), len(full_tiles))):
      shared = piece.intersection(full_tiles[index]).area
      if shared > best_area:
        best, best_area = index, shared
    if best is None:
      unattributed += 1
      continue
    claimed[best].append(piece)
  regions = [shapely.union_all([s] + claimed[i])
             for i, s in enumerate(strands)]
  holes = []
  for band in conscious:
    try:
      snapped = tu.gridify(band)
    except Exception:                                  # noqa: BLE001
      continue
    holes.extend(g for g in getattr(snapped, "geoms", [snapped])
                 if g.geom_type == "Polygon" and g.area > 1)
  unit = copy.deepcopy(thin)
  unit.tiles = gpd.GeoDataFrame(
    {"tile_id": [f"s{i}" for i in range(len(regions))]
                + [f"h{i}" for i in range(len(holes))]},
    geometry=regions + holes, crs=thin.tiles.crs)
  return unit, unattributed


def structure(name, aspect):
  """The class counts of the absorbed weave, or why there are none.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.

  Returns:
    A dict of readings, `note` carrying an unswallowed exception's name
    and `trace` its traceback.
  """
  row = {"aspect": aspect, "note": "", "trace": ""}
  unit, unattributed = absorbed_by_replacement(name, aspect)
  row["tiles"], row["unattributed"] = len(unit.tiles), unattributed
  gap, overlap, _left = te.plane_coverage(unit)
  row["gap"], row["overlap"] = gap, overlap
  try:
    unit._setup_regularised_prototile()
  except Exception as exc:                             # noqa: BLE001
    row["note"] = f"regularising raised {type(exc).__name__}"
    row["trace"] = traceback.format_exc(limit=5)
    return row
  try:
    topology = te._topology_class()(unit, True)
  except Exception as exc:                             # noqa: BLE001
    row["note"] = f"{type(exc).__name__}: {str(exc)[:48]}"
    row["trace"] = traceback.format_exc(limit=6)
    return row
  row["edges"], row["vertices"] = classes_of(topology)
  return row


def main():
  """Measure the absorbed weaves, with tilings beside them for scale."""
  print("=== tilings, as the yardstick ===")
  for name in TILINGS:
    unit = catalog.make_unit(spec_for(name), spacing=SPACING, crs=None)
    topology, why = te.build(unit)
    if topology is None:
      print(f"  {name:22} no topology: {why[:40]}")
      continue
    edges, vertices = classes_of(topology)
    print(f"  {name:22} {len(unit.tiles):>3} tiles  "
          f"{edges:>3} edge / {vertices:>3} vertex classes")

  for name in WEAVES:
    print(f"\n=== {name}, incidental daylight absorbed ===")
    shapes = []
    for aspect in ASPECTS:
      row = structure(name, aspect)
      shapes.append((row.get("edges"), row.get("vertices")))
      print(f"  aspect {row['aspect']:<5} {row['tiles']:>3} tiles  "
            f"gap {row['gap']:.6f} overlap {row['overlap']:.6f}  "
            f"{row['unattributed']:>2} unattributed  "
            f"{row.get('edges', '-')} edge / {row.get('vertices', '-')} "
            f"vertex classes  {row['note']}")
      if row["trace"]:
        print("      " + row["trace"].replace("\n", "\n      ")[:520])
    if all(s[0] is not None for s in shapes):
      print(f"  across aspects: "
            f"{'INVARIANT' if len(set(shapes)) == 1 else 'MOVES'}")


if __name__ == "__main__":
  main()
