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
    # EVEN COUNTS ONLY, 2 to 8 in steps of 2 (maintainer's decision,
    # 2026-09-05): the library's docstring says zigzag "will only work
    # correctly if n is even", and the tab audit measured class b of
    # the default design opening a gap at every odd count. The tab's
    # drag snaps to even and settles a typed odd count; a record that
    # carries an odd count from before this is still applied, and the
    # change list reports the gap it opens, as it always did.
    "args": (("n", "Zigzags", 2.0, 8.0, 2.0, 2.0),
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

# WHAT THE TAB SAYS WHEN A REPLAYED EDIT AIMS AT A DESIGN WHOSE CLASSES
# HAVE MOVED (conflict 7, settled 2026-09-05: the shelf key stays
# narrow and the replay reports). One template, and the mark is what a
# guard looks for, so the sentence can be reworded in review without
# retuning anything -- this suite has been broken by the maintainer's
# own edit to a sentence before.
CLASSES_MOVED = (
  "{label} on {selector!r} was made when this design's {target} classes "
  "were {against}; they are {now} now, so it may not move the same "
  "{target}s.")
CLASSES_MOVED_MARK = "was made when this design's"

ZIGZAG_CLAMPED = (
  "Zigzag edge on {selector} was drawn at an amplitude of {drawn} rather than "
  "{asked}: a deeper wave than that runs beyond the edges next to it. The "
  "number you set is kept, so it comes back in full wherever the design "
  "leaves room for it.")
ZIGZAG_CLAMPED_MARK = "was drawn at an amplitude of"


def _three_figures(value: float) -> str:
  """A number as a person reads it, at three significant figures.

  Args:
    value: the number to show.

  Returns:
    It as a string, trailing zeros and a trailing point removed, since
    this project's rule is at most three significant figures in any
    number a user meets and "0.586" reads where "0.5859375" does not.
  """
  if not value:
    return "0"
  text = f"{value:.3g}"
  return text.rstrip("0").rstrip(".") if "." in text else text


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


def shelf_key(family: str, elements: int, dual=False) -> str:
  """The key an edit list is shelved under.

  Args:
    family: the catalogue KEY of the design, never the label.
    elements: how many elements the design has.
    dual: whether the map is being tiled with the design's DUAL, which
      is a different design with its own edges and its own class
      labels -- or HOW MANY TIMES OVER, since duals chain (2026-09-06)
      and the dual of a dual is a third design. False or 0 where the
      caller has no opinion, which is what an older record carries;
      True is one.

  Returns:
    A string, because this travels through JSON in the working state
    and JSON has no tuples -- a lesson this repository has already
    paid for once, where an edge id went out as a tuple and came home
    as a list.

  THE DUAL IS A TERM BECAUSE IT IS A DESIGN. (2026-09-02, found by
  THREE hunts of one round from three directions -- backwards from
  harm, the specification itself, and the stochastic sessions.) `a`
  names one edge of `hex-slice 4` and quite another of its dual, and
  this key could not tell them apart: an edit made on the dual was
  replayed onto the design's own like-named edge the moment the box
  came off, silently, and rode into the map and the saved file.
  Measured from the record rather than from the geometry
  (`tools/probes/what_the_shelf_key_cannot_tell_apart.py`): with the
  control, a change of family, the key moves and the shelf goes quiet
  as designed; ticking the dual left the key at `hex-slice 4#4` and
  the design's own edit standing, and an edit applied on the dual
  landed in the DESIGN's shelf -- one entry becoming two.

  IT IS A SUFFIX so that nothing already saved moves: a record written
  before this carries the plain key and goes on restoring under it,
  which is the same reasoning as `WORKING_STATE_VERSION` not being
  bumped for an added key.

  WHAT IS DELIBERATELY NOT IN IT is every other design term -- the
  spacing, the modifiers -- though a modifier can move the class
  structure under a label too. That is a wider question about when
  somebody's edits should go quiet, it is the maintainer's, and it is
  recorded in ROADMAP.md rather than settled here.
  """
  return f"{family}#{int(elements)}" + "#dual" * int(dual)


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
    return False, _why_not(exc, unit)
  return True, ""


def covers_its_cell(unit):
  """Whether a unit's tiles fill the cell they repeat in.

  Args:
    unit: a Tileable.

  Returns:
    True where the tiles' area equals the prototile's to within a part
    in a million, False where it falls short, and None where the
    question cannot be asked. A unit that tiles the plane covers
    exactly one cell per repeat, so a shortfall is ground the tiling
    leaves bare -- an inset's channels, a weave's gaps at a strand
    width under 1.0, or a dual missing tiles.

  NOT `gaps()`, DELIBERATELY. That measures HOLES in a patch's union,
  which is what an edit opens; an inset opens channels that reach the
  patch's edge and are not holes, and it measured 0.0 on an inset that
  leaves 35% of the cell bare (2026-09-05). Measured on the default
  design: plain 1.0, inset 25 at 0.651, the promoted-but-short dual
  0.766, the default weave at strand width 0.75 0.9375.
  """
  try:
    tiles = float(unit.tiles.geometry.area.sum())
    cell = float(unit.prototile.geometry.area.sum())
    if cell <= 0:
      return None
    return abs(tiles / cell - 1.0) < 1e-6
  except Exception:                                   # noqa: BLE001
    return None


def _why_not(exc: Exception, unit=None) -> str:
  """Turn the library's complaint into the plugin's own sentence.

  Args:
    exc: whatever `Topology` raised.
    unit: the Tileable it raised on, where the caller has it. Without
      it the answer is the gaps sentence, which was every answer until
      2026-09-05.

  Returns:
    One sentence for the user. The library's own words name its
    internals -- "Vertex ... Tiles: [] is not in list" -- which tells
    somebody nothing about the control they just moved.

  IT MEASURES BEFORE IT BLAMES A GAP. (2026-09-05, field report 5.)
  This returned the gaps sentence for EVERY exception, and the default
  design's dual -- whose tiles meet exactly -- was told to set its
  strand width to 1.0. The library raises for more than one reason and
  only one of them is a control somebody can move, so where the unit
  is to hand it is asked whether its tiles cover their cell, and a
  design whose tiles do is told the truth: the library could not work
  out its structure, and nothing on the tab mends that. Where the
  question cannot be asked the old sentence stands, since a wrong
  "your tiles meet" would send somebody hunting a defect in the
  library that is really an inset.
  """
  if unit is not None and covers_its_cell(unit) is True:
    return (
      "This design's tiles meet, but the library could not work out "
      "its structure, so there is nothing here to edit.")
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


def build(unit, weave=None):
  """The topology of a unit, or None where it has gaps.

  Args:
    unit: the Tileable, before modifiers.
    weave: None for a design that tiles as it stands, or a dict of the
      terms a weave has to be rebuilt from -- `spec`, `spacing`,
      `aspect`, `strands`, `reading` and `families` -- which lets a
      design with daylight be scaffolded into one that tiles.

  Returns:
    `(topology, reason)` where the topology is None on a refusal, and
    for a scaffolded weave `(topology, reason, unit, kinds)`, the unit
    being the scaffolded stand-in and `kinds` saying which of its tiles
    are cloth. Callers that pass no `weave` get the pair they always
    got.

  A WEAVE IS TRIED PLAINLY FIRST. At an aspect of 1.0 a weave already
  tiles, and scaffolding one that needs no scaffolding would put filler
  tiles into a design that has no daylight to fill.

  MEASURED COST, 2026-08-30: 0.75s on laves 3.3.4.3.4 and 2.1-4.4s on
  hex-slice 6 and square-colouring 5. That is why the caller builds
  this off the main thread and only once somebody has ticked the
  experimental box.
  """
  plain = None
  try:
    plain = _topology_class()(unit, True)
  except Exception as exc:                            # noqa: BLE001
    reason = _why_not(exc, unit)
  if plain is not None:
    if weave is None:
      return plain, ""
    # A WEAVE THAT NEEDS NO SCAFFOLDING IS STILL A WEAVE, so the
    # strand-family question is put to it here as well: at full width
    # the mirror that carries warps onto wefts is exactly the symmetry
    # this reading declines to believe in. It sits OUTSIDE the build's
    # own `try`, or a refinement that raised would be reported as a
    # design with no topology at all.
    if weave.get("families") == WARP_AND_WEFT_APART:
      keep_warp_and_weft_apart(plain, None)
    return plain, "", unit, {}, None
  if weave is None:
    return None, reason
  topology, filled, kinds, glue, note = weave_topology(
    weave.get("spec"), weave.get("spacing"), weave.get("aspect"),
    crs=None, strands=weave.get("strands"),
    reading=weave.get("reading", ASPECT_LIKE_A_DROP),
    families=weave.get("families", WARP_AND_WEFT_TOGETHER))
  if topology is None:
    return None, note or reason, None, kinds, glue
  return topology, "", filled, kinds, glue


def classes(topology) -> dict:
  """The edge and vertex classes an edit can be aimed at.

  Args:
    topology: a built Topology.

  Returns:
    {"edge": "ab", "vertex": "AB"} -- each a string of the distinct
    transitivity-class labels, in order, which is the form the
    library's own selector takes.

  IT CANNOT BE SPLIT BACK PAST TWENTY-SIX CLASSES, and that is a
  property of the SELECTOR rather than a defect here: the library
  labels `aa` after `z`, so a joined string stops having one character
  per class. Anything that wants the labels as labels asks
  `class_labels` instead; this stays as it is because a selector is
  what the library takes.
  """
  edges = sorted({e.label for e in topology.edges.values()
                  if getattr(e, "label", None)})
  points = sorted({v.label for v in topology.points.values()
                   if getattr(v, "label", None)})
  return {"edge": "".join(edges), "vertex": "".join(points)}


def class_labels(topology, glue=None) -> dict:
  """The class labels as labels, collapsed by a gluing where given.

  Args:
    topology: a built Topology.
    glue: the map `glue_the_aspect_holes` returned, or None to take the
      classes as the library assigned them.

  Returns:
    `{"edge": [...], "vertex": [...]}`, each a sorted list of the
    distinct labels, one entry per class.

  A LIST RATHER THAN A JOINED STRING, because past twenty-six classes
  the library issues `aa` after `z` and a string cannot be split back
  into labels. A scaffolded weave passes that at once -- `twill weave
  a|b-` has fifty-two edge classes at aspect 0.75 -- so what was a
  latent defect the moment something built on the scaffolding is live
  now that something does.

  AND THE GLUING COLLAPSES THEM HERE, which is what makes the reading
  of a weave's daylight visible to somebody choosing a class: under
  `ASPECT_LIKE_AN_INSET` several of the library's labels name one class
  and the chooser should offer one entry, not several.
  """
  edges = {e.label for e in topology.edges.values()
           if getattr(e, "label", None)}
  points = {v.label for v in topology.points.values()
            if getattr(v, "label", None)}
  if glue:
    edges = {glue["edges"].get(label, label) for label in edges}
    points = {glue["points"].get(label, label) for label in points}
  return {"edge": sorted(edges, key=_label_order),
          "vertex": sorted(points, key=_label_order)}


def _label_order(label: str):
  """Sort a class label the way the library issues them.

  Args:
    label: a class label, `a` to `z` then `aa`, `ab` and on.

  Returns:
    A sort key putting every one-letter label before every two-letter
    one.

  PLAIN ALPHABETICAL IS WRONG HERE, and visibly so: it puts `aa`
  between `a` and `b`, so a basket weave's chooser reads `a, aa, ab,
  ac, ad, ae, b, c`. This project has the same rule for element ids at
  `bridge.element_order`, for the same reason -- `"aa" < "z"`.
  """
  return (len(label), label)


def _move_edges_vertex_consistent(topology, selector: str, displacement_of):
  """Apply an edge manipulation WITHOUT tearing the tiling.

  Args:
    topology: the Topology to edit; it is not mutated (a copy is
      returned).
    selector: the edge-class labels to move, e.g. "a".
    displacement_of: a callable (rx, ry) -> (dx, dy) giving how far a
      point at offset (rx, ry) from the edge midpoint moves under the
      manipulation.

  Returns:
    A new Topology whose `.tileable` carries the edited unit, of the
    same shape `transform_geometry` returns, so the caller chains the
    next edit onto it unchanged.

  IT IS A FUNCTION SO THAT ROTATE AND SCALE SHARE IT. Both library
  manipulations move an edge's two endpoint vertices about the edge's
  own centroid, and both therefore tear a tiling the same way: a tiling
  vertex is shared by two edges of the same class (and by edges of
  others), so two edges moving it about two different centroids each
  demand it sit in a different place. The fan tears -- a lens gap where
  the images pull apart, a lens overlap where they cross. On laves
  3.3.4.3.4 that is 2.2% gap at 20 degrees of rotation and a comparable
  tear under a scale, which is why a plain rotate or scale reports
  itself as no longer carrying a topology.

  A VERTEX ORBIT MOVES ONCE, AND PERIODICALLY. The displacement is
  accumulated per `base_ID` -- the lattice orbit -- from the ORIGINAL
  positions so the order edges are visited cannot change it, averaged,
  and applied to every copy of that orbit, exactly as the library
  applies `push_vertex`. One vector per orbit is a lattice-PERIODIC
  displacement, so the edited unit still tiles with its own translates
  and the tiling stays edge-to-edge across unit boundaries by
  construction -- which is the property the library's per-edge version,
  writing each shared vertex last-write-wins, does not keep.

  WHERE IT MOVES NOTHING, NO GAP-FREE MOVE EXISTS. A periodic
  displacement cannot move the two ends of an edge whose endpoints share
  an orbit in opposite directions, so the design's own symmetry can
  force the orbit's one displacement to zero. That is not the rule
  failing: it is the honest answer that this edge class cannot be turned
  or stretched while its tiles still meet -- the per-edge version's
  apparent movement there is a torn non-tiling, measured to build no
  Topology at all. The caller reports it in the design's own terms, as
  push_vertex's gate reports a vertex with nowhere to go.

  THE COST where it DOES move is that a shared edge is not moved by
  exactly the requested amount: where two edges meet they pull the
  vertex two ways and it takes their average, so the effective change is
  the consistent one rather than the rigid one. That is the trade a
  gap-free manipulation makes, and it is the point -- the result is a
  tiling rather than a torn one.
  """
  import copy
  import geopandas as gpd
  import shapely.affinity as affine
  topo = copy.deepcopy(topology)
  totals = {}                                # base_ID -> [sum_dx, sum_dy, n]
  for edge in topo.edges.values():
    if edge.label not in selector:
      continue
    v0, v1 = edge.get_vertices()
    mid_x = (v0.point.x + v1.point.x) / 2
    mid_y = (v0.point.y + v1.point.y) / 2
    for vertex in (v0, v1):
      dx, dy = displacement_of(vertex.point.x - mid_x, vertex.point.y - mid_y)
      total = totals.setdefault(vertex.base_ID, [0.0, 0.0, 0])
      total[0] += dx
      total[1] += dy
      total[2] += 1
  moves = {base: (t[0] / t[2], t[1] / t[2]) for base, t in totals.items()}
  for point in topo.points.values():
    move = moves.get(point.base_ID)
    if move is not None:
      point.point = affine.translate(point.point, move[0], move[1])
  for tile in topo.tiles:
    tile.set_corners_from_edges()
  topo.tileable.tiles.geometry = gpd.GeoSeries(
    [topo.tiles[i].shape for i in range(topo.n_tiles)])
  topo.tileable._setup_regularised_prototile()
  return topo


def rotate_edges_vertex_consistent(topology, selector: str, angle: float):
  """Rotate a class of edges gap-free; see `_move_edges_vertex_consistent`.

  Args:
    topology: the Topology to edit; not mutated.
    selector: the edge-class labels to rotate.
    angle: degrees counter-clockwise, as the library's `rotate_edge`
      takes it. `centre` is not offered because the tab only ever
      rotates about the edge midpoint.

  Returns:
    A new Topology carrying the rotated unit.
  """
  import math
  theta = math.radians(angle)
  cos_t, sin_t = math.cos(theta), math.sin(theta)

  def displacement_of(rx, ry):
    return (cos_t * rx - sin_t * ry) - rx, (sin_t * rx + cos_t * ry) - ry

  return _move_edges_vertex_consistent(topology, selector, displacement_of)


def scale_edges_vertex_consistent(topology, selector: str, sf: float):
  """Scale a class of edges gap-free; see `_move_edges_vertex_consistent`.

  Args:
    topology: the Topology to edit; not mutated.
    selector: the edge-class labels to scale.
    sf: the factor, as the library's `scale_edge` takes it -- each
      endpoint moves (sf - 1) of its distance from the edge midpoint.

  Returns:
    A new Topology carrying the scaled unit.
  """
  def displacement_of(rx, ry):
    return (sf - 1.0) * rx, (sf - 1.0) * ry

  return _move_edges_vertex_consistent(topology, selector, displacement_of)


def move_as_applied(topology, selector, how, ready):
  """Perform the manipulation a COMMIT would perform, whoever is asking.

  Args:
    topology: the Topology the edit is aimed with.
    selector: the class labels, as the library's own selector string.
    how: the manipulation's key.
    ready: its arguments ALREADY in map units -- callers holding a
      record's own fractions pass them through `in_map_units` and
      `whole_where_needed` first, exactly as `apply` does.

  Returns:
    Whatever the manipulation returns, which is the same shape
    `transform_geometry` gives back, so a caller may chain it.

  WHY THIS IS A FUNCTION AND NOT THREE LINES INSIDE `apply`. Rotate and
  scale are REFORMULATED here to move each shared vertex once rather
  than each edge about its own midpoint, because the library's per-edge
  versions tear the tiling (C-341). That reformulation was written into
  `apply` alone, and it has three callers who must agree with it: the
  drop, the drag PREVIEW, and `lays_out`, which is the predicate every
  ceiling is found with. Measured 2026-09-07 on `laves 3.3.4.3.4` class
  `a`: the per-edge route leaves 1.78% of a fundamental cell open at 15
  degrees and raises outright at 60, where the committed route is
  gap-free at both -- so a person dragging a rotate was shown a torn
  design, told in red that it could not be tiled, and would have been
  given a perfect tiling had they let go. One owner is the only thing
  that stops the three drifting apart again; when a reformulation
  reroutes a library call, its callers are the door list.
  """
  if how == "rotate_edge":
    return rotate_edges_vertex_consistent(
      topology, selector, ready.get("angle", 0.0))
  if how == "scale_edge":
    return scale_edges_vertex_consistent(
      topology, selector, ready.get("sf", 1.0))
  return topology.transform_geometry(True, True, selector, how, **ready)


def _expanded(selector: str, glue, target: str = "") -> str:
  """Every library label a glued class stands for.

  Args:
    selector: the labels an edit was aimed at, as the library takes
      them.
    glue: the map `glue_the_aspect_holes` returned, or None.
    target: "edge" or "vertex", saying which of the two maps to read.

  Returns:
    The selector, widened to every label whose class is one the
    selector names. Without a gluing it is returned unchanged.

  THIS IS WHAT MAKES AN EDIT CROSS A HOLE. Under the reading that glues
  a strand-width gap away, the two strands facing each other across it
  share one class, so an edit aimed at that class has to move both of
  their facing edges; aimed at the library's own label it would move
  one and leave the other, and the hole the gluing said was not there
  would open or close as a result.
  """
  if not glue or not selector:
    return selector
  which = glue.get("points" if target == "vertex" else "edges", {})
  wanted = {which.get(label, label) for label in selector}
  return "".join(sorted(label for label, klass in which.items()
                        if klass in wanted)) or selector


def apply(topology, edits, glue=None):
  """Replay an edit list onto a topology, returning what to draw.

  Args:
    topology: a freshly built Topology for the current unit.
    edits: the record, oldest first.
    glue: the label maps a reading of a weave's daylight called for, or
      None where the classes stand as the library assigned them. Where
      one is given, an edit aimed at a glued class is applied to EVERY
      library label that class stands for, which is what makes an edit
      reach both sides of a hole.


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

  (D-35.)
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
    # A GLUED CLASS STANDS FOR SEVERAL OF THE LIBRARY'S LABELS, and
    # unless it is expanded the edit reaches one side of a hole and not
    # the other -- which is precisely the adjacency the gluing was
    # asserting. The library's own selector is a string of labels, so
    # the expansion is a string too.
    selector = _expanded(selector, glue, edit.get("target"))
    # NOTHING HERE ASKS WHETHER THE DESIGN STILL HAS A REBUILDABLE
    # TOPOLOGY, and that is the point of chaining: the object carries
    # its own classes forward, so an edit after one that opened gaps is
    # aimed with the labels it was always aimed with. The guard that
    # stood here refused exactly that case.
    if current is None:
      refusals.append(
        f"{MANIPULATIONS[how]['label']} on {selector} could not be applied, "
        f"because there has been no topology successfully calculated.")
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
    # THE CLASSES MAY HAVE MOVED SINCE THE EDIT WAS MADE, and the edit
    # is applied anyway to whatever its labels name now -- but it SAYS
    # so. A scale in one axis turns the default design's two edge
    # classes into four (measured by the specification hunt of
    # 2026-09-02), so `a` then names a quarter of what it did while
    # the change list reads the same. An older record with no
    # alphabet says nothing, which is the honest answer for it.
    against = edit.get("against") or ""
    if against and against != available:
      refusals.append(CLASSES_MOVED.format(
        label=MANIPULATIONS[how]["label"], selector=selector,
        target=target, against=against, now=available or "none"))
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
      # ROTATE AND SCALE ARE REFORMULATED to move shared vertices once
      # rather than each edge about its own midpoint, so the tiling
      # stays edge-to-edge where the library's per-edge versions tear it
      # (see _move_edges_vertex_consistent). Every other manipulation
      # goes to the library unchanged.
      moved = move_as_applied(current, selector, how, args)
    except Exception:                                 # noqa: BLE001
      # A MANIPULATION CAN FAIL BY RAISING AS WELL AS BY PRODUCING
      # SOMETHING UNTILEABLE, and the two arrive here separately. The
      # clamp below has to be reachable from BOTH: measured on `laves
      # 3.3.4.3.4`, a zigzag at h=2.0 on class `a` RAISES inside the
      # library rather than coming back undrawable, so a clamp written
      # only against the second route fires on neither.
      moved = None
    drawable = None
    if moved is not None:
      drawable, _repaired = _make_drawable(moved.tileable)
    if drawable is None and how == "zigzag_edge":
      # CLAMP RATHER THAN REFUSE. A zigzag too deep for its neighbours
      # used to be dropped whole with "a smaller value often works",
      # which costs the person the gesture and leaves them to find the
      # limit by bisecting it themselves. The largest amplitude that
      # lays out is a question we can ask, so the edit is applied AT
      # that amplitude and the reduction is said.
      # THE RECORD IS NOT REWRITTEN, and that is the whole of why this
      # is safe to do at replay. The ceiling moves as other edits move
      # the neighbouring geometry, so a clamp written back into the
      # record would shave the number a little further on every replay
      # and never give it back -- a ratchet, silently eroding what
      # somebody typed. Holding the asked-for value and clamping on the
      # way to the screen is idempotent instead: the same design always
      # draws the same wave, and a design that regains room draws the
      # full one again. It is the shape of a kept scheme being held
      # rather than owned.
      # PAID FOR ONLY WHERE THE EDIT WOULD OTHERWISE BE LOST: the
      # search costs up to about 1.4s on `laves 3.3.4.3.4`, and it runs
      # only on the branch that today produces nothing at all.
      ceiling = zigzag_ceiling(current, selector, edit.get("args") or {})
      asked = float((edit.get("args") or {}).get("h", 0.0) or 0.0)
      if ceiling > 0.0 and ceiling < asked:
        try:
          clamped = in_map_units(
            whole_where_needed({**(edit.get("args") or {}), "h": ceiling}),
            current.tileable)
          moved = current.transform_geometry(
            True, True, selector, how, **clamped)
          drawable, _repaired = _make_drawable(moved.tileable)
        except Exception:                               # noqa: BLE001
          drawable = None
        if drawable is not None:
          refusals.append(ZIGZAG_CLAMPED.format(
            selector=selector or "this design",
            asked=_three_figures(asked / 2.0),
            drawn=_three_figures(ceiling / 2.0)))
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
      if how in ("rotate_edge", "scale_edge"):
        # A VERTEX-CONSISTENT ROTATE OR SCALE MOVES NOTHING EXACTLY WHERE
        # NO GAP-FREE ONE EXISTS: to keep the tiling the shared vertices
        # take a single lattice-periodic displacement, and the design's
        # symmetry can force that to zero -- the same obstruction that
        # makes push_vertex cancel at a symmetric vertex. Say which,
        # rather than the generic sentence, so a person meeting a control
        # that does nothing learns it is the design and not a fault.
        verb = "turn" if how == "rotate_edge" else "stretch"
        refusals.append(
          f"{MANIPULATIONS[how]['label']} on {selector or 'this design'} "
          f"leaves it unchanged: the design's symmetry gives these edges "
          f"nowhere to {verb} while its tiles still meet.")
      else:
        refusals.append(
          f"{MANIPULATIONS[how]['label']} on {selector or 'this design'} "
          f"changed nothing about it, so the design is as it was.")
    tileable = drawable
    # COVERAGE-BASED VALIDITY, not gaps(): a tear where the units pull
    # apart, leaving a gap open onto the surrounding space rather than a
    # hole enclosed within one, reads as sound to gaps(); the mark reads
    # plane_coverage, which measures a whole fundamental cell and catches
    # gaps and overlaps alike.
    gap_ratio, overlap_ratio, _where = plane_coverage(drawable)
    marks.append({"applied": True, "gap": gap_ratio,
                  "overlap": overlap_ratio,
                  "sound": gap_ratio < GAP_TOLERANCE
                  and overlap_ratio < GAP_TOLERANCE})
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


def daylight_by_kind(unit, spec, spacing: float, aspect: float) -> dict:
  """Tell a weave's two kinds of daylight apart, using its strands code.

  Args:
    unit: the WeaveUnit as built, at the strand width in force.
    spec: its catalogue entry, which carries `strands` and `weave_type`.
    spacing: the spacing the unit was built at.
    aspect: the strand width the unit was built at.

  Returns:
    ``{"width": geometry, "conscious": geometry}`` -- the daylight that
    strand WIDTH opens, and the ground a HYPHEN in the strands code
    leaves deliberately empty. Either may be an empty geometry, and a
    code with no hyphen always makes `conscious` empty.

  WHY BOTH ARE NEEDED AT ONCE. Scaffolding a weave means filling its
  daylight so a topology can be built at all, and a topology needs the
  design GAP-FREE -- so the conscious gap has to be filled too, or
  there is no topology to reprocess. What the two must not share is
  MEANING: strands either side of width-daylight are the same fabric
  and an edit may travel across it, while a hyphen is a strand the
  person deliberately left out and nothing should connect through it.
  (Maintainer's construction, 2026-09-08; C-347.)

  IT ASKS THE LIBRARY RATHER THAN REIMPLEMENTING THE GRID. The same
  weave is built with each hyphen replaced by an unused letter, and
  the ground that ghost carries and the real one does not IS the
  conscious gap, exactly. Reconstructing the strand bands here would
  duplicate `_get_cell_strands`, whose widths, expansions and
  over-under differencing are the library's business.

  AND THE ASPECT TRICK DOES NOT WORK, which is why this is not that:
  a hyphen weave built at aspect 1.0 has gap 0.000000 and OVERLAP
  0.125000, the neighbouring strands having grown across the empty
  slot, so subtracting the solid design's gaps isolates nothing.
  """
  import shapely
  from . import catalog
  code = str(spec.get("strands", ""))
  gap = plane_coverage(unit)[2]
  empty = shapely.Polygon()
  daylight = gap if gap is not None else empty
  if "-" not in code:
    return {"width": daylight, "conscious": empty}
  used = set(catalog.elements_in_strands(code))
  spare = [c for c in "zyxwvutsrq" if c not in used]
  if len(spare) < code.count("-"):
    return {"width": daylight, "conscious": empty}
  ghost_code = "".join(spare.pop(0) if ch == "-" else ch for ch in code)
  try:
    ghost = catalog.make_unit(spec, spacing=spacing, crs=None,
                              aspect=aspect, strands=ghost_code)
  except Exception:                                   # noqa: BLE001
    return {"width": daylight, "conscious": empty}
  real_ground = shapely.union_all(list(unit.tiles.geometry))
  ghost_ground = shapely.union_all(list(ghost.tiles.geometry))
  # THE TWO HALVES MUST BE IN THE SAME FRAME, and until 2026-09-08 they
  # were not: `width` comes from `plane_coverage`, which measures ONE
  # fundamental cell, while the ghost difference is a region of the
  # plane built from tile geometry that overhangs the cell, since a
  # weave's strand pieces are longer along their axis than the cell is.
  # Unclipped, the two summed to 0.246 of a cell against a gap of 0.055
  # on `twill weave a|b-`, so filling both double-covers the ground and
  # the design that reaches `Topology` overlaps its own translates.
  # Clipped to the design's own gap they partition it exactly, measured
  # on five weaves at four aspects each; a code with no hyphen is
  # unaffected, its conscious gap being empty either way. (C-351.)
  conscious = ghost_ground.difference(real_ground).intersection(daylight)
  return {"width": daylight.difference(conscious.buffer(_A_WHISKER)),
          "conscious": conscious}


_A_WHISKER = 1e-6
"""How far a boolean difference may miss by and still mean the same thing.

Small enough not to move a boundary anybody can see, large enough that
two coordinates the same to a millionth are treated as one -- which is
what a difference of two independently built unions needs.
"""


def plane_coverage(unit):
  """Whether a unit tiles the plane cleanly -- no gaps AND no overlaps.

  Args:
    unit: a Tileable.

  Returns:
    (gap_ratio, overlap_ratio, missing) -- the fraction of one
    fundamental cell left UNCOVERED, the fraction covered TWICE, and the
    uncovered ground itself so it can be drawn. (0.0, 0.0, None) where
    the question cannot be asked.

  WHY THIS EXISTS BESIDE `gaps()`. `gaps()` finds HOLES enclosed within
  the patch's union, and a tear does not always make a hole: the
  library's per-edge `rotate_edge` pulls whole units APART, leaving a gap
  that opens onto the surrounding space rather than an interior ring --
  so `gaps()` reported a rotate of hex-slice 3 as sound while its units
  had visibly separated (measured 2026-09-07; it is the same blind spot
  the `gaps()` docstring already names for an inset's open slots). A
  validity mark that misses that is a false green in the one place this
  tab most needs the truth.

  HOW IT CATCHES BOTH. It lays a patch two rings deep, takes ONE
  fundamental cell -- the parallelogram of the two shortest independent
  lattice vectors -- centred well inside the patch, and asks how much of
  THAT KNOWN AREA the tiles actually cover. A gap-free tiling covers any
  interior cell entirely, whatever shape the tear is; a gap that opens
  onto the surrounding space leaves the cell short exactly as an enclosed
  hole does. The overlap is the summed tile
  area within the cell minus the union's, which a mere union can never
  reveal. Placement need not align to the tiles: a tiling covers every
  translate of a cell, so any cell fully inside the patch answers.
  """
  # IMPORTED AT THE POINT OF USE, as everything geometric here is.
  import shapely
  from shapely.geometry import Polygon
  try:
    vectors = getattr(unit, "vectors", None) or {}
    candidates = sorted(
      (tuple(float(c) for c in v) for v in vectors.values()),
      key=lambda v: v[0] * v[0] + v[1] * v[1])
    first = second = None
    for candidate in candidates:
      if candidate[0] * candidate[0] + candidate[1] * candidate[1] < 1e-18:
        continue
      if first is None:
        first = candidate
        continue
      if abs(first[0] * candidate[1] - first[1] * candidate[0]) > 1e-9:
        second = candidate
        break
    if second is None:
      return 0.0, 0.0, None
    patch = unit.get_local_patch(r=2, include_0=True)
    tiles = _one_tile_per_piece_of_ground(list(patch.geometry))
    covered = shapely.union_all(tiles)
    centre = covered.centroid
    ox = centre.x - (first[0] + second[0]) / 2
    oy = centre.y - (first[1] + second[1]) / 2
    cell = Polygon([
      (ox, oy),
      (ox + first[0], oy + first[1]),
      (ox + first[0] + second[0], oy + first[1] + second[1]),
      (ox + second[0], oy + second[1])])
    cell_area = cell.area
    if cell_area <= 0:
      return 0.0, 0.0, None
    inside = covered.intersection(cell)
    gap_ratio = max(0.0, 1.0 - inside.area / cell_area)
    summed = 0.0
    for tile in tiles:
      part = tile.intersection(cell)
      if not part.is_empty:
        summed += part.area
    overlap_ratio = max(0.0, (summed - inside.area) / cell_area)
    missing = cell.difference(covered)
    if missing.is_empty or gap_ratio < GAP_TOLERANCE:
      missing = None
    return gap_ratio, overlap_ratio, missing
  except Exception:                                   # noqa: BLE001
    return 0.0, 0.0, None


# HOW WIDE A PATCH `tears_in_the_patch` MAY LAY. It starts at the
# smallest that has ever sufficed and grows until the block of cells
# it measures fits inside; the ceiling is there because a design that
# never fits should draw no hatch rather than lay patches for ever.
# Measured 2026-09-07: `laves 3.3.4.3.4` and `archimedean 4.8.8` fit
# at 2, `hex-slice 3` and `square-colouring 3` at 3, and the four
# `chavey` designs at 5 -- though chavey and hex-slice share a
# lattice, a cell and a block, which is why this is asked rather than
# computed.
_LEAST_PATCH = 2
_MOST_PATCH = 7


def _outline_of(covered):
  """The ground a patch is responsible for, holes filled in.

  Args:
    covered: the union of a patch's tiles.

  Returns:
    The same shape with every interior ring closed, so a tear inside
    it stays visible as a difference while ground beyond it does not.

  WHY IT IS NOT A CONVEX HULL. That was the first version of this
  measure and it reported 1,000,000 units of tear on an untouched
  design, because a patch's outer edge is ragged and a hull does not
  follow it. An outline follows it exactly: it is the patch's own
  boundary, and the only thing removed is the holes -- which are what
  a tear IS.
  """
  # IMPORTED AT THE POINT OF USE, as everything geometric here is.
  import shapely
  from shapely.geometry import Polygon
  parts = getattr(covered, "geoms", None) or [covered]
  filled = [Polygon(part.exterior) for part in parts
            if getattr(part, "exterior", None) is not None]
  return shapely.union_all(filled) if filled else covered


# THE TWO READINGS OF A WEAVE'S DAYLIGHT, and the switch between them
# (maintainer's instruction, 2026-09-08). A weave below full width has
# empty ground from three causes -- the strand width, a hyphen in the
# strands code, and any inset -- and which of them a STRUCTURE may see
# is a principle rather than a fact. Each cause removes cloth
# monotonically, so a reading is applied by REBUILDING with the causes
# it disregards set to their neutral values, never by labelling a
# region with the cause that opened it: one aperture mixes provenance,
# and "opened by the hyphen" is itself ambiguous between the band a
# hyphen opens at full width and the extra it opens at a given width.
# The discussion is docs/process/the-topology-of-a-weave-and-its-holes.md.
# NAMED FOR WHAT THE GAP IS BEING LIKENED TO, not for what it becomes.
# The decision is which of the other two absences a strand-width gap
# resembles: a dropped strand, which every reading counts, or an inset,
# which no reading counts. Calling the two readings "holes" and
# "styling" named the consequence and hid the comparison, which is the
# whole of the question (maintainer's correction, 2026-09-08).
ASPECT_LIKE_A_DROP = "like-a-drop"
ASPECT_LIKE_AN_INSET = "like-an-inset"
ASPECT_READINGS = (ASPECT_LIKE_A_DROP, ASPECT_LIKE_AN_INSET)

# WHETHER ONE CLASS MAY HOLD BOTH STRAND FAMILIES, which is a second
# and INDEPENDENT question from the one above; the construction is at
# `keep_warp_and_weft_apart`.
WARP_AND_WEFT_TOGETHER = "together"
WARP_AND_WEFT_APART = "apart"
STRAND_FAMILIES = (WARP_AND_WEFT_TOGETHER, WARP_AND_WEFT_APART)

# JUST BELOW ONE RATHER THAN AT IT: at exactly 1.0 the library's
# assembly dissolves adjacent pieces that share a label, so a twill's
# sixteen tiles become two and the design stops being the same design.
# Measured in the report; 0.999 keeps every piece and leaves a
# millionth of a cell of daylight, which the scaffolding fills.
FULL_WIDTH = 0.999


def _pieces_of(geometry, floor: float = 1.0) -> list:
  """A geometry's polygonal parts, slivers under `floor` dropped.

  Args:
    geometry: any shapely geometry, or None.
    floor: the smallest area to keep, in squared map units.

  Returns:
    A list of Polygons.

  EVERY FILLER PIECE IS TAKEN SEPARATELY because
  `_setup_regularised_prototile` dissolves tiles by `tile_id` and
  `Topology` reads corners through `shape.exterior`, which a
  MultiPolygon has not: a merged filler left two weaves of three
  refusing and read as a fact about weaves (C-347).
  """
  import shapely  # noqa: F401
  if geometry is None or geometry.is_empty:
    return []
  return [g for g in getattr(geometry, "geoms", [geometry])
          if g.geom_type == "Polygon" and not g.is_empty and g.area > floor]


def _closed_up(strands: list, gap: float) -> list:
  """Grow every strand piece until the pieces abut, without merging them.

  Args:
    strands: the strand polygons.
    gap: the residual daylight to close, as a fraction of a cell.

  Returns:
    A new list of polygons, one per input, each grown by half the
    hairline that separated it from its neighbours.

  ABUT, NOT MERGE, which is the whole difficulty. Unioning a piece
  with the daylight beside it was tried and it FUSED same-direction
  neighbours -- a plain weave's four strands became two, which is the
  library's own behaviour at an aspect of exactly 1.0 arriving by
  another door and losing the very pieces the structure is about. A
  mitred buffer grows each piece in place, so they meet and stay
  distinct; the corners overlap by the square of the buffer, which is
  a millionth of a cell at the widths this is used at and is checked
  by the caller rather than assumed.
  """
  if gap <= 0:
    return list(strands)
  return [strand.buffer(gap / 2.0, join_style="mitre", cap_style="square")
          for strand in strands]


def _snapped_pieces(geometry, floor: float = 1.0) -> list:
  """Filler pieces already snapped to the grid the library snaps to.

  Args:
    geometry: the daylight to cut into filler.
    floor: the smallest piece to keep, in squared map units.

  Returns:
    A list of Polygons, each of which survives `tiling_utils.gridify`
    unchanged, with anything that gridding splits handed back as
    separate pieces.

  A WORKAROUND FOR UPSTREAM, AT THE NARROWEST POINT. `get_clean_polygon`
  ends in `gridify`, which is `shapely.set_precision` at 1e-06, and a
  polygon that pinches at that scale comes back as a MULTIPOLYGON;
  `get_corners` then asks the result for `.exterior`, which a
  MultiPolygon has not, and the build raises. Measured 2026-09-08 on
  the three cube weaves at aspect 0.75: 3, 11 and 13 filler pieces of
  68, 65 and 21 stop being a single polygon under the library's own
  gridify.

  IT CORRECTS THE INPUT RATHER THAN REPLACING THE BEHAVIOUR, which is
  this project's rule for somebody else's defect: the filler is ours to
  shape, gridding it here makes the library's own gridding idempotent
  on it, and every piece the grid splits becomes its own tile, which
  the scaffolding wants anyway since `_setup_regularised_prototile`
  dissolves by `tile_id`.

  WHEN IT CAN GO: when `get_clean_polygon` returns the largest part, or
  `get_corners` takes a MultiPolygon. `test_upstream_still_splits_a_
  pinched_polygon_when_gridding` asserts the defect with the plugin out
  of the way, so its failure is the news that this can be deleted.
  """
  import weavingspace.tiling_utils as tiling_utils
  out = []
  for piece in _pieces_of(geometry, floor):
    try:
      snapped = tiling_utils.gridify(piece)
    except Exception:                                 # noqa: BLE001
      # A PIECE THE GRID WILL NOT TAKE AT ALL is dropped rather than
      # passed on: handing it over is the raise this exists to avoid,
      # and the caller's coverage check is what notices if dropping it
      # leaves a gap.
      continue
    out.extend(_pieces_of(snapped, floor))
  return out


def scaffolded_weave(spec, spacing: float, aspect: float, crs=None,
                     strands=None, reading: str = ASPECT_LIKE_A_DROP):
  """A gap-free stand-in for a weave, and what each of its tiles is.

  Args:
    spec: the catalogue entry for the weave.
    spacing: the strand-to-strand distance the design is built at.
    aspect: the strand width the USER chose, as a fraction of spacing.
    crs: passed to `catalog.make_unit`; None for a bare unit.
    strands: a typed strands code overriding the entry's own, or None.
    reading: `ASPECT_LIKE_A_DROP`, where the daylight a narrow strand
      leaves is filled and kept as part of the structure, or
      `ASPECT_LIKE_AN_INSET`, where the strand width is neutralised by
      rebuilding at full width and only a hyphen's ground is kept.

  Returns:
    `(unit, kinds, note)`. `unit` is a Tileable covering the plane, or
    None where one could not be made; `kinds` maps every tile_id to
    "strand", "aspect" or "dropped"; `note` is empty on success and
    otherwise says what refused, in the terms of a control.

  WHY BOTH READINGS STILL FILL. `Topology` needs a gap-free tiling, so
  a hole cannot BE a hole in the structure: it has to be a tile. What
  the reading changes is which holes exist to be filled, which is why
  it is applied by rebuilding rather than by tagging.

  UNDER `ASPECT_LIKE_AN_INSET` THE GEOMETRY IS NOT THE DRAWING'S. It is
  the same weave at full width, so an edit made against it is aimed at
  a STRAND and carried back to the drawn pieces by name rather than by
  position: the two sets of pieces do not correspond geometrically,
  measured as a bijection on the plain weaves alone and on neither
  twill nor the basket, where several thin pieces fall inside one
  full-width piece.
  """
  import shapely
  import geopandas as gpd
  from . import catalog
  if reading not in ASPECT_READINGS:
    return None, {}, f"unknown reading {reading!r}"
  # BOTH READINGS SCAFFOLD THE DESIGN AS DRAWN. Reading B used to
  # rebuild at full width, which fought the library twice over: at
  # exactly 1.0 it fuses same-label pieces, just below it leaves a
  # hairline that upstream's cleaner reduces below four corners, and
  # closing the hairline by growing the strands fuses them again. The
  # maintainer's construction (2026-09-08) does it in the STRUCTURE
  # instead, gluing each aspect hole's opposite sides and identifying
  # its four corners, so no geometry moves and none of that arises.
  built_at = aspect
  try:
    unit = catalog.make_unit(spec, spacing=spacing, crs=crs,
                             aspect=built_at, strands=strands)
  except Exception as exc:                            # noqa: BLE001
    return None, {}, f"the weave could not be built: {exc}"
  strand_tiles = [(g, str(i)) for g, i in
                  zip(unit.tiles.geometry, unit.tiles["tile_id"])
                  if g.geom_type == "Polygon"]
  if not strand_tiles:
    return None, {}, "the weave has no strands to build from"
  kinds = {}
  geometries, ids = [], []
  for geometry, tile_id in strand_tiles:
    geometries.append(geometry)
    ids.append(tile_id)
    kinds[tile_id] = "strand"
  daylight = daylight_by_kind(unit, spec, spacing, built_at)
  filler = [("dropped", piece)
            for piece in _snapped_pieces(daylight["conscious"])]
  filler += [("aspect", piece)
             for piece in _snapped_pieces(daylight["width"])]
  for index, (kind, piece) in enumerate(filler):
    tile_id = f"{'d' if kind == 'dropped' else 'w'}{index}"
    geometries.append(piece)
    ids.append(tile_id)
    kinds[tile_id] = kind
  frame = gpd.GeoDataFrame({"tile_id": ids}, geometry=geometries,
                           crs=unit.tiles.crs)
  filled = _shallow_copy_with_tiles(unit, frame)
  if filled is None:
    return None, kinds, "the library would not rebuild the unit from " \
                        "the scaffolded tiles"
  gap, overlap, _left = plane_coverage(filled)
  if gap > 1e-6 or overlap > 1e-6:
    return None, kinds, (f"the scaffolding leaves a gap of {gap:.6f} and an "
                         f"overlap of {overlap:.6f} of a cell, so it is not "
                         f"a tiling")
  return filled, kinds, ""


def weave_topology(spec, spacing: float, aspect: float, crs=None,
                   strands=None, reading: str = ASPECT_LIKE_A_DROP,
                   families: str = WARP_AND_WEFT_TOGETHER):
  """The topology of a weave under one reading of its daylight.

  Args:
    spec: the catalogue entry for the weave.
    spacing: the strand-to-strand distance.
    aspect: the strand width the user chose.
    crs: passed through to the unit's construction.
    strands: a typed strands code, or None for the entry's own.
    reading: which daylight the structure may see; see
      `scaffolded_weave`.
    families: `WARP_AND_WEFT_APART` to split every class that holds
      edges of both strand directions, or `WARP_AND_WEFT_TOGETHER` for
      the classes the library assigns.

  Returns:
    `(topology, unit, kinds, glue, note)`. The topology is None where
    one could not be built and `note` then says why in the terms of a
    control rather than of the library. `glue` is None under
    `ASPECT_LIKE_A_DROP` and otherwise carries the label maps that
    collapse each strand-width hole away, which is what makes the two
    readings differ at all.

  THE FILLER IS DROPPED BY THE CALLER, not here: an edit is applied to
  the scaffolded unit and the strands are recovered afterwards by
  asking `kinds`, which is the shape ruling 1 of C-347 sets out.

  THE TWO QUESTIONS ARE SEPARATE AND ARE ANSWERED IN ORDER. Splitting
  warp from weft is a refinement of the classes and gluing an aspect
  hole away is a merge of them, so the refinement runs FIRST and the
  gluing then reads whatever labels are in force -- which is right
  rather than merely convenient, since the two sides of an aspect hole
  face each other along one direction and a gluing therefore never
  crosses the split.
  """
  filled, kinds, note = scaffolded_weave(
    spec, spacing, aspect, crs=crs, strands=strands, reading=reading)
  if filled is None:
    return None, None, kinds, None, note
  try:
    topology = _topology_class()(filled, True)
  except Exception as exc:                            # noqa: BLE001
    return None, filled, kinds, None, _why_not(exc, filled)
  if families == WARP_AND_WEFT_APART:
    keep_warp_and_weft_apart(topology, kinds)
  # THE READING IS APPLIED HERE OR IT IS APPLIED NOWHERE. Both readings
  # scaffold identically, since the difference is a quotient of the
  # structure rather than a change to the geometry, so a caller that
  # merely PASSED a reading and never glued would get the same answer
  # for both and no sign of it. The one entry point that names the
  # reading is the one that has to honour it.
  glue = (glue_the_aspect_holes(topology, kinds)
          if reading == ASPECT_LIKE_AN_INSET else None)
  return topology, filled, kinds, glue, ""


def _find(parent: dict, label: str) -> str:
  """The representative of a label's class, with the path shortened.

  Args:
    parent: the union-find map, mutated in place.
    label: the label to look up.

  Returns:
    The class representative.
  """
  root = label
  while parent.get(root, root) != root:
    root = parent[root]
  while parent.get(label, label) != label:
    parent[label], label = root, parent[label]
  return root


def _union(parent: dict, one: str, two: str) -> None:
  """Put two labels in one class.

  Args:
    parent: the union-find map, mutated in place.
    one, two: the labels to join.

  Returns:
    None.
  """
  a, b = _find(parent, one), _find(parent, two)
  if a != b:
    parent[max(a, b)] = min(a, b)


def glue_the_aspect_holes(topology, kinds: dict) -> dict:
  """Treat each aspect hole as if its opposite sides touched.

  Args:
    topology: a `Topology` built from a scaffolded weave.
    kinds: the map `scaffolded_weave` returned, tile_id to kind.

  Returns:
    A dict with `edges` and `points`, each mapping a label to the class
    it belongs to once the gluing is done, and `before`/`after` counts.

  THE MAINTAINER'S CONSTRUCTION (2026-09-08). A rectangular hole the
  strand width opened should be read as though the strands on opposite
  sides of it were touching, which is two adjacencies rather than four
  independent edges, and its four corners are then one point. So the
  hole is quotiented out of the STRUCTURE while the drawing keeps it.

  NOTHING GEOMETRIC HAPPENS HERE, and that is the point. Neutralising
  the strand width by rebuilding the design at full width was tried
  first and fails three ways: the library fuses same-label pieces at
  exactly 1.0, leaves a hairline just below it that upstream's cleaner
  cannot make a polygon of, and fuses them again if the hairline is
  closed by growing the strands. A quotient touches none of that.

  A HOLE THAT IS NOT FOUR-SIDED IS LEFT ALONE, since "opposite sides"
  names nothing there, and a dropped strand's ground is never glued
  under either reading: a hyphen is a strand somebody left out, and
  what it opens is a hole in both readings.
  """
  by_id = {}
  for tile in topology.tiles:
    by_id.setdefault(getattr(tile, "base_ID", None), []).append(tile)
  edge_parent, point_parent = {}, {}
  # COUNTED BY BASE TILE, not by tile: `topology.tiles` holds every
  # copy in the patch, so a design with nine holes reported eighty-one
  # of them glued. The union operations are idempotent, so only the
  # count was wrong, which is exactly the kind of figure somebody
  # quotes later.
  glued = set()
  for tile in topology.tiles:
    if kinds.get(_tile_id_of(tile, topology)) != "aspect":
      continue
    edges = [topology.edges[e] for e in getattr(tile, "edges", [])
             if e in topology.edges]
    labels = [getattr(e, "label", "") for e in edges]
    if len(labels) != 4 or not all(labels):
      continue
    _union(edge_parent, labels[0], labels[2])
    _union(edge_parent, labels[1], labels[3])
    corners = [topology.points[c] for c in getattr(tile, "corners", [])
               if c in topology.points]
    names = [getattr(v, "label", "") for v in corners if getattr(v, "label", "")]
    for other in names[1:]:
      _union(point_parent, names[0], other)
    glued.add(getattr(tile, "base_ID", id(tile)))
  edges_before = {getattr(e, "label", "") for e in topology.edges.values()
                  if getattr(e, "label", "")}
  points_before = {getattr(v, "label", "") for v in topology.points.values()
                   if getattr(v, "label", "")}
  edge_map = {label: _find(edge_parent, label) for label in edges_before}
  point_map = {label: _find(point_parent, label) for label in points_before}
  return {"edges": edge_map, "points": point_map, "glued": len(glued),
          "before": (len(edges_before), len(points_before)),
          "after": (len(set(edge_map.values())),
                    len(set(point_map.values())))}


# ---------------------------------------------------------------------
# WARP AND WEFT: A SECOND AND INDEPENDENT READING OF THE SAME STRUCTURE
#
# The library takes its classes as orbits under the design's FULL
# symmetry group. A weave's drawing generally admits a mirror carrying
# warps onto wefts, so one class holds edges of both directions -- 81
# vertical against 80 horizontal on one twill class. A CLOTH HAS NO
# SUCH SYMMETRY: warp and weft differ physically whatever the picture
# does, so that mirror is a symmetry of the picture and never of the
# weave (the maintainer's question, 2026-09-11; C-353).
#
# It is INDEPENDENT of the aspect-gap reading and is applied first, so
# a gluing runs on whatever labels are in force.

# Upstream's own test for "the same element under a transform" is a
# centroid distance of ten times `tiling_utils.RESOLUTION`, and the
# refinement matches elements exactly as `_find_edge_transitivity_classes`
# does or it would be measuring something else.
SAME_PLACE = 10 * 1e-6


def _long_axis(polygon):
  """The direction of a tile's longer side.

  Args:
    polygon: a tile's shape.

  Returns:
    An (dx, dy) pair along the longest side of the minimum rotated
    rectangle, or None where the shape has no usable rectangle.

  A STRAND PIECE IS LONGER ALONG ITS OWN AXIS than across it, which is
  what keeps ribbons continuous across cells (C-347), so the long side
  of the bounding rectangle IS the strand's direction. Reading it off
  the geometry rather than off the spec means a rotated family and a
  triaxial one need no special case.
  """
  try:
    corners = list(polygon.minimum_rotated_rectangle.exterior.coords)[:4]
  except Exception:                                   # noqa: BLE001
    return None
  if len(corners) < 4:
    return None
  best, longest = None, -1.0
  for index in range(4):
    (x0, y0), (x1, y1) = corners[index], corners[(index + 1) % 4]
    span = math.hypot(x1 - x0, y1 - y0)
    if span > longest:
      longest, best = span, (x1 - x0, y1 - y0)
  return best


def _as_direction(dx: float, dy: float) -> float:
  """A vector's direction as an angle in degrees, modulo a half turn.

  Args:
    dx, dy: the vector's components.

  Returns:
    The angle in [0, 180), a direction and its reverse answering the
    same, since a strand has no arrowhead.
  """
  angle = math.degrees(math.atan2(dy, dx)) % 180.0
  return 0.0 if abs(angle - 180.0) < 1e-6 else angle


def _same_direction(one: float, other: float, tolerance: float = 0.5) -> bool:
  """Whether two angles name one direction.

  Args:
    one, other: angles in degrees.
    tolerance: how many degrees apart still counts as the same.

  Returns:
    True where they agree modulo a half turn.
  """
  return abs(((one - other + 90.0) % 180.0) - 90.0) < tolerance


def strand_directions(unit, kinds: dict = None) -> list:
  """The distinct directions a weave's strands run in.

  Args:
    unit: the unit the topology was built from, scaffolded or not.
    kinds: the map `scaffolded_weave` returned, so the filler is left
      out; None or empty to read every tile, which is what a weave at
      full width wants.

  Returns:
    A sorted list of angles in degrees, two for a biaxial weave and
    three for a triaxial one. An empty list where the tiles give no
    usable rectangle.
  """
  frame = getattr(unit, "tiles", None)
  if frame is None:
    return []
  found = []
  ids = frame["tile_id"].astype(str) if "tile_id" in frame else None
  for index, shape in enumerate(frame.geometry):
    if kinds and ids is not None and kinds.get(str(ids.iloc[index])) != "strand":
      continue
    axis = _long_axis(shape)
    if axis is None:
      continue
    angle = _as_direction(axis[0], axis[1])
    if not any(_same_direction(angle, other) for other in found):
      found.append(angle)
  return sorted(found)


def _carries_every_direction(matrix, directions: list) -> bool:
  """Whether a transform leaves each strand direction where it is.

  Args:
    matrix: a shapely affine 6-tuple.
    directions: the angles `strand_directions` found.

  Returns:
    True where every direction maps to itself, which is what makes the
    transform a member of the direction-preserving subgroup. A
    transform sending a direction to one that is not in the list at
    all answers False, since it does not act on the families we are
    keeping apart.
  """
  a, b, c, d = matrix[0], matrix[1], matrix[2], matrix[3]
  for angle in directions:
    ux, uy = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    if not _same_direction(_as_direction(a * ux + b * uy, c * ux + d * uy),
                           angle):
      return False
  return True


def _composed(one, two):
  """The transform that applies `one` and then `two`.

  Args:
    one, two: shapely affine 6-tuples.

  Returns:
    Their composition, as a 6-tuple.
  """
  a1, b1, c1, d1, e1, f1 = one
  a2, b2, c2, d2, e2, f2 = two
  return (a2 * a1 + b2 * c1, a2 * b1 + b2 * d1,
          c2 * a1 + d2 * c1, c2 * b1 + d2 * d1,
          a2 * e1 + b2 * f1 + e2, c2 * e1 + d2 * f1 + f2)


def _transform_pool(topology) -> list:
  """Every transform the refinement may take orbits under.

  Args:
    topology: a built Topology.

  Returns:
    A list of distinct shapely affine 6-tuples: the ones the library
    recorded, plus each pairwise composition of them.

  THE COMPOSITES ARE NOT A REFINEMENT OF THE METHOD, THEY ARE WHAT
  MAKES IT AGREE WITH THE LIBRARY. `tile_matching_transforms` is a
  list of matches rather than a closed group, and each match is a
  PARTIAL relation -- the library seeks the image among the base
  elements alone and finds nothing where it lands on a copy. Taking
  orbits under the list as it stands gives 12 edge classes on `plain
  weave a|b` where the library gives 10 and 37 on `basket weave ab|cd`
  where it gives 31; with the pairwise composites the counts are 10 and
  31 exactly, on all three weaves measured. Dropping the
  direction-swapping members of the shorter list would therefore have
  split classes for a second reason nobody asked for.

  DEDUPLICATION IS WHAT MAKES IT AFFORDABLE: `twill weave a|b` records
  47 transforms, so 2,209 products, of which 510 are distinct.
  """
  listed = []
  for transform in (getattr(topology, "tile_matching_transforms", {})
                    or {}).values():
    matrix = getattr(transform, "transform", None)
    if not matrix or len(matrix) < 6:
      continue
    listed.append(tuple(float(value) for value in matrix[:6]))
  pool = {}
  for matrix in listed:
    pool.setdefault(_transform_key(matrix), matrix)
  for one in listed:
    for two in listed:
      product = _composed(one, two)
      pool.setdefault(_transform_key(product), product)
  return list(pool.values())


def _transform_key(matrix):
  """A rounded form of a transform, for telling two of them apart.

  Args:
    matrix: a shapely affine 6-tuple.

  Returns:
    A tuple key. The linear part is rounded far finer than the offsets
    because it is made of sines and cosines near unity while the
    offsets are in map units, where a millionth of a metre is already
    below the library's own resolution.
  """
  return (tuple(round(value, 9) for value in matrix[:4])
          + tuple(round(value, 6) for value in matrix[4:6]))


def _nearest_among(points: dict, tolerance: float):
  """A lookup taking a position to the element already there.

  Args:
    points: element key to a shapely Point.
    tolerance: how close counts as the same place.

  Returns:
    A callable (x, y) -> key or None.

  IT IS BUCKETED rather than a scan, because the pool holds hundreds
  of transforms and the base elements hundreds of points: a scan is
  the product of the two and this is not.
  """
  cell = tolerance * 10.0
  buckets = {}
  for key, point in points.items():
    buckets.setdefault((round(point.x / cell), round(point.y / cell)),
                       []).append(key)

  def lookup(x: float, y: float):
    gx, gy = round(x / cell), round(y / cell)
    for dx in (-1, 0, 1):
      for dy in (-1, 0, 1):
        for key in buckets.get((gx + dx, gy + dy), ()):
          point = points[key]
          if math.hypot(point.x - x, point.y - y) <= tolerance:
            return key
    return None

  return lookup


def _orbits(points: dict, matrices: list) -> dict:
  """Which elements the given transforms carry onto one another.

  Args:
    points: element key to the shapely Point that stands for it -- an
      edge's centroid or a vertex's own position, which is what the
      library compares.
    matrices: the transforms to take orbits under.

  Returns:
    A dict of element key to the key that represents its orbit.
  """
  lookup = _nearest_among(points, SAME_PLACE)
  parent = {key: key for key in points}

  def find(key):
    while parent[key] != key:
      parent[key] = parent[parent[key]]
      key = parent[key]
    return key

  for a, b, c, d, e, f in matrices:
    for key, point in points.items():
      landed = lookup(a * point.x + b * point.y + e,
                      c * point.x + d * point.y + f)
      if landed is None:
        continue
      one, two = find(key), find(landed)
      if one != two:
        parent[max(one, two)] = min(one, two)
  return {key: find(key) for key in points}


def _partition_of(marks: dict) -> set:
  """A labelling read as the set of groups it makes.

  Args:
    marks: element key to whatever names its class.

  Returns:
    A set of frozensets, so two labellings can be compared without
    caring what the classes are called.
  """
  groups = {}
  for key, mark in marks.items():
    groups.setdefault(mark, set()).add(key)
  return {frozenset(members) for members in groups.values()}


def keep_warp_and_weft_apart(topology, kinds: dict = None) -> dict:
  """Split each class that holds edges of two strand directions.

  Args:
    topology: a built Topology, whose edge and vertex labels are
      REWRITTEN in place where the refinement applies.
    kinds: the map `scaffolded_weave` returned, or None to read every
      tile as cloth, which is what a weave at full width wants.

  Returns:
    A dict with `note` -- empty where the refinement was applied and a
    sentence where it was not -- `directions`, and `before`/`after`
    counts of edge and vertex classes.

  THE LABELS ARE REWRITTEN RATHER THAN MAPPED, and that is what makes
  this compose with everything downstream at no cost. A gluing is a
  MERGE and travels as a map from label to class; a refinement is a
  SPLIT, and no map from the library's labels can express one. Every
  consumer here and in the library reads `edge.label`, from the
  chooser through `transform_geometry`'s own `label in selector`, so
  putting the new classes in the labels means the drawing, the
  selector, the replay and the gluing all learn about them at once.

  AND THE CONTROL IS THE REASON TO TRUST IT. Taking orbits under the
  WHOLE pool must reproduce the library's own classes exactly; where it
  does not, the pool is not describing this design's symmetry and a
  refinement taken from it would be describing the pool. The function
  then changes nothing and says so, rather than shipping a partition
  that is not a refinement of the one somebody is looking at.
  (C-353.)
  """
  directions = strand_directions(getattr(topology, "tileable", None), kinds)
  before = (len(class_labels(topology)["edge"]),
            len(class_labels(topology)["vertex"]))
  if len(directions) < 2:
    return {"note": "this design has no second strand direction to keep "
                    "apart", "directions": directions,
            "before": before, "after": before}
  edges = [edge for edge in topology.edges.values()
           if getattr(edge, "label", None)]
  points = [point for point in topology.points.values()
            if getattr(point, "label", None)]
  edge_places, vertex_places = {}, {}
  for edge in edges:
    edge_places.setdefault(edge.base_ID, edge.get_geometry().centroid)
  for point in points:
    vertex_places.setdefault(point.base_ID, point.point)
  pool = _transform_pool(topology)
  library_edges = {edge.base_ID: edge.label for edge in edges}
  library_points = {point.base_ID: point.label for point in points}
  if (_partition_of(_orbits(edge_places, pool))
      != _partition_of(library_edges)
      or _partition_of(_orbits(vertex_places, pool))
      != _partition_of(library_points)):
    return {"note": "this design's symmetries do not reproduce its own "
                    "classes, so warp and weft cannot be told apart here",
            "directions": directions, "before": before, "after": before}
  kept = [matrix for matrix in pool
          if _carries_every_direction(matrix, directions)]
  _relabel(edges, _orbits(edge_places, kept), library_edges, edge_places,
           _library_labels(False))
  _relabel(points, _orbits(vertex_places, kept), library_points,
           vertex_places, _library_labels(True))
  after = (len(class_labels(topology)["edge"]),
           len(class_labels(topology)["vertex"]))
  return {"note": "", "directions": directions,
          "before": before, "after": after}


def _library_labels(upper: bool) -> list:
  """The alphabet the library labels classes with.

  Args:
    upper: True for the vertex alphabet, False for the edge one.

  Returns:
    The library's own list, so a refined design is labelled exactly as
    an unrefined one is and nothing downstream has to learn a second
    spelling.
  """
  from .vendor.weavingspace.topology import LABELS, labels
  return LABELS if upper else labels


def _relabel(elements, orbit_of: dict, was: dict, places: dict,
             alphabet: list) -> None:
  """Write a refined class onto every element that belongs to it.

  Args:
    elements: the topology's edges or points, as objects with a
      `label` and a `base_ID`.
    orbit_of: base_ID to the key representing its refined class.
    was: base_ID to the label the library gave it.
    places: base_ID to the point that stands for it.
    alphabet: the label list to draw from.

  Returns:
    None; the elements are relabelled in place.

  THE ORDER IS DETERMINISTIC AND FOLLOWS THE OLD ONE, so a class that
  did not split keeps its neighbours' company and a rebuild of the same
  design gives the same names: classes are sorted by the library label
  they came out of, and within one label by the position of their
  first member. A refinement renames every class after the first split
  whatever we do, which is what the shelf's own alphabet check is for.
  """
  order = {}
  for base, orbit in orbit_of.items():
    place = places[base]
    key = (_label_order(was[base]), round(place.x, 6), round(place.y, 6))
    if orbit not in order or key < order[orbit]:
      order[orbit] = key
  names = {orbit: alphabet[index]
           for index, orbit in enumerate(sorted(order, key=order.get))
           if index < len(alphabet)}
  for element in elements:
    name = names.get(orbit_of.get(element.base_ID))
    if name:
      element.label = name


def _tile_id_of(tile, topology) -> str:
  """The scaffolded unit's own id for a topology tile.

  Args:
    tile: a `Tile` from the topology.
    topology: the topology it belongs to.

  Returns:
    The `tile_id` string, or "" where it cannot be recovered.

  THE TOPOLOGY KEEPS THE UNIT'S ORDER for its base tiles, so the id is
  read off the frame by position rather than matched by geometry,
  which would be a second definition of the same correspondence.
  """
  index = getattr(tile, "base_ID", None)
  frame = getattr(getattr(topology, "tileable", None), "tiles", None)
  if index is None or frame is None or index >= len(frame):
    return ""
  return str(frame["tile_id"].iloc[index])


def strands_of(unit, kinds: dict):
  """The tiles of a scaffolded unit that are cloth rather than filler.

  Args:
    unit: a unit from `scaffolded_weave`, possibly after an edit.
    kinds: the map that call returned.

  Returns:
    A GeoDataFrame of the strand tiles alone, which is the design a
    person sees once the scaffolding is dropped.
  """
  keep = [tile_id in kinds and kinds[tile_id] == "strand"
          for tile_id in unit.tiles["tile_id"].astype(str)]
  return unit.tiles[keep]


def _one_tile_per_piece_of_ground(tiles):
  """Drop tiles the patch hands back twice.

  Args:
    tiles: the patch's geometries, as `get_local_patch` returns them.

  Returns:
    The same list with exact duplicates removed, keeping the first of
    each.

  WHY IT IS NEEDED. `plane_coverage`'s overlap term is the summed tile
  area inside one cell MINUS the union's, which is the only way a mere
  union can reveal two tiles on one piece of ground. That subtraction
  cannot tell two tiles apart from one tile counted twice, and
  `get_local_patch(r=2)` hands the same tile back twice on five of the
  catalogue's 1,168 designs -- `square-colouring 3` and `chavey H`,
  `I`, `J`, `K`. Measured 2026-09-07: `square-colouring 3` untouched
  read overlap 0.2222 and `still_has_a_topology` False, so every edit
  a person made on it was marked as having broken a tiling that was
  never broken, and every drag drew red. Deduplicated, it reads
  0.00000000.

  EXACT EQUALITY IS THE RIGHT TEST HERE, not a tolerance: these are
  the same tile emitted twice by the same construction, not two tiles
  that happen to coincide, and a tolerance would start merging tiles
  that genuinely overlap -- which is the thing this measure exists to
  find.
  """
  kept = []
  seen = set()
  for tile in tiles:
    try:
      key = tile.wkb
    except Exception:                                   # noqa: BLE001
      kept.append(tile)
      continue
    if key in seen:
      continue
    seen.add(key)
    kept.append(tile)
  return kept


def tears_in_the_patch(unit, across=3):
  """Every torn piece of ground in a block of interior cells.

  Args:
    unit: a Tileable, usually one an edit has just produced.
    across: how many fundamental cells wide the block is. Three gives
      nine cells; the patch is laid wide enough to hold them, which is
      asked rather than computed -- see below.

  Returns:
    A geometry of the ground the tiles fail to cover across that
    block, or None where the question cannot be asked. Empty where the
    tiling is sound.

  WHY CELLS RATHER THAN A HULL. The first version of this took the
  covered union's convex hull, eroded it by one cell and subtracted --
  and reported 1,000,000 units of "tear" on an UNTOUCHED `laves
  3.3.4.3.4`, exactly one cell's worth, because a patch's outer edge
  is ragged and a hull does not follow it. Hatching that paints a
  sound design as broken at its border. A block of whole fundamental
  cells is interior BY CONSTRUCTION, so there is no boundary to erode
  and nothing to tune: a tiling covers every translate of a cell, so
  any cell inside the patch answers, and the block simply asks more of
  them. The test that caught it asserts both halves -- a sound design
  hatches nothing, a torn one hatches more than a single cell shows.

  WHAT IT COSTS, and the earlier claim here that it was free is no
  longer true: it lays its OWN patches now, one per radius it tries,
  where it used to borrow the one `plane_coverage` lays. Measured
  2026-09-07 on designs torn by a per-edge rotate, which is the only
  case that reaches it: 9.5 ms on `laves 3.3.4.3.4`, 138 ms on
  `hex-slice 3`, 133 ms on `chavey H`. It is asked ONCE PER LANDING
  and only where the coverage figure has already said the design is
  torn, against a topology build of 0.75 to 19 seconds, so the growth
  is affordable exactly where it is needed.
  """
  import shapely
  from shapely.geometry import Polygon
  try:
    vectors = getattr(unit, "vectors", None) or {}
    candidates = sorted(
      (tuple(float(c) for c in v) for v in vectors.values()),
      key=lambda v: v[0] * v[0] + v[1] * v[1])
    first = second = None
    for candidate in candidates:
      if candidate[0] * candidate[0] + candidate[1] * candidate[1] < 1e-18:
        continue
      if first is None:
        first = candidate
        continue
      if abs(first[0] * candidate[1] - first[1] * candidate[0]) > 1e-9:
        second = candidate
        break
    if second is None:
      return None
    # THE RADIUS IS ASKED FOR, NOT CHOSEN. The block must lie inside
    # the patch, or its corners hang over ground that has no tiles at
    # all and get hatched as damage -- 144,337 units of it on a sound
    # `hex-slice 3` when the radius was 2. A radius picked by
    # measuring a few designs is a number tuned rather than derived,
    # and it was wrong again at 3: `chavey H` needs 5 while
    # `hex-slice 3` needs 3 THOUGH THE TWO SHARE A LATTICE, an
    # identical cell and an identical block, so nothing about the
    # geometry here predicts it -- how far `get_local_patch` reaches
    # is the tileable's own business.
    # SO THE PATCH IS ASKED WHETHER IT HOLDS THE BLOCK, and grows
    # until it does. The test is against the patch's OUTLINE with its
    # holes filled: a tear makes holes INSIDE that outline, and those
    # are the thing being measured, while ground beyond the outline is
    # simply where the patch stopped.
    block = None
    covered = None
    for radius in range(_LEAST_PATCH, _MOST_PATCH + 1):
      patch = unit.get_local_patch(r=radius, include_0=True)
      covered = shapely.union_all(list(patch.geometry))
      centre = covered.centroid
      half = across // 2
      cells = []
      for i in range(-half, half + 1):
        for j in range(-half, half + 1):
          ox = (centre.x - (first[0] + second[0]) / 2
                + i * first[0] + j * second[0])
          oy = (centre.y - (first[1] + second[1]) / 2
                + i * first[1] + j * second[1])
          cells.append(Polygon([
            (ox, oy),
            (ox + first[0], oy + first[1]),
            (ox + first[0] + second[0], oy + first[1] + second[1]),
            (ox + second[0], oy + second[1])]))
      block = shapely.union_all(cells)
      if block.within(_outline_of(covered)):
        break
    if block is None or covered is None:
      return None
    return block.difference(covered)
  except Exception:                                   # noqa: BLE001
    # A DESIGN THIS CANNOT BE ASKED OF DRAWS NO HATCH, which is the
    # honest answer: the mark says "there is a tear here" and has
    # nothing to say when the question will not answer.
    return None


def still_has_a_topology(unit) -> bool:
  """Whether this design's tiles still meet, and so can carry one.

  Args:
    unit: a Tileable.

  Returns:
    True where the design covers a fundamental cell with no gap and no
    overlap. This is the cheap twin of `can_build`, and it answers the
    same question: `Topology` refuses a design whose tiles do not meet.
    It reads `plane_coverage` rather than `gaps()` so a tear where the
    units pull apart -- a gap open onto the surrounding space rather than
    a hole enclosed within one -- cannot pass as sound.
  """
  gap_ratio, overlap_ratio, _where = plane_coverage(unit)
  return gap_ratio < GAP_TOLERANCE and overlap_ratio < GAP_TOLERANCE


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

  (D-34.)
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


ZIGZAG_CAP = 2.0
"""The largest `h` the amplitude box can hold, peak to peak."""


def lays_out(unit_or_topology, selector, how, args):
  """Would this manipulation produce something that can be tiled?

  Args:
    unit_or_topology: the Topology an edit would be aimed with.
    selector: the class labels, as the library's own selector string.
    how: the manipulation's key.
    args: its arguments, in the RECORD's units -- this converts them
      exactly as `apply` does, so the two cannot disagree about what a
      number means.

  Returns:
    True where the result can be laid out. Asked through the same two
    steps `apply` uses -- the transform, then `_make_drawable` -- so
    this is the refusal's own question rather than a second opinion
    about it, which is what stops a ceiling that says yes where the
    edit is then refused.
  """
  current = unit_or_topology
  try:
    ready = in_map_units(whole_where_needed(dict(args or {})),
                         current.tileable)
    moved = move_as_applied(current, selector, how, ready)
    drawable, _repaired = _make_drawable(moved.tileable)
    return drawable is not None
  except Exception:                                     # noqa: BLE001
    return False


def zigzag_ceiling(topology, selector, args, cap=ZIGZAG_CAP, steps=8):
  """The largest amplitude a zigzag on these classes can be given.

  Args:
    topology: the Topology the edit is aimed with.
    selector: the edge classes it is aimed at.
    args: the zigzag's arguments; only `n` and `smoothness` are read,
      `h` being what this searches for.
    cap: the largest amplitude worth offering, the box's own maximum.
    steps: how many bisection halvings to take. Eight gives the cap
      over 256, about 0.008 at the default cap, which is finer than
      the box's own three significant figures.

  Returns:
    The largest `h` that lays out, or 0.0 where nothing does. Where the
    cap itself lays out the cap is returned unprobed, which is the
    common case and costs one probe rather than nine.

  WHY BISECTION RATHER THAN GEOMETRY. Whether a wave clears its
  neighbours is decided by the library's own layout, not by a
  formula we could write here: the amplitude, the count and the
  smoothness together decide where the crest falls, and a rule of our
  own would be a second definition of the library's answer -- which is
  this project's commonest defect. Monotone in `h`, so bisection is
  exact to its tolerance and terminates: a bigger wave that lays out
  never makes a smaller one fail.
  """
  probe = dict(args or {})
  probe["h"] = cap
  if lays_out(topology, selector, "zigzag_edge", probe):
    return cap
  low, high = 0.0, cap
  for _ in range(steps):
    middle = (low + high) / 2.0
    probe["h"] = middle
    if lays_out(topology, selector, "zigzag_edge", probe):
      low = middle
    else:
      high = middle
  return low


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

  THE `override` ARGUMENT IS ASKED FOR RATHER THAN ASSUMED.
  `TileUnit._setup_regularised_prototile` takes it and
  `WeaveUnit`'s does not, so passing it unconditionally raised
  `TypeError` on every weave and this function answered None for
  ALL of them -- which made the supplied-geometry workaround the
  dual leans on silently tiling-only, and read as a fact about
  weaves rather than about this line. Found 2026-09-08 while
  scaffolding a weave's daylight (C-347).
  """
  import copy
  import inspect
  try:
    twin = copy.deepcopy(unit)
    twin.tiles = tiles
    settle = twin._setup_regularised_prototile
    if "override" in inspect.signature(settle).parameters:
      settle(override=True)
    else:
      settle()
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
  # THE COMPLETE DUAL, for the same two reasons `dual_as_tileable` gives:
  # the file's dual table was the truncated, slivered one until
  # 2026-09-05, so a colleague opening it saw four of the default
  # design's six dual tiles.
  frame = complete_dual(topology)
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

def complete_dual(topology):
  """The dual tiling, one tile per vertex of the unit, corners consistent.

  Args:
    topology: a built Topology. Its constructor has already run
      `generate_dual`, which fills `dual_tiles` with one polygon per
      vertex class of the unit; where it has not, it is run here.

  Returns:
    A GeoDataFrame with a `tile_id` column in this project's own
    alphabet and one polygon per dual tile, carrying the source's CRS,
    or None where the library gives no dual at all.

  TWO LIBRARY DEFECTS ARE WORKED AROUND HERE, both measured 2026-09-05
  on the vendor at 6190917 and both offered upstream in
  docs/process/upstream-note-the-dual-is-truncated-and-drifts.md.
  Delete this function and use `topology.get_dual_tiles()` when
  `test_the_library_still_truncates_and_drifts_the_dual` fails.

  THE LIBRARY TRUNCATES THE DUAL TO THE SOURCE'S TILE COUNT.
  `get_dual_tiles` labels the dual's polygons with
  `list(self.tileable.tiles.tile_id)[:n]`, and a GeoDataFrame built
  from a data column of four beside six geometries has FOUR rows. A
  dual has one tile per vertex, which is `edges - faces` per unit by
  Euler, and that is more than the source's tiles on many designs:
  the default design's dual came back 4 of 6 and covered 77% of the
  ground, archimedean 4.8.8 2 of 4, hex-colouring 3 3 of 6. So the
  frame is built here from `dual_tiles` itself, which already holds
  the whole set.

  AND ITS CORNERS DRIFT BETWEEN COPIES. A dual tile's corners are the
  centres of the tiles around a vertex, and the library's centre is
  `polylabel`, a numerical search that lands about a unit apart on
  two copies of one tile. Adjacent dual tiles therefore disagreed
  about their shared edge by about a unit, leaving four slivers of
  577 units in a 250,000-unit cell -- and the library's own Topology
  could not match those corners at its 1e-6 resolution, which is why
  it refused the default design's dual while building the same
  tiling from its own catalogue. Every copy's centre is taken here as
  its BASE tile's centre translated by the copy's offset, which is
  exact by construction: measured, the coverage is then 1.000000 on
  every design tried and the library builds a Topology of all of them.
  """
  if topology is None:
    return None
  try:
    if not getattr(topology, "dual_tiles", None):
      topology.generate_dual()
    if not topology.dual_tiles:
      return None
    from shapely import geometry as geom
    polygons = []
    for vertex_id in topology.dual_tiles:
      vertex = topology.points[vertex_id]
      polygons.append(geom.Polygon(
        [_consistent_centre(topology, tile) for tile in vertex.get_tiles()]))
    import geopandas as gpd
    return gpd.GeoDataFrame(
      {"tile_id": [_letters(index) for index in range(len(polygons))]},
      geometry=gpd.GeoSeries(polygons),
      crs=getattr(getattr(topology, "tileable", None), "crs", None))
  except Exception:                                   # noqa: BLE001
    return None


def _consistent_centre(topology, tile):
  """A tile's centre, identical under translation to its base tile's.

  Args:
    topology: the Topology the tile belongs to.
    tile: any tile in its patch, a base tile or a copy.

  Returns:
    A shapely Point: the base tile's own centre moved by the copy's
    offset, read off the two shapes' centroids, which are exact linear
    functions of the coordinates and so agree to the last bit. For a
    base tile that is its own centre unchanged. See `complete_dual`
    for what this replaces and why.
  """
  from shapely import geometry as geom
  base = topology.tiles[tile.base_ID]
  centre = _exact_centre(base.shape)
  if base is tile:
    return centre
  dx = tile.shape.centroid.x - base.shape.centroid.x
  dy = tile.shape.centroid.y - base.shape.centroid.y
  return geom.Point(centre.x + dx, centre.y + dy)


def _exact_centre(shape):
  """A tile's centre, the same shape at every spacing.

  Args:
    shape: the tile's polygon.

  Returns:
    A shapely Point: the library's own choice of centre -- the
    centroid of a regular polygon, the pole of inaccessibility of any
    other, which is the incentre of the tangential tiles the Laves
    designs are made of -- found to one part in a thousand million of
    the tile's own size rather than to the library's absolute
    tolerance.

  WHY THE TOLERANCE IS RELATIVE. The library's `Tile.centre` is
  `polylabel` at its default tolerance of one map unit, so each base
  tile's centre carries noise of about half a per cent of the spacing
  -- 16 units at a spacing of 3000 -- and the noise differs between
  the four tiles of the default design. The dual's corners are those
  centres, so the dual's symmetry was whatever the noise left it, and
  it changed with the SPACING: measured 2026-09-05 through
  `dev/probes/audit_dual_centre_options.py`, the promoted dual of
  `laves 3.3.4.3.4` had three edge classes and four rotation centres
  at 3000, two rotations and four mirrors at 1000, and TEN edge
  classes with no symmetry at all at 2900 -- so an edit on class `a`
  of the dual named a different set of edges after a spacing change,
  and the tab's symmetry line described noise. At a relative
  tolerance the same probe reads two edge classes, one vertex class,
  four rotations and eight mirrors at every spacing tried, which is
  the class structure of the catalogue's own snub-square tiling, and
  every triangle comes back `D3` where the noisy centre gave `C1`.
  The centroid gives the same classes but isosceles triangles (`D1`),
  because the Cairo pentagon's centroid is not its incentre; the
  library's choice of the incentre is kept and only its precision is
  changed.
  """
  from shapely.ops import polylabel
  try:
    from weavingspace.tiling_utils import is_regular_polygon
    if is_regular_polygon(shape):
      return shape.centroid
  except Exception:                                   # noqa: BLE001
    pass
  scale = max(float(shape.area) ** 0.5, 1e-12)
  return polylabel(shape, tolerance=scale * 1e-9)


def dual_on_offer(topology, promoted=None):
  """The dual a design can be tiled with, or the reason there is none.

  Args:
    topology: a built Topology, or None where the tab holds none.
    promoted: the dual already promoted to a Tileable, for a caller
      that holds one; None to promote it here. A seam for the guard
      that stages a dual short of its cell, which no catalogue design
      produces any more.

  Returns:
    (dual, "") where the dual promotes to a Tileable that lays out and
    covers its cell, else (None, sentence) with the sentence for the
    person. Three refusals, each a different fact: no topology at all;
    a dual the library cannot lay out; a dual that would leave holes.
    The last is ruling 2 of 2026-09-05 -- a map with holes never ships
    -- and is what the completed dual's coverage check guards.
  """
  if topology is None:
    return None, ("This design has no topology, so it has no dual to "
                  "tile with.")
  dual = promoted if promoted is not None else dual_as_tileable(topology)
  if dual is None:
    return None, "This design's dual cannot be laid out as a tiling."
  if covers_its_cell(dual) is not True:
    return None, ("This design's dual would leave holes in the map, so "
                  "it is not offered.")
  return dual, ""


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
  # THE COMPLETE DUAL, NOT `get_dual_tiles()`: the library's frame is
  # truncated to the source's tile count and its corners drift between
  # copies, both worked around in `complete_dual` -- and both were how
  # "Map the dual" drew a map with holes on the default design.
  frame = complete_dual(topology)
  if frame is None or len(frame) == 0:
    return None
  if not _lattice_of(topology):
    return None
  try:
    tiles = frame.copy()
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
