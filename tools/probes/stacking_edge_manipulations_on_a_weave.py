"""What a weave looks like after edge manipulations are STACKED.

A single edit is measured elsewhere. Stacking them is a different
question, and it is one no count can answer, because what goes wrong
when edits accumulate is a SHAPE: a ribbon that stops being a ribbon, a
strand that has wandered across a crossing, a cloth whose warps are no
longer parallel. `apply` chains each edit onto the object the last one
returned and never rebuilds, so nothing in between asks whether the
result still reads as a weave.

WHAT THIS DRAWS, one row per structure and one column per edit applied
so far: the cloth alone, with the filler dropped, each strand piece
coloured by its own direction so a ribbon that has stopped being
straight is visible as such. The aimed class is named above each
column, and the figure's caption carries the two numbers that matter
per step -- how much of a cell moved, and whether the result still
lays out.

WHAT TO LOOK FOR, since a picture is only as good as the question put
to it:

  A RIBBON OF CONSTANT WIDTH is what reads as yarn, and ruling 3 of
  C-347 is that an edit moves a strand's two long edges IN PHASE. A
  strand that is wider in some places than others after stacking is
  that ruling failing under accumulation.

  THE INTERLACEMENT, which is the thing a weave IS: the same strands
  crossing the same partners in the same order. A strand that has
  moved ACROSS a crossing has composed a different cloth, and C-347's
  empirical rule is exactly that an edit survives provided one does
  not.

  TEARS AND OVERLAPS between neighbouring pieces, which `plane_coverage`
  reports as a number and which the eye finds faster.

  AND THE SCAFFOLDING SHOWING THROUGH: the filler is dropped for the
  drawing, so ground that was cloth and is now bare says a strand has
  shrunk away from its neighbour.

Run it in the reference venv, unbuffered, under the watchdog:

    PYTHONUNBUFFERED=1 python3 tools/watchdog.py --stall 900 \
      --timeout 5400 -- ./.venv-reference/bin/python3 \
      tools/probes/stacking_edge_manipulations_on_a_weave.py
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

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402

SPACING = 1000.0
ASPECT = 0.75
WEAVE = "plain weave a|b"
# THE STACK IS THREE EDGE MANIPULATIONS IN THE ORDER A PERSON WOULD
# REACH FOR THEM, each aimed at the FIRST class of its own moment
# rather than at a class chosen for the picture: bending an edge, then
# turning one, then stretching one. Vertex manipulations are left out
# deliberately -- the question here is what EDGE edits do to a ribbon.
STACK = (("zigzag_edge", {"n": 2, "h": 0.15}),
         ("rotate_edge", {"angle": 12.0}),
         ("scale_edge", {"sf": 1.15}))
IMAGES = os.path.join(HERE, "docs", "process", "images", "holes-as-tiles")
# WARP AND WEFT GET ONE COLOUR EACH, which is the whole point of the
# drawing: a piece drawn in the warp colour sitting where a weft should
# be is a strand that has crossed, and no number in this project says
# so as fast.
INK = ((0.0, "#c44e52"), (90.0, "#4c72b0"))
OTHER = "#8172b2"


def _ink_for(direction):
  """The colour a piece running in `direction` is drawn in.

  Args:
    direction: the angle of the piece's long axis, or None.

  Returns:
    A colour. `OTHER` only where the piece is on NEITHER of the weave's
    directions, which is the thing the drawing exists to show.

  IT ASKS `_same_direction` RATHER THAN ROUNDING, and that is a repair
  rather than a refinement. Keyed by `round(direction, 1)` this drew
  every piece purple after a rotate -- a direction of 179.9 is 0.0
  modulo a half turn and rounds to neither key -- so the picture
  reported every strand off its axis while `_off_axis`, which does ask
  modulo a half turn, reported none. The reading that was WRONG was the
  one with no control beside it: a drawing cannot be trusted past the
  arithmetic its colours are chosen by.
  """
  if direction is None:
    return OTHER
  for angle, colour in INK:
    if te._same_direction(direction, angle):
      return colour
  return OTHER


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


def cloth_of(unit, kinds: dict) -> list:
  """The strand polygons of a unit, with their own directions.

  Args:
    unit: a scaffolded unit, edited or not.
    kinds: the map `scaffolded_weave` returned.

  Returns:
    A list of `(geometry, direction)` for the cloth alone.
  """
  out = []
  ids = unit.tiles["tile_id"].astype(str)
  for row, geometry in enumerate(unit.tiles.geometry):
    if kinds.get(str(ids.iloc[row])) != "strand":
      continue
    if geometry.geom_type != "Polygon":
      continue
    axis = te._long_axis(geometry)
    out.append((geometry,
                te._as_direction(axis[0], axis[1]) if axis else None))
  return out


def widths_along(polygon) -> tuple:
  """How much a piece's width varies along its own axis.

  Args:
    polygon: one strand piece.

  Returns:
    `(narrowest, widest)` across the piece, measured as the extent
    across its own long axis at each of nine stations along it.

  A RIBBON OF CONSTANT WIDTH IS WHAT READS AS YARN, so this is the
  number the picture is being checked against: a swing between the two
  is one long side moving without the other, which is ruling 3 of C-347
  failing. It is measured rather than eyeballed because the eye is good
  at seeing THAT something is wrong and poor at saying how much.
  """
  import shapely
  axis = te._long_axis(polygon)
  if axis is None:
    return (0.0, 0.0)
  angle = te._as_direction(axis[0], axis[1])
  turned = shapely.affinity.rotate(polygon, -angle, origin="centroid")
  minx, miny, maxx, maxy = turned.bounds
  spans = []
  for step in range(1, 10):
    x = minx + (maxx - minx) * step / 10.0
    cut = shapely.intersection(
      turned, shapely.geometry.LineString([(x, miny - 1), (x, maxy + 1)]))
    if cut.is_empty:
      continue
    spans.append(cut.bounds[3] - cut.bounds[1])
  return (min(spans), max(spans)) if spans else (0.0, 0.0)


def _cover(cloth: list, cell: float) -> float:
  """How much of a fundamental cell the cloth covers.

  Args:
    cloth: the `(geometry, direction)` pairs the drawing uses.
    cell: the prototile's area.

  Returns:
    The cloth's own area over the cell's, which for a weave at aspect
    `a` starts near `1 - (1 - a)**2` and MUST NOT CLIMB: a weave whose
    strands have grown until the daylight closes has stopped being a
    weave, whatever a tiling check says about it.

  IT IS THE AREA RATHER THAN THE UNION, deliberately: two pieces that
  have grown into each other cover less ground than they sum to, and
  the sum is what says they have grown.
  """
  return sum(g.area for g, _d in cloth) / cell if cell else 0.0


def _off_axis(cloth: list, axes: list) -> int:
  """How many pieces no longer run along one of the weave's directions.

  Args:
    cloth: the `(geometry, direction)` pairs.
    axes: the directions the weave was BUILT with.

  Returns:
    A count. A strand that has turned off its own axis is no longer
    parallel to the strands it is meant to lie beside, which is what
    the drawing shows as a piece changing colour.
  """
  return sum(1 for _g, d in cloth
             if d is None or not any(te._same_direction(d, a) for a in axes))


def run(reading: str, families: str) -> dict:
  """Stack the manipulations under one structure and keep every step.

  Args:
    reading: which reading of the aspect gaps to build under.
    families: whether one class may hold both strand directions.

  Returns:
    A dict with `steps` -- one entry per stage, carrying the cloth, the
    class aimed at, the ground moved and whether the result lays out --
    and `note` where the weave would not build at all.
  """
  spec = spec_for(WEAVE)
  topology, unit, kinds, glue, note = te.weave_topology(
    spec, SPACING, ASPECT, reading=reading, families=families)
  if topology is None:
    return {"note": note, "steps": []}
  cell = unit.prototile.geometry[0].area
  built = cloth_of(unit, kinds)
  axes = sorted({round(d, 1) for _g, d in built if d is not None})
  steps = [{"aimed": "as built", "cloth": built,
            "moved": 0.0, "sound": te.still_has_a_topology(unit),
            "said": "", "cover": _cover(built, cell),
            "off_axis": _off_axis(built, axes)}]
  edits = []
  for how, args in STACK:
    # THE CLASS IS READ OFF THE DESIGN AS IT STANDS AT THIS STEP, since
    # a chained edit is aimed with the labels the last one left --
    # which is `apply`'s own contract and the thing a stack has to be
    # driven through rather than around.
    labels = te.class_labels(topology, glue).get("edge") or []
    if not labels:
      break
    edits = edits + [{"how": how, "target": "edge", "classes": labels[0],
                      "args": dict(args)}]
    edited, refusals, _state = te.apply(topology, list(edits), glue=glue)
    if edited is None:
      steps.append({"aimed": f"{how} on {labels[0]}", "cloth": [],
                    "moved": 0.0, "sound": False,
                    "said": "; ".join(refusals)})
      continue
    moved = 0.0
    for (old, _d), (new, _e) in zip(steps[0]["cloth"],
                                    cloth_of(edited, kinds)):
      moved += old.symmetric_difference(new).area
    now = cloth_of(edited, kinds)
    steps.append({"aimed": f"{how} on {labels[0]}",
                  "cloth": now,
                  "moved": moved / cell,
                  "sound": te.still_has_a_topology(edited),
                  "said": "; ".join(refusals),
                  "cover": _cover(now, cell),
                  "off_axis": _off_axis(now, axes)})
  return {"note": "", "steps": steps}


def draw(rows: list, path: str) -> None:
  """Draw every structure's stack as a grid, and write it out.

  Args:
    rows: a list of `(title, result)` as `run` returns them.
    path: where to write the PNG.

  Returns:
    None.
  """
  wide = max(len(result["steps"]) for _t, result in rows) or 1
  everything = [g for _t, result in rows for step in result["steps"]
                for g, _d in step["cloth"]]
  frame = None
  if everything:
    xs = [x for g in everything for x, _y in g.exterior.coords]
    ys = [y for g in everything for _x, y in g.exterior.coords]
    pad = max(max(xs) - min(xs), max(ys) - min(ys)) * 0.04
    frame = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
  figure, axes = plt.subplots(len(rows), wide,
                              figsize=(3.1 * wide, 3.3 * len(rows)))
  if len(rows) == 1:
    axes = [axes]
  for row, (title, result) in enumerate(rows):
    for column in range(wide):
      axis = axes[row][column] if wide > 1 else axes[row]
      axis.set_aspect("equal")
      axis.axis("off")
      if column >= len(result["steps"]):
        continue
      step = result["steps"][column]
      for geometry, direction in step["cloth"]:
        colour = _ink_for(direction)
        axis.add_patch(MplPolygon(
          list(geometry.exterior.coords), closed=True,
          facecolor=colour, edgecolor="#222222", linewidth=0.4, alpha=0.9))
      # ONE EXTENT FOR EVERY PANEL, or the columns cannot be compared --
      # which is the second fault this drawing had. Scaling each panel
      # to its own cloth zooms a step whose pieces moved outward, and
      # the daylight between strands then LOOKS closed while the area
      # says it has not moved at all. A picture meant for comparison
      # must be drawn in one frame.
      if frame:
        axis.set_xlim(frame[0], frame[2])
        axis.set_ylim(frame[1], frame[3])
      mark = "lays out" if step["sound"] else "DOES NOT LAY OUT"
      axis.set_title(f"{step['aimed']}\n{mark}, covers "
                     f"{step['cover']:.3f}, {step['off_axis']} off axis",
                     fontsize=7)
      if column == 0:
        axis.text(-0.08, 0.5, title, transform=axis.transAxes, fontsize=8,
                  rotation=90, va="center", ha="right")
  figure.suptitle(
    f"{WEAVE} at aspect {ASPECT}: three edge manipulations stacked\n"
    f"warp red, weft blue, filler dropped", fontsize=10)
  figure.tight_layout()
  figure.savefig(path, dpi=150)
  plt.close(figure)


def main() -> None:
  """Stack the manipulations under every structure, draw, and report."""
  os.makedirs(IMAGES, exist_ok=True)
  rows = []
  for reading in te.ASPECT_READINGS:
    for families in te.STRAND_FAMILIES:
      title = f"{reading}\n{families}"
      result = run(reading, families)
      rows.append((title, result))
      print(f"\n=== {reading} / {families} ===")
      if result["note"]:
        print(f"  refused: {result['note']}")
        continue
      for step in result["steps"]:
        widths = [widths_along(g) for g, _d in step["cloth"]]
        swing = max((wide - narrow) / wide for narrow, wide in widths
                    if wide > 0) if widths else 0.0
        print(f"  {step['aimed']:<28} moved {step['moved']:.4f}, "
              f"{'lays out' if step['sound'] else 'DOES NOT LAY OUT'}, "
              f"width swing {swing:>5.1%}, "
              f"cloth covers {step['cover']:.3f} of a cell, "
              f"{step['off_axis']:>2} piece(s) off axis"
              f"{'  said: ' + step['said'][:36] if step['said'] else ''}")
  path = os.path.join(IMAGES, "stacked-edge-edits.png")
  draw(rows, path)
  print(f"\nwrote {path}")


if __name__ == "__main__":
  main()
