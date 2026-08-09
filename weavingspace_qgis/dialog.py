"""Main dialog of the WeavingSpace plugin.

Design controls mirror the mapweaver web app; output is one QGIS layer
per tile element, gathered in a layer-tree group, each given a standard
QGIS renderer so refinement happens in QGIS's normal styling tools.
Regenerating replaces the previous group's layers in place (styling
survives unless an element's assignment changed).

A QGIS/Qt PRIMER for weavingspace maintainers
---------------------------------------------
If you know the weavingspace library but not QGIS, these are the ideas
this file leans on; everything else is ordinary Python.

* Qt widgets and signals. The dialog is built from Qt widgets
  (QComboBox, QSpinBox, ...). A widget announces changes by emitting a
  *signal*; ``widget.someSignal.connect(fn)`` registers ``fn`` to run
  when it fires. Two recurring subtleties: setting a widget's value in
  code fires the same signal a user interaction would, so programmatic
  updates are wrapped in ``blockSignals(True)/(False)`` to avoid
  feedback loops; and ``activated`` fires only on real user picks while
  ``currentIndexChanged`` fires for programmatic changes too, which is
  how we tell "user touched this" from "we set it".

* Debouncing with QTimer. A single-shot QTimer runs its ``timeout``
  slot once, ``interval`` ms after the most recent ``start()``; calling
  ``start()`` again restarts the countdown. We funnel every control
  change through two such timers so that dragging a spinner rebuilds
  the preview (350 ms) and regenerates the map (900 ms) once per pause,
  not once per tick.

* Threading via QgsTask (see worker.py). Qt GUIs are single-threaded:
  only the main thread may touch widgets, and long work on the main
  thread freezes QGIS. QgsApplication.taskManager() runs a QgsTask's
  ``run()`` on a worker thread and its ``finished()`` back on the main
  thread. THE ONE HARD RULE (see MAINTAINING.md): the worker must never
  touch pyproj/PROJ, because QGIS uses the same PROJ library on the
  main thread and concurrent use segfaults; ``_generate`` therefore
  strips CRS off every GeoDataFrame before handing it to the task and
  ``done`` reattaches it afterwards.

* The project and its layer tree. QgsProject.instance() is the open
  project: a registry of layers (``addMapLayer``/``removeMapLayer``,
  each layer keyed by a stable string ``id()``) plus a *layer tree*
  (``layerTreeRoot()``) that is the panel the user sees, where layers
  can be gathered into named groups. We add layers with
  ``addMapLayer(layer, False)`` (False = don't auto-place in the tree)
  and then attach them to our own group node explicitly.

* Table cell widgets. QTableWidget lets a real widget live in a cell
  (``setCellWidget``); we use that for the per-element combos, spinner,
  and colour button. Two Qt traps found the hard way: a widget placed
  into a *hidden* column can paint at the table's origin until a layout
  pass (so visibility is set explicitly after placing), and "blank"
  cells are made by *removing* the widget, not hiding it, because some
  render paths paint hidden cell widgets anyway.

Targets QGIS 4+ (PyQt6, Python 3.12+); imports go through the
``qgis.PyQt`` layer and the few version-sensitive APIs through
compat.py, so a future QGIS transition lands in one file.
"""

from __future__ import annotations

import json
import math
import os
import traceback

from qgis.PyQt.QtCore import QSize, Qt, QTimer
from qgis.PyQt.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from qgis.PyQt.QtWidgets import (
  QAbstractButton,
  QApplication,
  QCheckBox,
  QComboBox,
  QDialog,
  QDoubleSpinBox,
  QFormLayout,
  QGroupBox,
  QHBoxLayout,
  QLabel,
  QLineEdit,
  QMessageBox,
  QProgressBar,
  QPushButton,
  QSpinBox,
  QTableWidget,
  QTableWidgetItem,
  QTabWidget,
  QVBoxLayout,
  QWidget,
)
from qgis.core import (
  QgsApplication,
  QgsMapLayerProxyModel,
  QgsProject,
)
from qgis.gui import QgsColorButton, QgsFileWidget, QgsMapLayerComboBox

from . import bridge, catalog, perception
from .category_editor import CategoryColourDialog
from .worker import TilingTask

GROUP_BASE_NAME = "WeavingSpace tiles"


def _plugin_version() -> str:
  """The installed version, read from metadata.txt (one source of truth)."""
  try:
    meta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "metadata.txt")
    with open(meta, encoding="utf-8") as f:
      for line in f:
        if line.startswith("version="):
          return line.split("=", 1)[1].strip()
  except Exception:
    pass
  return "unknown"


def compat_layer_available(dialog, layer) -> bool:
  """compat.layer_data_is_available, imported at the point of use.

  Args:
    dialog: unused; present so the live gate can call this as one
      short line beside its other guards.
    layer: the layer to test.

  Returns:
    Whatever compat.layer_data_is_available says.

  This exists only to keep the import out of a guard clause in the
  middle of the live-render gate, which is already a long list of
  conditions and reads better without an import wedged into it.
  """
  from . import compat
  return compat.layer_data_is_available(layer)


def _polygon_filter():
  """Filter value so the region combo lists only polygon layers."""
  from . import compat
  return compat.polygon_layer_filter()


def _nice_number(x: float) -> float:
  """Round x up to a 'clean' value (1/2/2.5/5 times a power of ten),
  used so the derived default spacing reads as a sensible number."""
  # A layer with no CRS set can report an infinite extent, and
  # math.floor(math.log10(inf)) raises OverflowError rather than
  # returning anything. That reached a user as an unhandled exception
  # from pressing Generate, with nothing said about the layer.
  if not math.isfinite(x) or x <= 0:
    return 1.0
  exp = math.floor(math.log10(x))
  mant = x / 10 ** exp
  for m in (1, 2, 2.5, 5, 10):
    if mant <= m:
      return m * 10 ** exp
  return 10 ** (exp + 1)


# How large a ramp swatch is drawn in the Colour ramp dropdown. This
# has to be applied in TWO places to have any effect: the pixmap is
# drawn at this size, and each combo is told to display icons at this
# size. A QComboBox left alone uses the platform style's icon size,
# which on a desktop theme is around 16 pixels, so a swatch drawn
# larger than that was simply scaled back down and the ramp was almost
# unreadable -- which is what it looked like, and why enlarging the
# pixmap on its own would have changed nothing.
RAMP_SWATCH = QSize(64, 18)

# What separates two notices sharing the dialog's single note line
# when there is no QGIS message bar to stack them in. See
# WeavingSpaceDialog._report_quietly.
NOTE_SEPARATOR = "  |  "

# The "Edit colours" column. Appended after the columns that were
# already there and moved into place visually, so no existing column
# number changes. See _build_ui, where the move happens.
COL_EDIT_COLOURS = 8


def _ramp_icon(name: str, reverse: bool = False):
  """Small preview swatch (a QIcon) for a named colour ramp.

  Args:
    name: a ramp in QgsStyle.
    reverse: draw it running the other way, so the swatch shows the
      direction the map will actually use.

  Returns:
    A QIcon, or None when the ramp or the API is unavailable.

  QgsStyle.defaultStyle() is the user's style library (a sqlite DB of
  named symbols and colour ramps shared across all of QGIS); ramps are
  looked up in it by name.
  """
  try:
    from qgis.core import QgsSymbolLayerUtils
    # bridge.get_ramp clones and, when asked, reverses; the swatch
    # therefore shows the direction the map will actually use
    ramp = bridge.get_ramp(name, reverse)
    if ramp is not None:
      return QgsSymbolLayerUtils.colorRampPreviewIcon(ramp, RAMP_SWATCH)
  except Exception:
    pass
  return None


# The one live dialog in this QGIS session, if any. The plugin reuses
# a single dialog, but nothing stopped a second one existing: reloading
# the plugin (routine while developing, and QGIS's Plugin Reloader does
# it constantly) leaves the previous instance alive with its timers
# running and possibly a tiling in flight. Since a new dialog adopts
# the existing output group, two instances would write to the same
# layers, each unaware of the other. One at a time, enforced.
_LIVE_DIALOG = None


class ToggleSwitch(QAbstractButton):
  """A small sliding on/off switch: a knob that moves left to right.

  Qt has no switch widget, and the usual workaround -- a QCheckBox
  with a stylesheet -- renders differently on every platform and
  theme, which is precisely what a table full of them would show up.
  Painting it directly is a few lines and looks the same everywhere.

  It is an ordinary QAbstractButton, so everything a checkbox offers
  still works: setChecked/isChecked, the toggled signal, space to
  operate it from the keyboard, and the disabled state.

  Args:
    parent: the owning widget, as usual in Qt.
  """

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setCheckable(True)
    self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    self.setFixedSize(34, 18)
    self.setCursor(Qt.CursorShape.PointingHandCursor)

  def sizeHint(self):  # noqa: N802 (Qt API)
    """The size Qt should give this switch when it can choose.

    Returns:
      A QSize wide enough for the knob to travel visibly, and short
      enough to sit in a table row without stretching it.
    """
    return QSize(34, 18)

  def paintEvent(self, _event):  # noqa: N802 (Qt API)
    """Draw the track, then the knob at whichever end applies.

    Colours come from the widget's palette rather than being
    hard-coded, so the switch follows a light or dark QGIS theme
    without knowing anything about it.
    """
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    palette = self.palette()
    on = self.isChecked()
    enabled = self.isEnabled()
    track = palette.color(palette.ColorRole.Highlight) if on \
      else palette.color(palette.ColorRole.Mid)
    if not enabled:
      track.setAlpha(70)
    radius = self.height() / 2
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(track))
    painter.drawRoundedRect(0, 0, self.width(), self.height(),
                            radius, radius)
    knob = palette.color(palette.ColorRole.Base)
    if not enabled:
      knob.setAlpha(150)
    painter.setBrush(QBrush(knob))
    inset = 2
    diameter = self.height() - 2 * inset
    x = (self.width() - diameter - inset) if on else inset
    painter.drawEllipse(int(x), inset, diameter, diameter)
    if self.hasFocus():
      painter.setPen(QPen(palette.color(palette.ColorRole.Highlight), 1))
      painter.setBrush(Qt.BrushStyle.NoBrush)
      painter.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1,
                              radius, radius)
    painter.end()


class TilePreview(QWidget):
  """Live preview of the tile unit, painted directly with Qt.

  This deliberately does not use matplotlib (absent from some QGIS
  installs) nor a QGIS map canvas (heavyweight): shapely polygon
  coordinates from the weavingspace unit are transformed to widget
  pixels and painted with QPainter, Qt's low-level drawing API. A
  QWidget subclass repaints by overriding ``paintEvent``; calling
  ``self.update()`` schedules such a repaint.
  """

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setMinimumSize(280, 280)
    self._polys = []
    self._ids = []
    self._id_colours = {}
    # (tile_id, x, y, w, h) per central-unit tile: label anchor at the
    # tile's representative point plus its bounds, so labels can be
    # skipped on tiles that draw too small to carry one
    self._labels = []
    self._message = "Pick a design to preview it."

  def show_unit(self, unit, id_colours: dict, shells: int = 0):
    """Show a tile unit, optionally with rings of neighbours.

    Args:
      unit: the Tileable to draw.
      id_colours: {tile_id: colour} for the elements, carrying alpha
        so an element's opacity shows.
      shells: 0 draws the unit alone; 1 or more adds that many rings
        of translated copies around it. The dialog defaults to 1,
        because insetting and the way tiles meet across a join are
        invisible in a unit shown by itself.

    Returns:
      None; the widget repaints itself.
    """
    try:
      if shells <= 0:
        patch = unit.tiles
      else:
        patch = unit.get_local_patch(r=shells, include_0=True)
      polys = []
      for tid, shp in zip(patch.tile_id, patch.geometry):
        geoms = shp.geoms if hasattr(shp, "geoms") else [shp]
        for g in geoms:
          if g.is_empty or not hasattr(g, "exterior"):
            continue
          rings = [list(g.exterior.coords)] + \
                  [list(r.coords) for r in g.interiors]
          polys.append((tid, rings))
      self._polys = polys
      self._ids = sorted({p[0] for p in polys})
      self._id_colours = id_colours
      # label the central unit's tiles with their ids, as the web
      # app's design view does. The centroid is the visual centre and
      # the right anchor for (near-)convex tiles; representative_point
      # is only the fallback for concave shapes whose centroid falls
      # outside them (anchoring everything at representative_point put
      # labels visibly off-centre on asymmetric pentagons, since that
      # point comes from a bbox-midheight scanline, not the centre)
      labels = []
      for tid, shp in zip(unit.tiles.tile_id, unit.tiles.geometry):
        geoms = shp.geoms if hasattr(shp, "geoms") else [shp]
        for g in geoms:
          if g.is_empty or not hasattr(g, "exterior"):
            continue
          point = g.centroid
          if not g.contains(point):
            point = g.representative_point()
          x0, y0, x1, y1 = g.bounds
          labels.append((tid, point.x, point.y, x1 - x0, y1 - y0))
      self._labels = labels
      self._message = None if polys else "Nothing to draw."
    except Exception as e:  # keep UI alive whatever the library does
      self._polys, self._labels = [], []
      self._message = f"Preview failed:\n{e}"
    self.update()

  def show_message(self, text: str):
    """Replace the drawing with a centred message (errors, prompts)."""
    self._polys, self._labels, self._message = [], [], text
    self.update()

  def paintEvent(self, event):  # noqa: N802 (Qt API)
    """Fit the stored polygons to the widget and draw them.

    Map y grows upward, widget y grows downward, hence the flip in
    ``to_screen``. Ring coordinates come straight from shapely
    (exterior plus interior rings); QPainterPath's even-odd filling
    makes holes render correctly without extra work.
    """
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(self.rect(), QColor("#fafafa"))
    if not self._polys:
      painter.setPen(QPen(QColor("#666666")))
      painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       self._message or "")
      painter.end()
      return
    # Fit EVERYTHING drawn — the unit and every context shell — into
    # the widget. The extent comes from all rings of all polygons, not
    # only their exteriors and not only the central unit, so raising
    # the shell count zooms out rather than running off the edge.
    xs = [x for _, rings in self._polys for ring in rings for x, _y in ring]
    ys = [y for _, rings in self._polys for ring in rings for _x, y in ring]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = max(x1 - x0, 1e-9), max(y1 - y0, 1e-9)
    margin = 8
    scale = min((self.width() - 2 * margin) / w,
                (self.height() - 2 * margin) / h)
    ox = (self.width() - scale * w) / 2
    oy = (self.height() - scale * h) / 2

    def to_screen(x, y):
      return (ox + (x - x0) * scale,
              self.height() - (oy + (y - y0) * scale))

    for tid, rings in self._polys:
      path = QPainterPath()
      for ring in rings:
        pts = [to_screen(x, y) for x, y in ring]
        path.moveTo(*pts[0])
        for p in pts[1:]:
          path.lineTo(*p)
        path.closeSubpath()
      colour = self._id_colours.get(
        tid, bridge.ID_COLOURS[
          self._ids.index(tid) % len(bridge.ID_COLOURS)])
      painter.setBrush(QBrush(QColor(colour)))
      # No outline. The design view shows a unit and its neighbours as
      # areas of colour, and a dark line around every tile competes
      # with the thing being judged: whether the shapes read as
      # distinct elements by their COLOUR and form. A hairline also
      # thickens relative to the tiles as the pattern gets finer, so
      # at small spacings the preview turned into a mesh. Tile
      # boundaries on the MAP are a separate, deliberate control
      # ("Draw tile boundaries" on the Data & colours tab) and are
      # unaffected by this.
      painter.setPen(Qt.PenStyle.NoPen)
      painter.drawPath(path)

    # subtle tile-id labels on the central unit, as in the web app's
    # design view: semi-transparent, luminance-aware (dark ink on
    # light fills, light ink on dark), and only where the tile draws
    # large enough to carry a letter without clutter
    # the app's own font size, so the ids read as part of the
    # interface rather than as fine print (the user's ask); the
    # subtlety comes from the alpha, not from shrinking the type
    font = painter.font()
    app_font = QApplication.font()
    if app_font.pointSizeF() > 0:
      font.setPointSizeF(app_font.pointSizeF())
    painter.setFont(font)
    metrics = painter.fontMetrics()
    box = max(metrics.height(), metrics.horizontalAdvance("W")) + 4
    for tid, lx, ly, lw, lh in self._labels:
      # no label on a tile too small to hold one at this type size
      if min(lw, lh) * scale < box:
        continue
      fill = QColor(self._id_colours.get(
        tid, bridge.ID_COLOURS[
          self._ids.index(tid) % len(bridge.ID_COLOURS)]
        if tid in self._ids else "#cccccc"))
      # perceived luminance decides the ink; alpha keeps it subtle
      luminance = (0.299 * fill.red() + 0.587 * fill.green()
                   + 0.114 * fill.blue())
      ink = QColor(255, 255, 255, 170) if luminance < 140 \
        else QColor(0, 0, 0, 130)
      painter.setPen(ink)
      sx, sy = to_screen(lx, ly)
      painter.drawText(int(sx - box / 2), int(sy - box / 2), box, box,
                       Qt.AlignmentFlag.AlignCenter, tid)
    painter.end()


class WeavingSpaceDialog(QDialog):
  """The plugin's one window: design a tile unit, assign variables and
  symbology per element, and generate the tiled map as QGIS layers.

  The flow, in weavingspace terms: the Design tab's controls are the
  arguments to TileUnit/WeaveUnit plus the Tileable transform methods
  (``_build_unit`` performs exactly the web app's construction
  sequence); the Data & colours table maps tile_ids to dataset fields
  and initial symbology; ``_generate`` runs Tiling(...).get_tiled_map()
  in a background task; ``_add_output_layers`` splits the resulting
  GeoDataFrame by tile_id into one QGIS layer each (via bridge.py) and
  manages the layer-tree group across regenerations.
  """

  # element counts offered (the catalogue's keys: 2..16, 18, 19, 20)
  N_CHOICES = sorted(catalog.TILINGS_BY_N)
  # entries of the per-row Style dropdown; "Quant: X" rows all mean a
  # graduated (classed numeric) renderer, differing in break method
  MODES = ["Quant: Quantiles", "Quant: Equal intervals",
           "Quant: Natural breaks", "Quant: Pretty breaks",
           "Quant: Unclassed", "Categorized", "Single colour"]
  GRAD_SCHEMES = {
    "Quant: Quantiles": "Quantiles",
    "Quant: Equal intervals": "Equal intervals",
    "Quant: Natural breaks": "Natural breaks (Jenks)",
    "Quant: Pretty breaks": "Pretty breaks",
    # the web app's continuous look, reproduced with standard QGIS
    # machinery: 50 linearly spaced (equal) intervals reads as an
    # unclassed ramp at map scale while staying a normal graduated
    # renderer in the styling panel
    "Quant: Unclassed": "Unclassed",
  }
  # sequential ramps cycled across rows as defaults (all exist in the
  # QGIS style library, natively or installed by bridge.ensure_ramps_...)
  DEFAULT_RAMPS = ["Reds", "Blues", "Greens", "Purples", "Oranges", "Greys",
                   "YlOrRd", "PuBuGn", "RdPu", "GnBu", "YlGn", "BuPu"]

  def __init__(self, iface, parent=None):
    """iface is QGIS's plugin interface object (QgisInterface); the
    dialog only uses its message bar for success/warning banners, so
    tests pass a small stub instead."""
    super().__init__(parent)
    self.iface = iface
    self.setWindowTitle(
      "WeavingSpace – tiled & woven multivariate maps "
      f"(v{_plugin_version()})")
    # the current weavingspace Tileable (rebuilt by _rebuild_unit) and
    # the in-flight background task, if any (single-flight: _generate
    # refuses to start a second one)
    self._unit = None
    self._task = None
    # regeneration tracking, so Generate replaces rather than piles up:
    # our layer-tree group's name, the project layer id per tile_id,
    # the outline layer's id, each element's last-seeded assignment
    # signature (unchanged signature => keep the user's hand-refined
    # renderer), the last GeoPackage path, and the last full-run
    # signature (used to skip no-op live regenerations)
    self._group_name = None
    self._element_layer_ids = {}
    self._outline_layer_id = None
    self._last_signatures = {}
    self._last_path = None
    self._last_run_sig = None
    # the geometry of the last completed run, so a later style-only
    # change can be answered without tiling again
    self._last_geometry_sig = None
    # per-element UI memory, keyed by tile_id so it survives table
    # rebuilds: category counts per (layer id, field), each element's
    # class-source choice, QML files browsed anywhere this session,
    # picked single colours, and last ramp names
    self._cat_count_cache = {}
    self._class_choices = {}
    self._browsed_qmls = []
    self._single_colours = {}
    self._ramp_choices = {}
    self._reverse_choices = {}
    self._opacity_choices = {}
    # Colours chosen by hand in the Categorical colour editor:
    # {tile_id: {field: {str(value): "#rrggbb"}}}. Keyed by FIELD as
    # well as element so that moving an element to another variable
    # and back restores the work rather than discarding it, and so
    # that two fields sharing a value name ("other", "none", "1")
    # cannot silently colour each other.
    self._category_colours = {}
    # which layer auto-spacing last ran for (it must run once per
    # newly chosen layer, never on the combo's spurious re-emissions)
    self._auto_spacing_layer = None
    # Bumped whenever the region layer tells us it changed. The
    # signatures below include it, so an edit made in QGIS while this
    # dialog is open cannot be mistaken for "nothing has changed".
    self._data_version = 0
    self._watched_layer = None
    self._watched_fields = ()
    # None until a layer is chosen, so choosing the first one is not
    # mistaken for the CRS having been changed underneath us.
    self._watched_crs = None
    # So that losing a layer can be told apart from never having had
    # one: the dialog opens with the combo empty and that is not an
    # event worth reporting.
    self._had_a_layer = False
    # Said once per layer, not once per debounce tick: a warning
    # repeated every 900ms is one a user learns to stop reading.
    self._said_live_cannot_track = False
    # Likewise once per layer: a source that has gone stays gone, and
    # repeating it on every debounce tick teaches the user to ignore
    # the message line.
    self._said_source_gone = False
    self._retire_previous_instance()
    self._adopt_existing_group()
    bridge.ensure_ramps_installed()
    self._ramp_names = bridge.ramp_names()
    self._preview_timer = QTimer(self)
    self._preview_timer.setSingleShot(True)
    self._preview_timer.setInterval(350)
    self._preview_timer.timeout.connect(self._rebuild_unit)
    # live update: from the moment a layer and variables are in
    # place (no button press needed), setting changes regenerate the
    # map automatically (debounced, size-gated, no-op-skipping)
    self._live_timer = QTimer(self)
    self._live_timer.setSingleShot(True)
    self._live_timer.setInterval(900)
    self._live_timer.timeout.connect(self._maybe_live_generate)
    self._live_pending = False
    # {field: how many distinct values it had last run}, so a
    # categorical field that gains or loses a class can be
    # reported: its existing colours will have moved.
    self._category_counts = {}
    self._build_ui()
    self._update_layer_exclusions()
    # order matters: families must be populated (_on_n_changed) before
    # the layer handler builds the first unit and queues the first
    # automatic render
    self._on_n_changed()
    self._on_layer_changed()
    # singleShot(0, fn) runs fn on the next event-loop pass, i.e. after
    # pending layout work; sizing any earlier reads stale geometry
    QTimer.singleShot(0, self._fit_to_design)

  # ---------------------------------------------------------------- UI setup

  def _build_ui(self):
    """Construct every widget and wire its signals.

    Layout is nested boxes: a horizontal split (controls left, preview
    right), tabs on the left, and QFormLayouts (label/field rows)
    inside the tabs. Widgets kept as ``self.*`` are read back later by
    ``_unit_kwargs``/``_assignments``; everything else is fire-and-
    forget. Every control that affects the design connects to
    ``_queue_preview``; things that affect only the output connect to
    ``_queue_live``.
    """
    main = QHBoxLayout(self)
    left = QVBoxLayout()
    main.addLayout(left, 5)

    right = QVBoxLayout()
    right.addWidget(QLabel("Tile unit preview"))
    self.preview = TilePreview()
    self.preview.setMinimumSize(230, 230)
    right.addWidget(self.preview, 1)
    shells_row = QHBoxLayout()
    shells_row.addWidget(QLabel("Context shells"))
    self.shells_spin = QSpinBox()
    self.shells_spin.setRange(0, 4)
    # One ring of neighbours is the default because a great deal of
    # what a unit does only becomes visible once it is repeated:
    # insetting, how tiles meet across the join, and whether the
    # pattern reads the way it looks in isolation. The unit alone is
    # still one click away for anyone who wants the bare design.
    self.shells_spin.setValue(1)
    self.shells_spin.setToolTip(
      "Rings of neighbouring copies around the unit; "
      "0 shows the unit alone.")
    self.shells_spin.valueChanged.connect(
      self._refresh_preview_colours)
    shells_row.addWidget(self.shells_spin)
    shells_row.addStretch(1)
    right.addLayout(shells_row)
    main.addLayout(right, 2)
    self._design_wrapper = None

    tabs = QTabWidget()
    left.addWidget(tabs, 1)

    # ---- tab 1: design
    design = QWidget()
    form = QFormLayout(design)

    # QgsMapLayerComboBox is QGIS's own layer chooser: it tracks the
    # project's layer list by itself and emits layerChanged
    self.layer_combo = QgsMapLayerComboBox()
    self.layer_combo.setFilters(_polygon_filter())
    self.layer_combo.setToolTip(
      "The polygon layer whose attributes will be mapped. Best not to use "
      "lat-long datasets.")
    self.layer_combo.layerChanged.connect(self._on_layer_changed)
    form.addRow("Region layer", self.layer_combo)

    self.n_combo = QComboBox()
    for n in self.N_CHOICES:
      self.n_combo.addItem(str(n), n)
    self.n_combo.setCurrentText("4")
    self.n_combo.setToolTip(
      "How many variables the pattern can carry.")
    self.n_combo.currentIndexChanged.connect(self._on_n_changed)
    form.addRow("Number of elements", self.n_combo)

    self.kind_combo = QComboBox()
    self.kind_combo.addItems(["tiling", "weave"])
    self.kind_combo.setToolTip(
      "Tilings give side-by-side patches; weaves give strands "
      "the eye can follow.")
    self.kind_combo.currentIndexChanged.connect(self._on_kind_changed)
    form.addRow("Tiling or weave", self.kind_combo)

    self.family_combo = QComboBox()
    self.family_combo.setToolTip(
      "The pattern catalogue for the chosen element count.")
    self.family_combo.currentIndexChanged.connect(self._on_family_changed)
    form.addRow("Family", self.family_combo)

    self.spacing_spin = QDoubleSpinBox()
    self.spacing_spin.setRange(1e-6, 1e12)
    self.spacing_spin.setDecimals(6)
    self.spacing_spin.setValue(1000)
    self.spacing_spin.setToolTip(
      "The pattern's grain in map units. Try aiming near the typical polygon "
      "width.")
    self.spacing_spin.valueChanged.connect(self._queue_preview)
    spacing_row = QHBoxLayout()
    spacing_row.addWidget(self.spacing_spin)
    auto = QPushButton("Auto")
    auto.setToolTip("A coarse value from the layer extent, good for iterating")
    auto.clicked.connect(self._auto_spacing)
    spacing_row.addWidget(auto)
    form.addRow("Spacing (map units)", spacing_row)

    # family-specific options
    self.opt_offset = QDoubleSpinBox()
    self.opt_offset.setRange(-1.0, 1.0)
    self.opt_offset.setSingleStep(0.01)
    self.opt_offset.setDecimals(2)
    self.opt_offset.setToolTip(
      "Where the cuts start: 0 at the corners, 1 at the edge "
      "midpoints.")
    self.opt_offset.valueChanged.connect(self._queue_preview)
    self.opt_offset_row = self._form_row(form, "Offset", self.opt_offset)

    self.opt_offset_angle = QDoubleSpinBox()
    self.opt_offset_angle.setRange(-50, 85)
    self.opt_offset_angle.setSingleStep(1)
    self.opt_offset_angle.setToolTip(
      "Rotates the dissection's internal cuts within each tile.")
    self.opt_offset_angle.valueChanged.connect(self._queue_preview)
    self.opt_offset_angle_row = self._form_row(
      form, "Inner angle", self.opt_offset_angle)

    self.opt_point_angle = QDoubleSpinBox()
    self.opt_point_angle.setRange(10, 120)
    self.opt_point_angle.setValue(30)
    self.opt_point_angle.setToolTip(
      "Sharpness of the star points, in degrees.")
    self.opt_point_angle.valueChanged.connect(self._queue_preview)
    self.opt_point_angle_row = self._form_row(
      form, "Point angle", self.opt_point_angle)

    self.opt_aspect = QDoubleSpinBox()
    self.opt_aspect.setRange(0.083, 1.0)
    self.opt_aspect.setSingleStep(0.083)
    self.opt_aspect.setDecimals(3)
    self.opt_aspect.setValue(0.75)
    self.opt_aspect.setToolTip(
      "Strand width as a fraction of spacing; 1.0 leaves no gaps.")
    self.opt_aspect.valueChanged.connect(self._queue_preview)
    self.opt_aspect_row = self._form_row(
      form, "Strand width", self.opt_aspect)

    self.opt_over_under = QLineEdit()
    self.opt_over_under.setPlaceholderText("e.g. 2 or 1,2 or 1,2,2,1")
    self.opt_over_under.setToolTip(
      "How many crossing strands each strand passes over, then under.")
    self.opt_over_under.textChanged.connect(self._queue_preview)
    self.opt_over_under_row = self._form_row(
      form, "Over-under", self.opt_over_under)

    # grid's array shape: two spinners in one row. With fewer
    # elements than cells the library leaves the surplus cells as
    # regular openings (see catalog.tightest_grid), so these two
    # controls set both the arrangement and how porous the grid is.
    grid_box = QWidget()
    grid_lay = QHBoxLayout(grid_box)
    grid_lay.setContentsMargins(0, 0, 0, 0)
    self.opt_grid_rows = QSpinBox()
    self.opt_grid_rows.setRange(1, 26)
    self.opt_grid_cols = QSpinBox()
    self.opt_grid_cols.setRange(1, 26)
    for sp, tip in ((self.opt_grid_rows, "Rows of squares in the unit"),
                    (self.opt_grid_cols,
                     "Columns of squares in the unit. Surplus cells "
                     "become regular openings.")):
      sp.setToolTip(tip)
      sp.valueChanged.connect(self._queue_preview)
      grid_lay.addWidget(sp)
    self.opt_grid_row = self._form_row(
      form, "Grid rows \u00d7 cols", grid_box)

    # transformations: paired spins keep the dialog short enough to
    # leave the map visible behind it
    mods = QGroupBox("Transformations")
    mform = QFormLayout(mods)

    def spin(lo, hi, val, step):
      box = QDoubleSpinBox()
      box.setRange(lo, hi)
      box.setValue(val)
      box.setSingleStep(step)
      box.setDecimals(3 if step < 1 else 1)
      box.valueChanged.connect(self._queue_preview)
      return box

    def pair(label, a, b):
      row = QHBoxLayout()
      row.addWidget(a)
      row.addWidget(b)
      mform.addRow(label, row)

    self.mod_rotate = spin(-90, 90, 0, 1)
    self.mod_rotate.setToolTip(
      "Turn the whole pattern; 15–75° usually suits two-direction "
      "weaves.")
    mform.addRow("Rotate (°)", self.mod_rotate)
    self.mod_scale_x = spin(0.5, 4.0, 1.0, 0.02)
    self.mod_scale_x.setToolTip("Stretch the pattern right-left.")
    self.mod_scale_y = spin(0.5, 4.0, 1.0, 0.02)
    self.mod_scale_y.setToolTip("Stretch the pattern up-down.")
    pair("Scale EW / NS", self.mod_scale_x, self.mod_scale_y)
    self.mod_skew_x = spin(-45, 45, 0, 1)
    self.mod_skew_x.setToolTip("Slant the pattern right-left.")
    self.mod_skew_y = spin(-45, 45, 0, 1)
    self.mod_skew_y.setToolTip("Slant the pattern up-down.")
    pair("Skew EW / NS (°)", self.mod_skew_x, self.mod_skew_y)
    self.mod_p_inset = spin(0, 10, 0, 0.1)
    self.mod_p_inset.setToolTip(
      "Opens a gap around each whole unit (tilings only).")
    self.mod_t_inset = spin(0, 5, 0, 0.1)
    self.mod_t_inset.setToolTip(
      "Opens a thin gap around every tile or strand.")
    pair("Inset group / tiles (%)", self.mod_p_inset, self.mod_t_inset)
    self.mod_glyph = QCheckBox("Scale as glyph (independent of tiling)")
    self.mod_glyph.setToolTip(
      "Shrink each unit in place, into separate glyphs.")
    self.mod_glyph.toggled.connect(self._queue_preview)
    mform.addRow(self.mod_glyph)

    wrapper = QWidget()
    wl = QVBoxLayout(wrapper)
    wl.setContentsMargins(0, 0, 0, 0)
    wl.addWidget(design)
    wl.addWidget(mods)
    wl.addStretch(1)
    tabs.addTab(wrapper, "Design")
    self._design_wrapper = wrapper

    # ---- tab 2: data & colours
    data_tab = QWidget()
    dlayout = QVBoxLayout(data_tab)
    hint = QLabel(
      "Each element/row below becomes its own QGIS layer, initially "
      "symbolized using the options available under the 'Style' "
      "dropdowns; refine it afterwards in QGIS's built-in Layer "
      "Styling panel. A plausible style is picked from each field's "
      "type and follows the variable until you choose one yourself.")
    hint.setWordWrap(True)
    dlayout.addWidget(hint)
    self.table = QTableWidget(0, 9)
    self.table.setHorizontalHeaderLabels(
      ["Tile id", "Variable", "Style", "Classes", "Colour ramp",
       "Reverse", "Opacity %", "Categ colourmap src", "Edit colours"])
    self.table.setColumnWidth(0, 55)
    self.table.setColumnWidth(1, 160)
    self.table.setColumnWidth(2, 165)
    self.table.setColumnWidth(3, 55)
    self.table.setColumnWidth(4, 172)   # a 64px swatch plus the name
    self.table.setColumnWidth(5, 62)
    self.table.setColumnWidth(6, 72)
    self.table.setColumnWidth(7, 150)
    self.table.setColumnWidth(COL_EDIT_COLOURS, 92)
    self.table.setColumnHidden(3, True)
    self.table.setColumnHidden(7, True)
    self.table.setColumnHidden(COL_EDIT_COLOURS, True)
    # "Edit colours" belongs beside the ramp, since it does the same
    # job by hand. It is nevertheless the LAST column logically, and
    # only moved into place visually. Inserting it at position 5 would
    # have renumbered Reverse, Opacity and the class source, and those
    # numbers are written out in dozens of places here and in the
    # tests -- a renumbering that silently repoints a test at the
    # wrong widget is exactly how a test comes to pass for the wrong
    # reason, which has happened here before.
    self.table.horizontalHeader().moveSection(COL_EDIT_COLOURS, 5)
    dlayout.addWidget(self.table, 1)

    cls_row = QFormLayout()
    self.opt_tile_outlines = QCheckBox("Draw tile boundaries")
    self.opt_tile_outlines.setToolTip(
      "Outline every tile on the map.")
    cls_row.addRow(self.opt_tile_outlines)
    dlayout.addLayout(cls_row)
    tabs.addTab(data_tab, "Data && colours")

    # ---- tab 3: options
    opts_tab = QWidget()
    olayout = QVBoxLayout(opts_tab)
    self.opt_join_prototiles = QCheckBox("Join data using whole tileable")
    self.opt_join_prototiles.setToolTip(
      "Every element in a unit takes its data from the same area.")
    self.opt_retain = QCheckBox("Retain complete tileables at edges")
    self.opt_retain.setToolTip(
      "Keeps whole units that touch the region, letting the pattern "
      "spill outward.")
    self.opt_clip = QCheckBox("Clip by map units (no ragged edges)")
    self.opt_clip.setToolTip(
      "Trims the pattern to the region outline. The sloleft step.")
    self.opt_icons = QCheckBox("Use tileable as icon (one per map unit)")
    self.opt_icons.setToolTip(
      "One unit at the centre of each polygon, instead of a "
      "continuous pattern.")
    self.opt_outlines = QCheckBox("Add map unit outlines layer")
    self.opt_outlines.setToolTip(
      "Adds the region boundaries as outlines on top of the pattern.")
    self.opt_new_group = QCheckBox(
      "Create as new group (keep the previous result)")
    self.opt_new_group.setToolTip(
      "Keeps the previous result and adds this run as a separate "
      "group.")
    self.opt_colour_warnings = QCheckBox(
      "Warn about lack of legibility in colour choices")
    self.opt_colour_warnings.setToolTip(
      "Warns when two elements use colours a reader may confuse.")
    for cb in (self.opt_join_prototiles, self.opt_retain, self.opt_clip,
               self.opt_icons, self.opt_outlines, self.opt_new_group,
               self.opt_colour_warnings):
      olayout.addWidget(cb)

    out_form = QFormLayout()
    self.gpkg_widget = QgsFileWidget()
    from . import compat
    compat.set_save_file_mode(self.gpkg_widget)
    self.gpkg_widget.setFilter("GeoPackage (*.gpkg)")
    self.gpkg_widget.setDialogTitle("Save tiled map to GeoPackage")
    self.gpkg_widget.setToolTip(
      "Save all element layers, with styling, to one file.")
    out_form.addRow("Save to GeoPackage\n(empty = temporary layers)",
                    self.gpkg_widget)
    olayout.addLayout(out_form)
    olayout.addStretch(1)
    tabs.addTab(opts_tab, "Map options")

    # ---- tab 4: help (condensed guide; full version in docs/USER-GUIDE.md)
    # QTextBrowser renders a subset of HTML and opens links externally
    from qgis.PyQt.QtWidgets import QTextBrowser
    from .help_content import HELP_HTML
    help_tab = QTextBrowser()
    help_tab.setOpenExternalLinks(True)
    help_tab.setHtml(
      HELP_HTML + f"<p><small>WeavingSpace QGIS plugin version "
                  f"{_plugin_version()}</small></p>")
    tabs.addTab(help_tab, "Help")

    # ---- bottom bar
    bottom = QHBoxLayout()
    self.live_check = QCheckBox("Live update")
    self.live_check.setChecked(True)
    self.live_check.setToolTip(
      "Draws and redraws the map as you change settings, without "
      "pressing Generate.")
    bottom.addWidget(self.live_check)
    self.live_note = QLabel("")
    self.live_note.setStyleSheet("color: #888888;")
    bottom.addWidget(self.live_note)
    self.progress = QProgressBar()
    self.progress.setVisible(False)
    bottom.addWidget(self.progress, 1)
    bottom.addStretch(1)
    self.generate_btn = QPushButton("Generate tiled map")
    self.generate_btn.clicked.connect(lambda: self._generate())
    bottom.addWidget(self.generate_btn)
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(self.close)
    bottom.addWidget(close_btn)
    left.addLayout(bottom)

    # wider than tall: room for the table's columns, height set by the
    # Design tab so the map stays visible behind the dialog
    self.resize(1180, 560)

    # any of these should refresh the live map too (design controls
    # already funnel through _queue_preview)
    for cb in (self.opt_tile_outlines, self.opt_join_prototiles,
               self.opt_retain, self.opt_clip, self.opt_icons,
               self.opt_outlines):
      cb.toggled.connect(self._queue_live)

  def _fit_to_design(self):
    """Size the dialog to the Design tab's actual (visible) content, so
    it stays short enough to leave the map visible behind it; called
    again when family-specific rows appear or disappear.

    Qt's ``sizeHint`` (a widget's preferred size) is only trustworthy
    after its layouts have recomputed, and hidden rows can leave stale
    contributions behind; invalidating every child layout first forces
    an honest measurement. The +96 covers the tab bar and bottom bar.
    """
    if getattr(self, "_design_wrapper", None) is None:
      return
    for child in self._design_wrapper.findChildren(QWidget):
      if child.layout() is not None:
        child.layout().invalidate()
    layout = self._design_wrapper.layout()
    if layout is not None:
      layout.invalidate()
      layout.activate()
    height = self._design_wrapper.sizeHint().height() + 96
    self.resize(max(self.width(), 1180), max(400, height))

  def _form_row(self, form: QFormLayout, label: str, widget: QWidget):
    """Add a labelled row to a form.

    Args:
      form: the QFormLayout to add to.
      label: the text shown beside the control.
      widget: the control itself.

    Returns:
      (label widget, control) so ``_on_family_changed`` can show and
      hide the pair together — hiding a control while its label stays
      is the classic way a dialog ends up looking broken.
    """
    lab = QLabel(label)
    form.addRow(lab, widget)
    return (lab, widget)

  # ------------------------------------------------------------- UI dynamics

  def _current_spec(self) -> dict | None:
    """The catalogue entry (TileUnit/WeaveUnit constructor kwargs) for
    the currently selected element count and family, or None while the
    combos are being repopulated."""
    name = self.family_combo.currentText()
    n = self.n_combo.currentData()
    return catalog.TILINGS_BY_N.get(n, {}).get(name)

  def _on_n_changed(self):
    """Repopulate the family list for the chosen element count.

    Some counts exist only as tilings or only as weaves; if the current
    kind has no families the kind combo is flipped silently
    (blockSignals prevents that flip from re-triggering this handler).
    """
    n = self.n_combo.currentData()
    families = catalog.TILINGS_BY_N.get(n, {})
    kind = self.kind_combo.currentText()
    names = [name for name, spec in families.items()
             if spec["type"] == ("tiling" if kind == "tiling" else "weave")]
    if not names:  # this n only has the other kind: switch kind silently
      names = list(families)
      other = families[names[0]]["type"]
      self.kind_combo.blockSignals(True)
      self.kind_combo.setCurrentText(
        "tiling" if other == "tiling" else "weave")
      self.kind_combo.blockSignals(False)
      kind = self.kind_combo.currentText()
      names = [name for name, spec in families.items()
               if spec["type"] == ("tiling" if kind == "tiling" else "weave")]
    self.family_combo.blockSignals(True)
    self.family_combo.clear()
    self.family_combo.addItems(names)
    self.family_combo.blockSignals(False)
    self._on_family_changed()

  def _on_kind_changed(self):
    """Tiling/weave toggle reuses the family-repopulation logic."""
    self._on_n_changed()

  def _on_family_changed(self):
    """Show exactly the option rows this family understands.

    The mapping mirrors weavingspace's constructor arguments: slice and
    dissection tilings take ``offset`` (dissections also
    ``offset_angle``, with hex and square variants allowing different
    angle ranges), star1 takes ``point_angle``, weaves take ``aspect``,
    and twill/basket weaves an over-under pattern whose default comes
    from the catalogue entry. The dialog is then re-fitted because row
    visibility changes its natural height.
    """
    spec = self._current_spec()
    if spec is None:
      return
    is_weave = spec["type"] == "weave"
    tiling_type = spec.get("tiling_type", "")
    show = {
      self.opt_offset_row: not is_weave and (
        "slice" in tiling_type or "dissect" in tiling_type),
      self.opt_offset_angle_row: not is_weave and "dissect" in tiling_type,
      self.opt_point_angle_row: tiling_type == "star1",
      self.opt_aspect_row: is_weave,
      self.opt_over_under_row:
        is_weave and spec.get("weave_type") in ("twill", "basket"),
      self.opt_grid_row: tiling_type == "grid",
    }
    for (lab, widget), visible in show.items():
      lab.setVisible(visible)
      widget.setVisible(visible)
    if "dissect" in tiling_type:
      self.opt_offset.setRange(0, 1)
      lo, hi = ((-50, 85) if "hex" in tiling_type else (-30, 70))
      self.opt_offset_angle.setRange(lo, hi)
    elif "slice" in tiling_type:
      self.opt_offset.setRange(-1, 1)
    if is_weave and spec.get("weave_type") in ("twill", "basket"):
      self.opt_over_under.blockSignals(True)
      self.opt_over_under.setText(str(spec.get("n", "2")))
      self.opt_over_under.blockSignals(False)
    if tiling_type == "grid":
      # reset to the tightest fit for this element count; a signal
      # here would schedule a second rebuild of the same unit
      rows, cols = catalog.tightest_grid(spec["n"])
      for sp, v in ((self.opt_grid_rows, rows),
                    (self.opt_grid_cols, cols)):
        sp.blockSignals(True)
        sp.setValue(v)
        sp.blockSignals(False)
    QTimer.singleShot(0, self._fit_to_design)
    self._queue_preview()

  def _update_layer_exclusions(self):
    """Keep the plugin's own output layers out of the region combo.

    Without this, a generated element layer (tagged with a custom
    property) can be offered, or even auto-selected, as the next
    region, and the plugin would happily tile its own output.
    """
    outputs = [lyr for lyr in QgsProject.instance().mapLayers().values()
               if lyr.customProperty("weavingspace_output")]
    try:
      self.layer_combo.setExceptedLayerList(outputs)
    except Exception:
      pass

  def _on_layer_changed(self):
    """React to the region-layer choice (or to combo re-emissions).

    QgsMapLayerComboBox re-emits layerChanged whenever the project's
    layer list changes, which happens after every generation, so
    anything here must be safe to run repeatedly for the same layer.
    """
    self._cat_count_cache = {}
    layer = self.layer_combo.currentLayer()
    # Hear the layer itself, not merely the fact that a different one
    # was chosen: a user editing in QGIS never touches this combo.
    if layer is not self._watched_layer:
      self._watch_layer(layer)
      self._said_live_cannot_track = False      # a new layer, a new answer
      self._said_source_gone = False
      self._watched_fields = tuple(
        f.name() for f in layer.fields()) if layer is not None else ()
      self._watched_crs = layer.crs().authid() if layer is not None else None
    if layer is None and self._had_a_layer:
      # The layer combo empties itself when its layer leaves the
      # project, and does it silently. A user who removed a layer for
      # some unrelated reason is otherwise left with a dialog whose
      # controls all still look armed and a Generate button that will
      # simply tell them to choose a layer.
      self._had_a_layer = False
      self._report_quietly(
        "The region layer was removed from the project, so there is "
        "nothing to map. Choose another layer.")
    elif layer is not None:
      self._had_a_layer = True
    self._adapt_to_the_layer(layer)
    # derive spacing once per newly chosen layer; the combo re-emits
    # layerChanged whenever project layers shuffle (e.g. after every
    # generation), and that must not clobber a hand-set spacing
    if layer is not None and layer.id() != self._auto_spacing_layer:
      self._auto_spacing_layer = layer.id()
      self._auto_spacing()
    # populate the variable choosers the moment the layer is chosen
    # (synchronously, not on the preview debounce), and queue the
    # automatic first render
    self._rebuild_unit()
    self._queue_live()

  def _layer_fingerprint(self):
    """What the region layer CONTAINS, cheaply enough to ask often.

    Returns:
      A comparable tuple — feature count, extent rounded to the metre,
      field names, CRS — or None when no layer is chosen. Combined
      with ``_data_version`` this goes into both signatures.

    Why both this and the signals. This part is cheap, deterministic,
    and catches edits made straight through the data provider, which
    is what Processing and a good deal of plugin code do and which
    emits nothing this dialog could hear. It cannot catch an edit that
    leaves the count and the bounding box alone — a value retyped, a
    vertex nudged inwards — which is exactly what the signals are for.
    Neither mechanism covers the other's blind spot, so the plugin
    uses both.

    The extent is rounded because it is floating-point and asking
    twice about an unchanged layer must give the same answer; a metre
    is far below the size of anything these tiles are drawn at.
    """
    from . import compat
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return None
    if not compat.layer_data_is_available(layer):
      # The source is gone -- a deleted file, a dropped connection.
      # Reading extent() here would segfault QGIS outright, so the
      # fingerprint says "unavailable" and lets the callers refuse.
      return ("unavailable",)
    count = layer.featureCount()
    if count < 0:
      # The provider does not know yet. Remote sources -- WFS, OGC API
      # - Features, an ArcGIS service, PostGIS over a slow link --
      # answer -1 until they have fetched, and some only ever return an
      # estimate. A number like that is worse than no number: it would
      # report changes that never happened and hide ones that did,
      # according to which way the estimate drifted. None says "not
      # known", and _data_is_unobservable decides what to do about it.
      #
      # Nothing is bumped here. An earlier version incremented the
      # data version from inside this method, which is a side effect
      # in a getter and, worse, a loop: both signatures call this on
      # every debounce tick, so an uncountable layer re-tiled
      # continuously -- across a network, with nobody watching.
      count = None
    ext = layer.extent()
    return (
      count,
      (round(ext.xMinimum()), round(ext.yMinimum()),
       round(ext.xMaximum()), round(ext.yMaximum())),
      tuple(f.name() for f in layer.fields()),
      layer.crs().authid(),
    )

  def _data_is_unobservable(self) -> bool:
    """Whether this layer can change without the plugin being able to tell.

    Returns:
      True for a layer that will not say how many features it has.
      That is the honest signature of a source living somewhere else
      -- a WFS, an OGC API - Features endpoint, an ArcGIS service, a
      database over a slow link -- which can be rewritten on a server
      with no file touched here and no signal raised.

    There is no clever way to close this gap. Counting the features
    ourselves means pulling the whole dataset across a network, and
    doing that on a debounce tick is worse than the problem. So the
    plugin is explicit about what it does not know, and the two
    callers answer differently: see _restyle_only, which always
    re-tiles such a layer when the user asks, and _maybe_live_generate,
    which declines to chase it.
    """
    layer = self.layer_combo.currentLayer()
    return layer is not None and layer.featureCount() < 0

  def _bump_data_version(self, *_args):
    """Record that the region layer changed under us.

    Args:
      *_args: whatever the emitting signal carries; all of them are
        ignored, because the only thing being recorded is THAT
        something changed.

    Returns:
      None. The counter feeds both signatures, so the next run cannot
      be skipped as a no-op, and a live update is queued so a user
      watching the map sees it follow their edit.
    """
    self._data_version += 1
    # Follow the edit as well as recording it. This is the only place
    # a field being renamed, dropped or retyped is heard: the layer
    # COMBO does not change when a user edits the layer it is already
    # pointed at, so _on_layer_changed never runs and an element would
    # go on naming a column that has gone -- failing later, at the
    # join, with a message about a missing column rather than about
    # the edit that removed it.
    self._adapt_to_the_layer(self._watched_layer)
    self._queue_live()

  # The layer signals worth hearing. Editing through QGIS's own tools
  # goes through the edit buffer and ends in committedX / dataChanged;
  # updatedFields covers a column added, dropped or renamed; crsChanged
  # covers a CRS reassigned without reprojecting, which changes what
  # every coordinate means without changing one of them.
  _WATCHED_SIGNALS = ("dataChanged", "updatedFields", "crsChanged",
                      "featureAdded", "featuresDeleted", "geometryChanged",
                      "attributeValueChanged", "committedGeometriesChanges",
                      "committedAttributeValuesChanges", "editingStopped",
                      # A subset filter set in Layer Properties changes
                      # which features exist for everything downstream,
                      # without touching one of them.
                      "subsetStringChanged",
                      # The layer now reads from somewhere else, or has
                      # been reloaded from a file that changed underneath
                      # it. QGIS does not watch files, so this arrives
                      # only when something asks the layer to reload --
                      # the Reload command, an auto-refresh interval --
                      # but when it does arrive the map is out of date.
                      "dataSourceChanged")

  # repaintRequested is deliberately NOT in that list, though it looks
  # tempting. It fires on every style change too, and re-tiling on a
  # style change is the exact cost the restyle fast path exists to
  # avoid.

  def _watch_layer(self, layer):
    """Listen to the chosen layer, and stop listening to the last one.

    Args:
      layer: the newly chosen region layer, or None.

    Returns:
      None. Connections are made defensively: the signal list is
      QGIS's, and a future release may drop one. A missing signal
      should cost this plugin one blind spot, not an exception on
      every layer change, so each is connected only if it exists.
    """
    previous = self._watched_layer
    if previous is not None and previous is not layer:
      # The whole loop is guarded, not merely the disconnect. When a
      # layer is removed from the project its C++ object goes with it,
      # and then even ASKING the Python wrapper for an attribute
      # raises RuntimeError -- which is precisely the moment this runs,
      # since removing the layer is what changed the combo.
      try:
        # repaintRequested is included on the way OUT whether or not it
        # was connected on the way in: disconnecting something that was
        # never connected is caught below, whereas leaving one behind
        # would re-tile on every style change of a layer the user has
        # moved on from.
        for name in tuple(self._WATCHED_SIGNALS) + ("repaintRequested",):
          signal = getattr(previous, name, None)
          if signal is not None:
            try:
              signal.disconnect(self._bump_data_version)
            except (TypeError, RuntimeError):
              pass          # never connected; nothing to undo
      except RuntimeError:
        pass                # the layer is already gone, signals with it
    self._watched_layer = layer
    if layer is None:
      return
    # A layer QGIS reloads on a timer is one the user has declared
    # dynamic, and its reload arrives as a repaint rather than as any
    # of the editing signals. That is the ONLY circumstance in which
    # repaintRequested is worth hearing: on an ordinary layer it also
    # fires for every style change, and re-tiling on those is the whole
    # cost the restyle fast path exists to avoid.
    from . import compat          # imported here, as elsewhere in this file
    names = list(self._WATCHED_SIGNALS)
    if compat.layer_auto_refreshes(layer):
      names.append("repaintRequested")
    for name in names:
      signal = getattr(layer, name, None)
      if signal is not None:
        try:
          signal.connect(self._bump_data_version)
        except (TypeError, RuntimeError):
          pass

  def _adapt_to_the_layer(self, layer):
    """Follow the layer when an edit makes a setting untrue.

    Args:
      layer: the current region layer, or None.

    Returns:
      None. Settings may be changed, and anything changed is reported.

    Adapting rather than only complaining, because in these cases
    there is exactly one sensible answer and making the user find it
    is busywork. Where there is NOT one sensible answer the dialog
    does not guess: a field that vanished while another appeared may
    be a rename or may be two unrelated edits, and quietly pointing an
    element at the new column would map data the user never asked
    for. That case unassigns the element and says so, which is the
    honest response to an ambiguity.
    """
    if layer is None:
      return
    from . import compat
    if not compat.layer_data_is_available(layer):
      return                      # nothing safe to read; see _generate

    # The spacing is a number of the LAYER's units, so a CRS change
    # silently changes what it means: 500 metres becomes 500 feet, or
    # 500 of whatever a layer with no CRS is counted in. Re-deriving
    # is the only sensible answer -- the old number is not wrong so
    # much as no longer about anything -- and it is exactly the kind
    # of adaptation that must be announced, because a user who typed
    # a spacing will otherwise find it changed with no explanation.
    authid = layer.crs().authid()
    if self._watched_crs is not None and authid != self._watched_crs:
      self._watched_crs = authid
      before = self.spacing_spin.value()
      self._auto_spacing()
      after = self.spacing_spin.value()
      if abs(after - before) > 1e-9:
        self._report_quietly(
          f"The layer's coordinate system changed, so the spacing has "
          f"been recalculated as {after:,.6f}".rstrip("0").rstrip(".")
          + " " + compat.map_unit_label(layer) + ".")
    else:
      self._watched_crs = authid

    names = tuple(f.name() for f in layer.fields())
    if names == self._watched_fields:
      return
    lost = [n for n in self._watched_fields if n not in names]
    self._watched_fields = names

    # Whatever else changed, the choosers must now offer exactly the
    # columns the layer has. A column ADDED in QGIS -- the Field
    # Calculator is the usual way -- was previously invisible here
    # until the user switched layers and back, with nothing on screen
    # to suggest that was the remedy.
    #
    # In place, never by rebuilding the table: a rebuild replaces every
    # cell widget, and one arriving mid-interaction is the "race among
    # choosers" this project has already paid for once, where an open
    # dropdown dies and the pick commits to a dead widget. Editing the
    # items of the existing combos leaves widget identity alone, which
    # is what that race's regression test checks.
    wanted = ["---"] + list(names)
    # What each row was showing BEFORE the item lists are rewritten.
    # Rewriting them drops any selection naming a column that has gone,
    # so a later pass asking "which rows lost their column" would find
    # none: they would all read "---" already, and the re-default below
    # would never fire. Read first, then rewrite.
    chosen_by_row = {}
    for row in range(self.table.rowCount()):
      combo = self.table.cellWidget(row, 1)
      if combo is not None and hasattr(combo, "currentText"):
        chosen_by_row[row] = combo.currentText()
    for row in range(self.table.rowCount()):
      combo = self.table.cellWidget(row, 1)
      if combo is None or not hasattr(combo, "itemText"):
        continue
      if [combo.itemText(i) for i in range(combo.count())] == wanted:
        continue
      chosen = chosen_by_row.get(row, combo.currentText())
      combo.blockSignals(True)
      combo.clear()
      combo.addItems(wanted)
      # A choice that survived the edit is kept; one whose column has
      # gone falls back to unassigned, and the message below says so.
      combo.setCurrentText(chosen if chosen in wanted else "---")
      combo.blockSignals(False)

    if not lost:
      return
    # An element pointed at a column that is no longer there. Leaving
    # it would fail at the join, deep inside a run, with a message
    # about a missing column rather than about the user's own edit.
    #
    # It re-defaults to a surviving field rather than being unassigned,
    # and that is a settled decision rather than a convenience: losing
    # a column costs an element its VARIABLE, not its place on the map.
    # An element left unassigned draws as flat fill, so a deletion in
    # QGIS would quietly cost the map two of its four variables. The
    # preference is the same one _refresh_table uses -- numeric fields,
    # skipping the ones that are obviously row identifiers -- because
    # two rules for "which field would this element sensibly show"
    # would drift apart and then disagree in front of a user.
    fields = self._layer_fields()
    id_like = {"fid", "objectid", "id", "gid", "ogc_fid"}
    numeric = [f for f in fields if self._field_is_numeric(f)]
    preferred = [f for f in numeric if f.lower() not in id_like] \
        or numeric or fields
    moved = []
    for row in range(self.table.rowCount()):
      combo = self.table.cellWidget(row, 1)
      was = chosen_by_row.get(row)
      if combo is None or was not in lost:
        continue
      identifier = self.table.item(row, 0)
      now = preferred[row % len(preferred)] if preferred else "---"
      combo.blockSignals(True)
      combo.setCurrentText(now)
      combo.blockSignals(False)
      moved.append((was, now))
      # the hand-picked category colours belonged to the OLD field and
      # mean nothing for the new one; they are keyed by field, so the
      # element's other fields keep theirs
      if identifier is not None:
        self._category_colours.get(identifier.text(), {}).pop(was, None)
    if moved:
      gone = sorted({was for was, _ in moved})
      landed = sorted({now for _, now in moved if now != "---"})
      if landed:
        self._report_quietly(
          f"{', '.join(gone)} is no longer in the layer, so the "
          f"elements using it now show "
          f"{', '.join(landed)} instead.")
      else:
        self._report_quietly(
          f"{', '.join(gone)} is no longer in the layer, and there is "
          f"nothing left to show in its place.")

  def _auto_spacing(self):
    """Derive a coarse spacing from the layer extent (about fifteen
    repeating units across), rounded to a clean number. Degrees are
    scaled to rough metres because geographic layers get reprojected
    to Web Mercator before tiling."""
    from . import compat
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return
    if not compat.layer_data_is_available(layer):
      # extent() on a layer whose source has gone segfaults QGIS; see
      # compat.layer_data_is_available.
      self._report_quietly(
        "That layer's data is no longer available, so a spacing "
        "cannot be suggested.")
      return
    ext = layer.extent()
    dim = max(ext.width(), ext.height())
    if layer.crs().isGeographic():
      dim = dim * 111_000  # approximate metres, layer will be reprojected
    if math.isfinite(dim) and dim > 0:
      self.spacing_spin.setValue(_nice_number(dim / 15))
    else:
      # No usable extent: a layer with no CRS, or an empty one. Leave
      # the spacing alone rather than guessing from a bad number, and
      # say so, because the user pressed a button and is owed an
      # answer either way.
      self._report_quietly(
        "That layer has no usable extent, so a spacing cannot be "
        "suggested. Type a spacing instead.")

  def _layer_fields(self) -> list[str]:
    """Attribute (column) names of the region layer; ``fields()`` is
    QGIS's schema accessor, analogous to a GeoDataFrame's columns."""
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return []
    return [f.name() for f in layer.fields()]

  def _field_is_numeric(self, name: str) -> bool:
    """Whether a field holds numbers (drives the Quant/Categorized
    default in ``_plausible_mode``)."""
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return False
    idx = layer.fields().indexOf(name)
    return idx >= 0 and layer.fields().field(idx).isNumeric()

  # ---------------------------------------------------------------- preview

  def _queue_preview(self, *args):
    """Debounced funnel for DESIGN-tab changes: restart both countdowns
    (unit + table rebuild and preview repaint at 350 ms, live map
    regeneration at 900 ms). Signal payloads arrive in *args and are
    ignored.

    Data & colours widgets must NOT use this path: the rebuild it
    schedules replaces every table cell widget, and a rebuild landing
    350 ms after one palette pick destroys the chooser the user has
    open for the next one (the "race among choosers" this once
    caused). They use _refresh_preview_colours instead.
    """
    self._preview_timer.start()
    self._queue_live()

  def _refresh_preview_colours(self, *args):
    """Light path for Data & colours changes: repaint the preview with
    the current per-element colours and queue a live regeneration —
    without touching the unit or the table, whose widgets stay the
    same objects throughout (so open dropdowns and half-made picks
    survive)."""
    if self._unit is not None:
      self.preview.show_unit(self._unit, self._table_id_colours(),
                             self.shells_spin.value())
    self._queue_live()

  def _queue_live(self, *args):
    """Debounced funnel for output-affecting changes; also the choke
    point where the table's dynamic columns are kept coherent, since
    every relevant control change passes through here."""
    self._update_dynamic_columns()
    self._live_timer.start()

  def closeEvent(self, event):  # noqa: N802 (Qt API)
    """Qt calls this when the window closes; cancelling the task keeps
    a closed dialog from computing invisibly (the task's cancel path
    still reports once, resetting our state; see worker.py)."""
    if self._task is not None:
      try:
        self._task.cancel()
      except Exception:
        pass
    super().closeEvent(event)

  def showEvent(self, event):  # noqa: N802 (Qt API)
    """Qt calls this when the window (re)appears. Two duties: re-fit
    the height once real layout geometry exists, and recover from any
    zombie task (we believe a run is active but the task manager shows
    it dead), which otherwise blocks all future generations."""
    super().showEvent(event)
    QTimer.singleShot(0, self._fit_to_design)
    if self._task is not None:
      try:
        from . import compat
        alive = self._task.status() in compat.task_active_statuses()
      except Exception:
        alive = False
      if not alive:
        self._task = None
        self.generate_btn.setEnabled(True)
        self.progress.setVisible(False)

  def _maybe_live_generate(self):
    """Debounced auto-generation, including the very first map.

    Runs whenever it is safe and cheap: live update on, temporary-layer
    output only (regenerating a GeoPackage on every tweak would hammer
    the disk), not in keep-both-groups mode, no task in flight (then it
    just flags a rerun), a layer and at least one variable in place, a
    modest estimated tile count (the estimate uses the layer's extent
    directly to avoid building a GeoDataFrame just to decide), and
    settings actually different from the last completed run. The first
    render needs no button press; choosing a layer is enough.
    """
    self.live_note.setText("")
    if not self.live_check.isChecked():
      return
    if self.gpkg_widget.filePath().strip() or \
        self.opt_new_group.isChecked():
      return
    if self._task is not None:
      self._live_pending = True
      return
    layer = self.layer_combo.currentLayer()
    if layer is None or self._unit is None:
      return
    if not compat_layer_available(self, layer):
      # Same crash, reached from the live path -- and reachable long
      # before any of this session's changes: live update on, the file
      # deleted underneath, and QGIS is gone with no diagnostic.
      if not self._said_source_gone:
        self._said_source_gone = True
        self._report_quietly(
          "That layer's data is no longer available, so the map "
          "cannot be updated.")
      return
    if self._data_is_unobservable():
      # Live update works by noticing that something changed. This
      # layer will not say, so the only way to keep up would be to
      # re-tile on every tick -- which for a remote source means
      # fetching somebody's whole dataset over and over, unattended,
      # because a dialog happens to be open. Say so instead, once, and
      # leave Generate to do it when the user actually wants it.
      if not self._said_live_cannot_track:
        self._said_live_cannot_track = True
        self._report_quietly(
          "This layer does not report its size, so live update "
          "cannot follow it. Press Generate to redraw.")
      return
    if not any(a["var"] for a in self._assignments()):
      return
    ext = layer.extent()
    scale = 111_000 if layer.crs().isGeographic() else 1
    bounds = (ext.xMinimum() * scale, ext.yMinimum() * scale,
              ext.xMaximum() * scale, ext.yMaximum() * scale)
    est = bridge.estimate_tile_count_bounds(self._unit, bounds)
    if est > bridge.LIVE_UPDATE_MAX_TILES:
      self.live_note.setText(
        f"live update paused (about {est:,} tiles); press Generate")
      return
    if self._run_signature() == self._last_run_sig and \
        QgsProject.instance().layerTreeRoot().findGroup(
          self._group_name or "") is not None:
      return  # nothing changed since the last run
    if self._restyle_only():
      return  # only the colours changed: done already, no tiling
    self._generate(live=True)

  def _unit_kwargs(self) -> dict:
    """Collect the TileUnit/WeaveUnit constructor arguments from the
    Design controls. The CRS is the region layer's EPSG code where it
    has one (weavingspace expects an int or authority string); layers
    in geographic coordinates fall back to 3857, matching the
    reprojection applied in bridge.layer_to_gdf."""
    spec = self._current_spec()
    layer = self.layer_combo.currentLayer()
    crs = 3857
    if layer is not None and not layer.crs().isGeographic():
      authid = layer.crs().authid()
      if authid.upper().startswith("EPSG:"):
        crs = int(authid.split(":")[1])
      else:
        crs = authid
    return dict(
      spec=spec,
      spacing=self.spacing_spin.value(),
      crs=crs,
      offset=self.opt_offset.value(),
      offset_angle=self.opt_offset_angle.value(),
      point_angle=self.opt_point_angle.value(),
      aspect=self.opt_aspect.value(),
      over_under=self.opt_over_under.text() or None,
      nrows=self.opt_grid_rows.value(),
      ncols=self.opt_grid_cols.value(),
    )

  def _build_unit(self):
    """Construct the Tileable exactly as the web app does: catalogue
    spec plus options, then the modifier chain rotate -> scale -> skew
    -> insets (tilings inset tiles and prototile in % of spacing;
    weaves scale the tile inset by aspect and have no prototile
    inset). Pure weavingspace; no QGIS involved."""
    kwargs = self._unit_kwargs()
    spec = kwargs.pop("spec")
    if spec is None:
      return None
    unit = catalog.make_unit(spec, **kwargs)
    # Apply each modifier only when it actually changes something.
    # An identity transform is not free: weavingspace rebuilds the
    # geometry, and the sub-micron rounding that follows can flip
    # which region polygon a tile overlaps most, so a map with all
    # modifiers at their defaults would differ slightly from the same
    # design built without them. Skipping identities also spares the
    # work on every preview rebuild.
    if self.mod_rotate.value():
      unit = unit.transform_rotate(self.mod_rotate.value())
    if (self.mod_scale_x.value(), self.mod_scale_y.value()) != (1.0, 1.0) \
        or self.mod_glyph.isChecked():
      unit = unit.transform_scale(
        self.mod_scale_x.value(), self.mod_scale_y.value(),
        self.mod_glyph.isChecked())
    if self.mod_skew_x.value() or self.mod_skew_y.value():
      unit = unit.transform_skew(self.mod_skew_x.value(),
                                 self.mod_skew_y.value())
    spacing = self.spacing_spin.value()
    if spec["type"] == "tiling":
      if self.mod_t_inset.value():
        unit = unit.inset_tiles(self.mod_t_inset.value() * spacing / 100)
      if self.mod_p_inset.value():
        unit = unit.inset_prototile(
          self.mod_p_inset.value() * spacing / 100)
    elif self.mod_t_inset.value():
      # a weave's tile inset is scaled by strand width, or thin
      # strands would vanish at inset values a tiling shrugs off
      unit = unit.inset_tiles(
        self.mod_t_inset.value() * self.opt_aspect.value() * spacing / 100)
    return unit

  def _rebuild_unit(self):
    """Rebuild the unit and everything derived from it (assignment
    table rows, preview). Runs on the main thread; unit construction
    is fast enough for that (the expensive step is the tiling itself,
    which is what the background task exists for)."""
    try:
      self._unit = self._build_unit()
    except Exception as e:
      self._unit = None
      self.preview.show_message(f"Could not build tile unit:\n{e}")
      return
    if self._unit is None:
      self.preview.show_message("Pick a design to preview it.")
      return
    self._refresh_table()
    self.preview.show_unit(self._unit, self._table_id_colours(),
                           self.shells_spin.value())

  # ------------------------------------------------------------- data table

  def _tile_ids(self) -> list[str]:
    """Sorted distinct tile_id labels of the current unit ("a", "b",
    ...); one table row and one output layer per id."""
    if self._unit is None:
      return []
    try:
      return sorted(set(self._unit.tiles.tile_id))
    except Exception:
      return []

  # sentinel item-data values in the class-source combo: SHARED is a
  # legacy value from when a dialog-wide style file existed (still
  # mapped to automatic for old stored choices); BROWSE marks the
  # "Choose file..." entry that opens a file dialog
  SHARED, BROWSE = "__shared__", "__browse__"
  # qualitative colour sets cycled as defaults for categorized rows
  CAT_DEFAULT_RAMPS = ["tab10", "Set2", "Set1", "Pastel1", "Dark2", "Set3"]

  def _category_count(self, field_name: str) -> int:
    """Distinct non-null values in a field, shown (greyed) in the
    Classes cell of categorized rows. ``uniqueValues`` asks the layer's
    data provider, which may scan the table, hence the cache keyed by
    (layer id, field); the cache clears when the layer changes."""
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return 0
    idx = layer.fields().indexOf(field_name)
    if idx < 0:
      return 0
    key = (layer.id(), field_name)
    if key not in self._cat_count_cache:
      try:
        self._cat_count_cache[key] = len(
          {v for v in layer.uniqueValues(idx) if v is not None})
      except Exception:
        self._cat_count_cache[key] = 0
    return self._cat_count_cache[key]

  def _populate_class_source_combo(self, combo, current=None):
    """(Re)build a row's class-source choices.

    Args:
      combo: the combo to refill; the current selection is preserved
        when that choice still exists.
      current: a token to select instead, e.g. "file:/path.qml".

    Returns:
      None. The choices are: automatic colours, any
    QML browsed in any row this session (the pool in _browsed_qmls, so
    one file chosen once is offered to every categorized row), any
    loaded layer with categorized symbology, and a browse entry. The
    SHARED sentinel survives only as a legacy stored value from the
    since-removed dialog-wide style file box, mapped to automatic."""
    from qgis.core import QgsCategorizedSymbolRenderer
    if current is None:
      current = combo.currentData()
    if current == self.SHARED:  # legacy stored choice
      current = ""
    wanted = [("Automatic colours", "")]
    for path in self._browsed_qmls:
      wanted.append((os.path.basename(path), "file:" + path))
    for lyr in QgsProject.instance().mapLayers().values():
      try:
        if isinstance(lyr.renderer(), QgsCategorizedSymbolRenderer):
          wanted.append((f"Layer: {lyr.name()}", f"layer:{lyr.id()}"))
      except Exception:
        continue
    if current and current.startswith("file:") \
        and current not in [w[1] for w in wanted]:
      wanted.append((os.path.basename(current[5:]), current))
    wanted.append(("Choose file…", self.BROWSE))
    existing = [(combo.itemText(i), combo.itemData(i))
                for i in range(combo.count())]
    if existing != wanted:
      combo.blockSignals(True)
      combo.clear()
      for text, data in wanted:
        combo.addItem(text, data)
      combo.blockSignals(False)
    idx = combo.findData(current)
    if idx < 0:
      idx = 0
    if combo.currentIndex() != idx:
      combo.blockSignals(True)
      combo.setCurrentIndex(idx)
      combo.blockSignals(False)
    combo.setProperty("last_idx", combo.currentIndex())

  def _make_class_source_combo(self, prev_choice, tile_id=None):
    """One row's class-source dropdown.

    Args:
      prev_choice: the token to preselect, remembered per element in
        _class_choices.
      tile_id: the element this row carries; it rides on the widget
        via setProperty so the shared handlers know which element
        they are answering for.

    Returns:
      A combo, created only while that row is
    categorized (see _sync_row). ``setProperty`` stores arbitrary data
    on a Qt object; the tile_id rides along so the shared handlers know
    which element to record choices for. The ``activated`` handler
    intercepts the BROWSE entry to open a native file dialog, adds the
    chosen QML to the session-wide pool, and re-selects it; a cancelled
    dialog restores the previous selection."""
    combo = QComboBox()
    combo.setProperty("tile_id", tile_id)
    combo.setToolTip(
      "Where this element's class colours come from.")
    self._populate_class_source_combo(
      combo, prev_choice if prev_choice is not None else "")

    def activated(index):
      from qgis.PyQt.QtWidgets import QFileDialog
      if combo.itemData(index) == self.BROWSE:
        path, _filter = QFileDialog.getOpenFileName(
          self, "Class colours from a QGIS style file", "",
          "QGIS layer style (*.qml)")
        if path:
          if path not in self._browsed_qmls:
            self._browsed_qmls.append(path)
          self._populate_class_source_combo(combo, "file:" + path)
        else:
          combo.blockSignals(True)
          combo.setCurrentIndex(combo.property("last_idx") or 0)
          combo.blockSignals(False)
      combo.setProperty("last_idx", combo.currentIndex())
      tid = combo.property("tile_id")
      if tid:
        was = self._class_choices.get(tid)
        self._class_choices[tid] = combo.currentData()
        # importing a scheme is the same kind of act as choosing a
        # ramp: it names where this element's colours come from
        if combo.currentData() and combo.currentData() != was:
          self._clear_category_colours(tid, "an imported class source")
      self._queue_live()

    combo.activated.connect(activated)
    return combo

  def _make_reverse_box(self, tile_id, checked):
    """One row's Reverse checkbox, centred in its cell.

    Args:
      tile_id: the element the row belongs to, carried on the widget
        so the handler can record the choice against the element
        rather than the row (rows are rebuilt; elements persist).
      checked: its initial state, restored from _reverse_choices.

    Returns:
      A QWidget wrapper holding the switch. Qt centres a small widget
      in a table cell only if you put it in a layout, hence the
      wrapper; ``_row_reverse`` unwraps it again. The control is a
      sliding switch rather than a checkbox because that is what the
      same idea looks like in the browser tool these maps also come
      from, and because a row of switches reads as a set of states
      rather than a list of ticks.

    Toggling repaints the row's ramp swatch the other way round and
    goes through the light preview path, so it behaves like every
    other Data-tab control: no table rebuild, no chooser race.
    """
    holder = QWidget()
    layout = QHBoxLayout(holder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    box = ToggleSwitch()
    box.setProperty("tile_id", tile_id)
    box.setChecked(bool(checked))
    box.setToolTip("Run this element's ramp the other way round")
    layout.addWidget(box)

    def toggled(state, b=box):
      tid = b.property("tile_id")
      if tid:
        self._reverse_choices[tid] = b.isChecked()
      # the swatch should show what the map will do
      self._refresh_ramp_icons()
      self._refresh_preview_colours()

    box.toggled.connect(toggled)
    return holder

  def _make_opacity_spin(self, tile_id, value):
    """One row's opacity cell.

    Args:
      tile_id: the element it belongs to, carried on the widget so the
        handler records against the element rather than the row.
      value: 0-100, restored from _opacity_choices.

    Returns:
      A QSpinBox reading 0-100 with a "%" suffix, matching QGIS's own
      opacity control (100 is solid). A spin box rather than a slider:
      it is compact enough for a table that already carries seven
      columns, the numbers stay comparable down the column at a
      glance, and it steps rather than streaming, so each change costs
      one repaint. Dragging remains available in QGIS's own Layer
      Properties, which regeneration deliberately does not overwrite.
    """
    spin = QSpinBox()
    spin.setRange(0, 100)
    spin.setSingleStep(5)
    spin.setSuffix("%")
    spin.setProperty("tile_id", tile_id)
    spin.setValue(int(value))
    spin.setToolTip(
      "How solid this element draws, as QGIS layer opacity; "
      "100 is opaque.")

    def changed(_v, sp=spin):
      tid = sp.property("tile_id")
      if tid:
        self._opacity_choices[tid] = sp.value()
      self._refresh_preview_colours()

    spin.valueChanged.connect(changed)
    return spin

  def _row_opacity(self, row):
    """The opacity spin box for a row, or None mid-rebuild."""
    return self.table.cellWidget(row, 6)

  def _row_reverse(self, row):
    """The QCheckBox inside a row's Reverse cell, or None when that
    row has no ramp to reverse."""
    holder = self.table.cellWidget(row, 5)
    if holder is None:
      return None
    return holder.findChild(ToggleSwitch)

  def _refresh_ramp_icons(self):
    """Redraw each row's ramp swatch in its current direction.

    Only the icons change: the combo keeps its items, its index, and
    its identity, so a repaint here can never disturb a dropdown the
    user has open (the chooser-race rule).
    """
    for row in range(self.table.rowCount()):
      combo = self.table.cellWidget(row, 4)
      if combo is None or not hasattr(combo, "count"):
        continue
      box = self._row_reverse(row)
      reverse = bool(box is not None and box.isEnabled() and box.isChecked())
      for i in range(combo.count()):
        icon = _ramp_icon(combo.itemText(i), reverse)
        if icon is not None:
          combo.setItemIcon(i, icon)

  def _make_ramp_combo(self, tile_id, wanted):
    """One row's colour-ramp dropdown.

    Args:
      tile_id: the element the row belongs to; the pick is recorded
        against it in _ramp_choices, so it survives table rebuilds
        and the Single-colour swap.
      wanted: the ramp to preselect, if it still exists.

    Returns:
      A combo listing every ramp in the QGIS style library, each with
      a preview swatch drawn in its current direction.
    """
    ramp_combo = QComboBox()
    # without this the swatch drawn above is scaled down to the
    # platform's default icon size, and the ramp cannot be read
    ramp_combo.setIconSize(RAMP_SWATCH)
    ramp_combo.setProperty("tile_id", tile_id)
    for name in self._ramp_names:
      icon = _ramp_icon(name)
      if icon is not None:
        ramp_combo.addItem(icon, name)
      else:
        ramp_combo.addItem(name)
    if ramp_combo.findText(wanted) < 0:
      wanted = self._ramp_names[0] if self._ramp_names else ""
    ramp_combo.setCurrentText(wanted)

    def changed(_i, c=ramp_combo):
      tid = c.property("tile_id")
      if tid:
        self._ramp_choices[tid] = c.currentText()
        # a new ramp is a new source of truth for this element's
        # colours, so anything picked by hand goes with it
        self._clear_category_colours(tid, "a new colour ramp")
      self._refresh_preview_colours()

    ramp_combo.currentIndexChanged.connect(changed)
    return ramp_combo

  def _make_colour_button(self, tile_id, colour_hex):
    """The swatch-plus-picker button for Single colour rows.

    Args:
      tile_id: the element it belongs to, so the picked colour is
        remembered per element in _single_colours.
      colour_hex: the colour to start on.

    Returns:
      A QgsColorButton -- QGIS's native colour widget, so the picker
      here is the one users meet elsewhere in QGIS -- which replaces
      the ramp dropdown while the row is on Single colour.
    """
    button = QgsColorButton()
    button.setColor(QColor(colour_hex))
    button.setToolTip("Fill colour for this element")

    def changed(colour, tid=tile_id):
      self._single_colours[tid] = colour.name()
      self._refresh_preview_colours()

    button.colorChanged.connect(changed)
    return button

  def _row_widgets(self, row):
    """The seven per-row cell widgets, in column order: variable,
    style, classes, ramp-or-colour, reverse, opacity, class source.
    Any may be None mid-rebuild or by design (the class-source cell
    exists only on categorized rows, and the ramp cell may hold a
    QgsColorButton instead of a combo)."""
    return (self.table.cellWidget(row, 1), self.table.cellWidget(row, 2),
            self.table.cellWidget(row, 3), self.table.cellWidget(row, 4),
            self.table.cellWidget(row, 5),
            self.table.cellWidget(row, 6),
            self.table.cellWidget(row, 7))

  def _row_mode(self, row) -> str:
    """A row's style resolved to its renderer kind: every "Quant: X"
    entry collapses to "Graduated"; the break method itself is read
    separately in _assignments."""
    var_combo, mode_combo, *_rest = self._row_widgets(row)
    if mode_combo is None:
      return "Single colour"
    raw = mode_combo.currentText()
    return "Graduated" if raw in self.GRAD_SCHEMES else raw

  def _sync_row(self, row):
    """Keep a row's widgets coherent with its style: the Classes cell is
    editable only for Quant styles (categorized rows grey it out and
    show the detected category count), the ramp swaps between
    quantitative and categorical families, and the class-source cell
    exists only on categorized rows."""
    var_combo, mode_combo, k_spin, ramp_combo, reverse_holder, \
      opacity_spin, file_combo = self._row_widgets(row)
    if None in (var_combo, mode_combo, k_spin):
      return
    mode = self._row_mode(row)
    var = var_combo.currentText()
    var = None if var == "---" else var

    k_spin.blockSignals(True)
    if mode == "Graduated" and \
        mode_combo.currentText() == "Quant: Unclassed":
      # fixed class count: 50 linear steps stand in for a continuous
      # ramp, so the cell is informative rather than editable
      k_spin.setSpecialValueText("")
      k_spin.setRange(0, 9999)
      k_spin.setValue(50)
      k_spin.setEnabled(False)
    elif mode == "Graduated":
      # 2 to 20 classes. The web app offers no equivalent control at
      # all (it renders continuously, which is what Quant: Unclassed
      # reproduces here), so the ceiling is ours: 20 matches the app's
      # element-count slider and the largest categorical palettes,
      # which is about as many steps as a ramp can carry before the
      # classes stop reading as classes
      k_spin.setSpecialValueText("")
      k_spin.setRange(2, 20)
      k_spin.setValue(min(int(k_spin.property("user_k") or 5), 20))
      k_spin.setEnabled(True)
    elif mode == "Categorized" and var:
      n = self._category_count(var)
      k_spin.setSpecialValueText("")
      k_spin.setRange(0, 9999)
      k_spin.setValue(n)
      k_spin.setEnabled(False)
    else:
      k_spin.setRange(0, 9999)
      k_spin.setSpecialValueText("–")
      k_spin.setValue(0)
      k_spin.setEnabled(False)
    k_spin.blockSignals(False)

    id_item0 = self.table.item(row, 0)
    row_tid = id_item0.text() if id_item0 else None
    if mode == "Single colour":
      if not isinstance(ramp_combo, QgsColorButton) and row_tid:
        if ramp_combo is not None:
          self._ramp_choices[row_tid] = ramp_combo.currentText()
        start = self._single_colours.get(
          row_tid,
          bridge.ramp_swatch_colour(
            ramp_combo.currentText() if ramp_combo is not None
            else self._ramp_choices.get(row_tid, "Reds")))
        self._single_colours[row_tid] = start
        self.table.setCellWidget(
          row, 4, self._make_colour_button(row_tid, start))
      ramp_combo = None
    elif isinstance(ramp_combo, QgsColorButton) and row_tid:
      wanted = self._ramp_choices.get(
        row_tid, self.DEFAULT_RAMPS[row % len(self.DEFAULT_RAMPS)])
      ramp_combo = self._make_ramp_combo(row_tid, wanted)
      self.table.setCellWidget(row, 4, ramp_combo)
    # the Reverse cell: present on every row so the column reads
    # evenly, but enabled only where there is a ramp to reverse. On a
    # Single colour row it greys out AND clears, because a reversed
    # single colour means nothing and a stale tick would mislead
    tid_for_row = self.table.item(row, 0)
    row_id = tid_for_row.text() if tid_for_row else None
    has_ramp = ramp_combo is not None and not isinstance(
      ramp_combo, QgsColorButton)
    box = self._row_reverse(row)
    if box is None and row_id:
      self.table.setCellWidget(row, 5, self._make_reverse_box(
        row_id, self._reverse_choices.get(row_id, False)))
      box = self._row_reverse(row)
    if box is not None:
      box.blockSignals(True)
      box.setEnabled(has_ramp)
      box.setChecked(bool(has_ramp and row_id
                          and self._reverse_choices.get(row_id, False)))
      box.blockSignals(False)

    # opacity applies to every element, ramp or no ramp (a single
    # colour and even an unassigned no-data fill can be softened), so
    # unlike Reverse this cell is always present and always enabled
    if row_id and self._row_opacity(row) is None:
      self.table.setCellWidget(row, 6, self._make_opacity_spin(
        row_id, self._opacity_choices.get(row_id, 100)))

    if ramp_combo is not None:
      ramp = ramp_combo.currentText()
      is_cat_ramp = ramp in bridge.CATEGORICAL_RAMPS
      target = None
      if mode == "Categorized" and not is_cat_ramp:
        ramp_combo.setProperty("last_quant", ramp)
        target = (ramp_combo.property("last_cat")
                  or self.CAT_DEFAULT_RAMPS[
                    row % len(self.CAT_DEFAULT_RAMPS)])
      elif mode == "Graduated" and is_cat_ramp:
        ramp_combo.setProperty("last_cat", ramp)
        target = (ramp_combo.property("last_quant")
                  or self.DEFAULT_RAMPS[row % len(self.DEFAULT_RAMPS)])
      if target is not None and ramp_combo.findText(target) >= 0:
        ramp_combo.blockSignals(True)
        ramp_combo.setCurrentText(target)
        ramp_combo.blockSignals(False)
        if row_tid:
          self._ramp_choices[row_tid] = target

    show_file = mode == "Categorized" and bool(var) \
      and not self.table.isColumnHidden(7)
    id_item = self.table.item(row, 0)
    tid = id_item.text() if id_item else None
    if show_file:
      if file_combo is None:
        default = self._class_choices.get(tid, "")
        file_combo = self._make_class_source_combo(default, tid)
        self.table.setCellWidget(row, 7, file_combo)
      else:
        file_combo.setProperty("tile_id", tid)
        self._populate_class_source_combo(file_combo)
    elif file_combo is not None:
      if tid:
        self._class_choices[tid] = file_combo.currentData()
      self.table.removeCellWidget(row, 7)

    # The "Edit colours" button. Unlike the class source it is not
    # removed on non-categorical rows: a hole in the column would read
    # as a control that failed to appear, where a greyed button says
    # plainly that this element has no categories to colour.
    if not self.table.isColumnHidden(COL_EDIT_COLOURS):
      button = self.table.cellWidget(row, COL_EDIT_COLOURS)
      if button is None:
        # "Custom" rather than an ellipsis: the column heading says
        # what the button is for, but the button itself has to say
        # what it DOES, since a disabled ellipsis reads as a control
        # that is broken rather than one that does not apply here.
        button = QPushButton("Custom")
        button.clicked.connect(self._edit_category_colours)
        self.table.setCellWidget(row, COL_EDIT_COLOURS, button)
      button.setProperty("tile_id", tid)
      usable = mode == "Categorized" and bool(var)
      button.setEnabled(usable)
      button.setToolTip(
        "Choose a colour for each value this element takes"
        if usable else
        "Only elements with a categorized style have values to colour")
    elif self.table.cellWidget(row, COL_EDIT_COLOURS) is not None:
      self.table.removeCellWidget(row, COL_EDIT_COLOURS)

  def _update_dynamic_columns(self):
    """The Classes and Categ-colourmap-src columns exist only while
    they mean something, and every row's widgets are kept coherent."""
    rows = range(self.table.rowCount())
    modes = {}
    for row in rows:
      var_combo = self.table.cellWidget(row, 1)
      var = var_combo.currentText() if var_combo else "---"
      modes[row] = (self._row_mode(row), var not in ("", "---"))
    # the Classes column earns its place whenever ANY row has a class
    # count worth seeing — editable for graduated rows, greyed for
    # categorized ones, where it reports how many categories were
    # detected. Hiding it on an all-categorical map (as it once did)
    # took that count away exactly when it is most useful
    has_classes = any(m in ("Graduated", "Categorized") and has_var
                      for m, has_var in modes.values())
    self.table.setColumnHidden(3, not has_classes)
    # Reverse belongs beside the ramp, so it comes and goes with the
    # ramps: a map made entirely of single colours has nothing to
    # reverse and should not carry a column of dead checkboxes
    has_ramp_row = any(m in ("Graduated", "Categorized") and has_var
                       for m, has_var in modes.values())
    self.table.setColumnHidden(5, not has_ramp_row)
    has_categorical = any(m == "Categorized" and has_var
                          for m, has_var in modes.values())
    self.table.setColumnHidden(7, not has_categorical)
    # "Edit colours" only means anything where there are categories to
    # colour, so it appears on exactly the same condition as the class
    # source beside it. On rows that are not categorical the button
    # stays but is disabled (see _sync_row): a gap in the column would
    # read as a missing control rather than an inapplicable one.
    self.table.setColumnHidden(COL_EDIT_COLOURS, not has_categorical)
    for row in rows:
      self._sync_row(row)

  def _refresh_table(self):
    """Rebuild the assignment table for the current unit and layer.

    Rows are recreated from scratch (simplest correct behaviour when
    the element count changes), so all per-element choices that must
    survive live in dicts keyed by tile_id and are re-applied here:
    ``_assignments()`` is read *before* clearing to capture them.
    Defaults cycle the non-id-like numeric fields and the ramp list.
    Signal connections are made after initial values are set, so the
    setup itself does not fire handlers.
    """
    ids = self._tile_ids()
    fields = self._layer_fields()
    # fields that are almost certainly row identifiers rather than
    # data: mapping them produces a meaningless rainbow, so they are
    # skipped when picking each element's default variable (still
    # offered in the dropdown, since someone may genuinely want one)
    id_like = {"fid", "objectid", "id", "gid", "ogc_fid"}
    numeric = [f for f in fields if self._field_is_numeric(f)]
    preferred = [f for f in numeric if f.lower() not in id_like] or numeric
    previous = self._assignments()
    prev_by_id = {a["id"]: a for a in previous}
    self.table.setRowCount(len(ids))
    for row, tid in enumerate(ids):
      item = QTableWidgetItem(tid)
      item.setFlags(Qt.ItemFlag.ItemIsEnabled)
      self.table.setItem(row, 0, item)

      var_combo = QComboBox()
      var_combo.addItem("---")
      var_combo.addItems(fields)
      prev = prev_by_id.get(tid)
      if prev and prev["var"] in fields:
        var_combo.setCurrentText(prev["var"])
      elif prev is not None and prev["var"] is None:
        pass  # deliberately unassigned: leave it on "---". Cycling a
        # default back in here would undo the user's choice on every
        # design change, and their map would grow an element they had
        # switched off
      elif preferred:
        var_combo.setCurrentText(preferred[row % len(preferred)])
      var_combo.currentIndexChanged.connect(
        self._refresh_preview_colours)
      self.table.setCellWidget(row, 1, var_combo)

      mode_combo = QComboBox()
      mode_combo.addItems(self.MODES)
      mode_combo.setToolTip(
        "How this element is symbolized; adjustable later in the "
        "Layer Styling panel.")
      mode_combo.setCurrentText(self._plausible_mode(
        var_combo.currentText()))
      if prev and prev.get("mode_raw") in self.MODES \
          and prev.get("style_touched"):
        mode_combo.setCurrentText(prev["mode_raw"])
      mode_combo.setProperty(
        "touched", bool(prev and prev.get("style_touched")))
      mode_combo.activated.connect(
        lambda _i, c=mode_combo, v=var_combo: self._on_mode_chosen(c, v))
      mode_combo.currentIndexChanged.connect(
        self._refresh_preview_colours)
      self.table.setCellWidget(row, 2, mode_combo)
      var_combo.currentIndexChanged.connect(
        lambda _i, v=var_combo, m=mode_combo: self._follow_variable(v, m))

      k_spin = QSpinBox()
      # 2 to 20, the settled range, and the SAME range _sync_row sets.
      # This said (2, 12) while _sync_row said (2, 20): a restored
      # count above twelve was clamped by the setValue below, before
      # the wider range arrived. Nothing showed, because the real
      # value also rides on the user_k property and _sync_row restores
      # it from there — so the bug was invisible and waiting for
      # whoever reordered these two lines.
      k_spin.setRange(2, 20)
      k_spin.setValue(prev["k"] if prev and prev.get("k") else 5)
      k_spin.setProperty("user_k",
                         prev["k"] if prev and prev.get("k") else 5)
      k_spin.setToolTip(
        "Number of classes; categorized rows show how many "
        "categories were found.")

      def on_k(v, sp=k_spin):
        if sp.isEnabled():
          sp.setProperty("user_k", v)
          self._queue_live()

      k_spin.valueChanged.connect(on_k)
      self.table.setCellWidget(row, 3, k_spin)
      k_spin.setVisible(not self.table.isColumnHidden(3))

      default = self.DEFAULT_RAMPS[row % len(self.DEFAULT_RAMPS)]
      wanted = prev["ramp"] if prev and prev.get("ramp") else \
        self._ramp_choices.get(tid, default)
      self.table.setCellWidget(
        row, 4, self._make_ramp_combo(tid, wanted))
      if prev and prev.get("single_colour"):
        self._single_colours[tid] = prev["single_colour"]
      if prev is not None and "reverse" in prev:
        self._reverse_choices[tid] = prev["reverse"]
      if prev is not None and "opacity" in prev:
        self._opacity_choices[tid] = prev["opacity"]

      if prev and prev.get("class_choice") is not None:
        self._class_choices[tid] = prev["class_choice"]
    self._update_dynamic_columns()

  # ------------------------------------------------------------ assignments

  def _stamp_category_colours(self, layer, assignment):
    """Record an element's hand-picked colours on its output layer.

    Args:
      layer: the output layer for this element.
      assignment: its dict from ``_assignments()``.

    Returns:
      None. Writes a custom property QGIS saves inside the project
      file, or clears it when there is nothing to record, so a layer
      never carries stale choices from a previous assignment.

    JSON rather than a Python repr: a custom property is written into
    the .qgz as text, and this has to survive being read back by a
    future version without eval'ing whatever the file contains.
    """
    picked = assignment.get("category_colours")
    if picked:
      layer.setCustomProperty(
        "weavingspace_category_colours",
        json.dumps({"field": assignment["var"], "colours": picked},
                   sort_keys=True))
    else:
      layer.removeCustomProperty("weavingspace_category_colours")

  def _adopt_category_colours(self, layer, tile_id):
    """Read hand-picked colours back off an adopted output layer.

    Args:
      layer: an existing output layer found in the project.
      tile_id: the element it carries.

    Returns:
      None. Fills in this element's colours only where the dialog has
      none of its own, so a reopened project restores the user's work
      without overwriting anything chosen since.

    Anything unreadable is ignored rather than raised: a project file
    edited by hand, or written by a later version of the plugin, must
    not stop the dialog from opening.
    """
    raw = layer.customProperty("weavingspace_category_colours")
    if not raw:
      return
    try:
      stored = json.loads(raw)
      field = stored["field"]
      colours = {str(k): str(v) for k, v in stored["colours"].items()}
    except (ValueError, KeyError, TypeError, AttributeError):
      return
    if not field or not colours:
      return
    self._category_colours.setdefault(tile_id, {}).setdefault(
      field, dict(colours))

  def _clear_category_colours(self, tile_id, because):
    """Forget an element's hand-picked colours for its current field.

    Args:
      tile_id: the element.
      because: what the user just did, named in the notice ("a new
        colour ramp", "an imported class source").

    Returns:
      None. Says so when anything was actually discarded, and stays
      quiet otherwise.

    Choosing a ramp or importing a QML names a new source of truth for
    this element's colours, so the hand-picked ones go. That is the
    settled rule and it makes the ramp control mean what it says, but
    it does throw away deliberate work -- so it is not done silently.
    Only the CURRENT field is cleared: another variable's colours are
    still there if the element is switched back to it.
    """
    for_element = self._category_colours.get(tile_id)
    if not for_element:
      return
    var_combo = None
    for row in range(self.table.rowCount()):
      item = self.table.item(row, 0)
      if item is not None and item.text() == tile_id:
        var_combo = self.table.cellWidget(row, 1)
        break
    field = var_combo.currentText() if var_combo else None
    if not field or field == "---":
      return
    discarded = for_element.pop(field, None)
    if not discarded:
      return
    self._report_quietly(
      f"Choosing {because} for element '{tile_id}' discarded "
      f"{len(discarded)} colour(s) you had picked by hand for "
      f"'{field}'.")

  def _current_category_colours(self, assignment):
    """What each value of a categorical element draws in right now.

    Args:
      assignment: one dict from ``_assignments()``, already known to
        be Categorized with a variable.

    Returns:
      ({value: "#rrggbb"}, [values in class order]) with
      bridge.NO_DATA_KEY last for the catch-all, or (None, None) when
      the region layer or its field has gone.

    Built by asking bridge for the SAME renderer the map would get,
    against the region layer, and reading the colours back out of it.
    Re-deriving the sampling here instead would mean a second copy of
    a rule this project has already got wrong once -- an earlier
    hand-derivation used round() where matplotlib uses int(), and
    painted the middle category the wrong colour. One implementation
    means the editor cannot disagree with the map.
    """
    layer = self.layer_combo.currentLayer()
    if layer is None or assignment["var"] not in \
        [f.name() for f in layer.fields()]:
      return None, None
    template = self._template_for(assignment.get("class_source"))
    renderer = bridge.make_categorized_renderer(
      layer, assignment["var"], assignment["ramp"],
      assignment.get("outline", False), template,
      assignment.get("reverse", False),
      assignment.get("category_colours"))
    colours, order = {}, []
    for category in renderer.categories():
      value = category.value()
      key = bridge.NO_DATA_KEY if value is None else str(value)
      colours[key] = category.symbol().color().name()
      order.append(key)
    return colours, order

  def _template_for(self, token):
    """The imported class scheme for one class-source token, or None.

    Args:
      token: what the class-source combo holds ("file:…", "layer:…"
        or empty).

    Returns:
      {value: (symbol, label)} or None. A broken file yields None
      rather than raising: a class source that cannot be read should
      leave the element on automatic colours, not stop the user.
    """
    if not token:
      return None
    try:
      if token.startswith("layer:"):
        return bridge.template_from_layer(
          QgsProject.instance().mapLayer(token[6:]))
      return bridge.load_categorized_template(token[5:])
    except Exception:
      return None

  def _edit_category_colours(self):
    """Open the Categorical colour editor for the row that asked.

    Returns:
      None. Colours picked are recorded against the element AND the
      field, applied through the ordinary restyle path, and checked
      for separability once when the window closes.

    Nothing here touches a layer. A run finishing while the window is
    open replaces every element layer, so the editor works entirely
    on the dialog's own record and lets the restyle path find whatever
    layers currently exist -- which also means a colour picked during
    a run is simply applied when that run lands.
    """
    button = self.sender()
    if button is None:
      return
    tile_id = button.property("tile_id")
    assignment = next((a for a in self._assignments()
                       if a["id"] == tile_id), None)
    if assignment is None or assignment["mode"] != "Categorized" \
        or not assignment["var"]:
      return
    field = assignment["var"]
    colours, order = self._current_category_colours(assignment)
    if not order:
      self._report_quietly(
        f"'{field}' has no values to colour in this layer.")
      return

    def picked(value, colour):
      self._category_colours.setdefault(tile_id, {}) \
          .setdefault(field, {})[str(value)] = colour
      self._apply_style_change()

    editor = CategoryColourDialog(tile_id, field, order, colours,
                                  picked, self)
    editor.exec()
    self._warn_about_close_colours()

  def _apply_style_change(self):
    """Repaint after a symbology change, without re-tiling.

    Returns:
      None. Falls through quietly when there is nothing on the map
      yet, or a run is in flight -- in the latter case the change is
      already recorded and the finishing run will seed it.
    """
    self._refresh_preview_colours()
    self._restyle_only()

  def _warn_about_close_colours(self):
    """Say so if hand-picked colours left two elements inseparable.

    Returns:
      None. Reports at most one notice, on closing the editor rather
      than on each pick: a warning that fires while someone is still
      choosing is noise, and the question only has an answer once
      they have finished.
    """
    if not self.opt_colour_warnings.isChecked():
      # the same opt-in as the check after a run: a reader asked for
      # this opinion or they did not, and the editor is not a special
      # case
      return
    project = QgsProject.instance()
    fills = {}
    for tid, layer_id in self._element_layer_ids.items():
      layer = project.mapLayer(layer_id)
      if layer is None:
        continue                # deleted output: nothing to judge
      colours = bridge.renderer_fill_colours(layer)
      if colours:
        fills[tid] = colours
    if len(fills) < 2:
      return
    assignments = {a["id"]: a for a in self._assignments()}
    note = perception.clash_message(perception.clashes(
      fills,
      shared={tid: (assignments[tid].get("ramp"),
                    assignments[tid].get("reverse"),
                    assignments[tid].get("class_source"))
              for tid in fills if tid in assignments}))
    if note is not None:
      self._report_quietly(note)

  def _assignments(self) -> list[dict]:
    """Read the Data & colours table into plain dicts.

    The ONE crossing point between widget state and everything
    downstream: symbology seeding, run signatures, preview colours,
    and every test that wants to know what the dialog thinks. Nothing
    else should read the table's cells directly.

    Returns:
      A list with one dict per element, in table order. Keys:

      * ``id`` — the element's tile_id ("a", "b", ...)
      * ``var`` — the chosen field, or None when the row is on "---"
      * ``mode`` — resolved symbology: "Graduated", "Categorized" or
        "Single colour" (the dropdown's Quant: entries all resolve to
        "Graduated"; the scheme says which kind)
      * ``mode_raw`` — the literal dropdown text, for restoring the
        row after a rebuild
      * ``ramp``, ``single_colour`` — the colour choice, whichever
        kind the row carries
      * ``reverse`` — the Reverse box: run that element's ramp the
        other way. False whenever the row has no ramp to reverse
      * ``opacity`` — 0-100, applied as QGIS layer opacity (100 is
        solid). Kept apart from the colours, so it survives every
        change of ramp, scheme or class count
      * ``scheme`` — break method for graduated rows, including
        "Unclassed"
      * ``k`` — class count (50 and greyed for "Unclassed", the
        detected category count for categorized rows)
      * ``outline`` — draw tile boundaries
      * ``class_source`` — where a categorized row's colours come
        from: None for automatic, else a "file:<path>" or
        "layer:<id>" token
      * ``class_choice`` — the raw combo value, kept so the choice
        survives a table rebuild
      * ``style_touched`` — the user picked the style by hand, so it
        should stop following the field's type

    The dicts are snapshots, not live views: change one and nothing
    happens to the table.
    """
    result = []
    for row in range(self.table.rowCount()):
      id_item = self.table.item(row, 0)
      var_combo, mode_combo, k_spin, ramp_combo, reverse_holder, \
        opacity_spin, file_combo = self._row_widgets(row)
      reverse_box = self._row_reverse(row)
      if id_item is None or var_combo is None:
        continue
      var = var_combo.currentText()
      var = None if var == "---" else var
      mode_raw = (mode_combo.currentText() if mode_combo
                  else self._plausible_mode(var or "---"))
      scheme = "Quantiles"
      if mode_raw in self.GRAD_SCHEMES:
        mode = "Graduated"
        scheme = self.GRAD_SCHEMES[mode_raw]
      else:
        mode = mode_raw
      # A graduated renderer classifies NUMBERS, and over a text field
      # it comes back with no ranges at all, so every tile falls
      # outside every class and the layer draws as nothing. The
      # choosers are corrected as the user works (_on_mode_chosen,
      # _follow_variable), but this is the one place every consumer
      # reads -- the run, the restyle fast path, the signature, a
      # session restored from a saved project -- so the correction is
      # made here as well and cannot be got round.
      if mode == "Graduated" and var and not self._field_is_numeric(var):
        mode, mode_raw, scheme = "Categorized", "Categorized", "Quantiles"
      choice = (file_combo.currentData() if file_combo is not None
                else self._class_choices.get(
                  id_item.text() if id_item else "", ""))
      if not choice or choice in (self.BROWSE, self.SHARED):
        source = None
      else:
        source = choice  # "file:<path>" or "layer:<id>"
      k = 5
      if k_spin is not None:
        k = int(k_spin.property("user_k") or k_spin.value() or 5)
      if scheme == "Unclassed":
        k = 50  # fixed by definition of the style
      tid_text = id_item.text()
      if isinstance(ramp_combo, QgsColorButton):
        ramp_name = self._ramp_choices.get(tid_text, "Reds")
        single_colour = ramp_combo.color().name()
      else:
        ramp_name = (ramp_combo.currentText() if ramp_combo
                     else self._ramp_choices.get(tid_text, "Reds"))
        single_colour = self._single_colours.get(tid_text)
      result.append({
        "id": tid_text,
        "var": var,
        "mode": mode,
        "mode_raw": mode_raw,
        "ramp": ramp_name,
        "reverse": bool(reverse_box is not None
                        and reverse_box.isEnabled()
                        and reverse_box.isChecked()),
        "opacity": (opacity_spin.value() if opacity_spin is not None
                    else 100),
        "single_colour": single_colour,
        "scheme": scheme,
        "k": k,
        "outline": self.opt_tile_outlines.isChecked(),
        # the class source matters (and re-seeds) only when categorized
        "class_source": source if mode == "Categorized" else None,
        "class_choice": choice,
        # Colours chosen by hand for this element AND this field. A
        # different variable in the same element has its own set, so
        # switching away and back restores rather than discards.
        "category_colours": (
          self._category_colours.get(tid_text, {}).get(var)
          if mode == "Categorized" and var else None),
        "style_touched": bool(mode_combo is not None
                              and mode_combo.property("touched")),
      })
    return result

  def _plausible_mode(self, var_text: str) -> str:
    """The style a fresh element gets: quantile classes for numeric
    fields, categorized symbology for text, a flat fill for nothing."""
    if not var_text or var_text == "---":
      return "Single colour"
    return "Quant: Quantiles" if self._field_is_numeric(var_text) \
      else "Categorized"

  def _on_mode_chosen(self, mode_combo, var_combo):
    """React to the user picking an element's style by hand.

    Args:
      mode_combo: the style chooser just used. It is marked as
        touched, which is what stops the style following the field's
        type from then on.
      var_combo: the same row's variable chooser, read for the field
        the style would apply to.

    Returns:
      None. The style may be snapped back to Categorized, and the
      user told why.

    _follow_variable already covers one order: a style chosen, then
    the variable changed to text. This is the order it cannot see --
    the text field chosen FIRST, then a Quant: style picked on top of
    it. Nothing corrected that, so the chooser went on reading
    "Quant: Quantiles" while the map was drawn by a graduated
    renderer over words. Such a renderer has no ranges at all, every
    tile falls outside every class, and all of the element layers
    paint nothing whatever -- a run that reports success and produces
    an empty map.
    """
    mode_combo.setProperty("touched", True)
    var = var_combo.currentText()
    if mode_combo.currentText() in self.GRAD_SCHEMES and \
        var not in ("", "---") and not self._field_is_numeric(var):
      # blockSignals so the correction does not read as another user
      # choice; the preview refresh the signal would have done is
      # called directly instead.
      mode_combo.blockSignals(True)
      mode_combo.setCurrentText("Categorized")
      mode_combo.blockSignals(False)
      self._report_quietly(
        f"'{var}' holds text, so it is drawn as categories rather "
        f"than a range of values.")
      self._refresh_preview_colours()

  def _follow_variable(self, var_combo, mode_combo):
    """Keep a row's style in step with its variable.

    Args:
      var_combo: the row's variable chooser, just changed.
      mode_combo: the row's style chooser, which may be adjusted.

    Returns:
      None. Until the user picks a style themselves it follows the
      field's type; a hand-picked Quant: style still yields to
      Categorized when the variable stops being numeric, because the
      alternative is a graduated renderer on text.
    """
    var = var_combo.currentText()
    if not mode_combo.property("touched"):
      mode_combo.blockSignals(True)
      mode_combo.setCurrentText(self._plausible_mode(var))
      mode_combo.blockSignals(False)
      self._refresh_preview_colours()
    elif mode_combo.currentText() in self.GRAD_SCHEMES and \
        var not in ("", "---") and not self._field_is_numeric(var):
      mode_combo.blockSignals(True)
      mode_combo.setCurrentText("Categorized")
      mode_combo.blockSignals(False)
      self._refresh_preview_colours()

  PREVIEW_MIN_OPACITY = 40

  def _table_id_colours(self) -> dict:
    """Each element's representative colour for the preview, softened
    by its opacity.

    Returns:
      {tile_id: "#rrggbbaa"} — a swatch colour per element, carrying
      an alpha channel taken from the element's Opacity cell.

    The alpha is FLOORED at PREVIEW_MIN_OPACITY. The preview paints on
    a plain panel rather than over the map, so a very low value there
    would fade toward the panel's grey and take the tile-id labels
    with it, while telling the reader nothing true: on the map the
    element composites over whatever lies beneath it, not over this
    background. Showing the effect but keeping the design legible is
    the compromise the user chose.
    """
    from qgis.PyQt.QtGui import QColor
    colours = {}
    for a in self._assignments():
      if a["mode"] == "Single colour" and a.get("single_colour"):
        base = a["single_colour"]
      else:
        base = (bridge.ramp_swatch_colour(a["ramp"])
                if a["var"] else bridge.NO_DATA_FILL)
      opacity = max(self.PREVIEW_MIN_OPACITY, int(a.get("opacity", 100)))
      colour = QColor(base)
      colour.setAlpha(round(255 * opacity / 100))
      colours[a["id"]] = colour.name(QColor.NameFormat.HexArgb)
    return colours

  def _geometry_signature(self):
    """Everything that changes the TILES, as one comparable tuple.

    The dividing line that makes restyling cheap: family, spacing,
    modifiers, the map-option switches, the region layer, the output
    path, and which variables are mapped (they are joined onto the
    tiles while tiling, so a new variable does need new geometry).
    Absent from it: ramp, classification scheme, class count, single
    colour, class source, outline. Those change only how existing
    tiles are painted.

    Returns:
      A tuple to compare with the last run's. Equal means the tiles
      on screen are still the right tiles, and a style change can be
      answered by re-seeding renderers instead of tiling again.
    """
    layer = self.layer_combo.currentLayer()
    kwargs = self._unit_kwargs()
    kwargs.pop("spec", None)
    return (
      layer.id() if layer is not None else None,
      self.family_combo.currentText(), self.n_combo.currentData(),
      tuple(sorted(kwargs.items())),
      self.mod_rotate.value(), self.mod_scale_x.value(),
      self.mod_scale_y.value(), self.mod_skew_x.value(),
      self.mod_skew_y.value(), self.mod_p_inset.value(),
      self.mod_t_inset.value(), self.mod_glyph.isChecked(),
      self.opt_join_prototiles.isChecked(), self.opt_retain.isChecked(),
      self.opt_clip.isChecked(), self.opt_icons.isChecked(),
      self.opt_outlines.isChecked(),
      self.gpkg_widget.filePath().strip() or None,
      tuple(sorted(a["var"] for a in self._assignments() if a["var"])),
      # What the layer HOLDS, not merely which layer it is. Without
      # this, deleting half the features left every term here
      # identical, so the run was treated as a style-only change and
      # answered by re-seeding the renderers on tiles built from data
      # that no longer existed -- a map of deleted places, redrawn on
      # demand and never marked as out of date.
      self._layer_fingerprint(), self._data_version,
    )

  def _restyle_only(self) -> bool:
    """Answer a style change by re-seeding the existing layers.

    Laying out a tiling is the expensive step, and a ramp or class
    count has nothing to do with it: the tiles on screen are already
    the right tiles. So when only symbology changed, this repaints
    them in place — no worker thread, no task, no flicker, and no
    waiting.

    Returns:
      True when the map was restyled here and no tiling is needed;
      False when the caller must do a full run (different geometry,
      nothing generated yet, or the layers have since been deleted).
    """
    project = QgsProject.instance()
    if self._last_geometry_sig is None or self._task is not None:
      return False
    if self.opt_new_group.isChecked():
      # "Create as new group" asks for a SECOND result to compare
      # against, which repainting the first one cannot provide, even
      # though nothing about the geometry changed
      return False
    if self._data_is_unobservable():
      # A layer that will not say how many features it has may have
      # been rewritten on a server since the last run, with nothing
      # locally to show for it. The fingerprint cannot see that, so
      # the fast path would repaint tiles built from data that is no
      # longer there. The user pressed Generate: re-tile, and let the
      # cost be the price of an answer that is actually current.
      return False
    if self._geometry_signature() != self._last_geometry_sig:
      return False
    if not self._element_layer_ids:
      return False
    layers = {tid: project.mapLayer(lid)
              for tid, lid in self._element_layer_ids.items()}
    if any(layer is None for layer in layers.values()):
      return False  # the user deleted the output; a full run rebuilds it
    assignments = {a["id"]: a for a in self._assignments()}
    if set(assignments) != set(layers):
      return False

    # class sources are loaded once per distinct token, as a full run
    # does; a broken file simply leaves that element on automatic
    # colours rather than stopping the restyle
    templates = {}
    for token in {a.get("class_source") for a in assignments.values()
                  if a.get("class_source")}:
      try:
        templates[token] = (
          bridge.template_from_layer(project.mapLayer(token[6:]))
          if token.startswith("layer:")
          else bridge.load_categorized_template(token[5:]))
      except Exception:
        templates[token] = None

    changed = []
    for tid, layer in layers.items():
      a = assignments[tid]
      signature = self._signature(a)
      if self._last_signatures.get(tid) == signature:
        continue  # this element is already wearing what it should
      bridge.seed_renderer(layer, a, templates.get(a.get("class_source")))
      # this element changed in the dialog, so its opacity is ours to
      # set; an element whose signature matched is skipped entirely
      # above, which is what leaves a hand-set opacity alone
      layer.setOpacity(max(0, min(100, a.get("opacity", 100))) / 100.0)
      # the fast path re-seeds without going through _add_output_layers,
      # so it has to record the hand-picked colours itself or a colour
      # chosen here would be missing from a project saved afterwards
      self._stamp_category_colours(layer, a)
      if self._last_path:
        # a GeoPackage carries its own cartography, so the file has to
        # learn about the change too
        bridge.embed_style(layer)
      layer.setName(f"{tid} – {a['var']}" if a["var"]
                    else f"{tid} (no data)")
      self._last_signatures[tid] = signature
      changed.append(tid)

    if changed and self.iface is not None:
      self.iface.messageBar().pushSuccess(
        "WeavingSpace",
        f"restyled {', '.join(changed)} (no re-tiling needed)")
    self._last_run_sig = self._run_signature()
    return True

  def _run_signature(self):
    """Everything that affects the output, as one comparable tuple;
    live update skips regenerating when this equals the last run's
    (reopening the dialog, for instance, changes nothing)."""
    layer = self.layer_combo.currentLayer()
    kwargs = self._unit_kwargs()
    kwargs.pop("spec", None)
    return (
      layer.id() if layer is not None else None,
      self.family_combo.currentText(), self.n_combo.currentData(),
      tuple(sorted(kwargs.items())),
      self.mod_rotate.value(), self.mod_scale_x.value(),
      self.mod_scale_y.value(), self.mod_skew_x.value(),
      self.mod_skew_y.value(), self.mod_p_inset.value(),
      self.mod_t_inset.value(), self.mod_glyph.isChecked(),
      self.opt_join_prototiles.isChecked(), self.opt_retain.isChecked(),
      self.opt_clip.isChecked(), self.opt_icons.isChecked(),
      self.opt_outlines.isChecked(),
      self.gpkg_widget.filePath().strip() or None,
      tuple((a["id"], a["var"], a["mode"], a["ramp"], a["scheme"],
             a["k"], a["outline"], a["class_source"],
             a.get("single_colour"), a.get("reverse", False),
             a.get("opacity", 100))
            for a in self._assignments()),
      # See _geometry_signature: live update compares this tuple to
      # decide a run would be a no-op, and an edit to the layer must
      # not look like one.
      self._layer_fingerprint(), self._data_version,
    )

  @staticmethod
  def _signature(a: dict) -> tuple:
    """The settings that decide one element's symbology.

    Args:
      a: one dict from ``_assignments()``.

    Returns:
      A tuple usable as a dictionary key. Regeneration compares it
      with the value stored from the previous run: unchanged means
      the element keeps the renderer it already has, so a style
      refined by hand in QGIS's styling dock survives; changed means
      it is re-seeded from the dialog.

    Note what is absent — spacing, family, modifiers. Those alter the
    GEOMETRY, not what the colours mean, so a design change should
    not throw away the user's styling work.
    """
    # Hand-picked category colours belong here for the same reason
    # the ramp does: they decide what this element looks like, and
    # _restyle_only re-seeds exactly the elements whose signature
    # moved. Sorted into a tuple because a dict is unhashable and
    # because two identical sets of choices must compare equal
    # whatever order they were picked in.
    picked = a.get("category_colours") or {}
    return (a["var"], a["mode"], a["ramp"], a["scheme"], a["k"],
            a["outline"], a.get("class_source"), a.get("single_colour"),
            a.get("reverse", False), a.get("opacity", 100),
            tuple(sorted(picked.items())))

  # ---------------------------------------------------------------- generate

  def _generate(self, live: bool = False):
    """Validate, guard, and launch one tiling run as a background task,
    unless the change was only ever about colour.

    ``live=True`` marks automatic (debounced) runs: they fail silently
    where a button press would pop a message box, and they skip the
    are-you-sure confirmation. The path from here: build a CRS-less
    copy of the inputs, run weavingspace's Tiling in the task's worker
    thread, then ``done`` reattaches the CRS and hands the result to
    ``_on_generated`` on the main thread. ``done`` also reports the
    run's coverage: how many areas of the region the pattern missed
    entirely, which is a fact about the map rather than a fault, and
    goes to the message bar rather than a dialog.
    """
    if self._task is not None:
      self._live_pending = True  # one run at a time; rerun when done
      return
    if not live and self._restyle_only():
      return  # the button pressed after a style change: instant
    layer = self.layer_combo.currentLayer()
    if layer is None:
      if not live:
        QMessageBox.warning(self, "WeavingSpace", "Choose a region layer.")
      return
    if self._preview_timer.isActive():
      # A design change schedules the unit rebuild 350 ms later, so a
      # Generate pressed inside that window would tile the PREVIOUS
      # design (an integration test comparing the output against a
      # direct library call caught this). Flush the pending rebuild
      # first: the settings on screen are what the user asked for.
      self._preview_timer.stop()
      self._rebuild_unit()
    if self._unit is None:
      self._rebuild_unit()
    if self._unit is None:
      if not live:
        QMessageBox.warning(self, "WeavingSpace",
                            "The tile unit could not be built.")
      return
    assignments = self._assignments()
    if not any(a["var"] for a in assignments):
      if not live:
        QMessageBox.warning(
          self, "WeavingSpace",
          "Assign at least one variable in the Data & colours tab.")
      return

    path_now = self.gpkg_widget.filePath().strip() or None
    if not live and self.opt_new_group.isChecked() and path_now \
        and path_now == self._last_path:
      QMessageBox.warning(
        self, "WeavingSpace",
        "You asked to keep the previous result as its own group, but "
        "writing to the same GeoPackage would overwrite its data. "
        "Choose a different file for this run.")
      return

    from . import compat
    if not compat.layer_data_is_available(layer):
      # Reading from a layer whose source has gone is not merely an
      # error: extent() alone segfaults QGIS. Refuse while there is
      # still a plugin here to refuse with.
      if not live:
        QMessageBox.critical(
          self, "WeavingSpace",
          "That layer's data is no longer available. Reload it in "
          "QGIS, or choose another layer.")
      return

    fields = sorted({a["var"] for a in assignments if a["var"]})
    try:
      region = bridge.layer_to_gdf(layer, fields)
    except Exception as e:
      QMessageBox.critical(self, "WeavingSpace", str(e))
      return

    # ---- size guard: small spacing on a big extent segfaults QGIS by
    # exhausting memory inside GEOS, so refuse pathological requests
    # the guards, in order of severity. The estimate is deliberately
    # cheap and slightly generous: refusing a map that would have
    # worked is a nuisance, but attempting one that exhausts memory
    # inside GEOS takes QGIS down with it
    est = bridge.estimate_tile_count(self._unit, region)
    if est > bridge.MAX_TILES_HARD:
      if not live:
        suggestion = bridge.min_reasonable_spacing(
          self._unit, region, self.spacing_spin.value())
        QMessageBox.critical(
          self, "WeavingSpace",
          f"A spacing this small asks for roughly {est:,} tiles. For this "
          f"layer a spacing of about {suggestion:,.0f} map units or more will "
          f"work.")
      return
    if not live and est > bridge.MAX_TILES_CONFIRM:
      answer = QMessageBox.question(
        self, "WeavingSpace",
        f"This will generate roughly {est:,} tiles and may take a "
        "while. Continue?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
      if answer != QMessageBox.StandardButton.Yes:
        return

    # CRITICAL: the worker thread must never touch pyproj/PROJ. QGIS uses
    # the same PROJ library from the main thread, and concurrent use
    # segfaults the whole application (this was the intermittent crash on
    # spacing changes). The tiling is pure geometry, so strip CRS from
    # everything the worker sees and reattach it on the main thread after.
    import copy
    result_crs = region.crs
    region = region.copy()
    region.crs = None
    unit = copy.deepcopy(self._unit)
    unit.crs = None
    for attr in ("tiles", "prototile", "regularised_prototile"):
      part = getattr(unit, attr, None)
      if part is not None:
        part.crs = None

    # Trace each tile back to the area it took its data from. The
    # column goes on the worker's copy of the region, travels with the
    # library's own attribute join onto the tiles, and comes off again
    # inside the worker, so nothing downstream ever sees it. This is
    # what makes the coverage count below a set difference over one
    # integer column rather than a second spatial pass.
    unit_id_column = bridge.add_unit_ids(region)
    unit_count = len(region)
    # Written on the worker thread, read on the main thread in done().
    # Safe without a lock: QGIS delivers finished() as a queued signal
    # after run() has returned, so the write happens-before the read
    coverage = {"missing": None}

    as_icons = self.opt_icons.isChecked()
    join_proto = self.opt_join_prototiles.isChecked()
    retain = self.opt_retain.isChecked()
    ragged = not self.opt_clip.isChecked()

    def work(task):
      from weavingspace import Tiling
      task.setProgress(5)
      tiling = Tiling(unit, region, as_icons=as_icons)
      if task.isCanceled():
        return None
      task.setProgress(40)
      tm = tiling.get_tiled_map(
        join_on_prototiles=join_proto,
        retain_tileables=retain,
        ragged_edges=ragged)
      task.setProgress(90)
      # Count here, where the tiled frame is already in memory and
      # still carries the tracing column; the same call strips the
      # column off again. Measured at 1% of the run on the packaged
      # Auckland data (tools/measure_coverage_warning.py)
      coverage["missing"] = bridge.count_units_without_tiles(
        tm.map, unit_id_column, unit_count)
      return None if task.isCanceled() else tm.map

    self.generate_btn.setEnabled(False)
    self.progress.setVisible(True)
    self.progress.setRange(0, 100)

    family = self.family_combo.currentText()
    path = path_now
    # Snapshot the signatures NOW, alongside the assignments, because
    # they describe what THIS run is about to draw. Recording them on
    # completion instead reads the table as it stands then, which may
    # already carry a change the user made while the tiling ran: the
    # map would be drawn with the old settings while the dialog
    # believed it matched the new ones, and every later check —
    # including live update's "has anything changed?" — would agree
    # that nothing needed doing. That is how a ramp picked mid-run
    # went missing.
    run_sig = self._run_signature()
    geometry_sig = self._geometry_signature()
    # Snapshotted for the same reason: the coverage notice names the
    # spacing THIS map was tiled at, and the user is free to type a
    # different one while it runs. map_unit_label reads the layer, so
    # it also has to happen here on the main thread
    spacing_used = self.spacing_spin.value()
    unit_label = bridge.map_unit_label(layer)

    def done(gdf, error):
      if gdf is not None and result_crs is not None:
        gdf.crs = result_crs  # reattach on the main thread (pyproj-safe)
      self._on_generated(gdf, error, family, layer, assignments, path,
                         run_sig, geometry_sig, live)
      # The coverage notice goes out AFTER _on_generated, never inside
      # it: that method's finally clears live_note, which is where
      # _report_quietly writes when there is no QGIS window (headless
      # runs, the test harness), so a notice pushed earlier would be
      # wiped a moment later. A run that failed, was cancelled, or
      # produced nothing at all has already said so more loudly
      if error is None and gdf is not None and len(gdf) > 0:
        note = bridge.coverage_message(coverage["missing"], unit_count,
                                       spacing_used, unit_label)
        if note is not None:
          self._report_quietly(note)
        # And whether any categorical field's class count moved since
        # the last run: if it did, the colours of the classes that
        # were already there have moved with it. Counted from the
        # frame in hand, which already holds the values that were
        # mapped, so this costs a nunique() per categorical element
        # and no second pass over the data.
        note = getattr(self, "_pending_colour_note", None)
        if note is not None:
          self._report_quietly(note)
          self._pending_colour_note = None
        # A column that turned out to hold one value everywhere. The
        # renderer has already collapsed to a single class (see
        # bridge.make_graduated_renderer); this is the half of it the
        # user can read. Taken from the frame just mapped rather than
        # from the layer, which is where the values actually went, and
        # deduplicated because several elements may share one field.
        said_constant = set()
        for assignment in assignments:
          field = assignment.get("var")
          if not field or assignment.get("mode") != "Graduated":
            continue
          if field in said_constant or field not in gdf.columns:
            continue
          if bridge.numeric_values_are_constant(gdf[field]):
            said_constant.add(field)
            self._report_quietly(bridge.constant_field_message(field))
          # Gaps in the column, counted from the frame just mapped.
          # The breaks already exclude them (see
          # bridge.make_graduated_renderer); this is the half the
          # user can read, and it is what gives them a chance of
          # understanding if QGIS's own Classify button later moves
          # every break by counting the nulls as zero.
          missing = int(gdf[field].isna().sum())
          note = bridge.missing_values_message(
            field, missing, int(len(gdf)))
          if note is not None:
            said_constant.add(field)
            self._report_quietly(note)
        for assignment in assignments:
          field = assignment.get("var")
          if not field or assignment.get("mode") != "Categorized":
            continue
          if field not in gdf.columns:
            continue
          current = int(gdf[field].nunique(dropna=True))
          shift = bridge.categorical_shift_message(
            field, self._category_counts.get(field), current)
          self._category_counts[field] = current
          if shift is not None:
            self._report_quietly(shift)

    self._task = TilingTask(
      f"WeavingSpace: tiling with {family}", work, done)

    def on_progress(p):
      self.progress.setValue(int(p))
      if p < 40:
        self.progress.setFormat("laying out the tiling… %p%")
      elif p < 90:
        self.progress.setFormat("joining data to tiles… %p%")
      else:
        self.progress.setFormat("adding layers… %p%")

    self._task.progressChanged.connect(on_progress)
    QgsApplication.taskManager().addTask(self._task)

  # ------------------------------------------------- output layer management

  def _retire_previous_instance(self):
    """Shut down any dialog left over from before this one.

    Called from __init__, so by the time a new dialog finishes
    constructing it is the only live one. The predecessor gets the
    same treatment as closing it by hand: its debounce timers stop,
    a tiling in flight is cancelled, and it hides. Its widgets are
    left intact rather than deleted, because Qt may still deliver
    queued signals to them and a deleted C++ object would take QGIS
    down with it.

    Returns:
      None. ``_LIVE_DIALOG`` is left pointing at this dialog.
    """
    global _LIVE_DIALOG
    previous = _LIVE_DIALOG
    if previous is not None and previous is not self:
      try:
        previous._live_timer.stop()
        previous._preview_timer.stop()
        previous.live_check.setChecked(False)
        if previous._task is not None:
          previous._task.cancel()
          previous._task = None
        previous.hide()
      except RuntimeError:
        # the Qt object is already gone; nothing to retire
        pass
    _LIVE_DIALOG = self

  def _adopt_existing_group(self):
    """Take over the output group this project already has, if any.

    Group tracking lives on the dialog instance, so without this a
    dialog opened later in a QGIS session (the plugin closed and
    reopened, which users do constantly) would find its default group
    name taken and quietly start "WeavingSpace tiles 2", leaving the
    first group behind with stale layers. That contradicts the
    settled design, where Generate replaces the previous result in
    place and "Create as new group" is the only route to a second
    one. Output layers carry their element id in a custom property,
    so adoption is exact rather than name-guessing.

    ``_last_signatures`` is deliberately left empty: the dialog cannot
    know which assignments produced the adopted layers, so the next
    run re-seeds their symbology rather than preserving hand styling
    it cannot vouch for. Within a session, hand styling still
    survives as before.
    """
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(GROUP_BASE_NAME)
    if group is None:
      return
    project = QgsProject.instance()
    for child in group.children():
      layer = child.layer() if hasattr(child, "layer") else None
      if layer is None or project.mapLayer(layer.id()) is None:
        continue
      tid = layer.customProperty("weavingspace_tile_id")
      if tid:
        self._element_layer_ids[str(tid)] = layer.id()
        # a project saved with hand-picked colours brings them back
        self._adopt_category_colours(layer, str(tid))
      elif layer.customProperty("weavingspace_outline"):
        self._outline_layer_id = layer.id()
    if self._element_layer_ids or self._outline_layer_id:
      self._group_name = GROUP_BASE_NAME

  def _get_or_make_group(self, force_new: bool):
    """Return (layer-tree group, created?) for this run's output.

    Reuses the group from the previous run unless forced (user asked
    for a new group, or the output path changed) or the user deleted
    it; a new group gets the first free "WeavingSpace tiles N" name and
    resets all per-run tracking. ``insertGroup(0, ...)`` puts it at the
    top of the layers panel.
    """
    root = QgsProject.instance().layerTreeRoot()
    if not force_new and self._group_name:
      group = root.findGroup(self._group_name)
      if group is not None:
        return group, False
    name = GROUP_BASE_NAME
    i = 1
    while root.findGroup(name) is not None:
      i += 1
      name = f"{GROUP_BASE_NAME} {i}"
    self._group_name = name
    self._element_layer_ids = {}
    self._outline_layer_id = None
    self._last_signatures = {}
    return root.insertGroup(0, name), True

  def _on_generated(self, gdf, error, family, source_layer, assignments,
                    path, run_sig=None, geometry_sig=None, live=False):
    """Main-thread completion handler for every run, successful or not.

    Args:
      gdf: the tiled GeoDataFrame, or None when the run failed or was
        cancelled.
      error: the exception raised in the worker, or None.
      family: the design's display name, for messages.
      source_layer: the region layer that was tiled.
      assignments: the table snapshot taken when the run STARTED, so
        symbology always matches the geometry it was computed with.
      path: the GeoPackage being written, or None.
      run_sig, geometry_sig: what this run drew, captured at launch.
        Recording them here instead would read the table as it stands
        NOW, which may already carry a change made while the tiling
        ran -- and the dialog would then believe the map matches
        settings it never used.

    Returns:
      None; the project gains the layers, and the dialog returns to
      an idle state via _finish_run.

    Sorts cancellation (both None: reset quietly), failure (shown
    with the worker's exception), empty output, and success (layers
    added by ``_add_output_layers``; its own failures are caught so an
    output-side bug cannot wedge the dialog either).

    ORDER MATTERS, and an earlier version got it wrong. The running
    state is cleared and any queued live rerun started only in the
    ``finally`` at the end, AFTER the layers exist. Building output is
    main-thread work — a layer per element, renderer seeding, possibly
    a GeoPackage write — and on a big map it takes noticeably longer
    than the tiling did. Clearing the state first let a queued live
    run launch a second task while the first was still materializing:
    tasks piled up in QGIS's task manager, and because the progress
    bar had already been hidden the last thing the user saw was the
    worker's "5%", which reads as a hang.
    """
    if gdf is None and error is None:
      self._finish_run()
      return  # cancelled: reset quietly
    if error is not None:
      self._finish_run()
      if isinstance(error, MemoryError):
        message = ("Ran out of memory while tiling; a larger spacing "
                   "will work for this layer.")
      else:
        message = "Tiling failed:\n\n" + "".join(
          traceback.format_exception_only(type(error), error))
      if live:
        self._report_quietly(message.replace("\n\n", " "))
      else:
        QMessageBox.critical(self, "WeavingSpace", message)
      return
    if gdf is None or len(gdf) == 0:
      self._finish_run()
      QMessageBox.warning(self, "WeavingSpace",
                          "The tiling produced no tiles.")
      return
    # the output phase: keep the progress bar up, in its indefinite
    # (busy) form, and say what is happening. This is the part that
    # used to look like a hang
    self.progress.setRange(0, 0)
    self.live_note.setText(f"Adding {len(gdf):,} tiles to the map...")
    QApplication.processEvents()  # let that text actually paint
    try:
      self._add_output_layers(gdf, family, source_layer, assignments,
                              path, run_sig, geometry_sig)
    except Exception as e:
      # The commonest way to land here is the user deleting the region
      # layer while the tiling ran: the result is fine, but there is
      # nothing left to attach it to. That is not an error to stop the
      # world with -- it is a thing the user just did on purpose -- so
      # it goes to the message bar, where QGIS puts everything else of
      # that kind. A modal box here also hangs any headless run,
      # because offscreen nobody can dismiss it.
      if not self._source_layer_alive(source_layer):
        self._report_quietly(
          "The region layer was removed while the map was being made, "
          "so there was nothing to add it to.")
      elif live:
        self._report_quietly(
          "Could not add the result layers: " + "".join(
            traceback.format_exception_only(type(e), e)).strip())
      else:
        QMessageBox.critical(
          self, "WeavingSpace",
          "Could not add the result layers:\n" + "".join(
            traceback.format_exception_only(type(e), e)))
    finally:
      self.live_note.setText("")
      self._finish_run()

  def _source_layer_alive(self, source_layer) -> bool:
    """Is the region layer this run tiled still in the project?

    Args:
      source_layer: the layer handed to the run when it started.

    Returns:
      True when it is still registered. A layer the user deleted
      mid-run leaves a Python wrapper whose C++ object is gone, so
      touching it raises RuntimeError rather than returning None --
      hence the try.
    """
    if source_layer is None:
      return False
    try:
      return QgsProject.instance().mapLayer(source_layer.id()) is not None
    except RuntimeError:
      return False

  def _report_quietly(self, message: str) -> None:
    """Tell the user something without stopping them.

    Args:
      message: one sentence for QGIS's message bar.

    Returns:
      None. Falls back to the dialog's own note line when there is no
      iface (which is how the tests run), so nothing is ever lost
      just because there is no QGIS window.

    One run can produce three notices at once -- areas left out at
    this spacing, categories whose colours moved, and element colours
    a reader cannot separate. QGIS's message bar stacks them, so a
    user sees all three; a QLabel holds one string, so the fallback
    used to keep only the last and silently drop the rest. That made
    the promise above false exactly when several things were wrong at
    once, which is when a reader most needs to be told. Notices are
    therefore JOINED rather than replaced.
    """
    if self.iface is not None:
      self.iface.messageBar().pushWarning("WeavingSpace", message)
      return
    existing = self.live_note.text()
    # a repeat within one run says nothing new, and stacking it would
    # push the earlier notices out of sight
    if message in existing.split(NOTE_SEPARATOR):
      return
    self.live_note.setText(
      f"{existing}{NOTE_SEPARATOR}{message}" if existing else message)

  def _finish_run(self):
    """End of a run, however it ended: re-enable Generate, hide the
    progress bar, forget the task, and only THEN start any live rerun
    that was queued while we were busy. Called from exactly one place
    per outcome so a run can never be left half-finished."""
    self.generate_btn.setEnabled(True)
    self.progress.setVisible(False)
    self.progress.setRange(0, 100)
    self._task = None
    if self._live_pending:
      self._live_pending = False
      self._live_timer.start()

  def _add_output_layers(self, gdf, family, source_layer, assignments,
                         path, run_sig=None, geometry_sig=None):
    """Turn the tiled GeoDataFrame into the project's output layers.

    Args:
      gdf: the worker's result, CRS already reattached on the main
        thread. One row per tile, with a ``tile_id`` column and the
        mapped variables joined on.
      family: the design's display name, used in the layer-group's
        message and the status note.
      source_layer: the region layer that was tiled; the optional
        outlines layer is made from it.
      assignments: the ``_assignments()`` snapshot taken BEFORE the
        run began, so fiddling with the table during a long tiling
        cannot leave the symbology disagreeing with the geometry.
      path: a GeoPackage path, or None for temporary layers. With a
        path, each element is written into the file, the file-backed
        layer replaces the memory one, and the style is embedded so
        the file carries its own cartography.

    Returns:
      None; the project is what changes. Afterwards
      ``_element_layer_ids`` maps element ids to layer ids and
      ``_last_signatures`` records what each element was seeded from,
      which is what lets the NEXT run re-seed only what changed.

    Steps, in order and why the order matters:
    1. find or create the layer-tree group;
    2. load each distinct class-source (QML file or donor layer) once;
    3. clone the previous run's renderers *before* touching any layer,
       so hand-refined symbology can be carried onto the replacements;
    4. when writing a GeoPackage, drop the old file-backed layers first
       (open layers hold the sqlite file and the rewrite can deadlock
       on the lock, notably on Windows);
    5. per tile_id: slice the GeoDataFrame, convert via
       bridge.gdf_to_layer (memory layer) and optionally
       bridge.write_gpkg_layer (file-backed), then either reattach the
       cloned renderer (assignment signature unchanged) or seed a fresh
       one; tag with the custom property that keeps outputs out of the
       region combo; register with the project but attach to our group
       ourselves (addMapLayer(..., False));
    6. refresh the outlines layer, remove the previous run's layers,
       and record ids/signatures/paths for the next regeneration.

    Layer *identities* change on every run (a documented trade-off:
    print-layout references need re-picking) but styling continuity is
    preserved via the signature check.
    """
    project = QgsProject.instance()
    force_new = self.opt_new_group.isChecked() or path != self._last_path
    group, created = self._get_or_make_group(force_new)
    group.setName(self._group_name)

    old_ids = dict(self._element_layer_ids)
    old_outline = self._outline_layer_id
    new_ids = {}
    by_id = {a["id"]: a for a in assignments}
    tile_ids = sorted(set(gdf["tile_id"]))
    warned_cardinality = []
    # {tile_id: the fills that element will paint}, gathered as the
    # renderers go on so the separability check sees the map's real
    # colours -- including any the user refined by hand
    element_fills = {}

    templates, template_errors = {}, []
    for token in {a.get("class_source") for a in assignments
                  if a.get("class_source")}:
      try:
        if token.startswith("layer:"):
          templates[token] = bridge.template_from_layer(
            project.mapLayer(token[6:]))
        else:
          templates[token] = bridge.load_categorized_template(token[5:])
      except Exception as e:
        template_errors.append(f"{token.split(':', 1)[1][-40:]}: {e}")

    # A run carries the settings it was launched with, which is right
    # for everything that decides the GEOMETRY: a spacing typed while
    # the tiles are being laid out belongs to the next run, not this
    # one. Hand-picked category colours are the exception. The editor
    # is usable while a run is in flight, and the restyle path
    # declines during one, so a colour chosen in that window would be
    # seeded from the stale snapshot and silently lost the moment the
    # run landed. The dialog's record is the authority for those, so
    # it is re-read here rather than trusted from the snapshot.
    for a in assignments:
      if a.get("mode") == "Categorized" and a.get("var"):
        a["category_colours"] = self._category_colours.get(
          a["id"], {}).get(a["var"])

    # keep the previous run's renderers (possibly hand-refined in the
    # styling dock) before touching any layers
    old_renderers = {}
    old_layer_opacity = {}
    for tid, lid in old_ids.items():
      old_layer = project.mapLayer(lid)
      if old_layer is not None and old_layer.renderer() is not None:
        old_renderers[tid] = old_layer.renderer().clone()
        # opacity lives on the layer, not the renderer, so it has to
        # be carried across separately when an element is kept as-is
        old_layer_opacity[tid] = old_layer.opacity()
    if path:
      # release file handles before overwriting GeoPackage layers,
      # otherwise the write can hit sqlite locks (notably on Windows)
      for lid in old_ids.values():
        if project.mapLayer(lid) is not None:
          project.removeMapLayer(lid)
      old_ids = {}

    first_gpkg_layer = True
    for tid in tile_ids:
      a = by_id.get(tid, {"id": tid, "var": None, "mode": "Single colour",
                          "ramp": "Greys", "scheme": "Quantiles", "k": 5,
                          "outline": False})
      display = f"{tid} – {a['var']}" if a["var"] else f"{tid} (no data)"
      sub = gdf[gdf["tile_id"] == tid]
      mem = bridge.gdf_to_layer(sub, display)
      if path:
        out = bridge.write_gpkg_layer(mem, path, f"tiles_{tid}",
                                      first=first_gpkg_layer and created)
        first_gpkg_layer = False
      else:
        out = mem

      # styling: keep the previous layer's (possibly hand-refined)
      # renderer when this element's assignment didn't change
      signature = self._signature(a)
      unchanged = (tid in old_renderers
                   and self._last_signatures.get(tid) == signature)
      if unchanged:
        out.setRenderer(old_renderers[tid])
        # opacity travels with the renderer: an element the dialog has
        # not changed keeps whatever opacity its layer had, which may
        # be one the user set by hand in Layer Properties. Same promise
        # the renderer gets, and the reason opacity is a layer property
        # rather than something baked into the colours
        if old_layer_opacity.get(tid) is not None:
          out.setOpacity(old_layer_opacity[tid])
      else:
        if a["mode"] == "Categorized" and a["var"]:
          idx = mem.fields().indexOf(a["var"])
          if idx >= 0 and len(mem.uniqueValues(idx)) > 60:
            warned_cardinality.append(f"{tid} ({a['var']})")
        bridge.seed_renderer(out, a, templates.get(a.get("class_source")))
        # re-seeded, so the dialog is the authority for this element's
        # whole appearance this run, opacity included
        out.setOpacity(max(0, min(100, a.get("opacity", 100))) / 100.0)
      if path:
        bridge.embed_style(out)
      element_fills[tid] = bridge.renderer_fill_colours(out)
      out.setCustomProperty("weavingspace_output", True)
      # Hand-picked category colours travel with the layer, so a saved
      # project reopened after QGIS restarts still knows them and the
      # next Generate keeps them. The dialog's own dict lives only as
      # long as the session; the .qgz outlives it.
      self._stamp_category_colours(out, a)
      # the element this layer carries, so a dialog opened later in
      # the session can adopt the group instead of starting a rival
      # one (see _adopt_existing_group)
      out.setCustomProperty("weavingspace_tile_id", tid)
      project.addMapLayer(out, False)
      group.addLayer(out)
      new_ids[tid] = out.id()
      self._last_signatures[tid] = signature

    # map unit outlines (kept on top of the group, project-only)
    if old_outline and project.mapLayer(old_outline) is not None:
      project.removeMapLayer(old_outline)
      self._outline_layer_id = None
    if self.opt_outlines.isChecked():
      outline_layer = bridge.region_outline_layer(source_layer)
      outline_layer.setCustomProperty("weavingspace_output", True)
      outline_layer.setCustomProperty("weavingspace_outline", True)
      project.addMapLayer(outline_layer, False)
      group.insertLayer(0, outline_layer)
      self._outline_layer_id = outline_layer.id()

    # drop the previous run's element layers
    for tid, lid in old_ids.items():
      if project.mapLayer(lid) is not None:
        project.removeMapLayer(lid)
    for tid in list(self._last_signatures):
      if tid not in new_ids:
        del self._last_signatures[tid]
    self._element_layer_ids = new_ids
    self._last_path = path
    # what this run DREW, not what the table says now (see the note
    # where these are captured, in _generate)
    self._last_run_sig = (run_sig if run_sig is not None
                          else self._run_signature())
    self._last_geometry_sig = (geometry_sig if geometry_sig is not None
                               else self._geometry_signature())
    self._update_layer_exclusions()

    # Are any two ELEMENTS' colours too close for a reader to
    # separate? Asked of the finished renderers, under ordinary vision
    # and the two red-green deficiencies. The plugin does not change
    # anyone's ramps on the strength of it; which colours to use is
    # the cartographer's decision, and this only makes the cost of a
    # choice visible while it can still be changed.
    #
    # Off unless asked for. It is a second opinion on a cartographic
    # choice rather than a fault, and while somebody is still trying
    # ramps it has nothing useful to say -- it would fire on almost
    # every intermediate state, which is how a warning becomes
    # something people learn to ignore. The whole check is skipped
    # rather than computed and withheld, so an unchecked box costs
    # nothing at all.
    colour_clash = None
    if self.opt_colour_warnings.isChecked():
      from weavingspace_qgis import perception
      colour_clash = perception.clash_message(
        perception.clashes(
          {tid: fills for tid, fills in element_fills.items() if fills},
          shared={a["id"]: (a.get("ramp"), a.get("reverse"),
                            a.get("class_source"))
                  for a in assignments}))
    # Stashed rather than reported here. This runs inside
    # _on_generated, whose finally clears live_note -- so a notice
    # pushed now is wiped a moment later, which is exactly what
    # happened the first time, and is why the coverage notice waits
    # too. The done callback sends it once the dust has settled.
    self._pending_colour_note = colour_clash

    if self.iface is not None:
      note = f"'{self._group_name}': {len(gdf)} tiles across " \
             f"{len(tile_ids)} element layers"
      if path:
        note += f", saved to {path}"
      self.iface.messageBar().pushSuccess("WeavingSpace", note)
      if colour_clash is not None:
        self.iface.messageBar().pushWarning("WeavingSpace", colour_clash)

      if warned_cardinality:
        self.iface.messageBar().pushWarning(
          "WeavingSpace",
          "Categorized styling produced a very large number of classes "
          "for: " + ", ".join(warned_cardinality)
          + ". Is that field really categorical?")
      if template_errors:
        self.iface.messageBar().pushWarning(
          "WeavingSpace",
          "Some class style files could not be used ("
          + "; ".join(template_errors)
          + "); automatic colours were applied instead.")
