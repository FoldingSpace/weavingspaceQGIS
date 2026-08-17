"""What ONE interaction with this dialog costs, in a tree of your choosing.

The tester's complaint is not that a release made a run slower. It is
that the plugin USED TO BE easy to iterate with and no longer feels
that way -- a drift across versions, in the interactive loop rather
than in Generate. A per-run profile answers a different question, and
this project has already taken that measurement and found the Python
side flat to within 0.09%.

So this measures a TICK: nudge one control, let the dialog's own
debounce fire, and see what that costs. Nobody has ever measured what
one interaction costs here, which is why ABSOLUTE figures are printed
first and comparisons second. A loop can be slow without any release
having made it slower, and this project has already found one such
thing by accident -- a ramp swatch redrawn 306,558 times in a single
test, uncached since it was written.

FOUR TICKS, chosen because they are what somebody iterating actually
does: nudge a design number, change a design number that forces the
weave unit to be rebuilt, pick a different ramp, and rebuild the
table. Each is driven through the CONTROL'S OWN SIGNAL and then given
only the dialog's own debounce, because setting a value directly and
calling the handler yourself measures a path no user is on.

WHAT TO READ, in this order. The absolute wall and CPU per tick, which
is what a person feels. Then the call count, which is the figure that
survives profiler overhead -- on 2026-08-16 a self-time ratio
understated a threefold difference as 1.2x while the counts carried it
exactly. Then, if you are comparing two trees, the per-function counts
through `compare_profiles.py`, which keys on (file, function) and
never on line numbers.

Run it in each tree with the same PERF_TICKS, and mind that the two
trees must be measured on a QUIET machine: this reports CPU as well as
wall precisely so a busy machine announces itself as a gap between
them.

Env: WEAVINGSPACE_REPO (which tree to measure), PERF_OUT (optional,
where to dump the profile for compare_profiles.py), PERF_TICKS (how
many of each tick, default 10).
"""
import cProfile
import importlib.util
import os
import pstats
import sys
import time

REPO = os.environ["WEAVINGSPACE_REPO"]
OUT = os.environ.get("PERF_OUT")
TICKS = int(os.environ.get("PERF_TICKS", "10"))
os.chdir(REPO)
sys.path.insert(0, REPO)

spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

from qgis.core import QgsApplication, QgsProject            # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()
T._no_modal_dialogs()

SETTLE = 500          # ms: past the 350 preview debounce and the 900 live one
# What each live tick actually did: (a task was seen, tiles before,
# tiles after, element layers). Printed rather than trusted --
# a live tick that never ran a tiling costs almost nothing and
# reads exactly like a tree that is simply faster.
LIVE_EVIDENCE = []


def build():
  """A dialog on a region layer, live update off, ready to be nudged.

  Args:
    None; the fixture is decided by PERF_EXTRA_LAYERS in the
    environment, described below.

  Returns:
    The open dialog. Live update is OFF deliberately: it fires a whole
    tiling run on a 900 ms debounce, and a run is the thing this probe
    exists NOT to measure.

  PERF_EXTRA_LAYERS fills the project with that many further layers
  before the dialog opens, and it is the more interesting setting. A
  fixture of four or five layers cannot show a cost that rises with
  how big somebody's project is -- `QgsProject.findLayer` walks the
  layer tree, and several of this plugin's lookups ask it once per
  layer id per interaction. Whether that matters is a question about
  a REAL project, and the way to answer it is to build one.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  project.clear()
  T._tick(100)
  layer = T.make_region_layer(n=6)
  project.addMapLayer(layer)
  for i in range(int(os.environ.get("PERF_EXTRA_LAYERS", "0"))):
    decoy = T.make_region_layer(n=2)
    decoy.setName(f"decoy {i}")
    project.addMapLayer(decoy)
  dlg = WeavingSpaceDialog(iface=T._Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  T._tick(SETTLE)
  return dlg


def nudge_a_number(dlg, i):
  """Step the offset angle, which redraws the preview and nothing else.

  Args:
    dlg: the open dialog.
    i: which tick this is; its parity decides whether the step goes up
      or down, so the value oscillates rather than drifting off the
      control's range over a long run.

  Returns:
    None, which the caller reads as "the tick happened".
  """
  box = dlg.opt_offset_angle
  box.setValue(box.value() + (1 if i % 2 == 0 else -1))
  T._tick(SETTLE)


def nudge_the_unit(dlg, i):
  """Step the tile inset, which rebuilds the weave unit itself.

  Args:
    dlg: the open dialog.
    i: which tick this is; parity alternates the step, as above.

  Returns:
    None, which the caller reads as "the tick happened".
  """
  box = dlg.mod_t_inset
  box.setValue(box.value() + (1 if i % 2 == 0 else -1))
  T._tick(SETTLE)


def pick_a_ramp(dlg, i):
  """Choose a different ramp on the first row that offers one.

  Args:
    dlg: the open dialog.
    i: which tick this is; it picks the ramp, cycling through four so
      each tick is a real change.

  Returns:
    True when a ramp was picked, False when no row offered one -- and
    the caller stops on False rather than averaging a tick that never
    happened in as a cheap one.
  """
  ramps = ("Reds", "Blues", "Greens", "Purples")
  for row in range(dlg.table.rowCount()):
    for column in range(dlg.table.columnCount()):
      widget = dlg.table.cellWidget(row, column)
      if widget is None or not hasattr(widget, "findText"):
        continue
      wanted = widget.findText(ramps[i % len(ramps)])
      if wanted < 0:
        continue
      widget.setCurrentIndex(wanted)
      widget.activated.emit(wanted)          # what a click emits
      T._tick(SETTLE)
      return True
  return False


def rebuild_the_table(dlg, _i):
  """Re-point the layer chooser at the same layer, which rebuilds.

  Args:
    dlg: the open dialog.
    _i: which tick this is, unused -- setting the chooser to nothing
      and back is the same act every time.

  Returns:
    True, so the caller counts the tick.
  """
  layer = dlg.layer_combo.currentLayer()
  dlg.layer_combo.setLayer(None)
  dlg.layer_combo.setLayer(layer)
  T._tick(SETTLE)
  return True


def nudge_with_live_update(dlg, i):
  """The tick a real user makes: nudge a control with live update ON.

  Args:
    dlg: the open dialog, already carrying output from a Generate.
    i: which tick this is; only its parity is used, to step the
      control up and down alternately so every nudge is a genuine
      change rather than a no-op the run signature would skip.

  Returns:
    True, always, so the caller counts the tick. What the tick
    actually DID is appended to `LIVE_EVIDENCE` instead, because a
    tick that ran no tiling costs almost nothing and would otherwise
    read as a tree that is simply faster.

  This is the honest configuration and the expensive one. Live update
  is what every user has, and it turns a nudge into a whole tiling run
  behind a 900 ms debounce -- so "easy to iterate with" lives here and
  not in the preview redraw the other ticks measure. The wait is on
  the RUN ENDING rather than on a number of seconds, because a fixed
  sleep measures the sleep on a fast machine and truncates the work on
  a slow one.
  """
  project = QgsProject.instance()
  before = {lid: project.mapLayer(lid).featureCount()
            for lid in dict(dlg._element_layer_ids).values()
            if project.mapLayer(lid) is not None}
  dlg.live_check.setChecked(True)
  box = dlg.mod_t_inset
  box.setValue(box.value() + (1 if i % 2 == 0 else -1))
  deadline = time.monotonic() + 120
  seen = False
  # WATCH FOR THE TASK WHILE THE DEBOUNCE IS STILL RUNNING, in short
  # steps rather than one long one. A single `_tick(1000)` can carry a
  # whole quick run inside it, so the wait loop afterwards sees no
  # task and the tick reports as though nothing ran -- which is how a
  # tree that IS doing the work comes out looking free.
  for _ in range(14):
    T._tick(100)
    if getattr(dlg, "_task", None) is not None:
      seen = True
  while getattr(dlg, "_task", None) is not None \
      and time.monotonic() < deadline:
    seen = True
    T._tick(100)
  T._tick(200)                                # the landing is main-thread
  dlg.live_check.setChecked(False)
  after = {lid: project.mapLayer(lid).featureCount()
           for lid in dict(dlg._element_layer_ids).values()
           if project.mapLayer(lid) is not None}
  LIVE_EVIDENCE.append((seen, sum(before.values()), sum(after.values()),
                        len(after)))
  return True


def time_one(name, action, dlg, ticks):
  """Drive one kind of tick `ticks` times and report what it cost.

  Args:
    name: what to call it in the printout.
    action: a callable taking (dialog, index); anything falsy it
      returns means the tick did not happen.
    dlg: the open dialog.
    ticks: how many times to drive it.

  Returns:
    (name, done, wall_ms, cpu_ms) with the two figures PER TICK, or
    (name, 0, 0, 0) when nothing could be driven -- which the caller
    prints rather than hides, because an axis that never ran is
    indistinguishable from one that is free.

  The dialog's own debounce wait is subtracted from neither figure.
  That is deliberate: wall clock includes the wait and is therefore
  useless on its own, which is exactly why CPU is printed beside it.
  """
  action(dlg, 0)                              # warm, uncounted
  wall = time.monotonic()
  cpu = time.process_time()
  done = 0
  for i in range(ticks):
    if action(dlg, i + 1) is False:
      break
    done += 1
  wall = (time.monotonic() - wall) * 1000.0
  cpu = (time.process_time() - cpu) * 1000.0
  if not done:
    return (name, 0, 0.0, 0.0)
  return (name, done, wall / done, cpu / done)


def main():
  """Absolute cost first, then the profile, then the totals."""
  dlg = build()
  print(f"tree: {REPO}")
  # THE PREMISE, PRINTED. A probe that quietly failed to build the
  # project it claims to measure reports "no effect" and looks exactly
  # like a measurement, which is the more dangerous of the two ways a
  # probe can be wrong.
  print(f"layers in the project: "
        f"{len(QgsProject.instance().mapLayers())} "
        f"(asked for {int(os.environ.get('PERF_EXTRA_LAYERS', '0')) + 1})")
  print(f"nodes in the layer tree: "
        f"{len(QgsProject.instance().layerTreeRoot().findLayerIds())}")
  print(f"elements in the table: {dlg.table.rowCount()}, "
        f"spacing {dlg.spacing_spin.value()}")
  print(f"\n{'tick':<28}{'ticks':>6}{'wall ms':>10}{'cpu ms':>10}")
  measured = []
  for name, action in (("nudge a design number", nudge_a_number),
                       ("nudge the weave unit", nudge_the_unit),
                       ("pick a different ramp", pick_a_ramp),
                       ("rebuild the table", rebuild_the_table)):
    row = time_one(name, action, dlg, TICKS)
    measured.append(row)
    if not row[1]:
      print(f"{name:<28}{'NOT DRIVEN -- read nothing from this line':>26}")
      continue
    print(f"{name:<28}{row[1]:>6}{row[2]:>10.1f}{row[3]:>10.1f}")

  # ...and the expensive one, separately and fewer times, because it
  # runs a whole tiling and is the tick a real user actually makes
  live = int(os.environ.get("PERF_LIVE_TICKS", "3"))
  if live:
    # A DIALOG OF ITS OWN, AND ONE EXPLICIT GENERATE FIRST. Both were
    # learned the hard way on 2026-08-17. The four ticks above leave
    # the dialog in a state where v0.24.0 produced no output at all,
    # so the live tick timed a debounce there and a whole tiling here
    # and the comparison read 3.6x while the two were not doing the
    # same thing. And live update itself differs between the trees --
    # 0.24.0 waits for a first Generate where a later version renders
    # as soon as a layer and its variables are in place -- so the
    # Generate is driven explicitly in both. The evidence lines below
    # exist so neither can recur silently.
    dlg.close()
    dlg = build()
    T._generate_and_wait(dlg)
    T._tick(SETTLE)
    row = time_one("nudge, live update ON", nudge_with_live_update,
                   dlg, live)
    measured.append(row)
    print(f"{row[0]:<28}{row[1]:>6}{row[2]:>10.1f}{row[3]:>10.1f}")
    ran = sum(1 for seen, _b, _a, _n in LIVE_EVIDENCE if seen)
    moved = sum(1 for _s, b, a, _n in LIVE_EVIDENCE if b != a)
    print(f"    of {len(LIVE_EVIDENCE)} live ticks, {ran} ran a task "
          f"and {moved} changed the tile count")
    print(f"    tiles per tick: "
          f"{[a for _s, _b, a, _n in LIVE_EVIDENCE]} "
          f"across {LIVE_EVIDENCE[-1][3] if LIVE_EVIDENCE else 0} layers")
    if not ran:
      print("    READ NOTHING FROM THE LINE ABOVE: no tiling ran, so "
            "it timed a debounce and not a run")

  # ...and the same ticks again under the profiler, for the counts
  profiler = cProfile.Profile()
  profiler.enable()
  for _name, action in (("a", nudge_a_number), ("b", nudge_the_unit),
                        ("c", pick_a_ramp), ("d", rebuild_the_table)):
    for i in range(TICKS):
      action(dlg, i + 1)
  profiler.disable()
  stats = pstats.Stats(profiler)
  print(f"\ncalls across {TICKS} of each tick: {stats.total_calls}")
  if OUT:
    # dumped HERE: these harnesses end in os._exit, and cProfile's own
    # dump happens at interpreter shutdown, which never arrives
    profiler.dump_stats(OUT)
    print(f"wrote {OUT}")
  print("\nThe wall figures include the dialog's own 350 ms debounce "
        "wait,\nso read CPU for what the machine actually did and "
        "wall for what\na person waits. A gap between them that grows "
        "between trees is\ncontention, not the plugin.")
  dlg.close()


main()
