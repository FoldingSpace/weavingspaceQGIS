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
from qgis.PyQt.QtGui import (
  QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF)
from qgis.PyQt.QtWidgets import (
  QAbstractItemView,
  QCheckBox,
  QComboBox,
  QGridLayout,
  QGroupBox,
  QHBoxLayout,
  QLabel,
  QListWidget,
  QListWidgetItem,
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
  # The eighth, added 2026-09-01: the symmetries the design already
  # knows about. OFF by default like the dual, because it answers a
  # question somebody has to have asked.
  ("symmetries", "Symmetries", False),
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
# THE SYMMETRIES ARE STRUCTURE RATHER THAN CONTENT, so they are drawn
# in one restrained colour: a rotation centre and a mirror line say
# the same kind of thing about the design and should read as one
# layer, not as two more things competing with the tiles.
_SYMMETRY_INK = "#6a1b9a"
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
# A MOVE HELD AT ITS LIMIT, drawn amber: the glyph and the preview
# stop where the parameter does, so a person dragging past the max
# sees it stop rather than imagining more will happen (2026-09-06).
_CLAMPED_INK = "#f9a825"

# WHAT A DRAG HELD AT ITS LIMIT SAYS, per manipulation. The value stops
# following the pointer where the next step could not be laid out, and
# the sentence has to name the move somebody is making: one sentence
# for all of them told a person dragging a rotate that "a deeper wave"
# ran beyond its neighbours. Keyed by the manipulation, with None as
# the fallback for one that gains a handle later and no sentence yet.
_HELD_SENTENCE = {
  "zigzag_edge": ("A deeper wave than this runs beyond the edges next "
                  "to it. Let go of the click to draw the wave as shown."),
  "rotate_edge": ("Turning this edge further would run it past the edges "
                  "beside it. Let go of the click to draw the turn as "
                  "shown."),
  "scale_edge": ("Stretching this edge further would run it past the "
                 "edges beside it. Let go of the click to draw the "
                 "stretch as shown."),
  None: ("This is as far as the design allows. Let go of the click to "
         "draw the move as shown."),
}

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
  # AND ALL OF THAT IS HISTORY AS OF 2026-09-05, kept because it is the
  # argument the rulings had to beat. The offsets above bought
  # separation from a FIRST-WINS hit test, and the price was the
  # zigzag's readout standing 60px off its own edge. `_handle_at` asks
  # which handle is NEAREST now, so an overlap is tight rather than
  # fatal, and the zigzag is placed where its position MEANS
  # something: "peak" is not an offset at all but a computed point,
  # `length / (2n)` along and `h` of the length out. Its entry keeps
  # the tuple's shape so nothing else has to know.
  ("zigzag_edge", "peak", 0, "diamond"),
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
# HOW CLOSE THE ZIGZAG'S HANDLE MAY COME TO A VERTEX. Handles are tested
# before vertices, so a handle on a vertex makes that vertex unclickable
# -- the measured reason the far-side offset was refused on 2026-08-31.
# Sized as the reach plus a seat's half-width, so the two never overlap.
# ON AN EDGE TOO SHORT FOR ITS SEATS THE POSITION IS NO LONGER AN EXACT
# READOUT, and that is said out loud rather than left to be discovered:
# `zigzag_readout_is_exact` answers it. (Ruling 4 of 2026-09-05.)
_CLEAR_OF_VERTEX = 15.0
# WHERE ALONG THE EDGE THE COUNT'S TWO ENDS SIT, as fractions of the
# edge from its start: the floor nearest the start, the ceiling toward
# the far end, and the even counts between them spread evenly. THE
# COUNT INTERPOLATES (maintainer's ruling, 2026-09-06): the handle used
# to sit on the wave's first peak, `length / (2n)` along, so its stops
# crowded toward the start as the count rose -- from four the next lay
# 0.042 and 0.021 of the edge away against a deadband of 0.10, and four
# and six could be typed but never dragged to. Spread evenly the stops
# are 0.117 of the edge apart, every count is one drag away, and the
# readout is exact wherever the edge has room for the seats. The ghost
# still crests at the library's own pitch, so the drawing is honest
# about the wave while the handle reads the count. TWO SITS AT A
# QUARTER, which is the first crest of a two-count wave, so the default
# handle is where it always was; and EIGHT STOPS AT 0.60, since the
# end handles stand at the edge's end and two handles closer than
# twice the reach make one unclickable (M-29): a first form seated the
# ends at 0.15 and 0.85 and rc17's second build measured the zigzag
# handle 19.1px from the scale handle inside a 13px reach at the
# window's floor. At 0.60 on the floor's 69px edge it is 28.9px clear.
_COUNT_SEATS = (0.25, 0.60)
# HOW FAR ALONG AN EDGE A DRAG MUST TRAVEL BEFORE IT MOVES THE COUNT,
# as a fraction of that edge's own length. A gesture aimed ACROSS an
# edge still resolves to a little travel ALONG it -- `scale_edge` was
# measured on 2026-08-30 committing a scale of 1.003 from what was
# meant as a click -- and the count is the coarsest parameter here, so
# an accidental step is the most expensive. SIZED FROM THE GLYPH: a
# tenth of the edge is just under one 12px seat on the 94px edges
# measured on 2026-09-05, so a gesture that never leaves the handle's
# own drawn shape cannot change the count. (Ruling 2 of that day.)
_COUNT_DEADBAND = 0.10
# The count's declared range, mirrored here because the drag clamps to
# it before `_within_the_box` ever sees the value -- and a drag that
# ran past the box's range once recorded a number the box would not
# show (archimedean 4.8.8, 2026-09-01).
_COUNT_FLOOR, _COUNT_CEILING = 2, 8
# THE COUNT IS EVEN. (Maintainer's decision, 2026-09-05, grilled.) The
# library's own `zigzag_edge` says it "will only work correctly if n
# is even", and the tab audit measured it: on the default design
# class a was sound at every count while class b opened a gap of
# 0.63%, 0.40% and 0.35% at n=1, 3 and 5 and none at 2 and 4. A box
# offering a value the library documents as unsupported offers
# something that works by the luck of the geometry, so the drag snaps
# to even counts, the box steps by two, and a typed odd count is
# settled to the nearest even one when editing finishes. A request for
# odd counts belongs upstream, beside the existing notes.
_COUNT_STEP = 2


class CrestSpinBox(TrimmedSpinBox):
  """The Amplitude box: shows the crest's distance, holds the library's `h`.

  The library's `h` is peak to peak, so a typed 0.4 draws a crest 0.2
  of the edge out -- and since round eight the handle, the ghost and
  the map agree about that, leaving the box the one reader of `h` a
  person meets. (Maintainer's ruling, 2026-09-06, the third of three:
  the box converts and the record keeps `h`.) QT HOLDS CREST UNITS
  and every Python reader gets `h`: the face, the arrows, the typed
  text and Qt's own validation all work in the number a person sees,
  while `value`, `setValue`, `minimum`, `maximum`, `setRange` and
  `setSingleStep` convert by `_CREST_OF_H`, so the record, the drag,
  the memory, every test that drives the box and every saved file
  keep the library's units. The first form converted the TEXT alone
  and left Qt's range in `h`, and Qt then judged a typed floor of
  0.005 as below 0.01 and fixed it up to twice itself (C-337).
  `valueChanged` carries Qt's crest value; the tab's one connection
  ignores the payload and reads `value()`.
  """

  def value(self):
    """The held amplitude as the library's `h`, peak to peak."""
    return super().value() / _CREST_OF_H

  def setValue(self, amplitude):                        # noqa: N802 (Qt API)
    """Hold an amplitude given as `h`.

    Args:
      amplitude: peak to peak, the library's own parameter.
    """
    super().setValue(float(amplitude) * _CREST_OF_H)

  def minimum(self):
    """The floor, as `h`."""
    return super().minimum() / _CREST_OF_H

  def maximum(self):
    """The ceiling, as `h`."""
    return super().maximum() / _CREST_OF_H

  def setRange(self, low, high):                        # noqa: N802 (Qt API)
    """Set the range given as `h`.

    Args:
      low: the floor, peak to peak.
      high: the ceiling, peak to peak.
    """
    super().setRange(float(low) * _CREST_OF_H, float(high) * _CREST_OF_H)

  def singleStep(self):                                 # noqa: N802 (Qt API)
    """One arrow press, as `h`."""
    return super().singleStep() / _CREST_OF_H

  def setSingleStep(self, step):                        # noqa: N802 (Qt API)
    """Set what one arrow press moves, given as `h`.

    Args:
      step: peak to peak, as the manipulation table spells it.
    """
    super().setSingleStep(float(step) * _CREST_OF_H)


def _count_seat(count) -> float:
  """Where along an edge the zigzag handle sits for a count.

  Args:
    count: the zigzag count, clamped to the declared range.

  Returns:
    The fraction of the edge, from its start, at which that count's
    seat lies: the floor at `_COUNT_SEATS[0]`, the ceiling at
    `_COUNT_SEATS[1]`, and the counts between spread evenly. ONE OWNER
    with `_count_at` below, so the handle and the drag that moves it
    cannot disagree about where a count is.
  """
  near, far = _COUNT_SEATS
  held = min(float(_COUNT_CEILING), max(float(_COUNT_FLOOR), float(count)))
  t = (held - float(_COUNT_FLOOR)) / float(_COUNT_CEILING - _COUNT_FLOOR)
  return near + t * (far - near)


def _count_at(fraction) -> int:
  """The even count whose seat is nearest a place along the edge.

  Args:
    fraction: a position along the edge as a fraction of its length
      from its start; beyond either seat it reads as that seat.

  Returns:
    The nearest even count in the declared range, the inverse of
    `_count_seat`.
  """
  near, far = _COUNT_SEATS
  t = min(1.0, max(0.0, (float(fraction) - near) / (far - near)))
  return _even_count(float(_COUNT_FLOOR) + t * (_COUNT_CEILING - _COUNT_FLOOR))
# A CLICK ON THE ZIGZAG HANDLE THAT SLIPS A PIXEL IS STILL A CLICK.
# (Maintainer's decision, 2026-09-05, grilled.) The amplitude's click
# threshold used to be 0.01 of the edge's length -- the box's floor --
# which on the 94px and 69px edges the default design draws at the
# window's floor is 0.9px and 0.7px: not where "I meant that" sits but
# where "the pointer moved at all" sits, so a click on the handle that
# slipped one pixel recorded a wave nobody could see and paid for a
# rebuild of the topology. SIZED FROM THE GLYPH, as the count's
# deadband is: half a 12px seat, so a gesture that never leaves the
# handle's own drawn shape cannot record an amplitude, and past it the
# amplitude is where the handle sits, as before. Typing in the box is
# unaffected, since this is asked only of a drag.
_AMPLITUDE_DEADBAND_PX = 6.0

# The one sentence the tab and the dialog both say when the dual button
# is pressed on a map that is already a dual's.

# THE LIBRARY'S `h` IS PEAK TO PEAK. `zigzag_between_points` scales its
# sine by `h * r / 2`, so the wave crests half of `h` times the edge's
# length out from the edge on either side -- and the handle, the
# ghost and the drag's inverse all stood at the whole of `h` until
# 2026-09-06, showing a wave 2.1 times deeper than the one the map got
# (found by the specification hunt of round eight; driven and measured
# on the default design: handle at 0.400 of the edge, crest at 0.190).
# One constant, four readers, so the picture and the map cannot come
# apart again by one site forgetting. The default smoothness samples
# the sine short of its peak by about 5%, which is left to the map.
_CREST_OF_H = 0.5

# HOW MANY PROBES THE DROP SPENDS closing the gap between the value a
# drag held and the one the pointer reached. Each halves what is left
# and costs about 161 ms -- the same transform the preview performs
# every frame -- so three is about half a second at the end of a
# gesture and leaves at most an eighth of the shortfall. The full
# bisection is eight steps and 1.4 s, which is why it is not run at
# the press. (Maintainer's ruling, 2026-09-07.)
_REFINING_STEPS = 3


def _in_the_units_the_controls_show(edit):
  """An edit's arguments as the tab displays them, not as it stores them.

  Args:
    edit: one entry of the change list's record.

  Returns:
    A copy of its `args`, with the zigzag's `h` converted to the crest
    distance the Amplitude box shows. The record itself is untouched:
    it holds the library's `h` so that nothing saved moves (C-337).

  WHY IT IS NEEDED. `h` is the wave's PEAK-TO-PEAK width and the crest
  sits half of it out from the edge, so `_CREST_OF_H` converts at the
  handle, the ghost, the drag's inverse, the Amplitude box and the
  clamp's sentence -- five readouts of one quantity. The change list
  was a sixth and printed the raw record, so a person who typed 0.25
  read `h 0.5` in their own list of changes, and a clamped edit could
  put `h 1` on the same screen as "drawn at an amplitude of 0.488
  rather than 0.5". (Found 2026-09-07; the KEYS are still the
  library's names throughout this list, which is a display question
  nobody has put to the maintainer.)
  """
  args = dict(edit.get("args") or {})
  if edit.get("how") == "zigzag_edge" and "h" in args:
    try:
      args["h"] = float(args["h"]) * _CREST_OF_H
    except (TypeError, ValueError):
      pass
  return args


def _push_for_travel(travel, gain):
  """The `push_d` that moves the ground as far as the pointer went.

  Args:
    travel: how far the gesture travelled along the rail, as a
      fraction of the unit's own span.
    gain: how far the ground moves for `push_d` of one at this vertex,
      from `TopologyView.push_gain`, or None where it cannot be asked.

  Returns:
    The value to record, in the library's own `push_d`.

  WHY THERE IS A CONVERSION AT ALL. `push_vertex` multiplies `push_d`
  by the SUM OF THE UNIT VECTORS from each neighbour to the vertex,
  whose length is a property of that vertex rather than of anything a
  person set -- 0.4142 on `archimedean 4.8.8` against a nudge's 1.0,
  measured 2026-09-07. So a rail drag of sixty pixels moved the vertex
  twenty-five, and the tab's comment claiming "one unit of travel
  along the rail is one unit of push, with no gain factor in between"
  was describing what it intended rather than what it did.

  THE MAINTAINER'S RULING (2026-09-07, by grilling): `push_d` IS A
  DISTANCE, so the vertex follows the pointer and the record keeps the
  library's parameter -- the same shape as the Amplitude box, which
  shows the crest and holds `h`. A gain factor nobody can see is
  exactly what this tab rejected twice already when the end handle was
  tuned by guessing.
  """
  if not gain:
    return float(travel)
  return float(travel) / float(gain)


def _as_the_controls_name_them(edit):
  """An edit's arguments, named and ordered as its own boxes are.

  Args:
    edit: one entry of the change list's record.

  Returns:
    A list of `(label, value)` pairs -- "Amplitude" rather than `h`,
    "Zigzags" rather than `n` -- in the order the manipulation
    declares them, which is the order the boxes appear in. An argument
    the manipulation does not declare keeps its own key and goes last,
    so a record written before a rule changed still reads.

  WHY THE LABELS RATHER THAN THE RECORD'S KEYS. `MANIPULATIONS`
  already carries the label each box shows, and the row's own verb
  comes from that same record -- "Zigzag edge" is `label`. The keys
  are the LIBRARY's parameter names, which nobody using the plugin has
  met; and since the amplitude is converted on its way here, a row
  printing `h` beside a number the record does not hold would look
  like the record without being it. (Maintainer's ruling, 2026-09-07.)
  """
  args = _in_the_units_the_controls_show(edit)
  spec = edits_module.MANIPULATIONS.get(edit.get("how"), {})
  named = []
  for declared in spec.get("args", ()):
    key, label = declared[0], declared[1]
    if key in args:
      named.append((label, args.pop(key)))
  named.extend((key, args[key]) for key in sorted(args))
  return named


def _even_count(value) -> int:
  """The even count nearest a number, inside the count's range.

  Args:
    value: a count a drag or a keyboard produced, whole or not.

  Returns:
    An even integer between `_COUNT_FLOOR` and `_COUNT_CEILING`. An odd
    count is exactly halfway between two even ones, and Python's
    `round` settles halves to the even NUMBER -- 2.5 to 2 and 1.5 to 2
    -- which sent a typed 5 to 4 and a typed 3 to 4 in the first
    draft; halves settle UP here, so 3 becomes 4 and 5 becomes 6, and
    the same rule serves the drag's snap and the typed count.
  """
  even = int(math.floor(float(value) / _COUNT_STEP + 0.5)) * _COUNT_STEP
  return max(_COUNT_FLOOR, min(_COUNT_CEILING, even))


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

  # (target, label, adding) since 2026-09-01: `adding` is True where
  # the click was modified, meaning add this class to the selection
  # rather than replace it. The panel owns the selection; the view
  # reports what was clicked and how.
  chose = pyqtSignal(str, str, bool)
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
    # WHAT A DRAG IN PROGRESS IS: {clamped, failed, reason, key}, or
    # None at rest. The preview shows the RESULT and this says whether
    # that result is valid, held at a limit, or a design that cannot
    # be tiled -- so the drawing never lets a person imagine a move
    # will be allowed when it will not (maintainer's principle,
    # 2026-09-06). Ruling 5 of 2026-08-31 still governs the DROP:
    # validity is shown, not enforced, so a failed move is drawn red
    # while the pointer is down and still recorded-and-marked if let
    # go, not refused.
    self._drag_status = None
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
    # WHAT THE ZIGZAG'S HANDLE HAS TO SAY, as (count, amplitude), or
    # None where the chosen manipulation is not a zigzag. The view
    # cannot ask -- the parameter boxes belong to the panel -- so the
    # panel PUSHES this whenever a box moves or a drag previews, which
    # keeps ONE OWNER for the question exactly as `_arguments` is the
    # one owner of what the boxes say. (Rulings 1 and 3 of 2026-09-05.)
    self._zigzag_readout = None
    # WHERE THE CHOSEN THING SAT AT THE LAST REBUILD, so the handles
    # come back to the place a person clicked rather than to whichever
    # member of the class sorts first. None whenever there is nothing
    # to come back to.
    self._chosen_anchor = None
    # A handle under the pointer, and the one being dragged.
    self._hover_handle = ""
    self._held_handle = ""
    self._press = None
    # WHERE THE GRAB AND THE RELEASE LANDED, IN PIXELS, so the drop can
    # ask how far the pointer travelled without re-deriving it from the
    # unit-space press. A drag that travelled a real distance is a
    # gesture the drop must commit whatever the number worked out to --
    # the whole of 'if you can draw it, you can run it' (2026-09-06).
    self._press_px = None
    self._release_px = None
    # The edge a drag took hold of, in UNIT coordinates:
    # (mid_x, mid_y, along_x, along_y, length). Kept here because the
    # view is what did the hit test and knows which concrete edge was
    # grabbed, while the panel is what knows the manipulations -- so
    # the geometry crosses over and the meaning does not.
    self._press_edge = None
    # AND THE PUSH RAIL'S GAIN, frozen with it and for the same
    # reason: both are measured on the geometry as it stood at the
    # press, never on the preview the gesture is moving.
    self._press_gain = None
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
    self._drag_status = None
    # THE HELD OBJECT BELONGS TO THE OLD TOPOLOGY and every rebuild
    # makes new ones, so keeping it would draw handles on geometry
    # nothing else refers to -- and `is` comparisons against it would
    # answer False for the edge that looks identical on screen. The
    # CLASS survives a rebuild; the object does not.
    # BUT WHERE IT SAT SURVIVES TOO, and that is the half this was
    # missing. A class has several members, and re-seating on the
    # FIRST of them moves the handles across the drawing: measured
    # 2026-09-02, a vertex clicked and then rebuilt under the pointer
    # put its handle 177 pixels from the click, so the press that
    # followed found nothing and the drag drew no preview at all. The
    # anchor is taken and cleared by `_settle_what_the_handles_sit_on`
    # at the point of use, so a person CHOOSING a class from the
    # chooser still lands on its first member, which is what choosing
    # a class means.
    self._chosen_anchor = self._where_a_thing_sits(self._chosen_thing)
    self._chosen_thing = None
    self._message = "" if topology is not None else (
      message or "This tiling has not had a topology calculated for it.")
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
    if topology is None:
      self._drag_status = None
    self.update()

  def set_drag_status(self, status):
    """Record what the drag in progress would do, for the paint.

    Args:
      status: a dict with `clamped`, `failed`, `reason` and `key`, or
        None at rest. The preview draws its outline in the state's
        colour and the active glyph follows, so valid, clamped at a
        limit, and a design that cannot be tiled are told apart as
        the gesture goes.
    """
    self._drag_status = status
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
    self._settle_what_the_handles_sit_on()
    self.update()

  def _where_a_thing_sits(self, thing):
    """The unit-space point a vertex or an edge is anchored at.

    Args:
      thing: a Vertex or an Edge from the drawn topology, or None.

    Returns:
      (x, y) in unit coordinates -- a vertex's own point, or an edge's
      midpoint end to end -- and None where there is nothing to place
      or the geometry cannot be read. Used to put the handles back
      where they were after a rebuild replaces every object.
    """
    if thing is None:
      return None
    point = getattr(thing, "point", None)
    if point is not None:
      try:
        return (float(point.x), float(point.y))
      except Exception:                                 # noqa: BLE001
        return None
    frame = self._edge_frame(thing)
    return None if frame is None else (frame[0], frame[1])

  def _settle_what_the_handles_sit_on(self) -> None:
    """Move the handles onto the class that is now chosen.

    Returns:
      None. Leaves `_chosen_thing` alone where it is already a member
      of the chosen class, moves it to the first member otherwise, and
      clears it where the class has no member drawn.

    WHY IT EXISTS. `_chosen_thing` had ONE writer, in
    `mousePressEvent`, so choosing a class in the combo or the tick
    list moved the SELECTION -- which Apply, the drag preview and the
    drop all ask -- and left the handles where the last click had put
    them. Measured 2026-09-02: click `edge b`, choose `edge a` from
    the chooser, and the selection reads `('edge', 'a')` while all
    three handles stay on b, to the pixel.
    WHAT THAT COSTS is not merely a wrong-looking picture. A drag's
    parameter is a POLAR COORDINATE about the handle's own edge --
    the scale factor is how far out the end sits, the rotation is the
    angle it makes -- so grabbing a handle seated on b and having the
    edit recorded against a measures the number on the wrong edge.
    MEMBERSHIP IS ASKED THE WAY THE PAINT ASKS IT, `label in chosen`,
    because a selection may name several classes and "every edge"
    always does: its datum is the whole group.
    """
    target, chosen = self._chosen
    topology = self._drawn()
    if topology is None or not chosen or not target:
      self._chosen_thing = None
      return
    members = (topology.edges.values() if target == "edge"
               else topology.points.values())
    held = self._chosen_thing
    for thing in members:
      if getattr(thing, "label", None) in chosen:
        # THE ONE ALREADY IN HAND WINS, so a click that chose a
        # particular edge is not moved off it by the chooser being
        # synced to the class that click selected.
        if held is not None and held is thing:
          return
    # NEAREST THE PLACE THE HANDLES WERE, where a rebuild has just
    # left an anchor; the first member otherwise, which is what
    # choosing a class from the chooser means. Taken and cleared here,
    # at the point of use, like every other deferred intent in this
    # project -- an anchor left standing would drag a later, unrelated
    # choice back to an old position.
    anchor, self._chosen_anchor = self._chosen_anchor, None
    best, best_away = None, None
    for thing in members:
      if getattr(thing, "label", None) not in chosen:
        continue
      if anchor is None:
        self._chosen_thing = thing
        return
      sits = self._where_a_thing_sits(thing)
      away = None if sits is None else (
        (sits[0] - anchor[0]) ** 2 + (sits[1] - anchor[1]) ** 2)
      if best is None or (away is not None
                          and (best_away is None or away < best_away)):
        best, best_away = thing, away
    self._chosen_thing = best

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
    if self.gesture_in_progress() and self._bounds:
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
      # WHILE A DRAG IS IN PROGRESS THE OUTLINE CARRIES ITS STATE: red
      # and dotted where the move would leave a design that cannot be
      # tiled, amber where it is held at a limit, the ordinary line
      # where it is fine -- so what is drawn says whether it will be
      # allowed (2026-09-06).
      status = self._drag_status if self._preview is not None else None
      tile_pen = QPen(QColor(_TILE_LINE), 1)
      if status and status.get("failed"):
        tile_pen = QPen(QColor(_GAP_INK), 1.5)
        tile_pen.setStyle(Qt.PenStyle.DotLine)
      elif status and status.get("clamped"):
        tile_pen = QPen(QColor(_CLAMPED_INK), 1.5)
      painter.setPen(tile_pen)
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
      # LIGHTER NOW THAT IT COVERS THE WHOLE TEAR. (Maintainer's
      # ruling, 2026-09-07.) The hatch used to mark one cell's worth
      # of missing ground and now marks every torn piece in the patch
      # -- 21 pieces against 4 on the default design's per-edge rotate
      # -- so at full strength it would dominate a drawing that is
      # already carrying class labels, handles and a ghost. This
      # project has withdrawn a hatching once for confusing people,
      # and its own rule is that a heavy mark competes with the thing
      # being judged: the mark has to be findable, not loud.
      faint = QColor(_GAP_INK)
      faint.setAlpha(110)
      painter.setBrush(QBrush(faint, Qt.BrushStyle.BDiagPattern))
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

    # THE SYMMETRIES, under everything the person is aiming at and
    # over the tiles, because they explain the design rather than
    # being part of it. Drawn in the view's own painter from what the
    # Topology already holds: upstream's `plot_tiling_symmetries` goes
    # through matplotlib, which cannot run inside the signed QGIS
    # process on macOS -- this project's side tooling keeps matplotlib
    # in `.venv-reference` for exactly that reason.
    if self._shown["symmetries"]:
      self._draw_symmetries(painter, topology)

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
        # MEMBERSHIP, NOT EQUALITY, because a selection may name
        # several classes -- and "every edge" always could: its datum
        # is the whole group, so a string like "ab" was compared for
        # equality against single labels and lit nothing at all.
        kin = (not held and target == "edge" and chosen
               and edge.label in chosen)
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
      # NO SEAT FOR AN UNLABELLED CORNER: the edge's own path already
      # passes through it, `_nearest` cannot select it, and a dot on
      # every corner of a smoothed zigzag is two hundred beads that
      # read as vertices nothing can take hold of.
      if not (getattr(vertex, "label", None) or ""):
        continue
      held = (target == "vertex" and vertex is self._chosen_thing)
      kin = (not held and target == "vertex" and chosen
             and vertex.label in chosen)
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
    # and they sit on the geometry they belong to.
    # AND THEY ARE DRAWN DURING A DRAG TOO, ANCHORED TO THE FRAME THE
    # GESTURE BEGAN IN. (Maintainer's ruling, 2026-09-07.) They used to
    # be left out whenever a preview stood, on the reading that a
    # preview moves the geometry so the handles would describe a shape
    # no longer under them -- which is true, and left the drag with no
    # cue at all beyond the tile outlines. The frame they take instead
    # is `grabbed_edge()`, captured at the press and held for the whole
    # gesture, which is ALREADY what the drag's own arithmetic is
    # measured against: the value is read as a polar coordinate about
    # that frozen midpoint, so anchoring the picture to anything else
    # would draw one thing and record another.
    # NOT THE PREVIEW'S OWN GEOMETRY, deliberately. Re-deriving a
    # paint-time anchor from what the gesture is changing is the
    # feedback loop this tab has already paid for: `_fit` did it, and a
    # nudge held perfectly still climbed 0.104 to 0.356 over six
    # repaints while the scale fell. The cost accepted here is that on
    # a large move the cue sits where the edge WAS rather than where
    # the preview has taken it.
    held = self._press_edge if self._preview is not None else None
    frame = held or (self._edge_frame(self._chosen_thing)
                     if self._chosen[0] == "edge" else None)
    self._draw_what_the_move_bears_on(painter, held)
    self._draw_the_zigzag_it_would_make(painter)
    for key, where, shape in self.handles():
      lit = (key in (self._hover_handle, self._held_handle))
      self._draw_handle(painter, key, where, frame, lit)
    self._say_what_the_drag_is_doing(painter)
    painter.end()

  def _say_what_the_drag_is_doing(self, painter):
    """Put the drag's own sentence at the foot of the drawing.

    Args:
      painter: the active QPainter.

    Returns:
      None; nothing is drawn where no gesture is being held or
      refused, which is the ordinary case.

    WHY IT IS PAINTED HERE RATHER THAN PUT IN A LABEL. (Maintainer's
    ruling, 2026-09-07, by grilling.) The sentences existed and
    reached nobody: `_status_of_a_drag` composes them into `reason`
    and the paint read only `failed` and `clamped`, so `_HELD_SENTENCE`,
    the refusal and both coverage sentences were write-only. Three
    homes were possible and this is the one chosen: the panel's `note`
    already means two things and the suite's own settle helper reads
    text there as an answer having ARRIVED, so a third meaning is the
    one-store-two-meanings fault this tab has paid for once; a label
    of its own is a second place to look during a gesture, and people
    do not look away mid-drag. Painted in the drawing it is read where
    the eye already is, and it DIES WITH THE PICTURE -- nothing has to
    remember to clear it, which is the half of this that keeps going
    wrong elsewhere.

    IT TAKES THE COLOUR THE OUTLINES TAKE, so the words and the ink
    say the same thing: amber where a value is held at its limit, red
    where the previewed design cannot be tiled.
    """
    status = self._drag_status if self._preview is not None else None
    if not status:
      return
    saying = (status.get("reason") or "").strip()
    if not saying:
      return
    ink = QColor(_GAP_INK if status.get("failed") else _CLAMPED_INK)
    painter.setPen(QPen(ink))
    font = painter.font()
    font.setPointSizeF(max(8.0, font.pointSizeF() - 1.0))
    painter.setFont(font)
    # ACROSS THE FOOT OF THE WIDGET, wrapped, over the ground rather
    # than over the unit: the drawing is 420px at its floor and a
    # sentence across the middle of it would cover the thing being
    # judged.
    room = QRectF(8.0, self.height() - 40.0,
                  max(40.0, self.width() - 16.0), 34.0)
    painter.drawText(room, int(Qt.AlignmentFlag.AlignLeft
                               | Qt.AlignmentFlag.AlignBottom
                               | Qt.TextFlag.TextWordWrap), saying)

  def _draw_what_the_move_bears_on(self, painter, frame):
    """Draw the thing a drag turns, stretches or rides on.

    Args:
      painter: the active QPainter.
      frame: the frozen `(mid_x, mid_y, along_x, along_y, length)` of
        the edge the gesture took hold of, or None when no drag is in
        progress -- in which case nothing is drawn, since a cue with no
        gesture to explain is one more mark on a crowded drawing.

    Returns:
      None.

    WHAT THIS IS FOR. (Maintainer's principle, 2026-09-06: a
    manipulation shows a subtle cue of the entity or symmetry it bears
    on -- the pivot, the push rail, the edge.) A rotate turns about the
    edge's own midpoint and a scale holds that midpoint fixed, so the
    pivot is the one point neither of them moves and is exactly what a
    person needs to see to predict either; a zigzag rides on the edge,
    so the baseline is the cue. The push rail already existed and is
    drawn with its own handle.

    ANCHORED TO THE FROZEN FRAME, like everything else about a drag
    (maintainer's ruling, 2026-09-07). The pivot is meaningless if it
    moves with the geometry the gesture is changing -- it would stop
    being the point that stays still, which is the whole of what it
    says.

    DRAWN FAINT AND DASHED, because it explains the gesture rather than
    being part of it: this drawing already carries class labels, the
    handles, the ghost and now the hatch, and the tab has been reported
    unusable once for having too much on it.
    """
    if not frame:
      return
    mid_x, mid_y, along_x, along_y, length = frame
    key = self._held_handle
    if key not in ("rotate_edge", "scale_edge", "zigzag_edge"):
      return
    pivot = self._to_screen(mid_x, mid_y)
    ends = (self._to_screen(mid_x - along_x * length / 2.0,
                            mid_y - along_y * length / 2.0),
            self._to_screen(mid_x + along_x * length / 2.0,
                            mid_y + along_y * length / 2.0))
    ink = QColor(_HANDLE_INK)
    ink.setAlpha(120)
    pen = QPen(ink, 1.0)
    pen.setStyle(Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # THE EDGE AS IT WAS: the axis a scale stretches along and the
    # baseline a zigzag rides on, both of which are the same line.
    painter.drawLine(ends[0], ends[1])

    if key == "rotate_edge":
      # AND THE ANGLE, AS AN ARC ABOUT THE PIVOT, swept from where the
      # edge's end WAS to where the pointer has taken it. Read off the
      # two positions rather than off the value, so the arc cannot
      # disagree with the handle: both are polar coordinates about
      # this same frozen midpoint.
      if self._release_px is not None:
        import math
        radius = max(12.0, ((ends[1].x() - pivot.x()) ** 2
                            + (ends[1].y() - pivot.y()) ** 2) ** 0.5)
        was = math.atan2(ends[1].y() - pivot.y(), ends[1].x() - pivot.x())
        now = math.atan2(self._release_px.y() - pivot.y(),
                         self._release_px.x() - pivot.x())
        sweep = math.degrees(now - was)
        while sweep > 180.0:
          sweep -= 360.0
        while sweep < -180.0:
          sweep += 360.0
        box = QRectF(pivot.x() - radius, pivot.y() - radius,
                     radius * 2, radius * 2)
        # Qt measures in sixteenths of a degree, anticlockwise, from
        # three o'clock -- and the widget's y runs DOWN, so both the
        # start and the sweep are negated to read as they look.
        painter.drawArc(box, int(-math.degrees(was) * 16),
                        int(-sweep * 16))

    # THE PIVOT ITSELF, last so it sits above its own lines.
    painter.setPen(QPen(ink, 1.0))
    painter.setBrush(QBrush(ink))
    painter.drawEllipse(pivot, 2.5, 2.5)
    painter.setBrush(Qt.BrushStyle.NoBrush)

  def _draw_symmetries(self, painter, topology):
    """Draw the design's own symmetries: centres and mirror lines.

    Args:
      painter: the active QPainter.
      topology: the topology being drawn.

    Returns:
      None.

    A ROTATION CENTRE IS DRAWN AS ITS OWN ORDER: a two-fold centre is
    a lens, a three-fold a triangle, a four-fold a square, a six-fold
    a hexagon. That is the crystallographic convention and it is also
    the rule this tab already follows for its handles -- a mark should
    be a picture of what it means rather than a legend somebody has to
    look up.

    A MIRROR IS A LINE ACROSS THE WHOLE DRAWING, because that is what
    it is: the reflection holds everywhere, not only where the tiles
    happen to be. It is dashed so it cannot be read as an edge.

    THE DISTINCT ONES ONLY. `square-colouring 5` records 96 matching
    transforms and `laves 3.3.4.3.4` records 24; drawn as recorded
    they pile several marks on one centre and say less than one mark
    does. `topology_edits.symmetries_to_draw` keeps the highest order
    per centre and one line per mirror.
    """
    found = edits_module.symmetries_to_draw(topology)
    if not found["rotations"] and not found["mirrors"]:
      return
    pen = QPen(QColor(_SYMMETRY_INK), 1)
    pen.setStyle(Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    reach = max(self.width(), self.height()) * 2
    for x, y, degrees in found["mirrors"]:
      middle = self._to_screen(x, y)
      angle = math.radians(degrees)
      along = QPointF(math.cos(angle) * reach, -math.sin(angle) * reach)
      painter.drawLine(QPointF(middle.x() - along.x(),
                               middle.y() - along.y()),
                       QPointF(middle.x() + along.x(),
                               middle.y() + along.y()))
    solid = QPen(QColor(_SYMMETRY_INK), 1)
    painter.setPen(solid)
    painter.setBrush(QBrush(QColor(_SYMMETRY_INK)))
    for x, y, order in found["rotations"]:
      middle = self._to_screen(x, y)
      radius = 5.0
      if order == 2:
        # A LENS, which is the two-fold mark: two arcs meeting at the
        # points, drawn here as a narrow diamond, since at five pixels
        # the two read the same and one path is cheaper.
        painter.drawPolygon(QPolygonF([
          QPointF(middle.x(), middle.y() - radius),
          QPointF(middle.x() + radius * 0.55, middle.y()),
          QPointF(middle.x(), middle.y() + radius),
          QPointF(middle.x() - radius * 0.55, middle.y())]))
        continue
      corners = []
      for step in range(order):
        turn = math.radians(90.0 + step * 360.0 / order)
        corners.append(QPointF(middle.x() + math.cos(turn) * radius,
                               middle.y() - math.sin(turn) * radius))
      painter.drawPolygon(QPolygonF(corners))

  def _draw_the_zigzag_it_would_make(self, painter):
    """Ghost the wave the current numbers would put on this edge.

    Args:
      painter: the active QPainter, or None to compute the wave
        without drawing it, which is how its geometry is asserted.

    Returns:
      The wave's points, or None where there is nothing to draw. The
      SECOND of them is the first peak, which is where the handle sits.
      Drawn only when an edge is chosen AND the chosen
      manipulation is the zigzag, which is when "what would this do"
      is the question somebody is actually asking. (Maintainer's
      decision, 2026-09-05.)

    WHY THE GLYPH COULD NOT CARRY THIS. The seat is 12px and its
    drawing radius about 9.5px, so eight oscillations inside it are a
    smudge and every amplitude above about a third saturates to the
    same picture -- it could show CHANGE but never VALUE. The edge is
    ~94px on the designs measured here, which is room enough for both.
    The glyph's own comment claimed it drew "at the amplitude it is
    about to make it in" and drew a fixed shape; that claim becomes
    true here instead, where there is space to keep it.

    IT PASSES THROUGH THE HANDLE, and that is a requirement rather than
    a nicety: the handle sits on the wave's FIRST PEAK by ruling 3, so
    a ghost whose first peak fell anywhere else would be one fact drawn
    twice in two places -- this project's commonest defect, wearing
    paint. `test_the_zigzag_ghost_passes_through_its_handle` holds it.

    IT IS COMPUTED HERE AND STORED NOWHERE, which is deliberate after
    this morning's sweep: a picture that is derived at paint time has
    no actor that clears it and therefore cannot be left describing a
    state that has moved on.

    AND IT IS THE WAVE'S SHAPE, NOT THE LIBRARY'S EXACT OUTPUT.
    `zigzag_edge` smooths through a spline of its own, so the landing
    draws a rounder line than this. Said plainly because a cue that
    quietly differs from the result is worse than none: what this
    answers is more-or-less, and the drag preview and the landing are
    what answer exactly.
    """
    if not self._zigzag_readout or len(self._zigzag_readout) < 3:
      return None
    count, height, chosen = self._zigzag_readout[:3]
    if not chosen:
      return None
    edge = self._chosen_edge_on_screen()
    if edge is None:
      return None
    start, finish, reach = edge
    count = max(1, int(round(count)))
    rise = float(height) * reach * _CREST_OF_H
    if rise < 0.5:
      return None               # nothing a person could see
    along = ((finish.x() - start.x()) / reach,
             (finish.y() - start.y()) / reach)
    # THE SAME SIDE AS THE HANDLE, which is the side the wave goes
    # (see `handles`): the screen's right of the edge.
    normal = (along[1], -along[0])

    # THE PEAKS, AT THE ODD MULTIPLES OF `length / (2n)`, which is
    # where the library's sine actually crests: `zigzag_between_points`
    # is a sine over the edge, so its EVEN multiples are the zero
    # CROSSINGS. Drawing a full-amplitude point at every multiple --
    # which this did until 2026-09-07 -- gives 2n-1 lobes at twice the
    # pitch, and at the default n=2 the trailing lobe bulges to the
    # wrong side of the edge entirely. Measured against the library at
    # h=0.4: the ghost drew (.25,+.2)(.50,-.2)(.75,+.2) where the map
    # gets (.25,+.2)(.50,0)(.75,-.2). There are `count` peaks, one per
    # zigzag, and the polyline crosses the baseline between them by
    # construction.
    points = [start]
    step = reach / (2.0 * count)
    for index in range(count):
      at = step * (2 * index + 1)
      side = 1 if index % 2 == 0 else -1
      points.append(QPointF(
        start.x() + along[0] * at + normal[0] * rise * side,
        start.y() + along[1] * at + normal[1] * rise * side))
    points.append(finish)

    if painter is None:
      return points
    ghost = QPen(QColor(_HANDLE_INK), 1.2)
    ghost.setStyle(Qt.PenStyle.DashLine)
    painter.setPen(ghost)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for first, second in zip(points, points[1:]):
      painter.drawLine(first, second)
    self._draw_what_the_two_axes_do(painter, points[1] if len(points) > 1
                                    else start, along, normal)
    return points

  def _draw_what_the_two_axes_do(self, painter, at, along, normal):
    """Four cues saying what dragging each way would do.

    Args:
      painter: the active QPainter, or None to compute without drawing.
      at: the handle's own place, which the four sit around.
      along: the edge's unit direction, in widget coordinates.
      normal: its perpendicular, likewise.

    Returns:
      The four (QPointF, count, height) the cues are drawn at, so a
      test can assert where they sit without reading pixels.

    EACH CUE IS A MINIATURE OF WHAT IT PRODUCES -- a deeper wave for
    further out, a tighter one for further along -- which is the
    maintainer's own standard that a handle's shape must make sense for
    what it does. A person reads "that way makes this" without being
    told, and without the arrow-plus-label vocabulary that has to be
    learnt.

    THEY ARE PAINTED AND NEVER CLICKED, which is what makes four of
    them affordable at all. (Maintainer's decision, 2026-09-05.) A
    clickable glyph needs 26px of clearance from its neighbour to be
    separately hittable, and the edges here measure ~94px on the
    packaged fixture and ~40px on hex-slice 6 -- so four more targets
    do not fit, and putting them off the edge would stop them belonging
    to it. As cues they compete for nothing and cost the same on any
    edge.

    THEY SIT BEYOND THE CATCH RADIUS, deliberately: something drawn
    inside `_HANDLE_REACH` of the seat looks like part of the control
    and invites a click that does nothing, which is worse than no cue.
    """
    out = _HANDLE_REACH + 7.0
    places = (
      # further out: deeper. Further in: shallower.
      (QPointF(at.x() + normal[0] * out, at.y() + normal[1] * out), 2, 3.4),
      (QPointF(at.x() - normal[0] * out, at.y() - normal[1] * out), 2, 1.2),
      # further along: a shorter wavelength, so more of them.
      (QPointF(at.x() + along[0] * out, at.y() + along[1] * out), 4, 2.2),
      (QPointF(at.x() - along[0] * out, at.y() - along[1] * out), 1, 2.2),
    )
    if painter is None:
      return places
    faint = QPen(QColor(_HANDLE_INK), 1.0)
    painter.setPen(faint)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for centre, count, height in places:
      span = 9.0
      step = span / (2.0 * count)
      marks = [QPointF(centre.x() - along[0] * span / 2.0,
                       centre.y() - along[1] * span / 2.0)]
      for index in range(2 * count - 1):
        side = 1 if index % 2 == 0 else -1
        reach_here = -span / 2.0 + step * (index + 1)
        marks.append(QPointF(
          centre.x() + along[0] * reach_here + normal[0] * height * side,
          centre.y() + along[1] * reach_here + normal[1] * height * side))
      marks.append(QPointF(centre.x() + along[0] * span / 2.0,
                           centre.y() + along[1] * span / 2.0))
      for first, second in zip(marks, marks[1:]):
        painter.drawLine(first, second)
    return places

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
      # A POINT WITH NO LABEL IS NOT A VERTEX ANYBODY CAN EDIT. A
      # zigzag replaces an edge's two ends with a curve of corners --
      # 207 of them on the default design after one zigzag at n=2,
      # against its 72 vertices -- and a corner belongs to no class:
      # clicking one put the selection at ("vertex", ""), the chooser
      # read "0 of 2 vertex classes", nothing was ticked, no handle
      # appeared and Apply did nothing in silence, which is this
      # plugin's own definition of a dead control (measured 2026-09-05,
      # driving the tab). The click falls through to the edge the
      # corner lies on, which is the thing a person aiming there can
      # actually move.
      if not (getattr(vertex, "label", None) or ""):
        continue
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

  def set_zigzag_readout(self, values):
    """Tell the view what the zigzag handle has to say.

    Args:
      values: (count, amplitude, chosen), or None. Amplitude is the
        fraction of the edge's own length that `zigzag_edge` takes as
        `h`, so the handle's offset is that fraction of the edge's
        SCREEN length and the same gesture means the same shape on any
        edge. `chosen` says whether the zigzag is the manipulation now
        selected: the HANDLE is drawn either way, because a handle is
        the choice of manipulation, while the ghost of the wave is
        drawn only when somebody is actually asking what a zigzag
        would do.

    Returns:
      None. Repaints where the value moved, because the handle's place
      has moved with it.
    """
    if values != self._zigzag_readout:
      self._zigzag_readout = values
      self.update()

  def _chosen_edge_on_screen(self):
    """The chosen edge as (start, finish, length) in widget pixels.

    Returns:
      A tuple, or None where nothing suitable is chosen or its
      geometry will not answer.
    """
    target, _label = self._chosen
    thing = self._chosen_thing
    if target != "edge" or thing is None:
      return None
    try:
      coords = list(thing.get_geometry().coords)
      start = self._to_screen(*coords[0])
      finish = self._to_screen(*coords[-1])
    except Exception:                                 # noqa: BLE001
      return None
    run, rise = finish.x() - start.x(), finish.y() - start.y()
    reach = (run * run + rise * rise) ** 0.5
    return None if reach <= 0 else (start, finish, reach)

  def chosen_edge_length_on_screen(self):
    """How long the chosen edge is drawn, in widget pixels.

    Returns:
      The length, or None where no edge is chosen or its geometry will
      not answer. Asked by the panel to size the zigzag's click
      threshold from the glyph rather than from the edge's fraction.
    """
    edge = self._chosen_edge_on_screen()
    return None if edge is None else edge[2]

  def zigzag_readout_is_exact(self) -> bool:
    """Whether the zigzag handle is where its count says it is.

    Returns:
      True where the count's seat sits clear of both vertices, so the
      along-position is a true readout of the count; False where the
      clamp has taken over and the handle has stopped moving as the
      count rises. The panel says so when this is False, because a
      readout that has quietly stopped being one is worse than none --
      it reads as a control that has stopped responding.
    """
    edge = self._chosen_edge_on_screen()
    if edge is None or not self._zigzag_readout:
      return True
    _start, _finish, reach = edge
    count = max(1, int(round(self._zigzag_readout[0])))
    wanted = _count_seat(count) * reach
    return _CLEAR_OF_VERTEX <= wanted <= reach - _CLEAR_OF_VERTEX

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
    # The perpendicular, in SCREEN terms, ON THE SIDE THE WAVE GOES.
    # The library's zigzag puts its first lobe on the LEFT of the edge
    # in unit space (y up), which the view's y-flip puts on the RIGHT
    # of the edge on screen: `(rise, -run)`. The other sign stood here
    # until 2026-09-06, so the handle and the ghost bulged one way and
    # every tile bulged the other, the two tiles sharing the edge
    # swapping the ground they covered (round eight, repairs17;
    # measured on the default design and hex-slice 6).
    start, finish = self._to_screen(*coords[0]), self._to_screen(*coords[-1])
    run, rise = finish.x() - start.x(), finish.y() - start.y()
    reach = (run * run + rise * rise) ** 0.5 or 1.0
    normal = (rise / reach, -run / reach)
    placed = []
    for key, at, out, shape in _EDGE_HANDLES:
      if at == "peak":
        # THE ZIGZAG'S HANDLE IS A READOUT, NOT A GRAB POINT. It sits
        # at the count's SEAT along the edge -- `_count_seat`, the even
        # counts spread evenly between two seats since 2026-09-06 -- and
        # `h` of the edge's length out along the normal, so its
        # distance from the edge IS the amplitude. Until 2026-09-05
        # `out` was a static 60 while the code claimed that distance
        # was the amplitude, which put a zero-amplitude readout 60px
        # off its own edge: further away, on a 40px edge, than the edge
        # is long. That is the field report this answers.
        # CLAMPED CLEAR OF BOTH VERTICES, because a handle over a
        # vertex makes that vertex unclickable. Where the edge is too
        # short to hold the clearance at all the seat goes to the
        # middle, which is the honest answer for an edge with no room.
        if not self._zigzag_readout:
          continue
        count = max(1, int(round(self._zigzag_readout[0])))
        along = _count_seat(count) * reach
        room = reach - _CLEAR_OF_VERTEX
        along = (reach / 2.0 if room <= _CLEAR_OF_VERTEX
                 else min(max(along, _CLEAR_OF_VERTEX), room))
        out = float(self._zigzag_readout[1]) * reach * _CREST_OF_H
        base_x = start.x() + (run / reach) * along
        base_y = start.y() + (rise / reach) * along
        placed.append((key,
                       QPointF(base_x + normal[0] * out,
                               base_y + normal[1] * out),
                       shape))
        continue
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

  def push_gain(self):
    """How far the ground moves for one unit of `push_d` here.

    Returns:
      The length of the library's own displacement at `push_d = 1.0`,
      in the unit's coordinates, or None where nothing is chosen, the
      chosen thing is not a vertex, or the direction cancels. DURING A
      GESTURE it is the value measured at the press and held there.

    HELD FOR THE LENGTH OF A DRAG, exactly as the edge's frame is.
    `_drawn()` is the drag's own PREVIEW once the first frame has been
    painted, and a push moves the very neighbours this length is
    summed from -- so read live it falls 0.4142, 0.3827, 0.3470,
    0.3138, 0.2660, 0.2001, 0.1029 over seven frames while the ground
    runs 1.9 times ahead of the pointer, and what gets recorded then
    depends on how many move events the machine delivered: 45 px
    recorded 0.2805 and 90 px recorded 0.1996. Measured 2026-09-07.
    This is the loop `_fit` already froze the frame for (C-198),
    arriving in the rail an hour after the rail gained a divisor.

    ASKED OF THE LIBRARY, exactly as `push_direction` is and for the
    same reason: `push_vertex` returns its displacement without
    applying it, so a second copy of the arithmetic here would drift
    from what the manipulation does. That method NORMALISES what this
    one measures -- it wants the direction and throws the length away
    -- which is why the gain went unnoticed: the two halves of one
    call, and only one of them was ever read.
    """
    if self.gesture_in_progress() and self._press_gain is not None:
      return self._press_gain
    return self._push_gain_now()

  def _push_gain_now(self):
    """Measure the push's gain against the design an edit is aimed at.

    Returns:
      What `push_gain` describes, taken from the held topology.
      Called by `push_gain` when no gesture is in progress, and once
      at the press to fill the value a gesture holds.

    ASKED OF `_topology` AND NEVER OF `_drawn()`, which is the half a
    first repair got wrong: freezing the VALUE at the press is no use
    while the STORE it is frozen from is the preview. The drop
    deliberately KEEPS a preview after a drag that recorded an edit --
    the rebuild is asynchronous and costs 0.75 to 19 seconds -- so a
    second press inside that window froze its divisor against the
    PREVIOUS drag's preview and the ground then ran 1.93 times ahead
    of the pointer (measured 2026-09-07 on `archimedean 4.8.8`, two
    40px rail drags with no landing between them; with a landing
    between, 1.0000 both times).

    `_on_dragging` builds every frame from `self._topology`, so this
    is also the store the gesture is actually aimed at -- and it is
    what the twin does: `_press_edge` freezes `_edge_frame` of the
    chosen thing, the base object's geometry, never what is drawn.
    """
    if self._chosen[0] != "vertex" or self._chosen_thing is None:
      return None
    topology = self._topology
    if topology is None:
      return None
    # BOTH HALVES FROM ONE STORE, which is the whole of this. The
    # library takes the vertex's own point from the ARGUMENT and its
    # neighbours from the TOPOLOGY -- `neighbours = [self.points[v] for
    # v in vertex.neighbours]` -- so handing a vertex seated on the
    # preview to the held design mixes a moved point with unmoved
    # neighbours and the gain is neither design's. A first repair took
    # the topology off the preview and left the vertex there; this took
    # the topology off the design and left the vertex on the preview,
    # which is the same fault with the halves swapped: measured
    # 2026-09-07, a second push after re-choosing the class recorded
    # 0.0884 where a landing between gave 0.1495, and the gain read
    # 0.4746 to 0.6801 against the honest 0.4142.
    # The vertex carries its own `ID`, and `points` is keyed by it.
    seated = topology.points.get(
      getattr(self._chosen_thing, "ID", None), self._chosen_thing)
    try:
      dx, dy = topology.push_vertex(seated, 1.0)
    except Exception:                                 # noqa: BLE001
      return None
    reach = (dx * dx + dy * dy) ** 0.5
    return reach if reach > 1e-6 else None

  def _handle_at(self, point) -> str:
    """The manipulation whose handle is under a point, or "".

    Args:
      point: where the pointer is.

    Returns:
      The manipulation key. Handles are tested BEFORE edges and
      vertices, because a handle sits on top of the thing it belongs
      to and is the smaller target.

    NEAREST WINS, NOT FIRST. This used to return the first handle
    within reach, which is only harmless while no two handles overlap:
    where two sit closer than twice the reach, the earlier one wins the
    WHOLE overlap and the later one cannot be clicked at any point at
    all. That cost `zigzag_edge` 23 edges of two designs in 2026-08-31,
    and it was answered then by pushing the handles apart -- which is
    what put the zigzag's readout 60px off its own edge and produced
    the field report this replaces. Asking which is NEAREST makes an
    overlap merely tight instead of fatal: each handle keeps the half
    of it that is closer to itself, so the arrangement is free to put a
    handle where its POSITION MEANS SOMETHING rather than where the
    tie-break happens to leave it reachable. (Ruling 1 of 2026-09-05.)
    """
    best, gap = "", _HANDLE_REACH
    for key, where, _shape in self.handles():
      away = ((where.x() - point.x()) ** 2 +
              (where.y() - point.y()) ** 2) ** 0.5
      if away < gap:
        best, gap = key, away
    return best

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

  def drag_travel_px(self) -> float:
    """How far the pointer moved between the grab and the release, in pixels.

    Returns:
      The straight-line pixel distance from where a handle was grabbed
      to where it was let go, or 0 where there was no grab. The drop
      reads it to tell a drag from a click: a gesture that travelled a
      real distance drew a preview and must commit it, even where the
      number it worked out equals the one the box already held -- a
      zigzag dragged on a fresh edge whose amplitude box carried a
      value from the last edit recorded NOTHING before this, because
      the value had not moved though the pointer plainly had (reported
      on rc17, 2026-09-06).
    """
    if self._press_px is None or self._release_px is None:
      return 0.0
    dx = self._release_px.x() - self._press_px.x()
    dy = self._release_px.y() - self._press_px.y()
    return (dx * dx + dy * dy) ** 0.5

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
      self._press_px = QPointF(point)
      self._release_px = QPointF(point)
      self._press_edge = (self._edge_frame(self._chosen_thing)
                          if self._chosen[0] == "edge" else None)
      # AND THE PUSH'S GAIN, FROZEN WITH IT. Measured on the topology
      # as it stands at the PRESS, because `_drawn()` becomes the
      # drag's own preview a frame later and the vertex's neighbours
      # move with it: the divisor then falls 0.4142 -> 0.1029 over
      # seven frames and the ground runs 1.9x ahead of the pointer.
      # This is C-198 in the rail rather than in the fit.
      self._press_gain = (self._push_gain_now()
                          if self._chosen[0] == "vertex" else None)
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
    # SHIFT OR COMMAND ADDS TO THE SELECTION rather than replacing it,
    # which is how every drawing tool anybody has used builds a
    # multiple selection. A plain click still replaces, so nothing
    # somebody already knows about this tab changes.
    adding = bool(event.modifiers() & (
      Qt.KeyboardModifier.ShiftModifier
      | Qt.KeyboardModifier.ControlModifier
      | Qt.KeyboardModifier.MetaModifier))
    self.chose.emit(target, label, adding)

  def gesture_in_progress(self) -> bool:
    """Is a drag under way, with the button still down?

    Returns:
      True between a press on a handle and the release that ends it.

    ASKED BY TWO THINGS FOR ONE REASON. `_fit` returns early while this
    is true, so the frame a drag is measured in cannot move under the
    gesture; and the panel HOLDS a topology landing for the same
    length of time, since adopting one wipes the preview and the
    highlight the gesture is aimed with. Both are the same rule --
    what a gesture is measured against is fixed until it ends -- and
    it is one method so they cannot come apart.
    """
    return self._press is not None

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
    self._release_px = QPointF(point)
    x, y = self._to_unit(point)
    # AS A FRACTION OF THE UNIT, not in map units: the manipulations
    # take proportions, and a drag that meant different amounts at
    # different spacings would be a control nobody could learn.
    self.dragging.emit((x - x0) / span, (y - y0) / span)

  def mouseReleaseEvent(self, event):  # noqa: N802 (Qt API)
    """End a drag, and let the panel commit it."""
    if self._press is None:
      return
    self._release_px = QPointF(event.position() if hasattr(event, "position")
                               else event.pos())
    self._press = None
    self._press_edge = None
    self._press_gain = None
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
  # THE BUTTON ASKS THE DIALOG TO GENERATE THE DUAL (ruling 1 of
  # 2026-09-05): the panel knows whether a dual is on offer, and the
  # dialog is what can land a map in a group. One signal, like the
  # edits, so the panel never reaches into the dialog.
  dual_requested = pyqtSignal()

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
    # THE LAST VALUE IN THIS GESTURE THAT LAID OUT, so a drag pushed
    # past the limit HOLDS there rather than being dropped. It belongs
    # to one gesture: `_on_grabbed` empties it at the press and
    # `_commit_the_drag` at the drop, so a later drag can never hold a
    # number an earlier one left behind.
    self._drag_last_good = None
    # WHAT THE POINTER ASKED FOR after the value stopped following it,
    # kept so the drop can close most of the gap between the two. Its
    # writers and clearers are exactly `_drag_last_good`'s, since the
    # pair is meaningless apart.
    self._drag_reached = None
    # The numbers as they stood when the handle was grabbed; see
    # `_on_grabbed`.
    self._drag_started_with = {}
    # WHAT IS SELECTED, as (target, labels) -- the one owner, which
    # the combo, the tick list and the drawing all follow.
    self._selection = ("", "")
    # The combo's temporary row for a subset nobody listed, or None.
    self._subset_row = None
    # A BUILD THAT LANDS WHILE THE POINTER IS DOWN, held until the drop.
    # See `set_unit`, which is where the reasoning lives.
    self._landing_held = None
    # AND THE SENTENCE THAT CAME WITH IT. A landing arrives as three
    # calls -- `set_unit`, `set_marks`, `report` -- and only the FIRST
    # is held while a gesture is in progress, so a refusal was written
    # into the note and then wiped by the held `set_unit` replaying at
    # the drop. Held here and said with the landing it belongs to.
    self._refusals_held = None
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

    # THE LIST THAT CONFIRMS WHAT IS SELECTED. (Maintainer's decision,
    # 2026-09-01: click to select, a list to confirm, each following
    # the other.) The drawing is where an edit is aimed -- shift or
    # command adds a class -- and this says which classes are in hand
    # without anybody having to read the highlight and count. Ticking
    # a row does the same job for somebody who never discovers the
    # modifier, which is the discoverability half of the same ruling.
    #
    # IT IS SHORT ON PURPOSE. Measured across a 48-design spread, most
    # designs carry one or two classes of each kind and the richest in
    # the sample has seven, so a list of rows costs a few lines rather
    # than a scrolling panel.
    self.class_list = QListWidget()
    self.class_list.setToolTip(
      "Every class in this design. Tick more than one to move them "
      "together.")
    self.class_list.setSelectionMode(
      QAbstractItemView.SelectionMode.NoSelection)
    self.class_list.setMaximumHeight(110)
    self.class_list.itemChanged.connect(self._on_class_ticked)
    grid.addWidget(self.class_list, 1, 0, 1, 2)

    # WHAT THE DESIGN'S SYMMETRY IS, in words, beside the classes it
    # explains. `D4` is dihedral of order four -- four rotations and
    # four mirrors -- and `C2` cyclic of order two, which is the
    # standard notation for a shape's own symmetry group. The counts
    # beside it are the tiling's, not a tile's.
    self.symmetry_note = QLabel("")
    self.symmetry_note.setWordWrap(True)
    self.symmetry_note.setToolTip(
      "The symmetry group of each tile, and how many symmetries the "
      "whole design has.")
    grid.addWidget(self.symmetry_note, 2, 0, 1, 2)

    self.how_combo = QComboBox()
    for key, spec in MANIPULATION_ORDER():
      self.how_combo.addItem(spec["label"], key)
    self.how_combo.setToolTip("What to do to the chosen class.")
    self.how_combo.currentIndexChanged.connect(self._rebuild_arguments)
    grid.addWidget(QLabel("Do"), 3, 0)
    grid.addWidget(self.how_combo, 3, 1)

    self._argument_rows = []
    # WHAT THE BOXES SAID, so a rebuild does not silently hand back
    # defaults. Keyed by manipulation: changing the verb asks for that
    # verb's parameters, and a build landing does not.
    self._argument_memory = {}
    self._arguments_belong_to = None
    self._argument_grid = grid
    side.addWidget(change)

    # THE DUAL AS A DESIGN, not merely as an overlay. (Maintainer's
    # decision, 2026-09-01.) The "Dual tiling" switch above draws the
    # dual over the design; this MAKES it the design, so the map is
    # tiled with it -- which is what promoting it to a tiling of its
    # own means.
    #
    # IT COSTS A TOPOLOGY BUILD PER REBUILD, which is 0.3 to 20
    # seconds depending on the design, and that is why it is a tick
    # rather than something the plugin does on its own: the tick is
    # the asking, exactly as it is for the experimental tabs.
    # IT IS A BUTTON AND A LABEL NOW, NOT A BOX (maintainer's ruling 1
    # of 2026-09-05, on field report 5). "Generate the dual and tile
    # it" lands the dual in a group of its own, named for the group it
    # came from, and the label below says when the group on screen is
    # one of those. The box is KEPT BUT NEVER SHOWN: it is the one
    # store of "is the map tiled with the dual", and thirteen readers
    # -- the geometry signature, the stamp, the shelf key, the working
    # state's design row -- speak that widget's language. A plain
    # attribute would mean a new record kind for one flag; a box
    # nobody can click is a bool with the plumbing already attached.
    # Nothing here is the two-controls-one-fact fault of C-43: there
    # is one store, one button that sets it, and a record that
    # restores it.
    self.map_dual = QCheckBox("Map the dual instead")
    self.map_dual.toggled.connect(self._say_whether_the_dual_is_mapped)
    self.dual_button = QPushButton("Generate the dual and tile it")
    self.dual_button.setToolTip(
      "Tiles the map with this design's dual, in a new layer group of "
      "its own.")
    self.dual_button.setEnabled(False)
    self.dual_button.clicked.connect(self.dual_requested.emit)
    side.addWidget(self.dual_button)
    self.dual_label = QLabel("")
    # How many times over the group on screen is dualled, as the store
    # tells it: the label says so. Duals chain (maintainer's ruling of
    # 2026-09-06), so the button stays offered on a dual group.
    self._depth_of_the_dual = 0
    self.dual_label.setWordWrap(True)
    side.addWidget(self.dual_label)

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

    # THE MAP'S LIVE UPDATE, WHERE THE EDITING HAPPENS. (Maintainer's
    # idea, 2026-09-05.) The tab redraws its OWN view on every edit
    # whatever this says; what this switches is the WHOLE-LAYER re-tile
    # in QGIS, which a topology edit triggers because an edit IS a
    # geometry change -- 1.36s at spacing 250 and 3.8s at 150, on every
    # Apply, while somebody making several edits in a row wants none of
    # them until they are done. The switch was two tabs away from the
    # work.
    #
    # IT IS A VIEW AND NEVER A STORE, which is the whole of what keeps
    # it out of the fault C-43 records. That one was two controls with
    # DIFFERENT SEMANTICS aimed at one outcome -- a one-shot entry
    # beside a standing preference -- so five readers asked one and one
    # asked the other. This box holds nothing: the dialog's own
    # `live_check` is the single owner, the dialog binds the two
    # symmetrically with signals blocked (as `_sync_pin_controls`
    # already does, or setting a control right fires the handler that
    # set it right), and NOTHING ANYWHERE MAY READ THIS BOX to decide
    # anything. `test_one_live_update_switch_seen_from_two_tabs` holds
    # both halves of that.
    self.live_here = QCheckBox("Live update of the map")
    self.live_here.setToolTip(
      "Redraws the whole map as you edit. The view above always "
      "follows your edits.")
    side.addWidget(self.live_here)

    self.note = QLabel("")
    self.note.setWordWrap(True)
    side.addWidget(self.note)
    # A SECOND LABEL, AND THAT IS THE POINT OF IT. (2026-09-01.) The
    # working sentence went into `note` first, and `note` already
    # means "the answer, or the reason there is none" -- so the
    # suite's own waiter, which treats a non-empty note as an answer
    # having arrived, returned before the build landed and a test read
    # a class list that did not exist yet. One store with two meanings
    # is this project's commonest defect wearing a QLabel, and the
    # repair belongs to the store rather than to the waiter that
    # trusted it.
    self.working = QLabel("")
    self.working.setWordWrap(True)
    side.addWidget(self.working)
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

    AND THE MARKS GO ENTIRELY, rather than being trimmed. This is the
    DESIGN-CHANGE door -- a family or an element count moved, and the
    working state's own edit list put back -- so every mark on hand
    describes the design being left. `set_marks`' docstring already
    says it: a mark that outlives the replay it came from describes
    another design. Trimming would keep the first few, which is worse
    than keeping none, since they would be silently about somebody
    else's edits.

    (Measured 2026-09-07: switching a design carried the outgoing
    one's "not applied" onto the incoming one's first change for 6.45
    seconds, until the rebuild landed. The repair for that fault two
    hours earlier enumerated Undo and Clear -- the two writers anybody
    would list -- and this restore is the third.)
    """
    self._edits = [dict(edit) for edit in (edits or [])]
    self._marks = []
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

  def say_a_build_is_coming(self) -> None:
    """Say that this tab's answer is still being worked out.

    Returns:
      None. Writes into the same note `set_unit` uses for the reason a
      design carries no topology, so the landing clears it by writing
      its own answer there and nothing has to remember to.

    THE TAB SAYS IT RATHER THAN GOING GREY. (Maintainer, 2026-09-01.)
    Greying was tried first and taken out the same hour: it takes the
    tab away from somebody mid-edit for as long as a build lasts,
    which is 0.79s on `laves 3.3.4.3.4` and 19.08s on `hex-colouring
    7`, and two registered tests went red because ticking the box no
    longer made the tab usable. What the interval needs is not a
    closed door but a sentence, because the drawing behind it is still
    the PREVIOUS design's until the build lands.

    AND IT IS ITS OWN LABEL, NOT THE NOTE. See the comment where
    `working` is built: the note means "the answer, or why there is
    none", and writing a third meaning into it made every waiter that
    reads it return early.
    """
    self.working.setText("Working out the design's structure…")

  def say_the_build_has_not_started(self) -> None:
    """Say that the work was handed over and has not begun.

    Returns:
      None. The sentence goes in the NOTE rather than beside the
      working label, because the note means "the answer, or why there
      is none" and a build nobody has started is a reason there is
      none -- so every waiter that reads the note gets a real answer
      instead of waiting out its ceiling on silence. The working
      sentence comes down with it, or the tab would promise an answer
      in one line and deny it in the next.

    IT DOES NOT CLEAR THE TOPOLOGY the tab is already showing. The
    previous design's picture staying up is the behaviour every other
    interval here has -- a build is queued and the drawing is the old
    one until the new one lands -- and blanking it would trade a stale
    picture for none at all. What changes is that the tab now SAYS the
    answer is not coming.

    AND IT IS UNDONE BY A LANDING, wherever one arrives: `set_unit`
    writes its own message into the note and empties `working`, so a
    build that starts late corrects this with nothing having to
    remember to.
    """
    self.working.setText("")
    self.note.setText(
      "QGIS has not started working out this design's structure. It "
      "may be busy with other work; the tab will fill in if the work "
      "begins.")

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
      None. A landing that arrives while a DRAG is in progress is held
      until the drop rather than applied, and `_settle_a_landing_the_
      drag_held` is what applies it.

    WHY A GESTURE OUTRANKS A LANDING. `show_topology` clears the drag's
    preview and the chosen thing -- correctly, since both belong to the
    topology being replaced -- so a build finishing under the pointer
    wiped the picture the person was dragging, put the un-edited design
    back beneath their hand, and dropped the highlight showing what
    they were aiming at. The drop then committed the edit anyway, out
    of a record they could no longer see. Measured 2026-09-01: one run
    in eight here, and all three CI platforms failed the drag guard's
    own premise -- "the drag drew no preview at all" -- which is what
    an intermittent wipe looks like from a runner.
    IT IS THE SIBLING OF THE FROZEN FRAME. A drag reads every position
    against the frame it began in; adopting a new topology mid-gesture
    moves the thing that frame describes, so the same rule applies to
    both -- a gesture's world is fixed for the length of the gesture.
    """
    if self.view.gesture_in_progress():
      self._landing_held = (unit, topology, message, ghost)
      return
    # AND A LANDING THAT ARRIVES WITH NO GESTURE SUPERSEDES A HELD ONE,
    # which is what stops a press nobody ever released -- a button held
    # while the window goes away -- leaving a stale design behind for
    # ever.
    self._landing_held = None
    self._unit = unit
    self._topology = topology
    # WHERE THE TILES NO LONGER MEET, computed once here rather than at
    # every repaint: 0.3 ms is cheap against a build and not against a
    # hover. None where the design is sound, which is the ordinary case
    # and draws nothing at all.
    where = None
    if unit is not None:
      # COVERAGE-BASED, so the hatch agrees with the change list's own
      # `sound` mark: `plane_coverage` catches a tear where the units
      # pull apart, which `gaps()` misses because it sees only a hole
      # enclosed within one.
      ratio, _overlap, missing = edits_module.plane_coverage(unit)
      if ratio >= edits_module.GAP_TOLERANCE:
        # AND THE HATCH SHOWS THE WHOLE TEAR, not the one cell the
        # coverage figure is measured over. (Maintainer's ruling,
        # 2026-09-07.) One cell is enough to DECIDE that a tiling has
        # torn, which is what `ratio` is for, and it is not enough to
        # SHOW the tear: on a per-edge rotate of the default design it
        # is 4 pieces of ground against 21, a fortieth of what is
        # actually torn. `tears_in_the_patch` lays its own patch, wide
        # enough to hold the block it measures, so what is hatched is
        # damage rather than the edge of what was drawn. It costs
        # 9.5 ms on the default design and about 140 ms on a hex-keyed
        # one -- paid once per landing, and only on this branch, where
        # the coverage figure has already said the design is torn.
        where = edits_module.tears_in_the_patch(unit) or missing
    self.view.show_topology(topology, message, ghost=ghost, gaps=where)
    self._say_what_the_symmetry_is(unit, topology)
    self._refresh_classes()
    self.note.setText(message if topology is None else "")
    # AND THE WORKING SENTENCE COMES DOWN HERE, wherever a build
    # lands: this is the one place every route to an answer passes
    # through, so nothing else has to remember to clear it.
    self.working.setText("")
    for widget in (self.class_combo, self.how_combo, self.apply_button):
      widget.setEnabled(topology is not None)
    self._offer_the_dual(topology)

  def _offer_the_dual(self, topology) -> None:
    """Enable the dual button only where a dual can be tiled, and say why not.

    Args:
      topology: what the tab now holds, or None.

    Returns:
      None. The button is enabled where `dual_on_offer` hands back a
      dual, and disabled with the reason in its tooltip otherwise --
      no topology, a dual the library cannot lay out, or one that would
      leave holes. Asked at every landing, which is the one place every
      route to an answer passes through, so the button can never offer
      a dual of a design that has moved on. (Ruling 2 of 2026-09-05: a
      map with holes never ships.)
    """
    dual, why = edits_module.dual_on_offer(topology)
    # ON TOP OF A DUAL TOO: the tab holds the dual's topology and offers
    # ITS dual, and since 2026-09-06 the build takes it, one level per
    # frozen list in the record's chain. Until then the store was a
    # boolean that took the dual once and the second press landed a
    # copy under a longer name, so the button was refused here.
    self.dual_button.setEnabled(dual is not None)
    self.dual_button.setToolTip(
      why if dual is None else
      "Tiles the map with this design's dual, in a new layer group of "
      "its own.")

  def _say_whether_the_dual_is_mapped(self, on) -> None:
    """The label beside the button: is the group on screen a dual's?

    Args:
      on: the store's new value -- a bool from the box, or the DEPTH
        from the dialog, since duals chain and the label says how
        many times over.

    Returns:
      None. The sentence is shown while the map is tiled with the
      dual and cleared otherwise; it follows the STORE rather than the
      button, so a group restored from its record says so without the
      button having been pressed this session (ruling 4).
    """
    depth = int(on)
    self._depth_of_the_dual = depth
    self.dual_label.setText(
      "" if depth < 1 else
      "Tiled with the dual of this design." if depth == 1 else
      f"Tiled with the dual of this design, taken {depth} times over.")
    # AND THE OFFER FOLLOWS THE STORE, since it is one of its terms.
    self._offer_the_dual(getattr(self, "_topology", None))

  # -------------------------------------------------------- controls

  def _say_what_the_symmetry_is(self, unit, topology) -> None:
    """Report each tile's own group and the design's symmetry count.

    Args:
      unit: the Tileable being shown, or None.
      topology: its built Topology, or None.

    Returns:
      None; the line under the class list is rewritten, and emptied
      where there is nothing to say rather than left describing the
      design before this one.

    IT IS A READING, NOT A CONTROL. Nothing here decides anything --
    the gate that greys a manipulation asks
    `directions_a_class_may_move` instead, which is about a CLASS and
    its stabiliser rather than about a tile's own shape. Two different
    questions that both get called symmetry, kept apart deliberately.
    """
    if unit is None or topology is None:
      self.symmetry_note.setText("")
      return
    codes = [code for code in edits_module.tile_symmetry_codes(unit) if code]
    found = edits_module.symmetries_to_draw(topology)
    parts = []
    if codes:
      parts.append("Tiles: " + ", ".join(codes))
    rotations, mirrors = len(found["rotations"]), len(found["mirrors"])
    if rotations or mirrors:
      parts.append(f"{rotations} rotation centre"
                   f"{'' if rotations == 1 else 's'}, "
                   f"{mirrors} mirror{'' if mirrors == 1 else 's'}")
    self.symmetry_note.setText(" — ".join(parts))

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
    # WHAT THE PERSON HAD CHOSEN, READ BEFORE THE CLEAR. A rebuild
    # refills this chooser, and a refilled combo sits on its first
    # entry -- so the class somebody clicked was replaced by whichever
    # class happens to sort first, with nothing said. The verb chooser
    # beside it has kept its own selection across a refill since it was
    # written ("narrowing the list does not silently retarget an edit
    # somebody was in the middle of describing"), and the two had no
    # business disagreeing.
    # MEASURED 2026-09-02: click `vertex B`, let a queued build land
    # before the pointer goes down, and the chooser reads `vertex A`,
    # `_chosen_thing` is None, the press finds no handle, the drag
    # draws no preview and records no edit. macOS CI failed `every way
    # of editing the topology moves the drawing` on exactly that --
    # both of its vertex cell's complaints at once -- while the test
    # passes here three times in three, the window being narrow rather
    # than the behaviour being rare.
    wanted = self.class_combo.currentData()
    self.class_combo.blockSignals(True)
    self.class_combo.clear()
    # DEFINED BEFORE THE GUARD, because the tick list below reads it
    # too and a design with no topology must leave both controls empty
    # rather than raising inside a Qt slot, where the exception is
    # swallowed along with the rest of the handler.
    groups = {}
    if self._topology is not None:
      groups = edits_module.classes(self._topology)
      for target in ("vertex", "edge"):
        for label in groups.get(target, ""):
          self.class_combo.addItem(f"{target} {label}", (target, label))
        if groups.get(target):
          self.class_combo.addItem(f"every {target}",
                                   (target, groups[target]))
    self.class_combo.blockSignals(False)
    # AND THE TICK LIST, from the same walk, so the two cannot come to
    # describe different designs. It carries one row per class and no
    # group row: "every" is what ticking them all means.
    self._subset_row = None
    self.class_list.blockSignals(True)
    self.class_list.clear()
    for target in ("vertex", "edge"):
      for label in groups.get(target, ""):
        item = QListWidgetItem(f"{target} {label}")
        item.setData(Qt.ItemDataRole.UserRole, (target, label))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Unchecked)
        self.class_list.addItem(item)
    self.class_list.blockSignals(False)
    # AND THE CHOICE IS PUT BACK WHERE THE NEW DESIGN STILL HAS IT. A
    # class that survived the rebuild is found by its own
    # (target, label); a design that no longer carries it falls
    # through to the first entry, which is the old behaviour and the
    # right answer when the class is genuinely gone. The objects are
    # new either way, and `_select_classes` re-seats `_chosen_thing`
    # on a member of the chosen class -- which is what
    # `show_topology` means by "the CLASS survives a rebuild".
    # COMPARED IN PYTHON, NOT BY `findData`, and that is not a
    # preference. These items carry a TUPLE, and `findData` matches
    # through QVariant, where a tuple never equals an equal tuple --
    # so it answers -1 for a class that is plainly in the list. The
    # verb chooser's own `findData` beside this one works only
    # because its data is a string. Measured 2026-09-02: the first
    # repair here used `findData` and changed nothing whatever, the
    # probe reporting the same chooser moving B to A.
    if wanted is not None:
      for index in range(self.class_combo.count()):
        if self.class_combo.itemData(index) == wanted:
          self.class_combo.blockSignals(True)
          self.class_combo.setCurrentIndex(index)
          self.class_combo.blockSignals(False)
          break
    # THE SELECTION IS RE-ESTABLISHED FROM THE COMBO, which now names
    # the class the person chose where the design still has it -- so a
    # rebuild leaves the three controls agreeing rather than leaving
    # the tick list empty beside a combo naming something.
    data = self.class_combo.currentData()
    if data:
      self._select_classes(*data)
    else:
      self._selection = ("", "")
      self._refresh_manipulations()

  def _refresh_manipulations(self):
    """Offer only the manipulations that suit what is selected.

    Returns:
      None. The chooser keeps whatever it was on where that is still
      valid, so narrowing the list does not silently retarget an edit
      somebody was in the middle of describing.
    """
    # THE OWNER SAYS WHICH KIND IS IN HAND, and it is the same answer
    # for one class or several -- a manipulation takes edges or
    # vertices, so a selection is only ever of one kind.
    kind = self._selection[0]
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
    self._grey_what_the_symmetry_holds()
    self.how_combo.blockSignals(False)
    self._rebuild_arguments()

  def _grey_what_the_symmetry_holds(self) -> None:
    """Turn off a manipulation the design's own symmetry forbids.

    Returns:
      None; an item in the verb chooser may be disabled and the note
      may gain a sentence.

    WHAT IT IS FOR. `push_vertex` moves a vertex along the directions
    its own symmetry leaves free, and where the symmetry leaves none
    it moves nothing at all: measured on `laves 3.3.4.3.4` and
    `hex-slice 3`, where the tab drew a rail of zero length and a
    person pulling it was told nothing, against 0.10 and 0.13 of the
    unit on `archimedean 4.8.8` and `archimedean 3.12.12`. The control
    is greyed WITH ITS REASON now, which is the ruling of 2026-08-31
    about shapes that say what they do, arriving at a control that
    cannot do anything.

    ONLY `push_vertex`. A nudge is an arbitrary displacement and moves
    the design whatever the symmetry says -- measured at 0.20 of the
    unit on the very classes the push cannot move -- so greying by
    symmetry alone would take away a working control.

    AND ONLY WHERE EVERY SELECTED CLASS IS HELD. With several classes
    in hand the edit is offered while ANY of them can move, since the
    manipulation is applied to each and the others simply contribute
    nothing.

    IT IS NECESSARY AND NOT SUFFICIENT, and the sentence says so: a
    class with a direction available may still yield nothing, which
    `laves 3.3.4.3.4` class B does. So the note reports what was
    measured -- the symmetry holds this class -- rather than promising
    that everything else will move.
    """
    target, labels = self._selection
    if self._topology is None or target != "vertex" or not labels:
      return
    free = max(
      (edits_module.directions_a_class_may_move(self._topology, target, label)
       for label in labels), default=2)
    if free > 0:
      return
    for index in range(self.how_combo.count()):
      if self.how_combo.itemData(index) != "push_vertex":
        continue
      item = self.how_combo.model().item(index)
      if item is not None:
        item.setEnabled(False)
      self.how_combo.setItemData(
        index,
        "The symmetry of this design holds this class in place, so a "
        "push along it has nowhere to go.",
        Qt.ItemDataRole.ToolTipRole)
      if self.how_combo.currentIndex() == index:
        for other in range(self.how_combo.count()):
          if other != index and self.how_combo.model().item(
              other).isEnabled():
            self.how_combo.setCurrentIndex(other)
            break
      break

  def _rebuild_arguments(self):
    """Build the parameter boxes the chosen manipulation needs.

    THE VALUES SURVIVE THE REBUILD, and until 2026-09-05 they did not.
    This runs from `_refresh_manipulations`, which runs from
    `_refresh_classes`, which runs from `set_unit` -- so EVERY BUILD
    THAT LANDS tore down these boxes and made fresh ones at their
    DEFAULTS. Measured that day by driving a landing: `n` typed as 6
    and `h` as 0.6 came back 2 and 0.25, silently, on an ordinary
    journey. That is the field report "a zigzag does not stick": the
    numbers a person set were not the numbers the edit was made with,
    and nothing said so.
    IT IS THE SAME FAULT AS THE PREVIEW SNAPPING BACK, in a different
    store: a thing cleared by an actor that is not the one replacing
    it. (C-244, and the sweep this belongs to is under 0.24.4.)

    THE MEMORY IS KEYED BY MANIPULATION, so each verb keeps its own
    numbers -- pick zigzag, set an amplitude, go to rotate and back,
    and the amplitude is where you left it. That is the per-element,
    per-field memory rule of 2026-08-21 arriving at this tab: what
    stays ACTIVE changes, what is REMEMBERED does not. A verb nobody
    has touched still opens at its declared defaults, which is the
    only thing an unused verb can honestly show.
    """
    key = self.how_combo.currentData()
    # Remembered BEFORE the teardown, and against the key the values
    # were typed for rather than the one about to be built.
    if self._argument_rows and self._arguments_belong_to is not None:
      self._argument_memory[self._arguments_belong_to] = self._arguments()
    for label, box in self._argument_rows:
      label.setParent(None)
      box.setParent(None)
    self._argument_rows = []
    self._arguments_belong_to = key
    if key is None:
      return
    remembered = self._argument_memory.get(key, {})
    for row, (name, label, low, high, default, step) in enumerate(
        edits_module.MANIPULATIONS[key]["args"], start=4):
      caption = QLabel(label)
      # THE AMPLITUDE BOX SHOWS THE CREST'S DISTANCE and holds `h`
      # (maintainer's ruling, 2026-09-06): three decimals, since the
      # floor of 0.01 in `h` is 0.005 on the face of the box.
      crest = key == "zigzag_edge" and name == "h"
      box = CrestSpinBox() if crest else TrimmedSpinBox()
      if crest:
        box.setDecimals(3)
      box.setRange(low, high)
      box.setSingleStep(step)
      box.setValue(remembered.get(name, default))
      box.setToolTip(
        "How far the crests reach out from the edge, as a fraction of the edge's length."
        if crest else f"{label} for this change.")
      box.setProperty("argument", name)
      if key == "zigzag_edge" and name == "n":
        # EVEN COUNTS ONLY, and a typed odd one is settled rather than
        # refused: `setSingleStep(2)` from a floor of 2 makes the
        # arrows step 2, 4, 6, 8, but a spin box accepts what is typed
        # into it, so the settling happens when editing finishes --
        # the honest moment, where the person sees 3 become 4, rather
        # than a `valueChanged` handler rewriting the box under their
        # keystrokes, which is one of the things this project has
        # already found eating what somebody typed.
        box.setToolTip("Zigzags for this change: even counts only, "
                       "since the library lays out only those.")
        box.editingFinished.connect(
          lambda b=box: self._keep_the_count_even(b))
      self._argument_grid.addWidget(caption, row, 0)
      self._argument_grid.addWidget(box, row, 1)
      # THE ZIGZAG'S HANDLE IS A READOUT OF THESE BOXES, so a box that
      # moves has to move the handle. Connected here rather than at the
      # box's construction because these rows are rebuilt whenever the
      # manipulation changes, and a connection made once would be to a
      # widget that has since been reparented away.
      box.valueChanged.connect(self._push_zigzag_readout)
      self._argument_rows.append((caption, box))
    self._push_zigzag_readout()
    # IT USED TO REFILL THE CLASS LIST FROM HERE, because the list was
    # filtered by the manipulation. Under select-then-act the list
    # holds every class whatever the verb is, so that call is not
    # merely redundant -- `_refresh_classes` now calls
    # `_refresh_manipulations`, which calls this, and the pair would
    # recurse without end.

  def _arguments(self) -> dict:
    """What the parameter boxes currently say, the zigzag's count settled.

    Returns:
      {argument: value} off the boxes; where the boxes belong to
      `zigzag_edge`, `n` is the nearest even count in range whatever
      the box shows. THE RECORD IS EVEN AT ITS ONE OWNER: the settle
      on `editingFinished` never fires for a person who types 3 and
      moves to the drawing (it takes no focus) or straight to Apply,
      and a settle at the zigzag handle's grab left every other door --
      a sibling handle, the chooser, Apply itself -- banking or
      recording the odd count (round eight, repairs18, 2026-09-06). The
      box itself is settled by `editingFinished` and at the grab.
    """
    values = {box.property("argument"): box.value()
              for _label, box in self._argument_rows}
    if getattr(self, "_arguments_belong_to", None) == "zigzag_edge" \
        and "n" in values:
      values["n"] = float(_even_count(values["n"]))
    return values

  def _push_zigzag_readout(self):
    """Tell the view where the zigzag handle now belongs.

    Returns:
      None. The view cannot ask this for itself -- the parameter boxes
      are the panel's -- so the panel is the ONE OWNER of it, exactly
      as it is of `_arguments`. Called when a box moves, when the
      manipulation changes, and while a drag previews, which are the
      three ways the answer can change.

    AND IT SAYS WHEN THE READOUT HAS STOPPED BEING ONE. Above the count
    at which the clamp bites, the handle no longer moves with `n`; the
    note says so rather than leaving somebody to decide the control is
    broken.
    """
    # THE HANDLE IS SHOWN WHATEVER IS CHOSEN, because a handle IS the
    # choice of manipulation -- the ruling of 2026-08-30 that this tab
    # is built on. Reading the live boxes only while zigzag happens to
    # be selected would make the glyph vanish for anybody who had not
    # already chosen it, which is precisely the state `push_vertex` was
    # in before it got a rail. So: the boxes where they are the
    # zigzag's, the manipulation's declared defaults otherwise, and the
    # handle then always shows the zigzag the current settings describe.
    chosen = self.how_combo.currentData() == "zigzag_edge"
    # UNDER ANOTHER VERB THE BANK ANSWERS, not the declared defaults:
    # `_rebuild_arguments` has just banked the person's numbers and
    # `_on_grabbed` seeds a drag from them, so a handle drawn at the
    # defaults stood 44px from the wave it would record (round eight,
    # repairs20). The defaults stand in only where nothing was banked.
    if chosen:
      args = self._arguments()
    else:
      args = {name: default for name, _label, _low, _high, default, _step
              in edits_module.MANIPULATIONS["zigzag_edge"]["args"]}
      args.update(getattr(self, "_argument_memory", {}).get("zigzag_edge") or {})
      if "n" in args:
        args["n"] = float(_even_count(args["n"]))
    self.view.set_zigzag_readout(
      (args.get("n", 2.0), args.get("h", 0.0), chosen))
    # AND WHERE THE CLAMP HAS BITTEN, THE BOX SAYS SO. Deliberately the
    # BOX's tooltip and not the panel's note line: the note is written
    # by refusals and by the build's own messages, so a second writer
    # there would clear somebody else's sentence or be cleared by it --
    # which is the transient-picture fault this project already has a
    # rule about, arriving in a message store instead of a drawing.
    # A MARK ON THE GLYPH ITSELF IS OWED and is recorded in ROADMAP.md:
    # a tooltip is legible to somebody who goes looking, and the person
    # this is for is watching the handle rather than the box.
    exact = self.view.zigzag_readout_is_exact()
    for _label, box in self._argument_rows:
      if box.property("argument") != "n" or \
          self.how_combo.currentData() != "zigzag_edge":
        continue
      box.setToolTip(
        "Zigzags for this change: even counts only, since the library "
        "lays out only those."
        if exact else
        "Zigzags for this change, even counts only. This edge is too "
        "short to place that many apart on the drawing, so the handle "
        "has stopped moving with the count -- this box is where the "
        "count is.")

  def _on_class_chosen(self):
    """Highlight whatever class the chooser now names, and re-offer
    the manipulations that suit it."""
    data = self.class_combo.currentData()
    if data:
      # THROUGH THE OWNER, so picking a row in the combo moves the
      # tick list and the drawing with it -- the "each following the
      # other" half of the ruling.
      self._select_classes(*data)

  def _on_chose(self, target, label, adding=False):
    """Follow a click in the view back into the selection.

    Args:
      target: "edge" or "vertex", as the view reports it.
      label: the class label that was clicked.
      adding: True where the click carried shift, control or command,
        meaning add this class to the selection rather than replace
        it. A click on a class already in hand REMOVES it, so the same
        gesture undoes itself -- and the last one cannot be removed,
        since a selection of nothing is not a state this tab has.

    Returns:
      None. The list holds every class of both kinds since
      2026-08-30, so a click always lands somewhere -- which is the
      whole of select-then-act. Before that the list was filtered by
      the current manipulation and a click on the other kind moved
      nothing here while the drawing highlighted it anyway.

    ADDING ACROSS KINDS IS A REPLACEMENT, deliberately: a manipulation
    takes edges or vertices and never both, so a selection holding
    some of each could not be applied and the chooser would have
    nothing honest to say.

    AND A PLAIN CLICK INSIDE THE SELECTION CHANGES NOTHING.
    (Maintainer's rule, 2026-09-07.) A plain click outside the ticked
    set replaces it, which is what a plain click has always done and
    is what somebody expects of a drawing; but where several classes
    are ticked, clicking ONE of them used to collapse the selection
    onto that one -- measured on `laves 3.3.4.3.4`, a click on `A` with
    `AB` held left `A` alone ticked. So an edit aimed at both classes
    was silently narrowed to one by the act of pointing at what was
    already selected, which is how somebody loses a selection they
    built deliberately. The click still moves `_chosen_thing` in the
    view, so the handles follow the pointer to the instance under it;
    only the CLASS selection stands still.
    """
    held_target, held = self._selection
    if adding and target == held_target:
      labels = [x for x in held if x != label] if label in held \
          else list(held) + [label]
      self._select_classes(target, "".join(sorted(labels)) or label)
      return
    if target == held_target and label in held:
      # ALREADY IN HAND. Refreshing the manipulations is still right --
      # the instance under the pointer decides which handles are drawn
      # -- but the selection itself must not narrow.
      self._refresh_manipulations()
      return
    self._select_classes(target, label)

  def _select_classes(self, target: str, labels: str) -> None:
    """Put the selection on one or more classes, and move everything.

    Args:
      target: "edge" or "vertex".
      labels: one or more class labels, as a string -- which is the
        shape the library's own selector takes, so nothing is
        translated on the way to `transform_geometry`.

    Returns:
      None. The combo, the tick list and the drawing all follow this,
      with their signals blocked: setting a control right would
      otherwise fire the handler that set it right, which is the same
      discipline `_sync_pin_controls` carries.
    """
    self._selection = (target, labels)
    self._sync_the_selection()
    self.view.set_chosen(target, labels)
    self._refresh_manipulations()

  def _sync_the_selection(self) -> None:
    """Make the combo and the tick list say what is selected.

    Returns:
      None. The combo names the class where exactly one is in hand,
      the group entry where every class of that kind is, and a COUNT
      -- "2 of 3 vertex classes" -- for anything between, which is a
      row it grows and removes as needed rather than a lie about which
      single class an edit will move.
    """
    target, labels = self._selection
    self.class_combo.blockSignals(True)
    self.class_list.blockSignals(True)
    try:
      wanted = None
      for index in range(self.class_combo.count()):
        data = self.class_combo.itemData(index)
        if data and data[0] == target and data[1] == labels:
          wanted = index
          break
      if wanted is None:
        # A SUBSET NOBODY LISTED, so the combo grows a row for it and
        # that row is replaced rather than accumulated: one temporary
        # entry at a time, removed as soon as the selection is
        # something the list already names.
        text = (f"{len(labels)} of "
                f"{len(self._labels_of(target))} {target} classes")
        if self._subset_row is not None:
          self.class_combo.removeItem(self._subset_row)
        self.class_combo.addItem(text, (target, labels))
        self._subset_row = self.class_combo.count() - 1
        wanted = self._subset_row
      elif self._subset_row is not None:
        self.class_combo.removeItem(self._subset_row)
        self._subset_row = None
        wanted = None
        for index in range(self.class_combo.count()):
          data = self.class_combo.itemData(index)
          if data and data[0] == target and data[1] == labels:
            wanted = index
            break
      if wanted is not None:
        self.class_combo.setCurrentIndex(wanted)
      for index in range(self.class_list.count()):
        item = self.class_list.item(index)
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
          continue
        ticked = (data[0] == target and data[1] in labels)
        item.setCheckState(Qt.CheckState.Checked if ticked
                           else Qt.CheckState.Unchecked)
    finally:
      self.class_combo.blockSignals(False)
      self.class_list.blockSignals(False)

  def _labels_of(self, target: str) -> str:
    """Every class label of one kind, as one string.

    Args:
      target: "edge" or "vertex".

    Returns:
      The labels in the order the topology lists them, or "" where
      this design has none of that kind.
    """
    if self._topology is None:
      return ""
    groups = edits_module.classes(self._topology)
    return groups.get(target, "")

  def _on_class_ticked(self, item) -> None:
    """Follow a tick in the list into the selection.

    Args:
      item: the row whose check state changed.

    Returns:
      None. Unticking the last class of a kind is refused by putting
      the tick back, because an edit aimed at nothing is not something
      this tab can carry -- and a control that silently accepts an
      impossible state is worse than one that will not move.
    """
    data = item.data(Qt.ItemDataRole.UserRole)
    if not data:
      return
    target, label = data
    held_target, held = self._selection
    if item.checkState() == Qt.CheckState.Checked:
      labels = (list(held) + [label]) if target == held_target else [label]
    else:
      if target != held_target:
        return
      labels = [x for x in held if x != label]
      if not labels:
        self._sync_the_selection()      # put the last tick back
        return
    self._select_classes(target, "".join(sorted(set(labels))))

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
        break
    # A TYPED COUNT NEEDS NO SETTLING HERE: `_arguments` settles it
    # wherever the record reads the boxes (round eight, 2026-09-06), and
    # the drag's own write-back puts the settled count in the box.
    # WHAT THE NUMBERS WERE WHEN THE HANDLE WAS TAKEN, so a drag that
    # moves only the COUNT can be told from one that moved nothing.
    # `_drag_moved` asks whether a gesture asked for anything, and it
    # can only ask that of a parameter by comparing with where the
    # parameter started -- a count of 3 is not "no movement" merely
    # because 3 is what the box holds after the drag put it there.
    self._drag_started_with = dict(self._arguments())
    self._drag_last_good = None
    self._drag_reached = None

  # ------------------------------------------------------------ drag

  def _drag_argument(self, key, frame, dx, dy, span, current=None):
    """What a drag on an edge means for the chosen manipulation.

    Args:
      key: the manipulation the `how` chooser names.
      frame: the grabbed edge's (mid_x, mid_y, along_x, along_y,
        length), in unit coordinates.
      dx: travel left to right, as a fraction of the unit.
      dy: travel bottom to top, as the same fraction.
      span: the unit's own width, to turn those fractions back into
        unit coordinates so they can be compared with the edge.
      current: what the parameter boxes say now, or None. A parameter
        that is a POSITION has to be moved from where it already is,
        and the zigzag's count is one: the glyph sits on the first
        peak, so the drag carries it from that peak rather than from
        nothing.

    Returns:
      A mapping of argument name to value -- possibly more than one,
      since a zigzag's glyph carries both its count and its amplitude
      -- or an empty mapping where this manipulation takes nothing a
      drag can supply.

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
      # ACROSS IS THE AMPLITUDE AND ALONG IS THE COUNT, which is the
      # whole of ruling 2 of 2026-09-05. Both are relative to the
      # edge's own length, so the same gesture means the same shape on
      # a long edge and a short one, and both are POSITIONS: the glyph
      # sits at the count's seat along the edge (`_count_seat`) and `h`
      # of the length out, so where the person has taken it IS the
      # pair of numbers.
      # THE AMPLITUDE IS WHERE THE HANDLE NOW SITS, NOT HOW FAR IT
      # TRAVELLED. The glyph is drawn `h` of the edge's length out
      # along the normal, so the press lands there and `across` is the
      # travel FROM there -- and until 2026-09-05 this line read
      # `abs(across) / length`, the travel alone, so a handle grabbed
      # at h=0.3 and moved one pixel along the edge previewed a wave of
      # 0.01, and a drag meant to step the COUNT flattened the zigzag
      # to nothing on its way (measured driving the tab: typed 0.3,
      # eight pixels along, recorded h 0.01 and n 1). The count half of
      # this same function was already a position (`here + along`
      # below); this is its amplitude half brought level with it,
      # which is ruling 1 of that day in as many words -- the distance
      # from the edge IS the amplitude.
      # THE SIGN IS THE VIEW'S. The normal the handle is drawn along is
      # taken in screen space, where y grows downward, and `across`
      # here is the dot with the unit-space normal, where y grows up
      # -- so the handle side is NEGATIVE `across`, and the handle's
      # own position is `-h * length`. Moving further out makes
      # `across` more negative and `h` larger; moving back toward the
      # edge brings it toward zero and past it, and the absolute value
      # is what makes crossing the edge fold rather than go negative,
      # since the box holds no negative amplitude.
      was_h = float(current.get("h", 0.0)) if current else 0.0
      # AND THE HANDLE SITS AT HALF OF `h`, since the library's `h`
      # is peak to peak (`_CREST_OF_H`), so the position is read in
      # crest units and handed back in the box's.
      # THE HANDLE SIDE IS POSITIVE `across` since 2026-09-06: the
      # unit-space left normal, `(-ay, ax)`, is where the library puts
      # the first lobe and where the handle now sits, so its position
      # is `+h * length * _CREST_OF_H` and travel further out adds.
      changes = {"h": abs(was_h * length * _CREST_OF_H + across)
                      / (length * _CREST_OF_H)}
      # THE DEADBAND IS NOT OPTIONAL. `scale_edge` was measured on
      # 2026-08-30 committing a scale of 1.003 from a drag meant as a
      # click, because a gesture mostly ACROSS an edge still resolves
      # to a little travel ALONG it -- and here that would silently
      # change the count, which is the coarsest parameter on the tab.
      # SIZED FROM THE GLYPH RATHER THAN GUESSED: a tenth of the edge
      # is just under one 12px seat on the 94px edges measured here, so
      # a gesture that never leaves the handle's own drawn shape cannot
      # move the count. (`h` needs no such guard: it is continuous, and
      # a small amplitude is a small amplitude.)
      if abs(along) >= _COUNT_DEADBAND * length:
        was = float(current.get("n", 2.0)) if current else 2.0
        here = _count_seat(was) * length
        moved = here + along
        # THE NEAREST EVEN COUNT TO WHERE THE HANDLE NOW IS, the seats
        # spread evenly along the edge (2026-09-06). Dragging toward
        # the edge's far end RAISES the count; two sits on its own
        # first crest and eight stops clear of the end handles.
        changes["n"] = _count_at(moved / length if length > 1e-9 else 0.0)
      return changes
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
      return {"angle": math.degrees(math.atan2(across, out))}
    if key == "scale_edge":
      return {"sf": math.hypot(out, across) / half}
    return {}

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
    # THE OWNER AGAIN: a drag moves whatever is selected, which since
    # 2026-09-01 may be several classes.
    data = self._selection
    key = self.how_combo.currentData()
    if self._topology is None or not data[1] or not key:
      return
    raw_changes = {}
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
        # AND DIVIDED BY THE VERTEX'S OWN GAIN, so the ground follows
        # the pointer (maintainer's ruling, 2026-09-07). The comment
        # above said there was no gain factor in between; there was,
        # and it was the library's, 0.4142 on `archimedean 4.8.8`.
        travel = float(dx * way[0] - dy * way[1])
        raw_changes["push_d"] = _push_for_travel(
          travel, self.view.push_gain())
        args["push_d"] = self._within_the_box("push_d", raw_changes["push_d"])
      elif key == "nudge_vertex":
        raw_changes["dx"], raw_changes["dy"] = float(dx), float(dy)
        args["dx"] = self._within_the_box("dx", float(dx))
        args["dy"] = self._within_the_box("dy", float(dy))
      else:
        return
    else:
      frame = self.view.grabbed_edge()
      if frame is None:
        return
      # FROM WHERE THE HANDLE WAS TAKEN, NEVER FROM THE LAST FRAME.
      # `dragging` reports travel cumulative from the press, and each
      # frame writes its result back into the boxes below, so seeding
      # the position from the live boxes added the whole travel again
      # on every move event: a 5px drag delivered as 25 events
      # recorded h 0.288 where 0.068 was asked (round eight,
      # repairs16, 2026-09-06). `_drag_started_with` was written for
      # exactly this and read only by `_drag_moved` until then.
      started = dict(self._drag_started_with) or dict(args)
      changes = self._drag_argument(
        key, frame, dx, dy, self.view.unit_span(), current=started)
      if not changes:
        return
      for name, value in changes.items():
        raw_changes[name] = value
        args[name] = self._within_the_box(name, value)
    self._drag_from = dict(args)
    # THE GLYPH FOLLOWS THE GESTURE, because its position is the pair
    # of numbers: a handle that stayed put while the wave under it
    # changed would be a readout that lies for the length of a drag.
    # The count SNAPS here, visibly, which is the point -- the stops a
    # person sees are the counts they can have.
    if key == "zigzag_edge":
      self.view.set_zigzag_readout(
        (args.get("n", 2.0), args.get("h", 0.0), True))
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
      # AND THROUGH THE COMMIT'S OWN DOOR, not the library's. Rotate and
      # scale are reformulated in `move_as_applied` to keep the tiling
      # edge-to-edge, and calling the library directly here drew a torn
      # design for a move whose commit is gap-free -- 1.78% of a cell
      # open at 15 degrees on `laves 3.3.4.3.4`, and a raise at 60 --
      # so the honest preview honestly reported a tear the drop would
      # never have made.
      moved = edits_module.move_as_applied(
        self._topology, data[1], key,
        edits_module.in_map_units(
          edits_module.whole_where_needed(args),
          getattr(self._topology, "tileable", None)))
    except Exception:                                 # noqa: BLE001
      # AND A PREVIEW THAT FAILED COMMITS NOTHING. `_drag_from` is what
      # the drop records, so leaving it set would let a gesture that
      # drew nothing still add an edit -- the user would be shown one
      # thing and given another.
      # THE VALUE STOPS AT THE LAST ONE THAT LAID OUT, rather than the
      # gesture being dropped. (Maintainer's ruling, 2026-09-07.) The
      # preview is already built every frame -- 158ms for the
      # transform -- and a ceiling probe is 161ms because it IS that
      # same transform, so the predicate this needs is one the drag has
      # already evaluated: there is nothing to compute and nothing to
      # cache. The pointer may keep going; the number does not.
      # WHY NOT A CEILING HERE. Bisecting for the exact maximum costs
      # 1.4s, which is a freeze at the moment somebody starts dragging.
      # This is exact to one frame of pointer travel instead.
      # AND THE DROP DOES NOT MAKE IT EXACT, which this comment claimed
      # until 2026-09-07 and which is worth stating plainly because the
      # claim is inviting: `apply`'s clamp is entered only where the
      # edit produced nothing drawable, and a held value laid out by
      # construction, so the clamp can only ever LOWER what it is
      # given. Nothing raises a held value to the true ceiling.
      # WHAT THAT COSTS, measured: a frame is 158 ms and the default
      # design's edges draw at about 94 px, so a pointer at 250 px/s
      # advances 0.42 of the amplitude between samples against a
      # ceiling of 0.594 -- the shortfall is bounded by a frame of
      # travel, not by a pixel of it. Ruling 2 is what ships (the value
      # holds at the last one that laid out); making the drop seek the
      # exact ceiling would be a change to that ruling rather than a
      # repair, and it is the maintainer's.
      if self._drag_last_good is not None:
        self._drag_from = dict(self._drag_last_good)
        # AND WHAT THE POINTER ASKED FOR ANYWAY, which the drop uses to
        # close most of the gap the frame's own coarseness leaves.
        self._drag_reached = dict(args)
        self._show_arguments(self._drag_last_good)
      else:
        # NOTHING HAS LAID OUT YET IN THIS GESTURE, so there is no
        # value to hold and nothing to record -- the first frame
        # already failed.
        self._drag_from = None
      # AND IT SAYS SO, WHICH IS THE HALF THAT WAS MISSING. Returning
      # here left the PREVIOUS preview and the previous state on
      # screen, so a drag pushed past what can be laid out went on
      # drawing the last wave that worked, in the ordinary ink, with
      # nothing to say the pointer had gone beyond it -- a person
      # imagining a move will be allowed when it will not, which is
      # exactly what the honest preview exists to prevent. The picture
      # is kept, since a drawing that vanishes mid-gesture says less
      # than one that stops; the STATE is what changes.
      # CLAMPED RATHER THAN FAILED where a value is being held: FAILED
      # now means a move that lays out and still tears, which is what
      # `plane_coverage` measures. Held at a limit is amber, not red.
      self.view.set_drag_status({
        "clamped": self._drag_last_good is not None,
        "failed": self._drag_last_good is None, "key": key,
        # TWO SENTENCES, BECAUSE THE TWO STATES ARE DIFFERENT THINGS
        # to be told. Where a value is being HELD the move is fine and
        # the number has simply stopped following the pointer, so the
        # sentence invites the drop: letting go records the held value,
        # which is what is on screen. Where nothing in this gesture has
        # laid out there is no held value at all, so that sentence
        # promises nothing about the drop and says what to do instead.
        # NEITHER MAY OUTRUN THE CODE BESIDE IT, which is the thing to
        # check when either is reworded: a first draft offered to
        # record a move and draw it as deep as it could go, on the
        # branch that had just cleared what the drop reads.
        # AND THE HELD SENTENCE NAMES THE MOVE IT IS ABOUT. One
        # sentence for every manipulation told somebody dragging a
        # ROTATE that "a deeper wave than this runs beyond the edges" --
        # found by rendering the gesture rather than by reading, since
        # the words are only wrong on the branch a drag past the limit
        # reaches.
        "reason": (
          (_HELD_SENTENCE.get(key) or _HELD_SENTENCE[None])
          if self._drag_last_good is not None else
          "Your suggestion can't be laid out as a tiling as it "
          "stands; a smaller move usually can.")})
      return
    # THIS FRAME LAID OUT, so it becomes the value a later frame
    # holds at if the pointer goes further than the design allows.
    self._this_frame_laid_out(args)
    self.view.show_preview(moved)
    # AND THE NUMBER BOXES FOLLOW, so a drag is a way of typing rather
    # than a second, separate control: drag roughly, then read what it
    # chose and correct it by hand.
    self._show_arguments(args)
    # AND THE DRAWING SAYS WHICH OF THREE STATES THIS MOVE IS IN, so a
    # person never imagines a move will be allowed when it will not
    # (maintainer's principle, 2026-09-06). CLAMPED: the raw gesture
    # asked past a box limit, so the value stopped and the glyph does
    # too. FAILED: the previewed design leaves gaps and cannot be
    # tiled -- asked of the cheap union `gaps`, not a build, so it is
    # affordable once a frame. Shown, not enforced (ruling 5).
    self.view.set_drag_status(
      self._status_of_a_drag(key, raw_changes, args, moved))

  def _status_of_a_drag(self, key, raw_changes, args, moved) -> dict:
    """Whether the move in progress is valid, clamped or failed.

    Args:
      key: the manipulation.
      raw_changes: what the gesture asked for, before the boxes
        clamped it.
      args: the values after clamping, which the preview was built
        from.
      moved: the previewed topology.

    Returns:
      {clamped, failed, reason, key}. `clamped` is True where the raw
      gesture ran past a box's own range, so what is drawn is the
      limit rather than what the pointer asked; `failed` is True
      where the previewed design cannot be tiled, with `reason` the
      words to show. A count SNAPPING to an even value is not
      clamping -- only a value pushed past its min or max is.
    """
    clamped = False
    for name, raw in raw_changes.items():
      for _label, box in self._argument_rows:
        if box.property("argument") != name:
          continue
        if float(raw) < box.minimum() - 1e-9 \
            or float(raw) > box.maximum() + 1e-9:
          clamped = True
        break
    failed, reason = False, ""
    unit = getattr(moved, "tileable", None)
    if unit is not None:
      try:
        # COVERAGE, NOT `gaps()`. This draft asked `gaps()`, which finds
        # only holes ENCLOSED within a patch -- so a move that pulls the
        # units apart, leaving a tear open onto the surrounding space,
        # read as perfectly sound and the preview would have drawn it
        # valid (C-341). `plane_coverage` measures one fundamental
        # cell and catches a gap and an overlap alike, which is what
        # the soundness mark and the hatch already read.
        gap, overlap, _missing = edits_module.plane_coverage(unit)
        if gap >= edits_module.GAP_TOLERANCE:
          failed = True
          reason = ("This much would leave gaps the tiles cannot "
                    "close; ease back to keep a tiling.")
        elif overlap >= edits_module.GAP_TOLERANCE:
          failed = True
          reason = ("This much would make the tiles overlap; ease "
                    "back to keep a tiling.")
      except Exception:                             # noqa: BLE001
        pass
    return {"clamped": clamped, "failed": failed,
            "reason": reason, "key": key}

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
    """Commit the drag as an edit, or put the view back.

    Returns:
      None. Whatever this does with the drag, a landing HELD while the
      pointer was down is settled on the way out -- through a `finally`
      rather than at each of the four exits, since an exit added later
      would otherwise strand a build nobody applied.
    """
    edits_before = len(self._edits)
    try:
      self._commit_the_drag()
    finally:
      self._settle_a_landing_the_drag_held(edits_before)

  def _settle_a_landing_the_drag_held(self, edits_before: int) -> None:
    """Apply a build that finished while the pointer was down.

    Args:
      edits_before: how many edits stood when the drop began, which is
        what says whether this gesture committed one.

    Returns:
      None. The held landing is DISCARDED where the drop recorded an
      edit, because that record makes the dialog chain and land again
      within the tick -- and the held one describes the design as it
      was BEFORE the edit, so applying it would draw the previous
      design over the new one and then be corrected, which is a flicker
      rather than a picture. Where the gesture committed nothing there
      is no second landing coming, so this is the one that draws it.
    """
    held = self._landing_held
    said, self._refusals_held = self._refusals_held, None
    self._landing_held = None
    if held is None or len(self._edits) != edits_before:
      # THE SENTENCE GOES WITH THE LANDING IT CAME WITH. Where the
      # gesture committed an edit the held landing is discarded and a
      # fresh one is already coming with its own refusals, so keeping
      # these would put the previous design's sentence over the new
      # one's.
      return
    self.set_unit(*held)
    # AND IT IS SAID AFTER `set_unit`, which clears the note: the
    # order the call site uses, restored at the moment the landing
    # actually arrives on screen.
    self._say_what_could_not_be_drawn(said)

  def _commit_the_drag(self):
    """End the gesture, and take down the state it was drawn in.

    Returns:
      None. Delegates the whole decision to `_commit_the_drag_body`
      and clears the drag status afterwards, through a `finally` so
      every exit is covered -- including one somebody adds later.

    THE STATUS BELONGS TO THE GESTURE, NOT TO THE PICTURE, which is
    what makes this a different question from the preview's. The
    preview is deliberately KEPT where an edit was recorded, since the
    rebuild that answers it is asynchronous and clearing at the drop
    put the un-edited design back for 1.7 seconds; but the amber or
    red that says "this is being held at a limit" describes a pointer
    that is no longer down, and leaving it up would colour a settled
    picture with the state of a gesture that has ended.
    """
    try:
      self._commit_the_drag_body()
    finally:
      self.view.set_drag_status(None)
      self._drag_last_good = None
      self._drag_reached = None

  def _commit_the_drag_body(self):
    """Turn the gesture just ended into an edit, or discard it.

    Returns:
      None. THE PREVIEW IS KEPT WHERE AN EDIT WAS RECORDED and cleared
      at once on every path that records nothing.

    WHY IT IS NOT CLEARED AT THE DROP. It was, on the first line, and
    the rebuild that answers an edit is ASYNCHRONOUS -- so between the
    drop and the landing `_drawn` fell back to `self._topology`, which
    is the UN-EDITED design. Field report against 0.24.4rc15: "it
    reverts for a second and then a few seconds later updates
    correctly". Measured on the default design, `laves 3.3.4.3.4`: the
    old design stood for 1.676 seconds, and the settled drawing's
    fingerprint was IDENTICAL to what the preview had been showing --
    so the correct picture was on screen, was thrown away, and was
    recomputed. On `hex-colouring 7`, whose build is nineteen seconds,
    that is nineteen seconds of the wrong design under somebody's hand.

    WHAT CLEARS IT INSTEAD is the landing, which every route to an
    answer passes through: `show_topology` sets `_preview = None` as
    its own third line. So the preview stands exactly as long as there
    is nothing better to draw, which is what a preview is for.

    AND THE DISCARD PATHS STILL CLEAR AT ONCE, because there a preview
    describes something the record does NOT hold -- a press that went
    nowhere, a selection the tab cannot act on -- and leaving it up
    would be the view describing an edit nobody made. That is the fault
    `show_preview` was split from `show_topology` to prevent, and it is
    the reason this is a decision per path rather than one line moved.

    THE OPEN CASE IS A RECORD WITH NO REBUILD BEHIND IT, and it is
    left drawing the edit deliberately: if no landing ever arrives the
    preview shows what the person asked for, which agrees with the
    change list, where reverting would show a design the list denies.
    """
    if self._drag_from is None:
      self.view.show_preview(None)
      return
    args = self._drag_from
    self._drag_from = None
    # THE OWNER, as at the preview and at Apply -- one question, one
    # answer, whichever control the person used to ask it.
    data = self._selection
    key = self.how_combo.currentData()
    if not data[1] or not key:
      self.view.show_preview(None)
      return
    # A PRESS THAT WENT NOWHERE IS A CLICK, and a click chooses a class
    # rather than editing anything. The test is on what the drag
    # actually asked for, per manipulation, because "nothing moved"
    # is a different number for an angle than for a fraction.
    # A REAL DRAG COMMITS WHAT THE PREVIEW DREW, whatever the number
    # worked out to. `_drag_moved` asks whether the VALUE moved, which
    # is right for a click on a handle already at its value but wrong
    # for a drag on a fresh edge whose box holds a leftover value: the
    # amplitude clamped at the ceiling could not rise, so a plain
    # outward drag recorded nothing though the preview had drawn the
    # zigzag (rc17, 2026-09-06). The pointer travelling past the click
    # threshold IS the gesture, so either answer commits it.
    if not (self._drag_moved(key, args, self._drag_started_with,
                             self._amplitude_deadband())
            or self.view.drag_travel_px() >= _AMPLITUDE_DEADBAND_PX):
      self.view.show_preview(None)
      return
    args = self._refined_towards_what_was_asked(key, data[1], args,
                                                self._drag_reached)
    self._record({"classes": data[1], "how": key, "args": args})

  def _this_frame_laid_out(self, args):
    """Keep a frame that laid out, and forget anything held before it.

    Args:
      args: the values this frame previewed, which laid out.

    Returns:
      None; `_drag_last_good` becomes these values and
      `_drag_reached` is dropped.

    WHY THE FORGETTING IS THE POINT. `_drag_reached` is what the
    pointer had asked for at the moment the value stopped following
    it, and the drop refines from the held value toward it. Its reason
    expires the instant a later frame lays out: somebody who drags too
    far, meets the refusal, eases back inside and lets go is no longer
    holding anything. Left standing, it made the drop bisect toward a
    value abandoned mid-gesture -- measured 2026-09-07 on `archimedean
    4.8.8`: a gesture ending on 0.100, with the box, the preview and
    the status all agreeing, recorded 0.350, and the record is what
    travels to the file and replays.

    So the two are written at ONE site, since a pair whose members are
    set in different places is a pair that comes apart.
    """
    self._drag_last_good = dict(args)
    self._drag_reached = None

  def _refined_towards_what_was_asked(self, key, labels, good, asked,
                                      steps=_REFINING_STEPS):
    """Close most of the gap between a held value and the pointer's.

    Args:
      key: the manipulation.
      labels: the classes the edit is aimed at.
      good: the value the drag held, which laid out by construction.
      asked: what the pointer had reached by then, or None where the
        gesture was never held at all.
      steps: how many probes to spend. Each halves the remaining gap
        and costs about 161 ms, being the same transform the preview
        performs every frame.

    Returns:
      The furthest value toward `asked` that still lays out, or `good`
      unchanged where there is nothing to close or no topology to ask.

    WHY THE DROP AND NOT THE DRAG. A drag holds at the last value that
    laid out (ruling 2, 2026-09-07) and computes no ceiling, because
    bisecting for the exact one costs 1.4 s -- a freeze at the moment
    somebody starts dragging. What that leaves is a shortfall bounded
    by a FRAME of pointer travel rather than a pixel of it: a frame is
    158 ms and the default design's edges draw at about 94 px, so a
    pointer at 250 px/s advances 0.42 of the amplitude between samples
    against a ceiling of 0.594. The number you ended up with depended
    on how fast you moved the mouse.

    So the refining happens ONCE, at the drop, where half a second is
    a gesture ending rather than a window freezing, and three probes
    leave at most an eighth of that gap. (Maintainer's ruling,
    2026-09-07, by grilling: ruling 2's reasoning kept and its
    mouse-speed dependence removed.)

    THE DISCRETE ARGUMENTS ARE NOT INTERPOLATED. A zigzag's count
    snaps to even numbers and its smoothness is a sample count, so a
    midpoint between two of them is not a value any control can hold;
    they stay as the held frame had them, which is what the person was
    shown.
    """
    topology = self._topology
    if topology is None or not asked or not good:
      return good
    moving = [name for name in asked
              if name not in ("n", "smoothness")
              and isinstance(asked.get(name), (int, float))
              and isinstance(good.get(name), (int, float))
              and abs(float(asked[name]) - float(good[name])) > 1e-12]
    if not moving:
      return good
    low, high = 0.0, 1.0
    best = dict(good)
    for _ in range(max(0, int(steps))):
      middle = (low + high) / 2.0
      candidate = dict(good)
      for name in moving:
        candidate[name] = (float(good[name]) + middle
                           * (float(asked[name]) - float(good[name])))
      if edits_module.lays_out(topology, labels, key, candidate):
        best, low = candidate, middle
      else:
        high = middle
    return best

  def _amplitude_deadband(self) -> float:
    """Half a handle seat, as a fraction of the chosen edge's length.

    Returns:
      `_AMPLITUDE_DEADBAND_PX` over the chosen edge's screen length,
      so the same pixels of slip mean the same thing on a long edge
      and a short one; the box's floor, 0.01, where no edge is chosen
      or the view cannot measure it, which is the pure-function
      default `_drag_moved` carries.
    """
    reach = self.view.chosen_edge_length_on_screen()
    if not reach:
      return 0.01
    # In the box's units: the seat is `h * reach * _CREST_OF_H` px out,
    # so half a seat of pixels is that many over the crest scale.
    return _AMPLITUDE_DEADBAND_PX / (reach * _CREST_OF_H)

  def _keep_the_count_even(self, box):
    """Settle a typed zigzag count to the nearest even one.

    Args:
      box: the count's spin box, after editing finished.

    Returns:
      None. Moves the box only where its value is odd or outside the
      count's range, so an even count typed is left exactly as typed
      and nothing is rewritten under a keystroke.
    """
    value = float(box.value())
    even = _even_count(value)
    if abs(even - value) > 1e-9:
      box.setValue(even)

  def _drag_moved(self, key, args, started=None,
                  amplitude_deadband=0.01) -> bool:
    """Did this drag ask for anything?

    Args:
      key: the manipulation the drag is for.
      args: the parameters the drag produced.
      started: what the boxes said when the handle was grabbed, or
        None. Passed IN rather than read off `self`, because this is
        called unbound as a pure function by
        `test_every_handle_a_drag_offers_commits_what_it_previewed` --
        which is a fair thing for a test to do of a function that is
        about its arguments, and the reason to keep it that way.
      amplitude_deadband: the smallest change of the zigzag's `h`
        that counts as a gesture, as a fraction of the edge's own
        length. The panel passes half a handle seat in the chosen
        edge's screen pixels (`_amplitude_deadband`); the default is
        the box's floor, for a caller with no drawing to measure.

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
    if key == "push_vertex":
      # THE FIFTH MEMBER, and the reason this table is the thing that
      # went stale. `_drag_moved` was written 2026-08-30 when a vertex
      # carried ONE handle; the push rail was added on 2026-08-31 with
      # the ruling that every manipulation is reachable on the
      # drawing, and a table keyed by manipulation does not grow with
      # the family by itself. Without this the fall-through answered
      # False, so `_commit_the_drag` returned before `_record` and a
      # push somebody had watched move under their hand was thrown
      # away in silence -- measured 2026-09-02 on `archimedean 4.8.8`,
      # where the drag previewed and left the record at nought while
      # the nudge handle beside it recorded exactly as it should.
      # ITS OWN IDEA OF NOTHING is a fraction of the unit, as the
      # nudge's is: `push_d` is what the rail's own length is measured
      # in, and both become map units at `in_map_units`.
      return abs(args.get("push_d", 0.0)) > 1e-4
    if key == "zigzag_edge":
      # EITHER PARAMETER COUNTS. The amplitude is continuous, so its
      # own smallest meaningful change guards it; the count is whole,
      # and any step of it is a step somebody made past the deadband.
      # Before the count was draggable this asked about `h` alone, and
      # a gesture that moved only the count would have been discarded
      # as a click -- which is the "nothing happened" this tab has
      # already been reported for once.
      was = (started or {})
      was_n = was.get("n")
      stepped = (was_n is not None
                 and round(float(args.get("n", was_n)))
                 != round(float(was_n)))
      # THE AMPLITUDE MOVED FROM WHERE IT WAS, not "is not zero": the
      # handle is a position, so a click on a handle already at 0.3
      # comes back reading 0.3, and only travel from there is a
      # gesture. Under half a seat of travel it is a click, whatever
      # the box's floor is (the decision of 2026-09-05, at
      # `_AMPLITUDE_DEADBAND_PX`).
      was_h = float(was.get("h", 0.0))
      return stepped or (abs(float(args.get("h", 0.0)) - was_h)
                         > amplitude_deadband)
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
    # THE OWNER, NOT THE COMBO. The two agree by construction, and
    # asking the owner is what stops a later reader having to know
    # which of three controls is authoritative.
    target, labels = self._selection
    if self._topology is None or not labels:
      return
    self._record({"classes": labels,
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

    AND THE RECORD CARRIES THE ALPHABET IT WAS AIMED AGAINST (conflict
    7, settled 2026-09-05): the edge or vertex classes the design had
    when the edit was made. The shelf key stays narrow -- family,
    count, dual -- so a spacing or modifier tweak never puts an edit
    away; what a modifier CAN do is split a class, so `a` names a
    different set of edges than it did, and `apply` compares this
    against the design it replays onto and says so. Recorded here
    rather than at each caller because a drag and the Apply button
    both arrive at this one door.
    """
    how = edit.get("how")
    if self._topology is not None and "against" not in edit:
      target = edits_module.MANIPULATIONS.get(how, {}).get("target", "")
      edit["against"] = edits_module.classes(self._topology).get(target, "")
    self._edits.append(edit)
    self._refresh_list()
    self.edits_changed.emit()

  def _keep_the_marks_in_step(self):
    """Drop any mark left without an edit under it.

    Returns:
      None; `_marks` is truncated to the length of `_edits`.

    WHY IT IS NEEDED AT ALL. `_marks` is written by ONE writer, a
    landing, and read BY INDEX beside `_edits`. Undo and Clear change
    `_edits` alone, which is harmless for the rows that survive -- the
    marks still line up -- and is not harmless for the NEXT edit
    somebody makes, which lands on an index a stale mark still
    occupies and wears the verdict of the change it replaced. Measured
    2026-09-07: record a rotate that tears, undo it, record a sound
    scale, and the new row reads "from here the tiles no longer meet"
    until the rebuild lands seconds later -- up to nineteen on the
    slowest design in the catalogue.

    A mark that is ABSENT is already handled everywhere: `_refresh_list`
    says nothing rather than guessing, which is the right answer for an
    edit no build has judged yet. So truncating is the whole repair.
    """
    del self._marks[len(self._edits):]

  def _undo(self):
    """Take the most recent change off."""
    if self._edits:
      self._edits.pop()
      self._keep_the_marks_in_step()
      self._refresh_list()
      self.edits_changed.emit()

  def _clear(self):
    """Take every change off this design."""
    if self._edits:
      self._edits = []
      self._keep_the_marks_in_step()
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
      args = ", ".join(f"{label} {value:g}" for label, value in
                       _as_the_controls_name_them(edit))
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

    AN EMPTY LIST WRITES NOTHING. (2026-09-05, field report 5.) The
    note is one QLabel with two writers: `set_unit` puts the reason
    there is no topology into it, and the landing calls this
    immediately afterwards with the replay's refusals -- which, on a
    design whose topology was refused, is an empty list. Writing
    `" ".join([])` erased the reason the panel had been given one call
    earlier, so a person met a blank tab. `set_unit` already clears
    the note wherever a topology arrives, so there is nothing for an
    empty report to clear; it only ever had something to ADD.

    AND A GESTURE HOLDS THIS ALONGSIDE THE LANDING IT BELONGS TO.
    (2026-09-07.) The reasoning above depends on an ORDER -- `set_unit`
    first, this immediately afterwards -- and a landing arriving under
    a pointer INVERTS it: `set_unit` returns early and is replayed at
    the drop, where it clears the note this had already written. So
    somebody who happened to be holding a handle when the build landed
    was never told why their replayed edit could not move what it
    named. Held here and said by `_settle_a_landing_the_drag_held`,
    which is the one place that knows the landing has arrived.
    """
    if self.view.gesture_in_progress():
      self._refusals_held = list(refusals or [])
      return
    self._say_what_could_not_be_drawn(refusals)

  def _say_what_could_not_be_drawn(self, refusals):
    """Put the replay's refusals into the note, where there are any.

    Args:
      refusals: sentences from the replay, or an empty list.

    Returns:
      None; an empty list writes nothing, for the reason `report`
      gives above.
    """
    if refusals:
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
