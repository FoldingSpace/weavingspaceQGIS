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

import math

from qgis.PyQt.QtCore import QPointF, QRectF, Qt, pyqtSignal
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
# WARMER THAN THE INK AND COOLER THAN THE CHOSEN, so a class under the
# pointer is legible as "this is what a click would take" without
# competing with the class already chosen. Hover has to be a THIRD
# state: with only two, the moment before a click looks like the
# moment after it.
_HOVER_INK = "#f9a825"
# THE CLASS THE SELECTION BELONGS TO, in a light tint. An edit applies
# to a whole transitivity class, so the drawing has to say both things
# at once: THIS is the one you are holding, and THESE go with it. One
# colour for both said only the second, and about half the drawing lit
# up, so a click never looked aimed at anything.
_CLASSMATE_INK = "#f0b95c"
_DUAL_INK = "#7e57c2"
_CENTRE_INK = "#90a4ae"
_HANDLE_INK = "#00695c"
_HANDLE_LIT = "#00bfa5"
# The design an edit was made FROM, under the edited one. Paler than
# the tile outline it sits beneath, because it is there to be compared
# against rather than looked at: a ghost that competes with the ink
# makes the drawing harder to aim at, which is the fault the design
# view's own no-outline rule was written about.
_GHOST_INK = "#c9b8d8"
# Ground the tiles no longer cover. Warm, so it reads as a condition
# rather than as ink somebody drew, and hatched rather than filled.
_GAP_INK = "#e57373"

# WHAT EACH HANDLE MEANS, AND WHERE IT SITS. A handle IS the choice of
# manipulation -- grabbing one selects it -- so the vocabulary is in
# the drawing rather than in a chooser somebody has to set first.
#
#   at  : "end" | "middle" | "point", the anchor on the element
#   out : how far perpendicular to that anchor, in pixels, so two
#         handles on one anchor do not sit on top of each other
#   shape: how it is drawn, so the three are told apart at a glance
# WHERE EACH HANDLE SITS, and how far off the edge, in pixels. The
# offsets are perpendicular to the edge, so a handle never sits on the
# line it acts on -- at 0 and 16 the three of them piled into a cluster
# a few pixels across on a 40px edge, which is the "perceivable"
# failure the maintainer met on 2026-08-31.
# THE GLYPHS ARE 12px SEATS NOW, so the offsets are sized to keep them
# clear of each other and of the vertices at the edge's ends.
_EDGE_HANDLES = (
  ("scale_edge", "end", 0, "square"),
  ("rotate_edge", "end", 30, "circle"),
  # THE ZIGZAG STANDS FURTHER OUT, and the gap between the offsets is
  # what separates it. It and `rotate_edge` are pushed along the SAME
  # normal, one from the middle and one from the end, so at equal
  # offsets their separation is HALF THE EDGE'S SCREEN LENGTH --
  # measured 20.4px on hex-slice 6 and archimedean 4.8.8 at the
  # window's own size, inside the 26px within which `_handle_at`
  # returns whichever comes first. Rotate is asked first, so it won the
  # whole overlap and the zigzag handle could not be hit at all on 23
  # edges of each design. Different offsets make the separation
  # hypotenuse(half-length, 30), which is at least 30px however short
  # the edge, with nothing to tune.
  # PUTTING IT ON THE OTHER SIDE WAS TRIED FIRST AND IS WORSE. A
  # negative offset separates it from rotate just as well and lands it
  # where the VERTICES are: handles are tested before vertices, so
  # while an edge was held the vertex under that handle could not be
  # clicked at all, which the interaction matrix caught within minutes.
  ("zigzag_edge", "middle", 60, "diamond"),
)
# A VERTEX HAS TWO MANIPULATIONS AND THEREFORE TWO HANDLES.
# (Maintainer, 2026-08-31: "all interactions in that topology image,
# not just one".) `push_vertex` was reachable only through the chooser
# and the Apply button, so one of the five things this tab can do was
# absent from the thing it does them on.
# THEY ARE DIFFERENT KINDS OF GESTURE AND LOOK IT: a nudge is free and
# two-dimensional, a push runs along ONE direction the design chooses
# -- away from everything the vertex is joined to -- so the push handle
# sits on a drawn RAIL, which is what makes the constraint visible
# rather than surprising.
_VERTEX_HANDLES = (
  ("nudge_vertex", "point", 0, "circle"),
  ("push_vertex", "rail", 34, "rail"),
)
# Matched to the drawn seat: a handle a person can see is a
# handle they can hit.
_HANDLE_REACH = 13.0


def _point_to_segment(point, start, finish) -> float:
  """How far a point is from a line SEGMENT, not from its infinite line.

  Args:
    point: the QPointF being measured.
    start: one end of the segment.
    finish: the other.

  Returns:
    The distance in the same units the points are in. The projection
    is clamped to the segment, so a point beyond an end measures to
    that END rather than to somewhere off the edge -- which is what
    stops a short edge claiming the whole line it happens to lie on.
  """
  run, rise = finish.x() - start.x(), finish.y() - start.y()
  span = run * run + rise * rise
  if span <= 0:
    return ((point.x() - start.x()) ** 2 +
            (point.y() - start.y()) ** 2) ** 0.5
  along = ((point.x() - start.x()) * run +
           (point.y() - start.y()) * rise) / span
  along = max(0.0, min(1.0, along))
  nearest_x = start.x() + along * run
  nearest_y = start.y() + along * rise
  return ((point.x() - nearest_x) ** 2 +
          (point.y() - nearest_y) ** 2) ** 0.5


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
  # Which manipulation a grabbed handle means. The panel sets its own
  # chooser from this, so the handle and the chooser cannot disagree.
  grabbed = pyqtSignal(str)
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
    # THE FLOOR IS WHAT THE VIEW ACTUALLY GETS, because the side panel
    # takes its own preferred width and the view is what is left. At
    # 180 the drawing a person came here to edit had 180px of an 825px
    # window -- measured 2026-08-31 -- which is the "perceivable"
    # failure the maintainer met, arriving through the layout rather
    # than through the handles. The page's own sizeHint carries this
    # up to the window, which grows when the tab is chosen.
    self.setMinimumSize(420, 300)
    self.setMouseTracking(True)
    self._topology = None
    # The design the edits were made FROM, drawn as a wireframe under
    # the edited one so a change reads as a change rather than as a
    # picture somebody has to remember the previous state of.
    self._ghost = None
    # The ground the tiles no longer cover, where an edit has opened
    # gaps. Drawn subtly, because it is a fact about the design rather
    # than an error: some editing goes on working when not all of it
    # does, which is the maintainer's ruling of 2026-08-31.
    self._gaps = None
    self._preview = None
    self._message = "Generate a map to see its topology."
    self._shown = {key: on for key, _label, on in TOGGLES}
    self._chosen = ("", "")
    # What the pointer is over, which is not the same as what is
    # chosen. Mouse tracking was already on before this existed, so
    # every move event was delivered and discarded.
    self._hover = ("", "")
    # THE CONCRETE THING SELECTED, not just its class. An edit applies
    # to the class, but the handles have to be drawn ON something, and
    # the honest something is the one the person clicked.
    self._chosen_thing = None
    # A handle under the pointer, and the one being dragged.
    self._hover_handle = ""
    self._held_handle = ""
    self._press = None
    # The edge a drag took hold of, in UNIT coordinates:
    # (mid_x, mid_y, along_x, along_y, length). Kept here because the
    # view is what did the hit test and knows which concrete edge was
    # grabbed, while the panel is what knows the manipulations -- so
    # the geometry crosses over and the meaning does not.
    self._press_edge = None
    self._scale = 1.0
    self._origin = (0.0, 0.0)
    self._bounds = (0.0, 0.0, 1.0, 1.0)

  # ----------------------------------------------------------- state

  def show_topology(self, topology, message: str = "", ghost=None,
                    gaps=None):
    """Draw this topology, or a message where there is none.

    Args:
      topology: a built Topology, or None.
      message: what to say instead when there is nothing to draw.
      ghost: a second topology to draw UNDER it as a wireframe -- the
        design the edits were made from. None where there is nothing
        to compare against, which is every unedited design.
      gaps: the ground the tiles no longer cover, drawn so that a
        design which has stopped carrying a topology SHOWS where,
        rather than only saying so. None where they still meet.

    Returns:
      None; the widget repaints.
    """
    self._topology = topology
    self._ghost = ghost
    self._gaps = gaps
    self._preview = None
    # THE HELD OBJECT BELONGS TO THE OLD TOPOLOGY and every rebuild
    # makes new ones, so keeping it would draw handles on geometry
    # nothing else refers to -- and `is` comparisons against it would
    # answer False for the edge that looks identical on screen. The
    # CLASS survives a rebuild; the object does not.
    self._chosen_thing = None
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
    # FIT THE UNIT, NOT THE WHOLE PATCH. (Maintainer, 2026-08-31: the
    # interaction "has to be perceivable".) `topology.tiles` is the
    # unit AND its neighbouring copies -- 36 tiles for a four-tile unit
    # on laves 3.3.4.3.4 -- so fitting all of them drew the thing being
    # edited at a third of the size the panel could give it, with the
    # handles as a cluster of rings a few pixels across and every class
    # label overlapping its neighbour.
    # THE COPIES ARE STILL DRAWN, and run off the edges: they are
    # context, which is what says how the tiles meet, and they are
    # exactly what somebody is NOT editing. `n_tiles` is the library's
    # own count of the unit's own tiles, and the patch is laid out so
    # that the first n are those.
    # AND THE FRAME IS HELD STILL FOR THE LENGTH OF A GESTURE. A drag
    # freezes its origin and the unit's span at the press, and every
    # later position is read as a fraction of that frame -- so a fit
    # taken mid-drag makes the transform an OUTPUT of the thing the
    # drag is changing as well as the input it is measured against.
    # The loop that follows is not subtle: the preview moves the
    # geometry, the fit re-measures a larger extent, the scale falls,
    # the same screen point now means a bigger displacement, and the
    # geometry moves further. Measured 2026-09-01 with the pointer
    # HELD STILL through six repaints on laves 3.3.4.3.4: the recorded
    # nudge climbed 0.104, 0.207, 0.280, 0.318, 0.342, 0.356 while the
    # scale fell 0.6138 to 0.5541 and the drawn bounds grew at every
    # pass. What somebody is given is then decided by how many times
    # the widget happened to repaint.
    # THE PRE-DRAG FRAME IS THE RIGHT ONE TO KEEP, since it is the one
    # the drag's own origin was taken in; the fit resumes at the drop,
    # when `_press` is cleared and the next paint measures the design
    # as it finally stands.
    if getattr(self, "_press", None) is not None and self._bounds:
      return
    core = topology.tiles[:getattr(topology, "n_tiles", len(topology.tiles))]
    xs, ys = [], []
    for tile in (core or topology.tiles):
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

    # THE GHOST FIRST, so everything else is drawn over it. It is the
    # design the edits were made from, in a thin dashed outline and no
    # fill: enough to see what moved, not enough to compete with the
    # thing you are aiming at. It is deliberately NOT fitted separately
    # -- both are drawn through the same transform, or the comparison
    # would be between two pictures at different scales, which is no
    # comparison at all.
    if self._ghost is not None:
      painter.setBrush(Qt.BrushStyle.NoBrush)
      ghost_pen = QPen(QColor(_GHOST_INK), 1)
      ghost_pen.setStyle(Qt.PenStyle.DashLine)
      painter.setPen(ghost_pen)
      for tile in self._ghost.tiles:
        painter.drawPath(self._path(tile.shape))

    if self._shown["tiles"]:
      painter.setBrush(QBrush(QColor(_TILE_FILL)))
      painter.setPen(QPen(QColor(_TILE_LINE), 1))
      for tile in topology.tiles:
        painter.drawPath(self._path(tile.shape))

    # WHERE THE TILES NO LONGER MEET, over the tiles and under
    # everything a person aims at. Hatched rather than filled: this is
    # the same mark the pin column uses for "nothing can go here", and
    # the design view's own rule is that a heavy mark competes with the
    # thing being judged. It is drawn on the EDITED design, which is
    # the only one that can have gaps.
    if self._gaps is not None:
      painter.setPen(Qt.PenStyle.NoPen)
      painter.setBrush(QBrush(QColor(_GAP_INK),
                              Qt.BrushStyle.BDiagPattern))
      for part in getattr(self._gaps, "geoms", [self._gaps]):
        if not part.is_empty:
          painter.drawPath(self._path(part))

    if self._shown["dual"]:
      painter.setBrush(Qt.BrushStyle.NoBrush)
      pen = QPen(QColor(_DUAL_INK), 2)
      pen.setStyle(Qt.PenStyle.DashLine)
      painter.setPen(pen)
      # THE DUAL TILES TOO, because the tiling does. (Maintainer,
      # 2026-08-31: "the dual doesn't tile, just appear in one place?")
      # `topology.tiles` is a PATCH of repeats and `dual_tiles` is one
      # repeat's worth -- 36 against 6 on laves 3.3.4.3.4, 28 against 4
      # on hex-slice 4 -- so with the toggle on, the dual sat in the
      # middle of a field of tiles it did not cover. The tiling is
      # periodic, so the dual repeats on the same lattice; nothing was
      # replicating it.
      for offset in self._lattice_offsets(topology):
        for shape in getattr(topology, "dual_tiles", {}).values():
          painter.drawPath(self._path(shape, offset))

    if self._shown["centres"]:
      painter.setBrush(QBrush(QColor(_CENTRE_INK)))
      painter.setPen(Qt.PenStyle.NoPen)
      for tile in topology.tiles:
        centre = getattr(tile, "centre", None)
        if centre is not None:
          painter.drawEllipse(self._to_screen(centre.x, centre.y), 3, 3)

    over, warm = self._hover
    if self._shown["edges"]:
      for edge in topology.edges.values():
        line = self._edge_line(edge)
        if line is None:
          continue
        # THREE STATES, NOT TWO. `held` is the one edge the person
        # clicked; `kin` is the rest of its class, which an edit will
        # change as well; `near` is what a click would take now. One
        # colour for held and kin said only "these all change", so
        # half the drawing lit at once and a click never looked aimed.
        held = (target == "edge" and edge is self._chosen_thing)
        kin = (not held and target == "edge" and edge.label == chosen
               and chosen)
        near = (not held and not kin and over == "edge"
                and edge.label == warm and warm)
        painter.setPen(QPen(QColor(
          _CHOSEN_INK if held else _CLASSMATE_INK if kin
          else _HOVER_INK if near else _EDGE_INK),
          3 if held else 2 if kin or near else 1.5))
        painter.drawPath(line)

    if self._shown["edge_labels"]:
      painter.setPen(QPen(QColor(_EDGE_INK)))
      for edge in topology.edges.values():
        where = self._edge_midpoint(edge)
        if where is not None and getattr(edge, "label", None):
          painter.drawText(where, str(edge.label))

    for vertex in topology.points.values():
      held = (target == "vertex" and vertex is self._chosen_thing)
      kin = (not held and target == "vertex" and vertex.label == chosen
             and chosen)
      near = (not held and not kin and over == "vertex"
              and vertex.label == warm and warm)
      point = self._to_screen(vertex.point.x, vertex.point.y)
      painter.setBrush(QBrush(QColor(
        _CHOSEN_INK if held else _CLASSMATE_INK if kin
        else _HOVER_INK if near else _VERTEX_INK)))
      painter.setPen(Qt.PenStyle.NoPen)
      size = 5 if held else 4 if kin or near else 3
      painter.drawEllipse(point, size, size)
      if self._shown["vertex_labels"] and getattr(vertex, "label", None):
        painter.setPen(QPen(QColor(_VERTEX_INK)))
        painter.drawText(QPointF(point.x() + 6, point.y() - 6),
                         str(vertex.label))

    # THE HANDLES GO ON TOP, because they are the thing being aimed at
    # and they sit on the geometry they belong to. A preview is drawn
    # from the topology as it stood before the drag, so during a drag
    # the handles would be describing a shape that is no longer under
    # them -- they are left out until the gesture ends.
    if self._preview is None:
      frame = self._edge_frame(self._chosen_thing) \
          if self._chosen[0] == "edge" else None
      for key, where, shape in self.handles():
        lit = (key in (self._hover_handle, self._held_handle))
        self._draw_handle(painter, key, where, frame, lit)
    painter.end()

  def _draw_handle(self, painter, key, where, frame, lit):
    """Draw one handle AS A PICTURE OF WHAT IT DOES.

    Args:
      painter: the active QPainter.
      key: the manipulation this handle performs.
      where: its position, in widget coordinates.
      frame: the chosen edge's (mid_x, mid_y, along_x, along_y, length)
        in unit coordinates, or None for a vertex. The glyphs that have
        a direction are drawn ALONG the edge, since an arrow pointing
        somewhere the edge does not go is worse than no arrow.
      lit: whether the pointer is on it, or it is being dragged.

    Returns:
      None.

    WHY GLYPHS RATHER THAN A HOVER LABEL. (Maintainer, 2026-08-31:
    "hover states aren't as good as shapes that make sense ... like
    visually make sense for what they do".) A hover has to be
    discovered before it can teach anything, and a first-time reader
    never hovers -- so what the handles were was three abstract shapes,
    a square, a circle and a diamond, whose meanings existed only in
    the code. A double-headed arrow along the edge, a curved arrow, and
    a little wave say stretch, turn and zigzag without anybody being
    told, and they go on saying it while the pointer is elsewhere.

    EVERY GLYPH IS DRAWN OVER A PALE DISC, because a mark that competes
    with vertex and edge labels on a crowded drawing is a mark nobody
    finds -- and this project's own measurement of an unclipped hatch
    is what that costs. The disc is the perceivable part; the glyph
    inside it is the learnable part.
    """
    # BIG ENOUGH TO READ THE GLYPH IN. At eight pixels the arrow, the
    # arc and the wave were three indistinguishable rings; the glyph is
    # the whole point of drawing them, so the seat is sized for the
    # glyph rather than for the dot it used to be.
    size = 14.0 if lit else 12.0
    ink = QColor(_HANDLE_LIT if lit else _HANDLE_INK)
    # THE RAIL IS DRAWN BEFORE ITS HANDLE, from the vertex out to it,
    # so the one direction a push can take is visible before anybody
    # drags anything. Without it the handle looks free, and a person
    # pulling sideways would find the design moving somewhere else.
    if key == "push_vertex" and self._chosen_thing is not None:
      try:
        anchor = self._to_screen(self._chosen_thing.point.x,
                                 self._chosen_thing.point.y)
      except Exception:                               # noqa: BLE001
        anchor = None
      if anchor is not None:
        rail = QPen(QColor(_HANDLE_INK), 1.0)
        rail.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(rail)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(anchor, where)
    # The seat: a filled disc with a white rim, so the glyph reads
    # against tiles, edges and labels alike.
    painter.setPen(QPen(QColor("#ffffff"), 2.0))
    painter.setBrush(QBrush(QColor("#ffffff")))
    painter.drawEllipse(where, size, size)
    painter.setPen(QPen(ink, 1.6))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(where, size, size)

    # Which way the edge runs, on SCREEN. The view flips y, so this is
    # taken from screen points rather than from the unit vector.
    angle = 0.0
    if frame is not None:
      mid_x, mid_y, ax, ay, _length = frame
      here = self._to_screen(mid_x, mid_y)
      there = self._to_screen(mid_x + ax, mid_y + ay)
      angle = math.degrees(math.atan2(there.y() - here.y(),
                                      there.x() - here.x()))
    painter.save()
    painter.translate(where)
    painter.rotate(angle)
    painter.setPen(QPen(ink, 1.8))
    reach = size - 2.5
    if key == "scale_edge":
      # A DOUBLE-HEADED ARROW ALONG THE EDGE: pull the end out or in.
      painter.drawLine(QPointF(-reach, 0), QPointF(reach, 0))
      for tip, step in ((reach, -1), (-reach, 1)):
        painter.drawLine(QPointF(tip, 0),
                         QPointF(tip + 3 * step, -3))
        painter.drawLine(QPointF(tip, 0),
                         QPointF(tip + 3 * step, 3))
    elif key == "rotate_edge":
      # A CURVED ARROW: the one glyph everybody already reads as turn.
      rect = QRectF(-reach, -reach, reach * 2, reach * 2)
      painter.drawArc(rect, 30 * 16, 240 * 16)
      painter.drawLine(QPointF(reach * 0.87, -reach * 0.5),
                       QPointF(reach * 0.87 - 3, -reach * 0.5 - 3))
      painter.drawLine(QPointF(reach * 0.87, -reach * 0.5),
                       QPointF(reach * 0.87 + 2, -reach * 0.5 - 4))
    elif key == "zigzag_edge":
      # A WAVE: the shape the manipulation makes, at the amplitude it
      # is about to make it in.
      path = QPainterPath(QPointF(-reach, 0))
      path.lineTo(QPointF(-reach / 2, -reach * 0.7))
      path.lineTo(QPointF(0, reach * 0.7))
      path.lineTo(QPointF(reach / 2, -reach * 0.7))
      path.lineTo(QPointF(reach, 0))
      painter.drawPath(path)
    elif key == "push_vertex":
      # A SINGLE ARROW POINTING OUT ALONG THE RAIL: one direction, away
      # from everything this vertex is joined to. The glyph is turned
      # to the rail rather than to the edge, since there is no edge.
      painter.rotate(-angle)
      way = self.push_direction() or (1.0, 0.0)
      painter.rotate(math.degrees(math.atan2(way[1], way[0])))
      painter.drawLine(QPointF(-reach, 0), QPointF(reach, 0))
      painter.drawLine(QPointF(reach, 0), QPointF(reach - 4, -3.5))
      painter.drawLine(QPointF(reach, 0), QPointF(reach - 4, 3.5))
    else:
      # A VERTEX MOVES IN ANY DIRECTION, so: a four-way arrow.
      painter.rotate(-angle)                 # direction means nothing here
      for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        painter.drawLine(QPointF(0, 0), QPointF(x * reach, y * reach))
        painter.drawLine(QPointF(x * reach, y * reach),
                         QPointF(x * reach - (x * 3) + (y * 3),
                                 y * reach - (y * 3) + (x * 3)))
        painter.drawLine(QPointF(x * reach, y * reach),
                         QPointF(x * reach - (x * 3) - (y * 3),
                                 y * reach - (y * 3) - (x * 3)))
    painter.restore()

  def _lattice_offsets(self, topology):
    """Every translation that carries the unit onto a patch copy.

    Args:
      topology: what is being drawn.

    Returns:
      A list of (dx, dy) in unit coordinates, starting with (0, 0).
      Empty of duplicates, so a dual is drawn once per position.

    TAKEN FROM THE TILEABLE'S OWN VECTORS, which are exact.

    THE OBVIOUS ROUTE WAS TRIED FIRST AND IS WRONG. `Topology`'s
    docstring promises the patch is laid out so that
    `tiles[i % n_tiles]` is the base tile of `tiles[i]`, so the offset
    of copy i looks like the difference between the two centres.
    Measured on laves 3.3.4.3.4: that gives TWENTY-ONE distinct offsets
    for nine positions, clustered around the true lattice but scattered
    by about 1.4 units, because a tile's `centre` is an incentre
    recomputed per tile and the correspondence is not exact. Drawing a
    dual at each would have put twenty-one copies where nine belong.

    The tileable states the lattice outright -- `vectors` maps (1,0)
    and (0,1) to the two translations -- and the patch is one ring of
    copies, which its own tile count confirms.
    """
    tiles = getattr(topology, "tiles", None)
    base = getattr(topology, "n_tiles", 0)
    tileable = getattr(topology, "tileable", None)
    vectors = getattr(tileable, "vectors", None) if tileable else None
    if not tiles or base <= 0 or not vectors:
      return [(0.0, 0.0)]
    # ASKED OF THE TRANSLATIONS, NOT OF HOW THEY ARE KEYED. This read
    # `vectors.get((1, 0))` and `.get((0, 1))` until 2026-09-01, and a
    # HEX tileable keys the same dict by three-element coordinates --
    # (0,1,-1), (1,0,-1), (1,-1,0) -- so both lookups missed and the
    # fallback below fired in silence. Measured that day: 871 of the
    # catalogue's 1,168 entries got the repeat and 297 did not, among
    # them every hex-slice, hex-colouring and square-colouring, and
    # hex-slice is one of the two designs the commit that wrote this
    # quotes as its own measurement. Two lattice translations are two
    # lattice translations however the dictionary spells their names,
    # so the shortest and the shortest not parallel to it are taken.
    first = second = None
    for candidate in sorted(
        (tuple(float(c) for c in v) for v in vectors.values()),
        key=lambda v: v[0] * v[0] + v[1] * v[1]):
      if candidate[0] == 0 and candidate[1] == 0:
        continue
      if first is None:
        first = candidate
        continue
      # NOT PARALLEL, or the two together describe a line rather than
      # a lattice and every copy would land on one row.
      cross = first[0] * candidate[1] - first[1] * candidate[0]
      if abs(cross) > 1e-9:
        second = candidate
        break
    if first is None or second is None:
      return [(0.0, 0.0)]
    # HOW FAR THE PATCH REACHES, asked of the patch rather than
    # assumed: 36 tiles over a unit of 4 is nine positions, which is
    # one ring. A design whose patch is bigger draws more copies
    # without this having to know which.
    copies = max(1, len(tiles) // base)
    reach = max(1, int(round(copies ** 0.5)) // 2)
    return [(first[0] * i + second[0] * j, first[1] * i + second[1] * j)
            for i in range(-reach, reach + 1)
            for j in range(-reach, reach + 1)]

  def _path(self, polygon, offset=(0.0, 0.0)):
    """A shapely polygon as a QPainterPath in widget coordinates.

    Args:
      polygon: the shapely geometry.
      offset: (dx, dy) in UNIT coordinates to draw it at instead of
        where it sits, which is how one repeat's worth of dual tiles is
        drawn across the whole patch. The default draws it in place.

    Returns:
      A QPainterPath, holes included -- even-odd filling makes them
      render without extra work, as TilePreview already relies on.
    """
    path = QPainterPath()
    rings = [polygon.exterior] + list(polygon.interiors)
    for ring in rings:
      points = [self._to_screen(x + offset[0], y + offset[1])
                for x, y in ring.coords]
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
      (target, label, thing) for the nearest thing within reach, else
      ("", "", None). `thing` is the Vertex or the Edge itself, so a
      caller that needs its geometry does not have to find it again
      from the label -- a class may hold several edges, and the one a
      person grabbed is the one a drag is about. VERTICES WIN TIES
      within their radius, because a vertex sits ON an edge and is the
      smaller target -- a person aiming at one would otherwise get the
      edge underneath it.
    """
    topology = self._drawn()
    if topology is None:
      return "", "", None
    # EIGHT PIXELS, NOT TWELVE. A vertex sits at the END of every edge
    # meeting it, so its reach is subtracted from both. Measured
    # 2026-08-30 on laves 3.3.4.3.4 at a realistic view size, edges run
    # 31 to 43px on screen -- so a 12px reach at each end claimed 24 of
    # a median 43, and MORE THAN HALF of every edge could not be
    # clicked as an edge at all. At eight it is a third, which leaves
    # the middle of an edge reliably an edge, and a vertex is still the
    # easier target of the two because it wins ties inside its radius.
    best, found = 8.0, ("", "", None)
    for vertex in topology.points.values():
      screen = self._to_screen(vertex.point.x, vertex.point.y)
      distance = ((screen.x() - point.x()) ** 2 +
                  (screen.y() - point.y()) ** 2) ** 0.5
      if distance < best:
        best, found = distance, ("vertex", vertex.label or "", vertex)
    if found[0]:
      return found
    # AN EDGE IS CLICKABLE ALONG ITS LENGTH, not at a disc on its
    # middle. Until 2026-08-30 this measured the distance to
    # `_edge_midpoint` alone, so clicking squarely on an edge anywhere
    # but its centre selected nothing -- and the design measured that
    # day has 107 edges whose midpoints are small and crowded.
    best = 8.0
    for edge in topology.edges.values():
      distance = self._distance_to_edge(edge, point)
      if distance is not None and distance < best:
        best, found = distance, ("edge", edge.label or "", edge)
    return found

  def _distance_to_edge(self, edge, point) -> float | None:
    """How far a widget point is from an edge, in pixels.

    Args:
      edge: the Edge.
      point: where the pointer is.

    Returns:
      The distance to the nearest point ON the edge, following every
      vertex of it rather than the straight line between its ends --
      an edge that has been zigzagged already is a wiggly line, and
      the thing a person aims at is the line they can see. None where
      the edge has no geometry.
    """
    try:
      line = edge.get_geometry()
      coords = list(getattr(line, "coords", []))
    except Exception:                                 # noqa: BLE001
      return None
    if len(coords) < 2:
      return None
    best = None
    previous = self._to_screen(*coords[0])
    for x, y in coords[1:]:
      current = self._to_screen(x, y)
      distance = _point_to_segment(point, previous, current)
      best = distance if best is None else min(best, distance)
      previous = current
    return best

  def handles(self):
    """Where the handles are, for the thing now selected.

    Returns:
      A list of (manipulation key, QPointF, shape). Empty where
      nothing is selected or its geometry will not answer.

    A HANDLE IS THE CHOICE OF MANIPULATION rather than a way of
    supplying a number to one already chosen. That is the whole of the
    redesign of 2026-08-30: the drag used to mean whatever the `how`
    chooser said, which is a mapping that exists only in the code, so
    nothing on screen said a drag would do anything or what. A handle
    sits where the thing it moves actually moves -- the end that
    swings, the end that stretches, the middle that bows out -- and
    the previous arrangement grabbed the MIDPOINT for rotate and
    scale, which is the one point neither of them moves.
    """
    target, _label = self._chosen
    thing = self._chosen_thing
    if thing is None:
      return []
    if target == "vertex":
      try:
        point = self._to_screen(thing.point.x, thing.point.y)
      except Exception:                               # noqa: BLE001
        return []
      placed = []
      for key, at, out, shape in _VERTEX_HANDLES:
        if at != "rail":
          placed.append((key, point, shape))
          continue
        # THE RAIL POINTS WHERE THE PUSH WOULD GO, and where the design
        # gives it nowhere to go there is no handle at all. Measured
        # 2026-08-31: `push_vertex` sums the unit vectors from each
        # neighbour, and at a symmetric vertex those CANCEL -- on laves
        # 3.3.4.3.4 and hex-slice 3 the resultant is 1e-9, so the
        # control genuinely cannot move that design. A handle that
        # looks live and does nothing is worse than an absent one.
        way = self.push_direction()
        if way is None:
          continue
        placed.append((key,
                       QPointF(point.x() + way[0] * out,
                               point.y() + way[1] * out),
                       shape))
      return placed
    frame = self._edge_frame(thing)
    if frame is None:
      return []
    mid_x, mid_y, ax, ay, _length = frame
    try:
      coords = list(thing.get_geometry().coords)
    except Exception:                                 # noqa: BLE001
      return []
    anchors = {"end": self._to_screen(*coords[-1]),
               "middle": self._to_screen(mid_x, mid_y)}
    # The perpendicular, in SCREEN terms. The view flips y, so the
    # screen normal is taken from screen points rather than from the
    # unit vector, or the handles sit on the wrong side.
    start, finish = self._to_screen(*coords[0]), self._to_screen(*coords[-1])
    run, rise = finish.x() - start.x(), finish.y() - start.y()
    reach = (run * run + rise * rise) ** 0.5 or 1.0
    normal = (-rise / reach, run / reach)
    placed = []
    for key, at, out, shape in _EDGE_HANDLES:
      anchor = anchors.get(at)
      if anchor is None:
        continue
      placed.append((key,
                     QPointF(anchor.x() + normal[0] * out,
                             anchor.y() + normal[1] * out),
                     shape))
    return placed

  def push_direction(self):
    """Which way a push would move the chosen vertex, on screen.

    Returns:
      A unit (dx, dy) in WIDGET coordinates, or None where nothing is
      chosen, the chosen thing is not a vertex, or the direction
      cancels to nothing.

    ASKED OF THE LIBRARY RATHER THAN REIMPLEMENTED. `push_vertex`
    returns its displacement without applying it, so calling it with a
    distance of one gives the direction and costs nothing -- and it
    cannot drift from what the manipulation will actually do, which a
    second copy of the arithmetic here certainly would.

    THE SCREEN FLIP IS WHY THIS RETURNS WIDGET COORDINATES. Map y grows
    upward and widget y grows downward, so a direction taken in unit
    space and drawn without flipping puts the rail on the wrong side of
    the vertex -- the same trap the edge handles' normal already
    carries a comment about.
    """
    if self._chosen[0] != "vertex" or self._chosen_thing is None:
      return None
    topology = self._drawn()
    if topology is None:
      return None
    try:
      dx, dy = topology.push_vertex(self._chosen_thing, 1.0)
    except Exception:                                 # noqa: BLE001
      return None
    # A CANCELLED PUSH IS TESTED IN UNIT COORDINATES, NOT IN PIXELS.
    # `push_d = 1.0` returns a vector whose length is a property of the
    # VERTEX -- 0.414 on archimedean 4.8.8, 1.5e-9 on laves 3.3.4.3.4
    # where the incident edges are symmetric and the unit vectors
    # cancel. Nine orders apart, so this discriminates with nothing to
    # tune. Asking in PIXELS instead hid the real one: 0.414 units at
    # this zoom is half a pixel, so a one-pixel floor called a working
    # control dead.
    if (dx * dx + dy * dy) ** 0.5 < 1e-6:
      return None
    here = self._to_screen(self._chosen_thing.point.x,
                           self._chosen_thing.point.y)
    there = self._to_screen(self._chosen_thing.point.x + dx,
                            self._chosen_thing.point.y + dy)
    run, rise = there.x() - here.x(), there.y() - here.y()
    reach = (run * run + rise * rise) ** 0.5
    if reach <= 0.0:                    # degenerate transform only
      return None
    return (run / reach, rise / reach)

  def _handle_at(self, point) -> str:
    """The manipulation whose handle is under a point, or "".

    Args:
      point: where the pointer is.

    Returns:
      The manipulation key. Handles are tested BEFORE edges and
      vertices, because a handle sits on top of the thing it belongs
      to and is the smaller target.
    """
    for key, where, _shape in self.handles():
      if ((where.x() - point.x()) ** 2 +
          (where.y() - point.y()) ** 2) ** 0.5 < _HANDLE_REACH:
        return key
    return ""

  def _edge_frame(self, edge):
    """An edge's own axes, in unit coordinates.

    Args:
      edge: the Edge a drag took hold of.

    Returns:
      (mid_x, mid_y, along_x, along_y, length) with `along` a unit
      vector from the first end to the last, or None where the edge
      has no usable geometry. END TO END rather than following every
      vertex: an edge that has already been zigzagged is a wiggly
      line, and what a person drags is still the thing running between
      its two ends.
    """
    try:
      line = edge.get_geometry()
      coords = list(getattr(line, "coords", []))
    except Exception:                                 # noqa: BLE001
      return None
    if len(coords) < 2:
      return None
    (x0, y0), (x1, y1) = coords[0], coords[-1]
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    if length <= 0:
      return None
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0,
            (x1 - x0) / length, (y1 - y0) / length, length)

  def grabbed_edge(self):
    """The frame of the edge a drag is holding, or None.

    Returns:
      The tuple `_edge_frame` describes, for the edge under the press.
    """
    return self._press_edge

  def unit_span(self) -> float:
    """How big the unit is, in its own coordinates.

    Returns:
      The LARGER of the width and the height the view fitted to. A
      drag arrives as a fraction of this, so anything comparing a drag
      with an edge's LENGTH needs it to get back into the same terms.

    IT MUST AGREE WITH `topology_edits.unit_span`, WHICH OWNS THE
    DEFINITION, because a drag's fraction is multiplied back out by
    that one when the edit is committed. It read the WIDTH alone until
    2026-09-01 while the model read `max(width, height)`, so on any
    unit that is not square the committed move overshot where the
    pointer had been -- measured at 1.268x on laves 3.3.4.3.4, whose
    unit is 557.68 by 707.11, and 1.000x on the square designs, which
    is why every example anybody tried hid it.
    """
    return max(self._bounds[2] - self._bounds[0],
               self._bounds[3] - self._bounds[1])

  def mousePressEvent(self, event):  # noqa: N802 (Qt API)
    """Choose the class under the pointer, and begin a drag.

    EDGES DRAG AS WELL AS VERTICES since 2026-08-30. Before that a
    click on an edge selected its class and nothing more, so the three
    manipulations that are ABOUT edges -- zigzag, rotate, scale -- were
    reachable only by typing a number and pressing Apply.
    """
    point = (event.position() if hasattr(event, "position")
             else event.pos())
    # A HANDLE FIRST. It sits on the thing it belongs to, so testing
    # the thing first would make the handles unreachable.
    handle = self._handle_at(point)
    if handle:
      self._held_handle = handle
      # THE SAME EXPRESSION THE COMMIT USES, asked of the one method
      # that owns it rather than written out a second time here.
      self._press = (self._to_unit(point), self.unit_span())
      self._press_edge = (self._edge_frame(self._chosen_thing)
                          if self._chosen[0] == "edge" else None)
      self.grabbed.emit(handle)
      self.setCursor(Qt.CursorShape.ClosedHandCursor)
      return
    target, label, thing = self._nearest(point)
    if not target:
      return
    # SELECT, THEN ACT. The click chooses whatever is under the
    # pointer, whatever manipulation happens to be named -- and the
    # panel narrows its chooser to what suits the selection, rather
    # than the chooser deciding in advance what may be clicked. The
    # arrangement before this filtered the class list by the current
    # manipulation, so clicking an edge while a vertex manipulation
    # was chosen moved nothing in the panel while the DRAWING went on
    # highlighting the edge: one fact, two stores, disagreeing on
    # screen.
    self._chosen_thing = thing
    self.set_chosen(target, label)
    self.chose.emit(target, label)

  def mouseMoveEvent(self, event):  # noqa: N802 (Qt API)
    """Follow the pointer: report a drag, or light what is under it."""
    point = event.position() if hasattr(event, "position") else event.pos()
    if self._press is None:
      # NOT A DRAG, SO IT IS HOVER. `setMouseTracking(True)` has been
      # on since this widget was written and every move event arrived
      # here and was discarded, so nothing told a person that a click
      # would land on anything until they made it.
      handle = self._handle_at(point)
      target, label, _thing = ("", "", None) if handle \
          else self._nearest(point)
      if (handle, target, label) != (self._hover_handle, *self._hover):
        self._hover_handle, self._hover = handle, (target, label)
        self.setCursor(Qt.CursorShape.OpenHandCursor
                       if handle or target
                       else Qt.CursorShape.ArrowCursor)
        self.update()
      return
    (x0, y0), span = self._press
    x, y = self._to_unit(point)
    # AS A FRACTION OF THE UNIT, not in map units: the manipulations
    # take proportions, and a drag that meant different amounts at
    # different spacings would be a control nobody could learn.
    self.dragging.emit((x - x0) / span, (y - y0) / span)

  def mouseReleaseEvent(self, event):  # noqa: N802 (Qt API)
    """End a drag, and let the panel commit it."""
    if self._press is None:
      return
    self._press = None
    self._press_edge = None
    self._held_handle = ""
    self.setCursor(Qt.CursorShape.OpenHandCursor
                   if self._hover_handle or self._hover[0]
                   else Qt.CursorShape.ArrowCursor)
    self.dropped.emit()

  def leaveEvent(self, event):  # noqa: N802 (Qt API)
    """Put the highlight out when the pointer goes.

    Without this the last thing hovered stays lit after the pointer
    has left the drawing, which says a click would land somewhere it
    would not.
    """
    if self._hover != ("", ""):
      self._hover = ("", "")
      self.update()
    super().leaveEvent(event)


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
    # One per edit, as the replay reported them: whether each was
    # applied, and whether the design still carried a topology after
    # it. Empty until a replay has answered, and the list says nothing
    # rather than guessing while it is.
    self._marks = []
    self._drag_from = None
    layout = QHBoxLayout(self)

    self.view = TopologyView()
    self.view.chose.connect(self._on_chose)
    self.view.grabbed.connect(self._on_grabbed)
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
    # AND IT MUST NOT BE CRUSHED, which is the other half of scrolling.
    # The horizontal bar is deliberately off, so a column narrower than
    # its content does not scroll -- it CLIPS, with no way to reach what
    # is cut off. Measured 2026-08-31 at the window's own size: 71px of
    # viewport for content wanting 271, which is every control on this
    # side of the tab gone. The floor is taken from the content itself
    # in `showEvent`, once a real layout pass has made the answer
    # meaningful.
    self._side_scroll = side_scroll
    self._side_holder = side_holder
    self._floored = False

    # ONE LINE, BECAUSE THE LABEL WRAPS. `setWordWrap(True)` reflows to
    # whatever width the panel has, so an embedded newline is the
    # plugin fighting the renderer: it broke after "inset or" with room
    # to spare and left a ragged two-and-a-bit lines. Same rule as the
    # release body against the changelog -- the question is always
    # whether the renderer reflows, and here it does.
    note = QLabel(
      "The structure of the repeating unit, before any inset or "
      "strand width is applied — not of the map on the ground.")
    note.setWordWrap(True)
    side.addWidget(note)

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

    # WHAT TO DRAW GOES LAST, AND IN TWO COLUMNS. (Maintainer's
    # screenshot, 2026-08-31.) These seven checkboxes stood FIRST and in
    # one column, so the side panel opened with a legend and the
    # controls the tab exists for -- the class, the manipulation, its
    # arguments, Apply -- were below the fold of a scroll area, with
    # "Change" cut off at the bottom edge. Somebody opening the tab had
    # to scroll to find out that it does anything.
    # THEY ARE A DISPLAY PREFERENCE, not an act: nothing here changes a
    # design, so nothing here should come before the things that do.
    # Two columns halves the height they take, which is what stops the
    # change list being squeezed on a short window.
    show = QGroupBox("Show")
    show_layout = QGridLayout(show)
    self.toggles = {}
    for index, (key, label, on) in enumerate(TOGGLES):
      box = QCheckBox(label)
      box.setChecked(on)
      box.setToolTip(f"Draws {label.lower()} in the view.")
      box.toggled.connect(
        lambda checked, k=key: self.view.set_shown(k, checked))
      show_layout.addWidget(box, index // 2, index % 2)
      self.toggles[key] = box
    side.addWidget(show)

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

  def showEvent(self, event):  # noqa: N802 (Qt API)
    """Give the control column a floor, once the layout is real.

    Args:
      event: Qt's show event, passed straight through.

    Returns:
      None.

    SIZE HINTS ARE STALE BEFORE A LAYOUT PASS, which is this project's
    own rule and the reason this is not done in the constructor: a
    column measured before assembly reports its children's phantom
    widths. `activate()` forces the pass, and the flag makes it once --
    re-reading on every show would let the floor creep up as the
    content changes, which is a feedback loop rather than a floor.
    """
    super().showEvent(event)
    if self._floored:
      return
    self._side_holder.layout().activate()
    wanted = self._side_holder.sizeHint().width()
    if wanted > 0:
      # The scrollbar's own width, so the vertical bar cannot eat into
      # the content it is there to scroll.
      bar = self._side_scroll.verticalScrollBar().sizeHint().width()
      self._side_scroll.setMinimumWidth(wanted + bar)
      self._floored = True

  def set_unit(self, unit, topology, message: str = "", ghost=None):
    """Show a new design's topology.

    Args:
      unit: the Tileable the topology was built from, before modifiers.
        Since 2026-08-31 this is the design AS EDITED, where there are
        edits, because a picture that does not answer to what somebody
        just did is not worth drawing.
      topology: the built Topology, or None. Where there are edits this
        is the CHAINED object, whose classes are the ones the person
        has been aiming with -- and which exists even on a design whose
        gaps would refuse a fresh build.
      message: why there is none, when there is none.
      ghost: the topology the edits were made FROM, drawn underneath as
        a wireframe so the change is visible as a change, or None where
        nothing has been edited and there is nothing to compare with.

    Returns:
      None.
    """
    self._unit = unit
    self._topology = topology
    # WHERE THE TILES NO LONGER MEET, computed once here rather than at
    # every repaint: 0.3 ms is cheap against a build and not against a
    # hover. None where the design is sound, which is the ordinary case
    # and draws nothing at all.
    where = None
    if unit is not None:
      ratio, missing = edits_module.gaps(unit)
      if ratio >= edits_module.GAP_TOLERANCE:
        where = missing
    self.view.show_topology(topology, message, ghost=ghost, gaps=where)
    self._refresh_classes()
    self.note.setText(message if topology is None else "")
    for widget in (self.class_combo, self.how_combo, self.apply_button):
      widget.setEnabled(topology is not None)

  # -------------------------------------------------------- controls

  def _refresh_classes(self):
    """Fill the class chooser with everything the unit has.

    SELECT, THEN ACT (2026-08-30). This used to list only the classes
    the CURRENT manipulation could be aimed at, which made the tab
    mode-first: you had to name the verb before the drawing would
    answer to the noun. So somebody who opened the tab, saw an edge
    they wanted to bend, and clicked it got nothing at all -- the
    default manipulation targets vertices. Every drawing tool anybody
    has used works the other way round, and worse, the VIEW
    highlighted the clicked edge while the chooser did not follow, so
    the two disagreed on screen.

    Both kinds are offered now, and `_refresh_manipulations` narrows
    the VERB to what suits whatever is selected.
    """
    self.class_combo.blockSignals(True)
    self.class_combo.clear()
    if self._topology is not None:
      groups = edits_module.classes(self._topology)
      for target in ("vertex", "edge"):
        for label in groups.get(target, ""):
          self.class_combo.addItem(f"{target} {label}", (target, label))
        if groups.get(target):
          self.class_combo.addItem(f"every {target}",
                                   (target, groups[target]))
    self.class_combo.blockSignals(False)
    self._refresh_manipulations()
    self._on_class_chosen()

  def _refresh_manipulations(self):
    """Offer only the manipulations that suit what is selected.

    Returns:
      None. The chooser keeps whatever it was on where that is still
      valid, so narrowing the list does not silently retarget an edit
      somebody was in the middle of describing.
    """
    data = self.class_combo.currentData()
    kind = data[0] if data else ""
    wanted = self.how_combo.currentData()
    self.how_combo.blockSignals(True)
    self.how_combo.clear()
    for key, spec in edits_module.MANIPULATIONS.items():
      if not kind or spec["target"] == kind:
        self.how_combo.addItem(spec["label"], key)
    if wanted is not None:
      for index in range(self.how_combo.count()):
        if self.how_combo.itemData(index) == wanted:
          self.how_combo.setCurrentIndex(index)
          break
    self.how_combo.blockSignals(False)
    self._rebuild_arguments()

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
    # IT USED TO REFILL THE CLASS LIST FROM HERE, because the list was
    # filtered by the manipulation. Under select-then-act the list
    # holds every class whatever the verb is, so that call is not
    # merely redundant -- `_refresh_classes` now calls
    # `_refresh_manipulations`, which calls this, and the pair would
    # recurse without end.

  def _arguments(self) -> dict:
    """What the parameter boxes currently say."""
    return {box.property("argument"): box.value()
            for _label, box in self._argument_rows}

  def _on_class_chosen(self):
    """Highlight whatever class the chooser now names, and re-offer
    the manipulations that suit it."""
    data = self.class_combo.currentData()
    if data:
      self.view.set_chosen(*data)
    # The verb follows the noun. Safe to call from here: it touches
    # the how chooser and the argument boxes and never the class list.
    self._refresh_manipulations()

  def _on_chose(self, target, label):
    """Follow a click in the view back into the chooser.

    Args:
      target: "edge" or "vertex", as the view reports it.
      label: the class label that was clicked.

    Returns:
      None. The list holds every class of both kinds since
      2026-08-30, so a click always lands somewhere -- which is the
      whole of select-then-act. Before that the list was filtered by
      the current manipulation and a click on the other kind moved
      nothing here while the drawing highlighted it anyway.
    """
    for index in range(self.class_combo.count()):
      data = self.class_combo.itemData(index)
      if data and data == (target, label):
        self.class_combo.setCurrentIndex(index)
        return

  def _on_grabbed(self, key: str):
    """Take the manipulation from the handle somebody took hold of.

    Args:
      key: the manipulation that handle stands for.

    Returns:
      None. THE HANDLE IS THE CHOICE, so the chooser is set from it
      rather than the other way round -- which is what makes the two
      unable to disagree, and what lets somebody use this tab without
      touching the chooser at all.
    """
    for index in range(self.how_combo.count()):
      if self.how_combo.itemData(index) == key:
        if index != self.how_combo.currentIndex():
          self.how_combo.setCurrentIndex(index)
        return

  # ------------------------------------------------------------ drag

  def _drag_argument(self, key, frame, dx, dy, span):
    """What a drag on an edge means for the chosen manipulation.

    Args:
      key: the manipulation the `how` chooser names.
      frame: the grabbed edge's (mid_x, mid_y, along_x, along_y,
        length), in unit coordinates.
      dx: travel left to right, as a fraction of the unit.
      dy: travel bottom to top, as the same fraction.
      span: the unit's own width, to turn those fractions back into
        unit coordinates so they can be compared with the edge.

    Returns:
      (argument name, value), or (None, None) where this manipulation
      takes nothing a drag can supply.

    A DRAG SUPPLIES THE PARAMETER OF THE MANIPULATION ALREADY CHOSEN,
    rather than a gesture vocabulary of its own. The alternative
    considered was direction-decides -- perpendicular means zigzag,
    along means scale, around means rotate -- and it was refused
    because the `how` chooser ALREADY says which manipulation is
    meant, so a second, invisible way of saying it could only
    disagree with the first. It also has to be learnt, where this has
    only to be noticed.
    """
    _mx, _my, ax, ay, length = frame
    # The drag resolved into the edge's own axes: how far along it,
    # and how far across it.
    along = (dx * ax + dy * ay) * span
    across = (-dx * ay + dy * ax) * span
    if key == "zigzag_edge":
      # Amplitude relative to the edge's own length, so the same
      # gesture means the same shape on a long edge and a short one.
      # This one was ALREADY a position: the diamond sits off the
      # middle, and how far off it now is IS the amplitude.
      return "h", abs(across) / length
    # A HANDLE IS A POSITION, NOT A DISTANCE TRAVELLED.
    # (Maintainer's instruction, 2026-08-31: the interaction has to be
    # easy to use, easy to learn, and perceivable. This is the audit's
    # own recommendation of 2026-08-30, which it recorded and did not
    # build.)
    #
    # WHAT A DELTA COST. Turning travel into a parameter needs a LEVER,
    # and a lever is a gain factor nobody can see -- so it can only be
    # tuned by guessing, and it was wrong twice: half the edge's length
    # made a 34px drag invert the edge, and the full length still
    # turned a 35px drag into a scale factor of 0.28.
    #
    # THE END HANDLE STARTS AT THE END OF THE EDGE, half a length from
    # the middle along its axis. Where the pointer has taken it is
    # therefore (radius, angle) about that middle, and the two
    # parameters ARE those polar coordinates -- the scale factor is how
    # much further out it now sits, and the rotation is the angle it
    # now makes. Nothing to tune, and the edge follows the pointer
    # exactly, which is also what makes the handle a READOUT: it
    # already sits where the current value puts it.
    half = length / 2.0 or 1.0
    out = half + along          # the handle's distance along the axis
    if key == "rotate_edge":
      return "angle", math.degrees(math.atan2(across, out))
    if key == "scale_edge":
      return "sf", math.hypot(out, across) / half
    return None, None

  def _on_dragging(self, dx, dy):
    """Preview the chosen manipulation while the pointer moves.

    Args:
      dx: how far, left to right, as a fraction of the unit.
      dy: how far, bottom to top, as the same fraction.

    Returns:
      None. The preview is applied from the topology as it stood
      BEFORE the drag, never from the last frame, so one gesture is
      one manipulation rather than a hundred composed.

    IT USED TO BE A NUDGE AND NOTHING ELSE -- the method named
    `nudge_vertex` outright, so a vertex drag meant a nudge even with
    `push_vertex` chosen, and an edge drag meant nothing at all.
    """
    data = self.class_combo.currentData()
    key = self.how_combo.currentData()
    if self._topology is None or not data or not key:
      return
    spec = edits_module.MANIPULATIONS.get(key, {})
    # A drag can only mean the manipulation in force, and only where
    # that manipulation is about the kind of thing being dragged.
    # Clicking an edge while a vertex manipulation is chosen already
    # declines to retarget the edit; this declines to preview one.
    if spec.get("target") != data[0]:
      return
    args = dict(self._arguments())
    if data[0] == "vertex":
      if key == "push_vertex":
        # ALONG THE RAIL AND NOTHING ELSE. `dx` and `dy` arrive as
        # fractions of the unit, so projecting them onto the push
        # direction gives the push distance in the same fraction the
        # record keeps -- one unit of travel along the rail is one unit
        # of push, with no gain factor in between. Travel ACROSS the
        # rail is discarded, which is what a one-dimensional control
        # means and what the drawn rail promises.
        way = self.view.push_direction()
        if way is None:
          return
        # The rail is in WIDGET coordinates, where y grows downward,
        # and the drag arrives in unit terms where y grows up.
        # HELD INSIDE THE BOX, as the edge branch already was. Both
        # vertex branches assigned the drag straight into `args` while
        # the edge branch passed through `_within_the_box`, so a drag
        # past the control's own range recorded a number the box would
        # not show: measured 2026-09-01 on archimedean 4.8.8, a drag
        # of 2.0 left the record holding 2.0 beside a box reading 1.0,
        # and the RECORD is what travels to the file and replays. It
        # does not reproduce on laves 3.3.4.3.4, where the library
        # refuses a nudge that large before anything is recorded --
        # which is why the guard for this names its design.
        args["push_d"] = self._within_the_box(
          "push_d", float(dx * way[0] - dy * way[1]))
      elif key == "nudge_vertex":
        args["dx"] = self._within_the_box("dx", float(dx))
        args["dy"] = self._within_the_box("dy", float(dy))
      else:
        return
    else:
      frame = self.view.grabbed_edge()
      if frame is None:
        return
      name, value = self._drag_argument(
        key, frame, dx, dy, self.view.unit_span())
      if name is None:
        return
      args[name] = self._within_the_box(name, value)
    self._drag_from = dict(args)
    try:
      # THROUGH THE SAME COERCION THE COMMIT USES. Every parameter box
      # is a QDoubleSpinBox, so `n` and `smoothness` arrive as floats
      # and `zigzag_edge` raises "'float' object cannot be interpreted
      # as an integer" -- which `apply()` has always avoided through
      # `_WHOLE` and this path did not. Measured 2026-08-30: rotate and
      # scale previewed while zigzag drew nothing, silently, because
      # the raise is swallowed here.
      # FRACTIONS IN THE RECORD, MAP UNITS AT THE LIBRARY -- and this
      # is the SECOND place that conversion has to happen, which the
      # ruling of 2026-08-31 said happened at "the one place the unit
      # is known". It did not: `in_map_units` had exactly one caller,
      # in `apply`, so the drag PREVIEW handed the library a fraction
      # where the commit hands it a distance. Measured 2026-09-01 on
      # laves 3.3.4.3.4, one tenth of the unit: the commit moves the
      # ground 70.71 map units and the preview moved 0.10 -- the span,
      # 707.1x -- so a person dragging a vertex saw nothing happen at
      # all and then watched the design jump when they let go, which
      # is the complaint rulings 1 and 2 were written to answer.
      #
      # `_drag_from` above keeps the FRACTIONS, deliberately: the
      # record is what a person set and what travels to the file, and
      # only the library call is in map units.
      moved = self._topology.transform_geometry(
        True, True, data[1], key,
        **edits_module.in_map_units(
          edits_module.whole_where_needed(args),
          getattr(self._topology, "tileable", None)))
    except Exception:                                 # noqa: BLE001
      # AND A PREVIEW THAT FAILED COMMITS NOTHING. `_drag_from` is what
      # the drop records, so leaving it set would let a gesture that
      # drew nothing still add an edit -- the user would be shown one
      # thing and given another.
      self._drag_from = None
      return
    self.view.show_preview(moved)
    # AND THE NUMBER BOXES FOLLOW, so a drag is a way of typing rather
    # than a second, separate control: drag roughly, then read what it
    # chose and correct it by hand.
    self._show_arguments(args)

  def _within_the_box(self, name, value):
    """Clamp a dragged value to what its own control accepts.

    Args:
      name: the argument's name, as `MANIPULATIONS` spells it.
      value: what the drag worked out.

    Returns:
      The value, held inside the spin box's own range -- which is the
      range the library's parameter is documented at. A drag can reach
      any number; the control is what says which of them are meanings.
    """
    for _label, box in self._argument_rows:
      if box.property("argument") == name:
        return max(box.minimum(), min(box.maximum(), float(value)))
    return float(value)

  def _show_arguments(self, args):
    """Move the parameter boxes to what a drag worked out.

    Args:
      args: the argument mapping the preview was built from.

    Returns:
      None. The boxes carry no `valueChanged` connection, so setting
      them starts nothing -- they are read when Apply is pressed.
    """
    for _label, box in self._argument_rows:
      name = box.property("argument")
      if name in args:
        box.setValue(float(args[name]))

  def _on_dropped(self):
    """Commit the drag as an edit, or put the view back."""
    self.view.show_preview(None)
    if self._drag_from is None:
      return
    args = self._drag_from
    self._drag_from = None
    data = self.class_combo.currentData()
    key = self.how_combo.currentData()
    if not data or not key:
      return
    # A PRESS THAT WENT NOWHERE IS A CLICK, and a click chooses a class
    # rather than editing anything. The test is on what the drag
    # actually asked for, per manipulation, because "nothing moved"
    # is a different number for an angle than for a fraction.
    if not self._drag_moved(key, args):
      return
    self._record({"classes": data[1], "how": key, "args": args})

  def _drag_moved(self, key, args) -> bool:
    """Did this drag ask for anything?

    Args:
      key: the manipulation.
      args: what the drag worked out.

    Returns:
      True where the gesture asked for a real change. Each
      manipulation has its own idea of nothing: zero travel for a
      nudge, zero degrees for a rotation, and a factor of ONE for a
      scale -- which is why this is not one comparison against zero.
    """
    if key == "nudge_vertex":
      return abs(args.get("dx", 0.0)) > 1e-4 or abs(args.get("dy", 0.0)) > 1e-4
    if key == "zigzag_edge":
      return abs(args.get("h", 0.0)) > 0.01
    if key == "rotate_edge":
      return abs(args.get("angle", 0.0)) > 0.5
    if key == "scale_edge":
      # ONE PER CENT, not a thousandth. Measured 2026-08-30: a 34px
      # drag mostly ACROSS an edge still resolves to a little travel
      # ALONG it, and at a thousandth that committed a scale of 1.003
      # -- an edit nobody asked for, from what was meant as a click to
      # select the class. Each threshold is the smallest change of its
      # own parameter somebody could have meant.
      return abs(args.get("sf", 1.0) - 1.0) > 0.01
    return False

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
    """Redraw the list of changes, oldest first, with their marks.

    EACH ROW SAYS WHETHER THE DESIGN STILL CARRIED A TOPOLOGY once that
    change had been made, which is what tells somebody how far back
    they would have to roll to get one that does. (Maintainer's ask,
    2026-08-31.) The mark is deliberately quiet -- a suffix rather than
    a colour, since the drawing is where colour has work to do -- and
    it is ABSENT rather than guessed where no mark has arrived yet,
    because a row silently claiming to be sound is worse than a row
    that says nothing.
    """
    self.edit_list.clear()
    for index, edit in enumerate(self._edits):
      spec = edits_module.MANIPULATIONS.get(edit.get("how"), {})
      args = ", ".join(f"{k} {v:g}" for k, v in
                       sorted((edit.get("args") or {}).items()))
      mark = self._marks[index] if index < len(self._marks) else None
      if mark is None:
        suffix = ""
      elif not mark.get("applied"):
        suffix = "  — not applied"
      elif mark.get("sound"):
        suffix = ""
      else:
        suffix = "  — from here the tiles no longer meet"
      self.edit_list.addItem(
        f"{spec.get('label', edit.get('how'))} on {edit.get('classes')}"
        + (f" ({args})" if args else "") + suffix)
    self.undo_button.setEnabled(bool(self._edits))
    self.clear_button.setEnabled(bool(self._edits))

  def set_marks(self, marks):
    """Say, per edit, whether the design still had a topology after it.

    Args:
      marks: one entry per edit in `edits()`, oldest first, as
        `topology_edits.apply` returns them. An empty list clears the
        annotations rather than leaving stale ones, since a mark that
        outlives the replay it came from describes another design.

    Returns:
      None; the change list is redrawn.
    """
    self._marks = list(marks or [])
    self._refresh_list()

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
