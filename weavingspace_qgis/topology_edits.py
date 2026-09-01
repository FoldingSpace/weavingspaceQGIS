"""What a person has done to a tiling's topology, and how it is replayed.

The Topology tab lets somebody take hold of an edge class or a vertex
class of the repeating UNIT and move it. This module is the record of
those acts and the rules for replaying them; the tab is the view.

WHAT IS RECORDED IS THE ACT, NOT THE RESULT (ruling 3 of the grilling
of 2026-08-30). An edit is `{"classes": "ab", "how": "push_vertex",
"args": {...}}` -- about a hundred bytes -- and it is replayed onto a
unit built fresh from the catalogue. Storing the edited GEOMETRY
instead was measured and refused: the coordinates scale with spacing,
so a stored polygon is wrong the moment somebody changes it, while a
class label was measured stable across rebuilds AND across spacings
500 and 1300.

AND AN EDIT BELONGS TO THE DESIGN IT WAS MADE ON (ruling 4). Edge
classes differ between families -- laves 3.3.4.3.4 has `a,b` and
hex-slice 4 has `a,b,c,d` -- so `a` names a different edge in each and
replaying by label alone would land somebody's edit on the wrong one.
Edits are therefore SHELVED by (family, element count): idle while the
design is elsewhere, and back when it returns. That is the shape this
project has settled twice, for the scheme shelf and for a modifier
number somebody typed.

THE TOPOLOGY IS OF THE UN-MODIFIED UNIT (ruling 1), built before aspect
and insets are applied. `Topology` requires a GAP-FREE tiling and the
plugin's ordinary settings do not give it one: the default weave aspect
is 0.75, and any tile inset makes even laves 3.3.4.3.4 raise. Editing
the motif and letting the modifiers apply over the top is the order the
pipeline already uses.
"""

from __future__ import annotations

import math

# Each entry is one manipulation the tab offers:
#   label     what the control says
#   target    "edge" or "vertex" -- which class list to choose from
#   args      (name, label, low, high, default, step) per parameter
#   fragile   True where the result often cannot be tiled; see `apply`
#
# MEASURED ON FOUR DESIGNS, 2026-08-30. `push_vertex`, `nudge_vertex`,
# `scale_edge` and `rotate_edge` each produce a tiling that draws, at
# 0.04-0.05s. `zigzag_edge` produced none, and is offered anyway on the
# maintainer's decision: it is the manipulation upstream's own notebook
# features, and leaving it out would make the tab thinner than the
# library. It attempts a repair and refuses in words where it cannot,
# which is `bridge.inset_collapse_message`'s shape rather than the
# library's raw "make_valid=False along with 159 invalid input
# geometries".
MANIPULATIONS = {
  "push_vertex": {
    "label": "Push vertex out",
    "target": "vertex",
    # `push_d`, NOT `d`, and the difference is silent: the library
    # filters supplied kwargs to the ones its function accepts, so a
    # wrong name is DROPPED rather than refused. Measured 2026-08-30 --
    # an early probe passed `d` with a lowercase selector, no vertex
    # matched, nothing ran at all, and the unchanged unit drew
    # perfectly, which read exactly like a manipulation that worked.
    "args": (("push_d", "Distance", -1.0, 1.0, 0.1, 0.01),),
    "fragile": False,
  },
  "nudge_vertex": {
    "label": "Nudge vertex",
    "target": "vertex",
    "args": (("dx", "Left-Right", -1.0, 1.0, 0.05, 0.01),
             ("dy", "Up-Down", -1.0, 1.0, 0.05, 0.01)),
    "fragile": False,
  },
  "rotate_edge": {
    "label": "Rotate edge",
    "target": "edge",
    "args": (("angle", "Angle (°)", -90.0, 90.0, 15.0, 1.0),),
    "fragile": False,
  },
  "scale_edge": {
    "label": "Scale edge",
    "target": "edge",
    "args": (("sf", "Factor", 0.1, 3.0, 1.1, 0.05),),
    "fragile": False,
  },
  "zigzag_edge": {
    "label": "Zigzag edge",
    "target": "edge",
    # `smoothness` is the authors' own third argument, and the
    # selector they pass is a STRING OF MANY CLASSES rather than one.
    # Both were learnt from `examples/topology-working.ipynb` after a
    # first reading nearly filed this as a defect in the library.
    "args": (("n", "Zigzags", 1.0, 8.0, 2.0, 1.0),
             ("h", "Amplitude", 0.01, 1.0, 0.25, 0.05),
             ("smoothness", "Smoothness", 0.0, 6.0, 3.0, 1.0)),
    "fragile": True,
  },
}

# Which arguments are whole numbers, so a spin box's float does not
# reach a library expecting a count.
_WHOLE = {"n", "smoothness"}

# WHICH ARGUMENTS ARE DISTANCES, AND THEREFORE FRACTIONS OF THE UNIT.
# (2026-08-31, measured after the maintainer reported that clicking and
# dragging nodes moved nothing at all.)
#
# The library's `dx`, `dy` and `push_d` are ABSOLUTE displacements in
# the unit's own coordinates, and these controls offer them over -1 to
# 1 as though they were proportions. On a design spanning 707 map
# units that made the whole domain of both vertex manipulations
# invisible:
#
#     nudge_vertex  dx=dy=1.0  ->  moves 1.414 units  =  0.20% of it
#     nudge_vertex  dx=0.5     ->  moves 0.500 units  =  0.07%
#     push_vertex   push_d=1.0 ->  moves 0.414 units  =  0.06%
#
# Under a pixel on a 400-pixel drawing, at the largest value either
# control can express -- which is this project's own rule that A
# CONTROL MUST BE ABLE TO REPRESENT ITS DOMAIN, arriving in a new tab.
# The edge manipulations were never affected: an angle, a factor and a
# zigzag count are dimensionless, and at one step they move 1-6%.
#
# SO THE RECORD KEEPS FRACTIONS and the library is handed map units.
# The record is what a person set and what travels to the file; the
# multiplication happens at the one place the unit is known. A drag
# already reports itself as a fraction of the unit, so the two now
# agree by construction rather than by a factor nobody could see.
_SPAN_RELATIVE = {"dx", "dy", "push_d"}


def unit_span(unit) -> float:
  """How wide the unit is, in its own coordinates.

  Args:
    unit: a Tileable.

  Returns:
    The larger of its tiles' width and height, or 1.0 where that
    cannot be read -- a fallback of one leaves a fraction meaning what
    it meant before this scaling existed, which is a small edit rather
    than a wrong one.
  """
  try:
    x0, y0, x1, y1 = unit.tiles.total_bounds
    span = max(float(x1) - float(x0), float(y1) - float(y0))
    return span if span > 0 else 1.0
  except Exception:                                   # noqa: BLE001
    return 1.0


def in_map_units(args: dict, unit) -> dict:
  """A record's fractions as the distances the library expects.

  Args:
    args: the edit's arguments as recorded, where every distance is a
      fraction of the unit's span.
    unit: the Tileable the edit is about to be applied to.

  Returns:
    A new dict with the distance arguments multiplied by that span and
    everything else untouched. Never mutates its input: the record is
    what travels to the file, and scaling it in place would write map
    units into a file that promises fractions.
  """
  span = unit_span(unit)
  return {key: (value * span if key in _SPAN_RELATIVE else value)
          for key, value in args.items()}

# How much of the unit's own area has to change before a manipulation
# counts as having done something. The measurement it rests on is at
# `_same_shape`, which is the only reader.
_NOTHING_MOVED = 1e-7


def whole_where_needed(args: dict) -> dict:
  """An argument mapping with the counts made whole.

  Args:
    args: what a control or a saved edit says, where every number is a
      float because every parameter box is a QDoubleSpinBox.

  Returns:
    A new mapping, with the arguments named in `_WHOLE` rounded to
    integers and the rest left as floats. The original is untouched.

  IT IS A FUNCTION SO THAT BOTH CALLERS SHARE IT. `zigzag_edge` counts
  zigzags with `range`, so a float `n` raises "'float' object cannot be
  interpreted as an integer" -- and `apply` had done this inline since
  it was written while the tab's own live PREVIEW did not, so a zigzag
  drag drew nothing and said nothing (measured 2026-08-30). One fact
  held in two places, mended in one, is this project's commonest
  defect; here it is the same fact in one place.
  """
  return {name: int(round(value)) if name in _WHOLE else float(value)
          for name, value in args.items()}


def shelf_key(family: str, elements: int) -> str:
  """The key an edit list is shelved under.

  Args:
    family: the family name as the chooser shows it.
    elements: how many elements the design has.

  Returns:
    A string, because this travels through JSON in the working state
    and JSON has no tuples -- a lesson this repository has already
    paid for once, where an edge id went out as a tuple and came home
    as a list.
  """
  return f"{family}#{int(elements)}"


def can_build(unit) -> tuple[bool, str]:
  """Whether a topology can be built for this unit, and why not.

  Args:
    unit: the Tileable to examine.

  Returns:
    (True, "") where a topology can be built, else (False, reason) with
    a sentence naming the CONTROL rather than the library. `Topology`
    needs a gap-free tiling, and what opens the gaps is always a
    control somebody moved: a weave's strand width, or an inset.

  THE ANSWER IS TAKEN BY TRYING, not by inspecting the design. Whether
  a unit is gap-free is a property of its geometry, and the conditions
  that produce gaps are not a list anybody here could keep current --
  measured on 2026-08-29, a plain weave builds a topology at aspect 1.0
  and raises at 0.95, 0.9 and 0.75 alike, which no reading of the
  controls would have predicted.
  """
  try:
    _topology_class()(unit, True)
  except Exception as exc:                            # noqa: BLE001
    return False, _why_not(exc)
  return True, ""


def _why_not(exc: Exception) -> str:
  """Turn the library's complaint into the plugin's own sentence.

  Args:
    exc: whatever `Topology` raised.

  Returns:
    One sentence for the user. The library's own words name its
    internals -- "Vertex ... Tiles: [] is not in list" -- which tells
    somebody nothing about the control they just moved.
  """
  return (
    "This design has gaps between its tiles, and a topology can only "
    "be worked out for a design whose tiles meet. Set the strand "
    "width to 1.0, or the tile inset to 0, to work on its topology.")


def _topology_class():
  """The vendored Topology class, imported at the point of use.

  Returns:
    The class. Imported lazily because the vendored library is heavy
    and this module is read by the dialog at construction, where a tab
    nobody has unlocked should cost nothing.
  """
  from .vendor.weavingspace.topology import Topology
  return Topology


def build(unit):
  """The topology of a unit, or None where it has gaps.

  Args:
    unit: the Tileable, before modifiers.

  Returns:
    (topology, "") or (None, reason).

  MEASURED COST, 2026-08-30: 0.75s on laves 3.3.4.3.4 and 2.1-4.4s on
  hex-slice 6 and square-colouring 5. That is why the caller builds
  this off the main thread and only once somebody has ticked the
  experimental box.
  """
  try:
    return _topology_class()(unit, True), ""
  except Exception as exc:                            # noqa: BLE001
    return None, _why_not(exc)


def classes(topology) -> dict:
  """The edge and vertex classes an edit can be aimed at.

  Args:
    topology: a built Topology.

  Returns:
    {"edge": "ab", "vertex": "AB"} -- each a string of the distinct
    transitivity-class labels, in order, which is the form the
    library's own selector takes.
  """
  edges = sorted({e.label for e in topology.edges.values()
                  if getattr(e, "label", None)})
  points = sorted({v.label for v in topology.points.values()
                   if getattr(v, "label", None)})
  return {"edge": "".join(edges), "vertex": "".join(points)}


def apply(topology, edits):
  """Replay an edit list onto a topology, returning what to draw.

  Args:
    topology: a freshly built Topology for the current unit.
    edits: the record, oldest first.

  Returns:
    (tileable, refusals, state) -- the unit to tile, a list of
    sentences about edits that could not be drawn, and a dict carrying
    what the caller needs afterwards:

      "topology"  the object the NEXT edit is aimed with
      "marks"     one entry per edit, in order, saying whether it was
                  applied and whether the design still carried a
                  topology once it had been

    The tileable is the ORIGINAL where every edit was refused, so a
    design never silently becomes something nobody asked for. The marks
    are one-to-one with `edits`, including the ones that were refused,
    because a change list whose annotations slip by one is worse than
    a change list with none.

  EACH EDIT IS APPLIED TO THE OBJECT THE LAST ONE RETURNED, and is NOT
  rebuilt in between. (Maintainer's question, 2026-08-31: "if the
  topology breaks, can't we still apply some of the operations using
  the last topology labels regardless even if we currently are dealing
  with an invalid topology?" -- and the answer measured that day is
  yes, with two other gains besides.)

  WHAT REBUILDING COST, measured on the two designs a topology can be
  had for. It made an edit after a topology-BREAKING one impossible:
  `rotate_edge` routinely leaves a design with gaps, `Topology` refuses
  a design with gaps, so `build` returned None and every later edit was
  refused for want of anything to aim at. Chained, the same pair
  applies -- laves 3.3.4.3.4 goes to area 246,110 where rebuilding
  could not go at all. And it moved the LABELS under the person: a
  fresh build re-derives the classes, so "A" afterwards is not
  necessarily the A they clicked, which is why the two arms disagree by
  a rounding on hex-slice 3 and agree exactly on laves.

  UPSTREAM'S CAUTION IS ABOUT SOMETHING ELSE. `transform_geometry`
  prints that a new Topology "will probably not be correctly labelled",
  which is a warning that its labels may not match A FRESH BUILD. We do
  not want a fresh build: the labels a person aims with are the ones
  they were shown, and keeping them is the point rather than a
  compromise. Measured over five chained edits on two designs: the
  class list never moved (`a,b` and `A,B` throughout) and every
  intermediate tileable stayed valid.

  AND THE REPAIR IS NOT FED BACK. `_make_drawable` mends what a
  manipulation can emit -- coincident vertices, mostly zigzag's, and
  upstream fixed that at source in the commit vendored the same day --
  and the mended copy is what is DRAWN and tiled. The chain carries the
  library's own object, because handing a repaired tileable back into
  a topology would be building the thing this rebuild-free path exists
  to avoid. The repair is measured to leave every area unchanged to a
  part in 1e9, so the two do not drift in any way a map can show.
  """
  current = topology
  tileable = topology.tileable
  refusals = []
  # ONE MARK PER EDIT, in the order they were made: whether the edit
  # was applied at all, and whether the design STILL CARRIED A TOPOLOGY
  # once it had been. (Maintainer's ask, 2026-08-31: "maybe we can
  # visually indicate in the editor and even the change list what the
  # topologically valid transformations were such that there's some
  # indication of how far back you'd need to roll".) It costs 0.3 ms an
  # edit, which is what makes it affordable to ask every time rather
  # than only when somebody wonders.
  marks = []
  for edit in edits or ():
    how = edit.get("how")
    if how not in MANIPULATIONS:
      refusals.append(f"'{how}' is not a manipulation this version "
                      f"offers, so it was left out.")
      marks.append({"applied": False, "gap": None,
                    "sound": None})
      continue
    selector = edit.get("classes") or ""
    # NOTHING HERE ASKS WHETHER THE DESIGN STILL HAS A REBUILDABLE
    # TOPOLOGY, and that is the point of chaining: the object carries
    # its own classes forward, so an edit after one that opened gaps is
    # aimed with the labels it was always aimed with. The guard that
    # stood here refused exactly that case.
    if current is None:
      refusals.append(
        f"{MANIPULATIONS[how]['label']} on {selector} could not be "
        f"applied, because there is no topology to aim it with.")
      marks.append({"applied": False, "gap": None,
                    "sound": None})
      continue
    # AN EDIT AIMED AT A CLASS THIS DESIGN DOES NOT HAVE IS ANSWERED
    # HERE, EXACTLY, BEFORE ANY GEOMETRY IS INVOLVED. The library takes
    # such a selector without complaint -- `transform_geometry` walks
    # its edges asking `e.label in selector` and simply matches none --
    # so the change list would grow while the map stood still. That is
    # the ordinary consequence of the shelf: edits are replayed by
    # class LABEL, and a label belongs to the design it was made on.
    # Asking the topology which labels it holds needs no tolerance and
    # cannot be defeated by the library re-gridding what it hands back,
    # which is what the shape comparison below was trying and failing to
    # do for this case (measured 2026-08-31).
    target = MANIPULATIONS[how]["target"]
    available = classes(current).get(target, "")
    wanted = list(dict.fromkeys(selector))
    missing = [label for label in wanted if label not in available]
    if missing:
      names = ", ".join(repr(label) for label in missing)
      kept = "".join(label for label in wanted if label in available)
      if not kept:
        refusals.append(
          f"{MANIPULATIONS[how]['label']} on {selector or 'nothing'!r} "
          f"was not applied: this design has no {target} class {names}. "
          f"Its {target} classes are "
          f"{available or 'none, so it cannot carry this change'}.")
        marks.append({"applied": False, "gap": None,
                      "sound": None})
        continue
      # SOME of the classes are here, so the change is made to those
      # and the rest are named. Saying nothing about them would leave
      # a change that half happened and looked complete.
      refusals.append(
        f"{MANIPULATIONS[how]['label']} on {selector!r} was applied to "
        f"{kept!r} only: this design has no {target} class {names}.")
      selector = kept
    # FRACTIONS IN THE RECORD, MAP UNITS AT THE LIBRARY, and the unit
    # asked is the CURRENT one so a chain of edits keeps meaning the
    # same thing as the design moves under it.
    args = in_map_units(whole_where_needed(edit.get("args") or {}),
                        current.tileable)
    try:
      moved = current.transform_geometry(True, True, selector, how, **args)
    except Exception:                                 # noqa: BLE001
      refusals.append(_refusal(how, selector))
      marks.append({"applied": False, "gap": None,
                    "sound": None})
      continue
    drawable, _repaired = _make_drawable(moved.tileable)
    if drawable is None:
      refusals.append(_refusal(how, selector))
      marks.append({"applied": False, "gap": None,
                    "sound": None})
      continue
    # THE MAP FOLLOWS THE EDIT EVEN WHERE THE TOPOLOGY CANNOT BE
    # REBUILT, which is the distinction this got wrong first time.
    # Measured 2026-08-30: `rotate_edge` and `scale_edge` produce a
    # unit that lays out perfectly and whose topology will not build,
    # and refusing those threw away a drawable map to protect an
    # ability nobody had asked to keep. Rebuilding is for AIMING THE
    # NEXT EDIT; drawing needs only the tileable.
    # AND AN EDIT THAT CHANGES NOTHING IS REPORTED TOO, which is a
    # different sentence from "this could not be drawn" and was missing
    # until the topology matrix asked for it (2026-08-30). The library
    # is entitled to accept a manipulation and move nothing -- a
    # selector matching no edge of that class, or a parameter this
    # geometry is indifferent to -- and `transform_geometry` neither
    # raises nor says so. Without this the person presses Apply, the
    # list of changes grows, the map is identical, and NOTHING explains
    # why: a control that takes a click and does nothing at all, which
    # is this plugin's second characteristic failure.
    if _same_shape(tileable, drawable):
      refusals.append(
        f"{MANIPULATIONS[how]['label']} on {selector or 'this design'} "
        f"changed nothing about it, so the design is as it was. A "
        f"different class, or a larger value, usually does something.")
    tileable = drawable
    ratio, _where = gaps(drawable)
    marks.append({"applied": True, "gap": ratio,
                  "sound": ratio < GAP_TOLERANCE})
    # CHAINED, NOT REBUILT. `moved` is the library's own object and
    # carries the labels this edit was aimed with; `drawable` is the
    # repaired copy that gets drawn and tiled. See the docstring for
    # what rebuilding here used to cost.
    current = moved
  # AND THE DUAL IS REFRESHED, because `transform_geometry` makes its
  # new object with `copy.deepcopy` -- so `dual_tiles` comes across
  # UNCHANGED and describes the design before the edit. Measured
  # 2026-08-31 on laves 3.3.4.3.4 after a 15-degree rotate: the copied
  # dual has area 249,423 and the honest one 248,842, and a rebuild of
  # that edited unit is impossible because the rotation opens gaps --
  # so recomputing here is the ONLY way to have a dual that belongs to
  # the design. It costs 4 ms.
  # THIS IS LEDGER ROW 2026-08-30's DEFECT ARRIVING BY A NEW ROAD: a
  # motif written beside somebody else's dual, which is what ruling 3's
  # two tables exist to prevent.
  if current is not None and current is not topology:
    try:
      current.generate_dual()
    except Exception:                                 # noqa: BLE001
      # A dual that cannot be recomputed is left as it was rather than
      # dropped: the toggle draws something slightly stale instead of
      # nothing, and the write refuses a pair whose stamps disagree.
      pass
  return tileable, refusals, {"topology": current, "marks": marks}


def gaps(unit):
  """Where a unit's tiles fail to fill the prototile they sit in.

  Args:
    unit: a Tileable.

  Returns:
    (ratio, geometry) -- how much of the prototile is NOT covered, as a
    fraction of its area, and the uncovered ground itself so it can be
    drawn. (0.0, None) where the question cannot be asked.

  WHY THIS RATHER THAN A BUILD. `Topology` requires a gap-free tiling,
  so "does this design still carry a topology" and "do its tiles still
  meet" are the same question -- and one of them costs seconds while
  the other costs a union. Measured on laves 3.3.4.3.4, 2026-08-31,
  against what a real build answers for the same design:

      untouched      0.0        4.0 ms    a build succeeds
      after a nudge  5.2e-10    4.9 ms    a build succeeds
      after a rotate 1.2e-2     5.1 ms    a build REFUSES

  Seven orders of clear air between the two answers and about two
  hundred times cheaper than the build, which is what makes it
  affordable once per edit -- so the change list can say where a design
  stopped carrying a topology, and somebody can see how far back they
  would have to roll.

  AND THE SAME SUBTRACTION IS THE PICTURE. The uncovered ground is
  exactly what a person needs shown rather than described, which is
  this project's own rule that a control's promise is visual and has to
  be driven to the pixels.
  """
  # IMPORTED AT THE POINT OF USE, as everything geometric in this
  # module is: it is reached only when somebody has opened the tab, and
  # the plugin's start-up should not pay for that.
  import shapely
  try:
    # THE GAPS ARE HOLES IN A PATCH, which is what "the tiles no longer
    # meet" means: lay one ring of repeats down, union them, and any
    # interior ring is ground the tiling has stopped covering.
    #
    # THE FIRST VERSION SUBTRACTED THE UNION FROM THE PROTOTILE and was
    # wrong in a way that read perfectly: a unit's tiles need not lie
    # INSIDE the particular polygon its prototile is, so an untouched
    # laves 3.3.4.3.4 -- whose tiles and prototile have the same area
    # to the last bit -- reported 10.6% of it missing. It was caught by
    # the tab marking an unedited design as broken, which is a claim
    # this project has learnt to distrust: everything reported the same
    # number, including the fixture the standalone measurement had
    # called sound.
    patch = unit.get_local_patch(r=1, include_0=True)
    covered = shapely.union_all(list(patch.geometry))
    holes = []
    for part in getattr(covered, "geoms", [covered]):
      for ring in getattr(part, "interiors", []):
        holes.append(shapely.Polygon(ring))
    if not holes:
      return 0.0, None
    missing = shapely.union_all(holes)
    whole = shapely.union_all([covered, missing])
    if whole.area <= 0:
      return 0.0, None
    return float(missing.area) / float(whole.area), missing
  except Exception:                                   # noqa: BLE001
    return 0.0, None


# Below this the tiles are meeting as well as floating point allows,
# and above it a topology cannot be built. Measured nine orders apart,
# so the threshold is not a tuning parameter -- anything between 1e-9
# and 1e-3 draws the same line on every design tried.
GAP_TOLERANCE = 1e-6


def still_has_a_topology(unit) -> bool:
  """Whether this design's tiles still meet, and so can carry one.

  Args:
    unit: a Tileable.

  Returns:
    True where the gap ratio is under GAP_TOLERANCE. This is the cheap
    twin of `can_build`, and it answers the same question: `Topology`
    refuses a design with gaps.
  """
  ratio, _where = gaps(unit)
  return ratio < GAP_TOLERANCE


def _same_shape(before, after) -> bool:
  """Whether two units are the same shape, for reporting purposes.

  Args:
    before: the unit as it stood.
    after: the unit a manipulation produced.

  Returns:
    True where nothing a person could see has moved. Compares the
    GROUND each tile covers -- the symmetric difference between every
    tile and its counterpart, over the unit's own area -- so the answer
    is about shape rather than about how the coordinates happen to be
    written down.

  IT TOOK THREE WRONG INSTRUMENTS TO GET HERE, and each looked
  obviously right.

  ROUNDING AREAS TO NINE DECIMAL PLACES is an ABSOLUTE tolerance, and a
  unit at spacing 500 has tiles of area 62,500. Measured 2026-08-30:
  asking for a manipulation on a class that does not exist still moves
  every area by about 4e-5 -- the library rebuilding and re-gridding
  the geometry, not an edit -- so the test called that a change and the
  report never fired. That is this project's rule about magnitude being
  a fixture dimension, met from the other side.

  COMPARING AREAS AT ALL IS THE SECOND MISTAKE, and it survived the
  first repair. `push_vertex` on this suite's own fixture moves
  vertices while leaving every tile's area inside any sane tolerance --
  the four tiles of laves 3.3.4.3.4 are 62,500 apiece before and after
  -- so a summary statistic said "nothing happened" about an edit whose
  WKT plainly differs. A statistic is not a shape: two different
  polygons can share an area, and this fixture is full of tiles that
  do.

  AND `shapely.equals_exact` IS THE THIRD, which is the one that made
  this report unreachable rather than merely noisy. It compares
  COORDINATE SEQUENCES and not shapes: two rings covering identical
  ground read as different the moment one of them begins at another
  vertex. `transform_geometry` re-grids the unit it hands back and
  restarts those rings, so on archimedean 4.8.8 -- the first design in
  the catalogue that carries a topology, and therefore the one the
  registered test lands on -- a manipulation aimed at a class that does
  not exist moved a coordinate by FIVE HUNDRED map units while the
  symmetric difference stayed at 2.4e-4. The comparison duly answered
  "something changed", the report stayed silent, and the test written
  to catch exactly that silence failed. (Measured 2026-08-31.)

  THE MEASUREMENT THE THRESHOLD RESTS ON, taken the same day over three
  designs, as a fraction of the unit's own area:

      a manipulation matching no class     1.5e-9 to 2.5e-9
      push_vertex where it moves anything  1.9e-4
      nudge, rotate and scale              2.8e-4 to 1.4e-1

  So `_NOTHING_MOVED` has three orders of clear air on either side of
  it. What is left at 1e-9 is the library rebuilding and re-gridding
  the geometry on the way past, which it does whether or not anything
  was edited.

  IT ANSWERS FALSE WHEN IT CANNOT TELL, deliberately: a unit whose
  geometry will not be read is not evidence that nothing happened, and
  saying "this changed nothing" wrongly is worse than staying quiet.
  """
  try:
    one = getattr(before, "tiles", None)
    two = getattr(after, "tiles", None)
    if one is None or two is None or len(one) != len(two):
      return False
    moved, area = 0.0, 0.0
    for a, b in zip(one.geometry, two.geometry):
      moved += a.symmetric_difference(b).area
      area += a.area
    if area <= 0.0:
      return False
    return (moved / area) < _NOTHING_MOVED
  except Exception:                                     # noqa: BLE001
    return False


def _refusal(how: str, selector: str) -> str:
  """What the user is told when an edit cannot be drawn.

  Args:
    how: the manipulation's key.
    selector: the classes it was aimed at.

  Returns:
    One sentence naming the CONTROL, not the library. The library's own
    message quotes its internals and a count of invalid geometries,
    which tells nobody what to do differently.
  """
  label = MANIPULATIONS.get(how, {}).get("label", how)
  return (f"{label} on {selector or 'this design'} left tiles that "
          f"cannot be laid out, so it was not applied. A smaller value "
          f"often works where a larger one does not.")


def _make_drawable(unit):
  """Repair an edited unit far enough to tile, or say it cannot be.

  Args:
    unit: the Tileable a manipulation produced.

  Returns:
    (unit, repaired) where the unit can be tiled -- `repaired` saying
    whether anything had to be mended -- else (None, False).

  WHY THIS EXISTS AND WHAT IT IS WORTH. Measured 2026-08-30 across four
  designs: `zigzag_edge` produces tiles the tiling machinery refuses,
  even through the call shape upstream's own notebook uses. Mending
  them with `shapely.make_valid` rescues hex-slice 4, which then draws
  382 tiles, and makes laves 3.3.4.3.4 worse -- 159 invalid geometries
  becoming 343. So the repair is attempted and its success is CHECKED
  rather than assumed, which is why this returns None instead of
  handing back something that will raise later, inside a worker, where
  the user would meet it as a run that did nothing.
  """
  if _tiles_lay_out(unit):
    return unit, False
  try:
    mended = unit.tiles.copy()
    # STEP ONE IS EXACT AND DOES ALMOST ALL OF IT. Measured on
    # `chavey` code K -- the design upstream's own notebook zigzags --
    # twelve of twenty tiles come back invalid, and dropping repeated
    # vertices takes that to ONE with every area unchanged to a part
    # in 1e9. A repeated vertex is a zero-length segment, which
    # shapely reports as a self-intersection, so removing it changes
    # no shape whatever.
    step_one = [_upstream_clean(g) or _without_repeats(g) or g
                for g in mended.geometry]
    # STEP TWO IS FOR THE RESIDUE, and is a repair rather than a
    # tidy-up: a genuine crossing. It is applied only to the tiles
    # that are still invalid, so a design needing none is untouched by
    # it -- and measured on that same case it moved no tile's area
    # either.
    import shapely
    step_two = []
    for shape in step_one:
      if shape.is_valid:
        step_two.append(shape)
        continue
      whole = _largest_part(shapely.make_valid(shape))
      step_two.append(whole if whole is not None else shape)
    mended["geometry"] = step_two
    trial = _shallow_copy_with_tiles(unit, mended)
    if trial is not None and _tiles_lay_out(trial):
      return trial, True
  except Exception:                                   # noqa: BLE001
    pass
  return None, False


def _upstream_clean(polygon):
  """Upstream's own repair for the polygons a manipulation emits.

  Args:
    polygon: a shapely Polygon or MultiPolygon.

  Returns:
    The cleaned polygon, or None where the library has no such function
    or it will not run -- in which case the caller falls back to this
    module's own exact dedupe, so a vendor without it still works.

  THE LIBRARY'S AUTHOR NAMED THIS, 2026-08-30: "I can recover valid
  polygons from the ones it makes with tiling_utils.get_clean_polygon",
  and "there's probably some doubling up of coordinates happening" --
  which is the same fault this module measured independently as
  repeated vertices, confirmed from the side that wrote the
  manipulation.

  IT IS PREFERRED OVER OUR OWN FOR TWO REASONS, and neither is
  deference. It removes corners that are merely VERY CLOSE as well as
  exactly coincident, and then the COLINEAR ones -- a zigzag emits both
  -- where ours only ever removed exact repeats. And it is upstream's,
  so it moves with the library at a re-vendor instead of being a second
  implementation of the same idea that has to be kept in step.

  OURS IS KEPT AS THE FALLBACK rather than deleted, because this is a
  vendored dependency: a re-vendor that drops or renames the function
  would otherwise take the repair with it silently.
  """
  try:
    from .vendor.weavingspace import tiling_utils
  except Exception:                                     # noqa: BLE001
    return None
  clean = getattr(tiling_utils, "get_clean_polygon", None)
  if clean is None:
    return None
  try:
    mended = clean(polygon)
  except Exception:                                     # noqa: BLE001
    # A polygon it cannot clean is not a reason to lose the tile; the
    # caller's own dedupe and `make_valid` still have a turn.
    return None
  return mended if mended is not None and not mended.is_empty else None


def _without_repeats(polygon, tol: float = 1e-9):
  """The same polygon with consecutive coincident vertices removed.

  Args:
    polygon: a shapely Polygon.
    tol: how close two points must be to count as the same one.

  Returns:
    A Polygon of the same shape, or None where a ring is left with too
    few points to be one. Rings are closed again explicitly, since
    dropping a repeat can open one.

  THIS IS NOT AN APPROXIMATION. A ring carrying the same point twice
  has a zero-length segment in it, and every such segment is reported
  as a self-intersection; taking it out leaves the boundary exactly
  where it was. Measured 2026-08-30: areas unchanged to a part in 1e9
  across the whole unit.
  """
  from shapely.geometry import Polygon

  def tidy(ring):
    points = list(ring.coords)
    if not points:
      return None
    kept = [points[0]]
    for point in points[1:]:
      if ((point[0] - kept[-1][0]) ** 2 +
          (point[1] - kept[-1][1]) ** 2) ** 0.5 > tol:
        kept.append(point)
    if ((kept[0][0] - kept[-1][0]) ** 2 +
        (kept[0][1] - kept[-1][1]) ** 2) ** 0.5 > tol:
      kept.append(kept[0])
    return kept if len(kept) >= 4 else None

  try:
    outer = tidy(polygon.exterior)
    if outer is None:
      return None
    holes = [ring for ring in (tidy(r) for r in polygon.interiors) if ring]
    return Polygon(outer, holes)
  except Exception:                                   # noqa: BLE001
    return None


def _largest_part(geometry):
  """The biggest polygon in whatever `make_valid` handed back.

  Args:
    geometry: a Polygon, a MultiPolygon, or a collection.

  Returns:
    The largest Polygon in it, or None where there is none. Mending a
    self-intersection can split a tile into a large piece and a sliver;
    the tile is the large piece, and keeping the collection would give
    an element a second body nobody drew.
  """
  if geometry is None:
    return None
  if getattr(geometry, "geom_type", "") == "Polygon":
    return geometry
  parts = [part for part in getattr(geometry, "geoms", [])
           if getattr(part, "geom_type", "") == "Polygon"]
  return max(parts, key=lambda part: part.area) if parts else None


def _shallow_copy_with_tiles(unit, tiles):
  """The same unit wearing different tiles.

  Args:
    unit: the Tileable to copy.
    tiles: the GeoDataFrame to put on it.

  Returns:
    A copy, or None where the library will not make one. The
    regularised prototile is rebuilt, which is the step
    `transform_geometry` does not take and which upstream's own
    notebook takes by hand whenever it builds a unit from topology
    output.
  """
  import copy
  try:
    twin = copy.deepcopy(unit)
    twin.tiles = tiles
    twin._setup_regularised_prototile(override=True)
  except Exception:                                   # noqa: BLE001
    return None
  return twin


def _tiles_lay_out(unit) -> bool:
  """Whether this unit's tiles can be laid out at all.

  Args:
    unit: the Tileable to test.

  Returns:
    True when every tile is a valid polygon and the unit can produce a
    local patch, which is the cheapest question that separates a unit
    the tiling machinery will accept from one it refuses.

  ASKED OF THE UNIT RATHER THAN BY TILING A REGION, deliberately: a
  real tiling needs a region and costs whatever the region costs, and
  this is asked while somebody is dragging.
  """
  try:
    if not all(g.is_valid and not g.is_empty for g in unit.tiles.geometry):
      return False
    patch = unit.get_local_patch(r=1, include_0=True)
    return bool(len(patch)) and all(g.is_valid for g in patch.geometry)
  except Exception:                                   # noqa: BLE001
    return False


def dual_frame(topology):
  """The dual tiling, as a frame ready to become a layer.

  Args:
    topology: a built Topology.

  Returns:
    A GeoDataFrame of the dual's polygons with a `tile_id` column, or
    None where the library gives none. Written to the GeoPackage beside
    the unit so a colleague can open the motif and its dual without the
    plugin at all -- the argument that put the element tables and their
    styles in there.
  """
  try:
    frame = topology.get_dual_tiles()
  except Exception:                                   # noqa: BLE001
    return None
  if frame is None or not len(frame):
    return None
  return _in_unit_space(frame)


def unit_frame(unit):
  """The tile unit's own tiles, as a frame ready to become a layer.

  Args:
    unit: a Tileable -- the edited one where there are edits, since
      what belongs in the file is what somebody made rather than what
      the family starts at.

  Returns:
    A GeoDataFrame of the unit's tiles carrying no CRS, or None where
    the unit has no tiles to give.

  IT IS THE UNIT AND NOT THE MAP. The map's tiles are already in the
  file, one table per element, in the region's own coordinates. This is
  the motif those were stamped out of, which is the thing a topology is
  ABOUT and the thing an edit moves.
  """
  tiles = getattr(unit, "tiles", None)
  if tiles is None or not len(tiles):
    return None
  return _in_unit_space(tiles)


def _in_unit_space(frame):
  """A copy of a frame with any CRS taken off it.

  Args:
    frame: a GeoDataFrame from the topology or the unit.

  Returns:
    A COPY with `crs` set to None, so the caller cannot hand a live
    frame to a writer and have the stripping reach the object the rest
    of the dialog is drawing from.

  WHY THIS EXISTS AS A FUNCTION RATHER THAN A LINE AT EACH WRITE. The
  unit carries whatever CRS the map is in -- `_adopt_edited_unit` puts
  it back on deliberately, so the preview and the tiling agree -- and
  that CRS is a LIE about these coordinates: the numbers are a few
  units across because they describe a motif, not a place. Writing
  them under the map's CRS would put a two-unit-wide unit at the
  origin of somebody's projection. One owner, so the two writes cannot
  drift apart the way a pair in this project usually does.
  """
  copy = frame.copy()
  try:
    copy.crs = None
  except Exception:                                   # noqa: BLE001
    # A frame that will not give its CRS up is not written at all,
    # since the whole point of the table is that it carries none.
    return None
  return copy

# ---------------------------------------------------------------------
# THE SYMMETRIES A DESIGN ALREADY KNOWS ABOUT
#
# A built `Topology` carries `tile_matching_transforms`: every isometry
# that maps the tiling onto itself, each one a `Transform` with a kind,
# an angle and a centre. Measured 2026-09-01, that is 18 of them on
# `archimedean 4.8.8`, 24 on `laves 3.3.4.3.4` and 96 on
# `square-colouring 5`, so the drawing needs the DISTINCT ones rather
# than the list.
#
# WHY THIS MATTERS FOR EDITING, and not only for looking. A class whose
# every symmetry pins it in place cannot be moved by any displacement
# at all: the tab drew a rail of zero length for `push_vertex` on
# `laves 3.3.4.3.4` and on `hex-slice 3`, and a person pulling it saw
# nothing happen and was told nothing. `directions_a_class_may_move`
# answers that question from the group rather than from the arithmetic.

def _stabiliser(topology, point, tolerance: float = 1e-6):
  """The symmetries that leave one point where it is.

  Args:
    topology: a built Topology.
    point: an (x, y) pair in the unit's own coordinates.
    tolerance: how close counts as "the same place", in map units.

  Returns:
    A list of 2x2 linear parts, as ((a, b), (c, d)) tuples -- the
    rotation or reflection each stabilising transform performs about
    that point. The identity is always among them.

  MODULO THE LATTICE, which is what makes the question answerable on a
  repeating design at all: a symmetry that carries this vertex onto
  the SAME vertex one cell over stabilises it as far as the pattern is
  concerned, and refusing those would report every class as free.
  """
  basis = _lattice_of(topology)
  reduce = _reducer(basis) if basis else (lambda xy: (round(xy[0], 6),
                                                      round(xy[1], 6)))
  here = reduce(point)
  found = []
  for transform in (getattr(topology, "tile_matching_transforms", {})
                    or {}).values():
    matrix = getattr(transform, "transform", None)
    if not matrix or len(matrix) < 6:
      continue
    a, b, c, d, xoff, yoff = (float(v) for v in matrix[:6])
    moved = (a * point[0] + b * point[1] + xoff,
             c * point[0] + d * point[1] + yoff)
    if reduce(moved) == here:
      found.append(((a, b), (c, d)))
  return found


def _lattice_of(topology):
  """The two shortest independent translations of a design, or None.

  Args:
    topology: a built Topology, whose `tileable` carries the vectors.

  Returns:
    A pair of (x, y) tuples, or None where fewer than two independent
    translations are stated. Read from the VALUES rather than the
    keys, since a hex tileable keys them by three-element coordinates
    and a square one by pairs -- the same fault the dual's own repeat
    was drawn wrongly by until 2026-09-01.
  """
  unit = getattr(topology, "tileable", None)
  vectors = getattr(unit, "vectors", None) or {}
  candidates = sorted((tuple(float(c) for c in v) for v in vectors.values()),
                      key=lambda v: v[0] * v[0] + v[1] * v[1])
  first = second = None
  for candidate in candidates:
    if abs(candidate[0]) < 1e-12 and abs(candidate[1]) < 1e-12:
      continue
    if first is None:
      first = candidate
      continue
    cross = first[0] * candidate[1] - first[1] * candidate[0]
    if abs(cross) > 1e-9:
      second = candidate
      break
  return None if second is None else (first, second)


def _reducer(basis):
  """A function taking a point to its place within one cell.

  Args:
    basis: the two lattice vectors.

  Returns:
    A callable mapping (x, y) to a rounded pair of fractional cell
    coordinates, so two points that differ by whole translations
    answer the same.
  """
  ax, ay = basis[0]
  bx, by = basis[1]
  determinant = ax * by - ay * bx

  def reduce(point):
    if abs(determinant) < 1e-12:
      return (round(point[0], 6), round(point[1], 6))
    u = (by * point[0] - bx * point[1]) / determinant
    v = (-ay * point[0] + ax * point[1]) / determinant
    u, v = u - math.floor(u), v - math.floor(v)
    # a coordinate a hair under one is a coordinate at zero
    u = 0.0 if u > 1 - 1e-6 else u
    v = 0.0 if v > 1 - 1e-6 else v
    return (round(u, 6), round(v, 6))

  return reduce


def directions_a_class_may_move(topology, target: str, label: str) -> int:
  """How many independent directions a class can be displaced in.

  Args:
    topology: a built Topology.
    target: "vertex" -- the only kind this answers for, since an edge
      manipulation moves a curve rather than a point and its freedom
      is a different question.
    label: the class label.

  Returns:
    2 where the class is free, 1 where it may only move along a line,
    0 where every displacement breaks a symmetry that holds it -- and
    2 where the question cannot be answered (no topology, no such
    class, no symmetries recorded), because refusing to draw a control
    on an unanswered question is worse than drawing one that does
    nothing.

  IT IS NECESSARY AND NOT SUFFICIENT, which the caller must say out
  loud. A zero here means no displacement is available; a one or a two
  does NOT promise a particular manipulation will move anything, since
  a manipulation's own construction may still yield nothing --
  measured on `laves 3.3.4.3.4` class B, which has a one-dimensional
  fixed space and whose push still comes back empty.

  THE ARITHMETIC: stack (L - I) for every stabilising transform and
  take the rank. A displacement d survives the symmetry exactly when
  L d = d for every L that holds the point, so the space of allowed
  displacements is the null space of that stack, and its dimension is
  2 minus the rank.
  """
  if topology is None or target != "vertex" or not label:
    return 2
  point = None
  for vertex in getattr(topology, "points", {}).values():
    if getattr(vertex, "label", None) == label:
      point = (float(vertex.point.x), float(vertex.point.y))
      break
  if point is None:
    return 2
  holders = _stabiliser(topology, point)
  if not holders:
    return 2
  rows = []
  for (a, b), (c, d) in holders:
    rows.append((a - 1.0, b))
    rows.append((c, d - 1.0))
  return 2 - _rank(rows)


def _rank(rows, tolerance: float = 1e-9) -> int:
  """The rank of a list of two-element rows, by elimination.

  Args:
    rows: pairs of floats.
    tolerance: below this a value is zero, which on coordinates of a
      few hundred map units is comfortably below anything real.

  Returns:
    0, 1 or 2. Written out rather than taken from numpy so this module
    keeps working where the scientific stack is being provisioned --
    two columns is not an occasion for a matrix library.
  """
  remaining = [list(row) for row in rows
               if abs(row[0]) > tolerance or abs(row[1]) > tolerance]
  if not remaining:
    return 0
  pivot = max(remaining, key=lambda row: abs(row[0]))
  if abs(pivot[0]) <= tolerance:
    return 1
  rank = 1
  for row in remaining:
    if row is pivot:
      continue
    factor = row[0] / pivot[0]
    left = row[1] - factor * pivot[1]
    if abs(left) > tolerance:
      rank = 2
      break
  return rank


def symmetries_to_draw(topology, limit: int = 60):
  """The distinct symmetries of a design, ready to be drawn.

  Args:
    topology: a built Topology, or None.
    limit: how many of each kind to return at most. `square-colouring
      5` records 96 transforms, and a drawing showing all of them says
      less than one showing the distinct ones.

  Returns:
    A dict with "rotations" -- (x, y, order) triples, one per distinct
    centre, carrying the HIGHEST order found there -- and "mirrors" --
    (x, y, degrees) triples, one per distinct line. Translations are
    left out: the lattice is already visible in the tiles themselves.
    An empty pair of lists where there is nothing to draw.
  """
  rotations, mirrors = {}, {}
  for transform in (getattr(topology, "tile_matching_transforms", {})
                    or {}).values():
    kind = getattr(transform, "transform_type", "")
    centre = getattr(transform, "centre", None)
    angle = float(getattr(transform, "angle", 0.0) or 0.0)
    if centre is None:
      continue
    where = (round(float(centre.x), 4), round(float(centre.y), 4))
    if kind == "rotation":
      if abs(angle) < 1e-9:
        continue
      order = int(round(360.0 / abs(angle)))
      if order < 2:
        continue
      rotations[where] = max(rotations.get(where, 0), order)
    elif kind == "reflection":
      # A MIRROR IS A LINE, so two transforms differing by half a turn
      # in their stated angle are one line and are drawn once.
      line = (where, round(angle % 180.0, 3))
      mirrors[line] = True
  return {
    "rotations": [(x, y, order)
                  for (x, y), order in list(rotations.items())[:limit]],
    "mirrors": [(x, y, angle)
                for ((x, y), angle) in list(mirrors)[:limit]],
  }


def tile_symmetry_codes(unit):
  """Each distinct tile's own symmetry group, as codes.

  Args:
    unit: a Tileable.

  Returns:
    A list of codes like "D4" or "C2", one per tile of the unit, in
    the unit's own order -- or an empty list where the library cannot
    answer. `D` is dihedral (mirrors as well as rotations) and `C`
    cyclic (rotations alone), which is the standard notation for a
    shape's own symmetry group.
  """
  try:
    from weavingspace.symmetry import Symmetries
  except Exception:                                   # noqa: BLE001
    return []
  codes = []
  for geometry in getattr(unit, "tiles", []).geometry:
    try:
      codes.append(Symmetries(geometry).get_symmetry_group_code())
    except Exception:                                 # noqa: BLE001
      codes.append("")
  return codes

# ---------------------------------------------------------------------
# THE DUAL, AS A DESIGN IN ITS OWN RIGHT
#
# THIS IS A WORKAROUND FOR SOMETHING THE LIBRARY DOES NOT OFFER, and it
# is written to this project's own procedure for that (the
# dependency-bug-workaround skill), which means: the measurement is
# here, the removal criteria are here, and a canary test asserts that
# the gap is still there so the day it closes the suite says so.
#
# WHAT IS MISSING. `Topology.get_dual_tiles()` hands back a frame of
# the dual's polygons with tile ids, and the dual of a periodic tiling
# repeats on the SAME lattice -- measured, its ground covers 249,423
# map units against the unit's 248,842, a third of a percent apart.
# But `Tileable.__init__` delegates to `_setup_tiles()`, which
# dispatches on `tiling_type` and has no path for supplied geometry:
# an unrecognised type prints a message and falls back to the default
# tileable. So there is no constructor for "here are the tiles and the
# vectors, make me a Tileable".
#
# WHAT WOULD LET THIS GO. A `TileUnit` that accepts tiles and vectors,
# or a `Topology.dual_as_tileable()`. The patch has gone upstream; when
# it lands, `test_the_library_still_cannot_build_a_unit_from_tiles`
# fails, and that failure is GOOD NEWS: delete this function's body in
# favour of the library's own, and delete the canary with it.

def dual_as_tileable(topology):
  """Turn a design's dual into a Tileable that can be mapped.

  Args:
    topology: a built Topology whose `generate_dual` has run, or which
      can run it.

  Returns:
    A Tileable drawing the dual's tiles on the source design's own
    lattice, or None where the dual cannot be built or the source
    states no usable vectors. None rather than a raise, because a
    design that cannot offer a dual is an ordinary answer and every
    caller here has something to say about it.

  IT COPIES THE SOURCE AND REPLACES ITS TILES, rather than
  constructing a Tileable from nothing: the object carries a CRS, a
  spacing, an id and the vectors, all of which the dual shares by
  construction, and reaching for a constructor that does not exist is
  what this function is working around in the first place.

  THE IDS ARE OURS. The dual's tiles correspond to the source's
  VERTICES, so they are lettered in the order `get_dual_tiles` returns
  them through `bridge.element_table_name`'s own alphabet -- which is
  what keeps a dual of twenty-seven tiles sorting `aa` after `z`
  rather than second.
  """
  if topology is None:
    return None
  unit = getattr(topology, "tileable", None)
  if unit is None:
    return None
  try:
    if not getattr(topology, "dual_tiles", None):
      topology.generate_dual()
    frame = topology.get_dual_tiles()
  except Exception:                                   # noqa: BLE001
    return None
  if frame is None or len(frame) == 0:
    return None
  if not _lattice_of(topology):
    return None
  try:
    ids = [_letters(index) for index in range(len(frame))]
    tiles = frame.copy()
    tiles["tile_id"] = ids
    dual = _shallow_copy_with_tiles(unit, tiles)
    # THE PROTOTILE HAS TO BE REBUILT FROM THE VECTORS, or the unit
    # carries the SOURCE design's outline around the dual's tiles and
    # every consumer that clips to it -- the tiling, the preview, the
    # region overlay -- draws a shape neither design has.
    dual.prototile = dual.get_prototile_from_vectors()
    dual._setup_regularised_prototile()
  except Exception:                                   # noqa: BLE001
    return None
  return dual if _tiles_lay_out(dual) else None


def _letters(index: int) -> str:
  """The nth tile id, in this project's own alphabet.

  Args:
    index: zero-based position.

  Returns:
    "a" to "z", then "aa" to "zz" -- the same doubled alphabet the
    element ceilings settled on, so a dual with more than
    twenty-six tiles keeps ids a GeoPackage can hold apart.
  """
  first, second = divmod(index, 26)
  return (chr(ord("a") + first - 1) if first else "") + chr(ord("a") + second)


def the_library_can_build_a_unit_from_tiles() -> bool:
  """Has the library grown a constructor for supplied geometry?

  Returns:
    True the day `Tileable` accepts tiles and vectors directly -- by
    a `from_tiles` classmethod, a `tiles=` keyword its setup honours,
    or a `dual_as_tileable` of its own. False while the workaround
    above is still earning its place.

  ASKED OF THE LIBRARY, WITH OUR CODE OUT OF THE WAY, which is what
  makes the canary that reads it evidence about the dependency rather
  than about us.
  """
  try:
    from weavingspace.tile_unit import TileUnit
    from weavingspace.topology import Topology
  except Exception:                                   # noqa: BLE001
    return False
  if hasattr(TileUnit, "from_tiles") or hasattr(Topology, "dual_as_tileable"):
    return True
  # A `tiles=` keyword that the setup actually honours would show as a
  # unit whose tiles are the ones handed over; today the keyword is
  # swallowed by `**kwargs` and `_setup_tiles` builds a default.
  try:
    import geopandas as gpd
    from shapely.geometry import Polygon
    square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    frame = gpd.GeoDataFrame({"tile_id": ["a"]}, geometry=[square])
    made = TileUnit(tiling_type="cairo", tiles=frame)
    return len(made.tiles) == 1
  except Exception:                                   # noqa: BLE001
    return False
