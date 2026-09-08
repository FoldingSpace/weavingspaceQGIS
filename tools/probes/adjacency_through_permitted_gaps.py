"""Adjacency that passes through some kinds of gap and not others.

The typed tiling of a weave (`holes_made_of_typed_tiles.py`) cuts the
daylight canonically -- by what each piece is FOR -- and its class
structure holds still as the strand width varies, which the arbitrary
cut's did not. But it carries a great deal of structure that is about
the daylight rather than about the fabric: thirty edge classes for a
plain weave, where the weave has four strands.

THIS IS THE STEP AFTER (the maintainer's framing, 2026-09-08). Take the
typed tiling as the substrate and define adjacency as reachability
THROUGH tiles of permitted kinds. An aspect tile is transparent,
because the daylight a strand's own width opens is not a real
separation; the band a dropped strand left is opaque, because that
absence is the one gap a weave really has. The permitted set is a
parameter rather than a rule baked into the code, so what a different
choice would give can be measured rather than argued about.

AND THE ADJACENCIES ARE GROUPED BY SYMMETRY rather than counted. The
library computes a transitivity class for every edge of the typed
tiling, so an adjacency realised by passing through a gap tile can be
named by the classes of the edges it crosses. Two adjacencies with the
same crossing signature are the same KIND of adjacency, which is a
stronger invariant than a count or a degree sequence and is derived
from the design's own symmetries rather than from anything chosen here.

WHAT IT MEASURES, per weave and per aspect: how many strand-to-strand
adjacencies there are, how many distinct kinds of adjacency, and
whether either moves as the strand width varies. It reports the same
with the dropped band made transparent, which is the comparison that
says whether the distinction between the two kinds of gap does any
work at this level.

Run it in the reference venv, under the watchdog:

    python3 tools/watchdog.py --stall 400 --timeout 5400 -- \
      ./.venv-reference/bin/python3 \
      tools/probes/adjacency_through_permitted_gaps.py

NO TIMINGS ARE TAKEN; every figure is structural.
"""
import faulthandler
import os
import signal
import sys
import warnings
from collections import deque

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "weavingspace_qgis", "vendor"))
sys.path.insert(0, os.path.join(HERE, "tools", "probes"))

warnings.filterwarnings("ignore", category=RuntimeWarning)
faulthandler.register(signal.SIGUSR1)

import holes_made_of_typed_tiles as typed  # noqa: E402

ASPECTS = (0.9, 0.75, 0.5, 0.25)
WEAVES = ("plain weave a|b", "twill weave a|b", "twill weave a|b-",
          "plain weave ab-|cd-")


def kind_of(label: str) -> str:
  """What a tile is, read from the id the typed tiling gave it.

  Args:
    label: the tile's own id.

  Returns:
    "strand", "aspect" or "dropped".
  """
  if label.startswith("s"):
    return "strand"
  return "dropped" if label.startswith("d") else "aspect"


def tile_graph(topology) -> tuple:
  """The tiles of a topology, what kind each is, and what meets what.

  Args:
    topology: a built Topology of a typed tiling.

  Returns:
    (kinds, neighbours, orbit): what each tile is, what meets what
    with the edge class between them, and which ORBIT of the
    lattice each tile belongs to. The orbit is what makes an
    answer about the unit rather than about the patch: the patch
    holds many copies of every strand, and counting pairs of
    copies gave 106 pairs for a weave with four strands.

  IT IS READ OFF THE LIBRARY'S OWN INCIDENCE. Every Edge carries the
  tiles either side of it, so the tile graph is exactly what the
  topology already knows, rather than a second computation from
  geometry that could disagree with it.
  """
  kinds, orbit = {}, {}
  for tile in topology.tiles:
    kinds[tile.ID] = kind_of(str(getattr(tile, "label", "") or ""))
    orbit[tile.ID] = getattr(tile, "base_ID", tile.ID)
  neighbours = {tile.ID: [] for tile in topology.tiles}
  for edge in topology.edges.values():
    left, right = getattr(edge, "left_tile", None), getattr(edge, "right_tile", None)
    if left is None or right is None or left == right:
      continue
    if left not in neighbours or right not in neighbours:
      continue
    label = getattr(edge, "label", "") or "?"
    neighbours[left].append((right, label))
    neighbours[right].append((left, label))
  return kinds, neighbours, orbit


def adjacencies(kinds, neighbours, orbit, transparent) -> dict:
  """Strand-to-strand adjacency, passing only through permitted kinds.

  Args:
    kinds: a tile index to its kind.
    neighbours: the tile graph.
    orbit: a tile index to the lattice orbit it belongs to, so the
      answer is about the unit's strands rather than the patch's copies
      of them.
    transparent: the set of kinds a path may pass through.

  Returns:
    A dict from a sorted pair of strand tile ids to the set of crossing
    signatures that realise it -- each signature the sorted tuple of
    edge classes the path used. The signature is what groups
    adjacencies by symmetry: two paths crossing the same classes are
    the same kind of adjacency.

  A path may pass through any number of transparent tiles, so a wide
  band of daylight joins the strands either side of it however many
  tiles it was cut into. That is what makes the answer independent of
  the cutting rather than merely canonical in it.
  """
  found = {}
  strands = [i for i, kind in kinds.items() if kind == "strand"]
  started = set()
  for start in strands:
    if orbit[start] in started:
      continue
    started.add(orbit[start])
    # Walk out of this strand, through transparent tiles only, and
    # record every strand reached with the classes crossed on the way.
    queue = deque()
    for other, label in neighbours[start]:
      queue.append((other, (label,)))
    seen = set()
    while queue:
      here, crossed = queue.popleft()
      if (here, crossed) in seen:
        continue
      seen.add((here, crossed))
      if kinds.get(here) == "strand":
        if orbit[here] == orbit[start]:
          continue
        pair = (min(orbit[start], orbit[here]), max(orbit[start], orbit[here]))
        found.setdefault(pair, set()).add(tuple(sorted(crossed)))
        continue
      if kinds.get(here) not in transparent:
        continue
      if len(crossed) >= 4:
        continue
      for other, label in neighbours[here]:
        queue.append((other, crossed + (label,)))
  return found


def read(name: str, aspect: float) -> dict:
  """Build the typed tiling and read its permitted-gap adjacency.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.

  Returns:
    A dict of readings, with `note` where a step refused.
  """
  row = typed.read(name, aspect)
  out = {"name": name, "aspect": aspect, "note": row["note"],
         "strands": row["strands"], "aspect_tiles": row["aspect_tiles"],
         "dropped_tiles": row["dropped_tiles"]}
  if row["note"]:
    return out
  # Rebuild the topology here: `typed.read` does not hand it back.
  from weavingspace_qgis import topology_edits as te
  import copy
  import geopandas as gpd
  from weavingspace_qgis import catalog
  unit = catalog.make_unit(typed.spec_for(name), spacing=typed.SPACING,
                           crs=None, aspect=aspect)
  strands = row["strand_shapes"]
  snapped = row["snapped"]
  filled = copy.deepcopy(unit)
  filled.tiles = gpd.GeoDataFrame(
    {"tile_id": [f"s{i}" for i in range(len(strands))]
                + [f"{'d' if k == 'dropped' else 'w'}{i}"
                   for i, (k, _g, _o) in enumerate(snapped)]},
    geometry=list(strands) + [g for _k, g, _o in snapped],
    crs=unit.tiles.crs)
  filled._setup_regularised_prototile()
  topology = te._topology_class()(filled, True)
  kinds, neighbours, orbit = tile_graph(topology)
  for permitted, key in ((("aspect",), "respecting"),
                         (("aspect", "dropped"), "ignoring")):
    found = adjacencies(kinds, neighbours, orbit, set(permitted))
    signatures = {sig for sigs in found.values() for sig in sigs}
    out[f"{key}_pairs"] = len(found)
    out[f"{key}_kinds"] = len(signatures)
  return out


def main() -> None:
  """Read the permitted-gap adjacency across aspects, and compare rules."""
  for name in WEAVES:
    print(f"\n=== {name} ===")
    shapes = []
    for aspect in ASPECTS:
      row = read(name, aspect)
      if row["note"]:
        print(f"  aspect {aspect:<5} {row['note']}")
        shapes.append(None)
        continue
      shapes.append((row["respecting_pairs"], row["respecting_kinds"]))
      print(f"  aspect {aspect:<5} {row['strands']:>3} strands, "
            f"{row['aspect_tiles']:>3} aspect, {row['dropped_tiles']:>2} dropped   "
            f"through aspect only: {row['respecting_pairs']:>3} pairs in "
            f"{row['respecting_kinds']:>3} kinds   "
            f"through both: {row['ignoring_pairs']:>3} pairs in "
            f"{row['ignoring_kinds']:>3} kinds")
    if all(s is not None for s in shapes):
      print(f"  across aspects: "
            f"{'INVARIANT' if len(set(shapes)) == 1 else 'MOVES'}")


if __name__ == "__main__":
  main()
