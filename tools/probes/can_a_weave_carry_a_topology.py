"""Four routes to a topology for a weave, three of which fail.

The Topology tab refuses a weave: strands are narrower than their cells, so
the design has gaps and `Topology` needs a gap-free tiling. This asks whether
that is a fact about weaves or an artefact of how they are built, by driving
the four routes tried on 2026-09-08 and printing what each returns.

  1. build SOLID (aspect 1.0) and edit there
  2. build NEARLY solid, so the thin weave's combinatorics survive
  3. thin by INSETTING a solid weave
  4. SCAFFOLD the daylight, take the topology, drop the scaffolding

Only the fourth closes the round trip, and it closes it on all three once
the filler pieces are exploded and given DISTINCT ids -- see `_filler_ids`,
which is where an evening went. The reasoning, the dead ends and what is
owed are in docs/process/weaving-and-topology.md; the rulings are in
CLAUDE.md under C-347.

Run it with the reference venv, which drives the vendored library with no
QGIS in the way:

    ./.venv-reference/bin/python3 tools/probes/can_a_weave_carry_a_topology.py

NO TIMINGS ARE TAKEN. Every figure here is structural -- what builds, what
covers, what a piece measures -- so it is honest on a busy machine.

USE `plane_coverage` AND NEVER prototile-minus-tiles for a gap: a unit's
tiles need not lie inside the particular polygon its prototile is, and the
cheap subtraction reports a tenth of an untouched design missing
(docs/TOPOLOGY.md). This probe's own first version did that and was caught
by a twill whose SOLID gap read larger than its thin one.
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "weavingspace_qgis", "vendor"))

import geopandas as gpd  # noqa: E402
import shapely  # noqa: E402

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402

SPACING = 1000.0
FILLER_ID = "z"
# One plain, one twill, and one twill whose strands code carries a hyphen --
# the three shapes that behave differently, rather than a sample.
WEAVES = ("plain weave a|b", "twill weave a|b", "twill weave a|b-")


def spec_for(name: str) -> dict:
  """The catalogue's own entry for a weave, looked up rather than typed.

  Args:
    name: the catalogue key, e.g. ``twill weave a|b-``.

  Returns:
    The spec dict `catalog.make_unit` takes.

  Raises:
    KeyError: where no entry of that name exists, which is the honest
      answer -- a family typed is not a family chosen.
  """
  for entries in catalog.TILINGS_BY_N.values():
    if name in entries:
      return entries[name]
  raise KeyError(name)


def unit_at(name: str, aspect: float):
  """A weave built at a given strand width.

  Args:
    name: the catalogue key for the weave.
    aspect: strand width as a fraction of the spacing. At 1.0 the strands
      meet and the assembly takes its fusing path; below it they do not.

  Returns:
    The WeaveUnit, with no modifiers applied.
  """
  return catalog.make_unit(spec_for(name), spacing=SPACING, crs=None,
                           aspect=aspect)


def coverage(unit) -> tuple:
  """Gap and overlap of one fundamental cell, and the gap's geometry.

  Args:
    unit: the Tileable to measure.

  Returns:
    `plane_coverage`'s triple. The third member is the gap GEOMETRY, which
    is what the scaffolding route fills and what a prototile subtraction
    cannot honestly supply.
  """
  return te.plane_coverage(unit)


def route_one_and_two_solid_and_nearly() -> None:
  """Routes 1 and 2: does going solid, or nearly solid, give a topology?"""
  print("=== 1 and 2. solid, and nearly solid ===")
  print(f"  {'weave':20}{'aspect':>8}{'tiles':>7}{'gap of cell':>16}  topology")
  for name in WEAVES:
    for aspect in (1.0, 0.999, 0.99, 0.75):
      unit = unit_at(name, aspect)
      top, _why = te.build(unit)
      print(f"  {name:20}{aspect:>8}{len(unit.tiles):>7}"
            f"{coverage(unit)[0]:>16.8f}  {top is not None}")


def route_three_inset_cannot_thin() -> None:
  """Route 3: an inset shortens where thinning lengthens."""
  print("\n=== 3. can an inset stand in for thinning? ===")
  real, solid = unit_at(WEAVES[0], 0.75), unit_at(WEAVES[0], 1.0)
  # 1.0 -> 0.75 of the spacing takes 0.125 of it off each side of a strand.
  inset = solid.inset_tiles(0.125 * SPACING)
  for label, unit in (("real 0.75", real), ("solid", solid),
                      ("inset of solid", inset)):
    areas = sorted({round(g.area) for g in unit.tiles.geometry})
    print(f"  {label:16} piece areas {areas}")
  union_real = shapely.union_all(list(real.tiles.geometry))
  union_inset = shapely.union_all(list(inset.tiles.geometry))
  sym = union_real.symmetric_difference(union_inset).area
  print(f"  symmetric difference {sym:.0f}, "
        f"{sym / union_real.area:.1%} of the real weave")


def filler_pieces(gap) -> list:
  """The daylight, as single-part polygons.

  Args:
    gap: `plane_coverage`'s gap geometry, of any shapely type.

  Returns:
    A list of Polygons, multi-part members exploded and slivers dropped.

  EXPLODING IS NOT TIDINESS, IT IS THE FIX. A multi-part tile reaches
  `tiling_utils.get_corners`, which asks for `shape.exterior` and raises
  `AttributeError` on a MultiPolygon -- which `build` then reports as the
  library being unable to work out the structure. See `_filler_ids`.
  """
  out = []
  for part in getattr(gap, "geoms", [gap]):
    if part.is_empty or part.area <= 1:
      continue
    out.extend(getattr(part, "geoms", [part]))
  return [p for p in out if not p.is_empty and p.area > 1]


def _filler_ids(count: int) -> list:
  """One DISTINCT id per filler piece.

  Args:
    count: how many filler pieces there are.

  Returns:
    A list of distinct ids, none of which is a strand's.

  THE DISTINCTNESS IS LOAD-BEARING and cost an evening to find.
  `_setup_regularised_prototile()` dissolves the tiles by `tile_id`, so
  filler sharing one id merges into a MULTI-PART tile and `Topology`
  refuses -- not because the design has no structure, but because a tile
  it must take corners from has no single exterior ring. With one id per
  piece nothing merges. Sharing an id made two weaves of three fail and
  read as a fact about weaves.
  """
  return [f"{FILLER_ID}{i}" for i in range(count)]


def route_four_scaffold_the_daylight() -> None:
  """Route 4: fill the gaps, take the topology, drop the filler.

  THE FILLER SHOULD COME FROM THE STRANDS CODE, not from geometry: a
  position the code marks `-` is a deliberate absence and must stay open.
  This probe fills the measured gap wholesale, which is enough to answer
  whether a topology can be reached at all and is NOT the rule to build.
  """
  print("\n=== 4. scaffold the daylight, then drop it ===")
  for name in WEAVES:
    thin = unit_at(name, 0.75)
    gap = coverage(thin)[2]
    if gap is None:
      print(f"  {name:20} no gap geometry")
      continue
    parts = filler_pieces(gap)
    tiles = gpd.GeoDataFrame(
      {"tile_id": list(thin.tiles.tile_id) + _filler_ids(len(parts))},
      geometry=list(thin.tiles.geometry) + parts, crs=thin.tiles.crs)
    filled = copy.deepcopy(thin)
    filled.tiles = tiles
    # WeaveUnit's own signature: it takes no `override`, which is why
    # `topology_edits._shallow_copy_with_tiles` cannot copy one.
    filled._setup_regularised_prototile()
    gap_after, overlap_after, _g = coverage(filled)
    top, why = te.build(filled)
    print(f"  {name:20} {len(thin.tiles):>3} + {len(parts):>3} filler -> "
          f"{len(tiles):>3} tiles   gap {gap_after:.6f} overlap "
          f"{overlap_after:.6f}   topology {top is not None}")
    if top is None:
      print(f"  {'':20} refused: {why[:64]}")
      continue
    classes = te.classes(top)
    print(f"  {'':20} classes {classes}")
    edge = (classes.get("edge") or "")[:1]
    if not edge:
      continue
    edited, refused, _state = te.apply(
      top, [{"how": "zigzag_edge", "classes": edge,
             "args": {"n": 2, "h": 0.2, "smoothness": 3}}])
    if edited is None:
      print(f"  {'':20} edit refused: {refused}")
      continue
    kept = edited.tiles[~edited.tiles.tile_id.str.startswith(FILLER_ID)]
    print(f"  {'':20} edited; dropping the filler leaves {len(kept)} tiles, "
          f"all valid {all(g.is_valid for g in kept.geometry)}")


def main() -> None:
  """Drive the four routes in order."""
  route_one_and_two_solid_and_nearly()
  route_three_inset_cannot_thin()
  route_four_scaffold_the_daylight()


if __name__ == "__main__":
  main()
