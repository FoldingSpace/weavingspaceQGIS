#!/usr/bin/env python3
"""Record which plugin lines each test executes, once, for reuse.

    QT_QPA_PLATFORM=offscreen ... <qgis python> tools/coverage_per_test.py

Writes ``reports/per-test-coverage.json``: {test name: [ "file:line",
... ]}.

Why: mutation testing is only affordable if a mutant runs the tests
that could possibly notice it, rather than the whole suite. Running
every test against every mutant costs minutes each; running the two
or three tests that execute the mutated line costs seconds. This is
the map that makes that possible, and it needs building only when the
tests or the code move enough to matter.

Method: the suite's own ``check()`` is wrapped so that each test runs
with sys.monitoring LINE events enabled and its own set of touched
lines recorded. That is the same mechanism tools/coverage_report.py
uses; the difference is attribution per test rather than in total.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "weavingspace_qgis")
EXCLUDED = (os.path.join(SRC, "vendor"), os.path.join(SRC, "libs"))
sys.path.insert(0, ROOT)


def main():
  """Run the suite test by test, recording lines touched by each.

  Returns:
    None; writes reports/per-test-coverage.json and prints a summary.
  """
  import importlib.util
  # Raise the suite's per-test stall ceiling BEFORE the suite is
  # loaded, because it reads the variable once at import.
  #
  # Recording coverage runs every test under sys.monitoring, which
  # costs about SIX TIMES the plain duration -- measured 2026-08-11:
  # "free-text inputs survive nonsense" 82s on CI and 513s here,
  # "staggered actions during a run" 161s plain and 855s here. The
  # ceilings in run_tests are sized for a plain run, so under
  # monitoring an ordinary healthy test can pass 600 seconds and be
  # killed as hung. That is a FALSE stall: it costs a whole candidate
  # (two hours, here) and reports a defect that does not exist.
  #
  # An hour, so that even the slowest test has a wide margin at six
  # times its cost, while a genuine hang is still bounded. Set rather
  # than defaulted, and only for this stage: a plain run keeps the
  # tighter ceiling, where it is right.
  os.environ.setdefault("WEAVINGSPACE_TEST_STALL", "3600")
  spec = importlib.util.spec_from_file_location(
    "rt", os.path.join(ROOT, "tests", "run_tests.py"))
  rt = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(rt)

  from qgis.core import QgsApplication
  QgsApplication.setPrefixPath(
    os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  app = QgsApplication([], True)
  app.initQgis()
  rt._enable_stack_dumps()
  rt._no_modal_dialogs()

  mon = sys.monitoring
  tool = mon.COVERAGE_ID
  mon.use_tool_id(tool, "per-test-coverage")
  current = set()

  def on_line(code, lineno):
    filename = code.co_filename
    if filename.startswith(SRC) and not filename.startswith(EXCLUDED):
      current.add(f"{os.path.relpath(filename, ROOT)}:{lineno}")
    return None   # never DISABLE: a later test must see the line too

  mon.register_callback(tool, mon.events.LINE, on_line)

  per_test = {}
  original_check = rt.check

  def timed_check(name, fn, sharded=True):
    """Run one test with its own recording set.

    Args:
      name: the test's display name.
      fn: the test body.
      sharded: forwarded to check(), which uses it to leave a
        registration made from INSIDE a test out of the shard deal.
        A wrapper that swallowed this argument would fail the moment
        such a test ran -- and did, in the first sharded candidate,
        because the fix for it was written on a branch parked for a
        later version while the change that needed it went into this
        one.

    Returns:
      Whatever check() returns; the lines touched are recorded
      against this test's name.
    """
    current.clear()
    mon.set_events(tool, mon.events.LINE)
    try:
      original_check(name, fn, sharded=sharded)
    finally:
      mon.set_events(tool, 0)
      # Record ONLY the tests this process actually ran. check()
      # returns None whether it skipped a test (not dealt to this
      # shard) or ran it, so the return value cannot tell the two
      # apart; the suite's own PASSED and FAILED lists can, because
      # both are appended inside the body after the deal.
      #
      # Recording unconditionally gave every shard an entry for all
      # 286 names, roughly 190 of them empty, and the merge stage
      # refused: a name in more than one shard means the deal was not
      # disjoint. It was right to refuse for a second reason too --
      # an empty entry claims the test covers no line at all, which
      # would tell mutate_auto never to offer that test the chance to
      # notice a mutant, quietly overstating survivors in the one
      # direction a coverage record is dangerous to be wrong in.
      # (2026-08-11, the second defect this stage caught in a night.)
      if name in rt.PASSED or name in rt.FAILED:
        per_test[name] = sorted(current)

  rt.check = timed_check
  written = []

  def write_the_record():
    """Write this process's share of the record, at most once.

    Returns:
      None; writes reports/per-test-coverage.json, or
      per-test-coverage.<i>of<n>.json when sharded, and prints how
      many tests and lines it holds. Reached from two places -- the
      suite's exit and the ordinary return below -- so it refuses a
      second call rather than writing the file twice.

    One file per shard when sharded, merged by the caller. Named for
    the shard rather than written concurrently to one path: three
    processes writing the same JSON is a corrupt record, and a
    corrupt coverage record is the one failure that silently
    understates survivors while looking healthy.
    """
    if written:
      return
    written.append(True)
    shard = os.environ.get("WEAVINGSPACE_TEST_SHARD", "")
    suffix = "." + shard.replace("/", "of") if shard else ""
    out = os.path.join(ROOT, "reports", f"per-test-coverage{suffix}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
      json.dump(per_test, f, indent=1, sort_keys=True)
    covered = len({line for lines in per_test.values() for line in lines})
    print(f"\nrecorded {len(per_test)} tests covering {covered} lines "
          f"-> {os.path.relpath(out, ROOT)}")

  # The suite does not RETURN from main(). It ends in os._exit, added
  # 2026-08-11 so that a segfault in Qt/QGIS teardown could not turn a
  # finished, fully reported run into exit 139. os._exit skips
  # everything after it -- finally blocks, atexit handlers, the rest
  # of this function -- so on 2026-08-11 this recorder ran the entire
  # suite three times, printed no summary, wrote no file, and the
  # candidate aborted at the merge stage with "nothing to merge".
  # Two correct fixes, each invisible to the other; the collision is
  # the defect, not either fix.
  #
  # So the record is written on the way THROUGH that exit rather than
  # after it. Wrapping os._exit here rather than editing the suite
  # keeps the requirement with the tool that has it: this recorder
  # observes a suite it does not own, and a suite that grows a second
  # exit path later costs nothing on this side.
  #
  # A NON-ZERO exit deliberately writes NOTHING. A failed or
  # watchdog-killed run holds a partial record, and a partial shard
  # file is worse than a missing one: it names the shard it was part
  # of, so the merger counts the set complete and every test that
  # never ran reads as a test that touches no lines -- which is
  # exactly how a coverage record understates survivors while looking
  # healthy.
  real_exit = os._exit

  def exit_after_writing_the_record(code):
    """Stand in for os._exit so the record survives the suite's exit.

    Args:
      code: the exit status the suite chose. Zero means it finished
        and the record is complete; anything else leaves no file.

    Returns:
      Never returns; the process ends here.
    """
    if code == 0:
      write_the_record()
    sys.stdout.flush()
    sys.stderr.flush()
    real_exit(code)

  os._exit = exit_after_writing_the_record
  try:
    rt.main()
  except SystemExit:
    pass
  finally:
    mon.free_tool_id(tool)

  # Reached only if the suite ever stops exiting for itself. Leave
  # from HERE rather than returning: QGIS, PROJ and Qt tear down in an
  # order Python's exit sequence does not respect, and the crash lands
  # as main()'s locals are destroyed -- after the record is safely
  # written, so it costs nothing but a fatal signal on the way out,
  # which would one day fail a release for no reason.
  write_the_record()
  sys.stdout.flush()
  sys.stderr.flush()
  real_exit(0)


if __name__ == "__main__":
  main()
