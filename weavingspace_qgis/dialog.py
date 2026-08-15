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

from qgis.PyQt.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from qgis.PyQt.QtGui import (
  QBrush, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap)
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
  QStyle,
  QStyleOptionComboBox,
  QStylePainter,
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

# How many stripes a swatch shows. The swatch is 64px wide, and below
# about 8px a stripe stops reading as a colour of its own; eight also
# samples a ramp closely enough that neighbouring ramps stay
# distinguishable in the dropdown.
SWATCH_STRIPES = 8

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
    # bridge.get_ramp clones and, when asked, reverses; the swatch
    # therefore shows the direction the map will actually use
    ramp = bridge.get_ramp(name, reverse)
    if ramp is None:
      return None
    # Drawn through the SAME construction as a Custom swatch (user
    # instruction, 2026-08-09): equal vertical stripes of sampled
    # colours, not QGIS's continuous gradient preview. Two cells side
    # by side in one column should differ in what they SHOW, never in
    # how they are drawn -- a gradient beside a striped swatch reads
    # as two kinds of thing, and the Custom swatch is the honest one
    # because a classed map paints steps rather than a gradient.
    # Sampled at the ends inclusive (i/(n-1)), which is where the
    # first and last classes of a graduated map take their colours,
    # so the swatch's extremes are the map's extremes.
    stripes = SWATCH_STRIPES
    colours = [ramp.color(i / (stripes - 1)).name()
               for i in range(stripes)]
    # deliberately NOT narrowed by any row's Ramp Display Range:
    # choosing a ramp resets that window (the settled "until
    # reselected anew"), so a windowed preview would promise colours
    # the click itself would discard
    return _striped_icon(colours)
  except Exception:
    pass
  return None


# The layout rule, settled 2026-08-09 and ordered deliberately: the
# window never exceeds 1280 logical pixels, the narrowest screen still
# in use, because a wider window is one nobody can see whole. Within
# that, the TABLE comes first -- it never scrolls horizontally, since
# a horizontal scrollbar on a table is invisible in practice and the
# columns to its right go unfound -- and the preview then gives up
# width, down to a floor below which it stops being able to show
# whether shapes read as distinct elements. If those ever conflict,
# narrow COLUMNS, not the preview past its floor.
MAX_WINDOW_WIDTH = 1280

# Extra pixels reserved beside the scrollbar. Qt's own metric and the
# bar it draws disagree by four pixels on this platform, and a table
# short by even one grows a horizontal scrollbar -- the one thing the
# layout rule forbids, because columns past it go unfound. Cheap
# insurance: the window is capped anyway and the preview gives up the
# difference. (2026-08-10.)
SCROLLBAR_SLACK = 6
PREVIEW_FLOOR = 260


# The tooltip for a ramp cell reading "Custom". The wording is the
# user's own (settled 2026-08-09), and sits AT the fifteen-word
# tooltip cap: fifteen words, which the checker allows and one more
# would not.
CUSTOM_RAMP_TOOLTIP = ("Colours set by hand or by a class file. "
                       "Choose a ramp to replace them.")


def _striped_icon(colours, boxed=(), hatched=()):
  """The one way this dialog draws a colour swatch.

  Args:
    colours: "#rrggbb" strings in the order they should appear, left
      to right. At most SWATCH_STRIPES are drawn; an empty list gets
      one neutral grey stripe, so a cell never shows an empty icon
      that would read as a failure to draw.
    boxed: which stripes carry a PINNED class bound, as indices into
      the drawn stripes -- 0 for the first, -1 for the last. Each is
      outlined, which is how the table says "this end is yours"
      without the ramp cell having to claim the ramp is no longer the
      ramp: a pin moves breaks, not colours (maintainer's decision,
      2026-08-14).
    hatched: which stripes stand for classes NO TILE WEARS, as
      indices. Each is crossed with light diagonals. Copying a ladder
      onto an element carrying another column can leave classes the
      data cannot reach, and those are kept rather than dropped --
      a copy is meant to reproduce a classification and a silently
      shortened one does not -- so the emptiness is made visible
      instead of being left silent (maintainer's decision,
      2026-08-14).

  Returns:
    A QIcon of equal vertical stripes at RAMP_SWATCH size.

  EVERY swatch in the ramp column goes through here -- the named
  ramps in the dropdown and the Custom swatch alike (user
  instruction, 2026-08-09). Sharing the construction is the point:
  cells in one column should differ in what they show and never in
  how they are drawn, and stripes are the honest shape for both,
  because a classed map paints steps rather than a gradient.
  """
  shown = list(colours)[:SWATCH_STRIPES] or ["#c0c0c0"]
  pixmap = QPixmap(RAMP_SWATCH)
  pixmap.fill(Qt.GlobalColor.transparent)
  painter = QPainter(pixmap)
  width = RAMP_SWATCH.width() / len(shown)
  for i, name in enumerate(shown):
    painter.fillRect(
      QRectF(i * width, 0, width, RAMP_SWATCH.height()), QColor(name))
  # Diagonals first, then the pin boxes, both over the fills: a
  # hatched stripe may also be a pinned one, and the box must read as
  # the outer line rather than being crossed by the hatching.
  for index in hatched:
    position = index if index >= 0 else len(shown) + index
    if not 0 <= position < len(shown):
      continue
    fill = QColor(shown[position])
    lightness = (fill.red() * 299 + fill.green() * 587
                 + fill.blue() * 114) / 1000.0
    ink = QColor("#ffffff") if lightness < 128 else QColor("#000000")
    ink.setAlpha(140)             # light, so the colour still reads
    painter.setPen(QPen(ink, 1))
    left = position * width
    height = RAMP_SWATCH.height()
    step = 4
    offset = -height
    while offset < width:
      painter.drawLine(QPointF(left + offset, height),
                       QPointF(left + offset + height, 0.0))
      offset += step
  # The pin boxes go on LAST, over the fills, so an outline is never
  # painted away by the stripe beside it. Drawn in the stripe's own
  # contrasting ink rather than a fixed colour, or the box would
  # vanish on a dark ramp and shout on a pale one.
  for index in boxed:
    position = index if index >= 0 else len(shown) + index
    if not 0 <= position < len(shown):
      continue
    fill = QColor(shown[position])
    lightness = (fill.red() * 299 + fill.green() * 587
                 + fill.blue() * 114) / 1000.0
    ink = QColor("#ffffff") if lightness < 128 else QColor("#000000")
    painter.setPen(QPen(ink, 2))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRect(QRectF(position * width + 1, 1, width - 2,
                            RAMP_SWATCH.height() - 2))
  painter.end()
  return QIcon(pixmap)


def _custom_swatch_icon(colours, boxed=(), hatched=()):
  """The swatch drawn while a ramp cell reads "Custom".

  Args:
    colours: the element's actual colours as "#rrggbb" strings, in
      class order, exactly as the renderer would paint them --
      unsorted and unfiltered, so the swatch samples the map rather
      than presenting a tidied summary of it.
    boxed: stripe indices carrying a pinned bound; see _striped_icon.
    hatched: stripe indices for classes no tile wears; see the same.

  Returns:
    A QIcon of the first colours as equal vertical stripes, drawn by
    _striped_icon, which is also what every named ramp's swatch goes
    through.
  """
  return _striped_icon(colours, boxed, hatched)


class RampCombo(QComboBox):
  """The colour-ramp dropdown, able to DISPLAY "Custom" without
  listing it.

  An element whose colours are partly decided by something other than
  its ramp shows "Custom" in this cell -- hand-picked values or an
  imported class source on a categorized row, positional class picks
  or a narrowed display range on a graduated one -- because a ramp
  name alone would be a control lying about the map. But "Custom"
  must never be an ITEM: every standard ramp
  stays selectable at all times (an explicit user requirement), and an
  item the user could choose would need a meaning to give it. So only
  the CLOSED combo's painting is overridden; the popup list, the
  model, the current index and every signal are untouched.

  The underlying index deliberately stays on the last-picked ramp. A
  class source or a hand-pick governs only the values it names, and
  the ramp still colours the leftovers (pinned by
  test_a_class_source_that_does_not_match_the_data), so there is
  always a real ramp underneath the Custom display and the dropdown
  still reaches it.

  Args:
    parent: the owning widget, as usual in Qt.
  """

  def __init__(self, parent=None):
    super().__init__(parent)
    # None means "paint normally"; a QIcon means "paint the Custom
    # display, with this swatch of the element's actual colours"
    self._custom_icon = None
    # a swatch whose pinned ends are boxed, shown BESIDE the ramp's
    # own name; Custom outranks it when both apply
    self._pinned_icon = None

  def set_custom_display(self, icon):
    """Show or clear the Custom display.

    Args:
      icon: a QIcon of the element's actual colours to draw as the
        swatch, or None to return to painting the current ramp.

    Returns:
      None. Only the closed combo's painting changes; items, index
      and signals are untouched, so a dropdown the user has open
      cannot be disturbed (the chooser-race rule).
    """
    self._custom_icon = icon
    # repaint unconditionally: a fresh swatch for an unchanged state
    # (one more colour picked) must also reach the screen
    self.update()

  def set_pinned_display(self, icon):
    """Show the ramp's NAME beside a swatch that boxes a pinned end.

    Args:
      icon: a QIcon of the element's classes with its pinned ends
        outlined, or None to return to the plain ramp swatch.

    Returns:
      None. Unlike set_custom_display this leaves the TEXT alone, and
      that is the whole point: a pin moves breaks, not colours, so
      the cell goes on naming the ramp it really is drawing while the
      box says which end the user set (maintainer's decision,
      2026-08-14). Custom outranks it -- an element with hand-picked
      colours is Custom whether or not it is also pinned.
    """
    self._pinned_icon = icon
    self.update()

  def showing_custom(self) -> bool:
    """Whether the closed combo currently reads Custom."""
    return self._custom_icon is not None

  def paintEvent(self, event):  # noqa: N802 (Qt API)
    """Qt calls this to draw the CLOSED combo; the popup draws its own
    items and is never affected. When the Custom display is on, the
    text and icon are swapped inside the style option Qt was about to
    draw anyway, so platform styling, the focus ring and the drop-down
    arrow all stay native."""
    if self._custom_icon is None and self._pinned_icon is None:
      super().paintEvent(event)
      return
    if self._custom_icon is None:
      # pinned but not custom: Qt draws the combo as it always would,
      # with the ramp's own name, and only the swatch is swapped
      painter = QStylePainter(self)
      option = QStyleOptionComboBox()
      self.initStyleOption(option)
      option.currentIcon = self._pinned_icon
      option.iconSize = RAMP_SWATCH
      painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
      painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)
      return
    painter = QStylePainter(self)
    option = QStyleOptionComboBox()
    self.initStyleOption(option)
    option.currentText = "Custom"
    option.currentIcon = self._custom_icon
    option.iconSize = RAMP_SWATCH
    painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
    painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)


# The one live dialog in this QGIS session, if any. The plugin reuses
# a single dialog, but nothing stopped a second one existing: reloading
# the plugin (routine while developing, and QGIS's Plugin Reloader does
# it constantly) leaves the previous instance alive with its timers
# running and possibly a tiling in flight. Since a new dialog adopts
# the existing output group, two instances would write to the same
# layers, each unaware of the other. One at a time, enforced.
_LIVE_DIALOG = None

# Where the one-at-a-time rule REALLY keeps its record. A module
# global is not enough: QGIS's Plugin Reloader re-executes this
# module, which resets `_LIVE_DIALOG = None` above, and the dialog
# built from the reloaded class then retires nothing -- the
# predecessor keeps its timers running against the group the newcomer
# has just adopted. So the reference is parked on the QApplication
# instance, which outlives every plugin reload, under this key; the
# module global stays as the fallback for the rare case where there
# is no application object (some headless uses).
_LIVE_KEY = "weavingspace_live_dialog"


def _live_dialog():
  """The dialog currently in charge, across module reloads.

  Returns:
    The live WeavingSpaceDialog, or None. Read from the QApplication
    instance first (it survives a plugin reload, and this module does
    not), falling back to the module global.
  """
  try:
    from qgis.PyQt.QtWidgets import QApplication
    app = QApplication.instance()
    if app is not None:
      return app.property(_LIVE_KEY)
  except Exception:
    pass
  return _LIVE_DIALOG


def _set_live_dialog(dialog):
  """Record which dialog is in charge, where a reload cannot forget.

  Args:
    dialog: the dialog taking over, or None to clear the record.

  Returns:
    None. Written to BOTH the application property and the module
    global, so either route answers correctly whichever module object
    a caller happens to be running in.
  """
  global _LIVE_DIALOG
  _LIVE_DIALOG = dialog
  try:
    from qgis.PyQt.QtWidgets import QApplication
    app = QApplication.instance()
    if app is not None:
      app.setProperty(_LIVE_KEY, dialog)
  except Exception:
    pass


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
    # tile's label anchor plus its bounds, so labels can be skipped on
    # tiles that draw too small to carry one. The anchor is the
    # CENTROID, with representative_point() only as the fallback when
    # the centroid falls outside a concave tile -- naming
    # representative_point here was left over from before that change,
    # which was made because it put labels visibly off-centre
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

  # element counts offered (the catalogue's keys: every count from 2
  # to 26, where single-character element ids stop being distinct
  # without case -- see catalog.MAX_ELEMENTS for why that matters)
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
    # {gpkg path: {element ids this dialog wrote into it}}. Kept so a
    # design that SHRINKS can remove the tables its own previous run
    # left behind, and so that it can remove ONLY those: a GeoPackage
    # is an ordinary file somebody may keep other data in, and
    # deleting a table on the strength of its name matching our
    # convention would eventually delete somebody's work.
    self._gpkg_tables_written = {}
    self._last_run_sig = None
    # the geometry of the last completed run, so a later style-only
    # change can be answered without tiling again
    self._last_geometry_sig = None
    # per-element UI memory, keyed by tile_id so it survives table
    # rebuilds: category counts per (layer id, field), each element's
    # class-source choice, QML files browsed anywhere this session,
    # picked single colours, and last ramp names
    self._cat_count_cache = {}
    # one field's values, keyed by (layer, field, fingerprint) and
    # holding a single entry: the breaks are cut from these, and a
    # stale set would classify the map against data that has gone
    self._values_cache = {}
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
    # Graduated (quant) customization, settled 2026-08-09. Class
    # colours picked by hand are keyed POSITIONALLY -- {tile_id:
    # {field: {str(class index): "#rrggbb"}}} -- because a class has
    # no name to follow when its breaks move; per-field so switching
    # a variable away and back restores the work, exactly as the
    # categorical picks do.
    self._quant_colours = {}
    # Class bounds a person set, {tile_id: {field: {"low": float,
    # "high": float}}}. Keyed by field as well as element, like the
    # hand-picked colours, so switching a variable away and back
    # restores the pins rather than applying one column's numbers to
    # another's data. The copy feature on the roadmap extends this
    # record with the boundary VALUES and a per-end pin FLAG; pins
    # alone need only the bounds, and the two are the same statement
    # until a copy separates them.
    self._pinned_bounds = {}
    # {tile_id: (lo, hi)}: the percent window of the ramp the classes
    # sample from (the Ramp Display Range). Absent means the whole
    # ramp. Data-blind, so it survives a field switch; only choosing
    # a ramp resets it.
    self._ramp_ranges = {}
    # {tile_id: class count}. Every other per-element control has had
    # a dict of this shape since the settled decision that these
    # belong to the ELEMENT and not the row widget; the class count
    # alone rode on the spinner's `user_k` property, which is enough
    # to survive a table rebuild (the count comes back through the
    # previous assignments) and not enough to survive a REOPEN, where
    # there are no previous assignments and every row is built fresh
    # on 5. Added 2026-08-13 so a reopened project can be told what
    # the layer's own renderer says. (Maintainer's decision the same
    # day: preserve the row across a save where we can.)
    self._class_counts = {}
    # {tile_id: mode} -- the renderer kind each element was last SYNCED
    # in, which is what tells a deliberate ramp pick from the automatic
    # swap that follows a style change. _sync_row substitutes a
    # qualitative palette when a row turns Categorized carrying a
    # sequential ramp, and that is right: a sequential ramp over
    # categories is a cartographic error nobody chose. It ran on EVERY
    # sync, though, and a sync follows every data-tab change -- so a
    # ramp deliberately picked on a row already sitting in that mode
    # was swapped straight back out, after the pick had destroyed the
    # element's hand-picked colours on its way past. The user paid for
    # a change they did not get. Comparing against the mode at the last
    # sync separates the two cases without depending on which Qt signal
    # arrives first, which is where two earlier attempts foundered.
    # (Found by the stochastic hunt 2026-08-13; maintainer's decision:
    # leave the dropdown offering every ramp, cartographer beware.)
    self._synced_modes = {}
    # {class-source token: (mtime_ns, size)} -- the last reading taken
    # of each QML this session, so that a file which has GONE can keep
    # the stamp it had rather than moving the signature. See
    # _class_source_stamp.
    self._class_source_stamps = {}
    # {tile_id: {"Graduated": name, "Categorized": name}} -- the ramp
    # each element last wore in each mode, so a style excursion and
    # back costs nothing. This lived on the combo widget as `last_quant`
    # and `last_cat` until 2026-08-13, which survives a style flip and
    # NOT a table rebuild: any design change rebuilds the table 350 ms
    # later, so a ramp crossed over before that landed came back as a
    # positional default instead. Every other per-element choice is
    # keyed by tile id for exactly this reason (settled decision).
    self._ramp_memory = {}
    # True while the dialog itself is writing renderers, so the
    # styleChanged watcher (see _on_layer_style_edited) can tell a
    # QGIS-side edit from our own seeding and react only to the first
    self._applying_style = False
    # elements whose renderer the LAST run carried over unchanged;
    # _finish_run re-examines them for dock edits made mid-run
    self._preserved_this_run = []
    # {tile_id: (key, QIcon)} -- the Custom-display swatch, cached
    # against everything that decides an element's colours, because
    # building one means constructing the real renderer against the
    # region layer (see _custom_swatch_for)
    self._custom_swatch_cache = {}
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
    # The ramps come FIRST, and the order is load-bearing as of
    # 2026-08-13. Adoption now reads an existing layer's ramp back
    # off its renderer, which means asking which library ramp draws
    # it -- and this ran two lines before `_ramp_names` existed, so
    # every lookup failed and every adopted element fell through to
    # Custom. The ramps must also be INSTALLED by then, or a project
    # styled with a mapweaver palette reopens unable to name it.
    bridge.ensure_ramps_installed()
    self._ramp_names = bridge.ramp_names()
    self._adopt_existing_group()
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
    # True once the window has been closed. A closed dialog
    # must not write into the project: the timers can be
    # stopped, but the region layer's signals stay connected
    # and re-arm them. NOT `isVisible()`, deliberately -- the
    # test suite drives live update on dialogs it never
    # shows, so a visibility test would quietly disable the
    # behaviour it was meant to guard.
    self._closed = False
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
    # 260 is the settled width floor (2026-08-09): below it the
    # preview cannot do its job -- judging whether shapes read as
    # distinct elements by colour and form -- and merely occupies
    # space. The layout rule gives the table its columns first, then
    # lets the preview give up width down to exactly here.
    self.preview.setMinimumSize(PREVIEW_FLOOR, 230)
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
       "Reverse", "Opacity", "Categ colourmap src", "Edit colours"])
    # Qt draws a row-number gutter unless told not to, so the table
    # showed 1, 2, 3, 4 immediately beside the Tile id column showing
    # a, b, c, d: two columns of identifiers, one of them meaningless,
    # and the meaningless one read as authoritative. The LETTERS are
    # the element ids everything in this plugin is keyed on -- the
    # preview labels them, the output layers are named for them, the
    # colour records are dictionaries of them. Hiding the gutter also
    # returns width the table needs to show every column without
    # scrolling sideways, which nobody notices it doing.
    self.table.verticalHeader().setVisible(False)
    self.table.setColumnWidth(0, 50)
    self.table.setColumnWidth(1, 160)
    self.table.setColumnWidth(2, 152)
    self.table.setColumnWidth(3, 55)
    self.table.setColumnWidth(4, 172)   # a 64px swatch plus the name
    self.table.setColumnWidth(5, 58)
    self.table.setColumnWidth(6, 68)
    self.table.setColumnWidth(7, 150)
    self.table.setColumnWidth(COL_EDIT_COLOURS, 82)
    # The conditional columns start hidden. These three lines are the
    # FIRST state the table has; _refresh_table then calls
    # _update_dynamic_columns, which decides these three from the
    # assignments (it decides FOUR columns in all -- Reverse is the
    # fourth and is not hidden here, because a table with no layer has
    # no ramp for it to belong to), so for a dialog that reaches a
    # layer these three are redundant. They are kept for the moment BEFORE that -- a table
    # built and shown with no layer chosen -- because a dead column
    # in front of a first-time user is exactly the fault the hiding
    # exists to prevent. Guarded by test_dialog_structure, which
    # names the columns by header rather than by index so a
    # renumbering cannot quietly hide the wrong one.
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
    and catches an edit that CHANGES WHAT IT MEASURES — the feature
    count, the bounding box, the field names, the CRS. The signals
    catch edits made through QGIS's own editing session. Between them
    they cover most of what a user does.

    WHAT NEITHER COVERS, stated plainly because the docstring here
    used to claim the opposite. An edit made straight through the
    DATA PROVIDER — which is what Processing and a good deal of
    plugin code do — emits no signal this dialog can hear, and if it
    rewrites values in place it moves nothing measured above. Every
    value in a column can change with the count, the extent, the
    names and the CRS all identical, and the plugin will not notice:
    Generate is then a silent no-op against data that has moved
    underneath it. Measured 2026-08-13.

    That is a LIMIT rather than a bug, and it is deliberate as of the
    same day (maintainer's decision): the alternatives are polling
    somebody's data or fingerprinting the values themselves, which
    costs a full scan on every check for a case the plugin cannot
    reliably detect anyway. The rule this file used to state — that
    "neither mechanism covers the other's blind spot" — was simply
    untrue, and a false promise in a docstring is worse than a known
    gap, because it stops anybody looking.

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
      # An EMPTY layer has no extent, and QGIS says so with DBL_MAX
      # sentinels rather than with zeros -- so `round()` on the width
      # meets NaN and raises `cannot convert float NaN to integer`.
      # Deleting every feature from the region layer is an ordinary
      # thing to do mid-session, and this runs from the live path and
      # from both signatures, where the raise goes to a console
      # nobody has open. Found by the stochastic hunt on 2026-08-13
      # (seeds 356, 401, 409) and reproduced directly. "empty" is a
      # perfectly good fingerprint: it differs from every real extent
      # and from itself never, so an emptied layer compares equal to
      # an emptied layer and unequal to one with data, which is all
      # this tuple is for. Guarded by
      # test_an_emptied_region_layer_does_not_raise.
      ("empty" if ext.isNull() or ext.isEmpty() else
       (round(ext.xMinimum()), round(ext.yMinimum()),
        round(ext.xMaximum()), round(ext.yMaximum()))),
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
    element at the NEW column would map data the user never asked for.
    So it does not do that: the element re-defaults to a surviving
    field and the user is told which one it landed on, and only when
    no field survives at all does it go unassigned. Losing a column
    costs an element its variable, not its place on the map.
    (This block said the element was unassigned, which the comment
    twenty lines below and CLAUDE.md both contradict; corrected
    2026-08-12.)
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
      # THE PICKS ARE KEPT, exactly as the graduated ones are. This
      # used to pop the categorical record for the vanished field,
      # while `_quant_colours` was left alone -- so renaming a column
      # in QGIS destroyed every colour a user had picked by hand for
      # that element, unannounced, and renaming it straight back did
      # not bring them home. The graduated twin survived the same
      # act. Both records are keyed by element AND field, which is
      # what makes keeping them safe: a field that never returns
      # costs a few bytes, and a field that does return -- a rename
      # undone a second later, which is the ordinary case -- finds
      # its colours waiting. Made symmetrical on the maintainer's
      # instruction, 2026-08-13. Guarded by
      # test_a_renamed_column_does_not_destroy_hand_picked_colours.
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
    every relevant control change passes through here.

    A CLOSED dialog arms nothing. Stopping the timers on the way out
    was not enough, because the region layer's own signals are still
    connected and re-arm them: see closeEvent for what that cost.
    """
    self._update_dynamic_columns()
    if self._closed:
      return
    self._live_timer.start()

  def closeEvent(self, event):  # noqa: N802 (Qt API)
    """Qt calls this when the window closes.

    Args:
      event: the close event, passed through untouched.

    Returns:
      None. A tiling in flight is cancelled, so a closed dialog does
      not go on computing invisibly (the task's cancel path still
      reports once, resetting our state; see worker.py), and the
      DEBOUNCE TIMERS ARE STOPPED. Cancelling the task alone was not
      enough: a live-update timer armed a moment before the close
      fires ~900ms later, and _maybe_live_generate then starts a
      fresh tiling that writes layers into the project on behalf of a
      window nobody can see -- which is exactly what a user unloading
      the plugin has asked not to happen.
    """
    if self._task is not None:
      try:
        self._task.cancel()
      except Exception:
        pass
    for timer in (getattr(self, "_live_timer", None),
                  getattr(self, "_preview_timer", None)):
      if timer is not None:
        try:
          timer.stop()
        except RuntimeError:
          pass                  # the Qt object is already gone
    self._live_pending = False
    # And the dialog is CLOSED, which the timers alone could not say.
    # Stopping them stopped the beat already armed; it did nothing
    # about the region layer's own signals, which stay connected to a
    # closed window and re-arm the timer on the user's next edit. So
    # a user who closed the dialog, DELETED the output group -- which
    # this project documents as the whole of the undo -- and then
    # edited their own data got the group and every element layer
    # written straight back, by a window they had shut. Its twin
    # `_retire_previous_instance` had this right for a superseded
    # dialog all along, by unchecking live update on the way past;
    # this path never learned it. Measured 2026-08-13. showEvent
    # clears the flag, so reopening restores the user's own setting
    # rather than silently turning live update off.
    # Guarded by test_a_closed_dialog_writes_nothing_into_the_project.
    self._closed = True
    super().closeEvent(event)

  def showEvent(self, event):  # noqa: N802 (Qt API)
    """Qt calls this when the window (re)appears.

    The fit below is a THIRD call site -- construction and family
    changes fit the window too -- and no test can tell its removal
    from the others, because the window will not grow past what the
    design needs nor shrink below its layout minimums. It is kept
    deliberately (user decision, 2026-08-10): the occasion it guards
    lives in real QGIS, a re-show after a screen or DPI change, and
    a window opening too small to show its own controls is the fault
    this line exists to prevent. Its catalogue entry is accepted
    rather than closed, with the evidence recorded there. Two duties: re-fit
    the height once real layout geometry exists, and recover from any
    zombie task (we believe a run is active but the task manager shows
    it dead), which otherwise blocks all future generations."""
    self._closed = False
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
    if self._closed:
      return          # a shut window draws nothing
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

  def _numeric_value_count(self, field_name: str) -> int:
    """Distinct finite numbers a field holds, across the REGION layer.

    Args:
      field_name: the attribute a graduated row is classifying.

    Returns:
      How many distinct values there are to divide into classes, or 0
      when there is no layer, no such field, or the provider refuses
      the question — in which case the caller reduces nothing, since
      an unknown count is not a small one.

    Why the region layer and not the element layer, which is what
    actually gets classified. An element layer holds only ITS OWN
    tiles, so the distinct count is per element, and reducing against
    it lets two elements carrying the same variable draw different
    numbers of classes. That was measured on 2026-08-13, cost a
    reverted release-candidate, and is the worse fault on a map whose
    purpose is reading elements against each other
    (test_metamorphic_variable_permutation says so in as many words).
    The region layer gives one answer for the whole map, and it is
    also stable under spacing: a design redrawn at a finer spacing
    does not silently gain classes.

    The price, accepted deliberately and already accepted elsewhere:
    at a coarse spacing the region layer can hold a value no tile
    carries, so a class can still go unworn. That is the same
    trade-off the Categorical colour editor settled on 2026-08-08,
    for the same reason, and the areas that received no tiles are
    reported separately by coverage_message.

    Cached like its categorical sibling, and in the same dict, since
    ``uniqueValues`` asks the provider and may scan the table; both
    are cleared together when the layer changes.
    """
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return 0
    idx = layer.fields().indexOf(field_name)
    if idx < 0:
      return 0
    key = (layer.id(), field_name, "numeric")
    if key not in self._cat_count_cache:
      try:
        self._cat_count_cache[key] = bridge.distinct_numeric_count(
          layer.uniqueValues(idx))
      except Exception:
        self._cat_count_cache[key] = 0
    return self._cat_count_cache[key]

  def _classification_values(self, field_name: str):
    """One column of the region, prepared for cutting breaks from.

    Args:
      field_name: the column a graduated element classifies.

    Returns:
      A geometry-less layer holding one entry per area, gaps
      included, or None when there is no layer or no such field --
      which tells make_graduated_renderer to classify the element
      layer as it always did.

    A LAYER rather than a list, and built once: every element wearing
    this column is seeded from the same copy, where handing over the
    values would have each element build its own -- twenty-six copies
    of a fifty-thousand-row column for one map.

    One entry per AREA rather than the distinct values, because
    quantiles are decided by how many areas fall where; a set of
    distinct values would weight a value held by one area the same as
    one held by half the map.

    Cached against the layer's own FINGERPRINT rather than merely its
    id. The count and extent move whenever features are added or
    removed, so an edit that changes what should be classified
    retires the entry; what it cannot see is a value rewritten
    straight through the data provider, which is the documented limit
    described at _on_layer_changed and applies to every other reading
    the dialog takes of this layer.
    """
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return None
    index = layer.fields().indexOf(field_name)
    if index < 0:
      return None
    # `_layer_fingerprint` takes no argument -- it reads the chosen
    # layer itself, which is the one being scanned two lines below.
    # Calling it with one raised TypeError into the guard beneath,
    # and the whole classification quietly fell back to per-element
    # breaks: a change that appeared to do nothing, which is exactly
    # what a silent fallback looks like from outside.
    key = (layer.id(), field_name, self._layer_fingerprint())
    if key not in self._values_cache:
      # one scan, and only when the fingerprint says the last one is
      # out of date. The same scan the missing-values notice makes.
      # The dict is REPLACED rather than added to, so the previous
      # fingerprint's values cannot sit there being wrong.
      try:
        values = [feature[field_name] for feature in layer.getFeatures()]
      except Exception:
        return None
      self._values_cache = {
        key: bridge.classification_source(field_name, values)}
    return self._values_cache.get(key)

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
        # a graduated row's customization travels with the flip: the
        # display window mirrors and the positional picks swap ends,
        # so reversing twice restores everything (settled 2026-08-09)
        self._mirror_quant_customization(tid)
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
    """The ToggleSwitch inside a row's Reverse cell, or None when that
    row has no ramp to reverse.

    Not a QCheckBox: ToggleSwitch is a QAbstractButton subclass drawn
    by hand, and its own docstring says why a styled QCheckBox was
    rejected. Named wrongly here and in _reverse_state's comment until
    2026-08-12."""
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
      A RampCombo listing every ramp in the QGIS style library, each
      with a preview swatch drawn in its current direction. On
      categorized and graduated rows alike it can additionally
      DISPLAY "Custom" (see RampCombo); _sync_row decides when.
    """
    ramp_combo = RampCombo()
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
        # colours, so anything picked by hand goes with it -- and on
        # a graduated row the display range resets too ("until
        # reselected anew", settled 2026-08-09)
        self._clear_category_colours(tid, "a new colour ramp")
        self._clear_quant_customization(tid, "a new colour ramp")
      self._refresh_preview_colours()

    ramp_combo.currentIndexChanged.connect(changed)

    def picked(_index, c=ramp_combo):
      # ``changed`` above runs only when the INDEX changes. While the
      # cell reads Custom the index still sits on the ramp colouring
      # the leftover values, so re-choosing that same ramp fires only
      # this signal -- and it is still the deliberate act of choosing
      # a ramp, which destroys the hand-picks (the settled rule; the
      # notice comes from _clear_category_colours as ever). On an
      # ordinary index change both signals fire, but ``changed`` has
      # already cleared the picks and refreshed the display by the
      # time this runs, so the guard makes it a no-op.
      if not c.showing_custom():
        return
      tid = c.property("tile_id")
      if tid:
        self._clear_category_colours(tid, "a new colour ramp")
        self._clear_quant_customization(tid, "a new colour ramp")
      self._refresh_preview_colours()

    ramp_combo.activated.connect(picked)
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
      # clamp the PROPERTY, not only the display: `_assignments`
      # reads the property, so clamping one and not the other is how
      # a cell and a map come to disagree about the same number
      k_spin.setProperty(
        "user_k", min(int(k_spin.property("user_k") or 5), 20))
      k_spin.setValue(int(k_spin.property("user_k")))
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
    # evenly, but enabled only where reversing means something. On a
    # Single colour row it greys out AND clears, because a reversed
    # single colour means nothing and a stale tick would mislead. A
    # Categorized row is disabled the same way even though it carries
    # a ramp: category colours are assignments to named values, not a
    # scale with a direction, so "the other way round" only shuffles
    # which value gets which colour. The control re-enables the moment
    # a quantitative style is chosen (user decision, 2026-08-09). The
    # recorded choice survives underneath, exactly as for Single
    # colour, so switching a row away and back costs no tick.
    tid_for_row = self.table.item(row, 0)
    row_id = tid_for_row.text() if tid_for_row else None
    has_ramp = ramp_combo is not None and not isinstance(
      ramp_combo, QgsColorButton)
    can_reverse = has_ramp and mode != "Categorized"
    box = self._row_reverse(row)
    if box is None and row_id:
      self.table.setCellWidget(row, 5, self._make_reverse_box(
        row_id, self._reverse_choices.get(row_id, False)))
      box = self._row_reverse(row)
    if box is not None:
      box.blockSignals(True)
      box.setEnabled(can_reverse)
      box.setChecked(bool(can_reverse and row_id
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
      # Remember this ramp under the family it BELONGS to, which is not
      # necessarily the mode the row is in: a categorized row carrying
      # YlOrRd is remembering a quantitative choice, and filing it under
      # "Categorized" would hand it straight back on the next flip. So
      # the ramp's own family decides the slot, and the swap below reads
      # the slot the MODE wants. Recorded on every sync rather than only
      # when a swap happens, so the ramp to come back to is whatever the
      # user last had, not merely whatever was last displaced.
      family = "Categorized" if is_cat_ramp else "Graduated"
      memory = self._ramp_memory.setdefault(row_tid, {}) \
        if row_tid else {}
      memory[family] = ramp
      # Has the row CHANGED mode since it was last synced? Only then is
      # the ramp in the cell one nobody chose for this mode, and only
      # then may it be swapped. On a row that has not moved, the ramp
      # arrived by the user picking it, and substituting it here would
      # undo the pick they just made -- while _clear_category_colours
      # had already destroyed their hand-picked colours on the way in,
      # for a change that then did not happen.
      moved = row_tid is None or self._synced_modes.get(row_tid) != mode
      target = None
      if moved and mode == "Categorized" and not is_cat_ramp:
        target = (memory.get("Categorized")
                  or self.CAT_DEFAULT_RAMPS[
                    row % len(self.CAT_DEFAULT_RAMPS)])
      elif moved and mode == "Graduated" and is_cat_ramp:
        target = (memory.get("Graduated")
                  or self.DEFAULT_RAMPS[row % len(self.DEFAULT_RAMPS)])
      if target is not None and ramp_combo.findText(target) >= 0:
        ramp_combo.blockSignals(True)
        ramp_combo.setCurrentText(target)
        ramp_combo.blockSignals(False)
        if row_tid:
          self._ramp_choices[row_tid] = target
          memory[mode] = target        # the slot the mode just filled

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
        # "Customize" rather than an ellipsis: the column heading says
        # what the button is for, but the button itself has to say
        # what it DOES, since a disabled ellipsis reads as a control
        # that is broken rather than one that does not apply here. And
        # a verb rather than "Custom": that word is the ramp cell's
        # display for colours already customized, and one word naming
        # a STATE in one column and an ACTION in the next would read
        # as the same thing twice. The -ize spelling is the project's
        # Canadian-spelling rule, no exception needed.
        button = QPushButton("Customize")
        button.clicked.connect(self._edit_category_colours)
        self.table.setCellWidget(row, COL_EDIT_COLOURS, button)
      button.setProperty("tile_id", tid)
      usable = mode in ("Categorized", "Graduated") and bool(var)
      button.setEnabled(usable)
      if mode == "Graduated" and var:
        # graduated rows edit class colours and the display range;
        # Unclassed rows open the same window with the range alone
        # live, so the button stays enabled there too
        tip = "Choose class colours, or narrow the ramp's display range"
      elif usable:
        tip = "Choose a colour for each value this element takes"
      else:
        tip = "Only elements drawn in classes have colours to edit"
      button.setToolTip(tip)
    elif self.table.cellWidget(row, COL_EDIT_COLOURS) is not None:
      self.table.removeCellWidget(row, COL_EDIT_COLOURS)

    # The ramp cell of a categorized row reads "Custom" while the ramp
    # alone no longer decides the element's colours: any hand-picked
    # colour recorded for the CURRENT field, or an imported class
    # source. "Any pick" deliberately, not "a pick that differs from
    # the ramp" -- under the latter the cell would read a ramp name
    # while an override was still recorded and outranking it in
    # make_categorized_renderer, which is a control lying about the
    # map. Two consequences fall out rather than being separate rules:
    # switching the variable to a field with no picks leaves Custom by
    # itself (and switching back re-enters it), and a reopened project
    # that adopted saved colours shows Custom. (Settled 2026-08-09.)
    ramp_cell = self.table.cellWidget(row, 4)
    if isinstance(ramp_cell, RampCombo):
      show_custom = False
      if mode == "Categorized" and var and row_tid:
        picks = self._category_colours.get(row_tid, {}).get(var)
        # read the live combo where the row has one; _class_choices
        # only catches up when the widget is removed or used
        file_widget = self.table.cellWidget(row, 7)
        choice = (file_widget.currentData() if file_widget is not None
                  else self._class_choices.get(row_tid, ""))
        has_source = bool(choice) and choice not in (self.BROWSE,
                                                     self.SHARED)
        show_custom = bool(picks) or has_source
      elif mode == "Graduated" and var and row_tid:
        # a graduated row is Custom while positional picks exist or
        # the Ramp Display Range is narrower than the whole ramp
        quant_picks = self._quant_colours.get(row_tid, {}).get(var)
        window = tuple(self._ramp_ranges.get(row_tid, (0, 100)))
        show_custom = bool(quant_picks) or window != (0, 100)
      # A PINNED row is not Custom: its colours are its ramp's, and
      # only its breaks are hand-set. So it keeps naming the ramp and
      # takes a boxed swatch instead, which is what says "this end is
      # yours" without the cell claiming the ramp is no longer the
      # ramp (maintainer's decision, 2026-08-14). Custom outranks it
      # when both apply, because hand-picked colours really do leave
      # the ramp behind.
      pinned = (self._pinned_bounds.get(row_tid, {}).get(var)
                if mode == "Graduated" and var and row_tid else None)
      if show_custom:
        ramp_cell.set_custom_display(
          self._custom_swatch_for(row_tid, var))
        ramp_cell.set_pinned_display(None)
        ramp_cell.setToolTip(CUSTOM_RAMP_TOOLTIP)
      else:
        ramp_cell.set_custom_display(None)
        ramp_cell.set_pinned_display(
          self._custom_swatch_for(row_tid, var) if pinned else None)
        # only undo our own tooltip; never blank one set elsewhere
        if ramp_cell.toolTip() == CUSTOM_RAMP_TOOLTIP:
          ramp_cell.setToolTip("")

    # Last: the row is now in step with its style, so record the mode
    # it was synced in. The next sync compares against this to tell a
    # deliberate ramp pick (mode unchanged) from the automatic swap a
    # style change earns (mode moved). It is written at the END so that
    # an early return above -- a half-built row mid-rebuild -- leaves
    # the previous answer standing rather than claiming a sync that did
    # not finish.
    if row_tid:
      self._synced_modes[row_tid] = mode

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
    # "Edit colours" appears whenever any element draws in CLASSES --
    # categorized or graduated alike, since the editor now serves both
    # (settled 2026-08-09). On rows with nothing to edit the button
    # stays but is disabled (see _sync_row): a gap in the column would
    # read as a missing control rather than an inapplicable one.
    has_editable = any(m in ("Categorized", "Graduated") and has_var
                       for m, has_var in modes.values())
    self.table.setColumnHidden(COL_EDIT_COLOURS, not has_editable)
    for row in rows:
      self._sync_row(row)
    # every place a column can appear or disappear funnels through
    # here, so this is where the layout rule is enforced
    self._fit_table_width()

  def _fit_table_width(self):
    """Give the table room for every visible column, within the cap.

    Returns:
      None. Sets the table's minimum width to the sum of its visible
      columns (plus frame and a vertical scrollbar's worth of slack,
      since a scrollbar that appears steals viewport width), and
      grows the WINDOW by any shortfall, capped at MAX_WINDOW_WIDTH.
      Qt then honours the minimum through every layout pass, which is
      what makes "the table never scrolls horizontally" a property of
      the dialog rather than an aspiration. The window is never
      shrunk here: columns disappearing hands the space to the
      preview, which is the layout rule's own priority order.
    """
    needed = sum(
      self.table.columnWidth(column)
      for column in range(self.table.columnCount())
      if not self.table.isColumnHidden(column))
    # Room for the table's own CHROME -- its frame and the vertical
    # scrollbar that appears as soon as the rows overflow. Measure it
    # rather than predict it: the difference between the widget and
    # its viewport IS the chrome Qt has actually drawn, whereas
    # PM_ScrollBarExtent reports the style's nominal 14px while the
    # bar drawn here is 18px. A table sized from the metric therefore
    # scrolled horizontally by those few pixels -- the exact fault
    # the layout rule forbids, reachable at sixteen elements on the
    # shipped catalogue, and invisible because the old layout test
    # only ever measured four rows. The metric stays as the fallback
    # for the first pass, before a viewport exists to measure.
    # (2026-08-10.)
    chrome = self.table.width() - self.table.viewport().width()
    fallback = 2 * self.table.frameWidth() + self.table.style().pixelMetric(
      QStyle.PixelMetric.PM_ScrollBarExtent)
    # Whichever is LARGER. The measured chrome is the truth once a
    # viewport exists, but this runs before layout too, and a first
    # pass that under-reserves leaves the table one or two pixels
    # short -- enough for a horizontal scrollbar, which is the whole
    # fault. Reserving a few pixels too many costs nothing: the
    # window is capped at MAX_WINDOW_WIDTH and the preview absorbs
    # the difference down to its floor.
    needed += max(chrome, fallback) + SCROLLBAR_SLACK
    self.table.setMinimumWidth(needed)
    shortfall = needed - self.table.width()
    if shortfall > 0 and self.width() < MAX_WINDOW_WIDTH:
      self.resize(min(MAX_WINDOW_WIDTH, self.width() + shortfall),
                  self.height())

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
      mode_combo.setProperty("tile_id", tid)
      # the baseline the scheme-change destruction compares against;
      # kept current in _on_mode_chosen
      mode_combo.setProperty("last_style", mode_combo.currentText())
      mode_combo.activated.connect(
        lambda _i, c=mode_combo, v=var_combo: self._on_mode_chosen(c, v))
      # currentIndexChanged rather than activated, so the destruction
      # fires however the style really changes -- a click emits both,
      # and the dialog's own programmatic style writes all block
      # signals, so nothing here reacts to the dialog talking to
      # itself
      mode_combo.currentIndexChanged.connect(
        lambda _i, c=mode_combo: self._on_style_changed(c))
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
      # the previous assignments first (a rebuild inside one
      # session), then the element's own record, which is the only
      # thing that exists after a REOPEN, then the default
      # The ELEMENT'S OWN RECORD FIRST, and the order matters. `prev`
      # is the previous ASSIGNMENT, whose k is 50 for a row sitting on
      # Quant: Unclassed -- fixed by the definition of that style
      # rather than chosen by anybody. Restoring from it wrote 50 into
      # `user_k`, which `_assignments` reads, so an excursion through
      # Unclassed and back left the element claiming fifty classes
      # while the spinner displayed its clamped 20 and the map drew
      # something else again: three numbers for one setting.
      # `_class_counts` is only ever written by a user moving the
      # spinner, so it is the one of the two that means "chosen".
      # Clamped here as well as displayed, because a value the
      # controls cannot express must not survive in a property.
      # Guarded by test_an_unclassed_excursion_leaves_the_count_alone.
      restored_k = self._class_counts.get(tid)
      if not restored_k and prev and prev.get("k"):
        restored_k = prev["k"]
      restored_k = max(2, min(int(restored_k or 5), 20))
      k_spin.setValue(restored_k)
      k_spin.setProperty("user_k", restored_k)
      k_spin.setToolTip(
        "Number of classes; categorized rows show how many "
        "categories were found.")

      k_spin.setProperty("tile_id", tid)

      def on_k(v, sp=k_spin):
        if sp.isEnabled():
          sp.setProperty("user_k", v)
          # and against the element, so the count outlives the widget
          if sp.property("tile_id"):
            self._class_counts[sp.property("tile_id")] = v
          # a new class count reclassifies the column, and positional
          # picks name classes that no longer exist: destroy, and say
          # so (settled 2026-08-09). Only enabled spins reach here,
          # which is exactly the editable graduated rows.
          tid_here = sp.property("tile_id")
          if tid_here:
            self._clear_quant_customization(
              tid_here, "a new class count", reset_range=False)
            self._release_copied_breaks(tid_here, "a new class count")
          self._queue_live()

      k_spin.valueChanged.connect(on_k)
      self.table.setCellWidget(row, 3, k_spin)
      k_spin.setVisible(not self.table.isColumnHidden(3))

      default = self.DEFAULT_RAMPS[row % len(self.DEFAULT_RAMPS)]
      # THE ELEMENT'S RECORD FIRST, then the previous assignment.
      # These were the other way round, and `prev` is a snapshot that
      # can be older than the record: after a run landed, the cell
      # came back showing the ramp the run was LAUNCHED with while
      # `_ramp_choices` held the one the user had picked while it
      # tiled. The map keeping the old ramp there is deliberate --
      # with live update off nothing repaints unasked -- but the
      # CONTROL denying a choice the dialog had kept is not: it is a
      # control lying about the map, which is the fault the Custom
      # display exists to prevent elsewhere. `_ramp_choices` is
      # written by every path that changes a ramp, including the one
      # that follows a dock edit, so it is the authority.
      # Guarded by test_a_ramp_chosen_during_a_run_is_not_lost.
      wanted = self._ramp_choices.get(tid) \
        or (prev.get("ramp") if prev else None) or default
      self.table.setCellWidget(
        row, 4, self._make_ramp_combo(tid, wanted))
      if prev and prev.get("single_colour"):
        self._single_colours[tid] = prev["single_colour"]
      if prev is not None and "reverse" in prev:
        # The report may only ADD a tick, never remove one, and the
        # asymmetry is the point.
        # `_assignments` reports the SWITCH, and reports False while
        # it is greyed -- right for the map, since an element with no
        # ramp must not reverse anything, but it is not a statement
        # about what the user chose. `_sync_row` unchecks that widget
        # and deliberately leaves the record standing so the tick
        # returns when the element has a ramp again; restoring from
        # the report undid exactly that, and a rebuild in the greyed
        # state silently discarded the tick. An actual untick needs
        # no help here: the toggle handler has already written False
        # into the record, so a False in the report carries nothing
        # the record does not already know. Guarded by
        # test_a_reverse_tick_survives_a_rebuild_while_it_is_greyed.
        self._reverse_choices[tid] = bool(prev["reverse"]) \
            or self._reverse_choices.get(tid, False)
      if prev is not None and "opacity" in prev:
        self._opacity_choices[tid] = prev["opacity"]

      if prev and prev.get("class_choice") is not None:
        self._class_choices[tid] = prev["class_choice"]
    self._update_dynamic_columns()

  # ------------------------------------------------------------ assignments

  def _stamp_category_colours(self, layer, assignment):
    """Record an element's customization on its output layer.

    Args:
      layer: the output layer for this element.
      assignment: its dict from ``_assignments()``.

    Returns:
      None. Writes TWO custom properties QGIS saves inside the
      project file -- weavingspace_category_colours for categorical
      hand-picks, weavingspace_quant_style for a graduated element's
      positional picks, PINNED BOUNDS and display range -- each
      cleared when there is nothing to record, so a layer never
      carries stale choices from a previous assignment.

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
    # the graduated customization travels the same way: positional
    # picks plus the display window, under their own property so the
    # two records cannot corrupt one another
    quant = assignment.get("quant_colours")
    window = tuple(assignment.get("range_bounds", (0, 100)))
    # ...and the PINNED BOUNDS with them. They have to be stamped
    # because nothing on a renderer records that a break was CHOSEN
    # rather than computed: a reopened project would read the breaks
    # back as ordinary classes, the row would show no pin, and the
    # next Generate would recompute over them. That is the shape of
    # the opacity and ramp defects of 2026-08-13, and this is the
    # same remedy.
    pinned = assignment.get("pinned") or {}
    if assignment.get("mode") == "Graduated" and (quant or pinned
                                                  or window != (0, 100)):
      layer.setCustomProperty(
        "weavingspace_quant_style",
        json.dumps({"field": assignment["var"],
                    "colours": quant or {},
                    # low and high are numbers; "breaks" is a whole
                    # copied ladder, so both shapes have to travel
                    "pinned": {
                      key: ([float(x) for x in value]
                            if isinstance(value, (list, tuple))
                            else float(value))
                      for key, value in pinned.items()},
                    "range": list(window)}, sort_keys=True))
    else:
      layer.removeCustomProperty("weavingspace_quant_style")

  def _adopt_category_colours(self, layer, tile_id):
    """Read stamped customization back off an adopted output layer.

    Args:
      layer: an existing output layer found in the project.
      tile_id: the element it carries.

    Returns:
      None. Reads BOTH stamped records -- categorical hand-picks, and
      a graduated element's positional picks with its display range
      -- filling in only where the dialog has nothing of its own, so
      a reopened project restores the user's work without overwriting
      anything chosen since.

    Anything unreadable is ignored rather than raised: a project file
    edited by hand, or written by a later version of the plugin, must
    not stop the dialog from opening.
    """
    # OPACITY comes from the layer itself rather than from a stamp,
    # because QGIS already persists layer opacity in the project and a
    # second copy could only disagree with it. Until 2026-08-13 the
    # dialog read neither: a reopened project showed 100% in the table
    # while the layer was still at the 60% the user chose, and the two
    # disagreed silently. That is worse than losing the setting, since
    # _add_output_layers pushes the dialog's belief back onto the
    # layer, so the next restyle -- any restyle, for any reason --
    # quietly undid a choice still visible in QGIS's own layer panel.
    # Only filled in where the dialog has nothing of its own, like
    # everything else here, so a choice made since reopening wins.
    if tile_id not in self._opacity_choices:
      self._opacity_choices[tile_id] = max(0, min(100, round(
        layer.opacity() * 100)))
    # THE ROW'S SYMBOLOGY, read off the renderer QGIS saved. Same
    # argument as opacity above and the same authority: the layer is
    # carrying the map, so it is carrying the truth, and a table that
    # disagrees with it does not stay cosmetic -- _add_output_layers
    # pushes the table's belief back, so the next Generate would
    # overwrite the map with defaults the user never chose. Until
    # 2026-08-13 the ramp, the reverse flag and the class count were
    # all lost this way; the round-trip test compared all three and
    # never moved them off a default, so nothing failed.
    #
    # WHERE THE RAMP CANNOT BE NAMED, the classes themselves are read
    # back and the row reads Custom -- the maintainer's instruction,
    # and the honest answer, since Custom already means "these
    # colours, not that ramp" and the swatch draws them. A reversed
    # ramp is a clone matching no name in the library, so it arrives
    # here as Custom rather than as a wrong ramp name, which is the
    # right way round: the map is preserved exactly and the control
    # stops claiming a ramp that is not what is drawn.
    self._adopt_row_symbology(layer, tile_id)
    raw = layer.customProperty("weavingspace_category_colours")
    if raw:
      try:
        stored = json.loads(raw)
        field = stored["field"]
        colours = {str(k): str(v) for k, v in stored["colours"].items()}
      except (ValueError, KeyError, TypeError, AttributeError):
        field, colours = None, None
      if field and colours:
        self._category_colours.setdefault(tile_id, {}).setdefault(
          field, dict(colours))
    # and the graduated record, guarded the same way: an unreadable
    # property must never stop the dialog from opening
    raw = layer.customProperty("weavingspace_quant_style")
    if not raw:
      return
    try:
      stored = json.loads(raw)
      field = stored["field"]
      colours = {str(k): str(v)
                 for k, v in stored.get("colours", {}).items()}
      lo, hi = (int(x) for x in stored.get("range", [0, 100]))
    except (ValueError, KeyError, TypeError, AttributeError):
      return
    if not field:
      return
    if colours:
      self._quant_colours.setdefault(tile_id, {}).setdefault(
        field, dict(colours))
    if (lo, hi) != (0, 100) and 0 <= lo <= hi <= 100 \
        and tile_id not in self._ramp_ranges:
      self._ramp_ranges[tile_id] = (lo, hi)
    # The pins, under the same one-unreadable-property-must-not-stop-
    # the-dialog-opening guard as everything above, and under the
    # same gap rule as the colours: only ever filled in where the
    # dialog holds nothing, since anything it holds was chosen since
    # reopening and wins.
    stored_pins = {}
    try:
      for key, value in (stored.get("pinned") or {}).items():
        if key in ("low", "high"):
          stored_pins[str(key)] = float(value)
        elif key == "breaks" and isinstance(value, (list, tuple)):
          stored_pins["breaks"] = [float(x) for x in value]
    except (TypeError, ValueError):
      stored_pins = {}
    if stored_pins:
      self._pinned_bounds.setdefault(tile_id, {}).setdefault(
        field, dict(stored_pins))

  def _adopt_row_symbology(self, layer, tile_id):
    """Read an adopted layer's ramp, class count and colours back.

    Args:
      layer: an existing output layer found in the project, whose
        renderer QGIS restored from the project file.
      tile_id: the element it carries.

    Returns:
      None. Fills in `_ramp_choices`, `_reverse_choices`,
      `_class_counts`, `_single_colours` and, where the ramp cannot be
      named, the positional picks in `_quant_colours` that make the
      row read Custom. Only ever fills a gap: anything the dialog
      already holds for this element was chosen since reopening and
      wins.

    Nothing here raises. A project written by another version, or
    edited by hand, must not stop the dialog opening -- so an
    unreadable renderer leaves the row on its defaults, which is
    exactly the behaviour that existed before this method.
    """
    try:
      renderer = layer.renderer()
    except Exception:
      return
    if renderer is None:
      return

    # A SINGLE SYMBOL is the whole of an unassigned or single-colour
    # element's styling, and the colour is right there on it.
    if hasattr(renderer, "symbol") and not hasattr(renderer, "ranges") \
        and not hasattr(renderer, "categories"):
      try:
        symbol = renderer.symbol()
        if symbol is not None and tile_id not in self._single_colours:
          self._single_colours[tile_id] = symbol.color().name()
      except Exception:
        pass
      return

    named, flipped = None, False
    try:
      # The REVERSE-aware match here, not _ramp_name_matching: a
      # reversed element's renderer carries a clone matching no name,
      # so the exact question would answer None and the row would come
      # back Custom with the tick lost. Recovering the flag is the
      # last thing a project round trip used to drop.
      named, flipped = self._ramp_match(renderer.sourceColorRamp())
    except Exception:
      named, flipped = None, False
    if named and tile_id not in self._ramp_choices:
      self._ramp_choices[tile_id] = named
      # Filed in the same breath and under the same gap rule as the
      # ramp, because the two are one choice: a name recovered without
      # its direction would put the row's combo on a ramp the map runs
      # the other way, which is the table lying about the map.
      if tile_id not in self._reverse_choices:
        self._reverse_choices[tile_id] = flipped

    if not hasattr(renderer, "ranges"):
      # A CATEGORIZED renderer, and until 2026-08-13 this returned
      # here with nothing recovered -- the twin asymmetry again, five
      # lines from the graduated recovery that has worked all along.
      #
      # What it cost: an element whose colours came from an imported
      # QML has a renderer matching no ramp in the library, so `named`
      # is None and the colours ARE the style. Nothing restores
      # `_class_choices` (the file token is stamped nowhere), so on
      # reopen the row read a default ramp with custom=False, and the
      # next Generate re-seeded the element from that ramp and painted
      # the user's imported scheme away. Measured on the map: four
      # file colours before, Set2's four after.
      #
      # The recovery is the maintainer's settled instruction for the
      # whole reopen question -- preserve what we can, and where we
      # cannot, read the classes back off the layer and call the row
      # Custom. Here the classes carry their own VALUES, so the
      # recovery is exact rather than positional: this is the easier
      # half of a rule already applied to the harder one.
      if not hasattr(renderer, "categories"):
        return
      try:
        field = renderer.classAttribute()
        # read values and colours in one pass while the category
        # objects are alive, for the same reason the ranges below are
        # held: a symbol pointer off a dead temporary segfaults
        pairs = [(category.value(), category.symbol().color().name())
                 for category in renderer.categories()]
      except Exception:
        return
      if not field or not pairs:
        return
      if self._category_colours.get(tile_id, {}).get(field):
        return          # the user has picks of their own; do not touch
      if named:
        # A named ramp is not proof that the ramp decides the colours.
        # A categorized renderer built from an imported QML records a
        # source ramp all the same (since 2026-08-13, so that QGIS's
        # own panel can show one), while the template's colours
        # override it -- so returning here on a name recovered nothing
        # for exactly the case that needs it.
        #
        # The question is therefore not "is there a ramp" but "does
        # that ramp explain what is drawn". Ask the real seeding code
        # rather than reproducing its sampling rule here: a
        # reimplementation would agree with itself and not with the
        # map. Equal means the ramp is the style and the row should go
        # on reading its name; different means the colours are the
        # style and the row reads Custom.
        try:
          from_ramp = bridge.make_categorized_renderer(
            layer, field, named, False, None, flipped)
          expected = {str(c.value()): c.symbol().color().name()
                      for c in from_ramp.categories()}
        except Exception:
          expected = None
      else:
        expected = None

      # Recover only the colours the ramp does NOT explain. Recording
      # all of them would be wrong in both directions: an element
      # coloured by an ordinary ramp would come back reading Custom,
      # and an element with ONE hand-picked colour would come back
      # owning five, so the record would stop meaning "what the user
      # chose" and start meaning "what is currently drawn".
      recovered = {}
      for value, colour in pairs:
        # the catch-all category carries no value; it is the one the
        # editor exposes under bridge.NO_DATA_KEY
        blank = value is None or str(value) in ("", "NULL")
        if blank:
          continue
        if expected is not None and expected.get(str(value)) == colour:
          continue
        recovered[str(value)] = colour
      if recovered:
        self._category_colours.setdefault(tile_id, {})[field] = recovered
      return
    try:
      # hold the list while it is read: a range object from ranges()
      # is a temporary, and a symbol pointer off a dead one segfaults
      # (the lesson the constant-column fix paid for)
      bands = [(r.symbol().color().name()) for r in renderer.ranges()]
    except Exception:
      return
    if not bands:
      return

    # The class count, but only where the spinner could hold it. Fifty
    # bands is Quant: Unclassed, whose count is fixed by the scheme
    # rather than chosen, and forcing 50 into a 2..20 spinner would
    # clamp to 20 and quietly describe a different map.
    if 2 <= len(bands) <= 20 and tile_id not in self._class_counts:
      self._class_counts[tile_id] = len(bands)

    if named:
      return
    # No ramp in the library draws these, so the colours ARE the
    # style: keep them positionally and let _sync_row read Custom.
    try:
      field = renderer.classAttribute()
    except Exception:
      return
    if not field:
      return
    if self._quant_colours.get(tile_id, {}).get(field):
      return          # the user has picks of their own; do not touch
    self._quant_colours.setdefault(tile_id, {})[field] = {
      str(index): colour for index, colour in enumerate(bands)}

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

  def _row_for_element(self, tile_id):
    """The table row currently carrying one element, or None.

    Args:
      tile_id: the element to find.

    Returns:
      The row index, or None mid-rebuild. Rows are looked up fresh
      every time because rebuilds recreate them; nothing may cache a
      row number against an element.
    """
    for row in range(self.table.rowCount()):
      item = self.table.item(row, 0)
      if item is not None and item.text() == tile_id:
        return row
    return None

  def _assignment_for(self, tile_id):
    """One element's current assignment dict, or None.

    Args:
      tile_id: the element to find, as it appears in column 0.

    Returns:
      Its dict from ``_assignments()``, read FRESH -- the table is the
      only record, and a rebuild replaces every row -- or None when no
      row carries that element, which happens mid-rebuild and after
      the design has changed under a handler that outlived it. Every
      caller must handle None; none of them may cache the result.

    Why this exists as a method rather than nine copies of one
    generator expression. It was nine copies, and the comparison
    inside them is exactly the kind of thing that goes wrong
    silently: get it wrong and the lookup finds a DIFFERENT element,
    or none at all on a one-element map, and the caller then stamps a
    signature against the wrong id or repaints a window with another
    element's colours. Nothing raises either way. Automatic mutants
    landed on three of the nine copies and every one survived, and
    the three faults were separately invisible until a mutant
    happened to pick that particular copy -- so the copies were not
    nine chances to catch the fault, they were nine places for it to
    hide. Collapsed here, one mutation does the work of nine.
    (2026-08-12.)
    """
    return next((a for a in self._assignments()
                 if a["id"] == tile_id), None)

  def _clear_quant_customization(self, tile_id, because,
                                 reset_range=True):
    """Forget an element's positional class colours, and perhaps its
    display range.

    Args:
      tile_id: the element.
      because: what the user just did, named in the notice ("a new
        colour ramp", "a new class count", "a new display range").
      reset_range: also restore the Ramp Display Range to the whole
        ramp. True only for a ramp choice -- "until reselected anew"
        is the settled rule -- since a scheme or class-count change
        reclassifies the data without saying anything about the ramp.

    Returns:
      None. Says so when anything was actually discarded, quiet
      otherwise. The picks die whenever the ramp is asked anew to
      decide the colours (settled 2026-08-09); only the CURRENT
      field's picks go, since another variable's are still keyed
      under their own name.
    """
    row = self._row_for_element(tile_id)
    var_combo = self.table.cellWidget(row, 1) if row is not None else None
    field = var_combo.currentText() if var_combo else None
    discarded = None
    if field and field != "---":
      discarded = self._quant_colours.get(tile_id, {}).pop(field, None)
    had_window = tuple(
      self._ramp_ranges.get(tile_id, (0, 100))) != (0, 100)
    if reset_range:
      self._ramp_ranges.pop(tile_id, None)
    self._custom_swatch_cache.pop(tile_id, None)
    if discarded:
      self._report_quietly(
        f"Choosing {because} for element '{tile_id}' discarded "
        f"{len(discarded)} class colour(s) you had picked by hand.")
    elif reset_range and had_window:
      self._report_quietly(
        f"Choosing {because} for element '{tile_id}' restored the "
        f"ramp's full display range.")

  def _mirror_quant_customization(self, tile_id):
    """Carry an element's quant customization through a Reverse flip.

    Args:
      tile_id: the element whose Reverse switch was just toggled.

    Returns:
      None. The display window mirrors (lo, hi -> 100-hi, 100-lo), so
      it keeps showing the same segment of colour run the other way,
      and the positional picks swap ends (class i -> k-1-i on k
      classes): a colour picked for the old class 2 of 7 lands on the
      new class 5. Reversing twice therefore restores everything
      exactly -- the involution the tests pin. (Settled 2026-08-09:
      Reverse carries the customization along rather than destroying
      it.)
    """
    row = self._row_for_element(tile_id)
    if row is None or self._row_mode(row) != "Graduated":
      return
    lo, hi = self._ramp_ranges.get(tile_id, (0, 100))
    if (lo, hi) != (0, 100):
      self._ramp_ranges[tile_id] = (100 - hi, 100 - lo)
    var_combo = self.table.cellWidget(row, 1)
    field = var_combo.currentText() if var_combo else None
    picks = self._quant_colours.get(tile_id, {}).get(field or "")
    if picks:
      k_spin = self.table.cellWidget(row, 3)
      count = int(k_spin.value()) if k_spin is not None else 0
      if count > 0:
        self._quant_colours[tile_id][field] = {
          str(count - 1 - int(index)): colour
          for index, colour in picks.items()
          if index.isdigit() and int(index) < count}
    self._custom_swatch_cache.pop(tile_id, None)

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

  def _current_graduated_classes(self, assignment):
    """The classes a graduated element draws right now.

    Args:
      assignment: one dict from ``_assignments()``, already known to
        be Graduated with a variable.

    Returns:
      [(lower, upper, "#rrggbb"), ...] in class order, or [] when no
      layer can answer. Built by asking bridge for the SAME renderer
      the map would get -- range window and positional picks included
      -- so the editor and the swatch cannot disagree with the map.
      Classified against the element's own output layer when one
      exists (its breaks are the map's breaks); against the region
      layer otherwise, which is what lets the editor open before
      anything is generated, at the price the categorical editor
      already accepted: the pre-generation preview may differ
      slightly from the tiled result.
    """
    from qgis.core import QgsGraduatedSymbolRenderer
    project = QgsProject.instance()
    layer = None
    lid = self._element_layer_ids.get(assignment["id"])
    if lid:
      candidate = project.mapLayer(lid)
      if candidate is not None and assignment["var"] in \
          [f.name() for f in candidate.fields()]:
        layer = candidate
    if layer is None:
      layer = self.layer_combo.currentLayer()
    if layer is None or assignment["var"] not in \
        [f.name() for f in layer.fields()]:
      return []
    renderer = bridge.make_graduated_renderer(
      layer, assignment["var"], assignment["ramp"],
      assignment.get("scheme", "Quantiles"), assignment.get("k", 5),
      assignment.get("outline", False),
      assignment.get("reverse", False),
      assignment.get("range_bounds", (0, 100)),
      assignment.get("quant_colours"),
      # the same values the MAP is classified from, or this preview
      # of the row's colours would predict a map drawn from a
      # different sample -- which is the disagreement
      # test_the_preview_agrees_with_the_map_it_predicts hunts
      self._classification_values(assignment["var"]),
      assignment.get("pinned"))
    # iterate the list while it is bound to the loop: range objects
    # from ranges() are temporaries, and a symbol pointer read off a
    # dead one segfaults (the lesson the constant-column fix paid for)
    return [(r.lowerValue(), r.upperValue(), r.symbol().color().name())
            for r in renderer.ranges()]

  def _unworn_stripes(self, tile_id, assignment, stripes):
    """Which swatch stripes stand for classes nothing wears.

    Args:
      tile_id: the element.
      assignment: its dict from ``_assignments()``.
      stripes: how many stripes the swatch will draw, which is the
        class count except on Unclassed, where fifty classes are
        sampled down to eight.

    Returns:
      A list of stripe indices to hatch, empty when every class is
      worn or when the question cannot be answered -- an unknown is
      never drawn as an emptiness.

    Asked of the ELEMENT's own output layer, because the question is
    what THIS element draws rather than what the map as a whole
    holds. Where no output exists yet the region's values answer it,
    which is the same fallback the class preview uses.

    Refused outright when the stripes are a SAMPLE of the classes
    (Unclassed), since a stripe then stands for several classes and
    hatching it would claim more than was measured.
    """
    field = assignment.get("var")
    if not field or assignment.get("mode") != "Graduated":
      return []
    layer_id = self._element_layer_ids.get(tile_id)
    layer = QgsProject.instance().mapLayer(layer_id) if layer_id else None
    renderer = layer.renderer() if layer is not None else None
    if renderer is None or not hasattr(renderer, "ranges"):
      return []
    bounds = [(r.lowerValue(), r.upperValue()) for r in renderer.ranges()]
    if len(bounds) != stripes:
      return []
    index = layer.fields().indexOf(field)
    if index < 0:
      return []
    try:
      return bridge.unworn_classes(bounds, layer.uniqueValues(index))
    except Exception:
      return []

  def _custom_swatch_for(self, tile_id, field):
    """The swatch for one element's Custom display.

    Args:
      tile_id: the element whose ramp cell is reading Custom.
      field: its current variable, named in the cache key so a field
        switch cannot serve another field's colours.

    Returns:
      A QIcon of the first few colours the element actually draws in,
      taken from the SAME renderer the map gets (via
      _current_category_colours or _current_graduated_classes, so the
      swatch cannot disagree with the map). Rebuilt whenever anything
      deciding those colours changes -- the cache key is the pick
      set, the ramp, its direction, and the field, plus the class
      source on a categorized row or the scheme, class count and
      display window on a graduated one -- and reused otherwise,
      because building it constructs a real renderer and _sync_row
      runs on every control change.
    """
    assignment = self._assignment_for(tile_id)
    if assignment is None:
      return _custom_swatch_icon([])
    if assignment["mode"] == "Graduated":
      # positional picks and the display window are what decide a
      # graduated row's colours, so they are the cache key here
      picks = assignment.get("quant_colours") or {}
      pinned = assignment.get("pinned") or {}
      # the pins are IN the key: without them the box would be drawn
      # once and then cached past every later pin and unpin, which is
      # a swatch quietly describing a map that has moved
      key = (field, assignment.get("ramp"), assignment.get("reverse"),
             assignment.get("scheme"), assignment.get("k"),
             tuple(assignment.get("range_bounds", (0, 100))),
             tuple(sorted(picks.items())),
             tuple(sorted((k, tuple(v) if isinstance(v, list) else v)
                          for k, v in pinned.items())),
             # the data's own fingerprint: an edit that empties a
             # class must take the hatching off, and one that fills
             # it must put it back
             self._layer_fingerprint())
      cached = self._custom_swatch_cache.get(tile_id)
      if cached is not None and cached[0] == key:
        return cached[1]
      shades = [colour for _lo, _hi, colour
                in self._current_graduated_classes(assignment)]
      if assignment.get("scheme") == "Unclassed" and len(shades) > 8:
        # fifty slivers would all land in the first eight stripes;
        # sample the window evenly instead, so the swatch shows the
        # whole of what the range selected
        step = (len(shades) - 1) / 7
        shades = [shades[round(j * step)] for j in range(8)]
      # First stripe for a pinned low bound, last for a pinned high
      # one. On Unclassed the fifty classes were sampled down to
      # eight stripes just above, so the boxed stripe reads as "the
      # low end" rather than literally class 0 of fifty -- which is
      # what the pin means there anyway.
      boxed = ([0] if pinned.get("low") is not None else []) + \
              ([-1] if pinned.get("high") is not None else [])
      # ...and which classes nothing wears, asked of the ELEMENT's
      # own layer, since the question is what THIS element draws. A
      # copied ladder is the only ordinary way to get one: the class
      # count is otherwise reduced to the value count, so an empty
      # class cannot arise from a computed classification.
      hatched = self._unworn_stripes(tile_id, assignment, len(shades))
      icon = _custom_swatch_icon(shades, boxed, hatched)
      self._custom_swatch_cache[tile_id] = (key, icon)
      return icon
    picks = assignment.get("category_colours") or {}
    key = (field, assignment.get("ramp"), assignment.get("reverse"),
           assignment.get("class_source"),
           tuple(sorted(picks.items())))
    cached = self._custom_swatch_cache.get(tile_id)
    if cached is not None and cached[0] == key:
      return cached[1]
    colours, order = self._current_category_colours(assignment)
    icon = _custom_swatch_icon(
      [colours[value] for value in order] if order else [])
    self._custom_swatch_cache[tile_id] = (key, icon)
    return icon

  def _watch_element_layer(self, layer, tile_id):
    """Follow QGIS-side symbology edits on one element output layer.

    Args:
      layer: the freshly created or adopted output layer.
      tile_id: the element it carries.

    Returns:
      None. Connects the layer's ``styleChanged`` signal -- which
      QGIS emits both when the styling dock installs a new renderer
      (setRenderer) and when a symbol is edited in place -- to
      _on_layer_style_edited. The connection dies with the layer, and
      element layers are recreated every run, so there is nothing to
      disconnect by hand. The layer is looked up again by id when the
      signal fires, because reacting through a captured wrapper whose
      C++ object died is a crash.
    """
    layer.styleChanged.connect(
      lambda lid=layer.id(), tid=str(tile_id):
        self._on_layer_style_edited(lid, tid))

  def _ramp_match(self, ramp):
    """Name a colour ramp, allowing for one that has been reversed.

    Args:
      ramp: a QgsColorRamp taken from a renderer -- one QGIS restored
        from a project file, or one somebody built in the styling
        dock -- or None.

    Returns:
      ``(name, reversed)``: the name under which this ramp appears in
      the ramp dropdown and whether it is that ramp run the other
      way, or ``(None, False)`` when nothing in the library draws it.
      Compared by the ramp's own serialized properties rather than by
      object identity, because both the dock and the project reader
      hand out clones.

    Why the reversed pass exists. Reversing produces a clone that
    matches no NAME in the library, so a project reopened with a
    reversed element used to come back reading Custom: the colours
    were preserved exactly, and the fact that they came from
    reversing a named ramp was not. The tick a user had set was
    simply gone, and `NOT_YET_RESTORED` in
    test_a_project_round_trip_changes_nothing_a_user_chose named it
    as the last thing a round trip lost.

    The two passes are ordered, and the order is the point: an exact
    match wins before any reversed one is tried, so a ramp that
    happens to equal its own reverse is reported unreversed rather
    than by whichever name the iteration reached first.
    """
    if ramp is None:
      return None, False
    try:
      wanted = (type(ramp).__name__, ramp.properties())
    except Exception:
      return None, False
    for flipped in (False, True):
      for name in self._ramp_names:
        candidate = bridge.get_ramp(name, flipped)
        if candidate is not None and \
            (type(candidate).__name__, candidate.properties()) == wanted:
          return name, flipped
    return None, False

  def _ramp_name_matching(self, ramp):
    """The QgsStyle name of a ramp drawn exactly as the library draws it.

    Args:
      ramp: a QgsColorRamp, or None.

    Returns:
      The name under which an identical ramp appears in the ramp
      dropdown, or None when nothing matches OR when the match is a
      REVERSED clone.

    That last exclusion keeps this the question the styling-dock
    handlers actually ask, which is not "which ramp is this" but "is
    the layer wearing exactly what the dialog would seed from a name
    it can put in the combo". A reversed ramp is not, so those
    handlers go on adopting it as hand-picked colours -- the settled
    fallback, which preserves the map exactly and reads Custom.
    Reopening asks the other question and calls `_ramp_match`.
    """
    name, flipped = self._ramp_match(ramp)
    return None if flipped else name

  def _on_layer_style_edited(self, layer_id, tile_id):
    """React when someone restyles an element layer in QGIS itself.

    Args:
      layer_id: the output layer whose style changed.
      tile_id: the element it carries.

    Returns:
      None. The dialog is not modal to QGIS, so a user can open an
      element layer in the styling dock and recolour it while the
      dialog sits there naming a ramp that no longer decides the map
      -- the exact lie the Custom display exists to prevent. Two
      reactions, chosen by what the dock now holds (user decision,
      2026-08-09):

      * the renderer is a clean classify from a STANDARD ramp (its
        source ramp matches a named ramp, its colours are exactly
        what seeding from that ramp alone would give, and no imported
        class source is in force): the dialog follows -- the row's
        ramp combo moves to that name, which destroys any hand-picks
        through the ordinary handler, notice included;
      * anything else: the changed colours are ADOPTED as hand-picked
        choices for the current field, exactly as reopening a saved
        project adopts stamped colours. The cell reads Custom, the
        colours survive regeneration and travel into the project
        file, and choosing a ramp later destroys them with the
        existing notice rather than silently.

      Our own seeding is ignored twice over: while a run is landing
      its layers ``_task`` is still set (the run is not over until
      its layers exist), and the restyle fast path raises
      ``_applying_style``. Graduated renderers take the same two
      reactions through _graduated_layer_edited (positional picks,
      quantitative-family follows). Only single-symbol and unknown
      renderers are left alone: they survive through the signature
      rule, and the ramp cell makes no claim a recolour could turn
      into a lie.
    """
    from qgis.core import (QgsCategorizedSymbolRenderer,
                           QgsGraduatedSymbolRenderer)
    live = _live_dialog()
    if live is not None and live is not self:
      # a RETIRED instance's connections outlive its retirement,
      # because the layers do; without this gate both dialogs would
      # adopt the same dock edit and the user would be told twice
      return
    if self._applying_style or self._task is not None:
      return
    if self._element_layer_ids.get(tile_id) != layer_id:
      return  # a stale connection from a layer since replaced
    layer = QgsProject.instance().mapLayer(layer_id)
    if layer is None:
      return
    renderer = layer.renderer()
    if isinstance(renderer, QgsGraduatedSymbolRenderer):
      # the graduated mirror of everything below (settled 2026-08-09)
      self._graduated_layer_edited(layer, tile_id, renderer)
      return
    if not isinstance(renderer, QgsCategorizedSymbolRenderer):
      return
    assignment = self._assignment_for(tile_id)
    if assignment is None or assignment["mode"] != "Categorized" \
        or not assignment["var"]:
      return
    if renderer.classAttribute() != assignment["var"]:
      # reclassified on a different field in the dock: the dialog has
      # no record to reconcile that against, so it leaves the work
      # alone (the signature rule already preserves it)
      return
    # what the layer actually draws now, keyed like the dialog's own
    # records (NO_DATA_KEY for the catch-all)
    actual = {}
    for category in renderer.categories():
      value = category.value()
      key = bridge.NO_DATA_KEY if value is None else str(value)
      actual[key] = category.symbol().color().name()
    expected, _order = self._current_category_colours(assignment)
    if expected is None:
      return  # the region layer or its field has gone; nothing to judge
    if all(expected.get(key) == colour for key, colour in actual.items()):
      return  # our own seeding, or an edit that changed nothing

    # a clean classify from a standard ramp? Only without an imported
    # class source -- while a file governs the classes, a dock
    # recolour is a divergence from the file, which is Custom by
    # definition -- and only for a ramp of the CATEGORICAL family.
    # A categorized row auto-swaps quantitative ramps away (_sync_row),
    # so following one would snap the combo to a different ramp while
    # the layer wears the dock's colours: the very lie this handler
    # exists to prevent. Such an edit is adopted as Custom instead.
    name = self._ramp_name_matching(renderer.sourceColorRamp())
    if name is not None and name in bridge.CATEGORICAL_RAMPS \
        and not assignment.get("class_source"):
      trial = bridge.make_categorized_renderer(
        layer, assignment["var"], name, assignment["outline"])
      trial_colours = {
        str(c.value()): c.symbol().color().name()
        for c in trial.categories() if c.value() is not None}
      dock_colours = {key: colour for key, colour in actual.items()
                      if key != bridge.NO_DATA_KEY}
      if dock_colours == trial_colours:
        # cleared here as well as in the combo handler, because when
        # the dock re-applied the ramp the dialog already names,
        # setCurrentText below fires no signal and the picks would
        # outlive the clean ramp the layer now wears
        self._clear_category_colours(tile_id, "a new colour ramp")
        for row in range(self.table.rowCount()):
          item = self.table.item(row, 0)
          combo = self.table.cellWidget(row, 4)
          if item is not None and item.text() == tile_id \
              and combo is not None and hasattr(combo, "findText") \
              and combo.findText(name) >= 0:
            # the ordinary handler runs: it records the choice and
            # destroys any hand-picks, with the standing notice
            combo.setCurrentText(name)
            break
        self._report_quietly(
          f"Element '{tile_id}' now follows the '{name}' ramp chosen "
          f"in QGIS.")
        # refresh explicitly: when the dock re-applied the ramp the
        # combo already named, no combo signal ran to do it
        self._refresh_preview_colours()
        # the layer already wears this exact style, so the element is
        # marked as seeded and the next restyle leaves it in peace
        refreshed = self._assignment_for(tile_id)
        if refreshed is not None:
          self._last_signatures[tile_id] = self._signature(refreshed)
          # and the LAYER is told the picks are gone, which is the
          # half this branch never did. The dicts were cleared and
          # the user was told the ramp now governs, while the stamp
          # went on holding the discarded colours -- and the stamp is
          # what survives into the .qgz. So the pick came back on
          # reopen, silently painted over the ramp the user had
          # chosen instead, and `_last_signatures` above guaranteed
          # no restyle would ever heal it. `_stamp_category_colours`
          # clears each property when there is nothing to record,
          # which is exactly this case; its two ADOPT exits called it
          # and these two FOLLOW exits did not. Measured 2026-08-13.
          # Guarded by test_a_discarded_pick_does_not_come_back.
          # the CATEGORIZED half of this branch
          self._stamp_category_colours(layer, refreshed)
        return

    # adopt the divergent colours as hand-picks for the current field
    field = assignment["var"]
    record = self._category_colours.setdefault(tile_id, {}) \
        .setdefault(field, {})
    adopted = 0
    for key, colour in actual.items():
      if expected.get(key) != colour and record.get(key) != colour:
        record[key] = colour
        adopted += 1
    if not adopted:
      return
    self._custom_swatch_cache.pop(tile_id, None)
    # the layer already wears these colours; recording the new
    # signature stops the restyle path re-seeding it, which would
    # discard any OTHER refinement the dock applied alongside them
    refreshed = self._assignment_for(tile_id)
    if refreshed is not None:
      self._last_signatures[tile_id] = self._signature(refreshed)
      self._stamp_category_colours(layer, refreshed)
    self._report_quietly(
      f"Element '{tile_id}' keeps the {adopted} colour(s) set in "
      f"QGIS; its ramp cell now reads Custom.")
    self._refresh_preview_colours()

  def _graduated_layer_edited(self, layer, tile_id, renderer):
    """React to a styling-dock edit of a GRADUATED element layer.

    Args:
      layer: the element output layer whose style changed.
      tile_id: the element it carries.
      renderer: its QgsGraduatedSymbolRenderer, already checked.

    Returns:
      None. The graduated mirror of the categorized watcher, settled
      2026-08-09: a clean classify from a named QUANTITATIVE ramp --
      source ramp recognisable, colours exactly the plugin's own
      full-window seeding -- is FOLLOWED (combo moves, range resets,
      picks destroyed with the notice); any other divergence is
      ADOPTED as positional picks, so the cell reads Custom and the
      colours survive regeneration. Categorical-family ramps never
      follow, because a graduated row auto-swaps them away and the
      combo would land elsewhere than the layer. A dock edit that
      changed the CLASS COUNT or the field is a reclassification the
      dialog has no record to reconcile against, so it is left alone
      -- the signature rule preserves it, as it always has. That
      count is measured against what the plugin would DRAW, not
      against the row's ``k``: the two differ whenever a column has
      fewer distinct values than the row asks classes for.
    """
    assignment = self._assignment_for(tile_id)
    if assignment is None or assignment["mode"] != "Graduated" \
        or not assignment["var"]:
      return
    if renderer.classAttribute() != assignment["var"]:
      return
    ranges = renderer.ranges()
    actual = [r.symbol().color().name() for r in ranges]
    if not actual:
      return
    # The count is compared against what the plugin would DRAW, below,
    # and not against the row's `k`. Those are two different numbers
    # whenever the column has fewer distinct values than the row asks
    # classes for: `k` is the ask, the map honestly draws fewer, and a
    # guard reading the ask rejected every dock edit on such an
    # element -- adoption stopped silently and the user's recolour was
    # thrown away by the next restyle. Found on 2026-08-14 by
    # test_a_graduated_dock_refinement_survives_the_next_restyle, one
    # commit after the reduction it is about.
    expected = [colour for _lo, _hi, colour
                in self._current_graduated_classes(assignment)]
    if actual == expected:
      return  # our own seeding, or an edit that changed nothing
    if len(expected) != len(actual):
      # THE count guard, and the only one: the layer against what the
      # plugin would draw for this row. A CONSTANT column is
      # deliberately collapsed to one class here, while QGIS's own
      # Classify button happily returns five identical "7 - 7" ranges
      # over the same data. Five against one, both agreeing that k is
      # five -- which is why comparing either against `k` answers the
      # wrong question. The positional walk below then ran off the end
      # of the shorter list, inside a slot on rendererChanged -- so
      # the traceback went to a console nobody had open and adoption
      # quietly stopped for that element.
      # A reclassification the dialog has no matching record for is
      # left alone, exactly as a changed class count is; the
      # signature rule preserves it. Guarded by
      # test_a_dock_classify_on_a_constant_column_does_not_crash.
      return

    name = self._ramp_name_matching(renderer.sourceColorRamp())
    if name is not None and name not in bridge.CATEGORICAL_RAMPS:
      trial = bridge.make_graduated_renderer(
        layer, assignment["var"], name, assignment.get("scheme",
                                                       "Quantiles"),
        assignment.get("k", 5), assignment.get("outline", False),
        classify_from=self._classification_values(assignment["var"]))
      # hold the list; range temporaries dangle (the settled lesson)
      trial_colours = [r.symbol().color().name()
                       for r in trial.ranges()]
      if actual == trial_colours:
        # cleared here as well as in the combo handler, for the same
        # reason as the categorized branch: re-applying the ramp the
        # dialog already names fires no combo signal
        self._clear_quant_customization(tile_id, "a new colour ramp")
        row = self._row_for_element(tile_id)
        combo = (self.table.cellWidget(row, 4)
                 if row is not None else None)
        if combo is not None and hasattr(combo, "findText") \
            and combo.findText(name) >= 0:
          combo.setCurrentText(name)
        self._report_quietly(
          f"Element '{tile_id}' now follows the '{name}' ramp chosen "
          f"in QGIS.")
        self._refresh_preview_colours()
        refreshed = self._assignment_for(tile_id)
        if refreshed is not None:
          self._last_signatures[tile_id] = self._signature(refreshed)
          # and the LAYER is told the picks are gone, which is the
          # half this branch never did. The dicts were cleared and
          # the user was told the ramp now governs, while the stamp
          # went on holding the discarded colours -- and the stamp is
          # what survives into the .qgz. So the pick came back on
          # reopen, silently painted over the ramp the user had
          # chosen instead, and `_last_signatures` above guaranteed
          # no restyle would ever heal it. `_stamp_category_colours`
          # clears each property when there is nothing to record,
          # which is exactly this case; its two ADOPT exits called it
          # and these two FOLLOW exits did not. Measured 2026-08-13.
          # Guarded by test_a_discarded_pick_does_not_come_back.
          # the GRADUATED half of this branch
          self._stamp_category_colours(layer, refreshed)
        return

    # adopt the divergent classes as positional picks
    field = assignment["var"]
    record = self._quant_colours.setdefault(tile_id, {}) \
        .setdefault(field, {})
    adopted = 0
    for index, colour in enumerate(actual):
      if expected[index] != colour and record.get(str(index)) != colour:
        record[str(index)] = colour
        adopted += 1
    if not adopted:
      return
    self._custom_swatch_cache.pop(tile_id, None)
    # the layer already wears these colours; recording the signature
    # stops the restyle path re-seeding it and discarding whatever
    # else the dock changed alongside them
    refreshed = self._assignment_for(tile_id)
    if refreshed is not None:
      self._last_signatures[tile_id] = self._signature(refreshed)
      self._stamp_category_colours(layer, refreshed)
    self._report_quietly(
      f"Element '{tile_id}' keeps the {adopted} colour(s) set in "
      f"QGIS; its ramp cell now reads Custom.")
    self._refresh_preview_colours()

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
    """Open the colour editor for the row that asked.

    Returns:
      None. One button, two destinations: a categorized row opens the
      editor's categorical mode here, and a graduated row is handed
      to _edit_quant_colours, which opens the SAME window in its
      graduated dress. Either way colours picked are recorded against
      the element AND the field, applied through the ordinary restyle
      path, and checked for separability once when the window closes.

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
    assignment = self._assignment_for(tile_id)
    if assignment is None or not assignment["var"] \
        or assignment["mode"] not in ("Categorized", "Graduated"):
      return
    field = assignment["var"]

    if assignment["mode"] == "Graduated":
      self._edit_quant_colours(tile_id, field, assignment)
      return

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

  def _edit_quant_colours(self, tile_id, field, assignment):
    """Open the colour editor in its graduated mode.

    Args:
      tile_id: the element being edited.
      field: its numeric variable.
      assignment: its dict from ``_assignments()``.

    Returns:
      None. The same window as the categorical editor, in its
      graduated dress: two read-only bound columns, editable class
      colours keyed by POSITION, and the Ramp Display Range section
      live at the top. For Quant: Unclassed the class list is shown
      locked and translucent -- fifty slivers are a preview, not an
      editing surface -- and the range alone is live (settled
      2026-08-09). Everything flows through the dialog's records and
      the ordinary restyle path, exactly as the categorical mode
      does, so it is equally safe while a run is in flight.
    """
    classes = self._current_graduated_classes(assignment)
    if not classes:
      self._report_quietly(
        f"'{field}' has no classes to colour in this layer.")
      return
    unclassed = assignment.get("scheme") == "Unclassed"
    order = [str(index) for index in range(len(classes))]
    colours = {str(index): colour
               for index, (_lo, _hi, colour) in enumerate(classes)}
    bounds = [(lower, upper) for (lower, upper, _c) in classes]

    def picked(index, colour):
      # positional: "class 3 is this colour", surviving break moves
      self._quant_colours.setdefault(tile_id, {}) \
          .setdefault(field, {})[str(index)] = colour
      self._apply_style_change()

    def range_changed(lo, hi):
      # moving the range reinterpolates every class, so the picks go
      # (settled; the notice fires only when there were any). The
      # fresh colours are handed back for the editor to repaint with.
      self._clear_quant_customization(
        tile_id, "a new display range", reset_range=False)
      self._ramp_ranges[tile_id] = (int(lo), int(hi))
      self._custom_swatch_cache.pop(tile_id, None)
      self._apply_style_change()
      refreshed = self._assignment_for(tile_id)
      if refreshed is None:
        return []
      return [colour for _lo, _hi, colour
              in self._current_graduated_classes(refreshed)]

    def pin_changed(which, value):
      # The editor asks; the dialog decides. A message back means
      # REFUSED and the editor puts its control where it was, so the
      # window never shows a bound the map does not have -- reverting
      # rather than clamping, because a typed number is either
      # honoured or visibly rejected and never quietly changed into a
      # different one.
      wanted = dict(self._pinned_bounds.get(tile_id, {}).get(field) or {})
      if value is None:
        wanted.pop(which, None)
      else:
        wanted[which] = float(value)
      source = self._classification_values(field)
      values = (source.uniqueValues(source.fields().indexOf(field))
                if source is not None else [])
      problem = bridge.pin_problem(
        wanted.get("low"), wanted.get("high"), values,
        assignment.get("k", 5))
      if problem:
        self._report_quietly(problem)
        return problem
      if wanted:
        self._pinned_bounds.setdefault(tile_id, {})[field] = wanted
      else:
        self._pinned_bounds.get(tile_id, {}).pop(field, None)
      self._custom_swatch_cache.pop(tile_id, None)
      self._apply_style_change()
      return None

    editor = CategoryColourDialog(
      tile_id, field, order, colours, picked, self,
      bounds=bounds, locked=unclassed,
      range_bounds=tuple(self._ramp_ranges.get(tile_id, (0, 100))),
      ramp_name=assignment["ramp"],
      reverse=assignment.get("reverse", False),
      range_changed=range_changed,
      pinned=self._pinned_bounds.get(tile_id, {}).get(field),
      pin_changed=pin_changed,
      copy_targets=self._copy_targets(tile_id),
      copy_to=lambda target: self._copy_classification(tile_id, target))
    editor.exec()
    self._warn_about_close_colours()

  def _copy_classification(self, source_id, target_id):
    """Send one element's whole classification to another.

    Args:
      source_id: the element whose editor is open.
      target_id: the element to copy onto.

    Returns:
      A message when the copy was REFUSED, or None when it was made.
      Refusals are rare: a target that has since lost its variable,
      or a source with no classes to send.

    WHAT TRAVELS: the class breaks, the colours, the class count, the
    style (so an Unclassed source makes its target Unclassed, which
    is the only way "breaks and number of classes" can be honoured in
    both directions) and the PIN FLAGS. The flags travel separately
    from the values, and that difference is what makes a copy behave:
    copying from an element with no pins leaves the target's breaks
    hand-set and neither end pinned, so its swatch draws no box.
    Collapsing the two would make every copy look fully pinned and
    leave "unpin" with nothing coherent to do (settled 2026-08-14).

    The receiving element's own extremes fit the ends, in
    bridge.fitted_breaks; classes its data cannot reach are KEPT and
    hatched rather than dropped.

    What was replaced is REPORTED rather than asked about, which is
    how every other loss in this plugin is handled.
    """
    source = self._assignment_for(source_id)
    target = self._assignment_for(target_id)
    if source is None or target is None or not target.get("var"):
      return "That element has no variable to classify."
    classes = self._current_graduated_classes(source)
    if not classes:
      return "This element has no classes to copy."
    # the INTERIOR boundaries: the outer edges belong to whichever
    # column receives them, which is what fitted_breaks decides
    interior = [upper for _lo, upper, _c in classes[:-1]]
    if not interior:
      return "A single class has no breaks to copy."

    # ...what the target is about to lose, named before it goes
    field = target["var"]
    lost = []
    if self._quant_colours.get(target_id, {}).get(field):
      lost.append("its hand-picked colours")
    if self._pinned_bounds.get(target_id, {}).get(field):
      lost.append("its pinned bounds")
    if self._class_counts.get(target_id) not in (None, source.get("k")):
      lost.append(f"its class count of {self._class_counts[target_id]}")

    # THE STYLE GOES FIRST, and the order is not cosmetic: putting a
    # row on another style releases any copied ladder it carries (a
    # copy is made for one scheme and one count), so setting the
    # style AFTER writing the record made the copy release the very
    # ladder it had just written. Measured, 2026-08-14: the copy
    # reported success and changed nothing on the map.
    self._copy_style_to_row(target_id, source.get("mode_raw"))
    record = {"breaks": [float(b) for b in interior]}
    # the FLAGS, copied as flags: which ends the source had pinned,
    # not merely that its breaks are now hand-set
    source_pins = self._pinned_bounds.get(source_id, {}).get(
      source.get("var")) or {}
    for end in ("low", "high"):
      if source_pins.get(end) is not None:
        record[end] = float(source_pins[end])
    self._pinned_bounds.setdefault(target_id, {})[field] = record

    # the colours, positionally, which is what makes the row Custom
    self._quant_colours.setdefault(target_id, {})[field] = {
      str(index): colour for index, (_lo, _hi, colour) in enumerate(classes)}
    self._class_counts[target_id] = len(classes)
    self._ramp_choices[target_id] = source.get("ramp")
    self._reverse_choices[target_id] = bool(source.get("reverse"))
    self._custom_swatch_cache.pop(target_id, None)
    self._apply_style_change()
    self._report_quietly(
      f"Element '{target_id}' now uses the classes from element "
      f"'{source_id}'"
      + (f", replacing {' and '.join(lost)}." if lost else "."))
    return None

  def _copy_style_to_row(self, tile_id, mode_raw):
    """Put a target row's Style cell on the source's entry.

    Args:
      tile_id: the element receiving the copy.
      mode_raw: the source row's literal Style text, e.g.
        "Quant: Unclassed".

    Returns:
      None. The style travels with the breaks, because fifty
      hand-set breaks on a row whose spinner caps at twenty is the
      three-numbers-for-one-setting fault
      test_an_unclassed_excursion_leaves_the_count_alone guards.
      Driven through the combo's own ``activated`` signal, which is
      what marks a style as the user's choice: a bare setCurrentText
      leaves the next design rebuild free to revert it.
    """
    row = self._row_for_element(tile_id)
    combo = self.table.cellWidget(row, 2) if row is not None else None
    if combo is None or not hasattr(combo, "findText") or not mode_raw:
      return
    index = combo.findText(mode_raw)
    if index < 0:
      return
    combo.setCurrentIndex(index)
    combo.activated.emit(index)

  def _release_copied_breaks(self, tile_id, because):
    """Drop a copied ladder, keeping the pins that came with it.

    Args:
      tile_id: the element whose classification is being recomputed.
      because: what the user just did, named in the notice.

    Returns:
      None. Says so only when something was actually released.

    A COPY DEGRADES TO ITS PINS rather than to nothing. The copied
    boundary VALUES were chosen for a particular class count and a
    particular set of breaks, so a new count retires them; the pin
    FLAGS and the two bounds they name are a smaller and more durable
    statement, and they survive, with the scheme recomputing the
    middle around them. That is the pin mechanism doing exactly its
    job, and it is why the record holds the two separately (settled
    2026-08-14).
    """
    for field, record in list(
        self._pinned_bounds.get(tile_id, {}).items()):
      if not record.get("breaks"):
        continue
      kept = {key: value for key, value in record.items()
              if key in ("low", "high")}
      if kept:
        self._pinned_bounds[tile_id][field] = kept
      else:
        self._pinned_bounds[tile_id].pop(field, None)
      self._custom_swatch_cache.pop(tile_id, None)
      self._report_quietly(
        f"Element '{tile_id}' had classes copied from another element, "
        f"and {because} recomputes them"
        + (". Its pinned bounds are kept." if kept else "."))

  def _copy_targets(self, source_id):
    """The elements this one's classification may be copied to.

    Args:
      source_id: the element whose editor is open.

    Returns:
      [(tile_id, label)] in table order: every OTHER element carrying
      a variable and drawn by a quantitative style, categorized rows
      excluded because a class ladder means nothing to them. An
      element with no variable is left out too, having no column to
      classify. Empty when there is nobody to copy to, and the editor
      then builds no dropdown at all rather than offering a control
      that can do nothing.
    """
    targets = []
    for assignment in self._assignments():
      tile_id = assignment.get("id")
      if tile_id == source_id or not assignment.get("var"):
        continue
      if assignment.get("mode") != "Graduated":
        continue
      targets.append((tile_id, f"{tile_id} \u2013 {assignment['var']}"))
    return targets

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
    # through the gated helper, like every consumer of this opinion:
    # the box check above only saves building the fills
    note = self._legibility_note(fills, self._assignments())
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
      * ``k`` — class count (50 and greyed for "Unclassed"), as the
        SPINNER shows it. A column cannot be cut into more classes
        than it has distinct values, but that reduction belongs to
        make_graduated_renderer at the moment it classifies, not
        here: this is the record of what the user ASKED for, and a
        row whose record disagreed with its own cell is what
        test_an_unclassed_excursion_leaves_the_count_alone caught
        when the reduction was briefly made in this block
        (2026-08-14). On a CATEGORIZED row the cell displays the
        detected category count but ``k`` carries the row's
        remembered graduated count, 5 by default: the spin box is
        disabled there, so nothing writes the displayed number into
        ``user_k``. Harmless downstream, since seed_renderer reads
        ``k`` only for Graduated, but this block said the count was
        the detected one until 2026-08-12
      * ``outline`` — draw tile boundaries
      * ``class_source`` — where a categorized row's colours come
        from: None for automatic, else a "file:<path>" or
        "layer:<id>" token
      * ``quant_colours`` — a graduated row's positional class
        picks, {class index as str: "#rrggbb"}; None off graduated
        rows or when the current field has none
      * ``range_bounds`` — the Ramp Display Range as (lo, hi)
        percent; (0, 100) means the whole ramp, and is what
        non-graduated rows always carry
      * ``class_choice`` — the raw combo value, kept so the choice
        survives a table rebuild
      * ``pinned`` — class bounds set by hand, as ``{"low": float,
        "high": float}`` with either key absent, or None. ``low`` is
        the first class's upper bound and ``high`` is the last
        class's lower bound; the classifier cuts the row's count
        minus one class per pin and the pinned classes are put back
        around the result (bridge.make_graduated_renderer)
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
        # ...and so does what is INSIDE it, which the token alone
        # cannot say. See _class_source_stamp.
        "class_source_stamp": (
          self._class_source_stamp(source) if mode == "Categorized"
          else None),
        "class_choice": choice,
        # Class bounds set by hand, for this element AND this field.
        # Graduated only: a categorical element has no bounds to pin.
        "pinned": (self._pinned_bounds.get(tid_text, {}).get(var)
                   if mode == "Graduated" and var else None),
        # Colours chosen by hand for this element AND this field. A
        # different variable in the same element has its own set, so
        # switching away and back restores rather than discards.
        "category_colours": (
          self._category_colours.get(tid_text, {}).get(var)
          if mode == "Categorized" and var else None),
        # Positional class colours and the ramp's display window,
        # both graduated-only. The range rides every graduated row so
        # seeding never has to guess a default.
        "quant_colours": (
          self._quant_colours.get(tid_text, {}).get(var)
          if mode == "Graduated" and var else None),
        "range_bounds": (
          tuple(self._ramp_ranges.get(tid_text, (0, 100)))
          if mode == "Graduated" else (0, 100)),
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

  def _on_style_changed(self, mode_combo):
    """Destroy positional picks when a row's break method changes.

    Args:
      mode_combo: the style chooser whose index just moved.

    Returns:
      None. A changed scheme reclassifies the column, so positional
      picks name classes that no longer exist: they are destroyed,
      with the standing notice (settled 2026-08-09). Compared against
      the last style seen so nothing fires when the index merely
      resettles on the same entry; the display range survives,
      because it says nothing about the classification, only about
      the ramp. Crossing to or from a non-quant style counts too --
      Categorized and back is two reclassifications, not none.
    """
    was = mode_combo.property("last_style")
    now_style = mode_combo.currentText()
    mode_combo.setProperty("last_style", now_style)
    tid_here = mode_combo.property("tile_id")
    if tid_here and was is not None and now_style != was and \
        (now_style in self.GRAD_SCHEMES or was in self.GRAD_SCHEMES):
      self._clear_quant_customization(
        tid_here, "a new style", reset_range=False)

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
    # A copied ladder was copied for a particular SCHEME as well as a
    # particular count, so choosing another retires its values -- and
    # keeps the pins that came with them, which is the whole reason
    # the record holds the two apart.
    for row in range(self.table.rowCount()):
      if self.table.cellWidget(row, 2) is mode_combo:
        item = self.table.item(row, 0)
        if item is not None:
          self._release_copied_breaks(item.text(), "a new class style")
        break
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
      # UNASSIGNED FIRST, in the same order `seed_renderer` uses, and
      # the order is the whole of it. The map asks `if not var` before
      # anything else and paints NO_DATA; this asked about the MODE
      # first, and an element left on "---" defaults to Single colour
      # and keeps a colour button -- so the preview showed that colour
      # while the map drew grey. The preview exists to judge a design
      # before committing to it, so a quarter of the pattern being
      # judged in a colour the map never paints is the preview failing
      # at its one job. Measured 2026-08-13: preview #e7342a against a
      # map drawing (221, 221, 221). Guarded by
      # test_an_unassigned_element_previews_as_it_draws.
      if not a["var"]:
        base = bridge.NO_DATA_FILL
      elif a["mode"] == "Single colour" and a.get("single_colour"):
        base = a["single_colour"]
      else:
        base = bridge.ramp_swatch_colour(a["ramp"])
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

    # Class sources are loaded once per distinct token, as a full run
    # does. A file that cannot be read leaves its element ALONE and is
    # reported, which is the settled behaviour for a class source that
    # goes away: the map is not thrown away and the colours are not
    # reset, because a missing file is a reason to stop consulting the
    # file rather than a reason to repaint somebody's map
    # (test_a_class_source_that_moves_after_the_map_is_drawn).
    #
    # This path used to swallow the failure into `templates[token] =
    # None` and seed from nothing, so nudging any style control after
    # moving a QML repainted the element in automatic colours, with no
    # notice and the cell still naming the file. The re-tile twin five
    # hundred lines below collected the same failure into
    # `template_errors` and warned. Measured 2026-08-13.
    templates, template_errors, unreadable = {}, [], set()
    for token in {a.get("class_source") for a in assignments.values()
                  if a.get("class_source")}:
      try:
        templates[token] = (
          bridge.template_from_layer(project.mapLayer(token[6:]))
          if token.startswith("layer:")
          else bridge.load_categorized_template(token[5:]))
      except Exception as e:
        unreadable.add(token)
        template_errors.append(f"{token.split(':', 1)[1][-40:]}: {e}")

    changed = []
    # the flag keeps _on_layer_style_edited from mistaking this very
    # seeding for a styling-dock edit and adopting our own colours
    self._applying_style = True
    try:
      for tid, layer in layers.items():
        a = assignments[tid]
        signature = self._signature(a)
        if self._last_signatures.get(tid) == signature:
          continue  # this element is already wearing what it should
        if a.get("class_source") in unreadable:
          # The scheme this element draws from cannot be read, so it
          # KEEPS THE COLOURS IT IS WEARING. Everything else about the
          # element is still honoured -- the opacity below is usually
          # the very change that brought us here -- because refusing
          # that too would turn one unreadable file into a row whose
          # controls do nothing.
          pass
        else:
          bridge.seed_renderer(
            layer, a, templates.get(a.get("class_source")),
            self._classification_values(a.get("var")) if a.get("var")
            else None)
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
    finally:
      self._applying_style = False

    if changed and self.iface is not None:
      self.iface.messageBar().pushSuccess(
        "WeavingSpace",
        f"restyled {', '.join(changed)} (no re-tiling needed)")
    if template_errors:
      # the same words the re-tile path uses, so a user who meets this
      # on either path is told the same thing about the same file
      self._report_quietly(
        "Could not read the class colours file, so these elements "
        "keep their colours: " + "; ".join(template_errors))
    # A class count the column cannot support is reported HERE as well
    # as on the run path, and this is the path that usually meets it:
    # moving the Classes spinner is a style-only change, so it is
    # answered by a restyle and never reaches the run's notices at
    # all. Saying it on one path only is the twin asymmetry this
    # project has now paid for several times over. Deduplicated by
    # field, because several elements may carry the same column.
    said = set()
    for tid in changed:
      a = assignments[tid]
      field = a.get("var")
      if not field or a.get("mode") != "Graduated" or field in said:
        continue
      note = bridge.few_values_message(
        field, self._numeric_value_count(field),
        a.get("k", 5))
      if note is not None:
        said.add(field)
        self._report_quietly(note)
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
      # The three STYLE items at the end are the ones _signature
      # carries, and they are here for a reason measured on
      # 2026-08-13: the live tick RETURNS on an unchanged signature
      # WITHOUT reaching _restyle_only, so anything missing from this
      # tuple can never be applied on the live path at all. A
      # hand-picked colour changed with live update on, and nothing
      # else touched, was simply swallowed -- the editor and the
      # table both showing it as applied while the map went on
      # without it. Including them costs nothing: the geometry
      # signature is unchanged, so the run that follows is a restyle
      # in place rather than a tiling. Guarded by
      # test_a_pick_is_not_swallowed_by_the_live_path.
      tuple((a["id"], a["var"], a["mode"], a["ramp"], a["scheme"],
             a["k"], a["outline"], a["class_source"],
             a.get("class_source_stamp"),
             a.get("single_colour"), a.get("reverse", False),
             a.get("opacity", 100),
             tuple(sorted((a.get("category_colours") or {}).items())),
             tuple(sorted((a.get("quant_colours") or {}).items())),
             # a copied ladder puts a LIST in this record, and a
             # tuple holding a list cannot be hashed; a signature
             # nobody can hash is one nobody may put in a set
             tuple(sorted(
               (key, tuple(value) if isinstance(value, list) else value)
               for key, value in (a.get("pinned") or {}).items())),
             tuple(a.get("range_bounds", (0, 100))))
            for a in self._assignments()),
      # See _geometry_signature: live update compares this tuple to
      # decide a run would be a no-op, and an edit to the layer must
      # not look like one.
      self._layer_fingerprint(), self._data_version,
    )

  def _class_source_stamp(self, token):
    """What is INSIDE a class-source file, cheaply enough to ask on
    every debounce tick.

    Args:
      token: an element's ``class_source`` -- ``file:<path>`` for a
        QML, ``layer:<id>`` for a donor layer, or None/"" for none.

    Returns:
      For a QML, ``(token, (mtime_ns, size))``; for anything else the
      token unchanged. The value goes into both signatures, so editing
      the file moves them and the element is re-seeded.

    Why this exists: the signatures carried the TOKEN alone, so a
    scheme rewritten on disk left every signature equal. Pressing
    Generate repainted nothing and said nothing, and the user got
    their old colours back with no indication why. Measured
    2026-08-13.

    Why a MISSING file deliberately does not move the stamp: the last
    reading is returned instead. Losing the file is not an edit, and
    the settled behaviour when a class source goes away is to keep the
    map and stop consulting the file, telling the user once
    (test_a_class_source_that_moves_after_the_map_is_drawn). Letting
    the disappearance move the signature would re-seed the element
    from nothing, which is exactly the repaint that behaviour exists
    to prevent.

    Why mtime and size rather than a hash: this is asked on every
    debounce tick, and a hash means reading the whole file each time
    to answer a question whose wrong answer costs one extra restyle.
    A rewrite that preserves both is possible in principle and has no
    consequence a user would notice.
    """
    if not token or not token.startswith("file:"):
      return token
    path = token[5:]
    try:
      info = os.stat(path)
      stamp = (info.st_mtime_ns, info.st_size)
      self._class_source_stamps[token] = stamp
    except OSError:
      stamp = self._class_source_stamps.get(token)
    return (token, stamp)

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
    quant = a.get("quant_colours") or {}
    return (a["var"], a["mode"], a["ramp"], a["scheme"], a["k"],
            a["outline"], a.get("class_source"),
            # the file's CONTENTS, not merely its name: see
            # _class_source_stamp
            a.get("class_source_stamp"), a.get("single_colour"),
            a.get("reverse", False), a.get("opacity", 100),
            tuple(sorted(picked.items())),
            # graduated customization is symbology like everything
            # else here: positional picks, the display window and the
            # pinned bounds all re-seed exactly the elements they
            # changed. A pin missing from here would be recorded and
            # never drawn, which is what the display range was
            # measured doing on 2026-08-13.
            tuple(sorted(quant.items())),
            # a copied ladder puts a LIST in this record, and a
            # tuple holding a list cannot be hashed; a signature
            # nobody can hash is one nobody may put in a set
            tuple(sorted(
              (key, tuple(value) if isinstance(value, list) else value)
              for key, value in (a.get("pinned") or {}).items())),
            tuple(a.get("range_bounds", (0, 100))))

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
    # An inset large enough to swallow elements is checked BEFORE the
    # variable guard below, because when it has taken all of them the
    # table is empty and that guard fires -- telling the user to
    # assign a variable to a design that no longer has anywhere to put
    # one. The inset is what they changed and the inset is what the
    # sentence should name. Where it has taken only SOME, the
    # survivors are slivers and the library's overlay refuses them, so
    # this refusal replaces a modal quoting geopandas internals.
    #
    # Asked only when the inset is actually set, so that a design
    # losing elements for some other reason is never blamed on a
    # control the user left alone. With no inset the two counts agree
    # for every design in the catalogue: 247 of 247, measured
    # 2026-08-13, which is what makes the comparison safe to gate a
    # refusal on.
    collapse = bridge.inset_collapse_message(
      int(self.n_combo.currentData() or 0), len(self._tile_ids()),
      self.mod_t_inset.value()) if self.mod_t_inset.value() else None
    if collapse is not None:
      if not live:
        QMessageBox.warning(self, "WeavingSpace", collapse)
      else:
        self._report_quietly(collapse)
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
      # live runs report quietly, like every other failure on this
      # path. This one popped a modal on the debounced path until
      # 2026-08-12: CLAUDE.md forbids unconditional modal dialogs on
      # generation paths (one hung the suite for thirty-one minutes),
      # and _generate's own docstring says a live run fails silently
      # where a button press would pop a box. Two branches did not.
      if live:
        self._report_quietly(f"Could not read the layer: {e}")
      else:
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
          else:
            # The same rule at n > 1: the row asked for more classes
            # than the column has values, so the map draws fewer than
            # the spinner shows. Counted from the REGION layer, which
            # is what _assignments reduced against, so the sentence
            # cannot disagree with the map it describes -- and said
            # only where the constant notice did not already say it,
            # since one value is this rule's n == 1 instance and two
            # sentences about one column is one too many.
            note = bridge.few_values_message(
              field, self._numeric_value_count(field),
              assignment.get("k", 5))
            if note is not None:
              said_constant.add(field)
              self._report_quietly(note)
          # Gaps in the column, counted from the REGION LAYER, because
          # the sentence says "areas" and must mean the user's areas:
          # counting the tiled frame here once produced "31 of 96
          # areas" for a layer of twenty-four, and the reader went
          # looking for areas they do not have. The breaks already
          # exclude the nulls (see bridge.make_graduated_renderer);
          # this is the half the user can read, and what gives them a
          # chance of understanding if QGIS's own Classify button
          # later moves every break by counting nulls as zero.
          index = layer.fields().indexOf(field) \
            if self._source_layer_alive(layer) else -1
          if index < 0:
            continue
          missing = sum(
            1 for feature in layer.getFeatures()
            if feature[field] is None or str(feature[field]) == "NULL")
          note = bridge.missing_values_message(
            field, missing, int(layer.featureCount()))
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
      None. The live-dialog record (see _set_live_dialog, which keeps
      it on the QApplication so a plugin RELOAD cannot forget it) is
      left pointing at this dialog. The predecessor is recognised by
      identity, never by isinstance: after a reload it is an instance
      of a different class object with the same name, and an
      isinstance test would quietly decide there was nothing to
      retire.
    """
    previous = _live_dialog()
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
    _set_live_dialog(self)

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
        # adopted layers are watched like freshly made ones, so a
        # styling-dock edit reaches the dialog here too
        self._watch_element_layer(layer, str(tid))
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
      live: whether this run came from the live-update debounce
        rather than from the user pressing Generate. It decides how
        loudly a failure is reported -- an explicit Generate that
        fails owes the user a message, while a live run that fails
        must not interrupt somebody who never asked for it -- and it
        is what allows a queued live rerun to start once this one has
        finished landing its layers.

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
      # ...and the same for a run that came back empty, which on a
      # live update is a spacing the user is still adjusting rather
      # than anything they need stopping for.
      if live:
        self._report_quietly("The tiling produced no tiles.")
      else:
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

  def _legibility_note(self, fills, assignments):
    """The colour-legibility opinion, or None -- gated HERE.

    Args:
      fills: {tile_id: [(r, g, b), ...]} of what each element paints.
      assignments: the run's assignment dicts, for the shared-ramp
        exemption (elements deliberately sharing one ramp are not a
        clash, they are the shared-ramp technique).

    Returns:
      perception.clash_message's sentence, or None -- always None
      while "Warn about lack of legibility in colour choices" is
      unchecked. The gate lives INSIDE this helper so every caller,
      present and future, inherits it: the opt-in is a property of
      the opinion itself, not a courtesy each call site remembers.
      The user has reported ungated sightings; whatever path fires
      next fires through here, gated. (User instruction, 2026-08-09,
      twice.)
    """
    if not self.opt_colour_warnings.isChecked():
      return None
    from weavingspace_qgis import perception
    return perception.clash_message(perception.clashes(
      fills,
      shared={a["id"]: (a.get("ramp"), a.get("reverse"),
                        a.get("class_source"))
              for a in assignments}))

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
    # A dock edit made WHILE the run was in flight was ignored by the
    # styleChanged watcher (a run in progress must not be mistaken for
    # a user restyle) and then carried across by the preserved-
    # renderer path -- on the map but in no record, so the ramp cell
    # went on naming a ramp the layer no longer wears. Re-examine
    # exactly the preserved layers now the run is over -- but ONLY
    # those whose table state has not moved since the run landed. An
    # element the user changed mid-run also reads as "preserved" (the
    # landing used the launch snapshot), and re-examining it would
    # adopt the OLD colours as hand-picks that then outrank the very
    # change the user made: three race tests failed exactly that way
    # the first time this loop ran unguarded. A moved element belongs
    # to the queued rerun, which re-seeds it; a real dock edit made
    # after that rerun reaches the watcher normally.
    if self._preserved_this_run:
      current_by_id = {a["id"]: a for a in self._assignments()}
      for tid in self._preserved_this_run:
        lid = self._element_layer_ids.get(tid)
        assignment = current_by_id.get(tid)
        if lid and assignment is not None and \
            self._last_signatures.get(tid) == self._signature(assignment):
          self._on_layer_style_edited(lid, tid)
    self._preserved_this_run = []
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
      run_sig, geometry_sig: what this run actually drew, captured
        when it was LAUNCHED, and recorded here as the dialog's new
        baseline. Both default to None, in which case the signatures
        are read from the table as it stands now -- which is right
        only for a synchronous path, where nothing can have changed
        in between. For a run that went through the worker they must
        be passed, or a setting altered during a long tiling would be
        recorded as though the map already showed it, and the next
        Generate would take the restyle fast path over geometry that
        never matched.

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
    # one. Hand-picked COLOURS are the exception, on both styling
    # paths. Their editors are usable while a run is in flight, and
    # the restyle path declines during one, so a colour chosen in
    # that window would be seeded from the stale snapshot and
    # silently lost the moment the run landed. The dialog's record is
    # the authority for those, so it is re-read here rather than
    # trusted from the snapshot.
    for a in assignments:
      if a.get("mode") == "Categorized" and a.get("var"):
        a["category_colours"] = self._category_colours.get(
          a["id"], {}).get(a["var"])
      elif a.get("mode") == "Graduated":
        # The graduated half of that fix, missing until 2026-08-13
        # although the rule had been written down for the
        # categorical half since the day it was made. The quant
        # editor writes positional class colours and the ramp's
        # display window into the same record through the same
        # window, so trusting the snapshot here destroyed both the
        # moment a run landed -- and stamped them ABSENT onto
        # weavingspace_quant_style, so a reopened project could not
        # bring them back either. The window rides every graduated
        # row whether or not a variable is assigned, matching what
        # _assignments builds, so seeding never has to guess.
        # Guarded by
        # test_a_class_colour_picked_during_a_run_is_not_lost.
        if a.get("var"):
          a["quant_colours"] = self._quant_colours.get(
            a["id"], {}).get(a["var"])
        a["range_bounds"] = tuple(
          self._ramp_ranges.get(a["id"], (0, 100)))

    # NOT the rest of the symbology, and the distinction is settled
    # rather than accidental. A ramp, class count, opacity or Reverse
    # changed during a run is NOT lost: it stays in the element's
    # record, the table keeps it, and the next Generate applies it.
    # With live update off the plugin deliberately does not repaint
    # on its own -- the table and the map may disagree until the user
    # asks, which is what `test_race_restyle_during_run` has asserted
    # since long before tonight. Hand-picked COLOUR is the exception
    # because it was genuinely destroyed rather than merely deferred:
    # the landing run stamped it ABSENT onto the layer, past the
    # reach of a reopen. Re-reading the rest here was tried on
    # 2026-08-13 and reverted the same night; it made the map repaint
    # unasked and put two tests in direct contradiction.

    # keep the previous run's renderers (possibly hand-refined in the
    # styling dock) before touching any layers
    old_renderers = {}
    old_layer_opacity = {}
    old_subsets = {}
    for tid, lid in old_ids.items():
      old_layer = project.mapLayer(lid)
      if old_layer is not None and old_layer.renderer() is not None:
        old_renderers[tid] = old_layer.renderer().clone()
        # opacity lives on the layer, not the renderer, so it has to
        # be carried across separately when an element is kept as-is
        old_layer_opacity[tid] = old_layer.opacity()
      # A subset string is the user's own filter, set in Layer
      # Properties or the layer panel's Filter dialogue, and it used
      # to die with the layer at every regeneration -- deliberate
      # work silently discarded, unlike the hand styling beside it,
      # which survives. Carried across on the same promise (user
      # decision, 2026-08-09). Every element that HAD one gets it
      # back, whether or not its assignment changed: a filter says
      # which features to draw, not how to colour them.
      if old_layer is not None and old_layer.subsetString():
        old_subsets[tid] = old_layer.subsetString()
    if path:
      # release file handles before overwriting GeoPackage layers,
      # otherwise the write can hit sqlite locks (notably on Windows)
      for lid in old_ids.values():
        if project.mapLayer(lid) is not None:
          project.removeMapLayer(lid)
      old_ids = {}

    first_gpkg_layer = True
    # elements whose renderer is carried over rather than re-seeded;
    # _finish_run re-examines exactly these, because a dock edit made
    # mid-run rides across in that renderer with no record behind it
    self._preserved_this_run = []
    for tid in tile_ids:
      a = by_id.get(tid, {"id": tid, "var": None, "mode": "Single colour",
                          "ramp": "Greys", "scheme": "Quantiles", "k": 5,
                          "outline": False})
      display = f"{tid} – {a['var']}" if a["var"] else f"{tid} (no data)"
      sub = gdf[gdf["tile_id"] == tid]
      mem = bridge.gdf_to_layer(sub, display)
      if path:
        # THE FILE IS RECREATED ONLY IF IT DOES NOT EXIST, and that
        # condition used to be `created` -- meaning the layer-tree
        # GROUP was new, which is true on the first run of any fresh
        # dialog, on "Create as new group", and whenever the output
        # path changes. `first=True` becomes CreateOrOverwriteFile,
        # which recreates the WHOLE GeoPackage. So a user who chose a
        # .gpkg they already had lost everything else in it: their
        # own tables, and the region layer itself if it lived there,
        # in which case the map was drawn from data the same run had
        # just deleted. Nothing said so -- the open layer answers
        # featureCount() from cache -- and the only warning fires on
        # a different condition entirely and advises choosing another
        # file, which would destroy that one instead.
        #
        # Destroying data the plugin did not create is the one thing
        # it must never do, and the stale-table drop at the end of
        # this method already says so in as many words: it removes
        # only tables THIS dialog wrote, never a table the user's own
        # file already contained. That is also what makes recreating
        # the file unnecessary -- dropping our own dead tiles_*
        # tables is the job recreation was doing, done narrowly.
        # Measured 2026-08-13. Guarded by
        # test_a_generate_spares_the_rest_of_the_users_geopackage.
        out = bridge.write_gpkg_layer(mem, path, f"tiles_{tid}",
                                      first=(first_gpkg_layer
                                             and not os.path.exists(path)))
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
        self._preserved_this_run.append(tid)
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
        # the same values as the restyle path hands over, so an
        # element wears the same breaks whichever path drew it
        bridge.seed_renderer(
          out, a, templates.get(a.get("class_source")),
          self._classification_values(a.get("var")) if a.get("var")
          else None)
        # re-seeded, so the dialog is the authority for this element's
        # whole appearance this run, opacity included
        out.setOpacity(max(0, min(100, a.get("opacity", 100))) / 100.0)
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
      # The style goes into the GeoPackage LAST, and the order is the
      # whole point. QGIS stores a layer's custom properties inside
      # the style it saves, so embedding before the stamps above wrote
      # a style that named none of them -- and the .gpkg is the file
      # that LEAVES. Opened cold, its layers came back unstamped, so
      # the plugin did not recognise its own output and OFFERED IT AS
      # A REGION LAYER, which the settled rules say must never happen:
      # tile the tiles and the next map is drawn on the last one.
      # `_restyle_only` had the order right; this path did not.
      # Measured 2026-08-13. Guarded by
      # test_an_exported_geopackage_is_still_recognised_as_our_own.
      if path:
        bridge.embed_style(out)
      project.addMapLayer(out, False)
      group.addLayer(out)
      # the user's own filter, back on the fresh layer. Applied AFTER
      # the renderer, because a subset changes what a classifier
      # would see and the styling above belongs to the whole element;
      # a provider that refuses the clause (a GeoPackage column the
      # memory layer had, say) leaves the element unfiltered rather
      # than unpainted.
      if tid in old_subsets:
        if not out.setSubsetString(old_subsets[tid]):
          self._report_quietly(
            f"The filter you had set on element '{tid}' could not be "
            f"applied to the new layer, so it now draws everything.")
      new_ids[tid] = out.id()
      self._last_signatures[tid] = signature
      self._watch_element_layer(out, tid)

    if path:
      # Each GeoPackage handle above was opened while its SIBLINGS
      # were still being appended to the same file, and the earliest
      # handles cache "no spatial index" from that moment: the R-tree
      # is in the file (verified against sqlite directly) while the
      # provider believes otherwise, so QGIS quietly skips
      # index-assisted paths for exactly those elements. One reload
      # per layer, after all writing is over, refreshes the answer.
      for lid in new_ids.values():
        written = project.mapLayer(lid)
        if written is not None:
          written.dataProvider().reloadData()

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
    # A GeoPackage is REPLACED table by table, so a design that
    # shrank left its old elements in the file: the map showed three
    # and the file held six, with nothing to say which three were the
    # map. That file is the thing a user sends to somebody else, so
    # the wrongness travels while the map stays right. Only tables
    # THIS dialog wrote into THIS file are removed, and only those
    # the current design no longer has -- never a table the user's
    # own file already contained. Guarded by
    # test_a_geopackage_loses_the_elements_a_design_dropped.
    if path:
      written = self._gpkg_tables_written.get(path, set())
      for stale in sorted(written - set(new_ids)):
        bridge.drop_gpkg_layer(path, f"tiles_{stale}")
      self._gpkg_tables_written[path] = set(new_ids)
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
    colour_clash = self._legibility_note(
      {tid: fills for tid, fills in element_fills.items() if fills},
      assignments)
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
      # colour_clash is NOT pushed here: it rides _pending_colour_note
      # and the done callback sends it once the dust settles. Pushing
      # it here as well delivered every legibility warning twice to a
      # real message bar -- the stash was added for the note-line wipe
      # and the immediate push was never taken out.
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
