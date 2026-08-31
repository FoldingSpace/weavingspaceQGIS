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
    (tileable, refusals) -- the unit to tile, and a list of sentences
    about edits that could not be drawn. The tileable is the ORIGINAL
    where every edit was refused, so a design never silently becomes
    something nobody asked for.

  EACH EDIT IS APPLIED FROM THE TOPOLOGY THE LAST ONE PRODUCED, which
  is what makes a list of edits mean what it reads like. Upstream's own
  caution is that a transformed Topology is not reliably labelled, so
  the topology is rebuilt between edits -- 1.08s apiece on the fastest
  design measured, which is the cost of a list rather than of a drag.
  """
  current = topology
  tileable = topology.tileable
  refusals = []
  for edit in edits or ():
    how = edit.get("how")
    if how not in MANIPULATIONS:
      refusals.append(f"'{how}' is not a manipulation this version "
                      f"offers, so it was left out.")
      continue
    selector = edit.get("classes") or ""
    # A REBUILT TOPOLOGY IS WHAT THE NEXT EDIT IS AIMED WITH, so an
    # edit after one that left no workable topology has nothing to
    # aim at. That is a different sentence from "this change could not
    # be drawn", and it names the change that actually cost it.
    if current is None:
      refusals.append(
        f"{MANIPULATIONS[how]['label']} on {selector} could not be "
        f"applied, because an earlier change left a design whose "
        f"topology cannot be worked out.")
      continue
    args = {}
    for name, value in (edit.get("args") or {}).items():
      args[name] = int(round(value)) if name in _WHOLE else float(value)
    try:
      moved = current.transform_geometry(True, True, selector, how, **args)
    except Exception:                                 # noqa: BLE001
      refusals.append(_refusal(how, selector))
      continue
    drawable, _repaired = _make_drawable(moved.tileable)
    if drawable is None:
      refusals.append(_refusal(how, selector))
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
    current, _why = build(drawable)
  return tileable, refusals


def _same_shape(before, after) -> bool:
  """Whether two units are the same shape, for reporting purposes.

  Args:
    before: the unit as it stood.
    after: the unit a manipulation produced.

  Returns:
    True where nothing a person could see has moved. Compares the
    COORDINATES of every tile, within a tolerance scaled to the unit.

  IT TOOK TWO WRONG INSTRUMENTS TO GET HERE, and both are worth
  knowing, because each looked obviously right.

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

  SO THE COORDINATES ARE COMPARED, with `shapely.equals_exact` and a
  tolerance of a millionth of the unit's own span. At spacing 500 that
  is 5e-4: three orders above the re-gridding noise, and far below the
  smallest manipulation on offer, a nudge of 0.05 units.

  IT ANSWERS FALSE WHEN IT CANNOT TELL, deliberately: a unit whose
  geometry will not be read is not evidence that nothing happened, and
  saying "this changed nothing" wrongly is worse than staying quiet.
  """
  try:
    import shapely
    one = getattr(before, "tiles", None)
    two = getattr(after, "tiles", None)
    if one is None or two is None or len(one) != len(two):
      return False
    # THE TOLERANCE IS SCALED TO THE UNIT, which is the whole trick: a
    # unit's coordinates follow the SPACING, so a fixed number is a
    # different question at 500 than at 5.
    low_x, low_y, high_x, high_y = one.total_bounds
    span = max(abs(high_x - low_x), abs(high_y - low_y), 1.0)
    tolerance = span * 1e-6
    return all(
      shapely.equals_exact(a, b, tolerance=tolerance)
      for a, b in zip(one.geometry, two.geometry))
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
