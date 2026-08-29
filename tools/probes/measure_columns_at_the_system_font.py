"""What does each table column actually NEED at a desktop font?

The maintainer's decision of 2026-08-29: the window's 54px overshoot
comes off the COLUMNS, not off the preview floor and not off the 1280
ceiling. Which columns have slack is a measurement rather than a
guess, so this asks each one what its own contents need.

THE FONT IS SET RATHER THAN THE PLATFORM SWITCHED. The overshoot was
found by launching without QT_QPA_PLATFORM=offscreen, which uses cocoa
and the system font at 13pt where offscreen gives Sans Serif at 9pt.
Setting the font under offscreen reproduces the metrics without
needing a window server, which is also how the guard will have to ask
-- a check that can only measure the font every runner supplies is
measuring nowhere anybody is.
"""

import os
import sys

sys.path.insert(0, os.environ.get("WS_REPO", os.getcwd()))

from tools.probe_kit import start                      # noqa: E402

HEADS = ["Tile id", "Variable", "Style", "Classes", "Colour ramp",
         "Reverse", "Opacity", "Categ colourmap src", "Edit colours"]


def report(probe, label, point_size=None, family=None):
  """Build the widest table there is and say what each column needs.

  Args:
    probe: the running `Probe`.
    label: what to print this reading as.
    point_size: a font size to impose, or None for whatever the
      platform gives.
    family: a font family to impose, or None.

  Returns:
    A dict of column index -> (width set, width the content needs).
  """
  from qgis.PyQt.QtGui import QFont
  from qgis.PyQt.QtWidgets import QApplication
  from weavingspace_qgis.dialog import (
    MAX_WINDOW_WIDTH, PREVIEW_FLOOR, WeavingSpaceDialog)
  suite = probe.suite

  if point_size is not None:
    font = QFont(family or QApplication.font().family())
    font.setPointSize(point_size)
    QApplication.setFont(font)

  probe.clear()
  layer = suite.make_region_layer()
  probe.project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=None)
  try:
    dlg.live_check.setChecked(False)
    dlg.layer_combo.setLayer(layer)
    suite._tick(200)
    # the widest state the table has, exactly as the guard stages it
    dlg.table.cellWidget(1, 1).setCurrentText("landcover")
    dlg._update_dynamic_columns()
    dlg.show()
    suite._tick(400)

    print()
    print("=" * 72)
    print(f"{label}  (font {QApplication.font().family()!r} "
          f"{QApplication.font().pointSize()}pt)")
    print("=" * 72)
    widths = {}
    for column in range(dlg.table.columnCount()):
      if dlg.table.isColumnHidden(column):
        continue
      set_to = dlg.table.columnWidth(column)
      needs = dlg.table.sizeHintForColumn(column)
      head = dlg.fontMetrics().horizontalAdvance(HEADS[column]) + 24
      widths[column] = (set_to, needs, head)
      slack = set_to - max(needs, head)
      print(f"  {column} {HEADS[column]:<22} set {set_to:>4}  "
            f"content {needs:>4}  header {head:>4}  slack {slack:>4}")
    total = sum(w for w, _n, _h in widths.values())
    floor = sum(max(n, h) for _w, n, h in widths.values())
    print(f"  {'':<24} set {total:>4}  needed {floor:>4}  "
          f"slack {total - floor:>4}")
    print(f"  minimumSizeHint {dlg.minimumSizeHint().width()}px, "
          f"sizeHint {dlg.sizeHint().width()}px, "
          f"table minimum {dlg.table.minimumSizeHint().width()}px")
    print(f"  window {dlg.width()}px (cap {MAX_WINDOW_WIDTH}), "
          f"preview {dlg.preview.width()}px (floor {PREVIEW_FLOOR}), "
          f"table scrolls {dlg.table.horizontalScrollBar().maximum()}px")
    return widths
  finally:
    dlg.close()


def main():
  """Report what each table column needs at two fonts.

  Returns:
    None; it prints. TWO fonts because the whole point is that they
    disagree: `QT_QPA_PLATFORM=offscreen` supplies Sans Serif 9pt to
    every runner and every CI job, a desktop supplies about 13pt, and
    a width measured at the first is a claim about the harness rather
    than about anybody's screen.
  """
  probe = start()
  report(probe, "AS EVERY RUNNER MEASURES IT")
  report(probe, "AT A DESKTOP FONT", point_size=13)


main()
