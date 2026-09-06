"""The general audit of the Topology tab (maintainer's ask, 2026-09-05).

Every control and every handle on the tab, driven on the packaged
Auckland data in the order a person meets them, with LIVE UPDATE AT
ITS DEFAULT (on), and every store read after each act. The probe
prints, per step, which stores moved and what they now say, and ends
with a list of anomalies -- each a sentence a person could act on --
so the verdict is a work list rather than a green tick.

THE STORES, read together at every step because this plugin's
characteristic defect is two of them disagreeing: the panel's
selection owner, the class combo, the tick list, the drawing's chosen
thing, the verb chooser, the argument boxes, the edit list and its
marks, the note and the working sentence, the symmetry line, the dual
button and its label, the two live-update boxes, the shelf, the
panel's drawn unit, the dialog's unit, and the MAP the element layers
hold.

Run:
    PYTHONPATH="$PWD:$PWD/tools" PYTHONUNBUFFERED=1 "$QGIS_PY" \\
      tools/probes/audit_the_topology_tab_as_a_person_meets_it.py
"""
import faulthandler
import hashlib
import os
import sys
import time

faulthandler.enable()

import probe_kit                                      # noqa: E402

sys.path.insert(0, probe_kit._repo_root())
probe = probe_kit.start()
suite = probe.suite

from qgis.core import QgsProject, QgsVectorLayer      # noqa: E402
from qgis.PyQt.QtCore import QPoint, Qt               # noqa: E402
from qgis.PyQt.QtTest import QTest                    # noqa: E402
from weavingspace_qgis import topology_edits          # noqa: E402
from weavingspace_qgis.dialog import WeavingSpaceDialog  # noqa: E402

AUCKLAND = os.path.join(probe_kit._repo_root(), "tests", "data",
                        "imd-auckland-sa2-2018.gpkg")
ANOMALIES = []
NOTES = []


def say(line):
  """Print one line at once, so a hung step is visible where it hung."""
  print(line, flush=True)


def anomaly(text):
  """Record a sentence a person could act on, and print it marked."""
  ANOMALIES.append(text)
  say(f"    !! {text}")


def note(text):
  """Record an observation that is not a fault, and print it marked."""
  NOTES.append(text)
  say(f"    -- {text}")


# ------------------------------------------------------------ readers

def ground(unit):
  """Area, perimeter and a digest of the tiles' WKB -- the perimeter
  and the digest move under every manipulation; the area is conserved
  by most and is here only as a sanity figure."""
  if unit is None or getattr(unit, "tiles", None) is None:
    return None
  tiles = unit.tiles
  digest = hashlib.sha256()
  for wkb in sorted(bytes(g.wkb) for g in tiles.geometry):
    digest.update(wkb)
  return (round(float(tiles.geometry.area.sum()), 1),
          round(float(tiles.geometry.length.sum()), 3),
          digest.hexdigest()[:10])


def map_digest(dlg):
  """The suite's own digest of the element layers, so the MAP is a store."""
  return suite._element_layer_digest(dlg)


def stores(dlg):
  """Read every store the Topology tab and the dialog hold, in one dict.

  Keyed by store name; the values are plain comparables so two
  readings can be diffed. Reads and never moves anything.
  """
  p = dlg.topology_panel
  v = p.view
  key = topology_edits.shelf_key(dlg._family_key(), dlg._element_count(),
                                 dlg._mapping_the_dual())
  ticks = [p.class_list.item(i).text() for i in range(p.class_list.count())
           if p.class_list.item(i).checkState() == Qt.CheckState.Checked]
  thing = getattr(v, "_chosen_thing", None)
  return {
    "selection": p._selection,
    "combo": p.class_combo.currentText(),
    "ticks": tuple(ticks),
    "view_chosen": tuple(getattr(v, "_chosen", ("", ""))),
    "chosen_thing": (type(thing).__name__ + ":" + str(getattr(thing, "label", ""))
                     if thing is not None else None),
    "how": p.how_combo.currentData(),
    "how_offered": tuple(p.how_combo.itemData(i)
                         for i in range(p.how_combo.count())),
    "args": tuple(sorted((k, round(float(v_), 4)) for k, v_ in p._arguments().items())),
    "edits": len(p._edits),
    "edit_rows": tuple(p.edit_list.item(i).text()
                       for i in range(p.edit_list.count())),
    "marks": tuple((m.get("applied"), m.get("sound")) for m in p._marks),
    "note": (p.note.text() or "").strip(),
    "working": (p.working.text() or "").strip(),
    "symmetry": (p.symmetry_note.text() or "").strip(),
    "dual_enabled": p.dual_button.isEnabled(),
    "dual_tip": p.dual_button.toolTip()[:70],
    "dual_label": p.dual_label.text(),
    "live": (dlg.live_check.isChecked(), p.live_here.isChecked()),
    "shelf": len((dlg._topology_shelf or {}).get(key) or []),
    "shelf_keys": tuple(sorted((dlg._topology_shelf or {}).keys())),
    "drawn": ground(getattr(p, "_unit", None)),
    "design": ground(getattr(dlg, "_unit", None)),
    "preview": getattr(v, "_preview", None) is not None,
    "map": map_digest(dlg),
    "group": dlg._group_name,
    "task": dlg._task is not None,
    "topology_task": dlg._topology_task is not None,
    "holds": p._topology is not None,
    "apply_enabled": p.apply_button.isEnabled(),
    "undo_enabled": p.undo_button.isEnabled(),
    "clear_enabled": p.clear_button.isEnabled(),
  }


def diff(before, after):
  """The stores that moved between two readings.

  Args:
    before: a reading from `stores`.
    after: a later reading; only keys present in `before` are compared.

  Returns:
    {name: (old, new)} for every store whose value differs.
  """
  return {k: (before[k], after[k]) for k in before if before[k] != after[k]}


def report(label, before, after, show=("selection", "combo", "ticks",
                                       "view_chosen", "how", "args",
                                       "edits", "note", "working",
                                       "drawn", "design", "map",
                                       "preview", "dual_enabled",
                                       "dual_label", "live", "shelf",
                                       "group", "marks", "edit_rows")):
  """Print which stores an act moved, and the old and new values of the
  ones worth reading.

  Args:
    label: the act, as printed.
    before: the reading taken before the act.
    after: the reading taken after it.
    show: the stores whose values are printed when they moved; the
      rest are named only.

  Returns:
    the `diff` of the two readings.
  """
  moved = diff(before, after)
  say(f"  [{label}] moved: {sorted(moved)}")
  for k in show:
    if k in moved:
      b, a = moved[k]
      say(f"      {k}: {b!r} -> {a!r}")
  return moved


def wait_until(check, seconds=40.0, every=0.2):
  """Pump the event loop until `check()` answers True or the ceiling passes.

  Args:
    check: a callable answering whether the awaited state has arrived.
    seconds: the hang-catcher, on the monotonic clock.
    every: seconds pumped between checks.

  Returns:
    True when the check answered, False at the ceiling.
  """
  began = time.monotonic()
  while time.monotonic() - began < seconds:
    suite._tick(int(every * 1000))
    if check():
      return True
  return False


def wait_for_stores(dlg, before, wanted, seconds=40.0):
  """Wait until every named store has moved from `before`.

  Args:
    dlg: the dialog.
    before: a reading from `stores`.
    wanted: the set of store names that must all have moved.
    seconds: the hang-catcher.
  """
  return wait_until(lambda: wanted <= set(diff(before, stores(dlg))), seconds)


def quiet(dlg, seconds=60):
  """Wait for the dialog, its topology build and the tab to be at rest.

  Args:
    dlg: the dialog.
    seconds: the hang-catcher for each settle.
  """
  suite._settle(dlg, seconds=seconds)
  suite._settle_topology(dlg, seconds=min(seconds, 30))
  suite._the_topology_tab_is_quiet(dlg, seconds=seconds)
  suite._settle(dlg, seconds=seconds)


# ------------------------------------------------------------- aiming

def aim_at(view, kind, every=False):
  """A widget point on the vertex or edge nearest the middle, clear of
  every handle and (for an edge) every vertex. Copied from the suite's
  own aimer rather than re-derived.

  Args:
    view: the TopologyView.
    kind: "vertex" or "edge".
    every: return every candidate point rather than the nearest one.
  """
  topology = view._drawn()
  if topology is None:
    return [] if every else None
  middle = (view.width() / 2, view.height() / 2)
  seated = [where for _key, where, _shape in (view.handles() or [])]

  def under_a_handle(point):
    return any(((where.x() - point.x()) ** 2
                + (where.y() - point.y()) ** 2) ** 0.5 < 13.0
               for where in seated)

  def consider(x, y):
    point = view._to_screen(x, y)
    if not (0 <= point.x() <= view.width() and 0 <= point.y() <= view.height()):
      return None
    if under_a_handle(point):
      return None
    away = ((point.x() - middle[0]) ** 2 + (point.y() - middle[1]) ** 2) ** 0.5
    return away, QPoint(int(round(point.x())), int(round(point.y())))

  if kind == "vertex":
    found = [(consider(v.point.x, v.point.y), v.label)
             for v in topology.points.values()]
    ordered = sorted((f for f in found if f[0]), key=lambda f: f[0][0])
    out = [(pt, label) for (_away, pt), label in ordered]
    return out if every else (out[0] if out else None)
  seats = [view._to_screen(v.point.x, v.point.y) for v in topology.points.values()]
  found_all = []
  for edge in topology.edges.values():
    try:
      coords = list(edge.get_geometry().coords)
    except Exception:                                   # noqa: BLE001
      continue
    for (ax, ay), (bx, by) in zip(coords, coords[1:]):
      for step in range(1, 10):
        fraction = step / 10.0
        found = consider(ax + (bx - ax) * fraction, ay + (by - ay) * fraction)
        if not found:
          continue
        clear = min(((found[1].x() - seat.x()) ** 2
                     + (found[1].y() - seat.y()) ** 2) ** 0.5
                    for seat in seats) if seats else 99.0
        if clear <= 12.0:
          continue
        found_all.append((found[0], found[1], edge.label))
  found_all.sort(key=lambda f: f[0])
  out = [(pt, label) for _a, pt, label in found_all]
  return out if every else (out[0] if out else None)


def click(view, at, modifier=Qt.KeyboardModifier.NoModifier):
  """Click the drawing at a widget point, the way QTest delivers one.

  Args:
    view: the TopologyView.
    at: the QPoint clicked.
    modifier: the keyboard modifier held, none by default.
  """
  QTest.mouseClick(view, Qt.MouseButton.LeftButton, modifier, at)
  suite._tick(150)


def drag(view, at, far, during=None):
  """Press at one point, move to another, release there.

  Args:
    view: the TopologyView.
    at: where the press lands.
    far: where the release lands.
    during: an optional callable run between the move and the release,
      whose answer is returned so a reading can be taken mid-gesture.

  Returns:
    whatever `during` returned, or None.
  """
  QTest.mousePress(view, Qt.MouseButton.LeftButton,
                   Qt.KeyboardModifier.NoModifier, at)
  suite._tick(30)
  QTest.mouseMove(view, far)
  suite._tick(60)
  seen = during() if during else None
  QTest.mouseRelease(view, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, far)
  suite._tick(50)
  return seen


def handle(view, key):
  """The widget point of the handle with this key, or None if not drawn.

  Args:
    view: the TopologyView.
    key: the handle's key as `view.handles()` names it.
  """
  for k, where, _shape in view.handles():
    if k == key:
      return QPoint(int(round(where.x())), int(round(where.y())))
  return None


def type_into(box, text):
  """Type a number into a spin box the way a person does.

  Args:
    box: the spin box.
    text: the characters typed before Return.
  """
  box.setFocus()
  box.lineEdit().selectAll()
  QTest.keyClicks(box, text)
  QTest.keyClick(box, Qt.Key.Key_Return)
  suite._tick(50)


def box_for(panel, name):
  """The argument spin box for a named argument, or None.

  Args:
    panel: the TopologyPanel.
    name: the argument the box carries in its `argument` property.
  """
  for _label, box in panel._argument_rows:
    if box.property("argument") == name:
      return box
  return None


# ------------------------------------------------------------- set-up

say("== SET-UP: Auckland, live update at its default, experimental on")
layer = QgsVectorLayer(AUCKLAND, "auckland", "ogr")
assert layer.isValid() and layer.featureCount() == 155
QgsProject.instance().addMapLayer(layer)
dlg = WeavingSpaceDialog(iface=suite._Iface())
dlg.show()
suite._tick(300)
say(f"  live update default: {dlg.live_check.isChecked()}")
assert dlg.live_check.isChecked(), "PREMISE: live update is not on by default"
dlg.layer_combo.setLayer(layer)
suite._tick(400)
dlg.spacing_spin.setValue(3000.0)
# THE FIRST MAP LANDS ON ITS OWN under live update.
ok = wait_until(lambda: bool(dlg._element_layer_ids) and dlg._task is None, 90)
say(f"  first map landed on its own: {ok}; group {dlg._group_name!r}; "
    f"family {dlg._family_key()!r} n={dlg._element_count()}")
if not ok:
  anomaly("with live update at its default the first map never landed")
quiet(dlg)
dlg.opt_experimental.setChecked(True)
suite._tick(200)
# Go to the tab, as a person would.
from qgis.PyQt.QtWidgets import QTabWidget               # noqa: E402
tab_widget = dlg.findChild(QTabWidget)
for i in range(tab_widget.count()):
  if tab_widget.widget(i) is dlg.topology_panel or \
      tab_widget.tabText(i).lower().startswith("topology"):
    tab_widget.setCurrentIndex(i)
    break
suite._tick(300)
say(f"  tab in front: {tab_widget.tabText(tab_widget.currentIndex())!r}; "
    f"enabled: {tab_widget.isTabEnabled(tab_widget.currentIndex())}")
try:
  suite._wait_for_the_topology(dlg, seconds=40.0, explain=True)
except AssertionError as exc:
  anomaly(f"the tab never answered after the box was ticked: {exc}")
quiet(dlg)
panel = dlg.topology_panel
view = panel.view
view.grab()
suite._tick(50)
say(f"  view size {view.width()}x{view.height()}; window {dlg.width()}x{dlg.height()}")
S = stores(dlg)
say(f"  baseline: holds={S['holds']} note={S['note']!r} working={S['working']!r} "
    f"symmetry={S['symmetry']!r}")
say(f"  baseline: selection={S['selection']} combo={S['combo']!r} ticks={S['ticks']} "
    f"how={S['how']} offered={S['how_offered']} args={S['args']}")
say(f"  baseline: dual_enabled={S['dual_enabled']} tip={S['dual_tip']!r} "
    f"label={S['dual_label']!r} live={S['live']} apply={S['apply_enabled']} "
    f"undo={S['undo_enabled']} clear={S['clear_enabled']}")
say(f"  baseline: drawn={S['drawn']} design={S['design']} map={S['map']}")
if not S["holds"]:
  anomaly(f"no topology on the default design; note={S['note']!r}")
if S["drawn"] != S["design"]:
  anomaly("the panel's drawn unit and the dialog's unit disagree before any edit")
if S["live"] != (True, True):
  anomaly(f"the two live-update boxes disagree at the start: {S['live']}")
if S["selection"] == ("", ""):
  anomaly("nothing is selected after the first landing, so the handles have nowhere to sit")
BASE_MAP = S["map"]
BASE_DESIGN = S["design"]

# ---------------------------------------------- 1. clicking things

say("== 1. CLICK A VERTEX, CLICK AN EDGE, SHIFT-CLICK, THE LIST, THE COMBO")
groups = topology_edits.classes(panel._topology)
say(f"  classes: {groups}")
for kind in ("vertex", "edge"):
  candidates = aim_at(view, kind, every=True)
  if not candidates:
    anomaly(f"no {kind} is drawn inside the widget to click")
    continue
  moved_any = False
  for at, label in candidates:
    before = stores(dlg)
    if before["selection"] == (kind, label):
      continue
    click(view, at)
    after = stores(dlg)
    moved = report(f"click {kind} {label} at {at.x()},{at.y()}", before, after)
    if after["selection"] != (kind, label):
      anomaly(f"clicking {kind} {label} left the selection at {after['selection']}")
    if after["view_chosen"] != (kind, label):
      anomaly(f"clicking {kind} {label}: the drawing holds {after['view_chosen']}")
    if after["combo"] != f"{kind} {label}":
      anomaly(f"clicking {kind} {label}: the combo reads {after['combo']!r}")
    if after["ticks"] != (f"{kind} {label}",):
      anomaly(f"clicking {kind} {label}: the tick list reads {after['ticks']}")
    wanted_target = kind
    offered = [topology_edits.MANIPULATIONS[k]["target"] for k in after["how_offered"]]
    if any(t != wanted_target for t in offered):
      anomaly(f"after clicking a {kind} the verb chooser offers {after['how_offered']}")
    if after["edits"] != before["edits"] or after["preview"]:
      anomaly(f"a plain click on a {kind} recorded an edit or left a preview")
    moved_any = True
    break
  if not moved_any:
    note(f"every drawn {kind} was already the selection, nothing to move")

# Shift-click a second edge class, if the design has one.
edge_labels = groups.get("edge", "")
if len(edge_labels) >= 2:
  held = panel._selection[1] if panel._selection[0] == "edge" else ""
  other = next((l for l in edge_labels if l not in held), None)
  if panel._selection[0] != "edge":
    for at, label in aim_at(view, "edge", every=True):
      click(view, at)
      if panel._selection[0] == "edge":
        break
  held = panel._selection[1]
  other = next((l for l in edge_labels if l not in held), None)
  spot = next(((at, l) for at, l in aim_at(view, "edge", every=True) if l == other), None)
  if spot is None:
    note(f"no drawn edge of class {other!r} is clear of handles to shift-click")
  else:
    before = stores(dlg)
    click(view, spot[0], Qt.KeyboardModifier.ShiftModifier)
    after = stores(dlg)
    report(f"shift-click edge {other}", before, after)
    want = "".join(sorted(set(held) | {other}))
    if after["selection"] != ("edge", want):
      anomaly(f"shift-click gave selection {after['selection']}, wanted ('edge', {want!r})")
    if set(after["ticks"]) != {f"edge {l}" for l in want}:
      anomaly(f"shift-click: ticks {after['ticks']} do not match {want!r}")
    say(f"      combo now reads {after['combo']!r}")
    # Shift-click the same again removes it.
    before = stores(dlg)
    click(view, spot[0], Qt.KeyboardModifier.ShiftModifier)
    after = stores(dlg)
    report(f"shift-click edge {other} again (remove)", before, after)
    if after["selection"] != ("edge", held):
      anomaly(f"a second shift-click did not remove {other}: {after['selection']}")
    # The tick list: tick the other, then try to untick the last.
    for i in range(panel.class_list.count()):
      item = panel.class_list.item(i)
      if item.text() == f"edge {other}":
        before = stores(dlg)
        item.setCheckState(Qt.CheckState.Checked)
        suite._tick(100)
        after = stores(dlg)
        report(f"tick 'edge {other}' in the list", before, after)
        if after["selection"] != ("edge", want):
          anomaly(f"ticking a row gave {after['selection']}, wanted ('edge', {want!r})")
        # untick both, the last must be refused
        for j in range(panel.class_list.count()):
          it = panel.class_list.item(j)
          if it.checkState() == Qt.CheckState.Checked:
            before = stores(dlg)
            it.setCheckState(Qt.CheckState.Unchecked)
            suite._tick(100)
            after = stores(dlg)
            report(f"untick {it.text()!r}", before, after)
        if not panel._selection[1]:
          anomaly("unticking every row left a selection of nothing")
        elif len(panel._selection[1]) != 1:
          anomaly(f"unticking rows left {panel._selection}")
        else:
          say(f"      the last tick was put back: {panel._selection}")
        break
else:
  note(f"the default design has {len(edge_labels)} edge class(es); no multi-select to drive")

# The combo: pick every entry and see the others follow.
say("  -- the class combo, every entry")
for i in range(panel.class_combo.count()):
  data = panel.class_combo.itemData(i)
  before = stores(dlg)
  panel.class_combo.setCurrentIndex(i)
  suite._tick(100)
  after = stores(dlg)
  say(f"    combo -> {panel.class_combo.itemText(i)!r}: selection={after['selection']} "
      f"view={after['view_chosen']} ticks={after['ticks']} how={after['how']} "
      f"offered={after['how_offered']}")
  if tuple(after["selection"]) != tuple(data):
    anomaly(f"combo row {panel.class_combo.itemText(i)!r} gave selection {after['selection']}")
  if after["view_chosen"] != tuple(data):
    anomaly(f"combo row {panel.class_combo.itemText(i)!r}: drawing holds {after['view_chosen']}")
  if set(after["ticks"]) != {f"{data[0]} {l}" for l in data[1]}:
    anomaly(f"combo row {panel.class_combo.itemText(i)!r}: ticks {after['ticks']}")
  if after["edits"] != before["edits"] or after["preview"]:
    anomaly("picking a combo row recorded an edit or left a preview")

# ------------------------------------------- 2. the verb chooser

say("== 2. THE VERB CHOOSER AND ITS BOXES: memory per verb, typing")
# Start on an edge.
for at, label in aim_at(view, "edge", every=True):
  click(view, at)
  if panel._selection[0] == "edge":
    break
assert panel._selection[0] == "edge", "PREMISE: could not select an edge"
for key in ("rotate_edge", "scale_edge", "zigzag_edge"):
  idx = panel.how_combo.findData(key)
  if idx < 0:
    anomaly(f"{key} is not offered on an edge")
    continue
  before = stores(dlg)
  panel.how_combo.setCurrentIndex(idx)
  suite._tick(100)
  after = stores(dlg)
  wanted_args = tuple(a[0] for a in topology_edits.MANIPULATIONS[key]["args"])
  have = tuple(k for k, _ in after["args"])
  say(f"    {key}: boxes {after['args']}; handles {[k for k, _w, _s in view.handles()]}")
  if set(have) != set(wanted_args):
    anomaly(f"{key} shows boxes {have}, wanted {wanted_args}")
  if after["edits"] != before["edits"]:
    anomaly(f"choosing {key} recorded an edit")
# Type into zigzag's boxes, switch away and back.
idx = panel.how_combo.findData("zigzag_edge")
panel.how_combo.setCurrentIndex(idx)
suite._tick(100)
n_box, h_box = box_for(panel, "n"), box_for(panel, "h")
type_into(n_box, "3")
type_into(h_box, "0.3")
say(f"    typed n=3 h=0.3; boxes read n={n_box.value()} h={h_box.value()}; "
    f"readout={view._zigzag_readout}")
if n_box.value() != 3.0 or abs(h_box.value() - 0.3) > 1e-6:
  anomaly(f"typing into the zigzag boxes gave n={n_box.value()} h={h_box.value()}")
if view._zigzag_readout[:2] != (3.0, 0.3):
  anomaly(f"the zigzag readout did not follow the boxes: {view._zigzag_readout}")
panel.how_combo.setCurrentIndex(panel.how_combo.findData("rotate_edge"))
suite._tick(100)
type_into(box_for(panel, "angle"), "20")
panel.how_combo.setCurrentIndex(panel.how_combo.findData("zigzag_edge"))
suite._tick(100)
n_box, h_box = box_for(panel, "n"), box_for(panel, "h")
say(f"    back on zigzag: n={n_box.value()} h={h_box.value()}")
if (n_box.value(), round(h_box.value(), 6)) != (3.0, 0.3):
  anomaly(f"the zigzag boxes forgot their numbers across a verb change: "
          f"n={n_box.value()} h={h_box.value()}")
panel.how_combo.setCurrentIndex(panel.how_combo.findData("rotate_edge"))
suite._tick(100)
if box_for(panel, "angle").value() != 20.0:
  anomaly(f"rotate forgot its angle across a verb change: {box_for(panel, 'angle').value()}")
# A landing must not eat them: force a rebuild by nudging the spacing.
before_args = (n_box.value(), h_box.value())
panel.how_combo.setCurrentIndex(panel.how_combo.findData("zigzag_edge"))
suite._tick(100)
dlg.spacing_spin.setValue(2900.0)
quiet(dlg, seconds=90)
try:
  suite._wait_for_the_topology(dlg, seconds=40.0)
except AssertionError as exc:
  anomaly(f"after a spacing change the tab never answered: {exc}")
n_box, h_box = box_for(panel, "n"), box_for(panel, "h")
say(f"    after a landing (spacing 2900): n={n_box.value()} h={h_box.value()} "
    f"selection={panel._selection} how={panel.how_combo.currentData()}")
if (n_box.value(), round(h_box.value(), 6)) != (3.0, 0.3):
  anomaly(f"a landing reset the zigzag boxes to n={n_box.value()} h={h_box.value()}")
if panel._selection[0] != "edge":
  anomaly(f"a landing moved the selection off the edge: {panel._selection}")
if panel.how_combo.currentData() != "zigzag_edge":
  anomaly(f"a landing moved the verb: {panel.how_combo.currentData()}")

# --------------------------------------------- 3. every handle

say("== 3. EVERY HANDLE, DRAGGED, WITH LIVE UPDATE ON")
BASE_MAP = map_digest(dlg)
BASE_DESIGN = ground(dlg._unit)
S = stores(dlg)
if S["drawn"] != S["design"]:
  anomaly("before any drag the drawn unit and the dialog's unit disagree")


def drag_a_handle(key, far_of, label):
  """Drag one handle and read every store during and after.

  Args:
    key: the handle's key as `view.handles()` names it.
    far_of: a callable giving the release point from the grab point.
    label: the act, as printed.
  """
  at = handle(view, key)
  if at is None:
    return None
  far = far_of(at)
  before = stores(dlg)
  during = drag(view, at, far, during=lambda: stores(dlg))
  d_moved = diff(before, during)
  say(f"  [{label}] during: moved {sorted(d_moved)}; preview={during['preview']} "
      f"args={during['args']} how={during['how']}")
  if not during["preview"]:
    anomaly(f"{label}: nothing was previewed while the pointer moved")
  if during["how"] != key:
    anomaly(f"{label}: grabbing the handle did not choose {key}: {during['how']}")
  # one pump after the drop: the picture must still be the edited one
  suite._tick(30)
  just = stores(dlg)
  if just["edits"] != before["edits"] + 1:
    anomaly(f"{label}: the drop recorded {just['edits'] - before['edits']} edit(s)")
    return before, just
  if not just["preview"]:
    anomaly(f"{label}: the preview was cleared at the drop (snap-back)")
  landed = wait_for_stores(dlg, before, {"design", "drawn", "map"}, seconds=90)
  quiet(dlg, seconds=90)
  after = stores(dlg)
  moved = report(label, before, after)
  if not landed:
    anomaly(f"{label}: after 90s not all of design/drawn/map moved; moved={sorted(moved)}")
  if after["drawn"] != after["design"]:
    anomaly(f"{label}: drawn {after['drawn']} != design {after['design']} after landing")
  if after["preview"]:
    anomaly(f"{label}: the preview is still up after the landing")
  if after["working"]:
    anomaly(f"{label}: the working sentence is still up: {after['working']!r}")
  if after["shelf"] != after["edits"]:
    anomaly(f"{label}: shelf holds {after['shelf']} edits, panel {after['edits']}")
  if len(after["marks"]) != after["edits"]:
    anomaly(f"{label}: {len(after['marks'])} marks for {after['edits']} edits")
  elif not after["marks"][-1][0]:
    anomaly(f"{label}: the edit was recorded but marked not applied; note={after['note']!r}")
  if after["selection"] != before["selection"]:
    anomaly(f"{label}: the landing moved the selection {before['selection']} -> {after['selection']}")
  if after["how"] != key:
    anomaly(f"{label}: the landing moved the verb to {after['how']}")
  say(f"      edit row: {after['edit_rows'][-1] if after['edit_rows'] else None}; "
      f"mark={after['marks'][-1] if after['marks'] else None}; note={after['note']!r}")
  return before, after


# Edge handles first: select an edge.
for at, label in aim_at(view, "edge", every=True):
  click(view, at)
  if panel._selection[0] == "edge":
    break
say(f"  edge selected: {panel._selection}; handles: {[(k, round(w.x()), round(w.y())) for k, w, _ in view.handles()]}")
drag_a_handle("scale_edge", lambda at: QPoint(at.x() + 14, at.y() - 10), "drag STRETCH (scale_edge)")
drag_a_handle("rotate_edge", lambda at: QPoint(at.x() + 12, at.y() + 12), "drag TURN (rotate_edge)")
r = drag_a_handle("zigzag_edge", lambda at: QPoint(at.x() + 9, at.y() - 13), "drag ZIGZAG across (h)")
if r:
  say(f"      zigzag args after across-drag: {r[1]['args']}")
# The count by dragging ALONG the edge: take the frame from the view.
frame = view._edge_frame(view._chosen_thing) if view._chosen_thing is not None else None
if frame is not None:
  at = handle(view, "zigzag_edge")
  if at is not None:
    try:
      coords = list(view._chosen_thing.get_geometry().coords)
      start, finish = view._to_screen(*coords[0]), view._to_screen(*coords[-1])
      run, rise = finish.x() - start.x(), finish.y() - start.y()
      reach = (run * run + rise * rise) ** 0.5 or 1.0
      # toward the START raises the count and toward the far end lowers
      # it; go the way the count can still move. (The first run of this
      # arm dragged toward the start from a count already at the
      # ceiling and flagged the product for its own instrument.)
      n_before = box_for(panel, "n").value() if box_for(panel, "n") else None
      sign = 1.0 if (n_before or 0) >= 8 else -1.0
      dx, dy = sign * run / 3.0, sign * rise / 3.0
      r2 = drag_a_handle("zigzag_edge",
                         lambda a: QPoint(int(round(a.x() + dx)), int(round(a.y() + dy))),
                         "drag ZIGZAG along (count)")
      if r2:
        n_after = dict(r2[1]["args"]).get("n")
        say(f"      count before {n_before} -> after {n_after}; edge {reach:.0f}px on screen")
        if n_after == n_before:
          anomaly("dragging the zigzag handle a third of the edge along it did not change the count")
    except Exception as exc:                            # noqa: BLE001
      anomaly(f"could not drive the count drag: {exc!r}")
# Vertex handles.
for at, label in aim_at(view, "vertex", every=True):
  click(view, at)
  if panel._selection[0] == "vertex":
    break
say(f"  vertex selected: {panel._selection}; handles: {[(k, round(w.x()), round(w.y())) for k, w, _ in view.handles()]}")
drag_a_handle("nudge_vertex", lambda at: QPoint(at.x() + 10, at.y() - 8), "drag NUDGE (nudge_vertex)")
if handle(view, "push_vertex") is None:
  free = [topology_edits.directions_a_class_may_move(panel._topology, "vertex", l)
          for l in panel._selection[1]]
  note(f"no push rail on vertex {panel._selection[1]!r} (free directions {free}); "
       f"push_vertex greyed: "
       f"{[ (panel.how_combo.itemText(i), panel.how_combo.model().item(i).isEnabled()) for i in range(panel.how_combo.count())]}")
  # try every other vertex class for a rail
  for lbl in groups.get("vertex", ""):
    if lbl == panel._selection[1]:
      continue
    spot = next(((a, l) for a, l in aim_at(view, "vertex", every=True) if l == lbl), None)
    if spot:
      click(view, spot[0])
      if handle(view, "push_vertex") is not None:
        break
if handle(view, "push_vertex") is not None:
  way = view.push_direction()
  drag_a_handle("push_vertex",
                lambda at: QPoint(int(round(at.x() + way[0] * 14)), int(round(at.y() + way[1] * 14))),
                "drag PUSH along the rail (push_vertex)")
else:
  note("push_vertex has no rail on any vertex class of this design (symmetry holds them)")

# ------------------------------------------ 4. Apply, Undo, Clear

say("== 4. APPLY WITH TYPED NUMBERS, UNDO, CLEAR")
for at, label in aim_at(view, "edge", every=True):
  click(view, at)
  if panel._selection[0] == "edge":
    break
panel.how_combo.setCurrentIndex(panel.how_combo.findData("zigzag_edge"))
suite._tick(100)
type_into(box_for(panel, "n"), "4")
type_into(box_for(panel, "h"), "0.2")
before = stores(dlg)
panel.apply_button.click()
suite._tick(30)
landed = wait_for_stores(dlg, before, {"design", "drawn", "map", "edits"}, seconds=90)
quiet(dlg, seconds=90)
after = stores(dlg)
report("Apply zigzag n=4 h=0.2", before, after)
if not landed:
  anomaly("Apply: design/drawn/map/edits did not all move within 90s")
last = panel._edits[-1] if panel._edits else None
say(f"      recorded: {last}")
if not last or last.get("how") != "zigzag_edge" or \
    round(float(last["args"].get("n", 0))) != 4 or abs(float(last["args"].get("h", 0)) - 0.2) > 1e-6:
  anomaly(f"Apply recorded {last}, not zigzag n=4 h=0.2")
if last and "against" not in last:
  anomaly("the recorded edit carries no 'against' alphabet")
n_edits = after["edits"]
before = stores(dlg)
panel.undo_button.click()
landed = wait_for_stores(dlg, before, {"design", "drawn", "map", "edits"}, seconds=90)
quiet(dlg, seconds=90)
after = stores(dlg)
report("Undo", before, after)
if after["edits"] != n_edits - 1:
  anomaly(f"Undo left {after['edits']} edits, expected {n_edits - 1}")
if not landed:
  anomaly("Undo: design/drawn/map/edits did not all move")
before = stores(dlg)
panel.clear_button.click()
landed = wait_for_stores(dlg, before, {"design", "drawn", "map", "edits"}, seconds=90)
quiet(dlg, seconds=90)
after = stores(dlg)
report("Clear", before, after)
if after["edits"] != 0:
  anomaly(f"Clear left {after['edits']} edits")
if after["undo_enabled"] or after["clear_enabled"]:
  anomaly("Undo/Clear still enabled with an empty list")
say(f"      map after Clear == map before any edit: {after['map'] == BASE_MAP}; "
    f"design == : {after['design'] == BASE_DESIGN}")
if after["design"] != BASE_DESIGN:
  anomaly(f"after Clear the unit is not the plain one: {after['design']} vs {BASE_DESIGN}")
if after["map"] != BASE_MAP:
  anomaly("after Clear the map digest is not the pre-edit one (the map did not return)")

# ------------------------------------------------ 5. the toggles

say("== 5. THE SHOW TOGGLES")
for key, box in panel.toggles.items():
  was = box.isChecked()
  box.setChecked(not was)
  suite._tick(60)
  view.grab()
  shown = getattr(view, "_shown", {}).get(key)
  say(f"    {key}: {was} -> {box.isChecked()}; view shows {shown}")
  if shown != (not was):
    anomaly(f"toggle {key}: the view's _shown reads {shown} after the box went to {not was}")
  box.setChecked(was)
  suite._tick(60)
  if getattr(view, "_shown", {}).get(key) != was:
    anomaly(f"toggle {key} did not restore")
S = stores(dlg)
if S["edits"] != 0:
  anomaly("toggling the show boxes recorded an edit")

# ------------------------------------------ 6. live update, two views

say("== 6. LIVE UPDATE, SEEN FROM TWO TABS")
for who, box in (("tab", panel.live_here), ("dialog", dlg.live_check)):
  box.setChecked(False)
  suite._tick(60)
  say(f"    {who} box off -> live={(dlg.live_check.isChecked(), panel.live_here.isChecked())}")
  if dlg.live_check.isChecked() or panel.live_here.isChecked():
    anomaly(f"unticking the {who}'s box left {(dlg.live_check.isChecked(), panel.live_here.isChecked())}")
  box.setChecked(True)
  suite._tick(60)
  if not (dlg.live_check.isChecked() and panel.live_here.isChecked()):
    anomaly(f"re-ticking the {who}'s box left {(dlg.live_check.isChecked(), panel.live_here.isChecked())}")
# With live OFF, an Apply must move the drawing and NOT the map.
panel.live_here.setChecked(False)
suite._tick(60)
for at, label in aim_at(view, "edge", every=True):
  click(view, at)
  if panel._selection[0] == "edge":
    break
panel.how_combo.setCurrentIndex(panel.how_combo.findData("rotate_edge"))
suite._tick(100)
type_into(box_for(panel, "angle"), "15")
before = stores(dlg)
panel.apply_button.click()
wait_for_stores(dlg, before, {"design", "drawn", "edits"}, seconds=90)
quiet(dlg, seconds=90)
after = stores(dlg)
report("Apply rotate 15 with live OFF", before, after)
if after["map"] != before["map"]:
  anomaly("with live update off, Apply re-tiled the map (preserve, do not repaint)")
if not ({"design", "drawn", "edits"} <= set(diff(before, after))):
  anomaly("with live update off, Apply did not move design+drawn+edits")
say(f"      said: {probe.said(dlg)[-200:]!r}")
# Then Generate draws it.
before = stores(dlg)
dlg._generate()
suite._settle(dlg, seconds=90)
quiet(dlg, seconds=90)
after = stores(dlg)
report("Generate after the live-off edit", before, after)
if after["map"] == before["map"]:
  anomaly("Generate after an edit made with live off did not move the map")
panel.live_here.setChecked(True)
suite._tick(60)
before = stores(dlg)
panel.clear_button.click()
wait_for_stores(dlg, before, {"design", "drawn", "map", "edits"}, seconds=90)
quiet(dlg, seconds=90)
after = stores(dlg)
report("Clear (live back on)", before, after)
if after["map"] != BASE_MAP:
  anomaly("after Clear with live on the map is not the pre-edit one")

# --------------------------------------------------- 7. the dual

say("== 7. THE DUAL BUTTON AND ITS LABEL")
S = stores(dlg)
say(f"    enabled={S['dual_enabled']} tip={S['dual_tip']!r} label={S['dual_label']!r} group={S['group']!r}")
source_group = dlg._group_name
source_ids = dict(dlg._element_layer_ids)
if not S["dual_enabled"]:
  anomaly(f"the dual button is disabled on the default design: {S['dual_tip']!r}")
else:
  before = stores(dlg)
  panel.dual_button.click()
  ok = wait_until(lambda: dlg._task is None and dlg._group_name != source_group, 120)
  quiet(dlg, seconds=120)
  try:
    suite._wait_for_the_topology(dlg, seconds=40.0)
  except AssertionError as exc:
    anomaly(f"after the dual button the tab never answered: {exc}")
  quiet(dlg, seconds=60)
  after = stores(dlg)
  report("Generate the dual and tile it", before, after)
  root = QgsProject.instance().layerTreeRoot()
  groups_now = [g.name() for g in root.findGroups()]
  say(f"      groups: {groups_now}; dialog on {dlg._group_name!r}; mapping the dual: {dlg._mapping_the_dual()}")
  say(f"      dual elements: {sorted(dlg._element_layer_ids)}; source layers still present: "
      f"{all(QgsProject.instance().mapLayer(l) is not None for l in source_ids.values())}")
  say(f"      tab now: holds={after['holds']} note={after['note']!r} classes={topology_edits.classes(panel._topology) if panel._topology else None} "
      f"symmetry={after['symmetry']!r} dual_enabled={after['dual_enabled']} tip={after['dual_tip']!r}")
  if dlg._group_name != f"{source_group} — dual":
    anomaly(f"the dual landed in {dlg._group_name!r}, not {source_group + ' — dual'!r}")
  if after["dual_label"] != "Tiled with the dual of this design.":
    anomaly(f"the dual label reads {after['dual_label']!r}")
  if not after["holds"]:
    anomaly(f"the tab holds no topology of the dual: {after['note']!r}")
  if after["edits"] != 0 or after["shelf"] != 0:
    anomaly(f"the dual group inherited edits: panel {after['edits']} shelf {after['shelf']}")
  # An edit on the dual, then back to the source: the shelves must be separate.
  for at, label in aim_at(view, "edge", every=True):
    click(view, at)
    if panel._selection[0] == "edge":
      break
  if panel._selection[0] == "edge":
    panel.how_combo.setCurrentIndex(panel.how_combo.findData("scale_edge"))
    suite._tick(100)
    type_into(box_for(panel, "sf"), "1.2")
    before = stores(dlg)
    panel.apply_button.click()
    wait_for_stores(dlg, before, {"design", "drawn", "map", "edits"}, seconds=90)
    quiet(dlg, seconds=90)
    after = stores(dlg)
    report("Apply scale 1.2 on the DUAL", before, after)
    say(f"      shelf keys: {after['shelf_keys']}")
  else:
    note("could not select an edge on the dual to edit it")
  # Back to the source group through the chooser.
  def choose_group(name):
    for i in range(dlg.group_combo.count()):
      h = dlg.group_combo.itemData(i)
      g = dlg._group_for_handle(h) if h is not None else None
      if g is not None and g.name() == name:
        dlg.group_combo.setCurrentIndex(i)
        dlg.group_combo.activated.emit(i)
        suite._tick(500)
        return True
    return False
  before = stores(dlg)
  assert choose_group(source_group), "PREMISE: the source group is not in the chooser"
  quiet(dlg, seconds=90)
  try:
    suite._wait_for_the_topology(dlg, seconds=40.0)
  except AssertionError as exc:
    anomaly(f"after choosing the source group the tab never answered: {exc}")
  quiet(dlg, seconds=60)
  after = stores(dlg)
  report("choose the SOURCE group", before, after)
  say(f"      mapping the dual: {dlg._mapping_the_dual()}; label {after['dual_label']!r}; "
      f"edits {after['edits']} shelf {after['shelf']}; design {after['design']} == base {after['design'] == BASE_DESIGN}")
  if dlg._mapping_the_dual():
    anomaly("back on the source group the store still says the dual is mapped")
  if after["dual_label"]:
    anomaly(f"back on the source the label still reads {after['dual_label']!r}")
  if after["edits"] != 0:
    anomaly(f"the source group shows the dual's edits: {after['edit_rows']}")
  if after["design"] != BASE_DESIGN:
    anomaly("back on the source the unit is not the plain design")
  before = stores(dlg)
  assert choose_group(f"{source_group} — dual")
  quiet(dlg, seconds=90)
  try:
    suite._wait_for_the_topology(dlg, seconds=40.0)
  except AssertionError as exc:
    anomaly(f"after choosing the dual group the tab never answered: {exc}")
  quiet(dlg, seconds=60)
  after = stores(dlg)
  report("choose the DUAL group again", before, after)
  say(f"      mapping the dual: {dlg._mapping_the_dual()}; label {after['dual_label']!r}; "
      f"edits {after['edits']} shelf {after['shelf']} rows {after['edit_rows']}")
  if not dlg._mapping_the_dual():
    anomaly("back on the dual group the store does not say the dual is mapped")
  if after["edits"] != 1:
    anomaly(f"the dual group's edit did not come back: {after['edits']}")
  # And Generate on the dual group re-tiles the dual (ruling 4).
  before = stores(dlg)
  dlg._generate()
  suite._settle(dlg, seconds=90)
  quiet(dlg, seconds=90)
  after = stores(dlg)
  say(f"      Generate on the dual group: group {dlg._group_name!r}, still the dual: {dlg._mapping_the_dual()}, "
      f"map moved: {after['map'] != before['map']}, elements {sorted(dlg._element_layer_ids)}")
  if dlg._group_name != f"{source_group} — dual" or not dlg._mapping_the_dual():
    anomaly("Generate on the dual group did not stay a dual in its own group")
  # Clear its edit, return to the source.
  panel.clear_button.click()
  quiet(dlg, seconds=90)
  choose_group(source_group)
  quiet(dlg, seconds=90)
  try:
    suite._wait_for_the_topology(dlg, seconds=40.0)
  except AssertionError as exc:
    anomaly(f"back on the source (again) the tab never answered: {exc}")

# ------------------------------------------------- 8. save and load

say("== 8. SAVE WITH AN EDIT, THEN LOAD IT BACK IN A FRESH DIALOG")
for at, label in aim_at(view, "edge", every=True):
  click(view, at)
  if panel._selection[0] == "edge":
    break
panel.how_combo.setCurrentIndex(panel.how_combo.findData("zigzag_edge"))
suite._tick(100)
type_into(box_for(panel, "n"), "3")
type_into(box_for(panel, "h"), "0.25")
before = stores(dlg)
panel.apply_button.click()
wait_for_stores(dlg, before, {"design", "drawn", "map", "edits"}, seconds=90)
quiet(dlg, seconds=90)
edited_design = ground(dlg._unit)
edited_map = map_digest(dlg)
path = probe.path("audit.gpkg")
wrote = probe.save(dlg, path)
quiet(dlg, seconds=120)
tables = probe.tables(path)
say(f"    saved: {wrote}; tables: {tables}")
if not wrote:
  anomaly(f"the save did not write; said {probe.said(dlg)[-200:]!r}")
if "weavingspace_unit_no_crs" not in tables or "weavingspace_dual_no_crs" not in tables:
  anomaly(f"the file lacks the unit/dual tables: {tables}")
try:
  from weavingspace_qgis import bridge
  record = bridge.read_working_state(path)
  design_rec = (record or {}).get("design", {})
  say(f"    record topology_edits: {design_rec.get('topology_edits')}; "
      f"topology_written: {record.get('topology_written')}; map_dual: {design_rec.get('map_dual')}")
  if not design_rec.get("topology_edits"):
    anomaly("the file's record carries no topology_edits")
except Exception as exc:                                # noqa: BLE001
  anomaly(f"could not read the file's record: {exc!r}")
# A fresh dialog, Load.
dlg.close()
dlg.deleteLater()
suite._tick(200)
probe.clear()
layer = QgsVectorLayer(AUCKLAND, "auckland", "ogr")
QgsProject.instance().addMapLayer(layer)
dlg2 = WeavingSpaceDialog(iface=suite._Iface())
dlg2.show()
suite._tick(300)
dlg2.layer_combo.setLayer(layer)
suite._tick(400)
wait_until(lambda: dlg2._task is None and bool(dlg2._element_layer_ids), 90)
quiet(dlg2, seconds=90)
say(f"    fresh dialog: live={dlg2.live_check.isChecked()} experimental={dlg2.opt_experimental.isChecked()}")
dlg2.resume_widget.setFilePath(path)
loaded = False
for name in ("load_button", "resume_button"):
  btn = getattr(dlg2, name, None)
  if btn is not None:
    btn.click()
    loaded = True
    break
if not loaded:
  # fall back to the suite's own helper if there is one
  helper = getattr(suite, "press_load", None)
  if helper:
    helper(dlg2, path)
    loaded = True
say(f"    pressed Load: {loaded}")
suite._settle(dlg2, seconds=120)
quiet(dlg2, seconds=120)
p2 = dlg2.topology_panel
say(f"    after Load: edits in panel {len(p2._edits)} rows {[p2.edit_list.item(i).text() for i in range(p2.edit_list.count())]}; "
    f"experimental {dlg2.opt_experimental.isChecked()}; design {ground(dlg2._unit)} == edited {ground(dlg2._unit) == edited_design}; "
    f"map == saved {map_digest(dlg2) == edited_map}; providers {probe.providers(dlg2)}")
if len(p2._edits) != 1:
  anomaly(f"after Load the panel holds {len(p2._edits)} edits, not 1")
if ground(dlg2._unit) != edited_design:
  anomaly("after Load the unit is not the edited one that was saved")
# Tick the box: the tab should draw the edited design with a ghost.
dlg2.opt_experimental.setChecked(True)
suite._tick(200)
try:
  suite._wait_for_the_topology(dlg2, seconds=40.0)
except AssertionError as exc:
  anomaly(f"after Load and the box the tab never answered: {exc}")
quiet(dlg2, seconds=60)
S2 = stores(dlg2)
say(f"    tab after the box: holds={S2['holds']} drawn={S2['drawn']} design={S2['design']} "
    f"marks={S2['marks']} note={S2['note']!r} ghost={getattr(p2.view, '_ghost', None) is not None}")
if S2["drawn"] != S2["design"]:
  anomaly("after Load the drawn unit and the dialog's unit disagree")
if S2["marks"] and not S2["marks"][0][0]:
  anomaly(f"after Load the restored edit is marked not applied; note {S2['note']!r}")

# -------------------------------------------------------- verdict

say("")
say("== NOTES")
for n in NOTES:
  say(f"  - {n}")
say("== ANOMALIES")
if not ANOMALIES:
  say("  none")
for a in ANOMALIES:
  say(f"  - {a}")
dlg2.close()
dlg2.deleteLater()
suite._tick(100)
say("PROBE ENDED")
