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
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402

SPACING = 1000.0
ASPECT = 0.75
WEAVES = ("plain weave a|b", "twill weave a|b", "twill weave a|b-")
# THE TWILL IS WHAT THE FIGURE DRAWS because it is the case that can
# discriminate: a plain weave's four pieces all move under either
# reading, so a picture of one shows the same thing twice.
FIGURE_WEAVE = "twill weave a|b"
IMAGES = os.path.join(HERE, "docs", "process", "images", "holes-as-tiles")
# ONE COLOUR PER CLASS, and the list is longer than any weave drawn
# here needs, so a design with more classes wraps rather than raising.
CLASS_INK = ("#c44e52", "#4c72b0", "#55a868", "#8172b2", "#dd8452",
             "#937860", "#da8bc3", "#8c8c8c", "#ccb974", "#64b5cd")
MOVED = "#dd8452"
STILL = "#4c72b0"
FILLER = "#e4e4e4"


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


def _pieces_and_movement(name: str, reading: str):
  """One weave's strand pieces before and after an edit, and which moved.

  Args:
    name: the catalogue key.
    reading: which reading of the daylight to build under.

  Returns:
    `(before, after, moved, filler, aimed, topology, glue, note)` --
    the strand polygons as built and as edited, a list of booleans one
    per piece, the filler polygons, the class the edit was aimed at,
    the topology its classes were read from, the gluing in force, and
    any refusal.

  THE PIECES ARE PAIRED BY POSITION, which the library's own order
  makes safe: `apply` transforms the tiles it was given and hands back
  a frame of the same length in the same order. The lengths are
  checked rather than assumed, since a pairing that slipped by one
  would colour the wrong pieces and look like a result.
  """
  spec = spec_for(name)
  topology, unit, kinds, glue, note = te.weave_topology(
    spec, SPACING, ASPECT, reading=reading)
  if topology is None:
    return [], [], [], [], "", None, None, note
  labels = te.class_labels(topology, glue)
  aimed = (labels.get("edge") or [""])[0]
  edit = {"how": "zigzag_edge", "target": "edge", "classes": aimed,
          "args": {"n": 2, "h": 0.15}}
  edited, _refusals, _state = te.apply(topology, [edit], glue=glue)
  def pieces(of_unit):
    return [(g, tile_id) for g, tile_id in
            zip(of_unit.tiles.geometry, of_unit.tiles["tile_id"].astype(str))
            if g.geom_type == "Polygon"]
  before_all = pieces(unit)
  after_all = pieces(edited) if edited is not None else before_all
  if len(before_all) != len(after_all):
    return [], [], [], [], "", None, None, \
      "the edit changed how many tiles there are"
  before = [g for g, tile_id in before_all if kinds.get(tile_id) == "strand"]
  after = [g for (g, tile_id), (_b, _i) in zip(after_all, before_all)
           if kinds.get(tile_id) == "strand"]
  filler = [g for g, tile_id in before_all if kinds.get(tile_id) != "strand"]
  moved = [one.symmetric_difference(two).area > one.area / 1e4
           for one, two in zip(before, after)]
  return before, after, moved, filler, aimed, topology, glue, ""


def _draw_reading(axis, name: str, reading: str, cells: float,
                  label_size: int) -> None:
  """Draw one weave under one reading onto one axis.

  Args:
    axis: the matplotlib axis.
    name: the catalogue key of the weave.
    reading: which reading of the aspect gaps to build under.
    cells: half the window's width, in spacings.
    label_size: the point size of an ordinary class label.

  Returns:
    None; the axis is mutated.
  """
  (before, after, moved, filler, aimed, topology, glue,
   note) = _pieces_and_movement(name, reading)
  if topology is None:
    axis.set_title(f"{name}: {note[:50]}", fontsize=9)
    axis.axis("off")
    return
  names = te.class_labels(topology, glue)
  order = names.get("edge") or []
  ink = {label: CLASS_INK[i % len(CLASS_INK)]
         for i, label in enumerate(order)}
  for piece in filler:
    axis.add_patch(MplPolygon(list(piece.exterior.coords), closed=True,
                              facecolor="#ece3cd", edgecolor="#b9ac8c",
                              linewidth=0.8, zorder=1))
  for piece, did in zip(after, moved):
    for part in getattr(piece, "geoms", [piece]):
      if part.geom_type != "Polygon":
        continue
      axis.add_patch(MplPolygon(
        list(part.exterior.coords), closed=True,
        facecolor="#fbe0cd" if did else "#ccd9ec",
        edgecolor="#6f6f6f", linewidth=0.9, zorder=2))
  for piece in before:
    axis.add_patch(MplPolygon(list(piece.exterior.coords), closed=True,
                              facecolor="none", edgecolor="#3a3a3a",
                              linewidth=0.8, linestyle=(0, (4, 3)),
                              zorder=3))
  middle = shapely.union_all(before) if before else shapely.Polygon()
  centre = middle.centroid
  half = cells * SPACING
  for edge in topology.edges.values():
    label = getattr(edge, "label", "")
    if not label:
      continue
    klass = glue["edges"].get(label, label) if glue else label
    line = edge.get_geometry()
    point = line.interpolate(0.5, normalized=True)
    if abs(point.x - centre.x) > half or abs(point.y - centre.y) > half:
      continue
    colour = ink.get(klass, "#333333")
    is_aimed = klass == aimed
    axis.plot(*line.xy, color=colour, zorder=4,
              linewidth=3.2 if is_aimed else 1.6,
              solid_capstyle="round", alpha=1.0 if is_aimed else 0.8)
    axis.text(point.x, point.y, klass,
              fontsize=label_size + 1 if is_aimed else label_size,
              color="white" if is_aimed else colour, ha="center",
              va="center", zorder=5, fontweight="bold",
              bbox=dict(boxstyle="round,pad=0.15",
                        facecolor=colour if is_aimed else "white",
                        edgecolor="none", alpha=0.95))
  axis.set_xlim(centre.x - half * 1.04, centre.x + half * 1.04)
  axis.set_ylim(centre.y - half * 1.04, centre.y + half * 1.04)
  axis.set_aspect("equal")
  axis.axis("off")
  # THE TITLE NAMES WHICH GAPS. A weave's ground is empty for three
  # different reasons and "gaps" alone does not say which is being
  # decided about, which is the whole of the question (maintainer's
  # correction, 2026-09-11).
  says = ("aspect gaps COUNT, as a dropped strand's gap does"
          if reading == te.ASPECT_LIKE_A_DROP
          else "aspect gaps IGNORED, as an inset's gaps are")
  axis.set_title(f"{name}\n{says}\n"
                 f"{len(order)} edge classes: {', '.join(order)}; "
                 f"aimed at {aimed}\n"
                 f"{sum(moved)} of {len(moved)} ribbon pieces moved",
                 fontsize=9, pad=6)


def figure(path: str, weaves=(FIGURE_WEAVE,), cells: float = 1.15,
           size=(14.6, 8.0), label_size: int = 11) -> None:
  """Draw what one edit reaches, with the classes it was aimed at named.

  Args:
    path: where to write the PNG.
    weaves: the catalogue keys to draw, one row each.
    cells: half the window's width, in spacings. A small window makes
      one hole legible; a larger one shows the pattern repeating,
      which is what says the alternation is the design rather than an
      accident of where the picture was cut.
    size: the figure's size in inches.
    label_size: the point size of an ordinary class label.

  Returns:
    None; the PNG is written.

  THE TWO HALVES BELONG IN ONE PICTURE. Which ribbons moved says what
  happened; the class names say WHY, and shown apart a reader has to
  take the second on trust. The edges are the ones the classes were
  read from, before the edit, drawn over the pieces as edited: that is
  the honest pairing, since the edit was aimed at those edges and the
  wave is what came of it.
  """
  os.makedirs(IMAGES, exist_ok=True)
  figure_, axes = plt.subplots(len(weaves), 2, figsize=size, squeeze=False)
  for row, name in enumerate(weaves):
    for column, reading in enumerate(te.ASPECT_READINGS):
      _draw_reading(axes[row][column], name, reading, cells, label_size)
  figure_.suptitle(
    f"The same zigzag at aspect {ASPECT}, aimed at the first edge class, "
    f"under each reading of a weave's ASPECT GAPS.\n"
    f"A dropped strand's ground counts under both readings; an inset's "
    f"counts under neither. Only the aspect gap is in question.\n"
    f"The aimed-at class is thick with a filled label. Dashed is where "
    f"each ribbon was. Peach moved, blue did not, cream is the filler.",
    fontsize=10)
  figure_.tight_layout(rect=(0, 0, 1, 0.90))
  figure_.savefig(path, dpi=140)
  plt.close(figure_)


def labelled_figure(path: str) -> None:
  """Draw every edge class, named, under each reading of the daylight.

  Args:
    path: where to write the PNG.

  Returns:
    None; the PNG is written.

  WHAT IT IS FOR. The earlier figure shows which ribbons an edit
  reaches and not WHY, so a reader has to take the classes on trust.
  Here every edge of the structure is drawn in its class's own colour
  with the class named on it, so the gluing can be seen doing its
  work: four edges round a hole carry four names on the left and the
  facing pairs carry one name each on the right.

  ONE FUNDAMENTAL CELL'S WORTH IS DRAWN. `topology.edges` holds every
  edge of the patch of repeats the constructor lays, so drawing them
  all would stack a dozen copies of each label on top of each other;
  the window is centred on the unit and sized from it.
  """
  os.makedirs(IMAGES, exist_ok=True)
  figure_, axes = plt.subplots(1, 2, figsize=(14.0, 7.4))
  for axis, reading in zip(axes, te.ASPECT_READINGS):
    topology, unit, kinds, glue, note = te.weave_topology(
      spec_for(FIGURE_WEAVE), SPACING, ASPECT, reading=reading)
    if topology is None:
      axis.set_title(note[:60], fontsize=9)
      continue
    names = te.class_labels(topology, glue)
    order = names.get("edge") or []
    ink = {name: CLASS_INK[i % len(CLASS_INK)]
           for i, name in enumerate(order)}
    for geometry, tile_id in zip(unit.tiles.geometry,
                                 unit.tiles["tile_id"].astype(str)):
      if geometry.geom_type != "Polygon":
        continue
      axis.add_patch(MplPolygon(
        list(geometry.exterior.coords), closed=True,
        facecolor="#eef1f6" if kinds.get(tile_id) == "strand" else "#f6f2e8",
        edgecolor="#d0d0d0", linewidth=0.5, zorder=1))
    middle = shapely.union_all(
      [g for g in unit.tiles.geometry if g.geom_type == "Polygon"])
    centre = middle.centroid
    # A WINDOW OF ABOUT TWO CELLS, not the whole unit: drawn whole, a
    # twill puts three hundred labels in the frame and none of them can
    # be read, which is a diagram of the fact that there are a lot of
    # edges rather than of what the classes are.
    half = 1.15 * SPACING
    drawn = 0
    for edge in topology.edges.values():
      label = getattr(edge, "label", "")
      if not label:
        continue
      klass = glue["edges"].get(label, label) if glue else label
      line = edge.get_geometry()
      point = line.interpolate(0.5, normalized=True)
      if (abs(point.x - centre.x) > half or abs(point.y - centre.y) > half):
        continue
      colour = ink.get(klass, "#333333")
      axis.plot(*line.xy, color=colour, linewidth=3.0, solid_capstyle="round",
                zorder=3)
      axis.text(point.x, point.y, klass, fontsize=12, color=colour,
                ha="center", va="center", zorder=4, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                          edgecolor="none", alpha=0.9))
      drawn += 1
    axis.set_xlim(centre.x - half * 1.06, centre.x + half * 1.06)
    axis.set_ylim(centre.y - half * 1.06, centre.y + half * 1.06)
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title(
      f"{'gaps count, like a dropped strand' if reading == te.ASPECT_LIKE_A_DROP else 'gaps ignored, like an inset'}\n"
      f"{len(order)} edge class(es): {', '.join(order)}",
      fontsize=10, pad=8)
  figure_.suptitle(
    f"{FIGURE_WEAVE} at aspect {ASPECT}, two cells of it: every edge "
    f"named by its class.\nPale blue is ribbon. Cream is the filler that "
    f"plugs a gap. Round a cream square, the four edges carry four names "
    f"on the left and two on the right.", fontsize=10)
  figure_.tight_layout(rect=(0, 0, 1, 0.88))
  figure_.savefig(path, dpi=140)
  plt.close(figure_)


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
  figure(os.path.join(IMAGES, "what-an-edit-reaches.png"))
  figure(os.path.join(IMAGES, "what-an-edit-reaches-wide.png"),
         weaves=("twill weave a|b", "basket weave ab|cd"),
         cells=2.6, size=(17.0, 17.4), label_size=7)
  labelled_figure(os.path.join(IMAGES, "the-edge-classes-named.png"))
  print(f"\nfigure written to {IMAGES}")


if __name__ == "__main__":
  main()
