"""Does a class-aimed zigzag make a ribbon undulate, or pinch and swell?

Ruling 3 of C-347 says an edit must move a strand's two long edges IN
PHASE, because a ribbon of constant width is what reads as yarn. This asks
whether the class selector the tab already has delivers that, and the
answer is that it depends on the class -- which is neither of the two
outcomes the question was posed with.

TWO PARTS, and the first is what makes the second readable.

  A. WHAT A LONG SIDE IS MADE OF. The scaffolding abuts a strand at every
     crossing, so a long side is not one edge: it is four on a plain weave
     and five on a twill. Each segment carries its own class, and the
     probe reports WHERE along the strand each sits, so a stagger is
     measured rather than inferred from the arithmetic below.

  B. WHAT AN EDIT DOES. For each class in turn, the width across the
     strand and the centreline's offset, sampled along the strand's own
     axis:

       width constant, centreline moving   the two sides move together
       width swinging, centreline moving   one side moves at a time

THE AXIS IS NOT THE PIECE'S LONGER SIDE. A weave cuts the strand passing
UNDER into pieces wider than they are long -- 750 by 250 at spacing 1000
and aspect 0.75 -- so "longer" names the ACROSS direction on those and
every reading comes back transposed. The across extent is `aspect *
spacing` on every piece, over or under, so that is what picks the axis,
and `axis_of` refuses a piece where neither side is that width rather
than measuring the wrong thing quietly. This probe's first version did
take the longer side, and reported a constant width of 250 on a strand
750 wide.

THE WIDTH IS A CHORD ON A FIXED AXIS, so a steeply sloped edge reads
slightly wide and a swing must not be quoted as an exact amplitude. The
CONSTANT reading is exact, which is the one the conclusion rests on: two
edges displaced by the same graph function leave every chord at the
original width.

AN AREA DIGEST CANNOT ANSWER ANY OF THIS -- a zigzag conserves area
whichever way the edges move, which is why the question stood open.

Run it with the reference venv, which drives the vendored library with no
QGIS in the way:

    ./.venv-reference/bin/python3 \
      tools/probes/what_a_class_aimed_edit_does_to_a_ribbon.py

NO TIMINGS ARE TAKEN. Every figure is structural, so it is honest on a
busy machine. The record is docs/process/weaving-and-topology.md.
"""
import copy
import math
import os
import sys
import warnings

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "weavingspace_qgis", "vendor"))

warnings.filterwarnings("ignore", category=RuntimeWarning)

import geopandas as gpd  # noqa: E402
from shapely.geometry import LineString  # noqa: E402

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402

SPACING = 1000.0
ASPECT = 0.75
STRAND_WIDTH = ASPECT * SPACING
FILLER_ID = "z"
# One plain and one twill: they answer DIFFERENTLY, which is the finding.
WEAVES = ("plain weave a|b", "twill weave a|b")
SAMPLES = 41
NEAR = 1.0
BARS = " .:-=+*#"


def spec_for(name: str) -> dict:
  """The catalogue's own entry for a weave, looked up rather than typed.

  Args:
    name: the catalogue key, e.g. ``twill weave a|b``.

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


def scaffolded(name: str) -> tuple:
  """A thin weave with its daylight filled, per C-347's first ruling.

  Args:
    name: the catalogue key for the weave.

  Returns:
    (thin, filled) -- the weave as a person would get it, and the same
    weave with one DISTINCT-id filler piece per piece of daylight. The
    distinctness is load-bearing: `_setup_regularised_prototile` dissolves
    by `tile_id`, and merged filler is a multi-part tile `Topology`
    refuses.
  """
  thin = catalog.make_unit(spec_for(name), spacing=SPACING, crs=None,
                           aspect=ASPECT)
  gap = te.plane_coverage(thin)[2]
  parts = [piece
           for part in getattr(gap, "geoms", [gap])
           for piece in getattr(part, "geoms", [part])
           if not piece.is_empty and piece.area > 1]
  tiles = gpd.GeoDataFrame(
    {"tile_id": list(thin.tiles.tile_id)
                + [f"{FILLER_ID}{i}" for i in range(len(parts))]},
    geometry=list(thin.tiles.geometry) + parts, crs=thin.tiles.crs)
  filled = copy.deepcopy(thin)
  filled.tiles = tiles
  filled._setup_regularised_prototile()
  return thin, filled


def axis_of(polygon):
  """The strand's own frame for one piece, or None where it is not one.

  Args:
    polygon: a strand piece, over or under.

  Returns:
    (along, across, run, width, centre) with the two directions as unit
    vectors, or None where NEITHER side of the piece is the strand's
    width -- which is a piece this probe has no business measuring, and
    saying so beats measuring the wrong direction.
  """
  rect = polygon.minimum_rotated_rectangle
  c = list(rect.exterior.coords)[:5]
  if len(c) < 3:
    return None
  a = (c[1][0] - c[0][0], c[1][1] - c[0][1])
  b = (c[2][0] - c[1][0], c[2][1] - c[1][1])
  la, lb = math.hypot(*a), math.hypot(*b)
  if la < 1e-9 or lb < 1e-9:
    return None
  if abs(la - STRAND_WIDTH) < abs(lb - STRAND_WIDTH):
    across, along, width, run = a, b, la, lb
  else:
    across, along, width, run = b, a, lb, la
  if abs(width - STRAND_WIDTH) > 1.0:
    return None
  n, m = math.hypot(*along), math.hypot(*across)
  return ((along[0] / n, along[1] / n), (across[0] / m, across[1] / m),
          run, width, rect.centroid)


def edges_of(topology) -> list:
  """Every edge in the topology as a line with its class label.

  Args:
    topology: a built Topology.

  Returns:
    A list of (LineString, label). An edge's `corners` are vertex ids into
    `topology.points`, and the whole run of them is the edge -- taking
    only the two end `vertices` would draw a chord across a curve.
  """
  out = []
  for edge in topology.edges.values():
    points = [topology.points[c].point for c in edge.corners]
    if len(points) < 2:
      continue
    line = LineString([(p.x, p.y) for p in points])
    if line.length > 1e-6:
      out.append((line, getattr(edge, "label", "") or "?"))
  return out


def long_sides(tile, edges) -> dict:
  """The edges lying along one strand piece's two long sides.

  Args:
    tile: the strand piece, un-edited.
    edges: the (line, label) pairs from `edges_of`.

  Returns:
    {"+": [...], "-": [...]}, each a list of (start, end, label, length)
    with start and end measured ALONG the strand from its centre, or an
    empty dict where the piece has no strand frame.
  """
  found = axis_of(tile)
  if found is None:
    return {}
  u, v, _run, _width, centre = found
  sides = {"+": [], "-": []}
  for line, label in edges:
    mid = line.interpolate(0.5, normalized=True)
    if tile.exterior.distance(mid) > NEAR:
      continue
    dx = line.coords[-1][0] - line.coords[0][0]
    dy = line.coords[-1][1] - line.coords[0][1]
    n = math.hypot(dx, dy)
    if abs((dx * u[0] + dy * u[1]) / n) < 0.99:      # across, not along
      continue
    offset = (mid.x - centre.x) * v[0] + (mid.y - centre.y) * v[1]
    ends = sorted((x - centre.x) * u[0] + (y - centre.y) * u[1]
                  for x, y in (line.coords[0], line.coords[-1]))
    sides["+" if offset > 0 else "-"].append(
      (ends[0], ends[1], label, line.length))
  return {key: sorted(value) for key, value in sides.items()}


def profile(original, edited):
  """Width and centreline offset sampled along the strand's own axis.

  Args:
    original: the un-edited piece, which supplies the frame.
    edited: the same piece after an edit, which is what is measured.

  Returns:
    (widths, offsets, width, run), or None where the piece has no strand
    frame. Sampling stops 5% clear of each end, where the cut line meets
    the piece's own end edges rather than its sides.
  """
  found = axis_of(original)
  if found is None:
    return None
  u, v, run, width, centre = found
  half = max(run, width) * 2.0
  widths, offsets = [], []
  for i in range(SAMPLES):
    t = (i / (SAMPLES - 1) - 0.5) * run * 0.90
    px, py = centre.x + t * u[0], centre.y + t * u[1]
    line = LineString([(px - half * v[0], py - half * v[1]),
                       (px + half * v[0], py + half * v[1])])
    hit = line.intersection(edited)
    if hit.is_empty:
      continue
    widths.append(hit.length)
    projected = [(x - px) * v[0] + (y - py) * v[1]
                 for geom in getattr(hit, "geoms", [hit])
                 for x, y in geom.coords]
    offsets.append((min(projected) + max(projected)) / 2.0)
  if not widths:
    return None
  return widths, offsets, width, run


def sparkline(values) -> str:
  """The SHAPE of a profile, so a wave is told from a jog by eye.

  Args:
    values: one reading per sample along the strand.

  Returns:
    One character per sample, scaled between the profile's own extremes --
    so a flat profile draws as spaces rather than as noise magnified.
  """
  lo, hi = min(values), max(values)
  if hi - lo < 1e-9:
    return BARS[0] * len(values)
  return "".join(BARS[min(len(BARS) - 1,
                          int((v - lo) / (hi - lo) * (len(BARS) - 1)))]
                 for v in values)


def signature(measured) -> str:
  """One line naming a behaviour, so sixteen tiles do not fill a page.

  Args:
    measured: `profile`'s tuple.

  Returns:
    The width range and swing, the centreline's travel, the run, and the
    centreline's shape -- all as fractions of the strand's own width, so
    the numbers do not depend on the spacing.
  """
  widths, offsets, width, run = measured
  swing = max(widths) - min(widths)
  wander = max(offsets) - min(offsets)
  return (f"width {min(widths):7.1f}-{max(widths):7.1f} "
          f"(swing {swing / width:6.1%})  centre {wander / width:6.1%}  "
          f"run {run:6.1f}  {sparkline(offsets)}")


def report_what_a_long_side_is_made_of(thin, edges) -> None:
  """Part A: the segments of each long side, and whether they align.

  Args:
    thin: the weave as a person gets it, whose tiles supply the frames.
    edges: the (line, label) pairs from `edges_of`.
  """
  print("  A. what each long side is made of")
  for row in range(len(thin.tiles)):
    tile = thin.tiles.geometry.iloc[row]
    sides = long_sides(tile, edges)
    name = thin.tiles.tile_id.iloc[row]
    if not sides:
      print(f"    tile {name:>3} (row {row:>2}): no side is the strand's "
            f"width; not a piece this probe measures")
      continue
    plus, minus = sides["+"], sides["-"]
    shared = {label for *_, label, _ in plus} & {label for *_, label, _ in minus}
    print(f"    tile {name:>3} (row {row:>2}): "
          f"{len(plus)} + {len(minus)} edges along its two long sides; "
          f"shared classes {sorted(shared) or 'NONE'}")
    for label in sorted(shared):
      here = [(s, e) for s, e, l, _ in plus if l == label]
      there = [(s, e) for s, e, l, _ in minus if l == label]
      aligned = all(any(abs(s1 - s2) < 1.0 and abs(e1 - e2) < 1.0
                        for s2, e2 in there) for s1, e1 in here)
      print(f"      class {label}: + at {[(round(s), round(e)) for s, e in here]}"
            f"  - at {[(round(s), round(e)) for s, e in there]}  "
            f"{'ALIGNED, so in phase' if aligned else 'STAGGERED, so one side at a time'}")


def report_what_an_edit_does(thin, filled, topology) -> None:
  """Part B: the width and centreline under a zigzag aimed at each class.

  Args:
    thin: the weave as a person gets it, whose tiles are the subject.
    filled: the scaffolded weave, whose row order the edit must preserve.
    topology: the Topology built on `filled`.
  """
  print("  B. what a zigzag n=2 h=0.2 aimed at each class does")
  strands = len(thin.tiles)
  print("    CONTROL, no edit -- every strand must read flat:")
  seen = {}
  for row in range(strands):
    geom = thin.tiles.geometry.iloc[row]
    measured = profile(geom, geom)
    key = signature(measured) if measured else "no strand frame"
    seen.setdefault(key, []).append(row)
  for line, rows in seen.items():
    print(f"      x{len(rows):<3} {line}")

  for label in te.classes(topology)["edge"]:
    edited, refused, _state = te.apply(
      topology, [{"how": "zigzag_edge", "classes": label,
                  "args": {"n": 2, "h": 0.2, "smoothness": 3}}])
    print(f"    aimed at edge class {label!r}:")
    if edited is None:
      print(f"      refused: {refused}")
      continue
    after = edited.tiles
    if list(after.tile_id) != list(filled.tiles.tile_id):
      print("      PREMISE FAILED: the row order moved under the edit")
      continue
    seen, still = {}, 0
    for row in range(strands):
      before = thin.tiles.geometry.iloc[row]
      now = after.geometry.iloc[row]
      if before.symmetric_difference(now).area <= 1.0:
        still += 1
        continue
      measured = profile(before, now)
      key = signature(measured) if measured else "no strand frame"
      seen.setdefault(key, []).append(row)
    print(f"      {strands - still} of {strands} strand tiles moved")
    for line, rows in sorted(seen.items(), key=lambda kv: -len(kv[1])):
      print(f"      x{len(rows):<3} {line}")


def main() -> None:
  """Both parts, on a plain weave and a twill, which answer differently."""
  for name in WEAVES:
    thin, filled = scaffolded(name)
    topology, why = te.build(filled)
    print(f"\n=== {name} at aspect {ASPECT}, spacing {SPACING:.0f} ===")
    if topology is None:
      print(f"  no topology: {why}")
      continue
    labels = te.classes(topology)["edge"]
    print(f"  edge classes {labels!r}; {len(thin.tiles)} strand tiles + "
          f"{len(filled.tiles) - len(thin.tiles)} filler")
    report_what_a_long_side_is_made_of(thin, edges_of(topology))
    report_what_an_edit_does(thin, filled, topology)


if __name__ == "__main__":
  main()
