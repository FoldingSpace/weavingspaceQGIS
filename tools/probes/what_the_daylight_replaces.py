"""Attribute a weave's daylight to the strands it stands in for.

Every earlier attribution here has been geometric: give a piece of
daylight to the strand it lies NEAREST. That is a heuristic, and it
answers the wrong question at a crossing, where the ground was opened
by two strands retreating and belongs to neither one more than the
other.

THE ATTRIBUTION THIS PROBE TESTS (the maintainer's, 2026-09-08) asks
what each piece of daylight REPLACES: which strand would have covered
that ground had the yarn been drawn at full width. It is computed the
way `daylight_by_kind` computes a conscious gap, by building a second
weave and comparing -- here the same weave at an aspect just under 1.0,
so nothing fuses and every full-width piece keeps its own identity.

TWO QUESTIONS IT IS MEANT TO SETTLE, both raised against the corner
reading of a crossing hole.

  Does absorbing by replacement keep the adjacency of two strands
  running ALONGSIDE each other? At full width they would abut along a
  line, so they are neighbours; but in a plain weave the ground between
  them is interrupted by the strands crossing it, and an attribution
  that carves every crossing hole among perpendicular pairs could lose
  the parallel pair entirely.

  And does it refuse the diagonal? Two strands at opposite corners of a
  hole meet, if at all, at a point. An adjacency asserted there is not
  a contact, and where the two strands cross elsewhere it is that
  crossing which should carry the relation.

The adjacency is reported with the strand letters, so a pair running in
one direction can be told from a pair that crosses.

Run it in the reference venv, under the watchdog:

    python3 tools/watchdog.py --stall 300 --timeout 3600 -- \
      ./.venv-reference/bin/python3 \
      tools/probes/what_the_daylight_replaces.py

NO TIMINGS ARE TAKEN; every figure is structural.
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

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402

SPACING = 1000.0
NEARLY_SOLID = 0.999
ASPECTS = (0.9, 0.75, 0.5, 0.25)
WEAVES = ("plain weave a|b", "twill weave a|b", "twill weave a|b-")
A_SEGMENT = 1.0


def spec_for(name):
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


def directions_of(code):
  """Which direction each element rides in, read from the strands code.

  Args:
    code: the strands code, e.g. ``ab-|cd``.

  Returns:
    A dict from element letter to the index of its direction, so two
    strands can be told to run alongside one another rather than
    across.
  """
  out = {}
  for index, run in enumerate(str(code).split("|")):
    for letter in run:
      if letter.isalpha():
        out[letter] = index
  return out


def replaced_by(thin, full):
  """Which full-width piece each piece of daylight stands in for.

  Args:
    thin: the weave at the strand width in force.
    full: the same weave built nearly solid, whose pieces are what the
      daylight replaces.

  Returns:
    A list, one entry per thin strand, of the daylight ground
    attributed to it. A piece of daylight goes to the full-width piece
    covering most of it, which is the whole of the attribution: no
    distance is measured and no tie is broken by order.
  """
  thin_tiles = list(thin.tiles.geometry)
  full_tiles = list(full.tiles.geometry)
  daylight = te.plane_coverage(thin)[2]
  claimed = [[] for _ in thin_tiles]
  for piece in parts_of(daylight):
    best, best_area = None, 0.0
    for index, candidate in enumerate(full_tiles):
      if index >= len(thin_tiles):
        break
      shared = piece.intersection(candidate).area
      if shared > best_area:
        best, best_area = index, shared
    if best is not None:
      claimed[best].append(piece)
  return claimed


def absorbed_regions(thin, claimed):
  """Each strand together with the ground it stands in for.

  Args:
    thin: the weave at the strand width in force.
    claimed: `replaced_by`'s attribution.

  Returns:
    One polygon per strand.
  """
  out = []
  for index, strand in enumerate(thin.tiles.geometry):
    out.append(shapely.union_all([strand] + claimed[index]))
  return out


def adjacency(regions, letters):
  """Which absorbed regions share an edge, named by strand letter.

  Args:
    regions: the absorbed regions, one per strand.
    letters: the tile id of each strand, in the same order.

  Returns:
    A sorted list of (letter, letter) pairs. A shared POINT is not an
    adjacency: two regions meeting at a corner are not in contact, and
    that is the whole of the answer to whether a hole may be crossed
    diagonally.
  """
  pairs = set()
  for i, one in enumerate(regions):
    for j in range(i + 1, len(regions)):
      shared = one.boundary.intersection(regions[j].boundary)
      if (not shared.is_empty) and shared.length > A_SEGMENT:
        pairs.add(tuple(sorted((letters[i], letters[j]))))
  return sorted(pairs)


def read(name, aspect):
  """Absorb by replacement and report what it joins.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.

  Returns:
    A dict of readings.
  """
  spec = spec_for(name)
  thin = catalog.make_unit(spec, spacing=SPACING, crs=None, aspect=aspect)
  full = catalog.make_unit(spec, spacing=SPACING, crs=None,
                           aspect=NEARLY_SOLID)
  letters = [str(x) for x in thin.tiles.tile_id]
  claimed = replaced_by(thin, full)
  regions = absorbed_regions(thin, claimed)
  merged = shapely.union_all(regions)
  overlap = sum(r.area for r in regions) - merged.area
  pairs = adjacency(regions, letters)
  direction = directions_of(spec.get("strands", ""))
  alongside = [p for p in pairs
               if direction.get(p[0]) is not None
               and direction.get(p[0]) == direction.get(p[1])]
  crossing = [p for p in pairs if p not in alongside]
  return {"aspect": aspect, "strands": len(regions),
          "unclaimed": len(parts_of(te.plane_coverage(thin)[2]))
                       - sum(len(c) for c in claimed),
          "overlap": overlap, "pairs": pairs,
          "alongside": alongside, "crossing": crossing,
          "full_tiles": len(full.tiles)}


def main():
  """Read the replacement attribution across aspects."""
  for name in WEAVES:
    print(f"\n=== {name} ===")
    print(f"  the full-width reference is the same weave at aspect "
          f"{NEARLY_SOLID}")
    seen = []
    for aspect in ASPECTS:
      row = read(name, aspect)
      seen.append((tuple(row["pairs"]),))
      print(f"  aspect {aspect:<5} {row['strands']:>3} strands, "
            f"{row['full_tiles']:>3} full-width pieces, "
            f"{row['unclaimed']:>2} daylight pieces unattributed, "
            f"overlap {row['overlap']:.1f}")
      print(f"      alongside: {row['alongside']}")
      print(f"      crossing : {row['crossing']}")
    print(f"  across aspects: "
          f"{'INVARIANT' if len(set(seen)) == 1 else 'MOVES'}")


if __name__ == "__main__":
  main()
