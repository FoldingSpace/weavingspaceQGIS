"""Drive a session's ORDINARY acts and read every store that holds the answer.

WHY THIS EXISTS, and why it is a committed tool rather than a probe.
This project's defects are not evenly distributed over shapes: most of
the ledger of 2026-08-26 is ONE FACT HELD IN SEVERAL STORES, MENDED IN
ONE. A shape that recurs that reliably can be ENUMERATED rather than
hunted, and enumeration is where the economics invert -- one build, no
verification queue, a reproduction attached to every failure, and it
goes on catching the next instance for nothing. The argument, the
first outing's cost and its findings are in docs/process/HUNT-RECORD.md
under "WHAT TO RUN INSTEAD OF A HUNT, AND WHEN"; CLAUDE.md carries the
standing rule that this is PROPOSED BESIDE any round of hunts.

The first outing was built on 2026-08-26, ran in about seven minutes,
found three defects in ground sixteen hunts had finished reading an
hour earlier -- including the plainest of the lot, that opening a
fresh plugin dialog onto the same project lost every hand-chosen
variable, style, ramp and class count -- and was then left in session
scratch, where it is gone. That is the failure HUNT-RECORD.md warns
about at its own foot. This is the same instrument, rebuilt to be run
again.

ONE ORACLE, MANY ACTS. A session is a sequence of acts, of three kinds
this project has always tested separately:

  CONTROL ACTS       a ramp, a class count, a spacing, a variable, an
                     opacity -- anything in the dialog;
  QGIS-SIDE ACTS     a class recoloured in the styling dock, a group
                     renamed in the layers panel;
  BOUNDARY CROSSINGS a fresh plugin dialog onto the same project,
                     saving a project and reopening it, saving the
                     GeoPackage, choosing a group, switching dataset
                     and returning.

All three are judged by the same three invariants, none of which needs
an oracle -- there is no "right answer" to be written down anywhere,
only stores that must not contradict each other:

  AGREEMENT   every store holding a fact agrees about it: the row a
              person reads, the renderer the map draws, the group's
              own record, and the record in the file a colleague
              opens;
  COLLATERAL  an act about element X leaves every OTHER element's row
              and ladder exactly as it was;
  RETURN      doing a thing and undoing it comes back to where it
              started.

ONE FLAG SEPARATES THE KINDS and it is what makes a single harness
honest. A CONTROL act MUST CHANGE SOMETHING -- an act that changed
nothing passes all three invariants while proving nothing, which is
this project's standing trap. A BOUNDARY CROSSING MUST CHANGE NOTHING:
closing a window is not an edit, and neither is saving a file.

USAGE. It needs QGIS's own Python and QGIS's own prefix, which is what
tools/hunt_probe.py discovers (this project had that prefix wrong for
months and ran with no colour ramps at all, so DO NOT hand-roll the
environment):

    python3 tools/hunt_probe.py --prepare --name sweep
    python3 tools/hunt_probe.py --run tools/consistency_sweep.py

    tools/consistency_sweep.py --list        # the acts, without running
    tools/consistency_sweep.py --act reopen  # one act by name fragment
    tools/consistency_sweep.py --seed 7      # reproduce a run exactly

WHAT MAKES ITS ANSWERS BELIEVABLE, since ten of the first outing's
fourteen failures were its own:

  * THE PREMISE IS ASSERTED EVERY TIME. Each case checks that its
    fixture is staged off the plugin's own defaults, that every store
    answered with something, and that the act's control really moved.
    The first outing reported the map ignoring a data edit until the
    probe was made to check that the twelve values it multiplied by
    ten were not all zero, which they were.
  * WHAT WAS COMPARED IS COUNTED AND REPORTED. A sweep that compared
    nothing is the same green as a sweep that found nothing.
  * IT READS WHAT THE MAP DRAWS. The map store walks the LAYER TREE
    for layers carrying `weavingspace_tile_id`, not the dialog's own
    record of them, so a dialog that has lost its layers is measured
    rather than believed. QGIS list getters hand back copies whose
    contents are freed, so `ranges()` is bound to a name before it is
    subscripted -- unbound, that has segfaulted QGIS here once and
    answered a plausible wrong `#000000` once.
  * THE FILE IS READ AS A FILE. Tables, the working-state record and
    the embedded styles come back through OGR and sqlite with every
    handle released, never through a layer this tool keeps open: an
    open handle changes what the next reading sees, and a value just
    written can be sitting in sqlite's write-ahead log beside the file
    rather than in it.
  * CONTROLS ARE DRIVEN THE WAY A USER DRIVES THEM. The ramp and style
    combos record from `activated`, which only a click emits; a bare
    `setCurrentText` leaves the next rebuild free to revert the choice.
  * IT WAITS ON THE EVENT. `_settle` from the suite is the model and
    is what this uses: no task in flight, no live timer, no preview
    timer. Never a number of seconds.
  * THE PROJECT IS EMPTIED BETWEEN CASES. Everything shares one
    QgsProject singleton, and a case that leaves layers behind means
    the next one measures this tool's rubbish.

AND IT COUNTS ITS OWN FAULTS SEPARATELY. A case that cannot stage
itself is reported as a HARNESS fault, never as a finding: a sweep
whose failures are mostly its own is one nobody acts on.
"""
import argparse
import json
import os
import random
import sys
import time
import traceback

# THE TREE UNDER TEST IS THE TREE THIS FILE SITS IN. `hunt_probe.py`
# runs a probe with the frozen copy as the working directory, and the
# ordinary invocation there is `--run tools/consistency_sweep.py`, so
# the file being executed is the frozen copy's own. Deriving the root
# from __file__ rather than from the cwd means a copy of this tool run
# from anywhere still imports the package that sits beside it, which
# is the fault a sibling hunt's stray sys.path insert would otherwise
# produce: probing one tree while importing another.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))


# --------------------------------------------------------------------
# THE ACTS, AS DATA
#
# A tenth act is a ROW here, not a function: the drivers below are
# parameterised, so an act names one of them and the argument it takes.
# That is deliberate and is what the first outing lacked -- its acts
# were nine near-identical functions, and the tenth was not written
# because writing it meant writing a tenth function.
#
# Each row is:
#   name     what the report calls it, in a user's words
#   kind     "control", "qgis" or "boundary"; the kind decides the
#            change flag, which is the one thing separating them
#   driver   a key of DRIVERS
#   argument what that driver takes, as a dict
#   subject  the element this act is ABOUT, for COLLATERAL, or None
#            where the act is about the whole design
#   returns  whether the act has an inverse, for RETURN. Every setter
#            driver hands back the argument that undoes it, so a row
#            never has to name the old value -- which would go stale
#            the moment the fixture changed.
# --------------------------------------------------------------------
ACTS = (
  # CONTROL ACTS. Each must change something.
  ("a colour ramp chosen for element a",
   "control", "ramp", {"element": "a", "value": "YlGn"}, "a", True),
  ("the class count moved on element a",
   "control", "classes", {"element": "a", "value": 8}, "a", True),
  ("element c pointed at another variable",
   "control", "variable", {"element": "c", "value": "v2"}, "c", True),
  ("a style chosen by hand for element a",
   "control", "style", {"element": "a", "value": "Quant: Equal intervals"},
   "a", True),
  ("element a made half transparent",
   "control", "opacity", {"element": "a", "value": 40}, "a", True),
  ("the ramp reversed on element a",
   "control", "reverse", {"element": "a", "value": True}, "a", True),
  ("the spacing changed",
   "control", "spacing", {"value": 420.0}, None, True),

  # QGIS-SIDE ACTS. The user works in QGIS rather than in the dialog;
  # these must change something too, and what they change must survive
  # the Generate that follows (the "preserve, do not repaint" ruling).
  ("a class recoloured in the styling dock",
   "qgis", "dock_recolour", {"element": "a", "value": "#ff00aa"}, "a", False),
  ("the output group renamed in the layers panel",
   "qgis", "rename_group", {"value": "my own map"}, None, True),

  # BOUNDARY CROSSINGS. Each must change NOTHING.
  ("a fresh plugin dialog opened onto the same project",
   "boundary", "reopen_plugin", {}, None, False),
  ("the project saved and reopened",
   "boundary", "reopen_project", {}, None, False),
  ("the map saved to its GeoPackage",
   "boundary", "save_gpkg", {}, None, False),
  ("the group chosen in the group chooser",
   "boundary", "choose_group", {}, None, False),
  ("the dataset switched away and back",
   "boundary", "switch_dataset_and_back", {}, None, False),
)


# The facts a store can hold about one element. Kept short on purpose:
# every one of them is something a user can SEE (in the table, on the
# map, or on opening the file elsewhere), so a disagreement about any
# of them is a report somebody could write.
FACTS = ("variable", "mode", "scheme", "classes", "ramp", "opacity")

# Facts that are NOT compared between stores because only one store
# holds them, and are compared between MOMENTS -- which is what
# COLLATERAL and RETURN and the boundary's change flag ask. The
# ladder is here on the brief's own wording: an act about element X
# leaves every other element's row and LADDER exactly as it was, and
# a ladder is its bounds as much as its colours. Leaving the bounds
# out cost this sweep a false clean on its first run: choosing Equal
# intervals over Quantiles moves no colour, no count and no mode, so
# with colours alone the act "changed nothing".
MOMENT_FACTS = ("_colours", "_bounds", "_tiles")

# The four stores, in the order a report should name them.
STORES = ("row", "map", "group", "file")


class Absent:
  """A store that structurally cannot hold a fact, as against holding None.

  The difference is the whole of the agreement oracle's honesty. A row
  on "Single colour" has no variable to disagree ABOUT, so it must be
  skipped; a row that says "v1" while the map draws "v2" is two stores
  answering, and that is a finding. Using None for both would make
  every lost fact look like a fact nobody holds.
  """
  def __repr__(self):
    return "<absent>"


ABSENT = Absent()


# --------------------------------------------------------------------
# THE SESSION: one fixture, staged deliberately off the defaults
# --------------------------------------------------------------------
class Session:
  """One staged session: a region on disk, a dialog, a map, a file.

  Attributes:
    dlg: the live dialog. REPLACED by the reopen-plugin act, so every
      reader takes it from here rather than closing over it.
    region: the region layer in force.
    gpkg: where the map is saved.
    folder: the temporary directory holding both, removed at teardown.

  WHY THE REGION IS WRITTEN TO DISK even though most of this suite's
  fixtures are memory layers: memory layers do not survive a project
  save at all, so the save-and-reopen boundary would be measuring
  their disappearance rather than the plugin's memory.
  """

  # THE STAGING, and every value here is chosen NOT to be one the
  # plugin would have picked. A fixture on its defaults lands on the
  # right answer by accident -- three fixtures in a row failed to make
  # a reordering visible on 2026-08-26 for exactly that reason -- so
  # the premise below asserts the staging took.
  # v3 is i*j, heavily tied and skewed, and it is on element a
  # deliberately: v1 and v2 are flat gradients over this grid, so
  # quantiles and equal intervals cut them at the SAME places and an
  # act that changes the scheme changes nothing anybody can read.
  # A fixture that cannot exhibit its case passes while proving
  # nothing, which is what the first run of this rebuild did.
  VARIABLES = {"a": "v3", "b": "landcover", "c": "v1", "d": "v2"}
  SPACING = 500.0
  FAMILY = "laves 3.3.4.3.4"
  ELEMENTS = 4
  RAMP = "Reds"
  CLASSES = 6

  def __init__(self, harness, seed):
    self.h = harness
    self.rng = random.Random(seed)
    self.folder = None
    self.dlg = None
    self.region = None
    self.gpkg = None
    self.spare = None

  # -- staging ------------------------------------------------------
  def open(self):
    """Build the fixture and land one map, or raise.

    Returns:
      None. Anything raised here is a HARNESS fault: the case never
      reached the act it was about.
    """
    import tempfile
    from qgis.core import QgsProject, QgsVectorLayer, QgsVectorFileWriter
    from weavingspace_qgis.dialog import WeavingSpaceDialog
    h = self.h

    QgsProject.instance().clear()
    self.folder = tempfile.mkdtemp(prefix="weavingspace_sweep_")
    self.gpkg = os.path.join(self.folder, "map.gpkg")

    # the region on disk, so a project round trip has something to
    # point at
    memory = h.make_region_layer(n=6, cell=1000)
    region_path = os.path.join(self.folder, "region.gpkg")
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = "region"
    QgsVectorFileWriter.writeAsVectorFormatV3(
      memory, region_path, QgsProject.instance().transformContext(), options)
    self.region = QgsVectorLayer(f"{region_path}|layername=region",
                                 "region", "ogr")
    if not self.region.isValid():
      raise RuntimeError("the region layer would not come back off disk")
    QgsProject.instance().addMapLayer(self.region)

    self.dlg = WeavingSpaceDialog(iface=h.Iface())
    self.dlg.live_check.setChecked(False)   # manual paths, deterministically
    self.dlg.layer_combo.setLayer(self.region)
    h.tick(200)
    self.dlg.n_spin.setValue(self.ELEMENTS)
    self.dlg.family_combo.setCurrentText(self.FAMILY)
    self.dlg.spacing_spin.setValue(self.SPACING)
    h.settle(self.dlg)

    for tid, field in self.VARIABLES.items():
      row = self._row_of(tid)
      if row is None:
        continue
      self.dlg.table.cellWidget(row, 1).setCurrentText(field)
    h.settle(self.dlg)
    # a ramp and a class count nobody would have defaulted to, driven
    # through `activated` because that is what marks a choice as the
    # user's
    self.pick_combo(self._row_of("a"), 4, self.RAMP)
    spin = self.dlg.table.cellWidget(self._row_of("a"), 3)
    if spin is not None and hasattr(spin, "setValue"):
      spin.setValue(self.CLASSES)
    h.settle(self.dlg)

    self.dlg.gpkg_widget.setFilePath(self.gpkg)
    h.generate(self.dlg)
    h.settle(self.dlg)
    h.press_save(self.dlg, self.gpkg)

  def close(self):
    """Let go of everything, including the file handles.

    Returns:
      None. The project is cleared FIRST: an output layer still open
      on the GeoPackage keeps a handle on a file the temporary
      directory is about to remove, and on Windows that is the
      WinError 32 nine of this suite's temporary directories met.
    """
    import shutil
    from qgis.core import QgsProject
    try:
      if self.dlg is not None:
        self.dlg.close()
    except Exception:
      pass
    self.dlg = None
    QgsProject.instance().clear()
    if self.folder:
      shutil.rmtree(self.folder, ignore_errors=True)
    self.folder = None

  # -- small conveniences the drivers share --------------------------
  def _row_of(self, tile_id):
    """Which table row carries this element, or None.

    Args:
      tile_id: an element id, "a".."d" in this fixture.

    Returns:
      The row index, or None where the design does not carry it --
      which a driver reports as a premise failure rather than
      silently doing nothing to row 0.
    """
    for row in range(self.dlg.table.rowCount()):
      item = self.dlg.table.item(row, 0)
      if item is not None and item.text() == tile_id:
        return row
    return None

  def pick_combo(self, row, column, wanted):
    """Choose a combo entry the way a click chooses it.

    Args:
      row: the table row.
      column: the table column.
      wanted: the text to pick. When it is not on offer, ANY other
        entry is taken instead and the substitute is returned -- a
        fresh QGIS holds a different ramp list from a seeded one, and
        a sweep that skips the act on such a machine reports a clean
        run for a case it never drove.

    Returns:
      (previous text, chosen text), or None where there is no such
      combo. The previous text is what undoes the act.

    `activated` is emitted as well as the index being set, because
    several of these handlers record the choice as THE USER'S from
    that signal alone; a bare setCurrentText leaves the next design
    rebuild free to revert it.
    """
    combo = self.dlg.table.cellWidget(row, column) if row is not None else None
    if combo is None or not hasattr(combo, "findText"):
      return None
    before = combo.currentText()
    index = combo.findText(wanted)
    if index < 0:
      offers = [combo.itemText(i) for i in range(combo.count())]
      alternatives = [t for t in offers if t and t != before and t != "---"]
      if not alternatives:
        return None
      index = combo.findText(self.rng.choice(alternatives))
    combo.setCurrentIndex(index)
    combo.activated.emit(index)
    self.h.settle(self.dlg)
    return before, combo.itemText(index)


# --------------------------------------------------------------------
# THE STORES
#
# Four readers, deliberately independent of each other and of the
# dialog's own bookkeeping wherever that is possible.
# --------------------------------------------------------------------
def read_row(session):
  """What the table says, which is what a person reads.

  Args:
    session: the live session.

  Returns:
    {element id: {fact: value}}. Taken from `_assignments()`, the ONE
    crossing point between widget state and everything downstream, so
    this reads the same thing the product reads rather than a second
    interpretation of the cells.

  `classes` is reported only for Graduated rows. On a Categorized row
  the record's `k` carries the row's REMEMBERED graduated count while
  the cell displays the detected category count, so comparing it with
  what the map draws would be comparing two different questions.
  """
  found = {}
  for a in session.dlg._assignments():
    single = a.get("mode") == "Single colour"
    found[a["id"]] = {
      "variable": ABSENT if single else a.get("var"),
      "mode": a.get("mode"),
      "scheme": a.get("scheme") if a.get("mode") == "Graduated" else ABSENT,
      "classes": a.get("k") if a.get("mode") == "Graduated" else ABSENT,
      "ramp": a.get("ramp") if not single else ABSENT,
      "opacity": a.get("opacity"),
      # not a comparable fact; carried so the hand-pick check below
      # can ask whether the map draws what the row says was picked
      "_picks": a.get("quant_colours") or {},
    }
  return found


def element_layers():
  """The plugin's element layers, found by asking the LAYER TREE.

  Returns:
    {element id: QgsVectorLayer}, in layer-tree order.

  NOT `dialog._element_layer_ids`, deliberately. That record is one of
  the stores under test: a dialog that has lost track of its own
  layers would then be measured as a map that does not exist, and the
  finding would read as an empty map rather than as a lost record.

  THE TWIN IS EXCLUDED. A paired artefact inherits the identity of
  what it is paired with, so the no-data layer carries its element's
  `weavingspace_tile_id` too; taking whichever came first would mean
  reading a renderer built to enumerate kinds of absence. The outline
  layer is excluded for the same reason.
  """
  from qgis.core import QgsProject
  found = {}
  for node in QgsProject.instance().layerTreeRoot().findLayers():
    layer = node.layer()
    if layer is None:
      continue
    tid = layer.customProperty("weavingspace_tile_id")
    if not tid:
      continue
    if layer.customProperty("weavingspace_no_data"):
      continue
    if layer.customProperty("weavingspace_outline"):
      continue
    found.setdefault(str(tid), layer)
  return found


def read_map(session):
  """What the map DRAWS, read off the renderers themselves.

  Args:
    session: the live session (unused beyond symmetry with the other
      readers; the map belongs to the project, not to the dialog).

  Returns:
    {element id: {fact: value}} with a `_colours` entry holding the
    class colours in ladder order.

  `ranges()` and `categories()` HAND BACK COPIES whose contents are
  freed the moment the temporary goes, so both are bound to a name
  before anything is subscripted. Unbound, that has segfaulted QGIS
  here once and returned a plausible wrong `#000000` once, and the
  second cost an hour aimed at the wrong cause.
  """
  from qgis.core import (QgsGraduatedSymbolRenderer,
                         QgsCategorizedSymbolRenderer,
                         QgsSingleSymbolRenderer)
  found = {}
  for tid, layer in element_layers().items():
    renderer = layer.renderer()
    opacity = int(round(layer.opacity() * 100))
    if isinstance(renderer, QgsGraduatedSymbolRenderer):
      ranges = renderer.ranges()          # BIND FIRST, then subscript
      colours = []
      for one in ranges:
        symbol = one.symbol()
        colours.append(symbol.color().name() if symbol else None)
      # THE LADDER, to six figures. A renderer does not record WHICH
      # scheme cut it in any spelling the row would recognise, so the
      # scheme is compared among the three record stores and the map
      # answers with the thing a scheme actually decides: where the
      # breaks fall. Rounded because a bound that survives a file
      # round trip can differ in its last bit, and this project has
      # already learned not to make anything depend on that.
      bounds = tuple((round(one.lowerValue(), 6), round(one.upperValue(), 6))
                     for one in ranges)
      found[tid] = {"_tiles": layer.featureCount(),
                    "variable": renderer.classAttribute(),
                    "mode": "Graduated", "scheme": ABSENT,
                    "classes": len(ranges),
                    "ramp": ABSENT, "opacity": opacity,
                    "_colours": tuple(colours), "_bounds": bounds}
    elif isinstance(renderer, QgsCategorizedSymbolRenderer):
      categories = renderer.categories()  # BIND FIRST, then subscript
      colours = []
      for one in categories:
        symbol = one.symbol()
        colours.append(symbol.color().name() if symbol else None)
      found[tid] = {"_tiles": layer.featureCount(),
                    "variable": renderer.classAttribute(),
                    "mode": "Categorized", "scheme": ABSENT,
                    "classes": ABSENT,
                    "ramp": ABSENT, "opacity": opacity,
                    "_colours": tuple(colours),
                    "_bounds": tuple(str(one.value()) for one in categories)}
    else:
      kind = ("Single colour" if isinstance(renderer, QgsSingleSymbolRenderer)
              else type(renderer).__name__)
      symbol = (renderer.symbol()
                if isinstance(renderer, QgsSingleSymbolRenderer) else None)
      found[tid] = {"_tiles": layer.featureCount(),
                    "variable": ABSENT, "mode": kind, "scheme": ABSENT,
                    "classes": ABSENT,
                    "ramp": ABSENT, "opacity": opacity,
                    "_colours": ((symbol.color().name(),) if symbol else ()),
                    "_bounds": ()}
  return found


def output_groups():
  """Every layer-tree group holding one of the plugin's element layers.

  Returns:
    A list of group nodes. A LIST rather than one group, because "this
    session left two output groups" is itself a finding this sweep has
    made before -- and because a later reading of "the group's record"
    is meaningless while there are two candidates for which group that
    is.
    Found by asking the LAYERS, never by name: a name is a label a
    user may edit, and this project has already shipped a defect built
    on looking a group up by its name.
  """
  from qgis.core import QgsProject
  groups = []
  for node in QgsProject.instance().layerTreeRoot().findGroups():
    for child in node.findLayers():
      layer = child.layer()
      if layer is not None and layer.customProperty("weavingspace_tile_id"):
        groups.append(node)
        break
  return groups


def read_group(session):
  """The working state the output group carries, read with plain json.

  Args:
    session: the live session, used only to say which group the dialog
      believes it is working in when there is more than one.

  Returns:
    {element id: {fact: value}}, empty where no group carries a record.

  Read straight off the node's custom property rather than through
  `dialog._read_working_state`, so the store is not being reported by
  the same code that writes it.
  """
  from weavingspace_qgis.dialog import WORKING_STATE_PROPERTY
  groups = output_groups()
  if not groups:
    return {}
  # WHEN A DEFECT MULTIPLIES THE THINGS A READING COULD BE ABOUT, name
  # the subject: a probe that read "whichever group came last" once
  # reported a record disagreeing with the row, and it was reading a
  # stale second group nobody was working in.
  wanted = getattr(session.dlg, "_group_name", None)
  node = groups[0]
  for candidate in groups:
    if wanted and candidate.name() == wanted:
      node = candidate
      break
  raw = node.customProperty(WORKING_STATE_PROPERTY)
  if not raw:
    return {}
  try:
    record = json.loads(raw)
  except (ValueError, TypeError):
    return {}
  return _elements_of(record)


def read_file(session):
  """The record inside the GeoPackage, as a colleague receives it.

  Args:
    session: the live session, for the output path.

  Returns:
    {element id: {fact: value}}, empty where the file holds no record.

  Read through OGR's metadata and sqlite, with every handle released
  before returning. An instrument that holds a GeoPackage open changes
  what the next reading of it sees -- measured here on 2026-08-27,
  where an open handle made the next run report zero tables -- and a
  value just written can be sitting in sqlite's write-ahead log beside
  the file rather than in it.
  """
  from weavingspace_qgis import bridge
  path = session.gpkg
  if not path or not os.path.exists(path):
    return {}
  record = bridge.read_working_state(path)
  if not isinstance(record, dict):
    return {}
  return _elements_of(record)


def _elements_of(record):
  """Turn a working-state record into the common fact vocabulary.

  Args:
    record: a working state, from a group property or from a file.

  Returns:
    {element id: {fact: value}}. The keys are the ones
    `WORKING_STATE_ELEMENT` carries, mapped onto the same names the
    row and the map answer in, so the three can be compared at all.
  """
  found = {}
  for element in (record.get("elements") or []):
    tid = element.get("id")
    if not tid:
      continue
    single = element.get("mode") == "Single colour"
    found[str(tid)] = {
      "variable": ABSENT if single else element.get("var"),
      "mode": element.get("mode"),
      "scheme": (element.get("scheme") if element.get("mode") == "Graduated"
                 else ABSENT),
      "classes": (element.get("k") if element.get("mode") == "Graduated"
                  else ABSENT),
      "ramp": element.get("ramp") if not single else ABSENT,
      "opacity": element.get("opacity"),
      "_picks": element.get("quant_colours") or {},
    }
  return found


# The design facts, which belong to the whole map rather than to any
# element. They are here because the first run of this rebuild reported
# that CHANGING THE SPACING changed nothing: spacing is not a property
# of an element, so a per-element oracle is blind to it, and the change
# flag caught the blindness -- which is the whole reason the flag
# exists. `n` is the sharpest of the three, because the MAP holds it
# too: a design saying four elements against a group holding three is a
# disagreement anybody could see in the layers panel.
DESIGN_FACTS = ("n", "family", "spacing")


def read_design(session):
  """The design, from every store that records one.

  Args:
    session: the live session.

  Returns:
    {store: {fact: value}}. The map answers `n` alone -- by counting
    the element layers it actually drew -- because a renderer knows
    nothing about families or spacings.
  """
  from weavingspace_qgis.dialog import WORKING_STATE_PROPERTY
  dlg = session.dlg
  wanted = {"n": ("n_spin", "number"), "family": ("family_combo", "text"),
            "spacing": ("spacing_spin", "number")}
  row = {}
  for fact, (attribute, kind) in wanted.items():
    widget = getattr(dlg, attribute, None)
    row[fact] = (dlg._read_control(widget, kind) if widget is not None
                 else ABSENT)
  found = {"row": row,
           "map": {"n": len(element_layers()), "family": ABSENT,
                   "spacing": ABSENT},
           "group": {}, "file": {}}

  groups = output_groups()
  record = None
  if groups:
    wanted_name = getattr(dlg, "_group_name", None)
    node = groups[0]
    for candidate in groups:
      if wanted_name and candidate.name() == wanted_name:
        node = candidate
        break
    raw = node.customProperty(WORKING_STATE_PROPERTY)
    if raw:
      try:
        record = json.loads(raw)
      except (ValueError, TypeError):
        record = None
  found["group"] = _design_of(record)

  from weavingspace_qgis import bridge
  filed = (bridge.read_working_state(session.gpkg)
           if session.gpkg and os.path.exists(session.gpkg) else None)
  found["file"] = _design_of(filed if isinstance(filed, dict) else None)
  return found


def _design_of(record):
  """Pull the three design facts out of a working-state record.

  Args:
    record: a working state, or None.

  Returns:
    {fact: value}, empty where there is no record. Absent keys come
    back ABSENT rather than None: a record that never carried a
    spacing is a different claim from one carrying no spacing, and
    only the second is a finding.
  """
  if not isinstance(record, dict):
    return {}
  design = record.get("design") or {}
  return {fact: design.get(fact, ABSENT) for fact in DESIGN_FACTS}


def read_identity(session):
  """What the output group is CALLED, asked of two stores.

  Args:
    session: the live session.

  Returns:
    {"panel": what the layers panel shows, "dialog": what the dialog
    believes it is working in}. A name is a LABEL and never an
    identity here -- the lookup asks the layers -- but the two stores
    must still agree about the label, and a rename in the panel is an
    ordinary act that this project has already shipped a defect over.
  """
  groups = output_groups()
  return {"panel": groups[0].name() if groups else ABSENT,
          "dialog": getattr(session.dlg, "_group_name", ABSENT)}


def observe(session):
  """Read every store at one moment.

  Args:
    session: the live session.

  Returns:
    {"row": ..., "map": ..., "group": ..., "file": ...,
     "_groups": how many output groups the project holds}.

  Read at REST and nowhere else: the callers settle the dialog first.
  During a run, a landing or an applied style the record and the layer
  are transiently out of step and what sits on the layer is nobody's
  decision.
  """
  return {"row": read_row(session), "map": read_map(session),
          "group": read_group(session), "file": read_file(session),
          "_groups": len(output_groups()), "design": read_design(session),
          "identity": read_identity(session)}


# --------------------------------------------------------------------
# THE INVARIANTS
# --------------------------------------------------------------------
def check_agreement(observation):
  """Every store holding a fact agrees about it.

  Args:
    observation: one reading of all four stores.

  Returns:
    (comparisons made, [disagreement, ...]). Each disagreement names
    the element, the fact, and WHAT EACH STORE SAID -- the report is
    useless without the values, and a count of comparisons is what
    stops a vacuous run reading as a clean one.
  """
  comparisons = 0
  disagreements = []
  elements = sorted({tid for store in STORES
                     for tid in observation[store]})
  for tid in elements:
    # A store that does not carry the element AT ALL is a different
    # kind of disagreement from one that carries it with a different
    # value, and it is the one that means a layer or a record went
    # missing. Reported before any fact is compared.
    holding = [s for s in STORES if tid in observation[s]]
    missing = [s for s in STORES if tid not in observation[s]]
    comparisons += len(STORES) - 1
    if missing and holding:
      disagreements.append({
        "element": tid, "fact": "the element exists at all",
        "said": {s: ("held" if s in holding else "MISSING")
                 for s in STORES}})
      continue
    for fact in FACTS:
      said = {}
      for store in holding:
        value = observation[store][tid].get(fact, ABSENT)
        if value is not ABSENT:
          said[store] = value
      if len(said) < 2:
        continue                    # nothing to disagree with
      comparisons += len(said) - 1
      distinct = {_comparable(v) for v in said.values()}
      if len(distinct) > 1:
        disagreements.append({"element": tid, "fact": fact, "said": said})

  # THE DESIGN, which no element holds and which three stores do.
  for fact in DESIGN_FACTS:
    said = {}
    for store in STORES:
      value = (observation["design"].get(store) or {}).get(fact, ABSENT)
      if value is not ABSENT:
        said[store] = value
    if len(said) < 2:
      continue
    comparisons += len(said) - 1
    if len({_comparable(v) for v in said.values()}) > 1:
      disagreements.append({"element": "(the design)", "fact": fact,
                            "said": said})

  # AND WHAT THE GROUP IS CALLED, which two stores hold.
  said = {k: v for k, v in observation["identity"].items() if v is not ABSENT}
  if len(said) > 1:
    comparisons += len(said) - 1
    if len({_comparable(v) for v in said.values()}) > 1:
      disagreements.append({"element": "(the output group)",
                            "fact": "its name", "said": said})
  return comparisons, disagreements


def _comparable(value):
  """One spelling per value, so a float and an int are not a finding.

  Args:
    value: whatever a store answered.

  Returns:
    A hashable form. Opacity comes back as 40 from one store and 40.0
    from another, and a sweep that reported that as a disagreement
    would be reporting on Python rather than on the plugin.
  """
  if isinstance(value, bool):
    return value
  if isinstance(value, (int, float)):
    return round(float(value), 6)
  return value


def check_picks_are_drawn(observation):
  """Every hand-picked class colour is the colour the map draws there.

  Args:
    observation: one reading of all four stores.

  Returns:
    (comparisons, [disagreement, ...]).

  This is the four-corner question in miniature: the user's intent, as
  recorded, against what the renderer paints. It is separated from the
  agreement walk because it compares a MAP of picks against a LIST of
  drawn colours rather than two like values.
  """
  comparisons = 0
  disagreements = []
  for tid, facts in observation["map"].items():
    colours = facts.get("_colours") or ()
    for store in ("row", "group", "file"):
      picks = (observation[store].get(tid) or {}).get("_picks") or {}
      for index, wanted in picks.items():
        try:
          position = int(index)
        except (TypeError, ValueError):
          continue
        if position >= len(colours):
          continue
        comparisons += 1
        if str(colours[position]).lower() != str(wanted).lower():
          disagreements.append({
            "element": tid, "fact": f"class {position}'s hand-picked colour",
            "said": {store: wanted, "map": colours[position]}})
  return comparisons, disagreements


def check_collateral(before, after, subject):
  """An act about element X moved nothing about any other element.

  Args:
    before: the observation taken before the act.
    after: the observation taken after it.
    subject: the element the act was about. None means the act was
      about the whole design, for which there is no collateral
      question and this returns (0, []) -- reported as "not judged"
      rather than as a pass, since a check that cannot fail is not a
      check.

  Returns:
    (comparisons, [disagreement, ...]).
  """
  if subject is None:
    return 0, []
  comparisons = 0
  disagreements = []
  for store in STORES:
    for tid in sorted(set(before[store]) | set(after[store])):
      if tid == subject:
        continue
      was = before[store].get(tid)
      now = after[store].get(tid)
      for fact in FACTS + MOMENT_FACTS:
        old = (was or {}).get(fact, ABSENT)
        new = (now or {}).get(fact, ABSENT)
        if old is ABSENT and new is ABSENT:
          continue
        comparisons += 1
        if _comparable(old) != _comparable(new):
          disagreements.append({
            "element": tid, "fact": f"{fact} (in the {store})",
            "said": {"before the act": old, "after it": new}})
  return comparisons, disagreements


def check_same(before, after, why):
  """Two readings of every store are identical.

  Args:
    before: the earlier observation.
    after: the later one.
    why: what the comparison is about, for the report -- "a boundary
      crossing changed something" or "the act did not come back".

  Returns:
    (comparisons, [disagreement, ...]).

  This is BOTH the boundary crossing's own invariant and RETURN's,
  which is not a coincidence: a crossing is an act whose inverse is
  doing nothing.
  """
  comparisons = 0
  disagreements = []
  comparisons += 1
  if before["_groups"] != after["_groups"]:
    disagreements.append({
      "element": "(the project)", "fact": f"how many output groups: {why}",
      "said": {"before": before["_groups"], "after": after["_groups"]}})
  for fact in DESIGN_FACTS:
    for store in STORES:
      old_value = (before["design"].get(store) or {}).get(fact, ABSENT)
      new_value = (after["design"].get(store) or {}).get(fact, ABSENT)
      if old_value is ABSENT and new_value is ABSENT:
        continue
      comparisons += 1
      if _comparable(old_value) != _comparable(new_value):
        disagreements.append({
          "element": "(the design)",
          "fact": f"{fact} (in the {store}): {why}",
          "said": {"before": old_value, "after": new_value}})
  for store, old_value in before["identity"].items():
    new_value = after["identity"].get(store, ABSENT)
    if old_value is ABSENT and new_value is ABSENT:
      continue
    comparisons += 1
    if _comparable(old_value) != _comparable(new_value):
      disagreements.append({
        "element": "(the output group)",
        "fact": f"its name (as the {store} has it): {why}",
        "said": {"before": old_value, "after": new_value}})
  for store in STORES:
    for tid in sorted(set(before[store]) | set(after[store])):
      was = before[store].get(tid)
      now = after[store].get(tid)
      for fact in FACTS + MOMENT_FACTS:
        old = (was or {}).get(fact, ABSENT)
        new = (now or {}).get(fact, ABSENT)
        if old is ABSENT and new is ABSENT:
          continue
        comparisons += 1
        if _comparable(old) != _comparable(new):
          disagreements.append({
            "element": tid, "fact": f"{fact} (in the {store}): {why}",
            "said": {"before": old, "after": new}})
  return comparisons, disagreements


def anything_moved(before, after):
  """Whether ANY store answered differently.

  Args:
    before: the earlier observation.
    after: the later one.

  Returns:
    True when something moved. A CONTROL act that moves nothing passes
    every invariant while proving nothing, which is this project's
    standing trap and the reason this function exists.
  """
  _n, differences = check_same(before, after, "change flag")
  return bool(differences)


# --------------------------------------------------------------------
# THE DRIVERS
#
# Each takes (session, argument) and returns the argument that UNDOES
# it, or None where it has no inverse. Returning the undo argument
# rather than naming it in the act table is what keeps the table data:
# the old value is read from the fixture at the moment of the act, so
# it cannot go stale.
# --------------------------------------------------------------------
def drive_ramp(session, argument):
  """Choose a colour ramp for one element, as a click chooses it.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"element": <tile id>, "value": <what to set>}``.

  Returns:
    The argument that UNDOES this act -- the value the control held
    before -- so the RETURN invariant can be driven without the act
    table naming an old value that would go stale.

  Raises:
    RuntimeError where the control is absent or ALREADY holds the
    value being set. Both are premise failures rather than findings:
    an act that could not move has measured nothing, and reporting
    that as red is how a sweep's failures come to be mostly its own.
  """
  row = session._row_of(argument["element"])
  if row is None:
    raise RuntimeError(f"no row for element {argument['element']!r}")
  moved = session.pick_combo(row, 4, argument["value"])
  if moved is None:
    raise RuntimeError("the ramp combo would not take a choice")
  before, chosen = moved
  if before == chosen:
    raise RuntimeError(f"the ramp was already {chosen!r}, so this act "
                       f"could not change anything")
  return {"element": argument["element"], "value": before}


def drive_style(session, argument):
  """Choose a symbology style for one element, as a click chooses it.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"element": <tile id>, "value": <what to set>}``.

  Returns:
    The argument that UNDOES this act -- the value the control held
    before -- so the RETURN invariant can be driven without the act
    table naming an old value that would go stale.

  Raises:
    RuntimeError where the control is absent or ALREADY holds the
    value being set. Both are premise failures rather than findings:
    an act that could not move has measured nothing, and reporting
    that as red is how a sweep's failures come to be mostly its own.
  """
  row = session._row_of(argument["element"])
  if row is None:
    raise RuntimeError(f"no row for element {argument['element']!r}")
  moved = session.pick_combo(row, 2, argument["value"])
  if moved is None:
    raise RuntimeError("the style combo would not take a choice")
  before, chosen = moved
  if before == chosen:
    raise RuntimeError(f"the style was already {chosen!r}")
  return {"element": argument["element"], "value": before}


def drive_variable(session, argument):
  """Point one element at another column.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"element": <tile id>, "value": <what to set>}``.

  Returns:
    The argument that UNDOES this act -- the value the control held
    before -- so the RETURN invariant can be driven without the act
    table naming an old value that would go stale.

  Raises:
    RuntimeError where the control is absent or ALREADY holds the
    value being set. Both are premise failures rather than findings:
    an act that could not move has measured nothing, and reporting
    that as red is how a sweep's failures come to be mostly its own.
  """
  row = session._row_of(argument["element"])
  if row is None:
    raise RuntimeError(f"no row for element {argument['element']!r}")
  moved = session.pick_combo(row, 1, argument["value"])
  if moved is None:
    raise RuntimeError("the variable combo would not take a choice")
  before, chosen = moved
  if before == chosen:
    raise RuntimeError(f"the variable was already {chosen!r}")
  return {"element": argument["element"], "value": before}


def drive_classes(session, argument):
  """Move one element's class count.

  The spinner is set rather than typed into. Typing is a separate
  question this project has paid for four times (a validator eating a
  keystroke, a handler rewriting its own box) and it belongs in a test
  aimed at controls; what this sweep is about is whether the stores
  agree once the number has been accepted.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"element": <tile id>, "value": <what to set>}``.

  Returns:
    The argument that UNDOES this act -- the value the control held
    before -- so the RETURN invariant can be driven without the act
    table naming an old value that would go stale.

  Raises:
    RuntimeError where the control is absent or ALREADY holds the
    value being set. Both are premise failures rather than findings:
    an act that could not move has measured nothing, and reporting
    that as red is how a sweep's failures come to be mostly its own.
  """
  row = session._row_of(argument["element"])
  spin = (session.dlg.table.cellWidget(row, 3) if row is not None else None)
  if spin is None or not hasattr(spin, "setValue"):
    raise RuntimeError("this element has no class-count spinner")
  before = spin.value()
  if before == argument["value"]:
    raise RuntimeError(f"the class count was already {before}")
  spin.setValue(argument["value"])
  session.h.settle(session.dlg)
  return {"element": argument["element"], "value": before}


def drive_opacity(session, argument):
  """Move one element's opacity.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"element": <tile id>, "value": <what to set>}``.

  Returns:
    The argument that UNDOES this act -- the value the control held
    before -- so the RETURN invariant can be driven without the act
    table naming an old value that would go stale.

  Raises:
    RuntimeError where the control is absent or ALREADY holds the
    value being set. Both are premise failures rather than findings:
    an act that could not move has measured nothing, and reporting
    that as red is how a sweep's failures come to be mostly its own.
  """
  row = session._row_of(argument["element"])
  cell = (session.dlg.table.cellWidget(row, 6) if row is not None else None)
  if cell is None or not hasattr(cell, "setValue"):
    raise RuntimeError("this element has no opacity control")
  before = cell.value()
  if before == argument["value"]:
    raise RuntimeError(f"the opacity was already {before}")
  cell.setValue(argument["value"])
  session.h.settle(session.dlg)
  return {"element": argument["element"], "value": before}


def drive_reverse(session, argument):
  """Tick or untick one element's Reverse box.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"element": <tile id>, "value": <what to set>}``.

  Returns:
    The argument that UNDOES this act -- the value the control held
    before -- so the RETURN invariant can be driven without the act
    table naming an old value that would go stale.

  Raises:
    RuntimeError where the control is absent or ALREADY holds the
    value being set. Both are premise failures rather than findings:
    an act that could not move has measured nothing, and reporting
    that as red is how a sweep's failures come to be mostly its own.
  """
  row = session._row_of(argument["element"])
  cell = (session.dlg.table.cellWidget(row, 5) if row is not None else None)
  box = cell
  if cell is not None and not hasattr(cell, "setChecked"):
    # the box is centred inside a container widget in some builds, so
    # look one level down rather than assuming the cell IS the box
    for child in cell.findChildren(type(cell)):
      if hasattr(child, "setChecked"):
        box = child
        break
  if box is None or not hasattr(box, "setChecked"):
    raise RuntimeError("this element has no Reverse box")
  before = box.isChecked()
  if before == argument["value"]:
    raise RuntimeError(f"Reverse was already {before}")
  box.setChecked(argument["value"])
  session.h.settle(session.dlg)
  return {"element": argument["element"], "value": before}


def drive_spacing(session, argument):
  """Change the tile spacing, which is a GEOMETRY change.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"value": <what to set>}``, or empty where the act
      takes nothing.

  Returns:
    The argument that undoes this act, or None where it has no
    inverse and the RETURN invariant is therefore not asked.

  Raises:
    RuntimeError where the act could not be driven at all, which is a
    premise failure rather than a finding.
  """
  before = session.dlg.spacing_spin.value()
  if abs(before - argument["value"]) < 1e-9:
    raise RuntimeError(f"the spacing was already {before}")
  session.dlg.spacing_spin.setValue(argument["value"])
  session.h.settle(session.dlg)
  return {"value": before}


def drive_dock_recolour(session, argument):
  """Recolour one class the way QGIS's styling dock does.

  The renderer is CLONED, the class recoloured on the clone, and the
  clone installed with `setRenderer`. Editing the renderer the layer
  is holding is what a bare `ranges()[0].symbol().setColor(...)` does,
  and that recolours a TEMPORARY: the layer never changes and the
  probe measures nothing. This project has made that mistake twice.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"element": <tile id>, "value": <what to set>}``.

  Returns:
    The argument that UNDOES this act -- the value the control held
    before -- so the RETURN invariant can be driven without the act
    table naming an old value that would go stale.

  Raises:
    RuntimeError where the control is absent or ALREADY holds the
    value being set. Both are premise failures rather than findings:
    an act that could not move has measured nothing, and reporting
    that as red is how a sweep's failures come to be mostly its own.
  """
  from qgis.core import QgsGraduatedSymbolRenderer
  layers = element_layers()
  layer = layers.get(argument["element"])
  if layer is None:
    raise RuntimeError(f"no layer for element {argument['element']!r}")
  renderer = layer.renderer()
  if not isinstance(renderer, QgsGraduatedSymbolRenderer):
    raise RuntimeError("this element is not drawn with a graduated renderer")
  clone = renderer.clone()
  ranges = clone.ranges()               # BIND FIRST, then subscript
  if not ranges:
    raise RuntimeError("the renderer has no classes to recolour")
  symbol = ranges[0].symbol().clone()
  was = symbol.color().name()
  if was.lower() == argument["value"].lower():
    raise RuntimeError("that class already wears the colour being set")
  from qgis.PyQt.QtGui import QColor
  symbol.setColor(QColor(argument["value"]))
  clone.updateRangeSymbol(0, symbol)
  layer.setRenderer(clone)
  layer.triggerRepaint()
  session.h.settle(session.dlg)
  # PREMISE: the edit reached the LAYER, not a copy of its renderer.
  now = layer.renderer().ranges()
  landed = now[0].symbol().color().name() if now else None
  if str(landed).lower() != argument["value"].lower():
    raise RuntimeError(f"the dock edit never reached the layer: it draws "
                       f"{landed!r}")
  return None


def drive_rename_group(session, argument):
  """Rename the output group in the layers panel, as a user may.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"value": <what to set>}``, or empty where the act
      takes nothing.

  Returns:
    The argument that undoes this act, or None where it has no
    inverse and the RETURN invariant is therefore not asked.

  Raises:
    RuntimeError where the act could not be driven at all, which is a
    premise failure rather than a finding.
  """
  groups = output_groups()
  if not groups:
    raise RuntimeError("there is no output group to rename")
  node = groups[0]
  before = node.name()
  if before == argument["value"]:
    raise RuntimeError("the group already has that name")
  node.setName(argument["value"])
  session.h.settle(session.dlg)
  return {"value": before}


def drive_reopen_plugin(session, argument):
  """Open a FRESH dialog onto the same project.

  This is the act HUNT-RECORD.md records as the plainest defect the
  first outing found. It models the plugin being closed and opened
  again far enough into a QGIS session that the old dialog object has
  gone -- the journey `_adopt_existing_group`'s own docstring names as
  something "users do constantly".

  Closing the WINDOW alone is deliberately not this act: `open_dialog`
  reuses the object, so a hidden window brought back holds everything
  it had, and testing that would be testing nothing.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"value": <what to set>}``, or empty where the act
      takes nothing.

  Returns:
    The argument that undoes this act, or None where it has no
    inverse and the RETURN invariant is therefore not asked.

  Raises:
    RuntimeError where the act could not be driven at all, which is a
    premise failure rather than a finding.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  old = session.dlg
  try:
    old.close()
  except Exception:
    pass
  fresh = WeavingSpaceDialog(iface=session.h.Iface())
  fresh.live_check.setChecked(False)
  session.dlg = fresh
  session.h.tick(300)
  session.h.settle(fresh)
  return None


def drive_reopen_project(session, argument):
  """Save the project, empty QGIS, and read it back.

  `clear()` between the write and the read is what makes this a
  reading of the FILE rather than of memory: without it QGIS keeps the
  live layers and merges into them, and the act would pass whatever
  the file contained.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"value": <what to set>}``, or empty where the act
      takes nothing.

  Returns:
    The argument that undoes this act, or None where it has no
    inverse and the RETURN invariant is therefore not asked.

  Raises:
    RuntimeError where the act could not be driven at all, which is a
    premise failure rather than a finding.
  """
  from qgis.core import QgsProject
  path = os.path.join(session.folder, "session.qgz")
  project = QgsProject.instance()
  if not project.write(path):
    raise RuntimeError(f"the project would not write to {path}")
  project.clear()
  if project.mapLayers():
    raise RuntimeError("clear() left layers behind")
  if not project.read(path):
    raise RuntimeError(f"the project would not read back from {path}")
  session.h.tick(400)
  session.h.settle(session.dlg)
  # the region layer is a new object after the round trip
  for layer in project.mapLayers().values():
    if not layer.customProperty("weavingspace_tile_id") \
       and not layer.customProperty("weavingspace_output"):
      session.region = layer
      break
  return None


def drive_save_gpkg(session, argument):
  """Press Save, which is the act that writes the file.

  Saving became a positive act on 2026-08-27: a run no longer writes
  the GeoPackage, so this is a boundary crossing in its own right --
  writing a file must not change the map or anybody's records.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"value": <what to set>}``, or empty where the act
      takes nothing.

  Returns:
    The argument that undoes this act, or None where it has no
    inverse and the RETURN invariant is therefore not asked.

  Raises:
    RuntimeError where the act could not be driven at all, which is a
    premise failure rather than a finding.
  """
  wrote = session.h.press_save(session.dlg, session.gpkg)
  if not wrote:
    raise RuntimeError("Save wrote nothing")
  session.h.settle(session.dlg)
  return None


def drive_choose_group(session, argument):
  """Choose, in the group chooser, the group already being worked in.

  An ordinary act -- a person confirming where the output goes -- and
  one that restores the whole working state, so it is the sharpest
  test there is of whether that state was ever lost.

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"value": <what to set>}``, or empty where the act
      takes nothing.

  Returns:
    The argument that undoes this act, or None where it has no
    inverse and the RETURN invariant is therefore not asked.

  Raises:
    RuntimeError where the act could not be driven at all, which is a
    premise failure rather than a finding.
  """
  combo = getattr(session.dlg, "group_combo", None)
  if combo is None or combo.count() == 0:
    raise RuntimeError("there is no group chooser to choose from")
  index = max(combo.currentIndex(), 0)
  combo.setCurrentIndex(index)
  combo.activated.emit(index)
  session.h.settle(session.dlg)
  return None


def drive_switch_dataset_and_back(session, argument):
  """Point the region chooser at another dataset, then back again.

  The return leg is the whole act: switching away is expected to
  deactivate what the new data cannot carry, and coming home is
  expected to give it back (the rulings of 2026-08-21 and 2026-08-26).

  Args:
    session: the staged session; the act is driven through its dialog
      and its layers, never through a snapshot of either.
    argument: ``{"value": <what to set>}``, or empty where the act
      takes nothing.

  Returns:
    The argument that undoes this act, or None where it has no
    inverse and the RETURN invariant is therefore not asked.

  Raises:
    RuntimeError where the act could not be driven at all, which is a
    premise failure rather than a finding.
  """
  from qgis.core import QgsProject
  if session.spare is None:
    session.spare = session.h.make_region_layer(n=4, cell=1000,
                                                origin=(500000, 500000))
    session.spare.setName("other region")
    QgsProject.instance().addMapLayer(session.spare)
    session.h.settle(session.dlg)
  home = session.region
  session.dlg.layer_combo.setLayer(session.spare)
  session.h.tick(300)
  session.h.settle(session.dlg)
  if session.dlg.layer_combo.currentLayer() is not session.spare:
    raise RuntimeError("the chooser would not take the other dataset")
  session.dlg.layer_combo.setLayer(home)
  session.h.tick(300)
  session.h.settle(session.dlg)
  if session.dlg.layer_combo.currentLayer() is not home:
    raise RuntimeError("the chooser would not come home")
  return None


DRIVERS = {
  "ramp": drive_ramp,
  "style": drive_style,
  "variable": drive_variable,
  "classes": drive_classes,
  "opacity": drive_opacity,
  "reverse": drive_reverse,
  "spacing": drive_spacing,
  "dock_recolour": drive_dock_recolour,
  "rename_group": drive_rename_group,
  "reopen_plugin": drive_reopen_plugin,
  "reopen_project": drive_reopen_project,
  "save_gpkg": drive_save_gpkg,
  "choose_group": drive_choose_group,
  "switch_dataset_and_back": drive_switch_dataset_and_back,
}


# --------------------------------------------------------------------
# THE HARNESS
# --------------------------------------------------------------------
class Harness:
  """The suite's own helpers, borrowed rather than written again.

  Attributes:
    Iface: the stub QGIS interface, so notices go where they go in a
      real session rather than to the dialog's note line.
    settle: wait until no task, no live timer and no preview timer.
    generate: press Generate and wait for the run to land.
    press_save: press Save and say whether a file was written.
    make_region_layer: the synthetic region.
    tick: turn the event loop briefly.

  WHY IMPORT tests/run_tests.py rather than reimplement: those helpers
  encode measurements this tool would otherwise get wrong. `_settle`
  waits on the EVENT rather than on seconds; `press_save` reads BOTH
  stores a refusal can land in, since a Save refused through a
  QMessageBox leaves the message bar empty and reading one store and
  concluding silence is this project's own harness fault eleven. The
  module has no side effects at import: it builds its QgsApplication
  inside `main()`, which this tool does for itself below.
  """

  def __init__(self):
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    import run_tests
    self.suite = run_tests
    self.Iface = run_tests._Iface
    self.settle = run_tests._settle
    self.generate = run_tests._generate_and_wait
    self.press_save = run_tests.press_save
    self.make_region_layer = run_tests.make_region_layer
    self.tick = run_tests._tick


def start_qgis():
  """Bring QGIS up exactly as the suite does.

  Returns:
    The QgsApplication, which must be kept alive for the run: letting
    it be collected takes the whole process with it.
  """
  from qgis.core import QgsApplication
  QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"),
                               True)
  app = QgsApplication([], True)
  app.initQgis()
  return app


def premise(session, where):
  """Assert the fixture can exhibit the case, before anything is judged.

  Args:
    session: the staged session.
    where: what is about to happen, named in the failure.

  Raises:
    RuntimeError naming what was missing. Every one of these is a
    HARNESS fault rather than a finding: a case that cannot stage
    itself has measured nothing, and reporting it as red is how a
    sweep's failures come to be mostly its own.

  THE PREMISE IS THE ONE THING THAT CATCHES THE FIRST OUTING'S EIGHT
  KNOWN PROBE FAULTS -- a freed temporary answering `#000000`, a
  widget held across a rebuild, an oracle reading a stale snapshot, a
  fixture that could not exhibit its case. Nothing else does.
  """
  observation = observe(session)
  if not observation["row"]:
    raise RuntimeError(f"{where}: the table holds no elements")
  if not observation["map"]:
    raise RuntimeError(f"{where}: the project holds no element layers, so "
                       f"there is no map to read")
  if not observation["group"]:
    raise RuntimeError(f"{where}: the output group carries no record")
  if not observation["file"]:
    raise RuntimeError(f"{where}: the GeoPackage carries no record")
  # STAGED OFF THE DEFAULTS. A fixture the plugin would have produced
  # anyway cannot tell a restored choice from a re-derived one, which
  # is how three fixtures in a row failed to show a reordering on
  # 2026-08-26.
  chosen = observation["row"].get("a") or {}
  if chosen.get("ramp") in (None, ABSENT):
    raise RuntimeError(f"{where}: element a carries no chosen ramp, so a "
                       f"lost choice would look like a default")
  variables = {t: f.get("variable") for t, f in observation["row"].items()}
  if len(set(variables.values())) < 2:
    raise RuntimeError(f"{where}: every element carries the same variable "
                       f"({variables!r}), so collateral cannot be seen")
  return observation


def run_act(harness, act, seed, report):
  """Stage one session, drive one act, and judge it.

  Args:
    harness: the borrowed suite helpers.
    act: one row of ACTS.
    seed: the run's seed, so a case's random substitutions repeat.
    report: the accumulating record, appended to in place.

  Returns:
    None. Everything is written into `report`, because a sweep that
    stops at the first failure reports one cell of a matrix.
  """
  name, kind, driver, argument, subject, reversible = act
  entry = {"act": name, "kind": kind, "judged_by": [], "findings": [],
           "comparisons": 0, "harness": None, "seconds": 0.0}
  report.append(entry)
  started = time.monotonic()          # monotonic: a closed laptop makes
  session = Session(harness, seed)    # wall clock lie about duration
  try:
    session.open()
    before = premise(session, f"staging {name!r}")

    undo = DRIVERS[driver](session, argument)

    # A CONTROL or QGIS-side act is judged after the user asks for the
    # map and saves it, because that is the journey: change something,
    # press Generate, send the file on. A BOUNDARY crossing is judged
    # on its own, with nothing pressed -- the whole claim is that it
    # changed nothing.
    if kind != "boundary":
      harness.generate(session.dlg)
      harness.settle(session.dlg)
      harness.press_save(session.dlg, session.gpkg)
    harness.settle(session.dlg)
    after = observe(session)

    # THE CHANGE FLAG, which is the one thing separating the kinds.
    if kind == "boundary":
      entry["judged_by"].append("changed nothing")
      count, differences = check_same(before, after,
                                      "a boundary crossing is not an edit")
      entry["comparisons"] += count
      entry["findings"].extend(differences)
    else:
      entry["judged_by"].append("changed something")
      entry["comparisons"] += 1
      if not anything_moved(before, after):
        entry["findings"].append({
          "element": "(the act)", "fact": "it changed nothing at all",
          "said": {"note": "every store answered exactly as before, so "
                           "the three invariants below prove nothing "
                           "about this act"}})

    entry["judged_by"].append("agreement")
    count, differences = check_agreement(after)
    entry["comparisons"] += count
    entry["findings"].extend(differences)

    count, differences = check_picks_are_drawn(after)
    if count:
      entry["judged_by"].append("hand-picked colours are drawn")
    entry["comparisons"] += count
    entry["findings"].extend(differences)

    count, differences = check_collateral(before, after, subject)
    if subject is not None:
      entry["judged_by"].append(f"collateral (everything but {subject})")
    entry["comparisons"] += count
    entry["findings"].extend(differences)

    if reversible and undo is not None:
      DRIVERS[driver](session, undo)
      if kind != "boundary":
        harness.generate(session.dlg)
        harness.settle(session.dlg)
        harness.press_save(session.dlg, session.gpkg)
      harness.settle(session.dlg)
      back = observe(session)
      entry["judged_by"].append("return")
      count, differences = check_same(back, before, "the act was undone")
      entry["comparisons"] += count
      entry["findings"].extend(differences)
  except Exception as exc:
    entry["harness"] = f"{type(exc).__name__}: {exc}"
    entry["traceback"] = traceback.format_exc()
  finally:
    entry["seconds"] = time.monotonic() - started
    try:
      session.close()
    except Exception as exc:          # a teardown fault is still mine
      entry["harness"] = (entry["harness"] or "") + \
        f" | teardown {type(exc).__name__}: {exc}"


def one_act_in_a_child(index, seed, where):
  """Run act `index` in a process of its own and read its verdict back.

  Args:
    index: which row of ACTS to drive.
    seed: this run's seed, passed on so the child's substitutions
      match the parent's report.
    where: a directory the child may write its verdict into.

  Returns:
    The child's entry, or one this function invents describing how the
    child died.

  WHY A CHILD PER ACT, and it was learned the expensive way on the
  first run of this rebuild: act eleven segfaulted inside a Qt signal
  handler during a project read, and a segfault is not an exception --
  it took the process, and with it the report on the ten acts that had
  already finished AND the three that had not started. A sweep that
  reports nothing about thirteen acts because of one is worth less
  than no sweep, since its silence reads as absence.
  It also makes the isolation total. Everything here shares one
  QgsProject singleton and one style library, and a case that leaves
  something behind means the next one measures this tool's rubbish; a
  fresh process cannot.
  THE CHILD IS INSTRUMENTED BEFORE IT CRASHES: `faulthandler` is on
  (the suite's `_enable_stack_dumps`), so a death in C names a call
  rather than leaving exit -11 and two empty streams.
  """
  import subprocess
  verdict = os.path.join(where, f"act-{index}.json")
  command = [sys.executable, "-u", os.path.abspath(__file__),
             "--one", str(index), "--seed", str(seed), "--json", verdict]
  started = time.monotonic()
  done = subprocess.run(command, capture_output=True, text=True,
                        timeout=1800)
  if os.path.exists(verdict):
    with open(verdict, encoding="utf-8") as handle:
      entry = json.load(handle)
    entry["child_output"] = done.stdout
    return entry
  # No verdict file means the child never got to write one. Say what
  # it was doing rather than only that it failed: the last lines of
  # its own output are the whole diagnosis for a crash in C.
  tail = "\n".join((done.stdout + done.stderr).strip().splitlines()[-25:])
  return {"act": ACTS[index][0], "kind": ACTS[index][1], "judged_by": [],
          "findings": [], "comparisons": 0,
          "harness": f"the child died (exit {done.returncode}) without "
                     f"writing a verdict",
          "traceback": tail, "seconds": time.monotonic() - started}


def render(report, seed, spent):
  """Print what was driven, what was compared, and what disagreed.

  Args:
    report: the accumulated per-act records.
    seed: this run's seed, printed so the run can be repeated.
    spent: how long the whole sweep took, in seconds.

  Returns:
    The process exit status: 1 when anything disagreed OR when any
    case failed on its own premise, because a sweep that could not
    drive half its acts is not a clean sweep and must not read as one.
  """
  print()
  print("=" * 70)
  print(f"CONSISTENCY SWEEP  seed {seed}  {spent:.0f}s")
  print("=" * 70)
  compared = sum(e["comparisons"] for e in report)
  findings = [e for e in report if e["findings"]]
  faults = [e for e in report if e["harness"]]
  for entry in report:
    if entry["harness"]:
      mark = "HARNESS"
    elif entry["findings"]:
      mark = "DISAGREE"
    else:
      mark = "clean"
    print(f"\n{mark:9} [{entry['kind']}] {entry['act']}  "
          f"({entry['comparisons']} comparisons, {entry['seconds']:.0f}s)")
    print(f"          judged by: {', '.join(entry['judged_by']) or 'nothing'}")
    if entry["harness"]:
      print(f"          MY OWN FAULT: {entry['harness']}")
      # The last few lines of what the child said, because a death in
      # C leaves an exit status and two empty streams unless somebody
      # kept them: a failure message that names only the assertion it
      # reached says nothing a reader can act on.
      for line in (entry.get("traceback") or "").strip().splitlines()[-6:]:
        print(f"            | {line}")
    for finding in entry["findings"]:
      print(f"          - {finding['element']}: {finding['fact']}")
      for store, value in finding["said"].items():
        print(f"              {store}: {value!r}")
  print()
  print("-" * 70)
  print(f"{len(report)} acts driven, {compared} comparisons made")
  print(f"{len(findings)} act(s) with disagreements, "
        f"{len(faults)} harness fault(s) of my own")
  if not compared:
    print("NOTHING WAS COMPARED, which is not a clean run: a sweep that "
          "compared nothing is the same green as one that found nothing.")
    return 1
  return 1 if (findings or faults) else 0


def main():
  """Parse the arguments and run the sweep.

  Returns:
    A process exit status: 0 only when every act was driven and every
    invariant held.
  """
  parser = argparse.ArgumentParser(
    description="Drive a session's ordinary acts and read every store "
                "that holds the answer.",
    epilog="Run it under QGIS's own Python: "
           "python3 tools/hunt_probe.py --run tools/consistency_sweep.py")
  parser.add_argument("--seed", type=int, default=None,
                      help="the seed for substitutions this run has to "
                           "make (a ramp a fresh QGIS does not carry); "
                           "printed on every run either way")
  parser.add_argument("--act", action="append", default=None,
                      help="drive only acts whose name contains this; "
                           "may be given more than once")
  parser.add_argument("--kind", choices=("control", "qgis", "boundary"),
                      default=None, help="drive only acts of this kind")
  parser.add_argument("--list", action="store_true",
                      help="print the acts and stop")
  parser.add_argument("--one", type=int, default=None,
                      help="drive ONE act by index and write its verdict "
                           "to --json; this is how the sweep runs each "
                           "act in a process of its own, and is not "
                           "meant to be typed")
  parser.add_argument("--json", default=None,
                      help="where --one writes its verdict")
  args = parser.parse_args()

  if args.list:
    for index, act in enumerate(ACTS):
      print(f"{index:3}  [{act[1]:8}] {act[0]}")
    return 0

  seed = args.seed if args.seed is not None else random.randrange(1 << 30)

  # ---- the child half: one act, one process, one verdict
  if args.one is not None:
    app = start_qgis()
    harness = Harness()
    # A modal QMessageBox blocks a headless run outright, so the
    # suite's own suppression is installed before any dialog is built.
    # Its recorder is also the second of the two stores a refusal can
    # land in, which `press_save` reads. The stack dumps are what turn
    # a death in C into a named call.
    harness.suite._quieten_the_offscreen_platform()
    harness.suite._no_modal_dialogs()
    harness.suite._enable_stack_dumps()
    report = []
    run_act(harness, ACTS[args.one], seed, report)
    if args.json:
      with open(args.json, "w", encoding="utf-8") as handle:
        json.dump(report[0], handle, default=repr)
    app.exitQgis()
    return 0

  # ---- the parent half: spawn one child per act and gather them
  import tempfile
  wanted = []
  for index, act in enumerate(ACTS):
    if args.kind and act[1] != args.kind:
      continue
    if args.act and not any(fragment.lower() in act[0].lower()
                            for fragment in args.act):
      continue
    wanted.append(index)

  print(f"[consistency_sweep] seed {seed}  tree {ROOT}")
  print(f"[consistency_sweep] {len(wanted)} act(s) of {len(ACTS)}, "
        f"each in a process of its own")
  report = []
  started = time.monotonic()
  where = tempfile.mkdtemp(prefix="weavingspace_sweep_verdicts_")
  for index in wanted:
    print(f"\n---- {ACTS[index][0]}")
    entry = one_act_in_a_child(index, seed, where)
    report.append(entry)
    print(f"     {'HARNESS' if entry['harness'] else len(entry['findings'])} "
          f"| {entry['comparisons']} comparisons | "
          f"{entry['seconds']:.0f}s")
  return render(report, seed, time.monotonic() - started)


if __name__ == "__main__":
  sys.exit(main())
