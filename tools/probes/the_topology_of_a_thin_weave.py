"""Does a thin weave have a topology, and whose topology is it?

`Topology` needs a gap-free tiling. A weave at aspect below 1.0 is not
one: its strands are narrower than their cells, so the plane is not
covered and the constructor refuses. Treating the DAYLIGHT AS TILES
makes it one (C-347), which is what lets an edit be aimed at a strand
at all.

That construction raises the question this probe is for. If we invent
the holes, the classes an edit is aimed at might be a fact about our
invention rather than about the weave. So the test is INVARIANCE: hold
the weave and vary the strand width, which changes every coordinate in
the design and none of its combinatorics. If the class structure moves
with the aspect, the topology belongs to the filling; if it stands
still, the filling is only a way of computing something the weave had
all along.

WHAT IT MEASURES, per weave and per aspect:

  the strand tiles, and the pieces the daylight becomes
  whether the filled design is gap-free, and whether Topology takes it
  the EDGE and VERTEX CLASSES, which are what an edit is aimed at
  how many vertex classes stand on ground only the filler touches
  the dual: how many tiles, since a dual has one per vertex
  and aspect 1.0 as the CONTROL, where the library fuses same-label
    pieces and the design becomes a different one

AND IT WRITES THE FIGURES the discussion uses, so the pictures and the
numbers cannot drift apart. They go to
docs/process/images/holes-as-tiles/.

Run it in the reference venv, which has matplotlib and no QGIS in the
way, under the watchdog since a topology build is the expensive end of
this catalogue:

    python3 tools/watchdog.py --stall 300 --timeout 3600 -- \
      ./.venv-reference/bin/python3 tools/probes/the_topology_of_a_thin_weave.py

NO TIMINGS ARE TAKEN. Every figure here is structural, so it is honest
on a busy machine.

AN EARLIER VERSION ATTRIBUTED VERTICES AGAINST `topology.tileable`,
which is the FILLED unit -- so every vertex sat on a "strand", none
could ever be credited to the filler, and it reported 0 of 280 at every
aspect. A uniform verdict is almost always the instrument. The strands
are passed in explicitly now.
"""
import copy
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

import geopandas as gpd  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402
from shapely.geometry import Point  # noqa: E402

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402
import weavingspace.tiling_utils as tu  # noqa: E402

SPACING = 1000.0
FILLER_ID = "z"
ASPECTS = (0.9, 0.75, 0.5, 0.25)
WEAVES = ("plain weave a|b", "twill weave a|b")
IMAGES = os.path.join(HERE, "docs", "process", "images", "holes-as-tiles")
ON_EDGE = 1e-3

STRAND_FILL = "#4c72b0"
FILLER_FILL = "#dcdcdc"
DUAL_EDGE = "#c44e52"


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


def daylight_of(unit) -> list:
  """The holes between strands, as single-part pieces the library can hold.

  Args:
    unit: a thin weave.

  Returns:
    A list of Polygons, each snapped to the library's own precision --
    a piece that pinches at RESOLUTION is split by `set_precision`
    inside the library's own cleaner, and the multi-part result reaches
    `get_corners`, which asks it for `.exterior`.
  """
  geometry = te.plane_coverage(unit)[2]
  if geometry is None:
    return []
  out = []
  for part in getattr(geometry, "geoms", [geometry]):
    for piece in getattr(part, "geoms", [part]):
      if piece.is_empty or piece.area <= 1:
        continue
      try:
        snapped = tu.gridify(piece)
      except Exception:                                # noqa: BLE001
        continue
      for one in getattr(snapped, "geoms", [snapped]):
        if not one.is_empty and one.is_valid and one.area > 1:
          out.append(one)
  return out


def scaffolded(name: str, aspect: float):
  """A thin weave whose holes have been made tiles.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.

  Returns:
    (thin, filled, filler). EVERY FILLER PIECE TAKES ITS OWN ID: the
    regularising step dissolves by `tile_id`, so pieces sharing one
    become a multi-part tile the library refuses.
  """
  thin = catalog.make_unit(spec_for(name), spacing=SPACING, crs=None,
                           aspect=aspect)
  filler = daylight_of(thin)
  tiles = gpd.GeoDataFrame(
    {"tile_id": list(thin.tiles.tile_id)
                + [f"{FILLER_ID}{i}" for i in range(len(filler))]},
    geometry=list(thin.tiles.geometry) + filler, crs=thin.tiles.crs)
  filled = copy.deepcopy(thin)
  filled.tiles = tiles
  filled._setup_regularised_prototile()
  return thin, filled, filler


def class_counts(topology) -> tuple:
  """How many distinct edge and vertex classes, counted as LABELS.

  Args:
    topology: a built Topology.

  Returns:
    (edges, vertices) as integers.

  NOT `len(te.classes(...))`. That helper joins the labels into one
  string, which counts characters rather than classes the moment any
  label is two letters -- and past twenty-six classes the library
  issues `aa`, `ab`, which is exactly the case this probe reaches.
  """
  edges = {e.label for e in topology.edges.values() if getattr(e, "label", "")}
  points = {v.label for v in topology.points.values()
            if getattr(v, "label", "")}
  return len(edges), len(points)


def whose_vertex_classes(topology, strands, filler) -> tuple:
  """Which vertex classes stand on ground only the FILLER touches.

  Args:
    topology: the built Topology of the filled design.
    strands: the THIN weave's own tiles, passed explicitly.
    filler: the filler polygons.

  Returns:
    (ours, total, labels_ours) over the distinct vertex CLASSES, which
    are what an edit is aimed at. A class is credited to the
    scaffolding where a representative point lies on a filler
    boundary and on NO strand boundary; a vertex where two strands
    already met is the weave's own.

  THIS IS THE NUMBER THE QUESTION TURNS ON for the dual, which has one
  tile per vertex: a dual standing mostly on classes we invented is a
  fact about the filling.
  """
  seen, ours, labels = {}, 0, []
  for vertex in topology.points.values():
    label = getattr(vertex, "label", "")
    if not label or label in seen:
      continue
    seen[label] = vertex
  for label, vertex in sorted(seen.items()):
    point = Point(vertex.point.x, vertex.point.y)
    on_filler = any(p.exterior.distance(point) < ON_EDGE for p in filler)
    on_strand = any(g.exterior.distance(point) < ON_EDGE
                    for g in strands if g.geom_type == "Polygon")
    if on_filler and not on_strand:
      ours += 1
      labels.append(label)
  return ours, len(seen), labels


def measure(name: str, aspect: float) -> dict:
  """Everything one weave at one strand width has to say.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.

  Returns:
    A dict of readings, with `note` carrying the reason where a step
    refused. Nothing raises: a refusal is a reading.
  """
  row = {"name": name, "aspect": aspect, "note": ""}
  thin, filled, filler = scaffolded(name, aspect)
  row["strands"] = len(thin.tiles)
  row["filler"] = len(filler)
  row["tiles"] = len(filled.tiles)
  gap, overlap, _ = te.plane_coverage(filled)
  row["gap"], row["overlap"] = gap, overlap
  topology, why = te.build(filled)
  if topology is None:
    row["note"] = why[:60]
    return row
  row["n_edges"], row["n_vertices"] = class_counts(topology)
  row["edges"], row["vertices"] = row["n_edges"], row["n_vertices"]
  ours, total, _labels = whose_vertex_classes(topology, list(thin.tiles.geometry),
                                              filler)
  row["ours"], row["classes_total"] = ours, total
  try:
    dual = te.complete_dual(topology)
    row["dual"] = None if dual is None else len(dual)
  except Exception as exc:                             # noqa: BLE001
    row["dual"] = None
    row["note"] = f"dual: {type(exc).__name__}"
  return row


def draw(axis, polygons, face, edge="#333333", width=0.6, alpha=1.0):
  """Put polygons on an axis.

  Args:
    axis: the matplotlib axis.
    polygons: shapely geometries; multi-part members are exploded here.
    face: fill colour, or None for outline only.
    edge: outline colour.
    width: outline width.
    alpha: fill transparency.
  """
  for polygon in polygons:
    for part in getattr(polygon, "geoms", [polygon]):
      if part.is_empty or part.geom_type != "Polygon":
        continue
      axis.add_patch(MplPolygon(
        list(part.exterior.coords), closed=True,
        facecolor="none" if face is None else face,
        edgecolor=edge, linewidth=width, alpha=alpha))


def tidy(axis, title):
  """Square the axis, drop its furniture and fit the content.

  Args:
    axis: the matplotlib axis.
    title: what to put above it.
  """
  axis.set_aspect("equal")
  axis.axis("off")
  axis.set_title(title, fontsize=9)
  axis.relim()
  axis.autoscale()


def figure_holes_become_tiles(name: str, aspect: float, path: str) -> None:
  """Figure 1: the weave, its daylight, and the two together as a tiling.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.
    path: where to write the PNG.
  """
  thin, filled, filler = scaffolded(name, aspect)
  strands = list(thin.tiles.geometry)
  figure, axes = plt.subplots(1, 3, figsize=(12, 4.4))
  draw(axes[0], strands, STRAND_FILL)
  tidy(axes[0], f"the weave at aspect {aspect}\n{len(strands)} strand tiles, "
                f"and holes")
  draw(axes[1], filler, FILLER_FILL)
  tidy(axes[1], f"the daylight alone\n{len(filler)} pieces")
  draw(axes[2], filler, FILLER_FILL)
  draw(axes[2], strands, STRAND_FILL)
  tidy(axes[2], f"holes as tiles\n{len(filled.tiles)} tiles, and now a tiling")
  figure.suptitle(f"{name}: a weave becomes a tiling when its holes are tiles",
                  fontsize=10)
  figure.tight_layout()
  figure.savefig(path, dpi=140)
  plt.close(figure)


def figure_across_aspects(name: str, path: str, rows) -> None:
  """Figure 2: the filled design and its dual as the strands thin.

  Args:
    name: the catalogue key.
    path: where to write the PNG.
    rows: the measurements, so the captions cannot drift from them.
  """
  figure, axes = plt.subplots(1, len(ASPECTS), figsize=(4 * len(ASPECTS), 4.6))
  for axis, aspect in zip(axes, ASPECTS):
    thin, _filled, filler = scaffolded(name, aspect)
    topology, _why = te.build(_filled)
    draw(axis, filler, FILLER_FILL, width=0.4)
    draw(axis, list(thin.tiles.geometry), STRAND_FILL, width=0.4, alpha=0.6)
    row = next(r for r in rows if r["aspect"] == aspect)
    if topology is not None:
      dual = te.complete_dual(topology)
      if dual is not None:
        draw(axis, list(dual.geometry), None, edge=DUAL_EDGE, width=1.3)
    tidy(axis, f"aspect {aspect}\n"
               f"{row.get('edges', '-')} edge classes, "
               f"{row.get('vertices', '-')} vertex classes\n"
               f"dual {row.get('dual', '-')} tiles")
  figure.suptitle(f"{name}: the filled design and its dual, as the strands "
                  f"thin. The classes do not move.", fontsize=10)
  figure.tight_layout()
  figure.savefig(path, dpi=140)
  plt.close(figure)


def figure_the_control_at_one(name: str, path: str) -> None:
  """Figure 3: aspect 1.0, where the library fuses and the design changes.

  Args:
    name: the catalogue key.
    path: where to write the PNG.
  """
  thin_low = catalog.make_unit(spec_for(name), spacing=SPACING, crs=None,
                               aspect=0.75)
  solid = catalog.make_unit(spec_for(name), spacing=SPACING, crs=None,
                            aspect=1.0)
  figure, axes = plt.subplots(1, 2, figsize=(8.4, 4.4))
  draw(axes[0], list(thin_low.tiles.geometry), STRAND_FILL)
  tidy(axes[0], f"aspect 0.75\n{len(thin_low.tiles)} strand tiles")
  draw(axes[1], list(solid.tiles.geometry), STRAND_FILL)
  tidy(axes[1], f"aspect 1.0\n{len(solid.tiles)} tiles: same-label pieces "
                f"have FUSED")
  figure.suptitle(f"{name}: going solid is not the same weave", fontsize=10)
  figure.tight_layout()
  figure.savefig(path, dpi=140)
  plt.close(figure)


def halved(piece) -> list:
  """One filler piece cut in two across the middle of its own bounds.

  Args:
    piece: a filler Polygon.

  Returns:
    The two halves, or the piece itself where a half comes back empty
    or multi-part. A second cutting of the SAME ground, which is all
    the control needs: it is not a better filling, only a different
    one.
  """
  from shapely import box
  x0, y0, x1, y1 = piece.bounds
  middle = (x0 + x1) / 2
  out = [piece.intersection(box(x0, y0, middle, y1)),
         piece.intersection(box(middle, y0, x1, y1))]
  kept = [g for g in out
          if not g.is_empty and g.area > 1 and g.geom_type == "Polygon"]
  return kept or [piece]


def classes_under(name: str, aspect: float, cut):
  """The class structure of one weave under one way of cutting its holes.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.
    cut: a function from a filler piece to a list of pieces.

  Returns:
    (thin, pieces, edges, vertices) with the class strings, or the
    strings replaced by None where the design refused.
  """
  thin, _filled, filler = scaffolded(name, aspect)
  pieces = [g for p in filler for g in cut(p)]
  tiles = gpd.GeoDataFrame(
    {"tile_id": list(thin.tiles.tile_id)
                + [f"{FILLER_ID}{i}" for i in range(len(pieces))]},
    geometry=list(thin.tiles.geometry) + pieces, crs=thin.tiles.crs)
  unit = copy.deepcopy(thin)
  unit.tiles = tiles
  unit._setup_regularised_prototile()
  topology, _why = te.build(unit)
  if topology is None:
    return thin, pieces, None, None
  edges, vertices = class_counts(topology)
  return thin, pieces, edges, vertices


def figure_the_filling_decides(name: str, aspect: float, path: str) -> list:
  """Figure 4: the same holes cut two ways, and the classes that follow.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.
    path: where to write the PNG.

  Returns:
    One row per cutting, so the caption cannot drift from the numbers.

  THIS IS THE CONTROL THE WHOLE ARGUMENT RESTS ON. Both cuttings cover
  exactly the same ground and leave the weave untouched, so a
  difference in the classes can only be the filling's.
  """
  rows = []
  figure, axes = plt.subplots(1, 2, figsize=(8.6, 4.6))
  for axis, (label, cut) in zip(axes, (("as the difference gives them", None),
                                       ("each piece cut in half", halved))):
    thin, pieces, edges, vertices = classes_under(
      name, aspect, (lambda p: [p]) if cut is None else cut)
    draw(axis, pieces, FILLER_FILL, width=0.7)
    draw(axis, list(thin.tiles.geometry), STRAND_FILL, width=0.4, alpha=0.6)
    tidy(axis, f"{label}\n{len(pieces)} filler pieces\n"
               f"{edges or 0} edge classes, {vertices or 0} vertex classes")
    rows.append((label, len(pieces), edges, vertices))
  figure.suptitle(f"{name} at aspect {aspect}: the same ground, cut two "
                  f"ways. The classes follow the cutting.", fontsize=10)
  figure.tight_layout()
  figure.savefig(path, dpi=140)
  plt.close(figure)
  return rows


def main() -> None:
  """Measure across aspects, draw, and print the table the write-up quotes."""
  os.makedirs(IMAGES, exist_ok=True)
  print(f"{'weave':18}{'aspect':>7}{'strands':>8}{'filler':>7}{'tiles':>6}"
        f"{'gap':>10}{'overlap':>9}  {'edges':<10}{'vertices':<10}"
        f"{'ours':>5}{'dual':>6}  note")
  everything = {}
  for name in WEAVES:
    rows = []
    for aspect in ASPECTS:
      row = measure(name, aspect)
      rows.append(row)
      print(f"{name:18}{row['aspect']:>7}{row['strands']:>8}{row['filler']:>7}"
            f"{row['tiles']:>6}{row['gap']:>10.6f}{row['overlap']:>9.6f}  "
            f"{row.get('edges', '-'):<10}{row.get('vertices', '-'):<10}"
            f"{row.get('ours', '-'):>5}{str(row.get('dual', '-')):>6}  "
            f"{row['note']}")
    everything[name] = rows
    stable = len({(r.get("edges"), r.get("vertices")) for r in rows}) == 1
    print(f"{'':18}class structure across aspects: "
          f"{'INVARIANT' if stable else 'MOVES'}")
    figure_across_aspects(name, os.path.join(
      IMAGES, f"{name.split()[0]}-across-aspects.png"), rows)
  figure_holes_become_tiles(
    WEAVES[1], 0.75, os.path.join(IMAGES, "holes-become-tiles.png"))
  figure_the_control_at_one(
    WEAVES[1], os.path.join(IMAGES, "solid-is-a-different-design.png"))
  print("\nthe control: the same ground, cut two ways")
  for label, pieces, edges, vertices in figure_the_filling_decides(
      WEAVES[1], 0.5, os.path.join(IMAGES, "the-filling-decides.png")):
    print(f"  {label:32} {pieces:>3} pieces  "
          f"{edges or 0:>4} edge classes  {vertices or 0:>4} vertex classes")
  print(f"\nfigures written to {IMAGES}")


if __name__ == "__main__":
  main()
