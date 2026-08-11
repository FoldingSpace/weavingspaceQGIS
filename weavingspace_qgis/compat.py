"""Every QGIS-version-sensitive API call in one place.

WHY THIS FILE EXISTS
--------------------
QGIS moves: the 3-to-4 transition changed the Qt toolkit, scoped the
enums, and reworked constructors, and a future 4-to-5 transition will
break things again. The plugin's rule is:

    All version-dependent QGIS/Qt API access goes through this module.
    Nothing else in the plugin is allowed a try/except on a QGIS API.

The plugin targets QGIS 4+ (PyQt6, Python 3.12+), so each helper is
currently a one-liner in the QGIS 4 spelling; the module earns its keep
as the place where the *next* breakage gets absorbed. When a future
QGIS release breaks something, run ``tests/run_tests.py`` (see
MAINTAINING.md) to find out which helper, add a fallback branch there,
and note the QGIS version in its docstring.

Each helper here answers one question whose ANSWER changed (or may
change) between QGIS versions, and returns the thing the caller
wants rather than a version number: a constructed object, an enum
member, a boolean. Callers therefore never branch on versions
themselves, and a future break is a one-line fix in this file with
the old branch kept and its QGIS version noted.
"""

from __future__ import annotations

from qgis.core import QgsField, QgsMapLayerProxyModel, QgsTask, QgsVectorFileWriter


def make_field(name: str, python_type) -> QgsField:
  """QgsField (one column of a layer's schema) for a python type.

  Args:
    name: the attribute name to create.
    python_type: ``float``, ``int`` or ``str``.

  Returns:
    A QgsField of the matching QGIS type.

  QGIS 4 constructs fields from QMetaType.Type (Qt's runtime type ids);
  the old QVariant-based constructor was removed with QGIS 3, which is
  why this lives in compat.
  """
  from qgis.PyQt.QtCore import QMetaType
  kind = {float: QMetaType.Type.Double, int: QMetaType.Type.LongLong,
          str: QMetaType.Type.QString}[python_type]
  return QgsField(name, kind)


def polygon_layer_filter():
  """Filter value for QgsMapLayerComboBox.setFilters (scoped enum)."""
  return QgsMapLayerProxyModel.Filter.PolygonLayer


def task_can_cancel():
  """QgsTask construction flag allowing user cancellation."""
  return QgsTask.Flag.CanCancel


def task_active_statuses():
  """QgsTask statuses that mean "still going" (queued/held/running);
  used by the dialog's zombie-task recovery on reopen."""
  return (QgsTask.TaskStatus.Queued, QgsTask.TaskStatus.OnHold,
          QgsTask.TaskStatus.Running)


def set_save_file_mode(file_widget) -> None:
  """Put a QgsFileWidget into save-a-file mode (scoped enum)."""
  from qgis.gui import QgsFileWidget
  file_widget.setStorageMode(QgsFileWidget.StorageMode.SaveFile)


def writer_overwrite_file():
  """QgsVectorFileWriter action: create/overwrite the whole file."""
  return QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile


def writer_overwrite_layer():
  """QgsVectorFileWriter action: replace one layer inside the file."""
  return QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer


def writer_no_error():
  """QgsVectorFileWriter success code."""
  return QgsVectorFileWriter.WriterError.NoError


def classification_method(scheme: str):
  """Instantiate a QGIS classification method by user-facing scheme name.

  Returns None if this QGIS build lacks the class (callers then fall
  back to QGIS's default classification). The Qgs* class names have
  been stable for years; if a future QGIS renames them, update the map.
  """
  import qgis.core as qc
  names = {
    "Quantiles": "QgsClassificationQuantile",
    "Equal intervals": "QgsClassificationEqualInterval",
    "Natural breaks (Jenks)": "QgsClassificationJenks",
    "Pretty breaks": "QgsClassificationPrettyBreaks",
  }
  cls = getattr(qc, names.get(scheme, "QgsClassificationQuantile"), None)
  return cls() if cls is not None else None


def layer_data_is_available(layer) -> bool:
  """Whether a layer's data source can still be safely questioned.

  Args:
    layer: any map layer, or None.

  Returns:
    True when the layer exists and its provider still has data behind
    it. False for a layer whose file has been deleted, whose database
    connection has dropped, or whose source has otherwise gone --
    including the case where the layer itself still claims to be
    valid.

  Ask this BEFORE reading a layer's extent, and the reason is not
  tidiness. A GeoPackage layer whose file is deleted and then reloaded
  answers isValid() with True, featureCount() with -2, and extent()
  by segfaulting the whole application: no exception, no traceback,
  no message in the log, QGIS simply gone. The provider's own
  isValid() is the honest answer and the only one that helps.

  It lives in compat because it reaches through to the data provider,
  and the relationship between a layer's validity and its provider's
  is exactly the sort of thing a QGIS release adjusts.
  """
  if layer is None:
    return False
  try:
    if not layer.isValid():
      return False
    provider = layer.dataProvider()
    return provider is not None and provider.isValid()
  except RuntimeError:
    # the C++ object has been deleted out from under the wrapper,
    # which is its own kind of unavailable
    return False


def layer_auto_refreshes(layer) -> bool:
  """Whether a layer refreshes itself on a timer.

  Args:
    layer: any map layer.

  Returns:
    True when QGIS is set to reload this layer periodically. Switching
    that on is a user saying "this data moves", which is the one case
    where the plugin follows a layer's repaint signal — normally it
    must not, because repaints also fire on style changes and
    re-tiling on those is precisely the cost the restyle fast path
    exists to avoid.

  This lives in compat because the spelling is exactly the sort of
  thing a QGIS release moves: QGIS 4 asks ``autoRefreshMode()``, which
  returns a Qgis.AutoRefreshMode whose Disabled member means off. The
  QGIS 3 spelling is deliberately NOT carried. This plugin targets
  QGIS 4+, so a branch for 3 could never run, and compat exists to
  absorb the NEXT break rather than to remember the last one.

  Anything this build cannot answer comes back False, which is the
  safe direction and not merely the cautious one: a wrong False costs
  one missed refresh on a layer the user set to reload itself, while a
  wrong True re-tiles the whole map on every repaint — style changes
  included, which is the entire cost the restyle fast path exists to
  avoid.
  """
  mode = getattr(layer, "autoRefreshMode", None)
  if mode is None:
    return False
  try:
    from qgis.core import Qgis
    return mode() != Qgis.AutoRefreshMode.Disabled
  except Exception:
    return False


def map_unit_label(layer) -> str:
  """The abbreviation for a layer's distance units, e.g. "m".

  Args:
    layer: the region layer whose CRS decides what "spacing" counts
      in. Read on the main thread; this touches the layer.

  Returns:
    QGIS's own abbreviation for that CRS's distance unit ("m", "ft",
    "\u00b0"), or "map units" when it has none, which is the phrase the
    dialog's own spacing label uses so an unknown unit still reads as
    a sentence.

  This lives here rather than beside its caller because the enum it
  reads is exactly the kind of thing QGIS moves: 3.30 relocated the
  distance units to Qgis.DistanceUnit, and a future release may do it
  again. When it breaks, this is the one line to fix.
  """
  from qgis.core import QgsUnitTypes
  # A geographic layer is REPROJECTED to Web Mercator before anything
  # is tiled (see bridge.layer_to_gdf), so the spacing the user sets
  # and the coverage notice reports are metres, whatever the layer's
  # own units say. Reading the layer's CRS here produced "At 2,000 deg
  # spacing ..." for a number that was metres -- a label contradicting
  # the quantity beside it.
  if layer.crs().isGeographic():
    return "m"
  return QgsUnitTypes.toAbbreviatedString(layer.crs().mapUnits()) \
      or "map units"



def save_style_to_database(layer, name: str, description: str) -> None:
  """Save a layer's style into its own GeoPackage, on whichever API exists.

  Args:
    layer: the file-backed output layer whose current symbology is to
      travel inside the .gpkg, so that opening the file elsewhere
      shows the map already symbolized.
    name: the style's name in the file's layer_styles table. Trimmed
      by the caller to the thirty characters GDAL gives that column.
    description: the free-text description stored beside it.

  Returns:
    None. Failures are swallowed by the caller, deliberately: a style
    that will not save must never fail a run that produced a map.

  WHY THIS IS HERE. ``saveStyleToDatabase`` is DEPRECATED as of QGIS
  4.0.3 in favour of ``saveStyleToDatabaseV2``, which differs in what
  it returns rather than in what it is asked. A deprecated call is
  precisely the kind of thing a later QGIS changes or withdraws, and
  this project's rule is that every version-sensitive QGIS call lives
  in this module -- so when it goes, this is the one line to fix
  rather than a hunt through bridge.py.

  It is written the useAsDefault way round on purpose: QGIS matches a
  default style by TABLE rather than by style name, which is why the
  name can be trimmed without anything losing track of it.
  """
  saver = getattr(layer, "saveStyleToDatabaseV2", None)
  if saver is None:
    # older QGIS: the deprecated spelling is all there is
    saver = layer.saveStyleToDatabase
  saver(name, description, True, "")
