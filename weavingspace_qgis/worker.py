"""Background execution of the tiling computation via QgsTask.

For weavingspace-minded readers: QGIS runs long jobs on its own
thread pool through QgsTask. You subclass it, put the slow work in
``run()`` (which executes on a WORKER thread), and QGIS calls
``finished()`` back on the MAIN thread when the work ends. Only the
main thread may touch the GUI or the project, so the split matters.

The one rule this plugin cannot break: no pyproj/PROJ use inside
``run()``. QGIS links the same PROJ library, and concurrent use
crashes the whole application. The dialog therefore strips CRS from
everything the worker sees and reattaches it in the callback.
"""

from __future__ import annotations

import time

from qgis.core import QgsTask


class TilingTask(QgsTask):
  """One tiling run, off the main thread.

  Args (to the constructor):
    description: the label QGIS shows in its task manager.
    work_fn: callable taking THIS task and returning the result
      (here, the tiled GeoDataFrame). It runs on a worker thread, so
      it may not touch the GUI, the project, or PROJ. It should check
      ``task.isCanceled()`` between steps and report progress with
      ``task.setProgress(0..100)``.
    on_done: callable taking (result, error), run on the main thread.
      Exactly one of the two is not None; both are None when the run
      was cancelled.

  The exactly-once guarantee matters more than it looks: the dialog
  clears its running-task state in on_done, and a run that ended
  without calling it would leave the plugin permanently convinced a
  tiling is still in flight, refusing every later Generate. Cancel
  paths and exceptions inside the callback are covered too.
  """

  def __init__(self, description, work_fn, on_done):
    from . import compat
    super().__init__(description, compat.task_can_cancel())
    self._work_fn = work_fn
    self._on_done = on_done
    self._result = None
    self._error = None
    self._reported = False
    # WHERE THE WORK GOT TO, for a stall that has to be diagnosed from
    # outside. Both are monotonic, since only a monotonic clock may be
    # subtracted, and both are written by the WORKER and read by the
    # main thread -- a plain attribute assignment, which is atomic
    # enough under the GIL and needs no lock for a reading nobody acts
    # on. See `where_the_work_got_to` for what they are for.
    self.entered_at = None
    self.returned_at = None

  def run(self):  # worker thread
    """Do the work. Returning False routes to finished(ok=False),
    which is how both a raised exception and a cancellation arrive.

    Returns:
      True where the work returned and was not cancelled, False where
      it raised or was cancelled. Records the moment it was entered and
      the moment it left, the second in a `finally` so the raising path
      is stamped too -- the question these answer is whether `run` came
      BACK, and an exception is a way of coming back.
    """
    self.entered_at = time.monotonic()
    try:
      self._result = self._work_fn(self)
    except Exception as e:  # noqa: BLE001 - surfaced to the user
      self._error = e
      return False
    finally:
      self.returned_at = time.monotonic()
    return not self.isCanceled()

  def where_the_work_got_to(self) -> str:
    """Say how far this task's worker got, for a stall report.

    Returns:
      One short phrase -- "never entered run()", "inside run() for
      12.3s", "returned from run() 4.1s ago, not yet delivered", or
      "delivered" -- naming the state and, where a clock reading is
      meaningful, how long it has been in it.

    WHY THIS EXISTS, and it is the whole of its justification. A stall
    in the topology build is diagnosed from outside, and the readings
    reached for first cannot answer it: a task whose `run()` has
    RETURNED still reports `Running`, because the status moves to
    `Complete` only when the main thread delivers the callback, and
    both `QThreadPool.globalInstance().activeThreadCount()` and
    `threading.enumerate()` are blind to a live QGIS task worker
    (measured on QGIS 4.0.3,
    `tools/probes/what_a_running_task_reading_can_tell_apart.py`). So a
    build QGIS never started and a build that finished and was never
    handed back look identical from the outside -- and they want
    OPPOSITE recoveries, since cancelling the second throws a completed
    result away. These two stamps tell them apart by being read.
    IT IS AN INSTRUMENT AND NOT A GUARD: nothing branches on it, and
    the recovery it is meant to inform is 0.24.5's, in ROADMAP.md.
    """
    if self.entered_at is None:
      return "never entered run()"
    if self.returned_at is None:
      return f"inside run() for {time.monotonic() - self.entered_at:.1f}s"
    if not self._reported:
      return ("returned from run() "
              f"{time.monotonic() - self.returned_at:.1f}s ago, "
              "not yet delivered")
    return "delivered"

  def _report(self, result, error):
    """Hand the outcome to the dialog, at most once.

    Args:
      result: what work_fn returned, or None.
      error: the exception it raised, or None. Both None means the
        run was cancelled.

    Returns:
      None. The guard matters because finished() and cancel() can
      both fire for the same task, and calling back twice would let
      the dialog start a run while it believes one is still going.
    """
    if self._reported:
      return
    self._reported = True
    try:
      self._on_done(result, error)
    except Exception:  # never leave the dialog thinking we still run
      import traceback
      traceback.print_exc()

  def finished(self, ok):  # main thread
    """QGIS's completion callback: hand the dialog either the result
    or the error, never both."""
    self._report(self._result if ok else None,
                 self._error if not ok else None)

  def cancel(self):  # main thread
    """Ask QGIS to stop this task, and tell the dialog immediately.

    Returns:
      None. Cancellation is a request: work already inside the
      library cannot be interrupted, so the task may run to
      completion in the background. Reporting now is what lets the
      dialog become usable again at once.
    """
    super().cancel()
    self._report(None, None)
