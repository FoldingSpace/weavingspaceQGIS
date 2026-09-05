"""How often does a topology build never get an answer, and what does
QGIS's task manager hold when it does not?

    cd "<the checkout>"
    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \\
      | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    PYTHONHOME="$QGIS_PYTHONHOME" QT_QPA_PLATFORM=offscreen \\
      PYTHONUNBUFFERED=1 "$QGIS_PY" tools/probes/how_often_a_build_never_starts.py

WS_ATTEMPTS sets how many times to try (default 8); WS_ROOT names the
checkout to drive, so the same instrument answers on two trees.

WHAT IT WAS WRITTEN FOR. The sharded suite of 2026-09-04 reported one
cell of the topology matrix failing -- "the tab neither built a
topology nor said why not" -- and this is what settled what that
actually was. Driven alone the panel waits with `_topology_task` set,
QGIS's manager holding one task reading `Queued`, and the global thread
pool reading `active=0`: the build was handed over and never started,
which is neither a slow build nor a worker holding a thread.

IT REPORTS A RATE RATHER THAN A VERDICT, deliberately. The stall
appeared 4 times in 86 attempts here, clustered in one twenty-minute
window, and then not at all in a run of 30 -- so a probe that stops at
its first clean attempt measures the machine's mood, and a two-arm
comparison drawn from a handful of attempts says nothing at all. This
project made that mistake with this very defect and the correction is
in ROADMAP.md.

AND IT CARRIES THE DISCRIMINATOR that decides who owns the stall: at
the failure it adds a SECOND task and reads whether the stuck one then
starts. If it does, QGIS merely never re-ran its queue; if it does not,
the manager is refusing that task, which is a different fault with a
different owner. That question is still OPEN -- the stall has not been
caught with this armed -- which is why the instrument is committed
rather than thrown away.
"""

import faulthandler, importlib.util, os, sys, threading, time

ROOT = os.environ.get(
    "WS_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ATTEMPTS = int(os.environ.get("WS_ATTEMPTS", "8"))
sys.path.insert(0, ROOT)
spec = importlib.util.spec_from_file_location(
    "rt", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

from qgis.core import QgsApplication, QgsProject, QgsTask
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
app = QgsApplication([], True)
app.initQgis()
rt._enable_stack_dumps()
rt._no_modal_dialogs()

STATUS = {getattr(QgsTask, n): n for n in
          ("Queued", "OnHold", "Running", "Complete", "Terminated")
          if hasattr(QgsTask, n)}


def manager_state():
  """What QGIS's own task manager holds. A `_topology_task` set and
  never cleared has three shapes needing three repairs, and only the
  manager tells them apart."""
  tm = QgsApplication.taskManager()
  rows = []
  for task in tm.tasks():
    try:
      rows.append(f"{task.description()!r} "
                  f"{STATUS.get(task.status(), task.status())}")
    except RuntimeError:
      rows.append("<deleted task wrapper>")
  return (f"count={tm.count()} active={tm.countActiveTasks()} "
          + ("; ".join(rows) or "no tasks"))


print(f"driving {ROOT}")
print(f"CONTENTION={rt.CONTENTION}  attempts={ATTEMPTS}")

shapes = rt._topology_matrix_shapes()
wanted = [s for s in shapes if s[1] == "crosses 4"]
assert wanted, f"PREMISE: 'crosses 4' is not among the shapes {shapes}"
(label, family, n) = wanted[0]
print(f"shape under test: {label!r}, index {shapes.index(wanted[0])} of "
      f"{len(shapes)}")

layer = rt.make_region_layer()
QgsProject.instance().addMapLayer(layer)
from weavingspace_qgis.dialog import WeavingSpaceDialog
from weavingspace_qgis import dialog as dialog_module

never, verdicts, alive = 0, [], []
with rt._temp_dir() as td:
  for attempt in range(1, ATTEMPTS + 1):
    dlg = WeavingSpaceDialog(iface=rt._Iface())
    alive.append(dlg)
    try:
      dlg.live_check.setChecked(False)
      dlg.opt_experimental.setChecked(True)
      dlg.show()
      rt._tick(200)
      dlg.n_spin.setValue(int(n))
      rt._tick(200)
      if not (dlg.family_combo.findData(family) >= 0
              or dlg.family_combo.findText(family) >= 0):
        verdicts.append("SKIPPED (chooser offers no such family)")
        continue
      rt._choose_family(dlg, family)
      rt._tick(300)
      began = time.monotonic()
      rt._settle_topology(dlg)
      answered = rt._wait_for_the_topology(dlg)
      took = time.monotonic() - began
      if not answered:
        never += 1
        print(f"\n  attempt {attempt}: NEVER ANSWERED after {took:.1f}s")
        print(f"    live dialog is this one? "
              f"{dialog_module._live_dialog() is dlg}")
        print(f"    dialog: task="
              f"{getattr(dlg, '_topology_task', None) is not None} "
              f"wanted={bool(getattr(dlg, '_topology_wanted', False))} "
              f"built_for={getattr(dlg, '_topology_built_for', None)!r}")
        print(f"    manager: {manager_state()}")
        print(f"    every dialog so far, topology task set?: "
              f"{[getattr(d, '_topology_task', None) is not None for d in alive]}")
        print(f"    every dialog so far, TILING task set?: "
              f"{[getattr(d, '_task', None) is not None for d in alive]}")
        # A TASK THAT STAYS Queued MEANS NOTHING RAN IT, so the
        # question is what is holding the pool. QGIS's task manager
        # runs its work on the global QThreadPool, and a worker that
        # never returns is invisible in the manager's own count.
        from qgis.PyQt.QtCore import QThreadPool
        pool = QThreadPool.globalInstance()
        print(f"    global thread pool: active={pool.activeThreadCount()} "
              f"max={pool.maxThreadCount()}")
        print(f"    python threads: "
              f"{[th.name for th in threading.enumerate()]}")
        # THE DECISIVE READING: what every thread is actually doing.
        # A stack naming the vendored tiling says the worker never came
        # back, which is a different defect from a manager that will
        # not schedule.
        # WHOSE TASK IS THE QUEUED ONE, and does the manager still
        # own it? A dialog holding a task the manager has forgotten is
        # a different defect from a manager refusing to start one it
        # holds, and only identity tells them apart.
        tm = QgsApplication.taskManager()
        mine = getattr(dlg, "_topology_task", None)
        try:
          tid = tm.taskId(mine) if mine is not None else None
        except Exception as exc:                        # noqa: BLE001
          tid = f"<taskId raised {exc}>"
        print(f"    the dialog's own task: id={tid} "
              f"status={STATUS.get(mine.status(), mine.status()) if mine is not None else None} "
              f"is-in-manager={any(x is mine for x in tm.tasks())}")
        if hasattr(tm, "dependenciesSatisfied") and isinstance(tid, int):
          print(f"    dependenciesSatisfied({tid}) = "
                f"{tm.dependenciesSatisfied(tid)}")
        # THE DISCRIMINATOR: does adding ANOTHER task start this one?
        # QGIS runs its queue on task-manager events, so if a second
        # add unsticks the first, the manager merely never re-ran its
        # queue -- a scheduling stall. If it does not, the manager is
        # REFUSING this task, which is a different fault with a
        # different owner.
        from qgis.core import QgsTask as _QgsTask
        class _Nudge(_QgsTask):
          def run(self):
            return True
        nudge = _Nudge("weavingspace stall nudge")
        tm.addTask(nudge)
        for _ in range(15):
          rt._tick(200)
          time.sleep(0.4)
          if mine is not None and mine.status() != 0:
            break
        print(f"    after adding a second task: this one is "
              f"{STATUS.get(mine.status(), mine.status()) if mine is not None else None}"
              f"; {manager_state()}")
        print("    ---- every thread's stack ----")
        sys.stdout.flush()
        faulthandler.dump_traceback(file=sys.stdout, all_threads=True)
        sys.stdout.flush()
        print("    ---- end of stacks ----")
        # is it never, or merely slow? wait far past the ceiling
        for _ in range(60):
          rt._tick(200)
          time.sleep(0.8)
          panel = dlg.topology_panel
          if panel._topology is not None or (panel.note.text() or "").strip():
            break
        print(f"    after {time.monotonic() - began:.0f}s in all: "
              f"_topology={dlg.topology_panel._topology is not None} "
              f"| {manager_state()}")
        verdicts.append(f"NEVER ANSWERED ({took:.1f}s)")
        continue
      verdict, detail = rt._topology_matrix_cell(
        dlg, "rotate_edge", "after re-Generate", td)
      verdicts.append(f"{verdict} ({took:.1f}s to answer)")
      print(f"  attempt {attempt}: {verdict}  [answered in {took:.2f}s] "
            f"| {manager_state()}")
    finally:
      dlg.close()
      for other in list(QgsProject.instance().mapLayers().values()):
        if other is not layer:
          QgsProject.instance().removeMapLayer(other.id())

print(f"\nRATE: {never} of {ATTEMPTS} attempts never got an answer")
for i, v in enumerate(verdicts, 1):
  print(f"  {i}: {v}")
print("SENTINEL: probe finished, every attempt reported")
sys.stdout.flush()
os._exit(0)
