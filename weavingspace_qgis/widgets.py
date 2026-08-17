"""Small Qt widgets shared by the dialog and the colour editor.

There is one of them, and it exists because two boxes in this plugin
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
