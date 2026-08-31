"""The Topology tab: a view of the repeating unit's structure, and the
controls that let somebody take hold of it.

WHAT THIS TAB IS ABOUT, said here because the word is overloaded and a
GIS user will reasonably expect the other meaning. This is the
COMBINATORIAL AND SYMMETRY structure of the repeating UNIT -- which
tiles are the same shape, which edges are equivalent under the tiling's
own symmetries, and the dual. It is NOT geospatial topology: no claim
is made that the polygons on the ground share edges exactly, and with
an inset or a strand width below 1.0 the map deliberately has gaps.
GeoPackage has no topology model either, adopted or community, and
GDAL implements none; the two things share a word and nothing else.

WHAT IT IS FOR. `topology.py` is the richest thing in the vendored
library the plugin did not expose, and it offers real MANIPULATIONS
rather than only description. A person can take an edge class or a
vertex class and move it, and watch the tiling answer.

THE VIEW FOLLOWS UPSTREAM'S OWN NOTEBOOK. `examples/topology-working.
ipynb` plots with seven toggles -- original tiles, tile centres, vertex
labels, edge labels, edges, offset edges, dual tiles -- and those are
the seven here, because they are what the technique's authors reach for
when they look at one of these.
"""

from __future__ import annotations

from qgis.PyQt.QtCore import QPointF, Qt, pyqtSignal
from qgis.PyQt.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from qgis.PyQt.QtWidgets import (
  QCheckBox,
  QComboBox,
  QGridLayout,
  QGroupBox,
  QHBoxLayout,
  QLabel,
  QListWidget,
  QPushButton,
  QScrollArea,
  QVBoxLayout,
  QWidget,
)

from . import topology_edits as edits_module
from .widgets import TrimmedSpinBox

# What the seven toggles are called and whether they start on. The
# defaults show the structure a person came to look at -- the tiles,
# their edges and the labels that name what an edit can be aimed at --
# without the dual, which is a second tiling drawn over the first and
# is better asked for than imposed.
TOGGLES = (
  ("tiles", "Tiles", True),
  ("centres", "Tile centres", False),
  ("edges", "Edges", True),
  ("offset", "Offset edges", False),
  ("vertex_labels", "Vertex labels", True),
  ("edge_labels", "Edge labels", True),
  ("dual", "Dual tiling", False),
)

# Ink. The tiles are pale so the structure drawn over them reads; the
# selected class is the one saturated thing on screen.
_TILE_FILL = "#e9eef3"
_TILE_LINE = "#b9c6d2"
_EDGE_INK = "#37474f"
_VERTEX_INK = "#37474f"
_CHOSEN_INK = "#d84315"
_DUAL_INK = "#7e57c2"
_CENTRE_INK = "#90a4ae"


class TopologyView(QWidget):
  """Paints a topology, and lets a class be chosen or dragged.

  Signals:
    chose: (target, label) when somebody clicks a vertex or an edge --
      the CLASS, not the individual, because a class is what an edit
      can be aimed at.
    dragging: (dx, dy) in unit coordinates while a vertex is dragged.
    dropped: () when the drag ends and the edit should be committed.

  A DRAG IS PREVIEWED, NOT ACCUMULATED. Each frame re-applies one
  manipulation from the topology as it stood BEFORE the drag began,
  with the parameter the pointer currently implies. Accumulating a
  transform per frame would compose a hundred of them across one
  gesture, and the cost measured on 2026-08-30 says the same: applying
  a transform is 0.04-0.05s, while rebuilding the topology so that
  another edit can be aimed is 1.08s. The drag pays the first per
  frame and the second once, on release.
  """

  chose = pyqtSignal(str, str)
  dragging = pyqtSignal(float, float)
  dropped = pyqtSignal()

  def __init__(self, parent=None):
    """Set up an empty view.

    Args:
      parent: the owning widget, as Qt expects.
    """
    super().__init__(parent)
    # SMALL, BECAUSE A TAB MUST NOT DICTATE THE WINDOW'S SIZE. A
    # QStackedWidget takes the largest page's minimum, so a generous
    # minimum here would set the height of the Design tab as well --
    # and measured 2026-08-30 it did: the page wanted 607x581 against
    # Design's 428, which pushed the dialog past the screen ceiling
    # that had just been added. A MINIMUM BEATS A RESIZE, so the clamp
    # could not pull it back. The view is happiest large and must be
    # able to be small.
    self.setMinimumSize(180, 150)
    self.setMouseTracking(True)
    self._topology = None
    self._preview = None
    self._message = "Generate a map to see its topology."
    self._shown = {key: on for key, _label, on in TOGGLES}
    self._chosen = ("", "")
    self._press = None
    self._scale = 1.0
    self._origin = (0.0, 0.0)
    self._bounds = (0.0, 0.0, 1.0, 1.0)

  # ----------------------------------------------------------- state

  def show_topology(self, topology, message: str = ""):
    """Draw this topology, or a message where there is none.

    Args:
      topology: a built Topology, or None.
      message: what to say instead when there is nothing to draw.

    Returns:
      None; the widget repaints.
    """
    self._topology = topology
    self._preview = None
    self._message = "" if topology is not None else (
      message or "This design has no topology to show.")
    self.update()

  def show_preview(self, topology):
    """Draw a transient result while a drag is in progress.

    Args:
      topology: the transformed Topology to paint instead of the real
        one, or None to go back to it.

    Returns:
      None. Kept apart from `show_topology` so that letting go of a
      drag mid-gesture cannot leave the view describing something the
      record does not hold.
    """
    self._preview = topology
    self.update()

  def set_shown(self, key: str, on: bool):
    """Turn one of the seven parts of the drawing on or off.

    Args:
      key: a key from TOGGLES.
      on: whether to draw it.

    Returns:
      None.
    """
    self._shown[key] = bool(on)
    self.update()

  def set_chosen(self, target: str, label: str):
    """Highlight a class, so a person can see what an edit will move.

    Args:
      target: "edge" or "vertex".
      label: the class label, or "" for none.

    Returns:
      None.
    """
    self._chosen = (target, label)
    self.update()

  # ---------------------------------------------------------- paint

  def _drawn(self):
    """The topology actually on screen, preview included."""
    return self._preview if self._preview is not None else self._topology

  def _fit(self, topology):
    """Work out the transform from unit coordinates to the widget.

    Args:
      topology: what is being drawn.

    Returns:
      None; stores the scale and origin for `_to_screen`. The extent
      comes from the TILES rather than from everything drawn, so
      turning the dual on does not shift the tiles under the pointer
      mid-gesture -- a view that moves when you change what it shows
      is one nobody can aim at.
    """
    xs, ys = [], []
    for tile in topology.tiles:
      x0, y0, x1, y1 = tile.shape.bounds
      xs += [x0, x1]
      ys += [y0, y1]
    if not xs:
      xs, ys = [0.0, 1.0], [0.0, 1.0]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    self._bounds = (x0, y0, x1, y1)
    width = max(x1 - x0, 1e-9)
    height = max(y1 - y0, 1e-9)
    margin = 14
    self._scale = min((self.width() - 2 * margin) / width,
                      (self.height() - 2 * margin) / height)
    self._origin = ((self.width() - self._scale * width) / 2,
                    (self.height() - self._scale * height) / 2)

  def _to_screen(self, x, y):
    """One unit coordinate as a widget point.

    Args:
      x: unit x.
      y: unit y.

    Returns:
      A QPointF. Map y grows upward and widget y grows downward, hence
      the flip, which is the same convention TilePreview uses.
    """
    x0, y0, _x1, _y1 = self._bounds
    return QPointF(self._origin[0] + (x - x0) * self._scale,
                   self.height() - (self._origin[1] + (y - y0) * self._scale))

  def _to_unit(self, point):
    """One widget point back in unit coordinates.

    Args:
      point: a QPoint or QPointF from a mouse event.

    Returns:
      (x, y) in unit coordinates, which is what a manipulation's
      arguments are in.
    """
    x0, y0, _x1, _y1 = self._bounds
    return (x0 + (point.x() - self._origin[0]) / self._scale,
            y0 + (self.height() - point.y() - self._origin[1]) / self._scale)

  def paintEvent(self, event):  # noqa: N802 (Qt API)
    """Draw the topology, honouring the seven toggles."""
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(self.rect(), QColor("#fafafa"))
    topology = self._drawn()
    if topology is None:
      painter.setPen(QPen(QColor("#666666")))
      painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       self._message)
      painter.end()
      return
    self._fit(topology)
    target, chosen = self._chosen

    if self._shown["tiles"]:
      painter.setBrush(QBrush(QColor(_TILE_FILL)))
      painter.setPen(QPen(QColor(_TILE_LINE), 1))
      for tile in topology.tiles:
        painter.drawPath(self._path(tile.shape))

    if self._shown["dual"]:
      painter.setBrush(Qt.BrushStyle.NoBrush)
      pen = QPen(QColor(_DUAL_INK), 2)
      pen.setStyle(Qt.PenStyle.DashLine)
      painter.setPen(pen)
      for shape in getattr(topology, "dual_tiles", {}).values():
        painter.drawPath(self._path(shape))

    if self._shown["centres"]:
      painter.setBrush(QBrush(QColor(_CENTRE_INK)))
      painter.setPen(Qt.PenStyle.NoPen)
      for tile in topology.tiles:
        centre = getattr(tile, "centre", None)
        if centre is not None:
          painter.drawEllipse(self._to_screen(centre.x, centre.y), 3, 3)

    if self._shown["edges"]:
      for edge in topology.edges.values():
        line = self._edge_line(edge)
        if line is None:
          continue
        lit = (target == "edge" and edge.label == chosen and chosen)
        painter.setPen(QPen(QColor(_CHOSEN_INK if lit else _EDGE_INK),
                            3 if lit else 1.5))
        painter.drawPath(line)

    if self._shown["edge_labels"]:
      painter.setPen(QPen(QColor(_EDGE_INK)))
      for edge in topology.edges.values():
        where = self._edge_midpoint(edge)
        if where is not None and getattr(edge, "label", None):
          painter.drawText(where, str(edge.label))

    for vertex in topology.points.values():
      lit = (target == "vertex" and vertex.label == chosen and chosen)
      point = self._to_screen(vertex.point.x, vertex.point.y)
      painter.setBrush(QBrush(QColor(_CHOSEN_INK if lit else _VERTEX_INK)))
      painter.setPen(Qt.PenStyle.NoPen)
      painter.drawEllipse(point, 5 if lit else 3, 5 if lit else 3)
      if self._shown["vertex_labels"] and getattr(vertex, "label", None):
        painter.setPen(QPen(QColor(_VERTEX_INK)))
        painter.drawText(QPointF(point.x() + 6, point.y() - 6),
                         str(vertex.label))
    painter.end()

  def _path(self, polygon):
    """A shapely polygon as a QPainterPath in widget coordinates.

    Args:
      polygon: the shapely geometry.

    Returns:
      A QPainterPath, holes included -- even-odd filling makes them
      render without extra work, as TilePreview already relies on.
    """
    path = QPainterPath()
    rings = [polygon.exterior] + list(polygon.interiors)
    for ring in rings:
      points = [self._to_screen(x, y) for x, y in ring.coords]
      if not points:
        continue
      path.moveTo(points[0])
      for point in points[1:]:
        path.lineTo(point)
      path.closeSubpath()
    return path

  def _edge_line(self, edge):
    """One edge as a path, offset from its tiles where asked.

    Args:
      edge: the Edge to draw.

    Returns:
      A QPainterPath, or None where the edge has no geometry. The
      OFFSET toggle is upstream's own: drawing each edge slightly
      inside its tile separates the two edges that share a boundary,
      which is what makes an edge class visible at all on a dense
      unit.
    """
    try:
      line = edge.get_geometry()
    except Exception:                                 # noqa: BLE001
      return None
    if line is None or line.is_empty:
      return None
    if self._shown["offset"]:
      try:
        line = line.parallel_offset(
          (self._bounds[2] - self._bounds[0]) * 0.012, "left")
      except Exception:                               # noqa: BLE001
        pass
    geoms = getattr(line, "geoms", [line])
    path = QPainterPath()
    for part in geoms:
      coords = list(getattr(part, "coords", []))
      if not coords:
        continue
      points = [self._to_screen(x, y) for x, y in coords]
      path.moveTo(points[0])
      for point in points[1:]:
        path.lineTo(point)
    return path if not path.isEmpty() else None

  def _edge_midpoint(self, edge):
    """Where an edge's label goes.

    Args:
      edge: the Edge.

    Returns:
      A QPointF at the middle of the edge, or None.
    """
    try:
      line = edge.get_geometry()
      middle = line.interpolate(0.5, normalized=True)
    except Exception:                                 # noqa: BLE001
      return None
    return self._to_screen(middle.x, middle.y)

  # ------------------------------------------------------ pointing

  def _nearest(self, point):
    """The vertex or edge closest to a widget point.

    Args:
      point: where the pointer is.

    Returns:
      (target, label, vertex) for the nearest thing within reach, else
      ("", "", None). VERTICES WIN TIES within their radius, because a
      vertex sits ON an edge and is the smaller target -- a person
      aiming at one would otherwise get the edge underneath it.
    """
    topology = self._drawn()
    if topology is None:
      return "", "", None
    best, found = 12.0, ("", "", None)
    for vertex in topology.points.values():
      screen = self._to_screen(vertex.point.x, vertex.point.y)
      distance = ((screen.x() - point.x()) ** 2 +
                  (screen.y() - point.y()) ** 2) ** 0.5
      if distance < best:
        best, found = distance, ("vertex", vertex.label or "", vertex)
    if found[0]:
      return found
    best = 10.0
    for edge in topology.edges.values():
      where = self._edge_midpoint(edge)
      if where is None:
        continue
      distance = ((where.x() - point.x()) ** 2 +
                  (where.y() - point.y()) ** 2) ** 0.5
      if distance < best:
        best, found = distance, ("edge", edge.label or "", None)
    return found

  def mousePressEvent(self, event):  # noqa: N802 (Qt API)
    """Choose the class under the pointer, and begin a drag."""
    target, label, vertex = self._nearest(event.position()
                                          if hasattr(event, "position")
                                          else event.pos())
    if not target:
      return
    self.set_chosen(target, label)
    self.chose.emit(target, label)
    if target == "vertex" and vertex is not None:
      self._press = (self._to_unit(event.position()
                                   if hasattr(event, "position")
                                   else event.pos()),
                     self._bounds[2] - self._bounds[0])

  def mouseMoveEvent(self, event):  # noqa: N802 (Qt API)
    """Report how far a drag has travelled, in unit terms."""
    if self._press is None:
      return
    (x0, y0), span = self._press
    x, y = self._to_unit(event.position() if hasattr(event, "position")
                         else event.pos())
    # AS A FRACTION OF THE UNIT, not in map units: `nudge_vertex` takes
    # a proportion, and a drag that meant different amounts at
    # different spacings would be a control nobody could learn.
    self.dragging.emit((x - x0) / span, (y - y0) / span)

  def mouseReleaseEvent(self, event):  # noqa: N802 (Qt API)
    """End a drag, and let the panel commit it."""
    if self._press is None:
      return
    self._press = None
    self.dropped.emit()


class TopologyPanel(QWidget):
  """The whole tab: the view, the seven toggles, and the edit controls.

  Signals:
    edits_changed: the record moved, so the design should be redrawn
      and the working state restamped.
  """

  edits_changed = pyqtSignal()

  def __init__(self, parent=None):
    """Build the tab's widgets.

    Args:
      parent: the owning widget.
    """
    super().__init__(parent)
    self._topology = None
    self._unit = None
    self._edits = []
    self._drag_from = None
    layout = QHBoxLayout(self)

    self.view = TopologyView()
    self.view.chose.connect(self._on_chose)
    self.view.dragging.connect(self._on_dragging)
    self.view.dropped.connect(self._on_dropped)
    layout.addWidget(self.view, 1)

    # THE CONTROLS SCROLL, so that this tab cannot set the height of
    # every other one. A QStackedWidget takes the largest page's
    # minimum, and this column -- seven toggles, two groups, three
    # buttons and a list -- is simply taller than the Design tab:
    # measured 2026-08-30 at 552px against Design's 428, which pushed
    # the window past the screen ceiling, and a MINIMUM BEATS A
    # RESIZE, so the clamp could not pull it back. Scrolling keeps
    # every control reachable while asking for nothing.
    side_holder = QWidget()
    side = QVBoxLayout(side_holder)
    side.setContentsMargins(0, 0, 0, 0)
    side_scroll = QScrollArea()
    side_scroll.setWidget(side_holder)
    side_scroll.setWidgetResizable(True)
    side_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    side_scroll.setHorizontalScrollBarPolicy(
      Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    layout.addWidget(side_scroll)

    note = QLabel(
      "The structure of the repeating unit, before any inset or\n"
      "strand width is applied — not of the map on the ground.")
    note.setWordWrap(True)
    side.addWidget(note)

    show = QGroupBox("Show")
    show_layout = QVBoxLayout(show)
    self.toggles = {}
    for key, label, on in TOGGLES:
      box = QCheckBox(label)
      box.setChecked(on)
      box.setToolTip(f"Draws {label.lower()} in the view.")
      box.toggled.connect(
        lambda checked, k=key: self.view.set_shown(k, checked))
      show_layout.addWidget(box)
      self.toggles[key] = box
    side.addWidget(show)

    change = QGroupBox("Change")
    grid = QGridLayout(change)
    self.class_combo = QComboBox()
    self.class_combo.setToolTip("Which class of edge or vertex to move.")
    self.class_combo.currentIndexChanged.connect(self._on_class_chosen)
    grid.addWidget(QLabel("Class"), 0, 0)
    grid.addWidget(self.class_combo, 0, 1)

    self.how_combo = QComboBox()
    for key, spec in MANIPULATION_ORDER():
      self.how_combo.addItem(spec["label"], key)
    self.how_combo.setToolTip("What to do to the chosen class.")
    self.how_combo.currentIndexChanged.connect(self._rebuild_arguments)
    grid.addWidget(QLabel("Do"), 1, 0)
    grid.addWidget(self.how_combo, 1, 1)

    self._argument_rows = []
    self._argument_grid = grid
    side.addWidget(change)

    buttons = QHBoxLayout()
    self.apply_button = QPushButton("Apply")
    self.apply_button.setToolTip("Adds this change to the design.")
    self.apply_button.clicked.connect(self._apply)
    buttons.addWidget(self.apply_button)
    self.undo_button = QPushButton("Undo")
    self.undo_button.setToolTip("Removes the most recent change.")
    self.undo_button.clicked.connect(self._undo)
    buttons.addWidget(self.undo_button)
    self.clear_button = QPushButton("Clear")
    self.clear_button.setToolTip("Removes every change to this design.")
    self.clear_button.clicked.connect(self._clear)
    buttons.addWidget(self.clear_button)
    side.addLayout(buttons)

    side.addWidget(QLabel("Changes, oldest first"))
    self.edit_list = QListWidget()
    self.edit_list.setToolTip("Every change made to this design.")
    # Same reason as the view's: this list grows with what is in it
    # and must not set the floor for every other tab.
    self.edit_list.setMinimumHeight(48)
    side.addWidget(self.edit_list, 1)

    self.note = QLabel("")
    self.note.setWordWrap(True)
    side.addWidget(self.note)
    self._rebuild_arguments()

  # ------------------------------------------------------- the record

  def edits(self) -> list:
    """The edit list as it stands.

    Returns:
      A list of plain dicts, JSON-ready, oldest first.
    """
    return [dict(edit) for edit in self._edits]

  def set_edits(self, edits):
    """Put a recorded edit list back, without announcing a change.

    Args:
      edits: what the working state held, or None.

    Returns:
      None. Silent because this is a RESTORE: announcing it would ask
      the dialog to redraw a map that already describes these edits,
      which is how a restore comes to look like an edit.
    """
    self._edits = [dict(edit) for edit in (edits or [])]
    self._refresh_list()

  def set_unit(self, unit, topology, message: str = ""):
    """Show a new design's topology.

    Args:
      unit: the Tileable the topology was built from, before modifiers.
      topology: the built Topology, or None.
      message: why there is none, when there is none.

    Returns:
      None.
    """
    self._unit = unit
    self._topology = topology
    self.view.show_topology(topology, message)
    self._refresh_classes()
    self.note.setText(message if topology is None else "")
    for widget in (self.class_combo, self.how_combo, self.apply_button):
      widget.setEnabled(topology is not None)

  # -------------------------------------------------------- controls

  def _refresh_classes(self):
    """Fill the class chooser for whatever the view is showing."""
    self.class_combo.blockSignals(True)
    self.class_combo.clear()
    if self._topology is not None:
      groups = edits_module.classes(self._topology)
      target = edits_module.MANIPULATIONS[
        self.how_combo.currentData()]["target"]
      for label in groups.get(target, ""):
        self.class_combo.addItem(f"{target} {label}", (target, label))
      if groups.get(target):
        self.class_combo.addItem(f"every {target}",
                                 (target, groups[target]))
    self.class_combo.blockSignals(False)
    self._on_class_chosen()

  def _rebuild_arguments(self):
    """Build the parameter boxes the chosen manipulation needs."""
    for label, box in self._argument_rows:
      label.setParent(None)
      box.setParent(None)
    self._argument_rows = []
    key = self.how_combo.currentData()
    if key is None:
      return
    for row, (name, label, low, high, default, step) in enumerate(
        edits_module.MANIPULATIONS[key]["args"], start=2):
      caption = QLabel(label)
      box = TrimmedSpinBox()
      box.setRange(low, high)
      box.setSingleStep(step)
      box.setValue(default)
      box.setToolTip(f"{label} for this change.")
      box.setProperty("argument", name)
      self._argument_grid.addWidget(caption, row, 0)
      self._argument_grid.addWidget(box, row, 1)
      self._argument_rows.append((caption, box))
    self._refresh_classes()

  def _arguments(self) -> dict:
    """What the parameter boxes currently say."""
    return {box.property("argument"): box.value()
            for _label, box in self._argument_rows}

  def _on_class_chosen(self):
    """Highlight whatever class the chooser now names."""
    data = self.class_combo.currentData()
    if data:
      self.view.set_chosen(*data)

  def _on_chose(self, target, label):
    """Follow a click in the view back into the chooser.

    Args:
      target: "edge" or "vertex", as the view reports it.
      label: the class label that was clicked.

    Returns:
      None. Where the chooser has no entry for that class -- which
      happens when the current manipulation targets the other kind --
      nothing moves, so clicking an edge while a vertex manipulation
      is chosen does not silently retarget the edit.
    """
    for index in range(self.class_combo.count()):
      data = self.class_combo.itemData(index)
      if data and data == (target, label):
        self.class_combo.setCurrentIndex(index)
        return

  # ------------------------------------------------------------ drag

  def _on_dragging(self, dx, dy):
    """Preview a nudge while the pointer moves.

    Args:
      dx: how far, left to right, as a fraction of the unit.
      dy: how far, bottom to top, as the same fraction.

    Returns:
      None. The preview is applied from the topology as it stood
      BEFORE the drag, never from the last frame, so one gesture is
      one manipulation rather than a hundred composed.
    """
    data = self.class_combo.currentData()
    if self._topology is None or not data or data[0] != "vertex":
      return
    self._drag_from = (dx, dy)
    try:
      moved = self._topology.transform_geometry(
        True, True, data[1], "nudge_vertex", dx=float(dx), dy=float(dy))
    except Exception:                                 # noqa: BLE001
      return
    self.view.show_preview(moved)

  def _on_dropped(self):
    """Commit the drag as an edit, or put the view back."""
    self.view.show_preview(None)
    if self._drag_from is None:
      return
    dx, dy = self._drag_from
    self._drag_from = None
    data = self.class_combo.currentData()
    if not data or (abs(dx) < 1e-4 and abs(dy) < 1e-4):
      return
    self._record({"classes": data[1], "how": "nudge_vertex",
                  "args": {"dx": float(dx), "dy": float(dy)}})

  # --------------------------------------------------------- editing

  def _apply(self):
    """Add the change the controls describe."""
    data = self.class_combo.currentData()
    if self._topology is None or not data:
      return
    self._record({"classes": data[1],
                  "how": self.how_combo.currentData(),
                  "args": self._arguments()})

  def _record(self, edit):
    """Append one edit and tell the dialog.

    Args:
      edit: the record to add.

    Returns:
      None. The edit is kept even where it cannot be drawn: the
      REFUSAL is reported by whoever replays the list, so the record
      says what somebody asked for and the map says what could be
      done. Dropping it here would leave a person having pressed a
      button that did nothing and said nothing.
    """
    self._edits.append(edit)
    self._refresh_list()
    self.edits_changed.emit()

  def _undo(self):
    """Take the most recent change off."""
    if self._edits:
      self._edits.pop()
      self._refresh_list()
      self.edits_changed.emit()

  def _clear(self):
    """Take every change off this design."""
    if self._edits:
      self._edits = []
      self._refresh_list()
      self.edits_changed.emit()

  def _refresh_list(self):
    """Redraw the list of changes, oldest first."""
    self.edit_list.clear()
    for edit in self._edits:
      spec = edits_module.MANIPULATIONS.get(edit.get("how"), {})
      args = ", ".join(f"{k} {v:g}" for k, v in
                       sorted((edit.get("args") or {}).items()))
      self.edit_list.addItem(
        f"{spec.get('label', edit.get('how'))} on {edit.get('classes')}"
        + (f" ({args})" if args else ""))
    self.undo_button.setEnabled(bool(self._edits))
    self.clear_button.setEnabled(bool(self._edits))

  def report(self, refusals):
    """Say what could not be drawn.

    Args:
      refusals: sentences from the replay, or an empty list.

    Returns:
      None.
    """
    self.note.setText(" ".join(refusals))


def MANIPULATION_ORDER():  # noqa: N802 (reads as a constant)
  """The manipulations in the order the tab offers them.

  Returns:
    (key, spec) pairs, vertex moves first because they are the ones a
    drag performs and therefore the ones somebody meets first.
  """
  order = ("push_vertex", "nudge_vertex", "rotate_edge", "scale_edge",
           "zigzag_edge")
  return [(key, edits_module.MANIPULATIONS[key]) for key in order]
