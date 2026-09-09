"""Does an edit aimed across a weave's gap actually move both sides?

The two readings of a weave's daylight give different structures, which
is measured. What that does not establish is whether either can be
EDITED, and in particular whether the reading that glues a strand-width
gap away lets an edit reach the strands on BOTH sides of it -- which is
the whole content of saying they are adjacent.

WHAT IT MEASURES, per weave and per reading:

  whether an edit aimed at a class the scaffolding introduced applies
    at all, rather than being refused or silently matching nothing
  whether the STRANDS move, as against the filler alone, since an edit
    that only rearranges scaffolding has changed nothing a person sees
  under the gluing, whether BOTH strands facing each other across a
  hole move, which is what the glued class asserts

THE CONTROL IS THE UNGLUED READING. The same edit aimed at the same
class without the gluing should move one side, so a run where both
readings move the same ground would be measuring the instrument rather
than the gluing.

Run it in the reference venv, under the watchdog:

    python3 tools/watchdog.py --stall 600 --timeout 3600 -- \
      ./.venv-reference/bin/python3 \
      tools/probes/does_an_edit_cross_a_weaves_gap.py
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
ASPECT = 0.75
WEAVES = ("plain weave a|b", "twill weave a|b", "twill weave a|b-")


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


def strand_ground(unit, kinds: dict):
  """The ground the CLOTH covers, with the scaffolding left out.

  Args:
    unit: a scaffolded unit, before or after an edit.
    kinds: the map `scaffolded_weave` returned.

  Returns:
    A shapely geometry, the union of the tiles that are strands.

  THE FILLER IS EXCLUDED DELIBERATELY. An edit that rearranged
  scaffolding and left the strands where they were has changed nothing
  anybody looks at, and comparing whole units would call that a
  success.
  """
  keep = [g for g, tile_id in zip(unit.tiles.geometry,
                                  unit.tiles["tile_id"].astype(str))
          if kinds.get(tile_id) == "strand" and g.geom_type == "Polygon"]
  return shapely.union_all(keep) if keep else shapely.Polygon()


def read(name: str, reading: str) -> dict:
  """Apply one edit under one reading and say what moved.

  Args:
    name: the catalogue key.
    reading: `ASPECT_LIKE_A_DROP` or `ASPECT_LIKE_AN_INSET`.

  Returns:
    A dict of readings, with `note` carrying any refusal.
  """
  spec = spec_for(name)
  topology, unit, kinds, glue, note = te.weave_topology(
    spec, SPACING, ASPECT, reading=reading)
  if topology is None:
    return {"note": note}
  labels = te.class_labels(topology, glue)
  wanted = labels.get("edge") or []
  if not wanted:
    return {"note": "no edge classes to aim at"}
  # THE FIRST CLASS IS AIMED AT rather than one chosen for the answer
  # it gives: picking the class that moves most would be choosing the
  # result. It is the class the tab's own chooser would open on.
  selector = wanted[0]
  edit = {"how": "zigzag_edge", "target": "edge", "classes": selector,
          "args": {"n": 2, "h": 0.15}}
  before = strand_ground(unit, kinds)
  edited, refusals, state = te.apply(topology, [edit], glue=glue)
  after = strand_ground(edited, kinds) if edited is not None else before
  difference = before.symmetric_difference(after)
  moved = difference.area
  cell = unit.prototile.geometry[0].area
  # HOW MANY STRANDS MOVED, not merely how much ground. Twice the area
  # is what one strand moved twice as far looks like as well as what
  # two strands moved once looks like, and the gluing's whole claim is
  # the second. Each patch of moved ground is attributed to the strand
  # tiles it lies against, before the edit.
  patches = [g for g in getattr(difference, "geoms", [difference])
             if g.geom_type == "Polygon" and g.area > cell / 1e6]
  # BY PIECE, NOT BY ELEMENT. `tile_id` on a strand is the element
  # LETTER, so a plain weave's four pieces answer as two ids and both
  # readings report the same pair whatever they did -- an instrument
  # aggregating over the very distinction under test (C-349). Each
  # piece is named by its own position instead.
  strands = [(g, f"{tile_id}@{g.centroid.x:.0f},{g.centroid.y:.0f}")
             for g, tile_id in
             zip(unit.tiles.geometry, unit.tiles["tile_id"].astype(str))
             if kinds.get(tile_id) == "strand" and g.geom_type == "Polygon"]
  touched = set()
  for patch in patches:
    for geometry, piece in strands:
      if geometry.distance(patch) < SPACING / 1000.0:
        touched.add(piece)
  widened = te._expanded(selector, glue, "edge")
  return {
    "note": "; ".join(refusals) if refusals else "",
    "classes": len(wanted),
    "selector": selector,
    "widened": widened,
    "widened_to": len(widened),
    "moved": moved / cell,
    "patches": len(patches),
    "strands_touched": len(touched),
    "which": sorted(touched),
    "strand_count": len(strands),
    "applied": bool(state.get("marks") and state["marks"][0].get("applied")),
  }


def main() -> None:
  """Report, per weave, what an edit does under each reading."""
  for name in WEAVES:
    print(f"\n=== {name} at aspect {ASPECT} ===")
    for reading in te.ASPECT_READINGS:
      row = read(name, reading)
      if row.get("note") and not row.get("classes"):
        print(f"  {reading:14s} refused: {row['note'][:60]}")
        continue
      print(f"  {reading:14s} {row['classes']:>3} edge class(es); aimed at "
            f"{row['selector']!r} widened to {row['widened_to']} label(s); "
            f"applied {row['applied']}; moved {row['moved']:.6f} of a "
            f"cell in {row['patches']} patch(es) against "
            f"{row['strands_touched']} of {row['strand_count']} "
            f"strand piece(s)"
            + (f"  [{row['note'][:40]}]" if row["note"] else ""))


if __name__ == "__main__":
  main()
