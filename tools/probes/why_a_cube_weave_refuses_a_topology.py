"""Why the three cube weaves refuse a topology: one root, two faces.

They were the last undiagnosed weave failures. Driven with the exception
UNSWALLOWED -- because a refusal our own code composes is a SENTENCE
rather than a diagnosis, which this project has already paid for once --
all three fail inside the same library call:

    a--|b--|c--   AttributeError: 'MultiPolygon' has no 'exterior'
    a-b|c-d|e-f   GEOSException: unable to assign free hole to a shell
    abc|def|ghi   ... at -433.01270299999999 1000.000002

`tiling_utils.get_clean_polygon` ends `return gridify(geom.Polygon(
corners))` and `gridify` is `shapely.set_precision` at `RESOLUTION`.
That one call is BOTH failures: it raises on some input, and on other
input it splits a pinched polygon into a MultiPolygon which
`Topology._initialise_points_into_tiles` hands straight to
`get_corners`, which asks for `.exterior`.

THE DECISIVE READING IS THE CONTROL, not the failure. The same tile
cleans to a Polygon where it sits in the frame and to a MultiPolygon in
two of its seven translated copies -- so what decides it is the lattice
OFFSET moving a near-pinch onto the grid, and nothing about triaxiality
is special beyond its offsets being irrational multiples of the
resolution. Part B is that reading.

AND A REPAIR AIMED AT THE OBJECT YOU CAN SEE IS DEAD CODE. Exploding
multi-part tiles takes the frame's count to zero and the same exception
still fires, because the geometry that raises is made downstream in the
patch. Snapping the filler first is the half that moves something: it
takes `a-b|c-d|e-f` past the GEOSException entirely.

Run it with the reference venv, under the watchdog, since the largest
cube weave is 81 tiles and a topology build is the expensive end of this
catalogue:

    python3 tools/watchdog.py --stall 300 --timeout 10800 -- \
      ./.venv-reference/bin/python3 \
      tools/probes/why_a_cube_weave_refuses_a_topology.py

The record is docs/process/weaving-and-topology.md and the note offered
upstream is
docs/process/upstream-note-a-cleaned-polygon-may-be-multi-part.md.
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

# `tools/watchdog.py` sends SIGUSR1 before it kills, and a child that has
# not registered a faulthandler answers by dying rather than by naming
# the line it stopped on.
faulthandler.register(signal.SIGUSR1)

import geopandas as gpd  # noqa: E402
import shapely  # noqa: E402

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402
import weavingspace.tiling_utils as tu  # noqa: E402

SPACING = 1000.0
ASPECT = 0.75
CUBES = ("cube weave a--|b--|c--", "cube weave a-b|c-d|e-f",
         "cube weave abc|def|ghi")
# A biaxial control, so a failure about the SCAFFOLDING rather than about
# these designs shows itself as both arms failing.
CONTROL = "twill weave a|b"


def spec_for(name: str) -> dict:
  """The catalogue's own entry for a weave, looked up rather than typed.

  Args:
    name: the catalogue key.

  Returns:
    The spec dict `catalog.make_unit` takes.

  Raises:
    KeyError: where no entry of that name exists -- a family typed is
      not a family chosen.
  """
  for entries in catalog.TILINGS_BY_N.values():
    if name in entries:
      return entries[name]
  raise KeyError(name)


def filler_for(unit, snap: bool) -> list:
  """The daylight as single-part pieces, optionally pre-snapped.

  Args:
    unit: the thin weave.
    snap: whether to put each piece through the library's own `gridify`
      before handing it over, which is the half of the repair that moves
      something.

  Returns:
    A list of Polygons. Slivers under a square unit are dropped, and a
    piece that raises on being snapped is dropped rather than carried,
    since a filler piece the library cannot hold is not filler.
  """
  geometry = te.plane_coverage(unit)[2]
  if geometry is None:
    return []
  out = []
  for part in getattr(geometry, "geoms", [geometry]):
    for piece in getattr(part, "geoms", [part]):
      if piece.is_empty or piece.area <= 1:
        continue
      if not snap:
        out.append(piece)
        continue
      try:
        snapped = tu.gridify(piece)
      except Exception:                              # noqa: BLE001
        continue
      for one in getattr(snapped, "geoms", [snapped]):
        if not one.is_empty and one.is_valid and one.area > 1:
          out.append(one)
  return out


def scaffolded(name: str, snap: bool):
  """A weave with its daylight filled, ready for a topology.

  Args:
    name: the catalogue key.
    snap: passed to `filler_for`.

  Returns:
    The Tileable, or a string saying which step refused it -- the string
    is the finding on the arms that fail before a topology is attempted.
  """
  thin = catalog.make_unit(spec_for(name), spacing=SPACING, crs=None,
                           aspect=ASPECT)
  parts = filler_for(thin, snap)
  tiles = gpd.GeoDataFrame(
    {"tile_id": list(thin.tiles.tile_id) + [f"z{i}" for i in range(len(parts))]},
    geometry=list(thin.tiles.geometry) + parts, crs=thin.tiles.crs)
  filled = copy.deepcopy(thin)
  filled.tiles = tiles
  try:
    filled._setup_regularised_prototile()
  except Exception as exc:                           # noqa: BLE001
    return f"regularising raised {type(exc).__name__}: {str(exc)[:60]}"
  return filled


def part_a_what_each_weave_does() -> None:
  """Every arm, with the traceback rather than a composed sentence."""
  print("=== A. what each weave does, snapped and not ===")
  for name in (CONTROL, *CUBES):
    for snap in (False, True):
      unit = scaffolded(name, snap)
      label = f"{name}  gridify={snap}"
      if isinstance(unit, str):
        print(f"  {label:44} {unit}")
        continue
      multi = sum(1 for g in unit.tiles.geometry if g.geom_type != "Polygon")
      Topology = te._topology_class()
      try:
        topology = Topology(unit, True)
      except Exception as exc:                       # noqa: BLE001
        print(f"  {label:44} {type(exc).__name__}: {str(exc)[:44]} "
              f"[{multi} multi-part tiles]")
        continue
      labels = sorted({e.label for e in topology.edges.values() if e.label})
      print(f"  {label:44} BUILT, {len(labels)} edge classes, "
            f"{len(unit.tiles)} tiles")


def part_b_which_copies_split() -> None:
  """The control that names the cause: the same tile, in seven copies."""
  print(f"\n=== B. which copies the cleaner splits (RESOLUTION "
        f"{tu.RESOLUTION}) ===")
  unit = scaffolded(CUBES[0], snap=True)
  if isinstance(unit, str):
    print(f"  could not get that far: {unit}")
    return
  ids = list(unit.tiles.tile_id)
  patch = unit.get_local_patch(r=1, include_0=True).geometry
  print(f"  {len(unit.tiles)} tiles, patch of {len(patch)} "
        f"({len(patch) // len(unit.tiles)} copies)")
  split = 0
  for i, shape in enumerate(patch):
    cleaned = tu.get_clean_polygon(shape)
    if cleaned.geom_type == "Polygon":
      continue
    split += 1
    who = ids[i % len(unit.tiles)]
    corners = tu.get_corners(shape, repeat_first=False)
    rebuilt = shapely.Polygon([(p.x, p.y) for p in corners])
    base = unit.tiles.geometry.iloc[i % len(unit.tiles)]
    print(f"\n  shape {i:>3} is tile {who!r}, copy {i // len(unit.tiles)}")
    print(f"    before {shape.geom_type}, area {shape.area:.3f}, "
          f"{len(shape.exterior.coords)} corners, valid {shape.is_valid}")
    print(f"    after  {cleaned.geom_type}, {len(cleaned.geoms)} parts, "
          f"losing {shape.area - cleaned.area:.6f} of area")
    print(f"    rebuilt before the snap: {rebuilt.geom_type}, "
          f"valid {rebuilt.is_valid}")
    print(f"    THE SAME TILE IN THE FRAME cleans to "
          f"{tu.get_clean_polygon(base).geom_type}")
  print(f"\n  {split} of {len(patch)} patch shapes split; the tile is sound "
        f"where it sits, so the LATTICE OFFSET is what decides it")


def main() -> None:
  """Both parts, with the traceback kept for anything unexpected."""
  try:
    part_a_what_each_weave_does()
    part_b_which_copies_split()
  except Exception:                                  # noqa: BLE001
    print("the probe itself raised:")
    traceback.print_exc()


if __name__ == "__main__":
  main()
