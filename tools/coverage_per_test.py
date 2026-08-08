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

  def timed_check(name, fn):
    """Run one test with its own recording set."""
    current.clear()
    mon.set_events(tool, mon.events.LINE)
    try:
      original_check(name, fn)
    finally:
      mon.set_events(tool, 0)
      per_test[name] = sorted(current)

  rt.check = timed_check
  try:
    rt.main()
  except SystemExit:
    pass
  finally:
    mon.free_tool_id(tool)

  out = os.path.join(ROOT, "reports", "per-test-coverage.json")
  os.makedirs(os.path.dirname(out), exist_ok=True)
  with open(out, "w", encoding="utf-8") as f:
    json.dump(per_test, f, indent=1, sort_keys=True)
  covered = len({line for lines in per_test.values() for line in lines})
  print(f"\nrecorded {len(per_test)} tests covering {covered} lines "
        f"-> {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
  main()
