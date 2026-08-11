"""Conversion between QGIS layers and GeoDataFrames, plus symbology.

This module is the translation layer between the two data worlds:

* weavingspace's world: geopandas GeoDataFrames of shapely geometries,
  where the tiling itself happens;
* QGIS's world: QgsVectorLayer objects, each a schema (``fields()``)
  plus features (rows with a geometry and attribute values) served by a
  *data provider* ("memory" = held in RAM, "ogr" = read from a file
  such as a GeoPackage), and rendered by a *renderer* object attached
  to the layer.

The exchange format between the worlds is WKB (well-known binary), a
standard byte encoding of geometry that both shapely and QGIS speak
natively, so no coordinates are ever reinterpreted by hand.

Output model: one layer per tile element (tile_id), each given a
*standard* QGIS renderer as its initial symbology (graduated classes
for numeric variables, categorized classes for nominal ones,
single-colour otherwise) so all refinement happens in QGIS's normal
styling tools. The relevant QGIS renderer classes:

* QgsSingleSymbolRenderer: one symbol for every feature;
* QgsGraduatedSymbolRenderer: numeric field sliced into class ranges,
  each range coloured from a colour ramp;
* QgsCategorizedSymbolRenderer: one entry per distinct field value.

Colour ramps come from the user's QGIS style library (QgsStyle, a
sqlite database of named symbols/ramps shared by all of QGIS); the web
app's matplotlib palettes are installed into it once, under their
original names, tagged 'mapweaver', so both worlds use the same names.
"""

from __future__ import annotations

import json
import math
import os

from qgis.PyQt.QtGui import QColor
from qgis.core import (
  NULL,
  QgsCategorizedSymbolRenderer,
  QgsFeature,
  QgsField,
  QgsFillSymbol,
  QgsGeometry,
  QgsGradientColorRamp,
  QgsGradientStop,
  QgsGraduatedSymbolRenderer,
  QgsPresetSchemeColorRamp,
  QgsRendererCategory,
  QgsSingleSymbolRenderer,
  QgsStyle,
  QgsVectorLayer,
)

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(PLUGIN_DIR, "palettes.json")) as _f:
  PALETTES = json.load(_f)

# ramps suited to categorical data: the qualitative palette names from
# palettes.json, installed as preset-scheme (discrete-colour) ramps.
# The dialog uses this set to tell "categorical ramp" from "gradient"
CATEGORICAL_RAMPS = set(PALETTES["categorical"])

# distinct colours for tile ids in the design preview (tab20)
ID_COLOURS = PALETTES["categorical"]["tab20"]

# light grey used wherever an element has no variable or a feature has
# no value
NO_DATA_FILL = "#dddddd"

# The key standing for the catch-all category in a per-value colour
# override map. A real field value could in principle be the string
# "no data", so this is deliberately something no attribute value can
# collide with rather than a readable word.
NO_DATA_KEY = "\x00no-data"
# tag attached to ramps we install, so they are identifiable/removable
RAMP_TAG = "mapweaver"

# tile-count guard rails (tile count grows as 1/spacing^2, so a small
# spacing can innocently request millions of polygons): above HARD the
# run is refused outright (it would exhaust memory inside GEOS and kill
# QGIS), above CONFIRM a button press asks first, above LIVE the
# debounced auto-regeneration pauses and waits for an explicit press
MAX_TILES_HARD = 200_000
MAX_TILES_CONFIRM = 40_000
LIVE_UPDATE_MAX_TILES = 20_000


# ------------------------------------------------------------------ ramps

def ensure_ramps_installed() -> None:
  """Install the web app's palettes into the QGIS style library.

  Only names not already present (case-insensitively) are added, so the
  built-in ColorBrewer ramps QGIS ships stay untouched. Gradient ramps
  are built from the 16 colour stops in palettes.json; categorical
  palettes become preset-scheme ramps. All are tagged 'mapweaver'.
  """
  style = QgsStyle.defaultStyle()
  existing = {n.lower() for n in style.colorRampNames()}

  def save(name, ramp):
    try:
      style.addColorRamp(name, ramp)
      style.saveColorRamp(name, ramp, False, [RAMP_TAG])
    except Exception:
      pass

  for group in ("sequential", "diverging"):
    for name, stops in PALETTES[group].items():
      if name.lower() in existing:
        continue
      gradient_stops = [
        QgsGradientStop(i / (len(stops) - 1), QColor(c))
        for i, c in enumerate(stops[1:-1], start=1)]
      ramp = QgsGradientColorRamp(
        QColor(stops[0]), QColor(stops[-1]), False, gradient_stops)
      save(name, ramp)
  for name, colours in PALETTES["categorical"].items():
    if name.lower() in existing:
      continue
    save(name, QgsPresetSchemeColorRamp([QColor(c) for c in colours]))


def ramp_names() -> list[str]:
  """Every ramp name in the user's style library (built-ins, our
  installed palettes, and anything the user added themselves)."""
  return QgsStyle.defaultStyle().colorRampNames()


def get_ramp(name: str, reverse: bool = False):
  """A colour ramp from QGIS's style library, optionally reversed.

  Args:
    name: a ramp name in QgsStyle (the mapweaver palettes are
      installed there once by ensure_ramps_installed).
    reverse: return the ramp running the other way. Reversing is a
      real cartographic choice, not a gimmick — a sequential ramp
      reads "more is darker" or "more is lighter" depending on it,
      and a diverging one can be flipped to put the colour the reader
      associates with "high" on the right side.

  Returns:
    A ramp object owned by the caller (always a clone, so reversing
    it never disturbs the style library), or None when the name is
    unknown.

  Reversal is applied per ramp KIND, because QGIS models them
  differently: gradient ramps carry an invert() of their own; preset
  (discrete) schemes are a list of colours, so the list is reversed;
  anything else is sampled at even steps and rebuilt as a gradient
  running the other way, which is exact enough for symbology and
  never fails on a ramp type we have not met.
  """
  from qgis.core import (QgsGradientColorRamp, QgsPresetSchemeColorRamp,
                         QgsStyle)
  style = QgsStyle.defaultStyle()
  ramp = style.colorRamp(name)
  if ramp is None:
    # Resolve case-insensitively, because that is how installation
    # decides. ensure_ramps_installed skips a palette whose name
    # matches an existing ramp IGNORING CASE, so that QGIS's own
    # ramps are never duplicated -- and QGIS on Linux ships Cividis,
    # Inferno, Magma and Plasma where this plugin's table says
    # cividis, inferno, magma, plasma. An exact lookup then found
    # nothing: the plugin declined to install its own ramp because
    # QGIS had one, and then could not find the one QGIS had. Four
    # palettes were simply unavailable to every Linux user, with the
    # chooser still offering them. Found by CI on 2026-08-11; it
    # cannot happen on macOS, whose QGIS ships neither casing.
    #
    # The two rules must agree, and this is the direction that
    # agrees WITHOUT putting both Cividis and cividis in the user's
    # style library. It also makes a case-mismatched name behave
    # exactly like an exactly-matching one (Greys, which QGIS ships
    # too): the user's existing ramp wins, which is what "additive
    # only" has always meant here.
    wanted = name.lower()
    for candidate in style.colorRampNames():
      if candidate.lower() == wanted:
        ramp = style.colorRamp(candidate)
        break
  if ramp is None:
    return None
  ramp = ramp.clone()
  if not reverse:
    return ramp
  if isinstance(ramp, QgsPresetSchemeColorRamp):
    # colors() hands back bare QColors, but setColors expects QGIS's
    # "named colour list": (colour, label) pairs. Passing the bare
    # list raises a type error at the sip boundary, so pair them up
    # with empty labels, which is what an unlabelled scheme carries
    ramp.setColors([(colour, "") for colour in reversed(ramp.colors())])
    return ramp
  if hasattr(ramp, "invert"):
    ramp.invert()
    return ramp
  steps = 32
  stops = [ramp.color(1.0 - i / (steps - 1)) for i in range(steps)]
  return QgsGradientColorRamp(stops[0], stops[-1])

def ramp_swatch_colour(name: str) -> str:
  """Representative hex colour of a ramp, for the design preview."""
  try:
    colour = get_ramp(name).color(0.65)
    return colour.name()
  except Exception:
    return "#c0c0c0"


# ---------------------------------------------------- QGIS <-> GeoDataFrame

def layer_to_gdf(layer: QgsVectorLayer, field_names: list[str],
                 target_crs: str | None = None):
  """Build a GeoDataFrame from a polygon layer, carrying field_names.

  This is the way INTO weavingspace: everything downstream is plain
  geopandas, exactly as in the library's own notebooks.

  Args:
    layer: any QGIS polygon layer (memory, GeoPackage, shapefile —
      the provider does not matter, features are read through the
      same iterator).
    field_names: attribute names to carry across. Only these become
      columns; anything else on the layer is dropped, which keeps the
      frame small for the tiling's spatial join.
    target_crs: force a CRS for the result (anything geopandas
      accepts). Left as None, a projected layer keeps its own CRS and
      a geographic one is reprojected to EPSG:3857, matching the web
      app: tiling in degrees would give tiles that change size with
      latitude.

  Returns:
    A GeoDataFrame with one row per non-empty feature, the requested
    columns, valid geometry, and a CRS set.

  Raises:
    ValueError: the layer has no non-empty polygon features (tiling
      nothing would fail later, in a less obvious place).
  """
  import geopandas as gpd
  import numpy as np
  import shapely
  import shapely.wkb

  # getFeatures() iterates the layer's rows; each geometry crosses to
  # shapely via WKB bytes. QGIS represents missing attribute values
  # with its own NULL sentinel (not Python None), normalised here
  geoms, data = [], {f: [] for f in field_names}
  for feat in layer.getFeatures():
    g = feat.geometry()
    if g is None or g.isEmpty():
      continue
    geoms.append(shapely.wkb.loads(bytes(g.asWkb())))
    for f in field_names:
      v = feat[f]
      # On QGIS 4 this normalisation is a no-op: a NULL attribute
      # already reads back as Python None, for numeric and string
      # fields alike, from memory and file providers (verified
      # 2026-08-07; the mutation catalogue records it as an
      # equivalent mutant for that reason). It stays as insurance
      # against providers that hand back QGIS's NULL sentinel
      # instead, where pandas would make the column object dtype and
      # every downstream classification would quietly misbehave.
      data[f].append(None if v == NULL or v is None else v)
  if not geoms:
    raise ValueError("The selected layer has no (non-empty) polygon features.")

  gdf = gpd.GeoDataFrame(data, geometry=geoms, crs=layer.crs().authid())
  bad = ~gdf.geometry.is_valid
  if bad.any():
    gdf.loc[bad, "geometry"] = gdf.loc[bad, "geometry"].make_valid()
  if target_crs:
    gdf = gdf.to_crs(target_crs)
  elif gdf.crs is not None and gdf.crs.is_geographic:
    gdf = gdf.to_crs(3857)
  return gdf


def _make_field(name: str, python_type) -> QgsField:
  """A QgsField of the right type for a Python type.

  Args:
    name: the attribute name to create.
    python_type: ``str``, ``int`` or ``float``; anything else is
      treated as text, which is the safe direction to be wrong in.

  Returns:
    A QgsField ready for addAttributes(). The type mapping itself
    lives in compat.py, because QGIS 3 and 4 spell it differently.
  """
  from . import compat
  return compat.make_field(name, python_type)


def gdf_to_layer(gdf, name: str) -> QgsVectorLayer:
  """Convert a (Multi)Polygon GeoDataFrame to a QGIS memory layer.

  Args:
    gdf: the frame to convert. Its columns become attributes, its CRS
      becomes the layer's, and its geometry is normalised to
      MultiPolygon (a QGIS layer holds one geometry type, and a
      tiling can yield both).
    name: the layer name shown in the layers panel.

  Returns:
    A memory layer holding one feature per row. Memory layers live in
    RAM and vanish with the project unless exported, which is exactly
    what temporary map output wants.

  A "memory" layer lives only in RAM (it vanishes with the project
  unless exported); its constructor takes a URI string encoding the
  geometry type and CRS. The schema is declared from the frame's
  dtypes, then one QgsFeature is built per row. Geometries are
  normalised to MultiPolygon because a QGIS layer holds a single
  geometry type, while a tiled GeoDataFrame freely mixes Polygon,
  MultiPolygon, and (after clipping) GeometryCollection, from which
  only the polygonal parts are kept.
  """
  import pandas as pd
  from shapely.geometry import MultiPolygon, Polygon

  crs_str = ""
  if gdf.crs is not None:
    authid = gdf.crs.to_authority()
    crs_str = f"?crs={authid[0]}:{authid[1]}" if authid \
      else f"?crs=wkt:{gdf.crs.to_wkt()}"
  layer = QgsVectorLayer(f"MultiPolygon{crs_str}", name, "memory")
  if gdf.crs is None:
    # A memory layer whose URI names no CRS does not arrive WITHOUT
    # one: QGIS gives it EPSG:4326. That matters here because a region
    # layer with no CRS set is tiled in its own coordinates, whatever
    # those are, so the output would claim to be degrees while holding
    # numbers in the thousands -- a map placed at longitude 3197, and
    # one QGIS would happily reproject as though the degrees meant
    # something. The input said it did not know; the output says the
    # same.
    from qgis.core import QgsCoordinateReferenceSystem
    layer.setCrs(QgsCoordinateReferenceSystem())
  provider = layer.dataProvider()

  columns = [c for c in gdf.columns if c != gdf.geometry.name]
  kinds = {}
  for c in columns:
    if pd.api.types.is_integer_dtype(gdf[c]):
      kinds[c] = int
    elif pd.api.types.is_float_dtype(gdf[c]):
      kinds[c] = float
    else:
      kinds[c] = str
  provider.addAttributes([_make_field(c, kinds[c]) for c in columns])
  layer.updateFields()

  feats = []
  geoms = gdf.geometry.tolist()
  col_values = {c: gdf[c].tolist() for c in columns}
  for i, shp in enumerate(geoms):
    if shp is None or shp.is_empty:
      continue
    if isinstance(shp, Polygon):
      shp = MultiPolygon([shp])
    elif not isinstance(shp, MultiPolygon):
      polys = [g for g in getattr(shp, "geoms", [])
               if isinstance(g, Polygon)]
      if not polys:
        continue
      shp = MultiPolygon(polys)
    feat = QgsFeature(layer.fields())
    geom = QgsGeometry()
    geom.fromWkb(shp.wkb)
    feat.setGeometry(geom)
    for c in columns:
      v = col_values[c][i]
      if v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NA:
        feat[c] = NULL
      elif kinds[c] is int:
        feat[c] = int(v)
      elif kinds[c] is float:
        feat[c] = float(v)
      else:
        feat[c] = str(v)
    feats.append(feat)
  provider.addFeatures(feats)
  layer.updateExtents()
  # A memory layer arrives with NO spatial index, and every canvas
  # repaint, identify click and snap filters by rectangle -- a linear
  # scan per layer per paint. Measured (QGIS 4.0.3, 20k tiles):
  # viewport queries run fifteen times faster indexed, and the build
  # is one cheap pass here against a scan on every interaction after.
  provider.createSpatialIndex()
  return layer


# ------------------------------------------------------------ size guard

def estimate_tile_count(unit, region_gdf) -> int:
  """Estimate how many tiles a Tiling over this region would create.

  Args:
    unit: the tile unit (TileUnit or WeaveUnit) about to be tiled.
    region_gdf: the region, used only for its total bounds.

  Returns:
    An estimated tile count, at or above the true one. Cheap enough
    to call on every keystroke, which is the point: the guards decide
    whether to run at all before anything expensive happens.
  """
  return estimate_tile_count_bounds(unit, tuple(region_gdf.total_bounds))


def estimate_tile_count_bounds(unit, b, scale: float = 1.0) -> int:
  """Estimate the tile count from a bounds tuple rather than a frame.

  Mirrors _TileGrid's geometry: the library covers a circle enclosing
  the region's bounding rectangle (buffered by one tile diagonal, so
  edge units are complete), then steps across it with the unit's two
  translation vectors. The number of prototile positions is therefore
  the circle's area divided by the area of the parallelogram those
  vectors span, and each position contributes one tile per element.

  Args:
    unit: the tile unit; its tiles and translation vectors are read.
    b: (xmin, ymin, xmax, ymax) in the unit's own coordinates. Taking
      bounds rather than a GeoDataFrame lets the live-update gate ask
      this question straight from a QGIS layer extent, without
      building a frame it may not need.
    scale: answer as though the unit had been built at ``scale``
      times its spacing, without building it. Both the tile diagonal
      and the translation vectors scale linearly with spacing, so the
      whole estimate follows from multiplying them -- which is what
      lets min_reasonable_spacing check a suggestion against this
      same estimator instead of trusting an inverse-square law that
      ignores the border term.

  Returns:
    An estimated tile count; MAX_TILES_HARD + 1 when the vectors are
    degenerate (a unit that does not tile the plane), so a broken
    design is refused rather than attempted.
  """
  tb = unit.tiles.total_bounds
  tile_diag = math.hypot(tb[2] - tb[0], tb[3] - tb[1]) * scale
  w = (b[2] - b[0]) + 2 * tile_diag
  h = (b[3] - b[1]) + 2 * tile_diag
  radius = math.hypot(w, h) / 2
  v = unit.get_vectors()
  det = abs(v[0][0] * v[1][1] - v[0][1] * v[1][0]) * scale * scale
  if det <= 0:
    return MAX_TILES_HARD + 1
  n_prototiles = math.pi * radius * radius / det
  estimate = n_prototiles * max(len(unit.tiles), 1)
  # A layer with no CRS gives infinite bounds once reprojection is
  # attempted, and int(inf) raises OverflowError -- which reached the
  # user as an unhandled exception from pressing Generate, before any
  # guard could decline politely. Treat "cannot be counted" as "too
  # many", which is exactly what the caller already knows how to
  # refuse.
  if not math.isfinite(estimate):
    return MAX_TILES_HARD + 1
  return int(estimate)


def min_reasonable_spacing(unit, region_gdf, spacing: float) -> float:
  """Suggest a spacing that would bring the tile count under the cap.

  Tile count scales roughly with 1/spacing squared (halve the
  spacing, quadruple the tiles), so the spacing that lands on the cap
  is the current one times the square root of the overshoot.

  Args:
    unit: the tile unit as currently configured.
    region_gdf: the region being tiled.
    spacing: the spacing the user asked for, in map units.

  Returns:
    The requested spacing when it is already safe, otherwise the
    smallest spacing that would fit under MAX_TILES_HARD. Used in the
    refusal message, so the user is told what WOULD work rather than
    only what will not.
  """
  est = estimate_tile_count(unit, region_gdf)
  if est <= MAX_TILES_HARD:
    return spacing
  # The inverse-square law alone is not enough. Tile count grows as
  # 1/spacing^2 in the interior, but the estimate also buffers the
  # region by a tile diagonal, and that border term does not shrink
  # at the same rate -- so the spacing this arithmetic names came
  # back estimating 0.5-3.9% OVER the hard limit and was refused the
  # moment the user tried it. A suggestion that is itself refused is
  # worse than no suggestion: it reads as the plugin contradicting
  # itself. So the law gives the starting point and the ESTIMATOR
  # itself has the last word, widening until it agrees.
  scale = math.sqrt(est / MAX_TILES_HARD)
  bounds = tuple(region_gdf.total_bounds)
  for _ in range(60):
    if estimate_tile_count_bounds(unit, bounds, scale) <= MAX_TILES_HARD:
      break
    scale *= 1.02
  return spacing * scale


# ----------------------------------------------------------- tile coverage

def add_unit_ids(region_gdf) -> str:
  """Number the region's areas so tiles can be traced back to them.

  A tiled map is not a choropleth: where the spacing is coarse
  relative to a small area, that area can win no tile at all and then
  appears nowhere on the map, silently. The tiling itself gives no way
  to notice, because weavingspace drops its own internal region id
  (DZID) before handing back the map. So the plugin puts a column of its own on the
  region: every non-geometry column of the region rides along through
  the library's attribute join onto the tiles, which turns "who was
  left out?" into a difference between two sets of integers rather
  than a second spatial pass over the geometry.

  Args:
    region_gdf: the region frame about to be tiled. MUTATED: it gains
      one integer column. Pass the worker's own copy, not a frame the
      rest of the plugin still reads.

  Returns:
    The name of the column added, which is "ws_unit_id" unless the
    user's own data already has that field, in which case a digit is
    appended until the name is free (the same guard weavingspace
    itself uses for its DZID column, and for the same reason: the name
    has to survive an overlay against arbitrary user attributes).
  """
  name = "ws_unit_id"
  i = 0
  while name in region_gdf.columns:
    name = f"ws_unit_id{i}"
    i += 1
  region_gdf[name] = range(len(region_gdf))
  return name


def count_units_without_tiles(tiled_gdf, id_column: str,
                              unit_count: int) -> int:
  """How many region areas the finished tiling left empty.

  Args:
    tiled_gdf: the tiled map as the library returned it, one row per
      tile, carrying the tracing column added by ``add_unit_ids``.
      MUTATED: that column is dropped here, in place, so it never
      reaches the output layers or the GeoPackage. In place because
      ``drop`` without it copies the whole frame, and this frame is
      the largest thing in the run.
    id_column: the column name ``add_unit_ids`` returned.
    unit_count: how many areas the region had before tiling.

  Returns:
    The number of areas no tile drew its data from: areas the
    cartographer will not find on the map. Counting distinct ids is a
    hash over one integer column, so the cost is linear in tiles and
    trivial beside the tiling that produced them.
  """
  served = tiled_gdf[id_column].nunique()
  tiled_gdf.drop(columns=[id_column], inplace=True)
  return unit_count - served


def map_unit_label(layer: QgsVectorLayer) -> str:
  """The abbreviation for a layer's distance units, e.g. "m".

  Args:
    layer: the region layer whose CRS sets what "spacing" counts in.

  Returns:
    Whatever compat.map_unit_label returns. The call itself lives in
    compat.py because the enum behind it is version-sensitive, and
    this project keeps every such call in one place so a QGIS upgrade
    breaks one file rather than several.
  """
  from weavingspace_qgis import compat
  return compat.map_unit_label(layer)


def renderer_fill_colours(layer) -> list:
  """Every fill colour a layer's renderer will actually paint.

  Args:
    layer: an output layer with its renderer already seeded.

  Returns:
    A list of (r, g, b) tuples on 0..255 -- one per class for a
    graduated or categorized renderer, one for a single-symbol one,
    and an empty list if the renderer is of some kind this does not
    know. Read from the renderer rather than recomputed from the ramp,
    so it reflects what the map will look like even when the user has
    refined the symbology by hand in the Layer Styling panel.
  """
  renderer = layer.renderer()
  colours = []
  for accessor in ("ranges", "categories"):
    items = getattr(renderer, accessor, None)
    if callable(items):
      for item in items():
        symbol = item.symbol()
        if symbol is not None:
          colour = symbol.color()
          colours.append((colour.red(), colour.green(), colour.blue()))
      return colours
  symbol = getattr(renderer, "symbol", None)
  if callable(symbol) and symbol() is not None:
    colour = symbol().color()
    colours.append((colour.red(), colour.green(), colour.blue()))
  return colours


def categorical_shift_message(field: str, previous: int | None,
                              current: int) -> str | None:
  """Warn that a categorical field's colours have moved under the user.

  Args:
    field: the attribute whose class count changed, named so the user
      knows which element to look at.
    previous: how many distinct values it had on the last run in this
      session, or None the first time it is seen.
    current: how many it has now.

  Returns:
    One sentence for the message bar, or None when nothing moved.

  Why this is worth saying. Categorical colours are sampled across the
  palette by position -- entry int(i * len(palette) / (k - 1)) for
  class i of k -- which is matplotlib's ListedColormap rule and what
  the original renderer does, so the plugin is behaving correctly.
  The consequence is still surprising: measured on tab10, going from
  three classes to four changes the colour of two of the three
  originals, and four to five changes three of four. Only the first
  and last classes stay put, because the formula pins the palette's
  endpoints.

  A cartographer who filters their data, or maps a neighbouring region
  with one class more, gets a map whose colours mean something
  different from the last one, with nothing to say so. The remedy
  already exists in the plugin -- import a colour mapping for that
  element and the colours stop moving -- so the message names it.
  """
  if previous is None or previous == current or current < 2:
    return None
  return (f"'{field}' now has {current} categories where it had "
          f"{previous}, so the colours of the existing classes have "
          f"changed: they are sampled across the palette by position. "
          f"Import a colour mapping (QML) for that element to keep "
          f"colours the same from one map to the next.")


def coverage_message(missing: int, unit_count: int, spacing: float,
                     unit_label: str) -> str | None:
  """The message bar's warning about areas the pattern missed.

  Args:
    missing: how many areas received no tiles (from
      ``count_units_without_tiles``).
    unit_count: how many areas the region layer holds altogether.
    spacing: the spacing this run used, in the region's map units.
    unit_label: what those units are called, from ``map_unit_label``.

  Returns:
    One sentence for the message bar, or None when every area got at
    least one tile and there is nothing to say.

    The spacing is in the sentence deliberately. Users arrive at a
    spacing by trying several, and each try pushes another of these
    notices; without the number they are a stack of identical
    complaints, and with it they are the coverage cost of each spacing
    the user tried, side by side.
  """
  if missing <= 0:
    return None
  # Six decimals then strip: that is the spacing spin box's own
  # resolution, so the number in the message is the number the user
  # typed. Rounding harder would print "0 m" for the fine spacings a
  # degree-based or very local CRS makes reasonable
  spacing_text = f"{spacing:,.6f}".rstrip("0").rstrip(".")
  return (f"At {spacing_text} {unit_label} spacing, {missing:,} of "
          f"{unit_count:,} areas received no tiles and appear nowhere "
          f"on the map.")


# ------------------------------------------------------- renderer seeding

def _fill_symbol(colour: str, outline: bool) -> QgsFillSymbol:
  """A plain polygon fill.

  Args:
    colour: any string QGIS accepts, typically "#rrggbb".
    outline: draw a thin dark boundary. False removes the stroke
      entirely so adjacent tiles meet without seams.

  Returns:
    A QgsFillSymbol. QgsFillSymbol.createSimple takes a dict of
  string properties; outline=False removes the stroke entirely so
  adjacent tiles meet without seams (the web app's look), True draws a
  thin dark boundary."""
  opts = {"color": colour}
  opts.update({"outline_color": "35,35,35,255", "outline_width": "0.1"}
              if outline else {"outline_style": "no"})
  return QgsFillSymbol.createSimple(opts)


def numeric_values_are_constant(values) -> bool:
  """Whether a column holds exactly one distinct number.

  Args:
    values: any iterable of attribute values — a QGIS layer's
      ``uniqueValues`` set, or a pandas column. Nulls, text that is
      not a number, and non-finite values are all skipped, because
      none of them is something a class break can fall between.

  Returns:
    True when what remains is a single distinct number, False when
    there are two or more AND when there are none at all. An empty
    column is deliberately not "constant": it has no value to show,
    which is a different situation with its own handling, and calling
    it constant would put a class break on nothing.

  One rule, two callers: ``make_graduated_renderer`` asks it of the
  element layer to decide how many classes to cut, and the dialog
  asks it of the frame that was just mapped to decide whether to say
  anything. Deriving the rule twice is how the map and the message
  come to disagree.
  """
  seen = set()
  for value in values:
    if value is None or value == NULL:
      continue
    try:
      number = float(value)
    except (TypeError, ValueError):
      continue
    if not math.isfinite(number):
      continue
    seen.add(number)
    if len(seen) > 1:
      return False
  return len(seen) == 1


def missing_values_message(field: str, missing: int, total: int):
  """The notice for a column with gaps in it.

  Args:
    field: the attribute name, as the user chose it in the table.
    missing: how many mapped areas have no value for it.
    total: how many areas were mapped altogether.

  Returns:
    One sentence for the message bar, or None when nothing is
    missing. Worth saying whatever the breaks do: a reader looking at
    a patch of no-data colour is owed the count, and a user who later
    presses Classify in QGIS's own panel -- which recomputes with
    nulls counted as zero, moving every break -- has at least been
    told the column has gaps.
  """
  if missing <= 0:
    return None
  return (f"{missing:,} of {total:,} areas have no value for "
          f"'{field}'. They draw as no data, outside the class "
          f"breaks.")


def constant_field_message(field: str) -> str:
  """The notice for a column that turned out to hold one value.

  Args:
    field: the attribute name, as the user chose it in the table.

  Returns:
    One sentence for the message bar. There is no None case: the
    caller has already established that the column is constant, and
    the whole point is that this is worth saying. A map drawn from a
    constant column looks like a map of nothing in particular, and a
    user who does not know the column is constant will look for the
    fault in the pattern instead of in the data.
  """
  return (f"Every area has the same value for '{field}', so it "
          f"draws as one class, not a range.")


def make_graduated_renderer(layer: QgsVectorLayer, field: str,
                            ramp_name: str, scheme: str, k: int,
                            outline: bool,
                            reverse: bool = False,
                            range_bounds: tuple = (0, 100),
                            overrides: dict | None = None
                            ) -> QgsGraduatedSymbolRenderer:
  """Classed-numeric symbology for one element layer.

  Args:
    layer: the element's layer. It must already hold its features,
      because the classification is computed FROM them.
    field: the numeric attribute to classify.
    ramp_name: a ramp in QgsStyle (the mapweaver palettes are
      installed there by ensure_ramps_installed).
    scheme: one of the labels compat.classification_method knows
      ("Quantiles", "Equal intervals", "Natural breaks (Jenks)",
      "Pretty breaks"), or "Unclassed" (see below).
    k: how many classes; ignored for "Unclassed", which fixes 50.
    outline: draw a thin dark boundary on each tile.
    reverse: run the ramp the other way; get_ramp applies it, so every
      position below is a position on the ramp as the user sees it.
    range_bounds: (lo, hi) percentages, 0 <= lo <= hi <= 100, choosing
      where in the ramp the FIRST and LAST classes take their colours;
      classes between interpolate linearly (settled 2026-08-09). The
      default (0, 100) is deliberately a no-op: QGIS's own classifier
      colours class i at ramp.color(i/(k-1)) (measured, QGIS 4.0.3),
      which is exactly what the formula gives over the full window, so
      untouched rows keep byte-identical colours.
    overrides: {str(class_index): "#rrggbb"} chosen by hand in the
      colour editor's graduated mode. Keyed by POSITION, not by value,
      because a class has no name to follow when the breaks move; they
      outrank the range and the ramp alike, and are applied last.

  Returns:
    A QgsGraduatedSymbolRenderer, not yet attached to the layer
    (seed_renderer does that). It is an ordinary QGIS renderer, so
    everything about it stays editable in the styling dock.

  The mechanics: ``updateClasses`` asks QGIS to scan the
  layer's values and cut k classes using the chosen classification
  method (quantile/equal/Jenks/pretty, instantiated via compat since
  the class names are version-sensitive), colouring each class from
  the named ramp. The result is exactly what the user would get from
  the Graduated mode of QGIS's own symbology panel, so it remains
  fully editable there.

  scheme "Unclassed" is the plugin's reproduction of the web app's
  continuous choropleth, and it is derived from upstream's own
  semantics rather than invented: in the library, unclassed means
  n_classes=0, which TiledMap._set_colourspecs turns into scheme=None
  (vendor/weavingspace/tile_map.py), handing the column to geopandas/
  matplotlib whose continuous normalization is a *linear* map from the
  column's [min, max] onto the ramp. There is no upstream interval
  code to call; the exact QGIS-native equivalent of that linear map is
  equal intervals over [min, max], discretized here at 50 steps —
  visually indistinguishable from the continuous ramp at map scale
  while remaining an ordinary, panel-editable graduated renderer.
  """
  from . import compat
  if scheme == "Unclassed":
    scheme, k = "Equal intervals", 50
  # A column with one distinct value has nothing to divide. Asked for
  # five classes QGIS returns five, every one of them reading "7 - 7"
  # and each in a different colour: a legend showing variation the
  # data does not have. Every feature still falls in the first class,
  # so the MAP was never wrong -- only the legend beside it, which is
  # the part a reader trusts to say what the colours mean. One class
  # is the honest picture, and the dialog says so in words as well
  # (see constant_field_message). Placed after the Unclassed line so
  # it overrides that scheme's fixed 50 too.
  index = layer.fields().indexOf(field)
  # One pass over the column answers both questions below: is it
  # constant, and does it contain nulls.
  values = layer.uniqueValues(index) if index >= 0 else set()
  constant = index >= 0 and numeric_values_are_constant(values)
  if constant:
    k = 1
  renderer = QgsGraduatedSymbolRenderer(field)
  renderer.setSourceSymbol(_fill_symbol("#c0c0c0", outline))
  renderer.setSourceColorRamp(get_ramp(ramp_name, reverse))
  method = compat.classification_method(scheme)
  if method is not None:
    # How many decimals the LABELS carry. QGIS defaults to four, so a
    # column of values around 1e-9 gets five classes every one of
    # which prints "0 - 0": distinct colours on the map, one printed
    # meaning in the legend, which is a legend lying about its own
    # map (measured QGIS 4.0.3, 2026-08-09). Asking QGIS itself for
    # more decimals is configuration rather than reimplementation --
    # its own formatter still writes the labels. Raised only when the
    # data needs it, so ordinary magnitudes keep QGIS's normal look,
    # and capped where its formatter stops helping.
    finite = [float(v) for v in values
              if v is not None and v != NULL and isinstance(v, (int, float))
              and float(v) == float(v) and abs(float(v)) <= 1e307]
    if finite and hasattr(method, "setLabelPrecision"):
      span = max(finite) - min(finite)
      if span > 0:
        step = span / max(int(k), 1)
        # decimals needed for one step to survive rounding, plus two
        # so neighbouring breaks differ in more than the last digit
        needed = int(math.ceil(-math.log10(step))) + 2 if step < 1 else 0
        precision = max(method.labelPrecision(), min(15, needed))
        if precision != method.labelPrecision():
          method.setLabelPrecision(precision)
          if hasattr(method, "setLabelTrimTrailingZeroes"):
            method.setLabelTrimTrailingZeroes(True)
    renderer.setClassificationMethod(method)

  # ---- NULLs, and why this layer is filtered before being classified
  #
  # QGIS's classifier counts a NULL as ZERO. Its own minimumValue()
  # excludes nulls, so QGIS contradicts itself and the classifier
  # wins: nine values of 1..9 with five nulls beside them come back
  # as 0-0, 0-2.5, 2.5-5.75, 5.75-9 instead of 1-3, 3-5, 5-7, 7-9.
  # Every break is in the wrong place and the legend gains a class
  # that means "missing" while reading as a number. Nothing about it
  # is visible: no error, no empty layer, just a choropleth that is
  # quietly wrong. Measured the same on the memory provider and on a
  # GeoPackage through OGR (2026-08-09, QGIS 4.0.3), so it is the
  # classifier and not one provider's quirk.
  #
  # So the INPUT is corrected rather than the output: hide the nulls,
  # let QGIS classify exactly what it should have classified, put the
  # layer back. The alternative -- computing breaks here -- would mean
  # owning quantiles, equal intervals, Jenks and pretty breaks as four
  # algorithms, and every place our arithmetic differed from QGIS's
  # would be a fresh way for this plugin to disagree with the styling
  # panel the user opens next.
  #
  # Safe because this is the ELEMENT OUTPUT layer, which the plugin
  # creates and owns. The user's region layer is never filtered.
  #
  # WHEN QGIS FIXES THIS, and it may: the filtering becomes redundant
  # rather than harmful, since a classifier that already ignores nulls
  # gets the same answer either way. You will hear about it from
  # test_qgis_still_counts_nulls_as_zero, which asserts the UNFILTERED
  # behaviour is still broken and fails on the day it stops being.
  # That test exists to be a canary, so treat its failure as good news
  # and delete this block rather than "fixing" the test.
  # ...AND the same treatment for values that are not NUMBERS. QGIS
  # 4.0.3, measured 2026-08-09 with the plugin out of the way (a
  # child process calling QgsGraduatedSymbolRenderer.updateClasses
  # directly): Natural breaks (Jenks) SEGFAULTS -- exit 139, the
  # application gone with the user's unsaved project -- on a column
  # holding an infinity or a magnitude near the double limit
  # (+/-1e308); quantiles and equal intervals survive NaN but return
  # NaN class bounds, so every tile falls outside every class, the
  # layer paints nothing and the run reports success. Identical on
  # the memory provider and through OGR on a GeoPackage.
  #
  # The fix hands the classifier different INPUT rather than
  # replacing its arithmetic: one clause more on the subset string
  # this function already sets and restores. NaN fails every
  # comparison and the infinities fall outside the bounds, so the
  # classifier sees only finite numbers and its own four algorithms
  # go on deciding the breaks.
  #
  # DELETE THIS when test_qgis_still_crashes_on_infinite_class_breaks
  # fails: that canary asserts the crash directly, so its failure
  # means QGIS has been fixed and this clause is redundant. The NULL
  # half above has its own canary (test_qgis_still_counts_nulls_as_
  # zero) and they may well not be fixed together, so check both
  # before removing either.
  FINITE = 1e307
  restore = None
  awkward = any(
    v is None or v == NULL or (isinstance(v, float)
                               and (v != v or abs(v) > FINITE))
    for v in values)
  if index >= 0 and awkward:
    previous = layer.subsetString()
    clause = (f'"{field}" IS NOT NULL AND "{field}" > {-FINITE:g} '
              f'AND "{field}" < {FINITE:g}')
    combined = f"({previous}) AND {clause}" if previous else clause
    # A provider may refuse a subset string. Wrong breaks beat no map,
    # so a refusal falls through to classifying everything, exactly as
    # before this block existed.
    if layer.setSubsetString(combined):
      restore = previous
  try:
    renderer.updateClasses(layer, k)
  finally:
    if restore is not None:
      layer.setSubsetString(restore)
  # A single class spans the whole ramp and QGIS colours it from the
  # ramp's START (measured, QGIS 4.0.3: one class on Reds comes back
  # #fff5f0, the ramp's 0.0 endpoint) -- for a sequential ramp that is
  # near-white, which on the map reads as "no data" rather than "one
  # value". The ramp's MIDDLE is the honest colour for a constant
  # column: unmistakably a member of the chosen ramp without claiming
  # either extreme. get_ramp has already applied any reversal, so 0.5
  # is the middle of the ramp as the user sees it. (User decision,
  # 2026-08-09.)
  # Every symbol below is built FRESH rather than cloned off a range:
  # ``renderer.ranges()`` hands back temporaries, and a symbol
  # pointer read off one dangles as soon as the temporary dies --
  # cloning through it segfaulted QGIS outright when this block was
  # first written.
  lo, hi = range_bounds
  count = len(renderer.ranges())
  if constant and count:
    # One class ranges over the whole window, and QGIS colours it
    # from the ramp's START (measured: near-white on Reds), which on
    # the map reads as "no data" rather than "one value". The
    # window's MIDDLE is the honest colour -- the plain ramp middle
    # when the window is the whole ramp. (User decision, 2026-08-09.)
    mid = get_ramp(ramp_name, reverse).color((lo + hi) / 200.0).name()
    renderer.updateRangeSymbol(0, _fill_symbol(mid, outline))
  elif (lo, hi) != (0, 100) and count:
    # the Ramp Display Range: first class at lo, last at hi, linear
    # between. Skipped entirely at (0, 100) because QGIS's own
    # colours already ARE this formula there, and recolouring would
    # only add a place for the two to disagree.
    ramp = get_ramp(ramp_name, reverse)
    for i in range(count):
      along = i / (count - 1) if count > 1 else 0.5
      fraction = (lo + (hi - lo) * along) / 100.0
      renderer.updateRangeSymbol(
        i, _fill_symbol(ramp.color(fraction).name(), outline))
  # hand-picked class colours outrank the range and the ramp alike
  for key, colour in (overrides or {}).items():
    try:
      index = int(key)
    except (TypeError, ValueError):
      continue
    if 0 <= index < count:
      renderer.updateRangeSymbol(index, _fill_symbol(colour, outline))
  return renderer


def load_categorized_template(path: str) -> dict:
  """Read a QML style file and return its class scheme.

  This is how a colour mapping prepared once in QGIS (or shared by a
  colleague) becomes the "Categ colourmap src" of an element: the
  file's own categories are the authority for class codes, labels and
  colours, and anything the data has that the file does not mention
  falls back to an automatic colour.

  Args:
    path: a .qml file saved by QGIS from a categorized layer.

  Returns:
    {str(value): (symbol, label)} — the symbol is a CLONE, so callers
    may attach it to a renderer without the file's own renderer being
    disturbed, and the key is stringified because a QML may hold
    numbers where the data holds text, or the reverse.

  Raises:
    ValueError: the file carries no categorized symbology (a
    graduated or single-symbol style has nothing to say about
    classes).
  """
  from qgis.PyQt.QtXml import QDomDocument
  from qgis.core import QgsFeatureRenderer, QgsReadWriteContext
  doc = QDomDocument()
  with open(path, encoding="utf-8") as f:
    doc.setContent(f.read())
  elem = doc.documentElement().firstChildElement("renderer-v2")
  if elem.isNull():
    raise ValueError("No symbology found in the style file.")
  renderer = QgsFeatureRenderer.load(elem, QgsReadWriteContext())
  if not isinstance(renderer, QgsCategorizedSymbolRenderer):
    raise ValueError(
      "The style file does not contain categorised symbology.")
  mapping = {}
  for cat in renderer.categories():
    if cat.value() is None or cat.value() == "":
      continue
    mapping[str(cat.value())] = (cat.symbol().clone(), cat.label())
  if not mapping:
    raise ValueError("The style file defines no classes.")
  return mapping


def template_from_layer(source_layer) -> dict:
  """Class scheme taken from another loaded layer's categorized renderer,
  in the same {str(value): (symbol clone, label)} form as a QML file."""
  renderer = source_layer.renderer() if source_layer is not None else None
  if not isinstance(renderer, QgsCategorizedSymbolRenderer):
    raise ValueError("That layer has no categorized symbology")
  mapping = {}
  for cat in renderer.categories():
    if cat.value() is None or cat.value() == "":
      continue
    mapping[str(cat.value())] = (cat.symbol().clone(), cat.label())
  if not mapping:
    raise ValueError("That layer's symbology defines no classes")
  return mapping


def make_categorized_renderer(layer: QgsVectorLayer, field: str,
                              ramp_name: str, outline: bool,
                              template: dict | None = None,
                              reverse: bool = False,
                              overrides: dict | None = None,
                              ) -> QgsCategorizedSymbolRenderer:
  """One class per distinct field value, plus a "no data" catch-all.

  Args:
    layer: the element's layer; its distinct values define the
      classes, so it must already hold its features.
    field: the categorical attribute to classify.
    ramp_name: a ramp in QgsStyle. Preset (discrete) schemes are
      sampled as matplotlib's ListedColormap does; gradient ramps are
      sampled evenly.
    outline: draw tile boundaries.
    template: an imported class scheme ({value: (symbol, label)});
      values it names keep its exact colour and label, and anything
      it omits falls back to an automatic colour.
    reverse: run the ramp the other way.
    overrides: {str(value): "#rrggbb"} chosen by hand in the
      Categorical colour editor, plus optionally NO_DATA_KEY for the
      catch-all. These outrank the template and the ramp alike.
      Values not named here are coloured exactly as before.

  Returns:
    A QgsCategorizedSymbolRenderer, including the None-valued
    category QGIS uses to catch values no class matched.

  Colours come from, in order of preference: the template (a scheme
  from a QML file or donor layer; values it names keep their exact
  symbol and label), the cycled colours of a preset-scheme ramp, or
  even sampling along a gradient ramp. Values are sorted with numbers
  before strings so mixed-type fields (possible after joins) cannot
  break Python's comparison rules.
  """
  idx = layer.fields().indexOf(field)
  values = sorted(
    (v for v in layer.uniqueValues(idx) if v is not None and v != NULL),
    key=lambda v: (isinstance(v, str), v))
  ramp = get_ramp(ramp_name, reverse)
  preset = ramp.colors() if isinstance(ramp, QgsPresetSchemeColorRamp) \
    else None
  categories = []
  overrides = overrides or {}
  n = max(len(values), 1)
  for i, v in enumerate(values):
    # A colour chosen by hand in the Categorical colour editor outranks
    # everything below it, including an imported scheme: it is the most
    # specific statement anyone has made about this value. The label is
    # left as the value's own text, because the user picked a colour,
    # not a name.
    if str(v) in overrides:
      categories.append(QgsRendererCategory(
        v, _fill_symbol(overrides[str(v)], outline), str(v)))
      continue
    if template is not None and str(v) in template:
      symbol, label = template[str(v)]
      categories.append(QgsRendererCategory(v, symbol.clone(), label))
      continue
    if preset:
      # sample the discrete set exactly as matplotlib's ListedColormap
      # does when geopandas colours k categories (upstream's
      # categorical path): the category code is normalised to
      # code/(k-1) in [0, 1] and the colormap maps that to entry
      # int(x * N), clamped. For 5 classes on tab10 that is entries
      # 0, 2, 5, 7, 9 — note 5 at the midpoint (int(0.5 * 10)), not 4;
      # a round() here once painted the middle category purple where
      # the original renders brown, caught by the release suite's
      # colourspace comparison. Beyond the set's size, cycle.
      if n <= len(preset):
        idx = min(int(i * len(preset) / (n - 1)), len(preset) - 1) \
          if n > 1 else 0
      else:
        idx = i % len(preset)
      colour = preset[idx].name()
    else:
      colour = ramp.color(i / (n - 1) if n > 1 else 0.5).name()
    categories.append(QgsRendererCategory(
      v, _fill_symbol(colour, outline), str(v)))
  # The catch-all for values no class matched. It is a colour a reader
  # sees -- often over a large area, where a join left gaps -- so the
  # editor offers it too, under the key below.
  categories.append(QgsRendererCategory(
    None, _fill_symbol(overrides.get(NO_DATA_KEY, NO_DATA_FILL), outline),
    "no data"))
  return QgsCategorizedSymbolRenderer(field, categories)


def make_single_renderer(colour: str, outline: bool) -> QgsSingleSymbolRenderer:
  """Flat fill for every feature.

  Args:
    colour: the fill, typically "#rrggbb".
    outline: draw tile boundaries.

  Returns:
    A QgsSingleSymbolRenderer, used both for the Single colour style
    and for elements carrying no variable at all.
  """
  return QgsSingleSymbolRenderer(_fill_symbol(colour, outline))


def seed_renderer(layer: QgsVectorLayer, assignment: dict,
                  template: dict | None = None) -> None:
  """Give one element layer its initial symbology.

  The single point where a row of the dialog's table becomes QGIS
  symbology. Everything it produces is a standard renderer, so the
  user's next move can be QGIS's own styling dock; the plugin never
  needs to be asked again.

  Args:
    layer: the element's layer, already carrying its tiles.
    assignment: one dict from ``dialog._assignments()``. Keys read
      here: ``var`` (None means the element carries no variable and
      gets a plain no-data fill), ``mode`` ("Graduated",
      "Categorized" or "Single colour", already resolved from the
      style dropdown and the field's type), ``ramp``, ``scheme``
      (including "Unclassed"), ``k``, ``outline``,
      ``single_colour`` for Single colour rows, and for graduated
      rows ``range_bounds`` (where in the ramp the classes sample)
      and ``quant_colours`` (positional hand-picks, which outrank
      the range and the ramp).
    template: a class scheme from load_categorized_template or
      template_from_layer. Applied only to categorized elements;
      ignored otherwise. The assignment's ``category_colours``, if
      present, outrank it value by value.

  Returns:
    None. The renderer is attached to the layer and a repaint is
    requested, which is what any map canvas showing it needs.
  """
  var = assignment.get("var")
  outline = assignment.get("outline", False)
  # setRenderer hands the layer its symbology object; triggerRepaint
  # afterwards tells any map canvas showing the layer to redraw
  if not var:
    layer.setRenderer(make_single_renderer(NO_DATA_FILL, outline))
  elif assignment["mode"] == "Categorized":
    layer.setRenderer(make_categorized_renderer(
      layer, var, assignment["ramp"], outline, template,
      assignment.get("reverse", False),
      assignment.get("category_colours")))
  elif assignment["mode"] == "Single colour":
    colour = assignment.get("single_colour") or \
      ramp_swatch_colour(assignment["ramp"])
    layer.setRenderer(make_single_renderer(colour, outline))
  else:
    layer.setRenderer(make_graduated_renderer(
      layer, var, assignment["ramp"], assignment.get("scheme", "Quantiles"),
      assignment.get("k", 5), outline, assignment.get("reverse", False),
      assignment.get("range_bounds", (0, 100)),
      assignment.get("quant_colours")))
  layer.triggerRepaint()


# ------------------------------------------------------------ GPKG output

def write_gpkg_layer(layer: QgsVectorLayer, path: str, layer_name: str,
                     first: bool) -> QgsVectorLayer:
  """Write one layer into a GeoPackage and return the file-backed layer.

  Args:
    layer: the in-memory element layer to write.
    path: the .gpkg file. It may hold every element of a map, which
      is the point: one file to share rather than four.
    layer_name: the name inside the file (the plugin uses
      "tiles_<element id>").
    first: True for the first element of a run into a fresh file,
      which RECREATES the file; False replaces just this layer inside
      an existing one. Getting this backwards would silently discard
      the elements written before it.

  Returns:
    A layer reading from the file (the "ogr" provider, via QGIS's
    "path|layername=x" URI form). The caller should use this in place
    of the memory layer it passed in, so what the user sees is what
    is on disk.

  Raises:
    RuntimeError: the writer refused; the message carries its reason.

  A GeoPackage is a sqlite file that can hold many named layers.
  QgsVectorFileWriter is QGIS's exporter; its enums are reached through
  compat because their spelling changed between QGIS 3 and 4, and its
  return convention (bare code vs tuple) also drifted, hence the
  isinstance check. The returned layer reads from the file via the
  "ogr" provider using QGIS's "path|layername=x" URI form, replacing
  the memory layer that was written.
  """
  from qgis.core import (QgsCoordinateTransformContext, QgsVectorFileWriter)
  from . import compat
  options = QgsVectorFileWriter.SaveVectorOptions()
  options.driverName = "GPKG"
  options.layerName = layer_name
  # A GeoPackage's primary key column is called "fid", and GDAL maps
  # an attribute of that name onto it. Tiles inherit their region
  # polygon's attributes, so many tiles share one "fid" value and the
  # write fails outright on the first duplicate -- which a user hits
  # simply by mapping a field called fid, as GeoPackage-sourced layers
  # routinely have. Naming the key column something else leaves the
  # attribute to be written as an ordinary column, under its own name.
  # SPATIAL_INDEX is GDAL's GeoPackage default already; named here so
  # the R-tree the interactive map depends on cannot vanish behind a
  # changed default, and so the intent is visible beside the FID fix
  options.layerOptions = ["FID=weavingspace_fid", "SPATIAL_INDEX=YES"]
  options.actionOnExistingFile = (
    compat.writer_overwrite_file() if first
    else compat.writer_overwrite_layer())
  result = QgsVectorFileWriter.writeAsVectorFormatV3(
    layer, path, QgsCoordinateTransformContext(), options)
  code = result[0] if isinstance(result, tuple) else result
  if code != compat.writer_no_error():
    raise RuntimeError(
      f"Writing {layer_name} to {path} failed: {result}")
  out = QgsVectorLayer(f"{path}|layername={layer_name}", layer.name(), "ogr")
  if not out.isValid():
    raise RuntimeError(f"Could not re-open {layer_name} from {path}")
  return out


def embed_style(layer: QgsVectorLayer) -> None:
  """Best-effort: save the layer's current style into its GeoPackage.

  QGIS keeps styles in a ``layer_styles`` table inside the same file
  (``useAsDefault=True`` makes it load automatically), which is what
  lets a colleague open the .gpkg and see the map already symbolized.
  Best-effort because the API signature has drifted across versions
  and a failed style save should never fail the run.

  The style NAME is trimmed to thirty characters because that is the
  width GDAL gives layer_styles.styleName, and a longer one is
  truncated with a warning on every write -- which a user with a long
  column name meets routinely, since output layers are named after
  the element and its variable (a 73-character field produced a
  77-character style name, GDAL, 2026-08-11). Nothing depended on the
  full name: QGIS loads the default style by matching the TABLE, not
  the style's name, so the only cost of the old behaviour was a
  warning nobody could act on and a stored value that did not say
  what it claimed. Trimming here rather than leaving GDAL to do it
  means the value in the file is one this code chose.
  """
  # 30 is GDAL's column width, not a preference; if a future GDAL
  # widens it this can simply go.
  name = layer.name()[:30]
  try:
    layer.saveStyleToDatabase(name, "seeded by WeavingSpace",
                              True, "")
  except Exception:
    pass


def region_outline_layer(source_layer: QgsVectorLayer) -> QgsVectorLayer:
  """A second QGIS layer reading the *same underlying data source* as
  the region layer (same provider and URI, nothing copied), symbolized
  as outlines only: the web app's "show map units" overlay.

  Args:
    source_layer: the region layer being tiled.

  Returns:
    An unowned layer, styled but not yet added to the project.

  The styling mirrors what the app draws over its maps: a wide white
  line UNDER a narrow black one, so the boundary stays legible over
  both pale and dark parts of the pattern. In QGIS that is two symbol
  layers in one fill symbol, the first drawn first.
  """
  layer = QgsVectorLayer(source_layer.source(),
                         f"{source_layer.name()} (outlines)",
                         source_layer.providerType())
  sym = QgsFillSymbol.createSimple({
    "style": "no", "outline_color": "255,255,255,255",
    "outline_width": "0.9"})
  narrow = QgsFillSymbol.createSimple({
    "style": "no", "outline_color": "0,0,0,255", "outline_width": "0.35"})
  # appendSymbolLayer draws on top of what is already there, giving
  # the black-over-white casing
  sym.appendSymbolLayer(narrow.symbolLayer(0).clone())
  layer.renderer().setSymbol(sym)
  return layer
