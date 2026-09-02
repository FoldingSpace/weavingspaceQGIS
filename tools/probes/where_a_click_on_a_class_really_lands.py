"""Whether an aimed click really reaches the class it names.

WHY IT EXISTS. `test_several_classes_can_be_moved_together` aims its
shift-click at "a vertex of the second class" by taking the FIRST such
vertex drawn inside the widget. That is not the same question as
"where would a click reach that class", because `mousePressEvent`
tests HANDLES FIRST -- they sit on whatever is already selected and
are the smaller target -- and then takes the NEAREST thing. On
2026-09-01 one Linux leg failed that test with the selection left
exactly where the plain click had put it, `('vertex', 'A')`, while
this Mac passed every time.

TWO ARMS IN ONE RUN, because a repair nobody has watched fail is not
proved:

  CONTROL   the ordinary drawing. Every candidate of the second class
            is reported with what the view's own hit test says about
            it, and the old aimer's pick is judged. Here it selects,
            which is why this machine passes.
  STAGED    the runner's condition, made rather than waited for: a
            handle is declared over the FIRST candidate, so the old
            aimer picks a point that selects nothing while the new one
            walks on to a candidate that does.

THE WINDOW IS NOT THE LEVER, which was measured before this shape was
settled: at 1025x450, 1200x700, 1400x900 and 1600x1000 the drawing is
420x462 every time, because the window's own minimum pins it. A sweep
over sizes therefore reports one verdict for every input, which is
this project's own tell for an instrument that is varying nothing.

RUN IT with the checkout on the path, offscreen, under QGIS's python:

    PYTHONUNBUFFERED=1 QT_QPA_PLATFORM=offscreen "$QGIS_PY" \\
      tools/probes/where_a_click_on_a_class_really_lands.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
for path in (ROOT, os.path.join(ROOT, "weavingspace_qgis", "vendor")):
    if path not in sys.path:
        sys.path.insert(0, path)

from qgis.core import QgsApplication, QgsProject                # noqa: E402
from qgis.PyQt.QtCore import QPoint                             # noqa: E402

DESIGN = "laves 3.3.4.3.4"
ELEMENTS = 4


def pump(seconds):
    """Turn the event loop while real time passes.

    Args:
      seconds: how long to wait, in wall-clock seconds.

    Returns:
      None. A `processEvents` loop alone lets NO wall time pass, so a
      QgsTask never finishes under one -- a trap this project has
      already paid for in a probe that concluded a design had no
      topology at all.
    """
    from qgis.PyQt.QtCore import QCoreApplication
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        QCoreApplication.processEvents()
        time.sleep(0.02)


def seats_of(view, label):
    """Every drawn point of one vertex class, in the view's own order.

    Args:
      view: the topology drawing widget.
      label: the vertex class label wanted.

    Returns:
      A list of QPoint inside the widget, in the order the topology
      yields them -- which is the order the old aimer walked, so its
      first entry IS what that aimer would have clicked.
    """
    topology = view._drawn()
    found = []
    if topology is None:
        return found
    for vertex in topology.points.values():
        if getattr(vertex, "label", None) != label:
            continue
        point = view._to_screen(vertex.point.x, vertex.point.y)
        if (0 <= point.x() <= view.width()
                and 0 <= point.y() <= view.height()):
            found.append(QPoint(int(round(point.x())),
                                int(round(point.y()))))
    return found


def would_select(view, at, label):
    """Would a click there choose that vertex class?

    Args:
      view: the drawing widget.
      at: the QPoint a click would land on.
      label: the vertex class wanted.

    Returns:
      True where the view's own press logic reaches that class: no
      handle under the pointer, and the nearest thing being the one
      wanted. Asked of the product rather than recomputed here.
    """
    if view._handle_at(at):
        return False
    target, found, _thing = view._nearest(at)
    return (target, found) == ("vertex", label)


def arm(rt, name, stage_a_handle):
    """Drive one arm and report what each aimer would have selected.

    Args:
      rt: the imported test module, for its fixtures and helpers.
      name: what to call this arm in the output.
      stage_a_handle: True to declare a handle over the first
        candidate, which is the runner's condition staged rather than
        waited for.

    Returns:
      None; the reading is printed. Each arm clears the project first,
      because two arms sharing one QgsProject is a contaminated
      control and reads exactly like machine contention.
    """
    from qgis.PyQt.QtCore import Qt as QtNamespace
    from qgis.PyQt.QtTest import QTest
    from weavingspace_qgis.dialog import WeavingSpaceDialog
    import weavingspace_qgis.topology_edits as topology_edits

    QgsProject.instance().clear()
    layer = rt.make_region_layer()
    QgsProject.instance().addMapLayer(layer)
    dlg = WeavingSpaceDialog(iface=rt._Iface())
    try:
        dlg.opt_experimental.setChecked(True)
        dlg.live_check.setChecked(False)
        dlg.show()
        pump(0.3)
        dlg.n_spin.setValue(ELEMENTS)
        pump(0.3)
        rt._choose_family(dlg, DESIGN)
        pump(0.4)
        if not rt._wait_for_the_topology(dlg):
            print(f"{name}: PREMISE no topology was built")
            return
        panel = dlg.topology_panel
        view = panel.view
        view.grab()
        pump(0.1)

        groups = topology_edits.classes(panel._topology)
        vertices = groups.get("vertex", "")
        if len(vertices) < 2:
            print(f"{name}: PREMISE {len(vertices)} vertex class(es)")
            return
        first, second = vertices[0], vertices[1]

        start = seats_of(view, first)
        if not start:
            print(f"{name}: PREMISE nothing of {first!r} is drawn")
            return
        QTest.mouseClick(view, QtNamespace.MouseButton.LeftButton,
                         QtNamespace.KeyboardModifier.NoModifier, start[0])
        pump(0.2)
        print(f"=== {name} ===")
        print(f"    drawing {view.width()}x{view.height()}, "
              f"classes {vertices}, after the plain click "
              f"{panel._selection}")

        candidates = seats_of(view, second)
        if not candidates:
            print(f"    PREMISE nothing of {second!r} is drawn")
            return

        if stage_a_handle:
            # THE CONDITION, MADE RATHER THAN WAITED FOR. The runner's
            # drawing put the first candidate somewhere a click cannot
            # reach it; which vertex that is true of is decided by the
            # layout and so by the fonts. Declaring a handle over that
            # point reproduces the same state here, deterministically.
            blocked = candidates[0]
            real_handle_at = view._handle_at

            def _handle_at(point, _real=real_handle_at, _at=blocked):
                near = ((point.x() - _at.x()) ** 2
                        + (point.y() - _at.y()) ** 2) ** 0.5
                return "nudge_vertex" if near <= 6.0 else _real(point)

            view._handle_at = _handle_at
            print(f"    STAGED: a handle now covers "
                  f"({blocked.x()},{blocked.y()})")

        old_pick = candidates[0]
        new_pick = next((c for c in candidates
                         if would_select(view, c, second)), None)
        print(f"    old aimer picks ({old_pick.x()},{old_pick.y()}), "
              f"which {'selects' if would_select(view, old_pick, second) else 'SELECTS NOTHING'}")
        print(f"    new aimer picks "
              f"{f'({new_pick.x()},{new_pick.y()})' if new_pick else 'NOTHING'}"
              f" of {len(candidates)} drawn")

        for which, at in (("old", old_pick), ("new", new_pick)):
            if at is None:
                print(f"    {which}: no point to click")
                continue
            panel._selection = ("vertex", first)
            panel._sync_selection_controls() if hasattr(
                panel, "_sync_selection_controls") else None
            QTest.mouseClick(view, QtNamespace.MouseButton.LeftButton,
                             QtNamespace.KeyboardModifier.NoModifier,
                             start[0])
            pump(0.15)
            QTest.mouseClick(view, QtNamespace.MouseButton.LeftButton,
                             QtNamespace.KeyboardModifier.ShiftModifier,
                             at)
            pump(0.15)
            held = panel._selection
            both = held[0] == "vertex" and set(held[1]) == {first, second}
            print(f"    {which} aimer -> selection {held} "
                  f"{'HOLDS BOTH' if both else 'DOES NOT HOLD BOTH'}")
    finally:
        dlg.close()
        pump(0.2)


def main():
    """Run the control and the staged arm, in that order.

    Returns:
      Exit status 0; the reading is the output.
    """
    app = QgsApplication([], False)          # bound, or it is collected
    app.initQgis()
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    import run_tests as rt                                      # noqa: E402

    arm(rt, "CONTROL: the ordinary drawing", stage_a_handle=False)
    arm(rt, "STAGED: the first candidate unreachable",
        stage_a_handle=True)
    QgsProject.instance().clear()
    pump(0.2)
    # SAY THAT THE READINGS ARE COMPLETE. Without exitQgis this probe
    # died of a segmentation fault at interpreter teardown, AFTER both
    # arms had printed -- which is indistinguishable from the thing
    # being measured crashing, and is the one shape an instrument must
    # not have.
    app.exitQgis()
    print("both arms reported; teardown complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
