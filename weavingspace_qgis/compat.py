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

