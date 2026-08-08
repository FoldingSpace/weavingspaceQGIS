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
  ramp = QgsStyle.defaultStyle().colorRamp(name)
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


def estimate_tile_count_bounds(unit, b) -> int:
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

  Returns:
    An estimated tile count; MAX_TILES_HARD + 1 when the vectors are
    degenerate (a unit that does not tile the plane), so a broken
    design is refused rather than attempted.
  """
  tb = unit.tiles.total_bounds
  tile_diag = math.hypot(tb[2] - tb[0], tb[3] - tb[1])
  w = (b[2] - b[0]) + 2 * tile_diag
  h = (b[3] - b[1]) + 2 * tile_diag
  radius = math.hypot(w, h) / 2
  v = unit.get_vectors()
  det = abs(v[0][0] * v[1][1] - v[0][1] * v[1][0])
  if det <= 0:
    return MAX_TILES_HARD + 1
  n_prototiles = math.pi * radius * radius / det
  return int(n_prototiles * max(len(unit.tiles), 1))


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
  return spacing * math.sqrt(est / MAX_TILES_HARD)


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


def make_graduated_renderer(layer: QgsVectorLayer, field: str,
                            ramp_name: str, scheme: str, k: int,
                            outline: bool,
                            reverse: bool = False
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
  renderer = QgsGraduatedSymbolRenderer(field)
  renderer.setSourceSymbol(_fill_symbol("#c0c0c0", outline))
  renderer.setSourceColorRamp(get_ramp(ramp_name, reverse))
  method = compat.classification_method(scheme)
  if method is not None:
    renderer.setClassificationMethod(method)
  renderer.updateClasses(layer, k)
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
    raise ValueError("that layer has no categorized symbology")
  mapping = {}
  for cat in renderer.categories():
    if cat.value() is None or cat.value() == "":
      continue
    mapping[str(cat.value())] = (cat.symbol().clone(), cat.label())
  if not mapping:
    raise ValueError("that layer's symbology defines no classes")
  return mapping


def make_categorized_renderer(layer: QgsVectorLayer, field: str,
                              ramp_name: str, outline: bool,
                              template: dict | None = None,
                              reverse: bool = False,
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
  n = max(len(values), 1)
  for i, v in enumerate(values):
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
  categories.append(QgsRendererCategory(
    None, _fill_symbol(NO_DATA_FILL, outline), "no data"))
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
      (including "Unclassed"), ``k``, ``outline``, and
      ``single_colour`` for Single colour rows.
    template: a class scheme from load_categorized_template or
      template_from_layer. Applied only to categorized elements;
      ignored otherwise.

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
      assignment.get("reverse", False)))
  elif assignment["mode"] == "Single colour":
    colour = assignment.get("single_colour") or \
      ramp_swatch_colour(assignment["ramp"])
    layer.setRenderer(make_single_renderer(colour, outline))
  else:
    layer.setRenderer(make_graduated_renderer(
      layer, var, assignment["ramp"], assignment.get("scheme", "Quantiles"),
      assignment.get("k", 5), outline, assignment.get("reverse", False)))
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
  options.layerOptions = ["FID=weavingspace_fid"]
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
  """
  try:
    layer.saveStyleToDatabase(layer.name(), "seeded by WeavingSpace",
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
