"""Choosing a colour for each value a categorical element takes.

The plugin's automatic colours come from a ramp, sampled the way the
original library samples it. That is the right default and a poor
final answer: a reader of a land-cover map expects forest to be green,
and no ramp knows that. Importing a QML says the same thing more
laboriously, and only for people who already have one.

So this is the small window behind the "Edit colours" button: the
values on the left, the colour each currently draws in on the right,
and a picker on any of them. It is deliberately not a styling panel.
QGIS already has one of those, it is better than anything this plugin
would build, and everything chosen here ends up in an ordinary
QgsCategorizedSymbolRenderer that the styling dock can go on editing.

The same window serves GRADUATED elements in a second mode. There the
rows are classes rather than values (two read-only columns give each
class's lower and upper bound), and a Ramp Display Range section sits
at the very top: a preview of the ramp with a two-handled slider and a
pair of percent boxes beneath it, choosing the stretch of the ramp the
classes are spread across. For Quant: Unclassed the fifty classes are
shown locked and translucent -- there is nothing to hand-pick when the
ramp is continuous -- and the range section alone is live, repainting
the greyed list as it moves.

What this module does NOT do is touch a layer, and in graduated mode
it does not compute a single colour either: the range section reports
(lo, hi) to the dialog through a callback and paints whatever colours
come back. The dialog owns the colours and the layers; a run finishing
while this window is open replaces the element layers underneath, and
a window holding a layer reference would be writing into a corpse.
"""
from __future__ import annotations

from qgis.PyQt.QtCore import QEvent, QSize, Qt, QTimer
from qgis.PyQt.QtGui import QColor, QIcon, QPixmap
from qgis.PyQt.QtWidgets import (QAbstractItemView, QColorDialog, QDialog,
                                 QDialogButtonBox, QGraphicsOpacityEffect,
                                 QHBoxLayout, QHeaderView, QLabel,
                                 QPushButton, QSpinBox, QTableWidget,
                                 QTableWidgetItem, QVBoxLayout)

from . import bridge

# The value column is a fixed width rather than one fitted to the
# longest value. A column that resizes itself makes every element's
# editor a different width, so the window jumps about as a user moves
# between elements; a settled width is easier to read across. Values
# longer than this elide, and the full text is on hover.
VALUE_WIDTH = 125

# The colour column holds a swatch and a six-digit hex code, and does
# not need to grow.
COLOUR_WIDTH = 120

# In graduated mode the value column is replaced by two bound columns,
# Lower and Upper. Class breaks are numbers with the trailing zeros
# trimmed, so they are short; this width holds seven digits and a
# decimal point comfortably without widening the window for nothing.
BOUND_WIDTH = 70

# How many rows are visible before the window scrolls. Beyond this a
# scroll bar appears and the window stops growing: fifteen covers most
# categorical fields outright, and a taller window would start
# obscuring the map the colours are being chosen for.
VISIBLE_ROWS = 15

SWATCH = QSize(48, 16)

# The ramp preview strip in the Ramp Display Range section. Tall
# enough that the colours read as a ramp rather than a hairline; the
# range slider beneath it is fixed to the same width so a handle sits
# directly under the point of the ramp it selects.
RAMP_PREVIEW_HEIGHT = 20

# How long the range section waits, while a slider handle is being
# dragged, before asking the dialog for fresh colours. Recolouring
# fifty classes on every mouse move would make the drag stutter;
# 150 ms is short enough to feel live and long enough to skip the
# intermediate positions. Release, or finishing an edit in a percent
# box, fires immediately.
RANGE_DEBOUNCE_MS = 150

# The Unclassed list is shown at just under half opacity: present
# enough to watch the range recolour it, faded enough to read as
# not-editable.
LOCKED_OPACITY = 0.45

# A hex code is read digit by digit and compared down the column, so
# it wants fixed pitch. Named families rather than a single font, in
# the order they are likely to exist: macOS, Windows, Linux, then
# whatever Qt calls its default fixed font.
MONO_FAMILIES = "Menlo, Consolas, 'DejaVu Sans Mono', monospace"


def colour_swatch(colour: str) -> QIcon:
  """A filled rectangle standing for one colour.

  Args:
    colour: "#rrggbb".

  Returns:
    A QIcon. Drawn rather than themed so the colour shown is exactly
    the colour the map will use.
  """
  pixmap = QPixmap(SWATCH)
  pixmap.fill(QColor(colour))
  return QIcon(pixmap)


class CategoryColourDialog(QDialog):
  """The colour editor for one element, categorical or graduated.

  Args:
    tile_id: the element being edited, shown in the window so a user
      with several open in turn knows which one this is.
    field: the attribute whose values (or classes) are listed.
    order: the row keys, in the order the renderer classes them, as
      strings. Categorical mode lists the field's values (including
      bridge.NO_DATA_KEY for the catch-all); graduated mode lists the
      class-index strings "0" .. "k-1", which are what key the
      dialog's positional picks, and has no no-data row.
    colours: {key: "#rrggbb"} for what each row currently draws in,
      keyed exactly as `order` is.
    picked: called with (key, "#rrggbb") the moment a colour is
      picked, so the map repaints while the window is still open.
      That is the point of the window being modal to the plugin
      rather than to QGIS: the canvas stays live and the change can
      be watched.
    parent: the plugin dialog. The window is modal against it.
    bounds: graduated mode's switch. A list of (lower, upper) floats,
      one per entry of `order`; when given, the single value column
      is replaced by two read-only columns, Lower and Upper, printed
      with trailing zeros trimmed (12.5, 40). Omitted (None), the
      editor is exactly the categorical window it always was.
    locked: True for Quant: Unclassed. The class table is shown
      translucent with every colour button disabled -- a continuous
      ramp has no class colours worth picking by hand -- but the
      table still repaints when the range section hands back new
      colours, which is how a user watches the range take effect.
    range_bounds: (lo, hi) percent integers, or None for no range
      section at all (categorical mode). When given, the Ramp
      Display Range section renders at the very top of the window,
      outside the table's scrolling, so no window size can hide it.
    ramp_name: the ramp the range section previews, by its QgsStyle
      name; looked up through bridge.get_ramp so the strip shows the
      ramp exactly as the map will sample it.
    reverse: whether that ramp is currently reversed. The preview is
      drawn AS SEEN, so a handle at 20% always sits under the colour
      that 20% will produce.
    range_changed: callback(lo, hi) -> list of "#rrggbb" in class
      order. The editor calls it when the range moves (debounced
      during a drag, immediate on release or a finished spin-box
      edit) and repaints its rows with whatever comes back. The
      editor never computes a colour itself and never touches a
      layer: the dialog owns both.

  The values come from the REGION layer rather than from the output,
  so this works before anything has been generated. One consequence
  is worth knowing: at a coarse spacing some areas receive no tiles,
  so a value listed here may not appear on the map at all.
  """

  def __init__(self, tile_id, field, order, colours, picked,
               parent=None, *, bounds=None, locked=False,
               range_bounds=None, ramp_name=None, reverse=False,
               range_changed=None):
    super().__init__(parent)
    # Graduated mode is recognised by its extras, not by a flag of its
    # own: bounds columns and a range section arrive together from the
    # dialog, and either one means the rows are classes.
    graduated = bounds is not None or range_bounds is not None
    self.setWindowTitle("Graduated colour editor" if graduated
                        else "Categorical colour editor")
    # Modal to the plugin dialog only. Application-modal would block
    # the map canvas too, and a colour picked without being able to
    # look at the map is picked blind.
    self.setWindowModality(Qt.WindowModality.WindowModal)
    self._on_change = picked
    self._colours = dict(colours)
    self._values = list(order)
    self._bounds = list(bounds) if bounds is not None else None
    self._locked = locked
    self._ramp_name = ramp_name
    self._reverse = reverse
    self._range_changed = range_changed

    layout = QVBoxLayout(self)
    # The range section goes in FIRST, before even the heading: it is
    # the live control in Unclassed mode and must never scroll out of
    # reach, so it sits above everything the table's scroll bar can
    # move. Its widths are settled later, once the table has decided
    # how wide the window is.
    if range_bounds is not None:
      self._build_range_section(layout, range_bounds)

    # Two lines rather than one. The window is sized to the TABLE, and
    # a field name long enough to widen it past the table would drag
    # the whole dialogue wider for no benefit; broken in two, the
    # heading fits in the width the table already needs.
    heading = QLabel(f"Element '{tile_id}'\ncoloured by '{field}'")
    heading.setWordWrap(True)
    layout.addWidget(heading)

    columns = 2 if self._bounds is None else 3
    self.table = QTableWidget(len(self._values), columns, self)
    self.table.setHorizontalHeaderLabels(
      ["Value", "Colour"] if self._bounds is None
      else ["Lower", "Upper", "Colour"])
    self.table.verticalHeader().setVisible(False)
    # Whole rows would suggest the row is the thing being acted on;
    # the colour cell is. Selection is off entirely: every click here
    # should either open a picker or do nothing.
    self.table.setSelectionMode(
      QAbstractItemView.SelectionMode.NoSelection)
    self.table.setEditTriggers(
      QAbstractItemView.EditTrigger.NoEditTriggers)

    for row, value in enumerate(self._values):
      if self._bounds is None:
        # Categorical: the value in one cell, exactly as before.
        label = self._label_for(value)
        cell = QTableWidgetItem(label)
        cell.setToolTip(label)    # the full value, however long
        # Values right, colours left, so the two columns meet at the
        # middle of the window: the eye runs down the gap between a
        # value and its colour instead of across a gap that widens
        # with every short name. The header keeps Qt's own alignment,
        # which is what tells you it is a header.
        cell.setTextAlignment(Qt.AlignmentFlag.AlignRight
                              | Qt.AlignmentFlag.AlignVCenter)
        if value == bridge.NO_DATA_KEY:
          # separated from the data's own values, because it is not
          # one
          font = cell.font()
          font.setItalic(True)
          cell.setFont(font)
        self.table.setItem(row, 0, cell)
      else:
        # Graduated: the class's two bounds, read-only, one per cell.
        # Right-aligned like the categorical values, and for the same
        # reason: numbers are compared down a column by their ends.
        for col, bound in enumerate(self._bounds[row]):
          cell = QTableWidgetItem(self._format_bound(bound))
          cell.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                | Qt.AlignmentFlag.AlignVCenter)
          self.table.setItem(row, col, cell)

      # The colour button is the last column in either mode.
      self.table.setCellWidget(row, columns - 1,
                               self._colour_button(value))

    self._size_columns()

    if self._locked:
      # The Unclassed list is watched, not edited: the buttons are
      # already disabled (see _colour_button), and the whole table is
      # faded so the window says so at a glance. The effect belongs
      # to the table, so the range section above stays fully opaque.
      effect = QGraphicsOpacityEffect(self.table)
      effect.setOpacity(LOCKED_OPACITY)
      self.table.setGraphicsEffect(effect)

    layout.addWidget(self.table)

    if range_bounds is not None:
      # Now the table has fixed its own width, the ramp strip and the
      # slider can be drawn at exactly that width, so a slider handle
      # sits directly beneath the point of the ramp it selects.
      self._fit_range_section(self._table_width)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.rejected.connect(self.reject)
    buttons.accepted.connect(self.accept)
    layout.addWidget(buttons)
    # The table is sized first and the window fitted to it, never the
    # other way round: a window sized by guess leaves either a strip
    # of dead space beside the table or a scroll bar the rows did not
    # need. The range section, when present, has fixed sizes of its
    # own by this point, so the same fit grows the window by exactly
    # its height and nothing is hidden at any size.
    self.adjustSize()
    self.setFixedSize(self.sizeHint())

  def _label_for(self, value):
    """What the left column says for one value."""
    return "(no data)" if value == bridge.NO_DATA_KEY else str(value)

  def _format_bound(self, value):
    """A class bound as the row prints it.

    Args:
      value: one end of a class interval, a float.

    Returns:
      The number with trailing zeros trimmed -- 12.5 stays "12.5",
      40.0 becomes "40" -- because a column of ".000000" tails says
      nothing and hides the digits that differ. Ten significant
      digits, so ordinary data prints exactly and only absurd
      magnitudes fall back to scientific notation.
    """
    text = f"{float(value):.10g}"
    # A negative zero can fall out of classification arithmetic and
    # reads as a typo; print it as the zero it is.
    return "0" if text == "-0" else text

  def _colour_button(self, value):
    """The colour button for one row, in either mode.

    Args:
      value: the row's key -- a categorical value, or a class-index
        string in graduated mode. Stored on the button, so _pick
        knows which colour it is being asked to change.

    Returns:
      A QPushButton showing the current colour as swatch and hex
      code, wired to open the picker; disabled when the window is
      locked, since a continuous ramp leaves nothing to pick.
    """
    button = QPushButton(self._colours.get(value, bridge.NO_DATA_FILL))
    button.setIcon(colour_swatch(
      self._colours.get(value, bridge.NO_DATA_FILL)))
    button.setIconSize(SWATCH)
    button.setProperty("value", value)
    # left-aligned and fixed pitch: hex codes are compared down the
    # column, and a proportional font makes that needlessly hard
    button.setStyleSheet(
      f"text-align: left; font-family: {MONO_FAMILIES};")
    button.clicked.connect(self._pick)
    if self._locked:
      button.setEnabled(False)
    return button

  def _size_columns(self):
    """Give the table exactly the size its contents need.

    Returns:
      None. Sets every column to its fixed width and then FIXES the
      table's own size to the space those columns and up to
      VISIBLE_ROWS rows occupy, so the surrounding layout has a real
      number to fit the window to. The width is kept on
      self._table_width for the range section, which is drawn to
      match it.

    The order matters and is the whole point: columns, then rows, then
    the table, and only then the window. Sizing the window first and
    letting the table fill it is what leaves a margin of dead space
    down one side, or a horizontal scroll bar over a table that would
    have fitted.

    A vertical scroll bar takes width from the viewport rather than
    adding it, so when there are more rows than fit, its width is
    added here -- otherwise the last column is clipped by exactly the
    scroll bar that appeared to accommodate the rows.
    """
    # Categorical is value + colour; graduated is lower + upper +
    # colour. Same discipline either way: every column a settled
    # width, so the window is the same size for every element.
    if self._bounds is None:
      column_widths = [VALUE_WIDTH, COLOUR_WIDTH]
    else:
      column_widths = [BOUND_WIDTH, BOUND_WIDTH, COLOUR_WIDTH]
    header = self.table.horizontalHeader()
    for col, col_width in enumerate(column_widths):
      self.table.setColumnWidth(col, col_width)
      header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)

    rows = self.table.rowCount()
    row_height = (self.table.verticalHeader().defaultSectionSize()
                  if rows == 0 else self.table.rowHeight(0))
    shown = min(rows, VISIBLE_ROWS)
    frame = self.table.frameWidth() * 2

    width = sum(column_widths) + frame
    if rows > VISIBLE_ROWS:
      width += self.table.verticalScrollBar().sizeHint().width()
    height = header.height() + row_height * shown + frame
    self.table.setFixedSize(width, height)
    self._table_width = width

  def _build_range_section(self, layout, range_bounds):
    """The Ramp Display Range controls, above everything else.

    Args:
      layout: the window's vertical layout, still empty; the section
        is its first occupant so no scrolling can hide it.
      range_bounds: (lo, hi) percent integers, the range as the
        dialog last knew it.

    Returns:
      None. Adds the section label, the ramp preview strip, the
      two-handled slider and the two percent boxes, and wires them
      so any movement reaches _send_range -- debounced while a
      slider handle is dragging, immediately on release or when a
      spin-box edit finishes. The preview strip and slider get
      their widths later (_fit_range_section), once the table has
      settled how wide the window is.
    """
    # qgis.gui is imported here rather than at module top so the
    # categorical editor, which never needs it, costs nothing extra;
    # the same lazy habit the rest of the plugin uses for qgis.core.
    from qgis.gui import QgsRangeSlider

    lo, hi = range_bounds
    layout.addWidget(QLabel("Ramp Display Range"))

    # The strip previewing the ramp. Its pixmap is drawn in
    # _fit_range_section, at the width the table settles on.
    self._ramp_label = QLabel(self)
    layout.addWidget(self._ramp_label)

    # A two-handled slider: QGIS's own widget for choosing a
    # sub-range, the same control its styling panels use. Values are
    # whole percents of the ramp's length.
    self.range_slider = QgsRangeSlider(Qt.Orientation.Horizontal, self)
    self.range_slider.setRangeLimits(0, 100)
    self.range_slider.setRange(lo, hi)
    self.range_slider.setToolTip(
      "Drag the handles to choose the stretch of ramp the classes "
      "use.")
    layout.addWidget(self.range_slider)

    # The same two numbers again, as spin boxes, for anyone who wants
    # to type 25 rather than aim for it. Each box's allowed range is
    # clamped by the other's current value, so the two can touch (a
    # constant colour is a legitimate choice) but can never cross.
    self.lower_spin = QSpinBox(self)
    self.lower_spin.setSuffix("%")
    self.lower_spin.setRange(0, hi)
    self.lower_spin.setValue(lo)
    self.lower_spin.setToolTip(
      "Lower end of the ramp stretch, as a percentage.")
    self.upper_spin = QSpinBox(self)
    self.upper_spin.setSuffix("%")
    self.upper_spin.setRange(lo, 100)
    self.upper_spin.setValue(hi)
    self.upper_spin.setToolTip(
      "Upper end of the ramp stretch, as a percentage.")
    spin_row = QHBoxLayout()
    spin_row.addWidget(self.lower_spin)
    # The stretch pushes the boxes to the two ends of the window, so
    # each sits under the slider handle it duplicates.
    spin_row.addStretch(1)
    spin_row.addWidget(self.upper_spin)
    layout.addLayout(spin_row)

    # One single-shot timer debounces the drag: every movement
    # restarts it, so the dialog is only asked for colours once the
    # handle has paused. Release and finished edits bypass it.
    self._range_timer = QTimer(self)
    self._range_timer.setSingleShot(True)
    self._range_timer.setInterval(RANGE_DEBOUNCE_MS)
    self._range_timer.timeout.connect(self._send_range)

    # The last (lo, hi) actually reported. Seeded with the opening
    # values so merely opening the window never asks the dialog to
    # recolour a map that has not changed.
    self._last_range_sent = (lo, hi)
    # Guards the two-way sync below: the slider updates the boxes and
    # the boxes update the slider, and without the flag each would
    # re-enter the other forever.
    self._syncing = False

    self.range_slider.rangeChanged.connect(self._slider_moved)
    # QgsRangeSlider is a plain QWidget and offers no sliderReleased
    # signal, so the moment the drag ends is caught by watching the
    # slider's own mouse events: a button release means the handles
    # are where the user wants them, and the debounce wait would only
    # delay the answer.
    self.range_slider.installEventFilter(self)
    self.lower_spin.valueChanged.connect(self._spin_changed)
    self.upper_spin.valueChanged.connect(self._spin_changed)
    self.lower_spin.editingFinished.connect(self._spin_settled)
    self.upper_spin.editingFinished.connect(self._spin_settled)

  def _fit_range_section(self, width):
    """Draw the ramp strip and line the slider up beneath it.

    Args:
      width: the table's settled width in pixels, which is the
        window's content width; the strip and slider both take it,
        so slider positions and ramp positions coincide.

    Returns:
      None. Renders the ramp preview through QGIS's own utility --
      the identical drawing the styling panels use -- so what the
      strip shows is exactly what sampling the ramp will produce. An
      unknown ramp name leaves the strip blank at the same size
      rather than failing: the slider still works, it just has
      nothing to point at.
    """
    from qgis.core import QgsSymbolLayerUtils
    ramp = (bridge.get_ramp(self._ramp_name, self._reverse)
            if self._ramp_name else None)
    if ramp is not None:
      self._ramp_label.setPixmap(
        QgsSymbolLayerUtils.colorRampPreviewPixmap(
          ramp, QSize(width, RAMP_PREVIEW_HEIGHT)))
    self._ramp_label.setFixedSize(width, RAMP_PREVIEW_HEIGHT)
    self.range_slider.setFixedWidth(width)

  def _slider_moved(self, lo, hi):
    """Follow a slider movement into the spin boxes, debounced.

    Args:
      lo: the lower handle's value, whole percent.
      hi: the upper handle's value, whole percent.

    Returns:
      None. Mirrors the values into the spin boxes (re-clamping each
      against the other, so typing afterwards still cannot cross
      them) and restarts the debounce timer; the dialog hears about
      it when the drag pauses or the button is released.
    """
    if self._syncing:
      return                      # an echo of our own update
    self._syncing = True
    try:
      # Clamps first, then values: setting a value outside a box's
      # current range would silently truncate it.
      self.lower_spin.setMaximum(hi)
      self.upper_spin.setMinimum(lo)
      self.lower_spin.setValue(lo)
      self.upper_spin.setValue(hi)
    finally:
      self._syncing = False
    self._range_timer.start()

  def _spin_changed(self, _value):
    """Follow a spin-box change into the slider, debounced.

    Args:
      _value: the box's new value; unused, because both boxes are
        read afresh -- either one may have moved.

    Returns:
      None. Re-clamps the two boxes against each other, mirrors them
      into the slider, and restarts the debounce timer. Arrow-button
      clicks land here too, so they respond after the debounce even
      though no editingFinished ever fires for them.
    """
    if self._syncing:
      return                      # an echo of our own update
    self._syncing = True
    try:
      lo = self.lower_spin.value()
      hi = self.upper_spin.value()
      self.lower_spin.setMaximum(hi)
      self.upper_spin.setMinimum(lo)
      self.range_slider.setRange(lo, hi)
    finally:
      self._syncing = False
    self._range_timer.start()

  def _spin_settled(self):
    """A spin-box edit is finished: report it now, not later.

    Returns:
      None. editingFinished means Return was pressed or focus left
      the box -- the number is meant -- so the debounce wait is
      cancelled and the dialog asked immediately.
    """
    self._range_timer.stop()
    self._send_range()

  def eventFilter(self, obj, event):
    """Catch the end of a slider drag.

    Args:
      obj: the watched widget; only the range slider is watched.
      event: the event on its way to that widget.

    Returns:
      Whatever QDialog's own filter returns -- never True from here,
      because the slider must still receive the release and finish
      its drag; this filter only listens. A release fires the range
      report immediately, standing in for the sliderReleased signal
      QgsRangeSlider does not have.
    """
    if (obj is getattr(self, "range_slider", None)
        and event.type() == QEvent.Type.MouseButtonRelease):
      self._range_timer.stop()
      self._send_range()
    return super().eventFilter(obj, event)

  def _send_range(self):
    """Report the range to the dialog and repaint with its answer.

    Returns:
      None. Calls range_changed(lo, hi) -- the dialog computes the
      colours, never this window -- and paints the returned list
      over the rows in class order. Skips entirely when (lo, hi) is
      what was last reported, so a release after a debounce tick, or
      an editingFinished after an unchanged edit, costs nothing.
    """
    lo = self.lower_spin.value()
    hi = self.upper_spin.value()
    if (lo, hi) == self._last_range_sent:
      return
    self._last_range_sent = (lo, hi)
    if self._range_changed is None:
      return
    fresh = self._range_changed(lo, hi)
    if fresh:
      self._repaint_colours(fresh)

  def _repaint_colours(self, hexes):
    """Paint a new set of colours over the rows.

    Args:
      hexes: "#rrggbb" strings in class order, as range_changed
        returned them.

    Returns:
      None. Updates the recorded colour and the button for each row
      in step; the buttons repaint even when the window is locked,
      because watching the range recolour the list is exactly what
      the locked window is for. zip stops at the shorter side, so a
      list of the wrong length can never reach past the rows.
    """
    colour_col = self.table.columnCount() - 1
    for row, (value, colour) in enumerate(zip(self._values, hexes)):
      self._colours[value] = colour
      button = self.table.cellWidget(row, colour_col)
      if button is None:
        continue                  # no button, nothing to repaint
      button.setText(colour)
      button.setIcon(colour_swatch(colour))

  def _pick(self):
    """Open a colour picker for the row whose button was clicked.

    Returns:
      None. A chosen colour is recorded, the button restyled, and
      picked called at once so the map follows while the window is
      still open. Cancelling the picker changes nothing.
    """
    button = self.sender()
    if button is None:
      return
    value = button.property("value")
    start = QColor(self._colours.get(value, bridge.NO_DATA_FILL))
    # The rows are classes in graduated mode and values otherwise,
    # and the picker's title should not claim one is the other.
    title = ("Colour for this class" if self._bounds is not None
             else "Colour for this value")
    chosen = QColorDialog.getColor(start, self, title)
    if not chosen.isValid():
      return                      # the user cancelled
    name = chosen.name()
    if name == self._colours.get(value):
      return                      # picked the colour it already was
    self._colours[value] = name
    button.setText(name)
    button.setIcon(colour_swatch(name))
    if self._on_change is not None:
      self._on_change(value, name)

  def _flush_pending_range(self):
    """Land any range movement still sitting in the debounce timer.

    Returns:
      None. The user made that movement and then closed the window,
      so it counts -- but it must land now, synchronously, not 150 ms
      later when a timer fires into a dialog that believes the editor
      is gone. Found the hard way: a stray debounce tick after close
      destroyed a pick made just after. Safe to call twice, because
      _send_range skips when nothing changed since the last report.
    """
    timer = getattr(self, "_range_timer", None)
    if timer is not None and timer.isActive():
      timer.stop()
      self._send_range()

  def done(self, result):  # noqa: N802 (Qt API)
    """Qt calls this when exec/accept/reject end the window.

    Args:
      result: the dialog result code, passed through untouched.

    Returns:
      None. Flushes the pending range first (see
      _flush_pending_range). closeEvent below does the same for the
      OTHER exit: close() on a dialog that was never shown delivers a
      close event without ever reaching done() (measured, Qt 6 /
      QGIS 4.0.3), and the suite drives the editor exactly that way.
    """
    self._flush_pending_range()
    super().done(result)

  def closeEvent(self, event):  # noqa: N802 (Qt API)
    """Qt calls this when the window is closed with close().

    Args:
      event: the close event, passed through untouched.

    Returns:
      None. The flush lives here as well as in done() because the two
      paths do not meet: a shown dialog's close() reaches done()
      through QDialog's reject, but a NEVER-SHOWN dialog's close()
      delivers only this event. Flushing twice costs nothing --
      _send_range reports only changes.
    """
    self._flush_pending_range()
    super().closeEvent(event)

  def colours(self) -> dict:
    """Every row's colour as it now stands, hand-picked or not."""
    return dict(self._colours)
