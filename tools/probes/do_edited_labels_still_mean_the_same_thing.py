"""Can the Topology tab draw the EDITED motif and keep its labels?

The maintainer's report of 2026-08-31: clicking and dragging on the
drawing changes the map and the preview, the drawing itself flickers
during the drag and then goes back, and the settled picture never
reflects the edit -- "and thus it's impossible to use".

The mechanism is not in doubt: the landing hands the panel
`built["unit"]` and `built["topology"]`, which are the motif BEFORE the
edits are replayed. What has kept this a ruling rather than a repair is
the LABELS. Edits are replayed by class label against a topology built
from the un-edited unit, and upstream cautions that a TRANSFORMED
topology "will probably not be correctly labelled" -- so drawing the
edited ground was thought to cost either a highlight that sits away
from the ink or labels that mean something else on replay.

THAT CAUTION MAY NOT APPLY HERE, and this measures whether it does.
`built["edited_topology"]` is not a transformed object: it is
`topology_edits.build(edited)`, a topology REBUILT from the edited
unit, which is exactly what upstream's caution tells a caller to do.
It is already computed, on the worker, and the saved dual is already
taken from it.

WHAT WOULD MAKE THE REPAIR SAFE, and each is asserted separately
rather than as one verdict:

  1. the edited rebuild carries the SAME SET of edge and vertex class
     labels as the un-edited one -- so a person aiming at "a" in the
     edited drawing is aiming at something the next replay can find;
  2. the labels correspond ELEMENT BY ELEMENT, so the highlight lands
     on the same edge a person clicked rather than on a different one
     wearing that name;
  3. and the edited ground really is different, or the whole
     comparison is between a thing and itself -- the premise this
     project has been caught by more than once.

A DISAGREEMENT IS AN ANSWER TOO: if the labels move, the repair costs
a decision about what the picture is for, and that is the maintainer's
rather than mine.

    cd <checkout> && PYTHONUNBUFFERED=1 QT_QPA_PLATFORM=offscreen \\
      "$QGIS_PY" do_edited_labels_still_mean_the_same_thing.py
"""

import os
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
# The vendored library, by hand: `deps.add_paths()` does this
# inside QGIS, and a probe that leaves it out dies at
# `from weavingspace import TileUnit` inside make_unit.
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))

from weavingspace_qgis import catalog, topology_edits      # noqa: E402


def classes(topology):
  """The edge and vertex class labels a topology offers.

  Args:
    topology: a built Topology.

  Returns:
    (edge labels sorted, vertex labels sorted) -- the same two
    questions `topology_edits` asks when it fills the tab's chooser,
    asked the same way so this measures what the tab would show.
  """
  edges = sorted({e.label for e in topology.edges.values()
                  if getattr(e, "label", None)})
  points = sorted({v.label for v in topology.points.values()
                   if getattr(v, "label", None)})
  return edges, points


def by_element(topology):
  """Each element's label, keyed by its own identity in the topology.

  Returns:
    Two dicts, edges and points, keyed by the topology's own keys, so
    two topologies can be compared element by element rather than as
    sets. Sets alone would call a relabelling "the same" whenever it
    is a permutation, which is precisely the case that would land a
    highlight on the wrong edge.
  """
  edges = {k: getattr(e, "label", None) for k, e in topology.edges.items()}
  points = {k: getattr(v, "label", None) for k, v in topology.points.items()}
  return edges, points


def ground(unit):
  """Area and perimeter of a unit's tiles -- what a person sees."""
  tiles = unit.tiles
  return (round(float(tiles.geometry.area.sum()), 3),
          round(float(tiles.geometry.length.sum()), 3))


def try_design(label, spec, how, args):
  """Measure one design end to end and print what it says.

  Args:
    label: what to call this row in the output.
    spec: the catalogue entry to build the unit from.
    how: the manipulation to apply.
    args: its arguments, as the record keeps them.

  Returns:
    Nothing; prints. Every premise it depends on is asserted or
    reported rather than assumed -- an arm whose edit moved nothing is
    comparing a thing with itself.
  """
  print(f"\n--- {label}: {how} {args} ---")
  unit = catalog.make_unit(spec, spacing=500.0, crs=3857)
  plain, why = topology_edits.build(unit)
  if plain is None:
    print(f"  no topology: {why}")
    return
  topology = plain["topology"] if isinstance(plain, dict) else plain
  before_edges, before_points = classes(topology)
  target = before_points[0] if "vertex" in how else before_edges[0]

  edits = [{"classes": target, "how": how, "args": args}]
  edited, refusals = topology_edits.apply(topology, edits)
  if refusals:
    print(f"  refused: {refusals}")
  if edited is None:
    print("  PREMISE FAILED: the edit produced no unit")
    return

  # PREMISE: the edit MOVED the ground. `push_vertex` cancels exactly
  # on a symmetric vertex, so an arm that measures a design it cannot
  # move is comparing a thing with itself.
  moved_from, moved_to = ground(unit), ground(edited)
  print(f"  ground: {moved_from} -> {moved_to}")
  if moved_from == moved_to:
    print("  PREMISE FAILED: this manipulation moved nothing on this "
          "design, so nothing below is evidence")
    return

  rebuilt, why_again = topology_edits.build(edited)
  if rebuilt is None:
    print(f"  the edited unit carries NO topology: {why_again}")
    print("  -> the drawing cannot show the edited motif on this "
          "design without losing the classes entirely")
    return
  edited_topology = (rebuilt["topology"] if isinstance(rebuilt, dict)
                     else rebuilt)

  after_edges, after_points = classes(edited_topology)
  print(f"  edge classes   {before_edges} -> {after_edges}")
  print(f"  vertex classes {before_points} -> {after_points}")

  same_sets = (before_edges == after_edges
               and before_points == after_points)
  be, bp = by_element(topology)
  ae, ap = by_element(edited_topology)
  same_keys = (set(be) == set(ae) and set(bp) == set(ap))
  same_each = same_keys and all(be[k] == ae[k] for k in be) \
      and all(bp[k] == ap[k] for k in bp)

  print(f"  same label SETS:            {same_sets}")
  print(f"  same element KEYS:          {same_keys}")
  print(f"  same label PER ELEMENT:     {same_each}")
  if same_sets and same_each:
    print("  -> the edited rebuild can be drawn AND hit-tested: every "
          "class means what it meant")
  elif same_sets:
    print("  -> the same classes exist but not on the same elements: "
          "a highlight could land on the wrong one")
  else:
    print("  -> the classes themselves move, so aiming at the edited "
          "drawing records labels the replay cannot use")


try_design("laves 3.3.4.3.4 n=4",
           catalog.TILINGS_BY_N[4]["laves 3.3.4.3.4"],
           "nudge_vertex", {"dx": 0.15, "dy": 0.1})
try_design("archimedean 4.8.8 n=2",
           catalog.TILINGS_BY_N[2]["archimedean 4.8.8"],
           "nudge_vertex", {"dx": 0.15, "dy": 0.1})
try_design("laves 3.3.4.3.4 n=4 (edge)",
           catalog.TILINGS_BY_N[4]["laves 3.3.4.3.4"],
           "rotate_edge", {"angle": 20.0})
