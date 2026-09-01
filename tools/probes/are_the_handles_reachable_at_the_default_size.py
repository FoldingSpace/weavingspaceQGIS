"""Can every handle be hit, in the window a person actually gets?

The maintainer's requirement, 2026-08-31: "everything needs to be
clickable at realistic sizes of course... maybe that means making the
window a little larger by default". Nothing here had been measured --
the handles were sized and offset against a widget whose size was
chosen by a probe, which is not the size the dialog opens at.

THREE WAYS A HANDLE FAILS, and only the first is obvious:

  OFF THE WIDGET. A handle is drawn at an offset from the thing it
  belongs to, so a vertex near the edge of the view puts its rail
  handle outside the viewport, where nothing can click it.

  ON TOP OF ANOTHER. `_handle_at` returns the FIRST handle within
  `_HANDLE_REACH` and the order is fixed, so two handles closer than
  twice the reach make one of them unreachable ANYWHERE -- the earlier
  one in the list wins over the whole overlap. On an edge, `rotate` sits
  at the end and `zigzag` at the middle, both pushed out along the same
  normal, so their separation is HALF THE EDGE'S SCREEN LENGTH. A short
  edge hides its zigzag handle completely.

  TOO SMALL TO AIM AT. Reported here as the drawn seat against the
  reach, since a handle a person cannot see is one they will not try.

THE VIEW IS GRABBED BEFORE ANYTHING IS MEASURED, because `_fit` runs
inside `paintEvent`: a widget that has been resized and never painted
has `_bounds` at (0, 0, 1, 1) and `_scale` at 1.0, so every screen
figure it reports is raw unit coordinates wearing pixels' clothes.
That cost a whole round of readings on 2026-08-31.

AND THE WINDOW IS NEVER RESIZED. The point is the size the dialog
opens at with the Topology tab chosen, which is what a person meets.

    cd <checkout> && PYTHONUNBUFFERED=1 QT_QPA_PLATFORM=offscreen \\
      "$QGIS_PY" tools/probes/are_the_handles_reachable_at_the_default_size.py
"""

import importlib.util
import os

ROOT = os.getcwd()
spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

from qgis.core import QgsApplication, QgsProject          # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()
rt._no_modal_dialogs()

from weavingspace_qgis import topology_tab                # noqa: E402
from weavingspace_qgis.dialog import WeavingSpaceDialog   # noqa: E402

# Three designs with different vertex symmetries, so the rail handle is
# present on some and correctly absent on others.
DESIGNS = (("laves 3.3.4.3.4", 4), ("hex-slice", 6), ("archimedean 4.8.8", 8))


def separation(placed):
  """The closest two handles come to each other, in pixels.

  Args:
    placed: what `handles()` returned -- (key, QPointF, shape) triples.

  Returns:
    (distance, key, key) for the closest pair, or None where there are
    fewer than two handles to compare.
  """
  worst = None
  for i, (key_a, at_a, _shape_a) in enumerate(placed):
    for key_b, at_b, _shape_b in placed[i + 1:]:
      gap = ((at_a.x() - at_b.x()) ** 2 +
             (at_a.y() - at_b.y()) ** 2) ** 0.5
      if worst is None or gap < worst[0]:
        worst = (gap, key_a, key_b)
  return worst


def look(dlg, family, n):
  """Measure every handle of every class on one design.

  Args:
    dlg: the open dialog, already showing.
    family: the design family, as the chooser spells it.
    n: the element count.

  Returns:
    None. Prints one block per design.
  """
  dlg.n_spin.setValue(n)
  rt._tick(200)
  dlg.family_combo.setCurrentText(family)
  rt._tick(300)
  if not rt._wait_for_the_topology(dlg):
    print(f"  {family} {n}: no topology")
    return

  panel = dlg.topology_panel
  view = panel.view
  # THE GRAB IS THE MEASUREMENT'S PRECONDITION, not decoration.
  view.grab()
  topology = view._drawn()
  width, height = view.width(), view.height()

  off, ambiguous, worst_gap = 0, [], None
  counted = 0
  for kind, things in (("edge", list(topology.edges.values())),
                       ("vertex", list(topology.points.values()))):
    for thing in things:
      view._chosen = (kind, getattr(thing, "label", "") or "")
      view._chosen_thing = thing
      placed = view.handles()
      if not placed:
        continue
      # ONLY THINGS DRAWN INSIDE THE VIEW ARE SELECTABLE AT ALL.
      # `topology.edges` and `topology.points` span the whole PATCH of
      # repeats, and the view fits the UNIT -- so the surrounding ring
      # is off the widget by design, and counting it would report a
      # third of every design as unreachable. What matters is a handle
      # that escapes while the thing it belongs to is on screen.
      anchor = placed[0][1]
      if not (0 <= anchor.x() <= width and 0 <= anchor.y() <= height):
        continue
      counted += 1
      for key, at, _shape in placed:
        if not (0 <= at.x() <= width and 0 <= at.y() <= height):
          off += 1
      near = separation(placed)
      if near is None:
        continue
      if worst_gap is None or near[0] < worst_gap[0]:
        worst_gap = near
      # TWICE THE REACH is the threshold: below it the two circles
      # overlap and the earlier key wins the whole overlap.
      if near[0] < 2 * topology_tab._HANDLE_REACH:
        ambiguous.append((round(near[0], 1), near[1], near[2]))

  print(f"  {family} {n}: view {width}x{height}, "
        f"{counted} selectable things")
  print(f"    handles off the widget: {off}")
  if worst_gap is not None:
    print(f"    closest two handles:    {worst_gap[0]:.1f}px "
          f"({worst_gap[1]} / {worst_gap[2]}), "
          f"reach {topology_tab._HANDLE_REACH}")
  print(f"    ambiguous pairs:        {len(ambiguous)}"
        + (f"  e.g. {ambiguous[:3]}" if ambiguous else ""))


def report_layout(dlg):
  """Print what the window's width buys the two halves of the tab.

  Args:
    dlg: the open dialog.

  Returns:
    None.

  THE SIDE PANEL IS THE OTHER HALF OF THE BARGAIN. Room given to the
  drawing comes out of the panel beside it, and the maintainer's first
  report about this tab was that the Change controls sat below the
  fold -- so a repair that fixes the drawing by crushing the controls
  has moved the complaint rather than answered it.
  """
  page = dlg._tabs.currentWidget()
  print(f"  window {dlg.width()}x{dlg.height()}, "
        f"page sizeHint {page.sizeHint().width()}x{page.sizeHint().height()}")
  panel = dlg.topology_panel
  for child in panel.children():
    if child.__class__.__name__ == "QScrollArea":
      inner = child.widget()
      wants = inner.sizeHint().width()
      got = child.viewport().width()
      print(f"    side panel viewport {got}px for content wanting "
            f"{wants}px -- {'CRUSHED' if got < wants else 'fits'}")
      break


def main():
  """Open the dialog at its own size and measure what it offers."""
  QgsProject.instance().clear()
  QgsProject.instance().addMapLayer(rt.make_region_layer())

  dlg = WeavingSpaceDialog(iface=rt._Iface())
  try:
    dlg.opt_experimental.setChecked(True)
    dlg.live_check.setChecked(False)
    dlg.show()
    rt._tick(200)
    # Choosing the tab is what lets the window grow to it, which is
    # the whole subject: the size a person gets, not one we asked for.
    dlg._tabs.setCurrentIndex(dlg._topology_tab_index)
    rt._tick(300)
    asked = dlg._width_for_the_current_tab()
    # THE OFFSCREEN PLATFORM REPORTS AN 800px SCREEN, so
    # `_within_the_screen` clamps whatever the layout asks for and the
    # window never grows -- `_size_to_the_current_tab` only resizes
    # when the answer is WIDER than today. That is the harness, not the
    # product: this project already records that a font is not a
    # platform, and a virtual screen is not a desk either. So the
    # reading is taken TWICE, and the second one is the honest answer
    # about a person's display.
    print(f"  the layout asks for {asked}px; this platform's screen "
          f"clamps it to {dlg._within_the_screen(asked, 458)[0]}")
    for label in ("as the offscreen platform allows", "at the asked width"):
      if label.startswith("at the"):
        dlg.resize(asked, dlg.height())
        rt._tick(200)
      print(f"\n  --- {label} ---")
      report_layout(dlg)
      for family, n in DESIGNS:
        look(dlg, family, n)
  finally:
    dlg.close()
    dlg.deleteLater()
    rt._tick(100)


main()
