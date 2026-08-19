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

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QDoubleSpinBox, QWidget


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


# The SI prefixes, largest first, with the power each names. A bound
# follows the data and the data spans twelve orders of magnitude, so a
# column wide enough for 1023192923 is absurd for 1.56 and one sized
# for 1.56 elides a billion. Writing 1.02G costs four characters and
# says the same thing.
SI_PREFIXES = ((1e24, "Y"), (1e21, "Z"), (1e18, "E"), (1e15, "P"),
               (1e12, "T"), (1e9, "G"), (1e6, "M"), (1e3, "k"),
               (1e-3, "m"), (1e-6, "µ"), (1e-9, "n"),
               (1e-12, "p"), (1e-15, "f"), (1e-18, "a"),
               (1e-21, "z"), (1e-24, "y"))

# WHERE PLAIN DIGITS STOP EARNING THEIR ROOM. Between these two a
# number reads perfectly well as itself and a prefix would be
# affectation; outside them the digits stop fitting any column anybody
# would want. 1e5 rather than 1e3 deliberately: 1500 is a number
# people read, and "1.5k" for it would be the plugin being clever at a
# reader's expense.
SI_ABOVE = 1e5
SI_BELOW = 1e-3


class ClearMark(QWidget):
  """The cross that gives a bound back, as a widget rather than paint.

  A WIDGET BECAUSE PAINT COULD NOT BE SEEN. `MarkableSpinBox` drew
  this cross in its own `paintEvent`, five pixels from its left edge,
  which is inside the QLineEdit a QDoubleSpinBox puts there -- and Qt
  paints a child AFTER its parent, so the line edit's own background
  went over it every time. Measured 2026-08-19 on a marked box grabbed
  offscreen: 721 dark pixels for the heavy outline and ZERO inside the
  cross's own rectangle, on a mark that had been drawn since it was
  written and had never once been visible.

  The click was repaired that morning by watching the line edit, and
  the paint was left underneath it: the fix took the half that had
  been reported. A CHILD WIDGET ANSWERS BOTH AT ONCE -- it paints
  above the line edit and it takes the press by ordinary hit-testing,
  which is what a person's click does.

  It fills itself with the palette's Base colour, the line edit's own
  background, so the cross reads as sitting on the field rather than
  on a patch of something else.

  Args:
    parent: the box this belongs to.
  """

  clicked = pyqtSignal()

  def __init__(self, parent=None):
    """Start hidden; the box shows this when its number becomes a
    person's."""
    super().__init__(parent)
    self.setCursor(Qt.CursorShape.ArrowCursor)
    self.setToolTip("Give this bound back to the classification")

  def paintEvent(self, event):                         # noqa: N802 (Qt API)
    """Draw the field behind, then the two strokes.

    Args:
      event: the Qt paint event, unused.

    Returns:
      None.
    """
    from qgis.PyQt.QtGui import QColor, QPainter, QPen
    painter = QPainter(self)
    try:
      painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
      painter.fillRect(self.rect(), self.palette().base())
      # RED, AND THE REASON IS LEGIBILITY RATHER THAN ALARM
      # (maintainer's suggestion, 2026-08-19). Drawn in the same black
      # as the heavy outline it sits inside, and two pixels from it,
      # the left arm merges with the frame at this size: the mark was
      # reported as having its leftmost fifth CLIPPED when measurement
      # showed its ink whole and simply touching a line of the same
      # colour. A different hue separates the two without moving
      # either, and it also says "this undoes something", which is
      # what the mark is for.
      pen = QPen(QColor(178, 34, 34))
      pen.setWidth(2)
      painter.setPen(pen)
      # inset by two, so the strokes do not touch the edges and the
      # mark reads as a cross rather than as a filled square
      box = self.rect().adjusted(2, 2, -2, -2)
      painter.drawLine(box.topLeft(), box.bottomRight())
      painter.drawLine(box.bottomLeft(), box.topRight())
    finally:
      painter.end()

  def mousePressEvent(self, event):                    # noqa: N802 (Qt API)
    """Announce the click and consume it.

    Args:
      event: the Qt mouse event.

    Returns:
      None. Consumed so the press never reaches the line edit beneath
      and no text cursor is dropped into the number.
    """
    self.clicked.emit()
    event.accept()


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
    # THE CROSS IS A CHILD, not paint. See `ClearMark`: drawn by this
    # widget's own painter it landed under the line edit and was never
    # visible on any build, while the event filter below made it
    # clickable -- so the affordance worked and could not be found.
    # A child paints above its sibling and takes the press itself.
    self._cross = ClearMark(self)
    self._cross.clicked.connect(self.cleared)
    self._cross.hide()
    # ...AND THE FILTER STAYS, narrowly. The child covers the cross's
    # rectangle, so a press there reaches it and never the line edit;
    # this is for the platform where a stacking order goes otherwise,
    # where it costs one comparison and saves the affordance.
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
      self._place_the_cross()
      self.update()

  def _place_the_cross(self):
    """Put the clear mark where the geometry says, and on top.

    Returns:
      None. Shown only while marked, since an unmarked bound is the
      classification's and there is nothing to give back.

    RAISED EVERY TIME, not once at construction: a QAbstractSpinBox
    rebuilds and re-stacks its line edit on a style change, and a
    child that has fallen behind it is a cross nobody can see -- which
    is the whole defect this widget exists to end.
    """
    self._cross.setGeometry(self._clear_rect())
    self._cross.setVisible(self._marked)
    if self._marked:
      self._cross.raise_()

  def resizeEvent(self, event):                        # noqa: N802 (Qt API)
    """Keep the clear mark with the box as it changes size.

    Args:
      event: the Qt resize event, passed through untouched.

    Returns:
      None. `_clear_rect` is measured from the box's HEIGHT, so a row
      that grows moves the mark, and a mark left at the old geometry
      would sit off-centre or outside the frame.
    """
    super().resizeEvent(event)
    self._place_the_cross()

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
      # THE CROSS IS NOT DRAWN HERE, and it was until 2026-08-19. It
      # belongs inside this outline and this is the wrong brush for
      # it: the line edit covers those pixels and paints after us, so
      # every stroke put here was painted over. `ClearMark` is a child
      # widget instead. The outline stays, because it is drawn on the
      # FRAME, which is the one part of the box no child covers.
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
    # NINE, AND THE CEILING IS THE NUMBER'S. The mark takes its width
    # out of the line edit's text margin, so every pixel it gains the
    # number loses: at twelve, "1.56" came back "1.5" with the last
    # digit elided in a column this editor really uses. A bound box
    # that cannot show its bound is a worse fault than a small mark.
    side = max(8, min(9, self.height() - 10))
    top = (self.height() - side) // 2
    # CLEAR OF THE FRAME, not a fixed five pixels. The heavy outline is
    # two pixels wide and is drawn one pixel in, so it occupies the
    # first three or four columns; a mark starting at five sits two
    # pixels from a line of its own weight, which is close enough that
    # its left arm was reported as CLIPPED. Measured 2026-08-19: the
    # outline in columns 0 to 3 and the strokes in 7 to 11, both whole.
    # Asked of the style rather than assumed, since a frame is a
    # platform's business and this project has been wrong about a
    # hard-coded Qt geometry before.
    from qgis.PyQt.QtWidgets import QStyle
    frame = self.style().pixelMetric(
      QStyle.PixelMetric.PM_DefaultFrameWidth, None, self)
    return QRect(max(7, int(frame) + 5), top, side, side)

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
