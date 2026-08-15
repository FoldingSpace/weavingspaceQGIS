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

# lowercase ramp name -> the name the style library actually uses.
# Filled lazily by get_ramp and cleared by ensure_ramps_installed.
# It exists for speed, and the speed is not a nicety: resolving a name
# case-insensitively means listing every ramp in the style, which is a
# query against the style database, and the ramp COMBO asks for an
# icon per ramp per row. Without this, one table rebuild on a QGIS
# whose ramp names differ in case from ours ran the query hundreds of
# times and took a test from 248 seconds to over 600 (Linux CI,
# 2026-08-11). A user would have felt it as a dialog that stopped
# responding when they changed layer.
_RAMP_NAME_BY_LOWER = {}

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
  # whatever this adds changes what get_ramp should resolve to
  _RAMP_NAME_BY_LOWER.clear()
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

  Reversal is applied per ramp KIND, because QGIS models the two
  differently. A preset (discrete) scheme is a list of colours, so the
  list is reversed. Everything else carries an invert() of its own and
  is asked to use it.

  There used to be a third branch here, sampling an unknown ramp at 32
  even steps and rebuilding it as a gradient, for "a ramp type we have
  not met". It was unreachable and is gone (2026-08-13). `invert` is
  defined on QgsColorRamp ITSELF, not on the subclasses, so
  `hasattr(ramp, "invert")` is true for every ramp QGIS defines and
  for any subclass a third-party plugin might register -- measured on
  all six built-in classes and on a bare subclass. The fallback could
  not run, and it was also the worst of the three: rebuilding a
  discrete scheme as a two-stop gradient would have thrown away every
  colour between the ends.
  """
  from qgis.core import QgsPresetSchemeColorRamp, QgsStyle
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
    actual = _RAMP_NAME_BY_LOWER.get(wanted)
    if actual is None:
      # one listing, then remembered. A miss refreshes the map once
      # rather than per lookup, so a name that is genuinely absent
      # costs one query and not one per caller.
      _RAMP_NAME_BY_LOWER.clear()
      _RAMP_NAME_BY_LOWER.update(
        {n.lower(): n for n in style.colorRampNames()})
      actual = _RAMP_NAME_BY_LOWER.get(wanted)
    if actual is not None:
      ramp = style.colorRamp(actual)
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
  ramp.invert()
  return ramp

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


def distinct_numeric_count(values, limit: int | None = None) -> int:
  """How many distinct finite numbers a column holds.

  Args:
    values: any iterable of attribute values — a QGIS layer's
      ``uniqueValues`` set, or a pandas column. Nulls, text that is
      not a number, and non-finite values are all skipped, because
      none of them is something a class break can fall between: a
      NULL is excluded from the breaks by the workaround below, and
      a NaN or an infinity is not a class anybody can read.
    limit: stop counting once this many have been seen. Purely a
      cost control for the constant check, which needs to know
      whether there are two and not how many there are; the count
      returned is then that limit rather than the true total, so
      pass it only when a ceiling is all you are asking about.

  Returns:
    The number of distinct finite numbers, or ``limit`` when one was
    given and reached.

  One rule, three callers: the class-count reduction asks it of the
  REGION layer, ``numeric_values_are_constant`` asks it of whatever
  it is given, and the dialog asks it of the frame just mapped to
  decide whether to say anything. Deriving the rule more than once is
  how the map and the message come to disagree.
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
    if limit is not None and len(seen) >= limit:
      break
  return len(seen)


def numeric_values_are_constant(values) -> bool:
  """Whether a column holds exactly one distinct number.

  Args:
    values: any iterable of attribute values; see
      ``distinct_numeric_count``, which does the counting so that the
      constant case and the general fewer-values-than-classes case
      cannot come to disagree about what counts as a value.

  Returns:
    True when what remains is a single distinct number, False when
    there are two or more AND when there are none at all. An empty
    column is deliberately not "constant": it has no value to show,
    which is a different situation with its own handling, and calling
    it constant would put a class break on nothing.

  The ceiling of two is what keeps this cheap on a large column: the
  answer is settled by the second distinct value, whatever follows.
  """
  return distinct_numeric_count(values, limit=2) == 1


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


def inset_collapse_message(declared: int, remaining: int,
                           inset_percent: float) -> str:
  """The notice for a tile inset that has eaten the design.

  Args:
    declared: how many elements the chosen family carries.
    remaining: how many survive the inset, i.e. how many the unit
      still holds.
    inset_percent: the Tiles inset control's value, as a percentage
      of the spacing, quoted back so the sentence names the control
      the user actually touched.

  Returns:
    One sentence for the message bar, or None when nothing was lost,
    so the caller can ask unconditionally.

  Insetting shrinks every tile by a fixed distance, so at a large
  enough inset the narrower elements disappear entirely. That is
  legitimate arithmetic and worth saying, because what the user meets
  otherwise is a sentence about something else. When SOME elements
  survive they are slivers, which the library's overlay then refuses
  as invalid geometry, and the run failed with "ValueError: You have
  passed make_valid=False along with 1978 invalid input geometries",
  in a modal, naming geopandas internals rather than the inset just
  typed. When ALL of them go, the table empties and the run was
  refused with "Assign at least one variable in the Data & colours
  tab" -- true, and about the wrong thing entirely. Measured on QGIS
  4.0.3, 2026-08-13, on stripes 25 at 2% and stripes 10 at 5%.
  """
  if remaining >= declared:
    return None
  if remaining <= 0:
    return (f"A tiles inset of {inset_percent:g}% leaves nothing of "
            f"this design: every element is narrower than the inset. "
            f"Reduce the inset, or choose a coarser spacing.")
  return (f"A tiles inset of {inset_percent:g}% has removed "
          f"{declared - remaining} of this design's {declared} "
          f"elements, and the rest are slivers. Reduce the inset, or "
          f"choose a coarser spacing.")


def pin_problem(low, high, values, asked: int):
  """Why a pair of pinned bounds cannot be used, or None.

  Args:
    low: the upper bound of the FIRST class, set by hand, or None
      when that end is not pinned.
    high: the lower bound of the LAST class, or None.
    values: the column's values, as ``distinct_numeric_count`` reads
      them -- the region's, since that is what the breaks are cut
      from.
    asked: the class count the row asks for, so that a pin leaving
      nothing for the middle can be told from one that merely leaves
      little.

  Returns:
    A sentence for the message bar naming what is wrong, or None when
    the pins are usable. The caller reverts the edit on a sentence
    and applies it on None; this function decides nothing about the
    map.

  What is REFUSED here is only what cannot be drawn at all: bounds
  that cross, a bound outside the data, or a pin that leaves no
  sample for the middle classes. What is deliberately NOT refused is
  a pin leaving fewer distinct values than remaining classes -- that
  draws fewer classes through the ordinary reduction and says so
  through few_values_message, which is one answer to "the data cannot
  support this count" rather than two. (Settled 2026-08-14.)
  """
  numbers = sorted(
    float(v) for v in values
    if v is not None and v != NULL and isinstance(v, (int, float))
    and math.isfinite(float(v)))
  if not numbers:
    return ("There are no values to pin a class bound against.")
  smallest, largest = numbers[0], numbers[-1]
  for name, bound in (("lower", low), ("upper", high)):
    if bound is None:
      continue
    if not math.isfinite(float(bound)):
      return f"The {name} class bound must be a number."
    if not smallest <= float(bound) <= largest:
      return (f"The {name} class bound must sit between "
              f"{_trim(smallest)} and {_trim(largest)}, which is what "
              f"the data covers.")
  if low is not None and high is not None and float(low) >= float(high):
    return ("The first class must end below where the last class "
            "begins.")
  # A ladder of k classes has k-1 boundaries, and each pin names one
  # of them. Two pins on a two-class row therefore name two
  # boundaries where there is one, and the pinned classes would not
  # meet: measured, that draws 0-10 beside 60-121 with everything
  # between them in no class at all. Refused rather than resolved,
  # because choosing which of the two typed numbers to honour is the
  # kind of guess this project's notices exist to avoid.
  pins = (low is not None) + (high is not None)
  if pins and int(asked) - 1 < pins:
    available = int(asked) - 1
    return (f"A {int(asked)}-class ladder has "
            f"{available} boundar{'y' if available == 1 else 'ies'} "
            f"to pin, so it cannot carry {pins}. Ask for more "
            f"classes, or unpin one end.")
  # Something has to be left for the classes in between. A pin takes
  # one class of its own, so the middle is what the row asked for
  # minus the pins, and it needs at least one value to cut.
  middle = [v for v in numbers
            if (low is None or v > float(low))
            and (high is None or v < float(high))]
  pins = (low is not None) + (high is not None)
  if int(asked) - pins > 0 and not middle:
    return ("Those bounds leave nothing between them to divide into "
            "classes.")
  return None


def _trim(value: float) -> str:
  """A number as a person would write it, with trailing zeros gone."""
  text = f"{float(value):.6g}"
  return text


def few_values_message(field: str, distinct: int, asked: int):
  """The notice for a column with fewer distinct values than classes.

  Args:
    field: the attribute name, as the user chose it in the table.
    distinct: how many distinct finite values the REGION layer holds
      for it — the user's own areas, not the tiles, for the same
      reason missing_values_message counts areas.
    asked: how many classes the table asked for.

  Returns:
    One sentence for the message bar, or None when the count was not
    reduced, so the caller can report unconditionally.

  This is the constant-column notice at n > 1, and it exists for the
  same reason: the class count in the table would otherwise describe
  a legend the map does not have. Left unsaid, a user sees their
  Classes spinner reading five and a legend of three and has nothing
  to tell them which is the truth. It also gives them a chance of
  understanding what happens if they later press Classify in QGIS's
  own Graduated panel, which recomputes k from the panel and puts the
  five back.
  """
  if distinct >= asked or distinct <= 0:
    return None
  return (f"'{field}' has {distinct} distinct value"
          f"{'' if distinct == 1 else 's'}, so it draws as {distinct} "
          f"class{'' if distinct == 1 else 'es'}, not {asked}.")


def _apply_pinned_bounds(renderer, low, high, smallest, largest,
                         outline, method, wants_middle=True):
  """Put the pinned classes back around the computed middle.

  Args:
    renderer: the graduated renderer, already carrying the classes
      the scheme cut from the samples between the pins.
    low: the first class's upper bound, or None.
    high: the last class's lower bound, or None.
    smallest, largest: the column's extremes, which become the outer
      edges of the pinned classes.
    outline: whether tiles are stroked, for the symbols built here.
    method: the classification method, asked for its own label text
      so a pinned class is labelled the way every other class is.
    wants_middle: False when the pins account for every class the row
      asked for, in which case the classes the scheme cut are dropped
      rather than kept beside them.

  Returns:
    None; the renderer's classes are replaced in place.

  The SNAP is here: the first computed class's lower bound is moved
  to the pin, and the last computed class's upper bound likewise, so
  the ladder has no gap. Without it a pin at 10 over data that
  resumes at 14 leaves 10 to 14 in no class, and a value arriving
  there later paints as no data on a map that looks perfectly fine.
  Only the outermost edge moves; the scheme's own breaks are
  untouched.

  Symbols are built FRESH rather than cloned off a range, for the
  reason recorded above updateRangeSymbol: ``ranges()`` hands back
  temporaries and a symbol pointer read off a dead one segfaults.
  """
  middle = ([(r.lowerValue(), r.upperValue()) for r in renderer.ranges()]
            if wants_middle else [])
  if middle:
    if low is not None:
      middle[0] = (float(low), middle[0][1])
    if high is not None:
      middle[-1] = (middle[-1][0], float(high))
  bounds = list(middle)
  if low is not None:
    bounds.insert(0, (float(smallest), float(low)))
  if high is not None:
    bounds.append((float(high), float(largest)))
  renderer.deleteAllClasses()
  # QGIS 4's addClass takes a SYMBOL only (measured: the
  # QgsRendererRange overload of older versions is gone), so each
  # class is added and then given its bounds and label by index.
  for lower, upper in bounds:
    renderer.addClass(_fill_symbol("#c0c0c0", outline))
  for position, (lower, upper) in enumerate(bounds):
    renderer.updateRangeLowerValue(position, lower)
    renderer.updateRangeUpperValue(position, upper)
    label = f"{_trim(lower)} - {_trim(upper)}"
    if method is not None and hasattr(method, "labelForRange"):
      try:
        label = method.labelForRange(lower, upper)
      except Exception:
        pass
    renderer.updateRangeLabel(position, label)


def classification_source(field: str, values) -> QgsVectorLayer | None:
  """A throwaway layer holding one column, for cutting breaks from.

  Args:
    field: the attribute name to give the column. It must be the name
      the renderer classifies on, since ``updateClasses`` looks the
      field up BY NAME in whatever layer it is handed.
    values: every value of that column, in feature order and WITH its
      gaps -- nulls and non-finite numbers included. Frequencies
      decide quantile breaks, so this is one entry per area rather
      than a set of distinct values.

  Returns:
    A geometry-less memory layer carrying those values as doubles, or
    None when it could not be built, which tells the caller to fall
    back to classifying the layer it already has.

  Why a copy exists at all. Breaks must be cut from the WHOLE map's
  values or two elements carrying one variable class differently
  (see make_graduated_renderer), and the values live on the user's
  region layer -- which this plugin must not filter, since the null
  workaround below works by hiding rows and the standing promise is
  that only layers the plugin created are touched. Filtering
  somebody's own layer would also flicker their canvas and, if
  anything went wrong midway, leave it filtered.

  The fields are built through the provider rather than through a URI
  because a column name may carry spaces or punctuation that a
  ``field=name:double`` URI does not survive.
  """
  from . import compat
  try:
    layer = QgsVectorLayer("None", "weavingspace classification", "memory")
    provider = layer.dataProvider()
    if not provider.addAttributes([compat.make_field(field, float)]):
      return None
    layer.updateFields()
    features = []
    for value in values:
      feature = QgsFeature(layer.fields())
      # NULL and NaN are passed through rather than dropped: the
      # workaround in make_graduated_renderer exists to deal with
      # them, and dropping them here would be a second, silent rule
      # doing the same job differently.
      feature[field] = value
      features.append(feature)
    if not provider.addFeatures(features):
      return None
    layer.updateExtents()
    return layer
  except Exception:
    return None


def make_graduated_renderer(layer: QgsVectorLayer, field: str,
                            ramp_name: str, scheme: str, k: int,
                            outline: bool,
                            reverse: bool = False,
                            range_bounds: tuple = (0, 100),
                            overrides: dict | None = None,
                            classify_from=None,
                            pinned: dict | None = None
                            ) -> QgsGraduatedSymbolRenderer:
  """Classed-numeric symbology for one element layer.

  Args:
    layer: the element's layer. It must already hold its features,
      because the renderer is built for them -- though the BREAKS
      come from ``classify_from`` where that is given.
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
    classify_from: where the breaks come from. Either every value of
      this column across the WHOLE map -- one entry per region area,
      nulls and all, since frequencies decide quantile breaks -- or a
      layer already holding them, which is what the dialog passes so
      that one copy serves every element. Given either, the breaks
      and the class count are cut from those values rather than from
      the element layer's own tiles, so that two elements carrying
      one variable class identically; see the long note in the body
      for what that costs and why it is worth it. None classifies the
      layer passed in, which is what a direct caller or a test gets.
    pinned: class bounds a person set, as ``{"low": float, "high":
      float}`` with either key absent. ``low`` is the FIRST class's
      upper bound and ``high`` is the LAST class's lower bound; the
      samples inside a pinned class leave the pool, the scheme cuts
      the row's count minus one class per pin, and the pinned classes
      are put back around the result. Validate with ``pin_problem``
      before passing: bounds that cannot be drawn are the caller's to
      refuse, and this function assumes it has been asked something
      possible.

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
  unclassed = scheme == "Unclassed"
  if scheme == "Unclassed":
    scheme, k = "Equal intervals", 50
  # ---- WHICH VALUES THE BREAKS ARE CUT FROM
  #
  # Not the same question as which layer wears them, and getting the
  # two confused is a defect this plugin shipped until 2026-08-14.
  # An element LAYER holds only that element's tiles, so classifying
  # it cuts the breaks from a different sample per element. Measured
  # on QGIS 4.0.3 with four elements carrying ONE variable at n=12,
  # k=5, no reduction involved:
  #
  #   a  [(0, 3.4), (3.4, 14.0), (14.0, 30.4), (30.4, 55.6), ...]
  #   b  [(0, 4.0), (4.0, 14.0), (14.0, 30.0), (30.0, 55.0), ...]
  #   c  [(0, 4.0), (4.0, 13.6), (13.6, 30.0), (30.0, 55.0), ...]
  #   d  [(0, 3.4), (3.4, 12.0), (12.0, 30.0), (30.0, 54.0), ...]
  #
  # Four elements, four legends, one variable: the same colour means
  # a different number depending on which element a reader is looking
  # at. On a map whose whole purpose is reading elements against each
  # other that is the worst kind of wrong, because every element
  # looks perfectly reasonable alone. It is the same argument that
  # rejected a per-element CLASS COUNT on 2026-08-13, applied to the
  # breaks, and it went unnoticed because the standard fixture asks
  # for more classes than it has distinct values -- which makes
  # quantile breaks collapse onto the values themselves and agree by
  # accident.
  #
  # So the caller hands over the region's values and the breaks are
  # cut ONCE for the whole map. This departs from upstream, which
  # classifies each element's subset separately
  # (tile_map._plot_subsetted_gdf calls plot() per group), and the
  # departure is deliberate under the standing rule that the plugin
  # may have its own ideas where they fit QGIS and this kind of map.
  # The reference comparison stays a real differential because
  # TiledMap.render can be handed these same breaks
  # (scheme="UserDefined", classification_kwds={"bins": ...}), which
  # leaves it checking everything except the axis we moved on purpose.
  #
  # Without values to hand -- a direct caller, a test -- the layer
  # given is classified, exactly as before.
  # A prepared layer is accepted as well as raw values, and the
  # dialog passes one: building a copy of the column per ELEMENT
  # would mean twenty-six copies of a fifty-thousand-row column for
  # one map, where the whole map needs one.
  if classify_from is None:
    source = None
  elif hasattr(classify_from, "getFeatures"):
    source = classify_from
  else:
    source = classification_source(field, classify_from)
  if source is None:
    source = layer
  # A column with one distinct value has nothing to divide. Asked for
  # five classes QGIS returns five, every one of them reading "7 - 7"
  # and each in a different colour: a legend showing variation the
  # data does not have. Every feature still falls in the first class,
  # so the MAP was never wrong -- only the legend beside it, which is
  # the part a reader trusts to say what the colours mean. One class
  # is the honest picture, and the dialog says so in words as well
  # (see constant_field_message). Placed after the Unclassed line so
  # it overrides that scheme's fixed 50 too.
  index = source.fields().indexOf(field)
  # One pass over the column answers all three questions below: how
  # many distinct values there are, whether it is constant, and
  # whether it contains nulls.
  values = source.uniqueValues(index) if index >= 0 else set()
  distinct = distinct_numeric_count(values) if index >= 0 else 0
  if distinct == 1:
    k = 1
  elif not unclassed and 0 < distinct < int(k):
    # The general form of the constant case, and the constant case is
    # its n == 1 instance. Five classes over three distinct values
    # gives five ranges of which two are DEGENERATE: a value sits on
    # a break, QGIS gives it to the first range containing it, and
    # the ranges above never paint. Measured 2026-08-13 with a render
    # context, k=5 over {1, 5, 9}: five swatches, three colours on
    # the map, the highest value drawn mid-grey while the legend's
    # black sat beside a range nothing occupied. Upstream reduces k
    # in exactly this case (_plot_subsetted_gdf sets cspec["k"] to
    # the value count), so this follows the library rather than
    # inventing a rule.
    #
    # Unclassed is exempt: its fifty steps reproduce a continuous
    # ramp rather than a class count anybody chose, and cutting them
    # to the number of distinct values would turn a settled
    # continuous look into a coarse classed one.
    k = distinct
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
  # directly): a column holding an infinity or a NaN comes back with
  # NaN class bounds, so every tile falls outside every class, the
  # layer paints nothing and the run reports success. Measured on the
  # memory provider and through OGR on a GeoPackage.
  #
  # This comment used to say that Natural breaks (Jenks) SEGFAULTS on
  # such a column -- exit 139, the application gone with the user's
  # unsaved project. RE-MEASURED 2026-08-12 across nine combinations
  # (infinities with NaN, +/-1e308, and both together, each through
  # quantiles, natural breaks and equal intervals) and nothing
  # crashed on QGIS 4.0.3. That is not proof the original measurement
  # was wrong -- a larger column or another provider may still do it
  # -- so it is recorded as UNREPRODUCED rather than deleted. The NaN
  # half reproduces exactly and is what the canary now asserts.
  #
  # The fix hands the classifier different INPUT rather than
  # replacing its arithmetic: one clause more on the subset string
  # this function already sets and restores. NaN fails every
  # comparison and the infinities fall outside the bounds, so the
  # classifier sees only finite numbers and its own four algorithms
  # go on deciding the breaks.
  #
  # DELETE THIS when test_qgis_still_mishandles_non_finite_class_breaks
  # fails: that canary drives QGIS's classifier directly, so its
  # failure means QGIS has been fixed and this clause is redundant.
  # It did not exist when this comment first named it, which is worse
  # than naming nothing -- a reader was told to watch for something
  # that could not happen. Written 2026-08-12. The NULL
  # half above has its own canary (test_qgis_still_counts_nulls_as_
  # zero) and they may well not be fixed together, so check both
  # before removing either.
  # ---- PINNED BOUNDS, which ride the same filtering
  #
  # A pin is a class bound a person set: the first class's upper
  # bound, the last class's lower bound, or both. The samples inside
  # a pinned class leave the pool, the scheme cuts what the row asked
  # for MINUS one class per pin, and the pinned classes are put back
  # around the result afterwards (_apply_pinned_bounds, which also
  # snaps the middle to meet them).
  #
  # It is done by extending the subset string this function already
  # sets and restores, for the reason the null workaround gives: hand
  # the classifier different INPUT rather than replacing its
  # arithmetic. Quantiles, equal intervals, Jenks and pretty breaks go
  # on being QGIS's, so the plugin cannot drift from the panel the
  # user opens next.
  low_pin = high_pin = None
  if pinned:
    low_pin = pinned.get("low")
    high_pin = pinned.get("high")
  finite_values = sorted(
    float(v) for v in values
    if v is not None and v != NULL and isinstance(v, (int, float))
    and math.isfinite(float(v)))
  if not finite_values:
    low_pin = high_pin = None
  pins = (low_pin is not None) + (high_pin is not None)
  # What is left for the scheme to cut. It can be NOTHING -- both ends
  # pinned on a two-class row asks for two classes and names both of
  # them -- and the classifier cannot be asked for zero, so it is
  # asked for one and the answer is thrown away below. Without that,
  # a two-class row with two pins drew three.
  wants_middle = int(k) - pins > 0
  if pins:
    k = max(1, int(k) - pins)
  FINITE = 1e307
  restore = None
  awkward = any(
    v is None or v == NULL or (isinstance(v, float)
                               and (v != v or abs(v) > FINITE))
    for v in values)
  if index >= 0 and (awkward or pins):
    previous = source.subsetString()
    clause = (f'"{field}" IS NOT NULL AND "{field}" > {-FINITE:g} '
              f'AND "{field}" < {FINITE:g}')
    if low_pin is not None:
      clause += f' AND "{field}" > {float(low_pin):.17g}'
    if high_pin is not None:
      clause += f' AND "{field}" < {float(high_pin):.17g}'
    combined = f"({previous}) AND {clause}" if previous else clause
    # A provider may refuse a subset string. Wrong breaks beat no map,
    # so a refusal falls through to classifying everything, exactly as
    # before this block existed.
    if source.setSubsetString(combined):
      restore = previous
  try:
    # `source` and not `layer`: the breaks come from the whole map's
    # values (see above), and the filtering just applied belongs to
    # whichever layer is about to be scanned. When no values were
    # handed over the two are the same object and this is the
    # behaviour that shipped before.
    renderer.updateClasses(source, k)
  finally:
    if restore is not None:
      source.setSubsetString(restore)
  if pins:
    _apply_pinned_bounds(renderer, low_pin, high_pin, finite_values[0],
                         finite_values[-1], outline, method,
                         wants_middle)
  # A single class spans the whole ramp and QGIS colours it from the
  # ramp's START (measured, QGIS 4.0.3: one class on Reds comes back
  # #fff5f0, the ramp's 0.0 endpoint) -- for a sequential ramp that is
  # near-white, which on the map reads as "no data" rather than "one
  # value". The ramp's MIDDLE is the honest colour for a constant
  # column: unmistakably a member of the chosen ramp without claiming
  # either extreme. get_ramp has already applied any reversal, so the
  # sample is taken in the ramp as the user sees it. The point sampled
  # is the middle of the DISPLAY WINDOW, which is 0.5 only when the
  # window is the whole ramp -- the comment above the sample itself
  # says so correctly, and this paragraph contradicted it until
  # 2026-08-12. (User decision, 2026-08-09.)
  # Every symbol below is built FRESH rather than cloned off a range:
  # ``renderer.ranges()`` hands back temporaries, and a symbol
  # pointer read off one dangles as soon as the temporary dies --
  # cloning through it segfaulted QGIS outright when this block was
  # first written.
  lo, hi = range_bounds
  count = len(renderer.ranges())
  if distinct == 1 and count:
    # One class ranges over the whole window, and QGIS colours it
    # from the ramp's START (measured: near-white on Reds), which on
    # the map reads as "no data" rather than "one value". The
    # window's MIDDLE is the honest colour -- the plain ramp middle
    # when the window is the whole ramp. (User decision, 2026-08-09.)
    mid = get_ramp(ramp_name, reverse).color((lo + hi) / 200.0).name()
    renderer.updateRangeSymbol(0, _fill_symbol(mid, outline))
  elif ((lo, hi) != (0, 100) or pins) and count:
    # the Ramp Display Range: first class at lo, last at hi, linear
    # between. Skipped at (0, 100) UNLESS a bound is pinned, because
    # QGIS's own colours already ARE this formula there and
    # recolouring would only add a place for the two to disagree --
    # but with a pin they are not: updateClasses coloured the MIDDLE
    # classes across the whole ramp before the pinned ones were put
    # back around them, so the pinned classes would have no colour at
    # all and the middle would wear the extremes. Recolouring the
    # full set restores exactly what QGIS would have drawn for this
    # many classes.
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
  renderer = QgsCategorizedSymbolRenderer(field, categories)
  # Record WHICH RAMP produced these classes, exactly as the graduated
  # path does two hundred lines above. QGIS keeps this on the renderer
  # as the ramp a fresh classify would use, and until 2026-08-13 the
  # categorized path set it on neither its own output nor anything
  # else, which cost two things.
  #
  # A user opening QGIS's Categorized panel on one of our element
  # layers found the ramp field EMPTY, so nothing there said which
  # ramp the colours came from and pressing Classify started from
  # whatever the panel happened to show.
  #
  # And it made dialog._on_layer_style_edited's clean-ramp branch
  # unreachable. That branch asks _ramp_name_matching what ramp a
  # dock-side renderer carries, so that re-applying the ramp the
  # dialog already names clears the hand-picks it replaces; against a
  # renderer with no source ramp it always answered None, so a clean
  # classify was adopted as Custom hand-picks instead and the ramp
  # cell never went back to naming a ramp. The graduated twin at
  # dialog.py:3501 worked the whole time, which is why nobody noticed:
  # the behaviour was right for half the styles.
  #
  # Cloned rather than handed over, because `ramp` is still being read
  # above for the preset colours and the renderer takes ownership of
  # what it is given.
  if ramp is not None:
    renderer.setSourceColorRamp(ramp.clone())
  return renderer


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
                  template: dict | None = None,
                  classify_from=None) -> None:
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
    classify_from: the whole map's values for this element's column,
      handed straight to make_graduated_renderer so that every
      element carrying one variable gets the same breaks. Ignored
      off graduated rows, where there are no breaks to cut. The
      assignment's ``pinned`` bounds travel the same way.

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
      assignment.get("quant_colours"), classify_from,
      assignment.get("pinned")))
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


def drop_gpkg_layer(path: str, layer_name: str) -> bool:
  """Best-effort: remove one table from a GeoPackage.

  Args:
    path: the .gpkg file to edit.
    layer_name: the table to remove, which the CALLER must have
      written itself. Nothing here checks that, and nothing can: a
      GeoPackage is an ordinary file a user may keep other data in,
      so deciding what is ours to delete belongs with whoever wrote
      it. The dialog passes only element tables it wrote on its own
      previous run into this same file.

  Returns:
    True when the table is gone, False when there was nothing to
    remove or the file would not open. Never raises: this tidies up
    after a design that shrank, and failing to tidy must not fail the
    run that produced the map.

  Why it exists: a run writes one table per element and REPLACES
  those it writes, so a session that goes from six elements to three
  used to leave the other three behind. The map is right and the file
  is wrong -- and the file is the thing that gets sent to somebody
  else, who opens it and finds layers belonging to a design that no
  longer exists, with no way to tell which three are the map.
  """
  try:
    from osgeo import ogr
  except ImportError:
    return False        # no GDAL bindings: leave the file untouched
  source = None
  try:
    # 1 = open for update; the DELETE below is a no-op otherwise
    source = ogr.Open(path, 1)
    if source is None:
      return False
    for index in range(source.GetLayerCount()):
      if source.GetLayer(index).GetName() == layer_name:
        source.DeleteLayer(index)
        return True
    return False
  except Exception:
    return False
  finally:
    # closing the dataset is what flushes the change to disk
    source = None


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
  from . import compat
  name = layer.name()[:30]
  try:
    # through compat: the call this used to make directly is
    # deprecated, and a deprecated call is what a later QGIS breaks
    compat.save_style_to_database(layer, name, "seeded by WeavingSpace")
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
