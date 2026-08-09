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

What this module does NOT do is touch a layer. It reports the colours
back to the dialog, which owns them; a run finishing while this window
is open replaces the element layers underneath, and a window holding a
layer reference would be writing into a corpse.
"""
from __future__ import annotations

from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtGui import QColor, QIcon, QPixmap
from qgis.PyQt.QtWidgets import (QAbstractItemView, QColorDialog, QDialog,
                                 QDialogButtonBox, QHeaderView, QLabel,
                                 QPushButton, QTableWidget, QTableWidgetItem,
                                 QVBoxLayout)

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

# How many rows are visible before the window scrolls. Beyond this a
# scroll bar appears and the window stops growing: fifteen covers most
# categorical fields outright, and a taller window would start
# obscuring the map the colours are being chosen for.
VISIBLE_ROWS = 15

SWATCH = QSize(48, 16)

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
  """The Categorical colour editor for one element.

  Args:
    tile_id: the element being edited, shown in the window so a user
      with several open in turn knows which one this is.
    field: the attribute whose values are listed.
    values: the values themselves, in the order the renderer classes
      them, as strings.
    colours: {value: "#rrggbb"} for what each currently draws in,
      including bridge.NO_DATA_KEY for the catch-all.
    on_change: called with (value, "#rrggbb") the moment a colour is
      picked, so the map repaints while the window is still open.
      That is the point of the window being modal to the plugin
      rather than to QGIS: the canvas stays live and the change can
      be watched.
    parent: the plugin dialog. The window is modal against it.

  The values come from the REGION layer rather than from the output,
  so this works before anything has been generated. One consequence
  is worth knowing: at a coarse spacing some areas receive no tiles,
  so a value listed here may not appear on the map at all.
  """

  def __init__(self, tile_id, field, values, colours, on_change,
               parent=None):
    super().__init__(parent)
    self.setWindowTitle("Categorical colour editor")
    # Modal to the plugin dialog only. Application-modal would block
    # the map canvas too, and a colour picked without being able to
    # look at the map is picked blind.
    self.setWindowModality(Qt.WindowModality.WindowModal)
    self._on_change = on_change
    self._colours = dict(colours)
    self._values = list(values)

    layout = QVBoxLayout(self)
    # Two lines rather than one. The window is sized to the TABLE, and
    # a field name long enough to widen it past the table would drag
    # the whole dialogue wider for no benefit; broken in two, the
    # heading fits in the width the table already needs.
    heading = QLabel(f"Element '{tile_id}'\ncoloured by '{field}'")
    heading.setWordWrap(True)
    layout.addWidget(heading)

    self.table = QTableWidget(len(self._values), 2, self)
    self.table.setHorizontalHeaderLabels(["Value", "Colour"])
    self.table.verticalHeader().setVisible(False)
    # Whole rows would suggest the row is the thing being acted on;
    # the colour cell is. Selection is off entirely: every click here
    # should either open a picker or do nothing.
    self.table.setSelectionMode(
      QAbstractItemView.SelectionMode.NoSelection)
    self.table.setEditTriggers(
      QAbstractItemView.EditTrigger.NoEditTriggers)

    for row, value in enumerate(self._values):
      label = self._label_for(value)
      cell = QTableWidgetItem(label)
      cell.setToolTip(label)      # the full value, however long
      # Values right, colours left, so the two columns meet at the
      # middle of the window: the eye runs down the gap between a
      # value and its colour instead of across a gap that widens with
      # every short name. The header keeps Qt's own alignment, which
      # is what tells you it is a header.
      cell.setTextAlignment(Qt.AlignmentFlag.AlignRight
                            | Qt.AlignmentFlag.AlignVCenter)
      if value == bridge.NO_DATA_KEY:
        # separated from the data's own values, because it is not one
        font = cell.font()
        font.setItalic(True)
        cell.setFont(font)
      self.table.setItem(row, 0, cell)

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
      self.table.setCellWidget(row, 1, button)

    self._size_columns()
    layout.addWidget(self.table)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.rejected.connect(self.reject)
    buttons.accepted.connect(self.accept)
    layout.addWidget(buttons)
    # The table is sized first and the window fitted to it, never the
    # other way round: a window sized by guess leaves either a strip
    # of dead space beside the table or a scroll bar the rows did not
    # need.
    self.adjustSize()
    self.setFixedSize(self.sizeHint())

  def _label_for(self, value):
    """What the left column says for one value."""
    return "(no data)" if value == bridge.NO_DATA_KEY else str(value)

  def _size_columns(self):
    """Give the table exactly the size its contents need.

    Returns:
      None. Sets both columns to their fixed widths and then FIXES the
      table's own size to the space those columns and up to
      VISIBLE_ROWS rows occupy, so the surrounding layout has a real
      number to fit the window to.

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
    self.table.setColumnWidth(0, VALUE_WIDTH)
    self.table.setColumnWidth(1, COLOUR_WIDTH)
    header = self.table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)

    rows = self.table.rowCount()
    row_height = (self.table.verticalHeader().defaultSectionSize()
                  if rows == 0 else self.table.rowHeight(0))
    shown = min(rows, VISIBLE_ROWS)
    frame = self.table.frameWidth() * 2

    width = VALUE_WIDTH + COLOUR_WIDTH + frame
    if rows > VISIBLE_ROWS:
      width += self.table.verticalScrollBar().sizeHint().width()
    height = header.height() + row_height * shown + frame
    self.table.setFixedSize(width, height)

  def _pick(self):
    """Open a colour picker for the row whose button was clicked.

    Returns:
      None. A chosen colour is recorded, the button restyled, and
      on_change called at once so the map follows while the window is
      still open. Cancelling the picker changes nothing.
    """
    button = self.sender()
    if button is None:
      return
    value = button.property("value")
    start = QColor(self._colours.get(value, bridge.NO_DATA_FILL))
    chosen = QColorDialog.getColor(start, self, "Colour for this value")
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

  def colours(self) -> dict:
    """Every value's colour as it now stands, hand-picked or not."""
    return dict(self._colours)
