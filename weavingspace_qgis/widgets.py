"""Small Qt widgets shared by the dialog and the colour editor.

There are two, and the first exists because two boxes in this plugin
need the same trick for the same reason. A `QDoubleSpinBox` shows a
value with exactly `decimals` places, always, so a box wide enough for
a rate of 4e-07 prints a round 500 as "500.000000" -- which is what a
tester met on 2026-08-17 and reported.

THE TEMPTING FIX IS THE DESTRUCTIVE ONE, and this project made it
once. Lowering `decimals` to tidy the display also lowers what the box
can HOLD: `decimals` governs display AND input AND storage together,
and a box at zero decimals cannot represent 500.5, so typing it gave
501 and the map was drawn from the rounded number with nothing said.
The rule that came out of that is in CLAUDE.md and is the whole reason
this module exists: a DISPLAY rule belongs in `textFromValue`, which
touches neither the stored value nor the validator.

WHY A MODULE RATHER THAN A METHOD IN EACH. Both boxes had their own
copy for a day. This project's own record is full of one behaviour
described in two places drifting apart -- it is the shape behind the
re-read rule, the twin-anchor rule and half the defects of 2026-08-16
-- and a trimmer is small enough that two copies look harmless right
up until one of them learns about locales and the other does not.
`dialog.py` and `category_editor.py` both already import from here
rather than from each other, which also keeps the import graph acyclic
(dialog imports category_editor, so the reverse could not happen).
"""
from __future__ import annotations

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QDoubleSpinBox


class TrimmedSpinBox(QDoubleSpinBox):
  """A spin box that keeps its precision and prints no idle zeros.

  Subclass this wherever a box must span magnitudes -- spacing runs
  from 1e-6 to 1e12, a class bound may be a rate or a province area in
  square metres -- so that one `decimals` setting can be generous
  enough for the smallest case without punishing the largest with a
  row of zeros.

  What it does NOT do is change the value, the range or the validator.
  A caller still chooses `decimals` for what the box must be able to
  HOLD, and this only decides how the held number is written down.
  """

  def textFromValue(self, value):                      # noqa: N802 (Qt API)
    """The number as a reader wants it: no trailing zeros, no rounding.

    Args:
      value: the number the box currently holds.

    Returns:
      Qt's own text for that value with idle zeros removed -- "500"
      rather than "500.000000", "500.5" rather than "500.500000", and
      "0.000001" unchanged, since none of its zeros are idle. A value
      with nothing after the point loses the point too.

    Built by TRIMMING Qt's own answer rather than formatting the
    number here, so the decimal point and any group separator stay the
    locale's. This project has already had a locale defect that took
    two CI rounds to name, and formatting a number by hand is how the
    next one arrives.
    """
    shown = super().textFromValue(value)
    point = self.locale().decimalPoint()
    if point and point in shown:
      shown = shown.rstrip("0").rstrip(point)
    return shown


class MarkableSpinBox(TrimmedSpinBox):
  """A bound box that shows whether its number is a person's.

  The class-bound boxes each hold a number that is either COMPUTED by
  the classification or SET by the user, and a reader cannot tell
  which from the number itself. A pin column said it for two of them
  and said nothing about the ladder's outer edges; the maintainer's
  instruction of 2026-08-19 replaced the column with a mark on the box
  itself, identically for a floor, a pin or a ceiling, so one
  convention covers all four and the table loses a column.

  PAINTED, NOT STYLESHEETED, for the reason `PinButton` and
  `ToggleSwitch` are painted: a stylesheet border on a
  `QDoubleSpinBox` replaces the platform's own frame rather than
  adding to it, so the box stops looking like the others on that
  platform -- and this project has a standing rule against controls
  whose appearance depends on a theme it has never relied on. Drawing
  over the frame after Qt has drawn it is a few lines and looks the
  same on every machine.

  Args:
    parent: the owning widget, as usual in Qt.
  """

  # Emitted when the cross inside the box is clicked. A SIGNAL rather
  # than the widget restoring a value itself, because the number to go
  # back to is the CLASSIFICATION's, which this widget has no way to
  # know -- and a box that guessed would be a second description of a
  # ladder the editor already holds.
  cleared = pyqtSignal()

  def __init__(self, parent=None):
    """Start unmarked, which is what a computed bound is.

    THE LINE EDIT IS WATCHED, and that is what makes the cross
    clickable at all. A QDoubleSpinBox is a composite: Qt puts a
    QLineEdit inside it, and on every platform measured that child
    starts at x=1 to x=3 and runs almost the full width -- so it
    covers the cross entirely and takes the press, leaving
    `mousePressEvent` on this widget never called for the one region
    that needs it. Measured 2026-08-19: the line edit at (3, 3, 96,
    20) over a cross at (5, 8, 10, 10), and `childAt` the cross's own
    centre answering QLineEdit. The mark had been drawn since it was
    written and had never once been clickable; the guard passed
    because it handed the event straight to the box, which proves the
    HANDLER works and not that anybody can reach it.
    """
    super().__init__(parent)
    self._marked = False
    edit = self.lineEdit()
    if edit is not None:
      edit.installEventFilter(self)

  def eventFilter(self, watched, event):               # noqa: N802 (Qt API)
    """Let a click on the cross through to this widget's own handler.

    Args:
      watched: the object the event was sent to; only this box's own
        line edit is of interest.
      event: the Qt event.

    Returns:
      True when the press landed on the cross, which consumes it so
      the line edit never sees it and no text cursor is placed;
      otherwise whatever the base class decides, so ordinary typing
      and selection are untouched.
    """
    from qgis.PyQt.QtCore import QEvent
    if self._marked and event.type() == QEvent.Type.MouseButtonPress \
        and watched is self.lineEdit():
      point = event.position().toPoint() \
          if hasattr(event, "position") else event.pos()
      # the child's coordinates are not this widget's, and the cross
      # is measured in THIS widget's
      here = watched.mapTo(self, point)
      if self._clear_rect().adjusted(-3, -3, 3, 3).contains(here):
        self.cleared.emit()
        return True
    return super().eventFilter(watched, event)

  def _keep_the_text_clear(self):
    """Reserve room at the left so digits do not sit under the cross.

    Returns:
      None. Sets the line edit's left text margin to the cross's own
      width plus a little air while marked, and back to nothing when
      not, so an unmarked box is laid out exactly as every other spin
      box in the window. Margins move the TEXT and not the widget,
      which is why the event filter above is still needed: the line
      edit goes on covering these pixels whatever its margins say.
    """
    edit = self.lineEdit()
    if edit is None:
      return
    room = self._clear_rect().right() + 3 if self._marked else 0
    edit.setTextMargins(room, 0, 0, 0)

  def setMarked(self, marked):                         # noqa: N802 (Qt API)
    """Say whether this number is the user's rather than computed.

    Args:
      marked: True to draw the heavy outline, False for none.

    Returns:
      None. Repaints only when the state actually changes, so calling
      this on every refresh costs nothing.
    """
    marked = bool(marked)
    if marked != self._marked:
      self._marked = marked
      self._keep_the_text_clear()
      self.update()

  def isMarked(self):                                  # noqa: N802 (Qt API)
    """Whether the heavy outline is being drawn.

    Returns:
      True when this box is showing a number somebody set.
    """
    return self._marked

  def paintEvent(self, event):                         # noqa: N802 (Qt API)
    """Draw the box, then its mark on top.

    Args:
      event: the Qt paint event, passed through untouched.

    Returns:
      None.

    The rectangle is inset by half the pen width so the stroke lands
    INSIDE the widget: drawn on the frame itself, Qt clips the outer
    half and the line reads thinner on one side than the other, which
    is the kind of asymmetry that looks like a rendering fault rather
    than a signal.
    """
    super().paintEvent(event)
    if not self._marked:
      return
    from qgis.PyQt.QtCore import Qt as _Qt
    from qgis.PyQt.QtGui import QPainter, QPen
    painter = QPainter(self)
    try:
      painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
      pen = QPen(_Qt.GlobalColor.black)
      pen.setWidth(2)
      painter.setPen(pen)
      painter.setBrush(_Qt.BrushStyle.NoBrush)
      painter.drawRect(self.rect().adjusted(1, 1, -2, -2))
      # ...and the cross that gives the bound back, drawn INSIDE the
      # outline it belongs to. Same pen, so the two read as one mark
      # rather than as a control somebody has added to the box.
      cross = self._clear_rect()
      pen.setWidth(1)
      painter.setPen(pen)
      painter.drawLine(cross.topLeft(), cross.bottomRight())
      painter.drawLine(cross.bottomLeft(), cross.topRight())
    finally:
      painter.end()

  def _clear_rect(self):
    """Where the cross is drawn, and where a click on it counts.

    Returns:
      A QRect inside the box's left edge, square, sized from the
      widget's height so it scales with the row rather than being
      pinned to one screen's pixels.

    ON THE LEFT, DELIBERATELY. Qt puts the spin arrows against the
    RIGHT edge, and a clear target sharing that side is a target
    people hit by accident while stepping a number -- which on these
    boxes throws away a bound somebody set. One geometry, read by the
    painter and by the hit test alike, so the mark cannot be drawn in
    one place and clickable in another.
    """
    from qgis.PyQt.QtCore import QRect
    side = max(6, min(10, self.height() - 12))
    top = (self.height() - side) // 2
    return QRect(5, top, side, side)

  def mousePressEvent(self, event):                    # noqa: N802 (Qt API)
    """Give the bound back when the cross is clicked.

    Args:
      event: the Qt mouse event.

    Returns:
      None. Emits `cleared` and swallows the click when it landed on
      the cross; otherwise the box behaves exactly as a spin box does.

    Only while MARKED, because an unmarked box draws no cross and a
    click there is somebody reaching for the text.
    """
    if self._marked:
      position = event.position().toPoint() \
          if hasattr(event, "position") else event.pos()
      if self._clear_rect().adjusted(-3, -3, 3, 3).contains(position):
        self.cleared.emit()
        event.accept()
        return
    super().mousePressEvent(event)
