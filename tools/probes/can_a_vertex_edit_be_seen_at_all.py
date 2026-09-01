"""Can either vertex manipulation move a design VISIBLY at its own maximum?

The offset probe found `nudge_vertex` moving 0.071 map units on a unit
spanning 707 at its own step, and 0.283 at four steps -- a hundredth of
a percent. That is below anything a screen can show, so a person
dragging a NODE would see nothing whatever the drawing did, which is
what the maintainer was doing when they reported the tab unusable.

THE CONTROL'S WHOLE DOMAIN IS THEREFORE THE QUESTION, not the step.
`dx` and `dy` run -1.0 to 1.0; this asks what the EXTREME of that range
does. This project's own rule: a control must be able to represent its
domain, and the way to find out is to type the largest thing it accepts
and read what the map is built from.
"""
import os, sys
ROOT = os.getcwd()
sys.path.insert(0, ROOT)
from weavingspace_qgis import deps
deps.add_paths()
from weavingspace_qgis import catalog, topology_edits

for family, n in [("laves 3.3.4.3.4", 4), ("archimedean 4.8.8", 2)]:
  spec = catalog.TILINGS_BY_N[n][family]
  unit = catalog.make_unit(spec, spacing=500.0, crs=3857)
  x0, y0, x1, y1 = unit.tiles.total_bounds
  span = max(x1 - x0, y1 - y0)
  built, why = topology_edits.build(unit)
  topology = built  # build() returns the Topology itself, not a dict
  points = sorted({v.label for v in topology.points.values()
                   if getattr(v, "label", None)})
  print(f"\n=== {family} n={n}, unit span {span:.1f} map units ===")
  for how, args in (("nudge_vertex", {"dx": 1.0, "dy": 1.0}),
                    ("nudge_vertex", {"dx": 0.5, "dy": 0.0}),
                    ("push_vertex", {"push_d": 1.0})):
    for label in points:
      edited, refusals = topology_edits.apply(
        topology, [{"classes": label, "how": how, "args": args}])
      if edited is None:
        print(f"  {how} {args} on {label}: no unit ({refusals})")
        continue
      a = unit.tiles.reset_index(drop=True)
      b = edited.tiles.reset_index(drop=True)
      moved = max(float(ga.hausdorff_distance(gb))
                  for ga, gb in zip(a.geometry, b.geometry))
      note = f"  REFUSED" if refusals else ""
      print(f"  {how:<13} {str(args):<26} class {label}: "
            f"{moved:8.3f} = {moved / span * 100:6.3f}% of the unit{note}")
