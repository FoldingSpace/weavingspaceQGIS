"""Which drawn piece is which strand: the join the report said was missing.

docs/process/the-topology-of-a-weave-and-its-holes.md concludes that a
weave's structure is its INTERLACEMENT -- strands, crossings, and which
of the two rides over -- and that no construction on the rendered
polygons recovers it, the rendering being a projection that cuts the
strand passing under. It then says the two halves do not yet meet: the
interlacement names strands by loom coordinate, and an edit has to move
polygons.

THIS BUILDS THAT JOIN AND MEASURES WHETHER IT HOLDS. It is a
DIFFERENTIAL, which is the shape that has found most of this project's
real defects: two independent descriptions of one thing, compared, so a
disagreement is a defect by construction rather than a judgement.

  from the CODE, through the loom: each strand's cyclic over-and-under,
    and its FLOATS -- the maximal runs it rides over, which are the
    only parts of it a flat drawing can show
  from the DRAWING, through the geometry alone: each polygon's
    direction (the axis across which it measures aspect * spacing), the
    strand it belongs to (which line of that direction its centre sits
    on), and its length along its own axis

Neither side is derived from the other. The loom knows nothing of
aspect and the geometry knows nothing of over and under.

WHAT IT REPORTS, per weave and per aspect:

  whether every drawn piece is attributed to exactly one strand
  whether the number of pieces on a strand is a fixed multiple of its
    number of floats, and whether that multiple is the same for every
    strand of the weave
  whether the STRAND CLASSES the geometry falls into are the same
    partition as the classes the code gives
  the ROOM a strand has to move before it meets its neighbour, which
    is what an edit has to be clamped to, and which depends on the
    aspect where the edit itself does not

Run it in the reference venv, under the watchdog:

    python3 tools/watchdog.py --stall 600 --timeout 3600 -- \
      ./.venv-reference/bin/python3 \
      tools/probes/the_join_between_a_weave_and_its_drawing.py

NO TIMINGS ARE TAKEN; every figure is structural, so running it
beside other probes cannot change an answer. Where a step refuses, the
exception is printed rather than a sentence composed from it.
"""
import collections
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
from matplotlib.patches import Rectangle  # noqa: E402

from weavingspace_qgis import catalog  # noqa: E402
from weavingspace import weave_matrices  # noqa: E402
from weavingspace._loom import Loom  # noqa: E402

SPACING = 1000.0
ASPECTS = (0.9, 0.75, 0.5, 0.25)
WEAVES = ("plain weave a|b", "twill weave a|b", "basket weave ab|cd",
          "twill weave a|b-", "plain weave ab-|cd-")
IMAGES = os.path.join(HERE, "docs", "process", "images", "holes-as-tiles")
FIGURE_WEAVE = "twill weave a|b-"
CLASS_FILLS = ("#4c72b0", "#dd8452", "#55a868", "#c44e52")
# A tenth of the spacing separates two strand lines from two readings
# of one; the closest two lines can be is the spacing itself.
LINE_TOLERANCE = SPACING / 10.0


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


def loom_for(spec: dict):
  """The crossing sites and layer orders a weave's code implies.

  Args:
    spec: the catalogue entry, carrying `strands`, `weave_type` and the
      over-under `n`.

  Returns:
    A `Loom`.

  NO GEOMETRY IS BUILT, and `catalog.get_over_under` is the parser the
  plugin itself uses rather than a second one written here, which could
  disagree with it. A basket takes a single number where a twill takes
  the whole run.
  """
  code = str(spec.get("strands", ""))
  runs = code.split("|")
  warp = list(runs[0]) if runs else []
  weft = list(runs[1]) if len(runs) > 1 else []
  over_under = catalog.get_over_under(str(spec.get("n", "2")))
  kind = spec.get("weave_type", "plain")
  if kind == "basket":
    over_under = (over_under[0] if isinstance(over_under, (tuple, list))
                  else over_under)
  return Loom(weave_matrices.get_weave_pattern_matrix(
    weave_type=kind, n=over_under, warp=warp, weft=weft))


def floats_from_the_code(spec: dict) -> dict:
  """Each strand's floats, read from the loom and from nothing else.

  Args:
    spec: the catalogue entry.

  Returns:
    A dict keyed by (axis, index) whose values are the lengths of that
    strand's maximal runs of riding OVER, longest first. A strand that
    rides over nothing has an empty list.

  A FLOAT IS WHAT A FLAT DRAWING CAN SHOW OF A STRAND. Where a strand
  passes beneath, the picture cuts it, so the visible pieces of a
  strand are exactly its floats and the runs are what the geometry
  should be compared against. The runs are taken CYCLICALLY, since the
  loom is one repeat of something periodic and a float may wrap.
  """
  loom = loom_for(spec)
  rides = {}
  for site, order in zip(loom.indices, loom.orderings):
    if not isinstance(order, tuple) or len(order) < 2:
      continue
    row, column = site[0], site[1]
    rides.setdefault(("axis0", row), {})[column] = (order[-1] == 0)
    rides.setdefault(("axis1", column), {})[row] = (order[-1] == 1)
  out = {}
  for key, along in rides.items():
    sequence = [along[position] for position in sorted(along)]
    out[key] = _cyclic_runs(sequence)
  return out


def _cyclic_runs(sequence: list) -> list:
  """The lengths of the maximal runs of True, taken round the cycle.

  Args:
    sequence: a list of booleans, one per crossing along a strand.

  Returns:
    The run lengths, longest first. An all-True sequence gives one run
    of its own length rather than an unbounded one.

  THE WRAP IS THE POINT. A strand whose repeat begins in the middle of
  a float would otherwise be read as having two short floats where it
  has one long one, which would make the answer depend on where the
  library happened to start counting.
  """
  if not sequence or not any(sequence):
    return []
  if all(sequence):
    return [len(sequence)]
  start = next(i for i in range(len(sequence))
               if sequence[i] and not sequence[i - 1])
  rotated = sequence[start:] + sequence[:start]
  runs, current = [], 0
  for value in rotated:
    if value:
      current += 1
    elif current:
      runs.append(current)
      current = 0
  if current:
    runs.append(current)
  return sorted(runs, reverse=True)


def _lines(values: list) -> list:
  """Cluster a list of coordinates into the distinct lines they lie on.

  Args:
    values: coordinates along one axis.

  Returns:
    The cluster centres, in order.

  Two readings of one strand's line differ by floating point; two
  strands differ by at least the spacing, so a tenth of the spacing
  separates them with a wide margin either way.
  """
  out = []
  for value in sorted(values):
    if out and value - out[-1][-1] < LINE_TOLERANCE:
      out[-1].append(value)
    else:
      out.append([value])
  return [sum(group) / len(group) for group in out]


def pieces_from_the_drawing(name: str, aspect: float) -> dict:
  """Attribute every drawn polygon to a direction and a strand.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.

  Returns:
    A dict carrying the attributed pieces, the pieces that could not be
    attributed, and the lines found in each direction.

  THE DIRECTION IS THE AXIS ACROSS WHICH THE PIECE MEASURES ONE STRAND
  WIDTH, which is `aspect * spacing` by construction and is what tells
  a piece's across from its along whatever its length. A piece that
  measures a strand width BOTH ways is square and ambiguous, and is
  reported rather than assigned: at a low enough aspect a float of one
  is very nearly square, and guessing there would put pieces on the
  wrong strands while reading as a clean result.
  """
  unit = catalog.make_unit(spec_for(name), spacing=SPACING, crs=None,
                           aspect=aspect)
  width = aspect * SPACING
  near = width / 50.0
  found, ambiguous, squares = [], [], []
  for geometry, tile_id in zip(unit.tiles.geometry, unit.tiles["tile_id"]):
    if geometry.geom_type != "Polygon":
      continue
    x0, y0, x1, y1 = geometry.bounds
    across_x = abs((x1 - x0) - width) < near
    across_y = abs((y1 - y0) - width) < near
    if across_x and across_y:
      squares.append((tile_id, (x0 + x1) / 2.0, (y0 + y1) / 2.0,
                      x1 - x0, y1 - y0))
      continue
    if across_x:
      # Narrow in x, so the ribbon runs along y: a warp-like strand
      # named by the x line its centre sits on.
      found.append({"axis": "x", "line": (x0 + x1) / 2.0,
                    "along": y1 - y0, "tile_id": tile_id})
    elif across_y:
      found.append({"axis": "y", "line": (y0 + y1) / 2.0,
                    "along": x1 - x0, "tile_id": tile_id})
    else:
      ambiguous.append((tile_id, x1 - x0, y1 - y0))
  lines = {axis: _lines([p["line"] for p in found if p["axis"] == axis])
           for axis in ("x", "y")}
  # A SQUARE PIECE IS SETTLED BY THE LINES THE OTHER PIECES DREW, which
  # is information already in hand rather than a guess: at an aspect of
  # 0.5 a float of one is exactly as long as it is wide, and half a
  # twill's pieces measure one strand width both ways. It goes to
  # whichever direction has a strand line under its centre, and stays
  # ambiguous where both do or neither does.
  for tile_id, cx, cy, wide, tall in squares:
    on_x = any(abs(c - cx) < LINE_TOLERANCE for c in lines["x"])
    on_y = any(abs(c - cy) < LINE_TOLERANCE for c in lines["y"])
    if on_x and not on_y:
      found.append({"axis": "x", "line": cx, "along": tall,
                    "tile_id": tile_id})
    elif on_y and not on_x:
      found.append({"axis": "y", "line": cy, "along": wide,
                    "tile_id": tile_id})
    else:
      ambiguous.append((tile_id, wide, tall))
  for piece in found:
    centres = lines[piece["axis"]]
    piece["strand"] = min(range(len(centres)),
                          key=lambda i: abs(centres[i] - piece["line"]))
  return {"pieces": found, "ambiguous": ambiguous, "lines": lines,
          "width": width, "tiles": len(unit.tiles),
          "unit": unit, "squares": len(squares)}


def room_to_move(drawing: dict) -> float:
  """The clear distance between neighbouring strands of one direction.

  Args:
    drawing: a `pieces_from_the_drawing` result.

  Returns:
    The smallest gap between two adjacent strand lines of the same
    direction, less one strand width, as a fraction of the spacing; or
    0.0 where a direction has fewer than two strands.

  THIS IS THE CLAMP AN EDIT MEETS AND NOT THE EDIT ITSELF. A strand may
  be moved across its own direction until it touches its neighbour, and
  how far that is depends on the strand WIDTH -- so the same edit is
  legal at one aspect and not at another, which is the argument for
  holding what was asked and clamping on the way to the screen rather
  than writing the clamp back into the record.
  """
  best = None
  for axis in ("x", "y"):
    centres = drawing["lines"][axis]
    for first, second in zip(centres, centres[1:]):
      # Centre to centre, less the two half-widths that face each
      # other, is the clear air between the ribbons themselves.
      clear = (second - first) - drawing["width"]
      best = clear if best is None else min(best, clear)
  if best is None:
    return 0.0
  return best / SPACING


def classes_from_each_side(spec: dict, drawing: dict) -> dict:
  """The strand classes the code gives, beside those the drawing gives.

  Args:
    spec: the catalogue entry.
    drawing: a `pieces_from_the_drawing` result.

  Returns:
    A dict with a count from each side and whether the two partitions
    have the same shape -- the same number of classes of the same
    sizes.

  WHY THE SHAPE RATHER THAN THE MEMBERSHIP. The two sides name their
  strands differently: the loom by row and column, the geometry by
  which line a piece sits on, and nothing here establishes that loom
  row 0 is the leftmost line. What CAN be compared without assuming a
  correspondence is the partition's shape, and a disagreement there is
  a disagreement whatever the naming.
  """
  code = floats_from_the_code(spec)
  by_code = collections.Counter(
    tuple(runs) for key, runs in code.items() if runs)
  by_drawing = collections.Counter()
  grouped = collections.defaultdict(list)
  for piece in drawing["pieces"]:
    grouped[(piece["axis"], piece["strand"])].append(piece["along"])
  for lengths in grouped.values():
    by_drawing[tuple(sorted((round(v / SPACING, 3) for v in lengths),
                            reverse=True))] += 1
  return {
    "code_classes": len(by_code),
    "code_shape": sorted(by_code.values(), reverse=True),
    "drawing_classes": len(by_drawing),
    "drawing_shape": sorted(by_drawing.values(), reverse=True),
    "same_shape": (sorted(by_code.values(), reverse=True)
                   == sorted(by_drawing.values(), reverse=True)),
    "code_strands": sum(by_code.values()),
    "drawing_strands": sum(by_drawing.values()),
  }


def read(name: str, aspect: float) -> dict:
  """Compare the code's floats with the drawing's pieces at one aspect.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.

  Returns:
    A dict of readings for one row of the report.
  """
  spec = spec_for(name)
  code = floats_from_the_code(spec)
  drawing = pieces_from_the_drawing(name, aspect)
  floats = sum(len(runs) for runs in code.values())
  pieces = len(drawing["pieces"])
  ratios = set()
  per_strand = collections.Counter(
    (p["axis"], p["strand"]) for p in drawing["pieces"])
  for count in per_strand.values():
    ratios.add(count)
  return {
    "aspect": aspect,
    "tiles": drawing["tiles"],
    "pieces": pieces,
    "ambiguous": len(drawing["ambiguous"]),
    "squares": drawing["squares"],
    "code_strands": sum(1 for runs in code.values() if runs),
    "drawn_strands": len(per_strand),
    "floats": floats,
    "pieces_per_strand": sorted(ratios),
    "room": room_to_move(drawing),
    "classes": classes_from_each_side(spec, drawing),
  }


def figure(name: str, aspects, path: str) -> None:
  """Draw the code's classes beside the drawing's, at two strand widths.

  Args:
    name: the catalogue key.
    aspects: two strand widths to draw.
    path: where to write the PNG.

  Returns:
    None; the PNG is written.

  WHAT THE COLOURS DO AND DO NOT CLAIM. Each side is coloured by its
  OWN classes -- the loom's strands by their cyclic over-and-under, the
  drawn pieces by the lengths of the pieces on their strand -- because
  nothing here establishes that loom row 0 is the leftmost line. What
  the figure shows, and what the probe measures, is that the two
  partitions have the same SHAPE and that the drawing's does not move
  with the strand width.
  """
  spec = spec_for(name)
  code = floats_from_the_code(spec)
  ranking = sorted({tuple(runs) for runs in code.values() if runs},
                   key=lambda r: (-sum(r), r))
  loom = loom_for(spec)
  figure_, axes = plt.subplots(1, 1 + len(aspects),
                              figsize=(4.6 * (1 + len(aspects)), 4.8))

  axis = axes[0]
  rows = max(site[0] for site in loom.indices) + 1
  columns = max(site[1] for site in loom.indices) + 1
  for site, order in zip(loom.indices, loom.orderings):
    row, column = site[0], site[1]
    top = order[-1] if isinstance(order, tuple) and len(order) > 1 else None
    if top is None:
      fill, edge = "#f2f2f2", "#cccccc"
    else:
      key = tuple(code.get(("axis0", row) if top == 0
                           else ("axis1", column), ()))
      fill = CLASS_FILLS[ranking.index(key) % len(CLASS_FILLS)] if key \
        else "#f2f2f2"
      edge = "#20304a"
    axis.add_patch(Rectangle((column, rows - 1 - row), 1, 1,
                             facecolor=fill, edgecolor=edge, linewidth=0.6))
  axis.set_xlim(-0.2, columns + 0.2)
  axis.set_ylim(-0.2, rows + 0.2)
  axis.set_aspect("equal")
  axis.axis("off")
  axis.set_title("the code: one cell per crossing, tinted by the\n"
                 "class of whichever strand rides over it", fontsize=9, pad=8)

  for panel, aspect in zip(axes[1:], aspects):
    drawing = pieces_from_the_drawing(name, aspect)
    lengths = {}
    for piece in drawing["pieces"]:
      lengths.setdefault((piece["axis"], piece["strand"]), []).append(
        round(piece["along"] / SPACING, 3))
    shapes = sorted({tuple(sorted(v, reverse=True)) for v in lengths.values()},
                    key=lambda r: (-sum(r), r))
    unit = drawing["unit"]
    drawn = {id(g): g for g in unit.tiles.geometry}
    for geometry in unit.tiles.geometry:
      if geometry.geom_type != "Polygon":
        continue
      x0, y0, x1, y1 = geometry.bounds
      here = None
      for piece in drawing["pieces"]:
        centre = (x0 + x1) / 2.0 if piece["axis"] == "x" else (y0 + y1) / 2.0
        span = (y1 - y0) if piece["axis"] == "x" else (x1 - x0)
        if (abs(centre - piece["line"]) < 1e-6
            and abs(span - piece["along"]) < 1e-6):
          here = piece
          break
      if here is None:
        fill = "#f2f2f2"
      else:
        key = tuple(sorted(lengths[(here["axis"], here["strand"])],
                           reverse=True))
        fill = CLASS_FILLS[shapes.index(key) % len(CLASS_FILLS)]
      panel.add_patch(MplPolygon(list(geometry.exterior.coords), closed=True,
                                 facecolor=fill, edgecolor="#20304a",
                                 linewidth=0.5))
    panel.set_aspect("equal")
    panel.axis("off")
    panel.relim()
    panel.autoscale()
    panel.set_title(f"the drawing at aspect {aspect}: pieces tinted by\n"
                    f"the class of the strand they were attributed to",
                    fontsize=9, pad=8)
  figure_.suptitle(f"{name}: the same partition, read from the code and "
                   f"from the polygons", fontsize=10)
  figure_.tight_layout(rect=(0, 0, 1, 0.88))
  figure_.savefig(path, dpi=140)
  plt.close(figure_)


def main() -> None:
  """Report the join for each weave across the strand widths."""
  for name in WEAVES:
    print(f"\n=== {name} ===")
    shapes = []
    for aspect in ASPECTS:
      try:
        row = read(name, aspect)
      except Exception as exc:                           # noqa: BLE001
        print(f"  aspect {aspect:<5} {type(exc).__name__}: {exc}")
        continue
      klass = row["classes"]
      shapes.append((klass["drawing_classes"], tuple(klass["drawing_shape"])))
      print(f"  aspect {row['aspect']:<5} "
            f"{row['tiles']:>3} tiles  {row['pieces']:>3} attributed  "
            f"{row['ambiguous']:>2} ambiguous "
            f"({row['squares']} square)  "
            f"{row['drawn_strands']:>3} strands drawn against "
            f"{row['code_strands']:>3} threaded  "
            f"{row['floats']:>3} floats  "
            f"pieces per strand {row['pieces_per_strand']}  "
            f"room {row['room']:.3f}")
      print(f"        classes: code {klass['code_classes']} "
            f"{klass['code_shape']}   drawing {klass['drawing_classes']} "
            f"{klass['drawing_shape']}   "
            f"{'AGREE' if klass['same_shape'] else 'DISAGREE'}")
    if shapes:
      print(f"  the drawing's classes across aspects: "
            f"{'INVARIANT' if len(set(shapes)) == 1 else 'MOVE'}")
  os.makedirs(IMAGES, exist_ok=True)
  figure(FIGURE_WEAVE, (0.75, 0.25),
         os.path.join(IMAGES, "the-join-between-code-and-drawing.png"))
  print(f"\nfigure written to {IMAGES}")


if __name__ == "__main__":
  main()
