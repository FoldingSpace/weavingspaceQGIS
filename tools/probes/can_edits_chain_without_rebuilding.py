"""Can a second edit be aimed with the FIRST topology's labels?

The maintainer's question, 2026-08-31: "if the topology breaks, can't
we still apply some of the operations using the last topology labels
regardless even if we currently are dealing with an invalid topology?"

TODAY `apply` rebuilds a Topology between edits, so an edit that leaves
a design with gaps -- `rotate_edge` does, routinely -- makes every
later edit impossible: `build` returns None and the next edit is
refused for want of anything to aim at.

THE PROPOSAL is to chain on the object `transform_geometry` RETURNS
rather than on a rebuild. Upstream's caution is that such an object
"will probably not be correctly labelled", which is an objection about
labels matching a fresh build -- and if the labels are the ones we
started with and keep aiming with, that is not a cost.

THREE ARMS, and the third is the one that decides it:
  A  rebuild between edits (what ships)
  B  chain on the returned object, no rebuild
  C  an edit whose result has NO topology, followed by another --
     impossible under A by construction

WHAT IS COMPARED: the ground each arm ends on. If A and B agree where
both can run, chaining composes and the rebuild buys nothing; if they
differ, the rebuild is doing something and the difference is the price
of the proposal.
"""
import os, sys
ROOT = os.getcwd(); sys.path.insert(0, ROOT)
from weavingspace_qgis import deps; deps.add_paths()
from weavingspace_qgis import catalog, topology_edits

def ground(unit):
  """A unit described by what it covers.

  Args:
    unit: the Tileable to measure.

  Returns:
    (tile count, total area, total perimeter), rounded -- enough to
    tell two arms apart without being sensitive to how the library
    writes a ring down.
  """
  t = unit.tiles
  return (len(t), round(float(t.geometry.area.sum()), 3),
          round(float(t.geometry.length.sum()), 3))

def build(unit):
  """Build a topology, keeping the reason when there is none.

  Args:
    unit: the Tileable to build from.

  Returns:
    (topology or None, the reason it refused).
  """
  topo, why = topology_edits.build(unit)
  return topo, why

for family, n in (("laves 3.3.4.3.4", 4), ("hex-slice 3", 3)):
  spec = catalog.TILINGS_BY_N[n][family]
  unit = catalog.make_unit(spec, spacing=500.0, crs=3857)
  topo, why = build(unit)
  if topo is None:
    print(f"{family}: no topology ({why})"); continue
  edges = sorted({e.label for e in topo.edges.values() if e.label})
  points = sorted({v.label for v in topo.points.values() if v.label})
  print(f"\n=== {family}: edges {edges}, vertices {points}, "
        f"start {ground(topo.tileable)} ===")

  pairs = [
    ("nudge then nudge",
     [("nudge_vertex", points[0], {"dx": 0.5, "dy": 0.5}),
      ("nudge_vertex", points[-1], {"dx": -0.5, "dy": 0.5})]),
    ("rotate then nudge",
     [("rotate_edge", edges[0], {"angle": 15.0}),
      ("nudge_vertex", points[0], {"dx": 0.5, "dy": 0.5})]),
  ]
  for name, seq in pairs:
    # ---- ARM A: rebuild between
    cur, a_ok, a_note = topo, True, ""
    for how, sel, args in seq:
      if cur is None:
        a_ok, a_note = False, "no topology to aim the next edit with"
        break
      try:
        cur = cur.transform_geometry(True, True, sel, how, **args)
      except Exception as exc:
        a_ok, a_note = False, f"{type(exc).__name__}: {exc}"
        break
      cur, why = build(cur.tileable)
      if cur is None:
        a_note = f"rebuild failed: {why[:40]}"
    a_ground = ground(cur.tileable) if (a_ok and cur is not None) else None

    # ---- ARM B: chain on what transform_geometry returns
    cur, b_ok, b_note = topo, True, ""
    for how, sel, args in seq:
      try:
        cur = cur.transform_geometry(True, True, sel, how, **args)
      except Exception as exc:
        b_ok, b_note = False, f"{type(exc).__name__}: {exc}"
        break
    b_ground = ground(cur.tileable) if b_ok else None

    print(f"  {name}")
    print(f"    A rebuild-between : {a_ground}  {a_note}")
    print(f"    B chained         : {b_ground}  {b_note}")
    print(f"    agree: {a_ground == b_ground}")
