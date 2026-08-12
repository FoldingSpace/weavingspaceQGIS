"""Draw the grid of pattern families shown at the top of the pages.

Sixteen designs, eight across and two down, every one of them the SAME
REAL PLACE carrying the SAME REAL VARIABLES. Only the pattern changes
from cell to cell. That is the whole idea: the question a newcomer has
is "what can this look like", and sixteen answers over one dataset
answers it in a way that one dataset in one pattern cannot.

## Why real data, and not sixteen bare tile units

The first version drew the tile units alone -- one repeat of each
family, coloured by element, no data. It was clearer as a diagram and
it broke the rule this project keeps about published images: every
picture on the README and the project page shows real data displayed
as a map, because the plugin's claim is that several attributes of
real PLACES can be read from one map, and a field of coloured shapes
quietly argues the opposite. Tiling Auckland sixteen ways keeps the
claim and the catalogue in one picture, so no exception to the rule is
needed. (User instruction, 2026-08-12.)

## Why every design here has FIVE ELEMENTS OR FEWER

The Auckland file carries five indices of deprivation, and that
constrains the grid -- though to the element COUNT rather than to the
number of cells. A design with seven elements over five variables has
to either repeat a variable, which puts the same data in two places
and invites a reader to compare them, or leave elements blank, which
shows the pattern as full of holes. Neither is what the plugin does
when it is used properly. So the families below are all n <= 5, and
there are comfortably sixteen of those. (Raised by the maintainer,
2026-08-12: "there are only five variables so i assume that
constrains you". It does, and this is the shape of the constraint.)

## Why the colours avoid the pale ends of their ramps

Each element gets its own sequential ramp, and a sequential ramp's low
end is nearly white. At this size a near-white element does not read as
a low value, it reads as a hole: the shape vanishes into the page and
the design looks broken rather than subtle. (User instruction,
2026-08-12.)

The obvious way to fix that is a truncated colormap, and it does not
work. TiledMap checks every name in `colors_to_use` against its own
CMAPS_SEQUENTIAL list and, finding an unknown one, SILENTLY replaces
it with a positional default -- so a registered "Reds starting at
0.35" came back as Greys and Purples with no complaint whatsoever.
That is the second silent substitution in this library that this file
has run into, after the default tile unit below, and both have the
same shape: an invalid request answered with a plausible object
instead of an error.

So the truncation is done through the library's OWN vmins, which is
supported and checked: the floor is set well below each variable's
minimum, which maps the real data into the strong end of a ramp the
library already accepts. Same picture, no lying about colormap names.

## Why a family is verified rather than trusted

An unsupported or under-specified design does not raise. The library
prints a complaint and hands back a DEFAULT unit, which draws
perfectly well and is a different design. An earlier version of this
file wrote its sixteen specifications out by hand, four were missing
arguments their family requires, and the grid rendered four fallback
shapes under four other families' names and reported "16 of 16". So
the specifications come from `catalog.TILINGS_BY_N` -- the same
entries the plugin's chooser offers, arguments included -- and the
element count that arrives is checked against the count promised. A
mismatch is dropped and named, never drawn.

That is the same failure `test_the_catalogue_offers_only_designs_that
_build` exists to catch, reproduced here by going around the catalogue
instead of through it.

## Running it

Needs geopandas AND matplotlib, so it runs in the reference
environment rather than under QGIS's Python (macOS code-signing
refuses PyPI C extensions inside the signed QGIS process):

    ./.venv-reference/bin/python3 tools/make_pattern_grid.py

`tools/make_site_images.py` calls it while retaking the published
pictures, so the grid is regenerated with everything else at each
release. A published picture nobody regenerates keeps its authority
while losing its accuracy.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# the vendored library, and the repository itself for catalog.py
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))
sys.path.insert(0, ROOT)

OUT = os.path.join(ROOT, "docs", "img", "patterns.png")
REGION = os.path.join(ROOT, "tests", "data", "imd-auckland-sa2-2018.gpkg")

COLS, ROWS = 8, 2

# Which family fills each cell, as (catalogue name prefix, element
# count). Chosen to span the KINDS rather than to be the prettiest
# sixteen -- slices, colourings, crosses, stars, the Laves and
# Archimedean tilings, the grid and stripe extras, and three weaves --
# so somebody scanning the two rows comes away knowing the catalogue
# holds more than one idea. Every count is five or fewer; see above.
# ORDERED so that neighbours are neighbours: the sequence runs
# slices -> dissections -> colourings -> crosses -> stars -> the
# Laves and Archimedean tilings -> grid and stripes -> weaves, and
# within a family by element count. A reader moving along the row
# then sees one thing change at a time instead of jumping between
# unrelated ideas, which is what lets them tell what the FAMILY does
# as against what the element count does.
WANTED = [
  ("hex-slice", 3), ("hex-slice", 5), ("square-slice", 4),
  ("square-dissection", 5), ("hex-colouring", 5),
  ("square-colouring", 4), ("crosses", 3), ("crosses", 5),
  ("star1", 3), ("star2", 3), ("laves", 4), ("archimedean", 3),
  ("grid", 4), ("stripes", 5), ("plain weave", 3),
  ("twill weave", 4),
]

# How much of the region's extent each cell shows, as a fraction.
# Two things are traded here and neither wins outright. Too wide and
# the pattern is a haze, so the cell shows that a design exists
# without showing what it IS. Too tight and every tile is legible but
# they are all one colour, so the map looks like a texture rather than
# like data -- and the thing worth seeing is that deprivation in
# Auckland comes in PATCHES, which needs enough ground on screen for
# the patches to appear. Landed at two thirds after both extremes
# were looked at. (User instructions, 2026-08-12: zoom in a little
# more so we can see; then zoom out a little and increase the spacing
# so we get some regionalization, spatial autocorrelation visible.)
ZOOM = 0.68

# Each TILING is turned by a small angle, so the grid does not read as
# sixteen designs all obediently square to the page -- a tiling's
# orientation is a real control (mod_rotate in the dialog) and a
# catalogue that never uses it under-sells the family. Drawn from
# -45..45 and rounded to 15, so the angles look chosen rather than
# jittered. WEAVES are left alone: their strands carry direction as
# part of what the design MEANS, and turning one says something the
# other cells do not.
#
# Seeded from the family's own name rather than from the clock, so
# the picture is the same every time it is regenerated. A published
# image that reshuffles itself each release would show up as a diff in
# every release commit and teach everybody to ignore the diff.
ROTATION_CHOICES = [-45, -30, -15, 0, 15, 30, 45]

# All five are indices of deprivation for the same Auckland areas, so
# every cell is the same place saying the same things in a different
# pattern. Never repeated within a cell, which is why the counts above
# stop at five.
#
# The ramp is bound to the VARIABLE, not to the element position, and
# that binding is the point of the whole grid. Deprivation is red in
# every cell; income is green in every cell. A reader can therefore
# carry what they learned from one pattern into the next and see the
# same place through sixteen different arrangements of the same
# information -- which is the argument the plugin exists to make. Bind
# by position instead and the first element of a three-element design
# and of a five-element design share a colour while showing different
# data, and the grid becomes sixteen unrelated pictures.
# (User instruction, 2026-08-12: make the variables as comparable
# between examples as possible.)
# NO RED. The obvious five sequential ramps put Reds beside Greens,
# and red against green is the pair a red-green deficient reader
# cannot separate -- roughly one man in twelve. Mitigating it would
# mean tuning the two until they were just about distinguishable;
# removing red removes the confusion at its source, and the remaining
# hues span blue, orange, purple, grey and green with no pair that
# collapses. This is the same concern the plugin's own legibility
# warning exists for, and a grid arguing for multivariate colour that
# some readers cannot read would be arguing against itself.
# (User instruction, 2026-08-12.)
# Oranges was here and had to go: it is the highest-chroma hue in the
# set and it advanced against the blues, purples and greys hard enough
# that every cell read as an orange map with other things in it. That
# is a failure of the grid's whole purpose -- five variables shown as
# equals -- so the fix is a calmer warm ramp rather than a tweak to
# the floor, which would only have made the orange darker.
# YlOrBr was tried next and was no better: its middle is bright gold,
# which advances just as hard. What works is a genuinely low-chroma
# warm -- copper, muted brown -- and REVERSED, so that high values are
# dark as they are on every other ramp here. Unreversed it runs dark
# to light, which would have made this the one variable where a big
# number looked pale.
# (User instruction, 2026-08-12: the oranges are too overdominant.)
VARIABLE_RAMPS = {
  "imd": "Blues",
  "employment": "copper_r",
  "income": "Purples",
  "crime": "Greys",
  "housing": "Greens",
}
VARIABLES = list(VARIABLE_RAMPS)

# How far BELOW the data's own minimum to put the colour scale's floor,
# as a fraction of the data's range. At 0.55 the real values occupy
# roughly the top two thirds of each ramp, which is dark enough to read
# at this size while leaving plenty of range in play. Done this way
# rather than with a truncated colormap because the library rejects
# colormap names it does not recognise -- silently. See the docstring.
RAMP_FLOOR = 0.55


def colour_floor(values):
  """The vmin that keeps this variable off the pale end of its ramp.

  Args:
    values: the column being mapped, as a pandas Series.

  Returns:
    A number below the data's minimum, far enough that the real values
    land in the strong part of the ramp rather than starting at
    near-white. None when the column is empty or constant, where there
    is no range to push and matplotlib's own default is right.

  This is the supported way to do what a truncated colormap would do.
  TiledMap silently replaces a colormap name it does not recognise, so
  registering "Reds from 0.35" produces Greys with no warning; vmins
  is part of its own interface and is honoured.
  """
  low, high = values.min(), values.max()
  if low is None or high is None or high == low:
    return None
  return low - RAMP_FLOOR * (high - low)


def chosen_entries():
  """One catalogue entry per wanted family, in grid order.

  Returns:
    A list of (label, spec, elements) from ``catalog.TILINGS_BY_N``, so
    every spec carries whatever arguments its family requires. A
    family absent at the count asked for is reported and skipped
    rather than guessed at, because guessing is how the hand-written
    version produced four impostors.
  """
  from weavingspace_qgis import catalog
  found = []
  for prefix, count in WANTED:
    families = catalog.TILINGS_BY_N.get(count, {})
    name = next((k for k in families if k.startswith(prefix)), None)
    if name is None:
      print(f"  no '{prefix}' at {count} elements; skipped")
      continue
    found.append((name, families[name], count))
  return found


def rotation_for(label):
  """The angle this family is drawn at, stable across regenerations.

  Args:
    label: the catalogue name, e.g. "hex-slice 3".

  Returns:
    One of ROTATION_CHOICES, chosen by hashing the name rather than by
    a random draw, so the same family always comes out at the same
    angle. Regenerating the grid must produce the same picture, or
    every release carries a diff nobody can review and everybody
    learns to wave through.
  """
  import hashlib
  digest = hashlib.sha256(label.encode("utf-8")).digest()
  return ROTATION_CHOICES[digest[0] % len(ROTATION_CHOICES)]


def unit_for(label, spec, spacing, elements):
  """Build one tile unit, and refuse a substituted default.

  Args:
    label: the catalogue's own name for the family, used in messages.
    spec: that family's entry from TILINGS_BY_N.
    spacing: the unit size in map units (metres here, EPSG:2193).
    elements: how many elements the catalogue promises, which is the
      key it was found under. Deliberately NOT spec["n"]: for a weave
      that key is the over-under pattern, so comparing against it
      declared three perfectly good weaves to be substituted defaults
      because a "plain weave ab|c" carries n=1 and three elements.

  Returns:
    A Tileable, or None when what came back is not the family asked
    for. The check is the ELEMENT COUNT, because an unsupported
    request does not raise -- it prints a complaint and substitutes a
    default unit, and a substitute draws just as happily as the real
    thing.
  """
  from weavingspace_qgis import catalog
  try:
    unit = catalog.make_unit(spec, spacing=spacing, crs=2193)
  except Exception as trouble:                   # noqa: BLE001
    print(f"  dropped {label}: {trouble}")
    return None
  actual = len(set(unit.tiles.tile_id))
  if actual != elements:
    print(f"  dropped {label}: asked for {elements} elements and the "
          f"library built {actual}, so this is a substituted default "
          f"rather than the family it would be labelled as")
    return None
  # Tilings only: a weave's strand direction is part of its meaning.
  # Applied AFTER the element-count check, so a rotation can never be
  # what makes a substituted default look like the real thing.
  if spec.get("type") == "tiling":
    angle = rotation_for(label)
    if angle:
      unit = unit.transform_rotate(angle)
  return unit


def draw_cell(png, unit, region, label, window):
  """Tile the region with one unit and render it to its own PNG.

  Args:
    png: where to write this cell's image.
    unit: the Tileable to lay across the region.
    region: the GeoDataFrame being mapped, carrying VARIABLES.
    label: the family's catalogue name, for the failure message.
      window: (minx, miny, maxx, maxy) in the region's own
        coordinates. EVERY cell is drawn to this same window, which is
        the whole reason the grid reads as one place: the coastline
        falls in the same spot in all sixteen, so a viewer sees
        immediately that only the pattern changed. Letting each cell
        frame itself put the same edge in sixteen different places and
        the grid looked like sixteen datasets.

  Returns:
    True when something was drawn, False otherwise. A tiling that
    produces nothing must not pass as a blank cell: in a grid of
    sixteen, white reads as a pattern that draws nothing rather than
    as a step that was skipped.

  Elements take the first N variables in a fixed order, and each
  variable brings its OWN ramp, so deprivation is red in every cell of
  the grid and income is green in every cell. That is what makes the
  sixteen comparable rather than merely sixteen: a reader carries what
  they learned from one pattern straight into the next.
  """
  import matplotlib.pyplot as plt
  from weavingspace import Tiling
  tiled = Tiling(unit, region).get_tiled_map()
  ids = sorted(set(unit.tiles.tile_id))
  tiled.ids_to_map = ids
  # the first len(ids) variables, each with ITS OWN ramp, so the same
  # variable wears the same colour in every cell of the grid
  shown = VARIABLES[:len(ids)]
  tiled.vars_to_map = shown
  tiled.colors_to_use = [VARIABLE_RAMPS[v] for v in shown]
  # the floor comes from the WHOLE region, not from the tiles this
  # design happens to produce, so a coarse pattern and a fine one put
  # the same value at the same colour -- which is the comparability
  # the grid exists for
  tiled.vmins = [colour_floor(region[v]) for v in shown]
  if getattr(tiled, "map", None) is None or len(tiled.map) == 0:
    print(f"  dropped {label}: the tiling produced no tiles")
    return False
  # TiledMap.render builds and owns its own figure -- it takes no axes
  # -- so each cell is rendered separately and the sixteen are pasted
  # into a grid afterwards. Fighting the library for control of the
  # figure would mean reaching into the renderer this project
  # deliberately treats as the reference.
  figure = tiled.render(legend=False, figsize=(3, 3))
  minx, miny, maxx, maxy = window
  for cell in figure.axes:
    cell.set_axis_off()
    cell.set_xlim(minx, maxx)
    cell.set_ylim(miny, maxy)
    cell.set_aspect("equal")
  # NOT bbox_inches="tight": tight re-crops to whatever each cell
  # happens to contain, which would undo the shared window above and
  # hand every design its own framing again.
  figure.subplots_adjust(left=0, right=1, top=0, bottom=0)
  figure.savefig(png, dpi=110, facecolor="white", pad_inches=0)
  # closed explicitly: sixteen figures left to the garbage collector
  # would sit in matplotlib's global registry and warn partway through
  plt.close(figure)
  return True


def main():
  """Draw the grid and write it to docs/img/patterns.png.

  Returns:
    0 when every cell was drawn, 1 when any family was dropped. The
    grid is written either way, because a page with fourteen patterns
    beats a page with none -- but the exit status says the picture and
    the catalogue have diverged, so a release cannot publish a short
    grid without anybody being told.

  Raises:
    SystemExit: when the region file has lost one of the columns the
      grid maps. Drawing it anyway would produce sixteen cells that
      are no longer the same place saying the same things.
  """
  import geopandas
  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt

  region = geopandas.read_file(REGION)
  missing = [v for v in VARIABLES if v not in region.columns]
  if missing:
    raise SystemExit(
      f"{REGION} does not carry {missing}; this grid shows one place "
      f"saying the same things sixteen ways and cannot if the columns "
      f"have been renamed")
  if len(WANTED) != COLS * ROWS:
    raise SystemExit(
      f"{len(WANTED)} families for {COLS}x{ROWS} cells; the grid would "
      f"come out short or over-full")

  # Coarse relative to the region, so each cell shows the PATTERN
  # rather than a haze of tiny tiles. Derived from the region's own
  # extent rather than written as a number, so a different dataset
  # dropped in here still produces legible cells.
  extent = max(region.total_bounds[2] - region.total_bounds[0],
               region.total_bounds[3] - region.total_bounds[1])
  # Coarser than it first was: bigger tiles over more ground means
  # each tile averages a larger area, and neighbouring tiles then
  # agree with each other where the underlying pattern is regional.
  # That agreement -- the visible clumping of like with like -- is
  # what a reader should take away, because it is the property that
  # makes a tiled multivariate map worth drawing at all.
  spacing = extent / 15

  # The one window every cell is drawn to. Square, centred on the
  # region, and ZOOM of its longer side -- so the same ground, at the
  # same scale, in the same place, sixteen times over.
  midx = (region.total_bounds[0] + region.total_bounds[2]) / 2
  midy = (region.total_bounds[1] + region.total_bounds[3]) / 2
  half = extent * ZOOM / 2
  window = (midx - half, midy - half, midx + half, midy + half)

  import tempfile
  from PIL import Image

  entries = chosen_entries()
  scratch = tempfile.mkdtemp(prefix="weavingspace-grid-")
  cells, drawn = [], 0
  for index, (label, spec, elements) in enumerate(entries):
    unit = unit_for(label, spec, spacing, elements)
    png = os.path.join(scratch, f"cell{index}.png")
    if unit is not None and draw_cell(png, unit, region, label, window):
      cells.append(png)
      drawn += 1

  # Square-cropped to a common size and butted together with a hair of
  # white between, so the grid reads as one object rather than as
  # sixteen pictures that happen to be adjacent.
  SIDE, GAP = 300, 6
  width = COLS * SIDE + (COLS - 1) * GAP
  height = ROWS * SIDE + (ROWS - 1) * GAP
  sheet = Image.new("RGB", (width, height), "#ffffff")
  for index, png in enumerate(cells[:COLS * ROWS]):
    # No per-cell cropping: the shared window already framed them
    # identically, and cropping here by anything but the same amount
    # would put the coastline back in sixteen different places.
    tile = Image.open(png).convert("RGB")
    side = min(tile.size)
    tile = tile.crop(((tile.width - side) // 2, (tile.height - side) // 2,
                      (tile.width + side) // 2, (tile.height + side) // 2))
    tile = tile.resize((SIDE, SIDE), Image.LANCZOS)
    # BOUSTROPHEDON: the second row runs right to left, so the eighth
    # design sits directly above the ninth and the sequence never
    # jumps the width of the page between two neighbours. Reading it
    # as a plain grid still works; reading it as a path works better.
    row = index // COLS
    col = index % COLS if row % 2 == 0 else COLS - 1 - (index % COLS)
    sheet.paste(tile, (col * (SIDE + GAP), row * (SIDE + GAP)))
  sheet.save(OUT)
  print(f"wrote {OUT}: {drawn} of {len(WANTED)} families drawn")
  return 0 if drawn == len(WANTED) else 1


if __name__ == "__main__":
  sys.exit(main())
