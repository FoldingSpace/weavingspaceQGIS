"""Run a named subset of the suite, in the suite's own conditions.

Lives in tools/ because it is DOCUMENTED -- CLAUDE.md and
docs/PUBLISHING.md both tell a maintainer to iterate with it -- and
until 2026-08-11 it sat in dev/, which is gitignored. So the command
three documents recommended named a file no clone contained, and only
somebody who was not us would ever find out. Linux CI found it, being
the first checkout of this repository that was not this machine.

The full run takes minutes; this is for checking a specific fix. It
mirrors what tests/run_tests.py does at start-up -- including
_no_modal_dialogs(), whose absence in an earlier scratch runner made
two perfectly ordinary warning dialogs look like twenty-minute hangs.
"""
import importlib.util
import os
import sys
import traceback

# The checkout this script lives in, derived rather than written
# down: a hard-coded path meant that running the copy inside a git
# WORKTREE quietly exercised the other checkout's tests instead --
# green results about code that was not being edited. (2026-08-10.)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

from qgis.core import QgsApplication, QgsProject      # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
app = QgsApplication([], True)
app.initQgis()
rt._no_modal_dialogs()

WANTED = sys.argv[1:]
failed = 0
for name in WANTED:
  QgsProject.instance().clear()      # the suite's empty-project rule
  fn = getattr(rt, name, None)
  if fn is None:
    print(f"MISSING  {name}")
    failed += 1
    continue
  try:
    fn()
    print(f"PASS  {name}")
  except Exception:
    failed += 1
    print(f"FAIL  {name}")
    traceback.print_exc()
    import sys as _s; _s.stdout.flush()

print(f"\n{len(WANTED) - failed} passed, {failed} failed")
os._exit(1 if failed else 0)      # before locals are destroyed: the
                                  # coverage tooling segfaults at exit
