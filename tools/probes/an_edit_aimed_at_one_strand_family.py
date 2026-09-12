"""Does an edit aimed at a refined class move only one strand family?

Splitting warp from weft is measured as a refinement of the CLASSES
(`warp_and_weft_kept_apart.py`). That is not the claim anybody cares
about. The claim is that an edit aimed at one of the refined classes
moves the warps and leaves the wefts, and a class count cannot say
whether it does: the labels could split perfectly while the edit went
on reaching both directions, which is exactly what happens if the
selector is widened, or if the refinement renames classes without the
library's own `label in selector` seeing the new names.

So this is the sibling of `does_an_edit_cross_a_weaves_gap.py`, asking
the same kind of question of the other switch. That one measured
whether a glued class reaches BOTH sides of a hole; this measures
whether a refined class reaches only ONE direction of strand.

WHAT IT MEASURES, per weave and per reading of the aspect gaps:

  which strand PIECES move under an edit aimed at the first edge class
  how many distinct DIRECTIONS those moved pieces run in

THE CONTROL IS THE UNREFINED SETTING, and it has to bite. With warp and
weft together the same edit must move pieces of both directions, or the
design cannot show the refinement doing anything and a one-direction
answer under `apart` would be measuring the weave rather than the
switch. A run where both settings answer the same is a failed
measurement, not a finding.

BY PIECE, NOT BY ELEMENT, and by each piece's own direction rather than
by the class it was aimed at. A strand's `tile_id` is the element
LETTER, so a plain weave's four pieces answer as two ids whatever they
did -- an instrument aggregating over the very distinction under test
(C-349). Each piece is named by its position and classified by the long
axis of its own rectangle.

AND EACH PIECE IS COMPARED WITH ITS OWN EDITED SELF, which is the
second version of this probe. The first took the symmetric difference
of ALL the cloth and attributed each patch of it to the pieces within a
map unit -- the rule its sibling uses, which is right for asking
whether both sides of a hole moved and wrong here: a patch at a corner
lies within a map unit of a warp AND of a weft, so every reading came
back "two directions" whatever the edit did. It said so while the moved
AREA was halving exactly, 0.0023 of a cell to 0.0012 on the twill,
which is the refinement plainly working and the instrument plainly not
seeing it. Comparing piece against piece needs no tolerance about what
lies near what. The tile order is asserted rather than assumed.

Run it in the reference venv, unbuffered, under the watchdog:

    PYTHONUNBUFFERED=1 python3 tools/watchdog.py --stall 900 \
      --timeout 5400 -- ./.venv-reference/bin/python3 \
      tools/probes/an_edit_aimed_at_one_strand_family.py
"""
import faulthandler
import os
import signal
import sys
import time
import warnings

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "weavingspace_qgis", "vendor"))

warnings.filterwarnings("ignore", category=RuntimeWarning)
faulthandler.register(signal.SIGUSR1)

import shapely  # noqa: E402

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402

SPACING = 1000.0
ASPECT = 0.75
WEAVES = ("plain weave a|b", "twill weave a|b")


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


def strand_pieces(unit, kinds: dict) -> list:
  """Every drawn piece of cloth, named by where it sits.

  Args:
    unit: a scaffolded unit.
    kinds: the map `scaffolded_weave` returned.

  Returns:
    A list of `(geometry, name, direction)`, the direction being the
    angle of the piece's own long axis.
  """
  out = []
  for geometry, tile_id in zip(unit.tiles.geometry,
                               unit.tiles["tile_id"].astype(str)):
    if kinds.get(tile_id) != "strand" or geometry.geom_type != "Polygon":
      continue
    axis = te._long_axis(geometry)
    if axis is None:
      continue
    out.append((geometry,
                f"{tile_id}@{geometry.centroid.x:.0f},{geometry.centroid.y:.0f}",
                te._as_direction(axis[0], axis[1])))
  return out


def read(name: str, reading: str, families: str) -> dict:
  """Aim one edit at the first edge class and say what moved.

  Args:
    name: the catalogue key.
    reading: which reading of the aspect gaps to build under.
    families: whether one class may hold both strand directions.

  Returns:
    A dict of readings, with `note` carrying any refusal.
  """
  started = time.monotonic()
  topology, unit, kinds, glue, note = te.weave_topology(
    spec_for(name), SPACING, ASPECT, reading=reading, families=families)
  if topology is None:
    return {"note": note}
  wanted = te.class_labels(topology, glue).get("edge") or []
  if not wanted:
    return {"note": "no edge classes to aim at"}
  # THE FIRST CLASS IS AIMED AT rather than one chosen for the answer it
  # gives, as its sibling probe does: it is the class the tab's own
  # chooser opens on, and picking the one that answers best would be
  # choosing the result.
  selector = wanted[0]
  edit = {"how": "zigzag_edge", "target": "edge", "classes": selector,
          "args": {"n": 2, "h": 0.15}}
  pieces = strand_pieces(unit, kinds)
  cell = unit.prototile.geometry[0].area
  edited, refusals, _state = te.apply(topology, [edit], glue=glue)
  if edited is None:
    return {"note": "; ".join(refusals) or "the edit produced nothing"}
  # THE ROWS MUST LINE UP OR THE COMPARISON IS BETWEEN TWO DESIGNS.
  # `apply` edits the tiles in place and adds none, so piece i before
  # is piece i after -- asserted here rather than believed, since a
  # repair that reordered them would give every piece a plausible and
  # meaningless displacement.
  was = list(zip(unit.tiles.geometry, unit.tiles["tile_id"].astype(str)))
  now = list(zip(edited.tiles.geometry, edited.tiles["tile_id"].astype(str)))
  if len(was) != len(now) or [i for _g, i in was] != [i for _g, i in now]:
    return {"note": "the edit changed the tile order, so no piece can be "
                    "compared with itself"}
  moved, directions, ground = [], [], 0.0
  for (old, tile_id), (new, _same) in zip(was, now):
    if kinds.get(tile_id) != "strand" or old.geom_type != "Polygon":
      continue
    shifted = old.symmetric_difference(new).area
    if shifted <= cell / 1e6:
      continue
    ground += shifted
    axis = te._long_axis(old)
    angle = te._as_direction(axis[0], axis[1]) if axis else 0.0
    moved.append(f"{tile_id}@{old.centroid.x:.0f},{old.centroid.y:.0f}")
    if not any(te._same_direction(angle, other) for other in directions):
      directions.append(angle)
  return {"note": "; ".join(refusals) if refusals else "",
          "classes": len(wanted), "aimed": selector,
          "pieces": len(pieces), "moved": len(moved),
          "directions": sorted(round(a, 1) for a in directions),
          "ground": ground / cell,
          "seconds": time.monotonic() - started}


def main() -> None:
  """Report what one edit reaches under each setting of each switch."""
  for name in WEAVES:
    print(f"\n=== {name} at aspect {ASPECT} ===")
    for reading in te.ASPECT_READINGS:
      for families in te.STRAND_FAMILIES:
        answer = read(name, reading, families)
        if answer["note"]:
          print(f"  {reading:14s} {families:9s} -- {answer['note'][:60]}")
          continue
        print(f"  {reading:14s} {families:9s} aimed at {answer['aimed']:>3} "
              f"of {answer['classes']:>3} classes: moved "
              f"{answer['moved']:>3} of {answer['pieces']:>3} pieces, "
              f"running in {len(answer['directions'])} direction(s) "
              f"{answer['directions']}, {answer['ground']:.4f} of a cell "
              f"({answer['seconds']:.0f}s)")


if __name__ == "__main__":
  main()
