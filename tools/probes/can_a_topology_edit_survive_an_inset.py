"""Can a topology edit be made before an inset and the inset applied after?

`Topology` needs a gap-free tiling, so a tile or group inset takes the
Topology tab away outright. This asks the question that decides whether that
is a fact about the design or an artefact of the ORDER the modifier chain
runs in: `_build_unit` applies the insets LAST, after rotate, scale and skew,
and every step before them preserves the tiling, so the un-inset design is
one call back rather than gone.

Three arms, each answering one thing:

  1. does an inset really refuse a topology            (today's behaviour)
  2. does editing the plain unit and insetting after work, on designs and
     manipulations chosen for their failure modes      (is it buildable)
  3. is a tear still distinguishable once an inset has opened gaps of its
     own                                               (what the mark means)

The third is the one with a number on it, and it is why the validity
judgement runs on the skeleton: an inset's gaps swamp a tear as a FRACTION
while the tear's own contribution is conserved, so judging the inset design
against a threshold reads every inset design as catastrophically torn.

Run it with the checkout on the path and the reference venv, which drives
`topology_edits` and the vendored library with no QGIS in the way:

    ./.venv-reference/bin/python3 tools/probes/can_a_topology_edit_survive_an_inset.py

NO TIMINGS ARE TAKEN HERE, deliberately. The figures this probe produces are
structural -- what builds, what covers, what refuses -- so they are honest on
a busy machine, where a timing taken beside a running suite is not.

The account is C-346; the table it produced is in docs/TOPOLOGY.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "weavingspace_qgis", "vendor"))

from weavingspace_qgis import catalog, topology_edits  # noqa: E402

SPACING = 1000.0

# Chosen for their lattices rather than for being representative: laves and
# archimedean are orthogonal, hex-slice is not, and a block laid on a
# non-orthogonal lattice is where the tear-finder went wrong before (row 2 of
# round nine).
DESIGNS = (("laves 3.3.4.3.4", 4), ("archimedean 4.8.8", 2), ("hex-slice 3", 3))


def unit_for(family: str, n: int):
  """The catalogue's own unit for a design, looked up rather than typed.

  Args:
    family: the catalogue's key, e.g. ``laves 3.3.4.3.4``.
    n: the element count the entry lives under in TILINGS_BY_N.

  Returns:
    A Tileable with no modifiers applied, exactly as `_build_unit` starts.

  A FAMILY TYPED IS NOT A FAMILY CHOSEN: composing the spec by hand gives
  `KeyError: 'tiling_type'`, and typing a family at a count it does not exist
  at silently measures a different design. This probe's own first run did the
  first of those on all three designs.
  """
  return catalog.make_unit(catalog.TILINGS_BY_N[n][family],
                           spacing=SPACING, crs=None)


def gap_of_one_cell(unit) -> float:
  """How much of one fundamental cell the unit's tiles leave uncovered.

  Args:
    unit: the Tileable to measure.

  Returns:
    The gap term of `plane_coverage`, a fraction of one cell.

  `plane_coverage` rather than `gaps()`, which finds only holes ENCLOSED
  within a patch and so cannot see units that have pulled apart -- and an
  inset's channels reach the patch's edge, so `gaps()` reads 0.0 on a design
  that leaves a third of its cell bare (C-341).
  """
  return topology_edits.plane_coverage(unit)[0]


def does_an_inset_refuse_a_topology() -> None:
  """Arm one: confirm that an inset really does take the tab away."""
  print("=== 1. an inset refuses a topology (today's behaviour) ===")
  for family, n in DESIGNS:
    unit = unit_for(family, n)
    plain, _why = topology_edits.build(unit)
    line = f"  {family:20} plain {plain is not None}"
    for pct in (1.0, 5.0):
      inset, _w = topology_edits.build(unit.inset_tiles(pct * SPACING / 100))
      line += f"   inset {pct:g}% {inset is not None}"
    print(line)


def does_an_edit_survive_being_inset() -> None:
  """Arm two: edit the plain unit, then inset the result."""
  print("\n=== 2. edit the plain unit, then inset it ===")
  for family, n in DESIGNS:
    unit = unit_for(family, n)
    top, _why = topology_edits.build(unit)
    if top is None:
      print(f"  {family}: no topology even plain, skipped")
      continue
    edges = topology_edits.classes(top).get("edge") or ""
    vertices = topology_edits.classes(top).get("vertex") or ""
    for how, args, sel in (
        ("zigzag_edge", {"n": 2, "h": 0.3, "smoothness": 3}, edges[:1]),
        ("rotate_edge", {"angle": 15}, edges[:1]),
        ("nudge_vertex", {"dx": 0.1, "dy": 0.1}, vertices[:1])):
      if not sel:
        continue
      edited, _refused, _state = topology_edits.apply(
        top, [{"how": how, "classes": sel, "args": args}])
      if edited is None:
        print(f"  {family:20} {how:13} refused")
        continue
      marks = []
      for shrink, pct in (("tiles", 1.0), ("tiles", 5.0), ("prototile", 5.0)):
        after = (edited.inset_tiles(pct * SPACING / 100) if shrink == "tiles"
                 else edited.inset_prototile(pct * SPACING / 100))
        ok = (all(g.is_valid for g in after.tiles.geometry)
              and not any(g.is_empty for g in after.tiles.geometry))
        marks.append(f"{shrink[:4]} {pct:g}% {'ok' if ok else 'BROKEN'}")
      print(f"  {family:20} {how:13} " + "  ".join(marks))


def is_a_tear_visible_under_an_inset() -> None:
  """Arm three: the number the validity ruling turns on.

  Driven on class `b` deliberately. The first version of this drove class `a`,
  where an odd zigzag count is sound at every count docs/TOPOLOGY.md lists, so
  it produced a negative that could not have been positive.
  """
  print("\n=== 3. is a tear visible once an inset has opened gaps? ===")
  unit = unit_for("laves 3.3.4.3.4", 4)
  top, _why = topology_edits.build(unit)
  klass = topology_edits.classes(top)["edge"][1]
  print(f"  class {klass!r}, which the audit's table says tears on an odd count")
  print(f"  {'state':34}{'gap of one cell':>18}")
  for n in (2, 3):
    edited, _r, _s = topology_edits.apply(
      top, [{"how": "zigzag_edge", "classes": klass,
             "args": {"n": n, "h": 0.3, "smoothness": 3}}])
    if edited is None:
      print(f"  zigzag n={n}: refused")
      continue
    sound = "sound" if n % 2 == 0 else "TORN"
    print(f"  zigzag n={n} skeleton ({sound}){'':>10}{gap_of_one_cell(edited):18.6f}")
    for pct in (1.0, 5.0):
      inset = edited.inset_tiles(pct * SPACING / 100)
      print(f"     + inset {pct:g}%{'':22}{gap_of_one_cell(inset):18.6f}")


def main() -> None:
  """Run the three arms in order, each printing its own table."""
  does_an_inset_refuse_a_topology()
  does_an_edit_survive_being_inset()
  is_a_tear_visible_under_an_inset()


if __name__ == "__main__":
  main()
