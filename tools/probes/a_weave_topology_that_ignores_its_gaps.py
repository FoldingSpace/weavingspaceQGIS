"""Can a weave's structure be read across its gaps rather than through them?

The scaffolded topology of a thin weave depends on how we cut its holes:
the same ground cut two ways gives six edge classes or well over a
hundred (docs/process/the-topology-of-a-weave-and-its-holes.md). That
makes the classes a property of our filling as much as of the weave,
which is a poor foundation for aiming an edit.

THE PROPOSAL THIS PROBE TESTS (the maintainer's, 2026-09-08) is to use
the filling as an INTERMEDIATE step and then contract it. Two strands
separated only by the daylight that strand WIDTH opens are the same
fabric and should count as sharing an edge; a strand the person
deliberately left out, marked by a hyphen in the strands code, is a
real absence and nothing should connect across it. `daylight_by_kind`
already tells those two apart.

WHY IT SHOULD WORK: the CONNECTED COMPONENTS of the daylight are
intrinsic to the region, where the pieces a boolean difference hands
back are not. Contracting through components is therefore
decomposition-free BY CONSTRUCTION -- the parts are unioned before the
components are taken -- and that is a property of the rule rather than
a result, so it is stated here and not dressed up as an experiment.

WHAT IS NOT free, and is therefore worth measuring, is whether the
structure survives changing the design's geometry. Varying the strand
width moves every coordinate and, on a twill at aspect 0.25, changes
how many components the daylight even has. If the contracted structure
stands still through that, it is telling us something about the weave.

WHAT IT MEASURES:

  the components of each kind of daylight, which is what gets contracted
  the contracted adjacency on the strand tiles: how many pairs, and the
    degree sequence, which together fingerprint the structure
  whether that fingerprint moves as the strand width varies
  what cutting a component before contracting costs, which is why the
    rule must take them whole
  and, on weaves whose codes carry hyphens, whether honouring the
    conscious gap ever changes the answer -- a distinction that changes
    nothing would be idle

Run it in the reference venv, under the watchdog:

    python3 tools/watchdog.py --stall 300 --timeout 3600 -- \
      ./.venv-reference/bin/python3 \
      tools/probes/a_weave_topology_that_ignores_its_gaps.py

NO TIMINGS ARE TAKEN; every figure is structural.
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
ASPECTS = (0.9, 0.75, 0.5, 0.25)
PLAIN = "plain weave a|b"
TWILL = "twill weave a|b"
HYPHENS = ("twill weave a|b-", "plain weave ab-|cd-",
           "twill weave ab-|cd-")
IMAGES = os.path.join(HERE, "docs", "process", "images", "holes-as-tiles")
# A shared boundary shorter than this is a touching point rather than a
# shared edge. Sized well below a strand's width and well above the
# library's own precision of 1e-06.
A_SEGMENT = 1.0

STRAND_FILL = "#4c72b0"
WIDTH_FILL = "#dcdcdc"
CONSCIOUS_FILL = "#f0c987"
LINK = "#c44e52"


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


def parts_of(geometry) -> list:
  """A geometry's non-trivial polygonal components.

  Args:
    geometry: any shapely geometry, possibly empty or multi-part.

  Returns:
    A list of Polygons, slivers under a square unit dropped.
  """
  if geometry is None or geometry.is_empty:
    return []
  return [g for g in getattr(geometry, "geoms", [geometry])
          if g.geom_type == "Polygon" and not g.is_empty and g.area > 1]


def daylight_components(unit, name: str, aspect: float) -> tuple:
  """The two kinds of daylight, each as its own connected components.

  Args:
    unit: the thin weave.
    name: its catalogue key, for the spec `daylight_by_kind` needs.
    aspect: the strand width it was built at.

  Returns:
    (width_components, conscious_components). The components are taken
    from the UNION of each kind, so they are intrinsic to the region
    rather than to any cutting of it -- which is the whole point of
    contracting through them.
  """
  kinds = te.daylight_by_kind(unit, spec_for(name), SPACING, aspect)
  width = shapely.union_all(parts_of(kinds["width"]) or [shapely.Polygon()])
  conscious = shapely.union_all(
    parts_of(kinds["conscious"]) or [shapely.Polygon()])
  return parts_of(width), parts_of(conscious)


def touching(tile, region) -> bool:
  """Whether a tile shares an EDGE with a region, not merely a point.

  Args:
    tile: a strand polygon.
    region: a daylight component.

  Returns:
    True where their boundaries share more than `A_SEGMENT` of length.
    A shared point is a corner meeting, which should not by itself make
    two strands neighbours.
  """
  shared = tile.boundary.intersection(region.boundary)
  return (not shared.is_empty) and shared.length > A_SEGMENT


def contracted_adjacency(strands, bridges) -> set:
  """Which strand tiles are neighbours once the daylight is contracted.

  Args:
    strands: the weave's own tiles.
    bridges: the daylight components an edit may travel across.

  Returns:
    A set of index pairs. Two strands are neighbours where they already
    share an edge, or where both share an edge with one bridge -- the
    second being the contraction, which reads a gap as an
    identification rather than as a separation.
  """
  pairs = set()
  for i, one in enumerate(strands):
    for j in range(i + 1, len(strands)):
      shared = one.boundary.intersection(strands[j].boundary)
      if (not shared.is_empty) and shared.length > A_SEGMENT:
        pairs.add((i, j))
  for bridge in bridges:
    around = [i for i, tile in enumerate(strands) if touching(tile, bridge)]
    for a_index, i in enumerate(around):
      for j in around[a_index + 1:]:
        pairs.add((min(i, j), max(i, j)))
  return pairs


def abuts(region, other, reach: float = 1e-2) -> bool:
  """Whether two daylight regions lie against one another.

  Args:
    region: a width-daylight component.
    other: a conscious-gap component.
    reach: how far apart they may be and still count as touching.

  Returns:
    True where they come within `reach`.

  NOT a boundary intersection. `daylight_by_kind` returns the width
  daylight as the difference of the whole daylight and the conscious
  gap BUFFERED BY A WHISKER, so the two regions are held about a
  millionth of a unit apart by construction and their boundaries never
  meet. A veto written on boundary contact therefore fired zero times
  on three weaves, which is the uniform verdict that names the
  instrument rather than the design. Distance answers the question the
  veto is actually asking.
  """
  return region.distance(other) <= reach


def adjacency_with_a_veto(strands, width, conscious) -> tuple:
  """Adjacency where a dropped strand PROHIBITS a join, rather than
  merely failing to make one.

  Args:
    strands: the weave's own tiles.
    width: the components of the daylight strand width opens.
    conscious: the components a hyphen in the code leaves empty.

  Returns:
    (pairs, vetoed_bridges) -- the adjacency, and how many width
    components were refused as bridges.

  WHY A VETO RATHER THAN AN OMISSION. (Maintainer's proposal,
  2026-09-08.) Simply not bridging across conscious ground changes
  nothing measurable: the strands either side of a dropped strand turn
  out to be joined by some other route anyway. But the ground beside a
  dropped strand is geometrically indistinguishable from ordinary
  daylight while meaning something else, and a rule that reads it as
  ordinary will join strands the person deliberately separated. So a
  width component that ABUTS conscious ground is refused as a bridge:
  the hyphen prohibits the connection instead of leaving it to be made
  by a gap that merely looks equivalent.

  Direct contact is never vetoed. Two strands whose boundaries actually
  meet are neighbours whatever lies elsewhere in the design.
  """
  pairs = set()
  for i, one in enumerate(strands):
    for j in range(i + 1, len(strands)):
      shared = one.boundary.intersection(strands[j].boundary)
      if (not shared.is_empty) and shared.length > A_SEGMENT:
        pairs.add((i, j))
  vetoed = 0
  for bridge in width:
    if any(abuts(bridge, gap) for gap in conscious):
      vetoed += 1
      continue
    around = [i for i, tile in enumerate(strands) if touching(tile, bridge)]
    for a_index, i in enumerate(around):
      for j in around[a_index + 1:]:
        pairs.add((min(i, j), max(i, j)))
  return pairs, vetoed


def adjacency_with_a_targeted_veto(strands, width, conscious) -> tuple:
  """Adjacency where a dropped strand vetoes only the pairs it lies BETWEEN.

  Args:
    strands: the weave's own tiles.
    width: the components of the daylight strand width opens.
    conscious: the components a hyphen in the code leaves empty.

  Returns:
    (pairs, withheld) -- the adjacency, and the pairs the veto removed.

  BETWEEN THE TWO RULES THAT BRACKET THE ANSWER. Declining to bridge
  across conscious ground changes nothing, because the fabric routes
  around a dropped strand; refusing every width component that abuts
  conscious ground refuses almost all of them, since the empty slot is
  a long band that most of the daylight touches somewhere, and it
  isolates most of the strands. This asks the narrower question the
  proposal is really about: does the dropped strand lie BETWEEN these
  two strands? The segment joining their nearest points is tested
  against the conscious ground, so a join is refused exactly where
  taking it would cross the slot the person left empty.

  Direct contact is never vetoed.
  """
  from shapely import LineString, ops
  pairs, withheld = set(), []
  for i, one in enumerate(strands):
    for j in range(i + 1, len(strands)):
      shared = one.boundary.intersection(strands[j].boundary)
      if (not shared.is_empty) and shared.length > A_SEGMENT:
        pairs.add((i, j))
  for bridge in width:
    around = [i for i, tile in enumerate(strands) if touching(tile, bridge)]
    for a_index, i in enumerate(around):
      for j in around[a_index + 1:]:
        pair = (min(i, j), max(i, j))
        if pair in pairs:
          continue
        near = ops.nearest_points(strands[i], strands[j])
        between = LineString([near[0], near[1]])
        if any(between.intersects(gap) for gap in conscious):
          withheld.append(pair)
          continue
        pairs.add(pair)
  return pairs, sorted(set(withheld) - pairs)


def fingerprint(strands, pairs) -> str:
  """A short, comparable summary of a contracted structure.

  Args:
    strands: the weave's own tiles.
    pairs: the adjacency from `contracted_adjacency`.

  Returns:
    A string giving the tile count, the pair count and the sorted
    degree sequence. Two structures with the same fingerprint are not
    proved isomorphic, but a DIFFERENCE is proof they are not the same,
    which is what the control needs.
  """
  degree = [0] * len(strands)
  for i, j in pairs:
    degree[i] += 1
    degree[j] += 1
  return (f"{len(strands)} strands, {len(pairs)} adjacent pairs, "
          f"degrees {sorted(degree)}")


def read(name: str, aspect: float, cut=None) -> dict:
  """Everything one weave at one strand width has to say, contracted.

  Args:
    name: the catalogue key.
    aspect: strand width as a fraction of the spacing.
    cut: an optional function applied to each width component before
      contracting, so a DIFFERENT cutting of identical ground can be
      compared. None leaves the components whole.

  Returns:
    A dict of readings, including the fingerprint the control compares.
  """
  unit = catalog.make_unit(spec_for(name), spacing=SPACING, crs=None,
                           aspect=aspect)
  strands = [g for g in unit.tiles.geometry if g.geom_type == "Polygon"]
  width, conscious = daylight_components(unit, name, aspect)
  bridges = width if cut is None else [p for w in width for p in cut(w)]
  pairs = contracted_adjacency(strands, bridges)
  through_all = contracted_adjacency(strands, bridges + conscious)
  return {"aspect": aspect, "strands": len(strands),
          "width_parts": len(width), "conscious_parts": len(conscious),
          "pairs": pairs, "through_all": through_all,
          "fingerprint": fingerprint(strands, pairs),
          "unit": unit, "tiles": strands,
          "width": width, "conscious": conscious}


def halved(piece) -> list:
  """One component cut in two across the middle of its own bounds.

  Args:
    piece: a daylight component.

  Returns:
    The two halves, or the piece where a half comes back unusable. A
    second cutting of the SAME ground: not a better one, only different.
  """
  x0, y0, x1, y1 = piece.bounds
  middle = (x0 + x1) / 2
  out = [piece.intersection(shapely.box(x0, y0, middle, y1)),
         piece.intersection(shapely.box(middle, y0, x1, y1))]
  kept = [g for g in out
          if not g.is_empty and g.area > 1 and g.geom_type == "Polygon"]
  return kept or [piece]


def draw_structure(axis, reading, title: str) -> None:
  """Draw the strands, the two kinds of daylight, and the contraction.

  Args:
    axis: the matplotlib axis.
    reading: one `read` result.
    title: what to put above it.
  """
  for polygon in reading["width"]:
    axis.add_patch(MplPolygon(list(polygon.exterior.coords), closed=True,
                              facecolor=WIDTH_FILL, edgecolor="#bbbbbb",
                              linewidth=0.4))
  for polygon in reading["conscious"]:
    axis.add_patch(MplPolygon(list(polygon.exterior.coords), closed=True,
                              facecolor=CONSCIOUS_FILL, edgecolor="#c8a15a",
                              linewidth=0.6))
  for polygon in reading["tiles"]:
    axis.add_patch(MplPolygon(list(polygon.exterior.coords), closed=True,
                              facecolor=STRAND_FILL, edgecolor="#20304a",
                              linewidth=0.4, alpha=0.85))
  centres = [t.representative_point() for t in reading["tiles"]]
  for i, j in reading["pairs"]:
    axis.plot([centres[i].x, centres[j].x], [centres[i].y, centres[j].y],
              color=LINK, linewidth=1.0, zorder=5)
  for point in centres:
    axis.plot([point.x], [point.y], marker="o", markersize=2.5,
              color=LINK, zorder=6)
  axis.set_aspect("equal")
  axis.axis("off")
  axis.set_title(title, fontsize=9, pad=8)
  axis.relim()
  axis.autoscale()


def figure_across_aspects(name: str, readings, path: str) -> None:
  """Figure: the contracted structure as the strands thin.

  Args:
    name: the catalogue key.
    readings: one `read` result per aspect.
    path: where to write the PNG.
  """
  figure, axes = plt.subplots(1, len(readings), figsize=(4 * len(readings), 4.4))
  for axis, reading in zip(axes, readings):
    draw_structure(axis, reading,
                   f"aspect {reading['aspect']}\n"
                   f"{reading['width_parts']} gaps contracted\n"
                   f"{len(reading['pairs'])} adjacent pairs")
  figure.suptitle(f"{name}: strands joined across the daylight that width "
                  f"opens. The structure does not move.", fontsize=10)
  figure.tight_layout(rect=(0, 0, 1, 0.88))
  figure.savefig(path, dpi=140)
  plt.close(figure)


def figure_the_hyphen_is_respected(name: str, path: str) -> tuple:
  """Figure: a conscious gap left uncontracted, beside one contracted.

  Args:
    name: a catalogue key whose strands code carries a hyphen.
    path: where to write the PNG.

  Returns:
    (honouring, ignoring, added) -- the two fingerprints and the pairs
    that appear only when every gap is read across.
  """
  reading = read(name, 0.75)
  figure, axes = plt.subplots(1, 2, figsize=(8.6, 4.6))
  draw_structure(axes[0], reading,
                 f"the hyphen respected\n{len(reading['pairs'])} pairs")
  ignoring = dict(reading)
  ignoring["pairs"] = reading["through_all"]
  draw_structure(axes[1], ignoring,
                 f"contracting every gap\n{len(reading['through_all'])} pairs")
  figure.suptitle(f"{name}: a dropped strand is an absence, not a gap "
                  f"to read across", fontsize=10)
  figure.tight_layout(rect=(0, 0, 1, 0.88))
  figure.savefig(path, dpi=140)
  plt.close(figure)
  return (fingerprint(reading["tiles"], reading["pairs"]),
          fingerprint(reading["tiles"], reading["through_all"]),
          sorted(reading["through_all"] - reading["pairs"]))


def main() -> None:
  """Test the proposal: across aspects, against a second cutting, and on a hyphen."""
  os.makedirs(IMAGES, exist_ok=True)
  for name in (PLAIN, TWILL):
    print(f"\n=== {name}: contracting the width daylight ===")
    readings = []
    for aspect in ASPECTS:
      reading = read(name, aspect)
      readings.append(reading)
      print(f"  aspect {aspect:<5} {reading['width_parts']:>3} width gaps  "
            f"{reading['conscious_parts']:>2} conscious   "
            f"{reading['fingerprint']}")
    stable = len({r["fingerprint"] for r in readings}) == 1
    print(f"  across aspects: {'INVARIANT' if stable else 'MOVES'}")
    figure_across_aspects(name, readings, os.path.join(
      IMAGES, f"{name.split()[0]}-contracted.png"))

  print("\n=== why the components must be taken WHOLE ===")
  print("  Contracting through the components of the daylight is")
  print("  decomposition-free BY CONSTRUCTION: the pieces are unioned")
  print("  before the components are taken, so no cutting of them can")
  print("  survive into the answer. What is NOT free is taking them")
  print("  whole, and cutting a component before contracting shows why.")
  for name in (PLAIN, TWILL):
    whole = read(name, 0.5)
    cut = read(name, 0.5, cut=halved)
    print(f"  {name}")
    print(f"    components whole   : {whole['fingerprint']}")
    print(f"    each cut in half   : {cut['fingerprint']}")
    print(f"    {'the halves lose adjacency, so the rule must take components whole' if whole['fingerprint'] != cut['fingerprint'] else 'unchanged here, which does not make the requirement idle'}")

  print("\n=== is a dropped strand ever a gap that separates? ===")
  for name in HYPHENS:
    slug = name.replace(" ", "-").replace("|", "_")
    honouring, ignoring, added = figure_the_hyphen_is_respected(
      name, os.path.join(IMAGES, f"hyphen-{slug}.png"))
    print(f"  {name}")
    print(f"    hyphen respected : {honouring}")
    print(f"    every gap joined : {ignoring}")
    print(f"    pairs the hyphen withholds: {len(added)} {added[:6]}")

  print("\n=== a hyphen as a VETO rather than an omission ===")
  print("  Not bridging across conscious ground changes nothing, because")
  print("  the strands either side are joined some other way. Refusing a")
  print("  width component that ABUTS conscious ground is the stronger")
  print("  rule: the hyphen prohibits a join that a gap which merely")
  print("  looks equivalent would otherwise make.")
  for name in HYPHENS:
    reading = read(name, 0.75)
    vetoed_pairs, vetoed = adjacency_with_a_veto(
      reading["tiles"], reading["width"], reading["conscious"])
    withheld = sorted(reading["pairs"] - vetoed_pairs)
    print(f"  {name}")
    print(f"    no veto      : {fingerprint(reading['tiles'], reading['pairs'])}")
    print(f"    with the veto: {fingerprint(reading['tiles'], vetoed_pairs)}")
    print(f"    {vetoed} of {len(reading['width'])} width components refused; "
          f"{len(withheld)} pairs withheld")
    aimed, aimed_withheld = adjacency_with_a_targeted_veto(
      reading["tiles"], reading["width"], reading["conscious"])
    print(f"    targeted veto: {fingerprint(reading['tiles'], aimed)}")
    print(f"      the dropped strand lies between "
          f"{len(aimed_withheld)} pair(s) {aimed_withheld[:6]}")

  print(f"\nfigures written to {IMAGES}")


if __name__ == "__main__":
  main()
