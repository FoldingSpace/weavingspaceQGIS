"""Main dialog of the WeavingSpace plugin.

Design controls mirror the mapweaver web app; output is one QGIS layer
per tile element, gathered in a layer-tree group, each given a standard
QGIS renderer so refinement happens in QGIS's normal styling tools.
Regenerating replaces the previous group's layers in place (styling
survives unless an element's assignment changed).

A QGIS/Qt PRIMER for weavingspace maintainers
---------------------------------------------
If you know the weavingspace library but not QGIS, these are the ideas
this file leans on; everything else is ordinary Python.

* Qt widgets and signals. The dialog is built from Qt widgets
  (QComboBox, QSpinBox, ...). A widget announces changes by emitting a
  *signal*; ``widget.someSignal.connect(fn)`` registers ``fn`` to run
  when it fires. Two recurring subtleties: setting a widget's value in
  code fires the same signal a user interaction would, so programmatic
  updates are wrapped in ``blockSignals(True)/(False)`` to avoid
  feedback loops; and ``activated`` fires only on real user picks while
  ``currentIndexChanged`` fires for programmatic changes too, which is
  how we tell "user touched this" from "we set it".

* Debouncing with QTimer. A single-shot QTimer runs its ``timeout``
  slot once, ``interval`` ms after the most recent ``start()``; calling
  ``start()`` again restarts the countdown. We funnel every control
  change through two such timers so that dragging a spinner rebuilds
  the preview (PREVIEW_DEBOUNCE_MS, widened on a slow rebuild) and
  regenerates the map (LIVE_DEBOUNCE_MS) once per pause,
  not once per tick.

* Threading via QgsTask (see worker.py). Qt GUIs are single-threaded:
  only the main thread may touch widgets, and long work on the main
  thread freezes QGIS. QgsApplication.taskManager() runs a QgsTask's
  ``run()`` on a worker thread and its ``finished()`` back on the main
  thread. THE ONE HARD RULE (see MAINTAINING.md): the worker must never
  touch pyproj/PROJ, because QGIS uses the same PROJ library on the
  main thread and concurrent use segfaults; ``_generate`` therefore
  strips CRS off every GeoDataFrame before handing it to the task and
  ``done`` reattaches it afterwards.

* The project and its layer tree. QgsProject.instance() is the open
  project: a registry of layers (``addMapLayer``/``removeMapLayer``,
  each layer keyed by a stable string ``id()``) plus a *layer tree*
  (``layerTreeRoot()``) that is the panel the user sees, where layers
  can be gathered into named groups. We add layers with
  ``addMapLayer(layer, False)`` (False = don't auto-place in the tree)
  and then attach them to our own group node explicitly.

* Table cell widgets. QTableWidget lets a real widget live in a cell
  (``setCellWidget``); we use that for the per-element combos, spinner,
  and colour button. Two Qt traps found the hard way: a widget placed
  into a *hidden* column can paint at the table's origin until a layout
  pass (so visibility is set explicitly after placing), and "blank"
  cells are made by *removing* the widget, not hiding it, because some
  render paths paint hidden cell widgets anyway.

Targets QGIS 4+ (PyQt6, Python 3.12+); imports go through the
``qgis.PyQt`` layer and the few version-sensitive APIs through
compat.py, so a future QGIS transition lands in one file.
"""

from __future__ import annotations

import json
import math
import os
import time
import traceback

from qgis.PyQt.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from qgis.PyQt.QtGui import (
  QBrush, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap)
from qgis.PyQt.QtWidgets import (
  QAbstractButton,
  QApplication,
  QCheckBox,
  QComboBox,
  QDialog,
  QDoubleSpinBox,
  QFormLayout,
  QGroupBox,
  QHBoxLayout,
  QLabel,
  QLineEdit,
  QMessageBox,
  QProgressBar,
  QPushButton,
  QSpinBox,
  QStyle,
  QStyleOptionComboBox,
  QStylePainter,
  QTableWidget,
  QTableWidgetItem,
  QTabWidget,
  QVBoxLayout,
  QWidget,
)
from qgis.core import (
  QgsApplication,
  QgsMapLayerProxyModel,
  QgsProject,
  QgsRectangle,
)
from qgis.gui import QgsColorButton, QgsFileWidget, QgsMapLayerComboBox

from . import bridge, catalog, perception
from .category_editor import CategoryColourDialog
from .widgets import TrimmedSpinBox
from .worker import TilingTask

GROUP_BASE_NAME = "WeavingSpace tiles"

# ---------------------------------------------------------------------
# THE WORKING STATE: what an output group carries, so that CHOOSING a
# group restores the map it describes instead of the dialog inferring
# one. Ruling 4 of 2026-08-25 (CLAUDE.md, "THE OUTPUT GROUP IS THE UNIT
# OF WORK"), settled by a grilling after a colleague drove the older
# rules through a demo of several datasets in a row: three memory
# scopes -- records kept per dataset, a design carried globally, a
# group remembered nowhere -- answered one act in three different ways,
# and none of the three was named anywhere on screen.
#
# THE TABLES BELOW ARE THE RECORD'S REAL DEFINITION, and capture and
# restore read the SAME ones. That is the whole safety of it.
# `_adopt_dock_bounds` keeps its record and its restore whitelist as
# two separate enumerations, and a key added to the first and forgotten
# from the second is dropped in SILENCE on every reopen -- so the
# record is right all session and wrong the moment the project comes
# back, which is how that one was got wrong once. One table cannot
# drift from itself, so widening the record IS widening the whitelist.

# The chooser's last entry, which is not a group but an instruction:
# the next run builds one of its own. Shown last rather than first so
# the groups that exist read as the ordinary case.
NEW_GROUP_LABEL = "Create new"

# THE TWO DEBOUNCES, AND THEY ARE WHAT A PERSON FEELS. Nudging a design
# control schedules two pieces of work: the tile unit and the design
# preview are rebuilt after PREVIEW_DEBOUNCE_MS of quiet, and with live
# update on the MAP is re-tiled after LIVE_DEBOUNCE_MS. They guard very
# different costs -- measured 2026-08-26 on a sixteen-polygon fixture, a
# preview rebuild is about 20 ms of CPU and a live tick about 229 ms,
# and on the maintainer's own three thousand areas a Generate is
# seconds -- which is why they are two numbers and not one. Collapsing
# them would either delay the feedback that says an input registered,
# or launch real tilings at the preview's cadence.
#
# NAMED HERE BECAUSE THEY WERE WRITTEN IN SIX PLACES. The intervals had
# no home: two `setInterval` calls, four docstrings and a stack of test
# waits, all carrying the literal number, so changing one meant finding
# the rest -- and the suite's staggered-action sweep chose its delays to
# STRADDLE these boundaries, so a value moved without it would have
# quietly stopped straddling anything while still passing. That sweep
# derives its delays from these constants now.
#
# THE PREVIEW INTERVAL IS A FLOOR, NOT A FIXED WAIT, and that is what
# makes shortening it safe on a machine nobody here has measured.
# (Maintainer's decision, 2026-08-26: take the shorter number "if the
# recommended option there is generally safe on different sorts of
# computers and load conditions" -- so the condition was checked
# rather than assumed, and a flat number does not meet it.)
#
# WHAT A DEBOUNCE ACTUALLY GUARDS, since the obvious worry is the
# wrong one. The timer is SINGLE-SHOT and restarted by every change,
# so continuous input -- a held-down spin button, a dragged slider --
# fires exactly ONE rebuild whatever the interval, and shortening it
# changes only how soon that rebuild starts. What a longer interval
# really absorbs is a HESITATION: a pause of 150-350 ms mid-
# interaction, which at 350 is swallowed and at 150 starts work the
# user is about to interrupt. On a machine where a rebuild is cheap
# that costs nothing. Where it is expensive it is the "snappy feel
# has gone" complaint made worse.
# WHAT MAKES A REBUILD EXPENSIVE IS ELEMENTS AND FIELDS, NOT
# FEATURES, and this comment said otherwise until it was measured on
# 2026-08-26: one rebuild makes 30,529 primitive calls over sixteen
# areas and 30,529 over three thousand -- identical. The number that
# moves it is the design's element count crossed with the width of
# the attribute table, and at twenty-six elements over a hundred
# columns a rebuild cost 871 ms and armed this timer at its ceiling.
# The earlier claim borrowed the shape of the uncached-value defect
# of 2026-08-19, which really was about features (3,011 rescanned 23
# times for one keystroke) and is a different mechanism on a
# different path.
#
# SO THE WAIT IS AT LEAST AS LONG AS THE LAST REBUILD TOOK, floored at
# PREVIEW_DEBOUNCE_MS and capped at PREVIEW_DEBOUNCE_CEILING_MS, which
# is the flat value it had before. A fast machine with a small design
# gets the short wait; a slow one, or a heavy design, widens itself
# back towards the old number and is never worse than it was. Measured
# with the MONOTONIC clock, per this project's rule that only
# timestamps are wall clock -- a laptop closed mid-interaction must not
# come back believing a rebuild took two hours.
#
# THE LIVE INTERVAL IS UNTOUCHED, deliberately. It guards something
# genuinely expensive -- 229 ms on a sixteen-polygon fixture, seconds
# on three thousand areas -- and shortening it is only safe alongside
# cancelling a superseded run sooner, which is a change to the run
# lifecycle rather than to a number and wants its own round.
PREVIEW_DEBOUNCE_MS = 150
# ...AND NEVER LONGER THAN THIS, which is what the preview debounce
# was flat until 2026-08-26.
PREVIEW_DEBOUNCE_CEILING_MS = 350
LIVE_DEBOUNCE_MS = 900

WORKING_STATE_PROPERTY = "weavingspace_working_state"

# Bumped when the shape below changes in a way an older plugin could
# not read. A record from a FUTURE version is refused whole rather than
# half-read (`_read_working_state`), because a design restored with the
# keys this version happens to recognise is a design nobody chose.
WORKING_STATE_VERSION = 1

# Each row is (record key, the dialog's attribute, how to read and
# write it). CAPTURED FROM THE SAME SET `_geometry_signature` READS --
# family, kind, element count, `_unit_kwargs`'s own controls, the seven
# modifiers, the glyph box and the five map-option switches -- so the
# record and the signature cannot come to describe different designs.
# The one addition is `tile_outlines`, which reaches the signature
# through every assignment's "outline" rather than on its own.
#
# ORDER IS LOAD-BEARING AT THE FRONT of this table and nowhere else:
# the family list is REBUILT from the element count and the kind, so a
# family written before them lands in a list that is about to be
# replaced. `_apply_working_state` sets those three itself, in order,
# and walks the rest of the table plainly.
WORKING_STATE_DESIGN = (
  ("n", "n_combo", "data"),
  ("kind", "kind_combo", "text"),
  ("family", "family_combo", "text"),
  ("spacing", "spacing_spin", "number"),
  ("offset", "opt_offset", "number"),
  ("offset_angle", "opt_offset_angle", "number"),
  ("point_angle", "opt_point_angle", "number"),
  ("aspect", "opt_aspect", "number"),
  ("over_under", "opt_over_under", "line"),
  ("grid_rows", "opt_grid_rows", "number"),
  ("grid_cols", "opt_grid_cols", "number"),
  ("rotate", "mod_rotate", "number"),
  ("scale_x", "mod_scale_x", "number"),
  ("scale_y", "mod_scale_y", "number"),
  ("skew_x", "mod_skew_x", "number"),
  ("skew_y", "mod_skew_y", "number"),
  ("prototile_inset", "mod_p_inset", "number"),
  ("tile_inset", "mod_t_inset", "number"),
  ("glyph", "mod_glyph", "checked"),
  ("join_prototiles", "opt_join_prototiles", "checked"),
  ("retain", "opt_retain", "checked"),
  ("clip", "opt_clip", "checked"),
  ("icons", "opt_icons", "checked"),
  ("outlines", "opt_outlines", "checked"),
  ("tile_outlines", "opt_tile_outlines", "checked"),
)

# WHAT EACH ELEMENT CARRIES, every key of it taken from
# `_assignments()` -- "the ONE crossing point between widget state and
# everything downstream" by its own docstring. Taking the record from
# there rather than reading the table a second time means the group
# remembers exactly what the run was built from.
#
# TWO KEYS OF `_assignments()` ARE DELIBERATELY ABSENT, and both are
# facts about the DATA rather than choices somebody made:
# `value_digest` summarises the column's values, and
# `class_source_stamp` summarises what is inside a QML. Storing either
# would freeze a reading of data that moves, and both are recomputed
# from the live layer whenever they are wanted. `mode` is absent too,
# since `_assignments` DERIVES it from `mode_raw` and the column's
# type -- storing the derived form would restore "Categorized" onto a
# row whose owner chose a quantitative scheme, which is the same
# mistake `_refresh_table` records against shelving `prev["mode_raw"]`.
WORKING_STATE_ELEMENT = (
  # "mode" joined this list on 2026-08-26, in the same commit as the
  # code that reads it, per the rule that THIS LIST IS THE RECORD'S
  # REAL DEFINITION: a key missing from it is dropped in silence, and
  # the restore then behaves as though the record never held it.
  # It is here because CLEARING a record needs to know WHY the record
  # is silent. `_assignments` reports pins, class colours and the ramp
  # window as empty for any row not wearing Graduated, and categorical
  # colours as empty for any row not wearing Categorized -- so silence
  # means "another style" as often as it means "nobody chose one", and
  # only the mode tells the two apart. Without it the clearing is
  # inert, which is how it was found: two tests went red saying a
  # record rode onto a group that never had one.
  "id", "var", "mode", "mode_raw", "scheme", "k", "ramp", "reverse",
  "single_colour", "opacity", "class_source", "class_choice",
  "quant_colours", "category_colours", "range_bounds", "pinned",
  "style_touched",
  # "kept" joined on 2026-08-26, in the same commit as the code that
  # writes and reads it: the OTHER fields' pins and hand-picks for
  # this element, per field, so a saved PROJECT carries the whole
  # working memory home (the revisit ruling 6 anticipated). It rides
  # the .qgz through the layer-tree node and MUST NEVER reach the
  # GeoPackage's record -- what a redistributed file shows is the
  # limit of what it contains -- which `_file_safe_state` enforces at
  # every file write.
  "kept",
)

# WHAT SITS AT THE EDGE OF "THE WHOLE WORKING STATE", written down
# because the roadmap asked for the list explicitly and because the
# next person will want to add something to it.
#
# THE RULE THAT DECIDES IT: the record holds what DESCRIBES THE MAP,
# never what describes the session's working habits. A map has a
# design, a symbology and a file it was written to; it does not have
# an opinion about whether the preview redraws as you type.
#
# So the output path is IN -- it is where this group's map actually
# went, and a resumed group that wrote somewhere else would overwrite
# a stranger's file. Live update, the colour-legibility warning and
# "Create as new group" are OUT: the first two are preferences about
# how the dialog behaves while somebody works, and the third is an
# instruction about the NEXT run rather than a property of this one.
# The preview's context shells are out for the same reason.
WORKING_STATE_EDGES = ("output_path", "region")
# `region_crs` rides beside `region` and is deliberately NOT an edge.
# The edges are the two facts a LANDING alone may move; the system the
# region was drawn in is a property OF that region rather than a third
# thing to decide, so it is carried wherever `region` is carried and
# asked for nowhere else. It exists because a CRS a person assigned
# lives on the layer and not in its source string, so a recovery
# rebuilt from the string alone brought the region back in the file's
# own coordinates (2026-08-28).


def _plugin_version() -> str:
  """The installed version, read from metadata.txt (one source of truth)."""
  try:
    meta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "metadata.txt")
    with open(meta, encoding="utf-8") as f:
      for line in f:
        if line.startswith("version="):
          return line.split("=", 1)[1].strip()
  except Exception:
    pass
  return "unknown"


def compat_layer_available(dialog, layer) -> bool:
  """compat.layer_data_is_available, imported at the point of use.

  Args:
    dialog: unused; present so the live gate can call this as one
      short line beside its other guards.
    layer: the layer to test.

  Returns:
    Whatever compat.layer_data_is_available says.

  This exists only to keep the import out of a guard clause in the
  middle of the live-render gate, which is already a long list of
  conditions and reads better without an import wedged into it.
  """
  from . import compat
  return compat.layer_data_is_available(layer)


def _polygon_filter():
  """Filter value so the region combo lists only polygon layers."""
  from . import compat
  return compat.polygon_layer_filter()


def _nice_number(x: float) -> float:
  """Round x up to a 'clean' value (1/2/2.5/5 times a power of ten),
  used so the derived default spacing reads as a sensible number."""
  # A layer with no CRS set can report an infinite extent, and
  # math.floor(math.log10(inf)) raises OverflowError rather than
  # returning anything. That reached a user as an unhandled exception
  # from pressing Generate, with nothing said about the layer.
  if not math.isfinite(x) or x <= 0:
    return 1.0
  exp = math.floor(math.log10(x))
  mant = x / 10 ** exp
  for m in (1, 2, 2.5, 5, 10):
    if mant <= m:
      return m * 10 ** exp
  return 10 ** (exp + 1)


# How large a ramp swatch is drawn in the Colour ramp dropdown. This
# has to be applied in TWO places to have any effect: the pixmap is
# drawn at this size, and each combo is told to display icons at this
# size. A QComboBox left alone uses the platform style's icon size,
# which on a desktop theme is around 16 pixels, so a swatch drawn
# larger than that was simply scaled back down and the ramp was almost
# unreadable -- which is what it looked like, and why enlarging the
# pixmap on its own would have changed nothing.
RAMP_SWATCH = QSize(64, 18)

# How many stripes a swatch shows. The swatch is 64px wide, and below
# about 8px a stripe stops reading as a colour of its own; eight also
# samples a ramp closely enough that neighbouring ramps stay
# distinguishable in the dropdown.
SWATCH_STRIPES = 8

# What separates two notices sharing the dialog's single note line
# when there is no QGIS message bar to stack them in. See
# WeavingSpaceDialog._report_quietly.
NOTE_SEPARATOR = "  |  "

# The "Edit colours" column. Appended after the columns that were
# already there and moved into place visually, so no existing column
# number changes. See _build_ui, where the move happens.
COL_EDIT_COLOURS = 8


# DRAWN ONCE PER RAMP AND DIRECTION, not once per appearance.
#
# Every ramp combo is filled with an icon for EVERY ramp in the style
# library, and there is one combo per table row, so a single table
# rebuild draws around 240 of these. Measured 2026-08-16 on one test:
# 306,558 icon draws, 311,613 style-library lookups and 2.45 million
# fillRect calls, against 115,038 / 117,053 / 920,304 for the same
# test at 0.24.2 -- the same work, done nearly three times as often
# because this release rebuilds the table more.
#
# An icon is a pure function of the ramp's name and its direction, and
# the ramp library does not change while nobody is editing it, so
# almost all of that is the identical picture drawn again. The cache
# keys on exactly what the drawing depends on.
#
# WHAT INVALIDATES IT: every signal QgsStyle offers about its
# contents changing. Measured on QGIS 4.0.3 (2026-08-16):
# removeColorRamp emits rampRemoved and entityRemoved, and the cache
# hears both; plain addColorRamp emits NOTHING. That silence is
# harmless for a new name -- it was never cached, so the next ask
# misses and draws fresh -- and stale only for an in-place overwrite
# of an existing name through that same silent call, which nothing in
# this plugin does (ensure_ramps_installed skips names that exist).
# Clearing is cheap either way: the next draw refills what it needs.
# Failures are NOT cached: a lookup returning None usually means a
# ramp not installed yet, and caching that would outlive the install
# if a signal were ever missed.
_RAMP_ICON_CACHE = {}
_RAMP_ICONS_WATCHED = []


def _forget_ramp_icons(*_ignored):
  """Drop every cached swatch; the next draw rebuilds what it needs."""
  _RAMP_ICON_CACHE.clear()


def _watch_the_style_library():
  """Connect the cache's invalidation to QGIS's own style signals.

  Done on first use rather than at import, because QgsStyle wants a
  running QgsApplication and this module is imported before one
  exists in some harnesses.

  Signals are connected through ``getattr`` and each is optional, as
  ``_watch_layer`` does for layers: the list is QGIS's, a future
  release may rename one, and a missing signal should cost a stale
  swatch rather than an exception on the first table build.
  """
  if _RAMP_ICONS_WATCHED:
    return
  _RAMP_ICONS_WATCHED.append(True)      # even if the connecting fails
  try:
    from qgis.core import QgsStyle
    style = QgsStyle.defaultStyle()
    for name in ("entityAdded", "entityChanged", "entityRemoved",
                 "entityRenamed", "rampAdded", "rampChanged",
                 "rampRemoved", "rampRenamed", "styleChanged"):
      signal = getattr(style, name, None)
      if signal is not None:
        signal.connect(_forget_ramp_icons)
  except Exception:
    # No style library yet, or a QGIS that names none of these. The
    # cache still works; it simply will not hear about a change, and
    # the un-cached behaviour was to redraw every time anyway.
    pass


def same_destination(one, other):
  """Whether two output paths name the SAME FILE.

  Args:
    one: a path as the file widget or a layer source gives it, or an
      empty value for "no file, draw into memory".
    other: the same, to compare against.

  Returns:
    True when both name no file at all, or when both resolve to one
    file on disk. False otherwise.

  WHY NOT `a == b`. It was, and on 2026-08-17 a Windows CI runner
  showed what that costs: the dialog held a path through the user
  directory's 8.3 SHORT NAME (the truncated form ending in a tilde and
  a digit) where the widget held the long name. One file, two
  spellings. Compared as strings they differ, so
  `_add_output_layers` read the destination as CHANGED and built a
  rival group beside the one it had just adopted: the invisible double
  map, on the platform most of this plugin's users are on, and
  invisible on macOS and Linux where the two spellings never arise.

  `realpath` resolves the short name and any symlink; `normcase`
  folds the case and the separator, which Windows needs and which is
  a no-op elsewhere. This is the "identifiers that differ only in
  case" family: a name leaving Python for a filesystem can come back
  spelt differently, and comparing what came back against what went
  out is what fails.

  A path that cannot be resolved -- a file not yet written, a
  disconnected drive -- falls back to the normalised string, since
  refusing to answer is worse than answering approximately.
  """
  if not one and not other:
    return True
  if not one or not other:
    return False

  def settled(path):
    """One path reduced to a form two spellings of it will share.

    Args:
      path: the path to normalise.

    Returns:
      The resolved, case-folded path, or the case-folded original
      when the filesystem cannot resolve it.
    """
    try:
      return os.path.normcase(os.path.realpath(path))
    except (OSError, ValueError):
      return os.path.normcase(path)

  # ASK THE FILESYSTEM FIRST, because it is the authority on whether
  # two names are one file and the answer differs per VOLUME. Added
  # 2026-08-17, hours after this function, when a hunt showed the hole
  # its fixture had hidden: `normcase` is identity on POSIX and
  # `realpath` does not fold case, while APFS does -- so `Output.gpkg`
  # and `output.gpkg` are one file on this Mac and compared as two.
  # Measured by two routes: two Generates produced `WeavingSpace
  # tiles` and `WeavingSpace tiles 2` over ONE file on disk, and after
  # an adoption the two groups read the same four tables. The double
  # map, on the developer's own platform, through the very fix written
  # to prevent it.
  #
  # A blanket casefold would be WRONG on a case-sensitive volume,
  # where those really are two files. `samefile` compares device and
  # inode, so the volume decides -- and it answers Windows' short
  # names too.
  try:
    if os.path.samefile(one, other):
      return True
  except OSError:
    # one of them does not exist yet, which is ordinary: a GeoPackage
    # names where output is GOING. Fall through to the string form,
    # whose remaining gap is two case-differing spellings of a file
    # that has not been written -- once it exists, the check above
    # settles it.
    pass
  return settled(one) == settled(other)


def same_source(one, other):
  """Whether two layer sources name the SAME DATASET.

  Args:
    one: a source string as `QgsVectorLayer.source()` gives it, or as
      the plugin stamped it into `weavingspace_region`.
    other: the same, to compare against.

  Returns:
    True when both are empty, or when both name one file and the same
    layer inside it. False otherwise.

  WHY NOT `a == b`, which is what six sites did until 2026-08-26. A
  source is a PATH plus a provider tail (`|layername=tiles_a_v1`),
  and the path half comes back from a project file spelt however QGIS
  chose to write it: on Windows the plugin stamps
  `C:\\WORKSP~1\\...\\region.gpkg|layername=region` and reads
  back `C:/workspace/.../region.gpkg|layername=region`. One
  dataset, two spellings, compared as two datasets.

  WHAT THAT COST, measured on a Windows runner six CI rounds running:
  a reopened project's output group appeared to have been made from
  ANOTHER dataset, so the guard that protects a kept result refused
  the ordinary recovery run -- through a QMessageBox, which never
  reaches the message bar, so the user meets a Generate that produces
  nothing and says nothing. The same comparison decides which group a
  dataset owns, whether the landing may write over a group, and
  whether the resume finds a layer already open, so the fault reaches
  every one of the group-unit rulings on the platform most of this
  plugin's users are on.

  The file half is delegated to `same_destination`, which asks the
  filesystem first (device and inode, so the volume decides about
  case, and Windows short names resolve) and falls back to a
  normalised string for a file not yet written. The tail is compared
  case-folded, because a GeoPackage folds table names too.
  """
  if not one and not other:
    return True
  if not one or not other:
    return False
  one_path, _, one_tail = str(one).partition("|")
  other_path, _, other_tail = str(other).partition("|")
  if not same_destination(one_path, other_path):
    return False
  return one_tail.strip().lower() == other_tail.strip().lower()


def _ramp_icon(name: str, reverse: bool = False):
  """Small preview swatch (a QIcon) for a named colour ramp.

  Cached per (name, direction); see _RAMP_ICON_CACHE above for what
  clears it.

  Args:
    name: a ramp in QgsStyle.
    reverse: draw it running the other way, so the swatch shows the
      direction the map will actually use.

  Returns:
    A QIcon, or None when the ramp or the API is unavailable.

  QgsStyle.defaultStyle() is the user's style library (a sqlite DB of
  named symbols and colour ramps shared across all of QGIS); ramps are
  looked up in it by name.
  """
  _watch_the_style_library()
  key = (name, bool(reverse))
  cached = _RAMP_ICON_CACHE.get(key)
  if cached is not None:
    return cached
  try:
    # bridge.get_ramp clones and, when asked, reverses; the swatch
    # therefore shows the direction the map will actually use
    ramp = bridge.get_ramp(name, reverse)
    if ramp is None:
      return None
    # Drawn through the SAME construction as a Custom swatch (user
    # instruction, 2026-08-09): equal vertical stripes of sampled
    # colours, not QGIS's continuous gradient preview. Two cells side
    # by side in one column should differ in what they SHOW, never in
    # how they are drawn -- a gradient beside a striped swatch reads
    # as two kinds of thing, and the Custom swatch is the honest one
    # because a classed map paints steps rather than a gradient.
    # Sampled at the ends inclusive (i/(n-1)), which is where the
    # first and last classes of a graduated map take their colours,
    # so the swatch's extremes are the map's extremes.
    stripes = SWATCH_STRIPES
    colours = [ramp.color(i / (stripes - 1)).name()
               for i in range(stripes)]
    # deliberately NOT narrowed by any row's Ramp Display Range:
    # choosing a ramp resets that window (the settled "until
    # reselected anew"), so a windowed preview would promise colours
    # the click itself would discard
    icon = _striped_icon(colours)
    if icon is not None:
      _RAMP_ICON_CACHE[key] = icon
    return icon
  except Exception:
    pass
  return None


# The layout rule, settled 2026-08-09 and ordered deliberately: the
# window never exceeds 1280 logical pixels, the narrowest screen still
# in use, because a wider window is one nobody can see whole. Within
# that, the TABLE comes first -- it never scrolls horizontally, since
# a horizontal scrollbar on a table is invisible in practice and the
# columns to its right go unfound -- and the preview then gives up
# width, down to a floor below which it stops being able to show
# whether shapes read as distinct elements. If those ever conflict,
# narrow COLUMNS, not the preview past its floor.
MAX_WINDOW_WIDTH = 1280

# Extra pixels reserved beside the scrollbar. Qt's own metric and the
# bar it draws disagree by four pixels on this platform, and a table
# short by even one grows a horizontal scrollbar -- the one thing the
# layout rule forbids, because columns past it go unfound. Cheap
# insurance: the window is capped anyway and the preview gives up the
# difference. (2026-08-10.)
SCROLLBAR_SLACK = 6
PREVIEW_FLOOR = 260


# The tooltip for a ramp cell reading "Custom". The wording is the
# user's own (settled 2026-08-09), and sits AT the fifteen-word
# tooltip cap: fifteen words, which the checker allows and one more
# would not.
CUSTOM_RAMP_TOOLTIP = ("Hand-picked colours, a class file, or a narrowed "
                       "range. Choose a ramp to replace them.")


def _striped_icon(colours, boxed=()):
  """The one way this dialog draws a colour swatch.

  Args:
    colours: "#rrggbb" strings in the order they should appear, left
      to right. At most SWATCH_STRIPES are drawn; an empty list gets
      one neutral grey stripe, so a cell never shows an empty icon
      that would read as a failure to draw.
    boxed: which class EDGES carry a bound somebody set, as
      `(index, side)` pairs -- index into the drawn stripes, 0 for the
      first and -1 for the last, and side "left" or "right". Each gets
      a heavy stroke down that edge, which is how the table says "this
      end is yours" without the ramp cell having to claim the ramp is
      no longer the ramp: a pin moves breaks, not colours
      (maintainer's decision, 2026-08-14).
      AN EDGE RATHER THAN THE WHOLE STRIPE since 2026-08-19, on the
      maintainer's design: the record holds FOUR ends and a stripe has
      one outline, so boxing conflated the floor with the low pin and
      left the ceiling with nowhere to be drawn at all -- which is how
      a ceiling somebody had set showed no mark whatever. Four ends,
      four edges, and a class with both bounds set gets both sides.

  Returns:
    A QIcon of equal vertical stripes at RAMP_SWATCH size.

  EVERY swatch in the ramp column goes through here -- the named
  ramps in the dropdown and the Custom swatch alike (user
  instruction, 2026-08-09). Sharing the construction is the point:
  cells in one column should differ in what they show and never in
  how they are drawn, and stripes are the honest shape for both,
  because a classed map paints steps rather than a gradient.
  """
  shown = list(colours)[:SWATCH_STRIPES] or ["#c0c0c0"]
  pixmap = QPixmap(RAMP_SWATCH)
  pixmap.fill(Qt.GlobalColor.transparent)
  painter = QPainter(pixmap)
  width = RAMP_SWATCH.width() / len(shown)
  for i, name in enumerate(shown):
    painter.fillRect(
      QRectF(i * width, 0, width, RAMP_SWATCH.height()), QColor(name))
  # THE SWATCH USED TO HATCH CLASSES NO TILE WEARS, and stopped on
  # 2026-08-17: the maintainer ruled that users are not used to the
  # mark, so it confused rather than helped. What it was FOR is worth
  # keeping in mind before anybody reaches for it again -- a copied
  # ladder can leave classes the receiving column cannot reach, and
  # those are kept rather than dropped, so the emptiness was drawn
  # instead of being left silent. It is now reported in words
  # instead; `bridge.unworn_classes` still answers which classes are
  # empty and other code still asks it.
  # The pin boxes go on over the fills, so an outline is never
  # painted away by the stripe beside it. Drawn in the stripe's own
  # contrasting ink rather than a fixed colour, or the box would
  # vanish on a dark ramp and shout on a pale one.
  for index, side in boxed:
    position = index if index >= 0 else len(shown) + index
    if not 0 <= position < len(shown):
      continue
    fill = QColor(shown[position])
    lightness = (fill.red() * 299 + fill.green() * 587
                 + fill.blue() * 114) / 1000.0
    ink = QColor("#ffffff") if lightness < 128 else QColor("#000000")
    painter.setPen(QPen(ink, 2))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    # ONE EDGE, NOT THE WHOLE STRIPE (maintainer's design, 2026-08-19).
    # A boxed stripe said "something about this class is yours" and
    # made the reader work out which end; the edge says which. It also
    # composes -- a class with both bounds set gets both sides -- and
    # it is what let the ceiling be drawn at all, since the four ends
    # map onto four edges and a stripe has only one outline.
    #
    # INSET BY ONE, because the outermost edges of the icon are the
    # floor and the ceiling: a stroke on the very edge reads as the
    # icon's own border rather than as a mark.
    x = (position * width + 2.5) if side == "left" \
        else ((position + 1) * width - 2.5)
    painter.drawLine(QPointF(x, 1.0),
                     QPointF(x, RAMP_SWATCH.height() - 1.0))
  painter.end()
  return QIcon(pixmap)


def _dump(*parts):
  """Print one diagnostic line when the dump flag is set.

  Args:
    *parts: whatever should appear on the line; each is stringified
      and the lot joined with spaces.

  Returns:
    None, and nothing at all unless WEAVINGSPACE_ADOPT_DUMP is set in
    the environment.

  WHY THE PIECES ARRIVE SEPARATELY rather than as one formatted
  sentence. `tools/text_review.py` collects every prose-looking string
  literal in this package so a person can read it before it ships, and
  a formatted diagnostic looks exactly like a sentence -- two of these
  duly turned up in the review queue asking the maintainer to approve
  "ADOPT {}: layer={} dialog={}". Widening the reviewer's filter to
  exclude them would be the wrong lever, since that filter decides
  what a human reads and this project has already lost three live
  sentences to one that threw too much away. Short labels are not
  prose, so nothing has to be excluded.

  These dumps exist because reasoning about which rebuild writes a
  record cost two reverted fixes; instrumenting it named the sequence
  in one run. Kept behind the flag for the next investigation.
  """
  if os.environ.get("WEAVINGSPACE_ADOPT_DUMP"):
    print(" ".join(str(part) for part in parts), flush=True)


def _custom_swatch_icon(colours, boxed=()):
  """The swatch drawn while a ramp cell reads "Custom".

  Args:
    colours: the element's actual colours as "#rrggbb" strings, in
      class order, exactly as the renderer would paint them --
      unsorted and unfiltered, so the swatch samples the map rather
      than presenting a tidied summary of it.
    boxed: stripe indices carrying a pinned bound; see _striped_icon.

  Returns:
    A QIcon of the first colours as equal vertical stripes, drawn by
    _striped_icon, which is also what every named ramp's swatch goes
    through.
  """
  return _striped_icon(colours, boxed)


# The fewest decimal places any number box in this dialog may have,
# whatever its own step suggests. The significant-figures sweep is a
# DISPLAY rule and `decimals` is not a display setting: it decides
# what the box can hold and store as well as what it prints. Three is
# the maintainer's figure, 2026-08-17, sized so a half-degree rotation
# and a quarter-unit inset both survive being typed. Costs nothing to
# look at, because every box here trims its own trailing zeros.
_LEAST_FIGURES_DECIMALS = 3


class SpacingSpinBox(TrimmedSpinBox):
  """A spacing box that keeps its precision and shows no idle zeros.

  Spacing spans 1e-6 to 1e12, twelve orders of magnitude, so it is the
  one control no single `decimals` suits: enough for a floor plan at
  half a metre is far too many for a country at fifty kilometres, and
  that is what produced "500.000000" in the field report of
  2026-08-17.

  THE FIRST FIX FOR THAT WAS WRONG AND IS WORTH RECORDING, because the
  mistake is easy to repeat. It sized `decimals` from the spacing
  auto-fitting had just computed -- 500 gives three significant
  figures at zero decimals -- and a QDoubleSpinBox with zero decimals
  cannot REPRESENT 500.5. So typing 500.5 gave 501, typing 215.509124
  gave 216, and the map was tiled from the rounded number with nothing
  said. `decimals` governs display AND input AND storage, so any rule
  that lowers it to tidy the display destroys data.

  Trimming the TEXT costs none of that, and it was always the whole of
  the complaint: nobody objected to the precision, they objected to
  six zeros after a round number. So the box keeps its six decimals
  and simply does not print zeros it does not need.

  THE TRIMMING ITSELF MOVED TO `widgets.TrimmedSpinBox` on 2026-08-17,
  when the class-bound boxes were widened and needed exactly the same
  thing. It lived here in full for a day, and a second copy was
  written in `category_editor.py` before anybody noticed the two would
  have to learn about locales separately. This class keeps only what
  is about SPACING; the shared behaviour is documented where it lives.
  """


class ModeCombo(QComboBox):
  """The style chooser, able to DISPLAY "Custom" without listing it.

  An element whose class boundaries came from somewhere other than its
  scheme shows "Custom" in this cell, because a scheme name would be a
  control lying about the map: the ladder QGIS is drawing was not cut
  by quantiles, however the row still reads "Quant: Quantiles".

  THE CONVENTION IS ITS SIBLING'S, deliberately. ``RampCombo`` solved
  this once for colour and the answer is the same here: only the
  CLOSED combo's painting is overridden, so the popup list, the model,
  the current index and every signal are untouched. "Custom" is never
  an ITEM -- every scheme stays selectable at all times, which is an
  explicit user requirement for the ramp cell and holds here for the
  same reason -- and the underlying index stays on the last-picked
  scheme, so choosing one reclassifies and retires the stored ladder
  through the existing degrade-to-pins rule.

  WHEN IT IS ON: whenever the pinned record holds `breaks`, a whole
  ladder somebody else decided, from EITHER door -- a boundary
  retyped in QGIS's Symbology panel, or Copy classification from
  another element. One record, one description (maintainer's
  decision, 2026-08-20).

  WHEN IT IS OFF: pins alone. A `low` or `high` pin takes one class
  out of the pool and the scheme genuinely still cuts the rest, so
  saying Custom would deny a scheme that is doing most of the work;
  `floor` and `ceiling` move no boundary at all.

  Args:
    parent: the owning widget, as usual in Qt.
  """

  def __init__(self, parent=None):
    super().__init__(parent)
    self._custom = False

  def set_custom_display(self, on):
    """Show or clear the Custom display.

    Args:
      on: True to paint "Custom" over the closed combo, False to go
        back to painting whatever scheme is selected.

    Returns:
      None. Repaints unconditionally, since the same state reached
      twice must still reach the screen.
    """
    self._custom = bool(on)
    self.update()

  def showing_custom(self) -> bool:
    """Whether the closed combo currently reads Custom."""
    return self._custom

  def paintEvent(self, event):  # noqa: N802 (Qt API)
    """Qt calls this to draw the CLOSED combo; the popup draws its own
    items and is never affected. The text is swapped inside the style
    option Qt was about to draw anyway, so platform styling, the focus
    ring and the drop-down arrow all stay native."""
    if not self._custom:
      super().paintEvent(event)
      return
    painter = QStylePainter(self)
    option = QStyleOptionComboBox()
    self.initStyleOption(option)
    option.currentText = "Custom"
    painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
    painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)


class RampCombo(QComboBox):
  """The colour-ramp dropdown, able to DISPLAY "Custom" without
  listing it.

  An element whose colours are partly decided by something other than
  its ramp shows "Custom" in this cell -- hand-picked values or an
  imported class source on a categorized row, positional class picks
  or a narrowed display range on a graduated one -- because a ramp
  name alone would be a control lying about the map. But "Custom"
  must never be an ITEM: every standard ramp
  stays selectable at all times (an explicit user requirement), and an
  item the user could choose would need a meaning to give it. So only
  the CLOSED combo's painting is overridden; the popup list, the
  model, the current index and every signal are untouched.

  The underlying index deliberately stays on the last-picked ramp. A
  class source or a hand-pick governs only the values it names, and
  the ramp still colours the leftovers (pinned by
  test_a_class_source_that_does_not_match_the_data), so there is
  always a real ramp underneath the Custom display and the dropdown
  still reaches it.

  Args:
    parent: the owning widget, as usual in Qt.
  """

  def __init__(self, parent=None):
    super().__init__(parent)
    # None means "paint normally"; a QIcon means "paint the Custom
    # display, with this swatch of the element's actual colours"
    self._custom_icon = None
    # a swatch whose pinned ends are boxed, shown BESIDE the ramp's
    # own name; Custom outranks it when both apply
    self._pinned_icon = None

  def set_custom_display(self, icon):
    """Show or clear the Custom display.

    Args:
      icon: a QIcon of the element's actual colours to draw as the
        swatch, or None to return to painting the current ramp.

    Returns:
      None. Only the closed combo's painting changes; items, index
      and signals are untouched, so a dropdown the user has open
      cannot be disturbed (the chooser-race rule).
    """
    self._custom_icon = icon
    # repaint unconditionally: a fresh swatch for an unchanged state
    # (one more colour picked) must also reach the screen
    self.update()

  def set_pinned_display(self, icon):
    """Show the ramp's NAME beside a swatch that boxes a pinned end.

    Args:
      icon: a QIcon of the element's classes with its pinned ends
        outlined, or None to return to the plain ramp swatch.

    Returns:
      None. Unlike set_custom_display this leaves the TEXT alone, and
      that is the whole point: a pin moves breaks, not colours, so
      the cell goes on naming the ramp it really is drawing while the
      box says which end the user set (maintainer's decision,
      2026-08-14). Custom outranks it -- an element with hand-picked
      colours is Custom whether or not it is also pinned.
    """
    self._pinned_icon = icon
    self.update()

  def showing_custom(self) -> bool:
    """Whether the closed combo currently reads Custom."""
    return self._custom_icon is not None

  def paintEvent(self, event):  # noqa: N802 (Qt API)
    """Qt calls this to draw the CLOSED combo; the popup draws its own
    items and is never affected. When the Custom display is on, the
    text and icon are swapped inside the style option Qt was about to
    draw anyway, so platform styling, the focus ring and the drop-down
    arrow all stay native."""
    if self._custom_icon is None and self._pinned_icon is None:
      super().paintEvent(event)
      return
    if self._custom_icon is None:
      # pinned but not custom: Qt draws the combo as it always would,
      # with the ramp's own name, and only the swatch is swapped
      painter = QStylePainter(self)
      option = QStyleOptionComboBox()
      self.initStyleOption(option)
      option.currentIcon = self._pinned_icon
      option.iconSize = RAMP_SWATCH
      painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
      painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)
      return
    painter = QStylePainter(self)
    option = QStyleOptionComboBox()
    self.initStyleOption(option)
    option.currentText = "Custom"
    option.currentIcon = self._custom_icon
    option.iconSize = RAMP_SWATCH
    painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
    painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)


# The one live dialog in this QGIS session, if any. The plugin reuses
# a single dialog, but nothing stopped a second one existing: reloading
# the plugin (routine while developing, and QGIS's Plugin Reloader does
# it constantly) leaves the previous instance alive with its timers
# running and possibly a tiling in flight. Since a new dialog adopts
# the existing output group, two instances would write to the same
# layers, each unaware of the other. One at a time, enforced.
_LIVE_DIALOG = None

# Where the one-at-a-time rule REALLY keeps its record. A module
# global is not enough: QGIS's Plugin Reloader re-executes this
# module, which resets `_LIVE_DIALOG = None` above, and the dialog
# built from the reloaded class then retires nothing -- the
# predecessor keeps its timers running against the group the newcomer
# has just adopted. So the reference is parked on the QApplication
# instance, which outlives every plugin reload, under this key; the
# module global stays as the fallback for the rare case where there
# is no application object (some headless uses).
_LIVE_KEY = "weavingspace_live_dialog"

# ...and beside it, a plain STRING naming which dialog that record is
# about. Parking the object on the QApplication solved the reload
# problem and created a worse one: nothing cleared the property when
# the dialog was destroyed, so the application went on holding a
# pointer to freed memory, and merely READING it segfaulted QGIS --
# not raising, not returning None, crashing the host application.
# Measured 2026-08-16: destroy the dialog, then recolour any element
# layer in QGIS's styling dock, and the styleChanged handler dies in
# _live_dialog at the property read. Reachable in ordinary use,
# because Plugin Reloader destroys the previous dialog and the output
# layers outlive it.
# Checking the object for deadness cannot work -- the crash IS the
# read -- so the record is cleared while the dialog is still alive
# enough to say so, from its own destroyed signal. The token is what
# makes that safe: a dialog being destroyed AFTER its successor
# registered must not clear the successor's record, and comparing
# tokens is the only comparison available once the object is gone.
_LIVE_TOKEN_KEY = "weavingspace_live_dialog_token"


def _dialog_is_gone(dialog):
  """Whether a dialog's C++ half has been destroyed under Python.

  Args:
    dialog: a WeavingSpaceDialog, or None.

  Returns:
    True when the object must not be touched -- it is None, sip
    reports the wrapped C++ object deleted, or the dialog has been
    RETIRED because the plugin is being unloaded. False when it is
    safe, and False as well when sip cannot be imported, since
    refusing to work is worse than the rare crash this guards.

  RETIREMENT IS ASKED HERE because this is the question every
  long-lived handler puts first, and the alternative lever does not
  work: the neighbouring gate reads "if there IS a live dialog and it
  is not me, drop", so clearing that record makes every dialog think
  it is in charge rather than none. A plugin the user disabled went on
  adopting dock edits, rewriting the project's group record and
  speaking into QGIS's message bar until QGIS was restarted.
  (2026-08-27.)

  Qt disconnects a signal from a BOUND METHOD when the receiving
  QObject dies, but a LAMBDA is an ordinary Python object that Qt
  keeps alive and goes on calling. An element layer outlives the
  dialog that made it, so its styleChanged lambda fires into a dead
  dialog and reaches a deleted QTableWidget. Guarding at the handler
  covers every route by which the connection can survive, which
  disconnecting at one teardown site would not.
  """
  if dialog is None:
    return True
  # IS IT DELETED FIRST, AND THE ORDER IS THE WHOLE OF IT. This guard
  # exists to be safe on an object that may already be dead, so it may
  # not TOUCH that object before asking. The retirement check below
  # went in above this one on 2026-08-27 -- "asked before sip, because
  # it is cheaper" -- and reading any attribute off a deleted wrapper
  # raises `RuntimeError: wrapped C/C++ object ... has been deleted`,
  # from inside a Qt slot, which took the whole suite down with
  # `Fatal Python error: Aborted` at the one test that destroys a
  # dialog and then pokes it. Cheaper is not a reason to ask a
  # question of something that may not be there.
  try:
    from qgis.PyQt import sip
  except Exception:
    sip = None
  if sip is not None:
    try:
      if sip.isdeleted(dialog):
        return True
    except Exception:
      return False
  # A RETIRED DIALOG IS GONE AS FAR AS EVERY HANDLER IS CONCERNED,
  # though its Python object is perfectly alive: QGIS unloading the
  # plugin takes the menu entry and the reference away, so there is no
  # route back to this window and nothing it does can be seen or
  # undone. Asked only once the object is known to be live -- and
  # still defensively, since being wrong here must never raise into a
  # Qt slot.
  try:
    return bool(getattr(dialog, "_retired", False))
  except Exception:
    return True


def _forget_live_dialog(token):
  """Drop the live-dialog record, if it is still the one named.

  Args:
    token: the string identifying the dialog whose destruction is
      being reported.

  Returns:
    None. Does nothing when the record has since moved to another
    dialog, which is the case this exists to get right.
  """
  global _LIVE_DIALOG
  try:
    from qgis.PyQt.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
      _LIVE_DIALOG = None
      return
    # reading the TOKEN is safe where reading the dialog is not: it
    # is a string, and holds no pointer into the dead object
    if app.property(_LIVE_TOKEN_KEY) != token:
      return
    app.setProperty(_LIVE_KEY, None)
    app.setProperty(_LIVE_TOKEN_KEY, None)
  except Exception:
    pass
  _LIVE_DIALOG = None


def _live_dialog():
  """The dialog currently in charge, across module reloads.

  Returns:
    The live WeavingSpaceDialog, or None. Read from the QApplication
    instance first (it survives a plugin reload, and this module does
    not), falling back to the module global.
  """
  try:
    from qgis.PyQt.QtWidgets import QApplication
    app = QApplication.instance()
    if app is not None:
      return app.property(_LIVE_KEY)
  except Exception:
    pass
  return _LIVE_DIALOG


def _set_live_dialog(dialog):
  """Record which dialog is in charge, where a reload cannot forget.

  Args:
    dialog: the dialog taking over, or None to clear the record.

  Returns:
    None. Written to BOTH the application property and the module
    global, so either route answers correctly whichever module object
    a caller happens to be running in.
  """
  global _LIVE_DIALOG
  _LIVE_DIALOG = dialog
  token = f"weavingspace-dialog-{id(dialog)}" if dialog is not None else None
  try:
    from qgis.PyQt.QtWidgets import QApplication
    app = QApplication.instance()
    if app is not None:
      app.setProperty(_LIVE_KEY, dialog)
      app.setProperty(_LIVE_TOKEN_KEY, token)
  except Exception:
    pass
  if dialog is None:
    return
  # The record must not outlive what it points at. `destroyed` fires
  # while the object is going away, which is the last moment anything
  # can safely say so -- afterwards the property read itself crashes.
  # The token travels by default argument rather than by capturing
  # `dialog`, since a closure holding the dialog would keep a
  # reference to the very object whose death is being reported.
  try:
    dialog.destroyed.connect(
      lambda *_ignored, t=token: _forget_live_dialog(t))
  except Exception:
    pass


class ToggleSwitch(QAbstractButton):
  """A small sliding on/off switch: a knob that moves left to right.

  Qt has no switch widget, and the usual workaround -- a QCheckBox
  with a stylesheet -- renders differently on every platform and
  theme, which is precisely what a table full of them would show up.
  Painting it directly is a few lines and looks the same everywhere.

  It is an ordinary QAbstractButton, so everything a checkbox offers
  still works: setChecked/isChecked, the toggled signal, space to
  operate it from the keyboard, and the disabled state.

  Args:
    parent: the owning widget, as usual in Qt.
  """

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setCheckable(True)
    self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    self.setFixedSize(34, 18)
    self.setCursor(Qt.CursorShape.PointingHandCursor)

  def sizeHint(self):  # noqa: N802 (Qt API)
    """The size Qt should give this switch when it can choose.

    Returns:
      A QSize wide enough for the knob to travel visibly, and short
      enough to sit in a table row without stretching it.
    """
    return QSize(34, 18)

  def paintEvent(self, _event):  # noqa: N802 (Qt API)
    """Draw the track, then the knob at whichever end applies.

    Colours come from the widget's palette rather than being
    hard-coded, so the switch follows a light or dark QGIS theme
    without knowing anything about it.
    """
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    palette = self.palette()
    on = self.isChecked()
    enabled = self.isEnabled()
    track = palette.color(palette.ColorRole.Highlight) if on \
      else palette.color(palette.ColorRole.Mid)
    if not enabled:
      track.setAlpha(70)
    radius = self.height() / 2
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(track))
    painter.drawRoundedRect(0, 0, self.width(), self.height(),
                            radius, radius)
    knob = palette.color(palette.ColorRole.Base)
    if not enabled:
      knob.setAlpha(150)
    painter.setBrush(QBrush(knob))
    inset = 2
    diameter = self.height() - 2 * inset
    x = (self.width() - diameter - inset) if on else inset
    painter.drawEllipse(int(x), inset, diameter, diameter)
    if self.hasFocus():
      painter.setPen(QPen(palette.color(palette.ColorRole.Highlight), 1))
      painter.setBrush(Qt.BrushStyle.NoBrush)
      painter.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1,
                              radius, radius)
    painter.end()


class TilePreview(QWidget):
  """Live preview of the tile unit, painted directly with Qt.

  This deliberately does not use matplotlib (absent from some QGIS
  installs) nor a QGIS map canvas (heavyweight): shapely polygon
  coordinates from the weavingspace unit are transformed to widget
  pixels and painted with QPainter, Qt's low-level drawing API. A
  QWidget subclass repaints by overriding ``paintEvent``; calling
  ``self.update()`` schedules such a repaint.
  """

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setMinimumSize(280, 280)
    self._polys = []
    self._ids = []
    self._id_colours = {}
    # (tile_id, x, y, w, h) per central-unit tile: label anchor at the
    # tile's label anchor plus its bounds, so labels can be skipped on
    # tiles that draw too small to carry one. The anchor is the
    # CENTROID, with representative_point() only as the fallback when
    # the centroid falls outside a concave tile -- naming
    # representative_point here was left over from before that change,
    # which was made because it put labels visibly off-centre
    self._labels = []
    self._message = "Pick a design to preview it."

  def show_unit(self, unit, id_colours: dict, shells: int = 0):
    """Show a tile unit, optionally with rings of neighbours.

    Args:
      unit: the Tileable to draw.
      id_colours: {tile_id: colour} for the elements, carrying alpha
        so an element's opacity shows.
      shells: 0 draws the unit alone; 1 or more adds that many rings
        of translated copies around it. The dialog defaults to 1,
        because insetting and the way tiles meet across a join are
        invisible in a unit shown by itself.

    Returns:
      None; the widget repaints itself.
    """
    try:
      if shells <= 0:
        patch = unit.tiles
      else:
        patch = unit.get_local_patch(r=shells, include_0=True)
      polys = []
      for tid, shp in zip(patch.tile_id, patch.geometry):
        geoms = shp.geoms if hasattr(shp, "geoms") else [shp]
        for g in geoms:
          if g.is_empty or not hasattr(g, "exterior"):
            continue
          rings = [list(g.exterior.coords)] + \
                  [list(r.coords) for r in g.interiors]
          polys.append((tid, rings))
      self._polys = polys
      self._ids = sorted({p[0] for p in polys},
                         key=bridge.element_order)
      self._id_colours = id_colours
      # label the central unit's tiles with their ids, as the web
      # app's design view does. The centroid is the visual centre and
      # the right anchor for (near-)convex tiles; representative_point
      # is only the fallback for concave shapes whose centroid falls
      # outside them (anchoring everything at representative_point put
      # labels visibly off-centre on asymmetric pentagons, since that
      # point comes from a bbox-midheight scanline, not the centre)
      labels = []
      for tid, shp in zip(unit.tiles.tile_id, unit.tiles.geometry):
        geoms = shp.geoms if hasattr(shp, "geoms") else [shp]
        for g in geoms:
          if g.is_empty or not hasattr(g, "exterior"):
            continue
          point = g.centroid
          if not g.contains(point):
            point = g.representative_point()
          x0, y0, x1, y1 = g.bounds
          labels.append((tid, point.x, point.y, x1 - x0, y1 - y0))
      self._labels = labels
      self._message = None if polys else "Nothing to draw."
    except Exception as e:  # keep UI alive whatever the library does
      self._polys, self._labels = [], []
      self._message = f"Preview failed:\n{e}"
    self.update()

  def show_message(self, text: str):
    """Replace the drawing with a centred message (errors, prompts)."""
    self._polys, self._labels, self._message = [], [], text
    self.update()

  def paintEvent(self, event):  # noqa: N802 (Qt API)
    """Fit the stored polygons to the widget and draw them.

    Map y grows upward, widget y grows downward, hence the flip in
    ``to_screen``. Ring coordinates come straight from shapely
    (exterior plus interior rings); QPainterPath's even-odd filling
    makes holes render correctly without extra work.
    """
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(self.rect(), QColor("#fafafa"))
    if not self._polys:
      painter.setPen(QPen(QColor("#666666")))
      painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       self._message or "")
      painter.end()
      return
    # Fit EVERYTHING drawn — the unit and every context shell — into
    # the widget. The extent comes from all rings of all polygons, not
    # only their exteriors and not only the central unit, so raising
    # the shell count zooms out rather than running off the edge.
    xs = [x for _, rings in self._polys for ring in rings for x, _y in ring]
    ys = [y for _, rings in self._polys for ring in rings for _x, y in ring]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = max(x1 - x0, 1e-9), max(y1 - y0, 1e-9)
    margin = 8
    scale = min((self.width() - 2 * margin) / w,
                (self.height() - 2 * margin) / h)
    ox = (self.width() - scale * w) / 2
    oy = (self.height() - scale * h) / 2

    def to_screen(x, y):
      return (ox + (x - x0) * scale,
              self.height() - (oy + (y - y0) * scale))

    for tid, rings in self._polys:
      path = QPainterPath()
      for ring in rings:
        pts = [to_screen(x, y) for x, y in ring]
        path.moveTo(*pts[0])
        for p in pts[1:]:
          path.lineTo(*p)
        path.closeSubpath()
      colour = self._id_colours.get(
        tid, bridge.ID_COLOURS[
          self._ids.index(tid) % len(bridge.ID_COLOURS)])
      painter.setBrush(QBrush(QColor(colour)))
      # No outline. The design view shows a unit and its neighbours as
      # areas of colour, and a dark line around every tile competes
      # with the thing being judged: whether the shapes read as
      # distinct elements by their COLOUR and form. A hairline also
      # thickens relative to the tiles as the pattern gets finer, so
      # at small spacings the preview turned into a mesh. Tile
      # boundaries on the MAP are a separate, deliberate control
      # ("Draw tile boundaries" on the Data & colours tab) and are
      # unaffected by this.
      painter.setPen(Qt.PenStyle.NoPen)
      painter.drawPath(path)

    # subtle tile-id labels on the central unit, as in the web app's
    # design view: semi-transparent, luminance-aware (dark ink on
    # light fills, light ink on dark), and only where the tile draws
    # large enough to carry a letter without clutter
    # the app's own font size, so the ids read as part of the
    # interface rather than as fine print (the user's ask); the
    # subtlety comes from the alpha, not from shrinking the type
    font = painter.font()
    app_font = QApplication.font()
    if app_font.pointSizeF() > 0:
      font.setPointSizeF(app_font.pointSizeF())
    painter.setFont(font)
    metrics = painter.fontMetrics()
    box = max(metrics.height(), metrics.horizontalAdvance("W")) + 4
    for tid, lx, ly, lw, lh in self._labels:
      # no label on a tile too small to hold one at this type size
      if min(lw, lh) * scale < box:
        continue
      fill = QColor(self._id_colours.get(
        tid, bridge.ID_COLOURS[
          self._ids.index(tid) % len(bridge.ID_COLOURS)]
        if tid in self._ids else "#cccccc"))
      # perceived luminance decides the ink; alpha keeps it subtle
      luminance = (0.299 * fill.red() + 0.587 * fill.green()
                   + 0.114 * fill.blue())
      ink = QColor(255, 255, 255, 170) if luminance < 140 \
        else QColor(0, 0, 0, 130)
      painter.setPen(ink)
      sx, sy = to_screen(lx, ly)
      painter.drawText(int(sx - box / 2), int(sy - box / 2), box, box,
                       Qt.AlignmentFlag.AlignCenter, tid)
    painter.end()


class WeavingSpaceDialog(QDialog):
  """The plugin's one window: design a tile unit, assign variables and
  symbology per element, and generate the tiled map as QGIS layers.

  The flow, in weavingspace terms: the Design tab's controls are the
  arguments to TileUnit/WeaveUnit plus the Tileable transform methods
  (``_build_unit`` performs exactly the web app's construction
  sequence); the Data & colours table maps tile_ids to dataset fields
  and initial symbology; ``_generate`` runs Tiling(...).get_tiled_map()
  in a background task; ``_add_output_layers`` splits the resulting
  GeoDataFrame by tile_id into one QGIS layer each (via bridge.py) and
  manages the layer-tree group across regenerations.
  """

  # element counts offered (the catalogue's keys: every count from 2
  # to 256 for TILINGS, whose ids run a..z then aa..zz, and 2 to 26
  # for weaves, which name their strands one character at a time --
  # see catalog.MAX_ELEMENTS_WEAVE and MAX_ELEMENTS_TILING, which
  # differ on purpose and say why at length)
  N_CHOICES = sorted(catalog.TILINGS_BY_N)
  # entries of the per-row Style dropdown; "Quant: X" rows all mean a
  # graduated (classed numeric) renderer, differing in break method
  # The styles a row can NAME. Every entry but the last is something
  # the plugin draws; DEFERRING is something it stops drawing, and it
  # is in this list rather than outside it because the row must always
  # be a true description of the map (settled 2026-08-15). It is shown
  # ALWAYS and enabled ONLY while the element is deferring: a freely
  # selectable version would need `_plausible_mode`, the text-field
  # correction and the Classes and Reverse columns each to hold an
  # opinion about it, and a chooser that silently grows an item is not
  # trusted.
  DEFERRING = "Deferring to QGIS"
  MODES = ["Quant: Quantiles", "Quant: Equal intervals",
           "Quant: Natural breaks", "Quant: Pretty breaks",
           "Quant: Unclassed", "Categorized", "Single colour",
           DEFERRING]
  GRAD_SCHEMES = {
    "Quant: Quantiles": "Quantiles",
    "Quant: Equal intervals": "Equal intervals",
    "Quant: Natural breaks": "Natural breaks (Jenks)",
    "Quant: Pretty breaks": "Pretty breaks",
    # the web app's continuous look, reproduced with standard QGIS
    # machinery: 50 linearly spaced (equal) intervals reads as an
    # unclassed ramp at map scale while staying a normal graduated
    # renderer in the styling panel
    "Quant: Unclassed": "Unclassed",
  }
  # sequential ramps cycled across rows as defaults (all exist in the
  # QGIS style library, natively or installed by bridge.ensure_ramps_...)
  DEFAULT_RAMPS = ["Reds", "Blues", "Greens", "Purples", "Oranges", "Greys",
                   "YlOrRd", "PuBuGn", "RdPu", "GnBu", "YlGn", "BuPu"]

  def __init__(self, iface, parent=None):
    """iface is QGIS's plugin interface object (QgisInterface); the
    dialog only uses its message bar for success/warning banners, so
    tests pass a small stub instead."""
    super().__init__(parent)
    self.iface = iface
    self.setWindowTitle(
      "WeavingSpace – tiled & woven multivariate maps "
      f"(v{_plugin_version()})")
    # the current weavingspace Tileable (rebuilt by _rebuild_unit) and
    # the in-flight background task, if any (single-flight: _generate
    # refuses to start a second one)
    self._unit = None
    self._task = None
    # regeneration tracking, so Generate replaces rather than piles up:
    # our layer-tree group's name, the project layer id per tile_id,
    # the outline layer's id, each element's last-seeded assignment
    # signature (unchanged signature => keep the user's hand-refined
    # renderer), the last GeoPackage path, and the last full-run
    # signature (used to skip no-op live regenerations)
    self._group_name = None
    # What our output group was CALLED when the run in flight started,
    # or None when no run has started. The landing compares it with
    # the name the group has then, which is how a rename made DURING a
    # run (the user keeping that result) is told from a rename made
    # before it (the group is just called that now). Declared here
    # rather than only where it is set, because the landing reads it
    # on every run including the first.
    self._group_name_at_launch = None
    self._element_layer_ids = {}
    # {tile id: layer id} for the half of an element that draws its
    # missing values. Set up HERE and not only where it is filled: a
    # record several paths read must exist from construction, and
    # relying on getattr defaults at the read sites is how one path
    # sees {} while another sees the real thing.
    self._no_data_layer_ids = {}
    self._outline_layer_id = None
    self._last_signatures = {}
    self._last_path = None
    # TRUE between adopting a group somebody else's session wrote and
    # the first Generate into it. Adoption records that group's file in
    # `_last_path`, so without this the destination the user then
    # chooses reads as a CHANGE and the run builds a rival beside the
    # group it just took over -- see `_add_output_layers`, where this
    # is read and cleared.
    self._adopted_group_unwritten = False
    # {gpkg path: {element ids this dialog wrote into it}}. Kept so a
    # design that SHRINKS can remove the tables its own previous run
    # left behind, and so that it can remove ONLY those: a GeoPackage
    # is an ordinary file somebody may keep other data in, and
    # deleting a table on the strength of its name matching our
    # convention would eventually delete somebody's work.
    self._gpkg_tables_written = {}
    # {(layer id, column, data version): bool} -- see _column_has_nulls
    self._nulls_cache = {}
    # {(layer id, column, data version, floor, ceiling): bool} -- see
    # _limits_exclude_anything. Keyed on the LIMITS as well, because
    # moving a floor must retire the answer without touching the data
    # version, which is about the column changing underneath us.
    self._limit_cache = {}
    # the watched layer's id, recorded by `_layers_going` while the
    # layer still exists, so the removal notice does not depend on
    # which of two Qt handlers runs first
    self._removal_pending = None
    self._last_run_sig = None
    # What each dataset LOOKED LIKE when a map was last drawn from it,
    # keyed by layer id: {layer id: fingerprint}. Keyed rather than a
    # single slot because the fact belongs to a map and a session holds
    # several -- see the note at the landing that writes it. Empty
    # until a run lands, and never persisted: it is a reading of a
    # moment rather than part of any design.
    self._fingerprint_when_drawn = {}
    # the geometry of the last completed run, so a later style-only
    # change can be answered without tiling again
    self._last_geometry_sig = None
    # per-element UI memory, keyed by tile_id so it survives table
    # rebuilds: category counts per (layer id, field), each element's
    # class-source choice, QML files browsed anywhere this session,
    # picked single colours, and last ramp names
    self._cat_count_cache = {}
    self._nulls_cache = {}
    self._limit_cache = {}
    # one field's values, keyed by (layer, field, fingerprint) and
    # holding a single entry: the breaks are cut from these, and a
    # stale set would classify the map against data that has gone
    self._values_cache = {}
    # {(layer id, field): a hashable summary of that column's values}.
    # Filled by the same scan that builds the classification source,
    # and read by _signature so an element is re-seeded when the
    # column it draws actually moves.
    self._value_digests = {}
    # the colour editor while it is showing, or None. Deferral closes
    # it: its rows describe a renderer that has just stopped existing.
    self._open_editor = None
    self._class_choices = {}
    self._browsed_qmls = []
    self._single_colours = {}
    self._ramp_choices = {}
    self._reverse_choices = {}
    self._opacity_choices = {}
    # The scheme SHELF: {tile_id: {field: the whole scheme}} for
    # columns a dataset change dropped -- written by _shelve_scheme,
    # read back by _unshelve_scheme when the element returns to data
    # that has the field. Session-scoped, unlike the stamped colour
    # records; the ruling (CLAUDE.md, 2026-08-21) says what stays
    # ACTIVE changes and what is REMEMBERED does not.
    self._scheme_memory = {}
    # ...AND THE BANKS THE FIELD-KEYED VIEWS ARE SWAPPED THROUGH on a
    # change of dataset (maintainer's ruling, 2026-08-24: NO residue
    # of one dataset -- column names included -- may steer or reach
    # another). {layer id: {"colours", "pins", "shelf"}}. The three
    # field-keyed attributes -- _category_colours, _pinned_bounds,
    # _scheme_memory -- are VIEWS into the current dataset's bank, and
    # _swap_dataset_memory rebinds them. A re-added layer has a new id
    # and forfeits its session memory: documented, not hidden.
    self._dataset_memory = {}
    self._memory_layer_id = None
    # While a layer change is being answered, dropped schemes belong
    # to the dataset they were made ON: the rebuild runs after the
    # swap, so _shelve_scheme writes here when it is set.
    self._pending_outgoing_shelf = None
    # Elements whose scheme was SHELVED and not yet rebuilt. Read and
    # cleared by `_refresh_table`: a shelved scheme must not be
    # refilled from the previous table, and the rebuild's own
    # `column_gone` test cannot see door three, where
    # `_adapt_to_the_layer` re-points the row at a surviving column
    # BEFORE the rebuild runs. Two hunts found that door on
    # 2026-08-25, keeping the ramp and the class count against ruling
    # 3, and the class source going home wearing another dataset's
    # file through the same gap.
    self._scheme_just_reset = set()
    # THE USER ASKED FOR A GROUP OF ITS OWN, by choosing "Create new"
    # in the output-group chooser. Armed there, spent by the next
    # landing, which then re-populates the chooser around the group it
    # has just made.
    #
    # IT REPLACES `_fresh_group_for_new_data`, retired on 2026-08-25
    # with ruling 1. That flag was armed by `_begin_new_dataset` so
    # that the first Generate after a change of dataset could not land
    # on the previous dataset's map -- a proxy for a fact nobody could
    # see. Under the binding the fact is on screen: the chooser says
    # which group a run will land in, and choosing a dataset selects
    # its own most recent group, so B's map lands on B's group because
    # that is what is selected rather than because a flag was set.
    self._new_group_chosen = False
    # True only while `_on_group_chosen` is moving the region chooser
    # on the user's behalf. Choosing a group is RESUMING work, so the
    # protections a change of dataset arms must not fire: they exist
    # to stop B's map replacing A's result, which is answered here by
    # which group is selected.
    self._selecting_a_group = False
    # The elements of a working state being restored, for exactly ONE
    # rebuild. `_refresh_table` normally reads the table it is about
    # to replace, which is the right answer for every other rebuild
    # and precisely the wrong one here: restoring a group means the
    # rows standing there belong to the map being left, not the map
    # being returned to. Set by `_apply_working_state` and cleared by
    # the rebuild that consumes it, so nothing can restore twice.
    self._restoring_assignments = None
    # True once a run has LANDED in this dialog session. It is the
    # second half of what makes a layer change a change of DATASET:
    # see the switched_from_work comment in _on_layer_changed.
    self._landed_this_session = False
    # True between `cleared` and the end of the adoption that
    # follows it, so adoption can tell a choice from an echo.
    self._project_is_being_replaced = False
    # Colours chosen by hand in the Categorical colour editor:
    # {tile_id: {field: {str(value): "#rrggbb"}}}. Keyed by FIELD as
    # well as element so that moving an element to another variable
    # and back restores the work rather than discarding it, and so
    # that two fields sharing a value name ("other", "none", "1")
    # cannot silently colour each other.
    self._category_colours = {}
    # ...AND WHICH OF THOSE THE PLUGIN WROTE ITSELF, because an
    # element whose class-source file has gone keeps the colours it is
    # drawing by having them RECORDED -- the record is what the next
    # run, restyle and reopen read -- and those are not a person's
    # picks. {tile_id: {field: {str(value): "#rrggbb"}}}, the same
    # shape as the record it shadows, so the two can be compared entry
    # by entry: a colour the user has changed since no longer matches
    # and is left alone. (Maintainer's ruling, 2026-08-26: record
    # them, but a restored file wins.)
    self._kept_for_unreadable = {}
    # Graduated (quant) customization, settled 2026-08-09. Class
    # colours picked by hand are keyed POSITIONALLY -- {tile_id:
    # {field: {str(class index): "#rrggbb"}}} -- because a class has
    # no name to follow when its breaks move; per-field so switching
    # a variable away and back restores the work, exactly as the
    # categorical picks do.
    self._quant_colours = {}
    # THE LADDER THE PLUGIN LAST PAINTED, {tile_id: {field: [(lower,
    # upper, "#rrggbb"), ...]}}. Settled by /grill-me on 2026-08-20,
    # replacing a guard computed as a DELTA that was armed for one
    # invocation only (ledger row 2 of that day).
    #
    # WHAT IT IS FOR. When QGIS hands a ladder back, the plugin has to
    # say of each class whether the colour on it is ONE WE PUT THERE
    # or one a person chose, and it cannot ask by index: adding a
    # class renumbers every class above it, so a positional walk sees
    # the plugin's own ramp displaced by one and adopts the lot as
    # somebody's hand-picks. DERIVING what we would draw now cannot
    # answer it either -- once the dock has changed the ladder, what
    # we would draw now is not what we drew then, which is how the
    # first durable attempt over-reached and was withdrawn.
    #
    # WHAT MAKES IT ANSWERABLE, measured on QGIS 4.0.3, 2026-08-20:
    # `addClass` inserts a degenerate (0.0, 0.0) class at index 0
    # wearing the source symbol's grey, and EVERY SURVIVING CLASS
    # KEEPS ITS BOUNDS BIT FOR BIT. So a colour can be matched back to
    # the class it was painted on, exactly, with no tolerance at all.
    #
    # WRITTEN at the three places the plugin can honestly say it knows
    # the ladder -- when it seeds a renderer (both paths), when it
    # adopts a group whose layers it has only just met, and at the end
    # of a dock edit it has finished attributing. NEVER on a follow:
    # the follow brings the ROW up to the layer and runs BEFORE
    # attribution, so refreshing there would record the dock's ladder
    # as ours and declare every colour on it our own.
    #
    # NOT STAMPED, deliberately. A reopened project re-derives it at
    # adoption from the layer in front of it, which is exactly what
    # the baseline means -- "the ladder as we last understood it" --
    # and it keeps the record out of `weavingspace_quant_style`, whose
    # restore whitelist is the shape this project has already been bitten
    # by twice. An ABSENT entry therefore means "we have never seen
    # this element's ladder", which is not the same as "it has not
    # moved" and is read that way at every site.
    self._painted_ladders = {}
    # ...and its categorical twin, {tile_id: {field: {value: colour}}}
    # -- the categories the plugin itself painted, so a dock edit can
    # be told apart from the plugin's own work by attribution rather
    # than by delta, exactly as the graduated side has done since the
    # ruling of 2026-08-20. Absent means "never seen" and DECLINES.
    self._painted_categories = {}
    # {layer id: the last fingerprint taken while that layer's data
    # was READABLE}. Ledger row 4 of 2026-08-20, a regression from the
    # row-32 fix. `_layer_fingerprint` must not call `extent()` on a
    # layer whose source has gone -- that segfaults QGIS outright --
    # so it used to answer `("unavailable",)`, and THAT answer travels
    # into `_geometry_signature`. A changed geometry signature means
    # "re-tile", which is the one thing that cannot be done from data
    # that has gone: `_restyle_only` declined and the refusal was
    # discarded in silence, so a colour picked after the file moved
    # was recorded, never painted and never mentioned.
    #
    # "The source has gone" is NOT "the design you asked for is
    # different", and folding the two together made every reader of
    # that signature treat a moved file as a design change. Answering
    # with the last good reading keeps the signature still, so the
    # restyle runs -- correctly, since it re-seeds renderers on tiles
    # that already exist and needs nothing whatever from the region
    # layer. The RUN still refuses, through `_generate`'s own direct
    # call to `compat.layer_data_is_available`, which is where the
    # refusal belongs and where the moved-file wording already lives.
    self._last_good_fingerprint = {}
    # Class bounds a person set, {tile_id: {field: {"low": float,
    # "high": float}}}. Keyed by field as well as element, like the
    # hand-picked colours, so switching a variable away and back
    # restores the pins rather than applying one column's numbers to
    # another's data. The copy feature on the roadmap extends this
    # record with the boundary VALUES and a per-end pin FLAG; pins
    # alone need only the bounds, and the two are the same statement
    # until a copy separates them.
    self._pinned_bounds = {}
    # {tile_id: (lo, hi)}: the percent window of the ramp the classes
    # sample from (the Ramp Display Range). Absent means the whole
    # ramp. Data-blind, so it survives a field switch; only choosing
    # a ramp resets it.
    self._ramp_ranges = {}
    # {tile_id: class count}. Every other per-element control has had
    # a dict of this shape since the settled decision that these
    # belong to the ELEMENT and not the row widget; the class count
    # alone rode on the spinner's `user_k` property, which is enough
    # to survive a table rebuild (the count comes back through the
    # previous assignments) and not enough to survive a REOPEN, where
    # there are no previous assignments and every row is built fresh
    # on 5. Added 2026-08-13 so a reopened project can be told what
    # the layer's own renderer says. (Maintainer's decision the same
    # day: preserve the row across a save where we can.)
    self._class_counts = {}
    # {tile_id: mode} -- the renderer kind each element was last SYNCED
    # in, which is what tells a deliberate ramp pick from the automatic
    # swap that follows a style change. _sync_row substitutes a
    # qualitative palette when a row turns Categorized carrying a
    # sequential ramp, and that is right: a sequential ramp over
    # categories is a cartographic error nobody chose. It ran on EVERY
    # sync, though, and a sync follows every data-tab change -- so a
    # ramp deliberately picked on a row already sitting in that mode
    # was swapped straight back out, after the pick had destroyed the
    # element's hand-picked colours on its way past. The user paid for
    # a change they did not get. Comparing against the mode at the last
    # sync separates the two cases without depending on which Qt signal
    # arrives first, which is where two earlier attempts foundered.
    # (Found by the stochastic hunt 2026-08-13; maintainer's decision:
    # leave the dropdown offering every ramp, cartographer beware.)
    self._synced_modes = {}
    # {class-source token: (mtime_ns, size)} -- the last reading taken
    # of each QML this session, so that a file which has GONE can keep
    # the stamp it had rather than moving the signature. See
    # _class_source_stamp.
    self._class_source_stamps = {}
    # (layer id, fingerprint) -> (dissolved area, dissolved perimeter),
    # so the live gate can measure the ground without a geometry pass
    # per keystroke; see `_ground_and_edge`.
    self._ground_cache = {}
    # {tile_id: {"Graduated": name, "Categorized": name}} -- the ramp
    # each element last wore in each mode, so a style excursion and
    # back costs nothing. This lived on the combo widget as `last_quant`
    # and `last_cat` until 2026-08-13, which survives a style flip and
    # NOT a table rebuild: any design change rebuilds the table a
    # preview debounce
    # later, so a ramp crossed over before that landed came back as a
    # positional default instead. Every other per-element choice is
    # keyed by tile id for exactly this reason (settled decision).
    self._ramp_memory = {}
    # True while the dialog itself is writing renderers, so the
    # styleChanged watcher (see _on_layer_style_edited) can tell a
    # QGIS-side edit from our own seeding and react only to the first
    self._applying_style = False
    # the mode a person chose, banked per element AND field so a
    # variable's return wears its own style rather than the last
    # field's (maintainer's ruling, 2026-08-26, sparing the picks)
    self._mode_by_field = {}
    # elements whose renderer the LAST run carried over unchanged;
    # _finish_run re-examines them for dock edits made mid-run
    self._preserved_this_run = []
    # elements a user has just TAKEN BACK from QGIS: the row now names
    # a plugin style and the layer has not been re-seeded yet, so it
    # still holds the renderer somebody built in the styling panel.
    # `_refresh_deferring_rows` must leave those rows alone, and must
    # move every other row that reads as deferring.
    #
    # WHICH MOVED LAST IS THE WHOLE QUESTION, and nothing about the
    # pair (row says a style, layer says something unnameable) can
    # answer it: that pair is identical whether a person picked a
    # style a moment ago or pasted a rule-based renderer a moment ago.
    # So it is RECORDED here rather than inferred. Emptied per element
    # as soon as the layer agrees, and dropped the instant a dock edit
    # arrives for that element, because the layer has then moved after
    # the pick.
    self._picked_back = set()
    # {tile_id: layer_id} -- element layers whose repaintRequested has
    # fired and not yet been reconciled. An in-place dock edit emits
    # NO style signal (measured 2026-08-20; see _watch_element_layer),
    # so the repaint the dock asks for afterwards is its only audible
    # trace. A dict rather than a set so a queued entry still knows
    # which layer it was about if the combo moves before the timer
    # drains; the 300 ms coalesces a data edit's double fire and a
    # dock drag's per-tick stream into one read.
    self._repaint_pending = {}
    self._repaint_timer = QTimer(self)
    self._repaint_timer.setSingleShot(True)
    self._repaint_timer.setInterval(300)
    self._repaint_timer.timeout.connect(self._drain_repaint_reconcile)
    # {tile_id: monotonic seconds} -- when a real styleChanged last
    # arrived for the element, written by _on_style_signal and read by
    # the repaint hook so a heard edit's repaint echo is not handled a
    # second time at the drain.
    self._style_signal_at = {}
    # {tile_id: (assignment, bounds, colours)} -- dock edits that
    # arrived while a run was in flight, replayed once it has landed.
    # See _adopt_dock_bounds for why the numbers are kept rather than
    # a note to look again.
    self._adoption_deferred = {}
    # {tile_id: (key, QIcon)} -- the Custom-display swatch, cached
    # against everything that decides an element's colours, because
    # building one means constructing the real renderer against the
    # region layer (see _custom_swatch_for)
    self._custom_swatch_cache = {}
    # THE DIALOG OUTLIVES THE PROJECT, which is the whole reason this
    # connection exists. QGIS keeps one dialog per session, so opening
    # a second project leaves every record below holding the FIRST
    # project's answers -- and the keys collide readily, because tile
    # ids come from the family ("a", "b", "c") and field names repeat
    # across projects drawn from one data schema. Measured 2026-08-15:
    # a low bound pinned at 84.7 in a project whose column ran 0-121
    # was carried into the next project, whose column ran 0-9, where
    # it drew the whole map as a single class 0-84.7 -- a number that
    # column's own data cannot carry and that the plugin REFUSES when
    # somebody types it. The record's own comment already said pins
    # must not apply "one column's numbers to another's data"; this is
    # that rule across a boundary rather than across a field switch.
    # `cleared` fires on File > New and before File > Open, so the
    # stamped records on the incoming project's layers are read into
    # an empty dialog and win, which is also what makes the
    # setdefault in _adopt_row_pins correct rather than merely safe.
    QgsProject.instance().cleared.connect(self._forget_the_last_project)
    # ...AND ADOPT THE INCOMING PROJECT'S OWN GROUP once it has loaded.
    # `cleared` fires first and empties the dialog's records, which
    # stops the next Generate drawing over a map it knows nothing
    # about; but on its own that left the dialog with no group at all,
    # so the run made a SECOND one beside the group the user had just
    # opened and expected to be taken over. A visible extra group beat
    # an invisible double map, which is why it shipped that way, and
    # this is the repair the roadmap named.
    #
    # `readProject` fires after the project's layers exist, so
    # adoption finds them; and it is the same method the constructor
    # calls, so a dialog that survives a File > Open ends up in
    # exactly the state a freshly opened one would be in. Adoption is
    # by the layers' own custom properties rather than by group name,
    # so it cannot be fooled by a project that happens to contain a
    # group called "WeavingSpace tiles".
    QgsProject.instance().readProject.connect(
      lambda _doc: self._on_project_read())
    # AND the project's own removal signal, because the layer chooser
    # is not a reliable witness to its own layer leaving. Measured
    # 2026-08-15 across four arrangements: with ONE polygon layer in
    # the project QgsMapLayerComboBox emits layerChanged (and the
    # notice below fires), with TWO it emits and silently selects the
    # survivor, and with THREE OR MORE IT EMITS NOTHING AT ALL. The
    # dialog then goes on holding a layer QGIS has destroyed: nothing
    # is said, and Generate does nothing whatever -- no map, no
    # refusal, no message. A user with a real project, which is the
    # case with three or more layers in it, meets a plugin that has
    # quietly stopped working.
    # `layersRemoved` carries the ids, which is what makes this safe
    # to ask: the layer object is already gone by then, so anything
    # here must compare ids rather than touch the wrapper.
    # BOTH signals, and the first one is what makes this reliable.
    # `layersRemoved` arrives after the layers are gone -- and after
    # QgsMapLayerComboBox has churned, which with exactly two polygon
    # layers makes it emit layerChanged and quietly select the
    # survivor. If that handler runs first it moves
    # `_watched_layer_id` onto the survivor, so the removal handler
    # then finds nothing of its own among the removed ids and says
    # nothing. Qt does not promise an order between two connections,
    # so this passed on the development Mac and failed on all three
    # CI runners at exactly the two-layer case (2026-08-16).
    # `layersWillBeRemoved` fires BEFORE any of that, so what was
    # about to be lost is recorded while it is still true.
    QgsProject.instance().layersWillBeRemoved.connect(self._layers_going)
    QgsProject.instance().layersRemoved.connect(self._layers_removed)
    # A GROUP RENAMED IN THE LAYERS PANEL IS STILL THE GROUP, and the
    # CHOOSER has to say so. Renaming one is an ordinary act this
    # plugin has already paid for twice, and ruling 1 of 2026-08-25
    # rests on the chooser naming the map a run will land in -- so a
    # chooser still showing the old name is the invisible rule
    # arriving through the control that replaced it. Found by the
    # four-axis matrix on its first run.
    #
    # THE ROOT HEARS A CHILD'S RENAME, measured on QGIS 4.0.3,
    # 2026-08-25: renaming a group under the root emits `nameChanged`
    # there. Connected through `getattr` like the layer watches, since
    # the signal is QGIS's and a future release may move it; a missing
    # signal should cost one refresh, not an exception. Gated like
    # every other connection to something that outlives this dialog.
    tree_root = QgsProject.instance().layerTreeRoot()
    renamed = getattr(tree_root, "nameChanged", None)
    if renamed is not None:
      renamed.connect(self._a_group_was_renamed)
    # which layer auto-spacing last ran for (it must run once per
    # newly chosen layer, never on the combo's spurious re-emissions)
    self._auto_spacing_layer = None
    # WHOSE NUMBER IS IN THE SPACING BOX. True once somebody has typed
    # or stepped one, False while it is whatever the plugin derived --
    # and a typed number survives a change of dataset where a derived
    # one is replaced (maintainer's ruling, 2026-08-25). Pressing Auto
    # hands the choice back, so it clears. Set here rather than in
    # _build_ui, which runs later: the spacing box connects its own
    # handler, and an attribute that does not exist yet raises inside a
    # Qt slot, where the exception is swallowed and takes the rest of
    # the handler with it.
    self._spacing_is_mine = False
    # (layer id, field names) the assignment table was last built
    # for, so a layer choice that lands after the signal can be
    # noticed. See _settle_layer_choice.
    self._table_built_for = None
    # True while the assignment table was last built with no
    # fields to offer, so its empty rows are not mistaken for
    # a user's choice. See _refresh_table.
    self._fieldless_build = True
    # Bumped whenever the region layer tells us it changed. The
    # signatures below include it, so an edit made in QGIS while this
    # dialog is open cannot be mistaken for "nothing has changed".
    self._data_version = 0
    # How many edits have been HEARD on each dataset, keyed by layer
    # id. `_data_version` answers the same question for the session as
    # a whole, which is right for the signatures and wrong for any
    # question about ONE map: a counter that rises when somebody edits
    # another dataset would report every map as moved. Only the
    # watched layer's signals are connected, so a bump is always
    # attributable to the layer in force.
    self._edits_by_layer = {}
    self._watched_layer = None
    # The watched layer's id, kept beside the object because it is
    # what survives the object being destroyed. See _layers_removed.
    self._watched_layer_id = None
    # The last non-zero value each scale control held, so stepping
    # across zero can continue in the direction of travel. See
    # _skip_zero_scale.
    self._last_scale = {}
    self._watched_fields = ()
    # None until a layer is chosen, so choosing the first one is not
    # mistaken for the CRS having been changed underneath us.
    self._watched_crs = None
    # So that losing a layer can be told apart from never having had
    # one: the dialog opens with the combo empty and that is not an
    # event worth reporting.
    self._had_a_layer = False
    # Said once per layer, not once per debounce tick: a warning
    # repeated every 900ms is one a user learns to stop reading.
    self._said_live_cannot_track = False
    # Likewise once per layer: a source that has gone stays gone, and
    # repeating it on every debounce tick teaches the user to ignore
    # the message line.
    self._said_source_gone = False
    self._retire_previous_instance()
    # The ramps come FIRST, and the order is load-bearing as of
    # 2026-08-13. Adoption now reads an existing layer's ramp back
    # off its renderer, which means asking which library ramp draws
    # it -- and this ran two lines before `_ramp_names` existed, so
    # every lookup failed and every adopted element fell through to
    # Custom. The ramps must also be INSTALLED by then, or a project
    # styled with a mapweaver palette reopens unable to name it.
    bridge.ensure_ramps_installed()
    self._ramp_names = bridge.ramp_names()
    self._adopt_existing_group()
    # How long the LAST preview rebuild took, in milliseconds. Zero
    # until one has happened, which is right: the first rebuild of a
    # session has nothing to be slower than, and the floor applies.
    self._last_rebuild_ms = 0.0
    self._preview_timer = QTimer(self)
    self._preview_timer.setSingleShot(True)
    self._preview_timer.setInterval(PREVIEW_DEBOUNCE_MS)
    self._preview_timer.timeout.connect(self._rebuild_unit)
    # live update: from the moment a layer and variables are in
    # place (no button press needed), setting changes regenerate the
    # map automatically (debounced, size-gated, no-op-skipping)
    self._live_timer = QTimer(self)
    self._live_timer.setSingleShot(True)
    self._live_timer.setInterval(LIVE_DEBOUNCE_MS)
    self._live_timer.timeout.connect(self._maybe_live_generate)
    self._live_pending = False
    # A Generate PRESSED while a run is in flight, which is a
    # different fact from a live tick deferred the same way and must
    # not share its flag. `_live_pending` is honoured by starting the
    # live timer, and `_maybe_live_generate`'s second gate returns
    # whenever live update is switched off -- so with the box
    # unticked a press was queued, handed to a path that cannot run
    # it, and lost in silence, with nothing said. Measured
    # 2026-08-28: press Generate on a four-element design while a
    # seven-element run is in flight and the map keeps all seven
    # while the table asks for four, three layers left tagged for
    # elements the design no longer has -- which is what a later
    # dialog adopts the group by. One flag gating two different
    # things, which this project has paid for before.
    self._press_pending = False
    # True once the window has been closed. A closed dialog
    # must not write into the project: the timers can be
    # stopped, but the region layer's signals stay connected
    # and re-arm them. NOT `isVisible()`, deliberately -- the
    # test suite drives live update on dialogs it never
    # shows, so a visibility test would quietly disable the
    # behaviour it was meant to guard.
    self._closed = False
    # {field: how many distinct values it had last run}, so a
    # categorical field that gains or loses a class can be
    # reported: its existing colours will have moved.
    self._category_counts = {}
    self._build_ui()
    self._limit_the_figures_on_show()
    # ...and now that the widget exists, show the path adoption
    # recovered a moment ago. The order is the whole point: adoption
    # runs before the UI is built.
    self._show_the_adopted_path()
    self._update_layer_exclusions()
    # order matters: families must be populated (_on_n_changed) before
    # the layer handler builds the first unit and queues the first
    # automatic render
    self._on_n_changed()
    self._on_layer_changed()
    # ...and LAST, the design of whatever group adoption took over.
    # Last because it restores into widgets the two calls above build,
    # and because it must be able to move the region chooser without
    # `_on_layer_changed` then re-deriving over the top of it.
    self._restore_the_adopted_design()
    # singleShot(0, fn) runs fn on the next event-loop pass, i.e. after
    # pending layout work; sizing any earlier reads stale geometry
    QTimer.singleShot(0, self._fit_to_design)

  # ---------------------------------------------------------------- UI setup

  # Controls whose number is not a rounded setting but a value read
  # off the DATA or typed by a person, where clipping to three
  # figures would change what the software is working from rather
  # than merely how it reads. Each is the "good reason otherwise" the
  # maintainer's rule allows for, and each is named here so that
  # adding one is a decision somebody makes rather than an omission.
  # SPACING IS THE ONE, and its exemption is a parked problem rather
  # than a settled answer. Its range is 1e-6 to 1e12, twelve orders of
  # magnitude, so no single `decimals` is right for both a floor plan
  # at half a metre and a country at fifty kilometres -- and the sweep
  # below runs at CONSTRUCTION, while auto-spacing sets the value
  # later, from the layer. Left to the sweep it took 0 decimals from
  # its step of 1 and would have rounded a legitimate 0.5 m spacing to
  # nothing. What it actually wants is the rule re-applied whenever
  # the value changes, which is a hook worth adding deliberately; it
  # is on ROADMAP.md. Until then this box keeps the six decimals the
  # maintainer complained about, which is the honest state: one
  # control still wrong rather than one control quietly broken.
  #
  # The class-bound boxes, which ARE data-sized on purpose, live in
  # category_editor and this sweep never reaches them.
  FIGURES_EXEMPT = ("spacing_spin",)

  def _limit_the_figures_on_show(self):
    """Show at most three significant figures in every number box.

    Returns:
      None; each `QDoubleSpinBox` the dialog owns has its `decimals`
      set, except any named in `FIGURES_EXEMPT`.

    THE MAINTAINER'S RULE, 2026-08-17: at most three significant
    figures displayed, unless there is good reason otherwise. Six
    decimal places on a spacing in metres is five digits nobody can
    reach and nobody wants -- the arrows cannot move them and the
    data does not warrant them.

    WHY A SWEEP RATHER THAN A NUMBER PER CONTROL. Every box decided
    for itself before this, in five different ways: spacing at six
    decimals, offset at two, aspect at three, the modifier boxes with
    a local `3 if step < 1 else 1`, and six boxes that set nothing at
    all and so got Qt's default two -- which is how the offset ANGLE
    came to read "0.00" degrees. Five rules in five places is what
    produced the inconsistency, and a sixth rule would not have cured
    it. This runs once at construction over whatever boxes exist, so
    a control added next year is right without anybody remembering.

    THE STEP DECIDES AND THE CAP BOUNDS IT, which is the arrangement
    the first attempt had backwards. A control's `singleStep` is its
    own declaration of the smallest amount it is meant to move by:
    step 1 means whole units, and printing three decimals after them
    is noise the arrows can never touch. So the decimals a box would
    need to show its own step are the answer, and three significant
    figures are the ceiling on that answer.

    Counting the ceiling from the VALUE alone does not work, and its
    own first output said so: every box sitting at zero came out with
    three decimals, because zero has no digits to count, so the
    offset angle read "0.000" degrees with a step of one. The step is
    what makes zero legible.

    Where the two genuinely disagree -- a step of 0.01 on a control
    whose values run in the thousands, where three figures are used
    up before the point -- the CAP wins and the arrows move a digit
    that is not shown. That is the maintainer's rule applied
    literally, and the honest repair is to widen the step, so one
    number per control still governs both.

    Costs one pass over the dialog's widgets at construction,
    microseconds once, and nothing whatever per repaint.
    """
    from qgis.PyQt.QtWidgets import QDoubleSpinBox
    # MATCHED BY IDENTITY, NOT BY `objectName`, which the first
    # version used and which is empty on every box here -- so the
    # exemption matched nothing, spacing was swept after all, and its
    # minimum of 1e-6 rounded to zero at 0 decimals.
    # `test_every_control_accepts_the_range_it_should` caught it, on
    # an assertion about ranges rather than about decimals: a silent
    # skip is invisible at the site and shows up somewhere else.
    exempt = {id(getattr(self, name, None))
              for name in self.FIGURES_EXEMPT}
    for box in self.findChildren(QDoubleSpinBox):
      if id(box) in exempt:
        continue
      # what the step itself needs, found by asking rather than by
      # arithmetic on logarithms, which has edge cases at exact powers
      step = abs(box.singleStep())
      needed = 0
      while needed < 3 and step and round(step, needed) != step:
        needed += 1
      # ...and the three-figure ceiling, counted at the control's own
      # scale: the larger of what it holds and what it steps by, so a
      # box resting at zero is still sized by the units it moves in
      scale = max(abs(box.value()), step)
      digits = len(str(int(scale))) if scale >= 1 else 0
      # THREE DECIMALS AT LEAST, on the maintainer's ruling of
      # 2026-08-17, and the reason is the one this project already
      # wrote down about the spacing box and then repeated here.
      # `decimals` governs display AND input AND storage, so a rule
      # that lowers it to tidy the display DESTROYS DATA -- and this
      # sweep had lowered `mod_rotate`, `mod_skew_x/y`,
      # `opt_offset_angle` and `opt_point_angle` to ZERO. Typing 22.5
      # into Rotate swallowed the 5, the unit was built at 22 degrees
      # vertex-for-vertex, and nothing was said. 22.5 is the natural
      # angle for an eight-fold design. Found by a hunt the same day
      # the sweep was written; the sibling that got it right is
      # `widgets.TrimmedSpinBox`, whose docstring names this exact
      # mistake as the tempting one.
      #
      # The display rule is kept by TRIMMING instead: every box here
      # is a TrimmedSpinBox now, so it prints "0" rather than "0.000"
      # and "22.5" rather than "22.500" while still HOLDING whatever
      # somebody types. The cap still bounds what is shown; the floor
      # stops it eating what is stored.
      box.setDecimals(max(_LEAST_FIGURES_DECIMALS,
                          min(needed, max(0, 3 - digits))))

  def _build_ui(self):
    """Construct every widget and wire its signals.

    Layout is nested boxes: a horizontal split (controls left, preview
    right), tabs on the left, and QFormLayouts (label/field rows)
    inside the tabs. Widgets kept as ``self.*`` are read back later by
    ``_unit_kwargs``/``_assignments``; everything else is fire-and-
    forget. Every control that affects the design connects to
    ``_queue_preview``; things that affect only the output connect to
    ``_queue_live``.
    """
    main = QHBoxLayout(self)
    left = QVBoxLayout()
    main.addLayout(left, 5)

    right = QVBoxLayout()
    right.addWidget(QLabel("Tile unit preview"))
    self.preview = TilePreview()
    # 260 is the settled width floor (2026-08-09): below it the
    # preview cannot do its job -- judging whether shapes read as
    # distinct elements by colour and form -- and merely occupies
    # space. The layout rule gives the table its columns first, then
    # lets the preview give up width down to exactly here.
    self.preview.setMinimumSize(PREVIEW_FLOOR, 230)
    right.addWidget(self.preview, 1)
    shells_row = QHBoxLayout()
    shells_row.addWidget(QLabel("Context shells"))
    self.shells_spin = QSpinBox()
    self.shells_spin.setRange(0, 4)
    # One ring of neighbours is the default because a great deal of
    # what a unit does only becomes visible once it is repeated:
    # insetting, how tiles meet across the join, and whether the
    # pattern reads the way it looks in isolation. The unit alone is
    # still one click away for anyone who wants the bare design.
    self.shells_spin.setValue(1)
    self.shells_spin.setToolTip(
      "Rings of neighbouring copies around the unit; "
      "0 shows the unit alone.")
    self.shells_spin.valueChanged.connect(
      self._refresh_preview_colours)
    shells_row.addWidget(self.shells_spin)
    shells_row.addStretch(1)
    right.addLayout(shells_row)
    main.addLayout(right, 2)
    self._design_wrapper = None

    tabs = QTabWidget()
    left.addWidget(tabs, 1)

    # ---- tab 1: design
    design = QWidget()
    form = QFormLayout(design)

    # QgsMapLayerComboBox is QGIS's own layer chooser: it tracks the
    # project's layer list by itself and emits layerChanged
    self.layer_combo = QgsMapLayerComboBox()
    self.layer_combo.setFilters(_polygon_filter())
    self.layer_combo.setToolTip(
      "The polygon layer whose attributes will be mapped. Best not to use "
      "lat-long datasets.")
    self.layer_combo.layerChanged.connect(self._on_layer_changed)
    form.addRow("Region layer", self.layer_combo)

    # THE OUTPUT GROUP, CHOSEN RATHER THAN INFERRED (ruling 1 of
    # 2026-08-25). It sits beside the region chooser because the two
    # are bound: choosing either selects the other. This is not a
    # memory feature -- the group is a QGIS-side artefact that already
    # exists and already carries its dataset in `weavingspace_region`,
    # and it was already being chosen on every run by a rule the user
    # could neither see nor override.
    self.group_combo = QComboBox()
    self.group_combo.setToolTip(
      "Which map to work on, or start another beside it.")
    self.group_combo.activated.connect(self._on_group_chosen)
    form.addRow("QGIS Layer Group", self.group_combo)

    self.n_combo = QComboBox()
    for n in self.N_CHOICES:
      self.n_combo.addItem(str(n), n)
    self.n_combo.setCurrentText("4")
    self.n_combo.setToolTip(
      "How many variables the pattern can carry.")
    self.n_combo.currentIndexChanged.connect(self._on_n_changed)
    form.addRow("Number of elements", self.n_combo)

    self.kind_combo = QComboBox()
    self.kind_combo.addItems(["tiling", "weave"])
    self.kind_combo.setToolTip(
      "Tilings give side-by-side patches; weaves give strands "
      "the eye can follow.")
    self.kind_combo.currentIndexChanged.connect(self._on_kind_changed)
    form.addRow("Tiling or weave", self.kind_combo)

    self.family_combo = QComboBox()
    self.family_combo.setToolTip(
      "The pattern catalogue for the chosen element count.")
    self.family_combo.currentIndexChanged.connect(self._on_family_changed)
    form.addRow("Family", self.family_combo)

    self.spacing_spin = SpacingSpinBox()
    self.spacing_spin.setRange(1e-6, 1e12)
    self.spacing_spin.setDecimals(6)
    self.spacing_spin.setValue(1000)
    self.spacing_spin.setToolTip(
      "The pattern's grain in map units. Try aiming near the typical polygon "
      "width.")
    self.spacing_spin.valueChanged.connect(self._queue_preview)
    # ...and record whose number it now is, before the preview is
    # queued or after, it makes no difference: both connections fire on
    # the same signal and neither reads the other's work.
    self.spacing_spin.valueChanged.connect(self._spacing_typed)
    spacing_row = QHBoxLayout()
    spacing_row.addWidget(self.spacing_spin)
    auto = QPushButton("Auto")
    auto.setToolTip("A coarse value from the layer extent, good for iterating")
    auto.clicked.connect(self._auto_spacing)
    spacing_row.addWidget(auto)
    form.addRow("Spacing (map units)", spacing_row)

    # family-specific options
    self.opt_offset = TrimmedSpinBox()
    self.opt_offset.setRange(-1.0, 1.0)
    self.opt_offset.setSingleStep(0.01)
    self.opt_offset.setDecimals(2)
    self.opt_offset.setToolTip(
      "Where the cuts start: 0 at the corners, 1 at the edge "
      "midpoints.")
    self.opt_offset.valueChanged.connect(self._queue_preview)
    self.opt_offset_row = self._form_row(form, "Offset", self.opt_offset)

    self.opt_offset_angle = TrimmedSpinBox()
    self.opt_offset_angle.setRange(-50, 85)
    self.opt_offset_angle.setSingleStep(1)
    self.opt_offset_angle.setToolTip(
      "Rotates the dissection's internal cuts within each tile.")
    self.opt_offset_angle.valueChanged.connect(self._queue_preview)
    self.opt_offset_angle_row = self._form_row(
      form, "Inner angle", self.opt_offset_angle)

    self.opt_point_angle = TrimmedSpinBox()
    self.opt_point_angle.setRange(10, 120)
    self.opt_point_angle.setValue(30)
    self.opt_point_angle.setToolTip(
      "Sharpness of the star points, in degrees.")
    self.opt_point_angle.valueChanged.connect(self._queue_preview)
    self.opt_point_angle_row = self._form_row(
      form, "Point angle", self.opt_point_angle)

    self.opt_aspect = TrimmedSpinBox()
    self.opt_aspect.setRange(0.083, 1.0)
    self.opt_aspect.setSingleStep(0.083)
    self.opt_aspect.setDecimals(3)
    self.opt_aspect.setValue(0.75)
    self.opt_aspect.setToolTip(
      "Strand width as a fraction of spacing; 1.0 leaves no gaps.")
    self.opt_aspect.valueChanged.connect(self._queue_preview)
    self.opt_aspect_row = self._form_row(
      form, "Strand width", self.opt_aspect)

    self.opt_over_under = QLineEdit()
    self.opt_over_under.setPlaceholderText("e.g. 2 or 1,2 or 1,2,2,1")
    self.opt_over_under.setToolTip(
      "How many crossing strands each strand passes over, then under.")
    self.opt_over_under.textChanged.connect(self._queue_preview)
    self.opt_over_under_row = self._form_row(
      form, "Over-under", self.opt_over_under)

    # grid's array shape: two spinners in one row. With fewer
    # elements than cells the library leaves the surplus cells as
    # regular openings (see catalog.tightest_grid), so these two
    # controls set both the arrangement and how porous the grid is.
    grid_box = QWidget()
    grid_lay = QHBoxLayout(grid_box)
    grid_lay.setContentsMargins(0, 0, 0, 0)
    self.opt_grid_rows = QSpinBox()
    self.opt_grid_rows.setRange(1, 26)
    self.opt_grid_cols = QSpinBox()
    self.opt_grid_cols.setRange(1, 26)
    for sp, tip in ((self.opt_grid_rows, "Rows of squares in the unit"),
                    (self.opt_grid_cols,
                     "Columns of squares in the unit. Surplus cells "
                     "become regular openings.")):
      sp.setToolTip(tip)
      sp.valueChanged.connect(self._queue_preview)
      grid_lay.addWidget(sp)
    self.opt_grid_row = self._form_row(
      form, "Grid rows \u00d7 cols", grid_box)

    # transformations: paired spins keep the dialog short enough to
    # leave the map visible behind it
    mods = QGroupBox("Transformations")
    mform = QFormLayout(mods)

    def spin(lo, hi, val, step):
      """One modifier's spin box, wired to the preview.

      Args:
        lo: the smallest value the control accepts.
        hi: the largest.
        val: where it starts, which is the identity for that modifier.
        step: how far one press of an arrow moves it; also decides
          the decimals shown, since a sub-unit step wants three and a
          whole-unit step wants one.

      Returns:
        The QDoubleSpinBox, already connected to the preview debounce.
      """
      box = TrimmedSpinBox()
      box.setRange(lo, hi)
      box.setValue(val)
      box.setSingleStep(step)
      box.setDecimals(max(_LEAST_FIGURES_DECIMALS,
                          3 if step < 1 else 1))
      # ONE SIGNAL PER FINISHED EDIT, not one per keystroke, and this
      # line is the whole of a defect that made a mirrored design
      # impossible to type.
      #
      # `_skip_zero_scale` watches `valueChanged` and moves the box off
      # zero, because a scale of zero collapses the unit and surfaces
      # later as a raw LinAlgError. With keyboard tracking on -- Qt's
      # default -- that signal fires on every character, so typing
      # `-0.5` announced a landing on ZERO after the leading nought:
      # the handler rewrote the box, the remaining `.5` landed in the
      # middle of the rewritten text, and the sign flipped. Measured
      # 2026-08-17 by reading tile centroids rather than the box: from
      # a mirrored design, typing -0.5 silently UN-MIRRORED it, putting
      # every variable on the wrong side of the map at a size that
      # looks exactly right. No value between -1 and 1 could be typed
      # at all; fourteen of fourteen missed.
      #
      # A RANGE IS NOT THE ONLY THING THAT EATS A KEYSTROKE. A handler
      # that rewrites its own box does it too, and only real key
      # events see it -- every guard on this control drives `setValue`
      # or `stepBy`, and its docstring says "dragging or stepping",
      # so typing was never in view. The class-bound box has carried
      # this same line since it was written.
      box.setKeyboardTracking(False)
      box.valueChanged.connect(self._queue_preview)
      return box

    def pair(label, a, b):
      """Two controls side by side on one labelled form row.

      Args:
        label: the form label, as the user reads it.
        a: the left-hand widget.
        b: the right-hand one.

      Returns:
        None; the row is added to the modifiers form.
      """
      row = QHBoxLayout()
      row.addWidget(a)
      row.addWidget(b)
      mform.addRow(label, row)

    # A FULL TURN EITHER WAY (maintainer's request, 2026-08-25). It
    # was -90..90, which is enough to reach every DISTINCT pattern --
    # a tiling repeats -- but a person turning a design does not think
    # in equivalence classes, and a range that stops at 90 refuses the
    # obvious 180 and makes the control feel broken. Measured before
    # widening, as the negative scales were: 0, 45, 90, 91, 135, 180,
    # 270, 359, 360 and their negatives all build a valid unit with
    # the same element count and area, so nothing downstream needed a
    # guard. The tooltip's 15-75 degrees stays: it is advice about
    # what reads well on two-direction weaves, not a bound.
    self.mod_rotate = spin(-360, 360, 0, 1)
    self.mod_rotate.setToolTip(
      "Turn the whole pattern; 15–75° usually suits two-direction "
      "weaves.")
    mform.addRow("Rotate (°)", self.mod_rotate)
    # NEGATIVE SCALES MIRROR THE PATTERN, and are allowed as of
    # 2026-08-16 at a user's request. Measured before widening the
    # range: `Tileable.transform_scale` is a plain GeoSeries.scale, so
    # -1 is a true reflection -- every centroid lands at exactly
    # (-x, y), the element ids survive, and the whole chain through
    # get_tiled_map, gdf_to_layer and the GeoPackage write returns the
    # same tile count and the same total area. Elements swap sides of
    # the map, which is the point of asking for it.
    #
    # ZERO IS THE HOLE IN THAT RANGE. transform_scale(0, ...) does not
    # raise; it returns a collapsed unit whose prototile has no area,
    # and the failure surfaces much later inside Tiling.__init__ as
    # numpy.linalg.LinAlgError: Singular matrix, which reaches the
    # user as a raw "Tiling failed" line. A spin box cannot exclude a
    # single value, so _skip_zero below steps over it in whichever
    # direction the user is travelling.
    self.mod_scale_x = spin(-4.0, 4.0, 1.0, 0.02)
    self.mod_scale_x.setToolTip(
      "Stretch the pattern right-left; negative mirrors it.")
    self.mod_scale_y = spin(-4.0, 4.0, 1.0, 0.02)
    self.mod_scale_y.setToolTip(
      "Stretch the pattern up-down; negative mirrors it.")
    for box in (self.mod_scale_x, self.mod_scale_y):
      box.valueChanged.connect(
        lambda value, b=box: self._skip_zero_scale(b, value))
    pair("Scale EW / NS", self.mod_scale_x, self.mod_scale_y)
    self.mod_skew_x = spin(-45, 45, 0, 1)
    self.mod_skew_x.setToolTip("Slant the pattern right-left.")
    self.mod_skew_y = spin(-45, 45, 0, 1)
    self.mod_skew_y.setToolTip("Slant the pattern up-down.")
    pair("Skew EW / NS (°)", self.mod_skew_x, self.mod_skew_y)
    self.mod_p_inset = spin(0, 10, 0, 0.1)
    self.mod_p_inset.setToolTip(
      "Opens a gap around each whole unit (tilings only).")
    self.mod_t_inset = spin(0, 5, 0, 0.1)
    self.mod_t_inset.setToolTip(
      "Opens a thin gap around every tile or strand.")
    pair("Inset group / tiles (%)", self.mod_p_inset, self.mod_t_inset)
    self.mod_glyph = QCheckBox("Scale as glyph (independent of tiling)")
    self.mod_glyph.setToolTip(
      "Shrink each unit in place, into separate glyphs.")
    self.mod_glyph.toggled.connect(self._queue_preview)
    mform.addRow(self.mod_glyph)

    wrapper = QWidget()
    wl = QVBoxLayout(wrapper)
    wl.setContentsMargins(0, 0, 0, 0)
    wl.addWidget(design)
    wl.addWidget(mods)
    wl.addStretch(1)
    tabs.addTab(wrapper, "Design")
    self._design_wrapper = wrapper

    # ---- tab 2: data & colours
    data_tab = QWidget()
    dlayout = QVBoxLayout(data_tab)
    hint = QLabel(
      "Each element/row below becomes its own QGIS layer, initially "
      "symbolized using the options available under the 'Style' "
      "dropdowns; refine it afterwards in QGIS's built-in Layer "
      "Styling panel. A plausible style is picked from each field's "
      "type and follows the variable until you choose one yourself.")
    hint.setWordWrap(True)
    dlayout.addWidget(hint)
    self.table = QTableWidget(0, 9)
    self.table.setHorizontalHeaderLabels(
      ["Tile id", "Variable", "Style", "Classes", "Colour ramp",
       "Reverse", "Opacity", "Categ colourmap src", "Edit colours"])
    # Qt draws a row-number gutter unless told not to, so the table
    # showed 1, 2, 3, 4 immediately beside the Tile id column showing
    # a, b, c, d: two columns of identifiers, one of them meaningless,
    # and the meaningless one read as authoritative. The LETTERS are
    # the element ids everything in this plugin is keyed on -- the
    # preview labels them, the output layers are named for them, the
    # colour records are dictionaries of them. Hiding the gutter also
    # returns width the table needs to show every column without
    # scrolling sideways, which nobody notices it doing.
    self.table.verticalHeader().setVisible(False)
    self.table.setColumnWidth(0, 50)
    self.table.setColumnWidth(1, 160)
    self.table.setColumnWidth(2, 152)
    self.table.setColumnWidth(3, 55)
    self.table.setColumnWidth(4, 172)   # a 64px swatch plus the name
    self.table.setColumnWidth(5, 58)
    self.table.setColumnWidth(6, 68)
    self.table.setColumnWidth(7, 150)
    self.table.setColumnWidth(COL_EDIT_COLOURS, 82)
    # The conditional columns start hidden. These three lines are the
    # FIRST state the table has; _refresh_table then calls
    # _update_dynamic_columns, which decides these three from the
    # assignments (it decides FOUR columns in all -- Reverse is the
    # fourth and is not hidden here, because a table with no layer has
    # no ramp for it to belong to), so for a dialog that reaches a
    # layer these three are redundant. They are kept for the moment BEFORE that -- a table
    # built and shown with no layer chosen -- because a dead column
    # in front of a first-time user is exactly the fault the hiding
    # exists to prevent. Guarded by test_dialog_structure, which
    # names the columns by header rather than by index so a
    # renumbering cannot quietly hide the wrong one.
    self.table.setColumnHidden(3, True)
    self.table.setColumnHidden(7, True)
    self.table.setColumnHidden(COL_EDIT_COLOURS, True)
    # "Edit colours" belongs beside the ramp, since it does the same
    # job by hand. It is nevertheless the LAST column logically, and
    # only moved into place visually. Inserting it at position 5 would
    # have renumbered Reverse, Opacity and the class source, and those
    # numbers are written out in dozens of places here and in the
    # tests -- a renumbering that silently repoints a test at the
    # wrong widget is exactly how a test comes to pass for the wrong
    # reason, which has happened here before.
    self.table.horizontalHeader().moveSection(COL_EDIT_COLOURS, 5)
    dlayout.addWidget(self.table, 1)

    cls_row = QFormLayout()
    self.opt_tile_outlines = QCheckBox("Draw tile boundaries")
    self.opt_tile_outlines.setToolTip(
      "Outline every tile on the map.")
    cls_row.addRow(self.opt_tile_outlines)
    dlayout.addLayout(cls_row)
    tabs.addTab(data_tab, "Data && colours")

    # ---- tab 3: options
    opts_tab = QWidget()
    olayout = QVBoxLayout(opts_tab)
    self.opt_join_prototiles = QCheckBox("Join data using whole tileable")
    self.opt_join_prototiles.setToolTip(
      "Every element in a unit takes its data from the same area.")
    self.opt_retain = QCheckBox("Retain complete tileables at edges")
    self.opt_retain.setToolTip(
      "Keeps whole units that touch the region, letting the pattern "
      "spill outward.")
    self.opt_clip = QCheckBox("Clip by map units (no ragged edges)")
    self.opt_clip.setToolTip(
      "Trims the pattern to the region outline. The slowest step.")
    self.opt_icons = QCheckBox("Use tileable as icon (one per map unit)")
    self.opt_icons.setToolTip(
      "One unit at the centre of each polygon, instead of a "
      "continuous pattern.")
    self.opt_outlines = QCheckBox("Add map unit outlines layer")
    self.opt_outlines.setToolTip(
      "Adds the region boundaries as outlines on top of the pattern.")
    self.opt_new_group = QCheckBox(
      "Create as new group (keep the previous result)")
    self.opt_new_group.setToolTip(
      "Keeps the previous result and adds this run as a separate "
      "group.")
    self.opt_colour_warnings = QCheckBox(
      "Warn about lack of legibility in colour choices")
    self.opt_colour_warnings.setToolTip(
      "Warns when two elements use colours a reader may confuse.")
    for cb in (self.opt_join_prototiles, self.opt_retain, self.opt_clip,
               self.opt_icons, self.opt_outlines, self.opt_new_group,
               self.opt_colour_warnings):
      olayout.addWidget(cb)

    olayout.addStretch(1)
    tabs.addTab(opts_tab, "Map options")

    # ---- tab 4: saving and opening, which are one subject
    # SAVING AND OPENING ARE THE SAME ACT FROM TWO ENDS, so they are
    # built alike and sit together: one file row each, the same
    # widget, the same filter, the same shape of label, and a button
    # each that DOES the thing. They lived on Map options until
    # 2026-08-27, where saving sat under seven switches about how the
    # map is drawn and opening was a button some distance below it --
    # two halves of one idea, looking nothing like each other.
    # (Maintainer's instruction that day.)
    #
    # SAVING IS A POSITIVE ACT (maintainer's ruling, the same day, and
    # the reason this tab has buttons at all). A path chooser records
    # what you WOULD save to or load from and does nothing on its own;
    # the button is the act. Until this ruling, setting the output path
    # was the documented way to save and every Generate wrote the file
    # -- so a map was saved as a side effect of drawing it, a path
    # chosen for later was written to at once, and live update had to
    # be held back to stop it rewriting somebody's file on every
    # keystroke.
    files_tab = QWidget()
    flayout = QVBoxLayout(files_tab)
    files_form = QFormLayout()
    self.gpkg_widget = QgsFileWidget()
    from . import compat
    compat.set_save_file_mode(self.gpkg_widget)
    self.gpkg_widget.setFilter("GeoPackage (*.gpkg)")
    self.gpkg_widget.setDialogTitle("Save tiled map to GeoPackage")
    self.gpkg_widget.setToolTip(
      "Where Save will write the map. Nothing is written until you press 'Save'.")
    save_row = QHBoxLayout()
    save_row.addWidget(self.gpkg_widget, 1)
    self.save_button = QPushButton("Save")
    self.save_button.setToolTip("Write the map as it stands to that file.")
    self.save_button.clicked.connect(self._save_pressed)
    save_row.addWidget(self.save_button)
    files_form.addRow("Save the map to", save_row)
    # THE SOURCE TRAVELS ONLY IF ASKED (ruling 5 of 2026-08-25). A
    # saved map records where its data came from, which is enough to
    # carry on with on the machine that made it; putting the data
    # itself in is for a file somebody ELSE is meant to continue.
    # It belongs beside the box it qualifies rather than under the
    # whole tab, which is why it is a row of the same form.
    self.opt_embed_source = QCheckBox(
      "Include the source data, so others can carry on with it")
    self.opt_embed_source.setToolTip(
      "Copies the region layer into the file, making it larger.")
    files_form.addRow("", self.opt_embed_source)
    # WHOSE ANSWER IS IN THE BOX. `_embedded_when_resumed` is what a
    # FILE said when it was opened, keyed by file; `_embed_box_touched`
    # is whether this person has since had an opinion. Only the second
    # may overrule the first, which is what keeps a recipient's Save
    # from emptying a file they never asked to change while leaving a
    # deliberate untick meaning exactly what it says.
    self._embedded_when_resumed = {}
    # HOW MANY TIMES ANYBODY HAS TOUCHED THE BOX, and what that count
    # was when each file was opened. A plain "has it been touched"
    # bool was the first repair's own mistake, and it is the mistake
    # the commit that introduced it had just written into CLAUDE.md:
    # a fact keyed by subject needs its OVERRIDE keyed by subject as
    # well, or one tick anywhere in the session strips every
    # self-contained file opened afterwards. Measured 2026-08-28 by
    # the hunt aimed at that repair: tick, save your own file, untick,
    # then open a colleague's map and save -- their embedded copy gone
    # and the file no longer redrawable.
    self._embed_touches = 0
    self.opt_embed_source.toggled.connect(self._note_an_embed_touch)
    # ...and the other end, built from the same widget so the two rows
    # read as one pair. Choosing a file here is NOT the act either: a
    # chooser that loaded the moment it was filled would be the same
    # confusion as a chooser that saved, and the maintainer's ruling
    # names both ends of it.
    self.resume_widget = QgsFileWidget()
    compat.set_open_file_mode(self.resume_widget)
    self.resume_widget.setFilter("GeoPackage (*.gpkg)")
    self.resume_widget.setDialogTitle("Open a saved map")
    self.resume_widget.setToolTip(
      "Which saved map Load will open. Nothing is loaded until you press 'Load'.")
    load_row = QHBoxLayout()
    load_row.addWidget(self.resume_widget, 1)
    self.load_button = QPushButton("Load")
    self.load_button.setToolTip("Carry on with the map in that file.")
    self.load_button.clicked.connect(self._load_pressed)
    load_row.addWidget(self.load_button)
    files_form.addRow("Load a saved map", load_row)
    flayout.addLayout(files_form)
    flayout.addStretch(1)
    tabs.addTab(files_tab, "Save && open")

    # ---- tab 4: help (condensed guide; full version in docs/USER-GUIDE.md)
    # QTextBrowser renders a subset of HTML and opens links externally
    from qgis.PyQt.QtWidgets import QTextBrowser
    from .help_content import HELP_HTML
    help_tab = QTextBrowser()
    help_tab.setOpenExternalLinks(True)
    help_tab.setHtml(
      HELP_HTML + f"<p><small>WeavingSpace QGIS plugin version "
                  f"{_plugin_version()}</small></p>")
    tabs.addTab(help_tab, "Help")

    # ---- bottom bar
    bottom = QHBoxLayout()
    self.live_check = QCheckBox("Live update")
    self.live_check.setChecked(True)
    self.live_check.setToolTip(
      "Draws and redraws the map as you change settings, without "
      "pressing Generate.")
    bottom.addWidget(self.live_check)
    self.live_note = QLabel("")
    self.live_note.setStyleSheet("color: #888888;")
    bottom.addWidget(self.live_note)
    self.progress = QProgressBar()
    self.progress.setVisible(False)
    bottom.addWidget(self.progress, 1)
    bottom.addStretch(1)
    self.generate_btn = QPushButton("Generate tiled map")
    self.generate_btn.clicked.connect(lambda: self._generate())
    bottom.addWidget(self.generate_btn)
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(self.close)
    bottom.addWidget(close_btn)
    left.addLayout(bottom)

    # wider than tall: room for the table's columns, height set by the
    # Design tab so the map stays visible behind the dialog
    self.resize(1180, 560)

    # any of these should refresh the live map too (design controls
    # already funnel through _queue_preview)
    for cb in (self.opt_tile_outlines, self.opt_join_prototiles,
               self.opt_retain, self.opt_clip, self.opt_icons,
               self.opt_outlines):
      cb.toggled.connect(self._queue_live)

  def _fit_to_design(self):
    """Size the dialog to the Design tab's actual (visible) content, so
    it stays short enough to leave the map visible behind it; called
    again when family-specific rows appear or disappear.

    Qt's ``sizeHint`` (a widget's preferred size) is only trustworthy
    after its layouts have recomputed, and hidden rows can leave stale
    contributions behind; invalidating every child layout first forces
    an honest measurement. The +96 covers the tab bar and bottom bar.
    """
    if getattr(self, "_design_wrapper", None) is None:
      return
    for child in self._design_wrapper.findChildren(QWidget):
      if child.layout() is not None:
        child.layout().invalidate()
    layout = self._design_wrapper.layout()
    if layout is not None:
      layout.invalidate()
      layout.activate()
    height = self._design_wrapper.sizeHint().height() + 96
    self.resize(max(self.width(), 1180), max(400, height))

  def _form_row(self, form: QFormLayout, label: str, widget: QWidget):
    """Add a labelled row to a form.

    Args:
      form: the QFormLayout to add to.
      label: the text shown beside the control.
      widget: the control itself.

    Returns:
      (label widget, control) so ``_on_family_changed`` can show and
      hide the pair together — hiding a control while its label stays
      is the classic way a dialog ends up looking broken.
    """
    lab = QLabel(label)
    form.addRow(lab, widget)
    return (lab, widget)

  # ------------------------------------------------------------- UI dynamics

  def _current_spec(self) -> dict | None:
    """The catalogue entry (TileUnit/WeaveUnit constructor kwargs) for
    the currently selected element count and family, or None while the
    combos are being repopulated."""
    name = self.family_combo.currentText()
    n = self.n_combo.currentData()
    return catalog.TILINGS_BY_N.get(n, {}).get(name)

  def _on_n_changed(self):
    """Repopulate the family list for the chosen element count.

    Some counts exist only as tilings or only as weaves; if the current
    kind has no families the kind combo is flipped silently
    (blockSignals prevents that flip from re-triggering this handler).
    """
    n = self.n_combo.currentData()
    families = catalog.TILINGS_BY_N.get(n, {})
    kind = self.kind_combo.currentText()
    names = [name for name, spec in families.items()
             if spec["type"] == ("tiling" if kind == "tiling" else "weave")]
    if not names:  # this n only has the other kind: switch kind silently
      names = list(families)
      other = families[names[0]]["type"]
      self.kind_combo.blockSignals(True)
      self.kind_combo.setCurrentText(
        "tiling" if other == "tiling" else "weave")
      self.kind_combo.blockSignals(False)
      kind = self.kind_combo.currentText()
      names = [name for name, spec in families.items()
               if spec["type"] == ("tiling" if kind == "tiling" else "weave")]
    self.family_combo.blockSignals(True)
    self.family_combo.clear()
    self.family_combo.addItems(names)
    self.family_combo.blockSignals(False)
    self._on_family_changed()

  def _on_kind_changed(self):
    """Tiling/weave toggle reuses the family-repopulation logic."""
    self._on_n_changed()

  def _on_family_changed(self):
    """Show exactly the option rows this family understands.

    The mapping mirrors weavingspace's constructor arguments: slice and
    dissection tilings take ``offset`` (dissections also
    ``offset_angle``, with hex and square variants allowing different
    angle ranges), star1 takes ``point_angle``, weaves take ``aspect``,
    and twill/basket weaves an over-under pattern whose default comes
    from the catalogue entry. The dialog is then re-fitted because row
    visibility changes its natural height.
    """
    spec = self._current_spec()
    if spec is None:
      return
    is_weave = spec["type"] == "weave"
    tiling_type = spec.get("tiling_type", "")
    show = {
      self.opt_offset_row: not is_weave and (
        "slice" in tiling_type or "dissect" in tiling_type),
      self.opt_offset_angle_row: not is_weave and "dissect" in tiling_type,
      self.opt_point_angle_row: tiling_type == "star1",
      self.opt_aspect_row: is_weave,
      self.opt_over_under_row:
        is_weave and spec.get("weave_type") in ("twill", "basket"),
      self.opt_grid_row: tiling_type == "grid",
    }
    for (lab, widget), visible in show.items():
      lab.setVisible(visible)
      widget.setVisible(visible)
    if "dissect" in tiling_type:
      self.opt_offset.setRange(0, 1)
      lo, hi = ((-50, 85) if "hex" in tiling_type else (-30, 70))
      self.opt_offset_angle.setRange(lo, hi)
    elif "slice" in tiling_type:
      self.opt_offset.setRange(-1, 1)
    if is_weave and spec.get("weave_type") in ("twill", "basket"):
      self.opt_over_under.blockSignals(True)
      self.opt_over_under.setText(str(spec.get("n", "2")))
      self.opt_over_under.blockSignals(False)
    if tiling_type == "grid":
      # reset to the tightest fit for this element count; a signal
      # here would schedule a second rebuild of the same unit
      rows, cols = catalog.tightest_grid(spec["n"])
      for sp, v in ((self.opt_grid_rows, rows),
                    (self.opt_grid_cols, cols)):
        sp.blockSignals(True)
        sp.setValue(v)
        sp.blockSignals(False)
    QTimer.singleShot(0, self._fit_to_design)
    self._queue_preview()

  def _update_layer_exclusions(self):
    """Keep the plugin's own output layers out of the region combo.

    Without this, a generated element layer (tagged with a custom
    property) can be offered, or even auto-selected, as the next
    region, and the plugin would happily tile its own output.
    """
    outputs = [lyr for lyr in QgsProject.instance().mapLayers().values()
               if lyr.customProperty("weavingspace_output")]
    try:
      self.layer_combo.setExceptedLayerList(outputs)
    except Exception:
      pass

  def _on_layer_changed(self):
    """React to the region-layer choice (or to combo re-emissions).

    QgsMapLayerComboBox re-emits layerChanged whenever the project's
    layer list changes, which happens after every generation, so
    anything here must be safe to run repeatedly for the same layer.
    """
    # A RETIRED DIALOG DOES NOTHING HERE. QgsMapLayerComboBox
    # re-emits layerChanged whenever the project's layers churn, and
    # every dialog ever opened still owns a combo doing that until its
    # C++ object dies -- so a session that opens the plugin several
    # times pays a full weave-unit rebuild per dead window per project
    # change, which is quadratic. Measured 2026-08-16: this path alone
    # ran 647 times in one test against 230 at v0.24.2, and it is the
    # last of the four routes that reached a window nobody is looking
    # at. The gate is the one `_on_project_read` has carried since it
    # was written.
    if _dialog_is_gone(self) or _live_dialog() is not self:
      return
    self._cat_count_cache = {}
    self._nulls_cache = {}
    self._limit_cache = {}
    layer = self.layer_combo.currentLayer()
    # CAPTURED BEFORE `_watch_layer` MOVES IT. One dataset being
    # swapped for another is not the same act as choosing the first
    # one: only the swap can RETAIN a setup made for other data, which
    # is what `_settle_retained_schemes` below asks about. Reading
    # `_watched_layer` after the watch is rearmed would answer about
    # the layer we have just adopted.
    # THE DATASET IN FORCE, NOT THE WATCHED LAYER OBJECT. Asked of
    # `_watched_layer`, this missed the route a hunt found on
    # 2026-08-25: REMOVE the region layer from the project and choose
    # another, and the removal has already nulled the watch -- so the
    # next dataset read as a FIRST CHOICE, the output path was never
    # cleared, and Generate wrote the new data over the GeoPackage
    # holding the last one's map, unasked. The code disagreed with
    # itself, since `_swap_dataset_memory` banked the old dataset on
    # the same pass. `_memory_layer_id` is the identity of the dataset
    # whose bank is open; a removal does not touch it, which is what
    # makes it the honest answer to "which dataset is in force".
    switched = (layer is not None and self._memory_layer_id is not None
                and layer.id() != self._memory_layer_id)
    # ...AND ONLY LEAVING A DATASET THIS SESSION HAS BUILT FROM IS A
    # CHANGE OF DATASET. The full suite drew this boundary on the
    # first whole run of the seven rulings, with three cases the plain
    # `switched` got wrong, and ONE CLAUSE covers all three. A
    # RECOVERY is not a switch -- reopening a project whose region
    # file has MOVED and pointing at live data re-finds the same work
    # -- because a reopened session has not landed anything yet. A
    # COMBO AUTO-LANDING in a busy project is not a dataset the user
    # chose, for the same reason. And a PRE-GENERATE FIDDLE is a
    # first choice: nothing is built, so there is nothing to protect.
    # A liveness clause on the OUTGOING layer was tried beside this
    # one and deleted when its catalogue entry could only survive:
    # every measured journey is decided by the landing alone, and in
    # the one it would change -- land a run, lose the source file,
    # pick new data -- protecting the landed result is the rulings'
    # own answer.
    switched_from_work = switched and self._landed_this_session
    if switched:
      _dump("SWITCH", "boundary",
            "change-of-dataset" if switched_from_work
            else "first-choice", "landed=", self._landed_this_session)
    # LEAVING A DATASET STAMPS WHAT YOU LEAVE. The group record is
    # ordinarily written at landings -- but a choice made and switched
    # away from INSIDE the live debounce has no landing yet, so the
    # return applied the record from before the pick and the choice
    # died silently, while the switch notice's own sentence had just
    # testified to it ("landcover ... now show p, q instead"). One
    # stamp from the live widgets, taken before the swap below empties
    # the view, makes the record describe the state a person actually
    # left. A run in flight is left to its landing, whose launch
    # snapshot must win. Found by the switchdoor hunt of 2026-08-26
    # (round nine); the settled journey was already clean.
    if switched_from_work and not self._selecting_a_group \
        and self._task is None:
      try:
        # THE REGION IS THE OUTGOING DATASET'S. The chooser already
        # holds the NEW layer when this handler runs, so a plain
        # capture would stamp the group being left as the other
        # dataset's -- of one fact written twice, the writer with a
        # reason here is `_memory_layer_id`, which the swap below has
        # not yet moved.
        outgoing = QgsProject.instance().mapLayer(
          self._memory_layer_id or "")
        # AND A DATASET THAT HAS GONE LEAVES NOTHING TO STAMP. When
        # the outgoing layer has been REMOVED from the project rather
        # than switched away from, the table in front of us is blank
        # because the fields went with it -- a blank the plugin
        # imposed, not a choice anybody made -- and this handler runs
        # for every dialog whose combo re-emits, including one the
        # user has closed. Stamping there wrote an empty variable and
        # "Single colour" over every element of a perfectly good
        # record, so the next dialog opened in that project met a
        # table describing nothing and a Generate that refused for
        # want of a variable, beside layers plainly drawn from v1.
        # Measured 2026-08-26 (the record was intact through the close
        # and the removal, and blank the moment another layer
        # arrived); it is the reason `test_the_layer_changes_without_
        # being_edited` went red on every platform at once.
        group = self._group_of_our_layers(
          QgsProject.instance().layerTreeRoot())
        # ...AND THE GROUP HAS TO BE THAT DATASET'S OWN MAP.
        # `_group_of_our_layers` answers "where this dialog's layers
        # are", which is the group the last run LANDED in -- not
        # necessarily the group of the dataset being left. Generate on
        # A, switch to B, come back to A while that run lands, and the
        # two are different groups: the stamp then wrote the dataset
        # being left onto the OTHER dataset's map, so a group's record
        # and its own layers disagreed about where the map came from --
        # the single fact the landing's refusal to overwrite and the
        # group binding both read. Ask the LAYERS, which is the
        # authority for that question everywhere else here; output made
        # before the stamp carries none and keeps the older rule.
        stamps = [child.layer().customProperty("weavingspace_region")
                  for child in (group.children() if group is not None
                                else [])
                  if getattr(child, "layer", lambda: None)() is not None
                  and child.layer().customProperty("weavingspace_region")]
        if outgoing is None:
          _dump("SWITCH", "no-stamp-the-outgoing-dataset-is-gone")
        elif stamps and not any(same_source(mark, outgoing.source())
                                for mark in stamps):
          _dump("SWITCH", "no-stamp-that-group-is-another-datasets")
        else:
          self._stamp_working_state(
            group, launch_state={"region": outgoing.source()})
      except Exception:
        _dump("STATE", "switch-stamp-failed",
              traceback.format_exc(limit=3))
    # The memory banks swap on ANY change of layer -- hygiene rather
    # than protection, so it is not gated on the landing: what belongs
    # to a dataset must never be readable while another is chosen.
    self._swap_dataset_memory(layer)
    # Hear the layer itself, not merely the fact that a different one
    # was chosen: a user editing in QGIS never touches this combo.
    if layer is not self._watched_layer:
      self._watch_layer(layer)
      self._said_live_cannot_track = False      # a new layer, a new answer
      self._said_source_gone = False
      self._watched_fields = tuple(
        f.name() for f in layer.fields()) if layer is not None else ()
      self._watched_crs = layer.crs().authid() if layer is not None else None
    if layer is None and self._had_a_layer:
      # The layer combo empties itself when its layer leaves the
      # project, and does it silently. A user who removed a layer for
      # some unrelated reason is otherwise left with a dialog whose
      # controls all still look armed and a Generate button that will
      # simply tell them to choose a layer.
      self._had_a_layer = False
      self._report_quietly(
        "The region layer was removed from the project, so there is "
        "nothing to map. Choose another layer.")
    elif layer is not None:
      self._had_a_layer = True
    self._adapt_to_the_layer(layer)
    # derive spacing once per newly chosen layer; the combo re-emits
    # layerChanged whenever project layers shuffle (e.g. after every
    # generation), and that must not clobber a hand-set spacing
    # ...AND A NUMBER A PERSON TYPED SURVIVES A CHANGE OF DATASET TOO.
    # (Maintainer's ruling, 2026-08-25.) The guard above was written to
    # protect a typed spacing from the combo's re-emissions, and it
    # re-derived over that same spacing the moment the dataset really
    # changed: a probe typed 137, worked on another layer, came back
    # and read 500 -- the auto-derived figure, with nothing said.
    # WHAT THE PLUGIN DERIVED IS STILL RE-DERIVED, which is the other
    # half of the ruling: a number nobody chose says nothing about the
    # new data, and without this a country-sized layer would keep a
    # floor plan's grain and draw nothing anybody wants.
    # The absurd cases this now allows are caught where the maintainer
    # put them rather than by re-deriving: the live gate pauses and
    # says so, and the confirm gate asks before an explicit run. A
    # spacing carried onto a dataset in different units is the case
    # that argument is really about.
    # THE LAYER ID IS RECORDED EITHER WAY. Skipping the assignment
    # when the spacing is the user's would leave the guard armed, and
    # the combo's next re-emission would then derive over the very
    # number this clause exists to keep.
    if layer is not None and layer.id() != self._auto_spacing_layer:
      self._auto_spacing_layer = layer.id()
      if not self._spacing_is_mine:
        self._auto_spacing()
    # populate the variable choosers the moment the layer is chosen
    # (synchronously, not on the preview debounce), and queue the
    # automatic first render
    # A CHANGE OF DATASET DOES ITS HOUSEKEEPING FIRST -- the output
    # path, the fresh-group flag and the design-floor question all
    # precede the rebuild, because a Yes to that question changes what
    # the rebuild builds.
    # THE DATASET SELECTS ITS GROUP (ruling 2), and that runs BEFORE
    # the change-of-dataset housekeeping, because what it finds
    # decides whether any of that housekeeping is still needed. A
    # dataset with a group of its own is being RESUMED: its output
    # path, its design and its symbology all come back together, so
    # clearing the path and asking the design-floor question would be
    # undoing the restore in the same breath as making it. A dataset
    # with no group here is genuinely new work, and gets both.
    #
    # Skipped while `_on_group_chosen` is driving the chooser, or the
    # two halves of the binding would call each other.
    restored = False
    if not self._selecting_a_group:
      restored = self._bind_group_to_dataset()
    if switched_from_work and not restored and not self._selecting_a_group:
      self._begin_new_dataset(layer)
    # WHAT THE SWITCH IS ABOUT TO RE-POINT, so it can be SAID. The
    # deleted-column door has announced this exact loss since it was
    # written -- "v1 is no longer in the layer, so the elements using
    # it now show v3 instead" -- while a change of dataset re-pointed
    # the same chosen variables in silence, and the next map displayed
    # variables nobody picked with nothing on screen to say so.
    # (Maintainer's ruling, 2026-08-26: the switch door speaks, in the
    # twin's sentence family, naming the NEW layer because at a switch
    # it is the layer that moved rather than the column.) Snapshot
    # before the rebuild, compare after: `_rebuild_unit` refreshes the
    # table synchronously, so the re-derive has happened by the
    # comparison. Recovery and a group selection stay silent -- a
    # recovery is not a switch. Found by the notices hunt, 2026-08-26.
    before_vars = {}
    if switched and not self._selecting_a_group:
      for row_index in range(self.table.rowCount()):
        item = self.table.item(row_index, 0)
        var_combo = self.table.cellWidget(row_index, 1)
        if item is not None and var_combo is not None:
          before_vars[item.text()] = var_combo.currentText()
    self._rebuild_unit()
    if switched and not self._selecting_a_group and before_vars:
      new_fields = {f.name() for f in layer.fields()} if layer else set()
      moved = []
      for row_index in range(self.table.rowCount()):
        item = self.table.item(row_index, 0)
        var_combo = self.table.cellWidget(row_index, 1)
        if item is None or var_combo is None:
          continue
        was = before_vars.get(item.text())
        now = var_combo.currentText()
        if was and was != "---" and was not in new_fields and now != was:
          moved.append((was, now))
      if moved:
        # EVERY ELEMENT GETS THE SENTENCE THAT IS TRUE OF IT. One
        # aggregate sentence flattened the pairs, so an element left
        # with NOTHING was affirmatively covered by "now show ...
        # instead" about its neighbours -- the mixed case lying about
        # exactly the element that lost most (the switchdoor hunt of
        # 2026-08-26). The two approved sentence templates are
        # unchanged; what changed is which elements each one speaks
        # for.
        where = layer.name() if layer is not None else "this layer"
        landed_pairs = [(was, now) for was, now in moved if now != "---"]
        stranded = sorted({was for was, now in moved if now == "---"})
        if landed_pairs:
          gone = sorted({was for was, _ in landed_pairs})
          landed = sorted({now for _, now in landed_pairs})
          self._report_quietly(
            f"{', '.join(gone)} is not in '{where}', so the elements "
            f"using it now show {', '.join(landed)} instead.")
        if stranded:
          self._report_quietly(
            f"{', '.join(stranded)} is not in '{where}', and there is "
            f"nothing left to show in its place.")
    # ...and the table now standing there is asked whether a scheme it
    # kept still makes sense on the new data. It runs AFTER the rebuild
    # because it reads the rows that rebuild produced, and only on a
    # swap, so nothing is asked of somebody choosing their first layer.
    if switched:
      self._settle_retained_schemes()
    self._pending_outgoing_shelf = None
    self._queue_live()
    # ...AND AGAIN ONCE THE COMBO HAS SETTLED. QgsMapLayerComboBox
    # emits layerChanged as the project's layer list churns, and it
    # can emit BEFORE updating its own selection: on the first layer
    # added to an empty project this handler runs with currentLayer()
    # still None, so the rebuild above builds the assignment table
    # from NO fields and nothing rebuilds it afterwards. The user is
    # left with a region layer chosen, four rows, and a Variable
    # dropdown offering only "---".
    #
    # Reported from the field on 2026-08-15, against 0.24.2, by
    # somebody who opened the plugin before loading their data --
    # loading data first has always worked, which is exactly why no
    # test caught it: every test in this suite puts the layer in the
    # project before the dialog exists.
    QTimer.singleShot(0, self._settle_layer_choice)

  def _settle_layer_choice(self):
    """Rebuild the table if the chooser landed on a layer after the fact.

    A RETIRED DIALOG DOES NOTHING HERE, and the guard is the same one
    `_on_project_read` carries. This runs from a `singleShot` queued
    off the layer chooser, and a dialog the user has finished with is
    still connected to the project until its C++ object dies -- which
    may be much later, or never in a session that opens the plugin
    several times. Each such dialog rebuilding its unit is a full
    weave construction for a window nobody is looking at.

    Returns:
      None. Compares what the assignment table was last built for
      against what the chooser holds now, and rebuilds only when they
      differ -- so this is safe on every one of the combo's frequent
      re-emissions, and cannot loop.

    See _on_layer_changed for why it is needed: that signal can arrive
    before the combo has a current layer at all, and a table built in
    that instant has no fields in it.
    """
    if _dialog_is_gone(self) or _live_dialog() is not self:
      return
    layer = self.layer_combo.currentLayer()
    stamp = (layer.id() if layer is not None else None,
             tuple(self._layer_fields()))
    if stamp == self._table_built_for:
      return
    self._table_built_for = stamp
    # THE DATASET IN FORCE BINDS HERE TOO. This is the other route by
    # which a layer becomes the chooser's -- the combo settling after
    # the fact, which is how a plugin opened BEFORE the data gets its
    # first dataset -- and it did not swap banks, so
    # `_memory_layer_id` stayed None while the user worked. The next
    # dataset they picked then took the pre-identity merge branch and
    # inherited the first one's hand-picked colours, keyed by its
    # value strings, into its map and its saved project. Found by a
    # hunt, 2026-08-25, inside that merge's own first night: when a
    # branch keys on "no identity yet", enumerate every route that
    # reaches that state.
    self._swap_dataset_memory(layer)
    self._rebuild_unit()

  def _swap_dataset_memory(self, layer):
    """Bank the outgoing dataset's field-keyed memory, open the new one's.

    Args:
      layer: the region layer the chooser now holds, or None.

    Returns:
      None. The three field-keyed views -- hand-picked colours, pinned
      bounds, the scheme shelf -- are rebound to the incoming layer's
      bank, so nothing keyed by one dataset's COLUMN NAMES is readable
      while another dataset is in the chooser (maintainer's ruling,
      2026-08-24). Returning to a layer reopens its bank: the A-B-A
      journey restores its work through here.

    A CARVE WAS BUILT HERE AND REMOVED THE SAME DAY. It copied the
    current field's hand-picked colours and pinned bounds across when
    the new dataset shared the column name -- "carry the symbology for
    variables in common" -- and the maintainer asked the question that
    ended it: a categorical scheme on a confidential column would hand
    its VALUE STRINGS to any dataset sharing the name, and the landing
    stamp would write them into that dataset's .qgz and GeoPackage.
    Nothing structural tells "same wards, next year" from "unrelated
    data with a coincident name", and between those two, silence sides
    with the confidential case. So: the STYLE keeps by name as it
    always has -- mode, ramp, Reverse, class count carry no data --
    and the value-laden records never cross; sharing a ladder across
    files is an explicit act, not an ambient one. Keep-by-name still
    outranks the bank for the element's COLUMN: an element arriving
    home wearing a surviving name keeps it rather than consulting the
    shelf, the composition of two rulings rather than a third.
    """
    # OUR OWN OUTPUT IS NOT A DATASET EITHER, and neither is anything
    # the chooser touches while a project is being read. On File >
    # Open with the panel open, the combo binds one of the plugin's
    # own output layers for an instant before adoption runs -- so the
    # identity bound to THAT, the pre-identity merge never fired, and
    # the adopted project's hand-picked colours and pinned bounds were
    # banked under an output layer where nothing could reach them: the
    # editor offered the ramp default and the next Generate painted
    # over them and wiped the stamp from the .qgz and the GeoPackage.
    # Found by a hunt, 2026-08-25. The lesson it left is the one to
    # keep: when a branch keys on "no identity yet", ask what ELSE
    # binds an identity, not only which code paths call the branch.
    if layer is not None and (
        layer.customProperty("weavingspace_output")
        or self._project_is_being_replaced):
      return
    if layer is None:
      # AN EMPTY CHOOSER IS NOT A DATASET, and closing the bank here
      # is what defeated the boundary fix above: removing the region
      # layer empties the combo, this ran with None, banked the
      # outgoing dataset and NULLED the identity -- so the next
      # dataset arrived to find nothing in force and read as a first
      # choice. Nothing can be read or written against no layer, so
      # holding the bank open costs nothing and keeps the one record
      # that remembers which dataset the session was working on.
      return
    new_id = layer.id()
    old_id = self._memory_layer_id
    if old_id == new_id:
      return
    # THE KEPT-FOR-UNREADABLE SHADOW BANKS WITH THE RECORD IT SHADOWS.
    # It holds VALUE STRINGS, so ruling 8 governs it exactly as it
    # governs the hand-picks: left unbanked, a column name shared
    # between two datasets would let one dataset's kept colours decide
    # what is released from the other's record.
    outgoing = {"colours": self._category_colours,
                "pins": self._pinned_bounds,
                "shelf": self._scheme_memory,
                "kept": self._kept_for_unreadable}
    if old_id is not None:
      self._dataset_memory[old_id] = outgoing
    bank = self._dataset_memory.get(new_id)
    if bank is None:
      bank = {"colours": {}, "pins": {}, "shelf": {}, "kept": {}}
      if new_id is not None:
        self._dataset_memory[new_id] = bank
    if old_id is None:
      # RECORDS WRITTEN BEFORE ANY DATASET IDENTITY EXISTS belong to
      # the FIRST dataset chosen. A reopened project's adoption reads
      # the stamps into the views before the chooser settles, and
      # rebinding to a fresh bank here silently discarded everything a
      # saved project carried -- eleven round-trip tests went red on
      # the banks' first full suite, every one with an empty record.
      # MERGED rather than assigned, because the incoming bank may
      # already exist from an earlier visit in this session.
      for name, store in outgoing.items():
        target = bank[name]
        for tid, fields in store.items():
          target.setdefault(tid, {}).update(fields)
    self._category_colours = bank["colours"]
    self._pinned_bounds = bank["pins"]
    self._scheme_memory = bank["shelf"]
    self._kept_for_unreadable = bank.setdefault("kept", {})
    self._memory_layer_id = new_id
    _dump("SWAP", str(old_id)[:12], "->", str(new_id)[:12],
          "banked" if old_id is not None else "no-outgoing")
    self._pending_outgoing_shelf = (outgoing["shelf"]
                                    if old_id is not None else None)
    return

  def _begin_new_dataset(self, layer):
    """What a change of region dataset does before the table rebuilds.

    Args:
      layer: the newly chosen region layer.

    Returns:
      None. Three acts, all from the maintainer's rulings of
      2026-08-21 (recorded in CLAUDE.md). The OUTPUT PATH is cleared:
      B's map written over A's saved file destroys a result whether or
      not the schemas match, so the clearing is unconditional on a
      switch and announced -- re-generating the SAME dataset still
      overwrites in place, which is the settled contract, untouched.
      The NEXT RUN IS MARKED for a fresh group through the same door
      "Create as new group" uses, so the previous dataset's result
      stays in the project. And where the new data SEEMINGLY cannot
      fill the design -- fewer seemingly-usable columns than elements
      -- the plugin ASKS before recomposing, naming both numbers and
      what Yes does. "Seemingly" is the maintainer's own hedge: the
      usable-column count is a heuristic, not a fact.

    A MODAL IS ALLOWED HERE: this is the layer-change path, where the
    hundred-values question set the precedent, and no generation path
    runs through it. The flag rather than the checkbox, because
    ticking "Create as new group" would leave a control the user owns
    showing a choice they did not make.
    """
    widget = getattr(self, "gpkg_widget", None)
    if widget is not None and widget.filePath():
      widget.blockSignals(True)
      widget.setFilePath("")
      widget.blockSignals(False)
      _dump("SWITCH", "path-cleared")
      self._report_quietly(
        "The GeoPackage path was cleared, so the dataset saved from "
        "your previous work isn't overwritten; choose a new path to "
        "save this one.")
    # THE FLAG THAT USED TO BE ARMED HERE IS RETIRED (ruling 1 of
    # 2026-08-25). `_fresh_group_for_new_data` made the next Generate
    # build a group of its own so the previous dataset's map survived,
    # which was a proxy for a fact nobody could see. The fact is on
    # screen now: `_bind_group_to_dataset` runs before this and has
    # already selected either this dataset's own group or "Create
    # new", and the run lands in whichever the chooser names. This
    # method is only reached when there was no group to select, so
    # "Create new" is what the user is looking at.
    _dump("SWITCH", "no-group-for-this-dataset")
    if layer is None:
      return
    # The same id-like set _refresh_table skips when it picks
    # defaults: a column of row identifiers is offered, never counted.
    fields = [f.name() for f in layer.fields()]
    id_like = {"fid", "objectid", "id", "gid", "ogc_fid"}
    usable = [f for f in fields if f.lower() not in id_like]
    elements = len(self._tile_ids())
    # Below TWO the question cannot be honoured -- the smallest design
    # on offer has two elements -- so a one-column dataset keeps the
    # design and shares the column, as always.
    if 2 <= len(usable) < elements:
      from qgis.PyQt.QtWidgets import QMessageBox
      count = len(usable)
      answer = QMessageBox.question(
        self, "WeavingSpace",
        f"This layer seemingly has {count} usable columns, and the "
        f"design has {elements} elements. Change to a design with "
        f"{count} elements?")
      if answer == QMessageBox.StandardButton.Yes:
        # Signals LIVE deliberately: the n chooser's own cascade is
        # what repopulates the family list for the new count and picks
        # its default, and driving that any other way would be a
        # second implementation of the rule.
        self.n_combo.setCurrentText(str(count))

  def _skip_zero_scale(self, box, value):
    """Step a scale control over zero rather than onto it.

    Args:
      box: the scale spin box that just changed.
      value: the value it now holds.

    Returns:
      None. When the box has landed exactly on zero it is moved one
      step further in the direction it was travelling, so a user
      dragging or stepping across zero passes through rather than
      stopping on it.

    WHY ZERO IS SPECIAL. A scale of zero collapses the tile unit to no
    area at all, and the library does not complain at the time: it
    returns the degenerate unit and the failure appears later inside
    `Tiling.__init__` as `numpy.linalg.LinAlgError: Singular matrix`,
    which reaches a user as a raw "Tiling failed" line about a matrix
    they never asked about. Measured 2026-08-16, when negatives were
    allowed and zero became reachable for the first time.

    A QDoubleSpinBox cannot carry a hole in its range, so the hole is
    made here. The direction matters: stepping DOWN through zero must
    land on -0.02 and stepping UP on +0.02, or the control fights the
    user by pushing them back the way they came.
    """
    if value != 0:
      self._last_scale[box] = value
      return
    previous = self._last_scale.get(box, 1.0)
    step = box.singleStep()
    box.blockSignals(True)
    box.setValue(-step if previous > 0 else step)
    box.blockSignals(False)
    self._last_scale[box] = box.value()
    self._queue_preview()

  def _layers_going(self, layer_ids):
    """Record that the watched layer is about to be removed.

    Args:
      layer_ids: the ids QGIS is ABOUT to remove, as strings. The
        layers still exist at this moment, but nothing here touches
        them: only the recorded id is needed.

    Returns:
      None. Sets `_removal_pending` to the watched id when it is
      among them, and leaves it alone otherwise, so an unrelated
      removal cannot arm a notice about the region layer.

    This exists only because the ORDER of the two handlers is not
    guaranteed; see the connection site for the measurement.
    """
    if _dialog_is_gone(self) or _live_dialog() is not self:
      return
    if self._watched_layer_id is None:
      return
    if self._watched_layer_id in tuple(layer_ids):
      self._removal_pending = self._watched_layer_id

  def _layers_removed(self, layer_ids):
    """Notice the region layer leaving when the chooser does not say so.

    Args:
      layer_ids: the ids QGIS is removing, as strings. They are ids
        rather than layers deliberately -- by the time this arrives
        the objects are destroyed, so nothing here may touch a layer
        wrapper, including the one this dialog was watching.

    Returns:
      None. Does nothing at all unless the layer this dialog is
      pointed at is among those removed, in which case it re-runs the
      ordinary layer-changed path so that the chooser, the assignment
      table and the notice all follow.

    Why this exists, measured 2026-08-15. QgsMapLayerComboBox is not a
    reliable witness to its own layer being destroyed: with one
    polygon layer in the project it emits layerChanged, with two it
    emits and quietly selects the survivor, and with THREE OR MORE it
    emits nothing whatever. The dialog was then left holding a
    destroyed layer with nothing said, and Generate produced no map
    and no refusal -- silence, on a project of the size any real one
    has. `layersRemoved` is the project's own account of the same
    event and does not depend on a widget's bookkeeping.
    """
    if _dialog_is_gone(self) or _live_dialog() is not self:
      return
    # FIRST, REBUILD THE EXCLUSION LIST, and before any early return
    # below, because this is the one record the dialog keeps that
    # holds POINTERS to layers QGIS has just destroyed.
    # `setExceptedLayerList` stores the layer objects themselves, and
    # nothing rebuilt the list when layers were REMOVED -- only at
    # construction, at a project read, at a resume and after a
    # landing. So after File > New the combo went on excluding a set
    # of dead pointers, and a layer allocated at a recycled address is
    # then excluded for being somebody else: the chooser offers
    # NOTHING while the project plainly holds a polygon layer, and
    # Generate refuses for want of a region with no way for the user
    # to see why.
    # Measured 2026-08-27: clear the project, add one region, and the
    # chooser offers [] with the project holding ['region']. Rebuilt
    # from the live layers each time, as this method has always done,
    # the stale pointers cannot survive the removal that made them
    # stale.
    # WHAT GUARDS IT IS THE SUITE RATHER THAN A CATALOGUE ENTRY, and
    # that is a deliberate record rather than an omission. The harm
    # needs a new layer to be ALLOCATED where a destroyed one was, so
    # the test that caught it
    # (`test_a_second_project_does_not_take_the_first_ones_opacity`)
    # fails in a full run and passes when run alone. An entry over
    # this line would therefore report SURVIVED most times it was
    # judged -- a false negative, which is worse than no entry at
    # all. A deterministic guard would need a way to ask the combo
    # what it is excluding without dereferencing the pointers it
    # holds, and QGIS offers none.
    # AND THE FAMILY WAS SWEPT rather than this one site mended. The
    # question is which widgets we hand LAYER OBJECTS that they then
    # keep: `setExceptedLayerList` is the only one -- `setLayer`
    # names the current layer, whose lifetime the combo follows
    # through the project, and `setFilters` takes flags -- and the
    # colour editor deliberately holds no layer at all. One member,
    # and this is it.
    self._update_layer_exclusions()
    # The id this dialog was pointed at, taken from whichever witness
    # still holds it: `_removal_pending` was set before the removal,
    # `_watched_layer_id` is only still right if no combo handler has
    # run in between.
    pending = getattr(self, "_removal_pending", None)
    self._removal_pending = None
    lost = pending or self._watched_layer_id
    if lost is None:
      return
    if lost not in tuple(layer_ids) and pending is None:
      return
    # SAY SO, and say it HERE. The notice in _on_layer_changed fires
    # only when the chooser is left holding nothing, which is the
    # one-layer case; with a survivor present the combo quietly moves
    # to it and that arm never runs. Before this handler existed, a
    # project of three or more simply went deaf and the map stayed
    # put. Now it follows -- so without a sentence it would follow
    # SILENTLY, and a hunt measured exactly that on 2026-08-16: four
    # element layers moved twenty kilometres onto different ground
    # with different variables, the group replaced in place, and the
    # only message was "312 tiles across 4 element layers".
    #
    # Trading a silent do-nothing for a silent wrong map is worse than
    # the fault it fixed, and CLAUDE.md already promised that the
    # region layer being removed "is reported rather than silently
    # emptying the chooser".
    survivor = self.layer_combo.currentLayer()
    if survivor is not None:
      self._report_quietly(
        f"The region layer was removed from the project, so the map "
        f"now follows '{survivor.name()}'. Check the variables: they "
        f"have been matched to the new layer's columns.")
    # Drop the reference BEFORE anything else runs: _watch_layer's
    # disconnect loop is guarded against a destroyed wrapper, but
    # there is no reason to hand it one when we already know.
    self._watched_layer = None
    self._watched_layer_id = None
    self._on_layer_changed()

  def _show_the_adopted_path(self):
    """Put the recovered output path into the file widget.

    Returns:
      None. Does nothing when there is no path to show or the widget
      does not exist yet, which is why it is a method rather than two
      lines at the adoption site: `_adopt_existing_group` runs BEFORE
      `_build_ui` in the constructor, so a version of this written
      there silently did nothing at all -- a guard skipping the whole
      job, which is the shape this project has paid for before.

    WHAT IT PREVENTS. The output path is persisted nowhere, so on
    reopening a project the widget came back empty while `_last_path`
    was correctly recovered from the adopted layers' own sources. An
    empty widget is simultaneously the condition that lets live update
    run and the condition that sends output to MEMORY, so opening the
    plugin on a saved project fired an unasked run that replaced four
    file-backed layers with memory layers of the default design --
    hand styling gone, the GeoPackage link severed, and the layers
    empty after the next save and reopen. Making the two records agree
    closes both halves at once.

    Signals are blocked because this is RECOVERY, not a destination
    somebody chose: a user who has touched nothing should not have
    their own change handlers fired at them.
    """
    widget = getattr(self, "gpkg_widget", None)
    if widget is None or not self._last_path:
      return
    try:
      widget.blockSignals(True)
      widget.setFilePath(self._last_path)
    finally:
      widget.blockSignals(False)

  def _ground_and_edge(self, layer):
    """How much ground a region really covers, and its boundary.

    Args:
      layer: the region layer, read in whatever CRS it holds.

    Returns:
      `(area, perimeter)` of the layer's DISSOLVED geometry in the
      same units the extent is measured in, or `(None, None)` where
      that cannot be worked out -- an unavailable layer, a transform
      PROJ will not make, a geometry that will not union. A caller
      handed None falls back to assuming the region fills its extent,
      which is the older and more generous assumption rather than a
      wrong one.

    WHY DISSOLVED. Adjacent cells cut from a raster share edges that
    need no allowance, where a scatter of islands each carry their
    own; summing each polygon's perimeter measures how the data was
    cut into rows rather than the ground it covers. Measured
    2026-08-19 across four models, and the dissolved boundary is the
    only one generous on both shapes.

    CACHED BY WHAT THE LAYER CONTAINS, because this is asked from the
    live gate on every debounce tick and a dissolve is a pass over
    every geometry. The cache is keyed on the layer's fingerprint, so
    an edit invalidates it; entries for OTHER layers are kept, which
    is the half `_classification_values` got wrong once -- replacing
    the whole dict on a miss gave a twenty-three element design a hit
    rate of zero.
    """
    from . import compat
    if not compat.layer_data_is_available(layer):
      return (None, None)
    # KEYED ON THIS LAYER'S OWN CONTENTS, deliberately not through
    # `_layer_fingerprint`: that one describes the layer IN FORCE and
    # takes no argument, so using it here would file one layer's
    # ground under another layer's fingerprint. Coarser than that
    # helper on purpose -- a vertex moved INSIDE the bounding box
    # changes neither the count nor the extent, which is the same
    # stated limit the fingerprint itself carries -- and the cost of
    # being wrong is an estimate slightly out of date, where the cost
    # of a wrong KEY is one layer answering for another.
    try:
      extent = layer.extent()
      key = (layer.id(), int(layer.featureCount()),
             round(extent.xMinimum(), 6), round(extent.yMinimum(), 6),
             round(extent.xMaximum(), 6), round(extent.yMaximum(), 6))
    except Exception:
      return (None, None)
    if key in self._ground_cache:
      return self._ground_cache[key]
    try:
      from qgis.core import (QgsCoordinateReferenceSystem,
                             QgsCoordinateTransform, QgsGeometry)
      # THE SAME UNITS THE EXTENT IS IN, or the ground and the box it
      # is compared against are two different measurements: only a
      # GEOGRAPHIC layer is transformed, exactly as
      # `_extent_in_working_units` decides it.
      transform = None
      if layer.crs().isGeographic():
        transform = QgsCoordinateTransform(
          layer.crs(), QgsCoordinateReferenceSystem("EPSG:3857"),
          QgsProject.instance())
      shapes = []
      for feature in layer.getFeatures():
        geometry = feature.geometry()
        if geometry is None or geometry.isNull() or geometry.isEmpty():
          continue
        if transform is not None:
          moved = QgsGeometry(geometry)
          if moved.transform(transform) != 0:
            continue
          geometry = moved
        shapes.append(geometry)
      if not shapes:
        answer = (None, None)
      else:
        whole = QgsGeometry.unaryUnion(shapes)
        answer = ((None, None) if whole is None or whole.isEmpty()
                  else (float(whole.area()), float(whole.length())))
    except Exception:
      answer = (None, None)
    # only THIS layer's stale readings go; every other layer's stay
    self._ground_cache = {
      known: value for known, value in self._ground_cache.items()
      if known[0] != layer.id()}
    self._ground_cache[key] = answer
    return answer

  def _extent_in_working_units(self, layer):
    """The layer's extent as the TILING will see it, in metres.

    Args:
      layer: the region layer, in whatever CRS the user has it.

    Returns:
      A QgsRectangle in the coordinates the tiling works in --
      the layer's own for a projected CRS, and EPSG:3857 for a
      geographic one, which is what `bridge.layer_to_gdf` reprojects
      to. None when there is no usable extent.

    WHY NOT DEGREES TIMES 111,000. That was the arithmetic here and it
    is only right at the equator. Web Mercator's y scale is
    111,320/cos(latitude), so the error grows with latitude: measured
    2026-08-17, x1.0 at the equator, x2.0 at the Faroes, x2.3 in
    Troms and x21.5 on a Svalbard strip. The live-update gate
    therefore UNDERSTATED the map by those factors: a Faroes layer at
    2,676 m scored 19,995 against a 20,000 ceiling and launched a run
    that really wanted 40,235 tiles, and a Svalbard strip scored
    19,685 and really wanted 422,056 -- past the hard cap, refused
    with an empty note line. Asking QGIS to transform the rectangle
    costs one call and cannot drift from what the tiling does,
    because it is the same reprojection.

    A transform that fails -- a CRS pair PROJ cannot relate -- falls
    back to the old approximation rather than refusing, since a
    slightly wrong ceiling beats no map at all.
    """
    from . import compat
    if not compat.layer_data_is_available(layer):
      return None
    extent = layer.extent()
    if not layer.crs().isGeographic():
      return extent
    try:
      from qgis.core import (QgsCoordinateReferenceSystem,
                             QgsCoordinateTransform)
      transform = QgsCoordinateTransform(
        layer.crs(), QgsCoordinateReferenceSystem("EPSG:3857"),
        QgsProject.instance())
      return transform.transformBoundingBox(extent)
    except Exception:
      # the old approximation, kept as the fallback and named as one
      return QgsRectangle(extent.xMinimum() * 111_000,
                          extent.yMinimum() * 111_000,
                          extent.xMaximum() * 111_000,
                          extent.yMaximum() * 111_000)

  def _gpkg_key(self, path):
    """The key under which one GeoPackage's tables are recorded.

    Args:
      path: the file, spelt however the caller happens to hold it --
        from a layer's own source, or from the file widget.

    Returns:
      A form that two spellings of one file share, so the record
      cannot split in two; the path unchanged when it is empty.

    Why not the path itself. `same_destination` taught `_last_path`
    to compare files rather than strings on 2026-08-17; this record
    was its twin and was not told. One file under two spellings gave
    two keys, so a run could not see the tables an earlier run had
    written and a shrinking design orphaned a table in the file the
    user sends on.
    """
    if not path:
      return path
    # DEVICE AND INODE WERE TRIED HERE AND WITHDRAWN, hours later the
    # same night. They answer "one file, two spellings" exactly -- and
    # they also change when the file is REPLACED rather than edited,
    # which is what a sync client, an rsync, a restore or a copied-in
    # file from a colleague all do. Measured: three elements written,
    # the file replaced, the design shrunk to two, and `tiles_c` stayed
    # in the GeoPackage while the record split across two keys. That is
    # the very harm this key was introduced to prevent, arriving
    # through its own fix. A path outlives the bytes at it; an inode
    # does not, and this record is about the destination rather than
    # about a particular copy of it.
    try:
      settled = os.path.normcase(os.path.realpath(path))
    except (OSError, ValueError):
      settled = os.path.normcase(path)
    # `normcase` folds case on Windows only, so ask this VOLUME
    # whether it folds -- macOS usually does, Linux usually does not,
    # and the answer belongs to the disk rather than to the platform.
    # Probed on the resolved name, so a symlink cannot mislead it.
    try:
      folder, leaf = os.path.split(settled)
      if leaf and leaf != leaf.upper() and os.path.exists(
          os.path.join(folder, leaf.upper())):
        return settled.lower()
    except (OSError, ValueError):
      pass
    return settled

  def _a_reading_of_the_data(self, layer):
    """What a dataset looks like now, for comparing against later.

    Args:
      layer: the dataset to read.

    Returns:
      A comparable pair: what the layer CONTAINS structurally, and how
      many edits this dialog has heard on it.

    WHY TWO TERMS, and the second is the one that was missing. The
    fingerprint reads the feature count, the extent, the field names
    and the CRS — none of which an ordinary VALUE EDIT moves. So the
    moved-data notice, whose own commit message cites {7,17,27,37}
    travelling beside a map drawn from {0,1,2,3}, could not report the
    case it was written for: measured 2026-08-28 by the `undoredo`
    hunt, which corrupted the data identically on two journeys and got
    a warning only on the one that also deleted a feature. A keystroke
    unrelated to whether the data moved decided whether anybody was
    told.
    THE EDIT COUNT IS PER DATASET rather than the session's own
    `_data_version`, which rises when any watched layer is edited and
    would report a map as moved because somebody edited a different
    one.
    WHAT IT STILL CANNOT SEE is an edit made straight through the data
    provider, which emits nothing this dialog hears. That is the limit
    `_layer_fingerprint` already documents at length and a decision of
    2026-08-13 rather than an oversight; the alternative is scanning
    the values, and the honest place to reconsider it is there.
    """
    return (self._layer_fingerprint(layer),
            self._edits_by_layer.get(layer.id(), 0))

  def _note_the_data_this_map_opened_over(self, record, path):
    """Record what the region looked like as a saved map was opened.

    Args:
      record: the working state read out of the file, whose "region"
        names the dataset the map was drawn from.
      path: the GeoPackage being opened, so a source pointing INTO
        that file — the embedded copy — is recognised as this map's
        own data rather than as somebody else's layer.

    Returns:
      None. It writes one entry into `_fingerprint_when_drawn`, or
      nothing at all where the region in force is not this map's.

    WHY A RESUME NEEDS THIS AT ALL. Those readings are taken at
    landings, and a Load is not one — so the moved-data notice could
    never speak about a map that was OPENED rather than drawn. Somebody
    opens a saved map, edits their region, presses Save, and the file
    ends up holding tiles cut from the old numbers beside a copy of the
    new ones with nothing said, which is the exact state the notice
    exists to announce and the journey a shared file makes likeliest.
    Measured 2026-08-28 by the `repairs4` hunt, reading the file's
    tiles and its embedded copy back with bare OGR: {0,1,2,3,4,6,9}
    beside {7,8,9,10,11,13,16}.

    IT IS CALLED FROM BOTH RESUME BRANCHES, the fresh load and the
    already-open one, because they are two doors into the same room
    and this project has paid for a guard at one of them before. The
    first repair put it at the fresh-load door alone, and the test
    written beside it went red — the ordinary journey, opening a map
    whose layers are still in the project, takes the other door.

    WHAT IT CAN AND CANNOT SAY, since the reading is taken NOW rather
    than when the tiles were cut. It answers "has this data moved since
    you opened the map", which is what a Save after a Load is about. It
    cannot answer whether the sender's data had already moved before
    the file reached you — nothing here knows when those tiles were
    drawn — so it stays quiet about that rather than guessing.
    """
    chosen = self.layer_combo.currentLayer()
    if chosen is None:
      return
    here = chosen.source()
    # The same test the resume already applies to decide whether the
    # source came back at all: the recorded dataset, or the copy inside
    # the file where that is what was recovered. A chooser left on
    # somebody else's layer is not this map's data and gets no entry,
    # which is what keeps one map's reading off another map.
    if not here:
      return
    if not (same_source(here, record.get("region") or "")
            or str(here).startswith(str(path))):
      return
    self._fingerprint_when_drawn[chosen.id()] = self._a_reading_of_the_data(chosen)

  def _layer_fingerprint(self, layer=None):
    """What the region layer CONTAINS, cheaply enough to ask often.

    Args:
      layer: the layer to read. Defaults to whatever the region chooser
        holds, which is what both signatures want, since they ask about
        the design the user is editing NOW. Pass one explicitly where
        the question is about a PARTICULAR map's dataset rather than
        about the current one — the moved-data notice at Save does,
        because a chooser that has moved on would otherwise have the
        notice comparing two different datasets and calling the
        difference a change (measured 2026-08-28).

    Returns:
      A comparable tuple — feature count, extent rounded to the metre,
      field names, CRS — or None when no layer is chosen. Combined
      with ``_data_version`` this goes into both signatures.

    Why both this and the signals. This part is cheap, deterministic,
    and catches an edit that CHANGES WHAT IT MEASURES — the feature
    count, the bounding box, the field names, the CRS. The signals
    catch edits made through QGIS's own editing session. Between them
    they cover most of what a user does.

    WHAT NEITHER COVERS, stated plainly because the docstring here
    used to claim the opposite. An edit made straight through the
    DATA PROVIDER — which is what Processing and a good deal of
    plugin code do — emits no signal this dialog can hear, and if it
    rewrites values in place it moves nothing measured above. Every
    value in a column can change with the count, the extent, the
    names and the CRS all identical, and the plugin will not notice:
    Generate is then a silent no-op against data that has moved
    underneath it. Measured 2026-08-13.

    That is a LIMIT rather than a bug, and it is deliberate as of the
    same day (maintainer's decision): the alternatives are polling
    somebody's data or fingerprinting the values themselves, which
    costs a full scan on every check for a case the plugin cannot
    reliably detect anyway. The rule this file used to state — that
    "neither mechanism covers the other's blind spot" — was simply
    untrue, and a false promise in a docstring is worse than a known
    gap, because it stops anybody looking.

    The extent is rounded because it is floating-point and asking
    twice about an unchanged layer must give the same answer; a metre
    is far below the size of anything these tiles are drawn at.
    """
    from . import compat
    if layer is None:
      layer = self.layer_combo.currentLayer()
    if layer is None:
      return None
    if not compat.layer_data_is_available(layer):
      # The source is gone -- a deleted file, a dropped connection.
      # Reading extent() here would segfault QGIS outright, so nothing
      # below this line may run.
      #
      # ANSWER WITH THE LAST GOOD READING rather than with a sentinel.
      # A sentinel is a DIFFERENT value, so it moves the geometry
      # signature, so the restyle path reads a vanished file as a
      # changed design and declines -- silently. Standing still is the
      # honest answer here: nothing about what the user asked for has
      # changed, only whether it can be read, and that is a question
      # `_generate` asks for itself before it tiles anything.
      #
      # The fallback stays `("unavailable",)` for a layer we never got
      # to read at all, which is the safe default and the behaviour
      # this replaced.
      return self._last_good_fingerprint.get(layer.id(), ("unavailable",))
    count = layer.featureCount()
    if count < 0:
      # The provider does not know yet. Remote sources -- WFS, OGC API
      # - Features, an ArcGIS service, PostGIS over a slow link --
      # answer -1 until they have fetched, and some only ever return an
      # estimate. A number like that is worse than no number: it would
      # report changes that never happened and hide ones that did,
      # according to which way the estimate drifted. None says "not
      # known", and _data_is_unobservable decides what to do about it.
      #
      # Nothing is bumped here. An earlier version incremented the
      # data version from inside this method, which is a side effect
      # in a getter and, worse, a loop: both signatures call this on
      # every debounce tick, so an uncountable layer re-tiled
      # continuously -- across a network, with nobody watching.
      count = None
    ext = layer.extent()
    fingerprint = (
      count,
      # An EMPTY layer has no extent, and QGIS says so with DBL_MAX
      # sentinels rather than with zeros -- so `round()` on the width
      # meets NaN and raises `cannot convert float NaN to integer`.
      # Deleting every feature from the region layer is an ordinary
      # thing to do mid-session, and this runs from the live path and
      # from both signatures, where the raise goes to a console
      # nobody has open. Found by the stochastic hunt on 2026-08-13
      # (seeds 356, 401, 409) and reproduced directly. "empty" is a
      # perfectly good fingerprint: it differs from every real extent
      # and from itself never, so an emptied layer compares equal to
      # an emptied layer and unequal to one with data, which is all
      # this tuple is for. Guarded by
      # test_an_emptied_region_layer_does_not_raise.
      ("empty" if ext.isNull() or ext.isEmpty() else
       (round(ext.xMinimum()), round(ext.yMinimum()),
        round(ext.xMaximum()), round(ext.yMaximum()))),
      tuple(f.name() for f in layer.fields()),
      layer.crs().authid(),
    )
    # THE LAST READING TAKEN WHILE THE DATA WAS THERE, kept per layer
    # id so switching the chooser cannot hand one layer's history to
    # another. This is the only place a good reading is produced, so
    # it is the only place that records one.
    self._last_good_fingerprint[layer.id()] = fingerprint
    return fingerprint

  def _data_is_unobservable(self) -> bool:
    """Whether this layer can change without the plugin being able to tell.

    Returns:
      True for a layer that will not say how many features it has.
      That is the honest signature of a source living somewhere else
      -- a WFS, an OGC API - Features endpoint, an ArcGIS service, a
      database over a slow link -- which can be rewritten on a server
      with no file touched here and no signal raised.

    There is no clever way to close this gap. Counting the features
    ourselves means pulling the whole dataset across a network, and
    doing that on a debounce tick is worse than the problem. So the
    plugin is explicit about what it does not know, and the two
    callers answer differently: see _restyle_only, which always
    re-tiles such a layer when the user asks, and _maybe_live_generate,
    which declines to chase it.
    """
    layer = self.layer_combo.currentLayer()
    return layer is not None and layer.featureCount() < 0

  def _bump_data_version(self, *_args):
    """Record that the region layer changed under us.

    Args:
      *_args: whatever the emitting signal carries; all of them are
        ignored, because the only thing being recorded is THAT
        something changed.

    Returns:
      None. The counter feeds both signatures, so the next run cannot
      be skipped as a no-op, and a live update is queued so a user
      watching the map sees it follow their edit.

    A RETIRED DIALOG DOES NOTHING HERE. This is the fifth route into
    the work a dialog keeps doing after the user has finished with it,
    and the four gated on 2026-08-16 were all PROJECT or COMBO
    signals -- this one hangs off the region LAYER, which is why
    gating those four left it open. Measured 2026-08-17: deleting an
    assigned column pushed the identical warning once per dialog ever
    opened.
    """
    if _dialog_is_gone(self) or _live_dialog() is not self:
      return
    self._data_version += 1
    # ...AND AGAINST THE DATASET IT HAPPENED TO, which is what makes it
    # usable by anything asking about one map rather than about the
    # session. The watched layer is the only one whose signals reach
    # here, so this attribution needs no argument from the signal.
    # Its C++ half can be gone by the time a queued signal arrives --
    # removing a layer is what fires several of these -- and asking a
    # dead wrapper for its id raises, so the reading is guarded.
    watched = self._watched_layer
    if watched is not None:
      try:
        edited = watched.id()
      except RuntimeError:
        edited = None
      if edited:
        self._edits_by_layer[edited] = self._edits_by_layer.get(edited, 0) + 1
    # Follow the edit as well as recording it. This is the only place
    # a field being renamed, dropped or retyped is heard: the layer
    # COMBO does not change when a user edits the layer it is already
    # pointed at, so _on_layer_changed never runs and an element would
    # go on naming a column that has gone -- failing later, at the
    # join, with a message about a missing column rather than about
    # the edit that removed it.
    self._adapt_to_the_layer(self._watched_layer)
    self._queue_live()

  # The layer signals worth hearing. Editing through QGIS's own tools
  # goes through the edit buffer and ends in committedX / dataChanged;
  # updatedFields covers a column added, dropped or renamed; crsChanged
  # covers a CRS reassigned without reprojecting, which changes what
  # every coordinate means without changing one of them.
  _WATCHED_SIGNALS = ("dataChanged", "updatedFields", "crsChanged",
                      "featureAdded", "featuresDeleted", "geometryChanged",
                      "attributeValueChanged", "committedGeometriesChanges",
                      "committedAttributeValuesChanges", "editingStopped",
                      # A subset filter set in Layer Properties changes
                      # which features exist for everything downstream,
                      # without touching one of them.
                      "subsetStringChanged",
                      # The layer now reads from somewhere else, or has
                      # been reloaded from a file that changed underneath
                      # it. QGIS does not watch files, so this arrives
                      # only when something asks the layer to reload --
                      # the Reload command, an auto-refresh interval --
                      # but when it does arrive the map is out of date.
                      "dataSourceChanged")

  # repaintRequested is deliberately NOT in that list, though it looks
  # tempting. It fires on every style change too, and re-tiling on a
  # style change is the exact cost the restyle fast path exists to
  # avoid.

  def _watch_layer(self, layer):
    """Listen to the chosen layer, and stop listening to the last one.

    Args:
      layer: the newly chosen region layer, or None.

    Returns:
      None. Connections are made defensively: the signal list is
      QGIS's, and a future release may drop one. A missing signal
      should cost this plugin one blind spot, not an exception on
      every layer change, so each is connected only if it exists.
    """
    previous = self._watched_layer
    if previous is not None and previous is not layer:
      # The whole loop is guarded, not merely the disconnect. When a
      # layer is removed from the project its C++ object goes with it,
      # and then even ASKING the Python wrapper for an attribute
      # raises RuntimeError -- which is precisely the moment this runs,
      # since removing the layer is what changed the combo.
      try:
        # repaintRequested is included on the way OUT whether or not it
        # was connected on the way in: disconnecting something that was
        # never connected is caught below, whereas leaving one behind
        # would re-tile on every style change of a layer the user has
        # moved on from.
        for name in tuple(self._WATCHED_SIGNALS) + ("repaintRequested",):
          signal = getattr(previous, name, None)
          if signal is not None:
            try:
              signal.disconnect(self._bump_data_version)
            except (TypeError, RuntimeError):
              pass          # never connected; nothing to undo
      except RuntimeError:
        pass                # the layer is already gone, signals with it
    self._watched_layer = layer
    # The ID is kept BESIDE the object, because it is the only part
    # that survives the layer's destruction: once QGIS removes a
    # layer, asking its Python wrapper for id() raises RuntimeError,
    # and `layersRemoved` arrives exactly then. See _layers_removed.
    self._watched_layer_id = layer.id() if layer is not None else None
    if layer is None:
      return
    # A layer QGIS reloads on a timer is one the user has declared
    # dynamic, and its reload arrives as a repaint rather than as any
    # of the editing signals. That is the ONLY circumstance in which
    # repaintRequested is worth hearing: on an ordinary layer it also
    # fires for every style change, and re-tiling on those is the whole
    # cost the restyle fast path exists to avoid.
    from . import compat          # imported here, as elsewhere in this file
    names = list(self._WATCHED_SIGNALS)
    if compat.layer_auto_refreshes(layer):
      names.append("repaintRequested")
    for name in names:
      signal = getattr(layer, name, None)
      if signal is not None:
        try:
          signal.connect(self._bump_data_version)
        except (TypeError, RuntimeError):
          pass

  def _adapt_to_the_layer(self, layer):
    """Follow the layer when an edit makes a setting untrue.

    Args:
      layer: the current region layer, or None.

    Returns:
      None. Settings may be changed, and anything changed is reported.

    Adapting rather than only complaining, because in these cases
    there is exactly one sensible answer and making the user find it
    is busywork. Where there is NOT one sensible answer the dialog
    does not guess: a field that vanished while another appeared may
    be a rename or may be two unrelated edits, and quietly pointing an
    element at the NEW column would map data the user never asked for.
    So it does not do that: the element re-defaults to a surviving
    field and the user is told which one it landed on, and only when
    no field survives at all does it go unassigned. Losing a column
    costs an element its variable, not its place on the map.
    (This block said the element was unassigned, which the comment
    twenty lines below and CLAUDE.md both contradict; corrected
    2026-08-12.)
    """
    if layer is None:
      return
    from . import compat
    if not compat.layer_data_is_available(layer):
      return                      # nothing safe to read; see _generate

    # The spacing is a number of the LAYER's units, so a CRS change
    # silently changes what it means: 500 metres becomes 500 feet, or
    # 500 of whatever a layer with no CRS is counted in. Re-deriving
    # is the only sensible answer -- the old number is not wrong so
    # much as no longer about anything -- and it is exactly the kind
    # of adaptation that must be announced, because a user who typed
    # a spacing will otherwise find it changed with no explanation.
    authid = layer.crs().authid()
    if self._watched_crs is not None and authid != self._watched_crs:
      self._watched_crs = authid
      before = self.spacing_spin.value()
      self._auto_spacing()
      after = self.spacing_spin.value()
      if abs(after - before) > 1e-9:
        self._report_quietly(
          f"The layer's coordinate system changed, so the spacing has "
          f"been recalculated as {after:,.6f}".rstrip("0").rstrip(".")
          + " " + compat.map_unit_label(layer) + ".")
    else:
      self._watched_crs = authid

    names = tuple(f.name() for f in layer.fields())
    if names == self._watched_fields:
      return
    lost = [n for n in self._watched_fields if n not in names]
    self._watched_fields = names

    # Whatever else changed, the choosers must now offer exactly the
    # columns the layer has. A column ADDED in QGIS -- the Field
    # Calculator is the usual way -- was previously invisible here
    # until the user switched layers and back, with nothing on screen
    # to suggest that was the remedy.
    #
    # In place, never by rebuilding the table: a rebuild replaces every
    # cell widget, and one arriving mid-interaction is the "race among
    # choosers" this project has already paid for once, where an open
    # dropdown dies and the pick commits to a dead widget. Editing the
    # items of the existing combos leaves widget identity alone, which
    # is what that race's regression test checks.
    wanted = ["---"] + list(names)
    # What each row was showing BEFORE the item lists are rewritten.
    # Rewriting them drops any selection naming a column that has gone,
    # so a later pass asking "which rows lost their column" would find
    # none: they would all read "---" already, and the re-default below
    # would never fire. Read first, then rewrite.
    chosen_by_row = {}
    for row in range(self.table.rowCount()):
      combo = self.table.cellWidget(row, 1)
      if combo is not None and hasattr(combo, "currentText"):
        chosen_by_row[row] = combo.currentText()
    for row in range(self.table.rowCount()):
      combo = self.table.cellWidget(row, 1)
      if combo is None or not hasattr(combo, "itemText"):
        continue
      if [combo.itemText(i) for i in range(combo.count())] == wanted:
        continue
      chosen = chosen_by_row.get(row, combo.currentText())
      combo.blockSignals(True)
      combo.clear()
      combo.addItems(wanted)
      # A choice that survived the edit is kept; one whose column has
      # gone falls back to unassigned, and the message below says so.
      combo.setCurrentText(chosen if chosen in wanted else "---")
      combo.blockSignals(False)

    if not lost:
      return
    # An element pointed at a column that is no longer there. Leaving
    # it would fail at the join, deep inside a run, with a message
    # about a missing column rather than about the user's own edit.
    #
    # It re-defaults to a surviving field rather than being unassigned,
    # and that is a settled decision rather than a convenience: losing
    # a column costs an element its VARIABLE, not its place on the map.
    # An element left unassigned draws as flat fill, so a deletion in
    # QGIS would quietly cost the map two of its four variables. The
    # preference is the same one _refresh_table uses -- numeric fields,
    # skipping the ones that are obviously row identifiers -- because
    # two rules for "which field would this element sensibly show"
    # would drift apart and then disagree in front of a user.
    fields = self._layer_fields()
    id_like = {"fid", "objectid", "id", "gid", "ogc_fid"}
    numeric = [f for f in fields if self._field_is_numeric(f)]
    preferred = [f for f in numeric if f.lower() not in id_like] \
        or numeric or fields
    moved = []
    for row in range(self.table.rowCount()):
      combo = self.table.cellWidget(row, 1)
      was = chosen_by_row.get(row)
      if combo is None or was not in lost:
        continue
      identifier = self.table.item(row, 0)
      tid_here = identifier.text() if identifier else None
      mode_cell = self.table.cellWidget(row, 2)
      # ...AND THE STYLE GOES WITH THE COLUMN, which is the same ruling
      # as a change of region dataset and a THIRD door into it. The
      # other two are answered in `_refresh_table`, which asks whether
      # the element's remembered column is still in the layer -- and
      # cannot see this one, because this loop re-points the row at a
      # column that IS. Measured 2026-08-20: deleting 'landcover' in
      # QGIS moved the element to a numeric 'v2' and left the
      # categorical scheme on it. Since 2026-08-21 the WHOLE scheme
      # goes with the column, onto the shelf, and an element PREFERS a
      # field it has shown before, bringing that field's scheme back.
      # The seven rulings are in CLAUDE.md.
      if tid_here and mode_cell is not None:
        _dump("DOOR-3", tid_here, "sees", mode_cell.currentText())
        self._shelve_scheme(tid_here, {
          "var": was,
          "mode_raw": mode_cell.currentText(),
          "style_touched": bool(mode_cell.property("touched")),
        })
      remembered = None
      if tid_here:
        shelf = self._scheme_memory.get(tid_here, {})
        held = [f for f in fields if f in shelf]
        if held:
          remembered = held[0]
      now = remembered if remembered is not None else (
        preferred[row % len(preferred)] if preferred else "---")
      combo.blockSignals(True)
      combo.setCurrentText(now)
      combo.blockSignals(False)
      combo.setProperty("ws_last_var", now)
      restored = self._unshelve_scheme(tid_here, remembered) \
          if tid_here and remembered is not None else None
      instead = self._plausible_mode(now)
      if restored is not None and mode_cell is not None:
        back = restored.get("mode_raw") if restored.get("touched") \
            else instead
        if back in self.MODES and mode_cell.findText(back) >= 0:
          mode_cell.blockSignals(True)
          mode_cell.setCurrentText(back)
          mode_cell.blockSignals(False)
        mode_cell.setProperty("touched", bool(restored.get("touched")))
        mode_cell.setProperty("last_style", mode_cell.currentText())
        self._sync_row(row)
        # ...AND THE CONTROLS COME HOME WITH IT. This door edits in
        # place and never rebuilds, so restoring the RECORDS left the
        # widgets showing whatever the element wore while its column
        # was away: a hunt measured a map made with nine classes of
        # YlOrBr coming home as five of Reds, and reading YlOrBr at
        # nine one unrelated rebuild later -- three maps from one set
        # of choices. Where a path edits in place, the widgets ARE the
        # state, which is this block's second lesson of the night.
        back_ramp = restored.get("ramp")
        ramp_cell = self.table.cellWidget(row, 4)
        if back_ramp and ramp_cell is not None \
            and hasattr(ramp_cell, "findText") \
            and ramp_cell.findText(back_ramp) >= 0:
          ramp_cell.blockSignals(True)
          ramp_cell.setCurrentText(back_ramp)
          ramp_cell.blockSignals(False)
        back_k = restored.get("k")
        k_cell = self.table.cellWidget(row, 3)
        if back_k and k_cell is not None and hasattr(k_cell, "setValue"):
          k_cell.blockSignals(True)
          k_cell.setValue(int(back_k))
          k_cell.setProperty("user_k", int(back_k))
          k_cell.blockSignals(False)
        switch = self._row_reverse(row)
        if switch is not None:
          switch.blockSignals(True)
          switch.setChecked(bool(restored.get("reverse")))
          switch.blockSignals(False)
      elif mode_cell is not None and mode_cell.findText(instead) >= 0:
        # RE-DERIVED WHOEVER CHOSE IT. This required `touched` until a
        # hunt read the MAP on 2026-08-25: a DERIVED categorical style
        # on a deleted text column stayed categorical on the numeric
        # column the element landed on, and Generate drew 37
        # categories -- one legend line per value. The ruling is about
        # the COLUMN going, not about who picked the style, and the
        # widget reset below already worked that way; the two halves
        # of one block disagreed.
        mode_cell.blockSignals(True)
        mode_cell.setCurrentText(instead)
        mode_cell.blockSignals(False)
        mode_cell.setProperty("touched", False)
        mode_cell.setProperty("last_style", instead)
        self._sync_row(row)
      if mode_cell is not None and restored is None:
        # ...AND THE CONTROLS THEMSELVES, for EVERY row whose column
        # has gone AND NOTHING WAS RESTORED. That last clause is a
        # regression this block caused within the hour of being
        # widened: when the shelf hands a scheme back -- an element
        # coming home to a column that has returned -- this ran a line
        # later and overwrote it, so a map made with nine classes of
        # YlOrBr came home as five of Reds, and one unrelated rebuild
        # later read Reds at nine. Three maps from one set of choices.
        # has gone rather than only one whose STYLE somebody chose.
        # This sat inside the branch above for an hour on 2026-08-25
        # and a hunt found the hole: `_shelve_scheme` pops the records
        # for every dropped row, so a user who picked a RAMP and
        # accepted the derived style lost it twice -- the ramp went on
        # painting the replacement column, then flipped to a default
        # at the next unrelated rebuild. This door edits the row IN
        # PLACE and never rebuilds (the race-among-choosers rule), so
        # the widgets ARE the state and clearing the records alone is
        # half a fix.
        fresh = self.DEFAULT_RAMPS[row % len(self.DEFAULT_RAMPS)]
        ramp_cell = self.table.cellWidget(row, 4)
        if ramp_cell is not None and hasattr(ramp_cell, "findText") \
            and ramp_cell.findText(fresh) >= 0:
          ramp_cell.blockSignals(True)
          ramp_cell.setCurrentText(fresh)
          ramp_cell.blockSignals(False)
          if tid_here:
            self._ramp_choices[tid_here] = fresh
        k_cell = self.table.cellWidget(row, 3)
        if k_cell is not None and hasattr(k_cell, "setValue"):
          k_cell.blockSignals(True)
          k_cell.setValue(5)
          k_cell.setProperty("user_k", 5)
          k_cell.blockSignals(False)
        switch = self._row_reverse(row)
        if switch is not None:
          switch.blockSignals(True)
          switch.setChecked(False)
          switch.blockSignals(False)
          if tid_here:
            self._reverse_choices[tid_here] = False
      moved.append((was, now))
      # THE PICKS ARE KEPT, exactly as the graduated ones are. This
      # used to pop the categorical record for the vanished field,
      # while `_quant_colours` was left alone -- so renaming a column
      # in QGIS destroyed every colour a user had picked by hand for
      # that element, unannounced, and renaming it straight back did
      # not bring them home. The graduated twin survived the same
      # act. Both records are keyed by element AND field, which is
      # what makes keeping them safe: a field that never returns
      # costs a few bytes, and a field that does return -- a rename
      # undone a second later, which is the ordinary case -- finds
      # its colours waiting. Made symmetrical on the maintainer's
      # instruction, 2026-08-13. Guarded by
      # test_a_renamed_column_does_not_destroy_hand_picked_colours.
    if moved:
      gone = sorted({was for was, _ in moved})
      landed = sorted({now for _, now in moved if now != "---"})
      if landed:
        self._report_quietly(
          f"{', '.join(gone)} is no longer in the layer, so the "
          f"elements using it now show "
          f"{', '.join(landed)} instead.")
      else:
        self._report_quietly(
          f"{', '.join(gone)} is no longer in the layer, and there is "
          f"nothing left to show in its place.")

  def _auto_spacing(self):
    """Derive a coarse spacing from the layer extent (about fifteen
    repeating units across), rounded to a clean number. Degrees are
    scaled to rough metres because geographic layers get reprojected
    to Web Mercator before tiling."""
    from . import compat
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return
    if not compat.layer_data_is_available(layer):
      # extent() on a layer whose source has gone segfaults QGIS; see
      # compat.layer_data_is_available.
      self._report_quietly(
        "That layer's data is no longer available, so a spacing "
        "cannot be suggested.")
      return
    # measured where the TILING works, not in degrees scaled by a
    # constant that is only right at the equator -- see
    # _extent_in_working_units
    ext = self._extent_in_working_units(layer) or layer.extent()
    dim = max(ext.width(), ext.height())
    if math.isfinite(dim) and dim > 0:
      # DECIMALS FIRST, THEN THE VALUE, and that order is the whole
      # of it: a spin box rounds whatever it is given to the decimals
      # it currently has, so setting a spacing of 0.47 into a box
      # showing none stores 0. The suggestion is the only number that
      # knows this layer's scale -- a floor plan and a country arrive
      # through this same line -- which is why the figures are sized
      # here rather than at construction, where the box holds a
      # default that says nothing about anybody's data.
      suggested = _nice_number(dim / 15)
      # THE NUMBER THIS WRITES IS THE PLUGIN'S, and the assignment
      # BELOW the write is what says so. `setValue` emits
      # `valueChanged` synchronously, so `_spacing_typed` runs first
      # and marks the box as somebody's choice; clearing it afterwards
      # is what corrects that. THE ORDER IS LOAD-BEARING -- moved above
      # the write, every suggestion would look hand-typed and no
      # dataset would ever get a spacing derived for it again.
      # A `_deriving_spacing` guard stood here and was DELETED on
      # 2026-08-25, when its catalogue entry could only SURVIVE: this
      # is the only programmatic writer of the box (the construction
      # default is set before the handler is connected), so the guard
      # and the assignment did one job twice and mutating either
      # changed nothing any test could see. Redundant is not free --
      # it costs a permanent survivor in the catalogue and a reader
      # who cannot tell which mechanism is the live one.
      self.spacing_spin.setValue(suggested)
      # ...INCLUDING WHEN THE USER PRESSED Auto, which is the point of
      # clearing it here rather than only on the layer-change path:
      # asking for a suggestion is handing the choice back.
      self._spacing_is_mine = False
    else:
      # No usable extent: a layer with no CRS, or an empty one. Leave
      # the spacing alone rather than guessing from a bad number, and
      # say so, because the user pressed a button and is owed an
      # answer either way. Ownership is left alone with it: nothing was
      # written, so whoever's number is in the box is still theirs.
      self._report_quietly(
        "That layer has no usable extent, so a spacing cannot be "
        "suggested. Type a spacing instead.")

  def _spacing_typed(self, _value):
    """Record that the number in the spacing box is the user's own.

    Args:
      _value: the box's new value, which this does not read. The
        handler is about WHO changed the spacing, never about what to.

    Returns:
      None. Sets `_spacing_is_mine`, which is what carries a typed
      spacing across a change of dataset.

    IT FIRES FOR THE PLUGIN'S OWN WRITE TOO, and that is deliberate
    rather than overlooked. `_auto_spacing` clears the flag on the line
    after its `setValue`, so a suggestion ends up marked as the
    plugin's whichever order the signals run in. A second guard here
    was written and removed the same day: two mechanisms for one rule
    meant the catalogue could kill neither alone, which is a permanent
    survivor rather than a guarded behaviour.
    """
    self._spacing_is_mine = True

  def _layer_fields(self) -> list[str]:
    """Attribute (column) names of the region layer; ``fields()`` is
    QGIS's schema accessor, analogous to a GeoDataFrame's columns.

    OUR OWN PRIMARY KEY IS NOT ONE OF THEM. A GeoPackage this plugin
    wrote carries `weavingspace_fid`, the key column named so it
    cannot collide with a user column called fid -- and a region layer
    read back out of such a file therefore arrives carrying it. That
    is not the user's data and mapping it cannot mean anything, so it
    is not offered.

    MEASURED 2026-08-25, on the resume path that made it reachable: an
    element defaulted onto `weavingspace_fid` (numeric, and not in the
    id-like list, so the default picker took it), the run named its
    table `tiles_a_weavingspace_fid`, and the write failed outright --
    "UNIQUE constraint failed", because the writer sets that column as
    the FID while the data now held one too. Sixteen of sixty-one
    features written and the whole landing lost.
    """
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return []
    return [f.name() for f in layer.fields()
            if f.name() != bridge.GPKG_FID_COLUMN]

  def _field_is_numeric(self, name: str) -> bool:
    """Whether a field holds numbers (drives the Quant/Categorized
    default in ``_plausible_mode``)."""
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return False
    idx = layer.fields().indexOf(name)
    return idx >= 0 and layer.fields().field(idx).isNumeric()

  # ---------------------------------------------------------------- preview

  def _queue_preview(self, *args):
    """Debounced funnel for DESIGN-tab changes: restart both countdowns
    (unit + table rebuild and preview repaint after the preview
    debounce, live map
    regeneration at 900 ms). Signal payloads arrive in *args and are
    ignored.

    Data & colours widgets must NOT use this path: the rebuild it
    schedules replaces every table cell widget, and a rebuild landing
    a debounce after one palette pick destroys the chooser the user has
    open for the next one (the "race among choosers" this once
    caused). They use _refresh_preview_colours instead.
    """
    self._preview_timer.setInterval(self._preview_wait())
    self._preview_timer.start()
    self._queue_live()

  def _refresh_preview_colours(self, *args):
    """Light path for Data & colours changes: repaint the preview with
    the current per-element colours and queue a live regeneration —
    without touching the unit or the table, whose widgets stay the
    same objects throughout (so open dropdowns and half-made picks
    survive)."""
    if self._unit is not None:
      self.preview.show_unit(self._unit, self._table_id_colours(),
                             self.shells_spin.value())
    self._queue_live()

  def _queue_live(self, *args):
    """Debounced funnel for output-affecting changes; also the choke
    point where the table's dynamic columns are kept coherent, since
    every relevant control change passes through here.

    A CLOSED dialog arms nothing. Stopping the timers on the way out
    was not enough, because the region layer's own signals are still
    connected and re-arm them: see closeEvent for what that cost.
    """
    self._update_dynamic_columns()
    if self._closed:
      return
    self._live_timer.start()

  def retire(self):
    """Stand this dialog down for good, because the plugin is going.

    Returns:
      None. Clears the record of which dialog is in charge, when that
      is this one, and marks this dialog closed. Nothing is
      disconnected: an element layer outlives the dialog that made it
      and its lambda is an ordinary Python object Qt goes on calling,
      so every long-lived connection here is guarded AT THE HANDLER
      rather than at a teardown site -- which is what makes clearing
      one record enough to silence all of them.

    THE GATE ASKED WHICH OF US IS IN CHARGE AND NEVER WHETHER ANY OF
    US SHOULD BE. Retirement here only ever happened by SUCCESSION: a
    new dialog takes the record, and the old one's handlers see
    `_live_dialog() is not self` and return. With no successor the
    record goes on naming a dialog the user has disposed of -- so
    disabling the plugin in QGIS's Plugin Manager left it adopting
    dock edits, rewriting the project's group record, and pushing
    sentences into QGIS's message bar about controls in a window there
    is no longer any way to open. It lasted until QGIS was restarted.
    (Found by the two-dialogs hunt, 2026-08-27.)

    IT DOES NOT CLEAR THE RECORD OF WHO IS IN CHARGE, and that was
    the first attempt. The gate reads "if there IS a live dialog and
    it is not me, drop" -- None means "nobody has said", so clearing
    the record makes EVERY dialog believe it is in charge rather than
    none. Measured 2026-08-27: the message the disabled plugin had
    just been fixed for came straight back. So retirement is a fact
    about this dialog, read by `_dialog_is_gone`, which every
    long-lived handler already asks first.

    NOT CALLED WHEN THE WINDOW IS MERELY CLOSED, and that is the
    distinction the fix turns on: `plugin.open_dialog` REUSES this
    object, so a closed window is a hidden one that the user may bring
    back with its map, its records and its adopted edits intact.
    Retiring there would leave a dialog that can be reopened and can
    no longer do anything.
    """
    self._closed = True
    self._retired = True
    # AND THE COLOUR EDITOR GOES WITH THE DIALOG, which the twin that
    # retires a PREVIOUS instance has done since 2026-08-26 and this
    # one did not. That window holds no layer and writes to the
    # dialog's records, so a plugin the user has DISABLED left a live
    # editor repainting their output layers and restamping the group's
    # record -- from a plugin they had turned off, with no way left to
    # open it and see. Measured 2026-08-28: element a's renderer moved
    # under a pick made after `retire(); close()`, and the colour
    # reached the saved .qgz twice.
    # The two teardowns are twins written a day apart, and this is the
    # line the later one did not copy.
    if self._open_editor is not None:
      try:
        self._open_editor.reject()
      except Exception:
        pass
    _dump("RETIRE", "plugin-unloaded")

  def closeEvent(self, event):  # noqa: N802 (Qt API)
    """Qt calls this when the window closes.

    Args:
      event: the close event, passed through untouched.

    Returns:
      None. A tiling in flight is cancelled, so a closed dialog does
      not go on computing invisibly (the task's cancel path still
      reports once, resetting our state; see worker.py), and the
      DEBOUNCE TIMERS ARE STOPPED. Cancelling the task alone was not
      enough: a live-update timer armed a moment before the close
      fires ~900ms later, and _maybe_live_generate then starts a
      fresh tiling that writes layers into the project on behalf of a
      window nobody can see -- which is exactly what a user unloading
      the plugin has asked not to happen.
    """
    if self._task is not None:
      try:
        self._task.cancel()
      except Exception:
        pass
    for timer in (getattr(self, "_live_timer", None),
                  getattr(self, "_preview_timer", None)):
      if timer is not None:
        try:
          timer.stop()
        except RuntimeError:
          pass                  # the Qt object is already gone
    self._live_pending = False
    self._press_pending = False   # a closed window presses nothing
    # And the dialog is CLOSED, which the timers alone could not say.
    # Stopping them stopped the beat already armed; it did nothing
    # about the region layer's own signals, which stay connected to a
    # closed window and re-arm the timer on the user's next edit. So
    # a user who closed the dialog, DELETED the output group -- which
    # this project documents as the whole of the undo -- and then
    # edited their own data got the group and every element layer
    # written straight back, by a window they had shut. Its twin
    # `_retire_previous_instance` had this right for a superseded
    # dialog all along, by unchecking live update on the way past;
    # this path never learned it. Measured 2026-08-13. showEvent
    # clears the flag, so reopening restores the user's own setting
    # rather than silently turning live update off.
    # Guarded by test_a_closed_dialog_writes_nothing_into_the_project.
    self._closed = True
    super().closeEvent(event)

  def showEvent(self, event):  # noqa: N802 (Qt API)
    """Qt calls this when the window (re)appears.

    The fit below is a THIRD call site -- construction and family
    changes fit the window too -- and no test can tell its removal
    from the others, because the window will not grow past what the
    design needs nor shrink below its layout minimums. It is kept
    deliberately (user decision, 2026-08-10): the occasion it guards
    lives in real QGIS, a re-show after a screen or DPI change, and
    a window opening too small to show its own controls is the fault
    this line exists to prevent. Its catalogue entry is accepted
    rather than closed, with the evidence recorded there. Two duties: re-fit
    the height once real layout geometry exists, and recover from any
    zombie task (we believe a run is active but the task manager shows
    it dead), which otherwise blocks all future generations."""
    self._closed = False
    super().showEvent(event)
    QTimer.singleShot(0, self._fit_to_design)
    if self._task is not None:
      try:
        from . import compat
        alive = self._task.status() in compat.task_active_statuses()
      except Exception:
        alive = False
      if not alive:
        self._task = None
        self.generate_btn.setEnabled(True)
        self.progress.setVisible(False)

  def _maybe_live_generate(self):
    """Debounced auto-generation, including the very first map.

    Runs whenever it is safe and cheap: live update on, temporary-layer
    output only (regenerating a GeoPackage on every tweak would hammer
    the disk), not in keep-both-groups mode, no task in flight (then it
    just flags a rerun), a layer and at least one variable in place, a
    modest estimated tile count (the estimate uses the layer's extent
    directly to avoid building a GeoDataFrame just to decide), and
    settings actually different from the last completed run. The first
    render needs no button press; choosing a layer is enough.
    """
    if self._closed:
      _dump("LIVE-GATE", "closed")
      return          # a shut window draws nothing
    self.live_note.setText("")
    if not self.live_check.isChecked():
      _dump("LIVE-GATE", "live-update-off")
      return
    # THE OUTPUT-PATH HALF OF THIS GATE IS DELETED, not explained.
    # (Ruling of 2026-08-27.) It stopped live update the moment an
    # output path was set, silently, while the user guide promised a
    # note -- and its reason was that a live run must not rewrite
    # somebody's file on every keystroke. Under "saving is a positive
    # act" no run writes at all, so the gate could not fire, and a
    # guard that cannot fire sits in the source reading as protection.
    # Ledger row 11 of that date.
    # "CREATE AS NEW GROUP" STAYS: it asks for a SECOND map to compare
    # against, and building one unattended on every keystroke is not
    # what anybody means by it.
    if self.opt_new_group.isChecked():
      _dump("LIVE-GATE", "new-group")
      return
    if self._task is not None:
      self._live_pending = True
      _dump("LIVE-GATE", "run-in-flight")
      return
    layer = self.layer_combo.currentLayer()
    if layer is None or self._unit is None:
      _dump("LIVE-GATE", "no-layer-or-unit")
      return
    if not compat_layer_available(self, layer):
      _dump("LIVE-GATE", "source-gone")
      # Same crash, reached from the live path -- and reachable long
      # before any of this session's changes: live update on, the file
      # deleted underneath, and QGIS is gone with no diagnostic.
      #
      # BUT THIS GUARD IS ABOUT TILING, AND THE EXIT BELOW IT IS ABOUT
      # PAINTING. A restyle re-seeds renderers on tiles that already
      # exist; it reads nothing from the region layer, which is
      # exactly why picking a ramp after the file moved worked
      # perfectly before the source ever came into question. Left as a
      # bare refusal this stood in front of that exit, so a colour
      # picked afterwards was recorded, never drawn, and explained by
      # a sentence about the DATA when the fact was about the FILE
      # (ledger row 4 of 2026-08-20). The rule it broke is one this
      # project already had: a guard that asks about one thing must
      # not stand in front of an exit that is about another.
      #
      # Nothing below this may read the layer -- `extent()` on a dead
      # source segfaults QGIS -- so the restyle is tried HERE rather
      # than by falling through. `_restyle_only` asks
      # `layer_data_is_available` for itself, through
      # `_layer_fingerprint`, and answers with the last good reading
      # instead of touching the extent.
      if self._restyle_only():
        # THE PAIR TRAVELS TO EVERY DOOR. This exit is four lines from
        # row 21's fix and was missing the same refresh: a restyle
        # answered here left the preview resting on the colours from
        # before the act, exactly the harm the pair below cures.
        # Found by the preview hunt of 2026-08-26 (round nine),
        # measured at the widget's own resting store.
        self._refresh_preview_colours()
        _dump("LIVE-GATE", "restyled-without-the-source")
        return
      if not self._said_source_gone:
        self._said_source_gone = True
        self._report_quietly(
          "That layer's data is no longer available, so the map "
          "cannot be updated.")
      return
    if self._data_is_unobservable():
      _dump("LIVE-GATE", "unobservable")
      # Live update works by noticing that something changed. This
      # layer will not say, so the only way to keep up would be to
      # re-tile on every tick -- which for a remote source means
      # fetching somebody's whole dataset over and over, unattended,
      # because a dialog happens to be open. Say so instead, once, and
      # leave Generate to do it when the user actually wants it.
      if not self._said_live_cannot_track:
        self._said_live_cannot_track = True
        self._report_quietly(
          "This layer does not report its size, so live update "
          "cannot follow it. Press Generate to redraw.")
      return
    if not any(a["var"] for a in self._assignments()):
      _dump("LIVE-GATE", "no-variable")
      return
    # THE EXTENT THE TILING WILL ACTUALLY SEE. This scaled degrees by
    # a flat 111,000, which understates a high-latitude map by up to
    # twentyfold and let live update launch runs far past the ceiling
    # this gate exists to enforce.
    ext = self._extent_in_working_units(layer)
    if ext is None:
      _dump("LIVE-GATE", "no-extent")
      return
    bounds = (ext.xMinimum(), ext.yMinimum(),
              ext.xMaximum(), ext.yMaximum())
    # ICON MODE IS NOT A TILING, and asking the tiling estimator about
    # it paused live update on maps of a hundred tiles. One unit goes
    # on each area, so the count is areas times elements and the
    # spacing decides how BIG an icon is drawn rather than how many
    # there are. Measured 2026-08-19: twenty-five areas and a
    # four-element unit answered 103,914 against 100 actually drawn,
    # which is five times this ceiling, so the map silently stopped
    # following the user. Ledger row 3.
    if self.opt_icons.isChecked():
      est = bridge.estimate_icon_count(self._unit, layer.featureCount())
    else:
      # THE GROUND, NOT THE BOX ROUND IT -- the fix of 2026-08-19 went
      # to the estimator's arithmetic and to Generate's caller, and
      # this caller kept the old question by passing no geometry. So
      # the path a user meets on EVERY KEYSTROKE went on counting the
      # bounding rectangle: two long islands occupying 4% of their own
      # extent read 64,098 tiles against 7,490 drawn, and live update
      # paused a map well under its own ceiling, telling the user a
      # number the run then disproved. Measured 2026-08-27 at 5.5x,
      # 8.6x, 34x and 2,592x on four sparse shapes.
      # A `None` ground is the older, more generous assumption and is
      # still honest, so a layer whose geometry cannot be measured
      # keeps exactly the behaviour it had.
      ground, edge = self._ground_and_edge(layer)
      est = bridge.estimate_tile_count_bounds(
        self._unit, bounds, covered_area=ground, covered_edge=edge)
    # A SENTINEL IS NOT A COUNT, and this gate has to say so first.
    # Both sentinels are NEGATIVE, so `est > LIVE_UPDATE_MAX_TILES` is
    # False for them: read as a number, a design that does not tile
    # the plane would sail through the gate and be handed to a run
    # that cannot draw it. The note has to be honest as well -- the
    # roadmap asked that it never read "about inf tiles", which is
    # what an unsplit sentinel would eventually have produced.
    if not bridge.is_a_size(est):
      self.live_note.setText(
        "live update paused: this design cannot be drawn on this "
        "layer; press Generate to see why")
      _dump("LIVE-GATE", "not-a-size", est)
      return
    if est > bridge.LIVE_UPDATE_MAX_TILES:
      self.live_note.setText(
        f"live update paused (about {est:,} tiles); press Generate")
      _dump("LIVE-GATE", "too-many-tiles")
      return
    if self._run_signature() == self._last_run_sig and \
        QgsProject.instance().layerTreeRoot().findGroup(
          self._group_name or "") is not None:
      _dump("LIVE-GATE", "same-signature")
      return  # nothing changed since the last run
    _dump("LIVE-GATE", "reached-restyle")
    if self._restyle_only():
      # ...AND THE PREVIEW LEARNS WHAT THE RESTYLE JUST PAINTED. The
      # control's own handler repainted the preview at pick time,
      # when the layers still wore the OLD style -- so without this
      # call the preview rests one act behind the map on every
      # style change the live path answers, and a person iterating
      # judges their design by colours the map no longer draws.
      # `_apply_style_change` pairs restyle-then-refresh; this path
      # never had the pair. Geometry endings self-heal by accident
      # (the landing's rebuild repaints), which is why only
      # style-ending acts rested stale. Found by the preview hunt of
      # 2026-08-26; shipping since 2026-08-17.
      self._refresh_preview_colours()
      _dump("LIVE-GATE", "restyled")
      return  # only the colours changed: done already, no tiling
    self._generate(live=True)

  def _unit_kwargs(self) -> dict:
    """Collect the TileUnit/WeaveUnit constructor arguments from the
    Design controls. The CRS is the region layer's EPSG code where it
    has one (weavingspace expects an int or authority string); layers
    in geographic coordinates fall back to 3857, matching the
    reprojection applied in bridge.layer_to_gdf."""
    spec = self._current_spec()
    layer = self.layer_combo.currentLayer()
    crs = 3857
    if layer is not None and not layer.crs().isGeographic():
      authid = layer.crs().authid()
      if authid.upper().startswith("EPSG:"):
        crs = int(authid.split(":")[1])
      else:
        crs = authid
    return dict(
      spec=spec,
      spacing=self.spacing_spin.value(),
      crs=crs,
      offset=self.opt_offset.value(),
      offset_angle=self.opt_offset_angle.value(),
      point_angle=self.opt_point_angle.value(),
      aspect=self.opt_aspect.value(),
      over_under=self.opt_over_under.text() or None,
      nrows=self.opt_grid_rows.value(),
      ncols=self.opt_grid_cols.value(),
    )

  def _build_unit(self):
    """Construct the Tileable exactly as the web app does: catalogue
    spec plus options, then the modifier chain rotate -> scale -> skew
    -> insets (tilings inset tiles and prototile in % of spacing;
    weaves scale the tile inset by aspect and have no prototile
    inset). Pure weavingspace; no QGIS involved."""
    kwargs = self._unit_kwargs()
    spec = kwargs.pop("spec")
    if spec is None:
      return None
    unit = catalog.make_unit(spec, **kwargs)
    # Apply each modifier only when it actually changes something.
    # An identity transform is not free: weavingspace rebuilds the
    # geometry, and the sub-micron rounding that follows can flip
    # which region polygon a tile overlaps most, so a map with all
    # modifiers at their defaults would differ slightly from the same
    # design built without them. Skipping identities also spares the
    # work on every preview rebuild.
    if self.mod_rotate.value():
      unit = unit.transform_rotate(self.mod_rotate.value())
    if (self.mod_scale_x.value(), self.mod_scale_y.value()) != (1.0, 1.0) \
        or self.mod_glyph.isChecked():
      unit = unit.transform_scale(
        self.mod_scale_x.value(), self.mod_scale_y.value(),
        self.mod_glyph.isChecked())
    if self.mod_skew_x.value() or self.mod_skew_y.value():
      unit = unit.transform_skew(self.mod_skew_x.value(),
                                 self.mod_skew_y.value())
    spacing = self.spacing_spin.value()
    if spec["type"] == "tiling":
      if self.mod_t_inset.value():
        unit = unit.inset_tiles(self.mod_t_inset.value() * spacing / 100)
      if self.mod_p_inset.value():
        unit = unit.inset_prototile(
          self.mod_p_inset.value() * spacing / 100)
    elif self.mod_t_inset.value():
      # a weave's tile inset is scaled by strand width, or thin
      # strands would vanish at inset values a tiling shrugs off
      unit = unit.inset_tiles(
        self.mod_t_inset.value() * self.opt_aspect.value() * spacing / 100)
    return unit

  def _preview_wait(self) -> int:
    """How long to wait for quiet before rebuilding the preview.

    Returns:
      Milliseconds: at least `PREVIEW_DEBOUNCE_MS`, at most
      `PREVIEW_DEBOUNCE_CEILING_MS`, and otherwise as long as the last
      rebuild actually took.

    A FLOOR RATHER THAN A FIXED WAIT, and the reasoning is at the
    constants. In short: the timer is single-shot and restarted by
    every change, so a shorter interval does not cause more rebuilds
    during continuous input -- it only starts the one rebuild sooner.
    What it does change is whether a HESITATION mid-interaction is
    absorbed, and that only matters where a rebuild is expensive. So
    the interval is asked to be at least as long as the last rebuild
    was, which makes a slow machine or a heavy design widen itself
    back towards the number this was flat at before, with no attempt
    here to guess at hardware nobody has measured.
    """
    return int(max(PREVIEW_DEBOUNCE_MS,
                   min(PREVIEW_DEBOUNCE_CEILING_MS,
                       getattr(self, "_last_rebuild_ms", 0.0))))

  def _rebuild_unit(self):
    """Rebuild the unit and everything derived from it (assignment
    table rows, preview). Runs on the main thread; unit construction
    is fast enough for that (the expensive step is the tiling itself,
    which is what the background task exists for)."""
    started = time.monotonic()
    try:
      self._unit = self._build_unit()
    except Exception as e:
      self._unit = None
      self.preview.show_message(f"Could not build tile unit:\n{e}")
      return
    if self._unit is None:
      self.preview.show_message("Pick a design to preview it.")
      return
    self._refresh_table()
    self.preview.show_unit(self._unit, self._table_id_colours(),
                           self.shells_spin.value())
    # WHAT THIS COST, so the next debounce can be at least this long.
    # See PREVIEW_DEBOUNCE_MS: the wait is a floor rather than a fixed
    # number precisely so a machine or a design nobody here measured
    # widens it back towards the old flat value on its own.
    self._last_rebuild_ms = (time.monotonic() - started) * 1000.0

  # ------------------------------------------------------------- data table

  def _tile_ids(self) -> list[str]:
    """Sorted distinct tile_id labels of the current unit ("a", "b",
    ...); one table row and one output layer per id."""
    if self._unit is None:
      return []
    try:
      return sorted(set(self._unit.tiles.tile_id),
                    key=bridge.element_order)
    except Exception:
      return []

  # sentinel item-data values in the class-source combo: SHARED is a
  # legacy value from when a dialog-wide style file existed (still
  # mapped to automatic for old stored choices); BROWSE marks the
  # "Choose file..." entry that opens a file dialog
  SHARED, BROWSE = "__shared__", "__browse__"
  # qualitative colour sets cycled as defaults for categorized rows
  CAT_DEFAULT_RAMPS = ["tab10", "Set2", "Set1", "Pastel1", "Dark2", "Set3"]

  def _category_count(self, field_name: str, tile_id: str = "") -> int:
    """How many categories a categorized row's element draws.

    Args:
      field_name: the column that row is drawing.
      tile_id: the element, when one is known. Its OUTPUT LAYER is
        asked first, because the cell is a report and must describe
        the element it sits beside; the region answers only before
        anything has been drawn, or when that element has no output.

    Returns:
      The count of distinct non-null values, greyed into the Classes
      cell.

    IT REPORTS THIS ELEMENT, NOT THE MAP (settled with the maintainer,
    2026-08-15). It read the region for every row, so four elements
    sharing a column all showed 6 while one of them drew 5 -- the
    Classes cell describing somebody else's element. Rows sharing a
    column may now legitimately read 6, 6, 6, 5, and all four are
    true: the odd one is the element with no tile of that value. No
    notice is raised when they differ, because elements differ
    routinely on real data and a warning that fires constantly is one
    people learn to ignore.

    The colours themselves are decided map-wide, so a difference here
    is a difference in what an element CONTAINS and never in what a
    colour MEANS.

    ``uniqueValues`` asks the layer's data provider, which may scan
    the table, hence the cache keyed by (layer id, field); the cache
    clears when the layer changes."""
    drawn = QgsProject.instance().mapLayer(
      self._element_layer_ids.get(tile_id, "")) if tile_id else None
    if drawn is not None:
      index = drawn.fields().indexOf(field_name)
      if index >= 0:
        return len({v for v in drawn.uniqueValues(index)
                    if v is not None and str(v) != "NULL"})
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return 0
    idx = layer.fields().indexOf(field_name)
    if idx < 0:
      return 0
    # KEYED ON THE DATA VERSION as both sibling caches are: without
    # it an edit in QGIS left this answering from before the edit, so
    # the Classes cell reported 4 where the column now held 5.
    key = (layer.id(), field_name, self._data_version)
    if key not in self._cat_count_cache:
      try:
        self._cat_count_cache[key] = len(
          {v for v in layer.uniqueValues(idx) if v is not None})
      except Exception:
        self._cat_count_cache[key] = 0
    return self._cat_count_cache[key]

  def _classification_values(self, field_name: str):
    """One column of the region, prepared for cutting breaks from.

    Args:
      field_name: the column a graduated element classifies.

    Returns:
      A geometry-less layer holding one entry per area, gaps
      included, or None when there is no layer or no such field --
      which tells make_graduated_renderer to classify the element
      layer as it always did.

    A LAYER rather than a list, and built once: every element wearing
    this column is seeded from the same copy, where handing over the
    values would have each element build its own -- twenty-six copies
    of a fifty-thousand-row column for one map.

    One entry per AREA rather than the distinct values, because
    quantiles are decided by how many areas fall where; a set of
    distinct values would weight a value held by one area the same as
    one held by half the map.

    Cached against the layer's own FINGERPRINT rather than merely its
    id. The count and extent move whenever features are added or
    removed, so an edit that changes what should be classified
    retires the entry; what it cannot see is a value rewritten
    straight through the data provider, which is the documented limit
    described at _on_layer_changed and applies to every other reading
    the dialog takes of this layer.
    """
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return None
    index = layer.fields().indexOf(field_name)
    if index < 0:
      return None
    # `_layer_fingerprint` takes no argument -- it reads the chosen
    # layer itself, which is the one being scanned two lines below.
    # Calling it with one raised TypeError into the guard beneath,
    # and the whole classification quietly fell back to per-element
    # breaks: a change that appeared to do nothing, which is exactly
    # what a silent fallback looks like from outside.
    # `_data_version` AS WELL AS the fingerprint, because the
    # fingerprint measures what a layer IS -- count, extent, field
    # names, CRS -- and a value retyped in QGIS's editing session
    # moves none of them. Both SIGNATURES already carried it, so a
    # retyped value correctly stopped a run being a no-op; this cache
    # did not, so the run went ahead and classified from a snapshot of
    # the values as they were. Measured 2026-08-15: a column edited
    # from 0-121 down to 0-3 through startEditing/commitChanges went
    # on drawing classes 84.7 to 121, with four of five wearing
    # nothing and every tile in the first. The bump is the dialog's
    # own counter, so this costs a tuple comparison.
    key = (layer.id(), field_name, self._layer_fingerprint(),
           self._data_version)
    if key not in self._values_cache:
      # one scan, and only when the fingerprint says the last one is
      # out of date. The same scan the missing-values notice makes.
      try:
        values = [feature[field_name] for feature in layer.getFeatures()]
      except Exception:
        return None
      # ONE ENTRY PER FIELD, NOT ONE ENTRY. This dict was REPLACED
      # wholesale, on the sound reasoning that a stale fingerprint's
      # values must never sit here being wrong -- and replacing it
      # threw away every OTHER column's entry at the same time. With
      # one element that is free, since there is only ever one column
      # to hold. With twenty-three elements on twenty-three columns
      # the hit rate is ZERO: `_assignments` asks `_value_digest` for
      # every element, every digest routes through here, and each one
      # evicted the last, so a single keystroke rescanned the whole
      # layer once per element and built a fresh memory layer each
      # time.
      #
      # MEASURED 2026-08-19 on the reporter's own data, 3,011
      # polygons and 23 columns: 46 scans per interactive tick,
      # 1,041,176 calls and 3,543 ms of CPU, against 119,352 calls
      # and 172 ms at 0.24.2 -- and one Generate at 62.7 seconds
      # against 2.5. The regression arrived with this function, which
      # exists at neither tag. Keeping the other fields costs 70,228
      # calls and 72.6 ms, below 0.24.2.
      #
      # THE SAFETY PROPERTY IS KEPT EXACTLY, and it is the reason the
      # filter is written on the KEY rather than on a timestamp: an
      # entry survives only while its layer, its fingerprint and its
      # `_data_version` all still match the one being written, which
      # is the same condition the lookup above tests. Anything the
      # data has moved under is dropped in the same statement that
      # writes the new value, so there is no window in which a stale
      # entry is reachable.
      #
      # WHY IT COULD NOT SHOW HERE: the suite's fixture is four
      # elements over thirty-six features, against twenty-three over
      # three thousand -- a factor of 481 with no change of shape, so
      # the cost was real all along and never large enough to see.
      self._values_cache = {
        older: cached for older, cached in self._values_cache.items()
        if older[0] == key[0] and older[2:] == key[2:]}
      self._values_cache[key] = bridge.classification_source(
        field_name, values)
      # ...and a DIGEST of what was scanned, taken here because the
      # scan is already paid for. _signature reads it, so an element
      # is re-seeded when the column it classifies moves and not
      # merely when the layer emitted a signal: `_data_version` bumps
      # for a column ADDED as well, and re-seeding on that destroyed
      # hand styling that had every right to survive
      # (test_a_column_appearing_in_qgis_keeps_hand_styling).
      numbers = sorted(
        float(v) for v in values
        if isinstance(v, (int, float)) and math.isfinite(float(v)))
      # ...AND WHAT IS UNPLACEABLE, per kind. Every term above is
      # built from FINITE values, so swapping one kind of absence for
      # another -- a NULL edited to an infinity in QGIS -- moved
      # nothing: the digest was identical, `_signature` said
      # unchanged, the run kept the previous paired renderer, and the
      # tiles now wearing `pos-infinity` matched no category and were
      # drawn as NOTHING. The hole the paired layer exists to remove,
      # arriving through the gate meant to notice. Measured by a hunt,
      # 2026-08-16: digest identical either side of the edit, four
      # tiles unpainted after it.
      #
      # Counted per KIND rather than in total, because a NULL becoming
      # an infinity leaves the total unchanged and is exactly the edit
      # that must be noticed.
      absent = {}
      for v in values:
        if not bridge.cannot_be_placed(v):
          continue
        if isinstance(v, float) and v == float("inf"):
          kind = bridge.POS_INF_KEY
        elif isinstance(v, float) and v == float("-inf"):
          kind = bridge.NEG_INF_KEY
        else:
          kind = bridge.NO_DATA_KEY
        absent[kind] = absent.get(kind, 0) + 1
      # ...AND THE WORDS, not only the numbers. Every term above is
      # numeric, so a TEXT column digested identically whichever
      # values it held: recoding forest to alpine in QGIS's attribute
      # table moved nothing, `_signature` said unchanged, and the
      # landing reattached the stale categorized renderer -- the new
      # value painted catch-all grey under a legend still listing the
      # departed class, with nothing said. The numeric half of exactly
      # this was fixed on 2026-08-15 and its guard test drove a
      # numeric column, which is how the text half survived. Found by
      # the data-edit hunt, 2026-08-26. Counted as frequencies, since
      # categorical classes are cut from value counts.
      words = {}
      for v in values:
        if v is None or isinstance(v, (int, float)) \
            or bridge.cannot_be_placed(v):
          continue
        words[str(v)] = words.get(str(v), 0) + 1
      self._value_digests[(layer.id(), field_name)] = (
        len(values), len(numbers),
        numbers[0] if numbers else None,
        numbers[-1] if numbers else None,
        hash(tuple(numbers)),
        tuple(sorted(absent.items())),
        hash(tuple(sorted(words.items()))))
    return self._values_cache.get(key)

  def _value_digest(self, field_name):
    """A cheap summary of the column an element classifies.

    Args:
      field_name: the attribute the row is drawing.

    Returns:
      A hashable tuple — row count, finite count, smallest, largest
      and a hash of the sorted values — or None when there is no
      layer or the column has not been scanned. Suitable for a
      signature and for nothing else: it identifies a distribution
      rather than describing one.

    Taken from the scan `_classification_values` already makes, so
    this costs a dictionary lookup rather than a pass over the data.
    It answers the question `_layer_fingerprint` cannot: the
    fingerprint measures what a layer IS, and every value in a column
    can change while the count, the extent, the field names and the
    CRS all stand still.
    """
    layer = self.layer_combo.currentLayer()
    if layer is None or not field_name:
      return None
    # ALWAYS through the values cache, never short-circuited on the
    # digest already being there: that cache knows when a rescan is
    # due (its key carries the fingerprint and the edit counter) and
    # this dict does not. Skipping the call when a digest existed left
    # the first scan's summary in place forever, so the signature went
    # on describing the data as it was and the map kept the old
    # classification -- the very fault this digest was added to fix.
    # The call is a dictionary hit whenever nothing has changed.
    self._classification_values(field_name)
    return self._value_digests.get((layer.id(), field_name))

  def _populate_class_source_combo(self, combo, current=None):
    """(Re)build a row's class-source choices.

    Args:
      combo: the combo to refill; the current selection is preserved
        when that choice still exists.
      current: a token to select instead, e.g. "file:/path.qml".

    Returns:
      None. The choices are: automatic colours, any
    QML browsed in any row this session (the pool in _browsed_qmls, so
    one file chosen once is offered to every categorized row), any
    loaded layer with categorized symbology, and a browse entry. The
    SHARED sentinel survives only as a legacy stored value from the
    since-removed dialog-wide style file box, mapped to automatic."""
    from qgis.core import QgsCategorizedSymbolRenderer
    if current is None:
      current = combo.currentData()
    if current == self.SHARED:  # legacy stored choice
      current = ""
    wanted = [("Automatic colours", "")]
    for path in self._browsed_qmls:
      wanted.append((os.path.basename(path), "file:" + path))
    for lyr in QgsProject.instance().mapLayers().values():
      try:
        if isinstance(lyr.renderer(), QgsCategorizedSymbolRenderer):
          wanted.append((f"Layer: {lyr.name()}", f"layer:{lyr.id()}"))
      except Exception:
        continue
    if current and current.startswith("file:") \
        and current not in [w[1] for w in wanted]:
      wanted.append((os.path.basename(current[5:]), current))
    wanted.append(("Choose file…", self.BROWSE))
    existing = [(combo.itemText(i), combo.itemData(i))
                for i in range(combo.count())]
    if existing != wanted:
      combo.blockSignals(True)
      combo.clear()
      for text, data in wanted:
        combo.addItem(text, data)
      combo.blockSignals(False)
    idx = combo.findData(current)
    if idx < 0:
      idx = 0
    if combo.currentIndex() != idx:
      combo.blockSignals(True)
      combo.setCurrentIndex(idx)
      combo.blockSignals(False)
    combo.setProperty("last_idx", combo.currentIndex())

  def _make_class_source_combo(self, prev_choice, tile_id=None):
    """One row's class-source dropdown.

    Args:
      prev_choice: the token to preselect, remembered per element in
        _class_choices.
      tile_id: the element this row carries; it rides on the widget
        via setProperty so the shared handlers know which element
        they are answering for.

    Returns:
      A combo, created only while that row is
    categorized (see _sync_row). ``setProperty`` stores arbitrary data
    on a Qt object; the tile_id rides along so the shared handlers know
    which element to record choices for. The ``activated`` handler
    intercepts the BROWSE entry to open a native file dialog, adds the
    chosen QML to the session-wide pool, and re-selects it; a cancelled
    dialog restores the previous selection."""
    combo = QComboBox()
    combo.setProperty("tile_id", tile_id)
    combo.setToolTip(
      "Where this element's class colours come from.")
    self._populate_class_source_combo(
      combo, prev_choice if prev_choice is not None else "")

    def activated(index):
      from qgis.PyQt.QtWidgets import QFileDialog
      if combo.itemData(index) == self.BROWSE:
        path, _filter = QFileDialog.getOpenFileName(
          self, "Class colours from a QGIS style file", "",
          "QGIS layer style (*.qml)")
        if path:
          if path not in self._browsed_qmls:
            self._browsed_qmls.append(path)
          self._populate_class_source_combo(combo, "file:" + path)
        else:
          combo.blockSignals(True)
          combo.setCurrentIndex(combo.property("last_idx") or 0)
          combo.blockSignals(False)
      combo.setProperty("last_idx", combo.currentIndex())
      tid = combo.property("tile_id")
      if tid:
        was = self._class_choices.get(tid)
        self._class_choices[tid] = combo.currentData()
        # importing a scheme is the same kind of act as choosing a
        # ramp: it names where this element's colours come from
        if combo.currentData() and combo.currentData() != was:
          self._clear_category_colours(tid, "an imported class source")
      self._queue_live()

    combo.activated.connect(activated)
    return combo

  def _make_reverse_box(self, tile_id, checked):
    """One row's Reverse checkbox, centred in its cell.

    Args:
      tile_id: the element the row belongs to, carried on the widget
        so the handler can record the choice against the element
        rather than the row (rows are rebuilt; elements persist).
      checked: its initial state, restored from _reverse_choices.

    Returns:
      A QWidget wrapper holding the switch. Qt centres a small widget
      in a table cell only if you put it in a layout, hence the
      wrapper; ``_row_reverse`` unwraps it again. The control is a
      sliding switch rather than a checkbox because that is what the
      same idea looks like in the browser tool these maps also come
      from, and because a row of switches reads as a set of states
      rather than a list of ticks.

    Toggling repaints the row's ramp swatch the other way round and
    goes through the light preview path, so it behaves like every
    other Data-tab control: no table rebuild, no chooser race.
    """
    holder = QWidget()
    layout = QHBoxLayout(holder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    box = ToggleSwitch()
    box.setProperty("tile_id", tile_id)
    box.setChecked(bool(checked))
    box.setToolTip("Run this element's ramp the other way round")
    layout.addWidget(box)

    def toggled(state, b=box):
      tid = b.property("tile_id")
      if tid:
        self._reverse_choices[tid] = b.isChecked()
        # a graduated row's customization travels with the flip: the
        # display window mirrors and the positional picks swap ends,
        # so reversing twice restores everything (settled 2026-08-09)
        self._mirror_quant_customization(tid)
      # the swatch should show what the map will do
      self._refresh_ramp_icons()
      self._refresh_preview_colours()

    box.toggled.connect(toggled)
    return holder

  def _make_opacity_spin(self, tile_id, value):
    """One row's opacity cell.

    Args:
      tile_id: the element it belongs to, carried on the widget so the
        handler records against the element rather than the row.
      value: 0-100, restored from _opacity_choices.

    Returns:
      A QSpinBox reading 0-100 with a "%" suffix, matching QGIS's own
      opacity control (100 is solid). A spin box rather than a slider:
      it is compact enough for a table that already carries seven
      columns, the numbers stay comparable down the column at a
      glance, and it steps rather than streaming, so each change costs
      one repaint. Dragging remains available in QGIS's own Layer
      Properties, which regeneration deliberately does not overwrite.
    """
    spin = QSpinBox()
    spin.setRange(0, 100)
    spin.setSingleStep(5)
    spin.setSuffix("%")
    spin.setProperty("tile_id", tile_id)
    spin.setValue(int(value))
    spin.setToolTip(
      "How solid this element draws, as QGIS layer opacity; "
      "100 is opaque.")

    def changed(_v, sp=spin):
      tid = sp.property("tile_id")
      if tid:
        self._opacity_choices[tid] = sp.value()
      self._refresh_preview_colours()

    spin.valueChanged.connect(changed)
    return spin

  def _row_scheme(self, row):
    """The break method a row's style combo names, or "".

    Args:
      row: the table row.

    Returns:
      The scheme as `GRAD_SCHEMES` names it -- "Quantiles", "Equal
      intervals", "Unclassed" and so on -- or "" when the row is not
      graduated or the combo has gone mid-rebuild.
    """
    combo = self.table.cellWidget(row, 2)
    if combo is None:
      return ""
    return self.GRAD_SCHEMES.get(combo.currentText(), "")

  def _row_opacity(self, row):
    """The opacity spin box for a row, or None mid-rebuild."""
    return self.table.cellWidget(row, 6)

  def _row_reverse(self, row):
    """The ToggleSwitch inside a row's Reverse cell, or None when that
    row has no ramp to reverse.

    Not a QCheckBox: ToggleSwitch is a QAbstractButton subclass drawn
    by hand, and its own docstring says why a styled QCheckBox was
    rejected. Named wrongly here and in _reverse_state's comment until
    2026-08-12."""
    holder = self.table.cellWidget(row, 5)
    if holder is None:
      return None
    return holder.findChild(ToggleSwitch)

  def _refresh_ramp_icons(self):
    """Redraw each row's ramp swatch in its current direction.

    Only the icons change: the combo keeps its items, its index, and
    its identity, so a repaint here can never disturb a dropdown the
    user has open (the chooser-race rule).
    """
    for row in range(self.table.rowCount()):
      combo = self.table.cellWidget(row, 4)
      if combo is None or not hasattr(combo, "count"):
        continue
      box = self._row_reverse(row)
      reverse = bool(box is not None and box.isEnabled() and box.isChecked())
      for i in range(combo.count()):
        icon = _ramp_icon(combo.itemText(i), reverse)
        if icon is not None:
          combo.setItemIcon(i, icon)

  def _make_ramp_combo(self, tile_id, wanted):
    """One row's colour-ramp dropdown.

    Args:
      tile_id: the element the row belongs to; the pick is recorded
        against it in _ramp_choices, so it survives table rebuilds
        and the Single-colour swap.
      wanted: the ramp to preselect, if it still exists.

    Returns:
      A RampCombo listing every ramp in the QGIS style library, each
      with a preview swatch drawn in its current direction. On
      categorized and graduated rows alike it can additionally
      DISPLAY "Custom" (see RampCombo); _sync_row decides when.
    """
    ramp_combo = RampCombo()
    # without this the swatch drawn above is scaled down to the
    # platform's default icon size, and the ramp cannot be read
    ramp_combo.setIconSize(RAMP_SWATCH)
    ramp_combo.setProperty("tile_id", tile_id)
    # THE ELEMENT'S OWN RECORD, not the row's Reverse widget, because
    # this runs while the table is being BUILT and that widget may not
    # exist yet. `_reverse_choices` is what survives a rebuild, which
    # is the same reason the ramp itself is looked up by tile id.
    # THE RECORD, GATED BY THE MODE THAT CAN WEAR IT -- exactly the
    # gate `_refresh_ramp_icons`, `_sync_row` and `_assignments` all
    # apply, and this constructor did not: a Reverse kept silently
    # from a graduated excursion drew the swatch and all 64 dropdown
    # icons mirror-imaged on a CATEGORIZED row whose map, preview and
    # (disabled) toggle all said forward. Found by the pixels hunt,
    # 2026-08-26. The kept record is untouched; only what is DRAWN
    # follows what the row is wearing.
    switch_now = self._row_reverse(self._row_for_element(tile_id)) \
        if self._row_for_element(tile_id) is not None else None
    wearable = switch_now is None or switch_now.isEnabled()
    reversed_here = bool(self._reverse_choices.get(tile_id, False)) \
        and wearable
    for name in self._ramp_names:
      # IN THIS ELEMENT'S OWN DIRECTION, not always forward. The
      # swatch is how a user reads an element and chooses its next
      # ramp, and drawing it forward over a reversed map showed them
      # the mirror image of what they had.
      #
      # `_refresh_ramp_icons` draws them correctly and has exactly ONE
      # caller: the Reverse toggle. So the flip was right until the
      # next rebuild -- and a Generate rebuilds, because adding output
      # layers makes the layer combo re-emit; so do a spacing change, a
      # family change and reopening the project. A REFRESH WITH ONE
      # CALLER IS A REFRESH THAT ONLY WORKS ONCE: grep the CONSTRUCTOR
      # as well as the updater, and ask what rebuilds the widget.
      # Present since v0.23.0, found 2026-08-17.
      icon = _ramp_icon(name, reversed_here)
      if icon is not None:
        ramp_combo.addItem(icon, name)
      else:
        ramp_combo.addItem(name)
    if ramp_combo.findText(wanted) < 0:
      wanted = self._ramp_names[0] if self._ramp_names else ""
    ramp_combo.setCurrentText(wanted)

    def changed(_i, c=ramp_combo):
      tid = c.property("tile_id")
      if tid:
        self._ramp_choices[tid] = c.currentText()
        # a new ramp is a new source of truth for this element's
        # colours, so anything picked by hand goes with it -- and on
        # a graduated row the display range resets too ("until
        # reselected anew", settled 2026-08-09)
        self._clear_category_colours(tid, "a new colour ramp")
        self._clear_quant_customization(tid, "a new colour ramp")
      self._refresh_preview_colours()

    ramp_combo.currentIndexChanged.connect(changed)

    def picked(_index, c=ramp_combo):
      # ``changed`` above runs only when the INDEX changes. While the
      # cell reads Custom the index still sits on the ramp colouring
      # the leftover values, so re-choosing that same ramp fires only
      # this signal -- and it is still the deliberate act of choosing
      # a ramp, which destroys the hand-picks (the settled rule; the
      # notice comes from _clear_category_colours as ever). On an
      # ordinary index change both signals fire, but ``changed`` has
      # already cleared the picks and refreshed the display by the
      # time this runs, so the guard makes it a no-op.
      if not c.showing_custom():
        return
      tid = c.property("tile_id")
      if tid:
        self._clear_category_colours(tid, "a new colour ramp")
        self._clear_quant_customization(tid, "a new colour ramp")
      self._refresh_preview_colours()

    ramp_combo.activated.connect(picked)
    return ramp_combo

  def _make_colour_button(self, tile_id, colour_hex):
    """The swatch-plus-picker button for Single colour rows.

    Args:
      tile_id: the element it belongs to, so the picked colour is
        remembered per element in _single_colours.
      colour_hex: the colour to start on.

    Returns:
      A QgsColorButton -- QGIS's native colour widget, so the picker
      here is the one users meet elsewhere in QGIS -- which replaces
      the ramp dropdown while the row is on Single colour.
    """
    button = QgsColorButton()
    button.setColor(QColor(colour_hex))
    button.setToolTip("Fill colour for this element")

    def changed(colour, tid=tile_id):
      self._single_colours[tid] = colour.name()
      self._refresh_preview_colours()

    button.colorChanged.connect(changed)
    return button

  def _row_widgets(self, row):
    """The seven per-row cell widgets, in column order: variable,
    style, classes, ramp-or-colour, reverse, opacity, class source.
    Any may be None mid-rebuild or by design (the class-source cell
    exists only on categorized rows, and the ramp cell may hold a
    QgsColorButton instead of a combo)."""
    return (self.table.cellWidget(row, 1), self.table.cellWidget(row, 2),
            self.table.cellWidget(row, 3), self.table.cellWidget(row, 4),
            self.table.cellWidget(row, 5),
            self.table.cellWidget(row, 6),
            self.table.cellWidget(row, 7))

  def _row_mode(self, row) -> str:
    """A row's style resolved to its renderer kind: every "Quant: X"
    entry collapses to "Graduated"; the break method itself is read
    separately in _assignments."""
    var_combo, mode_combo, *_rest = self._row_widgets(row)
    if mode_combo is None:
      return "Single colour"
    raw = mode_combo.currentText()
    return "Graduated" if raw in self.GRAD_SCHEMES else raw

  def _sync_row(self, row):
    """Keep a row's widgets coherent with its style: the Classes cell is
    editable only for Quant styles (categorized rows grey it out and
    show the detected category count), the ramp swaps between
    quantitative and categorical families, and the class-source cell
    exists only on categorized rows."""
    var_combo, mode_combo, k_spin, ramp_combo, reverse_holder, \
      opacity_spin, file_combo = self._row_widgets(row)
    if None in (var_combo, mode_combo, k_spin):
      return
    mode = self._row_mode(row)
    var = var_combo.currentText()
    var = None if var == "---" else var

    k_spin.blockSignals(True)
    if mode == "Graduated" and \
        mode_combo.currentText() == "Quant: Unclassed":
      # fixed class count: 50 linear steps stand in for a continuous
      # ramp, so the cell is informative rather than editable
      k_spin.setSpecialValueText("")
      k_spin.setRange(0, 9999)
      k_spin.setValue(50)
      k_spin.setEnabled(False)
    elif mode == "Graduated":
      # 2 to 20 classes. The web app offers no equivalent control at
      # all (it renders continuously, which is what Quant: Unclassed
      # reproduces here), so the ceiling is ours: 20 matches the app's
      # element-count slider and the largest categorical palettes,
      # which is about as many steps as a ramp can carry before the
      # classes stop reading as classes
      k_spin.setSpecialValueText("")
      k_spin.setRange(2, 20)
      # clamp the PROPERTY, not only the display: `_assignments`
      # reads the property, so clamping one and not the other is how
      # a cell and a map come to disagree about the same number
      k_spin.setProperty(
        "user_k", min(int(k_spin.property("user_k") or 5), 20))
      # A RESTORED COUNT IS RAISED TO CARRY THE ROW'S PINS, and told.
      # (Maintainer's ruling, 2026-08-17, on a regression made earlier
      # the same day.) The Classes spinner refuses a count too small
      # for the pins in force -- but THIS site writes the spinner with
      # signals BLOCKED, so `on_k` never runs, and every excursion that
      # remembers a count comes back through here. Set Classes to 2,
      # go to Unclassed where k is 50, pin both ends legally, come
      # back to Quantiles: the remembered 2 returns and cannot hold two
      # pins. The retirement guard then kept them anyway, so the row,
      # the colour editor and the saved project all claimed bounds of
      # 10 and 60 over a map drawing 0/21/121, with nothing said.
      #
      # Raising is the one sensible response and the dialog makes it
      # rather than choosing between a user's two statements: the pins
      # are a smaller and more durable statement than a class count
      # they set before pinning, and this project already re-defaults
      # a lost column and re-derives a spacing on the same rule --
      # where an edit makes a setting untrue and there is exactly one
      # sensible answer, make it and say so.
      row_item_k = self.table.item(row, 0)
      carried = self._pins_in_force(
        row_item_k.text() if row_item_k is not None else "", var)
      if carried and int(k_spin.property("user_k")) - 1 < carried:
        k_spin.setProperty("user_k", min(carried + 1, 20))
        self._report_quietly(bridge.pin_count_raised_message(
          int(k_spin.property("user_k")), carried))
      k_spin.setValue(int(k_spin.property("user_k")))
      k_spin.setEnabled(True)
    elif mode == "Categorized" and var:
      # the row's own element, read from the table rather than from a
      # variable this scope does not have: _sync_row is given a row
      # index and nothing else
      row_item = self.table.item(row, 0)
      n = self._category_count(
        var, row_item.text() if row_item is not None else "")
      k_spin.setSpecialValueText("")
      k_spin.setRange(0, 9999)
      k_spin.setValue(n)
      k_spin.setEnabled(False)
    else:
      k_spin.setRange(0, 9999)
      k_spin.setSpecialValueText("–")
      k_spin.setValue(0)
      k_spin.setEnabled(False)
    k_spin.blockSignals(False)

    id_item0 = self.table.item(row, 0)
    row_tid = id_item0.text() if id_item0 else None
    if mode == "Single colour":
      if not isinstance(ramp_combo, QgsColorButton) and row_tid:
        if ramp_combo is not None:
          self._ramp_choices[row_tid] = ramp_combo.currentText()
        start = self._single_colours.get(
          row_tid,
          bridge.ramp_swatch_colour(
            ramp_combo.currentText() if ramp_combo is not None
            else self._ramp_choices.get(row_tid, "Reds")))
        self._single_colours[row_tid] = start
        self.table.setCellWidget(
          row, 4, self._make_colour_button(row_tid, start))
      ramp_combo = None
    elif isinstance(ramp_combo, QgsColorButton) and row_tid:
      wanted = self._ramp_choices.get(
        row_tid, self.DEFAULT_RAMPS[row % len(self.DEFAULT_RAMPS)])
      ramp_combo = self._make_ramp_combo(row_tid, wanted)
      self.table.setCellWidget(row, 4, ramp_combo)
    # the Reverse cell: present on every row so the column reads
    # evenly, but enabled only where reversing means something. On a
    # Single colour row it greys out AND clears, because a reversed
    # single colour means nothing and a stale tick would mislead. A
    # Categorized row is disabled the same way even though it carries
    # a ramp: category colours are assignments to named values, not a
    # scale with a direction, so "the other way round" only shuffles
    # which value gets which colour. The control re-enables the moment
    # a quantitative style is chosen (user decision, 2026-08-09). The
    # recorded choice survives underneath, exactly as for Single
    # colour, so switching a row away and back costs no tick.
    tid_for_row = self.table.item(row, 0)
    row_id = tid_for_row.text() if tid_for_row else None
    has_ramp = ramp_combo is not None and not isinstance(
      ramp_combo, QgsColorButton)
    can_reverse = has_ramp and mode != "Categorized"
    box = self._row_reverse(row)
    if box is None and row_id:
      self.table.setCellWidget(row, 5, self._make_reverse_box(
        row_id, self._reverse_choices.get(row_id, False)))
      box = self._row_reverse(row)
    if box is not None:
      box.blockSignals(True)
      box.setEnabled(can_reverse)
      box.setChecked(bool(can_reverse and row_id
                          and self._reverse_choices.get(row_id, False)))
      box.blockSignals(False)

    # opacity applies to every element, ramp or no ramp (a single
    # colour and even an unassigned no-data fill can be softened), so
    # unlike Reverse this cell is always present and always enabled
    if row_id and self._row_opacity(row) is None:
      self.table.setCellWidget(row, 6, self._make_opacity_spin(
        row_id, self._opacity_choices.get(row_id, 100)))
    elif row_id and row_id in self._opacity_choices:
      # ...AND IT FOLLOWS THE RECORD WHEN THE RECORD MOVES UNDER IT.
      # The cell was CREATED and never updated, which is invisible
      # while the only writer is the spin's own handler -- those two
      # agree by construction. ADOPTION is the other writer: opening a
      # saved project recovers each element's opacity off its layer,
      # and a cell standing from the outgoing project went on showing
      # 100 over a layer drawn at 40, with one Generate then painting
      # the 100 into the .qgz.
      #
      # Signals blocked, or setting the cell right would fire the
      # handler that writes the spin's value back into the record and
      # undo the adoption this exists to show.
      spin = self._row_opacity(row)
      wanted = int(self._opacity_choices[row_id])
      if spin.value() != wanted:
        _dump("CELL", row_id, spin.value(), ">", wanted)
        spin.blockSignals(True)
        spin.setValue(wanted)
        spin.blockSignals(False)
    if ramp_combo is not None:
      ramp = ramp_combo.currentText()
      is_cat_ramp = ramp in bridge.CATEGORICAL_RAMPS
      # A RAMP IS REMEMBERED UNDER THE MODE THE ROW IS IN, never under
      # the family the RAMP belongs to. (Maintainer's ruling,
      # 2026-08-27, on ledger row 13 of that date.) A row remembers
      # what it WORE in each mode: pick `Accent` while Graduated, pick
      # `Reds` back, and the categorical slot is untouched. Filing by
      # the ramp's own family instead put `Accent` into the categorical
      # slot permanently -- every visible cell came back, and the next
      # change of variable drew a ramp nobody had chosen this session.
      #
      # THE COMMENT THIS REPLACES ARGUED FOR THE OLD RULE, and its
      # worry is answered rather than overruled. It said that a
      # categorized row carrying `YlOrRd` is remembering a quantitative
      # choice and that filing it under "Categorized" would hand it
      # straight back on the next flip. It would -- and that is now the
      # wanted answer, because the row wore it there and nobody took it
      # off; a ramp left standing on a categorized row is one somebody
      # was content to see on it.
      #
      # ONLY A ROW THAT HAS NOT MOVED MAY RECORD, which is the whole of
      # the ordering here and the reason `moved` is computed first. On
      # the sync that FOLLOWS a mode change the cell still holds the
      # outgoing mode's ramp, so recording it under the incoming mode
      # would file the wrong ramp and then hand it straight to the swap
      # below, which reads the very slot that write had just filled --
      # a flip that undoes itself. A row that has not moved is one
      # whose ramp somebody chose for the mode it is in, which is
      # exactly the thing worth remembering, and it is recorded on
      # every such sync so the ramp to come back to is whatever they
      # last had rather than whatever was last displaced.
      moved = row_tid is None or self._synced_modes.get(row_tid) != mode
      memory = self._ramp_memory.setdefault(row_tid, {}) \
        if row_tid else {}
      if not moved and mode in ("Categorized", "Graduated"):
        memory[mode] = ramp
      # The swap is gated on `moved` for the other half of that reason:
      # on a row that has not moved the ramp arrived by somebody
      # picking it, and substituting it here would undo the pick they
      # just made -- while _clear_category_colours had already
      # destroyed their hand-picked colours on the way in, for a change
      # that then did not happen.
      target = None
      if moved and mode == "Categorized" and not is_cat_ramp:
        target = (memory.get("Categorized")
                  or self.CAT_DEFAULT_RAMPS[
                    row % len(self.CAT_DEFAULT_RAMPS)])
      elif moved and mode == "Graduated" and is_cat_ramp:
        target = (memory.get("Graduated")
                  or self.DEFAULT_RAMPS[row % len(self.DEFAULT_RAMPS)])
      if target is not None and ramp_combo.findText(target) >= 0:
        ramp_combo.blockSignals(True)
        ramp_combo.setCurrentText(target)
        ramp_combo.blockSignals(False)
        if row_tid:
          self._ramp_choices[row_tid] = target
          memory[mode] = target        # the slot the mode just filled

    show_file = mode == "Categorized" and bool(var) \
      and not self.table.isColumnHidden(7)
    id_item = self.table.item(row, 0)
    tid = id_item.text() if id_item else None
    if show_file:
      if file_combo is None:
        default = self._class_choices.get(tid, "")
        file_combo = self._make_class_source_combo(default, tid)
        self.table.setCellWidget(row, 7, file_combo)
      else:
        file_combo.setProperty("tile_id", tid)
        # IT FOLLOWS THE RECORD WHEN THE RECORD MOVES UNDER IT, which
        # is the fix the ramp cell beside it was given on 2026-08-18
        # and this one was not. Rebuilt without the record, the combo
        # merely PRESERVES whatever it was showing -- and `_assignments`
        # reads the widget, so `_refresh_table` then wrote that stale
        # answer back over the record. Selecting a group therefore
        # threw away an imported QML: the element reverted to automatic
        # colours, the next Generate drew the wrong ones and stamped an
        # empty class source onto the group, so the choice was gone
        # from the project and from the GeoPackage. Found by a hunt on
        # 2026-08-26, reading the layer's own renderer rather than the
        # dialog's dicts.
        # THE RECORD IS THE AUTHORITY HERE because the combo's own
        # `activated` handler writes to it the moment a person picks,
        # so it can never be behind a user's choice -- only ahead of a
        # widget that a group switch has just left stale.
        self._populate_class_source_combo(
          file_combo, self._class_choices.get(tid, ""))
    elif file_combo is not None:
      if tid:
        self._class_choices[tid] = file_combo.currentData()
      self.table.removeCellWidget(row, 7)

    # The "Edit colours" button. Unlike the class source it is not
    # removed on non-categorical rows: a hole in the column would read
    # as a control that failed to appear, where a greyed button says
    # plainly that this element has no categories to colour.
    if not self.table.isColumnHidden(COL_EDIT_COLOURS):
      button = self.table.cellWidget(row, COL_EDIT_COLOURS)
      if button is None:
        # "Customize" rather than an ellipsis: the column heading says
        # what the button is for, but the button itself has to say
        # what it DOES, since a disabled ellipsis reads as a control
        # that is broken rather than one that does not apply here. And
        # a verb rather than "Custom": that word is the ramp cell's
        # display for colours already customized, and one word naming
        # a STATE in one column and an ACTION in the next would read
        # as the same thing twice. The -ize spelling is the project's
        # Canadian-spelling rule, no exception needed.
        button = QPushButton("Customize")
        button.clicked.connect(self._edit_category_colours)
        self.table.setCellWidget(row, COL_EDIT_COLOURS, button)
      button.setProperty("tile_id", tid)
      usable = mode in ("Categorized", "Graduated") and bool(var)
      button.setEnabled(usable)
      if mode == "Graduated" and var:
        # graduated rows edit class colours and the display range;
        # Unclassed rows open the same window with the range alone
        # live, so the button stays enabled there too
        # ...and the two say different things, because on an Unclassed
        # row every colour button in that window is disabled: the
        # class list is a preview and only the range and the two ends
        # are live. One tooltip for both told half the users to choose
        # colours they cannot reach (found 2026-08-18 by a prose hunt).
        scheme_now = self._row_scheme(row)
        tip = ("Narrow the ramp's display range, and pin its ends"
               if scheme_now == "Unclassed" else
               "Choose class colours, or narrow the ramp's display range")
      elif usable:
        tip = "Choose a colour for each value this element takes"
      else:
        tip = "Only elements drawn in classes have colours to edit"
      button.setToolTip(tip)
    elif self.table.cellWidget(row, COL_EDIT_COLOURS) is not None:
      self.table.removeCellWidget(row, COL_EDIT_COLOURS)

    # The ramp cell of a categorized row reads "Custom" while the ramp
    # alone no longer decides the element's colours: any hand-picked
    # colour recorded for the CURRENT field, or an imported class
    # source. "Any pick" deliberately, not "a pick that differs from
    # the ramp" -- under the latter the cell would read a ramp name
    # while an override was still recorded and outranking it in
    # make_categorized_renderer, which is a control lying about the
    # map. Two consequences fall out rather than being separate rules:
    # switching the variable to a field with no picks leaves Custom by
    # itself (and switching back re-enters it), and a reopened project
    # that adopted saved colours shows Custom. (Settled 2026-08-09.)
    ramp_cell = self.table.cellWidget(row, 4)
    if isinstance(ramp_cell, RampCombo):
      show_custom = False
      if mode == "Categorized" and var and row_tid:
        picks = self._category_colours.get(row_tid, {}).get(var)
        # read the live combo where the row has one; _class_choices
        # only catches up when the widget is removed or used
        file_widget = self.table.cellWidget(row, 7)
        choice = (file_widget.currentData() if file_widget is not None
                  else self._class_choices.get(row_tid, ""))
        has_source = bool(choice) and choice not in (self.BROWSE,
                                                     self.SHARED)
        show_custom = bool(picks) or has_source
      elif mode == "Graduated" and var and row_tid:
        # a graduated row is Custom while positional picks exist or
        # the Ramp Display Range is narrower than the whole ramp
        quant_picks = self._quant_colours.get(row_tid, {}).get(var)
        window = tuple(self._ramp_ranges.get(row_tid, (0, 100)))
        show_custom = bool(quant_picks) or window != (0, 100)
      # A PINNED row is not Custom: its colours are its ramp's, and
      # only its breaks are hand-set. So it keeps naming the ramp and
      # takes a boxed swatch instead, which is what says "this end is
      # yours" without the cell claiming the ramp is no longer the
      # ramp (maintainer's decision, 2026-08-14). Custom outranks it
      # when both apply, because hand-picked colours really do leave
      # the ramp behind.
      pinned = (self._pinned_bounds.get(row_tid, {}).get(var)
                if mode == "Graduated" and var and row_tid else None)
      # THE SCHEME CELL ANSWERS A DIFFERENT QUESTION FROM THE RAMP
      # CELL, and the two are decided together here so they cannot
      # drift. The ramp cell asks whether the COLOURS are still the
      # ramp's; this asks whether the BOUNDARIES are still the
      # scheme's. A stored `breaks` ladder means they are not --
      # somebody retyped them in QGIS's panel, or copied a whole
      # classification across -- so the cell stops naming a scheme
      # the map is no longer cut by. Pins alone leave it naming the
      # scheme, since the scheme still cuts everything between them.
      mode_cell = self.table.cellWidget(row, 2)
      if mode_cell is not None and hasattr(mode_cell, "set_custom_display"):
        mode_cell.set_custom_display(bool((pinned or {}).get("breaks")))
      if show_custom:
        ramp_cell.set_custom_display(
          self._custom_swatch_for(row_tid, var))
        ramp_cell.set_pinned_display(None)
        ramp_cell.setToolTip(CUSTOM_RAMP_TOOLTIP)
      else:
        ramp_cell.set_custom_display(None)
        ramp_cell.set_pinned_display(
          self._custom_swatch_for(row_tid, var) if pinned else None)
        # only undo our own tooltip; never blank one set elsewhere
        if ramp_cell.toolTip() == CUSTOM_RAMP_TOOLTIP:
          ramp_cell.setToolTip("")

    # Last: the row is now in step with its style, so record the mode
    # it was synced in. The next sync compares against this to tell a
    # deliberate ramp pick (mode unchanged) from the automatic swap a
    # style change earns (mode moved). It is written at the END so that
    # an early return above -- a half-built row mid-rebuild -- leaves
    # the previous answer standing rather than claiming a sync that did
    # not finish.
    if row_tid:
      self._synced_modes[row_tid] = mode

  def _update_dynamic_columns(self):
    """The Classes and Categ-colourmap-src columns exist only while
    they mean something, and every row's widgets are kept coherent."""
    rows = range(self.table.rowCount())
    modes = {}
    for row in rows:
      var_combo = self.table.cellWidget(row, 1)
      var = var_combo.currentText() if var_combo else "---"
      modes[row] = (self._row_mode(row), var not in ("", "---"))
    # the Classes column earns its place whenever ANY row has a class
    # count worth seeing — editable for graduated rows, greyed for
    # categorized ones, where it reports how many categories were
    # detected. Hiding it on an all-categorical map (as it once did)
    # took that count away exactly when it is most useful
    has_classes = any(m in ("Graduated", "Categorized") and has_var
                      for m, has_var in modes.values())
    self.table.setColumnHidden(3, not has_classes)
    # Reverse belongs beside the ramp, so it comes and goes with the
    # ramps: a map made entirely of single colours has nothing to
    # reverse and should not carry a column of dead checkboxes
    has_ramp_row = any(m in ("Graduated", "Categorized") and has_var
                       for m, has_var in modes.values())
    self.table.setColumnHidden(5, not has_ramp_row)
    has_categorical = any(m == "Categorized" and has_var
                          for m, has_var in modes.values())
    self.table.setColumnHidden(7, not has_categorical)
    # "Edit colours" appears whenever any element draws in CLASSES --
    # categorized or graduated alike, since the editor now serves both
    # (settled 2026-08-09). On rows with nothing to edit the button
    # stays but is disabled (see _sync_row): a gap in the column would
    # read as a missing control rather than an inapplicable one.
    has_editable = any(m in ("Categorized", "Graduated") and has_var
                       for m, has_var in modes.values())
    self.table.setColumnHidden(COL_EDIT_COLOURS, not has_editable)
    for row in rows:
      self._sync_row(row)
    # every place a column can appear or disappear funnels through
    # here, so this is where the layout rule is enforced
    self._fit_table_width()

  def _fit_table_width(self):
    """Give the table room for every visible column, within the cap.

    Returns:
      None. Sets the table's minimum width to the sum of its visible
      columns (plus frame and a vertical scrollbar's worth of slack,
      since a scrollbar that appears steals viewport width), and
      grows the WINDOW by any shortfall, capped at MAX_WINDOW_WIDTH.
      Qt then honours the minimum through every layout pass, which is
      what makes "the table never scrolls horizontally" a property of
      the dialog rather than an aspiration. The window is never
      shrunk here: columns disappearing hands the space to the
      preview, which is the layout rule's own priority order.
    """
    needed = sum(
      self.table.columnWidth(column)
      for column in range(self.table.columnCount())
      if not self.table.isColumnHidden(column))
    # Room for the table's own CHROME -- its frame and the vertical
    # scrollbar that appears as soon as the rows overflow. Measure it
    # rather than predict it: the difference between the widget and
    # its viewport IS the chrome Qt has actually drawn, whereas
    # PM_ScrollBarExtent reports the style's nominal 14px while the
    # bar drawn here is 18px. A table sized from the metric therefore
    # scrolled horizontally by those few pixels -- the exact fault
    # the layout rule forbids, reachable at sixteen elements on the
    # shipped catalogue, and invisible because the old layout test
    # only ever measured four rows. The metric stays as the fallback
    # for the first pass, before a viewport exists to measure.
    # (2026-08-10.)
    chrome = self.table.width() - self.table.viewport().width()
    fallback = 2 * self.table.frameWidth() + self.table.style().pixelMetric(
      QStyle.PixelMetric.PM_ScrollBarExtent)
    # Whichever is LARGER. The measured chrome is the truth once a
    # viewport exists, but this runs before layout too, and a first
    # pass that under-reserves leaves the table one or two pixels
    # short -- enough for a horizontal scrollbar, which is the whole
    # fault. Reserving a few pixels too many costs nothing: the
    # window is capped at MAX_WINDOW_WIDTH and the preview absorbs
    # the difference down to its floor.
    needed += max(chrome, fallback) + SCROLLBAR_SLACK
    self.table.setMinimumWidth(needed)
    shortfall = needed - self.table.width()
    if shortfall > 0 and self.width() < MAX_WINDOW_WIDTH:
      self.resize(min(MAX_WINDOW_WIDTH, self.width() + shortfall),
                  self.height())

  def _shelve_scheme(self, tile_id, prev):
    """Put an element's scheme on the shelf and take it out of force.

    Args:
      tile_id: the element whose column has gone.
      prev: its assignment dict (or a dict shaped like one) from
        before the change, naming the dropped field in ``var``, the
        style in ``mode_raw`` and whether somebody chose it in
        ``style_touched``.

    Returns:
      None. The shelf entry holds the WHOLE scheme -- mode, ramp,
      Reverse, class count, class source and the per-mode ramp slots
      -- which is exactly the set a COPY overwrites: the maintainer's
      partition of 2026-08-20, applied to switching on 2026-08-21 so
      the two acts agree about what a scheme is. What stays behind is
      the element's own: the opacity, and the single colour, which is
      an unworn-style record under the standing ruling. Hand-picked
      colours and pinned bounds are already keyed by element AND
      field, so they shelve themselves.
    """
    dropped = prev.get("var")
    if not dropped:
      return
    _dump("SHELF", tile_id, "put", dropped, prev.get("mode_raw"),
          "touched" if prev.get("style_touched") else "derived")
    # During a layer change the rebuild runs AFTER the banks swapped,
    # so a dropped scheme is filed under the OUTGOING dataset -- the
    # one its column belonged to. Filing it in the incoming bank would
    # put one dataset's column names inside another's memory, which is
    # the leakage the banks exist to prevent.
    self._scheme_just_reset.add(tile_id)
    shelf = (self._pending_outgoing_shelf
             if self._pending_outgoing_shelf is not None
             else self._scheme_memory)
    shelf.setdefault(tile_id, {})[dropped] = {
      "mode_raw": prev.get("mode_raw"),
      "touched": bool(prev.get("style_touched")),
      "ramp": self._ramp_choices.pop(tile_id, None),
      "reverse": self._reverse_choices.pop(tile_id, None),
      "k": self._class_counts.pop(tile_id, None),
      "class_source": self._class_choices.pop(tile_id, None),
      "ramp_slots": self._ramp_memory.pop(tile_id, None),
    }
    self._custom_swatch_cache.pop(tile_id, None)

  def _unshelve_scheme(self, tile_id, field):
    """Bring a shelved scheme back into force for a returning field.

    Args:
      tile_id: the element.
      field: the column it is returning to.

    Returns:
      The shelf entry, with its records written back into force, or
      None when nothing was shelved for that field. The entry is
      REMOVED from the shelf: it is in force again, and a copy left
      behind would go stale the moment the user edits anything.
    """
    entry = (self._scheme_memory.get(tile_id) or {}).pop(field, None)
    if entry is None:
      _dump("SHELF", tile_id, "miss", field)
      return None
    _dump("SHELF", tile_id, "take", field, entry.get("mode_raw"),
          "touched" if entry.get("touched") else "derived")
    for record, key in ((self._ramp_choices, "ramp"),
                        (self._reverse_choices, "reverse"),
                        (self._class_counts, "k"),
                        (self._class_choices, "class_source")):
      if entry.get(key) is not None:
        record[tile_id] = entry[key]
    if entry.get("ramp_slots"):
      self._ramp_memory[tile_id] = entry["ramp_slots"]
    self._custom_swatch_cache.pop(tile_id, None)
    return entry

  def _refresh_table(self):
    """Rebuild the assignment table for the current unit and layer.

    Rows are recreated from scratch (simplest correct behaviour when
    the element count changes), so all per-element choices that must
    survive live in dicts keyed by tile_id and are re-applied here:
    ``_assignments()`` is read *before* clearing to capture them.
    Defaults cycle the non-id-like numeric fields and the ramp list.
    Signal connections are made after initial values are set, so the
    setup itself does not fire handlers.
    """
    ids = self._tile_ids()
    fields = self._layer_fields()
    # fields that are almost certainly row identifiers rather than
    # data: mapping them produces a meaningless rainbow, so they are
    # skipped when picking each element's default variable (still
    # offered in the dropdown, since someone may genuinely want one)
    id_like = {"fid", "objectid", "id", "gid", "ogc_fid"}
    numeric = [f for f in fields if self._field_is_numeric(f)]
    # ...OR ANY FIELD AT ALL, exactly as the deleted-column twin has
    # read since 2026-08-20 (its line says `or numeric or fields`).
    # Without the last fallback a switch to an all-text dataset left
    # re-pointed rows on "---" while the twin would have landed them
    # on a surviving column -- and the switch notice then covered
    # them with a sentence about the elements that DID land
    # somewhere. Ruling 5 of 2026-08-21 counts text columns as
    # usable. Found by the switchdoor hunt of 2026-08-26.
    preferred = [f for f in numeric
                 if f.lower() not in id_like] or numeric or fields
    # A GROUP BEING RESTORED SPEAKS FOR THE TABLE, for this one
    # rebuild. Everywhere else the previous ASSIGNMENTS are the right
    # thing to carry forward; here they belong to the map being left,
    # and reading them would put the outgoing design's variables and
    # schemes onto the design being returned to. Consumed rather than
    # read, so a second rebuild in the same breath -- which
    # `_settle_layer_choice` can produce -- reads the rows this one
    # has just written.
    previous = self._restoring_assignments or self._assignments()
    self._restoring_assignments = None
    prev_by_id = {a["id"]: a for a in previous}
    # THE MODE AS THE WIDGET HOLDS IT, captured before the loop starts
    # replacing cells. `_assignments` CORRECTS a quantitative style
    # standing on a non-numeric column to Categorized -- right for the
    # map, and wrong as a record of what somebody chose, because a
    # column the NEW layer does not have answers `_field_is_numeric`
    # False as surely as a text column does. Shelving `prev["mode_raw"]`
    # therefore filed every dropped quant scheme as "Categorized", and
    # the wrong mode then greyed the row's Reverse on the way back.
    # Measured 2026-08-21 with three dump lines, after reading had
    # named the wrong suspect.
    raw_modes = {}
    for existing in range(self.table.rowCount()):
      cell = self.table.item(existing, 0)
      widget = self.table.cellWidget(existing, 2)
      if cell is not None and widget is not None \
          and hasattr(widget, "currentText"):
        raw_modes[cell.text()] = widget.currentText()
    self.table.setRowCount(len(ids))
    for row, tid in enumerate(ids):
      item = QTableWidgetItem(tid)
      item.setFlags(Qt.ItemFlag.ItemIsEnabled)
      self.table.setItem(row, 0, item)

      var_combo = QComboBox()
      var_combo.addItem("---")
      var_combo.addItems(fields)
      prev = prev_by_id.get(tid)
      # A DROPPED COLUMN TAKES ITS WHOLE SCHEME (the seven rulings of
      # 2026-08-21, in CLAUDE.md; the mode-only form of 2026-08-20 is
      # ledger row 9). Shelved rather than destroyed, keyed by the
      # field it was cut for. THE FIELDLESS BUILD IS EXCLUDED, for the
      # reason recorded at the end of this method.
      column_gone = bool(fields) and prev is not None \
          and prev.get("var") is not None and prev["var"] not in fields
      if column_gone:
        self._shelve_scheme(tid, dict(prev, mode_raw=raw_modes.get(
          tid, prev.get("mode_raw"))))
      # ...and an element PREFERS a field it has shown before: when
      # the shelf holds a scheme for a column this dataset HAS -- the
      # A-B-A journey -- the element returns to it, and the scheme
      # comes back with it below. COMPUTED WHETHER OR NOT THE CURRENT
      # COLUMN SURVIVED (maintainer's ruling, 2026-08-26): when
      # datasets share column names, keep-by-name used to keep the
      # re-pointed column on the return leg while the same journey
      # with a landed group restored the person's choice through the
      # group record -- two settled rules answering one act by
      # whether a run happened to land. The shelf entry IS the
      # person's earlier choice, it is popped on restore, and a row
      # whose current column was itself chosen deliberately has no
      # shelf entry for another field to beat it.
      remembered = None
      shelf = self._scheme_memory.get(tid, {})
      held = [f for f in fields if f in shelf]
      if held:
        remembered = held[0]
      if remembered is not None:
        var_combo.setCurrentText(remembered)
      elif prev and prev["var"] in fields:
        var_combo.setCurrentText(prev["var"])
      elif prev is not None and prev["var"] is None \
          and not self._fieldless_build:
        pass  # deliberately unassigned: leave it on "---". Cycling a
        # default back in here would undo the user's choice on every
        # design change, and their map would grow an element they had
        # switched off
      elif preferred:
        var_combo.setCurrentText(preferred[row % len(preferred)])
      var_combo.currentIndexChanged.connect(
        self._refresh_preview_colours)
      self.table.setCellWidget(row, 1, var_combo)

      mode_combo = ModeCombo()
      mode_combo.addItems(self.MODES)
      mode_combo.setToolTip(
        "How this element is symbolized; adjustable later in the "
        "Layer Styling panel.")
      mode_combo.setCurrentText(self._plausible_mode(
        var_combo.currentText()))
      # The scheme comes back with a remembered field, stays where the
      # column survived, and is derived fresh everywhere else.
      restored = self._unshelve_scheme(tid, remembered) \
          if remembered is not None else None
      # A SCHEME THE SWITCH RESET MUST NOT BE REFILLED FROM `prev`.
      # The shelve above POPS the records, and three restores below
      # fall back to the previous ASSIGNMENT when the record is
      # empty -- which is exactly the state the pop just created, so
      # the ramp, the tick and the count all came straight back. That
      # is ruling 3 of 2026-08-21 undone by the code that reads the
      # table it was rebuilding.
      scheme_reset = restored is None and (
        column_gone or tid in self._scheme_just_reset)
      if restored is not None:
        if restored.get("mode_raw") in self.MODES \
            and restored.get("touched"):
          mode_combo.setCurrentText(restored["mode_raw"])
        mode_combo.setProperty("touched", bool(restored.get("touched")))
      elif prev and prev.get("mode_raw") in self.MODES \
          and prev.get("style_touched") and not column_gone:
        mode_combo.setCurrentText(prev["mode_raw"])
        mode_combo.setProperty("touched", True)
      else:
        mode_combo.setProperty(
          "touched", bool(prev and prev.get("style_touched")
                          and not column_gone))
      mode_combo.setProperty("tile_id", tid)
      # the baseline the scheme-change destruction compares against;
      # kept current in _on_mode_chosen
      mode_combo.setProperty("last_style", mode_combo.currentText())
      mode_combo.activated.connect(
        lambda _i, c=mode_combo, v=var_combo: self._on_mode_chosen(c, v))
      # currentIndexChanged rather than activated, so the destruction
      # fires however the style really changes -- a click emits both,
      # and the dialog's own programmatic style writes all block
      # signals, so nothing here reacts to the dialog talking to
      # itself
      mode_combo.currentIndexChanged.connect(
        lambda _i, c=mode_combo: self._on_style_changed(c))
      mode_combo.currentIndexChanged.connect(
        self._refresh_preview_colours)
      self.table.setCellWidget(row, 2, mode_combo)
      # seed the banked-mode bookkeeping with the field the row is
      # BORN on: a row that never moves never fires the handler, and
      # without the seed the first excursion had no outgoing field to
      # bank the chosen style under
      var_combo.setProperty("ws_last_var", var_combo.currentText())
      var_combo.currentIndexChanged.connect(
        lambda _i, v=var_combo, m=mode_combo: self._follow_variable(v, m))

      k_spin = QSpinBox()
      # 2 to 20, the settled range, and the SAME range _sync_row sets.
      # This said (2, 12) while _sync_row said (2, 20): a restored
      # count above twelve was clamped by the setValue below, before
      # the wider range arrived. Nothing showed, because the real
      # value also rides on the user_k property and _sync_row restores
      # it from there — so the bug was invisible and waiting for
      # whoever reordered these two lines.
      k_spin.setRange(2, 20)
      # ITS HANDLER WRITES BACK TO IT, so keyboard tracking must be
      # off. `on_k` refuses a count that cannot carry the row's pins
      # and puts the spinner back, and a validator is asked one
      # keystroke at a time: typing 20 arrives as "2" first, which on a
      # doubly-pinned row is refused and reverted, and the "0" then
      # lands in a box the handler has just rewritten. This is the same
      # family as `_skip_zero_scale` firing per keystroke and
      # un-mirroring a design (2026-08-17), and it becomes a defect the
      # moment a handler writes to its own box rather than when the box
      # is created -- which is why it is being added in the same commit
      # as that handler.
      k_spin.setKeyboardTracking(False)
      # the previous assignments first (a rebuild inside one
      # session), then the element's own record, which is the only
      # thing that exists after a REOPEN, then the default
      # The ELEMENT'S OWN RECORD FIRST, and the order matters. `prev`
      # is the previous ASSIGNMENT, whose k is 50 for a row sitting on
      # Quant: Unclassed -- fixed by the definition of that style
      # rather than chosen by anybody. Restoring from it wrote 50 into
      # `user_k`, which `_assignments` reads, so an excursion through
      # Unclassed and back left the element claiming fifty classes
      # while the spinner displayed its clamped 20 and the map drew
      # something else again: three numbers for one setting.
      # `_class_counts` is only ever written by a user moving the
      # spinner, so it is the one of the two that means "chosen".
      # Clamped here as well as displayed, because a value the
      # controls cannot express must not survive in a property.
      # Guarded by test_an_unclassed_excursion_leaves_the_count_alone.
      restored_k = self._class_counts.get(tid)
      if not restored_k and prev and prev.get("k") and not scheme_reset:
        restored_k = prev["k"]
      restored_k = max(2, min(int(restored_k or 5), 20))
      k_spin.setValue(restored_k)
      k_spin.setProperty("user_k", restored_k)
      k_spin.setToolTip(
        "Number of classes; categorized rows show how many "
        "categories were found.")

      k_spin.setProperty("tile_id", tid)

      def on_k(v, sp=k_spin):
        if sp.isEnabled():
          # THE COUNT IS REFUSED AND THE PINS ARE LEFT ALONE.
          # (Maintainer's ruling, 2026-08-17.) Moving this spinner to a
          # count too small to carry the row's pins used to let the
          # change through, whereupon `_retire_an_undrawable_pin`
          # popped the WHOLE record, removed the stamp so a reopen
          # could not recover it, and told the user the bound "cannot
          # be drawn from the values it holds now" -- blaming data that
          # had not moved. Putting the spinner back did not bring the
          # pins home. Measured 2026-08-17 by
          # `tools/probes/pins_killed_by_the_class_count.py`.
          #
          # Refusing here is `pin_problem`'s own convention: a refused
          # pin reverts its control and reports rather than being
          # quietly clamped. It is also the copied-ladder carve-out two
          # lines into `_retire_an_undrawable_pin` arriving from the
          # other side -- that one already keeps a copied ladder
          # through this very act, and says so, which left one handler
          # giving opposite answers to the same question.
          #
          # The sentence is `pin_problem`'s own, which was composed for
          # exactly this case and had never been shown to anybody.
          tid_here = sp.property("tile_id")
          refusal = self._class_count_refused(tid_here, v) \
              if tid_here else None
          if refusal:
            previous = int(sp.property("user_k") or 5)
            sp.blockSignals(True)
            sp.setValue(previous)
            sp.blockSignals(False)
            self._report_quietly(refusal)
            return
          sp.setProperty("user_k", v)
          # and against the element, so the count outlives the widget
          if sp.property("tile_id"):
            self._class_counts[sp.property("tile_id")] = v
          # a new class count reclassifies the column, and positional
          # picks name classes that no longer exist: destroy, and say
          # so (settled 2026-08-09). Only enabled spins reach here,
          # which is exactly the editable graduated rows.
          tid_here = sp.property("tile_id")
          if tid_here:
            self._clear_quant_customization(
              tid_here, "a new class count", reset_range=False)
            self._release_copied_breaks(tid_here, "a new class count")
          self._queue_live()

      k_spin.valueChanged.connect(on_k)
      self.table.setCellWidget(row, 3, k_spin)
      k_spin.setVisible(not self.table.isColumnHidden(3))

      default = self.DEFAULT_RAMPS[row % len(self.DEFAULT_RAMPS)]
      # THE ELEMENT'S RECORD FIRST, then the previous assignment.
      # These were the other way round, and `prev` is a snapshot that
      # can be older than the record: after a run landed, the cell
      # came back showing the ramp the run was LAUNCHED with while
      # `_ramp_choices` held the one the user had picked while it
      # tiled. The map keeping the old ramp there is deliberate --
      # with live update off nothing repaints unasked -- but the
      # CONTROL denying a choice the dialog had kept is not: it is a
      # control lying about the map, which is the fault the Custom
      # display exists to prevent elsewhere. `_ramp_choices` is
      # written by every path that changes a ramp, including the one
      # that follows a dock edit, so it is the authority.
      # Guarded by test_a_ramp_chosen_during_a_run_is_not_lost.
      wanted = self._ramp_choices.get(tid) \
        or (None if scheme_reset else (prev.get("ramp") if prev else None)) \
        or default
      self.table.setCellWidget(
        row, 4, self._make_ramp_combo(tid, wanted))
      if prev and prev.get("single_colour"):
        self._single_colours[tid] = prev["single_colour"]
      if prev is not None and "reverse" in prev and not scheme_reset:
        # The report may only ADD a tick, never remove one, and the
        # asymmetry is the point.
        # `_assignments` reports the SWITCH, and reports False while
        # it is greyed -- right for the map, since an element with no
        # ramp must not reverse anything, but it is not a statement
        # about what the user chose. `_sync_row` unchecks that widget
        # and deliberately leaves the record standing so the tick
        # returns when the element has a ramp again; restoring from
        # the report undid exactly that, and a rebuild in the greyed
        # state silently discarded the tick. An actual untick needs
        # no help here: the toggle handler has already written False
        # into the record, so a False in the report carries nothing
        # the record does not already know. Guarded by
        # test_a_reverse_tick_survives_a_rebuild_while_it_is_greyed.
        self._reverse_choices[tid] = bool(prev["reverse"]) \
            or self._reverse_choices.get(tid, False)
      # THE PREVIOUS TABLE FILLS A GAP; IT DOES NOT OVERRULE THE
      # RECORD. `prev` is the assignment read off the rows as they
      # stand, and it exists so a rebuild within one project does not
      # lose a choice. It was written back unconditionally, which
      # makes the WIDGETS the authority -- and after a project is
      # replaced the widgets belong to the project that has gone.
      #
      # Instrumented 2026-08-17, and this is the line the trace named:
      # `ADOPT a: layer=40 dialog=100 replacing=True` recovered the
      # user's 40 off the incoming layer, and the very next
      # `PREV a: table=100 dialog=40` put the outgoing project's 100
      # back over it. One Generate then painted 100 into the .qgz.
      #
      # Filling only a GAP costs nothing within a project, because the
      # spin's own handler writes the record on every change, so the
      # two are in step by construction and this branch never fires
      # except where the record has nothing.
      if prev is not None and "opacity" in prev \
          and tid not in self._opacity_choices:
        _dump("PREV", tid, "table=", prev["opacity"], "dialog=", "-")
        self._opacity_choices[tid] = prev["opacity"]

      if prev and prev.get("class_choice") is not None \
          and not scheme_reset:
        self._class_choices[tid] = prev["class_choice"]
      # A SECOND WRITE OF THE RESTORED CLASS SOURCE STOOD HERE and was
      # deleted the same night: `_unshelve_scheme` already puts it
      # back into `_class_choices`, so with the guard above in place
      # this could only ever repeat it. Its catalogue entry SURVIVED,
      # which is how a redundant line announces itself -- the second
      # time tonight, and the rule is the one this file already
      # carries: prefer deleting a line that does not earn its keep to
      # writing a test that defends it. The behaviour is guarded by
      # test_a_class_source_comes_home_to_the_dataset_it_was_chosen_on
      # through the guard above.
    # WAS THIS BUILD MADE WITHOUT ANY FIELDS? If so, the "---" it left
    # on every row is an artefact rather than a choice, and the next
    # build must apply its defaults instead of preserving it. A user
    # who opens the plugin before loading data got exactly that: the
    # dropdown filled in once the chooser settled, and every row
    # stayed empty because the fieldless build looked like somebody
    # deliberately unassigning all four.
    self._fieldless_build = not fields
    # Spent by the rebuild that answered it: a later rebuild has a
    # scheme nobody just reset, and leaving this armed would strip a
    # ramp the user chose after the switch.
    self._scheme_just_reset = set()
    self._update_dynamic_columns()
    # ...and every fresh row is asked what its LAYER holds, because
    # the rows above were built from the dialog's records and a layer
    # adopted from a reopened project or a GeoPackage may carry a
    # renderer no row can name. Without this a project reopened after
    # an element was styled in QGIS came back reading "Quant:
    # Quantiles" over a rule-based map, and the next Generate would
    # have destroyed the user's work -- measured 2026-08-15 by the
    # round-trip test, which is why deferral is inferred here rather
    # than trusted from a stamp.
    self._refresh_deferring_rows()

  # ------------------------------------------------------------ assignments

  def _stamp_category_colours(self, layer, assignment):
    """Record an element's customization on its output layer.

    Args:
      layer: the output layer for this element.
      assignment: its dict from ``_assignments()``.

    Returns:
      None. Writes TWO custom properties QGIS saves inside the
      project file -- weavingspace_category_colours for categorical
      hand-picks, weavingspace_quant_style for a graduated element's
      positional picks, PINNED BOUNDS and display range -- each
      cleared when there is nothing to record, so a layer never
      carries stale choices from a previous assignment.

    JSON rather than a Python repr: a custom property is written into
    the .qgz as text, and this has to survive being read back by a
    future version without eval'ing whatever the file contains.
    """
    # A DEFERRING ELEMENT'S RECORD IS LEFT ALONE, NEITHER WRITTEN NOR
    # CLEARED. While the plugin is not deciding an element's symbology
    # it has nothing to stamp -- and `_assignments` reports a
    # deferring row with mode "Deferring to QGIS" and its picks and
    # pins as None, which is INDISTINGUISHABLE HERE from a user who
    # cleared everything. So both branches below took their else and
    # removed the properties.
    #
    # Measured 2026-08-17, by both routes: pin an element and pick a
    # class colour, restyle it in QGIS's Symbology panel, then either
    # restyle or re-tile. The stamp is gone from the layer, gone from
    # the .qgz read as bytes, and a reopened project brings back
    # neither the bounds nor the colours -- while a control element
    # beside it, pinned identically and not deferring, keeps both. The
    # open window goes on showing the work the file no longer has,
    # which is what makes it silent.
    #
    # CLEARING IS RIGHT WHEN THE USER LET SOMETHING GO and wrong when
    # the plugin merely stopped deciding. Deferral is temporary by
    # design -- the whole point is that an element can be taken back
    # -- so the stamps are exactly what has to survive it. Asked of
    # the RENDERER rather than of the row, because that is the single
    # authority for this question and the row may not have caught up
    # at the landing.
    # ASKED OF THE LAYER IN HAND, not of `_element_is_deferring`,
    # which looks the element up in `_element_layer_ids`. At the run
    # LANDING that registry still names the layer this run is
    # replacing, so the question would be put to the old object --
    # measured, and it is why the first version of this guard mended
    # the restyle route and left the landing untouched. The two call
    # sites both have the right layer already; the registry is the
    # only thing that does not agree with them.
    if bridge.expressible_style(layer.renderer()) is None:
      return
    # THE DICTS ARE THE SOURCE, NOT THE MODE-FILTERED ASSIGNMENT.
    # `_assignments` reports these records EMPTY for any row not
    # wearing the mode that displays them -- so a stamp taken from it
    # wrote absence-by-mode as absence-by-choice, and a pin or a
    # hand-picked colour made on one style died at the project
    # boundary the moment the row generated wearing another. That is
    # the exact conflation row 14's fix gated in
    # `_apply_element_records`, arriving at the OTHER writer. The
    # session dicts hold what is genuinely kept (per element AND
    # field, kept silently, ruling of 2026-08-20), so absence in THEM
    # is a real absence and may clear. Found by the shelf hunt of
    # 2026-08-26, confirmed here by comparing stores.
    tid = str(assignment.get("id"))
    var = assignment.get("var")
    picked = (assignment.get("category_colours")
              or self._category_colours.get(tid, {}).get(var or ""))
    if picked:
      # WHICH OF THEM ARE ONLY HELD, and the stamp is the only place
      # that can say so across a project boundary. Colours kept
      # because a class-source file could not be read must survive a
      # save -- they are what the map draws -- and must still give way
      # when the file answers again; a reopened project that could not
      # tell them from picks would go on drawing them over a scheme
      # somebody had restored. Written as a list of the VALUES, so an
      # older build reading this property simply ignores a key it does
      # not know and behaves as it always did.
      held = list((self._kept_for_unreadable.get(tid) or {}).get(
        var or "") or {})
      stamp = {"field": assignment["var"], "colours": picked}
      if held:
        stamp["kept"] = sorted(held)
      layer.setCustomProperty(
        "weavingspace_category_colours", json.dumps(stamp, sort_keys=True))
    else:
      layer.removeCustomProperty("weavingspace_category_colours")
    # the graduated customization travels the same way: positional
    # picks plus the display window, under their own property so the
    # two records cannot corrupt one another
    quant = (assignment.get("quant_colours")
             or self._quant_colours.get(tid, {}).get(var or ""))
    window = tuple(assignment.get("range_bounds", (0, 100)))
    if window == (0, 100):
      window = tuple(self._ramp_ranges.get(tid, (0, 100)))
    # ...and the PINNED BOUNDS with them. They have to be stamped
    # because nothing on a renderer records that a break was CHOSEN
    # rather than computed: a reopened project would read the breaks
    # back as ordinary classes, the row would show no pin, and the
    # next Generate would recompute over them. That is the shape of
    # the opacity and ramp defects of 2026-08-13, and this is the
    # same remedy.
    pinned = (assignment.get("pinned")
              or self._pinned_bounds.get(tid, {}).get(var or "") or {})
    # The mode gate is GONE from this condition, deliberately: a pin
    # kept silently on a row wearing categories is still the user's
    # work, and the stamp is what carries it across the project
    # boundary. What decides is whether the SESSION holds anything.
    if (quant or pinned or window != (0, 100)):
      layer.setCustomProperty(
        "weavingspace_quant_style",
        json.dumps({"field": assignment["var"],
                    "colours": quant or {},
                    # low and high are numbers; "breaks" is a whole
                    # copied ladder, so both shapes have to travel
                    "pinned": {
                      key: ([float(x) for x in value]
                            if isinstance(value, (list, tuple))
                            else float(value))
                      for key, value in pinned.items()},
                    "range": list(window)}, sort_keys=True))
    else:
      layer.removeCustomProperty("weavingspace_quant_style")
    # ...AND THE GROUP RECORD FOLLOWS, coalesced. Every store of a
    # fact, mended together: a dock edit the dialog adopts re-stamps
    # the LAYER here, and until 2026-08-26 nothing re-stamped the
    # GROUP -- so a recolour made in QGIS's own panel was adopted
    # into the dialog, the layer and the file, while the group record
    # kept the pre-edit colours, and the next reopen applied that
    # stale record over everything adoption had just recovered (the
    # doors hunt of round nine; also the mechanism under the
    # consistency sweep's reopen finding). Queued rather than called,
    # because a landing stamps the group itself after calling this
    # once per element, and a burst of dock edits needs one stamp,
    # not one per signal.
    self._queue_group_restamp()

  def _queue_group_restamp(self):
    """Ask for the working group's record to be re-stamped, soon.

    Returns:
      None. Arms a zero-delay single shot that stamps the group of
      this dialog's own layers -- unless a run is in flight (its
      landing stamps with the launch snapshot, which must win), a
      group selection or restyle is mid-apply (the record and the
      widgets are transiently out of step, and what sits there is
      nobody's decision), or the dialog has been retired.

    Zero-delay is the coalescing: every caller in one event-loop turn
    shares the single queued stamp.
    """
    if getattr(self, "_group_restamp_queued", False):
      return
    self._group_restamp_queued = True

    def stamp():
      self._group_restamp_queued = False
      if (self._task is not None or self._selecting_a_group
          or getattr(self, "_applying_style", False)
          or _dialog_is_gone(self) or _live_dialog() is not self):
        return
      # AND A TABLE WITH NO FIELDS TO OFFER HAS NOTHING TO SAY. When
      # the region layer is removed from the project the table goes
      # blank because its columns went with it -- a blank the plugin
      # imposed, not one anybody chose -- and this writer stands
      # nowhere near a landing, so it wrote that blank over a good
      # record: every element's variable and style gone, and the next
      # dialog opened in that project met a map plainly drawn from
      # three columns beside a table describing none of them, with
      # Generate refusing for want of a variable. The switch-out stamp
      # was given this condition on 2026-08-26 and this door was not.
      # (Found 2026-08-27; `_fieldless_build` is the same owner of the
      # question that the assignment table itself reads.)
      if getattr(self, "_fieldless_build", False):
        _dump("STATE", "no-queued-restamp-the-table-has-no-fields")
        return
      try:
        self._stamp_working_state(
          self._group_of_our_layers(QgsProject.instance().layerTreeRoot()))
        # ...AND THE FILE'S OWN RECORD WITH IT, because a dock edit
        # this dialog adopts is written into the file's STYLES by
        # every adoption exit and was written into the file's RECORD
        # by none of them. The file then disagrees with itself, and
        # the half a colleague resumes from is the record: they open
        # the map drawing a colour somebody picked, the dialog tells
        # them nothing was picked, and their first Generate paints
        # over it. Queued here rather than added to six exits, so a
        # seventh cannot be written without it.
        # THE FILE'S RECORD IS SAVE'S, and this queue's job is the
        # GROUP's record alone. Before 2026-08-27 the file was
        # written by whatever act happened to touch it, which is how
        # its styles and its record came to disagree; now one act
        # writes both.
      except Exception:
        _dump("STATE", "queued-restamp-failed",
              traceback.format_exc(limit=3))
    QTimer.singleShot(0, stamp)

  def _adopt_category_colours(self, layer, tile_id):
    """Read stamped customization back off an adopted output layer.

    Args:
      layer: an existing output layer found in the project.
      tile_id: the element it carries.

    Returns:
      None. Reads BOTH stamped records -- categorical hand-picks, and
      a graduated element's positional picks with its display range
      -- filling in only where the dialog has nothing of its own, so
      a reopened project restores the user's work without overwriting
      anything chosen since.

    Anything unreadable is ignored rather than raised: a project file
    edited by hand, or written by a later version of the plugin, must
    not stop the dialog from opening.
    """
    # OPACITY comes from the layer itself rather than from a stamp,
    # because QGIS already persists layer opacity in the project and a
    # second copy could only disagree with it. Until 2026-08-13 the
    # dialog read neither: a reopened project showed 100% in the table
    # while the layer was still at the 60% the user chose, and the two
    # disagreed silently. That is worse than losing the setting, since
    # _add_output_layers pushes the dialog's belief back onto the
    # layer, so the next restyle -- any restyle, for any reason --
    # quietly undid a choice still visible in QGIS's own layer panel.
    # Only filled in where the dialog has nothing of its own, like
    # everything else here, so a choice made since reopening wins.
    # INSTRUMENT, behind an environment flag, kept because this exact
    # branch cost a reverted fix on 2026-08-17: it says what the LAYER
    # is carrying beside what the dialog already believes, which is
    # the only pair that decides whether adoption fills anything in.
    _dump("ADOPT", tile_id, "layer=", round(layer.opacity() * 100),
          "dialog=", self._opacity_choices.get(tile_id, "-"),
          "replacing=", self._project_is_being_replaced)
    # THE LAYER WINS WHILE A PROJECT IS BEING REPLACED, and only then.
    # "Fill in only where the dialog has nothing of its own" is right
    # within one project: a choice made since reopening must not be
    # overwritten. Across TWO projects it is wrong, because tile ids
    # repeat -- element `a` of the incoming project is element `a` of
    # the outgoing one as far as every record here is concerned.
    #
    # `_forget_the_last_project` empties those records, correctly, but
    # `_refresh_table` runs between the clear and this call and refills
    # them from the SURVIVING CELL WIDGETS, which still show the
    # previous project's numbers. Instrumented 2026-08-17: `FORGET`,
    # then `PREV a: table=100 dialog=<none>`, then `ADOPT a: layer=40
    # dialog=100` -- the user's 40 found and declined.
    if self._project_is_being_replaced or \
        tile_id not in self._opacity_choices:
      self._opacity_choices[tile_id] = max(0, min(100, round(
        layer.opacity() * 100)))
    # THE ROW'S SYMBOLOGY, read off the renderer QGIS saved. Same
    # argument as opacity above and the same authority: the layer is
    # carrying the map, so it is carrying the truth, and a table that
    # disagrees with it does not stay cosmetic -- _add_output_layers
    # pushes the table's belief back, so the next Generate would
    # overwrite the map with defaults the user never chose. Until
    # 2026-08-13 the ramp, the reverse flag and the class count were
    # all lost this way; the round-trip test compared all three and
    # never moved them off a default, so nothing failed.
    #
    # WHERE THE RAMP CANNOT BE NAMED, the classes themselves are read
    # back and the row reads Custom -- the maintainer's instruction,
    # and the honest answer, since Custom already means "these
    # colours, not that ramp" and the swatch draws them. A reversed
    # ramp is a clone matching no name in the library, so it arrives
    # here as Custom rather than as a wrong ramp name, which is the
    # right way round: the map is preserved exactly and the control
    # stops claiming a ramp that is not what is drawn.
    self._adopt_row_symbology(layer, tile_id)
    raw = layer.customProperty("weavingspace_category_colours")
    if raw:
      try:
        stored = json.loads(raw)
        field = stored["field"]
        colours = {str(k): str(v) for k, v in stored["colours"].items()}
      except (ValueError, KeyError, TypeError, AttributeError):
        field, colours = None, None
      if field and colours:
        # PER KEY, NOT PER FIELD, and the difference cost the No data
        # colour. `_adopt_row_symbology` runs first and ASSIGNS the
        # colours it recovered from the renderer -- which never
        # include the no-data entry, since no renderer records one --
        # so a setdefault on the FIELD found something already there
        # and did nothing. Measured 2026-08-16: the .qgz held
        # {"no-data": "#abcdef", "0": "#123456"} and the dialog came
        # back with the class colour alone, offering #dddddd over a
        # map still drawing #abcdef, until the next Generate painted
        # #dddddd over it. A plain close-and-reopen was enough.
        # The gap rule itself is unchanged and still right: anything
        # the dialog already holds was chosen since reopening and
        # wins. It just has to be asked about each colour rather than
        # about the whole field.
        have = self._category_colours.setdefault(tile_id, {}).setdefault(
          field, {})
        for key, value in colours.items():
          have.setdefault(key, value)
        # ...AND WHICH OF THEM THE ELEMENT ONLY HOLDS, so a scheme
        # file that answers again after the project is reopened takes
        # its colours back exactly as it would have done in the
        # session that saved them. A record written before this key
        # existed simply has none, and those colours stay as picks --
        # which is what that build recorded them as.
        held = stored.get("kept")
        if isinstance(held, list):
          shadow = self._kept_for_unreadable.setdefault(
            tile_id, {}).setdefault(field, {})
          for key in held:
            colour = colours.get(str(key))
            if colour is not None and have.get(str(key)) == colour:
              shadow.setdefault(str(key), colour)
    # and the graduated record, guarded the same way: an unreadable
    # property must never stop the dialog from opening
    raw = layer.customProperty("weavingspace_quant_style")
    if not raw:
      return
    try:
      stored = json.loads(raw)
      field = stored["field"]
      colours = {str(k): str(v)
                 for k, v in stored.get("colours", {}).items()}
      lo, hi = (int(x) for x in stored.get("range", [0, 100]))
    except (ValueError, KeyError, TypeError, AttributeError):
      return
    if not field:
      return
    if colours:
      # per key, for the reason spelled out on the categorized twin
      # above: the recovered class colours arrive first and would
      # otherwise make this whole merge a no-op, taking the No data
      # colour with them
      have = self._quant_colours.setdefault(tile_id, {}).setdefault(field, {})
      for key, value in colours.items():
        have.setdefault(key, value)
    if (lo, hi) != (0, 100) and 0 <= lo <= hi <= 100 \
        and tile_id not in self._ramp_ranges:
      self._ramp_ranges[tile_id] = (lo, hi)
    # The pins, under the same one-unreadable-property-must-not-stop-
    # the-dialog-opening guard as everything above, and under the
    # same gap rule as the colours: only ever filled in where the
    # dialog holds nothing, since anything it holds was chosen since
    # reopening and wins.
    stored_pins = {}
    try:
      # THIS WHITELIST IS THE RECORD'S REAL DEFINITION, and a key
      # missing from it is dropped in SILENCE on every reopen -- the
      # record in memory would be right all session and wrong the
      # moment the project came back. "floor" and "ceiling" joined it
      # on 2026-08-19 in the same commit that started writing them.
      # When you widen this record, widen this line: it is the only
      # place that decides what survives a save.
      for key, value in (stored.get("pinned") or {}).items():
        if key in ("low", "high", "floor", "ceiling"):
          stored_pins[str(key)] = float(value)
        elif key == "breaks" and isinstance(value, (list, tuple)):
          stored_pins["breaks"] = [float(x) for x in value]
    except (TypeError, ValueError):
      stored_pins = {}
    if stored_pins:
      self._pinned_bounds.setdefault(tile_id, {}).setdefault(
        field, dict(stored_pins))

  def _pins_in_force(self, tile_id, field):
    """How many ends of this element's ladder the user has pinned.

    Args:
      tile_id: the element.
      field: the column it carries; an empty name means no pins, since
        the record is keyed by field as well as by element.

    Returns:
      0, 1 or 2. A count rather than the record itself, because both
      callers want the same arithmetic -- a ladder of k classes has
      k-1 boundaries and each pin names one -- and reading the record
      twice is how two sites come to disagree about one number.
    """
    if not field:
      return 0
    record = self._pinned_bounds.get(tile_id, {}).get(field) or {}
    return (record.get("low") is not None) + \
        (record.get("high") is not None)

  def _class_count_refused(self, tile_id, count):
    """Why this class count cannot carry the element's pins, or None.

    Args:
      tile_id: the element whose Classes spinner is being moved.
      count: the count the spinner has just been moved to.

    Returns:
      One sentence for the message bar when the pins in force need
      more boundaries than `count` provides, or None -- which is the
      ordinary case, including every unpinned row. Nothing is changed
      here; the caller reverts its own control.

    Asked of the LIVE row rather than of any snapshot, because the
    spinner is being moved right now and the pins it must respect are
    whatever the colour editor has accepted by this moment. Reads the
    data not at all: whether a count can carry two pins is arithmetic
    about the ladder, and mixing the data into it is what made this
    refusal look like a statement about the user's values.
    """
    row = self._assignment_for(tile_id)
    field = (row or {}).get("var")
    if not field:
      return None
    record = self._pinned_bounds.get(tile_id, {}).get(field) or {}
    return bridge.pin_count_problem(
      record.get("low"), record.get("high"), count)

  def _retire_an_undrawable_pin(self, field, assignment):
    """Drop a pin the data has moved out from under, and say so.

    Args:
      field: the column the element carries.
      assignment: that element's row of `_assignments`, read for its
        tile id, its class count and its pin record.

    Returns:
      One sentence for the message bar when a pin was retired, or
      None when there was nothing to retire -- which is the ordinary
      case. The dialog's own record is cleared as a side effect, and
      the element is left to be re-stamped by the run in progress.

    WHY THIS EXISTS. `make_graduated_renderer` already asks
    `bridge.pin_problem` of the values as they NOW are and drops a
    pin it cannot draw, which is right: the alternative is a ladder
    running to a bound the data no longer reaches, four classes
    wearing nothing and every tile in the first. But bridge draws
    maps and says nothing, so the loss was invisible -- and the
    comment there said "the DIALOG reports the loss" while no such
    site existed anywhere.

    Measured 2026-08-16: pin `v1`'s low at 7.0 on a column running
    0-35, then retype that column to 5000-40000 or swap in a layer at
    that scale. The map's first class ends at 12000, and
    `_pinned_bounds` still holds 7.0, the ramp cell still draws its
    pinned box, the layer is still stamped with it, and nothing is
    said. Save, reopen, and the 7.0 is read back off the layer, so
    the row shows a pin over a map that ignores it -- while
    `pin_problem` refuses that very number if it is typed.

    A pin is a statement a PERSON made, so retiring one is worth a
    sentence rather than a silent correction; that is the same reason
    a refused pin reverts its control and reports instead of being
    quietly clamped.
    """
    tile_id = str(assignment.get("id") or "")
    record = self._pinned_bounds.get(tile_id, {}).get(field) or {}
    low, high = record.get("low"), record.get("high")
    # THE EDGES ARE ASKED TOO, and until 2026-08-19 they were not:
    # this returned here whenever `low` and `high` were both absent,
    # which is EXACTLY the record an adopted ladder writes -- `breaks`,
    # `floor` and `ceiling`, and neither pin. So pin flags had a
    # data-moved guard and edge values had none.
    #
    # WHAT THAT COST, measured that day by two hunts independently,
    # one of them reading the exported GeoPackage with sqlite3: retype
    # a ladder in QGIS's panel, then edit that column's values or
    # point the plugin at a layer of another magnitude, and every area
    # moved onto the paired layer as "outside the range". The element
    # drew nothing, flat khaki, in silence; Generate could not heal it
    # and the colour editor then refused to open, so no control named
    # the ceiling doing it.
    #
    # A CHECK THAT RUNS ONCE AT THE MOMENT A RECORD IS WRITTEN IS NOT
    # A GUARD ON THAT RECORD. `_adopt_dock_bounds` asks whether
    # anything survives the limits, and asks it once. This is the site
    # every caller already uses for "the data moved under this
    # record", so the same question belongs here, re-asked.
    limits = (record.get("floor") is not None
              or record.get("ceiling") is not None)
    if low is None and high is None and not limits:
      return None
    # THE LIVE CLASS COUNT, NEVER THE ONE THIS RUN WAS LAUNCHED WITH.
    # Two of the three callers hand in the LAUNCH SNAPSHOT, so a user
    # who raised the class count while a tiling was running and then
    # pinned both ends -- which the editor accepted, because it asks
    # the table -- had both bounds retired the instant the run landed:
    # `pin_problem` refuses two pins when `asked - 1 < 2`, and the
    # snapshot still said two. The record was cleared, the stamp was
    # REMOVED so a reopen could not recover them, the two pin controls
    # in the still-open window went on showing the numbers, and the
    # sentence blamed the user's data. Measured 2026-08-17.
    #
    # This project's rule is that everything the colour editor writes
    # must be RE-READ at the landing, and the re-read list was
    # complete. The loss came from a guard standing IN FRONT of it,
    # judging a fresh choice with a stale argument -- so the rule needs
    # its other half: A GUARD THAT RUNS BEFORE A RE-READ MUST BE ASKED
    # WITH RE-READ VALUES TOO.
    live = self._assignment_for(tile_id)
    if live is not None and live.get("var") == field:
      assignment = live
    source = self._classification_values(field)
    if source is None:
      return None
    values = source.uniqueValues(source.fields().indexOf(field))
    # A COPIED LADDER IS NOT JUDGED AGAINST THIS COLUMN, which is the
    # carve-out `make_graduated_renderer` has carried since copying
    # arrived and this site never learned. A copy is a claim about the
    # LADDER -- reproduce that classification here -- rather than a
    # claim about what these values support, which is the whole reason
    # somebody copies one. bridge says so at its own guard and
    # `test_a_pin_still_works_on_a_copied_ladder` holds it there.
    #
    # THE DISAGREEMENT WAS INVISIBLE AT BOTH CALL SITES, and that is
    # the lesson: `_copy_classification` validates each pin flag
    # ALONE, while this asks `pin_problem` about both TOGETHER. Two
    # bounds that are each fine separately can leave nothing between
    # them, so a ladder copied onto a column with a hole in it was
    # judged undrawable and the WHOLE record popped -- copied breaks
    # included -- the instant it was copied. Measured 2026-08-17: the
    # copy reports success, the record is empty immediately after, the
    # stamp writes `"pinned": {}`, and the next Generate silently
    # redraws that element with the scheme's own breaks. Four of five
    # boundaries differ.
    #
    # WHEN TWO SITES JUDGE ONE RECORD, CHECK THEY ASK THE JUDGE THE
    # SAME QUESTION. Retirement is for a pin the DATA MOVED OUT FROM
    # UNDER -- a column retyped or a layer swapped -- and a copy that
    # was legal when it was made has not had that happen to it.
    # THE LIMITS FIRST, and BEFORE the copied-ladder carve-out below:
    # an adopted ladder carries `breaks` and is exempt from having its
    # PINS judged against this column, which is right and is not what
    # this asks. Limits that exclude every value are not a claim about
    # a ladder; they are a pair of numbers the data has moved out from
    # under, and what they leave behind is an element that draws
    # nothing at all.
    # ASKED THROUGH `bridge.limits_leave_nothing`, which the COPY path
    # also asks before it writes a source's limits onto a target. The
    # test was written out by hand here first and would have been
    # written out a second time there; two spellings of one judgement
    # is how a copy comes to write limits this site then drops, and
    # this project has already paid for that at `pin_problem`.
    if limits and bridge.limits_leave_nothing(
        values, record.get("floor"), record.get("ceiling")):
      record.pop("floor", None)
      record.pop("ceiling", None)
      if not record:
        self._pinned_bounds.get(tile_id, {}).pop(field, None)
      self._custom_swatch_cache.pop(tile_id, None)
      return (f"The limits you set on '{field}' leave none of the "
              f"values it holds now, so they have been dropped.")
    if low is None and high is None:
      return None
    if record.get("breaks"):
      return None
    asked = int(assignment.get("k", 5) or 5)
    # ASKED OF THE POOL THE MAP IS CUT FROM, not of the whole column.
    # (Maintainer's ruling, 2026-08-19.) A floor or ceiling narrows
    # what the scheme classifies, and `bridge` judges the pin against
    # THAT pool -- so a pin the narrowed pool cannot carry was dropped
    # there, silently, while this site asked the un-narrowed question,
    # answered "fine", and said nothing. The record, the layer stamp
    # and the saved project then all went on claiming a pin the map
    # does not draw.
    #
    # THE TWO SITES NOW ASK THE JUDGE THE SAME QUESTION, which is this
    # project's own rule for a record judged in two places. The limits
    # stand and the pin is retired with the sentence below, the same
    # one a pin the data moved out from under already gets.
    judged = [v for v in values
              if bridge.absence_kind(v, record.get("floor"),
                                     record.get("ceiling"))
              != bridge.OUTSIDE_RANGE_KEY]
    if not bridge.pin_problem(low, high, judged, asked,
                              record.get("breaks")):
      return None
    # THE COUNT IN FORCE IS ASKED, AND NOTHING SOFTENS IT HERE.
    # This carried a re-ask with `max(asked, pins + 1)` for a few
    # hours on 2026-08-17, meaning to keep the Classes spinner from
    # destroying pins. It suppressed retirement on EVERY route while
    # only ONE door had been given a refusal, so a count arriving with
    # no control to refuse left the record and the layer stamp
    # claiming bounds the map was not drawing, in silence -- which is
    # worse than the loss it prevented, and is the exact harm row 28
    # was about.
    #
    # TWO DOORS INTO ONE STATE, ONE GUARDED, IS WHERE THE NEXT ONE
    # LIVES, and this was mine. The doors are guarded at the doors
    # now: the spinner refuses, and `_sync_row` raises a restored
    # count to one the pins fit. So a count reaching here really is
    # undrawable, and retiring it with a sentence is right.
    # ONLY THE PINS WHERE ONLY THE NARROWING REFUSED THEM.
    # (Maintainer's ruling, 2026-08-19.) Where the pin is undrawable
    # against the pool the LIMITS leave but drawable against the whole
    # column, the limits are what made it so -- and the ruling is that
    # THE LIMITS STAND AND THE PIN GOES. Taking the limits as well
    # would undo a second thing the user set, which they were never
    # asked about and would have to set again.
    if not bridge.pin_problem(low, high, values, asked,
                              record.get("breaks")):
      record.pop("low", None)
      record.pop("high", None)
      self._custom_swatch_cache.pop(tile_id, None)
      return (f"The class bound you set on '{field}' cannot be drawn "
              f"from the values it holds now, so it has been "
              f"recalculated.")
    # Clear the whole record for this field: the flags and any copied
    # boundary values go together, because what made them undrawable
    # was the column moving beneath all of them at once.
    self._pinned_bounds.get(tile_id, {}).pop(field, None)
    # The maintainer's wording, 2026-08-16. One form for one end and
    # for both: a user who pinned two ends and lost them reads "bound"
    # rather than "bounds", which is a small inaccuracy against the
    # cost of a sentence that changes shape while somebody is trying
    # to understand what happened to their map.
    return (f"The class bound you set on '{field}' cannot be drawn "
            f"from the values it holds now, so it has been "
            f"recalculated.")

  def _classes_nothing_wears(self, tile_id, assignment):
    """Which of an element's classes no tile of it falls into.

    Args:
      tile_id: the element, used to find its own output layer.
      assignment: its row of `_assignments()`, read for the variable
        and the styling mode.

    Returns:
      A list of class indices nothing occupies, or None when the
      question cannot be answered here -- no output layer yet, a
      renderer with no ranges, a field the layer does not carry. None
      and `[]` are deliberately different: `[]` is "measured, nothing
      is empty" and None is "not measured", and a caller must not
      report an unknown as an emptiness.

    THIS IS THE CALLER `bridge.unworn_classes` LOST, and the loss is
    the point. When the swatch hatching was withdrawn on 2026-08-17 it
    took `_unworn_stripes` with it, which was that function's only
    caller -- so the plugin went on computing nothing while CLAUDE.md,
    this module, docs/TESTING.md and the approved changelog all said
    emptiness was reported in words. A hunt measured it false the same
    day; the maintainer's ruling is that the signal was meant to stay,
    so it has a caller again.

    Asked of the ELEMENT's own output layer, because the question is
    what THIS element draws rather than what the map as a whole holds.
    A unit-tested mechanism with no live caller is a motionless axis,
    which is exactly what the hatching turned out to be as well, so
    the guard for this drives the notice rather than this method.
    """
    field = assignment.get("var")
    if not field or assignment.get("mode") != "Graduated":
      return None
    # UNCLASSED SAYS NOTHING ABOUT EMPTINESS, and this guard is the
    # second door into a rule the first door already had. An Unclassed
    # row IS "Graduated" with k forced to fifty, so nothing above this
    # line tells the two apart -- and fifty equal steps over any real
    # column leave a dozen or more of them unoccupied, always. Measured
    # 2026-08-17 on the packaged Auckland file: 15 of 50 empty on `fid`,
    # a uniform 1..155 and the least likely column in it to leave a gap.
    # The count was correct and the sentence should not have existed.
    #
    # `few_values_message` was given exactly this exemption on
    # 2026-08-16, after the maintainer reported the previous Unclassed
    # notice as unwanted: fifty is not a class count anybody chose, so
    # a notice about how few of them are filled is a warning about a
    # decision the user did not make. `test_an_unclassed_row_says_
    # nothing_about_a_reduction` holds that line.
    #
    # THE LESSON, which is this project's own and was paid for again:
    # when a sibling carries a hard-won exemption, GREP THE EXEMPTION
    # rather than the function. Restoring the emptiness signal added a
    # new caller asking the same question through a different door, and
    # the door had no lock on it.
    if assignment.get("scheme") == "Unclassed":
      return None
    layer_id = self._element_layer_ids.get(tile_id)
    layer = QgsProject.instance().mapLayer(layer_id) if layer_id else None
    renderer = layer.renderer() if layer is not None else None
    if renderer is None or not hasattr(renderer, "ranges"):
      return None
    # BOUND FIRST: a temporary list from a QGIS getter frees its
    # contents, and subscripting one has segfaulted this project once
    # and returned a plausible wrong colour another time.
    ranges = renderer.ranges()
    bounds = [(r.lowerValue(), r.upperValue()) for r in ranges]
    if not bounds:
      return None
    index = layer.fields().indexOf(field)
    if index < 0:
      return None
    try:
      return bridge.unworn_classes(bounds, layer.uniqueValues(index))
    except Exception:
      return None

  def _legend_size_note(self, field, assignment, tile_id=None):
    """The notice when a column draws fewer classes than it was asked.

    Args:
      field: the column the element carries.
      assignment: that element's row of _assignments, read for its
        class count and its pin record.
      tile_id: the element, so the ladder the map ACTUALLY draws can
        be asked which of its classes are empty. Optional, and when
        it is absent this falls back to the distinct-value count
        alone -- the behaviour of every caller before 2026-08-17.

    Returns:
      One sentence for the message bar, or None when the legend will
      hold exactly what the table asked for.

    Both notice sites call this rather than counting for themselves,
    because they used to count the WHOLE column against k -- true
    until a pin takes a class out of the ladder and its samples out
    of the pool, after which the sentence describes a legend the map
    does not have. That is the one thing these notices exist to
    prevent, so the arithmetic lives in bridge beside the code that
    performs it.

    TWO QUESTIONS, ONE SENTENCE, AND THE RENDERER WINS. The
    distinct-value count says WHY a ladder cannot be filled;
    `unworn_classes` says THAT it is not, measured on the classes the
    map draws. They are not the same question and a hunt found them
    disagreeing in four cases of six on 2026-08-17 -- a pin below the
    data, a pin above it, a copied ladder, and a plain tied column.
    So where the renderer can be asked, its answer decides whether
    anything is said at all, and the distinct-value sentence is
    preferred only when it is also true, because it carries the
    reason. Where it cannot be asked -- before the first run, most
    often -- the old count answers alone, since a notice that waits
    for output would never fire on the path a user meets first.
    """
    source = self._classification_values(field)
    if source is None:
      return None
    values = source.uniqueValues(source.fields().indexOf(field))
    asked = assignment.get("k", 5)
    # The SCHEME decides whether a reduction happens at all. An
    # Unclassed row is mode "Graduated" with k forced to fifty, so
    # nothing above this line distinguishes it, and the notice used to
    # announce a reduction the renderer never performs -- "12 distinct
    # values, so it draws as 12 classes, not 50" over a map drawing
    # fifty. The renderer's own guard is `if not unclassed`; this is
    # the same question, asked in the same words.
    drawn, from_pins = bridge.classes_the_map_will_draw(
      values, asked, assignment.get("pinned"),
      unclassed=assignment.get("scheme") == "Unclassed")
    explained = bridge.few_values_message(field, drawn, asked, from_pins)
    unworn = (self._classes_nothing_wears(tile_id, assignment)
              if tile_id is not None else None)
    if unworn is None:
      # nothing to measure against, so the count answers alone
      return explained
    if not unworn:
      # MEASURED, AND NOTHING IS EMPTY. The distinct-value sentence
      # may still be firing here -- fewer values than classes does not
      # mean a class goes unworn, since several values can share one
      # and the ladder still fill -- and saying "3 of 5 classes are
      # empty" over a map drawing five is the plainest kind of wrong.
      return None
    # BOTH FIRING IS NOT THE SAME AS BOTH AGREEING, and the count is
    # what a reader checks against their own legend. The
    # distinct-value sentence computes `asked - distinct`, which is a
    # PREDICTION; `unworn` is a measurement of the ladder in front of
    # them, and the two part company as soon as several values share a
    # class. So the reason is worth keeping only while it is telling
    # the truth about how many, and the measurement wins otherwise.
    if explained is not None and (asked - drawn) == len(unworn):
      return explained
    return bridge.empty_classes_message(field, len(unworn), asked)

  def _forget_the_last_project(self):
    """Drop every per-element record when the project is replaced.

    Called from QgsProject's `cleared` signal, which fires on File >
    New and immediately before File > Open. Nothing is read from the
    project here and nothing is written to it.

    Returns:
      None. Every record keyed by tile id is emptied in place, so the
      dialog meets the incoming project holding no beliefs about
      elements it has never seen.

    WHAT IS NOT DROPPED, and why. `_browsed_qmls` is the file
    chooser's memory of where the user keeps their styles, which is
    about a person's disk rather than about a map, and the watched
    layer state is re-established by the layer chooser's own handler
    when the new project's layers arrive.
    """
    # `_no_data_layer_ids` BELONGS IN THIS LIST, and its absence was
    # the third of the three clear sites this dialog has -- the one
    # named in the commit that fixed the second and then not checked.
    # A project opened while the dialog is still open left these ids
    # behind, and a .qgz restores layers under the SAME ids, so the
    # incoming project's no-data layers were deleted by the next
    # Generate as though they were the previous run's. Measured
    # 2026-08-16 by a hunt: both no-data layers gone from a reopened
    # project, while its element layers stayed.
    for record in (self._element_layer_ids, self._no_data_layer_ids,
                   self._last_signatures,
                   self._gpkg_tables_written, self._cat_count_cache,
                   self._values_cache, self._class_choices,
                   self._single_colours, self._ramp_choices,
                   self._reverse_choices, self._opacity_choices,
                   self._category_colours, self._quant_colours,
                   self._pinned_bounds, self._ramp_ranges,
                   self._class_counts, self._synced_modes,
                   self._class_source_stamps, self._ramp_memory,
                   # THE SHELF, which this list omitted until
                   # 2026-08-25. It was harmless only by accident: the
                   # bank swap used to run with None on a project
                   # replacement and empty the view on its way past,
                   # and tonight's fix -- an empty chooser no longer
                   # forgets the dataset -- removed that accident. A
                   # hunt found the consequence within the hour: a
                   # scheme shelved in the project you CLOSED merged
                   # into the first bank of the project you opened, so
                   # an element redrew a column from the old project,
                   # wearing its ramp, and wrote it into the
                   # GeoPackage. A cleanup that works by side effect
                   # is a cleanup nobody has written down.
                   self._scheme_memory,
                   # ...and the shadow of the hand-picks, joining the
                   # list in the commit that adds it rather than in
                   # the one that finds it missing. Left standing, it
                   # would release colours in the INCOMING project
                   # that were kept for a file the outgoing one named.
                   self._kept_for_unreadable,
                   self._custom_swatch_cache):
      record.clear()
    self._dataset_memory.clear()
    self._memory_layer_id = None
    self._pending_outgoing_shelf = None
    # ...AND WHAT THE OUTPUT-GROUP CHOOSER IS SHOWING, which is a
    # record keyed on layer ids from the project being replaced. Left
    # standing, its entries would name layers the incoming project has
    # never heard of, and a handle that resolves to nothing is exactly
    # the state `_on_group_chosen` has to rebuild its way out of. The
    # rule this method keeps failing is its own -- enumerate what a
    # clear site LEAVES -- so the new record joins it in the commit
    # that adds it rather than in the one that finds it missing.
    self._new_group_chosen = False
    self._selecting_a_group = False
    self._restoring_assignments = None
    # ...AND THE FACT THAT THIS SESSION HAS BUILT SOMETHING, which is
    # about the PROJECT and not about the window. `_landed_this_session`
    # means "there is work here to protect", and after File > Open
    # there is not: whatever this dialog built belongs to the project
    # being replaced. Left standing it made the incoming project's own
    # output group look like a stranger's -- the dialog let go of the
    # group it had just adopted and the next Generate built a rival
    # beside the user's map. It also decides `switched_from_work`, so
    # the same staleness would have read a first choice in the new
    # project as a change of dataset. Found 2026-08-25 by the reopen
    # journeys, and it is this method's own rule again: enumerate what
    # a clear site LEAVES.
    self._landed_this_session = False
    combo = getattr(self, "group_combo", None)
    if combo is not None:
      combo.blockSignals(True)
      combo.clear()
      combo.blockSignals(False)
    _dump("FORGET")
    # NEITHER DEFERRED-WORK FLAG SURVIVES A PROJECT, and until
    # 2026-08-28 both did. `closeEvent` clears them; this twin cleared
    # eight other remembered-intent records and not these two, so a
    # request queued while a run was in flight was carried into the
    # NEXT project opened and repainted its layers unasked -- and
    # adoption leaves `_last_signatures` empty, so the restyle's skip
    # matches nothing and every element is re-seeded. Found by the
    # asymmetry hunt of that day, working from the twin rather than
    # from the flag: a new flag inherits the clear site its
    # predecessor had and no other.
    # BEFORE THE CANCEL, NOT BESIDE `self._task = None` BELOW IT.
    # `TilingTask.cancel()` reports synchronously, so `_finish_run`
    # runs INSIDE this method and would honour a flag cleared
    # afterwards. Order, not presence, which is this file's own
    # standing lesson about a call put back in the wrong place.
    self._press_pending = False
    self._live_pending = False
    # ...and say so until adoption has read the incoming project. The
    # clear alone is not enough because the TABLE survives it and
    # refills these records before adoption is asked; this marker is
    # how adoption tells "the dialog holds a choice" from "the dialog
    # holds an echo of the project being replaced".
    self._project_is_being_replaced = True
    # ...AND THE MARKER CANNOT BE LEFT STANDING. Adoption's clear is
    # the primary drop, and File > New never reaches adoption at all
    # -- QGIS emits `cleared` and no `readProject` -- so the flag
    # stood for the rest of the session and `_swap_dataset_memory`
    # stayed inert (the doors hunt of 2026-08-26, round nine). A
    # project OPEN runs cleared-then-read synchronously, so a
    # zero-delay single shot queued here fires only after the whole
    # replacement -- adoption included -- has finished: by then a
    # standing flag is a leak, never a window.
    QTimer.singleShot(0, lambda: setattr(
      self, "_project_is_being_replaced", False))
    # ...AND THE TABLE, WHICH IS ITSELF A RECORD KEYED BY TILE ID.
    # Every dict above is emptied and the ROWS were left standing, so
    # the next `_refresh_table` read the surviving cell widgets as
    # `prev` and wrote their values straight back in -- before
    # adoption had a chance to read the incoming project's layers.
    # `setRowCount` does not destroy cell widgets, and the Opacity
    # cell is CREATED only when absent, so a spin box from the
    # previous project survived every clear this method performs.
    #
    # Measured 2026-08-17 with a dump inside both sites: on reopening
    # a saved project with the dialog open, `FORGET` ran, then
    # `PREV a: table=100 dialog=<none>` put 100 back, and adoption
    # then reported `ADOPT a: layer=40 dialog=100` -- it had found the
    # user's 40 per cent on the layer and declined it because the
    # dialog appeared to hold something of its own. One Generate later
    # the 100 was painted into the .qgz.
    #
    # THIS IS THE THIRD TIME THIS METHOD HAS BEEN FOUND INCOMPLETE,
    # and the rule it keeps failing is its own: ENUMERATE WHAT A CLEAR
    # SITE LEAVES, NOT WHAT IT CLEARS. The list above is long and
    # convincing and the thing it omitted was not a dict at all.
    self._mode_by_field = {}
    self._preserved_this_run = []
    # {tile_id: (assignment, bounds, colours)} -- dock edits that
    # arrived while a run was in flight, replayed once it has landed.
    # See _adopt_dock_bounds for why the numbers are kept rather than
    # a note to look again.
    self._adoption_deferred = {}
    # THE GROUP AND THE OUTPUT PATH GO TOO, and leaving them was the
    # larger half of this fault. `_group_name` survived, so
    # `_get_or_make_group` found the incoming project's group by name
    # and adopted it WITHOUT the element ids that say what is in it;
    # `_last_path` survived, so `force_new` stayed False and the
    # group was never rebuilt either (that second limb is history:
    # the path stopped feeding `force_new` on 2026-08-27, and what
    # keeps the record honest now is the forgetting below). The dialog then neither adopted
    # the opened project nor replaced it: the next Generate added its
    # layers ALONGSIDE the ones already there, the previous run's
    # elements sat above the new ones, and the map drew two tilings
    # at once while looking perfectly plausible. Measured 2026-08-16
    # by a hunt: ten layers in a group that should hold six.
    #
    # Forgetting the name is the honest state. A dialog just told the
    # project is gone knows nothing about which group in the NEXT
    # project is its own, and `_adopt_existing_group` runs only at
    # construction. Forgetting means the next Generate makes its own
    # group rather than silently sharing somebody else's: a visible
    # new group beats an invisible double map.
    # CANCEL ANY RUN STILL IN FLIGHT, first, because it was launched
    # for the project that is going away and `_on_generated` never
    # asks which project it is landing into. Measured 2026-08-17: with
    # a live run under way in project B, File > Open on project A
    # brought A's group back holding four MEMORY layers of 1,176
    # features tiled from B's region -- A's GeoPackage-backed layers
    # gone, and the whole thing reported as a success, "4,704 tiles
    # across 4 element layers". The user opened a project and it
    # destroyed the map in it.
    #
    # `cleared` fires on File > New and immediately BEFORE File >
    # Open, so this is the last moment at which the run can still be
    # stopped while it is still about the project it was started for.
    if self._task is not None:
      try:
        self._task.cancel()
      except Exception:
        # a task whose C++ object has gone cannot be cancelled and
        # does not need to be; refusing to forget the project because
        # of it would be worse
        pass
      self._task = None
    self._group_name = None
    self._last_path = None
    # THE WIDGET TOO, and it was the one record every clear site left
    # standing -- the only one a user can see, and the only one that
    # decides which bytes get written. Measured 2026-08-17: File > New,
    # a fresh region layer, Generate, and the previous project's
    # GeoPackage was rewritten from 55 features per element to 25,
    # with no warning. Blocked signals, because forgetting is not a
    # choice the user made in the widget.
    if hasattr(self, "gpkg_widget"):
      try:
        self.gpkg_widget.blockSignals(True)
        self.gpkg_widget.setFilePath("")
      finally:
        self.gpkg_widget.blockSignals(False)
    # ...and this, which belongs to the group being forgotten. A
    # record left set here would let the NEXT project's first run
    # replace a group it never adopted.
    self._adopted_group_unwritten = False
    self._outline_layer_id = None
    # auto-spacing must run again for whatever layer is chosen next:
    # the id it remembers belongs to a project that no longer exists
    self._auto_spacing_layer = None
    # ...and so does the claim that the number in the box is somebody's
    # own. A spacing typed for the project being closed must not keep
    # the next project's first dataset from getting a derived one,
    # which is the same reasoning as the line above it.
    self._spacing_is_mine = False

  def _adopt_row_symbology(self, layer, tile_id):
    """Read an adopted layer's ramp, class count and colours back.

    Args:
      layer: an existing output layer found in the project, whose
        renderer QGIS restored from the project file.
      tile_id: the element it carries.

    Returns:
      None. Fills in `_ramp_choices`, `_reverse_choices`,
      `_class_counts`, `_single_colours` and, where the ramp cannot be
      named, the positional picks in `_quant_colours` that make the
      row read Custom. Only ever fills a gap: anything the dialog
      already holds for this element was chosen since reopening and
      wins.

    Nothing here raises. A project written by another version, or
    edited by hand, must not stop the dialog opening -- so an
    unreadable renderer leaves the row on its defaults, which is
    exactly the behaviour that existed before this method.
    """
    try:
      renderer = layer.renderer()
    except Exception:
      return
    if renderer is None:
      return

    # A SINGLE SYMBOL is the whole of an unassigned or single-colour
    # element's styling, and the colour is right there on it.
    if hasattr(renderer, "symbol") and not hasattr(renderer, "ranges") \
        and not hasattr(renderer, "categories"):
      try:
        symbol = renderer.symbol()
        if symbol is not None and tile_id not in self._single_colours:
          self._single_colours[tile_id] = symbol.color().name()
      except Exception:
        pass
      return

    named, flipped = None, False
    try:
      # The REVERSE-aware match here, not _ramp_name_matching: a
      # reversed element's renderer carries a clone matching no name,
      # so the exact question would answer None and the row would come
      # back Custom with the tick lost. Recovering the flag is the
      # last thing a project round trip used to drop.
      named, flipped = self._ramp_match(renderer.sourceColorRamp())
    except Exception:
      named, flipped = None, False
    if named and tile_id not in self._ramp_choices:
      self._ramp_choices[tile_id] = named
      # Filed in the same breath and under the same gap rule as the
      # ramp, because the two are one choice: a name recovered without
      # its direction would put the row's combo on a ramp the map runs
      # the other way, which is the table lying about the map.
      if tile_id not in self._reverse_choices:
        self._reverse_choices[tile_id] = flipped

    if not hasattr(renderer, "ranges"):
      # A CATEGORIZED renderer, and until 2026-08-13 this returned
      # here with nothing recovered -- the twin asymmetry again, five
      # lines from the graduated recovery that has worked all along.
      #
      # What it cost: an element whose colours came from an imported
      # QML has a renderer matching no ramp in the library, so `named`
      # is None and the colours ARE the style. Nothing restores
      # `_class_choices` (the file token is stamped nowhere), so on
      # reopen the row read a default ramp with custom=False, and the
      # next Generate re-seeded the element from that ramp and painted
      # the user's imported scheme away. Measured on the map: four
      # file colours before, Set2's four after.
      #
      # The recovery is the maintainer's settled instruction for the
      # whole reopen question -- preserve what we can, and where we
      # cannot, read the classes back off the layer and call the row
      # Custom. Here the classes carry their own VALUES, so the
      # recovery is exact rather than positional: this is the easier
      # half of a rule already applied to the harder one.
      if not hasattr(renderer, "categories"):
        return
      try:
        field = renderer.classAttribute()
        # read values and colours in one pass while the category
        # objects are alive, for the same reason the ranges below are
        # held: a symbol pointer off a dead temporary segfaults
        pairs = [(category.value(), category.symbol().color().name())
                 for category in renderer.categories()]
      except Exception:
        return
      if not field or not pairs:
        return
      if self._category_colours.get(tile_id, {}).get(field):
        return          # the user has picks of their own; do not touch
      if named:
        # A named ramp is not proof that the ramp decides the colours.
        # A categorized renderer built from an imported QML records a
        # source ramp all the same (since 2026-08-13, so that QGIS's
        # own panel can show one), while the template's colours
        # override it -- so returning here on a name recovered nothing
        # for exactly the case that needs it.
        #
        # The question is therefore not "is there a ramp" but "does
        # that ramp explain what is drawn". Ask the real seeding code
        # rather than reproducing its sampling rule here: a
        # reimplementation would agree with itself and not with the
        # map. Equal means the ramp is the style and the row should go
        # on reading its name; different means the colours are the
        # style and the row reads Custom.
        try:
          from_ramp = bridge.make_categorized_renderer(
            layer, field, named, False, None, flipped)
          expected = {str(c.value()): c.symbol().color().name()
                      for c in from_ramp.categories()}
        except Exception:
          expected = None
      else:
        expected = None

      # Recover only the colours the ramp does NOT explain. Recording
      # all of them would be wrong in both directions: an element
      # coloured by an ordinary ramp would come back reading Custom,
      # and an element with ONE hand-picked colour would come back
      # owning five, so the record would stop meaning "what the user
      # chose" and start meaning "what is currently drawn".
      recovered = {}
      for value, colour in pairs:
        # the catch-all category carries no value; it is the one the
        # editor exposes under bridge.NO_DATA_KEY
        blank = value is None or str(value) in ("", "NULL")
        if blank:
          continue
        if expected is not None and expected.get(str(value)) == colour:
          continue
        recovered[str(value)] = colour
      if recovered:
        self._category_colours.setdefault(tile_id, {})[field] = recovered
      return
    try:
      # hold the list while it is read: a range object from ranges()
      # is a temporary, and a symbol pointer off a dead one segfaults
      # (the lesson the constant-column fix paid for)
      bands = [(r.symbol().color().name()) for r in renderer.ranges()]
    except Exception:
      return
    if not bands:
      return

    # The class count, but only where the spinner could hold it. Fifty
    # bands is Quant: Unclassed, whose count is fixed by the scheme
    # rather than chosen, and forcing 50 into a 2..20 spinner would
    # clamp to 20 and quietly describe a different map.
    if 2 <= len(bands) <= 20 and tile_id not in self._class_counts:
      self._class_counts[tile_id] = len(bands)

    try:
      field = renderer.classAttribute()
    except Exception:
      return
    if not field:
      return
    if self._quant_colours.get(tile_id, {}).get(field):
      return          # the user has picks of their own; do not touch

    # A NAMED RAMP IS NOT PROOF THAT THE RAMP DECIDES THE COLOURS, and
    # this half went on believing it was. The categorized branch above
    # was corrected on 2026-08-13 and its graduated twin, forty lines
    # away, was never revisited: `if named: return` threw away a class
    # a user had recoloured in QGIS's styling panel, in any session
    # where the plugin dialog was not open to hear `rendererChanged`.
    # Reopen the project, press Generate, and the colour was gone --
    # while the categorized element beside it survived the identical
    # journey. Measured 2026-08-16: #abcdef held through the reopen and
    # reverted to #e32f27 on the next run.
    #
    # So ask the real seeding code what the ramp WOULD draw, exactly as
    # the categorized branch does. Reimplementing the sampling here
    # would agree with itself rather than with the map.
    expected = None
    if named:
      # The SCHEME is deliberately absent from this question. A
      # scheme decides where the breaks fall; the colours are the
      # ramp sampled across however many classes there are, so
      # asking for the colours needs the ramp, the reverse flag, the
      # count and the display window and nothing else. Reaching for
      # make_graduated_renderer here would have meant inventing a
      # scheme to pass it -- and it reclassifies, so on a column
      # with few distinct values it can return FEWER classes than
      # the layer draws, which would read as colours the ramp does
      # not explain and recover the lot.
      expected = bridge.quant_class_colours(
        named, flipped, len(bands),
        tuple(self._ramp_ranges.get(tile_id, (0, 100))))
      if len(expected) != len(bands):
        expected = None          # cannot say; do not guess

    # Recover only the colours the ramp does NOT explain, for the same
    # reason the categorized branch gives: recording all of them would
    # make the record mean "what is drawn" rather than "what the user
    # chose", so an ordinary ramp would come back reading Custom.
    recovered = {}
    for index, colour in enumerate(bands):
      if expected is not None and index < len(expected) \
          and expected[index] == colour:
        continue
      recovered[str(index)] = colour
    if recovered and (expected is not None or not named):
      self._quant_colours.setdefault(tile_id, {})[field] = recovered

  def _a_kept_renderer_still_draws_this(self, renderer, assignment):
    """Can a renderer kept over an unreadable file still draw this element?

    Args:
      renderer: the renderer the element's PREVIOUS layer was drawing
        with, or None when there was no previous layer.
      assignment: the element's row as `_assignments` reports it, so
        `var` is the column the element draws NOW.

    Returns:
      True when that renderer can still paint this element, and False
      when it cannot -- in which case the caller seeds a fresh one
      rather than carrying this one across.

    WHY THIS IS ASKED OF THE RENDERER RATHER THAN OF WHAT CHANGED.
    Keeping the colours over a class source that has gone is right,
    and it stops being right the moment the element changes COLUMN: a
    renderer classed on `landcover` re-attached to an element now
    drawing `v1` puts every tile outside every class, so the map falls
    to the catch-all and reads as a solid sheet of grey. The element's
    layer is rebuilt at a landing and carries the identifiers plus the
    variable it draws (ruling 6, 2026-08-25), so the old column is not
    merely unused -- it is absent, and the renderer names a field the
    layer does not have. Measured 2026-08-27: classed on 'landcover'
    against fields ['tile_id', 'prototile_id', 'v1'].
    The neighbouring arm above asks the same question as a DELTA, off
    the previous signature. This one asks what the state can answer at
    any moment, which is the rule that ended the adoption family
    (attribution beats delta, 2026-08-26): a renderer that names a
    column is answerable whether or not we hold a signature for the
    row, so an adopted group -- which deliberately holds none -- is
    covered too.
    A SINGLE SYMBOL PAINTS EVERYTHING, whatever the values, which is
    what somebody usually leaves in Layer Properties; it names no
    field and so is never refused here. That is the same reading of
    "no categories covers everything" the carried-renderer rule
    already takes, and refusing it would throw away the very styling
    the carry exists to preserve.
    """
    if renderer is None:
      return False
    ask = getattr(renderer, "classAttribute", None)
    if ask is None:
      return True
    classed_on = ask()
    if not classed_on:
      return True
    return classed_on == (assignment.get("var") or "")

  def _own_the_colours_of_an_unreadable_source(self, layer, assignment):
    """Record what a kept renderer draws, because its file has gone.

    Args:
      layer: the element's layer, already wearing the renderer kept
        because its class-source file could not be read.
      assignment: that element's row as `_assignments` reports it.

    Returns:
      None. Writes each category's colour into the element's own
      record for its current field, and notes in
      `_kept_for_unreadable` that it was written HERE rather than
      chosen, so a file that can be read again takes the question
      back. A value the element already holds a colour for is left
      alone: that one is somebody's.

    WHY THE RECORD RATHER THAN THE RENDERER. Keeping the renderer is
    what stops the map repainting on the run in front of us; it is not
    what keeps the colours. The record is what the next run, the next
    restyle and the next reopen read, so colours held only on a
    renderer survive exactly until one of those and the element then
    falls back to automatic ones with nothing said. A missing file is
    a reason to stop consulting the file, not a reason to repaint
    somebody's map, and that has been the settled answer since the
    case was first tested.

    AND THEY ARE NOT PICKS FOREVER, which is the half round nine got
    right and this one must not undo: recorded colours that outrank a
    template mean restoring an edited scheme file changes nothing.
    The shadow record is what tells the two apart; its twin,
    `_release_colours_kept_for_an_unreadable_source`, hands the
    question back. (Maintainer's ruling, 2026-08-26, on the two
    registered tests that had come to demand opposite things.)
    """
    field = assignment.get("var")
    if not field or assignment.get("mode") != "Categorized":
      return
    # A DEFERRING ELEMENT IS NOBODY'S TO RECORD. Deferral means the
    # plugin has stopped deciding this element's symbology, and what
    # sits on the layer then is the dock's work rather than a scheme
    # file's -- recording it would make the plugin the author of
    # somebody else's colours, which is the same fault as adopting a
    # carry.
    if assignment.get("mode_raw") == self.DEFERRING:
      return
    renderer = layer.renderer() if layer is not None else None
    ask = getattr(renderer, "categories", None)
    if ask is None:
      return
    # NO SECOND GUARD HERE, AND THE MEASUREMENT IS THE REASON.
    # A renderer classed on a column the element no longer draws would
    # file that column's value strings under this one, so this site
    # was given the same question as the landing arm that decides the
    # carry. Audited per assertion on 2026-08-27 and measured
    # UNREACHABLE: with the landing arm in place the rebuilt layer
    # always wears a renderer classed on the field the row shows, and
    # with the arm reverted AND the table trim disabled the stale
    # column is still absent, because a re-tile rebuilds the frame
    # from the source. A guard that cannot fire reads as protection
    # while guarding nothing, and this project has deleted one before
    # for the same reason (ledger row 34, 2026-08-20).
    # WHAT WOULD REOPEN IT: an element keeping a renderer across a
    # change of column by any route that does not rebuild its layer.
    # There is none today; a restyle cannot, because changing the
    # mapped variable is a geometry change.
    # BOUND FIRST. A temporary list from a QGIS getter frees its
    # contents, so `categories()[0].symbol()` reads released memory --
    # once a segfault here, once a plausible wrong colour.
    categories = ask()
    tile_id = str(assignment.get("id"))
    record = self._category_colours.setdefault(tile_id, {}).setdefault(
      field, {})
    shadow = self._kept_for_unreadable.setdefault(tile_id, {}).setdefault(
      field, {})
    for category in categories:
      symbol = category.symbol()
      if symbol is None:
        continue
      value = category.value()
      # keyed as every other record here keys them, catch-all included
      key = bridge.NO_DATA_KEY if value is None else str(value)
      if key in record:
        continue
      colour = symbol.color().name()
      record[key] = colour
      shadow[key] = colour
    if shadow:
      _dump("KEPT", tile_id, field, "held=", len(shadow))

  def _release_colours_kept_for_an_unreadable_source(self, assignment):
    """Give the colours back to a class source that can be read again.

    Args:
      assignment: the element's row as `_assignments` reports it.

    Returns:
      None. Drops the entries this element's record only holds because
      its file had gone -- and only those still wearing the colour
      that was kept, since a colour the user has changed since is
      theirs and stays.

    This is the second half of the ruling above: the map keeps its
    colours while the file is unreadable, and the file governs again
    the moment it can be read. Without it, restoring an edited scheme
    would change nothing on the map and the control would look broken.
    """
    field = assignment.get("var")
    if not field:
      return
    tile_id = str(assignment.get("id"))
    for_element = self._kept_for_unreadable.get(tile_id)
    if not for_element:
      return
    shadow = for_element.pop(field, None)
    if not shadow:
      return
    record = (self._category_colours.get(tile_id) or {}).get(field) or {}
    given_back = 0
    for key, colour in shadow.items():
      if record.get(key) == colour:
        record.pop(key, None)
        given_back += 1
    if given_back:
      _dump("KEPT", tile_id, field, "released=", given_back)

  def _clear_category_colours(self, tile_id, because):
    """Forget an element's hand-picked colours for its current field.

    Args:
      tile_id: the element.
      because: what the user just did, named in the notice ("a new
        colour ramp", "an imported class source").

    Returns:
      None. Says so when anything was actually discarded, and stays
      quiet otherwise.

    Choosing a ramp or importing a QML names a new source of truth for
    this element's colours, so the hand-picked ones go. That is the
    settled rule and it makes the ramp control mean what it says, but
    it does throw away deliberate work -- so it is not done silently.
    Only the CURRENT field is cleared: another variable's colours are
    still there if the element is switched back to it.
    """
    for_element = self._category_colours.get(tile_id)
    if not for_element:
      return
    var_combo = None
    for row in range(self.table.rowCount()):
      item = self.table.item(row, 0)
      if item is not None and item.text() == tile_id:
        var_combo = self.table.cellWidget(row, 1)
        break
    field = var_combo.currentText() if var_combo else None
    if not field or field == "---":
      return
    discarded = for_element.pop(field, None)
    if not discarded:
      return
    self._report_quietly(
      f"Choosing {because} for element '{tile_id}' discarded "
      f"{len(discarded)} colour(s) you had picked by hand for "
      f"'{field}'.")

  def _row_for_element(self, tile_id):
    """The table row currently carrying one element, or None.

    Args:
      tile_id: the element to find.

    Returns:
      The row index, or None mid-rebuild. Rows are looked up fresh
      every time because rebuilds recreate them; nothing may cache a
      row number against an element.
    """
    for row in range(self.table.rowCount()):
      item = self.table.item(row, 0)
      if item is not None and item.text() == tile_id:
        return row
    return None

  def _assignment_for(self, tile_id):
    """One element's current assignment dict, or None.

    Args:
      tile_id: the element to find, as it appears in column 0.

    Returns:
      Its dict from ``_assignments()``, read FRESH -- the table is the
      only record, and a rebuild replaces every row -- or None when no
      row carries that element, which happens mid-rebuild and after
      the design has changed under a handler that outlived it. Every
      caller must handle None; none of them may cache the result.

    Why this exists as a method rather than nine copies of one
    generator expression. It was nine copies, and the comparison
    inside them is exactly the kind of thing that goes wrong
    silently: get it wrong and the lookup finds a DIFFERENT element,
    or none at all on a one-element map, and the caller then stamps a
    signature against the wrong id or repaints a window with another
    element's colours. Nothing raises either way. Automatic mutants
    landed on three of the nine copies and every one survived, and
    the three faults were separately invisible until a mutant
    happened to pick that particular copy -- so the copies were not
    nine chances to catch the fault, they were nine places for it to
    hide. Collapsed here, one mutation does the work of nine.
    (2026-08-12.)
    """
    return next((a for a in self._assignments(only=tile_id)
                 if a["id"] == tile_id), None)

  def _clear_quant_customization(self, tile_id, because,
                                 reset_range=True):
    """Forget an element's positional class colours, and perhaps its
    display range.

    Args:
      tile_id: the element.
      because: what the user just did, named in the notice ("a new
        colour ramp", "a new class count", "a new display range").
      reset_range: also restore the Ramp Display Range to the whole
        ramp. True only for a ramp choice -- "until reselected anew"
        is the settled rule -- since a scheme or class-count change
        reclassifies the data without saying anything about the ramp.

    Returns:
      None. Says so when anything was actually discarded, quiet
      otherwise. The picks die whenever the ramp is asked anew to
      decide the colours (settled 2026-08-09); only the CURRENT
      field's picks go, since another variable's are still keyed
      under their own name.
    """
    row = self._row_for_element(tile_id)
    var_combo = self.table.cellWidget(row, 1) if row is not None else None
    field = var_combo.currentText() if var_combo else None
    discarded = None
    if field and field != "---":
      # THE ABSENCE COLOURS SURVIVE. Reclassifying kills the
      # POSITIONAL picks -- a colour chosen for class 3 of 5 means
      # nothing on a ladder of 7 -- but the catch-all and infinity
      # picks name kinds of ABSENCE, which a class count says nothing
      # about, and they live in this same dict under non-digit keys
      # only since 2026-08-15, after the destruction rule was written.
      # (Maintainer's ruling, 2026-08-26, the same logic as the
      # Reverse mirror's.) The notice counts only what actually died.
      whole = self._quant_colours.get(tile_id, {}).pop(field, None)
      if whole:
        kept = {key: colour for key, colour in whole.items()
                if not key.isdigit()}
        discarded = {key: colour for key, colour in whole.items()
                     if key.isdigit()}
        if kept:
          self._quant_colours.setdefault(tile_id, {})[field] = kept
    had_window = tuple(
      self._ramp_ranges.get(tile_id, (0, 100))) != (0, 100)
    if reset_range:
      self._ramp_ranges.pop(tile_id, None)
    self._custom_swatch_cache.pop(tile_id, None)
    if discarded:
      self._report_quietly(
        f"Choosing {because} for element '{tile_id}' discarded "
        f"{len(discarded)} class colour(s) you had picked by hand "
        f"for '{field}'.")
    elif reset_range and had_window:
      self._report_quietly(
        f"Choosing {because} for element '{tile_id}' restored the "
        f"ramp's full display range.")

  def _mirror_quant_customization(self, tile_id):
    """Carry an element's quant customization through a Reverse flip.

    Args:
      tile_id: the element whose Reverse switch was just toggled.

    Returns:
      None. The display window mirrors (lo, hi -> 100-hi, 100-lo), so
      it keeps showing the same segment of colour run the other way,
      and the positional picks swap ends (class i -> k-1-i on k
      classes): a colour picked for the old class 2 of 7 lands on the
      new class 5. Reversing twice therefore restores everything
      exactly -- the involution the tests pin. (Settled 2026-08-09:
      Reverse carries the customization along rather than destroying
      it.)
    """
    row = self._row_for_element(tile_id)
    if row is None or self._row_mode(row) != "Graduated":
      return
    lo, hi = self._ramp_ranges.get(tile_id, (0, 100))
    if (lo, hi) != (0, 100):
      self._ramp_ranges[tile_id] = (100 - hi, 100 - lo)
    var_combo = self.table.cellWidget(row, 1)
    field = var_combo.currentText() if var_combo else None
    picks = self._quant_colours.get(tile_id, {}).get(field or "")
    if picks:
      k_spin = self.table.cellWidget(row, 3)
      count = int(k_spin.value()) if k_spin is not None else 0
      if count > 0:
        # POSITIONAL picks mirror; the ABSENCE picks do not move.
        # Since 2026-08-15 the catch-all and infinity colours live in
        # this same dict under non-digit keys, and rebuilding it from
        # digits alone destroyed a hand-picked No data colour on one
        # Reverse click -- silently, against the rule that Reverse
        # CARRIES the customization. A key that is not a class index
        # has no mirror image and simply comes along. Found by the
        # editor hunt of 2026-08-26.
        self._quant_colours[tile_id][field] = {
          **{index: colour for index, colour in picks.items()
             if not index.isdigit()},
          **{str(count - 1 - int(index)): colour
             for index, colour in picks.items()
             if index.isdigit() and int(index) < count}}
    self._custom_swatch_cache.pop(tile_id, None)

  def _current_category_colours(self, assignment):
    """What each value of a categorical element draws in right now.

    Args:
      assignment: one dict from ``_assignments()``, already known to
        be Categorized with a variable.

    Returns:
      ({value: "#rrggbb"}, [values in class order]) with
      bridge.NO_DATA_KEY last for the catch-all, or (None, None) when
      the region layer or its field has gone.

    Built by asking bridge for the SAME renderer the map would get,
    against the region layer, and reading the colours back out of it.
    Re-deriving the sampling here instead would mean a second copy of
    a rule this project has already got wrong once -- an earlier
    hand-derivation used round() where matplotlib uses int(), and
    painted the middle category the wrong colour. One implementation
    means the editor cannot disagree with the map.
    """
    layer = self.layer_combo.currentLayer()
    if layer is None or assignment["var"] not in \
        [f.name() for f in layer.fields()]:
      return None, None
    template = self._template_for(assignment.get("class_source"))
    renderer = bridge.make_categorized_renderer(
      layer, assignment["var"], assignment["ramp"],
      assignment.get("outline", False), template,
      assignment.get("reverse", False),
      assignment.get("category_colours"))
    colours, order = {}, []
    for category in renderer.categories():
      value = category.value()
      key = bridge.NO_DATA_KEY if value is None else str(value)
      colours[key] = category.symbol().color().name()
      order.append(key)
    return colours, order

  def _current_graduated_classes(self, assignment):
    """The classes a graduated element draws right now.

    Args:
      assignment: one dict from ``_assignments()``, already known to
        be Graduated with a variable.

    Returns:
      [(lower, upper, "#rrggbb"), ...] in class order, or [] when no
      layer can answer. Built by asking bridge for the SAME renderer
      the map would get -- range window and positional picks included
      -- so the editor and the swatch cannot disagree with the map.
      Classified against the element's own output layer when one
      exists (its breaks are the map's breaks); against the region
      layer otherwise, which is what lets the editor open before
      anything is generated, at the price the categorical editor
      already accepted: the pre-generation preview may differ
      slightly from the tiled result.
    """
    from qgis.core import QgsGraduatedSymbolRenderer
    project = QgsProject.instance()
    layer = None
    lid = self._element_layer_ids.get(assignment["id"])
    if lid:
      candidate = project.mapLayer(lid)
      if candidate is not None and assignment["var"] in \
          [f.name() for f in candidate.fields()]:
        layer = candidate
    if layer is None:
      layer = self.layer_combo.currentLayer()
    if layer is None or assignment["var"] not in \
        [f.name() for f in layer.fields()]:
      return []
    renderer = bridge.make_graduated_renderer(
      layer, assignment["var"], assignment["ramp"],
      assignment.get("scheme", "Quantiles"), assignment.get("k", 5),
      assignment.get("outline", False),
      assignment.get("reverse", False),
      assignment.get("range_bounds", (0, 100)),
      assignment.get("quant_colours"),
      # the same values the MAP is classified from, or this preview
      # of the row's colours would predict a map drawn from a
      # different sample -- which is the disagreement
      # test_the_preview_agrees_with_the_map_it_predicts hunts
      self._classification_values(assignment["var"]),
      assignment.get("pinned"))
    # iterate the list while it is bound to the loop: range objects
    # from ranges() are temporaries, and a symbol pointer read off a
    # dead one segfaults (the lesson the constant-column fix paid for)
    return [(r.lowerValue(), r.upperValue(), r.symbol().color().name())
            for r in renderer.ranges()]

  def _remember_painted_ladder(self, layer, tile_id):
    """Record the graduated ladder this layer is now wearing as OURS.

    Args:
      layer: the element output layer, just painted by the plugin (or
        just met, on adoption).
      tile_id: the element it carries.

    THE FIELD COMES OFF THE RENDERER, not off the row, and that is
    deliberate: the ladder belongs to whatever column the renderer
    actually classifies, the row can be mid-follow, and adoption has
    no row to consult at all. One source, so the two cannot disagree.

    Returns:
      None. Writes ``_painted_ladders[tile_id][field]`` as
      ``[(lower, upper, "#rrggbb"), ...]`` read straight off the
      layer's renderer, which is the only honest source: what we
      MEANT to paint and what QGIS actually holds can differ wherever
      a classifier reduced, snapped or collapsed something.

    CALL THIS WHEREVER THE PLUGIN PAINTS, and nowhere else. The three
    places are both ``seed_renderer`` sites and group adoption; a
    fourth painting path added later must call it too, or that
    element's dock edits will all read as unattributable and be
    declined. Never call it from ``_row_follows_the_renderer``: the
    follow runs BEFORE attribution and moves the row rather than the
    layer, so refreshing there would record whatever the dock left as
    our own and silently disarm the whole mechanism.
    """
    # imported here rather than at module scope, as its two siblings
    # in this file already are
    from qgis.core import (QgsCategorizedSymbolRenderer,
                           QgsGraduatedSymbolRenderer)
    if layer is None or not tile_id:
      return
    renderer = layer.renderer()
    # THE CATEGORICAL TWIN RECORDS TOO (2026-08-26). The categorized
    # walk used to attribute by DELTA -- adopt whatever differs from
    # what the plugin would seed NOW -- and a landing that keeps a
    # renderer over an unreadable class source made that delta lie:
    # "expected" fell back to automatic colours while the map
    # honestly wore the template, and the template's own colours were
    # adopted as a person's picks. Attribution by record is the
    # question the state can answer at any moment, which is the same
    # argument that built `_painted_ladders`.
    if isinstance(renderer, QgsCategorizedSymbolRenderer):
      cat_field = renderer.classAttribute()
      if cat_field:
        cats = renderer.categories()
        self._painted_categories.setdefault(str(tile_id), {})[cat_field] = {
          str(c.value()): c.symbol().color().name()
          for c in cats if c.symbol()}
      return
    if not isinstance(renderer, QgsGraduatedSymbolRenderer):
      return
    field = renderer.classAttribute()
    if not field:
      return
    # Bound to a name before it is subscripted: a range reached
    # through a temporary is freed under you, which this project has
    # now paid for three times -- most recently in the very probe
    # written to measure this defect.
    rows = renderer.ranges()
    ladder = [(one.lowerValue(), one.upperValue(),
               one.symbol().color().name().lower()) for one in rows]
    if ladder:
      self._painted_ladders.setdefault(str(tile_id), {})[field] = ladder

  def _colour_is_ours(self, tile_id, field, lower, upper, colour):
    """Did the PLUGIN put this colour on this class, or did a person?

    Args:
      tile_id: the element being judged.
      field: the column its ladder classifies.
      lower: the class's lower bound, as the layer holds it now.
      upper: its upper bound.
      colour: the colour it is wearing now, "#rrggbb".

    Returns:
      True when this colour is one the plugin painted, False when it
      is a person's, and None when there is NO RECORD of this
      element's ladder at all -- which is not the same answer and must
      not be collapsed into either. A caller meeting None knows only
      that it cannot say.

    TWO QUESTIONS, and both are needed. The first is by BOUNDS: this
    class is one we painted and still wears the colour we gave it.
    That is exact -- measured 2026-08-20, a class surviving an insert
    keeps its bounds bit for bit -- and it is what recognises a class
    QGIS merely renumbered.

    The second is by VALUE: the colour is one the stored ladder used
    somewhere. That is what carries a RETYPE, where every bound moves
    at once and no class can be matched by position, while the colours
    on them are still every one of them ours.

    THE ACCEPTED RESIDUAL (maintainer's decision, 2026-08-20): a
    person who deliberately picks a colour the ladder already uses
    elsewhere -- to make two classes read as one -- is judged to be
    us, and their pick is declined. It is declined OUT LOUD, by the
    notice the caller composes, rather than silently; and the colour
    editor remains the unambiguous way to say it. Widening this to
    catch that case would mean giving up the retype, which is the far
    commoner act.
    """
    known = (self._painted_ladders.get(tile_id) or {}).get(field)
    if not known:
      return None
    here = colour.lower()
    # EVERY CLASS AT THESE BOUNDS, not the first one found. A ladder
    # may hold SEVERAL classes with identical bounds and this project
    # meets them constantly: a constant column, a tied column, and
    # `{1, 5, 9}` at k=5, which returns three degenerate ranges. QGIS's
    # own `addClass` then inserts a (0.0, 0.0) class, so on a fixture
    # whose first real class is also (0.0, 0.0) the two collide.
    #
    # Measured 2026-08-20 against this very function's first draft,
    # which returned on the first match: the plugin's own #fff5f0 was
    # compared against the placeholder grey sharing its bounds, judged
    # changed, and adopted as a hand-pick. Four passing tests did not
    # see it; driving the product and printing the store did.
    at_these_bounds = [was for low, high, was in known
                       if abs(low - lower) < 1e-9 and abs(high - upper) < 1e-9]
    if at_these_bounds:
      return here in at_these_bounds
    # No class of ours ever had these bounds, so every bound has moved
    # -- which is what a RETYPE looks like. Fall back to asking whether
    # the colour is one we used anywhere on this ladder.
    return any(was == here for _low, _high, was in known)

  def _custom_swatch_for(self, tile_id, field):
    """The swatch for one element's Custom display.

    Args:
      tile_id: the element whose ramp cell is reading Custom.
      field: its current variable, named in the cache key so a field
        switch cannot serve another field's colours.

    Returns:
      A QIcon of the first few colours the element actually draws in,
      taken from the SAME renderer the map gets (via
      _current_category_colours or _current_graduated_classes, so the
      swatch cannot disagree with the map). Rebuilt whenever anything
      deciding those colours changes -- the cache key is the pick
      set, the ramp, its direction, and the field, plus the class
      source on a categorized row or the scheme, class count and
      display window on a graduated one -- and reused otherwise,
      because building it constructs a real renderer and _sync_row
      runs on every control change.
    """
    # A DEFERRING element's swatch comes off its LAYER, because the
    # plugin no longer decides those colours and the row must still
    # describe the map. `renderer_fill_colours` reads the renderer
    # rather than the ramp -- which it was already written to do --
    # and falls through to the base class's own `symbols()` for the
    # rule-based and other renderers that deferring consists of.
    # Refreshed by _refresh_deferring_rows on every styleChanged, so
    # it follows the styling panel (settled with the maintainer,
    # 2026-08-15).
    if self._element_is_deferring(tile_id):
      layer = QgsProject.instance().mapLayer(
        self._element_layer_ids.get(tile_id))
      renderer = layer.renderer() if layer is not None else None
      # ...unless the colour is DATA-DEFINED, where `symbols()` hands
      # back the BASE symbol rather than what any feature is painted:
      # a swatch claiming one colour for a map drawing hundreds is the
      # plugin describing a map it will not draw. An unknown is drawn
      # as an unknown rather than guessed at.
      if bridge.renderer_has_data_defined_fill(renderer):
        return _custom_swatch_icon([])
      shown = ["#%02x%02x%02x" % rgb
               for rgb in bridge.renderer_fill_colours(layer)[:8]] \
        if layer is not None else []
      return _custom_swatch_icon(shown)
    assignment = self._assignment_for(tile_id)
    if assignment is None:
      return _custom_swatch_icon([])
    if assignment["mode"] == "Graduated":
      # positional picks and the display window are what decide a
      # graduated row's colours, so they are the cache key here
      picks = assignment.get("quant_colours") or {}
      pinned = assignment.get("pinned") or {}
      # the pins are IN the key: without them the box would be drawn
      # once and then cached past every later pin and unpin, which is
      # a swatch quietly describing a map that has moved
      key = (field, assignment.get("ramp"), assignment.get("reverse"),
             assignment.get("scheme"), assignment.get("k"),
             tuple(assignment.get("range_bounds", (0, 100))),
             tuple(sorted(picks.items())),
             tuple(sorted((k, tuple(v) if isinstance(v, list) else v)
                          for k, v in pinned.items())),
             # The data's own fingerprint. Its stated reason left with
             # the swatch hatching on 2026-08-17 -- an edit that
             # emptied a class had to take the mark off, and one that
             # filled it had to put it back -- and nothing else in
             # this swatch depends on the data, since a graduated
             # row's colours come from the ramp, the count and the
             # window. So it may now be dead weight on a path that
             # runs per row per rebuild, which is exactly the kind of
             # thing the responsiveness entry in ROADMAP.md exists to
             # MEASURE rather than reason about. Kept until it is
             # measured; delete it if that measurement says so.
             self._layer_fingerprint())
      cached = self._custom_swatch_cache.get(tile_id)
      # THE CACHE IS THE ONE THING BETWEEN A CORRECT RECORD AND A
      # STALE CELL, so it says which it did. A recolour made in QGIS
      # was reported twice as reaching the map and not the window,
      # while the CLASSES cell beside it updated instantly -- and both
      # are written by `_sync_row` in one pass, so the hook fired and
      # the row re-synced. If the key has not moved, this hands back
      # yesterday's picture for good. Five reproductions failed
      # because every path they drove popped this cache.
      _dump("SWATCH", tile_id,
            "hit" if (cached is not None and cached[0] == key) else "miss",
            "picks=", picks, "pinned=", pinned)
      if cached is not None and cached[0] == key:
        return cached[1]
      shades = [colour for _lo, _hi, colour
                in self._current_graduated_classes(assignment)]
      if assignment.get("scheme") == "Unclassed" and len(shades) > 8:
        # fifty slivers would all land in the first eight stripes;
        # sample the window evenly instead, so the swatch shows the
        # whole of what the range selected
        step = (len(shades) - 1) / 7
        shades = [shades[round(j * step)] for j in range(8)]
      # ALL FOUR ENDS, EACH ON ITS OWN EDGE. This read `low` and
      # `high` alone until 2026-08-19 and the record had held four
      # ends since that morning, so a floor or a CEILING somebody had
      # set showed no mark at all -- reported by the maintainer, who
      # had pinned the upper class's upper bound and found the swatch
      # silent about it. The record grew and this site was not among
      # the ones grepped, which is the shape ledger row 21 already
      # names.
      #
      # The mapping is the ladder's own: the first class's LEFT edge
      # is the floor and its RIGHT edge is the low pin; the last
      # class's LEFT edge is the high pin and its RIGHT edge is the
      # ceiling. On Unclassed the fifty classes were sampled down to
      # eight stripes just above, so an edge reads as "the low end"
      # rather than literally class 0 of fifty -- which is what the
      # pin means there anyway.
      boxed = [pair for pair, end in (((0, "left"), "floor"),
                                      ((0, "right"), "low"),
                                      ((-1, "left"), "high"),
                                      ((-1, "right"), "ceiling"))
               if pinned.get(end) is not None]
      icon = _custom_swatch_icon(shades, boxed)
      self._custom_swatch_cache[tile_id] = (key, icon)
      return icon
    picks = assignment.get("category_colours") or {}
    key = (field, assignment.get("ramp"), assignment.get("reverse"),
           assignment.get("class_source"),
           tuple(sorted(picks.items())))
    cached = self._custom_swatch_cache.get(tile_id)
    if cached is not None and cached[0] == key:
      return cached[1]
    colours, order = self._current_category_colours(assignment)
    icon = _custom_swatch_icon(
      [colours[value] for value in order] if order else [])
    self._custom_swatch_cache[tile_id] = (key, icon)
    return icon

  def _watch_element_layer(self, layer, tile_id):
    """Follow QGIS-side symbology edits on one element output layer.

    Args:
      layer: the freshly created or adopted output layer.
      tile_id: the element it carries.

    Returns:
      None. Connects the layer's ``styleChanged`` signal -- which
      QGIS emits both when the styling dock installs a new renderer
      (setRenderer) and when a symbol is edited in place -- to
      _on_layer_style_edited. The connection dies with the layer, and
      element layers are recreated every run, so there is nothing to
      disconnect by hand. The layer is looked up again by id when the
      signal fires, because reacting through a captured wrapper whose
      C++ object died is a crash.
    """
    layer.styleChanged.connect(
      lambda lid=layer.id(), tid=str(tile_id):
        self._on_style_signal(lid, tid))
    # ...AND repaintRequested BESIDE IT, because styleChanged only
    # fires on `setRenderer` and the styling dock does not always call
    # that. Measured on QGIS 4.0.3 (2026-08-20, plugin out of the
    # way): recolouring a class's symbol IN PLACE emits neither
    # styleChanged nor rendererChanged -- and the dock then calls
    # `triggerRepaint()`, which is the only way the canvas learns, and
    # THAT emits repaintRequested. So the repaint is the one audible
    # trace of an in-place edit. A maintainer recoloured a class,
    # watched the map follow and the plugin sit still, three times
    # over two days (ledger row 28); adding a class reached us because
    # that action installs a whole renderer, which is what made the
    # two look inconsistent.
    #
    # The REGION layer's repaintRequested stays deliberately
    # unconnected -- there a repaint must not cause a re-tile, and
    # that older rule is about that layer. Here the reaction is
    # reading colours off a renderer, and the handler this feeds is
    # idempotent (it adopts only divergence) and already gated against
    # our own seeding (`_applying_style`) and runs in flight
    # (`_task`). DEBOUNCED, because a single data edit fires it twice
    # and a drag in the dock can fire it per tick; the set coalesces
    # and the timer drains through the one handler everything else
    # uses.
    layer.repaintRequested.connect(
      lambda *args, lid=layer.id(), tid=str(tile_id):
        self._queue_repaint_reconcile(lid, tid))

  def _on_style_signal(self, layer_id, tile_id):
    """The styleChanged entry point, stamped so its echo is known.

    Args:
      layer_id: the element output layer whose style changed.
      tile_id: the element it carries.

    Returns:
      None. Records WHEN a real styleChanged arrived for this element
      and then runs the ordinary handler. The stamp exists for the
      repaint hook beside it: a `setRenderer` edit emits styleChanged
      AND asks for a repaint, so without it every heard edit was
      handled twice -- once now and once at the drain, by which time
      the row had already followed and the second pass adopted the
      displaced colours the first had rightly declined. Monotonic,
      because it is a duration; wall clock jumps with the machine.

      NOT STAMPED while the plugin itself is writing renderers or a
      run is landing: those signals are our own seeding, the handler
      below gates them out, and stamping them left the repaint hook
      deaf for a second after every landing.
    """
    if not self._applying_style and self._task is None:
      self._style_signal_at[str(tile_id)] = time.monotonic()
    self._on_layer_style_edited(layer_id, tile_id)

  def _queue_repaint_reconcile(self, layer_id, tile_id):
    """Note that an element layer asked to be repainted, and look later.

    Args:
      layer_id: the element output layer that fired repaintRequested.
      tile_id: the element it carries.

    Returns:
      None. Records the pair and (re)starts the 300 ms drain timer.
      Two kinds of repaint are dropped rather than queued. The
      plugin's OWN: `_applying_style` is true exactly while the
      dialog writes renderers, and queueing those would make every
      restyle read its own output back a moment later. And the ECHO
      of a heard edit: `setRenderer` emits styleChanged first and
      asks for a repaint after, so a repaint arriving within a second
      of a styleChanged for the same element is that edit's shadow,
      already handled with fresher context than any drain would have.
      What survives the two drops is precisely the in-place edit,
      which emits nothing else.

      The stamp is written only for an edit heard AT REST: the
      plugin's own seeding fires styleChanged too, and stamping those
      made this hook deaf for a second after every landing -- which is
      exactly when a test, or a quick hand, recolours.
    """
    if _dialog_is_gone(self) or _live_dialog() is not self:
      return
    if self._applying_style:
      _dump("REPAINT", tile_id, "own")
      return
    if time.monotonic() - self._style_signal_at.get(str(tile_id),
                                                    -1e9) < 1.0:
      _dump("REPAINT", tile_id, "echo")
      return
    _dump("REPAINT", tile_id, "queued")
    self._repaint_pending[str(tile_id)] = layer_id
    self._repaint_timer.start()

  def _drain_repaint_reconcile(self):
    """Reconcile every element whose layer asked for a repaint.

    Returns:
      None. Runs the one style-edit handler for each queued element,
      which follows the row, adopts divergent colours, and stamps --
      or defers, mid-run, exactly as a styleChanged arrival would.
      Each element is contained on its own: this runs from a Qt
      timer, where an exception is swallowed and would take the rest
      of the queue with it.

      AN ELEMENT WHOSE ROW HAS MOVED IS SKIPPED, and this is the
      guard that keeps the drain honest. The handler reads the layer
      as news and the row as the user's standing wishes; between a
      control change and the restyle that answers it, the layer is
      simply BEHIND, and reconciling then would adopt the plugin's
      own outgoing style as somebody's picks. The row's signature
      against `_last_signatures` -- what the layer was last seeded
      from -- is the record of who moved: equal means only the layer
      can have, which is exactly a dock edit.
    """
    if _dialog_is_gone(self) or _live_dialog() is not self:
      return
    pending, self._repaint_pending = self._repaint_pending, {}
    for tile_id, layer_id in pending.items():
      try:
        assignment = self._assignment_for(tile_id)
        if assignment is None:
          _dump("REPAINT", tile_id, "no-row")
          continue
        # ...AND AN ABSENT RECORD IS NOT A ROW THAT MOVED. This read
        # `!= self._last_signatures.get(tile_id)` until 2026-08-20,
        # so a MISSING entry -- `None`, never equal to any real
        # signature -- was read as "the row moved" and the element
        # was skipped for good. `_adopt_existing_group` leaves that
        # record EMPTY on purpose, saying so in its own docstring, on
        # the reasoning that the dialog cannot know which assignments
        # produced layers it has only just met. So every element of
        # every REOPENED project took this branch: the repaint door
        # was shut in exactly the session the same docstring promises
        # that "hand styling still survives as before", and an
        # in-place recolour was painted back to the ramp at the next
        # Generate. Found by a hunt aimed at this pair of doors the
        # day they were written.
        recorded = self._last_signatures.get(tile_id)
        if recorded is not None and self._signature(assignment) != recorded:
          # the ROW moved; a restyle is pending, not a dock edit
          _dump("REPAINT", tile_id, "row-moved")
          continue
        _dump("REPAINT", tile_id, "drain")
        self._on_layer_style_edited(layer_id, tile_id)
      except Exception:
        continue

  def _ramp_match(self, ramp, prefer=None):
    """Name a colour ramp, allowing for one that has been reversed.

    Args:
      ramp: a QgsColorRamp taken from a renderer -- one QGIS restored
        from a project file, or one somebody built in the styling
        dock -- or None.
      prefer: a ramp name to try FIRST in each pass, or None. The
        shipped palettes contain byte-identical twins ('gray' and
        'gist_gray', 'binary' and 'gist_yarg' -- equality measured in
        palettes.json, 2026-08-26), so a ramp can match several names
        equally and iteration order used to decide. A user who picked
        'gray' and pressed Apply in the styling dock with no change
        watched the row and the records silently rename it to
        'gist_gray' -- no pixel ever differs, and the label must not
        move under them (maintainer's ruling, 2026-08-26). Callers
        that hold the row's current choice pass it here.

    Returns:
      ``(name, reversed)``: the name under which this ramp appears in
      the ramp dropdown and whether it is that ramp run the other
      way, or ``(None, False)`` when nothing in the library draws it.
      Compared by the ramp's own serialized properties rather than by
      object identity, because both the dock and the project reader
      hand out clones.

    Why the reversed pass exists. Reversing produces a clone that
    matches no NAME in the library, so a project reopened with a
    reversed element used to come back reading Custom: the colours
    were preserved exactly, and the fact that they came from
    reversing a named ramp was not. The tick a user had set was
    simply gone, and `NOT_YET_RESTORED` in
    test_a_project_round_trip_changes_nothing_a_user_chose named it
    as the last thing a round trip lost.

    The two passes are ordered, and the order is the point: an exact
    match wins before any reversed one is tried, so a ramp that
    happens to equal its own reverse is reported unreversed rather
    than by whichever name the iteration reached first.
    """
    if ramp is None:
      return None, False
    try:
      wanted = (type(ramp).__name__, ramp.properties())
    except Exception:
      return None, False
    for flipped in (False, True):
      # the preferred name goes first WITHIN each pass, never across
      # them: an exact match must still win before any reversed one,
      # or a ramp equalling its own reverse would flip its tick
      names = ([prefer] + [n for n in self._ramp_names if n != prefer]
               if prefer in self._ramp_names else self._ramp_names)
      for name in names:
        candidate = bridge.get_ramp(name, flipped)
        if candidate is not None and \
            (type(candidate).__name__, candidate.properties()) == wanted:
          return name, flipped
    return None, False

  def _ramp_name_matching(self, ramp, prefer=None):
    """The QgsStyle name of a ramp drawn exactly as the library draws it.

    Args:
      ramp: a QgsColorRamp, or None.
      prefer: a name to win ties among byte-identical twins, passed
        straight through to `_ramp_match` -- the dock handlers hand in
        the row's current choice so an Apply with no change cannot
        rename it. Omitted, iteration order decides as before.

    Returns:
      The name under which an identical ramp appears in the ramp
      dropdown, or None when nothing matches OR when the match is a
      REVERSED clone.

    That last exclusion keeps this the question the styling-dock
    handlers actually ask, which is not "which ramp is this" but "is
    the layer wearing exactly what the dialog would seed from a name
    it can put in the combo". A reversed ramp is not, so those
    handlers go on adopting it as hand-picked colours -- the settled
    fallback, which preserves the map exactly and reads Custom.
    Reopening asks the other question and calls `_ramp_match`.
    """
    name, flipped = self._ramp_match(ramp, prefer=prefer)
    return None if flipped else name

  def _adopt_the_layers_opacity(self, layer_id, tile_id):
    """Read an element's opacity back off its layer, and show it.

    Args:
      layer_id: the output layer somebody has just restyled in QGIS.
      tile_id: the element it carries.

    Returns:
      None. Updates this element's opacity record and the table cell
      that displays it, and does nothing at all when the two already
      agree with the layer, so an ordinary recolour costs one
      comparison.

    BOTH STORES, because the cell is one. `_assignments` reads the
    SPIN BOX, so a record updated alone is written back over at the
    next rebuild -- the widget-is-a-store fault this project has paid
    for twice. The cell is set with its signals blocked, or setting it
    right would fire the handler that writes the spin's value into the
    record and undo what this just adopted.
    """
    layer = QgsProject.instance().mapLayer(layer_id)
    if layer is None:
      return
    try:
      wearing = max(0, min(100, round(layer.opacity() * 100)))
    except Exception:
      return
    if self._opacity_choices.get(tile_id) == wearing:
      return
    _dump("OPACITY", tile_id, "layer=", wearing,
          "dialog=", self._opacity_choices.get(tile_id, "-"))
    self._opacity_choices[tile_id] = wearing
    for row in range(self.table.rowCount()):
      cell = self.table.item(row, 0)
      if cell is None or cell.text() != tile_id:
        continue
      spin = self._row_opacity(row)
      if spin is not None and spin.value() != wearing:
        spin.blockSignals(True)
        spin.setValue(wearing)
        spin.blockSignals(False)
      break

  def _on_layer_style_edited(self, layer_id, tile_id):
    """React when someone restyles an element layer in QGIS itself.

    Args:
      layer_id: the output layer whose style changed.
      tile_id: the element it carries.

    Returns:
      None. The dialog is not modal to QGIS, so a user can open an
      element layer in the styling dock and recolour it while the
      dialog sits there naming a ramp that no longer decides the map
      -- the exact lie the Custom display exists to prevent. Two
      reactions, chosen by what the dock now holds (user decision,
      2026-08-09):

      * the renderer is a clean classify from a STANDARD ramp (its
        source ramp matches a named ramp, its colours are exactly
        what seeding from that ramp alone would give, and no imported
        class source is in force): the dialog follows -- the row's
        ramp combo moves to that name, which destroys any hand-picks
        through the ordinary handler, notice included;
      * anything else: the changed colours are ADOPTED as hand-picked
        choices for the current field, exactly as reopening a saved
        project adopts stamped colours. The cell reads Custom, the
        colours survive regeneration and travel into the project
        file, and choosing a ramp later destroys them with the
        existing notice rather than silently.

      Our own seeding is ignored twice over: while a run is landing
      its layers ``_task`` is still set (the run is not over until
      its layers exist), and the restyle fast path raises
      ``_applying_style``. Graduated renderers take the same two
      reactions through _graduated_layer_edited (positional picks,
      quantitative-family follows). Only single-symbol and unknown
      renderers are left alone: they survive through the signature
      rule, and the ramp cell makes no claim a recolour could turn
      into a lie.
    """
    _dump("HEARD", tile_id, "layer=", layer_id)
    if _dialog_is_gone(self):
      # the layer outlived this dialog and its lambda came
      # with it; there is nothing here to update
      _dump("DROP", tile_id, "gone")
      return
    from qgis.core import (QgsCategorizedSymbolRenderer,
                           QgsGraduatedSymbolRenderer)
    live = _live_dialog()
    if live is not None and live is not self:
      # a RETIRED instance's connections outlive its retirement,
      # because the layers do; without this gate both dialogs would
      # adopt the same dock edit and the user would be told twice
      _dump("DROP", tile_id, "retired")
      return
    # THE LAYER HAS MOVED, so it outranks any style picked in the
    # table earlier: whatever the user last said about this element,
    # they have just said something newer in QGIS. Dropping the claim
    # here is what lets `_refresh_deferring_rows` below move the row
    # to "Deferring to QGIS" -- without it a row whose style had ever
    # been picked by hand went on naming that style over a rule-based
    # map, and the next Generate reclaimed the element and painted
    # over the work. `_applying_style` is excluded because that is the
    # plugin writing the renderer rather than a person, and a run in
    # flight is not: a rule-based style pasted 250 ms into a run is
    # exactly the case `_add_output_layers` reads the live row for.
    if not self._applying_style \
        and self._element_layer_ids.get(tile_id) == layer_id:
      self._picked_back.discard(tile_id)
    # OPACITY IS QGIS'S OWN, AND A PERSON HAS JUST MOVED IT. Adoption
    # at reopen has read it off the layer since 2026-08-13, for the
    # reason written there: the dialog's copy can only disagree, and
    # `_add_output_layers` pushes that copy back, so the next restyle
    # -- any restyle, for any reason -- quietly undoes a choice still
    # visible in QGIS's own panel. The same is true WITHIN a session
    # and nothing read it: set 20% in Layer Properties and the layer,
    # its renderer and the file's saved style all said 20 while the
    # widget, the dialog's record, the group's record and the file's
    # record all said 100. One ramp change and a Generate put 100 back
    # on the map. Measured by the agreement sweep, 2026-08-27.
    # AT REST ONLY, like every other adoption here: not while the
    # dialog is writing renderers, not while a run is in flight, and
    # not while a landing is still being reconciled -- during any of
    # those what sits on the layer is nobody's decision.
    if not self._applying_style and self._task is None \
        and tile_id not in self._preserved_this_run:
      self._adopt_the_layers_opacity(layer_id, tile_id)
    if self._applying_style or self._task is not None:
      # THE ROW STILL LEARNS IT IS DEFERRING, even mid-run, and that
      # one line is the difference between a style surviving and being
      # destroyed.
      #
      # Adopting a dock edit while a tiling is in flight is genuinely
      # unsafe -- the run lands with the settings it was LAUNCHED with
      # and would overwrite whatever we did -- so this gate is right.
      # What it must not do is leave the TABLE ignorant, because the
      # landing consults the table: `_add_output_layers` reads "the row
      # names a style, the layer holds something the row cannot name"
      # as the user having TAKEN THE ELEMENT BACK, so `kept_by_hand` is
      # false and it re-seeds. `_finish_run`'s catch-up only revisits
      # elements already in `_preserved_this_run`, which this one never
      # joined.
      #
      # MEASURED 2026-08-17, confirmed four ways including rendered
      # pixels: paste a rule-based style onto an element 250 ms into a
      # run and it is gone when the run lands, with the only notice
      # being the tile count. The identical paste a second earlier or
      # later survives and is honoured for good. Bounded, too -- an
      # element ALREADY deferring survives, and an EXPRESSIBLE paste in
      # the same window survives; the deferral has to BEGIN inside it.
      #
      # `_refresh_deferring_rows` writes no renderer and starts no run.
      # It reads each layer and moves the chooser, which is exactly the
      # knowledge the landing is about to need.
      self._refresh_deferring_rows()
      _dump("DROP", tile_id, "applying_style=", self._applying_style,
            "task=", self._task is not None)
      return
    if self._element_layer_ids.get(tile_id) != layer_id:
      # a stale connection from a layer since replaced
      _dump("DROP", tile_id, "stale-layer row=",
            self._element_layer_ids.get(tile_id))
      return
    # ...and BEFORE the two colour reactions below, the question of
    # whether a row can still name what this layer holds. A change of
    # renderer TYPE is not a recolour, and putting it through the
    # colour branches adopted category picks onto a row still reading
    # Graduated. Settled 2026-08-15: where a row can express the new
    # renderer it follows, and where it cannot the element DEFERS.
    # ASKED OF THE ROW, not of the layer. The layer already holds the
    # new renderer by the time this signal arrives, so asking it
    # whether the element "was" deferring always answers yes and the
    # notice never fires -- measured while building this, 2026-08-15.
    # The row is the thing that has not caught up yet, which is
    # precisely what makes it the right witness to whether the user
    # has been told.
    was_deferring = any(
      self.table.item(row, 0) is not None
      and self.table.item(row, 0).text() == tile_id
      and self.table.cellWidget(row, 2) is not None
      and self.table.cellWidget(row, 2).currentText() == self.DEFERRING
      for row in range(self.table.rowCount()))
    layer_now = QgsProject.instance().mapLayer(layer_id)
    now_deferring = (layer_now is not None
                     and bridge.expressible_style(layer_now.renderer()) is None)
    # RECONCILED EITHER WAY, and the `if now_deferring` this used to
    # sit inside was the bug: a dock edit that goes BACK to something
    # a row can name left the row saying "Deferring to QGIS" with its
    # controls inert over a map the plugin could perfectly well
    # describe. The two directions are one question asked once.
    self._refresh_deferring_rows()
    if now_deferring:
      if not was_deferring:
        # ONE notice, when it begins (maintainer's decision). The
        # editor goes with it: every number in that window describes
        # the renderer that has just been replaced, and leaving it
        # open guarantees the user reads one of them.
        if self._open_editor is not None:
          self._open_editor.reject()
        self._report_quietly(
          f"Element '{tile_id}' is now styled in QGIS, so its colours "
          f"are set in the Layer Styling panel.")
      # THE PICTURE FOLLOWS EVEN THOUGH THE RECORDS DO NOT. Deferral
      # means the plugin stops deciding this element's SYMBOLOGY; it
      # has never meant the design view may go on showing a colour the
      # map does not contain. Until 2026-08-28 this exit returned in
      # front of every refresh, so an element restyled in the dock kept
      # the plugin's old colour in the preview for the rest of the
      # session and no later act healed it -- measured by rendering the
      # widget, zero pixels of what the map draws. The guard is about
      # deferral and the exit below it was about the picture, which is
      # this file's own standing shape.
      self._refresh_preview_colours()
      _dump("DROP", tile_id, "deferring")
      return
    layer = QgsProject.instance().mapLayer(layer_id)
    if layer is None:
      _dump("DROP", tile_id, "no-layer")
      return
    renderer = layer.renderer()
    # THE ROW FOLLOWS THE LAYER FIRST, and everything below then runs
    # against a row that agrees with the map about which field, which
    # style, how many classes and which ramp. Added 2026-08-17 on the
    # maintainer's ruling, answering the field report that a break
    # retyped in QGIS's Symbology panel -- or a whole style pasted
    # across four elements -- never reached the plugin at all.
    #
    # ORDER IS THE WHOLE OF IT. The two handlers below compare the
    # layer's colours against what the plugin WOULD DRAW for this row,
    # and each of them returns early when the field, the class count
    # or the mode disagrees -- reasonably, since a positional walk
    # across two different ladders means nothing. So while the row was
    # stale those guards fired first and the edit was dropped on the
    # floor. Bringing the row up to date here makes them the
    # colour-refinement handlers they were always meant to be.
    # ...AND THE COLOUR HANDLER BELOW NO LONGER NEEDS TO BE TOLD WHAT
    # THIS DID. Bringing the row up to date disarms that handler's own
    # count guard -- `len(expected) != len(actual)`, where `expected`
    # is built from the ROW, so once the row has followed to six
    # classes it matches the layer's six. The first repair passed a
    # `count_moved` flag measured on both sides of this call, and that
    # flag was a DELTA: true on the signal carrying the change and
    # false on every signal after it, with three routes to a second
    # pass (ledger row 2 of 2026-08-20). It is gone. The handler now
    # asks a question the state can answer at ANY moment -- is this
    # colour one we painted -- against `_painted_ladders`.
    self._row_follows_the_renderer(tile_id, renderer)
    if isinstance(renderer, QgsGraduatedSymbolRenderer):
      # the graduated mirror of everything below (settled 2026-08-09)
      self._graduated_layer_edited(layer, tile_id, renderer)
      return
    if not isinstance(renderer, QgsCategorizedSymbolRenderer):
      # THE DESIGN VIEW STILL HAS TO FOLLOW, and until 2026-08-28 it
      # did not. This exit is taken by exactly the renderers deferral
      # is made of -- a rule-based fill, a single symbol somebody
      # mixed in the dock -- which is the one case where the map's
      # colour is nobody's but the user's. Both nameable siblings
      # refresh; this one returned in front of the refresh, so the
      # preview went on painting the plugin's old colour, a colour the
      # map does not contain, for the rest of the session, and no
      # later act healed it. Measured by rendering the widget: zero
      # pixels of the colour the map draws.
      # The fifth door into the room `test_every_restyle_door_repaints_
      # the_preview` walked on 2026-08-26, and the reason none of the
      # four found it is that the dialog's own computation is RIGHT
      # here -- `_table_id_colours` answers the new colour -- so every
      # test reading that function passes straight over it.
      self._refresh_preview_colours()
      return
    assignment = self._assignment_for(tile_id)
    if assignment is None or assignment["mode"] != "Categorized" \
        or not assignment["var"]:
      return
    if renderer.classAttribute() != assignment["var"]:
      # reclassified on a different field in the dock: the dialog has
      # no record to reconcile that against, so it leaves the work
      # alone (the signature rule already preserves it)
      return
    # what the layer actually draws now, keyed like the dialog's own
    # records (NO_DATA_KEY for the catch-all)
    actual = {}
    for category in renderer.categories():
      value = category.value()
      key = bridge.NO_DATA_KEY if value is None else str(value)
      actual[key] = category.symbol().color().name()
    expected, _order = self._current_category_colours(assignment)
    if expected is None:
      return  # the region layer or its field has gone; nothing to judge
    if all(expected.get(key) == colour for key, colour in actual.items()):
      # THE CATEGORIZED TWIN of the guard repaired in the graduated
      # path the same evening, and the twin is the lesson rather than
      # the fix. A FILL comparison cannot see a stroke, a legend label
      # or a deleted category -- so a user who adds outlines, retypes a
      # label or removes a class in QGIS's Symbology panel had the map,
      # the project and QGIS all agreeing while the GeoPackage a
      # colleague opens went on drawing the style from before the edit.
      # Generate did not heal it.
      #
      # MEASURED 2026-08-17, both sides in one probe run, which is what
      # made the sentence unarguable: a stroke added to a categorized
      # element gave 0 embeds and an unchanged file, while a break
      # retyped on a graduated one in the SAME run gave 1 embed and a
      # changed file. Read back two ways -- sqlite on
      # `layer_styles.styleQML` with no QGIS involved, and a cold
      # `QgsVectorLayer` with `loadDefaultStyle()` in a cleared
      # project. Deleting a category left the map drawing four and the
      # file declaring five.
      #
      # WHEN A GUARD OF THIS SHAPE IS FIXED, THE FIRST PLACE TO LOOK IS
      # THE SAME GUARD IN THE SIBLING RENDERER PATH. This project has
      # written down twice that a rule naming one of a pair gets read
      # as a rule about one of a pair; the graduated repair was made
      # hours before this one and never looked five hundred lines up.
      # THE FILE LEARNS AT SAVE (ruling of 2026-08-27). The change
      # above reaches the map, the project and the group's record
      # here; the GeoPackage is written by `_save_the_map`, in one
      # act with the record that describes it, so the two cannot
      # disagree. The paragraph above this is kept as HISTORY: it
      # argues for a write that used to happen at this line, and the
      # defect it describes is what the one-act save prevents.
      _dump("DROP", tile_id, "clean-classify")
      return  # our own seeding, or an edit that changed no colour

    # a clean classify from a standard ramp? Only without an imported
    # class source -- while a file governs the classes, a dock
    # recolour is a divergence from the file, which is Custom by
    # definition -- and only for a ramp of the CATEGORICAL family.
    # A categorized row auto-swaps quantitative ramps away (_sync_row),
    # so following one would snap the combo to a different ramp while
    # the layer wears the dock's colours: the very lie this handler
    # exists to prevent. Such an edit is adopted as Custom instead.
    name = self._ramp_name_matching(
      renderer.sourceColorRamp(),
      prefer=self._ramp_choices.get(tile_id))
    if name is not None and name in bridge.CATEGORICAL_RAMPS \
        and not assignment.get("class_source"):
      trial = bridge.make_categorized_renderer(
        layer, assignment["var"], name, assignment["outline"])
      trial_colours = {
        str(c.value()): c.symbol().color().name()
        for c in trial.categories() if c.value() is not None}
      dock_colours = {key: colour for key, colour in actual.items()
                      if key != bridge.NO_DATA_KEY}
      # THE CATCH-ALL IS ASKED ABOUT TOO, and dropping it from BOTH
      # sides is ledger row 5, shipping since 2026-08-10. It was
      # dropped for a real reason -- `trial` is built from the ramp
      # alone and its catch-all is the plugin's default, which says
      # nothing about a ramp -- but the effect was that an edit
      # touching ONLY the catch-all compared EQUAL to a clean
      # Classify. The handler then announced that the element "now
      # follows" a ramp nobody had chosen, cleared the user's picks,
      # and repainted those areas the default grey at the next
      # Generate.
      #
      # ASKED AGAINST `expected` RATHER THAN AGAINST `trial`, because
      # the question is not what the RAMP would put there -- the ramp
      # has no opinion about the catch-all -- but whether this class
      # is still drawing what THIS ELEMENT would draw, default or
      # earlier pick alike. A clean Classify leaves it alone, so the
      # follow branch loses nothing; a recolour moves it, which is
      # exactly the difference these two branches exist to tell apart.
      #
      # Unknown on either side does not block the follow: absence of
      # evidence is not evidence of a pick, which is a mistake this
      # project made in the other direction three days ago.
      here = actual.get(bridge.NO_DATA_KEY)
      ours = expected.get(bridge.NO_DATA_KEY)
      catch_all_moved = (here is not None and ours is not None
                         and here.lower() != ours.lower())
      if dock_colours == trial_colours and not catch_all_moved:
        # cleared here as well as in the combo handler, because when
        # the dock re-applied the ramp the dialog already names,
        # setCurrentText below fires no signal and the picks would
        # outlive the clean ramp the layer now wears
        self._clear_category_colours(tile_id, "a new colour ramp")
        for row in range(self.table.rowCount()):
          item = self.table.item(row, 0)
          combo = self.table.cellWidget(row, 4)
          if item is not None and item.text() == tile_id \
              and combo is not None and hasattr(combo, "findText") \
              and combo.findText(name) >= 0:
            # the ordinary handler runs: it records the choice and
            # destroys any hand-picks, with the standing notice
            combo.setCurrentText(name)
            break
        self._report_quietly(
          f"Element '{tile_id}' now follows the '{name}' ramp chosen "
          f"in QGIS.")
        # refresh explicitly: when the dock re-applied the ramp the
        # combo already named, no combo signal ran to do it
        self._refresh_preview_colours()
        # the layer already wears this exact style, so the element is
        # marked as seeded and the next restyle leaves it in peace
        refreshed = self._assignment_for(tile_id)
        if refreshed is not None:
          self._last_signatures[tile_id] = self._signature(refreshed)
          # and the LAYER is told the picks are gone, which is the
          # half this branch never did. The dicts were cleared and
          # the user was told the ramp now governs, while the stamp
          # went on holding the discarded colours -- and the stamp is
          # what survives into the .qgz. So the pick came back on
          # reopen, silently painted over the ramp the user had
          # chosen instead, and `_last_signatures` above guaranteed
          # no restyle would ever heal it. `_stamp_category_colours`
          # clears each property when there is nothing to record,
          # which is exactly this case; its two ADOPT exits called it
          # and these two FOLLOW exits did not. Measured 2026-08-13.
          # Guarded by test_a_discarded_pick_does_not_come_back.
          # the CATEGORIZED half of this branch
          self._stamp_category_colours(layer, refreshed)
          # ...AND THE FILE, which this exit forgot. Its twin in
          # `_restyle_only` stamps AND embeds; these four adoption
          # exits stamped only, so a recolour made in QGIS's own
          # styling dock never reached the exported GeoPackage -- and
          # the signature recorded a moment later then made the
          # restyle path SKIP the element, so pressing Generate could
          # not heal it either. A colleague opening the file saw the
          # colours from before the edit, beside a stamp claiming the
          # new ones. Measured 2026-08-17 over 1,751 comparisons
          # between a sending project and the file a separate process
          # opened: 11 disagreements for a categorical recolour, 12
          # for a graduated one, and an element at 0.25 opacity in the
          # project and 0.85 in the file.
          # THE FILE LEARNS AT SAVE (ruling of 2026-08-27). The change
          # above reaches the map, the project and the group's record
          # here; the GeoPackage is written by `_save_the_map`, in one
          # act with the record that describes it, so the two cannot
          # disagree. The paragraph above this is kept as HISTORY: it
          # argues for a write that used to happen at this line, and the
          # defect it describes is what the one-act save prevents.
        return

    # adopt the divergent colours as hand-picks for the current field
    field = assignment["var"]
    record = self._category_colours.setdefault(tile_id, {}) \
        .setdefault(field, {})
    # NO TEMPLATE GUARD HERE, AND THAT IS MEASURED RATHER THAN
    # OVERLOOKED. Its graduated twin declines to adopt a colour equal
    # to the renderer's SOURCE SYMBOL, because QGIS clones that symbol
    # for a class the user adds and the plugin was recording its own
    # placeholder as somebody's decision (ledger row 34). The obvious
    # next move is to write the same guard here, and it would be dead
    # code: `make_categorized_renderer` sets no source symbol, so
    # `sourceSymbol()` answers None on every categorized renderer this
    # plugin builds -- measured on QGIS 4.0.3, 2026-08-20, on a
    # six-category tab10 element. A guard that cannot fire is worse
    # than none, since it reads as protection and would sit in the
    # catalogue as an unkillable survivor forever.
    #
    # WHAT WOULD REOPEN IT: a QGIS release that gives the categorized
    # renderer a source symbol, or this plugin setting one. Either
    # makes a category added in the panel arrive wearing a template,
    # and a new category has a new KEY, so `expected.get(key)` is None
    # and the walk below would adopt it on sight.
    adopted = 0
    # ...BY ATTRIBUTION, NOT DELTA (2026-08-26, the seams hunt). The
    # walk used to adopt whatever differed from what the plugin would
    # seed NOW -- and a landing keeping a renderer over an unreadable
    # class source made that delta lie: "expected" fell back to
    # automatic colours while the map honestly wore the template, so
    # the template's own colours became hand-picks that outrank the
    # template forever. `_painted_categories` answers whose colour
    # each one is, exactly as `_painted_ladders` does for the
    # graduated twin; a colour the plugin painted, or one on an
    # element never seen, is declined -- neither is a person's
    # decision.
    painted = (self._painted_categories.get(str(tile_id)) or {}).get(field)
    unattributable = 0
    for key, colour in actual.items():
      if expected.get(key) != colour and record.get(key) != colour:
        if painted is None or painted.get(key) == colour:
          unattributable += 1
          continue
        record[key] = colour
        adopted += 1
    if unattributable:
      _dump("ADOPTCOLOUR", tile_id, "declined=", unattributable)
    _dump("ADOPTCOLOUR", tile_id, "adopted=", adopted,
          "expected=", expected, "actual=", actual)
    if not adopted:
      return
    self._custom_swatch_cache.pop(tile_id, None)
    # AND THE RECORD OF WHAT WE PAINTED FOLLOWS THE ADOPTION, which
    # until 2026-08-28 it did not. `_painted_categories` is what this
    # walk asks whose colour a category wears, and no exit of this
    # handler refreshed it -- so it went on naming the colours the
    # plugin painted BEFORE the adoption. Recolour two categories in
    # the dock, change your mind about one and put it back to the
    # colour it had, and the plugin kept the discarded colour, said
    # nothing, and the next control change plus a Generate painted it
    # back over the map. The graduated twin calls
    # `_remember_painted_ladder` at all three of its exits; this one
    # called it at none, and the tell was that the twin has the same
    # memory and refreshes it.
    self._remember_painted_ladder(layer, tile_id)
    # the layer already wears these colours; recording the new
    # signature stops the restyle path re-seeding it, which would
    # discard any OTHER refinement the dock applied alongside them
    refreshed = self._assignment_for(tile_id)
    if refreshed is not None:
      self._last_signatures[tile_id] = self._signature(refreshed)
      self._stamp_category_colours(layer, refreshed)
      # ...AND THE FILE, which this exit forgot. Its twin in
      # `_restyle_only` stamps AND embeds; these four adoption
      # exits stamped only, so a recolour made in QGIS's own
      # styling dock never reached the exported GeoPackage -- and
      # the signature recorded a moment later then made the
      # restyle path SKIP the element, so pressing Generate could
      # not heal it either. A colleague opening the file saw the
      # colours from before the edit, beside a stamp claiming the
      # new ones. Measured 2026-08-17 over 1,751 comparisons
      # between a sending project and the file a separate process
      # opened: 11 disagreements for a categorical recolour, 12
      # for a graduated one, and an element at 0.25 opacity in the
      # project and 0.85 in the file.
      # THE FILE LEARNS AT SAVE (ruling of 2026-08-27). The change
      # above reaches the map, the project and the group's record
      # here; the GeoPackage is written by `_save_the_map`, in one
      # act with the record that describes it, so the two cannot
      # disagree. The paragraph above this is kept as HISTORY: it
      # argues for a write that used to happen at this line, and the
      # defect it describes is what the one-act save prevents.
    self._report_quietly(
      f"Element '{tile_id}' keeps the {adopted} colour(s) set in "
      f"QGIS; its ramp cell now reads Custom.")
    self._refresh_preview_colours()

  def _row_follows_the_renderer(self, tile_id, renderer):
    """Make a row say what its layer now holds, after an outside edit.

    Args:
      tile_id: the element whose row is to be brought up to date.
      renderer: the renderer the layer is carrying NOW, taken off the
        layer rather than from any record of ours.

    Returns:
      True when something in the row actually moved, False when the
      row already agreed with the layer or when the renderer is one no
      row can name -- in which case the element is DEFERRING and
      `_refresh_deferring_rows` owns it instead.

    THE DEFECT THIS ANSWERS, reported from the field against rc5 and
    reproduced 2026-08-17. A tester set new break values on one
    element in QGIS's Symbology panel, copied that style onto the
    other four, and reset each one's variable and ramp by hand --
    QGIS's copy-and-paste carries the field along, so it has to be.
    None of it reached the plugin. The rows went on describing the map
    THE PLUGIN LAST DREW while QGIS drew something else, and the next
    Generate destroyed the lot.

    Three guards in `_graduated_layer_edited` each returned early on
    exactly the cases that matter -- a changed field, a changed class
    count, a changed mode -- on the reasoning that a reclassification
    is something the dialog has no record to reconcile against. That
    was true and was the wrong conclusion: the renderer IS the record,
    and reading it is what this does.

    THE MAINTAINER'S RULING, 2026-08-17, choosing between three
    options put to them: the row FOLLOWS the layer wherever the plugin
    can name what the layer holds, and defers only where it cannot.
    Pins were the alternative and cannot carry this -- the tester's
    element disagreed on the class COUNT and the RAMP as well as the
    breaks, and a pin names a bound. Deferring on any outside edit was
    the other, and hands away an element the user may still want to
    drive from the table.

    It also settles the reported oddity that three rows read
    CATEGORIZED over graduated layers. That was never a categorical
    fault: the rows were simply stale, and the greyed 32, 33 and 32
    were distinct-value counts belonging to whatever those rows last
    believed. Following the renderer makes the question disappear
    rather than answering it.

    SIGNALS ARE BLOCKED THROUGHOUT, and that is not a detail. A
    handler on this path must never reach `_rebuild_unit` or
    `_refresh_table`: a rebuild replaces every cell widget, and one
    landing mid-interaction is the "race among choosers" this project
    has a regression test for. So the widgets are moved quietly and
    the records they back are written directly, which is also why the
    signature is re-recorded here -- without it the next restyle would
    read a row that had changed with no signal and undo the follow.
    """
    style = bridge.expressible_style(renderer)
    if style is None:
      return False            # deferring; not ours to describe
    mode, scheme = style
    # SCOPED TO CLASSED RENDERERS, and the scope is the whole safety of
    # it. A SINGLE SYMBOL is already handled, correctly, by a settled
    # rule older than this method: hand styling survives a Generate
    # unless that element's dialog assignment CHANGED. Following it
    # here changes the assignment -- to "Single colour" -- so the next
    # Generate re-seeds the element and paints the plugin's own colour
    # over the one the user set in the dock. Measured 2026-08-17 by
    # `test_output_management`, which caught a hand-set #0b1e2d coming
    # back as #3c8bc2 the first time this ran unscoped.
    #
    # THE GENERAL SHAPE, worth keeping: a mechanism that makes the row
    # DESCRIBE the layer is safe only where the row can REPRODUCE the
    # layer. A field, a scheme, a class count and a named ramp are
    # reproducible; an arbitrary fill a person mixed in the dock is
    # not, and describing it as "Single colour" throws it away while
    # looking like agreement. What the field report is about is classed
    # renderers on both sides anyway -- both of the tester's
    # screenshots show Graduated.
    if mode not in ("Graduated", "Categorized"):
      return False
    row = self._row_for_element(tile_id)
    if row is None:
      return False
    moved = []

    # ---- the FIELD, which a pasted style carries along with it
    field = (renderer.classAttribute()
             if hasattr(renderer, "classAttribute") else "")
    variable = self.table.cellWidget(row, 1)
    if field and variable is not None and hasattr(variable, "findText") \
        and variable.currentText() != field \
        and variable.findText(field) >= 0:
      variable.blockSignals(True)
      variable.setCurrentText(field)
      variable.blockSignals(False)
      moved.append(f"variable to '{field}'")

    # ---- the STYLE, named the way the chooser names it
    label = mode
    if mode == "Graduated":
      label = next((text for text, name in self.GRAD_SCHEMES.items()
                    if name == scheme), label)
    chooser = self.table.cellWidget(row, 2)
    if chooser is not None and hasattr(chooser, "findText") \
        and chooser.currentText() != label and chooser.findText(label) >= 0:
      chooser.blockSignals(True)
      chooser.setCurrentText(label)
      chooser.blockSignals(False)
      # MARKED AS TOUCHED, or the next rebuild throws it away.
      # `_refresh_table` restores a row's mode from the previous
      # assignment only when `style_touched` is set, and otherwise
      # re-derives it from the variable's type -- so a style written
      # here with signals blocked survived until the first spacing
      # change and then silently reverted. Found by the full suite,
      # in `test_dialog_end_to_end`, which is the argument for
      # running it rather than a subset after touching this path.
      #
      # Setting it is not a fudge to get past a guard: the flag means
      # "somebody chose this rather than the plugin guessing", and
      # somebody did choose it -- in QGIS's Symbology panel instead
      # of in this table. `last_style` goes with it, since that is
      # the baseline a later scheme change compares against.
      chooser.setProperty("touched", True)
      chooser.setProperty("last_style", label)
      moved.append(f"style to {label}")

    # ---- the CLASS COUNT, and only where it means a count somebody
    # CHOSE. Unclassed's fifty is fixed by the style's definition and
    # has never been allowed into `_class_counts`; a CATEGORIZED
    # renderer's category count is a property of the data, and letting
    # it in here is precisely the leak that put a greyed 32 in front
    # of the tester and clamped it to 20 at the next rebuild. So the
    # count follows for classed graduated rows alone, and only inside
    # the range the spinner can actually hold.
    counter = self.table.cellWidget(row, 3)
    if mode == "Graduated" and scheme != "Unclassed" \
        and counter is not None and hasattr(renderer, "ranges"):
      ranges = renderer.ranges()          # bound: temporaries dangle
      count = len(ranges)
      if counter.minimum() <= count <= counter.maximum() \
          and int(counter.property("user_k") or counter.value()) != count:
        counter.blockSignals(True)
        counter.setValue(count)
        counter.setProperty("user_k", count)
        counter.blockSignals(False)
        # ...AND THE RECORD BEHIND THE CONTROL, which the widget alone
        # is not. `_refresh_table` rebuilds a row's class count from
        # `_class_counts` FIRST and falls back to the previous
        # assignment only when that is empty -- so writing the spinner
        # and not the record left the followed count alive until the
        # first spacing nudge and then silently reverted, taking the
        # user's classification with it at the next Generate. Exactly
        # the field report the follow exists to close, reopened by a
        # table rebuild.
        #
        # The COPY door twelve hundred lines down (`_sync_target_
        # controls`) writes both, and has since it was written. The
        # follow moved four things -- field, style, count, ramp -- and
        # only the one with a second store came undone, because the
        # other three have no record but the widget.
        #
        # GREP THE RECORD BEHIND A CONTROL, NOT THE CONTROL. A new
        # mechanism that sets a widget has to ask what else claims to
        # know that value, and a rebuild is where the two meet.
        #
        # `_class_counts` means "a count somebody CHOSE", and under
        # the maintainer's ruling a count set in QGIS's own Symbology
        # panel is chosen -- in a different window, by the same
        # person. The guard above already keeps out the two counts
        # that are NOT choices: Unclassed's fifty, fixed by the
        # style's definition, and a categorized renderer's category
        # count, which is a property of the data.
        self._class_counts[tile_id] = int(count)
        # ...AND THE COPIED LADDER IS RELEASED, exactly as both table
        # doors into this record do. A copy DEGRADES TO ITS PINS when
        # the class count changes -- that is the settled rule, and it
        # was enforced only at the doors a user opens inside the
        # plugin. This is the door QGIS opens, added 2026-08-17
        # without it, so a count set in the Symbology panel was
        # accepted, announced ("classes to 8"), and then silently
        # undone: `make_graduated_renderer` short-circuits on
        # `pinned["breaks"]`, so the element went on drawing the five
        # classes "Copy to..." had given it while the spinner read
        # eight. Measured 2026-08-19 in rendered pixels, against a
        # hand-pinned element beside it that survived the same edit.
        #
        # A RULE ENFORCED ONLY AT THE DOORS A USER OPENS INSIDE THE
        # PLUGIN IS UNENFORCED AT THE DOOR QGIS OPENS. Grep every
        # writer of the value a rule keys on, not only the handlers.
        self._release_copied_breaks(tile_id, "a new class count")
        moved.append(f"classes to {count}")

    # ---- the RAMP, where QGIS's own ramp answers to a name we offer
    name = self._ramp_name_matching(
      renderer.sourceColorRamp()
      if hasattr(renderer, "sourceColorRamp") else None,
      prefer=self._ramp_choices.get(tile_id))
    ramp_cell = self.table.cellWidget(row, 4)
    if name is not None and ramp_cell is not None \
        and hasattr(ramp_cell, "findText") \
        and ramp_cell.currentText() != name \
        and ramp_cell.findText(name) >= 0:
      ramp_cell.blockSignals(True)
      ramp_cell.setCurrentText(name)
      ramp_cell.blockSignals(False)
      self._ramp_choices[tile_id] = name
      moved.append(f"ramp to '{name}'")

    if not moved:
      return False
    # The row has changed with no signal, so nothing else knows. Record
    # the signature against the row AS IT NOW READS, or the next
    # restyle compares the layer with a row it has never seen and
    # re-seeds the very renderer this followed.
    refreshed = self._assignment_for(tile_id)
    if refreshed is not None:
      self._last_signatures[tile_id] = self._signature(refreshed)
      # ...AND THE STAMP AND THE FILE, which this method must do
      # ITSELF because making the row agree is exactly what stops the
      # handlers below doing it.
      #
      # THE REGRESSION THIS REPAIRS, found by a hunt within hours of
      # the follow landing and worth spelling out, because the shape
      # is general and invisible in a diff. `_graduated_layer_edited`
      # opens with `if actual == expected: return`, where `expected`
      # is what the plugin would draw FOR THIS ROW. Running before it
      # and making the row agree with the layer turns that guard from
      # a fall-through into a return -- so the stamp-and-embed exits
      # BEHIND it stopped being reached. Those exits were themselves a
      # fix made five hours earlier the same day, for precisely this
      # harm: a ramp changed in QGIS reaching the map and the project
      # but never the exported GeoPackage, with the signature recorded
      # a moment later making the restyle path skip the element, so
      # Generate could not heal it. A colleague opening the file saw
      # the colours from before the edit. Measured over 1,751
      # comparisons then; reproduced through two independent read
      # routes now, including reading `layer_styles.styleQML` out of
      # the file with sqlite.
      #
      # WHEN YOU INSERT A STEP BEFORE EXISTING HANDLERS, RE-READ EVERY
      # GUARD THOSE HANDLERS OPEN WITH. A guard that used to fall
      # through may now fire, and it takes everything behind it. One
      # commit disabled another without touching a line of it, and
      # nothing on screen told them apart: the row reads correctly in
      # both.
      layer_now = QgsProject.instance().mapLayer(
        self._element_layer_ids.get(tile_id, ""))
      if layer_now is not None:
        self._stamp_category_colours(layer_now, refreshed)
        # THE FILE LEARNS AT SAVE (ruling of 2026-08-27). The change
        # above reaches the map, the project and the group's record
        # here; the GeoPackage is written by `_save_the_map`, in one
        # act with the record that describes it, so the two cannot
        # disagree. The paragraph above this is kept as HISTORY: it
        # argues for a write that used to happen at this line, and the
        # defect it describes is what the one-act save prevents.
    self._refresh_preview_colours()
    self._report_quietly(
      f"Element '{tile_id}' follows the styling you set in QGIS: "
      + ", ".join(moved) + ".")
    return True

  def _adopt_dock_bounds(self, tile_id, assignment, bounds, colours):
    """Take up class boundaries retyped in QGIS's Symbology panel.

    Args:
      tile_id: the element whose layer was edited.
      assignment: its row, from ``_assignment_for``.
      bounds: ``[(lower, upper), ...]`` as the layer now holds them.
      colours: the layer's class colours, in the same order.

    Returns:
      None. Records the ladder as pinned bounds when a RETYPE moved
      the numbers and nothing else, so every reader of
      ``_current_graduated_classes`` -- the editor, the swatch, the
      table -- shows what QGIS is holding rather than what this dialog
      would compute.

    THE INTERIOR BOUNDARIES ONLY, with low/high cleared. Those two
    pin the FIRST class's upper bound and the LAST class's lower
    bound, not the ladder's outer edges; filling them from the edges
    wrote 0 and 80 into the interior and produced a ladder running
    backwards. The outer edges are the column's extremes, which is
    the model: typing 0 - 10 over a column starting at 3.1 gives
    (3.1, 10), the same areas in the same class.

    AND ONLY AT REST, which is the whole of the rest of this method's
    difficulty. A ladder read while the plugin is mid-work is not a
    ladder anybody typed.
    """
    # THREE REST CONDITIONS, and all three are needed. Bracketed by
    # bisection to the STORE below, after four theories were each
    # implemented and each wrong -- returning immediately before the
    # store made the failing guard pass while every check above it
    # still ran, and logging the store then named what it wrote: five
    # classes, breaks [1.0, 1.4, 2.6, 3.0], the plugin's OWN ladder on
    # that fixture, recorded as though a person had typed it. Pinned,
    # it was re-imposed when the next run landed, and a twelve-class
    # reclassification made in the dock became five.
    #
    # `_applying_style` alone is NOT enough: it is not set during the
    # mid-run re-examination that `_preserved_this_run` marks, which
    # is exactly when this fired. During any of the three the record
    # and the layer are transiently out of step.
    #
    # Guarded by test_a_dock_reclassification_lands_while_a_run_is
    # _finishing, which is older than this method and was protecting
    # real behaviour that must not be weakened to fit an addition.
    if getattr(self, "_applying_style", False):
      _dump("BOUNDS", tile_id, "applying-style")
      return
    # A RUN IN FLIGHT DEFERS THE ADOPTION; IT NO LONGER DISCARDS IT.
    # The rest conditions are right and stay: what sits on the layer
    # mid-landing is nobody's decision. But returning here THREW THE
    # EDIT AWAY, so a boundary retyped while a run was finishing was
    # gone when it landed -- which is the very shape the maintainer
    # ruled on for a pasted style in 2026-08-17, and which the
    # symbology matrix caught here on 2026-08-19 the day it gained a
    # race axis.
    #
    # THE BOUNDS ARE KEPT, NOT THE INTENTION TO RE-READ THEM. The
    # landing RE-SEEDS the element's renderer from the record, so
    # asking the layer again afterwards would read the plugin's own
    # ladder and adopt that -- the exact fault these guards exist to
    # prevent, arriving by the other door. What a person typed is
    # captured at the moment it arrives and applied once at rest.
    if getattr(self, "_task", None) is not None or \
        getattr(self, "_preserved_this_run", None):
      # ONLY WHAT ADOPTION COULD EVER TAKE. A change to the class COUNT
      # is a RECLASSIFICATION, which this method refuses further down
      # and must not touch -- the signature rule preserves those. Yet
      # capturing one here and replaying it made the map come back
      # with the plugin's five classes where the dock had left twelve:
      # the replay reached the element AFTER the landing had preserved
      # it and reconciled it back down. Deferring work that would be
      # refused anyway is not free; it is a second path to an element
      # the first path had already settled.
      #
      # `mine` is not asked for here, deliberately, because it BUILDS a
      # renderer and this runs inside a Qt slot on every dock edit. The
      # cheap count is enough to tell a retype from a reclassification.
      count = len(self._current_graduated_classes(assignment) or [])
      if count and count == len(bounds):
        self._adoption_deferred[tile_id] = (
          dict(assignment), list(bounds), list(colours))
      _dump("BOUNDS", tile_id, "in-flight, deferred=",
            tile_id in self._adoption_deferred)
      return
    field = assignment["var"]
    if not bounds or len(bounds) < 2:
      _dump("BOUNDS", tile_id, "too-few", len(bounds or ()))
      return
    mine = self._current_graduated_classes(assignment)
    # A CHANGED COUNT IS A RECLASSIFICATION, which this must not
    # touch: the handler leaves one alone and the signature rule
    # preserves it.
    if not mine or len(mine) != len(bounds):
      _dump("BOUNDS", tile_id, "count", len(mine or ()), "vs",
            len(bounds))
      return
    # ONLY WHEN THE COLOURS DID NOT MOVE, which is what separates a
    # hand RETYPE from a dock CLASSIFY. Classify picks a ramp and
    # rewrites both; the colour machinery already follows that and
    # recomputes the breaks, so pinning them here freezes a ladder
    # nobody chose.
    ours = [c.lower() for _lo, _hi, c in mine]
    theirs = [c.lower() for c in colours]
    if ours != theirs and all(a != b for a, b in zip(ours, theirs)):
      # A WHOLESALE REPAINT IS A CLASSIFY; A PARTIAL ONE IS SOMEBODY'S
      # HAND. The guard used to demand that NO colour had moved, which
      # is right about a Classify -- it picks a ramp and rewrites every
      # class -- and wrong about the visit where a person retypes a
      # boundary AND recolours a class. That satisfied neither branch,
      # so the boundary was never recorded here (ledger row 6).
      #
      # WHAT IT STILL REFUSES is unchanged: a ramp chosen in the dock
      # moves every class, so the ladder it computed is not pinned and
      # the colour machinery goes on recomputing the breaks. What it
      # now allows is the case where SOME classes still wear the
      # colours the plugin painted, which no Classify produces.
      #
      # THE COST, said plainly: recolouring every class one at a time
      # in a single visit reads as a Classify and its boundaries are
      # not adopted. That is the honest edge of a two-way question,
      # and it fails towards not pinning a ladder nobody chose.
      #
      # WHY IT MATTERED EVEN THOUGH THE BOUNDARY SURVIVED. Measured
      # 2026-08-20 with the gate dumps: the first signal declined here
      # and a SECOND, echoed by the colour adoption's own stamping,
      # adopted the bounds a moment later. So the record was right by
      # an accident of ordering -- which is the very shape this ledger
      # row exists to name, arriving in the repair rather than in the
      # bug. A promise kept by an echo is not kept.
      # HYPHENATED, like every other gate label here. Written as
      # "classify: every colour moved" it read as a SENTENCE to
      # `text_review.py`, which collects prose-looking literals, and
      # duly arrived in the maintainer's review queue -- a diagnostic
      # asking to be approved as user-facing text. The `_dump`
      # docstring already says short labels are not prose; the fix is
      # to write a label, not to widen the collector's filter.
      _dump("BOUNDS", tile_id, "classify-every-colour-moved")
      return
    if all(abs(lo - a) < 1e-9 and abs(hi - b) < 1e-9
           for (lo, hi, _c), (a, b) in zip(mine, bounds)):
      _dump("BOUNDS", tile_id, "unchanged")
      return  # the ladder we drew; nothing was retyped
    wanted = dict(self._pinned_bounds.get(tile_id, {}).get(field) or {})
    wanted["breaks"] = [upper for _lower, upper in bounds[:-1]]
    _dump("BOUNDS", tile_id, "adopting", wanted["breaks"])
    # A PIN THE ADOPTED LADDER STILL CARRIES IS KEPT, and until
    # 2026-08-19 both were dropped unconditionally. `low` and `high`
    # name boundaries BETWEEN classes, and adopting a ladder that
    # happens to run through one of them says nothing about whether
    # the person still means it: retyping some OTHER boundary in
    # QGIS's panel left the pinned one exactly where it was and
    # demoted it anyway. Nothing was said, and the harm arrived at the
    # next thing the user did -- `_release_copied_breaks` keeps only
    # `low`/`high`, so a class-count change then had nothing left to
    # degrade to, wiped the record, and told them their classes "had
    # been copied from another element", which had never happened.
    #
    # COMPARED AT THE BOX'S DISPLAYED PRECISION, for the reason the
    # give-a-bound-back route already uses it: an edge of 3.0999999
    # can never be matched exactly, and a rule nobody can satisfy is
    # the same as no rule. Measured 2026-08-19, found by a hunt
    # pointed at a pinned bound meeting each QGIS-side edit in turn.
    edges = [round(float(upper), 6) for _lower, upper in bounds[:-1]]
    for end in ("low", "high"):
      here = wanted.get(end)
      if here is None:
        continue
      if not any(abs(round(float(here), 6) - edge) < 1e-6
                 for edge in edges):
        wanted.pop(end, None)
    # THE OUTER EDGES ARE ADOPTED TOO, and until 2026-08-19 they were
    # not. Only the interior boundaries were taken, on the reasoning
    # -- written into the ledger and wrong -- that a ladder's ends are
    # the column's extremes by definition, so somebody typing 0 - 10
    # over a column starting at 3.1 gets (3.1, 10) and "the same areas
    # in the same class". That is true about which tile takes which
    # colour and false about what the LEGEND SAYS, and the legend is
    # what a reader trusts; this project has made exactly that
    # distinction before, over a constant column drawing five
    # identical ranges. It was also only ever an argument about the
    # BOTTOM: the tester typed 80 for the top of a column ending at
    # 79.1 and got 79.1 back, where nothing is even arguably
    # unchanged.
    #
    # `fitted_breaks` widens outward only, so a floor above the
    # column's minimum falls back to that minimum rather than
    # orphaning every value beneath it. Both are recorded here
    # regardless of which way they will be resolved, because this is
    # the record of WHAT A PERSON LEFT ON THE LAYER; deciding what is
    # drawable belongs at the drawing, not at the watching.
    wanted["floor"] = float(bounds[0][0])
    wanted["ceiling"] = float(bounds[-1][1])
    # ...AND AN END THAT MOVED BECOMES A PIN (maintainer's decision,
    # 2026-08-19). A ladder adopted from the dock used to be stored as
    # `breaks` alone, with `low` and `high` kept only where they still
    # coincided with an edge. That is right for a retype of some
    # middle boundary and wrong for a style PASTED from another
    # element: the receiving element took every number and no
    # statement that any of them was a person's, so nothing marked
    # them, `_release_copied_breaks` had nothing to degrade to, and a
    # pin the sending element carried simply vanished. Reported by the
    # maintainer against rc10; ledger row 30.
    #
    # ONLY WHERE THE END ACTUALLY MOVED, which is the narrower reading
    # of "adopt the ends as pins too" and the better one: retyping a
    # middle boundary leaves the outer two exactly where the plugin
    # put them, and pinning those would claim a decision nobody made.
    # `setdefault`, so a pin the loop above deliberately KEPT is never
    # overwritten by the same number arriving a second way.
    # ...AND NEVER ONTO THE LADDER'S OWN EDGE. A `low` equal to the
    # floor, or a `high` equal to the ceiling, makes a class of ZERO
    # WIDTH -- which is not a classification anybody asked for, and
    # which this project already records as able to bring QGIS down
    # rather than raise: `deleteClass` on a one-class renderer
    # segfaults. The maintainer met a segfault on rc11 adding a class
    # in the styling panel, with `low: 0.0` sitting exactly on
    # `floor: 0.0` in the dump immediately before it. Whether that is
    # the cause is unproven; the guard is right either way, since an
    # empty class is a thing to REPORT and never a thing to pin.
    # Ledger row 33.
    floor_here = float(wanted.get("floor", bounds[0][0]))
    ceiling_here = float(wanted.get("ceiling", bounds[-1][1]))
    if len(mine) == len(bounds) and edges:
      if abs(edges[0] - float(mine[0][1])) > 1e-9 \
          and abs(edges[0] - floor_here) > 1e-9:
        wanted.setdefault("low", edges[0])
      if abs(edges[-1] - float(mine[-1][0])) > 1e-9 \
          and abs(edges[-1] - ceiling_here) > 1e-9:
        wanted.setdefault("high", edges[-1])
    source = self._classification_values(field)
    values = (source.uniqueValues(source.fields().indexOf(field))
              if source is not None else [])
    # A LADDER THAT EXCLUDES EVERY VALUE IS NOT A CLASSIFICATION, and
    # adopting its ends blanks the map. Found by the symbology matrix
    # on 2026-08-19, on a column of about 1e9 whose ladder was retyped
    # to 0-80: the ceiling of 80 excluded all hundred values, the pool
    # emptied, and the element came back with NO CLASSES AT ALL --
    # where before the ends were adopted it drew five. The shape only
    # surfaced because the matrix gained a magnitude axis; the spine
    # shapes all live between 0 and about 80, where the same retype is
    # perfectly sensible.
    #
    # THE INTERIOR BREAKS ARE STILL TAKEN. What is dropped is only the
    # pair of edges, which then fall back to the column's own extremes
    # exactly as they did before this feature -- so the tester's own
    # report stays fixed and the map keeps its data. Somebody typing a
    # ladder that misses their data has made a mistake rather than a
    # request, and the honest answer is to follow what they typed as
    # far as it can be drawn.
    if any(bridge.absence_kind(v, wanted["floor"],
                               wanted["ceiling"]) != bridge.OUTSIDE_RANGE_KEY
           for v in values if not bridge.cannot_be_placed(v)):
      pass                       # something survives the limits; keep them
    else:
      wanted.pop("floor", None)
      wanted.pop("ceiling", None)
    if bridge.pin_problem(None, None, values, len(bounds),
                          wanted.get("breaks")):
      return
    self._pinned_bounds.setdefault(tile_id, {})[field] = wanted
    self._custom_swatch_cache.pop(tile_id, None)
    # THE ROW HAS MOVED WITH NO SIGNAL, so record the signature
    # against it as it now reads. The layer ALREADY WEARS this ladder
    # -- that is what was just adopted -- so the element has nothing
    # the dialog needs to impose, and leaving the old signature makes
    # the next run read it as CHANGED and re-seed the very thing this
    # followed. The four colour-adoption exits above each do this for
    # the same reason and say so; this one is the bounds' twin and was
    # written without it.
    #
    # MEASURED 2026-08-19, and it is why a twelve-class classify made
    # in QGIS's dock came back as the plugin's five. Adopting a
    # five-class retype put `breaks`, `floor` and `ceiling` into the
    # record, which is term 14 of the signature; the landing compared
    # a row carrying them against a signature recorded before they
    # existed, found them different, and re-seeded over the twelve
    # classes the user had made in the meantime. Bracketed by
    # bisecting dialog.py against its last-good copy, then dumping
    # the mismatching term.
    #
    # NOTHING IS REPAINTED HERE, deliberately: with live update off
    # the map is not refreshed on its own, and what this restores is
    # only that the landing stops CLOBBERING what a person left on the
    # layer. (Maintainer's ruling, 2026-08-19: preserve, do not
    # repaint.)
    refreshed = self._assignment_for(tile_id)
    if refreshed is not None:
      self._last_signatures[tile_id] = self._signature(refreshed)
      # ...AND THE STAMP AND THE FILE, which this exit forgot, exactly
      # as its four colour twins forgot them on 2026-08-17. Nothing on
      # a renderer records that a break was CHOSEN rather than
      # computed, so `weavingspace_quant_style` is the only thing a
      # reopened project has to go on -- and the line above, which
      # stops the landing clobbering the ladder, also makes
      # `_restyle_only` skip this element, so a Generate cannot heal
      # what a reopen has lost.
      #
      # MEASURED 2026-08-19, by a hunt reading the saved `.qgz` with
      # `zipfile` and the exported GeoPackage with `sqlite3`, neither
      # of which involves QGIS: the retyped ranges were in the file's
      # QML and `weavingspace_quant_style` appeared nowhere. So the
      # map came back looking right and the next Generate quietly
      # recomputed the plugin's own numbers.
      #
      # THE EMBED IS REPEATED HERE ON PURPOSE. `_graduated_layer_edited`
      # embeds on the way into this method, which is BEFORE the record
      # and the stamp exist; a file written then cannot carry them.
      layer_now = QgsProject.instance().mapLayer(
        self._element_layer_ids.get(tile_id) or "")
      if layer_now is not None:
        self._stamp_category_colours(layer_now, refreshed)
        # THE FILE LEARNS AT SAVE (ruling of 2026-08-27). The change
        # above reaches the map, the project and the group's record
        # here; the GeoPackage is written by `_save_the_map`, in one
        # act with the record that describes it, so the two cannot
        # disagree. The paragraph above this is kept as HISTORY: it
        # argues for a write that used to happen at this line, and the
        # defect it describes is what the one-act save prevents.
    # ...AND THE ROW IS TOLD, which is what makes the Style cell read
    # Custom. That cell is decided in `_sync_row`, whose callers are
    # the dynamic-column pass (reached from `_queue_live`) and the
    # deferral refresh -- neither of which a dock edit goes anywhere
    # near. So the record held a ladder somebody else cut while the
    # cell went on naming the scheme: a UNIT-TESTED MECHANISM WITH AN
    # UNDRIVEN CALLER, which is a motionless axis and a shape this
    # project has met before at `unworn_classes`.
    #
    # LAST, and contained. This runs inside a Qt slot where an
    # exception is swallowed, so anything placed ahead of the record
    # and the stamp above could cancel them with no trace.
    try:
      row = self._row_for_element(tile_id)
      if row is not None and row >= 0:
        self._sync_row(row)
    except Exception:
      pass

  def _replay_deferred_adoptions(self):
    """Adopt the dock edits that arrived while a run was in flight.

    Returns:
      None. Each element's captured bounds are offered to
      `_adopt_dock_bounds` once, and the store is emptied whatever the
      outcome -- an edit that cannot be adopted now will not become
      adoptable later, and keeping it would replay it after every
      subsequent run.

    WHY THE NUMBERS WERE CAPTURED rather than re-read: the landing
    RE-SEEDS each element's renderer from the record, so by the time
    this runs the layer holds the plugin's own ladder. Asking it again
    would adopt that as though a person had typed it, which is the
    fault the rest conditions exist to prevent -- reached by the other
    door, and the reason a note-to-look-again would have been worse
    than useless.

    STILL AT REST, and asserted rather than assumed: if a further run
    has started in the meantime, the guards inside `_adopt_dock_bounds`
    put the edit back into the store and this returns having done
    nothing, so the numbers survive to the next landing.
    """
    if _dialog_is_gone(self) or _live_dialog() is not self:
      return
    pending, self._adoption_deferred = self._adoption_deferred, {}
    for tile_id, (assignment, bounds, colours) in pending.items():
      try:
        self._adopt_dock_bounds(tile_id, assignment, bounds, colours)
      except Exception:
        # An exception in one element must not cost the others theirs;
        # this runs from a Qt timer, where a raise is swallowed and
        # takes the rest of the loop with it.
        continue
    # PRESERVE, DO NOT REPAINT. (Maintainer's ruling, 2026-08-19.) Two
    # settled contracts pull against each other here and this is the
    # line that reconciles them. `race: restyle during a run` requires
    # that with live update off the map is NOT refreshed on its own --
    # the table and the map may disagree until the user asks. `a dock
    # reclassification lands while a run is finishing` requires that a
    # twelve-class classify made in the dock is still ON the map
    # afterwards. Repainting satisfied the second and broke the first
    # and `a ramp chosen during a run is not lost` with it; doing
    # nothing did the reverse.
    #
    # NEITHER TEST ASKS FOR A REPAINT. What the second needs is that
    # the landing does not CLOBBER what a person left on the layer,
    # and the way this dialog already avoids that is by making the ROW
    # FOLLOW the renderer -- after which the element no longer looks
    # changed and nothing re-seeds it. That is precisely what the
    # landing does for `_preserved_this_run` a few lines above, so
    # these elements go through the same door rather than a second one
    # invented for them.
    #
    # The canvas is untouched either way, which is what live update
    # off means: the record carries the adopted bounds, and Generate
    # applies them.
    for tile_id in pending:
      lid = self._element_layer_ids.get(tile_id)
      if not lid:
        continue
      try:
        self._on_layer_style_edited(lid, tile_id)
      except Exception:
        # One element's failure must not cost the others theirs: this
        # runs from a Qt timer, where a raise is swallowed and takes
        # the rest of the loop with it.
        continue

  def _graduated_layer_edited(self, layer, tile_id, renderer):
    """React to a styling-dock edit of a GRADUATED element layer.

    Args:
      layer: the element output layer whose style changed.
      tile_id: the element it carries.
      renderer: its QgsGraduatedSymbolRenderer, already checked.

    Returns:
      None. The graduated mirror of the categorized watcher, settled
      2026-08-09: a clean classify from a named QUANTITATIVE ramp --
      source ramp recognisable, colours exactly the plugin's own
      full-window seeding -- is FOLLOWED (combo moves, range resets,
      picks destroyed with the notice); any other divergence is
      ADOPTED as positional picks, so the cell reads Custom and the
      colours survive regeneration. Categorical-family ramps never
      follow, because a graduated row auto-swaps them away and the
      combo would land elsewhere than the layer. A dock edit that
      changed the CLASS COUNT or the field is a reclassification the
      dialog has no record to reconcile against, so it is left alone
      -- the signature rule preserves it, as it always has. That
      count is measured against what the plugin would DRAW, not
      against the row's ``k``: the two differ whenever a column has
      fewer distinct values than the row asks classes for.
    """
    assignment = self._assignment_for(tile_id)
    if assignment is None or assignment["mode"] != "Graduated" \
        or not assignment["var"]:
      _dump("DROP", tile_id, "not-graduated", 
            None if assignment is None else assignment.get("mode"),
            None if assignment is None else assignment.get("var"))
      return
    if renderer.classAttribute() != assignment["var"]:
      _dump("DROP", tile_id, "field-mismatch layer=",
            renderer.classAttribute(), "row=",
            assignment["var"])
      return
    ranges = renderer.ranges()
    actual = [r.symbol().color().name() for r in ranges]
    if not actual:
      _dump("DROP", tile_id, "no-classes")
      return
    # The count is compared against what the plugin would DRAW, below,
    # and not against the row's `k`. Those are two different numbers
    # whenever the column has fewer distinct values than the row asks
    # classes for: `k` is the ask, the map honestly draws fewer, and a
    # guard reading the ask rejected every dock edit on such an
    # element -- adoption stopped silently and the user's recolour was
    # thrown away by the next restyle. Found on 2026-08-14 by
    # test_a_graduated_dock_refinement_survives_the_next_restyle, one
    # commit after the reduction it is about.
    expected = [colour for _lo, _hi, colour
                in self._current_graduated_classes(assignment)]
    if actual == expected:
      # A COLOUR COMPARISON CANNOT SEE A MOVED BREAK, and this exit
      # stood in front of everything that writes the file.
      #
      # MEASURED 2026-08-17, three fixtures and three read routes, one
      # of them reading `layer_styles.styleQML` out of the GeoPackage
      # with sqlite and no QGIS involved. Retype a class break in
      # QGIS's Symbology panel: QGIS, the plugin's map and the saved
      # .qgz all show it, and the file a colleague opens draws the
      # plugin's original ladder -- same colours, different classes.
      #
      #     what you see : [1.5, 2.0, 3.0, 4.0, 5.0]
      #     what they get: [1.0, 2.0, 3.0, 4.0, 5.0]
      #
      # Generate does not heal it: `_restyle_only` continues past an
      # element whose row never moved, before its own embed. A layer
      # opacity set in Layer Properties goes the same way, 0.25 in the
      # project and 1.0 in the file.
      #
      # The colour-only comparison dates to 2026-08-10 and is right
      # about what it is FOR -- deciding whether to adopt positional
      # picks. It was simply carrying an exit it has no business
      # deciding. So the file is brought up to date here, on the way
      # out, for every edit that reaches this line: the renderer on
      # the layer is the truth whatever our records say about colour.
      #
      # THE SHAPE, three times in one day: a guard that asks about one
      # thing standing in front of an exit that is about another. Ask
      # what a guard is FOR before deciding what it may skip.
      # THE FILE LEARNS AT SAVE (ruling of 2026-08-27). The change
      # above reaches the map, the project and the group's record
      # here; the GeoPackage is written by `_save_the_map`, in one
      # act with the record that describes it, so the two cannot
      # disagree. The paragraph above this is kept as HISTORY: it
      # argues for a write that used to happen at this line, and the
      # defect it describes is what the one-act save prevents.
      # A RETYPED BOUNDARY LANDS HERE, because moving a number moves
      # no colour, and this is the only exit concluding that nothing
      # else claimed the edit. LAST, and contained: this method runs
      # inside a Qt signal handler where an exception is SWALLOWED,
      # so anything added ahead of the work above can cancel it
      # silently.
      try:
        live = renderer.ranges()
        self._adopt_dock_bounds(
          tile_id, assignment,
          [(r.lowerValue(), r.upperValue()) for r in live], actual)
      except Exception:
        pass
      # THE LAYER NOW WEARS A LADDER WE ARE CALLING OURS, so it
      # becomes the baseline the next dock edit is judged against.
      # This exit is reached for our own seeding AND for a clean
      # Classify from a named ramp, and in both cases the plugin has
      # just agreed that what is on the layer is what it would draw.
      self._remember_painted_ladder(layer, tile_id)
      _dump("DROP", tile_id, "clean-classify")
      return  # our own seeding, or an edit that changed no colour
    if len(expected) != len(actual):
      _dump("DROP", tile_id, "count", len(expected), "vs", len(actual))
      # THE count guard, and the only one: the layer against what the
      # plugin would draw for this row. A CONSTANT column is
      # deliberately collapsed to one class here, while QGIS's own
      # Classify button happily returns five identical "7 - 7" ranges
      # over the same data. Five against one, both agreeing that k is
      # five -- which is why comparing either against `k` answers the
      # wrong question. The positional walk below then ran off the end
      # of the shorter list, inside a slot on rendererChanged -- so
      # the traceback went to a console nobody had open and adoption
      # quietly stopped for that element.
      # A reclassification the dialog has no matching record for is
      # left alone, exactly as a changed class count is; the
      # signature rule preserves it. Guarded by
      # test_a_dock_classify_on_a_constant_column_does_not_crash.
      return

    name = self._ramp_name_matching(
      renderer.sourceColorRamp(),
      prefer=self._ramp_choices.get(tile_id))
    if name is not None and name not in bridge.CATEGORICAL_RAMPS:
      # THE ROW'S REVERSE GOES IN, and leaving it out is how a forward
      # ramp set in QGIS came to "match" a row whose Reverse switch is
      # on. `_current_graduated_classes` passes it and this trial did
      # not, so the two disagreed about what the row would draw: the
      # plugin announced that the element now follows the named ramp,
      # the map was forward, the row still claimed reversed -- and the
      # next unrelated edit, asking for six classes, redrew the element
      # end for end in the project AND in the file.
      #
      # A REVERSED RAMP MATCHES NO NAME IN THE LIBRARY, which is why
      # this flag exists at all and why it keeps being dropped: every
      # comparison that reasons about ramp NAMES rather than rendered
      # COLOURS walks past it. Measured 2026-08-17. With the flag in,
      # a genuine forward ramp no longer matches the reversed row and
      # falls through to adoption as positional picks, so the cell
      # reads Custom -- which is the settled answer for colours the
      # row cannot name.
      trial = bridge.make_graduated_renderer(
        layer, assignment["var"], name, assignment.get("scheme",
                                                       "Quantiles"),
        assignment.get("k", 5), assignment.get("outline", False),
        reverse=assignment.get("reverse", False),
        classify_from=self._classification_values(assignment["var"]))
      # hold the list; range temporaries dangle (the settled lesson)
      trial_colours = [r.symbol().color().name()
                       for r in trial.ranges()]
      if actual == trial_colours:
        # cleared here as well as in the combo handler, for the same
        # reason as the categorized branch: re-applying the ramp the
        # dialog already names fires no combo signal
        self._clear_quant_customization(tile_id, "a new colour ramp")
        row = self._row_for_element(tile_id)
        combo = (self.table.cellWidget(row, 4)
                 if row is not None else None)
        if combo is not None and hasattr(combo, "findText") \
            and combo.findText(name) >= 0:
          combo.setCurrentText(name)
        self._report_quietly(
          f"Element '{tile_id}' now follows the '{name}' ramp chosen "
          f"in QGIS.")
        self._refresh_preview_colours()
        refreshed = self._assignment_for(tile_id)
        if refreshed is not None:
          self._last_signatures[tile_id] = self._signature(refreshed)
          # and the LAYER is told the picks are gone, which is the
          # half this branch never did. The dicts were cleared and
          # the user was told the ramp now governs, while the stamp
          # went on holding the discarded colours -- and the stamp is
          # what survives into the .qgz. So the pick came back on
          # reopen, silently painted over the ramp the user had
          # chosen instead, and `_last_signatures` above guaranteed
          # no restyle would ever heal it. `_stamp_category_colours`
          # clears each property when there is nothing to record,
          # which is exactly this case; its two ADOPT exits called it
          # and these two FOLLOW exits did not. Measured 2026-08-13.
          # Guarded by test_a_discarded_pick_does_not_come_back.
          # the GRADUATED half of this branch
          self._stamp_category_colours(layer, refreshed)
          # ...AND THE FILE, which this exit forgot. Its twin in
          # `_restyle_only` stamps AND embeds; these four adoption
          # exits stamped only, so a recolour made in QGIS's own
          # styling dock never reached the exported GeoPackage -- and
          # the signature recorded a moment later then made the
          # restyle path SKIP the element, so pressing Generate could
          # not heal it either. A colleague opening the file saw the
          # colours from before the edit, beside a stamp claiming the
          # new ones. Measured 2026-08-17 over 1,751 comparisons
          # between a sending project and the file a separate process
          # opened: 11 disagreements for a categorical recolour, 12
          # for a graduated one, and an element at 0.25 opacity in the
          # project and 0.85 in the file.
          # THE FILE LEARNS AT SAVE (ruling of 2026-08-27). The change
          # above reaches the map, the project and the group's record
          # here; the GeoPackage is written by `_save_the_map`, in one
          # act with the record that describes it, so the two cannot
          # disagree. The paragraph above this is kept as HISTORY: it
          # argues for a write that used to happen at this line, and the
          # defect it describes is what the one-act save prevents.
        return

    # THE LADDER FIRST, WHATEVER THE COLOURS DID. Adoption of BOUNDS
    # used to happen at one exit only -- the one concluding that
    # nothing else claimed the edit, which is to say that no colour
    # had moved. A style PASTED from another element layer moves the
    # breaks AND the colours, so it left by the door below and its
    # ladder was never adopted: the receiving element lost the pin the
    # sending one carried, silently, and the next Generate recomputed
    # its own breaks over somebody's copied classification.
    #
    # THE SHAPE IS THE ONE THIS FILE NAMES THREE TIMES: a guard that
    # asks about one thing standing in front of an exit that is about
    # another. Whether a COLOUR changed cannot decide whether a BOUND
    # was adopted. Reported by the maintainer against rc10, ledger row
    # 30; measured by pasting a's renderer onto b and reading b's
    # record, which stayed None.
    #
    # Contained for the same reason as its twin fifty lines above: an
    # exception inside a Qt slot is swallowed and would take the
    # colour adoption below with it.
    try:
      live = renderer.ranges()
      self._adopt_dock_bounds(
        tile_id, assignment,
        [(one.lowerValue(), one.upperValue()) for one in live], actual)
    except Exception:
      pass
    # adopt the divergent classes as positional picks
    field = assignment["var"]
    record = self._quant_colours.setdefault(tile_id, {}) \
        .setdefault(field, {})
    # ...BUT NEVER THE PLUGIN'S OWN TEMPLATE.
    # `make_graduated_renderer` sets the renderer's SOURCE SYMBOL to a
    # placeholder grey, and QGIS's Symbology panel clones that symbol
    # for a class the user ADDS. Measured on QGIS 4.0.3: adding a
    # class to a four-class Blues ladder inserts it AT INDEX 0 wearing
    # #c0c0c0, so the ladder reads grey, palest, pale, mid, darkest.
    # Nobody picked that grey -- QGIS copied it from us -- and
    # recording it as a hand-pick made the plugin defend its own
    # placeholder against the ramp for the life of the element. A
    # watcher may only adopt what a PERSON left behind. The
    # maintainer's dump showed exactly this, `picks` gaining
    # '0': '#c0c0c0' after a class was added in the panel: ledger
    # row 34.
    #
    # Bound to a name before it is read: a symbol reached through a
    # temporary is freed under you, which this project has already
    # paid for twice.
    # ...AND NOTHING AT ALL WHEN THE DOCK CHANGED HOW MANY CLASSES
    # THERE ARE. QGIS inserts the new class and every OTHER class
    # keeps the colour it already had, which now sits at a different
    # index -- so a positional walk sees the plugin's own previous
    # ramp sampling displaced by one and adopts the lot as somebody's
    # hand-picks. Measured from a maintainer's dump, 2026-08-20:
    # adding a class to a five-class Reds element adopted FOUR
    # colours nobody chose, after which the ramp could never govern
    # those classes again.
    #
    # THIS FUNCTION ALREADY HAD A GUARD FOR IT AND THE GUARD CANNOT
    # FIRE. `len(expected) != len(actual)` was written to leave a
    # reclassification alone, and `expected` comes from the ROW --
    # which `_row_follows_the_renderer` has just brought up to the
    # layer's new count, by a deliberate ordering added 2026-08-17 to
    # stop these handlers dropping dock edits on the floor. So the
    # two lengths agree and the walk runs. Inserting a step BEFORE a
    # handler turned its opening guard from a return into a
    # fall-through, which is the twin of a trap this project already
    # records from the other side. The caller measures the count on
    # both sides of the follow and says so.
    source = renderer.sourceSymbol()
    template = source.color().name() if source is not None else None
    adopted = 0
    unattributable = 0
    # THE WALK ASKS THE STORE, NOT THE INDEX. Bound to a name before
    # it is subscripted, for the reason recorded three times in this
    # project: a range reached through a temporary is freed under you.
    rows = renderer.ranges()
    for index, one in enumerate(rows):
      colour = one.symbol().color().name()
      # A user who genuinely wants the template's colour picks it on
      # a class QGIS did not just create, and that pick is adopted
      # by the next edit; what is declined here is a colour
      # identical to the template on the very edit that clones it.
      if colour == template:
        continue
      ours = self._colour_is_ours(
        tile_id, field, one.lowerValue(), one.upperValue(), colour)
      if ours is None:
        # NO RECORD OF THIS ELEMENT'S LADDER AT ALL, which is not the
        # same as "unchanged" and is not read as either. Declining is
        # the conservative half of the maintainer's decision of
        # 2026-08-20, and the notice below is the other half: the loss
        # is visible before the next Generate rather than after it.
        unattributable += 1
        continue
      if ours:
        continue
      if record.get(str(index)) != colour:
        record[str(index)] = colour
        adopted += 1
    _dump("ADOPTCOLOUR", tile_id, "adopted=", adopted,
          "unattributable=", unattributable,
          "known=", len((self._painted_ladders.get(tile_id) or {}).get(field)
                        or []),
          "expected=", expected, "actual=", actual)
    if unattributable:
      self._report_quietly(
        bridge.declined_colours_message(tile_id, unattributable))
    if not adopted:
      # nothing was taken up, but the ladder in front of us is still
      # what we now understand this element to be wearing
      self._remember_painted_ladder(layer, tile_id)
      return
    self._custom_swatch_cache.pop(tile_id, None)
    # the layer already wears these colours; recording the signature
    # stops the restyle path re-seeding it and discarding whatever
    # else the dock changed alongside them
    refreshed = self._assignment_for(tile_id)
    if refreshed is not None:
      self._last_signatures[tile_id] = self._signature(refreshed)
      self._stamp_category_colours(layer, refreshed)
      # ...AND THE FILE, which this exit forgot. Its twin in
      # `_restyle_only` stamps AND embeds; these four adoption
      # exits stamped only, so a recolour made in QGIS's own
      # styling dock never reached the exported GeoPackage -- and
      # the signature recorded a moment later then made the
      # restyle path SKIP the element, so pressing Generate could
      # not heal it either. A colleague opening the file saw the
      # colours from before the edit, beside a stamp claiming the
      # new ones. Measured 2026-08-17 over 1,751 comparisons
      # between a sending project and the file a separate process
      # opened: 11 disagreements for a categorical recolour, 12
      # for a graduated one, and an element at 0.25 opacity in the
      # project and 0.85 in the file.
      # THE FILE LEARNS AT SAVE (ruling of 2026-08-27). The change
      # above reaches the map, the project and the group's record
      # here; the GeoPackage is written by `_save_the_map`, in one
      # act with the record that describes it, so the two cannot
      # disagree. The paragraph above this is kept as HISTORY: it
      # argues for a write that used to happen at this line, and the
      # defect it describes is what the one-act save prevents.
    self._report_quietly(
      f"Element '{tile_id}' keeps the {adopted} colour(s) set in "
      f"QGIS; its ramp cell now reads Custom.")
    # LAST, and after the record has been written: the adopted colours
    # are now part of what this element is understood to be wearing,
    # so a second signal carrying the same ladder finds nothing new
    # rather than adopting it again.
    self._remember_painted_ladder(layer, tile_id)
    self._refresh_preview_colours()

  def _template_for(self, token):
    """The imported class scheme for one class-source token, or None.

    Args:
      token: what the class-source combo holds ("file:…", "layer:…"
        or empty).

    Returns:
      {value: (symbol, label)} or None. A broken file yields None
      rather than raising: a class source that cannot be read should
      leave the element on automatic colours, not stop the user.
    """
    if not token:
      return None
    try:
      if token.startswith("layer:"):
        return bridge.template_from_layer(
          QgsProject.instance().mapLayer(token[6:]))
      return bridge.load_categorized_template(token[5:])
    except Exception:
      return None

  def _edit_category_colours(self):
    """Open the colour editor for the row that asked.

    Returns:
      None. One button, two destinations: a categorized row opens the
      editor's categorical mode here, and a graduated row is handed
      to _edit_quant_colours, which opens the SAME window in its
      graduated dress. Either way colours picked are recorded against
      the element AND the field, applied through the ordinary restyle
      path, and checked for separability once when the window closes.

    Nothing here touches a layer. A run finishing while the window is
    open replaces every element layer, so the editor works entirely
    on the dialog's own record and lets the restyle path find whatever
    layers currently exist -- which also means a colour picked during
    a run is simply applied when that run lands.
    """
    button = self.sender()
    if button is None:
      return
    tile_id = button.property("tile_id")
    assignment = self._assignment_for(tile_id)
    if assignment is None or not assignment["var"] \
        or assignment["mode"] not in ("Categorized", "Graduated"):
      return
    field = assignment["var"]

    if assignment["mode"] == "Graduated":
      self._edit_quant_colours(tile_id, field, assignment)
      return

    colours, order = self._current_category_colours(assignment)
    if not order:
      self._report_quietly(
        f"'{field}' has no values to colour in this layer.")
      return

    def picked(value, colour):
      self._category_colours.setdefault(tile_id, {}) \
          .setdefault(field, {})[str(value)] = colour
      self._apply_style_change()

    editor = CategoryColourDialog(
      tile_id, field, order, colours, picked, self,
      copy_targets=self._copy_targets(tile_id, categorical=True),
      copy_to=lambda targets: self._copy_categories_to_many(
        tile_id, targets))
    # HELD while it is open, and only for the length of exec(), so
    # deferral beginning underneath can close it. QGIS stays live
    # while this window is modal to the plugin dialog, so a user
    # genuinely can restyle the element in the styling panel with its
    # colour editor open.
    self._open_editor = editor
    try:
      editor.exec()
    finally:
      self._open_editor = None
    self._warn_about_close_colours()

  def _edit_quant_colours(self, tile_id, field, assignment):
    """Open the colour editor in its graduated mode.

    Args:
      tile_id: the element being edited.
      field: its numeric variable.
      assignment: its dict from ``_assignments()``.

    Returns:
      None. The same window as the categorical editor, in its
      graduated dress: two read-only bound columns, editable class
      colours keyed by POSITION, and the Ramp Display Range section
      live at the top. For Quant: Unclassed the class list is shown
      locked and translucent -- fifty slivers are a preview, not an
      editing surface -- and the range alone is live (settled
      2026-08-09). Everything flows through the dialog's records and
      the ordinary restyle path, exactly as the categorical mode
      does, so it is equally safe while a run is in flight.
    """
    classes = self._current_graduated_classes(assignment)
    if not classes:
      self._report_quietly(
        f"'{field}' has no classes to colour in this layer.")
      return
    unclassed = assignment.get("scheme") == "Unclassed"
    order = [str(index) for index in range(len(classes))]
    colours = {str(index): colour
               for index, (_lo, _hi, colour) in enumerate(classes)}
    bounds = [(lower, upper) for (lower, upper, _c) in classes]

    # NO DATA IS ONE MORE ROW, and only where it means something. An
    # element with nothing missing gets no such row: a colour control
    # for a class the map does not draw is an invitation to wonder
    # which tiles it governs, and the answer would be none. Offered
    # for the classed and Unclassed graduated paths alike, since both
    # are graduated renderers and neither can place a null.
    # ONE ROW PER KIND PRESENT since 2026-08-16, not one row for all
    # of them. A NULL and an infinity are different statements -- one
    # says nobody recorded a value, the other says the value is off
    # the scale -- and the map now draws them apart, so the editor
    # that sets those colours has to offer them apart.
    picks = self._quant_colours.get(tile_id, {}).get(field, {}) or {}
    defaults = {key: fill for key, _v, _l, fill in bridge.ABSENCE_KINDS}
    for key in self._absence_kinds_for(tile_id, field):
      order.append(key)
      colours[key] = picks.get(key) or defaults[key]

    def picked(index, colour):
      # positional: "class 3 is this colour", surviving break moves
      self._quant_colours.setdefault(tile_id, {}) \
          .setdefault(field, {})[str(index)] = colour
      self._apply_style_change()

    def range_changed(lo, hi):
      # moving the range reinterpolates every class, so the picks go
      # (settled; the notice fires only when there were any). The
      # fresh colours are handed back for the editor to repaint with.
      self._clear_quant_customization(
        tile_id, "a new display range", reset_range=False)
      self._ramp_ranges[tile_id] = (int(lo), int(hi))
      self._custom_swatch_cache.pop(tile_id, None)
      self._apply_style_change()
      refreshed = self._assignment_for(tile_id)
      if refreshed is None:
        return []
      return [colour for _lo, _hi, colour
              in self._current_graduated_classes(refreshed)]

    def pin_changed(which, value):
      # The editor asks; the dialog decides. A message back means
      # REFUSED and the editor puts its control where it was, so the
      # window never shows a bound the map does not have -- reverting
      # rather than clamping, because a typed number is either
      # honoured or visibly rejected and never quietly changed into a
      # different one.
      wanted = dict(self._pinned_bounds.get(tile_id, {}).get(field) or {})
      if value is None:
        wanted.pop(which, None)
      else:
        wanted[which] = float(value)
      source = self._classification_values(field)
      values = (source.uniqueValues(source.fields().indexOf(field))
                if source is not None else [])
      problem = bridge.pin_problem(
        wanted.get("low"), wanted.get("high"), values,
        assignment.get("k", 5), wanted.get("breaks"))
      # `pin_problem` asks about the two PINS and has nothing to say
      # about an outer edge, which can neither cross another boundary
      # nor exhaust the middle. What a limit CAN do is swallow the
      # ladder: a floor above the first class's own upper bound, or a
      # ceiling below the last class's lower, leaves a class running
      # backwards -- which QGIS accepts and then draws as nothing, the
      # exact shape measured on 2026-08-17 when a pin below the
      # smallest value built a reversed range. Refused with the reason
      # said, in the terms of the control the person just moved.
      if not problem:
        problem = self._limit_problem(wanted, assignment)
      if problem:
        self._report_quietly(problem)
        return problem
      if wanted:
        self._pinned_bounds.setdefault(tile_id, {})[field] = wanted
      else:
        self._pinned_bounds.get(tile_id, {}).pop(field, None)
      self._custom_swatch_cache.pop(tile_id, None)
      self._apply_style_change()
      # A LIMIT THAT EXCLUDES CANNOT BE ANSWERED BY A REPAINT, and the
      # user has to be told when that means waiting. Setting a floor
      # or a ceiling inside the data moves tiles onto the paired
      # layer, which `_restyle_only` can neither make nor unmake, so
      # the change is GEOMETRY and needs a full run. With live update
      # on, one is already queued and nothing needs saying. With it
      # off, the number is accepted, the editor redraws around it, and
      # THE MAP DOES NOT MOVE -- which reads exactly like the control
      # not working. Measured 2026-08-19: a restated guard failed on
      # precisely this and four other explanations were killed first.
      # THE GATE THAT TELLS AND THE GATE THAT ACTS MUST ASK THE SAME
      # QUESTION, and for a day they did not. `_restyle_only` refuses
      # ANY limit edit, because the geometry signature carries the
      # floor and the ceiling as VALUES; this notice asked the
      # narrower question of whether the limits currently exclude
      # something. Every limit edit that stops excluding fell in the
      # gap: lowering a floor, or clearing it, or setting a first one
      # wide of the data, changed nothing on the map and said nothing
      # either, which reads exactly like the control not working.
      # Measured 2026-08-19 through the editor's own floor box, and
      # found by a hunt pointed at what the morning's own signature
      # fix had broken.
      if which in ("floor", "ceiling") and not self.live_check.isChecked():
        if self._limits_exclude_anything(
            self._assignment_for(tile_id) or {}):
          self._report_quietly(
            "Areas outside the limits stop being drawn on the next "
            "Generate, since leaving them out changes which tiles the "
            "map holds rather than only their colours.")
        else:
          # THE OTHER DIRECTION, which the sentence above cannot cover
          # honestly: widening a limit or giving it back does not stop
          # areas being drawn, it starts them again.
          self._report_quietly(
            "Areas the old limits left out come back on the next "
            "Generate, since which tiles the map holds is decided "
            "when it is drawn rather than when it is coloured.")
      # ...and the LADDER back, not merely "not refused". A pin
      # recomputes every break between the pinned ones, and the window
      # was built with the ladder from before that, so it went on
      # printing numbers the map no longer draws -- and offering the
      # stale one to the other pin. A string still means refused.
      settled = self._assignment_for(tile_id)
      if settled is None:
        return None
      return [(low, high) for low, high, _colour
              in self._current_graduated_classes(settled)]

    # What the scheme would compute with NOTHING pinned. The editor
    # needs it so a spin box moving off that number can pin itself and
    # moving back can unpin: without it the pin is a thing you click
    # and the two controls can disagree. Asked of the same code that
    # classifies the map, with the pins removed from the assignment --
    # `_current_graduated_classes` reads them from that dict, so
    # dropping the key is the whole of "as if nothing were pinned",
    # and self._pinned_bounds is never touched.
    unpinned = dict(assignment)
    unpinned.pop("pinned", None)
    try:
      defaults = [(low, high) for low, high, _colour
                  in self._current_graduated_classes(unpinned)]
    except Exception:
      defaults = None       # cannot say; the pin stays a click

    editor = CategoryColourDialog(
      tile_id, field, order, colours, picked, self,
      bounds=bounds, locked=unclassed, defaults=defaults,
      range_bounds=tuple(self._ramp_ranges.get(tile_id, (0, 100))),
      ramp_name=assignment["ramp"],
      reverse=assignment.get("reverse", False),
      range_changed=range_changed,
      pinned=self._pinned_bounds.get(tile_id, {}).get(field),
      pin_changed=pin_changed,
      copy_targets=self._copy_targets(tile_id),
      copy_to=lambda targets: self._copy_classification_to_many(
        tile_id, targets))
    # HELD while it is open, and only for the length of exec(), so
    # deferral beginning underneath can close it. QGIS stays live
    # while this window is modal to the plugin dialog, so a user
    # genuinely can restyle the element in the styling panel with its
    # colour editor open.
    self._open_editor = editor
    try:
      editor.exec()
    finally:
      self._open_editor = None
    self._warn_about_close_colours()

  def _copy_classification(self, source_id, target_id):
    """Send one element's whole classification to another.

    Args:
      source_id: the element whose editor is open.
      target_id: the single element to copy onto.

    Returns:
      A message when the copy was REFUSED, or None when it was made,
      which is the contract this had when a copy could name only one
      target. Kept exactly, because a dozen tests and several
      catalogue entries drive it: the loop, the single repaint and the
      composed notice all live in `_copy_classification_to_many`, and
      this is that function with a list of one.
    """
    return self._copy_classification_to_many(source_id, [target_id])

  def _distinct_values(self, field):
    """How many distinct values a column holds, or None when unknown.

    Args:
      field: the column name to count.

    Returns:
      An int, or None when no layer can answer -- in which case no
      caller may refuse anything, since absence of evidence is not
      evidence of a large number.

    Asked of `_classification_values`, which is the geometry-less
    scratch layer the whole map is classified from, so this counts the
    values a categorical style would actually DRAW rather than the
    ones one element's tiles happen to carry.
    """
    source = self._classification_values(field)
    if source is None:
      return None
    try:
      return len(source.uniqueValues(source.fields().indexOf(field)))
    except Exception:
      return None

  def _many_categories_is_wanted(self, field, count):
    """Ask before drawing one colour for every value of a large column.

    Args:
      field: the receiving column, named in the question.
      count: how many distinct values it holds.

    Returns:
      True when the user says draw it anyway, False when they decline.

    WHY THIS IS A QUESTION AND NOT A REFUSAL. A column of a hundred
    and twenty codes is a perfectly reasonable thing to categorize,
    and only the person looking at it knows whether their legend can
    carry it. What is NOT reasonable is finding out by watching QGIS
    draw three thousand swatches, which is what happened before this
    existed.

    A MODAL IS ALLOWED HERE, where the generation paths forbid one:
    this is reached from a copy somebody asked for, inside a window
    that is already modal to the dialog, so nothing is blocked that
    was not already waiting on them.
    """
    from qgis.PyQt.QtWidgets import QMessageBox
    answer = QMessageBox.question(
      self, "WeavingSpace",
      f"'{field}' holds {count:,} distinct values. Draw a colour for "
      f"each?")
    return answer == QMessageBox.StandardButton.Yes

  def _settle_retained_schemes(self):
    """Ask about a categorical scheme kept across a change of dataset.

    Returns:
      None. Elements whose retained scheme the user declines are moved
      to a style the new column can honestly carry, and the change is
      reported.

    THE SECOND DOOR INTO "TOO MANY CATEGORIES", and it shares its
    number with the first (`bridge.MANY_CATEGORIES`, asked by the copy)
    on the maintainer's ruling of 2026-08-20: one thing to explain and
    one thing to guard. A column that keeps its NAME across a change of
    region dataset keeps its element's setup -- and nothing about a
    name says the values are the same kind of thing, so a scheme cut
    for four words can meet three thousand floats and draw a colour,
    a legend line and a swatch for each.

    ONLY A SCHEME SOMEBODY CHOSE IS ASKED ABOUT. Where the plugin
    picked the style itself, `_refresh_table` has already re-derived it
    from the new column's type and there is nothing to retain; asking
    then would be asking about the plugin's own choice. So this is
    narrow by construction, which is what keeps a question from
    becoming a thing people click through.

    A MODAL IS ALLOWED HERE for the same reason it is allowed on the
    copy: the user has just picked a layer, so nothing is blocked that
    was not already waiting on them, and no generation path runs
    through this.
    """
    fields = self._layer_fields()
    if not fields:
      return
    # Grouped by COLUMN, because the question and the answer are both
    # about the column: two elements retaining a scheme on one field
    # are one question, and they take the same fallback.
    wanted = {}
    for row in range(self.table.rowCount()):
      identifier = self.table.item(row, 0)
      mode_cell = self.table.cellWidget(row, 2)
      var_cell = self.table.cellWidget(row, 1)
      if identifier is None or mode_cell is None or var_cell is None:
        continue
      if not mode_cell.property("touched"):
        continue
      if mode_cell.currentText() != "Categorized":
        continue
      field = var_cell.currentText()
      if not field or field not in fields:
        continue
      wanted.setdefault(field, []).append((row, identifier.text()))
    for field, rows in wanted.items():
      count = self._distinct_values(field)
      if count is None or count <= bridge.MANY_CATEGORIES:
        continue
      if self._many_categories_is_wanted(field, count):
        continue
      # DECLINED: the element must not be left drawing what they just
      # refused. A numeric column falls back to its plausible style,
      # which is a graduated one; a TEXT column has no quantitative
      # answer -- one never stands on a text field -- so the honest
      # fallback there is a single fill, which is the other way of
      # saying "not a colour for every value".
      instead = self._plausible_mode(field)
      if instead == "Categorized":
        instead = "Single colour"
      moved = []
      for row, tile_id in rows:
        mode_cell = self.table.cellWidget(row, 2)
        if mode_cell is None or mode_cell.findText(instead) < 0:
          continue
        mode_cell.blockSignals(True)
        mode_cell.setCurrentText(instead)
        mode_cell.blockSignals(False)
        mode_cell.setProperty("touched", False)
        mode_cell.setProperty("last_style", instead)
        # EVERY row that moved, not the first: the class-source cell
        # and the Classes spinner belong to the style, so a row left
        # unsynced goes on offering controls for a scheme it no
        # longer carries.
        self._sync_row(row)
        moved.append(tile_id)
      if moved:
        self._report_quietly(
          f"'{field}' holds {count:,} distinct values in this layer, "
          f"so {self._name_them(moved).lower()} "
          f"{'shows' if len(moved) == 1 else 'show'} it as "
          f"{instead} rather than a colour for each value.")

  def _copy_categories_to_many(self, source_id, target_ids):
    """Send one element's CATEGORICAL scheme to several others.

    Args:
      source_id: the element whose editor is open.
      target_ids: the elements to copy onto, in the order the chooser
        offered them. A list of one is the ordinary single copy.

    Returns:
      None when at least one target took the copy, or a message when
      none did. As with the graduated twin, the message is put on the
      note line here, because the editor discards what this returns.

    WHAT TRAVELS, and it is the maintainer's ruling of 2026-08-20: the
    copy OVERWRITES the target -- its style, its ramp, its Reverse, its
    per-value colours including the catch-all, and its class source,
    which travels as a FILE REFERENCE so the two elements go on
    agreeing as that file changes.

    WHAT NEVER TRAVELS, four things:

    * the VARIABLE. Carrying it would make the target a duplicate of
      the source, and a map whose whole purpose is reading several
      variables against each other would quietly lose one.
    * the OPACITY, as through every other change of scheme.
    * the OUTLINE, which decides whether tile EDGES are drawn and is
      not a colour.
    * the records of the style the row is NOT wearing -- pinned
      bounds, breaks, floor, ceiling, the remembered class count, the
      single colour. Kept, and kept SILENTLY, so a row switched back
      to a quantitative style finds its work where it left it.

    VALUES THE RECEIVING COLUMN DOES NOT HOLD ARE KEPT rather than
    dropped, on the same reasoning the graduated copy already uses: a
    copy reproduces a classification, and a silently shortened one
    does not. `make_categorized_renderer` builds the classes from the
    target's OWN values and applies an override where the value
    matches, so a colour for a value this column lacks simply waits.
    THE CASE THIS IS REALLY FOR is a column typed numeric that is
    genuinely categorical -- land-cover codes and the like -- where
    the colours land because the record keys on the value as text.

    AND IT ASKS FIRST above `bridge.MANY_CATEGORIES` distinct values,
    because a continuous column would otherwise be drawn with one
    colour, one legend line and one swatch per value.
    """
    source = self._assignment_for(source_id)
    if source is None or not source.get("var"):
      return self._say_and_return("That element has nothing to copy.")
    field = source["var"]
    picks = dict((self._category_colours.get(source_id, {})
                  .get(field) or {}))
    taken, refused, notes = [], [], []
    for target_id in target_ids:
      target = self._assignment_for(target_id)
      if target is None or not target.get("var"):
        refused.append((
          target_id,
          ("has no variable to colour; assign one first",
           "have no variable to colour; assign one first")))
        continue
      their_field = target["var"]
      count = self._distinct_values(their_field)
      if count is not None and count > bridge.MANY_CATEGORIES \
          and not self._many_categories_is_wanted(their_field, count):
        refused.append((target_id, ("was left alone", "were left alone")))
        continue
      unsent = self._write_categorical_style(
        target_id, target, source, picks)
      taken.append(target_id)
      if unsent:
        notes.append((None, unsent))
      missing = [value for value in picks
                 if value != bridge.NO_DATA_KEY
                 and not self._column_holds(their_field, value)]
      if missing:
        # A WHOLE CLAUSE NEEDS ITS OWN SENTENCE. The maintainer's
        # wording -- "kept N colours for values 'x' does not have" --
        # has its own verb, so slotting it into the frames the
        # GRADUATED copy uses for noun phrases produced "Element 'b'
        # gave up kept 5 colours..." on every copy that lost a value.
        # Measured on the composed message, 2026-08-20; the `None`
        # note is the mechanism that already exists for a sentence
        # naming its own element.
        notes.append((None,
                      f" Element '{target_id}' kept {len(missing)} "
                      f"{'colour' if len(missing) == 1 else 'colours'} "
                      f"for values '{their_field}' does not have."))

    message = self._copy_report(source_id, taken, refused, notes)
    if not taken:
      return self._say_and_return(message)
    self._apply_style_change()
    self._report_quietly(message)
    return None

  def _column_holds(self, field, value):
    """Whether a column carries this value, compared as TEXT.

    Args:
      field: the column to look in.
      value: the value key from a colour record, already a string.

    Returns:
      True when the column holds it, False when it does not, and True
      when nothing can answer -- an unknown must not be reported to
      the user as a value that failed to travel.

    COMPARED AS TEXT because that is how the record is keyed:
    `_category_colours` stores `str(value)`, which is exactly why a
    numeric column of category CODES receives a categorical copy
    perfectly well while a continuous one receives almost none of it.
    """
    source = self._classification_values(field)
    if source is None:
      return True
    try:
      held = source.uniqueValues(source.fields().indexOf(field))
    except Exception:
      return True
    return str(value) in {str(one) for one in held}

  def _write_categorical_style(self, target_id, target, source, picks):
    """Put the source's categorical scheme onto one target's row.

    Args:
      target_id: the element receiving the copy.
      target: its assignment dict, for the variable this must not touch.
      source: the sending element's assignment.
      picks: the per-value colours to write, catch-all included.

    Returns:
      None. Writes the RECORD and the ROW; the caller repaints once
      for the whole act.

    THE ROW IS MARKED AS TOUCHED, or the next rebuild throws the style
    away: `_refresh_table` restores a mode only when `style_touched` is
    set and otherwise re-derives it from the variable's type. That is
    not a fudge to get past a guard -- the flag means somebody chose
    this rather than the plugin guessing, and somebody did.
    """
    their_field = target["var"]
    # THE COPY OVERWRITES, with nothing kept back (maintainer's
    # ruling, 2026-08-20: the copy takes the per-value colours and the
    # catch-all). Writing only WHEN the source had picks left the
    # TARGET'S old hand-picks standing -- and hand-picks outrank both
    # the copied ramp and a copied QML template, so a copy from a
    # pick-less source told the user "element 'b' now uses the classes
    # from element 'a'" while b's forest stayed the old red for good,
    # stamped into every file. Found by the class-source hunt,
    # 2026-08-26, and verified at the stamp: an empty source CLEARS.
    if picks:
      self._category_colours.setdefault(target_id, {})[their_field] = \
          dict(picks)
    else:
      self._category_colours.get(target_id, {}).pop(their_field, None)
    self._custom_swatch_cache.pop(target_id, None)
    row = self._row_for_element(target_id)
    if row is None or row < 0:
      return
    mode_cell = self.table.cellWidget(row, 2)
    if mode_cell is not None and hasattr(mode_cell, "findText") \
        and mode_cell.findText("Categorized") >= 0:
      mode_cell.blockSignals(True)
      mode_cell.setCurrentText("Categorized")
      mode_cell.blockSignals(False)
      mode_cell.setProperty("touched", True)
      mode_cell.setProperty("last_style", "Categorized")
      # ...AND THE ROW IS BROUGHT INTO LINE BEFORE ANYTHING ELSE IS
      # WRITTEN INTO IT. The class-source cell EXISTS ONLY ON A
      # CATEGORIZED ROW, so a target that was quantitative a moment
      # ago has no widget in column 7 -- and the class source, which
      # the maintainer's ruling says travels, was written into `None`
      # and lost without a word. The sync also swaps the ramp combo
      # between the quantitative and categorical families, which is
      # why it belongs above the ramp rather than below it.
      self._sync_row(row)
    ramp_cell = self.table.cellWidget(row, 4)
    wanted = source.get("ramp")
    if ramp_cell is not None and wanted and hasattr(ramp_cell, "findText") \
        and ramp_cell.findText(wanted) >= 0:
      ramp_cell.blockSignals(True)
      ramp_cell.setCurrentText(wanted)
      ramp_cell.blockSignals(False)
    switch = self._row_reverse(row)
    if switch is not None:
      switch.blockSignals(True)
      switch.setChecked(bool(source.get("reverse")))
      switch.blockSignals(False)
    # THE CLASS SOURCE TRAVELS AS A REFERENCE, which is what makes the
    # copy reproduce colours a FILE governs (maintainer's ruling,
    # 2026-08-20). The cost is accepted and worth knowing: both
    # elements now depend on that one file, so if it moves, two lose
    # their colours rather than one.
    token = source.get("class_source")
    file_cell = self.table.cellWidget(row, 7)
    # ...AND A SOURCE WITH NO CLASS SOURCE CLEARS THE TARGET'S. The
    # overwrite ruling (2026-08-20, extended by row 31 of the
    # 2026-08-26 ledger for the hand-picks) names the class source
    # among what a copy carries -- and a QML template left standing
    # outranks the copied ramp exactly as the surviving picks did, so
    # a copy onto a QML-governed element said "now uses the classes
    # from element 'a'" while every QML colour stayed on the map and
    # in every record. Found by the seams hunt of 2026-08-26 (round
    # nine), one rung below row 31's fix.
    if not token:
      self._class_choices.pop(target_id, None)
      if file_cell is not None and hasattr(file_cell, "setCurrentIndex"):
        file_cell.blockSignals(True)
        file_cell.setCurrentIndex(0)
        file_cell.blockSignals(False)
    if token and file_cell is not None and hasattr(file_cell, "findData"):
      # A FIRST DRAFT ALSO OFFERED THE TOKEN HERE when the receiving
      # combo had never heard of it, on the theory that a project
      # reopened tomorrow would hand over a file nobody browsed in this
      # session. MEASURED 2026-08-20, that state cannot arise: the six
      # custom properties read back off a layer are output, tile_id,
      # category_colours, quant_style, no_data and outline, and NONE of
      # them is the class source -- so `_class_choices` is only ever
      # written from a widget, and every row's list is built from the
      # same session-wide pool. Given the fix, it would have been dead
      # code reading as protection. It becomes real the day a class
      # source is stamped and restored; the `else` below is what stays,
      # because a `layer:` token whose layer has left the project is
      # reachable now.
      where = file_cell.findData(token)
      if where >= 0:
        file_cell.blockSignals(True)
        file_cell.setCurrentIndex(where)
        file_cell.blockSignals(False)
        self._class_choices[target_id] = token
      else:
        # A `layer:` token whose layer has left the project, or whose
        # renderer is no longer categorized: there is nothing to point
        # at, and the target keeps the source it had. Said rather than
        # swallowed -- the colours arrived and the reference did not,
        # so the two elements will drift the moment that file changes.
        return (f" Element '{target_id}' took the colours but not the "
                f"class source, which is no longer offered here.")
    return None

  def _copy_classification_to_many(self, source_id, target_ids):
    """Send one element's classification to several others at once.

    Args:
      source_id: the element whose editor is open.
      target_ids: the elements to copy onto, in the order the chooser
        offered them. A list of one is the ordinary single copy.

    Returns:
      None when at least one target took the copy, or a message when
      NONE did -- either because the source has nothing to send, or
      because every target refused. The message is also put on the
      note line here rather than left to the caller: the editor
      discards what this returns, so a refusal returned and not
      reported was a refusal nobody saw.

    ONE REPAINT AND ONE NOTICE FOR THE WHOLE ACT. Copying onto four
    elements is one thing a person did, so it restyles once and says
    one thing; the alternative is four repaints and four bar messages,
    which on a table of twenty-three elements is also the slowness
    this project has open against it.

    A PARTIAL SUCCESS IS NEVER REPORTED AS A SUCCESS. (Maintainer's
    ruling, 2026-08-19, and it is the shape this project keeps
    meeting.) Each target is judged alone; the ones that can take the
    copy do; and the notice names the elements that took it and then
    each that did not, with its own reason. Never a bare count.
    """
    source = self._assignment_for(source_id)
    if source is None:
      return self._say_and_return("That element has nothing to copy.")
    classes = self._current_graduated_classes(source)
    if not classes:
      return self._say_and_return("This element has no classes to copy.")
    # the INTERIOR boundaries: the outer edges belong to whichever
    # column receives them, which is what fitted_breaks decides
    interior = [upper for _lo, upper, _c in classes[:-1]]
    if not interior:
      return self._say_and_return("A single class has no breaks to copy.")

    taken, refused, notes = [], [], []
    for target_id in target_ids:
      outcome = self._copy_onto_one(source_id, source, classes,
                                    interior, target_id)
      if outcome["refusal"]:
        refused.append((target_id, outcome["refusal"]))
        continue
      taken.append(target_id)
      if outcome["lost"]:
        notes.append((target_id, outcome["lost"]))
      if outcome["left_behind"]:
        notes.append((None, outcome["left_behind"]))

    # ONE COMPOSER FOR BOTH OUTCOMES, and the first draft had two. The
    # all-refused arm joined the reasons with a space, so three
    # targets sharing one reason produced that sentence three times,
    # each without a subject -- measured by a probe before any guard
    # was written for this. A second composer for the unhappy path is
    # how the unhappy path comes to read worse than the happy one.
    message = self._copy_report(source_id, taken, refused, notes)
    if not taken:
      # nothing was written, so nothing needs repainting; the reasons
      # are the whole of what the user has to act on
      return self._say_and_return(message)
    self._apply_style_change()
    self._stamp_what_was_copied(taken)
    self._report_quietly(message + self._copy_needs_a_generate(source_id))
    return None

  def _stamp_what_was_copied(self, taken):
    """Put each copied record onto its own layer, whatever the restyle did.

    Args:
      taken: the elements that received the copy.

    Returns:
      None. Writes `weavingspace_quant_style` through the same method
      the restyle and the landing use, so there is one spelling of
      what a stamp contains rather than two.

    IT EXISTS BECAUSE CARRYING LIMITS MOVED THE COPY ONTO A PATH THAT
    REFUSES IT. A floor or a ceiling is a GEOMETRY change -- excluding
    values moves tiles onto the paired layer, which `_restyle_only`
    can neither make nor unmake -- so once a copy carries the range,
    the restyle correctly declines the element AND the stamp, which
    the restyle is what writes. Measured 2026-08-19: a copy of breaks
    alone came back stamped, and the identical copy carrying a floor
    and a ceiling wrote the record and stamped nothing, so the copy
    reached the map and died at the next reopen.
    THAT IS LEDGER ROW 9 ARRIVING BY A NEW DOOR, and the door was one
    I opened the same afternoon. Nothing on a renderer records that a
    break was CHOSEN rather than computed, so the stamp is all a
    reopened project has.
    Stamping unconditionally rather than only where the restyle
    declined is deliberate: the two cases are told apart by a
    signature comparison fifteen hundred lines away, and a fix that
    has to predict that comparison is a fix that breaks when it moves.
    Writing the same JSON twice costs nothing.
    """
    project = QgsProject.instance()
    for tile_id in taken:
      layer = project.mapLayer(self._element_layer_ids.get(tile_id) or "")
      if layer is None:
        continue
      refreshed = self._assignment_for(tile_id)
      if refreshed is not None:
        self._stamp_category_colours(layer, refreshed)

  def _copy_needs_a_generate(self, source_id):
    """Say so when the copy cannot reach the map until Generate.

    Args:
      source_id: the element the classification came from, whose
        record decides whether limits travelled at all.

    Returns:
      A sentence to append to the copy's notice, or "" when the map is
      already showing the result.

    THE SAME HARM AS LEDGER ROW 12, from a new direction. Once the
    limits are in the geometry signature, a copy carrying them is a
    re-tile rather than a repaint, so with live update off the map
    does not move until the user asks. Saying nothing there reads
    exactly like the control not working, which is the harm the notice
    beside `pin_changed` exists to prevent -- and a copy is the
    quieter case of the two, since the row's numbers all change while
    the map stays where it was.
    """
    source = self._assignment_for(source_id)
    record = (self._pinned_bounds.get(source_id, {}).get(
      (source or {}).get("var")) or {}) if source else {}
    if record.get("floor") is None and record.get("ceiling") is None:
      return ""
    return (" The range travelled with them, so the map catches up at "
            "the next Generate: leaving areas out changes which tiles "
            "it holds rather than only their colour.")

  def _say_and_return(self, message):
    """Put a copy's refusal on the note line and hand it back.

    Args:
      message: the sentence explaining why nothing was copied.

    Returns:
      That same message, so the caller can return it unchanged.

    IT EXISTS BECAUSE A RETURNED REFUSAL WAS A SILENT ONE. The colour
    editor calls the copy through a lambda and discards what comes
    back, and every refusal here used to be a bare `return "..."`, so
    a user who asked for a copy the plugin would not make was told
    nothing at all. It was nearly unreachable while `_copy_targets`
    filtered out everything that could refuse; carrying limits makes
    it reachable, since a range can empty a column the chooser was
    perfectly right to offer.
    """
    self._report_quietly(message)
    return message

  def _copy_report(self, source_id, taken, refused, notes):
    """What to say about a copy, however many elements it touched.

    Args:
      source_id: the element the classification came from.
      taken: the elements that took the copy, in the order tried.
      refused: [(tile_id, why)] for the elements that could not, where
        `why` is a (singular, plural) pair so that several elements
        refused for ONE reason are named in one sentence rather than
        given that sentence each.
      notes: [(tile_id or None, phrases)] -- what each element gave
        up, and any bound left behind, which already names its own
        elements and so carries None.

    Returns:
      The whole message, ready for the bar. The single-target wording
      is preserved to the comma, since it is what several tests read
      and what every user of this control has met until today.
    """
    if len(taken) == 1 and not refused:
      lost = [phrases for tid, phrases in notes if tid == taken[0]]
      behind = "".join(phrase for tid, phrase in notes if tid is None)
      return (f"Element '{taken[0]}' now uses the classes from element "
              f"'{source_id}'"
              + (f", replacing {' and '.join(lost[0])}." if lost else ".")
              + behind)

    parts = []
    if taken:
      verb = "now uses" if len(taken) == 1 else "now use"
      parts.append(f"{self._name_them(taken)} {verb} the classes from "
                   f"element '{source_id}'.")
    elif refused:
      parts.append("Nothing was copied.")
    for tile_id, phrases in notes:
      if tile_id is None:
        parts.append(phrases.strip())
      else:
        parts.append(f"Element '{tile_id}' gave up "
                     f"{' and '.join(phrases)}.")
    # ...the refusals GROUPED BY REASON, so three elements a single
    # range excludes are named together. Repeating one sentence per
    # element reads as three separate problems and buries the one that
    # is actually there.
    grouped = {}
    for tile_id, why in refused:
      grouped.setdefault(why, []).append(tile_id)
    for why, ids in grouped.items():
      singular, plural = why
      parts.append(f"{self._name_them(ids)} "
                   f"{singular if len(ids) == 1 else plural}")
    return " ".join(parts)

  @staticmethod
  def _name_them(ids):
    """Elements named the way a person would say them.

    Args:
      ids: the tile ids, in the order they should be read.

    Returns:
      "Element 'b'", "Elements 'b' and 'c'", or "Elements 'b', 'c' and
      'd'", capitalised because every caller starts a sentence with
      it. No Oxford comma: this project's prose is Canadian on that
      point as on its spelling.
    """
    quoted = [f"'{tile_id}'" for tile_id in ids]
    word = "Element" if len(quoted) == 1 else "Elements"
    if len(quoted) <= 2:
      return f"{word} {' and '.join(quoted)}"
    return f"{word} {', '.join(quoted[:-1])} and {quoted[-1]}"

  def _copy_onto_one(self, source_id, source, classes, interior,
                     target_id):
    """Write one source's classification onto one target.

    Args:
      source_id: the element the classification came from.
      source: that element's row of `_assignments`, already read.
      classes: its (lower, upper, colour) triples, already computed.
      interior: its interior boundaries, already computed.
      target_id: the element receiving them.

    Returns:
      {"refusal": a sentence or None, "lost": [phrases], "left_behind":
      a sentence or ""}. It REPAINTS NOTHING and SAYS NOTHING: the
      caller restyles once for the whole act and composes one notice,
      so that copying onto four elements is not four repaints and four
      messages.

    NOTHING IS TOUCHED ON A REFUSED TARGET, which is why every check
    happens before the first write. The style used to be put on the
    row first, and a refusal after that point would have left the
    target on the source's style with none of its numbers.

    WHAT TRAVELS: the class breaks, the colours, the class count, the
    style (so an Unclassed source makes its target Unclassed, which
    is the only way "breaks and number of classes" can be honoured in
    both directions) and the PIN FLAGS. The flags travel separately
    from the values, and that difference is what makes a copy behave:
    copying from an element with no pins leaves the target's breaks
    hand-set and neither end pinned, so its swatch draws no box.
    Collapsing the two would make every copy look fully pinned and
    leave "unpin" with nothing coherent to do (settled 2026-08-14).

    AND THE FLOOR AND THE CEILING, added 2026-08-19 with the chooser
    that names several targets. They had never travelled, and the
    record was written wholesale, so a copy both failed to bring the
    source's range and destroyed whatever range the target had. That
    is a defect rather than a gap: a copy claims to reproduce a
    classification, and since 2026-08-19 the ladder's outer edges are
    part of one. It also mattered more than it looked, because the
    case that justified letting a bound sit outside the data at all
    was giving ONE PAIR OF LIMITS TO SEVERAL VARIABLES -- which is
    this act, and which the copy could not do.

    An edge is NOT checked the way a pin is, and the asymmetry is the
    rule rather than an oversight: a limit outside the receiving
    column draws perfectly well, its outer class simply going
    undisplayed, and refusing it would undo the ruling of 2026-08-17.
    The ONE thing refused is a range that leaves the receiving column
    with no drawable value at all, since that is an element with no
    classes, drawing flat, with no control on the row naming the
    number that did it. Asked through `bridge.limits_leave_nothing`,
    the same function `_retire_an_undrawable_pin` asks, so the copy
    cannot write limits the next reconciliation silently drops.

    TWO THINGS DO NOT TRAVEL, both added 2026-08-15 after a hunt.
    A pin flag is CHECKED against the receiving column first, because
    a pin is a claim about this element's own data and this was the
    one route by which an unchecked bound could arrive; a bound the
    receiving column cannot reach is left behind and said, and the
    ladder still travels whole. And an Unclassed source's class count
    does not travel at all: its fifty is fixed by the style rather
    than chosen by anybody, and `_class_counts` is the record that
    means CHOSEN -- written there, it was clamped to twenty at the
    next rebuild and replaced a count the user had picked.

    THE PIN IS JUDGED AGAINST THE POOL THE LIMITS LEAVE, which is the
    maintainer's ruling of 2026-08-19 arriving at a third door. Rows
    13 fixed it at the two sites that then existed; carrying limits
    through a copy opens another, and asking the un-narrowed question
    here would put a pin in the record that the map does not draw and
    that the next retirement pass drops without a word.

    The receiving element's own extremes fit the ends, in
    bridge.fitted_breaks; classes its data cannot reach are KEPT
    rather than dropped, because a copy reproduces a classification
    and a silently shortened one does not. Until 2026-08-17 the
    swatch also hatched them; the mark is gone on the maintainer's
    ruling and the emptiness is reported in words alone.

    What was replaced is REPORTED rather than asked about, which is
    how every other loss in this plugin is handled.
    """
    target = self._assignment_for(target_id)
    if target is None or not target.get("var"):
      # A REFUSAL IS A (singular, plural) PAIR, so `_copy_report` can
      # name several elements refused for ONE reason in one sentence.
      # Each half is a clause completing "Element 'b' ..." rather than
      # a whole sentence, since the composer supplies the subject and
      # a reason with its own subject cannot be grouped.
      return {"refusal": ("has no variable to classify, so it was "
                          "left out.",
                          "have no variable to classify, so they were "
                          "left out."),
              "lost": [], "left_behind": ""}
    field = target["var"]

    # EVERY JUDGEMENT BEFORE THE FIRST WRITE, so a refused target is
    # left exactly as it was. The style used to be put on the row
    # before the record was built, which was safe only while nothing
    # after that point could refuse.
    target_source = self._classification_values(field)
    target_values = (
      target_source.uniqueValues(target_source.fields().indexOf(field))
      if target_source is not None else [])

    source_record = self._pinned_bounds.get(source_id, {}).get(
      source.get("var")) or {}
    floor = source_record.get("floor")
    ceiling = source_record.get("ceiling")
    if bridge.limits_leave_nothing(target_values, floor, ceiling):
      # NAMED IN TERMS OF THE RANGE, because that is the thing the
      # user can move. "This element cannot take the copy" would be
      # true and useless: the range is on the SOURCE, so the fix is
      # over there rather than on the element being complained about.
      if floor is not None and ceiling is not None:
        shown = f"{float(floor):g} to {float(ceiling):g}"
      elif floor is not None:
        shown = f"starting at {float(floor):g}"
      else:
        shown = f"ending at {float(ceiling):g}"
      return {"refusal": (f"holds no values inside the range {shown}, "
                          f"so it was left out.",
                          f"hold no values inside the range {shown}, "
                          f"so they were left out."),
              "lost": [], "left_behind": ""}

    # ...what the target is about to lose, named before it goes
    lost = []
    if self._quant_colours.get(target_id, {}).get(field):
      lost.append("its hand-picked colours")
    if self._pinned_bounds.get(target_id, {}).get(field):
      lost.append("its pinned bounds")
    if self._class_counts.get(target_id) not in (None, source.get("k")):
      lost.append(f"its class count of {self._class_counts[target_id]}")

    # The fifty of Unclassed is a property of the style, not a count
    # somebody picked, and the two records below treat it differently.
    unclassed_source = source.get("scheme") == "Unclassed"

    # THE STYLE GOES FIRST, and the order is not cosmetic: putting a
    # row on another style releases any copied ladder it carries (a
    # copy is made for one scheme and one count), so setting the
    # style AFTER writing the record made the copy release the very
    # ladder it had just written. Measured, 2026-08-14: the copy
    # reported success and changed nothing on the map.
    self._copy_style_to_row(target_id, source.get("mode_raw"))
    record = {"breaks": [float(b) for b in interior]}
    # THE OUTER EDGES, carried whole and unchecked. A floor or ceiling
    # names where the ramp starts and stops; it moves no boundary,
    # takes no class out of the pool the scheme cuts from, and cannot
    # be refused for crossing anything -- which is why it lives in its
    # own registry rather than joining the pins. Out of the receiving
    # column's own range is FINE and is the whole point: that is how
    # one pair of limits comes to mean the same numbers on several
    # maps. The only range this refuses was refused above, before
    # anything was written.
    for edge in ("floor", "ceiling"):
      if source_record.get(edge) is not None:
        record[edge] = float(source_record[edge])
    # ...each PIN FLAG checked against the receiving column, because a
    # pin is a claim about this element's own data and the copy is the
    # only route by which one could arrive unexamined. The pin path
    # puts every typed bound through pin_problem first; this path did
    # not, so copying between elements carrying different variables
    # wrote a bound the plugin refuses when typed -- measured
    # 2026-08-15, a low of 72.6 landing on a column running 0 to 11.
    # The LADDER still travels whole, unreachable classes and all,
    # since reproducing a classification is what a copy is for; what
    # cannot travel is the claim that this element's user chose that
    # bound for this element's data. A dropped flag simply means the
    # copy no longer degrades to a pin: a later class count or scheme
    # retires it entirely and the element classifies its own values.
    #
    # AGAINST THE POOL THE LIMITS LEAVE, never the whole column.
    # (Maintainer's ruling, 2026-08-19, ledger row 13.) That ruling
    # brought two sites into step; carrying the limits through a copy
    # opens a third, and asking the un-narrowed question here would
    # accept a pin the map does not draw and that the next retirement
    # pass drops in silence -- which is exactly the harm row 13 was.
    judged = [value for value in target_values
              if bridge.absence_kind(value, record.get("floor"),
                                     record.get("ceiling"))
              != bridge.OUTSIDE_RANGE_KEY]
    dropped = []
    for end in ("low", "high"):
      if source_record.get(end) is None:
        continue
      wanted = float(source_record[end])
      trial = {"low": None, "high": None}
      trial[end] = wanted
      if bridge.pin_problem(trial["low"], trial["high"], judged,
                            source.get("k", 5)):
        dropped.append(end)
        continue
      record[end] = wanted
    # reported apart from `lost`, which says what the TARGET gave up:
    # a pin left behind is something the copy did not bring, and
    # folding the two together would tell the user they had lost a
    # bound they never set
    left_behind = ""
    if dropped:
      ends = " and ".join("lower" if end == "low" else "upper"
                          for end in dropped)
      left_behind = (
        f" The pinned {ends} "
        f"{'bounds from' if len(dropped) > 1 else 'bound from'} "
        f"element '{source_id}' "
        f"{'do' if len(dropped) > 1 else 'does'} not fit the values "
        f"element '{target_id}' holds, so "
        f"{'they were' if len(dropped) > 1 else 'it was'} left behind.")
    self._pinned_bounds.setdefault(target_id, {})[field] = record

    # the colours, positionally, which is what makes the row Custom
    # -- AND THE CATCH-ALL WITH THEM. The categorical copy carries the
    # catch-all by the ruling of 2026-08-20, and on 2026-08-26 the
    # maintainer ruled the graduated copy behaves the same: a copy
    # reproduces the classification's whole appearance, and the twin
    # layer's No data colour is part of how the element looks. The
    # absence picks live under non-digit keys beside the positional
    # ones, so they ride the same dict.
    # ...READ UNDER THE SOURCE'S OWN FIELD, never the target's. The
    # source's picks live where its variable filed them; asked under
    # `field` (the TARGET's variable) this read answered {} whenever
    # the two differed -- so the catch-all never travelled on the
    # ordinary cross-field copy -- and answered a STALE kept record
    # when the source happened to hold idle work for the target's
    # column, importing a colour nobody chose for this copy. The
    # categorical twin (`_copy_categorical_scheme`) and the pin read
    # a few lines above both already ask under the source's var.
    self._quant_colours.setdefault(target_id, {})[field] = {
      **{key: colour for key, colour in
         (self._quant_colours.get(source_id, {})
          .get(source.get("var")) or {}).items()
         if not key.isdigit()},
      **{str(index): colour
         for index, (_lo, _hi, colour) in enumerate(classes)}}
    # ...EXCEPT the fifty of an Unclassed source, which is fixed by
    # the definition of that style rather than chosen by anybody.
    # `_class_counts` means "chosen" -- the comment at the spinner
    # says so, and test_an_unclassed_excursion_leaves_the_count_alone
    # guards the same rule against a different route. Writing 50 here
    # let it through the newer one: the next table rebuild clamps a
    # count the controls cannot express, so a user who had chosen
    # four classes and copied from an Unclassed element came back to
    # a classed style redrawn in twenty, with nothing said. Measured
    # 2026-08-15: map 4, spinner 4, record 4 before the copy; map 12,
    # spinner 20, record 50 after a later design change.
    if not unclassed_source:
      self._class_counts[target_id] = len(classes)
    self._ramp_choices[target_id] = source.get("ramp")
    self._reverse_choices[target_id] = bool(source.get("reverse"))
    # THE CONTROLS TOO, and not only the records behind them. Until
    # 2026-08-15 a copy wrote _class_counts and _ramp_choices and left
    # the widgets alone, while `_assignments` reads the WIDGET -- so a
    # copy of seven classes left the map with seven, the spinner
    # showing five, the assignment claiming five and _class_counts
    # holding seven. Four descriptions of one setting, and the
    # reopened project produced a fifth reading. It is the same
    # three-numbers-for-one-setting fault
    # test_an_unclassed_excursion_leaves_the_count_alone guards, found
    # by a hunt pointed at "which of two records wins".
    self._sync_target_controls(
      target_id,
      None if unclassed_source else len(classes),
      source.get("ramp"), bool(source.get("reverse")))
    self._custom_swatch_cache.pop(target_id, None)
    # NO REPAINT AND NO NOTICE HERE. Both belong to the whole act
    # rather than to one target of it, so the caller restyles once and
    # composes one sentence; doing either per target turns a copy onto
    # four elements into four repaints and four bar messages, of which
    # the reader sees only the last.
    return {"refusal": None, "lost": lost, "left_behind": left_behind}

  def _sync_target_controls(self, tile_id, classes, ramp, reverse):
    """Put a copy's target row's own controls where the copy left it.

    Args:
      tile_id: the element that received the copy.
      classes: how many classes it now draws, or None when the copy
        came from an Unclassed source -- whose fifty is fixed by the
        style rather than chosen, and must not be written onto a row
        whose spinner means "chosen". The ramp and the reverse flag
        still travel in that case; only the count is withheld.
      ramp: the ramp name it now uses.
      reverse: whether that ramp runs the other way.

    Returns:
      None. Signals are blocked while each control is moved, and the
      records are written directly afterwards: the handlers behind
      these widgets clear hand-picked colours and release copied
      ladders, which is right when a USER moves them and wrong when a
      copy has just written the very thing they would clear.

    A number the widget does not know about is a number `_assignments`
    cannot read: it takes the class count from the spin box's own
    `user_k` property, so a record written without the widget leaves
    the row describing a map nobody made.
    """
    row = self._row_for_element(tile_id)
    if row is None:
      return
    spin = self.table.cellWidget(row, 3)
    if spin is not None and hasattr(spin, "setValue") \
        and classes is not None and 2 <= int(classes) <= 20:
      spin.blockSignals(True)
      spin.setValue(int(classes))
      spin.setProperty("user_k", int(classes))
      spin.blockSignals(False)
      self._class_counts[tile_id] = int(classes)
    combo = self.table.cellWidget(row, 4)
    if combo is not None and hasattr(combo, "findText") and ramp:
      index = combo.findText(ramp)
      if index >= 0:
        combo.blockSignals(True)
        combo.setCurrentIndex(index)
        combo.blockSignals(False)
    box = self._row_reverse(row)
    if box is not None and hasattr(box, "setChecked"):
      box.blockSignals(True)
      box.setChecked(bool(reverse))
      box.blockSignals(False)

  def _copy_style_to_row(self, tile_id, mode_raw):
    """Put a target row's Style cell on the source's entry.

    Args:
      tile_id: the element receiving the copy.
      mode_raw: the source row's literal Style text, e.g.
        "Quant: Unclassed".

    Returns:
      None. The style travels with the breaks, because fifty
      hand-set breaks on a row whose spinner caps at twenty is the
      three-numbers-for-one-setting fault
      test_an_unclassed_excursion_leaves_the_count_alone guards.
      Driven through the combo's own ``activated`` signal, which is
      what marks a style as the user's choice: a bare setCurrentText
      leaves the next design rebuild free to revert it.
    """
    row = self._row_for_element(tile_id)
    combo = self.table.cellWidget(row, 2) if row is not None else None
    if combo is None or not hasattr(combo, "findText") or not mode_raw:
      return
    index = combo.findText(mode_raw)
    if index < 0:
      return
    combo.setCurrentIndex(index)
    combo.activated.emit(index)

  def _release_copied_breaks(self, tile_id, because):
    """Drop a copied ladder, keeping the pins that came with it.

    Args:
      tile_id: the element whose classification is being recomputed.
      because: what the user just did, named in the notice.

    Returns:
      None. Says so only when something was actually released.

    A COPY DEGRADES TO ITS PINS rather than to nothing. The copied
    boundary VALUES were chosen for a particular class count and a
    particular set of breaks, so a new count retires them; the pin
    FLAGS and the two bounds they name are a smaller and more durable
    statement, and they survive, with the scheme recomputing the
    middle around them. That is the pin mechanism doing exactly its
    job, and it is why the record holds the two separately (settled
    2026-08-14).
    """
    # ONLY THE FIELD THE ACT IS ABOUT. Every call site of this method
    # is an act on the row's CURRENT field -- a class count moved, a
    # scheme chosen, a ladder adopted from the panel -- and the ruling
    # of 2026-08-20 keeps the records of every OTHER field silently.
    # Until 2026-08-26 this loop released every field's ladder, so a
    # class count changed while showing v2 destroyed a ladder copied
    # for v1, and the return to v1 drew re-derived breaks under the
    # surviving copied colours. Found by the shelf hunt, confirmed by
    # the style door independently. Where the row cannot be found the
    # old whole-element behaviour stands, which can only ever release
    # too much rather than corrupt.
    acted_on = None
    row_now = self._row_for_element(tile_id)
    if row_now is not None and row_now >= 0:
      var_combo = self.table.cellWidget(row_now, 1)
      if var_combo is not None:
        acted_on = var_combo.currentText() or None
    for field, record in list(
        self._pinned_bounds.get(tile_id, {}).items()):
      if acted_on is not None and field != acted_on:
        continue
      if not record.get("breaks"):
        continue
      # The outer edges go WITH the breaks rather than surviving like
      # the pins. A floor and a ceiling adopted from a retyped ladder
      # describe THAT ladder -- they were the ends of a particular set
      # of boundaries at a particular count -- so a new class count
      # retires them alongside the boundaries they bounded. A pin is
      # the smaller and more durable statement and is what survives,
      # which is this rule's whole shape (settled 2026-08-14, extended
      # to the ends 2026-08-19).
      kept = {key: value for key, value in record.items()
              if key in ("low", "high")}
      if kept:
        self._pinned_bounds[tile_id][field] = kept
      else:
        self._pinned_bounds[tile_id].pop(field, None)
      self._custom_swatch_cache.pop(tile_id, None)
      self._report_quietly(
        f"Element '{tile_id}' had classes copied from another element, "
        f"and {because} recomputes them"
        + (". Its pinned bounds are kept." if kept else "."))
      # ...AND THE ROW IS TOLD, at the ONE site that retires a ladder,
      # rather than at each of the three that call it. The Style cell
      # reads "Custom" while `breaks` are in force and is decided in
      # `_sync_row`, whose callers are the dynamic-column pass and the
      # deferral refresh -- so retiring the record left the cell
      # saying the ladder was somebody's when it had just been given
      # back to the scheme, a state with no control to leave it by.
      #
      # ORDERING IS WHY THIS CANNOT LIVE IN THE CALLER. `_on_mode_chosen`
      # and `_queue_live` are both connected to the same `activated`
      # signal, so the sync can run BEFORE the retirement and read the
      # record it is about to change. At the owner of the record, the
      # two cannot be out of order.
      try:
        row = self._row_for_element(tile_id)
        if row is not None and row >= 0:
          self._sync_row(row)
      except Exception:
        pass

  def _copy_targets(self, source_id, categorical=False):
    """The elements this one's classification may be copied to.

    Args:
      source_id: the element whose editor is open.
      categorical: True when the scheme being sent is a CATEGORICAL
        one, which overwrites the target's style outright and so may
        go to an element drawn any way at all. False -- the default --
        for a graduated copy, which sends a class ladder and therefore
        offers only the elements a ladder means something to.

    Returns:
      [(tile_id, label)] in table order: every OTHER element carrying
      a variable, filtered by `categorical` as above. An
      element with no variable is left out too, having no column to
      classify. Empty when there is nobody to copy to, and the editor
      then builds no dropdown at all rather than offering a control
      that can do nothing.
    """
    targets = []
    for assignment in self._assignments():
      tile_id = assignment.get("id")
      if tile_id == source_id or not assignment.get("var"):
        continue
      # A CATEGORICAL COPY OVERWRITES THE TARGET'S STYLE, so every
      # element carrying a variable is a candidate whatever it is drawn
      # as now; a graduated copy sends a class LADDER, which means
      # nothing to a categorized row, so that half keeps its filter.
      # (Maintainer's ruling, 2026-08-20.)
      if not categorical and assignment.get("mode") != "Graduated":
        continue
      targets.append((tile_id, f"{tile_id} \u2013 {assignment['var']}"))
    return targets

  def _apply_style_change(self):
    """Repaint after a symbology change, without re-tiling.

    Returns:
      None. Falls through quietly when there is nothing on the map
      yet, or a run is in flight -- in the latter case the change is
      already recorded and the finishing run will seed it. And when
      this dialog has been RETIRED, because a plugin the user has
      disabled paints nothing.
    """
    # A RETIRED DIALOG PAINTS NOTHING. Closing the colour editor at
    # `retire()` is what a person meets, and this is the other door
    # into the same room: the editor writes to this dialog's records
    # and calls back here, so an object that outlives the plugin -- a
    # window Qt has hidden but not destroyed, a timer, a lambda on a
    # layer -- could still reach the map. Every long-lived handler
    # here already asks this first; the styling path did not, which is
    # how a disabled plugin repainted an element and restamped the
    # group's record on 2026-08-28.
    if _dialog_is_gone(self):
      _dump("RESTYLE", "dialog-retired")
      return
    # THE RESTYLE GOES FIRST, and it used to be the whole of this
    # method. The swatch asked the ELEMENT'S OWN LAYER which classes
    # nothing wears, so painting it before the layer was restyled
    # asked the question of the previous map -- measured 2026-08-15,
    # a ladder copied from a 0-121 column onto an 0-11 one left three
    # classes unreachable and the swatch was built and cached with no
    # mark at all, so the hatching had never once appeared from the
    # copy that creates it.
    # THAT REASON LEFT WITH THE HATCHING on 2026-08-17. The swatch no
    # longer asks any layer: its colours are built from the
    # assignment through the same renderer builder the map uses. The
    # order is kept because it costs nothing -- the restyle reads the
    # dialog's records, never the preview -- and because reversing it
    # would be a change nobody has measured a reason for.
    self._restyle_only()
    self._refresh_preview_colours()
    # ...and the rows are re-asked, because a style change is exactly
    # how an element STOPS deferring: the user picks a plugin style,
    # the restyle above replaces the renderer somebody built in QGIS,
    # and the controls that were switched off must come back. Without
    # this they stayed inert until the next full run -- a row the
    # plugin had taken back that the user still could not touch.
    self._refresh_deferring_rows()

  def _warn_about_close_colours(self):
    """Say so if hand-picked colours left two elements inseparable.

    Returns:
      None. Reports at most one notice, on closing the editor rather
      than on each pick: a warning that fires while someone is still
      choosing is noise, and the question only has an answer once
      they have finished.
    """
    if not self.opt_colour_warnings.isChecked():
      # the same opt-in as the check after a run: a reader asked for
      # this opinion or they did not, and the editor is not a special
      # case
      return
    project = QgsProject.instance()
    fills = {}
    for tid, layer_id in self._element_layer_ids.items():
      layer = project.mapLayer(layer_id)
      if layer is None:
        continue                # deleted output: nothing to judge
      colours = bridge.renderer_fill_colours(layer)
      if colours:
        fills[tid] = colours
    if len(fills) < 2:
      return
    # through the gated helper, like every consumer of this opinion:
    # the box check above only saves building the fills
    note = self._legibility_note(fills, self._assignments())
    if note is not None:
      self._report_quietly(note)

  def _assignments(self, only=None) -> list[dict]:
    """Read the Data & colours table into plain dicts.

    The ONE crossing point between widget state and everything
    downstream: symbology seeding, run signatures, preview colours,
    and every test that wants to know what the dialog thinks. Nothing
    else should read the table's cells directly.

    Returns:
      A list with one dict per element, in table order. Keys:

      * ``id`` — the element's tile_id ("a", "b", ...)
      * ``var`` — the chosen field, or None when the row is on "---"
      * ``mode`` — resolved symbology: "Graduated", "Categorized" or
        "Single colour" (the dropdown's Quant: entries all resolve to
        "Graduated"; the scheme says which kind)
      * ``mode_raw`` — the literal dropdown text, for restoring the
        row after a rebuild
      * ``ramp``, ``single_colour`` — the colour choice, whichever
        kind the row carries
      * ``reverse`` — the Reverse box: run that element's ramp the
        other way. False whenever the row has no ramp to reverse
      * ``opacity`` — 0-100, applied as QGIS layer opacity (100 is
        solid). Kept apart from the colours, so it survives every
        change of ramp, scheme or class count
      * ``scheme`` — break method for graduated rows, including
        "Unclassed"
      * ``k`` — class count (50 and greyed for "Unclassed"), as the
        SPINNER shows it. A column cannot be cut into more classes
        than it has distinct values, but that reduction belongs to
        make_graduated_renderer at the moment it classifies, not
        here: this is the record of what the user ASKED for, and a
        row whose record disagreed with its own cell is what
        test_an_unclassed_excursion_leaves_the_count_alone caught
        when the reduction was briefly made in this block
        (2026-08-14). On a CATEGORIZED row the cell displays the
        detected category count but ``k`` carries the row's
        remembered graduated count, 5 by default: the spin box is
        disabled there, so nothing writes the displayed number into
        ``user_k``. Harmless downstream, since seed_renderer reads
        ``k`` only for Graduated, but this block said the count was
        the detected one until 2026-08-12
      * ``outline`` — draw tile boundaries
      * ``class_source`` — where a categorized row's colours come
        from: None for automatic, else a "file:<path>" or
        "layer:<id>" token
      * ``quant_colours`` — a graduated row's positional class
        picks, {class index as str: "#rrggbb"}; None off graduated
        rows or when the current field has none
      * ``range_bounds`` — the Ramp Display Range as (lo, hi)
        percent; (0, 100) means the whole ramp, and is what
        non-graduated rows always carry
      * ``class_choice`` — the raw combo value, kept so the choice
        survives a table rebuild
      * ``pinned`` — class bounds set by hand, as ``{"low": float,
        "high": float}`` with either key absent, or None. ``low`` is
        the first class's upper bound and ``high`` is the last
        class's lower bound; the classifier cuts the row's count
        minus one class per pin and the pinned classes are put back
        around the result (bridge.make_graduated_renderer)
      * ``style_touched`` — the user picked the style by hand, so it
        should stop following the field's type

    The dicts are snapshots, not live views: change one and nothing
    happens to the table.
    """
    result = []
    for row in range(self.table.rowCount()):
      id_item = self.table.item(row, 0)
      # ONE ROW WHERE ONE ROW IS WANTED. `only` changes nothing about
      # what a dict holds or about how fresh it is -- the same widgets
      # are read at the same moment -- and it is what stops
      # `_assignment_for` building every element to return one.
      # Measured 2026-08-28 at the 256-element ceiling raised the day
      # before: the landing walked 256 rows 768 times, 200,192
      # row-visits where 768 would do, and each visit re-derived the
      # region layer's fingerprint to hit a cache that then hit --
      # 201,987 derivations of an extent, a feature count and a CRS.
      # Together with the legibility check's own quadratic that was
      # thirty-eight seconds of frozen QGIS on every Generate after
      # the first, against one second at twenty-six elements.
      # A CACHE WAS THE OBVIOUS ANSWER AND IS FORBIDDEN HERE, in this
      # method's own words and for a good reason: the table is the
      # record, `_row_follows_the_renderer` moves rows while the
      # landing is seeding, and a snapshot taken at the start of a
      # landing is stale by the middle of it. Reading fewer rows costs
      # nothing in freshness; remembering them would.
      if only is not None and (id_item is None
                               or id_item.text() != only):
        continue
      var_combo, mode_combo, k_spin, ramp_combo, reverse_holder, \
        opacity_spin, file_combo = self._row_widgets(row)
      reverse_box = self._row_reverse(row)
      if id_item is None or var_combo is None:
        continue
      var = var_combo.currentText()
      var = None if var == "---" else var
      mode_raw = (mode_combo.currentText() if mode_combo
                  else self._plausible_mode(var or "---"))
      scheme = "Quantiles"
      if mode_raw in self.GRAD_SCHEMES:
        mode = "Graduated"
        scheme = self.GRAD_SCHEMES[mode_raw]
      else:
        mode = mode_raw
      # A graduated renderer classifies NUMBERS, and over a text field
      # it comes back with no ranges at all, so every tile falls
      # outside every class and the layer draws as nothing. The
      # choosers are corrected as the user works (_on_mode_chosen,
      # _follow_variable), but this is the one place every consumer
      # reads -- the run, the restyle fast path, the signature, a
      # session restored from a saved project -- so the correction is
      # made here as well and cannot be got round.
      if mode == "Graduated" and var and not self._field_is_numeric(var):
        mode, mode_raw, scheme = "Categorized", "Categorized", "Quantiles"
      choice = (file_combo.currentData() if file_combo is not None
                else self._class_choices.get(
                  id_item.text() if id_item else "", ""))
      if not choice or choice in (self.BROWSE, self.SHARED):
        source = None
      else:
        source = choice  # "file:<path>" or "layer:<id>"
      k = 5
      if k_spin is not None:
        k = int(k_spin.property("user_k") or k_spin.value() or 5)
      if scheme == "Unclassed":
        k = 50  # fixed by definition of the style
      tid_text = id_item.text()
      if isinstance(ramp_combo, QgsColorButton):
        ramp_name = self._ramp_choices.get(tid_text, "Reds")
        single_colour = ramp_combo.color().name()
      else:
        ramp_name = (ramp_combo.currentText() if ramp_combo
                     else self._ramp_choices.get(tid_text, "Reds"))
        single_colour = self._single_colours.get(tid_text)
      result.append({
        "id": tid_text,
        "var": var,
        "mode": mode,
        "mode_raw": mode_raw,
        "ramp": ramp_name,
        "reverse": bool(reverse_box is not None
                        and reverse_box.isEnabled()
                        and reverse_box.isChecked()),
        "opacity": (opacity_spin.value() if opacity_spin is not None
                    else 100),
        "single_colour": single_colour,
        "scheme": scheme,
        "k": k,
        "outline": self.opt_tile_outlines.isChecked(),
        # the class source matters (and re-seeds) only when categorized
        "class_source": source if mode == "Categorized" else None,
        # ...and so does what is INSIDE it, which the token alone
        # cannot say. See _class_source_stamp.
        "class_source_stamp": (
          self._class_source_stamp(source) if mode == "Categorized"
          else None),
        "class_choice": choice,
        # Class bounds set by hand, for this element AND this field.
        # Graduated only: a categorical element has no bounds to pin.
        "pinned": (self._pinned_bounds.get(tid_text, {}).get(var)
                   if mode == "Graduated" and var else None),
        # Colours chosen by hand for this element AND this field. A
        # different variable in the same element has its own set, so
        # switching away and back restores rather than discards.
        "category_colours": (
          self._category_colours.get(tid_text, {}).get(var)
          if mode == "Categorized" and var else None),
        # Positional class colours and the ramp's display window,
        # both graduated-only. The range rides every graduated row so
        # seeding never has to guess a default.
        "quant_colours": (
          self._quant_colours.get(tid_text, {}).get(var)
          if mode == "Graduated" and var else None),
        "range_bounds": (
          tuple(self._ramp_ranges.get(tid_text, (0, 100)))
          if mode == "Graduated" else (0, 100)),
        "style_touched": bool(mode_combo is not None
                              and mode_combo.property("touched")),
        # WHAT THE COLOURS MEAN depends on the values, so the counter
        # that follows an edit in QGIS rides in the element's own
        # record and therefore into _signature. See the note there.
        "value_digest": self._value_digest(var),
      })
    return result

  # Columns that write the RENDERER, and are therefore inert while an
  # element is deferring. The line is the renderer rather than a list
  # somebody maintains: Classes, Colour ramp, Reverse, the categorical
  # colourmap source and Edit colours all end up inside it. OPACITY
  # (column 6) is deliberately absent -- it is a layer property beside
  # the renderer, cannot destroy anything the styling panel built, and
  # is the one control a user is likely to want while reading a
  # hand-styled element against a basemap (settled 2026-08-15).
  RENDERER_COLUMNS = (3, 4, 5, 7, 8)

  def _refresh_deferring_rows(self):
    """Make every row say whether the plugin still styles its element.

    Returns:
      None. For each row: the style chooser reads "Deferring to QGIS"
      exactly when that element's layer holds a renderer no row can
      name, the DEFERRING entry is selectable only then, and the
      controls that write the renderer are enabled only when it is
      not.

    Called wherever layers can have changed underneath the table -- a
    run landing, a project adopted, a style edited in QGIS's own panel
    -- because the question is asked of the LAYER and the answer can
    move without the dialog doing anything.

    Signals are blocked while the chooser is moved: putting a row's
    own truth into it is not somebody choosing a style, and letting it
    read as one would fire the handler that RE-SEEDS, destroying the
    very work deferral exists to protect.
    """
    # rows that have just STOPPED deferring, so their controls can be
    # put back the way the row's own rules want them rather than the
    # way they happened to be when deferral began
    restore = set()
    for row in range(self.table.rowCount()):
      item = self.table.item(row, 0)
      combo = self.table.cellWidget(row, 2)
      if item is None or combo is None:
        continue
      deferring = self._element_is_deferring(item.text())
      model = combo.model()
      index = combo.findText(self.DEFERRING)
      if index >= 0 and model is not None:
        entry = model.item(index)
        if entry is not None:
          entry.setEnabled(deferring)
      # ...BUT NEVER OVER A STYLE THE USER HAS JUST PICKED. Picking a
      # plugin style is how somebody takes an element BACK from QGIS,
      # and `_add_output_layers` says at its own reclaim gate why a
      # test on the LAYER cannot see that: the layer still holds the
      # dock's renderer at the moment of the pick, because the
      # re-seeding it triggers has not happened yet. So
      # `_element_is_deferring` answers True, and this line quietly put
      # the row back to "Deferring to QGIS" -- with signals blocked, so
      # nothing noticed -- after which every path downstream correctly
      # preserved the dock's renderer over the user's choice.
      #
      # MEASURED 2026-08-19 by dumping which rows read as deferring at
      # every refresh: `[] -> ['c']` immediately after the pick, the
      # row taken back within the same Generate. Red since `7a7d163`,
      # which added a second route into this refresh at exactly the
      # wrong moment; found by the first full suite run of the day and
      # bisected over the 27 commits between rc9 and that one, after
      # six other readings had each been measured and died.
      #
      # `_picked_back` is the record of that act, and it is a set of
      # elements rather than a flag on the widget for a reason paid
      # for the same day. The first fix here read `style_touched`,
      # which means "somebody chose this row's mode" and stays true
      # for the rest of the session -- so a row whose style had EVER
      # been picked by hand could never afterwards follow a
      # rule-based style pasted onto its layer in QGIS, and the next
      # Generate reclaimed the element and painted over the user's
      # work. That is the rc5 field report arriving by a new door.
      # A STICKY FLAG CANNOT ANSWER A QUESTION ABOUT ORDER: the row
      # wins only until the layer agrees or the layer moves again.
      picked = item.text() in self._picked_back
      if not deferring:
        # the layer has caught up -- through the restyle the pick
        # triggered, or a run's landing -- so the claim is spent
        self._picked_back.discard(item.text())
      if deferring and combo.currentText() != self.DEFERRING \
          and not picked:
        combo.blockSignals(True)
        combo.setCurrentText(self.DEFERRING)
        combo.blockSignals(False)
      elif not deferring and combo.currentText() == self.DEFERRING:
        # THE ELEMENT STOPPED DEFERRING WITHOUT ANYBODY PICKING A
        # STYLE: somebody put QGIS back on something a row can name.
        # The row follows the RENDERER rather than guessing from the
        # variable, because the whole principle is that the row
        # describes the map -- and the map is now a thing with a name.
        # Measured 2026-08-15 by a hunt: without this the row sat on
        # "Deferring to QGIS" over a plain single symbol, with its
        # controls still inert, and the next Generate seeded a
        # graduated renderer over it saying only "no re-tiling
        # needed".
        layer_now = QgsProject.instance().mapLayer(
          self._element_layer_ids.get(item.text(), ""))
        style = bridge.expressible_style(
          layer_now.renderer()) if layer_now is not None else None
        variable = self.table.cellWidget(row, 1)
        label = self._plausible_mode(
          variable.currentText() if variable is not None else "")
        if style is not None:
          mode, scheme = style
          if mode == "Graduated":
            label = next(
              (text for text, name in self.GRAD_SCHEMES.items()
               if name == scheme), label)
          else:
            label = mode
          # A SINGLE COLOUR MUST BRING ITS COLOUR WITH IT, and this is
          # the third time today the same asymmetry has cost a defect.
          # Found by a hunt the same evening, in PIXELS rather than
          # renderers: 1,764 interior pixels of #0b1e2d before, 1,926
          # of #3c8bc2 after, and #0b1e2d gone. The identical dock edit
          # WITHOUT deferring first keeps the colour, which is what
          # proves deferral is the difference.
          #
          # Moving the row to "Single colour" is right -- the row
          # should say what the map is -- but it CHANGES THE
          # ASSIGNMENT, which is exactly the condition under which
          # Generate re-seeds an element. So the plugin drew its own
          # default over the fill the user had mixed in the dock. The
          # label was honest and the record behind it was empty.
          #
          # `_read_style_from_layer` at the reopen path already does
          # this, four hundred lines up: a single symbol carries its
          # colour on it, so read it. That twin was written for a
          # project coming back and guards `tile_id not in
          # self._single_colours`, because a remembered choice should
          # win on reopen. Here the user has JUST set it, so it
          # overwrites.
          if mode == "Single colour" and layer_now is not None:
            try:
              symbol = layer_now.renderer().symbol()
              if symbol is not None:
                self._single_colours[item.text()] = symbol.color().name()
            except Exception:
              pass          # a colour we cannot read is not one to guess
        combo.blockSignals(True)
        combo.setCurrentText(label)
        # TOUCHED, or the next rebuild throws this away -- and it is
        # the same line, for the same reason, that
        # `_row_follows_the_renderer` was given earlier the same day.
        # I taught one writer of this combo and never grepped for the
        # other. `_refresh_table` restores a row's mode only when
        # `style_touched` is set and otherwise re-derives it from the
        # variable's type, so a style written here with signals
        # blocked survived until the first spacing nudge and then
        # reverted -- taking with it, at the next Generate and in the
        # exported file, the plain fill or the equal-interval breaks
        # the user had just set in QGIS to take the element back.
        #
        # Measured 2026-08-17 in three arms: with no spacing nudge the
        # fill survives; with one, the row goes from "Single colour" to
        # "Quant: Quantiles" and the map and the file both follow, with
        # nothing said; and without deferring first, the same nudge
        # leaves the fill alone. So the rebuild is the difference and
        # deferral is the door.
        #
        # WHEN A FIX ADDS A FLAG WRITE, GREP EVERY OTHER WRITER OF THE
        # SAME WIDGET. The flag is a store, and it outranks the combo.
        combo.setProperty("touched", True)
        combo.setProperty("last_style", label)
        combo.blockSignals(False)
      if deferring:
        # THE RAMP CELL MUST NOT GO ON NAMING A RAMP. It read "Blues"
        # over a rule-based map while building this, which is a
        # control lying about the map -- the exact thing the Custom
        # display was built for, so it is what deferring uses. The
        # swatch beside it is sampled from the layer, and the cache
        # entry is dropped first because the colours it summarises
        # have just changed and its key cannot see the renderer.
        ramp_cell = self.table.cellWidget(row, 4)
        if ramp_cell is not None and hasattr(ramp_cell, "set_custom_display"):
          self._custom_swatch_cache.pop(item.text(), None)
          variable = self.table.cellWidget(row, 1)
          ramp_cell.set_custom_display(self._custom_swatch_for(
            item.text(),
            variable.currentText() if variable is not None else ""))
      for column in self.RENDERER_COLUMNS:
        widget = self.table.cellWidget(row, column)
        if widget is None or not hasattr(widget, "setEnabled"):
          continue
        if deferring:
          # MARKED as ours, because these controls are disabled for
          # other reasons too -- Classes on a categorical row, Edit
          # colours with no variable -- and re-enabling everything on
          # the way out would switch on controls that were never ours
          # to switch off.
          if widget.isEnabled():
            widget.setProperty("disabled_by_deferring", True)
          widget.setEnabled(False)
          widget.setToolTip("Styled in QGIS; set it in the Layer "
                            "Styling panel.")
        elif widget.property("disabled_by_deferring"):
          # THE MARK CAN BE STALE, and honouring it blindly is how the
          # tester met a Classes spinner reading a greyed 32. The mark
          # says "this was enabled when deferral began"; it does not
          # say the row still WANTS it enabled, and the row may have
          # become Categorized in between -- where the Classes cell
          # reports a distinct-value count and is not a control at
          # all. Re-enabled on a stale mark it sat live at 32 with a
          # range of 0..9999, one arrow click reached `on_k` and wrote
          # 33, and the next rebuild clamped that to the 2-20 ceiling.
          # Which is exactly the 20 and 20 in the second screenshot.
          #
          # So the mark is CLEARED either way -- deferral is over --
          # and the control is switched back on only if the row's own
          # rules would have it on. `_sync_row_enablement` is the one
          # place those rules live, so asking it cannot drift from
          # them the way a second copy here would.
          widget.setProperty("disabled_by_deferring", False)
          widget.setEnabled(True)
          restore.add(row)
    # ...and now the row's own rules have the last word, AFTER the
    # loop rather than inside it, since `_sync_row` reads several of
    # the widgets the loop is still walking.
    for row in sorted(restore):
      self._sync_row(row)

  def _element_is_deferring(self, tile_id) -> bool:
    """Is this element drawn by something no row can express?

    Args:
      tile_id: the element to ask about.

    Returns:
      True when the element HAS an output layer and that layer's
      renderer is of a kind the style chooser cannot name — rule-based
      or any other thing built in QGIS's styling panel, or a graduated
      renderer classified by a method this plugin does not offer.
      False when there is no layer yet, since an element that has
      never been drawn is not deferring to anything.

    INFERRED, NEVER STORED, and that is the whole design (settled
    2026-08-15). A stamp saying "deferring" beside a renderer saying
    what it actually is would be one fact in two places, which is the
    shape that cost this project most in a single evening: the two
    disagree the moment somebody reverts the renderer in the dock. The
    renderer is the single authority, which is also what the settled
    rule already says — renderers are standard QGIS objects and the
    dock is where refinement lives.

    It self-corrects, too. When a later version learns to express some
    renderer, elements deferring only for that reason simply stop,
    with nothing to migrate and no stale flag to clean up.

    The same question is asked from three directions that must agree —
    a dock edit, a reopened project, a layer out of a GeoPackage — so
    all three come here, and the GeoPackage case is the reason the
    STAMP may never answer it: a style written by an older version
    travels in that file and would otherwise resurrect a mode the
    layer does not hold (maintainer's condition, 2026-08-15).
    """
    layer_id = self._element_layer_ids.get(tile_id)
    layer = QgsProject.instance().mapLayer(layer_id) if layer_id else None
    if layer is None:
      return False
    return bridge.expressible_style(layer.renderer()) is None

  def _plausible_mode(self, var_text: str) -> str:
    """The style a fresh element gets: quantile classes for numeric
    fields, categorized symbology for text, a flat fill for nothing."""
    if not var_text or var_text == "---":
      return "Single colour"
    return "Quant: Quantiles" if self._field_is_numeric(var_text) \
      else "Categorized"

  def _on_style_changed(self, mode_combo):
    """Destroy positional picks when a row's break method changes.

    Args:
      mode_combo: the style chooser whose index just moved.

    Returns:
      None. A changed scheme reclassifies the column, so positional
      picks name classes that no longer exist: they are destroyed,
      with the standing notice (settled 2026-08-09). Compared against
      the last style seen so nothing fires when the index merely
      resettles on the same entry; the display range survives,
      because it says nothing about the classification, only about
      the ramp. Crossing to or from a non-quant style counts too --
      Categorized and back is two reclassifications, not none.
    """
    was = mode_combo.property("last_style")
    now_style = mode_combo.currentText()
    mode_combo.setProperty("last_style", now_style)
    tid_here = mode_combo.property("tile_id")
    if tid_here and was is not None and now_style != was and \
        (now_style in self.GRAD_SCHEMES or was in self.GRAD_SCHEMES):
      self._clear_quant_customization(
        tid_here, "a new style", reset_range=False)

  def _on_mode_chosen(self, mode_combo, var_combo):
    """React to the user picking an element's style by hand.

    Args:
      mode_combo: the style chooser just used. It is marked as
        touched, which is what stops the style following the field's
        type from then on.
      var_combo: the same row's variable chooser, read for the field
        the style would apply to.

    Returns:
      None. The style may be snapped back to Categorized, and the
      user told why.

    _follow_variable already covers one order: a style chosen, then
    the variable changed to text. This is the order it cannot see --
    the text field chosen FIRST, then a Quant: style picked on top of
    it. Nothing corrected that, so the chooser went on reading
    "Quant: Quantiles" while the map was drawn by a graduated
    renderer over words. Such a renderer has no ranges at all, every
    tile falls outside every class, and all of the element layers
    paint nothing whatever -- a run that reports success and produces
    an empty map.
    """
    mode_combo.setProperty("touched", True)
    # TAKING AN ELEMENT BACK FROM QGIS, recorded here because this is
    # the one moment it can be told apart from anything else. The
    # layer still holds the renderer somebody built in the styling
    # panel -- the re-seed this pick triggers has not run yet -- so
    # from here until the layer agrees, the row is the authority on
    # what this element is. See `_refresh_deferring_rows`, which is
    # where a refresh would otherwise put the row straight back.
    taken_back = mode_combo.property("tile_id")
    if taken_back and self._element_is_deferring(taken_back):
      self._picked_back.add(taken_back)
    var = var_combo.currentText()
    # A copied ladder was copied for a particular SCHEME as well as a
    # particular count, so choosing another retires its values -- and
    # keeps the pins that came with them, which is the whole reason
    # the record holds the two apart.
    for row in range(self.table.rowCount()):
      if self.table.cellWidget(row, 2) is mode_combo:
        item = self.table.item(row, 0)
        if item is not None:
          self._release_copied_breaks(item.text(), "a new class style")
        break
    if mode_combo.currentText() in self.GRAD_SCHEMES and \
        var not in ("", "---") and not self._field_is_numeric(var):
      # blockSignals so the correction does not read as another user
      # choice; the preview refresh the signal would have done is
      # called directly instead.
      mode_combo.blockSignals(True)
      mode_combo.setCurrentText("Categorized")
      mode_combo.blockSignals(False)
      self._report_quietly(
        f"'{var}' holds text, so it is drawn as categories rather "
        f"than a range of values.")
      self._refresh_preview_colours()

  def _follow_variable(self, var_combo, mode_combo):
    """Keep a row's style in step with its variable.

    Args:
      var_combo: the row's variable chooser, just changed.
      mode_combo: the row's style chooser, which may be adjusted.

    Returns:
      None. Until the user picks a style themselves it follows the
      field's type; a hand-picked Quant: style still yields to
      Categorized when the variable stops being numeric, because the
      alternative is a graduated renderer on text.
    """
    var = var_combo.currentText()
    # A VARIABLE CHANGE ENDS DEFERRAL, and the row says so NOW rather
    # than at the next landing. Deferral cannot survive it -- a
    # renderer keyed to the old column describes nothing about the new
    # one -- so this correction is made whether or not the user has
    # ever picked a style by hand, which is the one case `touched`
    # below would otherwise skip.
    #
    # Leaving it to the landing drew NOTHING AT ALL. Measured
    # 2026-08-15 by a hunt: an element styled in QGIS and then moved
    # onto a text column kept the mode "Deferring to QGIS", which is
    # not "Graduated", so the text-field guard in `_assignments` never
    # fired and seed_renderer fell into its graduated branch over
    # words. A graduated renderer over text has no ranges at all --
    # 84 of 84 tiles with no symbol, the row reading Categorized and
    # the message bar saying the element was "drawn by the plugin
    # again". Correcting the ROW here lets every guard downstream see
    # a mode it recognises, rather than teaching each of them a new
    # word.
    if mode_combo.currentText() == self.DEFERRING:
      mode_combo.blockSignals(True)
      mode_combo.setCurrentText(self._plausible_mode(var))
      mode_combo.blockSignals(False)
    # THE STYLE FOLLOWS THE FIELD, NOT THE ELEMENT (maintainer's
    # ruling, 2026-08-26, sparing the picks). A touched mode used to
    # ride the element across a variable change, so returning a row
    # from Categorized landcover to v1 arrived wearing Categorized --
    # and the Quantiles re-click the user was then forced into is a
    # genuine reclassify, which retires the very positional picks the
    # kept-silently ruling had preserved. The mode a person chose is
    # banked per element AND field on the way out, exactly as ruling 6
    # already keys the scheme limbs, and a field whose bank holds a
    # choice comes back wearing it -- no forced re-click, no cleared
    # picks. A user's own mode click on the controls still retires
    # picks as the 2026-08-09 rule says.
    tid_here = mode_combo.property("tile_id")
    prev_field = var_combo.property("ws_last_var")
    if tid_here and prev_field and prev_field not in ("", "---") \
        and prev_field != var and mode_combo.property("touched"):
      self._mode_by_field.setdefault(tid_here, {})[prev_field] = \
        mode_combo.currentText()
    var_combo.setProperty("ws_last_var", var)
    banked = (self._mode_by_field.get(tid_here, {}).get(var)
              if tid_here else None)
    if banked and banked in self.MODES and \
        mode_combo.findText(banked) >= 0 and \
        not (banked in self.GRAD_SCHEMES and var not in ("", "---")
             and not self._field_is_numeric(var)):
      mode_combo.blockSignals(True)
      mode_combo.setCurrentText(banked)
      mode_combo.blockSignals(False)
      mode_combo.setProperty("touched", True)
      self._refresh_preview_colours()
    elif not mode_combo.property("touched"):
      mode_combo.blockSignals(True)
      mode_combo.setCurrentText(self._plausible_mode(var))
      mode_combo.blockSignals(False)
      self._refresh_preview_colours()
    elif mode_combo.currentText() in self.GRAD_SCHEMES and \
        var not in ("", "---") and not self._field_is_numeric(var):
      _dump("FOLLOW-VAR", mode_combo.property("tile_id"),
            "quant-on-text ->", "Categorized", "var=", var)
      mode_combo.blockSignals(True)
      mode_combo.setCurrentText("Categorized")
      mode_combo.blockSignals(False)
      self._refresh_preview_colours()

  def _drawn_preview_colour(self, tile_id):
    """One colour standing for what the element's LAYER actually paints.

    Args:
      tile_id: the element, used to find its own output layer.

    Returns:
      A hex colour ("#rrggbb") read off that element's own renderer,
      or None when there is no layer yet or the renderer is of a kind
      `renderer_fill_colours` cannot read. None means "cannot say",
      and the caller answers it by falling back to the row's ramp
      rather than by leaving a quarter of the design uncoloured.

    Taken at the same 65% along the list of drawn colours that
    `ramp_swatch_colour` takes along a ramp, so an element read off
    the map and one computed from a ramp are represented by the same
    convention. The design view is a COMPARISON between elements, and
    two conventions inside one picture would make that comparison say
    something the map does not.

    NAMED FOR WHAT IT ANSWERS RATHER THAN FOR ITS FIRST CALLER. It
    arrived on 2026-08-17 as `_deferring_preview_colour`, and within
    the hour a hunt found the second case that needs exactly this --
    hand-picked class colours -- which the old name argued against
    reusing it for. A helper named after one caller is a helper the
    next caller writes again.
    """
    layer = QgsProject.instance().mapLayer(
      self._element_layer_ids.get(tile_id) or "")
    if layer is None:
      return None
    # `renderer_fill_colours` asks the RENDERER rather than the ramp,
    # and falls through to the base class's own `symbols()` for the
    # rule-based and other renderers deferring consists of -- which is
    # the whole reason this can answer at all.
    drawn = bridge.renderer_fill_colours(layer)
    if not drawn:
      return None
    red, green, blue = drawn[round(0.65 * (len(drawn) - 1))]
    return "#%02x%02x%02x" % (red, green, blue)

  PREVIEW_MIN_OPACITY = 40

  def _table_id_colours(self) -> dict:
    """Each element's representative colour for the preview, softened
    by its opacity.

    Returns:
      {tile_id: "#rrggbbaa"} — a swatch colour per element, carrying
      an alpha channel taken from the element's Opacity cell.

    The alpha is FLOORED at PREVIEW_MIN_OPACITY. The preview paints on
    a plain panel rather than over the map, so a very low value there
    would fade toward the panel's grey and take the tile-id labels
    with it, while telling the reader nothing true: on the map the
    element composites over whatever lies beneath it, not over this
    background. Showing the effect but keeping the design legible is
    the compromise the user chose.
    """
    from qgis.PyQt.QtGui import QColor
    colours = {}
    for a in self._assignments():
      # UNASSIGNED FIRST, in the same order `seed_renderer` uses, and
      # the order is the whole of it. The map asks `if not var` before
      # anything else and paints NO_DATA; this asked about the MODE
      # first, and an element left on "---" defaults to Single colour
      # and keeps a colour button -- so the preview showed that colour
      # while the map drew grey. The preview exists to judge a design
      # before committing to it, so a quarter of the pattern being
      # judged in a colour the map never paints is the preview failing
      # at its one job. Measured 2026-08-13: preview #e7342a against a
      # map drawing (221, 221, 221). Guarded by
      # test_an_unassigned_element_previews_as_it_draws.
      # ONE RULE: THE PREVIEW SHOWS WHAT THE MAP DRAWS.
      # (Maintainer's ruling, 2026-08-17, after this one expression
      # was found wrong SIX TIMES IN ONE DAY -- a deferring element's
      # layer, the Ramp Display Range, the row's Reverse, hand-picked
      # class and category colours, a column with nothing to classify,
      # and a constant column coloured from the middle of the window
      # rather than at 65% along it.)
      #
      # Each of those was a branch reading the ROW where it should
      # have read the MAP, and each was fixed separately by adding
      # another condition to the same `elif`. Six arms is a rule
      # nobody can hold in their head; asking the layer is one that
      # cannot drift, because the thing being described is the thing
      # being asked.
      #
      # THE FALLBACK IS FOR BEFORE THERE IS A MAP. `_drawn_preview_
      # colour` answers None when the element has no layer yet, which
      # is the ordinary state until the first Generate, and then the
      # row's own records are all there is to go on. That path keeps
      # the ramp's direction and window because they are what the map
      # WILL be drawn from.
      #
      # A DATA-DEFINED FILL is deliberately left reading the base
      # symbol, which is what QGIS itself shows for such a layer and
      # what `renderer_fill_colours` returns. The ramp cell beside it
      # draws an unknown, so the pair is honest taken together, and
      # the design view has to paint every element something.
      # (Maintainer's ruling the same day; recorded as a known limit
      # rather than as a defect.)
      base = self._drawn_preview_colour(a["id"])
      if base is None:
        if not a["var"]:
          base = bridge.NO_DATA_FILL
        elif a["mode"] == "Single colour" and a.get("single_colour"):
          base = a["single_colour"]
        else:
          base = bridge.ramp_swatch_colour(
              a["ramp"], bool(a.get("reverse", False)),
              tuple(a.get("range_bounds", (0, 100))))
      opacity = max(self.PREVIEW_MIN_OPACITY, int(a.get("opacity", 100)))
      colour = QColor(base)
      colour.setAlpha(round(255 * opacity / 100))
      colours[a["id"]] = colour.name(QColor.NameFormat.HexArgb)
    return colours

  def _geometry_signature(self):
    """Everything that changes the TILES, as one comparable tuple.

    The dividing line that makes restyling cheap: family, spacing,
    modifiers, the map-option switches, the region layer, the output
    path, and which variables are mapped (they are joined onto the
    tiles while tiling, so a new variable does need new geometry).
    Absent from it: ramp, classification scheme, class count, single
    colour, class source, outline. Those change only how existing
    tiles are painted.

    Returns:
      A tuple to compare with the last run's. Equal means the tiles
      on screen are still the right tiles, and a style change can be
      answered by re-seeding renderers instead of tiling again.
    """
    layer = self.layer_combo.currentLayer()
    kwargs = self._unit_kwargs()
    kwargs.pop("spec", None)
    return (
      layer.id() if layer is not None else None,
      self.family_combo.currentText(), self.n_combo.currentData(),
      tuple(sorted(kwargs.items())),
      self.mod_rotate.value(), self.mod_scale_x.value(),
      self.mod_scale_y.value(), self.mod_skew_x.value(),
      self.mod_skew_y.value(), self.mod_p_inset.value(),
      self.mod_t_inset.value(), self.mod_glyph.isChecked(),
      self.opt_join_prototiles.isChecked(), self.opt_retain.isChecked(),
      self.opt_clip.isChecked(), self.opt_icons.isChecked(),
      self.opt_outlines.isChecked(),
      self.gpkg_widget.filePath().strip() or None,
      tuple(sorted(a["var"] for a in self._assignments() if a["var"])),
      # WHETHER EACH ELEMENT NEEDS ITS TILES SPLIT, which is geometry
      # and not style however much it looks like styling. Only a full
      # run splits an element's missing values onto their own layer;
      # `_restyle_only` repaints a paired layer that already exists
      # and cannot make or unmake one. So switching an element from
      # Categorized to a graduated scheme was answered in place, the
      # nulls stayed on the graduated layer, and the holes this
      # feature exists to remove came straight back -- while the
      # reverse left a paired layer behind holding values nothing
      # drew. Measured 2026-08-16 by a hunt: eight null tiles
      # unpainted after the mode change, `symbolForFeature` answering
      # None for every one of them.
      #
      # IT CARRIES THE FIELD AND NOT MERELY A YES. The first version
      # of this term was a boolean per element, which is INVARIANT
      # UNDER A PERMUTATION: swap the variables of two elements whose
      # columns both have nulls and every boolean stays True, the
      # signature does not move, and the paired layer built for the
      # OLD field is left holding the wrong rows -- real values drawn
      # as no data, and areas that have values drawn as nothing.
      # Measured 2026-08-16: element 'a' with 16 tiles painted by
      # nothing and 17 greyed that all had a value, against a re-tile
      # of the same design with none of either.
      #
      # The lesson generalises: when a fix widens a signature, ask
      # whether the new term is COARSER than the thing it stands for.
      # A boolean summarising a field cannot see the field move.
      # AND THE LIMITS AS VALUES, for the same reason and by the same
      # mistake made twice. `_needs_a_no_data_split` learned about
      # floors and ceilings on 2026-08-18, which put them behind a
      # YES/NO -- so raising a floor from 20 to 40 answered yes both
      # times, the signature never moved, `_restyle_only` took the
      # change, and it can neither make nor unmake a split. The areas
      # the higher floor newly excludes stayed on the element layer
      # with no class to place them and drew as HOLES, while the
      # notice said to press Generate, which changed nothing. Worse on
      # a column that already holds a null: the predicate is true
      # before any limit exists, so even the FIRST limit was invisible.
      # Measured 2026-08-19 by three hunts at once, one of them in
      # pixels: 4,394 of the element's paint gone, 27.5 per cent.
      # This is the paragraph above, repeated: a boolean summarising a
      # field cannot see the field move, and neither can it see a
      # number move. Carrying the numbers costs two dict lookups.
      # ...AND WHICH ELEMENT CARRIES WHICH VARIABLE, not merely which
      # variables are mapped. The term above this one is the SET, and
      # a set is invariant under a PERMUTATION -- swapping two
      # elements' columns leaves it identical -- which was harmless
      # while every element layer carried every mapped column: a
      # restyle could re-seed element a onto b's column because the
      # column was there. Ruling 6 of 2026-08-25 trims each element to
      # the variable it displays, and that makes a permutation a
      # GEOMETRY change: element a's layer now holds only v1, so
      # re-seeding it onto v3 finds no field at all and QGIS hands
      # back a single symbol. Measured the day the trim landed, by
      # `test_metamorphic_variable_permutation`, which had passed
      # since it was written.
      #
      # This is the third time this signature has been widened for the
      # same reason, and the note beside the first two says it: a term
      # coarser than the thing it stands for cannot see that thing
      # move. A set could not see a permutation.
      tuple((a["id"], a.get("var"), self._needs_a_no_data_split(a),
             self._limits_key(a))
            for a in self._assignments()),
      # What the layer HOLDS, not merely which layer it is. Without
      # this, deleting half the features left every term here
      # identical, so the run was treated as a style-only change and
      # answered by re-seeding the renderers on tiles built from data
      # that no longer existed -- a map of deleted places, redrawn on
      # demand and never marked as out of date.
      self._layer_fingerprint(), self._data_version,
    )

  def _limits_key(self, assignment):
    """This element's floor and ceiling, as the signature carries them.

    Args:
      assignment: one row from `_assignments()`, read for its element
        id and its variable, which together key the pin record.

    Returns:
      ``(floor, ceiling)``, either of them None where the user has not
      set that end. A plain tuple of numbers, because the geometry
      signature is compared with ``==`` and must be hashable and
      cheap: this is two dictionary lookups and no scan of the data,
      which matters because the signature is asked on every debounce
      tick.

    WHY THE VALUES AND NOT A YES/NO. A limit is a geometry change --
    excluding a value moves its tiles onto the paired layer, and
    `_restyle_only` can neither make nor unmake one -- so the
    signature has to notice a limit MOVING and not merely a limit
    existing. Carried as a boolean it noticed neither: raising a floor
    left the signature identical, and on a column that already holds a
    null the answer was true before any limit was set at all.

    THE LIMITS ARE CARRIED WHETHER OR NOT THEY CURRENTLY EXCLUDE
    ANYTHING, deliberately. Asking whether they exclude would be a
    second, more expensive question whose answer changes with the
    data, and the cost of being wrong is not symmetric: a re-tile
    nobody needed is a slower interaction, while a split that never
    happens is an unpainted area, which reads as "nothing is here".
    """
    record = (self._pinned_bounds.get(assignment.get("id")) or {}).get(
      assignment.get("var")) or {}
    return (record.get("floor"), record.get("ceiling"))

  def _needs_a_no_data_split(self, assignment):
    """Whether this element's tiles must be split onto a second layer.

    Args:
      assignment: one row from `_assignments()`.

    Returns:
      True when the element's renderer may be unable to place some of
      its rows AND the column has such rows. False for every
      categorized or single-colour element, which have their own
      catch-all and need no second layer.

    A DEFERRING ELEMENT STILL NEEDS THE SPLIT, and forgetting that put
    holes in real maps for two days. Deferral is about WHO PICKS THE
    COLOURS; the split is about WHICH ROWS A RENDERER CAN PLACE, which
    is geometry -- as the signature comment beside this says. But
    `_assignments` resolves a deferring element's mode to
    "Deferring to QGIS", so a test for `== "Graduated"` answered False
    and the twin was retired.

    MEASURED 2026-08-17, two arms of one fixture differing only by a
    dock edit: with the element left alone, 58 tiles and ZERO of
    490,000 pixels unpainted; after refining it in QGIS's Symbology
    panel, the paired layer gone, the rows folded back onto an element
    whose renderer has no class for them, and 28,828 PIXELS UNPAINTED
    with nothing said. That is precisely the harm the No Data layer
    was built to remove: honest "not known" became holes reading
    "nothing is here".

    So the question is asked of what the renderer can PLACE. A
    categorized renderer has `addCategory` and therefore a catch-all,
    so it never needs the split whoever styles it. Anything else --
    graduated, or a renderer we have handed over and cannot inspect --
    may not place a null, and an unpainted area is the wrong way to
    fail: losing a custom fill is visible and undoable, a hole is
    neither.

    IT IS IN THE GEOMETRY SIGNATURE, so it is asked on every debounce
    tick and must not cost a scan each time; `_column_has_nulls`
    caches per column and per data version. Widening a signature into
    something that rescans the layer is a trap this project has
    already written down.
    """
    mode = assignment.get("mode")
    if mode in ("Categorized", "Single colour") or not mode:
      return False
    # A LIMIT NEEDS THE SPLIT EVEN WHERE THE DATA IS PERFECT, which is
    # the case this predicate could not see before 2026-08-19. A floor
    # or a ceiling inside the data excludes ordinary finite values, and
    # excluded rows go to the paired layer exactly as an absent one
    # does -- so a column with no NULL and no infinity can still need a
    # twin, and asking `_column_has_nulls` alone would answer no.
    #
    # THIS IS WHY THE PREDICATE, NOT THE SPLIT, IS THE THING TO WIDEN.
    # It feeds the GEOMETRY SIGNATURE, so answering no here sends a
    # limit change down `_restyle_only`, which can neither make nor
    # unmake a paired layer: the exclusion would be recorded, believed
    # and never drawn. That is the same door the infinities came
    # through on 2026-08-16, described at length below.
    if self._limits_exclude_anything(assignment):
      return True
    return self._column_has_nulls(assignment.get("var"))

  def _limit_problem(self, record, assignment):
    """Why this floor or ceiling cannot be drawn, or None.

    Args:
      record: the element's pin record as it WOULD be, with the new
        limit already in it -- asked of the prospective record rather
        than the stored one, so a refusal happens before anything is
        kept.
      assignment: that element's row, for the class count.

    Returns:
      A sentence for the user, or None when the limits are drawable.

    ONLY WHAT CANNOT BE DRAWN IS REFUSED, which is the rule the
    maintainer set for pins on 2026-08-17 and the reason the
    out-of-data guard was lifted then: a limit outside the column
    draws perfectly well and is the whole point of giving one pair to
    several variables. What is refused here is a limit that crosses
    the ladder's own interior -- a floor above the first class's upper
    bound leaves that class running backwards, which QGIS accepts and
    then paints as nothing.

    Asked against the boundaries the record itself carries, since a
    copied or adopted ladder names them exactly; where it names none,
    there is nothing for a limit to cross and this says so.
    """
    floor, ceiling = record.get("floor"), record.get("ceiling")
    if floor is None and ceiling is None:
      return None
    if floor is not None and ceiling is not None \
        and float(floor) >= float(ceiling):
      return ("The lowest value drawn must be below the highest; "
              f"{float(floor):g} is not below {float(ceiling):g}.")
    inner = [float(b) for b in (record.get("breaks") or [])]
    for end, pin in (("low", record.get("low")),
                     ("high", record.get("high"))):
      if pin is not None:
        inner.append(float(pin))
    if not inner:
      return None
    if floor is not None and float(floor) >= min(inner):
      return (f"The lowest value drawn ({float(floor):g}) is at or above "
              f"the first class boundary ({min(inner):g}), which would "
              f"leave that class with nothing to hold.")
    if ceiling is not None and float(ceiling) <= max(inner):
      return (f"The highest value drawn ({float(ceiling):g}) is at or "
              f"below the last class boundary ({max(inner):g}), which "
              f"would leave that class with nothing to hold.")
    # ...AND THE PIN JUDGED AGAINST THE POOL THE LIMITS LEAVE, which
    # is the other half of the maintainer's ruling of 2026-08-19: a
    # pin is judged against the values the map is actually cut from,
    # never the whole column, and the refusal belongs at the door.
    # `_retire_an_undrawable_pin` carries the same question for records
    # that already hold an undrawable pair; this stops new ones being
    # made. Without it a floor of 38 under a pin at 40 was accepted by
    # both guards and then dropped in silence inside `bridge`, leaving
    # the record, the layer stamp and the saved project all claiming a
    # pin the map does not draw.
    low, high = record.get("low"), record.get("high")
    field = (assignment or {}).get("var")
    if (low is not None or high is not None) and field:
      source = self._classification_values(field)
      if source is not None:
        values = source.uniqueValues(source.fields().indexOf(field))
        left = [v for v in values
                if bridge.absence_kind(v, floor, ceiling)
                != bridge.OUTSIDE_RANGE_KEY]
        asked = int((assignment or {}).get("k", 5) or 5)
        if bridge.pin_problem(low, high, left, asked,
                              record.get("breaks")):
          pinned_at = low if low is not None else high
          if floor is not None:
            return (f"The lowest value drawn ({float(floor):g}) leaves "
                    f"too few values above it for the class bound you "
                    f"pinned at {float(pinned_at):g} to be drawn.")
          return (f"The highest value drawn ({float(ceiling):g}) leaves "
                  f"too few values below it for the class bound you "
                  f"pinned at {float(pinned_at):g} to be drawn.")
    return None

  def _limits_exclude_anything(self, assignment):
    """Whether this element's floor or ceiling puts a value out of bounds.

    Args:
      assignment: one element's row, read for its variable and its
        pin record -- the record carries "floor" and "ceiling" when
        somebody has set them, and neither key when they have not.

    Returns:
      True when the column holds at least one finite value the limits
      exclude. False when there are no limits, no column, no region
      layer to ask, or nothing outside them.

    ASKED OF THE REGION, like every other question about what a column
    holds, since breaks are cut once from the whole map and an element
    that receives no tile on the excluded value still shares its
    ladder. Cached on the column, the limits and `_data_version`,
    because this sits in the geometry signature and is therefore asked
    on every debounce tick -- widening a signature into something that
    rescans the layer is a trap this project has already paid for.
    """
    record = assignment.get("pinned") or {}
    floor, ceiling = record.get("floor"), record.get("ceiling")
    if floor is None and ceiling is None:
      return False
    field = assignment.get("var")
    if not field:
      return False
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return False
    key = (layer.id(), field, self._data_version, floor, ceiling)
    cached = self._limit_cache.get(key)
    if cached is not None:
      return cached
    index = layer.fields().indexOf(field)
    if index < 0:
      self._limit_cache[key] = False
      return False
    found = False
    for feature in layer.getFeatures():
      # `absence_kind` decides, so this cannot drift from what the
      # split actually does with the same value -- which is the whole
      # reason that helper exists.
      if bridge.absence_kind(feature[field], floor,
                             ceiling) == bridge.OUTSIDE_RANGE_KEY:
        found = True
        break
    self._limit_cache[key] = found
    return found

  def _column_has_nulls(self, field):
    """Whether the region layer has UNPLACEABLE values in one column.

    Args:
      field: the column name, or None, which answers False.

    Returns:
      True when at least one feature's value there cannot be drawn by
      a graduated renderer -- a NULL, a NaN, or an infinity. False
      when none is, when there is no such column, or when there is no
      region layer to ask -- absence of an answer is not evidence of
      anything, and claiming one would put an element through a full
      re-tile for nothing.

    IT MUST ASK THE SAME QUESTION `bridge.split_out_the_no_data` ASKS,
    and for a few hours on 2026-08-16 it did not. The split widened
    from "missing" to "the classifier cannot place this", so that it
    would catch an infinity; this scan went on looking for NULL alone.
    The split itself is not gated by this, so a full Generate still
    drew correctly -- what this feeds is the GEOMETRY SIGNATURE, and
    on a column holding infinities but no NULLs the dialog therefore
    believed no split was needed, so a style-only change was answered
    by `_restyle_only`, which can neither make nor unmake a paired
    layer, and the holes came back. Exactly the defect
    test_changing_to_a_graduated_style_cuts_the_split_it_needs guards
    for nulls, reached through a door opened by widening a predicate
    without enumerating its readers.

    Cached on the layer, the column and `_data_version`, which is
    bumped whenever the data underneath changes, so an edit in QGIS
    retires the answer and nothing else does.
    """
    if not field:
      return False
    layer = self.layer_combo.currentLayer()
    if layer is None:
      return False
    key = (layer.id(), field, self._data_version)
    cached = self._nulls_cache.get(key)
    if cached is not None:
      return cached
    index = layer.fields().indexOf(field)
    if index < 0:
      self._nulls_cache[key] = False
      return False
    found = False
    for feature in layer.getFeatures():
      if bridge.cannot_be_placed(feature[field]):
        found = True
        break
    # One entry per column per data version. It IS cleared with the
    # sibling caches when the region layer changes -- which the
    # comment here claimed before anything did it, and a hunt counted
    # 600 entries after 200 data-version bumps. A comment describing
    # what the code was meant to do is worse than none, because it is
    # believed and therefore not checked.
    self._nulls_cache[key] = found
    return found

  def _restyle_no_data_layer(self, tile_id, assignment):
    """Repaint one element's missing-value layer in place.

    Args:
      tile_id: the element whose paired layer is to be repainted.
      assignment: that element's row, read for its variable, its
        outline switch and its opacity.

    Returns:
      None. Does nothing when the element has no paired layer, which
      is the ordinary case -- most maps have no missing values and
      pay nothing here.

    The colour comes from the same record the run-landing path reads,
    `_quant_colours[tile][field][NO_DATA_KEY]`, so the two ways a map
    can be repainted cannot come to disagree. That key is a string
    rather than a class index, and `make_graduated_renderer`'s
    override loop skips anything that is not an integer, so it can
    never be mistaken for a class colour.
    """
    layer_id = self._no_data_layer_ids.get(tile_id)
    if not layer_id:
      return
    from qgis.core import QgsProject
    layer = QgsProject.instance().mapLayer(layer_id)
    if layer is None:
      return
    field = assignment.get("var")
    # A DEFERRING ELEMENT'S TWIN KEEPS ITS OWN STYLING, on the same
    # terms the element does. The paired layer sits in the layer tree
    # like any other, so a user can give it a hatch or a different
    # grey in Layer Properties -- and the run-landing path already
    # protects that, carrying `old_no_data_renderers[tid]` whenever
    # the element is kept by hand, which includes every deferring one.
    # This path called setRenderer unconditionally, so hand styling
    # survived a RE-TILE and was destroyed by a RESTYLE, which is the
    # more ordinary act of the two.
    #
    # Measured 2026-08-17: a twin hand-styled to #123456 came through
    # a spacing change intact and came out of an opacity nudge as a
    # categorized renderer painting #dddddd.
    #
    # OPACITY IS STILL SET BELOW, deliberately: it is the one control
    # that stays live while deferring, and the two layers are one
    # element to a reader, so they must fade together.
    if not self._element_is_deferring(tile_id):
      colours, kinds = self._absence_colours_and_kinds(
        tile_id, field, layer)
      layer.setRenderer(bridge.make_no_data_renderer(
        # the DICT even when empty: a bare string colours every kind
        # alike, and each kind has its own default in ABSENCE_KINDS
        colours, assignment.get("outline", False), kinds))
    # the same opacity as its element: they are one element to a
    # reader, and two layers fading differently would say otherwise
    layer.setOpacity(max(0, min(100, assignment.get("opacity", 100))) / 100.0)
    # THE FILE LEARNS AT SAVE (ruling of 2026-08-27). The change
    # above reaches the map, the project and the group's record
    # here; the GeoPackage is written by `_save_the_map`, in one
    # act with the record that describes it, so the two cannot
    # disagree. The paragraph above this is kept as HISTORY: it
    # argues for a write that used to happen at this line, and the
    # defect it describes is what the one-act save prevents.
    layer.triggerRepaint()

  def _absence_kinds_for(self, tile_id, field):
    """Which kinds of unplaceable value this element actually has.

    Args:
      tile_id: the element being asked about.
      field: the column it is coloured by; falsy answers an empty list.

    Returns:
      The ABSENCE_KINDS keys present, in that tuple's order, so the
      editor lists no data, negative infinity, infinity however
      the data arrived. Empty when the element has nothing unplaceable.

    Asked of the PAIRED LAYER when one exists, exactly as
    `_element_has_missing_values` does, since that layer is this
    element's own tiles; and of the region layer before a first run,
    which is the only thing that can say then -- accepting, as that
    method already does, that the region is map-wide and this element
    might not receive a tile on every kind.
    """
    if not field:
      return []
    from qgis.core import QgsProject
    stored = None
    paired = self._no_data_layer_ids.get(tile_id)
    if paired:
      layer = QgsProject.instance().mapLayer(paired)
      if layer is not None:
        index = layer.fields().indexOf(bridge.ABSENCE_FIELD)
        if index >= 0:
          stored = {str(v) for v in layer.uniqueValues(index)}
    if stored is None:
      source = self.layer_combo.currentLayer()
      if source is None:
        return []
      index = source.fields().indexOf(field)
      if index < 0:
        return []
      stored = set()
      for feature in source.getFeatures():
        value = feature[field]
        if not bridge.cannot_be_placed(value):
          continue
        if isinstance(value, float) and value == float("inf"):
          stored.add(bridge.ABSENCE_VALUE[bridge.POS_INF_KEY])
        elif isinstance(value, float) and value == float("-inf"):
          stored.add(bridge.ABSENCE_VALUE[bridge.NEG_INF_KEY])
        else:
          stored.add(bridge.ABSENCE_VALUE[bridge.NO_DATA_KEY])
    return [key for key, value, _label, _fill in bridge.ABSENCE_KINDS
            if value in stored]

  def _element_has_missing_values(self, tile_id, field):
    """Whether this element actually draws tiles with no value.

    Args:
      tile_id: the element being asked about.
      field: the column it is coloured by; None answers False.

    Returns:
      True when a no-data layer exists for this element, or -- before
      anything has been generated -- when the REGION layer has nulls
      in that column. False otherwise, including when either question
      cannot be answered, since offering a No data row that governs
      nothing is worse than not offering one.

    Two sources deliberately, in that order. Once a map exists, the
    paired layer IS the answer and cannot disagree with what is
    drawn. Before that, the colour editor still opens -- it works
    before a first Generate, which is a settled property of this
    window -- and the region layer is the only thing that can say.
    """
    if not field:
      return False
    paired = self._no_data_layer_ids.get(tile_id)
    if paired:
      from qgis.core import QgsProject
      layer = QgsProject.instance().mapLayer(paired)
      if layer is not None:
        return layer.featureCount() > 0
    source = self.layer_combo.currentLayer()
    if source is None:
      return False
    index = source.fields().indexOf(field)
    if index < 0:
      return False
    for feature in source.getFeatures():
      # the SAME question the split asks, through the same owner: this
      # decides whether the editor offers a No data row at all, and
      # scanning for NULL alone withheld it on a column whose only
      # unplaceable values were infinities
      if bridge.cannot_be_placed(feature[field]):
        return True
    return False

  def _absence_colours_and_kinds(self, tile_id, field, layer):
    """The per-kind colours for a paired layer, and the kinds it holds.

    Args:
      tile_id: the element the paired layer belongs to.
      field: the column that element is coloured by.
      layer: the paired layer itself, read for which kinds of absence
        its tiles actually carry.

    Returns:
      ``(colours, kinds)`` -- a dict keyed by the ABSENCE_KINDS keys
      holding whatever the user has picked, and the set of stored kind
      values present on the layer. `kinds` is None when the layer has
      no ABSENCE_FIELD column at all, which is every layer written
      before that column existed and every older GeoPackage reopened;
      the renderer then falls back to its single catch-all.

    ONE PLACE, because both the creating path and the repainting twin
    need the same answer and this feature has already paid twice for
    a rule written into one of a pair.
    """
    picks = self._quant_colours.get(tile_id, {}).get(field, {}) or {}
    colours = {key: picks.get(key)
               for key, _stored, _label, _fill in bridge.ABSENCE_KINDS
               if picks.get(key)}
    if layer is None:
      return colours, None
    index = layer.fields().indexOf(bridge.ABSENCE_FIELD)
    if index < 0:
      return colours, None
    return colours, {str(v) for v in layer.uniqueValues(index)}

  def _add_no_data_layer(self, assignment, tile_id, absent, group,
                         project, path, table_name=None, hand_opacity=None,
                         hand_renderer=None, hand_subset=None,
                         region_source=None):
    """Draw one element's missing-value tiles as their own layer.

    Args:
      assignment: the element's row, read for its outline switch, its
        variable and the colour picked for No data.
      tile_id: the element these tiles belong to.
      absent: the rows whose value is missing, as a GeoDataFrame --
        never empty, since the caller checks before asking.
      group: the output group this run is filling.
      project: the QgsProject the layer is registered with.
      path: the output GeoPackage, or falsy for memory output.
      table_name: the table its ELEMENT was written to, which this
        one's name is built from by adding "_no_data". Passed rather
        than recomputed so the pair cannot come to disagree: the
        element's name depends on the variable it displays and on
        which names this run has already spent, and neither is
        knowable from here. None falls back to the old bare
        ``tiles_<tid>`` form, which is what a caller predating the
        naming rule would produce.
      hand_opacity: the opacity the PREVIOUS paired layer carried, as
        a fraction, when the user had set it by hand in Layer
        Properties. None when there was none, in which case the row's
        own opacity is used.
      hand_renderer: the renderer the previous paired layer wore, when
        this element's own styling was kept this run. None means the
        dialog is restyling the element, so the twin is rebuilt with
        it. Passed only through the element's own gate, which is what
        keeps the colour editor's No data pick reaching the map.
      hand_subset: the filter the previous paired layer carried, or
        None. NOT gated, because a subset says which features to draw
        rather than how to colour them and is nobody's styling -- the
        same rule the element's own subset follows.
      region_source: the source string of the dataset this map was
        tiled from, which is stamped onto the layer exactly as it is
        onto the element beside it. None leaves the twin unstamped,
        which is what output made before that stamp existed looks
        like. PASSED rather than written by the caller afterwards,
        because the twin's style goes into the GeoPackage inside this
        call and a stamp written after it would reach the project and
        never the file.

    Returns:
      None. The layer is registered, added to the group directly
      beneath its element, and its id recorded in
      `_no_data_layer_ids` so the next run can drop exactly this one.

    WHY A SECOND LAYER RATHER THAN A CLEVERER RENDERER. QGIS's
    graduated renderer has nowhere to put a missing value, and the
    alternatives were worse: a rule-based renderer would replace the
    standard one a user opens the styling dock expecting to find, and
    baking the no-data areas into the graduated layer as an extra
    class would put a class in the legend that the CLASSIFIER does
    not know about, so pressing Classify in QGIS's own panel would
    silently destroy it. A paired layer keeps every renderer standard
    and every QGIS panel truthful.
    (Design settled by the maintainer, 2026-08-16.)

    The plugin's own table still shows ONE element: No data is one
    more class in its colour editor, and this layer is where that
    class is drawn. That is the whole of the "seamless" requirement --
    two layers in QGIS, one element in the dialog.
    """
    field = assignment.get("var")
    name = f"{tile_id} – no data"
    layer = bridge.gdf_to_layer(absent, name)
    if layer is None or not layer.isValid():
      return
    if path:
      # its own table, named for the element it belongs to, so a
      # GeoPackage opened elsewhere carries the same two layers and
      # the stale-table drop below can recognise it as ours
      written = bridge.write_gpkg_layer(
        layer, path, f"{table_name or f'tiles_{tile_id}'}_no_data",
        first=False)
      if written is not None and written.isValid():
        layer = written
    # A RENDERER THE USER BUILT IN QGIS OUTRANKS OURS, on exactly the
    # terms its element's does: `hand_renderer` arrives only when the
    # element itself was left alone this run, so the pair is either
    # both kept or both rebuilt and the colour editor's No data pick
    # still reaches the map. (Maintainer's ruling, 2026-08-16, after
    # two hunts found this layer's styling silently replaced while the
    # element's was preserved and announced.)
    colours, kinds = self._absence_colours_and_kinds(tile_id, field, layer)
    # ...BUT ONLY IF IT CAN STILL DRAW WHAT THIS LAYER HOLDS. The
    # element's gate is the wrong question for the twin, and answering
    # it alone left holes in the map. An element's graduated breaks
    # come from the whole region and survive a re-tile; the twin's
    # CATEGORIES enumerate the kinds of absence one tiling happened to
    # produce. Two ordinary Generates at different spacings can hand
    # an element a kind it did not have before -- and a carried
    # renderer has no category for it and no catch-all, so those tiles
    # painted NO INK AT ALL. Measured 2026-08-16 by rendering each
    # paired layer over a magenta ground: the uncovered rows came back
    # as the background while their neighbours drew #8c9fc7 and
    # #dddddd. The mirror case was on the same map: elements that LOST
    # a kind kept its legend entry, naming an absence nothing draws.
    #
    # So the carried renderer is used while it covers the kinds
    # present, and rebuilt otherwise. Hand styling survives the case
    # that matters -- the same kinds, re-tiled -- and a hole never
    # survives, which is the right way round: a lost custom fill is
    # visible and undoable, an unpainted area is neither.
    #
    # A renderer WITHOUT categories -- a single symbol, which is what
    # somebody usually sets in Layer Properties -- paints every
    # feature whatever its kind, so it covers everything by
    # definition. Only a CATEGORIZED renderer can fail to have an
    # entry for a value, and only that case is asked about. Treating
    # "no categories" as "covers nothing" threw away exactly the hand
    # styling this carry-over exists to preserve.
    enough = hand_renderer is not None
    if enough and hasattr(hand_renderer, "categories"):
      # bound before subscripting: a temporary from a QGIS getter
      # frees its contents
      existing = hand_renderer.categories()
      enough = {str(c.value()) for c in existing} >= set(kinds or ())
    if enough:
      layer.setRenderer(hand_renderer)
    else:
      layer.setRenderer(bridge.make_no_data_renderer(
        colours, assignment.get("outline", False), kinds))
    # TAGGED AS OUR OUTPUT like every other layer this run writes, or
    # the plugin would offer it back as a region layer to tile -- the
    # settled rule that tiling the tiles draws the next map on the
    # last one. `weavingspace_no_data` is what tells this layer apart
    # from the element beside it, which carries the same tile id.
    layer.setCustomProperty("weavingspace_output", True)
    layer.setCustomProperty("weavingspace_tile_id", tile_id)
    layer.setCustomProperty("weavingspace_no_data", True)
    # ...AND WHICH DATASET IT CAME FROM, exactly as its element is
    # stamped. The commit that gave every output layer this stamp
    # anchored on the element's own `weavingspace_tile_id` line and
    # never touched the twin's identical one, so the twins have gone
    # unstamped since. Nothing costs a user anything today: all four
    # readers drop a falsy stamp. What makes it a countdown rather
    # than a harmless omission is a group holding ONLY twins -- then
    # the set of stamps is empty, and the refusal that stops a run
    # writing over a map made from another dataset reads that as
    # output made before the stamp existed and goes quiet. (Found by
    # the paired-layer hunt, 2026-08-27; measured as held redundantly,
    # fixed because an omission ruled benign has gone live here three
    # hours after the accident hiding it was removed.)
    if region_source:
      layer.setCustomProperty("weavingspace_region", region_source)
    # THE SAME OPACITY AS ITS ELEMENT. The repainting twin sets this
    # and the creating path did not, so an element faded to 40% drew
    # its missing-value areas at full strength -- the hardest shapes
    # on an otherwise faded map, hiding whatever lay beneath -- until
    # some unrelated style change silently corrected it, which meant
    # the map a user exported was the wrong one and the map they saw
    # afterwards was right. Found by two hunts independently on
    # 2026-08-16, in the commit that added this method, whose twin
    # forty lines above carries a comment saying the two halves must
    # fade together. Writing that comment did not put the line here.
    # A hand-set opacity from the PREVIOUS paired layer outranks the
    # row's spin box, on the same promise the element's own hand-set
    # opacity has always had: the dialog did not choose it, so the
    # dialog does not overwrite it.
    layer.setOpacity(hand_opacity if hand_opacity is not None else
                     max(0, min(100, assignment.get("opacity", 100))) / 100.0)
    # ...AND ONLY THEN EMBED IT. `embed_style` writes what the layer
    # is wearing AT THAT MOMENT into the GeoPackage, so setting the
    # opacity afterwards fixed the layer in the project and left the
    # FILE saying 1.0 -- the map a user sends on was not the map they
    # made. Both twins already had this order; the first fix for the
    # opacity, made hours earlier the same day, put the new line
    # after the embed and so corrected only the half that was easy to
    # see. When a fix is inserted into an existing sequence, check
    # the ORDER against the twin, not merely the presence of a line.
    # THE TWIN IS WRITTEN BY SAVE, beside its element and under the
    # same table name plus `_no_data`. Nothing is embedded here for
    # the same reason nothing is embedded at the element's own
    # landing: a run draws, and a save writes.
    project.addMapLayer(layer, False)
    # UNDER ITS OWN ELEMENT rather than at the end of the group. A twin
    # carries its element's tile id, so it sorts equal to it and lands
    # directly below -- which is where it has always been, and stopped
    # being free the moment seeding order and panel order came apart
    # (ruling 5 of 2026-08-27).
    self._join_in_panel_order(group, layer, tile_id)
    # The user's own filter back on the fresh layer, after the style
    # and the registration, exactly where the element's own subset is
    # restored. A provider that refuses the clause is left unfiltered
    # rather than failing the run: a slightly wider map beats no map.
    if hand_subset:
      layer.setSubsetString(hand_subset)
    self._no_data_layer_ids[tile_id] = layer.id()

  def _restyle_only(self) -> bool:
    """Answer a style change by re-seeding the existing layers.

    Laying out a tiling is the expensive step, and a ramp or class
    count has nothing to do with it: the tiles on screen are already
    the right tiles. So when only symbology changed, this repaints
    them in place — no worker thread, no task, no flicker, and no
    waiting.

    Returns:
      True when the map was restyled here and no tiling is needed;
      False when the caller must do a full run (different geometry,
      nothing generated yet, or the layers have since been deleted).
    """
    project = QgsProject.instance()
    if self._last_geometry_sig is None or self._task is not None:
      return False
    if self.opt_new_group.isChecked():
      # "Create as new group" asks for a SECOND result to compare
      # against, which repainting the first one cannot provide, even
      # though nothing about the geometry changed
      return False
    if self._data_is_unobservable():
      # A layer that will not say how many features it has may have
      # been rewritten on a server since the last run, with nothing
      # locally to show for it. The fingerprint cannot see that, so
      # the fast path would repaint tiles built from data that is no
      # longer there. The user pressed Generate: re-tile, and let the
      # cost be the price of an answer that is actually current.
      return False
    if self._geometry_signature() != self._last_geometry_sig:
      return False
    if not self._element_layer_ids:
      return False
    layers = {tid: project.mapLayer(lid)
              for tid, lid in self._element_layer_ids.items()}
    if any(layer is None for layer in layers.values()):
      return False  # the user deleted the output; a full run rebuilds it
    assignments = {a["id"]: a for a in self._assignments()}
    if set(assignments) != set(layers):
      return False

    # NO RECONCILE HERE, AND THAT IS MEASURED RATHER THAN FORGOTTEN.
    # The tempting third route for unheard dock edits was to adopt
    # them at this point, just before the re-seed -- and it was
    # written, and it failed its own neighbours' tests within the
    # hour: at this moment the layer legitimately disagrees with the
    # row BECAUSE THE USER JUST CHANGED THE ROW, and a reconcile
    # cannot tell that from a dock edit, so it adopted the plugin's
    # own not-yet-replaced style as hand-picks and the new ramp could
    # never land (2026-08-20). What actually protects an unheard edit
    # here is the rule this path has always had: an element whose ROW
    # did not move is skipped as unchanged, so its layer -- dock edit
    # and all -- is left alone.

    # Class sources are loaded once per distinct token, as a full run
    # does. A file that cannot be read leaves its element ALONE and is
    # reported, which is the settled behaviour for a class source that
    # goes away: the map is not thrown away and the colours are not
    # reset, because a missing file is a reason to stop consulting the
    # file rather than a reason to repaint somebody's map
    # (test_a_class_source_that_moves_after_the_map_is_drawn).
    #
    # This path used to swallow the failure into `templates[token] =
    # None` and seed from nothing, so nudging any style control after
    # moving a QML repainted the element in automatic colours, with no
    # notice and the cell still naming the file. The re-tile twin five
    # hundred lines below collected the same failure into
    # `template_errors` and warned. Measured 2026-08-13.
    templates, template_errors, unreadable = {}, [], set()
    for token in {a.get("class_source") for a in assignments.values()
                  if a.get("class_source")}:
      try:
        templates[token] = (
          bridge.template_from_layer(project.mapLayer(token[6:]))
          if token.startswith("layer:")
          else bridge.load_categorized_template(token[5:]))
      except Exception as e:
        unreadable.add(token)
        template_errors.append(f"{token.split(':', 1)[1][-40:]}: {e}")

    # DONORS ARE RE-SEEDED BEFORE THEIR FOLLOWERS HERE TOO, and the
    # twin needs it for the same reason the landing does even though
    # nothing is replaced on this path: the templates above were read
    # BEFORE the loop, so an element re-seeded inside it leaves any
    # follower reached later reading the colours it had a moment ago.
    # A guard added at one door belongs at every door into the same
    # room, and this room is "the follower draws what the donor draws".
    def donor_for(tile_id):
      token = (assignments.get(tile_id) or {}).get("class_source") or ""
      if not token.startswith("layer:"):
        return None
      donor_layer = project.mapLayer(token[6:])
      named = (donor_layer.customProperty("weavingspace_tile_id")
               if donor_layer is not None else None)
      if named:
        return str(named)
      return next((t for t, other in layers.items()
                   if other.id() == token[6:]), None)

    order = self._seeding_order(
      sorted(layers, key=bridge.element_order), donor_for)
    reseeded = set()

    changed = []
    # the flag keeps _on_layer_style_edited from mistaking this very
    # seeding for a styling-dock edit and adopting our own colours
    self._applying_style = True
    try:
      for tid in order:
        layer = layers[tid]
        a = assignments[tid]
        signature = self._signature(a)
        # ...AND A FOLLOWER WHOSE DONOR JUST MOVED IS NOT "already
        # wearing what it should", however still its own row is. Its
        # class-source stamp was taken before this restyle began, so
        # the signature cannot see a donor THIS pass re-seeded.
        if self._last_signatures.get(tid) == signature \
            and donor_for(tid) not in reseeded \
            and not (a.get("mode_raw") != self.DEFERRING
                     and bridge.expressible_style(layer.renderer()) is None):
          continue  # this element is already wearing what it should
        # the follower reads the donor's layer AS IT NOW STANDS, which
        # on this path is the same object re-seeded in place
        source_token = a.get("class_source") or ""
        if source_token.startswith("layer:"):
          fresh = layers.get(donor_for(tid))
          if fresh is not None:
            try:
              templates[source_token] = bridge.template_from_layer(fresh)
              unreadable.discard(source_token)
            except Exception as e:
              unreadable.add(source_token)
              template_errors.append(
                f"{source_token.split(':', 1)[1][-40:]}: {e}")
        # ...the second half of that test is the RECLAIM case, and it
        # is here for the same reason as on the run-landing path: an
        # element taken back by picking the style it had before
        # deferral arrives with the signature it had before deferral,
        # so "already wearing what it should" is exactly wrong -- it
        # is wearing what QGIS built.
        if a.get("mode_raw") == self.DEFERRING \
            and bridge.expressible_style(layer.renderer()) is None:
          # A DEFERRING ELEMENT IS NOT RESTYLED, and this arm is the
          # twin of `carried_while_deferring` on the run-landing path.
          # It was missing, and the run-landing arm alone was not
          # enough: a dock edit moves this element's signature all by
          # itself, because `_assignments` resolves its mode to
          # "Deferring to QGIS" and _signature carries the mode -- so
          # the very next Generate came here with a moved signature
          # and re-seeded a graduated renderer over the work somebody
          # had just done in the styling panel. Measured 2026-08-15 by
          # a hunt: 640 interior pixels of the dock's green replaced by
          # two shades of the plugin's Blues, the row still reading
          # "Deferring to QGIS", and the message bar saying only
          # "restyled b (no re-tiling needed)".
          #
          # The lesson generalises past this feature: when a new mode
          # is added to a row, follow it into the SIGNATURE, because a
          # mode that moves the signature by itself arms every fast
          # path guarded on a moved signature.
          #
          # Opacity is still set below, which is right: it is the one
          # control that stays live while deferring.
          pass
        elif a.get("class_source") in unreadable:
          # The scheme this element draws from cannot be read, so it
          # KEEPS THE COLOURS IT IS WEARING. Everything else about the
          # element is still honoured -- the opacity below is usually
          # the very change that brought us here -- because refusing
          # that too would turn one unreadable file into a row whose
          # controls do nothing.
          pass
        else:
          # released before the seeding reads the record, for the
          # reason its twin gives at the landing: a held colour
          # outranks a template, so a late release repaints the map
          # with the colours the file had before it went away
          self._release_colours_kept_for_an_unreadable_source(a)
          bridge.seed_renderer(
            layer, a, templates.get(a.get("class_source")),
            self._classification_values(a.get("var")) if a.get("var")
            else None)
          # ...and anything following THIS element's layer must be
          # re-seeded after it rather than skipped as unchanged
          reseeded.add(tid)
          # WE JUST PAINTED IT, so this ladder is the baseline every
          # later dock edit is judged against. Read back off the layer
          # rather than from `a`, because a classifier can reduce,
          # snap or collapse what we asked for.
          self._remember_painted_ladder(layer, a["id"])
        # AN ELEMENT WHOSE CLASS SOURCE CANNOT BE READ OWNS WHAT IT
        # DRAWS, the twin of the landing's own line and asked in the
        # same place for the same reason: after the renderer is
        # settled, so that every route to a kept renderer is covered
        # rather than the one arm that names the file.
        if a.get("class_source") in unreadable:
          self._own_the_colours_of_an_unreadable_source(layer, a)
        # this element changed in the dialog, so its opacity is ours to
        # set; an element whose signature matched is skipped entirely
        # above, which is what leaves a hand-set opacity alone
        layer.setOpacity(max(0, min(100, a.get("opacity", 100))) / 100.0)
        # the fast path re-seeds without going through _add_output_layers,
        # so it has to record the hand-picked colours itself or a colour
        # chosen here would be missing from a project saved afterwards
        self._stamp_category_colours(layer, a)
        # THE FILE LEARNS AT SAVE (ruling of 2026-08-27). The change
        # above reaches the map, the project and the group's record
        # here; the GeoPackage is written by `_save_the_map`, in one
        # act with the record that describes it, so the two cannot
        # disagree. The paragraph above this is kept as HISTORY: it
        # argues for a write that used to happen at this line, and the
        # defect it describes is what the one-act save prevents.
        layer.setName(f"{tid} – {a['var']}" if a["var"]
                      else f"{tid} (no data)")
        # ...AND THE PAIRED LAYER, or the No data colour would be the
        # one colour in this window that needed a full re-tile to take
        # effect. It is a style change like any other, and the whole
        # purpose of this path is that a style change never re-tiles.
        self._restyle_no_data_layer(tid, a)
        self._last_signatures[tid] = signature
        changed.append(tid)
    finally:
      self._applying_style = False

    if changed and self.iface is not None:
      self.iface.messageBar().pushSuccess(
        "WeavingSpace",
        f"restyled {', '.join(changed)} (no re-tiling needed)")
    if template_errors:
      # the same words the re-tile path uses, so a user who meets this
      # on either path is told the same thing about the same file
      self._report_quietly(
        "Could not read the class colours file, so these elements "
        "keep their colours: " + "; ".join(template_errors))
    # A class count the column cannot support is reported HERE as well
    # as on the run path, and this is the path that usually meets it:
    # moving the Classes spinner is a style-only change, so it is
    # answered by a restyle and never reaches the run's notices at
    # all. Saying it on one path only is the twin asymmetry this
    # project has now paid for several times over. Deduplicated by
    # field, because several elements may carry the same column.
    # TWO DEDUP SETS, NOT ONE, and conflating them made a retirement
    # depend on something no user can see. `said` is about the LEGEND
    # NOTICE -- several elements may carry one column and one sentence
    # about it is enough. The pin retirement is per ELEMENT: each has
    # its own record and its own stamp. Sharing the set meant an
    # element's dead pin was retired or kept according to whether an
    # EARLIER element had happened to raise a legend notice about the
    # same column. Measured 2026-08-17: with the first element at k=20
    # its notice fires and the second element keeps its dead pin in
    # silence; at k=6 it does not fire and the second is retired and
    # announced. Same act, opposite answers.
    said = set()
    for tid in changed:
      a = assignments[tid]
      field = a.get("var")
      if not field or a.get("mode") != "Graduated":
        continue
      # the pin FIRST: retiring one changes how many classes the
      # legend note is about, so asking in the other order describes
      # a ladder that is about to stop existing
      retired = self._retire_an_undrawable_pin(field, a)
      if retired is not None:
        # ...AND THE LAYER IS RESTAMPED, because this path stamps
        # BEFORE it reaches here while its twin `_add_output_layers`
        # retires first and stamps afterwards, saying at that line why
        # ("the last moment before the value is stamped"). Both retire
        # calls were written in ONE commit and the order was reversed
        # on this side, so the twin's own explanation sat fifteen
        # hundred lines from the path that got it wrong.
        #
        # The cost was not cosmetic: the user was told the bound "has
        # been recalculated" while the retired number went onto the
        # layer anyway, so reopening the saved project restored a pin
        # the row displayed and the map ignored. Only this path can
        # meet it -- a class-count change is symbology, so the
        # run-landing twin never sees the case.
        #
        # WHEN A FIX IS WRITTEN INTO TWO PATHS IN ONE COMMIT, DIFF THE
        # TWO HUNKS AGAINST EACH OTHER rather than each against its
        # own neighbourhood.
        layer_now = QgsProject.instance().mapLayer(
          self._element_layer_ids.get(tid, ""))
        if layer_now is not None:
          fresh = self._assignment_for(tid)
          self._stamp_category_colours(layer_now, fresh or a)
          # THE FILE LEARNS AT SAVE (ruling of 2026-08-27). The change
          # above reaches the map, the project and the group's record
          # here; the GeoPackage is written by `_save_the_map`, in one
          # act with the record that describes it, so the two cannot
          # disagree. The paragraph above this is kept as HISTORY: it
          # argues for a write that used to happen at this line, and the
          # defect it describes is what the one-act save prevents.
        self._report_quietly(retired)
      # THE CONSTANT COLUMN IS ASKED HERE TOO, and this is the path
      # that meets it. A class-count change is symbology, so it is
      # answered by a restyle and never reaches the run's notices --
      # yet `_legend_size_note` returns None at one distinct value,
      # deliberately, because the constant sentence is that rule's
      # n == 1 instance and lives in `constant_field_message`. So the
      # restyle path said nothing at all: measured 2026-08-17 with the
      # spinner reading 8 over a map drawing one class, and the only
      # message was "restyled a". Asked in the same order and the same
      # words as the run route, so the two cannot come to disagree.
      constant_source = self._classification_values(field)
      region_values = (
        constant_source.uniqueValues(
          constant_source.fields().indexOf(field))
        if constant_source is not None else [])
      if region_values and bridge.numeric_values_are_constant(
          region_values):
        note = bridge.constant_field_message(field)
      else:
        note = self._legend_size_note(field, a, tid)
      # DEDUPED BY THE SENTENCE, NOT BY THE COLUMN. It was keyed on
      # the field, on the reasoning that several elements may carry
      # one column and one sentence about it is enough -- true until
      # 2026-08-17, when this notice became PER ELEMENT and started
      # measuring emptiness on the ladder each element actually draws.
      # After that two elements on one column produce two DIFFERENT
      # and equally true sentences, and keying on the field meant the
      # first silenced the second: measured with one element at k=5
      # reporting one empty class of five while its neighbour drew
      # twenty classes with two empty and was never mentioned, under a
      # sentence quoting a class count it does not have.
      #
      # Keying on the sentence keeps what the field key was FOR --
      # elements that genuinely have nothing new to say are still
      # silent -- without deciding for an element that its neighbour
      # has spoken on its behalf.
      if note is not None and note not in said:
        said.add(note)
        self._report_quietly(note)
    self._last_run_sig = self._run_signature()
    # ...and the rows are re-asked here too, because this path answers
    # a Generate WITHOUT going through _add_output_layers, where the
    # other call lives. Reclaiming an element the user had styled in
    # QGIS is exactly a no-design-change Generate, so without this the
    # element was correctly re-seeded and its row's controls stayed
    # inert -- a row the plugin had taken back that the user could
    # still not touch. Measured 2026-08-15 by tracing which calls
    # actually fired.
    self._refresh_deferring_rows()
    # ...AND THE GROUP'S RECORD FOLLOWS THE RESTYLE. A style-only
    # change never reaches `_add_output_layers`, where the other stamp
    # lives, so without this line a ramp or a class count chosen after
    # the last re-tile was on the map and absent from the record --
    # and choosing the group again would have handed back a symbology
    # the user had moved on from. That asymmetry is the shape this
    # project already knows from `_stamp_category_colours` and from
    # the pin retirement, which is why it is being written in the same
    # commit as the stamp it pairs with rather than found later.
    self._stamp_working_state(
      self._group_of_our_layers(QgsProject.instance().layerTreeRoot()))
    # ...AND SO DOES THE FILE'S RECORD, WHICH IS THE SECOND DOOR. The
    # paragraph above argued exactly this case and then mended one
    # store of two: the group's record was given a write here on
    # 2026-08-25, and the FILE's record was added to the landing alone
    # later the same evening, so it inherited the gap it was written
    # to close. Found by a hunt on 2026-08-26, reading the file's own
    # metadata through GDAL: change a ramp and Generate -- a restyle,
    # no re-tile -- and the file's STYLES were updated while the
    # file's RECORD still described the map from before, so a
    # colleague opening that GeoPackage without the project resumed a
    # design the user had abandoned and their first Generate repainted
    # the map back to it. The file disagreed with itself.
    # A RESTYLE DOES NOT WRITE THE FILE either, and the store it
    # used to keep in step is kept in step by Save writing the
    # tables, the styles and the record together.
    return True

  def _run_signature(self):
    """Everything that affects the output, as one comparable tuple;
    live update skips regenerating when this equals the last run's
    (reopening the dialog, for instance, changes nothing)."""
    layer = self.layer_combo.currentLayer()
    kwargs = self._unit_kwargs()
    kwargs.pop("spec", None)
    return (
      layer.id() if layer is not None else None,
      self.family_combo.currentText(), self.n_combo.currentData(),
      tuple(sorted(kwargs.items())),
      self.mod_rotate.value(), self.mod_scale_x.value(),
      self.mod_scale_y.value(), self.mod_skew_x.value(),
      self.mod_skew_y.value(), self.mod_p_inset.value(),
      self.mod_t_inset.value(), self.mod_glyph.isChecked(),
      self.opt_join_prototiles.isChecked(), self.opt_retain.isChecked(),
      self.opt_clip.isChecked(), self.opt_icons.isChecked(),
      self.opt_outlines.isChecked(),
      self.gpkg_widget.filePath().strip() or None,
      # The three STYLE items at the end are the ones _signature
      # carries, and they are here for a reason measured on
      # 2026-08-13: the live tick RETURNS on an unchanged signature
      # WITHOUT reaching _restyle_only, so anything missing from this
      # tuple can never be applied on the live path at all. A
      # hand-picked colour changed with live update on, and nothing
      # else touched, was simply swallowed -- the editor and the
      # table both showing it as applied while the map went on
      # without it. Including them costs nothing: the geometry
      # signature is unchanged, so the run that follows is a restyle
      # in place rather than a tiling. Guarded by
      # test_a_pick_is_not_swallowed_by_the_live_path.
      tuple((a["id"], a["var"], a["mode"], a["ramp"], a["scheme"],
             a["k"], a["outline"], a["class_source"],
             a.get("class_source_stamp"),
             a.get("single_colour"), a.get("reverse", False),
             a.get("opacity", 100),
             tuple(sorted((a.get("category_colours") or {}).items())),
             tuple(sorted((a.get("quant_colours") or {}).items())),
             # a copied ladder puts a LIST in this record, and a
             # tuple holding a list cannot be hashed; a signature
             # nobody can hash is one nobody may put in a set
             tuple(sorted(
               (key, tuple(value) if isinstance(value, list) else value)
               for key, value in (a.get("pinned") or {}).items())),
             tuple(a.get("range_bounds", (0, 100))))
            for a in self._assignments()),
      # See _geometry_signature: live update compares this tuple to
      # decide a run would be a no-op, and an edit to the layer must
      # not look like one.
      self._layer_fingerprint(), self._data_version,
    )

  def _class_source_stamp(self, token):
    """What is INSIDE a class-source file, cheaply enough to ask on
    every debounce tick.

    Args:
      token: an element's ``class_source`` -- ``file:<path>`` for a
        QML, ``layer:<id>`` for a donor layer, or None/"" for none.

    Returns:
      For a QML, ``(token, (mtime_ns, size))``; for a donor layer,
      ``(token, ((value, colour, label), ...))`` taken from the
      template that layer would hand over; for anything else the token
      unchanged. The value goes into both signatures, so a change to
      either kind of source moves them and the element is re-seeded.

    Why this exists: the signatures carried the TOKEN alone, so a
    scheme rewritten on disk left every signature equal. Pressing
    Generate repainted nothing and said nothing, and the user got
    their old colours back with no indication why. Measured
    2026-08-13.

    Why a MISSING file deliberately does not move the stamp: the last
    reading is returned instead. Losing the file is not an edit, and
    the settled behaviour when a class source goes away is to keep the
    map and stop consulting the file, telling the user once
    (test_a_class_source_that_moves_after_the_map_is_drawn). Letting
    the disappearance move the signature would re-seed the element
    from nothing, which is exactly the repaint that behaviour exists
    to prevent.

    Why mtime and size rather than a hash: this is asked on every
    debounce tick, and a hash means reading the whole file each time
    to answer a question whose wrong answer costs one extra restyle.
    A rewrite that preserves both is possible in principle and has no
    consequence a user would notice.
    """
    if not token:
      return token
    if token.startswith("layer:"):
      # A DONOR LAYER IS CONTENT TOO, and it entered both signatures
      # BARE -- so an element declaring "take my classes from element
      # c" followed c once and never again. Recolour c, press
      # Generate, and c changes while d keeps the ladder it was given
      # minutes ago: two elements on one column drawing "crops" in
      # different colours, silently and for good, which is the
      # one-colour-one-meaning rule broken by the very control that
      # exists to uphold it. The QML half of this function has been
      # stamped by content since 2026-08-13; this half was not.
      # (Found by the collateral sweep, 2026-08-27.)
      #
      # FINGERPRINTED THROUGH `template_from_layer`, which is what the
      # dependent actually CONSUMES, so the stamp cannot come to
      # disagree with the thing it is stamping. It costs a clone per
      # category on each tick, where the QML half deliberately avoids
      # a hash for the same reason -- but this reads a renderer in
      # memory rather than a file, and the count is bounded by
      # `bridge.MANY_CATEGORIES` rather than by the size of anybody's
      # data.
      #
      # A DONOR THAT CANNOT BE READ RIGHT NOW returns the last
      # reading, exactly as a missing QML does and for the same
      # settled reason: losing a source is not an edit, and moving
      # the signature on it would re-seed the element from nothing.
      donor = QgsProject.instance().mapLayer(token[6:])
      try:
        template = bridge.template_from_layer(donor)
      except Exception:
        return (token, self._class_source_stamps.get(token))
      stamp = tuple(sorted(
        (value, symbol.color().name(), label)
        for value, (symbol, label) in template.items()))
      self._class_source_stamps[token] = stamp
      return (token, stamp)
    if not token.startswith("file:"):
      return token
    path = token[5:]
    try:
      info = os.stat(path)
      stamp = (info.st_mtime_ns, info.st_size)
      self._class_source_stamps[token] = stamp
    except OSError:
      stamp = self._class_source_stamps.get(token)
    return (token, stamp)

  @staticmethod
  def _signature(a: dict) -> tuple:
    """The settings that decide one element's symbology.

    Args:
      a: one dict from ``_assignments()``.

    Returns:
      A tuple usable as a dictionary key. Regeneration compares it
      with the value stored from the previous run: unchanged means
      the element keeps the renderer it already has, so a style
      refined by hand in QGIS's styling dock survives; changed means
      it is re-seeded from the dialog.

    Note what is absent — spacing, family, modifiers. Those alter the
    GEOMETRY, not what the colours mean, so a design change should
    not throw away the user's styling work.

    THE DATA IS NOT IN THAT LIST, and the distinction cost a wrong
    map. `value_digest` summarises the column this element draws, and
    it belongs here for the reason the geometry does not: if the
    values move, what a colour MEANS moves with them. It is the
    COLUMN'S own digest rather than the dialog's edit counter,
    because that counter also bumps for a column being ADDED, and
    re-seeding on that destroys hand styling which had every right to
    survive. Without it
    an element whose assignment had not changed kept the renderer it
    already had, so a column retyped in QGIS's editing session from
    0..121 down to 0..3 went on being drawn with the old data's
    quantiles — classes running to 121 over data reaching 3, four of
    five wearing nothing and every tile in the first, which is the
    flat no-data look this plugin's other guards exist to prevent.
    Measured 2026-08-15, and two nearer fixes (the classification
    cache's key, an unusable pin) each corrected a real fault without
    touching this one.

    The cost is deliberate: a data edit now RE-SEEDS, so styling
    refined in QGIS's dock does not survive one. That is the right
    way round, because the alternative is keeping a legend that
    describes numbers the layer no longer holds.
    """
    # Hand-picked category colours belong here for the same reason
    # the ramp does: they decide what this element looks like, and
    # _restyle_only re-seeds exactly the elements whose signature
    # moved. Sorted into a tuple because a dict is unhashable and
    # because two identical sets of choices must compare equal
    # whatever order they were picked in.
    picked = a.get("category_colours") or {}
    quant = a.get("quant_colours") or {}
    return (a["var"], a["mode"], a["ramp"], a["scheme"], a["k"],
            a.get("value_digest"),
            a["outline"], a.get("class_source"),
            # the file's CONTENTS, not merely its name: see
            # _class_source_stamp
            a.get("class_source_stamp"), a.get("single_colour"),
            a.get("reverse", False), a.get("opacity", 100),
            tuple(sorted(picked.items())),
            # graduated customization is symbology like everything
            # else here: positional picks, the display window and the
            # pinned bounds all re-seed exactly the elements they
            # changed. A pin missing from here would be recorded and
            # never drawn, which is what the display range was
            # measured doing on 2026-08-13.
            tuple(sorted(quant.items())),
            # a copied ladder puts a LIST in this record, and a
            # tuple holding a list cannot be hashed; a signature
            # nobody can hash is one nobody may put in a set
            tuple(sorted(
              (key, tuple(value) if isinstance(value, list) else value)
              for key, value in (a.get("pinned") or {}).items())),
            tuple(a.get("range_bounds", (0, 100))))

  # ---------------------------------------------------------------- generate

  def _generate(self, live: bool = False):
    """Validate, guard, and launch one tiling run as a background task,
    unless the change was only ever about colour.

    ``live=True`` marks automatic (debounced) runs: they fail silently
    where a button press would pop a message box, and they skip the
    are-you-sure confirmation. The path from here: build a CRS-less
    copy of the inputs, run weavingspace's Tiling in the task's worker
    thread, then ``done`` reattaches the CRS and hands the result to
    ``_on_generated`` on the main thread. ``done`` also reports the
    run's coverage: how many areas of the region the pattern missed
    entirely, which is a fact about the map rather than a fault, and
    goes to the message bar rather than a dialog.
    """
    if self._task is not None:
      # One run at a time, and this one reruns when that one is done.
      # WHICH KIND of rerun is the question, and one flag answering it
      # for both is what went wrong: a queued live tick is honoured by
      # restarting the live timer, whose handler refuses whenever live
      # update is off -- so a queued BUTTON press was handed to a path
      # that could not run it. A press is remembered as a press and
      # re-pressed by `_finish_run`.
      if live:
        self._live_pending = True
      else:
        self._press_pending = True
      _dump("GEN-GATE", "already-running", "live=", live)
      return
    # A REQUEST FOR A SECOND MAP CANNOT BE ANSWERED BY REPAINTING THE
    # FIRST. "Create as new group" has always taken the full path --
    # it is a settled decision, and the comparison escape hatch the
    # whole feature exists for -- and the group chooser's "Create new"
    # is the same request arriving through the control that replaced
    # it. Until 2026-08-28 it was not honoured here: choosing it and
    # pressing Generate with nothing else changed took the fast path,
    # so no second map appeared, nothing was said, and the request
    # stayed ARMED -- to fire on some later, unrelated run, which then
    # forked the map instead of replacing it in place. Measured with
    # the dumps on: `GEN-GATE restyled-instead`, one group, still
    # armed; then an ordinary spacing nudge, two groups.
    # The flag is spent by a LANDING, so the run has to be one.
    if not live and not self._new_group_chosen and self._restyle_only():
      # ...AND THE PREVIEW LEARNS WHAT WAS PAINTED, exactly as the
      # live path's restyle exits do. With live update off nothing
      # repaints the preview at pick time -- preserve, do not repaint
      # -- so the Generate that answers the change is the one moment
      # the preview can catch up, and without this pair it rested on
      # the previous design's colours while the map and table agreed
      # on the new ones. Found by the preview hunt of 2026-08-26
      # (round nine): the promise has four doors, and this one and
      # the source-gone exit never had the pair the other two carry.
      self._refresh_preview_colours()
      _dump("GEN-GATE", "restyled-instead")
      return  # the button pressed after a style change: instant
    layer = self.layer_combo.currentLayer()
    if layer is None:
      _dump("GEN-GATE", "no-region-layer", "live=", live)
      if not live:
        QMessageBox.warning(self, "WeavingSpace", "Choose a region layer.")
      return
    if self._preview_timer.isActive():
      # A design change schedules the unit rebuild a debounce later, so a
      # Generate pressed inside that window would tile the PREVIOUS
      # design (an integration test comparing the output against a
      # direct library call caught this). Flush the pending rebuild
      # first: the settings on screen are what the user asked for.
      self._preview_timer.stop()
      self._rebuild_unit()
    if self._unit is None:
      self._rebuild_unit()
    if self._unit is None:
      _dump("GEN-GATE", "no-unit", "live=", live)
      if not live:
        QMessageBox.warning(self, "WeavingSpace",
                            "The tile unit could not be built.")
      return
    # An inset large enough to swallow elements is checked BEFORE the
    # variable guard below, because when it has taken all of them the
    # table is empty and that guard fires -- telling the user to
    # assign a variable to a design that no longer has anywhere to put
    # one. The inset is what they changed and the inset is what the
    # sentence should name. Where it has taken only SOME, the
    # survivors are slivers and the library's overlay refuses them, so
    # this refusal replaces a modal quoting geopandas internals.
    #
    # Asked only when the inset is actually set, so that a design
    # losing elements for some other reason is never blamed on a
    # control the user left alone. With no inset the two counts agree
    # for every design in the catalogue: 247 of 247, measured
    # 2026-08-13, which is what makes the comparison safe to gate a
    # refusal on.
    collapse = bridge.inset_collapse_message(
      int(self.n_combo.currentData() or 0), len(self._tile_ids()),
      self.mod_t_inset.value()) if self.mod_t_inset.value() else None
    if collapse is not None:
      _dump("GEN-GATE", "inset-collapse")
      if not live:
        QMessageBox.warning(self, "WeavingSpace", collapse)
      else:
        self._report_quietly(collapse)
      return

    assignments = self._assignments()
    if not any(a["var"] for a in assignments):
      _dump("GEN-GATE", "no-variable", "live=", live)
      if not live:
        QMessageBox.warning(
          self, "WeavingSpace",
          "Assign at least one variable in the Data & colours tab.")
      return

    path_now = self.gpkg_widget.filePath().strip() or None
    # ASK THE FILE, not this dialog's memory. `_last_path` records
    # only what THIS instance last wrote, so a reopened project -- a
    # fresh dialog that remembers nothing -- would tick "create as new
    # group" to keep yesterday's map and overwrite it without a word.
    # Measured 2026-08-16: 41/40/41/40 features became 113/112/113/112
    # with no warning and no modal. A file outlives a session, and a
    # guard on session state cannot protect one.
    # KEEPING A RESULT IS KEEPING ITS FILE TOO, and this guard used to
    # ask only whether the user had TICKED the box. Three other things
    # now keep a previous result -- a change of dataset, a landing
    # whose group was made from another dataset, and the fresh-group
    # flag -- and on those routes the group was spared while the run
    # wrote into the same GeoPackage anyway: a hunt measured tiles_a
    # and tiles_b rewritten with the new dataset's columns and
    # tiles_c/tiles_d DROPPED, leaving the kept group drawing dead
    # layers under its own names. The panel was protected and the file
    # was destroyed. So the question is the one the GROUP asks:
    # is this run keeping somebody else's result?
    #
    # EVERYTHING ABOVE THIS LINE IS HISTORY, kept because the harm it
    # measured is what Save must now not repeat rather than because
    # anything here acts on it.
    # A RUN CANNOT OVERWRITE ANYTHING, so the gate that stood here is
    # gone. (Ruling of 2026-08-27.) It refused a Generate whose output
    # path would have written over a result the user had asked to
    # keep -- through a MODAL, which in a headless run left the
    # message bar empty and read as a Generate that did nothing. Its
    # whole subject was the file a run was about to write, and a run
    # writes no file now.
    # WHAT REPLACES IT IS AT SAVE, where the writing happens:
    # `_may_overwrite` asks before writing over a file this map did
    # not write. That is the maintainer's own wording -- with Save a
    # deliberate press, asking every time is noise, and a file
    # somebody else's map is in is not.

    from . import compat
    if not compat.layer_data_is_available(layer):
      # Reading from a layer whose source has gone is not merely an
      # error: extent() alone segfaults QGIS. Refuse while there is
      # still a plugin here to refuse with.
      _dump("GEN-GATE", "source-gone", "live=", live)
      if not live:
        QMessageBox.critical(
          self, "WeavingSpace",
          "That layer's data is no longer available. Reload it in "
          "QGIS, or choose another layer.")
      return

    fields = sorted({a["var"] for a in assignments if a["var"]})
    try:
      region = bridge.layer_to_gdf(layer, fields)
    except Exception as e:
      # live runs report quietly, like every other failure on this
      # path. This one popped a modal on the debounced path until
      # 2026-08-12: CLAUDE.md forbids unconditional modal dialogs on
      # generation paths (one hung the suite for thirty-one minutes),
      # and _generate's own docstring says a live run fails silently
      # where a button press would pop a box. Two branches did not.
      if live:
        self._report_quietly(f"Could not read the layer: {e}")
      else:
        QMessageBox.critical(self, "WeavingSpace", str(e))
      return

    # ---- size guard: small spacing on a big extent segfaults QGIS by
    # exhausting memory inside GEOS, so refuse pathological requests
    # the guards, in order of severity. The estimate is deliberately
    # cheap and slightly generous: refusing a map that would have
    # worked is a nuisance, but attempting one that exhausts memory
    # inside GEOS takes QGIS down with it
    # THE SAME QUESTION, ASKED THE RIGHT WAY IN ICON MODE. `as_icons`
    # used to be read fifty lines below this gate, so the guard that
    # decides whether the run happens at all had never heard of the
    # mode -- and refused designs of a hundred tiles while advising a
    # spacing that would only have drawn bigger icons. Read here
    # instead, and passed down unchanged. Ledger row 3.
    as_icons = self.opt_icons.isChecked()
    if as_icons:
      est = bridge.estimate_icon_count(self._unit, len(region))
    else:
      est = bridge.estimate_tile_count(self._unit, region)
    # ONE QUESTION, WHOSE WORDING ESCALATES BY BAND (maintainer's
    # ruling, 2026-08-25: "Warning not absolute. Find a different
    # approach to sentinel if appropriate."). What used to stand here
    # were two gates: a refusal above MAX_TILES_HARD on a comment
    # claiming the run would exhaust memory and kill QGIS, and a
    # question above MAX_TILES_CONFIRM. The refusal had already been
    # wrong in the expensive direction -- it declined a map the library
    # renders in five seconds -- and the figure it stood on is one
    # nothing here measures: different machines have different
    # maximums, and different designs have different needs at the same
    # count.
    #
    # WHAT IS KEPT is everything the refusal got right: the workable
    # spacing it suggested, and icon mode's own sentence, since a
    # spacing cannot help where each area takes one tile unit however
    # large it is drawn. WHAT IS ADDED is what a refusal never said --
    # that this may exhaust memory, that QGIS may stop responding, and
    # to save the project first.
    band = bridge.size_band(est)
    if band == "refuse":
      # NOT A SIZE AT ALL, and this is why the sentinel had to be
      # split off before the ceiling could soften: a design that does
      # not tile the plane, and a layer whose extent cannot be
      # measured, are facts rather than quantities. No question may
      # soften them, and each now says its own true thing instead of
      # borrowing the too-many-tiles advice, which helped neither.
      if not live:
        QMessageBox.critical(
          self, "WeavingSpace",
          bridge.untileable_message() if est == bridge.UNTILEABLE
          else bridge.uncountable_message())
      return
    if not live and band in ("ask", "heavy"):
      if band == "ask":
        question = bridge.many_tiles_question(est)
      elif as_icons:
        question = bridge.heavy_tiles_question(
          est,
          f"Spacing will not help, since each of this layer's "
          f"{len(region):,} areas takes one tile unit however large it "
          f"is drawn; a layer with fewer areas or a tileable with "
          f"fewer elements would.")
      else:
        suggestion = bridge.min_reasonable_spacing(
          self._unit, region, self.spacing_spin.value())
        question = bridge.heavy_tiles_question(
          est,
          f"A spacing of about {bridge.spacing_in_words(suggestion)} "
          f"map units or more would keep it smaller.")
      answer = QMessageBox.question(
        self, "WeavingSpace", question,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        # THE SAFE BUTTON IS THE DEFAULT, on the dependency-consent
        # precedent: a stray Return must not start something that may
        # take the machine.
        QMessageBox.StandardButton.No)
      if answer != QMessageBox.StandardButton.Yes:
        return

    # CRITICAL: the worker thread must never touch pyproj/PROJ. QGIS uses
    # the same PROJ library from the main thread, and concurrent use
    # segfaults the whole application (this was the intermittent crash on
    # spacing changes). The tiling is pure geometry, so strip CRS from
    # everything the worker sees and reattach it on the main thread after.
    import copy
    result_crs = region.crs
    region = region.copy()
    region.crs = None
    unit = copy.deepcopy(self._unit)
    unit.crs = None
    for attr in ("tiles", "prototile", "regularised_prototile"):
      part = getattr(unit, attr, None)
      if part is not None:
        part.crs = None

    # Trace each tile back to the area it took its data from. The
    # column goes on the worker's copy of the region, travels with the
    # library's own attribute join onto the tiles, and comes off again
    # inside the worker, so nothing downstream ever sees it. This is
    # what makes the coverage count below a set difference over one
    # integer column rather than a second spatial pass.
    unit_id_column = bridge.add_unit_ids(region)
    unit_count = len(region)
    # Written on the worker thread, read on the main thread in done().
    # Safe without a lock: QGIS delivers finished() as a queued signal
    # after run() has returned, so the write happens-before the read
    coverage = {"missing": None}

    # `as_icons` was read at the size guard above, deliberately: one
    # read means the gate and the run cannot disagree about which mode
    # this is.
    join_proto = self.opt_join_prototiles.isChecked()
    retain = self.opt_retain.isChecked()
    ragged = not self.opt_clip.isChecked()

    def work(task):
      from weavingspace import Tiling
      task.setProgress(5)
      tiling = Tiling(unit, region, as_icons=as_icons)
      if task.isCanceled():
        return None
      task.setProgress(40)
      tm = tiling.get_tiled_map(
        join_on_prototiles=join_proto,
        retain_tileables=retain,
        ragged_edges=ragged)
      task.setProgress(90)
      # Count here, where the tiled frame is already in memory and
      # still carries the tracing column; the same call strips the
      # column off again. Measured at 1% of the run on the packaged
      # Auckland data (tools/measure_coverage_warning.py)
      coverage["missing"] = bridge.count_units_without_tiles(
        tm.map, unit_id_column, unit_count)
      return None if task.isCanceled() else tm.map

    self.generate_btn.setEnabled(False)
    self.progress.setVisible(True)
    self.progress.setRange(0, 100)

    family = self.family_combo.currentText()
    path = path_now
    # Snapshot the signatures NOW, alongside the assignments, because
    # they describe what THIS run is about to draw. Recording them on
    # completion instead reads the table as it stands then, which may
    # already carry a change the user made while the tiling ran: the
    # map would be drawn with the old settings while the dialog
    # believed it matched the new ones, and every later check —
    # including live update's "has anything changed?" — would agree
    # that nothing needed doing. That is how a ramp picked mid-run
    # went missing.
    run_sig = self._run_signature()
    geometry_sig = self._geometry_signature()
    # Snapshotted WITH the signature it belongs to. The landing acts
    # on this switch rather than baking it into the tiling, so
    # reading it live at the landing let a mid-run toggle cancel its
    # own signature difference and leave the box inert for good; see
    # _add_output_layers for the measurement.
    outlines_at_launch = self.opt_outlines.isChecked()
    # ...and whether this run drew icons, for the same reason: the
    # coverage notice below is about the map THIS run made
    icons_at_launch = self.opt_icons.isChecked()
    # Snapshotted for the same reason: the coverage notice names the
    # spacing THIS map was tiled at, and the user is free to type a
    # different one while it runs. map_unit_label reads the layer, so
    # it also has to happen here on the main thread
    spacing_used = self.spacing_spin.value()
    # ...AND THE DESIGN THIS RUN IS ABOUT TO DRAW, for the record the
    # group will carry. The stamp at the landing re-reads the ELEMENT
    # half live, because hand-picked colours are settled policy to
    # re-read there, but the DESIGN half must be the one that was
    # tiled: a spacing typed while the tiling ran belongs to the next
    # run, and a group whose record claimed a design its own layers
    # were not drawn at would be a false statement stored in somebody
    # else's project. Same reasoning, and the same shape, as the
    # signatures a few lines above.
    state_at_launch = self._capture_working_state()
    unit_label = bridge.map_unit_label(layer)
    # Asked of the LAYER, because layer_to_gdf has already dropped
    # these rows out of the frame: a geometry-less row cannot be
    # tiled, and until now it vanished without a word, leaving a user
    # to compare their attribute table against the map and find one
    # row unaccounted for.
    blank_areas = bridge.count_areas_with_no_geometry(layer) \
      if self._source_layer_alive(layer) else 0

    def done(gdf, error):
      if gdf is not None and result_crs is not None:
        gdf.crs = result_crs  # reattach on the main thread (pyproj-safe)
      self._on_generated(gdf, error, family, layer, assignments, path,
                         run_sig, geometry_sig, live, outlines_at_launch,
                         state_at_launch)
      # The coverage notice goes out AFTER _on_generated, never inside
      # it: that method's finally clears live_note, which is where
      # _report_quietly writes when there is no QGIS window (headless
      # runs, the test harness), so a notice pushed earlier would be
      # wiped a moment later. A run that failed, was cancelled, or
      # produced nothing at all has already said so more loudly
      if error is None and gdf is not None and len(gdf) > 0:
        # ICON MODE GETS ITS OWN SENTENCE FOR THE SAME COUNT, because
        # "appear nowhere on the map" is false there: one unit is
        # placed on each area, so an icon IS drawn and what the count
        # marks is an area whose icon carries a NEIGHBOUR'S value.
        # (Maintainer's ruling, 2026-08-19, on a question the
        # `coverage_message` docstring had carried as open since
        # 2026-08-16.)
        note = (bridge.icon_misattribution_message
                if icons_at_launch else bridge.coverage_message)(
                  coverage["missing"], unit_count, spacing_used,
                  unit_label)
        if note is not None:
          self._report_quietly(note)
        # ...and in ICON MODE, the loss the map-wide count cannot
        # see. One tileable per area is the promise there, so an
        # element carrying fewer tiles than the region has areas is
        # missing icons -- while `coverage["missing"]` stays zero
        # because the other elements still draw those areas. Asked
        # only for icons, since in ordinary tiling an element having
        # fewer tiles than there are areas is the normal case.
        if outlines_at_launch is not None and icons_at_launch:
          short = {}
          for tid, lid in self._element_layer_ids.items():
            element = QgsProject.instance().mapLayer(lid)
            if element is None:
              continue
            # BOTH HALVES, or every gap in the column becomes a
            # fabricated notice. An element whose variable has missing
            # values keeps its icons for those areas on the PAIRED
            # layer, so counting the element alone reports it short by
            # exactly the number of gaps -- and since every element on
            # that column is short by the same amount, the sentence
            # named all four while saying the others still drew them,
            # which refutes itself. Measured 2026-08-16 on a 36-area
            # region with one gap: both halves sum to 36 of 36 on
            # every element, against a notice claiming up to 1
            # missing. This is the FOURTH reader to count an element
            # by `_element_layer_ids` alone since the paired layer
            # arrived; the commit before the one that added this loop
            # is called "Every count against the library now counts
            # both halves of an element".
            paired = QgsProject.instance().mapLayer(
              self._no_data_layer_ids.get(tid) or "")
            # ASK THE GEOMETRY, NOT THE ARITHMETIC. This was
            # `unit_count - drawn` until 2026-08-28: an AREA count
            # minus a TILE count, which is not the number of areas
            # without this element's icon in either direction. A
            # unit's tile sits off the centre it was placed at, so an
            # element's tile can fall wholly outside the small area it
            # belongs to while a neighbour's overhangs into it --
            # measured that day on 155 Auckland areas, where the
            # sentence named b, c and d while element a was the one
            # missing from three areas and b was missing from none.
            # The registered test could not see it because it checked
            # the sentence against this same arithmetic rather than
            # against the map.
            missing_here = self._areas_no_icon_reaches(element, paired)
            if missing_here > 0:
              short[str(tid)] = missing_here
          note = bridge.icon_coverage_message(
            short, unit_count, spacing_used, unit_label)
          if note is not None:
            self._report_quietly(note)
        # ...and separately, the rows that could not be drawn at all.
        # Its own sentence because the coverage one names a spacing as
        # the thing to change, and no spacing draws a row with no
        # geometry.
        note = bridge.unmappable_areas_message(
          blank_areas, unit_count + blank_areas) if blank_areas else None
        if note is not None:
          self._report_quietly(note)
        # And whether any categorical field's class count moved since
        # the last run: if it did, the colours of the classes that
        # were already there have moved with it. Counted from the
        # frame in hand, which already holds the values that were
        # mapped, so this costs a nunique() per categorical element
        # and no second pass over the data.
        note = getattr(self, "_pending_colour_note", None)
        if note is not None:
          self._report_quietly(note)
          self._pending_colour_note = None
        # A ramp this row names that the style library does not hold.
        # The renderers have already drawn the map in a substitute
        # (see bridge.ramp_or_default); this is the half the user can
        # read, and without it the only symptom is colours nobody
        # chose. DECIDED HERE rather than inside the builders, which
        # promise a renderer and must not start refusing -- and said
        # ONCE PER NAME, since several elements commonly share a ramp
        # and one sentence per element is how a notice becomes noise.
        said_missing = set()
        for assignment in assignments:
          name = assignment.get("ramp")
          if not name or name in said_missing:
            continue
          if assignment.get("mode") not in ("Graduated", "Categorized"):
            continue          # a single-colour row draws no ramp
          if bridge.get_ramp(name) is None:
            said_missing.add(name)
            self._report_quietly(bridge.missing_ramp_message(name))
        # A column that turned out to hold one value everywhere. The
        # renderer has already collapsed to a single class (see
        # bridge.make_graduated_renderer); this is the half of it the
        # user can read. Taken from the frame just mapped rather than
        # from the layer, which is where the values actually went, and
        # deduplicated because several elements may share one field.
        # TWO KINDS OF SENTENCE, TWO RECORDS, because one set gating
        # both was silencing an element on its neighbour's behalf.
        # `said_constant` is about a COLUMN -- every element carrying
        # it draws from the same values, so one sentence is enough --
        # and it went on ALSO gating the legend-size note, which has
        # been PER ELEMENT since 2026-08-17 and measures emptiness on
        # the ladder each element actually draws. So two rows on one
        # column with different class counts produced one sentence
        # quoting a ladder the other element does not have, while the
        # other drew twenty classes with fifteen empty and was never
        # mentioned. Measured 2026-08-27; open as row 41 of the
        # 2026-08-17 ledger for nine days, and this is the landing's
        # half of a fix the restyle path was given alone -- diff the
        # two hunks against each other, which is a rule this project
        # already writes down.
        # KEYED ON THE SENTENCE, exactly as the twin is: elements with
        # nothing new to say stay silent, and no element is decided
        # for by another.
        said_constant = set()
        said_notes = set()
        for assignment in assignments:
          field = assignment.get("var")
          if not field or assignment.get("mode") != "Graduated":
            continue
          if field not in gdf.columns:
            continue
          # The COLUMN's own sentences are said once; this row's own
          # sentence is asked for below whatever the column has said.
          column_spoken = field in said_constant
          # THE REGION LAYER, not the tiled frame -- the same source the
          # sibling branch below already documents, and the one this
          # branch quietly did not use. The renderer this sentence
          # describes is seeded from the region's values, so counting
          # the TILES made the sentence disagree with the legend
          # beside it: a small area dropped at a coarse spacing leaves
          # the tiled frame holding one value while the column holds a
          # range. Measured 2026-08-15 by a hunt -- region values
          # [10, 99], one area too small to catch a tile, the bar
          # saying "every area has the same value" while the map drew
          # (10, 54.5) and (54.5, 99). Worse, saying it SUPPRESSED the
          # true notice, because this branch marks the field as
          # already explained.
          #
          # The hunt's own lesson is the one to keep: where a family
          # of sentences documents which frame it counts, the branch
          # that does NOT say is the defect.
          constant_source = self._classification_values(field)
          region_values = (
            constant_source.uniqueValues(
              constant_source.fields().indexOf(field))
            if constant_source is not None else gdf[field])
          if bridge.numeric_values_are_constant(region_values):
            if not column_spoken:
              said_constant.add(field)
              self._report_quietly(bridge.constant_field_message(field))
          else:
            # The same rule at n > 1: the row asked for more classes
            # than the column has values, so the map draws fewer than
            # the spinner shows. Counted from the REGION layer, which
            # is what _assignments reduced against, so the sentence
            # cannot disagree with the map it describes -- and said
            # only where the constant notice did not already say it,
            # since one value is this rule's n == 1 instance and two
            # sentences about one column is one too many.
            retired = self._retire_an_undrawable_pin(field, assignment)
            if retired is not None:
              self._report_quietly(retired)
            note = self._legend_size_note(field, assignment,
                                          assignment.get("id"))
            # SAID FOR THIS ELEMENT, deduped by its own words. The
            # column record is still consulted, because the constant
            # sentence is this rule's n == 1 instance and two
            # sentences about one column is one too many -- but a
            # DIFFERENT sentence from a different element is not the
            # same sentence, and it is now said.
            if note is not None and not column_spoken \
                and note not in said_notes:
              said_notes.add(note)
              self._report_quietly(note)
          # Gaps in the column, counted from the REGION LAYER, because
          # the sentence says "areas" and must mean the user's areas:
          # counting the tiled frame here once produced "31 of 96
          # areas" for a layer of twenty-four, and the reader went
          # looking for areas they do not have. The breaks already
          # exclude the nulls (see bridge.make_graduated_renderer);
          # this is the half the user can read, and what gives them a
          # chance of understanding if QGIS's own Classify button
          # later moves every break by counting nulls as zero.
          index = layer.fields().indexOf(field) \
            if self._source_layer_alive(layer) else -1
          if index < 0:
            continue
          # COUNTED THROUGH THE SAME OWNER as the split, or the
          # sentence describes a different map from the one drawn.
          # Measured 2026-08-16 on 144 areas with two NULLs and four
          # infinities: the bar said "2 of 144" while the map drew
          # nine no-data tiles across seven areas, and on an
          # infinities-only column it said nothing whatever, so grey
          # patches appeared with no explanation.
          if column_spoken:
            continue
          # COUNTED OVER THE AREAS THAT REACHED THE MAP. The sentence
          # this feeds says the areas it counts "draw as no data", and
          # an area with NO GEOMETRY draws nothing whatever -- it
          # never became a tile, and it already has its own sentence
          # in `unmappable_areas_message`. Counting it here made the
          # number true of the table and false of the map: measured
          # 2026-08-27 on 25 areas where one row was both blank of
          # geometry and null in the column, so the bar promised four
          # no-data areas over a map drawing three.
          # THE TOTAL IS STILL THE USER'S OWN AREAS, which is why it
          # is not narrowed with the count: the sentence says "of 25
          # areas", and a reader looking at their own table must find
          # that number there.
          missing = sum(
            1 for feature in layer.getFeatures()
            if bridge.cannot_be_placed(feature[field])
            and not (feature.geometry() is None
                     or feature.geometry().isNull()
                     or feature.geometry().isEmpty()))
          note = bridge.missing_values_message(
            field, missing, int(layer.featureCount()))
          if note is not None:
            said_constant.add(field)
            self._report_quietly(note)
        for assignment in assignments:
          field = assignment.get("var")
          if not field or assignment.get("mode") != "Categorized":
            continue
          if field not in gdf.columns:
            continue
          current = int(gdf[field].nunique(dropna=True))
          shift = bridge.categorical_shift_message(
            field, self._category_counts.get(field), current)
          self._category_counts[field] = current
          if shift is not None:
            self._report_quietly(shift)

    # WHAT OUR GROUP IS CALLED AS THIS RUN STARTS, so the landing can
    # tell a rename that happened DURING the run from one that
    # happened before it. The two look identical to
    # `_get_or_make_group` -- our record holds one name and the tree
    # holds another -- and they mean opposite things:
    #
    #   renamed BEFORE the run: the group is simply called something
    #   else now, and this run replaces it in place like any other;
    #
    #   renamed DURING the run: the user has laid a claim on the
    #   result this run is about to replace, exactly as "Create as new
    #   group" does, so the landing leaves it alone and starts fresh.
    #
    # Read off the TREE rather than off `self._group_name`, which is
    # only refreshed at a landing and would still hold the old name in
    # both cases. Guarded by
    # `test_the_output_group_is_renamed_while_a_run_is_in_flight` on
    # one side and
    # `test_a_renamed_group_is_still_the_group_the_next_run_replaces`
    # on the other; before 2026-08-17 the first passed only because a
    # renamed group could not be found AT ALL, which is what made the
    # second one's defect.
    launching_group = self._group_of_our_layers(
      QgsProject.instance().layerTreeRoot())
    self._group_name_at_launch = (
      launching_group.name() if launching_group is not None else None)
    self._task = TilingTask(
      f"WeavingSpace: tiling with {family}", work, done)

    def on_progress(p):
      self.progress.setValue(int(p))
      if p < 40:
        self.progress.setFormat("laying out the tiling… %p%")
      elif p < 90:
        self.progress.setFormat("joining data to tiles… %p%")
      else:
        self.progress.setFormat("adding layers… %p%")

    self._task.progressChanged.connect(on_progress)
    QgsApplication.taskManager().addTask(self._task)

  # ------------------------------------------------- output layer management

  def _retire_previous_instance(self):
    """Shut down any dialog left over from before this one.

    Called from __init__, so by the time a new dialog finishes
    constructing it is the only live one. The predecessor gets the
    same treatment as closing it by hand: its debounce timers stop,
    a tiling in flight is cancelled, and it hides. Its widgets are
    left intact rather than deleted, because Qt may still deliver
    queued signals to them and a deleted C++ object would take QGIS
    down with it.

    Returns:
      None. The live-dialog record (see _set_live_dialog, which keeps
      it on the QApplication so a plugin RELOAD cannot forget it) is
      left pointing at this dialog. The predecessor is recognised by
      identity, never by isinstance: after a reload it is an instance
      of a different class object with the same name, and an
      isinstance test would quietly decide there was nothing to
      retire.
    """
    previous = _live_dialog()
    if previous is not None and previous is not self:
      try:
        previous._live_timer.stop()
        previous._preview_timer.stop()
        previous.live_check.setChecked(False)
        # ...AND ITS CHILD WINDOWS. The colour editor is WindowModal
        # to the DIALOG, deliberately, so QGIS stays usable -- which
        # also means it outlives its parent's retirement: hidden
        # parent, visible editor, and every pick its closures make
        # runs on the RETIRED dialog, whose restyle path still writes
        # renderers. A pick made there either went nowhere the map is
        # or reverted the live dialog's pending edits. The reachable
        # route into a retired dialog is not its widgets but its
        # surviving children. Found by the two-dialogs hunt,
        # 2026-08-26.
        if getattr(previous, "_open_editor", None) is not None:
          previous._open_editor.reject()
          previous._open_editor = None
        if previous._task is not None:
          previous._task.cancel()
          previous._task = None
        previous.hide()
      except RuntimeError:
        # the Qt object is already gone; nothing to retire
        pass
    _set_live_dialog(self)

  def _on_project_read(self):
    """Take over the project QGIS has just opened.

    Returns:
      None. Adopts the incoming project's output group, then brings
      the chooser and its exclusions into line with it, which is what
      the constructor does in the same order.

    GUARDED LIKE ITS SIBLINGS, and it was not at first. A connection
    made on the QgsProject SINGLETON outlives the dialog that made it,
    so every dialog ever built in a session would answer every project
    opened afterwards -- and reaching a destroyed dialog through a
    live connection is what took QGIS down once already here. The two
    checks are the ones `_on_layer_style_edited` carries: has this
    dialog been destroyed, and is it still the live one.

    AND IT DOES WHAT THE CONSTRUCTOR DOES. The first version adopted
    the group and stopped, while the constructor goes on to refresh
    the layer exclusions and the chooser -- so after a File > Open the
    chooser could sit on the plugin's OWN output, and Generate then
    failed with a KeyError about a column the user never chose. The
    comment claiming a surviving dialog "ends up in exactly the state
    a freshly opened one would be in" was therefore false when
    written; it is true now because the same three calls run.
    """
    if _dialog_is_gone(self) or _live_dialog() is not self:
      return
    self._adopt_existing_group()
    # ...and show what it recovered. Here the widget DOES exist -- the
    # dialog was already open when the project arrived -- but the
    # constructor's path needs the same call after `_build_ui`, so it
    # lives in one method rather than two copies that could drift.
    self._show_the_adopted_path()
    self._update_layer_exclusions()
    self._on_layer_changed()
    # ...and the design too, in the same order the constructor uses.
    # A project opened under a live dialog is the other door into the
    # loss `_restore_the_adopted_design` describes.
    self._restore_the_adopted_design()

  def _adopt_existing_group(self, group=None):
    """Take over an output group this project already holds.

    Args:
      group: the group to adopt, or None to take the one a reopened
        project should get -- `_newest_output_group`'s answer, which
        prefers a group made from the chosen dataset and falls back to
        recency. The argument exists so the output-group CHOOSER can
        reach this same door: a group somebody picked and a group a
        reopened project offers need the identical work done to them,
        and writing that twice is how the two would come to disagree.

    Group tracking lives on the dialog instance, so without this a
    dialog opened later in a QGIS session (the plugin closed and
    reopened, which users do constantly) would find its default group
    name taken and quietly start "WeavingSpace tiles 2", leaving the
    first group behind with stale layers. That contradicts the
    settled design, where Generate replaces the previous result in
    place and "Create as new group" is the only route to a second
    one. Output layers carry their element id in a custom property,
    so adoption is exact rather than name-guessing.

    ``_last_signatures`` is deliberately left empty: the dialog cannot
    know which assignments produced the adopted layers, so the next
    run re-seeds their symbology rather than preserving hand styling
    it cannot vouch for. Within a session, hand styling still
    survives as before.
    """
    root = QgsProject.instance().layerTreeRoot()
    if group is None:
      group = self._newest_output_group(root)
    if group is None:
      # THE MARKER DROPS ON THIS PATH TOO. The clear at the bottom of
      # this method says "cleared unconditionally, including on the
      # paths that adopt nothing" -- and this return was exactly such
      # a path, reached whenever the opened project holds no plugin
      # group at all. The flag then stood for the rest of the
      # session: `_swap_dataset_memory` stayed inert, the dataset
      # identity never bound, and one dataset's value-keyed
      # hand-picks stayed live under the next -- ruling 8's leak,
      # resurrected through an ordinary File > Open of a plain
      # project. Found by the doors hunt of 2026-08-26 (round nine).
      self._project_is_being_replaced = False
      return
    # Taken over rather than written by us, so the first Generate
    # REPLACES it whatever the output box says. Read and cleared in
    # `_add_output_layers`; set here rather than at the call sites
    # because this is the one place that establishes the fact.
    self._adopted_group_unwritten = True
    # WHICH GROUP WAS ADOPTED, so the DESIGN can be restored once the
    # widgets exist. This method runs before `_build_ui` in the
    # constructor, so it cannot apply a record itself; it remembers
    # the node and `_restore_the_adopted_design` does the rest. See
    # that method for what went wrong without it.
    self._adopted_group = group
    project = QgsProject.instance()
    self._no_data_layer_ids = dict(
      self._no_data_layer_ids)
    # Elements claimed by more than one layer in this group, collected
    # as they are met and reported once at the end; see the note where
    # they are found.
    twice = set()
    for child in group.children():
      layer = child.layer() if hasattr(child, "layer") else None
      if layer is None or project.mapLayer(layer.id()) is None:
        continue
      tid = layer.customProperty("weavingspace_tile_id")
      # A PAIRED NO-DATA LAYER CARRIES ITS ELEMENT'S TILE ID, because
      # it belongs to that element -- and this loop keyed adoption on
      # that id alone, so the paired layer OVERWROTE its own element
      # in `_element_layer_ids`. What followed was the worst outcome
      # this dialog can produce: the next Generate removed exactly
      # what `old_ids` named, which was the no-data layer, and left
      # the real element layer orphaned in the project. Yesterday's
      # map -- old tiling, old variable -- stayed on top of the new
      # one and was never updated again. Measured 2026-08-16 by a
      # hunt working backwards from harm: element 'a' drawn as
      # 'a - v1' with 938 features at spacing 400, over a live map of
      # 'a - v2' with 313 at 700.
      #
      # The general shape, worth more than the fix: a PAIRED artefact
      # inherits the identity property of the thing it is paired
      # with, so every lookup keyed on that property silently gains a
      # second answer. When you add one, grep the property rather
      # than the feature.
      # AND A SECOND CLAIMANT IS NOT SILENTLY PREFERRED. QGIS's own
      # Duplicate Layer copies custom properties, so a copy of an
      # output layer carries its element's id and this loop, taking
      # the LAST claimant in panel order, adopted whichever happened
      # to sit lower. The next Generate then removed the one it had
      # adopted and left the OTHER standing: last run's tiling,
      # permanently on top of the new map, under an identical name,
      # never updated again. That is the same catastrophe the paired
      # layer produced on 2026-08-16, through the door that fix did
      # not close -- its own comment says every lookup keyed on the
      # property gains a second answer, and it counted the plugin's
      # twin without counting the user's copy.
      # THE FIRST IN PANEL ORDER WINS, and nothing is deleted on a
      # guess: the two layers are indistinguishable (the properties
      # were copied, and a GeoPackage-backed copy shares even its
      # source), so removing the extra would be destroying something
      # somebody may have made on purpose -- keeping a copy of
      # yesterday's map is a reasonable thing to do. What the plugin
      # owes is to SAY so, since the one left behind will sit over
      # the new map otherwise.
      if tid and layer.customProperty("weavingspace_no_data"):
        if str(tid) in self._no_data_layer_ids:
          twice.add(str(tid))
        else:
          self._no_data_layer_ids[str(tid)] = layer.id()
      elif tid:
        if str(tid) in self._element_layer_ids:
          twice.add(str(tid))
        else:
          self._element_layer_ids[str(tid)] = layer.id()
        # a project saved with hand-picked colours brings them back
        self._adopt_category_colours(layer, str(tid))
        # THE LADDER IN FRONT OF US IS THE BASELINE, and this is the
        # third and last place the plugin may say it knows one. It
        # did not paint this layer -- it has only just met it -- but
        # "what we last understood the ladder to be" is exactly what
        # the record means, and on a reopen that is whatever the
        # project came back holding.
        #
        # WITHOUT THIS LINE EVERY REOPENED PROJECT WOULD READ AS
        # UNATTRIBUTABLE, and the colour judgement declines what it
        # cannot attribute -- so no dock recolour would ever be taken
        # up again after a reopen, which is the commonest journey
        # there is. That is the shape recorded two lines above about
        # `_last_signatures`, which is left empty on purpose here and
        # was read as evidence of change by a guard written the day
        # before (ledger row 1 of 2026-08-20). The difference is that
        # this record CAN be filled honestly from the layer, where a
        # signature cannot: the dialog still does not know which
        # assignment produced this ladder, but it does not need to.
        self._remember_painted_ladder(layer, str(tid))
        # adopted layers are watched like freshly made ones, so a
        # styling-dock edit reaches the dialog here too
        self._watch_element_layer(layer, str(tid))
      if tid or layer.customProperty("weavingspace_no_data"):
        # WHICH GEOPACKAGE TABLES ARE OURS, remembered across
        # sessions. `_gpkg_tables_written` lives on the dialog, so a
        # reopened plugin knew nothing about what yesterday's session
        # wrote and the stale-table drop had nothing to drop: a
        # design that shrank left its old elements in the file
        # forever, and the file is the thing a user sends on.
        #
        # Seeded from the ADOPTED LAYERS rather than by listing the
        # file, and that is the whole safety of it. A table is
        # treated as ours only when a layer in our own output group,
        # carrying our own custom property, is reading from it --
        # which is evidence, not a guess about a name. Listing
        # `tiles_*` in the file would have been easier and would risk
        # dropping a table a user happened to name that way, and
        # destroying data the plugin did not create is the one thing
        # it must never do.
        self._remember_our_table(layer)
      elif layer.customProperty("weavingspace_outline"):
        self._outline_layer_id = layer.id()
    if twice:
      # SAID ONCE, NAMING THE ELEMENTS, and never as a modal: this
      # runs at construction, before the user has done anything, and
      # a box in front of a dialog that is still opening is not a
      # message anybody asked for.
      self._report_quietly(
        f"More than one layer here says it is element "
        f"{', '.join(sorted(twice))} of this map, which usually means "
        f"a layer was duplicated. The plugin will replace the upper "
        f"one; move or remove the other, or its tiles will stay on "
        f"top of the new map.")
    if self._element_layer_ids or self._outline_layer_id:
      self._group_name = group.name()
    # THE MARKER IS DROPPED HERE AND ONLY HERE. Everything between the
    # `cleared` signal and this line belongs to the project being
    # replaced; from here on, a value in these records is a choice
    # somebody made in the project now open. Cleared unconditionally,
    # including on the paths that adopt nothing, or a File > New with
    # no output group to adopt would leave it standing and let a later
    # adoption overwrite a live choice.
    self._project_is_being_replaced = False

  def _remember_our_table(self, layer):
    """Record that this layer is reading a table this plugin wrote.

    Args:
      layer: an adopted output layer, element or no-data alike.

    Returns:
      None. Does nothing for a memory layer, which has no file behind
      it, or for a source this cannot parse -- in which case the
      table is simply not claimed, and the stale-table drop leaves it
      alone. Not claiming is always the safe direction: an unclaimed
      table survives, and only a claimed one can ever be removed.

    A GeoPackage layer's source reads `<path>|layername=<table>`, and
    both halves are needed: the record is keyed by file, since one
    dialog can write several over a session.
    """
    try:
      source = layer.source()
    except Exception:
      return
    if not source or "layername=" not in source:
      return
    path, _, rest = source.partition("|")
    table = rest.split("layername=", 1)[1].split("|", 1)[0]
    if not path or not table or not path.lower().endswith(".gpkg"):
      return
    self._gpkg_tables_written.setdefault(
      self._gpkg_key(path), set()).add(table)
    # ...AND THE PATH ITSELF, which adoption needs quite as much as
    # the group: it is what the file's own record is rewritten
    # through, and what puts the adopted file back in the chooser when
    # a project is reopened.
    # THE REASON IT WAS FIRST RECORDED HAS SINCE BEEN DELETED, and
    # saying so is cheaper than leaving a reader to infer it. Until
    # 2026-08-27 the landing armed a fresh group whenever this path
    # differed from the chooser's, so a dialog that had just adopted
    # the incoming project's group compared against None, decided the
    # destination had changed, and built a SECOND group beside the one
    # it had adopted -- two groups, four adopted layers orphaned, both
    # reading the SAME tables, measured by a hunt on 2026-08-16. That
    # inference is gone under the ruling that an output path never
    # decides which group a run lands on; the recording stays, for the
    # two reasons above.
    #
    # Taken from the layer rather than from the file widget, so it
    # describes where the output actually IS rather than where the
    # dialog would put it next.
    self._last_path = path

  def _our_groups(self, root):
    """Every output group in the project, newest first.

    Args:
      root: the project's layer tree root.

    Returns:
      A list of (group node, handle, region source). The HANDLE is the
      layer id of the first output layer in that group, and it is what
      the chooser stores.

    ASKED OF THE LAYERS, NEVER OF A NAME, which is this project's
    settled rule and the reason `_newest_output_group` and
    `_group_of_our_layers` were both rewritten in 2026-08-17: a group
    is OURS when it holds a layer carrying our own custom property.
    Renaming a group in the layers panel is an ordinary thing to do,
    and a chooser keyed on the name would lose the group the moment
    somebody did it. The name is still what is DISPLAYED -- a label is
    exactly what you show a person, and never what you look them up by.

    A LAYER ID IS THE HANDLE for the same reason. A group node has no
    identity of its own that survives a Qt wrapper being rebuilt, and
    a list rebuilt from the tree on every use cannot hold a stale one.

    NEWEST FIRST, read off `root.children()`, which is ordered and is
    how these groups are made: `_get_or_make_group` inserts at 0, so
    each new group pushes the last one down. NOT recursive, so a group
    somebody has nested inside a folder of their own is left alone --
    the same choice, for the same reason, as `_newest_output_group`.

    MAINTAINER'S RULING, 2026-08-26: NON-RECURSIVE IS FINE, and it is
    recorded here with what it costs rather than only what it buys,
    because a hunt raised it that day and the next one should not have
    to. Nesting an output group inside a folder takes it out of every
    reader that walks `root.children()`: the chooser stops listing it,
    the one-file-is-one-map check in `_resume_from_gpkg` cannot see
    it, so resuming that file builds a SECOND copy of the map beside
    it, and a later run on the new copy drops tables the nested one is
    still drawing from -- measured that day, `tiles_a_v1` removed from
    the file while the tidied group went on pointing at it. "Left
    alone" therefore means unmanaged rather than protected, which is
    the honest reading and the one the ruling accepts.
    """
    found = []
    for node in root.children():
      if not hasattr(node, "children"):
        continue
      ours = [child.layer() for child in node.children()
              if getattr(child, "layer", lambda: None)() is not None
              and (child.layer().customProperty("weavingspace_tile_id")
                   or child.layer().customProperty("weavingspace_outline"))]
      if not ours:
        continue
      stamps = [layer.customProperty("weavingspace_region")
                for layer in ours
                if layer.customProperty("weavingspace_region")]
      found.append((node, ours[0].id(), stamps[0] if stamps else None))
    return found

  def _dataset_label(self, source):
    """A readable name for the dataset a group was made from.

    Args:
      source: a layer source string, as stamped on every output layer,
        or None for output made before the stamp existed.

    Returns:
      A short label for the chooser. The project's own layer NAME
      where a layer with that source is still loaded, since that is
      what the user sees everywhere else; otherwise the file's base
      name, which at least says which file; otherwise None.

    The colleague's request was a dropdown "selecting output group
    with dataset as attribute", and this is that attribute. It is
    deliberately cosmetic: nothing is ever looked up by it.
    """
    if not source:
      return None
    for layer in QgsProject.instance().mapLayers().values():
      # THE SAME DOOR AS `_recover_the_source`, and it was open here
      # too. The map-unit outlines layer is built on the REGION'S OWN
      # SOURCE, so a walk that matches by source and takes the first
      # answer can name a group after the plugin's own output rather
      # than after the user's data -- and the chooser would then
      # label a map with a name nobody outside this code recognises.
      # Cosmetic where its twin cost a resume, and closed for the
      # reason this project already writes down twice: a guard that
      # is missing and currently costs nothing is a countdown rather
      # than a defence. (Found by the design-controls hunt alongside
      # its twin, 2026-08-27.)
      if layer.customProperty("weavingspace_output"):
        continue
      try:
        if same_source(layer.source(), source):
          return layer.name()
      except Exception:
        continue
    stem = source.split("|", 1)[0]
    base = os.path.basename(stem)
    return base or None

  def _point_the_chooser_at(self, source):
    """Select the region layer a saved record names, where we can.

    Args:
      source: the record's "region" -- a layer source string, or None
        or empty where the record does not name one, in which case
        nothing happens.

    Returns:
      None. The chooser is left where it was unless a layer this
      dialog is ALLOWED to select answers to that source.

    THREE COPIES OF THIS WALK EXISTED and the guards had reached one.
    `_recover_the_source` carries both of them and says why; the group
    chooser and the adopted-design restore carried neither, and a hunt
    found it on 2026-08-28 by asking what else answers to a region's
    source string.

    OUR OWN OUTPUT ANSWERS TO IT. The map-unit outlines layer is built
    on the REGION'S OWN SOURCE -- deliberately, since nothing is
    copied -- and carries `weavingspace_output`, which is what keeps it
    out of the region chooser. Each fact is right alone. Together they
    made this walk hand `setLayer` a layer the combo EXCLUDES, so the
    chooser came up EMPTY: with "Add map unit outlines layer" ticked,
    picking your own map's group lost the region and every element's
    variable fell to nothing. Measured 2026-08-28 with a control arm --
    outlines off, the same journey is clean -- on file-backed data,
    which is the only kind that can show it, since the collision is two
    layers sharing a source string and a memory layer's URI is not one
    anything else is built on.
    AND THE WALK SKIPPED "THE LAYER ALREADY IN FORCE", which turns an
    order-dependent fault into a certainty: with the region itself
    skipped, the outlines layer was the only match left.

    SO IT CHECKS THAT THE ASSIGNMENT TOOK, rather than assuming it.
    `setLayer` on an excluded layer is silent, and a walk that breaks
    on a set that did not happen leaves the chooser empty and reports
    nothing -- which is the fault this method exists to end.
    """
    if not source:
      return
    for layer in QgsProject.instance().mapLayers().values():
      # Never our own output. It answers to the region's source and is
      # not a region.
      try:
        if layer.customProperty("weavingspace_output"):
          continue
        same = same_source(layer.source(), source)
      except Exception:
        continue
      if not same or layer is self.layer_combo.currentLayer():
        continue
      self.layer_combo.setLayer(layer)
      if self.layer_combo.currentLayer() is layer:
        return
      # It did not take -- the combo refuses layers it excludes -- so
      # keep looking rather than breaking on a set that never happened.
    return

  def _refresh_group_combo(self):
    """Rebuild the output-group chooser from the project as it stands.

    Returns:
      None. Lists every output group newest first, with a "create new"
      entry at the end, and selects whichever group this dialog is
      working on.

    SIGNALS ARE BLOCKED THROUGHOUT, as `_sync_pin_controls` already
    does: putting the dialog's own truth into a chooser is not
    somebody choosing, and letting it read as one would fire the
    handler that restores a whole working state -- over the very
    session that was being described.

    Rebuilt rather than patched, on every occasion the set of groups
    can have moved: a run landing, a group adopted, a project read, a
    layer removed. A list maintained incrementally would need a rule
    for each of those, and this one has no state to go stale.
    """
    combo = getattr(self, "group_combo", None)
    if combo is None:
      return
    root = QgsProject.instance().layerTreeRoot()
    mine = self._group_of_our_layers(root)
    blocked = combo.signalsBlocked()
    combo.blockSignals(True)
    try:
      combo.clear()
      chosen = -1
      for group, handle, source in self._our_groups(root):
        dataset = self._dataset_label(source)
        # ...AND NEVER TWICE. Since 2026-08-26 a group is NAMED for
        # its dataset, so appending the dataset unconditionally read
        # "WeavingSpace tiles — nyc — nyc". The dataset is still
        # appended where the name does not already carry it, which is
        # a group somebody has renamed and output made before this
        # ruling -- for those the chooser is the only place the
        # dataset appears at all.
        label = group.name() if not dataset or dataset in group.name() \
            else f"{group.name()} — {dataset}"
        combo.addItem(label, handle)
        if mine is not None and group.name() == mine.name() \
            and chosen < 0 and handle in {
              child.layer().id() for child in mine.children()
              if getattr(child, "layer", lambda: None)() is not None}:
          chosen = combo.count() - 1
      combo.addItem(NEW_GROUP_LABEL, None)
      # ...AND "CREATE NEW" WINS WHERE IT IS ARMED, because the
      # chooser's promise is where the NEXT RUN lands, not which
      # group the dialog is restyling. Without this a rebuild put the
      # present group's name back while the run still built a new one,
      # so the control ruling 1 added to make the rule visible was
      # itself saying something untrue.
      if self._new_group_chosen:
        chosen = combo.count() - 1
      # "Create new" is the honest answer when this dialog is not
      # working on any of the groups listed -- a fresh session, or one
      # whose group the user has just deleted.
      combo.setCurrentIndex(chosen if chosen >= 0 else combo.count() - 1)
    finally:
      combo.blockSignals(blocked)

  def _group_for_handle(self, handle):
    """The group node a chooser entry names, or None.

    Args:
      handle: a layer id stored against a chooser entry.

    Returns:
      The layer-tree group holding that layer, or None where the layer
      has since been removed or dragged to the top level. Asked of the
      tree every time rather than remembered, so a stale answer is not
      possible.
    """
    if not handle:
      return None
    root = QgsProject.instance().layerTreeRoot()
    node = root.findLayer(handle)
    parent = node.parent() if node is not None else None
    # The tree ROOT has no parent of its own, which is how a group
    # under the root is told from the root itself; identity against
    # `root` is unreliable, since PyQt hands back a fresh wrapper
    # around the same C++ object.
    if parent is not None and parent.parent() is not None:
      return parent
    return None

  def _on_group_chosen(self, _index=0):
    """Work on the output group the user just picked.

    Args:
      _index: the chooser's index, which Qt sends and this ignores --
        the entry's DATA is the handle, and reading the index would
        break the moment the list is rebuilt in a different order.

    Returns:
      None. "Create new" arms the next run to build a group of its
      own; any other entry selects that group's dataset, takes the
      group over, and restores the working state it carries.

    THE ORDER IS FORCED. The dataset goes first, because the per-
    dataset memory banks swap on it and because the assignment table
    cannot restore a variable to a column the current layer does not
    have. The group is taken over next, so the dialog's records point
    at the layers being resumed rather than at the ones being left.
    Only then is the record applied, over a table built from the right
    fields.

    `_selecting_a_group` IS WHAT STOPS THIS BEING READ AS A CHANGE OF
    DATASET. Choosing a group is resuming work, not starting it: the
    protections `_begin_new_dataset` arms -- clearing the output path,
    demanding a fresh group, asking the design-floor question -- exist
    so that B's map never lands on A's result, and under the binding
    that is answered by WHICH GROUP IS SELECTED. Running them here
    would clear the very output path the record is about to restore.
    """
    if _dialog_is_gone(self) or _live_dialog() is not self:
      return
    # NOT WHILE A RUN IS IN FLIGHT. Choosing a group repoints the
    # records the landing is about to read -- `_stamp_working_state`
    # re-reads the elements live off the swapped table -- so a choice
    # made mid-tiling landed the run in a fresh rival group whose
    # saved record described ANOTHER map's design, and resuming that
    # group later silently redrew it with a variable nobody chose for
    # it. `_bind_group_to_dataset` has carried this same guard since
    # 2026-08-25; this door never got it (found by the mid-run hunt,
    # 2026-08-26 -- a guard added to one door belongs at every door).
    # The choice is REFUSED in words rather than queued, because a
    # queued choice would land against whatever the run leaves, which
    # is a design nobody has seen yet; the chooser is re-synced so it
    # goes on telling the truth.
    if self._task is not None:
      self._report_quietly(
        "A map is still being generated; choose the group to work on "
        "once it finishes.")
      self._refresh_group_combo()
      return
    combo = getattr(self, "group_combo", None)
    if combo is None:
      return
    handle = combo.currentData()
    if handle is None:
      # CREATE NEW: nothing moves now. The next run builds its own
      # group, and the chooser re-populates around it at the landing.
      self._new_group_chosen = True
      return
    group = self._group_for_handle(handle)
    if group is None:
      # The group has gone since the list was built. Rebuild rather
      # than guess: a chooser offering something that is not there is
      # worse than one that has just corrected itself.
      self._refresh_group_combo()
      return
    self._new_group_chosen = False
    record = self._read_working_state(group)
    self._selecting_a_group = True
    try:
      self._point_the_chooser_at((record or {}).get("region"))
      self._take_over_group(group)
      if record:
        self._apply_working_state(record)
      else:
        # A group made before this version, or one whose record could
        # not be read. Taking it over is still the right answer -- the
        # next Generate replaces THIS map rather than somebody else's
        # -- and the design simply stays where it is.
        self._rebuild_unit()
    finally:
      self._selecting_a_group = False
    self._refresh_group_combo()

  def _restore_the_adopted_design(self):
    """Put back the design of the group adoption has just taken over.

    Returns:
      None. When adoption found a group and that group carries a
      working state, the dialog is brought to it -- the region layer
      the map was made from, then every design control and every
      element's row -- exactly as choosing that group in the chooser
      does.

    WHY THIS EXISTS, measured 2026-08-26 and shipping since 2026-08-25
    (rc16, rc18, rc19). `_adopt_existing_group` took over a group's
    LAYERS and never read its RECORD, while `_on_group_chosen` read it
    and applied it three lines apart. So closing the plugin and
    opening it again -- which that method's own docstring calls
    something "users do constantly" -- brought back a table on the
    plugin's DEFAULT cycle over layers still drawing the map somebody
    had made: every hand-chosen variable, style, ramp and class count
    gone from the row while the map and the GeoPackage still held
    them. The next Generate then wrote the row's wrong answer onto the
    map, turning a categorical land-cover element into a quantitative
    one. Against ruling 4 of 2026-08-25, whose whole point is that
    selecting a group restores the working state "so nothing is
    inferred".
    A GUARD -- OR A RESTORE -- ADDED TO ONE DOOR BELONGS AT EVERY DOOR
    INTO THE SAME ROOM, which this file already records as the
    sharpest thing the group-unit build taught.

    THE ORDER IS THE WHOLE OF IT, and it is the lesson of the same
    week: the region layer is recovered BEFORE the record is applied,
    because a variable cannot be restored to a column the region in
    force does not have. Putting the recovery after the restore is
    what turned visibly wrong into invisibly wrong on 2026-08-26.

    CALLED FROM TWO PLACES AND NOT FROM `_adopt_existing_group`
    ITSELF. Adoption runs before `_build_ui` in the constructor, so
    there are no widgets to restore into; and `_take_over_group` calls
    adoption on the chooser's own path, where `_on_group_chosen`
    applies the record itself and a second application here would be
    redundant work on every group pick.
    """
    group = getattr(self, "_adopted_group", None)
    if group is None:
      return
    record = self._read_working_state(group)
    if not record:
      # A group made before this version, or one whose record could
      # not be read. Adoption alone is still right: the next Generate
      # replaces THIS map rather than somebody else's, and the design
      # simply stays where it is.
      return
    self._selecting_a_group = True
    try:
      self._point_the_chooser_at(record.get("region"))
      self._apply_working_state(record, keep_adopted=True)
    finally:
      self._selecting_a_group = False
    self._refresh_group_combo()

  def _a_group_was_renamed(self, *_args):
    """Keep the output-group chooser's labels true after a rename.

    Args:
      *_args: whatever QGIS sends with `nameChanged` -- the node and
        the new name -- both ignored. The chooser is rebuilt from the
        tree rather than patched, so which node moved does not matter,
        and reading the arguments would tie this to a signature QGIS
        is free to change.

    Returns:
      None. Rebuilds the chooser, and follows the rename in the
      dialog's own record of the group's name so the two agree.

    A NAME IS A LABEL, WHICH IS EXACTLY WHY THIS IS NEEDED. Nothing is
    looked UP by the name -- the chooser keys on a layer id and the
    group is found by asking the layers -- but the label is what the
    user reads, and ruling 1 rests on the chooser naming the map a run
    will land in. After a rename it named one that no longer existed.

    GUARDED LIKE ITS SIBLINGS. This connects to the layer TREE, which
    outlives the dialog: without the gate every dialog ever opened in
    a session would rebuild its chooser on every rename anywhere,
    which is the quadratic shape measured on 2026-08-16.
    """
    if _dialog_is_gone(self) or _live_dialog() is not self:
      return
    ours = self._group_of_our_layers(QgsProject.instance().layerTreeRoot())
    if ours is not None:
      # FOLLOW THE RENAME rather than undoing it, which is the rule
      # `_get_or_make_group` already keeps: the user's name wins.
      self._group_name = ours.name()
    self._refresh_group_combo()

  def _bind_group_to_dataset(self) -> bool:
    """Select the chosen dataset's own output group, and restore it.

    Returns:
      True when a group belonging to this dataset was found, taken
      over and its working state applied; False when the dataset has
      no group here, in which case the next run is armed to build one.

    THE OTHER HALF OF THE SYMMETRIC BINDING (ruling 2 of 2026-08-25).
    Choosing a group selects its dataset; choosing a dataset selects
    its group. Neither direction is the "real" one, which is what
    makes the pair predictable: whichever control the user touches,
    both end up describing one map.

    RECENCY IS THE TIE-BREAK where a dataset owns several groups
    (ruling 3), and it is READ off the project's own layer order
    rather than remembered. `_our_groups` returns newest first because
    `_get_or_make_group` inserts at 0, so the first match is the most
    recent. A fact about the project beats a guess about intent, and
    it survives a reopen where a session record would not -- which
    matters, because A-B-A has left one dataset owning two groups
    since ruling 2 made a second group the ordinary result of a demo.

    NO GROUP MEANS "CREATE NEW", and that is what retires
    `_fresh_group_for_new_data`. The old flag existed so the first
    Generate after a change of dataset could not land on the previous
    dataset's map. Here that cannot happen for a better reason: the
    run lands in the group the chooser NAMES, and a dataset with no
    group of its own names none.
    """
    # NOT WHILE A RUN IS IN FLIGHT, and this is the project's own rule
    # rather than a special case: anything that reads state off the
    # layer tree and RECORDS it must run at REST, because during a run
    # the record and the tree are transiently out of step and what
    # sits there is nobody's decision.
    #
    # MEASURED THE DAY THIS WAS WRITTEN, by a test that had guarded the
    # ground for weeks. Renaming the output group while a tiling runs
    # is how a user keeps that result, and the landing spots it by
    # comparing the group's name against the one it holds -- so taking
    # the group over mid-run, which FOLLOWS the rename, erased the
    # evidence the landing was about to read, and the next run took
    # the keepsake apart. The route is ordinary rather than exotic:
    # QgsMapLayerComboBox re-emits `layerChanged` whenever the
    # project's layers churn, which a run does twice.
    if self._task is not None:
      self._refresh_group_combo()
      return False
    layer = self.layer_combo.currentLayer()
    # AN EMPTY CHOOSER IS NOT A DATASET, which this dialog already
    # settled once for the memory banks and had to learn again here.
    # Removing the region layer empties the combo, and treating that
    # as "this dataset has no group" made the dialog let go of the map
    # it had already made -- while the layers sat in the project,
    # unclaimed, so the next Generate built a rival beside them. The
    # output is the user's map, not a view of the input.
    if layer is None:
      self._refresh_group_combo()
      return False
    source = layer.source()
    root = QgsProject.instance().layerTreeRoot()
    groups = self._our_groups(root)
    # `same_source` RATHER THAN `==`, and this was the twelfth reader
    # of a region stamp and the only one still comparing strings.
    # A source is a path plus `|layername=`, and one directory has
    # more than one absolute spelling -- `/var` against
    # `/private/var` on any Mac, a short name on Windows, a symlinked
    # sync folder anywhere -- so a project saved under one spelling
    # and reopened under another stopped recognising its own dataset's
    # output group. Measured 2026-08-28 by the cross-platform hunt: on
    # the respelt leg the chooser falls to "Create new" and the next
    # Generate builds a second group of the same dataset's tiles
    # beside the first, which is then never updated again. Shipped in
    # v0.24.3 at 18df97d, and missed by the sweep of 2026-08-26 for
    # the eighth site's own reason -- a stamp against a LIVE LAYER'S
    # source is a different pair of operands from a stamp against a
    # stamp, so a search for the phrasing found nothing.
    theirs = [entry for entry in groups
              if source and entry[2] and same_source(entry[2], source)]
    if not theirs and groups and not any(entry[2] for entry in groups):
      # OUTPUT FROM BEFORE THE REGION STAMP SAYS NOTHING about which
      # dataset it came from, and refusing to bind to it would leave
      # every project made by an older version permanently on "create
      # new" -- so the next Generate would pile a second group beside
      # the user's map instead of replacing it. `_newest_output_group`
      # makes the same allowance for the same reason, and the
      # condition is deliberately narrow: the fallback is taken only
      # when NO group in the project carries a stamp, never when one
      # simply belongs to another dataset.
      theirs = groups
    if not theirs and not self._landed_this_session:
      # NOTHING HAS BEEN BUILT IN THIS SESSION, so ADOPTION'S ANSWER
      # STANDS and the binding has nothing better to offer. This is
      # the clause `switched_from_work` already draws for the same
      # reason, arriving at a different control: a reopened session
      # has not landed anything, so there is nothing to protect and
      # no basis for overruling what adoption found.
      #
      # MEASURED, AND THE MEASUREMENT IS THE WHOLE REASON: a MEMORY
      # layer's `source()` carries a uid that changes when the project
      # is reopened, so a map made from one comes back stamped with a
      # string that matches nothing. Six reopen journeys went red at
      # once, the dialog letting go of the group it had just adopted
      # and the next Generate building a rival beside the user's map.
      # `weavingspace_region` was introduced because a source survives
      # a reopen where a layer id does not -- true of a FILE, and not
      # of memory. `_newest_output_group` makes the same allowance
      # from the other side, for the output that predates the stamp.
      self._refresh_group_combo()
      return False
    if not theirs:
      # NOT WORKING ON ANY GROUP, and the dialog must say so rather
      # than go on displaying the last one. Leaving it attached would
      # make the chooser name a map this dataset's run will not land
      # in, which is precisely the invisible rule ruling 1 replaces --
      # and the records it keeps are the ones a run READS to decide
      # what to remove.
      # AND NOTHING IS ARMED HERE, which is a distinction the first
      # build of this got wrong. `_new_group_chosen` means THE USER
      # ASKED FOR A NEW GROUP -- a deliberate act, and the reason the
      # file-overwrite warning fires -- while "this dataset has no
      # group in this project" is not an act at all. Setting one flag
      # for both put the warning in front of an ordinary journey:
      # reopen a GeoPackage's layers loose in a project, point the
      # plugin at the same file, and it refused the run saying "you
      # asked to keep the previous result as its own group", which
      # nobody had. One set gating two different things is a fault
      # this project has paid for before.
      #
      # The detach is enough on its own: with no group claimed,
      # `_get_or_make_group` finds none to reuse and makes one, and
      # the chooser shows "create new" because that is what having no
      # group looks like.
      self._detach_from_the_group()
      self._refresh_group_combo()
      return False
    group = theirs[0][0]          # newest first, so this is ruling 3
    # ALREADY WORKING ON IT MEANS DO NOTHING, and this is the clause
    # that keeps the binding from undoing the user's own work.
    # QgsMapLayerComboBox re-emits `layerChanged` whenever the
    # project's layers churn -- which a run does twice -- so without
    # it every landing was followed by the group's own record being
    # applied back over the dialog, wiping whatever had been changed
    # since. Measured 2026-08-25: a test swapped two elements'
    # variables, generated, and the swap was gone by the time the
    # renderers were read, one element left drawing a single symbol.
    #
    # ASKED OF THE LAYERS, like everything else here: a group is the
    # one we are on when it holds a layer this dialog claims.
    # ASKED OF ALL THIS DATASET'S GROUPS, not only the newest one.
    # Recency is a TIE-BREAK for choosing where nothing is chosen
    # (ruling 3); it is not a rule that overrules a group the user
    # picked, and ruling 1's whole gain is that the choice is on
    # screen and CAN be overruled. Asked of `group` alone, this clause
    # protected the newest group and nothing else -- so deliberately
    # choosing an older one lasted until the next churn of project
    # layers, which a run causes twice. Measured 2026-08-26: the user
    # chose the older group, a layer was added and removed, and the
    # dialog was on the newer one with its records repointed.
    mine = set(self._element_layer_ids.values())
    on_it = {child.layer().id()
             for entry in theirs
             for child in entry[0].children()
             if getattr(child, "layer", lambda: None)() is not None}
    if on_it & mine:
      # AND IT REALLY DOES NOTHING, the arming included. Clearing
      # `_new_group_chosen` here silently revoked "create new": the
      # user asks for a map of its own, the combo re-emits on the
      # next churn of project layers -- which a run causes twice --
      # and the arming is gone, so Generate overwrites the map they
      # asked to keep. Found by a hunt the hour this branch was
      # written; the branch's own comment says it is here to keep the
      # binding from undoing the user's work, and it was undoing one.
      self._refresh_group_combo()
      return False
    self._new_group_chosen = False
    record = self._read_working_state(group)
    self._take_over_group(group)
    if record:
      self._apply_working_state(record)
    self._refresh_group_combo()
    return bool(record)

  def _detach_from_the_group(self):
    """Stop working on whatever output group this dialog last held.

    Returns:
      None. Empties the records that say which layers are ours, so
      `_group_of_our_layers` answers None and the chooser falls back
      to "create new".

    IT REMOVES NOTHING FROM THE PROJECT. The group and its layers stay
    exactly where they are; what changes is that this dialog no longer
    claims them. That distinction is the whole of it -- these records
    are what a landing reads as `old_ids` to decide what to REPLACE,
    so a dialog still holding another dataset's layers while pointed
    at new data is one Generate away from deleting somebody's map.

    Shares its body with `_take_over_group`, which clears the same
    records before adopting different ones: one list, so the two
    cannot come to disagree about what "ours" consists of.
    """
    self._element_layer_ids = {}
    self._no_data_layer_ids = {}
    self._outline_layer_id = None
    self._last_signatures = {}
    self._group_name = None

  def _take_over_group(self, group):
    """Make an existing output group the one this dialog works on.

    Args:
      group: the layer-tree group to adopt.

    Returns:
      None. Clears the records that point at the group being LEFT,
      then adopts this one through the same door a reopened project
      uses.

    THE CLEARING IS THE WHOLE OF THE SAFETY. `_element_layer_ids` and
    its siblings are what the next run replaces, and adoption UPDATES
    them rather than replacing them -- so without this the dialog
    would believe it owned both groups' layers, and the next Generate
    would remove the layers of a map the user had switched away from.
    That is the paired-layer fault of 2026-08-16 arriving through a
    new door, and it is being written in the same commit as the door.
    """
    self._detach_from_the_group()
    self._group_name = group.name()
    self._adopt_existing_group(group)

  @staticmethod
  def _read_control(widget, kind):
    """One design control's value, in a form JSON can hold.

    Args:
      widget: the control named by a row of WORKING_STATE_DESIGN.
      kind: that row's third member -- "text", "data", "number",
        "checked" or "line".

    Returns:
      A str, int, float or bool. Nothing here returns a Qt object, so
      the record serializes without a custom encoder.

    Raises:
      ValueError: for a kind the table should never contain. Raised
        rather than ignored: the table is ours and static, so an
        unknown kind is a typing mistake, and silently skipping the
        control would drop it from the record without anything saying
        so -- which is the exact failure the single-table design of
        this record exists to prevent.
    """
    if kind == "text":
      return widget.currentText()
    if kind == "data":
      return widget.currentData()
    if kind == "number":
      return widget.value()
    if kind == "checked":
      return bool(widget.isChecked())
    if kind == "line":
      return widget.text()
    raise ValueError(f"working-state control kind {kind!r} is unknown")

  @staticmethod
  def _write_control(widget, kind, value):
    """Put a recorded value back into its design control.

    Args:
      widget: the control named by a row of WORKING_STATE_DESIGN.
      kind: that row's third member.
      value: whatever `_read_control` produced, after a JSON round
        trip.

    Returns:
      None. A "data" value the combo no longer offers is LEFT ALONE
      rather than forced: the element counts on offer are ours and
      fixed, so a miss means a record from another build, and moving
      the chooser to something arbitrary would be worse than keeping
      what is there.

    THE NUMBER IS COERCED TO THE BOX'S OWN TYPE, which is not
    fastidiousness. A QSpinBox holds an int and PyQt6 raises TypeError
    on `setValue(5.0)`, and JSON gives back a float for anything that
    was written with a decimal point -- so a grid row count restored
    from a saved project would raise inside whatever slot was calling,
    and an exception in a Qt slot is swallowed along with the rest of
    the handler.
    """
    if kind == "text":
      widget.setCurrentText("" if value is None else str(value))
    elif kind == "data":
      index = widget.findData(value)
      if index >= 0:
        widget.setCurrentIndex(index)
    elif kind == "number":
      widget.setValue(type(widget.value())(value))
    elif kind == "checked":
      widget.setChecked(bool(value))
    elif kind == "line":
      widget.setText("" if value is None else str(value))
    else:
      raise ValueError(f"working-state control kind {kind!r} is unknown")

  def _capture_working_state(self) -> dict:
    """The whole of the map this dialog currently describes.

    Returns:
      A plain dict, JSON-serializable, holding a version stamp, the
      design, one entry per element, and the two edge facts
      (WORKING_STATE_EDGES): where the output goes, and which dataset
      it was made from.

    Read straight off WORKING_STATE_DESIGN and `_assignments()`, so
    this function has no list of its own to fall out of step with the
    tables above. Capture and restore share those tables deliberately.
    """
    design = {}
    for key, attribute, kind in WORKING_STATE_DESIGN:
      widget = getattr(self, attribute, None)
      # A control absent from a half-built dialog is skipped rather
      # than recorded as None: restoring None into a spin box would
      # be a value nobody chose, where an absent key simply leaves
      # the control where it is.
      if widget is not None:
        design[key] = self._read_control(widget, kind)
    elements = [{key: assignment.get(key)
                 for key in WORKING_STATE_ELEMENT}
                for assignment in self._assignments()]
    # BACKFILL WHAT THE MODE HID. `_assignments` reports pins, class
    # colours, category colours and the window as empty for any row
    # not WEARING the mode that displays them -- absence-by-mode, not
    # absence-by-choice. The record is this design's persistence, so
    # it takes the kept work from the session dicts directly; the
    # apply side's mode gate (row 14) already refuses to clear on a
    # silent record, and a record that is never silent about kept
    # work cannot lose it at a reopen either. Found by the shelf hunt
    # of 2026-08-26 (the stamp writer) and confirmed against this
    # second writer by comparing stores.
    for element in elements:
      tid, var = str(element.get("id")), element.get("var")
      if not var:
        # A PARKED ROW STILL HAS A MEMORY. An element on "---"
        # displays nothing, so the flat keys stay empty -- but its
        # per-field work is exactly as real as an unworn field's on a
        # displaying row, and skipping the whole element here meant
        # parking a row and saving the project killed every pin and
        # hand-pick it ever held, in the record AND (via the stamp
        # writers reading `var or ""`) on the layer. The kept loop
        # below files EVERY field for a var-less element, since none
        # of them is displayed. Found by the kept hunt of 2026-08-26
        # (round nine) -- the maintainer's own "fields not in force
        # at a save" lead with its last corner unlit.
        kept = {}
        for field in (set(self._pinned_bounds.get(tid, {}))
                      | set(self._quant_colours.get(tid, {}))
                      | set(self._category_colours.get(tid, {}))):
          if not field:
            continue
          entry = {}
          if self._pinned_bounds.get(tid, {}).get(field):
            entry["pinned"] = dict(self._pinned_bounds[tid][field])
          if self._quant_colours.get(tid, {}).get(field):
            entry["quant_colours"] = dict(self._quant_colours[tid][field])
          if self._category_colours.get(tid, {}).get(field):
            entry["category_colours"] = \
              dict(self._category_colours[tid][field])
          if entry:
            kept[field] = entry
        if kept:
          element["kept"] = kept
        continue
      if not element.get("pinned"):
        kept = self._pinned_bounds.get(tid, {}).get(var)
        if kept:
          element["pinned"] = dict(kept)
      if not element.get("quant_colours"):
        kept = self._quant_colours.get(tid, {}).get(var)
        if kept:
          element["quant_colours"] = dict(kept)
      if not element.get("category_colours"):
        kept = self._category_colours.get(tid, {}).get(var)
        if kept:
          element["category_colours"] = dict(kept)
      if tuple(element.get("range_bounds") or (0, 100)) == (0, 100):
        window = tuple(self._ramp_ranges.get(tid, (0, 100)))
        if window != (0, 100):
          element["range_bounds"] = list(window)
      # ...AND THE OTHER FIELDS' KEPT WORK, so a saved PROJECT carries
      # the whole working memory home (maintainer's ruling,
      # 2026-08-26, the revisit ruling 6 anticipated). The flat keys
      # above hold the DISPLAYED field; `kept` holds every other
      # field's pins and hand-picks for this element, from the same
      # per-dataset bank, so ruling 8 is untouched. The group record
      # rides in the .qgz through the layer-tree node and never
      # reaches the GeoPackage -- and the FILE'S record must never
      # gain this key: what a redistributed file shows is the limit
      # of what it contains, which is why every write_working_state
      # call goes through `_file_safe_state`.
      kept = {}
      for field in (set(self._pinned_bounds.get(tid, {}))
                    | set(self._quant_colours.get(tid, {}))
                    | set(self._category_colours.get(tid, {}))):
        if field == var or not field:
          continue
        entry = {}
        if self._pinned_bounds.get(tid, {}).get(field):
          entry["pinned"] = dict(self._pinned_bounds[tid][field])
        if self._quant_colours.get(tid, {}).get(field):
          entry["quant_colours"] = dict(self._quant_colours[tid][field])
        if self._category_colours.get(tid, {}).get(field):
          entry["category_colours"] = \
            dict(self._category_colours[tid][field])
        if entry:
          kept[field] = entry
      if kept:
        element["kept"] = kept
    layer = self.layer_combo.currentLayer()
    return {
      "version": WORKING_STATE_VERSION,
      "design": design,
      "elements": elements,
      "output_path": self.gpkg_widget.filePath().strip() or None,
      # THE SOURCE AND NOT THE LAYER ID, because an id is a fact about
      # one QGIS session and a source survives the project being
      # closed. It is the same string every output layer already
      # carries as `weavingspace_region`.
      "region": layer.source() if layer is not None else None,
      # ...AND THE SYSTEM IT WAS DRAWN IN, because a CRS a person
      # ASSIGNED lives on the layer and not in its source string, so
      # rebuilding the region from `region` alone brings it back in
      # the file's own coordinates. Fixing a shapefile with no `.prj`
      # is the ordinary reason somebody assigns one, and a resumed map
      # whose region lands fourteen thousand kilometres from its tiles
      # is what that cost until 2026-08-28. Recorded beside the source
      # rather than inside it, and carried with it.
      "region_crs": (layer.crs().authid()
                     if layer is not None and layer.crs().isValid()
                     else None),
    }

  def _seeding_order(self, tile_ids, donor_for):
    """The order elements are SEEDED in, donors before their followers.

    Args:
      tile_ids: every element this run draws, in panel order.
      donor_for: a callable taking an element id and answering the
        element whose LAYER that one takes its classes from, or None
        where it follows nobody, follows a file, or follows a layer
        that is not one of this run's elements.

    Returns:
      A permutation of tile_ids in which an element that takes its
      classes from another element's layer comes AFTER that element.
      Nothing else is reordered, so a run with no follows returns the
      panel order it was given.

    Why it exists: the landing used to read every template once,
    before the loop, from the layers this run is REPLACING -- so a
    donor that MOVED was followed one run late, the follower drawing
    what the donor drew last time (ledger row 16 of 2026-08-27).
    Seeding the donor first is what lets the follower read the
    donor's NEW layer, and the template cannot simply be computed from
    the donor's ROW instead: a donor may be DEFERRING, its renderer
    made by hand in QGIS's dock and derivable from no assignment,
    which is exactly when following it is most useful.

    TWO ELEMENTS TAKING FROM EACH OTHER have no valid order, and that
    is not an error to refuse. The cycle is broken at whichever of
    them is reached second, so one keeps today's one-run lag and the
    other does not. Driven 2026-08-27: a cycle SETTLES rather than
    churning, because each run reads what the last one drew.
    """
    known = set(tile_ids)
    order, placed, placing = [], set(), set()

    def place(tid):
      # `placing` is the cycle guard, and reaching it is precisely what
      # leaves one element of a cycle reading its donor's outgoing
      # layer. `placed` is the ordinary already-done case.
      if tid in placed or tid in placing:
        return
      placing.add(tid)
      donor = donor_for(tid)
      if donor is not None and donor != tid and donor in known:
        place(donor)
      placing.discard(tid)
      placed.add(tid)
      order.append(tid)

    for tid in tile_ids:
      place(tid)
    return order

  def _join_in_panel_order(self, group, layer, tile_id):
    """Add a layer to the output group where its ELEMENT belongs.

    Args:
      group: the output group this run is filling.
      layer: the layer to add, already registered with the project.
      tile_id: the element the layer belongs to. A no-data twin
        carries its own element's id, which is what puts it directly
        below that element rather than at the end of the group.

    Returns:
      None. The layer joins before the first layer already in the
      group whose element sorts AFTER this one, and at the end when
      there is none -- so a twin, sorting equal to its element, lands
      under it.

    Why this exists rather than `group.addLayer`: seeding order and
    PANEL order stopped being the same thing when donors began being
    seeded before their followers (ruling 5 of 2026-08-27). Appending
    would leave the panel in whatever order the follow relationships
    forced, which is an order nobody chose and nobody can see the
    reason for; a panel reads `a`..`z` then `aa`.. through
    `bridge.element_order`, as every other list a person meets here
    does.
    """
    order = bridge.element_order(tile_id)
    at = None
    for index, node in enumerate(group.children()):
      # a group node has no `layer()`, and the outline layer carries no
      # tile id: both are simply passed over
      reader = getattr(node, "layer", None)
      other = reader() if callable(reader) else None
      named = (other.customProperty("weavingspace_tile_id")
               if other is not None else None)
      if named and bridge.element_order(str(named)) > order:
        at = index
        break
    if at is None:
      group.addLayer(layer)
    else:
      group.insertLayer(at, layer)

  def _repoint_donors(self, old_ids, new_ids):
    """Follow "take my classes from that layer" across a re-tile.

    Args:
      old_ids: the element layers this run replaced, by element.
      new_ids: the layers it made, by element.

    Returns:
      None. Rewrites any class-source choice naming a layer this run
      replaced so that it names the same ELEMENT'S new layer, and
      re-selects the affected rows' combos so the widget and the
      record agree.

    THE CHOICE IS STORED AS `layer:<layer id>`, and a re-tile gives
    every element a new layer with a new id -- so one Generate after
    the choice was made, the token named an object that no longer
    exists. The donor then read as an UNREADABLE source, the
    dependent kept the colours it already had under the keep-the-map
    promise, and two elements went on drawing one column in two sets
    of colours for good. That is the harm the control exists to
    prevent, arriving as a dangling reference rather than as a
    disagreement, which is why nothing complained. Measured
    2026-08-27: following works on arrival and the id stops resolving
    at the very next run.

    HEALED RATHER THAN RESOLVED AT EVERY READER, so the mended token
    is right in the row, in the group's record, in the project and in
    the GeoPackage; a reader-side fallback would leave four stores
    holding a reference to nothing.

    AND THE WIDGET IS MENDED WITH THE RECORD, because `_assignments`
    reads the COMBO. Healing the record alone was measured to last
    until the next rebuild, which writes the widget's stale answer
    back over it -- the same fault this column was given a fix for on
    2026-08-26, arriving from the other end.
    """
    replaced = {lid: tid for tid, lid in (old_ids or {}).items()}
    if not replaced:
      return
    moved = []
    for tid, token in list(self._class_choices.items()):
      if not token or not token.startswith("layer:"):
        continue
      donor = replaced.get(token[6:])
      if donor and donor in new_ids:
        self._class_choices[tid] = f"layer:{new_ids[donor]}"
        moved.append(tid)
    if not moved:
      return
    _dump("CLASSSRC", "repointed", ",".join(moved))
    for row in range(self.table.rowCount()):
      cell = self.table.item(row, 0)
      if cell is None or cell.text() not in moved:
        continue
      combo = self.table.cellWidget(row, 7)
      if combo is not None:
        self._populate_class_source_combo(
          combo, self._class_choices.get(cell.text(), ""))

  def _file_safe_state(self, record):
    """A working-state record fit to leave the machine in a GeoPackage.

    Args:
      record: a dict from `_capture_working_state`, or None.

    Returns:
      A deep-enough copy with every element's `kept` map removed, or
      None when the record was None. `kept` holds pins and hand-picked
      colours -- value strings and data-derived numbers -- for fields
      the map does NOT display, and the maintainer's ruling of
      2026-08-26 is that what a redistributed file shows is the limit
      of what it contains. The .qgz keeps the full record through the
      group's own property; only the FILE is stripped, at every
      write_working_state call, so a new call site cannot forget.
    """
    if not isinstance(record, dict):
      return record
    safe = dict(record)
    safe["elements"] = [
      {key: value for key, value in element.items() if key != "kept"}
      for element in (record.get("elements") or [])]
    return safe

  def _apply_working_state(self, record, keep_adopted=False) -> bool:
    """Put a group's recorded map back into the dialog.

    Args:
      record: a dict from `_read_working_state`, or None.
      keep_adopted: True at the ADOPTION doors (the constructor and a
        project read), where the only thing in the dicts is what
        adoption just recovered from THIS group's own layer stamps --
        so a key the record is silent about leaves the adopted value
        standing instead of clearing it. False at the group CHOOSER,
        where clearing on silence is what stops one group's answer
        riding onto another (ledger row 1). Passed through to
        `_apply_element_records`.

    Returns:
      True when the dialog was moved, False when there was nothing
      usable to apply.

    EVERY CONTROL IS WRITTEN WITH SIGNALS BLOCKED, as
    `_sync_pin_controls` already does, because setting a control right
    would otherwise fire the handler that set it right -- and those
    handlers rebuild the unit, queue a live run and destroy schemes.
    The rebuild is done ONCE at the end instead, deliberately.

    THE FAMILY IS SET IN THREE STEPS and not in one, because the
    family list is not a fixed list: `_on_n_changed` REBUILDS it from
    the element count and the kind, and `_on_family_changed` then
    writes the catalogue's own default over the over-under pattern. So
    the count and the kind go first, the list is rebuilt, the family is
    chosen, its options are shown, and only THEN is the rest of the
    table written -- so a recorded value always outranks a default
    that arrived while it was being restored.

    AND THE SIGNAL BLOCK IS RE-APPLIED after each of those calls.
    `QObject.blockSignals` is a flag rather than a counter, and both
    `_on_n_changed` and `_on_family_changed` block and UNBLOCK controls
    of their own on the way past -- so an outer block that was set once
    would be quietly cancelled by their inner release.
    """
    if not isinstance(record, dict):
      return False
    design = record.get("design") or {}
    rows = {key: (attribute, kind)
            for key, attribute, kind in WORKING_STATE_DESIGN}

    def blocked(state):
      for _key, attribute, _kind in WORKING_STATE_DESIGN:
        widget = getattr(self, attribute, None)
        if widget is not None:
          widget.blockSignals(state)
      self.gpkg_widget.blockSignals(state)

    def write(key):
      if key not in design or key not in rows:
        return
      attribute, kind = rows[key]
      widget = getattr(self, attribute, None)
      if widget is not None:
        self._write_control(widget, kind, design[key])

    blocked(True)
    try:
      write("n")
      write("kind")
      self._on_n_changed()          # rebuilds the family list
      blocked(True)
      write("family")
      self._on_family_changed()     # shows this family's own options
      blocked(True)
      for key in design:
        if key not in ("n", "kind", "family"):
          write(key)
      # THE OUTPUT PATH IS PART OF THE MAP, not of the session: see
      # WORKING_STATE_EDGES. A resumed group that wrote somewhere else
      # would put this map into a stranger's file.
      path = record.get("output_path")
      self.gpkg_widget.setFilePath(path or "")
      # A SPACING THAT CAME OUT OF A RECORD IS THE USER'S, because
      # somebody typed or accepted it when this group was made. Saying
      # otherwise would let the next change of dataset re-derive over
      # the number the group is being restored to show.
      self._spacing_is_mine = True
    finally:
      blocked(False)

    self._apply_element_records(record, keep_adopted)
    # The table is rebuilt ONCE, here, reading the record rather than
    # the rows it is about to replace. See `_restoring_assignments`.
    self._restoring_assignments = record.get("elements") or None
    self._rebuild_unit()
    # SPENT WHETHER OR NOT THE REBUILD USED IT. `_rebuild_unit`
    # returns early when there is no unit to build, and the record
    # left armed would then seed the NEXT rebuild -- one belonging to
    # a different design, or a different dataset. A record consumed
    # by whatever happens next is worse than one that was dropped.
    self._restoring_assignments = None
    return True

  def _apply_element_records(self, record, keep_adopted=False):
    """Write a record's per-element choices into the dialog's own dicts.

    Args:
      record: the whole working state, read for its "elements" list and
        for the "region" it was made from.
      keep_adopted: when True, a key the record is silent about never
        pops the dialog's dict -- the adoption-door contract, argued
        at `_apply_working_state`. Assignments still apply.

    Returns:
      None. Fills the element-keyed dicts `_refresh_table` restores
      from, so the rebuild that follows finds every choice where it
      normally looks. Nothing here touches a widget: the table is about
      to be rebuilt from scratch.

    THE VALUE-LADEN RECORDS ARE GATED ON THE DATASET, and that is
    ruling 8 of 2026-08-24 composed with ruling 4 rather than
    overruled by it. Hand-picked category colours are keyed by VALUE
    STRINGS and a pin holds data-derived NUMBERS, so both carry one
    dataset's content; restoring them onto another dataset would put
    that content into a second map and a second GeoPackage. Under the
    symmetric binding the two datasets agree on every ordinary
    journey, so this comparison costs one string and fires only when
    something has gone wrong -- a group whose source has moved, or a
    record written by hand.

    `quant_colours` is NOT gated: class colours are keyed by class
    INDEX, so they carry a choice about position on a ladder and no
    value from anybody's data.
    """
    elements = record.get("elements") or []
    layer = self.layer_combo.currentLayer()
    here = layer.source() if layer is not None else None
    # THROUGH `same_source`, AND THIS WAS THE EIGHTH SITE. The seven
    # mended on 2026-08-26 all compared a STAMP with a stamp; this one
    # compares the source of the layer in force with the region a
    # SAVED RECORD names, which is the same question across the same
    # boundary -- a project save respells the path half, so on Windows
    # every reopened project answered False here and dropped the pins
    # and the hand-picked colours the record was carrying home. Three
    # Windows-only reds, one comparison. A string that carries a path
    # inside it is a path, wherever the two halves came from.
    same_data = bool(here) and same_source(here, record.get("region"))
    for element in elements:
      if not isinstance(element, dict):
        continue
      tid = element.get("id")
      if not tid:
        continue
      var = element.get("var")
      # ASSIGNED, NOT MERELY SET -- ALL OF THEM, and this loop is the
      # reason to say it once here rather than at each line. Ruling 4
      # of 2026-08-25 is that selecting a group RESTORES the whole
      # working state "so nothing is inferred", and a key that is
      # written only when the incoming record HAS it infers the last
      # group's answer whenever this one is silent. Nothing else
      # clears these: `_detach_from_the_group` empties the layer ids
      # and the signatures and not this, and the per-dataset bank
      # swaps only on a change of DATASET, where two groups of one
      # dataset share a bank by construction.
      # MEASURED 2026-08-26, driven through the chooser's own signal:
      # a class colour hand-picked on one group came out drawn AND
      # STAMPED on another whose own record holds none, so it reached
      # the project file and the GeoPackage. Three hunts that could
      # not see each other reported it from three directions, which is
      # the strongest confirmation this method produces.
      # The window above was mended alone on 2026-08-26; its
      # neighbours are the same fault and were left standing, which is
      # this file's own "a guard added to one door belongs at every
      # door" wearing a fifth set of clothes.
      if element.get("ramp"):
        self._ramp_choices[tid] = element["ramp"]
      elif not keep_adopted:
        self._ramp_choices.pop(tid, None)
      if element.get("single_colour"):
        self._single_colours[tid] = element["single_colour"]
      elif not keep_adopted:
        self._single_colours.pop(tid, None)
      self._reverse_choices[tid] = bool(element.get("reverse"))
      if element.get("opacity") is not None:
        self._opacity_choices[tid] = int(element["opacity"])
      elif not keep_adopted:
        self._opacity_choices.pop(tid, None)
      self._class_choices[tid] = element.get("class_choice") or ""
      # THE COUNT ONLY WHERE SOMEBODY CHOSE IT. `k` is 50 on an
      # Unclassed row by the definition of that style rather than by
      # anybody's decision, and `_class_counts` is the record that
      # means CHOSEN -- writing the fifty into it is exactly what
      # test_an_unclassed_excursion_leaves_the_count_alone guards
      # against, arriving here by a new road.
      if element.get("scheme") != "Unclassed" \
          and element.get("k") is not None:
        self._class_counts[tid] = int(element["k"])
      elif not keep_adopted:
        # POPPED RATHER THAN WRITTEN, which keeps both promises at
        # once: an Unclassed row's fifty never becomes a CHOSEN count,
        # and a count chosen on the previous group does not survive
        # into one whose record says nobody chose anything.
        self._class_counts.pop(tid, None)
      # ASSIGNED, NOT MERELY SET, like the two siblings above it. This
      # wrote the window only when the incoming record held a narrowed
      # one, and nothing else clears the record -- `_detach_from_the_
      # group` empties the layer ids and the signatures and not this --
      # so a window narrowed on one group rode onto a group whose own
      # record says the ramp runs end to end, and that group's classes
      # took their colours from a stretch of ramp nobody chose for
      # them. Measured 2026-08-26 across two groups of one dataset:
      # the record said (0, 100) and the dialog held (10, 40).
      #
      # THE DEFAULT IS AN ABSENCE HERE, which is why this pops rather
      # than storing (0, 100): `_ramp_ranges` is the record that means
      # SOMEBODY NARROWED IT, exactly as `_class_counts` means somebody
      # CHOSE a count, and writing the default into it would make every
      # restored element look narrowed to every reader downstream.
      # SILENCE HAS MORE THAN ONE CAUSE, AND ONLY ONE OF THEM IS A
      # CHOICE. `_assignments` reports `pinned`, `quant_colours` and
      # `range_bounds` as empty for any row NOT WEARING GRADUATED, and
      # `category_colours` as empty for any row not wearing
      # Categorized -- so a record is silent about them whenever the
      # element is merely on another style, which is not the same
      # claim as "this group has none". Clearing on that silence
      # breaks the ruling of 2026-08-20 that THE RECORDS OF THE STYLE
      # A ROW IS NOT WEARING are kept, and kept SILENTLY, so a row
      # switched back finds its work where it left it.
      # FOUND BY A HUNT AIMED AT THESE VERY POPS, hours after they
      # were written: pin a bound, switch that element to categories,
      # choose your own group, and the pin was gone from the record
      # AND stamped absent on the layer, so a reopen could not bring
      # it back. The morning's ramp-window fix had the same fault, and
      # this is why "which reader made it silent" is the question.
      graduated = element.get("mode") == "Graduated"
      categorized = element.get("mode") == "Categorized"
      window = element.get("range_bounds")
      if window and tuple(window) != (0, 100):
        self._ramp_ranges[tid] = tuple(window)
      elif graduated and not keep_adopted:
        self._ramp_ranges.pop(tid, None)
      # THE VALUE-LADEN RECORDS ARE KEYED BY ELEMENT AND FIELD, so
      # what is cleared is this element's entry for THIS variable and
      # nothing else. Emptying the element outright would throw away
      # the work that switching a variable away and back is meant to
      # give back -- a colour picked for another column is not
      # something this group's record says anything about.
      if var:
        if element.get("quant_colours"):
          self._quant_colours.setdefault(tid, {})[var] = \
            dict(element["quant_colours"])
        elif graduated and not keep_adopted:
          self._quant_colours.get(tid, {}).pop(var, None)
      if not same_data:
        continue
      if var:
        if element.get("pinned"):
          self._pinned_bounds.setdefault(tid, {})[var] = \
            dict(element["pinned"])
        elif graduated and not keep_adopted:
          self._pinned_bounds.get(tid, {}).pop(var, None)
        if element.get("category_colours"):
          self._category_colours.setdefault(tid, {})[var] = \
            dict(element["category_colours"])
        elif categorized and not keep_adopted:
          self._category_colours.get(tid, {}).pop(var, None)
      # THE OTHER FIELDS' KEPT WORK comes back with the group, so a
      # reopened project restores what an in-session return always
      # has: pins and hand-picks for fields the row was not showing
      # at the save (maintainer's ruling, 2026-08-26). Assign-only,
      # deliberately: a record without the key is an OLD record, and
      # clearing on its silence would re-open the absence-by-mode
      # conflation row 14 closed. The displayed field's own records
      # were handled above and are not repeated here.
      for field, entry in (element.get("kept") or {}).items():
        if not field or field == var:
          continue
        if entry.get("pinned"):
          self._pinned_bounds.setdefault(tid, {})[field] = \
            dict(entry["pinned"])
        if entry.get("quant_colours"):
          self._quant_colours.setdefault(tid, {})[field] = \
            dict(entry["quant_colours"])
        if entry.get("category_colours"):
          self._category_colours.setdefault(tid, {})[field] = \
            dict(entry["category_colours"])

  def _stamp_working_state(self, group, launch_state=None):
    """Record the working state on an output group.

    Args:
      group: the layer-tree group this run's output landed in, or None.
      launch_state: the record captured when the run was LAUNCHED, or
        None on the restyle path, where nothing was launched and the
        controls have not moved since.

    Returns:
      None. Writes one JSON string to the group's own custom property,
      which QGIS saves inside the `.qgz` -- so the record persists with
      the project without this plugin owning a file of its own.

    THE TWO HALVES COME FROM DIFFERENT MOMENTS, deliberately, and each
    from the moment it is true. The DESIGN and the output path are the
    launch snapshot: a spacing typed while the tiling ran belongs to
    the next run, and a record claiming a design its own layers were
    not drawn at would be a false statement stored in somebody's
    project -- this software's characteristic failure wearing a custom
    property. The ELEMENTS are re-read LIVE, because everything the
    colour editors write is settled policy to re-read at the landing:
    those windows stay usable during a run, and a colour chosen in
    that window would otherwise be lost exactly as it once was from
    the map itself.

    A FAILURE HERE MUST NEVER COST A MAP. The group is perfectly
    usable without a record; it simply cannot be resumed, and telling
    somebody about a JSON error in the middle of making a map would be
    noise they cannot act on. It goes to the dump instead, where the
    next person diagnosing a group that will not restore will look.
    """
    if group is None:
      return
    try:
      record = self._capture_working_state()
      # THE MAP-SHAPED HALVES ARE CARRIED, NOT RE-DERIVED, and this is
      # what makes a stamp taken away from a landing safe. Until
      # 2026-08-26 the design, the output path and the region were
      # re-read from the live controls whenever no launch snapshot was
      # handed over -- which was true of the two writers round nine
      # added, the switch-out stamp and the queued restamp, neither of
      # which happens at a moment when the controls describe the map
      # this group holds. Measured: move the design controls away from
      # a landed group without generating, and one adopted dock edit
      # was enough to leave the group claiming a family, an element
      # count and a spacing its own layers were never drawn at; switch
      # the region chooser, and the group was filed under a dataset it
      # was not made from, which is the fact the landing's refusal and
      # the group binding both read.
      # So the previous record wins over a live reading, and only a
      # LANDING -- which passes the snapshot the run was launched
      # with -- may move these three. A group with no record yet still
      # takes the live values, since there is nothing older to trust.
      carried = self._read_working_state(group) or {}
      if isinstance(launch_state, dict):
        carried = {**carried, **launch_state}
      for key in ("design",) + WORKING_STATE_EDGES:
        if key in carried:
          record[key] = carried[key]
      # WHICH DATASET THIS RECORD NOW CLAIMS, and where that claim
      # came from: the two questions any disagreement between a
      # group's record and its layers comes down to.
      _dump("STATE", "stamp", group.name(),
            "region=", str(record.get("region"))[-26:],
            "from=", "launch" if isinstance(launch_state, dict)
            else ("carried" if carried else "live"))
      group.setCustomProperty(WORKING_STATE_PROPERTY, json.dumps(record))
    except Exception:
      _dump("STATE", "stamp-failed", traceback.format_exc(limit=3))

  def _load_pressed(self):
    """The Load button: carry on with the map the Open row names.

    Returns:
      None. Reads the path out of the Open chooser and hands it to
      `_resume_from_gpkg`, which does the work and says what it found.
      An empty chooser is answered in words rather than by opening a
      file dialogue: the row above says what Load will read, and a
      button that quietly asked a different question would make the
      chooser decorative.

    Why a button at all, when choosing a file could simply have done
    it: the maintainer's ruling of 2026-08-27 is that a path chooser
    records what you WOULD load from and the button does the loading.
    The first version of this tab resumed the moment a file was
    chosen, which is the same confusion as a save path that saved.
    """
    path = (self.resume_widget.filePath() or "").strip()
    if not path:
      self._report_quietly(
        "Choose a saved map in the box beside Load first.")
      return
    self._resume_from_gpkg(path)

  def _save_pressed(self):
    """The Save button: write the map as it stands.

    Returns:
      None. Everything it does is in `_save_the_map`, which is
      separated from the button so the whole act can be driven
      headlessly -- the suite presses this where a person would, and
      reads the file afterwards.
    """
    self._save_the_map()

  def _save_the_map(self, path=None) -> bool:
    """Write the map, its styles and its record to a GeoPackage.

    Args:
      path: where to write. Defaults to whatever the Save chooser
        holds, which is the ordinary case; a caller passes one only
        where it has a reason to.

    Returns:
      True when the file was written, False when there was nothing to
      write, nowhere to write it, or the user declined an overwrite.
      Every False answer is explained to the user first: a Save that
      does nothing and says nothing is the failure this whole ruling
      is about.

    WHAT IT WRITES, in one act, because these are one act: an element
    table per element (and one per no-data twin), each layer's style
    embedded into the file beside it, the stale tables this map no
    longer has, the source data when the box beside the chooser is
    ticked -- and dropped when it is not -- and last the resumable
    record, through `_file_safe_state`, so the file shows the limit of
    what it contains.

    WHY IT IS A BUTTON. Until 2026-08-27 every Generate wrote the file
    whenever an output path was set, so the map was saved as a side
    effect of drawing it: a path chosen for later was written to at
    once, live update had to be gated to stop it rewriting somebody's
    file on every keystroke, and clearing the box forked a second
    group. The maintainer ruled that saving is a positive act.

    THE LAYERS ARE REPOINTED AT THE FILE, in place, and that is not
    tidiness. A map drawn to memory layers and saved to a GeoPackage
    would otherwise come back EMPTY when the project is reopened --
    a memory layer round-trips through a .qgz as a valid layer with no
    features -- so the file would hold the map and the project would
    not. `compat.point_layer_at` keeps each layer's id, renderer, name
    and custom properties, which is what the rest of the dialog keys
    on.
    """
    import os
    from qgis.core import QgsProject
    from . import compat
    project = QgsProject.instance()
    if path is None:
      path = (self.gpkg_widget.filePath() or "").strip()
    if not path:
      self._report_quietly(
        "Choose a file in the box beside Save first.")
      return False
    # A PRESS MADE WHILE A RUN IS IN FLIGHT IS ABOUT THE RUN. What is
    # on screen at that moment is the PREVIOUS map, so writing it
    # would answer a different question from the one the press asked
    # -- silently, and over the file the user has just named. The run
    # lands in seconds and the press costs nothing to repeat.
    # This is the same door the group chooser and the resume already
    # guard with `self._task is not None`; a guard added to one door
    # belongs at every door into the same room.
    #
    # IT IS ASKED BEFORE "IS THERE A MAP", and the order is the whole
    # of what a person is told. On the FIRST run there are no element
    # layers yet, so the other way round a press mid-run answered
    # "There is no map to save yet. Press Generate first." -- which is
    # false twice over: they did press Generate, and it is running.
    # Found by the test that stages exactly that moment, 2026-08-27.
    if self._task is not None:
      self._report_quietly(
        "The map is still drawing. Save it once it has landed.")
      return False
    if not self._element_layer_ids:
      self._report_quietly(
        "There is no map to save yet. Press Generate first.")
      return False
    if not self._may_overwrite(path):
      return False
    # ASKED BEFORE ANYTHING IS WRITTEN, and that order is the whole of
    # it. Ownership is partly "have we saved here in this session",
    # which this very press is about to make true of any file at all --
    # so asking after the write would answer yes for a stranger's
    # GeoPackage and hand the drop below a licence to remove their
    # tables. The same trap the overwrite question already has, from
    # the other side.
    ours = self._this_map_owns_the_file(path)

    # WHAT EACH ELEMENT'S TABLE IS CALLED is decided when the map is
    # DRAWN, not here, so that two saves of one map cannot disagree
    # about it and so that the name follows the variable the element
    # actually displays (ruling 6 of 2026-08-25). A map adopted or
    # resumed rather than drawn carries the names it was found under.
    tables = dict(getattr(self, "_element_tables", {}) or {})
    order = sorted(self._element_layer_ids, key=bridge.element_order)
    missing = [tid for tid in order if tid not in tables]
    if missing:
      # THE LAYER'S OWN TABLE IS THE AUTHORITY where it already reads
      # from this file, and asking it is what stops a saved map being
      # destroyed by being saved. A dialog that opened a map with Load
      # never drew it, so it holds no record of what the tables are
      # called -- and where the region data could not be found the
      # variables are not restored either, so RECOMPUTING gave
      # `tiles_a` for a table the file calls `tiles_a_v1`. The save
      # then wrote four new tables, the stale-table drop removed the
      # four real ones as belonging to elements this map no longer
      # had, the embedded styles went with them, and the layers on
      # screen were left pointing at tables that no longer existed.
      # One press, and the file a person had opened was gone.
      # (Measured 2026-08-27 by the save matrix's `save-after-load`
      # route, on its first run.)
      taken = list(tables.values())
      for tid in missing:
        named = self._table_a_layer_already_reads(tid, path)
        if named:
          tables[tid] = named
          taken.append(named)
          continue
        # ...and only where there is no such layer is a name made up,
        # which is the adopted-group case this branch was written for:
        # the elements are known, the map was drawn elsewhere, and
        # naming the tables the way a run would have is a better
        # answer than refusing to save at all.
        assignment = self._assignment_for(tid) or {}
        tables[tid] = bridge.element_table_name(
          tid, assignment.get("var"), taken)
        taken.append(tables[tid])

    # A file that holds nothing is RECREATED and one that holds
    # something is added to, which is what protects a user's own
    # tables in a shared GeoPackage. "Does it exist" is not the
    # question -- closing a GeoPackage makes sqlite touch it, so a
    # deleted file can be back at zero bytes by the time we look.
    fresh = (not os.path.exists(path)) or os.path.getsize(path) == 0
    written_names = set()
    trouble = []
    for tid in order:
      # A TWIN NEVER TRAVELS WITHOUT ITS ELEMENT. The paired layer
      # holds the areas whose value is absent FOR THIS ELEMENT, so on
      # its own it is a set of holes belonging to nothing. Where the
      # element's layer has gone from the project -- somebody deleted
      # that one row of the group in the panel -- the loop below wrote
      # the twin anyway and the stale-table drop then took the element
      # table that was not written, leaving the file holding
      # `tiles_a_v1_no_data` with no `tiles_a_v1`. Measured 2026-08-28:
      # the plugin said "Saved", and a recipient's Load brought back
      # elements b, c and d beside an ORPHAN twin for a.
      # Skipping the pair leaves neither in the written names, so the
      # drop takes both and the file holds a map that is three elements
      # rather than a map that contradicts itself. That is the settled
      # shrank-design behaviour, applied to the pair rather than to one
      # half of it -- the paired-artefact rule of 2026-08-16, which
      # says every reader keyed on an element's identity gains a
      # second answer, read here from the writing side.
      if project.mapLayer(self._element_layer_ids.get(tid) or "") is None:
        continue
      for layer_id, table in (
          (self._element_layer_ids.get(tid), tables[tid]),
          (self._no_data_layer_ids.get(tid), f"{tables[tid]}_no_data")):
        layer = project.mapLayer(layer_id) if layer_id else None
        if layer is None:
          continue
        subset = layer.subsetString()
        # A LAYER ALREADY READING FROM THIS TABLE IS ALREADY SAVED,
        # and asking OGR to write it back is asking it to overwrite a
        # layer with itself, which it refuses: "Cannot overwrite an
        # OGR layer in place". Measured 2026-08-27, and it is not an
        # edge case -- it is the SECOND press on any map. The first
        # save repoints every layer at the file (which is what keeps
        # the map alive in a reopened project), so from then on every
        # further save met this, failed at the first element, and
        # returned before writing the styles, the stale-table drop or
        # the record. The whole of "save, change a colour, save
        # again" was unreachable.
        # The data needs no writing because it is already there: the
        # layer READS from that table, and QGIS commits a user's own
        # edits to the file itself. What still has to happen is
        # everything AFTER the write -- the style, the name counted as
        # current so the stale-table drop spares it, and the record.
        if same_source(layer.source(), f"{path}|layername={table}"):
          written_names.add(table)
          bridge.embed_style(layer)
          continue
        try:
          # `open_after=False`: the next line repoints THIS layer at
          # the table, so a layer opened here is discarded by
          # construction. The reason is that rather than a measured
          # saving -- an attempt to measure one here did not resolve a
          # difference at 64 or 128 elements, and the parameter's own
          # docstring says what was and was not established.
          bridge.write_gpkg_layer(layer, path, table, first=fresh,
                                  open_after=False)
        except Exception as e:
          trouble.append(f"{table}: {e}")
          continue
        fresh = False
        written_names.add(table)
        # ...and the project's own layer now reads from the file, so
        # the map survives the project being closed and reopened
        compat.point_layer_at(layer, path, table)
        if subset:
          layer.setSubsetString(subset)
        # the style goes in AFTER the repointing, or it would be
        # embedded against the memory layer's own source and the file
        # would carry a style nothing in it wears
        bridge.embed_style(layer)
    if trouble:
      self._report_quietly(
        f"Part of the map could not be written: {trouble[0]}")
      return False

    # Each handle above was opened while its siblings were still being
    # appended to the same file, so the earliest ones cache "no
    # spatial index" from that moment. One reload per layer, after all
    # the writing is over, refreshes the answer.
    for tid in order:
      for layer_id in (self._element_layer_ids.get(tid),
                       self._no_data_layer_ids.get(tid)):
        layer = project.mapLayer(layer_id) if layer_id else None
        if layer is not None:
          layer.dataProvider().reloadData()

    self._drop_tables_this_map_no_longer_has(path, written_names, ours)
    self._last_path = path
    self._gpkg_tables_written[self._gpkg_key(path)] = set(written_names)

    # THE RECORD LAST, so that a file which failed half way through
    # does not claim to be resumable. The design and the region come
    # from the group's own record where it has one, for the same
    # reason a landing takes them from its launch snapshot: they
    # describe the map that was DRAWN, and this method draws nothing.
    #
    # AND THAT SENTENCE WAS A CLAIM RATHER THAN A DESCRIPTION UNTIL
    # 2026-08-28. `_capture_working_state` reads the LIVE controls, so
    # with live update off -- where the map deliberately does not
    # follow the controls -- moving the design after a map landed and
    # then pressing Save wrote the design on SCREEN into the file
    # beside tiles drawn at another one. Measured: drawn at spacing
    # 600, box moved to 840, group record 600 and file record 840; and
    # with the element count moved 4 to 2, a file holding tiles a to d
    # whose own record names ['a', 'b']. A colleague opening it is
    # shown a design its tiles were never drawn at, and their first
    # Generate replaces the map with it.
    # The carry is the same one `_stamp_working_state` makes and for
    # the same reason (CLAUDE.md, 2026-08-26, ledger rows 55-57): only
    # a LANDING may move these three, because only a landing knows
    # what was drawn. Save is the second writer that never stands at
    # one, and it inherited the gap when the write moved here from the
    # landing path in 0ecdf7c.
    # TWO OF THE THREE, NOT ALL THREE, and the exception is the point:
    # `output_path` is the one edge this act legitimately decides. The
    # twin carries it because a landing does not choose where the file
    # goes; a SAVE does, and a file whose own record names another
    # file would point a resume at a stranger's map -- which is what
    # `_apply_working_state` says at the line that reads it back.
    resumable = self._capture_working_state()
    carried = self._read_working_state(self._group_of_our_layers(
      QgsProject.instance().layerTreeRoot())) or {}
    for key in ("design", "region", "region_crs"):
      if key in carried:
        resumable[key] = carried[key]
    # AND EACH ELEMENT'S VARIABLE, WHICH IS NOT A SETTING BUT A NAME.
    # The rest of an element's record is live on purpose, and must
    # stay so: the colour editors are usable while a run is in flight
    # and after it lands, so a colour or a pin chosen after the map
    # was drawn belongs in the file. The VARIABLE is different in kind
    # -- it decides the table the tiles were written into
    # (`tiles_<id>_<variable>`), so a live reading of it names a table
    # the file does not have.
    # Measured 2026-08-28, by a hunt aimed at this very repair an hour
    # after it landed: drawn with `a` on v1 into `tiles_a_v1`, the
    # chooser moved to v3, Save -- and the file's record said v3 while
    # its own table said v1, so a colleague's first Generate replaced
    # the sender's element. The same run re-drove this method's own
    # commit message and found its second example half-mended: design
    # n carried as 4 and the element list live as ['a', 'b'], beside
    # four tables. A record that contradicts itself is the thing the
    # ruling of 2026-08-26 forbids.
    # WHICH MOMENT EACH FIELD IS ABOUT is the question this file
    # already asks of every record built from two readings; the answer
    # here is per KEY rather than per record.
    # MEMBERSHIP AS WELL AS EACH ELEMENT'S VARIABLE, which the first
    # draft of this carry got wrong and the hunt aimed at it measured
    # the same evening. Carrying `design` -- which holds n -- while
    # leaving the element LIST live made the record contradict itself
    # the other way round: lower the count from four to two and press
    # Save, and the file held four tables under a record naming n=4
    # and two elements. A recipient's Load then brought c and d back
    # AUTO-ASSIGNED, so their controls named v3 and v1 beside layers
    # drawing v2 and v3, and their first Save destroyed both. Raising
    # the count gives the mirror: a record naming tables the file does
    # not hold.
    # So the record's ELEMENTS are the ones the map was drawn with,
    # each carrying the variable it was drawn with, and everything
    # else about them read live -- because the colour editors stay
    # usable after a landing and a colour or a pin chosen then belongs
    # in the file. That is the same per-key question as the design and
    # the region, asked of a list.
    drawn_list = [element for element in (carried.get("elements") or [])
                  if isinstance(element, dict) and element.get("id")]
    if drawn_list:
      live = {element.get("id"): element
              for element in (resumable.get("elements") or [])
              if isinstance(element, dict)}
      rebuilt = []
      for element in drawn_list:
        now = live.get(element["id"])
        if isinstance(now, dict):
          merged = dict(now)
          merged["var"] = element.get("var")
        else:
          # An element the table no longer shows at all: the map still
          # holds its tiles, so the record keeps what it was drawn
          # with rather than dropping it and orphaning the table.
          merged = dict(element)
        rebuilt.append(merged)
      resumable["elements"] = rebuilt
    resumable["region_embedded"] = self._embed_or_drop_the_source(path, ours)
    if not bridge.write_working_state(
        path, self._file_safe_state(resumable)):
      self._report_quietly(
        f"The map was saved to {os.path.basename(path)}, but its "
        f"design could not be written into the file, so opening it "
        f"elsewhere will show the map without carrying on with it.")
      return True
    # AND SAY SO WHERE THE DATA HAS MOVED SINCE THE MAP WAS DRAWN.
    # The file then holds tiles from the old numbers beside a copy of
    # the source holding the new ones, which is honest about neither
    # unless somebody is told. Measured 2026-08-28: a region edited in
    # QGIS between a Generate and a Save travelled as {7,17,27,37}
    # beside a map drawn from {0,1,2,3}, and the recipient was told
    # only that four element layers had opened.
    # ASKED OF THIS DATASET'S OWN READING, so it can only ever compare
    # like with like. A dataset nothing has been drawn from has no
    # entry and says nothing, which is the honest answer rather than a
    # guess: the record is keyed by layer id precisely so that another
    # map's reading can never be the one this comparison lands on.
    in_force = self.layer_combo.currentLayer()
    when_drawn = (None if in_force is None
                  else self._fingerprint_when_drawn.get(in_force.id()))
    moved = (when_drawn is not None
             and self._a_reading_of_the_data(in_force) != when_drawn)
    if moved:
      self._report_quietly(
        f"Saved to {os.path.basename(path)}. The data has changed "
        f"since this map was drawn, so the file holds the map as it "
        f"is and a copy of the data as it is now; press Generate and "
        f"save again to make them agree.")
      return True
    self._report_quietly(f"Saved to {os.path.basename(path)}.")
    return True

  def _table_a_layer_already_reads(self, tile_id, path):
    """The table in THIS file that an element's layer already reads.

    Args:
      tile_id: the element to ask about.
      path: the file being saved to.

    Returns:
      The table name, or None where that element has no layer, its
      layer reads from memory, or it reads from a DIFFERENT file --
      the last being a Save As, where the map must be written afresh
      under the names this map would choose rather than under the
      names some other file happens to use.

    Asked of the layer's own source rather than of any record here,
    because a map opened with Load was never drawn by this dialog and
    the record is empty; the source is the only witness that has not
    been through this session.
    """
    from qgis.core import QgsProject
    layer = QgsProject.instance().mapLayer(
      self._element_layer_ids.get(tile_id) or "")
    source = layer.source() if layer is not None else ""
    if "layername=" not in source:
      return None
    file_half = source.split("|", 1)[0]
    if not same_destination(file_half, path):
      return None
    return source.split("layername=", 1)[1].split("|", 1)[0] or None

  def _this_map_owns_the_file(self, path) -> bool:
    """Is this GeoPackage one THIS map has written, or somebody else's?

    Args:
      path: the file in question. It is assumed to exist and to hold
        something; an empty or absent file is nobody's and is decided
        by the caller.

    Returns:
      True where this dialog has already saved to it in this session,
      or where it carries a working-state record naming the dataset
      now in force. False otherwise, which means the file is somebody
      else's work as far as anything here can tell.

    IT IS ASKED OF THE FILE rather than remembered, which is what makes
    an ordinary re-save silent after a restart while keeping the
    question for the case that matters.

    WHY IT IS A METHOD OF ITS OWN, as of 2026-08-28. Two acts need this
    answer and only one of them was asking it: the overwrite question,
    and the drop that removes tables an earlier save left behind. The
    drop instead scoped itself to "this map's own elements" and decided
    that by the table-name prefix `tiles_<id>` -- and an element id is
    a LETTER, which every map in the world shares. So saving into a
    GeoPackage holding a colleague's map deleted their `tiles_a_*` and
    `tiles_b_*` and left `tiles_zz_*` and their own non-plugin tables
    standing, one line after a question promising to "leave the rest of
    the file alone". Measured 2026-08-28 by the `underneath` hunt and
    again here against a victim file built by bare GDAL, read back with
    stdlib sqlite3.
    THE LESSON THIS PROJECT ALREADY HAS: a name a user can choose is a
    LABEL and never an identity. A table name carries an element id,
    and an element id identifies an element WITHIN a map, not the map.
    """
    if self._gpkg_key(path) in self._gpkg_tables_written:
      return True
    record = bridge.read_working_state(path)
    if isinstance(record, dict):
      # A file carrying OUR record for THIS dataset is this map's own
      # file, met again after a restart. `same_source` owns the
      # comparison because a source is a path plus a layer name and a
      # project save respells the path half.
      layer = self.layer_combo.currentLayer()
      here = layer.source() if layer is not None else None
      if here and same_source(here, record.get("region")):
        return True
    return False

  def _may_overwrite(self, path) -> bool:
    """Ask before writing over a file this plugin did not write.

    Args:
      path: the file Save is about to write.

    Returns:
      True to go ahead, False when the user declined. A file that does
      not exist, holds nothing, or is one of ours is never asked
      about: with Save a deliberate press, asking every time is noise,
      and a file somebody else's work is in is not.
      (Maintainer's ruling, 2026-08-27.)

    WHAT COUNTS AS OURS, and it is asked of the FILE rather than
    remembered: a file this dialog has already saved to in this
    session, or one carrying a working-state record naming THE DATASET
    now in force. The second is what makes an ordinary re-save silent
    after a restart, and what keeps the question for the case that
    matters -- a GeoPackage holding somebody's own tables, or a map
    made from other data.

    IT IS THE DATASET AND NOT THE GROUP, deliberately, and the
    difference is worth stating because it leaves one case silent: a
    SECOND map of the SAME dataset, saved onto the first map's file,
    replaces it without a question. Three things decide that. The
    record carries `region` and `output_path` and no group identity at
    all (WORKING_STATE_EDGES), so a group-level question is not
    available to ask without widening what the file stores. The
    maintainer's ruling names the boundary as "a file the plugin did
    not write", and that file is one the plugin wrote from that data.
    And the save chooser is a SAVE-mode file dialogue, so the platform
    has already asked about replacing an existing file on the way in.
    If the group ever becomes the unit this question is asked about,
    the record needs a group identity first -- and this paragraph is
    where to start, rather than a comparison this record cannot make.
    """
    import os
    from qgis.PyQt.QtWidgets import QMessageBox
    if not os.path.exists(path) or os.path.getsize(path) == 0:
      return True
    if self._this_map_owns_the_file(path):
      return True
    answer = QMessageBox.question(
      self, "WeavingSpace",
      f"{os.path.basename(path)} already exists and was not written "
      f"by this map. Saving will replace the tables this map needs "
      f"and leave the rest of the file alone. Save anyway?",
      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
      QMessageBox.StandardButton.No)
    return answer == QMessageBox.StandardButton.Yes

  def _resume_from_gpkg(self, path) -> bool:
    """Carry on with a map saved to a GeoPackage.

    Args:
      path: the .gpkg to resume.

    Returns:
      True when the file's layers were loaded and its working state
      applied; False when there was nothing to resume, in which case
      the user has been told why.

    RULING 5 OF 2026-08-25, and the roadmap's "one I made earlier":
    point the plugin at a saved output GeoPackage -- WITHOUT the
    project that made it -- and have it adopt the group the way a
    reopened project is adopted. A demo can then open a finished
    result instead of tiling one live.

    NOTHING NEW IS INVENTED FOR THE STAMPS. Every output layer's
    custom properties are saved INSIDE its embedded style, so
    `loadDefaultStyle` brings back `weavingspace_output`,
    `weavingspace_tile_id` and the rest -- which is exactly what
    `test_an_exported_geopackage_is_still_recognised_as_our_own`
    already proves. So the layers arrive stamped, adoption recognises
    them on its own terms, and this method only has to put them in a
    group and apply the record.

    THE SOURCE COMES BACK BY REFERENCE unless it was embedded. If
    neither can be reached, the design is still restored and the user
    is told the data is missing: a map you can look at and cannot
    re-tile is worth more than a refusal.
    """
    # A GUARD ADDED TO ONE DOOR BELONGS AT EVERY DOOR INTO THE SAME
    # ROOM. `_on_group_chosen` and `_bind_group_to_dataset` both
    # refuse while a run is in flight, because repointing the records
    # mid-run lands the tiling in a rival group stamped with a
    # variable nobody chose -- and this third door had no guard, so a
    # resume during a run repointed `_element_layer_ids` under the
    # landing, silently dropped the map the user had just opened,
    # and one ordinary Generate then rewrote the saved GeoPackage
    # with the other dataset's tiling. Found by the doors hunt of
    # 2026-08-26 (round nine), the same shape as row 30.
    if self._task is not None:
      self._report_quietly(
        "A map is still being generated; open the saved map once it "
        "finishes.")
      return False
    record = bridge.read_working_state(path)
    if record is None:
      self._report_quietly(
        "That GeoPackage does not carry a saved map, so there is "
        "nothing to carry on with. Add its layers in QGIS to look at "
        "it.")
      return False
    version = record.get("version")
    if not isinstance(version, int) or version > WORKING_STATE_VERSION:
      # FORWARD-INCOMPATIBLE, REFUSED WHOLE. Taking the keys this
      # build happens to recognise would restore a design nobody
      # chose while looking exactly like a design somebody did.
      self._report_quietly(
        f"That map was saved by a newer version of the plugin "
        f"(record {version}, this build reads {WORKING_STATE_VERSION}), "
        "so it cannot be opened here. Update the plugin, or add its "
        "layers in QGIS to look at the map.")
      return False

    project = QgsProject.instance()
    from qgis.core import QgsVectorLayer
    from osgeo import gdal
    try:
      handle = gdal.OpenEx(path)
      tables = [handle.GetLayer(i).GetName()
                for i in range(handle.GetLayerCount())]
      handle = None
    except Exception:
      tables = []
    wanted = [name for name in tables if name.startswith("tiles_")]
    if not wanted:
      self._report_quietly(
        "That GeoPackage holds a saved map but none of its layers, so "
        "there is nothing to draw.")
      return False

    root = project.layerTreeRoot()
    # ONE FILE IS ONE MAP, so a file already open is TAKEN OVER rather
    # than opened again. Nothing asked this until 2026-08-26, and
    # resuming the same GeoPackage twice duly built a second group
    # over the same tables: two maps of one file, both drawing the
    # same layers, with the next Generate writing into the file both
    # of them read. That is the double map adoption exists to
    # prevent, arriving through a door adoption never sees -- and
    # under ruling 1 it is worse than it was, because the chooser
    # then offers two entries that are the same map and nothing
    # tells them apart.
    #
    # ASKED OF THE LAYERS' OWN SOURCES, never of a name: a group is
    # showing this file when it holds a layer whose provider string
    # names it. `|layername=` is what OGR appends per table, so the
    # comparison is on the part before it.
    already = None
    for node in root.findGroups():
      for child in node.children():
        layer = getattr(child, "layer", lambda: None)()
        try:
          source = layer.source() if layer is not None else ""
        except Exception:
          continue
        # THE FILE HALF THROUGH THE ONE COMPARATOR, never `==`. A
        # source is a path plus `|layername=`, and a path has more
        # than one spelling: a symlinked folder, a case-folding
        # filesystem, a Windows short name. Compared literally, a file
        # already open under another spelling opened a SECOND group
        # over the same tables -- two identical chooser entries, and
        # the next Generate rewriting the file both of them draw from.
        # The eight sites swept on 2026-08-26 all compared a stamp
        # with a stamp; this one compares a layer source with a path,
        # so a search for that shape could not reach it. (Ninth site,
        # found 2026-08-27.)
        if source and same_destination(source.split("|")[0], path):
          already = node
          break
      if already is not None:
        break
    if already is not None:
      # THE RECORD IS STILL APPLIED. Somebody asking to open a file
      # they already have open means "put me back on that map", which
      # is a resume rather than a no-op -- and the design may have
      # moved since. What is not done again is the LOADING, because
      # the layers are already there.
      # THE SOURCE COMES BACK FIRST, BEFORE THE DESIGN IS APPLIED, and
      # the order is the whole of it. `_apply_working_state` restores
      # each element's VARIABLE, and a variable can only be restored
      # to a column the region layer in force actually has -- so with
      # the chooser still on another dataset every element is
      # auto-assigned a default instead, the table then describes a
      # map the layers do not draw, and `_stamp_working_state` below
      # writes that loss onto the group.
      # THIS BRANCH HAD THE CALL AFTER THE RESTORE FOR AN HOUR, which
      # is this project's own rule arriving again: when a fix is
      # inserted into an existing sequence, check its ORDER against
      # the twin rather than only that the line is present. The twin
      # says why at its own call site; adding the call without
      # reading that is how presence came to stand in for order.
      # THE WHOLE RESUME RUNS UNDER `_selecting_a_group`, the recovery
      # and the tail included, and the window's width is the fix for
      # two defects the doors and switchdoor hunts found on the same
      # night (2026-08-26, round nine). The RECOVERY ran before the
      # window opened, so its `setLayer` fired the switch machinery:
      # the output path was cleared with a sentence, and the switch
      # door announced a re-point of an intermediate table the apply
      # replaced a breath later -- two spurious sentences on a journey
      # ruling 38 says stays silent. And the TAIL ran after the window
      # closed, so `_update_layer_exclusions` churned the layer combo,
      # `_bind_group_to_dataset` heard it, and the dialog was snatched
      # straight back to the current dataset's group -- the user told
      # "its map is the one being worked on" while standing on the
      # other map, the resumed group left unclaimed.
      self._selecting_a_group = True
      try:
        self._recover_the_source(path, record)
        self._take_over_group(already)
        self._apply_working_state(record)
        self.gpkg_widget.blockSignals(True)
        self.gpkg_widget.setFilePath(path)
        self.gpkg_widget.blockSignals(False)
        self._last_path = path
        # AND NOTHING HAS CHANGED SINCE THE MAP NOW ON SCREEN, for the
        # reason written at the twin below and with the same one line.
        # THE REPAIR WENT TO ONE DOOR OF TWO on 2026-08-28: the fresh
        # branch got it and this one did not, and this is the door a
        # person takes most -- opening a map whose layers are still in
        # the project, which is what "already open here" means. A Save
        # moves the output path, so the signature recorded at the last
        # landing no longer matches, the same-signature gate cannot
        # fire, and a live tick a second later re-tiled the opened map
        # into MEMORY layers: the GeoPackage-backed ones Save had just
        # made were removed and the project reopened empty. Measured
        # 2026-08-28 by comparing the two doors on one spelling of one
        # path -- fresh came back reading `ogr`, this one `memory`.
        # It needs no respelling to bite, though a respelt path reaches
        # it too, which is how the `pathspellings` hunt arrived.
        self._last_run_sig = self._run_signature()
        self._note_the_data_this_map_opened_over(record, path)
        # THE GROUP TAKES THE RECORD TOO, for the reason written at
        # the twin: the file carries it and the group did not, so
        # saving the project, reopening it and choosing that group
        # gave back its layers and none of its design. Measured here:
        # the twin leaves 1,959 characters on the group and this
        # branch left none. THE REGION IS THE FILE'S OWN: when
        # recovery fails the chooser still names the other dataset,
        # and a capture would stamp the resumed group as that
        # dataset's -- so choosing it later would re-tile the wrong
        # data into this file's own path.
        self._stamp_working_state(already, launch_state={
          key: value for key, value in
          (("region", record.get("region")), ("output_path", path))
          if value})
        # AND THE PLUGIN MUST NOT OFFER ITS OWN OUTPUT AS A REGION.
        # Construction, project-read and the run landing all update
        # the exclusions; this path registered element layers and did
        # not, so after a resume the region chooser listed the map's
        # own tile layers and could auto-select one -- and the next
        # Generate tiled the plugin's output, reporting success.
        self._update_layer_exclusions()
        self._refresh_group_combo()
      finally:
        self._selecting_a_group = False
      self._report_quietly(
        f"{os.path.basename(path)} is already open here, so its map "
        f"is the one being worked on.")
      return True
    # NAMED PROVISIONALLY, AND FOR ITS DATASET A MOMENT LATER. The
    # group has to exist before the file's layers can be put in it,
    # and the dataset is not known until `_recover_the_source` has
    # run, which is deliberately below -- so this takes a free name
    # now and the real one as soon as there is an answer.
    name = self._a_name_for_a_new_group(root)
    group = root.insertGroup(0, name)
    # TWO COUNTS, because they answer different questions. `opened` is
    # whether anything came back at all, which decides whether this
    # group has any business existing; `loaded` is how many ELEMENTS
    # came back, which is what the user is told. Sharing one number
    # between them is what made the message overstate the map, and
    # splitting them carelessly would leave a file of nothing but
    # paired layers with its group removed and its layers stranded
    # in the project, registered and shown nowhere.
    loaded = opened = 0
    # tables the file holds and QGIS would not open; reported once
    # below, beside the count of what did come back
    refused = []
    # (sort key, layer) for everything that opened, added to the group
    # together below so the panel reads in element order
    arriving = []
    for table in sorted(wanted):
      found = QgsVectorLayer(f"{path}|layername={table}", table, "ogr")
      if not found.isValid():
        # NAMED RATHER THAN PASSED OVER. The count below is honest --
        # it says how many layers came back -- but a person who saved
        # four elements and is handed three has lost one, and only the
        # case where EVERY table fails said anything. A loss is
        # reported, never silent, which is this project's own standing
        # rule. (Found by the notices hunt, 2026-08-27, by dropping
        # one element's table from a saved map and resuming it.)
        refused.append(table)
        continue
      # the stamps ride inside the embedded style, so this is what
      # makes the layer recognisably ours again
      found.loadDefaultStyle()
      # NAMED AS A FRESH RUN NAMES IT. The layers come back under
      # their TABLE names -- `tiles_a_v1`, `tiles_a_v1_no_data` -- so
      # a resumed map's panel and legend read in the plugin's internal
      # spelling where a generated one reads `a – v1` and
      # `a – no data`. Nobody outside this code knows what a tiles_
      # table is, and ruling 5 exists precisely so somebody can open a
      # finished result WITHOUT generating, which is the one journey
      # where nothing else ever corrects the name. The stamps needed
      # to compose it are on the layer the moment its embedded style
      # is loaded, one line above. (Found by the paired-layer hunt,
      # 2026-08-27.)
      # A NAME IS A LABEL AND NEVER AN IDENTITY, so nothing is looked
      # up by it and a name the user changes afterwards is theirs.
      stamped = (found.customProperty("weavingspace_tile_id") or "").strip()
      if stamped:
        if found.customProperty("weavingspace_no_data"):
          found.setName(f"{stamped} – no data")
        else:
          shown = next((element.get("var") for element
                        in (record.get("elements") or [])
                        if str(element.get("id")) == stamped), None)
          # An element carrying no variable keeps the table name
          # rather than being given a half-name: unassigned elements
          # are drawn as flat fill and a bare id says less than the
          # table does.
          if shown:
            found.setName(f"{stamped} – {shown}")
      project.addMapLayer(found, False)
      # ADDED IN ELEMENT ORDER, NOT TABLE ORDER, once every layer is
      # known. The tables are walked in `sorted` order, and a table
      # name carries its element -- so `tiles_aa_v1` falls before
      # `tiles_b_v1`, and a resumed map of more than twenty-six
      # elements would list its twenty-seventh SECOND while a freshly
      # generated one lists it last. `element_order` is the one owner
      # of that question (2026-08-27); the twin follows its element,
      # which is what the table order gave for free and this must
      # keep.
      arriving.append(
        ((bridge.element_order(stamped or table),
          1 if found.customProperty("weavingspace_no_data") else 0),
         found))
      # COUNTED AS AN ELEMENT ONLY IF IT IS ONE. A paired no-data
      # layer's table is `<table>_no_data`, which starts with `tiles_`
      # like every other, so counting the tables told somebody that a
      # four-element design had come back as six element layers. The
      # twins ARE loaded and adopted, correctly -- they are half of
      # how absence is drawn -- and they are simply not elements.
      opened += 1
      if not table.endswith("_no_data"):
        loaded += 1
    for _key, layer in sorted(arriving, key=lambda pair: pair[0]):
      group.addLayer(layer)
    if not opened:
      root.removeChildNode(group)
      self._report_quietly(
        "None of that GeoPackage's layers would open, so the map "
        "could not be brought back.")
      return False

    # THE SOURCE, by reference or from inside the file. Reached before
    # the record is applied, because the assignment table cannot
    # restore a variable to a column the region does not have -- and
    # INSIDE the `_selecting_a_group` window, with the tail, for the
    # two reasons written at the already-open branch above: the
    # recovery's `setLayer` must not fire the switch machinery's
    # sentences, and the tail's exclusion churn must not let the
    # binding snatch the dialog back to the current dataset's group.
    self._selecting_a_group = True
    try:
      self._recover_the_source(path, record)
      # ...AND NOW THE GROUP CAN SAY WHOSE MAP IT IS. Renamed before
      # `_take_over_group`, which records the name this dialog works
      # under; renaming a group nobody has seen yet is not the same
      # act as renaming one somebody named, which is theirs and is
      # never undone.
      named = self._a_name_for_a_new_group(root)
      if named != group.name():
        group.setName(named)
        self._group_name = named
      self._take_over_group(group)
      self._apply_working_state(record)
      # THE FILE BEING RESUMED IS THE OUTPUT FILE, whatever the record
      # says. The record carries the path the map was WRITTEN to, and
      # restoring that is right when the group is chosen inside its
      # own project -- but a resumed file may be a copy, or the same
      # file moved, and then the recorded path names somebody else's
      # map. Found by a hunt: copy a saved map, resume the copy, press
      # Generate, and the run overwrote the ORIGINAL while the copy
      # sat stale beside it. The one the user pointed at is the one
      # they mean.
      self.gpkg_widget.blockSignals(True)
      self.gpkg_widget.setFilePath(path)
      self.gpkg_widget.blockSignals(False)
      self._last_path = path
      # AND NOTHING HAS CHANGED SINCE THE MAP THAT IS NOW ON SCREEN,
      # which is what stops live update redrawing it. A resume arms
      # both debounce timers -- it moves the design controls to what
      # the file says -- and left `_last_run_sig` at whatever the
      # session had, so the same-signature gate could not fire and a
      # tick a second later re-tiled the opened map into MEMORY
      # layers. The GeoPackage-backed layers Save had made were
      # removed, so the project reopened empty: measured 2026-08-28
      # with live update at its default, 312 tiles becoming 0 across a
      # .qgz round trip, against 312 with the box unticked.
      # IT WAS INVISIBLE TO THE SUITE because every resume test unticks
      # live update -- a default no user is holding, which is the more
      # useful half of that measurement.
      self._last_run_sig = self._run_signature()
      # AND A RECOVERY IS STILL NOT A SWITCH. `_landed_this_session`
      # is set below so that a change of dataset after opening a map
      # is protected like any other -- but ONLY where this resume
      # actually found the data the map was made from. Where it did
      # not, the plugin has just asked the person to choose the region
      # layer to carry on with, and that choice is a RECOVERY: the
      # settled clause of 2026-08-21, in as many words. Setting the
      # flag regardless turned obeying that instruction into a switch,
      # so the path cleared, the group was let go and Generate built a
      # second identical group beside the map. Measured 2026-08-28 by
      # the hunt aimed at the repair that introduced it, with a
      # counterfactual arm.
      # RECOVERED MEANS THIS MAP'S OWN SOURCE, not merely that the
      # chooser holds something: a project that already contains an
      # unrelated polygon layer leaves the combo non-empty whether the
      # recovery worked or not, and asking the weaker question let the
      # defect straight back through. Either the recorded source, or
      # the copy inside the file where that is what was recovered.
      chosen = self.layer_combo.currentLayer()
      here = chosen.source() if chosen is not None else None
      recovered = bool(here) and (
        same_source(here, record.get("region") or "")
        or str(here).startswith(str(path)))
      # A MAP OPENED IS THIS SESSION'S WORK, exactly as a map drawn
      # is. `_landed_this_session` had one writer, the landing, so a
      # resume left it False: `switched_from_work` then read a change
      # of dataset as a FIRST CHOICE, `_begin_new_dataset` never ran,
      # the output path stayed pointed at the file just opened, and
      # nothing was said. Load a map, point the chooser at other data,
      # Generate, Save -- and the file you opened held the other
      # dataset's tiles under the first map's table names, measured
      # 2026-08-28 by reading the extents back with bare OGR. The
      # overwrite question could not save it either: the resume's own
      # adoption had already put the file into `_gpkg_tables_written`,
      # so `_may_overwrite` answered "ours".
      # The counterfactual is what named the cause: the identical
      # journey with this flag forced True clears the path and
      # announces it, like every other switch away from work.
      self._landed_this_session = recovered
      self._note_the_data_this_map_opened_over(record, path)
      # ...AND THE GROUP TAKES THE RECORD TOO, stamped with the FILE'S
      # region rather than whatever the chooser happens to hold when
      # recovery fails -- see the already-open branch.
      self._stamp_working_state(
        self._group_of_our_layers(QgsProject.instance().layerTreeRoot()),
        launch_state={key: value for key, value in
                      (("region", record.get("region")),
                       ("output_path", path)) if value})
      # THE SAME EXCLUSION THE OTHER BRANCH NEEDS, and for the same
      # reason: this path has just registered element layers, and
      # every other place that does so -- construction, project-read,
      # the run landing -- tells the region chooser to ignore them.
      # Without it the chooser offers the map's own tiles and the next
      # Generate draws a map from the plugin's output.
      self._update_layer_exclusions()
      self._refresh_group_combo()
    finally:
      self._selecting_a_group = False
    self._report_quietly(
      f"Opened the saved map from {os.path.basename(path)}: "
      f"{loaded} element layers.")
    # ...AND WHAT DID NOT COME BACK IS NAMED. Two causes, one
    # sentence, because a person meets one outcome: a table the file
    # still holds and QGIS will not open, and a table the file no
    # longer holds at all -- the second is what a dropped or partly
    # copied file gives you, and it never reached the loop above,
    # because the loop walks the tables the file HAS. Only the case
    # where EVERY table failed said anything, so somebody who saved
    # four elements and was handed three was told "3 element layers"
    # and nothing else, on the journey whose whole purpose is opening
    # a finished result. A loss is reported, never silent. (Found by
    # the notices hunt, 2026-08-27, by dropping one element's table
    # from a saved map and resuming it.)
    saved_elements = len([element for element
                          in (record.get("elements") or [])
                          if element.get("id")])
    # WRITTEN AS WHOLE SENTENCES rather than composed from fragments,
    # because the text-review queue shows a person what they are
    # approving and three interpolated pieces of one sentence cannot
    # be read or edited as prose.
    if saved_elements and loaded < saved_elements:
      self._report_quietly(
        f"That file gave back less than was saved to it: "
        f"{saved_elements - loaded} of its {saved_elements} element "
        f"layers are missing, so this map is not complete.")
    elif refused:
      self._report_quietly(
        f"{len(refused)} of that file's layers would not open, so this "
        f"map is not complete: {', '.join(sorted(refused))}.")
    return True

  def _areas_no_icon_reaches(self, element, paired, region=None):
    """How many of the region's areas no tile of this element touches.

    Args:
      element: the element's own output layer.
      paired: its no-data twin, or None. Counted TOO, because an
        element whose variable has gaps keeps those areas' icons on
        the twin -- counting the element alone reports every element
        on that column short by the number of gaps, which is the
        self-refuting sentence of 2026-08-16.
      region: the layer this run TILED. Defaults to the chooser's,
        which is right only while nobody has moved it since the run
        was launched -- the same reason `weavingspace_region` is taken
        from `source_layer` at the landing.

    Returns:
      The number of region features that no tile of this element
      intersects, or 0 when the question cannot be asked -- there is
      no region, or nothing was drawn. Zero rather than a guess: a
      sentence nobody can act on is worse than silence, and this
      number is quoted to a user.

    IT IS A SPATIAL QUESTION AND WAS ARITHMETIC. See the call site.
    Asked through a spatial index over the element's own tiles, so the
    cost is one index build plus one query per area rather than a
    comparison of two totals that are not comparable.

    AND A SPATIAL QUESTION HAS A CRS, which is what arithmetic never
    had to ask. `bridge.layer_to_gdf` sends a GEOGRAPHIC region to
    EPSG:3857 before tiling, so the output layers wear metres while the
    region still wears degrees -- and degrees never intersect metres,
    so every element counted as missing every area. A person with an
    ordinary WGS84 download therefore met, on every icon-mode run, a
    sentence naming all four elements as missing all sixteen areas
    while saying "which other elements still draw": false,
    self-contradictory, and impossible to act on. That is how a notice
    teaches people to ignore it.
    Measured 2026-08-28 by the `iconmode2` hunt on a 4326 grid, and
    again outside QGIS with bare OGR, shapely and pyproj: 16 per
    element untransformed, 0 per element once the region is put into
    the output's system. It shipped with the spatial rewrite the same
    evening; the guard written beside it uses the packaged Auckland
    data, which is EPSG:2193 and therefore cannot show it.
    """
    from qgis.core import (QgsCoordinateTransform, QgsGeometry,
                           QgsProject, QgsSpatialIndex)
    if region is None:
      region = self.layer_combo.currentLayer()
    if region is None or element is None:
      return 0
    tiles = []
    for layer in (element, paired):
      if layer is None:
        continue
      try:
        tiles.extend(f.geometry() for f in layer.getFeatures()
                     if not f.geometry().isEmpty())
      except Exception:
        return 0
    if not tiles:
      return 0
    index = QgsSpatialIndex()
    from qgis.core import QgsFeature
    holder = {}
    for number, geometry in enumerate(tiles):
      feature = QgsFeature(number)
      feature.setGeometry(geometry)
      index.addFeature(feature)
      holder[number] = geometry
    # THE REGION IS PUT INTO THE OUTPUT'S SYSTEM before anything is
    # compared. Where either side has no CRS the plugin tiles in the
    # layer's own coordinates and no transform is wanted; where they
    # agree there is nothing to do.
    move = None
    try:
      if (region.crs().isValid() and element.crs().isValid()
          and region.crs() != element.crs()):
        move = QgsCoordinateTransform(
          region.crs(), element.crs(), QgsProject.instance())
    except Exception:
      return 0
    missing = 0
    try:
      for area in region.getFeatures():
        shape = area.geometry()
        if shape is None or shape.isEmpty():
          continue
        if move is not None:
          # A transform can refuse a geometry outside its domain. The
          # honest answer then is the one this method already gives
          # when it cannot ask: nothing, rather than a count somebody
          # would act on.
          shape = QgsGeometry(shape)
          if shape.transform(move) != 0:
            return 0
        near = index.intersects(shape.boundingBox())
        if not any(holder[n].intersects(shape) for n in near):
          missing += 1
    except Exception:
      return 0
    return missing

  def _wear_the_recorded_crs(self, layer, record):
    """Give a recovered region the system it was drawn in.

    Args:
      layer: the layer just rebuilt from a recorded source string.
      record: the working state it was rebuilt from, read for
        "region_crs".

    Returns:
      None. Assigns the recorded system only where the layer's own is
      absent or differs, and only where the record has one -- a file
      that declares its system correctly needs nothing, and a record
      written before this key existed says nothing rather than
      claiming no CRS.

    A CRS A PERSON ASSIGNED IS NOT IN THE SOURCE STRING. It lives on
    the layer, so anything rebuilt from `source()` alone comes back in
    the file's coordinates -- which for a shapefile with no `.prj`, or
    a file that declares the wrong system, is the whole reason they
    assigned one.
    """
    from qgis.core import QgsCoordinateReferenceSystem
    authid = (record or {}).get("region_crs")
    if not authid or layer is None:
      return
    wanted = QgsCoordinateReferenceSystem(authid)
    if wanted.isValid() and layer.crs().authid() != authid:
      layer.setCrs(wanted)

  def _recover_the_source(self, path, record):
    """Point the region chooser at the data a saved map was made from.

    Args:
      path: the GeoPackage being resumed.
      record: its working state, read for "region" and for whether
        the source was embedded.

    Returns:
      None. Selects a layer already in the project where one matches,
      loads the recorded source where it can be reached, falls back to
      the copy inside the file where one was embedded, and says so
      when none of the three works.

    A LAYER ALREADY OPEN IS PREFERRED over loading a second copy of
    the same file, because two layers on one source is how a project
    ends up with the plugin pointed at one and the user editing the
    other.
    """
    from qgis.core import QgsVectorLayer
    project = QgsProject.instance()

    # THE BOX IS TOLD WHAT THE FILE HOLDS, before anything else, and
    # whichever of the three recoveries below runs. Until 2026-08-28 it
    # was not, and the cost landed on the person LEAST able to see it.
    # `_embed_or_drop_the_source` asks this control and nothing else,
    # and its drop branch was written for "the user unticked it"; a
    # dialog that has opened somebody's self-contained map with Load
    # has never touched the box, so the branch fired for "the plugin
    # never said" and stripped the copy the SENDER ticked it to
    # include. Measured that day: `weavingspace_region` present in the
    # file before the recipient's Save and absent after, read through
    # the plugin's own reader and through bare sqlite. The file could
    # then never be redrawn by anybody.
    # It is the repair-aimed-at-an-act rule met again: the drop was
    # right about the act and silent about its absence. The record is
    # the writer with a REASON here -- the sender decided this, and
    # the box is only a control -- so the record wins.
    # PER FILE, NOT ON THE CONTROL. The first repair set the checkbox
    # itself, and a hunt aimed at that repair measured what a
    # session-wide control does with a per-file fact, in both
    # directions: a recipient who opened an embedded map and then
    # pointed at their OWN private region had it copied into their own
    # file unasked, and a person who had ticked the box deliberately
    # had it silently unticked by opening any file without a copy in
    # it. The fact belongs to the FILE, so it is remembered against
    # the file and the control is left alone.
    self._embedded_when_resumed[self._gpkg_key(path)] = (
      bool(record.get("region_embedded")), self._embed_touches)

    wanted = record.get("region")
    if wanted:
      for layer in project.mapLayers().values():
        # OUR OWN OUTPUT IS NEVER THE ANSWER, however well its source
        # matches. The map-unit outlines layer is built on the REGION'S
        # OWN SOURCE -- deliberately, since nothing is copied -- and it
        # carries `weavingspace_output`, which is what keeps it out of
        # the region chooser. Those two facts are each right and they
        # collide in a walk that filters by neither: this loop took
        # whichever layer QGIS's map happened to yield first, and where
        # that was the outlines layer, `setLayer` on a layer the combo
        # EXCLUDES leaves the chooser empty -- and this returned, in
        # front of its own two fallbacks. The resume then reported
        # success beside a blank chooser, every element's variable
        # lost, and a Generate that launched nothing and said nothing.
        # Measured 2026-08-27: two of four ordinary reopen-and-resume
        # trials with nothing removed, and deterministic once the raw
        # layer is tidied out of the panel -- which is exactly what
        # having an outlines layer invites somebody to do.
        if layer.customProperty("weavingspace_output"):
          continue
        try:
          same = same_source(layer.source(), wanted)
        except Exception:
          continue
        if same:
          self.layer_combo.setLayer(layer)
          # ...AND THE CHOOSER IS ASKED WHETHER IT TOOK. A combo may
          # decline a layer for reasons this walk does not enumerate
          # -- the exclusion above is one and there may be others --
          # so a `setLayer` that did not land must fall through to the
          # fallbacks below rather than return as though it had.
          if self.layer_combo.currentLayer() is not None:
            return
      # named from the FILE half of the source alone: an OGR source
      # string carries `|layername=<table>`, so the basename of the
      # whole string read "region.gpkg|layername=region" in the
      # layers panel (the harm hunt of 2026-08-26)
      found = QgsVectorLayer(
        wanted, os.path.basename(str(wanted).split("|")[0]), "ogr")
      self._wear_the_recorded_crs(found, record)
      if found.isValid():
        project.addMapLayer(found)
        self.layer_combo.setLayer(found)
        return
    if record.get("region_embedded"):
      inside = QgsVectorLayer(
        f"{path}|layername={bridge.REGION_TABLE_NAME}",
        "region (from the saved map)", "ogr")
      self._wear_the_recorded_crs(inside, record)
      if inside.isValid():
        project.addMapLayer(inside)
        self.layer_combo.setLayer(inside)
        return
    self._report_quietly(
      "The data this map was made from could not be found, so it can "
      "be looked at but not redrawn. Choose the region layer to carry "
      "on.")

  def _embed_source_into(self, path, source_layer) -> bool:
    """Write the region's own data into the output file, if asked.

    Args:
      path: the output GeoPackage this run wrote.
      source_layer: the region layer that was tiled.

    Returns:
      True when the source was written into the file, False otherwise
      -- including when the box is unticked, which is the ordinary
      case, and when the write failed, since a file that cannot carry
      its source is still a perfectly good map.

    AN EXPLICIT OPT-IN, and the default is by REFERENCE (ruling 5 of
    2026-08-25). Two reasons, and the second is the one that decides
    it. A file stays small: the region is usually far larger than the
    tiles drawn from it. And a file stays PRIVATE -- somebody's data
    is not smuggled along inside a map of it, which is the same
    concern as ruling 8's, arriving at a different boundary. Making
    portability a choice somebody makes is the shape this plugin
    already uses for the dependency download.
    """
    box = getattr(self, "opt_embed_source", None)
    if box is None or not box.isChecked() or not path:
      return False
    if source_layer is None:
      return False
    try:
      frame = bridge.layer_to_gdf(
        source_layer, [f.name() for f in source_layer.fields()])
      written = bridge.write_gpkg_layer(
        bridge.gdf_to_layer(frame, bridge.REGION_TABLE_NAME),
        path, bridge.REGION_TABLE_NAME, first=False)
      return written is not None and written.isValid()
    except Exception:
      # The map is already written; a source that would not embed
      # costs the ability to resume this file on a machine that
      # cannot reach the original, and nothing else.
      _dump("STATE", "embed-failed", traceback.format_exc(limit=3))
      return False

  def _note_an_embed_touch(self, _on):
    """Count a deliberate opinion about including the source data.

    Args:
      _on: the box's new state, which this does not need -- ticking
        and unticking are both the user having spoken.

    Returns:
      None. Advances a counter that `_embed_or_drop_the_source` reads
      against the count recorded when each file was opened.

    WHY A COUNT AND NOT A FLAG. The question is per FILE: has this
    person expressed a choice SINCE THIS FILE was opened? A single
    session-wide "touched" bool answers a different question, and
    answering it cost a colleague's embedded data the first time this
    was written -- one tick anywhere in the session made every
    self-contained file opened afterwards strippable.
    """
    self._embed_touches += 1

  def _embed_or_drop_the_source(self, path, ours=True) -> bool:
    """Put the region data into the saved file, or take it back out.

    Args:
      path: the GeoPackage Save has just written.
      ours: whether this file was THIS map's before the save began.
        A file that is somebody else's gets nothing removed from it --
        `weavingspace_region` there is a table the plugin wrote for
        THEM, and taking it leaves their map unable to be redrawn by
        anyone. Taken before the write, because writing makes "we have
        saved here" true of any file at all.

    Returns:
      True when the file now holds a copy of the region layer, False
      when it does not -- which is the ordinary case, since embedding
      is an opt-in, and also the answer when a copy was removed or a
      write failed. The caller records it, so the file's own record
      and the file's own tables agree by construction.

    UNTICKING MEANS IT IS NOT IN THIS FILE. (Maintainer's ruling,
    2026-08-27, on ledger row 26 of that date.) Ticking the box,
    unticking it and saving again used to leave a full private copy of
    the region sitting in the file while the record beside it said
    `region_embedded: False` -- so the privacy the box promised was
    gone AND the resume the copy would have given was refused, since
    the record is what a resume reads. Measured on the file's own
    bytes through OGR.
    ONLY OUR OWN TABLE IS DROPPED, never anything else a user keeps in
    the file, which is the same line the stale-table drop holds: the
    plugin removes what the plugin wrote.
    IT FOLLOWS THE RULING OF 2026-08-26 that the file shows the limit
    of what it contains. A private copy somebody has switched off is
    exactly what they would be surprised to find in a file they send
    on.
    """
    box = getattr(self, "opt_embed_source", None)
    if box is not None and box.isChecked():
      # the layer in the chooser, which under the group binding is the
      # dataset this map belongs to
      return self._embed_source_into(path, self.layer_combo.currentLayer())
    # AND A COPY THE SENDER PUT THERE IS NOT THIS PERSON'S TO REMOVE
    # unless they say so. The drop below was written for the act of
    # UNTICKING; a dialog that opened somebody's self-contained map
    # has never touched the box, so without this it fired for the
    # act's ABSENCE and emptied a file the recipient could no longer
    # redraw. The question is asked of THIS file and only while the
    # box is untouched, so a deliberate untick still means what it
    # says.
    held, touches = self._embedded_when_resumed.get(
      self._gpkg_key(path), (False, None))
    if held and touches == self._embed_touches:
      return True
    # AND NOTHING IS REMOVED FROM A FILE THAT IS NOT THIS MAP'S.
    # `weavingspace_region` is a table the plugin writes, which is what
    # ruling 2 of 2026-08-27 scopes the drop to -- but in a GeoPackage
    # holding somebody ELSE'S map it is a table the plugin wrote for
    # THEM, and removing it leaves their map unable to be redrawn by
    # anyone. Measured 2026-08-28: saving into a colleague's file took
    # their embedded copy out along with two of their element tables.
    # In a file we do not own, only what we write is ours to touch.
    if ours and bridge.REGION_TABLE_NAME in bridge.gpkg_tables(path):
      bridge.drop_gpkg_layer(path, bridge.REGION_TABLE_NAME)
    return False

  def _drop_tables_this_map_no_longer_has(self, path, current, ours):
    """Remove element tables an earlier save left that this map lacks.

    Args:
      path: the GeoPackage being saved into.
      current: the table names this save has just written.
      ours: whether the file was THIS map's before this save began.
        Taken before anything is written, because the act of writing
        makes "we have saved here" true of any file whatever.

    Returns:
      None. Drops only tables THIS plugin wrote for THESE elements --
      never a table the user's own file already contained.

    A GeoPackage is replaced table by table, so a design that SHRANK
    would otherwise leave its old elements in the file: the map shows
    three and the file holds six, with nothing to say which three are
    the map. That file is the thing a user sends to somebody else, so
    the wrongness travels while the map stays right.

    THE FILE IS ASKED AS WELL AS THE SESSION, because the record is a
    record of what a DIALOG did. Since the variable joined the table
    name (ruling 6 of 2026-08-25), switching an element's variable
    writes a NEW table rather than replacing one -- so the old
    variable's table is stale the moment the switch lands, and a
    dialog that never adopted or resumed this file knows nothing about
    it. Resuming such a file loads the orphan as an extra element and
    the abandoned variable can paint over the map (measured
    2026-08-27, 23.7% of sampled pixels).
    SCOPED TO THIS MAP'S OWN ELEMENTS. A table for an element this map
    does not have is the shrank-design case the session record covers;
    sweeping every `tiles_*` in the file would make this a claim about
    somebody else's tables rather than about our own.
    """
    # NOTHING IS DROPPED FROM A FILE THAT IS NOT THIS MAP'S. The scope
    # below is by element id, and an element id is a LETTER that every
    # map shares -- so in a GeoPackage holding somebody else's map this
    # walk claimed their `tiles_a_*` and `tiles_b_*` as stale copies of
    # ours and removed them, while leaving their `tiles_zz_*` and their
    # own tables alone. That ran one line after a question promising to
    # "leave the rest of the file alone", and it made this method's own
    # Returns block ("never a table the user's own file already
    # contained") false. Measured 2026-08-28 against a victim file
    # built with bare GDAL and read back with stdlib sqlite3.
    # Their map is left whole; ours is still written beside it, which
    # is what the person asked for when they answered the question.
    if not ours:
      return
    key = self._gpkg_key(path)
    written = set(self._gpkg_tables_written.get(key, set()))
    # AND THE FILE'S OWN RECORD IS ASKED, which is the third reader
    # and the one that knows what the PREVIOUS save put there.
    # Until 2026-08-28 the candidates were the session's record union
    # the tables named for elements this map still has -- and a
    # DROPPED element is in neither. The docstring above called that
    # "the shrank-design case the session record covers", which is
    # true only while there is a group to adopt: that record is seeded
    # by adoption and cleared when a project is replaced. Close QGIS
    # without saving the project, or File > New with the dialog open,
    # reduce the design and save to the same file, and the dropped
    # elements' tables stayed -- with their columns, their values and
    # their `layer_styles` rows -- against a record naming only the
    # survivors. Measured 2026-08-28 across two processes: a file
    # holding `tiles_c_salary_secret` and `tiles_d_payroll_private`,
    # 66 rows each, read back with bare OGR, and the plugin's own Load
    # announcing four elements where the map had two.
    # THE SCOPE IS UNCHANGED and this is why the record rather than a
    # sweep: it names the elements THIS map's previous save wrote, so
    # nothing here becomes a claim about tables somebody else keeps in
    # the file. That is the ruling of 2026-08-26 -- the file shows the
    # limit of what it contains -- and ruling 8, since a dropped
    # element's column name and values are exactly the residue that
    # must not travel.
    knew = set(self._element_layer_ids)
    record = bridge.read_working_state(path)
    if isinstance(record, dict):
      for element in (record.get("elements") or []):
        if isinstance(element, dict) and element.get("id"):
          knew.add(str(element["id"]))
    for name in bridge.gpkg_tables(path):
      for tid in knew:
        stem = f"tiles_{tid}"
        if name == stem or name.startswith(f"{stem}_"):
          written.add(name)
          break
    for stale in sorted(written):
      # older records held bare element ids; those still name the
      # `tiles_<id>` they were written for
      name = stale if stale.startswith("tiles_") else f"tiles_{stale}"
      if name not in current:
        bridge.drop_gpkg_layer(path, name)

  def _read_working_state(self, group):
    """The working state a group carries, or None.

    Args:
      group: a layer-tree group, or None.

    Returns:
      The record as a dict, or None where the group has none, where
      what it has cannot be read, or where it was written by a LATER
      version of this plugin.

    A FORWARD-INCOMPATIBLE RECORD IS REFUSED WHOLE, and the user is
    told. Half-reading it -- taking the keys this build happens to
    recognise and ignoring the rest -- would restore a design nobody
    chose while looking exactly like a design somebody did, which is
    this project's characteristic failure wearing a file format.
    """
    if group is None:
      return None
    try:
      raw = group.customProperty(WORKING_STATE_PROPERTY)
    except Exception:
      return None
    if not raw:
      return None
    try:
      record = json.loads(raw)
    except Exception:
      _dump("STATE", "unreadable", group.name())
      return None
    if not isinstance(record, dict):
      return None
    version = record.get("version")
    if not isinstance(version, int):
      return None
    if version > WORKING_STATE_VERSION:
      self._report_quietly(
        f"This map was saved by a newer version of the plugin "
        f"(record {version}, this build reads {WORKING_STATE_VERSION}), "
        "so its settings cannot be restored. The layers are unaffected.")
      return None
    return record

  def _newest_output_group(self, root):
    """The output group a reopened dialog should take over.

    Args:
      root: the project's layer tree root.

    Returns:
      The layer-tree group holding the most recent output, or None
      when this project has none.

    WHY NOT ``findGroup(GROUP_BASE_NAME)``, which is what this did.
    "Create as new group" exists so a user can KEEP the previous
    result, and it names the new one "WeavingSpace tiles 2". The bare
    name then finds only the OLD group -- so a plugin closed and
    reopened, which users do constantly, adopted the map they had
    chosen to keep, and the next Generate overwrote exactly that
    while the map they were working on was orphaned and never updated
    again. Its stamps came back too, restoring a class bound they had
    unpinned. Measured 2026-08-15: run 1 pinned at 10, kept; run 2
    unpinned and recomputed; reopened, the dialog held run 1's layers
    and `{"a": {"v3": {"low": 10.0}}}`.

    AND WHY NOT THE NAME AT ALL, which is what replaced it. The newest
    used to be read off the SUFFIX -- the bare name counting as zero
    and "WeavingSpace tiles N" as N -- and the loop SKIPPED any group
    whose name did not match, on the reasoning that somebody had
    renamed it and it was not ours to guess. Renaming a group in the
    layers panel is an ordinary thing to do, and the consequence was
    that adoption found nothing: the next run built a rival, leaving
    the user's own layers in the renamed group, stale, with the
    GeoPackage link silently dropped. Measured 2026-08-17: rename,
    save, reopen, change the spacing, and the project holds
    'Deprivation, woven' with four file-backed layers beneath a fresh
    'WeavingSpace tiles' holding four memory layers of the same map.

    A group is OURS when it holds a layer carrying our own custom
    property, which is evidence rather than a guess about a name, and
    the same rule every other record in this dialog uses. It also
    means a layer somebody has dragged into a group of their own is
    followed rather than orphaned.

    THE NEWEST IS THE ONE NEAREST THE TOP of the layers panel, because
    that is how they are made: `_get_or_make_group` calls
    `insertGroup(0, ...)`, so each new group pushes the last one down.
    The suffix was a proxy for the same fact and disagreed with it in
    exactly one case -- a renamed group, where it gave no answer at
    all. `root.children()` is used rather than `findGroups()` because
    it is ordered and because it is deliberately NOT recursive: a
    group nested inside somebody's own folder is left alone, which
    `test_the_dialog_opens_quickly_in_a_crowded_project` stages with a
    decoy "WeavingSpace tiles 2" two levels down.
    """
    # THE DATASET IN THE CHOOSER OUTRANKS RECENCY, and that is the
    # 2026-08-25 half of this. Ruling 2 makes a second output group
    # the ordinary result of a demo, so "newest" stopped meaning "the
    # one this dialog is about": reopening a project holding maps of
    # two datasets and choosing the FIRST adopted the SECOND's group
    # and replaced its map at the next Generate -- two maps becoming
    # one dataset twice. A group made from the chosen dataset is
    # preferred; recency decides among those, and remains the whole
    # answer for output that predates the stamp.
    # ASKED THROUGH getattr, because adoption runs during
    # CONSTRUCTION, before the chooser exists -- the first draft of
    # this preference raised there, which is a Qt slot swallowing the
    # rest of the handler. With no chooser there is no dataset to
    # prefer, and recency is the whole answer, exactly as before.
    combo = getattr(self, "layer_combo", None)
    region = combo.currentLayer() if combo is not None else None
    wanted = region.source() if region is not None else ""
    fallback = None
    for node in root.children():
      # the root holds layers as well as groups; only a group can be
      # written into
      if not hasattr(node, "children"):
        continue
      # ...and it must actually hold output, or an empty leftover
      # would outrank the group carrying the user's map
      ours = [child.layer() for child in node.children()
              if getattr(child, "layer", lambda: None)() is not None
              and (child.layer().customProperty("weavingspace_tile_id")
                   or child.layer().customProperty(
                     "weavingspace_outline"))]
      if not ours:
        continue
      if fallback is None:
        fallback = node
      if not wanted:
        continue
      stamped = [layer.customProperty("weavingspace_region")
                 for layer in ours]
      if any(same_source(mark, wanted) for mark in stamped):
        return node
    # Nothing was made from this dataset -- or nothing says so, which
    # is what output from before the stamp looks like. The newest
    # group is the older and still correct answer there.
    return fallback

  def _group_of_our_layers(self, root):
    """The layer-tree group this dialog's own output is sitting in.

    Args:
      root: the project's layer tree root.

    Returns:
      The group holding a layer this dialog made, or None when it has
      made none yet, when they have all been removed, or when they are
      not in a group at all (a user can drag a layer out to the top
      level, and the root is not something we may write into).

    ASKING THE LAYERS IS EVIDENCE; asking for a name is a guess. Every
    other record in this dialog keys on a custom property, and the
    group lookup keyed on a NAME -- so renaming the group in the
    layers panel, which is an ordinary thing to do, hid it completely.
    A layer node knows its parent, so the group is simply wherever our
    layers are, whatever anybody has called it since.
    """
    project = QgsProject.instance()
    ids = list(self._element_layer_ids.values())
    ids += list(self._no_data_layer_ids.values())
    if self._outline_layer_id:
      ids.append(self._outline_layer_id)
    for layer_id in ids:
      # a record can outlive its layer: the user deletes one, or a
      # project is opened under an open dialog. Ask the project, not
      # the record, before believing the id names anything
      if project.mapLayer(layer_id) is None:
        continue
      # `findLayer` searches the whole tree, so this finds the layer
      # wherever it has been dragged to
      node = root.findLayer(layer_id)
      parent = node.parent() if node is not None else None
      # The tree ROOT has no parent of its own, which is how a group
      # under the root is told from the root itself -- identity
      # comparison against `root` is not reliable here, since PyQt
      # hands back a fresh wrapper around the same C++ object.
      if parent is not None and parent.parent() is not None:
        return parent
    return None

  def _a_name_for_a_new_group(self, root, tiled=None):
    """Compose the name a new output group takes.

    Args:
      root: the project's layer tree root, asked which names are
        already taken.
      tiled: the layer this map was made from, when the caller knows
        it; None asks the region chooser instead.

    Returns:
      The name, `WeavingSpace tiles — <dataset>`, with a counter
      appended only where that name is already in the tree. Nothing is
      created or renamed here.

    ONE OWNER, because the ruling of 2026-08-26 was written into the
    run's own door and NOT into the resume, which went on counting
    from the bare base -- so opening two saved maps in one project
    produced `WeavingSpace tiles` and `WeavingSpace tiles 2`, and the
    chooser, which appends the dataset only where the name lacks it,
    labelled both `WeavingSpace tiles — <dataset>`. Two identical
    entries writing different GeoPackages. A rule with two
    implementations has two behaviours the day one of them is wrong,
    which this project already knows from the candidate name that was
    derived twice.
    ASKED OF THE LAYER THIS MAP WAS MADE FROM where the caller knows
    it, falling back to the chooser only when it does not: which
    dataset a map came from is a fact about the tiles, and reading it
    live is what filed one dataset's tiles under another.
    THE NAME IS STILL A LABEL AND NEVER AN IDENTITY -- the lookup asks
    the layers, and a name a person changes is never changed back.
    """
    if tiled is None:
      combo = getattr(self, "layer_combo", None)
      tiled = combo.currentLayer() if combo is not None else None
    dataset = (tiled.name() or "").strip() if tiled is not None else ""
    base = f"{GROUP_BASE_NAME} — {dataset}" if dataset else GROUP_BASE_NAME
    name = base
    i = 1
    while root.findGroup(name) is not None:
      i += 1
      name = f"{base} {i}"
    return name

  def _get_or_make_group(self, force_new: bool, tiled=None):
    """Return (layer-tree group, created?) for this run's output.

    Args:
      force_new: skip the lookup entirely and build a new group. Set
        when the user ticked "Create as new group" or when the output
        destination changed, both of which mean this run must not
        overwrite the last one's result.
      tiled: the region layer this run was drawn from, used to NAME a
        group that has to be created. None where the caller has no
        such layer, and then the chooser answers instead; a name is a
        label rather than an identity, so an imperfect one costs a
        reader a moment and nothing else.

    Returns:
      A (group, created) pair. `created` is True only when a new group
      was made, which is also when every per-run record is reset --
      the caller reads `_element_layer_ids` afterwards to know what to
      replace, so emptying it here says "there is nothing to replace".

    Reuses the group from the previous run unless forced or the user
    deleted it; a new group is named for the dataset it was made from
    ("WeavingSpace tiles — nyc"), with a counter where that name is
    taken. ``insertGroup(0, ...)`` puts it at the top of the layers
    panel.

    THE LOOKUP ASKS THE LAYERS FIRST, and the name only as a fallback.
    Keying on the name meant a renamed group could not be found, so
    the next run built a rival over the same GeoPackage tables and
    -- because the miss also empties `_element_layer_ids`, which
    `_add_output_layers` reads as `old_ids` immediately afterwards --
    removed none of the layers it was replacing. Eight layers, two
    groups, four tables, and the abandoned group redrawing the new
    data under the old class breaks. Measured 2026-08-17 through both
    doors; guarded by
    `test_a_renamed_group_is_still_the_group_the_next_run_replaces`.

    The NAME FALLBACK is still worth having, for the one case the
    layers cannot answer: the group survives while its layers do not,
    which is what a user deleting the layers and undoing produces
    (`test_qgis_changes_around_the_plugin` stages exactly that, with
    QGIS restoring clones under new ids).
    """
    root = QgsProject.instance().layerTreeRoot()
    if not force_new:
      group = self._group_of_our_layers(root)
      if group is None and self._group_name:
        group = root.findGroup(self._group_name)
      if group is not None:
        # FOLLOW THE RENAME rather than undoing it. `_add_output_layers`
        # calls `setName(self._group_name)` on the way past, so leaving
        # the old name here would put it back and overrule the user in
        # the same breath as finding their group.
        self._group_name = group.name()
        return group, False
    # NAMED FOR THE DATASET IT IS MADE FROM (maintainer's ruling,
    # 2026-08-26, on meeting a panel of "WeavingSpace tiles" and
    # "WeavingSpace tiles 2" after tiling two datasets). The chooser
    # has labelled these groups with their dataset since the group
    # became the unit of work, so the name a person reads in the
    # dialog and the name they read in the layers panel disagreed for
    # no reason: the panel had the counter and the chooser had the
    # answer. The plugin's own name stays FIRST so its groups sort
    # together, which is what the counter was doing for them.
    #
    # ASKED OF THE LAYER THIS RUN TILED where the caller knows it,
    # falling back to the chooser only when it does not: which dataset
    # a map came from is a fact about the tiles, and reading it live
    # is what filed one dataset's tiles under another earlier today.
    name = self._a_name_for_a_new_group(root, tiled)
    self._group_name = name
    self._element_layer_ids = {}
    self._no_data_layer_ids = {}
    self._outline_layer_id = None
    self._last_signatures = {}
    return root.insertGroup(0, name), True

  def _on_generated(self, gdf, error, family, source_layer, assignments,
                    path, run_sig=None, geometry_sig=None, live=False,
                    outlines=None, launch_state=None):
    """Main-thread completion handler for every run, successful or not.

    Args:
      gdf: the tiled GeoDataFrame, or None when the run failed or was
        cancelled.
      error: the exception raised in the worker, or None.
      family: the design's display name, for messages.
      source_layer: the region layer that was tiled.
      assignments: the table snapshot taken when the run STARTED, so
        symbology always matches the geometry it was computed with.
      path: the GeoPackage being written, or None.
      run_sig, geometry_sig: what this run drew, captured at launch.
        Recording them here instead would read the table as it stands
        NOW, which may already carry a change made while the tiling
        ran -- and the dialog would then believe the map matches
        settings it never used.
      live: whether this run came from the live-update debounce
        rather than from the user pressing Generate. It decides how
        loudly a failure is reported -- an explicit Generate that
        fails owes the user a message, while a live run that fails
        must not interrupt somebody who never asked for it -- and it
        is what allows a queued live rerun to start once this one has
        finished landing its layers.
      outlines: whether the outlines box was ticked WHEN THIS RUN WAS
        LAUNCHED, captured for the same reason the signatures are and
        passed straight through to _add_output_layers. It is the one
        geometry setting the LANDING acts on rather than the tiling,
        so reading it live there let a mid-run toggle cancel its own
        signature difference. None means read it now.
      launch_state: the working state captured when this run was
        launched, passed through to the landing so the record the
        output group carries describes the design that was actually
        tiled. None where no snapshot was taken.

    Returns:
      None; the project gains the layers, and the dialog returns to
      an idle state via _finish_run.

    Sorts cancellation (both None: reset quietly), failure (shown
    with the worker's exception), empty output, and success (layers
    added by ``_add_output_layers``; its own failures are caught so an
    output-side bug cannot wedge the dialog either).

    ORDER MATTERS, and an earlier version got it wrong. The running
    state is cleared and any queued live rerun started only in the
    ``finally`` at the end, AFTER the layers exist. Building output is
    main-thread work — a layer per element, renderer seeding, possibly
    a GeoPackage write — and on a big map it takes noticeably longer
    than the tiling did. Clearing the state first let a queued live
    run launch a second task while the first was still materializing:
    tasks piled up in QGIS's task manager, and because the progress
    bar had already been hidden the last thing the user saw was the
    worker's "5%", which reads as a hang.
    """
    # A RETIRED DIALOG'S RESULT IS DISCARDED, whole. Retirement
    # cancels the task, but a run past its worker has already
    # reported, so its landing arrives here regardless -- and a
    # landing executed for a window the user has replaced removed the
    # live session's layers, adopted nothing, and built a rival
    # group beside the map ("WeavingSpace tiles 2", eight plugin
    # layers, one session) -- rows 18 and 19's settled rules broken
    # at a fifth door. The natural way to reach it is the natural act
    # itself: the landing is the long, hang-looking phase, and
    # clicking the toolbar button then is the ordinary retry. Found
    # by the seams hunt of 2026-08-26 (round nine). The map the user
    # keeps is whatever the LIVE dialog owns; this result belonged to
    # a window that no longer exists.
    if _dialog_is_gone(self) or _live_dialog() is not self:
      self._task = None
      return
    if gdf is None and error is None:
      self._finish_run()
      return  # cancelled: reset quietly
    if error is not None:
      self._finish_run()
      if isinstance(error, MemoryError):
        message = ("Ran out of memory while tiling; a larger spacing "
                   "will work for this layer.")
      else:
        message = "Tiling failed:\n\n" + "".join(
          traceback.format_exception_only(type(error), error))
      if live:
        self._report_quietly(message.replace("\n\n", " "))
      else:
        QMessageBox.critical(self, "WeavingSpace", message)
      return
    if gdf is None or len(gdf) == 0:
      self._finish_run()
      # ...and the same for a run that came back empty, which on a
      # live update is a spacing the user is still adjusting rather
      # than anything they need stopping for.
      if live:
        self._report_quietly("The tiling produced no tiles.")
      else:
        QMessageBox.warning(self, "WeavingSpace",
                            "The tiling produced no tiles.")
      return
    # the output phase: keep the progress bar up, in its indefinite
    # (busy) form, and say what is happening. This is the part that
    # used to look like a hang
    self.progress.setRange(0, 0)
    self.live_note.setText(f"Adding {len(gdf):,} tiles to the map...")
    QApplication.processEvents()  # let that text actually paint
    try:
      self._add_output_layers(gdf, family, source_layer, assignments,
                              path, run_sig, geometry_sig, outlines,
                              launch_state)
    except Exception as e:
      # The commonest way to land here is the user deleting the region
      # layer while the tiling ran: the result is fine, but there is
      # nothing left to attach it to. That is not an error to stop the
      # world with -- it is a thing the user just did on purpose -- so
      # it goes to the message bar, where QGIS puts everything else of
      # that kind. A modal box here also hangs any headless run,
      # because offscreen nobody can dismiss it.
      if not self._source_layer_alive(source_layer):
        self._report_quietly(
          "The region layer was removed while the map was being made, "
          "so there was nothing to add it to.")
      elif live:
        self._report_quietly(
          "Could not add the result layers: " + "".join(
            traceback.format_exception_only(type(e), e)).strip())
      else:
        QMessageBox.critical(
          self, "WeavingSpace",
          "Could not add the result layers:\n" + "".join(
            traceback.format_exception_only(type(e), e)))
    finally:
      self.live_note.setText("")
      self._finish_run()

  def _source_layer_alive(self, source_layer) -> bool:
    """Is the region layer this run tiled still in the project?

    Args:
      source_layer: the layer handed to the run when it started.

    Returns:
      True when it is still registered. A layer the user deleted
      mid-run leaves a Python wrapper whose C++ object is gone, so
      touching it raises RuntimeError rather than returning None --
      hence the try.
    """
    if source_layer is None:
      return False
    try:
      return QgsProject.instance().mapLayer(source_layer.id()) is not None
    except RuntimeError:
      return False

  def _legibility_note(self, fills, assignments):
    """The colour-legibility opinion, or None -- gated HERE.

    Args:
      fills: {tile_id: [(r, g, b), ...]} of what each element paints.
      assignments: the run's assignment dicts, for the shared-ramp
        exemption (elements deliberately sharing one ramp are not a
        clash, they are the shared-ramp technique).

    Returns:
      perception.clash_message's sentence, or None -- always None
      while "Warn about lack of legibility in colour choices" is
      unchecked. The gate lives INSIDE this helper so every caller,
      present and future, inherits it: the opt-in is a property of
      the opinion itself, not a courtesy each call site remembers.
      The user has reported ungated sightings; whatever path fires
      next fires through here, gated. (User instruction, 2026-08-09,
      twice.)
    """
    if not self.opt_colour_warnings.isChecked():
      return None
    from weavingspace_qgis import perception
    return perception.clash_message(perception.clashes(
      fills,
      shared={a["id"]: (a.get("ramp"), a.get("reverse"),
                        a.get("class_source"))
              for a in assignments}))

  def _report_quietly(self, message: str) -> None:
    """Tell the user something without stopping them.

    Args:
      message: one sentence for QGIS's message bar.

    Returns:
      None. Falls back to the dialog's own note line when there is no
      iface (which is how the tests run), so nothing is ever lost
      just because there is no QGIS window.

    One run can produce three notices at once -- areas left out at
    this spacing, categories whose colours moved, and element colours
    a reader cannot separate. QGIS's message bar stacks them, so a
    user sees all three; a QLabel holds one string, so the fallback
    used to keep only the last and silently drop the rest. That made
    the promise above false exactly when several things were wrong at
    once, which is when a reader most needs to be told. Notices are
    therefore JOINED rather than replaced.
    """
    if self.iface is not None:
      self.iface.messageBar().pushWarning("WeavingSpace", message)
      return
    existing = self.live_note.text()
    # a repeat within one run says nothing new, and stacking it would
    # push the earlier notices out of sight
    if message in existing.split(NOTE_SEPARATOR):
      return
    self.live_note.setText(
      f"{existing}{NOTE_SEPARATOR}{message}" if existing else message)

  def _finish_run(self):
    """End of a run, however it ended: re-enable Generate, hide the
    progress bar, forget the task, and only THEN start any live rerun
    that was queued while we were busy. Called from exactly one place
    per outcome so a run can never be left half-finished."""
    self.generate_btn.setEnabled(True)
    self.progress.setVisible(False)
    self.progress.setRange(0, 100)
    self._task = None
    # A dock edit made WHILE the run was in flight was ignored by the
    # styleChanged watcher (a run in progress must not be mistaken for
    # a user restyle) and then carried across by the preserved-
    # renderer path -- on the map but in no record, so the ramp cell
    # went on naming a ramp the layer no longer wears. Re-examine
    # exactly the preserved layers now the run is over -- but ONLY
    # those whose table state has not moved since the run landed. An
    # element the user changed mid-run also reads as "preserved" (the
    # landing used the launch snapshot), and re-examining it would
    # adopt the OLD colours as hand-picks that then outrank the very
    # change the user made: three race tests failed exactly that way
    # the first time this loop ran unguarded. A moved element belongs
    # to the queued rerun, which re-seeds it; a real dock edit made
    # after that rerun reaches the watcher normally.
    if self._preserved_this_run:
      current_by_id = {a["id"]: a for a in self._assignments()}
      for tid in self._preserved_this_run:
        lid = self._element_layer_ids.get(tid)
        assignment = current_by_id.get(tid)
        if lid and assignment is not None and \
            self._last_signatures.get(tid) == self._signature(assignment):
          self._on_layer_style_edited(lid, tid)
    self._preserved_this_run = []
    # ...AND REPLAY THE DOCK EDITS THAT ARRIVED UNDER THE RUN, which
    # is the one place `_adoption_deferred` is emptied by USE rather
    # than by being thrown away. The other three sites clear it
    # because the element is being rebuilt from scratch and a ladder
    # typed against the old one means nothing.
    #
    # DEFERRED BY A TIMER, because `_task` is cleared only AFTER
    # `_add_output_layers` -- a settled rule, so that a queued live
    # run cannot start a second tiling underneath output building --
    # and replaying here would meet the very guard that deferred
    # these in the first place and defer them again, forever.
    # singleShot(0) runs once this call stack has unwound and the
    # plugin is genuinely at rest.
    if self._adoption_deferred:
      QTimer.singleShot(0, self._replay_deferred_adoptions)
    # A PRESS QUEUED UNDER THE RUN IS RE-PRESSED, never handed to the
    # live path: that path returns at its second gate whenever live
    # update is off, which is exactly the state somebody is in when
    # they are pressing the button. Deferred by a timer for the same
    # reason the adoption replay above is -- `_task` was cleared a few
    # lines up, but this call stack is still inside the landing, and
    # `_generate` is entitled to a plugin at rest. A closed window
    # presses nothing.
    if self._press_pending:
      self._press_pending = False
      self._live_pending = False    # the press supersedes a live tick
      if not self._closed:
        QTimer.singleShot(0, self._generate)
    elif self._live_pending:
      self._live_pending = False
      self._live_timer.start()

  def _add_output_layers(self, gdf, family, source_layer, assignments,
                         path, run_sig=None, geometry_sig=None,
                         outlines=None, launch_state=None):
    """Turn the tiled GeoDataFrame into the project's output layers.

    Args:
      gdf: the worker's result, CRS already reattached on the main
        thread. One row per tile, with a ``tile_id`` column and the
        mapped variables joined on.
      family: the design's display name, used in the layer-group's
        message and the status note.
      source_layer: the region layer that was tiled; the optional
        outlines layer is made from it.
      assignments: the ``_assignments()`` snapshot taken BEFORE the
        run began, so fiddling with the table during a long tiling
        cannot leave the symbology disagreeing with the geometry.
      path: a GeoPackage path, or None for temporary layers. With a
        path, each element is written into the file, the file-backed
        layer replaces the memory one, and the style is embedded so
        the file carries its own cartography.
      run_sig, geometry_sig: what this run actually drew, captured
        when it was LAUNCHED, and recorded here as the dialog's new
        baseline. Both default to None, in which case the signatures
        are read from the table as it stands now -- which is right
        only for a synchronous path, where nothing can have changed
        in between. For a run that went through the worker they must
        be passed, or a setting altered during a long tiling would be
        recorded as though the map already showed it, and the next
        Generate would take the restyle fast path over geometry that
        never matched.
      outlines: whether the outlines box was ticked WHEN THIS RUN WAS
        LAUNCHED. None means read it now, which is right only for a
        caller that did not go through the worker. It is passed for
        the same reason the signatures are, and it is the one
        geometry setting the LANDING acts on rather than the tiling,
        which is what made reading it live a defect rather than a
        harmless shortcut.
      launch_state: the working state captured at launch. Its DESIGN
        half and output path go into the record this group carries,
        because the group must describe the map its own layers hold;
        the element half is re-read live. None means capture the whole
        thing now, which is right for a caller that did not go through
        the worker.

    Returns:
      None; the project is what changes. Afterwards
      ``_element_layer_ids`` maps element ids to layer ids and
      ``_last_signatures`` records what each element was seeded from,
      which is what lets the NEXT run re-seed only what changed.

    Steps, in order and why the order matters:
    1. find or create the layer-tree group;
    2. load each distinct class-source (QML file or donor layer) once;
    3. clone the previous run's renderers *before* touching any layer,
       so hand-refined symbology can be carried onto the replacements;
    4. when writing a GeoPackage, drop the old file-backed layers first
       (open layers hold the sqlite file and the rewrite can deadlock
       on the lock, notably on Windows);
    5. per tile_id: slice the GeoDataFrame, convert via
       bridge.gdf_to_layer (memory layer) and optionally
       bridge.write_gpkg_layer (file-backed), then either reattach the
       cloned renderer (assignment signature unchanged) or seed a fresh
       one; tag with the custom property that keeps outputs out of the
       region combo; register with the project but attach to our group
       ourselves (addMapLayer(..., False));
    6. refresh the outlines layer, remove the previous run's layers,
       and record ids/signatures/paths for the next regeneration.

    Layer *identities* change on every run (a documented trade-off:
    print-layout references need re-picking) but styling continuity is
    preserved via the signature check.
    """
    project = QgsProject.instance()
    # AN OUTPUT PATH NEVER DECIDES WHICH GROUP A RUN LANDS ON.
    # (Maintainer's ruling, 2026-08-27, ledger row 12.) The chooser
    # alone decides, which is what the ruling of 2026-08-25 gave it,
    # and "create new" remains the way to ask for a second map.
    #
    # WHAT WAS HERE, and why it is gone rather than narrowed. A
    # `moved_the_output` term compared this run's destination with the
    # last one's and armed a fresh group when they differed. Clearing
    # the output path therefore forked a group silently -- and under
    # live update it landed with no button press at all, from an
    # ordinary design tweak, which is how a panel fills with
    # near-identical group names. Found independently by the return
    # sweep and the live-update hunt.
    # ITS OWN REASON WAS THAT A RUN MUST NOT OVERWRITE THE LAST
    # RESULT'S FILE, and that reason is being taken away in the same
    # version: under "saving is a positive act" a run writes nothing,
    # so there is no file to overwrite and nothing left for the
    # inference to protect. A guard whose reason has gone reads as
    # protection, which is why the term is deleted with this
    # explanation rather than left standing.
    # WHAT IT COST WHILE IT STOOD is worth keeping, because it is the
    # shape of the argument rather than the argument: the term needed
    # a clause for a cleared box (recovery), a clause for a group
    # adopted but not yet written, and a clause for live update's
    # memory layers -- three narrowings in eleven days, each after a
    # measurement, each because the path was answering a question
    # about the GROUP. The chooser answers that question and can be
    # seen answering it.
    #
    # A RENAME MADE WHILE THIS RUN WAS TILING keeps the group, and is
    # the one case where finding it by its layers must NOT reuse it:
    # the user renamed the result they were looking at, which is the
    # same act as "Create as new group" made after the fact. The
    # comparison is against the name the group had when this run was
    # LAUNCHED, so a rename made earlier -- when the group is simply
    # called something else now -- is not caught by it.
    launched_as = getattr(self, "_group_name_at_launch", None)
    live_group = self._group_of_our_layers(
      QgsProject.instance().layerTreeRoot())
    renamed_mid_run = (launched_as is not None and live_group is not None
                       and live_group.name() != launched_as)
    # ...and the first landing after a change of dataset builds fresh
    # whatever the paths say: with no file in play both paths are
    # empty, same_destination answers True, and B's memory-mode map
    # would replace A's in place -- the demo journey the ruling of
    # 2026-08-21 exists for.
    # ...AND NEVER WRITE OVER A MAP MADE FROM ANOTHER DATASET. Ruling
    # 2 makes a second output group the ordinary result of a demo, and
    # ADOPTION RUNS AT CONSTRUCTION -- before the user has chosen
    # anything -- so a reopened project holding maps of two datasets
    # could adopt the wrong one and replace it at the next Generate.
    # Found by a hunt starting from the user's losses, 2026-08-25:
    # two maps became one dataset twice. Asked HERE rather than at
    # adoption because this is the moment the answer is knowable: the
    # chooser has settled and the layers carry their region stamp.
    # Output from before the stamp carries none and is left to the
    # older rules, which is what `not stamps` means below.
    # Recorded on every layer this run lands (see the stamp below) AND
    # read by the mismatch check immediately after. Defined HERE
    # because that check came first and referenced it eighteen lines
    # early: an UnboundLocalError inside the landing, swallowed, which
    # showed up as a run that quietly reused the previous group. The
    # rule this project already carries -- assert the postcondition,
    # not just the anchor -- would have caught it; a probe did.
    # ASKED OF THE LAYER THIS RUN TILED, never of the chooser as it
    # stands now. Which dataset a map came from is a fact about the
    # TILES, and the tiles were drawn from `source_layer` however the
    # chooser has moved since -- so reading it live made the answer
    # depend on where the user happened to be looking when the tiling
    # finished. Switch the region layer mid-run, which is an ordinary
    # act the race sweep already has a cell for, and A's tiles came
    # out stamped as B's: the chooser then labelled A's map with B's
    # name (ruling 1), the binding handed that group to B (ruling 2),
    # and the `theirs` check below -- whose whole job is refusing to
    # write over a map made from another dataset -- read the same
    # wrong stamp and let a B run replace it. Measured 2026-08-26 by
    # driving it rather than reading it: four of four layers of A's
    # tiles destroyed by a run on B.
    #
    # ONE ACT WAS WRITING ONE FACT TWICE, FROM TWO MOMENTS, which is
    # what made the pair legible once either was measured.
    # `_stamp_working_state` takes the record's `region` from the
    # LAUNCH snapshot, deliberately and correctly; this line took the
    # same fact live. The two now come from the same moment, so a
    # group's record and its layers cannot come to disagree about
    # whose map they are.
    #
    # AN EMPTY STRING IS THE HONEST ANSWER for a run whose region
    # layer was deleted underneath it: there is no dataset to name,
    # and unstamped output is a state the older rules already handle
    # (`not stamps` below). Stamping whatever the chooser holds
    # instead would file the map under a dataset it was never drawn
    # from, which is the defect above wearing its own workaround.
    region_now = (source_layer
                  if self._source_layer_alive(source_layer) else None)
    region_source = region_now.source() if region_now is not None else ""
    root_now = QgsProject.instance().layerTreeRoot()
    candidate = (self._group_of_our_layers(root_now)
                 or self._newest_output_group(root_now))
    theirs = False
    if candidate is not None and region_source:
      stamps = {child.layer().customProperty("weavingspace_region")
                for child in candidate.children()
                if getattr(child, "layer", lambda: None)() is not None
                and child.layer().customProperty("weavingspace_region")}
      theirs = bool(stamps) and not any(
        same_source(region_source, mark) for mark in stamps)
      if theirs and self._adopted_group_unwritten:
        # ...UNLESS THIS IS A RECOVERY, which the ruling of 2026-08-21
        # already decided and this guard, written on the 24th, did not
        # know about: "a recovery is not a switch -- reopening a
        # project whose region file has MOVED and pointing at live
        # data re-finds the same work". `_adopt_existing_group`'s own
        # contract says the same thing from the other end: a group
        # this dialog took over and has not yet written to is replaced
        # by the first Generate whatever the output box says.
        #
        # SO THE OTHER DATASET HAS TO BE REACHABLE for its map to be
        # somebody's work worth protecting. Where the stamped source
        # is gone -- moved, deleted, on a disk that is not mounted --
        # there is nothing to switch away FROM, and refusing to write
        # leaves the user with a rival group beside the map they were
        # recovering. Measured 2026-08-25: this test had been red on
        # an unpushed branch since the guard landed.
        #
        # WHAT IT DOES NOT COVER, said plainly rather than left to be
        # discovered: a project holding a map of data nobody loaded is
        # indistinguishable from a recovery, and this treats it as
        # one. That case is no longer invisible, which is what ruling 1
        # bought -- the chooser NAMES the group a run will land in, so
        # somebody can see the map they are about to replace.
        from . import compat
        theirs = any(
          compat.layer_data_is_available(other)
          for mark in stamps
          for other in project.mapLayers().values()
          if getattr(other, "source", lambda: None)() == mark)
    force_new = (self.opt_new_group.isChecked() or renamed_mid_run
                 or theirs
                 or self._new_group_chosen)
    # Spent the moment it is read: the group is this dialog's from
    # here on, so a later run has no claim on the softer treatment a
    # freshly adopted group gets. Cleared BEFORE the work below rather
    # than after, so an exception on the way cannot leave it armed.
    self._adopted_group_unwritten = False
    self._new_group_chosen = False
    group, created = self._get_or_make_group(force_new, tiled=source_layer)
    group.setName(self._group_name)

    old_ids = dict(self._element_layer_ids)
    old_outline = self._outline_layer_id
    new_ids = {}
    by_id = {a["id"]: a for a in assignments}
    tile_ids = sorted(set(gdf["tile_id"]), key=bridge.element_order)
    # WHICH ELEMENT A `layer:` CLASS SOURCE NAMES, asked of the LAYER
    # first and of this run's own record second. The layer is the
    # better answer because it survives a group adopted from a reopened
    # project, where `_element_layer_ids` may be empty while the layers
    # themselves still carry their stamps; the record is the fallback
    # for a layer that has already gone.
    owner_of_old = {lid: t for t, lid in old_ids.items()}

    def donor_for(tile_id):
      token = (by_id.get(tile_id) or {}).get("class_source") or ""
      if not token.startswith("layer:"):
        return None
      donor_layer = project.mapLayer(token[6:])
      named = (donor_layer.customProperty("weavingspace_tile_id")
               if donor_layer is not None else None)
      return str(named) if named else owner_of_old.get(token[6:])

    # DONORS ARE SEEDED BEFORE THEIR FOLLOWERS (ruling 5 of
    # 2026-08-27). Panel order is `tile_ids` and is what the group is
    # built in; this is the order the WORK is done in, and the two are
    # deliberately separate -- see `_join_in_panel_order`.
    seed_order = self._seeding_order(tile_ids, donor_for)
    warned_cardinality = []
    # {tile_id: the fills that element will paint}, gathered as the
    # renderers go on so the separability check sees the map's real
    # colours -- including any the user refined by hand
    element_fills = {}

    templates, template_errors, unreadable = {}, [], set()
    for token in {a.get("class_source") for a in assignments
                  if a.get("class_source")}:
      try:
        if token.startswith("layer:"):
          templates[token] = bridge.template_from_layer(
            project.mapLayer(token[6:]))
        else:
          templates[token] = bridge.load_categorized_template(token[5:])
      except Exception as e:
        # tracked exactly as the restyle twin tracks it, and for the
        # same keep-the-map promise; see the arm at the seeding below
        unreadable.add(token)
        template_errors.append(f"{token.split(':', 1)[1][-40:]}: {e}")

    # A run carries the settings it was launched with, which is right
    # for everything that decides the GEOMETRY: a spacing typed while
    # the tiles are being laid out belongs to the next run, not this
    # one. Hand-picked COLOURS are the exception, on both styling
    # paths. Their editors are usable while a run is in flight, and
    # the restyle path declines during one, so a colour chosen in
    # that window would be seeded from the stale snapshot and
    # silently lost the moment the run landed. The dialog's record is
    # the authority for those, so it is re-read here rather than
    # trusted from the snapshot.
    for a in assignments:
      if a.get("mode") == "Categorized" and a.get("var"):
        a["category_colours"] = self._category_colours.get(
          a["id"], {}).get(a["var"])
      elif a.get("mode") == "Graduated":
        # The graduated half of that fix, missing until 2026-08-13
        # although the rule had been written down for the
        # categorical half since the day it was made. The quant
        # editor writes positional class colours and the ramp's
        # display window into the same record through the same
        # window, so trusting the snapshot here destroyed both the
        # moment a run landed -- and stamped them ABSENT onto
        # weavingspace_quant_style, so a reopened project could not
        # bring them back either. The window rides every graduated
        # row whether or not a variable is assigned, matching what
        # _assignments builds, so seeding never has to guess.
        # Guarded by
        # test_a_class_colour_picked_during_a_run_is_not_lost.
        if a.get("var"):
          a["quant_colours"] = self._quant_colours.get(
            a["id"], {}).get(a["var"])
          # THE THIRD THING WRITTEN THROUGH THAT WINDOW, and it was
          # missing here until 2026-08-14. Pinned bounds and a copied
          # ladder are set from the same editor, while a run can be in
          # flight, and the restyle path declines during one -- so
          # without this a pin made in that window was seeded from the
          # stale snapshot, destroyed the moment the run landed, and
          # stamped ABSENT onto weavingspace_quant_style so a reopened
          # project could not bring it back either. Exactly the defect
          # the paragraph above describes, arriving a third time
          # because the rule was written as one about COLOUR. Guarded
          # by test_a_pin_set_during_a_run_is_not_lost.
          # ...and RETIRED HERE if the data has moved out from under
          # it, because this is the last moment before the value is
          # stamped onto the layer. Doing it at the notice sites alone
          # cleared the dialog's record and left the STAMP carrying
          # the dead number, so a reopen read it straight back -- the
          # acted-on-at-landing, recorded-at-launch shape again, and
          # it cost this feature a defect once already.
          retired = self._retire_an_undrawable_pin(a["var"], a)
          if retired is not None:
            self._report_quietly(retired)
          a["pinned"] = self._pinned_bounds.get(
            a["id"], {}).get(a["var"])
        a["range_bounds"] = tuple(
          self._ramp_ranges.get(a["id"], (0, 100)))

    # NOT the rest of the symbology, and the distinction is settled
    # rather than accidental. A ramp, class count, opacity or Reverse
    # changed during a run is NOT lost: it stays in the element's
    # record, the table keeps it, and the next Generate applies it.
    # With live update off the plugin deliberately does not repaint
    # on its own -- the table and the map may disagree until the user
    # asks, which is what `test_race_restyle_during_run` has asserted
    # since long before tonight. Hand-picked COLOUR is the exception
    # because it was genuinely destroyed rather than merely deferred:
    # the landing run stamped it ABSENT onto the layer, past the
    # reach of a reopen. Re-reading the rest here was tried on
    # 2026-08-13 and reverted the same night; it made the map repaint
    # unasked and put two tests in direct contradiction.

    # keep the previous run's renderers (possibly hand-refined in the
    # styling dock) before touching any layers
    old_renderers = {}
    old_layer_opacity = {}
    old_no_data_opacity = {}
    old_no_data_renderers = {}
    old_no_data_subsets = {}
    old_subsets = {}
    # ...AND THE STAMPS, which a DEFERRING element cannot rewrite for
    # itself. `_stamp_category_colours` leaves a deferring element's
    # records alone rather than clearing them, which is right on the
    # restyle path where the layer survives -- but a re-tile hands the
    # element a NEW layer, and leaving a new layer alone means the
    # pinned bounds and hand-picked colours are simply never written.
    # They travel here on exactly the terms the renderer and the
    # opacity already travel on. (2026-08-17.)
    old_stamps = {}
    for tid, lid in old_ids.items():
      old_layer = project.mapLayer(lid)
      if old_layer is not None:
        held = {name: old_layer.customProperty(name)
                for name in ("weavingspace_category_colours",
                             "weavingspace_quant_style")
                if old_layer.customProperty(name)}
        if held:
          old_stamps[tid] = held
      if old_layer is not None and old_layer.renderer() is not None:
        old_renderers[tid] = old_layer.renderer().clone()
        # opacity lives on the layer, not the renderer, so it has to
        # be carried across separately when an element is kept as-is
        old_layer_opacity[tid] = old_layer.opacity()
      # ...AND THE PAIRED LAYER'S OWN, which a user can set in Layer
      # Properties exactly as they set its element's. The element's
      # was carried across and the twin's was not, so fading an
      # element by hand and then changing the spacing snapped its
      # missing-value areas back to full strength -- the same harm
      # the spin-box half was fixed for, through the door that fix
      # did not close. Measured 2026-08-16 in pixels: 0.196 and
      # 1.000 after a re-tile, from 0.204 and 0.196 before it.
      paired_before = project.mapLayer(
        self._no_data_layer_ids.get(tid) or "")
      if paired_before is not None:
        old_no_data_opacity[tid] = paired_before.opacity()
        # ...AND ITS RENDERER AND ITS FILTER, on the same terms its
        # element gets. The paired layer sits in the layer tree like
        # any other, so a user can open Layer Properties and give it a
        # hatch, a different grey or a filter -- and every Generate
        # called setRenderer on it unconditionally, so that work
        # vanished while the identical act on the element beside it
        # survived AND was announced in the message bar. Found by two
        # hunts independently on 2026-08-16.
        # The RENDERER goes through the element's own gate
        # (maintainer's ruling the same day): when the dialog leaves
        # an element's styling alone it leaves its twin alone, and
        # when it restyles the element it restyles both. That keeps
        # the No data colour in the element's colour editor working --
        # picking one moves the style signature, so the pair is
        # rebuilt -- rather than creating a second, unguarded door
        # into the same state.
        if paired_before.renderer() is not None:
          old_no_data_renderers[tid] = paired_before.renderer().clone()
        # The FILTER is carried unconditionally, exactly as the
        # element's is, because a subset says which features to draw
        # rather than how to colour them and is nobody's styling.
        if paired_before.subsetString():
          old_no_data_subsets[tid] = paired_before.subsetString()
      # A subset string is the user's own filter, set in Layer
      # Properties or the layer panel's Filter dialogue, and it used
      # to die with the layer at every regeneration -- deliberate
      # work silently discarded, unlike the hand styling beside it,
      # which survives. Carried across on the same promise (user
      # decision, 2026-08-09). Every element that HAD one gets it
      # back, whether or not its assignment changed: a filter says
      # which features to draw, not how to colour them.
      if old_layer is not None and old_layer.subsetString():
        old_subsets[tid] = old_layer.subsetString()
    # what the LAST run's no-data layers were, so this run can drop
    # exactly those; the new ones are collected as they are built
    old_no_data = dict(self._no_data_layer_ids)
    self._no_data_layer_ids = {}

    def column_has_values(field):
      """Whether any tile ANYWHERE on this map has a value here.

      Args:
        field: the column, or None, which answers False.

      Returns:
        True when at least one tile of the whole run carries a usable
        value. Asked of `gdf`, the map entire, because the split is
        decided per element and an element cannot see past its own
        tiles -- which is exactly how an element sitting wholly on
        areas with no value came to be left unsplit and undrawn.

      Cached per run in `seen`: a design of twenty elements sharing
      four columns asks four questions, not twenty.
      """
      if not field or field not in getattr(gdf, "columns", []):
        return False
      if field not in seen:
        seen[field] = bool(gdf[field].notna().any())
      return seen[field]

    seen = {}
    # Which columns are DATA rather than identity, computed once for
    # the run: every variable any element displays. A column outside
    # this set is either the geometry or an identifier, and both stay
    # on every element.
    mapped_variables = {a["var"] for a in assignments if a.get("var")}
    # The table names this run has already used, so `element_table_name`
    # can refuse a collision. Kept per run rather than per file because
    # one run writes into one file, and the names are decided before
    # the file is touched.
    tables_this_run = {}
    # EVERY SWATCH IS RETHOUGHT, because a run changes which values an
    # element's tiles carry and the cache key cannot see that. The
    # hatching in particular is a fact about the ELEMENT'S OWN LAYER:
    # a coarser spacing can leave a class unreachable that was worn
    # before, or the reverse, and the cached icon would go on claiming
    # whichever was true of the previous map. Cheap -- an icon is
    # rebuilt only when a row asks for one.
    self._custom_swatch_cache.clear()
    # elements whose renderer is carried over rather than re-seeded;
    # _finish_run re-examines exactly these, because a dock edit made
    # mid-run rides across in that renderer with no record behind it
    self._preserved_this_run = []
    # {tile_id: (assignment, bounds, colours)} -- dock edits that
    # arrived while a run was in flight, replayed once it has landed.
    # See _adopt_dock_bounds for why the numbers are kept rather than
    # a note to look again.
    self._adoption_deferred = {}
    # elements THIS RUN actually re-seeded, as against carrying a
    # renderer across whole. A follower reads it to learn that its
    # donor moved underneath it; `_seeding_order` is what guarantees
    # the donor has already been answered by the time it is asked.
    reseeded = set()
    # rebuilt each run, so an element the design has dropped does not
    # leave its table name behind for a save to write again
    self._element_tables = {}
    for tid in seed_order:
      a = by_id.get(tid, {"id": tid, "var": None, "mode": "Single colour",
                          "ramp": "Greys", "scheme": "Quantiles", "k": 5,
                          "outline": False})
      # THE FOLLOWER READS THE DONOR'S NEW LAYER. `templates` above was
      # built from the layers this run is REPLACING, which is right for
      # a QML file and wrong for an element: seeding order puts the
      # donor first, so by the time a follower is reached its donor's
      # new layer exists and is what it must follow. Recomputed here
      # rather than in the loop's seeding branch because that branch is
      # reached down several arms, and a template read at only some of
      # them is the asymmetry this project keeps paying for.
      source_token = a.get("class_source") or ""
      if source_token.startswith("layer:"):
        donor_tid = donor_for(tid)
        fresh = (project.mapLayer(new_ids[donor_tid])
                 if donor_tid in new_ids else None)
        if fresh is not None:
          try:
            templates[source_token] = bridge.template_from_layer(fresh)
            # a donor whose OUTGOING layer could not be read -- the
            # dangling `layer:` token of ledger row 14 -- is not an
            # unreadable source once its new layer answers
            unreadable.discard(source_token)
          except Exception as e:
            unreadable.add(source_token)
            template_errors.append(
              f"{source_token.split(':', 1)[1][-40:]}: {e}")
      display = f"{tid} – {a['var']}" if a["var"] else f"{tid} (no data)"
      sub = gdf[gdf["tile_id"] == tid]
      # TRIMMED TO WHAT THIS ELEMENT DISPLAYS (ruling 6 of
      # 2026-08-25). The tiled frame carries every mapped variable on
      # every row, so each element layer used to hold all of them: a
      # colleague measured 23 elements each holding all 26 source
      # attributes, which took an 800 KB dataset to a 19 MB
      # GeoPackage, and a probe found a column deliberately named
      # `secret_code` sitting in all four tables of a map that never
      # displayed it. The file a user sends on carried attributes the
      # map never drew.
      #
      # THE IDENTIFIERS STAY. `tile_id` and `prototile_id` say which
      # element and which unit a tile belongs to -- they are what the
      # map IS rather than what it shows -- and adoption, the stale
      # table drop and anybody reading the file all expect them.
      # Measured 2026-08-25: a run's element layers carry
      # `weavingspace_fid`, `tile_id`, `prototile_id` and every mapped
      # variable, of which only the last group is trimmed.
      #
      # IT IS ONLY SAFE BECAUSE THE SOURCE COMES BACK. The colleague's
      # argument for carrying every column was that a tiling may be
      # missing data in some variables, so the full set hedges against
      # a lossy encoding. With the region recoverable by reference,
      # switching an element's variable RE-TILES from the source --
      # the set of mapped variables is a GEOMETRY change and always
      # has been -- rather than reading a column carried along just in
      # case. Rulings 5 and 6 close together or not at all.
      if mapped_variables:
        sub = sub[[column for column in sub.columns
                   if column not in mapped_variables
                   or column == a.get("var")]]
      # ROWS A GRADUATED RENDERER CANNOT PLACE COME OUT HERE.
      # QgsGraduatedSymbolRenderer has no class for a missing value --
      # no default, no-data, else or fallback symbol anywhere in its
      # public API on QGIS 4.0.3 -- so symbolForFeature answers None
      # and the tile is simply not painted. On a map whose whole
      # subject is areas, an unpainted area is a HOLE, and a hole
      # reads as "nothing is here" rather than "this is not known".
      # Reported from the field 2026-08-16 with an area null in every
      # column, so it appeared under two different tilings and
      # whichever variable was mapped.
      #
      # Only the GRADUATED path needs it. A categorized renderer has
      # `addCategory` and therefore its own catch-all, which this
      # plugin already builds and already lets a user colour.
      #
      # ...AND A DEFERRING ELEMENT, which reads as neither. Asked the
      # same question in the same words as `_needs_a_no_data_split`,
      # because these two decide one thing between them and answering
      # it twice is how they came to disagree: the predicate is in the
      # geometry signature and this line does the splitting, so a run
      # that promised a twin built none. Two doors, one state.
      field_here = a["var"] if self._needs_a_no_data_split(a) else None
      # THE LIMITS ARE RE-READ HERE, not taken from the snapshot this
      # run was launched with. Everything the colour editor writes is
      # re-read at the landing -- the rule that has now been got wrong
      # three times, over category colours, over class colours and
      # over pins -- and a floor set while a run was in flight is the
      # same case wearing new clothes. `_assignments` is asked afresh
      # above, so `a` already carries the live record.
      limits = (a.get("pinned") or {}) if field_here else {}
      drawable, absent = bridge.split_out_the_no_data(
        sub, field_here, column_has_values(field_here),
        limits.get("floor"), limits.get("ceiling"))
      mem = bridge.gdf_to_layer(drawable, display)
      # DECIDED FOR EVERY ELEMENT, not only the ones being written to
      # a file. The paired no-data layer's name is built from this
      # one, the stale-table drop compares against it, and memory-mode
      # output that is later saved has to agree with what a file run
      # would have produced -- so working it out inside `if path`
      # would give two runs of one design two different answers.
      table_name = bridge.element_table_name(tid, a.get("var"),
                                             tables_this_run.values())
      tables_this_run[tid] = table_name
      # NOTHING IS WRITTEN HERE. Until 2026-08-27 an element was
      # written into the GeoPackage at this point whenever an output
      # path was set, and the layer that joined the project read from
      # the file. The maintainer ruled that saving is a positive act:
      # Generate DRAWS, and `_save_the_map` writes -- so every element
      # arrives as a memory layer and Save repoints it at the file it
      # is written into.
      out = mem

      # styling: keep the previous layer's (possibly hand-refined)
      # renderer when this element's assignment didn't change
      signature = self._signature(a)
      previous = self._last_signatures.get(tid)
      unchanged = (tid in old_renderers and previous == signature)
      # A FOLLOWER MOVES WHEN ITS DONOR MOVES, and its own row need not
      # have moved at all: same variable, same style, same ramp, so the
      # signature matches and the renderer would be carried across
      # whole. That is the one-run lag from the other side, and
      # ordering the seeding is worth nothing while it stands --
      # the follower would be reached after the donor and then not
      # re-seeded at all.
      # ITS CLASS-SOURCE STAMP CANNOT ANSWER THIS, which is why the
      # question is asked here rather than left to the signature. The
      # stamp is read when the run is LAUNCHED, off the donor's layer
      # as it stood BEFORE this run re-seeded it, so a donor moved by
      # THIS run is invisible to it. A donor moved by anything else --
      # a dock edit, a ramp picked and then a spacing change -- does
      # move the stamp, and that route was already covered.
      if unchanged and donor_for(tid) in reseeded:
        unchanged = False
      # A DEFERRING element keeps the renderer somebody built in
      # QGIS's styling panel even though its assignment moved, because
      # the plugin has stopped styling it -- that is what deferring
      # means, and re-seeding here would destroy the work at the next
      # spacing change. Settled 2026-08-15.
      #
      # ONE THING BREAKS IT: the element's VARIABLE changing. A
      # renderer keyed to `landcover` re-attached to an element now
      # drawing `v3` puts every tile outside every class and paints
      # nothing -- the empty-map failure the text-field guard already
      # exists to prevent, arriving by a new road. So deferral follows
      # the same bargain hand styling has always had: it survives
      # unless THAT ELEMENT'S assignment changed in the one way that
      # makes it meaningless. `previous[0]` is the variable, because
      # _signature puts it first.
      # THE ROW'S OWN STATEMENT gates both of these, not the layer's
      # renderer alone. Picking a plugin style is how a user takes an
      # element BACK, and it must replace the dock's renderer at once
      # (settled 2026-08-15) -- but the layer still holds that
      # renderer at the moment of the pick, so a test on the layer
      # alone can never be false and the element could never be
      # reclaimed. Measured while building this: choosing Categorized
      # left the rule-based renderer in place for good.
      carried_while_deferring = (
        not unchanged and tid in old_renderers and previous is not None
        and a.get("mode_raw") == self.DEFERRING
        and bridge.expressible_style(old_renderers[tid]) is None
        and previous[0] == a.get("var"))
      if (not unchanged and tid in old_renderers and previous is not None
          and bridge.expressible_style(old_renderers[tid]) is None
          and previous[0] != a.get("var")):
        # ...and the loss is REPORTED, never silent, exactly as every
        # other loss on this path is
        self._report_quietly(
          f"Element '{tid}' was styled in QGIS, and changing its "
          f"variable means those classes no longer describe it, so it "
          f"is drawn by the plugin again.")
      # RECLAIMED: the layer holds something no row can name, and the
      # row now names a style. That is a user taking the element back,
      # and it must re-seed WHATEVER the signature says -- because
      # picking back the same style the element had before it was
      # deferred restores the old signature EXACTLY, so `unchanged`
      # goes true and the branch below preserves the very renderer
      # they are trying to replace. Measured while building this: the
      # row read Categorized, the map stayed rule-based through two
      # Generates, and the controls stayed inert because the element
      # was still, in fact, deferring.
      # ASKED OF THE LIVE ROW, not of the launch snapshot, and the
      # difference is a user's work. `a` is the assignment this run
      # was LAUNCHED with; deferral can begin while it runs -- pasting
      # a rule-based style onto an element is one keystroke -- and
      # `_on_layer_style_edited` returns early during a run, refreshing
      # the rows but never the snapshot. So the snapshot still named a
      # style, this read that as the user TAKING THE ELEMENT BACK, and
      # the landing re-seeded over the paste. Measured 2026-08-17: a
      # style pasted 250 ms into a run was gone when it landed, the
      # only notice being the tile count, while the same paste a
      # second either side survived and was honoured for good.
      #
      # An earlier attempt at this fixed the ROWS and not the answer
      # read here, and passed every neighbouring test while the hunt's
      # own reproduction still failed -- which is the argument for
      # running the reproduction rather than the neighbours.
      live_mode = a.get("mode_raw")
      live_row = self._assignment_for(tid)
      if live_row is not None:
        live_mode = live_row.get("mode_raw")
      reclaimed = (tid in old_renderers
                   and live_mode != self.DEFERRING
                   and bridge.expressible_style(old_renderers[tid]) is None)
      # THE GATE, named because its TWIN needs the same answer. This
      # is what tells "kept because the user set it" from "kept
      # because it was there", and the paired layer's copy of the
      # opacity carry-over was written without it: `old_no_data_
      # opacity` is filled unconditionally from whatever the previous
      # paired layer wore, so "hand-set in QGIS" was inferred rather
      # than recorded and was true of every paired layer that had ever
      # existed. Fading an element to 40 and changing the spacing in
      # one round therefore left its missing-value areas at full
      # strength, in the project AND in the exported GeoPackage, with
      # the spinner reading 40. Measured 2026-08-16 by opening the
      # tables cold in a cleared project: tiles_a 0.4, tiles_a_no_data
      # 1.0. The regression arrived inside the fix for the opposite
      # fault hours earlier, which is the shape worth remembering --
      # when a fix teaches a path to CARRY a value across, the gate is
      # the part that has to travel with it.
      kept_by_hand = ((unchanged or carried_while_deferring)
                      and not reclaimed)
      if kept_by_hand:
        out.setRenderer(old_renderers[tid])
        self._preserved_this_run.append(tid)
        # opacity travels with the renderer: an element the dialog has
        # not changed keeps whatever opacity its layer had, which may
        # be one the user set by hand in Layer Properties. Same promise
        # the renderer gets, and the reason opacity is a layer property
        # rather than something baked into the colours
        # ...EXCEPT WHERE THE ELEMENT IS KEPT BECAUSE IT IS DEFERRING,
        # where the dialog is still the authority for opacity. The
        # Opacity cell stays LIVE while an element is deferring --
        # `RENDERER_COLUMNS` leaves column 6 out deliberately, and the
        # restyle twin says so in as many words: "it is the one
        # control that stays live while deferring". Carrying the old
        # layer's value here overrode the number the user had just
        # set, and the table went on displaying it.
        #
        # Measured 2026-08-17: an element restyled in QGIS and faded
        # to 30 per cent came back from a re-tile at 1.0 with the
        # table still reading 30, while a control element that was not
        # deferring came back at 0.3. The carry is right for an
        # element the dialog has NOT changed, which is what its
        # comment says; deferral is the case where the dialog has.
        if carried_while_deferring:
          out.setOpacity(max(0, min(100, a.get("opacity", 100))) / 100.0)
        elif old_layer_opacity.get(tid) is not None:
          out.setOpacity(old_layer_opacity[tid])
      else:
        if a["mode"] == "Categorized" and a["var"]:
          idx = mem.fields().indexOf(a["var"])
          if idx >= 0 and len(mem.uniqueValues(idx)) > 60:
            warned_cardinality.append(f"{tid} ({a['var']})")
        # AN UNREADABLE CLASS SOURCE KEEPS THE COLOURS THE MAP WAS
        # WEARING, at the landing exactly as on the restyle path --
        # whose arm says why: everything else about the element is
        # still honoured, because refusing that too would turn one
        # unreadable file into a row whose controls do nothing. The
        # landing never had the arm, so the keep-the-map promise
        # rested on the run signature saying "unchanged": add any
        # second control to the act (an opacity with the spacing) and
        # sub-second timing decided whether the colours survived --
        # two runs less than a second apart gave two different maps.
        # Found by the class-source hunt, 2026-08-26. ONLY the
        # seeding is conditional: the stamps, the twin and every other
        # per-element step below run exactly as for any element.
        if a.get("class_source") in unreadable \
            and self._a_kept_renderer_still_draws_this(
              old_renderers.get(tid), a):
          # What this keeps is the plugin's own previous seeding held
          # over an unreadable file -- nobody's decision -- and no
          # adoption may record it as a person's picks. That is held
          # where every adoption route passes: the categorical walk
          # attributes each colour against `_painted_categories`
          # (2026-08-26), so the carry's colours -- which the plugin
          # painted -- are declined on every route, and a person's
          # dock edit on the kept renderer still differs and adopts.
          out.setRenderer(old_renderers[tid])
          self._preserved_this_run.append(tid)
        else:
          # THE FILE ANSWERS AGAIN, so anything this element was
          # holding on its behalf goes back BEFORE the seeding reads
          # the record -- hand-picked colours outrank a template by
          # design, so releasing afterwards would leave the seeding to
          # paint the colours the file had before it went away and the
          # restored file would look ignored.
          self._release_colours_kept_for_an_unreadable_source(a)
          # the same values as the restyle path hands over, so an
          # element wears the same breaks whichever path drew it
          bridge.seed_renderer(
            out, a, templates.get(a.get("class_source")),
            self._classification_values(a.get("var")) if a.get("var")
            else None)
          # this element MOVED, so anything following its layer must be
          # re-seeded too rather than carried across; the seeding order
          # puts those followers after it
          reseeded.add(tid)
        # the landing's half of the same baseline; see the twin in
        # `_restyle_only`, and note that the two are DELIBERATELY
        # separate calls rather than one shared helper wrapping
        # seed_renderer, because the two paths differ in what they do
        # to a DEFERRING element and a wrapper would hide that
        self._remember_painted_ladder(out, a["id"])
        # re-seeded, so the dialog is the authority for this element's
        # whole appearance this run, opacity included
        out.setOpacity(max(0, min(100, a.get("opacity", 100))) / 100.0)
      # AN ELEMENT WHOSE CLASS SOURCE CANNOT BE READ OWNS WHAT IT
      # DRAWS, and this is asked AFTER the renderer is settled rather
      # than inside the arm that keeps one, because TWO routes reach a
      # kept renderer here: the unreadable-source arm, and the older
      # promise that an element whose assignment has not changed keeps
      # its styling. The first draft asked inside the arm alone, and
      # the ordinary journey -- draw a map from a scheme file, move
      # the file, change the spacing -- takes the other route, so it
      # recorded nothing at all. The question the state can answer at
      # any moment is whether this element's source is readable, which
      # is what is asked here. (Maintainer's ruling, 2026-08-26.)
      if a.get("class_source") in unreadable:
        self._own_the_colours_of_an_unreadable_source(out, a)
      element_fills[tid] = bridge.renderer_fill_colours(out)
      out.setCustomProperty("weavingspace_output", True)
      # Hand-picked category colours travel with the layer, so a saved
      # project reopened after QGIS restarts still knows them and the
      # next Generate keeps them. The dialog's own dict lives only as
      # long as the session; the .qgz outlives it.
      self._stamp_category_colours(out, a)
      # A DEFERRING ELEMENT'S STAMPS ARE PUT BACK, because the call
      # above deliberately declines to write OR clear them and this
      # layer is new. Without it a re-tile loses the pinned bounds and
      # hand-picked colours of exactly the elements whose symbology
      # the user has taken into their own hands -- measured 2026-08-17
      # on both routes, with a control element beside it keeping both.
      #
      # AFTER the stamp call and BEFORE the GeoPackage write, which is
      # the order the whole block already depends on: QGIS stores a
      # layer's custom properties inside the style it saves, so a
      # stamp restored after the embed would reach the project and not
      # the file that leaves.
      if bridge.expressible_style(out.renderer()) is None:
        for name, value in (old_stamps.get(tid) or {}).items():
          out.setCustomProperty(name, value)
      # the element this layer carries, so a dialog opened later in
      # the session can adopt the group instead of starting a rival
      # one (see _adopt_existing_group)
      out.setCustomProperty("weavingspace_tile_id", tid)
      # ...AND WHICH DATASET MADE IT. Until 2026-08-25 nothing on a
      # landed layer said, which was harmless while a session held one
      # output group and became a real loss the moment ruling 2 made a
      # SECOND group the ordinary case: adoption takes the newest
      # group, so reopening a project with two maps and choosing the
      # FIRST dataset adopted the SECOND dataset's group and replaced
      # its map. Found by a hunt starting from the user's losses.
      # The SOURCE rather than the layer id, because an id is a
      # session's word for a layer and a source survives the file
      # being loaded again tomorrow.
      if region_source:
        out.setCustomProperty("weavingspace_region", region_source)
      # The style goes into the GeoPackage LAST, and the order is the
      # whole point. QGIS stores a layer's custom properties inside
      # the style it saves, so embedding before the stamps above wrote
      # a style that named none of them -- and the .gpkg is the file
      # that LEAVES. Opened cold, its layers came back unstamped, so
      # the plugin did not recognise its own output and OFFERED IT AS
      # A REGION LAYER, which the settled rules say must never happen:
      # tile the tiles and the next map is drawn on the last one.
      # `_restyle_only` had the order right; this path did not.
      # Measured 2026-08-13. Guarded by
      # test_an_exported_geopackage_is_still_recognised_as_our_own.
      project.addMapLayer(out, False)
      # ...at its ELEMENT'S place in the panel, which is no longer
      # where the loop happens to have reached: see `_seeding_order`
      self._join_in_panel_order(group, out, tid)
      if absent is not None and len(absent):
        self._add_no_data_layer(
          a, tid, absent, group, project, None, table_name,
          # ...through the SAME gate its element just went through.
          # Outside it, a value the dialog itself wrote last run reads
          # as a hand-set one and outranks the spin box the user just
          # moved.
          old_no_data_opacity.get(tid) if kept_by_hand else None,
          old_no_data_renderers.get(tid) if kept_by_hand else None,
          # the filter is not styling and is not gated, matching the
          # element's own subset a few lines below
          old_no_data_subsets.get(tid),
          # ...and the same provenance its element was stamped with a
          # few lines above, passed rather than copied afterwards
          # because the twin's style goes into the GeoPackage inside
          # this call, and a stamp written after it would reach the
          # project and never the file.
          region_source)
      # the user's own filter, back on the fresh layer. Applied AFTER
      # the renderer, because a subset changes what a classifier
      # would see and the styling above belongs to the whole element;
      # a provider that refuses the clause (a GeoPackage column the
      # memory layer had, say) leaves the element unfiltered rather
      # than unpainted.
      if tid in old_subsets:
        if not out.setSubsetString(old_subsets[tid]):
          self._report_quietly(
            f"The filter you had set on element '{tid}' could not be "
            f"applied to the new layer, so it now draws everything.")
      new_ids[tid] = out.id()
      # WHAT EACH ELEMENT'S TABLE WOULD BE CALLED, decided here even
      # though nothing is written here: `_save_the_map` must not
      # re-derive it, or two saves of one map could disagree about a
      # name and leave the earlier one behind as an orphan.
      self._element_tables[tid] = table_name
      self._last_signatures[tid] = signature
      self._watch_element_layer(out, tid)


    # map unit outlines (kept on top of the group, project-only)
    if old_outline and project.mapLayer(old_outline) is not None:
      project.removeMapLayer(old_outline)
      self._outline_layer_id = None
    # THE BOX AS IT WAS WHEN THE RUN WAS LAUNCHED, not as it stands
    # now. This read the live checkbox while recording the signature
    # captured at launch, and `opt_outlines` is the only geometry
    # term the landing acts on rather than baking into the tiling. So
    # toggling it MID-RUN cancelled its own signature difference: the
    # map already matched the new box, the signature no longer moved
    # when the user put the box back, and every later Generate went
    # down the restyle path, which can neither make nor unmake an
    # outlines layer. The box and the map then disagreed for good --
    # ticking it drew nothing and said nothing, unticking it left the
    # outlines drawn over the map. Present since 0.23.0; measured
    # 2026-08-16 by a hunt reading the layer tree.
    #
    # The general form: WHEN A RUN RECORDS A SNAPSHOT SIGNATURE,
    # every setting the landing still reads from its widget is a
    # place the two can disagree. The pair is the fault, not either
    # line.
    if (self.opt_outlines.isChecked() if outlines is None else outlines):
      outline_layer = bridge.region_outline_layer(source_layer)
      outline_layer.setCustomProperty("weavingspace_output", True)
      outline_layer.setCustomProperty("weavingspace_outline", True)
      project.addMapLayer(outline_layer, False)
      group.insertLayer(0, outline_layer)
      self._outline_layer_id = outline_layer.id()

    # AN ELEMENT THAT TAKES ITS CLASSES FROM ANOTHER ELEMENT'S LAYER
    # IS RE-POINTED HERE, BEFORE THAT LAYER IS DESTROYED. The choice
    # is stored as `layer:<layer id>`, and a re-tile gives every
    # element a NEW layer with a new id -- so one Generate after the
    # choice was made the token named an object that no longer
    # exists. The donor then read as an unreadable source, the
    # dependent kept the colours it already had under the
    # keep-the-map promise, and the two elements went on drawing one
    # column in two sets of colours for good: exactly the harm the
    # control exists to prevent, arriving as a dangling reference
    # rather than as a disagreement. Measured 2026-08-27 -- following
    # WORKS on arrival and the id stops resolving at the very next
    # run.
    # HEALED RATHER THAN RESOLVED AT EVERY READER, because a token
    # mended here is right in the row, in the group's record, in the
    # project and in the GeoPackage, where a reader-side fallback
    # would leave four stores holding a reference to nothing.
    # drop the previous run's element layers
    for tid, lid in old_ids.items():
      if project.mapLayer(lid) is not None:
        project.removeMapLayer(lid)
    # ...and the no-data layers that belonged to them. Keyed by
    # element, and removed by the SAME rule, because a paired layer
    # that outlives its element is a second map of stale values
    # sitting under the live one -- the failure the stale-table drop
    # already describes for the GeoPackage, in the layer tree.
    for tid, lid in old_no_data.items():
      if project.mapLayer(lid) is not None:
        project.removeMapLayer(lid)
    for tid in list(self._last_signatures):
      if tid not in new_ids:
        del self._last_signatures[tid]
    self._element_layer_ids = new_ids
    self._repoint_donors(old_ids, new_ids)
    # AFTER the ids are adopted, not during the loop that builds them:
    # the question "is this element deferring" is asked of the layer
    # the dialog currently points at, and until this line that is the
    # PREVIOUS run's layer. Asked once here rather than once per
    # element, which is also what it costs.
    self._refresh_deferring_rows()
    # THE STALE-TABLE DROP MOVED TO SAVE with everything else that
    # touches the file (ruling of 2026-08-27). It is
    # `_drop_tables_this_map_no_longer_has`, and it runs against the
    # tables that save has just written rather than against the ones a
    # run happened to produce.
    # `_last_path` is where this map was last SAVED, so only a save
    # may move it. A run that draws changes nothing about the file.
    # A LANDING IS WHAT MAKES A DATASET THIS SESSION'S WORK: from here
    # a change of region layer is a change of dataset, with everything
    # _begin_new_dataset does. Before it, a switch is a first choice.
    self._landed_this_session = True
    # ...AND WHAT THE DATA LOOKED LIKE WHEN IT WAS DRAWN, so a Save
    # can tell whether the region has moved since. A Save writes the
    # map as it stands and embeds the source as it stands, and those
    # are two different moments the instant somebody edits their layer
    # after generating: the tiles hold the old numbers, the embedded
    # copy holds the new ones, and nothing said so.
    # IT IS KEYED BY THE DATASET IT IS ABOUT, and that is the whole of
    # what makes it answerable later. The first version was a single
    # session-wide slot, compared at Save against whatever the region
    # chooser held then -- a fact about ONE map kept where a session
    # holds several. Draw two datasets, go back to the first through
    # the group chooser, and the two stores described different places:
    # the notice fired on a map whose data nobody had touched, telling
    # somebody their file disagreed with itself when it did not.
    # Measured 2026-08-28 by the `repairs4` hunt, reproduced here by a
    # counterfactual arm, and the first repair for it was worse than
    # the defect -- carrying the layer id ALONGSIDE one reading made
    # the notice quiet on a map whose data really had moved, trading a
    # false alarm for a missed one. A map is not told about by the last
    # landing anywhere in the session; it is told about by its own
    # dataset's reading, so that is what is kept.
    # The reading is taken from the layer this run TILED rather than
    # from the chooser, which is the rule `weavingspace_region` already
    # follows a few lines below, and for the same reason.
    if source_layer is not None:
      self._fingerprint_when_drawn[source_layer.id()] = (
        self._a_reading_of_the_data(source_layer))
    # what this run DREW, not what the table says now (see the note
    # where these are captured, in _generate)
    self._last_run_sig = (run_sig if run_sig is not None
                          else self._run_signature())
    self._last_geometry_sig = (geometry_sig if geometry_sig is not None
                               else self._geometry_signature())
    self._update_layer_exclusions()
    # THE GROUP TAKES THE WORKING STATE WITH IT (ruling 4 of
    # 2026-08-25). From here the group is the unit of work: choosing it
    # again restores this design and this symbology rather than the
    # dialog inferring them from three disagreeing scopes.
    #
    # The launch snapshot decides the DESIGN half and the live table
    # the ELEMENT half; the reasoning for that split is at
    # `_stamp_working_state`, beside the code that does it.
    self._stamp_working_state(group, launch_state)
    # THE FILE'S RECORD IS WRITTEN BY SAVE, in one act with the tables
    # and the styles it describes (ruling of 2026-08-27). A run that
    # writes nothing has nothing to record, and a record written apart
    # from the tables is how a file came to disagree with itself.
    # ...and the chooser learns about a group this run may have just
    # made. Rebuilt rather than appended to, so a group the run
    # REPLACED, or one the user deleted while it ran, leaves the list
    # in the same pass.
    self._refresh_group_combo()

    # Are any two ELEMENTS' colours too close for a reader to
    # separate? Asked of the finished renderers, under ordinary vision
    # and the two red-green deficiencies. The plugin does not change
    # anyone's ramps on the strength of it; which colours to use is
    # the cartographer's decision, and this only makes the cost of a
    # choice visible while it can still be changed.
    #
    # Off unless asked for. It is a second opinion on a cartographic
    # choice rather than a fault, and while somebody is still trying
    # ramps it has nothing useful to say -- it would fire on almost
    # every intermediate state, which is how a warning becomes
    # something people learn to ignore. The whole check is skipped
    # rather than computed and withheld, so an unchecked box costs
    # nothing at all.
    colour_clash = self._legibility_note(
      {tid: fills for tid, fills in element_fills.items() if fills},
      assignments)
    # Stashed rather than reported here. This runs inside
    # _on_generated, whose finally clears live_note -- so a notice
    # pushed now is wiped a moment later, which is exactly what
    # happened the first time, and is why the coverage notice waits
    # too. The done callback sends it once the dust has settled.
    self._pending_colour_note = colour_clash

    if self.iface is not None:
      # WHAT THE RUN DID, and no more. Until 2026-08-27 this added
      # ", saved to <path>" whenever a path was set, which was true
      # then and is false now: a run draws and the Save button
      # writes. A success notice claiming a file that was never
      # written is the worst of the three ways to be wrong here, and
      # the test that stages an unwritable directory is what caught
      # it. Nothing replaces the clause: the tab, its button and the
      # help say where saving lives, and a per-run reminder is how a
      # notice becomes something people stop reading.
      note = f"'{self._group_name}': {len(gdf)} tiles across " \
             f"{len(tile_ids)} element layers"
      self.iface.messageBar().pushSuccess("WeavingSpace", note)
      # colour_clash is NOT pushed here: it rides _pending_colour_note
      # and the done callback sends it once the dust settles. Pushing
      # it here as well delivered every legibility warning twice to a
      # real message bar -- the stash was added for the note-line wipe
      # and the immediate push was never taken out.
      if warned_cardinality:
        self.iface.messageBar().pushWarning(
          "WeavingSpace",
          "Categorized styling produced a very large number of classes "
          "for: " + ", ".join(warned_cardinality)
          + ". Is that field really categorical?")
      if template_errors:
        self.iface.messageBar().pushWarning(
          "WeavingSpace",
          "Some class style files could not be used ("
          + "; ".join(template_errors)
          + "); automatic colours were applied instead.")
