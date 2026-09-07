"""Which stall shapes can a `Running` task, an idle pool and a thread
list actually tell apart?

The R-4 recurrence of 2026-09-07 was diagnosed from three readings taken
at the stall -- the manager holding its task `Running`, the global
QThreadPool at `active=0`, and no worker in a thread dump -- and
characterised as "QGIS marked a build Running and never ran a worker for
it". That characterisation assumes two things about QGIS which nobody
had asked QGIS: that a task whose `run()` has RETURNED stops reading
`Running`, and that a live task worker shows up in the pool count and
the thread list. Both assumptions decide the recovery, since a build
that never started wants cancel-and-rebuild while a build that finished
and was never handed back wants delivering, and cancelling that one
throws a completed result away.

FOUR ARMS, each reading from the main thread with the event loop
deliberately NOT pumped, so the main-thread completion cannot have been
delivered and the readings are the ones a stall would show:

    A  added, before anything is pumped
    B  the worker is INSIDE run(), proved by a flag it sets on entry
    C  run() has RETURNED, proved by a flag it sets last, and
       `finished()` has provably not run
    D  pumped until it lands -- the control, which is what says the
       instrument can move at all

Run it with the checkout on the path:

    WS_ROOT="$PWD" PYTHONPATH="$PWD" QT_QPA_PLATFORM=offscreen \
      "$QGIS_PY" tools/probes/what_a_running_task_reading_can_tell_apart.py

WHAT IT FOUND on QGIS 4.0.3, macOS, 2026-09-07. Arm C reads `Running`:
the status moves to `Complete` only when the main thread delivers the
callback, so the recorded reading is consistent with BOTH shapes and
names neither. Arm B reads `active=0` and `['MainThread']` with a worker
demonstrably live, so those two readings prove nothing in any arm --
QGIS's task workers do not go through the pool Python can see, and a
foreign Qt thread is not a `threading` thread. Only the faulthandler
dump separates B from C, two thread blocks against one. The corrections
this forced are in ROADMAP.md under "Later, or never" and in
docs/TOPOLOGY.md's record of 2026-09-04.
"""
import faulthandler
import os
import sys
import threading
import time

sys.path.insert(0, os.environ.get("WS_ROOT", os.getcwd()))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qgis.core import QgsApplication, QgsTask       # noqa: E402
from qgis.PyQt.QtCore import QThreadPool            # noqa: E402

STATUSES = ("Queued", "OnHold", "Running", "Complete", "Terminated")


def name_of(status) -> str:
  """Name a QgsTask status code.

  Args:
    status: what `QgsTask.status()` returned.

  Returns:
    The status's own name, or the bare code in angle brackets where
    this QGIS spells the enum differently -- a probe that cannot name a
    code must still print it, since an unnamed number is the reading.
  """
  for label in STATUSES:
    if hasattr(QgsTask, label) and getattr(QgsTask, label) == status:
      return label
  return f"<{status}>"


class HeldTask(QgsTask):
  """A task whose worker announces entry to and exit from `run()`.

  Args (to the constructor):
    hold: a `threading.Event` the worker waits on inside `run()`, so
      the main thread decides when the work finishes and can therefore
      read the status on either side of that moment.

  The two flags are what make the arms honest: without them "the worker
  has finished" is an assumption about timing, which is the shape of
  reasoning this probe exists to replace.
  """

  def __init__(self, hold):
    super().__init__("probe", QgsTask.CanCancel)
    self.entered = threading.Event()
    self.returned = threading.Event()
    self.finished_called = False
    self._hold = hold

  def run(self):                                    # worker thread
    """Announce entry, wait to be released, announce the return."""
    self.entered.set()
    self._hold.wait(20.0)
    self.returned.set()
    return True

  def finished(self, ok):                           # main thread
    """Record that the completion was delivered."""
    self.finished_called = True


def line(arm: str, task: HeldTask, pool) -> str:
  """Compose one arm's reading.

  Args:
    arm: the arm's label and what is true in it.
    task: the task being read.
    pool: the global QThreadPool, read for the count that turns out to
      mean nothing.

  Returns:
    One line naming every reading, since a report that says which
    branch it reached and not what it found buys nothing.
  """
  return (f"{arm:<34} status={name_of(task.status()):<9} "
          f"pool.active={pool.activeThreadCount()} "
          f"threading={[t.name for t in threading.enumerate()]} "
          f"entered={task.entered.is_set()} "
          f"returned={task.returned.is_set()} "
          f"finished_called={task.finished_called}")


def main() -> int:
  """Run the four arms and print a reading apiece.

  Returns:
    0. The probe reports; judging what the readings mean is the
    reader's, and the docstring above carries what they meant here.
  """
  QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", ""), True)
  app = QgsApplication([], False)
  app.initQgis()

  hold = threading.Event()
  task = HeldTask(hold)
  pool = QThreadPool.globalInstance()
  print(f"pool max={pool.maxThreadCount()}")

  QgsApplication.taskManager().addTask(task)
  print(line("A  just added", task, pool))

  # The manager wants a turn of the event loop to dispatch. Give it
  # turns until the worker says it is in, then stop pumping for the
  # rest of the run, so nothing can deliver the completion behind us.
  deadline = time.monotonic() + 10.0
  while not task.entered.is_set() and time.monotonic() < deadline:
    app.processEvents()
    time.sleep(0.01)
  print(line("B  worker INSIDE run()", task, pool))
  print("B  the dump, which is the reading that CAN tell B from C:")
  faulthandler.dump_traceback(file=sys.stdout, all_threads=True)

  # Let run() return, and do not pump: `finished()` cannot have been
  # delivered, which is the whole of arm C's claim.
  hold.set()
  task.returned.wait(10.0)
  time.sleep(1.5)                    # the worker thread is long gone
  print(line("C  run() RETURNED, no pump", task, pool))
  print("C  the dump again:")
  faulthandler.dump_traceback(file=sys.stdout, all_threads=True)

  for _ in range(400):
    app.processEvents()
    time.sleep(0.01)
    if task.finished_called:
      break
  print(line("D  pumped (the control)", task, pool))

  sys.stdout.flush()
  # THROUGH `os._exit`, as this project's other QGIS probes do: an
  # orderly interpreter shutdown under a live QgsApplication is its
  # own source of noise, and the readings are already printed.
  os._exit(0)


if __name__ == "__main__":
  main()
