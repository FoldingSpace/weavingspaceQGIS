"""Everything a probe needs before it can ask its first question.

A probe is a small script that drives the plugin to answer ONE
question: does this claim reproduce, what does the file hold, which
gate refused. Hunts write dozens of them and so does anybody verifying
a hunt's claim. An audit on 2026-08-15 counted 373 one-shot probe
scripts in a single session, median 79 lines, of which roughly forty
were the same boilerplate re-typed: standing up QGIS, a project and a
dialog. This module is that forty lines, written once.

WHY IT IS A CORRECTNESS TOOL AND NOT A CONVENIENCE. The same audit
found ELEVEN hand-written wrappers all setting `QGIS_PREFIX_PATH` to a
doubled path that leaves QGIS unable to find its style database, so
those hunts probed a QGIS with no colour ramps and none of them knew.
A shared harness is wrong once instead of eleven times, and is fixed
for every future probe the day somebody understands the fault. The
round of 2026-08-28 produced four more of the same kind in one evening
-- a modal shim never installed, a message store read after the helper
that clears it, a context manager garbage-collected out from under an
open GeoPackage, and a fixture that forced the defect into its own
control arm. Each is prevented here, at the line, with the measurement
that found it.

USE IT LIKE THIS::

    from tools.probe_kit import start
    probe = start()                      # QGIS, an empty project, shims
    dlg, layer, tile_id = probe.dialog() # a categorical map to drive
    probe.generate(dlg)
    path = probe.path("map.gpkg")
    assert probe.save(dlg, path), "PREMISE: the save failed"
    print(probe.said(dlg))               # both message stores
    print(probe.tables(path))            # read without OGR or QGIS

Run it with QGIS's own interpreter, which is what `$QGIS_PY` names,
and put the checkout on the path so this module can be found::

    cd "<the checkout>"
    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \\
      | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 "$QGIS_PY" my_probe.py

`PYTHONPATH` is needed because `start()` cannot put the checkout on
the path in time for its own import; everything after that it does
for you. `PYTHONUNBUFFERED=1` is not decoration either: the suite ends
through `os._exit`, so a buffered line never reaches a pipe and a run
that printed nothing looks exactly like a run that passed. The
platform is set to offscreen by `start()` itself.
"""

import contextlib
import importlib.util
import os
import sqlite3
import sys


def _repo_root() -> str:
  """The checkout this probe is running against.

  Returns:
    An absolute path. `WS_REPO` wins where it is set, so a probe can
    be pointed at a frozen copy made by `tools/hunt_probe.py`;
    otherwise the directory holding this file's parent, which is the
    checkout it was imported from.

  Deriving it rather than accepting the current directory is
  deliberate: a probe that reads one tree and drives another reports
  fiction, and this project has spent whole rounds confirming defects
  in a commit a fix had already landed on top of.
  """
  named = os.environ.get("WS_REPO")
  if named:
    return os.path.abspath(named)
  return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Probe:
  """A QGIS application, an empty project, and the shims a probe needs.

  Attributes:
    suite: the loaded `tests/run_tests.py` module, so a probe can use
      the fixtures and helpers the suite already has rather than
      inventing near-copies of them.
    project: the one `QgsProject` instance everything shares.
    folder: a temporary directory that lives as long as this object.

  Build one with `start()` rather than by hand; the constructor
  assumes the application is already up.
  """

  def __init__(self, suite, project, folder, holder):
    self.suite = suite
    self.project = project
    self.folder = folder
    self._holder = holder

  def path(self, name: str) -> str:
    """A path inside this probe's own temporary directory.

    Args:
      name: the file name, e.g. ``"map.gpkg"``.

    Returns:
      An absolute path. The directory is held open for the probe's
      whole life -- see `start`, where the reason is written.
    """
    return os.path.join(self.folder, name)

  def dialog(self, **kwargs):
    """A dialog over the suite's categorical fixture, ready to drive.

    Args:
      **kwargs: passed straight to the suite's `_categorical_dialog`.

    Returns:
      ``(dialog, region layer, tile id)``, with live update switched
      OFF and the project otherwise empty.

    LIVE UPDATE IS LEFT OFF HERE AND THAT IS A DECISION TO REVISIT PER
    PROBE. It is ON by default in the product, and a whole family of
    resume tests was found on 2026-08-28 to be driving a setting no
    user holds -- which hid a defect that emptied a saved file. Where
    a probe is about what a person meets, tick it back on and say so.
    """
    dlg, layer, tile_id = self.suite._categorical_dialog(**kwargs)
    dlg.live_check.setChecked(False)
    return dlg, layer, tile_id

  def generate(self, dlg, spacing: float = 600.0) -> None:
    """Draw a map and wait for it to land.

    Args:
      dlg: the dialog to drive.
      spacing: map units between repeats. The default is coarse on
        purpose: a probe is almost never about tile COUNT, and a fine
        spacing costs minutes per run for nothing.

    Returns:
      None. Raises AssertionError where nothing was drawn, because a
      probe that goes on to measure an empty map measures nothing and
      says so far too late.
    """
    dlg.spacing_spin.setValue(spacing)
    self.suite._generate_and_wait(dlg)
    assert dlg._element_layer_ids, \
      "PREMISE: the run drew nothing, so there is no map to ask about"

  def save(self, dlg, path: str, overwrite: bool = True) -> bool:
    """Press Save where a person would and say whether anything landed.

    Args:
      dlg: the dialog whose map is being saved.
      path: where it should go. It is also put into the chooser, since
        the button reads the widget rather than any argument.
      overwrite: answer Yes to the question a file the plugin did not
        write raises. Pass False to leave the answer unstaged, which
        is what a probe ABOUT that question wants.

    Returns:
      True where the press wrote something. Raises where the plugin
      reported a save and left no file, or wrote without a word.

    IT GOES THROUGH THE BUTTON, not `_save_the_map`: a control must act
    through its own signal, or the connection could be deleted and
    every probe would go on passing.
    """
    if overwrite:
      from qgis.PyQt.QtWidgets import QMessageBox
      self.suite.MODAL_ANSWERS["question"] = QMessageBox.StandardButton.Yes
    dlg.gpkg_widget.setFilePath(path)
    return self.suite.press_save(dlg, path)

  def said(self, dlg) -> str:
    """Everything the plugin has told the person, from BOTH stores.

    Args:
      dlg: the dialog to read.

    Returns:
      The message bar and the note line joined into one string.

    WHY BOTH. `_report_quietly` writes to the note line when there is
    no iface and to the bar when there is, and a refusal made through
    a QMessageBox reaches neither -- it lands in the modal recorder,
    which `modals` below reads. Reading one store and concluding
    silence is this project's own harness fault eleven, met again by
    somebody who had read the entry describing it.
    AND `press_save` BLANKS BOTH BEFORE IT CLICKS, keeping what it read
    in a local. A probe that reads `BAR_MESSAGES` after calling it sees
    an empty store whatever happened, which cost an hour on 2026-08-28.
    """
    bar = " ".join(str(text) for _kind, text in self.suite.BAR_MESSAGES)
    note = getattr(dlg, "live_note", None)
    return f"{bar} {note.text() if note is not None else ''}".strip()

  def modals(self, last: int = 3):
    """The questions and warnings the plugin raised through a dialog.

    Args:
      last: how many of the most recent to return.

    Returns:
      A list of ``(kind, text)``. A run that appears to have done
      nothing has often refused through one of these, where the
      message bar stays empty.
    """
    return list(self.suite.MODALS[-last:])

  def tables(self, path: str, internals: bool = False) -> list:
    """The tables in a GeoPackage, read without OGR and without QGIS.

    Args:
      path: the .gpkg to read.
      internals: include sqlite's and GeoPackage's own bookkeeping --
        `gpkg_contents`, the `rtree_*` indexes, `sqlite_sequence`.
        Left out by default because a probe asking what a map holds
        does not want thirty index tables in its answer, and a reader
        skimming that answer can miss the one name that matters.

    Returns:
      A sorted list of table names, or an empty list where the file is
      not there.

    IT USES STDLIB SQLITE DELIBERATELY. An instrument that opens the
    file through OGR HOLDS it open, and the next run then fails at the
    sqlite level with "unable to open database file" -- read, on
    2026-08-27, as the product refusing to write. A reading taken with
    a different library from the one under test is also a second route
    rather than the same route twice.
    """
    if not os.path.exists(path):
      return []
    connection = sqlite3.connect(path)
    try:
      rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    finally:
      connection.close()
    names = sorted(name for (name,) in rows)
    if internals:
      return names
    return [name for name in names
            if not name.startswith(("gpkg_", "rtree_", "sqlite_"))]

  def providers(self, dlg) -> list:
    """What each element layer is actually reading from.

    Args:
      dlg: the dialog whose output layers to inspect.

    Returns:
      A sorted list of provider names -- ``["ogr"]`` for a map backed
      by its GeoPackage, ``["memory"]`` for one that has been re-tiled
      into memory, and ``"gone"`` for a layer the project no longer
      holds.

    This is the cheapest way to tell a map that survived a boundary
    from one that was silently redrawn: a memory-backed map looks
    identical on screen and vanishes when the project is reopened.
    """
    return sorted({
      (self.project.mapLayer(lid).dataProvider().name()
       if self.project.mapLayer(lid) is not None else "gone")
      for lid in dlg._element_layer_ids.values()})

  def clear(self) -> None:
    """Empty the project between arms of a probe.

    Returns:
      None.

    Everything shares one `QgsProject`, so a layer left behind changes
    which one the next dialog picks -- the rule the suite states as
    "tests must run with an EMPTY project", and it binds a probe with
    two arms exactly as hard.
    """
    self.project.clear()
    self.suite._tick(300)


def start(quiet: bool = True) -> Probe:
  """Stand up QGIS, an empty project and every shim a probe needs.

  Args:
    quiet: ask Qt not to print its font and threading chatter. It is
      on by default because that noise is read back by whoever is
      reading the probe's output, and none of it has ever been the
      answer to anything.

  Returns:
    A `Probe`.

  WHAT IT INSTALLS, AND WHY EACH ONE EXISTS.

  THE MODAL SHIM. `tests/run_tests.py` installs it in `main()`, so a
  probe that merely IMPORTS the suite gets real QMessageBoxes -- which
  offscreen wait for a click that can never come. That hung a probe for
  eight minutes on 2026-08-28 and a suite for thirty-one on an earlier
  occasion, and the `manyareas` hunt reported it as an instrument fault
  the same evening. It also means a guard that FIRED reads as a guard
  that did not.

  A HELD TEMPORARY DIRECTORY. `_temp_dir()` is a context manager, and a
  probe that calls it without holding the result has its folder swept
  away underneath an open GeoPackage: the save then fails at the sqlite
  level and reads as the product refusing to write. The directory lives
  as long as the returned `Probe`.

  AN EMPTY PROJECT, for the reason in `Probe.clear`.
  """
  root = _repo_root()
  os.chdir(root)
  if root not in sys.path:
    sys.path.insert(0, root)
  if quiet:
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.qpa.*=false")
  os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

  spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(root, "tests", "run_tests.py"))
  suite = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(suite)

  from qgis.core import QgsApplication, QgsProject
  QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  application = QgsApplication([], True)
  application.initQgis()
  # Kept on the module so the C++ side is not collected while a probe
  # is still driving it.
  globals()["_APPLICATION"] = application

  suite._no_modal_dialogs()
  holder = suite._temp_dir()
  folder = holder.__enter__()
  project = QgsProject.instance()
  project.clear()
  return Probe(suite, project, folder, holder)


def moved(before, after, what: str = "the fixture") -> None:
  """Assert that a probe's own setup actually changed something.

  Args:
    before: the reading taken before the act.
    after: the reading taken after it.
    what: what was supposed to move, for the message.

  Returns:
    None. Raises AssertionError where the two are equal.

  THE CHEAPEST GUARD THIS PROJECT KNOWS, and the one its probes keep
  forgetting. A fixture that cannot move cannot show that something
  moved it: a probe multiplied twelve values by ten and reported the
  map ignoring the change, and the twelve were all zero. Another set a
  spin box to a number `decimals` clamps and read the clamp back as a
  loss. Assert the quantity THE CODE READS, not the one you handed it.
  """
  assert before != after, (
    f"PREMISE: {what} did not change ({before!r} both before and "
    f"after), so nothing below can show that it was changed")


@contextlib.contextmanager
def unchanged(probe, path: str):
  """Hold a GeoPackage's contents across an act and report what moved.

  Args:
    probe: the `Probe` whose `tables` reader to use.
    path: the file to watch.

  Yields:
    A dict that gains ``"before"`` immediately and ``"after"`` on exit,
    plus ``"lost"`` and ``"gained"``.

  BYTES ARE NOT A PROPERTY OF AN UNTOUCHED GEOPACKAGE: a Generate after
  a Save leaves every table, count, style and record identical while
  the file grows from 184,320 to 356,352 bytes, because sqlite
  reorganises it as the layers reading it are replaced. Compare what
  the file HOLDS, which is what this does.
  """
  state = {"before": probe.tables(path)}
  yield state
  state["after"] = probe.tables(path)
  state["lost"] = [n for n in state["before"] if n not in state["after"]]
  state["gained"] = [n for n in state["after"] if n not in state["before"]]
