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

import math

from qgis.PyQt.QtCore import QEvent, QPointF, QSize, Qt, QTimer
from qgis.PyQt.QtGui import (QBrush, QColor, QIcon, QPainter, QPalette,
                             QPen, QPainterPath, QPixmap, QPolygonF)
from qgis.PyQt.QtWidgets import (QAbstractButton, QAbstractItemView,
                                 QColorDialog, QComboBox, QDialog,
                                 QDialogButtonBox,
                                 QDoubleSpinBox,
                                 QHBoxLayout, QHeaderView, QLabel,
                                 QPushButton, QSpinBox, QTableWidget,
                                 QTableWidgetItem, QVBoxLayout, QWidget)

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

# The pin column: a twenty-pixel glyph with room either side, so a
# pin sits centred in its cell without the column looking like a gap.
PIN_WIDTH = 34

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

# The Unclassed list used to be shown at just under half opacity,
# through a QGraphicsOpacityEffect on the whole table. That is gone
# (2026-08-17): an effect composites its source offscreen while the
# table scrolls by blitting, and the two disagreed visibly, painting
# each class bound faintly behind the row above it. The fade is done
# per item now, through the palette's own disabled colour, so there is
# no constant left to tune -- see the branch in `_rebuild`.

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



def _is_absence(value) -> bool:
  """Whether this row stands for an absence rather than a class.

  Args:
    value: the row's key, as it appears in the editor's `order`.

  Returns:
    True for any of the ABSENCE_KINDS keys. Derived from that tuple
    rather than testing one key, because the paired layer grew from
    one kind to three on 2026-08-16 and every site that asked
    `== NO_DATA_KEY` became a site that handled one of them: one such
    site was widened, its twin was not, and the editor raised
    IndexError on an element carrying an infinity -- inside a Qt slot,
    so the button simply did nothing and QGIS showed a Python error.
  """
  return any(value == key for key, _v, _l, _f in bridge.ABSENCE_KINDS)


class PinButton(QAbstractButton):
  """A pushpin that can be pressed in or left out.

  Pinning a class bound means "this break is mine, compute the rest
  around it", and the control for it is a pin because that is the
  word the feature is named for. It is DRAWN rather than taken from a
  font or an icon theme, exactly as `colour_swatch` and dialog.py's
  `ToggleSwitch` are: a pushpin codepoint renders as colour emoji on
  macOS and as a missing-glyph box on the QGIS container images, and
  a themed icon depends on an icon set this plugin has never once
  relied on. Painting it is a dozen lines and looks the same
  everywhere.

  It is an ordinary QAbstractButton, so setChecked/isChecked, the
  toggled signal, the space bar and the disabled state all work as
  they do for a checkbox.

  Args:
    parent: the owning widget, as usual in Qt.

  The two states are legible APART rather than merely different: out
  is a hollow outline lying at an angle, in is filled, upright and
  drawn in the palette's highlight colour. A pin whose states can
  only be told apart by looking twice is worse than the checkbox it
  replaces, which is the line
  test_a_toggle_switch_shows_which_way_it_is_set already holds for
  the other hand-painted control here.

  THE SILHOUETTE IS A TACK, and the first version was not. It drew a
  round head on a straight shaft, which is a MAGNIFYING GLASS -- the
  maintainer read it as one on sight, 2026-08-16, and once seen it
  cannot be unseen. What separates the two shapes is the taper: a
  lens has a handle of even width, a tack has a body that narrows to
  a point. So the head is wide and flat like a tack's, and the body
  is a triangle ending in a point rather than a line ending in
  nothing. Drawing an icon whose meaning is its outline is worth a
  minute with a pencil first; "it has the right parts" is not the
  same as "it reads as the thing".
  """

  SIZE = QSize(20, 20)

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setCheckable(True)
    self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    self.setFixedSize(self.SIZE)
    self.setCursor(Qt.CursorShape.PointingHandCursor)

  def sizeHint(self):  # noqa: N802 (Qt API)
    """The size Qt should give this pin when it can choose.

    Returns:
      A QSize square enough to draw a pin in and small enough to sit
      in a table row without stretching it.
    """
    return self.SIZE

  def paintEvent(self, _event):  # noqa: N802 (Qt API)
    """Draw the pin: head, shaft, a point, and a strike when it is out.

    Colours come from the widget's palette rather than being
    hard-coded, so the pin follows a light or dark QGIS theme without
    knowing anything about it.

    ONE GLYPH IN BOTH STATES since 2026-08-17, on the maintainer's
    instruction: unpinned is the pinned pin with a diagonal through
    it. What that replaces is a tilt-and-fill distinction -- out lay
    over at -35 degrees and was hollow -- which is legible only to
    somebody who has already learned it, where a struck-through
    symbol is a convention every reader arrives with.
    """
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    palette = self.palette()
    pinned = self.isChecked()
    ink = palette.color(palette.ColorRole.Highlight) if pinned \
      else palette.color(palette.ColorRole.WindowText)
    if not self.isEnabled():
      ink.setAlpha(70)
    width, height = self.width(), self.height()
    painter.save()
    painter.translate(width / 2.0, height / 2.0)
    # ONE GLYPH, STRUCK THROUGH WHEN IT IS OUT (maintainer's
    # instruction, 2026-08-17). The two states used to differ by TILT
    # and FILL -- out was a hollow pin lying over at -35 degrees, in
    # was filled and upright -- which reads at a glance only once
    # somebody has learned that a leaning pin means "not pinned".
    # A pin with a line through it is a mark every reader already
    # knows, and it says the same thing without being taught.
    painter.setPen(QPen(ink, 1.2))
    painter.setBrush(QBrush(ink))
    # The head is WIDE and FLAT, the way a tack's is seen side on --
    # a circle here is what made the old glyph a lens -- and the body
    # is a triangle narrowing to a point, since the taper is what
    # separates a tack from a magnifier.
    head = QPainterPath()
    head.addEllipse(QPointF(0.0, -height * 0.28),
                    width * 0.26, height * 0.11)
    body = QPainterPath()
    body.addPolygon(QPolygonF([
      QPointF(-width * 0.135, -height * 0.20),
      QPointF(width * 0.135, -height * 0.20),
      QPointF(0.0, height * 0.44)]))
    # United into ONE outline before stroking. Drawn as two shapes
    # the outline state showed both of their edges crossing inside
    # the glyph, which read as a cone rather than a pin; the filled
    # state hid the seam and looked fine, so this is a fault only the
    # unpinned half had.
    painter.drawPath(head.united(body).simplified())
    if not pinned:
      # STRUCK IN TWO PASSES, and the first is the reason it reads: a
      # single ink stroke over a filled glyph of the same ink is
      # invisible where it crosses it. So the window's own background
      # is laid down thicker first, cutting a channel through the
      # pin, and the ink line is drawn inside that channel -- which is
      # how every "not this" overlay is built and why they stay legible
      # over anything.
      reach = min(width, height) * 0.42
      cut = QPointF(-reach, -reach), QPointF(reach, reach)
      painter.setBrush(Qt.BrushStyle.NoBrush)
      painter.setPen(QPen(palette.color(palette.ColorRole.Window), 3.2))
      painter.drawLine(*cut)
      painter.setPen(QPen(ink, 1.6))
      painter.drawLine(*cut)
    painter.restore()
    if self.hasFocus():
      painter.setPen(QPen(palette.color(palette.ColorRole.Highlight), 1))
      painter.setBrush(Qt.BrushStyle.NoBrush)
      painter.drawRoundedRect(0, 0, width - 1, height - 1, 3, 3)
    painter.end()


class NoPinHere(QWidget):
  """Thin diagonal hatching where a pin cannot go.

  Args:
    parent: the owning widget, as usual in Qt.

  A pin can only name the FIRST class's upper bound and the LAST
  class's lower bound; every class between them has its breaks
  computed. Those cells were simply left empty, and an empty cell in
  a column called "Pin", with the table's own grid drawn round it,
  reads as a slot somebody has not filled in yet -- the maintainer's
  words, 2026-08-16: people might think they are able to add a pin
  there.

  Blank was tried first and is not available here for the reason the
  cell is misleading in the first place: the grid draws the box
  whether or not anything sits in it, so "nothing" and "an empty
  control" look the same. Hatching says NOT AVAILABLE in the one
  vocabulary a table has.

  THIS IS NOW THE ONLY PLACE THE PLUGIN HATCHES ANYTHING, and the
  history is worth a paragraph because it looks like a reversal and
  is not. The ramp swatch used the same mark for "no tile wears this
  class", and on 2026-08-16 the maintainer was asked whether two
  hatchings saying different KINDS of thing, met by a reader on one
  row, could be told apart; they ruled that 45 degrees in both is
  fine, since "nothing available here" covers both honestly and a
  second texture would ask somebody to distinguish two patterns at
  twelve pixels. On 2026-08-17 they ruled on a DIFFERENT question --
  whether the mark reads at all to somebody meeting it -- and took it
  off the swatch. The first ruling stands where it applies: do not
  differentiate this hatching from anything by angle or density on
  confusability grounds, because that was weighed.

  When the swatch's hatching DID read as ambiguous, the cause was
  ordinary and elsewhere: the diagonals were unclipped and spilled
  across neighbouring stripes.

  It takes no clicks and no focus: it is a statement, not a control.
  """

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

  def paintEvent(self, _event):  # noqa: N802 (Qt API)
    """Draw several thin diagonals across the cell.

    The ink is the palette's own text colour at low alpha, so the
    hatching follows a light or dark QGIS theme and stays quieter
    than any real control beside it.
    """
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    ink = self.palette().color(self.palette().ColorRole.WindowText)
    ink.setAlpha(95)
    painter.setPen(QPen(ink, 1.0))
    width, height = self.width(), self.height()
    # every fourth pixel, running corner to corner, so a narrow cell
    # still gets several lines rather than one lonely stroke
    step = 4
    offset = -height
    while offset < width:
      painter.drawLine(offset, height, offset + height, 0)
      offset += step
    painter.end()


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
    pinned: the class bounds already set by hand, as ``{"low":
      float or None, "high": float or None}``. ``low`` is the first
      class's upper bound and ``high`` is the last class's lower
      bound. None or an empty dict means neither end is pinned.
    copy_targets: the other elements this one's classification may be
      copied to, as [(tile_id, label)] in table order. Empty means no
      dropdown is built at all -- an element with no sibling to copy
      to should not be offered a control that can do nothing.
    copy_to: callback(tile_id) -> message or None. Called when a
      target is chosen; a message means it refused. The dropdown
      returns to reading "Copy to..." either way, so it never sits
      showing a completed action as though it were a state.
    pin_changed: callback(which, value) -> a refusal MESSAGE, or the
      ladder the map now draws as ``[(lower, upper), ...]``, where
      ``which`` is "low" or "high" and ``value`` is a float or None
      to unpin. The dialog validates, applies and repaints. A
      returned STRING means it REFUSED, and the editor puts the
      control back where it was; anything else is the new ladder,
      which the window redraws itself from -- a pin recomputes every
      break between the pinned ones, so "not refused" is not enough
      to keep the window honest. The editor decides nothing about
      what is legal, for the same reason it computes no colours:
      the rule lives with the map, not with the window.

  The values come from the REGION layer rather than from the output,
  so this works before anything has been generated. One consequence
  is worth knowing: at a coarse spacing some areas receive no tiles,
  so a value listed here may not appear on the map at all.
  """

  def __init__(self, tile_id, field, order, colours, picked,
               parent=None, *, bounds=None, locked=False,
               range_bounds=None, ramp_name=None, reverse=False,
               range_changed=None, pinned=None, pin_changed=None,
               copy_targets=(), copy_to=None, defaults=None):
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
    self._pinned = dict(pinned or {})
    self._pin_changed = pin_changed
    # {"low": (PinButton, QDoubleSpinBox)}, filled by whichever
    # presentation this dress uses: the table's own column for a
    # classed style, the clamp strip above it for Unclassed. One
    # record, one set of handlers, two places to put the controls.
    # {"low": [(pin, box), ...], "high": [...]} -- a LIST, because an
    # end may be named by the table's Pin column and by the clamp
    # strip at once. Keyed by the end rather than by the control, so
    # a handler always knows which boundary it is being asked about.
    self._pin_widgets = {}
    # What the scheme would compute for each end with NOTHING pinned,
    # as [(lower, upper), ...]. It is what makes a pin follow the
    # bound: moving a spin box away from this number IS pinning, and
    # putting it back is unpinning, so the control and the state can
    # never disagree. None when the dialog did not supply it, in
    # which case the pin goes back to being clicked explicitly.
    self._defaults = list(defaults) if defaults else None
    # Which row is the last CLASS, which is the last row unless a
    # no-data row follows the classes. Computed once, because two
    # places ask and a second reading of "last row" is how the pin
    # would land on the no-data row.
    # EVERY trailing absence row, not just one. This counted a single
    # no-data row until 2026-08-16, when the paired layer gained a row
    # per kind of unplaceable value -- so with an infinity present the
    # "last class" was an absence row, and the pin would have landed
    # on it.
    absence_keys = {key for key, _v, _l, _f in bridge.ABSENCE_KINDS}
    self._last_class_row = len(order) - 1
    while self._last_class_row >= 0 \
        and order[self._last_class_row] in absence_keys:
      self._last_class_row -= 1
    self._pins_offered = (bounds is not None and pin_changed is not None)

    layout = QVBoxLayout(self)
    # The range section goes in FIRST, before even the heading: it is
    # the live control in Unclassed mode and must never scroll out of
    # reach, so it sits above everything the table's scroll bar can
    # move. Its widths are settled later, once the table has decided
    # how wide the window is.
    # The Copy to... dropdown goes ABOVE everything, including the
    # range section: it acts on the whole of what this window shows,
    # so it reads as a heading rather than as one more control among
    # the classes.
    if bounds is not None and copy_targets and copy_to is not None:
      self._build_copy_row(layout, copy_targets, copy_to)
    if range_bounds is not None:
      self._build_range_section(layout, range_bounds)
    # ...and, for Quant: Unclassed only, the clamp: the same two pins
    # the classed table carries in a column, put above the list
    # instead. Fifty faded slivers are a preview rather than an
    # editing surface, and pinning row 0 of fifty is a strange way to
    # say "the ramp starts at 10". Same record, same handlers, same
    # glyph -- one feature wearing the dress that fits each style.
    if bounds is not None and locked and pin_changed is not None:
      self._build_clamp_strip(layout, bounds)

    # Two lines rather than one. The window is sized to the TABLE, and
    # a field name long enough to widen it past the table would drag
    # the whole dialogue wider for no benefit; broken in two, the
    # heading fits in the width the table already needs.
    heading = QLabel(f"Element '{tile_id}'\ncoloured by '{field}'")
    heading.setWordWrap(True)
    layout.addWidget(heading)

    # A PIN column, first, so the eye meets it on the way into the
    # row -- on BOTH graduated dresses since 2026-08-17.
    #
    # Unclassed used to be refused one, on the reasoning that fifty
    # faded slivers are a preview and that pinning row 0 of fifty is a
    # strange way to say "the ramp starts at 10". The clamp strip
    # above the table was built to say it better, and it does. What
    # that missed is that a user LEARNS the pin as a column: meeting
    # fifty faded rows and no column, they conclude the feature is not
    # there, which is what was reported. The maintainer's instruction
    # is to have both -- the column so the feature is where it was
    # learned, the strip because it is the better way to say it.
    #
    # The cost is that one end is now named by TWO controls, and
    # everything below about keeping them in step is that cost.
    self._pin_column = self._pins_offered
    columns = 2 if self._bounds is None else 3
    if self._pin_column:
      columns += 1
    self.table = QTableWidget(len(self._values), columns, self)
    self.table.setHorizontalHeaderLabels(
      ["Value", "Colour"] if self._bounds is None
      else (["Pin", "Lower", "Upper", "Colour"] if self._pin_column
            else ["Lower", "Upper", "Colour"]))
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
        # The catch-all is PARENTHESISED here and bare in the
        # graduated list, and the difference is deliberate: this
        # column holds nothing but the data's own values, so the
        # brackets are what say "not one of them". A graduated row
        # carries bounds beside every real class and needs no such
        # mark. Wrapped at the call site rather than inside
        # `_label_for`, because the two lists want different words
        # from it and a single answer cannot serve both -- which is
        # exactly what went wrong when a second `_label_for` was
        # written below the first instead of replacing it.
        label = self._label_for(value)
        if _is_absence(value):
          label = f"({label})"
        cell = QTableWidgetItem(label)
        cell.setToolTip(label)    # the full value, however long
        # Values right, colours left, so the two columns meet at the
        # middle of the window: the eye runs down the gap between a
        # value and its colour instead of across a gap that widens
        # with every short name. The header keeps Qt's own alignment,
        # which is what tells you it is a header.
        cell.setTextAlignment(Qt.AlignmentFlag.AlignRight
                              | Qt.AlignmentFlag.AlignVCenter)
        if _is_absence(value):
          # separated from the data's own values, because it is not
          # one
          font = cell.font()
          font.setItalic(True)
          cell.setFont(font)
        self.table.setItem(row, 0, cell)
      else:
        offset = 1 if self._pin_column else 0
        if _is_absence(value):
          # NOT A CLASS, and the row says so instead of pretending.
          # These are the element's tiles whose value is missing;
          # they have no bounds, they cannot be pinned, and the
          # classifier has never heard of them. They appear here at
          # all so that No data is ONE MORE COLOUR a person sets in
          # the same window as the rest -- two layers in QGIS, one
          # element in this dialog. (Maintainer's design, 2026-08-16.)
          # ITS OWN KIND, not a fixed word. This said "no data" for
          # every absence row, which was right while there was one and
          # became three rows reading the same thing the day the
          # paired layer learned to tell a NULL from an infinity. The
          # label comes from ABSENCE_KINDS, so this window, the legend
          # and the map cannot disagree about what a row means.
          cell = QTableWidgetItem(self._label_for(value))
          font = cell.font()
          font.setItalic(True)          # as the categorical catch-all
          cell.setFont(font)
          cell.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                | Qt.AlignmentFlag.AlignVCenter)
          self.table.setItem(row, offset, cell)
          self.table.setItem(row, offset + 1, QTableWidgetItem(""))
          if self._pin_column:
            self.table.setCellWidget(row, 0, NoPinHere())
        else:
          # Graduated: the class's two bounds, read-only, one per
          # cell. Right-aligned like the categorical values, and for
          # the same reason: numbers are compared down a column by
          # their ends.
          for col, bound in enumerate(self._bounds[row]):
            cell = QTableWidgetItem(self._format_bound(bound))
            cell.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                  | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, col + offset, cell)
          # ...except the two a pin makes editable: the FIRST class's
          # upper bound and the LAST class's lower bound, which are
          # the two boundaries a pin can name. The spin box is
          # present whether or not the end is pinned: swapping a
          # widget in and out on every toggle is how a cell comes to
          # hold a dead reference.
          #
          # THE LAST CLASS IS NOT ALWAYS THE LAST ROW. A no-data row
          # sits below every class when the element has missing
          # values, and reading "last row" as "last class" would have
          # given it the high pin -- a pin on something that has no
          # bound to pin.
          if self._pin_column:
            which = ("low" if row == 0 else
                     "high" if row == self._last_class_row else None)
            if which is not None:
              self._install_pin_row(row, which)
            else:
              # a middle class: its breaks are computed, and the cell
              # says so rather than sitting empty and looking free
              self.table.setCellWidget(row, 0, NoPinHere())

      # The colour button is the last column in either mode.
      self.table.setCellWidget(row, columns - 1,
                               self._colour_button(value))

    self._size_columns()

    if self._locked:
      # The Unclassed list is watched, not edited: the buttons are
      # already disabled (see _colour_button), and the text is faded
      # so the window says so at a glance. Only the table fades; the
      # range section above stays fully opaque.
      #
      # FADED PER ITEM, AND NOT WITH A GRAPHICS EFFECT, which is what
      # this did until 2026-08-17. `QGraphicsOpacityEffect` renders
      # its source into an offscreen pixmap, and `QAbstractScrollArea`
      # scrolls by BLITTING rather than repainting -- so the cached
      # source and the blitted viewport disagree and the old rows stay
      # composited under the new ones. The maintainer's screenshot
      # showed exactly that: a second, faint set of class bounds
      # behind the live ones, each about one row out. Unclassed is
      # where it bites because fifty classes are what make the table
      # scroll at all.
      #
      # HONEST LIMIT: the artefact lives in the window system's
      # backing store and could not be reproduced offscreen --
      # `grab()` repaints cleanly, and a scrolled render matched a
      # force-repainted one on 32,900 sampled pixels. So this removes
      # the mechanism the evidence points at rather than a fault
      # anything here could observe, and it wants confirming on a real
      # screen. What IS asserted by the suite is that no effect is
      # installed, since that is the cause and it is checkable.
      #
      # The palette's own disabled colour rather than a made-up grey:
      # it is what every other Qt widget uses to say "not yours to
      # edit", so the window agrees with the rest of QGIS and follows
      # a user's theme instead of assuming a light one.
      faded = self.table.palette().color(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText)
      for row in range(self.table.rowCount()):
        for column in range(self.table.columnCount()):
          item = self.table.item(row, column)
          if item is not None:
            item.setForeground(faded)

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

  def _build_copy_row(self, layout, targets, copy_to):
    """The "Copy to..." dropdown, above everything else in the window.

    Args:
      layout: the window's vertical layout.
      targets: [(tile_id, label)] for the elements this one may be
        copied to, in table order.
      copy_to: callback(tile_id) -> message or None; a message means
        the copy was refused and is already on the note line.

    Returns:
      None. The dropdown's first entry is the prompt "Copy to..." and
      carries no data, so choosing it does nothing; picking a target
      copies at once and the box returns to the prompt. It never sits
      showing a target as though the element were somehow bound to
      it: a copy is an act, not a state, and a control that remembers
      an act reads as a setting nobody set.
    """
    row = QWidget()
    line = QHBoxLayout(row)
    line.setContentsMargins(0, 0, 0, 0)
    box = QComboBox()
    box.addItem("Copy to...", None)
    for tile_id, label in targets:
      box.addItem(label, tile_id)
    box.setToolTip("Send this element's classes, colours, pins and "
                   "class count to another element")

    def chosen(index):
      target = box.itemData(index)
      if target is None:
        return
      copy_to(target)
      # back to the prompt whether it was taken or refused, without
      # re-entering this handler
      box.blockSignals(True)
      box.setCurrentIndex(0)
      box.blockSignals(False)

    box.activated.connect(chosen)
    line.addWidget(box, 0, Qt.AlignmentFlag.AlignVCenter)
    line.addStretch(1)
    self._copy_box = box
    layout.addWidget(row)

  def _build_clamp_strip(self, layout, bounds):
    """The Unclassed dress of the pins: two ends, above the table.

    Args:
      layout: the window's vertical layout, to add the strip to.
      bounds: the class bounds, from which the first and last are
        taken -- with fifty of them, those are the ends of the ramp
        rather than the ends of any class anybody chose.

    Returns:
      None. Builds the same PinButton and bound box the classed table
      builds, registered through the same `_register_pin` and driven
      by the same handlers, so the two presentations cannot come to
      mean different things. The wording is the difference: "Ramp
      starts at" and "Ramp ends at" rather than a pin on a class,
      because that is what fifty equal steps make of it.

      SINCE 2026-08-17 THIS SITS BESIDE THE PIN COLUMN rather than
      instead of it, on the maintainer's instruction: the column so
      somebody who learned the pin there still finds it, the strip
      because it says the thing better. `_sync_pin_controls` is what
      stops the two disagreeing.
    """
    strip = QWidget()
    row = QHBoxLayout(strip)
    row.setContentsMargins(0, 0, 0, 0)
    for which, label in (("low", "Ramp starts at"),
                         ("high", "Ramp ends at")):
      lower, upper = bounds[0] if which == "low" else bounds[-1]
      pin = PinButton()
      pin.setChecked(self._pinned.get(which) is not None)
      pin.setToolTip("Pin this end; the steps between are spread over "
                     "what is left")
      box = self._bound_box(upper if which == "low" else lower)
      row.addWidget(pin, 0, Qt.AlignmentFlag.AlignVCenter)
      row.addWidget(QLabel(label), 0, Qt.AlignmentFlag.AlignVCenter)
      row.addWidget(box, 0, Qt.AlignmentFlag.AlignVCenter)
      row.addSpacing(12)
      self._register_pin(which, pin, box)
    row.addStretch(1)
    layout.addWidget(strip)

  def _bound_box(self, value):
    """A spin box holding one class bound.

    Args:
      value: the bound to show, as a float.

    Returns:
      A QDoubleSpinBox sized to the column it must express. What is
      LEGAL is still decided by the map's own data and reported back
      through ``pin_changed``; a range set here refuses a number for
      a reason this window cannot explain, which is the opposite of a
      guardrail, so the limits below are generous rather than
      meaningful and exist only because Qt insists on having some.

    THE RANGE AND THE DECIMALS COME FROM THE DATA, and both used to be
    constants that ordinary geographic columns walk straight past.
    Measured 2026-08-15 with real widgets: the range was plus or minus
    1e12, so a province area of 1.875e12 square metres appeared in the
    box as 1e12 and pinned there; typing 3000000000000 left
    300000000000, a factor of ten, with nothing said. At the other end
    six decimals rounded a rate of 4e-07 to zero and 8.5e-07 to 1e-06.
    On twenty provinces at k=4, pinning the number the control
    produced rather than the number typed moved ELEVEN of twenty areas
    into a different class, and ``pin_problem`` accepts both, because
    both are inside the data.

    The docstring above this used to say the range was "wide open",
    which is what the code intended and not what it did.
    """
    # every endpoint the ladder holds, since the box must be able to
    # show any of them and a user may type between any two
    edges = [float(x) for pair in (self._bounds or []) for x in pair
             if isinstance(x, (int, float)) and math.isfinite(float(x))]
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
      edges.append(float(value))
    magnitude = max((abs(x) for x in edges), default=1.0) or 1.0
    span = (max(edges) - min(edges)) if len(edges) > 1 else magnitude
    box = QDoubleSpinBox()
    # ...enough decimal places to separate values on THIS column, and
    # no more: nine significant places below the span, which gives 0
    # on a column of square metres and eleven on a column of rates
    # `span > 0` is not the same question as "is this a number I can
    # take a logarithm of". A column with no usable values at all
    # gives Unclassed fifty classes running from 1.797e308 to -inf,
    # so the span is INFINITE, `span > 0` is true, and log10 of it
    # overflows -- an unhandled OverflowError escaping a Qt slot, so
    # the Edit colours button silently does nothing and QGIS throws
    # up its Python error window. Three clicks and no Generate.
    # Measured 2026-08-16 by a stochastic hunt at seed 301.
    places = (9 - int(math.floor(math.log10(span)))
              if math.isfinite(span) and span > 0 else 6)
    box.setDecimals(max(0, min(12, places)))
    box.setRange(-magnitude * 100.0, magnitude * 100.0)
    box.setValue(float(value))
    box.setKeyboardTracking(False)   # one signal per finished edit
    box.setAlignment(Qt.AlignmentFlag.AlignRight
                     | Qt.AlignmentFlag.AlignVCenter)
    return box

  def _register_pin(self, which, pin, box):
    """Wire one pin-and-bound pair to the end it names.

    Args:
      which: "low" for the first class's upper bound, "high" for the
        last class's lower bound.
      pin: the PinButton for this control.
      box: the QDoubleSpinBox holding this end's bound.

    Returns:
      None. The pair is added to `_pin_widgets[which]` and its three
      signals are connected, each carrying the PAIR that fired.

    THE PAIR TRAVELS WITH THE SIGNAL, and that is the whole reason
    this exists. Two controls may name one end -- the table's Pin
    column and the clamp strip -- so a handler told only "low" cannot
    know which box holds the number the user just typed. It used to
    read `_pin_widgets[which]`, which held ONE pair, so a second
    builder would have silently orphaned the first: still wired, still
    clickable, and applying the other control's number.
    """
    pair = (pin, box)
    self._pin_widgets.setdefault(which, []).append(pair)
    pin.toggled.connect(
      lambda on, w=which, p=pair: self._pin_toggled(w, on, p))
    box.editingFinished.connect(
      lambda w=which, p=pair: self._bound_edited(w, p))
    box.valueChanged.connect(
      lambda _v, w=which, p=pair: self._bound_moved(w, p))

  def _sync_pin_controls(self, which, source=None):
    """Make every control naming one end agree with the settled record.

    Args:
      which: "low" or "high".
      source: the pair the user just acted on, left alone so their
        own number is never rewritten under their hands.

    Returns:
      None. Every other pin for that end is set to match whether the
      end is pinned, and every other box to the pinned value. Signals
      are blocked throughout, or putting a control right would fire
      the handler that put it right.
    """
    value = self._pinned.get(which)
    for pair in self._pin_widgets.get(which, []):
      pin, box = pair
      if pin.isChecked() != (value is not None):
        pin.blockSignals(True)
        pin.setChecked(value is not None)
        pin.blockSignals(False)
        pin.update()
      if pair is source or value is None:
        continue
      box.blockSignals(True)
      box.setValue(float(value))
      box.blockSignals(False)

  def _install_pin_row(self, row, which):
    """Put a pin and an editable bound on one end row of the table.

    Args:
      row: the table row -- the first or the last, nothing else.
      which: "low" for the first class's upper bound, "high" for the
        last class's lower bound.

    Returns:
      None. The pin goes in column 0 and the editable bound replaces
      the read-only cell it shares a meaning with: the UPPER cell on
      the first row, the LOWER cell on the last, which are the two
      boundaries a pin can name. A pinned bound is the boundary
      between the pinned class and the rest, so no other cell in
      those rows becomes editable -- the outer edges belong to the
      data.
    """
    lower, upper = self._bounds[row]
    pin = PinButton()
    pin.setChecked(self._pinned.get(which) is not None)
    pin.setToolTip("Pin this bound; the rest are computed around it")
    box = self._bound_box(upper if which == "low" else lower)
    box.setToolTip("Set this bound; moving it off the computed value "
                   "pins it")
    column = 2 if which == "low" else 1     # Upper on top, Lower below
    holder = QWidget()
    layout = QHBoxLayout(holder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(pin, 0, Qt.AlignmentFlag.AlignCenter)
    self.table.setCellWidget(row, 0, holder)
    self.table.setCellWidget(row, column, box)
    self._register_pin(which, pin, box)

  def _default_bound(self, which):
    """The number the scheme computes for one end with no pin on it.

    Args:
      which: "low" for the first class's upper bound, "high" for the
        last class's lower bound.

    Returns:
      The bound as a float, or None when the dialog supplied no
      defaults -- in which case nothing can be inferred from the spin
      box and the pin stays a thing you click.
    """
    if not self._defaults:
      return None
    try:
      return float(self._defaults[0][1] if which == "low"
                   else self._defaults[-1][0])
    except (IndexError, TypeError, ValueError):
      return None

  def _bound_moved(self, which, source=None):
    """Follow the spin box: off the computed value is pinned, on it is not.

    Args:
      which: "low" or "high".
      source: the (pin, box) pair that fired, where an end is named
        by more than one control. Omitted, the first registered
        control answers -- which is right for a classed row, where
        there is only ever one.

    Returns:
      None. Applies through the same handlers a click goes through,
      so a pin made this way is the same pin in every respect.

    The maintainer's design, 2026-08-16: the up/down control is live
    at all times, moving it to anything other than what the
    classification would compute turns the pin ON, and a change that
    puts it back turns the pin OFF. It fires on a VALUE CHANGE and
    never on a repaint -- which is what lets somebody click the pin
    while the box already shows the computed number without the pin
    instantly undoing itself.

    The consequence, stated because it is a real one: a bound pinned
    deliberately AT the computed value releases if it is nudged away
    and back. Holding it would need the explicit click remembered
    separately from the value, and two pins that look identical
    behaving differently is the worse trade.
    """
    pair = source or next(iter(self._pin_widgets.get(which, [])), None)
    if pair is None:
      return
    pin, box = pair
    default = self._default_bound(which)
    if default is None:
      return
    # a tolerance of half the box's own last digit: the number shown
    # is rounded to those decimals, so an exact comparison would call
    # the displayed default "different" and pin it
    try:
      tolerance = 0.5 * (10.0 ** -box.decimals())
    except Exception:
      tolerance = 1e-9
    wants = abs(float(box.value()) - default) > tolerance
    if wants != pin.isChecked():
      pin.blockSignals(True)
      pin.setChecked(wants)
      pin.blockSignals(False)
      pin.update()
      self._pin_toggled(which, wants, pair)
    elif wants:
      self._bound_edited(which)

  def _redraw_bounds(self, bounds):
    """Show the ladder the map now draws, after a pin moved it.

    Args:
      bounds: ``[(lower, upper), ...]`` as the map now holds them, or
        anything falsy, which leaves the window alone.

    Returns:
      None. The read-only cells are rewritten and the two pin boxes
      moved to the boundaries they now name, with their signals
      blocked so putting a number in place does not read as somebody
      typing it.

    WHY THIS EXISTS. `self._bounds` was set once, at construction, and
    a pin recomputes every break between the pinned ones -- so the
    window went on printing the ladder from BEFORE the pin while the
    map drew the one after it. That is worse than merely stale: the
    disabled box for the other end still showed its old number, and
    clicking that pin applied the OLD number, moving three more breaks
    that nobody had touched. Measured 2026-08-15 with low pinned at
    30: the map read 30, 42, 55.5, 77 and the window read 14.2, 30,
    55, with the high box offering 55 for a boundary then at 77.

    The asymmetry that hid it is worth naming: `range_changed` hands
    its new colours back and the window repaints from them, while
    `pin_changed` answered only "refused or not".
    """
    if not bounds:
      return
    self._bounds = [(float(low), float(high)) for low, high in bounds]
    offset = 1 if self._pin_column else 0
    for row, pair in enumerate(self._bounds):
      if row >= self.table.rowCount():
        break
      for col, bound in enumerate(pair):
        cell = self.table.item(row, col + offset)
        if cell is not None:
          cell.setText(self._format_bound(bound))
    # ...and the two boxes, which name boundaries rather than cells:
    # the first class's upper bound and the last class's lower one
    for which, value in (("low", self._bounds[0][1]),
                         ("high", self._bounds[-1][0])):
      # EVERY control naming that end, not one: the table's Pin column
      # and the clamp strip both show it, and a stale second copy is
      # how a user comes to click a pin that applies a number the map
      # left behind three breaks ago.
      for _pin, box in self._pin_widgets.get(which, []):
        box.blockSignals(True)
        box.setValue(float(value))
        box.blockSignals(False)

  def _pin_toggled(self, which, on, source=None):
    """Pin or unpin one end, and put the control back if refused.

    Args:
      which: "low" or "high".
      on: True to pin at whatever the spin box currently shows,
        False to unpin and let that break be computed again.
      source: the (pin, box) pair that fired, where an end is named
        by more than one control. Omitted, the first registered
        control answers -- which is right for a classed row, where
        there is only ever one.

    Returns:
      None. The dialog validates and applies; a message back means it
      refused, and the pin returns to where it was without the map
      having moved. The signal is blocked while it is put back, or
      the revert would fire this handler a second time and report the
      refusal twice.
    """
    pair = source or next(iter(self._pin_widgets.get(which, [])), None)
    if pair is None:
      return
    pin, box = pair
    value = float(box.value()) if on else None
    answer = self._pin_changed(which, value) if self._pin_changed else None
    if isinstance(answer, str):
      pin.blockSignals(True)
      pin.setChecked(not on)
      pin.blockSignals(False)
      return
    self._pinned[which] = value
    # the ladder the map now draws, so the window and the map agree
    self._redraw_bounds(answer)
    self._sync_pin_controls(which, pair)

  def _bound_edited(self, which, source=None):
    """Move a pinned bound to the number just typed.

    Args:
      which: "low" or "high".
      source: the (pin, box) pair that fired, where an end is named
        by more than one control. Omitted, the first registered
        control answers -- which is right for a classed row, where
        there is only ever one.

    Returns:
      None. Refused edits put the previous number back, so the box
      never shows a bound the map does not have -- the whole point of
      reverting rather than clamping is that a typed number is either
      honoured or visibly rejected, never quietly changed into a
      different one.
    """
    pair = source or next(iter(self._pin_widgets.get(which, [])), None)
    if pair is None:
      return
    pin, box = pair
    if not pin.isChecked():
      return
    value = float(box.value())
    answer = self._pin_changed(which, value) if self._pin_changed else None
    if isinstance(answer, str):
      previous = self._pinned.get(which)
      box.blockSignals(True)
      if previous is not None:
        box.setValue(float(previous))
      box.blockSignals(False)
      return
    self._pinned[which] = value
    # every break between the pins has just moved, so the rest of the
    # window must say so too
    self._redraw_bounds(answer)
    self._sync_pin_controls(which, pair)

  def _label_for(self, value) -> str:
    """The words one row shows in its left-hand column.

    Called for EVERY categorical row and for the graduated list's
    absence rows, so it must answer for an ordinary value as well as
    for a kind of absence. There were two of these for a few hours on
    2026-08-16 -- a second written below the first rather than
    replacing it -- and Python keeps the last, so every categorical
    value was labelled "no data" and the window that exists to say
    which value draws in which colour said nothing of the sort.

    Args:
      value: the row's key: one of the ABSENCE_KINDS keys, or a value
        the field actually takes.

    Returns:
      That kind's label where the key names one, and otherwise the
      value as it reads. Never a fixed word for an unrecognised key:
      the categorical list is mostly unrecognised keys, so a
      catch-all answer here is wrong on nearly every row.
    """
    # The labels come from ABSENCE_KINDS so the editor, the legend and
    # the map cannot drift apart, and a fourth kind added there
    # appears here without an edit.
    for key, _stored, label, _fill in bridge.ABSENCE_KINDS:
      if value == key:
        return label
    return str(value)

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
      if self._pin_column:
        # The pin column is exactly as wide as a pin plus breathing
        # room. This is the window widening the design predicted, and
        # it is the whole of it: the bound columns already hold a
        # spin box comfortably at BOUND_WIDTH.
        column_widths.insert(0, PIN_WIDTH)
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
