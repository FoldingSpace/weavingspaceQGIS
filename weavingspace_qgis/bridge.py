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

# The absence vocabulary -- the no-data grey, the three kinds a
# graduated renderer cannot place, the column they are stamped into --
# is DEFINED in absence.py and re-exported here, so every existing
# `bridge.NO_DATA_FILL` and `bridge.ABSENCE_KINDS` still resolves.
# It moved out on 2026-08-16 for one reason: perception.py must know
# which fills are placeholders (they are identical across elements, so
# comparing them reports a clash in every design that has one) and
# perception.py is deliberately importable without QGIS, which this
# module is not. absence.py imports nothing, so both can read it and
# neither has to keep a copy that could go stale. See its docstring.
from .absence import (  # noqa: E402  (constants, read as such)
  ABSENCE_BY_VALUE,
  ABSENCE_FIELD,
  ABSENCE_KINDS,
  ABSENCE_VALUE,
  NEG_INF_KEY,
  NO_DATA_FILL,
  NO_DATA_KEY,
  POS_INF_KEY,
)

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


def count_areas_with_no_geometry(layer) -> int:
  """How many of a layer's rows carry no geometry at all.

  Args:
    layer: the region layer, asked directly rather than through the
      frame -- because the frame is where they have already gone.

  Returns:
    The number of rows whose geometry is missing or empty. 0 for any
    dataset that came out of a working editing session, which is why
    the cost is a single pass on the generate path and nowhere else.

  ``layer_to_gdf`` skips these rows when it builds the frame, and has
  since long before this function: a blank row cannot be tiled, and
  handing one to the library is how icon mode meets a centroid that
  does not exist. What it did not do was SAY so. The row simply was
  not there, the coverage count never saw it, and a user comparing
  their attribute table against the map found one row unaccounted
  for with nothing on screen to explain it.

  Deliberately not folded into the coverage sentence, which names a
  spacing as the thing to change. No spacing draws a row that has no
  geometry, and telling those two situations apart is the point.
  """
  blank = 0
  for feature in layer.getFeatures():
    geometry = feature.geometry()
    if geometry is None or geometry.isEmpty():
      blank += 1
  return blank


def unmappable_areas_message(blank: int, total: int):
  """The notice for rows that carry no geometry.

  Args:
    blank: how many rows had no geometry to draw.
    total: how many rows the region layer holds altogether.

  Returns:
    One sentence for the message bar, or None when every row had a
    geometry, which is the ordinary case.
  """
  if blank <= 0:
    return None
  return (f"{blank:,} of {total:,} areas have no geometry, so they are "
          f"left out of the map. No spacing will draw them.")


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


def expressible_style(renderer):
  """What a plugin row would have to say to describe this renderer.

  Args:
    renderer: any ``QgsFeatureRenderer`` taken off a layer, or None.

  Returns:
    ``(mode, scheme)`` the dialog can put in a row — ("Graduated",
    "Quantiles"), ("Graduated", "Unclassed"), ("Categorized", None) or
    ("Single colour", None) — or None when no row can express it,
    which is the cue to DEFER to QGIS.

  This is the whole of the "can we say this?" question, in one place,
  because it is asked from three directions that must agree: when the
  styling dock changes a layer, when a project is reopened, and when a
  layer comes back out of a GeoPackage. Three callers reaching three
  answers is the shape that has cost this project most.

  UNCLASSED is recognised by its construction rather than by a flag,
  since QGIS has no such concept: the plugin draws it as fifty equal
  intervals, so fifty equal-interval classes is what it looks like
  coming back. A user who builds fifty equal intervals by hand gets
  Unclassed, which is what they made.

  Rule-based, inverted-polygon, 2.5D, heatmap, null and anything else
  return None. So does a graduated renderer classified by a method the
  plugin does not offer -- the classes are real and the map is fine,
  and the row simply cannot name it.
  """
  if renderer is None:
    return None
  name = type(renderer).__name__
  if name == "QgsSingleSymbolRenderer":
    return ("Single colour", None)
  if name == "QgsCategorizedSymbolRenderer":
    return ("Categorized", None)
  if name != "QgsGraduatedSymbolRenderer":
    return None
  from . import compat
  scheme = compat.scheme_for_method(
    renderer.classificationMethod()
    if hasattr(renderer, "classificationMethod") else None)
  if scheme is None:
    return None
  if scheme == "Equal intervals" and len(renderer.ranges()) == 50:
    return ("Graduated", "Unclassed")
  return ("Graduated", scheme)


def renderer_has_data_defined_fill(renderer) -> bool:
  """Does this renderer decide a fill colour per feature?

  Args:
    renderer: any ``QgsFeatureRenderer``, or None.

  Returns:
    True when any symbol's fill colour comes from an expression or a
    field rather than from the symbol itself.

  Why the caller wants to know. ``symbols()`` hands back the BASE
  symbol, which is what a data-defined renderer starts from and not
  what any feature is painted. A swatch built from it would show one
  confident colour for a map drawing hundreds — the plugin describing
  a map it will not draw, which is the failure the Custom display and
  the hatched stripes both exist to prevent. An unknown is drawn as an
  unknown, never as a certainty.
  """
  if renderer is None:
    return False
  try:
    from qgis.core import QgsRenderContext, QgsSymbolLayer
    for symbol in renderer.symbols(QgsRenderContext()) or []:
      for index in range(symbol.symbolLayerCount()):
        properties = symbol.symbolLayer(index).dataDefinedProperties()
        for key in ("PropertyFillColor", "PropertyStrokeColor"):
          prop = getattr(QgsSymbolLayer, key, None)
          if prop is not None and properties.isActive(prop):
            return True
  except Exception:
    # A renderer that cannot be asked is not evidence of anything;
    # the caller falls back to its neutral display either way.
    return False
  return False


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
  # ...and for a renderer of some OTHER kind -- rule-based, and
  # anything else a user builds in the styling panel -- the base
  # class's own `symbols()` answers, in the renderer's own order.
  # Without this the function returned nothing for exactly the case
  # the deferring display needs it for (2026-08-15).
  if type(renderer).__name__ not in (
      "QgsGraduatedSymbolRenderer", "QgsCategorizedSymbolRenderer",
      "QgsSingleSymbolRenderer") and renderer is not None:
    try:
      from qgis.core import QgsRenderContext
      for symbol in renderer.symbols(QgsRenderContext()) or []:
        colour = symbol.color()
        colours.append((colour.red(), colour.green(), colour.blue()))
    except Exception:
      return []
    return colours
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


def icon_coverage_message(short: dict, unit_count: int,
                          spacing: float, unit_label: str) -> str | None:
  """The warning coverage_message cannot give, for icon mode.

  Args:
    short: {element id: how many areas that element has no icon for},
      already filtered to the elements that are short.
    unit_count: how many areas the region layer holds altogether.
    spacing: the spacing this run used, in the region's map units.
    unit_label: what those units are called.

  Returns:
    One sentence for the message bar, or None when every element has
    an icon for every area.

  WHY THIS IS SEPARATE from `coverage_message`. That one asks a
  MAP-WIDE question -- did any area get a tile anywhere -- and in
  icon mode the answer is yes even when half the elements have no
  icon for it, because the other half does. Measured 2026-08-16 on a
  144-area region with four elements: at 6,000 and 9,000 spacing two
  elements carried 132 icons and two carried 144, so twelve areas
  were missing from half the map and nothing was said, while the same
  loss in ordinary tiling mode is reported.

  Its sentence could not simply be reused: "appear nowhere on the
  map" would be FALSE of those areas, since the other elements do
  draw them. Trading silence for a wrong statement is not an
  improvement, so this says the thing that is true instead -- which
  elements, and how many areas each is missing.
  """
  if not short:
    return None
  spacing_text = f"{spacing:,.6f}".rstrip("0").rstrip(".")
  worst = max(short.values())
  named = ", ".join(sorted(short))
  return (f"At {spacing_text} {unit_label} spacing, elements {named} "
          f"have no icon for up to {worst:,} of {unit_count:,} areas, "
          f"which other elements still draw.")


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

    THE QUESTION IS MAP-WIDE, and in ICON MODE that makes it blind to
    a real loss. `count_units_without_tiles` counts areas that got a
    tile ANYWHERE, so an area still represented by one element is not
    missing even when another element has no icon for it. Measured
    2026-08-16 on a 144-area region with four elements: at 6,000 and
    9,000 spacing two elements carried 132 tiles and two carried 144,
    so twelve areas had no icon on half the map and this said
    nothing, while the same twelve at the same spacing in ordinary
    tiling mode are reported. At 400 all four carried 144.

    Whether that should change is the maintainer's call and is open:
    the sentence as written ("appear nowhere on the map") would be
    FALSE of those areas, so firing it unchanged would trade silence
    for a wrong statement, and a per-element count needs its own
    wording and its own review. Raised 2026-08-16 under #45.

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
    missing: how many mapped areas hold nothing a graduated
      renderer can place for it -- a NULL, a NaN or an
      infinity, counted through `cannot_be_placed`.
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
  # "DO NOT HAVE FINITE NUMERIC DATA" rather than "have no value"
  # (maintainer's wording, 2026-08-16). The count widened that day to
  # everything a graduated renderer cannot place -- a NULL, a NaN and
  # either infinity -- and "no value" is exactly true of the first and
  # false of an infinity, which is a value and simply not a finite
  # one. The sentence now covers what it counts.
  return (f"{missing:,} of {total:,} areas do not have finite numeric "
          f"data for '{field}'. They draw as no data, outside the "
          f"class breaks.")


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


def pin_problem(low, high, values, asked: int, breaks=None):
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
    breaks: the interior boundaries of a COPIED ladder already in
      force on this element, or None. A pin on top of a copy moves
      one of those boundaries, so it must not cross the next one.

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
    # The whole word is interpolated, never a word split across a
    # placeholder. "boundar{}" reads as a typo to anybody meeting it
    # in the text-review queue, which is where every sentence a user
    # sees is read before it ships, and a reviewer should never have
    # to reconstruct a word from a format string.
    boundaries = "boundary" if available == 1 else "boundaries"
    return (f"A {int(asked)}-class scheme has {available} "
            f"{boundaries} to pin, so it cannot carry {pins}. Ask "
            f"for more classes, or unpin one end.")
  # A pin sitting on top of a COPIED ladder moves one of that ladder's
  # boundaries, and it must not cross its neighbour: the ladder would
  # stop being monotonic and a class would run backwards. Checked here
  # rather than clamped there, because a typed number is honoured or
  # visibly rejected and never quietly changed.
  ladder = [float(b) for b in (breaks or [])]
  if ladder:
    if low is not None and len(ladder) > 1 and float(low) >= ladder[1]:
      return (f"The first class cannot end at {_trim(low)}: the copied "
              f"classes put the next break at {_trim(ladder[1])}.")
    if high is not None and len(ladder) > 1 and float(high) <= ladder[-2]:
      return (f"The last class cannot begin at {_trim(high)}: the "
              f"copied classes put the break before it at "
              f"{_trim(ladder[-2])}.")

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


class _AlreadyClassified(Exception):
  """Raised to skip the classifier when a copied ladder decided the
  breaks. An exception rather than a branch because the subset string
  is set and restored around that call in a try/finally, and a second
  code path around it is how one of the two comes to forget the
  restore."""


def _trim(value: float) -> str:
  """A number as a person would write it, with trailing zeros gone."""
  text = f"{float(value):.6g}"
  return text


def classes_the_map_will_draw(values, asked, pinned=None, unclassed=False):
  """How many classes this column actually draws, pins included.

  Args:
    values: every value of the column, from the REGION layer.
    asked: the class count the table asked for.
    pinned: the element's pin record, or None. A copied ladder's
      "breaks" decide their own count; "low" and "high" narrow the
      pool the scheme cuts from.
    unclassed: True when the row is Quant: Unclassed, which is EXEMPT
      from the reduction -- its fifty steps reproduce a continuous
      ramp rather than a class count anybody chose, so the renderer
      does not reduce them and neither may this. Omitted, it defaults
      False, which is the classed behaviour every other scheme wants.

  Returns:
    (count, from_a_pinned_pool). The count is what the legend will
    hold; the flag says whether the reduction came from the pool
    between the pins rather than from the whole column, which is what
    the notice needs in order to be true.

  ONE QUESTION ASKED ONCE. Both notice sites used to count the whole
  column and compare against k, which is right until a pin removes a
  class from the ladder AND its samples from the pool -- after which
  the sentence describes a legend the map does not have, which is the
  precise thing these notices exist to prevent. This is the same
  arithmetic make_graduated_renderer performs, kept beside it so the
  two cannot drift.
  """
  # A COPIED LADDER DECIDES ITS OWN COUNT, and the docstring above
  # used to assert that such a record "never comes through here" --
  # while `_legend_size_note` passed the whole record, which made the
  # assertion false the day it was written. Measured 2026-08-15 by a
  # hunt: a ladder of five copied onto a column holding {1, 5, 9} drew
  # FIVE classes, exactly as the copy feature intends, while the
  # message bar said it drew three. A copy's unreachable classes are
  # KEPT and hatched by design, so there is no reduction to report,
  # and saying otherwise describes a legend the map does not have --
  # the one thing these notices exist to prevent.
  #
  # When a docstring asserts that a case cannot arrive, grep the
  # callers before believing it.
  # QUANT: UNCLASSED IS EXEMPT FROM THE REDUCTION, and this is the
  # half that went missing. `make_graduated_renderer` reduces only
  # `if not unclassed`, because Unclassed reproduces a CONTINUOUS ramp
  # -- its fifty steps are the shape of the reproduction rather than a
  # class count anybody chose, so drawing fewer of them would not be
  # reproducing it. This helper was never told the scheme, so it went
  # on reducing, and the message bar told a user with twelve distinct
  # values that their Unclassed element "draws as 12 classes, not 50"
  # while the map drew fifty. Found by a hunt pointed at the settled
  # decisions, 2026-08-16, and reported by the maintainer the same
  # night as something they did not want to see.
  #
  # The docstring above claims this is the same arithmetic
  # make_graduated_renderer performs, "kept beside it so the two
  # cannot drift". That claim is only true now.
  if unclassed:
    return int(asked), False
  breaks = (pinned or {}).get("breaks")
  if breaks:
    return len(breaks) + 1, False
  finite = [float(v) for v in values
            if v is not None and v != NULL and isinstance(v, (int, float))
            and math.isfinite(float(v))]
  low = (pinned or {}).get("low")
  high = (pinned or {}).get("high")
  pins = (low is not None) + (high is not None)
  whole = distinct_numeric_count(finite)
  if not pins or int(asked) - pins <= 0:
    return (min(whole, int(asked)) if whole else int(asked)), False
  middle = [v for v in finite
            if (low is None or v > float(low))
            and (high is None or v < float(high))]
  middle_distinct = distinct_numeric_count(middle)
  room = int(asked) - pins
  if 0 < middle_distinct < room:
    return middle_distinct + pins, True
  return (min(whole, int(asked)) if whole else int(asked)), False


def few_values_message(field: str, distinct: int, asked: int,
                       pinned: bool = False):
  """The notice for a column with fewer distinct values than classes.

  Args:
    field: the attribute name, as the user chose it in the table.
    distinct: how many distinct finite values the REGION layer holds
      for it — the user's own areas, not the tiles, for the same
      reason missing_values_message counts areas.
    asked: how many classes the table asked for.
    pinned: whether the count came from the pool a PIN left rather
      than from the whole column, which changes the sentence: the
      column still holds every value it held, and a notice saying
      otherwise would send a user looking for data they have not
      lost. Defaults to False, the plain case.

  Returns:
    One sentence for the message bar, or None when every class the
    row asked for is occupied, so the caller can report
    unconditionally.

  WHAT THIS SENTENCE SAYS CHANGED ON 2026-08-16, with the behaviour
  it describes. It used to report a REDUCTION -- "draws as 3 classes,
  not 5" -- because the class count really was cut to the number of
  distinct values. That cut re-sampled the ramp across the survivors
  and moved colours nobody had chosen to move, so it was removed on
  the maintainer's ruling: the ladder keeps the length the row asked
  for, every class keeps the colour of its position, and the classes
  no tile can reach are hatched in the swatch instead.

  So the notice now reports EMPTINESS rather than shortening. It
  still earns its place for the reason the old one did: a user whose
  Classes spinner reads five while two swatches are hatched deserves
  to be told why, in words, rather than left to work it out from a
  pattern of diagonal lines.

  A column with ONE distinct value says nothing here: it genuinely
  does collapse to a single class, which is the maintainer's
  instruction of 2026-08-09, and `constant_field_message` is the
  sentence for it.
  """
  if distinct >= asked or distinct <= 1:
    return None
  empty = int(asked) - int(distinct)
  if pinned:
    return (f"'{field}' has {distinct} distinct values left between "
            f"its pinned bounds, so {empty} of the {asked} classes "
            f"are empty and their swatches are hatched.")
  return (f"'{field}' has {distinct} distinct values, so {empty} of "
          f"the {asked} classes are empty and their swatches are "
          f"hatched.")


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
  set_class_bounds(renderer, bounds, outline, method)


def set_class_bounds(renderer, bounds, outline, method):
  """Replace a renderer's classes with an exact list of bounds.

  Args:
    renderer: the graduated renderer to rewrite.
    bounds: ``[(lower, upper), ...]`` in class order, contiguous.
    outline: whether tiles are stroked, for the symbols built here.
    method: the classification method, asked for its own label text
      so these classes are labelled the way computed ones are.

  Returns:
    None; the classes are replaced in place, uncoloured. The caller
    colours them, because who decides a class's colour depends on
    whether a display window or a hand-pick is in force.

  Two callers: the pinned classes put back around a computed middle,
  and a whole ladder copied from another element. They share this so
  a copied class and a pinned one cannot come to be built or
  labelled differently.
  """
  renderer.deleteAllClasses()
  # QGIS 4's addClass takes a SYMBOL only (measured: the
  # QgsRendererRange overload of older versions is gone), so each
  # class is added and then given its bounds and label by index.
  for _lower, _upper in bounds:
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


def unworn_classes(bounds, values):
  """Which classes no value falls into.

  Args:
    bounds: ``[(lower, upper), ...]`` in class order, as a graduated
      renderer holds them.
    values: the values actually drawn -- the element's own, since the
      question is what THIS element uses.

  Returns:
    A list of class indices nothing occupies, in order. Empty when
    every class is worn, which is the ordinary case.

  QGIS's own containment rule, so this cannot disagree with the map
  it describes: a value belongs to the FIRST range that contains it,
  and a range holds ``lower <= v <= upper`` -- INCLUSIVE AT BOTH
  ENDS, which is what a graduated renderer actually does.

  THAT LAST WORD WAS WRONG UNTIL 2026-08-16 and it mattered the
  moment the degenerate-range nudge arrived. This used to exclude the
  lower bound for every range but the first, which agrees with the
  renderer while the ranges touch -- a value on a shared boundary is
  caught by the range BELOW it, earlier in the loop, so first-match
  hides the difference. Once `_nudge_off_shared_bounds` moves that
  lower range's top down by an ulp, the boundary value falls through
  to the degenerate range that means exactly it, and the renderer
  accepts it there while this rule refused it. Measured: with 1, 5, 9
  in five classes the map drew classes 1, 3 and 5, and this reported
  classes 2, 3, 4 and 5 unworn -- hatching two swatches that were in
  use.

  A class nothing occupies is a swatch in the legend no tile uses.
  Since the class count is no longer reduced to the value count, that
  is an ordinary situation rather than a rarity, and it is also
  reachable by COPYING a ladder from an element carrying another
  column. Either way they are kept rather than dropped and marked
  instead.
  """
  numbers = [float(v) for v in values
             if v is not None and v != NULL and isinstance(v, (int, float))
             and math.isfinite(float(v))]
  worn = set()
  for value in numbers:
    for index, (lower, upper) in enumerate(bounds):
      if lower <= value <= upper:
        worn.add(index)
        break
  return [index for index in range(len(bounds)) if index not in worn]


def fitted_breaks(breaks, smallest, largest):
  """A copied ladder of breaks, fitted to the receiving column.

  Args:
    breaks: the INTERIOR boundaries of the ladder being copied, in
      order -- k-1 numbers for a k-class ladder. The outer edges are
      not carried, being the data's own extremes by definition.
    smallest, largest: the receiving column's extremes.

  Returns:
    ``[(lower, upper), ...]``, one pair per class, contiguous, with
    the outermost edges at the receiving column's min and max. None
    when there is nothing to fit.

  THE END RULES, which are the maintainer's own specification
  (2026-08-14) and are what make a ladder copied from one variable
  usable on another. The highest class's upper bound and the lowest
  class's lower bound become the receiving column's max and min.
  Where that column's max sits BELOW the upper class's lower bound,
  the two are made equal and the top class collapses; where its min
  sits above the lower class's upper bound, the lower class's lower
  bound is set to its upper and the bottom class collapses. Since
  breaks are cut from the region's values for a field, two elements
  on the SAME variable share a data range and none of this bites --
  these rules exist for copying ACROSS variables, which is the case
  the feature is really for.

  A collapse moves the OUTER edge and never a copied boundary, and
  the first draft did the opposite: pulling the top class's lower
  bound down to a smaller column's max produced (30, 3) -- a class
  running backwards -- whenever more than one copied break sat above
  that max. Measured on breaks [4, 14.2, 30, 55] fitted to a column
  running 0 to 3. The ladder must stay monotonic whatever it is
  fitted to, so the collapse is expressed as an outer edge meeting
  its neighbour rather than as a boundary being dragged.

  What is NOT done here is dropping interior boundaries the receiving
  data cannot reach. They are KEPT, deliberately: a copy is supposed
  to reproduce a classification, and a silently shortened one does
  not. The emptiness is made visible instead, by hatching the swatch
  stripes no tile can use.
  """
  interior = [float(b) for b in (breaks or [])]
  if not interior:
    return None
  low, high = float(smallest), float(largest)
  bounds = [(min(low, interior[0]), interior[0])]
  for index in range(1, len(interior)):
    bounds.append((interior[index - 1], interior[index]))
  bounds.append((interior[-1], max(high, interior[-1])))
  return bounds


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


def cannot_be_placed(value) -> bool:
  """Whether a graduated renderer has nowhere to draw this value.

  Args:
    value: one attribute value, as QGIS hands it back -- Python None
      for a NULL, or a float which may be NaN or infinite.

  Returns:
    True when the value belongs on the paired No Data layer rather
    than in any class: a NULL, a NaN, or an infinity. False for
    anything a classifier can place, including text, which a
    graduated element never carries.

  ONE OWNER, because this question is asked in five places and the
  answer drifted apart three times in a single day. The split widened
  from "missing" to "the classifier cannot place this" so it would
  catch an infinity, and each reader had to be found separately
  afterwards: `_column_has_nulls`, which decides whether an element
  needs a split at all; `_element_has_missing_values`, which decides
  whether the colour editor offers a No data row; and the count
  behind the missing-values notice, which told a user 2 of 144 areas
  while the map drew 9 no-data tiles across 7 areas -- and said
  NOTHING AT ALL when the only unplaceable values were infinities,
  so grey patches appeared with no explanation.
  Each was a one-line scan for NULL that looked complete on its own.
  Deriving the rule once is the only way the map and the sentences
  about it can agree.
  """
  if value is None or value == NULL or str(value) == "NULL":
    return True
  if isinstance(value, float):
    # the only value not equal to itself is a NaN; the comparisons
    # catch either infinity. Both are ordinary values to QGIS, which
    # is why neither was noticed by a scan looking for absence.
    return value != value or value in (float("inf"), float("-inf"))
  return False


def _nudge_off_shared_bounds(renderer) -> int:
  """Let a repeated value reach the class that stands for it.

  Args:
    renderer: a QgsGraduatedSymbolRenderer whose classes have just
      been computed. Mutated in place.

  Returns:
    How many ranges were moved, which is zero for ordinary data. The
    count is returned so a caller or a test can assert that the
    adjustment did or did not happen, rather than inferring it.

  THE PROBLEM, measured on QGIS 4.0.3, 2026-08-16. Ask for five
  quantile classes over a column holding 1, 5 and 9 and QGIS returns
  ``1..1, 1..5, 5..5, 5..9, 9..9``. Three of those are DEGENERATE, and
  a graduated renderer gives a value to the FIRST range that contains
  it -- so 5 goes to ``1..5`` and 9 to ``5..9``, the two degenerate
  ranges above them can never be reached at all, and the map draws its
  highest value mid-grey while the legend's black sits beside a range
  nothing occupies. A reader matching the darkest swatch to "high"
  reads that map wrongly.

  THE FIX IS ONE UNIT IN THE LAST PLACE. Shrink the upper bound of
  every FINITE-WIDTH range, leaving the degenerate ones alone: a value
  sitting on a shared boundary then falls past the interval that was
  swallowing it and into the degenerate range that means exactly that
  value. Measured on the same case: 1, 5 and 9 land in classes 1, 3
  and 5, the highest value takes the darkest colour, and the ramp is
  used end to end.

  WHY IT IS SCOPED TO DEGENERATE RANGES. On ordinary data every range
  has width, and shrinking each upper bound would push any value
  sitting exactly on a break up into the next class -- reversing
  QGIS's own convention for no benefit whatever. So nothing happens
  unless the classifier has actually produced a degenerate range,
  which is its way of saying there were fewer distinct values than
  classes.

  WHAT THIS COSTS AND WHY IT IS STILL QGIS. The break values are
  QGIS's own; two of them move by an ulp, which its label formatter
  rounds away, so the legend still reads "1 - 5" and "5 - 9". The
  renderer stays an ordinary graduated renderer, so the styling panel,
  the QML round trip and the GeoPackage are unaffected, and pressing
  Classify in QGIS restores QGIS's untouched answer. It runs AFTER any
  pinned bounds, so it adjusts final bounds rather than ones a pin is
  about to rewrite.

  This replaces the class REDUCTION that stood here from 2026-08-14 to
  2026-08-16. Reducing k re-sampled the ramp across the survivors, so
  colours moved with nobody choosing to move them; keeping k and
  nudging leaves every class where it was. (Maintainer's ruling, and
  the nudge was the maintainer's idea.)
  """
  import math
  ranges = renderer.ranges()          # bound first: a temporary frees
  bounds = [(r.lowerValue(), r.upperValue()) for r in ranges]
  if not any(hi <= lo for lo, hi in bounds):
    return 0
  moved = 0
  for index, (lo, hi) in enumerate(bounds):
    # ONLY WHERE THE NEXT RANGE IS THE DEGENERATE ONE THAT WANTS THIS
    # BOUNDARY VALUE. Anything wider than that does harm:
    #
    # THE LAST RANGE MUST NEVER MOVE, because its upper bound is the
    # column's MAXIMUM. Shrinking it left the largest value belonging
    # to no range at all, so QGIS gave it no symbol and the map drew
    # a HOLE where the darkest tile should be, while the legend still
    # listed a class for it and a lower value wore the darkest
    # colour. Found within the hour by two hunts independently and
    # reproduced here: values [10]*8 + [20, 30] under Quantiles at
    # k=5 left 30 homeless, confirmed by rendering onto a coloured
    # ground, where that tile came back as the background.
    #
    # AND A RANGE WHOSE SUCCESSOR HAS WIDTH must not move either.
    # There is no degenerate class waiting to catch the boundary
    # value, so nudging would push it up into an ordinary class it
    # does not belong to -- which is the same convention-reversal the
    # scope test above exists to prevent, arriving one range at a
    # time instead of all at once.
    #
    # The first version of this loop had neither test and shipped
    # green, because its fixture ({1, 5, 9}) is degenerate at the TOP,
    # which is the one shape where the harm cannot appear. When a fix
    # ships with a single hand-made case, vary the case before
    # trusting the green.
    if index + 1 >= len(bounds):
      continue
    next_lo, next_hi = bounds[index + 1]
    if hi > lo and next_hi <= next_lo and next_lo == hi:
      # A MARGIN, NOT ONE UNIT IN THE LAST PLACE. The first version
      # stepped by `math.nextafter`, which made a tile's class depend
      # on the LAST BIT of a number -- and anything that perturbs a
      # float by an ulp then moves that tile between classes. It duly
      # broke the GeoPackage round trip on every platform: the
      # reloaded file-backed layers painted differently from the ones
      # the dialog had made, 2,413 of 48,948 pixels.
      #
      # A relative margin of 1e-9 is enormous beside any rounding a
      # store or a recomputation can introduce (which is ~1e-16
      # relative), and invisible beside anything a legend prints --
      # QGIS's formatter rounds it away, so the label still reads
      # "1 - 5". The `abs(hi) or 1.0` keeps it meaningful when the
      # bound is zero.
      #
      # It never crosses the range's own lower bound: with a margin
      # that wide a very narrow range could otherwise be turned
      # inside out, so the step is clamped and a range too narrow to
      # take it is left alone rather than inverted.
      margin = (abs(hi) or 1.0) * 1e-9
      shrunk = hi - margin
      if shrunk <= lo:
        continue
      renderer.updateRangeUpperValue(index, shrunk)
      moved += 1
  return moved


def quant_class_colours(ramp_name: str, reverse: bool, count: int,
                        range_bounds: tuple = (0, 100)) -> list:
  """The colours a graduated element wears, for a given ramp and k.

  Args:
    ramp_name: the ramp as the row names it, resolved through
      get_ramp, so QGIS's meaning for the name wins.
    reverse: whether the row's Reverse column is ticked.
    count: how many classes are drawn. One class is coloured from the
      MIDDLE of the window rather than its start, for the reason
      make_graduated_renderer gives at that branch.
    range_bounds: the Ramp Display Range as (lo, hi) percentages;
      (0, 100) is the whole ramp and is the default.

  Returns:
    A list of `count` colour names ("#rrggbb"), lowest class first.
    Empty when count is not positive or the ramp cannot be resolved --
    callers treat that as "cannot say" rather than as "no colours".

  WHY THIS IS A FUNCTION AND NOT THREE COPIES OF A ONE-LINER. QGIS
  colours class i at ramp.color(i/(k-1)) (measured, QGIS 4.0.3), and
  the plugin re-colours the same way when a display window or a pin
  is in force. That formula was written out twice in
  make_graduated_renderer, and a THIRD caller then needed it: reading
  an adopted layer back has to ask whether the ramp explains the
  colours that are drawn, and a reimplementation there would agree
  with itself rather than with the map. One owner means the question
  and the answer cannot drift apart.
  """
  if count <= 0:
    return []
  try:
    ramp = get_ramp(ramp_name, reverse)
  except Exception:
    return []
  if ramp is None:
    return []
  lo, hi = range_bounds
  colours = []
  for i in range(count):
    along = i / (count - 1) if count > 1 else 0.5
    colours.append(ramp.color((lo + (hi - lo) * along) / 100.0).name())
  return colours


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
  # AND NOTHING ELSE IS REDUCED. Between 2026-08-14 and 2026-08-16
  # this went on to cut k down to the number of distinct values
  # whenever there were fewer than the row asked for, following
  # upstream's `_plot_subsetted_gdf`. It was removed on the
  # maintainer's ruling, and the reason is about COLOUR rather than
  # about class counts.
  #
  # A REDUCED LADDER IS RE-SAMPLED, AND THAT MOVES COLOURS NOBODY
  # CHOSE TO MOVE. Class i takes ramp.color(i/(k-1)), so lowering k
  # re-spreads every surviving class across the whole ramp. Measured
  # 2026-08-16, five asked over four distinct values on Reds: the map
  # drew #fff5f0 #fca082 #e32f27 #67000d, which is the four-class
  # ladder exactly, and neither middle colour is one the five-class
  # ladder would have used. The three-value case looks correct only
  # by accident, since sampling three points and five points both
  # land on 0, half and 1. Worse, it is unstable: a column that
  # gains a value later re-colours every class, with nobody choosing
  # anything -- which is the one thing one-colour-one-meaning exists
  # to forbid.
  #
  # The maintainer's rule is that an empty class is INVISIBLE, NOT
  # DELETED. Keeping k satisfies it by construction: nothing is ever
  # re-sampled because the ladder never changes length, and the
  # classes no tile wears are HATCHED in the swatch by
  # `unworn_classes`, which already asks any graduated element's own
  # layer and needed no widening for this. The legend keeps entries a
  # reader can see are empty, which is what the hatching is for, and
  # the copy path -- which has always kept and hatched unreachable
  # classes -- stops being a special case.
  #
  # THE ONE-VALUE COLLAPSE ABOVE SURVIVES, deliberately: it is the
  # maintainer's instruction of 2026-08-09, and it answers a
  # different complaint. Five ranges all reading "7 - 7" in five
  # colours is a legend claiming variation the data does not have,
  # which hatching four of them would not cure. (Ruling 2026-08-16:
  # keep the smaller carve-out.)
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
  # A PIN THE DATA CAN NO LONGER CARRY IS DROPPED, because QGIS is
  # live and the plugin is not modal to it: a user can retype the
  # column, or reload the layer, long after pinning a bound, and a
  # pin is a claim about values that may since have moved. Measured
  # 2026-08-15 with a column edited from 0-121 down to 0-3 while a
  # low bound sat at 84.7 -- the ladder went on running to 121, four
  # of five classes wore nothing and every tile drew in the first,
  # which is the flat no-data look this plugin's other guards exist
  # to prevent. `pin_problem` is the same judge the typed bound faces,
  # asked again of the values as they now are; the DIALOG reports the
  # loss, since bridge draws maps and says nothing.
  # THAT LAST CLAUSE WAS FALSE UNTIL 2026-08-16, and a hunt found it:
  # no such site existed anywhere. The pin was dropped from the map
  # while the dialog's record, the swatch's pinned box and the layer's
  # stamp all went on asserting it, and a save and reopen read the
  # dead number straight back off the layer -- a pin shown as set over
  # a map that ignores it, while `pin_problem` refuses that very
  # number if it is typed. `dialog._retire_an_undrawable_pin` is the
  # site now, called from both notice paths. A comment describing what
  # a caller is supposed to do is not a caller.
  # ...but NOT under a copied ladder, which is deliberately allowed to
  # run past the receiving column: a copy reproduces a classification,
  # its unreachable classes are kept and hatched rather than dropped,
  # and a pin on such a ladder is a claim about the LADDER rather than
  # about this column's values. Judging it against the data would
  # refuse the high pin in
  # test_a_pin_still_works_on_a_copied_ladder, which is the settled
  # behaviour and not a defect.
  if (low_pin is not None or high_pin is not None) and finite_values \
      and not (pinned or {}).get("breaks"):
    if pin_problem(low_pin, high_pin, finite_values, k):
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
  # THE REDUCTION ABOVE ASKED ITS QUESTION TOO EARLY, and this asks it
  # again where the answer is decidable. Up there, k was compared with
  # the distinct values of the WHOLE column; a pin then takes a class
  # out of the ladder AND its samples out of the pool, so the scheme
  # is asked to cut k-pins classes from a strictly smaller set. That
  # is the same arithmetic the reduction exists to prevent, arriving
  # by a route it cannot see. Measured 2026-08-15 on the column
  # [1, 2, 3, 10, 20, 30, 100] with k=5 and pins at 3 and 30: the
  # middle holds {10, 20} and was asked for three classes, so the
  # ladder's third class, 13.3333 to 16.6667, was worn by no tile and
  # 20 painted a rung of the ramp too low. Four colours under a legend
  # of five, and nothing said so.
  #
  # The PINNED classes are not counted here. They are named rather
  # than cut, and a pinned class holding no samples is a deliberate
  # statement about where a reader's eye should start -- which is why
  # this counts the middle pool alone, on exactly the rule the subset
  # string below filters by, so the two cannot disagree.
  #
  # Unclassed is exempt for the reason the first reduction gives: its
  # fifty steps reproduce a continuous ramp rather than a class count
  # anybody chose.
  if pins and wants_middle and not unclassed:
    middle_values = [v for v in finite_values
                     if (low_pin is None or v > float(low_pin))
                     and (high_pin is None or v < float(high_pin))]
    middle_distinct = distinct_numeric_count(middle_values)
    if 0 < middle_distinct < int(k):
      k = middle_distinct
  # ---- A COPIED LADDER short-circuits the classifier entirely
  #
  # `pinned["breaks"]` holds every interior boundary of a ladder
  # copied from another element. There is nothing left for a scheme
  # to decide, so nothing is classified: the bounds are fitted to
  # this column's extremes (fitted_breaks) and set directly. That is
  # also why a copy needs no reduction -- "a column cannot be cut
  # into more classes than it has distinct values" governs breaks the
  # software COMPUTES, and never overrules one a user imported.
  copied = None
  if pinned and pinned.get("breaks") and finite_values:
    copied = fitted_breaks(pinned["breaks"], finite_values[0],
                           finite_values[-1])
  if copied is not None:
    # A PIN ON TOP OF A COPY moves that end's boundary, and until
    # 2026-08-15 it did nothing at all: this branch read
    # pinned["breaks"] and never looked at low or high, so the button
    # stayed down, the number was stamped into the project, and the
    # map did not move. Worse, it was LATENT -- releasing the copied
    # values later (a new class count) let the pin fire at a moment
    # the user had not connected it to. Found by a hunt pointed at
    # "which of two records wins", which is the right question: the
    # record holds two claims and each worked alone.
    #
    # The pin replaces the outermost boundary and its neighbour's
    # matching edge, so the ladder stays contiguous. A pin that would
    # cross the next copied boundary is refused by pin_problem before
    # it ever reaches here.
    if low_pin is not None and copied:
      copied[0] = (copied[0][0], float(low_pin))
      if len(copied) > 1:
        copied[1] = (float(low_pin), copied[1][1])
    if high_pin is not None and copied:
      copied[-1] = (float(high_pin), copied[-1][1])
      if len(copied) > 1:
        copied[-2] = (copied[-2][0], float(high_pin))
    set_class_bounds(renderer, copied, outline, method)
    pins = 1        # force the full recolour below, as a pin does
  FINITE = 1e307
  restore = None
  awkward = any(
    v is None or v == NULL or (isinstance(v, float)
                               and (v != v or abs(v) > FINITE))
    for v in values)
  if copied is None and index >= 0 and (awkward or pins):
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
    if copied is not None:
      raise _AlreadyClassified
    # `source` and not `layer`: the breaks come from the whole map's
    # values (see above), and the filtering just applied belongs to
    # whichever layer is about to be scanned. When no values were
    # handed over the two are the same object and this is the
    # behaviour that shipped before.
    renderer.updateClasses(source, k)
  except _AlreadyClassified:
    pass
  finally:
    if restore is not None:
      source.setSubsetString(restore)
  if pins and copied is None:
    _apply_pinned_bounds(renderer, low_pin, high_pin, finite_values[0],
                         finite_values[-1], outline, method,
                         wants_middle)
  _nudge_off_shared_bounds(renderer)
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
  # `count == 1` as well as `distinct == 1`, and the second half is
  # not redundant: a COPIED LADDER puts several classes on a column
  # holding one value, and this branch colours index 0 alone -- so
  # the other four kept the placeholder grey set_class_bounds builds
  # them with, and the element drew as flat #c0c0c0, which on a map
  # reads as no data. Measured 2026-08-15 on a column that is 7
  # everywhere carrying a four-break copied ladder: one Greens colour
  # and four greys. The pins-forced recolour below is what such a
  # ladder needs, and it was being shadowed by this branch winning
  # the if/elif. The one-class case itself is unchanged.
  if distinct == 1 and count == 1:
    # One class ranges over the whole window, and QGIS colours it
    # from the ramp's START (measured: near-white on Reds), which on
    # the map reads as "no data" rather than "one value". The
    # window's MIDDLE is the honest colour -- the plain ramp middle
    # when the window is the whole ramp. (User decision, 2026-08-09.)
    mid = quant_class_colours(ramp_name, reverse, 1, (lo, hi))
    if mid:
      renderer.updateRangeSymbol(0, _fill_symbol(mid[0], outline))
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
    for i, colour in enumerate(
        quant_class_colours(ramp_name, reverse, count, (lo, hi))):
      renderer.updateRangeSymbol(i, _fill_symbol(colour, outline))
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
                              classify_from: QgsVectorLayer | None = None,
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
    classify_from: a layer holding the WHOLE MAP's values for this
      column, or None to read the element's own tiles. It decides
      COLOURS only; the categories built below are still this
      element's own.

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
  def _sorted_values(source):
    """This column's distinct values, in the order colours follow.

    Args:
      source: a layer to ask, or an iterable of values already
        gathered. Callers hand over both: the run path passes the
        scratch layer `_classification_values` builds, and some
        callers pass the values themselves.

    Returns:
      The distinct non-null values, numbers before strings, which is
      the order the colours below follow.
    """
    if hasattr(source, "fields"):
      where = source.fields().indexOf(field)
      if where < 0:
        return []
      gathered = source.uniqueValues(where)
    else:
      gathered = source or []
    return sorted(
      {v for v in gathered if v is not None and v != NULL},
      key=lambda v: (isinstance(v, str), v))

  # ONE COLOUR MEANS ONE THING, and for a categorical column that is
  # decided by a value's POSITION in the whole map's list rather than
  # in this element's. Categorical colours follow ListedColormap
  # sampling -- code/(k-1) through int(x * N) -- so the NUMBER of
  # categories decides which colours are drawn, and one value an
  # element happens not to contain re-colours everything after it.
  # Measured 2026-08-15: four elements on one column and one tab10
  # ramp, three finding six values and the fourth five because no tile
  # of it caught a 'bare' area; #1f77b4 then meant 'bare' on three
  # elements and 'crops' on the fourth, and a reader matching a colour
  # against the legend read the wrong class.
  #
  # THE CATEGORY LIST STAYS THIS ELEMENT'S OWN. The defect is about
  # which colour a value gets, not about which values appear, so an
  # element carries only the categories it actually draws -- listing
  # 'bare' where no tile is 'bare' would tell a reader something false
  # about that element, which is the same species of lie.
  #
  # The graduated half of this rule was fixed on 2026-08-14 and this
  # half was not, because the rule had been written down as being
  # about class BREAKS. It is about MEANING (settled with the
  # maintainer, 2026-08-15, by /grill-me), and the wording in
  # CLAUDE.md now says so.
  values = _sorted_values(layer)
  everywhere = _sorted_values(classify_from) if classify_from is not None \
    else values
  if not everywhere:
    everywhere = values
  positions = {v: i for i, v in enumerate(everywhere)}
  ramp = get_ramp(ramp_name, reverse)
  preset = ramp.colors() if isinstance(ramp, QgsPresetSchemeColorRamp) \
    else None
  categories = []
  overrides = overrides or {}
  # ...and both the position and the count come from the map-wide
  # list, since ListedColormap sampling reads them together. A value
  # somehow absent from that list keeps its own position, which is the
  # pre-2026-08-15 behaviour and cannot be worse than refusing to
  # colour it.
  n = max(len(everywhere), 1)
  for own_index, v in enumerate(values):
    i = positions.get(v, own_index)
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


def _anything_to_classify(source, field) -> bool:
  """Whether a column holds a value a classifier could put a break in.

  Args:
    source: THE ELEMENT'S OWN LAYER, and deliberately not the shared
      classification source. The shared source is a geometry-less
      scratch layer built to cut breaks from the whole map, and
      asking it for this element's column answered False wherever it
      does not carry that name -- which greyed out elements that had
      perfectly good values, at up to 33,500 of 48,528 interior
      pixels against the library's map. Measured 2026-08-16, by four
      UI-against-library comparisons failing in a candidate build.

      The element layer is also the RIGHT question. By the time this
      is asked the missing rows have already been split off, so the
      layer holds exactly the rows a classifier could place: if any
      remain they have values, and if none remain there is genuinely
      nothing to classify.
    field: the column name.

  Returns:
    True when at least one usable numeric value is present. False
    when the column is absent, or holds nothing but nulls and values
    no break can separate. False is also the answer when the question
    cannot be asked, since drawing an element as no data is a milder
    wrong than drawing nothing at all.
  """
  try:
    index = source.fields().indexOf(field)
    if index < 0:
      return False
    return distinct_numeric_count(source.uniqueValues(index)) > 0
  except Exception:
    return False


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
      assignment.get("category_colours"), classify_from))
  elif assignment["mode"] == "Single colour":
    colour = assignment.get("single_colour") or \
      ramp_swatch_colour(assignment["ramp"])
    layer.setRenderer(make_single_renderer(colour, outline))
  elif not _anything_to_classify(layer, var):
    # NOTHING TO CLASSIFY, so the element draws as NO DATA rather
    # than not at all. The maintainer's decision, 2026-08-16.
    #
    # What happened before: QGIS builds a graduated renderer with
    # ZERO ranges over a column with no usable values, so
    # `symbolForFeature` answers None for every tile and the element
    # is simply absent from the map. Measured by a stochastic hunt at
    # 0.000 of the layer painted against 0.255 for its neighbours,
    # while the row still showed a swatch, a ramp name and a class
    # count of five, and the message bar said those areas "draw as no
    # data". Three statements to the user and none of them true. A
    # user reaches it by mapping a column that turned out empty, a
    # join that matched nothing, and on a design of several elements
    # the others draw normally so the map looks deliberate.
    #
    # THE DECISION IS TAKEN HERE AND NOT INSIDE THE CLASSIFIER,
    # deliberately. `make_graduated_renderer` promises a
    # QgsGraduatedSymbolRenderer, and callers read its ranges;
    # returning a different class from it crashed the dialog on the
    # very column this is about. "This cannot be classified at all"
    # is a decision ABOUT classifying, so it belongs above it.
    layer.setRenderer(make_single_renderer(NO_DATA_FILL, outline))
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


def split_out_the_no_data(frame, field, column_has_values=None):
  """Separate the rows a graduated renderer cannot draw.

  Args:
    frame: one element's tiles, as a GeoDataFrame.
    field: the column that element is coloured by, or None when it
      carries no variable at all.
    column_has_values: whether the column has any usable value
      ANYWHERE ON THE MAP, which this frame cannot know: it holds one
      element's tiles. True means the classifier has real breaks to
      draw with, so an element whose own tiles are all missing must
      still be split, or it draws nothing at all. None (the default)
      keeps the older behaviour for callers that cannot say.

  Returns:
    A pair ``(drawable, absent)`` of frames: the rows whose value the
    classifier can place, and the rows whose value is missing. When
    the field is None, absent from the frame, nothing is missing, or
    EVERYTHING is missing, `absent` is None and `drawable` is the
    frame unchanged -- so an ordinary map pays nothing for this, and
    an element with no values at all keeps all its tiles (see the
    all-missing branch below for why that case is left alone).

  WHY THE SPLIT EXISTS. QgsGraduatedSymbolRenderer has no class for a
  missing value: `symbolForFeature` answers None and the tile is
  simply not drawn, so the layer beneath shows through as a hole.
  Verified against the renderer's whole public API on QGIS 4.0.3 --
  there is no default, no-data, else or fallback symbol of any kind,
  where the CATEGORIZED renderer has `addCategory` and therefore its
  familiar "(no data)" catch-all.

  Reported from the field on 2026-08-16 with an area that is null in
  every variable, so it read as a hole under two different tilings and
  whichever column was mapped. The fix chosen by the maintainer keeps
  every renderer standard: the missing rows become their own layer,
  categorically rendered, grouped beside the graduated one, and the
  plugin's own table goes on showing ONE element with No data as one
  more class in its colour editor.
  """
  if field is None or frame is None or field not in getattr(
      frame, "columns", []):
    return frame, None
  import numpy as np
  import pandas as pd

  # WHAT THE CLASSIFIER CANNOT PLACE, which is wider than "missing".
  # `isna()` alone is False for an infinity, so ±inf was neither
  # classed (the breaks exclude non-finite values) nor split onto the
  # paired layer, and those areas were drawn as NOTHING -- a hole,
  # which is the very thing this split exists to abolish. Measured
  # 2026-08-16: sixteen tiles per element where symbolForFeature
  # returned None, 0.000 of the area painted against 0.26 for a
  # control. A GeoPackage really does carry an infinity: SQLite
  # stores it as REAL and OGR hands it straight back.
  #
  # A NaN needs no special case and deliberately gets none. `isna()`
  # already covers it, which collapses it into No data -- the
  # maintainer's ruling, because a GeoPackage stores a written NaN as
  # NULL, so a category of its own would be empty for anyone whose
  # data came from a file.
  values = frame[field]
  missing = values.isna()
  # to_numeric coerces a text column to NaN, so `infinite` is empty
  # there rather than raising: a text field has no infinities and
  # asking is not an error.
  numeric = pd.to_numeric(values, errors="coerce")
  infinite = numeric.notna() & ~np.isfinite(numeric)
  missing = missing | infinite
  if not bool(missing.any()):
    return frame, None
  if bool(missing.all()) and not column_has_values:
    # EVERY row is missing, and splitting here would be both
    # redundant and harmful. Redundant because there is nothing to
    # put on a second layer that is not already on the first.
    #
    # WHAT THIS COMMENT USED TO CLAIM WAS FALSE, and the correction
    # matters more than the branch. It said such an element "already
    # draws in NO_DATA_FILL through the single-symbol path below" --
    # but that path is reached only by an element carrying NO
    # variable, which an element with an empty column never is. A
    # stochastic hunt measured what actually happens on 2026-08-16:
    # QGIS builds a graduated renderer with ZERO ranges, every tile
    # gets no symbol, and the element is absent from the map at 0.000
    # painted against 0.255 for its neighbours, while its row shows a
    # swatch, a ramp name and a class count, and the message bar says
    # the areas "draw as no data". Three statements to the user, all
    # of them wrong.
    #
    # THE ELEMENT-LEVEL CASE IS DIFFERENT AND IS SPLIT. This function
    # is called per element, so `missing.all()` is a fact about THAT
    # ELEMENT'S TILES and not about the column: a design can easily
    # put one element entirely on areas that happen to have no value
    # while the column has plenty elsewhere. Declining the split
    # there left the element wearing breaks cut from the whole map
    # and matching none of them, so it was absent from the map while
    # its siblings drew normally, its row showed a swatch and a class
    # count, and the bar said those areas draw as no data. Measured
    # 2026-08-16 by a stochastic hunt: six tiles, six unpainted, no
    # paired layer, against siblings drawing correctly.
    # `column_has_values` is what tells the two cases apart.
    #
    # The COLUMN-level case needs no split, and now genuinely draws:
    # `make_graduated_renderer` returns a single no-data symbol when
    # the column has no usable values, so the whole element says "no
    # data" without a second layer. That was the claim this comment
    # made before it was true; the maintainer settled it on
    # 2026-08-16 and the code was changed to match. It replaced
    # settled behaviour
    # guarded by test_a_column_with_no_values_at_all_invents_no_class,
    # whose docstring says the element "is entitled to paint
    # nothing", and changing what an empty column draws is the
    # maintainer's decision rather than a defect to fix in passing.
    # Raised 2026-08-16; the choice is between drawing the element in
    # the no-data colour, which is what the message already promises,
    # and keeping the present silence. Harmful because the split would leave
    # the graduated layer EMPTY beside a full paired one, so the
    # element a user selects, filters and reads a feature count from
    # would carry no tiles at all.
    # Measured 2026-08-16 by test_a_column_with_no_values_at_all_
    # invents_no_class, which is where the regression surfaced: the
    # element reported 0 tiles.
    #
    # The rule this settles: the split rescues tiles that would be
    # HOLES AMONG DRAWN ONES. Where nothing is drawn, there is no
    # hole to read, and the existing path already says the right
    # thing.
    return frame, None
  # The paired layer carries WHICH KIND each row is, in a column the
  # plugin owns, so its renderer can categorize on one fixed name
  # without knowing which variable produced the layer. Computed from
  # the values rather than carried down from the region, because by
  # here they are exactly as informative: a NULL and a NaN are both
  # `isna()` and are meant to collapse, and an infinity is still an
  # infinity.
  gone = frame[missing].copy()
  kind = []
  for value in pd.to_numeric(gone[field], errors="coerce"):
    if pd.isna(value):
      kind.append(ABSENCE_VALUE[NO_DATA_KEY])
    elif value > 0:
      kind.append(ABSENCE_VALUE[POS_INF_KEY])
    else:
      kind.append(ABSENCE_VALUE[NEG_INF_KEY])
  gone[ABSENCE_FIELD] = kind
  return frame[~missing], gone


def make_no_data_renderer(colour, outline: bool, kinds=None):
  """The renderer for an element's missing-value layer.

  Args:
    colour: the fill those areas draw in. Either a "#rrggbb" string,
      which colours every kind alike and is what a caller with no
      per-kind picks passes, or a dict keyed by the ABSENCE_KINDS keys
      (NO_DATA_KEY, NEG_INF_KEY, POS_INF_KEY) holding a colour each.
      Missing entries fall back to that kind's default fill.
    outline: whether tile boundaries are drawn, exactly as elsewhere.
    kinds: which absence values this element's tiles actually hold, as
      the strings stored in ABSENCE_FIELD -- normally read off the
      paired layer. None means "only no-value", which is what a caller
      that has not looked should assume and is the shape every layer
      written before ABSENCE_FIELD existed has.

  Returns:
    A QgsCategorizedSymbolRenderer with ONE CATEGORY PER KIND PRESENT,
    labelled from ABSENCE_KINDS, in that tuple's order so the legend
    reads no data, negative infinity, infinity whatever order
    the tiles arrived in.

  ONLY THE KINDS PRESENT, for the reason the categorical path already
  gives: listing a category no tile of this element wears tells a
  reader something false about the element. An element whose gaps are
  all NULLs gets one entry, exactly as before this existed.

  BACKWARD COMPATIBLE ON PURPOSE. A layer written before
  ABSENCE_FIELD, or reopened from an older GeoPackage, has no such
  column; passing kinds=None gives it the single catch-all it has
  always had, categorized on "" so the value never matches and every
  feature falls to it.

  CATEGORIZED RATHER THAN SINGLE-SYMBOL, deliberately. A single symbol
  would paint the same pixels, and would put a bare layer name in the
  legend where this puts the words "no data" -- which is the whole
  point of drawing these areas rather than leaving them blank. It also
  matches what the categorical path already does for its own
  catch-all, so a reader meets one idea rather than two.
  """
  from qgis.core import QgsCategorizedSymbolRenderer, QgsRendererCategory
  # BUILT INLINE, and that is not a style preference. Holding the
  # category in a Python name and passing it to the renderer leaves
  # two owners of one symbol: the renderer takes it, Python frees it,
  # and the category comes back wearing a default BLACK fill.
  # Measured 2026-08-16 -- #dddddd through _fill_symbol, #dddddd
  # inside the category, #000000 once the renderer was constructed.
  # make_categorized_renderer above has always built its own
  # categories inline for the same reason.
  picks = colour if isinstance(colour, dict) else {}
  plain = colour if isinstance(colour, str) else None
  present = set(kinds or ())
  if not present:
    # nothing said, or a layer from before the column existed: the
    # single catch-all this has always produced. Categorized on "" so
    # no value ever matches and every feature falls to the category.
    return QgsCategorizedSymbolRenderer("", [
      QgsRendererCategory(
        None, _fill_symbol(plain or NO_DATA_FILL, outline), "no data")])
  categories = []
  for key, stored, label, fill in ABSENCE_KINDS:
    if stored not in present:
      continue
    # Each symbol BUILT INLINE, and that is not a style preference.
    # Holding one in a Python name and passing it to the category
    # leaves two owners: the renderer takes it, Python frees it, and
    # the category comes back wearing a default BLACK fill. Measured
    # 2026-08-16 -- #dddddd through _fill_symbol, #dddddd inside the
    # category, #000000 once the renderer was constructed.
    categories.append(QgsRendererCategory(
      stored, _fill_symbol(picks.get(key) or plain or fill, outline),
      label))
  return QgsCategorizedSymbolRenderer(ABSENCE_FIELD, categories)


def gpkg_tables_we_would_replace(path: str, layer_names) -> list:
  """Which of these tables the file ALREADY holds.

  Args:
    path: the .gpkg a run is about to write into. A path that does not
      exist yet is not an overwrite, and answers empty.
    layer_names: the table names this run intends to write, which for
      an element layer is what `write_gpkg_layer` would be given.

  Returns:
    The subset of `layer_names` already present in the file, in the
    order given, or an empty list when the file is absent, unreadable,
    or GDAL is not available. Never raises: this is asked in order to
    WARN somebody, and a check that explodes is worse than one that
    declines.

  WHY IT ASKS THE FILE. The dialog used to answer this from
  `_last_path`, a record of what THIS dialog instance last wrote --
  so a reopened project, whose dialog remembers nothing, would tick
  "create as new group" to keep yesterday's map and overwrite it
  without a word. Measured 2026-08-16: 41/40/41/40 features became
  113/112/113/112, no warning. A file outlives a session, so the
  question has to be put to the file.
  """
  if not path or not os.path.exists(path):
    return []
  try:
    from osgeo import ogr
  except ImportError:
    return []
  source = None
  try:
    source = ogr.Open(path, 0)          # 0 = read only; we only look
    if source is None:
      return []
    present = {source.GetLayer(i).GetName()
               for i in range(source.GetLayerCount())}
    return [name for name in layer_names if name in present]
  except Exception:
    return []
  finally:
    source = None


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
